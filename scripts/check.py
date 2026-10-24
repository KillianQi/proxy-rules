#!/usr/bin/env python3
"""Repository guard for a PUBLIC rules repo. Fails (exit 1) on anything that must not be published.

Checks
  1. Rule syntax: source/*.list and dist/surge/*.list may only contain allowed rule types
     (DOMAIN, DOMAIN-SUFFIX, DOMAIN-KEYWORD, public IP-CIDR/IP-CIDR6, IP-ASN, PROCESS-NAME),
     no policies; dist/clash additionally allows PROCESS-NAME-REGEX / PROCESS-PATH-REGEX.
  2. dist/ must be exactly what scripts/build.py produces (run build first, then `git diff --exit-code`).
  3. Leak patterns in every tracked text file (vendor/ gets a reduced set, see below):
     private / CGNAT / loopback / link-local / ULA addresses, tailnet hostnames (*.ts.net),
     mDNS names (*.local), proxy share URIs, proxy definitions, config section markers,
     device / source-IP rules, private keys, credential assignments.
  4. Hashed deny list: SHA-256 digests of private hostnames and secret values, read from the
     DENY_SHA256 environment variable (a GitHub Actions secret; comma / whitespace separated) and
     optionally --deny-file. Every token and every hostname suffix in the tree is hashed and compared.
     Neither the values nor their digests live in this repository; matches are reported by file and
     line only, never by content.
  5. Size floors: usa-native must keep at least MIN_RULES rules.
"""
import argparse
import hashlib
import ipaddress
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rules_common import (CLASH_EXTRA_TYPES, SURGE_TYPES, RuleError, is_comment,  # noqa: E402
                          parse_rule, validate_rule)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", "__pycache__", "node_modules"}
SELF = os.path.relpath(os.path.abspath(__file__), ROOT)
MIN_RULES = {"usa-native": 100}

# Pattern pieces are split so this file does not trip its own scan when read by other tools.
P = lambda *a: re.compile("".join(a), re.I | re.M)  # noqa: E731
LEAK_PATTERNS = [
    ("tailnet hostname", P(r"\b[a-z0-9-]+\.", r"ts\.net\b")),
    ("mDNS .local hostname", P(r"\b[a-z0-9-]+\.", r"local\b(?![-.])")),
    ("proxy share URI", P(r"\b(ss|ssr|vmess|vless|trojan|hysteria2?|hy2|tuic|snell|anytls|wireguard|socks5?)", r"://")),
    ("proxy definition", P(r"=\s*(ss|snell|trojan|vmess|vless|hysteria2|tuic|anytls|wireguard|socks5|https?)\s*,\s*[\w.-]+\s*,\s*\d+")),
    ("config section marker", P(r"^\s*\[(General|Proxy|Proxy Group|Rule|Host|URL Rewrite|Header Rewrite|MITM|Script|Ruleset [^\]]*|WireGuard [^\]]*|Panel|Map Local|Body Rewrite)\]\s*$")),
    ("clash config key", P(r"^\s*(proxies|proxy-groups|proxy-providers|external-controller|secret|authentication)\s*:")),
    ("device / source-IP rule", P(r"#!", r"REQUIREMENT|\bDEVICE", r"_MODEL\b|^\s*SRC-IP|\bSRC-", r"PORT,|\bIN-PORT,|\bSUBNET,")),
    ("private key block", P(r"-----BEGIN [A-Z ]*PRIVATE", r" KEY-----")),
    ("credential assignment", P(r"\b(password|passwd|psk|obfs-host|obfs-password|auth-key|authkey|api[_-]?key|x-key|ca-p12|ca-passphrase|token)\s*[=:]\s*\S")),
    ("managed config line", P(r"^#!", r"MANAGED-CONFIG")),
]
# vendor/ holds unmodified third-party lists; only check what could only come from us.
VENDOR_PATTERNS = {"tailnet hostname", "proxy share URI", "proxy definition", "private key block", "managed config line"}
VENDOR_TAILNET = P(r"\btail[0-9a-f]{4,}\.", r"ts\.net\b")

IPV4 = re.compile(r"(?<![\w.])(\d{1,3}(?:\.\d{1,3}){3})(?:/\d{1,2})?(?![\w.])")
IPV6 = re.compile(r"(?<![\w:])((?:[0-9a-f]{1,4}:){2,7}[0-9a-f]{0,4}|(?:[0-9a-f]{1,4}:){1,6}:[0-9a-f]{0,4})(?:/\d{1,3})?(?![\w:])", re.I)
CGNAT = ipaddress.ip_network(((100 << 24) | (64 << 16), 10))  # shared address space (CGNAT / tailnet)
TOKEN_RE = re.compile(r"[A-Za-z0-9_\-+/=.~]{6,}")
HOST = re.compile(r"\b(?:[a-z0-9-]{1,63}\.)+[a-z][a-z0-9-]{1,62}\b", re.I)
TEXT_EXT = {".list", ".txt", ".yaml", ".yml", ".md", ".py", ".toml", ".json", ".conf", ".sh", ".cfg", ".ini", ""}


def non_public(addr):
    try:
        ip = ipaddress.ip_address(addr)
    except ValueError:
        return False
    if ip.version == 4 and ip in CGNAT:
        return True
    return not ip.is_global and not ip.is_unspecified and not ip.is_multicast


