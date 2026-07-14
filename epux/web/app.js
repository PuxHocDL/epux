
// --- AUTH LOGIC ---
const originalFetch = window.fetch;
window.fetch = async function() {
    let [resource, config] = arguments;
    if (!config) config = {};
    if (!config.headers) config.headers = {};
    
    const token = localStorage.getItem('epux_token');
    if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
    }
    
    try {
        const response = await originalFetch(resource, config);
        if (response.status === 401 && !resource.includes('/api/auth/')) {
            showAuthScreen();
        }
        return response;
    } catch (e) {
        throw e;
    }
};

function showAuthScreen() {
    document.getElementById('auth-screen').style.display = 'flex';
    document.getElementById('user-info').style.display = 'none';
}

function hideAuthScreen(username) {
    document.getElementById('auth-screen').style.display = 'none';
    document.getElementById('user-info').style.display = 'block';
    document.getElementById('username-display').textContent = username;
}

document.getElementById('logout-btn').addEventListener('click', () => {
    localStorage.removeItem('epux_token');
    showAuthScreen();
});

async function handleAuth(action) {
    const user = document.getElementById('auth-username').value;
    const pass = document.getElementById('auth-password').value;
    const errEl = document.getElementById('auth-error');
    errEl.textContent = '';
    
    if (!user || pass.length < 4) {
        errEl.textContent = 'Nhập đủ tên và mật khẩu (>=4 ký tự)';
        return;
    }
    
    try {
        const res = await originalFetch(`/api/auth/${action}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: user, password: pass})
        });
        const data = await res.json();
        if (!res.ok) {
            errEl.textContent = data.detail || 'Lỗi đăng nhập/đăng ký';
        } else {
            localStorage.setItem('epux_token', data.access_token);
            hideAuthScreen(data.username);
            init(); // Re-init dashboard
        }
    } catch (e) {
        errEl.textContent = 'Không kết nối được server';
    }
}

document.getElementById('auth-login-btn').addEventListener('click', () => handleAuth('login'));
document.getElementById('auth-register-btn').addEventListener('click', () => handleAuth('register'));

// Check auth on load
originalFetch('/api/auth/me', {
    headers: { 'Authorization': `Bearer ${localStorage.getItem('epux_token')}` }
}).then(res => {
    if (res.ok) {
        res.json().then(data => {
            hideAuthScreen(data.username);
            // init() is called at the bottom of app.js normally
        });
    } else {
        showAuthScreen();
    }
}).catch(() => showAuthScreen());

// --- END AUTH LOGIC ---

/* EPux frontend — vanilla JS SPA */
"use strict";

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const main = $("#main");

// icon từ sprite trong index.html — một bộ nét vẽ thống nhất
const ic = (name) => `<svg class="ic" aria-hidden="true"><use href="#ic-${name}"/></svg>`;

const RARITY_ORDER = ["SSS", "SS", "S", "A", "B", "C", "D"];
const PACK_NAMES = { bronze: "Pack Đồng", silver: "Pack Bạc", gold: "Pack Vàng" };
const RATE_LABELS = [
  { label: "Quên", cls: "r0" },
  { label: "Khó", cls: "r1" },
  { label: "Ổn", cls: "r2" },
  { label: "Dễ", cls: "r3" },
];

/* ---------------- helpers ---------------- */

async function api(path, opts = {}) {
  const init = { headers: { "Content-Type": "application/json" }, ...opts };
  if (init.body && typeof init.body !== "string") init.body = JSON.stringify(init.body);
  let res;
  try {
    res = await fetch(path, init);
  } catch {
    throw new Error("Mất kết nối tới server EPux — kiểm tra lệnh `epux` còn chạy trong terminal không, rồi tải lại trang (F5).");
  }
  let data = {};
  try { data = await res.json(); } catch { /* empty */ }
  if (!res.ok) throw new Error(data.detail || `Lỗi ${res.status}`);
  return data;
}

function toast(msg, type = "") {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = msg;
  $("#toasts").appendChild(el);
  setTimeout(() => el.remove(), 4500);
  if (type === "err") SFX.play("err");
  else if (type === "ok") SFX.play("ok");
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

async function busy(btn, fn) {
  if (btn.disabled) return;
  btn.disabled = true;
  btn.classList.add("busy");
  try {
    await fn();
  } catch (err) {
    toast(err.message, "err");
  } finally {
    btn.disabled = false;
    btn.classList.remove("busy");
  }
}

function modal(html) {
  const root = $("#modal-root");
  root.innerHTML = `<div class="modal-back"><div class="modal">${html}</div></div>`;
  $(".modal-back", root).addEventListener("click", (e) => {
    if (e.target.classList.contains("modal-back")) closeModal();
  });
  return $(".modal", root);
}
function closeModal() { $("#modal-root").innerHTML = ""; }

function fmtDay(iso) {
  const [, m, d] = iso.split("-");
  return `${d}/${m}`;
}

function dueLabel(dueAt) {
  const diff = new Date(dueAt) - Date.now();
  if (diff <= 0) return "đến hạn";
  const mins = diff / 60000;
  if (mins < 60) return `${Math.round(mins)} phút nữa`;
  if (mins < 1440) return `${Math.round(mins / 60)} giờ nữa`;
  return `${Math.round(mins / 1440)} ngày nữa`;
}

/* ---------- gacha: chòm sao + thần hộ mệnh Hy Lạp ---------- */

// Mỗi bậc rarity là một "cấp bậc thần thoại": [tên, biểu tượng, danh xưng tiếng Việt]
const PATRONS = {
  D: [["Satyr", "🐐", "Tinh linh đồng nội"], ["Nymph", "🌿", "Tiên nữ suối nguồn"], ["Siren", "🧜‍♀️", "Người cá mê hoặc"], ["Centaur", "🐎", "Nhân mã thảo nguyên"], ["Harpy", "🪶", "Điểu nữ cuồng phong"]],
  C: [["Perseus", "🗡️", "Anh hùng diệt Medusa"], ["Heracles", "💪", "Lực sĩ 12 kỳ công"], ["Achilles", "🛡️", "Chiến binh gót ngọc"], ["Odysseus", "⛵", "Lãng khách mưu trí"], ["Theseus", "🐂", "Kẻ hạ Minotaur"], ["Atalanta", "🏃‍♀️", "Nữ thợ săn thần tốc"]],
  B: [["Nike", "🕊️", "Nữ thần chiến thắng"], ["Iris", "🌈", "Sứ giả cầu vồng"], ["Pan", "🎶", "Thần đồng nội"], ["Eros", "💘", "Thần tình ái"], ["Helios", "☀️", "Thần mặt trời"], ["Selene", "🌙", "Nữ thần mặt trăng"]],
  A: [["Athena", "🦉", "Nữ thần trí tuệ"], ["Apollo", "🎻", "Thần ánh sáng & thi ca"], ["Artemis", "🏹", "Nữ thần săn bắn"], ["Hermes", "🪽", "Sứ giả thần tốc"], ["Hephaestus", "🔨", "Thần rèn lửa thiêng"], ["Dionysus", "🍇", "Thần rượu nho"], ["Ares", "⚔️", "Thần chiến tranh"], ["Aphrodite", "🌹", "Nữ thần sắc đẹp"]],
  S: [["Zeus", "⚡", "Vua các vị thần"], ["Poseidon", "🔱", "Chúa tể đại dương"], ["Hades", "💀", "Vua âm phủ"], ["Hera", "👑", "Nữ hoàng Olympus"], ["Demeter", "🌾", "Nữ thần mùa màng"]],
  SS: [["Cronus", "⏳", "Titan thời gian"], ["Atlas", "🌍", "Titan vác bầu trời"], ["Prometheus", "🔥", "Kẻ trộm lửa thiêng"], ["Hyperion", "🌅", "Titan ánh sáng"], ["Rhea", "🦁", "Mẹ các vị thần"]],
  SSS: [["Chaos", "🌌", "Khởi nguyên vạn vật"], ["Nyx", "🌑", "Nữ thần bóng đêm"], ["Gaia", "🌏", "Mẹ đất vĩnh hằng"], ["Uranus", "🌠", "Bầu trời nguyên thủy"], ["Aether", "✨", "Ánh sáng thượng giới"]],
};

const MAX_STARS = 5;

function hashCode(str) {
  let h = 0;
  for (const ch of String(str)) h = (h * 31 + ch.codePointAt(0)) | 0;
  return Math.abs(h);
}

function mulberry32(seed) {
  return function () {
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function patronFor(w) {
  const pool = PATRONS[w.rarity] || PATRONS.C;
  return pool[hashCode(w.term) % pool.length];
}

// Chòm sao riêng cho từng từ — sinh từ hash nên mỗi từ một hình, không đổi giữa các lần xem.
function constellationSVG(term) {
  const rnd = mulberry32(hashCode(term));
  const n = 6 + Math.floor(rnd() * 4);
  const pts = [];
  for (let i = 0; i < n; i++) pts.push([8 + rnd() * 84, 12 + rnd() * 50]);
  let lines = "";
  for (let i = 1; i < n; i++) {
    lines += `<line x1="${pts[i - 1][0].toFixed(1)}" y1="${pts[i - 1][1].toFixed(1)}" x2="${pts[i][0].toFixed(1)}" y2="${pts[i][1].toFixed(1)}"/>`;
  }
  const a = Math.floor(rnd() * (n - 2));
  const b = n - 1 - Math.floor(rnd() * 2);
  if (a !== b) lines += `<line x1="${pts[a][0].toFixed(1)}" y1="${pts[a][1].toFixed(1)}" x2="${pts[b][0].toFixed(1)}" y2="${pts[b][1].toFixed(1)}"/>`;
  const alpha = Math.floor(rnd() * n);
  let stars = "";
  pts.forEach((p, i) => {
    const r = i === alpha ? 2.3 : 0.9 + rnd() * 1.1;
    stars += `<circle cx="${p[0].toFixed(1)}" cy="${p[1].toFixed(1)}" r="${(r * 2.6).toFixed(1)}" class="halo"/>`;
    stars += `<circle cx="${p[0].toFixed(1)}" cy="${p[1].toFixed(1)}" r="${r.toFixed(1)}" class="star"/>`;
  });
  return `<svg class="const" viewBox="0 0 100 70" preserveAspectRatio="xMidYMid meet" aria-hidden="true">${lines}${stars}</svg>`;
}

function starsHTML(w) {
  if (!w.owned) return "";
  const filled = "★".repeat(Math.min(w.stars, MAX_STARS));
  const empty = "★".repeat(Math.max(0, MAX_STARS - w.stars));
  const dupes = w.dupes ? `<span class="dupes">×${w.dupes}</span>` : "";
  return `<div class="tcg-stars">${filled}<span class="dim">${empty}</span>${dupes}</div>`;
}

function powerOf(w) {
  const base = { D: 20, C: 40, B: 80, A: 150, S: 280, SS: 480, SSS: 800 }[w.rarity] || 40;
  return Math.round(base * (1 + 0.25 * Math.max(0, w.stars - 1)));
}

function cardHTML(w, actions = "", opts = {}) {
  if (opts.locked) {
    return `
    <div class="tcg locked rarity-${w.rarity}" data-id="${w.id}">
      <div class="tcg-frame">
        <div class="tcg-top"><span class="tcg-rarity">◆ ${w.rarity}</span><span class="tcg-lock">${ic("lock")}</span></div>
        <div class="tcg-art">${constellationSVG(w.term)}<span class="tcg-patron-name">? ? ?</span></div>
        <div class="tcg-name">???</div>
        <div class="tcg-ipa">Mở pack để thu phục</div>
      </div>
    </div>`;
  }
  const p = patronFor(w);
  const colls = (w.collocations || []).slice(0, 2).map((c) => `<span class="chip">${esc(c)}</span>`).join("");
  return `
    <div class="tcg rarity-${w.rarity} ${w.stars >= MAX_STARS ? "ascended" : ""}" data-id="${w.id}">
      <div class="tcg-frame">
        <div class="tcg-top">
          <span class="tcg-rarity">◆ ${w.rarity}</span>
          ${w.is_gem ? `<span class="tcg-gemicon" title="Từ đắt giá">${ic("gem")}</span>` : ""}
          ${w.is_toeic ? `<span class="tcg-gemicon" title="Từ vựng TOEIC${w.toeic_part ? ` (${w.toeic_part})` : ''}" style="color:var(--accent);">T</span>` : ""}
        </div>
        <div class="tcg-art">
          ${constellationSVG(w.term)}
          <span class="tcg-patron-name" title="${esc(p[0])} — ${esc(p[2])}">${esc(p[0])}</span>
        </div>
        <div class="tcg-name">${esc(w.term)}</div>
        <div class="tcg-ipa">${esc(w.ipa)}${w.pos ? ` · ${esc(w.pos)}` : ""}</div>
        ${starsHTML(w)}
        ${w.meaning ? `<div class="tcg-meaning">${esc(w.meaning)}</div>` : ""}
        <div class="tcg-meta">
          ${w.topic ? `<span class="chip">${esc(w.topic)}</span>` : ""}
          ${colls}
          ${actions}
        </div>
      </div>
    </div>`;
}

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

async function refreshDueBadge() {
  try {
    const data = await api("/api/review/next");
    const badge = $("#due-badge");
    badge.hidden = !data.remaining;
    badge.textContent = data.remaining;
  } catch { /* server may be booting */ }
}

/* ---------------- router ---------------- */

const views = {};
let currentView = "dashboard";

function show(name) {
  if (!views[name]) name = "dashboard";
  currentView = name;
  if (location.hash !== `#${name}`) history.replaceState(null, "", `#${name}`);
  $$(".nav-btn").forEach((b) => b.classList.toggle("active", b.dataset.view === name));
  main.classList.remove("anim");
  main.innerHTML = `<div class="empty">Đang tải…</div>`;
  views[name]()
    .then(() => {
      void main.offsetWidth; // restart CSS animation
      main.classList.add("anim");
      runCountUps(main);
    })
    .catch((err) => {
      main.innerHTML = `<div class="empty">${ic("alert")} ${esc(err.message)}</div>`;
    });
}

$$(".nav-btn").forEach((b) => b.addEventListener("click", () => show(b.dataset.view)));

/* ---------------- dashboard ---------------- */

views.dashboard = async () => {
  const d = await api("/api/dashboard");
  const lv = d.level;
  const xpPct = Math.min(100, Math.round(((lv.xp - lv.current_floor) / (lv.next_level_xp - lv.current_floor)) * 100));
  const llmWarn = d.llm.configured ? "" : `
    <div class="card mb" style="border-color: var(--warn);">
      ${ic("alert")} <b>Chưa cấu hình LLM.</b> Thêm <code>AZURE_OPENAI_API_KEY</code>, <code>AZURE_OPENAI_ENDPOINT</code> vào file <code>.env</code> rồi khởi động lại — các tính năng AI đang tắt.
    </div>`;

  const challenges = d.challenges.map((c) => challengeHTML(c)).join("");
  const packs = d.packs.length
    ? d.packs.map((p) => packHTML(p)).join("")
    : `<div class="empty" style="padding: 12px;">Hoàn thành thử thách để nhận pack</div>`;

  const dailyCTA = d.need_daily_words && d.llm.configured ? `
    <div class="card mt" style="border-color: var(--accent);">
      <b>${ic("download")} Nạp từ mới hôm nay</b>
      <div style="color: var(--muted); font-size: 0.85rem; margin: 6px 0 12px;">
        Hôm nay bạn mới thêm ${d.today.new_words}/${d.daily_new_words} từ. Để AI chọn chủ đề IELTS và sinh từ cho bạn?
      </div>
      <button class="btn primary" id="daily-gen">${ic("sparkle")} Sinh ${d.daily_new_words - d.today.new_words} từ mới ngay</button>
    </div>` : "";

  main.innerHTML = `
    <div class="page-title">Hôm nay</div>
    <div class="page-sub">Học đều mỗi ngày — đường cong lãng quên không chờ ai cả.</div>
    ${llmWarn}
    <div class="tiles mb">
      <div class="tile"><div class="t-label">${ic("hourglass")} Đến hạn ôn</div><div class="t-value"><span data-countup="${d.stats.due}">0</span></div>
        <div class="t-sub">${d.today.reviews} lượt ôn hôm nay</div></div>
      <div class="tile"><div class="t-label">${ic("flame")} Streak</div><div class="t-value"><span data-countup="${d.stats.streak}">0</span> <small>ngày</small></div></div>
      <div class="tile"><div class="t-label">${ic("star")} Level ${lv.level}</div>
        <div class="t-value"><span data-countup="${lv.xp}">0</span> <small>XP</small></div>
        <div class="xpbar"><div style="width:${xpPct}%"></div></div></div>
      <div class="tile"><div class="t-label">${ic("cards")} Bộ sưu tập</div>
        <div class="t-value"><span data-countup="${d.stats.owned_cards}">0</span><small>/${d.stats.total_words}</small></div>
        <div class="t-sub">thẻ đã sở hữu</div></div>
    </div>
    <div class="row">
      <div class="card grow" style="min-width: 340px;">
        <b>${ic("target")} Thử thách hôm nay</b>
        ${challenges}
      </div>
      <div style="flex: 0 0 280px; display: flex; flex-direction: column; gap: 14px;">
        <div class="card">
          <b>${ic("gift")} Pack chưa mở</b>
          <div class="pack-shelf mt">${packs}</div>
        </div>
        <div class="card">
          <b>${ic("bolt")} Học nhanh</b>
          <div class="row mt">
            <button class="btn grow" onclick="show('review')">${ic("hourglass")} Ôn ngay</button>
            <button class="btn grow" onclick="show('quiz')">${ic("bolt")} Quiz</button>
            <button class="btn grow" onclick="show('writing')">${ic("quill")} Viết</button>
          </div>
        </div>
      </div>
    </div>
    ${dailyCTA}
  `;
  bindChallengeClaims();
  bindPackOpens();
  const dg = $("#daily-gen");
  if (dg) dg.addEventListener("click", () => busy(dg, async () => {
    const res = await api("/api/words/generate", { method: "POST", body: { count: d.daily_new_words - d.today.new_words } });
    toast(`Đã thêm ${res.words.length} từ mới (chủ đề: ${res.topic})`, "ok");
    show("dashboard");
  }));
};

function challengeHTML(c) {
  const pct = Math.min(100, Math.round((c.progress / c.target) * 100));
  let action;
  if (c.claimed) action = `<span class="done-mark">✓ Đã nhận</span>`;
  else if (c.done) action = `<button class="btn primary c-claim-btn" data-code="${c.code}">Nhận pack</button>`;
  else action = `<span class="tier-tag tier-${c.tier}">${PACK_NAMES[c.tier]}</span>`;
  return `
    <div class="challenge">
      <div class="c-info">
        <div class="c-title">${esc(c.title)}</div>
        <div class="c-desc">${esc(c.desc)}</div>
      </div>
      <div class="c-progress">
        <div class="pbar ${c.done ? "full" : ""}"><div style="width:${pct}%"></div></div>
        <div class="c-count">${c.progress}/${c.target}</div>
      </div>
      <div class="c-claim">${action}</div>
    </div>`;
}

function packHTML(p) {
  return `
    <button class="pack ${p.tier} pack-open-btn" data-id="${p.id}" data-tier="${p.tier}">
      <div class="p-icon">${ic("gift")}</div>
      <div class="p-name">${PACK_NAMES[p.tier] || p.tier}</div>
      <span class="btn primary" style="padding: 3px 12px; font-size: 0.75rem;">Mở</span>
    </button>`;
}

function bindChallengeClaims() {
  $$(".c-claim-btn").forEach((btn) => btn.addEventListener("click", () => busy(btn, async () => {
    const res = await api(`/api/challenges/${btn.dataset.code}/claim`, { method: "POST" });
    SFX.play("claim");
    toast(`Nhận được ${res.tier_vi}!`, "ok");
    show(currentView);
  })));
}

function bindPackOpens() {
  $$(".pack-open-btn").forEach((btn) =>
    btn.addEventListener("click", () => openPackFlow(btn.dataset.id, btn.dataset.tier || "bronze")));
}

const TIER_STARS = { bronze: "✦", silver: "✦ ✦", gold: "✦ ✦ ✦" };

function openPackFlow(packId, tier) {
  modal(`
    <div class="pack-stage">
      <div class="pack-visual ${tier}" id="pv">
        <div class="pv-sigil">EP</div>
        <div class="pv-stars">${TIER_STARS[tier] || "✦"}</div>
        <div class="pv-name">${PACK_NAMES[tier] || tier}</div>
      </div>
      <button class="btn primary" id="pv-open">${ic("sparkle")} Mở pack</button>
    </div>`);
  $("#pv-open").addEventListener("click", async (e) => {
    const b = e.currentTarget;
    if (b.disabled) return;
    b.disabled = true;
    SFX.play("shake");
    $("#pv").classList.add("opening");
    try {
      // gọi API song song với màn rung pack cho đủ độ hồi hộp
      const [res] = await Promise.all([
        api(`/api/packs/${packId}/open`, { method: "POST" }),
        wait(1000),
      ]);
      SFX.play("burst");
      const flash = document.createElement("div");
      flash.className = "flash-overlay";
      document.body.appendChild(flash);
      setTimeout(() => flash.remove(), 600);
      showReveal(res);
    } catch (err) {
      toast(err.message, "err");
      closeModal();
    }
  });
}

function showReveal(res) {
  let note = "";
  if (res.duplicate) {
    note = `<div class="rv-note">${ic("refresh")} Thẻ trùng! Bản sao: ×${res.card.dupes} — bấm vào thẻ trong Bộ sưu tập để GỘP nâng ★</div>`;
  } else if (res.generated) {
    note = `<div class="rv-note">${ic("sparkle")} Từ mới toanh — AI vừa rèn riêng cho bạn, đã vào lịch học!</div>`;
  }
  const m = modal(`
    <div class="reveal-stage rarity-${res.rarity}">
      <div class="rv-rays"></div>
      <div class="rv-rarity-banner">${res.duplicate ? "TRÙNG ×" + res.card.dupes : res.rarity}</div>
      ${cardHTML(res.card)}
      ${note}
      <div class="rv-actions">
        <button class="btn primary" onclick="closeModal(); show(currentView);">Tuyệt!</button>
      </div>
    </div>`);
  spawnSparks($(".reveal-stage", m), res.rarity);
  SFX.reveal(res.rarity, res.duplicate);
  setTimeout(() => TTS.speak(res.card.term), 800); // đọc từ sau fanfare
}

/* ---------------- chi tiết thẻ ---------------- */

async function openCardDetail(id) {
  let data;
  try {
    data = await api(`/api/words/${id}`);
  } catch (err) {
    toast(err.message, "err");
    return;
  }
  const w = data.word;
  const p = patronFor(w);
  const cost = w.stars;
  const canUpgrade = w.owned && w.stars < MAX_STARS && w.dupes >= cost;
  const colls = (w.collocations || []).map((c) => `<span class="chip">${esc(c)}</span>`).join(" ");
  modal(`
    <div class="detail rarity-${w.rarity}">
      <div class="detail-grid">
        <div class="detail-card">${cardHTML(w)}</div>
        <div class="detail-info">
          <div class="d-patron"><b>${esc(p[0])}</b> · ${esc(p[2])}</div>
          <div class="d-block">
            <button class="btn speak-btn" data-say="${esc(w.term)}">${ic("speaker")} Nghe từ</button>
            ${w.example ? ` <button class="btn ghost speak-btn" data-say="${esc(w.example)}" data-rate="0.95">${ic("speaker")} Nghe ví dụ</button>` : ""}
          </div>
          ${w.owned ? `<div class="d-power">${ic("bolt")} Sức mạnh: <b>${powerOf(w)}</b>${w.stars >= MAX_STARS ? ` <span class="asc">THĂNG HOA</span>` : ""}</div>` : ""}
          ${w.example ? `
          <div class="d-block"><div class="d-label">Ví dụ</div>
            <div class="d-example">"${esc(w.example)}"</div>
            ${w.example_vi ? `<div class="d-sub">${esc(w.example_vi)}</div>` : ""}
          </div>` : ""}
          ${colls ? `<div class="d-block"><div class="d-label">Collocations</div>${colls}</div>` : ""}
          ${w.notes ? `<div class="d-block"><div class="d-label">Cách dùng</div><div class="d-sub">${esc(w.notes)}</div></div>` : ""}
          <div class="d-block"><div class="d-label">Trí nhớ · đường cong lãng quên</div>
            <div class="pbar"><div style="width:${data.srs.retention_now}%"></div></div>
            <div class="d-sub">còn nhớ ~${data.srs.retention_now}% · ôn lại: ${dueLabel(w.due_at)} · đã ôn ${w.repetitions} lần${w.lapses ? ` · quên ${w.lapses} lần` : ""}</div>
          </div>
          ${w.owned ? `
          <div class="d-block"><div class="d-label">Nâng sao</div>
            <div class="d-stars">${starsHTML(w) || ""}</div>
            ${w.stars < MAX_STARS
              ? `<button class="btn primary mt" id="d-upgrade" ${canUpgrade ? "" : "disabled"}>${ic("star")} Gộp ${cost} bản sao → ${w.stars + 1}★</button>
                 ${canUpgrade ? "" : `<div class="d-sub" style="margin-top:6px;">cần ${cost} bản sao, đang có ×${w.dupes} — mở pack để săn thêm</div>`}`
              : `<div class="d-sub">Thẻ đã THĂNG HOA — cấp sao tối đa ✨</div>`}
          </div>` : `<div class="d-block d-sub">${ic("lock")} Chưa sở hữu thẻ này — hoàn thành thử thách để nhận pack.</div>`}
        </div>
      </div>
      <div style="text-align: right; margin-top: 14px;">
        <button class="btn" onclick="closeModal()">Đóng</button>
      </div>
    </div>`);
  $("#d-upgrade")?.addEventListener("click", (e) => busy(e.currentTarget, async () => {
    const res = await api(`/api/cards/${w.id}/upgrade`, { method: "POST" });
    SFX.play("upgrade");
    spawnSparks($(".detail", $("#modal-root")), w.rarity);
    toast(`"${res.word.term}" lên ${res.word.stars}★!`, "ok");
    await wait(650);
    openCardDetail(w.id);
  }));
}

// Nút loa: đọc text trong data-say bằng Web Speech API
document.addEventListener("click", (e) => {
  const sp = e.target.closest(".speak-btn");
  if (!sp) return;
  const ok = TTS.speak(sp.dataset.say, sp.dataset.rate ? Number(sp.dataset.rate) : undefined);
  if (!ok) toast("Trình duyệt không hỗ trợ đọc từ (Web Speech API).", "err");
});

// Blip nhẹ cho mọi nút bấm thường (nút có âm riêng như rate/quiz không nằm trong selector này)
document.addEventListener("click", (e) => {
  if (e.target.closest(".speak-btn")) return; // loa có tiếng đọc rồi, khỏi blip
  if (e.target.closest(".btn, .nav-btn, .subtab, .chip.clickable")) SFX.play("click");
});

// Click thẻ ở bất kỳ đâu (trừ màn reveal) -> mở chi tiết; thẻ khoá -> nhắc mở pack
document.addEventListener("click", (e) => {
  const termEl = e.target.closest(".w-term[data-id]");
  if (termEl) {
    openCardDetail(Number(termEl.dataset.id));
    return;
  }
  const tcg = e.target.closest(".tcg[data-id]");
  if (!tcg || tcg.closest(".reveal-stage") || tcg.closest(".detail") || tcg.closest(".arena-picker")) return;
  if (tcg.classList.contains("locked")) {
    toast("🔒 Thẻ chưa sở hữu — hoàn thành thử thách hằng ngày để nhận pack!");
    return;
  }
  openCardDetail(Number(tcg.dataset.id));
});

function spawnSparks(container, rarity) {
  const colors = rarity === "SSS"
    ? ["#ff5ca8", "#ffb054", "#7cf8b0", "#54c8ff", "#b06cff"]
    : [getComputedStyle(container).getPropertyValue("--rc").trim() || "#d9b45c", "#ffffff"];
  const count = rarity === "SSS" ? 34 : ["SS", "S"].includes(rarity) ? 26 : 16;
  for (let i = 0; i < count; i++) {
    const s = document.createElement("span");
    s.className = "spark";
    const angle = Math.random() * Math.PI * 2;
    const dist = 90 + Math.random() * 190;
    s.style.setProperty("--x", `${Math.cos(angle) * dist}px`);
    s.style.setProperty("--y", `${Math.sin(angle) * dist}px`);
    s.style.setProperty("--d", `${0.7 + Math.random() * 0.9}s`);
    s.style.setProperty("--s", `${3 + Math.random() * 6}px`);
    s.style.setProperty("--c", colors[i % colors.length]);
    s.style.animationDelay = `${Math.random() * 0.25}s`;
    container.appendChild(s);
  }
}

/* ---------------- review ---------------- */

views.review = async () => {
  const data = await api("/api/review/next");
  if (!data.word) {
    main.innerHTML = `
      <div class="page-title">Ôn tập</div>
      <div class="empty">${ic("check-circle")} Không còn thẻ nào đến hạn!<br><br>
        <button class="btn" onclick="show('quiz')">${ic("bolt")} Làm quiz cho nóng</button>
        <button class="btn" onclick="show('words')">${ic("download")} Thêm từ mới</button>
      </div>`;
    refreshDueBadge();
    return;
  }
  const w = data.word;
  main.innerHTML = `
    <div class="page-title">Ôn tập <span style="font-size: 0.9rem; color: var(--muted);">còn ${data.remaining} thẻ</span></div>
    <div class="page-sub">Nhớ lại nghĩa trước khi lật thẻ — đó mới là lúc não ghi nhớ.</div>
    <div class="flash-wrap">
      <div class="flip-scene" id="flash">
        <div class="flip-inner" id="flip-inner">
          <div class="flip-face front">
            <div class="flashcard rarity-${w.rarity}">
              <div><span class="rbadge">${w.rarity}</span> ${w.topic ? `<span class="chip">${esc(w.topic)}</span>` : ""}</div>
              <div class="f-term">${esc(w.term)} <button class="speak-btn f-speak" data-say="${esc(w.term)}" title="Nghe phát âm (P)">${ic("speaker")}</button></div>
              <div class="f-ipa">${esc(w.ipa)} ${w.pos ? "· " + esc(w.pos) : ""}</div>
              <div class="f-hint">✦ SPACE lật thẻ · P nghe phát âm ✦</div>
            </div>
          </div>
          <div class="flip-face back">
            <div class="flashcard rarity-${w.rarity}">
              <div class="f-term" style="font-size: 1.4rem;">${esc(w.term)} <button class="speak-btn f-speak" data-say="${esc(w.term)}" title="Nghe phát âm (P)">${ic("speaker")}</button></div>
              <div class="f-meaning">${esc(w.meaning)}</div>
              ${w.example ? `<div class="f-example">"${esc(w.example)}" <button class="speak-btn" data-say="${esc(w.example)}" data-rate="0.95" title="Nghe câu ví dụ">${ic("speaker")}</button></div>` : ""}
              ${w.example_vi ? `<div class="f-example-vi">${esc(w.example_vi)}</div>` : ""}
              ${(w.collocations || []).length ? `<div class="f-colls">${w.collocations.map((c) => `<span class="chip">${esc(c)}</span>`).join("")}</div>` : ""}
              ${w.notes ? `<div class="f-note">${ic("bulb")} ${esc(w.notes)}</div>` : ""}
            </div>
          </div>
        </div>
      </div>
      <div class="rate-row anim" id="rates" hidden>
        ${RATE_LABELS.map((r, i) => `
          <button class="rate-btn ${r.cls}" data-rating="${i}">
            <span class="r-label">${r.label}</span>
            <span class="r-int">${esc(data.intervals[i])}</span>
          </button>`).join("")}
      </div>
    </div>`;

  const reveal = () => {
    SFX.play("flip");
    $("#flip-inner").classList.add("flipped");
    $("#rates").hidden = false;
    TTS.speak(w.term); // tự đọc từ khi lật — luyện tai luôn
  };
  $("#flash").addEventListener("click", (e) => {
    if (e.target.closest(".speak-btn")) return; // bấm loa thì không lật thẻ
    if ($("#rates").hidden) reveal();
  });
  $$(".rate-btn").forEach((btn) => btn.addEventListener("click", () => busy(btn, async () => {
    SFX.play(`rate${btn.dataset.rating}`);
    await api(`/api/review/${w.id}`, { method: "POST", body: { rating: Number(btn.dataset.rating) } });
    refreshDueBadge();
    views.review();
  })));

  document.onkeydown = (e) => {
    if (currentView !== "review") { document.onkeydown = null; return; }
    if (e.code === "Space" && $("#rates")?.hidden) { e.preventDefault(); reveal(); }
    if (e.code === "KeyP") TTS.speak(w.term);
    if (["1", "2", "3", "4"].includes(e.key) && !$("#rates")?.hidden) {
      $$(".rate-btn")[Number(e.key) - 1]?.click();
    }
  };
};

/* ---------------- quiz ---------------- */

let quizScore = { ok: 0, total: 0 };

views.quiz = async () => {
  let q;
  try {
    q = await api("/api/quiz/question");
  } catch (err) {
    main.innerHTML = `<div class="page-title">Quiz</div><div class="empty">${esc(err.message)}<br><br>
      <button class="btn" onclick="show('words')">${ic("download")} Thêm từ trước đã</button></div>`;
    return;
  }
  const label = q.mode === "term_to_meaning" ? "Nghĩa của từ này là gì?" : "Từ nào khớp với nghĩa này?";
  main.innerHTML = `
    <div class="page-title">Quiz <span style="font-size: 0.9rem; color: var(--muted);">phiên này: ${quizScore.ok}/${quizScore.total}</span></div>
    <div class="page-sub">Trả lời đúng → thẻ được tính là nhớ; sai → quay lại ôn sớm.</div>
    <div class="quiz-wrap">
      <div class="card">
        <div style="color: var(--muted); font-size: 0.8rem;">${label}</div>
        <div style="font-size: 1.3rem; font-weight: 700; margin-top: 8px;">${esc(q.prompt)} ${q.mode === "term_to_meaning" && q.ipa ? `<span class="v-ipa">${esc(q.ipa)}</span>` : ""} ${q.mode === "term_to_meaning" ? `<button class="speak-btn" data-say="${esc(q.prompt)}" title="Nghe phát âm">${ic("speaker")}</button>` : ""}</div>
        <div id="options">${q.options.map((o) => `<button class="q-option" data-v="${esc(o)}">${esc(o)}</button>`).join("")}</div>
        <div id="q-after" class="mt" hidden>
          ${q.example ? `<div style="color: var(--muted); font-style: italic; font-size: 0.88rem;">Ví dụ: ${esc(q.example)} <button class="speak-btn" data-say="${esc(q.example)}" data-rate="0.95" title="Nghe câu ví dụ">${ic("speaker")}</button></div>` : ""}
          <button class="btn ghost mt speak-btn" data-say="${esc(q.mode === "term_to_meaning" ? q.prompt : q.correct)}">${ic("speaker")} Nghe từ</button>
          <button class="btn primary mt" id="q-next">Câu tiếp →</button>
        </div>
      </div>
    </div>`;

  $$(".q-option").forEach((btn) => btn.addEventListener("click", async () => {
    if (btn.disabled) return;
    $$(".q-option").forEach((b) => (b.disabled = true));
    const selected = btn.dataset.v;
    try {
      const res = await api("/api/quiz/answer", {
        method: "POST",
        body: { word_id: q.word_id, prompt: q.prompt, selected, correct: q.correct },
      });
      quizScore.total += 1;
      if (res.is_correct) quizScore.ok += 1;
      SFX.play(res.is_correct ? "correct" : "wrong");
      $$(".q-option").forEach((b) => {
        if (b.dataset.v === q.correct) b.classList.add("correct");
        else if (b === btn) b.classList.add("wrong");
      });
      $("#q-after").hidden = false;
      refreshDueBadge();
    } catch (err) { toast(err.message, "err"); }
  }));
  $("#q-next")?.addEventListener("click", () => views.quiz());
};

/* ---------------- words ---------------- */

const wordsState = { query: "", topic: "", rarity: "" };

views.words = async () => {
  const [wordsData, topicsData] = await Promise.all([
    api(`/api/words?query=${encodeURIComponent(wordsState.query)}&topic=${encodeURIComponent(wordsState.topic)}&rarity=${encodeURIComponent(wordsState.rarity)}`),
    api("/api/topics"),
  ]);
  const topics = topicsData.topics;
  const topicOptions = topics.map((t) => `<option value="${esc(t.name)}" ${wordsState.topic === t.name ? "selected" : ""}>${esc(t.name)}${t.name_vi ? ` — ${esc(t.name_vi)}` : ""}</option>`).join("");

  main.innerHTML = `
    <div class="page-title">Từ vựng</div>
    <div class="page-sub">${wordsData.words.length} từ đang hiển thị. AI tự điền nghĩa, IPA, ví dụ, collocations và độ hiếm.</div>

    <div class="card mb">
      <b>${ic("sparkle")} Sinh từ mới bằng AI</b>
      <div class="row mt">
        <div class="grow" style="min-width: 150px;">
          <label class="field">Chủ đề (IELTS / TOEIC)</label>
          <select id="gen-topic">
            <option value="">— AI tự chọn chủ đề hay —</option>
            ${topicOptions}
          </select>
        </div>
        <div style="width: 100px;">
          <label class="field">Trình độ</label>
          <select id="gen-level">
            <option value="">Tự động</option>
            <option value="B1">B1</option>
            <option value="B2">B2</option>
            <option value="C1">C1</option>
            <option value="C2">C2</option>
          </select>
        </div>
        <div style="width: 100px;">
          <label class="field">Bài thi</label>
          <select id="gen-context">
            <option value="">Chung</option>
            <option value="IELTS">IELTS</option>
            <option value="TOEIC">TOEIC</option>
          </select>
        </div>
        <div style="width: 90px;">
          <label class="field">Số từ</label>
          <input type="number" id="gen-count" value="8" min="1" max="20">
        </div>
        <div style="align-self: flex-end;">
          <button class="btn primary" id="gen-btn">Sinh từ</button>
        </div>
        <div style="align-self: flex-end;">
          <button class="btn" id="topics-btn" title="AI đề xuất chủ đề IELTS mới">${ic("bulb")} Gợi ý chủ đề</button>
        </div>
      </div>
      <div id="topics-list" class="mt" style="display:flex; gap:8px; flex-wrap:wrap;">
        ${topics.slice(0, 10).map((t) => `
          <span class="chip clickable topic-chip" data-name="${esc(t.name)}" title="${esc(t.description_vi)}">
            ${esc(t.name)} <small style="color:var(--muted)">(${t.word_count})</small>
          </span>`).join("")}
      </div>
    </div>

    <div class="card mb">
      <b>${ic("plus")} Thêm thủ công</b>
      <div class="row mt">
        <input type="text" id="add-term" class="grow" placeholder="Gõ từ/cụm từ tiếng Anh… AI sẽ điền phần còn lại">
        <button class="btn primary" id="add-btn">Thêm (AI điền)</button>
      </div>
    </div>

    <div class="row mb">
      <input type="text" id="w-search" class="grow" placeholder="Tìm từ, nghĩa, chủ đề…" value="${esc(wordsState.query)}">
      <select id="w-rarity" style="width: 130px;">
        <option value="">Mọi rarity</option>
        ${RARITY_ORDER.map((r) => `<option ${wordsState.rarity === r ? "selected" : ""}>${r}</option>`).join("")}
      </select>
    </div>

    <div class="card" id="w-list">
      ${wordsData.words.length ? wordsData.words.map((w) => wordRowHTML(w)).join("") : `<div class="empty">Chưa có từ nào khớp. Sinh từ mới bằng AI ở trên nhé!</div>`}
    </div>`;

  const genBtn = $("#gen-btn");
  genBtn.addEventListener("click", () => busy(genBtn, async () => {
    const res = await api("/api/words/generate", {
      method: "POST",
      body: { 
        topic: $("#gen-topic").value, 
        count: Number($("#gen-count").value) || 8,
        level: $("#gen-level").value,
        context: $("#gen-context").value
      },
    });
    toast(`Đã thêm ${res.words.length} từ (${res.topic})`, "ok");
    views.words();
  }));

  const topicsBtn = $("#topics-btn");
  topicsBtn.addEventListener("click", () => busy(topicsBtn, async () => {
    await api("/api/topics/suggest", { method: "POST" });
    toast("Đã có thêm chủ đề IELTS mới", "ok");
    views.words();
  }));

  $$(".topic-chip").forEach((chip) => chip.addEventListener("click", () => {
    wordsState.topic = wordsState.topic === chip.dataset.name ? "" : chip.dataset.name;
    views.words();
  }));

  const addBtn = $("#add-btn");
  const doAdd = () => busy(addBtn, async () => {
    const term = $("#add-term").value.trim();
    if (!term) return;
    const res = await api("/api/words", { method: "POST", body: { term, ai_enrich: true } });
    toast(`Đã thêm "${res.word.term}" (${res.word.rarity})`, "ok");
    views.words();
  });
  addBtn.addEventListener("click", doAdd);
  $("#add-term").addEventListener("keydown", (e) => { if (e.key === "Enter") doAdd(); });

  let searchTimer;
  $("#w-search").addEventListener("input", (e) => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => { wordsState.query = e.target.value; views.words(); }, 350);
  });
  $("#w-rarity").addEventListener("change", (e) => { wordsState.rarity = e.target.value; views.words(); });

  $$(".w-del").forEach((btn) => btn.addEventListener("click", async () => {
    if (!confirm("Xoá từ này khỏi bộ học?")) return;
    try {
      await api(`/api/words/${btn.dataset.id}`, { method: "DELETE" });
      toast("Đã xoá.", "ok");
      views.words();
    } catch (err) { toast(err.message, "err"); }
  }));
};

