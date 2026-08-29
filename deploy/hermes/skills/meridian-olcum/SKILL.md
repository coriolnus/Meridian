---
name: meridian-olcum
description: Meridian olay/artefakt sorgularında tahmin yerine ops/olcum.py kullan
version: 1.4.0
metadata:
  hermes:
    tags: [meridian, olcum, teshis]
---

# Meridian ölçümü — tahmin etme, sor

## Ne zaman kullanılır

- Bir olay defterinde bir şey aranacağı zaman
- "Bu artefaktı kim okuyor / yazıyor" sorusunda
- Bir teşhis sırasında "şu olay hiç basılmış mı" sorusunda

## Kural

**Olay adını TAHMİN ETME.** Önce gerçek adı bul:

    /opt/meridian/.venv/bin/python /opt/meridian/ops/olcum.py olay <desen>

Çıktının SON ÜÇ satırı her koşumda — bulgu olsun ya da olmasın — şunu söyler:

    # taranan kapsam: meridian/**/*.py, ops/**/*.py (N dosya) — BU KAPSAMIN DIŞI GÖRÜLMEDİ; …
    # çözülemeyen çağrı yeri: M (ad çalışma zamanında belirleniyor)
    # ayrıştırılamayan dosya: K (açıldı ve kapsam sayısına girdi ama parse EDİLEMEDİ — …)

Bu üç satırı GÖRMEZDEN GELME. Aşağıdaki "Kapsam" ve "Doğrulama" bölümleri neden bir cevabın
ancak bu üç satırla birlikte okunabileceğini anlatıyor.

## Kapsam — araç NEREYE bakıyor (ve nereye BAKMIYOR)

Araç **`meridian/` ve `ops/`** altındaki **`*.py`** dosyalarını statik olarak okur. Bu bir TAMLIK
iddiası DEĞİL, bir SINIR beyanıdır. **Bu kapsamın dışında basılan bir olayı araç GÖRMEZ** — ve
görmediğini hiçbir sayaca da yazamaz, çünkü açılmayan dosya hiçbir kovaya düşmez.

Sınır DOSYA TÜRÜNÜ de kapsar, sadece dizini değil. Ölçülmüş örnek: `ops/keepalive.sh` canlı bir
alarmı KABUKTAN basıyor —

    .venv/bin/python -c "from meridian import obs; obs.alarm('MECHANISM_STALE', …)"

Dosya `ops/` altındadır ama `.py` değildir, dolayısıyla araç onu hiç açmaz. (Bu örnekte ad yine
bulunur, çünkü `MECHANISM_STALE` hem bir `obs.py` jetonu hem `meridian/` içinde düzinelerce çağrı
yeri — ama yalnız kabuktan basılan bir ad sahte sıfır verirdi.) Kapsam satırı bu yüzden çıplak
dizin adı değil `meridian/**/*.py` biçiminde DESEN basar: "ops/" demek "ops/ altındaki her şey"
diye okunurdu.

Bilerek dışarıda bırakılanlar (ve nedenleri): `tests/` — fikstür adları UYDURULMUŞTUR
(`x_event`, `garip`, `BİLİNMEYEN_TOKEN`), içeri alınsaydı araç sahte ad üretirdi; `mutants/` —
mutasyona uğratılmış kopya; `research/…/sandbox/meridian/` — 2026-08-12 tarihli donmuş anlık
görüntü, adları bayat olabilir; `backups/` ve `_oncesi/` kopyaları.

Kapsam satırındaki kökler **taramanın kendi yürüyüşünden** üretilir, ayrı bir yere yazılmış
metinden değil — yani orada yazan şey, aracın gerçekten açtığı dizinlerin ta kendisidir. Bunu
iki çivi tutuyor (`test_BEYAN_EDILEN_KAPSAM_GERCEKTEN_TARANANDIR`,
`test_KAPSAM_BEYANI_TARAMAYLA_BIRLIKTE_HAREKET_EDER`): biri değişip diğeri unutulursa suite
kırmızıya düşer.

## Ölçülmüş tuzaklar (dördü de gerçek, dördü de canlıda oldu)

**Tuzak 1 — tahmin (2026-08-27).** Olay adı iki kez tahmin edildi, iki kez sahte sıfır alındı:

    aranan `pozisyon_adet_benimsendi` → 0     gerçek ad: `adet_benimsendi`
    aranan `position_drift`          → 0     o bir ALAN adı, olay değil

