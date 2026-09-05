"""test_ingest067_retry_v387.py — TSK-115 (2026-09-03): ingest067.py dilimli ana yol + hata-sinifli
retry + kosum tavani.

VAKA. Rol-1 A1 olcumu (2026-09-03 11:38Z): 158 OK / 348 HATA (146'si 429 gunluk ucretsiz tavan —
onceki gece; bu gece 500 "ProviderResponseError"). Eski ingest067.py butun-ya-da-hic tek POST'ta
gonderiyordu, hata sinifi ayirt etmiyordu (HTTPError de genel Exception de ayni 3-deneme/backoff
dalina giriyordu) ve basarisizlik ilerleme.jsonl'e HIC yazilmiyordu (yalniz basari).

SOZLESME (bkz. brief D1-D5):
  D1 dilimli ana yol   — belge_planla(): tek dilimse document_id `yol` KALIR, coklu dilimde
                         `yol#k/n` (1-tabanli); dilim_sup.dilimle() ITHAL edilir, kopyalanmaz.
  D2 hata sinifi        — hata_sinifi(status, govde): 429 -> dur (retry YOK); 500+isaretli/502/
                         503/504/ag-hatasi -> gecici (en cok 3 deneme, backoff 60/120/240 sn);
                         diger 4xx/5xx -> kalici (tek deneme, retry yok).
  D3 kosum tavani       — cagri-tavani'na gelince TEMIZ durur (durum: dur), sonraki is HIC denenmez.
  D4 ilerleme.jsonl     — {yol, dilim, durum, neden, bayt, ts}; YALNIZ durum==ok atlanir,
                         basarisiz/dur yeniden denenir.
  D5 ozet                — ok/gecici-hata/kalici/dur sayimi + boyut bandi x sinif tablosu.

MUTASYON KAPSAMASI (raporda dogrulanir):
  · 429'u hata_sinifi'nde "gecici" yap  -> test_b2_dur_siniflandirmasi_hemen_durur oturr.
  · backoff'u 30*n yap                  -> test_b1_gecici_uc_deneme_backoff_60_120_240 oturr.
  · basarisiz satirini yazmayi kaldir   -> test_e_yeniden_kosum_ok_atlanir_basarisiz_denenir oturr.

TSK-151 (2026-09-05, TSK-144 kesfi): hata_sinifi'ndaki gunluk-kota dalini kaldir -> test_a_hata_sinifi_tablosu
  (gunluk-kota satirlari) + test_b5_gunluk_kota_500_hemen_durur_retry_yok oturr (govde "kalici"ya
  duser). Per-minute istisnasini kaldir (429/500 govdesinde 'per-min' varken kosulsuz "dur" dondur)
  -> test_a_hata_sinifi_tablosu (per-min satirlari) + test_b6_gunluk_kota_permin_varyanti_gecici_retry_kalir
  oturr (retry hakki kaybolur).

Gercek HTTP/sleep YOK: `_cagri_yap` ve `time.sleep` monkeypatch. Betik betikten_modul_yukle ile
KAYNAKTAN yuklenir (bayat bytecode dersi, v334) — ham exec_module DEGIL.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from tests.conftest import betikten_modul_yukle

_YOL = pathlib.Path(__file__).resolve().parent.parent / \
    "research/olcumler/edg067_hindsight_faz1/ingest067.py"


@pytest.fixture()
def ing():
    """Her testte TAZE modul — `calistir`/`belge_isle` cagri_sayaci gibi paylasimli durum tasimaz
    ama monkeypatch.setattr(ing, ...) testler arasi sizmasin diye modul da tazelenir."""
    return betikten_modul_yukle(_YOL, f"ingest067_v387_{id(object())}")


def _kok_kur(tmp_path, dosyalar, head="abc123def"):
    """`manifest_uret.py` ciktisinin minik ikizi: `korpus/` + `manifest.json` (bkz. v358 `_paket_kur`)."""
    for yol, icerik in dosyalar.items():
        hedef = tmp_path / "korpus" / yol
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(icerik, encoding="utf-8")
    kayitlar = [{"yol": y, "blob": "blob-" + y,
                "bayt": len(i.encode("utf-8"))} for y, i in dosyalar.items()]
    (tmp_path / "manifest.json").write_text(
        json.dumps({"head_commit": head, "dosyalar": kayitlar}), encoding="utf-8")
    return tmp_path


def _kayit_toplayici():
    satirlar = []

    def kayit(*a):
        satirlar.append(" ".join(str(x) for x in a))
    kayit.satirlar = satirlar
    return kayit


def _ilerleme_oku(kok):
    yol = pathlib.Path(kok) / "ilerleme.jsonl"
    if not yol.exists():
        return []
    return [json.loads(s) for s in yol.read_text(encoding="utf-8").splitlines() if s.strip()]


def _uyku_toplayici(monkeypatch, ing):
    uykular = []
    monkeypatch.setattr(ing.time, "sleep", lambda s: uykular.append(s))
    return uykular


def _uyku_patlayan(monkeypatch, ing):
    def patlayan(s):
        raise AssertionError(f"sleep cagrilmamali idi (s={s})")
    monkeypatch.setattr(ing.time, "sleep", patlayan)


# =================================================================================================
# §A — hata_sinifi: tablo (D2)
# =================================================================================================
@pytest.mark.parametrize("status,govde,beklenen", [
    (429, "", "dur"),
    (429, "gunluk ucretsiz tavan doldu", "dur"),
    (500, "... ProviderResponseError: upstream patladi ...", "gecici"),
    (500, "... temporarily overloaded ...", "gecici"),
    (500, "... rate limit asildi ...", "gecici"),
    (500, "... you have been rate-limited, retry later ...", "gecici"),
    (500, "duz ic sunucu hatasi, isaret yok", "kalici"),
    (502, "bad gateway", "gecici"),
    (503, "service unavailable", "gecici"),
    (504, "gateway timeout", "gecici"),
    (None, "URLError: [Errno 61] Connection refused", "gecici"),
    (400, "bad request: eksik alan", "kalici"),
    (401, "unauthorized", "kalici"),
    (404, "not found", "kalici"),
    # ÖNEMLİ-1 (düzeltme turu 1, 2026-09-03): NEGATİF çiviler — "rate" bitişik-gövde kelimelerde
    # geçse de KALICI kalmalı; salt alt-dizge eşleşmesi bunları yanlışlıkla "gecici" sayardı.
    (500, "... accurate response generated by model, no issue ...", "kalici"),
    (500, "... provider returned a separate error code, unrelated ...", "kalici"),
    # DÜZELTME TURU 2 (TSK-151, 2026-09-05 — TSK-144 keşfi): OpenRouter hesap-geneli GÜNLÜK kota
    # aşımı 500 gövdesinde 'gecici' sayılıyordu (dilim başına 3 deneme x ~200s boşa, r2 ölçümü);
    # artık 'dur'. Per-minute/per-min varyantı (r2'de GÖRÜLMEDİ, mimariye önden konur) 'gecici'
    # KALIR — o gerçekten bekle-dene sınıfıdır. Nvidia overloaded DEĞİŞMEDİ (son satır).
    (500, "RateLimitError: free-models-per-day limit exceeded, retry tomorrow", "dur"),
    (500, "Rate limit exceeded: free-models-per-day quota for this account has been used", "dur"),
    (500, "RateLimitError: requests-per-day cap reached for tier", "dur"),  # fallback: 'per-day'+'RateLimit' ikilisi (literal 'free-models-per-day' yok)
    (429, "RateLimitError: free-models-per-min limit exceeded, retry in 12s", "gecici"),
    (500, "RateLimitError: free-models-per-min limit exceeded, retry in 12s", "gecici"),
    (500, "Service temporarily overloaded, please retry the request", "gecici"),  # Nvidia — DEĞİŞMEDİ
])
def test_a_hata_sinifi_tablosu(ing, status, govde, beklenen):
    assert ing.hata_sinifi(status, govde) == beklenen


def test_a2_backoff_dizisi_60_120_240(ing):
    assert [ing.backoff_sn(n) for n in (1, 2, 3)] == [60, 120, 240]


# =================================================================================================
# §B — belge_isle: retry + backoff + dur (D2, D3)
# =================================================================================================
def test_b1_gecici_uc_deneme_backoff_60_120_sonra_basarisiz(ing, monkeypatch):
    """KÜÇÜK-1 düzeltmesi (2026-09-03): 3. (son) denemeden SONRA bekleme YOK — 3 denemede yalnız
    İKİ bekleme olur (1→2 ve 2→3 arası), 3. deneme başarısız olunca hemen döner."""
    uykular = _uyku_toplayici(monkeypatch, ing)
    cagrilar = []

    def sahte(anahtar, base, method, path, body=None, timeout=3600):
        cagrilar.append(path)
        raise ing._CagriHatasi(500, "... ProviderResponseError: patladi ...")

    monkeypatch.setattr(ing, "_cagri_yap", sahte)
    durum, sinif, neden, cagri_sayaci, tok = ing.belge_isle(
        "k", "http://x", "meridian-arsiv", "docs/A.md", {}, cagri_sayaci=0, cagri_tavani=10)
    assert (durum, sinif) == ("basarisiz", "gecici_hata")
    assert cagri_sayaci == 3, "3 deneme yapilmali"
    assert len(cagrilar) == 3
    assert uykular == [60, 120], f"backoff dizisi 60/120 degil (son denemeden sonra bekleme OLMAMALI): {uykular}"
    assert neden and "500" in neden


def test_b2_dur_siniflandirmasi_hemen_durur_retry_yok(ing, monkeypatch):
    """429'u geciciye ceviren bir mutasyon bu testi kirmiziya duserdi: dur -> HIC retry/sleep yok,
    tek cagriyla biter (TSK-115 mutasyon kapsamasi)."""
    _uyku_patlayan(monkeypatch, ing)
    cagrilar = []

    def sahte(anahtar, base, method, path, body=None, timeout=3600):
        cagrilar.append(path)
        raise ing._CagriHatasi(429, "gunluk ucretsiz tavan doldu")

    monkeypatch.setattr(ing, "_cagri_yap", sahte)
    durum, sinif, neden, cagri_sayaci, tok = ing.belge_isle(
        "k", "http://x", "meridian-arsiv", "docs/A.md", {}, cagri_sayaci=0, cagri_tavani=10)
    assert (durum, sinif) == ("dur", "dur")
    assert cagri_sayaci == 1, "429'da ikinci deneme YAPILMAMALI"
    assert len(cagrilar) == 1


def test_b3_kalici_tek_denemede_biter_retry_yok(ing, monkeypatch):
    _uyku_patlayan(monkeypatch, ing)

    def sahte(anahtar, base, method, path, body=None, timeout=3600):
        raise ing._CagriHatasi(400, "bad request: eksik alan")

    monkeypatch.setattr(ing, "_cagri_yap", sahte)
    durum, sinif, neden, cagri_sayaci, tok = ing.belge_isle(
        "k", "http://x", "meridian-arsiv", "docs/A.md", {}, cagri_sayaci=0, cagri_tavani=10)
    assert (durum, sinif) == ("basarisiz", "kalici")
    assert cagri_sayaci == 1


def test_b4_basarili_gonderim_usage_tasir(ing, monkeypatch):
    def sahte(anahtar, base, method, path, body=None, timeout=3600):
        return 200, {"usage": {"input_tokens": 111, "output_tokens": 22}}

    monkeypatch.setattr(ing, "_cagri_yap", sahte)
    durum, sinif, neden, cagri_sayaci, (gi, ci) = ing.belge_isle(
        "k", "http://x", "meridian-arsiv", "docs/A.md", {}, cagri_sayaci=0, cagri_tavani=10)
    assert (durum, sinif, neden) == ("ok", "ok", None)
    assert (gi, ci) == (111, 22)
    assert cagri_sayaci == 1


def test_b5_gunluk_kota_500_hemen_durur_retry_yok(ing, monkeypatch):
    """TSK-151 (2026-09-05, TSK-144 kesfi) mutasyon kapsamasi: hata_sinifi'ndaki gunluk-kota dalini
    kaldirmak bu govdeyi 'kalici'ya dusurur — (durum, sinif) ("basarisiz", "kalici") olur, ("dur",
    "dur") DEGIL, bu test kirmiziya duser. BULGU (r2): bu govdeyle eskiden `gecici` sayilip dilim
    basina 3 deneme x ~200s bosa gidiyordu — artik TEK cagriyla, sifir bekleyisle biter."""
    _uyku_patlayan(monkeypatch, ing)
    cagrilar = []

    def sahte(anahtar, base, method, path, body=None, timeout=3600):
        cagrilar.append(path)
        raise ing._CagriHatasi(
            500, "RateLimitError: free-models-per-day limit exceeded, retry tomorrow")

    monkeypatch.setattr(ing, "_cagri_yap", sahte)
    durum, sinif, neden, cagri_sayaci, tok = ing.belge_isle(
        "k", "http://x", "meridian-arsiv", "docs/A.md", {}, cagri_sayaci=0, cagri_tavani=10)
    assert (durum, sinif) == ("dur", "dur")
    assert cagri_sayaci == 1, "gunluk kotada ikinci deneme YAPILMAMALI"
    assert len(cagrilar) == 1
    assert neden and "free-models-per-day" in neden


def test_b6_gunluk_kota_permin_varyanti_gecici_retry_kalir(ing, monkeypatch):
    """Karsit çivi: per-minute varyanti (r2'de gorulmedi, mimariye onden konur) 429'da bile 'dur'a
    DUSMEMELI — gecici sinifinin retry/backoff yolunu KORUR (3 deneme, backoff 60/120)."""
    uykular = _uyku_toplayici(monkeypatch, ing)
    cagrilar = []

    def sahte(anahtar, base, method, path, body=None, timeout=3600):
        cagrilar.append(path)
        raise ing._CagriHatasi(
            429, "RateLimitError: free-models-per-min limit exceeded, retry in 12s")

    monkeypatch.setattr(ing, "_cagri_yap", sahte)
    durum, sinif, neden, cagri_sayaci, tok = ing.belge_isle(
        "k", "http://x", "meridian-arsiv", "docs/A.md", {}, cagri_sayaci=0, cagri_tavani=10)
    assert (durum, sinif) == ("basarisiz", "gecici_hata")
    assert cagri_sayaci == 3, "per-minute varyanti 3 deneme HAKKINI korumali"
    assert len(cagrilar) == 3
    assert uykular == [60, 120]


# =================================================================================================
# §C — kosum tavani (D3): tavana gelince temiz durur, sonraki is HIC denenmez
# =================================================================================================
def test_c_cagri_tavani_dolunca_temiz_durur_ikinci_is_hic_denenmez(ing, monkeypatch, tmp_path):
    kok = _kok_kur(tmp_path, {"docs/A.md": "icerik a", "docs/B.md": "icerik b"})
    _uyku_toplayici(monkeypatch, ing)

    denenenler = []

    def sahte(anahtar, base, method, path, body=None, timeout=3600):
        doc_id = body["items"][0]["document_id"]
        denenenler.append(doc_id)
        if doc_id == "docs/B.md":
            raise AssertionError("B HIC denenmemeliydi — cagri tavani A'nin ilk denemesinde doldu")
        raise ing._CagriHatasi(503, "service unavailable")

    monkeypatch.setattr(ing, "_cagri_yap", sahte)
    kayit = _kayit_toplayici()
    sayimlar, cagri_sayaci = ing.calistir(str(kok), ing.VARSAYILAN_DILIM_BAYT, 1,
                                          "k", "http://x", "meridian-arsiv", kayit)
    assert cagri_sayaci == 1, "cagri-tavani=1 iken tek cagri yapilmali"
    assert sayimlar["dur"] == 1
    assert sayimlar == {"ok": 0, "gecici_hata": 0, "kalici": 0, "dur": 1}
    assert denenenler == ["docs/A.md"], "ikinci is denenmis"

    satirlar = _ilerleme_oku(kok)
    assert len(satirlar) == 1
    assert satirlar[0]["durum"] == "dur"
    assert "tavan" in satirlar[0]["neden"]


# =================================================================================================
# §D — ilerleme.jsonl semasi (D4) + basarisiz satiri YAZILIR (mutasyon kapsamasi)
# =================================================================================================
def test_d1_ilerleme_semasi_alanlari(ing, monkeypatch, tmp_path):
    kok = _kok_kur(tmp_path, {"docs/A.md": "kisa icerik"})
    monkeypatch.setattr(ing, "_cagri_yap",
                        lambda *a, **k: (200, {"usage": {"input_tokens": 1, "output_tokens": 1}}))
    kayit = _kayit_toplayici()
    ing.calistir(str(kok), ing.VARSAYILAN_DILIM_BAYT, 10, "k", "http://x", "meridian-arsiv", kayit)
    satirlar = _ilerleme_oku(kok)
    assert len(satirlar) == 1
    satir = satirlar[0]
    assert set(satir.keys()) == {"yol", "dilim", "durum", "neden", "bayt", "ts"}
    assert satir["yol"] == "docs/A.md"
    assert satir["dilim"] is None
    assert satir["durum"] == "ok"
    assert satir["neden"] is None
    assert satir["bayt"] == len("kisa icerik".encode())
    assert satir["ts"]


def test_d2_basarisiz_satiri_YAZILIR(ing, monkeypatch, tmp_path):
    """Mutasyon kapsamasi: 'basarisiz satirini yazmayi kaldir' bu testi kirmiziya dusurur."""
    kok = _kok_kur(tmp_path, {"docs/A.md": "kisa icerik"})
    _uyku_toplayici(monkeypatch, ing)

    def sahte(anahtar, base, method, path, body=None, timeout=3600):
        raise ing._CagriHatasi(400, "bad request")

    monkeypatch.setattr(ing, "_cagri_yap", sahte)
    kayit = _kayit_toplayici()
    sayimlar, _ = ing.calistir(str(kok), ing.VARSAYILAN_DILIM_BAYT, 10, "k", "http://x",
                               "meridian-arsiv", kayit)
    assert sayimlar["kalici"] == 1
    satirlar = _ilerleme_oku(kok)
    assert len(satirlar) == 1
    assert satirlar[0]["durum"] == "basarisiz"
    assert "400" in satirlar[0]["neden"]


# =================================================================================================
# §E — yeniden kosum: ok atlanir, basarisiz YENIDEN denenir (D4)
# =================================================================================================
def test_e_yeniden_kosum_ok_atlanir_basarisiz_denenir(ing, monkeypatch, tmp_path):
    kok = _kok_kur(tmp_path, {"docs/OK.md": "tamam", "docs/YENIDEN.md": "yeniden dene"})
    # onceki kosumu simule eden ilerleme.jsonl: OK.md basarili, YENIDEN.md basarisiz kalmis
    (kok / "ilerleme.jsonl").write_text(
        json.dumps({"yol": "docs/OK.md", "dilim": None, "durum": "ok", "neden": None,
                   "bayt": 5, "ts": "2026-09-03T00:00:00Z"}) + "\n" +
        json.dumps({"yol": "docs/YENIDEN.md", "dilim": None, "durum": "basarisiz",
                   "neden": "HTTP 503 onceki kosum", "bayt": 12,
                   "ts": "2026-09-03T00:00:00Z"}) + "\n",
        encoding="utf-8")

    denenenler = []

    def sahte(anahtar, base, method, path, body=None, timeout=3600):
        doc_id = body["items"][0]["document_id"]
        denenenler.append(doc_id)
        if doc_id == "docs/OK.md":
            raise AssertionError("OK.md daha once basariliydi, YENIDEN denenmemeliydi")
        return 200, {"usage": {"input_tokens": 1, "output_tokens": 1}}

    monkeypatch.setattr(ing, "_cagri_yap", sahte)
    kayit = _kayit_toplayici()
    sayimlar, _ = ing.calistir(str(kok), ing.VARSAYILAN_DILIM_BAYT, 10, "k", "http://x",
                               "meridian-arsiv", kayit)
    assert denenenler == ["docs/YENIDEN.md"]
    assert sayimlar == {"ok": 1, "gecici_hata": 0, "kalici": 0, "dur": 0}

    satirlar = _ilerleme_oku(kok)
    # eski iki satir + bu kosumun YENI ok satiri = 3
    assert len(satirlar) == 3
    yeni = [s for s in satirlar if s["ts"] != "2026-09-03T00:00:00Z"]
    assert len(yeni) == 1 and yeni[0]["yol"] == "docs/YENIDEN.md" and yeni[0]["durum"] == "ok"


def test_e2_eski_semali_ilerleme_satiri_ok_sayilir_atlanir(ing, monkeypatch, tmp_path):
    """KRİTİK-1 düzeltmesi (2026-09-03): A1'in gerçek `ilerleme.jsonl`'i (ölçüm 12:52Z, 146 satır)
    ESKİ şemayla yazıldı — `{yol, blob, sure_s, girdi_tok, cikti_tok}`, "durum" alanı HİÇ YOK
    (eski betik yalnız başarıyı yazıyordu). Bu satırlar 'ok' sayılıp atlanmalı — aksi hâlde A1'e
    taşındıktan sonraki İLK koşumda bu belgeler gereksiz yeniden POST edilir (çift LLM maliyeti).
    Mutasyon kapsaması: `_tamamlanan_oku`'daki `.get("durum", "ok")` varsayılanı kaldırılırsa bu
    test kırmızıya düşer."""
    kok = _kok_kur(tmp_path, {"research/cards/BASE-2026-001-sistem-karnesi.yaml": "eski belge",
                              "docs/YENI.md": "yeni belge"})
    # gercek A1 satirinin AYNISI (r1-brief.md, olcum 12:52Z) — "durum" alani YOK
    (kok / "ilerleme.jsonl").write_text(
        json.dumps({"yol": "research/cards/BASE-2026-001-sistem-karnesi.yaml",
                   "blob": "2fe1…", "sure_s": 172.7, "girdi_tok": 12661, "cikti_tok": 5717}) + "\n",
        encoding="utf-8")

    denenenler = []

    def sahte(anahtar, base, method, path, body=None, timeout=3600):
        doc_id = body["items"][0]["document_id"]
        denenenler.append(doc_id)
        if doc_id == "research/cards/BASE-2026-001-sistem-karnesi.yaml":
            raise AssertionError("eski-semali satir OK sayilmali, yeniden POST edilmemeli")
        return 200, {"usage": {"input_tokens": 1, "output_tokens": 1}}

    monkeypatch.setattr(ing, "_cagri_yap", sahte)
    kayit = _kayit_toplayici()
    sayimlar, _ = ing.calistir(str(kok), ing.VARSAYILAN_DILIM_BAYT, 10, "k", "http://x",
                               "meridian-arsiv", kayit)
    assert denenenler == ["docs/YENI.md"]
    assert sayimlar == {"ok": 1, "gecici_hata": 0, "kalici": 0, "dur": 0}


def test_e3_eski_semali_BUYUK_belge_tum_dilim_plani_atlanir_sifir_post(ing, monkeypatch, tmp_path):
    """K-1 düzeltme turu 2 (2026-09-03, yeniden-inceleme KISMİ bulgusu): eski-şemalı çıplak `yol`
    kaydı yalnız KÜÇÜK içerikle test edilmişti (test_e2) — asıl risk 32KB-60KB bandındaki eski "ok"
    belgeler: yeni `--dilim-bayt` (32.000) eşiğini AŞARLARSA `belge_planla` `yol#k/n` kimlikleri
    üretir, bunlar çıplak `yol` ile HİÇ eşleşmez ve belge parça parça TEKRAR gönderilirdi (KRİTİK-1
    ile aynı çift-LLM-maliyeti sınıfı, eşiği kaymış hâli). BELGE düzeyinde atlama (`_is_plani`nin
    `yol in tamamlanan` ön-kontrolü) bunu önler: çıplak `yol` ok ise dilim sayısı ne olursa olsun
    (burada 90KB -> 3 dilim) HİÇBİR POST atılmaz.

    Mutasyon kapsaması: `_is_plani`'deki belge-düzeyi `if yol in tamamlanan: continue` ön-kontrolü
    kaldırılırsa bu test kırmızıya düşer (3 dilim tek tek POST edilmeye çalışılır, patlayan öter)."""
    icerik = "".join(_bolum(i, 10_000) for i in range(1, 10))  # 9 bolum x 10.000B = 90.000B -> 3 dilim
    assert len(icerik.encode()) == 90_000
    kok = _kok_kur(tmp_path, {"docs/BUYUK-ESKI.md": icerik})
    # eski-sema (durum YOK), belge CIPLAK yol ile "ok" — tek POST'ta basariyla yuklenmis (eski
    # ana yol dilimleme YAPMIYORDU, her belgeyi tek POST'ta gonderiyordu).
    (kok / "ilerleme.jsonl").write_text(
        json.dumps({"yol": "docs/BUYUK-ESKI.md", "blob": "eski-blob",
                   "sure_s": 210.4, "girdi_tok": 9000, "cikti_tok": 4000}) + "\n",
        encoding="utf-8")

    def patlayan(anahtar, base, method, path, body=None, timeout=3600):
        raise AssertionError(f"SIFIR POST beklenirdi, cagrildi: {body['items'][0]['document_id']}")

    monkeypatch.setattr(ing, "_cagri_yap", patlayan)
    kayit = _kayit_toplayici()
    sayimlar, cagri_sayaci = ing.calistir(str(kok), ing.VARSAYILAN_DILIM_BAYT, 10, "k", "http://x",
                                          "meridian-arsiv", kayit)
    assert cagri_sayaci == 0
    assert sayimlar == {"ok": 0, "gecici_hata": 0, "kalici": 0, "dur": 0}
    assert _ilerleme_oku(kok) == [{"yol": "docs/BUYUK-ESKI.md", "blob": "eski-blob",
                                   "sure_s": 210.4, "girdi_tok": 9000, "cikti_tok": 4000}], (
        "ilerleme.jsonl'e yeni bir satir eklenmemeliydi (hicbir is yapilmadi)")


# =================================================================================================
# §F — dilimli ana yol (D1): 90k belge -> 3 dilim, document_id yol#1/3..#3/3, kayipsizlik
# =================================================================================================
def _bolum(i, hedef_bayt):
    on = f"## Bolum{i}\n\n"
    art = "\n\n"
    dolgu_uzunluk = hedef_bayt - len(on.encode()) - len(art.encode())
    assert dolgu_uzunluk > 0
    return on + ("x" * dolgu_uzunluk) + art


def test_f1_90k_belge_uc_dilime_boler_document_id_semasi(ing):
    icerik = "".join(_bolum(i, 10_000) for i in range(1, 10))  # 9 bolum x 10.000B = 90.000B
    assert len(icerik.encode()) == 90_000
    plan = ing.belge_planla("docs/BUYUK.md", icerik, ing.VARSAYILAN_DILIM_BAYT)
    assert [p[0] for p in plan] == ["docs/BUYUK.md#1/3", "docs/BUYUK.md#2/3", "docs/BUYUK.md#3/3"]
    assert "".join(p[1] for p in plan) == icerik, "dilimlerin birlesimi icerige esit degil (kayip)"
    assert all(d == f"{i}/3" for i, (_id, _p, d) in enumerate(plan, 1))


def test_f2_tek_dilimli_belge_document_id_yol_olarak_kalir(ing):
    plan = ing.belge_planla("docs/kucuk.md", "kisa icerik", ing.VARSAYILAN_DILIM_BAYT)
    assert plan == [("docs/kucuk.md", "kisa icerik", None)]


def test_f3_calistir_her_dilimi_ayri_document_id_ile_gonderir(ing, monkeypatch, tmp_path):
    icerik = "".join(_bolum(i, 10_000) for i in range(1, 10))
    kok = _kok_kur(tmp_path, {"docs/BUYUK.md": icerik})
    gonderilenler = []

    def sahte(anahtar, base, method, path, body=None, timeout=3600):
        gonderilenler.append(body["items"][0]["document_id"])
        return 200, {"usage": {"input_tokens": 1, "output_tokens": 1}}

    monkeypatch.setattr(ing, "_cagri_yap", sahte)
    kayit = _kayit_toplayici()
    sayimlar, cagri_sayaci = ing.calistir(str(kok), ing.VARSAYILAN_DILIM_BAYT, 10, "k",
                                          "http://x", "meridian-arsiv", kayit)
    assert gonderilenler == ["docs/BUYUK.md#1/3", "docs/BUYUK.md#2/3", "docs/BUYUK.md#3/3"]
    assert sayimlar["ok"] == 3
    assert cagri_sayaci == 3


# =================================================================================================
# §G — --kuru: POST sayisi 0, plan + bant dagilimi basilir
# =================================================================================================
def test_g_kuru_post_sifir_plan_basilir(ing, monkeypatch, tmp_path, capsys):
    kok = _kok_kur(tmp_path, {"docs/A.md": "a" * 5_000, "docs/B.md": "b" * 20_000})

    def patlayan(*a, **k):
        raise AssertionError("--kuru modunda AG cagrisi YAPILMAMALI")

    monkeypatch.setattr(ing, "_cagri_yap", patlayan)
    rc = ing.main(["--kuru", "--kok", str(kok)])
    assert rc == 0
    cikti = capsys.readouterr().out
    assert "docs/A.md" in cikti and "docs/B.md" in cikti
    assert "bant dagilimi" in cikti
    assert "<=8k" in cikti and "<=32k" in cikti


def test_g2_kuru_tamamlanan_isi_atlar(ing, monkeypatch, tmp_path, capsys):
    kok = _kok_kur(tmp_path, {"docs/A.md": "a" * 100, "docs/B.md": "b" * 100})
    (kok / "ilerleme.jsonl").write_text(
        json.dumps({"yol": "docs/A.md", "dilim": None, "durum": "ok", "neden": None,
                   "bayt": 100, "ts": "x"}) + "\n", encoding="utf-8")
    def patlayan(*a, **k):
        raise AssertionError("ag cagrisi yasak")

    monkeypatch.setattr(ing, "_cagri_yap", patlayan)
    rc = ing.main(["--kuru", "--kok", str(kok)])
    assert rc == 0
    cikti = capsys.readouterr().out
    assert "docs/A.md" not in cikti
    assert "docs/B.md" in cikti


# =================================================================================================
# §H — dilim_sup.py CLI'si EMEKLİ (K-2 ruling, düzeltme turu 1, 2026-09-03): main() fail-closed,
# kütüphane (dilimle) hâlâ çalışır. `v366` bu dosyayı AYRI test eder (saf çekirdek); burada yalnız
# emekliliğin kendisi + kütüphanenin hâlâ import-edilebilir/çalışır olduğu duman testi.
# =================================================================================================
def test_h1_supurme_cli_fail_closed_kuru_dahil(ing):
    assert ing.dilim_sup.main([]) == 2
    assert ing.dilim_sup.main(["--kuru"]) == 2


def test_h2_supurme_kutuphanesi_hala_calisir(ing):
    d = ing.dilim_sup.dilimle("## A\n\nx\n", esik=100)
    assert d == [{"metin": "## A\n\nx\n", "bolum": "A"}]
