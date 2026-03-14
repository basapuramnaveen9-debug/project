import re


def estimate_complexity(code):

    loops = code.count("for")

    if loops == 0:
        return "O(1)"

    if loops == 1:
        return "O(n)"

    if loops == 2:
        return "O(n^2)"

    if loops >= 3:
        return "O(n^3) or higher"


def estimate_space_complexity(code):
    arrays = len(re.findall(r"\[[^\]]*\]", code))
    dynamic_allocs = len(re.findall(r"\b(malloc|calloc|realloc|new)\b", code))

    if arrays == 0 and dynamic_allocs == 0:
        return "O(1)"

    if arrays + dynamic_allocs == 1:
        return "O(n)"

    return "O(n^2) or higher"


def count_loops(code):
    return len(re.findall(r"\b(for|while|do)\b", code))
