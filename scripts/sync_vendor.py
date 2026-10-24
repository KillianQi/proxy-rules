#!/usr/bin/env python3
"""Refresh vendor/ snapshots of the third-party lists named in upstreams.yaml.

For each enabled upstream: download -> sanity checks -> replace the snapshot only if it changed.
A snapshot is KEPT (and a warning emitted) when the download fails, returns non-200, is empty,
falls below min_lines / min_bytes, or shrinks by more than max_shrink versus the previous snapshot.
Exit code is 0 even when some upstreams are kept, so one dead upstream never blocks the rest;
use --strict to fail instead. Writes a Markdown summary to $GITHUB_STEP_SUMMARY when present.
"""
import argparse
import os
import sys
import time
import urllib.request

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "proxy-rules-vendor-sync/1.0 (+https://github.com/KillianQi/proxy-rules)"


def fetch(url, timeout=60, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                if r.status != 200:
                    raise IOError("HTTP %d" % r.status)
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 * (i + 1))
    raise IOError(str(last))


def count_lines(data):
    return sum(1 for l in data.decode("utf-8", "replace").splitlines()
               if l.strip() and not l.lstrip().startswith(("#", "//", ";")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--only", help="comma-separated upstream names")
    args = ap.parse_args()
    with open(os.path.join(ROOT, "upstreams.yaml"), encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    max_shrink = float(cfg.get("defaults", {}).get("max_shrink", 0.5))
    only = set(args.only.split(",")) if args.only else None
    rows, kept = [], 0
    for up in cfg["upstreams"]:
        name = up["name"]
        if up.get("enabled", True) is False or (only and name not in only):
            continue
        path = os.path.join(ROOT, up["path"])
        if not os.path.abspath(path).startswith(os.path.join(ROOT, "vendor") + os.sep):
            print("::error::%s: path must be under vendor/" % name)
            sys.exit(1)
        old = open(path, "rb").read() if os.path.exists(path) else None
        binary = up.get("kind") == "binary"
        status = "unchanged"
        try:
            data = fetch(up["url"])
            if not data.strip():
                raise IOError("empty body")
            if binary:
                size, floor, prev = len(data), int(up.get("min_bytes", 64)), len(old) if old else 0
                unit = "bytes"
            else:
                data.decode("utf-8")  # must be text
                size, floor = count_lines(data), int(up.get("min_lines", 1))
                prev = count_lines(old) if old else 0
                unit = "lines"
            if size < floor:
                raise IOError("%d %s < min %d" % (size, unit, floor))
            if prev and size < prev * (1 - max_shrink):
                raise IOError("shrank %d -> %d %s (> %d%%)" % (prev, size, unit, max_shrink * 100))
            if data != old:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "wb") as f:
                    f.write(data)
                status = "updated (%s %d -> %d)" % (unit, prev, size) if old else "new (%d %s)" % (size, unit)
        except Exception as e:  # noqa: BLE001
            kept += 1
            status = "KEPT old snapshot: %s" % e if old else "MISSING (no snapshot yet): %s" % e
            print("::warning::%s: %s" % (name, status))
        rows.append((name, status))
        print("%-40s %s" % (name, status))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("### vendor sync\n\n| upstream | result |\n|---|---|\n")
            f.writelines("| %s | %s |\n" % r for r in rows)
    if kept and args.strict:
        sys.exit(1)


if __name__ == "__main__":
    main()
