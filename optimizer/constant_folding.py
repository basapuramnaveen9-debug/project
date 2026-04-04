import ast
import re

from core.languages import normalize_language


DECL_PATTERN = re.compile(
    r"^(\s*)((?:(?:const\s+)?(?:int|long|short)\s+))([A-Za-z_]\w*)\s*=\s*([^;]+)\s*;\s*$"
)
MULTI_DECL_PATTERN = re.compile(
    r"^(\s*)((?:(?:const\s+)?(?:int|long|short)\s+))(.+);\s*$"
)
ASSIGN_PATTERN = re.compile(
    r"^(\s*)([A-Za-z_]\w*)\s*=\s*([^;]+)\s*;\s*$"
)
IDENTIFIER_PATTERN = re.compile(r"\b([A-Za-z_]\w*)\b")
KEYWORD_TOKENS = {"int", "long", "short", "const"}
PY_ASSIGN_PATTERN = re.compile(r"^(\s*)([A-Za-z_]\w*)\s*=\s*(.+?)\s*$")
PY_BLOCK_PREFIX_PATTERN = re.compile(
    r"^\s*(if|elif|else|for|while|def|class|with|try|except|finally|return|raise|yield|break|continue|pass|import|from|match|case)\b"
)


class _ConstExprEvaluator(ast.NodeVisitor):
    def __init__(self, constants):
        self.constants = constants

    def visit_Expression(self, node):
        return self.visit(node.body)

    def visit_Constant(self, node):
        if isinstance(node.value, int):
            return node.value
        raise ValueError("Only integer constants are supported")

    def visit_Name(self, node):
        if node.id in self.constants:
            return self.constants[node.id]
        raise ValueError(f"Unknown symbol: {node.id}")

    def visit_UnaryOp(self, node):
        value = self.visit(node.operand)
        if isinstance(node.op, ast.UAdd):
            return value
        if isinstance(node.op, ast.USub):
            return -value
        raise ValueError("Unsupported unary op")

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)

        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            if right == 0:
                raise ValueError("Division by zero")
            return left // right
        if isinstance(node.op, ast.FloorDiv):
            if right == 0:
                raise ValueError("Division by zero")
            return left // right
        if isinstance(node.op, ast.Mod):
            if right == 0:
                raise ValueError("Modulo by zero")
            return left % right

        raise ValueError("Unsupported binary op")

    def generic_visit(self, node):
        raise ValueError(f"Unsupported expression: {type(node).__name__}")


def _try_eval_constant_expr(expr, constants):
    try:
        parsed = ast.parse(expr, mode="eval")
        evaluator = _ConstExprEvaluator(constants)
        return evaluator.visit(parsed)
    except Exception:
        return None


def _format_assignment(indent, type_prefix, var_name, value):
    prefix = (type_prefix or "").strip()
    if prefix:
        return f"{indent}{prefix} {var_name} = {value};"
    return f"{indent}{var_name} = {value};"


def _split_declarators(decl_body):
    parts = []
    current = []
    depth = 0

    for char in decl_body:
        if char == "," and depth == 0:
            part = "".join(current).strip()
            if part:
                parts.append(part)
            current = []
            continue

        if char == "(":
            depth += 1
        elif char == ")" and depth > 0:
            depth -= 1

        current.append(char)

    tail = "".join(current).strip()
    if tail:
        parts.append(tail)

    return parts


def _build_decl_item(text, var_name, rhs_for_usage, folded_value, is_literal_decl):
    return {
        "text": text,
        "decl_var": var_name,
        "rhs": rhs_for_usage,
        "is_constant_decl": folded_value is not None,
        "is_literal_decl": is_literal_decl,
    }


def _simplify_statement(line, constants):
    return line


