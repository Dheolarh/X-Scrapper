import json
from pathlib import Path
from typing import Any, List
from selenium.webdriver.remote.webdriver import WebDriver


def save_cookies(driver: WebDriver, path: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    cookies = driver.get_cookies()
    p.write_text(json.dumps(cookies, indent=2), encoding="utf-8")


def load_cookies(driver: WebDriver, path: str, domain_hint: str = ".x.com") -> bool:
    p = Path(path)
    if not p.exists():
        return False
    try:
        cookies: List[dict[str, Any]] = json.loads(p.read_text(encoding="utf-8"))
        for c in cookies:
            # Selenium requires we're on the matching domain before adding cookies.
            # Callers should first driver.get("https://x.com") then load_cookies.
            # Normalize domain if needed.
            if c.get("domain") and not c["domain"].startswith("."):
                c["domain"] = "." + c["domain"]
            # Remove expiry None to avoid type issues
            if c.get("expiry") is None:
                c.pop("expiry", None)
            driver.add_cookie(c)
        return True
    except Exception:
        return False
