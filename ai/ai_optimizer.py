import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from core.language_runner import create_execution_artifacts
from core.languages import normalize_language, supports_local_optimization
from optimizer.constant_folding import fold_constants
from optimizer.dead_code_elimination import remove_dead_code
from optimizer.loop_optimizer import optimize_loops
from optimizer.memory_optimizer import optimize_memory
from optimizer.patterns import contains_dead_block, contains_sort, count_loop_tokens, detect_recursion, has_nested_loops

LANGUAGE_PATTERNS = {
    "c": {
        "output": re.compile(r"\b(printf|puts|putchar|fputs)\s*\("),
        "input": re.compile(r"\b(scanf|fgets|getchar|gets|getc|fread)\s*\("),
        "heap": re.compile(r"\b(malloc|calloc|realloc)\s*\("),
        "release": re.compile(r"\bfree\s*\("),
        "array": re.compile(r"\[[^\]]+\]"),
    },
    "cpp": {
        "output": re.compile(r"(std::cout|cout)\s*<<|\b(printf|puts|putchar|fputs)\s*\("),
        "input": re.compile(r"(std::cin|cin)\s*>>|getline\s*\(|\b(scanf|fgets|getchar|getc)\s*\("),
        "heap": re.compile(r"\b(malloc|calloc|realloc|new)\b"),
        "release": re.compile(r"\b(free|delete)\b"),
        "array": re.compile(r"\[[^\]]+\]|\bvector\s*<"),
    },
    "java": {
        "output": re.compile(r"System\.out\.print(?:ln)?\s*\("),
        "input": re.compile(r"\bScanner\b|readLine\s*\("),
        "heap": re.compile(r"\bnew\b"),
        "release": re.compile(r"$^"),
        "array": re.compile(r"\[[^\]]+\]|\bArrayList\s*<"),
    },
    "python": {
        "output": re.compile(r"\bprint\s*\(|sys\.stdout\.write\s*\("),
        "input": re.compile(r"\binput\s*\(|sys\.stdin\.(?:read|readline)\s*\("),
        "heap": re.compile(r"\[[^\]]*\]|\{[^}]*\}|\blist\s*\(|\bdict\s*\(|\bset\s*\("),
        "release": re.compile(r"$^"),
        "array": re.compile(r"\[[^\]]+\]|\{[^}]*\}"),
    },
    "javascript": {
        "output": re.compile(r"console\.log\s*\(|process\.stdout\.write\s*\("),
        "input": re.compile(r"prompt\s*\(|readline\s*\(|fs\.readFileSync\s*\("),
        "heap": re.compile(r"\bnew\b|\[[^\]]*\]|\{[^}]*\}"),
        "release": re.compile(r"$^"),
        "array": re.compile(r"\[[^\]]+\]|new\s+Array\s*\("),
    },
    "typescript": {
        "output": re.compile(r"console\.log\s*\(|process\.stdout\.write\s*\("),
        "input": re.compile(r"prompt\s*\(|readline\s*\(|fs\.readFileSync\s*\("),
        "heap": re.compile(r"\bnew\b|\[[^\]]*\]|\{[^}]*\}"),
        "release": re.compile(r"$^"),
        "array": re.compile(r"\[[^\]]+\]|new\s+Array\s*\("),
    },
    "go": {
        "output": re.compile(r"fmt\.Print(?:ln|f)?\s*\("),
        "input": re.compile(r"fmt\.Scan(?:ln|f)?\s*\(|bufio\.New(?:Reader|Scanner)\s*\("),
        "heap": re.compile(r"\bmake\s*\(|\bnew\s*\("),
        "release": re.compile(r"$^"),
        "array": re.compile(r"\[[^\]]*\][A-Za-z_]\w*|\[\][A-Za-z_]\w*"),
    },
    "rust": {
        "output": re.compile(r"\bprintln!\s*\(|\bprint!\s*\("),
        "input": re.compile(r"stdin\s*\(\)|read_line\s*\("),
        "heap": re.compile(r"\bvec!\s*\(|\bVec::new\s*\(|\bBox::new\s*\("),
        "release": re.compile(r"$^"),
        "array": re.compile(r"\[[^\]]+\]|\bvec!\s*\("),
    },
    "csharp": {
        "output": re.compile(r"Console\.Write(?:Line)?\s*\("),
        "input": re.compile(r"Console\.Read(?:Line|Key)?\s*\("),
        "heap": re.compile(r"\bnew\b"),
        "release": re.compile(r"$^"),
        "array": re.compile(r"\[[^\]]+\]|\bList\s*<"),
    },
    "php": {
        "output": re.compile(r"\becho\b|\bprint\s*\(|\bprintf\s*\("),
        "input": re.compile(r"fgets\s*\(\s*STDIN|readline\s*\("),
        "heap": re.compile(r"\[[^\]]*\]|\barray\s*\("),
        "release": re.compile(r"$^"),
        "array": re.compile(r"\[[^\]]+\]|\barray\s*\("),
    },
    "ruby": {
        "output": re.compile(r"\bputs\b|\bprint\b"),
        "input": re.compile(r"\bgets\b|STDIN\.read"),
        "heap": re.compile(r"\[[^\]]*\]|\bArray\.new\b|\bHash\.new\b"),
        "release": re.compile(r"$^"),
        "array": re.compile(r"\[[^\]]+\]|\bArray\.new\b"),
    },
    "kotlin": {
        "output": re.compile(r"\bprintln\s*\(|\bprint\s*\("),
        "input": re.compile(r"readLine\s*\(|\bScanner\s*\("),
        "heap": re.compile(r"\barrayOf\s*\(|\bmutableListOf\s*\(|\bIntArray\s*\("),
        "release": re.compile(r"$^"),
        "array": re.compile(r"\barrayOf\s*\(|\bIntArray\s*\(|\bArray\s*<"),
    },
}

