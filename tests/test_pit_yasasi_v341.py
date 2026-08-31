"""v337 — "PIT'siz fundamentals proxy YASAK" yasasının İLK mekanik çivisi.

CLAUDE.md §4 bu yasağı 2026-08-30'a kadar yalnız SAYIYORDU: `guard.py`de kapı yok, `codelaw.py`da
denetçi yok, `tests/` altında çivi yok. Ölçüm operatör kararıyla açıldı ve bu dosya yasağın ilk
mekanik karşılığıdır (`meridian/pitlaw.py`).

NUMARA KİMLİKTİR: `v337` bu turda BOŞTU (en büyük kullanılan `v336`,
`tests/test_pencere_damga_duzeltmesi_v336.py`). `v325` çakışması (iki dosya) bu dosyadan ÖNCE
vardı ve bu tur onu ne büyüttü ne düzeltti — kayıt için yazılıyor.

ÇİVİNİN KAPSAMI — DÜRÜST BEYAN. Gördüğü: kaynak ağacındaki DOĞRUDAN çağrı (`earnings.in_blackout`)
ve modül-içi kapanımla ULAŞILAN dolaylı zincir (`backtest → strategy.scan_entry → … →
days_since_report`). GÖREMEDİĞİ: dinamik erişim (`getattr`), sözlükten/dizgeden çağrı, ve kaynak
kaydında OLMAYAN bir adaptör — üçü de `rapor()["gorulmeyen"]` kovasında ADIYLA sayılır ve
`ok` hükmünü ETKİLEMEZ (ölçülemeyen şey ihlal değildir; ama sayılmayan körlük körlüğü gizler).

BİLİNEN İHLAL VAR ve YEŞİLE ALINDI (düzeltme AYRI KARAR — bu tur ölçtü, düzeltmedi):
`backtest.py` ve `cf_backfill.py` `earnings.in_blackout`u bilerek kesti ama AYNI dosyadaki
`strat.scan_entry`/`scan_all` çağrısı aynı PIT'siz takvimi tarihsel seansa sokuyor. Beyan
`pitlaw.BILINEN_IHLALLER`de gerekçesiyle duruyor ve `test_bilinen_ihlaller_HALA_GERCEK` onu
ölü kalmaya karşı çiviler.

Bu dosya `sandbox_state` KULLANMAZ: `pitlaw` (ve `codelaw`) diske yazmaz, `config.STATE`e hiç
dokunmaz — yalnız kaynak ağacını okur. `exec_module` da kullanmaz (v334 bayat-bytecode yasağı):
`from meridian import pitlaw` normal paket importudur, sentetik ağaçlar DOSYA olarak yazılıp
`root=` ile taranır, hiç yüklenmez.

SÜRÜM v337 → 341 önekiyle v341/v342 (2026-08-31): dosya worktree'de v337
olarak yazıldı; entegrasyon anında main'de v337 zaten doluydu (tahta_hijyeni_v337 /
karne_brifingi_v338). vNNN KİMLİKTİR; az-çapalı taraf taşınır — bu, oturumun ÜÇÜNCÜ vNNN
çakışması ve devir brief'i bunu kalem 3 olarak öngörmüştü.
"""
from __future__ import annotations

import ast
import pathlib
import textwrap

import pytest

from meridian import codelaw, pitlaw

KOK = "meridian"


# ---------------------------------------------------------------------------
# Sentetik ağaç kurucuları — ihlali ÜRETİP yakalandığını görmek için
# ---------------------------------------------------------------------------
def _yaz(kok: pathlib.Path, ad: str, govde: str) -> None:
    (kok / ad).write_text(textwrap.dedent(govde), encoding="utf-8")


def _dosya(yer: str) -> str:
    """`"backtest.py:5"` → `"backtest.py"`. Çağrı yerini ADIYLA sınamak için; beklenen değeri
    tam biçimde yazmak bu dosyada SAHTE BİR SATIR ÇAPASI doğururdu (bkz. ilk pozitif kontrol)."""
    return yer.rsplit(":", 1)[0]


