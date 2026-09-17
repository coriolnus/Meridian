"""v519 — TSK-196 (ii): yeniden-üretim ÇAĞRISI düşünce ölçülmüş ihlal kaybolmaz (2026-09-17).

NE ÖLÇÜLDÜ (Rol-1, A1 olay defteri, 2026-09-17T10:03Z bekçi): `brifing_kural_denetimi`
hukum=denetlenemedi, kaynak=llm_dustu, gerekçe "yeniden-üretim çağrısı düştü: RuntimeError('kapı
üst-akım hatası (kod 503 …". Aynı koşumun EDG-101 satırında `ilk_hukum.kaynak = llm` ve olayda
`ilk_ihlal` doluydu: denetçi ilk metinde İHLAL BULMUŞTU, düşen şey metni düzeltecek yeniden-üretim
çağrısıydı. `soul_denetimi._yeniden`in istisna dalı ölçülmüş hükmü `_dustu` ile DEĞİŞTİRİYORDU →
operatöre "kural denetimi yapılamadı" deniyor, olaydaki `ihlal` listesi boşalıyor, `yeniden_uretim`
False yazılıyordu. Denetimi YAPILMIŞ bir metin, yapılmamış gibi görünüyordu (Yasa 6 okuyucu tarafı,
uydurma yasağı).

KARAR (Rol-1, ROADMAP TSK-196, 2026-09-17 — TASARIM DEĞİŞMEZ): yalnız o istisna dalında hüküm İLK
hükümdür, giden metin DEĞİŞMEZ (ilk metin), `yeniden_uretim` True (denendi), yeni hüküm adı
`ihlal_duzeltilemedi`, beyan "kural denetimi: N ihlal bulundu, düzeltme çağrısı düştü (<neden>) — ilk
metin gitti", olay `gerekce`si düşüş nedenini taşır.

ÇİVİLER
  K0. Ölçülen modül BU ağacın modülüdür (worktree PYTHONPATH tuzağı).
  1.  İlk denetim ihlal bulur + yeniden-üretim çağrısı patlar → ilk metin gider, hüküm ilk hüküm,
      `hukum_adi` = `ihlal_duzeltilemedi`, `yeniden_uretim` True, `ihlal_duzeltildi` ÇIKMAZ.
  2.  Beyan biçimi TAM (N ölçülmüş ihlal sayısı, neden = istisnanın `repr`i ilk 200 karakter) ve
      "yapılamadı" İÇERMEZ; N kırpılmamış listeden sayılır.
  3.  `Gecis.kayit` + defterdeki olay: `hukum`, `ihlal` (kırpma aynen), `gerekce` (hüküm gerekçesi +
      düşüş nedeni; hüküm gerekçesi boşsa yalnız düşüş nedeni); `suzulen` ÇİFTLENMEZ.
  4.  Değişmeyen dallar eski değerleriyle: reddedildi (dogrula · boş cevap) · 2/2 ihlal · tavan ·
      ilk denetim düşer · yeniden-denetim düşer · temiz · düzeltildi.
  5.  EDG-101 yakalaması açıkken satırın `teslim_karari` = `ihlal_duzeltilemedi`, `ilk_hukum` ihlali
      taşır.

Testler gerçek `state/`e yazmaz (`sandbox_state`); `monkeypatch.undo()` KULLANILMAZ.
"""
from __future__ import annotations

import dataclasses
import importlib
import json
import pathlib

import pytest

from tests.test_soul_denetimi_v385 import (  # tek-kaynak: sahte profil/kuyruk/cevaplar v385'te
    _ihlalli_cevap, _Kuyruk, _olaylar, _profil_evi, _temiz_cevap)

KOK = pathlib.Path(__file__).resolve().parent.parent

#: Canlı vakanın istisna metninin biçimi (2026-09-17T10:03Z bekçi) — sınıf + kod + rota.
CANLI_HATA = RuntimeError("kapı üst-akım hatası (kod 503, rota hizli) — yeniden deneme de düştü")


@pytest.fixture
def sd():
    return importlib.import_module("ops.soul_denetimi")


