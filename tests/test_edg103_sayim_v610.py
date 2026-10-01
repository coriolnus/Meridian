"""tests/test_edg103_sayim_v610.py — EDG-2026-103 SAYIM ALETİ: K1–K4, D, PK/NK, kill-list (sayım kodu).

NUMARA: `ls tests | grep _v610` boş (2026-10-01, bu ağaçta ve diğer worktree'lerde ölçüldü; v609
`tsk260-yazim-yolu` ağacında alınmış).

NE ÖLÇÜLÜR. `research/olcumler/edg103_okuma_ilgi_atif/sayim.py` (saf hesap; dondurulmuş girdi dizinini
okur) ve `dondur.py` (Rol-1'in checkout'unda girdiyi dondurur; git'e YALNIZ salt-okur). Tanımlar kartın
donmuş alanlarından + `netlestirme_2026_10_01`den gelir; çiviler o tanımların SINIRLARINI ısırır:
  A  gerçek kart okunur: τ, W, pencere, eşikler, PK/NK, kill-list KARTTAN (sabit kopya yok)
  B  K1: S = pencereyle kesişen UTC takvim günü; okumasız gün, aynı gün iki okuma, kısmi okuma, etiket/yer tutucu
  C  pencere sınırları [10:33:10Z, +7 g) — okuma ve karar için
  D  W = 48 sa (0 ≤ Δ < W; tam 48 sa DIŞARIDA), τ = 0,15 (J ≥ τ; tam 0,15 İÇERİDE)
  E  K3 ve K4 (payda D; D_ilgili yalnız betimleyici; 'taze' ölçülemez → üst sınır)
  F  PK/NK: tutmazsa "GEÇERSİZ — alet doğrulanmadı", sayılar yalnız betimleyici + "hüküm DEĞİL"
  G  PK/NK tutarsa üç türlü kolon sonucu (GEÇTİ/KALDI/ÖLÇÜLEMEDİ) + D<n_min
  H  kart τ/W değişirse OKUNAN değer kullanılır; açılıştan sonra değiştiyse kill #8
  I  diğer kill maddeleri (#1, #4, #5, #7) + pencere kapanmadı + girdi bütünlüğü
  J  dondur.py: sentetik git deposunda giriş commit'i damgası, sentetik işaret, eksik sayfa
  K  `meridian` İTHAL EDİLMEZ (obs'a ulaşmaz): statik + operatör biçiminde alt süreç (`-X importtime`)

HER KOŞUM ALT SÜREÇTİR (sözleşme KOMUT SATIRIdır) ve `-B` ile: betikler `ops/`u ithal yoluna kendileri
ekler; test sürecine `sys.path` mutasyonu sızmasın, mutasyon turunda bayat pyc oluşmasın (v334 sınıfı).
GERÇEK DEPOYA ve A1'e DOKUNULMAZ: girdi dizinleri `tmp_path` altında kurulur; `dondur.py` testi kendi
sentetik git deposunu kurar (v547 deseni).
"""
from __future__ import annotations

import ast
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys

import pytest

from tests.conftest import betikten_modul_yukle

KOK = pathlib.Path(__file__).resolve().parents[1]
DIZIN = KOK / "research" / "olcumler" / "edg103_okuma_ilgi_atif"
SAYIM = DIZIN / "sayim.py"
DONDUR = DIZIN / "dondur.py"
KART = KOK / "research" / "cards" / "EDG-2026-103-hafiza-sayfa-okuma-ilgi-atif.yaml"
OKUMA_MODUL = KOK / "deploy" / "hindsight" / "hafiza_okuma_kaydi.py"

UTC = dt.timezone.utc
PENCERE_BAS = dt.datetime(2026, 9, 25, 10, 33, 10, tzinfo=UTC)
PENCERE_SON = dt.datetime(2026, 10, 2, 10, 33, 10, tzinfo=UTC)
PK_NK_ZAMANI = dt.datetime(2026, 9, 25, 10, 44, 38, tzinfo=UTC)
GECERSIZ_ALET = "GEÇERSİZ — alet doğrulanmadı"

#: PK sayfası: PK karar metninin 16 tokenından 13'ünü taşır → J(PK)=13/16, J(NK)=3/23 (< 0,15).
PK_SAYFASI = ("Meridian hedef sapma. EDG-103 penceresi bugün açılır kararı; zihin modeli kaynak "
              "tazeleme.")
NK_SAYFASI = "# Kripto Madencilik — Bankada Yok\n\n**Bankada bilgi yok.**"
#: K2 sınır çivilerinin sayfası: tam 20 token (tok01…tok20).
TEST_SAYFASI = " ".join(f"tok{i:02d}" for i in range(1, 21))
TEST_TOKENLARI = [f"tok{i:02d}" for i in range(1, 21)]
YABANCI = ["yabanci01", "yabanci02", "yabanci03"]


@pytest.fixture(scope="module")
def okm():
    return betikten_modul_yukle(OKUMA_MODUL, ad="hafiza_okuma_kaydi_v610")