DEFAULT_MAX_SUGGESTIONS = 6
DEFAULT_VARIANTS_TIMEOUT_SECONDS = 12.0
DEFAULT_VARIANT_VALIDATION_TIMEOUT_SECONDS = 2.5
SUGGESTION_CACHE = {}


def _suggestion_cache_key(code, language):
    payload = f"{normalize_language(language)}\0{str(code or '').strip()}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _suggestion_cache_settings():
    ttl_seconds = max(0.0, float(os.getenv("AI_SUGGESTION_CACHE_TTL_SECONDS", "900")))
    max_entries = max(0, int(os.getenv("AI_SUGGESTION_CACHE_MAX_ENTRIES", "128")))
    return ttl_seconds, max_entries


def _get_cached_suggestions(cache_key):
    ttl_seconds, _ = _suggestion_cache_settings()
    if ttl_seconds <= 0:
        return None

    entry = SUGGESTION_CACHE.get(cache_key)
    if not entry:
        return None

    if time.time() - entry["created_at"] > ttl_seconds:
        SUGGESTION_CACHE.pop(cache_key, None)
        return None

    return list(entry["suggestions"])


def _store_cached_suggestions(cache_key, suggestions):
    ttl_seconds, max_entries = _suggestion_cache_settings()
    cleaned = [str(item).strip() for item in suggestions if str(item).strip()]
    if ttl_seconds <= 0 or max_entries <= 0 or not cleaned:
        return

    SUGGESTION_CACHE[cache_key] = {
        "created_at": time.time(),
        "suggestions": cleaned,
    }

    if len(SUGGESTION_CACHE) <= max_entries:
        return

    overflow = len(SUGGESTION_CACHE) - max_entries
    stale_keys = sorted(SUGGESTION_CACHE, key=lambda key: SUGGESTION_CACHE[key]["created_at"])[:overflow]
    for stale_key in stale_keys:
        SUGGESTION_CACHE.pop(stale_key, None)


def _is_error_suggestion(text):
    cleaned = str(text or "").strip()
    return cleaned.startswith("AI Error:") or cleaned.startswith("Error:")


def _merge_suggestions(*groups, limit=DEFAULT_MAX_SUGGESTIONS):
    merged = []
    seen = set()
    max_items = max(1, int(limit or DEFAULT_MAX_SUGGESTIONS))

    for group in groups:
        for item in group or []:
            text = str(item or "").strip()
            if not text or _is_error_suggestion(text):
                continue

            fingerprint = re.sub(r"\s+", " ", text).casefold()
            if fingerprint in seen:
                continue

            seen.add(fingerprint)
            merged.append(text)
            if len(merged) >= max_items:
                return merged

    return merged


