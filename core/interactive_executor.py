import re
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path

PROJECT_TEMP_ROOT = Path(__file__).resolve().parent.parent / ".codex_tmp"
SESSION_TTL_SECONDS = 600


def prepare_interactive_code(code):
    main_match = re.search(r"\bint\s+main\s*\([^)]*\)\s*\{", code)
    if not main_match:
        return code

    insertion = "\n    setvbuf(stdout, NULL, _IONBF, 0);\n"
    return code[:main_match.end()] + insertion + code[main_match.end():]


class ExecutionSession:
    def __init__(self, process, workspace):
        self.id = uuid.uuid4().hex
        self.process = process
        self.workspace = workspace
        self.created_at = time.time()
        self.output = ""
        self.returncode = None
        self.finished = False
        self._lock = threading.Lock()

        self._stdout_thread = threading.Thread(target=self._read_stream, daemon=True)
        self._stdout_thread.start()

        self._watcher_thread = threading.Thread(target=self._watch_process, daemon=True)
        self._watcher_thread.start()

    def _append_output(self, text):
        if not text:
            return
        with self._lock:
            self.output += text

    def _read_stream(self):
        stream = self.process.stdout
        if stream is None:
            return

        while True:
            chunk = stream.read(1)
            if not chunk:
                break
            self._append_output(chunk)

    def _watch_process(self):
        self.returncode = self.process.wait()
        self.finished = True
        try:
            if self.process.stdin:
                self.process.stdin.close()
        except OSError:
            pass

    def poll(self, cursor=0):
        with self._lock:
            output = self.output

        safe_cursor = max(0, min(cursor, len(output)))
        return {
            "output": output[safe_cursor:],
            "cursor": len(output),
            "finished": self.finished,
            "exit_code": self.returncode,
        }

    def send_input(self, text):
        if self.finished:
            return {"ok": False, "error": "Program has already finished."}

        if self.process.stdin is None:
            return {"ok": False, "error": "Program input is not available."}

        payload = text if text.endswith("\n") else f"{text}\n"
        try:
            self.process.stdin.write(payload)
            self.process.stdin.flush()
            return {"ok": True}
        except OSError as exc:
            return {"ok": False, "error": f"Unable to send input: {exc}"}

    def stop(self):
        if self.finished:
            return

        self.process.terminate()
        try:
            self.process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=1)
        self.finished = True


class ExecutionManager:
    def __init__(self):
        self._sessions = {}
        self._lock = threading.Lock()

    def _cleanup(self):
        now = time.time()
        stale_ids = []
        with self._lock:
            for session_id, session in self._sessions.items():
                if session.finished and now - session.created_at > SESSION_TTL_SECONDS:
                    stale_ids.append(session_id)
            for session_id in stale_ids:
                self._sessions.pop(session_id, None)

    def start_session(self, code, timeout_seconds=5):
        self._cleanup()

        compiler = shutil.which("gcc") or shutil.which("clang")
        if not compiler:
            return {"ok": False, "error": "Compiler not found. Install gcc or clang to run code output."}

        try:
            PROJECT_TEMP_ROOT.mkdir(exist_ok=True)
            temp_path = PROJECT_TEMP_ROOT / f"run_{uuid.uuid4().hex}"
            temp_path.mkdir()
            source_path = temp_path / "program.c"
            binary_path = temp_path / ("program.exe" if compiler.endswith(".exe") else "program")
            source_path.write_text(prepare_interactive_code(code), encoding="utf-8")
        except OSError as exc:
            return {"ok": False, "error": f"Unable to create compiler workspace: {exc}"}

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
            return {"ok": False, "error": "Compilation timed out."}

        if compile_result.returncode != 0:
            error_text = (compile_result.stderr or compile_result.stdout or "").strip()
            return {"ok": False, "error": error_text or "Compilation failed with unknown error."}

        try:
            process = subprocess.Popen(
                [str(binary_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except OSError as exc:
            if getattr(exc, "winerror", None) == 4551:
                return {
                    "ok": False,
                    "error": (
                        "Compilation succeeded, but Windows Application Control blocked the generated "
                        "executable from running. Code execution is disabled by local policy on this machine."
                    ),
                }
            return {"ok": False, "error": f"Unable to run compiled program: {exc}"}

        session = ExecutionSession(process, temp_path)
        with self._lock:
            self._sessions[session.id] = session

        return {"ok": True, "session_id": session.id}

    def get_session(self, session_id):
        with self._lock:
            return self._sessions.get(session_id)

    def stop_session(self, session_id):
        session = self.get_session(session_id)
        if not session:
            return {"ok": False, "error": "Execution session not found."}
        session.stop()
        return {"ok": True}


execution_manager = ExecutionManager()
