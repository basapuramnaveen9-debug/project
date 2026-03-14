def optimize_memory(code):

    optimized = code

    if "malloc" in code and "free(" not in code:

        optimized += "\n// WARNING: malloc used without free"

    return optimized