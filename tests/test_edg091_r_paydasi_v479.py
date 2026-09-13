"""EDG-2026-091 CANLI R PAYDASI ÖLÇÜMÜNÜN ÇİVİLERİ — `research/olcumler/edg091_r_paydasi/olc.py`.

NE ÇİVİLER. Kartın (`research/cards/EDG-2026-091-canli-r-paydasi-kaynagi.yaml`) ölçüm yüzeyini:
payda türetiminin TEK yüklemi, ölçülemezliğin ADLI olması, sıkılaştırma olayının olayın KENDİ
alanlarından ölçülmesi, 2×2 tablonun "0 olay" ile "ölçülemedi"yi AYIRMASI, donmuş girdinin
manifestosu ve canlı `state/`e yazım olmaması. Betik HÜKÜM YAZMAZ (kart hükmü Rol-1'in) — çivi de
hüküm ölçmez, ölçüm yüzeyinin dürüstlüğünü ölçer.

ÇİVİLERİN HEDEF DALLARI (her biri mutasyonla ısırdığı gösterildi — rapor §Mutasyon kanıtları):
  A1 donmuş girdinin SHA256SUMS manifestosu (kill#3) · A2 `R_MULTIPLE_ALT` EDG-088'den İTHAL
  (tek-kaynak: burada yeniden yazılmaz) ve sıfır-R kümesi ADLI nedenle düşer · A3 plansız işlemde
  plan riski None + neden, TÜRETME YOK · B1 sentetik üç sahnenin oranı EL HESABIYLA birebir ·
  B2 kill#4 (PK düşerse hiçbir sayı yayılmaz, dosya yazılmaz) · C1 2×2 hücre toplamı = n_oran ve
  sıkılaştırma ÜÇ DEĞERLİ · C2 sıkılaştırma ölçütü olayın kendi `from_stop`/`to_stop` alanları ·
  C3 kod-okuması çapaları YAŞIYOR (sembol kaynakta gerçekten tanımlı) · C4 canlı `state/` ağacına
  yazım YOK + kapı gevşetilemez · C5 komut satırı sözleşmesi (`main()` değil KOMUT SATIRI).

SENTETİK SAHNE NEDEN SAF ARİTMETİK. `pk1_sentetik` motoru hiç çağırmaz: sayılar el hesabıdır
(giriş 100 · stop 90 · çıkış 80 · qty 20 …), yani çivi "motorun bugünkü davranışını" değil
FORMÜLÜ doğrular. Motorun davranışı ayrı bir yüzeydir ve kod-okuması çapalarıyla (C3) ölçülür.
"""
from __future__ import annotations

import json
import pathlib
import shutil
import sys

import pytest

