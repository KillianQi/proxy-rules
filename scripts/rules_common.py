"""Shared parsing helpers for proxy-rules (no third-party deps)."""
import ipaddress
import re

# Rule types allowed in source/ and dist/surge (Surge classical syntax).
SURGE_TYPES = {
    "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD",
    "IP-CIDR", "IP-CIDR6", "IP-ASN", "PROCESS-NAME",
}
# Extra types that only appear in dist/clash (converted from wildcard PROCESS-NAME).
CLASH_EXTRA_TYPES = {"PROCESS-NAME-REGEX", "PROCESS-PATH-REGEX"}
IP_TYPES = {"IP-CIDR", "IP-CIDR6", "IP-ASN"}
DOMAIN_TYPES = {"DOMAIN", "DOMAIN-SUFFIX"}

HOST_RE = re.compile(r"^(?=.{1,253}$)([a-z0-9_]([a-z0-9_-]{0,61}[a-z0-9_])?)(\.[a-z0-9_]([a-z0-9_-]{0,61}[a-z0-9_])?)*$")
KEYWORD_RE = re.compile(r"^[a-z0-9._-]{2,}$")
CGNAT = ipaddress.ip_network(((100 << 24) | (64 << 16), 10))  # shared address space (CGNAT / tailnet)


class RuleError(ValueError):
    pass


def is_comment(line):
    s = line.strip()
    return not s or s.startswith("#") or s.startswith("//") or s.startswith(";")


def parse_rule(line):
    """Return (type, value, options) for one non-comment Surge rule line."""
    parts = [p.strip() for p in line.strip().split(",")]
    if len(parts) < 2:
        raise RuleError("not a rule: %r" % line)
    rtype, value, opts = parts[0].upper(), parts[1], parts[2:]
    return rtype, value, opts


def public_network(value):
    try:
        net = ipaddress.ip_network(value, strict=False)
    except ValueError:
        return False
    if net.version == 4 and net.overlaps(CGNAT):
        return False
    return net.is_global


def validate_rule(rtype, value, opts, allowed=SURGE_TYPES):
    if rtype not in allowed:
        raise RuleError("rule type %s is not allowed" % rtype)
    if rtype in DOMAIN_TYPES:
        if not HOST_RE.match(value):
            raise RuleError("bad domain %r" % value)
    elif rtype == "DOMAIN-KEYWORD":
        if not KEYWORD_RE.match(value):
            raise RuleError("bad keyword %r" % value)
    elif rtype in ("IP-CIDR", "IP-CIDR6"):
        if not public_network(value):
            raise RuleError("non-public or invalid network %r" % value)
    elif rtype == "IP-ASN":
        if not value.isdigit():
            raise RuleError("bad ASN %r" % value)
    elif rtype in ("PROCESS-NAME", "PROCESS-NAME-REGEX", "PROCESS-PATH-REGEX"):
        if not value or len(value) > 200:
            raise RuleError("bad process name")
    for o in opts:
        if o != "no-resolve" or rtype not in IP_TYPES:
            raise RuleError("option %r not allowed (policies belong in the config, not the list)" % o)