**Tuzak 2 — aracın KENDİSİ, argüman biçimi (2026-08-29).** Aracın ilk sürümü yalnız düz dize
literalini (`obs.warn("ad", …)`) görüyordu; `obs.alarm(obs.ALARM_MIRROR_DRIFT, …)` gibi
adlandırılmış-sabit biçimini — depodaki BASKIN alarm yazım biçimi — GÖRMÜYORDU. `mirror_drift`
aransa 0, `naked_position` aransa 0 dönüyordu — ama bunlar o an ATEŞLENMEKTE olan gerçek
alarmlardı (`state/notify_undelivered.json`: MIRROR_DRIFT 51, NAKED_POSITION 9 teslim edilememiş
kayıt). `broker_reject` daha da kötüydü: araç sessizce YANLIŞ bir adla (`broker_rejects_acked`,
gerçek ama AYRI bir olay) eşleşiyordu — temiz bir ıskadan beter, çünkü YANLIŞ KANIT üretiyordu.

**Tuzak 3 — aracın KENDİSİ, ALICI takma adı (2026-08-29).** Tuzak 2'nin çaresi alıcıyı `obs` diye
HARD-CODE etmişti. Bu depoda `from . import obs as _obs` (çoğunlukla `except` blokları içinde)
YAYGIN bir kalıp — 44 çağrı yeri, düzinelerce takma ad (`_obs`, `_o`, `_o2`, `_obs_h`, `_obs0`,
`_obsL`, `_od`, `_os2`, …). Bu çağrılar hem çözülemiyordu HEM sayılmıyordu. `ALARM_ARAMA_HAVUZU_OLU`
— 2026-08-25'te TAM DA sessiz bir arızayı kapatmak için eklenmiş bir jeton — bu yüzden görünmezdi.

**Tuzak 4 — aracın KENDİSİ, KAPSAM (2026-08-29).** Tuzak 3'ten sonra bu belge, sayacın "her NE
olursa olsun çözemediğimiz her şeyi" kapsadığını söylüyordu. Ölçüm bunu yalanladı:

    olay oneri_brifingi_teslim        → OLAY YOK   (gerçekte: ops/oneri_brifingi.py)
    olay alarm_backlog_digest_teslim  → OLAY YOK   (gerçekte: ops/alarm_backlog_digest.py)

İkisi de mümkün olan EN DÜZ biçim (`obs.log("literal", …)`). Çözümleyicide hiçbir eksik yoktu —
araç `ops/` dizinini HİÇ AÇMIYORDU. Sayaç da kıpırdamıyordu: **okunmayan bir dosya hiçbir kovaya
düşmez.**

> **TARİH DÜZELTMESİ (2026-08-30).** O ölçüm günü bu iki olay CANLIYDI. Bugün DEĞİLLER: Faz 2
> kadansı `ops/sef_brifingi.py`ye devretti ve `meridian-brifing.service` iki eski betiği ARTIK
> KOŞTURMUYOR, yalnız `ozet_kur()`larını okuyor. İkisi de kaynakta DURUYOR (elle koşulursa
> ateşlenir) ama üretimde artık basılmıyor. Bugünün canlı teslimat olayı **`sef_brifingi_teslim`**
> (`ops/sef_brifingi.py`). Delik anlatısı aynen geçerli — değişen, örneğin hangisinin BUGÜN canlı
> olduğu. Bu satır burada, çünkü SKILL.md canlı ajana enjekte edilir (`skills.external_dirs`):
> bayat bir örnek, ajana bayat bir dünya öğretir.

**Kalıbın dersi (Tuzak 2, 3 ve 4 aynı kalıptır).** Her tur bir mekanizmayı düzeltti ve ardından
tamlığı YENİ SÖZCÜKLERLE yeniden iddia etti; bir sonraki deliği tehlikeli yapan şey tam da o
iddiaydı — vaade güvenen okuyucu sahte sıfırı KANIT sanar. Bu yüzden araç artık şunu yapmıyor:

> ~~"Araç bir sonuç verdiyse sonuç tamdır."~~ · ~~"Sayaç her şeyi kapsar."~~

Yerine kurulan tek değişmez: **araç tamlık iddia etmez; her cevabın yanında kendi kapsamını
beyan eder.**

## Artefakt okuyucuları