function wordRowHTML(w) {
  return `
    <div class="word-row rarity-${w.rarity}">
      <span class="rbadge">${w.rarity}</span>
      <div class="w-main">
        <span class="w-term" data-id="${w.id}" title="Xem chi tiết thẻ">${esc(w.term)}</span><span class="w-ipa">${esc(w.ipa)}</span>
        ${w.owned ? ` <span class="w-flag" title="Đã sở hữu thẻ">${ic("cards")}</span>` : ""}${w.is_gem ? ` <span class="w-flag gem" title="Từ đắt giá">${ic("gem")}</span>` : ""}${w.is_toeic ? ` <span class="w-flag" title="Từ vựng TOEIC${w.toeic_part ? ` (${w.toeic_part})` : ''}" style="background:var(--accent);color:#fff;">TOEIC</span>` : ""}
        <div class="w-meaning">${esc(w.meaning)}</div>
        ${w.example ? `<div class="w-example">"${esc(w.example)}"</div>` : ""}
      </div>
      <div class="w-side">
        <button class="speak-btn" data-say="${esc(w.term)}" title="Nghe phát âm">${ic("speaker")}</button>
        ${w.topic ? `<span class="chip">${esc(w.topic)}</span>` : ""}
        <div class="w-due">ôn: ${dueLabel(w.due_at)}</div>
        <button class="btn ghost danger w-del" data-id="${w.id}" style="font-size: 0.72rem; padding: 2px 8px; margin-top: 4px;">xoá</button>
      </div>
    </div>`;
}

