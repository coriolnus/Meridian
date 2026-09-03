# EDG-2026-019 ölçüm girdisi — DONMUŞ (Rol-1, 2026-09-03T13:14:29Z)
A1 `/opt/meridian/state`'ten salt-okunur çekim: `skill_gorusleri.jsonl` (6.138 satır, sha256 0479e45cda67ff41…), `meridian.db`
salt-okunur `sqlite3.backup` (trades 899; sha cdf932589b2cefb6…), `counterfactuals.jsonl` (7.289 satır; sha b2118466ce1a621c…),
`cf_open.json`, yerel `state/goal.yaml`. Birleştirme: motorun KENDİ `meridian.skill_gorus._gozlemler()` fonksiyonu, kum havuzu
STATE (config.STATE → scratch) ile kuru koşum — canlı/yerel state'e yazım yok (obs dosyası oluşmadı, ölçüldü). Sonuç 3.053 gözlem
(cf 2.154 · gerçek 899; 6 skill; eleme muhasebesi 0/0/0/0). Bu dosya kartın girdisi olarak git BLOB'una bağlanır (EDG-059 kuralı);
blob sha commit'ten sonra kart k_registry notuna yazılır. `olcum.py --kuru`: GÜNCEL-ŞEMA, ihlal yok.
