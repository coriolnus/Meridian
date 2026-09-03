"""tests/test_edg019_olcum_v389.py — EDG-2026-019 RESMÎ ÖLÇÜM betiğinin çivisi (TSK-073, 2026-09-03).

NE ÖLÇER. `research/olcumler/edg019_skill_gorus_etki/olcum.py` — kartın (`EDG-2026-019-skill-
gorus-defteri.yaml`) success_metric'inde donmuş eşiklerle (n_min=30 · FDR q=0.10 · |rank-IC|>=0.05)
donmuş bir girdiden (motor DOKUNULMADAN, canlı `state/` OKUNMADAN) FDR-sağkalan terfi adaylarını
bulan betik. Bu dosya AŞAĞIDAKİLERİ ölçer:
  (a) eşikler kartın SERBEST METNİNDEN doğru çekiliyor mu ve motor sabitleriyle bugün örtüşüyor mu
      (ayrışma çivisi — tek-kaynak yasası);
  (b) girdi şeması dedektörü gerçekten ölçüyor mu (--kuru yolunun altındaki fonksiyon);
  (c) POZİTİF KONTROL: sentetik, BİLİNEN rank-IC'li bir seri gerçekten TERFİ ADAYI olarak
      bulunuyor mu — ve MUTASYON (aynı skill'in skor↔r eşleşmesini karıştırıp IC'yi sıfırlamak)
      bu bulguyu GERÇEKTEN ÖTÜRÜYOR mu (CLAUDE.md §6: "çivi yeşili kanıt değildir").

KAPSAM DIŞI: kartın hükmü (Rol-1 verir, CLAUDE.md §3) — bu dosya betiğin DOĞRU ÖLÇTÜĞÜNÜ
kanıtlar, bir terfi/emeklilik kararı vermez.
"""
from __future__ import annotations

import datetime as _dt
import pathlib
import random

import pytest

from tests.conftest import betikten_modul_yukle

KOK = pathlib.Path(__file__).resolve().parents[1]
BETIK_YOLU = KOK / "research" / "olcumler" / "edg019_skill_gorus_etki" / "olcum.py"
KART_YOLU = KOK / "research" / "cards" / "EDG-2026-019-skill-gorus-defteri.yaml"


def _olcum():
    return betikten_modul_yukle(BETIK_YOLU, "edg019_olcum")


# ==================================================================================
# (a) eşikler karttan okunuyor + motorla ayrışma çivisi
# ==================================================================================

def test_esikler_kartin_serbest_metninden_dogru_cekiliyor():
    o = _olcum()
    esikler = o.esikleri_karttan_oku(KART_YOLU)
    assert esikler["fdr_q"] == pytest.approx(0.10)
    assert esikler["rank_ic_esigi"] == pytest.approx(0.05)
    assert esikler["n_min"] == 30
    assert esikler["ci_seviye"] == pytest.approx(0.95)
    assert esikler["kart_id"] == "EDG-2026-019"


