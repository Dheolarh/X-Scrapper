from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time
import os
import signal
import sys
import atexit
from typing import Dict, Any
import json

from src.config import Config
from src.main import single_run
from src.state import load_state, save_state

app = Flask(__name__)
CORS(app)  # Enable CORS for browser extensions

# Global state
automation_enabled = False
automation_thread = None
current_config = None
scrape_running = False
latest_results = []  # Store latest scraping results

# Cleanup function for graceful shutdown
def cleanup_and_exit():
    """Clean up resources and exit gracefully"""
    global automation_enabled, automation_thread
    
    print("\n[API] Shutting down server...")
    
    # Stop automation if running
    if automation_enabled:
        automation_enabled = False
        if automation_thread and automation_thread.is_alive():
            print("[API] Stopping automation thread...")
            automation_thread.join(timeout=5)
    
    print("[API] Server shutdown complete.")
    sys.exit(0)

# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"[API] Received signal {signum}")
    cleanup_and_exit()

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
if hasattr(signal, 'SIGBREAK'):  # Windows
    signal.signal(signal.SIGBREAK, signal_handler)

# Register atexit handler as backup
atexit.register(cleanup_and_exit)

class APIConfig:
    """Configuration class for API-received settings"""
    def __init__(self, config_data: Dict[str, Any]):
        # Store the original config data
        self.config_data = config_data
        
        # Don't modify environment variables, instead create config directly
        telegram_token = config_data['telegram'].get('botToken', '') if 'telegram' in config_data else ''
        telegram_chat = config_data['telegram'].get('chatId', '') if 'telegram' in config_data else ''
        
        twitter_username = config_data['twitter'].get('username', '') if 'twitter' in config_data else ''
        twitter_email = config_data['twitter'].get('email', '') if 'twitter' in config_data else ''
        twitter_password = config_data['twitter'].get('password', '') if 'twitter' in config_data else ''
        
        # Handle keywords properly
        search_keywords = config_data['keywords'].get('required', []) if 'keywords' in config_data else []
        required_post_keywords = config_data['keywords'].get('optional', []) if 'keywords' in config_data else []
        
        # Handle contact address requirement (default to True if not specified)
        contact_address_required = config_data.get('contactAddressRequired', True)
        
        # Build search query from search keywords
        search_query = ''
        search_url = ''
        if search_keywords:
            search_query = ' OR '.join([f'"{keyword}"' if ' ' in keyword else keyword for keyword in search_keywords])
            # Build URL-encoded search URL
            import urllib.parse
            encoded_query = urllib.parse.quote(search_query)
            search_url = f"https://x.com/search?q={encoded_query}&f=live"
            
            print(f"[API] Updated search configuration:")
            print(f"[API] - Search Keywords: {search_keywords}")
            print(f"[API] - Generated Search Query: {search_query}")
            print(f"[API] - Generated Search URL: {search_url}")
        else:
            print(f"[API] Warning: No search keywords provided. Using empty search query.")
        
        # Update environment variables temporarily for this config
        os.environ['TELEGRAM_BOT_TOKEN'] = telegram_token
        os.environ['TELEGRAM_CHAT_ID'] = telegram_chat
        os.environ['TWITTER_USERNAME'] = twitter_username
        os.environ['TWITTER_EMAIL'] = twitter_email
        os.environ['TWITTER_PASSWORD'] = twitter_password
        
        # Always set SEARCH_QUERY and SEARCH_URL, even if empty, to override defaults
        os.environ['SEARCH_QUERY'] = search_query
        os.environ['SEARCH_URL'] = search_url
        
        # Set contact address requirement
        os.environ['CONTACT_ADDRESS_REQUIRED'] = str(contact_address_required).lower()
        print(f"[API] - Contact Address Required: {contact_address_required}")
        if required_post_keywords:
            os.environ['REQUIRED_POST_KEYWORDS'] = ','.join(required_post_keywords)
            print(f"[API] - Set REQUIRED_POST_KEYWORDS: {required_post_keywords}")
        else:
            os.environ.pop('REQUIRED_POST_KEYWORDS', None)
            print(f"[API] - Cleared REQUIRED_POST_KEYWORDS (no optional keywords provided)")
        
        # Set contact address requirement
        print(f"[API] - Contact Address Required: {contact_address_required}")
        
        # Create Config object with updated environment
        self.config = Config()
        
        # Store the values we actually set
        self.search_query = search_query
        self.search_url = search_url
        self.required_post_keywords = required_post_keywords
        self.contact_address_required = contact_address_required

