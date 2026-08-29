#!/usr/bin/env python3
"""olcum.py — canlı sistemi TİPLİ sorgulama aracı. LLM yok, tahmin yok.

NEDEN VAR (2026-08-27). Canlı teşhiste olay adı iki kez tahmin edildi ve iki kez SAHTE SIFIR
alındı (`pozisyon_adet_benimsendi` → gerçek ad `adet_benimsendi`; `position_drift` → o bir ALAN,
olay değil). Sahte sıfır "arıza yok" diye okunur — deponun `olcum-baglami-tuzagi` dersi.

DÜZELTME (fix round 1, 2026-08-29 — KRİTİK). İlk sürüm yalnız DÜZ DİZE LİTERALİNİ yakalayan bir
regex kullanıyordu: `obs.warn("ad", …)` görürdü, `obs.alarm(obs.ALARM_MIRROR_DRIFT, …)` GÖRMEZDİ.
Bağımsız ölçüm bunun canlının EN YÜKSEK ÖNCELİKLİ alarm sınıfında sahte sıfır ürettiğini
gösterdi: MIRROR_DRIFT (8 çağrı yeri), NAKED_POSITION (2), TRAIL_DESYNC (1). Çare: `ast` ile
statik çözümleme — düz dize + `obs.ALARM_*` adlandırılmış sabiti + çağrı yerinin KENDİ
dosyasındaki modül-seviyesi sabiti + f-string iskeleti; çözülemeyen çağrılar `cozulemeyen`
sayacına düşer (SESSİZCE YUTULMAZ).

DÜZELTME (fix round 2, 2026-08-29 — KRİTİK, ÜÇÜNCÜ KÖR NOKTA). Round-1 çözümleyicisi ALICIYI
hard-code ediyordu (`f.value.id == "obs"`). Bu depoda YAYGIN bir kalıp bunu atlıyor:
`from . import obs as _obs` (çoğunlukla `except` blokları içinde) — 44 çağrı yeri, düzinelerce
takma ad (`_obs`, `_o`, `_o2`, `_obs_h`, `_obs0`, `_obsL`, `_od`, `_os2`, …). Bu çağrılar hem
ÇÖZÜLEMİYORDU HEM SAYILMIYORDU — round-1'in `cozulemeyen` sayacı da yalnız "obs.X(" biçimini
arıyordu, yani bir ENUMERASYONDU ve bilinmeyen bir biçimi YAKALAYAMAZDI. `ALARM_ARAMA_HAVUZU_OLU`
— 2026-08-25'te TAM DA sessiz bir arızayı kapatmak için eklenmiş bir jeton — bu yüzden
görünmezdi: arızaları kapatmak için var olan ARAÇ, arızayı kapatmak için var olan ALARMIN
KENDİSİNİ kaçırıyordu. Çare, iki parça:

  (a) ALICI ARTIK HARD-CODE DEĞİL. Her dosyanın KENDİ import ifadeleri taranır
      (`from . import obs as X`, `from meridian import obs as X`, `import meridian.obs as X`)
      ve `obs` modülüne BAĞLANAN yerel adlar çıkarılır — sabit bir takma-ad listesi YOK.

  (b) DÜRÜSTLÜK YAPISAL HALE GETİRİLDİ — AMA YALNIZ TARANAN KAPSAM İÇİNDE (bkz. round 4).
      `cozulemeyen` bir ENUMERASYON değil, bir ÇIKARMADIR: (metod adı log/warn/error/alarm olan
      TÜM çağrı yerleri, ALICI FARK ETMEKSİZİN) − (gerçekten çözülenler). AÇILAN DOSYALAR
      İÇİNDE tanınmayan bir alıcı/argüman biçimi ortaya çıkarsa (a)'daki gibi elle
      öğretilmemiş olsa bile TOPLAMA girer, ÇÖZÜLENE girmez, dolayısıyla otomatik olarak
      `cozulemeyen`e düşer — sessizce kaybolmaz. HİÇ AÇILMAYAN bir dosya ise HİÇBİR kovaya
      düşmez: çıkarma onu göremez. Bu yüzden kapsam BEYAN EDİLİR, iddia edilmez. Bunun kasıtlı bir
      yan etkisi: `obs`a hiç bağlı olmayan bir `baska_nesne.warn("x")` çağrısı da artık
      "çözülemeyen obs-benzeri çağrı" sayılır. Bu YANLIŞ YÖNDE bir abartı DEĞİL, DOĞRU yönde
      bir abartıdır — belirsizliği FAZLA beyan etmek dürüsttür, AZ beyan etmek tam da
      düzeltilen arızadır.

DÜZELTME (fix round 4, 2026-08-29 — ASIL KUSUR: TAMLIK İDDİASININ KENDİSİ). Round 1, 2 ve 3'ün
her biri BİR MEKANİZMAYI düzeltti ve ardından TAMLIĞI YENİ SÖZCÜKLERLE YENİDEN İDDİA ETTİ. Round
3'ten sonra SKILL.md "her NE olursa olsun çözemediğimiz her şey" diyordu. Ölçülen dördüncü delik
bu cümleyi yalanladı:

    ops/olcum.py olay oneri_brifingi_teslim        → OLAY YOK   (ops/oneri_brifingi.py)
    ops/olcum.py olay alarm_backlog_digest_teslim  → OLAY YOK   (ops/alarm_backlog_digest.py)

İkisi de CANLI olay, ikisi de mümkün olan EN DÜZ biçim (`obs.log("literal", …)`). Çözümleyicide
hiçbir eksik YOKTU — `tara()` yalnız `meridian/`i glob'luyordu, `ops/` HİÇ AÇILMIYORDU. Ve
`cozulemeyen` de KIPIRDAMIYORDU: okunmayan dosya ne TOPLAMA ne ÇÖZÜLENE girer, yani "yapısal
çıkarma" onu göremez. Bir tamlık vaadi tam da bu yüzden TEHLİKELİDİR: vaade güvenen okuyucu, sahte
sıfırı KANIT sanar.

DÜZELTİLEN ŞEY DÖRDÜNCÜ DELİK DEĞİL, DELİK ÜRETEN KALIPTIR. Kurulan değişmez:

    ARAÇ TAMLIK İDDİA ETMEZ. HER CEVABIN YANINDA KENDİ KAPSAMINI BEYAN EDER.

Uygulaması: (i) taranan kökler TEK adlandırılmış sabitte (`TARANAN_KOKLER`) — döngü içine gömülü
bir literal değil; (ii) `tara()` GERÇEKTEN girdiği kökleri ve açtığı dosya sayısını sonuçla birlikte
DÖNER (`taranan_kokler`, `taranan_dosya_sayisi`); (iii) CLI kapsam satırını bu DÖNEN değerden basar
— bulgu olsun olmasın HER koşumda; (iv) iki çivi beyanın taramadan sürüklenmesini imkânsız kılar
(`test_BEYAN_EDILEN_KAPSAM_GERCEKTEN_TARANANDIR` iki yönlü dosya-sayısı özdeşliği,
`test_KAPSAM_BEYANI_TARAMAYLA_BIRLIKTE_HAREKET_EDER` tek-kaynak kanıtı).

Üç sınıf ayrı tutulur; UYDURMA YASAĞI aracın KENDİSİNE de uygulanır:
  1. `adlar`       — KESİN çözülmüş literal adlar: düz dize + `obs.ALARM_*` adlandırılmış sabiti
                     + çağrıyı yapan modülün KENDİ modül-seviyesi sabiti (ör. `EVENT = "…"`).
  2. `desenler`    — f-string İSKELETLERİ (ör. `{...}_flag_decayed`) — KESİN AD DEĞİL, bir arama
                     deseni; kesin adla karıştırılırsa uydurma olur.
  3. `cozulemeyen` — ÇIKARMA ile türetilmiş SAYI (yukarıya bak). SESSİZCE YUTULMAZ — hem
                     `tara()` ile PROGRAMATİK olarak hem CLI çıktısında her koşumda raporlanır.
  4. `ayristirilamayan_dosya` — AÇILAN ama `ast.parse`ı düşen dosya sayısı (fix round 5). Böyle
                     bir dosya kapsam sayısına GİRER ama çağrıları ne toplama ne çözülene girer:
                     yapısal çıkarma onu göremez, o yüzden AYRI sayılır ve ayrı beyan edilir.

Alt komutlar:
    olay <desen>       kaynaktaki GERÇEK olay adlarını (+ f-string desenlerini) listeler

KAPSAM (ölçülmüş, 2026-08-29 — bkz. `TARANAN_KOKLER`): `meridian/` + `ops/`. `ops/` üretim
kodudur ve GERÇEKTEN olay basar (`oneri_brifingi_teslim`, `alarm_backlog_digest_teslim`,
`plan_geri_dolduruldu`). BİLEREK DIŞARIDA bırakılanlar, gerekçeleriyle: `tests/` (63 çağrı yeri —
`x_event`, `y_event`, `a`, `b`, `garip`, `BİLİNMEYEN_TOKEN` gibi UYDURULMUŞ fikstür adları; içeri
alınsaydı araç uydurma ad üretirdi, tam da yasakladığı şey), `mutants/` (mutmut'ın MUTASYONA
UĞRATILMIŞ kopyası — sahte adlar), `research/olcumler/.../sandbox/meridian/` (2026-08-12
tarihli DONMUŞ anlık görüntü — bayat adlar), `.superpowers/.../_oncesi/` (bir dosyanın
değişiklik-öncesi kopyası), `backups/`. Bu bir TAMLIK iddiası değil bir SINIR beyanıdır: bu
köklerin dışında basılan bir olayı araç GÖRMEZ ve göremediğini SÖYLER.

KAPSAM DOSYA TÜRÜYLE DE SINIRLI (ölçülmüş, 2026-08-29): yalnız `TARANAN_DOSYA_DESENI` (= `*.py`).
`ops/keepalive.sh:46` CANLI bir alarmı KABUKTAN basıyor — `python -c "from meridian import obs;
obs.alarm('MECHANISM_STALE', …)"`. Dosya `ops/` ALTINDA ama `.py` DEĞİL, dolayısıyla açılmaz ve
hiçbir sayaca düşmez. Bu somut örnekte ad yine bulunur (`MECHANISM_STALE` hem `obs.py` jetonu hem
`meridian/` içinde düzinelerce çağrı yeri), ama SINIF gerçektir. Bu yüzden beyan çıplak dizin adı
DEĞİL, `meridian/**/*.py` biçiminde DESEN basar: "ops/" demek "ops/ altındaki her şey" diye
okunurdu ve bu, tam da kaldırılan tamlık imasının küçük hâli olurdu.

YAGNI: "bu artefaktı kim okuyor" sorusunu `codelaw` ZATEN cevaplıyor; ikinci bir sarmalayıcı
ikinci bir gerçek olurdu. Statik çözümleme yalnız İKİ kaynağı bilir:
(a) `obs.py`nin kendi `ALARM_*` jetonları, (b) çağrı yerinin KENDİ dosyasındaki modül-seviyesi
sabit. BİLEREK YAPILMAYAN şey: INTERPROCEDURAL çözümleme (bir fonksiyon parametresinin
çağıranlar zincirinde hangi literale indiğini takip etmek, ör. `obs.log(olay, …)`) VE başka bir
dosyada tanımlı, `obs` OLMAYAN bir isme takılı sabite erişim (ör. `from . import broker as BR`
sonrası `obs.log(BR.EV_GAP_VETO, …)` — `BR`, `obs`a bağlı değil, bu yüzden argüman çözülmez).
İkisi de `cozulemeyen`e düşer (ÇIKARMA sayesinde otomatik — elle eklenmesi GEREKMEZ).

NOT (ölçülmüş): `from __future__ import annotations` BİLEREK KULLANILMIYOR. `OlayTarama`
dataclass'ı + bu betiğin test sarmalayıcısının yükleme biçimi (`spec_from_file_location` +
`exec_module`, `sys.modules`e KAYIT OLMADAN) bir araya gelince, ertelenmiş (string) tip
ipuçları CPython'ın dataclass iç kodunda `sys.modules[cls.__module__]`i arayıp `None` bulduğu
için `AttributeError` fırlatıyor (izole tekrarla doğrulandı). Python 3.12 zaten `dict[str,str]`,
`frozenset[str]`, `X | None` sözdizimini ERTELEMEDEN çalışma zamanında çözer — bu dosyanın
hedef çalışma zamanı (`.venv` = 3.12.7) için bu import gereksiz VE bu belirli yükleme biçiminde
zarar verici. (Bu betiğin test dosyası DIŞINDAKİ ~15 test dosyasında da aynı yükleme biçimi var;
o genel kırılganlık BİLEREK bu görevin kapsamı dışında bırakıldı — koordinatör ayrı bir kalem
olarak kaydetti.)
"""

