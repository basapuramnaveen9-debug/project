import re
import subprocess
import uuid
from pathlib import Path

from core.language_runner import create_execution_artifacts
from core.languages import normalize_language

PROJECT_TEMP_ROOT = Path(__file__).resolve().parent.parent / ".session_tmp"
INPUT_PATTERNS = {
    "c": re.compile(r"\b(scanf|fgets|getchar|gets)\b"),
    "cpp": re.compile(r"\b(cin|getline)\b"),
    "java": re.compile(r"\bScanner\b|readLine\s*\("),
    "python": re.compile(r"\binput\s*\("),
    "javascript": re.compile(r"\b(readline|prompt|process\.stdin)\b"),
    "typescript": re.compile(r"\b(readline|prompt|process\.stdin)\b"),
    "go": re.compile(r"\b(fmt\.Scan|fmt\.Scanf|fmt\.Scanln|bufio\.NewReader|os\.Stdin)\b"),
    "rust": re.compile(r"\b(stdin|read_line)\b"),
    "csharp": re.compile(r"\bConsole\.Read(Line|Key)\b"),
    "php": re.compile(r"\b(readline|fgets\s*\(\s*STDIN)\b"),
    "ruby": re.compile(r"\b(gets|STDIN\.gets)\b"),
    "kotlin": re.compile(r"\b(readLine|readln|Scanner\s*\()\b"),
}


def run_code(code, language="c", stdin_data="", timeout_seconds=3):
    """
    Compile or run code for the selected language, returning stdout or compiler/runtime errors.
    """
    language = normalize_language(language)

    try:
        PROJECT_TEMP_ROOT.mkdir(exist_ok=True)
        temp_path = PROJECT_TEMP_ROOT / f"run_{uuid.uuid4().hex}"
        temp_path.mkdir()
    except OSError as exc:
        return f"Unable to create compiler workspace: {exc}"

    artifacts = create_execution_artifacts(code, language, temp_path, timeout_seconds, interactive=False)
    if not artifacts.get("ok"):
        return artifacts.get("error", "Failed to prepare program execution.")

    try:
        run_result = subprocess.run(
            artifacts["run_cmd"],
            cwd=artifacts.get("cwd"),
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        input_pattern = INPUT_PATTERNS.get(language)
        if input_pattern and not (stdin_data or "").strip() and input_pattern.search(code):
            return "Program is waiting for input. Enter stdin values and run again."
        return "Runtime timed out."
    except OSError as exc:
        if getattr(exc, "winerror", None) == 4551:
            return (
                "Compilation or startup succeeded, but Windows Application Control blocked the generated "
                "program from running. Code execution is disabled by local policy on this machine."
            )
        return f"Unable to run the selected program: {exc}"

    if run_result.returncode != 0:
        runtime_text = (run_result.stderr or run_result.stdout or "").strip()
        return runtime_text or f"Program exited with code {run_result.returncode}."

    output_text = (run_result.stdout or "").strip()
    return output_text if output_text else "(Program produced no output)"


def run_c_code(code, stdin_data="", timeout_seconds=3):
    return run_code(code, "c", stdin_data=stdin_data, timeout_seconds=timeout_seconds)
