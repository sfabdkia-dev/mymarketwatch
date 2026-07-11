"""
DIY Stock Price Watcher
------------------------
Checks a watchlist of tickers against a % change threshold and sends a
Telegram notification when a threshold is crossed.

Env vars required (set as GitHub Secrets, or export locally for testing):
  TWELVE_DATA_API_KEY
  TELEGRAM_BOT_TOKEN
  TELEGRAM_CHAT_ID

Files:
  watchlist.json  - tickers + thresholds you edit by hand
  state.json       - auto-managed, tracks which alerts already fired today
"""

import json
import os
import sys
from datetime import date

import requests

WATCHLIST_FILE = "watchlist.json"
STATE_FILE = "state.json"

TWELVE_DATA_URL = "https://api.twelvedata.com/quote"
TELEGRAM_URL = "https://api.telegram.org/bot{token}/sendMessage"


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def get_quote(symbol, api_key):
    resp = requests.get(
        TWELVE_DATA_URL,
        params={"symbol": symbol, "apikey": api_key},
        timeout=10,
    )
    data = resp.json()
    if "close" not in data:
        print(f"  ! Could not fetch {symbol}: {data.get('message', data)}")
        return None
    return {
        "price": float(data["close"]),
        "prev_close": float(data.get("previous_close", data["close"])),
    }


def send_telegram(message, token, chat_id):
    resp = requests.post(
        TELEGRAM_URL.format(token=token),
        json={"chat_id": chat_id, "text": message},
        timeout=10,
    )
    if resp.status_code != 200:
        print(f"  ! Telegram send failed: {resp.text}")


def main():
    api_key = os.environ.get("TWELVE_DATA_API_KEY")
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not all([api_key, bot_token, chat_id]):
        print("Missing required environment variables. See top of file.")
        sys.exit(1)

    config = load_json(WATCHLIST_FILE, {"watchlist": []})
    today = str(date.today())
    state = load_json(STATE_FILE, {})

    # Reset state if it's a new day
    if state.get("date") != today:
        state = {"date": today, "alerted": {}}

    alerted = state["alerted"]

    for entry in config["watchlist"]:
        symbol = entry["symbol"]
        mode = entry.get("mode", "daily")
        threshold = entry["threshold_pct"]

        print(f"Checking {symbol} ({mode}, {threshold}%)...")
        quote = get_quote(symbol, api_key)
        if quote is None:
            continue

        price = quote["price"]

        if mode == "daily":
            reference = quote["prev_close"]
        else:  # fixed
            reference = entry["reference"]

        if reference == 0:
            continue

        pct_change = ((price - reference) / reference) * 100
        print(f"  price={price} reference={reference} change={pct_change:.2f}%")

        already_alerted = alerted.get(symbol) == True
        if abs(pct_change) >= threshold and not already_alerted:
            direction = "up" if pct_change > 0 else "down"
            msg = (
                f"{symbol} is {direction} {abs(pct_change):.2f}% "
                f"(now {price}, reference {reference})"
            )
            print(f"  -> ALERT: {msg}")
            send_telegram(msg, bot_token, chat_id)
            alerted[symbol] = True

    state["alerted"] = alerted
    save_json(STATE_FILE, state)


if __name__ == "__main__":
    main()