def _satir(yer: str) -> int:
    return int(yer.rsplit(":", 1)[1])


def _earnings_modulu(kok: pathlib.Path) -> None:
    """Kaynak kaydındaki adları GERÇEKTEN tanımlayan sentetik `earnings.py`. Adların var olması
    şart: `_call_index` çağrı hedefini modül KÖKÜNDEN çözer."""
    _yaz(kok, "earnings.py", """
        def in_blackout(t, d):
            return False

        def days_since_report(t, d, max_days=5):
            return False

        def known(t):
            return True
    """)


def _edgar_modulu(kok: pathlib.Path) -> None:
    _yaz(kok, "edgar_shares.py", """
        def as_of_shares(t, d):
            return None
    """)


# ---------------------------------------------------------------------------
# A) POZİTİF KONTROL — sentetik ihlal YAKALANIR
# ---------------------------------------------------------------------------
def test_pozitif_kontrol_tarihsel_modul_DOGRUDAN_cagirinca_yakalanir(tmp_path):
    """Yasanın çekirdeği: geçmiş bir seansı yeniden yürüten modül, PIT'siz bir karar-etkili
    kaynağı ÇAĞIRIRSA kırmızı. Bu çivi düşerse yasağın mekanik karşılığı yok demektir."""
    _earnings_modulu(tmp_path)
    _yaz(tmp_path, "backtest.py", """
        from . import earnings

        def replay(gun):
            return earnings.in_blackout("AAPL", gun)
    """)
    r = pitlaw.rapor(str(tmp_path))
    # ÇAPA DOĞURMA: beklenen değer `"backtest.py:5"` biçiminde YAZILMAZ. O dizge codelaw'ın
    # satır-çapası yasasına (`_CAPA_DESENI`, sıfır tolerans, `tests/` de taranır) gerçek bir çapa
    # gibi görünür ve hükmü DEPODAKİ `meridian/backtest.py`nin 5. satırına bağlanırdı — bu testin
    # sentetik tmp ağacıyla hiç ilgisi olmayan bir dosyaya. Dosya ve satır AYRI sınanır.
    assert [_dosya(k["yer"]) for k in r["tarihsel_dogrudan"]] == ["backtest.py"], \
        f"tarihsel doğrudan ihlal yakalanamadı: {r['tarihsel_dogrudan']}"
    assert [_satir(k["yer"]) for k in r["tarihsel_dogrudan"]] == [5]
    assert r["tarihsel_dogrudan"][0]["sembol"] == "earnings.in_blackout"
    assert r["ok"] is False, f"ihlal varken ok=True: {r}"


def test_pozitif_kontrol_TAKMA_ADLI_import_da_yakalanir(tmp_path):
    """`from . import earnings as earn` biçimi canlı `strategy.py`nin GERÇEK biçimidir —
    görülmeseydi çivi tam da ölçülen ihlali kaçırırdı."""
    _earnings_modulu(tmp_path)
    _yaz(tmp_path, "cf_backfill.py", """
        from . import earnings as earn

        def _plans_for_session(d):
            return earn.days_since_report("AAPL", d, max_days=35)
    """)
    r = pitlaw.rapor(str(tmp_path))
    assert [k["sembol"] for k in r["tarihsel_dogrudan"]] == ["earnings.days_since_report"], \
        f"takma adlı import çözülemedi: {r['tarihsel_dogrudan']}"


