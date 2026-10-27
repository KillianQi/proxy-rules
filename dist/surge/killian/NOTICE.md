# dist/surge/killian — 整合列表说明 / NOTICE

这些文件由 `scripts/build.py` 按 `composites.yaml` 生成，只给 Killian 的托管配置用；朋友配置继续用 `dist/surge/` 下的原有列表。

| 文件 | 来源 | 许可证 |
|---|---|---|
| `proxy.list` | source/proxy-extra.list<br>source/proxy-custom.list | MIT |
| `direct.list` | source/direct-broker.list<br>source/direct-misc.list<br>source/direct-custom.list | MIT |
| `direct-ext.list` | source/direct-misc.list | MIT |
| `native.list` | source/usa-native.list<br>vendor/VPSDance/ai-proxy-rules/rules/surge/global.list | MIT (VPSDance/ai-proxy-rules) |
| `reject-antiad.txt` | vendor/privacy-protection-tools/anti-AD/anti-ad-surge2.txt | MIT (privacy-protection-tools/anti-AD) |
| `reject-adlite.list` | vendor/blackmatrix7/ios_rule_script/rule/Surge/AdvertisingLite/AdvertisingLite_All_No_Resolve.list | GPL-2.0 (blackmatrix7/ios_rule_script) |
| `direct-cnmedia.list` | vendor/blackmatrix7/ios_rule_script/rule/Surge/BiliBili/BiliBili.list<br>vendor/blackmatrix7/ios_rule_script/rule/Surge/ChinaMedia/ChinaMedia.list | GPL-2.0 (blackmatrix7/ios_rule_script) |
| `games.list` | vendor/blackmatrix7/ios_rule_script/rule/Surge/Epic/Epic.list<br>vendor/blackmatrix7/ios_rule_script/rule/Surge/Sony/Sony.list<br>vendor/blackmatrix7/ios_rule_script/rule/Surge/Steam/Steam.list<br>vendor/blackmatrix7/ios_rule_script/rule/Surge/Nintendo/Nintendo.list | GPL-2.0 (blackmatrix7/ios_rule_script) |
| `icloud.list` | vendor/blackmatrix7/ios_rule_script/rule/Surge/iCloud/iCloud.list | GPL-2.0 (blackmatrix7/ios_rule_script) |
| `apple.list` | vendor/blackmatrix7/ios_rule_script/rule/Surge/Apple/Apple_All_No_Resolve.list | GPL-2.0 (blackmatrix7/ios_rule_script) |
| `bing.list` | vendor/blackmatrix7/ios_rule_script/rule/Surge/Bing/Bing.list | GPL-2.0 (blackmatrix7/ios_rule_script) |
| `github.list` | vendor/blackmatrix7/ios_rule_script/rule/Surge/GitHub/GitHub.list | GPL-2.0 (blackmatrix7/ios_rule_script) |
| `microsoft.list` | vendor/blackmatrix7/ios_rule_script/rule/Surge/Microsoft/Microsoft.list | GPL-2.0 (blackmatrix7/ios_rule_script) |
| `telegram.list` | vendor/blackmatrix7/ios_rule_script/rule/Surge/Telegram/Telegram.list | GPL-2.0 (blackmatrix7/ios_rule_script) |
| `google.list` | vendor/blackmatrix7/ios_rule_script/rule/Surge/Google/Google.list | GPL-2.0 (blackmatrix7/ios_rule_script) |
| `googlevoice.list` | vendor/blackmatrix7/ios_rule_script/rule/Surge/GoogleVoice/GoogleVoice.list | GPL-2.0 (blackmatrix7/ios_rule_script) |
| `youtube.list` | vendor/blackmatrix7/ios_rule_script/rule/Surge/YouTube/YouTube.list | GPL-2.0 (blackmatrix7/ios_rule_script) |
| `spotify.list` | vendor/blackmatrix7/ios_rule_script/rule/Surge/Spotify/Spotify.list | GPL-2.0 (blackmatrix7/ios_rule_script) |
| `globalmedia.list` | vendor/blackmatrix7/ios_rule_script/rule/Surge/GlobalMedia/GlobalMedia_All_No_Resolve.list | GPL-2.0 (blackmatrix7/ios_rule_script) |
| `proxy-all.list` | vendor/blackmatrix7/ios_rule_script/rule/Surge/Proxy/Proxy_All_No_Resolve.list | GPL-2.0 (blackmatrix7/ios_rule_script) |
| `cloudflare.list` | vendor/blackmatrix7/ios_rule_script/rule/Surge/Cloudflare/Cloudflare.list | GPL-2.0 (blackmatrix7/ios_rule_script) |
| `speedtest.list` | vendor/blackmatrix7/ios_rule_script/rule/Surge/Speedtest/Speedtest.list | GPL-2.0 (blackmatrix7/ios_rule_script) |
| `wechat.list` | vendor/blackmatrix7/ios_rule_script/rule/Surge/WeChat/WeChat.list | GPL-2.0 (blackmatrix7/ios_rule_script) |
| `duolingo.list` | vendor/blackmatrix7/ios_rule_script/rule/Surge/Duolingo/Duolingo.list | GPL-2.0 (blackmatrix7/ios_rule_script) |
| `hijacking.list` | vendor/blackmatrix7/ios_rule_script/rule/Surge/Hijacking/Hijacking.list | GPL-2.0 (blackmatrix7/ios_rule_script) |
| `chinaasn.list` | vendor/blackmatrix7/ios_rule_script/rule/Surge/ChinaASN/ChinaASN_Resolve.list | GPL-2.0 (blackmatrix7/ios_rule_script) |
| `ai-muse.list` | vendor/fatesdf/surge-rules/ai-muse.conf | none — no LICENSE upstream; mirrored with attribution, removed on request |
| `cn.list` | vendor/Blankwonder/surge-list/cn.list | none — no LICENSE upstream; mirrored with attribution, removed on request |

- 含 blackmatrix7/ios_rule_script 内容的文件按 **GPL-2.0** 再分发（上游原文见 https://github.com/blackmatrix7/ios_rule_script/blob/master/LICENSE），本目录对应的源码即 `composites.yaml`、`scripts/` 与 `vendor/` 下的原始快照。
- privacy-protection-tools/anti-AD 与 VPSDance/ai-proxy-rules 为 **MIT**，版权归原作者，许可证原文见各自仓库 LICENSE。
- `ai-muse.list`（fatesdf/surge-rules）与 `cn.list`（Blankwonder/surge-list）的上游**没有声明许可证**：只做一对一镜像、不与其他内容合并，文件头注明原地址和作者，版权归原作者；原作者提出要求时会立即删除（见 README「致谢」）。
- 一对一镜像文件（文件头带「原始地址」）的规则与上游逐条一致，只去掉注释和完全重复的行。
