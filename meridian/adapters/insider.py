"""adapters/insider.py — Form 4 (içeriden işlem) verisi: FMP insider-trading akışından artımlı
defter + Cohen–Malloy–Pomorski (2012) rutin/fırsatçı sınıflaması.

(a) Ne yapar: FMP stable'ın `insider-trading/latest` akışını (piyasa geneli — maliyet evren
boyundan BAĞIMSIZ: sembol başına değil sayfa başına istek) artımlı tarar, REPLAY_UNIVERSE
kesişimini ham deftere işler ve sembol-başına özet skor üretir. `insider-trading/search` (sembol
başına geçmiş) ücretsiz FMP planında HTTP 402 döner (kota değil PLAN sınırı — canlı ölçüldü; aynı
sondayla limit>100 ve page>=1 de 402, `date=` sessizce yok sayılıyor); `--gecmis` yolu 402'yi
dürüstçe raporlar, plan yükselirse çalışır. Rotasyon/kota/maskeleme/muhasebe adapters/fmp.py'den
gelir. Rol: evrene onay/tilt katmanı HAZIRLAMAK, karar vermek değil.
(b) Kilit girişler: fetch_delta() (su işaretine yetişince duran artımlı tarama; `tavana_carpti`
yarım kalışı görünür kılar), gecmis_cek(), ozet() (ağ yok), siniflandir(), yon_coz(), durum(),
health(); CLI: --fetch/--gecmis/--ozet/--durum.
(c) Değişmezler — UYDURMA YASAĞI bu dosyanın en önemli satırıdır: CMP basitleştirmesinde RUTİN =
aynı kişi+sembol işlemin takvim ayında önceki 3 yılın HER BİRİNDE de işlem yapmış; FIRSATÇI =
pencere kapsanıyor ama koşul sağlanmıyor; SINIFLANAMADI = defter o pencereye BAKAMIYOR. Veri
yokluğunu fırsatçılık saymak taze defterdeki her işlemi sinyal ilan ederdi — kapsam yoksa cevap
SINIFLANAMADI'dır ve özet bunu ayrı sayar. YÖN disiplini: "iktisap" ≠ "açık piyasa alımı"; nete
yalnız işlem kodu P (alım) ve S (satım) girer, ödül/icra/stopaj/bağış `diger`, okunamayan kod
`bilinmiyor`. Alan eşlemesi takma-ad haritasıyla toleranslıdır ama sessiz değildir: eşlenemeyen ham
alanlar `alan_teshis.eslesmeyen_alanlar`a yazılır (şema sürüklenmesi adıyla görünür).
(d) Okur/yazar: state/insider_trades.json (ham defter; su işareti + kapsam_sembol) ve
state/insider_signals.json (özet) — İKİSİNİN DE TEK YAZARI bu CLI'dır; canlı worker bu dosyalara
dokunmaz, yazım store.write_json ile atomiktir. Okuyucusuz-yazım yasağına BEYANLI ERTELEME: bugünkü
tek tüketici CLI + testler; loop/api bağlantısı defter 3 yıllık kapsama ulaşana dek bilinçli olarak
bekletilir (hazırlık ölçüsü: `kapsam.siniflama_hazir_mi`)."""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import sys

LEDGER_FILE = "insider_trades.json"     # ham defter — TEK YAZAR: bu CLI
SIGNAL_FILE = "insider_signals.json"    # özet skor  — TEK YAZAR: bu CLI

VARSAYILAN_GUN = 30          # --fetch penceresi (gün)
VARSAYILAN_OZET_GUN = 90     # --ozet penceresi (gün) — CMP tarzı "son çeyrek" birikimi
GECMIS_YIL = 3               # sınıflama için gereken geçmiş yıl sayısı
SAYFA_LIMIT = 100            # FMP sayfa boyu — ÜCRETSİZ PLANIN TAVANI (limit>100 → 402, aşağıya bak)
VARSAYILAN_SAYFA_TAVANI = 40 # soğuk koşuda kotayı bölmek için (ÜCRETLİ plan varsayımı — bkz. aşağı)
DEFTER_TAVANI = 60_000       # defter satır tavanı (en yenileri tutulur) — dosya sınırsız büyümesin

