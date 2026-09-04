# EDG-2026-071 K1 ölçüm girdisi — DONMUŞ (Rol-1, A1 çekimi)

Kaynak: `.superpowers/sdd/2026-09-04-edg071/girdi/hypotheses_donmus_2026-09-04.jsonl` (Rol-1'in A1'den
çektiği canlı `state/hypotheses.jsonl` donmuş kopyası, 60 satır, 2026-07-14T10:12:40Z →
2026-08-21T18:02:05Z, `source` alanı okunabilir). sha256:
`6a9de67f823b761d38519fab71857cadb109873559873774db6e291f6c80e420` (bu kopyayla doğrulandı —
`shasum -a 256`, ajan turu 2026-09-04). Bu dosya EDG-071 ölçüm ajanı tarafından
`research/olcumler/edg071_hayalet_suzgec/girdi/` altına DEĞİŞTİRİLMEDEN kopyalanmıştır; commit'te
git BLOB'una bağlanır (EDG-059 kuralı — kart girdisi çalışma ağacına değil blob'a bağlanır).

Üretici (`source`) dağılımı (60 satır): `deterministic` 25 · `hermes:gemini` 12 · `hermes:nous` 10 ·
`deterministic:virgin` 8 · `coordinate_search` 2 · `cf_evidence` 2 · `sprint_search` 1.

ÖLÇÜM SINIRI (ADIM-0/D2 ile birlikte okunur): repo'nun git tarihi 2026-07-31T10:08:23+03:00'te
başlıyor ("Meridian ilk sürüm kontrolü — WP-H git kapısı", `d9c3f24b`). Bu girdinin 60 satırından
42'si bu tarihten ÖNCEye damgalı: 9 GÜN TÜMÜYLE öncesi (41 satır: 07-14/19/20/21/22/23/27/28/29) +
2026-07-31'in KENDİSİNİN erken saati (1 satır, 02:52 UTC — o günün İKİNCİ satırı, 11:34 UTC, İLK
repo commit'inden SONRAdır ve ÇÖZÜLÜR; çözümleme birimi TEK TEK `ts`dir, gün DEĞİL). O `ts`ler
için `git rev-list -1 --before=<ts> main` boş döner (repo'da henüz commit YOK), yani o anın motor
sabit-zinciri git blob'undan ÇÖZÜLEMEZ. `olcum.py` bu satırları "ölçülemedi: git-tarihi-öncesi"
diye AYRI sayar (uydurma yasağı — var olmayan bir commit'e dayanan hüküm üretilmez); K1 birincil
oranı yalnız çözülebilen 18 satır üzerinden raporlanır, 42/60 ayrıca ADIYLA görünür.
