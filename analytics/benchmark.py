from core.languages import normalize_language
from optimizer.patterns import contains_sort, count_loop_tokens, has_nested_loops


LANGUAGE_COST_MULTIPLIER = {
    "c": 0.85,
    "cpp": 0.9,
    "java": 1.1,
    "python": 1.8,
    "javascript": 1.35,
    "typescript": 1.4,
    "go": 0.95,
    "rust": 0.82,
    "csharp": 1.08,
    "php": 1.6,
    "ruby": 1.9,
    "kotlin": 1.12,
}


def estimate_runtime(code, language="c"):
    language = normalize_language(language)
    loops = count_loop_tokens(code, language)
    base = 0.001

    runtime = base * (loops + 1) * LANGUAGE_COST_MULTIPLIER[language]

    if has_nested_loops(code, language):
        runtime *= 1.7

    if contains_sort(code):
        runtime *= 1.4

    return round(runtime, 6)
