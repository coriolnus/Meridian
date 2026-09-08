# EDG-2026-086 — pano sohbeti kalite sayacı

Kart: `research/cards/EDG-2026-086-pano-sohbet-kalite.yaml` · Plan:
`docs/superpowers/plans/2026-09-08-pano-sohbet-b3.md` · Çiviler: `tests/test_edg086_sayim_v450.py`
(sayaç) ve `tests/test_sohbet_cikti_atif_v449.py` (defterin atıf alanı).

Bu betik **sayar, hüküm vermez**. Eşikler karttan okunur ve rapora yalnız SAYI olarak yazılır;
hükmü Rol-1 aynı turda karta + K defterine işler (CLAUDE.md §5). Pencere dolmadan markdown
"HÜKÜM YOK (betimleyici ara-rapor)" başlığı taşır.

## Komut satırı

```
.venv/bin/python research/olcumler/edg086_pano_sohbet/sayim.py \
    --defter state/sohbet.jsonl \
    --cikti research/olcumler/edg086_pano_sohbet/sonuc_<tarih>.json \
    --markdown research/olcumler/edg086_pano_sohbet/sonuc_<tarih>.md \
    --baslangic 2026-09-08T00:00Z
```

| Bayrak | Zorunlu | Ne |
|---|---|---|
| `--defter` | ✔ | `state/sohbet.jsonl` yolu. **Salt okunur** — betik bu dosyaya yazmaz. |
| `--cikti` | ✔ | JSON sonucun yazılacağı yol (dizin yoksa açılır). |
| `--markdown` | ✘ | İnsan raporu. Verilmezse üretilmez. |
| `--onaylar` | ✘ | `approvals.jsonl`. Verilmezse **defterin yanındaki** dosya aranır; yoksa öneri ölçüsü `None` + `neden` olur. |
| `--kart` | ✘ | Eşiklerin okunduğu kart; varsayılan EDG-2026-086 kartı. |
| `--baslangic` | ✘ | ISO damga; bu andan ÖNCEKİ satırlar pencere dışıdır (`girdi.n_pencere_disi`). **`Z` de `+00:00` da olur** — damga ayrıştırılıp UTC'ye normalize edilir, dizge olarak kıyaslanmaz; ayrıştırılamayan damgada betik **durur** (sessizce boş rapor üretmez). |

Betik `state/`e ve `meridian.obs`a **yazmaz**, ağa **çıkmaz**. `meridian.sohbet`ten yalnız saf
çıkarıcılar (`cikti_atiflari`, `belirsiz_semboller`), donuk sabitler ve sistem-şablonu
**imzalarını** üreten kota cümlesi alınır; defteri `store` üzerinden değil, verilen dosya
yolundan okur — yani `config.STATE`e hiç dokunmaz.

Terminale basılan özet satırı `n_pencere_disi`yi de taşır: operatör damga biçimi yüzünden
pencereyi kaybettiyse bunu raporun içinde değil, komutu koştuğu anda görür.

## Ölçümün paydası

Kartın kill-list'i nettir: *"uydurma sayımı araç çıktısını değil **cevabı tek başına** okursa ölçüm
geçersiz"*. Payda iki kaynaktan birleşir ve hiçbiri cevabın kendisi değildir:

1. **Araç çıktısı.** Defter araç çıktısının **metnini** saklamaz (8 KB × 6 tur × 100+ mesaj ve sır
   yüzeyi); onun yerine `meridian/sohbet.py` her **veri okumuş** araç çağrısından sonra o turun
   `cikti_atiflari` alanına dört sınıflık literal atıf kümesini yazar. Sayaç cevabı **aynı**
   çıkarıcıyla ayırır ve turların birleşik kümesinde arar.