def _fold_c_like_constants(code):
    constants = {}
    items = []

    for line in code.splitlines():
        match = DECL_PATTERN.match(line)
        assign_match = ASSIGN_PATTERN.match(line)
        if not match and assign_match:
            indent = assign_match.group(1) or ""
            var_name = assign_match.group(2)
            rhs = assign_match.group(3).strip()
            folded_value = _try_eval_constant_expr(rhs, constants)

            if folded_value is not None:
                constants[var_name] = folded_value
                items.append(
                    _build_decl_item(
                        _format_assignment(indent, "", var_name, folded_value),
                        var_name,
                        str(folded_value),
                        folded_value,
                        rhs.lstrip("-").isdigit(),
                    )
                )
            else:
                constants.pop(var_name, None)
                items.append(
                    _build_decl_item(line, var_name, rhs, None, False)
                )
            continue

        if not match:
            items.append(
                {
                    "text": _simplify_statement(line, constants),
                    "decl_var": None,
                    "rhs": None,
                    "is_constant_decl": False,
                    "is_literal_decl": False,
                }
            )
            continue

        multi_match = MULTI_DECL_PATTERN.match(line)
        if not multi_match:
            items.append(
                {
                    "text": line,
                    "decl_var": None,
                    "rhs": None,
                    "is_constant_decl": False,
                    "is_literal_decl": False,
                }
            )
            continue

        indent = multi_match.group(1) or ""
        type_prefix = multi_match.group(2) or ""
        decl_body = multi_match.group(3).strip()
        declarators = _split_declarators(decl_body)

        if len(declarators) == 1:
            var_name = match.group(3)
            rhs = match.group(4).strip()
            folded_value = _try_eval_constant_expr(rhs, constants)

            if folded_value is not None:
                constants[var_name] = folded_value
                items.append(
                    _build_decl_item(
                        _format_assignment(indent, type_prefix, var_name, folded_value),
                        var_name,
                        str(folded_value),
                        folded_value,
                        rhs.lstrip("-").isdigit(),
                    )
                )
            else:
                constants.pop(var_name, None)
                items.append(
                    _build_decl_item(line, var_name, rhs, None, False)
                )
            continue

        split_items = []
        all_constant = True
        for decl in declarators:
            if "=" not in decl:
                all_constant = False
                split_items = []
                break

            var_name, rhs = decl.split("=", 1)
            var_name = var_name.strip()
            rhs = rhs.strip()
            folded_value = _try_eval_constant_expr(rhs, constants)
            if folded_value is None:
                constants.pop(var_name, None)
                all_constant = False
                split_items = []
                break

            constants[var_name] = folded_value
            split_items.append(
                _build_decl_item(
                    _format_assignment(indent, type_prefix, var_name, folded_value),
                    var_name,
                    str(folded_value),
                    folded_value,
                    rhs.lstrip("-").isdigit(),
                )
            )

        if all_constant:
            items.extend(split_items)
        else:
            items.append(
                {
                    "text": line,
                    "decl_var": None,
                    "rhs": None,
                    "is_constant_decl": False,
                    "is_literal_decl": False,
                }
            )

    used_vars = set()
    for item in items:
        source_text = item["rhs"] if item["rhs"] is not None else item["text"]
        for token in IDENTIFIER_PATTERN.findall(source_text):
            if token not in KEYWORD_TOKENS:
                used_vars.add(token)

    filtered = []
    retained_decl_count = 0
    last_constant_decl_text = None
    for item in items:
        decl_var = item["decl_var"]
        if decl_var and item["is_constant_decl"]:
            last_constant_decl_text = item["text"]
            if decl_var not in used_vars:
                continue
            retained_decl_count += 1
        filtered.append(item["text"])

    if not filtered:
        filtered = [item["text"] for item in items if item["text"].strip()]

    if retained_decl_count == 0 and last_constant_decl_text:
        non_decl_lines = [item["text"] for item in items if item["decl_var"] is None]
        filtered = [last_constant_decl_text] + non_decl_lines

    return "\n".join(filtered)


def _fold_python_constants(code):
    constants = {}
    optimized_lines = []

    for line in code.splitlines():
        if not line.strip():
            optimized_lines.append(line)
            continue

        if PY_BLOCK_PREFIX_PATTERN.match(line):
            optimized_lines.append(line)
            continue

        match = PY_ASSIGN_PATTERN.match(line)
        if not match:
            optimized_lines.append(line)
            continue

        indent = match.group(1) or ""
        var_name = match.group(2)
        rhs = match.group(3).strip()
        rhs_code = rhs.partition("#")[0].strip()

        if not rhs_code or "," in rhs_code:
            constants.pop(var_name, None)
            optimized_lines.append(line)
            continue

        folded_value = _try_eval_constant_expr(rhs_code, constants)
        if folded_value is None:
            constants.pop(var_name, None)
            optimized_lines.append(line)
            continue

        constants[var_name] = folded_value
        optimized_lines.append(f"{indent}{var_name} = {folded_value}")

    return "\n".join(optimized_lines)


def fold_constants(code, language="c"):
    language = normalize_language(language)

    if language == "python":
        return _fold_python_constants(code)

    return _fold_c_like_constants(code)
