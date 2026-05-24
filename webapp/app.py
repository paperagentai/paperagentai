"""
Backend server for PaperAgent — the automated research pipeline.

Usage:
  cd paperagentai
  python webapp/app.py

Then either:
  - Open http://localhost:5000 in your browser, OR
  - Open https://paperagentai.github.io and point it to this backend

The GitHub Pages frontend (docs/) connects to this backend via the
configurable "Backend API URL" setting.
"""

import os
import sys
import json
import threading
import queue
import time
import re
from datetime import datetime
from io import StringIO

# Ensure the repo root is on sys.path so we can import pipeline internals
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)
os.chdir(ROOT_DIR)

from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from openai import OpenAI

app = Flask(__name__, template_folder="templates", static_folder="static")

# ── CORS — allow GitHub Pages and localhost to call this backend ────────────

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
    return response

@app.before_request
def handle_options():
    if request.method == "OPTIONS":
        resp = app.make_default_options_response()
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
        return resp

# ── Paths ─────────────────────────────────────────────────────────────────────
PROMPT_DIR = os.path.join(ROOT_DIR, "prompts")
LOG_DIR    = os.path.join(ROOT_DIR, "logs")
CONTEXT_DIR = os.path.join(ROOT_DIR, "context")

os.makedirs(LOG_DIR, exist_ok=True)

