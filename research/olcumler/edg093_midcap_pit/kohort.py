#!/usr/bin/env python3
"""EDG-2026-093 ADIM-0 EKSEN A — S&P MidCap 400 PIT kohort ÜRETİCİSİ (as-of günlük, 2020-07-27+).

ROL: ÖLÇÜM/ÜRETİM ajanı. Bu modül HÜKÜM VERMEZ (`hukum: "YOK — Rol-1"`), KARTA DOKUNMAZ,
`meridian/*.py`ye DOKUNMAZ, `meridian`i İTHAL ETMEZ (pytest dışı koşumda `meridian.obs` canlı
YEREL deftere yazar — CLAUDE.md §2), canlı `state/`e YAZMAZ ve AĞA ÇIKMAZ (bütün girdiler
yereldeki donmuş blob'lardır; `olc.cek()` HTTP yolu bu turda HİÇ çağrılmadı).

NE YAPAR
  (1) SHA KAPILARI — ham wikitext ve MDY xlsx beklenen sha256'ya eşit değilse DURUR (dosya ADIYLA,
      çıkış 2). Beklenen sha koda YAZILMAZ: ham için `ham_SHA256.txt`, xlsx için `girdi/SHA256SUMS`
      (ikisi de depoda, EDG-092 turunda donmuş) — tek-kaynak yasası.
  (2) DEĞİŞİKLİK TABLOSU — `olc.tabloyu_ayristir` (EDG-092) İTHAL edilir, KOPYALANMAZ.
  (3) GÜNCEL LİSTE — `olc.mdy_tickerlari` (SPDR MDY holdings xlsx, stdlib zipfile).
  (3b) ÇOK-SEMBOLLÜ HÜCRE (TUR-2) — `UA/UAA` gibi TEK hücrede yazılmış İKİ HİSSE SINIFI AYRI
      sembollere BÖLÜNÜR (S&P endeksleri iki sınıfı ayrı bileşen sayar; kaynak tablonun KENDİ
      hücresi). Bölünmezse `UA/UAA` diye bir HAYALET ticker kohorta girer ve gerçek `UA`/`UAA`
      kohortta HİÇ görünmez (tur-1'de ölçüldü: 163 csv satırının 146'sı hayaleti taşıyordu).
  (4) AS-OF GÜNLÜK — `edg075 olcum.as_of` (EDG-075/092 ile AYNI fonksiyon nesnesi) pencere
      içindeki HER TAKVİM GÜNÜ için çağrılır. Algoritma burada YENİDEN YAZILMAZ.
  (5) KARAR TABLOSU — aday satırlar İKİ kaynaktan gelir: (a) pencere içindeki TEK YANLI satırlar,
      (b) geri sarmada ETKİSİZ adım üreten satırlar (yeniden adlandırma/birleşmelerin yaşadığı
      yer). Her satıra bir `karar` bağlanır: `esle:<eski>-><yeni>` (YENİDEN ADLANDIRMA KİMLİĞİ —
      UYGULANIR) | `cift:<cikan>-><giren>` (iki yarım satır aynı olay — ANOTASYON, listeyi
      DEĞİŞTİRMEZ) | `dusur` | `belirsiz`. İki jeton AYRIDIR çünkü davranışları AYRIDIR: `cift`
      uygulansaydı çıkan isim kohorttan tamamen silinirdi (ölçüldü). Kararlar tablonun KENDİ
      `Reason`/`<ref>` hücrelerinden ÖNERİLİR (ağ yok, uydurma yok; MDY listesindeki varlık/yokluk
      TANIdır, karar gerekçesi OLAMAZ); karar veremeyen satır `belirsiz` KALIR ve gün başına
      belirsiz isim sayısına girer.
  (6) KAPILAR — kart eşikleri: her gün için |as_of(t)| ∈ `kohort_boyut_bant` VE belirsiz isim
      ≤ `belirsiz_isim_gun_ust`. Eşikler KARTTAN okunur, koda sayı yazılmaz (CLAUDE.md §5).
  (7) PIT-PK — kartın `pozitif_kontrol` (4) maddesi: EDG-092 `bilinen_olaylar` kümesinden sabit
      tohumla 10 olay çekilir; olay yürürlük gününde as-of listeye yansımalı (t-1 eski / t yeni,
      tolerans 1 gün — EDG-092 K1 ile AYNI).

ÇIKTILAR VE OKUYUCULARI (Yasa 6 — okunmayan artefakt üretilmez)
  · `research/pit_universe/sp400_uyelik_tarihi.csv` — OKUYUCU: EDG-093 ana ölçümü (mid-cap kohort
    evreni) ve ileride TSK-065 canlı evren genişletmesi; biçim emsali `sp500_uyelik_tarihi.csv`in
    tüketicileriyle AYNI (`research/qc_dogrulama/pit_araliklari_uret.py`,
    `research/olcumler/edg066_tick_arsiv/kapsam_uret.py`, `tests/test_qc_defter_v4_pit_evren_v383.py`).
  · `research/pit_universe/sp400_elle_esleme.yaml` — OKUYUCU: Rol-1 (kararları gözden geçirir).
    ÜRETİLMİŞ dosyadır: her `--uygula` YENİDEN ÜRETİR, elle düzenlenmez; düzenlenmiş bir tablo
    koşuma `--esleme <yol>` ile AÇIK yoldan verilir (çıktıdaki dosya GİRDİ DEĞİLDİR).
  · `research/olcumler/edg093_midcap_pit/adim0a_sonuc_<damga>.json` — OKUYUCU: Rol-1 (ADIM-0 A
    hükmü) ve devir brief'i.

ÖLÇÜLEN CSV SÖZLEŞMESİ (VARSAYILMADI — `sp500_uyelik_tarihi.csv` üzerinde ölçüldü 2026-09-14;
sha256 39a9202c9ef69a74c0ff07e2113ad41fb6da7c8c5b6cd9541f0185fb4391e717):
  · başlık `date,tickers`; 2.718 veri satırı; 1996-01-02 → 2026-06-30; LF satır sonu.
  · `date` ARTAN ve TEKRARSIZ; `tickers` alfabetik SIRALI, iç tekrar YOK, virgülle birleşik ve
    (virgül içerdiği için) çift tırnaklı.
  · Dosya GÜNLÜK DEĞİLDİR: 2.717 ardışık çiftin 2.024'ü BİREBİR AYNI kümeyi taşır ve takvim
    günlerinin çoğu dosyada YOKTUR — yani bir ADIM FONKSİYONU ÖRNEKLEMESİDİR.
  · AS-OF OKUMASI: `t` günündeki üyelik = `tarih ≤ t` olan SON satır (aynı okuma
    `research/qc_dogrulama/pit_araliklari_uret.py` ve `qc_defter_021_d.py` başlıklarında da
    ölçülmüş hâlde yazılıdır).
  Bu dosya AYNI sözleşmeyle üretilir: pencere başı satırı + ÜYELİĞİN DEĞİŞTİĞİ her gün bir satır.
  Böylece her takvim günü için as-of okuması BİREBİR doğrudur ve dosya gereksiz kopya taşımaz.

RASTGELELİK: PIT-PK örneklemesi `random.Random(TOHUM)`; `TOHUM` kart kimliğinden (`TOHUM_ADI`)
sha256 ile türetilir — çağrı başına değişmez, dosyada ADIYLA durur.

KOMUT SATIRI SÖZLEŞMESİ (ops emsali: sözleşme KOMUT SATIRIdır, `main()` değil):
  `--kuru`                     yalnız sayıları basar, HİÇBİR dosya yazmaz.
  `--uygula --cikti <dizin>`   csv + elle eşleme yaml + sonuç json yazar (`<dizin>` depo kökü gibi
                               davranır: altına `research/pit_universe/` ve
                               `research/olcumler/edg093_midcap_pit/` açılır).
ÇIKIŞ KODLARI: 0 = kapılar geçti · 2 = sha kapısı / girdi hatası · 3 = ADIM-0 kapısı düştü
(boyut bandı ya da belirsiz tavanı). Kapı düşse de sonuç JSON'u YİNE yazılır (Yasa 6).
"""
from __future__ import annotations

import argparse
import copy
import csv
import datetime as dt
import hashlib
import io
import json
import pathlib
import random
import re
import sys

import yaml

SANDBOX = pathlib.Path(__file__).resolve().parent
KOK = SANDBOX.parents[2]

