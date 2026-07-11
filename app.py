"""
Local web UI for managing watchlist.json.

Run:
    pip install -r requirements.txt
    Create a .env file with: TWELVE_DATA_API_KEY=xxx
    python app.py

Then open http://localhost:5000
"""

import json
import os
import re
import subprocess

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

load_dotenv()

app = Flask(__name__, static_folder="static")

WATCHLIST_FILE = "watchlist.json"
TWELVE_DATA_URL = "https://api.twelvedata.com/quote"


def load_watchlist():
    if not os.path.exists(WATCHLIST_FILE):
        return []
    with open(WATCHLIST_FILE, "r") as f:
        raw = f.read()
    # Strip // line comments so we can parse the file even when hand-edited
    raw = re.sub(r"//[^\n]*", "", raw)
    try:
        data = json.loads(raw)
        return data.get("watchlist", [])
    except json.JSONDecodeError:
        return []


def save_watchlist(entries):
    data = {
        "_comment": "mode: 'daily' compares against previous close. 'fixed' compares against a price you set yourself in 'reference'.",
        "watchlist": entries,
    }
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(data, f, indent=2)


def publish_watchlist():
    """Commit and push watchlist.json so the GitHub Actions workflow picks it up."""
    repo_dir = os.path.dirname(os.path.abspath(__file__)) or "."

    def run(*args):
        return subprocess.run(
            ["git", *args], cwd=repo_dir, capture_output=True, text=True
        )

    run("add", WATCHLIST_FILE)

    status = run("status", "--porcelain", "--", WATCHLIST_FILE)
    if status.stdout.strip():
        commit = run("commit", "-m", "Update watchlist via web UI")
        if commit.returncode != 0:
            return {"ok": False, "message": commit.stderr.strip() or commit.stdout.strip()}

    # The Actions workflow commits state.json back to the repo, so main can
    # be ahead of what we have locally. Rebase onto it before pushing.
    # Always run this (even with no new commit) in case a prior push failed
    # and left an unpushed local commit behind.
    pull = run("pull", "--rebase", "--autostash")
    if pull.returncode != 0:
        run("rebase", "--abort")
        return {"ok": False, "message": "Could not rebase onto latest changes:\n" + (pull.stderr.strip() or pull.stdout.strip())}

    push = run("push")
    if push.returncode != 0:
        return {"ok": False, "message": push.stderr.strip() or push.stdout.strip()}

    return {"ok": True, "pushed": True, "message": "Published to GitHub."}


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/watchlist", methods=["GET"])
def get_watchlist():
    return jsonify(load_watchlist())


@app.route("/api/watchlist", methods=["POST"])
def set_watchlist():
    entries = request.get_json()
    if not isinstance(entries, list):
        return jsonify({"error": "Expected a JSON array"}), 400
    save_watchlist(entries)
    publish_result = publish_watchlist()
    return jsonify({"ok": True, "publish": publish_result})


@app.route("/api/check-ticker")
def check_ticker():
    symbol = request.args.get("symbol", "").strip().upper()
    if not symbol:
        return jsonify({"error": "No symbol provided"}), 400

    api_key = os.environ.get("TWELVE_DATA_API_KEY")
    if not api_key:
        return jsonify({"error": "TWELVE_DATA_API_KEY not set in environment"}), 500

    try:
        resp = requests.get(
            TWELVE_DATA_URL,
            params={"symbol": symbol, "apikey": api_key},
            timeout=10,
        )
        data = resp.json()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if "close" not in data:
        msg = data.get("message", "Ticker not found or API error")
        return jsonify({"found": False, "message": msg})

    return jsonify(
        {
            "found": True,
            "symbol": symbol,
            "price": float(data["close"]),
            "prev_close": float(data.get("previous_close", data["close"])),
            "name": data.get("name", symbol),
        }
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
