import json, subprocess, sys, os, re, datetime, requests
REPO=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README=os.path.join(REPO,"README.md")
def get_latest():
    result=subprocess.run([sys.executable, os.path.join(REPO,"scripts/get_latest.py")], capture_output=True, text=True, timeout=30)
    if result.returncode!=0: raise RuntimeError(result.stderr or result.stdout)
    return json.loads(result.stdout)["latest"]
def fmt(items):
    rows=[]
    for it in items[:6]:
        rows.append(f'<td align="center"><img src="{it["home_badge"]}" width="60" alt="{it["home"]}"><br><sub><strong>{it["home"]} vs {it["away"]}</strong></sub><br><img src="{it["away_badge"]}" width="60" alt="{it["away"]}"></td>')
    if not rows: return "<p>No matches today</p>"
    html=['<table><tr>']
    for i, cell in enumerate(rows):
        html.append(cell)
        if (i+1)%3==0 and i!=len(rows)-1: html.append('</tr><tr>')
    html.append('</tr></table>')
    return "\n".join(html)
def post_fb(latest):
    fb_page=os.environ.get("FB_PAGE_ID"); fb_token=os.environ.get("FB_PAGE_ACCESS_TOKEN")
    if not fb_page or not fb_token: return
    try:
        lines=["⚽ Latest Matches — Socolive TV"]
        for it in latest[:5]: lines.append(f"🔴 {it.get('home','')} vs {it.get('away','')}")
        lines.append("\n📲 https://soco-live.github.io")
        message="\n".join(lines)
        last_file=os.path.join(REPO,".fb_last_post_id")
        if os.path.exists(last_file):
            try:
                with open(last_file) as f: pid=f.read().strip()
                if pid: requests.delete(f"https://graph.facebook.com/v25.0/{pid}", params={"access_token":fb_token}, timeout=15)
            except: pass
        badge=latest[0].get("home_badge") if latest else None
        if badge and badge.startswith("http"):
            url=f"https://graph.facebook.com/v25.0/{fb_page}/photos"; data={"url":badge,"message":message,"access_token":fb_token}
        else:
            url=f"https://graph.facebook.com/v25.0/{fb_page}/feed"; data={"message":message,"access_token":fb_token}
        r=requests.post(url, data=data, timeout=30); j=r.json()
        if "id" in j:
            with open(last_file,"w") as f: f.write(j["id"])
    except: pass
def update():
    latest=get_latest(); block=fmt(latest)
    with open(README,"r",encoding="utf-8") as f: txt=f.read()
    new=re.sub(r'<!-- LATEST_START -->.*?<!-- LATEST_END -->', f'<!-- LATEST_START -->\n{block}\n<!-- LATEST_END -->', txt, flags=re.DOTALL)
    if new!=txt:
        with open(README,"w",encoding="utf-8") as f: f.write(new)
        post_fb(latest)
    else:
        post_fb(latest)
if __name__=="__main__": update()