# `sys.path` eki ZORUNLU ve BİLİNÇLİ (emsal: EDG-092 `olc.py` başlığı). Bu betik DOĞRUDAN koşulur;
# o zaman `sys.path[0]` BU dizindir ve `ops.` ön eki editable-install `.pth`i üzerinden BAŞKA BİR
# CHECKOUT'a düşer (worktree'den `ModuleNotFoundError`, ana checkout'ta sessizce ORANIN kopyası —
# hafıza `worktree-pythonpath-tuzagi`).
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))
from ops.sasi_yukleyici import kaynaktan_yukle                                    # noqa: E402

EDG092_DIZIN = KOK / "research" / "olcumler" / "edg092_sp400_uyelik"
OLC_YOLU = EDG092_DIZIN / "olc.py"
HAM_VARSAYILAN = EDG092_DIZIN / "ham" / "sp400_oldid_1373849406.wiki"
HAM_SHA_KAYDI = EDG092_DIZIN / "ham_SHA256.txt"
XLSX_VARSAYILAN = EDG092_DIZIN / "girdi" / "mdy_holdings_2026-09-10.xlsx"
XLSX_SHA_KAYDI = EDG092_DIZIN / "girdi" / "SHA256SUMS"
KART093_YOLU = (KOK / "research" / "cards"
                / "EDG-2026-093-midcap-pit-kohort-sagkalan-ust-sinir.yaml")
KART092_YOLU = (KOK / "research" / "cards"
                / "EDG-2026-092-sp400-uyelik-tarihcesi-ucretsiz-kaynak-fizibilite.yaml")

CSV_GORECELI = pathlib.PurePosixPath("research/pit_universe/sp400_uyelik_tarihi.csv")
ESLEME_GORECELI = pathlib.PurePosixPath("research/pit_universe/sp400_elle_esleme.yaml")
SONUC_DIZIN_GORECELI = pathlib.PurePosixPath("research/olcumler/edg093_midcap_pit")

#: PIT-PK örnekleme tohumu. Kart kimliğinden türetilir — çağrılar arası SABİT, dosyada ADIYLA.
TOHUM_ADI = "EDG-2026-093"
TOHUM = int(hashlib.sha256(TOHUM_ADI.encode("utf-8")).hexdigest()[:8], 16)
#: PIT-PK örneklem büyüklüğü ve tolerans — kart `pozitif_kontrol` (4) lafzı ("rastgele 10 olay",
#: "tolerans 1 gün, EDG-092 K1 ile aynı").
PK_OLAY_N = 10
PK_TOLERANS_GUN = 1

#: EŞLEME ÖNERİSİ — tablonun KENDİ gerekçe hücresinden okunan iki desen. Kaynak: EDG-092 tanısı
#: ("spin-off çiftleri, ardışık kitaplama"). Desenler KAPI DEĞİL, ÖNERİ üretir; Rol-1 gözden geçirir.
SPINOFF_RE = re.compile(r"spun[\s-]*off|spin[\s-]*off", re.IGNORECASE)
KAP_DEGISIM_RE = re.compile(r"market\s+capitalization", re.IGNORECASE)
#: İki yarım satırın "ardışık kitaplama" sayılması için üst sınır (takvim günü). 3 SEÇİMDİR ve
#: beyanlıdır: EDG-092 tanısındaki 12 satırın hepsi 1 gün arayla kitaplanmış; 3 gün bir hafta sonu
#: köprüsüne izin verir, daha geniş bir pencere ALAKASIZ satırları eşleştirme riskini doğurur.
ESLEME_GUN_PENCERESI = 3
KARAR_ONEKLERI = ("esle:", "cift:", "dusur", "belirsiz")
KARAR_CIFT_RE = re.compile(r"(?:esle|cift):[A-Z0-9.\-]{1,8}->[A-Z0-9.\-]{1,8}")
ESLEME_ALANLARI = ("satir", "karar", "gerekce", "kaynak")

#: ÇOK-SEMBOLLÜ TICKER HÜCRESİ (TUR-2). S&P endeksleri bir şirketin İKİ HİSSE SINIFINI AYRI
#: bileşen sayar ve kaynak tablo bunu TEK hücrede yazar (ölçülen iki hücre: `UA/UAA` eklenen,
#: `UAA/UA` çıkan). Hücre bölünmezse `UA/UAA` diye bir HAYALET "ticker" kohorta girer — inceleme
#: ölçümü 2026-09-14: tur-1 csv'sinin 163 satırının 146'sı bu hayaleti taşıyordu ve gerçek `UA`
#: ile `UAA` kohortta HİÇ yoktu. Ayıraçlar `/`, `,`, `;` (hepsi taranır; ölçülen yalnız `/`).
HUCRE_AYIRAC_RE = re.compile(r"[/,;]")
#: Gerekçe hücresindeki BORSA PARANTEZİ — yeniden adlandırmanın YENİ sembolünü veren TEK makine
#: okunur işaret (ör. "changed its name and symbol to … (NYSE: HR)"). Dar tutulur: düzyazıdaki
#: serbest büyük-harf kısaltmaları sembol saymak yanlış eşleme üretirdi (EDG-092 PK-2'nin ölçülmüş
#: yanlış-pozitifi: gerekçede rename ANLATILAN satır gerçek bir üyelik değişikliğiydi).
BORSA_SEMBOL_RE = re.compile(
    r"\(\s*(?:NYSE\s+AMERICAN|NYSE|NASDAQ|NASD|AMEX|CBOE|BATS)\s*:\s*([A-Z][A-Z0-9.\-]{0,5})\s*\)",
    re.IGNORECASE)


class GirdiHatasi(Exception):
    """SHA kapısı / girdi sözleşmesi ihlali — çağıran çıkış 2 ile durur."""


def _olc_yukle():
    """EDG-092 ölçüm betiğini DOSYA YOLUNDAN, KAYNAKTAN DERLEYEREK yükler.

    Ham `spec.loader.exec_module` YASAK (v334): o yol `__pycache__`e bakar ve zaman damgalı
    pyc'nin geçerlilik ölçütü yalnız (tam-saniye mtime, bayt boyutu) çiftidir — `olc.py`de boyutu
    değiştirmeyen bir düzenleme aynı saniyede kalırsa BAYAT bytecode koşar ve bu üretici sessizce
    ESKİ ayrıştırıcıyla iş görür. `sys_modules_kaydet=True` betiğin kendi adını çözebilmesi için."""
    return kaynaktan_yukle(OLC_YOLU, "edg092_olc_kohort", sys_modules_kaydet=True)


OLC = _olc_yukle()
#: EDG-075 `as_of` — EDG-092 üzerinden AYNI modül nesnesi (tek-kaynak; kopya değil).
ORTAK = OLC.ORTAK


# ======================================================================================
# SHA KAPILARI
# ======================================================================================

def sha256_dosya(yol: pathlib.Path) -> str:
    return hashlib.sha256(pathlib.Path(yol).read_bytes()).hexdigest()


def sha_kaydindan(kayit_yolu: pathlib.Path, dosya_adi: str) -> str:
    """`shasum -a 256` biçimli kayıttan (`<sha>  <yol>`) beklenen sha'yı okur. Kayıt satırı yoksa
    UYDURMA YOK — `GirdiHatasi`."""
    kayit = pathlib.Path(kayit_yolu)
    if not kayit.exists():
        raise GirdiHatasi(f"sha kaydı yok: {kayit} — beklenen sha UYDURULAMAZ")
    for satir in kayit.read_text(encoding="utf-8").splitlines():
        parcalar = satir.split()
        if len(parcalar) >= 2 and pathlib.PurePosixPath(parcalar[-1]).name == dosya_adi:
            return parcalar[0]
    raise GirdiHatasi(f"sha kaydında '{dosya_adi}' satırı yok: {kayit} — beklenen sha UYDURULAMAZ")


def sha_kapisi(yol: pathlib.Path, beklenen: str, ad: str) -> str:
    """Dosyanın sha256'sını ölçer ve `beklenen`e eşit değilse DURUR — hata metni dosyayı ADIYLA
    anar (kart `girdi_kimligi` disiplini; sessiz devam ETMEZ)."""
    yol = pathlib.Path(yol)
    if not yol.exists():
        raise GirdiHatasi(f"{ad}: girdi dosyası yok — {yol}")
    olculen = sha256_dosya(yol)
    if olculen != beklenen:
        raise GirdiHatasi(
            f"{ad}: sha256 UYUŞMUYOR — dosya {yol}; ölçülen {olculen}; beklenen {beklenen}")
    return olculen


# ======================================================================================
# KART — EŞİKLER VE PENCERE (koda sayı yazılmaz)
# ======================================================================================

