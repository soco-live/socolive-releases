import json, subprocess, sys, os, re, datetime, requests

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(REPO, "README.md")
INDEX = os.path.join(REPO, "index.html")

def get_latest():
    result = subprocess.run([sys.executable, os.path.join(REPO, "scripts/get_latest.py")], capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)
    return json.loads(result.stdout)["latest"]

def fmt_readme(items):
    rows = []
    for it in items[:6]:
        rows.append(f'<td align="center"><a href="#download"><img src="{it["home_badge"]}" width="60" alt="{it["home"]}"><br><sub><strong>{it["home"]} vs {it["away"]}</strong></sub><br><img src="{it["away_badge"]}" width="60" alt="{it["away"]}"></a></td>')
    if not rows:
        return "<p>No matches today</p>"
    html = ['<table><tr>']
    for i, cell in enumerate(rows):
        html.append(cell)
        if (i + 1) % 3 == 0 and i != len(rows) - 1:
            html.append('</tr><tr>')
    html.append('</tr></table>')
    return "\n".join(html)

def fmt_html_matches(items):
    badges = ["FOOTBALL LIVE", "MATCH DAY", "KICK OFF", "LIVE STREAMS"]
    day_badge = badges[datetime.date.today().toordinal() % len(badges)]
    cards = []
    for it in items[:7]:
        home = it.get("home", "Home")
        away = it.get("away", "Away")
        home_badge = it.get("home_badge", "")
        away_badge = it.get("away_badge", "")
        cards.append(f'''        <a href="#download" style="display:flex;align-items:center;gap:8px;padding:8px 10px;background:rgba(34,197,94,0.08);border-radius:10px;border-left:3px solid #22c55e;text-decoration:none;color:inherit">
          <div style="display:flex;align-items:center;gap:6px;flex-shrink:0">
            <img src="{home_badge}" alt="{home}" style="height:32px;width:auto" loading="lazy">
            <span style="font-weight:700;color:var(--c-text-muted);font-size:0.75rem">VS</span>
            <img src="{away_badge}" alt="{away}" style="height:32px;width:auto" loading="lazy">
          </div>
          <div style="flex:1;min-width:0">
            <div style="display:flex;align-items:center;gap:5px">
              <span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#22c55e"></span>
              <span style="font-size:0.6rem;font-weight:700;color:#22c55e;letter-spacing:0.04em">TODAY</span>
              <span style="font-size:0.55rem;color:var(--c-text-muted)">| Fixture</span>
            </div>
            <div style="font-weight:600;font-size:0.75rem;color:var(--c-text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{home} vs {away}</div>
          </div>
        </a>''')

    inner = "\n".join(cards) if cards else '        <div class="py-4 text-center text-xs text-[var(--c-text-muted)]">No matches scheduled today</div>'

    return f'''      <div class="promo-card">
        <div class="promo-badge">{day_badge}</div>
        <div style="display:flex;flex-direction:column;gap:6px;margin-top:4px">
{inner}
        </div>
        <a href="#download" class="promo-btn" style="margin-top:12px;display:flex;align-items:center;justify-content:center;gap:8px;width:100%;padding:10px;border-radius:10px;background:var(--c-primary);color:#ffffff;font-weight:700;font-size:0.8rem;text-decoration:none">
          <i class="fa-solid fa-play"></i> Watch Live Matches on TV & Phone
        </a>
      </div>'''

def post_fb(latest):
    fb_page = os.environ.get("FB_PAGE_ID")
    fb_token = os.environ.get("FB_PAGE_ACCESS_TOKEN")
    if not fb_page or not fb_token:
        return
    try:
        lines = ["⚽ Latest Matches — Socolive TV"]
        for it in latest[:5]:
            lines.append(f"🔴 {it.get('home', '')} vs {it.get('away', '')}")
        lines.append("\n📲 https://football.tvphone.com#download")
        message = "\n".join(lines)
        last_file = os.path.join(REPO, ".fb_last_post_id")
        if os.path.exists(last_file):
            try:
                with open(last_file) as f:
                    pid = f.read().strip()
                if pid:
                    requests.delete(f"https://graph.facebook.com/v25.0/{pid}", params={"access_token": fb_token}, timeout=15)
            except:
                pass
        badge = latest[0].get("home_badge") if latest else None
        if badge and badge.startswith("http"):
            url = f"https://graph.facebook.com/v25.0/{fb_page}/photos"
            data = {"url": badge, "message": message, "access_token": fb_token}
        else:
            url = f"https://graph.facebook.com/v25.0/{fb_page}/feed"
            data = {"message": message, "access_token": fb_token}
        r = requests.post(url, data=data, timeout=30)
        j = r.json()
        if "id" in j:
            with open(last_file, "w") as f:
                f.write(j["id"])
    except:
        pass

def update():
    latest = get_latest()

    # 1. Update index.html (Static SEO pre-rendering for Googlebot)
    if os.path.exists(INDEX):
        html_block = fmt_html_matches(latest)
        with open(INDEX, "r", encoding="utf-8") as f:
            idx_txt = f.read()
        new_idx = re.sub(r'<!-- MATCHES_START -->.*?<!-- MATCHES_END -->', f'<!-- MATCHES_START -->\n{html_block}\n      <!-- MATCHES_END -->', idx_txt, flags=re.DOTALL)
        if new_idx != idx_txt:
            with open(INDEX, "w", encoding="utf-8") as f:
                f.write(new_idx)

    # 3. Post to Facebook
    post_fb(latest)

if __name__ == "__main__":
    update()