# ---- ÜCRETSİZ PLANIN ÖLÇÜLMÜŞ SINIRLARI (Rol 1 canlı sondajı) ------------------------
# TAHMİN DEĞİL, SONDA: dört sınır da canlı istekle doğrulandı. Buraya yazılmalarının sebebi, otonom
# kadansın tavanını BU DOSYADAN türetmesi — sayı çağıranda sabitlenirse iki yerde iki tavan olur ve
# biri güncellenmez (bu deponun tekrar eden hatası).
#   * `insider-trading/search?symbol=…`  → HTTP 402 (PLAN sınırı, kota değil — `/latest` aynı
#     anahtarla 200 veriyordu). `--gecmis` yolu bu planda ölü; kaldırılmadı, plan yükselince çalışır.
#   * `limit > 100`                      → HTTP 402. Yani `SAYFA_LIMIT` tesadüfen değil, TAVANDA.
#   * `page >= 1`                        → HTTP 402. **SAYFALAMA BU PLANDA YOK**: yalnız `page=0`
#     çalışıyor. Otonom kadans bu yüzden `PLAN_SAYFA_TAVANI` kullanır; `sayfa>0` DENENMEZ, çünkü her
#     deneme garantili bir 402'dir — kota yakar, satır getirmez.
#   * `date=` parametresi                → SESSİZCE YOK SAYILIYOR (200 + günün verisi). Yani tarih
#     penceresini sunucuya YAPTIRAMAYIZ; pencere YEREL olarak süzülür (fetch_delta zaten öyle yapar).
#     Bu, "parametre kabul edildi" ile "parametre uygulandı"nın ayrı şeyler olduğunun canlı örneği.
PLAN_SAYFA_TAVANI = 1        # ücretsiz planda ÇALIŞAN tek sayfa: page=0
#
# "GÜNLÜK BİRİKTİRMEYLE 3 YIL DOLAR" — ÖLÇÜLMEMİŞ BİR UMUTTUR (dürüstlük düzeltmesi).
# Bu dosyanın başlığı ve `codelaw.DECLARED_SINKS`teki erteleme gerekçesi, sınıflama penceresinin
# `/latest` akışının günlük birikmesiyle dolacağını söylüyor. O cümle bir ÖLÇÜM değil bir UMUTTU ve
# Rol 1'in sondası neden şüpheli olduğunu gösterdi: günde TEK sayfa = en yeni ~100 dosyalama ve
# evren isabeti ~6/100 ölçüldü. Yani günlük kazanım ~6 satır ve bunlar GEÇMİŞE değil BUGÜNE ait —
# `latest` akışı geriye doğru derinleşmez, ileriye doğru akar. 3 yıllık geçmiş penceresi bu yoldan
# ancak 3 yıl BEKLEYEREK dolar. Kadans yine de koşar (biriken ileri pencere gerçek ve ücretsizdir),
# ama "ne zaman bağlanabiliriz?" sorusunun cevabı `kapsam.siniflama_hazir_mi` ALANIDIR — bu cümle
# değil. Gerçek kısayol FMP planını yükseltmektir (`search` ucu açılır).

# --- ALAN EŞLEMESİ (FMP stable insider-trading sözleşmesi) --------------------------------------
# Her kanonik alan için ADAY ham anahtarlar, ÖNCELİK SIRASIYLA. Tolerans BİLİNÇLİ ve SINIRLI:
# sağlayıcı bir alanı yeniden adlandırırsa satır sessizce boş kalmasın diye yakın eşanlamlılar
# denenir; hiçbiri tutmazsa alan None kalır ve ham anahtar `eslesmeyen_alanlar`a düşer.
ALAN_ADAYLARI: dict[str, tuple[str, ...]] = {
    "sembol":        ("symbol", "ticker"),
    "filing_tarihi": ("filingDate", "filedDate", "filing_date"),
    "islem_tarihi":  ("transactionDate", "transaction_date", "date"),
    "kisi":          ("reportingName", "reportingCik", "insiderName", "name"),
    "unvan":         ("typeOfOwner", "officerTitle", "relationship"),
    "islem_kodu":    ("transactionType", "transactionCode", "acquistionOrDisposition"),
    "adet":          ("securitiesTransacted", "shares", "transactionShares"),
    "fiyat":         ("price", "transactionPricePerShare", "pricePerShare"),
    "kalan":         ("securitiesOwned", "sharesOwnedFollowingTransaction"),
    "yon_bayragi":   ("acquisitionOrDisposition", "acquistionOrDisposition", "acquiredDisposed"),
}
# Sağlayıcının verdiği ama kanonik satıra girmeyen, BİLİNEN ve zararsız alanlar (canlı yanıttan
# doğrulandı). Teşhis bunları "bilinmeyen alan" saymaz.
_BEKLENEN_EKSTRA = {"link", "url", "securityName", "formType", "companyCik", "reportingCik",
                    "totalValue", "directOrIndirect"}
# TEŞHİSİN ÖLÇTÜĞÜ ŞEY: ŞEMA SÜRÜKLENMESİ (tanımadığımız BİR ALAN ADI) — "bilinen alan ama bu
# satırda boş" DEĞİL. İkisi ayrılmazsa teşhis her koşuda dolu görünür, kurt masalına döner ve
# gerçek sürüklenme geldiğinde kimse bakmaz. (Canlı ilk koşuda tam bu oldu: `transactionType`
# bazı satırlarda boş olduğu için "eşlenmeyen" listesine düşüyordu — oysa eşleme DOĞRUydu.)
_BILINEN_ANAHTARLAR = {a for adaylar in ALAN_ADAYLARI.values() for a in adaylar} | _BEKLENEN_EKSTRA

_HEALTH: dict = {"ok": None, "calls": 0, "fails": 0, "last_error": "", "at": None,
                 "last_path": None, "rows": 0}


def health() -> dict:
    return dict(_HEALTH)


# ------------------------------------------------------------------ yardımcılar
def _simdi() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def _store():
    from .. import store
    return store