def automation_worker():
    """Background worker for automation mode"""
    global automation_enabled, scrape_running, current_config, latest_results
    
    while automation_enabled:
        if current_config and not scrape_running:
            try:
                scrape_running = True
                add_activity_event("🤖 Running automated scrape...", "info")
                print("[API] Running automated scrape...")
                result = single_run(current_config.config, return_results=True)
                sent_count, results = result if isinstance(result, tuple) else (result, [])
                latest_results[:] = results  # Update global results
                add_activity_event(f"✅ Automated scrape completed - sent {sent_count} messages", "success")
                print("[API] Automated scrape completed")
            except Exception as e:
                add_activity_event(f"❌ Automated scrape failed: {str(e)}", "error")
                print(f"[API] Automation error: {e}")
            finally:
                scrape_running = False
        
        # Wait 10 minutes (600 seconds) between runs
        for i in range(600):
            if not automation_enabled:
                break
            time.sleep(1)

@app.route('/status', methods=['GET'])
def health_check():
    """Backend health check endpoint"""
    return jsonify({
        'status': 'online',
        'message': 'Backend is running',
        'automation_enabled': automation_enabled,
        'scrape_running': scrape_running
    })

@app.route('/api/config', methods=['POST'])
def save_config():
    """Save configuration from frontend"""
    global current_config
    
    try:
        config_data = request.get_json()
        
        if not config_data:
            return jsonify({'error': 'No configuration data provided'}), 400
        
        # Validate required fields
        required_fields = ['telegram', 'twitter', 'keywords']
        for field in required_fields:
            if field not in config_data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create API config that updates environment variables
        current_config = APIConfig(config_data)
        
        # Save config to file for persistence
        config_file = 'api_config.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        return jsonify({
            'status': 'success',
            'message': 'Configuration saved successfully',
            'config': config_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config/debug', methods=['GET'])
def debug_config():
    """Debug endpoint to see current configuration"""
    return jsonify({
        'environment_vars': {
            'SEARCH_QUERY': os.environ.get('SEARCH_QUERY'),
            'SEARCH_URL': os.environ.get('SEARCH_URL'),
            'REQUIRED_POST_KEYWORDS': os.environ.get('REQUIRED_POST_KEYWORDS'),
            'TELEGRAM_BOT_TOKEN': '***' if os.environ.get('TELEGRAM_BOT_TOKEN') else None,
            'TELEGRAM_CHAT_ID': os.environ.get('TELEGRAM_CHAT_ID'),
            'TWITTER_USERNAME': os.environ.get('TWITTER_USERNAME'),
            'TWITTER_EMAIL': os.environ.get('TWITTER_EMAIL'),
            'TWITTER_PASSWORD': '***' if os.environ.get('TWITTER_PASSWORD') else None,
        },
        'has_current_config': current_config is not None,
        'api_config_file_exists': os.path.exists('api_config.json'),
        'current_search_query_in_use': current_config.search_query if current_config else None,
        'current_search_url_in_use': current_config.search_url if current_config else None
    })

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    try:
        config_file = 'api_config.json'
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            return jsonify({'config': config_data})
        else:
            return jsonify({'config': None})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/results', methods=['GET'])