2. **Operatörün kendi mesajı.** "T00842 planı ne durumda?" sorusuna gelen cevapta T00842'nin
   tekrarlanması modelin ürettiği bir değer değil, kullanıcının girdisinin yankısıdır. Uydurma
   sayılsaydı oran hak etmeden **yükselir** ve donuk 0,05 eşiği sahte bir hüküm üretirdi.
   Yankının büyüklüğü `uydurma.mesaj_kaynakli` ile ayrıca raporlanır.

### Satırlar üç kovaya ayrılır

| Kova | Ne | Ölçülür mü |
|---|---|---|
| `sistem_metni_n` | Cevabı **döngü** yazdı: kota kapısı, zincir düşmesi (`llm_dustu`), tur tavanı, `mesgul`. | **Hayır.** O cümlelerdeki hiçbir dizge modelin iddiası değil; ölçülseydi "kota dolu (120/120)" iki uydurma üretirdi. |
| `bos_payda_n` | **Model** konuştu ama hiçbir araç veri okumadı. | **Evet, boş paydayla.** Kartın hipotez (a) maddesinin kanonik arıza vakası: cevaptaki her atıf dayanaksızdır. |
| (normal) | En az bir başarılı araç çağrısı var. | Evet. |

Sınıf tavanı (200) aşılan **sınıflar** o satırda ölçülmez, **satır** ölçülür: `sayi` taşan bir veri
cevabında `kimlik`/`yol`/`sembol` paydaları tamdır. Satırın tamamını elemek, en çok sayı taşıyan —
yani uydurma riski en yüksek — cevapları seçerek elerdi. Kaç satırda hangi sınıfın kesildiği
`uydurma.atif_kesilen_sinif` ile durur.

## JSON alan sözlüğü

