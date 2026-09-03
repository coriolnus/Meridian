"""test_wp2d_pano_beyani_v246.py — WP2-D BACAK-3 (pano reset/pencere beyanı) + ROADMAP Ö-30.

=================================================================================================
KALEM 1 — WP2-D BACAK-3: PANO HANGİ PENCEREYİ GÖSTERDİĞİNİ SÖYLER
=================================================================================================
ÖLÇÜLEN ARIZA (canlı, 2026-08-14 · EDG-2026-036 · ROADMAP WP2-D):

  `equity_curve.json` **882 nokta** taşıyor ve sonuncusu **2026-07-20** — eğri 24 gündür donuktu.
  Pano bunu HİÇBİR YERDE söylemiyordu: grafiğe bakan operatör "P&L yansıtmıyor" diye okudu.
  Aynı zarfta **1 reset işareti** var (`SR-20260801T151429+0000`, `egri_son_nokta
  ["2026-07-20", 94457.91]`) — yani tek çizgi bir sermaye tabanı değişiminin ÖNCESİNİ ve
  SONRASINI birlikte kapsıyor. Ve 24 günlük boşluk **KAPANMAYACAK** (geriye doldurmak uydurma
  olurdu), yani seri yeni noktalarla sürerken ortada KALICI bir delik olacak.

  v245-D iki bacağı bitirdi (`ledgerstamp.seed_boundary` artık eğrinin son noktasından okumuyor;
  `loop.daily_cycle` seans sonunda günde tek nokta yazıyor) ve üçüncüsü için İKİ YÜZEY BIRAKTI:
  zarfın `reset_isaretleri` anahtarı + `daily_cycle` makbuzunun `durum` alanı. İkisi de teldeydi,
  ikisinin de PANODA OKUYUCUSU YOKTU (`/api/performance` zarfı olduğu gibi servis ediyordu ama
  `app.js` yalnız `points`e bakıyordu; makbuz ise `_son_dongu()`nun beyaz listesine hiç girmemişti).

BU TURUN ÇÖZÜMÜ: hesap SUNUCUDA (`api._egri_beyani`), pano yalnız ÇİZER. Pano ikinci bir
"kaç gün geride" yasası kursaydı ilk düzenlemede uçtan sessizce ayrışırdı (`sermaye.koken`
docstring'indeki "iki hesap" kusuru).

=================================================================================================
KALEM 2 — `config.default_strategy()` YEDEĞİ CANLIYLA AYRIŞIKTI (ROADMAP Ö-30)
=================================================================================================
`state/goal.yaml:123-125` kendi metninde BEYAN EDİYOR: *"BERABERİNDE GİDEN AYAR: `position_size_r`
1,0 → 0,5 … İkisi AYRILMAZ."* Ama çiftin yarısı git-izli `goal.yaml`da (`max_open_positions: 20`),
öteki yarısı izlenmeyen `state/strategy.yaml`da — ve o dosya yok/boş/bozuk olduğu an
`config.load_strategy()` sessizce `default_strategy()`e düşüyor, orada `position_size_r: 1.0`
yürürlüğe giriyordu. Beyan edilmiş bir invaryant TEK DOSYA ARIZASIYLA kırılıyordu.

Seviye dürüstçe: toplam-risk patlaması DEĞİL (`heat_hard_r` 5,0R yine bağlar) — değişen portföyün
ŞEKLİ: aynı ısıda yarı sayıda, iki kat büyük pozisyon. Ölçülmemiş bir bileşim.

HİÇBİR TEST CANLI STATE'E YAZMAZ: durum yazan her test `sandbox_state` üzerinden koşar.
"""
from __future__ import annotations

import json
import pathlib
import re

import pytest
import yaml

from fastapi.testclient import TestClient

from meridian import api, config, sermaye, store

SRC = pathlib.Path(__file__).resolve().parent.parent
APPJS = (SRC / "meridian" / "web" / "app.js").read_text()
# YORUM SATIRLARI SAYILMAZ (repo deseni: test_pano_durum_kartlari_v191): bu turun her bloğu
# kaldırdığı/ eklediği şeyi gerekçesiyle yazıyor; gerekçe kaynakta durmalı ama BİLDİRİM sanılmamalı.
APPJS_KOD = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))


