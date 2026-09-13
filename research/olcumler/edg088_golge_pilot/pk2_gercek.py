"""pk2_gercek.py — EDG-2026-088 POZİTİF KONTROL (2) "GERÇEK": canlı NORMAL yolun SON 10 GERÇEK
işlemini gölge motorundan geçirir ve gölge R ile gerçek R'yi kıyaslar.

SORU. Kart `EDG-2026-088` `pozitif_kontrol` (2): "GERÇEK — canlı NORMAL yolun son 10 gerçek işlemi
gölge motorundan geçirilir; gölge R − gerçek R farkı komisyon+kayma payı içinde
(`esikler.golge_gercek_fark_R_ust`)". Plan §Rol-1 hükümleri 7 aynı ayağı daraltır: "yalnız GERÇEK
işlemler: son 10 gerçek işlem BİR KEZ yeniden yürütülür". Bu betik o kontrolün ŞASİ KOŞUMUDUR;
PK (3)'ün (`pk3_selef.py`) kardeşidir ve onun şasisini İTHAL EDER, kopyalamaz.

ÜÇ PARÇA, ÜÇÜ DE İTHAL (tek-kaynak yasası — bu dosyada yeniden yazılan hiçbir eşik/yasa yoktur):
  1. GİRDİ — Rol-1'in A1'den SALT-OKUR çektiği DONMUŞ artefakt (`pk2_gercek/girdi/…json` +
     `SHA256SUMS`). İçinde `trades` (canlı kâğıt defterin son 12 satırı), `plans` (o işlemlerin
     plan satırları) ve `e2` (`entry_execution` satırları) durur. Planın icra girdileri
     (`entry_trigger` / `stop` / `profit_target` / `setup`) PLAN TABLOSUNDAN alınır — işlemin
     gerçekleşmiş `entry`/`exit`inden TÜRETİLMEZ (türetilen bir tetik, ölçüleni uydurulana
     çevirirdi; UYDURMA YASAĞI ve `pk3_selef`in aynı hükmü).
  2. GÖLGE — `pk3_selef.golgeden_gecir` → `golge_icra.adim`, seans seans, D'den kapanışa. Giriş ve
     çıkış yasaları motorun kendisinindir (`broker.entry_limit_price`,
     `broker.PaperBroker._touch_exit`, `strategy.manage_position`); takvim/bar/rejim beslemesi ve
     GEÇİCİ state yönlendirmesi (`pk3_selef._state_kur`) PK (3) ile BİREBİR AYNI yoldur.
  3. HÜKÜM SAYISI — `sayim.kontrol_olc`. Eşik (`golge_icra.FARK_R_UST`), komisyon+kayma payının
     tanımı (`sayim._friksiyon_payi`, ÜRETİMİN `PaperBroker` sürtünmesinden) ve `gecti`nin ÜÇ
     DEĞERLİ mantığı ORADA yaşar; bu betik onları ÇAĞIRIR. İkinci bir eşik yorumu ilk düzeltmede
     çatallanırdı — kart PK (2)'yi zaten "üç değerli, pay goal.yaml'dan" diye dondurdu
     (kart notu 2026-09-08).

ÇIPLAK AYNA SINIFI (kart kill#3: sessiz düşürme YOK). Gerçek işlemlerin bir kısmında broker
dolumunun kanıtı (`extra_json.alpaca_fill_price` ve/veya `dolum_ts`) YOKTUR. Bunlar PK (2)'den
DÜŞÜRÜLMEZ: `dolum_sinifi` ile ADIYLA sınıflanır ve ortalama İKİ paydadan verilir — `kontrol`
(HEPSİ, hükmün kümesi) ve `kontrol_dogrulanmis` (yalnız `dogrulanmis` sınıfı, TANI). Sınıf bir
sembol listesi DEĞİL bir ALAN ÖLÇÜMÜDÜR: liste, girdi değiştiği gün sessizce bayatlardı.

BEYANLI SAPMALAR (ölçüldü — sessiz değil, yazılı; raporun `sapmalar` bloğunda da durur):
  (a) GİRİŞ SEMANTİĞİ. Üretimin `PaperBroker.fill_entry`i silahlı planı ertesi açılışta KOŞULSUZ
      doldurur (kaymalı); gölge motoru "ilk uygun bar + stop-al dolumu" kuralını uygular
      (`golge_icra` beyanlı sapma 3) ve sürtünmeyi fiyata İŞLEMEZ (sapma 1). Açılışı tetiğin
      ALTINDA olan bir seansta gerçek yol girer, gölge GİRMEZ (`giris_reddi="tetik_gelmedi"`).
      Bu, PK (2)'nin ölçmek İÇİN var olduğu farktır; sayısı `kontrol.giris_yok_n`de durur.
  (b) İCRA GİRDİSİ (ATR). `golge_icra._girisi_dene` limiti `entry_limit_price(tetik, None)` ile
      kurar — uyuyan planda ATR yoktur. Gerçek yolda ATR VARDIR ve donmuş girdinin `e2` satırında
      ölçülüdür; gölge onu KULLANMAZ (motorun kendi sapması 4). Fark raporun `e2_atr` sütununda
      görünür, gölgeye ENJEKTE EDİLMEZ.
  (c) PARAMETRE KUŞAĞI. `--params` bir DİZİN alır ve İKİ DONMUŞ SINIF vardır (bkz. aşağıda);
      VARSAYILAN `canli_v5_donmus`tur çünkü ölçülen 10 işlemin 10'u `strategy_version=5` ile
      doğdu. Taban ile planların sürümü ayrışıyorsa her işlem `parametre_ayrismasi` tanısını
      taşır, `parametre_uyumu` ÜÇ DEĞERLİ olarak raporlanır ve rapor ADIYLA söyler. Sayı
      UYDURULMAZ: hangi kuşağın koştuğu ölçülür, kıyas o beyanla okunur.
  (d) REJİM KAPISI. `meridian.regime.regime_ok` bir FONKSİYON olarak doğduysa TEK KAYNAK odur;
      doğmadıysa motor ifadesinin BEYANLI kopyası (`pk3_selef.rejim_of`) konuşur. Hangisinin
      konuştuğu ÖLÇÜLÜR ve `rejim_kapisi` bloğunda durur (TSK-184 aynı anda uçuşta).
  (e) BAR KAYNAĞI. Kart tarihsel yolda `state/barlar/` parquet arşivini ister; yerelde o arşiv
      YOKTUR ve CSV önbelleği kabul edilir (`bar_kaynak="state/bars"`, PK (3) ile aynı beyan).
      `--bars-dizin` VARSAYILANI artık yerel `state/bars` DEĞİL, Rol-1'in A1'den SALT-OKUR
      çektiği DONMUŞ kopyadır (`pk2_gercek/girdi/bars`, 13 CSV): tur-1'de yerel önbellek
      2026-07-28'de bitiyordu, işlem penceresi ise 2026-08-19…09-11'dir — 10 işlemin 10'u
      ölçülemedi. Kapsam İŞLEM BAŞINA ölçülür (D + ATR ısınması, `golge_icra.LOOKBACK_BAR`);
      karşılamayan işlem `bar_yok:<sembol>` sınıfıyla listede DURUR, sessizce düşmez.

PARAMETRE SINIFI — İKİ DONMUŞ KAYNAK, İKİ AYRI KİMLİK KAPISI (tur-1 §Kaygı 2'nin kapanışı).
  `edg032c_donmus`  → PK (3) ile aynı git-izli kopya; kimlik kapısı `edg032c` KÜNYE KIYASIDIR
                      (`pk3_selef.donmus_parametreler`, AYNEN) ve hücre künyeden enjekte edilir.
  `canli_v5_donmus` → donmuş girdinin altındaki canlı `strategy.yaml` v5 (+ repo goal/bounds);
                      künye kıyası YOKTUR (başka bir kuşağın bayt kaydıdır — Rol-1'in koşumu tam
                      da orada "sha uyuşmuyor (goal.yaml)" ile durdu), yerine GİRDİ MANİFESTOSU
                      kıyası vardır (`girdi/SHA256SUMS`, `params_v5/<ad>` satırları) ve hücre
                      dosyaların KENDİSİNDEN ölçülür (enjeksiyon YOK — uydurma yasağı).
  Sınıf TAHMİN EDİLMEZ, adresten çözülür: iki dizin de modül sabitidir. Üçüncü bir dizin ya da
  bir DOSYA verilirse hata AÇIKTIR ve iki kabul edilen kaynağı adıyla sayar.

PIT (tarihsel yeniden yürütme — SIFIR TOLERANS). `bars_of` her seansta o günün KIRPIĞINI döndürür
(`pk3_selef.golgeden_gecir`), rejim `idx.loc[:d]` ile kurulur: D+1'in barı D'nin görüş alanına
yapısal olarak giremez. `pitlaw` kapı sözleşmesine BU BETİK GİRMEZ — hiçbir fonksiyonu kapı
vokabülerinden (GO/NO_GO/REVIEW) bir karar sabiti döndürmez ve yeni bir tarayıcı yüzeyi açmaz.

KILL#5 (kart): "kontrol PK'sı tutmazsa hiçbir sayı yayılmaz". `gecti is False` olduğunda rapor
işlem başına HİÇBİR sayı basmaz; yalnız engelin KENDİSİ (ortalama |fark|, eşik, pay) ve
bastırılan alanların ADLARI durur — emsal `sayim.markdown_uret`in yayın engeli bloğudur.

OKUR: donmuş girdi artefaktı (+ manifestosu), donmuş bar önbelleği (`pk2_gercek/girdi/bars`,
SALT-OKUNUR), iki donmuş sözleşme kopyasından BİRİ (`pk2_gercek/girdi/params_v5/` — varsayılan —
ya da `pk3_selef/params_donmus/`), edg032c sınıfında ayrıca `edg032c` taban künyesi.
YAZAR: yalnız `--cikti-dizin` altındaki iki artefakt (`sonuc_<utc>.json` + `rapor_<utc>.md`) ve
`--state-dizin` altındaki GEÇİCİ gölge defteri. Canlı `state/` altına HİÇBİR ŞEY yazmaz —
`--state-dizin` deponun `state/` ağacının altındaysa betik BAŞLAMADAN durur.

KOŞUM (operatörün koşacağı biçim) — `--girdi`, `--bars-dizin` ve `--params` VERİLMEZ:
üçünün de varsayılanı donmuş kopyadır, o yüzden reçete taze bir klonda da olduğu gibi koşar.
  .venv/bin/python research/olcumler/edg088_golge_pilot/pk2_gercek.py \\
      --state-dizin <tmp> --cikti-dizin research/olcumler/edg088_golge_pilot/pk2_gercek
ÇIKIŞ: 0 geçti · 2 düştü ya da ölçülemedi · 1 hata (ön şart tutmadı).

"SON 10" KOMUT SATIRINDAN GEVŞETİLEMEZ: `--n-gercek` / `--beklenen-tickerlar` diye bir bayrak
YOKTUR. Kümenin sayısı ve İSİMLERİ modül sabitidir ve `son_n_gercek` onları ÇAĞRI ANINDA çözer
(imza varsayılanı olarak değil) — böylece sabiti yamalayan bir çivi gerçekten yamayı ölçer,
üretim yolu ise kapıyı hiç geçemez (`pk3_selef.suz_049` ile aynı desen).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import sys

import pandas as pd
import yaml

SANDBOX = pathlib.Path(__file__).resolve().parent
KOK = SANDBOX.parents[2]
# TAVUK-YUMURTA BOOTSTRAP: yolu kuran yardımcının KENDİSİ yolda olmalı; bu üç satır yalnız BU
# dizini koyar. Depo kökünü `_ortak.yolu_kur` `sys.path[0]`a koyar ve AYNI yardımcıyı
# `pk3_selef` de çağırır (tek-kaynak yasası; tur-1 §Kaygı 9: `meridian` bu makinede KURULU ve
# kurulu kopya ANA CHECKOUT'u gösteriyor — kök yolda önce gelmezse bir worktree'den koşan betik
# sessizce BAŞKA bir ağacın motorunu ölçerdi). Çözülen yol sonuç künyesine yazılır
# (`motor_yolu`), böylece iddia değil KANIT olur.
if str(SANDBOX) not in sys.path:
    sys.path.insert(0, str(SANDBOX))

import _ortak  # noqa: E402           — iki ölçüm betiğinin PAYLAŞTIĞI yardımcılar

#: Çözülen `(depo kökü, ölçüm dizini)` — `pk3_selef.YOL` ile AYNI olmalıdır (ayrışma çivisi v472 D3).
YOL = _ortak.yolu_kur(__file__)

import pk3_selef as pk3  # noqa: E402  — PK (3) şasisi: donmuş parametre kapıları + gölge geçişi
import sayim  # noqa: E402           — PK (2) eşiği, payı ve üç değerli `gecti` ORADA yaşar
from meridian import golge_icra as gi  # noqa: E402
from meridian import ledgerstamp  # noqa: E402

KART = "EDG-2026-088"
PK = 2

#: RO L-1 HÜKMÜ 7'NİN DONUK KÜMESİ. Sayı DA isim DE kapıdır: girdi değişirse ölçülen popülasyon
#: sessizce başkalaşır ve "PK (2)" adı aynı kalarak başka bir sınamaya dönüşürdü. İsimler
#: donmuş artefaktın `trades` sırasının (A1 sorgusu: `ts_open` DESC) İLK 10'undan ölçülmüştür.
N_GERCEK = 10
BEKLENEN_TICKERLAR = ("MU", "VRTX", "REGN", "CF", "MPC", "NOW", "ECL", "PANW", "DE", "MRVL")

#: Donmuş girdinin adı — betiğin KENDİ dizinine göreli (mutlak yol gömmek, deponun başka bir
#: checkout'unda ya sessizce yanlış dosyayı okurdu ya da hiç okuyamazdı; `pk3_selef` ile aynı desen).
GIRDI_ADI = "pk2_gercek/girdi/a1_gercek_islemler_2026-09-13.json"
MANIFEST_ADI = "SHA256SUMS"

#: DONMUŞ BAR ÖNBELLEĞİ — `--bars-dizin` VARSAYILANI. Tur-1 PK (2)'yi ÖLÇEMEDİ çünkü yerel
#: `state/bars` 2026-07-28'de bitiyordu ve işlem penceresi 2026-08-19…09-11'dir. Rol-1 A1'den
#: SALT-OKUR çektiği 13 CSV'yi (10 işlem sembolü + BDX/LLY yedeği + SPY endeksi) donmuş girdinin
#: altına koydu; dosya adları KÜÇÜK HARFTİR çünkü yükleyici öyle bekler
#: (`adapters.data._cache_path`: `ticker.lower()` — ÖLÇÜLDÜ, varsayılmadı; çivi v472 D2).
BARS_ADI = "pk2_gercek/girdi/bars"

#: PARAMETRE KAYNAĞININ İKİ SINIFI — ikisi de DONMUŞ, ama KİMLİK KAPILARI AYRI (bkz. modül
#: başlığı "PARAMETRE SINIFI"). Ad bir etikettir ve sonuç künyesine yazılır: hangi düğme
#: kuşağının koştuğu okurun TAHMİNİNE bırakılmaz.
PARAMS_SINIFLARI = ("edg032c_donmus", "canli_v5_donmus")

#: CANLI v5 KOPYASININ DİZİNİ — `--params` VARSAYILANI. Betiğin KENDİ dizinine göreli (mutlak yol
#: gömülmez); manifestosu ÜST dizindedir (`girdi/SHA256SUMS`, `params_v5/<ad>` satırlarıyla).
PARAMS_V5_ADI = "pk2_gercek/girdi/params_v5"

#: v5 sınıfında sözleşme dosyalarının adları — PK (3) ile AYNI üçlü (ikinci bir liste ayrışırdı).
SOZLESME_DOSYALARI = pk3.SOZLESME_DOSYALARI

#: BROKER DOLUMUNUN KANIT ALANLARI (`trades.extra_json`). Sınıf bunların VARLIĞINDAN ölçülür.
DOLUM_FIYAT_ALANI = "alpaca_fill_price"
DOLUM_TS_ALANI = "dolum_ts"
SINIFLAR = ("dogrulanmis", "kismi", "ciplak")

#: KILL#5'TE BASTIRILAN İŞLEM-BAŞI ALANLAR — adları raporda durur, DEĞERLERİ durmaz.
BASTIRILAN = ("golge_r", "gercek_r", "fark_r", "golge_giris_fiyat", "golge_cikis_neden",
              "seans_farki")

#: Gölge takibinin beyanlı üst sınırı — PK (3) ile AYNI sabit (ikinci bir kopya sessizce ayrışırdı).
SEANS_TAVANI = pk3.SEANS_TAVANI
BAR_KAYNAK = pk3.BAR_KAYNAK

#: Ölçüm ön şartı tutmadığında atılır. PK (3) ile AYNI sınıf: iki betik tek `except Blok` ile
#: sarmalanabilsin ve "bloklandı" hükmü iki ayakta AYNI şey demek olsun.
Blok = pk3.Blok


def depo_koku() -> pathlib.Path:
    """Depo kökü — betiğin KENDİ konumundan. Mutlak yol gömülmez."""
    return KOK


def girdi_varsayilan(betik: pathlib.Path | None = None) -> pathlib.Path:
    """`--girdi` VARSAYILANI: git-izli donmuş A1 artefaktı, betiğin dizinine göreli."""
    return (betik or pathlib.Path(__file__)).resolve().parent / GIRDI_ADI


def bars_varsayilan(betik: pathlib.Path | None = None) -> pathlib.Path:
    """`--bars-dizin` VARSAYILANI: donmuş bar önbelleği, betiğin dizinine göreli (SALT-OKUNUR)."""
    return (betik or pathlib.Path(__file__)).resolve().parent / BARS_ADI


def params_edg032c_dizin(betik: pathlib.Path | None = None) -> pathlib.Path:
    """`edg032c_donmus` SINIFININ dizini — PK (3) ile AYNI kopya (kendi kopyası YOK)."""
    return pk3.params_varsayilan(None if betik is None else betik).parent


def params_v5_dizin(betik: pathlib.Path | None = None) -> pathlib.Path:
    """`canli_v5_donmus` SINIFININ dizini — donmuş girdinin altındaki canlı `strategy.yaml` v5."""
    return (betik or pathlib.Path(__file__)).resolve().parent / PARAMS_V5_ADI


def params_varsayilan(betik: pathlib.Path | None = None) -> pathlib.Path:
    """`--params` VARSAYILANI: CANLI v5 dizini.

    NİÇİN PK (3) İLE AYNI TABAN DEĞİL (tur-1 §Kaygı 2 — Rol-1'in koşumunu DURDURAN hata). PK (3)
    EDG-049'un planlarını YENİDEN DOĞURUR ve o planlar `edg032c` kuşağında (v3) doğdu; onun
    doğru tabanı donmuş edg032c kopyasıdır. PK (2) ise canlı yolun KENDİ işlemlerini ölçer ve
    o işlemlerin hepsi `strategy_version=5` ile doğdu (10/10, ölçüldü). Gölgeyi v3 ile yönetmek,
    "gölge motoru ≈ gerçek motor" sorusunu "v3 gölge ≈ v5 gerçek"e çevirirdi — ölçülen şey
    sessizce başkalaşırdı. Varsayılan bu yüzden v5'tir; edg032c dizini `--params` ile HÂLÂ
    verilebilir ve o sınıfın künye kapısı AYNEN işler.
    """
    return params_v5_dizin(betik)


# ==================================================================================================
# PARAMETRE SINIFI — İKİ DONMUŞ KAYNAK, İKİ AYRI KİMLİK KAPISI
# ==================================================================================================
def _manifest_satirlari(manifest: pathlib.Path) -> dict:
    """`SHA256SUMS` → `{göreli yol: sha}`. Biçim `sha256sum(1)`in kendisidir (`*` ikili işareti
    kırpılır); ayrıştırılamayan satır SESSİZCE atlanmaz, hiç eşleşmez ve kapı öter."""
    kayit: dict = {}
    for satir in manifest.read_text(encoding="utf-8").splitlines():
        parca = satir.split()
        if len(parca) >= 2:
            kayit[parca[-1].lstrip("*")] = parca[0]
    return kayit


def parametre_sinifi_coz(params_dizin: pathlib.Path,
                         betik: pathlib.Path | None = None) -> str:
    """`--params` DİZİNİNİN sınıfı: `edg032c_donmus` ya da `canli_v5_donmus`. Üçüncüsü YOK.

    SINIF TAHMİN EDİLMEZ, ADRESTEN ÇÖZÜLÜR. "Künye kıyasını dene, tutmazsa öteki sınıftır" gibi
    bir kural, KURCALANMIŞ bir edg032c dizinini sessizce v5 sanardı — yani kimlik kapısının
    kendisini bir sınıf tahminine çevirirdi. İki kabul edilen dizin modül sabitidir ve ÇAĞRI
    ANINDA çözülür (çivi sabiti yamalayabilsin, üretim yolu kapıyı hiç geçemesin — `son_n_gercek`
    ile aynı desen).

    Bir DOSYA verilirse hata AÇIKTIR: `--params` bir dizindir çünkü kimlik kapısı üç sözleşme
    dosyasının ÜÇÜNÜ birden ölçer (tek bir `strategy.yaml`, yanındaki goal/bounds'ı doğrulamaz).
    """
    yol = pathlib.Path(params_dizin)
    if yol.is_file() or yol.suffix in (".yaml", ".yml"):
        raise Blok(f"--params bir DİZİN alır, dosya değil: {yol} — kimlik kapısı "
                   f"{list(SOZLESME_DOSYALARI)} dosyalarının ÜÇÜNÜ birden ölçer")
    coz = yol.resolve()
    if coz == params_edg032c_dizin(betik).resolve():
        return PARAMS_SINIFLARI[0]
    if coz == params_v5_dizin(betik).resolve():
        return PARAMS_SINIFLARI[1]
    raise Blok(
        f"tanınmayan parametre dizini: {yol} — PK (2) YALNIZ iki donmuş kaynağı kabul eder: "
        f"{PARAMS_SINIFLARI[0]} → {params_edg032c_dizin(betik)} (künye kıyası) · "
        f"{PARAMS_SINIFLARI[1]} → {params_v5_dizin(betik)} (girdi manifestosu kıyası)")


def _v5_tabani(params_dizin: pathlib.Path) -> dict:
    """`canli_v5_donmus` tabanı: kimlik GİRDİ MANİFESTOSUNDAN, hücre KENDİ DOSYALARINDAN.

    KÜNYE KIYASI YOK, KİMLİK KAPISI VAR. `edg032c` künyesi bir BAŞKA kuşağın (v3) bayt kaydıdır;
    v5 dosyalarını ona karşı ölçmek "BLOKLANDI: donmuş sözleşme sha uyuşmuyor (goal.yaml)" dışında
    bir sonuç veremezdi (tur-1'de tam olarak bu oldu). Kapı KALKMAZ, YER DEĞİŞTİRİR: Rol-1'in
    A1'den çektiği artefaktın kendi manifestosu (`girdi/SHA256SUMS`) üç dosyanın da sha'sını
    taşır ve koşum onunla doğrulanır — manifesto yoksa ya da tutmazsa betik BAŞLAMAZ.

    HÜCRE DE ENJEKTE EDİLMEZ. PK (3)'te slot/boyut/ısı zarfı künyeden enjekte edilir çünkü
    `edg032c` bir ARAMA HÜCRESİDİR ve dosyalar o hücrenin dışından gelir. v5'te ise goal/strategy
    CANLI yolun KENDİ dosyalarıdır: gerçek işlemler tam o değerlerle doğdu, üstüne bir başka
    kuşağın hücresini yazmak ölçüleni uydurulana çevirirdi (UYDURMA YASAĞI).
    """
    dizin = pathlib.Path(params_dizin).resolve()
    man = dizin.parent / MANIFEST_ADI
    if not man.exists():
        raise Blok(f"v5 parametre dizininin manifestosu ({MANIFEST_ADI}) yok: {man} — donmuş "
                   "kopyanın kimliği doğrulanamaz")
    kayit = _manifest_satirlari(man)
    olculen = {}
    for ad in SOZLESME_DOSYALARI:
        dosya = dizin / ad
        if not dosya.exists():
            raise Blok(f"v5 parametre dizininde {ad} yok: {dosya}")
        olculen[ad] = hashlib.sha256(dosya.read_bytes()).hexdigest()
        anahtar = f"{dizin.name}/{ad}"
        if anahtar not in kayit:
            raise Blok(f"manifestoda {anahtar!r} satırı YOK: {man}")
        if kayit[anahtar] != olculen[ad]:
            raise Blok(f"v5 parametre sha256 uyuşmuyor ({ad}): ölçülen {olculen[ad][:16]} ≠ "
                       f"manifesto {kayit[anahtar][:16]} — donmuş kopya DEĞİŞMİŞ")

    stg = yaml.safe_load((dizin / "strategy.yaml").read_text(encoding="utf-8"))
    params = dict(stg["params"])
    if "position_size_r" not in params:
        raise Blok(f"v5 strategy.yaml `params.position_size_r` taşımıyor: {dizin} — "
                   "enjeksiyon değeri UYDURULAMAZ")
    by_regime = stg.get("params_by_regime") or None
    for rejim, ovr in (by_regime or {}).items():
        if ovr:
            raise Blok(f"params_by_regime[{rejim}] dolu ({sorted(ovr)}) — canlı v5 tabanında "
                       "rejim override'ı ölçülen tabanı sessizce kaydırırdı")
    goal_v = yaml.safe_load((dizin / "goal.yaml").read_text(encoding="utf-8")) or {}
    limitler = goal_v.get("limits") or {}
    for alan in ("max_open_positions", "heat_hard_r"):
        if alan not in limitler:
            raise Blok(f"v5 goal.yaml `limits.{alan}` taşımıyor: {dizin} — hücre UYDURULAMAZ")
    return {
        "sinif": PARAMS_SINIFLARI[1],
        "params": params, "by_regime": by_regime,
        "version": int(stg.get("version", 1)),
        # Hücre ÖLÇÜLÜR (enjekte edilmez); `goal_enjekte` v5'te ÇAĞRILMAZ — bkz. `kos`.
        "hucre": {"slot": int(limitler["max_open_positions"]),
                  "position_size_r": float(params["position_size_r"]),
                  "heat_hard_r": float(limitler["heat_hard_r"])},
        "hucre_kaynagi": "canli_v5_dosyalari",
        "sha256": olculen, "manifest": str(man),
        "kunye_yolu": None, "kunye_taban": None, "kunye_dondurma": None,
    }


def parametre_tabani(params_dizin: pathlib.Path, kunye_p: pathlib.Path | None = None,
                     betik: pathlib.Path | None = None) -> dict:
    """Sınıfına göre DONMUŞ parametre tabanı + kimlik kanıtı. Dönüş `pk3.donmus_parametreler`in
    sözlüğüne `sinif` / `hucre_kaynagi` ekler; ikisi de sonuç künyesine yazılır."""
    sinif = parametre_sinifi_coz(params_dizin, betik)
    if sinif == PARAMS_SINIFLARI[1]:
        return _v5_tabani(params_dizin)
    taban = pk3.donmus_parametreler(pathlib.Path(params_dizin) / "strategy.yaml", kunye_p)
    taban["sinif"] = PARAMS_SINIFLARI[0]
    taban["hucre_kaynagi"] = "edg032c_kunyesi"
    taban["manifest"] = None
    return taban


# ==================================================================================================
# GİRDİ KİMLİĞİ — manifesto MEKANİK kapıdır
# ==================================================================================================
def manifest_dogrula(yol: pathlib.Path, manifest: pathlib.Path | None = None) -> dict:
    """Donmuş girdinin sha256'sını YANINDAKİ `SHA256SUMS` ile karşılaştırır.

    Kart bir artefaktı donduruyorsa kimliği bir BEYAN değil bir ÖLÇÜM olmalıdır (EDG-2026-059
    sınıfı: ağaca bağlı girdi, ağaç değişince kartı sessizce öldürür). Manifesto yoksa ya da
    satır tutmuyorsa koşum BAŞLAMAZ — "ölçemedim" ile "eşleşmedi" karışmasın diye ikisi AYRI
    hükümdür ve ikisi de `Blok`tur.
    """
    yol = pathlib.Path(yol)
    if not yol.exists():
        raise Blok(f"girdi dosyası yok: {yol}")
    man = pathlib.Path(manifest) if manifest else (yol.parent / MANIFEST_ADI)
    if not man.exists():
        raise Blok(f"girdi manifestosu ({MANIFEST_ADI}) yok: {man} — donmuş girdinin kimliği "
                   "doğrulanamaz")
    beklenen = None
    for satir in man.read_text(encoding="utf-8").splitlines():
        parca = satir.split()
        if len(parca) >= 2 and parca[-1].lstrip("*") == yol.name:
            beklenen = parca[0]
            break
    if beklenen is None:
        raise Blok(f"manifestoda {yol.name!r} satırı YOK: {man}")
    olculen = hashlib.sha256(yol.read_bytes()).hexdigest()
    if olculen != beklenen:
        raise Blok(f"girdi sha256 uyuşmuyor ({yol.name}): ölçülen {olculen[:16]} ≠ "
                   f"manifesto {beklenen[:16]} — girdi DEĞİŞMİŞ, donmuş sayılamaz")
    return {"dosya": str(yol), "sha256": olculen, "manifest": str(man)}


def girdi_oku(yol: pathlib.Path, manifest: pathlib.Path | None = None) -> dict:
    """Donmuş artefakt — kimliği DOĞRULANDIKTAN sonra. Dönüş: sözlüğün kendisi + `kimlik`."""
    kimlik = manifest_dogrula(yol, manifest)
    veri = json.loads(pathlib.Path(yol).read_text(encoding="utf-8"))
    for alan in ("trades", "plans"):
        if not isinstance(veri.get(alan), list) or not veri[alan]:
            raise Blok(f"girdi artefaktında `{alan}` listesi YOK ya da boş: {yol}")
    veri["kimlik"] = kimlik
    return veri


# ==================================================================================================
# "SON 10" SÜZGECİ — DONUK
# ==================================================================================================
def son_n_gercek(trades: list[dict], n: int | None = None,
                 beklenen: tuple[str, ...] | None = None) -> list[dict]:
    """Donmuş `trades` listesinin İLK `n` satırı (A1 sorgusu `ts_open` DESC sıralı verdi).

    SIRA YENİDEN KURULMAZ. `ts_open` gününde ÜÇ işlem berabere (2026-08-20: MRVL/LLY/BDX) ve
    "son 10"un sınırı tam o beraberliğin İÇİNDEN geçiyor; yani sıralamayı burada yeniden
    türetmek, A1'in kesme noktasını sessizce kaydırabilirdi. Onun yerine küme İSİMLE dondurulur
    ve süzgeç bir KİMLİK sınamasına çevrilir: girdi başka bir sıra taşırsa koşum BAŞLAMAZ.

    İKİ VARSAYILAN DA ÇAĞRI ANINDA MODÜL SABİTİNDEN ÇÖZÜLÜR (imza varsayılanı olarak DEĞİL):
    imzada dondurulsalardı, sabiti yamalayan bir çivi eski değeri okumaya devam ederdi.
    """
    n = N_GERCEK if n is None else int(n)
    beklenen = BEKLENEN_TICKERLAR if beklenen is None else tuple(beklenen)
    if len(trades) < n:
        raise Blok(f"girdide yeterli işlem yok: {len(trades)} < {n}")
    secilen = list(trades[:n])
    olculen = tuple(str(t.get("ticker")) for t in secilen)
    if olculen != tuple(beklenen):
        raise Blok(f"son {n} gerçek işlem donuk küme ile AYNI DEĞİL: ölçülen {olculen} ≠ "
                   f"beklenen {tuple(beklenen)} — girdi değişmiş, başka bir popülasyon ölçülürdü")
    return secilen


# ==================================================================================================
# DOLUM SINIFI — ALAN ÖLÇÜMÜ (sembol listesi DEĞİL)
# ==================================================================================================
def _extra(trade: dict) -> dict:
    """`extra_json` — dizge ya da sözlük; çözülemiyorsa BOŞ sözlük (alan YOK demektir)."""
    ham = trade.get("extra_json")
    if isinstance(ham, dict):
        return ham
    if not isinstance(ham, str) or not ham.strip():
        return {}
    try:
        cozulen = json.loads(ham)
    except (ValueError, TypeError):  # sessiz-yutma: bozuk extra_json "alan yok" ile AYNI hükmü alır (çıplak sınıf) ve sınıf sayımında GÖRÜNÜR — uydurulmuş bir dolum kanıtı, doğrulanmamış bir işlemi doğrulanmış gösterirdi
        return {}
    return cozulen if isinstance(cozulen, dict) else {}


def dolum_sinifi(trade: dict) -> str:
    """Broker dolumunun KANIT sınıfı: `dogrulanmis` · `kismi` · `ciplak`.

    `dogrulanmis` — hem dolum FİYATI hem dolum ANI defterde (`alpaca_fill_price` + `dolum_ts`).
    `kismi`       — fiyat var, an YOK: ayna fiyatı kaydedilmiş ama dolum damgası düşmemiş.
    `ciplak`      — ikisi de yok: gerçek yolda broker dolumu DOĞRULANMAMIŞ işlem.
    Sınıf DÜŞÜRME ölçütü DEĞİLDİR (kart kill#3): yalnız ikinci bir ortalamanın paydasını kurar.
    """
    ex = _extra(trade)
    fiyat, an = DOLUM_FIYAT_ALANI in ex, DOLUM_TS_ALANI in ex
    if fiyat and an:
        return SINIFLAR[0]
    if fiyat or an:
        return SINIFLAR[1]
    return SINIFLAR[2]


# ==================================================================================================
# PLAN SATIRI — TÜRETME YOK
# ==================================================================================================
def plan_haritasi(plans: list[dict]) -> dict:
    """`plan_id → plan satırı`. Aynı kimlik iki kez gelirse koşum BAŞLAMAZ (hangisinin ölçüldüğü
    belirsiz kalırdı)."""
    harita: dict = {}
    for p in plans or []:
        pid = str(p.get("id") or "")
        if not pid:
            continue
        if pid in harita:
            raise Blok(f"plan tablosunda MÜKERRER kimlik: {pid}")
        harita[pid] = p
    return harita


def golge_plani(plan: dict) -> dict:
    """Plan satırından gölge motorunun TÜKETTİĞİ alanlar — hepsi BİREBİR kopya.

    `golge_icra._bekleyen_kayit` yalnız bu alanları okur. Sözlük DAR tutulur ki işlemin
    gerçekleşmiş fiyatları (`entry`/`exit`/`r_multiple`) gölge planına YAPISAL OLARAK giremesin:
    "türetme yok" bir söz değil bir kısıt olsun.
    """
    eksik = [a for a in ("id", "ticker", "date", "entry_trigger", "stop") if plan.get(a) is None]
    if eksik:
        raise Blok(f"plan satırında icra alanları eksik ({plan.get('id')}): {eksik} — "
                   "TÜRETİLMEZ (uydurma yasağı)")
    return {"id": plan["id"], "ticker": plan["ticker"], "date": plan["date"],
            "entry_trigger": plan["entry_trigger"], "stop": plan["stop"],
            "profit_target": plan.get("profit_target"), "setup": plan.get("setup"),
            "gate_verdict": plan.get("gate_verdict"),
            "dormant_setup": plan.get("dormant_setup"),
            "strategy_version": plan.get("strategy_version")}


# ==================================================================================================
# EŞİK / REJİM KAYNAĞI — İKİSİ DE ÖLÇÜLÜR, YENİDEN YAZILMAZ
# ==================================================================================================
def fark_ust() -> float:
    """PK (2) eşiği — `golge_icra.FARK_R_UST`. Bu dosyada sayı olarak YAZILI DEĞİLDİR; kart ile
    motor sabitinin ayrışmasını `sayim.calistir`ın `esik_ayrismasi` bloğu ayrıca ölçer."""
    return float(gi.FARK_R_UST)


def rejim_kapisi_kaynagi() -> dict:
    """`regime_ok` hangi kaynaktan konuşuyor — ÖLÇÜLÜR, varsayılmaz.

    Motorda bir FONKSİYON olarak doğduysa (TSK-184) tek kaynak odur ve gölge geçişinin de ona
    bağlanması gerekir; bugün YOK (ölçüldü) ve `pk3_selef.rejim_of`un BEYANLI kopyası konuşuyor.
    İkinci bir kopya BU dosyada açılmaz: aynı ifadenin üçüncü yazımı, ayrışmanın kendisi olurdu.
    """
    from meridian import regime as regime_mod

    var = hasattr(regime_mod, "regime_ok")
    return {
        "motorda_fonksiyon_var": var,
        "kullanilan": ("meridian.regime.regime_ok" if var
                       else "pk3_selef.rejim_of (beyanlı kopya)"),
        "beyan": ("`regime_ok` motorda bir FONKSİYON değil bir İFADEdir ve üç üreticide "
                  "(`backtest.replay`, `loop.daily_cycle`, `shadow_lifecycle._seed`) birebir "
                  "aynı biçimde yazılıdır; PK (3) şasisi onu BEYANLI kopya olarak taşır. "
                  "TSK-184 fonksiyonu doğurursa bu blok VAR der ve şasi tek kaynağa bağlanmalıdır "
                  "— bağlanmadan bu beyan bir AÇIK KALEMdir."),
    }


def _state_izni(state_dizin: pathlib.Path) -> pathlib.Path:
    """Geçici state kökü deponun `state/` ağacının ALTINDA olamaz — kapı `_ortak.state_izni`.

    İKİNCİ KOPYA KALDIRILDI (tur-1 §Kaygı 4). Kapı burada ve `pk3_selef.kos`ta iki ayrı yerde
    yazılıydı; aynı gerçeğin iki kopyası sessizce ayrışır. Artık ikisi de tek yardımcıyı çağırır
    ve ayrışma çivisi (v472 D3) yardımcıyı yamayıp İKİ betiğin de yamayı gördüğünü ölçer. Modül
    ÜZERİNDEN çağrılır (`_ortak.state_izni`), doğrudan ithal edilmiş bir adla değil: yama ancak
    çağrı anında çözülen bir adı ısırabilir.
    """
    return _ortak.state_izni(state_dizin, depo_koku())


# ==================================================================================================
# KOŞUM
# ==================================================================================================
def kos(girdi: pathlib.Path, bars_dizin: pathlib.Path, params_dizin: pathlib.Path,
        state_dizin: pathlib.Path, seans_tavani: int | None = None,
        kunye_p: pathlib.Path | None = None, manifest: pathlib.Path | None = None,
        n_gercek: int | None = None,
        beklenen_tickerlar: tuple[str, ...] | None = None) -> dict:
    """PK (2)'nin tamamı: girdi kimliği → gölge geçişi → `sayim.kontrol_olc`. Dönüş: sonuç sözlüğü.

    `--cikti-dizin`e YAZMAZ (yazım `main`in işidir): bu fonksiyon çivilerden de çağrılır ve bir
    ölçüm fonksiyonunun yan etkisi, testi dosya sistemine bağlamaktan başka bir şey yapmazdı.
    `n_gercek`/`beklenen_tickerlar` KOMUT SATIRINDA YOKTUR (bkz. modül başlığı); burada yalnız
    sentetik sahnenin mini-vakası için durur.
    """
    from meridian import config

    seans_tavani = SEANS_TAVANI if seans_tavani is None else int(seans_tavani)
    state_dizin = _state_izni(state_dizin)
    params_dizin = pathlib.Path(params_dizin)
    bars_dizin = pathlib.Path(bars_dizin)

    veri = girdi_oku(pathlib.Path(girdi), manifest)
    veri["kimlik"]["dosya_goreli"] = pk3._depo_goreli(pathlib.Path(veri["kimlik"]["dosya"]),
                                                      depo_koku())
    veri["kimlik"]["manifest_goreli"] = pk3._depo_goreli(
        pathlib.Path(veri["kimlik"]["manifest"]), depo_koku())
    secilen = son_n_gercek(veri["trades"], n_gercek, beklenen_tickerlar)
    planlar = plan_haritasi(veri["plans"])
    e2_harita = _e2_harita(veri.get("e2") or [])

    taban = parametre_tabani(params_dizin, kunye_p)
    donmus_dizin = params_dizin.resolve()
    goal_verisi = yaml.safe_load((donmus_dizin / "goal.yaml").read_text(encoding="utf-8")) or {}

    # STATE ÖNCE ÇEVRİLİR, BAR SONRA OKUNUR (PK (3) ile aynı sıra): `dataset.load_cached` bozuk
    # bir satır gördüğünde `obs.warn` yazar ve o yazım `config.STATE`e düşer.
    pk3._state_kur(state_dizin / "_yukleme", donmus_dizin)
    config.BARS = bars_dizin.resolve()
    from meridian import dataset
    from meridian.adapters import data as data_adapter

    bars, index = dataset.load_cached()
    if index is None or getattr(index, "empty", True):
        raise Blok(f"endeks barı ({data_adapter.INDEX_SYMBOL}) okunamadı: {bars_dizin}")
    per = {t: df.set_index("date").sort_index() for t, df in bars.items()}
    idx = index.set_index("date").sort_index()
    # ENJEKSİYON YALNIZ `edg032c_donmus` SINIFINDA. v5 goal'ü canlı yolun KENDİ dosyasıdır ve
    # `_state_kur` onu zaten geçici state'e kopyaladı; üstüne bir başka kuşağın hücresini yazmak
    # gerçek işlemin doğduğu zarfı sessizce değiştirirdi (bkz. `_v5_tabani` gerekçesi).
    if taban["sinif"] == PARAMS_SINIFLARI[0]:
        pk3.goal_enjekte(config.goal(), taban["hucre"])

    say = _seans_sayaci(idx)
    golge_satirlar: list[dict] = []
    islemler: list[dict] = []
    dogrulanmis_planlar: set[str] = set()
    for i, t in enumerate(secilen):
        kayit = _islem_kaydi(t, e2_harita, taban)
        kayit["gercek_seans_n"] = say(kayit["gercek_giris_ts"], kayit["gercek_cikis_ts"])
        pid = kayit["plan_id"]
        if kayit["dolum_sinifi"] == SINIFLAR[0]:
            dogrulanmis_planlar.add(pid)
        plan = planlar.get(pid)
        if plan is None:
            kayit["olculemedi"] = "plan_satiri_yok"
            islemler.append(kayit)
            continue
        gp = golge_plani(plan)
        kayit.update({"d_plan": str(gp["date"]), "tetik": gp["entry_trigger"],
                      "plan_stop": gp["stop"], "plan_hedef": gp["profit_target"]})
        d0 = pd.Timestamp(str(gp["date"]))
        if d0 not in idx.index:
            kayit["olculemedi"] = f"endeks_seansi_yok:{gp['date']}"
            islemler.append(kayit)
            continue
        kayit["bar_kapsami"] = _islem_bar_kapsami(per, kayit["ticker"], d0)
        if not kayit["bar_kapsami"]["yeterli"]:
            kayit["olculemedi"] = _kapsam_nedeni(kayit["bar_kapsami"], kayit["ticker"])
            islemler.append(kayit)
            continue
        satir, tani = pk3.golgeden_gecir(gp, d0, per, idx, taban,
                                         state_dizin / f"islem{i:02d}_{kayit['ticker']}",
                                         donmus_dizin, seans_tavani)
        kayit["golge_tani"] = {k: v for k, v in tani.items() if k != "adimlar"}
        if satir is None:
            kayit["olculemedi"] = tani.get("neden") or "satir_yok"
            islemler.append(kayit)
            continue
        golge_satirlar.append(satir)
        _satiri_isle(kayit, satir, say)
        islemler.append(kayit)

    gercek_yolu = state_dizin / "gercek_islemler.jsonl"
    gercek_yolu.parent.mkdir(parents=True, exist_ok=True)
    gercek_yolu.write_text(
        "".join(json.dumps(t, ensure_ascii=False, default=str) + "\n" for t in secilen),
        encoding="utf-8")

    esik = fark_ust()
    kontrol = sayim.kontrol_olc(golge_satirlar, gercek_yolu, goal_verisi, esik)
    dogrulanmis_satirlar = [r for r in golge_satirlar
                            if str(r.get("plan_id")) in dogrulanmis_planlar]
    kontrol_dogrulanmis = sayim.kontrol_olc(dogrulanmis_satirlar, gercek_yolu, goal_verisi, esik)
    _ciftleri_isle(islemler, kontrol)

    yayin_engeli: list[str] = []
    if kontrol["gecti"] is False:
        yayin_engeli.append(
            "kill#5 — PK (2) KONTROL ÖLÇÜLDÜ ve TUTMADI: ortalama |gölge R − gerçek R| = "
            f"{kontrol['ort_mutlak_fark_r']} (eşik {esik}, komisyon+kayma payı "
            f"{kontrol['komisyon_kayma_payi']}). Kart: 'kontrol PK'sı tutmazsa hiçbir sayı "
            "yayılmaz.'")

    import meridian as _meridian

    return {
        "kart": KART, "pozitif_kontrol": PK,
        "olculdu_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "gecti": kontrol["gecti"],
        "yayin_engeli": yayin_engeli,
        "bastirilan": list(BASTIRILAN),
        "n_gercek": len(secilen),
        "n_golge_satiri": len(golge_satirlar),
        "n_olculemeyen": sum(1 for k in islemler if k.get("olculemedi")),
        "n_gercek_disi": kontrol["n_gercek_disi"],
        "kontrol": kontrol,
        "kontrol_dogrulanmis": kontrol_dogrulanmis,
        "dolum_sinifi_dagilimi": {s: sum(1 for k in islemler if k["dolum_sinifi"] == s)
                                  for s in SINIFLAR},
        "islemler": islemler,
        "girdi": veri["kimlik"],
        "girdi_cekim_utc": veri.get("cekim_utc"),
        "parametre_kaynagi": {
            "sinif": taban["sinif"],
            "yol": str(params_dizin), "yol_goreli": pk3._depo_goreli(params_dizin, depo_koku()),
            "sha256": taban["sha256"], "manifest": taban.get("manifest"),
            "kunye": taban["kunye_yolu"],
            "taban": taban["kunye_taban"], "dondurma_utc": taban["kunye_dondurma"],
            "hucre": taban["hucre"], "hucre_kaynagi": taban["hucre_kaynagi"],
            "strategy_version": taban["version"],
            # ARTEFAKTA MUTLAK YOL YAZILMAZ: bugünkü worktree yolu yarın başka bir checkout'ta
            # anlamsızdır (`pk3_selef._depo_goreli` ile aynı doktrin).
            "kimlik_kapisi": (
                "edg032c künye kıyası (config_sha256.sandbox_kaynagi_edg022)"
                if taban["sinif"] == PARAMS_SINIFLARI[0] else
                "girdi manifestosu kıyası ({})".format(
                    pk3._depo_goreli(pathlib.Path(taban["manifest"]), depo_koku())
                    or taban["manifest"]))},
        "parametre_ayrismasi": {
            "params_strategy_version": taban["version"],
            "plan_strategy_versiyonlari": sorted(
                {k["strategy_version_plan"] for k in islemler
                 if k.get("strategy_version_plan") is not None}),
            "n_ayrisan": sum(1 for k in islemler if k.get("parametre_ayrismasi")),
            # ÜÇ DEĞERLİ: True = her planın kuşağı tabanla AYNI · False = en az biri ayrışıyor ·
            # None = hiçbir plan `strategy_version` taşımıyor, yani UYUM ÖLÇÜLEMEDİ (sıfır ile
            # "bilmiyorum" aynı şey değildir).
            "parametre_uyumu": (None if all(k.get("parametre_ayrismasi") is None for k in islemler)
                                else not any(k.get("parametre_ayrismasi") for k in islemler)),
            "beyan": ("tabanın `strategy_version`ı ile canlı planların `strategy_version`ı AYNI "
                      "DEĞİLSE gölge, gerçek işlemin doğduğu düğme kuşağından BAŞKA bir kuşakla "
                      "yönetilir; fark PK (2)'de sapma olarak GÖRÜNÜR, gizlenmez")},
        "rejim_kapisi": rejim_kapisi_kaynagi(),
        "bar_kaynagi": {"dizin": str(bars_dizin.resolve()),
                        "dizin_goreli": pk3._depo_goreli(bars_dizin, depo_koku()),
                        "etiket": BAR_KAYNAK,
                        "arsiv_parquet": None,
                        "son_seans": _bar_kapsami(per, idx),
                        "beyan": ("kart Rol-1 hükmü 2 tarihsel yolda state/barlar parquet "
                                  "arşivini ister; yerelde o dizin YOK (ölçüldü) → state/bars "
                                  "CSV kabul (PK (3) ile aynı beyan)")},
        "motor_yolu": getattr(_meridian, "__file__", None),
        "evren": {"n_sembol": len(per), "endeks": data_adapter.INDEX_SYMBOL},
        "esik": esik,
        "seans_tavani": seans_tavani,
        "sapmalar": [
            "giriş semantiği: üretim ertesi açılışta KOŞULSUZ + kaymalı doldurur, gölge 'ilk "
            "uygun bar + stop-al' kuralını uygular ve sürtünmeyi fiyata İŞLEMEZ "
            "(golge_icra beyanlı sapma 1 ve 3) — PK (2) tam olarak bu farkı ölçer",
            "icra girdisi (ATR): gerçek yolda entry_law ATR'si VAR (girdinin e2 satırında), gölge "
            "limiti atr=None ile kurar (golge_icra beyanlı sapma 4) — enjekte EDİLMEZ",
            "parametre kuşağı: donmuş edg032c tabanı ile planların strategy_version'ı ayrışabilir "
            "(`parametre_ayrismasi` bloğu)",
            "rejim kapısı: küresel/SIKI kapı (keşif sondasının gevşek dalı gölgeye uygulanmaz — "
            "golge_icra beyanlı sapma 5)",
            "bar kaynağı: state/bars CSV önbelleği (parquet arşivi yerelde yok)",
        ],
    }


def _e2_harita(e2: list[dict]) -> dict:
    """`plan_id → İÇ motorun dolum satırı` (yoksa ayna satırı). TANI amaçlıdır, gölgeye girmez."""
    harita: dict = {}
    for r in e2 or []:
        pid = str(r.get("plan_id") or "")
        if not pid:
            continue
        if r.get("motor") == "ic" or pid not in harita:
            harita[pid] = r
    return harita


def _islem_kaydi(t: dict, e2_harita: dict, taban: dict) -> dict:
    """Bir gerçek işlemin rapor satırının GERÇEK tarafı + sınıf/ayrışma tanıları."""
    pid = str(t.get("plan_id") or "")
    e2 = e2_harita.get(pid) or {}
    sv = t.get("strategy_version")
    return {
        "id": t.get("id"), "plan_id": pid, "ticker": t.get("ticker"),
        "dolum_sinifi": dolum_sinifi(t),
        "strategy_version_plan": sv,
        "parametre_ayrismasi": (None if sv is None else int(sv) != int(taban["version"])),
        "gercek_giris_ts": t.get("ts_open"), "gercek_cikis_ts": t.get("ts_close"),
        "gercek_entry": t.get("entry"), "gercek_exit": t.get("exit"),
        "gercek_r": t.get("r_multiple"), "gercek_cikis_neden": t.get("exit_reason"),
        "gercek_bars_held": t.get("bars_held"),
        "e2_resmi_acilis": e2.get("resmi_acilis"), "e2_fill": e2.get("fill"),
        "e2_atr": e2.get("atr"), "e2_limit": e2.get("limit"),
        "d_plan": None, "tetik": None, "plan_stop": None, "plan_hedef": None,
        "golge_giris_ts": None, "golge_giris_fiyat": None, "golge_cikis_ts": None,
        "golge_cikis_fiyat": None, "golge_cikis_neden": None, "golge_r": None,
        "golge_bar_n": None, "golge_giris_reddi": None, "kaynak_bar_hash": None,
        "giris_fiyat_farki": None, "cikis_neden_eslesti": None,
        "gercek_seans_n": None, "golge_seans_n": None, "seans_farki": None,
        "fark_r": None, "friksiyon_payi_r": None,
        "golge_tani": None, "bar_kapsami": None, "olculemedi": None,
    }


def _seans_sayaci(idx):
    """`(a, b) → (a, b] aralığındaki SEANS sayısı` — takvim ENDEKSTEN, uydurulmadan.

    NEDEN `bars_held` DEĞİL (ölçüldü 2026-09-13). Gölge defter satırının alan kümesi
    (`golge_icra.SATIR_ALANLARI`) `bars_held` TAŞIMAZ; taşıdığı `bar_n` TÜKETİLEN bar
    kesitlerinin sayısıdır ve ATR ısınma penceresini (`golge_icra.LOOKBACK_BAR`) de içerir. İkisi
    farklı büyüklüktür; `bar_n − trades.bars_held` çıkarması ADI "bar farkı" olan ama HİÇBİR
    şeyi ölçmeyen bir sayı üretirdi (ilk koşumda −13 yazdı). Karşılaştırılabilir olan TUTMA
    PENCERESİDİR ve iki taraf için de AYNI takvimden sayılır. Uç noktalardan biri takvimde yoksa
    dönüş `None`'dır: kısmi bir pencere, pencere değildir.
    """
    def say(a, b):
        if not a or not b:
            return None
        try:
            ta, tb = pd.Timestamp(str(a)), pd.Timestamp(str(b))
        except (ValueError, TypeError):  # sessiz-yutma: çözülemeyen damga "ölçülemedi"dir — uydurulmuş bir pencere, tutma süresi farkını sahte bir sayıya çevirirdi
            return None
        if ta not in idx.index or tb not in idx.index:
            return None
        return int(((idx.index > ta) & (idx.index <= tb)).sum())
    return say


def _satiri_isle(kayit: dict, satir: dict, say) -> None:
    """Gölge defter satırını rapor kaydına taşır ve TANI FARKLARINI ölçer."""
    kayit.update({
        "golge_giris_ts": satir.get("giris_ts"), "golge_giris_fiyat": satir.get("giris_fiyat"),
        "golge_cikis_ts": satir.get("cikis_ts"), "golge_cikis_fiyat": satir.get("cikis_fiyat"),
        "golge_cikis_neden": satir.get("cikis_neden"), "golge_r": satir.get("R"),
        "golge_bar_n": satir.get("bar_n"), "golge_giris_reddi": satir.get("giris_reddi"),
        "kaynak_bar_hash": satir.get("kaynak_bar_hash"),
    })
    if satir.get("R") is None:
        kayit["olculemedi"] = (satir.get("olculemedi") or satir.get("giris_reddi")
                               or "R_olculemedi")
    g, ge = kayit["golge_giris_fiyat"], kayit["gercek_entry"]
    if g is not None and ge is not None:
        kayit["giris_fiyat_farki"] = round(float(g) - float(ge), 6)
    if kayit["golge_cikis_neden"] and kayit["gercek_cikis_neden"]:
        kayit["cikis_neden_eslesti"] = (kayit["golge_cikis_neden"] == kayit["gercek_cikis_neden"])
    kayit["golge_seans_n"] = say(kayit["golge_giris_ts"], kayit["golge_cikis_ts"])
    if kayit["golge_seans_n"] is not None and kayit["gercek_seans_n"] is not None:
        kayit["seans_farki"] = kayit["golge_seans_n"] - kayit["gercek_seans_n"]


def _ciftleri_isle(islemler: list[dict], kontrol: dict) -> None:
    """`fark_r` ve `friksiyon_payi_r` TEK KAYNAKTAN (`sayim.kontrol_olc`) taşınır, yeniden
    HESAPLANMAZ — ikinci bir fark aritmetiği ilk düzeltmede çatallanırdı."""
    cift = {str(c["plan_id"]): c for c in kontrol.get("ciftler") or []}
    for k in islemler:
        c = cift.get(k["plan_id"])
        if c:
            k["fark_r"] = c.get("fark_r")
            k["friksiyon_payi_r"] = c.get("friksiyon_payi_r")


def _islem_bar_kapsami(per: dict, ticker: str, d0) -> dict:
    """BİR işlemin sembol barlarının D'yi ve ATR ISINMASINI karşılayıp karşılamadığı — ÖLÇÜM.

    TUR-1'İN KÖK NEDENİ BUYDU. Yerel önbellek 2026-07-28'de bitiyordu ve işlem penceresi
    2026-08-19…09-11'di; 10 işlemin 10'u ölçülemedi. Kapsam artık DENEMEDEN ÖNCE ölçülür ve
    yetmezse işlem `bar_yok:<sembol>` sınıfıyla listede DURUR — sessizce düşmez, ortalamanın
    paydasını sessizce küçültmez (kart kill#3'ün aynı hükmü). Isınma eşiği motorun KENDİ
    sabitidir (`golge_icra.LOOKBACK_BAR` = `strategy.ATR_PERIOD + 1`), burada sayı olarak
    yazılı DEĞİLDİR: ATR penceresi değişirse kapsam ölçüsü onunla birlikte değişir.
    """
    df = per.get(ticker)
    if df is None or not len(df):
        return {"var": False, "son_seans": None, "isinma_n": 0, "yeterli": False}
    d0 = pd.Timestamp(d0)
    isinma_n = int((df.index < d0).sum())
    return {"var": True, "son_seans": str(df.index.max().date()), "isinma_n": isinma_n,
            "yeterli": bool(d0 <= df.index.max() and isinma_n >= gi.LOOKBACK_BAR)}


def _kapsam_nedeni(kapsam: dict, ticker: str) -> str:
    """Kapsam yetmediğinde "ölçülemedi" NEDENİ — sınıf adıyla, tahminle değil."""
    if not kapsam["var"]:
        return f"bar_yok:{ticker}"
    if kapsam["isinma_n"] < gi.LOOKBACK_BAR:
        return f"bar_yok:{ticker}:isinma_{kapsam['isinma_n']}<{gi.LOOKBACK_BAR}"
    return f"bar_yok:{ticker}:son_seans_{kapsam['son_seans']}"


def _bar_kapsami(per: dict, idx) -> dict:
    """Bar önbelleğinin KAPSADIĞI son seans — işlem penceresi dışındaysa "ölçülemedi" bunun
    sonucudur ve sebebi ADIYLA raporda durur (uydurma yasağı: kapsam TAHMİN edilmez)."""
    sonlar = [str(df.index.max().date()) for df in per.values() if len(df)]
    return {"sembol_son_seans_max": max(sonlar) if sonlar else None,
            "sembol_son_seans_min": min(sonlar) if sonlar else None,
            "endeks_son_seans": (str(idx.index.max().date()) if len(idx) else None)}


# ==================================================================================================
# RAPOR
# ==================================================================================================
def _sayi(x, basamak: int = 6) -> str:
    if x is None:
        return "—"
    if isinstance(x, bool):
        return "evet" if x else "hayır"
    if isinstance(x, (int, float)):
        return f"{float(x):.{basamak}f}".rstrip("0").rstrip(".") or "0"
    return str(x)


def _hukum_adi(gecti) -> str:
    return {True: "GEÇTİ", False: "DÜŞTÜ", None: "ÖLÇÜLEMEDİ"}[gecti]


def _ortalama_satiri(ad: str, k: dict) -> str:
    return (f"- **{ad}**: n={k['n_cift']} çift (hüküm çifti {k['n_hukum_cifti']}) · "
            f"ortalama fark {_sayi(k['ort_fark_r'])}R · ortalama |fark| "
            f"**{_sayi(k['ort_mutlak_fark_r'])}R** · komisyon+kayma payı "
            f"{_sayi(k['komisyon_kayma_payi'])}R · eşik {_sayi(k['esik'])}R · "
            f"`gecti={k['gecti']}`" + (f" · neden: {k['neden']}" if k.get("neden") else ""))


def rapor_metni(sonuc: dict) -> str:
    """Sonuç sözlüğünün insan okuru için Markdown karşılığı. TEK KAYNAK sözlüktür: bu fonksiyon
    hiçbir sayıyı yeniden hesaplamaz, yalnız biçimlendirir (ve kill#5'te bastırır)."""
    d = sonuc
    k, kd = d["kontrol"], d["kontrol_dogrulanmis"]
    bas = [f"# {d['kart']} — PK ({d['pozitif_kontrol']}) GERÇEK: son {d['n_gercek']} gerçek işlem "
           "gölge motorunda", "",
           f"**HÜKÜM (ölçüm): {_hukum_adi(d['gecti'])}** — ölçüm {d['olculdu_utc']} · "
           "kart hükmü Rol-1'indir (bu rapor SAYI üretir)", ""]

    # ---- KILL#5: PK ölçülüp DÜŞTÜYSE işlem başına HİÇBİR sayı basılmaz ----------------------
    if d["yayin_engeli"]:
        s = bas + ["## PK DÜŞTÜ — SAYI YAYILMAZ", ""]
        s += [f"* {x}" for x in d["yayin_engeli"]]
        s += ["", f"Bastırılan alanlar: `{'`, `'.join(d['bastirilan'])}` "
                  "(işlem başına tablo tamamen bastırıldı).", "",
              "### Yalnız kontrol ölçümü (engelin kendisi)", "",
              _ortalama_satiri("hepsi (hükmün kümesi)", k),
              _ortalama_satiri("yalnız doğrulanmış dolum (tanı)", kd), "",
              "## Kimlik", ""] + _kimlik_satirlari(d)
        return "\n".join(s) + "\n"

    sat = ["| işlem | sembol | D | dolum sınıfı | gerçek R | gölge R | Δ R | pay R | "
           "gerçek çıkış | gölge çıkış | giriş fiyatı farkı | tutma seansı (gölge/gerçek) |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in d["islemler"]:
        sat.append("| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            r["id"], r["ticker"], r["d_plan"] or "—", r["dolum_sinifi"],
            _sayi(r["gercek_r"]), _sayi(r["golge_r"]) if r["golge_r"] is not None
            else (r["olculemedi"] or "ölçülemedi"),
            _sayi(r["fark_r"]), _sayi(r["friksiyon_payi_r"]),
            r["gercek_cikis_neden"] or "—",
            r["golge_cikis_neden"] or (r["golge_giris_reddi"] or "—"),
            _sayi(r["giris_fiyat_farki"]),
            f"{_sayi(r['golge_seans_n'])}/{_sayi(r['gercek_seans_n'])} "
            f"(Δ {_sayi(r['seans_farki'])})"))

    pa = d["parametre_ayrismasi"]
    return "\n".join(bas + [
        "## Ortalamalar — İKİ PAYDA (kart kill#3: çıplak ayna sınıfı DÜŞÜRÜLMEZ)", "",
        _ortalama_satiri("hepsi (hükmün kümesi)", k),
        _ortalama_satiri("yalnız doğrulanmış dolum (tanı)", kd),
        f"- dolum sınıfı dağılımı: {d['dolum_sinifi_dagilimi']} · giriş hiç olmayan gölge satırı: "
        f"{k['giris_yok_n']} · payı ölçülemeyen çift: {k['n_payi_olculemeyen']}",
        f"- gerçek defter: n={k['n_gercek']} satır okundu · `live_paper` damgası OLMAYAN "
        f"(hükme girmeyen): {d['n_gercek_disi']} · ölçülemeyen işlem: {d['n_olculemeyen']}",
        "",
        "## İşlem başına", "", *sat, "",
        "## Parametre kuşağı", "",
        f"- **sınıf**: `{d['parametre_kaynagi']['sinif']}` · kimlik kapısı: "
        f"{d['parametre_kaynagi']['kimlik_kapisi']} · hücre kaynağı: "
        f"`{d['parametre_kaynagi']['hucre_kaynagi']}`",
        f"- donmuş taban `strategy_version`: {pa['params_strategy_version']} · planların "
        f"sürümleri: {pa['plan_strategy_versiyonlari']} · ayrışan işlem: {pa['n_ayrisan']} · "
        f"`parametre_uyumu={pa['parametre_uyumu']}`",
        f"- {pa['beyan']}",
        "",
        "## Rejim kapısı", "",
        f"- motorda `regime.regime_ok` fonksiyonu: "
        f"{'VAR' if d['rejim_kapisi']['motorda_fonksiyon_var'] else 'YOK'} · kullanılan: "
        f"`{d['rejim_kapisi']['kullanilan']}`",
        f"- {d['rejim_kapisi']['beyan']}",
        "",
        "## Kimlik", "", *_kimlik_satirlari(d),
        "",
        "## Beyanlı sapmalar", "", *[f"- {x}" for x in d["sapmalar"]],
        "",
        "## PIT çapası", "",
        "Her satırın `kaynak_bar_hash`i TÜKETİLEN OHLCV kesitlerinden türer "
        "(`golge_icra.bar_hash`); gölge adımında evren `.loc[:D]` ile KIRPILARAK verilir — "
        "D+1'den sonraki bir bar D'nin görüş alanına yapısal olarak giremez.",
        "",
        *[f"- `{r['plan_id']}` → `{r['kaynak_bar_hash']}`" for r in d["islemler"]],
        "",
    ]) + "\n"


def _kimlik_satirlari(d: dict) -> list[str]:
    pk_ = d["parametre_kaynagi"]
    b = d["bar_kaynagi"]
    return [
        # MOTOR YOLU bilerek MUTLAKtır (hangi ağacın motoru koştu — kanıt); girdi yolları
        # göreli, çünkü artefakt başka bir checkout'ta da okunabilmeli.
        f"- **donmuş girdi**: `{d['girdi'].get('dosya_goreli') or d['girdi']['dosya']}` sha256 "
        f"`{d['girdi']['sha256'][:16]}…` (manifesto "
        f"`{d['girdi'].get('manifest_goreli') or d['girdi']['manifest']}`) · A1 çekimi "
        f"{d['girdi_cekim_utc']}",
        f"- **donmuş parametreler** (`{pk_['sinif']}`): "
        f"`{pk_.get('yol_goreli') or pk_['yol']}` sha256 "
        f"`{pk_['sha256']['strategy.yaml'][:16]}…` (goal `{pk_['sha256']['goal.yaml'][:16]}…`, "
        f"bounds `{pk_['sha256']['bounds.yaml'][:16]}…`) · `strategy_version` "
        f"{pk_['strategy_version']} · kimlik kapısı: {pk_['kimlik_kapisi']}"
        + (f" — `{pk_['taban']}` ({pk_['dondurma_utc']}), künye `{pk_['kunye']}`"
           if pk_['kunye'] else ""),
        f"- **bar kaynağı**: `{b.get('dizin_goreli') or b['dizin']}` "
        f"(`bar_kaynak=\"{b['etiket']}\"`) — sembol son seansı "
        f"{b['son_seans']['sembol_son_seans_min']}…{b['son_seans']['sembol_son_seans_max']} · "
        f"endeks son seansı {b['son_seans']['endeks_son_seans']}",
        f"  - {b['beyan']}",
        f"- **motor**: `{d['motor_yolu']}` · evren {d['evren']['n_sembol']} sembol + endeks "
        f"{d['evren']['endeks']} · seans tavanı {d['seans_tavani']}",
    ]


# ==================================================================================================
# KOMUT SATIRI
# ==================================================================================================
def main(argv: list[str] | None = None) -> int:
    """KOMUT SATIRI sözleşmesi. Çıkış: 0 geçti · 2 düştü ya da ölçülemedi · 1 hata."""
    ap = argparse.ArgumentParser(
        description=f"{KART} PK ({PK}) gerçek — son {N_GERCEK} gerçek işlem gölge motorunda")
    ap.add_argument("--girdi", type=pathlib.Path, default=None,
                    help=f"donmuş A1 artefaktı — VARSAYILAN git-izli kopya ({GIRDI_ADI}, "
                         "betiğin dizinine göreli); yanındaki SHA256SUMS ile doğrulanır")
    ap.add_argument("--bars-dizin", type=pathlib.Path, default=None,
                    help=f"bar önbelleği — SALT-OKUNUR; VARSAYILAN donmuş kopya ({BARS_ADI})")
    ap.add_argument("--params", type=pathlib.Path, default=None,
                    help=f"donmuş parametre DİZİNİ (dosya değil) — {PARAMS_SINIFLARI[0]} ya da "
                         f"{PARAMS_SINIFLARI[1]}; VARSAYILAN canlı v5 ({PARAMS_V5_ADI})")
    ap.add_argument("--state-dizin", required=True, type=pathlib.Path,
                    help="GEÇİCİ state kökü — gölge defteri buraya yazılır (canlı state YASAK)")
    ap.add_argument("--cikti-dizin", required=True, type=pathlib.Path,
                    help="sonuc_<utc>.json + rapor_<utc>.md buraya yazılır")
    ap.add_argument("--seans-tavani", type=int, default=SEANS_TAVANI,
                    help=f"gölge takibinin beyanlı üst sınırı (varsayılan {SEANS_TAVANI})")
    a = ap.parse_args(argv)

    try:
        sonuc = kos(a.girdi or girdi_varsayilan(), a.bars_dizin or bars_varsayilan(),
                    a.params or params_varsayilan(), a.state_dizin, a.seans_tavani)
    except Blok as e:
        print(f"BLOKLANDI: {e}", file=sys.stderr)
        return 1

    a.cikti_dizin.mkdir(parents=True, exist_ok=True)
    damga = sonuc["olculdu_utc"].replace(":", "").replace("-", "")
    (a.cikti_dizin / f"sonuc_{damga}.json").write_text(
        json.dumps(sonuc, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    (a.cikti_dizin / f"rapor_{damga}.md").write_text(rapor_metni(sonuc), encoding="utf-8")
    k = sonuc["kontrol"]
    if sonuc["yayin_engeli"]:
        print(f"{KART} PK({PK}): DÜŞTÜ — {sonuc['yayin_engeli'][0]}")
    else:
        print(f"{KART} PK({PK}): {_hukum_adi(sonuc['gecti'])} · çift {k['n_cift']}/"
              f"{sonuc['n_gercek']} · ortalama |fark| {_sayi(k['ort_mutlak_fark_r'])}R · "
              f"pay {_sayi(k['komisyon_kayma_payi'])}R · eşik {_sayi(k['esik'])}R · "
              f"ölçülemeyen {sonuc['n_olculemeyen']}")
    print(f"çıktı: {a.cikti_dizin}/sonuc_{damga}.json + rapor_{damga}.md")
    return 0 if sonuc["gecti"] is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
