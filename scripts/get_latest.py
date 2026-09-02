import httpx, json, sys
# Use SportsRC fallback — json.vnres.co now 403 even with referer, sportsrc proven 200
def get_latest():
    with httpx.Client(timeout=15, follow_redirects=True, headers={"User-Agent":"Mozilla/5.0"}) as c:
        r = c.get("https://api.sportsrc.org/", params={"data":"matches","category":"football"})
        r.raise_for_status()
        j=r.json()
        out=[]
        # mimic get_latest.py: filter today like promo does
        from datetime import datetime
        today=datetime.now().strftime("%Y%m%d")
        for m in j.get("data", [])[:30]:
            mt=m["date"]//1000
            if datetime.fromtimestamp(mt).strftime("%Y%m%d")!=today:
                continue
            out.append({"title": m["title"], "home": m["teams"]["home"]["name"], "away": m["teams"]["away"]["name"], "home_badge": m["teams"]["home"]["badge"], "away_badge": m["teams"]["away"]["badge"], "league": m.get("category","football")})
            if len(out)>=6:
                break
        # if today empty, fallback to first 6 overall
        if not out:
            for m in j.get("data", [])[:6]:
                out.append({"title": m["title"], "home": m["teams"]["home"]["name"], "away": m["teams"]["away"]["name"], "home_badge": m["teams"]["home"]["badge"], "away_badge": m["teams"]["away"]["badge"], "league": m.get("category","football")})
        return out

if __name__=="__main__":
    print(json.dumps({"latest": get_latest()}, indent=2))
