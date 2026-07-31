"""test_anayasa_hypothesis_v143.py — ANAYASA YASALARININ PROPERTY TESTLERİ (WP-H/H1, 2026-07-31).

NEDEN VAR. Bu depodaki testlerin neredeyse tamamı ÖRNEK testidir: bir girdi elle yazılır, bir
çıktı elle beklenir. Örnek testinin yapısal körlüğü şudur — aynı el iki tarafı da yazar, yani
testin hayal edebildiği girdiler dışında hiçbir şey ölçülmez. Bu depoda kaybedilen şeyler (NaN'ın
tele sızması, JSONL'de yarım satır, defterde damgasız aralık) tam olarak "kimsenin aklına gelmeyen
girdi" sınıfındandır.

Property testi soruyu tersine çevirir: girdiyi ÜRETEÇ yazar, biz yalnız YASAYI yazarız. Hypothesis
karşı-örnek bulursa onu KÜÇÜLTÜR (shrink) — yani rapor "şu 400 baytlık yapı patlattı" değil, "şu
minimal yapı patlattı" olur ve kök neden okunabilir kalır.

BEŞ YASA, BEŞ BÖLÜM:
  A) `store.sanitize`      — UYDURMA YASAĞI'nın KOD KAPISI: ölçülemeyen (NaN/±Inf) None olur ve
                             çıktı her zaman `allow_nan=False` ile serileştirilebilir.
  B) depo roundtrip        — H9 parite garantisinin property hâli: dosya arka ucu ile SQLite arka
                             ucu AYNI belgeyi döndürür, iki kez yazım idempotenttir, tip korunur.
  C) `store.update_json`   — kayıpsızlık: çok-adımlı, ÇOK İŞ PARÇACIKLI append/update/read
                             dizilerinde sayaç artışı kaybolmaz (durum makinesi).
  D) takvim kapısı         — seans-dışı satır `sanitize_bars` çıktısında ASLA görünmez; güvensiz
                             dönem `measurement_bars` çıktısında ASLA görünmez.
  E) defter kaynak damgası — ileri yoldan (`loop._persist_trade`) geçen her satır `live_paper`
                             taşır; damga bir kez basılır, ikinci yazar onu EZEMEZ.

ÖLÇÜM DİSİPLİNİ — ÜRETECİN KISITLARI UYDURMA DEĞİL, ÖLÇÜLMÜŞTÜR. Aşağıda birkaç yerde üreteç
bilerek daraltıldı. Her daraltmanın yanında NEDEN yazar ve nedenlerin tamamı bu turda çalıştırılan
bir kenar ölçümünden gelir (scratchpad probe, 2026-07-31). Daraltmayı gerekçesiz yapmak, testin
ölçmediği bir alanı ölçüyormuş gibi göstermek olurdu.

KUM HAVUZU HER ÖRNEKTE TAZE. `sandbox_state` fikstürü FONKSİYON kapsamlıdır: Hypothesis onu tek
bir test için üretilen ONLARCA örnek arasında PAYLAŞTIRIRDI ve durum örnekler arası sızardı (yani
5. örnek 4. örneğin defterini görürdü — testi sıra bağımlı yapan tam da bu). Bu yüzden kum havuzu
fikstür DEĞİL, örnek başına açılıp kapanan bir bağlam yöneticisidir.
"""
from __future__ import annotations

import contextlib
import json
import math
import shutil
import tempfile
import threading
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, invariant, rule

from meridian import config, ledgerstamp, storage, store
from meridian.adapters import data as data_adapter

# ---- HYPOTHESIS AYARI (BU DOSYADA, conftest'te DEĞİL) -------------------------------------------
# `deadline=None` GEREKÇELİ: bu dosyadaki örneklerin çoğu DİSKE dokunur (tmp dizin + sqlite şeması).
# Örnek başına duvar-saati diskin o anki yüküne bağlıdır ve bir deadline, YASANIN ihlalini değil
# makinenin meşguliyetini ölçerdi — yani kırmızı, kusur değil gürültü anlamına gelirdi.
# `max_examples` iş yüküne göre AYRI ayrı verilir: saf-hesap yasaları ucuz, disk yasaları pahalı.
_SAF = settings(deadline=None, max_examples=200)
_DISK = settings(deadline=None, max_examples=50,
                 suppress_health_check=[HealthCheck.too_slow])
_AGIR = settings(deadline=None, max_examples=25,
                 suppress_health_check=[HealthCheck.too_slow])


