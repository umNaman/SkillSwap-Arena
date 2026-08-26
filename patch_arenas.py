import re

# -------------
# index.html
# -------------
with open("index.html", "r") as f:
    html = f.read()

# Current index.html segments
# GD
gd_orig = """      <a href="/auth" class="arena-card primary reveal" id="arena-gd">
        <div class="arena-badge">● Live Now</div>
        <div class="arena-icon">💬</div>
        <h3>Group Discussion</h3>
        <p>6 anonymous participants. A random topic. 2 minutes to prepare, then 13 minutes to make your case, listen actively, and lead.</p>
        <div class="arena-meta">
          <span>3–6 members</span>
          <span>·</span>
          <span>2 min prep + 13 min live</span>
          <span>·</span>
          <span>Live &amp; active</span>
        </div>
      </a>"""

# Debate
debate_orig = """      <div class="arena-card reveal reveal-delay-1" id="arena-debate">
        <div class="arena-badge coming-soon">Coming Soon</div>
        <div class="arena-icon">⚖️</div>
        <h3>Debate Arena</h3>
        <p>Structured for-and-against debates. Argue your assigned position, then switch. Sharpens persuasion and rebuttals.</p>
        <div class="arena-meta">
          <span>4–6 members</span>
          <span>·</span>
          <span>Structured format</span>
        </div>
      </div>"""

# Coding
coding_orig = """      <div class="arena-card reveal reveal-delay-2" id="arena-code">
        <div class="arena-badge coming-soon">Coming Soon</div>
        <div class="arena-icon">⌨️</div>
        <h3>Coding Arena</h3>
        <p>Pair-programming style technical rounds. Think-aloud your approach. Peer-reviewed solutions and communication.</p>
        <div class="arena-meta">
          <span>1–2 members</span>
          <span>·</span>
          <span>Problem-solving</span>
        </div>
      </div>"""

# Mock
mock_orig = """      <div class="arena-card reveal reveal-delay-3" id="arena-mock">
        <div class="arena-badge coming-soon">Coming Soon</div>
        <div class="arena-icon">🎙️</div>
        <h3>Mock Interview</h3>
        <p>Anonymous one-on-one interview practice focused on structured answers, confidence, and clear communication.</p>
        <div class="arena-meta">
          <span>1-on-1</span>
          <span>·</span>
          <span>Interview practice</span>
        </div>
      </div>"""

# New Coding for index.html
coding_new = """      <a href="/coding-arena" class="arena-card primary reveal reveal-delay-1" id="arena-code">
        <div class="arena-badge">● Live Now</div>
        <div class="arena-icon">⌨️</div>
        <h3>Coding Arena</h3>
        <p>Pair-programming style technical rounds. Think-aloud your approach. Peer-reviewed solutions and communication.</p>
        <div class="arena-meta">
          <span>1–2 members</span>
          <span>·</span>
          <span>Problem-solving</span>
          <span>·</span>
          <span>Live &amp; active</span>
        </div>
      </a>"""

# New Debate for index.html (shifted delay)
debate_new = """      <div class="arena-card reveal reveal-delay-2" id="arena-debate">
        <div class="arena-badge coming-soon">Coming Soon</div>
        <div class="arena-icon">⚖️</div>
        <h3>Debate Arena</h3>
        <p>Structured for-and-against debates. Argue your assigned position, then switch. Sharpens persuasion and rebuttals.</p>
        <div class="arena-meta">
          <span>4–6 members</span>
          <span>·</span>
          <span>Structured format</span>
        </div>
      </div>"""

# Ensure we replace exactly the block of cards
old_block = f"{gd_orig}\n\n{debate_orig}\n\n{coding_orig}\n\n{mock_orig}"
new_block = f"{gd_orig}\n\n{coding_new}\n\n{debate_new}\n\n{mock_orig}"

if old_block in html:
    html = html.replace(old_block, new_block)
else:
    print("Could not find old_block in index.html!")

html = html.replace("Coding Interview", "Coding Arena")

with open("index.html", "w") as f:
    f.write(html)
print("Updated index.html")


# -------------
# app.html
# -------------
with open("app.html", "r") as f:
    html = f.read()

# In app.html, cards are like this:
gd_app = """          <div class="arena-card reveal" id="dash-arena-gd" onclick="startGDFlow()">
            <div class="arena-status live"><div class="live-dot"></div> Live</div>
            <div class="arena-card-icon">💬</div>
            <div class="arena-card-name">Group Discussion</div>
            <div class="arena-card-desc">Talk, Listen, Lead.</div>
            <div class="arena-card-meta">
              <span id="gd-seats-info">3–6 members</span>
            </div>
          </div>"""

debate_app = """          <div class="arena-card soon reveal">
            <div class="arena-status soon">⋯ Coming Soon</div>
            <div class="arena-card-icon">⚖️</div>
            <div class="arena-card-name">Debate Arena</div>
            <div class="arena-card-desc">Argue, Persuade, Win.</div>
            <div class="arena-card-meta">4–6 members</div>
          </div>"""

coding_app = """          <div class="arena-card reveal" onclick="window.location.href='/coding-arena'" role="link" tabindex="0" onkeydown="if(event.key==='Enter')window.location.href='/coding-arena'">
            <div class="arena-status live"><div class="live-dot"></div> Live</div>
            <div class="arena-card-icon">⌨️</div>
            <div class="arena-card-name">CODING ARENA</div>
            <div class="arena-card-desc">Solve. Compete. Improve.</div>
            <div class="arena-card-meta">1–2 members</div>
          </div>"""

mock_app = """          <div class="arena-card soon reveal">
            <div class="arena-status soon">⋯ Coming Soon</div>
            <div class="arena-card-icon">🎙️</div>
            <div class="arena-card-name">Mock Interview</div>
            <div class="arena-card-desc">Prepare, Perform, Ace.</div>
            <div class="arena-card-meta">1-on-1</div>
          </div>"""

coding_app_new = coding_app.replace("CODING ARENA", "Coding Arena")

old_block_app = f"{gd_app}\n{debate_app}\n{coding_app}\n{mock_app}"
new_block_app = f"{gd_app}\n{coding_app_new}\n{debate_app}\n{mock_app}"

if old_block_app in html:
    html = html.replace(old_block_app, new_block_app)
else:
    print("Could not find old_block_app in app.html!")

html = html.replace("Coding Interview", "Coding Arena")

with open("app.html", "w") as f:
    f.write(html)
print("Updated app.html")

