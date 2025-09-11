import json
from pathlib import Path
from typing import Dict, Any


def load_state(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"last_tweet_id": None, "seen_mints": []}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"last_tweet_id": None, "seen_mints": []}


def save_state(path: str, state: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
