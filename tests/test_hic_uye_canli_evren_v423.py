"""test_hic_uye_canli_evren_v423.py — HİÇ S&P 500 ÜYESİ OLMAMIŞ 6 SEMBOL CANLI EVRENE GERİ DÖNER
(TSK-143, 2026-09-05, İKİNCİ revizyon — operatör kararı, AYNI GÜN önceki commitin (82848bf) üstüne).

BAĞLAM: 82848bf tek bir `data.EVREN_DISI_BEYANLI` (10 sembol) defteri açtı ve `is_index_exited`
bu 10'un HEPSİNE True dedi — `LIVE_UNIVERSE = REPLAY_UNIVERSE eksi is_index_exited` de altısını
(BURL, LNG, PINS, ROKU, SNAP, SPOT) canlı evrenden düşürdü. Ama bu altısı S&P 500'den hiç ÇIKMADI —
hiç GİRMEDİ (BURL/ROKU S&P 400 üyesi, SPOT yabancı, LNG/PINS/SNAP hiç üye olmamış likit isimler).
"Endeks çıkışı" hükmü onlara UYMUYOR. Operatör kararı: yalnız GERÇEK çıkışlar (CAG, ENPH, MTCH,
VFC — dördü) canlı evrenden süzülsün; hiç-üye altısı GERİ DÖNSÜN.

BU TURUN SÖZÜ: `data.EVREN_DISI_BEYANLI` artık İKİ alt-sözlüğün (`ENDEKS_CIKISI_BEYANLI` 4,
`HIC_UYE_BEYANLI` 6) TÜRETİLMİŞ BİRLEŞİMİ. `is_index_exited` (LIVE süzgeci) YALNIZ ilkine bağlı;
YENİ `is_evren_disi_beyanli` (drift-beyanı görünürlüğü, `constituents.universe_drift()`ün
`beyanli_disi` alanı) birleşime bağlı. `LIVE_UNIVERSE` bu yüzden REPLAY_UNIVERSE eksi 4 (238→244).
Tarih düzeltmesi (EDG-2026-075/076, S&P DJI bültenleri): MTCH yürürlüğü '2026-03-09' değil
'2026-03-23'; VFC yürürlüğü '2024-04-01' değil '2024-04-03' — ikisi de duyuru/yürürlük tarihi
karışıklığıydı.

MUTASYON KANITI (raporda ayrıca anlatılır, TDD gereği — koda GEÇİCİ uygulanıp geri alınır):
  1. `is_index_exited` birleşime (`EVREN_DISI_BEYANLI`) bağlanırsa 6 hiç-üye sembol LIVE_UNIVERSE'den
     düşer → `test_live_universe_6_hic_uye_geri_donuyor` kırmızı.
  2. `EVREN_DISI_BEYANLI` birleşimi bozulup yalnız `ENDEKS_CIKISI_BEYANLI`ya eşitlenirse (HIC_UYE_
     BEYANLI düşerse) beyan kümesinden 6 sembol kaybolur ve `universe_drift()`ün `stale` alanı bu
     6'yı İÇERİR → `test_universe_drift_hic_uye_canlida_beyanli_disi_stale_ayrisir` kırmızı.
"""
from __future__ import annotations

from meridian.adapters import constituents, data

ENDEKS_CIKISI_4 = {"CAG", "ENPH", "MTCH", "VFC"}
HIC_UYE_6 = {"BURL", "LNG", "PINS", "ROKU", "SNAP", "SPOT"}
BEYANLI_10 = ENDEKS_CIKISI_4 | HIC_UYE_6


