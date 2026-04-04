import re

from core.languages import normalize_language

_C_LIKE_LOOP_PATTERN = re.compile(r"\b(for|while|do)\b")
_PYTHON_LOOP_PATTERN = re.compile(r"^\s*(for|while)\b", re.MULTILINE)
_SORT_PATTERN = re.compile(r"\b(?:sorted|sort|Arrays\.sort|Collections\.sort|std::sort|sort\.Slice|sort_by|sort_by_key)\b")
_C_LIKE_FALSE_BLOCK_PATTERN = re.compile(r"\b(?:if|while)\s*\(\s*(?:0|false)\s*\)", re.IGNORECASE)
_PYTHON_FALSE_BLOCK_PATTERN = re.compile(r"^\s*(?:if|while)\s+(?:False|0)\s*:", re.MULTILINE)
_C_RECURSION_PATTERN = re.compile(
    r"\b(?:int|long|void|float|double|char)\s+([A-Za-z_]\w*)\s*\([^)]*\)\s*\{",
    re.MULTILINE,
)
_CPP_RECURSION_PATTERN = re.compile(
    r"\b(?:int|long|void|float|double|char|bool|auto|std::\w+)\s+([A-Za-z_]\w*)\s*\([^)]*\)\s*\{",
    re.MULTILINE,
)
_JAVA_RECURSION_PATTERN = re.compile(
    r"\b(?:public|private|protected|static|final|synchronized|native|abstract|\s)+"
    r"(?:void|int|long|float|double|boolean|char|String|[A-Z]\w*)\s+([A-Za-z_]\w*)\s*\([^)]*\)\s*\{",
    re.MULTILINE,
)
_PYTHON_RECURSION_PATTERN = re.compile(r"^\s*def\s+([A-Za-z_]\w*)\s*\([^)]*\)\s*:", re.MULTILINE)
_JAVASCRIPT_RECURSION_PATTERN = re.compile(r"\bfunction\s+([A-Za-z_]\w*)\s*\([^)]*\)\s*\{", re.MULTILINE)
_PHP_RECURSION_PATTERN = re.compile(r"\bfunction\s+([A-Za-z_]\w*)\s*\([^)]*\)\s*\{", re.MULTILINE)
_RUBY_RECURSION_PATTERN = re.compile(r"^\s*def\s+([A-Za-z_]\w*)(?:\([^)]*\))?", re.MULTILINE)
_GO_RECURSION_PATTERN = re.compile(r"\bfunc\s+([A-Za-z_]\w*)\s*\([^)]*\)\s*(?:\([^)]*\)\s*)?\{", re.MULTILINE)
_RUST_RECURSION_PATTERN = re.compile(r"\bfn\s+([A-Za-z_]\w*)\s*\([^)]*\)\s*(?:->\s*[^{]+)?\{", re.MULTILINE)
_CSHARP_RECURSION_PATTERN = re.compile(
    r"\b(?:public|private|protected|internal|static|sealed|virtual|override|async|\s)+"
    r"(?:void|int|long|float|double|bool|string|char|[A-Z]\w*)\s+([A-Za-z_]\w*)\s*\([^)]*\)\s*\{",
    re.MULTILINE,
)
_KOTLIN_RECURSION_PATTERN = re.compile(r"\bfun\s+([A-Za-z_]\w*)\s*\([^)]*\)\s*(?::\s*[^{=]+)?\{", re.MULTILINE)


def count_loop_tokens(code, language="c"):
    language = normalize_language(language)
    if language == "python":
        return len(_PYTHON_LOOP_PATTERN.findall(code))
    return len(_C_LIKE_LOOP_PATTERN.findall(code))


def has_nested_loops(code, language="c"):
    language = normalize_language(language)
    if language == "python":
        return _has_nested_python_loops(code)
    return _has_nested_c_like_loops(code)


def contains_sort(code):
    return bool(_SORT_PATTERN.search(code))


def contains_dead_block(code, language="c"):
    language = normalize_language(language)
    if language == "python":
        return bool(_PYTHON_FALSE_BLOCK_PATTERN.search(code))
    return bool(_C_LIKE_FALSE_BLOCK_PATTERN.search(code))


def detect_recursion(code, language="c"):
    language = normalize_language(language)

    if language == "python":
        pattern = _PYTHON_RECURSION_PATTERN
    elif language == "java":
        pattern = _JAVA_RECURSION_PATTERN
    elif language == "cpp":
        pattern = _CPP_RECURSION_PATTERN
    elif language in {"javascript", "typescript"}:
        pattern = _JAVASCRIPT_RECURSION_PATTERN
    elif language == "php":
        pattern = _PHP_RECURSION_PATTERN
    elif language == "ruby":
        pattern = _RUBY_RECURSION_PATTERN
    elif language == "go":
        pattern = _GO_RECURSION_PATTERN
    elif language == "rust":
        pattern = _RUST_RECURSION_PATTERN
    elif language == "csharp":
        pattern = _CSHARP_RECURSION_PATTERN
    elif language == "kotlin":
        pattern = _KOTLIN_RECURSION_PATTERN
    else:
        pattern = _C_RECURSION_PATTERN

    for match in pattern.finditer(code):
        fn_name = match.group(1)
        body = code[match.end():]
        if re.search(rf"\b{re.escape(fn_name)}\s*\(", body):
            return fn_name

    return None


def _has_nested_c_like_loops(code):
    depth = 0
    loop_depths = []

    for line in code.splitlines():
        stripped = line.strip()
        if re.search(r"\b(for|while|do)\b", stripped):
            loop_depths.append(depth)
        depth += line.count("{")
        depth -= line.count("}")

    return len(loop_depths) >= 2 and max(loop_depths) > min(loop_depths)


def _has_nested_python_loops(code):
    active_loops = []

    for line in code.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        indent = len(re.match(r"^\s*", line).group(0).expandtabs(4))
        stripped = line.strip()

        while active_loops and indent <= active_loops[-1]:
            active_loops.pop()

        if re.match(r"^(for|while)\b", stripped):
            if active_loops:
                return True
            active_loops.append(indent)

    return False