/* ---------------- writing ---------------- */

const writingState = { sub: "practice", kind: "daily", prompt: null };

views.writing = async () => {
  main.innerHTML = `
    <div class="page-title">Writing</div>
    <div class="page-sub">Task 1 (biểu đồ), Task 2 và diễn đạt hằng ngày — AI ra đề, chấm band, sửa từng lỗi.</div>
    <div class="subtabs">
      <button class="subtab ${writingState.sub === "practice" ? "active" : ""}" data-sub="practice">${ic("quill")} Luyện viết</button>
      <button class="subtab ${writingState.sub === "task1" ? "active" : ""}" data-sub="task1">${ic("chart")} Task 1</button>
      <button class="subtab ${writingState.sub === "t1know" ? "active" : ""}" data-sub="t1know">${ic("bulb")} Tri thức T1</button>
      <button class="subtab ${writingState.sub === "patterns" ? "active" : ""}" data-sub="patterns">${ic("layers")} Mẫu câu</button>
      <button class="subtab ${writingState.sub === "history" ? "active" : ""}" data-sub="history">${ic("clock")} Lịch sử</button>
    </div>
    <div id="w-body"></div>`;
  $$(".subtab").forEach((b) => b.addEventListener("click", () => {
    if (writingState.sub === "task1" && b.dataset.sub !== "task1") t1Timer(true);
    writingState.sub = b.dataset.sub;
    views.writing();
  }));
  const body = $("#w-body");
  if (writingState.sub === "practice") renderWritingPractice(body);
  else if (writingState.sub === "task1") await renderTask1(body);
  else if (writingState.sub === "t1know") await renderTask1Knowledge(body);
  else if (writingState.sub === "patterns") await renderPatterns(body);
  else await renderWritingHistory(body);
};

