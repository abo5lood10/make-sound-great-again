#!/usr/bin/env python3
"""Make Sound Great Again: شغّل البرنامج بـ  python run.py"""
import sys

if sys.version_info < (3, 8):
    sys.exit("Python 3.8 or newer is required.")

from msga.app import main  # noqa: E402

if __name__ == "__main__":
    main()
