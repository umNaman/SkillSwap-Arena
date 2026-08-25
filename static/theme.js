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

  const initUserDropdown = () => {
    const avatarEl = document.getElementById('topbar-avatar') || document.getElementById('ca-user');
    if (!avatarEl || avatarEl.closest('.user-dropdown-wrapper')) return;

    let user = null;
    try { user = JSON.parse(localStorage.getItem('ss_user') || 'null'); } catch {}
    const isGuest = !!sessionStorage.getItem('ss_guest_token');
    const alias = sessionStorage.getItem('ss_alias') || localStorage.getItem('ss_alias') || user?.default_alias || 'Coder';
    const email = user?.email || '';

    const wrapper = document.createElement('div');
    wrapper.className = 'user-dropdown-wrapper';
    
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'user-dropdown-btn';
    btn.setAttribute('aria-label', 'User menu');
    btn.setAttribute('aria-expanded', 'false');
    
    avatarEl.parentNode.insertBefore(wrapper, avatarEl);
    btn.appendChild(avatarEl);
    wrapper.appendChild(btn);

    const menu = document.createElement('div');
    menu.className = 'user-dropdown-menu';
    
    const emailHtml = email ? `<div class="user-dropdown-email">${email.replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}</div>` : '';
    const safeAlias = alias.replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
    
    menu.innerHTML = `
      <div class="user-dropdown-header">
        <div class="user-dropdown-name">${safeAlias}</div>
        ${emailHtml}
      </div>
      <button type="button" class="user-dropdown-item" id="dd-dashboard">Dashboard</button>
      <button type="button" class="user-dropdown-item" id="dd-progress">My Progress</button>
      <button type="button" class="user-dropdown-item" id="dd-history">Session History</button>
      <div class="user-dropdown-divider"></div>
      <button type="button" class="user-dropdown-item danger" id="dd-logout">${isGuest ? 'Sign In / Exit Guest Session' : 'Log out'}</button>
    `;
    wrapper.appendChild(menu);

    const toggle = (e) => {
      e?.stopPropagation();
      const isOpen = menu.classList.contains('open');
      menu.classList.toggle('open', !isOpen);
      btn.setAttribute('aria-expanded', !isOpen);
    };

    btn.addEventListener('click', toggle);

    document.addEventListener('click', (e) => {
      if (!wrapper.contains(e.target)) {
        menu.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        menu.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
      }
    });

    document.getElementById('dd-dashboard').addEventListener('click', () => {
      if (window.location.pathname.includes('coding-arena')) window.location.href = '/app';
      else if (typeof showScreen === 'function') showScreen('dashboard');
      menu.classList.remove('open');
    });

    document.getElementById('dd-progress').addEventListener('click', () => {
      if (window.location.pathname.includes('coding-arena') && typeof showView === 'function') {
        showView('history');
      } else {
        if (window.location.pathname.includes('coding-arena')) {
           window.location.href = '/app';
        } else if (typeof showScreen === 'function') {
           showScreen('dashboard');
        }
      }
      menu.classList.remove('open');
    });

    document.getElementById('dd-history').addEventListener('click', () => {
      if (window.location.pathname.includes('coding-arena') && typeof showView === 'function') {
        showView('history');
      } else if (typeof showScreen === 'function') {
        showScreen('history');
      } else {
        window.location.href = '/app';
      }
      menu.classList.remove('open');
    });

    document.getElementById('dd-logout').addEventListener('click', () => {
      if (typeof handleLogout === 'function') {
        handleLogout();
      } else {
        localStorage.removeItem('ss_token');
        localStorage.removeItem('ss_user');
        sessionStorage.removeItem('ss_guest_token');
        sessionStorage.removeItem('ss_guest_id');
        sessionStorage.removeItem('ss_alias');
        window.location.href = '/login_page.html';
      }
    });
  };

  // Attach to DOMContentLoaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initUserDropdown);
  } else {
    initUserDropdown();
  }