def _universe() -> list[str]:
    """REPLAY_UNIVERSE — canlı evren. Geç import: data.py ağır (pandas) ve döngüsel bağımlılık riski."""
    from . import data
    return list(data.REPLAY_UNIVERSE)


def _iso(v) -> str | None:
    """Sağlayıcının tarih alanını ISO `YYYY-MM-DD`ye indirger. Ayrıştırılamayan tarih None'dır —
    'bugün' varsayılmaz: uydurulmuş bir tarih, işlemi yanlış aya (dolayısıyla yanlış sınıfa) atardı."""
    if not v:
        return None
    s = str(v)[:10]
    try:
        _dt.date.fromisoformat(s)
        return s
    except ValueError:  # sessiz-yutma: biçimsiz TEK tarih alanı; satır başına uyarı 100 satırlık sayfada log seli olurdu ve KAYIP zaten görünür — çağıran None'ı 'düşen satır' olarak SAYAR (rapor.dusen) ve teşhis defterine yazar
        return None


def _sayi(v) -> float | None:
    if v is None or v == "":
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):  # sessiz-yutma: sağlayıcının sayısal alanı biçimsiz; None 'ölçülemedi'nin dürüst temsilidir (0.0 yazmak ödül satırını bedelsiz alım gibi gösterirdi) ve özet `tutari_bilinmeyen_n` ile bunu AYRI sayar
        return None
    return f if f == f and abs(f) != float("inf") else None


def yon_coz(islem_kodu, yon_bayragi) -> str:
    """Form 4 işlem kodundan YÖN. 'İktisap' ≠ 'açık piyasa alımı' — bkz. modül docstring'i.

    alim  : kod P (P-Purchase) — yönetici parayla aldı
    satim : kod S (S-Sale)     — yönetici sattı
    diger : A/M/F/G/... ödül, opsiyon icrası, vergi stopajı, bağış — nete GİRMEZ
    bilinmiyor : kod okunamadı — nete GİRMEZ, ayrı sayılır
    """
    kod = str(islem_kodu or "").strip().upper()
    if not kod:
        # Yalnız A/D bayrağı var: iktisap mı elden çıkarma mı biliyoruz ama TÜRÜNÜ bilmiyoruz.
        # Ödülü alımdan ayıramadığımız için nete sokmak yanlış olurdu.
        return "bilinmiyor" if not str(yon_bayragi or "").strip() else "diger"
    bas = kod[0]
    if bas == "P":
        return "alim"
    if bas == "S":
        return "satim"
    if bas in ("A", "M", "F", "G", "C", "D", "I", "J", "K", "L", "U", "W", "X", "Z", "H"):
        return "diger"
    return "bilinmiyor"


def _kanonik(ham: dict) -> tuple[dict | None, set[str]]:
    """Ham FMP satırı → kanonik satır + EŞLENEMEYEN ham anahtar kümesi (teşhis için).
    Sembol ya da işlem tarihi yoksa satır DÜŞER (anahtarlanamaz, aya atanamaz)."""
    if not isinstance(ham, dict):
        return None, set()
    bilinmeyen = set(ham) - _BILINEN_ANAHTARLAR      # yalnız ŞEMA SÜRÜKLENMESİ
    out: dict = {}
    for kanon, adaylar in ALAN_ADAYLARI.items():
        for a in adaylar:
            if a in ham and ham[a] not in (None, ""):
                out[kanon] = ham[a]
                break
        else:
            out[kanon] = None
    sembol = str(out.get("sembol") or "").strip().upper()
    islem_tarihi = _iso(out.get("islem_tarihi"))
    if not sembol or not islem_tarihi:
        return None, bilinmeyen
    adet = _sayi(out.get("adet"))
    fiyat = _sayi(out.get("fiyat"))
    satir = {
        "sembol": sembol,
        "islem_tarihi": islem_tarihi,
        "filing_tarihi": _iso(out.get("filing_tarihi")),
        "kisi": str(out.get("kisi") or "").strip() or None,
        "unvan": str(out.get("unvan") or "").strip() or None,
        "islem_kodu": str(out.get("islem_kodu") or "").strip() or None,
        "yon": yon_coz(out.get("islem_kodu"), out.get("yon_bayragi")),
        "adet": abs(adet) if adet is not None else None,
        "fiyat": fiyat,
        "kalan_adet": _sayi(out.get("kalan")),   # işlem SONRASI elde kalan — bağlam, nete girmez
    }
    # TUTAR TÜRETİLİR, UYDURULMAZ: fiyat yoksa None kalır (0.0 değil — sıfır "bedelsiz" demektir
    # ve ödül satırlarıyla karışırdı).
    satir["tutar"] = (satir["adet"] * fiyat) if (satir["adet"] is not None and fiyat) else None
    satir["anahtar"] = _anahtar(satir)
    return satir, bilinmeyen


def _anahtar(s: dict) -> str:
    """Satır kimliği — artımlı birleştirmenin tekilliği buna dayanır. Sağlayıcı aynı dosyalamayı
    farklı sayfalarda/koşularda tekrar verdiğinde ÇİFT SAYILMAMASI gerekir; çift sayım net alımı
    sessizce şişirirdi."""
    ham = "|".join(str(s.get(k) or "") for k in
                   ("sembol", "islem_tarihi", "kisi", "islem_kodu", "adet", "fiyat"))
    return hashlib.sha1(ham.encode("utf-8")).hexdigest()[:16]


