#!/usr/bin/env python3
"""research/olcumler/edg103_okuma_ilgi_atif/sayim.py — EDG-2026-103 sayım aleti: K1–K4, D, PK/NK, kill-list.

NE ÖLÇER. Kart `research/cards/EDG-2026-103-hafiza-sayfa-okuma-ilgi-atif.yaml` ("zihin modeli sayfaları
neden karara girmiyor"): dört kol — K1 okuma kadansı (H1), K2 konu ilgisi (H2), K3 atıf boşluğu (H3),
K4 fazlalık (H4) —, sayaç-0 D, PK/NK alet doğrulaması ve kill-list'in sekiz maddesi ADIYLA. Tanımlar
kartın DONMUŞ alanlarından ve Rol-1'in hüküm-öncesi `netlestirme_2026_10_01` alanından gelir; bu betik
onlara UYAR, hiçbirini değiştirmez. HÜKMÜ Rol-1 VERİR (CLAUDE.md §5): betik eşik karşılaştırmasını kolon
kolon yan yana koyar; kartı ve K defterini YAZMAZ.

OKUYUCU (Yasa 6): Rol-1'in EDG-2026-103 kart hükmü. Çıktı yalnız `--cikti-json` / `--cikti-md` yollarına
yazılır (`--cikti-json` yoksa JSON stdout'a); başka hiçbir yere yazmaz.

GİRDİ — YALNIZ DONDURULMUŞ DİZİN (`dondur.py` üretir). Bu betik A1'e, ağa ve git'e ÇIKMAZ; `meridian`
paketini İTHAL ETMEZ (obs'a ulaşmaz — çivi v610 K, alt süreçte `-X importtime` ile ölçer). Dizindeki her
dosya `SHA256.txt` ile içerik-adreslidir; tek bayt değişirse hesap YAPILMAZ.
  kart.yaml             kartın dondurma anındaki hâli — τ, W, pencere, eşikler, PK/NK, kill-list BURADAN okunur
  kart_acilis.yaml      kartın pencere AÇILIŞ commit'indeki hâli (kill #8 ve eşik donukluğu kıyası)
  okuma.jsonl           A1 okuma kaydı (alan kümesi ve şema sürümü `hafiza_okuma_kaydi`ndan İTHAL)
  karar_envanteri.json  `ops/karar_envanteri.py` çıktısı, DEĞİŞTİRİLMEMİŞ (D'nin kaynağı)
  karar_zamanlari.json  her kararın commit damgası (kaynağının GİRİŞ commit'i) + sentetik işaret
  sayfalar/<kimlik>.md  sayfa anlık görüntüsü (`sayfa_oku.sh <kimlik>` çıktısı, baytı baytına)
  kunye.json            dondurma anı, HEAD, kart/enstrümantasyon ilk commit'leri, §0-5 kural izi, PK/NK zamanı

TANIMLAR (kart + netleştirme; UYGULANDIĞI YER sembolle):
  pencere   [bas, son) yarı-açık, commit/olay damgasıyla — netleştirme (2) ............ `pencerede`
  okuma     doğrulanmış = kip sayfa ∧ durum gercek ∧ http 200 (kill #3); gerçek = doğrulanmış ∧ etiketsiz
            ∧ pencerede (kill #7). Kısmi okuma (`| head`) kayıtta tam GET'tir → sayılır — netleştirme (7)
            ............................................................ `dogrulanmis`, `gercek_okumalar`
  K1        dolu gün / S; S = pencereyle KESİŞEN UTC takvim günleri (açılış ve kapanış yarım günleri DAHİL)
            — netleştirme (1) ............................................................ `pencere_gunleri`
  eşleşme   karar zamanı ∈ [okuma, okuma + W) (tam W DIŞARIDA; pencereyle aynı yarı-açık kural) ∧
            Jaccard(sayfa tokenları, karar tokenları) ≥ τ (eşitlik İÇERİDE) — netleştirme (4) ve (6);
            PK(b) ve NK AYNI tanımı kullanır (yol-tutarlı) .................................. `ilgili_mi`
  K2        ≥1 D kararıyla eşleşen gerçek okuma / gerçek okuma — `esikler` cümlesi, netleştirme (3);
            "okuma-karar çifti oranı" (olcum_plani) yalnız BETİMLEYİCİ ................... `kolonlari_hesapla`
  K3        D_ilgili içinde `sayfa` atıflı / |D_ilgili| (D_ilgili boşsa 0/0 → ÖLÇÜLEMEDİ)
  K4        payda `esikler`deki "atıflı kararlar" — netleştirme c ((5)'i düzeltir; D paydası betimleyici; D_ilgili
            boşsa ÖLÇÜLEMEDİ); pay: K4 atıf türü (kart: recall/memory/kart_benzer) taşıyan, `sayfa`
            taşımayan ve ilgili bir TAZE sayfa okuması olan karar. "Taze" = okuma anında is_stale=false;
            okuma kaydı o alanı TAŞIMAZ → taze ölçülemez: K4 değeri None, yalnız "hepsi taze" varsayımlı
            ÜST sınır verilir; karşılaştırma ancak üst sınır eşiği geçmiyorsa kesindir ... `_k4`
  τ, W      kartın `esikler` bloğundan OKUNUR (bağlayıcı yer, netleştirme (3)); olcum_plani ve
            netleştirme metinlerinde yazılı değerler kıyaslanır, ayrışırsa sayım YAPILMAZ ... `esik_alanlari`
  kill #6   PK (a) doğrulanmış pk okuması · (b) PK kararıyla eşleşme · (c) PK kararı `sayfa` atıflı;
            NK atıfsız ve hiçbir okumayla eşleşmez; EK NK sayfası kartın ifadesini taşır. Biri tutmazsa
            hukum "GEÇERSİZ — alet doğrulanmadı", kolon karşılaştırması YAYILMAZ; K1 ve D yalnız
            "hüküm DEĞİL" etiketli betimleyici ara raporda — netleştirme (6) ve (8) ...... `pk_nk_denetle`

ÇIKIŞ: 0 sonuç üretildi (hüküm ne olursa olsun — GEÇERSİZ de bir sonuçtur) · 1 girdi eksik/bozuk/
bütünlük kırık (hesap YAPILMAZ, uydurma yasağı) · 2 kullanım ya da kart çözümlenemedi.

CLI (sözleşme KOMUT SATIRIdır; Rol-1, yerelde, dondurulmuş girdiyle):
    .venv/bin/python research/olcumler/edg103_okuma_ilgi_atif/sayim.py --girdi <dizin> \\
        [--cikti-json sonuc.json] [--cikti-md rapor.md]
"""
from __future__ import annotations

import argparse
import ast
import datetime as _dt
import hashlib
import json
import pathlib
import re
import sys
from fractions import Fraction

KOK = pathlib.Path(__file__).resolve().parents[3]
#: Yalnız iki SAF dizin ithal yoluna eklenir; depo kökü EKLENMEZ (o, `meridian`ı ithal yoluna açardı).
for _dizin in (KOK / "ops", KOK / "deploy" / "hindsight"):
    if str(_dizin) not in sys.path:
        sys.path.insert(0, str(_dizin))

import yaml  # noqa: E402
import hafiza_okuma_kaydi as OKUMA  # noqa: E402
import karar_envanteri as KE  # noqa: E402
from kart_benzer import normalize_tokens  # noqa: E402

SEMA = 1
ARAC = "research/olcumler/edg103_okuma_ilgi_atif/sayim.py"
UTC = _dt.timezone.utc
SAYFA_TURU = "sayfa"
SHA_DOSYASI = "SHA256.txt"
SAYFA_DIZINI = "sayfalar"
GIRDI_DOSYALARI = ("kart.yaml", "kart_acilis.yaml", "okuma.jsonl", "karar_envanteri.json",
                   "karar_zamanlari.json", "kunye.json")
