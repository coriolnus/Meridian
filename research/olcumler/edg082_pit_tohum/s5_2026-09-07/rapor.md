# Tohum PIT yenileme — UYGULA (2026-09-07T18:19:51+00:00)

- araç: `ops/tohum_pit_yenile.py` · parti: `EDG-082A-2026-09-07` · varyant: A · üyelik: as_of · sv=91
- KAPI-0: uygula_izni=True (engel yok)
- pencere: 2022-01-01..2026-07-24 (--bitis)
- girdi: html sha `9909032c1f815a01…` · güncel liste sha `a0cfcccab994a6b9…` · params sha `795fd2046cfeabe7…`

## Önceki defter
- trades: toplam 901 · replay_seed 885 · live_paper 16 · belirsiz 0
- trade_plans: 511 (llm_opinion 390) → tohum 121 / korunan 390
- realized_pnl: 6366.84314200393 · eğri noktası 898

## Kıyas — eski tohum ↔ yeni tohum

| ölçüm | eski | yeni | Δ |
|---|---|---|---|
| n | 885 | 843 | -42 |
| avg_r | 0.0763 | 0.0754 | -0.0009 |
| medyan_r | -0.18 | -0.162 | 0.018 |
| kazanma | 0.3627 | 0.363 | 0.0003 |
| pnl$ | 20684.69 | 18503.14 | -2181.55 |

- yıl bazında (yeni): {'2022': 37, '2023': 173, '2024': 249, '2025': 203, '2026': 181}
- çıkış nedeni (yeni): {'regime_flip': 162, 'stop': 369, 'stop_gap': 51, 'target': 94, 'target_gap': 23, 'time_stop': 144}
- SIZINTI (yeni): üye-olmayan 0 · hiç-üye 0 · ölçülemedi 0
- SIZINTI (eski, aynı üyelikle): üye-olmayan 95
- kapı: olculdu (oos_score 0.3004)

## Yazım
- çalıştı: True — ok
- arşiv: `/opt/meridian/backups/tohum-arsiv-20260907T181951Z.jsonl` (sha256 `970619dff302a62a…`, 885 işlem + 121 plan)
- trades: 859 satır (yeni tohum 843 + korunan 16)
- trade_plans: 1032 satır (çakışan kimlik 310)
- eğri işareti: `TD-20260907T181951Z` (points DOKUNULMADI)

## Yazım sonrası doğrulama (EŞİK YOK — hüküm Rol-1'in)
- canlı satırlar bit-aynı: True (16 satır)
- realized_pnl aynı: True (6366.84314200393)
- seed_boundary.replay_end: 2026-07-24 (yeni tohum max ts_close 2026-07-24, eşleşti True)
- counts: 16 live / 843 tohum / 0 belirsiz
- eğri: points 898 (aynı: True), işaret 2
- korunum açıklanamayan: 7
- işlem kimliği çift: 0 · plan kimliği çift: 0
- rollback kapısı: ham_delta None · KAPI_ACILIYOR None

## Beyan
Bu betik `run.replay_seed` ÇAĞIRMAZ (EDG-036 kill: canlı satırları siler, planları ezer, karneyi arşivler). Yazım yalnız `store` kapısından geçer; `scoreboard.json`, `candidates.jsonl`, `portfolio.json` ve `equity_curve.json:points` DOKUNULMAZ. Barlar ÜRETİM yolundan (`dataset.load`) gelir — EDG-082 ölçümü bilerek ayrı bir minimal temizlik (`temiz_bar_oku`) kullanmıştı, yani bu koşumun bar temizliği ölçümünkinden FARKLIDIR ve iki koşumun işlem sayıları birebir eşit çıkmayabilir. `uyelik` süzgeci üye-olmayanı düşürür ama delist barını GERİ GETİREMEZ: PIT tohum bir ÜST SINIRDIR (tasarım §2).

## Açık sorular
1. trade `id` (T%05d) yeniden numaralama BU BETİĞİN İŞİ DEĞİL: yeni tohum T00001'den başlar ve korunan canlı satırlarla çakışabilir — `dogrulama.trades_kimlik.cift_n` ölçer, düzeltmeyi `ops/trade_id_yeniden_numarala.py` yapar (Rol-1 kararı).
2. aynı kimlikte hem tohum hem canlı plan varsa TOHUM planı düşürülür (canlı kazanır); plan bu kararı yazmıyordu — `kiyas.plan_cakismasi` sayıyı taşır.
3. `--bitis` verilmezse endeks barlarının SON tarihi alınır; o tarih KISMİ bir seans olabilir (`dataset.load` aynı-akşam bacağını taşımaz ama önbellek taze olabilir) — Rol-1 son TAM seansı biliyorsa `--bitis` ile açıkça vermelidir.
4. `equity_curve.points` DOKUNULMADI (ruling 3): yeni tohumun eğrisi (`res.equity`) YAZILMADI, yani eğri hâlâ ESKİ tohumun noktalarını taşıyor. Bu bilinçli — ama defter ile eğri arasındaki bu ayrışma kayda değer bir açık kalemdir.