def bos_defter() -> dict:
    return {"surum": 1, "guncellendi": None,
            "watermark": {"en_yeni_filing": None, "en_yeni_islem": None, "son_cekim": None},
            "cagri": {"toplam": 0, "son_tur": 0},
            "kapsam_sembol": {},          # sembol -> defterin gördüğü EN ESKİ işlem tarihi
            "alan_teshis": {"eslesmeyen_alanlar": [], "dusen_satir": 0},
            "islemler": []}


def defter_oku() -> dict:
    d = _store().read_json(LEDGER_FILE, None)
    if not isinstance(d, dict) or "islemler" not in d:
        return bos_defter()
    return d


# ------------------------------------------------------------------ çekim
def _fmp_get(path: str, params: dict) -> list:
    """FMP çağrısının TEK kapısı. Rotasyon/kota/maskeleme/muhasebe adapters/fmp._get'te — burada
    YALNIZ sağlık sayacı ve tip normalizasyonu var. YASA 4: hata YUTULMAZ, çağırana çıkar."""
    from . import fmp
    _HEALTH["calls"] += 1
    _HEALTH["at"] = _simdi()
    _HEALTH["last_path"] = path
    try:
        data = fmp._get(path, params)
    except Exception as e:
        _HEALTH["fails"] += 1
        _HEALTH.update({"ok": False, "last_error": f"{type(e).__name__}: {e}"[:200]})
        raise
    _HEALTH["ok"] = True
    _HEALTH["last_error"] = ""
    rows = data if isinstance(data, list) else []
    _HEALTH["rows"] += len(rows)
    return rows


def fetch_delta(gun: int = VARSAYILAN_GUN, sayfa_tavani: int = VARSAYILAN_SAYFA_TAVANI,
                limit: int = SAYFA_LIMIT, yaz: bool = True) -> dict:
    """`insider-trading/latest` akışını ARTIMLI tarar; REPLAY_UNIVERSE kesişimini deftere işler.

    PENCERE **DOSYALAMA** TARİHİNE GÖREDİR, işlem tarihine göre DEĞİL (canlı ilk koşuda bulunan
    kusur, 2026-07-29). `latest` akışı dosyalama sırasına göre akar ama Form 4 GEÇ dosyalanabilir:
    bugün gelen bir kayıt 2024'te yapılmış bir işlemi bildirebilir. Durma ölçütü işlem tarihi
    olsaydı, akışın ilk sayfasındaki TEK bir geç dosyalama taramayı derhal kesip geri kalan yeni
    dosyalamaları GÖRÜNMEZ kılardı — sessizce eksik bir defter, hiçbir testi kırmadan. (Canlı koşu
    tam bunu yaptı: sayfa 0'da durdu, `durma_sebebi=pencere_asildi`.) Özetin 90 günlük penceresi
    ise İŞLEM tarihine bakar; orada ekonomik olarak anlamlı olan odur.

    DURMA KOŞULLARI (hangisi önce gelirse):
      * satırın DOSYALAMA tarihi `gun` penceresinin gerisine düştü,
      * sayfanın TAMAMI defterde zaten var (su işaretine yetiştik) — artımlılığın özü,
      * sayfa boş geldi,
      * `sayfa_tavani` doldu → rapor `tavana_carpti=True` (yarım kalış GÖRÜNÜR).
    """
    from . import fmp
    evren = set(_universe())
    defter = defter_oku()
    mevcut = {s.get("anahtar") for s in defter["islemler"]}
    esik = (_dt.date.today() - _dt.timedelta(days=int(gun))).isoformat()

    rapor = {"cagri": 0, "sayfa": 0, "ham_satir": 0, "evren_disi": 0, "yeni": 0, "tekrar": 0,
             "dusen": 0, "tavana_carpti": False, "durma_sebebi": None, "esik_tarih": esik,
             "eslesmeyen_alanlar": [], "hata": None}

    if not fmp.available():
        rapor["hata"] = "FMP_API_KEY yok — insider çekimi devre dışı"
        return rapor
    if fmp.quota_blocked():
        # DÜRÜST BOZUNMA: kota dolmuşken istek atmak ne veri getirir ne kotayı geri verir.
        rapor["hata"] = "FMP tüm anahtarlar kota-bloklu — istek atılmadı"
        return rapor

    yeni_satirlar: list[dict] = []
    eslesmeyen: set[str] = set()
    for sayfa in range(int(sayfa_tavani)):
        # ÇAĞRI DENEMEDEN ÖNCE SAYILIR: başarısız istek de sağlayıcıya GİDER ve maliyeti vardır.
        # Yalnız başarılıları saymak, "kota etkisi" raporunu olduğundan UCUZ gösterirdi — ve bu
        # raporun tek işi o maliyeti dürüstçe söylemek (canlı koşuda bulundu: 3 başarısız `search`
        # çağrısı `cagri=0` diye raporlanmıştı).
        rapor["cagri"] += 1
        try:
            ham = _fmp_get("insider-trading/latest", {"page": sayfa, "limit": int(limit)})
        except Exception as e:
            # YASA 4: kısmi sonuç saklanır AMA sebep adıyla raporlanır. Sessiz boş dönmüyoruz.
            rapor["hata"] = f"{type(e).__name__}: {e}"[:200]
            rapor["durma_sebebi"] = "http_hatasi"
            break
        rapor["sayfa"] += 1
        rapor["ham_satir"] += len(ham)
        if not ham:
            rapor["durma_sebebi"] = "bos_sayfa"
            break
        sayfa_yeni, sayfa_eski, en_eski = 0, 0, None
        for h in ham:
            satir, artik = _kanonik(h)
            eslesmeyen |= artik
            if satir is None:
                rapor["dusen"] += 1
                continue
            # Su işareti DOSYALAMA tarihinden okunur; yoksa işlem tarihine düşülür (dürüst yedek).
            fd = satir.get("filing_tarihi") or satir["islem_tarihi"]
            en_eski = fd if en_eski is None else min(en_eski, fd)
            if satir["sembol"] not in evren:
                rapor["evren_disi"] += 1
                continue
            if satir["anahtar"] in mevcut:
                sayfa_eski += 1
                rapor["tekrar"] += 1
                continue
            mevcut.add(satir["anahtar"])
            yeni_satirlar.append(satir)
            sayfa_yeni += 1
        rapor["yeni"] += sayfa_yeni
        if en_eski is not None and en_eski < esik:
            rapor["durma_sebebi"] = "pencere_asildi"
            break
        # ARTIMLILIK: sayfanın evren-içi satırlarının TAMAMI defterdeyse su işaretine yetiştik.
        if sayfa_eski and not sayfa_yeni:
            rapor["durma_sebebi"] = "su_isareti"
            break
    else:
        rapor["tavana_carpti"] = True
        rapor["durma_sebebi"] = "sayfa_tavani"

    rapor["eslesmeyen_alanlar"] = sorted(eslesmeyen)[:20]
    if yaz:
        _defteri_birlestir(defter, yeni_satirlar, rapor, eslesmeyen)
    return rapor