KOK = pathlib.Path(__file__).resolve().parents[1]
OLCUM = KOK / "research" / "olcumler" / "edg091_r_paydasi"
EDG088 = KOK / "research" / "olcumler" / "edg088_golge_pilot"
for _p in (str(EDG088), str(OLCUM), str(KOK)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import olc  # noqa: E402
import sayim  # noqa: E402  — EDG-088 sayım modülü: `R_MULTIPLE_ALT`ın TEK kaynağı

DONMUS = OLCUM / "girdi" / "a1_cekim_2026-09-13.json"
DONMUS_SHA = OLCUM / "girdi" / "SHA256SUMS"

#: DONUK BEKLENTİLER — donmuş çekimin kendisinden (kart `veri_penceresi`: pencere BÜYÜMEZ).
#: Sayı değişirse girdi değişmiş demektir ve çivi bunu SÖYLER (sessizce uyum sağlamaz).
N_ISLEM = 24
N_PLANSIZ = 5
SIFIR_R_ISLEMLER = {"T00892", "T00896", "T00899", "T00901"}   # |r_multiple| < R_MULTIPLE_ALT


@pytest.fixture()
def kosum(tmp_path):
    """Ölçümü GEÇİCİ bir çıktı dizininde koşar (canlı defter yoluna hiç dokunulmaz)."""
    tam, yol = olc.kos(DONMUS, tmp_path / "cikti", tmp_path / "sanal_kok" / "state", DONMUS_SHA)
    return tam, yol


# ==================================================================================================
# A — GİRDİ, EŞİK, ÖLÇÜLEMEZLİK
# ==================================================================================================
def test_a1_manifesto_tutmazsa_blok(tmp_path):
    """kill#3: donmuş girdinin SHA256'sı manifestoyla tutmuyorsa ölçüm BAŞLAMAZ."""
    bozuk = tmp_path / DONMUS.name
    ham = json.loads(DONMUS.read_text(encoding="utf-8"))
    ham["trades"] = ham["trades"][:3]                      # içerik değişti → sha değişti
    bozuk.write_text(json.dumps(ham, ensure_ascii=False), encoding="utf-8")
    shutil.copy(DONMUS_SHA, tmp_path / "SHA256SUMS")
    with pytest.raises(olc.Blok) as e:
        olc.olc(bozuk, tmp_path / "SHA256SUMS", 0.02)
    assert "SHA256" in str(e.value)
    # manifestoda satır HİÇ yoksa da durur — "dosya adı yok" sessizce geçilmez
    (tmp_path / "bos").write_text("deadbeef  baska_dosya.json\n", encoding="utf-8")
    with pytest.raises(olc.Blok):
        olc.olc(DONMUS, tmp_path / "bos", 0.02)


def test_a2_r_multiple_alt_edg088den_ithal_ve_sifir_r_adli_neden(kosum):
    """TEK-KAYNAK: eşik burada yeniden YAZILMAZ, `sayim.R_MULTIPLE_ALT`tan gelir.

    Kanıt iki yönlü: (a) künyedeki değer ile modülün değeri AYNI nesneden, (b) eşiği yukarı
    çekince ölçülemeyen küme BÜYÜR — yani betik gerçekten o sabiti okuyor, kendi kopyasını değil.
    """
    tam, _ = kosum
    assert tam["r_multiple_alt"] == pytest.approx(float(sayim.R_MULTIPLE_ALT))
    assert tam["r_multiple_alt_kaynagi"].endswith("sayim.py::R_MULTIPLE_ALT")
    # betik kendi literalini taşımıyor (ikinci kopya = sessiz ayrışma)
    kaynak = (OLCUM / "olc.py").read_text(encoding="utf-8")
    assert "R_MULTIPLE_ALT = " not in kaynak

    dusenler = {i["id"] for i in tam["islemler"] if i["payda_turetilen"] is None
                and i["r_multiple"] is not None}
    assert dusenler == SIFIR_R_ISLEMLER
    for i in tam["islemler"]:
        if i["id"] in SIFIR_R_ISLEMLER:
            assert i["payda_olculemedi_neden"] and "R_MULTIPLE_ALT" in i["payda_olculemedi_neden"]
            assert i["oran"] is None                 # ölçülemeyen paydadan oran UYDURULMAZ

    # eşiği yükselt → küme büyümeli (sabit gerçekten okunuyor)
    buyuk = olc.payda_turet({"r_multiple": -1.083, "pnl_dollars": -420.49, "qty": 33}, 2.0)
    assert buyuk[0] is None and "R_MULTIPLE_ALT" in buyuk[1]


def test_a3_plansiz_islem_none_artı_neden(kosum):
    """Plan satırı olmayan işlemde plan riski TÜRETİLMEZ: None + ADLI neden (uydurma yasağı)."""
    tam, _ = kosum
    plansiz = [i for i in tam["islemler"] if i["plan_riski"] is None]
    assert len(plansiz) == N_PLANSIZ and tam["kapi"]["n_plansiz"] == N_PLANSIZ
    for i in plansiz:
        assert i["plan_riski_olculemedi_neden"]
        assert "plan satırı" in i["plan_riski_olculemedi_neden"]
        assert i["oran"] is None and i["giris_riski"] is None
    assert tam["kapi"]["n_islem"] == N_ISLEM


# ==================================================================================================
# B — POZİTİF KONTROLLER
# ==================================================================================================
def test_b1_sentetik_oran_el_hesabiyla(kosum):
    """PK (1): temiz sahne 1,000 · sıkılaştırılmış payda 0,500 · bütçe+yuvarlama 1,035."""
    tam, _ = kosum
    sahne = {s["ad"]: s for s in tam["pk"]["pk1_sentetik"]["sahneler"]}
    assert sahne["temiz"]["oran_ham"] == pytest.approx(1.0, abs=1e-9)
    assert sahne["siklastirilmis_payda"]["oran_ham"] == pytest.approx(0.5, abs=1e-9)
    assert sahne["butce_asagi_yuvarlama"]["oran_ham"] == pytest.approx(1.035, abs=1e-9)
    assert tam["pk"]["pk1_sentetik"]["gecti"] is True
    # payda formülü gerçekten |pnl/(r·qty)| — temiz sahnede plan riskine EŞİT
    assert sahne["temiz"]["payda_ham"] == pytest.approx(sahne["temiz"]["plan_riski"], abs=1e-9)


def test_b2_pk_dusunce_hicbir_sayi_yayilmaz(tmp_path, monkeypatch):
    """kill#4: bir PK ayağı düşerse `PKDustu` atılır ve sonuç dosyası YAZILMAZ."""
    cikti = tmp_path / "cikti"
    monkeypatch.setattr(olc, "pk1_sentetik", lambda r_alt: {"sahneler": [], "gecti": False})
    with pytest.raises(olc.PKDustu):
        olc.kos(DONMUS, cikti, tmp_path / "sanal_kok" / "state", DONMUS_SHA)
    assert not cikti.exists() or not list(cikti.glob("sonuc_*.json"))


def test_b2b_pk2_kartin_dort_on_olcumunu_uretir(kosum):
    """PK (2): kartın üst yorumundaki dört sayı betikle ±0,01 içinde yeniden üretilir."""
    tam, _ = kosum
    pk2 = tam["pk"]["pk2_gercek"]
    assert pk2["gecti"] is True
    assert {s["ticker"] for s in pk2["satirlar"]} == set(olc.PK2_BEKLENEN)
    for s in pk2["satirlar"]:
        bek = olc.PK2_BEKLENEN[s["ticker"]]
        assert abs(s["payda_olculen"] - bek["payda"]) <= olc.PK_TOLERANS
        assert abs(s["plan_riski_olculen"] - bek["plan_riski"]) <= olc.PK_TOLERANS


def test_b3_pk3_golge_ayagi_tam_bir_verir(kosum):
    """PK (3a): gölge yolunda payda TANIMI GEREĞİ giriş riskidir → oran 1,000 (±0,01)."""
    tam, _ = kosum
    pk3 = tam["pk"]["pk3_capraz"]
    assert pk3["golge"] and all(s["gecti"] for s in pk3["golge"])
    for s in pk3["golge"]:
        assert abs(s["oran"] - 1.0) <= olc.PK_TOLERANS
    # replay bandı VARSAYILMAZ: yuvarlama adımı defterden ölçülür
    assert pk3["r_ulp_olculen"] == pytest.approx(1e-3)
    assert all("turetilmis_bant" in s for s in pk3["replay"] if s.get("gecti") is not None
               and "neden" not in s)


# ==================================================================================================
# C — TABLO, OLAY SÖZLÜĞÜ, ÇAPA, STATE, KOMUT SATIRI
# ==================================================================================================
def test_c1_2x2_hucreleri_ve_uc_degerli_siklastirma(kosum):
    """2×2 hücre toplamı oranı ölçülen işlem sayısına EŞİT; '0 olay' ile 'ölçülemedi' AYRI."""
    tam, _ = kosum
    h = tam["tablo_2x2"]["hucreler"]
    assert sum(h.values()) == tam["kapi"]["n_oran"]
    assert set(h) == {"bant_disi_sik", "bant_disi_sik_yok", "bant_disi_sik_olculemedi",
                      "bantta_sik", "bantta_sik_yok", "bantta_sik_olculemedi"}
    # üç değerli alan: True / False / None — False'un nedeni "0 olay" demeli, "ölçülemedi" değil
    for i in tam["islemler"]:
        v = i["siklastirma"]["var"]
        assert v in (True, False, None)
        if v is False:
            assert "0 olay" in i["siklastirma"]["neden"]
    n_bd = tam["birincil"]["n_bant_disi"]
    if n_bd:
        assert tam["tablo_2x2"]["eslesme_orani"] == pytest.approx(h["bant_disi_sik"] / n_bd)
    else:
        assert tam["tablo_2x2"]["eslesme_neden"]


def test_c2_siklastirma_olayin_kendi_alanlarindan_olculur():
    """Trail olayı ancak `to_stop > from_stop` ise SIKILAŞTIRMAdır; ad tek başına yetmez."""
    yukari = [{"ts": "2026-08-20T20:00:00+00:00", "event": olc.TRAIL_OLAYI, "ticker": "X",
               "from_stop": 100.0, "to_stop": 110.0}]
    asagi = [{**yukari[0], "to_stop": 90.0}]
    alansiz = [{"ts": "2026-08-20T20:00:00+00:00", "event": olc.TRAIL_OLAYI, "ticker": "X"}]
    disarida = [{**yukari[0], "ts": "2026-07-01T20:00:00+00:00"}]
    assert olc.siklastirma_bul(yukari, "X", "2026-08-19", "2026-08-25", 95.0)["var"] is True
    assert olc.siklastirma_bul(asagi, "X", "2026-08-19", "2026-08-25", 95.0)["var"] is False
    assert olc.siklastirma_bul(alansiz, "X", "2026-08-19", "2026-08-25", 95.0)["var"] is None
    assert olc.siklastirma_bul(disarida, "X", "2026-08-19", "2026-08-25", 95.0)["var"] is False
    # koruma OCO'su plan stopunun ÜSTÜNDEyse sıkılaştırma, ALTINDA/eşitse ilk koruma kurulumu
    koruma = [{"ts": "2026-08-20T16:00:00+00:00", "event": "koruma_oco_gonderildi",
               "ticker": "X", "stop": 97.0}]
    assert olc.siklastirma_bul(koruma, "X", "2026-08-19", "2026-08-25", 95.0)["var"] is True
    assert olc.siklastirma_bul(koruma, "X", "2026-08-19", "2026-08-25", 99.0)["var"] is False
    assert olc.siklastirma_bul(koruma, "X", "2026-08-19", "2026-08-25", None)["var"] is None


def test_c3_kod_okumasi_capalari_yasiyor(kosum):
    """ADIM-0 (1) tablosundaki her ÇAPA gerçekten var olan bir tanımı gösteriyor.

    `.md`'de çürüyen bir çapa sessizdir; burada çürürse test kırmızıya döner. Çapa SEMBOLdür
    (satır değil): dosyada `def <ad>` / `class <ad>` aranır.
    """
    tam, _ = kosum
    tanimlar = tam["payda_tanimlari"]
    assert set(tanimlar) == {"canli", "golge", "replay"}
    for yol, kayit in tanimlar.items():
        dosya = KOK / kayit["dosya"]
        assert dosya.exists(), (yol, kayit["dosya"])
        metin = dosya.read_text(encoding="utf-8")
        for sembol in kayit["semboller"]:
            ad = sembol.split(".")[-1]
            assert f"def {ad}(" in metin or f"class {ad}" in metin, (yol, sembol)
        assert kayit["capa"].startswith(kayit["dosya"] + "::")
        # ÇAPA ile SEMBOL listesi AYRIŞAMAZ: çapanın gösterdiği ad listede olmak zorunda,
        # yoksa çürüyen bir çapa (bir harf fazla) sessizce geçerdi.
        assert kayit["capa"].split("::", 1)[1] in kayit["semboller"], kayit["capa"]
    # `_adet_benimse` ayrışmanın ADIdır — motorda gerçekten var olmalı
    assert "def _adet_benimse(" in (KOK / "meridian" / "loop.py").read_text(encoding="utf-8")
    adlar = {a["ad"] for a in tam["payda_ayrismalari"]}
    assert "adet_benimseme" in adlar and "birim_ayrismasi" in adlar


def test_c4_canli_state_agacina_yazim_yok(tmp_path):
    """Ölçüm canlı `state/` ağacını DEĞİŞTİRMEZ ve kapı gevşetilemez."""
    canli = KOK / "state"
    once = sorted((p.name, p.stat().st_mtime_ns, p.stat().st_size)
                  for p in canli.rglob("*") if p.is_file())
    olc.kos(DONMUS, tmp_path / "cikti", tmp_path / "sanal_kok" / "state", DONMUS_SHA)
    sonra = sorted((p.name, p.stat().st_mtime_ns, p.stat().st_size)
                   for p in canli.rglob("*") if p.is_file())
    assert once == sonra
    # kapı: state dizini deponun `state/` ağacının ALTINDA olamaz
    with pytest.raises(olc.Blok):
        olc.kos(DONMUS, tmp_path / "cikti2", canli / "gecici", DONMUS_SHA)


def test_c5_komut_satiri_sozlesmesi(tmp_path, capsys):
    """Sözleşme KOMUT SATIRIdır: bayraklar gerçekten etkir, çıkış kodları ayrışır."""
    cikti = tmp_path / "cikti"
    rc = olc.main(["--girdi", str(DONMUS), "--sha-dosya", str(DONMUS_SHA),
                   "--cikti-dizin", str(cikti),
                   "--state-dizin", str(tmp_path / "sanal_kok" / "state")])
    assert rc == 0
    yazilan = list(cikti.glob("sonuc_*.json"))
    assert len(yazilan) == 1
    cikti_metni = capsys.readouterr().out
    assert "ADIM-0 kapısı" in cikti_metni and str(yazilan[0]) in cikti_metni
    # manifesto yokken çıkış 1 (Blok) — sessiz 0 DEĞİL
    assert olc.main(["--girdi", str(DONMUS), "--sha-dosya", str(tmp_path / "yok"),
                     "--cikti-dizin", str(tmp_path / "c3"),
                     "--state-dizin", str(tmp_path / "sanal_kok" / "state")]) == 1


def test_c6_kapi_ve_birincil_ic_tutarli(kosum):
    """Kapı sayısı oranı ölçülen işlem sayısıyla, bant sayıları toplamla tutarlı."""
    tam, _ = kosum
    oranli = [i for i in tam["islemler"] if i["oran"] is not None]
    assert tam["kapi"]["n_oran"] == len(oranli)
    assert tam["kapi"]["gecti"] is (len(oranli) >= olc.N_ORAN_ALT)
    b = tam["birincil"]
    assert b["n_bantta"] + b["n_bant_disi"] == len(oranli)
    for i in oranli:
        assert i["oran_bantta"] is (olc.ORAN_BANT[0] <= i["oran"] <= olc.ORAN_BANT[1])
    assert tam["hukum"].startswith("YOK")          # hükmü Rol-1 yazar, betik değil
