import re

from optimizer.patterns import contains_sort, count_loop_tokens, detect_recursion, has_nested_loops


def detect_algorithm(code, language="c"):
    results = []
    loops = count_loop_tokens(code, language)
    recursion_fn = detect_recursion(code, language)

    if has_nested_loops(code, language):
        results.append("Nested loops detected O(n^2) or higher")
    elif loops == 1:
        results.append("Linear scan style algorithm O(n)")
    elif loops >= 3:
        results.append("High complexity loop structure")

    if contains_sort(code):
        results.append("Sorting routine detected")

    if recursion_fn:
        results.append(f"Recursive routine detected in `{recursion_fn}()`")

    if re.search(r"\b(mid|middle)\b", code) and re.search(r"\b(left|right|low|high)\b", code):
        results.append("Binary-search style midpoint logic detected")

    return results
