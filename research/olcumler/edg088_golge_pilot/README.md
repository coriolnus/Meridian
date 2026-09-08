# EDG-2026-088 — uyuyan kurulum gölge icra sayacı

Kart: `research/cards/EDG-2026-088-uyuyan-kurulum-golge-pilot.yaml` · Plan:
`docs/superpowers/plans/2026-09-08-golge-pilot-b1.md` (Task 3) · Çiviler:
`tests/test_edg088_sayim_v461.py` (sayaç) ve `tests/test_golge_icra_v456.py` +
`tests/test_golge_icra_kadans_v457.py` (motor ve kadans).

Bu betik **sayar, hüküm vermez**. Eşikler karttan ve motorun donuk sabitlerinden okunur, rapora
yalnız SAYI olarak yazılır; hükmü Rol-1 aynı turda karta + K defterine işler (CLAUDE.md §5).
Pencere dolmadan markdown "HÜKÜM YOK (betimleyici ara-rapor)" başlığı taşır ve **eşik
karşılaştırması bölümü hiç üretilmez** — n<30 ile yazılmış bir eşik cümlesi selef EDG-2026-049'un
ikinci düşme sebebiydi.

## Komut satırı

```
.venv/bin/python research/olcumler/edg088_golge_pilot/sayim.py \
    --defter state/golge_icra.jsonl \
    --cikti research/olcumler/edg088_golge_pilot/sonuc_<tarih>.json \
    --markdown research/olcumler/edg088_golge_pilot/sonuc_<tarih>.md \
    --baslangic <B1 dağıtım anı, ISO> \
    --pk3 research/olcumler/edg049_dormant_2026-08-23/islemler_tam_dormant_acik.json
```

| Bayrak | Zorunlu | Ne |
|---|---|---|
| `--defter` | ✔ | `state/golge_icra.jsonl` yolu. **Salt okunur** — betik bu dosyaya yazmaz. |
| `--cikti` | ✔ | JSON sonucun yazılacağı yol (dizin yoksa açılır). |
| `--markdown` | ✘ | İnsan raporu. Verilmezse üretilmez. |
| `--baslangic` | ✘ | ISO damga; bu andan ÖNCEKİ satırlar pencere dışıdır (`girdi.n_pencere_disi`). **`Z` de `+00:00` da olur** — damga ayrıştırılıp UTC'ye normalize edilir, dizge olarak kıyaslanmaz; ayrıştırılamayan damgada betik **durur** (sessizce boş rapor üretmez). Pencere B1 dağıtımından başlar (kartın `veri_penceresi`). |
| `--kart` | ✘ | Eşiklerin okunduğu kart; varsayılan EDG-2026-088 kartı. |
| `--gercek` | ✘ | PK (2)'nin gerçek ayağı (`state/trades.jsonl`). Verilmezse **defterin yanındaki** dosya aranır; yoksa PK (2) `gecti=None` + neden olur. |
| `--goal` | ✘ | Komisyon+kayma payının okunduğu `state/goal.yaml` (izli SSoT). |
| `--pk3` | ✘ | EDG-2026-049 kesiti (`islemler_tam_dormant_acik.json`). Verilmezse PK (3) ölçülmez. |

Betik `state/`e ve `meridian.obs`a **yazmaz**, ağa **çıkmaz**. Defteri `store` üzerinden değil
verilen dosya yolundan okur — yani `config.STATE`e hiç dokunmaz. `meridian.golge_icra`dan yalnız
donuk sabitler ve alan adları alınır; motorun `adim`/`ozet`/`kayit_al` fonksiyonları **çağrılmaz**
(hepsi `config.STATE`e bağlıdır). İthal zinciri ölçüldü: `golge_icra` → `barclock` · `broker` ·
`store` · `strategy`; `meridian.obs`, `meridian.loop` ve `adapters.alpaca` bu zincirde **yoktur**
ve ithal hiçbir dosya açmaz (çivi: `test_ithal_meridian_obs_u_TETIKLEMEZ_ve_state_ACMAZ`).

Terminale basılan özet satırı `pencere_disi`, `pk2`, `pk3` ve `yayin_engeli` sayılarını da taşır:
operatör damga biçimi yüzünden pencereyi kaybettiyse ya da kill#5 ateşlediyse bunu raporun içinde
değil, komutu koştuğu anda görür.

