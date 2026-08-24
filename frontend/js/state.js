export class StateManager {
  constructor(i18n, elements) {
    this.i18n = i18n;
    this.elements = elements;
    this.state = i18n.state;
  }

  updateState(stateObj) {
    if (stateObj.hasOwnProperty('geo')) {
      this.state.geo = stateObj.geo;
    }
    if (stateObj.hasOwnProperty('country')) {
      this.state.country = stateObj.country;
    }
    
    if (stateObj.hasOwnProperty('active')) {
      const isNowActive = stateObj.active;
      if (isNowActive !== this.state.active) {
        this.state.active = isNowActive;
        this.renderStatus();
      }
    }
    if (stateObj.hasOwnProperty('lang') && stateObj.lang !== this.state.lang) {
      this.state.lang = stateObj.lang;
      if (this.elements.langSelect) this.elements.langSelect.value = stateObj.lang;
      this.i18n.fetchAndApply();
    }
    if (stateObj.hasOwnProperty('theme') && stateObj.theme !== this.state.theme) {
      this.state.theme = stateObj.theme;
      document.documentElement.setAttribute('data-theme', this.state.theme);
    }
  }

  renderStatus() {
    this.elements.shield.className = 'status-shield';
    
    if (this.state.restarting) {
      this.elements.shield.classList.add('restarting');
      this.elements.statusText.setAttribute('data-i18n', 'status_validating');
      this.elements.statusText.textContent = this.i18n.t('status_validating');
      this.elements.timerBox.classList.add('hidden');
      this.elements.restartBtn.classList.add('hidden');
      return;
    }

    if (this.state.active) {
      this.elements.shield.classList.add('connected');
      
      if (this.state.geo && this.state.geo !== 'Unknown') {
        this.elements.statusText.setAttribute('data-i18n', 'status_connected_geo');
        const text = this.i18n.t('status_connected_geo')
          .replace('{city}', this.state.geo)
          .replace('{country}', this.state.country || 'US');
        this.elements.statusText.textContent = text;
      } else {
        this.elements.statusText.setAttribute('data-i18n', 'status_connected');
        this.elements.statusText.textContent = this.i18n.t('status_connected');
      }
      
      this.elements.mainActionBtn.setAttribute('data-i18n', 'btn_disconnect');
      this.elements.mainActionBtn.textContent = this.i18n.t('btn_disconnect');
      
      this.elements.restartBtn.classList.remove('hidden');
      this.elements.timerBox.classList.remove('hidden');
      this.startTimer();
    } else {
      this.elements.shield.classList.add('idle');
      this.elements.statusText.setAttribute('data-i18n', 'status_disconnected');
      this.elements.statusText.textContent = this.i18n.t('status_disconnected');

      this.elements.mainActionBtn.setAttribute('data-i18n', 'btn_connect');
      this.elements.mainActionBtn.textContent = this.i18n.t('btn_connect');

      this.elements.restartBtn.classList.add('hidden');
      this.elements.timerBox.classList.add('hidden');
      this.stopTimer();
    }
  }

  startTimer() {
    if (this.state.timerInterval) return;
    this.state.startTime = Date.now();
    this.updateTimerDisplay();
    this.state.timerInterval = setInterval(() => this.updateTimerDisplay(), 1000);
  }

  stopTimer() {
    if (this.state.timerInterval) {
      clearInterval(this.state.timerInterval);
      this.state.timerInterval = null;
    }
    this.elements.timerValue.textContent = '00:00:00';
  }

  updateTimerDisplay() {
    const elapsed = Math.floor((Date.now() - this.state.startTime) / 1000);
    const h = String(Math.floor(elapsed / 3600)).padStart(2, '0');
    const m = String(Math.floor((elapsed % 3600) / 60)).padStart(2, '0');
    const s = String(elapsed % 60).padStart(2, '0');
    this.elements.timerValue.textContent = `${h}:${m}:${s}`;
  }
}
