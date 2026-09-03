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

BİLİNEN İHLAL VARDI ve 2026-08-31'de KAPANDI (EDG-2026-062). `backtest.py` ve `cf_backfill.py`
`earnings.in_blackout`u bilerek kesmişti ama AYNI dosyadaki `strat.scan_entry`/`scan_all` çağrısı
aynı PIT'siz takvimi tarihsel seansa sokuyordu. Kaydın kendi yazdığı iki çıkıştan İKİNCİSİ
uygulandı ("PIT arşivine bağlanır"): çapa artık `params["earnings.pit_arsiv"]` ile `earnings_pit`e
SEVK EDİLİYOR, iki kayıt `BILINEN_IHLALLER`den `PIT_KORUMALI_ZINCIRLER`e TAŞINDI ve borç defteri
BOŞALDI. `test_BEYANLARIN_hepsi_hala_GERCEK` beklentiyi kayıttan TÜRETİR (iki yön de bağlı),
`test_PIT_SEVKI_capa_blogunda_DURUYOR` ise korumanın kendisini bağlar — çünkü zincir tarayıcısı
sevki GÖREMEZ ve görebilen bir çivi olmadan taşınan kayıtlar kendi kendini doğrulayan beyan olurdu.

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
    """`"backtest.py" + ":5"` birleşimi → `"backtest.py"`. Çağrı yerini ADIYLA sınamak için;
    beklenen değeri dosya-adı:satır-numarası tam biçiminde yazmak bu dosyada SAHTE BİR SATIR
    ÇAPASI doğururdu (bkz. ilk pozitif kontrol)."""
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
    # ÇAPA DOĞURMA: beklenen değer `"backtest.py" + ":5"` (dosya-adı:satır-numarası) biçiminde
    # YAZILMAZ. O dizge codelaw'ın
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
    # KORUMALI ZİNCİRLER ALANLI KAYITTIR (`gerekce` + `civi`): `str(kayit)` ile ölçmek sözlüğün
    # kendi gösterimini sayardı, yani gerekçe BOŞKEN bile eşiği geçerdi — sessiz muafiyet.
    kisa += [k for k, g in pitlaw.PIT_KORUMALI_ZINCIRLER.items()
             if len(str(g.get("gerekce", "")).strip()) < 20]
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
# C2) SEVK ÇÜRÜMESİ — "koruma kalkarsa kayıt çürür" cümlesinin MEKANİK karşılığı
# ---------------------------------------------------------------------------
# `PIT_KORUMALI_ZINCIRLER`in iki yeni kaydı (backtest.py, cf_backfill.py) bir KORUMAYA dayanır:
# `strategy.py`nin iki kazanç-çapalı değerlendiricisi çapayı `params.get("earnings.pit_arsiv")`
# ile SEVK EDER — param varken PIT arşivi (`earnings_pit`), yokken canlı `earnings.days_since_
# report`. Statik zincir tarayıcısı bu koşulu DEĞERLENDİREMEZ (`dolayli_zincirler` sevk dursa da
# kalksa da AYNI zinciri görür), yani beyanın kendisi ölçülmeden duramaz: sevk bir gün sessizce
# kaldırılırsa tarihsel yol PIT'siz takvime döner ve rapor bunu KORUMALI diye yazmaya devam
# ederdi. Aşağıdaki iki çivi o boşluğu kapatır — biri sevkin VARLIĞINI, öteki sevkin
# YÖNLENDİRDİĞİ kaynağın PIT kaydında olmasını bağlar.
_SEVK_ANAHTARI = "earnings.pit_arsiv"


