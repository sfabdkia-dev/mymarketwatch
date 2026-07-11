# DIY Stock Price Alert Bot

Free stock watcher that texts you on Telegram when a ticker moves past a %
threshold. Runs on GitHub Actions — no server needed.

## Files
- `watchlist.json` — your tickers, edit freely
- `stock_alert.py` — the script that checks prices and sends alerts
- `state.json` — auto-generated, tracks what's already alerted today
- `.github/workflows/stock-alerts.yml` — the free scheduler (every 30 min, market hours)

## Setup

1. **Get a Twelve Data API key**: sign up free at twelvedata.com, copy your API key.
2. **Get your Telegram bot token + chat ID** (from BotFather, as set up earlier).
3. **Create a new GitHub repo**, push these files to it.
4. In the repo, go to **Settings → Secrets and variables → Actions → New repository secret**, add:
   - `TWELVE_DATA_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
5. Go to **Settings → Actions → General → Workflow permissions**, select
   **"Read and write permissions"** (needed so the workflow can commit `state.json` back).
6. Edit `watchlist.json` with the tickers/thresholds you want.
7. Go to the **Actions** tab, select "Stock Price Alerts", click **Run workflow** to test it manually.

## Testing locally (optional)
```bash
pip install -r requirements.txt
export TWELVE_DATA_API_KEY=xxx
export TELEGRAM_BOT_TOKEN=xxx
export TELEGRAM_CHAT_ID=xxx
python stock_alert.py
```

## Notes
- `mode: "daily"` alerts on % move vs previous close (resets each day).
- `mode: "fixed"` alerts on % move vs a price you set yourself in `reference` (doesn't reset — good for long-term price targets).
- Once an alert fires for a ticker, it won't re-fire again until the next day (daily mode) or forever (fixed mode, until you edit the file) — edit `state.json` or `watchlist.json` to reset/change behavior.