def _an(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(UTC)


def _satir(okm, ts, *, kimlik="test-sayfa", etiket=None, icerik="gerçek içerik", http=200,
           tazeleme="2026-09-24T18:56:24Z", kip="sayfa", ad=None, sure_s=0.4):
    ortam = {"HAFIZA_OKUMA_ETIKET": etiket} if etiket else {}
    return okm.satir_kur(betik="sayfa_oku", kip=kip, sure_s=sure_s, kimlik=kimlik, ad=ad or kimlik,
                         tazeleme=tazeleme, http=http, icerik=icerik, ortam=ortam,
                         simdi=_an(ts) if isinstance(ts, str) else ts)


def _varsayilan_okumalar(okm):
    return [
        _satir(okm, "2026-09-25T10:32:05Z", kimlik="meridian-hedef-sapma", etiket="test-atesleme"),
        _satir(okm, "2026-09-25T10:33:08Z", kimlik="meridian-hedef-sapma", etiket="pk"),
        _satir(okm, "2026-09-25T10:33:10Z", kimlik="meridian-hedef-sapma"),
        # pencere kapandıktan SONRA çekilmiş anlık görüntünün kendi kaydı → kayıt pencereyi kapsıyor
        _satir(okm, "2026-10-02T11:00:00Z", kimlik="meridian-hedef-sapma", etiket="olcum-anlik"),
    ]


def _karar(sira_zaman, tokenler=None, atif=None, kimlik=None, sentetik=None, zaman_yok=False):
    return {"zaman": None if zaman_yok else sira_zaman, "tokenler": tokenler or list(YABANCI),
            "atif": atif or [], "kimlik": kimlik, "sentetik": sentetik or []}


def _varsayilan_kararlar():
    return [_karar(f"2026-09-2{g}T12:00:00Z") for g in range(6, 10)] + [_karar("2026-09-30T12:00:00Z")]


def _sayfa_md(kimlik, icerik, tazeleme="2026-10-02T09:00:00Z"):
    return f"# {kimlik} adı · id={kimlik} · v? · tazeleme={tazeleme}\n{icerik}\n"


def _kunye(**ust):
    kunye = {
        "sema": 1, "arac": "research/olcumler/edg103_okuma_ilgi_atif/dondur.py",
        "dondurma_ani": "2026-10-02T11:30:00+00:00", "repo_head": "f" * 40,
        "kart": {"yol": "research/cards/EDG-2026-103-hafiza-sayfa-okuma-ilgi-atif.yaml",
                 "ilk_commit": {"commit": "1" * 40, "zaman": "2026-09-25T08:05:07+00:00"},
                 "acilis_alani": "pencere_acilis_2026_09_25",
                 "acilis_commit": {"commit": "2" * 40, "zaman": PK_NK_ZAMANI.isoformat()}},
        "enstrumantasyon": {"yol": "deploy/hindsight/hafiza_okuma_kaydi.py",
                            "ilk_commit": {"commit": "3" * 40, "zaman": "2026-09-25T09:03:25+00:00"}},
        "kural_0_5": {"anahtar": "sayfa_oku.sh meridian-hedef-sapma",
                      "iz": [{"commit": "4" * 40, "zaman": "2026-09-25T06:00:00+00:00", "adet": 1}]},
        "pk_nk_zamani": PK_NK_ZAMANI.isoformat(),
        "envanter": {"baslangic": "2026-09-18", "bitis": "2026-10-02", "kenar_gun": 7},
    }
    for anahtar, deger in ust.items():
        kunye[anahtar] = deger
    return kunye


def girdi_yaz(dizin: pathlib.Path, okm, *, kart=None, kart_acilis=None, okumalar=None,
              kararlar=None, sayfalar=None, kunye=None, ek_ham_satir=None) -> pathlib.Path:
    """Geçerli bir dondurulmuş girdi dizini kurar (varsayılan senaryoda PK/NK TUTAR)."""
    kart_metni = KART.read_text(encoding="utf-8") if kart is None else kart
    dizin.mkdir(parents=True)
    (dizin / "kart.yaml").write_text(kart_metni, encoding="utf-8")
    # açılış sürümü varsayılan olarak GERÇEK kart: bir test kartı değiştirirse kill #8 kıyası bunu görür
    (dizin / "kart_acilis.yaml").write_text(KART.read_text(encoding="utf-8") if kart_acilis is None
                                            else kart_acilis, encoding="utf-8")
    satirlar = _varsayilan_okumalar(okm) if okumalar is None else okumalar
    ham = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in satirlar)
    if ek_ham_satir:
        ham += ek_ham_satir + "\n"
    (dizin / "okuma.jsonl").write_text(ham, encoding="utf-8")
    kk = _varsayilan_kararlar() if kararlar is None else kararlar
    env_kararlar, zamanlar = [], []
    for i, k in enumerate(kk):
        tarih = (k["zaman"] or "2026-09-27T00:00:00Z")[:10]
        baslik = f"KARAR sentetik {i}"
        env_kararlar.append({"tarih": tarih, "kimlik": k["kimlik"], "baslik": baslik, "kaynaklar": [],
                             "isaretler": ["karar"], "atif_var": bool(k["atif"]),
                             "atif_turleri": sorted(k["atif"]), "konu_tokenleri": sorted(k["tokenler"])})
        zamanlar.append({"sira": i, "tarih": tarih, "kimlik": k["kimlik"], "baslik": baslik,
                         "zaman": None if k["zaman"] is None else _an(k["zaman"]).isoformat(),
                         "zaman_neden": "anahtar tekil değil" if k["zaman"] is None else None,
                         "kaynaklar": [], "sentetik_isaretler": k["sentetik"]})
    (dizin / "karar_envanteri.json").write_text(json.dumps(
        {"sema": 1, "arac": "ops/karar_envanteri.py", "D": len(env_kararlar),
         "kararlar": env_kararlar}, ensure_ascii=False, indent=2), encoding="utf-8")
    (dizin / "karar_zamanlari.json").write_text(json.dumps(
        {"sema": 1, "kararlar": zamanlar}, ensure_ascii=False, indent=2), encoding="utf-8")
    sayfa_dizini = dizin / "sayfalar"
    sayfa_dizini.mkdir()
    sf = {"meridian-hedef-sapma": PK_SAYFASI, "nk-kripto-madencilik": NK_SAYFASI,
          "test-sayfa": TEST_SAYFASI}
    sf.update(sayfalar or {})
    for kimlik, icerik in sf.items():
        if icerik is not None:
            (sayfa_dizini / f"{kimlik}.md").write_text(_sayfa_md(kimlik, icerik), encoding="utf-8")
    (dizin / "kunye.json").write_text(json.dumps(kunye or _kunye(), ensure_ascii=False, indent=2),
                                      encoding="utf-8")
    sha_yaz(dizin)
    return dizin


def sha_yaz(dizin: pathlib.Path) -> None:
    satirlar = []
    for yol in sorted(p for p in dizin.rglob("*") if p.is_file() and p.name != "SHA256.txt"):
        satirlar.append(f"{hashlib.sha256(yol.read_bytes()).hexdigest()}  {yol.relative_to(dizin).as_posix()}")
    (dizin / "SHA256.txt").write_text("\n".join(satirlar) + "\n", encoding="utf-8")


def kos(girdi: pathlib.Path, tmp_path: pathlib.Path, *ek, importtime=False):
    cikti = tmp_path / f"sonuc_{girdi.name}.json"
    md = tmp_path / f"rapor_{girdi.name}.md"
    komut = [sys.executable, "-B", *(["-X", "importtime"] if importtime else []), str(SAYIM),
             "--girdi", str(girdi), "--cikti-json", str(cikti), "--cikti-md", str(md), *ek]
    r = subprocess.run(komut, capture_output=True, text=True, timeout=120, cwd=str(tmp_path))
    veri = json.loads(cikti.read_text(encoding="utf-8")) if r.returncode == 0 and cikti.exists() else None
    return r, veri, (md.read_text(encoding="utf-8") if md.exists() else None)


def sonuc(tmp_path, okm, ad="g", **kw):
    r, veri, md = kos(girdi_yaz(tmp_path / ad, okm, **kw), tmp_path)
    assert r.returncode == 0, r.stderr
    return veri, md


def _kill(veri, no):
    (madde,) = [m for m in veri["kill_list"] if m["no"] == no]
    return madde


