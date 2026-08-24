import { Api } from './api.js';

export class I18nManager {
  constructor(state) {
    this.state = state;
  }

  async fetchAndApply() {
    if (window.pywebview) {
      this.state.translations = await Api.getTranslations();
      this.applyTranslations();
    }
  }

  t(key) {
    return this.state.translations[key] || key;
  }

  applyTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (this.state.translations[key]) {
        el.textContent = this.state.translations[key];
      }
    });
  }

  async changeLanguage(lang, selectEl) {
    if (window.pywebview) {
      await Api.setLanguage(lang);
      this.state.lang = lang;
      if (selectEl) selectEl.value = lang;
      await this.fetchAndApply();
    }
  }
}
