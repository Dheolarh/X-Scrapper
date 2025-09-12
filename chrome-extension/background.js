// Background service worker for Chrome Extension
chrome.runtime.onInstalled.addListener(() => {
  console.log('Crypto Scraper Controller extension installed');
});

// Handle messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'checkBackendStatus') {
    // This could be used for periodic backend health checks
    fetch(request.url)
      .then(response => sendResponse({ online: response.ok }))
      .catch(() => sendResponse({ online: false }));
    return true; // Keep message channel open for async response
  }
});