def gecmis_cek(semboller: list[str], sayfa: int = 3, tavan: int = 20,
               limit: int = SAYFA_LIMIT, yaz: bool = True) -> dict:
    """`insider-trading/search?symbol=X` ile SEMBOL BAŞINA geçmiş derinleştirme (sınıflamanın
    3 yıllık penceresi için). MALİYET AÇIK: `min(len(semboller), tavan) * sayfa` istek — 250
    sembolün tamamına uygulanırsa günlük kota biter, bu yüzden `tavan` varsayılan olarak KÜÇÜK ve
    çağıran hangi sembollerin öncelikli olduğunu kendisi söyler."""
    from . import fmp
    evren = set(_universe())
    hedef = [s.strip().upper() for s in semboller if s and s.strip().upper() in evren][:int(tavan)]
    defter = defter_oku()
    mevcut = {s.get("anahtar") for s in defter["islemler"]}
    rapor = {"cagri": 0, "sembol": len(hedef), "yeni": 0, "tekrar": 0, "dusen": 0,
             "eslesmeyen_alanlar": [], "hata": None, "sembol_hata": {}}
    if not fmp.available():
        rapor["hata"] = "FMP_API_KEY yok — insider çekimi devre dışı"
        return rapor
    if fmp.quota_blocked():
        rapor["hata"] = "FMP tüm anahtarlar kota-bloklu — istek atılmadı"
        return rapor

    yeni_satirlar: list[dict] = []
    eslesmeyen: set[str] = set()
    for sym in hedef:
        for p in range(int(sayfa)):
            rapor["cagri"] += 1        # başarısız istek de maliyettir — bkz. fetch_delta gerekçesi
            try:
                ham = _fmp_get("insider-trading/search",
                               {"symbol": sym, "page": p, "limit": int(limit)})
            except Exception as e:
                rapor["sembol_hata"][sym] = f"{type(e).__name__}: {e}"[:120]
                # 402 = PLAN sınırı (kota değil): sonraki semboller de aynı yanıtı verecek.
                # Sembol sembol denemek 250 boş istek atmak olurdu — dur ve sebebi söyle.
                if "402" in str(e):
                    rapor["hata"] = ("insider-trading/search ÜCRETSİZ PLANDA KAPALI (HTTP 402) — "
                                     "geçmiş derinleştirme yapılamaz; 3 yıllık pencere yalnız "
                                     "/latest akışının birikmesiyle dolar")
                    return _bitir_gecmis(rapor, defter, yeni_satirlar, eslesmeyen, yaz)
                break
            if not ham:
                break
            for h in ham:
                satir, artik = _kanonik(h)
                eslesmeyen |= artik
                if satir is None:
                    rapor["dusen"] += 1
                    continue
                if satir["anahtar"] in mevcut:
                    rapor["tekrar"] += 1
                    continue
                mevcut.add(satir["anahtar"])
                yeni_satirlar.append(satir)
                rapor["yeni"] += 1
    return _bitir_gecmis(rapor, defter, yeni_satirlar, eslesmeyen, yaz)