# =================================================================================================
# KUM HAVUZU
# =================================================================================================
@contextlib.contextmanager
def kum_havuzu(db: bool = False):
    """Örnek BAŞINA taze `state/` dizini. `db=True` ise SQLite şeması kurulur (defterler DB'ye gider).

    SÖKÜMDE ÜÇ ŞEY GERİ ALINIR ve üçü de bu depoda belgeli bir sızıntı sınıfına karşılık gelir:
      1. `storage.close_all()` — bağlantı havuzu YOLA göre anahtarlıdır; kapatılmayan bağlantı
         silinmiş bir tmp dizinine tutunur ve sonraki örnek onu yeniden kullanmaya çalışırdı.
      2. `store._FILE_LOCKS` — kilit nesneleri (state_dizini, ad) ile anahtarlıdır; temizlenmezse
         süreç ömrü boyunca örnek başına bir kilit birikir (yavaş sızıntı, açık dosya tanıtıcısı).
      3. `config.STATE` — geri konmazsa SONRAKİ test canlı `state/`e yazar ve conftest'in canlı-
         sızıntı bekçisi onu (haklı olarak) düşürür.
    """
    kok = Path(tempfile.mkdtemp(prefix="meridian-hyp-"))
    st_dir = kok / "state"
    st_dir.mkdir(parents=True)
    eski = (config.STATE, config.HISTORY, config.BARS)
    config.STATE, config.HISTORY, config.BARS = st_dir, st_dir / "history", st_dir / "bars"
    storage.close_all()
    try:
        if db:
            storage.ensure_schema()
        yield st_dir
    finally:
        storage.close_all()
        anahtar = str(st_dir)
        with store._LOCKS_GUARD:
            for k in [k for k in store._FILE_LOCKS if k[0] == anahtar]:
                store._FILE_LOCKS.pop(k, None)
        config.STATE, config.HISTORY, config.BARS = eski
        shutil.rmtree(kok, ignore_errors=True)


def digest(obj) -> str:
    """NORMALİZE DİGEST: anahtar SIRASINDAN bağımsız karşılaştırma.

    Neden ham `==` yetmez: SQLite yolu satırı kolon sırasına göre yeniden kurar, dosya yolu ise
    yazıldığı sırayı korur. İki sözlük EŞİTTİR ama iki JSON metni değildir; digest karşılaştırması
    "aynı belge mi" sorusunu sorar, "aynı baytlar mı" sorusunu değil. `sort_keys` tam olarak bu
    ayrımı yapar; tip bilgisi (int vs float, bool vs int) json.dumps çıktısında KORUNUR
    (`1` ≠ `1.0` ≠ `true`), yani parite ölçümü tip sessizliğine düşmez."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False)


def yapraklar(obj):
    """Yapının tüm yaprak değerleri (sözlük ANAHTARLARI dahil) — invariant taraması için."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from yapraklar(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from yapraklar(v)
    else:
        yield obj


# =================================================================================================
# A) store.sanitize — UYDURMA YASAĞI'NIN KOD KAPISI
# =================================================================================================
# ÜRETEÇ KAPSAMI = `sanitize`in BEYAN ETTİĞİ SÖZLEŞME, bir fazlası değil. Docstring dört np dalı
# (floating/integer/bool_/ndarray) ve bir yerli-float dalı söz verir; üreteç tam olarak onları
# üretir. `np.datetime64`/`np.complex128` gibi BEYAN EDİLMEMİŞ tipleri üretmek, testi sözleşmenin
# dışında kırardı — yani var olmayan bir vaadi ölçerdi. (O tiplerin kapsanmadığı ÖLÇÜLMÜŞ bir
# olgudur ve bu satır onun kaydıdır; kapsama kararı sözleşme sahibinindir, testin değil.)
_METIN = st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=8)

_SKALER = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-(10 ** 12), max_value=10 ** 12),
    st.floats(allow_nan=True, allow_infinity=True),          # NaN/±Inf BİLEREK açık — yasanın konusu
    _METIN,
    st.builds(np.float64, st.floats(allow_nan=True, allow_infinity=True)),
    st.builds(np.float32, st.floats(width=32, allow_nan=True, allow_infinity=True)),
    st.builds(np.int64, st.integers(min_value=-(2 ** 62), max_value=2 ** 62)),
    st.builds(np.bool_, st.booleans()),
    st.builds(lambda xs: np.array(xs, dtype=float),
              st.lists(st.floats(allow_nan=True, allow_infinity=True), max_size=4)),
    st.builds(lambda xs: np.array(xs, dtype=np.int64),
              st.lists(st.integers(min_value=-(10 ** 9), max_value=10 ** 9), max_size=4)),
)

_YAPI = st.recursive(
    _SKALER,
    lambda alt: st.lists(alt, max_size=4) | st.dictionaries(_METIN, alt, max_size=4),
    max_leaves=14,
)


@_SAF
@given(x=_YAPI)
def test_sanitize_ciktisi_her_zaman_allow_nan_false_ile_serilesir(x):
    """YASA: `sanitize`ten geçen HİÇBİR yapı `allow_nan=False` serileştirmesini düşüremez.

    Bu tam olarak iki üretim yolunun sözleşmesidir: Starlette `JSONResponse` gövdeyi bu bayrakla
    dump eder (tek NaN → HTTP 500) ve tarayıcıdaki `JSON.parse` `NaN` jetonunu reddeder (pano
    dosyayı hiç okuyamaz). Yani bu property, iki gerçek arıza sınıfının ortak kapısıdır."""
    out = store.sanitize(x)
    json.dumps(out, allow_nan=False)     # istisna atarsa test düşer — mesaj Hypothesis'in shrink'i


@_SAF
@given(x=_YAPI)
def test_sanitize_sonlu_olmayan_hicbir_float_birakmaz(x):
    """YASA: çıktıda NaN/±Inf YOKTUR — ölçülemeyen değerin dürüst temsili `None`dır.

    `0.0`a çevirmek de serileştirilebilir bir çıktı verirdi; yasak olan tam olarak odur (UYDURMA
    YASAĞI): ölçülmemiş bir değeri ölçülmüş gibi göstermek."""
    for v in yapraklar(store.sanitize(x)):
        if isinstance(v, float):
            assert math.isfinite(v), f"sonlu olmayan float sızdı: {v!r}"


