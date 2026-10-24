"use strict";
/* Make Sound Great Again: واجهة النافذة / المتصفح. بدون أي مكتبات خارجية (خفيفة). */

// ---------- النصوص: [عربي, English] ----------
const T = {
  subtitle: ["حسّن جودة أي أغنية من رابط أو ملف", "Improve any song from a link or a file"],
  url_placeholder: ["الصق رابط (يوتيوب، تيكتوك، انستا، سبوتيفاي…) أو اكتب اسم الأغنية مثل: محمد عبده - الأماكن (سطر لكل وحدة)",
                    "Paste a link (YouTube, TikTok, Instagram, Spotify…) or type a song name like: Artist - Title (one per line)"],
  url_hint: ["يوتيوب · تيكتوك · ساوندكلاود · انستا · سبوتيفاي · تويتش (تسجيلات ومقاطع وبث مباشر). قوائم التشغيل تُكتشف تلقائيًا. سبوتيفاي: البرنامج يلقى الأغنية في يوتيوب وينزّلها. تويتش: صوت فقط، وللبث المباشر يظهر زر «إيقاف وحفظ».",
             "YouTube · TikTok · SoundCloud · Instagram · Spotify · Twitch (past broadcasts, clips and live streams). Playlists are detected automatically. Spotify: the app finds each song on YouTube. Twitch: audio only, and live streams get a “Stop & save” button."],
  paste_link: ["📋 لصق رابط من الحافظة", "📋 Paste link from clipboard"],
  paste_hint: ["اضغط Ctrl+V داخل المربع", "Press Ctrl+V inside the box"],
  drop_title: ["اسحب ملفات الأغاني هنا", "Drop song files here"],
  drop_sub: ["أو اضغط للاختيار من جهازك", "or click to choose from your computer"],
  files_selected: ["{n} ملف مختار", "{n} file(s) selected"],
  clear_files: ["إزالة الملفات المختارة", "Remove selected files"],
  preset: ["النمط", "Preset"], format: ["الصيغة", "Format"],
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
  p_ai_music: ["ذكاء اصطناعي: إزالة ضوضاء (أغاني)", "AI: noise removal (music)"],
  p_ai_voice: ["ذكاء اصطناعي: تنظيف الصوت (كلام)", "AI: voice cleanup (speech)"],
  d_auto: ["يفحص جودة الأغنية ويختار النمط المناسب لحاله: تنظيف للضعيفة، طبيعي للمتوسطة، وخفيف للعالية.",
           "Checks the song's quality and picks for you: clean-up for weak sources, natural for medium, gentle for high quality."],
  d_gentle: ["تعديل بسيط جدًا وتوحيد مستوى الصوت فقط. للأغاني الجيدة أصلًا (FLAC أو MP3 بجودة عالية).",
             "A very light touch plus loudness levelling. For songs that already sound good (FLAC or high-bitrate MP3)."],
  d_natural: ["إزالة ضوضاء خفيفة، وإبراز البيس والوضوح قليلًا، ولمسة لمعان في الترددات العالية.",
              "Light noise reduction, a little more bass and clarity, and some sparkle in the highs."],
  d_clean: ["إزالة ضوضاء أقوى ووضوح أعلى وضغط خفيف. للمقاطع الضعيفة والمضغوطة مثل تيكتوك وانستا.",
            "Stronger noise reduction, more clarity and gentle compression. For weak, heavily compressed clips (TikTok, Instagram)."],
  d_bass: ["يعزز الترددات المنخفضة (60 و120 هرتز) لبيس أثقل وأوضح.", "Boosts the low end (60 and 120 Hz) for heavier, punchier bass."],
  d_vocal: ["يرفع ترددات الصوت البشري ويخفف الطنين، عشان صوت المغني يوضح وسط الموسيقى.",
            "Lifts the voice frequencies and cuts muddiness so the singer stands out from the music."],
  d_ai_music: ["نموذج ذكاء اصطناعي (RNNoise) يشيل الخشخشة وضوضاء الخلفية، ممزوج مع الأصل عشان ما يضر الآلات.",
               "An AI model (RNNoise) removes hiss and background noise, blended with the original so instruments aren't harmed."],
  d_ai_voice: ["نموذج ذكاء اصطناعي مخصص للكلام: ينظّف صوت الشخص المتكلم من ضوضاء التسجيل.",
               "An AI model made for speech: cleans the speaker's voice from recording noise."],
  f_flac: ["FLAC (بدون ضغط)", "FLAC (lossless)"], f_mp3: ["MP3 320", "MP3 320"], f_m4a: ["M4A (AAC 256)", "M4A (AAC 256)"],
  f_opus: ["Opus 192", "Opus 192"], f_wav: ["WAV (24-bit)", "WAV (24-bit)"],
  d_flac: ["بدون أي فقد في الجودة. الأكبر حجمًا.", "No quality loss at all. The biggest files."],
  d_mp3: ["يشتغل على كل الأجهزة. حجم متوسط.", "Plays on every device. Medium size."],
  d_m4a: ["جودة ممتازة بحجم أصغر من MP3 تقريبًا.", "Excellent quality, usually smaller than MP3."],
  d_opus: ["أصغر حجم بجودة عالية جدًا. الأنسب لتوفير المساحة.", "The smallest files at very high quality. Best for saving space."],
  d_wav: ["بدون ضغط إطلاقًا. حجم كبير جدًا.", "Completely uncompressed. Very large files."],
  lufs_label: ["مستوى الصوت النهائي", "Target loudness"],
  lufs_hint: ["سبوتي / يوتيوب -14. أعلى رقم = أعلى صوت", "Spotify / YouTube use -14. Higher = louder"],
  l_n14: ["-14 LUFS (سبوتي / يوتيوب)", "-14 LUFS (Spotify / YouTube)"], l_n16: ["-16 LUFS (Apple Music / هادئ)", "-16 LUFS (Apple Music / quiet)"],
  l_n11: ["-11 LUFS (أعلى)", "-11 LUFS (louder)"], l_n9: ["-9 LUFS (عالي جدًا)", "-9 LUFS (very loud)"],
  l_off: ["بدون تعديل المستوى", "Don't change the level"],
  dl_n14: ["المستوى المعتمد في سبوتيفاي ويوتيوب. متوازن.", "The level Spotify and YouTube use. Balanced."],
  dl_n16: ["أهدأ شوي ويحافظ على الفروق بين الهادئ والعالي.", "A bit quieter, keeps more dynamics."],
  dl_n11: ["أعلى من المعتاد.", "Louder than usual."],
  dl_n9: ["عالي جدًا، وقد يضغط الصوت.", "Very loud, may sound squashed."],
  dl_off: ["يحافظ على مستوى الأغنية الأصلي (يمنع التشويه فقط).", "Keeps the song's original level (only prevents distortion)."],
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
  watch_label: ["مراقبة مجلد", "Watch a folder"],
  watch_hint: ["أي أغنية جديدة تنزل في المجلد تتحسّن تلقائيًا (الموجود فيه الحين ما يتأثر)", "Any new song dropped in the folder is enhanced automatically (existing files are left alone)"],
  tags_edit: ["✎ تعديل البيانات", "✎ Edit tags"], tags_title: ["العنوان", "Title"], tags_artist: ["الفنان", "Artist"], tags_album: ["الألبوم", "Album"],
  tags_save: ["حفظ", "Save"], tags_cover: ["تغيير الغلاف…", "Change cover…"], tags_saved: ["تم الحفظ ✓", "Saved ✓"],
  tags_failed: ["تعذّر الحفظ", "Couldn't save"],
  in_player: ["في المشغّل", "In the player"], details: ["التفاصيل", "Details"],
  keep_orig_label: ["الاحتفاظ بنسخة من الأصل", "Keep a copy of the original"],
  keep_orig_hint: ["للمقارنة وإعادة المعالجة والطيف. بدونها توفّر مساحة (صوت محسّن فقط)", "For comparing, re-running and the spectrogram. Off saves space (enhanced audio only)"],
  auto_player_label: ["إرسال الأغاني المحسّنة للمشغّل", "Send enhanced songs to the player"],
  auto_player_hint: ["كل أغنية تخلص تنضاف لقائمة المشغّل، وتشتغل لو المشغّل فاضي", "Every finished song is added to the player queue, and starts if nothing is playing"],
  // المشغّل
  player_mode: ["وضع المشغّل", "Player mode"],
  pin_on: ["البرنامج يفتح بوضع المشغّل (اضغط للإلغاء)", "The app opens in player mode (click to turn off)"],
  pin_off: ["افتح البرنامج دائمًا بوضع المشغّل", "Always open the app in player mode"],
  pl_add: ["إضافة", "Add"], pl_add_files: ["إضافة أغاني…", "Add songs…"], pl_add_folder: ["إضافة مجلد…", "Add a folder…"],
  pl_add_list: ["إضافة قائمة تشغيل (m3u)…", "Add a playlist (m3u)…"], pl_clear: ["مسح القائمة", "Clear queue"],
  pl_queue: ["قائمة التشغيل", "Queue"], pl_corner: ["نقل للزاوية الثانية (فوق / تحت)", "Move to the other corner (top / bottom)"],
  pl_back: ["الرجوع للمحسّن", "Back to the enhancer"],
  pl_empty: ["أضف أغاني أو مجلد من زر +", "Add songs or a folder with the + button"],
  pl_formats: ["كل الصيغ مدعومة، والفيديو يُشغَّل صوته فقط", "All formats work; videos play audio only"],
  pl_preparing: ["جاري التجهيز…", "Preparing…"], pl_failed: ["تعذّر تشغيل هذا الملف", "Couldn't play this file"],
  pl_nothing: ["لا شي يُشغَّل", "Nothing playing"], play_here: ["▶ شغّل بالمشغّل", "▶ Play in the player"],
  stop_rec: ["⏹ إيقاف وحفظ", "⏹ Stop & save"],
  rec_wait: ["🔴 يتصل بالبث…", "🔴 Connecting to the stream…"], rec_status: ["🔴 يسجّل البث المباشر… {mb} MB", "🔴 Recording the live stream… {mb} MB"],
  twitch_opus_note: ["حُفظ بصيغة Opus لأن البث طويل وصوته مضغوط أصلًا (يوفّر حجم كبير)", "Saved as Opus: the stream is long and its audio is already compressed (saves a lot of space)"],
  from_twitch: ["تويتش", "Twitch"],
  from_src: ["المصدر: {c} · {t}", "Source: {c} · {t}"], not_this: ["مو هذي الأغنية", "Not this song"],
  trying_next: ["أجرّب نسخة ثانية…", "Trying another version…"],
  library: ["المكتبة", "Library"], lib_search: ["ابحث بالاسم أو الفنان…", "Search by title or artist…"],
  lib_dups: ["المكررات فقط", "Duplicates only"], lib_play_all: ["▶ تشغيل الكل", "▶ Play all"],
  lib_scanning: ["جاري قراءة المكتبة… {n} أغنية", "Reading the library… {n} songs"], lib_count: ["{n} أغنية", "{n} songs"],
  lib_empty: ["ما فيه أغاني في مجلد الحفظ بعد", "No songs in the output folder yet"],
  lib_dup_badge: ["مكررة", "Duplicate"], lib_add: ["أضف للقائمة", "Add to queue"], lib_delete: ["حذف", "Delete"],
  lib_confirm: ["تأكيد الحذف؟ (يروح لسلة المحذوفات)", "Delete? (goes to the Recycle Bin)"],
  s_new: ["الأحدث", "Newest"], s_title: ["الاسم", "Title"], s_artist: ["الفنان", "Artist"], s_dur: ["المدة", "Length"],
  lyrics: ["الكلمات", "Lyrics"], lyrics_loading: ["جاري البحث عن الكلمات…", "Looking for lyrics…"],
  lyrics_none: ["ما لقيت كلمات لهذي الأغنية", "No lyrics found for this song"],
  lyrics_src: ["الكلمات من LRCLIB", "Lyrics from LRCLIB"],
  eq: ["المعادل", "EQ"], eq_low: ["البيس", "Bass"], eq_mid: ["الوسط", "Mids"], eq_high: ["التريبل", "Treble"],
  crossfade: ["انتقال ناعم (ثانية)", "Crossfade (s)"], eq_reset: ["إرجاع للصفر", "Reset"],
  eq_note: ["يشتغل وقت التشغيل على أي أغنية، بدون ما يغيّر الملفات", "Applies live to any song without changing the files"],
  trim_label: ["قص الصمت في البداية والنهاية", "Trim silence at start and end"],
  trim_hint: ["الصمت الحقيقي فقط، ما يقص المقدمات الهادئة", "Only true silence; quiet intros are kept"],
  tray_label: ["تكمل الموسيقى لما تقفل النافذة", "Keep playing when the window is closed"],
  tray_hint: ["البرنامج يبقى في أيقونة جنب الساعة (كليك يمين عليها للإغلاق)", "The app stays in the icon next to the clock (right-click it to quit)"],
  log_label: ["سجل البرنامج", "App log"], log_hint: ["لو صار خطأ، انسخ السجل وأرسله", "If something goes wrong, copy the log and send it"],
  log_copy: ["نسخ السجل", "Copy log"], log_copied: ["تم النسخ ✓ (الصقه في الرسالة)", "Copied ✓ (paste it in your message)"],
  log_manual: ["ما قدرت أنسخ تلقائيًا: حدد النص تحت وانسخه", "Couldn't copy automatically: select the text below and copy it"],
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
  about: ["عن البرنامج", "About"], version: ["الإصدار", "Version"],
  auto_check: ["التحقق من التحديثات عند التشغيل", "Check for updates on launch"],
  updates: ["التحديثات", "Updates"],
  update_app: ["تحديث البرنامج", "Update the app"],
  update_now: ["حدّث الآن", "Update now"],
  checking: ["جاري التحقق…", "Checking…"],
  up_to_date: ["أنت على آخر إصدار ✓", "You're up to date ✓"],
  update_banner: ["يوجد إصدار جديد من البرنامج ({v}).", "A new version is available ({v})."],
  updating: ["جاري التحديث…", "Updating…"],
  update_restarting: ["تم التحديث، البرنامج يقفل ويفتح من جديد…", "Updated, the app is closing and reopening…"],
  downloading: ["جاري تنزيل التحديث… {p}%", "Downloading the update… {p}%"],
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
const S = { cfg: null, lang: "ar", files: [], cards: {}, state: null, view: "main", upd: null, bootChecked: false,
  seenDone: null, mini: false, tall: false };
const fmt = (s, p) => s.replace(/\{(\w+)\}/g, (_, k) => (p[k] === undefined ? "" : p[k]));
const t = (k, p = {}) => fmt((T[k] || [k, k])[S.lang === "en" ? 1 : 0], p);
const msg = (k, p) => MSG[k] ? fmt(MSG[k][S.lang === "en" ? 1 : 0], p || {}) : k;
const f1 = v => (v === null || v === undefined || isNaN(v)) ? "؟" : (+v).toFixed(1);
const PRESETS = ["auto", "gentle", "natural", "clean", "bass", "vocal", "ai_music", "ai_voice"];
const LUFS = [[-14, "n14"], [-16, "n16"], [-11, "n11"], [-9, "n9"], [0, "off"]];
const FORMATS = ["flac", "mp3", "m4a", "opus", "wav"];
const MEDIA_RE = /\.(mp3|m4a|aac|flac|wav|ogg|opus|wma|aiff?|ape|mka|mp4|mkv|webm|mov|avi|m4v|flv|wmv)$/i;

async function api(path, body) {
  const r = await fetch(path, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  return r.json();
}
const btn = (cls, text, onclick) => { const b = document.createElement("button"); b.className = cls; b.textContent = text; b.onclick = onclick; return b; };

// ======================= قوائم منسدلة بنمط iOS =======================
// الـ <select> الأصلي يبقى مخفي ويحفظ القيمة (فباقي الكود يقرأ .value عادي)، وفوقه زر وقائمة منسدلة ناعمة.
const DD = { open: null };
function fillSelect(sel, items) {   // items: [[value, labelKey, descKey]]
  const cur = sel.value;
  sel.innerHTML = items.map(([v, k]) => `<option value="${v}">${t(k)}</option>`).join("");
  sel._items = items;
  if (cur !== "" && items.some(([v]) => String(v) === cur)) sel.value = cur;
  makeDropdown(sel).refresh();
}
function makeDropdown(sel) {
  if (sel._dd) return sel._dd;
  const b = document.createElement("button");
  b.type = "button"; b.className = "dd-btn";
  b.innerHTML = '<span class="dd-label"></span><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M7 10l5 5 5-5"/></svg>';
  sel.classList.add("dd-native"); sel.after(b);
  const dd = { sel, b, refresh() { const o = sel.options[sel.selectedIndex]; b.querySelector(".dd-label").textContent = o ? o.textContent : ""; } };
  b.addEventListener("click", e => { e.stopPropagation(); DD.open && DD.open.anchor === b ? closeMenu() : openSelectMenu(dd); });
  sel.addEventListener("change", () => dd.refresh());
  sel._dd = dd;
  return dd;
}
function openSelectMenu(dd) {
  const items = (dd.sel._items || []).map(([v, k, dk]) => ({
    label: t(k), desc: dk ? t(dk) : "", checked: String(v) === dd.sel.value,
    run: () => { dd.sel.value = v; dd.sel.dispatchEvent(new Event("change")); },
  }));
  openMenu(dd.b, items, { withDesc: items.some(i => i.desc), minWidth: 300 });
}
function openMenu(anchor, items, opts = {}) {
  closeMenu();
  const m = document.createElement("div");
  m.className = "dd-menu"; m.setAttribute("role", "listbox");
  const list = document.createElement("div"); list.className = "dd-list";
  const desc = document.createElement("div"); desc.className = "dd-desc";
  let active = Math.max(0, items.findIndex(i => i.checked));
  const setActive = i => {
    active = i;
    [...list.children].forEach((el, k) => el.classList.toggle("hover", k === i));
    if (opts.withDesc) { desc.textContent = items[i] ? items[i].desc : ""; desc.hidden = !desc.textContent; }
  };
  items.forEach((it, i) => {
    const row = document.createElement("div");
    row.className = "dd-item" + (it.checked ? " on" : ""); row.setAttribute("role", "option");
    row.innerHTML = '<span class="dd-check">✓</span><span class="dd-text"></span>';
    row.querySelector(".dd-text").textContent = it.label;
    row.addEventListener("mouseenter", () => setActive(i));
    row.addEventListener("click", e => { e.stopPropagation(); closeMenu(); it.run(); });
    list.append(row);
  });
  m.append(list);
  if (opts.withDesc) m.append(desc);
  document.body.append(m);
  // المكان: تحت الزر (أو فوقه لو ما فيه مساحة)، ومحاذي لبداية الزر حسب اتجاه اللغة
  const r = anchor.getBoundingClientRect(), vw = innerWidth, vh = innerHeight;
  const w = Math.min(Math.max(r.width, opts.minWidth || 240), vw - 16);
  m.style.width = w + "px";
  const rtl = document.documentElement.dir === "rtl";
  let left = rtl ? r.right - w : r.left;
  left = Math.max(8, Math.min(left, vw - w - 8));
  m.style.left = left + "px";
  const h = m.offsetHeight;
  const below = vh - r.bottom - 8, above = r.top - 8;
  if (h <= below || below >= 260 || below >= above) { m.style.top = (r.bottom + 6) + "px"; m.style.maxHeight = (below - 6) + "px"; m.style.transformOrigin = "top"; }
  else { m.style.top = Math.max(8, r.top - 6 - Math.min(h, above)) + "px"; m.style.maxHeight = above + "px"; m.style.transformOrigin = "bottom"; }
  setActive(active);
  requestAnimationFrame(() => m.classList.add("open"));
  const onKey = e => {
    if (e.key === "Escape") closeMenu();
    else if (e.key === "ArrowDown") { e.preventDefault(); setActive((active + 1) % items.length); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActive((active - 1 + items.length) % items.length); }
    else if (e.key === "Enter") { e.preventDefault(); const it = items[active]; closeMenu(); if (it) it.run(); }
  };
  DD.open = { m, anchor, onKey };
  document.addEventListener("keydown", onKey, true);
  anchor.classList.add("dd-active");
}
function closeMenu() {
  const o = DD.open; if (!o) return;
  DD.open = null;
  document.removeEventListener("keydown", o.onKey, true);
  o.anchor.classList.remove("dd-active");
  o.m.classList.remove("open"); o.m.classList.add("closing");
  setTimeout(() => o.m.remove(), 160);
}
document.addEventListener("click", e => { if (DD.open && !DD.open.m.contains(e.target)) closeMenu(); });
window.addEventListener("resize", closeMenu);
document.addEventListener("scroll", e => { if (DD.open && !DD.open.m.contains(e.target)) closeMenu(); }, true);

const PRESET_ITEMS = PRESETS.map(k => [k, "p_" + k, "d_" + k]);
const FORMAT_ITEMS = FORMATS.map(k => [k, "f_" + k, "d_" + k]);
const LUFS_ITEMS = LUFS.map(([v, k]) => [v, "l_" + k, "dl_" + k]);

// ---------- اللغة والمظهر ----------
function applyLang() {
  const html = document.documentElement;
  html.lang = S.lang; html.dir = S.lang === "ar" ? "rtl" : "ltr";
  document.querySelectorAll("[data-i18n]").forEach(el => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll("[data-i18n-ph]").forEach(el => { el.placeholder = t(el.dataset.i18nPh); });
  fillSelect($("preset"), PRESET_ITEMS); fillSelect($("format"), FORMAT_ITEMS); fillSelect($("lufs"), LUFS_ITEMS);
  $("back").textContent = (S.lang === "ar" ? t("back") + "  ›" : "‹  " + t("back"));
  $("libBack").textContent = $("back").textContent;
  $("libBtn").title = t("library");
  fillSelect($("libSort"), [["new", "s_new"], ["title", "s_title"], ["artist", "s_artist"], ["dur", "s_dur"]]);
  if (S.view === "library") renderLibrary();
  const tips = { pmBtn: "player_mode", plAdd: "pl_add", plQueue: "pl_queue", plCorner: "pl_corner", plBack: "pl_back" };
  for (const id in tips) $(id).title = t(tips[id]);
  setFiles(S.files); showOut(); fillAbout(); showUpdBanner(); updatePin();
  for (const id in S.cards) { S.cards[id].done = false; refreshCard(id); }
  if (S.state) renderBanner(S.state);
  if (typeof updateNow === "function") updateNow();
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
["bass", "treble"].forEach(k => $(k).addEventListener("input", () => { $(k + "Val").textContent = (+$(k).value > 0 ? "+" : "") + $(k).value; }));
const tuning = () => ({ bass: +$("bass").value, treble: +$("treble").value, lufs: +$("lufs").value });
$("saveDefaults").onclick = async () => {
  await saveCfg({ preset: $("preset").value, format: $("format").value, ...tuning() });
  $("saveDefaults").textContent = t("saved");
  setTimeout(() => { $("saveDefaults").textContent = t("save_defaults"); }, 1500);
};

// ---------- إرسال (عدد الملفات بنفس الوقت تلقائي حسب قدرة الجهاز، والقوائم تُكتشف تلقائيًا) ----------
$("go").onclick = async () => {
  $("formErr").textContent = "";
  const lines = $("urls").value.split(/\n+/).map(l => l.trim()).filter(Boolean);
  const isLink = l => /^https?:\/\//.test(l) || /^spotify:/.test(l);
  const urls = lines.flatMap(l => l.split(/\s+/)).filter(isLink);
  const queries = lines.filter(l => !/https?:\/\/|spotify:/.test(l));   // اسم أغنية بدون رابط: نبحث عنها
  if (!urls.length && !queries.length && !S.files.length) { $("formErr").textContent = t("need_input"); return; }
  const base = { preset: $("preset").value, format: $("format").value, ...tuning() };
  $("go").disabled = true;
  try {
    if (urls.length || queries.length) await api("/api/submit", { urls, queries, ...base });
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
$("cleanOld").onclick = () => { $("cleanBox").hidden = !$("cleanBox").hidden; };
$("cleanCancel").onclick = () => { $("cleanBox").hidden = true; };
$("cleanGo").onclick = async () => {
  const r = await api("/api/clean", { days: Math.max(0, +$("cleanDays").value || 0) });
  $("cleanBox").hidden = true;
  $("outInfo").textContent = t("deleted", { n: r.deleted });
};

// ---------- بطاقات الأغاني ----------
// الأغاني اللي خلصت تنضغط لسطر واحد (ما تتكدس) وتروح للمشغّل؛ الضغط على السطر يفتح التفاصيل.
function stageText(k) { return k in MSG ? msg(k) : t(k || "waiting"); }
function errText(e) { return !e ? "" : (e.key ? msg(e.key, e.params) : t("unexpected", { e: e.text })); }

function makeCard(it) {
  const el = document.createElement("section");
  el.className = "card song";
  el.innerHTML = `<div class="top"><div class="name"></div><span class="badge" hidden></span><span class="top-btns"></span></div>
    <div class="stage sub"></div><div class="bar-track"><i></i></div><div class="err"></div>
    <div class="actions"></div><div class="res"></div>`;
  $("list").prepend(el);
  const c = S.cards[it.id] = { el, it, done: false, key: null, name: el.querySelector(".name"), badge: el.querySelector(".badge"),
    stage: el.querySelector(".stage"), track: el.querySelector(".bar-track"), bar: el.querySelector(".bar-track i"),
    err: el.querySelector(".err"), actions: el.querySelector(".actions"), res: el.querySelector(".res"), topBtns: el.querySelector(".top-btns") };
  el.querySelector(".top").addEventListener("click", e => {
    if (c.it.status === "done" && !e.target.closest("button")) el.classList.toggle("open");
  });
  return c;
}
function refreshCard(id) {
  const c = S.cards[id]; if (!c) return; const it = c.it;
  c.name.textContent = (it.result && it.result.title) || it.label;
  const done = it.status === "done", error = it.status === "error", canc = it.status === "cancelled";
  c.el.classList.toggle("done", done);
  c.track.hidden = done; c.stage.hidden = done;
  c.bar.style.width = it.pct + "%";
  c.track.classList.toggle("fail", error);
  c.stage.textContent = error ? t("failed") : canc ? t("cancelled") : it.status === "waiting" ? t("waiting")
    : it.live && it.stage_key === "st_record" ? (it.rec_bytes ? t("rec_status", { mb: (it.rec_bytes / 1048576).toFixed(1) }) : t("rec_wait"))
    : `${stageText(it.stage_key)} · ${it.pct}%`;
  if (it.live && it.status === "running" && it.stage_key === "st_record") c.bar.style.width = "100%";
  c.err.textContent = error ? errText(it.error) : "";
  const actKey = [it.status, it.can_stop, it.can_retry, canc, S.lang].join("|");
  if (c.actKey !== actKey) {   // نعيد بناء الأزرار فقط لما تتغير حالتها (وإلا الضغطة ممكن تضيع مع التحديث الدوري)
    c.actKey = actKey;
    c.actions.innerHTML = "";
    if (it.can_stop) c.actions.append(btn("tint", t("stop_rec"), () => api("/api/stop", { id: it.id })));
    if (it.status === "waiting" || it.status === "running") c.actions.append(btn("link", t("cancel"), () => api("/api/cancel", { id: it.id })));
    if ((error || canc) && it.can_retry) c.actions.append(btn("tint", t("retry"), () => api("/api/retry", { id: it.id }).then(poll)));
  }
  if (done) { renderResult(c); } else { c.badge.hidden = true; c.res.innerHTML = ""; c.topBtns.innerHTML = ""; c.done = false; c.audio = null; }
}
function renderResult(c) {
  const r = c.it.result, it = c.it;
  const key = r.output_name + "|" + S.lang + "|" + it.can_rerun;
  if (c.done && c.key === key) return;
  const wasPlaying = c.audio ? { t: c.audio.currentTime, paused: c.audio.paused, w: c.which } : null;
  c.key = key;
  c.badge.hidden = false; c.badge.className = "badge q-" + r.quality; c.badge.textContent = t("q_" + r.quality);
  c.topBtns.innerHTML = "";
  c.topBtns.append(btn("tint mini-btn", "▶", () => playResult(it.id)));
  const chev = btn("chev", "", () => c.el.classList.toggle("open")); chev.title = t("details"); c.topBtns.append(chev);
  const used = t("p_" + r.preset).replace(/ \(.*\)$/, "") + (r.auto ? t("auto_tag") : "");
  const src = r.codec + (r.bitrate_kbps ? " " + r.bitrate_kbps + "kbps" : "");
  c.res.innerHTML = `<div class="meta"></div>
    ${r.original_url ? `<div class="ab"><button class="tint" data-w="o"></button><button class="tint" data-w="e"></button><span class="sub"></span></div>` : ""}
    <audio controls preload="none"></audio>
    <div class="more"></div><div class="spec" hidden></div>`;
  c.res.querySelector(".meta").textContent =
    (it.cached ? t("cached_note") + "\n" : "") +
    (r.match ? t("from_src", { c: r.match.channel || "YouTube", t: r.match.title }) + "\n" : "") +
    (r.format_note === "twitch_opus" ? t("twitch_opus_note") + "\n" : "") +
    `${msg(r.reason_key, r.reason_params)}\n${t("source")}: ${src}  ·  ${t("preset_used")}: ${used}\n` +
    `${t("loudness")}: ${f1(r.lufs_before)} ← ${f1(r.lufs_after)} LUFS  ·  ${t("peak")}: ${f1(r.tp_before)} ← ${f1(r.tp_after)} dBTP`;
  const a = c.audio = c.res.querySelector("audio");
  const known = [r.lufs_before, r.lufs_after].filter(v => v !== null && v !== undefined);
  const target = known.length ? Math.min(...known) : null;
  const vol = l => (l === null || l === undefined || target === null) ? 1 : Math.min(1, Math.pow(10, (target - l) / 20));
  const sets = { e: [r.output_url, vol(r.lufs_after)], o: [r.original_url, vol(r.lufs_before)] };
  const pick = (w, keep) => {
    c.which = w; a.src = sets[w][0]; a.volume = sets[w][1];
    if (keep) a.addEventListener("loadedmetadata", () => { a.currentTime = keep.t; if (!keep.paused) a.play(); }, { once: true });
    c.res.querySelectorAll(".ab button").forEach(b => { b.style.outline = b.dataset.w === w ? "2px solid var(--blue)" : "none"; });
  };
  const ab = c.res.querySelector(".ab");
  if (ab) {
    ab.querySelector('[data-w="o"]').textContent = "▶ " + t("original");
    ab.querySelector('[data-w="e"]').textContent = "▶ " + t("enhanced");
    ab.querySelector(".sub").textContent = t("fair_ab");
    ab.querySelectorAll("button").forEach(b => b.onclick = () => pick(b.dataset.w, { t: a.currentTime, paused: a.paused }));
  }
  pick(wasPlaying ? wasPlaying.w : "e", wasPlaying);
  a.addEventListener("play", () => { if (!audio.paused) audio.pause(); });  // ما يشتغلون الاثنين مع بعض

  const more = c.res.querySelector(".more"), spec = c.res.querySelector(".spec");
  more.append(btn("link", "📂 " + t("show_folder"), () => api("/api/open", {})));
  if (it.can_next) {
    const nb = btn("link", "↻ " + t("not_this"), async () => { nb.disabled = true; nb.textContent = t("trying_next"); await api("/api/next_match", { id: it.id }); poll(); });
    more.append(nb);
  }
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
    const sel = document.createElement("select");
    const go = btn("tint", t("rerun_go"), async () => { go.disabled = true; await api("/api/reprocess", { id: it.id, preset: sel.value, format: r.format, ...tuning() }); go.disabled = false; poll(); });
    const wrap = document.createElement("div"); wrap.className = "rerun";
    const lbl = document.createElement("span"); lbl.className = "sub"; lbl.textContent = t("rerun");
    wrap.append(lbl, sel, go); more.append(wrap);
    fillSelect(sel, PRESET_ITEMS); sel.value = r.auto ? "auto" : r.preset; sel._dd.refresh();
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
  row.append(btn("tint", t("tags_save"), async () => {
    const r = await api("/api/tags", { id: it.id, title: fields.title.value, artist: fields.artist.value, album: fields.album.value });
    msgEl.textContent = r.ok ? t("tags_saved") : t("tags_failed");
  }));
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
  const firstRender = S.seenDone === null;
  if (firstRender) S.seenDone = new Set(items.filter(i => i.status === "done").map(i => i.id));  // اللي من السجل ما ينرسل
  for (const it of items) {
    const c = S.cards[it.id] || makeCard(it);
    c.it = it;
    refreshCard(it.id);
    if (it.status === "done" && !S.seenDone.has(it.id)) {
      S.seenDone.add(it.id);
      if (S.cfg && S.cfg.auto_player) sendToPlayer(it.id);
    }
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

// ---------- التنقل بين الصفحات ----------
let lastView = "main";
function show(view) {
  if (view !== "settings") lastView = view;
  S.view = view;
  $("main").hidden = view !== "main"; $("settings").hidden = view !== "settings"; $("player").hidden = view !== "player";
  $("library").hidden = view !== "library";
  $("gear").hidden = view === "settings"; $("libBtn").hidden = view === "library";
  if (view === "library") loadLibrary();
  closeMenu();
  window.scrollTo(0, 0);
  if (view === "settings") loadSettings();
}
$("gear").onclick = () => show("settings");
$("back").onclick = () => show(lastView === "player" || lastView === "library" ? "main" : lastView);
$("libBtn").onclick = () => show("library");
$("libBack").onclick = () => show("main");
$("repoLink").onclick = () => api("/api/open_repo", {});

function fillAbout() {
  if (!S.state) return;
  $("aboutLine").textContent = `${S.state.app} · ${t("version")} ${S.state.version}`;
  $("repoLink").hidden = !S.state.repo_url;
  $("quit").hidden = S.state.mode !== "browser";
}
async function loadSettings() {
  setSeg("langSeg", S.lang); setSeg("themeSeg", S.cfg.theme);
  $("lightMode").checked = S.cfg.light; $("keepOrig").checked = S.cfg.keep_original; $("notifyOn").checked = S.cfg.notify;
  $("autoCheck").checked = S.cfg.auto_check; $("autoPlayer").checked = S.cfg.auto_player;
  $("trimOn").checked = S.cfg.trim_silence; $("trayClose").checked = S.cfg.tray_close;
  $("trayRow").hidden = !(S.state && S.state.platform === "win32" && S.state.mode === "window");
  $("outPath").value = S.cfg.out;
  $("watchOn").checked = S.cfg.watch_on; $("watchPath").value = S.cfg.watch || "";
  fillAbout();
  const v = await api("/api/ytdlp/version", {});
  $("engStatus").textContent = v.version ? "yt-dlp " + v.version : "—";
}
bindSeg("langSeg", async v => { S.lang = v; await saveCfg({ lang: v }); applyLang(); loadSettings(); });
bindSeg("themeSeg", async v => { await saveCfg({ theme: v }); applyTheme(); });
$("keepOrig").onchange = e => saveCfg({ keep_original: e.target.checked });
$("autoPlayer").onchange = e => saveCfg({ auto_player: e.target.checked });
$("trimOn").onchange = e => saveCfg({ trim_silence: e.target.checked });
$("trayClose").onchange = e => saveCfg({ tray_close: e.target.checked });
$("logCopy").onclick = async () => {
  const text = await (await fetch("/api/log")).text();
  try { await navigator.clipboard.writeText(text); $("logStatus").textContent = t("log_copied"); $("logBoxRow").hidden = true; }
  catch (e) {   // النسخ التلقائي ممنوع: نعرض النص عشان ينسخه بنفسه
    $("logBox").value = text; $("logBoxRow").hidden = false; $("logBox").select(); $("logStatus").textContent = t("log_manual");
  }
};
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

// ---------- التحديث: ضغطة وحدة (يتحقق، ينزّل، يقفل البرنامج ويفتحه من جديد) ----------
function updError(r) { return (T["upd_err_" + r.error] ? t("upd_err_" + r.error) : r.error) + (r.detail ? ` (${r.detail})` : ""); }
function showUpdBanner() {
  const has = S.upd && S.upd.available;
  $("gearDot").hidden = !has; $("updBanner").hidden = !has;
  if (has) $("updBannerText").textContent = t("update_banner", { v: S.upd.latest });
}
async function checkUpdates(cached) {
  const r = await api("/api/update/check", { cached });
  if (!r.error) S.upd = r;
  showUpdBanner();
  return r;
}
function setUpdStatus(text) { $("updStatus").textContent = text; if (!$("updBanner").hidden) $("updBannerText").textContent = text; }
function waitForRestart(oldVersion) {
  const deadline = Date.now() + 120000;
  const wait = async () => {
    try {
      const r = await (await fetch("/api/ping")).json();
      if (r.version && r.version !== oldVersion) { location.reload(); return; }
    } catch (e) { /* البرنامج يعيد التشغيل */ }
    if (Date.now() < deadline) setTimeout(wait, 1500);
  };
  setTimeout(wait, 3000);
}
let updating = false;
async function updateApp() {
  if (updating) return;
  updating = true;
  $("updBtn").disabled = true; $("updBannerGo").disabled = true;
  try {
    setUpdStatus(t("checking"));
    const c = await checkUpdates(false);
    if (c.error) { setUpdStatus(updError(c)); return; }
    if (!c.available) { setUpdStatus(t("up_to_date") + `  (v${c.current})`); return; }
    setUpdStatus(t("updating")); $("updProgRow").hidden = false; $("updProgBar").style.width = "0%";
    const poller = setInterval(async () => {
      try {
        const p = await api("/api/update/progress");
        if (p.state === "download" && p.total) { const pc = Math.round(100 * p.done / p.total); $("updProgBar").style.width = pc + "%"; setUpdStatus(t("downloading", { p: pc })); }
      } catch (e) { /* البرنامج قفل للتحديث */ }
    }, 500);
    let r;
    try { r = await api("/api/update/apply", {}); } finally { clearInterval(poller); }
    if (!r.ok) { $("updProgRow").hidden = true; setUpdStatus(updError(r)); return; }
    $("updProgBar").style.width = "100%"; setUpdStatus(t("update_restarting"));
    if (!r.exit) await api("/api/restart", {});   // تثبيت من الكود: نعيد التشغيل بأنفسنا
    waitForRestart(S.state.version);
  } catch (e) {
    setUpdStatus(t("unexpected", { e: e.message }));
  } finally {
    updating = false; $("updBtn").disabled = false; $("updBannerGo").disabled = false;
  }
}
$("updBtn").onclick = updateApp;
$("updBannerGo").onclick = updateApp;
$("engUpdate").onclick = async () => {
  const b = $("engUpdate"); b.disabled = true; $("engStatus").textContent = t("updating");
  const r = await api("/api/update/ytdlp", {});
  b.disabled = false;
  $("engStatus").textContent = r.ok ? t("engine_updated", { a: "yt-dlp " + (r.after || "") }) : (r.error ? updError(r) : t("engine_failed") + (r.detail ? ` (${r.detail})` : ""));
};
$("quit").onclick = async () => { await api("/api/quit", {}); document.body.innerHTML = ""; window.close(); };

// ---------- المكتبة: كل الأغاني في مجلد الحفظ ----------
const L = { files: [], timer: null };
const libKey = f => {
  const base = (f.title || f.name.replace(/_enhanced( \(\d+\))?$/, "").replace(/ \(\d+\)$/, "")).toLowerCase().replace(/[^\p{L}\p{N}]+/gu, "");
  return base + "|" + (f.artist || "").toLowerCase().replace(/[^\p{L}\p{N}]+/gu, "");
};
async function loadLibrary() {
  clearTimeout(L.timer);
  try {
    const r = await api("/api/library");
    L.files = r.files; renderLibrary();
    $("libStatus").textContent = r.scanning ? t("lib_scanning", { n: r.files.length }) : t("lib_count", { n: r.files.length });
    if (r.scanning && S.view === "library") L.timer = setTimeout(loadLibrary, 1500);
  } catch (e) { /* */ }
}
function libVisible() {
  const q = $("libSearch").value.trim().toLowerCase();
  const groups = {};
  L.files.forEach(f => { const k = libKey(f); (groups[k] = groups[k] || []).push(f); });
  const dupOf = f => {   // نفس الاسم والفنان ومدة متقاربة (±3 ثواني)
    const g = groups[libKey(f)] || [];
    return g.some(o => o !== f && (!o.duration || !f.duration || Math.abs(o.duration - f.duration) <= 3));
  };
  let list = L.files.map(f => Object.assign(f, { dup: dupOf(f) }));
  if (q) list = list.filter(f => [f.title, f.artist, f.album, f.name].join(" ").toLowerCase().includes(q));
  if ($("libDups").checked) list = list.filter(f => f.dup);
  const sort = $("libSort").value;
  const name = f => (f.title || f.name).toLowerCase();
  list.sort(sort === "title" ? (a, b) => name(a).localeCompare(name(b)) : sort === "artist" ? (a, b) => (a.artist || "~").localeCompare(b.artist || "~") || name(a).localeCompare(name(b))
    : sort === "dur" ? (a, b) => (b.duration || 0) - (a.duration || 0) : (a, b) => b.mtime - a.mtime);
  return list;
}
function renderLibrary() {
  const ol = $("libList"); ol.innerHTML = "";
  const list = libVisible();
  if (!L.files.length) { ol.innerHTML = `<li class="empty">${t("lib_empty")}</li>`; return; }
  list.slice(0, 1000).forEach(f => {
    const li = document.createElement("li");
    li.innerHTML = '<div class="lt"><div class="ln"></div><div class="sub la"></div></div><span class="ld"></span><span class="lb"></span>';
    li.querySelector(".ln").textContent = f.title || f.name;
    li.querySelector(".la").textContent = [f.artist, f.album].filter(Boolean).join(" · ") + (f.dup ? "  ·  ⚠ " + t("lib_dup_badge") : "");
    li.querySelector(".ld").textContent = f.duration ? fmtTime(f.duration) : "";
    const b = li.querySelector(".lb");
    b.append(btn("tint mini-btn", "▶", () => libPlay([f.path], true)));
    const add = btn("ictl", "+", () => libPlay([f.path], false)); add.title = t("lib_add"); b.append(add);
    const del = btn("ictl danger", "🗑", async () => {
      if (!confirm(t("lib_confirm"))) return;
      const r = await api("/api/library/delete", { path: f.path });
      if (r.ok) { L.files = L.files.filter(x => x !== f); renderLibrary(); }
    });
    del.title = t("lib_delete"); b.append(del);
    ol.append(li);
  });
}
async function libPlay(paths, play) {
  const r = await api("/api/library/play", { paths });
  mergeTracks(r.tracks, null);
  if (play && r.index !== null && r.index !== undefined) { audioGraph(); playIndex(r.index); }
}
$("libSearch").addEventListener("input", renderLibrary);
$("libSort").addEventListener("change", renderLibrary);
$("libDups").addEventListener("change", renderLibrary);
$("libPlayAll").onclick = () => { const list = libVisible(); if (list.length) libPlay(list.map(f => f.path), true); };

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
      applyTheme();
      $("bass").value = s.config.bass; $("treble").value = s.config.treble;
      ["bass", "treble"].forEach(k => $(k).dispatchEvent(new Event("input")));
      fillSelect($("preset"), PRESET_ITEMS); $("preset").value = s.config.preset;
      fillSelect($("format"), FORMAT_ITEMS); $("format").value = s.config.format;
      fillSelect($("lufs"), LUFS_ITEMS); $("lufs").value = String(s.config.lufs);
      applyLang(); fillEq();
      if (new URLSearchParams(location.search).get("view") === "player") enterPlayer(true);
    }
    renderBanner(s); render(s.items); fillAbout();
    busy = s.items.some(i => i.status === "waiting" || i.status === "running");
    if (!S.bootChecked) {
      S.bootChecked = true;
      if (S.cfg.auto_check) checkUpdates(true).catch(() => { });
      api("/api/player/tracks").then(r => { if (r.tracks.length && !P.tracks.length) resumePlayer(r); }).catch(() => { });
    }
  } catch (e) { /* الخادم غير متاح مؤقتًا */ }
  timer = setTimeout(poll, document.hidden ? 30000 : busy ? 1000 : 4000);
}
document.addEventListener("visibilitychange", () => { if (!document.hidden) poll(); });

// ======================= المشغّل =======================
// عنصرين audio: واحد شغّال وواحد احتياط للانتقال الناعم (crossfade). كل الأحداث نتعامل معها من العنصر الشغّال فقط.
const P = { tracks: [], idx: -1, shuffle: false, repeat: "off", order: [], mode: "direct", seeking: false, fading: false, pane: "queue",
  lyrics: null, lyricsFor: null };
const EL = [$("audio"), $("audio2")];
let cur = EL[0];
const other = () => (cur === EL[0] ? EL[1] : EL[0]);
const MIME = { mp3: "audio/mpeg", m4a: "audio/mp4", aac: "audio/aac", wav: "audio/wav", flac: "audio/flac", ogg: "audio/ogg",
  opus: 'audio/ogg; codecs="opus"', webm: "audio/webm", weba: "audio/webm", mp4: "video/mp4" };
const canDirect = ext => !!MIME[ext] && cur.canPlayType(MIME[ext]) !== "";
const fmtTime = s => { if (!isFinite(s) || s < 0) return "0:00"; s = Math.floor(s); const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), x = s % 60; return (h ? h + ":" + String(m).padStart(2, "0") : m) + ":" + String(x).padStart(2, "0"); };
const trackName = tr => tr.title || tr.name;
const srcFor = (tr, mode) => tr.blob || `/play/${tr.id}` + (mode === "transcode" ? "?mode=transcode" : "");

// ---- المعادل (Web Audio): بيس / وسط / تريبل، يشتغل وقت التشغيل ----
const AX = { ctx: null, gains: [], filters: [] };
function audioGraph() {
  if (AX.ctx) { if (AX.ctx.state === "suspended") AX.ctx.resume().catch(() => { }); return AX.ctx; }
  try {
    const ctx = AX.ctx = new (window.AudioContext || window.webkitAudioContext)();
    const low = ctx.createBiquadFilter(); low.type = "lowshelf"; low.frequency.value = 120;
    const mid = ctx.createBiquadFilter(); mid.type = "peaking"; mid.frequency.value = 1200; mid.Q.value = 0.8;
    const high = ctx.createBiquadFilter(); high.type = "highshelf"; high.frequency.value = 7500;
    low.connect(mid); mid.connect(high); high.connect(ctx.destination);
    AX.filters = [low, mid, high];
    AX.gains = EL.map(el => { const src = ctx.createMediaElementSource(el); const g = ctx.createGain(); src.connect(g); g.connect(low); return g; });
    applyEq();
  } catch (e) { AX.ctx = null; }
  return AX.ctx;
}
function applyEq() {
  const eq = (S.cfg && S.cfg.eq) || [0, 0, 0];
  AX.filters.forEach((f, i) => { f.gain.value = eq[i] || 0; });
}
const gainOf = el => AX.gains[EL.indexOf(el)];
function setGain(el, v) { const g = gainOf(el); if (g) { g.gain.cancelScheduledValues(0); g.gain.value = v; } }

// ---- وضع المشغّل: النافذة تصير مستطيل صغير قرب زاوية الشاشة (مو ملصوق بالحافة) ----
function windowMode(mode) { return api("/api/window/mode", { mode, corner: (S.cfg && S.cfg.mini_corner) || "bottom" }).catch(() => ({})); }
function setPane(name) {
  P.pane = name; setSeg("qTabs", name);
  $("paneQueue").hidden = name !== "queue"; $("paneLyrics").hidden = name !== "lyrics"; $("paneEq").hidden = name !== "eq";
  if (name === "lyrics") loadLyrics();
}
bindSeg("qTabs", setPane);
function enterPlayer(already) {
  S.mini = true;
  S.tall = !P.tracks.length;   // قائمة فاضية: نفتح القائمة عشان يبان زر الإضافة والشرح
  document.body.classList.add("mini");
  $("qWrap").hidden = !S.tall; $("plQueue").classList.toggle("on", S.tall);
  setPane(P.pane);
  show("player");
  if (!already || S.tall) windowMode(S.tall ? "mini_tall" : "mini");
}
function exitPlayer() {
  S.mini = false;
  document.body.classList.remove("mini");
  show("main");
  windowMode("full");
}
$("pmBtn").onclick = () => enterPlayer(false);
$("plBack").onclick = exitPlayer;
$("plQueue").onclick = () => {
  S.tall = !S.tall;
  $("qWrap").hidden = !S.tall; $("plQueue").classList.toggle("on", S.tall);
  windowMode(S.tall ? "mini_tall" : "mini");
};
$("plCorner").onclick = async () => {
  await saveCfg({ mini_corner: S.cfg.mini_corner === "top" ? "bottom" : "top" });
  windowMode(S.tall ? "mini_tall" : "mini");
};
function updatePin() {
  const on = !!(S.cfg && S.cfg.start_player);
  $("pmPin").classList.toggle("on", on);
  $("pmPin").title = t(on ? "pin_on" : "pin_off");
}
$("pmPin").onclick = async e => { e.stopPropagation(); await saveCfg({ start_player: !S.cfg.start_player }); updatePin(); };

// ---- القائمة ----
function rebuildOrder() {
  const n = P.tracks.length, idx = [...Array(n).keys()];
  if (P.shuffle) { for (let i = n - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [idx[i], idx[j]] = [idx[j], idx[i]]; } }
  if (P.shuffle && P.idx >= 0) { const k = idx.indexOf(P.idx); if (k > 0) { idx.splice(k, 1); idx.unshift(P.idx); } }
  P.order = idx;
}
function renderQueue() {
  const ol = $("queue"); ol.innerHTML = "";
  P.tracks.forEach((tr, i) => {
    const li = document.createElement("li"); li.className = i === P.idx ? "cur" : ""; li.dataset.i = i;
    li.innerHTML = '<span class="n"></span><span class="t"></span><span class="d"></span>';
    li.children[0].textContent = i === P.idx ? "▶" : i + 1; li.children[1].textContent = trackName(tr);
    li.children[2].textContent = tr.duration ? fmtTime(tr.duration) : "";
    li.onclick = () => { audioGraph(); playIndex(i); };
    ol.append(li);
  });
  $("plEmpty").hidden = P.tracks.length > 0;
}
function updateNow() {
  const tr = P.tracks[P.idx];
  $("npTitle").textContent = tr ? trackName(tr) : t("pl_nothing");
  $("npArtist").textContent = tr ? [tr.artist, tr.album].filter(Boolean).join(" · ") : "";
  const img = $("npCover");
  if (tr && tr.has_cover && !tr.blob) { img.src = "/api/player/cover?id=" + encodeURIComponent(tr.id); img.hidden = false; $("npIcon").hidden = true; }
  else { img.hidden = true; $("npIcon").hidden = false; }
  if ("mediaSession" in navigator && tr) {
    try { navigator.mediaSession.metadata = new MediaMetadata({ title: trackName(tr), artist: tr.artist || "", album: tr.album || "" }); } catch (e) { /* غير مدعوم */ }
  }
  if (P.pane === "lyrics" && S.tall) loadLyrics();
}
async function loadMeta(i) {
  const tr = P.tracks[i]; if (!tr || tr.blob || tr.meta) return;
  tr.meta = true;
  try { Object.assign(tr, await api("/api/player/meta?id=" + encodeURIComponent(tr.id))); } catch (e) { return; }
  const li = $("queue").children[i];
  if (li) { li.children[1].textContent = trackName(tr); li.children[2].textContent = tr.duration ? fmtTime(tr.duration) : ""; }
  if (i === P.idx) updateNow();
}
function setSrc(tr, mode, startAt) {
  P.mode = mode;
  cur.src = srcFor(tr, mode);
  if (mode === "transcode") $("npArtist").textContent = t("pl_preparing");
  if (startAt) cur.addEventListener("loadedmetadata", () => { cur.currentTime = startAt; }, { once: true });
}
function playIndex(i, opts = {}) {
  if (i < 0 || i >= P.tracks.length) return;
  P.fading = false;
  other().pause(); setGain(other(), 0); setGain(cur, 1);
  P.idx = i; const tr = P.tracks[i];
  rebuildOrder(); renderQueue(); updateNow();
  setSrc(tr, tr.blob || canDirect(tr.ext) ? "direct" : "transcode", opts.at);
  if (!opts.paused) cur.play().catch(() => { });
  loadMeta(i).then(() => { for (let k = 1; k <= 2; k++) loadMeta((i + k) % P.tracks.length); });
  const li = $("queue").children[i]; if (li && li.scrollIntoView) li.scrollIntoView({ block: "nearest" });
  savePlayer();
}
function step(delta) {
  if (!P.tracks.length) return null;
  const pos = P.order.indexOf(P.idx), np = pos + delta;
  if (np >= 0 && np < P.order.length) return P.order[np];
  if (P.repeat === "all") return P.order[(np + P.order.length) % P.order.length];
  return null;
}
function next() { const i = step(1); if (i !== null) playIndex(i); else cur.pause(); }
function prev() {
  if (cur.currentTime > 3) { cur.currentTime = 0; return; }
  const i = step(-1); if (i !== null) playIndex(i); else cur.currentTime = 0;
}
const idle = () => P.idx < 0 || cur.ended || !cur.src;
function mergeTracks(tracks, playAt) {
  const was = P.tracks[P.idx];
  const known = {}; P.tracks.forEach(tr => { known[tr.id] = tr; });
  P.tracks = tracks.map(tr => Object.assign(known[tr.id] || {}, tr));
  P.idx = was ? P.tracks.findIndex(tr => tr.id === was.id) : -1;
  rebuildOrder(); renderQueue();
  if (playAt !== undefined && playAt !== null && playAt >= 0 && idle()) playIndex(playAt);
}

// ---- الانتقال الناعم: قبل نهاية الأغنية بـ N ثانية، الجاية تبدأ والحالية تختفي تدريجيًا ----
function maybeCrossfade() {
  const cf = (S.cfg && S.cfg.crossfade) || 0;
  if (!cf || P.fading || P.repeat === "one" || !AX.ctx || !cur.duration || cur.paused) return;
  const left = cur.duration - cur.currentTime;
  if (left > cf || left < 0.3) return;
  const ni = step(1); if (ni === null) return;
  const tr = P.tracks[ni]; if (!tr) return;
  P.fading = true;
  const old = cur, nxt = other(), now = AX.ctx.currentTime;
  nxt.src = srcFor(tr, tr.blob || canDirect(tr.ext) ? "direct" : "transcode");
  const go = gainOf(old), gn = gainOf(nxt);
  gn.gain.cancelScheduledValues(now); gn.gain.setValueAtTime(0, now); gn.gain.linearRampToValueAtTime(1, now + left);
  go.gain.cancelScheduledValues(now); go.gain.setValueAtTime(go.gain.value, now); go.gain.linearRampToValueAtTime(0, now + left);
  nxt.play().catch(() => { });
  cur = nxt; P.idx = ni; P.mode = tr.blob || canDirect(tr.ext) ? "direct" : "transcode";
  rebuildOrder(); renderQueue(); updateNow(); savePlayer();
  loadMeta(ni);
  setTimeout(() => { old.pause(); P.fading = false; }, left * 1000 + 200);
}

// ---- الأحداث (من العنصر الشغّال فقط) ----
const fromCur = fn => e => { if (e.target === cur) fn(e); };
EL.forEach(el => {
  el.addEventListener("ended", fromCur(() => { if (P.repeat === "one") { cur.currentTime = 0; cur.play(); } else next(); }));
  el.addEventListener("error", fromCur(() => {
    const tr = P.tracks[P.idx]; if (!tr || !cur.src) return;
    if (P.mode === "direct" && !tr.blob) { setSrc(tr, "transcode"); cur.play().catch(() => { }); return; }  // المتصفح ما يشغّل الصيغة: نحوّلها مؤقتًا
    $("npArtist").textContent = t("pl_failed");
    setTimeout(() => { if (P.tracks[P.idx] === tr) next(); }, 1500);
  }));
  el.addEventListener("playing", fromCur(() => { const tr = P.tracks[P.idx]; if (tr) $("npArtist").textContent = [tr.artist, tr.album].filter(Boolean).join(" · "); setPlayIcon(true); }));
  el.addEventListener("pause", fromCur(() => { setPlayIcon(false); savePlayer(); }));
  el.addEventListener("timeupdate", fromCur(() => {
    const d = cur.duration || (P.tracks[P.idx] && P.tracks[P.idx].duration) || 0;
    $("tCur").textContent = fmtTime(cur.currentTime); $("tDur").textContent = fmtTime(d);
    if (!P.seeking && d) $("seek").value = Math.round(1000 * cur.currentTime / d);
    syncLyrics(cur.currentTime);
    maybeCrossfade();
    if (Date.now() - (P.savedAt || 0) > 5000) savePlayer();
  }));
  el.addEventListener("loadedmetadata", fromCur(() => { $("tDur").textContent = fmtTime(cur.duration); }));
});
const setPlayIcon = playing => { $("icoPlay").hidden = playing; $("icoPause").hidden = !playing; };
$("seek").addEventListener("input", () => { P.seeking = true; const d = cur.duration; if (d) $("tCur").textContent = fmtTime(d * $("seek").value / 1000); });
$("seek").addEventListener("change", () => { const d = cur.duration; if (d) cur.currentTime = d * $("seek").value / 1000; P.seeking = false; });
function togglePlay() {
  audioGraph();
  if (P.idx < 0 && P.tracks.length) playIndex(0);
  else if (cur.paused) { if (!cur.src && P.tracks[P.idx]) playIndex(P.idx); else cur.play().catch(() => { }); }
  else cur.pause();
}
$("btnPlay").onclick = togglePlay;
// المعادل يبدأ فقط بضغطة من المستخدم (المتصفح يمنع الصوت في Web Audio بدون تفاعل، فالتشغيل التلقائي يبقى عادي)
$("btnNext").onclick = () => { audioGraph(); next(); }; $("btnPrev").onclick = () => { audioGraph(); prev(); };
$("btnShuffle").onclick = () => { P.shuffle = !P.shuffle; $("btnShuffle").classList.toggle("on", P.shuffle); rebuildOrder(); };
$("btnRepeat").onclick = () => {
  P.repeat = P.repeat === "off" ? "all" : P.repeat === "all" ? "one" : "off";
  $("rep1").hidden = P.repeat !== "one"; $("btnRepeat").classList.toggle("on", P.repeat !== "off");
};
try { const v = localStorage.getItem("msga_vol"); if (v !== null) $("vol").value = v; } catch (e) { /* التخزين غير متاح */ }
EL.forEach(el => { el.volume = $("vol").value / 100; });
$("vol").addEventListener("input", () => { EL.forEach(el => { el.volume = $("vol").value / 100; }); try { localStorage.setItem("msga_vol", $("vol").value); } catch (e) { /* */ } });
document.addEventListener("keydown", e => {
  if (S.view !== "player" || DD.open || (/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName) && e.target.type !== "range")) return;
  if (e.code === "Space") { e.preventDefault(); togglePlay(); }
  else if (e.shiftKey && e.code === "ArrowRight") next();
  else if (e.shiftKey && e.code === "ArrowLeft") prev();
});
// أزرار الوسائط: من ويندوز (حتى لو البرنامج مو قدامك) أو من المتصفح
window.mediaKey = name => { if (name === "toggle") togglePlay(); else if (name === "next") next(); else if (name === "prev") prev(); else if (name === "stop") cur.pause(); };
if ("mediaSession" in navigator) {
  const set = (a, f) => { try { navigator.mediaSession.setActionHandler(a, f); } catch (e) { /* */ } };
  set("play", togglePlay); set("pause", () => cur.pause()); set("previoustrack", prev); set("nexttrack", next);
}

// ---- يتذكر مكانه: القائمة والأغنية والثانية ----
function savePlayer() {
  const tr = P.tracks[P.idx];
  if (tr && tr.blob) return;
  P.savedAt = Date.now();
  api("/api/player/save", { idx: P.idx, pos: cur.currentTime || 0 }).catch(() => { });
}
function resumePlayer(r) {
  P.tracks = r.tracks; renderQueue();
  const res = r.resume || {};
  if (res.idx >= 0 && res.idx < P.tracks.length) {
    P.idx = res.idx; rebuildOrder(); renderQueue(); updateNow();
    const tr = P.tracks[P.idx];
    setSrc(tr, canDirect(tr.ext) ? "direct" : "transcode", res.pos > 1 ? res.pos : 0);   // جاهز بنفس المكان، بدون تشغيل تلقائي
    if (P.mode === "transcode") $("npArtist").textContent = "";
    loadMeta(P.idx);
  } else updateNow();
}

// ---- الكلمات (LRCLIB): متزامنة، والضغط على سطر ينقلك له ----
function parseLrc(text) {
  const out = [];
  (text || "").split(/\r?\n/).forEach(line => {
    const tags = [...line.matchAll(/\[(\d+):(\d+(?:\.\d+)?)\]/g)];
    const words = line.replace(/\[[^\]]*\]/g, "").trim();
    tags.forEach(m => out.push({ t: +m[1] * 60 + +m[2], text: words }));
  });
  return out.sort((a, b) => a.t - b.t);
}
async function loadLyrics() {
  const tr = P.tracks[P.idx], box = $("paneLyrics");
  if (!tr || tr.blob) { box.innerHTML = `<div class="empty">${t(tr ? "lyrics_none" : "pl_nothing")}</div>`; P.lyrics = null; return; }
  if (P.lyricsFor === tr.id) return;
  P.lyricsFor = tr.id; P.lyrics = null;
  box.innerHTML = `<div class="empty">${t("lyrics_loading")}</div>`;
  let r; try { r = await api("/api/player/lyrics?id=" + encodeURIComponent(tr.id)); } catch (e) { r = { none: true }; }
  if (P.lyricsFor !== tr.id) return;
  box.innerHTML = "";
  if (r.synced) {
    P.lyrics = parseLrc(r.synced);
    P.lyrics.forEach((l, i) => {
      const d = document.createElement("div"); d.className = "lline"; d.textContent = l.text || "♪"; d.dataset.i = i;
      d.onclick = () => { cur.currentTime = l.t + 0.01; };
      box.append(d);
    });
  } else if (r.plain) {
    const d = document.createElement("div"); d.className = "lplain"; d.textContent = r.plain; box.append(d);
  } else { box.innerHTML = `<div class="empty">${t("lyrics_none")}</div>`; return; }
  const src = document.createElement("div"); src.className = "sub lsrc"; src.textContent = t("lyrics_src"); box.append(src);
  syncLyrics(cur.currentTime);
}
function syncLyrics(time) {
  if (!P.lyrics || P.pane !== "lyrics" || $("qWrap").hidden) return;
  let k = -1;
  for (let i = 0; i < P.lyrics.length; i++) { if (P.lyrics[i].t <= time + 0.15) k = i; else break; }
  if (k === P.lyricsLine) return;
  P.lyricsLine = k;
  const box = $("paneLyrics");
  box.querySelectorAll(".lline.on").forEach(el => el.classList.remove("on"));
  const el = box.querySelector(`.lline[data-i="${k}"]`);
  if (el) { el.classList.add("on"); el.scrollIntoView({ block: "center", behavior: "smooth" }); }
}

// ---- المعادل + الانتقال الناعم: الإعدادات ----
function fillEq() {
  const eq = (S.cfg && S.cfg.eq) || [0, 0, 0];
  [0, 1, 2].forEach(i => { $("eq" + i).value = eq[i]; $("eq" + i + "v").textContent = (eq[i] > 0 ? "+" : "") + eq[i]; });
  $("xfade").value = (S.cfg && S.cfg.crossfade) || 0; $("xfadev").textContent = $("xfade").value;
}
let eqSave = null;
[0, 1, 2].forEach(i => $("eq" + i).addEventListener("input", () => {
  const eq = [0, 1, 2].map(k => +$("eq" + k).value);
  S.cfg.eq = eq; $("eq" + i + "v").textContent = (eq[i] > 0 ? "+" : "") + eq[i];
  audioGraph(); applyEq();
  clearTimeout(eqSave); eqSave = setTimeout(() => saveCfg({ eq }), 400);
}));
$("xfade").addEventListener("input", () => {
  S.cfg.crossfade = +$("xfade").value; $("xfadev").textContent = $("xfade").value;
  clearTimeout(eqSave); eqSave = setTimeout(() => saveCfg({ crossfade: +$("xfade").value }), 400);
});
$("eqReset").onclick = async () => { await saveCfg({ eq: [0, 0, 0], crossfade: 0 }); fillEq(); applyEq(); };

// ---- زر + : إضافة أغاني / مجلد / قائمة m3u (تنضاف للقائمة بدون ما تمسح الموجود) ----
async function plAdd(kind) {
  const before = P.tracks.length;
  let r; try { r = await api("/api/player/open", { kind, append: true }); } catch (e) { r = { error: "x" }; }
  if (r.error) { $("plInput").click(); return; }   // ما فيه نافذة اختيار: نرجع لمتصفح الملفات
  mergeTracks(r.tracks, r.tracks.length > before ? before : null);
}
$("plAdd").onclick = e => {
  e.stopPropagation();
  if (DD.open && DD.open.anchor === $("plAdd")) { closeMenu(); return; }
  openMenu($("plAdd"), [
    { label: t("pl_add_files"), run: () => plAdd("files") },
    { label: t("pl_add_folder"), run: () => plAdd("folder") },
    { label: t("pl_add_list"), run: () => plAdd("files") },
    { label: t("pl_clear"), run: async () => { await api("/api/player/clear", {}); EL.forEach(el => { el.pause(); el.removeAttribute("src"); }); P.tracks = []; P.idx = -1; renderQueue(); updateNow(); } },
  ], { minWidth: 220 });
};
$("plInput").addEventListener("change", e => {
  const files = [...e.target.files].filter(f => MEDIA_RE.test(f.name));
  const base = P.tracks.length;
  const extra = files.map((f, i) => ({ id: "blob" + Date.now() + i, name: f.name.replace(/\.[^.]+$/, ""), ext: (f.name.split(".").pop() || "").toLowerCase(), blob: URL.createObjectURL(f) }));
  P.tracks = P.tracks.concat(extra); rebuildOrder(); renderQueue();
  if (extra.length && idle()) playIndex(base);
});
// أغنية خلصت تحسينها: تنضاف لقائمة المشغّل، وتشتغل لو المشغّل فاضي
async function sendToPlayer(itemId) {
  try {
    const r = await api("/api/player/add_item", { id: itemId });
    if (!r.error) mergeTracks(r.tracks, r.index);
  } catch (e) { /* */ }
}
async function playResult(itemId) {
  const r = await api("/api/player/add_item", { id: itemId });
  if (r.error) return;
  mergeTracks(r.tracks, null);
  audioGraph(); playIndex(r.index);
  enterPlayer(false);
}

poll();
