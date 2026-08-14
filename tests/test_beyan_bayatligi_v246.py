"""test_beyan_bayatligi_v246.py — "BEYANIN KODDAN GERİ KALMASI" SINIFININ ÇİVİLERİ (v246-A).

Bu dosya tek bir kusur sınıfını kovalar: kod değişir, onu anlatan BEYAN (yorum, muafiyet metni,
CLI çıktısı, yapılandırma listesi) olduğu yerde kalır ve hiçbir test kırmızı vermez. Sessizliğin
sebebi hep aynıdır — kapılar beyanın VARLIĞINA bakar, KAYNAKLA UYUŞMASINA değil.

BEŞ KALEM (ROADMAP §2-34a/b, §2-35a/b, §2-38) ve her birinin çivisi:
  A) `pyproject.toml` mutasyon seçimi — kendi türetme kuralına uyuyor mu (kaynak-metin çivisi).
  B) `backtest.py` ölü yereli KALDIRILDI — replay'in sektör kararı DEĞİŞMEDİ (davranış çivisi):
     kural guard'ta TEK, replay onu ÇAĞIRIYOR ve kapı hâlâ ısırıyor.
  C) `codelaw.DECLARED_SINKS["auth.json"]` çapası — VARLIK değil UYUŞMA olarak çivilenir; yazan
     listesi auth.py'den TÜRETİLİR (tamlık), çapa SEMBOLdür (satır numarası bayatlar).
  D) `auth_cli status` iki oturum sayısını da KODDAN türetiyor (sabitler saplanır, çıktı izler).
  E) v245-D ile yanlışlanan iki modül yorumu mezar taşlı: eski cümle DURUYOR, üstüne "artık şöyle"
     yazıldı ve düzeltmenin adlandırdığı mekanizmalar GERÇEKTEN var.

NEDEN "VARLIK DEĞİL UYUŞMA": §2-34a'nın kendisi bu dersin vakasıdır — `auth.json` beyanı
`api.py:420` diyordu, satır 426 olmuştu ve mevcut test yalnız terimlerin geçtiğine baktığı için
sessiz kaldı. Bir çapa, çapaladığı şeyle kıyaslanmıyorsa çapa değildir.
"""
from __future__ import annotations

import ast
import copy
import inspect
import pathlib
import re
import tomllib

import pytest

from meridian import auth, auth_cli, backtest, codelaw, config, guard, ledgerstamp, loop, sermaye
from tests.conftest import make_bars

KOK = pathlib.Path(__file__).resolve().parent.parent
KARAR_CEKIRDEGI = ("broker", "guard", "score")


# ================================================================================================
# A — MUTASYON SEÇİMİ KENDİ KURALINA UYUYOR MU (KALEM 1 · ROADMAP §2-35a)
# ================================================================================================
def _mutmut() -> dict:
    return tomllib.loads((KOK / "pyproject.toml").read_text())["tool"]["mutmut"]


def _pozitif_secim(cfg: dict) -> list[str]:
    """Seçimin POZİTİF bacağı: `--deselect` çiftlerinden ÖNCEKİ dosya listesi (H5 nihai biçim)."""
    poz: list[str] = []
    for o in cfg["pytest_add_cli_args_test_selection"]:
        if o == "--deselect":
            break
        poz.append(o)
    return poz


def _dogrudan_import_edenler() -> dict[str, set[str]]:
    """pyproject'in KENDİ türetme kuralı, mekanik hâli: `tests/*.py` içinde karar çekirdeğini
    DOĞRUDAN import eden dosyalar. Modül düzeyi VE fonksiyon içi sayılır — liste ikisini de
    içeriyor (ör. `test_audit_fixes.py` yalnız fonksiyon içinde import eder ve listededir)."""
    out: dict[str, set[str]] = {}
    for p in sorted((KOK / "tests").glob("*.py")):
        mods: set[str] = set()
        for n in ast.walk(ast.parse(p.read_text())):
            if isinstance(n, ast.ImportFrom):
                m = n.module or ""
                if m == "meridian":
                    mods |= {a.name for a in n.names if a.name in KARAR_CEKIRDEGI}
                elif m.startswith("meridian."):
                    parca = m.split(".")[1]
                    if parca in KARAR_CEKIRDEGI:
                        mods.add(parca)
            elif isinstance(n, ast.Import):
                for a in n.names:
                    if a.name.startswith("meridian."):
                        parca = a.name.split(".")[1]
                        if parca in KARAR_CEKIRDEGI:
                            mods.add(parca)
        if mods:
            out[f"tests/{p.name}"] = mods
    return out