| Alan | Ne |
|---|---|
| `girdi` | `defter`/`onaylar`/`kart_yolu`/`baslangic` + `n_ham_satir`, `n_pencere_disi`, `n_bozuk_satir`, `n_bozuk_ts` |
| `esikler` | Kartın `esikler` bloğu, **olduğu gibi** (kopya değil, okuma) |
| `n_mesaj`, `n_seans` | Pencere içindeki satır sayısı ve ayrık `oturum` sayısı |
| `pencere_doldu` | `n_mesaj ≥ esikler.n_alt_mesaj` **∧** `n_seans ≥ seans_alt` **∧** `uydurma.n_satir ≥ esikler.n_alt_mesaj`. Kartta eşik anahtarı yoksa `None` + `pencere_neden` (eksik eşik 0 sayılsaydı kapı sessizce **açılırdı**) |
| `seans_alt` | Seans alt sınırı (10). Kartın `esikler` bloğunda makine okunur alanı yok; sayı `veri_penceresi` metnine **çiviyle bağlı** |
| `uydurma.n_satir` | Gerçekten ölçülen satır sayısı (sistem metni hariç; boş paydalı satırlar **dahil**) |
| `uydurma.payda` | Ölçülen satırların cevaplarından çıkarılan atıf sayısı (dört sınıf toplamı, kesilen sınıflar hariç) |
| `uydurma.uydurma` | Bunlardan ne araç çıktısı kümesinde ne operatör mesajında **geçmeyenler** |
| `uydurma.mesaj_kaynakli` / `mesaj_kaynakli_kirilimi` | Araç çıktısında olmayıp **operatörün mesajında** geçen ve cevapta tekrarlanan atıflar (tanı: "oranın ne kadarı soru yankısı") |
| `uydurma.belirsiz` | `%12` · `yüzde 12` · `YÜZDE 12` · `12 %` (üç boşluğa kadar) · `1,103` · `1.000.000` · `MU`/`CI`/`T` gibi kısa sembol adayları · **çapasız** üç harfli adaylar (`DAL`, `HAL`, `TER`) — ölçülemeyen biçimler; uydurma **sayılmaz**, ayrı sayılır |
| `uydurma.belirsiz_pay` | `belirsiz / (payda + belirsiz)`. **Bedel yasası:** "uydurma oranı 0,0000" satırı, sayı sınıfına neredeyse hiç bakılamamış bir ölçümü temsil edebilir; körlüğün büyüklüğü bu payla görünür |
| `uydurma.oran` | `uydurma / payda`; payda 0 ise `None` + `oran_neden` |
| `uydurma.sinif_kirilimi` | Sınıf başına `{payda, uydurma, neden}` (`sayi`, `kimlik`, `yol`, `sembol`). Sıfır payda "temiz" demek değildir — `neden` bunu söyler |
| `uydurma.sistem_metni_n` / `bos_payda_n` / `atif_kesilen_sinif` | Kova sayıları (yukarıdaki tablo) |
| `uydurma.atif_beyani_bozuk_n` | `cikti_atif_kesildi` beklenmedik tipte olan tur sayısı. **Fail-closed:** o satırların dört sınıfı da eksik paydalı sayılır ve `olculemeyen`e adıyla girer — "payda tam" varsaymak sahte uydurma üretirdi |
| `uydurma.ornekler` | En çok 20 uydurma atıf (`ts`, `oturum`, `sinif`, `atif`) — kartın **elle PK**'sinin girdisi |
| `arac.tur_n` | Pencere içindeki model turu sayısı (tanı) |
| `arac.toplam_tool_calls` | Turların `tool_calls` toplamı — yapısal çağrı sayısı |
| `arac.sema_disi_n` | Şema-dışı araç çağrısı sayısı (turların `sema_disi` toplamı) |
| `arac.metin_arac_n` | Cevapta `ad(` biçiminde beyaz-liste araç adı geçen **ve** cevabı üreten turda yapısal çağrı olmayan satırlar (EDG-2026-074 sınıfı) |
| `arac.oran` | `(sema_disi_n + metin_arac_n) / (toplam_tool_calls + metin_arac_n)`. **Payda ÇAĞRIdır** — kart hipotezi (b) "araç *çağrılarının* ≥%90'ı şemaya uyar" der ve `arac_sema_disi_ust` o birimdedir. Metin-araç turu çağrı üretmediği için paydaya kendisi eklenir; oran tanım gereği ≤1 |
| `arac.tur_paydali_oran` | Aynı payın TUR paydalı hâli — **yalnız tanı.** Aynı sentetik defterde iki payda 0,10 eşiğinin iki yanına düşebilir; hangisinin okunduğu belli olsun diye ikisi de yazılır |
| `gecikme.p50_s`, `p95_s` | `statistics.quantiles(..., n=100, method="inclusive")`; 2'den az ölçümde `None` + `neden` |
| `gecikme.tur_kirilimi` | Tur sayısı → `{n, p50_s}` (tanı) |
| `gecikme.sure_yok_n` | `sure_s` alanı `None` olan satırlar |
| `kota.gun_basi_max` / `gun_basi_ort` | Gün başına `kota_bugun` tepesinin en büyüğü / ortalaması |
| `kota.dolu_pencere_n` / `dolu_pencere_pay` | `kota_bugun ≥ kart tavanı` olan satır sayısı / payı. Kartta `kota_gunluk_tavan` yoksa `None` + `dolu_pencere_neden` |
| `kota.llm_dustu_n` | Zincirin hiçbir ayağının cevap vermediği satırlar |
| `kota.olculemeyen_n` | `kota_bugun` `None` olan satırlar (telemetri halkası bugünün içinde dolmuş) |
| `oneri` | `approvals.jsonl`de `kaynak=sohbet` satırları: `n`/`onaylanan`/`reddedilen`/`bekleyen` (tanı). Defter yoksa hepsi `None` + `neden` |
| `model_kirilimi` | Künye → `{n, uydurma_oran, uydurma_payda, sema_disi_oran, tur_n}` |
| `olculemeyen` | Ölçülemeyen her şeyin adı ve nedeni (uydurma yasağı) |
| `beyan` | Betiğin ne yaptığı / ne yapmadığı — rapora da basılır |

