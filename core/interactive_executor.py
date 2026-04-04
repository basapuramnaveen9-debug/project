import bisect
import codecs
import locale
import os
import subprocess
import threading
import time
import uuid
from pathlib import Path

from core.language_runner import create_execution_artifacts
from core.languages import normalize_language

PROJECT_TEMP_ROOT = Path(__file__).resolve().parent.parent / ".session_tmp"
SESSION_TTL_SECONDS = 600


class ExecutionSession:
    def __init__(self, process, workspace):
        self.id = uuid.uuid4().hex
        self.process = process
        self.workspace = workspace
        self.created_at = time.time()
        self._chunks = []
        self._chunk_offsets = []
        self._length = 0
        self.returncode = None
        self.finished = False
        self._lock = threading.Lock()
        self._encoding = locale.getpreferredencoding(False)
        self._decoder = codecs.getincrementaldecoder(self._encoding)(errors="replace")

        self._stdout_thread = threading.Thread(target=self._read_stream, daemon=True)
        self._stdout_thread.start()

        self._watcher_thread = threading.Thread(target=self._watch_process, daemon=True)
        self._watcher_thread.start()

    def _append_output(self, text):
        if not text:
            return
        with self._lock:
            self._chunks.append(text)
            self._length += len(text)
            self._chunk_offsets.append(self._length)

    def _read_stream(self):
        stream = self.process.stdout
        if stream is None:
            return

        read = stream.read1 if hasattr(stream, "read1") else stream.read
        while True:
            chunk = read(4096)
            if not chunk:
                break
            text = self._decoder.decode(chunk)
            if text:
                self._append_output(text)

        tail = self._decoder.decode(b"", final=True)
        if tail:
            self._append_output(tail)

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
            total_len = self._length
            if total_len == 0:
                safe_cursor = 0
                chunks = []
            else:
                safe_cursor = max(0, min(cursor, total_len))
                if safe_cursor >= total_len:
                    chunks = []
                else:
                    idx = bisect.bisect_right(self._chunk_offsets, safe_cursor)
                    prev_len = self._chunk_offsets[idx - 1] if idx > 0 else 0
                    chunks = self._chunks[idx:].copy()
                    if chunks:
                        chunks[0] = chunks[0][safe_cursor - prev_len:]

        output = "".join(chunks)
        return {
            "output": output,
            "cursor": total_len,
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
            data = payload.encode(self._encoding, errors="replace")
            self.process.stdin.write(data)
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

    def start_session(self, code, language="c", timeout_seconds=5):
        self._cleanup()
        language = normalize_language(language)

        try:
            PROJECT_TEMP_ROOT.mkdir(exist_ok=True)
            temp_path = PROJECT_TEMP_ROOT / f"run_{uuid.uuid4().hex}"
            temp_path.mkdir()
        except OSError as exc:
            return {"ok": False, "error": f"Unable to create compiler workspace: {exc}"}

        artifacts = create_execution_artifacts(code, language, temp_path, timeout_seconds, interactive=True)
        if not artifacts.get("ok"):
            return artifacts

        try:
            env = None
            if artifacts.get("env"):
                env = os.environ.copy()
                env.update(artifacts["env"])

            process = subprocess.Popen(
                artifacts["run_cmd"],
                cwd=artifacts.get("cwd"),
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=-1,
            )
        except OSError as exc:
            if getattr(exc, "winerror", None) == 4551:
                return {
                    "ok": False,
                    "error": (
                        "Compilation or startup succeeded, but Windows Application Control blocked the generated "
                        "program from running. Code execution is disabled by local policy on this machine."
                    ),
                }
            return {"ok": False, "error": f"Unable to run the selected program: {exc}"}

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
