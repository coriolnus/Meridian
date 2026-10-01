"""v608 — G4 KALINTILARI: konuşan filonun Telegram kanalında iki davranış kusuru + belge ayrışmaları (2026-10-01).

Kaynak: G4 dal sonu incelemesi (`.superpowers/sdd/2026-09-30-konusan-filo-parca1b-g4-kanal-kablolamasi/final-review.md`
M-2, M-3, M-7) + G3b Task 2 incelemesi M4. Botlar canlıda KAPALI; düzeltmeler açılıştan önce.

  * M-2 — ALINTININ İÇERİK SATIRI TEK KURALDIR. Bot cevabına verilen yanıtta hafıza kaydının `(yanıt: …)` etiketi İMZA
    satırını (`💬 @bot · oturum (i/n)`) alıyordu, içeriği değil; gövdesiz `unut:` sorgusu ise imzayı atlıyordu — iki
    kural. Artık ikisi de `bot_kanal.alinti_icerik_satiri`dan geçer: baştaki boş satırlar, sohbet imza satırı (tanıyıcı
    `bot_kanal._SOHBET_IMZA` — Telegram dinleyicisi onu İTHAL eder) ve araçsız-veri uyarıları atlanır. Rapor alıntısında
    ilk satır (rapor başlığı) İÇERİKTİR: bugünkü davranış korunur. İçerik satırı yoksa etiket UYDURULMAZ.
  * M-3 — gövdesiz `unut:` yanıtında `bot_kanal.UYARI_ARACSIZ` / `UYARI_OLCULEMEDI` satırı sorgu olmaz (aynı kural).
  * M-7 — `unut` bekleyen kaydının şema yorumu (`bot_kanal.UNUT_BEKLEYEN` üstündeki yorum) kodun yazdığı HER alanı
    sayar: alanlar koddan ÖLÇÜLÜR (gerçek akış + `_bekleyen_guncelle` çağrılarının anahtar sözcükleri), yorumla
    kıyaslanır; `codelaw.DECLARED_SINKS` gerekçesi listeyi kopyalamaz, şema yorumunu gösterir.
  * G3b T2 M4 — sohbet profillerinin üretilmiş `distribution.yaml` `env_requires`ı `API_SERVER_KEY`i anar (Hermes
    `/p/<bot>/` isteğini profilin `.env`indeki anahtarla doğrular); ad, kanal katmanının okuduğu adla aynıdır.

Girdiler GERÇEK üreticilerden kurulur: bot cevabının Telegram metni `telegram_dinleyici.isle` + gerçek `bota_sor`
(sahte taşıyıcı/hafıza) ile üretilir, yanıt o metne verilir — çivi "benzerini" değil üretimdeki girdiyi sınar.
CANLIYA DOKUNMAZ: `sandbox_state` altında, ağ yok, `sleep` yok.
"""
from __future__ import annotations

import ast
import inspect
import pathlib
import re

import pytest
import yaml

from meridian import bot_kanal as bk, codelaw, store, telegram_dinleyici as td
from tests.conftest import betikten_modul_yukle
from tests.test_bot_kanal_v593 import SIMDI, SahteHafiza

KOK = pathlib.Path(__file__).resolve().parent.parent
YETKILI = "4242"
RAPOR = "🔭 Meridian bekçi — 29 Eyl\n1. TAKILI AAPL planı 3 gündür bekliyor"


class Tasiyici:
    """Araç sayısı ayarlanabilir sahte taşıyıcı: 0 → `UYARI_ARACSIZ`, `None` → `UYARI_OLCULEMEDI` (gerçek bota_sor)."""

    def __init__(self, metin="tamam", arac=2):
        self.metin, self.arac, self.cagrilar = metin, arac, []

    def sor(self, bot, mesaj, oturum):
        self.cagrilar.append((bot, mesaj, oturum))
        return bk.TasiyiciSonuc(self.metin, arac_cagrilari=self.arac)


def _gercek_bota_sor(tasiyici, hafiza):
    return lambda bot, mesaj, kanal, oturum: bk.bota_sor(bot, mesaj, kanal, oturum, tasiyici=tasiyici,
                                                         hafiza=hafiza, simdi=SIMDI)


def _mesaj(metin, yanit=None, mid=7):
    m = {"message_id": mid, "chat": {"id": int(YETKILI), "type": "private"}, "from": {"id": int(YETKILI)},
         "text": metin}
    if yanit is not None:
        m["reply_to_message"] = {"message_id": 41, "text": yanit}
    return m


def _telegram(metin, *, bota_sor, yanit=None):
    """Tek güncelleme `isle`den geçer; operatöre giden Telegram metinleri (parçalar) döner."""
    gidenler = []
    td.isle({"update_id": 1, "message": _mesaj(metin, yanit)}, yetkili_sohbet=YETKILI, bota_sor=bota_sor,
            gonder=lambda t, r: gidenler.append(t) or True, bugun="20260929")
    return gidenler