def test_pozitif_kontrol_DOLAYLI_zincir_yakalanir(tmp_path):
    """ÖLÇÜLEN GERÇEK İHLALİN BİÇİMİ. `in_blackout` kesildikten sonra geriye kalan yol budur:
    tarihsel modül bir KARAR modülünün fonksiyonunu çağırır, o fonksiyon iki sıçrama ötede
    PIT'siz kaynağa iner. `codelaw._reach_in_module`un `_HOP=1`i bunu göremezdi."""
    _earnings_modulu(tmp_path)
    _yaz(tmp_path, "strategy.py", """
        from . import earnings as earn

        def evaluate_pead(t, d):
            return earn.days_since_report(t, d, max_days=35)

        def scan_all(t, d):
            return evaluate_pead(t, d)

        def scan_entry(t, d):
            return scan_all(t, d)
    """)
    _yaz(tmp_path, "backtest.py", """
        from . import strategy as strat

        def replay(gun):
            return strat.scan_entry("AAPL", gun)
    """)
    r = pitlaw.rapor(str(tmp_path))
    beyansiz = r["tarihsel_dolayli_beyansiz"]
    assert beyansiz, f"iki sıçramalık dolaylı zincir görülmedi: {r}"
    k = beyansiz[0]
    assert (k["tarihsel_modul"], k["ara_modul"], k["ara_fonksiyon"]) \
        == ("backtest.py", "strategy.py", "scan_entry"), f"zincir yanlış çözüldü: {k}"
    assert k["uclar"] == ["earnings.days_since_report"], f"uç sembol yanlış: {k}"
    assert r["ok"] is False


def test_pozitif_kontrol_zincir_FONKSIYON_REFERANSI_uzerinden_de_gorulur(tmp_path):
    """ZİNCİRİN GERÇEK BİÇİMİ — ve çivinin ilk koşumda koptuğu yer. `strategy.scan_all`
    değerlendiricileri bir demetten koşturur (`for fn in (…, evaluate_pead, …): fn(...)`), yani
    `evaluate_pead` bir ÇAĞRI değil bir AD'dır. Yalnız çağrılara bakan kapanım tam da ölçülen
    ihlalin geçtiği yerde kopuyordu."""
    _earnings_modulu(tmp_path)
    _yaz(tmp_path, "strategy.py", """
        from . import earnings as earn

        def evaluate_pead(t, d):
            return earn.days_since_report(t, d, max_days=35)

        def scan_all(t, d):
            for fn in (evaluate_pead,):
                return fn(t, d)

        def scan_entry(t, d):
            return scan_all(t, d)
    """)
    _yaz(tmp_path, "backtest.py", """
        from . import strategy as strat

        def replay(gun):
            return strat.scan_entry("AAPL", gun)
    """)
    r = pitlaw.rapor(str(tmp_path))
    assert r["tarihsel_dolayli_beyansiz"], (
        "fonksiyon REFERANSI üzerinden kurulan zincir görülmedi — kapanım yalnız çağrılara "
        f"bakıyor olabilir: {r}")


def test_BEYAN_zinciri_ok_hukmunden_DUSURUR_ama_kaydi_TUTAR(tmp_path):
    """Bilinen-ihlal beyanı bir SUSTURMA değil bir DEFTERDİR: zincir raporda ADIYLA durur,
    yalnız `ok` hükmüne dokunmaz. Beyan zinciri raporun dışına atsaydı, düzeltilmemiş borç
    görünmez olurdu."""
    _earnings_modulu(tmp_path)
    _yaz(tmp_path, "strategy.py", """
        from . import earnings as earn

        def evaluate_pead(t, d):
            return earn.days_since_report(t, d, max_days=35)

        def scan_entry(t, d):
            return evaluate_pead(t, d)
    """)
    _yaz(tmp_path, "backtest.py", """
        from . import strategy as strat

        def replay(gun):
            return strat.scan_entry("AAPL", gun)
    """)
    beyan = {("backtest.py", "earnings", "days_since_report"):
             "sentetik beyan — ölçüldü ve düzeltmesi ayrı karara bırakıldı (≥20 karakter)"}
    r = pitlaw.rapor(str(tmp_path), bilinen=beyan)
    assert r["tarihsel_dolayli_beyansiz"] == [], f"beyanlı zincir beyansız sayıldı: {r}"
    assert len(r["tarihsel_dolayli_beyanli"]) == 1, "beyanlı zincir raporda tutulmadı"
    assert r["curuk_beyan"] == []
    assert r["ok"] is True, f"beyanlı zincir ok'u düşürdü: {r}"


