"""test_mirror_endpoint_v72.py — uç nokta ŞEMA normalleştirmesi (2026-07-22).

CANLI KANIT: `state/events.jsonl` bugün 33x `mirror_stream_bad_base` taşıyordu (09:26 → 11:54 UTC,
14:52'deki yeniden başlatmadan sonra da sürdü). İKİ AYRI kusur üst üste binmişti:

  (1) KAYNAK — `alpaca.endpoint()` operatörün girdiği tabanı HAM döndürüyordu. Pano alanı şemasız
      bir örnek öneriyor ("Boş bırakılırsa paper-api.alpaca.markets kullanılır"), yani şemasız
      değer beklenen girdi; ama şemasız taban `_url()`un https→wss dönüşümüne uymuyor ve HER
      bağlantı denemesinde yedeğe düşülüyordu. Günde 33 kez devreye giren bir güvenlik ağı ağ
      değil ASIL YOLDUR: gerçekten yanlış bir host yapılandırıldığı günü de aynı satırla gizler.
      Aynı kusur `_account_url()`u da protokolsüz bırakıyordu (httpx reddeder → ping "bağlanılamadı").

  (2) SAYAÇ — o 33 satırın kaynağı ÜRETİM DEĞİLDİ. `test_mirror_health_v68.py`in şemasız uç nokta
      testi gerçek bir `obs.warn` tetikliyor, `obs._emit` de canlı `state/events.jsonl`e yazıyordu;
      conftest'in canlı-state sızıntı bekçisi ise uygulama koşarken KENDİNİ KAPATIYOR. Yani test
      gürültüsü üretim olayı gibi okunuyordu. O test artık `sandbox_state` içinde koşuyor.

Kilit DEĞİŞMEDİ: hostname kilidi `_paper_base()`te aynen duruyor (bkz. son iki test). Buradaki
normalleştirme kilidin GİRDİSİNİ düzeltir, kilidi gevşetmez.

Yasalar:
  E1 İyi biçimli (ve panonun önerdiği şemasız) her taban `mirror_stream_bad_base` BASMAMALI.
  E2 Pozitif kontrol: gerçekten bozuk bir şema hâlâ BASMALI — ağ ölmedi, yalnız normal yol değil.
  E3 REST yolu da mutlak https olmalı (`_account_url()` protokolsüz kalamaz).
  E4 Hostname kilidi yerinde: benzer-görünen host, şemalı da şemasız da, PAPER tabanına düşer.

Ağ YOK, soket YOK, emir YOK; fikstürde sır yoktur ve hiçbir sır değeri basılmaz.
"""
from __future__ import annotations

import pytest

from meridian import mirror_stream as ms
from meridian.adapters import alpaca

LOCKED_URL = "wss://paper-api.alpaca.markets/stream"


def _set_endpoint(monkeypatch, value):
    """Uç noktayı sır katmanının ÜSTÜNDEN besler (dosya/env'e dokunulmaz, sır yazılmaz)."""
    monkeypatch.setattr(alpaca.secrets, "get",
                        lambda n, *a, **k: value if n == "ALPACA_PAPER_ENDPOINT" else "k")


def _capture_warns(monkeypatch) -> list[str]:
    """obs.warn'ı YAKALA. İki işi birden yapar: uyarıyı ölçer ve testin canlı `state/`e yazmasını
    imkânsız kılar (bu dosyanın var oluş sebebi olan sızıntının ta kendisi)."""
    seen: list[str] = []
    monkeypatch.setattr(ms.obs, "warn", lambda event, **fields: seen.append(event))
    return seen


# ---------- E1: iyi biçimli taban ASLA yedeğe düşmez ----------
@pytest.mark.parametrize("raw", [
    "https://paper-api.alpaca.markets",        # kanonik
    "https://paper-api.alpaca.markets/",       # sondaki bölü
    "https://paper-api.alpaca.markets/v2",     # sürüm eki zaten var
    "paper-api.alpaca.markets",                # ŞEMASIZ — panonun önerdiği biçim (canlıdaki hâl)
    "paper-api.alpaca.markets/v2",             # şemasız + sürüm eki
    "  paper-api.alpaca.markets  ",            # kopyala-yapıştır boşluğu
    "wss://paper-api.alpaca.markets",          # zaten ws şeması
    None,                                      # hiç ayarlanmamış → PAPER_BASE
])
def test_well_formed_endpoint_never_emits_bad_base(monkeypatch, sandbox_state, raw):
    """E1 — hepsi AYNI kilitli URL'yi vermeli ve TEK BİR uyarı bile basmamalı."""
    _set_endpoint(monkeypatch, raw)
    seen = _capture_warns(monkeypatch)

    url = ms.MirrorStreamListener._url()

    assert url == LOCKED_URL, f"{raw!r} → {url!r}"
    assert "mirror_stream_bad_base" not in seen, (
        f"{raw!r} iyi biçimli ama yedek yol devrede — güvenlik ağı normal yola dönüşmüş "
        f"durumda ve gerçekten yanlış bir hostu gizler (basılan uyarılar: {seen})")


