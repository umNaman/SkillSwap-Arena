import re

with open("auth.html", "r") as f:
    html = f.read()

# 1. Modify switchTab
switch_tab_orig = """function switchTab(id) {
  document.querySelectorAll('.auth-tab').forEach(t => { t.classList.remove('active'); t.setAttribute('aria-selected','false'); });
  document.querySelectorAll('.auth-panel').forEach(p => p.classList.remove('active'));
  document.getElementById('tab-'+id).classList.add('active');
  document.getElementById('tab-'+id).setAttribute('aria-selected','true');
  document.getElementById('panel-'+id).classList.add('active');
  const d = TEXT_DATA[id] || ['', ''];
  document.getElementById('auth-title').innerHTML = d[0];
  document.getElementById('auth-subtitle').innerHTML = d[1];
  clearError();
  history.replaceState(null, '', `?mode=${id}`);
}"""

switch_tab_new = """let turnstileWidgetId = null;
async function initTurnstile() {
  if (turnstileWidgetId !== null) return;
  try {
    const res = await fetch(`${API_BASE}/api/auth/config/turnstile`);
    const data = await res.json();
    const siteKey = data.site_key;
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    turnstileWidgetId = turnstile.render('#turnstile-container', {
      sitekey: siteKey,
      theme: isDark ? 'dark' : 'light',
    });
  } catch (err) {
    console.error("Turnstile config fetch failed", err);
  }
}

function switchTab(id) {
  document.querySelectorAll('.auth-tab').forEach(t => { t.classList.remove('active'); t.setAttribute('aria-selected','false'); });
  document.querySelectorAll('.auth-panel').forEach(p => p.classList.remove('active'));
  document.getElementById('tab-'+id).classList.add('active');
  document.getElementById('tab-'+id).setAttribute('aria-selected','true');
  document.getElementById('panel-'+id).classList.add('active');
  const d = TEXT_DATA[id] || ['', ''];
  document.getElementById('auth-title').innerHTML = d[0];
  document.getElementById('auth-subtitle').innerHTML = d[1];
  clearError();
  history.replaceState(null, '', `?mode=${id}`);
  
  if (id === 'guest') {
    initTurnstile();
  }
}"""

html = html.replace(switch_tab_orig, switch_tab_new)

# 2. Modify handleGuest
handle_guest_orig = """async function handleGuest() {
  clearError();
  const rawAlias = document.getElementById('guest-alias').value.trim();
  const alias = rawAlias.slice(0, 14); // enforce schema max_length=14
  if (!alias) { showError('Please enter an alias to continue.'); return; }

  const btn = document.getElementById('btn-guest');
  btn.disabled = true;
  btn.innerHTML = '<div class="spinner"></div> Entering…';

  try {
    const res = await fetch(`${API_BASE}/api/auth/anonymous`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ alias, cohort_code: null }),
    });"""

handle_guest_new = """async function handleGuest() {
  clearError();
  const rawAlias = document.getElementById('guest-alias').value.trim();
  const alias = rawAlias.slice(0, 14); // enforce schema max_length=14
  if (!alias) { showError('Please enter an alias to continue.'); return; }
  
  let turnstileToken = null;
  if (turnstileWidgetId !== null) {
      turnstileToken = turnstile.getResponse(turnstileWidgetId);
  }
  if (!turnstileToken) {
      showError('Please complete the CAPTCHA to continue as guest.');
      return;
  }

  const btn = document.getElementById('btn-guest');
  btn.disabled = true;
  btn.innerHTML = '<div class="spinner"></div> Entering…';

  try {
    const res = await fetch(`${API_BASE}/api/auth/anonymous`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ alias, cohort_code: null, turnstile_token: turnstileToken }),
    });"""

html = html.replace(handle_guest_orig, handle_guest_new)

# If validation fails in try catch, we should reset the turnstile
catch_block_orig = """    if (body.success && body.guest_token) {
      sessionStorage.setItem('ss_guest_token', body.guest_token);
      sessionStorage.setItem('ss_guest_id', body.guest_id);
      sessionStorage.setItem('ss_alias', body.alias);
      localStorage.removeItem('ss_token');
      window.location.href = '/app';
    } else {
      throw new Error("Invalid guest login response.");
    }
  } catch (err) {
    showError(err.message);
    btn.disabled = false;
    btn.textContent = 'Enter as Guest';
  }
}"""

catch_block_new = """    if (body.success && body.guest_token) {
      sessionStorage.setItem('ss_guest_token', body.guest_token);
      sessionStorage.setItem('ss_guest_id', body.guest_id);
      sessionStorage.setItem('ss_alias', body.alias);
      localStorage.removeItem('ss_token');
      window.location.href = '/app';
    } else {
      throw new Error("Invalid guest login response.");
    }
  } catch (err) {
    if (turnstileWidgetId !== null) turnstile.reset(turnstileWidgetId);
    showError(err.message);
    btn.disabled = false;
    btn.textContent = 'Enter as Guest';
  }
}"""

html = html.replace(catch_block_orig, catch_block_new)

# 3. Add to window load so if guest is active initially, it loads
init_tab_orig = """const params = new URLSearchParams(window.location.search);
const initMode = params.get('mode') || 'signin';
if (TEXT_DATA[initMode]) {
  switchTab(initMode);
} else {
  switchTab('signin');
}"""

init_tab_new = """const params = new URLSearchParams(window.location.search);
const initMode = params.get('mode') || 'signin';
if (TEXT_DATA[initMode]) {
  switchTab(initMode);
} else {
  switchTab('signin');
}"""

# I already modified switchTab so calling it at init will automatically trigger initTurnstile.

with open("auth.html", "w") as f:
    f.write(html)
print("done patching auth.html")