def esikleri_karttan_al(kart: dict) -> dict:
    """EDG-093 `esikler`den ADIM-0 A'nın İKİ eşiği. Alan yoksa ValueError (UYDURMA YOK)."""
    esikler = kart.get("esikler") if isinstance(kart, dict) else None
    if not isinstance(esikler, dict):
        raise ValueError("kart 'esikler' alanı yok/sözlük değil — betik eşiği UYDURAMAZ")
    bant = esikler.get("kohort_boyut_bant")
    if not (isinstance(bant, (list, tuple)) and len(bant) == 2):
        raise ValueError("kart eşiği bulunamadı: kohort_boyut_bant — betik eşiği UYDURAMAZ")
    ust = esikler.get("belirsiz_isim_gun_ust")
    if ust is None:
        raise ValueError("kart eşiği bulunamadı: belirsiz_isim_gun_ust — betik eşiği UYDURAMAZ")
    return {"kohort_boyut_bant": [int(bant[0]), int(bant[1])],
            "belirsiz_isim_gun_ust": int(ust), "kart_id": kart.get("card_id")}


def gunler(bas: str, son: str) -> list[str]:
    """[bas, son] kapalı aralığındaki HER TAKVİM GÜNÜ (ISO)."""
    d0, d1 = dt.date.fromisoformat(bas), dt.date.fromisoformat(son)
    if d1 < d0:
        raise ValueError(f"pencere ters: {bas} > {son}")
    return [(d0 + dt.timedelta(days=i)).isoformat() for i in range((d1 - d0).days + 1)]


# ======================================================================================
# ÇOK-SEMBOLLÜ HÜCRE (TUR-2) — `UA/UAA` → `UA` + `UAA`
# ======================================================================================

def sembolleri_bol(hucre: str | None) -> tuple[list[str], bool]:
    """(semboller, bolundu_mu). Ayıraçla ayrılmış parçaların HEPSİ ticker biçimindeyse hücre
    bölünür; biri bile değilse hücre OLDUĞU GİBİ kalır ve `bolundu` False döner (çağıran bunu
    `bolunemeyen` olarak RAPORLAR — sessizce bölmek uydurma, sessizce atmak Yasa 4 ihlali olurdu).

    Ticker biçimi EDG-092'nin TICKER_RE'sinden gelir (tek-kaynak: MDY listesini süzen desenin
    AYNISI) — iki ayrı ticker tanımı sessizce ayrışırdı."""
    if not hucre:
        return ([], False)
    parcalar = [p.strip() for p in HUCRE_AYIRAC_RE.split(hucre) if p.strip()]
    if len(parcalar) < 2:
        return ([hucre], False)
    if all(OLC.TICKER_RE.fullmatch(p) for p in parcalar):
        return (parcalar, True)
    return ([hucre], False)


def satirlari_bol(degisiklikler: list[dict]) -> tuple[list[dict], dict]:
    """(bolunmus_satirlar, rapor). Çok-sembollü hücre taşıyan tablo satırı SEMBOL BAŞINA bir ALT
    SATIRA bölünür; alt satırlar `satir_no`yu (provenans çapası) KORUR ve `alt_no` ile ayrılır.

    Neden satır bölmek: `as_of` (EDG-075, İTHAL) satır başına TEK `eklenen` ve TEK `cikan` okur ve
    bu üretici onu YENİDEN YAZMAZ. Eşleştirme sırayla yapılır — `AAX/AAY` eklenen + `DDD` çıkan →
    (`AAX`,`DDD`) ve (`AAY`,None); böylece karşı yarım İKİ KEZ kitaplanmaz.

    Satır sırası KORUNUR: `as_of` bugünden geriye sarar ve tablo satırları AZALAN tarihlidir;
    sıra bozulursa geri sarma adımları yanlış sırada uygulanır."""
    bolunmus: list[dict] = []
    bolunen: list[dict] = []
    bolunemeyen: list[dict] = []
    for r in degisiklikler:
        e, e_bolundu = sembolleri_bol(r.get("eklenen"))
        c, c_bolundu = sembolleri_bol(r.get("cikan"))
        for alan, ham, bolundu in (("eklenen", r.get("eklenen"), e_bolundu),
                                   ("cikan", r.get("cikan"), c_bolundu)):
            if ham and HUCRE_AYIRAC_RE.search(ham):
                kayit = {"satir_no": r.get("satir_no"), "tarih": r.get("tarih"), "alan": alan,
                         "hucre": ham}
                if bolundu:
                    kayit["semboller"] = e if alan == "eklenen" else c
                    bolunen.append(kayit)
                else:
                    kayit["neden"] = ("parçalardan biri ticker biçiminde değil — hücre BÖLÜNMEDİ "
                                      "(uydurma yok); Rol-1 okur")
                    bolunemeyen.append(kayit)
        for i in range(max(len(e), len(c), 1)):
            alt = dict(r)
            alt["eklenen"] = e[i] if i < len(e) else None
            alt["cikan"] = c[i] if i < len(c) else None
            alt["alt_no"] = i
            bolunmus.append(alt)
    return bolunmus, {"bolunen_n": len(bolunen), "bolunen": bolunen,
                      "bolunemeyen_n": len(bolunemeyen), "bolunemeyen": bolunemeyen,
                      "ayirac_deseni": HUCRE_AYIRAC_RE.pattern,
                      "ham_satir_n": len(degisiklikler), "bolunmus_satir_n": len(bolunmus)}


# ======================================================================================
# ELLE EŞLEME — TEK YANLI SATIRLAR
# ======================================================================================

def _anahtar(r: dict) -> tuple:
    """Satır kimliği: (wikitext satır indeksi, çok-sembollü hücre alt indeksi)."""
    return (r.get("satir_no"), r.get("alt_no", 0))


def tek_yanli_satirlar(degisiklikler: list[dict], bas: str, son: str) -> list[dict]:
    """Pencere içinde YALNIZ bir yanı dolu (eklenen XOR çıkan) satırlar — as-of kaymasının adayları.
    S&P 400 daima 400 üyelidir; tek yanlı bir satır ya gerçek bir tek-yanlı kitaplamadır (karşı
    yarısı ertesi gün gelir) ya da tabloda eksik bir yarımdır. Ayrımı bu fonksiyon YAPMAZ."""
    out = []
    for r in degisiklikler:
        t = r.get("tarih")
        if not t or not (bas <= t <= son):
            continue
        if bool(r.get("eklenen")) != bool(r.get("cikan")):
            out.append(r)
    return sorted(out, key=lambda r: (r["tarih"], r.get("satir_no", 0)))


def _satir_ozeti(r: dict, etkisiz: list[dict] | None = None) -> dict:
    """Eşleme tablosunun `satir` alanı — tablodaki HAM hücreler (yorum değil). `etkisiz_*` alanları
    geri sarmanın ÖLÇÜLEN kusurudur: o satır bir ETKİSİZ adım üretti (sembol kümede yok/zaten var)."""
    ozet = {"tarih": r.get("tarih"), "tarih_ham": r.get("tarih_ham"),
            "eklenen": r.get("eklenen"), "eklenen_ad": r.get("eklenen_ad"),
            "cikan": r.get("cikan"), "cikan_ad": r.get("cikan_ad"),
            "satir_no": r.get("satir_no"), "alt_no": r.get("alt_no", 0)}
    if etkisiz:
        ozet["etkisiz_adimlar"] = [{"adim": a["adim"], "sembol": a["sembol"]} for a in etkisiz]
        ozet["etkisiz_semboller"] = sorted({a["sembol"] for a in etkisiz})
    return ozet


def _gun_farki(a: str, b: str) -> int:
    return abs((dt.date.fromisoformat(a) - dt.date.fromisoformat(b)).days)


def geri_sarma(degisiklikler: list[dict], guncel_uyeler: set[str],
               tarih: str) -> tuple[set[str], dict, list[dict]]:
    """(uyeler, sayac, etkisiz_adimlar) — `as_of`un geri sarmasının ADIM ADIM muhasebesi.

    `as_of` bugünden geriye sararken her değişikliği ters çevirir: eklenen `discard`, çıkan `add`.
    `discard` küme o sembolü TAŞIMIYORSA hiçbir şey yapmaz, `add` sembol ZATEN varsa büyütmez.
    Bu İKİ ETKİSİZ ADIM tek yönlü bir sapma bırakır ve her biri tabloda bir kusuru işaret eder
    (yeniden adlandırma, birleşme ya da tablonun eksik yarımı). Küme hesabı `as_of` ile AYNI
    adımları yürütür; `as_of`un kendisi ÇAĞRILMAZ çünkü o yalnız SONUCU döndürür, muhasebeyi değil
    (tek-kaynak: burada ALGORİTMA değil MUHASEBE var — sonuç `uyelik_serisi` üzerinden hep
    gerçek `as_of`tan okunur)."""
    uyeler = set(guncel_uyeler)
    sayac = {"ekle_etkili": 0, "ekle_etkisiz": 0, "discard_etkili": 0, "discard_etkisiz": 0}
    etkisiz: list[dict] = []

    def _kayit(r: dict, adim: str, sembol: str) -> dict:
        return {"tarih": r["tarih"], "adim": adim, "sembol": sembol,
                "satir_no": r.get("satir_no"), "alt_no": r.get("alt_no", 0),
                "neden": r.get("neden")}

    for r in degisiklikler:
        if not (r.get("tarih") and r["tarih"] > tarih):
            continue
        if r.get("eklenen"):
            if r["eklenen"] in uyeler:
                uyeler.discard(r["eklenen"])
                sayac["discard_etkili"] += 1
            else:
                sayac["discard_etkisiz"] += 1
                etkisiz.append(_kayit(r, "discard", r["eklenen"]))
        if r.get("cikan"):
            if r["cikan"] in uyeler:
                sayac["ekle_etkisiz"] += 1
                etkisiz.append(_kayit(r, "ekle", r["cikan"]))
            else:
                uyeler.add(r["cikan"])
                sayac["ekle_etkili"] += 1
    return uyeler, sayac, etkisiz