# ================================================================================================
# A — gerçek kart okunur; değerler KARTTAN
# ================================================================================================

def test_A1_gercek_kart_cozumlenir_ve_varsayilan_senaryoda_alet_dogrulanir(tmp_path, okm):
    veri, md = sonuc(tmp_path, okm)
    p = veri["parametreler"]
    assert p["tau"] == "3/20" and p["W_saat"] == 48
    assert p["pencere"]["baslangic"] == "2026-09-25T10:33:10+00:00"
    assert p["pencere"]["bitis"] == "2026-10-02T10:33:10+00:00"
    assert p["n_min_karar"] == 5
    assert {k: v["ad"] for k, v in p["esikler"].items()} == {
        "K1": "k1_okuma_kadansi_alt", "K2": "k2_konu_ilgisi_alt", "K3": "k3_atif_orani_alt",
        "K4": "k4_fazlalik_ust"}
    assert p["k4_atif_turleri"] == ["recall", "memory", "kart_benzer"]
    assert veri["pk_nk"]["tuttu"] is True, veri["pk_nk"]
    assert veri["gecerlilik"]["alet_dogrulandi"] is True
    assert [m["no"] for m in veri["kill_list"]] == list(range(1, 9))
    assert all(m["madde"] for m in veri["kill_list"]), "kill maddesi KART metniyle anılmalı"
    assert set(veri["kolonlar"]) == {"K1", "K2", "K3", "K4"}
    assert md and "K1" in md and "PK/NK" in md and "Kill-list" in md


def test_A2_kart_pk_nk_metinleri_kartin_alanindan_okunur(tmp_path, okm):
    veri, _ = sonuc(tmp_path, okm)
    pk = veri["pk_nk"]["pk"]
    assert pk["metin"].startswith("[PK-EDG-103]") and "kaynak: zihin modeli meridian-hedef-sapma" in pk["metin"]
    assert veri["pk_nk"]["nk"]["metin"].startswith("[NK-EDG-103]")
    assert pk["okuma_etiketi"] == "pk" and pk["sayfa"] == "meridian-hedef-sapma"
    assert veri["pk_nk"]["ek_nk"]["sayfa"] == "nk-kripto-madencilik"
    assert veri["pk_nk"]["ek_nk"]["ifade"] == "bankada yok"


# ================================================================================================
# B — K1 gün sayımı (netleştirme (1) ve (7))
# ================================================================================================

def test_B1_K1_gun_sayimi_okumasiz_gun_ayni_gun_iki_okuma_kismi_okuma(tmp_path, okm):
    okumalar = _varsayilan_okumalar(okm) + [
        _satir(okm, "2026-09-26T08:00:00Z"), _satir(okm, "2026-09-26T20:00:00Z"),  # aynı gün iki okuma
        _satir(okm, "2026-09-27T08:00:00Z", etiket="olcum-anlik"),                 # etiketli: sayılmaz
        _satir(okm, "2026-09-28T07:00:00Z", icerik="Generating content..."),       # yer tutucu: sayılmaz
        _satir(okm, "2026-09-29T07:48:00Z", sure_s=0.01),                          # `| head -4` kısmi okuma
        _satir(okm, "2026-09-30T07:00:00Z", http=500, icerik=""),                  # hata: sayılmaz
    ]
    veri, _ = sonuc(tmp_path, okm, okumalar=okumalar)
    k1 = veri["kolonlar"]["K1"]
    assert k1["S_gunleri"] == ["2026-09-25", "2026-09-26", "2026-09-27", "2026-09-28", "2026-09-29",
                               "2026-09-30", "2026-10-01", "2026-10-02"]
    assert k1["dolu_gunler"] == ["2026-09-25", "2026-09-26", "2026-09-29"]
    assert (k1["pay"], k1["payda"], k1["okuma_sayisi"]) == (3, 8, 4)
    assert k1["karsilastirma"] == "KALDI"
    assert "2026-09-26" in k1["dolu_gunler"] and k1["okuma_sayisi"] == 4, "aynı gün iki okuma GÜNÜ bir kez doldurur"
    assert _kill(veri, 3)["kanit"]["sayilmayan_etiketsiz_sayfa_satiri"] == 2
    assert _kill(veri, 7)["kanit"]["etiketli_okuma"] == {"olcum-anlik": 2, "pk": 1, "test-atesleme": 1}


def test_B2_K1_her_gun_doluysa_gecer(tmp_path, okm):
    okumalar = _varsayilan_okumalar(okm) + [
        _satir(okm, f"2026-{a:02d}-{g:02d}T07:30:00Z") for a, g in
        ((9, 26), (9, 27), (9, 28), (9, 29), (9, 30), (10, 1), (10, 2))]
    veri, _ = sonuc(tmp_path, okm, okumalar=okumalar)
    k1 = veri["kolonlar"]["K1"]
    assert (k1["pay"], k1["payda"]) == (8, 8) and k1["karsilastirma"] == "GEÇTİ"


# ================================================================================================
# C — pencere sınırları [bas, son)
# ================================================================================================

def test_C1_pencere_sinirlari_okuma_ve_karar(tmp_path, okm):
    okumalar = [
        _satir(okm, "2026-09-25T10:32:05Z", kimlik="meridian-hedef-sapma", etiket="test-atesleme"),
        _satir(okm, "2026-09-25T10:33:08Z", kimlik="meridian-hedef-sapma", etiket="pk"),
        _satir(okm, "2026-09-25T10:33:09Z"),   # pencere ÖNCESİ
        _satir(okm, "2026-09-25T10:33:10Z"),   # pencere başı DAHİL
        _satir(okm, "2026-10-02T10:33:09Z"),   # son saniye DAHİL
        _satir(okm, "2026-10-02T10:33:10Z"),   # pencere sonu HARİÇ
    ]
    kararlar = [_karar("2026-09-25T10:33:09Z"), _karar("2026-09-25T10:33:10Z"),
                _karar("2026-10-02T10:33:09Z"), _karar("2026-10-02T10:33:10Z")] + [
        _karar(f"2026-09-2{g}T12:00:00Z") for g in (6, 7, 8)]
    veri, _ = sonuc(tmp_path, okm, okumalar=okumalar, kararlar=kararlar)
    k1 = veri["kolonlar"]["K1"]
    assert k1["dolu_gunler"] == ["2026-09-25", "2026-10-02"] and k1["okuma_sayisi"] == 2
    d = veri["D"]
    assert [k["sira"] for k in d["kararlar"]] == [1, 2, 4, 5, 6]
    assert d["deger"] == 5 and d["pencere_disi"] == 2


# ================================================================================================
# D — W ve τ sınırları (tek eşleşme tanımı: `ilgili_mi`)
# ================================================================================================