def test_A1_sektor_tavani_civisi_mutasyon_seciminde():
    """WP-15g'nin çivisi seçimde OLMALI: `guard.py` mutasyon kapsamında (`only_mutate`) ve
    `sector_cap_basis` davranışını sınayan TEK dosya bu. Yoksa paydayı yok sayan mutant hayatta
    kalır — v237 de-risk rampası satırı listeye tam bu gerekçeyle girmişti."""
    cfg = _mutmut()
    assert "meridian/guard.py" in cfg["only_mutate"], "kuralın öncülü düştü: guard.py kapsam dışı"
    poz = _pozitif_secim(cfg)
    assert "tests/test_sektor_tavani_ayristirma_v245.py" in poz
    # ve dosya GERÇEKTEN var (silinen/taşınan bir ad seçimi sessizce daraltır)
    assert (KOK / "tests" / "test_sektor_tavani_ayristirma_v245.py").exists()


def test_A2_secimdeki_her_dosya_diskte_duruyor():
    """Öz-testin (ops/haftalik_mutasyon.sh) biçim kapısının suite içindeki karşılığı: seçim bir
    AD LİSTESİDİR ve adlar çürüyebilir. Ritüel haftalık, kırmızı ise BUGÜN görünmeli."""
    for f in _pozitif_secim(_mutmut()):
        assert f.startswith("tests/") and f.endswith(".py"), f"pozitif seçimde yabancı öğe: {f}"
        assert (KOK / f).exists(), f"seçimdeki dosya yok: {f}"


def test_A3_turetme_kurali_MEKANIK_olarak_uygulanabiliyor_ve_sapma_BEYANLI():
    """Kural ile listenin farkı BU TURDA kapatılmadı (kapsam kararı Rol-1'in); kapatılmayan fark
    SESSİZ kalmasın diye pyproject'e ÖLÇÜLMÜŞ ve TARİHLİ bir not düştü. Bu çivi iki şeyi tutar:
    (1) türetme mekanik olarak uygulanabiliyor (kural bir temenni değil, çalıştırılabilir),
    (2) notun ADIYLA saydığı iki alt sınıf hâlâ gerçek — `wf_fixtures.py` kuralı sağlıyor ama
        pytest'in topladığı bir test modülü DEĞİL, yani körlemesine eklenemez."""
    turetilmis = _dogrudan_import_edenler()
    assert len(turetilmis) > len(_pozitif_secim(_mutmut())), \
        "türetme boş/eksik döndü — kural mekanik olarak uygulanamıyorsa liste denetlenemez demektir"
    assert "tests/wf_fixtures.py" in turetilmis, \
        "notun (a) alt sınıfı kayboldu: wf_fixtures artık kuralı sağlamıyor"
    assert "tests/wf_fixtures.py" not in _pozitif_secim(_mutmut()), \
        "test modülü OLMAYAN bir dosya seçime girmiş — kural körlemesine uygulanmış"
    metin = (KOK / "pyproject.toml").read_text()
    assert "SÜRÜKLENME ÖLÇÜLDÜ" in metin, "kural-liste farkı beyansız kaldı (sessiz sürüklenme)"