# =================================================================================================
# YARDIMCILAR
# =================================================================================================
def _isaret(egri_son="2026-07-20", id_="SR-20260801T151429+0000"):
    """`sermaye.uygula`nın zarfa bastığı işaretin şekli (sermaye.py::uygula)."""
    return {"id": id_, "tarih": "2026-08-01T15:14:29+00:00", "tip": "paper_equity_reset",
            "onceki_deger": 94457.91, "yeni_deger": 100000.0,
            "egri_son_nokta": [egri_son, 94457.91], "gerekce": "fikstür"}


def _zarf(points, isaretler=None):
    eq = {"version": 4, "points": list(points)}
    if isaretler is not None:
        eq[sermaye.CURVE_MARK_KEY] = list(isaretler)
    return eq


def _daily_cycle_yaz(state, makbuz, date="2026-08-14"):
    """Olay defterine BİR `daily_cycle` satırı — `_son_dongu()` tam olarak bunu okuyor."""
    (state / "events.jsonl").write_text(json.dumps({
        "ts": "2026-08-14T21:05:00+00:00", "level": "info", "event": "daily_cycle",
        "date": date, "regime": "chop", "candidates": 3, "plans": 1, "armed": 0,
        "open_positions": 0, "equity": 100000.0, "halted": False, "data_ok": True,
        "egri_nokta": makbuz}) + "\n")
    api._SON_DONGU_ONBELLEK.update(anahtar=None, yuk=None)     # damga değişti; önbellek elle boşaltılır


# =================================================================================================
# §1 — PENCERE: KAÇ NOKTA, HANGİ İKİ TARİH ARASI
# =================================================================================================
def test_beyan_PENCEREYI_olcer():
    b = api._egri_beyani(_zarf([["2023-01-12", 100000.0], ["2026-07-20", 94457.91]]), {})
    assert b["n_nokta"] == 2
    assert b["ilk"] == ["2023-01-12", 100000.0]
    assert b["son"] == ["2026-07-20", 94457.91]
    assert b["okunamayan_nokta"] == 0


def test_beyan_BOS_egride_SIFIR_cizmez():
    """Nokta yoksa `ilk`/`son` None'dur — [tarih, 0.0] uydurmak, tam da bu turun kapattığı hâl."""
    b = api._egri_beyani({"points": []}, {})
    assert b["n_nokta"] == 0 and b["ilk"] is None and b["son"] is None


@pytest.mark.parametrize("bozuk", [["2026-07-20"], "iki-eleman-degil", ["gecersiz-tarih", 1.0],
                                   ["2026-07-20", "sayi-degil"], None])
def test_beyan_OKUNAMAYAN_noktayi_SAYAR_seriye_KATMAZ(bozuk):
    b = api._egri_beyani(_zarf([["2026-07-17", 100.0], bozuk, ["2026-07-20", 110.0]]), {})
    assert b["okunamayan_nokta"] == 1
    assert b["n_nokta"] == 3                      # ham sayım DÜŞMEZ: zarf gerçekten 3 satır taşıyor
    assert b["ilk"] == ["2026-07-17", 100.0] and b["son"] == ["2026-07-20", 110.0]


# =================================================================================================
# §2 — DONUKLUK: EĞRİNİN DIŞINDAN ÖLÇÜLÜR (kitabın işlediği son seans)
# =================================================================================================
def test_beyan_GECIKMEYI_kitabin_son_seansindan_olcer():
    """CANLI VAKANIN KENDİSİ: eğri 2026-07-20'de duruyor, kitap 2026-08-13'ü işledi → 24 gün."""
    b = api._egri_beyani(_zarf([["2023-01-12", 100000.0], ["2026-07-20", 94457.91]]),
                         {"last_date": "2026-08-13"})
    assert b["gecikme_gun"] == 24
    assert b["son_seans"] == "2026-08-13"


def test_beyan_gecikme_SIFIR_ile_OLCULEMEDI_ayri_haller():
    guncel = api._egri_beyani(_zarf([["2026-08-13", 1.0], ["2026-08-14", 2.0]]),
                              {"last_date": "2026-08-14"})
    assert guncel["gecikme_gun"] == 0                       # "0 gün geride" = güncel
    for pf in ({}, {"last_date": None}, {"last_date": "bozuk"}, None):
        yok = api._egri_beyani(_zarf([["2026-08-14", 2.0]]), pf)
        assert yok["gecikme_gun"] is None, pf               # ölçülemedi ≠ 0