function renderWritingPractice(body) {
  const p = writingState.prompt;
  body.innerHTML = `
    <div class="row mb">
      <select id="wk" style="width: 260px;">
        <option value="daily" ${writingState.kind === "daily" ? "selected" : ""}>Diễn tả hoạt động thường ngày</option>
        <option value="ielts" ${writingState.kind === "ielts" ? "selected" : ""}>IELTS Writing Task 2</option>
      </select>
      <button class="btn primary" id="get-prompt">${ic("dice")} Lấy đề mới (AI)</button>
    </div>
    <div id="prompt-area">${p ? promptCardHTML(p) : `<div class="empty">Bấm "Lấy đề mới" để AI ra đề cho bạn.</div>`}</div>
    <div class="card mt" ${p ? "" : "hidden"} id="editor-card">
      <textarea id="essay" placeholder="Viết bài của bạn ở đây… (tiếng Anh)">${esc(localStorage.getItem("epux-draft") || "")}</textarea>
      <div class="wc-note"><span id="wc">0</span> từ ${p?.min_words ? `· tối thiểu ${p.min_words}` : ""}</div>
      <button class="btn primary mt" id="grade-btn">${ic("pen")} Chấm điểm (AI)</button>
    </div>
    <div id="grade-result" class="mt"></div>`;

  $("#wk").addEventListener("change", (e) => { writingState.kind = e.target.value; });
  const getBtn = $("#get-prompt");
  getBtn.addEventListener("click", () => busy(getBtn, async () => {
    writingState.prompt = await api("/api/writing/prompt", { method: "POST", body: { kind: writingState.kind } });
    renderWritingPractice(body);
  }));

  const essay = $("#essay");
  const updateWc = () => { $("#wc").textContent = essay.value.trim() ? essay.value.trim().split(/\s+/).length : 0; };
  if (essay) {
    updateWc();
    essay.addEventListener("input", () => { updateWc(); localStorage.setItem("epux-draft", essay.value); });
  }

  const gradeBtn = $("#grade-btn");
  if (gradeBtn) gradeBtn.addEventListener("click", () => busy(gradeBtn, async () => {
    const res = await api("/api/writing/grade", {
      method: "POST",
      body: {
        kind: writingState.prompt.kind || writingState.kind,
        title: writingState.prompt.title || "",
        prompt: writingState.prompt.prompt,
        content: essay.value,
        target_language: (writingState.prompt.target_language || []).map((t) => t.phrase).filter(Boolean),
      },
    });
    localStorage.removeItem("epux-draft");
    $("#grade-result").innerHTML = gradeResultHTML(res.writing);
    bindVocabUpgradeButtons();
    $("#grade-result").scrollIntoView({ behavior: "smooth" });
    toast("Đã chấm xong (+1 thử thách Luyện bút)", "ok");
  }));
}

function promptCardHTML(p) {
  const outline = (p.outline_vi || []).map((o) => `<li>${esc(o)}</li>`).join("");
  const lang = (p.target_language || []).map((t) => `
    <div class="tl-item">
      <span class="tl-phrase">${esc(t.phrase)}</span>
      ${t.note_vi ? `<span class="tl-note">${esc(t.note_vi)}</span>` : ""}
    </div>`).join("");
  return `
    <div class="card prompt-card">
      <div class="p-title">${esc(p.title || "Đề bài")} ${p.question_type ? `<span class="chip">${esc(p.question_type)}</span>` : ""}</div>
      <div class="p-text">${esc(p.prompt)}</div>
      ${p.guidance_vi ? `<div class="p-guide">${ic("bulb")} ${esc(p.guidance_vi)}</div>` : ""}
      ${outline ? `<details class="p-outline"><summary>${ic("list")} Dàn ý gợi ý — tự nghĩ trước rồi hãy mở</summary><ul>${outline}</ul></details>` : ""}
      ${lang ? `<div class="p-lang"><div class="p-lang-label">${ic("sparkle")} Thử dùng trong bài (AI sẽ để ý khi chấm)</div>${lang}</div>` : ""}
    </div>`;
}

const CRITERIA_LABELS = [
  ["task_response", "Task response"],
  ["coherence", "Coherence"],
  ["lexical_resource", "Lexical"],
  ["grammar", "Grammar"],
];
const ERROR_TYPE_VI = { grammar: "ngữ pháp", vocab: "từ vựng", spelling: "chính tả", coherence: "mạch lạc", task: "lạc đề" };

function gradeResultHTML(w) {
  const fb = w.feedback || {};
  const c = fb.criteria || {};
  const cf = fb.criteria_feedback || {};
  const critDetail = CRITERIA_LABELS
    .filter(([k]) => cf[k] && (cf[k].comment_vi || cf[k].to_next_band_vi))
    .map(([k, label]) => `
      <div class="crit-item">
        <div class="crit-head">${label} ${c[k] != null ? `<span class="chip">${c[k]}</span>` : ""}</div>
        ${cf[k].comment_vi ? `<div class="crit-comment">${esc(cf[k].comment_vi)}</div>` : ""}
        ${cf[k].to_next_band_vi ? `<div class="crit-next">↗ Để lên band: ${esc(cf[k].to_next_band_vi)}</div>` : ""}
      </div>`).join("");
  const strengths = (fb.strengths_vi || []).map((s) => `<li>${esc(s)}</li>`).join("");
  const errors = (fb.errors || []).map((e) => `
    <div class="error-item">
      ${e.type ? `<span class="chip err-type">${ERROR_TYPE_VI[e.type] || esc(e.type)}</span> ` : ""}
      <span class="e-quote">${esc(e.quote)}</span> → <span class="e-fix">${esc(e.fix)}</span>
      <div class="e-explain">${esc(e.explain_vi)}</div>
    </div>`).join("");
  const impNotes = (fb.improved_notes_vi || []).map((n) => `<li>${esc(n)}</li>`).join("");
  const plan = (fb.band_up_plan_vi || []).map((s) => `<li>${esc(s)}</li>`).join("");
  const vocab = (fb.vocab_upgrades || []).map((v) => `
    <div class="word-row">
      <div class="w-main">
        <span class="w-term">${esc(v.term)}</span>
        <div class="w-meaning">${esc(v.meaning_vi)}</div>
        ${v.replaces_vi ? `<div class="w-replaces">↔ ${esc(v.replaces_vi)}</div>` : ""}
        ${v.example ? `<div class="w-example">"${esc(v.example)}"</div>` : ""}
      </div>
      <button class="btn vocab-add" data-term="${esc(v.term)}">+ Học từ này</button>
    </div>`).join("");
  return `
    <div class="card">
      <b>Kết quả chấm</b>
      <div class="band-tiles mt">
        <div class="band-tile overall"><div class="b-num">${fb.overall_band ?? "?"}</div><div class="b-label">Overall band</div></div>
        <div class="band-tile"><div class="b-num">${c.task_response ?? "–"}</div><div class="b-label">Task response</div></div>
        <div class="band-tile"><div class="b-num">${c.coherence ?? "–"}</div><div class="b-label">Coherence</div></div>
        <div class="band-tile"><div class="b-num">${c.lexical_resource ?? "–"}</div><div class="b-label">Lexical</div></div>
        <div class="band-tile"><div class="b-num">${c.grammar ?? "–"}</div><div class="b-label">Grammar</div></div>
      </div>
      ${fb.summary_vi ? `<p class="mt" style="line-height: 1.6; color: var(--text-2);">${esc(fb.summary_vi)}</p>` : ""}
      ${critDetail ? `<details class="crit-details mt"><summary>${ic("search")} Phân tích từng tiêu chí</summary>${critDetail}</details>` : ""}
      ${strengths ? `<div class="mt strengths"><b>${ic("star")} Bạn đang làm tốt</b><ul>${strengths}</ul></div>` : ""}
      ${errors ? `<div class="mt"><b>${ic("x-circle")} Lỗi cần sửa (${(fb.errors || []).length})</b>${errors}</div>` : ""}
      ${fb.improved_version ? `
        <details class="improved">
          <summary>${ic("sparkle")} Xem bản viết lại ở band cao hơn</summary>
          <div class="imp-text">${esc(fb.improved_version)}</div>
          ${impNotes ? `<div class="imp-notes"><b>Vì sao bản này band cao hơn:</b><ul>${impNotes}</ul></div>` : ""}
        </details>` : ""}
      ${plan ? `<div class="mt band-plan"><b>${ic("target")} Việc cần làm cho bài sau</b><ol>${plan}</ol></div>` : ""}
      ${vocab ? `<div class="mt"><b>${ic("gem")} Từ vựng nâng band — thêm vào bộ học?</b>${vocab}</div>` : ""}
    </div>`;
}

