import re

from core.languages import normalize_language
from optimizer.patterns import contains_sort, count_loop_tokens, detect_recursion


def estimate_complexity(code, language="c"):
    loops = count_loop_tokens(code, language)
    recursion_fn = detect_recursion(code, language)

    if contains_sort(code) and loops <= 1:
        return "O(n log n)"

    if loops == 0 and recursion_fn:
        return "O(n) or depends on recursion branching"

    if loops == 0:
        return "O(1)"

    if loops == 1:
        return "O(n)"

    if loops == 2:
        return "O(n^2)"

    if loops >= 3:
        return "O(n^3) or higher"


def estimate_space_complexity(code, language="c"):
    language = normalize_language(language)

    if language == "python":
        containers = len(re.findall(r"\[[^\]]*\]|\{[^}]*\}|\blist\s*\(|\bdict\s*\(|\bset\s*\(", code))

        if containers == 0:
            return "O(1)"

        if containers == 1:
            return "O(n)"

        return "O(n^2) or higher"

    arrays = len(re.findall(r"\[[^\]]*\]", code))

    if language == "java":
        dynamic_allocs = len(re.findall(r"\bnew\b", code))
    elif language == "cpp":
        dynamic_allocs = len(re.findall(r"\b(malloc|calloc|realloc|new)\b", code))
    else:
        dynamic_allocs = len(re.findall(r"\b(malloc|calloc|realloc)\b", code))

    if arrays == 0 and dynamic_allocs == 0:
        return "O(1)"

    if arrays + dynamic_allocs == 1:
        return "O(n)"

    return "O(n^2) or higher"


def count_loops(code, language="c"):
    return count_loop_tokens(code, language)