def _bitir_gecmis(rapor, defter, yeni_satirlar, eslesmeyen, yaz):
    rapor["eslesmeyen_alanlar"] = sorted(eslesmeyen)[:20]
    if yaz:
        _defteri_birlestir(defter, yeni_satirlar, rapor, eslesmeyen)
    return rapor


def _defteri_birlestir(defter: dict, yeni: list[dict], rapor: dict, eslesmeyen: set[str]) -> None:
    """Defteri yaz. TEK YAZAR bu CLI; `store.write_json` atomik. `kapsam_sembol` sınıflamanın
    'bakabildiğimiz en eski tarih' kaydıdır ve SINIFLANAMADI kararının dayanağıdır."""
    st = _store()
    with st.file_lock(LEDGER_FILE):
        d = defter_oku()
        var = {s.get("anahtar") for s in d["islemler"]}
        for s in yeni:
            if s["anahtar"] not in var:
                var.add(s["anahtar"])
                d["islemler"].append(s)
        d["islemler"].sort(key=lambda s: (s.get("islem_tarihi") or "", s.get("sembol") or ""))
        if len(d["islemler"]) > DEFTER_TAVANI:
            d["islemler"] = d["islemler"][-DEFTER_TAVANI:]
        kaps = dict(d.get("kapsam_sembol") or {})
        for s in d["islemler"]:
            t, sym = s.get("islem_tarihi"), s.get("sembol")
            if t and sym and (sym not in kaps or t < kaps[sym]):
                kaps[sym] = t
        d["kapsam_sembol"] = kaps
        wm = d.setdefault("watermark", {})
        tarihler = [s.get("islem_tarihi") for s in d["islemler"] if s.get("islem_tarihi")]
        filingler = [s.get("filing_tarihi") for s in d["islemler"] if s.get("filing_tarihi")]
        wm["en_yeni_islem"] = max(tarihler) if tarihler else None
        wm["en_yeni_filing"] = max(filingler) if filingler else None
        wm["son_cekim"] = _simdi()
        c = d.setdefault("cagri", {"toplam": 0, "son_tur": 0})
        c["son_tur"] = int(rapor.get("cagri") or 0)
        c["toplam"] = int(c.get("toplam") or 0) + c["son_tur"]
        at = d.setdefault("alan_teshis", {"eslesmeyen_alanlar": [], "dusen_satir": 0})
        at["eslesmeyen_alanlar"] = sorted(set(at.get("eslesmeyen_alanlar") or []) | eslesmeyen)[:40]
        at["dusen_satir"] = int(at.get("dusen_satir") or 0) + int(rapor.get("dusen") or 0)
        d["guncellendi"] = _simdi()
        st.write_json(LEDGER_FILE, d)


# ------------------------------------------------------------------ sınıflama
def _ay(tarih: str) -> int:
    return int(tarih[5:7])


def _yil_geri(d: _dt.date, n: int) -> _dt.date:
    """`d`den `n` yıl geri. 29 Şubat'ta `date.replace(year=...)` ValueError atar (artık olmayan yıl);
    o gün 28 Şubat'a düşürülür. Küçük bir detay ama dört yılda bir TÜM sınıflamayı istisnayla
    düşürürdü ve o gün gelene kadar hiçbir test bunu göstermezdi."""
    try:
        return d.replace(year=d.year - int(n))
    except ValueError:  # sessiz-yutma: TEK bir takvim vakası (29 Şubat → 28 Şubat), hata değil TANIMLI davranış; sinyal üretmek dört yılda bir gerçek bir arıza yokken alarm çalardı
        return d.replace(year=d.year - int(n), day=28)


def siniflandir(kisi: str | None, sembol: str, islem_tarihi: str, gecmis: list[dict],
                kapsam_baslangic: str | None, yil: int = GECMIS_YIL) -> str:
    """RUTİN / FIRSATÇI / SINIFLANAMADI — modül docstring'indeki CMP basitleştirmesi.

    `gecmis`  : AYNI kişi+sembol için defterdeki TÜM işlemler (bu işlem dahil olabilir).
    `kapsam_baslangic` : defterin BU SEMBOL için gördüğü en eski işlem tarihi. Gereken pencerenin
                başlangıcından SONRAYSA cevap SINIFLANAMADI'dır — 'işlem yok' ile 'bakamıyoruz'
                aynı şey değildir (bu dosyanın en önemli ayrımı).
    """
    if not kisi:
        return "siniflanamadi"          # kişi bilinmeden 'aynı kişi' kuralı uygulanamaz
    try:
        d0 = _dt.date.fromisoformat(islem_tarihi)
    except (TypeError, ValueError):  # sessiz-yutma: SONUCUN KENDİSİ sinyaldir — 'siniflanamadi' özet dosyasında AYRI sayılır ve `siniflama_hazir_mi`yi False'a çeker; ayrıştırılamayan tarihi fırsatçı saymak tam da bu modülün yasakladığı uydurma olurdu
        return "siniflanamadi"
    pencere_baslangic = _yil_geri(d0, yil).isoformat()
    if not kapsam_baslangic or kapsam_baslangic > pencere_baslangic:
        return "siniflanamadi"
    ay = d0.month
    for k in range(1, int(yil) + 1):
        hedef_yil = d0.year - k
        if not any((t := g.get("islem_tarihi")) and int(t[:4]) == hedef_yil and _ay(t) == ay
                   for g in gecmis):
            return "firsatci"
    return "rutin"