def ai_optimize(code, language="c"):
    normalized_language = normalize_language(language)
    source = str(code or "")
    if not source.strip():
        return []

    cache_key = _suggestion_cache_key(source, normalized_language)
    cached = _get_cached_suggestions(cache_key)
    if cached:
        return cached

    fallback_suggestions = _heuristic_suggestions(source, normalized_language)
    runtime, error = _get_openai_runtime()
    max_suggestions = runtime["max_suggestions"] if runtime else DEFAULT_MAX_SUGGESTIONS

    if error or not runtime:
        suggestions = _merge_suggestions(fallback_suggestions, limit=max_suggestions)
    else:
        suggestions = _merge_suggestions(
            _openai_suggestions(source, normalized_language, runtime=runtime),
            fallback_suggestions,
            limit=max_suggestions,
        )

    if suggestions:
        _store_cached_suggestions(cache_key, suggestions)
        return suggestions

    return ["AI optimization completed without specific suggestions."]


def generate_ai_optimized_variants(code, language="c", count=5):
    try:
        requested_count = int(count)
    except (TypeError, ValueError):
        requested_count = 5

    requested_count = max(requested_count, 1)
    normalized_language = normalize_language(language)
    fallback_variants = _generate_local_optimized_variants(code, normalized_language, requested_count)
    runtime, error = _get_openai_runtime()
    if error:
        return _build_variant_response(
            code,
            normalized_language,
            fallback_variants,
            warning=f"{error} Showing locally optimized variants instead.",
        )

    system_prompt = (
        "You are an expert compiler engineer and semantics-preserving optimizer. Rewrite the user's program into shorter, cleaner, "
        "and better optimized versions while preserving the exact visible output behavior for the same inputs and all valid test cases. "
        "Keep the same programming language. You may change the structure, algorithm, helper functions, variable names, "
        "or control flow if the final behavior and printed output remain the same. "
        "Prioritize removing dead code, unreachable branches, redundant state, repeated work, and unnecessary loops. "
        "Preserve any testcase-driven input contract such as reading T test cases and processing each case in order. "
        "Never hardcode answers, narrow the accepted input range, or change I/O protocol. "
        "Return ONLY JSON."
    )
    user_prompt = (
        f"Language: {normalized_language}\n"
        f"Generate up to {requested_count} optimized variants of the following code.\n"
        "Requirements:\n"
        "- Use the user's exact code as the base.\n"
        "- Preserve the original output exactly for the same inputs and for any number of valid test cases.\n"
        "- Keep the same programming language.\n"
        "- Return full code for each variant, not snippets.\n"
        "- Return as many complete variants as you can, even if that is fewer than requested.\n"
        "- Remove dead code, unreachable branches, unused temporary state, and redundant calculations whenever it is safe.\n"
        "- Apply normal optimizations such as constant folding, loop cleanup, invariant hoisting, and data-structure or algorithm improvements when safe.\n"
        "- You may rewrite the program substantially if that makes it shorter, clearer, or faster.\n"
        "- You may change the algorithm, structure, variable names, helper functions, and loop style if the final behavior stays the same.\n"
        "- Do not change printed strings, output formatting, output order, or visible behavior.\n"
        "- Keep required input handling intact; do not replace dynamic input or testcase loops with hardcoded values.\n"
        "- If the original code handles multiple test cases, the optimized code must still handle multiple test cases the same way.\n"
        "- Prefer asymptotically better or equally efficient logic; do not make runtime or memory usage worse.\n"
        "- Prefer shorter and faster code when possible, but correctness is mandatory.\n"
        "- Prefer valid compilable or runnable code, not pseudocode.\n"
        "- In the `code` field, return properly formatted multi-line source code.\n"
        "- Do not return the whole program as one escaped string with literal \\n characters.\n"
        "- Keep titles short and summaries concise, and mention the concrete optimization that was applied.\n"
        "- Do not include markdown fences or extra prose.\n"
        "Return a JSON array using this schema:\n"
        '[{"title":"Variant name","summary":"Why this version is optimized","code":"full code here"}]\n\n'
        f"Code:\n{code}"
    )

    variant_timeout_seconds = _variant_timeout_seconds()
    general_timeout = max(0.5, float(runtime.get("timeout_seconds") or variant_timeout_seconds))
    effective_timeout = max(0.5, min(general_timeout, variant_timeout_seconds))
    client = runtime["client"]
    if effective_timeout < general_timeout:
        client = runtime["openai_class"](
            api_key=runtime["api_key"],
            base_url=runtime["base_url"],
            timeout=effective_timeout,
        )

    text, error = _chat_completion_with_hard_timeout(
        runtime,
        system_prompt,
        user_prompt,
        timeout_seconds=variant_timeout_seconds,
        temperature=0.25,
        max_tokens=max(2600, min(12000, requested_count * 1200)),
        client=client,
    )
    if error:
        return _build_variant_response(
            code,
            normalized_language,
            fallback_variants,
            warning=f"Remote AI variant generation was unavailable ({error}). Showing locally optimized variants instead.",
        )

    variants = _filter_output_preserving_variants(code, _parse_code_variants(text), normalized_language)
    if not variants:
        return _build_variant_response(
            code,
            normalized_language,
            fallback_variants,
            warning="The AI response could not be validated as a same-output rewrite, so locally optimized variants are shown instead.",
        )

    return _build_variant_response(code, normalized_language, variants)


