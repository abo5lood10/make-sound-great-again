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

> It can't bring back detail a low-quality source never had (a 64 kbps clip gets cleaner and clearer, not studio quality).

## Light on your computer

- Pure Python standard library: no heavy GUI toolkit, no Electron.
- The heavy work runs at **low CPU priority** by default (Settings → Light mode).
- Polls rarely while idle, and in browser mode it **quits by itself** when the page is closed.

## Install

You need **Python 3.8+** and **ffmpeg** (with ffprobe), plus `yt-dlp` (installed for you by the start scripts).

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

Want a standalone window instead of the browser tab? `pip install -r requirements-window.txt` (pywebview). Force the browser with `python run.py --browser`.

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

*Settings → Check for updates → Update → Restart.* The app reads `msga/version.py` on this repository's `main` branch and, if the number is higher, downloads the new files (or runs `git pull` if you cloned it).
To release a new version: bump `VERSION` in `msga/version.py` and push to `main`.
If you fork it, set your own repo with `python scripts/set_repo.py YOUR_USERNAME` (a git clone detects it automatically).

## Fonts

- The title uses **Audiowide** (SIL OFL 1.1, bundled, see `msga/web/fonts`).
- Arabic text uses the **Thmanyah (ثمانية) font if it's installed on your system**. It is *not* included here because its license doesn't allow redistribution; download it from Thmanyah's official site and install it, and the app picks it up automatically. Without it, a fallback font is used.

## Development

```bash
python -m unittest discover -s tests -v
```

CI runs the tests on Windows, macOS and Linux for every push.

## Legal

Download only what you have the right to use. You are responsible for how you use this tool and for respecting the terms of the sites and the copyright of the content.

MIT licensed (see `LICENSE`).