def test_OLU_BEYAN_curuk_sayilir(tmp_path):
    """Kodda karşılığı kalmayan beyan çürüktür (codelaw.stale_sinks disiplini). Düzeltilen bir
    borcun kaydı yerinde kalırsa liste 'kimsenin bakmadığı çöplüğe' döner."""
    _earnings_modulu(tmp_path)
    beyan = {("backtest.py", "earnings", "days_since_report"):
             "artık kodda olmayan bir zincire ait sentetik beyan (≥20 karakter gerekçe)"}
    r = pitlaw.rapor(str(tmp_path), bilinen=beyan)
    assert r["curuk_beyan"] == ["backtest.py→earnings.days_since_report"], \
        f"ölü beyan çürük sayılmadı: {r['curuk_beyan']}"
    assert r["ok"] is False


def test_pozitif_kontrol_canli_TABAN_asilinca_oter(tmp_path):
    """Canlı dünyanın hükmü çırçırdır: borç BÜYÜYEMEZ. Tabandan bir fazla çağrı kırmızıdır."""
    _earnings_modulu(tmp_path)
    govde = "from . import earnings\n\n"
    for i in range(pitlaw.CANLI_TABAN + 1):
        govde += f"def f{i}(d):\n    return earnings.in_blackout('AAPL', d)\n\n"
    (tmp_path / "loop.py").write_text(govde, encoding="utf-8")
    r = pitlaw.rapor(str(tmp_path))
    assert len(r["canli_karar_cagrilari"]) == pitlaw.CANLI_TABAN + 1
    assert r["canli_nuks"] is True, f"taban aşıldı ama nüks False: {r}"
    assert r["ok"] is False


# ---------------------------------------------------------------------------
# B) AŞIRIYA KAÇMAMA — yasa fazlasını yakalamaz
# ---------------------------------------------------------------------------
def test_PIT_kaynagi_tarihsel_yolda_ihlal_DEGIL(tmp_path):
    """`edgar_shares.as_of_shares` (filed <= t) tarihsel yolda MEŞRUDUR. Bu çivi olmasaydı yasa
    deponun tek gerçek PIT akışını da yasaklardı — yani doğru davranışı cezalandırırdı."""
    _edgar_modulu(tmp_path)
    _yaz(tmp_path, "backtest.py", """
        from . import edgar_shares as _es

        def replay(gun):
            return _es.as_of_shares("AAPL", gun)
    """)
    r = pitlaw.rapor(str(tmp_path))
    assert r["tarihsel_dogrudan"] == [], f"PIT kaynağı ihlal sayıldı: {r['tarihsel_dogrudan']}"
    assert r["tarihsel_dolayli_beyansiz"] == []
    assert r["ok"] is True, f"temiz ağaçta ok=False: {r}"


def test_BILGI_sinifi_sembol_tarihsel_yolda_ihlal_DEGIL(tmp_path):
    """`earnings.known` PIT'siz bir dosyayı okur ama dönüşü YALNIZ etikete gider (`COVERAGE_NOTE`);
    `verdict` yeniden atanmaz. Geriye-dönük önyargı kaynağın kendisinden değil, dönüşünün bir
    HÜKME girmesinden doğar — sınıf ayrımı bu yüzden var."""
    _earnings_modulu(tmp_path)
    _yaz(tmp_path, "backtest.py", """
        from . import earnings

        def replay(gun):
            return {"coverage": "known" if earnings.known("AAPL") else "yok"}
    """)
    r = pitlaw.rapor(str(tmp_path))
    assert r["tarihsel_dogrudan"] == [], f"bilgi sınıfı sembol ihlal sayıldı: {r}"
    assert r["ok"] is True


