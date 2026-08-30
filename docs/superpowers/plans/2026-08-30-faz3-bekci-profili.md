# Faz 3a — `@bekci` profili: uygulama planı

> **Ajan işçiler için:** ZORUNLU ALT-SKILL: superpowers:subagent-driven-development.

**Hedef:** Roster'ın İKİNCİ profili — **süregelen ve duran** durumları fark eden bekçi.
Repo tarafı eksiksiz; canlıda hiçbir şey yaratılmaz/etkinleştirilmez.

**Spec:** `docs/superpowers/specs/2026-08-27-bot-roster-design.md` §2 (`@bekci` = *"sessiz arıza
sınıfı"*), §3 (*"Faz 3 — kalan roster, her biri kanıtlandıkça"*), §9 (güvenlik duruşu).

**Zemin:** Faz 2 substratı HAZIR ve çivili — profil dağıtımı (`distribution.yaml`), koşum koşumu
kalıbı (`ops/sef_brifingi.py`), §9.4 üç çivi, F9 kaydı, kurulum reçetesi. Bu faz o substratın
İKİNCİ kullanıcısıdır; yeni altyapı yazılmaz.

---

## NEDEN `@bekci`, ve NEDEN `@hipotez` DEĞİL — ölçümle

Spec `@hipotez`'i *"en büyük ölçülmüş boşluk (5 günde 0 hipotez, 20 Tem'den beri 0 ship)"* diye
işaretlemişti. **O ölçüm DEFTERE bakıyordu; canlı döngü başka bir şey söylüyor** (A1, 2026-08-30):

```
warmup_sprint (saatlik, 93 turdur aynı): evaluated=40 · cleared=0 · best=null
  neden: KISMEN AYIRT EDİLEMEZ 36 · AYIRT EDİLEMEZ 2 · P(ΔS>0)=0.09/0.13 < gerekli 0.99
warmup_merdiven_kilitli: carpan=1 · duvar=1 · budget=10 · k_max=2 · ardisik=93
hypotheses.jsonl: 60 kayıt, HEPSİ reddedilmiş (32 backtest · 25 guard · 2 superseded · 1 confirmation)
sprint_cadence_skip son 3 gün: 191 kez "tetik_yok(gun=N<7, taze=0<5)"
```

**Sistem hipotez KITLIĞI çekmiyor — saatte 40 aday değerlendiriyor. Çektiği şey İSTATİSTİKSEL
GÜÇ.** 40'ın 36'sı "ayırt edilemez", çünkü sonda bütçesi 10 ve k_max 2, ikisi de `duvar=1`'e
çakılı. Birimin kendi şerhi: *"Duvar bir ÖLÇÜMDÜR ama SÜRESİ YOKTUR ve yeniden sınanmaz."*

**Ve daha fazla hipotez üretmek bunu ÖLÇÜLEBİLİR BİÇİMDE KÖTÜLEŞTİRİR:** eşik metninin kendisi
`K=40 aday cezası dahil` diyor — aday sayısı arttıkça ön eleme eşiği SIKILAŞIR. `@hipotez` bugün
kurulsa daha az aday geçerdi.

**Ruling:** Faz 3a = `@bekci`. Yanlışsa bedeli: profil adı ve SOUL yeniden yazılır, substrat aynı
kalır — ucuz. `@hipotez` merdiven duvarı yeniden sınandıktan SONRA yeniden değerlendirilir.

### Ve bulgunun kendisi `@bekci`'nin gerekçesi
Yukarıdaki zinciri bulmak ALTI ÖLÇÜM aldı, ve her halkası `info` seviyesinde saatlik loglanıyor:
son 3 günün 1645 olayının **1580'i `info`** (54 warn, 11 alarm). `ardisik=93` bir sayaçtır ve
**hiçbir kod onu okumaz**. Bu, kural yazılamayan sınıftır: bir watchdog kuralı arızayı ÖNCEDEN
bilmeyi gerektirir; `@bekci`'nin işi *"bu N turdur aynı ve kimse bakmadı"* demektir.

`@sef`ten AYRI BİR KALIP: `@sef` hazır hesaplanmış özetleri SIRALAR; `@bekci` ham defter üzerinde
YENİ bir ölçüm hesaplar ve **yokluğa** bakar (duran şeyler), varlığa değil.

## Global Constraints
- **TESPİT DETERMİNİSTİKTİR, LLM DEĞİL.** Süregelen/duran durumları Python bulur; modelin işi
  yalnız SIRALAMAK ve NEDEN önemli olduğunu bir satırda söylemektir. Model bir arıza UYDURAMAZ
  çünkü listeyi o üretmiyor.
- LLM düşerse ham liste yine gider (`@sef` sözleşmesinin aynısı).
- Boşken SESSİZ; ve **aynı takılı durumu her gün tekrar etme** — ilk geçişte söyle, sonra yalnız
  DEĞİŞTİĞİNDE (dikkat bütçesi, `@sef`in dersi).
