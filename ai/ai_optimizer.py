import re


PRINTF_PATTERN = re.compile(r"\bprintf\s*\(")
SCANF_PATTERN = re.compile(r"\bscanf\s*\(")
MALLOC_PATTERN = re.compile(r"\b(malloc|calloc|realloc)\s*\(")
FREE_PATTERN = re.compile(r"\bfree\s*\(")
ARRAY_PATTERN = re.compile(r"\[[^\]]+\]")
RECURSIVE_FN_PATTERN = re.compile(
    r"\b(?:int|long|void|float|double|char)\s+([A-Za-z_]\w*)\s*\([^)]*\)\s*\{",
    re.MULTILINE,
)


def _has_nested_loops(code):
    lines = code.splitlines()
    depth = 0
    loop_depths = []

    for line in lines:
        stripped = line.strip()
        if re.search(r"\b(for|while|do)\b", stripped):
            loop_depths.append(depth)
        depth += line.count("{")
        depth -= line.count("}")

    return len(loop_depths) >= 2 and max(loop_depths) > min(loop_depths)


def _detect_recursion(code):
    for match in RECURSIVE_FN_PATTERN.finditer(code):
        fn_name = match.group(1)
        body = code[match.end():]
        if re.search(rf"\b{re.escape(fn_name)}\s*\(", body):
            return fn_name
    return None


def ai_optimize(code):
    suggestions = []
    seen = set()

    def add(text):
        if text not in seen:
            seen.add(text)
            suggestions.append(text)

    printf_calls = len(PRINTF_PATTERN.findall(code))
    scanf_calls = len(SCANF_PATTERN.findall(code))
    loop_count = len(re.findall(r"\b(for|while|do)\b", code))
    malloc_calls = len(MALLOC_PATTERN.findall(code))
    has_free = bool(FREE_PATTERN.search(code))
    recursion_fn = _detect_recursion(code)

    if recursion_fn:
        add(f"`{recursion_fn}()` is recursive; consider an iterative version or memoization to reduce repeated work.")

    if _has_nested_loops(code):
        add("Nested loops are present; check whether precomputation or a better data structure can remove one loop level.")
    elif loop_count >= 1:
        add("Loop logic is present; move invariant calculations outside the loop body where possible.")

    if printf_calls >= 2:
        add("Multiple `printf` calls were detected; batching output can reduce I/O overhead.")
    elif printf_calls == 1 and loop_count >= 1 and "printf" in code:
        add("Avoid heavy I/O inside hot paths; if `printf` is in a loop, buffer output instead.")

    if scanf_calls >= 2:
        add("Repeated input calls can dominate runtime; consider faster input parsing if the dataset is large.")

    if malloc_calls and not has_free:
        add("Dynamic allocation is used without a matching `free()`; release heap memory on all exit paths.")
    elif malloc_calls:
        add("Dynamic allocation is present; reuse allocated buffers when possible to reduce allocation overhead.")

    if ARRAY_PATTERN.search(code) and loop_count >= 1:
        add("Array processing was detected; consider cache-friendly traversal and avoid repeated passes over the same data.")

    if re.search(r"\bif\s*\(\s*0\s*\)", code) or re.search(r"\bwhile\s*\(\s*0\s*\)", code):
        add("There is unreachable code guarded by a constant false condition; removing it will simplify the program.")

    if re.search(r"\bfor\s*\([^)]*;[^)]*;[^)]*\)\s*\{\s*printf\s*\(", code, re.DOTALL):
        add("Printing directly inside a loop is expensive; accumulate results first if you need higher throughput.")

    if "sort" in code.lower():
        add("Sorting is used; ensure the sort is necessary and avoid sorting the same data more than once.")

    if not suggestions:
        add("This program is already fairly direct; the next step is to profile it and optimize the hottest path.")

    return suggestions


class AIOptimizer:
    def suggest(self, code):
        return ai_optimize(code)
