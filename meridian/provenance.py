"""provenance.py — anahtar köken takibi: üretici↔tüketici alan ayrışmasının çalışma-anı dedektörü.

Baskın sessiz-kusur sınıfı tek cümledir: "aynı yasanın iki uygulaması var ve sessizce ayrışmış."
Veri biçiminde bu şu demek: bir modül `{"dormant_setup": ...}` yazar, başka modül `.get("dormant")`
okur — istisna yoktur, okuma None döner, dal `continue` ile atlanır, sayaç sessizce küçülür ve
binlerce satır yanlış etiketle deftere geçer. Testler bunu göremez, çünkü her test KENDİ
fikstürünü kurar: üretici ile tüketicinin beklentisini aynı el yazar. Alan alan parite testi
yazmak da çözüm değildir (unutulan ilk alanda sınıf geri döner); bu modül sınıfı YAPISAL ölçer —
uygulamanın KENDİ koşusu sondadır. `store.read_json/read_jsonl` sonuçları izlenen sözlüklerle
sarılır; her `.get(k)` ve `d[k]` isabet/ıska olarak kaydedilir. Koşu bitince:
okunan ∧ hiçbir satırda YOK → SÜRÜKLENME · yazılan ∧ hiç okunmayan → ÖLÜ ALAN.

GİRİŞLER: `sar` (store okuma yollarının çağırdığı sarmalayıcı; kapalıyken nesneyi değiştirmeden
döndürür — sıfır maliyet), `basla`/`dur`/`aktif`, `oturum` (yeniden-girişli ölçüm bağlamı: iç içe
ölçüm dıştakini ezmez), `rapor` (salt-okunur hüküm: drift / dead_fields / inconclusive).

KURT MASALI YASAĞI dedektörün kendisine de uygulanır: boş artefakt yargılanmaz (kanıt yokluğu ≠
sürüklenme); varsayılanlı okuma (`.get(k, x)`) ayrı sayılır, ihlal değildir; `OPSIYONEL` muafiyeti
GEREKÇE ister; `HARITA` anahtarı ŞEMA değil VERİ olan artefaktları beyan eder; çok-biçimli
defterde (events gibi) yokluk hüküm vermez, "belirsiz" yazılır. Dedektör hiçbir taban YAZMAZ:
her şey süreç-içi bellekte birikir. Varsayılan KAPALI; test oturumu ve günlük döngü açar.
"""
from __future__ import annotations

import threading
from collections import defaultdict

# ---- toplama durumu (süreç-içi; diske hiçbir şey yazılmaz) ----
_lock = threading.Lock()
_active = False
_read_hit: dict[str, set] = defaultdict(set)      # artefakt -> okunup BULUNAN anahtarlar
_read_miss: dict[str, set] = defaultdict(set)     # artefakt -> okunup BULUNAMAYAN anahtarlar
_read_defaulted: dict[str, set] = defaultdict(set)  # artefakt -> varsayılanla okunanlar (isteğe bağlı)
_present: dict[str, set] = defaultdict(set)       # artefakt -> verinin GERÇEKTE taşıdığı anahtarlar
_rows: dict[str, int] = defaultdict(int)          # artefakt -> görülen satır/nesne sayısı
_keycount: dict[str, int] = defaultdict(int)      # artefakt -> satır başına anahtar sayılarının toplamı
_keysets: dict[str, set] = defaultdict(set)       # artefakt -> farklı anahtar-kümesi imzaları
_disc: dict[str, dict] = defaultdict(lambda: defaultdict(int))   # artefakt -> ayırt edici alan sayımı

# AYIRT EDİCİ ALANLAR: varlığı "bu defterde birden çok KAYIT TÜRÜ var" demektir.
AYIRTEDICI = ("event", "type", "kind")
KEYSET_TAVAN = 256      # bellek sınırı; imza çeşitliliği bu sayıya kadar ölçülür

# ÇOK-BİÇİMLİ DEFTER EŞİĞİ. events.jsonl gibi defterlerde her olay TÜRÜ farklı alan taşır: birlik
# kümesi 40+, tipik satır 4-5 anahtar. Böyle bir defterde "hiçbir satırda yok" ARGÜMAN DEĞİLDİR —
# o alanı taşıyan olay türü henüz yaşanmamış olabilir. İlk koşuda tam bu oldu: dedektör
# events.jsonl'de `plan_id` sürüklenmesi bildirdi, oysa üretici (loop.py:114) alanı doğru yazıyor;
# yalnızca o beş olay türünden dördü bu defterde hiç ateşlememişti. Kanıtlayamadığımız yere
# "ihlal" değil "belirsiz" yazarız — kurt masalı yasağı dedektörün KENDİSİ için de geçerlidir.
HETEROJEN_KAT = 3.0

_SENTINEL = object()