import argparse
import ast
import dataclasses
import pathlib
import sys

KOK = pathlib.Path(__file__).resolve().parent.parent

# TARANAN KÖKLER — TEK KAYNAK, TEK ADLANDIRILMIŞ SABİT. Hem taramanın YÜRÜDÜĞÜ yer hem CLI'ın
# BEYAN ETTİĞİ kapsam BURADAN gelir. Döngünün içine gömülü bir literal olsaydı (round 1-3'te
# öyleydi: `(kok / "meridian").rglob(...)`) kapsam gizli kalırdı ve beyan ondan sürüklenirdi.
# Neden bu ikisi ve neden ötekiler değil: modül docstring'indeki "KAPSAM" bölümü.
TARANAN_KOKLER: tuple[str, ...] = ("meridian", "ops")

# TARANAN DOSYA DESENİ — beyanın DİZİN adında bitmemesi için ayrı bir sabit. ÖLÇÜLMÜŞ BEŞİNCİ
# DELİK SINIFI: `ops/keepalive.sh:46` CANLI bir alarmı kabuktan basıyor
# (`python -c "from meridian import obs; obs.alarm('MECHANISM_STALE', …)"`). Dosya `ops/`
# ALTINDA ama `.py` DEĞİL — araç onu açmaz. "kapsam: ops/" demek "ops/ altındaki her şey" diye
# okunur; çıplak dizin adı BAŞLI BAŞINA bir tamlık imasıdır. Hem `rglob` hem beyan bu sabiti
# kullanır. (Bu somut örnekte ad yine bulunur — `MECHANISM_STALE` obs.py jetonu ve `meridian/`
# içinde düzinelerce `.py` çağrı yeri var — ama SINIF gerçektir: yalnız kabuktan basılan bir ad
# sahte sıfır verirdi ve hiçbir sayaca düşmezdi.)
TARANAN_DOSYA_DESENI = "*.py"