function bindVocabUpgradeButtons() {
  $$(".vocab-add").forEach((btn) => btn.addEventListener("click", () => busy(btn, async () => {
    const res = await api("/api/words", { method: "POST", body: { term: btn.dataset.term, ai_enrich: true } });
    btn.textContent = "✓ Đã thêm";
    toast(`Đã thêm "${res.word.term}" (${res.word.rarity}) vào lịch học`, "ok");
  })));
}

/* ---------------- IELTS Task 1 ---------------- */

const SERIES_VARS = ["var(--series-1)", "var(--series-2)", "var(--series-3)", "var(--series-4)", "var(--series-5)"];
const AI_TYPES = ["line", "bar", "pie", "table"];

const task1State = {
  data: null,        // { knowledge, bank }
  mode: "bank",      // bank | ai
  type: "line",
  item: null,        // bank item currently shown
  gen: null,         // AI-generated task { prompt, chart, ... }
  timerId: null,
  secondsLeft: 20 * 60,
};

/* ---- chart renderer: exam-style figures, values read off the axes (no tooltips
       by design — revealing exact numbers would defeat the skill being practised) ---- */

function niceScale(maxValue) {
  if (!(maxValue > 0)) return { top: 1, ticks: [0, 0.5, 1] };
  const exp = Math.floor(Math.log10(maxValue));
  const base = Math.pow(10, exp);
  let top = base * 10;
  for (const c of [1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10]) {
    if (base * c >= maxValue) { top = base * c; break; }
  }
  const fmt = (n) => +n.toFixed(4);
  return { top, ticks: [0, 1, 2, 3, 4].map((i) => fmt((top * i) / 4)).concat(fmt(top)) };
}

function chartLegendHTML(names) {
  if (names.length < 2) return "";
  return `<div class="ch-legend">${names.map((n, i) => `
    <span class="ch-leg"><i style="background: ${SERIES_VARS[i % 5]}"></i>${esc(n)}</span>`).join("")}</div>`;
}

function svgLine(chart) {
  const cats = chart.categories || [];
  const series = chart.series || [];
  const W = 720, H = 340, L = 62, R = 108, T = 16, B = 44;
  const max = Math.max(...series.flatMap((s) => s.values || []), 0);
  const { top, ticks } = niceScale(max);
  const x = (i) => L + (i * (W - L - R)) / Math.max(1, cats.length - 1);
  const y = (v) => H - B - ((v / top) * (H - B - T));
  const grid = ticks.map((t) => `
    <line x1="${L}" y1="${y(t)}" x2="${W - R}" y2="${y(t)}" class="ch-grid"/>
    <text x="${L - 10}" y="${y(t) + 4}" class="ch-tick" text-anchor="end">${t}</text>`).join("");
  const xLabels = cats.map((c, i) => `
    <text x="${x(i)}" y="${H - B + 20}" class="ch-tick" text-anchor="middle">${esc(String(c))}</text>`).join("");
  const lines = series.map((s, si) => {
    const color = SERIES_VARS[si % 5];
    const pts = (s.values || []).map((v, i) => `${x(i)},${y(v)}`).join(" ");
    const dots = (s.values || []).map((v, i) => `<circle cx="${x(i)}" cy="${y(v)}" r="4" style="fill: ${color}"/>`).join("");
    const last = (s.values || []).length - 1;
    const label = last >= 0
      ? `<text x="${x(last) + 10}" y="${y(s.values[last]) + 4}" class="ch-end" style="fill: ${color}">${esc(s.name || "")}</text>`
      : "";
    return `<polyline points="${pts}" style="stroke: ${color}" class="ch-line"/>${dots}${label}`;
  }).join("");
  return `
    <svg viewBox="0 0 ${W} ${H}" class="ch-svg" role="img" aria-label="${esc(chart.title || "Line graph")}">
      ${grid}
      <line x1="${L}" y1="${T}" x2="${L}" y2="${H - B}" class="ch-axis"/>
      <line x1="${L}" y1="${H - B}" x2="${W - R}" y2="${H - B}" class="ch-axis"/>
      ${xLabels}${lines}
    </svg>`;
}

function svgBar(chart) {
  const cats = chart.categories || [];
  const series = chart.series || [];
  const W = 720, H = 340, L = 62, R = 20, T = 16, B = 52;
  const max = Math.max(...series.flatMap((s) => s.values || []), 0);
  const { top, ticks } = niceScale(max);
  const y = (v) => H - B - ((v / top) * (H - B - T));
  const bandW = (W - L - R) / Math.max(1, cats.length);
  const inner = bandW * 0.72;
  const barW = Math.max(6, inner / Math.max(1, series.length) - 2); // 2px surface gap between adjacent bars
  const grid = ticks.map((t) => `
    <line x1="${L}" y1="${y(t)}" x2="${W - R}" y2="${y(t)}" class="ch-grid"/>
    <text x="${L - 10}" y="${y(t) + 4}" class="ch-tick" text-anchor="end">${t}</text>`).join("");
  const bars = cats.map((c, ci) => {
    const groupX = L + ci * bandW + (bandW - inner) / 2;
    const rects = series.map((s, si) => {
      const v = (s.values || [])[ci] ?? 0;
      const bx = groupX + si * (barW + 2);
      const h = Math.max(0, (H - B) - y(v));
      return `<rect x="${bx}" y="${y(v)}" width="${barW}" height="${h}" rx="4"
                style="fill: ${SERIES_VARS[si % 5]}"><title>${esc(s.name || "")}: ${v}</title></rect>`;
    }).join("");
    return `${rects}<text x="${L + ci * bandW + bandW / 2}" y="${H - B + 20}" class="ch-tick"
              text-anchor="middle">${esc(String(c))}</text>`;
  }).join("");
  return `
    <svg viewBox="0 0 ${W} ${H}" class="ch-svg" role="img" aria-label="${esc(chart.title || "Bar chart")}">
      ${grid}
      <line x1="${L}" y1="${T}" x2="${L}" y2="${H - B}" class="ch-axis"/>
      <line x1="${L}" y1="${H - B}" x2="${W - R}" y2="${H - B}" class="ch-axis"/>
      ${bars}
    </svg>`;
}

function svgPie(chart) {
  const pies = chart.pies || [];
  const per = pies.length > 2 ? 2 : pies.length; // 2 per row
  const size = 220, r = 78, cx = size / 2, cy = size / 2 + 6;
  const svgs = pies.map((p) => {
    const slices = p.slices || [];
    const total = slices.reduce((a, s) => a + (Number(s.value) || 0), 0) || 1;
    let angle = -Math.PI / 2;
    const paths = slices.map((s, si) => {
      const frac = (Number(s.value) || 0) / total;
      const a0 = angle;
      const a1 = angle + frac * Math.PI * 2;
      angle = a1;
      const big = a1 - a0 > Math.PI ? 1 : 0;
      const p0 = [cx + r * Math.cos(a0), cy + r * Math.sin(a0)];
      const p1 = [cx + r * Math.cos(a1), cy + r * Math.sin(a1)];
      const mid = (a0 + a1) / 2;
      const lx = cx + (r + 22) * Math.cos(mid);
      const ly = cy + (r + 22) * Math.sin(mid);
      const anchor = Math.cos(mid) > 0.15 ? "start" : Math.cos(mid) < -0.15 ? "end" : "middle";
      const d = frac >= 0.999
        ? `M ${cx} ${cy - r} A ${r} ${r} 0 1 1 ${cx - 0.01} ${cy - r} Z`
        : `M ${cx} ${cy} L ${p0[0]} ${p0[1]} A ${r} ${r} 0 ${big} 1 ${p1[0]} ${p1[1]} Z`;
      // 2px surface stroke = the gap between adjacent fills
      return `<path d="${d}" style="fill: ${SERIES_VARS[si % 5]}" class="ch-slice"/>
              <text x="${lx}" y="${ly + 4}" class="ch-pie-label" text-anchor="${anchor}">${esc(String(s.value))}</text>`;
    }).join("");
    // viewBox is widened well past the circle so the value labels outside it are never clipped
    return `
      <figure class="ch-pie">
        <svg viewBox="-46 -6 ${size + 92} ${size + 30}" role="img" aria-label="${esc(p.title || "Pie chart")}">${paths}</svg>
        <figcaption>${esc(p.title || "")}</figcaption>
      </figure>`;
  }).join("");
  return `<div class="ch-pies" style="--per: ${per}">${svgs}</div>`;
}

function chartTableHTML(chart) {
  const cols = chart.columns || [];
  const rows = chart.rows || [];
  return `
    <div class="ch-table-wrap">
      <table class="ch-table">
        <thead><tr>${cols.map((c) => `<th>${esc(String(c))}</th>`).join("")}</tr></thead>
        <tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${esc(String(c))}</td>`).join("")}</tr>`).join("")}</tbody>
      </table>
    </div>`;
}

function dataTableHTML(chart) {
  if (chart.kind === "table") return "";
  let cols = [];
  let rows = [];
  if (chart.kind === "pie") {
    const labels = (chart.pies?.[0]?.slices || []).map((s) => s.label);
    cols = ["", ...labels];
    rows = (chart.pies || []).map((p) => [p.title, ...(p.slices || []).map((s) => s.value)]);
  } else {
    cols = ["", ...(chart.categories || [])];
    rows = (chart.series || []).map((s) => [s.name, ...(s.values || [])]);
  }
  return `
    <details class="ch-data">
      <summary>${ic("list")} Xem bảng số liệu (nếu nhìn biểu đồ chưa chắc số)</summary>
      ${chartTableHTML({ columns: cols, rows })}
    </details>`;
}

function chartHTML(chart) {
  if (!chart || !chart.kind) return "";
  let figure = "";
  if (chart.kind === "line") figure = svgLine(chart);
  else if (chart.kind === "bar") figure = svgBar(chart);
  else if (chart.kind === "pie") figure = svgPie(chart);
  else if (chart.kind === "table") figure = chartTableHTML(chart);
  const names = chart.kind === "pie"
    ? (chart.pies?.[0]?.slices || []).map((s) => s.label)
    : (chart.series || []).map((s) => s.name);
  return `
    <figure class="ch-fig">
      ${chart.title ? `<figcaption class="ch-title">${esc(chart.title)}</figcaption>` : ""}
      ${chart.unit ? `<div class="ch-unit">${esc(chart.unit)}</div>` : ""}
      ${chart.kind !== "table" ? chartLegendHTML(names) : ""}
      ${figure}
      ${dataTableHTML(chart)}
    </figure>`;
}

/* ---- practice screen ---- */

function t1Timer(stop) {
  if (task1State.timerId) { clearInterval(task1State.timerId); task1State.timerId = null; }
  if (stop) return;
  task1State.timerId = setInterval(() => {
    const el = $("#t1-clock");
    if (!el) { clearInterval(task1State.timerId); task1State.timerId = null; return; }
    task1State.secondsLeft = Math.max(0, task1State.secondsLeft - 1);
    const m = String(Math.floor(task1State.secondsLeft / 60)).padStart(2, "0");
    const s = String(task1State.secondsLeft % 60).padStart(2, "0");
    el.textContent = `${m}:${s}`;
    el.classList.toggle("low", task1State.secondsLeft <= 300);
    if (task1State.secondsLeft === 0) { clearInterval(task1State.timerId); task1State.timerId = null; }
  }, 1000);
}

