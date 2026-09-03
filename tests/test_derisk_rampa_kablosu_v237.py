"""test_derisk_rampa_kablosu_v237.py — OPT Faz-1'in İLK kalemi: de-risk rampasının goal-kablosu.

NEDEN VAR — ADI KONMUŞ SINIFIN İKİNCİ ÖRNEĞİ. `guard.py`nin C24 yorumu (2026-08-02) sınıfı adıyla
kaydetmişti: "canlı defterde plan kesen bir risk eşiği HİÇBİR yönetişim yüzeyinde görünmüyordu
(adı konmuş sınıfın ikinci örneği: `broker.max_positions_at` rampası)". İki hafta boyunca o ikinci
örnek yerinde durdu: `derisk_mult`in 0,03 / 0,08 eşikleri FONKSİYON GÖVDESİNDEYDİ — ne operatörün
değişmez zarfında (goal.yaml) ne arama uzayında (bounds.yaml). Sonucu ölçümde görüldü: EDG-2026-023
ve EDG-2026-026 bandı ancak MONKEYPATCH ile oynatabildi
(research/olcumler/edg026_slot20_2026-08-12/olcum.py::_rampa_fn).

BU TURDA NE OLDU (2026-08-12): eşikler `goal.yaml` → `limits.derisk_full_dd` /
`limits.derisk_floor_dd`ye taşındı, tek okuyucu `broker.derisk_ramp()`. Operatör kararı (karar
penceresi §E.1/§E.3) bandı 0,15 / 0,36'ya aldı ve MOD AYRIMI YOK dedi: kâğıt ile gerçek-para
BİREBİR aynı rampayı koşar, eski 3/8'e giden bir kod-yolu bırakılmadı.

DÖRT ÇİVİ:
  1. KABLO OKUNUYOR — goal.yaml'daki değer davranışı GERÇEKTEN değiştiriyor (yoksa "taşıdık" bir
     iddia olurdu; kablo bağlanmamış bir parametre en tehlikeli yalancı düğmedir).
  2. FAIL-SAFE = BENİMSENEN BANT — dosya/anahtar yoksa 0,15/0,36'ya düşer, eski 3/8'e DEĞİL.
  3. TEK RAMPA, MOD'DAN BAĞIMSIZ — `config.MODE`/`live_enabled` ne olursa olsun aynı sayı.
  4. 026 SEMANTİK AYNASI — kablolu fonksiyon, ölçümün monkeypatch'lediği fonksiyonla BİREBİR aynı
     sayıları veriyor (ölçülen dünya ile kablolanan dünya ayrışmışsa 026/032 damgası anlamsızdır).
"""
from __future__ import annotations

import pytest

from meridian import broker, config, guard


# =================================================================================================
# ÇİVİ 1 — KABLO GERÇEKTEN OKUNUYOR
# =================================================================================================
def test_rampa_goal_yamlden_okunur_ve_DAVRANISI_degistirir():
    """Yürürlükteki bant goal.yaml'dan gelir ve `derisk_mult` onu kullanır. `override` yolu,
    dosyaya dokunmadan (değişmez dosya) kablonun canlı olduğunu ispatlar."""
    lim = config.goal()["limits"]
    assert broker.derisk_ramp()["full_dd"] == float(lim["derisk_full_dd"])
    assert broker.derisk_ramp()["floor_dd"] == float(lim["derisk_floor_dd"])

    dar = broker.derisk_ramp({"derisk_full_dd": 0.03, "derisk_floor_dd": 0.08})
    assert (dar["full_dd"], dar["floor_dd"]) == (0.03, 0.08)
    # AYNI girdi, İKİ bant → İKİ FARKLI çarpan. Kablo bağlı olmasaydı ikisi eşit çıkardı.
    assert broker.derisk_mult(94.0, 100.0, dar) == pytest.approx(0.4, abs=1e-9)   # eski 3/8 dünyası
    assert broker.derisk_mult(94.0, 100.0) == 1.0                                 # bugünkü 15/36