class _SonraPatlar:
    """Verilen cevapları sırayla döner; cevaplar tükenince `hata`yı fırlatır. Gördüğü istemleri
    saklar — patlayan çağrının GERÇEKTEN yeniden-üretim çağrısı olduğu istemden ölçülür."""

    def __init__(self, *cevaplar, hata: BaseException = CANLI_HATA):
        self.cevaplar = list(cevaplar)
        self.hata = hata
        self.istemler: list[str] = []

    def __call__(self, istem):
        self.istemler.append(istem)
        if not self.cevaplar:
            raise self.hata
        return self.cevaplar.pop(0)


def _gecir(sd, tmp_path, cagir, *, ilk="ilk metin", ilk_istem="İLK İSTEM", terimler=(), **kw):
    return sd.gecir(profil_evi=_profil_evi(tmp_path), ilk_metin=ilk, ilk_istem=ilk_istem,
                    veri_terimleri=list(terimler), cagir=cagir, bot="bekci", **kw)


def _cokme_vakasi(sd, tmp_path, *, hata: BaseException = CANLI_HATA, ilk_cevap=None, **kw):
    """Canlı vakanın birebir akışı: denetim → ihlal → yeniden-üretim çağrısı PATLAR."""
    cagir = _SonraPatlar(ilk_cevap if ilk_cevap is not None else _ihlalli_cevap(), hata=hata)
    g = _gecir(sd, tmp_path, cagir, **kw)
    return g, cagir


# ================================================================================================
# K0 — ölçülen modül bu ağacın modülü
# ================================================================================================

def test_K0_olculen_modul_BU_agactan_yuklenir(sd):
    assert pathlib.Path(sd.__file__).resolve().is_relative_to(KOK), (
        f"ops.soul_denetimi başka bir ağaçtan yüklendi ({sd.__file__}) — yeşil bu ağacı ölçmez")


# ================================================================================================
# 1 — ilk hüküm korunur, ilk metin gider, etiket `ihlal_duzeltilemedi`
# ================================================================================================

def test_1_YENIDEN_URETIM_CAGRISI_DUSERSE_ILK_HUKUM_KORUNUR(sd, tmp_path, sandbox_state):
    g, cagir = _cokme_vakasi(sd, tmp_path)
    # Ön koşul: patlayan GERÇEKTEN yeniden-üretim çağrısıdır (ikinci çağrı, ihlal eki taşır).
    assert len(cagir.istemler) == 2, f"çağrı sayısı: {len(cagir.istemler)}"
    assert "ÖNCEKİ CEVABIN REDDEDİLDİ" in cagir.istemler[1], "patlayan çağrı yeniden-üretim değil"

    ilk_hukum = sd.ayristir(_ihlalli_cevap())
    assert g.metin == "ilk metin", f"giden metin değişti: {g.metin!r}"
    assert g.hukum_adi == "ihlal_duzeltilemedi", f"hüküm adı: {g.hukum_adi!r}"
    assert g.hukum_adi != "ihlal_duzeltildi"
    assert g.yeniden_uretim is True, "yeniden-üretim DENENDİ ama False yazıldı"
    assert g.hukum.olculdu is True and g.hukum.kaynak == "llm", f"hüküm ölçülmemişe çevrildi: {g.hukum!r}"
    assert g.hukum.ihlaller == ilk_hukum.ihlaller and g.hukum.ihlaller, (
        f"ölçülmüş ihlal listesi kayboldu: {g.hukum.ihlaller!r}")
    assert g.cagri_n == 3, f"düşen çağrı da sayılır (sıralama + denetim + yeniden-üretim): {g.cagri_n}"


def test_1B_MEKANIK_IHLALDE_DE_AYNI_DAL(sd, tmp_path, sandbox_state):
    """Mekanik hüküm (LLM'siz) de ÖLÇÜLMÜŞTÜR: yeniden-üretim çağrısı düşünce o da kaybolmamalı."""
    cagir = _SonraPatlar()           # İLK çağrı yeniden-üretimdir (mekanik dalda denetçi YOK)
    g = _gecir(sd, tmp_path, cagir, ilk="terim yok burada", terimler=["MECHANISM_STALE"])
    assert len(cagir.istemler) == 1, "mekanik dalda denetçi çağrıldı"
    assert g.metin == "terim yok burada" and g.hukum.kaynak == "mekanik", f"{g!r}"
    assert g.hukum_adi == "ihlal_duzeltilemedi" and g.yeniden_uretim is True, f"{g!r}"
    assert any("MECHANISM_STALE" in i for i in g.hukum.ihlaller), g.hukum.ihlaller