def test_D1_W_siniri_tam_48_saat_disarida_okuma_oncesi_karar_disarida(tmp_path, okm):
    okumalar = _varsayilan_okumalar(okm) + [_satir(okm, "2026-09-26T00:00:00Z")]
    kararlar = [
        _karar("2026-09-28T00:00:00Z", tokenler=TEST_TOKENLARI),   # 0: Δ = 48 sa tam → DIŞARIDA
        _karar("2026-09-27T23:59:59Z", tokenler=TEST_TOKENLARI),   # 1: Δ = 48 sa − 1 sn → İÇERİDE
        _karar("2026-09-25T23:59:59Z", tokenler=TEST_TOKENLARI),   # 2: okumadan ÖNCE → DIŞARIDA
        _karar("2026-09-26T00:00:00Z", tokenler=YABANCI),          # 3: Δ = 0, ilgisiz
        _karar("2026-09-29T12:00:00Z")]
    veri, _ = sonuc(tmp_path, okm, okumalar=okumalar, kararlar=kararlar)
    assert veri["kolonlar"]["K3"]["D_ilgili"] == [1]
    k2 = veri["kolonlar"]["K2"]
    (oku,) = [o for o in k2["okumalar"] if o["ts"] == "2026-09-26T00:00:00Z"]
    assert oku["zaman_icinde_karar"] == [1, 3], "Δ=0 İÇERİDE, Δ=48 sa ve Δ<0 DIŞARIDA"
    assert oku["eslesen_karar"] == [1]
    # 09-25 10:33:10 okumasının W'si: karar 2 ve 3; 09-26 okumasınınki: 1 ve 3 → 4 çift, 1 eşleşme
    assert (k2["betimleyici_cift_orani"]["pay"], k2["betimleyici_cift_orani"]["payda"]) == (1, 4)


def test_D2_tau_siniri_tam_015_iceride(tmp_path, okm):
    okumalar = _varsayilan_okumalar(okm) + [_satir(okm, "2026-09-26T00:00:00Z")]
    kararlar = [
        _karar("2026-09-26T01:00:00Z", tokenler=TEST_TOKENLARI[:3]),                # J = 3/20 = 0,15
        _karar("2026-09-26T02:00:00Z", tokenler=TEST_TOKENLARI[:3] + YABANCI[:1]),  # J = 3/21 < 0,15
    ] + [_karar(f"2026-09-2{g}T12:00:00Z") for g in (7, 8, 9)]
    veri, _ = sonuc(tmp_path, okm, okumalar=okumalar, kararlar=kararlar)
    assert veri["kolonlar"]["K3"]["D_ilgili"] == [0]
    k2 = veri["kolonlar"]["K2"]
    assert (k2["pay"], k2["payda"]) == (1, 2), "K2 = kararla örtüşen OKUMA / okuma (esikler cümlesi)"
    (oku,) = [o for o in k2["okumalar"] if o["ts"] == "2026-09-26T00:00:00Z"]
    assert oku["en_yuksek_jaccard"] == "3/20"


# ================================================================================================
# E — K3 ve K4 (payda D)
# ================================================================================================

def test_E1_K4_paydasi_D_ve_taze_olculemez_ust_sinir(tmp_path, okm):
    okumalar = _varsayilan_okumalar(okm) + [_satir(okm, "2026-09-26T00:00:00Z")]
    ilgili = TEST_TOKENLARI[:10]
    kararlar = [
        _karar("2026-09-26T01:00:00Z", tokenler=ilgili, atif=["recall"]),            # 0 K4 adayı
        _karar("2026-09-26T02:00:00Z", tokenler=ilgili, atif=["memory"]),            # 1 K4 adayı
        _karar("2026-09-26T03:00:00Z", tokenler=ilgili, atif=["sayfa", "recall"]),   # 2 sayfa SEÇİLDİ
    ] + [_karar(f"2026-09-2{g}T12:00:00Z", atif=["recall"]) for g in (6, 7, 8, 9)] + [
        _karar(f"2026-09-30T1{s}:00:00Z", atif=["recall"]) for s in (0, 1, 2)]
    veri, _ = sonuc(tmp_path, okm, okumalar=okumalar, kararlar=kararlar)
    k = veri["kolonlar"]
    assert veri["D"]["deger"] == 10
    assert k["K3"]["D_ilgili"] == [0, 1, 2]
    assert (k["K3"]["pay"], k["K3"]["payda"]) == (1, 3)
    k4 = k["K4"]
    assert k4["deger"] is None and "is_stale" in k4["neden"]
    assert k4["payda"] == 10
    assert k4["ust_sinir"] == {"pay": 2, "payda": 10, "kesir": "2/10", "deger": 0.2}
    assert k4["karsilastirma"] == "GEÇTİ", "üst sınır ≤ 0,50 → K4 kesin olarak eşiğin altında"
    assert k4["betimleyici_D_ilgili_paydasi"]["payda"] == 3


def test_E2_K4_adaysizsa_kesin_sifir(tmp_path, okm):
    veri, _ = sonuc(tmp_path, okm)
    k4 = veri["kolonlar"]["K4"]
    assert (k4["pay"], k4["payda"], k4["deger"]) == (0, 5, 0.0) and k4["karsilastirma"] == "GEÇTİ"
    k3 = veri["kolonlar"]["K3"]
    assert k3["deger"] is None and k3["karsilastirma"] == "ÖLÇÜLEMEDİ", "D_ilgili boş → 0/0"


# ================================================================================================
# F — PK/NK tutmazsa kill #6 HARFİYEN (netleştirme (6) ve (8))
# ================================================================================================

def _uzun_ilgisiz_pk_sayfasi():
    return PK_SAYFASI + " " + " ".join(f"dolgu{i:03d}" for i in range(200))


def test_F1_PK_b_tutmazsa_GECERSIZ_ve_sayilar_yalniz_betimleyici(tmp_path, okm):
    veri, md = sonuc(tmp_path, okm, sayfalar={"meridian-hedef-sapma": _uzun_ilgisiz_pk_sayfasi()})
    assert veri["pk_nk"]["pk"]["b_ilgi"]["tuttu"] is False
    assert veri["pk_nk"]["tuttu"] is False
    assert veri["hukum"] == GECERSIZ_ALET
    assert "kolonlar" not in veri and "D" not in veri
    b = veri["betimleyici_ara_rapor"]
    assert "hüküm DEĞİL" in b["etiket"]
    assert set(b) == {"etiket", "not", "K1", "D"}, "netleştirme (8): betimleyici yalnız K1 ve D"
    assert "karsilastirma" not in json.dumps(b, ensure_ascii=False)
    assert _kill(veri, 6)["durum"] == "TETİKLENDİ"
    assert "hüküm DEĞİL" in md and GECERSIZ_ALET in md