def _bot_cevabi(metin, arac=2):
    """`@bekci` sorusuna GERÇEK `bota_sor` + GERÇEK Telegram imzası/bölmesiyle üretilen cevap parçaları."""
    return _telegram("@bekci durum?", bota_sor=_gercek_bota_sor(Tasiyici(metin, arac), SahteHafiza()))


def _yanit_turu(yanitlanan, sozler):
    """Operatör `yanitlanan` Telegram metnine `sozler` ile yanıt verir; (bota giden metin, hafıza) döner."""
    cagrilar, h = [], SahteHafiza()
    gercek = _gercek_bota_sor(Tasiyici("anlaşıldı"), h)

    def bota_sor(bot, mesaj, kanal, oturum):
        cagrilar.append(mesaj)
        return gercek(bot, mesaj, kanal, oturum)

    _telegram(sozler, bota_sor=bota_sor, yanit=yanitlanan)
    (giden,) = cagrilar
    return giden, h


# =================================================================================================
# M-2 — rapor alıntısı (bugünkü davranış KORUNUR)
# =================================================================================================

def test_rapor_alintisina_yanitta_etiket_bugunku_gibi_rapor_basligi(sandbox_state):
    _, h = _yanit_turu(RAPOR, "bu kalem ne?")
    ((_, hafizaya, _, _),) = h.donusler
    assert hafizaya == "(yanıt: 🔭 Meridian bekçi — 29 Eyl)\nbu kalem ne?"
    giden, h = _yanit_turu(RAPOR, "hatırla: yarın bak")
    assert giden == "hatırla: yarın bak (yanıt: 🔭 Meridian bekçi — 29 Eyl)"
    assert h.yazilanlar[0][1] == giden.split(":", 1)[1].strip()


# =================================================================================================
# M-2 — bot cevabına yanıt (YENİ): etiket İÇERİK satırıdır, imza değil
# =================================================================================================

def test_bot_cevabina_yanitta_hafiza_etiketi_icerik_satiri(sandbox_state):
    (cevap,) = _bot_cevabi("AAPL planı onay bekliyor\nikinci satır")
    assert cevap.startswith("💬 @bekci · tg-bekci-20260929\n")            # girdi gerçekten imzalı bot cevabı
    _, h = _yanit_turu(cevap, "bu kalem ne?")
    ((_, hafizaya, _, _),) = h.donusler
    assert hafizaya == "(yanıt: AAPL planı onay bekliyor)\nbu kalem ne?"


def test_bot_cevabina_yanitta_hatirla_etiketi_icerik_satiri(sandbox_state):
    (cevap,) = _bot_cevabi("AAPL planı onay bekliyor\nikinci satır")
    giden, h = _yanit_turu(cevap, "hatırla: cuma tekrar bak")
    assert giden == "hatırla: cuma tekrar bak (yanıt: AAPL planı onay bekliyor)"
    assert h.yazilanlar[0][1] == "cuma tekrar bak (yanıt: AAPL planı onay bekliyor)"


@pytest.mark.parametrize("arac, uyari", [(0, bk.UYARI_ARACSIZ), (None, bk.UYARI_OLCULEMEDI)],
                         ids=["aracsiz", "olculemedi"])
def test_uyarili_bot_cevabina_yanitta_etiket_uyariyi_atlar(sandbox_state, arac, uyari):
    (cevap,) = _bot_cevabi("GEÇTİ kararı 3 kalem\nayrıntı", arac=arac)
    assert cevap.split("\n")[1] == uyari                                   # gerçek önek imzanın hemen altında
    _, h = _yanit_turu(cevap, "neden?")
    assert h.donusler[0][1] == "(yanıt: GEÇTİ kararı 3 kalem)\nneden?"
    giden, _ = _yanit_turu(cevap, "hatırla: kontrol et")
    assert giden == "hatırla: kontrol et (yanıt: GEÇTİ kararı 3 kalem)"


def test_cok_parcali_cevabin_ikinci_parcasina_yanitta_etiket_o_parcanin_icerigi(sandbox_state):
    uzun = "\n".join(f"satır {i:04d} " + "y" * 90 for i in range(120))
    parcalar = _bot_cevabi(uzun)
    assert len(parcalar) >= 3 and parcalar[1].split("\n", 1)[0].endswith(f" (2/{len(parcalar)})")
    ikinci_icerik = parcalar[1].split("\n")[1]
    _, h = _yanit_turu(parcalar[1], "bunu aç")
    assert h.donusler[0][1] == f"(yanıt: {ikinci_icerik[:bk.KAYNAK_ETIKETI_TAVANI]})\nbunu aç"
    giden, _ = _yanit_turu(parcalar[1], "hatırla: sonra")
    assert giden == f"hatırla: sonra (yanıt: {ikinci_icerik[:bk.KAYNAK_ETIKETI_TAVANI]})"


