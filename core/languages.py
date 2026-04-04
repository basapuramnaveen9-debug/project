PRIMARY_LANGUAGES = {
    "c": "C",
    "cpp": "C++",
    "java": "Java",
    "python": "Python",
}

MORE_LANGUAGES = {
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "go": "Go",
    "rust": "Rust",
    "csharp": "C#",
    "php": "PHP",
    "ruby": "Ruby",
    "kotlin": "Kotlin",
}

SUPPORTED_LANGUAGES = {
    **PRIMARY_LANGUAGES,
    **MORE_LANGUAGES,
}

LANGUAGE_ALIASES = {
    "c++": "cpp",
    "cplusplus": "cpp",
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "golang": "go",
    "rs": "rust",
    "cs": "csharp",
    "c#": "csharp",
    "rb": "ruby",
    "kt": "kotlin",
}

DEFAULT_LANGUAGE = "c"
C_LIKE_LANGUAGES = {
    "c",
    "cpp",
    "java",
    "javascript",
    "typescript",
    "go",
    "rust",
    "csharp",
    "php",
    "kotlin",
}
COMPILED_LANGUAGES = {"c", "cpp", "java", "go", "rust", "csharp", "kotlin"}
LOCAL_OPTIMIZATION_LANGUAGES = {"c", "cpp", "java", "python"}


def normalize_language(value):
    if value is None:
        return DEFAULT_LANGUAGE

    key = str(value).strip().lower()
    if not key:
        return DEFAULT_LANGUAGE

    if key in SUPPORTED_LANGUAGES:
        return key

    return LANGUAGE_ALIASES.get(key, DEFAULT_LANGUAGE)


def language_label(language):
    return SUPPORTED_LANGUAGES[normalize_language(language)]


def is_c_like(language):
    return normalize_language(language) in C_LIKE_LANGUAGES


def is_compiled_language(language):
    return normalize_language(language) in COMPILED_LANGUAGES


def supports_local_optimization(language):
    return normalize_language(language) in LOCAL_OPTIMIZATION_LANGUAGES