# obs'un GERÇEK yayım yüzeyi `log`/`warn`/`alarm` (meridian/obs.py; `error` ADI YOK — liste
# BİLEREK geniş: ileride eklenirse sessizce kaçırılmasın. Fazlalığın bedeli, obs'la ilgisiz
# `np.log`/`ap.error` çağrılarının `cozulemeyen`e karışmasıdır — belirsizliği FAZLA beyan etmek
# DOĞRU yöndeki hatadır.)
OBS_METOTLARI = frozenset({"log", "warn", "error", "alarm"})


@dataclasses.dataclass(frozen=True)
class OlayTarama:
    """Tarama sonucu ayrılır ve BİRİ ÖTEKİNİN yerine geçmez: bir f-string İSKELETİNİ kesin ad
    sanmak da, çözülemeyen bir çağrıyı sessizce yutmak da UYDURMA YASAĞI'nı ihlal eder.

    `cozulemeyen` bir ENUMERASYON DEĞİL, ÇIKARMADIR: `toplam_cagri_sayisi − çözülenler`. Bu
    yüzden `toplam_cagri_sayisi` da PUBLIC alandır — sayacın nasıl türediğini denetleyebilmek
    için (bkz. modül docstring'i, fix round 2).

    `taranan_kokler`/`taranan_dosya_sayisi` sonucun KAPSAMIDIR ve sonuçla BİRLİKTE taşınır
    (fix round 4): üç sayının hiçbiri kendi başına anlamlı değildir — "0 bulundu" ile "0 bulundu,
    şuraya bakarak" farklı iki cümledir, ve İKİNCİSİ dürüst olandır. Bu iki alan tarama SIRASINDA
    GERÇEKTEN girilen dizinlerden/açılan dosyalardan ölçülür; `TARANAN_KOKLER`in kopyası DEĞİLDİR
    (var olmayan bir kök beyana GİRMEZ).

    `ayristirilamayan_dosya` (fix round 5) round-4'ün arızasının DOSYA granülerliğindeki hâlini
    kapatır: `SyntaxError` veren bir dosya `taranan_dosya_sayisi`na SAYILIR (kapsam satırı onu
    "taradım" diye beyan eder) ama çağrıları NE `toplam_cagri_sayisi`na NE çözülenlere girer —
    yani "hiçbir kovaya düşmeyen" tam o şekil, ve yapısal ÇIKARMA onu göremez. Bu yüzden AYRI
    sayılır ve `cozulemeyen` gibi HER koşumda beyan edilir."""
    adlar: frozenset[str]
    desenler: frozenset[str]
    cozulemeyen: int
    toplam_cagri_sayisi: int
    taranan_kokler: tuple[str, ...]
    taranan_dosya_sayisi: int
    ayristirilamayan_dosya: int