@_SAF
@given(x=_YAPI)
def test_sanitize_numpy_tipi_birakmaz(x):
    """YASA: çıktıda numpy tipi KALMAZ — `np.float64` `float`ın alt sınıfıdır ve `json` onu tanımaz.

    `type(v).__module__` ile ölçülür, `isinstance` ile DEĞİL: `isinstance(np.float64(1), float)`
    True döner, yani isinstance tabanlı bir kontrol tam da yakalaması gereken sızıntıya KÖRDÜR."""
    for v in yapraklar(store.sanitize(x)):
        assert type(v).__module__ != "numpy", f"numpy tipi sızdı: {type(v).__name__}"


@_SAF
@given(x=_YAPI)
def test_sanitize_idempotenttir(x):
    """YASA: `sanitize(sanitize(x)) == sanitize(x)`.

    Neden önemli: `write_json` sanitize eder, `append_jsonl` sanitize eder, `write_jsonl` SATIR
    BAŞINA sanitize eder — aynı yapı üretim yolunda birden çok kez geçebilir. İdempotent olmayan
    bir dönüştürücü, kaç kez çağrıldığına bağlı bir çıktı üretirdi ve bu fark hiçbir yerde
    görünmezdi."""
    bir = store.sanitize(x)
    iki = store.sanitize(bir)
    assert digest(bir) == digest(iki)


@_SAF
@given(x=st.dictionaries(_METIN, _SKALER, max_size=6))
def test_sanitize_sozluk_anahtarlarina_dokunmaz(x):
    """YASA: dönüşüm DEĞERLERE uygulanır; anahtar kümesi birebir korunur. Bir anahtarın sessizce
    düşmesi ya da değişmesi, defteri okuyan her tüketicinin alanını kaybetmesi demektir."""
    assert set(store.sanitize(x).keys()) == set(x.keys())


# =================================================================================================
# B) DEPO ROUNDTRIP — H9 PARİTE GARANTİSİNİN PROPERTY HÂLİ
# =================================================================================================
# ÖLÇÜLMÜŞ İKİ PARİTE BOŞLUĞU, ÜRETEÇTEN BİLEREK DIŞLANDI (probe, 2026-07-31 — ikisi de bugün
# hiçbir üretim yazarının ürettiği şekil DEĞİL, ama kayda geçmeleri gerekir):
#   (1) `write_json(<doc varlığı>, None)` → dosya `None` döndürür, DB `default` döndürür.
#       Kök neden: `storage.read_doc` "belge YOK" ile "belge JSON null" hâllerini AYNI `None` ile
#       temsil eder; `store.read_json` ikincisini varsayılana çevirir. Üretimde scoreboard/
#       portfolio/shadow_books daima SÖZLÜKTÜR, o yüzden üreteç sözlükle sınırlandı.
#   (2) `write_json("equity_curve.json", {})` → dosya `{}`, DB `{"points": []}`.
#       Kök neden: seri okuyucusu zarfı YENİDEN KURAR ve `points` anahtarını her zaman ekler.
#       Üretimde tek yazar `run.replay_seed`tir ve daima `{"version": …, "points": […]}` yazar.
_JSON_SKALER = st.one_of(
    st.none(), st.booleans(),
    st.integers(min_value=-(10 ** 12), max_value=10 ** 12),
    st.floats(allow_nan=False, allow_infinity=False, allow_subnormal=False),
    _METIN,
)
_JSON_YAPI = st.recursive(
    _JSON_SKALER,
    lambda alt: st.lists(alt, max_size=4) | st.dictionaries(_METIN, alt, max_size=4),
    max_leaves=10,
)
# Belge varlıkları SÖZLÜKTÜR (yukarıdaki gerekçe (1)).
_BELGE = st.dictionaries(_METIN, _JSON_YAPI, max_size=6)

# Satır defterlerinin TİPLİ kolonları: üreteç bilerek hem DOĞRU hem YANLIŞ tipi üretir — tip
# koruma sözleşmesi ("uymayan alan extra_json'a düşer ve okumada extra KAZANIR") ancak yanlış tip
# üretildiğinde ölçülebilir.
_SATIR = st.fixed_dictionaries(
    {},
    optional={
        "id": _JSON_SKALER,
        "plan_id": _JSON_SKALER,
        "ticker": _METIN,
        "ts_close": _JSON_SKALER,
        "entry": _JSON_SKALER,             # REAL kolon — int/str/bool de gelebilir (kasıtlı)
        "exit": _JSON_SKALER,
        "qty": _JSON_SKALER,               # INTEGER kolon
        "score": _JSON_SKALER,
        "exploration": _JSON_SKALER,       # BOOL kolon
        "scaled_out": st.booleans(),
        "r_multiple": st.floats(allow_nan=False, allow_infinity=False, allow_subnormal=False),
        "kaynak": st.sampled_from(sorted(ledgerstamp.GECERLI)),
        "serbest_alan": _JSON_YAPI,        # _COLS'ta OLMAYAN alan — extra_json yolu
    },
)

