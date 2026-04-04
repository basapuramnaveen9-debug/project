import re

from core.languages import normalize_language


def _optimize_c_like_loops(code):
    code = re.sub(r"\bfor\s*\(", "for(", code)
    code = re.sub(r"\bwhile\s*\(", "while(", code)
    return code


def _optimize_python_loops(code):
    lines = []
    for line in code.splitlines():
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]
        if stripped.startswith("for ") or stripped.startswith("while "):
            stripped = re.sub(r"\s+:\s*$", ":", stripped)
        lines.append(f"{indent}{stripped}".rstrip())
    return "\n".join(lines)


def optimize_loops(code, language="c"):
    language = normalize_language(language)
    if language == "python":
        return _optimize_python_loops(code)
    return _optimize_c_like_loops(code)