async function renderTask1(body) {
  if (!task1State.data) task1State.data = await api("/api/task1/knowledge");
  const { bank, knowledge } = task1State.data;
  const types = task1State.mode === "ai" ? AI_TYPES : Object.keys(knowledge.types);
  if (!types.includes(task1State.type)) task1State.type = types[0];

  const task = task1State.mode === "bank" ? task1State.item : task1State.gen;
  const tips = (knowledge.type_tips[task1State.type] || []).map((t) => `<li>${esc(t)}</li>`).join("");

  body.innerHTML = `
    <div class="row mb t1-controls">
      <select id="t1-mode" style="width: 230px;">
        <option value="bank" ${task1State.mode === "bank" ? "selected" : ""}>Đề thật (có bài mẫu band 9)</option>
        <option value="ai" ${task1State.mode === "ai" ? "selected" : ""}>AI ra đề mới</option>
      </select>
      <select id="t1-type" style="width: 180px;">
        ${types.map((t) => `<option value="${t}" ${task1State.type === t ? "selected" : ""}>
          ${esc(knowledge.types[t].label_vi)}</option>`).join("")}
      </select>
      <button class="btn primary" id="t1-new">${ic("dice")} Lấy đề</button>
      ${task ? `<span class="t1-clock" id="t1-clock" title="20 phút như thi thật">20:00</span>` : ""}
    </div>

    ${tips ? `<details class="card t1-tips mb"><summary>${ic("bulb")} Mẹo cho dạng ${esc(knowledge.types[task1State.type].label_vi)}</summary><ul>${tips}</ul></details>` : ""}

    <div id="t1-task">${task ? t1TaskHTML(task) : `<div class="empty">Chọn dạng biểu đồ rồi bấm "Lấy đề".</div>`}</div>

    <div class="card mt" ${task ? "" : "hidden"} id="t1-editor">
      <textarea id="t1-essay" placeholder="Viết bài Task 1 của bạn ở đây… (tiếng Anh, 4 đoạn)">${esc(localStorage.getItem("epux-t1-draft") || "")}</textarea>
      <div class="wc-note"><span id="t1-wc">0</span> / 150 từ tối thiểu</div>
      <button class="btn primary mt" id="t1-grade">${ic("pen")} Chấm điểm (AI)</button>
    </div>
    <div id="t1-result" class="mt"></div>`;

  $("#t1-mode").addEventListener("change", (e) => {
    task1State.mode = e.target.value;
    task1State.item = null; task1State.gen = null;
    t1Timer(true);
    renderTask1(body);
  });
  $("#t1-type").addEventListener("change", (e) => { task1State.type = e.target.value; });

  const newBtn = $("#t1-new");
  newBtn.addEventListener("click", () => busy(newBtn, async () => {
    if (task1State.mode === "bank") {
      const pool = bank.filter((b) => b.type === task1State.type && b.id !== task1State.item?.id);
      if (!pool.length) { toast("Hết đề dạng này rồi", "warn"); return; }
      task1State.item = pool[Math.floor(Math.random() * pool.length)];
      task1State.gen = null;
    } else {
      task1State.gen = await api("/api/task1/generate", { method: "POST", body: { chart_type: task1State.type } });
      task1State.item = null;
    }
    localStorage.removeItem("epux-t1-draft");
    task1State.secondsLeft = 20 * 60;
    renderTask1(body);
    t1Timer();
  }));

  const essay = $("#t1-essay");
  if (essay) {
    const updateWc = () => {
      const n = essay.value.trim() ? essay.value.trim().split(/\s+/).length : 0;
      const el = $("#t1-wc");
      el.textContent = n;
      el.classList.toggle("short", n < 150);
    };
    updateWc();
    essay.addEventListener("input", () => { updateWc(); localStorage.setItem("epux-t1-draft", essay.value); });
  }

  const gradeBtn = $("#t1-grade");
  if (gradeBtn) gradeBtn.addEventListener("click", () => busy(gradeBtn, async () => {
    const payload = task1State.mode === "bank"
      ? { bank_id: task1State.item.id, content: essay.value }
      : {
          content: essay.value,
          prompt: task1State.gen.prompt,
          title: task1State.gen.title || "",
          chart_type: task1State.gen.chart_type || task1State.type,
          chart: task1State.gen.chart,
        };
    const res = await api("/api/task1/grade", { method: "POST", body: payload });
    t1Timer(true);
    localStorage.removeItem("epux-t1-draft");
    $("#t1-result").innerHTML =
      task1CheckHTML(res.writing.feedback) + gradeResultHTML(res.writing) + modelAnswerHTML(res.model);
    bindVocabUpgradeButtons();
    $("#t1-result").scrollIntoView({ behavior: "smooth" });
    toast("Đã chấm xong (+1 thử thách Luyện bút)", "ok");
  }));

  const modelBox = $(".p-model");
  if (modelBox) modelBox.addEventListener("toggle", async () => {
    const el = $(".p-model-body");
    if (!modelBox.open || !el || el.dataset.loaded) return;
    const m = await api(`/api/task1/model/${el.dataset.model}`);
    el.innerHTML = m.model.split("\n\n").map((p) => `<p>${esc(p)}</p>`).join("");
    el.dataset.loaded = "1";
  });

  if (task && !task1State.timerId) t1Timer();
}

function t1TaskHTML(task) {
  // bank item: has .image ; AI item: has .chart
  const outline = (task.outline_vi || []).map((o) => `<li>${esc(o)}</li>`).join("");
  const lang = (task.target_language || []).map((t) => `
    <div class="tl-item">
      <span class="tl-phrase">${esc(t.phrase)}</span>
      ${t.note_vi ? `<span class="tl-note">${esc(t.note_vi)}</span>` : ""}
    </div>`).join("");
  return `
    <div class="card prompt-card">
      <div class="p-title">${esc(task.title || "Task 1")}
        <span class="chip">${esc(task.type || task.chart_type || "")}</span>
        ${task.id ? `<span class="chip">đề thật</span>` : `<span class="chip">AI</span>`}
      </div>
      <div class="p-text">${esc(task.question || task.prompt)}</div>
      ${task.image ? `<img class="t1-img" src="${esc(task.image)}" alt="Biểu đồ đề bài">` : chartHTML(task.chart)}
      ${task.focus_vi ? `<div class="p-guide">${ic("target")} ${esc(task.focus_vi)}</div>` : ""}
      ${task.guidance_vi ? `<div class="p-guide">${ic("bulb")} ${esc(task.guidance_vi)}</div>` : ""}
      ${task.note_vi ? `<div class="p-note">${esc(task.note_vi)}</div>` : ""}
      ${outline ? `<details class="p-outline"><summary>${ic("list")} Dàn ý gợi ý — tự nghĩ trước rồi hãy mở</summary><ul>${outline}</ul></details>` : ""}
      ${lang ? `<div class="p-lang"><div class="p-lang-label">${ic("sparkle")} Thử dùng trong bài</div>${lang}</div>` : ""}
      ${task.id ? `<details class="p-model"><summary>${ic("book")} Bài mẫu band 9 — chỉ mở sau khi bạn đã viết xong</summary>
        <div class="p-model-body" data-model="${esc(task.id)}">Đang tải…</div></details>` : ""}
    </div>`;
}

function task1CheckHTML(fb) {
  const t = (fb || {}).task1_check;
  if (!t) return "";
  const item = (ok, label) => `
    <div class="t1-check ${ok ? "ok" : "bad"}">${ic(ok ? "check-circle" : "x-circle")} ${label}</div>`;
  return `
    <div class="card t1-checks">
      <b>${ic("target")} 4 điểm sống còn của Task 1</b>
      <div class="t1-check-row mt">
        ${item(t.has_overview, "Có overview")}
        ${item(t.data_accurate, "Số liệu chính xác")}
        ${item(t.opinion_free, "Không ý kiến cá nhân")}
        ${item(t.word_count_ok, "Đủ 150 từ")}
      </div>
      ${t.overview_quote ? `<div class="t1-quote">Overview tìm thấy: "${esc(t.overview_quote)}"</div>` : ""}
      ${t.verdict_vi ? `<div class="t1-verdict">${esc(t.verdict_vi)}</div>` : ""}
    </div>`;
}

function modelAnswerHTML(model) {
  if (!model || !model.model) return "";
  const paras = model.model.split("\n\n").map((p) => `<p>${esc(p)}</p>`).join("");
  return `
    <details class="card improved mt" open>
      <summary>${ic("book")} Đối chiếu bài mẫu band 9 (${model.words} từ)</summary>
      <div class="imp-text">${paras}</div>
    </details>`;
}

/* ---- knowledge screen ---- */

async function renderTask1Knowledge(body) {
  if (!task1State.data) task1State.data = await api("/api/task1/knowledge");
  const k = task1State.data.knowledge;

  const structure = k.structure.map((s) => `
    <div class="kn-step">
      <div class="kn-step-name">${esc(s.name)}</div>
      <div class="kn-step-body">${esc(s.body_vi)}</div>
      <div class="kn-step-ex">${esc(s.example)}</div>
    </div>`).join("");
  const rules = k.rules_vi.map((r) => `<li>${esc(r)}</li>`).join("");
  const traps = k.traps_vi.map((t) => `<li>${esc(t)}</li>`).join("");
  const tips = Object.entries(k.type_tips).map(([type, list]) => `
    <details class="kn-type">
      <summary>${esc(k.types[type].label_vi)} <span class="chip">${esc(k.types[type].label_en)}</span></summary>
      <ul>${list.map((t) => `<li>${esc(t)}</li>`).join("")}</ul>
    </details>`).join("");
  const lang = k.language.map((g) => `
    <div class="kn-lang-group">
      <div class="kn-lang-name">${esc(g.group_vi)}</div>
      <div class="kn-lang-items">${g.items.map((i) => `<span class="chip">${esc(i)}</span>`).join("")}</div>
    </div>`).join("");

  body.innerHTML = `
    <div class="card mb"><p class="kn-intro">${esc(k.intro_vi)}</p></div>

    <div class="card mb">
      <b>${ic("layers")} Bộ khung 4 đoạn — dùng cho MỌI dạng</b>
      <div class="kn-steps mt">${structure}</div>
    </div>

    <div class="card mb">
      <b>${ic("list")} Luật bất di bất dịch</b>
      <ul class="kn-list">${rules}</ul>
    </div>

    <div class="card mb">
      <b>${ic("alert")} Lỗi giết band</b>
      <ul class="kn-list kn-traps">${traps}</ul>
    </div>

    <div class="card mb">
      <b>${ic("chart")} Mẹo theo từng dạng</b>
      <div class="mt">${tips}</div>
    </div>

    <div class="card">
      <b>${ic("sparkle")} Ngôn ngữ mô tả số liệu</b>
      <div class="kn-lang mt">${lang}</div>
    </div>`;
}

async function renderPatterns(body) {
  const data = await api("/api/patterns");
  const presets = ["daily routines", "IT work life", "expressing opinions", "describing problems & solutions", "talking about plans"];
  body.innerHTML = `
    <div class="card mb">
      <b>${ic("layers")} Sinh mẫu câu theo chủ đề</b>
      <div class="row mt">
        <input type="text" id="pt-theme" class="grow" placeholder="Chủ đề, vd: daily routines, meetings, deadlines…" list="pt-presets">
        <datalist id="pt-presets">${presets.map((p) => `<option value="${p}">`).join("")}</datalist>
        <button class="btn primary" id="pt-gen">Sinh 6 mẫu câu</button>
      </div>
      <div class="mt" style="display: flex; gap: 8px; flex-wrap: wrap;">
        ${data.themes.map((t) => `<span class="chip clickable pt-theme-chip" data-t="${esc(t)}">${esc(t)}</span>`).join("")}
      </div>
    </div>
    <div id="pt-list">
      ${data.patterns.length ? data.patterns.map(patternCardHTML).join("") : `<div class="empty">Chưa có mẫu câu nào — sinh thử chủ đề "daily routines" nhé!</div>`}
    </div>`;

  const gen = $("#pt-gen");
  gen.addEventListener("click", () => busy(gen, async () => {
    const theme = $("#pt-theme").value.trim() || "daily routines";
    await api("/api/patterns/generate", { method: "POST", body: { theme, count: 6 } });
    toast(`Đã sinh mẫu câu cho "${theme}"`, "ok");
    renderPatterns(body);
  }));
  $$(".pt-theme-chip").forEach((chip) => chip.addEventListener("click", async () => {
    const d = await api(`/api/patterns?theme=${encodeURIComponent(chip.dataset.t)}`);
    $("#pt-list").innerHTML = d.patterns.map(patternCardHTML).join("");
    bindPatternPractice();
  }));
  bindPatternPractice();
}

function patternCardHTML(p) {
  return `
    <div class="card pattern-card">
      <div class="pt-pattern">${esc(p.pattern)} ${p.band ? `<span class="chip">${esc(p.band)}</span>` : ""}</div>
      <div class="pt-use">${esc(p.use_vi)}</div>
      ${(p.examples || []).map((e) => `<div class="pt-ex">· ${esc(e)}</div>`).join("")}
      <div class="practice-box">
        <input type="text" placeholder="Đặt câu của bạn với mẫu này…" class="grow pt-input" data-pattern="${esc(p.pattern)}">
        <button class="btn pt-check">Kiểm tra</button>
      </div>
      <div class="practice-fb"></div>
    </div>`;
}

function bindPatternPractice() {
  $$(".pt-check").forEach((btn) => btn.addEventListener("click", () => busy(btn, async () => {
    const input = btn.parentElement.querySelector(".pt-input");
    const fbEl = btn.parentElement.parentElement.querySelector(".practice-fb");
    if (!input.value.trim()) return;
    const res = await api("/api/patterns/practice", {
      method: "POST",
      body: { pattern: input.dataset.pattern, sentence: input.value },
    });
    fbEl.innerHTML = `
      <span style="color: ${res.ok ? "var(--good)" : "var(--warn)"}; font-weight: 700;">${res.score}/100</span>
      — ${esc(res.feedback_vi)}
      ${res.corrected && res.corrected !== input.value ? `<div style="color: var(--good); margin-top: 4px;">→ ${esc(res.corrected)}</div>` : ""}
      ${res.upgrade && res.upgrade !== res.corrected ? `<div style="margin-top: 4px;">${ic("sparkle")} Bản xịn hơn: <i>${esc(res.upgrade)}</i></div>` : ""}
      ${res.tip_vi ? `<div class="d-sub" style="margin-top: 4px;">${ic("bulb")} ${esc(res.tip_vi)}</div>` : ""}`;
  })));
}

async function renderWritingHistory(body) {
  const data = await api("/api/writing/history");
  if (!data.writings.length) {
    body.innerHTML = `<div class="empty">Chưa có bài viết nào được chấm.</div>`;
    return;
  }
  body.innerHTML = `
    <div class="card">
      ${data.writings.map((w) => `
        <div class="history-item" data-id="${w.id}">
          <div class="h-title">${w.overall_band != null ? `<span style="color: var(--good); font-weight: 800;">${w.overall_band}</span> · ` : ""}${esc(w.title || w.prompt.slice(0, 80))}</div>
          <div class="h-meta">${w.kind === "ielts" ? "IELTS Task 2" : "Daily"} · ${w.word_count} từ · ${new Date(w.created_at).toLocaleDateString("vi-VN")}</div>
          <div class="h-detail" hidden></div>
        </div>`).join("")}
    </div>`;
  const writings = Object.fromEntries(data.writings.map((w) => [w.id, w]));
  $$(".history-item").forEach((item) => item.addEventListener("click", (e) => {
    // click bên trong phần chi tiết (details, nút thêm từ, loa...) không được đóng cả khối
    if (e.target.closest(".h-detail")) return;
    const det = $(".h-detail", item);
    if (!det.hidden) { det.hidden = true; return; }
    const w = writings[item.dataset.id];
    det.innerHTML = `
      <div class="mt" style="color: var(--muted); font-size: 0.85rem;">Đề: ${esc(w.prompt)}</div>
      <div class="mt" style="white-space: pre-wrap; color: var(--text-2); font-size: 0.9rem; line-height: 1.6;">${esc(w.content)}</div>
      <div class="mt">${gradeResultHTML(w)}</div>`;
    det.hidden = false;
    bindVocabUpgradeButtons();
  }));
}

