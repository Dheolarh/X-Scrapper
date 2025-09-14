import os
import random
import time
from typing import List, Dict

from .config import Config
from .state import load_state, save_state
from .telegram_client import TelegramClient
from .twitter import TwitterWatcher


def format_message(item: Dict) -> str:
    username = item.get("username", "Unknown User")
    text = item.get("text", "").strip()
    mints = item.get("mints", [])
    timestamp = item.get("timestamp", "Unknown Time")
    post_url = item.get("post_url", "Unknown URL")
    likes = item.get("likes", "0")
    comments = item.get("comments", "0")
    reposts = item.get("reposts", "0")
    feed_source = item.get("feed_source", "Unknown Feed")
    
    # Format timestamp to be more readable
    formatted_time = timestamp
    try:
        from datetime import datetime
        import re
        # Try to parse ISO format datetime if available
        if 'T' in timestamp and 'Z' in timestamp:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = dt.strftime("%B %d, %Y at %I:%M %p UTC")
    except Exception:
        pass  # Keep original timestamp if parsing fails
    
    # Bold the new search keywords in post content
    keywords = [
        "pump", "sol", "coming soon", "launching soon", "launch", "project"
    ]
    formatted_text = text
    for keyword in keywords:
        # Case-insensitive replacement with bold formatting
        import re
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        formatted_text = pattern.sub(f"<b>{keyword}</b>", formatted_text)
    
    # Format contract addresses as inline quotes
    contracts_str = "\n".join(f"> {m}" for m in mints) if mints else "> No contract address found"
    
    # Format feed source with emoji
    feed_emoji = "🔥" if "Latest" in feed_source else "⭐" if "Top" in feed_source else "🏠" if "Homepage" in feed_source else "📡"
    
    # Build message with the new requested format
    message = f"""<b>USERNAME</b> || {username}

<b>POST CONTENT</b> || 
{formatted_text}

<b>TIME</b> || {formatted_time}

<b>REACTIONS</b> || Likes: {likes} -- Comments: {comments} -- Reposts: {reposts}

<b>FEED SOURCE</b> || {feed_emoji} {feed_source}

<b>POST URL:</b> {post_url}

<b>CONTRACT ADDRESS:</b>
{contracts_str}"""
    
    return message



def single_run(cfg: Config) -> int:
    print("[main] Loading state...")
    state = load_state(cfg.state_path)
    last_id = state.get("last_tweet_id")
    seen_mints = set(state.get("seen_mints", []))

    print("[main] Starting TwitterWatcher...")
    watcher = TwitterWatcher(cfg)
    watcher.start()
    try:
        print("[main] Opening search page...")
        watcher.open_search()
        print("[main] Collecting tweets from multiple feeds...")
        tweets = watcher.collect_tweets_multi_feed(max_count_per_feed=20)  # 20 tweets from each feed
        print(f"[main] Extracted {len(tweets)} tweets total from all feeds.")
        print("[main] Filtering matches...")
        matches = watcher.filter_matches(tweets)
        print(f"[main] Found {len(matches)} candidate matches.")

        # Allow duplicate tweets - just check for new mints
        new_items: List[Dict] = []
        for m in matches:
            new_mints = [x for x in m.get("mints", []) if x not in seen_mints]
            if new_mints:
                m["mints"] = new_mints
                new_items.append(m)
            # Also include tweets with no new mints but that haven't been seen recently
            elif not seen_mints or len(seen_mints) < 100:  # Allow some duplicates
                new_items.append(m)

        print(f"[main] {len(new_items)} new items to send to Telegram.")
        if not new_items:
            print("[main] No new items. Exiting.")
            return 0

        tg = TelegramClient(cfg.telegram_bot_token, cfg.telegram_chat_id)
        sent = 0
        for idx, item in enumerate(new_items):
            msg = format_message(item)
            print(f"[main] Sending item {idx+1}/{len(new_items)} to Telegram...")
            res = tg.send_message(msg)
            if res:
                print(f"[main] Sent successfully: {item.get('id')}")
                sent += 1
            else:
                print(f"[main] Failed to send: {item.get('id')}")
            # update state progressively
            if item.get("id"):
                last_id = max(last_id or "", item["id"])  # lexical fallback
            for mint in item.get("mints", []):
                seen_mints.add(mint)
            time.sleep(random.uniform(0.8, 1.6))

        print("[main] Saving state...")
        save_state(cfg.state_path, {
            "last_tweet_id": last_id,
            "seen_mints": sorted(seen_mints),
        })
        print(f"[main] Done. Sent {sent} messages.")
        return sent
    finally:
        print("[main] Stopping TwitterWatcher...")
        watcher.stop()


def main_loop():
    cfg = Config()
    while True:
        try:
            n = single_run(cfg)
            # jitter
            sleep_s = cfg.run_interval_sec + random.randint(-cfg.jitter_sec, cfg.jitter_sec)
            if sleep_s < 60:
                sleep_s = 60
            print(f"Cycle done. Sent {n}. Sleeping {sleep_s}s...")
            time.sleep(sleep_s)
        except KeyboardInterrupt:
            print("Stopped by user.")
            break
        except Exception as e:
            print(f"Run error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    # Single run if RUN_ONCE=1 set, else loop
    if os.getenv("RUN_ONCE", "0") == "1":
        sent = single_run(Config())
        print(f"Sent messages: {sent}")
    else:
        main_loop()
