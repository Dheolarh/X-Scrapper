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
      
      const result = await response.json();
      
      // Handle different response formats
      if (result && typeof result === 'object') {
        if (result.status === 'success' || result.message) {
          return result;
        } else if (result.error) {
          throw new Error(result.error);
        } else {
          // Return the result as-is if it has data
          return result;
        }
      } else if (typeof result === 'string') {
        return { status: 'success', message: result };
      } else {
        return { status: 'success', message: 'Scrape completed successfully' };
      }
    } catch (error) {
      console.error('Manual scrape failed:', error);
      
      // Provide better error messages
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error('Unable to connect to server. Please check if the API is running.');
      } else if (error.message.includes('HTTP error')) {
        throw new Error(`Server error: ${error.message}`);
      } else {
        throw new Error(error.message || 'Failed to start manual scrape');
      }
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
}

// UI and Event Handling
class CryptoScraperUI {
  constructor() {
    this.api = new BackendAPI();
    this.isLoading = false;
    this.currentTab = 'results';
    this.results = [];
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

    // Refresh results
    document.getElementById('refreshResults').addEventListener('click', () => {
      this.loadResults();
    });

    // Automation toggle
    document.getElementById('automationToggle').addEventListener('change', (e) => {
      this.toggleAutomation(e.target.checked);
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
      this.addLogEntry('Failed to load results', 'error');
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

      const config = {
        telegram_bot_token: document.getElementById('telegramBotId').value,
        telegram_chat_id: document.getElementById('telegramChatId').value,
        twitter_username: document.getElementById('twitterUsername').value,
        twitter_email: document.getElementById('twitterEmail').value,
        twitter_password: document.getElementById('twitterPassword').value,
        search_query: document.getElementById('requiredKeywords').value,
        required_post_keywords: document.getElementById('optionalKeywords').value,
        backend_url: document.getElementById('backendUrl').value
      };

      await this.api.saveConfig(config);
      await this.saveConfigToStorage(config);

      this.addLogEntry('Configuration saved successfully');
      
      submitBtn.textContent = originalText;
      submitBtn.disabled = false;
    } catch (error) {
      this.addLogEntry('Failed to save configuration', 'error');
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

      this.addLogEntry('Starting manual scrape...');
      
      const result = await this.api.startManualScrape();
      
      if (result.success) {
        this.addLogEntry(`Manual scrape completed: ${result.message}`);
        // Refresh results after scrape
        setTimeout(() => this.loadResults(), 2000);
      } else {
        this.addLogEntry('Manual scrape failed: ' + (result.error || 'Unknown error'), 'error');
      }
      
    } catch (error) {
      this.addLogEntry('Manual scrape failed: ' + error.message, 'error');
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
      this.addLogEntry(`${enabled ? 'Starting' : 'Stopping'} automation...`);
      
      const result = await this.api.toggleAutomation(enabled);
      
      if (result.success) {
        this.addLogEntry(`Automation ${enabled ? 'started' : 'stopped'} successfully`);
      } else {
        this.addLogEntry('Failed to toggle automation: ' + (result.error || 'Unknown error'), 'error');
        document.getElementById('automationToggle').checked = !enabled;
      }
    } catch (error) {
      this.addLogEntry('Failed to toggle automation: ' + error.message, 'error');
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

  async loadSavedConfig() {
    try {
      const result = await chrome.storage.local.get(['config']);
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
    } catch (error) {
      console.error('Failed to load saved config:', error);
    }
  }

  addLogEntry(message, type = 'info') {
    const logContainer = document.getElementById('logContainer');
    const timestamp = new Date().toLocaleTimeString();
    const logItem = document.createElement('div');
    logItem.className = `log-item ${type}`;
    logItem.innerHTML = `<span class="log-time">${timestamp}</span> ${message}`;
    
    logContainer.appendChild(logItem);
    logContainer.scrollTop = logContainer.scrollHeight;

    if (logContainer.children.length > 50) {
      logContainer.removeChild(logContainer.firstChild);
    }
  }
}

// Initialize the UI when the popup loads
document.addEventListener('DOMContentLoaded', () => {
  new CryptoScraperUI();
});