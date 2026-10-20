"""واجهة الطرفية:  python -m msga.cli <رابط أو ملف> ..."""
import argparse
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import core
from .version import APP_NAME, VERSION

print_lock = threading.Lock()


def fmt_report(r):
    parts = [f"Source: {r['codec']}" + (f" {r['bitrate_kbps']}kbps" if r["bitrate_kbps"] else ""),
             f"Preset: {r['preset']}" + (" (auto)" if r["auto"] else "")]
    if r["lufs_before"] is not None and r["lufs_after"] is not None:
        parts.append(f"Loudness: {r['lufs_before']:.1f} -> {r['lufs_after']:.1f} LUFS")
    return " | ".join(parts)


def run_one(idx, total, item, opts, live):
    label = f"[{idx}/{total}]"
    last = {"stage": None}

    def cb(stage, frac):
        text = core.msg(stage, "en")
        with print_lock:
            if live:
                print(f"\r{label} {text}: {frac * 100:3.0f}%   ", end="", flush=True)
            elif stage != last["stage"]:
                print(f"{label} {text}...", flush=True)
            last["stage"] = stage

    try:
        res = core.process_item(item, opts, cb)
    except core.EnhanceError as e:
        with print_lock:
            print(f"\n{label} FAILED {item}\n      {e.text('en')}", flush=True)
        return False
    with print_lock:
        r = res["report"]
        print(f"\n{label} OK {res['output']}\n      {fmt_report(r)}\n      "
              f"{core.msg(r['reason_key'], 'en', **r['reason_params'])}", flush=True)
        if res["original"]:
            print(f"      Original (for comparison): {res['original']}", flush=True)
    return True


def main(argv=None):
    cfg = core.load_config()
    ap = argparse.ArgumentParser(prog="python -m msga.cli", description=f"{APP_NAME} v{VERSION}")
    ap.add_argument("inputs", nargs="*", help="links or file paths")
    ap.add_argument("-p", "--preset", choices=[*core.PRESETS, "auto"], default=cfg["preset"],
                    help="auto | gentle | natural | clean | bass | vocal")
    ap.add_argument("-f", "--format", choices=core.CODECS, default=cfg["format"])
    ap.add_argument("-o", "--out", type=Path, default=Path(cfg["out"]), help="output folder")
    ap.add_argument("--lufs", type=int, choices=core.LUFS_CHOICES, default=cfg["lufs"],
                    help="target loudness (0 = don't change the level)")
    ap.add_argument("-j", "--jobs", type=int, default=cfg["jobs"], help="parallel jobs")
    ap.add_argument("--playlist", action="store_true", help="links are playlists: download every song")
    ap.add_argument("--clean", type=int, metavar="DAYS", help="delete output files older than DAYS")
    ap.add_argument("--version", action="version", version=f"{APP_NAME} {VERSION}")
    args = ap.parse_args(argv)

    if args.clean is not None:
        print(f"Deleted {core.clean_old(args.out, args.clean)} file(s).")
    if not args.inputs:
        if args.clean is None:
            ap.print_help()
        return 0

    try:
        items = []
        for x in args.inputs:
            if args.playlist and core.is_url(x):
                print(f"Reading playlist: {x}")
                items += core.expand_playlist(x)
            else:
                items.append(x)
    except core.EnhanceError as e:
        print(e.text("en"), file=sys.stderr)
        return 2

    opts = {"preset": args.preset, "format": args.format, "out_dir": args.out, "light": cfg["light"],
            "lufs": args.lufs, "bass": cfg["bass"], "treble": cfg["treble"]}
    jobs = max(1, min(8, args.jobs))
    live = jobs == 1 and sys.stdout.isatty()
    total = len(items)
    with ThreadPoolExecutor(jobs) as ex:
        ok = sum(ex.map(lambda p: run_one(p[0], total, p[1], opts, live), enumerate(items, 1)))
    print(f"\nDone: {ok} succeeded, {total - ok} failed. Files are in: {args.out}")
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
