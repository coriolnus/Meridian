#!/usr/bin/env python3
"""defter_ozeti_retain.py — GÜNLÜK DEFTER ÖZETİNİ Hindsight bankasına RETAIN eder (TSK-168).

KART: `research/cards/EDG-2026-089-hindsight-retain-akisi-yeni-pencere.yaml`. Kartın hipotezi
(i) şudur: harness'in HER GÜN yazdığı ve bankaya retain ettiği bir defter özeti bankayı büyütür
ve zihin modeli sayfaları ancak banka BÜYÜRKEN tazelenir (EDG-083/EDG-080-K2'nin "girdisiz banka"
dersi). Bu betik o akışın ÜRETİCİ ucudur.

BELGEYİ MODEL ÜRETMEZ — HARNESS ÜRETİR. Her sayı bir defterden okunur ve YANINDA kaynak yolu
yazılır; hiçbir satır özetlenmez, hiçbir sayı tahmin edilmez (kartın kill-list'i: "özet belgeyi
bir model üretirse ya da bir sayı defterden değil elle/tahminle yazılırsa → GEÇERSİZ"). Ölçülemeyen
alan `None` + NEDEN ile yazılır: sıfır ile "bilmiyorum" aynı şey değildir (uydurma yasağı).

SÖZLEŞME KOMUT SATIRIDIR (`main()` değil — CLAUDE.md §1, 2026-08-30 vakası):

    ops/defter_ozeti_retain.py --kuru   [--gun YYYY-MM-DD] [--kok YOL]
    ops/defter_ozeti_retain.py --uygula [--gun …] [--taban-url …] [--banka …] [--kok YOL]

    --kuru    belgeyi stdout'a basar; HİÇBİR HTTP çağrısı YAPMAZ ve deftere HİÇBİR olay yazmaz
              (kuru koşum K1 kadans sayımını şişiremez).
    --uygula  idempotens kapısı (GET documents/{id}) + retain (POST memories).
    --kok     `state/` ve `research/cards/` köklerini VERİLEN ağaca çevirir (çiviler `sandbox_state`
              ile aynı tmp ağacını verir). Verilmezse canlı `config` yolları kullanılır.

ÇIKIŞ KODLARI — ÜÇ SINIF, ÜÇ SAYI:
    0  retain edildi
    2  o günün belgesi bankada ZATEN VAR (idempotent; bir HATA DEĞİL)
    1  hata — sebep ADIYLA stderr'e (anahtar yok · GET/POST düştü · kip bayrağı çelişkili)

BEDEL (bedel yasası): günde bir belge (≤ `BELGE_TAVANI` karakter) bankaya girer; upstream retain
yolu kendi çıkarımını koşar (kota kolonu kartın `olcum_plani` son maddesinde ölçülür). Kazanç,
bankanın her gün BÜYÜMESİ ve sayfaların delta tazelemesinin girdisiz kalmamasıdır.

OKUR: `state/dagitim.json` · `state/trades.jsonl` · `state/portfolio.json` · `state/events.jsonl`
· `state/entry_execution.jsonl` · `research/cards/*.yaml` · gölge defteri (ithal özet).
YAZAR: `state/events.jsonl` (tek olay: `defter_ozeti_retain`). YENİ BİR `state/` DOSYASI AÇMAZ —
olayın okuyucusu EDG-089'un K1 sayımı ve bekçi brifinginin jenerik `durum:` yoludur (Yasa 6).

SIR DİSİPLİNİ: anahtar YALNIZ `Authorization` başlığında taşınır (URL'e/query'ye asla girmez),
hiçbir log/olay/çıktı satırına yazılmaz ve HER hata metni `_maskele`den geçer. Belgenin TAMAMI
`notify.scrub` süzgecinden geçer — kartın kill#3'ü: süzgeç atlanırsa akış KAPATILIR.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter

import yaml

# ops/ altından doğrudan koşulduğunda `meridian` paketi ve kardeş `ops` modülleri bulunabilsin.
# Kardeş betiklerin hepsi bu satırı taşır ve hepsi systemd'den koşar: bootstrap yalnız bazılarında
# olsaydı yeniden kurulmuş/bozulmuş bir .venv kadansın bir kısmını öldürür, kalanı çalışmaya
# devam ederdi — teşhisi en zor arıza şekli.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from meridian import config, notify, obs, secrets, storage, store   # noqa: E402
from ops import karne_hesap as _karne_hesap                         # noqa: E402
from ops import kart_endeksi_uret as _kart_endeksi                  # noqa: E402

# ---- SÖZLEŞME SABİTLERİ ------------------------------------------------------------------------
#: Hindsight tabanı ve credential kimliği pano vekilinin (`meridian/api.py`) okuduğu değerlerin
#: KOPYASIDIR ve bu bilinçlidir: bir `Type=oneshot` birim, iki sabiti okumak için FastAPI
#: uygulamasının TAMAMINI ithal edemez. Kopya kaçınılmaz olduğunda tek-kaynak yasasının reçetesi
#: AYRIŞMA ÇİVİSİdir — `tests/test_defter_ozeti_retain_v464.py` ikisini `api`nin sabitleriyle
#: EŞİTLER; taban ya da kimlik bir gün değişirse çivi öter, akış sessizce yanlış uca gitmez.
TABAN_URL_VARSAYILAN = "http://127.0.0.1:8888"
BANKA_VARSAYILAN = "meridian-arsiv"
KRED_ADI = "HINDSIGHT_API_TENANT_API_KEY"

#: Belge tavanı. Kartın `olcum_plani` ilk maddesinin SÖZLEŞMESİ ("≤4.000 karakter Markdown").
BELGE_TAVANI = 4000
#: Kesme beyanı — SESSİZ kesme bedel yasasının yasakladığı hâldir: kaç karakterin düştüğü yazılır.
KESIK_SABLONU = "\n… [KESİLDİ: belge {ham} karakterdi, tavan {tavan} — {kayip} karakter düştü]\n"

#: Alarm SINIF adının tavanı. `event` bacağı jeton+mesaj taşır ve mesaj uzun olabilir; sınırsız
#: bırakmak tek bir uzun alarmın belgenin geri kalanını tavanın dışına itmesi demekti. Kesik `…`
#: ile GÖRÜNÜR olur (gizli normalizasyon yok). Sayı ÖLÇÜLMEDİ, SEÇİLDİ.
ALARM_SINIF_SINIRI = 80
#: En çok kaç alarm sınıfı basılır (brief sözleşmesi). Gösterilmeyen sınıf sayısı AYRICA yazılır.
ALARM_SINIF_TAVANI = 8
#: Kart hüküm cümlesinin tavanı (brief sözleşmesi: ilk 160 karakter).
KART_HUKUM_SINIRI = 160

#: HTTP zaman aşımı (saniye). ÖLÇÜLMEDİ, SEÇİLDİ: birimin `TimeoutStartSec=300` tavanının çok
#: altında kalsın ve asılı bir upstream birimi `activating`de dondurup bir sonraki tetiği
#: atlatmasın (TSK-123'ün `meridian-brifing.service`te ölçtüğü arıza sınıfı).
ZAMAN_ASIMI_S = 30.0

OLAY = "defter_ozeti_retain"
BELGE_ONEKI = "meridian-gunluk-ozet-"
BELGE_BAGLAMI = "Meridian günlük defter özeti (harness)"
BELGE_ETIKETLERI = ["meridian", "gunluk-ozet"]
BELGE_KAYNAGI = "ops/defter_ozeti_retain.py"
SON_SATIR = ("Bu belge harness üretimidir; her sayı yanındaki dosyadan okunmuştur "
             "(EDG-2026-089, TSK-168).")

CIKIS_RETAIN = 0
CIKIS_HATA = 1
CIKIS_ZATEN_VAR = 2


# =================================================================================================
# KÖK ÇÖZÜMÜ
# =================================================================================================

def kok_uygula(kok) -> pathlib.Path:
    """`--kok` verilmişse `config` yollarını O ağacın altına çevirir; kart dizinini döner.

    NEDEN `config`i DEĞİŞTİRİR: defterler `store` üzerinden okunur (tek-kaynak — `trades.jsonl` ve
    `portfolio.json` DB'ye göçtü ve dosyayı DOĞRUDAN okuyan bir yol bugün YANLIŞ sayı verirdi) ve
    `store._state()` HER çağrıda `config.STATE`ten türer. Kökü yalnız kendi içinde tutan bir
    çözüm, `store`u canlı `state/`e okutmaya devam ederdi — yani `--kok` bir sandbox İDDİASI olur,
    sandbox OLMAZDI. Aynı üç alanı `tests/conftest.py::sandbox_state` de çevirir; çivi betiğe
    `--kok tmp_path` verip iki yolun AYNI dizini gösterdiğini ölçer."""
    if kok is None:
        return config.ROOT / "research" / "cards"
    kok = pathlib.Path(kok).resolve()
    config.STATE = kok / "state"
    config.HISTORY = config.STATE / "history"
    config.BARS = config.STATE / "bars"
    return kok / "research" / "cards"


def belge_kimligi(gun: str) -> str:
    """Belgenin `document_id`si — idempotens kapısının TEK anahtarı (gün başına bir belge)."""
    return f"{BELGE_ONEKI}{gun}"


def bugun_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


# =================================================================================================
# BÖLÜMLER — her satır `… sayı … (kaynak: <yol>)`
# =================================================================================================

def _dagitim(_gun: str) -> str:
    d = store.read_json("dagitim.json", None) or {}
    sha = d.get("deployed_sha")
    if not sha:
        return ("DAĞITIM: None (state/dagitim.json yok ya da `deployed_sha` taşımıyor — beyanlı "
                "dağıtım okunamadı) (kaynak: state/dagitim.json)")
    ts = d.get("dagitildi_utc") or "None (`dagitildi_utc` alanı yok)"
    return f"DAĞITIM: sha {str(sha)[:7]} · {ts} (kaynak: state/dagitim.json)"


def _kapanis_gunu(islem: dict) -> str | None:
    """Bir işlem satırının KAPANIŞ GÜNÜ. Kural kopyalanmaz, İTHAL edilir: hangi alanın kapanış
    damgası olduğu ve damgasız satırın atlandığı `ops/karne_hesap.py::_kapanis_gunleri`de yazılıdır
    ve karne hükmü de oradan okur. İki yerde ayrı yazılsaydı günlük özet ile karne aynı işlemi
    farklı güne sayabilirdi (tek-kaynak yasası)."""
    gunler = _karne_hesap._kapanis_gunleri([islem])
    return gunler[0] if gunler else None


def _karne(gun: str) -> list[str]:
    islemler = store.read_jsonl(_karne_hesap.DEFTER)
    kaynak = f"(kaynak: state/{_karne_hesap.DEFTER})"
    if not islemler:
        satirlar = [f"KARNE: kapanan işlem None (state/{_karne_hesap.DEFTER} hiç satır taşımıyor — "
                    f"'o gün kapanış yok' ile 'defter yok' AYIRT EDİLEMEZ) {kaynak}"]
    else:
        kapanan = [t for t in islemler if _kapanis_gunu(t) == gun]
        rler = [float(t["r_multiple"]) for t in kapanan if t.get("r_multiple") is not None]
        rsiz = len(kapanan) - len(rler)
        toplam = (f"{sum(rler):+.2f}" if rler else
                  "None (kapanan satırların hiçbirinde `r_multiple` yok)")
        parca = (f"KARNE: kapanan işlem {len(kapanan)} · toplam R {toplam} · "
                 f"kazanan {len([x for x in rler if x > 0])} · "
                 f"kaybeden {len([x for x in rler if x < 0])}")
        if rsiz:
            # Payda BEYANLI: R'si olmayan satır toplamın dışındadır ve bunu söylemeyen bir toplam,
            # eksik örneklemi tam gibi gösterirdi.
            parca += f" · R'siz satır {rsiz} (toplamın DIŞINDA)"
        satirlar = [f"{parca} {kaynak}"]

    pf = store.read_json(storage.PORTFOLIO, None)
    pf_kaynak = f"(kaynak: state/{storage.PORTFOLIO})"
    if pf is None:
        satirlar.append(f"KARNE: açık pozisyon None (state/{storage.PORTFOLIO} yok) {pf_kaynak}")
    elif "positions" not in pf:
        satirlar.append(f"KARNE: açık pozisyon None (`positions` alanı yok) {pf_kaynak}")
    else:
        satirlar.append(f"KARNE: açık pozisyon {len(pf.get('positions') or {})} {pf_kaynak}")
    return satirlar


def _status_blogu(ham: str) -> str:
    """`status:` satırı + hemen altındaki `#` yorum bloğu — kart hükmünün YAZILDIĞI yer.

    Hüküm METNİNİ `ops/kart_endeksi_uret.py::hukum_metni` üretir (ithal edilir); burada sorulan
    soru başkadır: "bu blok BUGÜNÜN tarihini taşıyor mu?". Aynı bloğun iki farklı sorusu olduğu
    için metin burada yeniden ÇIKARILIR, hüküm cümlesi KOPYALANMAZ."""
    satirlar = ham.split("\n")
    for i, satir in enumerate(satirlar):
        if not satir.startswith("status:"):
            continue
        blok = [satir]
        for devam in satirlar[i + 1:]:
            if not devam.startswith("#"):
                break
            blok.append(devam)
        return "\n".join(blok)
    return ""


def _kart_gunu_tasiyor(ham: str, kart: dict, gun: str) -> bool:
    """Kart O GÜN hüküm aldı mı? İki bağımsız işaret (biri ölçmezse öteki ölçsün):
      · `status:` satırı ya da onun yorum bloğu günü taşıyor,
      · `hukum_*` anahtarlarından biri günü taşıyor, ya da bir anahtar ADI günün alt-çizgili
        biçimiyle (`…_2026_09_12`) bitiyor."""
    if gun in _status_blogu(ham):
        return True
    gun_alt = gun.replace("-", "_")
    for anahtar, deger in (kart or {}).items():
        ad = str(anahtar)
        if ad.endswith(gun_alt):
            return True
        if ad.startswith("hukum_") and gun in str(deger):
            return True
    return False


def _kartlar(gun: str, kart_dizini: pathlib.Path) -> list[str]:
    kaynak_koku = "research/cards"
    if not kart_dizini.is_dir():
        return [f"KART HÜKÜMLERİ: None ({kaynak_koku} dizini yok — kart taraması YAPILAMADI) "
                f"(kaynak: {kaynak_koku}/)"]
    # Kart alanlarının okunması İTHALDİR (`card_id`/`status`/hüküm cümlesi tek kaynaktan gelir);
    # ham metin yalnız GÜN sorusu için ikinci kez okunur.
    kayitlar = {k["dosya"]: k for k in _kart_endeksi.kartlari_oku(kart_dizini)}
    secilen = []
    for ad, kayit in sorted(kayitlar.items()):
        ham = (kart_dizini / ad).read_text(encoding="utf-8")
        kart = yaml.safe_load(ham)
        if not _kart_gunu_tasiyor(ham, kart if isinstance(kart, dict) else {}, gun):
            continue
        hukum = (kayit["hukum"] or "")[:KART_HUKUM_SINIRI]
        secilen.append(f"- {kayit['card_id']} · {kayit['status']} · {hukum} "
                       f"(kaynak: {kaynak_koku}/{ad})")
    if not secilen:
        return [f"KART HÜKÜMLERİ (0): bugün hüküm alan kart yok ({len(kayitlar)} kart tarandı) "
                f"(kaynak: {kaynak_koku}/)"]
    return [f"KART HÜKÜMLERİ ({len(secilen)}):", *secilen]


def _alarm(gun: str) -> str:
    olaylar = store.read_jsonl(obs._EVENTS)
    kaynak = f"(kaynak: state/{obs._EVENTS})"
    if not olaylar:
        return (f"ALARM: None (state/{obs._EVENTS} hiç satır taşımıyor — 'alarm yok' ile 'defter "
                f"yok' AYIRT EDİLEMEZ) {kaynak}")
    gunun = [r for r in olaylar
             if r.get("level") == "alarm" and str(r.get("ts") or "")[:10] == gun]
    if not gunun:
        return f"ALARM (0): o gün alarm satırı yok {kaynak}"
    sayac = Counter(str(r.get("alarm") or r.get("event") or "?")[:ALARM_SINIF_SINIRI]
                    for r in gunun)
    gosterilen = sayac.most_common(ALARM_SINIF_TAVANI)
    metin = " · ".join(f"{ad} {n}" for ad, n in gosterilen)
    artan = len(sayac) - len(gosterilen)
    if artan:
        metin += f" · (+{artan} sınıf gösterilmedi)"
    return f"ALARM ({len(gunun)}): {metin} {kaynak}"


def _donusum(gun: str) -> str:
    from meridian import analytics          # dosya konvansiyonu: dar kullanımlı import fonksiyonda
    defter = analytics.ENTRY_LEDGER
    kaynak = f"(kaynak: state/{defter})"
    satirlar = store.read_jsonl(defter)
    if not satirlar:
        return (f"DÖNÜŞÜM (EXE-011): None (state/{defter} hiç satır taşımıyor — 'o gün karar yok' "
                f"ile 'defter yok' AYIRT EDİLEMEZ) {kaynak}")
    gunun = [r for r in satirlar if str(r.get("date") or "") == gun]
    dolum = len([r for r in gunun if r.get("fill") is not None])
    ayna = len([r for r in gunun if r.get("motor") == "ayna"])
    return (f"DÖNÜŞÜM (EXE-011): karar satırı {len(gunun)} · dolum {dolum} · ayna-satırı {ayna} "
            f"{kaynak}")


def _golge() -> str:
    kaynak = "(kaynak: meridian/golge_icra.py::ozet)"
    try:
        from meridian import golge_icra     # dosya konvansiyonu: dar kullanımlı import fonksiyonda
        o = golge_icra.ozet()
    except Exception as e:
        # sessiz-yutma: gölge özeti bu belgenin ZORUNLU parçası değildir; ölçülemezse sınıfıyla
        # birlikte `None` yazılır ve belgenin geri kalanı yine teslim edilir — bir tanı kolunun
        # düşmesi günlük kadansı düşüremez (Yasa 4 sinyali: sebep BELGEYE çıkar).
        return f"GÖLGE PİLOT (EDG-088): None ({type(e).__name__}: {e}) {kaynak}"
    return (f"GÖLGE PİLOT (EDG-088): n {o.get('n')} · n_acik {o.get('n_acik')} · "
            f"son_seans {o.get('son_seans')} {kaynak}")


# =================================================================================================
# BELGE
# =================================================================================================

def tavana_sigdir(metin: str) -> str:
    """Belgeyi `BELGE_TAVANI`na indirir. SON SATIR (kaynak beyanı) HER ZAMAN hayatta kalır ve
    kesme ADIYLA beyan edilir — sessiz kesme, kaybı ölçmeden kazanç saymak olurdu."""
    if len(metin) <= BELGE_TAVANI:
        return metin
    kuyruk = "\n" + SON_SATIR + "\n"
    govde = metin[: -len(kuyruk)] if metin.endswith(kuyruk) else metin
    # Kesik beyanı sabit uzunlukta değildir (kayıp sayısı içinde geçer); iki geçişte kurulur:
    # önce kaba bir bütçeyle kesilir, sonra beyan nihai uzunlukla yeniden yazılır.
    beyan = KESIK_SABLONU.format(ham=len(metin), tavan=BELGE_TAVANI, kayip=0)
    butce = BELGE_TAVANI - len(kuyruk) - len(beyan) - 8
    kesilmis = govde[:max(butce, 0)]
    beyan = KESIK_SABLONU.format(ham=len(metin), tavan=BELGE_TAVANI,
                                 kayip=len(govde) - len(kesilmis))
    return (kesilmis + beyan + kuyruk)[:BELGE_TAVANI]


def belge_uret(gun: str, kok=None) -> str:
    """Günün defter özeti — Markdown, ≤`BELGE_TAVANI` karakter, SÜZGEÇTEN geçmiş.

    SIRA SÖZLEŞMEDİR (kart `olcum_plani` ilk maddesi): başlık · dağıtım · karne · kart hükümleri ·
    alarm · dönüşüm · gölge pilot · kaynak beyanı."""
    kart_dizini = kok_uygula(kok)
    bolumler: list[str] = [
        f"# Meridian günlük defter özeti — {gun} (harness, sayılar defterden)",
        "",
        _dagitim(gun),
        *_karne(gun),
        *_kartlar(gun, kart_dizini),
        _alarm(gun),
        _donusum(gun),
        _golge(),
        "",
        SON_SATIR,
        "",
    ]
    # SÜZGEÇ TEK BOĞAZDAN, EN SONDA: bölüm bölüm süzmek, birleştirme sırasında eklenen bir metnin
    # süzgecin DIŞINDA kalmasına izin verirdi (kill#3 tek istisna tanımaz).
    return tavana_sigdir(notify.scrub("\n".join(bolumler)))


# =================================================================================================
# HİNDSIGHT UCU
# =================================================================================================

def _maskele(metin: str, sir: str | None) -> str:
    """Hata metninden anahtarı siler. İkinci savunma hattı: anahtar bugün yalnız BAŞLIKTA taşınır,
    ama istisna metni bir gün başlıkları da yazdırırsa sır stderr'e/olaya düşerdi."""
    if sir and len(sir) >= 8:
        return str(metin).replace(sir, "***")
    return str(metin)


def anahtar_coz() -> tuple[str | None, str]:
    """`(anahtar, kaynak-ya-da-neden)`. Sıra: systemd credential → `secrets.get` alt kanalı.

    CREDENTIAL ÖNCE, ve okuyucu İTHAL edilir (`secrets.credential_oku`): biçim toleransı (`AD=`
    öneki, kırpma, boş=None) tek kaynaktadır. Alt kanal (`secrets.get`) env ve `state/secrets.json`
    basamaklarını da dener — A1'de bu ad ORADA YOKTUR, ama operatörün yerel kuru koşumunu
    imkânsız kılmamak için zincir kapatılmaz. HİÇBİRİ yoksa SESSİZ DÜŞÜŞ YOK: anahtarsız bir POST
    401 alır ve 'retain denendi' gibi görünürdü."""
    kred = secrets.credential_oku(KRED_ADI)
    if kred:
        return kred, "credential"
    alt = secrets.get(KRED_ADI)
    if alt:
        return alt, "secrets.get (env/dosya)"
    kanal = ("credential kanalı var ama bu ad içinde yok"
             if os.environ.get(secrets.CREDENTIAL_DIZIN_ENV)
             else f"credential kanalı yok ({secrets.CREDENTIAL_DIZIN_ENV} ayarlı değil)")
    return None, (f"{KRED_ADI} hiçbir kanalda YOK — {kanal}; `secrets.get` alt kanalı da boş "
                  f"(kurulum: meridian-defter-ozeti-retain.service.d/54-hafiza-credential.conf)")


def _uc(taban: str, banka: str, yol: str) -> str:
    """Banka/belge kimliği PATH'e KAÇIRILARAK girer — kimliği çağıran verir ve kaçırılmamış bir
    kimlik, sözleşmeyi istemcinin insafına bırakırdı (pano vekilinin aynı savunması)."""
    return f"{taban}/v1/default/banks/{urllib.parse.quote(banka, safe='')}{yol}"


def _istek(url: str, anahtar: str, *, govde: bytes | None = None,
           yontem: str = "GET") -> tuple[int | None, bytes | None, str | None]:
    """Tek dış-çağrı boğazı. `(http_kodu, govde, neden)` — `neden` doluysa çağrı BAŞARISIZDIR.
    404 bir HATA DEĞİL bir CEVAPTIR (idempotens kapısının aradığı cevap), o yüzden kodu döner."""
    basliklar = {"Authorization": f"Bearer {anahtar}", "Accept": "application/json"}
    if govde is not None:
        basliklar["Content-Type"] = "application/json"
    istek = urllib.request.Request(url, data=govde, headers=basliklar, method=yontem)
    try:
        with urllib.request.urlopen(istek, timeout=ZAMAN_ASIMI_S) as cevap:
            return getattr(cevap, "status", None), cevap.read(), None
    except urllib.error.HTTPError as e:
        return e.code, None, None if e.code == 404 else _maskele(
            f"{yontem} {url} → HTTP {e.code} {e.reason}", anahtar)
    except Exception as e:
        # sessiz-yutma: ağ yolu URLError/socket.timeout/OSError/ssl.SSLError ve bozuk URL'de
        # ValueError atabilir; sınıf + metin `neden` olarak ÇAĞIRANA döner ve çağıran onu stderr'e
        # basıp çıkış 1 verir — yani sinyal yanıtın kendisidir, yutulan hiçbir şey yoktur.
        return None, None, _maskele(f"{yontem} {url} okunamadı ({type(e).__name__}: {e})", anahtar)


def belge_var_mi(taban: str, banka: str, kimlik: str,
                 anahtar: str) -> tuple[bool | None, str | None]:
    """İDEMPOTENS KAPISI: o günün belgesi bankada VAR MI? `(var_mi, neden)`.

    Kapı BANKAYA sorulur, yerel bir damgaya DEĞİL: yerel damga, belge bankada yokken 'var' diyebilir
    (dosya geri yüklendi) ya da tersi — ve K1 kadansı tam olarak bankadaki belgeyi sayar."""
    kod, _govde, neden = _istek(
        _uc(taban, banka, f"/documents/{urllib.parse.quote(kimlik, safe='')}"), anahtar)
    if neden:
        return None, neden
    return kod != 404, None


def retain_et(taban: str, banka: str, kimlik: str, belge: str,
              gun: str, anahtar: str) -> tuple[str | None, str | None]:
    """RetainRequest gönderir. `(operation_id, neden)` — `neden` doluysa retain OLMAMIŞTIR.

    `async: true`: upstream çıkarımı arka planda koşar; oneshot birim `TimeoutStartSec` duvarına
    upstream'in çıkarım süresiyle çarpmasın diye. Kadansın ölçüsü `async_operations` tablosudur
    (kartın K1 sayımı), o yüzden senkron beklemenin kazandıracağı bir kanıt yoktur."""
    item = {
        "content": belge,
        "timestamp": f"{gun}T00:00:00Z",
        "context": BELGE_BAGLAMI,
        "document_id": kimlik,
        "tags": list(BELGE_ETIKETLERI),
        "metadata": {"kaynak": BELGE_KAYNAGI,
                     "blob_sha": hashlib.sha256(belge.encode("utf-8")).hexdigest()},
    }
    govde = json.dumps({"items": [item], "async": True}, ensure_ascii=False).encode("utf-8")
    _kod, ham, neden = _istek(_uc(taban, banka, "/memories"), anahtar,
                              govde=govde, yontem="POST")
    if neden:
        return None, neden
    try:
        yanit = json.loads((ham or b"").decode("utf-8") or "null") or {}
    except ValueError as e:
        # sessiz-yutma: gövde JSON değilse retain'in OLUP OLMADIĞI bilinmez; `operation_id` YOK
        # (None) döner ve bu bir ihlal değil ölçülemezliktir — POST'un kendisi 2xx aldığı için
        # `neden` doldurulmaz, sinyal olaya `operation_id=None` olarak çıkar (uydurma yasağı).
        obs.warn(f"{OLAY}_yanit_ayristirilamadi", hata=f"{type(e).__name__}")
        yanit = {}
    if not isinstance(yanit, dict):
        yanit = {}
    op = yanit.get("operation_id")
    if not op:
        opsler = yanit.get("operation_ids") or []
        op = opsler[0] if opsler else None
    return (str(op) if op else None), None


# =================================================================================================
# KOMUT SATIRI
# =================================================================================================

def _ayristir(argv):
    ap = argparse.ArgumentParser(
        description="Günlük defter özetini üretir ve Hindsight bankasına retain eder "
                    "(EDG-2026-089, TSK-168).")
    ap.add_argument("--kuru", action="store_true",
                    help="belgeyi stdout'a bas; HTTP çağrısı YOK, defter yazımı YOK")
    ap.add_argument("--uygula", action="store_true", help="idempotens kapısı + retain")
    ap.add_argument("--gun", default=None, help="YYYY-MM-DD (varsayılan: bugün, UTC)")
    ap.add_argument("--taban-url", dest="taban_url", default=TABAN_URL_VARSAYILAN)
    ap.add_argument("--banka", default=BANKA_VARSAYILAN)
    ap.add_argument("--kok", default=None,
                    help="state/ ve research/cards köklerini bu ağaca çevir (ölçüm sandbox'ı)")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    a = _ayristir(argv)
    if a.kuru == a.uygula:
        # KİP BAYRAĞI TEK OLMALI (dagit'in çelişen-çift kapısıyla aynı hüküm): bayraksız bir koşum
        # "hangi kipi kastettim" sorusunu betiğe bıraktığı için sessizce yanlış kipi seçebilirdi.
        print("HATA: kip bayrağı TEK olmalı — `--kuru` ya da `--uygula` (ikisi birden/hiçbiri "
              "değil)", file=sys.stderr)
        return CIKIS_HATA
    gun = a.gun or bugun_utc()

    if a.kuru:
        print(belge_uret(gun, a.kok))
        return CIKIS_RETAIN

    anahtar, kaynak = anahtar_coz()
    if not anahtar:
        print(f"HATA: {kaynak}", file=sys.stderr)
        return CIKIS_HATA

    belge = belge_uret(gun, a.kok)
    kimlik = belge_kimligi(gun)

    var, neden = belge_var_mi(a.taban_url, a.banka, kimlik, anahtar)
    if neden:
        obs.warn(OLAY, gun=gun, document_id=kimlik, sonuc="hata", items=0,
                 karakter=len(belge), operation_id=None, hata=neden)
        print(f"HATA: idempotens kapısı okunamadı — {neden}", file=sys.stderr)
        return CIKIS_HATA
    if var:
        obs.log(OLAY, gun=gun, document_id=kimlik, sonuc="zaten_var", items=0,
                karakter=len(belge), operation_id=None, anahtar_kaynagi=kaynak)
        print(f"{kimlik} bankada ZATEN VAR — retain edilmedi (idempotent)")
        return CIKIS_ZATEN_VAR

    op, neden = retain_et(a.taban_url, a.banka, kimlik, belge, gun, anahtar)
    if neden:
        obs.warn(OLAY, gun=gun, document_id=kimlik, sonuc="hata", items=0,
                 karakter=len(belge), operation_id=None, hata=neden)
        print(f"HATA: retain düştü — {neden}", file=sys.stderr)
        return CIKIS_HATA

    obs.log(OLAY, gun=gun, document_id=kimlik, sonuc="retain", items=1,
            karakter=len(belge), operation_id=op, anahtar_kaynagi=kaynak)
    print(f"{kimlik} retain edildi ({len(belge)} karakter, operation_id={op})")
    return CIKIS_RETAIN


if __name__ == "__main__":
    sys.exit(main())