# =================================================================================================
# a) LIVE_UNIVERSE — 6 hiç-üye GERİ DÖNÜYOR, 4 gerçek çıkış HÂLÂ DIŞARIDA
# =================================================================================================
def test_live_universe_6_hic_uye_geri_donuyor_4_cikis_disarida():
    """MUTASYON 1 HEDEFİ: `is_index_exited` birleşime (10) bağlanırsa `LIVE_UNIVERSE` yeniden
    REPLAY-10'a (238) düşer ve bu çivi ötmeli. Doğru davranışta REPLAY-4 (244) beklenir."""
    assert len(data.LIVE_UNIVERSE) == len(data.REPLAY_UNIVERSE) - 4
    for t in HIC_UYE_6:
        assert t in data.LIVE_UNIVERSE, f"{t} hiç S&P 500 üyesi olmadı — canlı evrene GERİ DÖNMELİ"
    for t in ENDEKS_CIKISI_4:
        assert t not in data.LIVE_UNIVERSE, f"{t} gerçekten S&P 500'den ÇIKTI — canlı evrende KALMAMALI"


# =================================================================================================
# b) İki kapı, iki farklı hüküm: is_index_exited (dar, ÇIKIŞLAR) vs is_evren_disi_beyanli (birleşim)
# =================================================================================================
def test_is_index_exited_dar_is_evren_disi_beyanli_genis():
    """`is_index_exited` yalnız GERÇEK çıkışlara (CAG dahil) True der; hiç-üye bir sembolde (PINS)
    False döner ama `is_evren_disi_beyanli` PINS için True der — iki kapı KASITLI olarak AYRI
    hükümler taşır (LIVE süzgeci vs drift-beyanı görünürlüğü)."""
    assert data.is_index_exited("CAG") is True
    assert data.is_index_exited("cag") is True, "büyük/küçük harf duyarsız olmalı"
    assert data.is_index_exited("PINS") is False
    assert data.is_evren_disi_beyanli("PINS") is True
    assert data.is_evren_disi_beyanli("pins") is True
    # Boş/None/yaşayan bir isim ikisinde de False.
    assert not data.is_index_exited("") and not data.is_index_exited(None)
    assert not data.is_evren_disi_beyanli("") and not data.is_evren_disi_beyanli(None)
    assert not data.is_index_exited("AAPL") and not data.is_evren_disi_beyanli("AAPL")


def test_evren_disi_beyanli_iki_alt_sozlugun_ayrik_birlesimi():
    """`EVREN_DISI_BEYANLI` = `ENDEKS_CIKISI_BEYANLI` (4) ∪ `HIC_UYE_BEYANLI` (6), TOPLAM 10 —
    kopya DEĞİL, türetilmiş üçüncü ad (tek-kaynak yasası). İki alt-sözlük KESİŞMEZ: bir sembol ya
    gerçekten S&P 500'den ÇIKTI ya HİÇ ÜYE OLMADI, ikisi birden olamaz."""
    assert set(data.ENDEKS_CIKISI_BEYANLI) == ENDEKS_CIKISI_4
    assert set(data.HIC_UYE_BEYANLI) == HIC_UYE_6
    assert len(data.ENDEKS_CIKISI_BEYANLI) == 4
    assert len(data.HIC_UYE_BEYANLI) == 6
    kesisim = set(data.ENDEKS_CIKISI_BEYANLI) & set(data.HIC_UYE_BEYANLI)
    assert not kesisim, f"iki alt-sözlük kesişiyor: {sorted(kesisim)}"
    assert set(data.EVREN_DISI_BEYANLI) == BEYANLI_10
    assert len(data.EVREN_DISI_BEYANLI) == 10
    # GERİYE UYUMLULUK: INDEX_EXITED artık ENDEKS_CIKISI_BEYANLI'nin AYNI nesnesi (4 kayıt) —
    # TSK-143'ün İLK revizyonundaki gibi EVREN_DISI_BEYANLI'nin (10) AYNI nesnesi DEĞİL artık.
    assert data.INDEX_EXITED is data.ENDEKS_CIKISI_BEYANLI
    assert data.INDEX_EXITED is not data.EVREN_DISI_BEYANLI
    assert len(data.INDEX_EXITED) == 4