def _modul_sabitleri(agac: ast.Module) -> dict[str, str]:
    """Modülün SEVİYESİNDEKİ (fonksiyon/sınıf İÇİNDE değil) `AD = "dize"` atamalarını çıkarır.
    `meridian/sermaye.py`deki `EVENT = "paper_equity_reset"` gibi çağrı-yeri sabitlerini VE
    `meridian/obs.py`deki `ALARM_MIRROR_DRIFT = "MIRROR_DRIFT"` gibi jetonları çözmek için."""
    sabitler: dict[str, str] = {}
    for dugum in agac.body:
        hedefler: list[ast.expr] = []
        deger: ast.expr | None = None
        if isinstance(dugum, ast.Assign):
            hedefler, deger = dugum.targets, dugum.value
        elif isinstance(dugum, ast.AnnAssign) and dugum.value is not None:
            hedefler, deger = [dugum.target], dugum.value
        else:
            continue
        if (len(hedefler) == 1 and isinstance(hedefler[0], ast.Name)
                and isinstance(deger, ast.Constant) and isinstance(deger.value, str)):
            sabitler[hedefler[0].id] = deger.value
    return sabitler


def _obs_takma_adlari(agac: ast.Module) -> set[str]:
    """Modülün `obs`u BAĞLADIĞI yerel adları çıkarır: `from . import obs [as X]`,
    `from meridian import obs [as X]`, `import meridian.obs as X`. HARD-CODE EDİLMİŞ bir takma
    ad listesi YOK — bağlama modülün KENDİ import ifadelerinden türetilir (ölçülmüş, fix round
    2: bu depoda `_obs`, `_o`, `_o2`, `_obs_h`, `_obs0`, `_obsL`, `_od`, `_os2` DAHİL 44 çağrı
    yeri bu yolla bağlanıyor). `ast.walk` kullanılır — yalnız üst seviye DEĞİL, çünkü ölçülen
    YAYGIN kalıp yedek importu bir `except` bloğunun İÇİNE koyuyor."""
    adlar: set[str] = set()
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.ImportFrom):
            for al in dugum.names:
                if al.name == "obs":
                    adlar.add(al.asname or al.name)
        elif isinstance(dugum, ast.Import):
            for al in dugum.names:
                if al.name == "obs" and al.asname:
                    adlar.add(al.asname)
                elif al.name == "obs" and not al.asname:
                    adlar.add("obs")
                elif al.name.endswith(".obs") and al.asname:
                    adlar.add(al.asname)
                # `import meridian.obs` (asname YOK) → yerel ad `meridian` PAKET KÖKÜdür;
                # bare-Name alıcı biçimimizle eşleşmez (`meridian.obs.x` bir Attribute-of-
                # Attribute'tır) — bu depoda zaten kullanılmayan bir biçim, bilerek atlanır.
    return adlar