#: Kill-list maddesi → metninde bulunması gereken çapa. Değerlendirme sırası kartın SIRASINA bağlıdır;
#: kart maddeleri yeniden sıralanırsa/değişirse sayım çözümlemede durur (sessizce yanlış maddeyi ölçmez).
KILL_CAPALARI = ("kart-önce", "n_min_karar", "yer tutucu", "§0-5", "sır", "PK/NK tutmazsa", "sentetik", "τ/W")
HUKUM_GECERSIZ_ALET = "GEÇERSİZ — alet doğrulanmadı"
HUKUM_KART_ONCE = "GEÇERSİZ — kart-önce ihlali (kill #1)"
HUKUM_TAU_W = "GEÇERSİZ — τ/W açılıştan sonra değişti (kill #8)"
HUKUM_ESIK = "GEÇERSİZ — eşik açılıştan sonra değişti (CLAUDE.md §5)"
HUKUM_ARA = "ARA RAPOR — pencere kapanmadan donduruldu (netleştirme 2), hüküm DEĞİL"
HUKUM_AKIS = "AKIŞ KAPATILDI — sır denetimi (kill #5); sayı yayılmaz"
HUKUM_GECERLI = "ALET DOĞRULANDI — dört kolon eşikle yan yana; kart hükmünü Rol-1 yazar (CLAUDE.md §5)"
BETIMLEYICI_ETIKET = "hüküm DEĞİL — betimleyici ara rapor (netleştirme 8: yalnız K1 ve D)"
TAZE_NEDENI = ("'taze' (netleştirme 5: okuma anında is_stale=false) ölçülemez — okuma kaydı şeması v{s} "
               "is_stale alanı taşımıyor (hafiza_okuma_kaydi.ALANLAR); değer None, yalnız hepsi-taze "
               "varsayımlı üst sınır verilir")

if SAYFA_TURU not in KE.ATIF_TURLERI:   # envanterin atıf sözlüğü değişirse sessizce 0 saymasın
    raise ImportError(f"karar_envanteri.ATIF_TURLERI '{SAYFA_TURU}' türünü taşımıyor")


class KartHatasi(Exception):
    """Kart beklenen alanı/biçimi taşımıyor — sayım yapılmaz (çıkış 2)."""


class GirdiHatasi(Exception):
    """Dondurulmuş girdi eksik/bozuk/bütünlüğü kırık — sayım yapılmaz (çıkış 1)."""


# ================================================================================================
# KART
# ================================================================================================

_ZAMAN = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"
_SAYI = r"(\d+(?:[.,]\d+)?)"


def an(metin: str) -> _dt.datetime:
    """ISO zaman → UTC; saat dilimsiz zaman KABUL EDİLMEZ (yerel saat sessizce UTC sanılmasın)."""
    d = _dt.datetime.fromisoformat(str(metin))
    if d.tzinfo is None:
        raise ValueError(f"saat dilimsiz zaman: {metin}")
    return d.astimezone(UTC)


def _kesir(metin: str) -> Fraction:
    return Fraction(metin.replace(",", "."))


def _bagla(ad: str, baglayici: str, desen: str, kiyas: list[tuple[str, str, str]]) -> tuple[str, list]:
    """Bağlayıcı yerdeki TEK değer + kıyas yerlerinde yazılmışsa AYNI değer (yoksa KartHatasi)."""
    degerler = {m.group(1).replace(",", ".") for m in re.finditer(desen, baglayici)}
    if len(degerler) != 1:
        raise KartHatasi(f"{ad}: `esikler` bloğunda tek değer yok ({sorted(degerler) or 'hiç'})")
    deger = degerler.pop()
    yerler = [{"yer": "esikler", "deger": deger}]
    for yer, metin, kdesen in kiyas:
        for m in re.finditer(kdesen, metin):
            yazili = m.group(1).replace(",", ".")
            if _kesir(yazili) != _kesir(deger):
                raise KartHatasi(f"{ad} kart içinde tutarsız: esikler={deger} ↔ {yer}={yazili}")
            yerler.append({"yer": yer, "deger": yazili})
    return deger, yerler


def esik_alanlari(metin: str) -> dict:
    """τ, W ve sayısal eşikler — açılış sürümü (netleştirmesiz) için de çalışan ALT çözümleme."""
    try:
        veri = yaml.safe_load(metin)
    except yaml.YAMLError as e:
        raise KartHatasi(f"kart YAML değil: {e}") from e
    if not isinstance(veri, dict):
        raise KartHatasi("kart bir sözlük değil")
    _bas, bloklar = KE._kart_bloklari(metin)
    ham = {a: b for a, _n, b in bloklar}
    for gerekli in ("esikler", "olcum_plani"):
        if gerekli not in ham:
            raise KartHatasi(f"kart alanı yok: {gerekli}")
    net = "\n".join(ham[a] for a in sorted(ham) if re.fullmatch(r"netlestirme_\d{4}_\d{2}_\d{2}[a-z]?", a))
    tau, tau_yer = _bagla("τ", ham["esikler"], r"τ\s*\(\s*" + _SAYI + r"\s*\)", [
        ("olcum_plani", ham["olcum_plani"], r"τ\s*\(\s*öneri:\s*" + _SAYI),
        ("netlestirme", net, r"τ\s*=\s*" + _SAYI)])
    w, w_yer = _bagla("W", ham["esikler"], r"(?<!\w)W\s*\(\s*(\d+)\s*s\s*\)", [
        ("olcum_plani", ham["olcum_plani"], r"(?<!\w)W\s+saat\s*\(\s*öneri:\s*(\d+)\s*s\s*\)"),
        ("netlestirme", net, r"(?<!\w)W\s*=\s*(\d+)\s*sa\b")])
    esikler = veri.get("esikler")
    if not isinstance(esikler, dict) or not isinstance(esikler.get("n_min_karar"), int):
        raise KartHatasi("esikler.n_min_karar tamsayı değil")
    kolon = {}
    for k in ("k1", "k2", "k3", "k4"):
        adaylar = [a for a in esikler if str(a).startswith(k + "_")]
        if len(adaylar) != 1 or not adaylar[0].endswith(("_alt", "_ust")):
            raise KartHatasi(f"{k} için tek bir _alt/_ust eşiği yok: {adaylar}")
        kolon[k.upper()] = (adaylar[0], Fraction(str(esikler[adaylar[0]])))
    return {"veri": veri, "ham": ham, "tau": _kesir(tau), "tau_yerleri": tau_yer,
            "W_saat": int(w), "W_yerleri": w_yer, "n_min": esikler["n_min_karar"], "kolon_esikleri": kolon}


def _cumle(metin: str, isaret: str) -> str:
    """İşaretin backtick'siz TEK geçişinden ilk cümle sonuna kadar (`[PK-…]` anması değil, kararın kendisi)."""
    gecisler = [m.start() for m in re.finditer(r"(?<!`)" + re.escape(isaret) + r"(?!`)", metin)]
    if len(gecisler) != 1:
        raise KartHatasi(f"{isaret}: açılış kaydında tek karar geçişi yok ({len(gecisler)})")
    son = re.compile(r"\.(?=\s|$)").search(metin, gecisler[0])
    return metin[gecisler[0]: son.start() if son else len(metin)].strip()


def _ara(desen: str, metin: str, ad: str, bayrak=0) -> re.Match:
    m = re.search(desen, metin, bayrak)
    if not m:
        raise KartHatasi(f"kartta bulunamadı: {ad}")
    return m


