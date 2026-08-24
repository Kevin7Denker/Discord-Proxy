import { Api } from './api.js?v=2';
import { I18nManager } from './i18n.js?v=2';
import { StateManager } from './state.js?v=2';

class AppContext {
  constructor() {
    this.elements = {
      closeBtn: document.getElementById('close-button'),
      minBtn: document.getElementById('minimize-button'),
      themeBtn: document.getElementById('theme-button'),
      shield: document.getElementById('hero-shield'),
      statusText: document.getElementById('status-text'),
      timerBox: document.getElementById('timer-box'),
      timerValue: document.getElementById('session-timer'),
      mainActionBtn: document.getElementById('main-action-button'),
      restartBtn: document.getElementById('restart-button'),
      langSelect: document.getElementById('lang-select'),
      supportBtn: document.getElementById('support-button')
    };

    this.state = {
      active: false,
      restarting: false,
      startTime: 0,
      timerInterval: null,
      lang: 'en-US',
      theme: 'dark',
      translations: {}
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

    this.elements.themeBtn.addEventListener('click', async () => {
      this.state.theme = this.state.theme === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', this.state.theme);
      if (window.pywebview) {
        await Api.setTheme(this.state.theme);
      }
    });

    this.elements.langSelect.addEventListener('change', async (e) => {
      await this.i18n.changeLanguage(e.target.value, this.elements.langSelect);
      this.stateManager.renderStatus();
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

  updateState(stateObj) {
    this.stateManager.updateState(stateObj);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  new AppContext().init();
});