def iter_files():
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = sorted(d for d in dns if d not in SKIP_DIRS)
        for fn in sorted(fns):
            yield os.path.relpath(os.path.join(dp, fn), ROOT)


def is_text(rel):
    if os.path.splitext(rel)[1].lower() not in TEXT_EXT:
        return False
    with open(os.path.join(ROOT, rel), "rb") as f:
        return b"\0" not in f.read(8192)


def load_deny(args):
    raw = os.environ.get("DENY_SHA256", "")
    if args.deny_file:
        with open(args.deny_file, encoding="utf-8") as f:
            raw += "\n" + f.read()
    return {h.lower() for h in re.findall(r"\b[0-9a-fA-F]{64}\b", raw)}


def candidates(line):
    out = set(TOKEN_RE.findall(line))
    for h in HOST.findall(line):
        labels = h.lower().split(".")
        for i in range(len(labels) - 1):
            out.add(".".join(labels[i:]))
    return out


def check_rules(errors):
    rule_counts = {}
    groups = [("source", ".list", SURGE_TYPES), ("dist/surge", ".list", SURGE_TYPES),
              ("dist/clash", ".txt", SURGE_TYPES | CLASH_EXTRA_TYPES)]
    for d, ext, allowed in groups:
        base = os.path.join(ROOT, d)
        if not os.path.isdir(base):
            if d == "source":
                errors.append("source/ missing")
            continue
        for fn in sorted(os.listdir(base)):
            if not fn.endswith(ext):
                continue
            rel = os.path.join(d, fn)
            n_rules = 0
            with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
                for n, line in enumerate(f, 1):
                    if is_comment(line):
                        continue
                    try:
                        validate_rule(*parse_rule(line), allowed=allowed)
                        n_rules += 1
                    except RuleError as e:
                        errors.append("%s:%d: %s" % (rel, n, e))
            rule_counts[rel] = n_rules
    for name, floor in MIN_RULES.items():
        for rel in ("source/%s.list" % name, "dist/surge/%s.list" % name):
            if rel in rule_counts and rule_counts[rel] < floor:
                errors.append("%s: only %d rules (floor %d)" % (rel, rule_counts[rel], floor))
    # clash yaml: every payload entry must match the text twin
    cdir = os.path.join(ROOT, "dist/clash")
    if os.path.isdir(cdir):
        for fn in sorted(os.listdir(cdir)):
            if fn.endswith(".yaml"):
                with open(os.path.join(cdir, fn), encoding="utf-8") as f:
                    items = [l.strip()[3:-1].replace("''", "'") for l in f if l.startswith("  - '")]
                with open(os.path.join(cdir, fn[:-5] + ".txt"), encoding="utf-8") as f:
                    txt = [l.strip() for l in f if not is_comment(l)]
                if items != txt:
                    errors.append("dist/clash/%s does not match %s.txt" % (fn, fn[:-5]))
    return rule_counts


def check_leaks(errors, deny):
    scanned = 0
    for rel in iter_files():
        if not is_text(rel):
            continue
        scanned += 1
        vendor = rel.startswith("vendor" + os.sep)
        with open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace") as f:
            for n, line in enumerate(f, 1):
                where = "%s:%d" % (rel, n)
                if True:
                    for label, pat in LEAK_PATTERNS:
                        if vendor and label not in VENDOR_PATTERNS:
                            continue
                        if vendor and label == "tailnet hostname":
                            pat = VENDOR_TAILNET
                        if pat.search(line):
                            errors.append("%s: %s" % (where, label))
                    if not vendor:
                        for m in IPV4.finditer(line):
                            if non_public(m.group(1)):
                                errors.append("%s: non-public IPv4 address/range" % where)
                        for m in IPV6.finditer(line):
                            if non_public(m.group(1).rstrip(":") + ("::" if m.group(1).endswith(":") else "")):
                                errors.append("%s: non-public IPv6 address/range" % where)
                if deny:
                    for c in candidates(line):
                        if hashlib.sha256(c.encode()).hexdigest() in deny or \
                           hashlib.sha256(c.lower().encode()).hexdigest() in deny:
                            errors.append("%s: matches hashed deny list" % where)
                            break
    return scanned


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deny-file", help="extra file with SHA-256 digests (local use only)")
    ap.add_argument("--require-deny", action="store_true", help="fail if no deny digests are configured")
    args = ap.parse_args()
    errors = []
    deny = load_deny(args)
    if not deny:
        msg = "hashed deny list is empty (set the DENY_SHA256 Actions secret)"
        if args.require_deny:
            errors.append(msg)
        else:
            print("::warning::" + msg)
    counts = check_rules(errors)
    scanned = check_leaks(errors, deny)
    # de-duplicate, keep order
    errors = list(dict.fromkeys(errors))
    for e in errors:
        print("::error::" + e if os.environ.get("GITHUB_ACTIONS") else "ERROR " + e)
    print("checked %d rule files (%d rules), scanned %d text files, deny digests: %d -> %s"
          % (len(counts), sum(counts.values()), scanned, len(deny), "FAIL" if errors else "OK"))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