def get_results():
    """Get latest scraping results"""
    global latest_results
    try:
        return jsonify({
            'status': 'success',
            'results': latest_results,
            'count': len(latest_results),
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/credentials/clear-session', methods=['POST'])
def clear_session():
    """Clear stored browser sessions and cached login data"""
    try:
        import shutil
        
        # Clear Chrome user data directory
        user_data_dir = os.getenv("USER_DATA_DIR", "data/chrome_profile")
        if os.path.exists(user_data_dir):
            shutil.rmtree(user_data_dir)
            print(f"[API] Cleared Chrome profile directory: {user_data_dir}")
        
        # Clear cookies file
        cookies_path = os.getenv("COOKIES_PATH", "data/cookies.json")
        if os.path.exists(cookies_path):
            os.remove(cookies_path)
            print(f"[API] Cleared cookies file: {cookies_path}")
        
        # Clear state file
        state_path = os.getenv("STATE_PATH", "data/state.json")
        if os.path.exists(state_path):
            os.remove(state_path)
            print(f"[API] Cleared state file: {state_path}")
        
        return jsonify({
            'status': 'success',
            'message': 'Browser sessions and cached data cleared successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/credentials/validate', methods=['POST'])
def validate_credentials():
    """Validate if credentials have changed and clear sessions if needed"""
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Check if we have stored previous credentials
        credentials_file = 'stored_credentials.json'
        previous_credentials = {}
        
        if os.path.exists(credentials_file):
            with open(credentials_file, 'r') as f:
                previous_credentials = json.load(f)
        
        new_credentials = {
            'twitter_username': request_data.get('twitter', {}).get('username', ''),
            'twitter_email': request_data.get('twitter', {}).get('email', ''),
            'telegram_bot_token': request_data.get('telegram', {}).get('botToken', ''),
            'telegram_chat_id': request_data.get('telegram', {}).get('chatId', '')
        }
        
        # Check if Twitter credentials have changed
        twitter_changed = (
            previous_credentials.get('twitter_username') != new_credentials['twitter_username'] or
            previous_credentials.get('twitter_email') != new_credentials['twitter_email']
        )
        
        # Check if Telegram credentials have changed
        telegram_changed = (
            previous_credentials.get('telegram_bot_token') != new_credentials['telegram_bot_token'] or
            previous_credentials.get('telegram_chat_id') != new_credentials['telegram_chat_id']
        )
        
        response_data = {
            'twitter_changed': twitter_changed,
            'telegram_changed': telegram_changed,
            'session_cleared': False
        }
        
        # If Twitter credentials changed, clear browser session
        if twitter_changed:
            try:
                import shutil
                user_data_dir = os.getenv("USER_DATA_DIR", "data/chrome_profile")
                if os.path.exists(user_data_dir):
                    shutil.rmtree(user_data_dir)
                    print(f"[API] Twitter credentials changed - cleared Chrome profile: {user_data_dir}")
                
                cookies_path = os.getenv("COOKIES_PATH", "data/cookies.json")
                if os.path.exists(cookies_path):
                    os.remove(cookies_path)
                    print(f"[API] Cleared cookies file: {cookies_path}")
                
                response_data['session_cleared'] = True
            except Exception as e:
                print(f"[API] Error clearing session: {e}")
        
        # Store new credentials for future comparison
        with open(credentials_file, 'w') as f:
            json.dump(new_credentials, f, indent=2)
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scrape', methods=['POST'])
def start_manual_scrape():
    """Start manual scrape operation"""
    global current_config, scrape_running, latest_results
    
    try:
        if scrape_running:
            return jsonify({'error': 'Scrape already in progress'}), 409
        
        if not current_config:
            return jsonify({'error': 'No configuration available. Please save configuration first.'}), 400
        
        # Validate required configuration
        if not os.environ.get('TELEGRAM_BOT_TOKEN'):
            return jsonify({'error': 'Telegram Bot Token not configured'}), 400
            
        if not os.environ.get('TELEGRAM_CHAT_ID'):
            return jsonify({'error': 'Telegram Chat ID not configured'}), 400
            
        if not os.environ.get('TWITTER_USERNAME'):
            return jsonify({'error': 'Twitter username not configured'}), 400
            
        # Allow empty search query - it will search all tweets if no keywords specified
        search_query = os.environ.get('SEARCH_QUERY', '')
        
        print(f"[API] Starting manual scrape with:")
        print(f"[API] - Search Query: '{search_query}' {'(empty - will search all tweets)' if not search_query else ''}")
        print(f"[API] - Search URL: {os.environ.get('SEARCH_URL')}")
        print(f"[API] - Required Post Keywords: {os.environ.get('REQUIRED_POST_KEYWORDS', 'None')}")
        print(f"[API] - Contact Address Required: {os.environ.get('CONTACT_ADDRESS_REQUIRED', 'true')}")
        
        # Start scrape in background thread
        def run_scrape():
            global scrape_running
            try:
                scrape_running = True
                add_activity_event("🔄 Starting manual scrape...", "info")
                add_activity_event("📋 Connecting to Twitter feeds...", "info")
                add_activity_event("🔍 Searching for tweets with configured keywords...", "info")
                
                print("[API] Starting manual scrape...")
                result = single_run(current_config.config, return_results=True)
                sent_count, results = result if isinstance(result, tuple) else (result, [])
                latest_results[:] = results  # Update global results
                
                add_activity_event(f"✅ Manual scrape completed successfully", "success")
                add_activity_event(f"📊 Found and sent {sent_count} new messages to Telegram", "success")
                print(f"[API] Manual scrape completed. Sent {sent_count} messages.")
            except Exception as e:
                add_activity_event(f"❌ Manual scrape failed: {str(e)}", "error")
                print(f"[API] Manual scrape error: {e}")
                import traceback
                traceback.print_exc()
            finally:
                scrape_running = False
        
        scrape_thread = threading.Thread(target=run_scrape)
        scrape_thread.daemon = True
        scrape_thread.start()
        
        return jsonify({
            'status': 'success',
            'message': 'Manual scrape started',
            'scrape_running': True,
            'config_summary': {
                'search_query': os.environ.get('SEARCH_QUERY'),
                'has_telegram': bool(os.environ.get('TELEGRAM_BOT_TOKEN')),
                'has_twitter': bool(os.environ.get('TWITTER_USERNAME')),
                'required_post_keywords': os.environ.get('REQUIRED_POST_KEYWORDS', 'None')
            }
        })
        
    except Exception as e:
        print(f"[API] Error in start_manual_scrape: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/automation', methods=['POST'])
def toggle_automation():
    """Toggle automation on/off"""
    global automation_enabled, automation_thread, current_config
    
    try:
        data = request.get_json()
        enabled = data.get('enabled', False)
        
        if not current_config and enabled:
            return jsonify({'error': 'No configuration available. Please save configuration first.'}), 400
        
        if enabled and not automation_enabled:
            # Start automation
            automation_enabled = True
            automation_thread = threading.Thread(target=automation_worker)
            automation_thread.daemon = True
            automation_thread.start()
            message = 'Automation enabled'
            
        elif not enabled and automation_enabled:
            # Stop automation
            automation_enabled = False
            if automation_thread:
                automation_thread.join(timeout=1)
            message = 'Automation disabled'
            
        else:
            message = f'Automation already {"enabled" if enabled else "disabled"}'
        
        return jsonify({
            'status': 'success',
            'message': message,
            'automation_enabled': automation_enabled
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/automation/status', methods=['GET'])
def get_automation_status():
    """Get current automation status"""
    return jsonify({
        'enabled': automation_enabled,
        'scrape_running': scrape_running,
        'has_config': current_config is not None
    })

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get recent activity logs"""
    try:
        # Read from log file if it exists
        log_file = 'scraper.log'
        logs = []
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = f.readlines()[-50:]  # Last 50 lines
        
        return jsonify({'logs': logs})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def load_saved_config():
    """Load previously saved configuration on startup"""
    global current_config
    
    try:
        config_file = 'api_config.json'
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            current_config = APIConfig(config_data)
            print(f"[API] Loaded saved configuration:")
            print(f"[API] - Search Query: {os.environ.get('SEARCH_QUERY', 'Not set')}")
            print(f"[API] - Required Post Keywords: {os.environ.get('REQUIRED_POST_KEYWORDS', 'Not set')}")
            print(f"[API] - Telegram Bot Token: {'Set' if os.environ.get('TELEGRAM_BOT_TOKEN') else 'Not set'}")
            print(f"[API] - Twitter Username: {os.environ.get('TWITTER_USERNAME', 'Not set')}")
    except Exception as e:
        print(f"[API] Error loading saved config: {e}")

# Simple event system for real-time updates
activity_events = []
MAX_EVENTS = 50

def add_activity_event(message, event_type='info'):
    """Add an activity event for real-time logging"""
    global activity_events
    import datetime
    
    event = {
        'timestamp': datetime.datetime.now().strftime('%H:%M:%S'),
        'message': message,
        'type': event_type,
        'id': len(activity_events)
    }
    
    activity_events.append(event)
    
    # Keep only recent events
    if len(activity_events) > MAX_EVENTS:
        activity_events = activity_events[-MAX_EVENTS:]
    
    print(f"[ACTIVITY] {event['timestamp']} - {message}")

@app.route('/api/activity/events')
def activity_stream():
    """Server-sent events endpoint for real-time activity updates"""
    def generate():
        # Send existing events first
        for event in activity_events[-10:]:  # Send last 10 events
            yield f"data: {json.dumps(event)}\n\n"
        
        # Keep connection alive and send new events
        # Note: This is a simple implementation. For production, use Redis or similar
        last_event_id = len(activity_events)
        
        import time
        while True:
            # Check for new events
            if len(activity_events) > last_event_id:
                for event in activity_events[last_event_id:]:
                    yield f"data: {json.dumps(event)}\n\n"
                last_event_id = len(activity_events)
            
            time.sleep(1)  # Check every second
    
    response = app.response_class(generate(), mimetype='text/plain')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response

@app.route('/api/activity/log', methods=['GET'])
def get_activity_log():
    """Get recent activity log events"""
    return jsonify({
        'events': activity_events[-20:] if activity_events else []
    })

if __name__ == '__main__':
    print("[API] Starting Web3X Backend API Server...")
    
    try:
        # Load any previously saved configuration
        load_saved_config()
        
        # Start Flask server with better error handling
        app.run(
            host='localhost',  # Bind specifically to localhost
            port=5000,  # Back to port 5000
            debug=False,  # Disable debug mode to prevent auto-restart issues
            threaded=True,
            use_reloader=False  # Disable auto-reloader to prevent ghost processes
        )
    except OSError as e:
        if "Address already in use" in str(e):
            print("[API] ERROR: Port 5000 is already in use!")
            print("[API] Please stop any existing server instances or restart your system.")
            print("[API] You can also try using a different port by modifying the code.")
        else:
            print(f"[API] Server startup error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[API] Server interrupted by user")
        cleanup_and_exit()
    except Exception as e:
        print(f"[API] Unexpected error: {e}")
        cleanup_and_exit()