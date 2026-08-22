# Ö-49 ÇAPA/BEYAN ÇÜRÜMESİ — KALAN ENVANTERİ (2026-08-22)

**Kapsam:** WP6 tahta kalemi "Ö-49 çapa/beyan çürümesi kalanı". Bu gecenin iki satır-çapası
çürümesi düzeltildikten SONRA `codelaw.report()` ne taşıyor + ROADMAP'te 2026-08-1x tarihli
bayat "GÜNCEL DURUM/bekliyor" örneklemi. **Salt envanter — kod/test/ROADMAP DEĞİŞTİRİLMEDİ;
hüküm yok, sınıf + kanıt + reçete var.** Okuyucu: Rol-1 (tahta kalemi işlensin diye).

**Ölçüm:** `codelaw.report()` bu ağaçta 2026-08-22 koşuldu. Boş kovalara dair pozitif bulgu:
`silent_handlers` 0 · `artifact_violations` 0 · `orphan_patterns` 0 · `stale_claims` 0 ·
`stale_line_anchors` 0 · `unscanned` 0. Yani **İHLAL kovalarının hepsi boş**; kalanların tamamı
"ölçülemeyen/beyanlı" kovalarında (`ok=False` yapmazlar).

**Ölçülemeyenler (UYDURMA YASAĞI):** git tarihçesine BAKILMADI (sözleşme: bu oturum git komutu
koşmaz) ve canlı A1'e BAKILMADI (gerek yoktu; tüm bulgular repo-yerel). `engine.py` şasisinin
git geçmişinden kurtarılabilirliği = **None** (neden: git yasağı; ayrıca RAPOR.md "repoya hiçbir
bayt yazılmadı" diyor — muhtemelen hiç commit'lenmedi).

---

## 1. `line_anchor_unresolved` — 28 kayıt, 5 grup (tamamı `hedef_yok`)

Aracın adres defteri `meridian/ + tests/ + ops/` köklerinden kurulur (`codelaw.py`
`_EK_CAPA_KOKLERI`; `docs/` bilerek dışarıda, `research/` hiç sayılmamış). Bu 28 kaydın
**hiçbiri araç tarafından çürük İLAN EDİLMİŞ değil** — araç hüküm KURAMADIĞINI dürüstçe
raporluyor. Ben her grubu elle hedefine karşı ölçtüm:

| # | Grup (kayıt sayısı) | Kaynak → Çapa | Elle doğrulama (bu tur) | SINIF |
|---|---|---|---|---|
| G1 | broker.py ×4 (41, 299, 320, 321) | `research/olcumler/edg026_slot20_2026-08-12/olcum.py` 178/299/306 | **AYAKTA** — 178=`def _rampa_fn`, 299=monkeypatch ataması, 306-307=yayılım assert'leri; satır satır birebir tuttu | **Donmuş-artefakt istisnası** (çürüme YOK) + araç kör noktası (`research/` adres defterinde değil) |
| G2 | tests ×5: test_derisk_rampa_kablosu_v237 (9, 57, 156, 173), test_mutborc_broker_derisk_mult_v148 (153) | aynı edg026 `olcum.py` 178/302/304/306 | **AYAKTA** — 302/304 öz-sınama assert'leri birebir; üstelik v237 `_olcum_rampasi` İKİZ KOPYASIYLA sapmayı zaten test düzeyinde çiviliyor | **Donmuş-artefakt istisnası** (çürüme YOK; sapma riski v237 ikiziyle ayrıca sigortalı) |
| G3 | trend_shadow.py ×8 (43, 44, 45, 47, 173, 219, 253, 388) + test_trend_shadow_v144 (173) = ×9 | `engine.py` 21/22/23/55-61/75-78/151-196/171-190/198-260 | **DOĞRULANAMAZ** — `engine.py` REPO'DA HİÇ YOK (tek iz: `research/olcumler/trend_rafine/kod_damgasi.json` içindeki sha256 `579eade5…`, EDG-2026-009 şasisi). Çapaların gösterdiği satırlar hiçbir yerde okunamıyor | **GERÇEK RİSK: kanıt zinciri kopuk.** Çürüme değil (donmuş şasi değişmez) ama 9 çapanın hiçbiri repo içinden sınanamaz; tek güvence hash + sabitlerin trend_shadow'da sayı olarak taşınması (FRICTION_BPS=10, ATR22, K=3.5, N=10) |
| G4 | hermes.py ×2 (3326, 3327) | `tools/skill_usage.py:81`, `hermes_constants.py:56-67` (hermes-agent v0.18.2, depo DIŞI) | **AYAKTA** — `~/.hermes/hermes-agent/` altında elle doğrulandı: skill_usage.py:81 = `def _skills_dir()`, hermes_constants.py:56-67 = HERMES_HOME env çözümü; metin zaten sürüm-damgalı ("ÖLÇÜLDÜ, VARSAYILMADI, v0.18.2, 2026-08-13") | **Bilinçli dış-kaynak atfı** (araç depo dışını göremez; beyanı sürümüyle yazılı) |
| G5 | test_codelaw_kor_nokta_v214 ×7 (284, 305, 648, 665×2, 669, 679) + test_beyan_bayatligi_v246 (250) = ×8 | `karar.py:3`, `hedef.py:999/1`, `yok_boyle_bir_dosya.py:12`, `ayni.py:99`, `dosya.py:123` | **SENTETİK** — hepsi çapa-yasasının KENDİ testlerinin tmp_path fikstürleri / docstring örnekleri (`yok_boyle_bir_dosya.py` adı kendini anlatıyor; `dosya.py:123` "bu biçim YASAK" örneği) | **Aracın kendi test verisine kör noktası** (kendi kendine gürültü; çürüme yok) |

**Sayım:** 4+5+9+2+8 = 28 ✓. **Sınıf dağılımı: gerçek risk 9 (G3) · donmuş-artefakt 9 (G1+G2)
· bilinçli dış-atıf 2 (G4) · öz-gürültü 8 (G5). Gerçek "çürümüş" (yanlış satır gösteren) çapa: 0.**

## 2. `unread` — 37 artefakt: **hepsi beyanlı, ihlal 0**

`artifact_graph()`: unread=37, `declared_sinks`=37, `violations`=**[]**, `stale_sinks`=**[]**.
37'nin 37'si `DECLARED_SINKS`'te gerekçesiyle kayıtlı (bilinçli muafiyet). Liste rapora aynen
girer; ihlal olmadığından tek tek açılmadı.

**Tek dikkat kalemi — `auth.json` (DECLARED_SINKS'in 38. anahtarı):** grafikte HİÇ YOK
(unread'e girmiyor, `artifacts`'a çözülmüyor) çünkü yazımı `store.write_text` (auth.py:133) ve
`write_text` `WRITE_CALLS`'ta DEĞİL (codelaw.py:306 — yalnız `write_json/jsonl/update/merge`);
okuma da `Path.read_text` (auth.py:108). Yani `stale_sinks` bekçisi bu beyanı HİÇ
POLİSLEYEMEZ — codelaw.py:571-578'in kendi uyardığı "ölü muafiyet" şekli. Beyanın metni bunu
BİLİYOR ve söylüyor ("secrets.json ile AYNI sınıf … statik graf göremiyor") → sınıf: **bilinçli
muafiyet + aracın yapısal kör noktası** (yeni bulgu değil, ama Ö-49 envanterinde adıyla durmalı:
`store.write_text` kullanan 7 modül — auth, config, earnings, hermes, memory, skill_evolve,
run — artefakt grafiğinin tamamen dışında).

## 3. `unverifiable_claims` — 1 kayıt: `intraday_bars/*.jsonl`

Gelecek-zamanlı tüketici vaadi (Faz-5/6 kanıt korpusu, kart ailesi EXE-2026-002), `sinanamaz`
alanı + devir şartı ("ölçüm arşivi okuduğu gün BU SATIR KALDIRILMALI") yazılı; Rol-1 hükmü
2026-08-08 "yazım sökülmez". Retention 120 gün, sayaçlı. Sınıf: **bilinçli muafiyet / borç
defteri** — tasarımı gereği görünür kalır, bugün yapılacak iş yok.

## 4. `unresolved_artifact_calls` — 25 (not düzeyinde)

24 `ad_cozulemedi` = parametre/değişken üzerinden geçen adlar (store.py'nin kendi jenerik
sarmalayıcıları ×6, watchdog jenerik döngüleri ×6, ledger/ledgerstamp öznitelik atıfları vb.) —
statik analizin bilinen sınırı, adlı kovada dürüstçe sayılıyor. 1 `desen_beyanli` =
bararchive.py:114 → §3'teki beyanlı desen. **Sınıf: aracın beyanlı kör noktası; iş yok.**

---

## 5. ROADMAP 2026-08-1x "GÜNCEL DURUM/bekliyor" — BUGÜN bayat örneklem (tam tarama DEĞİL)

| # | Satır(lar) | Bayat iddia | Kanıt (bugünkü gerçek) |
|---|---|---|---|
| S1 | ROADMAP:2301 (§6 indeks) | EXE-2026-005 "**registered (08-17) · hüküm BEKLİYOR (Rol-1)**" | Kart `research/cards/EXE-2026-005-dinlenen-limit.yaml:67` = `status: measured  # 2026-08-22 Rol-1 HÜKMÜ`; ROADMAP:223 aynı işi "H6 ✅ KAPANDI 2026-08-22" damgalamış. **§6 satırı kartla ve §2 ile çelişiyor — EXE-006 vakasının (a033256) birebir yüzeyi** |
| S2 | ROADMAP:2304 (§6 indeks) | EDG-2026-040 "**registered (08-13) · ÖLÇÜLMEDİ — ön-kayıt**" | Kart `research/cards/EDG-2026-040-friksiyon-dayaniklilik.yaml:80` = `status: measured  # 2026-08-22`; ROADMAP:178 "measured (2026-08-22) — Ö1 DÜŞTÜ", ROADMAP:193 hükmü rakamlarıyla taşıyor. Aynı belge içinde iki durum |
| S3 | ROADMAP:270-284 (§3 GÜNCEL DURUM başlığı, 2026-08-13 ~20:30Z) | "**AÇIK ÜRETİM ARIZASI:** /api/diagnostics … v243 turu bunu kapatıyor" | v243 2026-08-14'te İNDİ ve kapattı — ROADMAP:2535 (§5): "parity_report 17,4→7,8 / 11,9→2,1 sn, sayfa artık teşhis ucunu BEKLEMİYOR"; §2 tablosu (ROADMAP:251) kalemi kapanmış sayıyor |
| S4 | aynı blok, ROADMAP:283-284 | "**İKİNCİ ACİL OPERATÖR KALEMİ: BİLDİRİM KANALI (N1)** — kanal yok, 29 alarm teslim edilemedi" | A2/N1 2026-08-22 KAPANDI — ROADMAP:224 "KANAL CANLI", ROADMAP:2013 "✅ KAPANDI (2026-08-22): Telegram canlı, test teslim edildi", ROADMAP:2463 |
| S5 | aynı blok, ROADMAP:275-276 | "beyin zinciri AYRIK (**nous=tencent**, gemini=flash-latest)" | 2026-08-14'te zincir DEĞİŞTİ — ROADMAP:2533: `tencent/hy3:free` katalogda hiç yokmuş; zincir artık `nemotron-3-ultra:free` → `gpt-oss-20b:free` |
| S6 | ROADMAP:332 (WP8 özet satırı) | "**AÇIK ÜRETİM ARIZASI: /api/diagnostics soğuk çağrıda 16,7s (v243 kapatıyor)**" | S3 ile aynı kanıt (ROADMAP:2535). Özet tablosu hâlâ "açık arıza" gösteriyor |
| S7 | ROADMAP:1241-1243 (WP8 detay) | "🆕 **AÇIK ÜRETİM ARIZASI (2026-08-13)** … *öncelik: yüksek*" | S3 ile aynı kanıt — üçüncü kopya; aynı arıza üç yerde "açık" duruyor |
| S8 | ROADMAP:1886-1890 (madde #38, 2026-08-14) | "run.py:194-204 ve sermaye.py:30-35 yorumları YANLIŞ … **iki modül yorumu açık kaldı**" | İkisi de mezar-taşıyla DÜZELTİLMİŞ: run.py:200 "↑ ARTIK BÖYLE DEĞİL (2026-08-14, v245-D…)", sermaye.py:46 "↑ ÜSTTEKİ GEREKÇE YANLIŞLANDI…". Kalem kapanmış işin kaydını taşıyor |
| S9 | ROADMAP:2178 (operatör envanteri md.2) | "Bildirim kanalı: Telegram/webhook — teslim zinciri hazır, **kanal boş**" | S4 ile aynı kanıt (ROADMAP:2013/2463) — dördüncü N1 kopyası |

**Kontrol edilip bayat ÇIKMAYAN (dürüstlük kaydı):** madde #37 `seed_boundary` otorite sorusu
(ROADMAP:1871, 2026-08-14 "Rol-1 kararı bekliyor") — kapanış izi bulunamadı, hâlâ gerçekten
açık görünüyor (bayat değil, yaşlanıyor; 8 gün). C3 QC-login (ROADMAP:2114-2119) operatör-bloklu
ve iddiası hâlâ doğru.

**Desen notu (sayı, hüküm değil):** S3-S7+S9'un altısı AYNI iki kapanışın (v243, N1) farklı
yüzeylerdeki kopyaları — §3 başlığı, §3-WP özet tablosu, WP detayı ve operatör envanteri aynı
gerçeği ayrı ayrı taşıyor; kapanış tek yerde işlenince diğerleri kalıyor. S1-S2 ise kart↔§6
çelişkisi — `v251` çivisinin kartı bağladığı ama §6 SATIRINI bağlamadığı boşluk (çivi
`HUKUM*.md`↔kart status ölçer; §6 metnini ölçen şey yok).

---

## 6. KAPATMA REÇETELERİ (ucuzdan pahalıya; hepsi seçenek, karar Rol-1/operatörde)

1. **[~30 dk, sıfır kod] ROADMAP düzeltme turu (S1-S9):** Rol-1 tek oturumda dokuz satırı
   günceller (S3-S7+S9 için altı yüzeyde iki kapanışı işlemek; S1-S2 için §6 satırlarını kart
   status'una eşitlemek; S8'i kapatmak). En yüksek getiri: §6↔kart çelişkisi K-defteri okumasını
   yanıltan sınıftır (EXE-006 vakasındaki üç-okuyucu analizi).
2. **[ucuz, tek dosya] G5 öz-gürültüsünü sustur:** codelaw'un kendi test fikstürlerini
   `line_anchor_unresolved`dan ayıklamak (ör. fikstür satırlarına `çapa-mezar-taşı` işareti veya
   testler-kendi-adres-uzayında kuralı). 28 kayıt → 20'ye iner, sinyal/gürültü düzelir.
   (meridian/codelaw.py veya tests/ dokunuşu — Opus brief'i ister.)
3. **[ucuz-orta, tek dosya] G1/G2 donmuş-artefakt çapalarını beyanlı yap:** ya `research/olcumler`
   adres defterine SALT-OKUNUR çözüm kökü olarak eklenir (9 kayıt ölçülür hâle gelir — bu tur elle
   yaptığımı araç her koşuda yapar), ya da bu çapalara "donmuş-artefakt" işaret sözleşmesi konur.
   Not: v237 ikiz-kopya çivisi semantik sapmayı zaten tutuyor; bu reçete yalnız envanter
   temizliği.
4. **[orta] `auth.json` ölü-muafiyet kapısı:** `write_text`'i (ve/veya erişimci-okumaları)
   artefakt grafiğine dahil etmek YA DA auth.json beyanını `secrets.json` gibi erişimci-iddia
   (`declared_claims` kind) sınıfına taşımak — böylece beyan yeniden polislenebilir olur.
   Dikkat: `write_text` eklenirse 7 modülün metin-artefaktları (lessons.md, scoreboard…) birden
   grafiğe girer ve her biri okuyucu/beyan triyajı ister — kapsamı bir kartla sınırlamak akıllıca.
5. **[pahalı / belki imkânsız] G3 `engine.py` kanıt zinciri:** (a) şasi yeniden üretilip
   `kod_damgasi.json` sha256'sına karşı doğrulanır ve `research/olcumler/trend_rafine/` altına
   arşivlenir (9 çapa ölçülür olur) — kurtarılabilirlik bu oturumda ölçülemedi (git yasağı);
   commit'lenmediyse yeniden-üretim gerekir; YA DA (b) trend_shadow.py'deki 8 çapa satır-numarasız
   içerik-atfına çevrilir (fonksiyon adı + sabit değeri — codelaw'un kendi "ÇAPA SEMBOLDÜR"
   doktrini, codelaw.py:427-431) — meridian/ dokunuşu, Opus brief'i ister.
6. **[iş yok] `intraday_bars/*.jsonl` + G4 dış-atıflar:** devir şartları kendi metinlerinde
   yazılı; Faz-5/6 ölçümü arşivi okuduğu gün / hermes-agent sürüm atladığı gün ele alınır.

---
*Üretim: WP6/Ö-49 envanter turu, 2026-08-22. Ölçüm aracı: `codelaw.report()` (karta tabi bir
ölçüm değil, bekçi raporu). Bu belge tarihli bir KAYITTIR — satır numaraları yazıldığı günün
ağacına aittir (codelaw docs/ istisna gerekçesi, codelaw.py:1319-1323).*
