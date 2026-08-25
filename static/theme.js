(() => {
  const STORAGE_KEY = 'skillswap-theme';
  const root = document.documentElement;
  const validTheme = value => value === 'dark' || value === 'light';

  const getCookieTheme = () => {
    try {
      const value = document.cookie
        .split('; ')
        .find(entry => entry.startsWith(`${STORAGE_KEY}=`))
        ?.split('=')[1];
      return validTheme(value) ? value : null;
    } catch {
      return null;
    }
  };

  const getSavedTheme = () => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (validTheme(saved)) return saved;
    } catch {
      /* Privacy-restricted contexts can disable localStorage. */
    }
    return getCookieTheme();
  };

  const getPreferredTheme = () => {
    const saved = getSavedTheme();
    if (saved) return saved;
    return window.matchMedia?.('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  };

  const icon = theme => theme === 'dark'
    ? '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 3a9 9 0 1 0 9 9 7 7 0 0 1-9-9Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>'
    : '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="4" stroke="currentColor" stroke-width="1.8"/><path d="M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32 1.41 1.41M2 12h2m16 0h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';

  const syncControls = theme => {
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      const next = theme === 'dark' ? 'light' : 'dark';
      button.innerHTML = icon(theme);
      button.setAttribute('aria-label', `Switch to ${next} mode`);
      button.setAttribute('title', `Switch to ${next} mode`);
      button.setAttribute('aria-pressed', String(theme === 'light'));
    });
    document.querySelector('meta[name="theme-color"]')?.setAttribute(
      'content',
      theme === 'light' ? '#F8FAFC' : '#080B0F'
    );
  };

  const setTheme = (theme, persist = true) => {
    if (!validTheme(theme)) return;
    const heroImage =
      theme === 'dark'
        ? '/static/hero-dark.png'
        : '/static/hero-light.png';

    root.dataset.theme = theme;
    root.style.setProperty('--hero-image', `url('${heroImage}')`);
    if (persist) {
      try {
        localStorage.setItem(STORAGE_KEY, theme);
      } catch {
        document.cookie = `${STORAGE_KEY}=${theme}; Max-Age=31536000; Path=/; SameSite=Lax`;
      }
    }
    if (document.readyState !== 'loading') syncControls(theme);
    window.dispatchEvent(new CustomEvent('skillswap:themechange', { detail: { theme } }));
  };

  setTheme(getPreferredTheme(), false);
  window.SkillSwapTheme = { get: () => root.dataset.theme, set: setTheme };

  const initializeControls = () => {
    syncControls(root.dataset.theme);
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      button.addEventListener('click', () => {
        setTheme(root.dataset.theme === 'dark' ? 'light' : 'dark');
      });
    });
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeControls, { once: true });
  } else {
    initializeControls();
  }
})();