def test_kaynak_alani_dogruyu_soyler():
    """"0,15 nereden geldi?" sorusu TAHMİNLE cevaplanmaz (config.live_expectancy_rule emsali)."""
    assert broker.derisk_ramp()["kaynak"] == {"full_dd": "goal.yaml", "floor_dd": "goal.yaml"}
    assert broker.derisk_ramp({})["kaynak"] == {"full_dd": "kod varsayilani",
                                                "floor_dd": "kod varsayilani"}


def test_max_positions_at_ayni_bandi_gorur():
    """Çarpan tek başına kalmaz: eşzamanlı pozisyon tavanı aynı banttan türer (026 öz-sınaması
    research/olcumler/edg026_slot20_2026-08-12/olcum.py::kosum — 5 tabanında 4, 20 tabanında 15)."""
    assert broker.max_positions_at(80.0, 100.0, 5) == 4
    assert broker.max_positions_at(80.0, 100.0, 20) == 15
    dar = {"full_dd": 0.03, "floor_dd": 0.08}
    assert broker.max_positions_at(80.0, 100.0, 20, dar) == 0     # eski bantta %20 dd zaten taban


# =================================================================================================
# ÇİVİ 2 — FAIL-SAFE: BENİMSENEN BANT (eski 3/8 DEĞİL)
# =================================================================================================
def test_param_yoksa_fail_safe_benimsenen_banttir():
    assert (broker.DERISK_FULL_DD, broker.DERISK_FLOOR_DD) == (0.15, 0.36)
    bos = broker.derisk_ramp({})
    assert (bos["full_dd"], bos["floor_dd"]) == (0.15, 0.36)
    assert broker.derisk_mult(80.0, 100.0, bos) == 0.7619


def test_goal_okunamazsa_rampa_YOK_olmaz(monkeypatch):
    """Yapılandırma patlarsa yasa ortadan kalkmaz — benimsenen banda düşer (YASA 4: sessiz-yutma
    damgalı ve gerekçeli; düşüş `kaynak` alanından okunur)."""
    def _patla():
        raise RuntimeError("goal.yaml okunamadı")

    monkeypatch.setattr(config, "goal", _patla)
    r = broker.derisk_ramp()
    assert (r["full_dd"], r["floor_dd"]) == (0.15, 0.36)
    assert r["kaynak"] == {"full_dd": "kod varsayilani", "floor_dd": "kod varsayilani"}
    assert broker.derisk_mult(64.0, 100.0) == 0.0            # kablo düşse de taban ÇALIŞIR


@pytest.mark.parametrize("bozuk", [
    {"derisk_full_dd": "abc"},                                  # sayı değil
    {"derisk_full_dd": -0.1},                                   # negatif
    {"derisk_full_dd": 0.40, "derisk_floor_dd": 0.20},          # TERS bant
    {"derisk_full_dd": 0.20, "derisk_floor_dd": 0.20},          # sıfır genişlik → sıçrama fonksiyonu
    {"derisk_floor_dd": 1.5},                                   # aralık dışı
])
def test_bozuk_deger_SESSIZCE_gecmez_ikisi_birden_varsayilana_doner(bozuk):
    """KELEPÇE (`entry_law` deseni): yarısı dosyadan yarısı koddan bir rampa, hiç olmayan rampadan
    tehlikelidir. `full_dd >= floor_dd` olduğu an çarpan bir SIÇRAMA fonksiyonuna dönerdi (tam
    boydan sıfıra, ara bant yok) — bu hiç kimsenin verdiği bir karar değildir."""
    r = broker.derisk_ramp(bozuk)
    assert (r["full_dd"], r["floor_dd"]) == (0.15, 0.36)
    assert r["kaynak"] == {"full_dd": "kod varsayilani", "floor_dd": "kod varsayilani"}


