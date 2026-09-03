"""EDG-2026-021 ⑤ — QC Security Master DELİST SONDASI (8 emekli sembol) · TEK HÜCRE.

NE SORAR: QuantConnect Research'te (FREE hesap) sekiz emekli sembolün delist OLAYINA
erişilebiliyor mu, erişiliyorsa tarihi ne? Cevap `research/qc_dogrulama/
wp-qc-5-retired-caprazdogrulama-2026-08-09.md`nin bıraktığı TEK açık adımdır: Massive
otoritesi 8'in 7'sini doğruladı, PARA'da boşluk kaldı (Massive `active=false` 0 kayıt).

NE BASMAZ: yerel tarihleri. Bu dosya QC'nin CEVABINI basar; kıyas YERELDE yapılır —
`python research/qc_dogrulama/qc_sonda_delist_8_kiyas.py --qc <json>`. Tek-kaynak yasası:
yerel tarih tablosu koddan/belgeden OKUNUR, buraya elle kopyalanmaz.

API ZEMİNİ — ÖLÇÜLDÜ (QC belgeleri, 2026-09-03, salt-okunur WebFetch):
  · `Delisting` sınıfı VARDIR: `type` (DelistingType.WARNING/DELISTED), `time`, `symbol`;
    algoritmada `slice.delistings` ile teslim edilir.
  · Delisting'in HISTORY isteğiyle çekilebildiği QC belgesinde YAZMIYOR ("Unlike splits and
    dividends, the documentation does not indicate that Delisting objects can be retrieved
    through history requests"). Yani Yol-1 bir VARSAYIM DEĞİL, bir ÖLÇÜMdür: dener ve sonucu
    (istisna metni dahil) basar.
  · `qb.history[DataType](symbol, ...)` ve `qb.history(DataType, symbol, ...)` biçimleri
    belgelidir (tip parametresi TradeBar/QuoteBar/Tick/özel sınıf için gösterilmiş).
  · `symbol.value` = NOKTA-ZAMANLI ticker · `symbol.id.date` = hisse için EN ERKEN LİSTELENME
    tarihi (delist DEĞİL — bu ayrım JSON'da beyanlıdır).

ÜÇ YOL — ilk ikisi delist OTORİTESİ arar, üçüncüsü açıkça VEKİLDİR:
  Yol-1  `qb.history(Delisting, sym, t0, t1)` ve `qb.history[Delisting](sym, t0, t1)`
  Yol-2  sembol/security özellikleri (`id.date`, `is_delisted`/`delisted`/`delisting` taraması)
  Yol-3  SON BAR tarihi (`qb.history(sym, t0, t1, DAILY)` son satırı) — VEKİLDİR: delist'i veri
         kesintisinden ayıramaz, `qc_delist_tarihi` alanına ASLA yazılmaz.

`qc_delist_tarihi` YALNIZ Yol-1/Yol-2 bir delist OLAYI verirse dolar; yoksa None + neden
(uydurma yasağı — vekil "delist tarihi" diye raporlanmaz).

KOŞUM: QC Research'te tek hücre —
    exec(open("qc_sonda_delist_8.py").read(), globals())
Çıktıyı `<<<SONDA_DELIST_JSON_BASLANGIC>>>` / `<<<SONDA_DELIST_JSON_SON>>>` arasından kopyala,
`research/olcumler/qc_dogrulama/sonda_delist_8.json` olarak kaydet.
"""

# %%
from datetime import datetime

import json

from AlgorithmImports import *

SONDA_SEMBOLLER = ("ANSS", "DFS", "FI", "HES", "IPG", "K", "PARA", "WBA")

# Pencere: sekizinin de delist'i 2025 içindedir; iki uçta bol tampon bırakıldı.
SONDA_BAS = datetime(2024, 1, 1)
SONDA_SON = datetime(2026, 7, 31)

