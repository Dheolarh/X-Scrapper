import os
import time
import requests
from typing import Optional

class TelegramClient:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        if not self.bot_token or not self.chat_id:
            raise ValueError("Telegram bot token or chat id missing.")

    def send_message(self, text: str, disable_web_page_preview: bool = True) -> Optional[dict]:
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "disable_web_page_preview": disable_web_page_preview,
                "parse_mode": "HTML",
            }
            r = requests.post(url, json=payload, timeout=20)
            if r.status_code == 429:
                # simple backoff
                retry_after = r.json().get("parameters", {}).get("retry_after", 2)
                time.sleep(retry_after + 1)
                r = requests.post(url, json=payload, timeout=20)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"[telegram] failed to send: {e}")
            return None
