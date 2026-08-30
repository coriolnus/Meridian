"""test_kart_hijyeni_v279.py — ÖN-KAYIT KARTI HİJYENİ (M8/U2+U3 kapanışı, 2026-08-23).

KAYIT ÇAPI — NEDEN BU DOSYA VAR. Üç kusur AYNI turda ölçüldü (docs/ELEME-WP5-2026-08-23.md
kalem 3 ve kalem 14) ve üçü de ELLE bakımın kaçırdığı sınıftı:

  1. ÇİFT ÜST-DÜZEY ANAHTAR. `EDG-2026-038` iki `verdict:` taşıyordu (`:120` boş placeholder +
     `:122` gerçek hüküm). ZARAR O GÜN OLMADI ama TESADÜFEN: PyYAML son-kazanır, ikinci (dolu)
     blok kazandı. Sıra ters olsaydı GERÇEK HÜKÜM SESSİZCE YUTULURDU — ve bir kartın hükmü
     yutulduğunda geriye "ölçüldü" diyen ama hükmü boş bir kart kalır, yani ölçüm defteri
     yalan söyler. Rol-1 vakayı 2026-08-23'te düzeltti; ÇİVİ BURADA çünkü sınıfın nüfusu
     tesadüfen 1'di, yapısal olarak değil.

  2. `pending-*` KALINTISI. 65 kartın 41'i ölçüm bittikten SONRA bile `pending-…` trial_id
     taşıyordu. K defteri (çoklu-sınama cezası) bu alandan okunur; "pending" bir koşum adı
     DEĞİL, bir söz'dür — hangi hücrenin gerçekten koştuğu kartın kendisinden okunamaz hale
     gelir ve kanıt zinciri (kart → `research/olcumler/<koşum>/<hücre>`) kopar. U2 turu 38
     ölçülmüş/arşiv kartını gerçek trial_id'ye çevirdi.

  3. BAYAT ENDEKS. `research/cards/README.md` EDG-001/002'yi hâlâ "Aktif kartlar (registered)"
     başlığında listeliyordu; ikisi de 2026-07-31'den beri `archived`. U3 turu endeksi
     `ops/kart_endeksi_uret.py` üreticisine bağladı (elle bakım bırakıldı).

KAPSAM — BU DOSYA NEYİ ÖLÇER, NEYİ ÖLÇMEZ:
  * ÖLÇER: kart dosyalarının BİÇİM hijyeni (çift anahtar), `k_registry.trial_ids` alanının
    STATÜYLE TUTARLILIĞI, ve README endeksinin kartlarla senkronu.
  * ÖLÇMEZ: kartın İÇERİĞİNİ — tez, eşik, kill-list, hüküm. Onlar Rol-1'in hükmüdür
    (CLAUDE.md §3: ölçüm ajanı karta dokunmaz). Bir trial_id'nin DOĞRU hücreyi gösterip
    göstermediği de burada sınanmaz: `EXE-2026-001 e1_grid/…` gibi tarih-eki atılmış ve
    `EXE-2026-006 EXE-006-limit-bacagi-hukum/…` gibi mantıksal koşum adları BİLEREK serbest
    biçimlidir (v219 aynı gerekçeyle bu alana kimlik öneki zorunluluğu koymaz). Burada
    yasaklanan tek dizge `pending`tir ve yalnız ÖLÇÜLMÜŞ kartlarda.

`tests/test_kart_kimlik_v219.py` (kimlik tekilliği) ve `tests/test_kart_hukum_damgasi_v251.py`
ile ÇAKIŞMAZ, onları TAMAMLAR: v219 dosya adı ↔ `card_id` özdeşliğine bakar ve `trial_ids`i
adıyla kapsam dışı bırakır; burası tam o boşluğun statüye bağlı yarısını kapatır.
"""
from __future__ import annotations

import pathlib

import pytest
import yaml

from tests.conftest import betikten_modul_yukle

KOK = pathlib.Path(__file__).resolve().parents[1]
KARTLAR = KOK / "research" / "cards"
URETICI_YOLU = KOK / "ops" / "kart_endeksi_uret.py"

