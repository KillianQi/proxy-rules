#!/usr/bin/env bash
# Install pinned, checksum-verified mihomo and gitleaks into $RUNNER_TEMP/bin (or ./.tools/bin).
set -euo pipefail
MIHOMO_VERSION=v1.19.33
MIHOMO_SHA256=386508bfb1c72c43b6a0eda73708ecdce82546581b0ebcb16366c53757c622b6
GITLEAKS_VERSION=8.30.1
GITLEAKS_SHA256=551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb
BIN="${RUNNER_TEMP:-$PWD/.tools}/bin"
mkdir -p "$BIN"; cd "$(mktemp -d)"
curl -fsSL -o mihomo.gz "https://github.com/MetaCubeX/mihomo/releases/download/${MIHOMO_VERSION}/mihomo-linux-amd64-compatible-${MIHOMO_VERSION}.gz"
echo "${MIHOMO_SHA256}  mihomo.gz" | sha256sum -c -
gunzip mihomo.gz && install -m 755 mihomo "$BIN/mihomo"
curl -fsSL -o gitleaks.tgz "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz"
echo "${GITLEAKS_SHA256}  gitleaks.tgz" | sha256sum -c -
tar xzf gitleaks.tgz gitleaks && install -m 755 gitleaks "$BIN/gitleaks"
[ -n "${GITHUB_PATH:-}" ] && echo "$BIN" >> "$GITHUB_PATH"
"$BIN/mihomo" -v | head -1; "$BIN/gitleaks" version
