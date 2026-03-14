def estimate_runtime(code):

    loops = code.count("for")

    base = 0.001

    runtime = base * (loops + 1)

    return round(runtime,6)