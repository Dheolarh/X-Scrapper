import os
from dataclasses import dataclass

@dataclass
class Config:
    # Telegram configuration - will be set by APIConfig
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    
    # Solana RPC (not used in current version)
    solana_rpc_url: str = ""

    # Twitter credentials - will be set by APIConfig
    twitter_username: str = ""
    twitter_password: str = ""
    twitter_email: str = ""

    # File paths
    cookies_path: str = "data/cookies.json"
    state_path: str = "data/state.json"
    user_data_dir: str = "data/chrome_profile"
    
    # Contact address requirement - will be set by APIConfig
    contact_address_required: bool = True

    # Search configuration - will be set by APIConfig
    search_query: str = ""
    search_url: str = ""

    # Timing configuration
    run_interval_sec: int = 600  # 10 minutes
    jitter_sec: int = 45

    # Browser configuration
    headless: bool = True
    user_agent: str = ""

    # Selenium timeouts
    page_load_timeout: int = 45
    implicit_wait: int = 5
    explicit_wait: int = 20
    
    def __post_init__(self):
        """Initialize config with environment variables if available (for APIConfig compatibility)"""
        # Only override defaults if environment variables are explicitly set
        if os.getenv("TELEGRAM_BOT_TOKEN"):
            self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if os.getenv("TELEGRAM_CHAT_ID"):
            self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        if os.getenv("TWITTER_USERNAME"):
            self.twitter_username = os.getenv("TWITTER_USERNAME", "")
        if os.getenv("TWITTER_PASSWORD"):
            self.twitter_password = os.getenv("TWITTER_PASSWORD", "")
        if os.getenv("TWITTER_EMAIL"):
            self.twitter_email = os.getenv("TWITTER_EMAIL", "")
        if os.getenv("SEARCH_QUERY"):
            self.search_query = os.getenv("SEARCH_QUERY", "")
        if os.getenv("SEARCH_URL"):
            self.search_url = os.getenv("SEARCH_URL", "")
        if os.getenv("CONTACT_ADDRESS_REQUIRED"):
            self.contact_address_required = os.getenv("CONTACT_ADDRESS_REQUIRED", "true").lower() == "true"
            
        # Optional overrides for other settings
        if os.getenv("RUN_INTERVAL_SEC"):
            self.run_interval_sec = int(os.getenv("RUN_INTERVAL_SEC", "600"))
        if os.getenv("JITTER_SEC"):
            self.jitter_sec = int(os.getenv("JITTER_SEC", "45"))
        if os.getenv("HEADLESS"):
            self.headless = os.getenv("HEADLESS", "true").lower() == "true"
        if os.getenv("USER_AGENT"):
            self.user_agent = os.getenv("USER_AGENT", "")
        if os.getenv("PAGE_LOAD_TIMEOUT"):
            self.page_load_timeout = int(os.getenv("PAGE_LOAD_TIMEOUT", "45"))
        if os.getenv("IMPLICIT_WAIT"):
            self.implicit_wait = int(os.getenv("IMPLICIT_WAIT", "5"))
        if os.getenv("EXPLICIT_WAIT"):
            self.explicit_wait = int(os.getenv("EXPLICIT_WAIT", "20"))
