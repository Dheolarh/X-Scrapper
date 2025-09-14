// Firefox-compatible background script
// Uses browser.runtime API for Firefox compatibility

// Extension installed listener
if (typeof browser !== 'undefined') {
  // Firefox
  browser.runtime.onInstalled.addListener(() => {
    console.log('Web3X Firefox extension installed');
    // Initialize badge
    browser.browserAction.setBadgeBackgroundColor({ color: '#667eea' });
  });

  // Handle messages from popup
  browser.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'checkBackendStatus') {
      fetch(request.url)
        .then(response => sendResponse({ online: response.ok }))
        .catch(() => sendResponse({ online: false }));
      return true; // Keep message channel open for async response
    }
    
    if (request.action === 'updateBadge') {
      const count = request.count || 0;
      if (count > 0) {
        browser.browserAction.setBadgeText({ text: count.toString() });
        browser.browserAction.setBadgeBackgroundColor({ color: '#ff4444' });
      } else {
        browser.browserAction.setBadgeText({ text: '' });
      }
      sendResponse({ success: true });
    }
    
    if (request.action === 'clearBadge') {
      browser.browserAction.setBadgeText({ text: '' });
      sendResponse({ success: true });
    }
  });
} else if (typeof chrome !== 'undefined') {
  // Chrome fallback
  chrome.runtime.onInstalled.addListener(() => {
    console.log('Web3X Chrome-compatible extension installed');
    // Initialize badge
    chrome.action.setBadgeBackgroundColor({ color: '#667eea' });
  });

  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'checkBackendStatus') {
      fetch(request.url)
        .then(response => sendResponse({ online: response.ok }))
        .catch(() => sendResponse({ online: false }));
      return true;
    }
    
    if (request.action === 'updateBadge') {
      const count = request.count || 0;
      if (count > 0) {
        chrome.action.setBadgeText({ text: count.toString() });
        chrome.action.setBadgeBackgroundColor({ color: '#ff4444' });
      } else {
        chrome.action.setBadgeText({ text: '' });
      }
      sendResponse({ success: true });
    }
    
    if (request.action === 'clearBadge') {
      chrome.action.setBadgeText({ text: '' });
      sendResponse({ success: true });
    }
    
    return true; // Keep message channel open for async response
  });
}