def kart_coz(metin: str) -> dict:
    kart = esik_alanlari(metin)
    veri, ham = kart["veri"], kart["ham"]
    card_id = str(veri.get("card_id") or "")
    m = re.fullmatch(r"([A-Z]+)-\d{4}-(\d{3})", card_id)
    if not m:
        raise KartHatasi(f"card_id biçimsiz: {card_id!r}")
    kisa = f"{m.group(1)}-{m.group(2)}"
    net = "\n".join(ham[a] for a in sorted(ham) if re.fullmatch(r"netlestirme_\d{4}_\d{2}_\d{2}[a-z]?", a))
    pencereler = {(x.group(1), x.group(2)) for x in
                  re.finditer(r"\[\s*(" + _ZAMAN + r")\s*,\s*(" + _ZAMAN + r")\s*\)", net)}
    if len(pencereler) != 1:
        raise KartHatasi(f"netleştirmede tek pencere [bas, son) yok ({len(pencereler)})")
    bas_s, son_s = pencereler.pop()
    bas, son = an(bas_s.replace("Z", "+00:00")), an(son_s.replace("Z", "+00:00"))
    acilislar = [a for a in veri if re.fullmatch(r"pencere_acilis_\d{4}_\d{2}_\d{2}", str(a))]
    if len(acilislar) != 1:
        raise KartHatasi(f"tek pencere_acilis_* alanı yok: {acilislar}")
    acilis = str(veri[acilislar[0]])
    pb = _ara(r"PENCERE BAŞI.*?(" + _ZAMAN + ")", acilis, "PENCERE BAŞI", re.S)
    if an(pb.group(1).replace("Z", "+00:00")) != bas:
        raise KartHatasi(f"pencere başı tutarsız: açılış {pb.group(1)} ↔ netleştirme {bas_s}")
    pk_metni = _cumle(acilis, f"[PK-{kisa}]")
    nk_metni = _cumle(acilis, f"[NK-{kisa}]")
    pk_etiket = _ara(r"POZİTİF KONTROL.*?\betiket\s+`([a-z0-9][a-z0-9_-]{0,31})`", acilis, "PK okuma etiketi",
                     re.S).group(1)
    pk_sayfa = _ara(r"kaynak:\s*zihin\s+modeli\s+([a-z0-9][a-z0-9._-]*)", pk_metni, "PK sayfası").group(1)
    ek = _ara(r"EK NK.*?`([a-z0-9][a-z0-9._-]*)`\s+sayfası.*?'([^']+)'\s+hükmünü",
              str(veri.get("pozitif_kontrol") or ""), "EK NK sayfası/ifadesi", re.S)
    kural = _ara(r"`(sayfa_oku\.sh\s+[a-z0-9][a-z0-9._-]*)`", str(veri.get("adim_0_on_kosul") or ""),
                 "§0-5 kural metni").group(1)
    ust = int(_ara(r"üst sınır\s+(\d+)\s+gün", str(veri.get("veri_penceresi") or ""), "pencere üst sınırı").group(1))
    plan = " ".join(str(x) for x in (veri.get("olcum_plani") or []))
    k4 = _ara(r"atıf\s+türü\s+([a-z_]+(?:/[a-z_]+)+)\s+İKEN", plan, "K4 atıf türleri").group(1).split("/")
    if not set(k4) <= set(KE.ATIF_TURLERI) or SAYFA_TURU in k4:
        raise KartHatasi(f"K4 atıf türleri envanter sözlüğünde değil: {k4}")
    kill = veri.get("kill_list")
    if not isinstance(kill, list) or len(kill) != len(KILL_CAPALARI):
        raise KartHatasi(f"kill_list {len(KILL_CAPALARI)} madde değil")
    for no, (madde, capa) in enumerate(zip(kill, KILL_CAPALARI), 1):
        if capa not in str(madde):
            raise KartHatasi(f"kill #{no} beklenen çapayı ('{capa}') taşımıyor — madde sırası değişmiş olabilir")
    kart.update({
        "card_id": card_id, "kisa": kisa, "bas": bas, "son": son, "ust_sinir_gun": ust,
        "acilis_alani": acilislar[0], "kural_anahtari": kural, "k4_turleri": k4,
        "kill_list": [" ".join(str(x).split()) for x in kill],
        "isaret_deseni": re.compile(r"\[(?:PK|NK)-" + re.escape(kisa) + r"\]"),
        "pk": {"metin": pk_metni, "etiket": pk_etiket, "sayfa": pk_sayfa},
        "nk": {"metin": nk_metni},
        "ek_nk": {"sayfa": ek.group(1), "ifade": ek.group(2)},
    })
    return kart


# ================================================================================================
# GİRDİ
# ================================================================================================

def sha256(yol: pathlib.Path) -> str:
    return hashlib.sha256(yol.read_bytes()).hexdigest()


def butunluk(girdi: pathlib.Path) -> dict[str, str]:
    """SHA256.txt ↔ dizin: her dosya listede, her özet tutuyor; aksi GirdiHatasi."""
    liste = girdi / SHA_DOSYASI
    if not liste.is_file():
        raise GirdiHatasi(f"{SHA_DOSYASI} yok — girdi dondurulmamış")
    beyan = {}
    for satir in liste.read_text(encoding="utf-8").splitlines():
        if satir.strip():
            ozet, _, yol = satir.partition("  ")
            beyan[yol] = ozet
    var = {p.relative_to(girdi).as_posix() for p in girdi.rglob("*") if p.is_file() and p.name != SHA_DOSYASI}
    if var != set(beyan):
        raise GirdiHatasi(f"{SHA_DOSYASI} dizinle örtüşmüyor: fazla {sorted(var - set(beyan))}, "
                          f"eksik {sorted(set(beyan) - var)}")
    for yol, ozet in sorted(beyan.items()):
        if sha256(girdi / yol) != ozet:
            raise GirdiHatasi(f"{yol} özeti tutmuyor — girdi dondurulduktan sonra değişmiş")
    for gerekli in GIRDI_DOSYALARI:
        if gerekli not in beyan:
            raise GirdiHatasi(f"girdi dosyası yok: {gerekli}")
    return beyan


def _json(yol: pathlib.Path):
    try:
        return json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise GirdiHatasi(f"{yol.name} okunamadı ({type(e).__name__})") from e


