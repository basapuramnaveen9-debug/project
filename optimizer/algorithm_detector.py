def detect_algorithm(code):

    results = []

    loops = code.count("for")

    if loops == 1:
        results.append("Linear algorithm O(n)")

    if loops == 2:
        results.append("Nested loops detected O(n^2)")

    if loops >= 3:
        results.append("High complexity loop structure")

    if "sort" in code:
        results.append("Sorting algorithm detected")

    return results