# =================================================================================================
# §3 — DELİKLER: TAKVİM GÜNÜYLE ÖLÇÜLÜR, EŞİK BEYAN EDİLİR
# =================================================================================================
def test_beyan_HAFTA_SONUNU_delik_saymaz_24_GUNU_sayar():
    """Cuma→Pazartesi 3 gün, hafta sonu + tek tatil Cuma→Salı 4 gün: ikisi de DOĞAL. Eşik 5'tir ve
    dışarı BEYAN edilir — okuyucu neyin sayıldığını bilmeden "delik yok" cümlesine güvenemez."""
    b = api._egri_beyani(_zarf([
        ["2026-07-17", 100.0],      # Cuma
        ["2026-07-20", 101.0],      # Pazartesi  → 3 gün, DOĞAL
        ["2026-07-24", 102.0],      # → 4 gün, DOĞAL (hafta sonu + tatil)
        ["2026-08-17", 103.0],      # → 24 gün, DELİK
    ]), {})
    assert b["bosluk_esigi_gun"] == 5
    assert b["n_bosluk"] == 1
    assert b["bosluklar"] == [{"onceki": "2026-07-24", "sonraki": "2026-08-17", "gun": 24, "i": 2}]
    assert b["en_buyuk_bosluk"]["gun"] == 24
    assert b["bosluk_kirpildi"] is False


def test_beyan_delik_INDISI_grafik_icin_HAM_dizin():
    """`i` panonun işaret koyduğu yerdir ve HAM `points` dizinidir — çözülemeyen bir nokta araya
    girse bile kayma OLMAZ (pano `sx(i)`yi ham diziden hesaplıyor)."""
    b = api._egri_beyani(_zarf([["2026-07-17", 100.0], ["bozuk", 0.0],
                                ["2026-07-20", 101.0], ["2026-08-17", 102.0]]), {})
    assert [g["i"] for g in b["bosluklar"]] == [2]


def test_beyan_delik_TAVANI_asilirsa_BEYAN_edilir():
    """Sessizce kısaltılmış bir liste "başka delik yok" diye okunurdu."""
    import datetime as _dt
    t0 = _dt.date(2020, 1, 6)
    pts = [[(t0 + _dt.timedelta(days=30 * k)).isoformat(), 100.0]
           for k in range(api._EGRI_BOSLUK_TAVAN + 3)]    # her adım 30 gün → her adım bir delik
    b = api._egri_beyani(_zarf(pts), {})
    assert b["n_bosluk"] > api._EGRI_BOSLUK_TAVAN
    assert b["bosluk_kirpildi"] is True
    assert len(b["bosluklar"]) == api._EGRI_BOSLUK_TAVAN == b["bosluk_tavani"]
    # KIRPMA EN YENİLERİ TUTAR: operatörün baktığı uç serinin sonudur.
    assert b["bosluklar"][-1]["sonraki"] == pts[-1][0]


# =================================================================================================
# §4 — KIRILMA: RESET İŞARETİ GÖRÜNÜR VE SERİDE KONUMLANIR
# =================================================================================================
def test_beyan_RESET_ISARETINI_tasir_ve_KONUMLANDIRIR():
    b = api._egri_beyani(_zarf([["2023-01-12", 100000.0], ["2026-07-20", 94457.91]],
                               [_isaret("2026-07-20")]), {})
    assert b["n_isaret"] == 1
    m = b["reset_isaretleri"][0]
    assert m["id"] == "SR-20260801T151429+0000"
    assert m["egri_son_nokta"] == ["2026-07-20", 94457.91]
    assert (m["onceki_deger"], m["yeni_deger"]) == (94457.91, 100000.0)
    assert m["i"] == 1 and m["konum_neden"] is None


def test_beyan_KONUMU_bulunamayan_isaret_GIZLENMEZ():
    """Yeri bulunamayan bir kırılmayı listeden düşürmek, beyanın kendisini yutmak olurdu."""
    b = api._egri_beyani(_zarf([["2023-01-12", 100000.0]], [_isaret("2099-01-01")]), {})
    assert b["n_isaret"] == 1
    m = b["reset_isaretleri"][0]
    assert m["i"] is None and m["konum_neden"] and "konumlandırılamaz" in m["konum_neden"]


