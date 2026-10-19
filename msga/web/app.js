"use strict";
/* Make Sound Great Again: واجهة المتصفح / النافذة. بدون أي مكتبات خارجية (خفيفة). */

// ---------- النصوص: [عربي, English] ----------
const T = {
  subtitle: ["حسّن جودة أي أغنية من رابط أو ملف", "Improve any song from a link or a file"],
  url_placeholder: ["الصق رابط يوتيوب أو تيكتوك أو انستا… (رابط في كل سطر)", "Paste a YouTube, TikTok or Instagram link… (one per line)"],
  drop_title: ["اسحب ملفات الأغاني هنا", "Drop song files here"],
  drop_sub: ["أو اضغط للاختيار من جهازك", "or click to choose from your computer"],
  files_selected: ["{n} ملف مختار", "{n} file(s) selected"],
  clear_files: ["إزالة الملفات المختارة", "Remove selected files"],
  preset: ["النمط", "Preset"], format: ["الصيغة", "Format"], jobs: ["ملفات بنفس الوقت", "Parallel jobs"],
  playlist: ["الرابط قائمة تشغيل", "Link is a playlist"],
  save_defaults: ["حفظ كإعدادات افتراضية", "Save as defaults"],
  saved: ["تم الحفظ ✓", "Saved ✓"],
  go: ["حسّن الجودة", "Enhance quality"],
  uploading: ["جاري رفع الملفات… {i}/{n}", "Uploading files… {i}/{n}"],
  need_input: ["حط رابط أو اختر ملف.", "Add a link or choose a file."],
  results: ["النتائج", "Results"],
  open_folder: ["فتح مجلد الحفظ", "Open output folder"],
  clean_old: ["حذف القديم…", "Delete old…"],
  clean_prompt: ["احذف ملفات مجلد الحفظ الأقدم من كم يوم؟", "Delete files in the output folder older than how many days?"],
  deleted: ["تم حذف {n} ملف", "Deleted {n} file(s)"],
  clear_list: ["مسح القائمة", "Clear list"],
  empty: ["ما فيه أغاني بعد", "No songs yet"],
  out_prefix: ["الملفات تنحفظ في: ", "Files are saved to: "],
  q_low: ["جودة منخفضة", "Low quality"], q_mid: ["جودة متوسطة", "Medium quality"], q_high: ["جودة عالية", "High quality"],
  p_auto: ["تلقائي (يكتشف جودة الأغنية)", "Automatic (detects song quality)"],
  p_gentle: ["خفيف جدًا", "Very gentle"], p_natural: ["طبيعي", "Natural"],
  p_clean: ["تنظيف (تيكتوك / انستا)", "Clean-up (TikTok / Instagram)"],
  p_bass: ["بيس أقوى", "More bass"], p_vocal: ["صوت المغني أوضح", "Clearer vocals"],
  source: ["المصدر", "Source"], preset_used: ["النمط", "Preset"], auto_tag: [" (تلقائي)", " (auto)"],
  loudness: ["مستوى الصوت", "Loudness"], peak: ["الذروة", "Peak"],
  original: ["الأصلي", "Original"], enhanced: ["المحسّن", "Enhanced"],
  fair_ab: ["المقارنة بنفس مستوى الصوت", "Compared at equal loudness"],
  download: ["تحميل", "Download"],
  waiting: ["بالانتظار", "Waiting"], failed: ["فشل", "Failed"], reading_playlist: ["قراءة القائمة", "Reading playlist"],
  settings: ["الإعدادات", "Settings"], back: ["رجوع", "Back"],
  language: ["اللغة", "Language"], appearance: ["المظهر", "Appearance"],
  th_system: ["النظام", "System"], th_light: ["فاتح", "Light"], th_dark: ["داكن", "Dark"],
  light_mode: ["الوضع الخفيف", "Light mode"],
  light_hint: ["يشغّل المعالجة بأولوية منخفضة عشان الجهاز يبقى سريع", "Runs processing at low priority so your computer stays responsive"],
  out_folder: ["مجلد الحفظ", "Output folder"], save: ["حفظ", "Save"],
  ar_font: ["الخط العربي", "Arabic font"],
  font_ok: ["خط ثمانية مثبّت ومستخدم", "Thmanyah font is installed and in use"],
  font_missing: ["خط ثمانية غير مثبّت: نزّله من موقع ثمانية الرسمي وثبّته في نظامك (يُستخدم تلقائيًا). حاليًا يُستخدم خط بديل.",
                 "Thmanyah font isn't installed: download it from Thmanyah's official site and install it on your system (it's picked up automatically). A fallback font is used for now."],
  about: ["عن البرنامج", "About"],
  version: ["الإصدار", "Version"],
  updates: ["التحديثات", "Updates"],
  check_updates: ["تحقق من التحديثات", "Check for updates"],
  checking: ["جاري التحقق…", "Checking…"],
  up_to_date: ["أنت على آخر إصدار ✓", "You're up to date ✓"],
  update_available: ["يوجد إصدار جديد: {v}", "A new version is available: {v}"],
  update_to: ["حدّث إلى {v}", "Update to {v}"],
  updating: ["جاري التحديث…", "Updating…"],
  updated: ["تم التحديث. أعد التشغيل لتطبيقه.", "Updated. Restart to apply it."],
  restart: ["إعادة التشغيل", "Restart"],
  upd_err_no_repo: ["مستودع GitHub غير محدد في version.py", "GitHub repository isn't set in version.py"],
  upd_err_network: ["تعذّر الاتصال بـ GitHub", "Couldn't reach GitHub"],
  upd_err_git: ["فشل git pull", "git pull failed"],
  upd_err_bad_archive: ["ملف التحديث غير صالح", "The update archive is invalid"],
  engine: ["محرك التنزيل (yt-dlp)", "Download engine (yt-dlp)"],
  update_engine: ["تحديث المحرك", "Update engine"],
  engine_updated: ["تم: {a}", "Done: {a}"],
  engine_failed: ["فشل التحديث", "Update failed"],
  quit: ["إغلاق البرنامج", "Quit the app"],
  missing_tools: ["ناقص: {tools}. ثبّته أولًا:", "Missing: {tools}. Install it first:"],
  unexpected: ["خطأ غير متوقع: {e}", "Unexpected error: {e}"],
};
let MSG = {}; // رسائل المحرك (مراحل / أخطاء / أسباب) من الخادم

