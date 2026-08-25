"""GEREKÇELİ RET — "görmedim" ile "gördüm ve istemedim" AYRI ŞEYLERDİR · v306

OPERATÖR İSTEĞİ (2026-08-25): "sembollerin üzerine tıklayıp bilgilerini görebilmeliyim, ve
review'da ise onaylayabilmeliyim veya reddedebilmeliyim."

ÖLÇÜLDÜ — RET, SANILDIĞI ŞEY DEĞİL: `girise_uygun` yasası `GO ya da (REVIEW ve operatör
onaylı)`. Yani onaylanmayan bir REVIEW planı ZATEN icra edilmiyor. Ret bir DURUM DEĞİŞİKLİĞİ
olamaz — çünkü değiştirecek durum yok. Operatör kararı (2026-08-25): ret bir KAYIT olsun.

BU YÜZDEN RET, ONAYIN AYNADAKİ GÖRÜNTÜSÜ DEĞİLDİR:
  · onay  → İCRA YETKİSİ verir (silahlı kümeye yazar, ayna emri gönderir)
  · ret   → HİÇBİR icra etkisi YOK; yalnız operatörün hükmünü ve GEREKÇESİNİ deftere yazar
Bu asimetri bilinçlidir ve ekranda da yazılıdır; "reddettim" tıklayan operatör bir şeyi
DURDURDUĞUNU sanmamalı — zaten durmuştu.

NEDEN YİNE DE DEĞERLİ (YASA 6 — okuyucusu var): sessiz zaman aşımı ile bilinçli ret bugüne
kadar AYNI görünüyordu. Ayrımı yazmak öğrenme için kanıttır: "operatör bu kurulumu GÖRDÜ ve şu
sebeple istemedi" cümlesi, hiç bakılmamış bir plandan başka bir şeydir.

YASA `loop`TA, UÇTA DEĞİL: `trade_plans.jsonl`in yazar listesi `ledgers.CONTRACTS`ta yazılıdır
(loop/run/hermes). Uç niyeti bildirir, defterin yasası burada yaşar — `operator_onay_ver`in
birebir emsali.
"""
from __future__ import annotations

import json

import pytest

from meridian import loop, store


def _plan(pid: str, verdict: str, **ek) -> dict:
    return {"id": pid, "ticker": "TEST", "date": "2026-08-24", "gate_verdict": verdict, **ek}


def _defter(planlar: list[dict]) -> None:
    store.write_jsonl("trade_plans.jsonl", planlar)


def test_ret_plan_satirina_GEREKCESIYLE_yazilir(sandbox_state):
    _defter([_plan("P-1", "REVIEW")])
    r = loop.operator_ret_ver("P-1", gerekce="kurulum zayıf, hacim teyidi yok", kanal="pano")
    assert r["ok"], f"ret verilemedi: {r}"
    satir = [json.loads(l) for l in open(store.path("trade_plans.jsonl"))][0] \
        if hasattr(store, "path") else store.read_jsonl("trade_plans.jsonl")[0]
    ret = satir.get(loop.RET_ALANI)
    assert isinstance(ret, dict) and ret.get("ts"), f"ret damgası yok: {satir}"
    assert "hacim teyidi" in str(ret.get("gerekce")), f"gerekçe kaydedilmemiş: {ret}"


def test_HUKUM_alani_DEGISMEZ(sandbox_state):
    """`gate_verdict` geriye dönük değişmez (loop.py'nin ONAY_ALANI bloğundaki yasa).
    Ret bir OLAYdır; kapı istatistiklerini kirletemez."""
    _defter([_plan("P-1", "REVIEW")])
    loop.operator_ret_ver("P-1", gerekce="yeterince güçlü değil")
    satir = store.read_jsonl("trade_plans.jsonl")[0]
    assert satir["gate_verdict"] == "REVIEW", (
        f"ret kapı hükmünü DEĞİŞTİRMİŞ — istatistikler kirlenir: {satir['gate_verdict']}")


def test_ret_ICRAYA_dokunmaz(sandbox_state):
    """ASIL ÇİVİ: ret silahlı kümeye DOKUNMAZ ve hiçbir emir göndermez."""
    _defter([_plan("P-1", "REVIEW")])
    store.write_json("portfolio.json", {"armed": [], "positions": {}, "last_date": "2026-08-24"})
    loop.operator_ret_ver("P-1", gerekce="beğenmedim, sektör zayıf")
    meta = store.read_json("portfolio.json", {})
    assert meta.get("armed") == [], f"ret silahlı kümeyi DEĞİŞTİRMİŞ: {meta.get('armed')}"