def test_beyan_isaret_YOKSA_bos_liste_ve_sifir():
    b = api._egri_beyani(_zarf([["2026-08-14", 1.0]]), {})
    assert b["n_isaret"] == 0 and b["reset_isaretleri"] == []


def test_CIVI_isaret_anahtari_TEK_KAYNAKTAN():
    """`api._egri_beyani` anahtarı `sermaye.CURVE_MARK_KEY`den okur; ikinci bir literal yazsaydı
    ad değiştiği gün pano sessizce boş liste gösterirdi (`test_defter_kaynak_damgasi_v140` o adı
    tek kaynakta çiviliyor)."""
    src = (SRC / "meridian" / "api.py").read_text()
    govde = src[src.index("def _egri_beyani("):src.index("@app.get(\"/api/performance\")")]
    assert "ec.get(_sr.CURVE_MARK_KEY)" in govde
    # Dışarı verilen ALAN ADI bilerek aynıdır (aynı kavram, aynı ad); yasak olan, zarfı OKURKEN
    # ikinci bir literal yazmaktır — ad değiştiği gün pano sessizce boş liste gösterirdi.
    assert 'ec.get("reset_isaretleri")' not in govde


# =================================================================================================
# §5 — MAKBUZ: `daily_cycle`ın `egri_nokta` alanı panoya ULAŞIYOR
# =================================================================================================
def test_son_dongu_EGRI_NOKTA_makbuzunu_TASIR(sandbox_state):
    _daily_cycle_yaz(sandbox_state, {"yazildi": True, "durum": "yazildi", "tarih": "2026-08-14",
                                     "deger": 100000.0, "ofset": 5542.09, "neden": None})
    sd = api._son_dongu()
    assert sd["var"] is True
    assert sd["egri_nokta"]["durum"] == "yazildi"
    assert sd["egri_nokta"]["ofset"] == 5542.09


def test_son_dongu_MAKBUZSUZ_satirda_None_yazildi_DEMEZ(sandbox_state):
    """Eski kayıtlar bu alanı taşımıyor. None = "ölçemedik"; False/"yazilmadi" uydurma olurdu."""
    (sandbox_state / "events.jsonl").write_text(json.dumps({
        "ts": "2026-08-14T21:05:00+00:00", "event": "daily_cycle", "date": "2026-08-14"}) + "\n")
    api._SON_DONGU_ONBELLEK.update(anahtar=None, yuk=None)
    assert api._son_dongu()["egri_nokta"] is None


# =================================================================================================
# §5b — HUNİNİN AĞZI: `daily_cycle`ın `taranan` alanı panoya ULAŞIYOR (2026-08-31)
# -------------------------------------------------------------------------------------------------
# Aynı sınıfın ikinci vakası ve aynı yerde: `_son_dongu()` bir BEYAZ LİSTEdir, motorun yazdığı yeni
# alan oraya girmedikçe telde kalır. `egri_nokta` bunu bir kez yaşadı (§5); `taranan` ikincisi.
# ÖLÇÜLEN ARIZA: pano eleme-SONRASI `candidates`ı "Taranan aday" diye etiketliyordu ve operatör
# "0 aday"ı "hiç tarama olmadı" diye okudu — oysa döngü koşmuş, 251 sembol taranmıştı.
# =================================================================================================
def _dongu_satiri(state, **ek):
    """`daily_cycle` satırını İSTENEN alanlarla yazar — alanın YOKLUĞU da bir hâldir."""
    (state / "events.jsonl").write_text(json.dumps({
        "ts": "2026-08-14T21:05:00+00:00", "level": "info", "event": "daily_cycle",
        "date": "2026-08-14", "candidates": 0, "plans": 0, "armed": 0, **ek}) + "\n")
    api._SON_DONGU_ONBELLEK.update(anahtar=None, yuk=None)