def aday_satirlar(degisiklikler_ham: list[dict], degisiklikler_bol: list[dict],
                  guncel_uyeler: set[str], bas: str, son: str) -> list[dict]:
    """Elle eşleme tablosunun ADAY satırları — İKİ kaynaktan, `(satir_no, alt_no)` ile teklenir:

      (a) TEK YANLI satırlar (tur-1): pencere içinde yalnız bir yanı dolu tablo satırları.
      (b) ETKİSİZ ADIM üreten satırlar (tur-2): geri sarmanın ölçülen kusurları — yeniden
          adlandırma/birleşme çiftlerinin yaşadığı yer.

    Tek yanlılık HAM (bölünmemiş) tablo satırında sorulur: çok-sembollü bir hücrenin alt satırı
    (ör. `AAY`, karşı yarımı olmayan ikinci hisse sınıfı) mekanik bir bölme artığıdır, Rol-1'e
    sorulacak bir KARAR değil."""
    adaylar: dict[tuple, dict] = {}
    for r in tek_yanli_satirlar(degisiklikler_ham, bas, son):
        adaylar[_anahtar(r)] = {"satir": r, "etkisiz": []}
    indeks = {_anahtar(r): r for r in degisiklikler_bol}
    _, _, etkisiz = geri_sarma(degisiklikler_bol, guncel_uyeler, bas)
    for a in etkisiz:
        if not (a["tarih"] and bas <= a["tarih"] <= son):
            continue
        k = (a["satir_no"], a["alt_no"])
        adaylar.setdefault(k, {"satir": indeks[k], "etkisiz": []})["etkisiz"].append(a)
    return [adaylar[k] for k in sorted(adaylar, key=lambda k: (
        adaylar[k]["satir"].get("tarih") or "", k[0] or 0, k[1]))]


def rename_onerisi(r: dict, etkisiz: list[dict]) -> str | None:
    """Gerekçe hücresi yeniden adlandırmayı AÇIKÇA söylüyorsa `esle:<eski>-><yeni>`, yoksa None.

    ÜÇ KOŞUL birden (hepsi tablonun KENDİ hücresinden; ağ yok, MDY listesi KARAR GEREKÇESİ DEĞİL):
      (1) satır bir ETKİSİZ adım üretti — yani geri sarmada ölçülmüş bir kusur var,
      (2) gerekçe metni yeniden-adlandırma sözlüğüyle eşleşiyor (sözlük EDG-092'den İTHAL, tek
          kaynak: aynı sözlük orada PK-2'nin tarama listesini de besler),
      (3) gerekçede borsa parantezinde TEK bir sembol var ve etkisiz adımların sembollerinden
          TAM BİRİ ondan farklı — o biri `<eski>`, parantezdeki `<yeni>`.
    Koşullardan biri düşerse karar VERİLMEZ (None → çağıran `belirsiz` bırakır). Gerekçe metninin
    tek başına kapı OLMADIĞI EDG-092'de ölçülmüştür: gerçek bir üyelik değişikliğinin gerekçesinde
    de birleşik şirketin adının değiştiği anlatılabiliyor — (1) ve (3) o yüzden zorunlu."""
    neden = r.get("neden") or ""
    if not etkisiz or not OLC.RENAME_SOZLUGU.search(neden):
        return None
    yeniler = sorted({t for t in (ORTAK._tick(s) for s in BORSA_SEMBOL_RE.findall(neden)) if t})
    if len(yeniler) != 1:
        return None
    yeni = yeniler[0]
    eskiler = sorted({a["sembol"] for a in etkisiz} - {yeni})
    if len(eskiler) != 1:
        return None
    return f"esle:{eskiler[0]}->{yeni}"


def esleme_onerisi(adaylar: list[dict]) -> list[dict]:
    """Aday satırlara tablonun KENDİ gerekçesinden karar ÖNERİR (ağ yok, uydurma yok).

    İKİ ÖNERİ KURALI, ikisi de beyanlı ve DAR:
      (a) YENİDEN ADLANDIRMA → `esle:<eski>-><yeni>`: `rename_onerisi`in üç koşulu. Bu karar
          UYGULANIR — as-of yürütmesinde o satırın `<eski>` sembolü `<yeni>` ile yazılır (aynı
          ihracın bugünkü adı), böylece etkisiz adım GERÇEK adıma döner.
      (b) İKİ YARIM SATIR → `cift:<çıkan>-><giren>`: gerekçesinde spin-off geçen bir YALNIZ-GİREN
          satır ile gerekçesinde "market capitalization" geçen bir YALNIZ-ÇIKAN satır
          `ESLEME_GUN_PENCERESI` içinde ve karşılıklı TEK adaysa. Bu karar bir ANOTASYONDUR:
          iki yarımın AYNI endeks değişiminin iki kitaplaması olduğunu kaydeder, HİÇBİR sembolü
          ve tarihi DEĞİŞTİRMEZ. Uygulansaydı çıkan isim kohorttan tamamen silinirdi (ölçüldü) —
          `esle` ile `cift` bu yüzden AYRI jetonlardır: aynı jetona iki davranış vermek tuzaktır.
    İki kural da karar veremezse satır `belirsiz` KALIR."""
    kararlar: dict[tuple, dict] = {}
    for a in adaylar:
        r = a["satir"]
        karar = rename_onerisi(r, a["etkisiz"])
        if karar:
            kararlar[_anahtar(r)] = {
                "karar": karar, "gerekce": r.get("neden"),
                "kaynak": {"wikitext_satir_no": [r.get("satir_no")],
                           "urller": sorted(set(r.get("urller") or [])),
                           "kural": ("gerekçe hücresi yeniden-adlandırma sözlüğüyle eşleşti ve "
                                     "borsa parantezinde TEK sembol verdi; <eski> geri sarmanın "
                                     "ETKİSİZ adımındaki sembol")}}

    kalanlar = [a["satir"] for a in adaylar if _anahtar(a["satir"]) not in kararlar
                and bool(a["satir"].get("eklenen")) != bool(a["satir"].get("cikan"))]
    girenler = [r for r in kalanlar if r.get("eklenen") and SPINOFF_RE.search(r.get("neden") or "")]
    cikanlar = [r for r in kalanlar if r.get("cikan") and KAP_DEGISIM_RE.search(r.get("neden") or "")]
    eslesen: set[tuple] = set()
    for g in girenler:
        adaylar_c = [c for c in cikanlar
                     if _gun_farki(g["tarih"], c["tarih"]) <= ESLEME_GUN_PENCERESI
                     and _anahtar(c) not in eslesen]
        if len(adaylar_c) != 1:
            continue
        c = adaylar_c[0]
        karsi = [g2 for g2 in girenler
                 if _gun_farki(g2["tarih"], c["tarih"]) <= ESLEME_GUN_PENCERESI]
        if len(karsi) != 1:
            continue
        karar = f"cift:{c['cikan']}->{g['eklenen']}"
        gerekce = " || ".join(x for x in (c.get("neden"), g.get("neden")) if x) or None
        kaynak = {"wikitext_satir_no": [c.get("satir_no"), g.get("satir_no")],
                  "urller": sorted(set((c.get("urller") or []) + (g.get("urller") or []))),
                  "kural": ("gerekçe hücresi: giren satırda spin-off, çıkan satırda market "
                            f"capitalization; |Δgün| ≤ {ESLEME_GUN_PENCERESI}; ANOTASYON — "
                            "değişiklik listesi DEĞİŞMEZ")}
        # Her satıra KENDİ kopyası verilir: paylaşılan sözlük YAML'da `&id001`/`*id001` çapası
        # üretir ve Rol-1'in okumasını tuzağa çevirir (bir kaydı değiştirmek ötekini de
        # değiştirmiş görünür).
        for x in (c, g):
            eslesen.add(_anahtar(x))
            kararlar[_anahtar(x)] = {"karar": karar, "gerekce": gerekce,
                                     "kaynak": copy.deepcopy(kaynak)}

    out = []
    for a in adaylar:
        r = a["satir"]
        k = kararlar.get(_anahtar(r))
        if k is None:
            k = {"karar": "belirsiz",
                 "gerekce": r.get("neden"),
                 "kaynak": {"wikitext_satir_no": [r.get("satir_no")],
                            "urller": sorted(set(r.get("urller") or [])),
                            "kural": "öneri kuralı karar veremedi — belirsiz KALIR (uydurma yok)"}}
        out.append({"satir": _satir_ozeti(r, a["etkisiz"]), **k})
    return out