# `equity_curve.json` zarfı: tek yazarın (run.replay_seed) ürettiği şekil.
_SERI = st.builds(
    lambda ver, pts: {"version": ver, "points": pts},
    st.integers(min_value=1, max_value=50),
    st.lists(st.tuples(st.dates().map(str),
                       st.floats(min_value=-1e9, max_value=1e9, allow_nan=False,
                                 allow_infinity=False, allow_subnormal=False))
             .map(list), max_size=6),
)


def _yaz_oku(ad: str, deger, *, db: bool, satir_defteri: bool):
    with kum_havuzu(db=db):
        assert storage.active(ad) is db, "kum havuzu kapıyı beklenen tarafa açmadı"
        if satir_defteri:
            store.write_jsonl(ad, deger)
            return store.read_jsonl(ad)
        store.write_json(ad, deger)
        return store.read_json(ad, "YOK")


@_DISK
@given(doc=_BELGE)
def test_belge_roundtrip_iki_arka_uctan_da_ayni_belgeyi_dondurur(doc):
    """YASA (H9 paritesi): tekil belge → yaz → oku, DOSYA ve SQLite arka uçlarında AYNI.

    Bu bir DİFERANSİYEL testtir ve tam olarak migrasyonun vaadini ölçer: "bu bir DEPOLAMA
    migrasyonudur, davranış migrasyonu DEĞİL". Tek arka ucu kendi beklentisine karşı sınamak bu
    vaadi ölçemezdi — iki arka uç aynı anda yanlış olsaydı test yine yeşil kalırdı."""
    dosya = _yaz_oku("scoreboard.json", doc, db=False, satir_defteri=False)
    db = _yaz_oku("scoreboard.json", doc, db=True, satir_defteri=False)
    assert digest(dosya) == digest(db)
    assert digest(dosya) == digest(store.sanitize(doc))


@_DISK
@given(rows=st.lists(_SATIR, max_size=6))
# NEGATİF SIFIR REGRESYON KİLİDİ — bu üç örnek RASTGELE seçilmedi, ölçüldü. Hypothesis 2026-07-31'de
# `-0.0`ın SQLite REAL kolonunda işaretini kaybettiğini buldu (bkz. `storage._isaretli_sifir`).
# Kusur LATENT'ti: canlı defterde o gün tek bir örneği yoktu ve elle yazılmış hiçbir test onu
# aramıyordu. `@example` olmadan bu kilit ÜRETECİN ŞANSINA kalırdı — ilk koşumda 50 örnek boyunca
# hiç `-0.0` çizilmemişti, yani suite yeşil kalıp kusuru geri kaçırabilirdi.
@example(rows=[{"entry": -0.0}])
@example(rows=[{"r_multiple": -0.0}])
@example(rows=[{"exit": -0.0, "qty": -0.0}])
def test_satir_defteri_roundtrip_paritesi_ve_tip_korumasi(rows):
    """YASA: satır defteri → yaz → oku, iki arka uçta AYNI **ve tipler korunur**.

    Tip koruması ayrıca sınanır: SQLite'ın tip afinitesi `60`ı `60.0`a çevirebilir ve bu SESSİZ
    bir veri değişikliği olurdu. `digest` int/float/bool ayrımını gösterdiği için (`1`/`1.0`/`true`
    farklı metinlerdir) parite eşitliği aynı zamanda tip eşitliğidir."""
    dosya = _yaz_oku("trades.jsonl", rows, db=False, satir_defteri=True)
    db = _yaz_oku("trades.jsonl", rows, db=True, satir_defteri=True)
    assert digest(dosya) == digest(db)
    assert digest(dosya) == digest([store.sanitize(r) for r in rows])


@_DISK
@given(seri=_SERI)
# Aynı regresyon kilidi, ikinci yazım yolu için (`do_write_series` kanonik-nokta dalı). Bu, testin
# ORİJİNAL olarak düştüğü küçültülmüş karşı-örneğin ta kendisidir.
@example(seri={"version": 1, "points": [["2000-01-01", -0.0]]})
def test_seri_zarfi_roundtrip_paritesi(seri):
    """YASA: `equity_curve.json` zarfı (version + points) iki arka uçta AYNI döner.

    Seri, üç varlık türünün en kırılganıdır: zarf `entity_meta.env_json`da, noktalar tipli
    kolonlarda, kanonik olmayan noktalar `extra_json`da yaşar — yani tek bir belge ÜÇ yere
    dağılır ve geri birleştirilir."""
    dosya = _yaz_oku("equity_curve.json", seri, db=False, satir_defteri=False)
    db = _yaz_oku("equity_curve.json", seri, db=True, satir_defteri=False)
    assert digest(dosya) == digest(db)