def _variant_timeout_seconds():
    return max(1.0, float(os.getenv("OPENAI_VARIANTS_TIMEOUT_SECONDS", str(DEFAULT_VARIANTS_TIMEOUT_SECONDS))))


def _build_variant_response(source_code, language, variants, warning=None):
    payload = {
        "ok": True,
        "language": normalize_language(language),
        "variants": list(variants or []),
    }

    if not payload["variants"]:
        payload["variants"] = [{
            "title": "Original Program",
            "summary": "A safe output-preserving optimized rewrite was not available, so the source program is shown unchanged.",
            "code": str(source_code or "").strip(),
        }]

    if warning:
        payload["warning"] = str(warning).strip()

    return payload


def _run_local_optimizer_pipeline(code, language="c"):
    current = str(code or "").strip()
    if not current:
        return ""
    if not supports_local_optimization(language):
        return current

    for _ in range(3):
        previous = current
        optimized = fold_constants(current, language)
        optimized = remove_dead_code(optimized, language)
        optimized = optimize_loops(optimized, language)
        optimized = optimize_memory(optimized, language)
        current = str(optimized or "").strip()
        if not current:
            return previous
        if current == previous:
            break

    return current


def _generate_local_optimized_variants(code, language="c", count=5):
    normalized_language = normalize_language(language)
    source = str(code or "").strip()
    if not source:
        return []
    if not supports_local_optimization(normalized_language):
        return []

    candidate_variants = []

    def add_variant(title, summary, candidate_code):
        cleaned = str(candidate_code or "").strip()
        if not cleaned:
            return
        candidate_variants.append({
            "title": title,
            "summary": summary,
            "code": cleaned,
        })

    add_variant(
        "Local Pipeline Pass",
        "Runs the built-in optimizer pipeline with repeated passes for folding, dead-code removal, and loop cleanup.",
        _run_local_optimizer_pipeline(source, normalized_language),
    )
    add_variant(
        "Dead Code First",
        "Prunes unreachable logic first, then applies the remaining cleanup passes to the live code path.",
        _run_local_optimizer_pipeline(remove_dead_code(source, normalized_language), normalized_language),
    )
    add_variant(
        "Constant Folding",
        "Precomputes compile-time expressions and removes redundant constant work before later cleanup.",
        fold_constants(source, normalized_language),
    )
    add_variant(
        "Dead Code Removed",
        "Removes unreachable branches, constant-false loops, and dead alternate paths without changing visible output.",
        remove_dead_code(source, normalized_language),
    )
    add_variant(
        "Loop Cleanup",
        "Applies conservative loop simplifications and formatting cleanup.",
        optimize_loops(source, normalized_language),
    )
    add_variant(
        "Fold Then Prune",
        "Combines constant folding with dead-code elimination for a shorter local rewrite.",
        remove_dead_code(fold_constants(source, normalized_language), normalized_language),
    )
    add_variant(
        "Prune Then Tighten",
        "Removes dead branches first, then cleans up loop syntax and spacing.",
        optimize_loops(remove_dead_code(source, normalized_language), normalized_language),
    )

    return _filter_output_preserving_variants(source, candidate_variants, normalized_language)[: max(1, int(count or 1))]