const $ = id => document.getElementById(id);
const S = { cfg: null, lang: "ar", files: [], cards: {}, state: null, view: "main", updAvailable: null };
const t = (k, p = {}) => fmt((T[k] || [k, k])[S.lang === "en" ? 1 : 0], p);
const fmt = (s, p) => s.replace(/\{(\w+)\}/g, (_, k) => (p[k] === undefined ? "" : p[k]));
const msg = (k, p) => MSG[k] ? fmt(MSG[k][S.lang === "en" ? 1 : 0], p || {}) : k;
const f1 = v => (v === null || v === undefined || isNaN(v)) ? "؟" : (+v).toFixed(1);

async function api(path, body) {
  const r = await fetch(path, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  return r.json();
}

// ---------- اللغة والمظهر ----------
function applyLang() {
  const html = document.documentElement;
  html.lang = S.lang; html.dir = S.lang === "ar" ? "rtl" : "ltr";
  document.querySelectorAll("[data-i18n]").forEach(el => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll("[data-i18n-ph]").forEach(el => { el.placeholder = t(el.dataset.i18nPh); });
  // قائمة الأنماط
  const cur = $("preset").value || (S.cfg && S.cfg.preset) || "auto";
  $("preset").innerHTML = ["auto", "gentle", "natural", "clean", "bass", "vocal"].map(k => `<option value="${k}">${t("p_" + k)}</option>`).join("");
  $("preset").value = cur;
  $("back").textContent = (S.lang === "ar" ? t("back") + "  ›" : "‹  " + t("back"));
  setFiles(S.files);
  showOut();
  fillAbout();
  for (const id in S.cards) refreshCard(id);
  if (S.state) renderBanner(S.state);
}
function applyTheme() {
  const th = S.cfg.theme;
  if (th === "light" || th === "dark") document.documentElement.dataset.theme = th;
  else delete document.documentElement.dataset.theme;
}
function setSeg(id, value) { document.querySelectorAll(`#${id} button`).forEach(b => b.classList.toggle("on", b.dataset.v === value)); }
function bindSeg(id, onPick) {
  document.querySelectorAll(`#${id} button`).forEach(b => b.addEventListener("click", () => { setSeg(id, b.dataset.v); onPick(b.dataset.v); }));
}
async function saveCfg(patch) {
  const r = await api("/api/config", patch);
  S.cfg = r.config;
  return S.cfg;
}
function showOut() { if (S.cfg) $("outInfo").textContent = t("out_prefix") + S.cfg.out; }

// ---------- الملفات ----------
function setFiles(files) {
  S.files = files;
  $("dropTitle").textContent = files.length ? t("files_selected", { n: files.length }) : t("drop_title");
  const names = files.map(f => f.name).join("، ");
  $("dropSub").textContent = files.length ? (names.length > 90 ? names.slice(0, 90) + "…" : names) : t("drop_sub");
  $("clearFiles").hidden = !files.length;
  $("clearFiles").textContent = t("clear_files");
}
$("drop").addEventListener("click", () => $("files").click());
$("drop").addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") $("files").click(); });
$("files").addEventListener("change", e => setFiles([...e.target.files]));
$("clearFiles").addEventListener("click", () => { $("files").value = ""; setFiles([]); });
["dragenter", "dragover"].forEach(ev => $("drop").addEventListener(ev, e => { e.preventDefault(); $("drop").classList.add("over"); }));
["dragleave", "drop"].forEach(ev => $("drop").addEventListener(ev, e => { e.preventDefault(); $("drop").classList.remove("over"); }));
$("drop").addEventListener("drop", e => setFiles([...e.dataTransfer.files]));

// ---------- الإعدادات السريعة ----------
let jobs = 1;
const setJobs = v => { jobs = Math.max(1, Math.min(8, v)); $("jobsVal").textContent = jobs; };
$("jobsMinus").onclick = () => setJobs(jobs - 1);
$("jobsPlus").onclick = () => setJobs(jobs + 1);
bindSeg("format", () => { });
$("saveDefaults").onclick = async () => {
  await saveCfg({ preset: $("preset").value, format: document.querySelector("#format .on").dataset.v, jobs });
  $("saveDefaults").textContent = t("saved");
  setTimeout(() => { $("saveDefaults").textContent = t("save_defaults"); }, 1500);
};

// ---------- إرسال ----------
$("go").onclick = async () => {
  $("formErr").textContent = "";
  const urls = $("urls").value.split(/\s+/).filter(u => /^https?:\/\//.test(u));
  if (!urls.length && !S.files.length) { $("formErr").textContent = t("need_input"); return; }
  const preset = $("preset").value, format = document.querySelector("#format .on").dataset.v;
  if (jobs !== S.cfg.jobs) await saveCfg({ jobs });
  $("go").disabled = true;
  try {
    if (urls.length) await api("/api/submit", { urls, preset, format, playlist: $("playlist").checked });
    for (let i = 0; i < S.files.length; i++) {
      $("formErr").textContent = t("uploading", { i: i + 1, n: S.files.length });
      const f = S.files[i];
      await fetch(`/api/upload?name=${encodeURIComponent(f.name)}&preset=${preset}&format=${format}`, { method: "POST", body: f });
    }
    $("formErr").textContent = "";
    $("urls").value = ""; $("files").value = ""; setFiles([]);
    poll();
  } catch (e) { $("formErr").textContent = t("unexpected", { e: e.message }); }
  $("go").disabled = false;
};
$("clearList").onclick = async () => { await api("/api/clear", {}); poll(); };
$("openFolder").onclick = () => api("/api/open", {});
$("cleanOld").onclick = async () => {
  const d = prompt(t("clean_prompt"), "30");
  if (d === null) return;
  const r = await api("/api/clean", { days: +d });
  $("outInfo").textContent = t("deleted", { n: r.deleted });
};

// ---------- بطاقات الأغاني ----------
function stageText(k) { return k in MSG ? msg(k) : t(k || "waiting"); }
function errText(e) { return !e ? "" : (e.key ? msg(e.key, e.params) : t("unexpected", { e: e.text })); }

function makeCard(it) {
  const el = document.createElement("section");
  el.className = "card song";
  el.innerHTML = `<div class="top"><div class="name"></div><span class="badge" hidden></span></div>
    <div class="stage sub"></div><div class="bar-track"><i></i></div><div class="err"></div><div class="res"></div>`;
  $("list").prepend(el);
  return S.cards[it.id] = { el, it, done: false, name: el.querySelector(".name"), badge: el.querySelector(".badge"),
    stage: el.querySelector(".stage"), track: el.querySelector(".bar-track"), bar: el.querySelector(".bar-track i"),
    err: el.querySelector(".err"), res: el.querySelector(".res") };
}
function refreshCard(id) {
  const c = S.cards[id]; if (!c) return; const it = c.it;
  c.name.textContent = (it.result && it.result.title) || it.label;
  const done = it.status === "done", error = it.status === "error";
  c.track.hidden = c.stage.hidden = done;
  c.bar.style.width = it.pct + "%";
  c.track.classList.toggle("fail", error);
  c.stage.textContent = error ? t("failed") : it.status === "waiting" ? t("waiting") : `${stageText(it.stage_key)} · ${it.pct}%`;
  c.err.textContent = error ? errText(it.error) : "";
  if (done) { renderResult(c); }
}
function renderResult(c) {
  const r = c.it.result;
  const wasPlaying = c.audio ? { t: c.audio.currentTime, paused: c.audio.paused, w: c.which } : null;
  c.badge.hidden = false; c.badge.className = "badge q-" + r.quality; c.badge.textContent = t("q_" + r.quality);
  const used = t("p_" + r.preset).replace(/ \(.*\)$/, "") + (r.auto ? t("auto_tag") : "");
  const src = r.codec + (r.bitrate_kbps ? " " + r.bitrate_kbps + "kbps" : "");
  c.res.innerHTML = `<div class="meta"></div>
    ${r.original_url ? `<div class="ab"><button class="tint" data-w="o"></button><button class="tint" data-w="e"></button><span class="sub"></span></div>` : ""}
    <audio controls preload="metadata"></audio><a class="dl" download></a>`;
  c.res.querySelector(".meta").textContent =
    `${msg(r.reason_key, r.reason_params)}\n${t("source")}: ${src}  ·  ${t("preset_used")}: ${used}\n` +
    `${t("loudness")}: ${f1(r.lufs_before)} ← ${f1(r.lufs_after)} LUFS  ·  ${t("peak")}: ${f1(r.tp_before)} ← ${f1(r.tp_after)} dBTP`;
  const dl = c.res.querySelector(".dl"); dl.href = r.output_url; dl.textContent = `⬇ ${t("download")} ${r.output_name}`;
  const audio = c.audio = c.res.querySelector("audio");
  const known = [r.lufs_before, r.lufs_after].filter(v => v !== null && v !== undefined);
  const target = known.length ? Math.min(...known) : null;
  const vol = l => (l === null || l === undefined || target === null) ? 1 : Math.min(1, Math.pow(10, (target - l) / 20));
  const sets = { e: [r.output_url, vol(r.lufs_after)], o: [r.original_url, vol(r.lufs_before)] };
  const pick = (w, keep) => {
    c.which = w; audio.src = sets[w][0]; audio.volume = sets[w][1];
    if (keep) audio.addEventListener("loadedmetadata", () => { audio.currentTime = keep.t; if (!keep.paused) audio.play(); }, { once: true });
    c.res.querySelectorAll(".ab button").forEach(b => { b.style.outline = b.dataset.w === w ? "2px solid var(--blue)" : "none"; });
  };
  const ab = c.res.querySelector(".ab");
  if (ab) {
    ab.querySelector('[data-w="o"]').textContent = "▶ " + t("original");
    ab.querySelector('[data-w="e"]').textContent = "▶ " + t("enhanced");
    ab.querySelector(".sub").textContent = t("fair_ab");
    ab.querySelectorAll("button").forEach(b => b.onclick = () => pick(b.dataset.w, { t: audio.currentTime, paused: audio.paused }));
  }
  pick(wasPlaying ? wasPlaying.w : "e", wasPlaying);
  c.done = true;
}
function render(items) {
  const ids = new Set(items.map(i => i.id));
  for (const id in S.cards) if (!ids.has(id)) { S.cards[id].el.remove(); delete S.cards[id]; }
  for (const it of items) {
    const c = S.cards[it.id] || makeCard(it);
    const wasDone = c.done;
    c.it = it;
    if (it.status === "done" && wasDone) continue; // ما نعيد بناء المشغّل أثناء التشغيل
    refreshCard(it.id);
  }
  $("empty").hidden = items.length > 0;
}

// ---------- تنبيه الأدوات الناقصة ----------
function renderBanner(s) {
  const b = $("banner");
  if (!s.missing.length) { b.hidden = true; return; }
  const hint = s.platform === "win32" ? "winget install ffmpeg" : s.platform === "darwin" ? "brew install ffmpeg" : "sudo apt install ffmpeg";
  const hasFF = s.missing.some(m => m.startsWith("ff"));
  const cmds = [hasFF ? hint : null, s.missing.includes("yt-dlp") ? "pip install yt-dlp" : null].filter(Boolean);
  b.innerHTML = "";
  const p = document.createElement("div"); p.textContent = t("missing_tools", { tools: s.missing.join(", ") }); b.append(p);
  cmds.forEach(c => { const code = document.createElement("code"); code.textContent = c; b.append(code, " "); });
  b.hidden = false;
}

// ---------- الإعدادات: صفحة ----------
function show(view) {
  S.view = view;
  $("main").hidden = view !== "main"; $("settings").hidden = view !== "settings";
  $("gear").hidden = view === "settings";
  window.scrollTo(0, 0);
  if (view === "settings") loadSettings();
}
$("gear").onclick = () => show("settings");
$("back").onclick = () => show("main");

function fillAbout() {
  if (!S.state) return;
  $("aboutLine").textContent = `${S.state.app} · ${t("version")} ${S.state.version}`;
  $("fontStatus").textContent = S.state.thmanyah ? t("font_ok") : t("font_missing");
  const link = $("repoLink"); link.hidden = !S.state.repo_url; if (S.state.repo_url) link.href = S.state.repo_url;
  $("quit").hidden = S.state.mode !== "browser";
}
async function loadSettings() {
  setSeg("langSeg", S.lang); setSeg("themeSeg", S.cfg.theme);
  $("lightMode").checked = S.cfg.light; $("outPath").value = S.cfg.out;
  fillAbout();
  const v = await api("/api/ytdlp/version", {});
  $("engStatus").textContent = v.version ? "yt-dlp " + v.version : "—";
}
bindSeg("langSeg", async v => { S.lang = v; await saveCfg({ lang: v }); applyLang(); loadSettings(); });
bindSeg("themeSeg", async v => { await saveCfg({ theme: v }); applyTheme(); });
$("lightMode").onchange = e => saveCfg({ light: e.target.checked });
$("outSave").onclick = async () => { await saveCfg({ out: $("outPath").value.trim() }); showOut(); $("outSave").textContent = t("saved"); setTimeout(() => { $("outSave").textContent = t("save"); }, 1500); };

// ---------- التحديثات ----------
function updError(r) { return t("upd_err_" + r.error) + (r.detail ? ` (${r.detail})` : ""); }
$("updCheck").onclick = async () => {
  $("updStatus").textContent = t("checking"); $("updRow").hidden = true;
  const r = await api("/api/update/check", {});
  if (r.error) { $("updStatus").textContent = updError(r); return; }
  if (!r.available) { $("updStatus").textContent = t("up_to_date") + `  (v${r.current})`; return; }
  $("updStatus").textContent = t("update_available", { v: r.latest });
  $("updRow").hidden = false; $("updTitle").textContent = `v${r.current} → v${r.latest}`;
  const ap = $("updApply"); ap.hidden = false; ap.textContent = t("update_to", { v: r.latest }); ap.disabled = false;
  $("updRestart").hidden = true;
};
$("updApply").onclick = async () => {
  const ap = $("updApply"); ap.disabled = true; ap.textContent = t("updating");
  const r = await api("/api/update/apply", {});
  if (!r.ok) { $("updStatus").textContent = updError(r); ap.disabled = false; ap.textContent = t("check_updates"); return; }
  $("updStatus").textContent = t("updated"); ap.hidden = true; $("updRestart").hidden = false;
};
$("updRestart").onclick = async () => {
  await api("/api/restart", {});
  const deadline = Date.now() + 20000;
  const wait = async () => {
    try { const r = await fetch("/api/ping"); if (r.ok && Date.now() > deadline - 17000) { location.reload(); return; } } catch (e) { /* السيرفر بيرجع */ }
    if (Date.now() < deadline) setTimeout(wait, 1000);
  };
  setTimeout(wait, 2500);
};
$("engUpdate").onclick = async () => {
  const b = $("engUpdate"); b.disabled = true; $("engStatus").textContent = t("updating");
  const r = await api("/api/update/ytdlp", {});
  b.disabled = false;
  $("engStatus").textContent = r.ok ? t("engine_updated", { a: "yt-dlp " + (r.after || "") }) : t("engine_failed") + (r.detail ? ` (${r.detail})` : "");
};
$("quit").onclick = async () => { await api("/api/quit", {}); document.body.innerHTML = ""; window.close(); };

// ---------- الدورة الرئيسية ----------
let timer = null;
async function poll() {
  clearTimeout(timer);
  let busy = false;
  try {
    const s = await api("/api/state");
    S.state = s;
    if (!S.cfg) {
      S.cfg = s.config; S.lang = s.config.lang;
      MSG = await (await fetch("/api/messages")).json();
      applyTheme(); setJobs(s.config.jobs); setSeg("format", s.config.format); $("preset").value = s.config.preset;
      applyLang();
    }
    renderBanner(s); render(s.items); fillAbout();
    busy = s.items.some(i => i.status === "waiting" || i.status === "running");
  } catch (e) { /* الخادم غير متاح مؤقتًا */ }
  // خفيف: نخفف الاستعلام لما الصفحة مخفية أو ما فيه شغل
  timer = setTimeout(poll, document.hidden ? 30000 : busy ? 1000 : 4000);
}
document.addEventListener("visibilitychange", () => { if (!document.hidden) poll(); });
poll();
