from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time
import os
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

class APIConfig:
    """Configuration class for API-received settings"""
    def __init__(self, config_data: Dict[str, Any]):
        # Update environment variables from frontend config
        if 'telegram' in config_data:
            os.environ['TELEGRAM_BOT_TOKEN'] = config_data['telegram'].get('botToken', '')
            os.environ['TELEGRAM_CHAT_ID'] = config_data['telegram'].get('chatId', '')
        
        if 'twitter' in config_data:
            os.environ['TWITTER_USERNAME'] = config_data['twitter'].get('username', '')
            os.environ['TWITTER_EMAIL'] = config_data['twitter'].get('email', '')  
            os.environ['TWITTER_PASSWORD'] = config_data['twitter'].get('password', '')
        
        if 'keywords' in config_data:
            search_keywords = config_data['keywords'].get('required', [])  # These are for Twitter search
            required_post_keywords = config_data['keywords'].get('optional', [])  # These are for post filtering
            
            # Build search query from search keywords
            search_query = ' OR '.join([f'"{keyword}"' if ' ' in keyword else keyword for keyword in search_keywords])
            os.environ['SEARCH_QUERY'] = search_query
            
            # Build URL-encoded search URL
            import urllib.parse
            encoded_query = urllib.parse.quote(search_query)
            os.environ['SEARCH_URL'] = f"https://x.com/search?q={encoded_query}&f=live"
            
            # Set required post keywords for filtering (these will be used by detect.py)
            if required_post_keywords:
                os.environ['REQUIRED_POST_KEYWORDS'] = ','.join(required_post_keywords)
        
        # Create Config object with updated environment
        self.config = Config()

def automation_worker():
    """Background worker for automation mode"""
    global automation_enabled, scrape_running, current_config
    
    while automation_enabled:
        if current_config and not scrape_running:
            try:
                scrape_running = True
                print("[API] Running automated scrape...")
                single_run(current_config.config)
                print("[API] Automated scrape completed")
            except Exception as e:
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

@app.route('/api/scrape', methods=['POST'])
def start_manual_scrape():
    """Start manual scrape operation"""
    global current_config, scrape_running
    
    try:
        if scrape_running:
            return jsonify({'error': 'Scrape already in progress'}), 409
        
        if not current_config:
            return jsonify({'error': 'No configuration available. Please save configuration first.'}), 400
        
        # Start scrape in background thread
        def run_scrape():
            global scrape_running
            try:
                scrape_running = True
                print("[API] Starting manual scrape...")
                result = single_run(current_config.config)
                print(f"[API] Manual scrape completed. Sent {result} messages.")
            except Exception as e:
                print(f"[API] Manual scrape error: {e}")
            finally:
                scrape_running = False
        
        scrape_thread = threading.Thread(target=run_scrape)
        scrape_thread.daemon = True
        scrape_thread.start()
        
        return jsonify({
            'status': 'success',
            'message': 'Manual scrape started',
            'scrape_running': True
        })
        
    except Exception as e:
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
            print("[API] Loaded saved configuration")
    except Exception as e:
        print(f"[API] Error loading saved config: {e}")

if __name__ == '__main__':
    print("[API] Starting Web3X Backend API Server...")
    
    # Load any previously saved configuration
    load_saved_config()
    
    # Start Flask server
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        threaded=True
    )