## Eşikler iki kaynaktan okunur, hiçbiri kopyalanmaz

Kartın `esikler` bloğu ve `meridian.golge_icra`nın donuk sabitleri **aynı sayıları** taşır (motorun
kendi çivisi ikisini zaten karşılaştırır). Sayaç ikisini de okur ve **ayrışmayı ölçer**:

| Kart alanı | Motor sabiti | Ne |
|---|---|---|
| `n_alt_plan` | `N_ALT` | K paydasının alt sınırı (KAPANAN gölge işlem) |
| `ci_alt_R_ust` | `CI_ALT_R` | CI95 alt sınırının aşması gereken değer |
| `kazanma_alt` | `KAZANMA_ALT` | kazanma oranı alt sınırı |
| `pencere_gun_ust` | `PENCERE_GUN` | pencerenin üst sınırı (gün) |
| `golge_gercek_fark_R_ust` | `FARK_R_UST` | PK (2)'nin fark tavanı |

Ayrışma çıkarsa (ya da kartın `ci_yontem` alanı kullanılan fonksiyonun adını taşımıyorsa)
`esik_ayrismasi` dolar ve **K bloğunun tamamı bastırılır**: eşiği ne olduğu belirsiz bir ölçümün
sayısını yayınlamak, ölçümü hak etmeden geçirmenin en sessiz yoludur. Eşik sayıları sayacın
gövdesinde literal olarak **geçmez** (çivi: `test_sayacta_esik_SAYISI_literal_olarak_YAZILI_DEGIL`).

## K paydası

| Satır | Paydada mı | Nerede görünür |
|---|---|---|
| Kapandı, `R` ölçüldü, `kaynak_bar_hash` dolu | **Evet** | `n`, `toplam_r`, `ci`, `kazanma_orani`, `pf`, kırılımlar |
| `cikis_neden = giris_yok`, `R = None` | Hayır | `olculemeyen` (nedeni `giris_reddi` ile ADIYLA) |
| `kaynak_bar_hash` `None` ya da boş dizge | Hayır | `olculemeyen` (`olculemedi` alanı, örn. `bar_eksik:2`) |

Eksik K, eşiği **hak etmeden geçme** yönünde yanlıdır; o yüzden ölçülemeyen satır sessizce
düşmez, adıyla durur. Bu kural motorun `golge_icra.ozet` fonksiyonunda da yazılıdır — kaçınılmaz
kopya bir **ayrışma çivisiyle** bağlıdır (aynı defter iki tarafa verilir, n · toplam_r ·
kazanma_orani · pf · dağılımlar birebir aynı çıkmalıdır).

## JSON alan sözlüğü