def test_son_dongu_TARANAN_evrenini_TASIR(sandbox_state):
    """Payda telde kalmıyor: motorun ölçtüğü eleme-öncesi evren panoya ULAŞIYOR."""
    _dongu_satiri(sandbox_state, taranan=251, taranan_neden=None)
    sd = api._son_dongu()
    assert sd["taranan"] == 251 and sd["taranan_neden"] is None
    assert sd["candidates"] == 0, "eleme sonrası sayı kaybolmuş — huninin İKİ basamağı da lazım"


def test_son_dongu_TARANAN_olculemediginde_NEDENI_de_TASIR(sandbox_state):
    """Tarama koşmadıysa sayı None'dur ve NEDEN yanında gelir; pano 0 çizmesin diye."""
    _dongu_satiri(sandbox_state, taranan=None, taranan_neden="HALT çekili — bu turda hiç tarama yapılmadı")
    sd = api._son_dongu()
    assert sd["taranan"] is None
    assert "HALT" in sd["taranan_neden"], "neden düştü — pano 'ölçülemedi'yi 'sıfır' diye çizer"


def test_son_dongu_ESKI_KAYITTA_taranan_SIFIR_DEMEZ(sandbox_state):
    """Bu turdan ESKİ satırlar alanı hiç taşımıyor. İKİ None hâli birbirinden ayrılır:
    alan yok → neden de None ("eski kayıt"); alan var ama ölçülemedi → neden DOLU."""
    _dongu_satiri(sandbox_state)                       # `taranan` anahtarı HİÇ YOK
    sd = api._son_dongu()
    assert sd["taranan"] is None and sd["taranan_neden"] is None, \
        "eski kayıt ile ölçülemeyen tarama aynı hâle indirgendi — pano ikisini ayıramaz"


@pytest.mark.parametrize("durum", ["yazildi", "tazelendi", "idempotent_atlandi", "yazilmadi"])
def test_beyan_SON_YAZIM_makbuzunu_DORT_HALDE_de_tasir(sandbox_state, durum):
    """`loop._persist_equity_point`in DÖRT hâli (`loop._persist_equity_point`) beyana OLDUĞU GİBİ geçer — pano
    `neden` metnine göre dizge eşleştirmek zorunda kalmasın diye o alan zaten makine-okunur."""
    _daily_cycle_yaz(sandbox_state, {"durum": durum, "tarih": "2026-08-14", "neden": "x"})
    b = api._egri_beyani(_zarf([["2026-08-14", 1.0]]), {})
    assert b["son_yazim"]["durum"] == durum
    assert b["son_dongu_tarih"] == "2026-08-14"


def test_beyan_makbuz_OKUNAMAZSA_yazilmadi_DEMEZ(sandbox_state):
    b = api._egri_beyani(_zarf([["2026-08-14", 1.0]]), {})     # olay defteri YOK
    assert b["son_yazim"] is None


# =================================================================================================
# §6 — UÇ: `/api/performance` beyanı GERÇEKTEN servis ediyor
# =================================================================================================
def test_api_performance_BEYANI_servis_eder(sandbox_state):
    store.write_json("equity_curve.json",
                     _zarf([["2023-01-12", 100000.0], ["2026-07-20", 94457.91]], [_isaret()]))
    store.write_json("portfolio.json", {"cash": 100000.0, "last_date": "2026-08-13",
                                        "positions": {}, "armed": []})
    _daily_cycle_yaz(sandbox_state, {"durum": "idempotent_atlandi", "tarih": "2026-08-13"})
    with TestClient(api.app) as c:
        r = c.get("/api/performance")
    assert r.status_code == 200
    b = r.json()["equity_curve_beyani"]
    assert b["gecikme_gun"] == 24 and b["n_isaret"] == 1
    assert b["son_yazim"]["durum"] == "idempotent_atlandi"
    # ZARF DA AYNEN DURUYOR: beyan onun YERİNE geçmez, YANINDA durur.
    assert r.json()["equity_curve"][sermaye.CURVE_MARK_KEY][0]["id"] == "SR-20260801T151429+0000"


# =================================================================================================
# §7 — PANO ÇİVİLERİ (kaynak): alan uçta VAR olmak, panoda OKUNUYOR demek DEĞİLDİR
# =================================================================================================
def test_CIVI_pano_egriyi_BEYANLA_cizer():
    assert "function line(pts, b)" in APPJS_KOD, "line() beyanı almıyor — işaretler çizilemez"
    assert "${line(eq, eqB)}${egriBeyani(eqB)}" in APPJS_KOD, \
        "Birikim sayfası eğriyi beyansız çiziyor"