@pytest.mark.parametrize("bacak", ["a", "c", "nk_atif", "nk_ilgi", "ek_nk"])
def test_F2_her_PK_NK_bacagi_tek_basina_GECERSIZ_yapar(tmp_path, okm, bacak):
    kw = {}
    if bacak == "a":
        kw["okumalar"] = [r for r in _varsayilan_okumalar(okm) if r["etiket"] != "pk"]
    elif bacak == "c":
        metin = KART.read_text(encoding="utf-8")
        assert metin.count("kararı, kaynak: zihin modeli") == 1
        kw["kart"] = metin.replace("kararı, kaynak: zihin modeli", 'kararı, "kaynak: zihin modeli')
    elif bacak == "nk_atif":
        metin = KART.read_text(encoding="utf-8")
        eski = 'yazılır" kararı.'          # kartta "altına" ile "yazılır" arasında satır kırılması var
        assert metin.count(eski) == 1
        kw["kart"] = metin.replace(eski, 'yazılır" kararı, hafıza: recall benzer.')
    elif bacak == "nk_ilgi":
        kw["sayfalar"] = {"meridian-hedef-sapma": PK_SAYFASI + " EDG-102 kuru adımı çıktısı /opt/veri/olcum/"
                                                               "edg102/ altına yazılır"}
    elif bacak == "ek_nk":
        kw["sayfalar"] = {"nk-kripto-madencilik": "# Kripto Madencilik\n\nMadencilik özeti: hash oranı."}
    veri, _ = sonuc(tmp_path, okm, **kw)
    assert veri["pk_nk"]["tuttu"] is False
    assert veri["hukum"] == GECERSIZ_ALET and "kolonlar" not in veri
    yollar = {"a": ("pk", "a_okuma"), "c": ("pk", "c_atif"), "nk_atif": ("nk", "atifsiz"),
              "nk_ilgi": ("nk", "ilgisiz"), "ek_nk": ("ek_nk", None)}
    ust, alt = yollar[bacak]
    dugum = veri["pk_nk"][ust] if alt is None else veri["pk_nk"][ust][alt]
    assert dugum["tuttu"] is False


# ================================================================================================
# G — PK/NK tutarsa üç türlü kolon sonucu; D < n_min
# ================================================================================================

def test_G1_uc_turlu_kolon_sonucu(tmp_path, okm):
    okumalar = _varsayilan_okumalar(okm) + [
        _satir(okm, f"2026-{a:02d}-{g:02d}T07:30:00Z") for a, g in
        ((9, 26), (9, 27), (9, 28), (9, 29), (9, 30), (10, 1), (10, 2))]
    veri, _ = sonuc(tmp_path, okm, okumalar=okumalar)
    sonuclar = {k: v["karsilastirma"] for k, v in veri["kolonlar"].items()}
    assert sonuclar == {"K1": "GEÇTİ", "K2": "KALDI", "K3": "ÖLÇÜLEMEDİ", "K4": "GEÇTİ"}
    assert veri["hukum"].startswith("ALET DOĞRULANDI")
    assert "betimleyici_ara_rapor" not in veri


def test_G2_D_n_min_altinda_dort_kol_olculemedi(tmp_path, okm):
    veri, _ = sonuc(tmp_path, okm, kararlar=_varsayilan_kararlar()[:4])
    assert veri["D"]["deger"] == 4
    for kolon in veri["kolonlar"].values():
        assert kolon["karsilastirma"] == "ÖLÇÜLEMEDİ" and "örnek yetersiz" in kolon["neden"]
    assert _kill(veri, 2)["durum"].startswith("ÖLÇÜLEMEDİ")


# ================================================================================================
# H — τ/W karttan OKUNUR; açılıştan sonra değiştiyse kill #8
# ================================================================================================

def _tau_w_degistir(metin: str) -> str:
    for eski, yeni in (("τ (0.15)", "τ (0.30)"), ("(öneri: 0.15", "(öneri: 0.30"), ("τ=0,15", "τ=0,30"),
                       ("W (48 s)", "W (24 s)"), ("(öneri: 48 s)", "(öneri: 24 s)"), ("W=48 sa", "W=24 sa")):
        assert metin.count(eski) == 1, eski
        metin = metin.replace(eski, yeni)
    return metin


def _tau_w_senaryosu(okm):
    okumalar = _varsayilan_okumalar(okm) + [_satir(okm, "2026-09-26T00:00:00Z")]
    kararlar = [_karar("2026-09-27T06:00:00Z", tokenler=TEST_TOKENLARI[:4]),   # Δ 30 sa, J 0,20
                _karar("2026-09-26T01:00:00Z", tokenler=TEST_TOKENLARI[:7])]   # Δ 1 sa, J 0,35
    return okumalar, kararlar + [_karar(f"2026-09-2{g}T12:00:00Z") for g in (7, 8, 9)]


def test_H1_kart_tau_W_degisirse_okunan_deger_kullanilir(tmp_path, okm):
    okumalar, kararlar = _tau_w_senaryosu(okm)
    once, _ = sonuc(tmp_path, okm, ad="once", okumalar=okumalar, kararlar=kararlar)
    assert once["kolonlar"]["K3"]["D_ilgili"] == [0, 1]
    yeni = _tau_w_degistir(KART.read_text(encoding="utf-8"))
    sonra, _ = sonuc(tmp_path, okm, ad="sonra", okumalar=okumalar, kararlar=kararlar,
                     kart=yeni, kart_acilis=yeni)
    assert sonra["parametreler"]["tau"] == "3/10" and sonra["parametreler"]["W_saat"] == 24
    assert sonra["kolonlar"]["K3"]["D_ilgili"] == [1]
    assert _kill(sonra, 8)["durum"] == "TETİKLENMEDİ"


def test_H2_tau_W_acilistan_sonra_degistiyse_kill8_GECERSIZ(tmp_path, okm):
    veri, _ = sonuc(tmp_path, okm, kart=_tau_w_degistir(KART.read_text(encoding="utf-8")))
    assert _kill(veri, 8)["durum"] == "TETİKLENDİ"
    assert veri["hukum"].startswith("GEÇERSİZ") and "kolonlar" not in veri


def test_H3_kart_ici_tau_tutarsizsa_sayim_yapilmaz(tmp_path, okm):
    metin = KART.read_text(encoding="utf-8").replace("τ=0,15", "τ=0,20")
    r, veri, _ = kos(girdi_yaz(tmp_path / "g", okm, kart=metin, kart_acilis=metin), tmp_path)
    assert r.returncode == 2 and veri is None
    assert "τ" in r.stderr


