import re


def optimize_loops(code):
    """
    Keep loop syntax intact and only apply safe formatting cleanup.
    """
    code = re.sub(r"\bfor\s*\(", "for(", code)
    code = re.sub(r"\bwhile\s*\(", "while(", code)
    return code