#: `pending-*` kalıntısı YASAK olan statüler. `registered`/`measuring` BİLEREK dışarıda —
#: orada `pending` DOĞRU hâldir (ölçüm henüz koşmadı) ve temizlenirse kart yalan söyler.
OLCULMUS_STATULER = frozenset({"measured", "measured_partial", "archived"})


def _uretici():
    """`ops/kart_endeksi_uret.py`yi dosyadan yükler (ops bir paket değil, import edilemez)."""
    return betikten_modul_yukle(URETICI_YOLU, "kart_endeksi_uret")


def cift_ust_duzey_anahtarlar(metin: str) -> list[str]:
    """Bir YAML belgesinde ÇİFT geçen üst-düzey anahtarlar (WP5 eleme turunun dedektörü).

    `yaml.compose` düğüm ağacını verir ve sözlüğe ÇEVİRMEZ — `safe_load` son-kazanır kuralıyla
    çifti zaten yutmuş olurdu, yani kusuru gören tek yol ham düğüm listesidir.
    """
    kok = yaml.compose(metin)
    if not isinstance(kok, yaml.MappingNode):
        return []
    adlar = [anahtar.value for anahtar, _deger in kok.value]
    return sorted({ad for ad in adlar if adlar.count(ad) > 1})


def _kartlar() -> list[tuple[pathlib.Path, str, dict]]:
    kayitlar = []
    for yol in sorted(KARTLAR.glob("*.yaml")):
        ham = yol.read_text(encoding="utf-8")
        kayitlar.append((yol, ham, yaml.safe_load(ham)))
    assert kayitlar, f"kart bulunamadı: {KARTLAR}"
    return kayitlar


# ==================================================================================
# (a) DUP-ANAHTAR ÇİVİSİ — EDG-2026-038 vakası (2026-08-23 Rol-1'ce düzeltildi)
# ==================================================================================

def test_hicbir_kartta_cift_ust_duzey_anahtar_yok():
    suclular = {
        yol.name: cift_ust_duzey_anahtarlar(ham)
        for yol, ham, _ in _kartlar()
        if cift_ust_duzey_anahtarlar(ham)
    }
    assert not suclular, (
        "Çift üst-düzey anahtar taşıyan kart(lar) var — PyYAML son-kazanır, yani ÖNCEKİ blok "
        f"SESSİZCE yutuluyor (EDG-2026-038 vakası): {suclular}"
    )


def test_dup_dedektoru_sentetik_carpik_karti_YAKALAR():
    """POZİTİF KONTROL (a): dedektör gerçekten ölçüyor mu, yoksa her zaman boş mu dönüyor?"""
    sentetik = (
        "card_id: SENTETIK-2026-000\n"
        "status: measured\n"
        "verdict:   # boş placeholder — EDG-038'in birinci bloğu\n"
        "verdict: gerçek hüküm burada\n"
    )
    assert cift_ust_duzey_anahtarlar(sentetik) == ["verdict"]
    # ve `safe_load` kusuru GERÇEKTEN yutuyor — çivinin neden gerektiğinin kanıtı:
    assert yaml.safe_load(sentetik)["verdict"] == "gerçek hüküm burada"
    # temiz bir kartta yanlış-alarm ÜRETMEZ:
    assert cift_ust_duzey_anahtarlar("card_id: X\nstatus: measured\nverdict: tek\n") == []


# ==================================================================================
# (b) `pending-` kalıntısı — yalnız ÖLÇÜLMÜŞ kartlarda yasak
# ==================================================================================

def test_olculmus_kartlarda_pending_trial_id_kalintisi_yok():
    suclular = {}
    olculmus = 0
    for yol, _ham, kart in _kartlar():
        if kart.get("status") not in OLCULMUS_STATULER:
            continue
        olculmus += 1
        tids = [str(t) for t in ((kart.get("k_registry") or {}).get("trial_ids") or [])]
        kalinti = [t for t in tids if t == "pending" or t.startswith("pending-")]
        if kalinti:
            suclular[yol.name] = kalinti
    assert olculmus > 0, "sınama boşa koştu: ölçülmüş kart bulunamadı"
    assert not suclular, (
        "Ölçülmüş kart(lar) hâlâ `pending` trial_id taşıyor — K defteri hangi hücrenin koştuğunu "
        f"okuyamaz (U2, docs/ELEME-WP5-2026-08-23.md kalem 3): {suclular}"
    )