def ozet(pencere_gun: int = VARSAYILAN_OZET_GUN, yaz: bool = True) -> dict:
    """Defterden sembol-başına özet skor üretir; `insider_signals.json`a yazar. AĞ ÇAĞRISI YOK.

    Skor = son `pencere_gun` gün içindeki FIRSATÇI **açık piyasa** işlemlerinin NET ALIMI:
      adet (alım-satım), $ tutar (alım-satım), ve alıcı/satıcı KİŞİ sayısı.
    Kişi sayısı ayrı tutulur çünkü tek bir yöneticinin büyük alımı ile üç yöneticinin ayrı ayrı
    alımı aynı $ tutarı üretebilir ama aynı şeyi söylemez (CMP'de yaygınlık ayrı bir boyuttur).
    """
    defter = defter_oku()
    islemler = defter.get("islemler") or []
    kapsam = defter.get("kapsam_sembol") or {}
    esik = (_dt.date.today() - _dt.timedelta(days=int(pencere_gun))).isoformat()

    # kişi+sembol geçmişi — sınıflama girdisi (defterin TAMAMI, pencere değil)
    gecmis: dict[tuple, list[dict]] = {}
    for s in islemler:
        gecmis.setdefault((s.get("sembol"), s.get("kisi")), []).append(s)

    semboller: dict[str, dict] = {}
    sinif_sayim = {"rutin": 0, "firsatci": 0, "siniflanamadi": 0}
    for s in islemler:
        t = s.get("islem_tarihi")
        if not t or t < esik:
            continue
        sym = s["sembol"]
        sinif = siniflandir(s.get("kisi"), sym, t, gecmis.get((sym, s.get("kisi")), []),
                            kapsam.get(sym))
        sinif_sayim[sinif] = sinif_sayim.get(sinif, 0) + 1
        e = semboller.setdefault(sym, {
            "firsatci_net_alim_adet": 0.0, "firsatci_net_alim_usd": 0.0,
            "firsatci_alici_kisi": set(), "firsatci_satici_kisi": set(),
            "islem_n": 0, "rutin_n": 0, "firsatci_n": 0, "siniflanamadi_n": 0,
            "yon_diger_n": 0, "yon_bilinmiyor_n": 0, "tutari_bilinmeyen_n": 0,
            "son_islem": None, "kapsam_baslangic": kapsam.get(sym)})
        e["islem_n"] += 1
        e[f"{sinif}_n"] += 1
        e["son_islem"] = t if not e["son_islem"] else max(e["son_islem"], t)
        yon = s.get("yon")
        if yon == "diger":
            e["yon_diger_n"] += 1
        elif yon == "bilinmiyor":
            e["yon_bilinmiyor_n"] += 1
        # NETE YALNIZ FIRSATÇI + AÇIK PİYASA satırları girer.
        if sinif != "firsatci" or yon not in ("alim", "satim"):
            continue
        isaret = 1.0 if yon == "alim" else -1.0
        adet, tutar = s.get("adet"), s.get("tutar")
        if adet is not None:
            e["firsatci_net_alim_adet"] += isaret * float(adet)
        if tutar is not None:
            e["firsatci_net_alim_usd"] += isaret * float(tutar)
        else:
            e["tutari_bilinmeyen_n"] += 1
        (e["firsatci_alici_kisi"] if yon == "alim" else e["firsatci_satici_kisi"]).add(s.get("kisi"))

    for e in semboller.values():
        e["firsatci_alici_kisi_n"] = len(e.pop("firsatci_alici_kisi"))
        e["firsatci_satici_kisi_n"] = len(e.pop("firsatci_satici_kisi"))
        e["firsatci_net_alim_adet"] = round(e["firsatci_net_alim_adet"], 2)
        e["firsatci_net_alim_usd"] = round(e["firsatci_net_alim_usd"], 2)

    evren = _universe()
    kapsanan = [k for k, v in kapsam.items()
                if v and v <= _yil_geri(_dt.date.today(), GECMIS_YIL).isoformat()]
    doc = {
        "surum": 1,
        "uretildi": _simdi(),
        "pencere_gun": int(pencere_gun),
        "siniflama": {
            "kural": "Cohen-Malloy-Pomorski basitleştirmesi: aynı kişi+sembol, işlemin takvim ayında "
                     f"önceki {GECMIS_YIL} yılın HER BİRİNDE de işlem varsa RUTİN; yoksa FIRSATÇI. "
                     "Defterin kapsamı o pencereye ULAŞMIYORSA cevap SINIFLANAMADI'dır (veri "
                     "yokluğu fırsatçılık DEĞİLDİR).",
            "gecmis_yil": GECMIS_YIL,
            "net_alim_tanimi": "yalnız Form 4 kodu P (alım) ve S (satım); ödül/icra/stopaj/bağış "
                               "satırları nete GİRMEZ",
            "sayim": sinif_sayim,
        },
        "kapsam": {
            "evren_n": len(evren),
            "defter_islem_n": len(islemler),
            "defter_en_eski": min((s.get("islem_tarihi") for s in islemler
                                   if s.get("islem_tarihi")), default=None),
            "defter_en_yeni": (defter.get("watermark") or {}).get("en_yeni_islem"),
            "islemli_sembol_n": len(semboller),
            f"{GECMIS_YIL}y_kapsamli_sembol_n": len(kapsanan),
            "siniflama_hazir_mi": bool(kapsanan) and sinif_sayim["siniflanamadi"] < sum(
                sinif_sayim.values() or [1]),
            "not": "siniflama_hazir_mi=False iken bu dosya bir SİNYAL DEĞİL, bir KAPSAM ÖLÇÜMÜDÜR.",
        },
        "cagri": defter.get("cagri") or {},
        "alan_teshis": defter.get("alan_teshis") or {},
        "semboller": dict(sorted(semboller.items())),
    }
    if yaz:
        _store().write_json(SIGNAL_FILE, doc)
    return doc