/* ---------------- collection ---------------- */

views.collection = async () => {
  const [col, ch] = await Promise.all([api("/api/collection"), api("/api/challenges")]);
  const byRarity = col.by_rarity || {};
  const summary = RARITY_ORDER.map((r) => {
    const s = byRarity[r] || { total: 0, owned: 0 };
    return `<div class="rs-chip rarity-${r}"><div class="rs-r">${r}</div><div class="rs-n">${s.owned || 0}/${s.total || 0}</div></div>`;
  }).join("") + `<div class="rs-chip rarity-S"><div class="rs-r">★</div><div class="rs-n">${col.total_stars || 0} sao</div></div>`;

  // Thẻ sở hữu trước, thẻ chưa có hiện silhouette ??? phía sau
  const groups = RARITY_ORDER.map((r) => {
    const cards = col.cards.filter((c) => c.rarity === r);
    if (!cards.length) return "";
    const owned = cards.filter((c) => c.owned);
    const locked = cards.filter((c) => !c.owned);
    return `
      <div class="rarity-section-title rarity-${r}">${r} · ${owned.length}/${cards.length} thẻ</div>
      <div class="cards-grid">
        ${owned.map((c) => cardHTML(c)).join("")}
        ${locked.map((c) => cardHTML(c, "", { locked: true })).join("")}
      </div>`;
  }).join("");

  const packs = ch.packs.length
    ? ch.packs.map((p) => packHTML(p)).join("")
    : `<div class="empty" style="padding: 10px;">Hết pack — làm thử thách ở tab "Hôm nay" để nhận thêm!</div>`;

  main.innerHTML = `
    <div class="page-title">Bộ sưu tập</div>
    <div class="page-sub">Mỗi từ là một thẻ bài có chòm sao và thần hộ mệnh riêng. Mở pack để thu phục thẻ — trùng thẻ thì gộp nâng ★.</div>
    <div class="rarity-summary">${summary}</div>
    <div class="row mb">
      <div class="card grow">
        <b>${ic("gift")} Pack chưa mở</b>
        <div class="pack-shelf mt">${packs}</div>
      </div>
      <div class="card" style="flex: 0 0 250px; display: flex; flex-direction: column; justify-content: center; gap: 10px;">
        <b>${ic("cards")} Mở rộng kho thẻ</b>
        <div style="color: var(--muted); font-size: 0.8rem;">AI sinh ~15 từ mới trên 3 chủ đề IELTS — thêm thẻ mới để săn trong pack.</div>
        <button class="btn primary" id="expand-btn">${ic("sparkle")} Mở rộng (+15 thẻ)</button>
      </div>
    </div>
    ${col.cards.length ? groups : `<div class="empty">Chưa có thẻ nào — bấm "Mở rộng kho thẻ" hoặc thêm từ ở tab Từ vựng!</div>`}`;
  bindPackOpens();
  const expandBtn = $("#expand-btn");
  expandBtn.addEventListener("click", () => busy(expandBtn, async () => {
    const res = await api("/api/collection/expand", { method: "POST", body: { count: 15 } });
    toast(`+${res.added} thẻ mới từ: ${res.topics.join(", ")}`, "ok");
    views.collection();
  }));
};

/* ---------------- arena (PK) ---------------- */

function opponentRowHTML(o) {
  const rarities = (o.rarities || []).map((r) => `<span class="chip rarity-chip rarity-${r}">${r}</span>`).join("");
  return `
    <div class="opponent-row">
      <div class="opp-info">
        <div class="opp-name">${esc(o.username)}</div>
        <div class="opp-meta">${ic("flame")} ${o.rating} · ${o.wins}T/${o.losses}B · ${o.card_count} thẻ ${rarities}</div>
      </div>
      <button class="btn primary arena-attack-btn" data-id="${o.user_id}" data-name="${esc(o.username)}">${ic("bolt")} Tấn công</button>
    </div>`;
}

function battleRowHTML(b) {
  const win = b.result === "win";
  return `
    <div class="battle-row ${win ? "win" : "loss"}">
      <div class="battle-main"><b>${esc(b.attacker_name)}</b> tấn công <b>${esc(b.defender_name)}</b>
        <span class="chip">${b.attacker_power} vs ${b.defender_power}</span></div>
      <div class="battle-meta">${win ? `${esc(b.attacker_name)} thắng` : `${esc(b.defender_name)} phòng thủ thành công`}
        · quiz ${b.quiz_correct}/${b.quiz_total}${b.pack_tier ? ` · +1 ${PACK_NAMES[b.pack_tier]}` : ""}</div>
    </div>`;
}

function openDefensePicker(currentIds, cards, maxCards) {
  const selected = new Set(currentIds);
  const ownedCards = cards.filter((c) => c.owned);
  const byId = Object.fromEntries(ownedCards.map((c) => [c.id, c]));

  const m = modal(`
    <div class="arena-picker">
      <div class="page-title" style="margin:0;">Xếp đội hình phòng thủ</div>
      <div class="page-sub">Chọn tối đa ${maxCards} thẻ — đây cũng là đội bạn dùng khi đi tấn công người khác.</div>
      <div class="arena-picker-power">${ic("bolt")} Sức mạnh: <b id="arena-picker-power-val">0</b></div>
      <div class="cards-grid arena-grid">${ownedCards.map((c) => cardHTML(c)).join("")}</div>
      <div class="arena-picker-actions">
        <button class="btn ghost" onclick="closeModal()">Huỷ</button>
        <button class="btn primary" id="arena-save-defense">${ic("check-circle")} Lưu đội hình</button>
      </div>
    </div>`);

  const refresh = () => {
    $$(".tcg[data-id]", m).forEach((el) => el.classList.toggle("selected", selected.has(Number(el.dataset.id))));
    const power = [...selected].reduce((s, id) => s + (byId[id] ? powerOf(byId[id]) : 0), 0);
    $("#arena-picker-power-val", m).textContent = `${power} (${selected.size}/${maxCards})`;
  };
  refresh();

  m.addEventListener("click", (e) => {
    const tcg = e.target.closest(".tcg[data-id]");
    if (!tcg) return;
    e.stopPropagation();
    const id = Number(tcg.dataset.id);
    if (selected.has(id)) selected.delete(id);
    else if (selected.size >= maxCards) { toast(`Chỉ được chọn tối đa ${maxCards} thẻ.`, "err"); return; }
    else selected.add(id);
    refresh();
  });

  $("#arena-save-defense", m).addEventListener("click", () => busy($("#arena-save-defense", m), async () => {
    if (!selected.size) { toast("Chọn ít nhất 1 thẻ.", "err"); return; }
    await api("/api/arena/defense", { method: "POST", body: { word_ids: [...selected] } });
    toast("Đã lưu đội hình phòng thủ!", "ok");
    closeModal();
    show("arena");
  }));
}

async function startAttack(defenderId, defenderName) {
  let prep;
  try {
    prep = await api(`/api/arena/attack/${defenderId}/prepare`, { method: "POST" });
  } catch (err) {
    toast(err.message, "err");
    return;
  }
  renderAttackQuiz(defenderId, defenderName, prep.questions);
}

function renderAttackQuiz(defenderId, defenderName, questions) {
  const answers = new Array(questions.length).fill(null);
  const m = modal(`
    <div class="arena-quiz">
      <div class="page-title" style="margin:0;">Tấn công ${esc(defenderName)}</div>
      <div class="page-sub">Trả lời đúng câu hỏi về từ vựng của đối thủ để cộng thêm sức mạnh tấn công (+15%/câu đúng).</div>
      ${questions.map((q, i) => `
        <div class="card mb aq-question" data-i="${i}">
          <div style="color: var(--muted); font-size: 0.8rem;">${q.mode === "term_to_meaning" ? "Nghĩa của từ này là gì?" : "Từ nào khớp với nghĩa này?"}</div>
          <div style="font-size: 1.1rem; font-weight: 700; margin-top: 6px;">${esc(q.prompt)}</div>
          <div class="mt aq-options">${q.options.map((o) => `<button class="q-option" data-v="${esc(o)}">${esc(o)}</button>`).join("")}</div>
        </div>`).join("")}
      <div class="arena-picker-actions">
        <button class="btn ghost" onclick="closeModal()">Huỷ</button>
        <button class="btn primary" id="aq-submit" disabled>${ic("bolt")} Tấn công! (0/${questions.length})</button>
      </div>
    </div>`);

  const updateSubmit = () => {
    const answered = answers.filter((a) => a !== null).length;
    const btn = $("#aq-submit", m);
    btn.disabled = answered < questions.length;
    btn.innerHTML = `${ic("bolt")} Tấn công! (${answered}/${questions.length})`;
  };

  $$(".aq-question", m).forEach((qEl, i) => {
    $$(".q-option", qEl).forEach((btn) => btn.addEventListener("click", () => {
      $$(".q-option", qEl).forEach((b) => b.classList.remove("picked"));
      btn.classList.add("picked");
      answers[i] = { word_id: questions[i].word_id, mode: questions[i].mode, selected: btn.dataset.v };
      updateSubmit();
    }));
  });

  $("#aq-submit", m).addEventListener("click", () => busy($("#aq-submit", m), async () => {
    const res = await api(`/api/arena/attack/${defenderId}/resolve`, { method: "POST", body: { answers } });
    showBattleResult(res, defenderName);
  }));
}

function showBattleResult(res, defenderName) {
  const win = res.result === "win";
  SFX.play(win ? "ok" : "err");
  const reviewHTML = res.reviewed.map((r) => `
    <div class="aq-review ${r.is_correct ? "correct" : "wrong"}">
      ${r.is_correct ? ic("check-circle") : ic("x-circle")} <b>${esc(r.term)}</b> — ${esc(r.meaning)}
    </div>`).join("");
  modal(`
    <div class="battle-result ${win ? "win" : "loss"}">
      <div class="br-banner">${win ? "CHIẾN THẮNG!" : "THẤT BẠI"}</div>
      <div class="br-vs">
        <div class="br-side"><div class="br-label">Bạn</div><div class="br-power">${res.attacker_power}</div></div>
        <div class="br-x">VS</div>
        <div class="br-side"><div class="br-label">${esc(defenderName)}</div><div class="br-power">${res.defender_power}</div></div>
      </div>
      <div class="br-detail">Quiz đúng ${res.quiz_correct}/${res.quiz_total} · sức mạnh gốc ${res.base_attacker_power} → ${res.attacker_power} sau bonus</div>
      <div class="mt">${reviewHTML}</div>
      <div class="br-rating">Điểm xếp hạng: ${res.attacker_delta >= 0 ? "+" : ""}${res.attacker_delta}</div>
      ${res.pack_tier ? `<div class="br-reward">${ic("gift")} Nhận được ${PACK_NAMES[res.pack_tier]}! Vào Bộ sưu tập để mở.</div>` : ""}
      <div class="rv-actions"><button class="btn primary" onclick="closeModal(); show('arena');">Xong</button></div>
    </div>`);
}

views.arena = async () => {
  const [status, opponentsRes, historyRes] = await Promise.all([
    api("/api/arena/status"),
    api("/api/arena/opponents"),
    api("/api/arena/history"),
  ]);
  const maxCards = status.max_cards;
  const defenseHTML = status.defense.length
    ? `<div class="cards-grid arena-grid-sm">${status.defense.map((c) => cardHTML(c)).join("")}</div>`
    : `<div class="empty" style="padding:12px;">Chưa xếp đội hình — bấm "Xếp đội hình" để chọn thẻ.</div>`;
  const oppRows = opponentsRes.opponents.length
    ? opponentsRes.opponents.map((o) => opponentRowHTML(o)).join("")
    : `<div class="empty" style="padding:12px;">Chưa có đối thủ nào xếp đội hình — rủ bạn bè cùng chơi EPux nhé!</div>`;
  const histRows = historyRes.battles.length
    ? historyRes.battles.map((b) => battleRowHTML(b)).join("")
    : `<div class="empty" style="padding:12px;">Chưa có trận đấu nào.</div>`;

  main.innerHTML = `
    <div class="page-title">Đấu Trường</div>
    <div class="page-sub">Xếp đội hình từ thẻ bài sở hữu để phòng thủ — người khác có thể tấn công đội hình này bất kỳ lúc nào. Muốn tấn công, trả lời đúng quiz về thẻ của đối thủ để cộng thêm sức mạnh.</div>
    <div class="tiles mb">
      <div class="tile"><div class="t-label">${ic("flame")} Điểm xếp hạng</div><div class="t-value"><span data-countup="${status.rating}">0</span></div></div>
      <div class="tile"><div class="t-label">${ic("check-circle")} Thắng</div><div class="t-value"><span data-countup="${status.wins}">0</span></div></div>
      <div class="tile"><div class="t-label">${ic("x-circle")} Thua</div><div class="t-value"><span data-countup="${status.losses}">0</span></div></div>
      <div class="tile"><div class="t-label">${ic("bolt")} Sức mạnh đội hình</div><div class="t-value"><span data-countup="${status.power}">0</span></div></div>
    </div>
    <div class="card mb">
      <div class="row" style="justify-content: space-between; align-items:center;">
        <b>${ic("cards")} Đội hình phòng thủ (tối đa ${maxCards} thẻ)</b>
        <button class="btn primary" id="arena-edit-defense">${ic("sliders")} Xếp đội hình</button>
      </div>
      <div class="mt">${defenseHTML}</div>
    </div>
    <div class="card mb">
      <b>${ic("target")} Đối thủ</b>
      <div class="mt arena-opponents">${oppRows}</div>
    </div>
    <div class="card">
      <b>${ic("list")} Lịch sử đấu gần đây</b>
      <div class="mt arena-history">${histRows}</div>
    </div>`;

  $("#arena-edit-defense").addEventListener("click", async () => {
    const col = await api("/api/collection");
    openDefensePicker(status.defense.map((c) => c.id), col.cards, maxCards);
  });
  $$(".arena-attack-btn").forEach((btn) => btn.addEventListener("click", () => {
    if (!status.defense.length) { toast("Xếp đội hình phòng thủ trước khi đi tấn công nhé!", "err"); return; }
    startAttack(Number(btn.dataset.id), btn.dataset.name);
  }));
};