def _sevk_blogu(fn_adi: str):
    """`strategy.<fn_adi>` gövdesinde `params.get("earnings.pit_arsiv")` testini taşıyan `if`
    düğümü (yoksa None). Kaynak AST'den okunur, metinden DEĞİL: bir yorum satırında geçen anahtar
    adı sevk sayılmamalıdır (`pitlaw._anilan_adlar`ın aynı gerekçesi)."""
    import inspect

    from meridian import strategy
    tree = ast.parse(textwrap.dedent(inspect.getsource(getattr(strategy, fn_adi))))
    for n in ast.walk(tree):
        if not isinstance(n, ast.If):
            continue
        for c in ast.walk(n.test):
            if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) \
                    and c.func.attr == "get" \
                    and any(isinstance(a, ast.Constant) and a.value == _SEVK_ANAHTARI
                            for a in c.args):
                return n
    return None


def _ad(cagri: ast.Call) -> tuple[str | None, str] | None:
    """`earnings_pit.days_since_report_pit(...)` → `("earnings_pit", "days_since_report_pit")`;
    nitelenmemiş `f(...)` → `(None, "f")`; çözülemeyen biçim → None."""
    if isinstance(cagri.func, ast.Attribute):
        return (cagri.func.value.id if isinstance(cagri.func.value, ast.Name) else None,
                cagri.func.attr)
    if isinstance(cagri.func, ast.Name):
        return (None, cagri.func.id)
    return None


def _cagrilar(dugumler: list) -> list[tuple[str | None, str]]:
    """Bu daldaki TÜM çağrılar. Varlık yüklemleri için yeterli, KAYIT yüklemleri için DEĞİL —
    onlar `_capa_cagrilari` kullanır (gerekçe orada)."""
    return [a for st in dugumler for n in ast.walk(st)
            if isinstance(n, ast.Call) and (a := _ad(n)) is not None]


def _capa_cagrilari(dugumler: list) -> list[tuple[str | None, str]]:
    """ÇAPA SINIFI: bu dalda bir KARAR TESTİNE (`if`/`while`) giren çağrılar.

    SINIF TANIMI, DIŞLAMA LİSTESİ DEĞİL — ve fark ölçülmüş bir kırılganlığı kapatıyor. Yüklem
    eskiden "PIT dalındaki HER nitelenmiş çağrı `PIT_KAYNAKLAR`ta olmalı" diyordu; o hâlde dala
    bir gün bir `obs.log(...)`, bir sayaç artışı ya da bir `pd.isna(...)` eklendiği an çivi
    kırmızıya döner ve mesajı YANLIŞ TEŞHİS verirdi ("sevkin yönlendirdiği kaynak kayıtta yok").
    Bir dışlama listesi (`{"log", "isna", ...}`) aynı kusuru erteler: liste, yazılmamış her yeni
    yardımcı çağrı için bayat doğar. Ölçüt bunun yerine ROLDÜR: bu turda çapayı belirleyen çağrı,
    sonucu kurulumun ateşleyip ateşlemeyeceğine karar veren çağrıdır — `pitlaw`ın kendi sınıf
    türetiminin (`_testte_gecer`) ölçütüyle aynı ölçüt.

    İKİ BİÇİM DE SAYILIR (`pitlaw._tohumlar` emsali): çağrı doğrudan testin içinde
    (`if not earnings_pit.days_since_report_pit(...)`) ya da sonucu bir ada atanmış ve O AD testte
    geçiyor (`x = ...pit(...)` → `if not x:`). İkincisini saymamak, çiviyi bir yeniden yazımla
    sessizce boşa düşürürdü."""
    out: list[tuple[str | None, str]] = []
    for st in dugumler:
        for n in ast.walk(st):
            if not isinstance(n, (ast.If, ast.While)):
                continue
            for c in ast.walk(n.test):                       # (1) doğrudan testteki çağrı
                if isinstance(c, ast.Call) and (a := _ad(c)) is not None:
                    out.append(a)
            adlar = {m.id for m in ast.walk(n.test) if isinstance(m, ast.Name)}
            for st2 in dugumler:                             # (2) teste giren ada atanan çağrı
                for asg in ast.walk(st2):
                    if isinstance(asg, (ast.Assign, ast.AnnAssign)) \
                            and isinstance(getattr(asg, "value", None), ast.Call) \
                            and {t.id for t in ast.walk(asg)
                                 if isinstance(t, ast.Name) and isinstance(t.ctx, ast.Store)} & adlar \
                            and (a := _ad(asg.value)) is not None:
                        out.append(a)
    return out


