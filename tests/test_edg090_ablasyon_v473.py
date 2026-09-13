"""EDG-2026-090 ABLASYON ÖLÇÜMÜNÜN ÇİVİLERİ — `research/olcumler/edg090_golge_ayrisma/ablasyon.py`.

NE ÇİVİLER. Kart `EDG-2026-090` gölge↔gerçek ayrışmasını ÜÇ ablasyona böler (A giriş semantiği ·
B E2 ATR enjeksiyonu · C `manage_position` paritesi) ve bunları ÖLÇÜM TARAFINDA uygular: üretim
kodu (`meridian/golge_icra.py`, `broker.py`, `strategy.py`) DEĞİŞMEZ, motorun iç yüzeyleri ölçüm
süreci içinde sarmalanır ve blok bitince geri konur. Bu dosya o iddiaların HER BİRİNİ ölçer.

ÇİVİLERİN HEDEF DALLARI (her biri mutasyonla ısırdığı gösterildi — rapor `rapor_edg090.md`):
  A1 eşikler KARTTAN okunur (bu dosyada da betikte de sayı olarak yazılı DEĞİL) ·
  A2 donmuş girdinin SHA256SUMS kimliği · A3 PK (2) kıyas artefaktı ZORUNLU ·
  B1 sentetik sahnede gölge R el hesabıyla birebir VE beş kipte AYNI (ablasyon BOZMUYOR) ·
  B2 A anahtarı koşulsuz dolumu AÇAR (tetiği gelmeyen plan girer) ve dolum fiyatı E2'nin ·
  B3 B anahtarı E2 ATR'sini limite ENJEKTE eder · B4 C anahtarı `scale_out` halkasını EKLER ·
  C1 ablasyon üretim yüzeylerini BİREBİR geri koyar ve kaynak sha'sını değiştirmez ·
  C2 canlı `state/` ağacına yazım YOK · C3 komut satırı sözleşmesi + PK düşünce ÇIKIŞ 2 ·
  D1 ters kontrolün YÖNÜ · D2 PK (2) kıyası ÖLÇÜLEN SAYI değişince DÜŞER ·
  D3 kıyas iki paydadan (kendi kümesi / ortak küme) · D4 PK düştüyse rapor SAYI BASMAZ ·
  D5 ADAY D'nin hassasiyet kapısı ve farkın TOPLAMSAL özdeşliği.

SENTETİK SAHNE NEDEN ABLASYONA KÖR. Sahnede `e2` satırı YOKTUR (A'nın dolumu barın açılışına,
B'nin ATR'si `None`a düşer) ve donmuş v5 sözleşmesinde `exit.scale_out_frac` 0'dır (C'nin eklediği
halka atıl koşar). Yani A/B/C YAPISAL olarak etkisizdir; kiplerden birinde R'nin kayması,
ablasyonun ölçtüğü şeyi değil BOZDUĞU şeyi gösterirdi. Sahnenin selefi
`tests/test_edg088_pk2_gercek_v472.py` B1 sahnesidir (aynı doktrin: iki işlem de GİRİŞ barının
içinde kapanır, çıkış zinciri ve rejim kapısı sonuca karışmaz).
"""
from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import sys

import pandas as pd
import pytest