def test_CANLI_modulun_cagrisi_TARIHSEL_kovaya_dusmez(tmp_path):
    """İki dünya ayrı: canlı `loop.py`nin `in_blackout` çağrısı sayılır ama tarihsel ihlal
    DEĞİLDİR. Karıştırmak, meşru ileri-bakışlı soruyu yasaklamak olurdu."""
    _earnings_modulu(tmp_path)
    _yaz(tmp_path, "loop.py", """
        from . import earnings

        def daily_cycle(d):
            return earnings.in_blackout("AAPL", d)
    """)
    r = pitlaw.rapor(str(tmp_path))
    assert r["tarihsel_dogrudan"] == [], "canlı çağrı tarihsel kovaya düştü"
    assert [_dosya(k["yer"]) for k in r["canli_karar_cagrilari"]] == ["loop.py"]
    assert [_satir(k["yer"]) for k in r["canli_karar_cagrilari"]] == [5]
    assert r["canli_nuks"] is False
    assert r["ok"] is True


def test_kayitta_OLMAYAN_modul_ihlal_URETMEZ_ama_SAYILIR(tmp_path):
    """Bilinmeyen bir adaptör hakkında hüküm KURULMAZ (uydurma yasağı) — ama sessizce muaf da
    kalmaz: `gorulmeyen` kovasına `kayitta_yok` adıyla düşer."""
    (tmp_path / "adapters").mkdir()
    (tmp_path / "adapters" / "yeni_saglayici.py").write_text("def cek():\n    return 1\n",
                                                             encoding="utf-8")
    r = pitlaw.rapor(str(tmp_path))
    adlar = [g["ad"] for g in r["gorulmeyen"] if g["neden"] == "kayitta_yok"]
    assert "yeni_saglayici" in adlar, f"kayıtsız adaptör sayılmadı: {r['gorulmeyen']}"
    assert r["gorulmeyen_by_reason"]["kayitta_yok"] >= 1
    assert r["ok"] is True, "ölçülemeyen şey ihlal SAYILMAMALI (uydurma yasağı)"


