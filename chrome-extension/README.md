# Twitter Crypto Scraper Chrome Extension

## Overview
This Chrome Extension provides a frontend interface to control your Twitter crypto scraping backend. It allows you to configure settings, start manual scrapes, and toggle automation from your browser.

## Features

### 🎛️ Configuration Management
- **Telegram Settings**: Bot Token and Chat ID configuration
- **Twitter Credentials**: Username, Email, and Password setup
- **Search Keywords**: Required and optional keyword configuration
- **Backend URL**: Configurable backend endpoint

### 🚀 Control Functions
- **Save Configuration**: Store settings both locally and send to backend
- **Manual Scrape**: Trigger immediate scraping operation
- **Automation Toggle**: Enable/disable continuous scraping mode
- **Backend Status**: Real-time connection status indicator

### 📊 User Interface
- Clean, professional popup interface
- Real-time activity logging
- Backend connection status indicator
- Form validation and error handling
- Configuration persistence

## Installation

1. **Load Extension in Chrome**:
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top right)
   - Click "Load unpacked"
   - Select the `chrome-extension` folder

2. **Setup Backend**:
   - Ensure your Python backend is running locally
   - Default backend URL: `http://localhost:5000`
   - Update backend URL in extension if different

## Usage

1. **Initial Setup**:
   - Click the extension icon in Chrome toolbar
   - Fill in all configuration fields
   - Click "Save Configuration"

2. **Manual Scraping**:
   - Click "Start Manual Scrape" to run immediately
   - Monitor activity log for results

3. **Automation**:
   - Toggle "Auto Scraping" to enable continuous mode
   - Backend will run scrapes every 10 minutes when enabled

## Backend API Endpoints

The extension expects your backend to provide these endpoints:

```
GET  /status                    - Backend health check
POST /api/config               - Save configuration
POST /api/scrape               - Start manual scrape
POST /api/automation           - Toggle automation (body: {"enabled": true/false})
GET  /api/automation/status    - Get automation status
```

## Configuration Storage

- Extension settings are stored locally in Chrome storage
- Settings are also sent to backend when saved
- Forms auto-populate from saved configuration

## Troubleshooting

1. **Backend Offline**: 
   - Check if your Python backend is running
   - Verify the backend URL in settings
   - Check console for connection errors

2. **Configuration Not Saving**:
   - Ensure all required fields are filled
   - Check backend API endpoints are responding
   - Verify CORS settings on backend

3. **Extension Not Loading**:
   - Check Chrome developer tools for errors
   - Ensure manifest.json is valid
   - Reload extension in chrome://extensions/

## File Structure

```
chrome-extension/
├── manifest.json        # Extension configuration
├── popup.html          # Main UI interface  
├── popup.css           # Styling
├── popup.js            # Frontend logic & API calls
├── background.js       # Service worker
└── icons/              # Extension icons (add your own)
```

## Next Steps

To connect with your Oracle Cloud deployment:
1. Update backend URL to your cloud instance
2. Ensure HTTPS if required
3. Add authentication if needed
4. Update CORS settings on backend