## Sembol sınıfının sınırları (ölçüm penceresi açılmadan daraltıldı)

Sohbetin cevap dili **Türkçe**, araç çıktısı ASCII/JSON. İki ölçülmüş arıza sınıfı vardı ve ikisi de
`sembol` sınıfında sahte uydurma üretiyordu:

* **ASCII sınırı** Türkçe büyük harfleri (Ç Ğ İ Ö Ş Ü) sınır sayıyordu: `HALİ` → `HAL`, `TERİM` →
  `TER`, `GEÇTİ` → `GE`. İlk ikisi **gerçek evren sembolü**. Sınır artık Unicode harf sınırıdır.
* **Kısa kesişimler**: evrende `T`, `V`, `D`, `O`, `MA`, `SO`, `MU`, `CI`, `DE`, `ON` gibi tek/iki
  harfli semboller var ve bunlar Türkçe metnin gündelik parçaları ("K defterine", "SO-…" öneki,
  "MU planı"). Sembol sayılsalardı sistematik yanlış-pozitif, sessizce atılsalardı **körlük**
  olurdu — `belirsiz` kovasına giderler (`meridian.sohbet.belirsiz_semboller`).
* **Üç harfli kesişimler** (ölçüldü 2026-09-08: evrenin 248 sembolünün **142'si** üç harfli):
  `DAL` bu deponun kendi sözlüğünde günlük bir kelimedir ("dal ucu", "dal kapanışı"); `HAL` ve
  `TER` de öyle. Asgari uzunluk kuralı bu sınıfı **küçülttü, kapatmadı**. Aday artık ancak aynı
  satırda bir **bağlam çapası** varsa sembol sayılır: `$` öneki · fiyat biçimi (`12.5`, `47,20`) ·
  "sembol" kelimesi · satırın kendi `kaynaklar` künyesi. Çapasız aday `belirsiz`e gider.

  **Çapa kapısı yalnız CEVAP tarafında koşar, paydada koşmaz** ve bu asimetri bileredir: araç
  çıktısı `indent=1` ile basılan JSON'dur, sembol kendi satırında fiyatından ayrı durur
  (`"ticker": "HAL",`). Kapı paydada da koşsaydı sembol paydadan düşer, cevaptaki çapalı yazımı
  dayanaksız görünür ve **sahte bir uydurma** doğardı. Payda geniş (yanlış pozitif üretmez), pay
  dar. Kalıntı beyanı: "HAL hissesi" gibi başka bağlam sözcükleri çapa **sayılmaz**; körlüğün
  büyüklüğü `belirsiz` kovasında durur.

Kartın eşiği, penceresi ve kill-list'i **değişmedi**; daraltma yalnız `olcum_plani`nın sınıf
tanımına dokunur ve ölçüm penceresi açılmadan yapıldı.

## Pozitif kontrol

Kartın `pozitif_kontrol` maddesinin **(1) SENTETİK** ayağı `tests/test_edg086_sayim_v450.py`
içindedir: 20 satırlık sahte defterde bilinen **3 uydurma · 2 metin-araç · 1 kota** vardır ve
sayaç tam olarak onları bulur; 4. bir uydurma eklendiğinde 4 bulur (çivinin kendi mutasyonu).
Üç uydurma **üç ayrı sınıftan** gelir (sayı · kimlik · **sembol**) ve sembol olanı aynı zamanda
"model konuştu ama hiç veri okumadı" satırıdır. Defter ayrıca bir **şema-dışı** tur (2 çağrı) ve
bir **zincir-düşmesi** satırı taşır; ikisi de 3/2/1 sayımını bozmaz ama K2 sayaçlarının mutasyonunu
ısırır. **(3) GERÇEK** ayak (10 canlı cevabın elle okunması) Rol-1'indir ve `uydurma.ornekler`
onun girdisidir.