# ================================================================================================
# I — diğer kill maddeleri, pencere kapanışı, girdi bütünlüğü
# ================================================================================================

def test_I1_kill5_sir_benzeri_okuma_satiri_akisi_kapatir(tmp_path, okm):
    gizli = "Bearer abcdefghijklmnopqrstuvwxyz0123"
    okumalar = _varsayilan_okumalar(okm) + [_satir(okm, "2026-09-27T08:00:00Z", ad=gizli)]
    girdi = girdi_yaz(tmp_path / "g", okm, okumalar=okumalar)
    r, veri, md = kos(girdi, tmp_path)
    assert r.returncode == 0, r.stderr
    assert veri["hukum"].startswith("AKIŞ KAPATILDI")
    assert "kolonlar" not in veri and "betimleyici_ara_rapor" not in veri and "pk_nk" not in veri
    assert _kill(veri, 5)["durum"] == "TETİKLENDİ"
    assert "abcdefghijklmnopqrstuvwxyz0123" not in json.dumps(veri, ensure_ascii=False) + md + r.stdout + r.stderr


def test_I2_kill1_enstrumantasyon_kart_oncesi_GECERSIZ(tmp_path, okm):
    kunye = _kunye(enstrumantasyon={"yol": "deploy/hindsight/hafiza_okuma_kaydi.py",
                                    "ilk_commit": {"commit": "3" * 40, "zaman": "2026-09-25T07:00:00+00:00"}})
    veri, _ = sonuc(tmp_path, okm, kunye=kunye)
    assert _kill(veri, 1)["durum"] == "TETİKLENDİ"
    assert veri["hukum"].startswith("GEÇERSİZ") and "kolonlar" not in veri


def test_I3_kill4_kural_pencerede_kaldirildiysa_K1_KALDI(tmp_path, okm):
    okumalar = _varsayilan_okumalar(okm) + [
        _satir(okm, f"2026-{a:02d}-{g:02d}T07:30:00Z") for a, g in
        ((9, 26), (9, 27), (9, 28), (9, 29), (9, 30), (10, 1), (10, 2))]
    kunye = _kunye(kural_0_5={"anahtar": "sayfa_oku.sh meridian-hedef-sapma", "iz": [
        {"commit": "4" * 40, "zaman": "2026-09-25T06:00:00+00:00", "adet": 1},
        {"commit": "5" * 40, "zaman": "2026-09-28T06:00:00+00:00", "adet": 0},
        {"commit": "6" * 40, "zaman": "2026-09-29T06:00:00+00:00", "adet": 1}]})
    veri, _ = sonuc(tmp_path, okm, okumalar=okumalar, kunye=kunye)
    assert _kill(veri, 4)["durum"] == "TETİKLENDİ"
    k1 = veri["kolonlar"]["K1"]
    assert (k1["pay"], k1["payda"]) == (8, 8) and k1["karsilastirma"] == "KALDI"


def test_I4_sentetik_isaretli_karar_D_disinda_ayri_listelenir(tmp_path, okm):
    kararlar = _varsayilan_kararlar() + [_karar("2026-09-25T11:00:00Z", sentetik=["[PK-EDG-103]"])]
    veri, _ = sonuc(tmp_path, okm, kararlar=kararlar)
    assert veri["D"]["deger"] == 5
    assert [k["sira"] for k in veri["D"]["sentetik_ayrilan"]] == [5]
    assert _kill(veri, 7)["kanit"]["sentetik_karar"] == 1


def test_I5_pencere_kapanmadan_dondurulduysa_ARA_rapor(tmp_path, okm):
    okumalar = [r for r in _varsayilan_okumalar(okm) if r["etiket"] != "olcum-anlik"]
    veri, _ = sonuc(tmp_path, okm, okumalar=okumalar,
                    kunye=_kunye(dondurma_ani="2026-10-02T07:30:00+00:00"))
    assert veri["hukum"].startswith("ARA RAPOR")
    assert "kolonlar" not in veri and "hüküm DEĞİL" in veri["betimleyici_ara_rapor"]["etiket"]


def test_I6_zamansiz_karar_varsa_hesap_yapilmaz(tmp_path, okm):
    kararlar = _varsayilan_kararlar() + [_karar(None, zaman_yok=True)]
    r, veri, _ = kos(girdi_yaz(tmp_path / "g", okm, kararlar=kararlar), tmp_path)
    assert r.returncode == 1 and veri is None and "commit damgası" in r.stderr


def test_I7_eksik_sayfa_goruntusu_hesap_yapilmaz(tmp_path, okm):
    r, veri, _ = kos(girdi_yaz(tmp_path / "g", okm, sayfalar={"nk-kripto-madencilik": None}), tmp_path)
    assert r.returncode == 1 and veri is None and "nk-kripto-madencilik" in r.stderr


def test_I8_girdi_bayti_degisirse_hesap_yapilmaz(tmp_path, okm):
    girdi = girdi_yaz(tmp_path / "g", okm)
    with (girdi / "okuma.jsonl").open("a", encoding="utf-8") as f:
        f.write("\n")
    r, veri, _ = kos(girdi, tmp_path)
    assert r.returncode == 1 and veri is None and "okuma.jsonl" in r.stderr


def test_I9_bozuk_ve_sema_disi_satir_sayilir_raporlanir(tmp_path, okm):
    veri, _ = sonuc(tmp_path, okm, ek_ham_satir='{"v": 1, "ts": "2026-09-27T00:00:00Z"}\n{bozuk')
    d = veri["girdi"]["okuma_kaydi"]
    assert d["sema_disi"] == [5] and d["bozuk_json"] == [6]


# ================================================================================================
# J — dondur.py: sentetik git deposu
# ================================================================================================

def _git(depo, *args, tarih=None):
    ortam = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    ortam.update({"GIT_AUTHOR_NAME": "Sahne", "GIT_AUTHOR_EMAIL": "sahne@ornek.gecersiz",
                  "GIT_COMMITTER_NAME": "Sahne", "GIT_COMMITTER_EMAIL": "sahne@ornek.gecersiz"})
    if tarih:
        ortam.update({"GIT_AUTHOR_DATE": tarih, "GIT_COMMITTER_DATE": tarih})
    return subprocess.run(["git", *args], cwd=str(depo), env=ortam, capture_output=True, text=True,
                          check=True, timeout=120)


#: Sentetik kart: gerçek kartın metni, pencere 3 güne kısaltılmış (testin koştuğu gün kapanmış olsun).
def _sentetik_kart() -> str:
    metin = KART.read_text(encoding="utf-8")
    assert metin.count("2026-10-02T10:33:10Z)") == 1
    return metin.replace("2026-10-02T10:33:10Z)", "2026-09-28T10:33:10Z)")