@pytest.mark.parametrize("alinti", ["💬 @karne · tg-karne-r55", "💬 @karne · tg-karne-r55 (2/3)\n\n",
                                    f"💬 @karne · tg-karne-r55\n{bk.UYARI_ARACSIZ}",
                                    f"\n💬 @karne\n{bk.UYARI_OLCULEMEDI}\n  \n"],
                         ids=["imza", "parca_ekli_imza", "imza_uyari", "eski_imza_uyari_bosluk"])
def test_iceriksiz_alintida_etiket_uydurulmaz(sandbox_state, alinti):
    # İçerik satırı yoksa imza ya da uyarı etikete GİRMEZ (ikinci kural olurdu) ve "(yanıt: )" gibi boş bir etiket de
    # yazılmaz: not ve dönüş kaydı alıntısız gider (gövdesiz `unut:` sorgusunun "uydurulmaz" kuralının aynısı).
    assert bk.alinti_icerik_satiri(alinti) == "" and bk.kaynak_etiketi(alinti) is None
    giden, h = _yanit_turu(alinti, "hatırla: not")
    assert giden == "hatırla: not" and h.yazilanlar[0][1] == "not"
    _, h = _yanit_turu(alinti, "ne demek?")
    assert h.donusler[0][1] == "ne demek?"


# =================================================================================================
# M-3 — gövdesiz `unut:` yanıtında uyarı satırı SORGU OLMAZ
# =================================================================================================

@pytest.mark.parametrize("arac", [0, None], ids=["aracsiz", "olculemedi"])
def test_govdesiz_unut_uyari_satirini_sorgu_yapmaz(sandbox_state, arac):
    (cevap,) = _bot_cevabi("GEÇTİ kararı 3 kalem\nayrıntı", arac=arac)
    giden, _ = _yanit_turu(cevap, "unut:")
    assert giden == "unut: GEÇTİ kararı 3 kalem"
    assert td.komut_oneki(giden) == ("unut", "GEÇTİ kararı 3 kalem")


@pytest.mark.parametrize("uyari", [bk.UYARI_ARACSIZ, bk.UYARI_OLCULEMEDI], ids=["aracsiz", "olculemedi"])
def test_govdesiz_unut_yalniz_imza_ve_uyari_varsa_govdesiz_gider(sandbox_state, uyari):
    giden, _ = _yanit_turu(f"💬 @karne · tg-karne-r55\n{uyari}\n", "unut:")
    assert giden == "unut:"


# =================================================================================================
# M-2/M-3 — TEK KAYNAK: kural, imza deseni ve uyarı metinleri `bot_kanal`da; dinleyici ithal eder
# =================================================================================================

def test_alinti_kurali_ve_imza_deseni_tek_kaynak():
    for ad in ("SOHBET_IMZA", "OTURUM_AYRACI", "PARCA_EKI", "_SOHBET_IMZA", "alinti_icerik_satiri", "kaynak_etiketi"):
        assert getattr(td, ad) is getattr(bk, ad), ad
    atananlar = {h.id for n in ast.parse(inspect.getsource(td)).body if isinstance(n, ast.Assign)
                 for h in n.targets if isinstance(h, ast.Name)}
    assert not atananlar & {"SOHBET_IMZA", "OTURUM_AYRACI", "PARCA_EKI", "_SOHBET_IMZA"}
    tanimlar = {n.name for n in ast.parse(inspect.getsource(td)).body if isinstance(n, ast.FunctionDef)}
    assert "_alinti_icerik_satiri" not in tanimlar                         # ikinci kural emekli
    assert not hasattr(bk, "alinti_ilk_satiri")                            # imzayı içerik sayan eski kural emekli
    kaynak = inspect.getsource(td)
    assert bk.UYARI_ARACSIZ not in kaynak and bk.UYARI_OLCULEMEDI not in kaynak


# =================================================================================================
# M-7 — bekleyen kaydın şema yorumu kodun yazdığı HER alanı sayar (alanlar koddan ölçülür)
# =================================================================================================

def _sema_yorumu() -> str:
    satirlar = inspect.getsource(bk).split("\n")
    i = next(i for i, s in enumerate(satirlar) if s.startswith("UNUT_BEKLEYEN ="))
    yorum = []
    while satirlar[i - 1].startswith("#:"):
        i -= 1
        yorum.insert(0, satirlar[i])
    assert yorum, "UNUT_BEKLEYEN üstünde şema yorumu yok"
    return "\n".join(yorum)


