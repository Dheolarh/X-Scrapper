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
from .detect import extract_candidates, contains_launch_phrase, has_contact_address

TWEET_SELECTOR = 'article[data-testid="tweet"]'
TWEET_TEXT_SELECTOR = 'div[data-testid="tweetText"]'
TIME_SELECTOR = 'time'


class TwitterWatcher:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.driver = None

    def _build_driver(self):
        print("[twitter] Building Chrome driver...")
        opts = uc.ChromeOptions()
        
        # Use persistent user data directory to maintain sessions
        import os
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
        opts.add_argument("--remote-debugging-port=9222")
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
            # Default user agent for cloud instances
            opts.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
        self.driver = uc.Chrome(options=opts)
        self.driver.set_page_load_timeout(self.cfg.page_load_timeout)
        self.driver.implicitly_wait(self.cfg.implicit_wait)
        print("[twitter] Chrome driver ready with persistent session.")

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
        
        # First, try to go directly to home to check login status
        self.driver.get("https://x.com/home")
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
        
        # Now proceed with search
        print(f"[twitter] Now navigating to search URL: {self.cfg.search_url}")
        self.driver.get(self.cfg.search_url)
        try:
            WebDriverWait(self.driver, self.cfg.explicit_wait).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, TWEET_SELECTOR))
            )
            print("[twitter] Search page loaded.")
        except TimeoutException:
            print("[twitter] Timeout waiting for tweets to appear.")
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

    def collect_tweets(self, max_count: int = 40) -> List[Dict[str, Any]]:
        assert self.driver is not None
        print(f"[twitter] Collecting up to {max_count} tweets...")
        results = []
        last_height = 0
        retries = 0
        scroll_attempts = 0
        max_scroll_attempts = 15  # Increased from 5
        
        while len(results) < max_count and retries < 8:  # Increased retry limit
            articles = self.driver.find_elements(By.CSS_SELECTOR, TWEET_SELECTOR)
            print(f"[twitter] Found {len(articles)} tweet articles on page.")
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
                    
                    results.append({
                        "id": tid,
                        "text": text,
                        "username": username,
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
            
            # STRICT REQUIREMENT: Must have BOTH "coming soon" AND contract address
            if not contains_launch_phrase(text):
                continue
            if not has_contact_address(text):
                continue
                
            addrs, links = extract_candidates(text)
            matches.append({
                "id": t.get("id"), 
                "text": text, 
                "username": t.get("username", "Unknown User"),
                "mints": list(set(addrs + links))
            })
        print(f"[twitter] Found {len(matches)} matches with both 'coming soon' and contract address.")
        return matches
