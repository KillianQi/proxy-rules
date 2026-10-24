# proxy-rules

自维护的 Surge / Clash（mihomo）分流规则，外加常用第三方规则列表的每日备份快照。
Self-maintained Surge / mihomo rule sets plus daily backup snapshots of the third-party lists they sit next to.

## 目录

| 路径 | 说明 |
|---|---|
| `source/` | **唯一人工编辑处**，Surge classical 语法，只写规则不写策略 |
| `dist/` | 由 `scripts/build.py` 生成，客户端引用这里，**不要手改** |
| `vendor/` | 第三方列表的每日快照（原样保存，保留各自许可证），只做备份 / 应急切换 |
| `upstreams.yaml` | 第三方列表清单：原地址、快照路径、许可证、下限 |
| `scripts/` | `build.py` 生成、`check.py` 规则与防泄漏检查、`sync_vendor.py` 快照同步 |

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

1. 只改 `source/*.list`（一行一条，不写策略；新增放进对应分组的注释下）。
2. 运行 `python3 scripts/build.py && python3 scripts/check.py`，把 `source/` 和 `dist/` 一起提交到 `main`。
3. 每次推送都会跑 CI：重新生成并比对 `dist/`、规则类型白名单、防泄漏检查、gitleaks。任何一项失败都要先修好。
4. `sync` 工作流每天 03:30（UTC+8）刷新 `vendor/` 快照：抓取失败、低于下限或缩水超过一半时保留旧快照并告警；有变化才提交。
5. 某个第三方地址失效时：先把配置临时指到本仓库 `vendor/` 下的同名快照，再找替代上游并更新 `upstreams.yaml`。

## 公开仓库的红线

本仓库公开。任何节点、密码、密钥、订阅 / 托管链接、私有域名、内网或组网地址、设备专属规则都不能出现在这里，
`scripts/check.py` 和 gitleaks 会在 CI 中拦截。

## 许可证

自维护部分（`source/`、`dist/`、`scripts/` 等）使用 MIT 许可证，见 [LICENSE](LICENSE)。
`vendor/` 下的文件属于各自上游并沿用原许可证（GPL-2.0 / GPL-3.0 / MIT，见 `upstreams.yaml`）。
