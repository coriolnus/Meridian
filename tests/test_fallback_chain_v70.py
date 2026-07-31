"""test_fallback_chain_v70.py — YEDEK GERÇEKTEN YEDEK Mİ? (2026-07-22)

Operatör: "NOUS_FALLBACK_MODEL'i ayarla." Ayarlamak tek başına yetmiyordu; üç ayrı sebeple:

  1. `NOUS_FALLBACK_MODEL` kod tarafından OKUNUYORDU ama `secrets` izin listesinde YOKTU — yani
     `secrets.set()` adı reddediyordu ve operatör onu hiçbir zaman ayarlayamıyordu. Düşüş zinciri
     ömrü boyunca tek elemanlı kaldı; olay kaydı "tüm model zinciri cevapsız (tried=1)" diyordu.
     Yedeğin YOKLUĞU, yedeğin BAŞARISIZLIĞI gibi okunuyordu.
  2. `NOUS_MODEL` = `gemini-3.5-flash`, yani zincirin ilk ayağı gemini kotasında. Yedek de aynı
     kotaya bakarsa zincir bir işe yaramaz — 429 dolduğunda iki ayak birden ölür. Canlıda tam bu
     oldu: üç gün boyunca 45 kez 429, 92 kez "boş yanıt".
  3. Bu bir YAPILANDIRMA değişmezidir, kod değişmezi değil — o yüzden burada test edilir. Bir
     gün biri yedeği "daha iyi" bir gemini modeline çevirirse hata sessiz olur: her şey çalışır
     gibi görünür, ta ki kota dolana kadar.

Ölçülen gerçek (yerel ajanla doğrulandı, 2026-07-22):
    hermes chat --model tencent/hy3:free  →  "Switched to fallback model:
    tencent/hy3:free via gemini → tencent/hy3:free via nous"
Yani model kimliği SAĞLAYICIYI da değiştiriyor; ikinci ayak Nous Portal kotasında.
"""
from __future__ import annotations

import pytest

from meridian import secrets


# provider ön-eki → kota sahibi. Model kimliğinden sağlayıcıyı çıkarmanın tek dürüst yolu bu:
# `gemini-*` Google kotası, `<satıcı>/<model>` biçimi Nous Portal yönlendirmesi.
def _quota_owner(model: str | None) -> str | None:
    if not model:
        return None
    m = model.strip().lower()
    if m.startswith(("gemini-", "models/gemini")):
        return "google"
    if m.startswith(("claude-", "anthropic/")):
        return "anthropic"
    if "/" in m:
        return "nous_portal"          # tencent/hy3:free, meta/…, qwen/… → Portal üzerinden
    return "unknown"


def _live(name: str) -> str | None:
    """CANLI operatör yapılandırmasını oku. `secrets` TTL önbelleklidir ve suite içinde başka bir
    test `config.STATE`'i kum havuzuna yönlendirmiş olabilir — o zaman önbellekte boş değer kalır ve
    bu testler SIRAYA bağlı olur. Önbellek temizlenir; yapılandırma yoksa test ATLANIR (temiz bir
    klonda ya da CI'da operatörün sırları yoktur — orada düşmek yanlış alarmdır)."""
    secrets._cache.clear()
    return secrets.get(name)


def _skip_if_unconfigured() -> tuple[str, str]:
    prim, fb = _live("NOUS_MODEL"), _live("NOUS_FALLBACK_MODEL")
    if not prim or not fb:
        pytest.skip("beyin zinciri bu ortamda yapılandırılmamış (temiz klon/CI)")
    return prim, fb


def test_fallback_name_is_settable():
    """İZİN LİSTESİ HATASI: kod okuyor ama store reddediyorsa değişken KALICI olarak boş kalır."""
    assert "NOUS_FALLBACK_MODEL" in secrets.ALLOWED, \
        "kod bu adı okuyor ama secrets.set onu reddeder — yedek hiç ayarlanamaz"


def test_the_chain_has_two_legs():
    """Düşüş zinciri en az iki elemanlı olmalı; tek elemanlı bir 'zincir' zincir değildir."""
    prim, fb = _skip_if_unconfigured()
    models = [m for m in dict.fromkeys([prim, fb]) if m]
    assert len(models) >= 2, f"düşüş zinciri tek elemanlı: {models}"


def test_the_two_legs_are_on_different_quotas():
    """ASIL DEĞİŞMEZ: 429 tek bir kotayı öldürür. İki ayak aynı kotadaysa yedek TİYATRODUR —
    her şey doğru yapılandırılmış görünür ve kota dolduğu gün ikisi birden düşer."""
    primary, fallback = _skip_if_unconfigured()
    p, f = _quota_owner(primary), _quota_owner(fallback)
    assert p != f, (f"yedek birincille AYNI kotada ({p}): {primary!r} → {fallback!r}. "
                    f"429 ikisini birden düşürür; bu bir yedek değil, ikinci bir ad.")


def test_quota_owner_classifier_is_not_vacuous():
    """Sınıflandırıcı çalışmıyorsa yukarıdaki test boş bir iddia olurdu."""
    assert _quota_owner("gemini-3.5-flash") == "google"
    assert _quota_owner("tencent/hy3:free") == "nous_portal"
    assert _quota_owner("gemini-3.5-flash") == _quota_owner("gemini-2.0-pro")   # aynı kota
    assert _quota_owner("gemini-3.5-flash") != _quota_owner("tencent/hy3:free")
    assert _quota_owner(None) is None


def test_the_free_leg_is_actually_free():
    """Operatörün kredisi yok: yedek ÜCRETSİZ bir model olmak zorunda, yoksa ilk 429'da
    faturalı bir çağrıya düşülür (bütçe kapısı ücretli beyinleri zaten kapatır — ama bu yol
    ajan CLI'sinden geçtiği için o kapıyı görmez)."""
    fb = _skip_if_unconfigured()[1].lower()
    assert fb.endswith(":free") or "free" in fb, \
        f"yedek ücretsiz görünmüyor: {fb!r} — operatörün Portal kredisi yok"


def test_agent_config_fallback_matches_the_secret():
    """Yerel ajanın kendi `fallback_providers` kaydı ile Meridian'ın sırrı AYRIŞMAMALI —
    iki yerde tanımlanan bir yasa, bu kod tabanının baskın hata desenidir."""
    import pathlib
    import yaml
    cfg_p = pathlib.Path.home() / ".hermes" / "config.yaml"
    if not cfg_p.exists():
        pytest.skip("yerel ajan kurulu değil")
    cfg = yaml.safe_load(cfg_p.read_text()) or {}
    fbs = cfg.get("fallback_providers") or []
    if not fbs:
        pytest.skip("ajan birincil sağlayıcısı zaten nous — fallback eklenmez (döngü olmaz)")
    assert fbs[0].get("model") == _skip_if_unconfigured()[1], \
        "ajan yapılandırması ile sır AYRIŞTI — hermes._sync_agent_config yeniden koşmalı"
    assert fbs[0].get("provider") != (cfg.get("model") or {}).get("provider"), \
        "ajanın yedeği birincil sağlayıcının kendisi — kota bağımsızlığı yok"