def test_CIVI_pano_beyani_KENDI_HESAPLAMAZ():
    """Pano `gecikme_gun`u SUNUCUDAN alır. Kendi tarih aritmetiğini kurmak, aynı yasanın ikinci
    uygulaması olurdu (`sermaye.koken` docstring'i: iki hesap → iki gerçek)."""
    govde = APPJS_KOD[APPJS_KOD.index("function egriBeyani(b)"):]
    govde = govde[:govde.index("\n}")]
    assert "b.gecikme_gun" in govde
    assert "Date" not in govde and "getTime" not in govde


def test_CIVI_pano_UC_HALI_ayirir_beyan_yoksa_SUSMAZ():
    govde = APPJS_KOD[APPJS_KOD.index("function egriBeyani(b)"):]
    govde = govde[:govde.index("\n}")]
    assert "if (!b) return" in govde and "ölçülemedi" in govde     # uç vermedi → "beyan yok"
    assert "gecikme ölçülemedi" in govde                           # kıyas yapılamadı ≠ güncel
    assert "gün geride" in govde                                   # donukluk gizlenmiyor


def test_CIVI_pano_MAKBUZUN_DORT_HALINI_de_tanir():
    """`idempotent_atlandi` ("yazmadım çünkü zaten yazılı") ile `yazilmadi` ("yazamadım") AYNI
    tonda gösterilirse operatör her gün bir uyarı görür ve uyarılara bakmayı bırakır."""
    blok = APPJS[APPJS.index("const EGRI_YAZIM_TR"):]
    blok = blok[:blok.index("\n};")]
    for durum in ("yazildi", "tazelendi", "idempotent_atlandi", "yazilmadi"):
        assert re.search(rf"\b{durum}:", blok), f"{durum} hâli panoda tanımsız"
    assert '"warn"' in blok and '"mut"' in blok                    # iki hâl iki ton


def test_CIVI_pano_DELIGI_ve_RESETI_grafikte_isaretler():
    govde = APPJS_KOD[APPJS_KOD.index("function line(pts, b)"):]
    govde = govde[:govde.index("\nfunction egriBeyani")]
    assert "bo.bosluklar" in govde and "bo.reset_isaretleri" in govde
    # KONUMU ÖLÇÜLEMEYEN İŞARET ÇİZİLMEZ (yer uydurulmaz) — ama şerit onu yine listeler.
    assert "m.i != null" in govde and "g.i != null" in govde


def test_CIVI_pano_TEK_NOKTAYLA_cizgi_UYDURMAZ():
    """`sx()` paydası `pts.length - 1`: tek noktayla NaN yol çizilir ve eski kod bunu sessizce
    boş bir SVG olarak basardı — "veri yok" demek yerine bozuk bir grafik."""
    govde = APPJS_KOD[APPJS_KOD.index("function line(pts, b)"):]
    govde = govde[:govde.index("\nfunction egriBeyani")]
    assert "pts.length < 2" in govde


def test_CIVI_bugun_egrisi_TAZELIGINI_soyler():
    """① Bugün'ün eğrisi tazeliğini SÖYLER — 24 gün donuk bir seri canlı bir trend gibi görünüyordu.

    ÇAPA TAŞINDI (KARAR-2026-08-24-B §5.3, BEYANLI): sayfada İKİ eğri vardı — mini "Sermaye eğrisi"
    kartı (`gb-eq`) ve Birikim'in tam eğrisi. Dub dönüşümünde Bugün'ün mini eğrisi ANA alan
    grafiğine BİRLEŞTİ (aynı seri, aynı beyan, iki yerde iki tazelik cümlesi ilk düzenlemede
    ayrışırdı). İDDİA DEĞİŞMEDİ: eğrinin YANINDA penceresini söyleyen bir beyan şeridi durur ve
    ölçülemeyen tazelik "güncel" diye okunmaz. Yeni çapa `pv-egri-beyan`dır.
    """
    govde = APPJS[APPJS.index('j("/api/performance").then(p => {'):]
    govde = govde[:govde.index("// KAPSAMA")]
    assert "p.equity_curve_beyani" in govde
    assert "gün geride" in govde and "tazelik ölçülemedi" in govde
    assert 'id="pv-egri-beyan"' in APPJS, "eğrinin pencere beyanı için kap yok"
    # TEK EĞRİ, TEK BEYAN: ikinci bir mini eğri geri gelirse bu satır kırmızı yanar.
    assert 'id="gb-eq"' not in APPJS, "mini eğri geri gelmiş — aynı seri iki yerde iki tazelik yazar"