/* ---------------- stats ---------------- */

views.stats = async () => {
  const data = await api("/api/stats");
  const s = data.stats;
  main.innerHTML = `
    <div class="page-title">Thống kê</div>
    <div class="page-sub">Trí nhớ và độ rộng vốn từ của bạn, nhìn bằng số liệu.</div>
    <div class="tiles mb">
      <div class="tile"><div class="t-label">${ic("book")} Tổng số từ</div><div class="t-value"><span data-countup="${s.total_words}">0</span></div></div>
      <div class="tile"><div class="t-label">${ic("check-circle")} Đã nhớ chắc</div><div class="t-value"><span data-countup="${s.mastered}">0</span></div><div class="t-sub">interval ≥ 21 ngày</div></div>
      <div class="tile"><div class="t-label">${ic("refresh")} Tổng lượt ôn</div><div class="t-value"><span data-countup="${s.reviews}">0</span></div></div>
      <div class="tile"><div class="t-label">${ic("quill")} Bài viết</div><div class="t-value"><span data-countup="${s.writings}">0</span></div></div>
      <div class="tile"><div class="t-label">${ic("target")} Band gần đây</div><div class="t-value">${s.recent_avg_band ?? "–"}</div><div class="t-sub">TB 5 bài mới nhất</div></div>
      <div class="tile"><div class="t-label">${ic("flame")} Streak</div><div class="t-value"><span data-countup="${s.streak}">0</span> <small>ngày</small></div></div>
    </div>
    <div class="card viz-root">
      <b>Hoạt động 14 ngày</b>
      <div class="chart-box mt" id="chart"></div>
      <div class="legend">
        <span class="lg"><span class="sw" style="background: var(--series-1);"></span> Lượt ôn</span>
        <span class="lg"><span class="sw" style="background: var(--series-2);"></span> Từ mới</span>
        <span class="lg"><span class="sw" style="background: var(--series-3);"></span> Bài viết</span>
        <button class="btn ghost" id="tbl-toggle" style="margin-left: auto; font-size: 0.75rem; padding: 2px 10px;">Xem bảng</button>
      </div>
      <div id="tbl" hidden></div>
    </div>`;
  renderActivityChart($("#chart"), data.activity);
  $("#tbl-toggle").addEventListener("click", () => {
    const tbl = $("#tbl");
    tbl.hidden = !tbl.hidden;
    if (!tbl.hidden && !tbl.innerHTML) {
      tbl.innerHTML = `<table class="datatable">
        <tr><th>Ngày</th><th>Lượt ôn</th><th>Từ mới</th><th>Bài viết</th></tr>
        ${data.activity.map((d) => `<tr><td>${fmtDay(d.date)}</td><td>${d.reviews}</td><td>${d.new_words}</td><td>${d.writings}</td></tr>`).join("")}
      </table>`;
    }
  });
};

function renderActivityChart(container, days) {
  const W = 720, H = 230, padL = 34, padR = 6, padT = 12, padB = 26;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const series = ["reviews", "new_words", "writings"];
  const colors = ["var(--series-1)", "var(--series-2)", "var(--series-3)"];
  const maxTotal = Math.max(5, ...days.map((d) => d.reviews + d.new_words + d.writings));
  const barW = Math.min(30, (plotW / days.length) * 0.6);
  const step = plotW / days.length;
  const y = (v) => padT + plotH - (v / maxTotal) * plotH;

  let grid = "";
  const ticks = 4;
  for (let i = 0; i <= ticks; i++) {
    const val = Math.round((maxTotal / ticks) * i);
    const yy = y(val);
    grid += `<line x1="${padL}" y1="${yy}" x2="${W - padR}" y2="${yy}" stroke="var(--grid)" stroke-width="1"/>
             <text x="${padL - 6}" y="${yy + 3.5}" text-anchor="end" font-size="10" fill="var(--muted)">${val}</text>`;
  }

  let bars = "", hover = "";
  days.forEach((d, i) => {
    const cx = padL + step * i + step / 2;
    const x = cx - barW / 2;
    let acc = 0;
    const vals = series.map((k) => d[k]);
    const total = vals.reduce((a, b) => a + b, 0);
    const topIdx = vals.map((v, j) => (v > 0 ? j : -1)).filter((j) => j >= 0).pop();
    vals.forEach((v, j) => {
      if (!v) return;
      const y1 = y(acc + v), y0 = y(acc);
      let h = y0 - y1;
      let yTop = y1;
      if (j !== topIdx && h > 3) h -= 2; // 2px surface gap between stacked segments
      if (j === topIdx && h > 4) {
        bars += `<path d="M${x},${yTop + h} L${x},${yTop + 3} Q${x},${yTop} ${x + 3},${yTop} L${x + barW - 3},${yTop} Q${x + barW},${yTop} ${x + barW},${yTop + 3} L${x + barW},${yTop + h} Z" fill="${colors[j]}"/>`;
      } else {
        bars += `<rect x="${x}" y="${yTop}" width="${barW}" height="${Math.max(h, 1.5)}" fill="${colors[j]}"/>`;
      }
      acc += v;
    });
    if (i % 2 === 0) {
      bars += `<text x="${cx}" y="${H - 8}" text-anchor="middle" font-size="10" fill="var(--muted)">${fmtDay(d.date)}</text>`;
    }
    hover += `<rect x="${padL + step * i}" y="${padT}" width="${step}" height="${plotH}" fill="transparent"
      data-i="${i}" data-total="${total}" class="hover-col"/>`;
  });

  container.innerHTML = `
    <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Hoạt động học 14 ngày">
      ${grid}
      <line x1="${padL}" y1="${padT + plotH}" x2="${W - padR}" y2="${padT + plotH}" stroke="var(--surface-3)" stroke-width="1"/>
      ${bars}
      ${hover}
    </svg>`;

  let tip = null;
  container.addEventListener("mousemove", (e) => {
    const col = e.target.closest(".hover-col");
    if (!col) { tip?.remove(); tip = null; return; }
    const d = days[Number(col.dataset.i)];
    if (!tip) { tip = document.createElement("div"); tip.className = "viz-tooltip"; document.body.appendChild(tip); }
    tip.innerHTML = `<b>${fmtDay(d.date)}</b><br>Lượt ôn: ${d.reviews}<br>Từ mới: ${d.new_words}<br>Bài viết: ${d.writings}`;
    tip.style.left = `${Math.min(e.clientX + 14, window.innerWidth - 160)}px`;
    tip.style.top = `${e.clientY - 10}px`;
  });
  container.addEventListener("mouseleave", () => { tip?.remove(); tip = null; });
}

/* ---------------- settings ---------------- */

views.settings = async () => {
  const data = await api("/api/config");
  const c = data.config;
  const llm = data.llm;
  main.innerHTML = `
    <div class="page-title">Cài đặt</div>
    <div class="page-sub">Cấu hình học tập và kết nối LLM.</div>
    <div class="card mb">
      <b>${ic("sparkle")} LLM</b>
      <div class="mt" style="font-size: 0.9rem; line-height: 1.8;">
        Trạng thái: ${llm.configured ? `<span style="color: var(--good);">● đã cấu hình</span>` : `<span style="color: var(--bad);">● chưa cấu hình (.env)</span>`}<br>
        Provider: <code>${esc(llm.provider || "—")}</code> · Model: <code>${esc(llm.model || "—")}</code><br>
        Endpoint: <code style="font-size: 0.78rem;">${esc(llm.endpoint || "—")}</code>
      </div>
      <button class="btn mt" id="llm-test" ${llm.configured ? "" : "disabled"}>${ic("plug")} Test kết nối</button>
      <span id="llm-test-result" style="margin-left: 10px; font-size: 0.85rem;"></span>
    </div>
    <div class="card">
      <b>${ic("book")} Học tập</b>
      <div class="row mt">
        <div style="width: 180px;">
          <label class="field">Trình độ hiện tại</label>
          <select id="cf-level">
            ${["A2", "B1", "B2", "C1"].map((l) => `<option ${c.level === l ? "selected" : ""}>${l}</option>`).join("")}
          </select>
        </div>
        <div style="width: 180px;">
          <label class="field">Band IELTS mục tiêu</label>
          <select id="cf-band">
            ${["5.5", "6.0", "6.5", "7.0", "7.5", "8.0"].map((b) => `<option ${c.target_band === b ? "selected" : ""}>${b}</option>`).join("")}
          </select>
        </div>
        <div style="width: 180px;">
          <label class="field">Từ mới mỗi ngày</label>
          <input type="number" id="cf-daily" value="${c.daily_new_words}" min="1" max="30">
        </div>
      </div>
      <div class="row mt">
        <div style="width: 180px;">
          <label class="field">Nhắc học mỗi (phút)</label>
          <input type="number" id="cf-remind" value="${c.reminder_minutes}" min="10" max="480">
        </div>
        <div style="width: 180px;">
          <label class="field">Im lặng từ</label>
          <input type="text" id="cf-qs" value="${esc(c.notify_quiet_start)}">
        </div>
        <div style="width: 180px;">
          <label class="field">đến</label>
          <input type="text" id="cf-qe" value="${esc(c.notify_quiet_end)}">
        </div>
      </div>
      <div style="color: var(--muted); font-size: 0.8rem; margin-top: 10px;">
        Nhắc học chạy bằng lệnh <code>epux remind --daemon</code> (xem README) — càng nhiều thẻ đến hạn nhắc càng dày.
      </div>
      <button class="btn primary mt" id="cf-save">${ic("check-circle")} Lưu cài đặt</button>
    </div>`;

  $("#llm-test").addEventListener("click", () => busy($("#llm-test"), async () => {
    const res = await api("/api/llm/test", { method: "POST" });
    $("#llm-test-result").innerHTML = res.ok
      ? `<span style="color: var(--good);">✓ LLM phản hồi OK</span>`
      : `<span style="color: var(--bad);">✗ ${esc(res.error)}</span>`;
  }));

  $("#cf-save").addEventListener("click", () => busy($("#cf-save"), async () => {
    await api("/api/config", {
      method: "PUT",
      body: {
        level: $("#cf-level").value,
        target_band: $("#cf-band").value,
        daily_new_words: Number($("#cf-daily").value),
        reminder_minutes: Number($("#cf-remind").value),
        notify_quiet_start: $("#cf-qs").value,
        notify_quiet_end: $("#cf-qe").value,
      },
    });
    toast("Đã lưu cài đặt.", "ok");
  }));
};

/* ---------------- boot ---------------- */

/* ---- hiệu ứng con trỏ kiểu ReactBits: spotlight + tilt 3D ---- */

document.addEventListener("mousemove", (e) => {
  const tcg = e.target.closest(".tcg");
  if (tcg && !tcg.closest(".reveal-stage")) {
    const r = tcg.getBoundingClientRect();
    const px = (e.clientX - r.left) / r.width - 0.5;
    const py = (e.clientY - r.top) / r.height - 0.5;
    tcg.style.transform = `perspective(700px) rotateY(${(px * 14).toFixed(2)}deg) rotateX(${(-py * 12).toFixed(2)}deg) translateY(-4px)`;
  }
});

document.addEventListener("mouseout", (e) => {
  const tcg = e.target.closest(".tcg");
  if (tcg && !(e.relatedTarget && tcg.contains(e.relatedTarget))) {
    tcg.style.transform = "";
  }
});

/* ---- count-up cho số liệu (kiểu ReactBits CountUp) ---- */

function runCountUps(root = document) {
  $$("[data-countup]", root).forEach((el) => {
    const target = Number(el.dataset.countup);
    delete el.dataset.countup; // chỉ chạy một lần
    if (!Number.isFinite(target)) return;
    const dur = 900;
    const t0 = performance.now();
    const tick = (t) => {
      const k = Math.min(1, (t - t0) / dur);
      el.textContent = Math.round(target * (1 - Math.pow(1 - k, 3)));
      if (k < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });
}

window.show = show;
window.closeModal = closeModal;

// nút bật/tắt âm thanh (trạng thái lưu localStorage)
const sfxBtn = $("#sfx-toggle");
const syncSfxBtn = () => { sfxBtn.innerHTML = SFX.enabled ? `${ic("speaker")} Âm thanh` : `${ic("speaker-off")} Đã tắt tiếng`; };
sfxBtn.addEventListener("click", () => { SFX.toggle(); syncSfxBtn(); });
syncSfxBtn();

window.addEventListener("hashchange", () => {
  const name = location.hash.slice(1);
  if (name !== currentView) show(name);
});
show(location.hash.slice(1) || "dashboard");
refreshDueBadge();
setInterval(refreshDueBadge, 90000);