def _heuristic_suggestions(code, language="c"):
    language = normalize_language(language)
    patterns = LANGUAGE_PATTERNS.get(language) or LANGUAGE_PATTERNS["c"]
    suggestions = []
    seen = set()

    def add(text):
        if text not in seen:
            seen.add(text)
            suggestions.append(text)

    output_calls = len(patterns["output"].findall(code))
    input_calls = len(patterns["input"].findall(code))
    loop_count = count_loop_tokens(code, language)
    heap_ops = len(patterns["heap"].findall(code))
    has_release = bool(patterns["release"].search(code))
    recursion_fn = detect_recursion(code, language)

    if recursion_fn:
        add(f"`{recursion_fn}()` is recursive; consider an iterative version or memoization to reduce repeated work.")

    if has_nested_loops(code, language):
        add("Nested loops are present; check whether precomputation or a better data structure can remove one loop level.")
    elif loop_count >= 1:
        if language == "python":
            add("Loop logic is present; move invariant work outside the loop and prefer built-in operations when possible.")
        else:
            add("Loop logic is present; move invariant calculations outside the loop body where possible.")

    if output_calls >= 2:
        if language == "python":
            add("Multiple `print()` calls were detected; collect output first if you need higher throughput.")
        elif language == "java":
            add("Multiple `System.out` calls were detected; batching output can reduce I/O overhead.")
        else:
            add("Multiple output calls were detected; batching output can reduce I/O overhead.")
    elif output_calls == 1 and loop_count >= 1:
        add("Avoid heavy I/O inside hot paths; if output is in a loop, buffer it first.")

    if input_calls >= 2:
        add("Repeated input calls can dominate runtime; consider faster input parsing if the dataset is large.")

    if language in {"c", "cpp"} and heap_ops and not has_release:
        add("Dynamic allocation is used without a matching release path; free or delete heap memory on all exits.")
    elif heap_ops and language in {"c", "cpp"}:
        add("Dynamic allocation is present; reuse allocated buffers when possible to reduce allocation overhead.")

    if language == "java" and "new ArrayList" in code and "ensureCapacity" not in code:
        add("If the target collection size is known, pre-size `ArrayList` to reduce reallocation work.")

    if language == "python" and ".append(" in code and loop_count >= 1:
        add("If you are building a list from a simple loop, a list comprehension may be faster and easier to read.")

    if patterns["array"].search(code) and loop_count >= 1:
        add("Array processing was detected; consider cache-friendly traversal and avoid repeated passes over the same data.")

    if contains_dead_block(code, language):
        add("There is unreachable code guarded by a constant false condition; removing it will simplify the program.")

    if re.search(r"\bfor\s*\([^)]*;[^)]*;[^)]*\)\s*\{\s*(?:printf|System\.out\.print|std::cout|cout)\b", code, re.DOTALL):
        add("Printing directly inside a loop is expensive; accumulate results first if you need higher throughput.")

    if language == "python" and re.search(r"range\s*\(\s*len\s*\(", code):
        add("If you only need items rather than indexes, iterate directly over the collection to simplify the loop.")

    if contains_sort(code):
        add("Sorting is used; ensure the sort is necessary and avoid sorting the same data more than once.")

    if not suggestions:
        add("This program is already fairly direct; the next step is to profile it and optimize the hottest path.")

    return suggestions


def _openai_suggestions(code, language="c", runtime=None):
    runtime = runtime or _get_openai_runtime()[0]
    if not runtime:
        return []

    suggestion_timeout = max(0.0, float(runtime.get("suggestions_timeout_seconds", 0.0)))
    if suggestion_timeout <= 0:
        return []

    system_prompt = (
        "You are a senior performance engineer. Analyze the user's code and return ONLY a JSON array of short strings. "
        "Provide 3-5 concise optimization suggestions. Focus on dead-code removal, time complexity, space usage, I/O efficiency, "
        "invariant work inside loops, and algorithmic improvements. If there is little to optimize, return one profiling-focused suggestion."
    )
    user_prompt = f"Language: {normalize_language(language)}\nCode:\n{code}"

    general_timeout = max(0.5, float(runtime.get("timeout_seconds") or suggestion_timeout))
    effective_timeout = max(0.5, min(general_timeout, suggestion_timeout))
    client = runtime["client"]
    if effective_timeout < general_timeout:
        client = runtime["openai_class"](
            api_key=runtime["api_key"],
            base_url=runtime["base_url"],
            timeout=effective_timeout,
        )

    text, error = _chat_completion(
        runtime,
        system_prompt,
        user_prompt,
        temperature=0.2,
        max_tokens=384,
        client=client,
        model=runtime["suggestions_model"],
    )
    if error:
        return []

    if not text:
        return []

    suggestions = _parse_suggestions(text)
    if not suggestions:
        return []

    return suggestions[: runtime["max_suggestions"]]