def test_CIVI_YASA6_beyanin_HER_ALANININ_panoda_okuyucusu_var(sandbox_state):
    """YASA 6 (okuyucusuz yazım yok) İKİ YÖNDE: ürettiğimiz her alanın panoda bir okuyucusu var.

    `son_yazim` GEÇİŞLİdir (`loop._persist_equity_point` makbuzu olduğu gibi taşınır) — onun iç
    alanlarının sözleşmesi loop tarafındadır ve `_son_dongu()` okuyucusu zaten var; burada yalnız
    panonun GERÇEKTEN okuduğu üç alanı (`durum`/`tarih`/`neden` + `ofset`) ölçüyoruz."""
    _daily_cycle_yaz(sandbox_state, {"durum": "yazildi", "tarih": "2026-08-14", "ofset": 0.0})
    b = api._egri_beyani(_zarf([["2026-07-17", 1.0], ["2026-08-17", 2.0]], [_isaret("2026-07-17")]),
                         {"last_date": "2026-08-18"})
    for alan in b:
        assert f".{alan}" in APPJS_KOD or f"b.{alan}" in APPJS_KOD, \
            f"`{alan}` üretiliyor ama panoda okuyucusu YOK (YASA 6)"
    for alan in b["bosluklar"][0]:
        assert f"g.{alan}" in APPJS_KOD, f"boşluk alanı `{alan}` okunmuyor"
    for alan in b["reset_isaretleri"][0]:
        assert f"m.{alan}" in APPJS_KOD, f"işaret alanı `{alan}` okunmuyor"


# =================================================================================================
# §8 — KALEM 2: YEDEK STRATEJİ CANLIYLA HİZALI (ROADMAP Ö-30)
# =================================================================================================
CANLI_STRATEJI = SRC / "state" / "strategy.yaml"
BEKLENEN_BOYUT = 0.5          # operatör kararı 2026-08-12 §E.1 · EDG-2026-026 C kolu + 032


def test_KALEM2_yedegin_boyutu_CANLI_karariyla_hizali():
    assert config.default_strategy()["params"]["position_size_r"] == BEKLENEN_BOYUT


@pytest.mark.parametrize("hal,icerik", [
    ("yok", None),
    ("bos", ""),
    ("bos_sozluk", "{}\n"),
    ("semasiz", "version: 5\nnote: params ANAHTARI YOK\n"),
    ("bozuk", "params: [bu bir liste degil sozluk\n  : : :\n"),
])
def test_KALEM2_UC_ARIZA_HALINDE_de_yedek_CANLI_boyutu_verir(sandbox_state, hal, icerik):
    """ÇİVİNİN ASIL CÜMLESİ: `strategy.yaml` yok/boş/bozuk olduğunda motorun koştuğu boyut,
    operatörün ölçtüğü boyuttur. Eskiden bu üç hâlin üçü de 1,0R'ye düşüyordu — yani beyan edilmiş
    invaryant (`goal.yaml:123-125`) tek dosya arızasıyla kırılıyordu."""
    if icerik is not None:
        config.strategy_path().write_text(icerik)
    s = config.load_strategy()
    assert s["params"]["position_size_r"] == BEKLENEN_BOYUT, hal


@pytest.mark.parametrize("icerik", ["", "{}\n", "version: 5\n", "params: [liste\n : : :\n"])
def test_KALEM2_dusus_SESSIZ_DEGIL_uyari_hala_basiliyor(sandbox_state, monkeypatch, icerik):
    """Değeri hizalamak, düşüşün DUYURULMASINI zayıflatmamalı: `strategy_file_unusable` uyarısı
    yerinde kalır (YASA 4). Uyarı kaybolursa operatör yedeğe düştüğünü hiç öğrenmez."""
    from meridian import obs
    kayit = []
    monkeypatch.setattr(obs, "warn", lambda ad, **kw: kayit.append((ad, kw)))
    config.strategy_path().write_text(icerik)
    config.load_strategy()
    assert [a for a, _ in kayit] == ["strategy_file_unusable"], icerik


