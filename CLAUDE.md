# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A serverless stock price alert bot. `workflows/stock_alert.py` runs on GitHub Actions every 30 minutes during market hours, checks tickers against thresholds via the Twelve Data API, and sends Telegram messages when a threshold is crossed. No server or database — state is persisted by committing `state.json` back to the repo after each run.

## Running locally

```bash
pip install -r requirements.txt
$env:TWELVE_DATA_API_KEY="xxx"
$env:TELEGRAM_BOT_TOKEN="xxx"
$env:TELEGRAM_CHAT_ID="xxx"
python workflows/stock_alert.py
```

## Key files

- `watchlist.json` — tickers and thresholds; edit to add/remove stocks
- `workflows/stock_alert.py` — the full script (single file, no submodules)
- `state.json` — auto-generated at runtime; tracks which alerts have fired today

## Alert modes

Two modes controlled per-ticker in `watchlist.json`:
- `"mode": "daily"` — compares current price against previous close; resets each calendar day
- `"mode": "fixed"` — compares against a hardcoded `"reference"` price; never resets automatically

Once an alert fires for a ticker it won't fire again until: next day (daily) or until `state.json` / `watchlist.json` is manually edited (fixed).

## Required secrets (GitHub Actions)

`TWELVE_DATA_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` — set under repo Settings → Secrets and variables → Actions. The workflow also needs **read and write permissions** (Settings → Actions → General → Workflow permissions) so it can commit `state.json`.