Bu araç o soruyu CEVAPLAMAZ — `codelaw` zaten cevaplıyor ve ikinci bir sarmalayıcı ikinci bir
gerçek olurdu. `codelaw.artifact_graph()` kullan.

## Doğrulama — bir cevabı nasıl okursun

**Boş liste (0 sonuç) TEK BAŞINA "olay yok" KANITI DEĞİLDİR.** Sıfır sonucun anlamı şudur ve
yalnızca şudur: *bu desene uyan bir olay, TARANAN KAPSAM İÇİNDE, statik olarak ÇÖZÜLEBİLEN çağrı
yerlerinde bulunamadı.* "Böyle bir olay yoktur" demek DEĞİLDİR. DÖRT ayrı neden vardır ve araç
hangisi olduğunu ayırt EDEMEZ:

1. Böyle bir olay gerçekten yok — aradığın bir ALAN adı olabilir (Tuzak 1).
2. Ad çalışma zamanında kuruluyor ve statik çözümleyici onu çözemedi → `# çözülemeyen çağrı yeri`
   sayısına düşer.
3. Olay kapsamın DIŞINDA basılıyor → araç oraya hiç bakmadı, **hiçbir sayaca da düşmez**
   (Tuzak 4). Bu "başka bir dizin" olabileceği gibi `ops/` altındaki bir **`.sh`** de olabilir
   (yukarıdaki `keepalive.sh` örneği).
4. Olay kapsam İÇİNDEKİ bir dosyada ama o dosya PARSE EDİLEMEDİ → `# ayrıştırılamayan dosya: K`.
   Bu, Tuzak 4'ün dosya granülerliğindeki hâlidir: dosya "taranan kapsam" SAYISINA girer (yani
   kapsam satırı onu taradım diye beyan eder) ama içindeki çağrılar hiçbir sayaca düşmez.
   **`K > 0` gördüğün bir koşumda sıfır sonuç "bulunamadı" bile DEĞİLDİR** — önce o dosyayı elle aç.

**Bu belgede bilerek SATIR NUMARASI YOK, yalnız dosya adı var.** `.md` dosyaları bu deponun çapa
tarayıcılarının hiçbirinin kapsamında değildir: buraya gömülen bir `dosya.py:123`, dosyanın her
düzenlemesinde SESSİZCE bayatlar ve hiçbir kapı ötmez. Konusu "bayat iddiaya güvenme" olan bir
belgede bayatlayabilen bir iddia bulunmaz. Sembolü ara, satırı değil.

`# çözülemeyen çağrı yeri: M` bir ÇIKARMADIR: (açılan dosyalarda metod adı log/warn/error/alarm
olan TÜM çağrı yerleri, ALICI FARK ETMEKSİZİN) − (gerçekten çözülenler). Bu, **kapsam içinde**
öngörülmemiş bir biçimin de sayılmasını sağlar — aracı elle güncellemeden. İki sınırı vardır ve
ikisi de bilinerek bırakılmıştır: (a) kapsam DIŞINI kapsamaz — dosya açılmadıysa çıkarma onu
göremez; (b) `obs`a hiç bağlı olmayan `np.log(...)` / `ap.error(...)` gibi çağrılar da bu sayıya
karışır (belirsizliği FAZLA beyan etmek dürüsttür; AZ beyan etmek dört tuzağın da kök nedeniydi).
Yani `M`, "kaç gerçek olay eksik" sorusunun cevabı DEĞİL, "kaç çağrı yeri BELİRSİZ" sorusununkidir.

**Okuma kuralı.** Aradığını bulamadıysan, önce o üç satıra bak:

- `M > 0` ise → aradığın şey o M çağrının içinde SAKLI olabilir. Deseni daraltmak YETMEZ; ilgili
  kaynak dosyada `obs`a (veya bir takma adına) giden çağrıyı ELLE bulup ilk argümanının nereden
  geldiğine bak.
- Kapsam satırındaki kökler aradığın kodu içermiyorsa → araç o dosyaya HİÇ BAKMADI. Cevap
  "olay yok" değil, "bakılmadı"dır; o dosyayı elle aç.
- `K > 0` ise → kapsam içindeki bir dosya AÇILDI ama okunamadı. Hangisi olduğunu araç söylemez;
  `python -m compileall -q meridian ops` onu adıyla verir.

Sıfır dönen bir arama gördüğünde **"araç arıza olmadığını söyledi" SONUCUNU ÇIKARMA** — araç bunu
hiçbir zaman iddia etmiyor.
