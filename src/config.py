import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    solana_rpc_url: str = os.getenv("SOLANA_RPC_URL", "")

    twitter_username: str = os.getenv("TWITTER_USERNAME", "")
    twitter_password: str = os.getenv("TWITTER_PASSWORD", "")
    twitter_email: str = os.getenv("TWITTER_EMAIL", "")

    cookies_path: str = os.getenv("COOKIES_PATH", "data/cookies.json")
    state_path: str = os.getenv("STATE_PATH", "data/state.json")
    user_data_dir: str = os.getenv("USER_DATA_DIR", "data/chrome_profile")

    search_query: str = os.getenv(
        "SEARCH_QUERY",
        'pump fun OR pumpfun OR "pump.fun" ("launch soon" OR "coming soon") -filter:replies',
    )
    search_url: str = os.getenv(
        "SEARCH_URL",
        "https://x.com/search?q=pump%20fun%20OR%20pumpfun%20OR%20%22pump.fun%22%20(%22launch%20soon%22%20OR%20%22coming%20soon%22)%20-filter%3Areplies&f=live",
    )

    run_interval_sec: int = int(os.getenv("RUN_INTERVAL_SEC", "600"))
    jitter_sec: int = int(os.getenv("JITTER_SEC", "45"))

    headless: bool = os.getenv("HEADLESS", "true").lower() == "true"
    user_agent: str = os.getenv("USER_AGENT", "")

    # Selenium timeouts
    page_load_timeout: int = int(os.getenv("PAGE_LOAD_TIMEOUT", "45"))
    implicit_wait: int = int(os.getenv("IMPLICIT_WAIT", "5"))
    explicit_wait: int = int(os.getenv("EXPLICIT_WAIT", "20"))
