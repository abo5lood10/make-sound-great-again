#!/usr/bin/env python3
"""Make Sound Great Again: شغّل البرنامج بـ  python run.py"""
import sys

if sys.version_info < (3, 8):
    sys.exit("Python 3.8 or newer is required.")

if len(sys.argv) > 1 and sys.argv[1] == "--ytdlp":
    # وضع داخلي للنسخة المجمّعة (exe / app): يشغّل yt-dlp المدمج بدل برنامج خارجي
    import yt_dlp
    yt_dlp.main(sys.argv[2:])
    sys.exit(0)

from msga.app import main  # noqa: E402

if __name__ == "__main__":
    main()
