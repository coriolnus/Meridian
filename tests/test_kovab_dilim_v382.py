"""v382 — KOVA B TEK DİLİM: TSK-101 (alarm imzası) · TSK-102 (süre düşüşü) · TSK-030 adım-3 (çapa göçü).

Bu dosya üç kalemin ORTAK çivi yüzeyidir; her bölüm kendi iddiasını ayrı taşır.

TARAMA NOTU (v382 kimlik beyanı): buradaki iki tarayıcı (`mekanizma=` kw'ı ve `dosya.py:SATIR`
çapası) `meridian/*.py` KAYNAK METNİNİ okur. Kaynak-metin tarayıcısının bilinen kusuru "boşta
temiz" demesidir — hedef desen sıfır olduğunda tarayıcının ÇALIŞTIĞI ile HİÇBİR ŞEY GÖRMEDİĞİ
ayırt edilemez. Bu yüzden her tarayıcının yanında (a) sentetik pozitif kontrol (tarayıcı uydurma
bir kaynağı verildiğinde İHLALİ YAKALAR) ve (b) canlı taban ölçüsü (aranan DOĞRU biçim kaynakta
gerçekten var) durur. İkisi olmadan bu dosya sessizce ölür.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
MERIDIAN = REPO / "meridian"
KAYNAKLAR = sorted(MERIDIAN.glob("*.py"))


def _obs_cagrilari_dugumden(kok: ast.AST):
    """Verilen AST düğümünün ALTINDAKİ `obs.<log|warn|alarm|event>(...)` çağrıları.

    AST kullanılır, regex DEĞİL: çok satırlı çağrılarda kw'lar satıra bölünür ve düz metin
    taraması onları kaçırır (bu dosyanın hedefi olan iki çağrı da çok satırlıdır).

    TARAYICININ SINIRI YAZILI (2026-09-03 incelemesi, K6): yalnız TABANI `obs` ADI olan çağrılar
    görülür. `from . import obs as _obs` ya da `from .obs import alarm` biçiminde yazılmış bir
    üretici bu tarayıcıya GÖRÜNMEZ. Bugün ağaçta öyle bir çağrı yok (ölçüldü 2026-09-03), yani
    tarayıcı bugün eksiksizdir — ama ilk öyle çağrı yazıldığı gün bu dosya SESSİZCE körelir.
    Sınırı kapatmak yerine YAZDIM: ölçülmemiş bir kapsam iddiası, kapsamın kendisinden beterdir.
    """
    for dugum in ast.walk(kok):
        if not isinstance(dugum, ast.Call):
            continue
        f = dugum.func
        if isinstance(f, ast.Attribute) and f.attr in ("log", "warn", "alarm", "event"):
            taban = f.value
            if isinstance(taban, ast.Name) and taban.id == "obs":
                yield f.attr, dugum


def _obs_cagrilari(kaynak: str):
    """`_obs_cagrilari_dugumden`in tüm-dosya sarmalı (tek çekirdek, iki giriş — tek-kaynak)."""
    yield from _obs_cagrilari_dugumden(ast.parse(kaynak))


def _kw_adlari(cagri: ast.Call) -> set[str]:
    return {k.arg for k in cagri.keywords if k.arg}


# =================================================================================================
# A) TSK-101 — ALARM/OLAY İMZASINDA `mekanizma=` (TÜRKÇE) KALMADI
# =================================================================================================
# CANLI ÖLÇÜM (2026-09-03, bu tur): `meridian/*.py` içinde `mekanizma=` kw'lı İKİ üretici vardı —
# `loop.py::_reconcile_gunu_atlandi` (broker_reconcile) ve `skill_gorus.py::kuyruk_kadansi` (skill_gorus_kuyruk).
# Brief tek aykırı imza ölçmüştü; ikincisi bu turda tarayıcıyla bulundu. İkisi de MECHANISM_STALE
# üreticisidir ve tüketiciler (`selfreview._olay_mekanizma`, `notify._signature`) `mechanism` okur:
# Türkçe alan defterde DURUYOR ama hiçbir okuyucuya ULAŞMIYORDU.
def test_meridian_kaynaginda_mekanizma_kw_li_obs_cagrisi_YOK():
    """Üretici imzası tek dilde olmalı: tüketicinin okuduğu ad `mechanism`."""
    ihlal = []
    for yol in KAYNAKLAR:
        for ad, cagri in _obs_cagrilari(yol.read_text(encoding="utf-8")):
            if "mekanizma" in _kw_adlari(cagri):
                ihlal.append(f"{yol.name}::obs.{ad} (satır {cagri.lineno})")
    assert not ihlal, ("obs çağrısında TÜRKÇE `mekanizma=` alanı — hiçbir tüketici bu adı "
                       f"okumaz (imza kayması): {ihlal}")


def test_tarayici_SENTETIK_ihlali_yakalar():
    """POZİTİF KONTROL: yukarıdaki tarayıcı boşta 'temiz' demiyor, gerçekten ısırıyor."""
    sentetik = ('from . import obs\n'
                'def f():\n'
                '    obs.alarm("MECHANISM_STALE", "x",\n'
                '              mekanizma="uydurma_mekanizma", gun=1)\n')
    bulunan = [ad for ad, c in _obs_cagrilari(sentetik) if "mekanizma" in _kw_adlari(c)]
    assert bulunan == ["alarm"], f"tarayıcı sentetik ihlali GÖRMEDİ: {bulunan}"


def test_mechanism_kw_li_uretici_TABANI_duruyor():
    """CANLI TABAN: doğru biçim kaynakta gerçekten var (ölçüldü 2026-09-03: 8 üretici —
    watchdog ×5, selfreview ×1, loop ×1, skill_gorus ×1). Taban düşerse tarayıcı 'temiz' der
    ama sistem alanı KAYBETMİŞ olur; sayı değil ALT SINIR çivilenir (yeni üretici serbest)."""
    n = sum(1 for yol in KAYNAKLAR
            for _ad, c in _obs_cagrilari(yol.read_text(encoding="utf-8"))
            if "mechanism" in _kw_adlari(c))
    assert n >= 8, f"`mechanism=` üretici sayısı ölçülen tabanın altında ({n} < 8)"


@pytest.mark.parametrize("modul,sembol,deger", [
    ("loop.py", "_reconcile_gunu_atlandi", "broker_reconcile"),
    ("skill_gorus.py", "kuyruk_kadansi", "skill_gorus_kuyruk"),
])
def test_TSK101_hedefi_iki_uretici_mechanism_yaziyor(modul, sembol, deger):
    """İki hedef üretici ADIYLA çivilenir — genel tarayıcı yeşilken bu iki çağrının alanı
    silinmiş de olabilirdi (tarayıcı yokluğu ihlal saymaz).

    `sembol` DE ÇİVİLENİR (2026-09-03 incelemesi, Ö1): ilk yazımda bu tablo `skill_gorus.olc` [çapa-mezar-taşı]
    diyordu ve öyle bir sembol YOKTU — yani TSK-030'un kapatmaya çalıştığı sınıfın bir örneği
    tam bu turda ÜRETİLDİ, üstelik `sembol` parametresi yalnız hata metninde geçtiği için hiçbir
    çivi görmedi. Artık iki iddia birden ölçülür: (a) sembol AST'de VAR, (b) `mechanism=` yazan
    çağrı O GÖVDENİN İÇİNDE. (b) olmadan tablo doğru adı taşıyıp yanlış gövdeyi gösterebilirdi.
    """
    agac = ast.parse((MERIDIAN / modul).read_text(encoding="utf-8"))
    govdeler = [d for d in ast.walk(agac)
                if isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef)) and d.name == sembol]
    assert govdeler, f"{modul} içinde `{sembol}` sembolü YOK — çapa çürük doğdu"
    bulundu = [c for g in govdeler for _ad, c in _obs_cagrilari_dugumden(g)
               if any(k.arg == "mechanism" and isinstance(k.value, ast.Constant)
                      and k.value.value == deger for k in c.keywords)]
    assert bulundu, f"{modul}::{sembol} GÖVDESİ artık `mechanism={deger!r}` yazmıyor"


def test_broker_reconcile_alarmi_KOSUMDA_mechanism_alani_dusurur(monkeypatch, sandbox_state):
    """KABLO KANITI — kaynak taraması alanın DEĞERİNİ görmez. Alarm gerçekten koşturulur ve
    olay sözlüğünün tepesinde `mechanism` bulunur (`obs._emit` kw'ları tepeye düşürür)."""
    from meridian import config, loop, obs, store
    takvim = ["2026-08-18", "2026-08-19", "2026-08-20", "2026-08-21"]
    monkeypatch.setattr(config, "BROKER", "alpaca_paper", raising=False)
    loop._RECONCILE_ATLANDI_LOGGED.clear()
    yakalanan: list = []
    monkeypatch.setattr(obs, "alarm",
                        lambda token, message, **f: yakalanan.append({"token": token, **f}))
    store.write_json("broker_reconcile.json", {"date": "2026-08-19", "position_drift": False})
    try:
        loop._reconcile_gunu_atlandi("noop", "2026-08-21", takvim=takvim)
    finally:
        loop._RECONCILE_ATLANDI_LOGGED.clear()
    assert yakalanan, "alarm hiç basılmadı — çivi kendi hedefini kaybetti"
    olay = yakalanan[0]
    assert olay["token"] == "MECHANISM_STALE"
    assert olay.get("mechanism") == "broker_reconcile", \
        f"alarm `mechanism` alanı taşımıyor: {sorted(olay)}"
    assert "mekanizma" not in olay, "Türkçe alan hâlâ basılıyor"


def test_selfreview_TSK101_alarmini_ADIYLA_okuyabilir():
    """TÜKETİCİ UCU: düzeltilen üreticinin olayı artık düşüşün İLK basamağında ad veriyor —
    mesaj öneki kırpmasına düşmüyor (v369 sınıf-4 → sınıf-1)."""
    from meridian import selfreview
    olay = {"alarm": "MECHANISM_STALE", "message": "mutabakat 3 işlem günüdür koşmuyor",
            "mechanism": "broker_reconcile", "gun": 3}
    assert selfreview._olay_mekanizma(olay) == "broker_reconcile"


# =================================================================================================
# B) TSK-102 — `watchdog_incidents` SÜRE DÜŞÜŞÜ (`sure_h` + `sure_kaynak`)
# =================================================================================================
# CANLI ÖLÇÜM (2026-09-03, bu tur — MECHANISM_STALE üreticilerinin süre alanları):
#   `watchdog.check_and_alarm` (bayat-geçiş)              → `gap_h` (+ gap_s/asim_s)
#   `watchdog.check_mutabakat_and_alarm` (mutabakat bayat) → `yas_h`
#   `watchdog.check_liveness_and_alarm` (orphan/stalled)   → `age_h`
#   `watchdog.check_integrity_and_alarm` (BAYAT TÜREV)     → `behind_h`  ← BU TURDA ALAN OLARAK BASILDI
#                                                  (ölçüm brief'le çelişti: değer HESAPLANIYOR ama
#                                                   yalnız alarm METNİNDE geçiyordu, olay alanı YOKTU)
# Rapor satırı yalnız `gap_h` okuduğu için "gecikme" sütunu sınıf-1 dışında HEP boştu — ölçüm
# varken boş sütun Yasa 6'nın ters yüzüdür.
SURE_SIRASI = ("gap_h", "age_h", "yas_h", "behind_h")


def test_sure_dusus_SIRASI_sabit_ve_dort_alanli():
    """Sıra KİMLİKTİR: aynı olay iki turda iki farklı alandan okunursa satırlar kıyaslanamaz."""
    from meridian import selfreview
    assert tuple(selfreview._SURE_ALANLARI) == SURE_SIRASI


@pytest.mark.parametrize("alan", SURE_SIRASI)
def test_her_alan_TEK_BASINA_okunur_ve_KAYNAGINI_soyler(alan):
    """Dört alanın her biri gerçekten bir basamaktır (parametrik: yeni alan eklenirse burası da
    büyümeli). `sure_kaynak` olmadan operatör hangi büyüklüğe baktığını bilemez — `gap_h`
    (sessizlik) ile `behind_h` (türev gecikmesi) AYNI ŞEY DEĞİLDİR."""
    from meridian import selfreview
    assert selfreview._olay_sure_h({alan: 12.5}) == (12.5, alan)


def test_ONCELIK_soldan_saga_ilk_DOLU_alan_kazanir():
    """Dört alan aynı olayda birlikte gelirse sıranın ilki kazanır."""
    from meridian import selfreview
    assert selfreview._olay_sure_h(
        {"gap_h": 1.0, "age_h": 2.0, "yas_h": 3.0, "behind_h": 4.0}) == (1.0, "gap_h")
    assert selfreview._olay_sure_h({"age_h": 2.0, "yas_h": 3.0}) == (2.0, "age_h")
    assert selfreview._olay_sure_h({"yas_h": 3.0, "behind_h": 4.0}) == (3.0, "yas_h")


def test_YOKLUK_None_dondurur_UYDURMAZ():
    """Uydurma yasağı: süre ölçülemediğinde 0.0 DEĞİL None. Sıfır "gecikme yok" der; None
    "ölçmedim" der ve ikisi aynı şey değildir."""
    from meridian import selfreview
    assert selfreview._olay_sure_h({}) == (None, None)
    assert selfreview._olay_sure_h({"kind": "parity", "artifact": "x.json"}) == (None, None)
    assert selfreview._olay_sure_h({"gap_h": None, "age_h": None}) == (None, None)
    assert selfreview._olay_sure_h("olay değil") == (None, None)


def test_SAYIYA_cevrilemeyen_deger_basamagi_TUKETMEZ():
    """Bir alan dolu ama sayı değilse (bozuk satır) düşüş DEVAM eder — yoksa tek bozuk alan
    arkasındaki ölçülmüş süreyi gizlerdi."""
    from meridian import selfreview
    assert selfreview._olay_sure_h({"gap_h": "yok", "age_h": 6.0}) == (6.0, "age_h")
    assert selfreview._olay_sure_h({"gap_h": "", "yas_h": 7.5}) == (7.5, "yas_h")


def test_BOOL_bir_SURE_DEGILDIR(sandbox_state):
    """K7 (2026-09-03 incelemesi): Python'da `float(True) == 1.0`, yani bir BAYRAK sessizce
    "1 saat" diye okunabilirdi. Bugün hiçbir üretici bu alanlara bool basmıyor (ölçüldü), ama
    ilk basan gün rapor "1.0 sa gecikme" yazar ve o sayı UYDURMA olur."""
    from meridian import selfreview
    assert selfreview._olay_sure_h({"gap_h": True}) == (None, None)
    assert selfreview._olay_sure_h({"gap_h": False, "age_h": 4.0}) == (4.0, "age_h")


def test_rapor_satiri_sure_h_TASIR_ve_gap_h_KORUNUR(sandbox_state):
    """ENTEGRASYON: yardımcının doğru olması yetmez — `build()` onu GERÇEKTEN çağırmalı.
    `gap_h` alanı KORUNUR (mevcut okuyucular kırılmaz; tek-kaynak değil GEÇİŞ zorunluluğu)."""
    import datetime as dt
    from meridian import selfreview, store
    simdi = dt.datetime.now(dt.timezone.utc)
    store.append_jsonl("events.jsonl", {
        "ts": (simdi - dt.timedelta(days=1)).isoformat(timespec="seconds"), "level": "alarm",
        "event": "MECHANISM_STALE SPRINT ORPHAN", "alarm": "MECHANISM_STALE",
        "message": "SPRINT ORPHAN: pid ölü", "kind": "sprint_liveness", "age_h": 9.5})
    rows = selfreview.build()["week"]["watchdog_incidents"]
    assert len(rows) == 1, rows
    r = rows[0]
    assert r["sure_h"] == 9.5 and r["sure_kaynak"] == "age_h", r
    assert r["gap_h"] is None, "gap_h `sure_h` ile DOLDURULMAMALI — kaynak alanı ayrı kalır"
    assert set(r) == {"mechanism", "gap_h", "sure_h", "sure_kaynak"}, r


def test_coherence_alarmi_behind_h_ALANINI_basar():
    """ÖLÇÜM DÜZELTMESİ (TSK-102): `behind_h` hesaplanıyordu ama yalnız alarm METNİNDE vardı;
    olay alanı olmadan düşüşün dördüncü basamağı HİÇ ATEŞLENEMEZDİ (ölü dal)."""
    import ast
    kaynak = (MERIDIAN / "watchdog.py").read_text(encoding="utf-8")
    bulundu = [c for _ad, c in _obs_cagrilari(kaynak)
               if any(k.arg == "behind_h" for k in c.keywords)
               and any(k.arg == "kind" and isinstance(k.value, ast.Constant)
                       and k.value.value == "coherence" for k in c.keywords)]
    assert bulundu, "BAYAT TÜREV alarmı `behind_h` alanını hâlâ basmıyor — dördüncü basamak ölü"


def test_dikkat_satiri_OLCULEN_sureyi_yazar(sandbox_state):
    """TÜKETİCİ UCU (Yasa 6): `sure_h` bir okuyucuya bağlanır — dikkat satırı en uzun ölçülen
    gecikmeyi ve kaynağını basar. Hiç ölçüm yoksa sayı UYDURULMAZ, satır sayısız kalır."""
    import datetime as dt
    from meridian import selfreview, store
    simdi = dt.datetime.now(dt.timezone.utc)
    for saat, alan in ((3.0, "age_h"), (41.25, "gap_h")):
        store.append_jsonl("events.jsonl", {
            "ts": (simdi - dt.timedelta(days=1)).isoformat(timespec="seconds"), "level": "alarm",
            "event": "MECHANISM_STALE x", "alarm": "MECHANISM_STALE",
            "message": "x", "mechanism": "m", alan: saat})
    satirlar = [a["why"] for a in selfreview.build().get("attention") or []
                if "bekçi olayı" in a["why"]]
    assert satirlar, "bekçi dikkat satırı hiç üretilmedi"
    assert "41.25" in satirlar[0] and "gap_h" in satirlar[0], \
        f"dikkat satırı ölçülen süreyi taşımıyor: {satirlar[0]}"


def test_dikkat_satiri_OLCUM_YOKKEN_sayi_UYDURMAZ(sandbox_state):
    """Karşı yön: süre ölçülemeyen olaylarda satır sayısız kalır (0 sa yazmaz)."""
    import datetime as dt
    from meridian import selfreview, store
    simdi = dt.datetime.now(dt.timezone.utc)
    store.append_jsonl("events.jsonl", {
        "ts": (simdi - dt.timedelta(days=1)).isoformat(timespec="seconds"), "level": "alarm",
        "event": "MECHANISM_STALE x", "alarm": "MECHANISM_STALE",
        "message": "BÜTÜNLÜK DEDEKTÖRÜ DÜŞTÜ", "kind": "detector_failed", "detector": "determinism"})
    satirlar = [a["why"] for a in selfreview.build().get("attention") or []
                if "bekçi olayı" in a["why"]]
    assert satirlar, "bekçi dikkat satırı hiç üretilmedi"
    # DAR VE DOĞRU İDDİA (2026-09-03 incelemesi, K8): ilk yazım kuyrukta "sa" HARF DİZİSİ
    # arıyordu ve metin bir gün "gecikme SAyısı" gibi bir sözcük alsa YANLIŞ SEBEPLE kırmızıya
    # dönerdi. Aranan şey kuyruğun KENDİSİdir.
    assert "(en uzun" not in satirlar[0], f"ölçüm yokken süre uyduruldu: {satirlar[0]}"


# =================================================================================================
# C) TSK-030 adım-3 — ESKİ `dosya.py:SATIR` ÇAPALARI (bu turda 16 çapa)
# =================================================================================================
# ÖLÇÜM (2026-09-03, tur başı): `meridian/*.py` 16 satır çapası taşıyordu. Üç sınıfa ayrıldılar:
#   (a) CANLI ÇAPA (8)      — hedefi okundu, `dosya.py::sembol` biçimine çevrildi,
#   (b) MEZAR TAŞI (7)      — "şu çapa bayatladı" DERSİNİ anlatan alıntılar; çevrilirse ders ölür,
#   (c) DESEN ÖRNEĞİ (1)    — `codelaw._CAPA_DESENI` şerhi, regexin YAKALAMASI GEREKEN biçimi
#                             alıntılıyor; çevrilirse belge kendi konusunu anlatamaz.
# (b) ve (c) beyanlı muafiyetle durur. MUAFİYET İŞARETİ İCAT EDİLMEZ: `codelaw._CAPA_MUAFIYETI`
# tek kaynaktır — ikinci bir işaret, taşınan dersi sessizce ihlale çevirirdi.
def _satir_capasi_deseni():
    """Satır çapası deseni TEK KAYNAKTAN gelir: `codelaw._CAPA_DESENI`.

    İlk yazımda desen buraya KOPYALANMIŞTI ve sessizce DARALMIŞTI (`[0-9]{2,5}` — tek haneli
    `x.py:7` [çapa-mezar-taşı] ya da altı haneli bir çapayı v382 görmez, codelaw görürdü). Muafiyet İŞARETİ zaten
    tek kaynaktan alınıyordu; desenin de öyle olması gerekirdi (tek-kaynak yasası: aynı gerçeğin
    iki kopyası sessizce ayrışır). 2026-09-03 incelemesi, K1.
    """
    from meridian import codelaw
    return codelaw._CAPA_DESENI


def _muafiyet() -> str:
    from meridian import codelaw
    return codelaw._CAPA_MUAFIYETI


def _capa_ihlalleri(kaynak: str, muaf: str):
    """Muafiyet İŞARETİ TAŞIMAYAN satırlardaki satır çapaları (satır no, metin)."""
    desen = _satir_capasi_deseni()
    for i, satir in enumerate(kaynak.splitlines(), 1):
        if muaf in satir:
            continue
        for m in desen.finditer(satir):
            yield i, m.group(0)


def test_muafiyet_isareti_CODELAW_TEK_KAYNAGINDAN_gelir():
    """Tek-kaynak yasası: bu dosya kendi işaretini yazsaydı, codelaw'ınkiyle sessizce ayrışırdı."""
    assert _muafiyet() == "çapa-mezar-taşı"


def test_capa_DESENI_de_CODELAW_TEK_KAYNAGINDAN_gelir():
    """K1 (2026-09-03 incelemesi): desen de kopyalanmaz, TÜRETİLİR. Kopya daralırsa bu dosya
    codelaw'ın gördüğü bir çapayı GÖRMEZ ve "temiz" der — susturulan bekçi sınıfı.
    Kopyanın somut kaybı ölçüldü: tek ve altı haneli çapalar."""
    desen = _satir_capasi_deseni()
    muaf = _muafiyet()
    for ornek in ("uydurma_modul.py:7", "uydurma_modul.py:412345"):
        assert desen.search(ornek), f"türetilen desen `{ornek}` çapasını görmüyor"
        assert list(_capa_ihlalleri(f"# bkz. {ornek}\n", muaf)) == [(1, ornek)], ornek


def test_meridian_kaynaginda_MUAFIYETSIZ_satir_capasi_YOK():
    """TSK-030 adım-3'ün bu turdaki hükmü: `meridian/*.py` içinde beyansız satır çapası kalmadı."""
    muaf = _muafiyet()
    ihlal = [f"{yol.name}:{n} → {c}" for yol in KAYNAKLAR
             for n, c in _capa_ihlalleri(yol.read_text(encoding="utf-8"), muaf)]
    assert not ihlal, ("beyansız `dosya.py:SATIR` çapası — satır kayar, çapa SESSİZCE yanlış "
                       f"satırı gösterir: {ihlal}")


def test_capa_tarayicisi_SENTETIK_ihlali_yakalar_ve_MUAFI_gecer():
    """POZİTİF KONTROL + muafiyet kapısı tek çivide: tarayıcı boşta 'temiz' demiyor, ve
    muafiyetli satırı ihlal SAYMIYOR (aksi hâlde mezar taşları yasayı susturmaya zorlardı)."""
    muaf = _muafiyet()
    yakalanan = list(_capa_ihlalleri("# bkz. uydurma_modul.py:4211 satırı\n", muaf))
    assert yakalanan == [(1, "uydurma_modul.py:4211")], yakalanan
    assert list(_capa_ihlalleri(f"# bkz. uydurma_modul.py:4211 ({muaf})\n", muaf)) == []


#: BU TURDA ÇEVRİLEN CANLI ÇAPALAR — (kaynak modül, yeni çapa metni, hedef bu depoda mı)
#: Hedefin GERÇEKTEN var olduğu AST ile doğrulanır. DOĞRULANAMAYAN YALNIZ hermes-agent İKİLİSİDİR
#: (dış depo, v0.18.2) ve o dürüstçe `False` ile işaretlidir — "doğruladım" demek uydurma olurdu.
#: DÜZELTME (2026-09-03 incelemesi, Ö2): donmuş ölçüm dizini (`research/olcumler/...`) ilk yazımda
#: yanlışlıkla "repo dışı" sayılmıştı. O dosya ağaçta MEVCUT ve semboller AST ile okunabilir; `False`
#: bir ÖLÇÜM değil, çivinin hedefi `MERIDIAN / basename` diye çözmesinden doğan bir SINIRDI. Çivi
#: artık yolu repo köküne göre çözüyor ve ikisi de `True`. Bu iki çapa başka HİÇBİR yerde
#: ölçülmüyor: `codelaw` kökleri `meridian`+`tests`+`ops`, `research/` onların dışında.
CEVRILEN = [
    ("analytics.py", "rollback.py::sweep_orphan_hypotheses", True),
    ("broker.py", "research/olcumler/edg026_slot20_2026-08-12/olcum.py::_rampa_fn", True),
    ("broker.py", "research/olcumler/edg026_slot20_2026-08-12/olcum.py::kosum", True),
    ("hermes.py", "tools/skill_usage.py::_skills_dir", False),
    ("hermes.py", "hermes_constants.py::HERMES_HOME", False),
    ("sprint_run.py", "reflect.py::coordinate_descent_search", True),
]


@pytest.mark.parametrize("modul,capa,_repo_ici", CEVRILEN)
def test_cevrilen_capa_KAYNAKTA_duruyor(modul, capa, _repo_ici):
    """Çapa metni ADIYLA çivilenir: satır çapası tarayıcısı yeşilken çapa büsbütün SİLİNMİŞ de
    olabilirdi ve o zaman ders kaybolurdu (sessizce silme yasağı)."""
    assert capa in (MERIDIAN / modul).read_text(encoding="utf-8"), \
        f"{modul} içinde `{capa}` çapası yok"


@pytest.mark.parametrize("modul,capa,repo_ici", [c for c in CEVRILEN if c[2]])
def test_repo_ici_hedef_sembolu_GERCEKTEN_var(modul, capa, repo_ici):
    """YORUM DOĞRULAMASI'nın mekanik yarısı: sembol AST'de bulunmalı. Sembol çapası da çürür,
    ama SESLİ çürür — bu çivi o sesi çıkarır.

    HEDEF REPO KÖKÜNE GÖRE ÇÖZÜLÜR (Ö2): çapa bir YOL taşıyorsa (`research/.../olcum.py`) o yol
    kökten okunur; taşımıyorsa (`rollback.py`) `meridian/` altından. İlk yazım her hedefi
    `MERIDIAN / basename` diye çözüyordu ve donmuş ölçüm dizinini YAPISAL OLARAK göremiyordu."""
    hedef, sembol = capa.split("::")
    yol = (REPO / hedef) if "/" in hedef else (MERIDIAN / hedef)
    assert yol.exists(), f"çapa hedefi ağaçta yok: {yol}"
    agac = ast.parse(yol.read_text(encoding="utf-8"))
    adlar = {d.name for d in ast.walk(agac)
             if isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    assert sembol in adlar, f"{hedef} içinde `{sembol}` sembolü YOK — çapa çürük doğdu"


def test_codelaw_satir_capasi_hukmu_TEMIZ():
    """Yasanın kendi ölçüsü: `stale_line_anchors` bu turdan sonra da çürük çapa görmemeli
    (yeni biçim `dosya.py::sembol` satır desenine HİÇ uymaz — yasa onu satır dünyasında
    görmez ve görmemesi doğrudur)."""
    from meridian import codelaw
    cozulemeyen: list = []
    curuk = codelaw.stale_line_anchors("meridian", cozulemeyen_out=cozulemeyen)
    assert curuk == [], f"çürük satır çapası: {curuk}"


# =================================================================================================
# D) TSK-006 — `session_refresh` ANAHTARI IP (restart sonrası 57 yol → 1 satır)
# =================================================================================================
# CANLI ÖLÇÜM (A1, son 24 saat, 2026-09-03 06:3xZ): 977 olayın 106'sı `session_refresh`, 97'si
# `ozet=False` İLK-SATIR — restart/pano açılışında 57 AYRI YOL için birer satır (saatlik tepe 44).
# Sözleşmenin GERİ KALANI v374'te çivilidir; burada YALNIZ ölçümün kendisi ÖLÇEKLE tekrarlanır:
# üç yolla geçen bir çivi, 57 yolda da geçerdi ama ÖLÇÜLEN OLGUYU anlatmazdı.
CANLI_YOL_SAYISI = 57         # ölçüldü 2026-09-03 (A1 canlı defteri, restart penceresi)


def test_RESTART_SONRASI_57_YOL_TEK_SATIR(sandbox_state):
    """TSK-006'nın ÖLÇÜLMÜŞ hâli: taze süreç (boş bellek) + tek IP + 57 ayrı yol → 1 satır.
    Eski (ip, yol) anahtarında bu 57 satırdı."""
    from meridian import api
    f = api._session_refresh_ornekle
    yazilan = [f("127.0.0.1", f"/api/y{i}", now=1788307200.0 + i)
               for i in range(CANLI_YOL_SAYISI)]
    basilan = [k for k in yazilan if k is not None]
    assert basilan == [{"ozet": False}], f"{len(basilan)} satır basıldı, 1 bekleniyordu"
    assert set(api._REFRESH_SON) == {"127.0.0.1"}, api._REFRESH_SON


def test_ERTESI_GUN_OZETI_57_YOLU_TEK_SATIRDA_tasir(sandbox_state):
    """BEDEL BEYANI'nın ölçülen yarısı: yol düzeyi görünürlük KAYBOLMAZ, bir gün GECİKİR —
    ertesi günün TEK özet satırı dağılımı taşır ve sayı korunur."""
    from meridian import api
    f = api._session_refresh_ornekle
    for i in range(CANLI_YOL_SAYISI):
        f("127.0.0.1", f"/api/y{i}", now=1788307200.0 + i)
    ozet = f("127.0.0.1", "/api/summary", now=1788307200.0 + 86400)
    assert ozet["ozet"] is True and ozet["gun"] == "2026-09-02", ozet
    # anında yazılan ilk satır sayılmaz (toplam korunumu) → 57 - 1 = 56
    assert ozet["toplam_n"] == CANLI_YOL_SAYISI - 1, ozet
    assert sum(ozet["yollar"].values()) + ozet["diger_n"] == ozet["toplam_n"], ozet
    assert len(ozet["yollar"]) == api._REFRESH_YOL_OZET, len(ozet["yollar"])


def test_conftest_SIFIRLAMASI_yeni_anahtar_yapisiyla_UYUMLU(sandbox_state):
    """Sıfırlama mekanizması sözlüğü YERİNDE temizler ve taban `{}`tır — anahtar tipi
    (tuple → str) ve değer şekli (liste + iç sözlük) değişse de uyumlu KALIR. Bu çivi o
    varsayımı ölçer: uyumsuzlaşırsa sızıntı SESSİZ olurdu (sonraki test hiç satır görmez)."""
    import tests.conftest as cf
    from meridian import api
    api._session_refresh_ornekle("1.2.3.4", "/x", now=1788307200.0)
    assert api._REFRESH_SON
    api._REFRESH_SON.clear()
    api._REFRESH_SON.update(cf._MODUL_DURUMU0["meridian.api._REFRESH_SON"])
    assert api._REFRESH_SON == {}, "taban boş değil — sıfırlama sonraki testi kirletir"


# =================================================================================================
# E) ÜÇÜNCÜ BESLEME — BU DİLİMİN KENDİ YAZDIĞI SEMBOL ÇAPALARI DENETLENİR
# =================================================================================================
# NEDEN VAR (2026-09-03 yeniden-incelemesi, Ö1 KISMİ): bu dilim "satır çapası → sembol çapası,
# çünkü sembol AST ile doğrulanabilir" iddiası üzerine kuruluydu — ve kendi yeni yorum metninde
# ÜÇ yanlış sembolü YEDİ konumda üretti (`skill_gorus.olc` · `notify._imza` ·  [çapa-mezar-taşı]
# `watchdog._sessiz_hat`; biri ÜRETİM kodunda) [çapa-mezar-taşı]. Hiçbir mekanik kapı görmedi: `codelaw` yasası
# `modül.sembol` biçimini YALNIZ `DECLARED_*` beyan metinlerinde tarar (`capa_uyusmasi` kapsam
# sınırı 1), bu dosyaların serbest yorumlarını HİÇ görmez.
#
# BU ÇİVİ O BOŞLUĞU DAR VE ÖLÇÜLEBİLİR BİÇİMDE KAPATIR: yasanın KENDİ çekirdeğini (`capa_uyusmasi`)
# üçüncü bir beslemeyle çağırır — yeni bir tarayıcı YAZMAZ (tek-kaynak yasası; ikinci bir çekirdek
# zamanla ayrışır ve "çürüme" tanımı ikiye bölünürdü).
#
# KAPSAM DÜRÜSTÇE DAR: yalnız BU DİLİMİN dokunduğu dosyalar. Depo genelindeki aynı sınıf
# (`meridian/**` + `tests/**` yorumları) ROADMAP'te TSK-119'un kardeşi olarak durur — burada
# genişletmek, ölçmediğim bir tabanı çivilemek olurdu.
#
# `meridian/api.py` BESLEMEDE DEĞİL VE BU BİR ÖLÇÜMDÜR, KAÇAMAK DEĞİL: aynı çekirdekle tarandığında
# o dosya YEDİ çürük `modül.sembol` çapası veriyor (ölçüldü 2026-09-03: `shadow_model.terfi` ×2,  [çapa-mezar-taşı]
# `shadow_model.refit_and_save`, `skills.ARSIV`, `ledgers.cf_resolved`, `durum_sozlugu.satirlar`,  [çapa-mezar-taşı]
# `auth.header.Authorization`) — HİÇBİRİ bu dilimin yazdığı satır değil, hepsi TUR ÖNCESİNDEN.  [çapa-mezar-taşı]
# Onları bu çiviye almak, kapsamı dışındaki bir borcu bu dilime fatura ederdi; sessizce atlamak ise
# ölçümü gizlemek olurdu. Üçüncü yol: ölçtüm, RAPORA yazdım, Rol-1'e devrettim (TSK-119 kardeşi).
UCUNCU_BESLEME = (
    "meridian/selfreview.py",                       # ÜRETİM: TSK-102 ölçüm tablosu
    "tests/test_kovab_dilim_v382.py",               # bu dosya (kendi tablolarım dahil)
    "tests/test_selfreview_mekanizma_adi_v369.py",
    "tests/test_karne_ship_sayimi_v304.py",
    "tests/test_ogrenme_katmani_durmasi_v235.py",
    "tests/test_skill_gorus_kuyruk_v356.py",
    "tests/test_mutborc_broker_entry_limit_price_v148.py",
    "tests/test_triyaj_duzeltmeleri_v274.py",
)


def _ucuncu_besleme_hukmu():
    """`codelaw.capa_uyusmasi`ı bu dilimin dosyalarıyla besler (çekirdek TEK, besleme üçüncü)."""
    from meridian import codelaw
    metinler = [(y, (REPO / y).read_text(encoding="utf-8")) for y in UCUNCU_BESLEME]
    return codelaw.capa_uyusmasi(metinler, modul_bicimi=True)


def test_BU_DILIMIN_yazdigi_SEMBOL_CAPALARI_CURUK_DEGIL():
    """ASIL HÜKÜM: `curuyen` = hedef modül VAR ama sembol YOK → çapa doğarken çürük.
    Ö1'in üç örneği (olc/_imza/_sessiz_hat) bu kovaya düşerdi."""
    out = _ucuncu_besleme_hukmu()
    assert out["curuyen"] == [], (
        "doğarken çürük sembol çapası — modül var, sembol YOK. Sembol çapasının tek üstünlüğü "
        f"SESLİ çürümesidir; ses buradan çıkar: {out['curuyen']}")


def test_UCUNCU_BESLEME_sessizce_BOS_DEGIL():
    """Tarayıcı "boşta temiz" diyemez: bu dosyalar GERÇEKTEN sembol çapası taşıyor ve
    çözülenler ölçülmüş bir sayıdır. Taban düşerse çivi hiçbir şey ölçmüyor demektir."""
    out = _ucuncu_besleme_hukmu()
    assert len(out["cozulen"]) >= 40, \
        f"üçüncü besleme neredeyse hiçbir çapa görmedi ({len(out['cozulen'])}) — kör kalmış olabilir"


def test_UCUNCU_BESLEME_Ö1in_UC_SEMBOLUNU_yakalardi():
    """POZİTİF KONTROL — yeşilin ANLAMI: aynı çekirdeğe Ö1'in üç yanlış adı sentetik olarak
    verilir ve ÜÇÜ DE `curuyen`e düşmelidir. Bu olmadan yukarıdaki iki çivi, tarayıcının
    çalıştığını değil yalnız sessiz olduğunu gösterirdi."""
    from meridian import codelaw
    sentetik = ("SENTETIK", "`skill_gorus.olc` `notify._imza` `watchdog._sessiz_hat` ")  # çapa-mezar-taşı
    out = codelaw.capa_uyusmasi([sentetik], modul_bicimi=True)
    curuk = {c["capa"] for c in out["curuyen"]}
    assert curuk == {"skill_gorus.olc", "notify._imza", "watchdog._sessiz_hat"}, out


def test_DUZELTILEN_UC_SEMBOL_gercekten_VAR():
    """Ö1 düzeltmesinin kendisi ölçülür: üç DOĞRU ad AST'de bulunmalı. Yanlışın gitmesi
    yetmez — doğrunun geldiği de ölçülmeli (aksi hâlde ad büsbütün silinmiş olabilirdi)."""
    for modul, sembol in (("skill_gorus.py", "kuyruk_kadansi"),
                          ("notify.py", "_signature"),
                          ("watchdog.py", "check_and_alarm")):
        agac = ast.parse((MERIDIAN / modul).read_text(encoding="utf-8"))
        adlar = {d.name for d in ast.walk(agac)
                 if isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
        assert sembol in adlar, f"{modul}::{sembol} YOK"
