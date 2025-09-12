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
      const response = await fetch(`${this.baseUrl}/api/automation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ enabled })
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
}

// UI and Event Handling
class CryptoScraperUI {
  constructor() {
    this.api = new BackendAPI();
    this.isLoading = false;
    this.init();
  }

  init() {
    this.loadSavedConfig();
    this.setupEventListeners();
    this.checkBackendStatus();
    this.loadAutomationStatus();
  }

  setupEventListeners() {
    // Form submission
    document.getElementById('configForm').addEventListener('submit', (e) => {
      e.preventDefault();
      this.saveConfiguration();
    });

    // Manual scrape button
    document.getElementById('manualScrape').addEventListener('click', () => {
      this.startManualScrape();
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

  async checkBackendStatus() {
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');

    try {
      const isOnline = await this.api.checkStatus();
      
      if (isOnline) {
        statusDot.className = 'status-dot online';
        statusText.textContent = 'Backend Online';
        this.logMessage('Backend connection successful', 'success');
      } else {
        statusDot.className = 'status-dot offline';
        statusText.textContent = 'Backend Offline';
        this.logMessage('Backend connection failed', 'error');
      }
    } catch (error) {
      statusDot.className = 'status-dot offline';
      statusText.textContent = 'Backend Offline';
      this.logMessage('Backend connection error', 'error');
    }
  }

  async loadAutomationStatus() {
    try {
      const status = await this.api.getAutomationStatus();
      document.getElementById('automationToggle').checked = status.enabled || false;
    } catch (error) {
      this.logMessage('Failed to load automation status', 'warning');
    }
  }

  async saveConfiguration() {
    if (this.isLoading) return;

    this.setLoading(true);
    this.logMessage('Saving configuration...', 'info');

    try {
      const config = this.getFormData();
      await this.api.saveConfig(config);
      
      // Save to Chrome storage
      await chrome.storage.local.set({ config });
      
      this.logMessage('Configuration saved successfully!', 'success');
    } catch (error) {
      this.logMessage(`Failed to save configuration: ${error.message}`, 'error');
    } finally {
      this.setLoading(false);
    }
  }

  async startManualScrape() {
    if (this.isLoading) return;

    this.setLoading(true);
    this.logMessage('Starting manual scrape...', 'info');

    try {
      const result = await this.api.startManualScrape();
      this.logMessage(`Manual scrape started successfully! ${result.message || ''}`, 'success');
    } catch (error) {
      this.logMessage(`Failed to start manual scrape: ${error.message}`, 'error');
    } finally {
      this.setLoading(false);
    }
  }

  async toggleAutomation(enabled) {
    if (this.isLoading) return;

    this.setLoading(true);
    this.logMessage(`${enabled ? 'Enabling' : 'Disabling'} automation...`, 'info');

    try {
      const result = await this.api.toggleAutomation(enabled);
      this.logMessage(`Automation ${enabled ? 'enabled' : 'disabled'} successfully!`, 'success');
    } catch (error) {
      this.logMessage(`Failed to toggle automation: ${error.message}`, 'error');
      // Revert toggle on failure
      document.getElementById('automationToggle').checked = !enabled;
    } finally {
      this.setLoading(false);
    }
  }

  getFormData() {
    return {
      telegram: {
        botToken: document.getElementById('telegramBotId').value.trim(),
        chatId: document.getElementById('telegramChatId').value.trim(),
      },
      twitter: {
        username: document.getElementById('twitterUsername').value.trim(),
        email: document.getElementById('twitterEmail').value.trim(),
        password: document.getElementById('twitterPassword').value.trim(),
      },
      keywords: {
        required: document.getElementById('requiredKeywords').value
          .split(',')
          .map(k => k.trim())
          .filter(k => k.length > 0),
        optional: document.getElementById('optionalKeywords').value
          .split(',')
          .map(k => k.trim())
          .filter(k => k.length > 0),
      },
      backendUrl: document.getElementById('backendUrl').value.trim(),
    };
  }

  async loadSavedConfig() {
    try {
      const result = await chrome.storage.local.get(['config']);
      const config = result.config;

      if (config) {
        // Populate form with saved data
        document.getElementById('telegramBotId').value = config.telegram?.botToken || '';
        document.getElementById('telegramChatId').value = config.telegram?.chatId || '';
        document.getElementById('twitterUsername').value = config.twitter?.username || '';
        document.getElementById('twitterEmail').value = config.twitter?.email || '';
        document.getElementById('twitterPassword').value = config.twitter?.password || '';
        document.getElementById('requiredKeywords').value = config.keywords?.required?.join(', ') || '';
        document.getElementById('optionalKeywords').value = config.keywords?.optional?.join(', ') || '';
        document.getElementById('backendUrl').value = config.backendUrl || 'http://localhost:5000';

        // Update API base URL
        this.api.baseUrl = config.backendUrl || 'http://localhost:5000';

        this.logMessage('Configuration loaded from storage', 'info');
      }
    } catch (error) {
      this.logMessage('Failed to load saved configuration', 'warning');
    }
  }

  setLoading(loading) {
    this.isLoading = loading;
    const buttons = document.querySelectorAll('.btn');
    const toggle = document.getElementById('automationToggle');

    buttons.forEach(btn => {
      btn.disabled = loading;
    });
    toggle.disabled = loading;

    if (loading) {
      this.logMessage('Processing...', 'info');
    }
  }

  logMessage(message, type = 'info') {
    const logContainer = document.getElementById('logContainer');
    const logItem = document.createElement('div');
    logItem.className = `log-item ${type}`;
    logItem.textContent = `${new Date().toLocaleTimeString()}: ${message}`;

    logContainer.insertBefore(logItem, logContainer.firstChild);

    // Keep only last 20 log items
    const items = logContainer.querySelectorAll('.log-item');
    if (items.length > 20) {
      items[items.length - 1].remove();
    }

    // Auto-scroll to latest message
    logContainer.scrollTop = 0;
  }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
  new CryptoScraperUI();
});