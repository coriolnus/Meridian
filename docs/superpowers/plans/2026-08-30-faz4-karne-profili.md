# Faz 4 — `@karne` profili: uygulama planı

> **Ajan işçiler için:** ZORUNLU ALT-SKILL: superpowers:subagent-driven-development.

**Hedef:** Roster'ın ÜÇÜNCÜ profili — `goal.yaml`ın sorduğu soruyu ("deney başarılı mı?")
periyodik, ölçülmüş ve okunur biçimde cevaplayan karne botu. Repo tarafı eksiksiz; canlıda
hiçbir şey yaratılmaz/etkinleştirilmez.

**Substrat:** ÜÇÜNCÜ kullanım — `@sef` (Faz 2) ve `@bekci` (Faz 3) kalıbı BİREBİR izlenir.
Şablon dosyalar: `deploy/hermes/profiles/bekci/` + `ops/bekci_brifingi.py` (en taze, iki dal
denetiminden geçmiş). Sapma yalnız gerekçeyle.

**Spec:** `docs/superpowers/specs/2026-08-27-bot-roster-design.md` §2 satırı:
*"`@karne` | zamanlanmış rapor + `goal.yaml`ın sorduğu soru | amaç"*.

---

## NEDEN `@karne` — ölçümle (2026-08-30, canlı A1)

Faz 3'te ertelenmişti ("Faz 3'ün en güçlü adayı"); bugünkü ölçüm gerekçeyi güçlendirdi:

1. **`goal.yaml` dört soru soruyor, bugün HİÇBİR teslimat cevaplamıyor:**
   `target_return_30d: 0.07` · `min_sharpe: 1.2` · `max_drawdown: 0.16` · `failure_below: -0.04`.
   `self_review.json` ölçüldü: öğrenme makinesini anlatıyor (reflections/ships/calibrations),
   amaç sorusunu DEĞİL.
2. **`goal_failure` olayı defterde 0 kez** (tüm tarih). Sessizlik iki anlama gelir: deney hiç
   başarısız olmadı YA DA rapor hiç koşmadı — ve ikisi ayırt EDİLEMİYOR. `watchdog.
   goal_failure_report` tanımlı (K1, 2026-07-30: o güne dek "deney başarısız olsa bunu
   söyleyecek tek satır kod yoktu") ama yalnız ARIZA anında konuşur. `@karne` bu sessizliği
   bilgiye çevirir: "ölçtüm, başarısız DEĞİL" ile "ölçemedim" farklı cümlelerdir (Uydurma yasağı).
3. **Veri katmanı notu, Görev 1 için:** karne/sermaye eğrisi SQLite'a taşınmış
   (`scoreboard.json.migrated`, `equity_curve.json.migrated`) — okuma YALNIZ `store.read_json`
   üzerinden; ham dosya yolu ölçümü yanlış katmanı ölçer (bu planın yazımında bizzat yaşandı).

## Global Constraints (üç fazın damıtılmışı — tümü ölçülmüş vakalı)

- **HESAP DETERMİNİSTİK, LLM YALNIZ SUNUM.** Dört hükmün dördü Python'da hesaplanır; model sayı
  ÜRETEMEZ ve bir hükmü SUSTURAMAZ. `@bekci` sözleşmesinin aynısı.
- **LLM teslimatın önkoşulu değil:** düşerse ham karne gider. Ardışık sessizlik tavanı yok —
  karne SUSMAZ: kadansı geldiyse her zaman gider (alarm botu değil RAPOR botu; boşken-sessiz
  kuralı BURADA GEÇERLİ DEĞİL ve bu sapma bilinçli — amaç sorusunun cevabı "değişmedi" bile
  olsa periyodik görünür olmalı, yoksa @bekci'nin "duran iş" sınıfına kendisi düşer).
  Dikkat bütçesi kadansla korunur (haftalık), bastırmayla değil.
- **Ölçülemeyen hüküm `None` + neden** — dört sorudan biri hesaplanamıyorsa (veri yok, pencere
  kısa) o satır "ölçülemedi: <neden>" der, iyi huylu sayı UYDURMAZ.
- Teslimat yalnız `meridian.notify.send` (§9.1) · profil duruşu §9.4 üçlüsü + `hooks_auto_accept`
  + kapalı araç takımları + `--accept-hooks` + boş cwd + scrub + veri fence'i — bekci'den kopya.
- Safe-root: `/opt/meridian/var/bots/karne`. Kendi timer'ı (`meridian-karne.{service,timer}`),
  haftalık kadans; slot Görev 3'te filo takvimi ölçülerek seçilir.
- Ajanlar: git yok (salt-okunur dahil) · pytest dışı obs koşumu yok · `monkeypatch.undo()` yok ·
  satır çapası yok · vNNN çakışma kontrolü (v334-v336 alınmış durumda) · mutasyonsuz yeşil kanıt
  değil · CLAUDE.md §2 kapıları aynen.

## Görevler

### Görev 1: Deterministik karne hesabı (`ops/karne_hesap.py` + çivileri)
`hesapla() -> dict`: dört hüküm — her biri `{"deger", "esik", "hukum": GECTI/KALDI/OLCULEMEDI,
"neden"}`. Girdi YALNIZ `store` üzerinden (equity_curve, scoreboard, trades). 30-günlük pencere
hesabı işlem-günü takvimiyle (mutabakat alarmının dersi: takvim günü değil). `goal_failure_report`
ile ÇİFT HESAP ÜRETMEZ: watchdog'un fonksiyonu varsa ÇAĞRILIR, kopyalanmaz (tek-kaynak yasası).
TDD: sentetik store fixture'ları; sınır vakaları (tam eşikte, pencere kısa, veri boş).

### Görev 2: Profil + koşum koşumu (`deploy/hermes/profiles/karne/` + `ops/karne_brifingi.py`)
bekci şekli birebir; farklar: susma-yok kuralı (yukarıda) + tekrar bastırma YOK (periyodik rapor
tanımı gereği tekrar eder; DEĞİŞEN hüküm vurgulanır). v329 kapsaması ÖLÇÜLEREK doğrulanır
(profil önce eksik duruşla → çiviler kırmızı → tamamla; Faz 3'ün usulü).

### Görev 3: Kadans + kurulum + F9
`meridian-karne.{service,timer}` (bekci emsalinden; `[Install]` yok, `is-enabled` kapısı,
sertleştirme + SERTLESTIRILEN listesine giriş, `Environment=` çifti). Haftalık slot filo
takvimine göre. `deploy.sh` + `F9_LISTE` + reçete çivileri — hepsi mevcut sınıf çivilerinin
kapsamına kendiliğinden girer, GİRDİĞİ ölçülür.

## Kapsam dışı
Canlıda kurulum/etkinleştirme (operatörün üç eylemi) · kalan roller (@kod, @ayna, @nobet,
@hipotez — sonuncusu duvar yeniden sınanana dek bloklu) · `goal_failure_report`un kendisinin
değiştirilmesi (çalışan koddur; @karne onu ÇAĞIRIR).