def _capali_degerlendiriciler() -> list[str]:
    """Kazanç-çapalı değerlendiricilerin TEK kaydı `arming.PIT_CAPALI_KURULUMLAR`tır (çivi v301
    onu iki yönlü bağlar). Burada ikinci bir liste yazmak, aynı gerçeğin sessizce ayrışan bir
    kopyasını doğururdu (tek-kaynak yasası)."""
    from meridian import arming
    return [f"evaluate_{s}" for s in sorted(arming.PIT_CAPALI_KURULUMLAR)]


def test_PIT_capali_degerlendirici_kaydi_BOS_DEGIL():
    """Aşağıdaki iki çivi kaydı gezer; kayıt boşalırsa ikisi de SESSİZCE yeşil olurdu."""
    assert _capali_degerlendiriciler(), \
        "arming.PIT_CAPALI_KURULUMLAR boş — sevk çivileri hiçbir şeyi koruMUYOR"


@pytest.mark.parametrize("fn_adi", _capali_degerlendiriciler())
def test_PIT_SEVKI_capa_blogunda_DURUYOR(fn_adi):
    """KORUMANIN KENDİSİ. Sevk kaldırılırsa `backtest.py`/`cf_backfill.py` kayıtları ÇÜRÜR:
    tarihsel yol yeniden `state/earnings.csv`e (bugünün ileri-pencere önbelleği) döner ve
    `PIT_KORUMALI_ZINCIRLER`in gerekçesi yalan olur. İKİ DAL DA ölçülür — param varken PIT,
    yokken canlı: yalnız `if` dalına bakan bir çivi, canlı dalın sessizce PIT'e çevrilmesini de
    (canlı taban ölçümünü boşa düşürerek) kaçırırdı."""
    blok = _sevk_blogu(fn_adi)
    assert blok is not None, (
        f"strategy.{fn_adi} içinde `params.get(\"{_SEVK_ANAHTARI}\")` sevki YOK — "
        "pitlaw.PIT_KORUMALI_ZINCIRLER'in backtest.py/cf_backfill.py kayıtları ÇÜRÜDÜ: "
        "korumasız zincir BORÇTUR (BILINEN_IHLALLER), kapatılmış yol değil")
    assert ("earnings_pit", "days_since_report_pit") in _capa_cagrilari(blok.body), (
        f"strategy.{fn_adi}: sevk dalının ÇAPASI PIT arşivi DEĞİL — dalın karar testine giren "
        f"çağrılar: {_capa_cagrilari(blok.body)}")
    assert ("earnings_pit", "days_since_report_pit") not in _capa_cagrilari(blok.orelse), (
        f"strategy.{fn_adi}: param YOKKEN de PIT arşivi soruluyor — canlı yol sessizce PIT'e "
        "çevrilmiş: canlı taban ölçümü (CANLI_TABAN) o an anlamını yitirir")
    assert any(fn == "days_since_report" for _sahip, fn in _capa_cagrilari(blok.orelse)), (
        f"strategy.{fn_adi}: param YOKKEN canlı çapa çağrılmıyor — canlı yol sessizce "
        f"değişmiş olabilir: {_capa_cagrilari(blok.orelse)}")


