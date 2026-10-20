"use strict";
/* Make Sound Great Again: واجهة النافذة / المتصفح. بدون أي مكتبات خارجية (خفيفة). */

// ---------- النصوص: [عربي, English] ----------
const T = {
  subtitle: ["حسّن جودة أي أغنية من رابط أو ملف", "Improve any song from a link or a file"],
  url_placeholder: ["الصق رابط يوتيوب أو تيكتوك أو انستا… (رابط في كل سطر)", "Paste a YouTube, TikTok or Instagram link… (one per line)"],
  paste_link: ["📋 لصق رابط من الحافظة", "📋 Paste link from clipboard"],
  paste_hint: ["اضغط Ctrl+V داخل المربع", "Press Ctrl+V inside the box"],
  drop_title: ["اسحب ملفات الأغاني هنا", "Drop song files here"],
  drop_sub: ["أو اضغط للاختيار من جهازك", "or click to choose from your computer"],
  files_selected: ["{n} ملف مختار", "{n} file(s) selected"],
  clear_files: ["إزالة الملفات المختارة", "Remove selected files"],
  preset: ["النمط", "Preset"], format: ["الصيغة", "Format"], jobs: ["ملفات بنفس الوقت", "Parallel jobs"],
  playlist: ["الرابط قائمة تشغيل", "Link is a playlist"],
  fine_tune: ["ضبط دقيق للصوت", "Fine-tune the sound"],
  bass: ["البيس (dB)", "Bass (dB)"], treble: ["الحدّة / التريبل (dB)", "Treble (dB)"],
  save_defaults: ["حفظ كإعدادات افتراضية", "Save as defaults"],
  saved: ["تم الحفظ ✓", "Saved ✓"],
  go: ["حسّن الجودة", "Enhance quality"],
  uploading: ["جاري رفع الملفات… {i}/{n}", "Uploading files… {i}/{n}"],
  need_input: ["حط رابط أو اختر ملف.", "Add a link or choose a file."],
  results: ["النتائج", "Results"],
  open_folder: ["فتح مجلد الحفظ", "Open output folder"],
  clean_old: ["حذف القديم…", "Delete old…"],
  clean_prompt: ["احذف ملفات مجلد الحفظ الأقدم من (يوم):", "Delete files in the output folder older than (days):"],
  delete: ["احذف", "Delete"], cancel: ["إلغاء", "Cancel"],
  deleted: ["تم حذف {n} ملف", "Deleted {n} file(s)"],
  clear_list: ["مسح القائمة", "Clear list"],
  empty: ["ما فيه أغاني بعد", "No songs yet"],
  out_prefix: ["الملفات تنحفظ في: ", "Files are saved to: "],
  q_low: ["جودة منخفضة", "Low quality"], q_mid: ["جودة متوسطة", "Medium quality"], q_high: ["جودة عالية", "High quality"],
  p_auto: ["تلقائي (يكتشف جودة الأغنية)", "Automatic (detects song quality)"],
  p_gentle: ["خفيف جدًا", "Very gentle"], p_natural: ["طبيعي", "Natural"],
  p_clean: ["تنظيف (تيكتوك / انستا)", "Clean-up (TikTok / Instagram)"],
  p_bass: ["بيس أقوى", "More bass"], p_vocal: ["صوت المغني أوضح", "Clearer vocals"],
  f_flac: ["FLAC (بدون ضغط)", "FLAC (lossless)"], f_mp3: ["MP3 320", "MP3 320"], f_m4a: ["M4A (AAC 256)", "M4A (AAC 256)"],
  f_opus: ["Opus 192", "Opus 192"], f_wav: ["WAV (24-bit)", "WAV (24-bit)"],
  source: ["المصدر", "Source"], preset_used: ["النمط", "Preset"], auto_tag: [" (تلقائي)", " (auto)"],
  loudness: ["مستوى الصوت", "Loudness"], peak: ["الذروة", "Peak"],
  original: ["الأصلي", "Original"], enhanced: ["المحسّن", "Enhanced"],
  fair_ab: ["المقارنة بنفس مستوى الصوت", "Compared at equal loudness"],
  show_folder: ["إظهار في المجلد", "Show in folder"],
  cached_note: ["معالَجة سابقًا بنفس الإعدادات", "Already processed with the same settings"],
  rerun: ["جرّب نمطًا ثانيًا", "Try another preset"], rerun_go: ["أعد المعالجة", "Re-run"],
  spectro: ["عرض الطيف", "Show spectrogram"], spectro_hide: ["إخفاء الطيف", "Hide spectrogram"],
  spec_loading: ["جاري رسم الطيف…", "Drawing the spectrogram…"], spec_failed: ["تعذّر رسم الطيف", "Couldn't draw the spectrogram"],
  pick_files: ["📁 اختر ملفات…", "📁 Choose files…"], pick_folder: ["🗂 اختر مجلد…", "🗂 Choose folder…"],
  choose: ["اختيار…", "Choose…"],
  picked: ["أُضيف {n} ملف للمعالجة", "{n} file(s) added"], nothing_found: ["ما لقيت ملفات صوت", "No audio files found"],
  lufs_label: ["مستوى الصوت النهائي", "Target loudness"],
  lufs_hint: ["سبوتي / يوتيوب -14. أعلى رقم = أعلى صوت", "Spotify / YouTube use -14. Higher = louder"],
  l_n14: ["-14 LUFS (سبوتي / يوتيوب)", "-14 LUFS (Spotify / YouTube)"], l_n16: ["-16 LUFS (Apple Music / هادئ)", "-16 LUFS (Apple Music / quiet)"],
  l_n11: ["-11 LUFS (أعلى)", "-11 LUFS (louder)"], l_n9: ["-9 LUFS (عالي جدًا)", "-9 LUFS (very loud)"],
  l_off: ["بدون تعديل المستوى", "Don't change the level"],
  p_ai_music: ["ذكاء اصطناعي: إزالة ضوضاء (أغاني)", "AI: noise removal (music)"],
  p_ai_voice: ["ذكاء اصطناعي: تنظيف الصوت (كلام)", "AI: voice cleanup (speech)"],
  watch_label: ["مراقبة مجلد", "Watch a folder"],
  watch_hint: ["أي أغنية جديدة تنزل في المجلد تتحسّن تلقائيًا (الموجود فيه الحين ما يتأثر)", "Any new song dropped in the folder is enhanced automatically (existing files are left alone)"],
  tags_edit: ["✎ تعديل البيانات", "✎ Edit tags"], tags_title: ["العنوان", "Title"], tags_artist: ["الفنان", "Artist"], tags_album: ["الألبوم", "Album"],
  tags_save: ["حفظ", "Save"], tags_cover: ["تغيير الغلاف…", "Change cover…"], tags_saved: ["تم الحفظ ✓", "Saved ✓"],
  tags_failed: ["تعذّر الحفظ", "Couldn't save"],
  update_restarting: ["جاري التحديث… البرنامج بيعيد التشغيل لحاله", "Updating… the app will restart by itself"],
  downloading: ["جاري تنزيل التحديث… {p}%", "Downloading the update… {p}%"],
  tab_enhance: ["تحسين", "Enhance"], tab_player: ["المشغّل", "Player"],
  url_hint: ["يوتيوب · تيكتوك · ساوندكلاود · انستا · سبوتيفاي (أغنية / ألبوم / قائمة). قوائم التشغيل تُكتشف تلقائيًا. سبوتيفاي: البرنامج يلقى الأغنية في يوتيوب وينزّلها (صوت سبوتيفاي نفسه محمي).",
             "YouTube · TikTok · SoundCloud · Instagram · Spotify (song / album / playlist). Playlists are detected automatically. Spotify: the app finds each song on YouTube and downloads it (Spotify's own audio is protected)."],
  keep_orig_label: ["الاحتفاظ بنسخة من الأصل", "Keep a copy of the original"],
  keep_orig_hint: ["للمقارنة وإعادة المعالجة والطيف. بدونها توفّر مساحة (صوت محسّن فقط)", "For comparing, re-running and the spectrogram. Off saves space (enhanced audio only)"],
  pl_files: ["📁 افتح ملفات…", "📁 Open files…"], pl_folder: ["🗂 افتح مجلد…", "🗂 Open folder…"], pl_clear: ["مسح القائمة", "Clear queue"],
  pl_empty: ["افتح ملفات صوت أو فيديو أو مجلد وأبدأ التشغيل", "Open audio or video files or a folder to start playing"],
  pl_formats: ["كل الصيغ مدعومة، والفيديو يُشغَّل صوته فقط", "All formats work; videos play audio only"],
  pl_preparing: ["جاري التجهيز…", "Preparing…"], pl_failed: ["تعذّر تشغيل هذا الملف", "Couldn't play this file"],
  pl_nothing: ["لا شي يُشغَّل", "Nothing playing"], play_here: ["▶ شغّل بالمشغّل", "▶ Play in the player"],
  waiting: ["بالانتظار", "Waiting"], failed: ["فشل", "Failed"], cancelled: ["أُلغيت", "Cancelled"],
  reading_playlist: ["قراءة القائمة", "Reading playlist"],
  retry: ["إعادة المحاولة", "Retry"],
  settings: ["الإعدادات", "Settings"], back: ["رجوع", "Back"],
  language: ["اللغة", "Language"], appearance: ["المظهر", "Appearance"],
  th_system: ["النظام", "System"], th_light: ["فاتح", "Light"], th_dark: ["داكن", "Dark"],
  light_mode: ["الوضع الخفيف", "Light mode"],
  light_hint: ["يشغّل المعالجة بأولوية منخفضة عشان الجهاز يبقى سريع", "Runs processing at low priority so your computer stays responsive"],
  notify_label: ["إشعار عند الانتهاء", "Notify when finished"],
  notify_hint: ["إشعار من النظام لما تخلص كل الأغاني", "A system notification when all songs are done"],
  out_folder: ["مجلد الحفظ", "Output folder"], save: ["حفظ", "Save"],
  ar_font: ["الخط العربي", "Arabic font"],
  font_ok: ["خط ثمانية مثبّت ومستخدم", "Thmanyah font is installed and in use"],
  font_missing: ["خط ثمانية غير مثبّت: نزّله من موقع ثمانية الرسمي وثبّته في نظامك (يُستخدم تلقائيًا). حاليًا يُستخدم خط بديل.",
                 "Thmanyah font isn't installed: download it from Thmanyah's official site and install it on your system (it's picked up automatically). A fallback font is used for now."],
  about: ["عن البرنامج", "About"], version: ["الإصدار", "Version"],
  auto_check: ["التحقق من التحديثات عند التشغيل", "Check for updates on launch"],
  updates: ["التحديثات", "Updates"],
  check_updates: ["تحقق من التحديثات", "Check for updates"],
  checking: ["جاري التحقق…", "Checking…"],
  up_to_date: ["أنت على آخر إصدار ✓", "You're up to date ✓"],
  update_available: ["يوجد إصدار جديد: {v}", "A new version is available: {v}"],
  update_banner: ["يوجد إصدار جديد من البرنامج ({v}).", "A new version is available ({v})."],
  open_settings: ["افتح الإعدادات", "Open settings"],
  update_to: ["حدّث إلى {v}", "Update to {v}"],
  open_releases: ["صفحة التحميل", "Download page"],
  updating: ["جاري التحديث…", "Updating…"],
  updated: ["تم التحديث. أعد التشغيل لتطبيقه.", "Updated. Restart to apply it."],
  restart: ["إعادة التشغيل", "Restart"],
  upd_err_no_repo: ["مستودع GitHub غير محدد في version.py", "GitHub repository isn't set in version.py"],
  upd_err_network: ["تعذّر الاتصال بـ GitHub", "Couldn't reach GitHub"],
  upd_err_git: ["فشل git pull", "git pull failed"],
  upd_err_bad_archive: ["ملف التحديث غير صالح", "The update archive is invalid"],
  upd_err_no_update: ["ما فيه تحديث جديد", "No update available"],
  upd_err_bad_checksum: ["فشل التحقق من سلامة ملف التحديث", "The update file failed its integrity check"],
  upd_err_frozen: ["هذي نسخة مجمّعة: نزّل الإصدار الجديد من صفحة التحميل", "This is a packaged build: download the new version from the download page"],
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
const S = { cfg: null, lang: "ar", files: [], cards: {}, state: null, view: "main", upd: null, bootChecked: false };
const fmt = (s, p) => s.replace(/\{(\w+)\}/g, (_, k) => (p[k] === undefined ? "" : p[k]));
const t = (k, p = {}) => fmt((T[k] || [k, k])[S.lang === "en" ? 1 : 0], p);
const msg = (k, p) => MSG[k] ? fmt(MSG[k][S.lang === "en" ? 1 : 0], p || {}) : k;
const f1 = v => (v === null || v === undefined || isNaN(v)) ? "؟" : (+v).toFixed(1);
const PRESETS = ["auto", "gentle", "natural", "clean", "bass", "vocal", "ai_music", "ai_voice"];
const LUFS = [[-14, "l_n14"], [-16, "l_n16"], [-11, "l_n11"], [-9, "l_n9"], [0, "l_off"]];
const FORMATS = ["flac", "mp3", "m4a", "opus", "wav"];

async function api(path, body) {
  const r = await fetch(path, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  return r.json();
}
const opts = (sel, keys, prefix) => keys.map(k => `<option value="${k}">${t(prefix + k)}</option>`).join("");

// ---------- اللغة والمظهر ----------
function applyLang() {
  const html = document.documentElement;
  html.lang = S.lang; html.dir = S.lang === "ar" ? "rtl" : "ltr";
  document.querySelectorAll("[data-i18n]").forEach(el => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll("[data-i18n-ph]").forEach(el => { el.placeholder = t(el.dataset.i18nPh); });
  const curP = $("preset").value || (S.cfg && S.cfg.preset) || "auto";
  const curF = $("format").value || (S.cfg && S.cfg.format) || "flac";
  $("preset").innerHTML = opts("preset", PRESETS, "p_"); $("preset").value = curP;
  $("format").innerHTML = opts("format", FORMATS, "f_"); $("format").value = curF;
  const curL = $("lufs").value || (S.cfg && String(S.cfg.lufs));
  $("lufs").innerHTML = LUFS.map(([v, k]) => `<option value="${v}">${t(k)}</option>`).join(""); if (curL !== null && curL !== undefined) $("lufs").value = curL;
  $("back").textContent = (S.lang === "ar" ? t("back") + "  ›" : "‹  " + t("back"));
  setFiles(S.files); showOut(); fillAbout(); showUpdBanner();
  for (const id in S.cards) { S.cards[id].done = false; refreshCard(id); }
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
async function saveCfg(patch) { const r = await api("/api/config", patch); S.cfg = r.config; return S.cfg; }
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

// اختيار ملفات / مجلد من نافذة النظام (تُعالَج من مكانها بدون نسخ). لو ما فيه نافذة نرجع لاختيار المتصفح.
async function pickNative(kind, fallbackInput) {
  $("formErr").textContent = "";
  let r;
  try { r = await api("/api/pick", { kind }); } catch (e) { r = { error: "x" }; }
  if (r.error) { fallbackInput.click(); return; }
  if (!r.paths.length) return;
  const res = await api("/api/submit_paths", { paths: r.paths, preset: $("preset").value, format: $("format").value, ...tuning() });
  $("formErr").textContent = res.error ? t("nothing_found") : t("picked", { n: res.added });
  poll();
}
$("pickFiles").onclick = () => pickNative("files", $("files"));
$("pickFolder").onclick = () => pickNative("folder", $("folderInput"));
const MEDIA_RE = /\.(mp3|m4a|aac|flac|wav|ogg|opus|wma|aiff?|ape|mka|mp4|mkv|webm|mov|avi|m4v|flv|wmv)$/i;
$("folderInput").addEventListener("change", e => { setFiles([...e.target.files].filter(f => MEDIA_RE.test(f.name))); });

// لصق من الحافظة + Ctrl/Cmd+Enter للإرسال
$("pasteBtn").onclick = async () => {
  $("pasteHint").textContent = "";
  try {
    const text = (await navigator.clipboard.readText()).trim();
    if (/^https?:\/\//.test(text)) { $("urls").value = ($("urls").value.trim() + "\n" + text).trim() + "\n"; return; }
    $("pasteHint").textContent = "—";
  } catch (e) { $("urls").focus(); $("pasteHint").textContent = t("paste_hint"); }
};
$("urls").addEventListener("keydown", e => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); $("go").click(); } });

// ---------- الإعدادات السريعة ----------
let jobs = 1;
const setJobs = v => { jobs = Math.max(1, Math.min(8, v)); $("jobsVal").textContent = jobs; };
$("jobsMinus").onclick = () => setJobs(jobs - 1);
$("jobsPlus").onclick = () => setJobs(jobs + 1);
["bass", "treble"].forEach(k => $(k).addEventListener("input", () => { $(k + "Val").textContent = (+$(k).value > 0 ? "+" : "") + $(k).value; }));
const tuning = () => ({ bass: +$("bass").value, treble: +$("treble").value, lufs: +$("lufs").value });
$("saveDefaults").onclick = async () => {
  await saveCfg({ preset: $("preset").value, format: $("format").value, jobs, ...tuning() });
  $("saveDefaults").textContent = t("saved");
  setTimeout(() => { $("saveDefaults").textContent = t("save_defaults"); }, 1500);
};

// ---------- إرسال ----------
$("go").onclick = async () => {
  $("formErr").textContent = "";
  const urls = $("urls").value.split(/\s+/).filter(u => /^https?:\/\//.test(u));
  if (!urls.length && !S.files.length) { $("formErr").textContent = t("need_input"); return; }
  const base = { preset: $("preset").value, format: $("format").value, ...tuning() };
  if (jobs !== S.cfg.jobs) await saveCfg({ jobs });
  $("go").disabled = true;
  try {
    if (urls.length) await api("/api/submit", { urls, playlist: $("playlist").checked, ...base });
    for (let i = 0; i < S.files.length; i++) {
      $("formErr").textContent = t("uploading", { i: i + 1, n: S.files.length });
      const f = S.files[i];
      const q = new URLSearchParams({ name: f.name, ...base });
      await fetch("/api/upload?" + q, { method: "POST", body: f });
    }
    $("formErr").textContent = "";
    $("urls").value = ""; $("files").value = ""; setFiles([]);
    poll();
  } catch (e) { $("formErr").textContent = t("unexpected", { e: e.message }); }
  $("go").disabled = false;
};
$("clearList").onclick = async () => { await api("/api/clear", {}); poll(); };
$("openFolder").onclick = () => api("/api/open", {});
// مربع داخلي بدل prompt() (ما يشتغل في النوافذ المستقلة)
$("cleanOld").onclick = () => { $("cleanBox").hidden = !$("cleanBox").hidden; };
$("cleanCancel").onclick = () => { $("cleanBox").hidden = true; };
$("cleanGo").onclick = async () => {
  const r = await api("/api/clean", { days: Math.max(0, +$("cleanDays").value || 0) });
  $("cleanBox").hidden = true;
  $("outInfo").textContent = t("deleted", { n: r.deleted });
};

// ---------- بطاقات الأغاني ----------
function stageText(k) { return k in MSG ? msg(k) : t(k || "waiting"); }
function errText(e) { return !e ? "" : (e.key ? msg(e.key, e.params) : t("unexpected", { e: e.text })); }
const btn = (cls, text, onclick) => { const b = document.createElement("button"); b.className = cls; b.textContent = text; b.onclick = onclick; return b; };

function makeCard(it) {
  const el = document.createElement("section");
  el.className = "card song";
  el.innerHTML = `<div class="top"><div class="name"></div><span class="badge" hidden></span></div>
    <div class="stage sub"></div><div class="bar-track"><i></i></div><div class="err"></div>
    <div class="actions"></div><div class="res"></div>`;
  $("list").prepend(el);
  return S.cards[it.id] = { el, it, done: false, key: null, name: el.querySelector(".name"), badge: el.querySelector(".badge"),
    stage: el.querySelector(".stage"), track: el.querySelector(".bar-track"), bar: el.querySelector(".bar-track i"),
    err: el.querySelector(".err"), actions: el.querySelector(".actions"), res: el.querySelector(".res") };
}
function refreshCard(id) {
  const c = S.cards[id]; if (!c) return; const it = c.it;
  c.name.textContent = (it.result && it.result.title) || it.label;
  const done = it.status === "done", error = it.status === "error", canc = it.status === "cancelled";
  c.track.hidden = done; c.stage.hidden = done;
  c.bar.style.width = it.pct + "%";
  c.track.classList.toggle("fail", error);
  c.stage.textContent = error ? t("failed") : canc ? t("cancelled") : it.status === "waiting" ? t("waiting") : `${stageText(it.stage_key)} · ${it.pct}%`;
  c.err.textContent = error ? errText(it.error) : "";
  c.actions.innerHTML = "";
  if (it.status === "waiting" || it.status === "running") c.actions.append(btn("link", t("cancel"), () => api("/api/cancel", { id: it.id })));
  if ((error || canc) && it.can_retry) c.actions.append(btn("tint", t("retry"), () => api("/api/retry", { id: it.id }).then(poll)));
  if (done) { renderResult(c); } else { c.badge.hidden = true; c.res.innerHTML = ""; c.done = false; c.audio = null; }
}
function renderResult(c) {
  const r = c.it.result, it = c.it;
  const key = r.output_name + "|" + S.lang + "|" + it.can_rerun;
  if (c.done && c.key === key) return;
  const wasPlaying = c.audio ? { t: c.audio.currentTime, paused: c.audio.paused, w: c.which } : null;
  c.key = key;
  c.badge.hidden = false; c.badge.className = "badge q-" + r.quality; c.badge.textContent = t("q_" + r.quality);
  const used = t("p_" + r.preset).replace(/ \(.*\)$/, "") + (r.auto ? t("auto_tag") : "");
  const src = r.codec + (r.bitrate_kbps ? " " + r.bitrate_kbps + "kbps" : "");
  c.res.innerHTML = `<div class="meta"></div>
    ${r.original_url ? `<div class="ab"><button class="tint" data-w="o"></button><button class="tint" data-w="e"></button><span class="sub"></span></div>` : ""}
    <audio controls preload="metadata"></audio>
    <div class="more"></div><div class="spec" hidden></div>`;
  c.res.querySelector(".meta").textContent =
    (it.cached ? t("cached_note") + "\n" : "") +
    `${msg(r.reason_key, r.reason_params)}\n${t("source")}: ${src}  ·  ${t("preset_used")}: ${used}\n` +
    `${t("loudness")}: ${f1(r.lufs_before)} ← ${f1(r.lufs_after)} LUFS  ·  ${t("peak")}: ${f1(r.tp_before)} ← ${f1(r.tp_after)} dBTP`;
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

  // أدوات إضافية: إظهار في المجلد / الطيف / نمط ثاني
  const more = c.res.querySelector(".more"), spec = c.res.querySelector(".spec");
  more.append(btn("link", t("play_here"), () => playResult(it.id)));
  more.append(btn("link", "📂 " + t("show_folder"), () => api("/api/open", {})));
  if (it.can_tags) {
    const tagsBox = document.createElement("div"); tagsBox.className = "tags"; tagsBox.hidden = true;
    more.append(btn("link", t("tags_edit"), async () => {
      tagsBox.hidden = !tagsBox.hidden;
      if (!tagsBox.hidden && !tagsBox.dataset.loaded) { tagsBox.dataset.loaded = "1"; await buildTags(tagsBox, it); }
    }));
    c.res.append(tagsBox);
  }
  if (it.can_rerun) {
    const specBtn = btn("link", "📈 " + t("spectro"), () => {
      spec.hidden = !spec.hidden;
      specBtn.textContent = "📈 " + (spec.hidden ? t("spectro") : t("spectro_hide"));
      if (!spec.hidden && !spec.dataset.loaded) { spec.dataset.loaded = "1"; loadSpectrogram(spec, it.id); }
    });
    more.append(specBtn);
    const sel = document.createElement("select"); sel.innerHTML = opts("", PRESETS, "p_"); sel.value = r.auto ? "auto" : r.preset;
    const go = btn("tint", t("rerun_go"), async () => { go.disabled = true; await api("/api/reprocess", { id: it.id, preset: sel.value, format: r.format, ...tuning() }); go.disabled = false; poll(); });
    const wrap = document.createElement("div"); wrap.className = "rerun";
    const lbl = document.createElement("span"); lbl.className = "sub"; lbl.textContent = t("rerun");
    wrap.append(lbl, sel, go); more.append(wrap);
  }
  c.done = true;
}
async function buildTags(box, it) {
  const cur = await api("/api/tags?id=" + encodeURIComponent(it.id));
  if (cur.error) { box.textContent = t("tags_failed"); return; }
  const fields = {};
  [["title", "tags_title"], ["artist", "tags_artist"], ["album", "tags_album"]].forEach(([k, lbl]) => {
    const l = document.createElement("label"); l.textContent = t(lbl);
    const i = document.createElement("input"); i.type = "text"; i.value = cur[k] || ""; fields[k] = i;
    l.append(i); box.append(l);
  });
  const row = document.createElement("div"); row.className = "inline";
  const msgEl = document.createElement("span"); msgEl.className = "sub";
  const save = btn("tint", t("tags_save"), async () => {
    const r = await api("/api/tags", { id: it.id, title: fields.title.value, artist: fields.artist.value, album: fields.album.value });
    msgEl.textContent = r.ok ? t("tags_saved") : t("tags_failed");
  });
  row.append(save);
  if (cur.cover_ok) {
    const file = document.createElement("input"); file.type = "file"; file.accept = "image/jpeg,image/png"; file.hidden = true;
    file.onchange = async () => {
      if (!file.files[0]) return;
      const r = await (await fetch("/api/cover?id=" + encodeURIComponent(it.id), { method: "POST", body: file.files[0] })).json();
      msgEl.textContent = r.ok ? t("tags_saved") : t("tags_failed");
    };
    row.append(btn("tint", t("tags_cover"), () => file.click()), file);
  }
  row.append(msgEl); box.append(row);
}
function loadSpectrogram(box, id) {
  box.innerHTML = `<div class="sub" data-s="load">${t("spec_loading")}</div>`;
  let pending = 2;
  const done = () => { if (--pending === 0) box.querySelector('[data-s="load"]').remove(); };
  [["o", "original"], ["e", "enhanced"]].forEach(([w, key]) => {
    const fig = document.createElement("figure");
    const cap = document.createElement("figcaption"); cap.textContent = t(key);
    const img = new Image(); img.alt = t(key);
    img.onload = done;
    img.onerror = () => { fig.textContent = t("spec_failed"); done(); };
    img.src = `/api/spectrogram?id=${encodeURIComponent(id)}&which=${w}`;
    fig.append(cap, img); box.append(fig);
  });
}
function render(items) {
  const ids = new Set(items.map(i => i.id));
  for (const id in S.cards) if (!ids.has(id)) { S.cards[id].el.remove(); delete S.cards[id]; }
  for (const it of items) {
    const c = S.cards[it.id] || makeCard(it);
    c.it = it;
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

// ---------- صفحة الإعدادات ----------
function show(view) {
  if (view !== "settings") lastTab = view;
  S.view = view;
  $("main").hidden = view !== "main"; $("settings").hidden = view !== "settings"; $("player").hidden = view !== "player";
  $("gear").hidden = view === "settings"; $("tabs").hidden = view === "settings";
  setSeg("tabSeg", view === "player" ? "player" : "main");
  window.scrollTo(0, 0);
  if (view === "settings") loadSettings();
}
$("gear").onclick = () => show("settings");
bindSeg("tabSeg", v => show(v));
let lastTab = "main";
$("back").onclick = () => show(lastTab);
$("repoLink").onclick = () => api("/api/open_repo", {});
$("updBannerGo").onclick = () => show("settings");

function fillAbout() {
  if (!S.state) return;
  $("aboutLine").textContent = `${S.state.app} · ${t("version")} ${S.state.version}`;
  $("fontStatus").textContent = S.state.thmanyah ? t("font_ok") : t("font_missing");
  $("repoLink").hidden = !S.state.repo_url;
  $("quit").hidden = S.state.mode !== "browser";
}
async function loadSettings() {
  setSeg("langSeg", S.lang); setSeg("themeSeg", S.cfg.theme);
  $("lightMode").checked = S.cfg.light; $("keepOrig").checked = S.cfg.keep_original; $("notifyOn").checked = S.cfg.notify; $("autoCheck").checked = S.cfg.auto_check;
  $("outPath").value = S.cfg.out;
  $("watchOn").checked = S.cfg.watch_on; $("watchPath").value = S.cfg.watch || "";
  fillAbout();
  if (S.upd && S.upd.available) showUpdateResult(S.upd);
  const v = await api("/api/ytdlp/version", {});
  $("engStatus").textContent = v.version ? "yt-dlp " + v.version : "—";
}
bindSeg("langSeg", async v => { S.lang = v; await saveCfg({ lang: v }); applyLang(); loadSettings(); });
bindSeg("themeSeg", async v => { await saveCfg({ theme: v }); applyTheme(); });
$("keepOrig").onchange = e => saveCfg({ keep_original: e.target.checked });
$("lightMode").onchange = e => saveCfg({ light: e.target.checked });
$("notifyOn").onchange = e => saveCfg({ notify: e.target.checked });
$("autoCheck").onchange = e => saveCfg({ auto_check: e.target.checked });
$("watchOn").onchange = e => saveCfg({ watch_on: e.target.checked });
$("watchSave").onclick = async () => { await saveCfg({ watch: $("watchPath").value.trim() }); $("watchSave").textContent = t("saved"); setTimeout(() => { $("watchSave").textContent = t("save"); }, 1500); };
$("watchPick").onclick = async () => {
  const r = await api("/api/pick", { kind: "folder" });
  if (r.paths && r.paths[0]) { $("watchPath").value = r.paths[0]; await saveCfg({ watch: r.paths[0] }); }
};
$("outSave").onclick = async () => { await saveCfg({ out: $("outPath").value.trim() }); showOut(); $("outSave").textContent = t("saved"); setTimeout(() => { $("outSave").textContent = t("save"); }, 1500); };

// ---------- التحديثات ----------
function updError(r) { return (T["upd_err_" + r.error] ? t("upd_err_" + r.error) : r.error) + (r.detail ? ` (${r.detail})` : ""); }
function showUpdBanner() {
  const has = S.upd && S.upd.available;
  $("gearDot").hidden = !has; $("updBanner").hidden = !has;
  if (has) $("updBannerText").textContent = t("update_banner", { v: S.upd.latest });
}
function showUpdateResult(r) {
  $("updStatus").textContent = t("update_available", { v: r.latest });
  $("updRow").hidden = false; $("updTitle").textContent = `v${r.current} → v${r.latest}`;
  const ap = $("updApply"); ap.hidden = false; ap.textContent = t("update_to", { v: r.latest }); ap.disabled = false;
  $("updReleases").hidden = true; $("updRestart").hidden = true;
}
async function checkUpdates(cached) {
  const r = await api("/api/update/check", { cached });
  if (!r.error) S.upd = r;
  showUpdBanner();
  return r;
}
$("updCheck").onclick = async () => {
  $("updStatus").textContent = t("checking"); $("updRow").hidden = true;
  const r = await checkUpdates(false);
  if (r.error) { $("updStatus").textContent = updError(r); return; }
  if (!r.available) { $("updStatus").textContent = t("up_to_date") + `  (v${r.current})`; return; }
  showUpdateResult(r);
};
function waitForRestart(oldVersion) {
  const deadline = Date.now() + 120000;
  const wait = async () => {
    try {
      const r = await (await fetch("/api/ping")).json();
      if (r.version && r.version !== oldVersion) { location.reload(); return; }
    } catch (e) { /* السيرفر بيرجع */ }
    if (Date.now() < deadline) setTimeout(wait, 1500);
  };
  setTimeout(wait, 3000);
}
$("updApply").onclick = async () => {
  const ap = $("updApply"); ap.disabled = true; ap.textContent = t("updating");
  $("updProgRow").hidden = false; $("updProgBar").style.width = "0%";
  const poller = setInterval(async () => {
    try {
      const p = await api("/api/update/progress");
      if (p.state === "download" && p.total) { const pc = Math.round(100 * p.done / p.total); $("updProgBar").style.width = pc + "%"; $("updStatus").textContent = t("downloading", { p: pc }); }
    } catch (e) { /* قد يكون البرنامج قفل للتحديث */ }
  }, 500);
  let r;
  try { r = await api("/api/update/apply", {}); } finally { clearInterval(poller); }
  if (!r.ok) { $("updProgRow").hidden = true; $("updStatus").textContent = updError(r); ap.disabled = false; ap.textContent = t("check_updates"); return; }
  ap.hidden = true;
  if (r.exit) { $("updProgBar").style.width = "100%"; $("updStatus").textContent = t("update_restarting"); waitForRestart(S.state.version); return; }
  $("updProgRow").hidden = true; $("updStatus").textContent = t("updated"); $("updRestart").hidden = false;
};
$("updReleases").onclick = () => api("/api/open_repo", { releases: true });
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
  $("engStatus").textContent = r.ok ? t("engine_updated", { a: "yt-dlp " + (r.after || "") }) : (r.error ? updError(r) : t("engine_failed") + (r.detail ? ` (${r.detail})` : ""));
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
      applyTheme(); setJobs(s.config.jobs);
      $("bass").value = s.config.bass; $("treble").value = s.config.treble;
      ["bass", "treble"].forEach(k => $(k).dispatchEvent(new Event("input")));
      $("preset").innerHTML = opts("", PRESETS, "p_"); $("preset").value = s.config.preset;
      $("format").innerHTML = opts("", FORMATS, "f_"); $("format").value = s.config.format;
      $("lufs").innerHTML = LUFS.map(([v, k]) => `<option value="${v}">${t(k)}</option>`).join(""); $("lufs").value = s.config.lufs;
      applyLang();
    }
    renderBanner(s); render(s.items); fillAbout();
    busy = s.items.some(i => i.status === "waiting" || i.status === "running");
    if (!S.bootChecked) {
      S.bootChecked = true;
      if (S.cfg.auto_check) checkUpdates(true).catch(() => { });
      api("/api/player/tracks").then(r => { if (r.tracks.length && !P.tracks.length) { P.tracks = r.tracks; renderQueue(); updateNow(); } }).catch(() => { });
    }
  } catch (e) { /* الخادم غير متاح مؤقتًا */ }
  // خفيف: نخفف الاستعلام لما الصفحة مخفية أو ما فيه شغل
  timer = setTimeout(poll, document.hidden ? 30000 : busy ? 1000 : 4000);
}
document.addEventListener("visibilitychange", () => { if (!document.hidden) poll(); });
poll();


// ======================= المشغّل =======================
const P = { tracks: [], idx: -1, shuffle: false, repeat: "off", order: [], mode: "direct", seeking: false };
const audio = $("audio");
const MIME = { mp3: "audio/mpeg", m4a: "audio/mp4", aac: "audio/aac", wav: "audio/wav", flac: "audio/flac", ogg: "audio/ogg",
  opus: 'audio/ogg; codecs="opus"', webm: "audio/webm", weba: "audio/webm", mp4: "video/mp4" };
const canDirect = ext => !!MIME[ext] && audio.canPlayType(MIME[ext]) !== "";
const fmtTime = s => { if (!isFinite(s) || s < 0) return "0:00"; s = Math.floor(s); const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), x = s % 60; return (h ? h + ":" + String(m).padStart(2, "0") : m) + ":" + String(x).padStart(2, "0"); };
const trackName = t => t.title || t.name;

function rebuildOrder() {
  const n = P.tracks.length, idx = [...Array(n).keys()];
  if (P.shuffle) { for (let i = n - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [idx[i], idx[j]] = [idx[j], idx[i]]; } }
  if (P.shuffle && P.idx >= 0) { const k = idx.indexOf(P.idx); if (k > 0) { idx.splice(k, 1); idx.unshift(P.idx); } }
  P.order = idx;
}
function renderQueue() {
  const ol = $("queue"); ol.innerHTML = "";
  P.tracks.forEach((t, i) => {
    const li = document.createElement("li"); li.className = i === P.idx ? "cur" : ""; li.dataset.i = i;
    li.innerHTML = '<span class="n"></span><span class="t"></span><span class="d"></span>';
    li.children[0].textContent = i === P.idx ? "▶" : i + 1; li.children[1].textContent = trackName(t);
    li.children[2].textContent = t.duration ? fmtTime(t.duration) : "";
    li.onclick = () => playIndex(i);
    ol.append(li);
  });
  $("plEmpty").hidden = P.tracks.length > 0;
}
function updateNow() {
  const t = P.tracks[P.idx];
  $("npTitle").textContent = t ? trackName(t) : t_("pl_nothing");
  $("npArtist").textContent = t ? [t.artist, t.album].filter(Boolean).join(" · ") : "";
  const img = $("npCover");
  if (t && t.has_cover && !t.blob) { img.src = "/api/player/cover?id=" + encodeURIComponent(t.id); img.hidden = false; $("npIcon").hidden = true; }
  else { img.hidden = true; $("npIcon").hidden = false; }
  if ("mediaSession" in navigator && t) {
    try { navigator.mediaSession.metadata = new MediaMetadata({ title: trackName(t), artist: t.artist || "", album: t.album || "" }); } catch (e) { /* غير مدعوم */ }
  }
}
const t_ = k => t(k);
async function loadMeta(i) {
  const t = P.tracks[i]; if (!t || t.blob || t.meta) return;
  t.meta = true;
  try { Object.assign(t, await api("/api/player/meta?id=" + encodeURIComponent(t.id))); } catch (e) { return; }
  const li = $("queue").children[i];
  if (li) { li.children[1].textContent = trackName(t); li.children[2].textContent = t.duration ? fmtTime(t.duration) : ""; }
  if (i === P.idx) updateNow();
}
function setSrc(t, mode) {
  P.mode = mode;
  audio.src = t.blob || `/play/${t.id}` + (mode === "transcode" ? "?mode=transcode" : "");
  $("npArtist").textContent = mode === "transcode" ? t_("pl_preparing") : $("npArtist").textContent;
  audio.play().catch(() => { });
}
function playIndex(i) {
  if (i < 0 || i >= P.tracks.length) return;
  P.idx = i; const t = P.tracks[i];
  rebuildOrder(); renderQueue(); updateNow();
  setSrc(t, t.blob || canDirect(t.ext) ? "direct" : "transcode");
  loadMeta(i).then(() => { for (let k = 1; k <= 2; k++) loadMeta((i + k) % P.tracks.length); });
  const li = $("queue").children[i]; if (li && li.scrollIntoView) li.scrollIntoView({ block: "nearest" });
}
function step(delta) {
  if (!P.tracks.length) return null;
  const pos = P.order.indexOf(P.idx), np = pos + delta;
  if (np >= 0 && np < P.order.length) return P.order[np];
  if (P.repeat === "all") return P.order[(np + P.order.length) % P.order.length];
  return null;
}
function next() { const i = step(1); if (i !== null) playIndex(i); else { audio.pause(); } }
function prev() {
  if (audio.currentTime > 3) { audio.currentTime = 0; return; }
  const i = step(-1); if (i !== null) playIndex(i); else audio.currentTime = 0;
}
function loadQueue(tracks, start) {
  P.tracks = tracks; P.idx = -1; renderQueue();
  if (tracks.length) playIndex(start || 0); else { audio.pause(); audio.removeAttribute("src"); updateNow(); }
}
audio.addEventListener("ended", () => { if (P.repeat === "one") { audio.currentTime = 0; audio.play(); } else next(); });
audio.addEventListener("error", () => {
  const t = P.tracks[P.idx]; if (!t) return;
  if (P.mode === "direct" && !t.blob) { setSrc(t, "transcode"); return; }  // المتصفح ما يشغّل الصيغة: نحوّلها مؤقتًا
  $("npArtist").textContent = t_("pl_failed");
  setTimeout(() => { if (P.tracks[P.idx] === t) next(); }, 1500);
});
audio.addEventListener("playing", () => { const t = P.tracks[P.idx]; if (t) $("npArtist").textContent = [t.artist, t.album].filter(Boolean).join(" · "); $("btnPlay").textContent = "⏸"; });
audio.addEventListener("pause", () => { $("btnPlay").textContent = "▶"; });
audio.addEventListener("timeupdate", () => {
  const d = audio.duration || (P.tracks[P.idx] && P.tracks[P.idx].duration) || 0;
  $("tCur").textContent = fmtTime(audio.currentTime); $("tDur").textContent = fmtTime(d);
  if (!P.seeking && d) $("seek").value = Math.round(1000 * audio.currentTime / d);
});
audio.addEventListener("loadedmetadata", () => { $("tDur").textContent = fmtTime(audio.duration); });
$("seek").addEventListener("input", () => { P.seeking = true; const d = audio.duration; if (d) $("tCur").textContent = fmtTime(d * $("seek").value / 1000); });
$("seek").addEventListener("change", () => { const d = audio.duration; if (d) audio.currentTime = d * $("seek").value / 1000; P.seeking = false; });
$("btnPlay").onclick = () => { if (P.idx < 0 && P.tracks.length) playIndex(0); else if (audio.paused) audio.play().catch(() => { }); else audio.pause(); };
$("btnNext").onclick = next; $("btnPrev").onclick = prev;
$("btnShuffle").onclick = () => { P.shuffle = !P.shuffle; $("btnShuffle").classList.toggle("on", P.shuffle); rebuildOrder(); };
$("btnRepeat").onclick = () => {
  P.repeat = P.repeat === "off" ? "all" : P.repeat === "all" ? "one" : "off";
  $("btnRepeat").textContent = P.repeat === "one" ? "🔂" : "🔁"; $("btnRepeat").classList.toggle("on", P.repeat !== "off");
};
try { const v = localStorage.getItem("msga_vol"); if (v !== null) $("vol").value = v; } catch (e) { /* التخزين غير متاح */ }
audio.volume = $("vol").value / 100;
$("vol").addEventListener("input", () => { audio.volume = $("vol").value / 100; try { localStorage.setItem("msga_vol", $("vol").value); } catch (e) { /* */ } });
document.addEventListener("keydown", e => {
  if (S.view !== "player" || /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName) && e.target.type !== "range") return;
  if (e.code === "Space") { e.preventDefault(); $("btnPlay").click(); }
  else if (e.shiftKey && e.code === "ArrowRight") next();
  else if (e.shiftKey && e.code === "ArrowLeft") prev();
});
if ("mediaSession" in navigator) {
  const set = (a, f) => { try { navigator.mediaSession.setActionHandler(a, f); } catch (e) { /* */ } };
  set("play", () => audio.play()); set("pause", () => audio.pause()); set("previoustrack", prev); set("nexttrack", next);
}
async function plOpen(kind) {
  let r; try { r = await api("/api/player/open", { kind }); } catch (e) { r = { error: "x" }; }
  if (r.error) { $("plInput").click(); return; }   // ما فيه نافذة اختيار: نرجع لمتصفح الملفات
  if (r.tracks.length) loadQueue(r.tracks, 0);
}
$("plFiles").onclick = () => plOpen("files");
$("plFolder").onclick = () => plOpen("folder");
$("plInput").addEventListener("change", e => {
  const files = [...e.target.files].filter(f => MEDIA_RE.test(f.name));
  loadQueue(files.map((f, i) => ({ id: "blob" + i, name: f.name.replace(/\.[^.]+$/, ""), ext: (f.name.split(".").pop() || "").toLowerCase(), blob: URL.createObjectURL(f) })), 0);
});
$("plClear").onclick = async () => { await api("/api/player/clear", {}); loadQueue([], 0); };
async function playResult(itemId) {
  const r = await api("/api/player/add_item", { id: itemId });
  if (r.error) return;
  P.tracks = r.tracks; show("player"); renderQueue(); playIndex(r.index);
}