@_DISK
@given(doc=_BELGE, rows=st.lists(_SATIR, max_size=5), db=st.booleans())
def test_iki_kez_yazim_idempotenttir(doc, rows, db):
    """YASA: aynı belgeyi İKİ kez yazmak, bir kez yazmakla aynı sonucu verir.

    Neden ayrı bir yasa: `write_jsonl` satır defterini EZER (`DELETE` + `executemany`), `write_doc`
    ise `ON CONFLICT DO UPDATE` yapar. İkisi de "ikinci yazım birikim YAPMAZ" sözü verir; bu söz
    tutulmazsa bir yeniden-koşum defteri sessizce iki katına çıkarırdı (bu depoda `merge_dated_
    jsonl`in var olma sebebi tam olarak bu sınıftır)."""
    with kum_havuzu(db=db):
        store.write_json("portfolio.json", doc)
        bir = store.read_json("portfolio.json", "YOK")
        store.write_json("portfolio.json", doc)
        assert digest(store.read_json("portfolio.json", "YOK")) == digest(bir)

        store.write_jsonl("trade_plans.jsonl", rows)
        bir_r = store.read_jsonl("trade_plans.jsonl")
        store.write_jsonl("trade_plans.jsonl", rows)
        assert digest(store.read_jsonl("trade_plans.jsonl")) == digest(bir_r)