def okuma_kaydi_oku(metin: str) -> tuple[list[dict], dict]:
    """Şema v1 satırları; bozuk/şema-dışı satır HESABA GİRMEZ ama numarasıyla raporlanır."""
    satirlar, bozuk, sema_disi = [], [], []
    alanlar = set(OKUMA.ALANLAR)
    for no, ham in enumerate(metin.splitlines(), 1):
        if not ham.strip():
            continue
        try:
            r = json.loads(ham)
        except ValueError:  # sessiz-yutma: bozuk satır SAYILMAZ ama satır numarasıyla `bozuk_json`a yazılıp raporlanır
            bozuk.append(no)
            continue
        if not isinstance(r, dict) or set(r) != alanlar or r.get("v") != OKUMA.SEMA:
            sema_disi.append(no)
            continue
        try:
            ts = _dt.datetime.strptime(str(r["ts"]), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        except ValueError:  # sessiz-yutma: biçimsiz ts'li satır hesaba girmez, numarasıyla `sema_disi`na raporlanır
            sema_disi.append(no)
            continue
        satirlar.append(dict(r, _ts=ts, _no=no))
    return satirlar, {"satir": len(satirlar) + len(bozuk) + len(sema_disi), "gecerli": len(satirlar),
                      "bozuk_json": bozuk, "sema_disi": sema_disi,
                      "ilk_ts": min((r["ts"] for r in satirlar), default=None),
                      "son_ts": max((r["ts"] for r in satirlar), default=None)}


_SAYFA_BASLIGI = re.compile(r"^# (?P<ad>.*) · id=(?P<kimlik>\S*) · v(?P<surum>\S*) · tazeleme=(?P<tazeleme>\S*)$")


def sayfa_goruntusu(yol: pathlib.Path, kimlik: str) -> dict:
    """`sayfa_oku.sh <kimlik>` çıktısı: 1. satır başlık, kalanı içerik + print'in sondaki '\\n'i."""
    if not yol.is_file():
        raise GirdiHatasi(f"sayfa anlık görüntüsü yok: {kimlik}")
    metin = yol.read_text(encoding="utf-8")
    ilk, _, kalan = metin.partition("\n")
    m = _SAYFA_BASLIGI.match(ilk)
    if not m or m.group("kimlik") != kimlik:
        raise GirdiHatasi(f"sayfa anlık görüntüsü başlığı biçimsiz ya da kimliği farklı: {kimlik}")
    icerik = kalan[:-1] if kalan.endswith("\n") else kalan
    durum = OKUMA.sayfa_durumu(icerik, m.group("tazeleme") or None)
    if durum != "gercek":
        raise GirdiHatasi(f"sayfa anlık görüntüsü gerçek içerik değil ({durum}): {kimlik}")
    return {"icerik": icerik, "tazeleme": m.group("tazeleme"), "sha256": hashlib.sha256(icerik.encode("utf-8")).hexdigest(),
            "tokenler": normalize_tokens(icerik)}


# ================================================================================================
# SINIFLAMA VE EŞLEŞME
# ================================================================================================

def pencerede(zaman: _dt.datetime, bas: _dt.datetime, son: _dt.datetime) -> bool:
    """Netleştirme (2): yarı-açık [bas, son)."""
    return bas <= zaman < son


def dogrulanmis(r: dict) -> bool:
    """Doğrulanmış okuma: gerçek gövde, HTTP 200, sayfa okuması (yer tutucu/boş/hata DEĞİL — kill #3)."""
    return r["kip"] == "sayfa" and r["durum"] == "gercek" and r["http"] == 200


def gercek_okumalar(satirlar: list[dict], bas, son) -> list[dict]:
    """K1–K4'ün okumaları: doğrulanmış ∧ etiketsiz (kill #7 — PK/test/anlık görüntü ayrı) ∧ pencerede."""
    return [r for r in satirlar if dogrulanmis(r) and r["etiket"] is None and pencerede(r["_ts"], bas, son)]


def pencere_gunleri(bas: _dt.datetime, son: _dt.datetime) -> list[_dt.date]:
    """Netleştirme (1): S = pencereyle KESİŞEN UTC takvim günleri. Pencere yarı-açık olduğu için son gün
    `son`dan bir mikrosaniye önceki anın günüdür; açılış (09-25) ve kapanış (10-02) yarım günleri S'dedir."""
    gun, son_gun = bas.date(), (son - _dt.timedelta(microseconds=1)).date()
    gunler = []
    while gun <= son_gun:
        gunler.append(gun)
        gun += _dt.timedelta(days=1)
    return gunler


def k1_gunleri(okumalar: list[dict], bas, son) -> tuple[list[_dt.date], list[_dt.date]]:
    """K1'in TEK sayımı (kolon ve betimleyici ara rapor ikisi de bunu kullanır): (S, dolu günler)."""
    return pencere_gunleri(bas, son), sorted({r["_ts"].date() for r in okumalar})


def jaccard(a: set, b: set) -> Fraction | None:
    birlesim = a | b
    return Fraction(len(a & b), len(birlesim)) if birlesim else None


def ilgili_mi(okuma_an, sayfa_tok, karar_an, karar_tok, tau: Fraction, W: _dt.timedelta) -> tuple[bool, bool, Fraction | None]:
    """K2 eşleşmesinin TEK tanımı (PK(b) ve NK da bunu kullanır). Dönüş: (W içinde mi, ilgili mi, J)."""
    if not (okuma_an <= karar_an < okuma_an + W):
        return False, False, None
    j = jaccard(sayfa_tok, karar_tok)
    return True, (j is not None and j >= tau), j


def okuma_tazeligi(_r: dict) -> bool | None:
    """Okuma anında sayfa taze miydi (is_stale=false)? Şema v1 bunu taşımaz → None (ölçülemez)."""
    if "is_stale" in OKUMA.ALANLAR:   # şema genişlerse bu dal yazılmadan sayım SESSİZCE eski kuralla koşmasın
        raise GirdiHatasi("okuma kaydı şeması is_stale taşıyor ama sayım tazelik dalı yazılmadı")
    return None


# ================================================================================================
# KARARLAR
# ================================================================================================

def karar_turleri_tokenleri(metin: str, tarih: _dt.date) -> tuple[set, set]:
    """PK/NK metnini envanterin KENDİ boru hattından geçirir (atıf türü + token + sır-benzeri süzgeci)."""
    kararlar, _atilan, _destek = KE.birlestir([{"tur": "kart", "ref": {"tur": "kart", "alan": "pk_nk"},
                                                "tarih": tarih, "kimlik": None, "baslik": metin,
                                                "metin": metin, "isaretler": ["pk_nk"]}])
    return set(kararlar[0]["atif_turleri"]), set(kararlar[0]["konu_tokenleri"])


def kararlari_kur(envanter: dict, zamanlar: dict, bas, son) -> dict:
    kararlar, zl = envanter.get("kararlar"), zamanlar.get("kararlar")
    if not isinstance(kararlar, list) or not isinstance(zl, list) or len(kararlar) != len(zl):
        raise GirdiHatasi("karar_envanteri.json ↔ karar_zamanlari.json karar sayısı örtüşmüyor")
    D, sentetik, disarida, zamansiz = [], [], 0, []
    for i, (k, z) in enumerate(zip(kararlar, zl)):
        if (z.get("sira"), z.get("tarih"), z.get("kimlik"), z.get("baslik")) != (i, k["tarih"], k["kimlik"], k["baslik"]):
            raise GirdiHatasi(f"karar {i}: envanter ↔ zaman kaydı farklı karar")
        if z.get("zaman") is None:
            zamansiz.append(f"{i} {k['tarih']} {k['kimlik']} ({z.get('zaman_neden')})")
            continue
        zaman = an(z["zaman"])
        if not pencerede(zaman, bas, son):
            disarida += 1
            continue
        kayit = {"sira": i, "tarih": k["tarih"], "kimlik": k["kimlik"], "baslik": k["baslik"], "zaman": zaman,
                 "atif": set(k["atif_turleri"]), "tok": set(k["konu_tokenleri"]),
                 "sentetik": list(z.get("sentetik_isaretler") or [])}
        (sentetik if kayit["sentetik"] else D).append(kayit)
    if zamansiz:
        raise GirdiHatasi(f"{len(zamansiz)} kararın commit damgası yok — pencereye yerleştirilemez: "
                          + "; ".join(zamansiz[:10]))
    return {"D": D, "sentetik": sentetik, "pencere_disi": disarida}


# ================================================================================================
# HESAP
# ================================================================================================

def oran(pay: int, payda: int) -> dict:
    if payda == 0:
        return {"pay": pay, "payda": 0, "kesir": None, "deger": None}
    return {"pay": pay, "payda": payda, "kesir": f"{pay}/{payda}", "deger": round(float(Fraction(pay, payda)), 4)}


def karsilastir(deger: Fraction | None, esik_adi: str, esik: Fraction) -> str:
    if deger is None:
        return "ÖLÇÜLEMEDİ"
    if esik_adi.endswith("_alt"):
        return "GEÇTİ" if deger >= esik else "KALDI"
    return "GEÇTİ" if deger <= esik else "KALDI"


def _k_sonuc(pay, payda, esik_adi, esik, neden=None, **ek) -> dict:
    deger = Fraction(pay, payda) if payda else None
    return {**oran(pay, payda), "esik": {"ad": esik_adi, "deger": float(esik), "yon": "≥" if esik_adi.endswith("_alt") else "≤"},
            "karsilastirma": karsilastir(deger, esik_adi, esik),
            "neden": neden if deger is not None or neden else "payda 0 (0/0) — ölçülemedi", **ek}


def _k4(D, d_ilgili_okumalar, k4_turleri, esik_adi, esik) -> dict:
    """K4 — netleştirme c ((5)'in DÜZELTMESİ): payda kartın donmuş `esikler` cümlesindeki "atıflı kararlar" =
    D'de bir hafıza KAYNAĞI atfı (sayfa ya da K4 türleri) taşıyan kararlar; D paydası yalnız betimleyici.
    `bos_beyan`/`diger` kaynak atfı DEĞİLDİR, paydaya girmez (dar payda → oran büyür → geçme yönüne sapmaz).
    D_ilgili boşsa fazlalık hiç sınanmamıştır: K3 gibi ÖLÇÜLEMEDİ ("0/… GEÇTİ" basılmaz)."""
    kaynak_turleri = {SAYFA_TURU} | set(k4_turleri)
    atifli = [d["sira"] for d in D if d["atif"] & kaynak_turleri]
    kesin, belirsiz = [], []
    for j, d in enumerate(D):
        if SAYFA_TURU in d["atif"] or not (d["atif"] & set(k4_turleri)) or j not in d_ilgili_okumalar:
            continue
        tazelik = [okuma_tazeligi(r) for r in d_ilgili_okumalar[j]]
        if any(t is True for t in tazelik):
            kesin.append(d["sira"])
        elif any(t is None for t in tazelik):
            belirsiz.append(d["sira"])
    n = len(atifli)
    alt, ust = (Fraction(len(kesin), n), Fraction(len(kesin) + len(belirsiz), n)) if n else (None, None)
    d_ilgili = len(d_ilgili_okumalar)
    if not d_ilgili_okumalar:
        sonuc = {"pay": None, "payda": n, "kesir": None, "deger": None,
                 "esik": {"ad": esik_adi, "deger": float(esik), "yon": "≤"}, "karsilastirma": "ÖLÇÜLEMEDİ",
                 "neden": "D_ilgili boş — fazlalık sınanmadı (K3 ile aynı; netleştirme c)"}
    elif not belirsiz:
        sonuc = _k_sonuc(len(kesin), n, esik_adi, esik)
    else:
        if ust is not None and karsilastir(ust, esik_adi, esik) == "GEÇTİ":
            kars = "GEÇTİ"          # her olası tazelikte eşiğin altında: kesin çıkarım
        elif alt is not None and karsilastir(alt, esik_adi, esik) == "KALDI":
            kars = "KALDI"          # hiçbir olası tazelikte eşiğin altına inemez
        else:
            kars = "ÖLÇÜLEMEDİ"
        sonuc = {"pay": None, "payda": n, "kesir": None, "deger": None,
                 "esik": {"ad": esik_adi, "deger": float(esik), "yon": "≤"},
                 "karsilastirma": kars, "neden": TAZE_NEDENI.format(s=OKUMA.SEMA)}
    sonuc.update({"alt_sinir": oran(len(kesin), n), "ust_sinir": oran(len(kesin) + len(belirsiz), n),
                  "aday_karar": belirsiz + kesin, "atifli_karar": atifli,
                  "payda_tanimi": "esikler 'atıflı kararlar': D'de " + "/".join(sorted(kaynak_turleri)) + " atfı taşıyan",
                  "betimleyici_D_paydasi": oran(len(kesin) + len(belirsiz), len(D)),
                  "betimleyici_D_ilgili_paydasi": oran(len(kesin) + len(belirsiz), d_ilgili)})
    return sonuc


def kolonlari_hesapla(kart: dict, okumalar: list[dict], D: list[dict], sayfa_tok: dict, kural_kaldirildi: bool) -> dict:
    tau, W = kart["tau"], _dt.timedelta(hours=kart["W_saat"])
    esik = kart["kolon_esikleri"]
    S, dolu = k1_gunleri(okumalar, kart["bas"], kart["son"])
    k1 = _k_sonuc(len(dolu), len(S), *esik["K1"], S_gunleri=[g.isoformat() for g in S],
                  dolu_gunler=[g.isoformat() for g in dolu], okuma_sayisi=len(okumalar))
    okuma_ozet, ilgili_okumalar, cift, eslesme = [], {}, 0, 0
    for r in okumalar:
        P = sayfa_tok[r["kimlik"]]
        zaman_icinde, eslesen, en_yuksek = [], [], None
        for j, d in enumerate(D):
            icinde, ilgili, J = ilgili_mi(r["_ts"], P, d["zaman"], d["tok"], tau, W)
            if not icinde:
                continue
            zaman_icinde.append(d["sira"])
            if J is not None and (en_yuksek is None or J > en_yuksek):
                en_yuksek = J
            if ilgili:
                eslesen.append(d["sira"])
                ilgili_okumalar.setdefault(j, []).append(r)
        cift += len(zaman_icinde)
        eslesme += len(eslesen)
        okuma_ozet.append({"ts": r["ts"], "kimlik": r["kimlik"], "zaman_icinde_karar": zaman_icinde,
                           "eslesen_karar": eslesen, "en_yuksek_jaccard": None if en_yuksek is None else
                           f"{en_yuksek.numerator}/{en_yuksek.denominator}"})
    k2 = _k_sonuc(sum(1 for o in okuma_ozet if o["eslesen_karar"]), len(okumalar), *esik["K2"],
                  okumalar=okuma_ozet, betimleyici_cift_orani={**oran(eslesme, cift),
                  "not": "olcum_plani 'okuma-karar çiftlerinin oranı' — netleştirme (3): betimleyici, hüküm DEĞİL"})
    d_ilgili = sorted(ilgili_okumalar)
    k3 = _k_sonuc(sum(1 for j in d_ilgili if SAYFA_TURU in D[j]["atif"]), len(d_ilgili), *esik["K3"],
                  D_ilgili=[D[j]["sira"] for j in d_ilgili])
    k4 = _k4(D, ilgili_okumalar, kart["k4_turleri"], *esik["K4"])
    kolonlar = {"K1": k1, "K2": k2, "K3": k3, "K4": k4}
    if len(D) < kart["n_min"]:
        for kolon in kolonlar.values():
            kolon.update({"karsilastirma": "ÖLÇÜLEMEDİ",
                          "neden": f"örnek yetersiz: D={len(D)} < n_min_karar={kart['n_min']} (kart esikler)"})
    if kural_kaldirildi:   # n_min'den SONRA: kart kill #4 "'ölçülemedi' değil KALDI" der (inceleme M2)
        k1.update({"karsilastirma": "KALDI", "neden": "kill #4: §0-5 kuralı pencere içinde kaldırıldı → K1 KALDI"})
    return kolonlar


def pk_nk_denetle(kart, satirlar, gercek, sayfalar, pk_nk_zamani) -> dict:
    tau, W = kart["tau"], _dt.timedelta(hours=kart["W_saat"])
    pk, nk, ek = kart["pk"], kart["nk"], kart["ek_nk"]
    pk_atif, pk_tok = karar_turleri_tokenleri(pk["metin"], pk_nk_zamani.date())
    nk_atif, nk_tok = karar_turleri_tokenleri(nk["metin"], pk_nk_zamani.date())
    pk_okumalari = [r for r in satirlar if r["etiket"] == pk["etiket"] and r["kip"] == "sayfa" and r["kimlik"] == pk["sayfa"]]
    a_okumalari = [r for r in pk_okumalari if dogrulanmis(r)]
    b_ayrinti = []
    for r in a_okumalari:
        icinde, ilgili, J = ilgili_mi(r["_ts"], sayfalar[pk["sayfa"]]["tokenler"], pk_nk_zamani, pk_tok, tau, W)
        b_ayrinti.append({"okuma_ts": r["ts"], "zaman_farki_sn": (pk_nk_zamani - r["_ts"]).total_seconds(),
                          "W_icinde": icinde, "jaccard": None if J is None else f"{J.numerator}/{J.denominator}",
                          "ilgili": ilgili})
    nk_okumalari = gercek + a_okumalari
    nk_ayrinti = []
    for r in nk_okumalari:
        icinde, ilgili, J = ilgili_mi(r["_ts"], sayfalar[r["kimlik"]]["tokenler"], pk_nk_zamani, nk_tok, tau, W)
        if icinde:
            nk_ayrinti.append({"okuma_ts": r["ts"], "kimlik": r["kimlik"],
                               "jaccard": None if J is None else f"{J.numerator}/{J.denominator}", "ilgili": ilgili})
    ek_baslik = next((s.strip() for s in sayfalar[ek["sayfa"]]["icerik"].splitlines() if s.strip()), "")
    sonuc = {
        "pk": {"metin": pk["metin"], "okuma_etiketi": pk["etiket"], "sayfa": pk["sayfa"],
               "karar_zamani": pk_nk_zamani.isoformat(),
               "a_okuma": {"tuttu": bool(a_okumalari), "pk_satiri": len(pk_okumalari),
                           "dogrulanmis": [r["ts"] for r in a_okumalari]},
               "b_ilgi": {"tuttu": any(x["ilgili"] for x in b_ayrinti), "ayrinti": b_ayrinti},
               "c_atif": {"tuttu": SAYFA_TURU in pk_atif, "atif_turleri": sorted(pk_atif)}},
        "nk": {"metin": nk["metin"], "karar_zamani": pk_nk_zamani.isoformat(),
               "atifsiz": {"tuttu": not nk_atif, "atif_turleri": sorted(nk_atif)},
               "ilgisiz": {"tuttu": not any(x["ilgili"] for x in nk_ayrinti), "ayrinti": nk_ayrinti}},
        # kart: sayfa "'bankada yok' HÜKMÜNÜ taşımalı" — hüküm sayfanın başlığıdır; gövdede geçen ifade
        # (ör. "… bankada yok DEĞİL") hükmü kanıtlamaz (inceleme M3)
        "ek_nk": {"sayfa": ek["sayfa"], "ifade": ek["ifade"], "baslik": ek_baslik,
                  "tuttu": ek_baslik.startswith("#") and ek["ifade"].casefold() in ek_baslik.casefold()},
    }
    sonuc["tuttu"] = all((sonuc["pk"]["a_okuma"]["tuttu"], sonuc["pk"]["b_ilgi"]["tuttu"],
                          sonuc["pk"]["c_atif"]["tuttu"], sonuc["nk"]["atifsiz"]["tuttu"],
                          sonuc["nk"]["ilgisiz"]["tuttu"], sonuc["ek_nk"]["tuttu"]))
    return sonuc


# ================================================================================================
# SIR DENETİMİ (kill #5)
# ================================================================================================

def notify_desenleri() -> list[tuple[str, re.Pattern]]:
    """`meridian/notify.py::_SIR_DESENLERI` — modül İTHAL EDİLMEDEN, kaynağın AST'inden okunur (tek kaynak;
    ithal `meridian.secrets`/obs'a uzanırdı). Bilinen-DEĞER katmanı (secrets.ALLOWED) sır deposunu okumayı
    gerektirdiği için burada YOKTUR — bedeli: biçimi tanınmayan ama değeri bilinen bir sır kaçabilir."""
    yol = KOK / "meridian" / "notify.py"
    try:
        agac = ast.parse(yol.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as e:
        raise GirdiHatasi(f"sır desenleri okunamadı ({yol.name}: {type(e).__name__}) — kill #5 ölçülemez") from e
    for d in agac.body:
        hedef = d.target if isinstance(d, ast.AnnAssign) else (d.targets[0] if isinstance(d, ast.Assign) else None)
        if isinstance(hedef, ast.Name) and hedef.id == "_SIR_DESENLERI":
            try:
                return [(ast.literal_eval(e.elts[0]), re.compile(ast.literal_eval(e.elts[1].args[0])))
                        for e in d.value.elts]
            except (AttributeError, IndexError, ValueError, re.error) as e:
                raise GirdiHatasi(f"_SIR_DESENLERI biçimi tanınmadı ({type(e).__name__}) — kill #5 ölçülemez") from e
    raise GirdiHatasi("meridian/notify.py içinde _SIR_DESENLERI yok — kill #5 ölçülemez")


_JETON_AYRACI = re.compile(r"[\s\"'(),;:]+")
_SHA_KIMLIK = re.compile(r"sha256:[0-9a-f]{64}")


def notify_taramasi(metinler: dict[str, str]) -> list[dict]:
    """notify sır desenleriyle satır satır tarama (yanlış-pozitifsiz katman). dondur.py yazmadan ÖNCE dondurulacak
    HER dosyaya, sayım kill #5'te dondurulmuş her metne uygular — tek tanım. Bulgu DEĞERİ asla dönmez."""
    desenler = notify_desenleri()
    return [{"kaynak": ad, "yer": f"satır {no}", "denetci": f"notify:{dad}"}
            for ad, metin in metinler.items() for no, satir in enumerate(metin.splitlines(), 1)
            for dad, d in desenler if d.search(satir)]


def sir_denetimi(okuma_metni: str, satirlar: list[dict], envanter: dict, ek_metinler: dict[str, str]) -> dict:
    """Kill #5: okuma kaydı + karar envanteri (notify + `_sir_benzeri`) ve dondurulan öteki metinler (sayfa
    görüntüleri, karar_zamanlari, künye — YALNIZ notify: sayfalar sır ADLARI ve uzun yol jetonları taşır,
    `_sir_benzeri` orada yanlış-pozitif verir). Bulgu DEĞERİ asla yazılmaz — yalnız yer ve denetçi adı."""
    desenler = notify_desenleri()
    bulgular = notify_taramasi({"okuma.jsonl": okuma_metni, **ek_metinler})
    for r in satirlar:
        for alan in ("betik", "kip", "ad", "bank", "butce", "durum", "hata", "etiket", "kimlik"):
            deger = r.get(alan)
            if not isinstance(deger, str) or (alan == "kimlik" and _SHA_KIMLIK.fullmatch(deger)):
                continue
            if any(KE._sir_benzeri(j) for j in _JETON_AYRACI.split(deger)):
                bulgular.append({"kaynak": "okuma.jsonl", "yer": f"satır {r['_no']} alan {alan}",
                                 "denetci": "karar_envanteri._sir_benzeri"})
    for i, k in enumerate(envanter.get("kararlar") or []):
        baslik = str(k.get("baslik") or "")
        bulgular += [{"kaynak": "karar_envanteri.json", "yer": f"karar {i} baslik", "denetci": f"notify:{ad}"}
                     for ad, d in desenler if d.search(baslik)]
        if any(KE._sir_benzeri(j) for j in list(k.get("konu_tokenleri") or []) + _JETON_AYRACI.split(baslik)):
            bulgular.append({"kaynak": "karar_envanteri.json", "yer": f"karar {i}",
                             "denetci": "karar_envanteri._sir_benzeri"})
    return {"bulgu_sayisi": len(bulgular), "bulgular": bulgular,
            "denetciler": [f"notify:{ad}" for ad, _d in desenler] + ["karar_envanteri._sir_benzeri"],
            "envanterin_kendi_attigi": envanter.get("sir_benzeri_atilan")}


# ================================================================================================
# KILL-LIST
# ================================================================================================

def kural_kaldirildi_mi(iz: list[dict], bas, son) -> tuple[bool, list]:
    """Pencere başındaki durum (bastan önceki son commit) + pencere içindeki her commit: adet 0 → kaldırıldı."""
    olaylar = sorted(((an(x["zaman"]), x) for x in iz), key=lambda t: t[0])
    once = [x for z, x in olaylar if z < bas]
    gecerli = ([once[-1]] if once else []) + [x for z, x in olaylar if pencerede(z, bas, son)]
    return (not once) or any(x["adet"] == 0 for x in gecerli), gecerli


def kill_degerlendir(kart, kunye, satirlar, kararlar, sir, pk_nk, kart_acilis, kural) -> list[dict]:
    bas, son = kart["bas"], kart["son"]
    kart_ilk = an(kunye["kart"]["ilk_commit"]["zaman"])
    enstr_ilk = an(kunye["enstrumantasyon"]["ilk_commit"]["zaman"])
    ilk_kayit = min((r["_ts"] for r in satirlar), default=None)
    k1_tetik = enstr_ilk < kart_ilk or (ilk_kayit is not None and ilk_kayit < kart_ilk)
    n_D, n_min = len(kararlar["D"]), kart["n_min"]
    ust_sinir = bas + _dt.timedelta(days=kart["ust_sinir_gun"])
    if n_D >= n_min:
        k2 = "TETİKLENMEDİ"
    elif son >= ust_sinir:
        k2 = "TETİKLENDİ"
    else:
        k2 = "ÖLÇÜLEMEDİ — D<n_min, pencere üst sınırına ulaşılmadı (kart: uzatma yok; karar Rol-1'de)"
    sayilmayan = [r for r in satirlar if r["kip"] == "sayfa" and r["etiket"] is None
                  and pencerede(r["_ts"], bas, son) and not dogrulanmis(r)]
    etiketli: dict[str, int] = {}
    for r in satirlar:
        if r["etiket"] is not None:
            etiketli[r["etiket"]] = etiketli.get(r["etiket"], 0) + 1
    tau_w_ayni = (kart["tau"], kart["W_saat"]) == (kart_acilis["tau"], kart_acilis["W_saat"])
    pk_tutmayan = [] if pk_nk is None else [
        ad for ad, t in (("PK(a)", pk_nk["pk"]["a_okuma"]["tuttu"]), ("PK(b)", pk_nk["pk"]["b_ilgi"]["tuttu"]),
                         ("PK(c)", pk_nk["pk"]["c_atif"]["tuttu"]), ("NK atıfsız", pk_nk["nk"]["atifsiz"]["tuttu"]),
                         ("NK ilgisiz", pk_nk["nk"]["ilgisiz"]["tuttu"]), ("EK NK", pk_nk["ek_nk"]["tuttu"])) if not t]
    kaldirildi, gecerli_iz = kural
    durumlar = [
        ("TETİKLENDİ" if k1_tetik else "TETİKLENMEDİ",
         {"kart_ilk_commit": kart_ilk.isoformat(), "enstrumantasyon_ilk_commit": enstr_ilk.isoformat(),
          "okuma_kaydi_ilk_satir": None if ilk_kayit is None else ilk_kayit.isoformat()}),
        (k2, {"D": n_D, "n_min_karar": n_min, "pencere_ust_siniri": ust_sinir.isoformat()}),
        ("UYGULANDI", {"sayilmayan_etiketsiz_sayfa_satiri": len(sayilmayan),
                       "satirlar": [{"ts": r["ts"], "durum": r["durum"], "http": r["http"]} for r in sayilmayan]}),
        ("TETİKLENDİ" if kaldirildi else "TETİKLENMEDİ",
         {"kural": kart["kural_anahtari"], "pencere_durumlari": gecerli_iz,
          "not": "netleştirme (7): yalnız KALDIRILMA ölçülür; geç/eksik/kısmi okuma K1'in kendisinde sayılır"}),
        ("TETİKLENDİ" if sir["bulgu_sayisi"] else "TETİKLENMEDİ",
         {"bulgu_sayisi": sir["bulgu_sayisi"], "bulgular": sir["bulgular"], "denetciler": sir["denetciler"],
          "envanterin_kendi_attigi": sir["envanterin_kendi_attigi"]}),
        ("ÖLÇÜLMEDİ — kill #5 akışı kapattı" if pk_nk is None else ("TETİKLENDİ" if pk_tutmayan else "TETİKLENMEDİ"),
         {"tutmayan": pk_tutmayan}),
        ("UYGULANDI", {"etiketli_okuma": dict(sorted(etiketli.items())), "sentetik_karar": len(kararlar["sentetik"])}),
        ("TETİKLENMEDİ" if tau_w_ayni else "TETİKLENDİ",
         {"acilis": {"tau": str(kart_acilis["tau"]), "W_saat": kart_acilis["W_saat"]},
          "simdi": {"tau": str(kart["tau"]), "W_saat": kart["W_saat"]}}),
    ]
    return [{"no": no, "madde": madde, "durum": durum, "kanit": kanit}
            for no, (madde, (durum, kanit)) in enumerate(zip(kart["kill_list"], durumlar), 1)]


# ================================================================================================
# ANA AKIŞ
# ================================================================================================

def _d_ozeti(D, kararlar, d_ilgili=None) -> dict:
    dagilim = {"atifli": sum(1 for d in D if d["atif"]), "yok": sum(1 for d in D if not d["atif"])}
    dagilim.update({t: sum(1 for d in D if t in d["atif"]) for t in KE.ATIF_TURLERI})
    return {"deger": len(D), "atif_dagilimi": dagilim, "pencere_disi": kararlar["pencere_disi"],
            "kararlar": [{"sira": d["sira"], "tarih": d["tarih"], "kimlik": d["kimlik"], "zaman": d["zaman"].isoformat(),
                          "baslik": d["baslik"], "atif_turleri": sorted(d["atif"]),
                          **({} if d_ilgili is None else {"ilgili": d["sira"] in d_ilgili})} for d in D],
            "sentetik_ayrilan": [{"sira": d["sira"], "tarih": d["tarih"], "kimlik": d["kimlik"],
                                  "isaretler": d["sentetik"]} for d in kararlar["sentetik"]]}


def say(girdi: pathlib.Path) -> dict:
    beyan = butunluk(girdi)
    try:
        kart = kart_coz((girdi / "kart.yaml").read_text(encoding="utf-8"))
        kart_acilis = esik_alanlari((girdi / "kart_acilis.yaml").read_text(encoding="utf-8"))
    except OSError as e:
        raise GirdiHatasi(f"kart okunamadı ({type(e).__name__})") from e
    kunye = _json(girdi / "kunye.json")
    envanter = _json(girdi / "karar_envanteri.json")
    okuma_metni = (girdi / "okuma.jsonl").read_text(encoding="utf-8")
    satirlar, okuma_denetimi = okuma_kaydi_oku(okuma_metni)
    bas, son = kart["bas"], kart["son"]
    kararlar = kararlari_kur(envanter, _json(girdi / "karar_zamanlari.json"), bas, son)
    D = kararlar["D"]
    gercek = gercek_okumalar(satirlar, bas, son)
    pk_nk_zamani = an(kunye["pk_nk_zamani"])
    gerekli = {r["kimlik"] for r in gercek} | {kart["pk"]["sayfa"], kart["ek_nk"]["sayfa"]}
    if None in gerekli:
        raise GirdiHatasi("kimliksiz gerçek okuma satırı var — sayfa eşlenemez")
    eksik = sorted(k for k in gerekli if not (girdi / SAYFA_DIZINI / f"{k}.md").is_file())
    if eksik:
        raise GirdiHatasi(f"sayfa anlık görüntüsü yok: {', '.join(eksik)}")
    sayfalar = {k: sayfa_goruntusu(girdi / SAYFA_DIZINI / f"{k}.md", k) for k in sorted(gerekli)}
    sayfa_tok = {k: s["tokenler"] for k, s in sayfalar.items()}
    ek_metinler = {p.relative_to(girdi).as_posix(): p.read_text(encoding="utf-8", errors="replace")
                   for p in sorted((girdi / SAYFA_DIZINI).glob("*.md"))}
    ek_metinler.update({ad: (girdi / ad).read_text(encoding="utf-8") for ad in ("karar_zamanlari.json", "kunye.json")})
    sir = sir_denetimi(okuma_metni, satirlar, envanter, ek_metinler)
    kural = kural_kaldirildi_mi(kunye["kural_0_5"]["iz"], bas, son)
    esik_ayni = (kart["n_min"], kart["kolon_esikleri"]) == (kart_acilis["n_min"], kart_acilis["kolon_esikleri"])
    pk_nk = None if sir["bulgu_sayisi"] else pk_nk_denetle(kart, satirlar, gercek, sayfalar, pk_nk_zamani)
    kill = kill_degerlendir(kart, kunye, satirlar, kararlar, sir, pk_nk, kart_acilis, kural)
    if sir["bulgu_sayisi"]:   # kill #5: akış KAPANIR — diğer maddelerin kanıtı (D, sayımlar) da yayılmaz
        kill = [m if m["no"] == 5 else {**m, "durum": "DEĞERLENDİRİLMEDİ — kill #5 akışı kapattı", "kanit": {}}
                for m in kill]
    sonuc = {
        "sema": SEMA, "kart": kart["card_id"], "arac": ARAC, "hukum": None,
        "gecerlilik": None,
        "parametreler": {
            "tau": f"{kart['tau'].numerator}/{kart['tau'].denominator}", "tau_ondalik": float(kart["tau"]),
            "tau_yerleri": kart["tau_yerleri"], "W_saat": kart["W_saat"], "W_yerleri": kart["W_yerleri"],
            "pencere": {"baslangic": bas.isoformat(), "bitis": son.isoformat(), "kural": "[baslangic, bitis)"},
            "n_min_karar": kart["n_min"],
            "esikler": {k: {"ad": a, "deger": float(v)} for k, (a, v) in kart["kolon_esikleri"].items()},
            "k4_atif_turleri": kart["k4_turleri"], "kaynak": "girdi/kart.yaml (esikler bağlayıcı; "
            "olcum_plani + netleştirme kıyaslandı)"},
        "netlestirme_uygulamasi": NETLESTIRME_UYGULAMASI,
        "girdi": {"dosyalar": beyan, "kunye": kunye, "okuma_kaydi": okuma_denetimi,
                  "sayfalar": {k: {"sha256": s["sha256"], "tazeleme": s["tazeleme"], "token": len(s["tokenler"]),
                                   "kayitta_ayni_ozetli_okuma": [r["ts"] for r in satirlar if r["kimlik"] == k
                                                                 and r["sha256"] == s["sha256"]]}
                               for k, s in sayfalar.items()}},
        "kill_list": kill,
    }
    if sir["bulgu_sayisi"]:
        sonuc["hukum"] = HUKUM_AKIS
        sonuc["gecerlilik"] = {"alet_dogrulandi": False, "nedenler": ["kill #5"]}
        return sonuc
    sonuc["pk_nk"] = pk_nk
    nedenler = []
    kapanis_kaniti = an(kunye["dondurma_ani"]) >= son and okuma_denetimi["son_ts"] is not None \
        and an(okuma_denetimi["son_ts"].replace("Z", "+00:00")) >= son
    if kill[0]["durum"] == "TETİKLENDİ":
        nedenler.append(HUKUM_KART_ONCE)
    if kill[7]["durum"] == "TETİKLENDİ":
        nedenler.append(HUKUM_TAU_W)
    if not esik_ayni:
        nedenler.append(HUKUM_ESIK)
    if not pk_nk["tuttu"]:
        nedenler.append(HUKUM_GECERSIZ_ALET)
    if not kapanis_kaniti:
        nedenler.append(HUKUM_ARA)
    sonuc["gecerlilik"] = {"alet_dogrulandi": pk_nk["tuttu"], "nedenler": nedenler,
                           "pencere_kapanis_kaniti": kapanis_kaniti}
    if nedenler:
        sonuc["hukum"] = nedenler[0]
        S, dolu = k1_gunleri(gercek, bas, son)
        sonuc["betimleyici_ara_rapor"] = {
            "etiket": BETIMLEYICI_ETIKET,
            "not": "K2–K4 τ'ya bağlıdır ve alet/pencere doğrulanmadan betimleyici olarak da YAYILMAZ",
            "K1": {**oran(len(dolu), len(S)), "S_gunleri": [g.isoformat() for g in S],
                   "dolu_gunler": [g.isoformat() for g in dolu], "okuma_sayisi": len(gercek)},
            "D": _d_ozeti(D, kararlar)}
        return sonuc
    sonuc["hukum"] = HUKUM_GECERLI
    sonuc["kolonlar"] = kolonlari_hesapla(kart, gercek, D, sayfa_tok, kural[0])
    sonuc["D"] = _d_ozeti(D, kararlar, set(sonuc["kolonlar"]["K3"]["D_ilgili"]))
    return sonuc


NETLESTIRME_UYGULAMASI = [
    {"madde": "(1) S = pencere içindeki UTC takvim günleri",
     "uygulama": "`pencere_gunleri`: pencereyle KESİŞEN UTC günleri; açılış ve kapanış yarım günleri DAHİL"},
    {"madde": "(2) pencere ve D commit/olay damgasıyla [bas, son)",
     "uygulama": "`pencerede` (okuma `ts`, karar `zaman` = kaynağının giriş commit'i — dondur.py); "
                 "kapanış kanıtı yoksa ARA RAPOR"},
    {"madde": "(3) K2 tanımı `esikler` cümlesi", "uygulama": "`kolonlari_hesapla`: K2 = eşleşen okuma / okuma; "
     "çift oranı betimleyici"},
    {"madde": "(4) W=48 sa commit saatiyle kesin", "uygulama": "`ilgili_mi`: 0 ≤ Δ < W (saniye çözünürlüğü)"},
    {"madde": "(5) K4 paydası D — GEÇERSİZ, netleştirme c ile DEĞİŞTİRİLDİ (aşağıda)",
     "uygulama": "uygulanmaz; 'taze = okuma anında is_stale=false' kısmı (5a) ile birlikte geçerli"},
    {"madde": "(6) τ ve sayfa token kümesi tam içerik, değiştirilmeden",
     "uygulama": "`esik_alanlari` (τ karttan) + `sayfa_goruntusu` (normalize_tokens(tam içerik))"},
    {"madde": "(7) kill #4: kaldırılma; geç/eksik/kısmi okuma K1'de",
     "uygulama": "`kural_kaldirildi_mi` + `dogrulanmis` (kısmi okuma = tam GET kaydı, sayılır)"},
    {"madde": "(8) kill #6 HARFİYEN", "uygulama": "`say`: PK/NK tutmazsa kolon/D üst düzeyde YOK; "
     "K1 ve D yalnız 'hüküm DEĞİL' etiketli betimleyici"},
    {"madde": "(9) sayım kodu bu dizinde", "uygulama": "sayim.py + dondur.py; çivi tests/test_edg103_sayim_v610.py"},
    {"madde": "b (1a) S = pencereyle kesişen 8 UTC günü", "uygulama": "`pencere_gunleri` (yarım uç günler dahil)"},
    {"madde": "b (4a) W yarı-açık 0 ≤ Δ < 48 sa", "uygulama": "`ilgili_mi`"},
    {"madde": "b (5a) taze ölçülemez → K4 None + üst sınır; kıyas yalnız kesinse",
     "uygulama": "`_k4` + `okuma_tazeligi` (şema is_stale taşırsa betik durur)"},
    {"madde": "b (6a) EK NK kill #6 kapsamında harfiyen",
     "uygulama": "`pk_nk_denetle`: ifade sayfanın BAŞLIK satırında (kartın 'hükmünü taşımalı'sı)"},
    {"madde": "b (10) girdi/ depoya girer, sır taşımaz",
     "uygulama": "dondur.py yazmadan önce her dosyayı notify desenleriyle tarar, eşleşmede YAZMAZ; sayım kill #5 "
                 "aynı taramayı `notify_taramasi` ile dondurulmuş her metne uygular"},
    {"madde": "c (5) DÜZELTME: K4 paydası `esikler`deki 'atıflı kararlar'; D paydası betimleyici",
     "uygulama": "`_k4`: payda = D'de sayfa/recall/memory/kart_benzer atfı taşıyan kararlar (`atifli_karar`); "
                 "`betimleyici_D_paydasi`; D_ilgili boşsa ÖLÇÜLEMEDİ"},
]


def rapor_md(s: dict) -> str:
    satir = [f"# EDG-2026-103 sayım — {s['parametreler']['pencere']['baslangic']} → "
             f"{s['parametreler']['pencere']['bitis']}", "", f"**hukum:** {s['hukum']}", ""]
    p = s["parametreler"]
    satir += [f"τ = {p['tau']} ({p['tau_ondalik']}) · W = {p['W_saat']} sa · n_min_karar = {p['n_min_karar']} "
              "(hepsi KARTTAN)", ""]
    if "kolonlar" in s:
        satir += ["## Kolonlar — eşik karşılaştırması (hüküm Rol-1'in)", "",
                  "| Kolon | pay/payda | değer | eşik | karşılaştırma | neden |", "|---|---|---|---|---|---|"]
        for ad, k in s["kolonlar"].items():
            pp = f"{k['pay']}/{k['payda']}" if k.get("pay") is not None else f"?/{k['payda']}"
            if ad == "K4" and k.get("ust_sinir"):
                pp += f" (üst sınır {k['ust_sinir']['kesir']})"
            satir.append(f"| {ad} | {pp} | {k['deger']} | {k['esik']['yon']} {k['esik']['deger']} | "
                         f"{k['karsilastirma']} | {k.get('neden') or ''} |")
        satir += ["", f"**D** = {s['D']['deger']} (pencere dışı {s['D']['pencere_disi']}, sentetik ayrılan "
                  f"{len(s['D']['sentetik_ayrilan'])}) · atıf dağılımı {s['D']['atif_dagilimi']}", ""]
    elif "betimleyici_ara_rapor" in s:
        b = s["betimleyici_ara_rapor"]
        satir += [f"## Betimleyici ara rapor — {b['etiket']}", "", b["not"], "",
                  f"- K1 (betimleyici): {b['K1']['kesir']} — dolu günler {b['K1']['dolu_gunler']}",
                  f"- D (betimleyici): {b['D']['deger']}", ""]
    if s.get("pk_nk"):
        pk = s["pk_nk"]
        satir += ["## PK/NK", "", f"tuttu: **{pk['tuttu']}**",
                  f"- PK (a) okuma: {pk['pk']['a_okuma']['tuttu']} · (b) ilgi: {pk['pk']['b_ilgi']['tuttu']} "
                  f"{[x['jaccard'] for x in pk['pk']['b_ilgi']['ayrinti']]} · (c) atıf: {pk['pk']['c_atif']['tuttu']}",
                  f"- NK atıfsız: {pk['nk']['atifsiz']['tuttu']} · ilgisiz: {pk['nk']['ilgisiz']['tuttu']}",
                  f"- EK NK ({pk['ek_nk']['sayfa']} '{pk['ek_nk']['ifade']}'): {pk['ek_nk']['tuttu']}", ""]
    satir += ["## Kill-list (kartın metniyle)", ""]
    satir += [f"{m['no']}. **{m['durum']}** — {m['madde']}" for m in s["kill_list"]]
    satir += ["", "## Netleştirme uygulaması", ""]
    satir += [f"- {n['madde']}: {n['uygulama']}" for n in s["netlestirme_uygulamasi"]]
    return "\n".join(satir) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="EDG-2026-103 sayımı (dondurulmuş girdiden; hüküm Rol-1'in).")
    ap.add_argument("--girdi", required=True, help="dondur.py'nin ürettiği dizin")
    ap.add_argument("--cikti-json", help="sonuç JSON yolu (yoksa stdout)")
    ap.add_argument("--cikti-md", help="insan-okur rapor yolu")
    a = ap.parse_args(argv)
    girdi = pathlib.Path(a.girdi)
    if not girdi.is_dir():
        print(f"HATA: girdi dizini yok: {girdi}", file=sys.stderr)
        return 2
    try:
        sonuc = say(girdi)
    except KartHatasi as e:
        print(f"HATA: kart çözümlenemedi — sayım YAPILMADI: {e}", file=sys.stderr)
        return 2
    except GirdiHatasi as e:
        print(f"HATA: girdi — sayım YAPILMADI: {e}", file=sys.stderr)
        return 1
    metin = json.dumps(sonuc, ensure_ascii=False, indent=2) + "\n"
    if a.cikti_md:
        pathlib.Path(a.cikti_md).write_text(rapor_md(sonuc), encoding="utf-8")
    if a.cikti_json:
        pathlib.Path(a.cikti_json).write_text(metin, encoding="utf-8")
        print(f"hukum: {sonuc['hukum']} → {a.cikti_json}")
    else:
        sys.stdout.write(metin)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
