from core.languages import normalize_language


def optimize_memory(code, language="c"):
    normalize_language(language)
    return code