@_DISK
@given(rows=st.lists(_SATIR, min_size=1, max_size=6), db=st.booleans())
def test_append_sirasi_korunur_ve_limit_kuyruktan_okur(rows, db):
    """YASA: `append_jsonl` ile eklenen satırlar SIRAYLA okunur ve `limit=n` SON n satırı verir.

    Sıra, bu depoda bir muhasebe alanıdır: `ledgerstamp.seed_boundary` defterin yazım SIRASINDAN
    tohum sınırını ölçer, `_persist_trade` son 30 satıra bakarak tekrarı bastırır. Sıra bozulursa
    ikisi de sessizce yanlış cevap verir."""
    with kum_havuzu(db=db):
        for r in rows:
            store.append_jsonl("trades.jsonl", r)
        hepsi = store.read_jsonl("trades.jsonl")
        assert digest(hepsi) == digest([store.sanitize(r) for r in rows])
        n = max(1, len(rows) // 2)
        assert digest(store.read_jsonl("trades.jsonl", limit=n)) == digest(hepsi[-n:])


@_DISK
@given(doc=_BELGE)
def test_damga_yalniz_icerik_degisince_degisir(doc):
    """YASA: `store.stamp(ad)` bir ÖNBELLEK ANAHTARIDIR — yazım oldu mu diye sorar.

    İki taraflı sözleşme: (a) yazımdan SONRA damga değişmiş olmalı (değişmezse `analytics._nd_stamp`
    ve `shadow_model.dataset_fingerprint` sonsuza kadar bayat önbellek servis eder), (b) yazım
    YOKKEN damga sabit kalmalı (değişirse her okuma önbelleği boşa düşürür). Dosya çağında bunu
    mtime yapıyordu; DB çağında `entity_meta.rev`. İkisi de AYNI sözü vermek zorunda."""
    for db in (False, True):
        with kum_havuzu(db=db):
            once = store.stamp("scoreboard.json")
            store.write_json("scoreboard.json", doc)
            sonra = store.stamp("scoreboard.json")
            assert sonra != once, f"yazımdan sonra damga değişmedi (db={db})"
            assert store.stamp("scoreboard.json") == sonra, f"yazım yokken damga oynadı (db={db})"


# =================================================================================================
# C) store.update_json KAYIPSIZLIĞI — ÇOK İŞ PARÇACIKLI DURUM MAKİNESİ
# =================================================================================================
class SayacMakinesi(RuleBasedStateMachine):
    """Çok-adımlı append/update/read dizilerinde SAYAÇ ARTIŞI KAYBOLMAZ.

    NEDEN DURUM MAKİNESİ, TEK BİR TEST DEĞİL: kayıp-güncelleme (`lost update`) tek bir çağrıda
    görünmez — iki yazarın ARASINDAKİ sırada doğar. Hypothesis burada girdiyi değil KOMUT DİZİSİNİ
    üretir ve karşı-örnek bulursa onu en kısa diziye küçültür ("2 adım: artır, artır" gibi).

    NEDEN İŞ PARÇACIĞI: `store.file_lock` iki katmanlıdır — süreç-İÇİ `RLock` ve süreçler-ARASI
    `flock`. Süreçler-arası katmanın kendi testi zaten var (`flock`, ayrı süreçle). Burada
    ölçülmeyen taraf ölçülür: AYNI süreçte eşzamanlı oku-değiştir-yaz. Canlıda bu yol gerçektir
    (zamanlayıcı ipliği + hermes ipliği + pano isteği aynı defteri yazar).

    NEDEN SAYAÇ: kayıp bir güncelleme "yanlış değer" değil, "EKSİK değer" üretir. Toplam artış
    beklenenden küçükse tam olarak o kadar yazım kaybolmuştur — hata mesajı kaybın BÜYÜKLÜĞÜNÜ
    söyler, sadece varlığını değil."""

    def __init__(self):
        super().__init__()
        self._havuz = kum_havuzu(db=False)
        self._havuz.__enter__()
        self.beklenen = 0
        self.satir = 0

    @initialize(db_acik=st.booleans())
    def arka_ucu_sec(self, db_acik):
        """Aynı yasa İKİ arka uçta da geçerli olmalı. Şema burada kurulur (kum havuzu açıldıktan
        sonra), çünkü `storage.active()` DB DOSYASININ varlığını çağrı anında ölçer."""
        if db_acik:
            storage.ensure_schema()

    @rule(n=st.integers(min_value=1, max_value=4))
    def es_zamanli_artir(self, n):
        """n iş parçacığı AYNI ANDA sayacı birer artırır. Kilit çalışıyorsa toplam tam n artar."""
        hatalar: list = []

        def _bir():
            try:
                store.update_json("scoreboard.json",
                                  lambda d: (d.__setitem__("sayac", int(d.get("sayac", 0)) + 1), True)[1],
                                  default={})
            except BaseException as e:            # iplik istisnası SESSİZ ÖLÜR — toplanmazsa
                hatalar.append(f"{type(e).__name__}: {e}")   # test yeşil kalır ve kayıp görünmez

        ip = [threading.Thread(target=_bir, name=f"hyp-artir-{i}") for i in range(n)]
        for t in ip:
            t.start()
        for t in ip:
            t.join(timeout=30)
        assert not hatalar, f"eşzamanlı güncelleyicide istisna: {hatalar}"
        assert not [t for t in ip if t.is_alive()], "güncelleyici iplik 30 sn'de bitmedi (kilit kilitlendi?)"
        self.beklenen += n

    @rule(row=_SATIR)
    def satir_ekle(self, row):
        store.append_jsonl("trades.jsonl", row)
        self.satir += 1

    @rule()
    def defteri_yeniden_yaz(self):
        """`update_jsonl` yolu: kilitli oku-değiştir-yaz. Satır SAYISI değişmemeli."""
        store.update_jsonl("trades.jsonl", lambda rows: [r.setdefault("dokunuldu", True) for r in rows] and True)

    @invariant()
    def sayac_kayipsiz(self):
        doc = store.read_json("scoreboard.json", {})
        assert int(doc.get("sayac", 0)) == self.beklenen, \
            (f"KAYIP GÜNCELLEME: sayaç {doc.get('sayac')} ama {self.beklenen} artış istendi "
             f"(fark {self.beklenen - int(doc.get('sayac', 0))} yazım kayboldu)")

    @invariant()
    def satir_kayipsiz(self):
        assert len(store.read_jsonl("trades.jsonl")) == self.satir

    def teardown(self):
        self._havuz.__exit__(None, None, None)


TestSayacMakinesi = SayacMakinesi.TestCase
TestSayacMakinesi.settings = settings(deadline=None, max_examples=25, stateful_step_count=10,
                                      suppress_health_check=[HealthCheck.too_slow])


# =================================================================================================
# D) TAKVİM KAPISI + KARANTİNA
# =================================================================================================
# BRİEF DÜZELTMESİ (kayda geçer): brief her iki iddiayı da `measurement_bars` çıktısına bağlıyordu.
# Kodda bunlar İKİ AYRI kapıdır ve tek fonksiyonda ölçülemezler:
#   * SEANS-DIŞI satır → `adapters.data.sanitize_bars` (takvim kapısı, XNYS seans kümesi).
#   * GÜVENSİZ DÖNEM  → `adapters.data.measurement_bars` (bütünlük defteri, `guvenli_baslangic`).
# İkisi de aşağıda kendi gerçek kapısında sınanır. Tek fonksiyona bağlamak, ölçülmeyen bir kapıyı
# ölçülmüş gibi göstermek olurdu.


def _gercek_seanslar(n: int = 400) -> list[str]:
    ses = data_adapter._sessions()
    if not ses:
        pytest.skip("XNYS takvimi bu makinede üretilemedi (pandas_market_calendars yok/patladı) — "
                    "takvim kapısı FAIL-OPEN'dır, yani ölçüm YAPILAMADI; yeşil göstermek yalan olurdu")
    lo, hi = data_adapter._SESSION_SPAN
    uygun = sorted(d for d in ses if "2015-01-01" <= d <= "2024-12-31")
    return uygun[:n]


def _cerceve(tarihler: list[str]) -> pd.DataFrame:
    """Kapıların REDDETMEYECEĞİ sağlıklı bir OHLCV çerçevesi (tek değişken: tarih kümesi)."""
    n = len(tarihler)
    kapanis = [100.0 + 0.05 * i for i in range(n)]
    return pd.DataFrame({
        "date": tarihler,
        "open": [c * 0.999 for c in kapanis],
        "high": [c * 1.004 for c in kapanis],
        "low": [c * 0.996 for c in kapanis],
        "close": kapanis,
        "volume": [2_000_000.0] * n,
    })


@contextlib.contextmanager
def _bar_sayaclari_korunur():
    """`adapters.data`nın süreç-içi hayalet/karantina sayaçları ÜRETİM globalidir. Test onları
    kirletirse sonraki test kendi kurmadığı bir sayımı görür (conftest'teki SECTORS dersinin
    aynısı — bu depoda iki kez yaşandı). Kaydet, temizle, geri koy."""
    adlar = ("_GHOST", "_GHOST_EVENTED", "_QUAR_EVENTED", "_CAL_MISMATCH",
             "_CAL_MISMATCH_WARNED", "_INTEGRITY_APPLIED", "_INTEGRITY_WARNED")
    yedek = {a: type(getattr(data_adapter, a))(getattr(data_adapter, a)) for a in adlar}
    for a in adlar:
        getattr(data_adapter, a).clear()
    try:
        yield
    finally:
        for a in adlar:
            g = getattr(data_adapter, a)
            g.clear()
            g.update(yedek[a]) if isinstance(g, dict) else g.update(yedek[a])


@_AGIR
@given(veri=st.data())
def test_seans_disi_satir_sanitize_bars_ciktisinda_asla_gorunmez(veri):
    """YASA: takvim kapısından geçen çerçevede seans-dışı tarih KALMAZ.

    TEK İSTİSNA VE O DA YASANIN PARÇASI: kapı bir serinin %1'inden fazlasını (ve ≥2 satırı)
    düşürecekse REDDEDER — çünkü bu artık onarım değil, serinin takvimini reddetmektir (geri
    alınamaz kayıp). Property bu dallanmayı ölçer: reddedilmediyse SIFIR hayalet kalmalı,
    reddedildiyse HİÇBİR hayalet satır düşmemiş olmalı. "Bazen düşürür bazen düşürmez" hâli
    kabul edilmez — kapının kararı ölçülebilir olmalıdır."""
    seanslar = _gercek_seanslar()
    n_temiz = veri.draw(st.integers(min_value=20, max_value=len(seanslar)), label="temiz_satir")
    hayalet = veri.draw(
        st.lists(st.sampled_from(["2020-01-04", "2020-01-05", "2021-07-04", "2022-12-25",
                                  "2023-01-01", "2023-11-23", "2024-05-25", "2024-07-04"]),
                 min_size=1, max_size=6, unique=True), label="hayalet_tarih")
    tarihler = sorted(set(seanslar[:n_temiz]) | set(hayalet))
    df = _cerceve(tarihler)
    ses = data_adapter._sessions()
    with kum_havuzu(), _bar_sayaclari_korunur():
        red = data_adapter.calendar_mismatch(df)
        out, rep = data_adapter.sanitize_bars(df, "HYPTEST")
        kalan = [d for d in out["date"].astype(str).str.slice(0, 10) if d not in ses]
        if red is None:
            assert kalan == [], f"seans-dışı satır kapıdan GEÇTİ: {kalan[:5]}"
            assert rep.get("ghost_session_dropped") == len(hayalet)
        else:
            assert "ghost_session_dropped" not in rep, \
                "kitlesel uyuşmazlık REDDEDİLMELİYDİ ama satır düşürüldü (geri alınamaz kayıp)"
            assert rep.get("calendar_mismatch_rows") == red["non_session_rows"]


@_AGIR
@given(veri=st.data())
def test_guvensiz_donem_measurement_bars_ciktisinda_asla_gorunmez(veri):
    """YASA: bütünlük defteri bir sembole `guvenli_baslangic` verdiyse, ÖLÇÜM çerçevesinde o
    tarihten ÖNCEKİ hiçbir satır bulunmaz — ve o tarihten SONRAKİ hiçbir satır kaybolmaz.

    İki yönlü olması şart: yalnız "öncesi yok" denseydi, her şeyi düşüren bir kapı da testi
    geçerdi (ve ölçüm evrenini sessizce boşaltırdı)."""
    seanslar = _gercek_seanslar(200)
    n = veri.draw(st.integers(min_value=10, max_value=len(seanslar)), label="satir")
    tarihler = seanslar[:n]
    kesim = veri.draw(st.integers(min_value=0, max_value=n - 1), label="kesim")
    guvenli = tarihler[kesim]
    df = _cerceve(tarihler)
    with kum_havuzu(), _bar_sayaclari_korunur():
        store.write_json("bars_integrity.json",
                         {"semboller": {"HYPTEST": {"guvenli_baslangic": guvenli}}})
        out = data_adapter.measurement_bars(df, "HYPTEST")
        gorulen = list(out["date"].astype(str).str.slice(0, 10))
        assert all(d >= guvenli for d in gorulen), \
            f"güvensiz dönem ölçüme SIZDI: {[d for d in gorulen if d < guvenli][:5]}"
        assert gorulen == [d for d in tarihler if d >= guvenli], \
            "kapı güvenli dönemden de satır düşürdü — ölçüm evreni sessizce daraldı"


@_AGIR
@given(veri=st.data())
def test_defteri_olmayan_sembol_icin_hicbir_satir_dusmez(veri):
    """YASA (fail-open'ın sesi): bütünlük defteri YOKSA ölçüm çerçevesi BİREBİR girdiye eşittir.
    Bir defterin yokluğu, tüm ölçüm evrenini susturmak için gerekçe değildir."""
    seanslar = _gercek_seanslar(120)
    n = veri.draw(st.integers(min_value=5, max_value=len(seanslar)), label="satir")
    df = _cerceve(seanslar[:n])
    with kum_havuzu(), _bar_sayaclari_korunur():
        out = data_adapter.measurement_bars(df, "DEFTERSIZ")
        assert list(out["date"]) == list(df["date"])


# =================================================================================================
# E) DEFTER KAYNAK DAMGASI
# =================================================================================================
_ISLEM = st.fixed_dictionaries({
    "ticker": st.text(alphabet="ABCDEFGH", min_size=1, max_size=4),
    "ts_close": st.dates().map(str),
    "exit_reason": st.sampled_from(["stop", "target", "time_stop", "trail"]),
    "exit": st.floats(min_value=0.01, max_value=1e5, allow_nan=False, allow_infinity=False,
                      allow_subnormal=False),
    "r_multiple": st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False,
                            allow_subnormal=False),
}, optional={"plan_id": st.text(alphabet="0123456789", min_size=1, max_size=6)})