# ================================================================================================
# 2 — beyan: ölçülmüş ihlal + düşüş nedeni + hangi metnin gittiği; "yapılamadı" YOK
# ================================================================================================

def test_2_BEYAN_IHLALI_DUSUSU_VE_GIDEN_METNI_SOYLER(sd, tmp_path, sandbox_state):
    g, _ = _cokme_vakasi(sd, tmp_path)
    assert "ihlal bulundu" in g.beyan and "düzeltme çağrısı düştü" in g.beyan, g.beyan
    assert "ilk metin gitti" in g.beyan, g.beyan
    assert "yapılamadı" not in g.beyan, f"denetimi YAPILMIŞ metin 'yapılamadı' diye beyan edildi: {g.beyan!r}"
    n = len(g.hukum.ihlaller)
    assert n == 2, f"ön koşul (sade_ozet False + 1 uydurma): {g.hukum.ihlaller!r}"
    assert g.beyan == (f"kural denetimi: {n} ihlal bulundu, düzeltme çağrısı düştü "
                       f"({repr(CANLI_HATA)[:200]}) — ilk metin gitti"), g.beyan


def test_2B_NEDEN_200_KARAKTERE_KIRPILIR_N_KIRPILMAMIS_LISTEDEN(sd, tmp_path, sandbox_state):
    uzun = RuntimeError("x" * 600)
    cok = json.dumps({"sade_ozet": False, "uydurma": [f"uyd{i}" for i in range(6)],
                      "cevrilen": []}, ensure_ascii=False)
    g, _ = _cokme_vakasi(sd, tmp_path, hata=uzun, ilk_cevap=cok)
    assert len(g.hukum.ihlaller) == 7 > sd.IHLAL_TAVANI, g.hukum.ihlaller
    assert g.beyan.startswith("kural denetimi: 7 ihlal bulundu, "), (
        f"N kırpılmış listeden sayıldı: {g.beyan[:60]!r}")
    assert f"({repr(uzun)[:200]})" in g.beyan and repr(uzun)[:201] not in g.beyan, (
        "neden 200 karakterlik kısa repr değil")


# ================================================================================================
# 3 — olay/damga kaydı
# ================================================================================================

def test_3_KAYIT_HUKUM_IHLAL_GEREKCE(sd, tmp_path, sandbox_state):
    g, _ = _cokme_vakasi(sd, tmp_path)
    k = g.kayit("bekci")
    assert k["hukum"] == "ihlal_duzeltilemedi", k
    assert k["kaynak"] == "llm" and k["yeniden_uretim"] is True and k["cagri_n"] == 3, k
    assert k["ihlal"] == g.hukum.ihlaller[:sd.IHLAL_TAVANI] and k["ihlal"], k
    dusus = f"yeniden-üretim çağrısı düştü: {repr(CANLI_HATA)[:200]}"
    assert k["gerekce"] == f"{g.hukum.gerekce} · {dusus}"[:200], k["gerekce"]
    assert g.hukum.gerekce and g.hukum.gerekce in k["gerekce"], "ölçülmüş hükmün gerekçesi düştü"
    assert "yeniden-üretim çağrısı düştü: RuntimeError(" in k["gerekce"], "düşüş nedeni kayıtta yok"


def test_3B_IHLAL_KAYITTA_TAVANLA_KIRPILIR(sd, tmp_path, sandbox_state):
    cok = json.dumps({"sade_ozet": False, "uydurma": [f"uyd{i}" for i in range(6)],
                      "cevrilen": []}, ensure_ascii=False)
    g, _ = _cokme_vakasi(sd, tmp_path, ilk_cevap=cok)
    assert g.kayit("bekci")["ihlal"] == g.hukum.ihlaller[:sd.IHLAL_TAVANI]
    assert len(g.kayit("bekci")["ihlal"]) == sd.IHLAL_TAVANI


def test_3C_HUKUM_GEREKCESI_BOSSA_YALNIZ_DUSUS_NEDENI(sd, tmp_path, sandbox_state):
    g, _ = _cokme_vakasi(sd, tmp_path)
    bos = dataclasses.replace(g, hukum=dataclasses.replace(g.hukum, gerekce=""))
    assert bos.kayit("bekci")["gerekce"] == (
        f"yeniden-üretim çağrısı düştü: {repr(CANLI_HATA)[:200]}")[:200], bos.kayit("bekci")