| Alan | Ne |
|---|---|
| `kart` | `golge_icra.KART` (`EDG-2026-088`) |
| `girdi` | `defter`/`gercek`/`goal`/`pk3`/`kart_yolu`/`baslangic` + `n_ham_satir`, `n_pencere_disi`, `n_bozuk_satir`, `n_bozuk_ts` |
| `esikler` | Kartın `esikler` bloğu, **olduğu gibi** (kopya değil, okuma) |
| `modul_sabitleri` | `golge_icra`nın donuk sabitleri, adlarıyla |
| `esik_ayrismasi` | Kart ↔ motor ayrışmalarının listesi. Boş değilse yayın engellenir |
| `n` | K paydası (yukarıdaki tablo) |
| `toplam_r`, `ort_r` | Toplam ve ortalama R. `n=0` ise **`None`**, 0 değil |
| `kazanma_orani`, `pf` | `R>0` payı; PF = kazançlar / \|kayıplar\| (kaybeden yoksa `None`) |
| `ci` | `olcum_araclari.blok_bootstrap_ci` çıktısı, **olduğu gibi**: `lo`/`hi`/`ort`/`blok`/`blok_kaynagi`/`B`/`tohum`/`iid`/`yontem`/`beyan`/`uyari`. **ORTALAMA R'nin** aralığıdır |
| `ci_kabul` | `iid is False` mı. `blok=1` (IID) **reddedilir**: zaman-sıralı seride aralığı sistematik olarak daraltır ve kartın donuk yöntemi moving block'tur |
| `ci_toplam` | `ci` × `n` — **TÜRETME**, ölçüm değil (`turetme` alanı bunu söyler). İşaret sınaması (alt sınır > 0) iki blokta aynıdır |
| `pencere` | `ilk_ts`/`son_ts`/`gun`/`gecen_gun`/`yayilma_gun`/`doldu`/`suresi_doldu`. `doldu = n ≥ N_ALT ∧ gecen_gun ≤ PENCERE_GUN`; damga hiç ölçülemezse `None` (False değil) |
| `kurulum_kirilimi` | Kurulum başına sayım — **TANI**, K'ye çarpılmaz (kart: hüküm toplamda) |
| `hukum_dagilimi` | Plandaki kapı hükmü (`GO`/`REVIEW`/`NO_GO`) dağılımı — tanı; gölgeye hepsi girer |
| `cikis_neden_dagilimi` | `stop`/`target`/`time_stop`/`regime_flip`/… dağılımı — tanı |
| `kol_kirilimi` | `dormant` / `kontrol` — PK (2)'nin paydası |
| `bar_kaynak_dagilimi` | `state/bars` (canlı yol) / `arsiv` (tarihsel yeniden yürütme) |
| `kontrol` | PK (2): `n_cift`, `n_golge_kontrol`, `n_gercek`, `ort_fark_r`, `ort_mutlak_fark_r`, `komisyon_kayma_payi`, `esik`, `gecti`, `ciftler`, `neden` |
| `pk3` | PK (3): 049 referansı (`n`, `kayip`, `toplam_r`, `plan_idler`) + `golge` tarafı + `esles` + `fark_r` + `neden` |
| `bedel` | `satir_gun`, `bayt`, `n_ham_satir` (bedel yasası) |
| `yayin_engeli` | Sayıların bastırılma sebepleri (kill#5 · eşik ayrışması). Boşsa yayın serbest |
| `bastirilan` | Bastırılan alan adları |
| `olculemeyen` | Ölçülemeyen her şeyin adı ve nedeni (uydurma yasağı) |
| `beyan` | Betiğin ne yaptığı / ne yapmadığı — rapora da basılır |

## Üç pozitif kontrol

**PK (1) — sentetik kimlik.** Motorun beş sentetik yolu (`stop` · `target` · `time_stop` ·
`regime_flip` · tetik hiç gelmedi) motorun kendi çivisinde koşar, ürettiği defter sayaca verilir ve
toplam R **el hesabıyla** çıkar: giriş 101 / stop 95 → R paydası 6,0; −1 + 1,5 − 0,5/6 + 1/6 =
0,5 + 0,5/6. Tetiği gelmeyen plan `R=None`dır ve **paydada değildir** (n=4, 5 değil). Senaryo
kopyalanmaz, motorun çivisinden **ithal edilir** (tek-kaynak).

**PK (2) — kontrol kolu (gölge ≈ gerçek).** `kol="kontrol"` gölge satırları `plan_id` ile
`trades.jsonl`deki gerçek işlemlere eşlenir. `gecti` üç değerlidir:

* `True` — ortalama \|gölge R − gerçek R\| hem kartın `golge_gercek_fark_R_ust` eşiğinin hem
  komisyon+kayma payının **içinde** (kart iki şartı da ister).
* `False` — ölçüldü, tutmadı → **kill#5**: `n`, `toplam_r`, `ci`, `kazanma_orani`, `pf` ve tüm
  kırılımlar hem JSON'da hem markdown'da **bastırılır**; markdown "PK DÜŞTÜ — SAYI YAYILMAZ"
  başlığıyla çıkar ve yalnız engelin kendi ölçümünü basar.
* `None` — **ölçülemedi** (gerçek defter yok, kontrol kolu boş ya da hiç çift eşleşmedi).
  Bastırmaz: ölçülmemiş bir PK'yı düşmüş saymak hükmü hak etmeden engellerdi. Neden `olculemeyen`e
  adıyla düşer.

Komisyon+kayma payı `state/goal.yaml`dan **ölçülür**, sabit yazılmaz:
`(2 × slippage_bps/10⁴ × giriş + 2 × commission_per_share) / (giriş − stop)`. `slippage_bps` goal'de
tek yön olarak yazılıdır, o yüzden iki bacak sayılır.

**PK (3) — selef EDG-2026-049.** Artefaktın `setup == "pullback"` dilimi **tam 6 satırdır**
(049'un n=6'sı); referans işaret 6/6 kayıp ve toplam **−4,725R**. Sayaç bu referansı her zaman
ölçer. Gölge tarafı ancak gölge defterinde o 6 `plan_id` varsa ölçülebilir:

| Durum | `esles` | Ne demek |
|---|---|---|
| 6 plan gölgede yok | `None` + "HARNESS KÖR" | Yeniden doğum (Rol-1 hükmü 3, seçenek c) **koşulmadı** |
| 6'nın bir kısmı var | `None` + "KISMİ" | Eksik dilim üzerinden eşleşme ölçülmez; eksik kimlikler adıyla |
| 6/6 kayıp, toplam R < 0 | `True` | 049 ile aynı **işaret** (eşitlik değil; sayısal fark `fark_r`) |
| İşaret ayrıştı | `False` | Gölge motoru 049 karşı-olgusuyla ayrışıyor — kartın "harness kör" hükmü |
| Dilim 6 değil | `None` + "ÖLÇÜLEMEDİ" | Artefakt değişmiş; başka bir dilimi ölçmek 049 ile kıyas olmazdı |

**PK (3)'ün gölge ayağı bugün ÖLÇÜLEMEZ ve sebebi ölçüldü** (2026-09-08): Rol-1 hükmü 3, 6 planın
`strategy.scan_all` ile yeniden doğurulmasını ister; `strategy.evaluate_pullback`in giriş kapısı
`rs_rating_value` okur (`entry.rs_rating_min`, varsayılan 70) ve o değer **kesitseldir** —
`indicators.rs_rating` evrenin TAMAMI üzerinden hesaplanır. 049 artefaktının satırlarında rs
yoktur, gölge motoru rs üretmez ve `r_multiple`den stop TÜRETİLMESİ Rol-1 hükmü 3 tarafından açıkça
reddedilmiştir. Yani yeniden doğum tam replay şasisini (evren barları + rejim çözümü + donmuş
edg032c künyesi) gerektirir; bir sayaç ya da çivi ölçeğinde yapılamaz. Sayaç bunu uydurmaz:
`esles=None` + "HARNESS KÖR" der.

## Markdown raporunun üç hâli

| Koşul | Başlık | Sayı basılır mı |
|---|---|---|
| `yayin_engeli` dolu (kill#5 ya da eşik ayrışması) | `## PK DÜŞTÜ — SAYI YAYILMAZ` | **Hayır** — yalnız engelin kendi ölçümü |
| `pencere.doldu` `True` değil | `## HÜKÜM YOK (betimleyici ara-rapor)` | Betimleyici sayılar evet, **eşik karşılaştırması hayır** |
| `pencere.doldu` `True` | `## Pencere DOLDU — sayılar aşağıda (hüküm Rol-1'in)` | Evet + eşik tablosu (yalnız sayı) |

Hiçbir hâlde "geçti/kaldı/GEÇER/KALIR" sözcüğü basılmaz (çivi). `hukum_dagilimi`nin `GO`/`REVIEW`/
`NO_GO` anahtarları **planın kapı hükmüdür**, ölçümün hükmü değildir.

## Bilinen sınırlar (beyan)

* **Kısmi satış gölgeye girmiyor.** Motorun beyanlı sapması (Task 1 raporu §6): canlı çıkış yolu
  `manage_position` + `_touch_exit` + `scale_out` üçlüsüdür; ilk ikisi çağrılır, `scale_out`
  `PaperBroker` kitabına bağlı olduğu için çağrılmaz. Bugünkü etkisi sıfırdır
  (`exit.scale_out_frac` varsayılanı 0), düğme açılırsa PK (2) bunu **düşerek** gösterir.
* **CI ortalamanın aralığıdır**, toplam ondan türetilir (`ci_toplam.turetme`).
* **Kanca P2 kapısının içindedir** (Task 2 raporu §7): HALT / bozuk veri / bütçe 0 / kitap dolu
  turlarında gölge adımı hiç koşmaz; çıkış bir sonraki koşulan seansın fiyatına kayar ve
  `bars_held` eksik sayılır. Taraflılık motorun çivisinde kayıtlıdır.
* **Sayaç defteri geriye dönük tamamlayamaz.** Plan doğduğu seansta yakalanmalıdır (Rol-1 hükmü 5);
  `trade_plans.jsonl` `cap=500` ile kırpıldığı için geriye dönük okuma n'i sessizce küçültürdü.
