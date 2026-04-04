import ast
import re
import textwrap

from core.languages import normalize_language

_C_FALSE = r"(?:0|false)"
_C_TRUE = r"(?:1|true)"
_C_IF_FALSE_ELSE_PATTERN = re.compile(
    rf"(?P<indent>^[ \t]*)if\s*\(\s*{_C_FALSE}\s*\)\s*\{{\s*(?P<then>[^{{}}]*)\s*\}}\s*else\s*\{{\s*(?P<else>[^{{}}]*)\s*\}}",
    flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
)
_C_IF_TRUE_ELSE_PATTERN = re.compile(
    rf"(?P<indent>^[ \t]*)if\s*\(\s*{_C_TRUE}\s*\)\s*\{{\s*(?P<then>[^{{}}]*)\s*\}}\s*else\s*\{{\s*(?P<else>[^{{}}]*)\s*\}}",
    flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
)
_C_IF_FALSE_PATTERN = re.compile(
    rf"(?P<indent>^[ \t]*)if\s*\(\s*{_C_FALSE}\s*\)\s*\{{\s*(?P<body>[^{{}}]*)\s*\}}",
    flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
)
_C_IF_TRUE_PATTERN = re.compile(
    rf"(?P<indent>^[ \t]*)if\s*\(\s*{_C_TRUE}\s*\)\s*\{{\s*(?P<body>[^{{}}]*)\s*\}}",
    flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
)
_C_WHILE_FALSE_PATTERN = re.compile(
    rf"(?P<indent>^[ \t]*)while\s*\(\s*{_C_FALSE}\s*\)\s*\{{\s*(?P<body>[^{{}}]*)\s*\}}",
    flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
)
_C_FOR_FALSE_PATTERN = re.compile(
    rf"(?P<indent>^[ \t]*)for\s*\([^;]*;\s*{_C_FALSE}\s*;[^)]*\)\s*\{{\s*(?P<body>[^{{}}]*)\s*\}}",
    flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
)


def _collapse_blank_lines(code):
    collapsed = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", str(code or ""))
    return collapsed.strip()


def _reindent_c_block(body, indent):
    cleaned = textwrap.dedent(str(body or "")).strip("\n")
    if not cleaned.strip():
        return ""

    lines = []
    for line in cleaned.splitlines():
        stripped = line.rstrip()
        if stripped:
            lines.append(f"{indent}{stripped}")
        else:
            lines.append("")
    return "\n".join(lines).strip("\n")


def _keep_c_branch(branch_name):
    def replacer(match):
        return _reindent_c_block(match.group(branch_name), match.group("indent") or "")

    return replacer


def _drop_c_branch(_match):
    return ""


def _remove_c_like_dead_code(code):
    current = str(code or "")
    if not current.strip():
        return ""

    patterns = (
        (_C_IF_FALSE_ELSE_PATTERN, _keep_c_branch("else")),
        (_C_IF_TRUE_ELSE_PATTERN, _keep_c_branch("then")),
        (_C_IF_FALSE_PATTERN, _drop_c_branch),
        (_C_IF_TRUE_PATTERN, _keep_c_branch("body")),
        (_C_WHILE_FALSE_PATTERN, _drop_c_branch),
        (_C_FOR_FALSE_PATTERN, _drop_c_branch),
    )

    for _ in range(6):
        previous = current
        for pattern, replacer in patterns:
            current = pattern.sub(replacer, current)
        current = _collapse_blank_lines(current)
        if current == previous.strip():
            break

    return current


def _literal_truth_value(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (bool, int)):
        return bool(node.value)
    return None


class _PythonDeadCodeTransformer(ast.NodeTransformer):
    def visit_If(self, node):
        node = self.generic_visit(node)
        truth_value = _literal_truth_value(node.test)
        if truth_value is True:
            return node.body
        if truth_value is False:
            return node.orelse or []
        return node

    def visit_While(self, node):
        node = self.generic_visit(node)
        truth_value = _literal_truth_value(node.test)
        if truth_value is False:
            return []
        return node


def _remove_python_dead_code(code):
    source = str(code or "")
    if not source.strip():
        return ""

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return _collapse_blank_lines(source)

    transformed = _PythonDeadCodeTransformer().visit(tree)
    ast.fix_missing_locations(transformed)
    try:
        optimized = ast.unparse(transformed)
    except Exception:
        return _collapse_blank_lines(source)

    return _collapse_blank_lines(optimized)


def remove_dead_code(code, language="c"):
    language = normalize_language(language)
    if language == "python":
        return _remove_python_dead_code(code)
    return _remove_c_like_dead_code(code)