@_DISK
@given(islemler=st.lists(_ISLEM, min_size=1, max_size=6), db=st.booleans())
def test_ileri_yoldan_gecen_her_islem_live_paper_damgasi_tasir(islemler, db):
    """YASA: `loop._persist_trade` defterin İLERİ yoludur — oradan geçen her satır canlı kâğıt
    döngünün GERÇEKTEN kapattığı bir işlemdir ve `live_paper` damgası taşır.

    Damga satır DİSKE DÜŞMEDEN basılır. Sonradan damgalamak damgasız bir aralık doğurur ve
    denetim bulgusu BT-1 tam olarak o aralıktı: 95 satırın tamamı "canlı defter" sanılıyordu."""
    from meridian import loop
    with kum_havuzu(db=db):
        for t in islemler:
            loop._persist_trade(dict(t))
        rows = store.read_jsonl("trades.jsonl")
        assert rows, "ileri yol hiçbir satır yazmadı"
        for r in rows:
            assert r.get(ledgerstamp.FIELD) == ledgerstamp.LIVE_PAPER, \
                f"damgasız/yanlış damgalı satır: {r.get(ledgerstamp.FIELD)!r}"


@_SAF
@given(satir=_ISLEM, ilk=st.sampled_from(sorted(ledgerstamp.GECERLI)),
       ikinci=st.sampled_from(sorted(ledgerstamp.GECERLI)))
