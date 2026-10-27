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

- 含 blackmatrix7/ios_rule_script 内容的文件按 **GPL-2.0** 再分发（上游原文见 https://github.com/blackmatrix7/ios_rule_script/blob/master/LICENSE），本目录对应的源码即 `composites.yaml`、`scripts/` 与 `vendor/` 下的原始快照。
- privacy-protection-tools/anti-AD 与 VPSDance/ai-proxy-rules 为 **MIT**，版权归原作者，许可证原文见各自仓库 LICENSE。
- 没有声明许可证的上游（如 fatesdf/surge-rules、Blankwonder/surge-list）**不合并、不再分发**，配置里直接引用原地址。
