import random
import time
from typing import List, Dict, Any, Optional

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from .config import Config
from . import session as sess
from .detect import extract_candidates, contains_launch_phrase, has_contact_address, get_launch_phrases

TWEET_SELECTOR = 'article[data-testid="tweet"]'
TWEET_TEXT_SELECTOR = 'div[data-testid="tweetText"]'
TIME_SELECTOR = 'time'


class TwitterWatcher:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.driver = None

    def _build_driver(self):
        print("[twitter] Building Chrome driver...")
        import os  # Import os at the beginning
        opts = uc.ChromeOptions()
        
        # Specify Chrome binary path explicitly
        chrome_binary = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        if os.path.exists(chrome_binary):
            opts.binary_location = chrome_binary
            print(f"[twitter] Using Chrome binary: {chrome_binary}")
        
        # Use persistent user data directory to maintain sessions
        os.makedirs(self.cfg.user_data_dir, exist_ok=True)
        opts.add_argument(f"--user-data-dir={os.path.abspath(self.cfg.user_data_dir)}")
        print(f"[twitter] Using user data directory: {os.path.abspath(self.cfg.user_data_dir)}")
        
        # Cloud-friendly options
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--disable-extensions")
        opts.add_argument("--disable-plugins")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        
        # Add more stable options for better reliability
        opts.add_argument("--disable-background-timer-throttling")
        opts.add_argument("--disable-backgrounding-occluded-windows")
        opts.add_argument("--disable-renderer-backgrounding")
        opts.add_argument("--disable-features=TranslateUI")
        opts.add_argument("--disable-ipc-flooding-protection")
        opts.add_argument("--no-first-run")
        opts.add_argument("--no-default-browser-check")
        
        # Set page load strategy for faster loading
        opts.page_load_strategy = 'eager'  # Don't wait for all resources
        
        # Remove conflicting remote debugging port
        # opts.add_argument("--remote-debugging-port=9222")
        opts.add_argument("--window-size=1920,1080")
        
        if self.cfg.headless:
            opts.add_argument("--headless=new")
            opts.add_argument("--disable-web-security")
            opts.add_argument("--allow-running-insecure-content")
        else:
            opts.add_argument("--start-maximized")
            
        if self.cfg.user_agent:
            opts.add_argument(f"--user-agent={self.cfg.user_agent}")
        else:
            # Default user agent for Windows
            opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
        try:
            self.driver = uc.Chrome(options=opts)
            # Set more reasonable timeouts
            self.driver.set_page_load_timeout(30)  # Reduced from default
            self.driver.implicitly_wait(self.cfg.implicit_wait)
            print("[twitter] Chrome driver ready with persistent session.")
        except Exception as e:
            print(f"[twitter] Failed to create Chrome driver: {e}")
            # Try with simpler options as fallback
            opts = uc.ChromeOptions()
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            if chrome_binary and os.path.exists(chrome_binary):
                opts.binary_location = chrome_binary
            try:
                self.driver = uc.Chrome(options=opts)
                self.driver.set_page_load_timeout(30)
                print("[twitter] Chrome driver created with fallback options.")
            except Exception as fallback_error:
                print(f"[twitter] Fallback Chrome driver creation also failed: {fallback_error}")
                raise

    def _jitter(self, a=0.5, b=1.4):
        time.sleep(random.uniform(a, b))

    def start(self):
        print("[twitter] Starting watcher...")
        if self.driver is None:
            self._build_driver()

    def stop(self):
        print("[twitter] Stopping watcher...")
        try:
            if self.driver:
                self.driver.quit()
        finally:
            self.driver = None

    def open_search(self):
        assert self.driver is not None
        print("[twitter] Checking if already logged in...")
        
        # Try to navigate to Twitter with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"[twitter] Attempt {attempt + 1}/{max_retries} to load Twitter...")
                # First, try to go directly to home to check login status
                self.driver.get("https://x.com/home")
                print("[twitter] Successfully loaded Twitter homepage")
                break
            except Exception as e:
                print(f"[twitter] Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    print("[twitter] All attempts failed. Trying simple approach...")
                    try:
                        # Last resort: try with a shorter timeout
                        self.driver.set_page_load_timeout(15)
                        self.driver.get("https://x.com")
                        time.sleep(5)
                        print("[twitter] Loaded basic Twitter page as fallback")
                    except Exception as final_error:
                        print(f"[twitter] Final attempt also failed: {final_error}")
                        raise
                else:
                    time.sleep(3)  # Wait before retry
        
        time.sleep(3)
        
        # Check if we're already logged in by looking for home page elements
        if self._is_logged_in():
            print("[twitter] Already logged in! Skipping login process.")
        else:
            print("[twitter] Not logged in, starting login process...")
            self._execute_login_script()
        
        # Wait 20 seconds as requested before search
        print("[twitter] Waiting 20 seconds before performing search...")
        time.sleep(20)

        # Generate search URL dynamically from search query instead of using cached URL
        search_query = self.cfg.search_query
        from urllib.parse import quote_plus
        encoded_query = quote_plus(search_query)
        dynamic_search_url = f"https://x.com/search?q={encoded_query}&f=live"
        
        # Now proceed with search
        print(f"[twitter] Now navigating to search URL: {dynamic_search_url}")
        search_load_attempts = 0
        max_search_load_attempts = 3
        
        while search_load_attempts < max_search_load_attempts:
            search_load_attempts += 1
            print(f"[twitter] Loading search page (attempt {search_load_attempts}/{max_search_load_attempts})")
            
            self.driver.get(dynamic_search_url)
            try:
                WebDriverWait(self.driver, self.cfg.explicit_wait).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, TWEET_SELECTOR))
                )
                print("[twitter] Search page loaded successfully.")
                break  # Success, exit the retry loop
                
            except TimeoutException:
                print(f"[twitter] Timeout waiting for tweets to appear (attempt {search_load_attempts})")
                if search_load_attempts < max_search_load_attempts:
                    print("[twitter] Retrying search page load...")
                    time.sleep(3)  # Wait before retry
                else:
                    print("[twitter] Failed to load search page after all attempts.")
        
        # Save cookies opportunistically
        try:
            sess.save_cookies(self.driver, self.cfg.cookies_path)
            print("[twitter] Cookies saved.")
        except Exception as e:
            print(f"[twitter] Cookie save error: {e}")

    def _is_logged_in(self) -> bool:
        """Check if we're already logged in by looking for home page indicators"""
        try:
            # Look for elements that only appear when logged in
            logged_in_indicators = [
                '[data-testid="SideNav_NewTweet_Button"]',  # Tweet button
                '[data-testid="AppTabBar_Home_Link"]',       # Home link in sidebar
                '[data-testid="primaryColumn"]',             # Main timeline column
                '[data-testid="tweetTextarea_0"]',           # Tweet compose box
                'nav[role="navigation"]'                     # Main navigation
            ]
            
            for selector in logged_in_indicators:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"[twitter] Found logged-in indicator: {selector}")
                    return True
                    
            # Also check URL - if we're redirected to login, we're not logged in
            current_url = self.driver.current_url
            if "login" in current_url or "flow" in current_url:
                print(f"[twitter] Login required - current URL: {current_url}")
                return False
                
            print("[twitter] No logged-in indicators found")
            return False
            
        except Exception as e:
            print(f"[twitter] Error checking login status: {e}")
            return False

    def _execute_login_script(self):
        """Execute the login.py logic using the current driver"""
        print("[twitter] Executing login.py approach...")
        try:
            url = "https://x.com/i/flow/login"
            self.driver.get(url)
            print(f"[twitter] Navigated to {url}")
            time.sleep(3)  # Give page time to load

            # Step 1: Enter username
            username = WebDriverWait(self.driver, 20).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))
            )
            username.send_keys(self.cfg.twitter_username)
            username.send_keys(Keys.ENTER)
            print("[twitter] Username entered and submitted.")
            time.sleep(5)  # Wait longer for next page to load

            # Step 2: Check if email verification is needed
            print(f"[twitter] Current URL after username: {self.driver.current_url}")
            
            # Check for email verification field first
            try:
                # Look for email verification input
                email_input = WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[data-testid="ocfEnterTextTextInput"]'))
                )
                print("[twitter] Email verification step detected.")
                
                if self.cfg.twitter_email:
                    email_input.send_keys(self.cfg.twitter_email)
                    email_input.send_keys(Keys.ENTER)
                    print("[twitter] Email entered for verification.")
                    time.sleep(5)  # Wait for verification
                else:
                    print("[twitter] ERROR: Email verification required but TWITTER_EMAIL not configured!")
                    raise Exception("Email verification required but TWITTER_EMAIL not set in config")
                    
            except TimeoutException:
                print("[twitter] No email verification required, proceeding to password.")
            
            # Step 3: Enter password - try multiple selectors
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[autocomplete="current-password"]'
            ]
            
            password = None
            for selector in password_selectors:
                try:
                    print(f"[twitter] Trying password selector: {selector}")
                    password = WebDriverWait(self.driver, 15).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"[twitter] Found password field with selector: {selector}")
                    break
                except TimeoutException:
                    print(f"[twitter] Password selector {selector} not found, trying next...")
                    continue
                    
            if not password:
                # Take a screenshot for debugging
                try:
                    self.driver.save_screenshot('data/login_password_fail.png')
                    print("[twitter] Screenshot saved to data/login_password_fail.png")
                except:
                    pass
                raise Exception("Could not find password field with any selector")

            # Step 4: Enter password
            password.send_keys(self.cfg.twitter_password)
            password.send_keys(Keys.ENTER)
            print("[twitter] Password entered and submitted.")
            time.sleep(3)

            print("[twitter] Login script execution complete.")
            print(f"[twitter] Final URL: {self.driver.current_url}")
            
        except Exception as e:
            print(f"[twitter] Login script execution failed: {e}")
            # Take screenshot on failure
            try:
                self.driver.save_screenshot('data/login_error.png')
                print("[twitter] Error screenshot saved to data/login_error.png")
            except:
                pass
            raise

    def _needs_login(self) -> bool:
        # Check for login form presence
        try:
            login_input = self.driver.find_elements(By.NAME, "text")
            return bool(login_input)
        except Exception:
            return False

    def _do_login(self):
        cfg = self.cfg
        try:
            print("[twitter] Starting login using Login.py approach...")
            # Go directly to login URL
            url = "https://x.com/i/flow/login"
            self.driver.get(url)
            
            # Enter username using the better selector
            print("[twitter] Waiting for username field...")
            username = WebDriverWait(self.driver, 20).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))
            )
            username.send_keys(cfg.twitter_username)
            username.send_keys(Keys.ENTER)
            print("[twitter] Username entered and submitted.")
            
            # Enter password
            print("[twitter] Waiting for password field...")
            password = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))
            )
            password.send_keys(cfg.twitter_password)
            password.send_keys(Keys.ENTER)
            print("[twitter] Password entered and submitted.")
            
            # Wait 20 seconds for login to complete as requested
            print("[twitter] Waiting 20 seconds for login to complete...")
            time.sleep(20)
            print(f"[twitter] Login complete. Current URL: {self.driver.current_url}")
            
        except Exception as e:
            print(f"[twitter] Login automation failed: {e}")
            raise Exception(f"[twitter] Login failed: {e}")

    def collect_tweets_multi_feed(self, max_count_per_feed: int = 20) -> List[Dict[str, Any]]:
        """Collect tweets from multiple feeds: Latest, Top, and Homepage"""
        assert self.driver is not None
        all_tweets = []
        
        # Get the search query from config
        search_query = self.cfg.search_query
        from urllib.parse import quote_plus
        encoded_query = quote_plus(search_query)
        
        feeds = [
            {
                "name": "Latest/Live Feed", 
                "url": f"https://x.com/search?q={encoded_query}&f=live",
                "description": "Most recent tweets with your search query"
            },
            {
                "name": "Top Feed", 
                "url": f"https://x.com/search?q={encoded_query}",
                "description": "Popular/trending tweets with your search query"
            },
            {
                "name": "Homepage Feed", 
                "url": "https://x.com/home",
                "description": "Your personalized timeline"
            }
        ]
        
        for i, feed in enumerate(feeds, 1):
            print(f"\n[twitter] === FEED {i}/3: {feed['name']} ===")
            print(f"[twitter] {feed['description']}")
            print(f"[twitter] URL: {feed['url']}")
            
            try:
                # Navigate to the feed
                print(f"[twitter] Loading {feed['name']}...")
                self.driver.get(feed['url'])
                time.sleep(5)  # Wait for page to load
                
                # Wait for tweets to appear
                try:
                    WebDriverWait(self.driver, 15).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, TWEET_SELECTOR))
                    )
                    print(f"[twitter] {feed['name']} loaded successfully")
                except TimeoutException:
                    print(f"[twitter] No tweets found in {feed['name']}, skipping...")
                    continue
                
                # Collect tweets from this feed
                feed_tweets = self.collect_tweets(max_count=max_count_per_feed)
                print(f"[twitter] Collected {len(feed_tweets)} tweets from {feed['name']}")
                
                # Add feed info to each tweet
                for tweet in feed_tweets:
                    tweet['feed_source'] = feed['name']
                    tweet['feed_url'] = feed['url']
                
                all_tweets.extend(feed_tweets)
                
                # Short break between feeds
                if i < len(feeds):
                    print(f"[twitter] Waiting 3 seconds before next feed...")
                    time.sleep(3)
                    
            except Exception as e:
                print(f"[twitter] Error collecting from {feed['name']}: {e}")
                continue
        
        print(f"\n[twitter] === MULTI-FEED COLLECTION COMPLETE ===")
        print(f"[twitter] Total tweets collected: {len(all_tweets)}")
        for feed in feeds:
            feed_count = len([t for t in all_tweets if t.get('feed_source') == feed['name']])
            print(f"[twitter] - {feed['name']}: {feed_count} tweets")
        
        return all_tweets

    def collect_tweets(self, max_count: int = 40) -> List[Dict[str, Any]]:
        assert self.driver is not None
        print(f"[twitter] Collecting up to {max_count} tweets...")
        results = []
        last_height = 0
        retries = 0
        scroll_attempts = 0
        max_scroll_attempts = 15  # Increased from 5
        refresh_attempts = 0
        max_refresh_attempts = 3  # Max times to refresh search page
        
        while len(results) < max_count and retries < 8:  # Increased retry limit
            articles = self.driver.find_elements(By.CSS_SELECTOR, TWEET_SELECTOR)
            print(f"[twitter] Found {len(articles)} tweet articles on page.")
            
            # If no tweets found and we haven't scrolled much, try refreshing the search page
            if len(articles) == 0 and scroll_attempts < 3 and refresh_attempts < max_refresh_attempts:
                print(f"[twitter] No tweets found on search page. Refreshing... (attempt {refresh_attempts + 1}/{max_refresh_attempts})")
                refresh_attempts += 1
                
                # Refresh the search page
                self.driver.refresh()
                time.sleep(5)  # Wait for page to reload
                
                # Wait for tweets to appear or timeout
                try:
                    WebDriverWait(self.driver, 15).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, TWEET_SELECTOR))
                    )
                    print("[twitter] Search page refreshed and tweets loaded.")
                except TimeoutException:
                    print("[twitter] Timeout waiting for tweets after refresh. Continuing...")
                
                continue  # Restart the loop after refresh
            
            for art in articles:
                try:
                    tid = art.get_attribute("data-tweet-id") or art.get_attribute("id") or None
                    # fallback: use time href as unique-ish id
                    time_el = art.find_element(By.CSS_SELECTOR, TIME_SELECTOR)
                    tid = tid or time_el.get_attribute("datetime") or time_el.get_attribute("aria-label")
                    text_el = art.find_element(By.CSS_SELECTOR, TWEET_TEXT_SELECTOR)
                    text = text_el.text
                    
                    # Extract username
                    username = "Unknown User"
                    try:
                        # Try multiple selectors for username
                        username_selectors = [
                            'div[data-testid="User-Name"] span:not([role="img"])',
                            '[data-testid="User-Name"] span',
                            'div[data-testid="User-Names"] span:first-child',
                            'a[role="link"] span'
                        ]
                        for selector in username_selectors:
                            username_els = art.find_elements(By.CSS_SELECTOR, selector)
                            if username_els:
                                username_text = username_els[0].text.strip()
                                if username_text and not username_text.startswith('@'):
                                    username = username_text
                                    break
                    except Exception:
                        pass
                    
                    # Extract timestamp
                    timestamp = "Unknown Time"
                    try:
                        time_element = art.find_element(By.CSS_SELECTOR, TIME_SELECTOR)
                        timestamp = time_element.get_attribute("datetime") or time_element.get_attribute("title") or time_element.text
                    except Exception:
                        pass
                    
                    # Extract post URL
                    post_url = "Unknown URL"
                    try:
                        # Look for the permalink to the tweet
                        time_link = art.find_element(By.CSS_SELECTOR, 'time').find_element(By.XPATH, '..')
                        if time_link.tag_name == 'a':
                            href = time_link.get_attribute('href')
                            if href:
                                post_url = href
                    except Exception:
                        pass
                    
                    # Extract engagement metrics (likes, comments, reposts)
                    likes = "0"
                    comments = "0"
                    reposts = "0"
                    try:
                        # Twitter engagement buttons are usually in a specific group
                        engagement_buttons = art.find_elements(By.CSS_SELECTOR, 'div[role="group"] button')
                        for button in engagement_buttons:
                            aria_label = button.get_attribute('aria-label') or ""
                            # Parse engagement counts from aria-labels
                            if 'like' in aria_label.lower():
                                # Extract number from "123 likes" or similar
                                import re
                                match = re.search(r'(\d+)', aria_label)
                                if match:
                                    likes = match.group(1)
                            elif 'repl' in aria_label.lower() or 'comment' in aria_label.lower():
                                match = re.search(r'(\d+)', aria_label)
                                if match:
                                    comments = match.group(1)
                            elif 'repost' in aria_label.lower() or 'retweet' in aria_label.lower():
                                match = re.search(r'(\d+)', aria_label)
                                if match:
                                    reposts = match.group(1)
                    except Exception:
                        pass
                    
                    results.append({
                        "id": tid,
                        "text": text,
                        "username": username,
                        "timestamp": timestamp,
                        "post_url": post_url,
                        "likes": likes,
                        "comments": comments,
                        "reposts": reposts,
                    })
                except Exception:
                    continue

            # More aggressive scrolling
            scroll_distance = random.randint(800, 1500)  # Increased scroll distance
            self.driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
            print(f"[twitter] Scrolled {scroll_distance}px. Collected {len(results)} tweets so far.")
            self._jitter(1.0, 2.5)  # Longer wait between scrolls
            
            # Check if we've scrolled to more content
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                retries += 1
                print(f"[twitter] No new content loaded. Retry {retries}/8")
                # Try scrolling to bottom then back up to trigger loading
                if retries % 2 == 0:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    self.driver.execute_script(f"window.scrollBy(0, -{scroll_distance});")
            else:
                retries = 0
                print(f"[twitter] Page height changed from {last_height} to {new_height}")
            
            last_height = new_height
            scroll_attempts += 1
            
            if scroll_attempts >= max_scroll_attempts:
                print(f"[twitter] Reached max scroll attempts ({max_scroll_attempts})")
                break
                
        print(f"[twitter] Finished collecting. Got {len(results)} tweets after {scroll_attempts} scroll attempts.")
        return results

    def filter_matches(self, tweets: List[Dict[str, Any]]):
        print(f"[twitter] Filtering {len(tweets)} tweets for matches...")
        matches = []
        for t in tweets:
            text = t.get("text", "")
            
            # Check for contract address only if required
            if self.cfg.contact_address_required and not has_contact_address(text):
                continue
                
            # Check for launch phrases only if keywords are configured
            launch_phrases = get_launch_phrases()
            if launch_phrases and len(launch_phrases) > 0:
                # If launch phrases are configured, require them
                if not contains_launch_phrase(text):
                    continue
            # If no launch phrases configured, skip this filter
                
            addrs, links = extract_candidates(text)
            matches.append({
                "id": t.get("id"), 
                "text": text, 
                "username": t.get("username", "Unknown User"),
                "timestamp": t.get("timestamp", "Unknown Time"),
                "post_url": t.get("post_url", "Unknown URL"),
                "likes": t.get("likes", "0"),
                "comments": t.get("comments", "0"),
                "reposts": t.get("reposts", "0"),
                "feed_source": t.get("feed_source", "Unknown Feed"),
                "feed_url": t.get("feed_url", ""),
                "mints": list(set(addrs + links))
            })
        
        # Update the log message based on filtering criteria
        filter_msg = []
        if get_launch_phrases():
            filter_msg.append("launch keywords")
        if self.cfg.contact_address_required:
            filter_msg.append("contract address")
        
        if filter_msg:
            print(f"[twitter] Found {len(matches)} matches with {' and '.join(filter_msg)}.")
        else:
            print(f"[twitter] Found {len(matches)} matches with contract address (no keyword filter).")
        return matches
