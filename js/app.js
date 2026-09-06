function initTheme() {
  const storedTheme = localStorage.getItem("tvphone-theme");
  if (storedTheme) {
    document.documentElement.setAttribute("data-theme", storedTheme);
  } else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
    document.documentElement.setAttribute("data-theme", "dark");
  } else {
    document.documentElement.setAttribute("data-theme", "light");
  }
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme");
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("tvphone-theme", next);
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function getFallbackPromo() {
  return `
    <div class="promo-card">
      <div class="promo-badge">FOOTBALL LIVE</div>
      <div class="promo-content text-center py-3">
        <span class="promo-meta text-xs font-bold text-[var(--c-primary)] mb-1 block"><i class="fa-solid fa-futbol"></i> Premier League, UCL & World Leagues</span>
        <h3 class="text-base font-bold text-[var(--c-text)] mb-2">Live Football on Android TV & Phone</h3>
        <p class="text-xs text-[var(--c-text-secondary)] mb-3 leading-relaxed">Watch live football fixtures with remote D-pad controls and mobile touch playback. Real-time scores and zero buffering.</p>
        <a href="#download" class="promo-btn inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-[var(--c-primary)] text-white no-underline"><i class="fa-solid fa-cloud-arrow-down"></i> Download Socolive TV</a>
      </div>
    </div>
  `;
}

async function loadLiveMatches() {
  const container = document.getElementById("dynamic-promo");
  if (!container) return;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 6000);
    const resp = await fetch("https://api.sportsrc.org/?data=matches&category=football", {
      signal: controller.signal,
      headers: { Accept: "application/json" }
    });
    clearTimeout(timeoutId);

    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const body = await resp.json();
    const matches = Array.isArray(body.data) ? body.data : [];

    const now = new Date();
    const nowTs = Math.floor(now.getTime() / 1000);
    const todayStr = now.toISOString().slice(0, 10).replace(/-/g, "");

    const validMatches = [];
    for (const m of matches) {
      const home = m?.teams?.home;
      const away = m?.teams?.away;
      const homeBadge = home?.badge;
      const awayBadge = away?.badge;
      if (!homeBadge || !awayBadge) continue;

      const mt = Math.floor((m.date || 0) / 1000);
      const matchDateStr = new Date(mt * 1000).toISOString().slice(0, 10).replace(/-/g, "");
      if (matchDateStr !== todayStr) continue;

      let status = "upcoming";
      if (nowTs >= mt && nowTs <= mt + 7200) {
        status = "live";
      } else if (nowTs > mt + 7200) {
        status = "finished";
      }

      validMatches.push({
        homeName: home.name || "Home",
        awayName: away.name || "Away",
        homeBadge,
        awayBadge,
        status,
        league: m.league?.name || "Football",
        timeStr: new Date(mt * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      });
    }

    if (validMatches.length === 0) {
      container.innerHTML = getFallbackPromo();
      return;
    }

    const displayed = validMatches.slice(0, 7);
    const badges = ["FOOTBALL LIVE", "MATCH DAY", "KICK OFF", "LIVE STREAMS"];
    const dayBadge = badges[Math.floor(Date.now() / 86400000) % badges.length];

    const cardsHtml = displayed.map((m, index) => {
      let statusLabel = "UPCOMING";
      let statusColor = "#22c55e";
      let statusBg = "rgba(34,197,94,0.08)";
      let dot = '<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#22c55e"></span>';

      if (m.status === "live") {
        statusLabel = "LIVE";
        statusColor = "#ef4444";
        statusBg = "rgba(239,68,68,0.12)";
        dot = '<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#ef4444;animation:pulse 1.5s infinite"></span>';
      } else if (m.status === "finished") {
        statusLabel = "FINISHED";
        statusColor = "#6b7280";
        statusBg = "rgba(107,114,128,0.08)";
        dot = "";
      }

      const isHero = index === 0 && m.status === "live";
      const logoSize = isHero ? "44px" : "32px";
      const padding = isHero ? "12px" : "8px 10px";
      const fontSize = isHero ? "0.85rem" : "0.75rem";

      return `
        <a href="#download" style="display:flex;align-items:center;gap:8px;padding:${padding};background:${statusBg};border-radius:10px;border-left:3px solid ${statusColor};text-decoration:none;color:inherit;transition:all 0.2s">
          <div style="display:flex;align-items:center;gap:6px;flex-shrink:0">
            <img src="${escapeHtml(m.homeBadge)}" alt="${escapeHtml(m.homeName)}" style="height:${logoSize};width:auto" loading="lazy" onerror="this.style.display='none'">
            <span style="font-weight:700;color:var(--c-text-muted);font-size:0.75rem">VS</span>
            <img src="${escapeHtml(m.awayBadge)}" alt="${escapeHtml(m.awayName)}" style="height:${logoSize};width:auto" loading="lazy" onerror="this.style.display='none'">
          </div>
          <div style="flex:1;min-width:0">
            <div style="display:flex;align-items:center;gap:5px">
              ${dot}
              <span style="font-size:0.6rem;font-weight:700;color:${statusColor};letter-spacing:0.04em">${statusLabel}</span>
              <span style="font-size:0.55rem;color:var(--c-text-muted)">| ${escapeHtml(m.timeStr)}</span>
            </div>
            <div style="font-weight:600;font-size:${fontSize};color:var(--c-text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escapeHtml(m.homeName)} vs ${escapeHtml(m.awayName)}</div>
          </div>
        </a>
      `;
    }).join("");

    container.innerHTML = `
      <div class="promo-card">
        <div class="promo-badge">${dayBadge}</div>
        <div style="display:flex;flex-direction:column;gap:6px;margin-top:4px">
          ${cardsHtml}
        </div>
        <a href="#download" class="promo-btn" style="margin-top:12px;display:flex;align-items:center;justify-content:center;gap:8px;width:100%;padding:10px;border-radius:10px;background:var(--c-primary);color:#ffffff;font-weight:700;font-size:0.8rem;text-decoration:none">
          <i class="fa-solid fa-play"></i> Watch Live Matches on TV & Phone
        </a>
      </div>
    `;
  } catch (err) {
    console.log("[Client] Live matches fallback active:", err.message);
    container.innerHTML = getFallbackPromo();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  loadLiveMatches();
});