def _guncelleme_anahtarlari() -> set[str]:
    """`_bekleyen_guncelle(kod, alan=…)` çağrılarının anahtar sözcükleri (statik ölçüm — her yol koşmasa da görünür)."""
    return {k.arg for n in ast.walk(ast.parse(inspect.getsource(bk))) if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name) and n.func.id == "_bekleyen_guncelle" for k in n.keywords if k.arg}


def test_unut_bekleyen_sema_yorumu_kodun_yazdigi_her_alani_sayar(sandbox_state):
    h = SahteHafiza(adaylar=[("m-1", "eski not"), ("m-2", "ikinci not")])

    def sor(metin):
        return bk.bota_sor("bekci", metin, "pano", "o", tasiyici=Tasiyici(), hafiza=h, simdi=SIMDI)

    kod_deseni = re.compile(r"onayla: unut ([0-9a-f]{6})")
    eski = kod_deseni.search(sor("unut: eski")).group(1)
    yeni = kod_deseni.search(sor("unut: yine eski")).group(1)          # eskiyi `suresi_doldu` + `yerine_gecen` yapar
    assert "Unuttum" in sor(f"onayla: unut {yeni}") and "Geri aldım" in sor(f"geri al: {yeni}")
    kayitlar = store.read_json(bk.UNUT_BEKLEYEN, {})
    assert kayitlar[eski]["yerine_gecen"] == yeni                       # akış gerçekten o alanı yazdı
    olculen = {a for k in kayitlar.values() for a in k} | _guncelleme_anahtarlari()
    assert {"yerine_gecen", "geri_alinan_idler", "unutulan_idler", "denenen", "kalan"} <= olculen
    yorum = _sema_yorumu()
    eksik = sorted(a for a in olculen if not re.search(rf"(?<![A-Za-z_]){a}(?![A-Za-z_])", yorum))
    assert not eksik, f"şema yorumunda olmayan alanlar: {eksik}"


def test_declared_sinks_gerekcesi_alan_listesini_kopyalamaz_sema_yorumunu_gosterir():
    # Tek-kaynak yasası (M-7): alan listesi TEK yerde tam olur; beyan gerekçesi listeyi kopyalamaz, şemayı gösterir.
    gerekce = codelaw.DECLARED_SINKS[bk.UNUT_BEKLEYEN]
    assert "bot_kanal.UNUT_BEKLEYEN" in gerekce
    assert "ts, son, durum" not in gerekce and "bellek kimlikleri" not in gerekce


# =================================================================================================
# G3b T2 M4 — sohbet manifesti `API_SERVER_KEY`i anar (üretilmiş; elle düzenleme yok)
# =================================================================================================

def _ur():
    return betikten_modul_yukle(KOK / "ops/sohbet_profili_uret.py", "sohbet_profili_uret_v608")


def _aktifler():
    from meridian import kadro
    return list(kadro.aktif_botlar())


@pytest.mark.parametrize("bot", _aktifler(), ids=lambda b: b.ad)
def test_sohbet_manifesti_api_sunucu_anahtarini_ister(bot):
    u = _ur()
    m = yaml.safe_load((KOK / f"deploy/hermes/sohbet/profiles/{bot.ad}/distribution.yaml").read_text(encoding="utf-8"))
    girdiler = [g for g in m["env_requires"] if g["name"] == u.SOHBET_API_SUNUCU_ANAHTARI]
    assert len(girdiler) == 1 and girdiler[0]["required"] is True
    aciklama = girdiler[0]["description"]
    assert aciklama == u.SOHBET_API_SUNUCU_ANAHTARI_ACIKLAMASI and ".env" in aciklama and "401" in aciklama
    # Üreteç girdisi depodaki üretilmiş dosyayla aynı (elle değil, üreteçle yazıldı — v599 `--kontrol` de bakar).
    assert yaml.safe_load(u.uret()[f"{u.SOHBET_KOK}/{bot.ad}/distribution.yaml"]) == m


def test_api_sunucu_anahtar_adi_kanal_katmaninin_okudugu_adla_ayni(monkeypatch):
    # Ayrışma çivisi: üreteç `bot_kanal`ı ithal EDEMEZ (zinciri `meridian.obs`a ulaşır — v599), adı kendi sabitinde
    # tutar; kanal katmanının `HermesTasiyici` varsayılanı credential'ı hangi adla OKUYORSA manifest o adı anmalı.
    okunan = []
    monkeypatch.setattr(bk.secrets, "credential_oku", lambda ad: okunan.append(ad) or "K" * 32)
    bk.HermesTasiyici()._anahtar()
    assert okunan == [_ur().SOHBET_API_SUNUCU_ANAHTARI]
