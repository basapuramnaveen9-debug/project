import os
import time
from flask import Flask, render_template, request, jsonify, send_from_directory

from core.compiler_pipeline import CompilerPipeline
from core.interactive_executor import execution_manager
from optimizer.algorithm_detector import detect_algorithm
from optimizer.complexity import count_loops, estimate_complexity, estimate_space_complexity
from ai.ai_optimizer import ai_optimize
from ai.sample_generator import generate_sample_program
from analytics.benchmark import estimate_runtime

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

pipeline = CompilerPipeline()


def env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def is_code_execution_enabled():
    configured = os.getenv("ENABLE_CODE_EXECUTION")
    if configured is not None:
        return env_flag("ENABLE_CODE_EXECUTION")
    return app.debug


def count_code_lines(code):
    return sum(1 for line in code.splitlines() if line.strip())


@app.route("/")
def index():
    return render_template("index.html", asset_version=str(int(time.time())))


@app.route("/healthz")
def healthz():
    return jsonify({"ok": True, "service": "RTRP", "code_execution": is_code_execution_enabled()})


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        app.static_folder,
        "favicon.svg",
        mimetype="image/svg+xml",
    )


@app.route("/sample", methods=["GET"])
def sample():
    return jsonify({"code": generate_sample_program()})


@app.route("/optimize", methods=["POST"])
def optimize():
    payload = request.json or {}
    code = payload.get("code", "")

    optimized = pipeline.run(code)

    return jsonify({
        "optimized": optimized,
        "ai": ai_optimize(code),
        "algorithm": detect_algorithm(code),
        "complexity": estimate_complexity(code),
        "space_complexity": estimate_space_complexity(code),
        "loops": count_loops(code),
        "runtime": estimate_runtime(code),
        "lines_before": count_code_lines(code),
        "lines_after": count_code_lines(optimized),
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

    payload = request.json or {}
    code = payload.get("code", "")
    result = execution_manager.start_session(code)
    status_code = 200 if result.get("ok") else 400
    return jsonify(result), status_code


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

    payload = request.json or {}
    text = payload.get("input", "")
    result = session.send_input(text)
    status_code = 200 if result.get("ok") else 400
    return jsonify(result), status_code


@app.route("/execute/<session_id>/stop", methods=["POST"])
def execute_stop(session_id):
    result = execution_manager.stop_session(session_id)
    status_code = 200 if result.get("ok") else 404
    return jsonify(result), status_code


@app.after_request
def disable_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


if __name__ == "__main__":
    debug = env_flag("FLASK_DEBUG", default=True)
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))
    app.run(host=host, port=port, debug=debug)