def _bloksuz(metin: str, *anahtarlar: str) -> str:
    out, atla = [], False
    for satir in metin.splitlines(keepends=True):
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:", satir)
        if m:
            atla = m.group(1) in anahtarlar
        if not atla:
            out.append(satir)
    return "".join(out)


ROADMAP_1 = """# ROADMAP
- **[TSK-903] sentetik kalem** — status: ACTIVE · owner: Rol-1
  What: (2026-09-26 12:0xZ KARAR [Rol-1] ilk not, hafıza: recall benzer yok) düz metin
"""
ROADMAP_2 = """# ROADMAP
- **[TSK-903] sentetik kalem** — status: ACTIVE · owner: Rol-1
  What: (2026-09-27 09:0xZ KARAR [Rol-1] ikinci not) (2026-09-26 12:0xZ KARAR [Rol-1] ilk not, hafıza: recall benzer yok) düz metin
"""
GUNLUK_1 = "# Günlük\n\n## 2026-09-20 başlangıç\n\nmetin\n"
#: 09-26 commit'i ESKİ (09-20) başlığın altına bir KARAR paragrafı ekler: birimin damgası başlığın değil,
#: işaretli satırın giriş commit'idir (başlık damgası kararı pencere dışına iterdi — alt sayım).
GUNLUK_2 = (GUNLUK_1 + "\nKARAR (operatör): eski başlık altına eklenen paragraf\n"
            "\n## 2026-09-26 açılış\n\n- KARAR (operatör 2026-09-26): [PK-EDG-103] sentetik PK izi\n")
GUNLUK_3 = GUNLUK_2 + "\n## 2026-09-28 kapanış\n\n- KARAR (operatör 2026-09-28): pencere sonrası karar\n"


#: `git add -A` yerel shim tarafından (geçici depoda bile) kapatılır — her ekleme AÇIK yolla.
KART_GORELI = "research/cards/EDG-2026-103-hafiza-sayfa-okuma-ilgi-atif.yaml"


@pytest.fixture
def sentetik_depo(tmp_path):
    depo = tmp_path / "depo"
    kart_yolu = depo / "research" / "cards" / "EDG-2026-103-hafiza-sayfa-okuma-ilgi-atif.yaml"
    kart_yolu.parent.mkdir(parents=True)
    _git(depo, "init", "-q", "-b", "main")
    kart = _sentetik_kart()
    kart_yolu.write_text(_bloksuz(kart, "pencere_acilis_2026_09_25", "netlestirme_2026_10_01"), encoding="utf-8")
    (depo / "CLAUDE.md").write_text("5. Rol-1 isen A1'de `~/bin/sayfa_oku.sh meridian-hedef-sapma` oku\n",
                                    encoding="utf-8")
    (depo / "ROADMAP.md").write_text("# ROADMAP\n", encoding="utf-8")
    (depo / "MERIDIAN_ENGINEERING_LOG.md").write_text(GUNLUK_1, encoding="utf-8")
    _git(depo, "add", "--", KART_GORELI, "CLAUDE.md", "ROADMAP.md", "MERIDIAN_ENGINEERING_LOG.md")
    _git(depo, "commit", "-q", "-m", "EDG-2026-103 ön-kayıt", tarih="2026-09-25T08:05:07Z")
    (depo / "deploy" / "hindsight").mkdir(parents=True)
    (depo / "deploy" / "hindsight" / "hafiza_okuma_kaydi.py").write_text("# kayıt\n", encoding="utf-8")
    _git(depo, "add", "--", "deploy/hindsight/hafiza_okuma_kaydi.py")
    _git(depo, "commit", "-q", "-m", "TSK-222 enstrümantasyon", tarih="2026-09-25T09:03:25Z")
    _git(depo, "commit", "-q", "--allow-empty", "-m", "TSK-901 → DONE: sınır öncesi",
         tarih="2026-09-25T10:33:09Z")
    _git(depo, "commit", "-q", "--allow-empty", "-m", "TSK-902 → DONE: sınırda",
         tarih="2026-09-25T10:33:10Z")
    kart_yolu.write_text(_bloksuz(kart, "netlestirme_2026_10_01"), encoding="utf-8")
    _git(depo, "add", "--", KART_GORELI)
    _git(depo, "commit", "-q", "-m", "EDG-103 pencere açıldı", tarih="2026-09-25T10:44:38Z")
    for metin_rm, metin_gn, tarih in ((ROADMAP_1, GUNLUK_2, "2026-09-26T12:00:00Z"),
                                      (ROADMAP_2, GUNLUK_2, "2026-09-27T09:00:00Z"),
                                      (ROADMAP_2, GUNLUK_3, "2026-09-28T11:00:00Z")):
        (depo / "ROADMAP.md").write_text(metin_rm, encoding="utf-8")
        (depo / "MERIDIAN_ENGINEERING_LOG.md").write_text(metin_gn, encoding="utf-8")
        _git(depo, "add", "--", "ROADMAP.md", "MERIDIAN_ENGINEERING_LOG.md")
        _git(depo, "commit", "-q", "-m", "Gunluk ve ROADMAP notu", tarih=tarih)
    kart_yolu.write_text(kart, encoding="utf-8")          # netleştirme pencere SONRASI eklenir (gerçekteki gibi)
    _git(depo, "add", "--", KART_GORELI)
    _git(depo, "commit", "-q", "-m", "EDG-103 netleştirme", tarih="2026-09-28T12:00:00Z")
    return depo


def _dondur(depo, tmp_path, okm, *, sayfalar=("meridian-hedef-sapma", "nk-kripto-madencilik"), ad="girdi"):
    okuma = tmp_path / "okuma.jsonl"
    okumalar = _varsayilan_okumalar(okm)[:3] + [
        _satir(okm, "2026-09-28T11:00:00Z", kimlik="meridian-hedef-sapma", etiket="olcum-anlik")]
    okuma.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in okumalar), encoding="utf-8")
    ek = []
    icerik = {"meridian-hedef-sapma": PK_SAYFASI, "nk-kripto-madencilik": NK_SAYFASI}
    for kimlik in sayfalar:
        yol = tmp_path / f"cekilen-{kimlik}.md"
        yol.write_text(_sayfa_md(kimlik, icerik[kimlik]), encoding="utf-8")
        ek += ["--sayfa", f"{kimlik}={yol}"]
    girdi = tmp_path / ad
    r = subprocess.run([sys.executable, "-B", str(DONDUR), "--repo", str(depo), "--okuma-kaydi", str(okuma),
                        "--girdi", str(girdi), *ek], capture_output=True, text=True, timeout=300,
                       cwd=str(depo))
    return r, girdi


