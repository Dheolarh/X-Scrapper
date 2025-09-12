# Web3X - Firefox Extension

## Overview
Firefox-compatible version of the Web3X Chrome extension. This version uses Manifest V2 and Firefox's WebExtensions API to provide the same functionality for Firefox users.

## Firefox-Specific Features

### 🦊 Firefox Compatibility
- **Manifest V2**: Uses the older but stable manifest format
- **browser.storage API**: Firefox's native storage API with Chrome fallback
- **WebExtensions**: Compatible with Firefox's extension system
- **Permissions**: Simplified permission model for Firefox

### 🔧 Key Differences from Chrome Version
- Uses `browser_action` instead of `action` in manifest
- Compatible with both `browser.*` (Firefox) and `chrome.*` (Chrome) APIs
- Manifest V2 format with background scripts array
- Different icon sizes (16, 32, 48, 96 for Firefox)

## Installation

### 🔧 For Development (Temporary):
1. Open Firefox
2. Go to `about:debugging`
3. Click "This Firefox"
4. Click "Load Temporary Add-on"
5. Select the `manifest.json` file from `firefox-extension` folder

### 📦 For Distribution:
1. **Zip the extension**:
   ```bash
   cd firefox-extension
   zip -r web3x-firefox.zip .
   ```

2. **Submit to Mozilla Add-ons**:
   - Go to [addons.mozilla.org/developers](https://addons.mozilla.org/developers)
   - Create account and submit the ZIP file
   - Wait for review (can take days/weeks)

### 🆔 For Self-Distribution:
1. **Get Extension ID**: Add to manifest.json:
   ```json
   "browser_specific_settings": {
     "gecko": {
       "id": "web3x@yourcompany.com",
       "strict_min_version": "57.0"
     }
   }
   ```

2. **Sign the Extension**: Required for permanent installation

## Browser Support

### ✅ Fully Supported:
- **Firefox** 57+ (Firefox Quantum and later)
- **Firefox ESR** (Extended Support Release)
- **Firefox Developer Edition**
- **Firefox Nightly**

### ⚡ Performance Notes:
- Firefox extensions may have slightly different performance characteristics
- Storage API calls are async in both browsers
- Network requests work identically

## API Differences Handled

### 🔄 Cross-Browser Compatibility:
```javascript
// Storage API
if (typeof browser !== 'undefined') {
  await browser.storage.local.set(data);  // Firefox
} else {
  await chrome.storage.local.set(data);   // Chrome
}

// Runtime API
browser.runtime.onInstalled || chrome.runtime.onInstalled
```

### 📱 Same Backend Integration:
- All API endpoints work identically
- Same configuration format
- Same functionality as Chrome version

## File Structure

```
firefox-extension/
├── manifest.json        # Manifest V2 for Firefox
├── popup.html          # Same UI as Chrome version
├── popup.css           # Identical styling
├── popup.js            # Firefox-compatible JavaScript
├── background.js       # Firefox background script
└── icons/              # Firefox icon sizes (16,32,48,96)
```

## Testing

### 🧪 Test in Firefox:
1. Load the temporary extension
2. Test all features:
   - Configuration saving/loading
   - Backend connection status
   - Manual scrape trigger
   - Automation toggle
   - Activity logging

### 🔍 Debug Issues:
- Open Firefox Developer Tools
- Go to "Storage" tab to check extension storage
- Check "Console" for JavaScript errors
- Use "Network" tab to verify API calls

## Distribution Strategy

### 🎯 Recommended Approach:
1. **Start with self-hosting**: For immediate use
2. **Submit to Mozilla**: For wider distribution
3. **Maintain both versions**: Chrome + Firefox for maximum reach

### 📊 Market Coverage:
- **Chrome Extension**: ~75% of users
- **Firefox Extension**: ~15% of users  
- **Combined**: ~90% browser coverage

## Next Steps

1. **Test thoroughly** in Firefox
2. **Add extension signing** for permanent installation
3. **Submit to Mozilla Add-ons** for public distribution
4. **Maintain parity** with Chrome version updates

The Firefox extension provides identical functionality to the Chrome version while being fully compatible with Firefox's extension system!