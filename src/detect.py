import re
import os
from typing import List, Tuple, Optional

BASE58_RE = r"[1-9A-HJ-NP-Za-km-z]"
SOL_ADDR_RE = re.compile(rf"\b({BASE58_RE}{{32,44}})\b")
PUMPFUN_LINK_RE = re.compile(r"https?://pump\.fun/coin/([1-9A-HJ-NP-Za-km-z]{32,44})")

# Default launch phrases
DEFAULT_LAUNCH_PHRASES = (
    "coming soon",
    "launching soon", 
    "launch",
)

def get_launch_phrases():
    """Get launch phrases from environment or return empty list if none configured"""
    env_keywords = os.getenv('REQUIRED_POST_KEYWORDS')
    if env_keywords and env_keywords.strip():
        return [phrase.strip().lower() for phrase in env_keywords.split(',') if phrase.strip()]
    return []  # Return empty list instead of defaults if not configured


def extract_candidates(text: str) -> Tuple[List[str], List[str]]:
    """Return (sol_addresses, pumpfun_mints) found in the text."""
    if not text:
        return [], []
    addrs = [m.group(1) for m in SOL_ADDR_RE.finditer(text)]
    links = [m.group(1) for m in PUMPFUN_LINK_RE.finditer(text)]
    # de-dup preserve order
    def unique(seq):
        seen = set()
        out = []
        for x in seq:
            if x not in seen:
                out.append(x)
                seen.add(x)
        return out

    return unique(addrs), unique(links)


def contains_launch_phrase(text: str) -> bool:
    """Check if text contains any launch-related phrases"""
    launch_phrases = get_launch_phrases()
    t = text.lower()
    return any(phrase in t for phrase in launch_phrases)


def has_contact_address(text: str) -> bool:
    """Check if text contains any contract address"""
    addrs, links = extract_candidates(text)
    return len(addrs) > 0 or len(links) > 0
