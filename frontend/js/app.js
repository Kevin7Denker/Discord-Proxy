import { Api } from './api.js?v=2';
import { I18nManager } from './i18n.js?v=2';
import { StateManager } from './state.js?v=2';

class AppContext {
  constructor() {
    this.elements = {
      closeBtn: document.getElementById('close-button'),
      minBtn: document.getElementById('minimize-button'),
      settingsBtn: document.getElementById('settings-button'),
      backBtn: document.getElementById('back-button'),
      dashboardView: document.getElementById('dashboard-view'),
      settingsView: document.getElementById('settings-view'),
      shield: document.getElementById('hero-shield'),
      statusText: document.getElementById('status-text'),
      timerBox: document.getElementById('timer-box'),
      timerValue: document.getElementById('session-timer'),
      mainActionBtn: document.getElementById('main-action-button'),
      restartBtn: document.getElementById('restart-button'),
      langSelect: document.getElementById('lang-select'),
      supportBtn: document.getElementById('support-button'),
      themeChoices: Array.from(document.querySelectorAll('[data-theme-choice]')),
      logToggle: document.getElementById('log-toggle'),
      logPanel: document.getElementById('log-panel'),
      logOutput: document.getElementById('log-output'),
      clearLogsBtn: document.getElementById('clear-logs-button'),
      proxySummary: document.getElementById('proxy-summary'),
      customProxyToggle: document.getElementById('custom-proxy-toggle'),
      editProxyBtn: document.getElementById('edit-proxy-button'),
      proxyModal: document.getElementById('proxy-modal'),
      proxyForm: document.getElementById('proxy-form'),
      closeProxyModalBtn: document.getElementById('close-proxy-modal'),
      cancelProxyBtn: document.getElementById('cancel-proxy-button'),
      resetProxyBtn: document.getElementById('reset-proxy-button'),
      proxyType: document.getElementById('proxy-type'),
      proxyHost: document.getElementById('proxy-host'),
      proxyPort: document.getElementById('proxy-port'),
      proxyUser: document.getElementById('proxy-user'),
      proxyPass: document.getElementById('proxy-pass')
    };

    this.state = {
      active: false,
      restarting: false,
      startTime: 0,
      timerInterval: null,
      lang: 'en-US',
      theme: 'dark',
      translations: {},
      logs: [],
      logsEnabled: false,
      proxyPreferences: {
        custom_proxy_enabled: false,
        custom_proxy: {},
        active_proxy: {}
      }
    };

    this.i18n = new I18nManager(this.state);
    this.stateManager = new StateManager(this.i18n, this.elements);

    this.bindEvents();
    window.discordProxy = this;
  }

  async init() {
    try {
      if (!window.pywebview) {
        setTimeout(() => this.init(), 50);
        return;
      }

      await this.i18n.fetchAndApply();
      const initialState = await Api.getInitialState();
      this.updateState(initialState);
      this.i18n.applyTranslations();
      this.syncSettingsControls();
      this.renderLogs();
    } catch (e) {
      setTimeout(() => this.init(), 100);
    }
  }