# HARİTA ŞEKİLLİ ARTEFAKTLAR: anahtarları ŞEMA değil VERİdir. `brain_cooldown.json` yalnız
# DİNLENMEDEKİ beyni taşır; `nous` okuyup None almak tasarımın kendisidir, sürüklenme değil.
# Şemalı bir defterde aynı okuma ihlaldir — fark, artefaktın sözleşmesindedir. Bu yüzden burada
# susturma değil BEYAN yapılır ve her satır gerekçe ister.
HARITA: dict[str, str] = {
    "brain_cooldown.json": "beyin adı → dinlenme kaydı; yalnız dinlenmedeki beyin yazılır",
    "bars_fingerprint.json": "dosya adı → parmak izi",
    "monotonic_state.json": "alan adı → son görülen değer",
    "ownership_state.json": "dosya adı → sahiplenilmiş alanlar",
    "mechanism_beats.json": "mekanizma adı → son nabız; yalnız ÇALIŞMIŞ mekanizma yazılır "
                            "(hiç koşmamışı watchdog üretkenlik dedektörü 'aç' diye ayrıca söyler)",
}

# İSTEĞE BAĞLI OLDUĞU YAZILI ALANLAR. Her kayıt bir GEREKÇE taşımak zorundadır; gerekçesiz
# giriş muafiyet saymaz (grant_amnesty ile aynı disiplin).
OPSIYONEL: dict[tuple[str, str], str] = {
    ("portfolio.json", "peak_equity"): "eski defterlerde yok; ilk turda doğar",
    ("heartbeat.json", "explore_mode"): "yalnız keşif modu açıkken yazılır",
}


def _kayit_sekli(art: str, row: dict) -> None:
    """Satırın ŞEKLİNİ biriktir: imza çeşitliliği + ayırt edici alan sayımı. `_lock` çağıranda tutulur."""
    if len(_keysets[art]) < KEYSET_TAVAN:
        _keysets[art].add(frozenset(row.keys()))
    for d in AYIRTEDICI:
        if d in row:
            _disc[art][d] += 1


class _Izlenen(dict):
    """dict'in birebir davranışı + okuma kaydı. `dict` alt sınıfı olduğu için json.dump, ==,
    kopyalama ve tüm tüketiciler hiçbir değişiklik olmadan çalışır."""

    __slots__ = ("_art",)

    def __init__(self, art: str, data: dict):
        super().__init__(data)
        self._art = art

    def get(self, key, default=None):
        var = dict.__contains__(self, key)
        with _lock:
            if var:
                _read_hit[self._art].add(key)
            elif default is not None:
                # varsayılan VERİLMİŞ: çağıran yokluğu tasarımca karşılıyor — sürüklenme değil
                _read_defaulted[self._art].add(key)
            else:
                _read_miss[self._art].add(key)
        return dict.get(self, key, default)

    def __getitem__(self, key):
        # d[k] ıskada KeyError fırlatır, yani zaten gürültülüdür; burada yalnız İSABETİ sayıyoruz
        # ki "yazılıyor ama hiç okunmuyor" ölçümü eksik çıkmasın.
        if dict.__contains__(self, key):
            with _lock:
                _read_hit[self._art].add(key)
        return dict.__getitem__(self, key)


def sar(art: str, obj):
    """store okuma yollarının çağırdığı sarmalayıcı. Kapalıyken nesneyi DEĞİŞTİRMEDEN döndürür —
    üretim yolunda sıfır maliyet ve sıfır davranış farkı."""
    if not _active:
        return obj
    if isinstance(obj, dict):
        with _lock:
            _present[art] |= set(obj.keys())
            _rows[art] += 1
            _keycount[art] += len(obj)
            _kayit_sekli(art, obj)
        return _Izlenen(art, obj)
    if isinstance(obj, list):
        out = []
        for r in obj:
            if isinstance(r, dict):
                with _lock:
                    _present[art] |= set(r.keys())
                    _rows[art] += 1
                    _keycount[art] += len(r)
                    _kayit_sekli(art, r)
                out.append(_Izlenen(art, r))
            else:
                out.append(r)
        return out
    return obj


def basla() -> None:
    global _active
    with _lock:
        _read_hit.clear(); _read_miss.clear(); _read_defaulted.clear()
        _present.clear(); _rows.clear(); _keycount.clear()
        _keysets.clear(); _disc.clear()
    _active = True


def dur() -> None:
    global _active
    _active = False


def _anlik() -> dict:
    return {"a": _active,
            "hit": {k: set(v) for k, v in _read_hit.items()},
            "miss": {k: set(v) for k, v in _read_miss.items()},
            "def": {k: set(v) for k, v in _read_defaulted.items()},
            "pres": {k: set(v) for k, v in _present.items()},
            "rows": dict(_rows), "kc": dict(_keycount),
            "ks": {k: set(v) for k, v in _keysets.items()},
            "disc": {k: dict(v) for k, v in _disc.items()}}