def esleme_dogrula(tablo: list[dict]) -> None:
    """Şema kapısı: her kaydın `ESLEME_ALANLARI` alanları olmalı ve `karar` sözlük DIŞI bir değer
    taşımamalı. Dosya `--esleme` ile dışarıdan verildiğinde yazım hatası SESSİZCE geçmesin diye."""
    if not isinstance(tablo, list):
        raise GirdiHatasi("elle eşleme tablosu liste değil")
    for i, kayit in enumerate(tablo):
        if not isinstance(kayit, dict):
            raise GirdiHatasi(f"elle eşleme kaydı #{i} sözlük değil")
        eksik = [a for a in ESLEME_ALANLARI if a not in kayit]
        if eksik:
            raise GirdiHatasi(f"elle eşleme kaydı #{i} eksik alan: {', '.join(eksik)}")
        karar = kayit.get("karar")
        if not isinstance(karar, str):
            raise GirdiHatasi(f"elle eşleme kaydı #{i}: 'karar' metin değil")
        if karar == "dusur" or karar == "belirsiz":
            continue
        if karar.startswith("esle:") or karar.startswith("cift:"):
            if not KARAR_CIFT_RE.fullmatch(karar):
                raise GirdiHatasi(
                    f"elle eşleme kaydı #{i}: çift kararı `<jeton>:<eski>-><yeni>` biçiminde "
                    f"değil: {karar!r}")
            continue
        raise GirdiHatasi(
            f"elle eşleme kaydı #{i}: tanınmayan karar {karar!r} — sözlük {KARAR_ONEKLERI}")


def esleme_uygula(degisiklikler: list[dict],
                  tablo: list[dict]) -> tuple[list[dict], list[dict], dict]:
    """(degisiklikler', belirsiz_kayitlar, rapor).

      · `dusur`     satır değişiklik listesinden ÇIKARILIR (tabloda hatalı kitaplandığı BEYANLA
                    tespit edilmiş satır).
      · `esle:X->Y` YENİDEN ADLANDIRMA KİMLİĞİ: kararın BAĞLI OLDUĞU satırda `X` hücresi `Y` ile
                    yazılır. İkame KÜRESEL DEĞİLDİR — aynı sembolü taşıyan alakasız satırlar
                    (ör. bir spin-off'un yeni hissesi, ana şirket eski sembolle anılırken) küresel
                    ikamede bozulurdu.
      · `cift:`     ANOTASYON — listeye DOKUNMAZ.
      · `belirsiz`  listeye dokunmaz; sembolleri gün-başına belirsiz sayımına girer.
    Uygulanamayan bir `esle` SESSİZCE yutulmaz: `uygulanmayan_esleme`de ADIYLA durur (Yasa 4)."""
    dusurulen = {_anahtar(k["satir"]) for k in tablo if k.get("karar") == "dusur"}
    esle: dict[tuple, tuple[str, str]] = {}
    for k in tablo:
        karar = str(k.get("karar") or "")
        if karar.startswith("esle:"):
            eski, yeni = karar[len("esle:"):].split("->")
            esle[_anahtar(k["satir"])] = (eski, yeni)

    kalan: list[dict] = []
    kullanilan: set[tuple] = set()
    for r in degisiklikler:
        a = _anahtar(r)
        if a in dusurulen:
            continue
        m = esle.get(a)
        if m and (r.get("eklenen") == m[0] or r.get("cikan") == m[0]):
            r = dict(r)
            if r.get("eklenen") == m[0]:
                r["eklenen"] = m[1]
            if r.get("cikan") == m[0]:
                r["cikan"] = m[1]
            kullanilan.add(a)
        kalan.append(r)

    uygulanmayan = [{"satir_no": a[0], "alt_no": a[1], "karar": f"esle:{m[0]}->{m[1]}"}
                    for a, m in esle.items() if a not in kullanilan]
    rapor = {"uygulanan_esleme_n": len(kullanilan),
             "uygulanmayan_esleme": sorted(uygulanmayan,
                                           key=lambda d: (d["satir_no"] or 0, d["alt_no"])),
             "dusurulen_satir_n": len(dusurulen)}
    belirsiz = [k for k in tablo if k.get("karar") == "belirsiz"]
    return kalan, belirsiz, rapor


def belirsiz_gun_serisi(belirsiz: list[dict], gun_listesi: list[str]) -> dict[str, list[str]]:
    """Gün → o gün üyeliği BELİRSİZ satıra bağlı olan semboller.

    Gerekçe: `as_of` bugünden geriye sarar; `t`den SONRAKİ bir değişiklik satırı `t` günündeki
    üyeliği belirler. Kararı verilmemiş bir satır `tarih > t` ise o satırın sembolünün `t`
    günündeki üyeliği de kararsızdır. `tarih ≤ t` olan belirsiz satır `t`yi ETKİLEMEZ.

    Hangi sembol: satır bir ETKİSİZ adım ürettiyse belirsiz olan O sembollerdir — satırın
    `eklenen`i değil (ör. `OMCL↑/COHR↓` satırında kusur `COHR`dadır). Etkisiz adım yoksa (tek
    yanlı satır) satırın dolu olan tek hücresi alınır."""
    kayitlar = []
    for k in belirsiz:
        s = k["satir"]
        semboller = s.get("etkisiz_semboller") or [s.get("eklenen") or s.get("cikan")]
        for sembol in semboller:
            if s.get("tarih") and sembol:
                kayitlar.append((s["tarih"], sembol))
    return {g: sorted({sem for t, sem in kayitlar if t > g}) for g in gun_listesi}


# ======================================================================================
# AS-OF SERİSİ VE CSV
# ======================================================================================

def uyelik_serisi(degisiklikler: list[dict], guncel_uyeler: set[str],
                  gun_listesi: list[str]) -> dict[str, frozenset[str]]:
    """Gün → as-of üyelik kümesi. `as_of` EDG-075'ten İTHAL — burada YENİDEN YAZILMAZ."""
    return {g: frozenset(ORTAK.as_of(degisiklikler, guncel_uyeler, g)) for g in gun_listesi}


def fazlalik_tanisi(degisiklikler: list[dict], guncel_uyeler: set[str], tarih: str) -> dict:
    """`as_of(tarih)` 400'den NEDEN sapıyor — geri sarmanın ETKİSİZ adımlarını sayar.

    Muhasebe `geri_sarma`dan gelir (TEK uygulama; aday satırları da o besler). Fonksiyon HÜKÜM
    VERMEZ; sapmanın muhasebesini çıkarır (`sapma` = etkili ekleme − etkili çıkarma; `as_of_n`
    ölçülenle her zaman eşittir — kalem kalem sayım Rol-1'in okuyacağı tanıdır)."""
    uyeler, sayac, etkisiz = geri_sarma(degisiklikler, guncel_uyeler, tarih)
    sayac["guncel_n"] = len(guncel_uyeler)
    sayac["as_of_n"] = len(uyeler)
    sayac["sapma"] = sayac["ekle_etkili"] - sayac["discard_etkili"]
    sayac["etkisiz_n"] = len(etkisiz)
    sayac["etkisiz_ornek"] = sorted(etkisiz, key=lambda d: d["tarih"])[:20]
    return sayac


def csv_satirlari(seri: dict[str, frozenset[str]], gun_listesi: list[str]) -> list[tuple[str, str]]:
    """Ölçülen sp500 sözleşmesi: pencere başı + ÜYELİĞİN DEĞİŞTİĞİ her gün bir satır; `tickers`
    alfabetik sıralı, virgülle birleşik. Her takvim günü için as-of okuması ("tarih ≤ t olan son
    satır") BİREBİR doğru kalır."""
    satirlar: list[tuple[str, str]] = []
    onceki: frozenset[str] | None = None
    for g in gun_listesi:
        kume = seri[g]
        if onceki is None or kume != onceki:
            satirlar.append((g, ",".join(sorted(kume))))
            onceki = kume
    return satirlar