# ticker → Symbol çözümü için ÇÖZÜM TARİHİ. Sekizi de bu tarihte işlem görüyordu; yalnız
# eşleme (map-file) çapasıdır, KIYASA GİRMEZ ve delist tarihi olarak kullanılmaz.
COZUM_TARIHI = datetime(2025, 1, 2)

_RES = getattr(Resolution, "DAILY", None) or getattr(Resolution, "Daily")
QB_SONDA = QuantBook()          # TAZE ve AYRI: defterin QB_PANEL/QB_BAR örneklerine dokunmaz

SONDA = {
    "sonda": "EDG-2026-021 ⑤ QC Security Master delist sondası",
    "surum": "1.0",
    "kosum": {"zaman_utc": str(datetime.utcnow()) + "Z",
              "ortam": "QuantConnect Research (QuantBook)",
              "qb": "TAZE QuantBook() — yalnız bu sonda için, paylaşılmaz",
              "pencere": [str(SONDA_BAS.date()), str(SONDA_SON.date())],
              "cozum_tarihi": str(COZUM_TARIHI.date())},
    "beyan": {
        "rol": "SAYI/OLGU üretir, hüküm vermez; yerel kıyas ayrı betikte (qc_sonda_delist_8_"
               "kiyas.py). Bu JSON yerel tarih TAŞIMAZ.",
        "id_tarihi": "symbol.id.date = EN ERKEN LİSTELENME tarihi (QC belgesi) — DELİST DEĞİL.",
        "son_bar_vekili": "son_bar_tarihi bir VEKİLDİR: veri kesintisi/likidite çöküşü ile "
                          "gerçek delist'i AYIRAMAZ; qc_delist_tarihi alanına yazılmaz.",
        "history_delisting": "QC belgesi Delisting'in history ile çekilebildiğini SÖYLEMİYOR; "
                             "Yol-1 bunu ölçer, varsaymaz.",
        "warning_ayrimi": "qc_delist_tarihi YALNIZ DelistingType.DELISTED olayından dolar. "
                          "WARNING olayı delist gününden bir gün ÖNCE gelir ve AYRI alana "
                          "(qc_uyari_tarihi) yazılır — aynı alana yazılsaydı kıyas sistematik "
                          "'AYRIK -1 gün' üretir, sahte otorite çelişkisi doğardı.",
    },
    "semboller": [],
    "olculemedi": [],
}


def _hata(e):
    return f"{type(e).__name__}: {e}"


def _tarih_str(x):
    try:
        return str(x)[:10]
    except Exception:
        # sessiz-yutma: yabancı runtime nesnesinin __str__'i patlayabilir; tarih ÖLÇÜLEMEDİ
        # demek None demektir ve çağıran onu None olarak raporlar (uydurma yasağı)
        return None


def _delisting_okuyucu(sonuc):
    """history dönüşünden delist OLAYLARINI çıkar: [(tarih, tip)] · tanınmazsa boş liste."""
    olaylar = []
    try:
        ogeler = list(sonuc.items()) if hasattr(sonuc, "items") else list(sonuc)
    except Exception:
        # sessiz-yutma: dönüş tipi ÖLÇÜLMEDİ (QC belgesi Delisting history'sini tanımlamıyor);
        # tanınmayan kap = "olay yok" ve çağıran bunu None + neden olarak raporlar
        return olaylar
    for oge in ogeler:
        d = oge[1] if isinstance(oge, tuple) and len(oge) == 2 else oge
        for k in (d if isinstance(d, (list, tuple)) else [d]):
            t = getattr(k, "time", None) or getattr(k, "end_time", None)
            tip = getattr(k, "type", None)
            if t is not None:
                olaylar.append({"tarih": _tarih_str(t), "tip": str(tip)})
    return olaylar


_DELIST_ALANLARI = ("is_delisted", "delisted", "delisting", "IsDelisted")