@pytest.mark.parametrize("fn_adi", _capali_degerlendiriciler())
def test_SEVKIN_YONLENDIRDIGI_KAYNAK_PIT_KAYDINDA(fn_adi):
    """Sevk bir kaynağa YÖNLENDİRİR ve o kaynak yasanın kaydında OLMALIDIR. Kayıtsız kalırsa
    `pitlaw` onun hakkında hiçbir hüküm taşımaz: ne PIT sözleşmeli beyaz listede, ne PIT'siz
    kaynak defterinde — yani "tarihsel yol artık PIT" cümlesinin arkasında ölçülmüş hiçbir şey
    kalmaz. Hedef kaynak KAYNAKTAN okunur, elle yazılmaz."""
    blok = _sevk_blogu(fn_adi)
    assert blok is not None, f"sevk bloğu yok: strategy.{fn_adi}"
    hedefler = [(sahip, fn) for sahip, fn in _capa_cagrilari(blok.body) if sahip]
    assert hedefler, (
        f"sevk dalının karar testine giren nitelenmiş çağrı YOK: strategy.{fn_adi} — çapa artık "
        "bir teste girmiyorsa kurulumun ateşleme kararı başka bir yerden veriliyor demektir")
    kayitsiz = [h for h in hedefler if h not in pitlaw.PIT_KAYNAKLAR]
    assert kayitsiz == [], (
        f"sevkin yönlendirdiği kaynak pitlaw.PIT_KAYNAKLAR'da YOK: {kayitsiz} — "
        "PIT beyanı kayıtsızdır, yasa o kaynak hakkında hiçbir şey söylemiyor")


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
    şeyi hâlâ ihlal, ya da kaldırılmış bir korumayı hâlâ koruma sanır.

    İKİ DEFTERİN İKİ AYRI HÜKMÜ ve beklenti KAYITTAN TÜRETİLİR (tek-kaynak yasası): borç defteri
    BOŞSA raporda beyanlı zincir de OLMAMALIDIR. Sabit bir "beyanlı zincir vardır" beklentisi,
    borç kapandığı gün doğru işi kırmızıya çevirirdi (EDG-2026-062: iki kayıt `PIT_KORUMALI_
    ZINCIRLER`e taşındı ve `BILINEN_IHLALLER` boşaldı)."""
    assert canli["curuk_beyan"] == [], \
        f"kodda karşılığı kalmayan beyan: {canli['curuk_beyan']}"
    if pitlaw.BILINEN_IHLALLER:
        assert canli["tarihsel_dolayli_beyanli"], (
            "BILINEN_IHLALLER dolu ama kodda tek zincir görülmedi — kayıt mı bayat, "
            "tarayıcı mı kör?")
    else:
        assert canli["tarihsel_dolayli_beyanli"] == [], (
            "BILINEN_IHLALLER BOŞ ama rapor beyanlı zincir gösteriyor — iki defter ayrıştı: "
            f"{canli['tarihsel_dolayli_beyanli']}")


def test_HER_KORUMALI_KAYIT_bir_CIVI_ADI_TASIR(canli):
    """YAPI BOŞLUĞU KAPANDI (düzeltme turu 1). Bugüne kadar üç kaydın üçünün de bir çürüme
    çivisi olması bir GELENEKTİ: `rapor()` korumanın var olup olmadığını hiç sormuyordu, yani
    dördüncü bir kayıt hiçbir çivi talep etmeden doğabilir ve doğduğu gün kendi kendini
    doğrulayan bir beyan olurdu. Emsal `KAPI_SOZLESMELERI`/`SINYAL_SOZLESMELERI` denetimidir —
    "kayıtsız yüzey doğduğu gün çivi öter" disiplini artık bu deftere de uygulanıyor."""
    assert canli["korumali_civi_curuk"] == [], (
        f"korumalı zincir kaydı çürük çivi ADI taşıyor: {canli['korumali_civi_curuk']} — "
        "kayıt, korumasını çürütebilen bir çiviye bağlı DEĞİL")
    assert set(canli["korumali_civiler"]) == set(canli["korumali_zincirler"]), \
        "her korumalı kaydın bir çivi alanı olmalı (kayıt kümesi ile çivi kümesi ayrıştı)"
    assert all(canli["korumali_civiler"].values()), \
        f"çivi adı BOŞ olan kayıt(lar): {canli['korumali_civiler']}"


def test_IKI_DEFTER_AYRIK(canli):
    """BORÇ DEFTERİ ile KAPATILMIŞ YOL DEFTERİ aynı anahtarı TAŞIYAMAZ.

    `rapor()` bir zinciri önce `PIT_KORUMALI_ZINCIRLER`de arar; aynı anahtar `BILINEN_IHLALLER`de
    de dururken zincir korumalı kovaya düşer ve borç kaydı `gorulen` kümesine ORTAK ANAHTAR
    üzerinden girdiği için ÇÜRÜK de sayılmaz — yani ölü bir borç kaydı sessizce yaşardı. Ayrım bu
    turda taşımayla kuruldu (EDG-2026-062); çakışma sessiz kalmasın."""
    ortak = sorted(set(pitlaw.BILINEN_IHLALLER) & set(pitlaw.PIT_KORUMALI_ZINCIRLER))
    assert ortak == [], (
        f"aynı anahtar iki defterde birden: {ortak} — biri ölü kayıttır ve çürüme denetimi "
        "onu göremez")


def test_KORUMALI_zincir_ihlal_sayilmaz_ama_RAPORDA_durur(canli):
    """Koşul-korumalı zincirler: tarayıcı zinciri GÖRÜR (koşulu değerlendiremez), hüküm beyanla
    verilir. Kova ayrı tutulur: `BILINEN_IHLALLER` düzeltilmemiş BORCUN defteridir, bu ise
    ölçülmüş ve KAPATILMIŞ bir yolun kaydı — ikisini karıştırmak düzeltilmiş işi borç gibi
    göstermek olurdu.

    Bugün ÜÇ kayıt, İKİ ayrı koruma biçimi:
      · `shadow_lifecycle → shadow_variants._judge` — `in_blackout` `if pit:` ile korunur.
      · `backtest` / `cf_backfill` → `strategy` — çapa `earnings.pit_arsiv` paramıyla PIT
        arşivine SEVK EDİLİR (EDG-2026-062). Sevkin varlığı ayrıca ve MEKANİK çivilidir
        (`test_PIT_SEVKI_capa_blogunda_DURUYOR`): kayıt "koruma kalkarsa çürür" diyor, o cümlenin
        karşılığı bu iki çividir.

    Modül kümesi KAYITTAN türetilir (tek-kaynak) — iki yön birden: raporda görünen her korumalı
    modül kayıtta, kayıttaki her modül raporda."""
    korumali = canli["tarihsel_dolayli_korumali"]
    assert korumali, "korumalı zincir kaydı dolu ama kodda görülmedi — koruma mı kalktı?"
    assert {k["tarihsel_modul"] for k in korumali} \
        == {m for (m, _mk, _fn) in pitlaw.PIT_KORUMALI_ZINCIRLER}, \
        f"korumalı kayıt ile rapor ayrıştı: {korumali}"
    uclar: dict[str, set[str]] = {}
    for k in korumali:
        uclar.setdefault(k["tarihsel_modul"], set()).update(k["uclar"])
    assert uclar == {"shadow_lifecycle.py": {"earnings.in_blackout"},
                     "backtest.py": {"earnings.days_since_report"},
                     "cf_backfill.py": {"earnings.days_since_report"}}, \
        f"korumalı zincirlerin uçları beklenenden farklı: {uclar}"


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
                and not canli["curuk_beyan"] and not canli["korumali_civi_curuk"]
                and len(canli["canli_karar_cagrilari"]) <= pitlaw.CANLI_TABAN
                and not canli["unscanned"])
    assert canli["ok"] is beklenen, f"ok hükmü bileşenleriyle tutarsız: {canli}"
    assert canli["ok"] is True, (
        f"PIT yasası canlı ağaçta KIRMIZI — tarihsel: {canli['tarihsel_dogrudan']} / "
        f"beyansız: {canli['tarihsel_dolayli_beyansiz']} / çürük: {canli['curuk_beyan']} / "
        f"canlı: {len(canli['canli_karar_cagrilari'])}/{pitlaw.CANLI_TABAN}")
