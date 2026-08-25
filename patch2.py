import re

with open("auth.html", "r") as f:
    html = f.read()

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

# regex replace
html = re.sub(r'function switchTab\(id\) \{[\s\S]*?history\.replaceState\(null, \'\', `\?mode=\$\{id\}`\);\n\}', switch_tab_new, html)

# also check if the catch_block matched:
catch_new = """    if (body.success && body.guest_token) {
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
    btn.innerHTML = 'Enter as Guest';
  }
}"""
# Wait, I'll just regex replace the catch block in handleGuest
html = re.sub(r'\} catch \(err\) \{\n\s*showError\(err.message\);\n\s*btn.disabled = false;\n\s*btn.textContent = \'Enter as Guest\';\n\s*\}', 
    "} catch (err) {\n    if (turnstileWidgetId !== null) turnstile.reset(turnstileWidgetId);\n    showError(err.message);\n    btn.disabled = false;\n    btn.textContent = 'Enter as Guest';\n  }", html)

with open("auth.html", "w") as f:
    f.write(html)