def _get_openai_runtime():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None, "Error: OPENAI_API_KEY is not set in the environment or .env file."

    try:
        from openai import OpenAI
    except ModuleNotFoundError:
        return None, (
            "Error: The 'openai' package is not installed in the active Python environment. "
            f"Interpreter: {sys.executable}. "
            f"Install it with: \"{sys.executable}\" -m pip install openai"
        )
    except ImportError as exc:
        return None, (
            "Error: The installed 'openai' package could not be imported correctly in the active "
            f"Python environment ({sys.executable}): {exc}"
        )

    model = os.getenv("OPENAI_MODEL", "openai/gpt-oss-20b")
    base_url = os.getenv("OPENAI_BASE_URL", "https://integrate.api.nvidia.com/v1").rstrip("/")
    timeout_seconds = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "30"))
    suggestions_timeout_seconds = float(os.getenv("OPENAI_SUGGESTIONS_TIMEOUT_SECONDS", "3.5"))
    suggestions_model = os.getenv("OPENAI_SUGGESTIONS_MODEL", model).strip() or model
    max_suggestions = max(1, int(os.getenv("OPENAI_MAX_SUGGESTIONS", str(DEFAULT_MAX_SUGGESTIONS))))

    runtime = {
        "api_key": api_key,
        "model": model,
        "base_url": base_url,
        "timeout_seconds": timeout_seconds,
        "suggestions_timeout_seconds": suggestions_timeout_seconds,
        "suggestions_model": suggestions_model,
        "max_suggestions": max_suggestions,
        "openai_class": OpenAI,
        "client": OpenAI(api_key=api_key, base_url=base_url, timeout=timeout_seconds),
    }
    return runtime, None


def _chat_completion_with_hard_timeout(
    runtime,
    system_prompt,
    user_prompt,
    timeout_seconds,
    temperature=0.6,
    max_tokens=1024,
    client=None,
    model=None,
    stream=False,
):
    state = {
        "text": "",
        "error": None,
    }
    completed = threading.Event()

    def worker():
        try:
            text, error = _chat_completion(
                runtime,
                system_prompt,
                user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                client=client,
                model=model,
                stream=stream,
            )
            state["text"] = text
            state["error"] = error
        except Exception as exc:
            state["error"] = str(exc)
        finally:
            completed.set()

    threading.Thread(target=worker, daemon=True).start()
    if not completed.wait(max(0.5, float(timeout_seconds or DEFAULT_VARIANTS_TIMEOUT_SECONDS))):
        return "", f"request timed out after {float(timeout_seconds):g} seconds"

    return state["text"], state["error"]


def _chat_completion(runtime, system_prompt, user_prompt, temperature=0.6, max_tokens=1024, client=None, model=None, stream=False):
    active_client = client or runtime["client"]
    active_model = model or runtime["model"]

    try:
        completion = active_client.chat.completions.create(
            model=active_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            top_p=1,
            max_tokens=max_tokens,
            stream=stream,
        )

        if stream:
            text_parts = []
            for chunk in completion:
                if not getattr(chunk, "choices", None):
                    continue
                delta = chunk.choices[0].delta
                content = getattr(delta, "content", None)
                if content:
                    text_parts.append(content)
            return "".join(text_parts).strip(), None

        return _extract_completion_text(completion), None
    except Exception as exc:
        import traceback

        traceback.print_exc()
        print(
            f"[AI DEBUG] key_set={bool(runtime['api_key'])}, base_url={runtime['base_url']}, "
            f"model={active_model}, error={exc!r}",
            flush=True,
        )
        return "", str(exc)


def _stream_chat_completion(runtime, system_prompt, user_prompt, temperature=0.6, max_tokens=1024):
    return _chat_completion(
        runtime,
        system_prompt,
        user_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )


def _extract_completion_text(response):
    choices = getattr(response, "choices", None)
    if choices is None and isinstance(response, dict):
        choices = response.get("choices", [])
    if not choices:
        return ""

    first_choice = choices[0]
    message = getattr(first_choice, "message", None)
    if message is None and isinstance(first_choice, dict):
        message = first_choice.get("message", {})

    content = getattr(message, "content", None)
    if content is None and isinstance(message, dict):
        content = message.get("content", "")

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
            else:
                text = getattr(item, "text", None)
            if text:
                parts.append(str(text))
        return "".join(parts).strip()

    return ""