- Teslimat yalnız `meridian.notify.send` (§9.1). Güvenlik duruşu §9.2/§9.3/§9.4 — `@sef`in
  profil şablonu birebir izlenir (guard kancası · `hooks_auto_accept` · kapalı araç takımları ·
  deny listesi · kendi safe-root'u).
- Canlıda profil YARATILMAZ, birim ETKİNLEŞTİRİLMEZ.
- Ajanlar git komutu koşmaz; tam suite yalnız Rol-1'de; `state/`e yazma; satır çapası yazma.

---

## Görev 1: Deterministik tespit katmanı (`ops/bekci_tarama.py`)

**Dosyalar:** Oluştur `ops/bekci_tarama.py` · Oluştur `tests/test_bekci_tarama_v333.py`

**Arayüz (Görev 2 buna bağlı):** `tara(gun: int = 3) -> dict` — `{"takili": [...], "duran": [...],
"olculemedi": [...]}`. Her kalem `{"ad", "deger", "ilk_gorulme", "son_gorulme", "kanit"}` taşır.

Üç sınıf, üçü de `state/events.jsonl`den ÖLÇÜLÜR:
1. **TAKILI** — aynı `(event, sebep)` çifti eşiği aşacak kadar tekrarlıyor VE değeri değişmiyor.
   `ardisik` alanı taşıyan olaylar doğrudan sayılır (bugün yalnız `warmup_merdiven_kilitli`).
2. **DURAN** — geçmişte düzenli tekrarlayan bir olay ARTIK GELMİYOR. Yokluk, varlıktan daha zor
   görülür ve bu depoda adı konmuş bir sınıftır.
3. **ÖLÇÜLEMEDİ** — ayrıştırılamayan satır, alanı olmayan olay. `None` + neden; sıfır sayılmaz.

**İYİ HUYLU GÜRÜLTÜ AYIKLANIR, ve bu ölçümle yapılır:** `sprint_cadence_skip` son 3 günde 554 kez
`saat_dilimi_disinda` (pencere dışı — normal) ve 95 kez `zaten_kosuyor` (normal). Aynı olayın
191 `tetik_yok(...taze=0<5)` kaydı ise DURUM sinyalidir. Sayı değil SEBEP ayırır; bir olayın
sıklığı tek başına arıza değildir.

TDD adımları: sentetik `tmp_path` defteriyle üç sınıf ayrı ayrı kırmızı doğar; iyi huylu sebebin
listeye GİRMEDİĞİ pozitif kontrol; bozuk satırın `olculemedi`ye düşüp sıfır sayılmadığı çivi.

## Görev 2: Profil + koşum koşumu (`@bekci`)

**Dosyalar:** Oluştur `deploy/hermes/profiles/bekci/{distribution.yaml,config.yaml,SOUL.md}` ·
Oluştur `ops/bekci_brifingi.py` · Oluştur `tests/test_bekci_brifingi_v332.py` ·
Değiştir `tests/test_bot_profil_durusu_v329.py` (yeni profil ÇİVİLERE OTOMATİK girer —
`_profiller()` dizini tarar, yani üç §9.4 çivisi kendiliğinden kapsar; bunu DOĞRULA)

`@sef`in şeklinden birebir kopyalanır — kuru-koşum varsayılan, boşken sessiz, LLM düşerse ham,
`--accept-hooks`, `HERMES_HOME` kimlik doğrulaması, boş cwd, scrub'lı prompt, veri fence'i,
ardışık sessizlik tavanı. **İkinci bir tasarım ikinci bir hata sınıfıdır.**

Safe-root: `/opt/meridian/var/bots/bekci` (dizin sınıfı `/var` zaten rsync dışı ve gitignore'lu).

TEKRAR BASTIRMA burada `@sef`ten DAHA SERT: takılı bir durum tanımı gereği her gün aynıdır.
Kural — bir kalem ilk geçişte bildirilir, sonra yalnız DEĞERİ değişince ya da uzun bir yeniden-
anma aralığı dolunca. Damga harness'in.

## Görev 3: Kadans ve kurulum

`meridian-brifing.service` ikinci bir `ExecStart` almaz — **`@sef` ile AYNI kadansa binmez**:
`@bekci` kendi timer'ını alır (`meridian-bekci.{service,timer}`), çünkü ikisi ayrı artefaktın
sahibi ve biri düşerse öteki koşmalı. Faz 1'in "tek sarmalayıcı" dersi burada TERSİNE geçerli:
o iki teslimat AYNI mesajı kuruyordu, bunlar AYRI mesaj.
`deploy.sh` kurulum adımı + `is-enabled` kapısı + `F9_LISTE` üç dosya — hepsi `@sef` emsalinden.

---

## KAPSAM DIŞI, gerekçeli
1. **Merdiven duvarının yeniden sınanması.** Birimin kendi şerhi: *"Duvarı gevşetmek bir ÖLÇÜM
   işidir, bir ops kararı değil"* ve etkinin YÖNÜ bilinmiyor (merdiveni açmak K'yı büyütür,
   eşiği sıkar — EDG-2026-058). Ön-kayıt kartı ister (CLAUDE.md madde 3) ve OPERATÖR KARARIDIR.
   Bu planın en değerli çıktısı o kalemi GÖRÜNÜR kılmasıdır, kendi başına çözmesi değil.
2. **`@hipotez`** — yukarıdaki hüküm; duvar sınandıktan sonra yeniden değerlendirilir.
3. **Canlıda kurulum/etkinleştirme** — operatörün üç eylemi, `deploy.sh` basar.