def durum() -> dict:
    from . import fmp
    d = defter_oku()
    return {"defter": {"islem_n": len(d.get("islemler") or []),
                       "guncellendi": d.get("guncellendi"),
                       "watermark": d.get("watermark"),
                       "cagri": d.get("cagri")},
            "fmp": {"available": fmp.available(), "quota_blocked": fmp.quota_blocked()},
            "health": health()}


# ------------------------------------------------------------------ CLI (YASA 6 tüketicisi)
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m meridian.adapters.insider",
        description="Form 4 içeriden işlem verisi (FMP) — artımlı çekim, CMP rutin/fırsatçı "
                    "sınıflaması, sembol-başına özet. AĞ ÇAĞRISI YALNIZ BURADAN.")
    ap.add_argument("--fetch", action="store_true", help="artımlı delta çekimi (insider-trading/latest)")
    ap.add_argument("--gecmis", action="store_true",
                    help="sembol-başına geçmiş derinleştirme (insider-trading/search) — TAVANLI")
    ap.add_argument("--ozet", action="store_true", help="defterden özet skoru üret ve yaz (ağ YOK)")
    ap.add_argument("--durum", action="store_true", help="defter/kota durumu (ağ YOK)")
    ap.add_argument("--gun", type=int, default=VARSAYILAN_GUN, help=f"çekim penceresi (varsayılan {VARSAYILAN_GUN})")
    ap.add_argument("--pencere", type=int, default=VARSAYILAN_OZET_GUN,
                    help=f"özet penceresi gün (varsayılan {VARSAYILAN_OZET_GUN})")
    ap.add_argument("--sayfa-tavani", type=int, default=VARSAYILAN_SAYFA_TAVANI,
                    help="kota koruması: en fazla kaç sayfa çekilsin")
    ap.add_argument("--sembol", type=str, default="", help="--gecmis için virgüllü sembol listesi")
    ap.add_argument("--tavan", type=int, default=20, help="--gecmis: en fazla kaç sembol")
    ap.add_argument("--sayfa", type=int, default=3, help="--gecmis: sembol başına sayfa")
    a = ap.parse_args(argv)

    if not any((a.fetch, a.gecmis, a.ozet, a.durum)):
        ap.print_help()
        return 2
    cikti: dict = {}
    if a.durum:
        cikti["durum"] = durum()
    if a.fetch:
        cikti["fetch"] = fetch_delta(gun=a.gun, sayfa_tavani=a.sayfa_tavani)
    if a.gecmis:
        syms = [s for s in a.sembol.replace(" ", "").split(",") if s]
        if not syms:
            # sembol verilmediyse: defterde SON HAREKET görülen semboller önceliklidir
            d = defter_oku()
            son = sorted((s for s in (d.get("islemler") or []) if s.get("islem_tarihi")),
                         key=lambda s: s["islem_tarihi"], reverse=True)
            syms, gor = [], set()
            for s in son:
                if s["sembol"] not in gor:
                    gor.add(s["sembol"])
                    syms.append(s["sembol"])
        cikti["gecmis"] = gecmis_cek(syms, sayfa=a.sayfa, tavan=a.tavan)
    if a.ozet:
        o = ozet(pencere_gun=a.pencere)
        cikti["ozet"] = {"pencere_gun": o["pencere_gun"], "siniflama": o["siniflama"]["sayim"],
                         "kapsam": o["kapsam"], "sembol_n": len(o["semboller"])}
    print(json.dumps(cikti, ensure_ascii=False, indent=2, default=str))
    # HATA VARSA ÇIKIŞ KODU 1: sessiz başarısızlık kabuk seviyesinde de görünsün (YASA 4).
    hatali = any(isinstance(v, dict) and v.get("hata") for v in cikti.values())
    return 1 if hatali else 0


if __name__ == "__main__":
    sys.exit(main())
