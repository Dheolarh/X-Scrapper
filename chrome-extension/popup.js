// Backend API integration functions
class BackendAPI {
  constructor(baseUrl = 'http://localhost:5000') {
    this.baseUrl = baseUrl;
  }

  async checkStatus() {
    try {
      const response = await fetch(`${this.baseUrl}/status`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      return response.ok;
    } catch (error) {
      console.error('Backend status check failed:', error);
      return false;
    }
  }

  async saveConfig(config) {
    try {
      const response = await fetch(`${this.baseUrl}/api/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Save config failed:', error);
      throw error;
    }
  }

  async startManualScrape() {
    try {
      const response = await fetch(`${this.baseUrl}/api/scrape`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Manual scrape failed:', error);
      throw error;
    }
  }

  async toggleAutomation(enabled) {
    try {
      const endpoint = enabled ? 'start' : 'stop';
      const response = await fetch(`${this.baseUrl}/api/automation/${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Toggle automation failed:', error);
      throw error;
    }
  }

  async getAutomationStatus() {
    try {
      const response = await fetch(`${this.baseUrl}/api/automation/status`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Get automation status failed:', error);
      throw error;
    }
  }

  async getResults() {
    try {
      const response = await fetch(`${this.baseUrl}/api/results`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Get results failed:', error);
      return { results: [] };
    }
  }

  async validateCredentials(configData) {
    try {
      const response = await fetch(`${this.baseUrl}/api/credentials/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(configData)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Credential validation failed:', error);
      throw error;
    }
  }

  async clearSession() {
    try {
      const response = await fetch(`${this.baseUrl}/api/credentials/clear-session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Clear session failed:', error);
      throw error;
    }
  }

  async getActivityLog() {
    try {
      const response = await fetch(`${this.baseUrl}/api/activity/log`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Get activity log failed:', error);
      return { events: [] };
    }
  }
}

// UI and Event Handling
class CryptoScraperUI {
  constructor() {
    this.api = new BackendAPI();
    this.isLoading = false;
    this.currentTab = 'results';
    this.results = [];
    this.activityLogTimer = null;
    this.init();
  }

  init() {
    this.setupTabs();
    this.setupEventListeners();
    this.loadSavedConfig();
    this.checkBackendStatus();
    this.loadAutomationStatus();
    this.loadResults();
    this.clearBadgeOnOpen();
    this.startActivityLogSync();
  }

  setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
      button.addEventListener('click', () => {
        const targetTab = button.dataset.tab;
        
        // Update button states
        tabButtons.forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
        
        // Update content states
        tabContents.forEach(content => content.classList.remove('active'));
        document.getElementById(`${targetTab}-tab`).classList.add('active');
        
        this.currentTab = targetTab;
        
        // Load results when switching to results tab
        if (targetTab === 'results') {
          this.loadResults();
        }
      });
    });
  }

  setupEventListeners() {
    // Configuration form submission
    document.getElementById('configForm').addEventListener('submit', (e) => {
      e.preventDefault();
      this.saveConfiguration();
    });

    // Manual scrape buttons
    document.getElementById('manualScrape').addEventListener('click', () => {
      this.startManualScrape();
    });

    // Start scrape from results tab
    document.getElementById('startScrapeFromResults')?.addEventListener('click', () => {
      this.startManualScrape();
    });

    // Refresh results
    document.getElementById('refreshResults').addEventListener('click', () => {
      this.loadResults();
    });

    // Clear activity log
    document.getElementById('clearActivityLog').addEventListener('click', () => {
      this.clearActivityLog();
    });

    // Automation toggle
    document.getElementById('automationToggle').addEventListener('change', (e) => {
      this.toggleAutomation(e.target.checked);
    });

    // Contract address toggle
    document.getElementById('contractAddressToggle').addEventListener('change', (e) => {
      this.updateContactAddressRequirement(e.target.checked);
    });

    // Backend URL change
    document.getElementById('backendUrl').addEventListener('change', (e) => {
      this.api.baseUrl = e.target.value;
      this.checkBackendStatus();
    });
  }

  async clearBadgeOnOpen() {
    try {
      await chrome.runtime.sendMessage({ action: 'clearBadge' });
    } catch (error) {
      console.log('Could not clear badge:', error);
    }
  }

  async updateBadge(count) {
    try {
      await chrome.runtime.sendMessage({ 
        action: 'updateBadge', 
        count: count 
      });
    } catch (error) {
      console.log('Could not update badge:', error);
    }
  }

  async loadResults() {
    try {
      const data = await this.api.getResults();
      this.results = data.results || [];
      this.displayResults();
      document.getElementById('resultsCount').textContent = `${this.results.length} results`;
    } catch (error) {
      console.error('Failed to load results:', error);
      this.addActivityLog('❌ Failed to load results', 'error');
    }
  }

  displayResults() {
    const container = document.getElementById('resultsContainer');
    
    if (this.results.length === 0) {
      container.innerHTML = `
        <div class="no-results">
          <div class="no-results-icon">🔍</div>
          <h4>No results yet</h4>
          <p>Run a manual scrape or enable automation to see results</p>
          <button id="startScrapeFromResults" class="btn primary">Start Scrape</button>
        </div>
      `;
      
      // Re-attach event listener
      const startButton = document.getElementById('startScrapeFromResults');
      if (startButton) {
        startButton.addEventListener('click', () => {
          this.startManualScrape();
        });
      }
      
      return;
    }

    const cardsHTML = this.results.map(result => this.createResultCard(result)).join('');
    container.innerHTML = cardsHTML;
  }

  createResultCard(result) {
    const feedEmoji = result.feed_source?.includes('Latest') ? '🔥' : 
                     result.feed_source?.includes('Top') ? '⭐' : 
                     result.feed_source?.includes('Homepage') ? '🏠' : '📡';
    
    const contractAddresses = (result.mints || []).map(mint => 
      `<div class="result-contract">${mint}</div>`
    ).join('');

    return `
      <div class="result-card">
        <div class="result-card-header">
          <div class="result-username">@${result.username}</div>
          <div class="result-feed">${feedEmoji} ${result.feed_source || 'Unknown'}</div>
        </div>
        <div class="result-card-body">
          <div class="result-text">${this.highlightKeywords(result.text || '')}</div>
          ${contractAddresses}
          <div class="result-meta">
            <div class="result-engagement">
              <span>❤️ ${result.likes || 0}</span>
              <span>💬 ${result.comments || 0}</span>
              <span>🔄 ${result.reposts || 0}</span>
            </div>
            <div class="result-time">${this.formatTime(result.timestamp)}</div>
          </div>
        </div>
      </div>
    `;
  }

  highlightKeywords(text) {
    const keywords = ['pump', 'sol', 'launch', 'project', 'coming soon'];
    let highlightedText = text;
    
    keywords.forEach(keyword => {
      const regex = new RegExp(`\\b(${keyword})\\b`, 'gi');
      highlightedText = highlightedText.replace(regex, '<strong>$1</strong>');
    });
    
    return highlightedText;
  }

  formatTime(timestamp) {
    if (!timestamp) return 'Unknown time';
    
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch (error) {
      return timestamp;
    }
  }

  async checkBackendStatus() {
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');

    try {
      const isOnline = await this.api.checkStatus();
      
      if (isOnline) {
        statusDot.className = 'status-dot online';
        statusText.textContent = 'Online';
      } else {
        statusDot.className = 'status-dot offline';
        statusText.textContent = 'Offline';
      }
    } catch (error) {
      statusDot.className = 'status-dot offline';
      statusText.textContent = 'Offline';
      console.error('Status check failed:', error);
    }
  }

  async saveConfiguration() {
    if (this.isLoading) return;

    try {
      this.isLoading = true;
      const submitBtn = document.querySelector('button[type="submit"]');
      const originalText = submitBtn.textContent;
      submitBtn.textContent = 'Saving...';
      submitBtn.disabled = true;

      // Get form values
      const telegramBotId = document.getElementById('telegramBotId').value;
      const telegramChatId = document.getElementById('telegramChatId').value;
      const twitterUsername = document.getElementById('twitterUsername').value;
      const twitterEmail = document.getElementById('twitterEmail').value;
      const twitterPassword = document.getElementById('twitterPassword').value;
      const requiredKeywords = document.getElementById('requiredKeywords').value;
      const optionalKeywords = document.getElementById('optionalKeywords').value;
      const backendUrl = document.getElementById('backendUrl').value;
      const contractAddressRequired = document.getElementById('contractAddressToggle').checked;

      // Build config in the format expected by the API
      const config = {
        telegram: {
          botToken: telegramBotId,
          chatId: telegramChatId
        },
        twitter: {
          username: twitterUsername,
          email: twitterEmail,
          password: twitterPassword
        },
        keywords: {
          required: requiredKeywords.split(',').map(k => k.trim()).filter(k => k),
          optional: optionalKeywords.split(',').map(k => k.trim()).filter(k => k)
        },
        contactAddressRequired: contractAddressRequired,
        backend_url: backendUrl
      };

      this.addActivityLog('🔄 Validating credentials...', 'info');
      
      // Validate credentials and clear sessions if changed
      try {
        const credentialResult = await this.api.validateCredentials(config);
        
        if (credentialResult.twitter_changed) {
          this.addActivityLog('🔑 Twitter credentials changed - clearing browser session', 'info');
        }
        if (credentialResult.telegram_changed) {
          this.addActivityLog('🤖 Telegram credentials updated', 'info');
        }
        if (credentialResult.session_cleared) {
          this.addActivityLog('✅ Browser session cleared successfully', 'success');
        }
      } catch (credError) {
        this.addActivityLog('⚠️ Credential validation failed: ' + credError.message, 'warning');
      }

      this.addActivityLog('💾 Saving configuration...', 'info');
      await this.api.saveConfig(config);
      
      // Save to local storage in legacy format for compatibility
      const legacyConfig = {
        telegram_bot_token: telegramBotId,
        telegram_chat_id: telegramChatId,
        twitter_username: twitterUsername,
        twitter_email: twitterEmail,
        twitter_password: twitterPassword,
        search_query: requiredKeywords,
        required_post_keywords: optionalKeywords,
        backend_url: backendUrl
      };
      await this.saveConfigToStorage(legacyConfig);

      this.addActivityLog('✅ Configuration saved successfully', 'success');
      this.addActivityLog(`📋 Contact address requirement: ${contractAddressRequired ? 'enabled' : 'disabled'}`, 'info');
      
      submitBtn.textContent = originalText;
      submitBtn.disabled = false;
    } catch (error) {
      this.addActivityLog('❌ Failed to save configuration: ' + error.message, 'error');
      console.error('Save failed:', error);
      
      const submitBtn = document.querySelector('button[type="submit"]');
      submitBtn.textContent = 'Save Configuration';
      submitBtn.disabled = false;
    } finally {
      this.isLoading = false;
    }
  }

  async startManualScrape() {
    if (this.isLoading) return;

    try {
      this.isLoading = true;
      const buttons = document.querySelectorAll('#manualScrape, #startScrapeFromResults');
      buttons.forEach(btn => {
        if (btn) {
          btn.textContent = 'Scraping...';
          btn.disabled = true;
        }
      });

      this.addActivityLog('🔄 Starting manual scrape...', 'info');
      this.addActivityLog('📋 Connecting to Twitter feeds...', 'info');
      
      const result = await this.api.startManualScrape();
      
      if (result && result.success) {
        this.addActivityLog('✅ Manual scrape completed successfully', 'success');
        this.addActivityLog(`📊 ${result.message || 'Scrape finished successfully'}`, 'info');
        // Refresh results after scrape
        setTimeout(() => this.loadResults(), 2000);
      } else if (result && result.error) {
        this.addActivityLog('❌ Manual scrape failed: ' + result.error, 'error');
      } else if (result && result.message) {
        // Some responses might have message but no success flag
        this.addActivityLog(`📋 ${result.message}`, 'info');
        setTimeout(() => this.loadResults(), 2000);
      } else {
        this.addActivityLog('⚠️ Manual scrape completed (no detailed response)', 'warning');
        setTimeout(() => this.loadResults(), 2000);
      }
      
    } catch (error) {
      this.addActivityLog('❌ Manual scrape failed: ' + error.message, 'error');
      console.error('Manual scrape failed:', error);
    } finally {
      this.isLoading = false;
      const buttons = document.querySelectorAll('#manualScrape, #startScrapeFromResults');
      buttons.forEach(btn => {
        if (btn) {
          btn.textContent = btn.id === 'manualScrape' ? 'Start Manual Scrape' : 'Start Scrape';
          btn.disabled = false;
        }
      });
    }
  }

  async toggleAutomation(enabled) {
    try {
      this.addActivityLog(`🔄 ${enabled ? 'Starting' : 'Stopping'} automation...`, 'info');
      
      const result = await this.api.toggleAutomation(enabled);
      
      if (result.success) {
        this.addActivityLog(`✅ Automation ${enabled ? 'started' : 'stopped'} successfully`, 'success');
      } else {
        this.addActivityLog('❌ Failed to toggle automation: ' + (result.error || 'Unknown error'), 'error');
        document.getElementById('automationToggle').checked = !enabled;
      }
    } catch (error) {
      this.addActivityLog('❌ Failed to toggle automation: ' + error.message, 'error');
      document.getElementById('automationToggle').checked = !enabled;
      console.error('Toggle automation failed:', error);
    }
  }

  async loadAutomationStatus() {
    try {
      const status = await this.api.getAutomationStatus();
      document.getElementById('automationToggle').checked = status.running || false;
    } catch (error) {
      console.error('Failed to load automation status:', error);
    }
  }

  async saveConfigToStorage(config) {
    return chrome.storage.local.set({ config: config });
  }

  // Activity Log Methods
  addActivityLog(message, type = 'info') {
    const activityLog = document.getElementById('activityLog');
    const timestamp = new Date().toLocaleTimeString();
    
    const activityItem = document.createElement('div');
    activityItem.className = `activity-item ${type}`;
    activityItem.innerHTML = `
      <span class="activity-time">${timestamp}</span>
      <span class="activity-message">${message}</span>
    `;
    
    activityLog.appendChild(activityItem);
    activityLog.scrollTop = activityLog.scrollHeight;
    
    // Keep only last 20 entries
    while (activityLog.children.length > 20) {
      activityLog.removeChild(activityLog.firstChild);
    }
  }

  clearActivityLog() {
    const activityLog = document.getElementById('activityLog');
    activityLog.innerHTML = `
      <div class="activity-item info">
        <span class="activity-time">Ready</span>
        <span class="activity-message">Activity log cleared</span>
      </div>
    `;
  }

  async syncActivityLog() {
    try {
      const result = await this.api.getActivityLog();
      if (result && result.events && result.events.length > 0) {
        this.displayActivityEvents(result.events);
      }
    } catch (error) {
      console.error('Failed to sync activity log:', error);
    }
  }

  displayActivityEvents(events) {
    const activityLog = document.getElementById('activityLog');
    
    // Clear existing activity log but keep first message
    activityLog.innerHTML = '';
    
    // Display events from backend
    events.forEach(event => {
      const activityItem = document.createElement('div');
      activityItem.className = `activity-item ${event.type || 'info'}`;
      activityItem.innerHTML = `
        <span class="activity-time">${event.timestamp}</span>
        <span class="activity-message">${event.message}</span>
      `;
      activityLog.appendChild(activityItem);
    });
    
    // If no events, show ready message
    if (events.length === 0) {
      const activityItem = document.createElement('div');
      activityItem.className = 'activity-item info';
      activityItem.innerHTML = `
        <span class="activity-time">Ready</span>
        <span class="activity-message">No recent activity</span>
      `;
      activityLog.appendChild(activityItem);
    }
    
    activityLog.scrollTop = activityLog.scrollHeight;
  }

  startActivityLogSync() {
    // Sync immediately
    this.syncActivityLog();
    
    // Then sync every 2 seconds
    this.activityLogTimer = setInterval(() => {
      this.syncActivityLog();
    }, 2000);
  }

  stopActivityLogSync() {
    if (this.activityLogTimer) {
      clearInterval(this.activityLogTimer);
      this.activityLogTimer = null;
    }
  }

  updateContactAddressRequirement(required) {
    this.addActivityLog(
      `Contract address requirement: ${required ? 'enabled' : 'disabled'}`, 
      'info'
    );
    // Save the setting to storage
    chrome.storage.local.set({ 
      contractAddressRequired: required 
    });
  }

  async loadSavedConfig() {
    try {
      const result = await chrome.storage.local.get(['config', 'contractAddressRequired']);
      if (result.config) {
        const config = result.config;
        document.getElementById('telegramBotId').value = config.telegram_bot_token || '';
        document.getElementById('telegramChatId').value = config.telegram_chat_id || '';
        document.getElementById('twitterUsername').value = config.twitter_username || '';
        document.getElementById('twitterEmail').value = config.twitter_email || '';
        document.getElementById('twitterPassword').value = config.twitter_password || '';
        document.getElementById('requiredKeywords').value = config.search_query || '';
        document.getElementById('optionalKeywords').value = config.required_post_keywords || '';
        
        if (config.backend_url) {
          document.getElementById('backendUrl').value = config.backend_url;
          this.api.baseUrl = config.backend_url;
        }
      }
      
      // Load contract address requirement setting
      const contractAddressRequired = result.contractAddressRequired !== undefined ? result.contractAddressRequired : true;
      document.getElementById('contractAddressToggle').checked = contractAddressRequired;
      
    } catch (error) {
      console.error('Failed to load saved config:', error);
      this.addActivityLog('⚠️ Failed to load saved configuration', 'warning');
    }
  }
}

// Initialize the UI when the popup loads
document.addEventListener('DOMContentLoaded', () => {
  new CryptoScraperUI();
});