def test_olculmemis_kartlarin_pendingi_DOKUNULMAZ():
    """`registered`/`measuring` kartlarda `pending` DOĞRU hâldir — temizlenmesi yasak.

    Bu sınama (b)'nin ters yönünü çivi altına alır: bir gün "tüm pending'leri sil" diye
    genelleştirilirse, ölçülmemiş kart ölçülmüş gibi görünür ve UYDURMA YASAĞI çiğnenir.
    """
    for yol, _ham, kart in _kartlar():
        if kart.get("status") not in {"registered", "measuring"}:
            continue
        tids = [str(t) for t in ((kart.get("k_registry") or {}).get("trial_ids") or [])]
        assert tids, f"{yol.name}: ölçülmemiş kartın trial_ids alanı BOŞ — ne söz ne koşum"


# ==================================================================================
# (c) README endeksi kartlarla senkron
# ==================================================================================

def test_readme_endeksi_kartlarla_senkron():
    kod = _uretici().main(["--kontrol"])
    assert kod == 0, (
        "research/cards/README.md endeksi kart durumlarıyla ayrışmış — "
        "`python ops/kart_endeksi_uret.py` ile yeniden üret (U3; elle düzenleme yok)"
    )


def test_endeks_kapisi_sentetik_bayat_readmeyi_YAKALAR(tmp_path):
    """POZİTİF KONTROL (c): `--kontrol` her zaman 0 mu dönüyor, yoksa gerçekten mi ölçüyor?"""
    uretici = _uretici()
    bayat = tmp_path / "README.md"
    bayat.write_text(
        "# sahte defter\n\n"
        f"{uretici.BASLA}\n"
        "- **EDG-2026-001** (`registered`) — BAYAT SATIR: kart 2026-07-31'den beri archived\n"
        f"{uretici.BITIR}\n",
        encoding="utf-8",
    )
    assert uretici.main(["--kontrol", "--cikti", str(bayat)]) == 1, "bayat endeks YAKALANMADI"
    assert uretici.main(["--cikti", str(bayat)]) == 0
    assert uretici.main(["--kontrol", "--cikti", str(bayat)]) == 0, "yeniden üretim GÜNCEL yapmadı"
    # elle yazılan bölüm KORUNDU (üretici yalnız sentinel arasını sahiplenir):
    assert bayat.read_text(encoding="utf-8").startswith("# sahte defter")


def test_endeks_uretimi_deterministik_ve_damgasiz():
    """Aynı kartlardan aynı metin çıkar; çıktıda üretim ZAMANI yoktur.

    Damga olsaydı her koşu diff üretir ve (c)'deki bayatlık kapısı anlamsızlaşırdı.
    """
    uretici = _uretici()
    bir, iki = uretici.endeks(), uretici.endeks()
    assert bir == iki
    assert "2026-08-2" not in bir.split("\n")[4], "endeks başlığına tarih damgası sızmış"


@pytest.mark.parametrize("statu", sorted(OLCULMUS_STATULER | {"registered", "measuring"}))
def test_her_statu_endekste_bir_kovaya_dusuyor(statu):
    """Statü kovası tanınmıyorsa kart 'diğer'e ADIYLA düşer — sessiz yutma YOK (YASA 4)."""
    uretici = _uretici()
    bilinen = {s for _ad, _baslik, statuler in uretici.KOVALAR for s in statuler}
    kayit = {"dosya": "x.yaml", "card_id": "SENTETIK-2026-000", "status": statu,
             "konu": "sentetik", "hukum": ""}
    metin = uretici.endeks([kayit])
    assert "SENTETIK-2026-000" in metin, f"{statu} statülü kart endeksten DÜŞTÜ"
    if statu not in bilinen:
        assert "Diğer" in metin