def csv_metni(satirlar: list[tuple[str, str]]) -> str:
    tampon = io.StringIO()
    yazici = csv.writer(tampon, lineterminator="\n")
    yazici.writerow(["date", "tickers"])
    for tarih, tickerlar in satirlar:
        yazici.writerow([tarih, tickerlar])
    return tampon.getvalue()


# ======================================================================================
# PIT-PK (kart pozitif_kontrol (4))
# ======================================================================================

def pk_pit(seri: dict[str, frozenset[str]], olaylar: list[dict], gun_listesi: list[str],
           n: int = PK_OLAY_N, tolerans: int = PK_TOLERANS_GUN, tohum: int = TOHUM) -> dict:
    """EDG-092 `bilinen_olaylar`dan sabit tohumla `n` olay: yürürlük gününde as-of listede
    yansımalı. `gecti` = t-1/t geçişi beklenen yönde VEYA ±`tolerans` gün içinde bir geçiş günü var.

    Penceresi dışında kalan (as-of serisi t-1 ya da t'yi taşımayan) olay `olculemedi` sayılır ve
    `gecti` None kalır — UYDURMA YOK (sıfır ile "bilmiyorum" aynı şey değildir)."""
    havuz = [o for o in olaylar if o.get("tarih") and o.get("sembol") and o.get("yon")]
    secilenler = sorted(havuz, key=lambda o: (o["tarih"], o["sembol"], o["yon"]))
    rastgele = random.Random(tohum)
    ornek = rastgele.sample(secilenler, min(n, len(secilenler)))
    ornek.sort(key=lambda o: (o["tarih"], o["sembol"]))

    ilk, sonuncu = gun_listesi[0], gun_listesi[-1]
    detay = []
    for o in ornek:
        t = o["tarih"]
        onceki_gun = (dt.date.fromisoformat(t) - dt.timedelta(days=1)).isoformat()
        if not (ilk <= onceki_gun and t <= sonuncu):
            detay.append({"sembol": o["sembol"], "yon": o["yon"], "tarih": t,
                          "t_1_uye": None, "t_uye": None, "gecis_gunu": None, "gecti": None,
                          "neden": "olay penceresi as-of serisinin DIŞINDA — ölçülemedi"})
            continue
        t_1 = o["sembol"] in seri[onceki_gun]
        t_u = o["sembol"] in seri[t]
        giris = o["yon"] == "giris"
        gecis = None
        for k in range(-tolerans, tolerans + 1):
            g = (dt.date.fromisoformat(t) + dt.timedelta(days=k)).isoformat()
            g_1 = (dt.date.fromisoformat(g) - dt.timedelta(days=1)).isoformat()
            if g not in seri or g_1 not in seri:
                continue
            oncesi, sonrasi = o["sembol"] in seri[g_1], o["sembol"] in seri[g]
            if (giris and not oncesi and sonrasi) or (not giris and oncesi and not sonrasi):
                gecis = g
                break
        detay.append({"sembol": o["sembol"], "yon": o["yon"], "tarih": t,
                      "t_1_uye": t_1, "t_uye": t_u, "gecis_gunu": gecis,
                      "gecti": bool(gecis is not None)})
    gecen = sum(1 for d in detay if d["gecti"] is True)
    olculemedi = sum(1 for d in detay if d["gecti"] is None)
    return {"tohum_adi": TOHUM_ADI, "tohum": tohum, "olay_havuzu_n": len(havuz),
            "ornek_n": len(ornek), "tolerans_gun": tolerans,
            "gecti_n": gecen, "olculemedi_n": olculemedi,
            "hepsi_gecti": bool(gecen == len(ornek) and ornek), "detay": detay}


# ======================================================================================
# ÖLÇÜM
# ======================================================================================

def olc(ham_yolu: pathlib.Path, xlsx_yolu: pathlib.Path, kart093: dict, bugun: str,
        ham_sha: str, xlsx_sha: str, kart092: dict,
        esleme_tablosu: list[dict] | None = None) -> dict:
    """ADIM-0 A'nın tüm sayıları. HÜKÜM YOK — `hukum` alanı sabit "YOK — Rol-1"."""
    esikler = esikleri_karttan_al(kart093)
    bas = OLC.pencere_baslangici_karttan(kart093)
    gun_listesi = gunler(bas, bugun)

    wikitext = pathlib.Path(ham_yolu).read_text(encoding="utf-8")
    degisiklikler, tablo_meta = OLC.tabloyu_ayristir(wikitext)
    guncel_liste, mdy_meta = OLC.mdy_tickerlari(pathlib.Path(xlsx_yolu))
    guncel = {t for t in guncel_liste if t}

    # (1) ÇOK-SEMBOLLÜ HÜCRE önce bölünür: aday satırları da, as-of serisini de BÖLÜNMÜŞ liste
    # besler — bölme sonradan yapılsaydı hayalet sembol tanının içine sızardı.
    degisiklikler_bol, bolme = satirlari_bol(degisiklikler)
    adaylar = aday_satirlar(degisiklikler, degisiklikler_bol, guncel, bas, bugun)
    onerilen = esleme_onerisi(adaylar)
    tablo = esleme_tablosu if esleme_tablosu is not None else onerilen
    esleme_dogrula(tablo)
    degisiklikler_son, belirsiz, esleme_raporu = esleme_uygula(degisiklikler_bol, tablo)

    seri = uyelik_serisi(degisiklikler_son, guncel, gun_listesi)
    boyutlar = [len(seri[g]) for g in gun_listesi]
    alt, ust = esikler["kohort_boyut_bant"]
    bant_disi = [{"tarih": g, "boyut": len(seri[g])} for g in gun_listesi
                 if not (alt <= len(seri[g]) <= ust)]

    belirsiz_seri = belirsiz_gun_serisi(belirsiz, gun_listesi)
    belirsiz_sayilari = [len(belirsiz_seri[g]) for g in gun_listesi]
    belirsiz_tavan = esikler["belirsiz_isim_gun_ust"]
    belirsiz_asan = [{"tarih": g, "n": len(belirsiz_seri[g]), "semboller": belirsiz_seri[g]}
                     for g in gun_listesi if len(belirsiz_seri[g]) > belirsiz_tavan]

    olaylar, kart_beyan_n, normalizasyon = OLC.olay_kumesi(kart092)
    pk = pk_pit(seri, olaylar, gun_listesi)

    csv_rows = csv_satirlari(seri, gun_listesi)
    metin = csv_metni(csv_rows)

    karar_sayimi: dict[str, int] = {}
    for k in tablo:
        ham_karar = str(k.get("karar", ""))
        anahtar = next((o[:-1] for o in ("esle:", "cift:") if ham_karar.startswith(o)), ham_karar)
        karar_sayimi[anahtar] = karar_sayimi.get(anahtar, 0) + 1

    # ÇOK-SEMBOLLÜ HÜCRE KANITI: kohortta ayıraç taşıyan sembol KALMAMALI. Sayı tanıdan değil
    # ÜRETİLEN seriden okunur — "böldüm" demek ile "csv'de yok" AYRI iddialardır.
    ayirac_tasiyan = sorted({s for g in gun_listesi for s in seri[g] if HUCRE_AYIRAC_RE.search(s)})
    ayirac_satir_n = sum(1 for _, tickerlar in csv_rows
                         if any(HUCRE_AYIRAC_RE.search(s) for s in tickerlar.split(",")))

    kapi_gecti = not bant_disi and not belirsiz_asan
    return {
        "kart_id": kart093.get("card_id"), "adim": "ADIM-0 EKSEN A",
        "damga": OLC.damga(), "bugun": bugun,
        "pencere": {"bas": bas, "son": bugun, "gun_n": len(gun_listesi)},
        "girdi_kimligi": {
            "ham_wikitext": {"yol": str(ham_yolu), "sha256": ham_sha},
            "mdy_xlsx": {"yol": str(xlsx_yolu), "sha256": xlsx_sha, "as_of": mdy_meta.get("as_of"),
                         "tutulan_n": mdy_meta.get("tutulan_n"),
                         "haric_tutulan": mdy_meta.get("haric_tutulan")},
            "kart093": str(KART093_YOLU), "kart092": str(KART092_YOLU)},
        "tablo_meta": {a: tablo_meta.get(a) for a in
                       ("satir_n_ham", "satir_n_gecerli", "hayalet_atlanan_n",
                        "tarih_cozulemeyen_n", "kaynaksiz_satir_n")},
        "esikler": esikler,
        "kohort": {
            "gun_n": len(gun_listesi),
            "boyut_min": min(boyutlar), "boyut_max": max(boyutlar),
            "boyut_ort": round(sum(boyutlar) / len(boyutlar), 4),
            "boyut_bas": len(seri[gun_listesi[0]]), "boyut_son": len(seri[gun_listesi[-1]]),
            "bant_disi_gun_n": len(bant_disi), "bant_disi": bant_disi[:40],
            "boyut_dagilimi": {str(b): boyutlar.count(b) for b in sorted(set(boyutlar))},
            "max_gunler": [g for g in gun_listesi if len(seri[g]) == max(boyutlar)][:20],
            "fazlalik_tanisi": fazlalik_tanisi(degisiklikler_son, guncel, bas),
            "csv_satir_n": len(csv_rows)},
        "belirsiz": {
            "aday_satir_n": len(adaylar),
            "tek_yanli_satir_n": sum(1 for a in adaylar if not a["etkisiz"]),
            "etkisiz_adim_satir_n": sum(1 for a in adaylar if a["etkisiz"]),
            "belirsiz_satir_n": len(belirsiz),
            "belirsiz_semboller": sorted({s for k in belirsiz
                                          for s in (k["satir"].get("etkisiz_semboller")
                                                    or [k["satir"].get("eklenen")
                                                        or k["satir"].get("cikan")]) if s}),
            "gun_max": max(belirsiz_sayilari), "gun_ort": round(
                sum(belirsiz_sayilari) / len(belirsiz_sayilari), 4),
            "tavan_asan_gun_n": len(belirsiz_asan), "tavan_asan": belirsiz_asan[:20]},
        "esleme": {"karar_sayimi": karar_sayimi, "kayit_n": len(tablo),
                   "kaynak": ("dosyadan okundu" if esleme_tablosu is not None
                              else "mekanik öneri (yeniden üretildi)"),
                   "gun_penceresi": ESLEME_GUN_PENCERESI,
                   "uygulanan_esleme_n": esleme_raporu["uygulanan_esleme_n"],
                   "uygulanmayan_esleme": esleme_raporu["uygulanmayan_esleme"],
                   "dusurulen_satir_n": esleme_raporu["dusurulen_satir_n"],
                   "esle_kararlari": sorted(k["karar"] for k in tablo
                                            if str(k.get("karar", "")).startswith("esle:")),
                   "jeton_sozlugu": {
                       "esle:<eski>-><yeni>": ("YENİDEN ADLANDIRMA KİMLİĞİ — kararın bağlı olduğu "
                                               "satırda sembol yeniden yazılır (UYGULANIR)"),
                       "cift:<cikan>-><giren>": ("İKİ YARIM SATIR aynı endeks olayı — ANOTASYON, "
                                                 "değişiklik listesi DEĞİŞMEZ"),
                       "dusur": "satır değişiklik listesinden ÇIKARILIR",
                       "belirsiz": "karar YOK — sembol o tarihten önceki günlerde belirsiz sayılır"}},
        "cok_sembollu_hucre": {
            **{a: bolme[a] for a in ("bolunen_n", "bolunen", "bolunemeyen_n", "bolunemeyen",
                                     "ayirac_deseni", "ham_satir_n", "bolunmus_satir_n")},
            "csv_ayirac_tasiyan_satir_n": ayirac_satir_n,
            "csv_ayirac_tasiyan_semboller": ayirac_tasiyan,
            "kural": ("`X/Y` (ve `X, Y`) hücresi AYRI sembollere bölünür — S&P endeksleri bir "
                      "şirketin iki hisse sınıfını AYRI bileşen sayar; kaynak tablonun KENDİ "
                      "hücresi. Parçalardan biri ticker biçiminde değilse hücre BÖLÜNMEZ ve "
                      "`bolunemeyen`de ADIYLA durur")},
        "pit_pk": pk,
        "guncel_liste": {"n": len(guncel), "kart_beyan_olay_n": kart_beyan_n,
                         "olay_normalizasyonu": normalizasyon},
        "kapi": {"gecti": kapi_gecti,
                 "boyut_bandi_gecti": not bant_disi,
                 "belirsiz_tavani_gecti": not belirsiz_asan},
        "csv_sha256": hashlib.sha256(metin.encode("utf-8")).hexdigest(),
        "hukum": "YOK — Rol-1",
        "beyan": ("ağa ÇIKILMADI (bütün girdiler yereldeki donmuş blob'lar; olc.cek() çağrılmadı) · "
                  "`meridian` İTHAL EDİLMEDİ · canlı state/'e YAZILMADI · karta DOKUNULMADI "
                  "(CLAUDE.md §3/§5)"),
    }, metin, tablo