def _parse_suggestions(text):
    cleaned = text.strip()
    if not cleaned:
        return []

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    except json.JSONDecodeError:
        pass

    lines = []
    for line in cleaned.splitlines():
        stripped = line.strip().lstrip("-* ").strip()
        if stripped:
            lines.append(stripped)
    return lines


def _parse_code_variants(text):
    payload = _load_json_payload(text)
    if isinstance(payload, dict):
        payload = payload.get("variants") or payload.get("items") or payload.get("results")

    if not isinstance(payload, list):
        return []

    variants = []
    for index, item in enumerate(payload, start=1):
        title = f"Optimized Variant {index}"
        summary = ""
        code = ""

        if isinstance(item, str):
            code = _normalize_variant_code(item)
        elif isinstance(item, dict):
            title = str(item.get("title") or item.get("name") or title).strip()
            summary = str(item.get("summary") or item.get("description") or item.get("strategy") or "").strip()
            code = _normalize_variant_code(item.get("code") or item.get("optimized_code") or item.get("content") or "")

        if code:
            variants.append({
                "title": title or f"Optimized Variant {index}",
                "summary": summary,
                "code": code,
            })

    return variants


def _normalize_variant_code(code):
    normalized = _strip_markdown_code_fence(str(code or "").strip())
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    if "\n" in normalized or "\\n" not in normalized:
        return normalized

    rebuilt = []
    in_quote = None
    index = 0
    converted = False

    while index < len(normalized):
        char = normalized[index]

        if char == "\\" and index + 1 < len(normalized):
            next_char = normalized[index + 1]

            if in_quote:
                rebuilt.append(char)
                rebuilt.append(next_char)
                index += 2
                continue

            if next_char == "n":
                rebuilt.append("\n")
                index += 2
                converted = True
                continue

            if next_char == "r":
                if normalized[index + 2:index + 4] == "\\n":
                    rebuilt.append("\n")
                    index += 4
                else:
                    rebuilt.append("\n")
                    index += 2
                converted = True
                continue

            if next_char == "t":
                rebuilt.append("    ")
                index += 2
                converted = True
                continue

        if char in {"'", '"'}:
            if in_quote is None:
                in_quote = char
            elif in_quote == char:
                backslash_count = 0
                check_index = index - 1
                while check_index >= 0 and normalized[check_index] == "\\":
                    backslash_count += 1
                    check_index -= 1
                if backslash_count % 2 == 0:
                    in_quote = None

        rebuilt.append(char)
        index += 1

    result = "".join(rebuilt).strip()
    return result if converted else normalized


def _filter_output_preserving_variants(source_code, variants, language="c"):
    filtered = []
    seen = {str(source_code or "").strip()}
    normalized_language = normalize_language(language)

    for index, variant in enumerate(variants, start=1):
        code = str(variant.get("code") or "").strip()
        if not code or code in seen:
            continue

        if not _is_output_preserving_variant(source_code, code, normalized_language):
            continue

        seen.add(code)
        filtered.append({
            "title": str(variant.get("title") or f"Optimized Variant {index}").strip() or f"Optimized Variant {index}",
            "summary": str(variant.get("summary") or "Output-preserving optimized rewrite with dead code removed where possible.").strip(),
            "code": code,
        })

    return filtered


def _is_output_preserving_variant(source_code, candidate_code, language="c"):
    source = str(source_code or "").strip()
    candidate = str(candidate_code or "").strip()
    if not source or not candidate:
        return False

    normalized_language = normalize_language(language)
    if candidate == source:
        return False

    live_source = remove_dead_code(source, normalized_language)
    live_candidate = remove_dead_code(candidate, normalized_language)
    if _sorted_string_literals(live_source) != _sorted_string_literals(live_candidate):
        return False

    if _source_has_input(source, normalized_language) and not _candidate_has_input(candidate, normalized_language):
        return False

    if _source_has_output(source, normalized_language) and not _candidate_has_output(candidate, normalized_language):
        return False

    if not _preserves_required_entrypoint(source, candidate, normalized_language):
        return False

    validation_result = _validate_compilation_and_output(source, candidate, normalized_language)
    if validation_result is False:
        return False

    return True