# ── Pipeline state ────────────────────────────────────────────────────────────
# Tracks running state: None = idle, otherwise dict with step info
pipeline_state = {
    "running": False,
    "current_step": None,
    "output_buffer": [],  # list of strings for SSE streaming
    "queue": None,        # threading queue
    "thread": None,
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _read_file(path):
    if not os.path.exists(path):
        return ""
    with open(path, "r") as f:
        return f.read()

def _write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

def _list_logs():
    logs = []
    if os.path.exists(LOG_DIR):
        for f in sorted(os.listdir(LOG_DIR)):
            if f.endswith(".md"):
                p = os.path.join(LOG_DIR, f)
                logs.append({
                    "name": f,
                    "size": os.path.getsize(p),
                    "mtime": datetime.fromtimestamp(os.path.getmtime(p)).isoformat(),
                })
    return logs

def _get_config():
    return {
        "research_question": _read_file(os.path.join(PROMPT_DIR, "research_question.md")),
        "research_context": _read_file(os.path.join(CONTEXT_DIR, "research_context.md")),
        "recent_papers": _read_file(os.path.join(CONTEXT_DIR, "recent_papers.md")),
        "feedback": _read_file(os.path.join(CONTEXT_DIR, "feedback.txt")),
        "api_key": os.getenv("LLM_API_KEY", ""),
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-v4-pro",
    }

# ── Routes: Pages ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

# ── Routes: Config API ────────────────────────────────────────────────────────

@app.route("/api/config", methods=["GET"])
def api_get_config():
    return jsonify(_get_config())

@app.route("/api/config", methods=["POST"])
def api_save_config():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    if "research_question" in data:
        _write_file(os.path.join(PROMPT_DIR, "research_question.md"), data["research_question"])
    if "research_context" in data:
        _write_file(os.path.join(CONTEXT_DIR, "research_context.md"), data["research_context"])
    if "recent_papers" in data:
        _write_file(os.path.join(CONTEXT_DIR, "recent_papers.md"), data["recent_papers"])
    if "feedback" in data:
        _write_file(os.path.join(CONTEXT_DIR, "feedback.txt"), data["feedback"])

    # API settings are session-only, not persisted
    if "api_key" in data and data["api_key"]:
        os.environ["LLM_API_KEY"] = data["api_key"]

    return jsonify({"status": "ok"})

# ── Routes: Logs API ──────────────────────────────────────────────────────────

@app.route("/api/logs", methods=["GET"])
def api_list_logs():
    return jsonify(_list_logs())

@app.route("/api/logs/<filename>", methods=["GET"])
def api_get_log(filename):
    # Security: only allow .md files
    if not filename.endswith(".md") or ".." in filename:
        return jsonify({"error": "Invalid filename"}), 400
    content = _read_file(os.path.join(LOG_DIR, filename))
    return jsonify({"name": filename, "content": content})

@app.route("/api/logs/<filename>", methods=["DELETE"])
def api_delete_log(filename):
    if not filename.endswith(".md") or ".." in filename:
        return jsonify({"error": "Invalid filename"}), 400
    path = os.path.join(LOG_DIR, filename)
    if os.path.exists(path):
        os.remove(path)
    return jsonify({"status": "ok"})

# ── Routes: Pipeline Execution ────────────────────────────────────────────────

STEP_INFO = {
    "1":  {"title": "Literature Review",           "prompt": "step1_literature.md",              "log": "01_literature.md"},
    "2":  {"title": "Research Questions",           "prompt": "step2_research_questions.md",      "log": "02_research_questions.md"},
    "3":  {"title": "Experiment Design",            "prompt": "step3_experiment_design.md",       "log": "03_experiment_design.md"},
    "4a": {"title": "Code Gen — run_experiments.py","prompt": "step4a_code_generation.md",        "log": "04a_code.md"},
    "4b": {"title": "Code Gen — prompts.py",        "prompt": "step4b_prompts.md",                "log": "04b_code.md"},
    "5a": {"title": "Paper — Related Work + Intro", "prompt": "step5a_related_work_intro.md",     "log": "05a_paper.md"},
    "5b": {"title": "Paper — Methodology",          "prompt": "step5b_methodology.md",             "log": "05b_paper.md"},
    "5c": {"title": "Paper — Results",              "prompt": "step5c_results.md",                 "log": "05c_paper.md"},
    "5d": {"title": "Paper — Discussion + Conclusion","prompt": "step5d_discussion_conclusion.md","log": "05d_paper.md"},
    "5e": {"title": "Paper — Review",               "prompt": "step5e_review.md",                  "log": "05e_modifications.md"},
}

STEP_MAX_TOKENS = {
    "1":  32000, "2": 8000, "3": 16000, "4": 32000,
    "4a": 32000, "4b": 16000, "5a": 128000, "5b": 128000,
    "5c": 128000, "5d": 128000, "5e": 32000,
}

def _emit(q, msg_type, data):
    """Push a server-sent event onto the queue."""
    q.put(json.dumps({"type": msg_type, "data": data}))

def _run_step(step_key, api_key, base_url, model, q):
    """Run a single pipeline step in a background thread, emitting SSE events."""
    info = STEP_INFO[step_key]
    _emit(q, "status", f"Starting Step {step_key}: {info['title']}")

    # Load research question & context
    rq = _read_file(os.path.join(PROMPT_DIR, "research_question.md")).strip()
    ctx = _read_file(os.path.join(CONTEXT_DIR, "research_context.md")).strip()
    if not rq:
        _emit(q, "error", "Research question is empty. Please set it in the Config tab.")
        _emit(q, "done", "")
        return

    # Load system prompt
    system_tmpl = _read_file(os.path.join(PROMPT_DIR, "system_base.md"))
    user_tmpl = _read_file(os.path.join(PROMPT_DIR, info["prompt"]))

    # Build variables
    variables = {"research_question": rq, "research_context": ctx}

    if step_key == "1":
        variables["recent_papers"] = _load_recent_papers_simple()
    elif step_key == "2":
        variables["01_literature"] = _read_file(os.path.join(LOG_DIR, "01_literature.md"))
    elif step_key == "3":
        variables["01_literature"] = _read_file(os.path.join(LOG_DIR, "01_literature.md"))
        variables["02_research_questions"] = _read_file(os.path.join(LOG_DIR, "02_research_questions.md"))
    elif step_key == "4a":
        variables["03_experiment_design"] = _read_file(os.path.join(LOG_DIR, "03_experiment_design.md"))
    elif step_key == "4b":
        variables["04a_code"] = _read_file(os.path.join(LOG_DIR, "04a_code.md"))
    elif step_key == "5a":
        results_path = os.path.join(LOG_DIR, "05_results.md")
        if not os.path.exists(results_path):
            _emit(q, "error", "Results file not found. Complete experiments first — save results to logs/05_results.md")
            _emit(q, "done", "")
            return
        variables["01_literature"] = _read_file(os.path.join(LOG_DIR, "01_literature.md"))
        variables["02_research_questions"] = _read_file(os.path.join(LOG_DIR, "02_research_questions.md"))
        variables["03_experiment_design"] = _read_file(os.path.join(LOG_DIR, "03_experiment_design.md"))
    elif step_key == "5b":
        variables["02_research_questions"] = _read_file(os.path.join(LOG_DIR, "02_research_questions.md"))
        variables["03_experiment_design"] = _read_file(os.path.join(LOG_DIR, "03_experiment_design.md"))
        variables["05a_paper"] = _read_file(os.path.join(LOG_DIR, "05a_paper.md"))
    elif step_key == "5c":
        variables["05_results"] = _read_file(os.path.join(LOG_DIR, "05_results.md"))
        variables["05a_paper"] = _read_file(os.path.join(LOG_DIR, "05a_paper.md"))
        variables["05b_paper"] = _read_file(os.path.join(LOG_DIR, "05b_paper.md"))
    elif step_key == "5d":
        variables["05a_paper"] = _read_file(os.path.join(LOG_DIR, "05a_paper.md"))
        variables["05b_paper"] = _read_file(os.path.join(LOG_DIR, "05b_paper.md"))
        variables["05c_paper"] = _read_file(os.path.join(LOG_DIR, "05c_paper.md"))
    elif step_key == "5e":
        variables["05a_paper"] = _read_file(os.path.join(LOG_DIR, "05a_paper.md"))
        variables["05b_paper"] = _read_file(os.path.join(LOG_DIR, "05b_paper.md"))
        variables["05c_paper"] = _read_file(os.path.join(LOG_DIR, "05c_paper.md"))
        variables["05d_paper"] = _read_file(os.path.join(LOG_DIR, "05d_paper.md"))

    # Fill template
    for k, v in variables.items():
        system_tmpl = system_tmpl.replace(f"{{{{{k}}}}}", v)
        user_tmpl = user_tmpl.replace(f"{{{{{k}}}}}", v)

    max_tok = STEP_MAX_TOKENS.get(step_key, 8000)

    _emit(q, "status", f"Calling {model}... (max_tokens={max_tok})")

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tok,
            messages=[
                {"role": "system", "content": system_tmpl},
                {"role": "user", "content": user_tmpl},
            ],
            stream=True,
        )

        full_output = []
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                full_output.append(token)
                _emit(q, "token", token)

        output_text = "".join(full_output)

        # Save to log
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        log_content = f"# Step {step_key}: {info['title']}\n_Generated: {timestamp}_\n\n{output_text}"
        _write_file(os.path.join(LOG_DIR, info["log"]), log_content)

        _emit(q, "status", f"Saved to logs/{info['log']}")
        _emit(q, "done", info["log"])

    except Exception as e:
        _emit(q, "error", str(e))
        _emit(q, "done", "")


