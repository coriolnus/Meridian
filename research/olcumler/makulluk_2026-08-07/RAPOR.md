# MAKULLÜK dedektörünün iki gerçek bulgusu — kök, ölçüm, onarım (2026-08-07)

Girdi: `research/olcumler/butunluk_dokumu_2026-08-06/RAPOR.md` §3.6 (D6) ve §3.7–3.8 (D7).
Bu tur ikisini de kapatır. Ortak ders: **bir dedektörü susturmanın iki yolu var, biri dürüst.**
Deseni gevşetmek bekçiyi kör eder; onarım artığın (ya da yanlış sınıflamanın) KAYNAĞINDA olmalı.

---

## BULGU 1 — `yeniden_hesap:orphan_state_files` (7 dosya)

### Yetim envanteri, KAYNAK KAYNAK

| # | dosya | kaynak | hüküm |
|---|---|---|---|
| 1 | `goal.yaml.bak-202608021652` | `dagit.sh:227` (o günkü hâli) | üretim artığı — TAŞI |
| 2 | `goal.yaml.bak-202608030421` | `dagit.sh:227` | üretim artığı — TAŞI |
| 3 | `goal.yaml.bak-202608031627` | `dagit.sh:227` | üretim artığı — TAŞI |
| 4 | `bounds.yaml.bak-202608021652` | `dagit.sh:227` | üretim artığı — TAŞI |
| 5 | `earnings.csv.20260803T100416Z.bak` | **depoda üreticisi YOK** → elle bakım penceresi | artık — TAŞI |
| 6 | `earnings.csv.sedbak` | **depoda üreticisi YOK** → `sed -i.sedbak` | artık — TAŞI |
| 7 | `auth.json` | üretici `auth._write` | **YETİM DEĞİL** — dedektörün kör noktası |

**1–4 neden kesin `dagit.sh`:** o satır `STATE_KOPYALA` listesindeki her dosya için
`state/$_sf.bak-$(date -u +%Y%m%d%H%M)` yazıyordu ve liste `git ls-files state/` ile türetiliyor —
bugün tam olarak **iki** dosya: `state/goal.yaml`, `state/bounds.yaml`. Yetim adları da damgaları da
birebir bu kümeyle ve o günlerin dağıtım pencereleriyle örtüşüyor.

**5–6 neden `dagit.sh` DEĞİL:** `earnings.csv` git-izli değil, yani `STATE_KOPYALA`ya hiç girmez.
`20260803T100416Z` damga biçimini üreten hiçbir betik depoda yok (`bakim_h9.sh` benzer biçimi
kullanır ama `/home/ubuntu/backups/state-premigration-*.tar.gz` yazar). İkisi de elle işlem artığı.

**Yerelde sıfır artık var** (`ls state/ | grep bak` → boş): sınıf yalnız A1'de doğuyor, çünkü
kaynağı A1'e SSH ile yazan bir satırdı.

### Onarım (a) — kaynak: `dagit.sh`

Yedek artık `/opt/meridian/backups/state/` altına yazılıyor (`mkdir -p` + damgalı ad).
`backups/` rsync dışlama listesinde olduğu için yedekler dağıtımla ne ezilir ne silinir.
Mesajlar yeni yolu gösteriyor ve hata dalı **geri dönüş komutunu birebir yazıyor**:

```
ssh ubuntu@<IP> "cp -p /opt/meridian/backups/state/goal.yaml.bak-<damga> /opt/meridian/state/goal.yaml"
```

Ek olarak `[5/5]`in sonuna **salt-okuma artık bekçisi** kondu: pencere kapanırken `state/` içinde
`*.bak-*|*.sedbak|*.bak` varsa operatör aynı oturumda görür (5–6 sınıfı bir betikten değil bir
alışkanlıktan doğuyor; kodla kapatılamaz, görünür kılınabilir).

### Onarım (b) — `ops/state_yetim_temizle.sh`

TAŞIR, **silmez** — bunlar geri-dönüş kopyalarıdır. Kuru koşu varsayılan; `--uygula` ile taşır.
`--yerel <kök>` SSH'sız çalışır (testler ve host-içi koşum). Öncesi/sonrası listeler, dedektörü
önce ve sonra koşar. Dedektör koşamazsa **sayı uydurulmaz**, atlanan adım adıyla yazılır.

Kuru koşu çıktısı (canlı listenin birebir kopyası bir kum-havuzunda):

