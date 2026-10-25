/* Anonymous responses are sent only when the viewer chooses Send response. */
(() => {
  'use strict';
  const endpoint = document.body.dataset.feedbackUrl;
  if (!endpoint) return;
  const scope = `nightwork:${location.pathname}`;
  const feelings = new Set(['surprised', 'curious', 'resonates', 'research-connection', 'share', 'confused', 'unmoved']);
  const read = (key) => { try { return JSON.parse(localStorage.getItem(key)); } catch { return null; } };
  const write = (key, value) => { try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* Session-only when storage is unavailable. */ } };
  let token = read(`${scope}:viewer`);
  if (typeof token !== 'string' || !/^[a-f0-9-]{36}$/.test(token)) {
    token = crypto.randomUUID();
    write(`${scope}:viewer`, token);
  }
  const score = (value) => Number.isInteger(value) && value >= 1 && value <= 5 ? value : null;
  for (const panel of document.querySelectorAll('.feedback[data-artwork]')) {
    const artwork = panel.dataset.artwork;
    const key = `${scope}:response:${artwork}`;
    const previous = read(key) || {};
    const state = {
      beauty: score(previous.beauty), inspiration: score(previous.inspiration),
      feelings: Array.isArray(previous.feelings) ? [...new Set(previous.feelings.filter((x) => feelings.has(x)))] : [],
      comment: typeof previous.comment === 'string' ? previous.comment.slice(0, 2000) : '',
      savedSnapshot: typeof previous.savedSnapshot === 'string' ? previous.savedSnapshot : null,
    };
    const form = panel.querySelector('form');
    const text = panel.querySelector('textarea');
    const status = panel.querySelector('.feedback-status');
    const send = panel.querySelector('.send');
    const payload = () => ({ beauty: state.beauty, inspiration: state.inspiration, feelings: [...state.feelings].sort(), comment: state.comment.trim() });
    const snapshot = () => JSON.stringify(payload());
    const filled = () => state.beauty !== null || state.inspiration !== null || state.feelings.length || state.comment.trim();
    const message = (value, error = false) => { status.textContent = value; status.dataset.error = String(error); };
    function paint() {
      for (const button of panel.querySelectorAll('[data-score]')) {
        const dimension = button.closest('[data-dimension]').dataset.dimension;
        button.setAttribute('aria-pressed', String(state[dimension] === Number(button.dataset.score)));
      }
      for (const button of panel.querySelectorAll('[data-feeling]')) {
        button.setAttribute('aria-pressed', String(state.feelings.includes(button.dataset.feeling)));
      }
      text.value = state.comment;
      send.textContent = !filled() && state.savedSnapshot ? 'Remove response' : 'Send response';
    }
    function changed() {
      paint(); write(key, state);
      message(snapshot() === state.savedSnapshot ? 'Response saved.' : 'Not sent yet.');
    }
    paint();
    if (state.savedSnapshot === snapshot()) message('Response saved.');
    else if (filled() || state.savedSnapshot) message('Not sent yet.');
    panel.addEventListener('click', (event) => {
      const button = event.target.closest('button');
      if (!button || button.disabled) return;
      if (button.dataset.score) {
        const dimension = button.closest('[data-dimension]').dataset.dimension;
        const value = Number(button.dataset.score);
        state[dimension] = state[dimension] === value ? null : value;
        changed();
      } else if (button.dataset.feeling) {
        const value = button.dataset.feeling;
        state.feelings = state.feelings.includes(value) ? state.feelings.filter((x) => x !== value) : [...state.feelings, value];
        changed();
      } else if (button.classList.contains('clear')) {
        state.beauty = null; state.inspiration = null; state.feelings = []; state.comment = '';
        changed();
      }
    });
    text.addEventListener('input', () => {
      state.comment = text.value;
      write(key, state);
      message('Not sent yet.');
    });
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      if (!filled() && !state.savedSnapshot) { message('Choose a response or add a thought.'); return; }
      const sent = snapshot();
      for (const control of form.querySelectorAll('button,textarea')) control.disabled = true;
      message('Sending…');
      try {
        const response = await fetch(endpoint.replace(/\/$/, '') + '/feedback', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          credentials: 'omit', referrerPolicy: 'no-referrer', signal: AbortSignal.timeout(15000),
          body: JSON.stringify({ artwork_id: artwork, token, ...JSON.parse(sent) }),
        });
        const result = await response.json();
        if (!response.ok || result.ok !== true) throw new Error(result.error || 'Please try again.');
        state.savedSnapshot = result.deleted ? null : sent;
        write(key, state);
        message(result.deleted ? 'Response removed.' : 'Saved. Thank you for sharing your response.');
      } catch (error) {
        message(`Not sent. ${error.name === 'TimeoutError' ? 'The service took too long. Please try again.' : error.message || 'Please try again.'}`, true);
      } finally {
        for (const control of form.querySelectorAll('button,textarea')) control.disabled = false;
        paint();
      }
    });
  }
})();