def _geri(sn: dict) -> None:
    global _active
    with _lock:
        for d, k in ((_read_hit, "hit"), (_read_miss, "miss"), (_read_defaulted, "def"),
                     (_present, "pres"), (_keysets, "ks")):
            d.clear(); d.update({a: set(b) for a, b in sn[k].items()})
        _rows.clear(); _rows.update(sn["rows"])
        _keycount.clear(); _keycount.update(sn["kc"])
        _disc.clear()
        for a, b in sn["disc"].items():
            _disc[a].update(b)
    _active = sn["a"]


class oturum:
    """YENİDEN-GİRİŞLİ ÖLÇÜM. İç içe bir ölçüm (ör. dedektörün kendi testi) DIŞTAKİNİ ezmemeli.
    Canlıda yaşandı: test fikstürü `basla()` çağırınca oturum boyu biriken 145 bin satırlık ölçüm
    sıfırlandı ve paket sonundaki rapor "1 artefakt" dedi. Bir bekçi, ölçtüğü şeyi perturbe
    etmemeli — kendi kendini de (2026-07-22)."""

    def __enter__(self):
        self._sn = _anlik()
        basla()
        return self

    def __exit__(self, *_):
        _geri(self._sn)
        return False


def aktif() -> bool:
    return _active


def rapor() -> dict:
    """Salt-okunur hüküm. Hiçbir dosya yazılmaz, hiçbir taban ilerletilmez."""
    surukleme, olu, belirsiz = [], [], []
    for art in sorted(set(_read_miss) | set(_present)):
        satir = _rows.get(art, 0)
        mevcut = _present.get(art, set())
        # KORUMA 1: BOŞ artefakt yargılanmaz. `satir`ı tek başına saymak yetmiyordu — boş bir
        # sözlük ({} olarak 11 kez okunan brain_cooldown.json) 11 "satır" sayılıp her okuması
        # sürüklenme sanılıyordu. Ölçüt satır sayısı değil, verinin HERHANGİ bir anahtar taşıması:
        # hiç anahtar görülmediyse üreticinin ne yazdığı bilinmiyordur, hüküm verilemez.
        if satir == 0 or not mevcut or art in HARITA:
            continue
        # ÇOK-BİÇİMLİLİK ÖLÇÜSÜ: birlik kümesi, tipik satırdan kat kat büyükse defter tek şemalı
        # değildir (events.jsonl: ~40 farklı alan, satır başına ~4). Böyle bir defterde yokluk
        # hüküm vermez — 'belirsiz' yazılır.
        # ÇOK-BİÇİMLİLİK — iki bağımsız ölçüt, biri yeterli:
        #  (a) AYIRT EDİCİ ALAN: satırların ~hepsinde `event`/`type`/`kind` var VE anahtar-kümesi
        #      imzaları çeşitli. Bu doğrudan "tek dosyada birden çok kayıt TÜRÜ" demektir.
        #  (b) ORAN: birlik kümesi, tipik satırdan kat kat büyük.
        # (a) ilkelidir; (b) ayırt edici alanı olmayan karışık defterler için ağdır.
        ort = _keycount.get(art, 0) / satir
        imza = len(_keysets.get(art, ()))
        disc = max(_disc.get(art, {}).values(), default=0)
        heterojen = (disc >= 0.9 * satir and imza >= 3) or (ort > 0 and len(mevcut) > HETEROJEN_KAT * ort)
        for k in sorted(_read_miss.get(art, set())):
            if k in mevcut:
                continue                 # bazı satırda var — kısmi alan, sürüklenme değil
            if (art, k) in OPSIYONEL and str(OPSIYONEL[(art, k)]).strip():
                continue                 # KORUMA 3: GEREKÇELİ muafiyet
            hedef = belirsiz if heterojen else surukleme
            hedef.append({"artifact": art, "key": k, "rows": satir,
                          "detail": (f"{satir} satırın hiçbirinde yok, ama defter çok-biçimli "
                                     f"(birlik {len(mevcut)} alan / satır ort {ort:.1f} / {imza} şema) — o alanı taşıyan "
                                     f"kayıt türü henüz yaşanmamış olabilir; KANITLANAMADI")
                                    if heterojen else
                                    f"{satir} satırın hiçbirinde yok — tüketici hep None okuyor"})
        okunan = _read_hit.get(art, set()) | _read_defaulted.get(art, set())
        for k in sorted(mevcut - okunan):
            olu.append({"artifact": art, "key": k, "rows": satir})
    return {"ok": not surukleme, "drift": surukleme, "inconclusive": belirsiz, "dead_fields": olu,
            "artifacts": len(_rows), "rows_seen": sum(_rows.values())}
