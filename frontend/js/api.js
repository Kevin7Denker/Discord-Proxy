export class Api {
  static async startDiscord() {
    return await window.pywebview.api.start_discord();
  }

  static async stopDiscord() {
    return await window.pywebview.api.stop_discord();
  }

  static async restartDiscord() {
    return await window.pywebview.api.restart_discord();
  }

  static async hideWindow() {
    return await window.pywebview.api.hide_window();
  }

  static async closeWindow() {
    return await window.pywebview.api.close_window();
  }

  static async setTheme(theme) {
    return await window.pywebview.api.set_theme(theme);
  }

  static async setLanguage(lang) {
    return await window.pywebview.api.set_language(lang);
  }

  static async getTranslations() {
    return await window.pywebview.api.get_translations();
  }

  static async getInitialState() {
    return await window.pywebview.api.get_initial_state();
  }

  static async openSupportLink() {
    return await window.pywebview.api.open_support_link();
  }

  static async setCustomProxy(settings) {
    return await window.pywebview.api.set_custom_proxy(settings);
  }

  static async setCustomProxyEnabled(enabled) {
    return await window.pywebview.api.set_custom_proxy_enabled(enabled);
  }

  static async resetCustomProxy() {
    return await window.pywebview.api.reset_custom_proxy();
  }

  static async getRecentLogs() {
    return await window.pywebview.api.get_recent_logs();
  }
}
