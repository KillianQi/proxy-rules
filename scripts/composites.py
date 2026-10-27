#!/usr/bin/env python3
"""Build dist/surge/killian/* from composites.yaml (ordered merge of source/ and vendor/ lists).

Called by scripts/build.py. Rules:
  * inputs are concatenated in order; comments dropped; exact duplicate lines removed (first kept);
  * exclude/*.list entries are removed (DOMAIN = identical DOMAIN entry only, covering suffix entries are kept;
    DOMAIN-SUFFIX = that domain and every entry under it);
  * fail-safe: an output below min_rules, or shrunk by more than max_shrink versus the previous
    published file, keeps the previous file (warning); with no previous file the build fails.
"""
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rules_common import is_comment, parse_rule  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "dist", "surge", "killian")
CONF = os.path.join(ROOT, "composites.yaml")
NOTE = "# 由 scripts/build.py 按 composites.yaml 生成（{name}），请勿手改。Generated file, do not edit."


def load_conf():
    with open(CONF, encoding="utf-8") as f:
        return yaml.safe_load(f)


def snapshot_previous():
    """Read currently published composites before dist/ is wiped."""
    prev = {}
    if os.path.isdir(OUT):
        for fn in os.listdir(OUT):
            with open(os.path.join(OUT, fn), encoding="utf-8") as f:
                prev[fn] = f.read()
    return prev


def count_rules(text):
    return sum(1 for l in text.splitlines() if not is_comment(l))


def load_exclude(paths):
    exact, suffix = set(), set()
    for rel in paths or []:
        with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
            for line in f:
                if is_comment(line):
                    continue
                t, v, _ = parse_rule(line)
                (exact if t == "DOMAIN" else suffix).add(v.lower())
    return exact, suffix


def excluded(t, v, exact, suffix, warn):
    """DOMAIN allow entry: drop only the identical DOMAIN entry; a covering suffix entry is KEPT
    (dropping it would also unblock subdomains) and reported. DOMAIN-SUFFIX allow entry: drop the
    domain and every DOMAIN / DOMAIN-SUFFIX entry under it."""
    if t not in ("DOMAIN", "DOMAIN-SUFFIX"):
        return False
    v = v.lower()
    if t == "DOMAIN" and v in exact:
        return True
    if t == "DOMAIN-SUFFIX":
        for a in exact:
            if a == v or a.endswith("." + v):
                warn.append("allow-listed %s is still covered by suffix entry %s (kept; the config's earlier "
                            "direct rule decides)" % (a, v))
    for s in suffix:
        if v == s or v.endswith("." + s):
            return True
        if t == "DOMAIN-SUFFIX" and s.endswith("." + v):
            warn.append("allow-listed %s is still covered by parent suffix %s" % (s, v))
    return False


def read_input(spec):
    if isinstance(spec, str):
        spec = {"path": spec}
    only, drop = set(spec.get("only_types") or []), set(spec.get("drop_types") or [])
    rows = []
    with open(os.path.join(ROOT, spec["path"]), encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if is_comment(line):
                continue
            t = line.split(",", 1)[0].upper()
            if only and t not in only or t in drop:
                continue
            rows.append(line)
    return spec["path"], rows


def build_one(c, defaults, warn):
    exact, suffix = load_exclude(c.get("exclude"))
    domainset = c.get("format") == "domainset"
    seen, out, sources, removed = set(), [], [], 0
    for spec in c["inputs"]:
        path, rows = read_input(spec)
        sources.append(path)
        for line in rows:
            if domainset:
                t, v = ("DOMAIN-SUFFIX", line[1:]) if line.startswith(".") else ("DOMAIN", line)
            else:
                parts = line.split(",")
                t, v = parts[0].upper(), (parts[1].strip() if len(parts) > 1 else "")
            if excluded(t, v, exact, suffix, warn):
                removed += 1
                continue
            if line in seen:
                continue
            seen.add(line)
            out.append(line)
    head = [NOTE.format(name=c["name"]),
            "# 来源（按顺序）：" + "；".join(sources),
            "# 许可证：" + str(c.get("license", "")) + "（见 dist/surge/killian/NOTICE.md）",
            "# 剔除：" + ("；".join(c.get("exclude") or []) or "无") + "，剔除 %d 条" % removed,
            "# 规则数：%d" % len(out)]
    return "\n".join(head + out) + "\n", len(out)


NOTICE = """# dist/surge/killian — 整合列表说明 / NOTICE

这些文件由 `scripts/build.py` 按 `composites.yaml` 生成，只给 Killian 的托管配置用；朋友配置继续用 `dist/surge/` 下的原有列表。

| 文件 | 来源 | 许可证 |
|---|---|---|
{rows}

- 含 blackmatrix7/ios_rule_script 内容的文件按 **GPL-2.0** 再分发（上游原文见 https://github.com/blackmatrix7/ios_rule_script/blob/master/LICENSE），本目录对应的源码即 `composites.yaml`、`scripts/` 与 `vendor/` 下的原始快照。
- privacy-protection-tools/anti-AD 与 VPSDance/ai-proxy-rules 为 **MIT**，版权归原作者，许可证原文见各自仓库 LICENSE。
- 没有声明许可证的上游（如 fatesdf/surge-rules、Blankwonder/surge-list）**不合并、不再分发**，配置里直接引用原地址。
"""


def build(prev):
    conf = load_conf()
    defaults = conf.get("defaults") or {}
    os.makedirs(OUT, exist_ok=True)
    warn, errors, rows = [], [], []
    for c in conf["composites"]:
        fn = c["name"] + (".txt" if c.get("format") == "domainset" else ".list")
        text, n = build_one(c, defaults, warn)
        old = prev.get(fn)
        floor = c.get("min_rules", 1)
        shrink = c.get("max_shrink", defaults.get("max_shrink", 0.3))
        bad = None
        if n < floor:
            bad = "%s: %d rules < floor %d" % (fn, n, floor)
        elif old is not None and n < count_rules(old) * (1 - shrink):
            bad = "%s: shrank %d -> %d (> %d%%)" % (fn, count_rules(old), n, shrink * 100)
        if bad:
            if old is None:
                errors.append(bad + ", no previous file to keep")
                continue
            warn.append(bad + ", kept previous file")
            text = old
        with open(os.path.join(OUT, fn), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        srcs = "<br>".join(s if isinstance(s, str) else s["path"] for s in c["inputs"])
        rows.append("| `%s` | %s | %s |" % (fn, srcs, c.get("license", "")))
        print("%-24s %6d rules" % ("killian/" + fn, count_rules(text)))
    with open(os.path.join(OUT, "NOTICE.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(NOTICE.format(rows="\n".join(rows)))
    for w in dict.fromkeys(warn):
        print("::warning::" + w)
    if errors:
        for e in errors:
            print("::error::" + e, file=sys.stderr)
        sys.exit(1)