def test_GEREKCESIZ_ret_KABUL_EDILMEZ(sandbox_state):
    """Gerekçesiz ret, sessiz zaman aşımından hiçbir farkı olmayan bir kayıttır — kartın
    tüm değeri gerekçede. Boş/çok kısa gerekçe reddedilir (YASA 4 eşiği ile aynı ruh)."""
    _defter([_plan("P-1", "REVIEW")])
    for kotu in ("", "   ", "yok"):
        r = loop.operator_ret_ver("P-1", gerekce=kotu)
        assert not r["ok"], f"gerekçesiz ret kabul edildi: {kotu!r} → {r}"
        assert r["kod"] == 400, f"yanlış kod: {r}"


def test_ONAYLI_plan_reddedilemez(sandbox_state):
    """Onay İCRA YETKİSİDİR ve ayna emri gitmiş olabilir. Onaylıyı 'reddetmek' operatöre
    durdurduğu yanılsaması verirdi — durduran kol KRİZ düğmesindeki cancel-open/flatten'dır."""
    _defter([_plan("P-1", "REVIEW", operator_onayi={"ts": "2026-08-24T10:00:00+00:00", "kanal": "pano"})])
    r = loop.operator_ret_ver("P-1", gerekce="fikrimi değiştirdim, kapatalım")
    assert not r["ok"] and r["kod"] == 409, f"onaylı plan reddedilebildi: {r}"
    assert "onay" in str(r["neden"]).lower()


def test_bilinmeyen_plan_404(sandbox_state):
    _defter([_plan("P-1", "REVIEW")])
    r = loop.operator_ret_ver("P-YOK", gerekce="bu plan yok ama gerekçe yeterince uzun")
    assert not r["ok"] and r["kod"] == 404


def test_IKINCI_ret_yeniden_yazmaz(sandbox_state):
    """Damga bir kez düşer; ikinci ret ilk gerekçeyi EZMEZ (onay emsali: `zaten_onayli`)."""
    _defter([_plan("P-1", "REVIEW")])
    loop.operator_ret_ver("P-1", gerekce="ilk gerekçe: hacim yetersiz")
    loop.operator_ret_ver("P-1", gerekce="ikinci gerekçe: tamamen başka bir sebep")
    ret = store.read_jsonl("trade_plans.jsonl")[0][loop.RET_ALANI]
    assert "ilk gerekçe" in str(ret.get("gerekce")), (
        f"ikinci ret ilk kaydı EZDİ — karar tarihçesi kayboldu: {ret}")


def test_NO_GO_reddedilebilir_ama_BEYANLI(sandbox_state):
    """NO_GO zaten icra edilmiyor; yine de operatör 'gördüm' diyebilmeli — ama kayıt bunun
    bir DURUM DEĞİŞİKLİĞİ olmadığını taşımalı, yoksa defter yanıltır."""
    _defter([_plan("P-1", "NO_GO")])
    r = loop.operator_ret_ver("P-1", gerekce="kapı zaten reddetmiş, ben de görüp kapatıyorum")
    assert r["ok"], f"NO_GO görülüp kapatılamadı: {r}"
    ret = store.read_jsonl("trade_plans.jsonl")[0][loop.RET_ALANI]
    assert ret.get("icra_etkisi") is False, "kaydın icra etkisi beyanı yok"


def test_olay_defterine_dusuyor(sandbox_state, monkeypatch):
    """YASA 6: kaydın okuyucusu var — olay defteri + pano. Sessiz yazım yok."""
    kayit = []
    monkeypatch.setattr(loop.obs, "log", lambda ad, **k: kayit.append((ad, k)) or {})
    _defter([_plan("P-1", "REVIEW")])
    loop.operator_ret_ver("P-1", gerekce="sektör rotasyonu ters, girmiyorum")
    adlar = [a for a, _ in kayit]
    assert "plan_operator_rejected" in adlar, f"ret olayı yazılmadı: {adlar}"
    _, k = next((x for x in kayit if x[0] == "plan_operator_rejected"))
    assert k.get("plan_id") == "P-1" and k.get("gerekce")