def test_esik_bulunamazsa_UYDURMAZ_value_error_atar(tmp_path):
    """POZİTİF KONTROL (a): kartın cümlesi değişip bir eşik kaybolursa betik SESSİZCE
    varsayılan atamıyor mu, gerçekten patlıyor mu?"""
    o = _olcum()
    bozuk = tmp_path / "bozuk-kart.yaml"
    bozuk.write_text(
        "card_id: SENTETIK-2026-000\n"
        "success_metric: >\n"
        "  Yalnız FDR q=0.10 var, geri kalan eşikler CÜMLEDEN SİLİNDİ.\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="rank_ic_esigi"):
        o.esikleri_karttan_oku(bozuk)


def test_esikler_motorun_donuk_sabitleriyle_BUGUN_ORTUSUYOR():
    """Ayrışma çivisi (tek-kaynak yasası): `meridian.skill_gorus.KART_*` kartla bugün AYNI mı?
    Farklıysa betik yine karttan okunanı kullanır (kart SSoT) ama bu test KIRMIZI olup haber verir."""
    o = _olcum()
    esikler = o.esikleri_karttan_oku(KART_YOLU)
    farklar = o.esikleri_motorla_karsilastir(esikler)
    assert farklar == [], f"kart ↔ motor eşikleri ayrıştı: {farklar}"


def test_p_arama_adim_motordan_turetiliyor_KOPYALANMAMIS(monkeypatch):
    """AYRIŞMA ÇİVİSİ (düzeltme turu 2026-09-03, inceleme bulgusu): `P_ARAMA_ADIM` bir KART EŞİĞİ
    DEĞİL — bootstrap p'nin ikili-arama çözünürlüğü, `success_metric`te hiç geçmiyor. Motor
    karşılığı VAR (`meridian.skill_gorus.P_ARAMA_ADIM`) ve betik onu ÇAĞRI ANINDA okur, ikinci
    bir sabit olarak YAZMAZ. Statik "aynı değer" karşılaştırması YETMEZ (iki ayrı `= 7` satırı da
    'aynı' görünürdü) — bu test DAVRANIŞLA ölçer: motorun çözünürlüğünü değiştirip betiğin ikili-
    arama ÇAĞRI SAYISININ gerçekten değiştiğini kanıtlar."""
    o = _olcum()
    from meridian import faz5_cikis as _f5
    from meridian import skill_gorus as _sg

    assert not hasattr(o, "P_ARAMA_ADIM"), (
        "olcum.py modül seviyesinde HÂLÂ kendi P_ARAMA_ADIM'ı var — motordan türetilmiyor, "
        "ikinci bir kopya olarak duruyor (tek-kaynak yasası ihlali)"
    )

    cagrilar: list[int] = []
    orijinal = _f5.tarih_kumeli_bootstrap

    def _sayan(*a, **k):
        cagrilar.append(1)
        return orijinal(*a, **k)

    monkeypatch.setattr(_f5, "tarih_kumeli_bootstrap", _sayan)

    # Sentetik seri ÖNCEDEN ÖLÇÜLDÜ (rnd.gauss(0.01, 0.05), tohum=3, n=40/20 küme): hem kaba
    # (adım=3, en_sert=%87,5) hem ince (adım=9, en_sert=%99,8) çözünürlükte ikili-arama DÖNGÜSÜNE
    # gerçekten girer (ne en_sert ne lo=0 ucunda erken dönmez) — yalnız TOPLAM tur sayısı değişir.
    rnd = __import__("random").Random(3)
    degerler = [rnd.gauss(0.01, 0.05) for _ in range(40)]
    tarihler = [f"2026-01-{(i // 2) + 1:02d}" for i in range(40)]

    monkeypatch.setattr(_sg, "P_ARAMA_ADIM", 3)
    cagrilar.clear()
    o._bootstrap_p_karttan(degerler, tarihler, 0.95)
    n_kaba = len(cagrilar)

    monkeypatch.setattr(_sg, "P_ARAMA_ADIM", 9)
    cagrilar.clear()
    o._bootstrap_p_karttan(degerler, tarihler, 0.95)
    n_ince = len(cagrilar)

    assert n_kaba == 6, f"kaba çözünürlükte (adım=3) beklenen 3+3=6 çağrı, ölçülen {n_kaba}"
    assert n_ince == 12, f"ince çözünürlükte (adım=9) beklenen 3+9=12 çağrı, ölçülen {n_ince}"
    assert n_ince > n_kaba, (
        "motorun P_ARAMA_ADIM'i değişince betiğin ikili-arama çağrı sayısı DEĞİŞMEDİ — "
        "türetim gerçek değil, sabit KOPYALANMIŞ olabilir"
    )


# ==================================================================================
# (b) girdi şeması dedektörü — --kuru yolunun altı
# ==================================================================================

def _iyi_satir(**over):
    satir = {"skill": "test-skill", "tarih": "2026-01-01", "hedef": "H1",
              "skor": 1.0, "karar": "hit_target", "r": 0.5, "mfe_r": 0.6, "kaynak": "gercek"}
    satir.update(over)
    return satir


def test_sema_gecerli_girdide_sifir_ihlal_uretir():
    o = _olcum()
    assert o.sema_ihlallerini_bul([_iyi_satir()]) == []


def test_sema_zorunlu_alan_eksikligini_YAKALAR():
    o = _olcum()
    satir = _iyi_satir()
    del satir["hedef"]
    ihlaller = o.sema_ihlallerini_bul([satir])
    assert any("zorunlu alan eksik" in i for i in ihlaller)


def test_sema_gorussuz_satiri_YAKALAR():
    o = _olcum()
    satir = _iyi_satir(skor=None, karar=None)
    ihlaller = o.sema_ihlallerini_bul([satir])
    assert any("görüşsüz satır" in i for i in ihlaller)


def test_sema_yabanci_alani_YAKALAR():
    """YASA 4 (sessiz yutma yok): tanınmayan alan adıyla raporlanır, sessizce yutulmaz."""
    o = _olcum()
    satir = _iyi_satir(uydurma_alan="sizinti")
    ihlaller = o.sema_ihlallerini_bul([satir])
    assert any("tanınmayan alan" in i and "uydurma_alan" in i for i in ihlaller)


def test_kuru_kapisi_gecerli_dosyada_sifir_donuyor(tmp_path):
    o = _olcum()
    girdi = tmp_path / "girdi.jsonl"
    import json
    girdi.write_text(json.dumps(_iyi_satir()) + "\n", encoding="utf-8")
    assert o.main(["--girdi", str(girdi), "--kuru"]) == 0


def test_kuru_kapisi_bozuk_dosyada_bir_donuyor(tmp_path):
    """POZİTİF KONTROL (b): --kuru kapısı her zaman 0 mu dönüyor, gerçekten mi ölçüyor?"""
    o = _olcum()
    girdi = tmp_path / "girdi.jsonl"
    import json
    satir = _iyi_satir()
    del satir["skill"]
    girdi.write_text(json.dumps(satir) + "\n", encoding="utf-8")
    assert o.main(["--girdi", str(girdi), "--kuru"]) == 1


# ==================================================================================
# (c) POZİTİF KONTROL — bilinen rank-IC'li seri BULUNUYOR mu + MUTASYON (IC sıfırlanınca ÖTÜYOR mu)
# ==================================================================================

def _tarih(i: int) -> str:
    return (_dt.date(2026, 1, 1) + _dt.timedelta(days=i // 2)).isoformat()


def _sentetik_satirlar(n: int = 32, *, karistir: bool = False) -> list[dict]:
    """`vcp-screener`: skor ve gerçekleşen R MÜKEMMEL monoton (bilinen güçlü rank-IC) — `n`
    gözlem, 2'şerli `n/2` ayrı tarih kümesinde (kümeli bootstrap için >=2 küme şartı rahat aşılır).
    `flat-skill`: R SABİT (rütbe varyansı sıfır) → rank-IC TANIMSIZ, deterministik "ölçülemedi"
    negatif kontrolü — şansa bırakılmaz.

    `karistir=True`: MUTASYON — `vcp-screener`in skor↔R eşleşmesi SABİT TOHUMLU bir karışıklıkla
    permüte edilir (tohum=14, bu satırda seçildi: `analytics.spearman_ic` ile önceden ÖLÇÜLDÜ —
    |IC|≈0,0022, kartın 0,05 etki eşiğinin AÇIKÇA altında; tersine çevirmek gibi bir "düzenli"
    permütasyon KULLANILMAZ, çünkü o da mükemmel NEGATİF korelasyon (|IC|=1) verir ve mutasyon
    hiçbir şeyi sıfırlamamış olurdu — bkz. bu kartın kendi hükmü: |rank-IC| eşiği İKİ YÖNLÜDÜR).
    Tarihler/hedefler AYNEN kalır, yalnız R DEĞERLERİNİN skor'a eşlenme SIRASI karışır."""
    skorlar = [float(i + 1) for i in range(n)]
    r_degerleri = [float(i + 1) * 0.05 for i in range(n)]
    if karistir:
        r_degerleri = list(r_degerleri)
        random.Random(14).shuffle(r_degerleri)
    satirlar = []
    for i in range(n):
        satirlar.append({
            "skill": "vcp-screener", "tarih": _tarih(i), "hedef": f"VCP-{i}",
            "skor": skorlar[i], "karar": "hit_target",
            "r": r_degerleri[i], "mfe_r": r_degerleri[i] + 0.05, "kaynak": "gercek",
        })
        satirlar.append({
            "skill": "flat-skill", "tarih": _tarih(i), "hedef": f"FLT-{i}",
            "skor": float(i + 1), "karar": "hit_target",
            "r": 0.5, "mfe_r": 0.55, "kaynak": "gercek",
        })
    return satirlar


def test_pk_bilinen_ic_bulunur_terfi_adayi_olarak():
    o = _olcum()
    esikler = o.esikleri_karttan_oku(KART_YOLU)
    satirlar = _sentetik_satirlar()
    assert o.sema_ihlallerini_bul(satirlar) == [], "sentetik girdi kendi şemasını ihlal ediyor"

    sonuc = o.olc(satirlar, esikler)
    siralayici = sonuc["yuzeyler"]["aday-siralayici"]["skiller"]

    # vcp-screener: mükemmel monoton ilişki → ÖLÇÜLDÜ, etki eşiğini AÇIKÇA geçti, FDR-sağkalan
    assert siralayici["vcp-screener"]["kova"] == "OLCULDU"
    assert siralayici["vcp-screener"]["olcum"]["rank_ic"] == pytest.approx(1.0, abs=1e-6)
    assert siralayici["vcp-screener"]["etki_esigi_gecti"] is True
    assert siralayici["vcp-screener"]["fdr"]["sagkalan"] is True
    assert siralayici["vcp-screener"]["terfi_adayi"] is True
    assert any(t["skill"] == "vcp-screener" and t["yuzey"] == "aday-siralayici"
               for t in sonuc["terfi_adaylari"])

    # flat-skill: R sabit → rank-IC TANIMSIZ, terfi adayı OLAMAZ (dedektör her zaman "buldum"
    # demiyor — negatif kontrol)
    assert siralayici["flat-skill"]["kova"] == "ÖLÇÜLEMEDİ"
    assert siralayici["flat-skill"]["olcum"] is None
    assert not any(t["skill"] == "flat-skill" for t in sonuc["terfi_adaylari"])


def test_mutasyon_ic_sifirlaninca_PK_OTUYOR():
    """MUTASYON KANITI (brief madde 7 / CLAUDE.md §6): `vcp-screener`in skor↔R eşleşmesi
    karıştırılınca (permütasyon, yukarıdaki testteki AYNI skill) yukarıdaki terfi bulgusu
    GERÇEKTEN kaybolmalı — kaybolmuyorsa dedektör hiçbir şeyi ölçmüyor, her zaman 'terfi' diyordur."""
    o = _olcum()
    esikler = o.esikleri_karttan_oku(KART_YOLU)
    satirlar = _sentetik_satirlar(karistir=True)

    sonuc = o.olc(satirlar, esikler)
    siralayici = sonuc["yuzeyler"]["aday-siralayici"]["skiller"]

    ic = siralayici["vcp-screener"]["olcum"]["rank_ic"]
    assert abs(ic) < esikler["rank_ic_esigi"], (
        f"mutasyon IC'yi etki eşiğinin ALTINA indirmedi (ölçülen {ic}) — kurgunun kendisi bozuk"
    )
    assert siralayici["vcp-screener"]["etki_esigi_gecti"] is False
    assert not any(t["skill"] == "vcp-screener" and t["yuzey"] == "aday-siralayici"
                   for t in sonuc["terfi_adaylari"]), (
        "IC sıfırlandıktan SONRA bile 'vcp-screener' terfi adayı kaldı — PK ÖTMEDİ, "
        "dedektör gerçekte ölçmüyor olabilir"
    )


def test_esleşmeyen_gorus_sayaci_dogru():
    """Kartın kill#4'ü ('çöp girdi çöp hüküm zinciri kapalı'): sonucu OLMAYAN bir hedefin
    görüşü 'eşleşmeyen' sayılır, sessizce düşmez."""
    o = _olcum()
    esikler = o.esikleri_karttan_oku(KART_YOLU)
    satirlar = _sentetik_satirlar()
    # bir satırın SONUCUNU (r) kaldır ama görüşü (skor) dursun — eşleşme kurulamaz olmalı
    satirlar = [dict(s) for s in satirlar]
    satirlar[0]["r"] = None
    sonuc = o.olc(satirlar, esikler)
    assert sonuc["yuzeyler"]["aday-siralayici"]["eslesmeyen_gorus"] >= 1
