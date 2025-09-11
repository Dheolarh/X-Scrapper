# TweetScrape

Headless Selenium automation that watches X/Twitter Live search for pump.fun-related Solana launches and posts matches to a Telegram channel.

## Features
- Headless, minimal jitter and scrolling to reduce detection
- Live search URL for queries like `pump fun` / `pump.fun` with launch phrases
- Extracts pump.fun coin links and Base58 Solana mints in text
- De-duplicates with state file and tracks last tweet id
- Sends formatted messages to Telegram via Bot API

## Quick start (Windows PowerShell)

1. Create and activate a Python environment (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Create your `.env` from the template and fill credentials:

```powershell
Copy-Item .env.example .env
# Edit .env to set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
```

3. First-time cookie bootstrap (optional but recommended):
- Temporarily set `HEADLESS=false` in `.env`.
- Run a single cycle to log in to X manually if prompted; then we’ll persist cookies in a follow-up iteration.

4. Run once to test:

```powershell
$env:RUN_ONCE="1"; python -m src.main
```

5. Continuous run (loop every ~10 minutes with jitter):

```powershell
python -m src.main
```

6. Schedule (Windows Task Scheduler):
- Create a task to run `python -m src.main` in the project folder.
- Set to run every 10 minutes. Ensure your virtualenv path is used or python is installed system-wide.

## Notes
- This tool uses undetected-chromedriver; ensure Chrome/Edge is installed. If a mismatch occurs, update your browser or pin undetected-chromedriver.
- DOM changes on X/Twitter can break selectors. Update `TWEET_SELECTOR` and `TWEET_TEXT_SELECTOR` in `src/twitter.py` if needed.
- Use responsibly and respect site terms.