def test_J1_dondur_giris_commiti_damgasi_ve_sayim_ucu_uca(sentetik_depo, tmp_path, okm):
    r, girdi = _dondur(sentetik_depo, tmp_path, okm)
    assert r.returncode == 0, r.stderr
    satirlar = (girdi / "SHA256.txt").read_text(encoding="utf-8").split("\n")
    listelenen = {s.split("  ", 1)[1] for s in satirlar if s.strip()}
    assert listelenen == {p.relative_to(girdi).as_posix() for p in girdi.rglob("*")
                          if p.is_file() and p.name != "SHA256.txt"}
    zl = json.loads((girdi / "karar_zamanlari.json").read_text(encoding="utf-8"))["kararlar"]
    zaman = {(z["kimlik"], z["tarih"]): z for z in zl}
    assert zaman[("TSK-901", "2026-09-25")]["zaman"] == "2026-09-25T10:33:09+00:00"
    assert zaman[("TSK-902", "2026-09-25")]["zaman"] == "2026-09-25T10:33:10+00:00"
    # ilk not 09-27'de aynı satıra ikinci not eklenince DEĞİŞMEZ: damga notun GİRİŞ commit'idir
    assert zaman[("TSK-903", "2026-09-26")]["zaman"] == "2026-09-26T12:00:00+00:00"
    assert zaman[("TSK-903", "2026-09-27")]["zaman"] == "2026-09-27T09:00:00+00:00"
    (sentetik,) = [z for z in zl if z["sentetik_isaretler"]]
    assert sentetik["sentetik_isaretler"] == ["[PK-EDG-103]"]
    (sonrasi,) = [z for z in zl if z["tarih"] == "2026-09-28" and z["kimlik"] is None]
    assert sonrasi["zaman"] == "2026-09-28T11:00:00+00:00"
    (eski_baslik,) = [z for z in zl if z["tarih"] == "2026-09-20"]
    assert eski_baslik["zaman"] == "2026-09-26T12:00:00+00:00", "damga başlığın değil işaretli satırın"
    assert eski_baslik["kaynaklar"][0]["anahtar_kaynagi"] == "isaretli_satir"
    kunye = json.loads((girdi / "kunye.json").read_text(encoding="utf-8"))
    assert kunye["kart"]["ilk_commit"]["zaman"] == "2026-09-25T08:05:07+00:00"
    assert kunye["enstrumantasyon"]["ilk_commit"]["zaman"] == "2026-09-25T09:03:25+00:00"
    assert kunye["pk_nk_zamani"] == "2026-09-25T10:44:38+00:00"
    assert [i["adet"] for i in kunye["kural_0_5"]["iz"]] == [1]
    assert "netlestirme_2026_10_01" not in (girdi / "kart_acilis.yaml").read_text(encoding="utf-8")
    rs, veri, _ = kos(girdi, tmp_path)
    assert rs.returncode == 0, rs.stderr
    assert veri["pk_nk"]["tuttu"] is True, veri["pk_nk"]
    kimlikler = [(k["kimlik"], k["tarih"]) for k in veri["D"]["kararlar"]]
    assert ("TSK-901", "2026-09-25") not in kimlikler and ("TSK-902", "2026-09-25") in kimlikler
    assert ("TSK-903", "2026-09-26") in kimlikler and ("TSK-903", "2026-09-27") in kimlikler
    assert (None, "2026-09-20") in kimlikler, "eski başlık altına pencerede eklenen karar D'de"
    assert all(t != "2026-09-28" for _k, t in kimlikler)
    assert _kill(veri, 7)["kanit"]["sentetik_karar"] == 1
    assert _kill(veri, 1)["durum"] == "TETİKLENMEDİ"


def test_J2_dondur_eksik_sayfayi_adiyla_soyler_ve_hicbir_sey_yazmaz(sentetik_depo, tmp_path, okm):
    r, girdi = _dondur(sentetik_depo, tmp_path, okm, sayfalar=("meridian-hedef-sapma",))
    assert r.returncode == 1
    assert "nk-kripto-madencilik" in r.stderr and "sayfa_oku.sh nk-kripto-madencilik" in r.stderr
    assert not girdi.exists()


def test_J3_dondur_kirli_agacta_ve_dolu_hedefte_durur(sentetik_depo, tmp_path, okm):
    (sentetik_depo / "ROADMAP.md").write_text("# ROADMAP\nkirli\n", encoding="utf-8")
    r, girdi = _dondur(sentetik_depo, tmp_path, okm)
    assert r.returncode == 2 and "commit" in r.stderr and not girdi.exists()


# ================================================================================================
# K — `meridian` İTHAL EDİLMEZ
# ================================================================================================

def _meridian_ithalleri(yol: pathlib.Path) -> set[str]:
    out = set()
    for d in ast.walk(ast.parse(yol.read_text(encoding="utf-8"))):
        if isinstance(d, ast.Import):
            out |= {a.name for a in d.names if a.name.split(".")[0] == "meridian"}
        elif isinstance(d, ast.ImportFrom) and d.module and d.module.split(".")[0] == "meridian":
            out.add(d.module)
    return out


def _yuklenen_meridian(stderr: str) -> list[str]:
    yuklenen = {s.split("|")[-1].strip() for s in stderr.splitlines() if "import time:" in s}
    return sorted(m for m in yuklenen if m == "meridian" or m.startswith("meridian."))


def test_K1_meridian_statik_olarak_ithal_edilmez():
    for yol in (SAYIM, DONDUR):
        assert _meridian_ithalleri(yol) == set(), yol.name


def test_K2_OPERATOR_BICIMINDE_sayim_obs_YUKLEMEZ(tmp_path, okm):
    r, veri, _ = kos(girdi_yaz(tmp_path / "g", okm), tmp_path, importtime=True)
    assert r.returncode == 0, r.stderr
    assert veri is not None
    assert _yuklenen_meridian(r.stderr) == []


def test_K3_OPERATOR_BICIMINDE_dondur_obs_YUKLEMEZ(sentetik_depo, tmp_path, okm):
    okuma = tmp_path / "okuma.jsonl"
    okuma.write_text("", encoding="utf-8")
    r = subprocess.run([sys.executable, "-B", "-X", "importtime", str(DONDUR), "--repo", str(sentetik_depo),
                        "--okuma-kaydi", str(okuma), "--girdi", str(tmp_path / "girdi")],
                       capture_output=True, text=True, timeout=300, cwd=str(sentetik_depo))
    assert r.returncode == 1, r.stderr       # sayfalar verilmedi → eksik sayfa; ithal kapanışı yine ölçülür
    assert "import time:" in r.stderr and _yuklenen_meridian(r.stderr) == []
