"""test_replay_sweep_v277.py — REPLAY-SWEEP İSKELETİNİN KAPI SINAMALARI (OPT Faz-1/WP3-B).

NEDEN VAR: `ops/replay_sweep.py` dört emsal ölçümün (edg045/edg046/edg048/exe008) ortak
omurgasını donduran kart-güdümlü koşum iskeletidir. İskeletin kapı fonksiyonları burada
SENTETİK mini-fikstürlerle sınanır — motor KOŞULMAZ, şasi YÜKLENMEZ, state/ YAZILMAZ; her
fikstür pytest `tmp_path` altındadır. Sınanan sınıflar:
  (1) kart okuma: parameter_grid ÇARPILARAK hücreleşir (K disiplini: EXE-008 emsali);
      seed/künye ölçülemezse UYDURULMAZ (None + neden — UYDURMA YASAĞI).
  (2) motor-sha künye kapısı: künyeyle birebir → geçer; tek bayt sapma → düşer (DURUR-davranışı
      koşucuda DURDU damgasına bağlanır; damga biçimi ayrıca sınanır).
  (3) kontrol-hücresi bayt-özdeşlik kapısı: üç defter sha256 kıyası + künye çivisi — pozitif
      kontrol (özdeş → geçer) ve negatifler (bayt sapması / eksik dosya / çivi tutarsızlığı).
  (4) eşlenik ay-kümeli bootstrap: seed-determinizmi (aynı seed → bayt-aynı sonuç; farklı
      seed → farklı CI), eşleniklik (özdeş defter → Δ=0, CI=[0,0]) ve ayırt edicilik
      (her ayda +sabit → CI-alt > 0) + takvim-dışı işlem SAYILIR (YASA-4).
  (5) DURDU/sonuc_grid damga biçimi: DURDU → exit 2 + dosyada DURDU anahtarı; temiz → exit 0.
  (6) enjeksiyon modülü arayüz sözleşmesi + `--stub` çıktısının yüklenebilirliği ve stub
      güvenliği (on_sinama gecti=False — stub yanlışlıkla ölçüme giremez).

HÜKÜM YOK sınıfı: iskelet karar kuralı taşımadığından burada "GO/NO-GO" sınaması YOKTUR —
sınanan şey kapıların mekanik doğruluğu ve damga biçimleridir.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import pathlib

import pytest

from tests.conftest import betikten_modul_yukle

rs = importlib.import_module("ops.replay_sweep")


# ---------------------------------------------------------------------------------------------
# fikstür yardımcıları — sentetik motor dizini / künye / defter üçlüsü
# ---------------------------------------------------------------------------------------------
def _motor_kur(dizin: pathlib.Path, icerikler: dict | None = None) -> dict:
    """Sahte motor dizini (4 dosya) kurar, sha haritasını döndürür."""
    dizin.mkdir(parents=True, exist_ok=True)
    shalar = {}
    for f in rs.MOTOR_SHA_DOSYALAR:
        veri = (icerikler or {}).get(f, f"# sahte {f}\n").encode()
        (dizin / f).write_bytes(veri)
        shalar[f] = hashlib.sha256(veri).hexdigest()
    return shalar


def _kunye_yaz(yol: pathlib.Path, motor_shalari: dict, kapi_shalari: dict | None = None) -> None:
    kunye = {"motor_sha256": {"kosum1_once": {f: {"sha256": s}
                                              for f, s in motor_shalari.items()}},
             "determinizm_kaniti": {"kapi_sha256": dict(kapi_shalari or {})}}
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(json.dumps(kunye), encoding="utf-8")


def _defter_uclusu(dizin: pathlib.Path, ek: str = "", tohum: str = "ozdes") -> dict:
    """Kontrol defter üçlüsünü (islemler_tam/islemler/seanslar) yazar; sha haritası döner."""
    dizin.mkdir(parents=True, exist_ok=True)
    shalar = {}
    for ad in rs.KAPI_DEFTERLER:
        govde = ad[: -len(".json")]
        veri = json.dumps({"d": govde, "t": tohum}).encode()
        (dizin / f"{govde}{ek}.json").write_bytes(veri)
        shalar[ad] = hashlib.sha256(veri).hexdigest()
    return shalar


def _kart_yaz(yol: pathlib.Path, govde: str) -> pathlib.Path:
    yol.write_text(govde, encoding="utf-8")
    return yol


# ---------------------------------------------------------------------------------------------
# (1) kart okuma — grid ÇARPILARAK, seed/künye ölçülür (uydurulmaz)
# ---------------------------------------------------------------------------------------------
def test_kart_grid_carpilarak_hucrelesir(tmp_path):
    kart = _kart_yaz(tmp_path / "K1.yaml", (
        "card_id: TST-2026-001\n"
        "features_asof: >\n  bootstrap (B=5000, seed 20260812)\n"
        "parameter_grid:\n"
        "  cap: [0.005, 0.01]\n"
        "  kural: [a, b, c]\n"
        "status: registered\n"))
    ko = rs.kart_oku(kart, arama_koku=tmp_path)
    assert ko["kart_id"] == "TST-2026-001"
    assert ko["hucre_n"] == 6                        # 2 × 3 — K ÇARPILARAK (EXE-008 emsali)
    assert ko["eksenler"] == ["cap", "kural"]        # karttaki eksen sırası korunur
    assert ko["hucreler"][0] == {"cap": 0.005, "kural": "a"}
    assert ko["hucreler"][-1] == {"cap": 0.01, "kural": "c"}
    # tek eksen — dejenere hâl
    kart2 = _kart_yaz(tmp_path / "K2.yaml", (
        "card_id: TST-2026-002\nfeatures_asof: seed 20260812\n"
        "parameter_grid:\n  bps: [5, 10, 20]\n"))
    assert rs.kart_oku(kart2, arama_koku=tmp_path)["hucre_n"] == 3


def test_kart_grid_olculemezse_none_ve_neden(tmp_path):
    kart = _kart_yaz(tmp_path / "K.yaml", "card_id: TST-2026-003\nfeatures_asof: seed 1\n")
    ko = rs.kart_oku(kart, arama_koku=tmp_path)
    assert ko["hucreler"] is None
    assert ko["hucreler_olculemedi_nedeni"]          # neden boş bırakılmaz (UYDURMA YASAĞI)


def test_kart_seed_olcumu(tmp_path):
    # emsal biçimleri: "seed 20260812" ve "seed=20260812" ve satır sarkması ("seed\n  20260812")
    for govde in ("f: 'B=5000, seed 20260812'", "f: 'seed=20260812'", "f: >\n  B=5000, seed\n  20260812"):
        kart = _kart_yaz(tmp_path / "K.yaml", f"card_id: X\nparameter_grid:\n  a: [1]\n{govde}\n")
        assert rs.kart_oku(kart, arama_koku=tmp_path)["seed"] == 20260812
    # seed yok → None + neden; ÇELİŞEN seed'ler → None + neden (uydurulmaz)
    kart = _kart_yaz(tmp_path / "K.yaml", "card_id: X\nparameter_grid:\n  a: [1]\n")
    ko = rs.kart_oku(kart, arama_koku=tmp_path)
    assert ko["seed"] is None and ko["seed_olculemedi_nedeni"]
    kart = _kart_yaz(tmp_path / "K.yaml",
                     "card_id: X\nparameter_grid:\n  a: [1]\nf: 'seed 1111 sonra seed 2222'\n")
    ko = rs.kart_oku(kart, arama_koku=tmp_path)
    assert ko["seed"] is None and "1111" in ko["seed_olculemedi_nedeni"]


def test_kart_kunye_cozumu(tmp_path):
    kok = tmp_path / "olcumler"
    (kok / "edg032c_taban_x").mkdir(parents=True)
    (kok / "edg032c_taban_x" / "TABAN_KUNYESI.json").write_text("{}")
    kart = _kart_yaz(tmp_path / "K.yaml", (
        "card_id: X\nparameter_grid:\n  a: [1]\n"
        "universe: 'edg032c şasisi AYNEN (TABAN_KUNYESI.json künyesi; seed 20260812)'\n"))
    ko = rs.kart_oku(kart, arama_koku=kok)
    assert ko["kunye_yolu"] and ko["kunye_yolu"].endswith("edg032c_taban_x/TABAN_KUNYESI.json")
    # iki aday dizin + kart metni birini anıyor → metinle tekilleşir
    (kok / "baska_taban_y").mkdir()
    (kok / "baska_taban_y" / "TABAN_KUNYESI.json").write_text("{}")
    ko = rs.kart_oku(kart, arama_koku=kok)
    assert ko["kunye_yolu"] and "edg032c_taban_x" in ko["kunye_yolu"]
    # kart hiçbir künye adı anmıyorsa → None + neden (uydurulmaz)
    kart2 = _kart_yaz(tmp_path / "K2.yaml",
                      "card_id: X\nparameter_grid:\n  a: [1]\nf: seed 20260812\n")
    ko2 = rs.kart_oku(kart2, arama_koku=kok)
    assert ko2["kunye_yolu"] is None and ko2["kunye_olculemedi_nedeni"]


# ---------------------------------------------------------------------------------------------
# (2) motor-sha künye kapısı — pozitif kontrol + tek bayt sapması + eksik dosya
# ---------------------------------------------------------------------------------------------
def test_motor_kunye_kapisi_pozitif_ve_negatif(tmp_path):
    motor = tmp_path / "meridian"
    shalar = _motor_kur(motor)
    kunye = tmp_path / "TABAN_KUNYESI.json"
    _kunye_yaz(kunye, shalar)
    m = rs.motor_sha(motor)
    assert m == shalar                                  # sha ölçümü dosyadan birebir
    assert rs.motor_kunye_kiyas(m, kunye)["kunyeyle_ayni"] is True   # pozitif kontrol
    # tek bayt sapması → kapı düşer ve sapan dosya ADIYLA raporlanır
    (motor / "broker.py").write_bytes(b"# degisti\n")
    kiyas = rs.motor_kunye_kiyas(rs.motor_sha(motor), kunye)
    assert kiyas["kunyeyle_ayni"] is False
    assert kiyas["dosyalar"]["broker.py"]["esit"] is False
    assert kiyas["dosyalar"]["backtest.py"]["esit"] is True
    # eksik dosya → sha None (ölçülemedi) → kapı düşer (sessiz geçiş yok)
    (motor / "guard.py").unlink()
    m2 = rs.motor_sha(motor)
    assert m2["guard.py"] is None
    assert rs.motor_kunye_kiyas(m2, kunye)["kunyeyle_ayni"] is False


def test_hucre_motor_kapisi_once_sonra(tmp_path):
    motor = tmp_path / "meridian"
    shalar = _motor_kur(motor)
    kunye = tmp_path / "K.json"
    _kunye_yaz(kunye, shalar)
    m = rs.motor_sha(motor)
    assert rs.hucre_motor_kapisi(m, dict(m), kunye)["gecti"] is True    # pozitif kontrol
    # koşum İÇİNDE değişim → düşer
    m_sonra = {**m, "strategy.py": "f" * 64}
    kapi = rs.hucre_motor_kapisi(m, m_sonra, kunye)
    assert kapi["gecti"] is False and kapi["motor_sha_ayni"] is False
    # değişmemiş ama künyeden sapmış (iki uçta aynı yanlış dünya) → yine düşer
    kapi2 = rs.hucre_motor_kapisi(m_sonra, m_sonra, kunye)
    assert kapi2["gecti"] is False and kapi2["motor_sha_ayni"] is True


# ---------------------------------------------------------------------------------------------
# (3) kontrol-hücresi bayt-özdeşlik kapısı — üç defter + künye çivisi
# ---------------------------------------------------------------------------------------------
def test_bayt_ozdeslik_kapisi_pozitif(tmp_path):
    yerel, taban = tmp_path / "yerel", tmp_path / "taban"
    _defter_uclusu(yerel)
    kapi_shalari = _defter_uclusu(taban)
    kunye = tmp_path / "K.json"
    _kunye_yaz(kunye, {}, kapi_shalari)
    out = rs.sasi_kapisi(yerel, taban, kunye, smoke=False)
    assert out["kill1_gecti"] is True and out["kunye_sha_tutarli"] is True
    assert (yerel / "sasi_kapisi.json").exists()        # kapı kanıtı damgalanır


def test_bayt_ozdeslik_kapisi_sapma_ve_eksik_dosya(tmp_path):
    yerel, taban = tmp_path / "yerel", tmp_path / "taban"
    _defter_uclusu(yerel)
    kapi_shalari = _defter_uclusu(taban)
    kunye = tmp_path / "K.json"
    _kunye_yaz(kunye, {}, kapi_shalari)
    # tek defterde tek bayt sapması → kapı düşer (DURUR-davranışının tetiği)
    (yerel / "islemler_kontrol.json").write_bytes(b'{"d": "islemler_kontrol", "t": "SAPMA"}')
    out = rs.sasi_kapisi(yerel, taban, kunye, smoke=False)
    assert out["kill1_gecti"] is False
    assert out["bayt_kiyas"]["islemler_kontrol.json"]["bayt_ozdes"] is False
    assert out["bayt_kiyas"]["seanslar_kontrol.json"]["bayt_ozdes"] is True
    # eksik taban dosyası → ölçülemedi nedeni + kapı düşer
    _defter_uclusu(yerel)                               # yereli onar
    (taban / "seanslar_kontrol.json").unlink()
    out2 = rs.sasi_kapisi(yerel, taban, kunye, smoke=False)
    assert out2["kill1_gecti"] is False
    assert out2["bayt_kiyas"]["seanslar_kontrol.json"]["olculemedi_nedeni"]


def test_bayt_ozdeslik_kunye_civisi_tutarsizligi(tmp_path):
    """Defterler bayt-özdeş AMA künye çivisi tutmuyor (taban dosyaları künyedeki kayıt değil)
    → kapı DÜŞER (edg046 künye çivisi emsali). Duman modunda çivi sınanmaz (None)."""
    yerel, taban = tmp_path / "yerel", tmp_path / "taban"
    _defter_uclusu(yerel)
    _defter_uclusu(taban)
    kunye = tmp_path / "K.json"
    _kunye_yaz(kunye, {}, {ad: "0" * 64 for ad in rs.KAPI_DEFTERLER})   # çivi başka dünyada
    out = rs.sasi_kapisi(yerel, taban, kunye, smoke=False)
    assert out["kunye_sha_tutarli"] is False and out["kill1_gecti"] is False
    _defter_uclusu(yerel, ek="_smoke")
    _defter_uclusu(taban, ek="_smoke")
    out_s = rs.sasi_kapisi(yerel, taban, kunye, smoke=True)
    assert out_s["kunye_sha_tutarli"] is None and out_s["kill1_gecti"] is True


# ---------------------------------------------------------------------------------------------
# (4) eşlenik ay-kümeli bootstrap — seed-determinizmi + eşleniklik + ayırt edicilik + YASA-4
# ---------------------------------------------------------------------------------------------
AYLAR = [f"2025-{m:02d}" for m in range(1, 13)]

def _defter(pnl_ay: dict) -> list[dict]:
    return [{"ts_open": f"{a}-15T14:30:00", "pnl_dollars": v} for a, v in pnl_ay.items()]

def test_bootstrap_seed_determinizmi():
    taban = _defter({a: 100.0 * (i - 6) for i, a in enumerate(AYLAR)})
    hucre = _defter({a: 130.0 * (i - 5) for i, a in enumerate(AYLAR)})
    d1 = rs.delta_pnl_ci(taban, hucre, AYLAR, seed=20260812)
    d2 = rs.delta_pnl_ci(taban, hucre, AYLAR, seed=20260812)
    assert d1 == d2                                    # aynı seed → bayt-aynı sonuç
    assert "seed=20260812" in d1["yontem"] and "karttan" in d1["yontem"]
    d3 = rs.delta_pnl_ci(taban, hucre, AYLAR, seed=12345)
    assert d3["ci95"] != d1["ci95"]                    # farklı seed → farklı çekiliş
    assert d3["delta_pnl"] == d1["delta_pnl"]          # nokta tahmini seed'den bağımsız

def test_bootstrap_eslenik_ozdes_defter_sifir():
    """EŞLENİKLİK pozitif kontrolü: iki kol AYNI defterse Δ=0 ve CI=[0,0] — iki kol aynı ayı
    görmeseydi (bağımsız çekiliş) CI sıfırdan şişerdi; bu test o hatayı yakalar."""
    defter = _defter({a: 250.0 * ((i % 5) - 2) for i, a in enumerate(AYLAR)})
    d = rs.delta_pnl_ci(defter, list(defter), AYLAR, seed=20260812)
    assert d["delta_pnl"] == 0.0
    assert d["ci95"] == [0.0, 0.0]
    assert d["sifir_disinda"] == "hayır (0 içinde)"

def test_bootstrap_ayirt_edicilik_ve_takvim_disi_sayimi():
    taban = _defter({a: 100.0 for a in AYLAR})
    hucre = _defter({a: 200.0 for a in AYLAR})         # her ayda +100 → CI-alt > 0 zorunlu
    d = rs.delta_pnl_ci(taban, hucre, AYLAR, seed=20260812)
    assert d["delta_pnl"] == 1200.0
    assert d["ci95"][0] > 0 and d["sifir_disinda"] == "evet (CI-alt > 0)"
    # takvim dışı işlem SAYILIR, sessiz düşmez (YASA-4)
    hucre_tasan = hucre + [{"ts_open": "2019-01-05T14:30:00", "pnl_dollars": 9e9}]
    d2 = rs.delta_pnl_ci(taban, hucre_tasan, AYLAR, seed=20260812)
    assert d2["takvim_disi_islem"] == {"taban": 0, "hucre": 1}
    assert d2["delta_pnl"] == 1200.0                   # taşan satır toplamı KİRLETMEZ


# ---------------------------------------------------------------------------------------------
# (5) DURDU / sonuc_grid damga biçimi
# ---------------------------------------------------------------------------------------------
def test_durdu_damgasi_exit_2_ve_dosyada(tmp_path):
    yol = tmp_path / "sonuc_grid.json"
    rapor = {"kart": "TST", "DURDU": "motor-künye kapısı: tutarsız — koşum YAPILMADI"}
    assert rs.rapor_yaz(rapor, yol) == 2               # DURDU → exit 2 (edg048 kanonik)
    d = json.loads(yol.read_text())
    assert d["DURDU"].startswith("motor-künye kapısı")

def test_temiz_damga_exit_0_ve_hukum_yok(tmp_path):
    yol = tmp_path / "sonuc_grid.json"
    rapor = {"kart": "TST", "hukum_yok": rs.HUKUM_YOK_BEYANI,
             "k_defteri_beyani": rs.K_DEFTERI_BEYANI}
    assert rs.rapor_yaz(rapor, yol) == 0
    d = json.loads(yol.read_text())
    assert "HÜKÜM İÇERMEZ" in d["hukum_yok"]           # hüküm yasağı damgada taşınır
    assert "K SAYMAZ" in d["k_defteri_beyani"]         # iskelet K saymaz — kart neyse o

def test_artik_bul_durdurma_tetigi(tmp_path):
    outdir = tmp_path
    assert rs.artik_bul(tmp_path, outdir, "hucre1", "") == []          # temiz → koşulabilir
    (outdir / "sonuc_hucre1.json").write_text("{}")
    (tmp_path / "state_hucre1").mkdir()
    artiklar = rs.artik_bul(tmp_path, outdir, "hucre1", "")
    assert set(artiklar) == {"sonuc_hucre1.json", "state_hucre1"}


# ---------------------------------------------------------------------------------------------
# (6) enjeksiyon modülü arayüzü + stub
# ---------------------------------------------------------------------------------------------
def test_arayuz_eksikse_baslamadan_durur(tmp_path):
    bos = tmp_path / "bos_enj.py"
    bos.write_text("KONTROL_HUCRE = {}\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="arayüzü EKSİK"):
        rs.enjeksiyon_modulu_yukle(bos)
    m = betikten_modul_yukle(bos, "bos_enj_t")
    a = rs.arayuz_dogrula(m)
    assert a["gecerli"] is False
    assert set(a["eksik"]) == {"yeni_kayit", "enjekte", "oz_sinama", "kol_kimligi"}

def test_stub_uretilir_yuklenir_ve_guvenlidir(tmp_path):
    yol = tmp_path / "enj_stub.py"
    rs.ornek_stub_uret(yol)
    modul = rs.enjeksiyon_modulu_yukle(yol)            # zorunlu arayüz TAM (pozitif kontrol)
    assert rs.arayuz_dogrula(modul)["gecerli"] is True
    # stub güvenliği: on_sinama doldurulmadan gecti=False → iskelet koşumu BAŞLATMAZ
    on = modul.on_sinama()
    assert on["gecti"] is False and on["neden"]
    # üzerine yazılmaz (yıkıcı değil)
    with pytest.raises(AssertionError, match="zaten var"):
        rs.ornek_stub_uret(yol)

def test_stub_oz_sinamasi_mekanik_ve_ayirt_edici(tmp_path):
    """Stub öz-sınaması sentetik kayıtla sınanır: tutarlı enjeksiyon → geçer; bozuk satır →
    düşer; boş yakalama → geçmez + ölçülemedi nedeni (boş geçen sınama sınama değildir)."""
    yol = tmp_path / "enj_stub.py"
    rs.ornek_stub_uret(yol)
    modul = rs.enjeksiyon_modulu_yukle(yol)
    hucre = {"ek_slip_bps": 10.0}
    ek = 10.0 / 10000.0
    kayit = {"cikis": [
        {"ticker": "AAA", "ts": "t1", "reason": "stop",
         "raw_exit_orig": 100.0, "raw_exit_enjekte": 100.0 * (1 - ek), "defter_exit": 99.85},
        {"ticker": "BBB", "ts": "t2", "reason": "target",
         "raw_exit_orig": 50.0, "raw_exit_enjekte": 50.0, "defter_exit": 49.97},
    ]}
    oz = modul.oz_sinama(hucre, kayit, ciktilar={}, kontrol=False)
    assert oz["kill2_gecti"] is True and oz["bozuk_n"] == 0
    # sızıntı: stop-dışı satıra enjeksiyon bulaşmış → yakalanır
    kayit["cikis"][1]["raw_exit_enjekte"] = 49.0
    oz2 = modul.oz_sinama(hucre, kayit, ciktilar={}, kontrol=False)
    assert oz2["kill2_gecti"] is False and oz2["bozuk_n"] == 1
    # boş yakalama → sınama boş, geçmiş sayılmaz
    oz3 = modul.oz_sinama(hucre, {"cikis": []}, ciktilar={}, kontrol=False)
    assert oz3["kill2_gecti"] is False and oz3["kill2_olculemedi_nedeni"]

def test_run_adi_varsayilan_ve_kontrol_rezerv(tmp_path):
    class _BosModul:                                   # run_adi vermeyen modül temsili
        pass
    ad = rs.run_adi(_BosModul(), {"cap": 0.005, "kural": "dinlenen limit"})
    assert ad == "cap0.005_kuraldinlenen-limit"        # deterministik + dosya-adı güvenli
    class _AdliModul:
        @staticmethod
        def run_adi(h):
            return f"cap{h['cap']}"
    assert rs.run_adi(_AdliModul(), {"cap": 0.01}) == "cap0.01"
    with pytest.raises(AssertionError, match="rezerve"):
        rs.run_adi(_BosModul(), {})                    # boş hücre → boş ad → geçersiz
    class _KontrolAdli:
        @staticmethod
        def run_adi(h):
            return "kontrol"                           # rezerve ada el koyma girişimi
    with pytest.raises(AssertionError, match="rezerve"):
        rs.run_adi(_KontrolAdli(), {"cap": 0.01})


def test_pf_edg037_tanimi():
    """PF donmuş tanımla (EDG-037): Σ(pnl>0)/|Σ(pnl<0)|; kayıp bacağı boşsa None + neden."""
    defter = [{"pnl_dollars": 300.0}, {"pnl_dollars": -100.0}, {"pnl_dollars": -50.0}]
    assert rs._pf(defter) == (2.0, None)
    pf, neden = rs._pf([{"pnl_dollars": 10.0}])
    assert pf is None and "TANIMSIZ" in neden