# ---------- E2: `_paper_base()` HER ZAMAN taşınabilir bir taban döndürür ----------
@pytest.mark.parametrize("raw", [
    "paper-api.alpaca.markets",                        # şemasız
    "  paper-api.alpaca.markets/v2  ",                 # şemasız + boşluk + sürüm eki
    "http://paper-api.alpaca.markets",                 # ZAYIF şema — anahtarlar açık metin giderdi
    "ftp://paper-api.alpaca.markets",                  # anlamsız şema
    "https://paper-api.alpaca.markets.evil.example.com",   # yabancı host (kilit devrede)
    "//paper-api.alpaca.markets",                      # şema-göreli
    "/",                                               # yalnız bölü — boşa iner
    None,
])
def test_paper_base_is_always_transport_ready(monkeypatch, sandbox_state, raw):
    """E2 — `mirror_stream_bad_base` yedeğinin NORMAL yol olmaktan çıkmasının tek sağlam ölçüsü:
    `_paper_base()` hiçbir girdide `https://`/`wss://` dışında bir şey döndürmemeli. Bu değişmez
    tutulduğu sürece yedek yol erişilemez kalır (canlıdaki 33 satırın yapısal karşılığı)."""
    _set_endpoint(monkeypatch, raw)
    base = alpaca._paper_base()
    assert base.startswith(("https://", "wss://")), f"{raw!r} → {base!r}"
    assert not base.endswith("/v2"), f"{raw!r} → sürüm eki tabanda kalmış: {base!r}"


# ---------- E3: ağ ÖLMEDİ — son çare koruması hâlâ konuşuyor ----------
def test_fallback_still_fires_if_paper_base_ever_regresses(monkeypatch, sandbox_state):
    """E3 — E1/E2 yedeği ERİŞİLEMEZ kılar; bu testin işi yedeğin SİLİNMEDİĞİNİ kanıtlamaktır.
    `_paper_base()` bir gün yeniden şemasız değer döndürürse `_url()` sessizce bağlanmaya çalışmaz:
    uyarır ve kilitli PAPER hostuna döner. Sessizce geçen bir yedek, hiç olmayan yedektir."""
    monkeypatch.setattr(alpaca, "_paper_base", lambda: "paper-api.alpaca.markets")
    seen = _capture_warns(monkeypatch)

    url = ms.MirrorStreamListener._url()

    assert "mirror_stream_bad_base" in seen, "bozuk taban SESSİZ geçti — yedek ölmüş"
    assert url == LOCKED_URL, "uyarı bassa bile kilitli PAPER hostuna dönülmeli"


# ---------- E3: REST yolu da mutlak ----------
@pytest.mark.parametrize("raw", ["paper-api.alpaca.markets", "paper-api.alpaca.markets/v2",
                                 "https://paper-api.alpaca.markets/v2"])
def test_account_url_is_absolute_https_and_not_doubled(monkeypatch, sandbox_state, raw):
    """E3 — httpx protokolsüz URL'yi reddeder; şemasız taban `ping()`i "bağlanılamadı"ya çeviriyordu
    (yanlış anahtar sanılabilecek bir arıza). /v2 de ikilenmemeli."""
    _set_endpoint(monkeypatch, raw)
    assert alpaca._account_url() == "https://paper-api.alpaca.markets/v2/account", raw


# ---------- E4: hostname kilidi YERİNDE ----------
@pytest.mark.parametrize("lookalike", [
    "https://paper-api.alpaca.markets.evil.example.com/v2",   # şemalı benzer-görünen host
    "paper-api.alpaca.markets.evil.example.com",              # ŞEMASIZ benzer-görünen host
    "https://evil.example.com/paper-api.alpaca.markets",      # yol parçasında kilit dizesi
])
def test_hostname_lock_survives_normalisation(monkeypatch, sandbox_state, lookalike):
    """E4 — şema tamamlama, kilidi atlatmanın yeni bir yolu OLMAMALI (denetim #51: bu hostlara
    APCA anahtar başlıkları gidiyordu). Kilit hâlâ HOSTNAME karşılaştırır, alt dize değil."""
    _set_endpoint(monkeypatch, lookalike)
    assert alpaca._paper_base() == alpaca.PAPER_BASE, lookalike
    _capture_warns(monkeypatch)
    assert ms.MirrorStreamListener._url() == LOCKED_URL, lookalike