# ======================================================================================
# YAZIM
# ======================================================================================

def esleme_yaml_metni(tablo: list[dict], kart_id: str | None) -> str:
    basli = (
        f"# {kart_id} ADIM-0 EKSEN A — S&P 400 değişiklik tablosunun ADAY satırlarının kararları.\n"
        "#\n"
        "# ÜRETİLMİŞ DOSYA — ELLE DÜZENLENMEZ. Üretici (`research/olcumler/edg093_midcap_pit/\n"
        "# kohort.py`) her `--uygula` koşumunda bu dosyayı YENİDEN ÜRETİR; kararlar tablonun KENDİ\n"
        "# gerekçe hücresinden MEKANİK olarak türetilir (tek-kaynak). Elle düzenlenmiş bir karar\n"
        "# tablosu koşuma `--esleme <yol>` ile AÇIK yoldan verilir; şema kapısı onu da korur.\n"
        "#\n"
        "# ADAY SATIR İKİ KAYNAKTAN gelir: (a) pencere içindeki TEK YANLI tablo satırları,\n"
        "# (b) geri sarmada ETKİSİZ adım üreten satırlar (`satir.etkisiz_adimlar`).\n"
        "#\n"
        "# `karar` SÖZLÜĞÜ (dışındaki değer REDDEDİLİR):\n"
        "#   esle:<eski>-><yeni>  YENİDEN ADLANDIRMA KİMLİĞİ — bu satırdaki <eski> sembolü bugünkü\n"
        "#                        <yeni> ile AYNI ihraçtır; as-of yürütmesinde UYGULANIR (satır\n"
        "#                        <yeni> ile yazılır). Yalnız gerekçe hücresi yeniden adlandırmayı\n"
        "#                        AÇIKÇA söylediğinde (sözlük + borsa parantezinde sembol) önerilir.\n"
        "#   cift:<cikan>-><giren>  İKİ YARIM SATIR aynı endeks değişiminin iki kitaplamasıdır\n"
        "#                        (ANOTASYON — değişiklik listesi ve tarihler DEĞİŞMEZ).\n"
        "#   dusur                satır tabloda hatalı kitaplanmış; değişiklik listesinden ÇIKARILIR.\n"
        "#   belirsiz             karar YOK — sembol o tarihten ÖNCEKİ günlerde 'belirsiz' sayılır.\n"
        "#\n"
        "# `gerekce` tablonun KENDİ Reason/<ref> hücresinden alınır; ağa ÇIKILMAZ, metin UYDURULMAZ.\n"
        "# MDY güncel listesindeki varlık/yokluk TANIdır, karar gerekçesi OLAMAZ (tek kaynak tablo).\n"
        "# `kaynak.wikitext_satir_no` ayrıştırılmış tablo satır indeksidir (ham wikitext sha'sı sonuç\n"
        "# JSON'unun `girdi_kimligi` alanında); `satir.alt_no` çok-sembollü hücrenin alt indeksidir.\n")
    return basli + yaml.safe_dump(tablo, allow_unicode=True, sort_keys=False, width=100)


def yaz(cikti_koku: pathlib.Path, sonuc: dict, csv_metin: str, tablo: list[dict]) -> dict:
    """Üç çıktıyı yazar ve yazılan yolları döndürür. ÜÇÜ DE ÜRETİCİ ÇIKTISIDIR ve her koşumda
    YENİDEN ÜRETİLİR (üretilmiş dosya elle düzenlenmez — düzenlenmiş tablo `--esleme` ile verilir);
    yalnız sonuç JSON'u damgalı olduğu için önceki koşumların JSON'ları YERİNDE KALIR."""
    cikti_koku = pathlib.Path(cikti_koku)
    csv_yolu = cikti_koku / CSV_GORECELI
    esleme_yolu = cikti_koku / ESLEME_GORECELI
    sonuc_yolu = cikti_koku / SONUC_DIZIN_GORECELI / f"adim0a_sonuc_{sonuc['damga']}.json"
    for y in (csv_yolu, esleme_yolu, sonuc_yolu):
        y.parent.mkdir(parents=True, exist_ok=True)

    csv_yolu.write_text(csv_metin, encoding="utf-8")
    esleme_yolu.write_text(esleme_yaml_metni(tablo, sonuc.get("kart_id")), encoding="utf-8")
    esleme_durumu = ("yeniden üretildi (dosyadan okunan tablo)"
                     if sonuc["esleme"]["kaynak"] == "dosyadan okundu"
                     else "yeniden üretildi (mekanik öneri)")
    sonuc = dict(sonuc)
    sonuc["cikti"] = {
        "csv": {"yol": str(csv_yolu), "sha256": sha256_dosya(csv_yolu)},
        "elle_esleme": {"yol": str(esleme_yolu), "sha256": sha256_dosya(esleme_yolu),
                        "durum": esleme_durumu},
        "sonuc_json": {"yol": str(sonuc_yolu)}}
    sonuc_yolu.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
    return sonuc


