import re


def remove_dead_code(code):
    code = re.sub(
        r'if\s*\(\s*0\s*\)\s*\{[^}]*\}',
        '',
        code
    )

    code = re.sub(
        r'while\s*\(\s*0\s*\)\s*\{[^}]*\}',
        '',
        code
    )

    code = re.sub(r'\n[ \t]*\n(?:[ \t]*\n)+', '\n\n', code)
    return code.strip()