def _fstring_iskeleti(dugum: ast.JoinedStr) -> str:
    """`f"{prefix}_flag_decayed"` → `"{...}_flag_decayed"` — yer tutucu GÖRÜNÜR işaretlenir,
    kesin ad değil arama deseni olduğu açık kalsın diye."""
    parcalar: list[str] = []
    for deger in dugum.values:
        if isinstance(deger, ast.Constant) and isinstance(deger.value, str):
            parcalar.append(deger.value)
        else:
            parcalar.append("{...}")
    return "".join(parcalar)


def _cagri_ilk_arg(
    cagri: ast.Call,
    yerel_sabitler: dict[str, str],
    obs_sabitler: dict[str, str],
    obs_takma_adlari: set[str],
) -> tuple[str, str] | None:
    """İlk konumsal argümanı çözer. Dönüş: ("ad", değer) | ("desen", iskelet) | None (çözülemedi).

    Dört sınıf (ölçülmüş, 2026-08-29):
      1. Düz dize literali                    → ("ad", değer)
      2. `<obs-takma-adı>.ALARM_XXX` sabiti    → ("ad", obs.py'deki değeri)   — ÇİFT dolaylı
                                                  olabilir: hem ALICI hem ARGÜMAN takma adlı.
      3. Çağrıyı yapan modülün KENDİ modül-seviyesi sabiti (bare `EVENT`) → ("ad", değeri)
      4. f-string                             → ("desen", iskelet)
      Bunların hiçbirine uymayan (ör. bir fonksiyon parametresi, ya da başka-dosya takma-adlı
      bir sabit) → None — ÇÖZÜLEMEDİ, çağıran taraf bunu ÇIKARMAYLA sayar (enumere ETMEZ).
    """
    if not cagri.args:
        return None
    ilk = cagri.args[0]
    if isinstance(ilk, ast.Constant) and isinstance(ilk.value, str):
        return ("ad", ilk.value)
    if isinstance(ilk, ast.JoinedStr):
        return ("desen", _fstring_iskeleti(ilk))
    if (isinstance(ilk, ast.Attribute) and isinstance(ilk.value, ast.Name)
            and ilk.value.id in obs_takma_adlari):
        if ilk.attr in obs_sabitler:
            return ("ad", obs_sabitler[ilk.attr])
        return None
    if isinstance(ilk, ast.Name) and ilk.id in yerel_sabitler:
        return ("ad", yerel_sabitler[ilk.id])
    return None