def ozet_satirlari(sonuc: dict) -> list[str]:
    k, b, p = sonuc["kohort"], sonuc["belirsiz"], sonuc["pit_pk"]
    return [
        f"kart            : {sonuc['kart_id']} · {sonuc['adim']} · damga {sonuc['damga']}",
        f"pencere         : {sonuc['pencere']['bas']} → {sonuc['pencere']['son']} "
        f"({sonuc['pencere']['gun_n']} takvim günü)",
        f"tablo           : geçerli satır {sonuc['tablo_meta']['satir_n_gecerli']} · "
        f"tarihi çözülemeyen {sonuc['tablo_meta']['tarih_cozulemeyen_n']}",
        f"kohort boyutu   : min {k['boyut_min']} · ort {k['boyut_ort']} · max {k['boyut_max']} "
        f"(bant {sonuc['esikler']['kohort_boyut_bant']}) · bant dışı gün {k['bant_disi_gun_n']}",
        f"boyut dağılımı  : {k['boyut_dagilimi']}",
        f"sapma tanısı    : güncel {k['fazlalik_tanisi']['guncel_n']} · etkili ekleme "
        f"{k['fazlalik_tanisi']['ekle_etkili']} · etkili çıkarma {k['fazlalik_tanisi']['discard_etkili']} "
        f"· ETKİSİZ ekle {k['fazlalik_tanisi']['ekle_etkisiz']} / discard "
        f"{k['fazlalik_tanisi']['discard_etkisiz']} → as_of(bas) {k['fazlalik_tanisi']['as_of_n']}",
        f"csv             : {k['csv_satir_n']} satır · sha256 {sonuc['csv_sha256'][:16]}…",
        f"çok-sembol      : bölünen hücre {sonuc['cok_sembollu_hucre']['bolunen_n']} · "
        f"bölünemeyen {sonuc['cok_sembollu_hucre']['bolunemeyen_n']} · csv'de ayıraç taşıyan satır "
        f"{sonuc['cok_sembollu_hucre']['csv_ayirac_tasiyan_satir_n']}",
        f"aday satır      : {b['aday_satir_n']} (tek yanlı {b['tek_yanli_satir_n']} · etkisiz adım "
        f"{b['etkisiz_adim_satir_n']}) · kararlar {sonuc['esleme']['karar_sayimi']}",
        f"uygulanan esleme: {sonuc['esleme']['uygulanan_esleme_n']} "
        f"{sonuc['esleme']['esle_kararlari']} · uygulanmayan "
        f"{sonuc['esleme']['uygulanmayan_esleme']}",
        f"belirsiz isim   : gün max {b['gun_max']} · ort {b['gun_ort']} "
        f"(tavan {sonuc['esikler']['belirsiz_isim_gun_ust']}) · tavanı aşan gün {b['tavan_asan_gun_n']}",
        f"PIT-PK          : {p['gecti_n']}/{p['ornek_n']} geçti · ölçülemedi {p['olculemedi_n']} "
        f"· tohum {p['tohum_adi']}={p['tohum']}",
        f"KAPI            : {'GEÇTİ' if sonuc['kapi']['gecti'] else 'DÜŞTÜ'} "
        f"(boyut {sonuc['kapi']['boyut_bandi_gecti']} · belirsiz {sonuc['kapi']['belirsiz_tavani_gecti']})",
        f"hüküm           : {sonuc['hukum']}",
    ]


def main(argv: list[str] | None = None) -> int:
    ayristirici = argparse.ArgumentParser(
        description="EDG-2026-093 ADIM-0 A — S&P 400 PIT kohort üreticisi")
    kip = ayristirici.add_mutually_exclusive_group(required=True)
    kip.add_argument("--kuru", action="store_true", help="yalnız sayıları bas, dosya YAZMA")
    kip.add_argument("--uygula", action="store_true", help="çıktıları yaz (--cikti zorunlu)")
    ayristirici.add_argument("--cikti", help="çıktı kökü (depo kökü gibi davranır)")
    ayristirici.add_argument("--ham", default=str(HAM_VARSAYILAN),
                             help="ham wikitext (.gitignore'lu — worktree'de yoksa açık yol ver)")
    ayristirici.add_argument("--xlsx", default=str(XLSX_VARSAYILAN))
    ayristirici.add_argument("--kart", default=str(KART093_YOLU))
    ayristirici.add_argument("--kart092", default=str(KART092_YOLU))
    ayristirici.add_argument("--esleme", default=None,
                             help="elle düzenlenmiş karar tablosu YAML'ı (verilmezse tablo mekanik "
                                  "olarak YENİDEN ÜRETİLİR; çıktıdaki dosya GİRDİ DEĞİLDİR)")
    ayristirici.add_argument("--bugun", default=None, help="ISO tarih (varsayılan: bugün, UTC)")
    ayristirici.add_argument("--beklenen-sha", default=None,
                             help="ham wikitext beklenen sha256 (varsayılan: ham_SHA256.txt)")
    ayristirici.add_argument("--ham-sha-kaydi", default=str(HAM_SHA_KAYDI))
    ayristirici.add_argument("--xlsx-sha-kaydi", default=str(XLSX_SHA_KAYDI))
    a = ayristirici.parse_args(argv)
    if a.uygula and not a.cikti:
        ayristirici.error("--uygula için --cikti zorunlu")

    try:
        ham_beklenen = a.beklenen_sha or sha_kaydindan(pathlib.Path(a.ham_sha_kaydi),
                                                       pathlib.Path(a.ham).name)
        ham_sha = sha_kapisi(pathlib.Path(a.ham), ham_beklenen, "ham wikitext")
        xlsx_beklenen = sha_kaydindan(pathlib.Path(a.xlsx_sha_kaydi), pathlib.Path(a.xlsx).name)
        xlsx_sha = sha_kapisi(pathlib.Path(a.xlsx), xlsx_beklenen, "MDY holdings xlsx")
    except GirdiHatasi as e:
        print(f"DURDU (sha kapısı): {e}", file=sys.stderr)
        return 2

    kart093 = OLC.kart_yukle(pathlib.Path(a.kart))
    kart092 = OLC.kart_yukle(pathlib.Path(a.kart092))
    bugun = a.bugun or dt.datetime.now(dt.timezone.utc).date().isoformat()

    # Karar tablosu YALNIZ `--esleme` ile AÇIK yoldan okunur. Çıktı dizinindeki dosya ÜRETİCİ
    # ÇIKTISIDIR — onu geri okumak, bir sonraki koşumun kendi ürettiği (belki eski sözlükle
    # yazılmış) kararları girdi sanmasına yol açardı; tek-kaynak yasasının klasik ayrışması.
    mevcut = None
    if a.esleme:
        esleme_yolu = pathlib.Path(a.esleme)
        if not esleme_yolu.exists():
            print(f"DURDU (girdi): --esleme dosyası yok — {esleme_yolu}", file=sys.stderr)
            return 2
        mevcut = yaml.safe_load(esleme_yolu.read_text(encoding="utf-8"))

    try:
        sonuc, csv_metin, tablo = olc(pathlib.Path(a.ham), pathlib.Path(a.xlsx), kart093, bugun,
                                      ham_sha, xlsx_sha, kart092, esleme_tablosu=mevcut)
    except GirdiHatasi as e:
        print(f"DURDU (girdi/şema): {e}", file=sys.stderr)
        return 2

    if a.uygula:
        sonuc = yaz(pathlib.Path(a.cikti), sonuc, csv_metin, tablo)

    for satir in ozet_satirlari(sonuc):
        print(satir)
    if a.uygula:
        for ad, kayit in sonuc["cikti"].items():
            print(f"yazıldı[{ad}] : {kayit['yol']}")
    else:
        print("kuru koşum      : hiçbir dosya YAZILMADI")
    return 0 if sonuc["kapi"]["gecti"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