KOK = pathlib.Path(__file__).resolve().parents[1]
EDG088 = KOK / "research" / "olcumler" / "edg088_golge_pilot"
EDG090 = KOK / "research" / "olcumler" / "edg090_golge_ayrisma"
for _p in (str(KOK), str(EDG088), str(EDG090)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ablasyon as ab  # noqa: E402
import pk2_gercek as pk2  # noqa: E402
from meridian import broker as brk  # noqa: E402
from meridian import golge_icra as gi  # noqa: E402

DONMUS_GIRDI_DIZIN = EDG088 / "pk2_gercek" / "girdi"
AAPL_PLAN = f"P-{ab.SENTETIK_D_PLAN}-AAPL"


def _goal() -> dict:
    import yaml
    return yaml.safe_load((ab.params_varsayilan() / "goal.yaml").read_text(encoding="utf-8"))


def _kos(kok: pathlib.Path, kod: str, enj: dict | None = None,
         girdi=None, bars=None) -> dict:
    """Sentetik sahnede BİR kip. Sahne yoksa kurulur; her kip kendi state alt dizininde koşar."""
    if girdi is None:
        girdi, bars = ab.sentetik_sahne(kok)
    return ab.kos_ablasyon(kod, girdi, bars, ab.params_varsayilan(), kok / "state",
                           enj or {}, _goal(), n_gercek=len(ab.SENTETIK_TICKERLAR),
                           beklenen_tickerlar=ab.SENTETIK_TICKERLAR)


def _islem(sonuc: dict, ticker: str) -> dict:
    return next(r for r in sonuc["islemler"] if r["ticker"] == ticker)


# ==================================================================================================
# A1 — EŞİKLER KARTTAN OKUNUR (tek-kaynak)
# ==================================================================================================
def test_A1_esikler_KARTTAN_okunur_betikte_sayi_olarak_YOK(tmp_path, monkeypatch):
    """Eşik betikte sayı olarak yazılı olsaydı kartla sessizce ayrışırdı: kartı yamayan bir çivi
    YENİ değeri görmek zorundadır."""
    es = ab.esikler()
    kart = pathlib.Path(ab.kart_yolu()).read_text(encoding="utf-8")
    assert es["ort_fark_r_ust"] == float(gi.FARK_R_UST)
    assert es["esik_ayrismasi"] is False

    sahte = tmp_path / "kart.yaml"
    sahte.write_text(kart.replace("ablasyon_dusus_alt_r: 0.05",
                                  "ablasyon_dusus_alt_r: 0.42"), encoding="utf-8")
    monkeypatch.setattr(ab, "kart_yolu", lambda: sahte)
    assert ab.esikler()["ablasyon_dusus_alt_r"] == 0.42


def test_A1_kart_esigi_MOTOR_SABITIYLE_ayrisirsa_BLOK(tmp_path, monkeypatch):
    """Kartın eşiği ile `golge_icra.FARK_R_UST` ayrışırsa hangi eşiğin konuştuğu belirsizdir."""
    kart = pathlib.Path(ab.kart_yolu()).read_text(encoding="utf-8")
    sahte = tmp_path / "kart.yaml"
    sahte.write_text(kart.replace("ort_fark_r_ust: 0.05", "ort_fark_r_ust: 0.09"),
                     encoding="utf-8")
    monkeypatch.setattr(ab, "kart_yolu", lambda: sahte)
    with pytest.raises(ab.Blok, match="AYRIŞIYOR"):
        ab.esikler()


def test_A1_kart_dosyasi_yoksa_BLOK(tmp_path, monkeypatch):
    monkeypatch.setattr(ab, "kart_yolu", lambda: tmp_path / "yok.yaml")
    with pytest.raises(ab.Blok, match="kart dosyası YOK"):
        ab.esikler()


# ==================================================================================================
# A2 — DONMUŞ GİRDİNİN KİMLİĞİ (SHA256SUMS)
# ==================================================================================================
def test_A2_donmus_girdi_manifestosunun_HER_SATIRI_tutar():
    """Kart bir artefaktı donduruyorsa kimliği BEYAN değil ÖLÇÜM olmalıdır (EDG-059 sınıfı)."""
    man = DONMUS_GIRDI_DIZIN / pk2.MANIFEST_ADI
    satirlar = [s.split() for s in man.read_text(encoding="utf-8").splitlines() if s.split()]
    assert len(satirlar) >= 17, len(satirlar)
    for parca in satirlar:
        yol = DONMUS_GIRDI_DIZIN / parca[-1].lstrip("*")
        assert yol.exists(), yol
        assert hashlib.sha256(yol.read_bytes()).hexdigest() == parca[0], yol.name


def test_A2_girdi_DEGISMISSE_olcum_baslamaz(tmp_path):
    kaynak = pk2.girdi_varsayilan()
    kopya = tmp_path / kaynak.name
    kopya.write_text(kaynak.read_text(encoding="utf-8") + " ", encoding="utf-8")
    (tmp_path / pk2.MANIFEST_ADI).write_text(
        f"{hashlib.sha256(kaynak.read_bytes()).hexdigest()}  {kaynak.name}\n", encoding="utf-8")
    with pytest.raises(ab.Blok, match="sha256 uyuşmuyor"):
        pk2.girdi_oku(kopya)


def test_A3_pk2_kiyas_artefakti_ZORUNLU(tmp_path):
    """PK (2) bir KIYAStır: artefakt yoksa "ölçemedim" ile "eşleşmedi" karışırdı."""
    assert ab.taban_sonuc_varsayilan().exists()
    with pytest.raises(ab.Blok, match="taban sonucu YOK"):
        ab.pk_taban({}, tmp_path / "yok.json")


# ==================================================================================================
# B1 — SENTETİK ZİNCİR: BEŞ KİPTE AYNI R
# ==================================================================================================
def test_B1_sentetik_R_EL_HESABIYLA_birebir_ve_BES_KIPTE_ayni(tmp_path, sandbox_state):
    pk = ab.pk_sentetik(tmp_path, ab.params_varsayilan(), _goal())
    assert pk["gecti"] is True, pk["sapan"]
    assert set(pk["kipler"]) == set(ab.ABLASYONLAR)
    for kod, olculen in pk["kipler"].items():
        assert olculen["AAPL"]["golge_r"] == pytest.approx(round(14.0 / 6.0, 6)), kod
        assert olculen["MSFT"]["golge_r"] == pytest.approx(-1.0), kod
        assert olculen["AAPL"]["neden"] == "target" and olculen["MSFT"]["neden"] == "stop", kod


def test_B1_sentetik_sapma_SESSIZ_gecmez(tmp_path, sandbox_state, monkeypatch):
    """Beklenen R yamanırsa PK DÜŞMELİ — çivi kendi ölçtüğünü doğrulamıyor."""
    monkeypatch.setitem(ab.SENTETIK_BEKLENEN_R, "MSFT", -0.5)
    pk = ab.pk_sentetik(tmp_path, ab.params_varsayilan(), _goal(), kodlar=("yok",))
    assert pk["gecti"] is False and pk["sapan"]


# ==================================================================================================
# B2 — A ANAHTARI: KOŞULSUZ DOLUM + E2 FİYATI
# ==================================================================================================
def _sahne_tetik_gelmedi(kok: pathlib.Path):
    """AAPL giriş barı tetiğin ALTINDA kapanır (h=99,5 < tetik 100) ama stopa DOKUNUR (l=94 ≤ 95).

    Gölgenin kendi kuralı: `tetik_gelmedi` → giriş YOK. Üretimin kuralı: ertesi açılışta KOŞULSUZ
    dolum (98,0) → aynı barda stop (95) → R = (95 − 98) / (98 − 95) = −1,0. İki kuralın AYRIŞTIĞI
    en dar sahne budur.
    """
    girdi, bars = ab.sentetik_sahne(kok)
    df = pd.read_csv(bars / "aapl.csv")
    df.loc[df.index[-1], ["open", "high", "low", "close"]] = [98.0, 99.5, 94.0, 96.0]
    df.to_csv(bars / "aapl.csv", index=False)
    return girdi, bars


def test_B2_A_anahtari_TETIGI_GELMEYEN_plani_ACAR(tmp_path, sandbox_state):
    girdi, bars = _sahne_tetik_gelmedi(tmp_path)
    taban = _kos(tmp_path, "yok", girdi=girdi, bars=bars)
    acik = _kos(tmp_path, "A", girdi=girdi, bars=bars)

    t, a = _islem(taban, "AAPL"), _islem(acik, "AAPL")
    assert t["golge_giris_reddi"] == "tetik_gelmedi" and t["golge_r"] is None
    assert a["golge_giris_reddi"] is None
    assert a["golge_giris_fiyat"] == pytest.approx(98.0)
    assert a["golge_r"] == pytest.approx(-1.0)
    iz = [x for x in acik["ablasyon"]["a_izi"] if x["plan_id"] == AAPL_PLAN]
    assert iz and iz[0]["golge_kuralinda_girerdi"] is False, iz


def test_B2_A_dolum_fiyati_E2_SATIRINDAN_gelir(tmp_path, sandbox_state):
    """Üretimin dolumu barın açılışı DEĞİL, E2'ye yazılmış GERÇEK dolumdur (kaymalı)."""
    girdi, bars = _sahne_tetik_gelmedi(tmp_path)
    enj = {AAPL_PLAN: {"fill": 98.4, "atr": None, "limit": None, "resmi_acilis": 98.0,
                       "gap_at_submit": False, "motor": "ic"}}
    s = _kos(tmp_path, "A", enj=enj, girdi=girdi, bars=bars)
    a = _islem(s, "AAPL")
    assert a["golge_giris_fiyat"] == pytest.approx(98.4)
    # R paydası da dolumdan türer: (95 − 98,4) / (98,4 − 95)
    assert a["golge_r"] == pytest.approx(round((95.0 - 98.4) / (98.4 - 95.0), 6))
    iz = [x for x in s["ablasyon"]["a_izi"] if x["plan_id"] == AAPL_PLAN][0]
    assert iz["dolum_kaynagi"] == "e2_fill" and iz["acilis"] == pytest.approx(98.0)


def test_B2_A_URETIMIN_KAPILARINI_uygular(tmp_path, sandbox_state):
    """Açılış planlanan stopun ALTINDA ise üretim de girmez — A kapıyı KALDIRMAZ, kuralı değiştirir."""
    girdi, bars = ab.sentetik_sahne(tmp_path)
    df = pd.read_csv(bars / "aapl.csv")
    df.loc[df.index[-1], ["open", "high", "low", "close"]] = [94.0, 99.0, 93.0, 96.0]
    df.to_csv(bars / "aapl.csv", index=False)
    s = _kos(tmp_path, "A", girdi=girdi, bars=bars)
    assert _islem(s, "AAPL")["golge_giris_reddi"] == "acilis_stop_altinda"
    iz = [x for x in s["ablasyon"]["a_izi"] if x["plan_id"] == AAPL_PLAN][0]
    assert iz["red"] == "acilis_stop_altinda" and iz["dolum"] is None


# ==================================================================================================
# B3 — B ANAHTARI: E2 ATR'Sİ LİMİTE ENJEKTE EDİLİR
# ==================================================================================================
def test_B3_B_anahtari_E2_ATR_sini_URETIMIN_hesabina_verir(tmp_path, sandbox_state):
    girdi, bars = ab.sentetik_sahne(tmp_path)
    enj = {AAPL_PLAN: {"fill": None, "atr": 5.0, "limit": None, "resmi_acilis": 101.0,
                       "gap_at_submit": False, "motor": "ic"}}
    taban = _kos(tmp_path, "yok", enj=enj, girdi=girdi, bars=bars)
    b = _kos(tmp_path, "B", enj=enj, girdi=girdi, bars=bars)

    assert taban["ablasyon"]["b_enjeksiyon_n"] == 0 and not taban["ablasyon"]["b_izi"]
    assert b["ablasyon"]["b_enjeksiyon_n"] >= 1, b["ablasyon"]["b_izi"]
    kayit = [x for x in b["ablasyon"]["b_izi"] if x["plan_id"] == AAPL_PLAN][0]
    assert kayit["enjekte_atr"] == pytest.approx(5.0)
    # HESABI ÜRETİM YAPAR: sarmalayıcı yalnız eksik argümanı doldurur.
    assert kayit["limit_atrli"] == pytest.approx(
        round(float(brk.entry_limit_price(kayit["tetik"], 5.0)), 6))
    assert kayit["limit_atrsiz"] == pytest.approx(
        round(float(brk.entry_limit_price(kayit["tetik"], None)), 6))
    assert kayit["limit_degisti"] is (kayit["limit_atrli"] != kayit["limit_atrsiz"])


def test_B3_B_kipinde_de_R_DEGISMEZ_sentetik_sahnede(tmp_path, sandbox_state):
    """Enjeksiyon GERÇEKLEŞİR ama yürürlükteki yasa altında limit bağlamayabilir: "bağlanmadı" ile
    "bağlandı, atıl" AYRI olgulardır ve sayaçlar ikisini ayırır."""
    girdi, bars = ab.sentetik_sahne(tmp_path)
    enj = {AAPL_PLAN: {"fill": None, "atr": 5.0, "limit": None, "resmi_acilis": 101.0,
                       "gap_at_submit": False, "motor": "ic"}}
    b = _kos(tmp_path, "B", enj=enj, girdi=girdi, bars=bars)
    assert _islem(b, "AAPL")["golge_r"] == pytest.approx(round(14.0 / 6.0, 6))


# ==================================================================================================
# B4 — C ANAHTARI: `scale_out` HALKASI ZİNCİRE EKLENİR
# ==================================================================================================
def test_B4_C_anahtari_scale_out_HALKASINI_ekler_ve_ATESLEMEDIGINI_sayar(tmp_path, sandbox_state):
    girdi, bars = ab.sentetik_sahne(tmp_path)
    taban = _kos(tmp_path, "yok", girdi=girdi, bars=bars)
    c = _kos(tmp_path, "C", girdi=girdi, bars=bars)
    assert taban["ablasyon"]["c_scale_out_cagrisi"] == 0
    assert c["ablasyon"]["c_scale_out_cagrisi"] >= 2, c["ablasyon"]
    assert c["ablasyon"]["c_scale_out_atesledi"] == 0
    assert "golge_icra.brk.PaperBroker._touch_exit" in c["ablasyon"]["sarmalanan_yuzeyler"]


def test_B4_C_paritesi_OLCULUR_varsayilmaz():
    """Paritenin kalan bacakları (keşif kolu, `scale_out` düğmesi, `pivot`, çıkış fiyatı) ÖLÇÜLÜR;
    ölçülemeyen bacak `None` + ADLI neden ile durur."""
    veri = pk2.girdi_oku(pk2.girdi_varsayilan())
    secilen = pk2.son_n_gercek(veri["trades"])
    par = ab.parite_olc(secilen, pk2.parametre_tabani(ab.params_varsayilan()),
                        ab.enjeksiyon_haritasi(veri))
    assert par["kesif_kolu"]["parite"] is (par["kesif_kolu"]["n_exploration"] == 0)
    assert par["scale_out"]["zincire_eklendi"] is True
    assert par["pivot"]["olculdu"] is False and par["pivot"]["neden"]
    assert par["cikis_icra_fiyati"]["parite"] is True, par["cikis_icra_fiyati"]
    assert par["zincir_sirasi"]["parite"] is True, par["zincir_sirasi"]


def test_B4_canli_dikis_KAYBOLURSA_parite_BAYAT_der():
    """Beyan kendi çürümesini haber vermeli: aranan dikiş yoksa `parite` False + ADLI neden."""
    yok = ab._dikisi_olc("BU_DIKIS_CANLI_GOVDEDE_YOK", "beyan")
    assert yok["olculdu"] is True and yok["parite"] is False and "BAYAT" in yok["neden"]


# ==================================================================================================
# C1 — ABLASYON ÜRETİME DOKUNMAZ (kart kill#2)
# ==================================================================================================
def test_C1_ablasyon_MOTOR_YUZEYLERINI_birebir_geri_koyar():
    once = (gi._girisi_dene, gi.brk, gi.adim, gi.strategy)
    with ab.ablasyon_kur("ABC", {}, _goal()) as iz:
        assert gi._girisi_dene is not once[0]
        assert gi.brk is not once[1] and gi.adim is not once[2]
        assert iz["sarmalanan"]
    assert (gi._girisi_dene, gi.brk, gi.adim, gi.strategy) == once


def test_C1_blok_ICINDE_hata_olsa_da_geri_konur():
    once = (gi._girisi_dene, gi.brk, gi.adim, gi.strategy)
    with pytest.raises(RuntimeError):
        with ab.ablasyon_kur("ABC", {}, _goal()):
            raise RuntimeError("ölçüm patladı")
    assert (gi._girisi_dene, gi.brk, gi.adim, gi.strategy) == once


def test_C1_URETIM_KAYNAGININ_sha256si_kosumdan_ETKILENMEZ(tmp_path, sandbox_state):
    once = ab.motor_kaynak_damgasi()
    assert set(once) == set(ab.MOTOR_DOSYALARI)
    ab.pk_sentetik(tmp_path, ab.params_varsayilan(), _goal(), kodlar=("yok", "ABC"))
    assert ab.motor_kaynak_damgasi() == once


def test_C1_taban_kipinde_SARMALAYICI_olamaz(tmp_path, sandbox_state, monkeypatch):
    """"Ablasyonsuz" iddiası ZORLANIR: bir sarmalayıcı sızarsa PK (2) onu göremezdi (künye
    kıyas dışıdır), o yüzden kapı ayrıca burada durur."""
    monkeypatch.setitem(ab.SARMALANAN, "A", ("sahte_yuzey",))
    monkeypatch.setattr(ab, "TABAN_KODU", "A")
    with pytest.raises(ab.Blok, match="taban kipinde SARMALAYICI"):
        _kos(tmp_path, "A")


# ==================================================================================================
# C2 — CANLI `state/` AĞACINA YAZIM YOK
# ==================================================================================================
def test_C2_depo_state_agaci_altindaki_state_dizini_BLOK(tmp_path):
    kok = pathlib.Path(pk2.depo_koku())
    with pytest.raises(ab.Blok, match="state/"):
        ab.kos(pk2.girdi_varsayilan(), ab.bars_varsayilan(), ab.params_varsayilan(),
               kok / "state" / "edg090", ("yok",))


def test_C2_kosum_CANLI_state_agacini_DEGISTIRMEZ(tmp_path, sandbox_state):
    canli = pathlib.Path(pk2.depo_koku()) / "state"
    once = sorted(p.name for p in canli.iterdir())
    ab.pk_sentetik(tmp_path, ab.params_varsayilan(), _goal(), kodlar=("yok", "A", "C"))
    assert sorted(p.name for p in canli.iterdir()) == once
    assert not (canli / gi.DEFTER).exists() and not (canli / gi.ACIK).exists()


# ==================================================================================================
# C3 — KOMUT SATIRI SÖZLEŞMESİ (ops sözleşmesi `main()` değil KOMUT SATIRIdır)
# ==================================================================================================
def test_C3_komut_satiri_zorunlu_bayraklar_ve_kapali_kume():
    yardim = ab.main.__doc__ or ""
    assert "0 rapor yazıldı" in yardim and "2 PK düştü" in yardim
    with pytest.raises(SystemExit):
        ab.main(["--cikti-dizin", "x"])                       # --state-dizin YOK
    with pytest.raises(SystemExit):
        ab.main(["--state-dizin", "x", "--cikti-dizin", "y", "--ablasyon", "Z"])


def test_C3_PK_dusunce_CIKIS_2_ve_rapor_SAYI_BASMAZ(tmp_path, sandbox_state, monkeypatch):
    """Sentetik sahne PK (3)'ü YAPISAL olarak düşürür (iki işlem de giriş barında kapanır, çıkış
    kuralı hiç koşmaz → ters kontrol ortalamayı ARTIRAMAZ). Kill emsali burada ölçülür.

    "SON 10" KÜMESİ KOMUT SATIRINDAN GEVŞETİLEMEZ (`pk2_gercek` sözleşmesi): mini-vaka sabitleri
    YAMAR, bayrak EKLEMEZ — `son_n_gercek` onları çağrı anında çözdüğü için yama gerçekten ölçülür.
    """
    monkeypatch.setattr(pk2, "N_GERCEK", len(ab.SENTETIK_TICKERLAR))
    monkeypatch.setattr(pk2, "BEKLENEN_TICKERLAR", ab.SENTETIK_TICKERLAR)
    girdi, bars = ab.sentetik_sahne(tmp_path / "sahne")
    cikti = tmp_path / "cikti"
    rc = ab.main(["--girdi", str(girdi), "--bars-dizin", str(bars),
                  "--params", str(ab.params_varsayilan()),
                  "--state-dizin", str(tmp_path / "st"), "--cikti-dizin", str(cikti),
                  "--ablasyon", "yok"])
    assert rc == 2
    md = next(cikti.glob("rapor_*.md")).read_text(encoding="utf-8")
    assert "SAYI YAYILMAZ" in md
    assert "Ablasyon tablosu" not in md and "ADAY D" not in md
    assert next(cikti.glob("sonuc_*.json")).exists()


def test_C3_ithal_meridian_obs_u_TETIKLEMEZ_ve_state_ACMAZ(tmp_path):
    """Betiği İTHAL ETMEK canlı deftere yazan modülü yüklememeli (emsal: v472'nin aynı çivisi)."""
    import os
    import subprocess

    betik = EDG090 / "ablasyon.py"
    ortam = dict(os.environ, MERIDIAN_ROOT=str(tmp_path), PYTHONPATH=str(KOK))
    kod = ("import sys, json, importlib.util;"
           f"spec=importlib.util.spec_from_file_location('a', r'{betik}');"
           "m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m);"
           "print(json.dumps({'obs': 'meridian.obs' in sys.modules,"
           " 'loop': 'meridian.loop' in sys.modules,"
           " 'alpaca': 'meridian.adapters.alpaca' in sys.modules}))")
    r = subprocess.run([sys.executable, "-c", kod], capture_output=True, text=True,
                       cwd=str(tmp_path), env=ortam)
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert json.loads(r.stdout.strip().splitlines()[-1]) == {
        "obs": False, "loop": False, "alpaca": False}
    assert not (tmp_path / "state").exists(), "ithal `state/` açtı"


# ==================================================================================================
# D1 — TERS KONTROLÜN YÖNÜ
# ==================================================================================================
def _sonuc(ort: float | None) -> dict:
    return {"kontrol": {"ort_mutlak_fark_r": ort},
            "ablasyon": {"ters_inkar_edilen_cikis": 3, "ters_cagri": 9}}


def test_D1_ters_kontrol_ARTMAZSA_duser():
    assert ab.pk_ters(_sonuc(0.10), _sonuc(0.40))["gecti"] is True
    assert ab.pk_ters(_sonuc(0.10), _sonuc(0.10))["gecti"] is False
    assert ab.pk_ters(_sonuc(0.10), _sonuc(0.02))["gecti"] is False
    olculemedi = ab.pk_ters(_sonuc(None), _sonuc(0.4))
    assert olculemedi["gecti"] is False and olculemedi["neden"]


def test_D1_ters_sarmalayici_exit_now_u_INKAR_eder(tmp_path, sandbox_state):
    """Kararı ÜRETİM verir; sarmalayıcı yalnız inkâr eder ve KAÇ kararı çevirdiğini sayar."""
    iz: list = []
    sahte = ab._manage_ters(iz)
    df = pd.DataFrame({"date": pd.bdate_range("2026-01-01", periods=40),
                       "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0,
                       "volume": 1e6})
    poz = {"entry": 100.0, "stop": 95.0, "trail_stop": 95.0, "r_per_share": 5.0, "pivot": 0.0}
    import yaml
    params = yaml.safe_load(
        (ab.params_varsayilan() / "strategy.yaml").read_text(encoding="utf-8"))["params"]
    from meridian import strategy as strat
    gercek = strat.manage_position(df, poz, params, 1, True)
    ters = sahte(df, poz, params, 1, True)
    assert ters.exit_now is (not gercek.exit_now)
    assert ters.trail_stop == gercek.trail_stop
    assert iz and iz[0]["orijinal_exit_now"] is bool(gercek.exit_now)


# ==================================================================================================
# D2 — PK (2) KIYASI: ÖLÇÜLEN SAYI DEĞİŞİNCE DÜŞER
# ==================================================================================================
def _taban_artefakt() -> dict:
    return json.loads(ab.taban_sonuc_varsayilan().read_text(encoding="utf-8"))


def test_D2_MUTLAK_YOL_ve_saat_farki_PK2_yi_DUSURMEZ(tmp_path):
    d = _taban_artefakt()
    yeniden = copy.deepcopy(d)
    yeniden["olculdu_utc"] = "2099-01-01T00:00:00+00:00"
    yeniden["motor_yolu"] = "/baska/agac/meridian/__init__.py"
    yeniden["girdi"]["dosya"] = "/baska/agac/girdi.json"
    yeniden["rejim_kapisi"]["motorda_fonksiyon_var"] = True
    yeniden["ablasyon"] = {"kod": "yok", "sarmalanan_yuzeyler": []}
    pk = ab.pk_taban(yeniden, ab.taban_sonuc_varsayilan())
    assert pk["gecti"] is True, pk["farklar"]
    assert [m["alan"] for m in pk["meta_farklari"]]


def test_D2_OLCULEN_SAYI_degisirse_PK2_DUSER_ve_farki_ADIYLA_soyler(tmp_path):
    d = copy.deepcopy(_taban_artefakt())
    d["kontrol"]["ort_mutlak_fark_r"] = 0.111111
    pk = ab.pk_taban(d, ab.taban_sonuc_varsayilan())
    assert pk["gecti"] is False
    assert any("ort_mutlak_fark_r" in f["yol"] for f in pk["farklar"]), pk["farklar"]


def test_D2_ISLEM_BASINA_bir_R_degisirse_de_DUSER():
    d = copy.deepcopy(_taban_artefakt())
    d["islemler"][0]["golge_r"] = -0.5
    pk = ab.pk_taban(d, ab.taban_sonuc_varsayilan())
    assert pk["gecti"] is False
    assert any("golge_r" in f["yol"] for f in pk["farklar"])


def test_D2_dislanan_alanlar_SAYI_TASIMAZ():
    """Dışlama listesi bir gevşetme yüzeyidir: ölçülen sayıları taşıyan hiçbir blok girmemeli."""
    for alan in ab.PK2_DISLANAN:
        kok = alan.split("/")[0]
        assert kok not in ("kontrol", "kontrol_dogrulanmis", "islemler", "esik", "gecti",
                           "dolum_sinifi_dagilimi", "parametre_ayrismasi"), alan
        assert ab.PK2_DISLANAN[alan], alan


# ==================================================================================================
# D3 — KIYAS İKİ PAYDADAN
# ==================================================================================================
def _kosum(ciftler: dict, islemler: list | None = None) -> dict:
    return {"kontrol": {"ciftler": [{"plan_id": p, "ticker": p, "fark_r": f,
                                     "friksiyon_payi_r": 0.02} for p, f in ciftler.items()],
                        "n_hukum_cifti": len(ciftler),
                        "ort_mutlak_fark_r": (round(sum(abs(x) for x in ciftler.values())
                                                    / len(ciftler), 6) if ciftler else None)},
            "kontrol_dogrulanmis": {"ort_mutlak_fark_r": None},
            "islemler": islemler or []}


def test_D3_YENI_CIFT_paydayi_buyutunce_IKI_dusus_AYRISIR():
    """A'da tetiği gelmeyen plan hüküm kümesine girer: "kendi kümesi" düşüşü PAYDANIN
    büyümesinden de gelebilir, "ortak küme" düşüşü gelmez. Tek sayı basmak bu körlüğü gizlerdi."""
    kosumlar = {"yok": _kosum({"P1": 0.9, "P2": 0.1}),
                "A": _kosum({"P1": 0.9, "P2": 0.1, "P3": 0.0})}
    k = ab.kiyas_kur(kosumlar, 0.05)
    tablo = {r["kod"]: r for r in k["tablo"]}
    assert k["ortak_kume"] == ["P1", "P2"]
    assert tablo["A"]["dusus_kendi_kumesi"] == pytest.approx(0.5 - round(1.0 / 3, 6), abs=1e-6)
    assert tablo["A"]["dusus_ortak_kume"] == pytest.approx(0.0)
    # KART HÜKMÜ İKİ PAYDADA AYRI ÇIKAR: kendi kümesinde "katkı var", ortak kümede YOK.
    assert tablo["A"]["katki_var_kendi"] is True and tablo["A"]["katki_var_ortak"] is False
    assert (tablo["A"]["n_iyilesen"], tablo["A"]["n_kotulesen"]) == (0, 0)


def test_D3_GERCEK_dususte_iki_payda_da_duser():
    kosumlar = {"yok": _kosum({"P1": 0.9, "P2": 0.1}), "A": _kosum({"P1": 0.2, "P2": 0.1})}
    tablo = {r["kod"]: r for r in ab.kiyas_kur(kosumlar, 0.05)["tablo"]}
    assert tablo["A"]["dusus_kendi_kumesi"] == pytest.approx(0.35)
    assert tablo["A"]["dusus_ortak_kume"] == pytest.approx(0.35)
    assert tablo["A"]["katki_var_kendi"] is True and tablo["A"]["katki_var_ortak"] is True
    assert (tablo["A"]["n_iyilesen"], tablo["A"]["n_kotulesen"]) == (1, 0)


def test_D3_ZIT_yonlu_degisim_ortalamada_YUTULMAZ():
    """Eşit ve zıt iki değişim ortalamayı hiç oynatmaz; yön sayacı ikisini de gösterir."""
    kosumlar = {"yok": _kosum({"P1": 0.4, "P2": 0.2}), "A": _kosum({"P1": 0.2, "P2": 0.4})}
    tablo = {r["kod"]: r for r in ab.kiyas_kur(kosumlar, 0.05)["tablo"]}
    assert tablo["A"]["dusus_ortak_kume"] == pytest.approx(0.0)
    assert (tablo["A"]["n_iyilesen"], tablo["A"]["n_kotulesen"]) == (1, 1)
    assert tablo["A"]["katki_var_ortak"] is False


# ==================================================================================================
# D4 — PK DÜŞTÜYSE RAPOR SAYI BASMAZ
# ==================================================================================================
def test_D4_yayin_engeli_varken_rapor_HICBIR_TABLOYU_basmaz():
    sonuc = {
        "kart": ab.KART, "selef": ab.SELEF, "olculdu_utc": "2026-09-13T00:00:00+00:00",
        "yayin_engeli": ["PK (3) TERS KONTROL DÜŞTÜ"], "bastirilan": list(ab.BASTIRILAN),
        "pk": {"sentetik": {"gecti": True, "sapan": []},
               "taban": {"gecti": True, "artefakt": "x", "meta_farklari": [],
                         "izdusum_sha256": {"donmus": "a" * 16, "yeniden": "b" * 16}},
               "ters": {"gecti": False, "taban_ort_mutlak": 0.29, "ters_ort_mutlak": 0.29,
                        "artis": 0.0, "inkar_edilen_cikis_karari": 0, "manage_cagrisi": 0}},
        "kaynak_dokunulmadi": {"gecti": True, "sonra": {"meridian/golge_icra.py": "f" * 64}},
        "girdi": {"dosya_goreli": "g", "sha256": "c" * 64}, "girdi_cekim_utc": "x",
        "parametre_kaynagi": {"sinif": "canli_v5_donmus", "yol_goreli": "p",
                              "sha256": {"strategy.yaml": "d" * 64}, "strategy_version": 5,
                              "kimlik_kapisi": "k"},
        "bar_kaynagi": {"dizin_goreli": "b", "etiket": "state/bars",
                        "son_seans": {"sembol_son_seans_min": "x", "sembol_son_seans_max": "y"}},
        "rejim_kapisi": {"kullanilan": "meridian.regime.regime_ok"}, "motor_yolu": "m",
        "seans_tavani": 120,
    }
    md = ab.rapor_metni(sonuc)
    assert "SAYI YAYILMAZ" in md
    for yasak in ("## Ablasyon tablosu", "## ADAY D", "## İşlem başına Δ", "0.29537"):
        assert yasak not in md, yasak
    for ad in ab.BASTIRILAN:
        assert f"`{ad}`" in md, ad


# ==================================================================================================
# D5 — ADAY D: HASSASİYET KAPISI + TOPLAMSAL ÖZDEŞLİK
# ==================================================================================================
def test_D5_R_MULTIPLE_ALT_altinda_payda_TURETILMEZ():
    """Sıfır ile "bilmiyorum" aynı şey değildir: hassasiyetsiz payda `None` + ADLI neden."""
    import sayim
    secilen = [{"plan_id": "P1", "ticker": "X", "r_multiple": 0.009, "qty": 10,
                "pnl_dollars": -3.79, "entry": 100.0, "exit": 99.6}]
    planlar = {"P1": {"stop": 95.0, "entry_trigger": 101.0}}
    d = ab.tani_d(secilen, planlar)[0]
    assert d["turetilen_risk_mesafesi"] is None
    assert str(sayim.R_MULTIPLE_ALT) in d["turetilemedi"]


def test_D5_oran_IKI_PAYDADAN_ve_ozdeslik_TUTAR():
    """Δ = Δ_payda + Δ_fiyat özdeşliği: kalan fark sınıfı bir beyan değil bir ÖLÇÜM."""
    secilen = [{"plan_id": "P1", "ticker": "VRTX", "r_multiple": -2.277, "qty": 38,
                "pnl_dollars": -1139.82, "entry": 559.3704, "exit": 529.3752}]
    planlar = {"P1": {"stop": 530.3365, "entry_trigger": 557.02}}
    d = ab.tani_d(secilen, planlar)[0]
    assert d["turetilen_risk_mesafesi"] == pytest.approx(13.1732, abs=1e-3)
    assert d["oran_giris"] == pytest.approx(29.0339 / 13.1732, abs=1e-3)
    assert d["oran_tetik"] == pytest.approx(26.6835 / 13.1732, abs=1e-3)
    assert d["oran_giris"] != d["oran_tetik"]

    sonuc = {"islemler": [{"plan_id": "P1", "ticker": "VRTX", "golge_r": -1.011391,
                           "fark_r": 1.265609}]}
    a = ab.ayrisma_tablosu([d], sonuc)[0]
    assert a["ozdeslik_tuttu"] is True, a
    # PAYDA baskın: VRTX'in farkının ezici kısmı fiyat yolundan DEĞİL paydadan gelir.
    assert abs(a["delta_payda"]) > abs(a["delta_fiyat"])
    # ÖZDEŞLİK GERÇEKTEN SINANIYOR MU: tutmayan bir girdi `False` vermeli, yoksa sütun bir
    # SÜSTÜR ve ayrışmanın toplamsallığı denetlenmemiş bir iddia olarak kalırdı.
    bozuk = ab.ayrisma_tablosu([d], {"islemler": [
        {"plan_id": "P1", "ticker": "VRTX", "golge_r": -1.011391, "fark_r": 0.5}]})[0]
    assert bozuk["ozdeslik_tuttu"] is False, bozuk


# ==================================================================================================
# C4 — ABLASYON KODU KAPALI KÜMEDEN ÇÖZÜLÜR (alt-dizge DEĞİL)
# ==================================================================================================
def test_C4_kod_KAPALI_KUMEDEN_cozulur_ALT_DIZGE_kod_UYDURAMAZ():
    """`"C" in kod` alt-dizge testi ADI OLMAYAN bir koda da bacak açardı (ör. `"CB"` → B+C).

    Kapalı küme iki şeyi birden zorlar: (1) `TERS_KODU` içindeki "C" harfi BİLİNÇLİ olarak
    C-zincirini açar ve bu artık bir harf tesadüfü değil bir KAYITTIR; (2) kümede olmayan kod
    sessizce koşmaz, `Blok` atar. Davranış tur-1 ile BİREBİR aynıdır — aşağıdaki yüzey kümeleri
    tur-1'in committed künyesinden (`enjeksiyon_kunyesi.sarmalanan_yuzeyler`) alınmıştır.
    """
    # TEK KAYNAK ÇİVİSİ: kod listesi iki yerde yaşıyor (ABLASYONLAR + BACAKLAR) — ayrışırsa burada kırılır.
    assert set(ab.BACAKLAR) == set(ab.ABLASYONLAR) | {ab.TERS_KODU}
    assert ab.BACAKLAR["yok"] == frozenset()
    assert ab.BACAKLAR["ABC"] == frozenset({"A", "B", "C"})
    assert ab.BACAKLAR[ab.TERS_KODU] == frozenset({"C"})

    with pytest.raises(ab.Blok, match="bilinmeyen ablasyon kodu"):
        with ab.ablasyon_kur("CB", {}, _goal()):
            pass

    beklenen = {
        "yok": (),
        "A": ab.SARMALANAN["A"],
        "B": ab.SARMALANAN["B"],
        "C": ab.SARMALANAN["C"],
        "ABC": ab.SARMALANAN["A"] + ab.SARMALANAN["B"] + ab.SARMALANAN["C"],
        ab.TERS_KODU: ab.SARMALANAN[ab.TERS_KODU],
    }
    for kod, yuzeyler in beklenen.items():
        with ab.ablasyon_kur(kod, {}, _goal()) as iz:
            assert sorted(set(iz["sarmalanan"])) == sorted(set(yuzeyler)), kod


# ==================================================================================================
# D6 — BAR KAYNAĞI AYRIŞMASI: `acilis` (donmuş CSV) ↔ `e2.resmi_acilis` (gerçek yol)
# ==================================================================================================
def test_D6_a_izi_RESMI_ACILISI_ve_BPS_yi_TASIR(tmp_path, sandbox_state):
    """`enjeksiyon_haritasi` `resmi_acilis`i ZATEN taşıyordu ama izde TÜKETİLMİYORDU: "bar
    kaynağı" sınıfının kanıtı statik bir cümleydi. Artık iz satırında SAYI durur."""
    girdi, bars = _sahne_tetik_gelmedi(tmp_path)          # giriş barının açılışı 98,0
    enj = {AAPL_PLAN: {"fill": 98.4, "atr": None, "limit": None, "resmi_acilis": 97.9,
                       "gap_at_submit": False, "motor": "ic"}}
    s = _kos(tmp_path, "A", enj=enj, girdi=girdi, bars=bars)
    iz = [x for x in s["ablasyon"]["a_izi"] if x["plan_id"] == AAPL_PLAN][0]
    assert iz["acilis"] == pytest.approx(98.0) and iz["resmi_acilis"] == pytest.approx(97.9)
    assert iz["acilis_vs_resmi_acilis_bps"] == pytest.approx((98.0 - 97.9) / 97.9 * 1e4, abs=1e-3)
    assert iz["bps_olculemedi"] is None


def test_D6_resmi_acilis_YOKSA_bps_NONE_ve_ADLI_NEDEN(tmp_path, sandbox_state):
    """Uydurma yasağı: ölçülemeyen bps 0 DEĞİL `None` + neden. Sıfır "iki kaynak aynı" demektir."""
    girdi, bars = _sahne_tetik_gelmedi(tmp_path)
    enj = {AAPL_PLAN: {"fill": 98.4, "atr": None, "limit": None, "resmi_acilis": None,
                       "gap_at_submit": False, "motor": "ic"}}
    s = _kos(tmp_path, "A", enj=enj, girdi=girdi, bars=bars)
    iz = [x for x in s["ablasyon"]["a_izi"] if x["plan_id"] == AAPL_PLAN][0]
    assert iz["resmi_acilis"] is None and iz["acilis_vs_resmi_acilis_bps"] is None
    assert "resmi_acilis" in (iz["bps_olculemedi"] or ""), iz


def test_D6_REDDEDILEN_planin_iz_satiri_da_BPS_tasir(tmp_path, sandbox_state):
    """Ret satırı alanları taşımazsa tablo sessizce yalnız GİREN işlemleri ölçer — bar kaynağı
    ayrışması ret kararının KENDİSİNİ de (açılış ≤ stop) besleyen bir girdidir."""
    girdi, bars = ab.sentetik_sahne(tmp_path)
    df = pd.read_csv(bars / "aapl.csv")
    df.loc[df.index[-1], ["open", "high", "low", "close"]] = [94.0, 99.0, 93.0, 96.0]
    df.to_csv(bars / "aapl.csv", index=False)
    enj = {AAPL_PLAN: {"fill": None, "atr": None, "limit": None, "resmi_acilis": 93.8,
                       "gap_at_submit": False, "motor": "ic"}}
    s = _kos(tmp_path, "A", enj=enj, girdi=girdi, bars=bars)
    iz = [x for x in s["ablasyon"]["a_izi"] if x["plan_id"] == AAPL_PLAN][0]
    assert iz["red"] == "acilis_stop_altinda" and iz["dolum"] is None
    assert iz["resmi_acilis"] == pytest.approx(93.8)
    assert iz["acilis_vs_resmi_acilis_bps"] == pytest.approx((94.0 - 93.8) / 93.8 * 1e4, abs=1e-3)


def _kf_sahne(a_izi: list) -> tuple[dict, list, dict]:
    """`kalan_fark_sinifi` için EN DAR sahne: iki hüküm çifti, iki payda, bir de A izi."""
    sonuc = {"kontrol": {"ciftler": [{"plan_id": "P1", "fark_r": 0.5, "friksiyon_payi_r": 0.02},
                                     {"plan_id": "P2", "fark_r": -0.2, "friksiyon_payi_r": 0.02}],
                         "ort_mutlak_fark_r": 0.35},
             "parametre_ayrismasi": {"parametre_uyumu": True, "n_ayrisan": 0},
             "ablasyon": {"a_izi": a_izi}}
    tani = [{"plan_id": "P1", "delta_payda": 0.4}, {"plan_id": "P2", "delta_payda": -0.15}]
    return sonuc, tani, {"ort_fark_r_ust": 0.05}


def _iz(pid, ticker, acilis, resmi):
    bps, neden = ab._acilis_bps(acilis, resmi)
    return {"plan_id": pid, "ticker": ticker, "seans": "2026-09-01", "red": None,
            "acilis": acilis, "resmi_acilis": resmi,
            "acilis_vs_resmi_acilis_bps": bps, "bps_olculemedi": neden}


def test_D6_kalan_fark_sinifi_BAR_KAYNAGINI_SAYIYLA_kanitlar():
    """Kartın `basari_tanimi`: "kalan fark sınıfı … hangisi, ÖLÇÜLMÜŞ kanıtla". Madde 3'ün kanıtı
    artık bir cümle değil n/ort/medyan/|ort| + sembol bazlı liste."""
    a_izi = [_iz("P1", "AAA", 100.0, 99.0),        # +101,0101 bps
             _iz("P2", "BBB", 200.0, 201.0),       # −49,7512 bps
             _iz("P3", "CCC", 300.0, 299.7),       # +10,0100 bps
             _iz("P4", "DDD", 50.0, None)]         # ÖLÇÜLEMEZ
    kf = ab.kalan_fark_sinifi(*_kf_sahne(a_izi))
    bk = kf["bar_kaynagi_bps"]

    bps = [101.010101, -49.751244, 10.010010]
    assert bk["n"] == 3 and bk["olculemeyen_n"] == 1
    assert bk["ort_bps"] == pytest.approx(sum(bps) / 3, abs=1e-3)
    # MEDYAN ORTALAMA DEĞİLDİR: tek bir aykırı değer ortalamayı taşır, medyanı taşımaz.
    assert bk["medyan_bps"] == pytest.approx(10.010010, abs=1e-3)
    assert bk["medyan_bps"] != pytest.approx(bk["ort_bps"], abs=1e-3)
    assert bk["ort_mutlak_bps"] == pytest.approx(sum(abs(x) for x in bps) / 3, abs=1e-3)
    assert [r["ticker"] for r in bk["sembol_bazli"]] == ["AAA", "BBB", "CCC"]   # |bps| azalan
    assert bk["olculemeyen_nedenler"] and all(bk["olculemeyen_nedenler"])

    sin = {x["sinif"].split(" (")[0]: x for x in kf["siniflar"]}
    bar = next(v for k, v in sin.items() if k.startswith("bar kaynağı"))
    assert "10.01" in bar["kanit"] and str(bk["n"]) in bar["kanit"], bar["kanit"]
    assert len(bar["sembol_bazli_bps"]) == 3


def test_D6_madde2_ile_madde3_AYNI_delta_fiyati_PAYLASTIGINI_soyler():
    """Ayrıştırılamayan pay "ölçüldü" gibi sunulmaz: iki sınıf da AYNI `delta_fiyat` sayısını
    taşır ve payları `None` + ADLI nedenle durur."""
    kf = ab.kalan_fark_sinifi(*_kf_sahne([_iz("P1", "AAA", 100.0, 99.0)]))
    paylasan = [x for x in kf["siniflar"] if x.get("paylasilan_sayi")]
    assert len(paylasan) == 2, [x["sinif"] for x in paylasan]
    adlar = {x["sinif"] for x in paylasan}
    for x in paylasan:
        assert x["paylasilan_sayi"] == "delta_fiyat"
        assert x["paylastigi_sinif"] in adlar - {x["sinif"]}
        assert x["ayrisan_pay_r"] is None
        assert "ölçülemedi" in x["ayrisan_pay_neden"] and "ayrışmaz" in x["ayrisan_pay_neden"]
    # PAYDA sınıfı ile PARAMETRE sınıfı bu paylaşımın DIŞINDADIR (dört sınıf tek torbaya girmez).
    assert [x.get("paylasilan_sayi") for x in kf["siniflar"]] == [None, "delta_fiyat",
                                                                  "delta_fiyat", None]


def test_D6_A_izi_BOSSA_bar_kaynagi_OLCULEMEDI_der_SIFIR_demez():
    kf = ab.kalan_fark_sinifi(*_kf_sahne([]))
    bk = kf["bar_kaynagi_bps"]
    assert (bk["n"], bk["ort_bps"], bk["medyan_bps"], bk["ort_mutlak_bps"]) == (0, None, None, None)
    assert bk["olculemedi_neden"]
    bar = next(x for x in kf["siniflar"] if x["sinif"].startswith("bar kaynağı"))
    assert "ÖLÇÜLEMEDİ" in bar["kanit"]


# ==================================================================================================
# ÇAPA YASASI — satır çapası yok (v401/v402 ile aynı yasa, ölçüm dosyasında da)
# ==================================================================================================
def test_capa_yasasi_olcum_dosyasinda_SATIR_CAPASI_yok():
    import re
    for yol in (EDG090 / "ablasyon.py", pathlib.Path(__file__)):
        metin = yol.read_text(encoding="utf-8")
        assert not re.findall(r"[A-Za-z_/.]+\.py:[0-9]+", metin), yol.name
