import re

with open("auth.html", "r") as f:
    html = f.read()

switch_tab_orig = """function switchTab(id) {
  document.querySelectorAll('.auth-tab').forEach(t => { t.classList.remove('active'); t.setAttribute('aria-selected','false'); });
  document.querySelectorAll('.auth-panel').forEach(p => p.classList.remove('active'));
  document.getElementById('tab-'+id).classList.add('active');
  document.getElementById('tab-'+id).setAttribute('aria-selected','true');
  document.getElementById('panel-'+id).classList.add('active');
  document.getElementById('auth-error').classList.remove('visible');
  const [h, s] = TAB_HEADINGS[id];
  document.getElementById('auth-heading-text') && (document.getElementById('auth-heading-text').innerHTML = h);
  document.querySelector('.auth-heading').innerHTML = h;
  document.getElementById('auth-sub-text').textContent = s;
}"""

switch_tab_new = """let turnstileWidgetId = null;
async function initTurnstile() {
  if (turnstileWidgetId !== null) return;
  try {
    const res = await fetch(`${window.API_BASE || ''}/api/auth/config/turnstile`);
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
  document.getElementById('auth-error').classList.remove('visible');
  const [h, s] = TAB_HEADINGS[id];
  document.getElementById('auth-heading-text') && (document.getElementById('auth-heading-text').innerHTML = h);
  document.querySelector('.auth-heading').innerHTML = h;
  document.getElementById('auth-sub-text').textContent = s;
  
  if (id === 'guest') {
    initTurnstile();
  }
}"""

if switch_tab_orig in html:
    html = html.replace(switch_tab_orig, switch_tab_new)
    with open("auth.html", "w") as f:
        f.write(html)
    print("Patched successfully")
else:
    print("Could not find switchTab_orig")