def test_KALEM2_DOSYA_YOK_hali_BUGUN_sessiz_BEYANLI_olgu(sandbox_state, monkeypatch):
    """DÜRÜST BEYAN, ONAY DEĞİL: dosyanın HİÇ olmaması bugün uyarı basmaz (config.py::load_strategy) —
    çünkü bu, `run.bootstrap_v01`in sahibi olduğu TAZE KURULUM yoludur. Olgu burada çivilenir ki
    bir gün değişirse BİLEREK değişsin; Rol-1'e ayrı kalem olarak raporlandı (uyarıyı buraya
    eklemek her çağrıda bir satır üretirdi — `_CALENDAR_WARNED` deseni gerektiren ayrı bir karar)."""
    from meridian import obs
    kayit = []
    monkeypatch.setattr(obs, "warn", lambda ad, **kw: kayit.append(ad))
    assert not config.strategy_path().exists()
    assert config.load_strategy()["params"]["position_size_r"] == BEKLENEN_BOYUT
    assert kayit == []


def test_KALEM2_SURUKLENME_dedektoru_canli_yuzeyle_BIREBIR():
    """Sürüklenme dedektörü: depoda `state/strategy.yaml` varsa yedek onunla BİREBİR olmalı.

    Dosya git-izli DEĞİL (CLAUDE.md §8: yalnız goal.yaml + bounds.yaml izli) — worktree/taze
    klonda YOKTUR. O hâlde test dürüstçe ATLANIR: "kıyas yapılamadı" ile "hizalı" aynı cümle
    değildir ve olmayan bir dosyaya karşı yeşil yanmak, dedektörü sessizce öldürürdü."""
    if not CANLI_STRATEJI.exists():
        pytest.skip("state/strategy.yaml bu checkout'ta yok (git-izsiz) — kıyas YAPILAMADI")
    canli = (yaml.safe_load(CANLI_STRATEJI.read_text()) or {}).get("params") or {}
    if "position_size_r" not in canli:
        pytest.skip("canlı strategy.yaml `position_size_r` taşımıyor — kıyas YAPILAMADI")
    assert float(canli["position_size_r"]) == BEKLENEN_BOYUT, (
        "YEDEK CANLIYLA AYRIŞTI: operatör canlı boyutu değiştirdi ama `config.default_strategy()` "
        "eski değerde kaldı — `goal.yaml:123-125` invaryantı yine tek dosya arızasıyla kırılır")


def test_KALEM2_yedek_BOUNDS_icinde_ve_GOAL_tavaninin_altinda():
    """Yedek yalnız 'canlıyla aynı' olmakla yetinmez: arama uzayında ve operatörün zarfında olmalı.
    (Türetme YAPILMAZ — bkz. `default_strategy()` docstring'i: tavandan türetmek bu kusurun kendisi.)"""
    v = config.default_strategy()["params"]["position_size_r"]
    b = config.bounds()["position_size_r"]
    assert b["min"] <= v <= b["max"]
    assert round((v - b["min"]) / b["step"], 6) == round(round((v - b["min"]) / b["step"]), 6), \
        "yedek adım ızgarasının DIŞINDA — Hermes bu değeri hiç öneremezdi"
    assert v <= float(config.limits()["max_position_r"])


def test_KALEM2_yedegin_UC_DIS_TUKETICISI_ADIYLA_bilinir():
    """Değişikliğin kapsamı beyanlı: yedeği okuyan üç dış yüzey (hepsi bu ajanın dosya sınırının
    DIŞINDA ve Rol-1'e raporlu). Yeni bir tüketici eklenirse bu test onu görünür kılar."""
    tuketici = {}
    for ad in ("run.py", "mutation.py", "sprint.py"):
        src = (SRC / "meridian" / ad).read_text()
        tuketici[ad] = src.count("config.default_strategy()")
    assert tuketici == {"run.py": 1, "mutation.py": 2, "sprint.py": 2}, tuketici
