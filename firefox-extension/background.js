// Firefox-compatible background script
// Uses browser.runtime API for Firefox compatibility

// Extension installed listener
if (typeof browser !== 'undefined') {
  // Firefox
  browser.runtime.onInstalled.addListener(() => {
    console.log('Web3X Firefox extension installed');
  });

  // Handle messages from popup
  browser.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'checkBackendStatus') {
      fetch(request.url)
        .then(response => sendResponse({ online: response.ok }))
        .catch(() => sendResponse({ online: false }));
      return true; // Keep message channel open for async response
    }
  });
} else if (typeof chrome !== 'undefined') {
  // Chrome fallback
  chrome.runtime.onInstalled.addListener(() => {
    console.log('Web3X Chrome-compatible extension installed');
  });

  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'checkBackendStatus') {
      fetch(request.url)
        .then(response => sendResponse({ online: response.ok }))
        .catch(() => sendResponse({ online: false }));
      return true;
    }
  });
}