for _s_ticker in SONDA_SEMBOLLER:
    kayit = {"ticker": _s_ticker, "qc_delist_tarihi": None, "qc_uyari_tarihi": None,
             "neden": None, "yollar": {}}

    # --- sembol çözümü (iki biçim: add_equity, sonra map-file çapalı üretim) --------------
    sym = None
    try:
        _sec = QB_SONDA.add_equity(_s_ticker, _RES)
        sym = _sec.symbol
        kayit["yollar"]["add_equity"] = {"oldu": True, "sembol": str(sym),
                                         "deger": str(getattr(sym, "value", None)),
                                         "id_tarihi": _tarih_str(getattr(sym.id, "date", None))}
    except Exception as e:
        _sec = None
        kayit["yollar"]["add_equity"] = {"oldu": False, "neden": _hata(e)}
    if sym is None:
        try:
            _s_sid = SecurityIdentifier.generate_equity(_s_ticker, Market.USA,
                                                        mapping_resolve_date=COZUM_TARIHI)
            sym = Symbol(_s_sid, _s_ticker)
            kayit["yollar"]["generate_equity"] = {"oldu": True, "sembol": str(sym)}
        except Exception as e:
            kayit["yollar"]["generate_equity"] = {"oldu": False, "neden": _hata(e)}
    if sym is None:
        kayit["neden"] = "sembol ÇÖZÜLEMEDİ — delist sorgusu hiç koşmadı"
        SONDA["olculemedi"].append({"alan": f"{_s_ticker}.sembol",
                                    "neden": kayit["neden"]})
        SONDA["semboller"].append(kayit)
        continue

    # --- YOL-1: Delisting history (İKİ biçim; belgede YOK, ÖLÇÜLÜYOR) ---------------------
    olaylar = []
    for ad, cagri in (("history(Delisting, sym, t0, t1)",
                       lambda s=sym: QB_SONDA.history(Delisting, s, SONDA_BAS, SONDA_SON)),
                      ("history[Delisting](sym, t0, t1)",
                       lambda s=sym: QB_SONDA.history[Delisting](s, SONDA_BAS, SONDA_SON))):
        try:
            _r = cagri()
            _o = _delisting_okuyucu(_r)
            kayit["yollar"][ad] = {"oldu": True, "n_olay": len(_o), "olaylar": _o[:6],
                                   "tip": type(_r).__name__}
            olaylar += _o
        except Exception as e:
            kayit["yollar"][ad] = {"oldu": False, "neden": _hata(e)}

    # --- YOL-2: sembol/security özellikleri ----------------------------------------------
    ozel = {"id_tarihi": _tarih_str(getattr(getattr(sym, "id", None), "date", None)),
            "id_tarihi_beyani": "EN ERKEN LİSTELENME (QC belgesi) — delist DEĞİL"}
    for _ad in _DELIST_ALANLARI:
        for _hedef, _etiket in ((_sec, "security"), (sym, "symbol")):
            if _hedef is None:
                continue
            try:
                _v = getattr(_hedef, _ad)
            except Exception:
                # sessiz-yutma: alan taraması KEŞİFTİR — olmayan alan bulgu değildir, yokluğu
                # zaten "ozel" sözlüğünde o anahtarın BULUNMAMASIYLA raporlanır
                continue
            ozel[f"{_etiket}.{_ad}"] = (_v if isinstance(_v, (int, float, bool, str))
                                        else str(_v))
    kayit["yollar"]["ozellikler"] = ozel

    # --- YOL-3: SON BAR (VEKİL — delist tarihi DEĞİL) ------------------------------------
    try:
        _h = QB_SONDA.history(sym, SONDA_BAS, SONDA_SON, _RES)
        if _h is None or len(_h) == 0:
            kayit["yollar"]["son_bar"] = {"oldu": True, "n": 0,
                                          "neden": "bar dönmedi (delist sonrası beklenir)"}
        else:
            _idx = _h.index
            _t = [_tarih_str(x) for x in (_idx.get_level_values(-1) if hasattr(
                _idx, "get_level_values") else _idx)]
            kayit["yollar"]["son_bar"] = {"oldu": True, "n": int(len(_h)),
                                          "ilk": min(_t), "son": max(_t)}
            kayit["son_bar_tarihi_VEKIL"] = max(_t)
    except Exception as e:
        kayit["yollar"]["son_bar"] = {"oldu": False, "neden": _hata(e)}

    # --- HÜKÜM ALANI: `qc_delist_tarihi` YALNIZ DelistingType.DELISTED olayından ---------
    # WARNING olayı delist gününden BİR GÜN ÖNCE gelir. Onu bu alana yazmak, kıyasta sistematik
    # "AYRIK −1 gün" üretir ve wp-qc-5'in çakışma-istisnasını SAHTE tetiklerdi. Ayrım
    # `son_bar_tarihi_VEKIL` deseninin aynısıdır: farklı şey, farklı alan.
    _delisted = [o for o in olaylar if "DELISTED" in str(o.get("tip", "")).upper()]
    _uyari = [o for o in olaylar if o not in _delisted]
    if _uyari:
        kayit["qc_uyari_tarihi"] = sorted(o["tarih"] for o in _uyari if o["tarih"])[-1]
        kayit["uyari_olay_sayisi"] = len(_uyari)
    if _delisted:
        kayit["qc_delist_tarihi"] = sorted(o["tarih"] for o in _delisted if o["tarih"])[-1]
        kayit["neden"] = None
        kayit["delist_olay_sayisi"] = len(_delisted)
    else:
        kayit["qc_delist_tarihi"] = None
        kayit["neden"] = (
            ("Delisting olayı geldi ama tipi DELISTED DEĞİL (WARNING) — tarih "
             "qc_uyari_tarihi'ne yazıldı; WARNING delist gününden bir gün ÖNCE gelir, "
             "delist tarihi DEĞİLDİR")
            if _uyari else
            ("Delisting olayı ALINAMADI (Yol-1 iki biçimde de olay vermedi, Yol-2 delist "
             "alanı göstermedi) — son_bar_tarihi VEKİLDİR, delist tarihi DEĞİLDİR"))
        SONDA["olculemedi"].append({"alan": f"{_s_ticker}.qc_delist_tarihi",
                                    "neden": kayit["neden"]})
    SONDA["semboller"].append(kayit)
    print(f"   {_s_ticker}: qc_delist={kayit['qc_delist_tarihi']} "
          f"uyari={kayit.get('qc_uyari_tarihi')} "
          f"son_bar_VEKIL={kayit.get('son_bar_tarihi_VEKIL')} neden={kayit['neden']}", flush=True)

