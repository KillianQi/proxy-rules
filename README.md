# proxy-rules

自维护的 Surge / Clash（mihomo）分流规则，外加常用第三方规则列表的每日备份快照。
Self-maintained Surge / mihomo rule sets plus daily backup snapshots of the third-party lists they sit next to.

## 目录

| 路径 | 说明 |
|---|---|
| `source/` | **唯一人工编辑处**，Surge classical 语法，只写规则不写策略 |
| `dist/` | Surge / Clash 格式的规则，客户端引用这里 |
| `vendor/` | 第三方列表的每日快照（原样保存，保留各自许可证），只做备份 / 应急切换 |
| `composites.yaml` | 整合列表定义：按顺序合并 `source/` 与 `vendor/`，输出 `dist/surge/killian/`（只给 Killian 的托管配置用） |
| `exclude/` | 合并时从上游剔除的条目（如 `reject-allow.list`：广告列表白名单） |
| `ci/friend-files.sha256` | 朋友配置直接引用的 3 个文件的哈希，CI 校验不被意外改动 |
| `upstreams.yaml` | 第三方列表清单：原地址、快照路径、许可证、下限 |
| `scripts/` | 维护脚本（`build.py`、`check.py`、`sync_vendor.py`） |

## 自维护列表

| 列表 | 用途 | 建议策略 |
|---|---|---|
| `usa-native` | 需要美国原生 IP 的金融 / KYC / 风控 / 券商 / Claude 配套服务 | 美国原生 IP 出口 |
| `ai-extra` | Meta AI / Muse 相关、上游 AI 列表未覆盖的 3 条 | 同上 |
| `direct-broker` | 富途、长桥（原生 IP 例外） | 直连，排在 `usa-native` 之前 |
| `microsoft-non-copilot` | 微软资讯 / 定位 / 遥测（原生 IP 例外） | 微软服务，排在 `usa-native` 之前 |
| `direct-misc` | 小红书、BoxJs | 直连 |
| `proxy-custom` | 零散需要代理的域名 | 代理 |
| `reject-custom` | 自定义拦截 | `REJECT-DROP` |
| `direct-custom` | 零散直连（如 QQ 同步助手 mazu） | 直连 |
| `native-priority` | sift.com / siftscience.com | 美国原生 IP 出口，排在 `qaq-custom` 之前 |
| `qaq-custom` | DigitalOcean ASN、sift 关键词 | 主力代理，排在原生 IP 列表之前 |
| `proxy-extra` | Tailscale 控制面 | 代理 |

### 整合列表（`dist/surge/killian/`）

由 `composites.yaml` 定义，每天随 sync 自动从 `vendor/` 快照重建：只合并在配置里原本相邻、策略相同的列表，保持顺序，去掉完全重复的行，并按 `exclude/` 剔除白名单条目。任一列表低于下限或比上一版缩水超过 30% 时保留上一版。许可证见 `dist/surge/killian/NOTICE.md`（含 blackmatrix7 内容的文件按 GPL-2.0 再分发；没有许可证的上游不合并）。

## 引用方式

把 `NAME` 换成上表中的列表名。

Surge：

```ini
RULE-SET,https://raw.githubusercontent.com/KillianQi/proxy-rules/main/dist/surge/NAME.list,<策略>,extended-matching,"update-interval=86400"
# 只含 DOMAIN / DOMAIN-SUFFIX 的列表另有更快的 DOMAIN-SET：dist/surge/domainset/NAME.txt
```

mihomo（Clash Meta）：

```yaml
rule-providers:
  NAME:
    type: http
    behavior: classical
    format: yaml
    url: https://raw.githubusercontent.com/KillianQi/proxy-rules/main/dist/clash/NAME.yaml
    interval: 86400
# 纯域名列表另有 behavior: domain 的 dist/clash/domain/NAME.txt 与 NAME.mrs
```

说明：Surge 的通配 `PROCESS-NAME` 在 Clash 输出里会转换成 `PROCESS-NAME-REGEX` / `PROCESS-PATH-REGEX`。

## 维护

1. 只改 `source/*.list`（一行一条，不写策略；新增放进对应分组的注释下）；要从上游剔除的写进 `exclude/`。改完运行 `python3 scripts/build.py` 并提交 `dist/`。
2. 某个第三方地址失效时：先把配置临时指到本仓库 `vendor/` 下的同名快照，再找替代上游并更新 `upstreams.yaml`。

## 许可证

自维护部分（`source/`、`dist/`、`scripts/` 等）使用 MIT 许可证，见 [LICENSE](LICENSE)。
`vendor/` 下的文件属于各自上游并沿用原许可证（GPL-2.0 / GPL-3.0 / MIT，见 `upstreams.yaml`）。
`dist/surge/killian/` 中合并了上游内容的文件沿用对应上游许可证，见该目录 `NOTICE.md`。
