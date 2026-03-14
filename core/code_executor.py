import re
import shutil
import subprocess
import uuid
from pathlib import Path

PROJECT_TEMP_ROOT = Path(__file__).resolve().parent.parent / ".codex_tmp"
INPUT_PATTERN = re.compile(r"\b(scanf|fgets|getchar|gets)\b")


def run_c_code(code, stdin_data="", timeout_seconds=3):
    """
    Compile and run C code, returning stdout or compiler/runtime errors.
    """
    compiler = shutil.which("gcc") or shutil.which("clang")
    if not compiler:
        return "Compiler not found. Install gcc or clang to run code output."

    try:
        PROJECT_TEMP_ROOT.mkdir(exist_ok=True)
        temp_path = PROJECT_TEMP_ROOT / f"run_{uuid.uuid4().hex}"
        temp_path.mkdir()
        source_path = temp_path / "program.c"
        binary_path = temp_path / ("program.exe" if compiler.endswith(".exe") else "program")
        source_path.write_text(code, encoding="utf-8")
    except OSError as exc:
        return f"Unable to create compiler workspace: {exc}"

    compile_cmd = [compiler, str(source_path), "-o", str(binary_path)]
    try:
        compile_result = subprocess.run(
            compile_cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "Compilation timed out."

    if compile_result.returncode != 0:
        error_text = (compile_result.stderr or compile_result.stdout or "").strip()
        return error_text or "Compilation failed with unknown error."

    try:
        run_result = subprocess.run(
            [str(binary_path)],
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        if not (stdin_data or "").strip() and INPUT_PATTERN.search(code):
            return "Program is waiting for input. Enter stdin values and run again."
        return "Runtime timed out."
    except OSError as exc:
        if getattr(exc, "winerror", None) == 4551:
            return (
                "Compilation succeeded, but Windows Application Control blocked the generated "
                "executable from running. Code execution is disabled by local policy on this machine."
            )
        return f"Unable to run compiled program: {exc}"

    if run_result.returncode != 0:
        runtime_text = (run_result.stderr or run_result.stdout or "").strip()
        return runtime_text or f"Program exited with code {run_result.returncode}."

    output_text = (run_result.stdout or "").strip()
    return output_text if output_text else "(Program produced no output)"