SONDA["ozet"] = {
    "sembol": len(SONDA["semboller"]),
    "qc_delist_alinan": sum(1 for k in SONDA["semboller"] if k["qc_delist_tarihi"]),
    "yalniz_uyari": sum(1 for k in SONDA["semboller"]
                        if not k["qc_delist_tarihi"] and k.get("qc_uyari_tarihi")),
    "yalniz_vekil": sum(1 for k in SONDA["semboller"]
                        if not k["qc_delist_tarihi"] and k.get("son_bar_tarihi_VEKIL")),
    "hicbir_sey": sum(1 for k in SONDA["semboller"]
                      if not k["qc_delist_tarihi"] and not k.get("son_bar_tarihi_VEKIL")),
}

print("\n" + "=" * 78)
print("EDG-2026-021 ⑤ · SONDA JSON — işaretler ARASINDAKİ metni kopyala")
print("kaydet: research/olcumler/qc_dogrulama/sonda_delist_8.json")
print("=" * 78)
print("<<<SONDA_DELIST_JSON_BASLANGIC>>>")
print(json.dumps(SONDA, ensure_ascii=False, indent=2, sort_keys=False, default=str))
print("<<<SONDA_DELIST_JSON_SON>>>")
print("=" * 78)
print("SONDA SONU ·", SONDA["ozet"])
