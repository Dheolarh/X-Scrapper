import re
from typing import List, Tuple, Optional

BASE58_RE = r"[1-9A-HJ-NP-Za-km-z]"
SOL_ADDR_RE = re.compile(rf"\b({BASE58_RE}{{32,44}})\b")
PUMPFUN_LINK_RE = re.compile(r"https?://pump\.fun/coin/([1-9A-HJ-NP-Za-km-z]{32,44})")

LAUNCH_PHRASES = (
    "coming soon",
    "launching soon", 
    "launch",
)


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
    t = text.lower()
    return any(phrase in t for phrase in LAUNCH_PHRASES)


def has_contact_address(text: str) -> bool:
    """Check if text contains any contract address"""
    addrs, links = extract_candidates(text)
    return len(addrs) > 0 or len(links) > 0