def test_damga_bir_kez_basilir_ikinci_yazar_ezemez(satir, ilk, ikinci):
    """YASA: bir satırın kökeni BİR KEZ ölçülür. İkinci bir yazar onu 'düzeltmeye' kalkarsa
    migrasyonun kanıtı sessizce kaybolur — `stamp` var olan GEÇERLİ damgayı EZMEZ."""
    r = ledgerstamp.stamp(dict(satir), ilk)
    assert r[ledgerstamp.FIELD] == ilk
    assert ledgerstamp.stamp(r, ikinci)[ledgerstamp.FIELD] == ilk


@_SAF
@given(satir=_ISLEM, kaynak=_METIN)
def test_gecersiz_damga_sessizce_kabul_edilmez(kaynak, satir):
    """YASA: sözlükte olmayan bir damga adı ValueError'dır. Sessizce kabul edilseydi defterde
    hiçbir okuyucunun tanımadığı bir üçüncü sınıf doğar ve `counts()` onu `belirsiz` sayardı —
    yani bir YAZIM HATASI, ölçülmüş bir belirsizlik gibi görünürdü."""
    if kaynak in ledgerstamp.GECERLI:
        return
    with pytest.raises(ValueError):
        ledgerstamp.stamp(dict(satir), kaynak)


@_SAF
@given(rows=st.lists(st.fixed_dictionaries({}, optional={
    ledgerstamp.FIELD: st.one_of(st.none(), _METIN, st.sampled_from(sorted(ledgerstamp.GECERLI))),
    "ticker": _METIN}), max_size=12))
def test_counts_muhasebesi_tamdir(rows):
    """YASA: `counts()` bir MUHASEBEDİR — üç kova toplamı defterin tamamına eşittir ve damgasız
    satırlar `belirsiz`in İÇİNDEDİR (alt kırılım olarak ayrıca sayılır).

    Toplam tutmazsa pano bir satırı ya iki kez ya hiç saymaz; ikisi de "gerçek canlı n" sayısını
    — sistemin kendisi hakkındaki en temel sayı — sessizce bozar."""
    c = ledgerstamp.counts(rows)
    assert c["live_paper_n"] + c["replay_seed_n"] + c["belirsiz_n"] == len(rows) == c["toplam"]
    assert c["damgasiz_n"] <= c["belirsiz_n"]
    assert c["training_n"] == c["replay_seed_n"]


@_DISK
@given(tohum=st.lists(_ISLEM, max_size=4), canli=st.lists(_ISLEM, max_size=4), db=st.booleans())
def test_iki_yazarin_defteri_damgaya_gore_tam_ayrisir(tohum, canli, db):
    """YASA: tohum yolu (`ledgerstamp.stamp_rows` → `write_jsonl`) ve ileri yol (`_persist_trade`)
    aynı deftere yazar; `split()` onları KAYIPSIZ ayırır. Bu ayrım olmadan `learning_scorecard`
    survivorship taşıyan simülasyon satırlarını canlı kanıt sayardı."""
    from meridian import loop
    with kum_havuzu(db=db):
        store.write_jsonl("trades.jsonl",
                          ledgerstamp.stamp_rows([dict(t) for t in tohum], ledgerstamp.REPLAY_SEED))
        for t in canli:
            loop._persist_trade(dict(t))
        rows = store.read_jsonl("trades.jsonl")
        parca = ledgerstamp.split(rows)
        assert sum(len(v) for v in parca.values()) == len(rows)
        assert all(r[ledgerstamp.FIELD] == ledgerstamp.REPLAY_SEED
                   for r in parca[ledgerstamp.REPLAY_SEED])
        assert all(r[ledgerstamp.FIELD] == ledgerstamp.LIVE_PAPER
                   for r in parca[ledgerstamp.LIVE_PAPER])