```
=== state yetim temizliği · mod=yerel · kök=<KÖK> · KURU KOŞU ===
--- [1/4] ÖNCESİ: state/ içindeki yedek artıkları ---
  ... bounds.yaml.bak-202608021652
  ... earnings.csv.20260803T100416Z.bak
  ... earnings.csv.sedbak
  ... goal.yaml.bak-202608021652
  ... goal.yaml.bak-202608030421
  ... goal.yaml.bak-202608031627
  toplam: 6 dosya
--- [2/4] dedektör (ÖNCE) ---
  · dedektör ADIMI ATLANDI: '<KÖK>' bir Meridian checkout'u değil (yalnız state temizliği ölçüldü)
--- [3/4] TAŞIMA: kuru koşu, hiçbir şey yapılmadı ---
  mv <KÖK>/state/bounds.yaml.bak-202608021652  →  <KÖK>/backups/state/bounds.yaml.bak-202608021652
  ... (6 satır)
--- [4/4] SONRASI: kuru koşuda ölçülmez (taşıma olmadı) ---
>> KURU KOŞU BİTTİ. Uygulamak için: bash ops/state_yetim_temizle.sh --uygula
```

`--uygula` ile aynı kum-havuzunda: 6 dosya taşındı, `auth.json` ve `goal.yaml` **yerinde kaldı**,
`state/ içinde yedek artığı KALMADI`. Canlıda KOŞULMADI — bakım penceresi Rol-1'de.

### Onarım (c) — `auth.json`: ÖLÇÜLDÜ, yetim DEĞİL

* **YAZAN:** `auth._write()` (0600, atomik) ← `set_password` / `rotate_key` / `issue_session`;
  ayrıca `python -m meridian.auth_cli set`.
* **OKUYAN:** `auth._read()` ← `password_set` / `verify_password` / `verify_session` / `issue_session`.
  DIŞ tüketici `api.py` ve dolaylı: `_auth` bağımlılığı her korumalı uçta `auth.verify_session(cookie)`
  çağırıyor (`api.py:420`), `/api/login` → `verify_password`+`issue_session`, `/api/auth/status` →
  `password_set`. **Dosya okunmasa 51 uç 401 dönerdi.**
* **Dedektör neden göremiyor:** `codelaw.artifact_graph` yalnız `store.read_*/write_*` çağrılarını
  görür; auth kendi dosya erişimini kullanır (`_auth_file().read_text()`) — `secrets.json` ile
  **aynı sınıf** (o da `recompute.accessor_read` ile muaf tutulmuş).
* **Hüküm:** `codelaw.DECLARED_SINKS`e gerekçeli beyan (hangi modül nasıl okuyor, yazılı).
  Silme kararı gündeme gelmez: dosya canlı kimlik yüzeyidir. Temizlik betiği ona **dokunmaz**
  (desen listesi yalnız yedek sonekleri; taşınsaydı operatör panosuna giremezdi).

---

## BULGU 2 — `eleme:*.eslesme:sema_elemesi` (İKİ İHLAL, TEK KÖK)

### Ölçüm

Betik: `sema_elemesi_kok.py` (SALT OKUMA — `Sieve` kullanılmaz, `obs.warn` no-op'a bağlanır,
`component_ic()`/`build()` çağrılmaz). Çıktı: `bulgu.json`.

Yerel koşum: `in=2201 · düşen=7 · hepsi sema:bar_yok:tarih` — yerel `state/sieve.json`daki
`component_ic.eslesme` kaydıyla (in 2201 / out 2194 / ×7) **birebir**. Canlı sayı `2216/2209/7`:
aşama, neden ve adet aynı; fark yalnız cf defterinin 15 satır daha büyümüş olması.

**Yedi satırın kimliği — hepsi TEK SEMBOL:**

| katman | ticker | tarih | ham barda var mı | güvenli başlangıç |
|---|---|---|---|---|
| cf | DD | 2022-11-10 | ✓ | 2025-11-04 |
| cf | DD | 2023-02-07 | ✓ | 2025-11-04 |
| cf | DD | 2024-05-01 | ✓ | 2025-11-04 |
| cf | DD | 2024-05-01 | ✓ | 2025-11-04 |
| cf | DD | 2024-05-24 | ✓ | 2025-11-04 |
| cf | DD | 2024-05-28 | ✓ | 2025-11-04 |
| cf | DD | 2024-07-31 | ✓ | 2025-11-04 |

### KÖK

`DD`nin `bars_integrity` kaydı iki kırılma taşıyor:

* **K3 · hayalet_geçmiş** — 2017-10-17 … 2019-07-16, 115 seans, medyan dolar hacmi **0.0**;
* **K1 · ölçek dikişi** — 2025-11-03, oran **0.4249** (açılış oranı 0.966, high/low 1.047).

