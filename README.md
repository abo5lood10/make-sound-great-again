# Make Sound Great Again

<p align="center"><img src="assets/icon.png" width="120" alt="icon"></p>

Paste a link (YouTube, TikTok, Instagram, …) or drop a file, and get a cleaner, better-sounding copy of the song.
Works on **Windows, macOS and Linux**. Arabic and English interface, light and dark mode.

الصق رابط أغنية (يوتيوب، تيكتوك، انستا …) أو اسحب ملف، ويطلع لك نسخة أنظف وأوضح.
يشتغل على **ويندوز وماك ولينكس**، بواجهة عربية وإنجليزية ومود فاتح وداكن.

## What it does

- Downloads the best available audio (or reads your local file).
- **Detects the source quality** (bitrate, lossless or not, missing high frequencies) and picks a preset automatically.
- Noise reduction, EQ, gentle harmonic "air", and **two-pass loudness normalization** (-14 LUFS) with a limiter.
- Saves **FLAC** (lossless) or **MP3 320**, keeping the cover art and tags.
- **A/B player** at equal loudness: compare the original and the enhanced version.
- Playlists, parallel jobs, progress bars, clear error messages.
- **Cancel** or **retry** any song; your **history survives restarts**; a link you already processed with the same settings isn't redone.
- **Try another preset** on a finished song without downloading again, and **fine-tune bass / treble** (±6 dB).
- **Spectrogram** (before / after) to *see* what changed, not just hear it.
- Formats: **FLAC, MP3 320, M4A (AAC 256), Opus 192, WAV 24-bit**.
- **Notification** when everything is done; paste a link from the clipboard; `Ctrl+Enter` to start.
- **Paste any link in the box**: YouTube, TikTok, SoundCloud, Instagram, and **Spotify songs, albums and playlists**. Playlists are detected automatically; everything is downloaded as audio only, enhanced and saved into the folder you chose in Settings. (Spotify's own audio is protected, so for Spotify links the app reads the song names from the public page and downloads each song from YouTube, picking the result with the same length. Public Spotify pages list up to about 50-100 songs of a long playlist.) By default only the enhanced audio is kept (no second "original" copy), to save disk space.
- **Player mode**: the headphones button (next to Settings) turns the window into a small rectangle near a screen corner (top or bottom, kept away from the very edge), always on top, with previous / play / next, seek, volume, shuffle, repeat, a queue you can expand, and a button back to the enhancer. The little pin on that button makes the app **open straight in player mode**. The **+** button adds songs, a whole folder or an `.m3u` playlist to the queue.
- **Enhanced songs go to the player** automatically (and start playing if nothing is playing); finished results collapse to one line instead of piling up.
- **iOS-style menus** for preset / format / loudness, with an explanation of each option on hover. The number of songs processed at once is chosen automatically for your computer.
- **One-click update**: *Settings → Update the app* (or the banner) checks, downloads, verifies, closes and reopens the app by itself.
- **Smarter song matching** for Spotify links and typed song names (just type `Artist - Title`, no link needed): results from YouTube Music's official songs and "- Topic" channels win; live, cover, remix, sped-up/slowed, karaoke and other versions are pushed down; if the downloaded length doesn't match, the next candidate is tried. Each result shows which channel it came from, with a **"Not this song"** button that swaps in the next candidate.
- **The player remembers** its queue, song and position after a restart; **keyboard media keys** work even when the app isn't in front (Windows); an **icon next to the clock** (play / pause / next / show / quit) and an option to keep playing when the window is closed.
- **Synced lyrics** (from the free, open LRCLIB database), a **live EQ** (bass / mids / treble) and **crossfade** in the player.
- **Library**: every song in your output folder with search, sorting, duplicate detection, play / add to queue, and delete (to the Recycle Bin).
- **Trim silence** at the start and end (true silence only), and **Copy log** in Settings for reporting problems.
- **Twitch** (paste the link): past broadcasts (VODs), clips, and **live streams**. Always **audio only**, saved in the stream's **original format** (its AAC track copied as-is into an `.m4a`: no enhancement, no re-encoding, same quality as the broadcast). For a live stream the card shows a red "Recording…" counter with a **Stop & save** button; whatever was recorded so far is saved (the recording is plain AAC, so it survives being stopped at any moment). A switch in Settings ("Twitch: audio only, original format") turns that off if you'd rather enhance Twitch audio like any other song. Channel / list pages are refused with a clear message (paste a single VOD or clip). Subscriber-only broadcasts can't be downloaded.
- **Built-in player**: open files or a folder from your computer and it plays everything in order, with previous / next, seek, volume, shuffle and repeat. Plays **every format** (formats the system can't play natively are converted on the fly with ffmpeg) and **videos play their audio only**.
- **Choose files or a whole folder** from the system dialog: songs are processed in place (your originals are never copied or moved), videos are turned into audio.
- **Watch a folder**: new songs dropped into it are enhanced automatically (existing files are left alone).
- **Edit tags** (title / artist / album) and **change the cover** of a finished song, without re-encoding.
- **Target loudness**: -14 LUFS (Spotify / YouTube), -16 (Apple Music), -11, -9, or leave the level alone.
- **AI noise removal** (light, local): RNNoise models through ffmpeg's `arnndn`, one for music and one for speech. Only used when you pick them.

> It can't bring back detail a low-quality source never had (a 64 kbps clip gets cleaner and clearer, not studio quality).

## Light on your computer

- Pure Python standard library for the app itself: no heavy GUI toolkit, no Electron (the window reuses the webview already in your OS).
- The heavy work runs at **low CPU priority** by default (Settings → Light mode).
- Polls rarely while idle, closing the window quits the app, and in browser mode it **quits by itself** when the page is closed.

## Install

### Windows: just download the app (no Python, no ffmpeg install)

Go to the **[Releases](../../releases/latest)** page and download either:

- **`Make-Sound-Great-Again-Setup.exe`**: a normal installer (per-user, no admin rights, Start menu + optional desktop shortcut, uninstaller), or
- `Make-Sound-Great-Again-windows.zip`: portable; extract it and double-click **`Make Sound Great Again.exe`**.

ffmpeg is already inside. **Updates install themselves** from inside the app (Settings → Check for updates → Update): it downloads the new version, verifies its SHA-256, replaces its own files and restarts. (Windows needs the Edge WebView2 runtime, already present on Windows 10/11.)
Windows SmartScreen may warn about an unsigned app: *More info → Run anyway*.

### From source (all systems)

You need **Python 3.8+** and **ffmpeg** (with ffprobe). `yt-dlp` and the window library are installed for you by the start scripts.

| OS | ffmpeg | Start |
|---|---|---|
| Windows | `winget install ffmpeg` | double-click `start.bat` |
| macOS | `brew install ffmpeg` | double-click `start.command` (first time: `chmod +x start.command`) |
| Linux | `sudo apt install ffmpeg` | `./start.sh` (optional: `scripts/install_linux_shortcut.sh` for a desktop icon) |

Or by hand:

```bash
pip install -r requirements.txt
python run.py
```

The app is a **real desktop app with its own window**, never a browser tab. On Windows/macOS the window comes from `pywebview` (installed by `pip install -r requirements.txt`; Windows also needs the Edge WebView2 runtime, already present on Windows 10/11), on Linux from the system's GTK + WebKit2 (`sudo apt install gir1.2-webkit2-4.0` if missing). On Windows/macOS it never falls back to the browser: if the window can't start you get an error message saying why. (`python run.py --browser` forces browser mode if you ever want it.)

> macOS tip: if Python (from python.org) reports certificate errors, run "Install Certificates.command" once, or `pip install certifi`.

### Command line

```bash
python -m msga.cli "https://www.youtube.com/watch?v=XXXX"
python -m msga.cli song.mp3 -p bass -f mp3
python -m msga.cli --playlist "https://www.youtube.com/playlist?list=XXXX" -j 2
```

## Settings

Open the gear icon: language (العربية / English), appearance (System / Light / Dark), light mode, output folder,
**version number and one-click updates**, and an "Update engine" button for yt-dlp (YouTube changes often; this fixes most download failures).

Your settings live outside the program folder (`%APPDATA%\MakeSoundGreatAgain`, `~/Library/Application Support/MakeSoundGreatAgain`, `~/.config/make-sound-great-again`), so updating never touches them. Default output: `Music/Make Sound Great Again`.

## Updates

The app **checks for updates when it starts** (a red dot appears on the gear icon; turn it off in Settings), and if a download fails it **updates yt-dlp by itself and retries once**.
Manual: *Settings → Check for updates → Update → Restart.* The app reads `msga/version.py` on this repository's `main` branch and, if the number is higher, downloads the new files (or runs `git pull` if you cloned it).
To release a new version: bump `VERSION` in `msga/version.py` and push to `main`.
If you fork it, set your own repo with `python scripts/set_repo.py YOUR_USERNAME` (a git clone detects it automatically).

## Standalone builds (no Python needed)

Pushing a version tag builds the apps on GitHub and attaches them to a release (the Windows build bundles an LGPL ffmpeg, checksum-verified in CI; the macOS build needs `brew install ffmpeg`):

```bash
git tag v1.1.0 && git push origin v1.1.0
```

Packaged builds update by downloading the new release (the app opens the download page for you). The release workflow smoke-tests each build before publishing.

## Fonts

- The title uses **Audiowide** (SIL OFL 1.1, bundled, see `msga/web/fonts`).
- Arabic text uses the **Thmanyah (ثمانية) font**. The Windows build embeds it in obfuscated form, which its license allows for packaged software. The font files are **not** in this repository and must not be redistributed: they reach the build only through encrypted repository secrets. When you run from source, the app uses Thmanyah if it's installed on your system, and otherwise a fallback font.

## Development

```bash
python -m unittest discover -s tests -v
```

CI runs the tests on Windows, macOS and Linux for every push.

## Legal

Download only what you have the right to use (this includes streamers' broadcasts: respect their rights and Twitch's terms). You are responsible for how you use this tool and for respecting the terms of the sites and the copyright of the content.

MIT licensed (see `LICENSE`).