def _sorted_string_literals(code):
    return sorted(re.findall(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', str(code or ""), flags=re.DOTALL))


def _source_has_input(code, language):
    patterns = LANGUAGE_PATTERNS.get(language) or LANGUAGE_PATTERNS["c"]
    return bool(patterns["input"].search(str(code or "")))


def _candidate_has_input(code, language):
    patterns = LANGUAGE_PATTERNS.get(language) or LANGUAGE_PATTERNS["c"]
    return bool(patterns["input"].search(str(code or "")))


def _source_has_output(code, language):
    patterns = LANGUAGE_PATTERNS.get(language) or LANGUAGE_PATTERNS["c"]
    return bool(patterns["output"].search(str(code or "")))


def _candidate_has_output(code, language):
    patterns = LANGUAGE_PATTERNS.get(language) or LANGUAGE_PATTERNS["c"]
    return bool(patterns["output"].search(str(code or "")))


def _preserves_required_entrypoint(source_code, candidate_code, language):
    source = str(source_code or "")
    candidate = str(candidate_code or "")

    if language in {"c", "cpp", "go", "rust", "csharp", "kotlin"} and re.search(r"\bmain\s*\(", source) and not re.search(r"\bmain\s*\(", candidate):
        return False

    if language == "java":
        source_main = re.search(r"\bstatic\s+void\s+main\s*\(", source)
        candidate_main = re.search(r"\bstatic\s+void\s+main\s*\(", candidate)
        if bool(source_main) != bool(candidate_main):
            return False

        public_classes_source = sorted(re.findall(r"\bpublic\s+class\s+([A-Za-z_]\w*)\b", source))
        public_classes_candidate = sorted(re.findall(r"\bpublic\s+class\s+([A-Za-z_]\w*)\b", candidate))
        if public_classes_source != public_classes_candidate:
            return False

    if language == "python":
        source_main_guard = re.search(r"if\s+__name__\s*==\s*['\"]__main__['\"]\s*:", source)
        candidate_main_guard = re.search(r"if\s+__name__\s*==\s*['\"]__main__['\"]\s*:", candidate)
        if bool(source_main_guard) != bool(candidate_main_guard):
            return False

    return True


def _validate_compilation_and_output(source_code, candidate_code, language):
    timeout_seconds = max(
        0.5,
        float(os.getenv("AI_VARIANT_VALIDATION_TIMEOUT_SECONDS", str(DEFAULT_VARIANT_VALIDATION_TIMEOUT_SECONDS))),
    )

    try:
        with tempfile.TemporaryDirectory(prefix="rtrp_variant_source_") as source_dir, tempfile.TemporaryDirectory(
            prefix="rtrp_variant_candidate_"
        ) as candidate_dir:
            source_artifacts = create_execution_artifacts(source_code, language, Path(source_dir), timeout_seconds)
            if not source_artifacts.get("ok"):
                return None

            candidate_artifacts = create_execution_artifacts(candidate_code, language, Path(candidate_dir), timeout_seconds)
            if not candidate_artifacts.get("ok"):
                return False

            if _source_has_input(source_code, language):
                return True

            source_run = _run_prepared_program(source_artifacts, timeout_seconds)
            if not source_run.get("ok"):
                return None

            candidate_run = _run_prepared_program(candidate_artifacts, timeout_seconds)
            if not candidate_run.get("ok"):
                return False

            return source_run["output"] == candidate_run["output"]
    except Exception:
        return None


def _run_prepared_program(artifacts, timeout_seconds):
    try:
        result = subprocess.run(
            artifacts["run_cmd"],
            cwd=artifacts.get("cwd"),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {"ok": False, "output": ""}

    output = f"{result.stdout or ''}{result.stderr or ''}"
    return {
        "ok": result.returncode == 0,
        "output": output,
    }


def _load_json_payload(text):
    cleaned = _strip_markdown_code_fence(text.strip())
    if not cleaned:
        return None

    candidates = [cleaned]
    for opener, closer in (("[", "]"), ("{", "}")):
        start = cleaned.find(opener)
        end = cleaned.rfind(closer)
        if start != -1 and end != -1 and end > start:
            snippet = cleaned[start:end + 1]
            if snippet not in candidates:
                candidates.append(snippet)

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    return None


def _strip_markdown_code_fence(text):
    cleaned = text.strip()
    if not cleaned.startswith("```"):
        return cleaned

    cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


class AIOptimizer:
    def suggest(self, code, language="c"):
        return ai_optimize(code, language)