# ================================================================================================
# B — ÖLÜ YEREL KALDIRILDI, SEKTÖR KARARI DEĞİŞMEDİ (KALEM 2 · ROADMAP §2-35b)
# ================================================================================================
def test_B1_backtest_te_IKINCI_sektor_kurali_YOK():
    """Yapısal çivi (AST — yorumları görmez, yalnız KODU ölçer): `backtest.py` sektör politikasını
    ne okur ne uygular. Mezar taşı yorumu DURUR (tarihçe-koru) ama kod tarafında ad YOKTUR."""
    src = pathlib.Path(inspect.getfile(backtest)).read_text()
    agac = ast.parse(src)
    adlar = {n.id for n in ast.walk(agac) if isinstance(n, ast.Name)}
    assert "max_sector_pct" not in adlar, "ölü yerel geri geldi — ikinci sektör kuralının tohumu"
    sabitler = {n.value for n in ast.walk(agac)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    assert "max_sector_exposure_pct" not in sabitler, \
        "backtest.py sektör tavanı anahtarını KODDA okuyor — ikinci uygulama doğuyor"
    assert "SEKTÖR TAVANI BURADA OKUNMAZ" in src, "mezar taşı silinmiş (tarihçe-koru ihlali)"


def test_B2_eksik_anahtarda_fail_closed_KORUNUYOR():
    """Kaldırılan satırın gözlenebilir TEK yan etkisi KeyError'ın YERİydi. Kapı hâlâ eksik anahtarı
    yutmuyor: `classify_gate` aynı KeyError'ı yükseltir — yani fail-closed kaybolmadı, taşındı."""
    plan = {"ticker": "AAA", "sector": "tech", "size_r": 0.5, "r_multiple_expected": 3.0}
    port = {"open_positions": 0, "sector_counts": {}, "day_pnl_pct": 0.0, "open_risk_r": 0.0}
    reg = {"exposure_budget_pct": 60, "leading_sectors": ["tech"]}
    eksik = {"limits": {"autonomy_level": 1, "max_position_r": 1.0, "max_open_positions": 5,
                        "max_daily_loss_pct": 3.0, "no_trade_before_bars": 2,
                        "kill_switch_file": "state/HALT"}}
    with pytest.raises(KeyError):
        guard.classify_gate(plan, port, reg, eksik)


# --- replay davranış çivisi: aynı barlar, YALNIZ sektör tavanı değişiyor -------------------------
# Hepsi `backtest.SECTORS`ta "tech" — uydurma sembol kullanılmaz (hepsi "?" sektörüne düşerdi ve
# tavan kıyası anlamını yitirirdi). Tohumlar farklı ki adaylar aynı gün YARIŞSIN.
_TEK_SEKTOR = {"AAPL": 11, "MSFT": 23, "NVDA": 37, "AVGO": 41, "AMD": 53, "CRM": 67,
               "ADBE": 71, "ORCL": 83, "INTC": 97, "ENPH": 101}
_N_BARS = 300


def _evren():
    idx = make_bars(_N_BARS, seed=7, trend=0.0006)
    bars = {t: make_bars(_N_BARS, seed=s, breakout_at=_N_BARS - 1) for t, s in _TEK_SEKTOR.items()}
    return bars, idx


def _replay_planlari(bars, idx, pct: float, max_open: int = 5) -> list[dict]:
    goal = copy.deepcopy(config.goal())
    goal["limits"]["max_open_positions"] = max_open
    goal["limits"]["max_sector_exposure_pct"] = pct
    goal["limits"].pop("sector_cap_basis", None)       # payda TÜRETİLSİN (canlı hâl)
    tarihler = [str(d.date()) for d in idx["date"].iloc[-6:]]
    res = backtest.replay(config.default_strategy()["params"], bars, idx, goal,
                          tarihler[0], tarihler[-1], strategy_version=1, with_gate_detail=True)
    return res.plan_log or []


def _sektor_vetosu(plan: dict) -> bool:
    return any("sektör tavanı" in r for r in (plan.get("gate_reasons") or []))


def test_B3_replay_sektor_karari_GUARD_tan_geliyor_ve_ISIRIYOR(sandbox_state):
    """DAVRANIŞ ÇİVİSİ (ölü yerelin kaldırılması kararı DEĞİŞTİRMEDİ). Aynı barlar, aynı params,
    değişen TEK şey `max_sector_exposure_pct` — payda 5 slot, yani fiili isim tavanı
    `floor(5 × pct/100)`:
      · %10  → 0 isim: İLK plan bile sektör gerekçesiyle NO_GO,
      · %40  → 2 isim: ilk iki plan silahlanır, ÜÇÜNCÜSÜ düşer (sayaç birikiyor),
      · %100 → 5 isim: hiçbir planda sektör vetosu yok.
    Üç koşumda da karar ağacında guard'ın `sector_cap` satırı VAR ve `value` alanı sektördeki isim
    sayısını 1→2→3 diye sayar: kararı yazan guard'tır, replay yalnız `sector_counts`u besler.
    BOŞ KÜMEYLE GEÇMEZ: en az üç plan üretilmediyse test kendini düşürür."""
    bars, idx = _evren()
    dar = _replay_planlari(bars, idx, pct=10.0)
    orta = _replay_planlari(bars, idx, pct=40.0)
    genis = _replay_planlari(bars, idx, pct=100.0)

    assert len(dar) >= 3 and len(orta) == len(dar) == len(genis), \
        f"çivi boş/asimetrik kümeyle geçemez: {len(dar)}/{len(orta)}/{len(genis)} plan"
    assert {p["sector"] for p in dar} == {"tech"}, "fikstür tek sektör olmalı (kıyas anlamını yitirir)"
    assert all(_sektor_vetosu(p) and p["gate_verdict"] == "NO_GO" for p in dar), \
        "dar tavanda sektör vetosu düşmedi — replay'de sektör kuralı ÖLÜ"
    assert not any(_sektor_vetosu(p) for p in genis), \
        "geniş tavanda sektör vetosu düştü — kural tavandan bağımsız (sabit) davranıyor"
    # İSİM TAVANI ARİTMETİĞİ: %40 × 5 slot = 2 isim → ilk ikisi geçer, üçüncü düşer.
    assert [_sektor_vetosu(p) for p in orta[:3]] == [False, False, True], \
        f"isim tavanı replay'de sayılmıyor: {[p['gate_verdict'] for p in orta[:3]]}"
    for kume in (dar, orta, genis):
        satirlar = [c for p in kume for c in (p.get("gate_checks") or []) if c["check"] == "sector_cap"]
        assert satirlar, "karar ağacında guard'ın `sector_cap` satırı yok — devir kopmuş"
    # ve sayaç GERÇEKTEN birikiyor (aynı seansta silahlanan her isim paydayı doldurur)
    degerler = [c["value"] for p in orta[:3] for c in p["gate_checks"] if c["check"] == "sector_cap"]
    assert degerler == [1, 2, 3], f"sektör sayacı replay'den guard'a doğru akmıyor: {degerler}"


# ================================================================================================
# C — `auth.json` ÇAPASI: VARLIK DEĞİL UYUŞMA (KALEM 3 · ROADMAP §2-34a)
# ================================================================================================
def _auth_yazan_girisler() -> set[str]:
    """auth.py'de `_write`e ULAŞAN AÇIK girişler (modül-içi çağrı kapanışı). Liste ezberlenmez,
    kaynaktan türetilir: yeni bir yazan yol doğduğunda beyan tamamlanmadan test düşer."""
    kaynak = (KOK / "meridian" / "auth.py").read_text()
    agac = ast.parse(kaynak)
    fonk = {n.name: n for n in ast.walk(agac) if isinstance(n, ast.FunctionDef)}
    cagrilar = {
        ad: {c.func.id for c in ast.walk(n) if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
        for ad, n in fonk.items()
    }
    ulasan = {"_write"}
    for _ in range(len(fonk)):                 # sabit noktaya kadar kapanış
        yeni = {ad for ad, cs in cagrilar.items() if cs & ulasan}
        if yeni <= ulasan:
            break
        ulasan |= yeni
    return {ad for ad in ulasan if not ad.startswith("_")}


def test_C1_capa_SEMBOLDUR_ve_kaynakla_UYUSUYOR():
    """§2-34a'nın kendisi: eski çapa `api.py:420` idi, satır 426 oldu, hiçbir test görmedi. Çapa
    artık SEMBOL (fonksiyon adı + çağrı dizgisi) ve UYUŞMASI ölçülüyor — beyan `api._auth` diyorsa
    api.py'de o fonksiyon VAR ve gövdesinde `auth.verify_session(` GERÇEKTEN çağrılıyor olmalı."""
    beyan = codelaw.DECLARED_SINKS["auth.json"]
    assert "api._auth" in beyan and "auth.verify_session(" in beyan
    api_src = (KOK / "meridian" / "api.py").read_text()
    dugum = next((n for n in ast.walk(ast.parse(api_src))
                  if isinstance(n, ast.FunctionDef) and n.name == "_auth"), None)
    assert dugum is not None, "beyan `api._auth` diyor ama api.py'de böyle bir fonksiyon yok"
    govde = ast.get_source_segment(api_src, dugum) or ""
    assert "auth.verify_session(" in govde, "çapa bayat: `_auth` artık verify_session çağırmıyor"


def test_C2_capada_SATIR_NUMARASI_YOK():
    """Sınıfın kökü: satır numarası gömen çapa, çapaladığı dosyanın HER düzenlemesinde bayatlar ve
    bayatlığı hiçbir yerde görünmez. Bu beyanda `dosya.py:123` biçimi YASAK."""
    assert not re.search(r"\w+\.py:\d+", codelaw.DECLARED_SINKS["auth.json"]), \
        "beyana yeniden satır-numarası çapası girdi (A17 çürüme sınıfı)"


def test_C3_yazan_listesi_TAM_kaynaktan_turetiliyor():
    """Eksik olan `refresh_session`dı ve eksikliği sessizdi. Artık liste TÜRETİLİR: auth.py'de
    `_write`e ulaşan her açık giriş beyanda ADIYLA geçmek zorunda (tamlık çivisi)."""
    beyan = codelaw.DECLARED_SINKS["auth.json"]
    girisler = _auth_yazan_girisler()
    assert {"set_password", "rotate_key", "issue_session", "refresh_session"} <= girisler, \
        f"türetme beklenen yazan yolları bulamadı: {sorted(girisler)}"
    eksik = sorted(ad for ad in girisler if ad not in beyan)
    assert not eksik, f"auth.json beyanı yazan yolları eksik sayıyor: {eksik}"


# ================================================================================================
# D — `auth_cli status` İKİ SAYIYI DA KODDAN TÜRETİYOR (KALEM 4 · ROADMAP §2-34b)
# ================================================================================================
def test_D1_status_oturum_omru_KODDAN_turetiyor(sandbox_state, monkeypatch, capsys):
    """Sabitler saplanır, çıktı İZLEMELİ. Metne gömülü bir "12 saat" bu testte hayatta kalamaz —
    beyanın koddan geri kalması tam olarak böyle başlamıştı."""
    monkeypatch.delenv("MERIDIAN_BIND_HOST", raising=False)
    monkeypatch.setattr(auth, "SESSION_TTL_S", 3 * 3600)
    monkeypatch.setattr(auth, "SESSION_ABSOLUTE_MAX_S", 2 * 86400)
    assert auth_cli._status() == 0
    cikti = capsys.readouterr().out
    assert "3 saat" in cikti and "2 gün" in cikti, f"sayılar koddan türemiyor:\n{cikti}"
    assert "12 saat" not in cikti and "7 gün" not in cikti, "eski sayılar metne gömülü kalmış"
    assert "KAYAN" in cikti and "mutlak tavan" in cikti, \
        "beyan eksik: kayan pencere ve mutlak tavan İKİSİ birden söylenmeli"


def test_D2_gercek_sabitlerle_bugunku_beyan(sandbox_state, monkeypatch, capsys):
    """Ve saplanmamış hâlde çıktı BUGÜNKÜ yasayı söylüyor (12 saat kayan + 7 gün tavan)."""
    monkeypatch.delenv("MERIDIAN_BIND_HOST", raising=False)
    assert auth_cli._status() == 0
    cikti = capsys.readouterr().out
    assert f"{auth.SESSION_TTL_S // 3600} saat" in cikti
    assert f"{auth.SESSION_ABSOLUTE_MAX_S // 86400} gün" in cikti


# ================================================================================================
# E — v245-D İLE YANLIŞLANAN İKİ YORUM (KALEM 5 · ROADMAP §2-38)
# ================================================================================================
def test_E1_run_py_yorumu_MEZAR_TASLI_duzeltilmis():
    """TARİHÇE-KORU: eski cümle SİLİNMEZ, üstüne "artık şöyle" yazılır ve düzeltme yeni mekanizmayı
    ADIYLA gösterir (`loop._persist_equity_point`)."""
    src = (KOK / "meridian" / "run.py").read_text()
    blok = src[src.index("KAYNAK DAMGASI (BT-1"):]
    blok = blok[:blok.index("with store.file_lock(\"trades.jsonl\")")]
    assert "tam olarak o çiftten ölçer" in blok, "eski cümle silinmiş (tarihçe-koru ihlali)"
    assert "ARTIK BÖYLE DEĞİL" in blok, "yanlışlanan cümlenin üstüne düzeltme yazılmamış"
    assert "_persist_equity_point" in blok and "seed_boundary" in blok


def test_E2_sermaye_docstringi_MEZAR_TASLI_duzeltilmis():
    assert sermaye.__doc__ is not None
    d = sermaye.__doc__
    assert "NOKTASININ TARİHİNDEN okur" in d, "eski cümle silinmiş (tarihçe-koru ihlali)"
    assert "YANLIŞLANDI" in d and "_persist_equity_point" in d


def test_E3_duzeltmenin_ADLANDIRDIGI_mekanizmalar_gercek():
    """Düzeltmenin kendisi de bayatlayabilir: adı geçen iki mekanizma GERÇEKTEN var mı? Biri
    yeniden adlandırılırsa bu çivi düşer ve yorum aynı gün güncellenir (uyuşma disiplini)."""
    assert callable(getattr(loop, "_persist_equity_point", None))
    assert callable(getattr(ledgerstamp, "seed_boundary", None))
    # ve sınırın son noktadan OKUNMADIĞI iddiası kaynakta karşılığını buluyor
    kaynak = inspect.getsource(ledgerstamp.seed_boundary)
    assert "SINIRI BELİRLEMEZ" in kaynak, \
        "seed_boundary artık 'son nokta sınırı belirlemez' demiyor — iki yorum yeniden yanlış olabilir"


def test_E4_sermaye_nin_IKINCI_capasi_da_SEMBOL_ve_uyusuyor():
    """A17'nin aynı dosyadaki ikinci vakası (bu turda ÖLÇÜLDÜ): docstring `broker.py:263` diyordu,
    o satır bugün de-risk rampasına ait — `PaperBroker.equity` 429'a kaymıştı. Çapa sembol+dizgi
    oldu; uyuşma burada ölçülür, satır numarası bir daha bayatlayamaz."""
    from meridian.broker import PaperBroker
    d = sermaye.__doc__ or ""
    assert "PaperBroker.equity" in d and "broker.py:263" in d, \
        "çapa ya sembolleşmemiş ya da vaka kaydı silinmiş (tarihçe-koru)"
    assert "eq = self.start_equity + self.realized_pnl" in inspect.getsource(PaperBroker.equity), \
        "çapa bayat: `PaperBroker.equity` artık bu satırı taşımıyor"
