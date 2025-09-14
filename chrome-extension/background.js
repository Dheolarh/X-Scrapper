// Background service worker for Chrome Extension
chrome.runtime.onInstalled.addListener(() => {
  console.log('Crypto Scraper Controller extension installed');
  // Initialize badge
  chrome.action.setBadgeBackgroundColor({ color: '#667eea' });
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
});

// Check for new results periodically when automation is enabled
let resultCheckInterval;

function startResultChecking(backendUrl) {
  if (resultCheckInterval) clearInterval(resultCheckInterval);
  
  resultCheckInterval = setInterval(async () => {
    try {
      // Get stored result count
      const result = await chrome.storage.local.get(['lastResultCount']);
      const lastCount = result.lastResultCount || 0;
      
      // Check for new results from backend (this would need an endpoint)
      // For now, we'll let the popup manage the badge updates
      
    } catch (error) {
      console.log('Error checking for new results:', error);
    }
  }, 30000); // Check every 30 seconds
}

function stopResultChecking() {
  if (resultCheckInterval) {
    clearInterval(resultCheckInterval);
    resultCheckInterval = null;
  }
}