def test_tek_ucu_verilen_bant_digerini_varsayilandan_alir():
    """Kısmi yapılandırma meşrudur (bant hâlâ geçerli); hangi ucun nereden geldiği BEYAN edilir."""
    r = broker.derisk_ramp({"derisk_floor_dd": 0.40})
    assert (r["full_dd"], r["floor_dd"]) == (0.15, 0.40)
    assert r["kaynak"] == {"full_dd": "kod varsayilani", "floor_dd": "goal.yaml"}


# =================================================================================================
# ÇİVİ 3 — TEK RAMPA HER MODDA (operatör kararı §E.3: "gerçek para'yı da birebir aynı yap")
# =================================================================================================
@pytest.mark.parametrize("mode,risk", [("paper", False), ("live", True), ("live", False)])
def test_mod_dallanmasi_YOK(monkeypatch, mode, risk):
    """Rol-1'in "gerçek-para 3/8 SABİT kalsın" önerisi operatör kararıyla AŞILDI. Bu çivi o kararı
    YAPISAL kılar: mod bir girdi DEĞİLDİR — `derisk_mult`/`derisk_ramp` imzasında mod yok, ve
    modu değiştirmek sayıyı değiştirmez."""
    monkeypatch.setattr(config, "MODE", mode)
    monkeypatch.setattr(config, "I_ACCEPT_RISK", risk)
    assert broker.derisk_ramp()["floor_dd"] == 0.36
    assert broker.derisk_mult(80.0, 100.0) == 0.7619
    assert broker.max_positions_at(80.0, 100.0, 20) == 15


def test_kaynakta_mod_kosullu_rampa_yolu_YOK():
    """YAPISAL ikinci hat: yarın biri `if live_enabled(): ...` ile ikinci bir bant eklerse
    davranış testi o kolu görmeyebilir (mod kapalı koşuyoruz). AST taraması görür.

    METİN taraması DEĞİL AST: bu dosyaların gerekçe blokları eski bandı (0,03/0,08) tarihçe olarak
    ANLATIYOR ve anlatmalı. Bir yorumun içindeki sayı bir kod-yolu değildir; metin taraması tam da
    tarihçe-koruma yasasını cezalandırırdı (test_sadelestirme_v123'ün AST gerekçesiyle aynı sınıf)."""
    import ast
    import inspect
    import textwrap
    isimler: set[str] = set()
    sayilar: set[float] = set()
    for fn in (broker.derisk_ramp, broker.derisk_mult, broker.max_positions_at):
        agac = ast.parse(textwrap.dedent(inspect.getsource(fn)))
        for d in ast.walk(agac):
            if isinstance(d, ast.Name):
                isimler.add(d.id)
            elif isinstance(d, ast.Attribute):
                isimler.add(d.attr)
            elif isinstance(d, ast.Constant) and isinstance(d.value, (int, float)) \
                    and not isinstance(d.value, bool):
                sayilar.add(float(d.value))
    for yasak in ("live_enabled", "MODE", "I_ACCEPT_RISK"):
        assert yasak not in isimler, f"rampa gövdesinde mod dallanması izi: {yasak}"
    assert not ({0.03, 0.08} & sayilar), "eski 3/8 bandı kodda hâlâ bir sabit olarak yaşıyor"


# =================================================================================================
# ÇİVİ 4 — 026 SEMANTİK AYNASI (ölçülen dünya == kablolanan dünya)
# =================================================================================================
def _olcum_rampasi(tam_dd: float, sifir_dd: float):
    """research/olcumler/edg026_slot20_2026-08-12/olcum.py::_rampa_fn — BİREBİR KOPYA.
    Kasıtlı ikiz: ölçümün koştuğu fonksiyon dondurulmuş bir dosyada yaşıyor ve oradan import
    edilemez (ölçüm sandbox'ı repo modülü değildir). Kopyanın işi, kablonun o dosyadan SAPMASINI
    yakalamaktır — ikisi ayrışırsa 026/032'nin damgaladığı sayılar bugünkü motoru anlatmaz."""
    def derisk_mult_param(equity: float, peak: float) -> float:
        if peak <= 0:
            return 1.0
        dd = (peak - equity) / peak
        if dd <= tam_dd:
            return 1.0
        if dd >= sifir_dd:
            return 0.0
        return round(1.0 - (dd - tam_dd) / (sifir_dd - tam_dd), 4)
    return derisk_mult_param