def test_3D_MEKANIK_GEREKCE_DE_KORUNUR(sd, tmp_path, sandbox_state):
    g = _gecir(sd, tmp_path, _SonraPatlar(), ilk="terim yok burada", terimler=["MECHANISM_STALE"])
    assert g.hukum_adi == "ihlal_duzeltilemedi", f"ön koşul: {g!r}"
    gerekce = g.kayit("bekci")["gerekce"]
    assert gerekce.startswith("terim korunumu MEKANİK") and "yeniden-üretim çağrısı düştü" in gerekce, (
        gerekce)


def test_3E_DEFTERDEKI_OLAY_ILK_HUKMU_TASIR_SUZULEN_CIFTLENMEZ(sd, tmp_path, sandbox_state):
    """Olay `Gecis.kayit` + ek alanlardan kurulur. `suzulen` ilk hükmün ve (FARKLIYSA) teslim hükmünün
    toplamıdır — teslim hükmü ilk hükmün ta kendisiyken iki kez sayılmamalı."""
    ilk_istem = "### kaynak\n" + sd._veri_bloku("kaynak", "bekçi ölçüldü")
    ilk_cevap = json.dumps({"sade_ozet": True, "uydurma": ["bekçi", "tetti"], "cevrilen": []},
                           ensure_ascii=False)
    g, _ = _cokme_vakasi(sd, tmp_path, ilk_cevap=ilk_cevap, ilk_istem=ilk_istem)
    assert g.hukum.suzulen == ["bekçi"] and g.hukum.ihlaller == ["uydurma sözcük: tetti"], g.hukum
    olay = _olaylar()
    assert len(olay) == 1, olay
    o = olay[0]
    assert o["hukum"] == "ihlal_duzeltilemedi" and o["kaynak"] == "llm", o
    assert o["yeniden_uretim"] is True and o["ihlal"] == ["uydurma sözcük: tetti"], o
    assert o["ilk_ihlal"] == o["ihlal"], o
    assert o["suzulen"] == ["bekçi"], f"suzulen çiftlendi/kayboldu: {o['suzulen']!r}"
    assert "yeniden-üretim çağrısı düştü" in o["gerekce"], o["gerekce"]
    assert o["brifing_ilk_satir"] == "ilk metin", o


# ================================================================================================
# 4 — değişmeyen dallar, eski değerleriyle
# ================================================================================================

def test_4A_REDDEDILDI_DOGRULA_HAM(sd, tmp_path, sandbox_state):
    g = _gecir(sd, tmp_path, _Kuyruk(_ihlalli_cevap(), "..."),
               dogrula=lambda c: "çok kısa" if len(c) < 20 else None)
    assert (g.metin, g.hukum_adi, g.yeniden_uretim, g.cagri_n) == (None, "ham", True, 3), g
    assert g.beyan == "kural denetimi: yeniden-üretim reddedildi (çok kısa), ham teslim", g.beyan


def test_4B_REDDEDILDI_BOS_CEVAP_HAM(sd, tmp_path, sandbox_state):
    g = _gecir(sd, tmp_path, _Kuyruk(_ihlalli_cevap(), "   "))
    assert (g.metin, g.hukum_adi, g.yeniden_uretim) == (None, "ham", True), g
    assert g.beyan == ("kural denetimi: yeniden-üretim reddedildi (yeniden-üretim boş cevap "
                       "verdi), ham teslim"), g.beyan


def test_4C_IKI_KEZ_IHLAL_HAM(sd, tmp_path, sandbox_state):
    g = _gecir(sd, tmp_path, _Kuyruk(_ihlalli_cevap(), "yine bozuk metin", _ihlalli_cevap()))
    assert (g.metin, g.hukum_adi, g.yeniden_uretim, g.cagri_n) == (None, "ham", True, 4), g
    assert g.beyan == "kural denetimi: 2/2 ihlal, ham teslim", g.beyan


def test_4D_YENIDEN_URETIM_TAVANA_TAKILIR_ESKI_DAVRANIS(sd, tmp_path, sandbox_state):
    """Tavan dalı İSTİSNA dalı DEĞİLDİR ve bu turda DEĞİŞMEZ (Rol-1 kararı): hüküm `_dustu`."""
    kuyruk = _Kuyruk(_ihlalli_cevap())
    g = _gecir(sd, tmp_path, kuyruk, baslangic_cagri=3)
    assert kuyruk.n == 1, "tavandayken yeniden-üretim çağrıldı"
    assert (g.metin, g.hukum_adi, g.yeniden_uretim, g.cagri_n) == (
        "ilk metin", "denetlenemedi", False, 4), g
    assert g.hukum.kaynak == "llm_dustu", g.hukum
    assert g.beyan == ("kural denetimi yapılamadı: ihlal bulundu ama yeniden-üretim çağrı "
                       "tavanına takıldı (4/4)"), g.beyan