# ---------------------------------------------------------------------------
# C) KAYDIN KENDİSİNİN DENETİMİ — beyan de denetlenir
# ---------------------------------------------------------------------------
def _tanimli_adlar(modul_koku: str) -> set[str] | None:
    """`meridian/` (ve `meridian/adapters/`) altında `<kök>.py`de tanımlı üst düzey adlar."""
    for f in codelaw._py_files(KOK):
        if f.name == f"{modul_koku}.py":
            tree = codelaw._ast_oku(f)
            return {n.name for n in ast.walk(tree)
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    return None


@pytest.mark.parametrize("kayit_adi", ["PIT_DISI_KAYNAKLAR", "PIT_KAYNAKLAR",
                                       "PIT_SOZLESMELI_BESLEYENI_KAPALI"])
def test_kayittaki_her_sembol_modulunde_GERCEKTEN_tanimli(kayit_adi):
    """İKİ YÖNLÜ TAMLIĞIN İLK YÖNÜ (emsal: arming.PIT_CAPALI_KURULUMLAR / çivi v301).
    Kayıt bir İDDİA değildir: adı değişen ya da silinen bir fonksiyon kaydı sessizce ölü
    bırakırsa yasa o kaynağı bir daha hiç görmez."""
    eksik = []
    for (modul_koku, fn) in getattr(pitlaw, kayit_adi):
        adlar = _tanimli_adlar(modul_koku)
        if adlar is None:
            eksik.append(f"{modul_koku}.py — modül bulunamadı")
        elif fn not in adlar:
            eksik.append(f"{modul_koku}.{fn} — modülde tanımlı değil")
    assert eksik == [], f"{kayit_adi} kaydı kaynakla uyuşmuyor: {eksik}"


def test_her_kaydin_GEREKCESI_var_ve_yeterince_uzun():
    """Gerekçesiz kayıt, `# sessiz-yutma:` gerekçesiz işaretiyle aynı şeydir: "karar verdim ve
    nedenini yazdım" yerine "üşendim". Eşik Yasa 4 emsalinden: ≥20 anlamlı karakter."""
    kisa = []
    for k, v in pitlaw.PIT_DISI_KAYNAKLAR.items():
        if len(v.get("gerekce", "").strip()) < 20:
            kisa.append(k)
    for kayit in (pitlaw.PIT_KAYNAKLAR, pitlaw.PIT_SOZLESMELI_BESLEYENI_KAPALI,
                  pitlaw.BILINEN_IHLALLER):
        kisa += [k for k, g in kayit.items() if len(str(g).strip()) < 20]
    assert kisa == [], f"gerekçesi eksik/kısa kayıtlar: {kisa}"


def test_sinif_degerleri_KAPALI_KUME():
    """Yeni bir sınıf adı sessizce eklenirse `karar_etkili()` süzgeci onu sessizce DIŞARIDA
    bırakır ve kaynak yasadan kaçar. Küme kapalı tutulur."""
    gecersiz = {k: v.get("sinif") for k, v in pitlaw.PIT_DISI_KAYNAKLAR.items()
                if v.get("sinif") not in {"karar_etkili", "bilgi"}}
    assert gecersiz == {}, f"tanımsız sınıf değeri: {gecersiz}"


def test_kayittaki_ad_ara_modulde_YEREL_DEGIL():
    """DOLAYLI ZİNCİRİN BEYANLI BEDELİ. Hedef adlar nitelenmemiştir (`days_since_report`);
    bir KARAR modülü aynı adla YEREL bir fonksiyon tanımlarsa zincir yanlış pozitif verir.
    Bugün çakışma yok — ve bu çivi, çakıştığı gün sessiz kalmamasını sağlar."""
    hedef = {fn for (_mk, fn) in pitlaw.karar_etkili()}
    cakisma = {}
    for m in pitlaw.CANLI_KARAR_YOLU:
        adlar = _tanimli_adlar(m[:-3])
        if adlar and (ortak := adlar & hedef):
            cakisma[m] = sorted(ortak)
    assert cakisma == {}, f"ara modülde aynı adlı yerel fonksiyon: {cakisma}"


# ---------------------------------------------------------------------------
# D) CANLI AĞACIN HÜKMÜ — bugün gerçekte ne var
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def canli():
    return pitlaw.rapor(KOK)


def test_canli_agacta_tarihsel_DOGRUDAN_ihlal_YOK(canli):
    """SIFIR TOLERANS DÜNYASI. `backtest.replay` ve `cf_backfill._plans_for_session`
    `in_blackout`u bilerek kesip yerine `olculemedi_replay`/`olculemedi_cf` sayacı koymuştu;
    bu çivi o hükmü artık MEKANİK tutar — kesik geri açılırsa suite kırmızıya döner."""
    assert canli["tarihsel_dogrudan"] == [], \
        f"tarihsel yolda doğrudan PIT'siz karar çağrısı: {canli['tarihsel_dogrudan']}"


def test_canli_agacta_BEYANSIZ_dolayli_zincir_YOK(canli):
    """Dolaylı zincirlerin hepsi ya YOK ya da `BILINEN_IHLALLER`de gerekçesiyle beyanlı.
    Beyansız bir zincir, ölçülmemiş bir geriye-dönük önyargı yoludur."""
    assert canli["tarihsel_dolayli_beyansiz"] == [], \
        f"beyansız dolaylı PIT zinciri: {canli['tarihsel_dolayli_beyansiz']}"


def test_BEYANLARIN_hepsi_hala_GERCEK(canli):
    """ÖLÜ BEYAN ÇÜRÜKTÜR (emsal: codelaw.stale_sinks). Bir bilinen ihlal düzeltildiği ya da bir
    koruma kaldırıldığı gün kaydın da düşmesi gerekir; yoksa bir sonraki okuyucu düzeltilmiş bir
    şeyi hâlâ ihlal, ya da kaldırılmış bir korumayı hâlâ koruma sanır."""
    assert canli["curuk_beyan"] == [], \
        f"kodda karşılığı kalmayan beyan: {canli['curuk_beyan']}"
    assert canli["tarihsel_dolayli_beyanli"], \
        "BILINEN_IHLALLER dolu ama kodda tek zincir görülmedi — kayıt mı bayat, tarayıcı mı kör?"


def test_KORUMALI_zincir_ihlal_sayilmaz_ama_RAPORDA_durur(canli):
    """`shadow_variants._judge` `in_blackout`u `if pit:` ile korur — tarihsel turda hiç
    çağrılmaz. Statik tarayıcı koşulu değerlendiremediği için zinciri GÖRÜR; hüküm beyanla
    verilir. Kova ayrı tutulur: `BILINEN_IHLALLER` düzeltilmemiş BORCUN defteridir, bu ise
    ölçülmüş ve KAPATILMIŞ bir yolun kaydı — ikisini karıştırmak düzeltilmiş işi borç
    gibi göstermek olurdu."""
    korumali = canli["tarihsel_dolayli_korumali"]
    assert korumali, "korumalı zincir kaydı dolu ama kodda görülmedi — koruma mı kalktı?"
    moduller = sorted({k["tarihsel_modul"] for k in korumali})
    assert moduller == ["shadow_lifecycle.py"], f"beklenmedik korumalı zincir: {korumali}"
    assert all(k["uclar"] == ["earnings.in_blackout"] for k in korumali), korumali


def test_canli_TABAN_asilmadi(canli):
    """Canlı karar yüzeyindeki PIT'siz çağrı borcu BÜYÜMEDİ."""
    assert not canli["canli_nuks"], (
        f"canlı PIT'siz karar çağrısı tabanı ({pitlaw.CANLI_TABAN}) aşıldı: "
        f"{canli['canli_karar_cagrilari']}")


def test_TABAN_YUKSELTILEMEZ():
    """Taban TEK YÖNLÜDÜR. Kırmızıyı yeşile çevirmenin yolu tabanı büyütmek olsaydı yasa
    kendi kendini gevşetirdi (emsal: codelaw TSX_CAPA_TABANI çivisi)."""
    assert pitlaw.CANLI_TABAN <= 5, (
        f"CANLI_TABAN {pitlaw.CANLI_TABAN}'e yükseltilmiş — taban düşer, YÜKSELMEZ. "
        "Yeni bir PIT'siz canlı kapı bilinçli bir karardır; bu satır değişmeden geçmez.")


def test_KAPSAM_BEYANI_sessiz_degil(canli):
    """Sıfır-ihlal iddiası kapsam bilinmeden okunamaz: rapor neyi göremediğini ADIYLA sayar."""
    assert "gorulmeyen" in canli and "gorulmeyen_by_reason" in canli
    assert set(canli["gorulmeyen_by_reason"]) <= {"dinamik_erisim", "kayitta_yok"}, \
        f"adlandırılmamış körlük sınıfı: {canli['gorulmeyen_by_reason']}"
    assert canli["kayit_boyu"]["karar_etkili"] >= 1, "karar-etkili kayıt boşalmış — yasa vakumda"


def test_canli_agacta_TARANAMAYAN_dosya_yok(canli):
    """Bekçinin kendi körlüğü: taranamayan dosya varsa sıfır-ihlal raporu VAKUMDUR."""
    assert canli["unscanned"] == [], f"taranamayan dosya: {canli['unscanned']}"


def test_rapor_iki_dunyayi_BIRLIKTE_ozetler(canli):
    """`ok` üç hükmün birleşimidir; biri sessizce düşerse `ok` yalancı yeşil olurdu."""
    beklenen = (not canli["tarihsel_dogrudan"] and not canli["tarihsel_dolayli_beyansiz"]
                and not canli["curuk_beyan"]
                and len(canli["canli_karar_cagrilari"]) <= pitlaw.CANLI_TABAN
                and not canli["unscanned"])
    assert canli["ok"] is beklenen, f"ok hükmü bileşenleriyle tutarsız: {canli}"
    assert canli["ok"] is True, (
        f"PIT yasası canlı ağaçta KIRMIZI — tarihsel: {canli['tarihsel_dogrudan']} / "
        f"beyansız: {canli['tarihsel_dolayli_beyansiz']} / çürük: {canli['curuk_beyan']} / "
        f"canlı: {len(canli['canli_karar_cagrilari'])}/{pitlaw.CANLI_TABAN}")