def tara(kok: pathlib.Path = KOK) -> OlayTarama:
    """`TARANAN_KOKLER`in altındaki `**/*.py`yi STATİK olarak tarar — import YOK, yan etki YOK.

    KAPSAM SONUÇLA BİRLİKTE DÖNER (fix round 4). Kökler döngünün içine gömülü DEĞİL,
    `TARANAN_KOKLER` sabitinden okunur; GERÇEKTEN girilen kökler (`taranan_kokler`) ve GERÇEKTEN
    açılan dosya sayısı (`taranan_dosya_sayisi`) yürüyüş SIRASINDA ölçülüp döndürülür. CLI
    kapsam cümlesini o dönen değerden basar — sabitin ikinci bir kopyasından değil. Bu, beyanın
    taramadan sürüklenmesini yapısal olarak engeller (iki çivi bunu sınar). Listede olan ama
    diskte OLMAYAN bir kök beyana GİRMEZ: "taradım" yalnız gerçekten girilen dizin için söylenir.

    `obs.py`nin
    kendi `ALARM_*` jetonlarını önce çözer; her dosya ayrıca KENDİ import'larından `obs`a
    bağlanan yerel adları VE kendi modül-seviyesi sabitlerini kendi kapsamında çözer.

    `kok` parametresi test edilebilirlik İÇİNDİR (varsayılan: gerçek depo kökü) — sentetik bir
    `tmp_path` ağacı vererek "yapısal ÇIKARMA" özelliğini repo'ya dokunmadan sınamak mümkün olsun
    diye (bkz. `tests/test_olcum_araci_v328.py::test_COZULEMEYEN_YAPISAL_TAMDIR_...`).

    `cozulemeyen` BİR ENUMERASYON DEĞİL: metod adı `log/warn/error/alarm` olan TÜM çağrı
    yerleri ALICIDAN BAĞIMSIZ sayılır (`toplam_cagri`), sonra GERÇEKTEN çözülenler bundan
    ÇIKARILIR. Böylece öngörülmemiş bir alıcı/argüman biçimi de otomatik olarak sayılır."""
    obs_py = kok / "meridian/obs.py"
    assert obs_py.exists(), f"{obs_py} YOK"
    obs_agac = ast.parse(obs_py.read_text(encoding="utf-8", errors="ignore"), filename=str(obs_py))
    obs_sabitler = _modul_sabitleri(obs_agac)

    adlar: set[str] = set()
    desenler: set[str] = set()
    toplam_cagri = 0
    cozulen_cagri = 0

    girilen_kokler: list[str] = []
    taranan_dosya = 0
    ayristirilamayan = 0

    for kok_adi in TARANAN_KOKLER:
        dizin = kok / kok_adi
        if not dizin.is_dir():
            continue  # var OLMAYAN bir kökü "taradım" diye BEYAN ETME (beyan ölçümdür, niyet değil)
        girilen_kokler.append(kok_adi)
        for yol in sorted(dizin.rglob(TARANAN_DOSYA_DESENI)):
            taranan_dosya += 1  # AÇILAN dosya — parse düşse bile bakıldı, beyan bunu sayar
            kaynak = yol.read_text(encoding="utf-8", errors="ignore")
            try:
                agac = ast.parse(kaynak, filename=str(yol))
            except SyntaxError:
                # Tek dosyanın parse hatası tüm taramayı düşürmemeli — ama SESSİZCE ATLANAMAZ
                # (fix round 5). Atlanan dosya `taranan_dosya`ya SAYILDI, yani kapsam satırı onu
                # "taradım" diye beyan ediyor; içindeki çağrılar ise ne toplama ne çözülene
                # giriyor — round-4'ün "hiçbir kovaya düşmeyen dosya" arızasının birebir aynısı,
                # bu kez dosya granülerliğinde. Bu yüzden AYRI sayılır ve her koşumda beyan edilir.
                ayristirilamayan += 1
                continue
            yerel_sabitler = _modul_sabitleri(agac)
            obs_takma_adlari = _obs_takma_adlari(agac)
            for dugum in ast.walk(agac):
                if not isinstance(dugum, ast.Call):
                    continue
                f = dugum.func
                if not (isinstance(f, ast.Attribute) and f.attr in OBS_METOTLARI):
                    continue
                toplam_cagri += 1  # ALICI FARK ETMEKSİZİN — metod adı eşleşen HER çağrı yeri
                if not (isinstance(f.value, ast.Name) and f.value.id in obs_takma_adlari):
                    continue  # obs'a bağlı değil → çözülmez, ama YUKARIDA zaten SAYILDI
                sonuc = _cagri_ilk_arg(dugum, yerel_sabitler, obs_sabitler, obs_takma_adlari)
                if sonuc is None:
                    continue  # obs'a bağlı ama biçim tanınmadı → YUKARIDA zaten SAYILDI
                cozulen_cagri += 1
                tur, deger = sonuc
                if tur == "desen":
                    desenler.add(deger)
                else:
                    adlar.add(deger)

    return OlayTarama(
        adlar=frozenset(adlar),
        desenler=frozenset(desenler),
        cozulemeyen=toplam_cagri - cozulen_cagri,
        toplam_cagri_sayisi=toplam_cagri,
        taranan_kokler=tuple(girilen_kokler),
        taranan_dosya_sayisi=taranan_dosya,
        ayristirilamayan_dosya=ayristirilamayan,
    )


