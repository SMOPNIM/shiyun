"""
诗云 - Web应用入口
究极吟诗程序 - 枚举所有UTF-8可打印字符排列组合
"""

import json
import os
import threading
from datetime import datetime

from flask import Flask, Response, jsonify, render_template, request

from generator import (
    PRESETS,
    estimate_total,
    get_session_stats,
    is_stopped,
    save_combinations,
    stop_session,
    stream_combinations,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24).hex()

_save_tasks: dict = {}
_save_lock = threading.Lock()


def resolve_chars(data: dict) -> str:
    preset = data.get("preset", "")
    chars = data.get("chars", "")
    if not chars and preset in PRESETS:
        chars = PRESETS[preset]["chars"]
    return chars


@app.route("/")
def index():
    presets_info = {
        k: {"label": v["label"], "description": v["description"]}
        for k, v in PRESETS.items()
    }
    return render_template("index.html", presets=presets_info)


@app.route("/api/presets")
def get_presets():
    return jsonify({
        k: {"label": v["label"], "description": v["description"]}
        for k, v in PRESETS.items()
    })


@app.route("/api/presets/<key>/chars")
def get_preset_chars(key):
    preset = PRESETS.get(key)
    if not preset:
        return jsonify({"error": "预设不存在"}), 404
    return jsonify({"chars": preset["chars"]})


@app.route("/api/estimate", methods=["POST"])
def estimate():
    data = request.json
    chars = resolve_chars(data)
    max_len = int(data.get("max_length", 1))
    total = estimate_total(len(chars), max_len)
    total_str = str(total)
    return jsonify({"total": total_str, "total_raw": total, "chars_len": len(chars)})


@app.route("/api/start", methods=["POST"])
def start():
    data = request.json
    session_id = data.get("session_id", "default")
    chars = resolve_chars(data)
    max_len = int(data.get("max_length", 1))

    if not chars:
        return jsonify({"error": "字符集不能为空"}), 400
    if max_len < 1:
        return jsonify({"error": "长度必须大于0"}), 400

    # Just record the session params; actual streaming happens on /stream
    total = estimate_total(len(chars), max_len)
    return jsonify({
        "status": "ready",
        "total": str(total),
        "total_raw": total,
        "chars_len": len(chars),
        "max_length": max_len,
        "session_id": session_id,
    })


@app.route("/api/stop", methods=["POST"])
def stop():
    data = request.json
    session_id = data.get("session_id", "default")
    stop_session(session_id)
    return jsonify({"status": "stopped"})


@app.route("/api/stats")
def stats():
    session_id = request.args.get("session_id", "default")
    stats = get_session_stats(session_id)
    stats["total"] = str(stats["total"])
    return jsonify(stats)


@app.route("/stream")
def stream():
    session_id = request.args.get("session_id", "default")
    preset = request.args.get("preset", "")
    chars = request.args.get("chars", "")
    if not chars and preset in PRESETS:
        chars = PRESETS[preset]["chars"]
    max_len = int(request.args.get("max_length", 1))

    if not chars:
        return jsonify({"error": "字符集不能为空"}), 400
    if max_len < 1:
        return jsonify({"error": "长度必须大于0"}), 400

    def generate():
        yield from stream_combinations(session_id, chars, max_len)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@app.route("/api/save", methods=["POST"])
def save():
    data = request.json
    session_id = data.get("session_id", "default")
    chars = resolve_chars(data)
    max_len = int(data.get("max_length", 1))
    compress = data.get("compress", True)

    if not chars:
        return jsonify({"error": "字符集不能为空"}), 400
    if max_len < 1:
        return jsonify({"error": "长度必须大于0"}), 400

    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"output/shiyun_{timestamp}"

    cancel_event = threading.Event()

    task_info = {
        "running": True,
        "progress": 0.0,
        "file": filename + (".gz" if compress else ""),
        "cancel_event": cancel_event,
        "result": None,
    }

    with _save_lock:
        _save_tasks[session_id] = task_info

    def _do_save():
        try:
            result = save_combinations(
                chars, max_len, filename, compress=compress, cancel_event=cancel_event
            )
            with _save_lock:
                task_info["running"] = False
                task_info["progress"] = 100.0
                task_info["result"] = result
        except Exception as e:
            with _save_lock:
                task_info["running"] = False
                task_info["result"] = {"error": str(e)}

    t = threading.Thread(target=_do_save, daemon=True)
    t.start()

    return jsonify({
        "status": "saving",
        "file": task_info["file"],
    })


@app.route("/api/save_status")
def save_status():
    session_id = request.args.get("session_id", "default")
    with _save_lock:
        task = _save_tasks.get(session_id)
        if not task:
            return jsonify({"saving": False})
        return jsonify({
            "saving": task["running"],
            "progress": round(task["progress"], 1),
            "file": task.get("file", ""),
            "count": task["result"]["count"] if task["result"] else 0,
        })


def main():
    os.makedirs("templates", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    print("=" * 50)
    print("  诗云 - 究极吟诗程序")
    print("  " + "=" * 46)
    print("  启动服务器 (Waitress)...")
    print("  本地访问: http://127.0.0.1:5000")
    print("  网络访问: http://<本机IP>:5000")
    print("  " + "=" * 46)
    print("  提示: 开始吟诗前请先选择字符集和最大长度")
    print("=" * 50)
    from waitress import serve

    serve(app, host="0.0.0.0", port=5000, threads=8)


if __name__ == "__main__":
    main()
