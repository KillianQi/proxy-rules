#!/usr/bin/env python3
"""Generate dist/ from source/*.list (Surge classical syntax).

Outputs per list NAME:
  dist/surge/NAME.list            Surge RULE-SET (comments and order kept)
  dist/surge/domainset/NAME.txt   Surge DOMAIN-SET  (only for DOMAIN/DOMAIN-SUFFIX-only lists)
  dist/clash/NAME.yaml            mihomo rule-provider, behavior: classical, format: yaml
  dist/clash/NAME.txt             mihomo rule-provider, behavior: classical, format: text
  dist/clash/domain/NAME.txt      mihomo behavior: domain, format: text (domain-only lists)
  dist/clash/domain/NAME.mrs      same as .mrs, only if a `mihomo` binary is on PATH (or --mihomo)
  dist/surge/killian/*            integrated lists defined in composites.yaml (scripts/composites.py)

Usage: python3 scripts/build.py [--mihomo PATH] [--no-mrs]
"""
import argparse
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rules_common import RuleError, is_comment, parse_rule, validate_rule  # noqa: E402
import composites  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "source")
DIST = os.path.join(ROOT, "dist")
GEN_NOTE = "# 由 scripts/build.py 从 source/{name}.list 生成，请勿手改。Generated file, do not edit."


def wildcard_to_regex(pattern):
    out = []
    for ch in pattern:
        if ch == "*":
            out.append(".*")
        elif ch == "?":
            out.append(".")
        elif ch in ".^$+{}[]()|\\":
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "^" + "".join(out) + "$"


def to_clash(rtype, value, opts):
    if rtype == "PROCESS-NAME" and ("*" in value or "?" in value):
        # mihomo has no wildcard PROCESS-NAME; use its regex rule types instead.
        rtype = "PROCESS-PATH-REGEX" if "/" in value else "PROCESS-NAME-REGEX"
        value = wildcard_to_regex(value)
    return ",".join([rtype, value] + opts)


def load(path):
    rows = []  # list of ("comment", text) or ("rule", (type, value, opts))
    errors = []
    seen = set()
    with open(path, encoding="utf-8") as f:
        for n, raw in enumerate(f, 1):
            line = raw.rstrip("\r\n")
            if is_comment(line):
                rows.append(("comment", line.strip()))
                continue
            try:
                rtype, value, opts = parse_rule(line)
                if rtype not in ("PROCESS-NAME",):
                    value = value.lower()
                validate_rule(rtype, value, opts)
            except RuleError as e:
                errors.append("%s:%d: %s" % (os.path.relpath(path, ROOT), n, e))
                continue
            key = (rtype, value)
            if key in seen:
                errors.append("%s:%d: duplicate rule %s,%s" % (os.path.relpath(path, ROOT), n, rtype, value))
                continue
            seen.add(key)
            rows.append(("rule", (rtype, value, opts)))
    return rows, errors


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def yaml_quote(s):
    return "'" + s.replace("'", "''") + "'"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mihomo", default=shutil.which("mihomo"))
    ap.add_argument("--no-mrs", action="store_true")
    args = ap.parse_args()

    names = sorted(f[:-5] for f in os.listdir(SRC) if f.endswith(".list"))
    all_errors = []
    built = {}
    for name in names:
        rows, errors = load(os.path.join(SRC, name + ".list"))
        all_errors += errors
        built[name] = rows
    if all_errors:
        print("\n".join(all_errors), file=sys.stderr)
        sys.exit(1)

    prev_composites = composites.snapshot_previous()
    shutil.rmtree(DIST, ignore_errors=True)
    for name, rows in built.items():
        rules = [r for kind, r in rows if kind == "rule"]
        note = GEN_NOTE.format(name=name)

        # Surge RULE-SET: keep comments and order.
        body = [note]
        for kind, r in rows:
            body.append(r if kind == "comment" else ",".join([r[0], r[1]] + r[2]))
        write(os.path.join(DIST, "surge", name + ".list"), "\n".join(body).rstrip("\n") + "\n")

        # Clash classical text / yaml.
        clash = [to_clash(*r) for r in rules]
        write(os.path.join(DIST, "clash", name + ".txt"), note + "\n" + "\n".join(clash) + "\n")
        write(os.path.join(DIST, "clash", name + ".yaml"),
              note + "\npayload:\n" + "".join("  - %s\n" % yaml_quote(c) for c in clash))

        # Domain-only lists: Surge DOMAIN-SET and mihomo domain behavior (+ .mrs).
        if rules and all(r[0] in ("DOMAIN", "DOMAIN-SUFFIX") for r in rules):
            ds = [("." + v) if t == "DOMAIN-SUFFIX" else v for t, v, _ in rules]
            write(os.path.join(DIST, "surge", "domainset", name + ".txt"), note + "\n" + "\n".join(ds) + "\n")
            md = [("+." + v) if t == "DOMAIN-SUFFIX" else v for t, v, _ in rules]
            txt = os.path.join(DIST, "clash", "domain", name + ".txt")
            write(txt, note + "\n" + "\n".join(md) + "\n")
            if args.mihomo and not args.no_mrs:
                subprocess.run([args.mihomo, "convert-ruleset", "domain", "text", txt, txt[:-4] + ".mrs"],
                               check=True, stdout=subprocess.DEVNULL)
        print("%-24s %4d rules" % (name, len(rules)))
    if not (args.mihomo and not args.no_mrs):
        print("note: mihomo not found, .mrs skipped", file=sys.stderr)
    composites.build(prev_composites)


if __name__ == "__main__":
    main()
