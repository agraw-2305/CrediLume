// Theme toggle for CrediLume (light/dark)
// Uses a class on <html> so Tailwind's `dark:` variants and CSS overrides can apply.
(function () {
  'use strict';

  const STORAGE_KEY = 'credilume-theme';
  const root = document.documentElement;

  function systemPrefersDark() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  }

  function getStoredTheme() {
    try {
      const v = localStorage.getItem(STORAGE_KEY);
      return v === 'dark' || v === 'light' ? v : null;
    } catch {
      return null;
    }
  }

  function setStoredTheme(theme) {
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      // ignore
    }
  }

  function applyTheme(theme) {
    const isDark = theme === 'dark';
    root.classList.toggle('dark', isDark);
    root.dataset.theme = theme;

    const label = document.querySelector('[data-theme-label]');
    if (label) label.textContent = isDark ? 'Switch to light mode' : 'Switch to dark mode';

    const btn = document.querySelector('[data-theme-toggle]');
    if (btn) {
      btn.setAttribute('aria-pressed', String(isDark));
      btn.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
      btn.title = isDark ? 'Switch to light mode' : 'Switch to dark mode';
    }
  }

  function init() {
    const stored = getStoredTheme();
    const theme = stored || (systemPrefersDark() ? 'dark' : 'light');
    applyTheme(theme);

    const btn = document.querySelector('[data-theme-toggle]');
    if (btn) {
      btn.addEventListener('click', function () {
        const next = root.classList.contains('dark') ? 'light' : 'dark';
        setStoredTheme(next);
        applyTheme(next);
      });
    }

    // If user hasn't explicitly chosen, follow OS changes.
    if (!stored && window.matchMedia) {
      const mq = window.matchMedia('(prefers-color-scheme: dark)');
      mq.addEventListener?.('change', function (e) {
        applyTheme(e.matches ? 'dark' : 'light');
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