# =================================================================================================
# c) universe_drift() — beyanli_disi (birleşim), hic_uye_canlida (YENİ), stale ayrımı
# =================================================================================================
def test_universe_drift_hic_uye_canlida_beyanli_disi_stale_ayrisir(sandbox_state, monkeypatch):
    """MUTASYON 2 HEDEFİ: `EVREN_DISI_BEYANLI` birleşimi bozulup `ENDEKS_CIKISI_BEYANLI`ya
    eşitlenirse (HIC_UYE_BEYANLI düşerse) bu 6 sembol `_beyanli_ve_emekli`den kaybolur ve `stale`
    onları İÇERİR — bu çivi o an ötmeli. Doğru davranışta: `stale` BEYANLI_10'u içermez (bu
    kurulumda tam boş, çünkü sentetik 'güncel liste' REPLAY_UNIVERSE'in beyanlı/emekli DIŞINDAKİ
    kalanını birebir kapsıyor), `hic_uye_canlida` tam 6, `beyanli_disi` tam 10, `index_exited_in_live`
    boş."""
    # 'S&P 500'ü temsil eden makul liste': REPLAY_UNIVERSE'in beyanlı(10, BU DOSYANIN SABİT
    # BEYANLI_10 literaliyle — data.EVREN_DISI_BEYANLI'DAN DEĞİL, kasıtlı: MUTASYON 2 tam bu
    # sözlüğü bozduğu için fixture'ın ONA bağımlı olması testi kendi hedefinden kör ederdi)/emekli
    # (11) DIŞINDA kalan gerçek isimleri + makullük kapısını (>=400) geçecek kadar dolgu.
    gercek_disi = sorted(set(data.REPLAY_UNIVERSE) - BEYANLI_10 - set(data.RETIRED_SYMBOLS))
    dolgu = [f"PAD{i}" for i in range(460 - len(gercek_disi))]
    guncel = gercek_disi + dolgu
    monkeypatch.setattr(constituents, "current", lambda *a, **k: guncel)

    d = constituents.universe_drift()

    assert d["status"] == "ok"
    assert d["stale"] == [], f"beyanlı/emekli dışı kalan sızmış: {d['stale']}"
    assert not (set(d["stale"]) & BEYANLI_10), "beyanlı 10 sembol stale'e SIZMIŞ"

    assert set(d["hic_uye_canlida"]) == HIC_UYE_6
    assert d["n_hic_uye_canlida"] == 6

    assert set(d["beyanli_disi"]) == BEYANLI_10
    assert d["n_beyanli_disi"] == 10

    assert d["index_exited_in_live"] == []
    assert d["index_exited_n"] == 4


def test_universe_drift_unknown_dalinda_da_hic_uye_canlida_alani_var(sandbox_state, monkeypatch):
    """`status == 'unknown'` dalı (üyelik kaynağı yok) `hic_uye_canlida`yı da EKSİKSİZ taşımalı —
    Yasa 6: kaynak çökse bile beyanlı görünürlük kaybolmaz."""
    monkeypatch.setattr(constituents, "current", lambda *a, **k: [])
    d = constituents.universe_drift()
    assert d["status"] == "unknown"
    assert set(d["hic_uye_canlida"]) == HIC_UYE_6
    assert d["n_hic_uye_canlida"] == 6
    assert set(d["beyanli_disi"]) == BEYANLI_10
    assert d["index_exited_in_live"] == []


# =================================================================================================
# d) Tarih düzeltmesi (EDG-2026-075/076): MTCH/VFC yürürlük tarihleri
# =================================================================================================
def test_mtch_vfc_yururluk_tarihleri_duzeltildi():
    """EDG-2026-075/076 (S&P DJI basın bültenleri): MTCH yürürlüğü '2026-03-09' DEĞİL '2026-03-23';
    VFC yürürlüğü '2024-04-01' DEĞİL '2024-04-03'. Eskiden ikisi de duyuru tarihiyle karışmıştı."""
    assert "2026-03-23" in data.ENDEKS_CIKISI_BEYANLI["MTCH"]
    assert "2026-03-09" not in data.ENDEKS_CIKISI_BEYANLI["MTCH"]
    assert "2024-04-03" in data.ENDEKS_CIKISI_BEYANLI["VFC"]
    assert "2024-04-01" not in data.ENDEKS_CIKISI_BEYANLI["VFC"]
