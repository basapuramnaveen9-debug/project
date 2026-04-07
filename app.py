import os
import subprocess
import time
from functools import lru_cache
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory

BASE_DIR = Path(__file__).parent
TRUTHY_ENV_VALUES = frozenset({"1", "true", "yes", "on"})
DEFAULT_VARIANT_COUNT = 5
NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}


from dotenv import load_dotenv

load_dotenv(dotenv_path=BASE_DIR / ".env")

from ai.ai_optimizer import ai_optimize, generate_ai_optimized_variants, resolve_ai_runtime_settings
from ai.sample_generator import generate_sample_program
from analytics.benchmark import estimate_runtime
from core.compiler_pipeline import CompilerPipeline
from core.interactive_executor import execution_manager
from core.languages import normalize_language
from optimizer.algorithm_detector import detect_algorithm
from optimizer.complexity import count_loops, estimate_complexity, estimate_space_complexity

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

pipeline = CompilerPipeline()


def env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in TRUTHY_ENV_VALUES


def is_code_execution_enabled():
    configured = os.getenv("ENABLE_CODE_EXECUTION")
    if configured is not None:
        return env_flag("ENABLE_CODE_EXECUTION")
    return app.debug


def is_ai_configured():
    return bool(resolve_ai_runtime_settings()["api_key"])


def count_code_lines(code):
    return sum(1 for line in code.splitlines() if line.strip())


def get_request_payload():
    return request.json or {}


def current_asset_version():
    return str(int(time.time()))


def _git_output(*args):
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=BASE_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""

    return result.stdout.strip()


@lru_cache(maxsize=1)
def current_build_info():
    commit = (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("GIT_COMMIT")
        or _git_output("rev-parse", "HEAD")
    )
    branch = (
        os.getenv("RENDER_GIT_BRANCH")
        or os.getenv("GIT_BRANCH")
        or _git_output("rev-parse", "--abbrev-ref", "HEAD")
    )
    source = "render" if os.getenv("RENDER_GIT_COMMIT") else "local"
    short_commit = commit[:7] if commit else "unknown"

    label_parts = []
    if branch and branch != "HEAD":
        label_parts.append(branch)
    label_parts.append(short_commit)

    return {
        "branch": branch or "",
        "commit": commit or "",
        "short_commit": short_commit,
        "source": source,
        "label": " - ".join(label_parts),
    }


def render_page(template_name):
    return render_template(
        template_name,
        asset_version=current_asset_version(),
        build_info=current_build_info(),
    )


def analyze_code(code, language):
    return {
        "complexity": estimate_complexity(code, language),
        "space_complexity": estimate_space_complexity(code, language),
        "loops": count_loops(code, language),
        "runtime": estimate_runtime(code, language),
        "lines": count_code_lines(code),
    }


def json_result(result, error_status):
    status_code = 200 if result.get("ok") else error_status
    return jsonify(result), status_code


@app.route("/")
def index():
    return render_page("index.html")


@app.route("/ai-optimization")
def ai_optimization_page():
    return render_page("ai_optimization.html")


@app.route("/healthz")
def healthz():
    ai_config = resolve_ai_runtime_settings()
    return jsonify({
        "ok": True,
        "service": "Optimization Studio",
        "code_execution": is_code_execution_enabled(),
        "ai_configured": bool(ai_config["api_key"]),
        "ai_provider": ai_config["provider"],
        "ai_api_key_env": ai_config["api_key_env"],
        "ai_base_url": ai_config["base_url"],
        "ai_base_url_source": ai_config["base_url_env"],
        "ai_model": ai_config["model"],
        "ai_model_source": ai_config["model_env"],
    })


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        app.static_folder,
        "favicon.svg",
        mimetype="image/svg+xml",
    )


@app.route("/sample", methods=["GET"])
def sample():
    language = normalize_language(request.args.get("language"))
    return jsonify({"code": generate_sample_program(language), "language": language})


@app.route("/ai/variants", methods=["POST"])
def ai_variants():
    payload = get_request_payload()
    code = payload.get("code", "")
    language = normalize_language(payload.get("language"))

    if not code.strip():
        return jsonify({"ok": False, "error": "Code is required."}), 400

    try:
        count = int(payload.get("count", DEFAULT_VARIANT_COUNT))
    except (TypeError, ValueError):
        count = DEFAULT_VARIANT_COUNT

    result = generate_ai_optimized_variants(code, language, max(count, 1))
    return json_result(result, 502)


@app.route("/ai/suggestions", methods=["POST"])
def ai_suggestions():
    payload = get_request_payload()
    code = payload.get("code", "")
    language = normalize_language(payload.get("language"))

    if not code.strip():
        return jsonify({"ok": False, "error": "Code is required.", "ai": []}), 400

    suggestions = ai_optimize(code, language)
    return jsonify({"ok": True, "language": language, "ai": suggestions})


@app.route("/optimize", methods=["POST"])
def optimize():
    payload = get_request_payload()
    code = payload.get("code", "")
    language = normalize_language(payload.get("language"))

    optimized = pipeline.run(code, language)
    before_metrics = analyze_code(code, language)
    after_metrics = analyze_code(optimized, language)

    return jsonify({
        "language": language,
        "optimized": optimized,
        "algorithm": detect_algorithm(code, language),
        "complexity": before_metrics["complexity"],
        "complexity_after": after_metrics["complexity"],
        "space_complexity": before_metrics["space_complexity"],
        "space_complexity_after": after_metrics["space_complexity"],
        "loops": before_metrics["loops"],
        "loops_after": after_metrics["loops"],
        "runtime": before_metrics["runtime"],
        "runtime_after": after_metrics["runtime"],
        "lines_before": before_metrics["lines"],
        "lines_after": after_metrics["lines"],
    })


@app.route("/execute/start", methods=["POST"])
def execute_start():
    if not is_code_execution_enabled():
        return jsonify({
            "ok": False,
            "error": (
                "Code execution is disabled on this deployment. "
                "Set ENABLE_CODE_EXECUTION=true only if you trust the environment and have sandboxing in place."
            ),
        }), 403

    payload = get_request_payload()
    code = payload.get("code", "")
    language = normalize_language(payload.get("language"))
    result = execution_manager.start_session(code, language)
    return json_result(result, 400)


@app.route("/execute/<session_id>/poll", methods=["GET"])
def execute_poll(session_id):
    session = execution_manager.get_session(session_id)
    if not session:
        return jsonify({"ok": False, "error": "Execution session not found."}), 404

    try:
        cursor = int(request.args.get("cursor", 0))
    except ValueError:
        cursor = 0

    data = session.poll(cursor)
    data["ok"] = True
    return jsonify(data)


@app.route("/execute/<session_id>/input", methods=["POST"])
def execute_input(session_id):
    session = execution_manager.get_session(session_id)
    if not session:
        return jsonify({"ok": False, "error": "Execution session not found."}), 404

    payload = get_request_payload()
    text = payload.get("input", "")
    result = session.send_input(text)
    return json_result(result, 400)


@app.route("/execute/<session_id>/stop", methods=["POST"])
def execute_stop(session_id):
    result = execution_manager.stop_session(session_id)
    return json_result(result, 404)


@app.after_request
def disable_cache(response):
    response.headers.update(NO_CACHE_HEADERS)
    return response


if __name__ == "__main__":
    debug = env_flag("FLASK_DEBUG", default=True)
    threaded = env_flag("FLASK_THREADED", default=True)
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))
    app.run(host=host, port=port, debug=debug, threaded=threaded)
