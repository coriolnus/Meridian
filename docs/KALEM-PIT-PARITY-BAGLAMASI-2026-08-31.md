# Açık kalem — PIT yasasının `parity_report` bağlaması (2026-08-31)

**Durum:** AÇIK, yapılmadı. **Sahibi:** Rol-1 (+ tasarım kararı operatörde: önbellek ve jeton).
**Kaynak:** PIT çivileri turunun devir notu (`docs/DEVIR-PIT-CIVISI-2026-08-30.md`), §4 madde 7.
**Neden ayrı kalem:** `meridian/watchdog.py` **mevcut bir dosyadır**; PIT turları bilinçli olarak
hiçbir mevcut dosyaya dokunmadı. Bu bağlama o disiplini kırar, dolayısıyla kendi turunu ve kendi
çivisini hak eder — bir yasa turunun kuyruğuna eklenmez.

---

## 1. Ne yapılacak

`pitlaw.rapor()` bugün yalnız **suite** tarafından okunuyor (`tests/test_pit_yasasi_v341.py` +
`tests/test_pit_sinif_turetimi_v342.py` — numaralar Rol-1'in `v341`/`v342` taşımasından sonraki
hâl). Yani yasa **CI'da** tutuyor ama **canlıda görünmüyor**: pano "PIT yasası yeşil mi" sorusunu
soramıyor, operatör ihlali ancak suite kırmızısından öğreniyor.

`meridian/watchdog.py::parity_report` içine bir satır eklenirse yasa çalışma zamanında da
okunur:

```python
rows.append({"check": "pit_yasasi", "ok": <hüküm>, "detail": "<ihlal özeti>"})
```

**Emsal aynı dosyada ve birebir uygun:** `parity_report`un **7d) TÜKETİCİSİ OLMAYAN ARTEFAKT**
bloğu (`from . import codelaw as _cl` → `artifact_graph()` → `rows.append({"check":
"artifact_unread", ...})`, `try/except` + `obs.warn` fallback). Yeni blok onun kardeşi olarak,
**ondan SONRA** yazılmalı.

## 2. Üç tasarım kararı — bunlar çözülmeden yazılmamalı

### 2.1 ÖNBELLEK ZORUNLU (en kritik)

`codelaw.artifact_graph()` **mtime damgalı önbelleğe sahiptir** (`_GRAPH_CACHE`, 8 slot) — 7d
bloğu bu yüzden ucuzdur ve kendi şerhi "statik tarama, ucuz" der.

**`pitlaw.rapor()` ÖNBELLEKSİZDİR.** Her çağrıda `_mods` + `codelaw._call_index` (iki kez:
`dogrudan_cagrilar` ve `dolayli_zincirler`) + `sinif_turet` + iki sözleşme denetimi koşar; ikisi
de tüm `meridian/` ağacını gezer. Ölçek için: `codelaw`ın kendi ölçümü soğuk `report()` için
**20,09 sn** diyor (2026-08-16). `parity_report` bir izleme döngüsünden çağrılıyorsa bu maliyet
kabul edilemez.

**Yapılacak:** `pitlaw`a `codelaw._onbellek_oku` / `_onbellege_yaz` gövdesi bağlanmalı — kendi
önbelleğini yazmak DEĞİL, o gövdeyi çağırmak (üç örnekli sınıf; biri düzeltilip ikisi bırakılırsa
sınıf kapanmaz). **Körlük sözleşmesi de gelir:** önbellek isabetinde `codelaw.UNSCANNED` geri
yazılmazsa bekçi "hiç kör noktam yok" der, oysa taramayı hiç yapmamıştır — bu tam olarak
`_onbellege_yaz`ın çözdüğü kusurdur.

### 2.2 ALARM JETONU İHLAL BAŞINA (7d'nin kendi dersi)

7d bloğunun şerhi bunu adıyla yazıyor: `parity:artifact_unread` **TEK genel jetondu** ve mandal
(`integrity_alarmed`) dolu kaldığı sürece YENİ bir artefakt okumasız kalsa hiç alarm üretmiyordu.
Çözüm `orphans` alanını satırda taşımak oldu.

PIT karşılığı: tek `parity:pit_yasasi` jetonu aynı hatayı tekrarlar. Satır **ihlal kimliğini**
taşımalı — ör. `"ihlaller": [f"{k['tarihsel_modul']}→{uc}" for ...]` — ki
`check_integrity_and_alarm` ihlal-başına jeton kurabilsin. İkinci bir PIT ihlali doğduğunda
birincinin mandalı onu yutmamalı.

### 2.3 HANGİ ALAN PANOYA GİDER (rapor tamamı GİTMEZ)