`guvenli_baslangic` SON kırılmanın ertesi günüdür → **2025-11-04**; `dislanan_bar: 5172`.
`adapters.data.measurement_bars` ölçüm çerçevesinden bu tarihten öncesini **bilerek** çıkarır
(gerekçesinde adı geçen HON/DD çifti). Yedi cf satırı da 2022–2024 aralığında, yani kesilen
bölgede. Barlar ham önbellekte **VAR**; çerçevede yok, çünkü çerçeve onları istemiyor.

**D7'nin sorusu — hayalet-seans ailesiyle kesişiyor mu?** Cevap ölçüldü: **evet, ama dolaylı.**
Sembol hayalet-geçmiş (K3) ailesine ait; ne var ki yedi tarihin hiçbiri hayalet penceresinin
İÇİNDE değil (o pencere 2019'da bitiyor). Kesen bıçak K1 ölçek dikişidir: `safe_start` son
kırılmanın ertesi günü olduğu için **tüm** 2004–2025 geçmişi ölçüm dışıdır. Yeni bir takvim
boşluğu YOKTUR.

**Eleme meşru mu? EVET.** Çözülmemiş bir ölçek dikişinin üstünden ileri getiri ölçmek
(`close[t+h]/close[t]-1`) ~2.35× sahte bir getiri üretirdi. Dışlama tam da bunu engelliyor.

### Onarım — "sessiz düşme"den çıkarıldı, bekçi zayıflatılmadı

`sema:` = *veri sözleşmesi hatası, yani BUG* demektir. Burada satır beklenen alanı **taşıyor**;
çerçeve barı taşımıyor ve taşımaması bir **karar**. Yani sınıflama yanlıştı ve pano her turda
olmayan bir yazılım hatası için iki kırmızı yakıyordu — sieve'in kendi yazılı gerekçesiyle
(*"dedektör kurt masalı anlatmamalı"*) birebir çelişerek.

Sınıflama **ikiye ayrıldı** (`component_ic.eslesme_nedeni`, tek tanım / iki tüketici —
`forward_returns` ile aynı gerekçe):

| durum | neden | sınıf |
|---|---|---|
| tarih `safe_start`tan önce (defter dışladı) | `piyasa:butunluk_dislamasi:guvenli_baslangic_oncesi` | BİLGİ — sayılır, ihlal değil |
| tarih çerçevede yok, defter bunu AÇIKLAMIYOR | `sema:bar_yok:tarih` (değişmedi) | BUG — ihlal üretir |

Yani gerçek arıza sınıfı (takvim boşluğu, hayalet seans, bozuk defter satırı) için dedektörün
dişi **yerinde**; susan yalnız yanlış alarm. Eşik kuralı defterden okunur, ikinci kez yazılmaz
(`measurement_bars` ile aynı `>=` sınırı) — `cic.butunluk_disladi`.

**GİZLENMEDİ, SAYILIYOR:** yeni neden eleme defterine (`state/sieve.json`) adıyla düşer;
`sieve.report()` onu `piyasa_drops`ta toplar ve pano "Eleme muhasebesi" tablosu satırı
`… → … kullanıldı · piyasa filtresi 7` diye çizer (app.js, Bölüm 5 — dosyaya dokunulmadı).

**AÇIK KALAN (paralel iş, pano):** panonun aşama satırı `piyasa:` elemelerini yalnız TOPLAM olarak
gösteriyor, neden-neden kırılımı `sv.stages[*].drops` yükünde var ama çizilmiyor. "Hangi 7 satır"
sorusu bugün ancak bu ölçüm dosyasından cevaplanıyor. `meridian/web/*` bu turda YASAK olduğu için
kalem devredildi.

**DOKUNULMAYAN:** `sema:bar_yok:sembol` (sembolün çerçevesi hiç yok) aynen `sema:` kaldı — bugün
sıfır kez tetikleniyor, yani ölçülmüş bir sorun yok. Bütünlük kırpması bir sembolü uzunluk
eşiğinin altına indirirse aynı sınıf oradan da doğabilir; ölçüldüğünde ayrı kalem olarak açılır.

---

## Dosyalar

* `sema_elemesi_kok.py` — salt-okuma ölçüm betiği (yeniden üretilebilir).
* `bulgu.json` — 7 satırın tam kimliği + her birinin düşme sebebi.
* Onarımlar: `dagit.sh`, `ops/state_yetim_temizle.sh` (yeni), `meridian/codelaw.py`,
  `meridian/component_ic.py`, `meridian/threshold_curve.py`.
* Testler: `tests/test_makulluk_temizlik_v204.py` (18 test).