def test_026_oz_sinamasinin_UC_NOKTASI_birebir():
    """research/olcumler/edg026_slot20_2026-08-12/olcum.py::kosum'un üç `assert`i, kablolu
    fonksiyonda AYNEN geçmeli."""
    assert broker.derisk_mult(90.0, 100.0) == 1.0
    assert abs(broker.derisk_mult(80.0, 100.0) - 0.7619) < 1e-9
    assert broker.derisk_mult(64.0, 100.0) == 0.0


@pytest.mark.parametrize("peak", [1.0, 0.25, 100.0, 100_000.0, 1_000_000.0])
def test_kablolu_fonksiyon_olcum_rampasiyla_IZGARA_BOYUNCA_ozdes(peak):
    """Üç nokta bir eğri yapmaz: dd %0 → %50 arası 501 noktada bit-bit eşitlik aranır (yuvarlama
    hanesi ve sınır yönleri dahil)."""
    ayna = _olcum_rampasi(0.15, 0.36)
    for i in range(501):
        dd = i / 1000.0
        eq = peak * (1.0 - dd)
        assert broker.derisk_mult(eq, peak) == ayna(eq, peak), f"dd={dd} peak={peak}"


def test_ayna_yanlis_bantla_ayrisir_POZITIF_KONTROL():
    """Üstteki özdeşlik testi bir şey KANITLIYOR mu? Yanlış bantlı ayna ayrışmalı — yoksa test
    her koşulda yeşil yanan bir süs olurdu."""
    yanlis = _olcum_rampasi(0.03, 0.08)
    assert broker.derisk_mult(94.0, 100.0) != yanlis(94.0, 100.0)


# =================================================================================================
# YETKİ — RAMPA OPERATÖR KALEMİDİR (C24 deseni birebir)
# =================================================================================================
def test_rampa_ucu_HERMESE_KAPALI():
    """C24'ün üç ısı eşiğiyle AYNI yasa (test_kovab_dalga3_v166 emsali): LIMIT_KEYS'te olmalı,
    bounds.yaml'da OLMAMALI (iki sahip = sessiz ayrışma + hükümsüz arama ekseni), ve
    `validate_change` öneriyi her şekliyle reddetmeli."""
    b, g, p = config.bounds(), config.goal(), config.default_strategy()["params"]
    for key in ("derisk_full_dd", "derisk_floor_dd"):
        assert key in guard.LIMIT_KEYS, f"{key} LIMIT_KEYS'te yok — GU1 sürüklenme testi kırılır"
        assert key not in b, f"{key} bounds.yaml'a da girmiş — iki sahip, sessiz ayrışma"
        for prop in ({"variable": key, "new": 0.2}, {"variable": f"{key}@chop", "new": 0.2},
                     {"variable": f"limits.{key}", "new": 0.2}, {"changes": {key: 0.2}}):
            assert not guard.validate_change(prop, p, b, g, [], 0).ok, f"{prop} guard'ı geçti"


def test_goal_yaml_bandi_benimsenen_karardir():
    """Dosyanın kendisi de çivili: pencere kararı 15/36 idi (EDG-023 ölçümü + §E.1/§E.3)."""
    lim = config.goal()["limits"]
    assert (float(lim["derisk_full_dd"]), float(lim["derisk_floor_dd"])) == (0.15, 0.36)
    assert float(lim["derisk_full_dd"]) < float(lim["derisk_floor_dd"])