`pitlaw.rapor()` bugün ~20 alanlı bir sözlük; hepsini satıra koymak panoyu boğar ve `detail`
metnini okunamaz yapar. Önerilen asgari:

- `ok` → satırın `ok`u
- `tarihsel_dogrudan` + `tarihsel_dolayli_beyansiz` → ihlal listesi (kimlikli, §2.2)
- `canli_karar_cagrilari` sayısı / `canli_taban` → "borç n/5" biçiminde
- `sinif_celiskileri` → varsa ADIYLA (yasanın kendi kaydı yanlışsa geri kalan hüküm vakumdur)

**Beyanlı olanlar satıra ihlal olarak YAZILMAZ** (`BILINEN_IHLALLER`, `PIT_KORUMALI_ZINCIRLER`) —
ama sayıları görünmeli, yoksa pano "sıfır ihlal" der ve açık borç görünmez olur.

## 3. Çapa etkisi — ölçüldü, güvenli

`watchdog.py`yi gösteren tek satır çapası **`tests/conftest.py:71` → `watchdog.py:195`**
(ölçüm 2026-08-31). Yeni blok 7d'den sonra, **1400+ bölgesine** gireceği için o çapa **kaymaz**.
Yine de: 195'ten ÖNCEye satır eklenirse çapa kırılır ve CI ilgisiz bir sebeple kırmızıya döner
(CLAUDE.md §2 kapısı).

`watchdog.py` `codelaw.OTHER_TRACK_FILES` içindedir (sessiz-yutma beyanı). Yeni bloğun `except`i
7d gibi `obs.warn` çağırdığı sürece ihlal üretmez — sinyal üreten yakalayıcı sessiz değildir.

## 4. Çivi (bu kalem çivisiz kapanmaz)

- **Pozitif kontrol:** sentetik bir ihlalde satırın `ok: False` ürettiği ve ihlal kimliğinin
  satırda taşındığı.
- **Aşırıya kaçmama:** beyanlı ihlal (`BILINEN_IHLALLER`) satırı kırmızıya ÇEVİRMEZ.
- **Jeton çivisi:** iki ayrı PIT ihlalinde ikincisinin alarmı birincinin mandalına takılmaz
  (7d'nin `orphans` çivisiyle aynı desen).
- **Önbellek körlüğü:** isabet dalında `UNSCANNED` geri yazılır (emsal:
  `test_codelaw_kor_nokta_v214.py::test_onbellek_KORLUGU_YUTMAZ`).
- **`parity_report` mevcut çivileri** (`tests/test_yasa6_dort_rapor_v261.py` ve komşuları)
  etkilenen kümeye girer.

## 5. Bu kalem YAPILMADIĞINDA ne kaybediliyor

Yasa CI'da tutuyor, yani **bir ihlal `main`e giremez**. Kaybedilen, canlı görünürlük: PIT yasası
panoda yok, dolayısıyla operatör "bugün yasa yeşil mi" diye bakamaz ve `BILINEN_IHLALLER`deki
açık borç panoda görünmez. Kalem bu yüzden **acil değil ama açık** — riski "sessiz ihlal" değil,
"sessiz borç".

---

## 6. Rol-1 yeniden-ölçüm şerhi — main'e alınırken (2026-08-31)

§3'ün çapa iddiası main'in bugünkü hâlinde YENİDEN ÖLÇÜLDÜ ve ÇÜRÜDÜ — iyi yönde:
`tests/conftest.py` içindeki `watchdog.py:195` metni CANLI ÇAPA DEĞİL, 2026-08-24 v282
turunda emekli edilmiş çapanın **mezar taşı yorumudur** ("ÇAPA SEMBOLE ÇEVRİLDİ" bloğu —
grep isabeti bağlam okunmadan canlı çapa sayılmış). Testlerden `watchdog.py`ye işaret eden
canlı satır çapası YOKTUR; 7d sonrasına blok eklemek hiçbir CI çapasını kırmaz. Bilinen tek
satır-numaralı atıf `meridian/web/app.js` içinde (`watchdog.py:660-661`, tasarım-sözü yorumu)
— bu kalemin dokunacağı bölge değil, ama bloğu 660'tan ÖNCE ekleyecek olan bilsin.
§3'ün geri kalanı (OTHER_TRACK_FILES + `obs.warn` fallback) doğrulandı, geçerli.
Üç tasarım kararı (§2.1 önbellek gövdesi + UNSCANNED geri yazımı, §2.2 ihlal-başına jeton,
§2.3 asgari alan + beyanlı sayılar görünür) bu oturumda KABUL edilmişti; kalem EDG-062
(b) bağlaması bittikten sonra kendi turunu bekliyor. Orijinal §3 kanıt olarak yerinde.