  bindEvents() {
    this.elements.closeBtn.addEventListener('click', () => {
      if (window.pywebview) Api.closeWindow();
    });

    this.elements.minBtn.addEventListener('click', () => {
      if (window.pywebview) Api.hideWindow();
    });

    this.elements.settingsBtn.addEventListener('click', () => this.showView('settings'));
    this.elements.backBtn.addEventListener('click', () => this.showView('dashboard'));

    this.elements.themeChoices.forEach((button) => {
      button.addEventListener('click', async () => {
        const theme = button.dataset.themeChoice;
        this.state.theme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        this.syncThemeButtons();
        if (window.pywebview) {
          await Api.setTheme(theme);
        }
      });
    });

    this.elements.langSelect.addEventListener('change', async (e) => {
      await this.i18n.changeLanguage(e.target.value, this.elements.langSelect);
      this.stateManager.renderStatus();
      this.renderProxySummary();
    });

    this.elements.logToggle.addEventListener('change', async (e) => {
      this.state.logsEnabled = e.target.checked;
      if (this.state.logsEnabled && window.pywebview) {
        this.state.logs = await Api.getRecentLogs();
      }
      this.renderLogs();
    });

    this.elements.clearLogsBtn.addEventListener('click', () => {
      this.state.logs = [];
      this.renderLogs();
    });

    this.elements.customProxyToggle.addEventListener('change', async (e) => {
      if (e.target.checked) {
        this.openProxyModal();
        this.syncProxyControls();
        return;
      }
      if (window.pywebview) {
        const result = await Api.setCustomProxyEnabled(false);
        this.updateState(result);
      }
    });

    this.elements.editProxyBtn.addEventListener('click', () => this.openProxyModal());
    this.elements.closeProxyModalBtn.addEventListener('click', () => this.closeProxyModal());
    this.elements.cancelProxyBtn.addEventListener('click', () => this.closeProxyModal());
    this.elements.proxyModal.addEventListener('click', (event) => {
      if (event.target === this.elements.proxyModal) this.closeProxyModal();
    });

    this.elements.proxyForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      if (!window.pywebview) return;
      const result = await Api.setCustomProxy(this.readProxyForm());
      this.updateState(result);
      this.closeProxyModal();
    });

    this.elements.resetProxyBtn.addEventListener('click', async () => {
      if (!window.pywebview) return;
      const result = await Api.resetCustomProxy();
      this.updateState(result);
      this.closeProxyModal();
    });

    this.elements.mainActionBtn.addEventListener('click', async () => {
      if (!window.pywebview) return;
      this.elements.mainActionBtn.disabled = true;
      try {
        if (this.state.active) {
          await Api.stopDiscord();
        } else {
          this.state.restarting = true;
          this.stateManager.renderStatus();
          await Api.startDiscord();
          this.state.restarting = false;
        }
      } finally {
        this.elements.mainActionBtn.disabled = false;
        this.stateManager.renderStatus();
      }
    });

    this.elements.restartBtn.addEventListener('click', async () => {
      if (!window.pywebview || !this.state.active) return;
      this.elements.restartBtn.disabled = true;
      this.elements.mainActionBtn.disabled = true;
      this.elements.restartBtn.classList.add('spin-fast');
      this.state.restarting = true;
      this.stateManager.renderStatus();

      try {
        await Api.restartDiscord();
      } finally {
        this.state.restarting = false;
        this.elements.restartBtn.classList.remove('spin-fast');
        this.elements.restartBtn.disabled = false;
        this.elements.mainActionBtn.disabled = false;
        this.stateManager.renderStatus();
      }
    });

    if (this.elements.supportBtn) {
      this.elements.supportBtn.addEventListener('click', async () => {
        if (window.pywebview) {
          await Api.openSupportLink();
        }
      });
    }
  }

  showView(viewName) {
    const settingsActive = viewName === 'settings';
    this.elements.dashboardView.classList.toggle('active-view', !settingsActive);
    this.elements.settingsView.classList.toggle('active-view', settingsActive);
  }

  updateState(stateObj) {
    if (!stateObj) return;
    if (stateObj.proxy_preferences) {
      this.state.proxyPreferences = stateObj.proxy_preferences;
    }
    if (Array.isArray(stateObj.logs)) {
      this.state.logs = stateObj.logs;
    }
    this.stateManager.updateState(stateObj);
    this.syncSettingsControls();
    this.renderLogs();
  }

  appendLogs(logs) {
    if (!Array.isArray(logs) || logs.length === 0) return;
    this.state.logs.push(...logs);
    this.state.logs = this.state.logs.slice(-500);
    if (this.state.logsEnabled) {
      this.renderLogs();
    }
  }

  syncSettingsControls() {
    if (this.elements.langSelect) this.elements.langSelect.value = this.state.lang;
    this.syncThemeButtons();
    this.syncProxyControls();
  }

  syncThemeButtons() {
    this.elements.themeChoices.forEach((button) => {
      button.classList.toggle('active', button.dataset.themeChoice === this.state.theme);
    });
  }

  syncProxyControls() {
    const preferences = this.state.proxyPreferences || {};
    const customProxy = preferences.custom_proxy || {};
    const enabled = Boolean(preferences.custom_proxy_enabled);
    this.elements.customProxyToggle.checked = enabled;
    this.elements.editProxyBtn.disabled = !enabled && Object.keys(customProxy).length === 0;
    this.fillProxyForm(this.getProxyFormSource());
    this.renderProxySummary();
  }

  renderProxySummary() {
    const preferences = this.state.proxyPreferences || {};
    const activeProxy = preferences.active_proxy || {};
    if (preferences.custom_proxy_enabled) {
      this.elements.proxySummary.removeAttribute('data-i18n');
      this.elements.proxySummary.textContent = `${activeProxy.proxy_type || 'SOCKS5'} - ${activeProxy.host || '127.0.0.1'}:${activeProxy.port || 1080}`;
      return;
    }
    this.elements.proxySummary.setAttribute('data-i18n', 'proxy_env_summary');
    const translated = this.i18n.t('proxy_env_summary');
    this.elements.proxySummary.textContent = translated === 'proxy_env_summary' ? 'Using .env proxy settings' : translated;
  }

  fillProxyForm(settings) {
    this.elements.proxyType.value = settings.proxy_type || 'SOCKS5';
    this.elements.proxyHost.value = settings.host || '';
    this.elements.proxyPort.value = settings.port || '';
    this.elements.proxyUser.value = settings.username || '';
    this.elements.proxyPass.value = settings.password || '';
  }

  readProxyForm() {
    return {
      proxy_type: this.elements.proxyType.value,
      host: this.elements.proxyHost.value,
      port: this.elements.proxyPort.value,
      username: this.elements.proxyUser.value,
      password: this.elements.proxyPass.value
    };
  }

  openProxyModal() {
    this.fillProxyForm(this.getProxyFormSource());
    this.elements.proxyModal.classList.remove('hidden');
    setTimeout(() => this.elements.proxyHost.focus(), 0);
  }

  getProxyFormSource() {
    const preferences = this.state.proxyPreferences || {};
    const customProxy = preferences.custom_proxy || {};
    if (Object.keys(customProxy).length > 0) {
      return customProxy;
    }
    return preferences.active_proxy || {};
  }

  closeProxyModal() {
    this.elements.proxyModal.classList.add('hidden');
    this.syncProxyControls();
  }

  renderLogs() {
    this.elements.logToggle.checked = this.state.logsEnabled;
    this.elements.dashboardView.classList.toggle('logs-open', this.state.logsEnabled);
    this.elements.logPanel.classList.toggle('hidden', !this.state.logsEnabled);
    if (!this.state.logsEnabled) return;
    this.elements.logOutput.textContent = this.state.logs.join('\n');
    this.elements.logOutput.scrollTop = this.elements.logOutput.scrollHeight;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  new AppContext().init();
});