def kapsam_beyani(t: OlayTarama) -> str:
    """Kapsam cümlesini TARAMANIN KENDİ SONUCUNDAN üretir — elle yazılmış bir kök listesinden
    DEĞİL. Poka-yoke (fix round 4): `TARANAN_KOKLER` değişince bu cümle kendiliğinden değişir.
    Cümle ayrı bir yerde tutulsaydı, biri güncellenip diğeri unutulurdu — round 1-3'ün tam
    kalıbı: mekanizma düzeltildi, İDDİA eski kaldı."""
    if not t.taranan_kokler:
        return "HİÇBİR KÖK TARANMADI — sonuç GEÇERSİZ, boşluğu 'bulunamadı' diye OKUMA"
    return (", ".join(f"{k}/**/{TARANAN_DOSYA_DESENI}" for k in t.taranan_kokler)
            + f" ({t.taranan_dosya_sayisi} dosya) — BU KAPSAMIN DIŞI GÖRÜLMEDİ; "
              "sıfır sonuç 'yok' değil 'BU KAPSAMDA bulunamadı' demektir")


def olay_adlari(desen: str = "") -> list[str]:
    """Kaynakta GERÇEKTEN basılan olay adları + f-string arama desenleri; `desen` alt-dizge
    süzgecidir (boş = hepsi). ÇÖZÜLEMEYEN sayısı BURADA YOKTUR (bu fonksiyon geriye-uyumluluk
    için düz bir liste döner) — onu görmek için `tara().cozulemeyen`i kullan. Boş dönüş TEK
    BAŞINA 'olay yok' KANITI DEĞİLDİR: hem statik çözümleyicinin bir kör noktası var, hem de
    sonuç `TARANAN_KOKLER` KAPSAMIYLA sınırlıdır — kapsamı görmek için `tara().taranan_kokler`
    (CLI her koşumda basar). Bu fonksiyon düz bir liste döndüğü için kapsamı TAŞIYAMAZ; kapsam
    beyanı gereken yerde `tara()`yi doğrudan çağır."""
    t = tara()
    d = desen.lower()
    return sorted(a for a in (t.adlar | t.desenler) if d in a.lower())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    alt = ap.add_subparsers(dest="komut", required=True)
    a1 = alt.add_parser("olay", help="gerçek olay adlarını (+ f-string desenlerini) listele")
    a1.add_argument("desen", nargs="?", default="")
    args = ap.parse_args(argv)

    t = tara()
    d = args.desen.lower()
    eslesen = sorted(a for a in (t.adlar | t.desenler) if d in a.lower())

    if not eslesen:
        print(
            f"'{args.desen}' desenine uyan OLAY YOK — TARANAN KAPSAM İÇİNDE. Bu ÜÇ şeyden biri "
            f"demektir: (1) böyle bir olay gerçekten yok — aranan bir ALAN adı olabilir; "
            f"(2) ad çalışma zamanında kuruluyor ve statik çözümleyici onu ÇÖZEMEDİ; "
            f"(3) olay kapsamın DIŞINDA bir dosyada basılıyor — araç oraya HİÇ BAKMADI. "
            f"Boş liste TEK BAŞINA 'arıza yok' KANITI DEĞİLDİR — aşağıdaki İKİ satıra bak."
        )
        cikis = 1
    else:
        for a in eslesen:
            print(a)
        cikis = 0
    # HER koşumda, bulgu olsun olmasın: önce NEREYE bakıldı, sonra orada NE çözülemedi. Boş
    # sonuç + görünür kapsam DÜRÜSTTÜR; boş sonuç + tamlık iması ARIZANIN KENDİSİDİR.
    print(f"# taranan kapsam: {kapsam_beyani(t)}")
    print(f"# çözülemeyen çağrı yeri: {t.cozulemeyen} (ad çalışma zamanında belirleniyor)")
    print(f"# ayrıştırılamayan dosya: {t.ayristirilamayan_dosya} (açıldı ve kapsam sayısına "
          f"girdi ama parse EDİLEMEDİ — içindeki çağrılar hiçbir sayaca düşmedi)")
    return cikis


if __name__ == "__main__":
    sys.exit(main())