def _load_recent_papers_simple():
    """Simplified recent papers loader for the web context."""
    path = os.path.join(CONTEXT_DIR, "recent_papers.md")
    if not os.path.exists(path):
        return "(none provided)"
    content = _read_file(path)
    titles = re.findall(r"\*\*Title:\*\*\s*(.+)", content)
    if not any(t.strip() for t in titles):
        return "(none provided — add papers to context/recent_papers.md)"

    # For web, just pass the raw content; the LLM can parse it
    return content

@app.route("/api/run/<step_key>", methods=["POST"])
def api_run_step(step_key):
    if step_key not in STEP_INFO and step_key != "all":
        return jsonify({"error": f"Unknown step: {step_key}"}), 400

    if pipeline_state["running"]:
        return jsonify({"error": "A pipeline step is already running"}), 409

    data = request.get_json() or {}
    api_key = data.get("api_key") or os.getenv("LLM_API_KEY", "")
    base_url = data.get("base_url", "https://api.deepseek.com")
    model = data.get("model", "deepseek-v4-pro")

    if not api_key:
        return jsonify({"error": "No API key. Set LLM_API_KEY env var or provide in request."}), 400

    # Determine steps to run
    if step_key == "all":
        steps = list(STEP_INFO.keys())
    else:
        steps = [step_key]

    q = queue.Queue()
    pipeline_state["running"] = True
    pipeline_state["queue"] = q
    pipeline_state["current_step"] = steps[0] if steps else None
    pipeline_state["output_buffer"] = []

    def run_all():
        try:
            for i, s in enumerate(steps):
                pipeline_state["current_step"] = s
                if i > 0:
                    _emit(q, "step_change", s)
                _run_step(s, api_key, base_url, model, q)
        finally:
            pipeline_state["running"] = False
            pipeline_state["current_step"] = None

    thread = threading.Thread(target=run_all, daemon=True)
    pipeline_state["thread"] = thread
    thread.start()

    return jsonify({"status": "started", "steps": steps})

@app.route("/api/stream")
def api_stream():
    """SSE endpoint: streams pipeline output in real-time."""
    def generate():
        q = pipeline_state.get("queue")
        if q is None:
            yield "data: " + json.dumps({"type": "error", "data": "No active pipeline"}) + "\n\n"
            return

        while True:
            try:
                msg = q.get(timeout=30)
                yield f"data: {msg}\n\n"
                # Check for done signal
                parsed = json.loads(msg)
                if parsed["type"] == "done":
                    break
            except queue.Empty:
                # Send heartbeat
                yield f"data: {json.dumps({'type': 'heartbeat', 'data': ''})}\n\n"
                if not pipeline_state["running"]:
                    break

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )

@app.route("/api/status", methods=["GET"])
def api_status():
    return jsonify({
        "running": pipeline_state["running"],
        "current_step": pipeline_state["current_step"],
    })

@app.route("/api/cancel", methods=["POST"])
def api_cancel():
    """Cancel a running pipeline (best-effort; can't cancel the API call itself)."""
    pipeline_state["running"] = False
    pipeline_state["current_step"] = None
    if pipeline_state.get("queue"):
        pipeline_state["queue"].put(json.dumps({"type": "error", "data": "Cancelled by user"}))
        pipeline_state["queue"].put(json.dumps({"type": "done", "data": ""}))
    return jsonify({"status": "cancelled"})

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\n  Research Pipeline — Web Frontend")
    print(f"  Root dir: {ROOT_DIR}")
    print(f"  Open http://localhost:5000 in your browser\n")
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