def test_4E_ILK_DENETIM_DUSERSE_DENETLENEMEDI_VE_YAPILAMADI(sd, tmp_path, sandbox_state):
    hata = RuntimeError("upstream 502")
    g = _gecir(sd, tmp_path, _SonraPatlar(hata=hata))
    assert (g.metin, g.hukum_adi, g.yeniden_uretim, g.cagri_n) == (
        "ilk metin", "denetlenemedi", False, 2), g
    assert g.beyan == f"kural denetimi yapılamadı: denetçi çağrısı düştü: {repr(hata)[:200]}", g.beyan
    assert g.kayit("bekci")["ihlal"] == [] and g.kayit("bekci")["kaynak"] == "llm_dustu"


def test_4F_YENIDEN_DENETIM_DUSERSE_DUZELTILMIS_METIN_GIDER(sd, tmp_path, sandbox_state):
    g = _gecir(sd, tmp_path, _SonraPatlar(_ihlalli_cevap(), "düzeltilmiş metin ve gerekçesi"))
    assert (g.metin, g.hukum_adi, g.yeniden_uretim) == (
        "düzeltilmiş metin ve gerekçesi", "denetlenemedi", True), g
    assert g.beyan.startswith("kural denetimi: yeniden-üretim denetlenemedi (denetçi çağrısı düştü: ")
    assert g.beyan.endswith("), düzeltilmiş metin gitti"), g.beyan


def test_4G_TEMIZ(sd, tmp_path, sandbox_state):
    g = _gecir(sd, tmp_path, _Kuyruk(_temiz_cevap()))
    assert (g.metin, g.hukum_adi, g.yeniden_uretim, g.beyan, g.cagri_n) == (
        "ilk metin", "temiz", False, "", 2), g


def test_4H_DUZELTILDI(sd, tmp_path, sandbox_state):
    g = _gecir(sd, tmp_path, _Kuyruk(_ihlalli_cevap(), "düzeltilmiş metin ve gerekçesi",
                                     _temiz_cevap()))
    assert (g.metin, g.hukum_adi, g.yeniden_uretim, g.beyan, g.cagri_n) == (
        "düzeltilmiş metin ve gerekçesi", "ihlal_duzeltildi", True, "", 4), g
    assert g.kayit("bekci")["gerekce"] == "denetçi hükmü", g.kayit("bekci")


# ================================================================================================
# 5 — EDG-101 yakalama satırı
# ================================================================================================

def test_5_EDG101_SATIRI_YENI_TESLIM_KARARINI_VE_ILK_IHLALI_TASIR(sd, tmp_path, monkeypatch,
                                                                  sandbox_state):
    dizin = tmp_path / "yakalama"
    monkeypatch.setenv(sd.EDG101_YAKALAMA_ENV, str(dizin))
    ilk_cevap = _ihlalli_cevap(("tetti", "kritikisi"))
    g, _ = _cokme_vakasi(sd, tmp_path, ilk_cevap=ilk_cevap)
    dosyalar = sorted(dizin.glob("edg101_*.jsonl"))
    assert len(dosyalar) == 1, dosyalar
    satirlar = [json.loads(s) for s in dosyalar[0].read_text(encoding="utf-8").splitlines()
                if s.strip()]
    assert len(satirlar) == 1, satirlar
    s = satirlar[0]
    assert s["teslim_karari"] == g.hukum_adi == "ihlal_duzeltilemedi", s["teslim_karari"]
    assert s["yeniden_uretim"] is True, s
    assert s["ilk_hukum"] == {"kaynak": "llm", "uydurma": ["tetti", "kritikisi"],
                              "terim_ihlal": [], "suzulen": []}, s["ilk_hukum"]
    assert s["teslim_hukum"] == s["ilk_hukum"], "teslim hükmü ilk hüküm değil"
    assert s["ilk_metin"] == "ilk metin", s["ilk_metin"]
