"""test_seyrelme_ayna_v372.py — E2 SEYRELME AYNA-SATIRI + haftalık dönüşüm okuyucusu.

KART: `research/cards/EXE-2026-011-seyrelme-ayna-satiri.yaml` (ön-kayıt 2026-09-02, TSK-019).
Bu dosya KODDAN ÖNCE yazıldı (kart-önce + H3 kapısı: çivi önce, kırmızıyı gör, sonra kod).

ÖLÇÜLEN KUSUR (kartın tezi): E2 satırını yalnız GÖNDERİM KAPISINA ULAŞAN plan alır — kapıya hiç
ulaşmayan plan İZ BIRAKMAZ. Canlı defterde 36/36 submitted+dolu göründüğü için "kaç plan doluma
dönüşmedi ve NEREDE düştü" sorusu bugün cevapsız; seyrelmenin TAMAMI kapı-öncesi ve ölçüsüz.

NE ÇİVİLENİR:
  A1 POZİTİF KONTROL (ÇEKİRDEK) · yol-tutarlı: silahlanmayan plan GERÇEK EOD yolundan geçince
                                  ayna-satırı doğar (sınıf not_armed); silahlanıp gönderilmiş
                                  kardeş plan ayna-satırı ALMAZ (tekillik). Tek-fonksiyon birim
                                  çağrısı PK sayılmaz — kanca `loop.daily_cycle`tan tetiklenir.
  A2 TEKİLLİK       · submitted + fill=None planı da ayna-satırı ALMAZ (izi zaten var; kart §2)
  A3 ARMED_NOT_SUB  · silahlıydı, kapıya hiç girmedi, izsiz düştü → armed_not_submitted
  A4 TAŞINAN PLAN   · bu seansta bar'ı olmayan (carried) plan hüküm ALMAZ — kaderi kapanmadı
  B1 GERİ-DOLUM YOK · kohort YALNIZ bir önceki seanstır; daha eski izsiz plan satır ALMAZ (kill#2)
  B2 SÖZLÜK DONUK   · üç sınıf, üçü de kaynakta; dördüncü sınıf İCAT EDİLMEZ
  B3 PIT/OLCULEMEDI · alanlardan sınıf çözülemeyen plan `olculemedi`ye düşer (uydurma yasağı)
  B4 AYRIŞMA ÇİVİSİ · `broker_status` damga vokabüleri ve kapı hükmü vokabüleri KAYNAKTAN türer
  C1 İDEMPOTENS     · aynı seans iki kez koşarsa ikinci koşum satır EKLEMEZ
  D1 OKUYUCU        · haftalık öz-inceleme dönüşüm satırı defterden doğru sayıları okur
  D2 DÜRÜST BOŞLUK  · defter boşken None (0 DEĞİL) — "ölçmedim" ile "sıfır" ayrı şeylerdir
  D3 TEK KAYNAK     · okuyucu sınıf sözlüğünü loop'tan TÜRETİR, kendi kopyasını tutmaz

YÖNTEM: hiçbir test ağa çıkmaz; `alpaca.py`'nin `httpx` istemcisi kayıt ediciyle değiştirilir (v233 deseni), adaptör
gövdeleri gerçek koşar. Kararların hepsi FİKSTÜRle ölçülür — canlı/yerel `state/` okunmaz.
"""
from __future__ import annotations

import ast
import datetime as dt
import pathlib
import shutil

import pytest
import yaml

from meridian import barclock as bc
from meridian import broker as BR
from meridian import config, loop, selfreview, store
from meridian.adapters import alpaca
from tests.conftest import make_bars

REPO = pathlib.Path(config.__file__).resolve().parent.parent
UTC = dt.timezone.utc
RTH = dt.datetime(2026, 7, 23, 14, 46, 30, tzinfo=UTC)   # 10:46:30 ET — tetik penceresi AÇIK
FAKE_KEY = "PKSEYRELMEV372FAKEKEY00112233"
FAKE_SECRET = "SKSEYRELMEV372FAKESECRET556677"


# =================================================================================================
# FİKSTÜRLER (v233 `ayna` fikstürünün birebir deseni — ikinci bir sahne gövdesi yazılmaz)
# =================================================================================================
class _Resp:
    def __init__(self, data, status=200):
        self._d, self.status_code = data, status

    def json(self):
        return self._d

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class SahteHttpx:
    """Alpaca REST'in kayıt edici taklidi — adaptör gövdeleri GERÇEK koşar, ağ hiç açılmaz."""

    def __init__(self):
        self.posts: list = []
        self.deletes: list = []
        self.acik_emirler: list = []
        self.pozisyonlar: list = []

    def get(self, url, **k):
        if url.endswith("/v2/account"):
            return _Resp({"equity": "100000", "status": "ACTIVE"})
        if "/v2/positions" in url:
            return _Resp([dict(p) for p in self.pozisyonlar])
        if "/v2/orders" in url:
            return _Resp([dict(o) for o in self.acik_emirler])
        if "/v2/assets/" in url:
            return _Resp({"tradable": True, "status": "active"})
        return _Resp({}, 404)

    def post(self, url, headers=None, json=None, timeout=None):
        self.posts.append(dict(json or {}))
        return _Resp({"id": f"srv-{len(self.posts)}", "status": "accepted",
                      "client_order_id": (json or {}).get("client_order_id")})

    def delete(self, url, headers=None, params=None, timeout=None):
        self.deletes.append(url.rsplit("/", 1)[-1])
        return _Resp({}, 200)


@pytest.fixture
def ayna(sandbox_state, monkeypatch):
    """Sahte kimlik + `alpaca_paper` arka ucu + httpx kayıt edicisi; saat tetik penceresi İÇİNDE."""
    from meridian import secrets as secrets_mod
    monkeypatch.setenv("ALPACA_PAPER_KEY", FAKE_KEY)
    monkeypatch.setenv("ALPACA_PAPER_SECRET", FAKE_SECRET)
    monkeypatch.delenv("MERIDIAN_GCP_PROJECT", raising=False)
    secrets_mod.clear_cache()
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    fake = SahteHttpx()
    monkeypatch.setattr(alpaca, "httpx", fake)
    bc.set_clock(lambda: RTH)
    yield sandbox_state, fake
    bc.reset_clock()
    secrets_mod.clear_cache()


def _seed_conf(sb):
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(REPO / "state" / f, sb / f)
    config.reload_config()
    (sb / "strategy.yaml").write_text(yaml.safe_dump(config.default_strategy()))


def _plan(pid, *, date, ticker=None, verdict="REVIEW", trigger=100.0, stop=95.0,
          target=112.0, **ek):
    """Canlı plan satırı şekli (`loop.daily_cycle` P3 üretimiyle aynı alanlar)."""
    return {"id": pid, "date": date, "ticker": ticker or pid.split("-")[-1], "side": "long",
            "entry_trigger": trigger, "stop": stop, "targets": [target], "profit_target": target,
            "size_r": 1.0, "r_multiple_expected": 2.4, "regime_at_plan": "chop", "sector": "Tech",
            "score": 71, "setup": "breakout_vcp", "dormant_setup": False,
            "strategy_version": 1, "gate_verdict": verdict,
            "gate_reasons": ["skor alt bantta"], **ek}


def _law(pid, trigger=100.0, ref=99.5, atr=1.0):
    return {pid: {**BR.entry_order_decision(trigger, ref_price=ref, atr=atr), "pivot": None}}


def _kitap(**ek):
    doc = {"armed": [], "positions": {}, "last_date": "2026-08-05", "cash": 100_000.0,
           "peak_equity": 100_000.0, "day_start_equity": 100_000.0, "realized_pnl": 0.0, **ek}
    store.write_json("portfolio.json", doc)
    return doc


def _e2(motor=None):
    rows = store.read_jsonl(loop.ENTRY_LEDGER)
    return [r for r in rows if motor is None or r.get("motor") == motor]


def _seyrelme(plan_id=None):
    return [r for r in _e2(loop.AYNA_SEYRELME_MOTOR)
            if plan_id is None or r.get("plan_id") == plan_id]


def _sahne(idx_seed=1):
    """(idx, bars, d_str, onceki) — iki sembollü evren; kohort tarihi bir önceki seanstır."""
    idx = make_bars(300, seed=idx_seed, trend=0.0009)
    bars = {"AAA": make_bars(300, seed=2), "BBB": make_bars(300, seed=3)}
    d_str = str(idx["date"].iloc[-1].date())
    onceki = str(idx["date"].iloc[-2].date())
    return idx, bars, d_str, onceki


# =================================================================================================
# A — POZİTİF KONTROL + TEKİLLİK (kartın çekirdeği)
# =================================================================================================
def test_a1_pk_silahlanmayan_plan_ayna_satiri_alir_gonderilen_kardes_ALMAZ(ayna):
    """KARTIN POZİTİF KONTROLÜ (YOL-TUTARLI, ÇEKİRDEK ÇİVİ).

    Fikstürde iki KARDEŞ plan aynı kohortta (bir önceki seans):
      AAA — kapıdan REVIEW aldı, onaylanmadı, silahlı kümeye HİÇ girmedi  → ayna-satırı VAR
      BBB — silahlandı ve aynaya gönderildi (E2'de `submitted` satırı var) → ayna-satırı YOK

    Kanca gerçek EOD yolundan (`loop.daily_cycle`) tetiklenir; tek-fonksiyon birim çağrısı PK
    sayılmaz. PK ateşlemezse kartın hiçbir sonucu yorumlanmaz."""
    sb, _fake = ayna
    _seed_conf(sb)
    idx, bars, d_str, onceki = _sahne()
    acilis = float(bars["BBB"]["open"].iloc[-1])

    aaa = _plan(f"P-{onceki}-AAA", date=onceki)                       # silahsız, onaysız REVIEW
    bbb = _plan(f"P-{onceki}-BBB", date=onceki, verdict="GO",
                trigger=round(acilis * 0.995, 2), stop=round(acilis * 0.90, 2),
                target=round(acilis * 1.2, 2))
    store.write_jsonl("trade_plans.jsonl", [aaa, bbb])
    _kitap(last_date=onceki, armed=[dict(bbb)], alpaca_submitted=[bbb["id"]],
           entry_law=_law(bbb["id"], trigger=bbb["entry_trigger"],
                          ref=bbb["entry_trigger"] * 0.995, atr=1.0))
    # BBB'nin GÖNDERİM İZİ diskte: kohort seansında kapıdan geçti (bu seansın işi değil).
    store.write_jsonl(loop.ENTRY_LEDGER, [
        {"ts": f"{onceki}T20:33:00+00:00", "date": onceki, "plan_id": bbb["id"], "ticker": "BBB",
         "motor": "ayna", "karar": "submitted", "fill": None, "kaynak": "loop"}])

    out = loop.daily_cycle(bars, idx, on_date=d_str)
    assert out.get("status") == "ok", out

    satirlar = _seyrelme()
    assert len(satirlar) == 1, (
        f"ayna-satırı tam olarak BİR plan için doğmalıydı, gördüğüm: "
        f"{[(r.get('plan_id'), r.get('red_sinifi')) for r in satirlar]}")
    r = satirlar[0]
    assert r["plan_id"] == aaa["id"], "silahlanmayan plan yerine başka plan işaretlendi"
    assert r["red_sinifi"] == loop.AYNA_SINIF_NOT_ARMED, r
    assert r["ticker"] == "AAA" and r["fill"] is None
    assert r["plan_date"] == onceki, "satır hangi seansın planını anlattığını söylemiyor"
    # TEKİLLİK (kart §2 + kill#1): gönderilmiş kardeşin İKİNCİ bir sonuç izi YOK.
    assert _seyrelme(bbb["id"]) == [], (
        "kapıya ULAŞMIŞ plana ayna-satırı yazıldı — aynı planın iki sonuç izi kill kriteridir")


def test_a2_submitted_ama_dolmamis_plan_ayna_satiri_ALMAZ(ayna):
    """KART §2 İKİNCİ YARISI: `submitted` + `fill=None` planın izi ZATEN var (dinlenen-limit
    ailesi EXE-2026-005'in konusu). İkinci bir iz yazmak kill#1'i tetiklerdi.

    A1'den FARKI: orada kardeş plan silahlı kümedeydi ve bu seans dolabilirdi; burada plan silahlı
    kümede DEĞİL (gönderildi, sonra düştü) — yani "izsiz kalmış gibi" görünen tam sınıf."""
    sb, _fake = ayna
    _seed_conf(sb)
    idx, bars, d_str, onceki = _sahne()
    ccc = _plan(f"P-{onceki}-CCC", date=onceki, verdict="GO")
    store.write_jsonl("trade_plans.jsonl", [ccc])
    _kitap(last_date=onceki, alpaca_submitted=[ccc["id"]])
    store.write_jsonl(loop.ENTRY_LEDGER, [
        {"ts": f"{onceki}T20:33:00+00:00", "date": onceki, "plan_id": ccc["id"], "ticker": "CCC",
         "motor": "ayna", "karar": "submitted", "fill": None, "kaynak": "loop"}])

    assert loop.daily_cycle(bars, idx, on_date=d_str).get("status") == "ok"
    assert _seyrelme() == [], "submitted+dolmamış plana ayna-satırı yazıldı (kart §2 ihlali)"


def test_a3_silahli_kaldi_kapiya_girmedi_ARMED_NOT_SUBMITTED(ayna, monkeypatch):
    """Silahlı kümedeydi, gönderim kapısına HİÇ girmedi ve izsiz düştü → `armed_not_submitted`.

    YOL: terfili ajanın dar vetosu (`loop._llm_veto_filter`) REVIEW+karşı planı silahlı kümeden
    düşürür; plan aynaya gönderilmediği için E2'de HİÇBİR satırı yoktur. Düzeltme öncesinde bu
    plan defterden sessizce kayboluyordu — sınıfın gerçek üreticisi budur."""
    sb, _fake = ayna
    _seed_conf(sb)
    from meridian import analytics as _an
    monkeypatch.setattr(_an, "llm_promoted", lambda: True)
    idx, bars, d_str, onceki = _sahne()
    ddd = _plan(f"P-{onceki}-AAA", date=onceki, verdict="REVIEW", llm_opinion="karşı")
    store.write_jsonl("trade_plans.jsonl", [ddd])
    _kitap(last_date=onceki, armed=[dict(ddd)], entry_law=_law(ddd["id"]))

    assert loop.daily_cycle(bars, idx, on_date=d_str).get("status") == "ok"
    pf = store.read_json("portfolio.json", {})
    assert ddd["id"] not in [a.get("id") for a in (pf.get("armed") or [])], \
        "fikstür kırık: plan silahlı kümeden düşmedi, ölçülen sınıf bu değil"
    satirlar = _seyrelme(ddd["id"])
    assert len(satirlar) == 1 and satirlar[0]["red_sinifi"] == loop.AYNA_SINIF_ARMED_NOT_SUBMITTED, \
        f"silahlı-ama-gönderilmemiş plan yanlış sınıflandı: {satirlar}"


def test_a4_bu_seans_bari_olmayan_TASINAN_plan_hukum_ALMAZ(ayna):
    """PIT: kaderi HENÜZ KAPANMAMIŞ plana bugünden hüküm verilmez.

    Bar'ı yayınlanmamış plan `_carry_armed_without_bar` ile SİLAHLI kalır (taşınır) ve bir sonraki
    seansta dolabilir. Ona bugün "dönüşmedi" demek, kartın kill#2 sınıfının (geriye dönük /
    erken hüküm) ta kendisi olurdu."""
    sb, _fake = ayna
    _seed_conf(sb)
    idx, bars, d_str, onceki = _sahne()
    # ZZZ'nin evrende barı YOK → plan taşınır (carried), silahlı kalır.
    zzz = _plan(f"P-{onceki}-ZZZ", date=onceki, verdict="GO")
    store.write_jsonl("trade_plans.jsonl", [zzz])
    _kitap(last_date=onceki, armed=[dict(zzz)], entry_law=_law(zzz["id"]))

    assert loop.daily_cycle(bars, idx, on_date=d_str).get("status") == "ok"
    pf = store.read_json("portfolio.json", {})
    assert zzz["id"] in [a.get("id") for a in (pf.get("armed") or [])], \
        "fikstür kırık: plan taşınmadı, ölçülen şey 'kaderi açık plan' değil"
    assert _seyrelme(zzz["id"]) == [], \
        "taşınan (hâlâ silahlı) plana hüküm yazıldı — kaderi kapanmadan 'dönüşmedi' denemez"


# =================================================================================================
# B — PIT / SÖZLÜK / AYRIŞMA
# =================================================================================================
def test_b1_gecmis_seansa_GERI_DOLUM_yok(ayna):
    """KİLL#2: kohort YALNIZ kitabın son işlediği seanstır. Daha eski izsiz bir plana ayna-satırı
    basmak, o günün "dönüşmedi" hükmünü BUGÜNDEN vermek olurdu — PIT ihlali."""
    sb, _fake = ayna
    _seed_conf(sb)
    idx, bars, d_str, onceki = _sahne()
    cok_eski = str(idx["date"].iloc[-6].date())
    eski = _plan(f"P-{cok_eski}-AAA", date=cok_eski)
    yeni = _plan(f"P-{onceki}-BBB", date=onceki)
    store.write_jsonl("trade_plans.jsonl", [eski, yeni])
    _kitap(last_date=onceki)

    assert loop.daily_cycle(bars, idx, on_date=d_str).get("status") == "ok"
    assert _seyrelme(eski["id"]) == [], "geçmiş seansa geri-dolum ayna-satırı basıldı (kill#2)"
    assert len(_seyrelme(yeni["id"])) == 1, "kohort planı işaretlenmedi — süzgeç fazla kesiyor"


def test_b2_sebep_sozlugu_DONUK_ucten_fazla_sinif_yok():
    """Sözlük DONUK (kart §3 + `beyanlı_sınırlar` 3): üç sınıf, ne bir eksik ne bir fazla.
    Dördüncü bir ayırt edilebilir sınıf bulunursa sözlüğe EKLENMEZ — `olculemedi`ye sayılır."""
    assert loop.AYNA_SEYRELME_SINIFLARI == (
        loop.AYNA_SINIF_NOT_ARMED, loop.AYNA_SINIF_ARMED_NOT_SUBMITTED,
        loop.AYNA_SINIF_OLCULEMEDI)
    assert sorted(loop.AYNA_SEYRELME_SINIFLARI) == [
        "armed_not_submitted", "not_armed", "olculemedi"]
    # KAYNAK TARAMASI: sınıflandırıcının HER `return`ü sözlükten çıkmalı. Ham sabit de (Constant)
    # modül sabiti de (Name) çözülür; çözülemeyen bir dönüş ifadesi KÖRLÜKTÜR ve çivi düşer —
    # "yalnız sabitlere bak" deseydik, adlarla dönen bu gövdede tarama boş küme bulup SESSİZCE
    # yeşil kalırdı (totolojik çivi).
    kaynak = pathlib.Path(loop.__file__).read_text(encoding="utf-8")
    fn = next(n for n in ast.walk(ast.parse(kaynak))
              if isinstance(n, ast.FunctionDef) and n.name == "_ayna_seyrelme_sinifi")
    donusler = [n.value for n in ast.walk(fn) if isinstance(n, ast.Return) and n.value is not None]
    assert donusler, "sınıflandırıcıda hiç `return` bulunamadı — tarama kör kalırdı"
    donen = set()
    for d in donusler:
        if isinstance(d, ast.Constant) and isinstance(d.value, str):
            donen.add(d.value)
        elif isinstance(d, ast.Name) and isinstance(getattr(loop, d.id, None), str):
            donen.add(getattr(loop, d.id))
        else:
            pytest.fail(f"sınıflandırıcı çözülemeyen bir ifade döndürüyor (satır {d.lineno}) — "
                        f"sözlük denetimi kör kalır")
    assert donen == set(loop.AYNA_SEYRELME_SINIFLARI), (
        f"sınıflandırıcının dönüş kümesi donuk sözlükle AYRIŞTI: kaynak={sorted(donen)} "
        f"sözlük={sorted(loop.AYNA_SEYRELME_SINIFLARI)}")


def test_b3_alanlardan_cozulemeyen_plan_OLCULEMEDIye_duser(ayna):
    """UYDURMA YASAĞI: kapı hükmü taşımayan (şeması eksik/sonradan doğmuş) bir plan satırından
    sınıf ÇÖZÜLEMEZ. Doğru cevap `olculemedi`dir — dördüncü bir sınıf icat etmek değil."""
    sb, _fake = ayna
    _seed_conf(sb)
    idx, bars, d_str, onceki = _sahne()
    kor = _plan(f"P-{onceki}-AAA", date=onceki)
    kor.pop("gate_verdict")                      # kapı hükmü YOK → silahlanma yolu okunamaz
    store.write_jsonl("trade_plans.jsonl", [kor])
    _kitap(last_date=onceki)

    assert loop.daily_cycle(bars, idx, on_date=d_str).get("status") == "ok"
    satirlar = _seyrelme(kor["id"])
    assert len(satirlar) == 1 and satirlar[0]["red_sinifi"] == loop.AYNA_SINIF_OLCULEMEDI, satirlar
    assert satirlar[0].get("red_nedeni"), "ölçülemedi sınıfı NEDENİNİ söylemiyor (dürüst boşluk)"


def test_b3b_broker_damgalari_sinif_UYDURMAZ():
    """K-1 (öz-çelişki onarımı, düzeltme turu 1): `broker_status` damgalarının HEPSİ silahlılık
    kanıtı DEĞİLDİR — damgayı KİMİN yazdığı sınıfı belirler.

      `gap_veto` · `failed_broker_rejection` → yazan yer `mirror_submit_armed`ın İÇİDİR, yani
          damgayı taşıyan plan gönderim kapısına ULAŞMIŞTIR ve karar satırını da orada alır.
          İzsiz kalmışsa geriye tek olasılık kalır: karar satırı YAZILAMADI (defter yazım
          arızası). Bu, donuk sözlükteki iki sınıfın HİÇBİRİ değildir → `olculemedi`. Aynı
          hüküm `gonderilmis` dalıyla birebir tutarlıdır; eski hâl kendi gerekçesiyle çelişiyordu.
      `armed_dropped_<kapı>`   → yazan yer `_armed_drop_row`dır ve o plan kapıya HİÇ ulaşmadan
          düşürülmüştür → gerçek silahlılık kanıtı."""
    pl = {"id": "P-X", "gate_verdict": "GO"}
    for bs in loop.ARMED_DAMGALARI:
        assert loop._ayna_seyrelme_sinifi({**pl, "broker_status": bs},
                                          silahliydi=False, gonderilmis=False) == \
            loop.AYNA_SINIF_OLCULEMEDI, \
            f"kapıya ULAŞMIŞ damga ({bs}) silahlılık kanıtı sayıldı — sınıf uydurma"
        assert "karar satırı" in loop._ayna_seyrelme_nedeni(
            {**pl, "broker_status": bs}, loop.AYNA_SINIF_OLCULEMEDI), \
            "alt-neden 'kapı damgası var ama karar satırı yok' hâlini adlandırmıyor"
    # TANINMAYAN damga da hüküm üretmez (panonun 'bilinmeyen değer ham basılır' disiplini).
    assert loop._ayna_seyrelme_sinifi({**pl, "broker_status": "yepyeni_bir_damga"},
                                      silahliydi=False, gonderilmis=False) == \
        loop.AYNA_SINIF_OLCULEMEDI
    # POZİTİF KONTROL (iki kanıt yolu da ÖLÜ DEĞİL): kapı-dışı düşme damgası ve silahlı üyelik.
    assert loop._ayna_seyrelme_sinifi({**pl, "broker_status": f"{loop.ARMED_DAMGA_ONEKI}halt"},
                                      silahliydi=False, gonderilmis=False) == \
        loop.AYNA_SINIF_ARMED_NOT_SUBMITTED
    assert loop._ayna_seyrelme_sinifi(pl, silahliydi=True, gonderilmis=False) == \
        loop.AYNA_SINIF_ARMED_NOT_SUBMITTED


def test_b3c_kapi_damgasi_SILAHLILIGA_baskin_cikar():
    """ÖNCELİK SIRASI, KOMBİNE VAKAYLA (düzeltme turu 2, Bulgu 3). İki kanıt AYNI ANDA doğru
    olabilir: plan kohort seansında silahlandı (`silahliydi=True`) VE sonra gönderim kapısına
    girip `gap_veto` yedi. İkisi de olduysa sınıfı GEÇ olan olgu belirler.

    NEDEN: `armed_not_submitted`ın metni "silahlı kaldı ama kapıya HİÇ girmedi"dir — kapı damgası
    taşıyan plan için bu cümle DÜPEDÜZ YANLIŞTIR. Doğru cevap `olculemedi`dir: plan kapıya ulaştı,
    karar satırı yazılamadı. Tek başına sınanan iki dal bu sırayı hiç ölçmüyordu; sıra ters
    çevrilse iki tekil çivi de yeşil kalırdı."""
    pl = {"id": "P-KOMBI", "gate_verdict": "GO", "broker_status": "gap_veto"}
    assert loop._ayna_seyrelme_sinifi(pl, silahliydi=True, gonderilmis=False) == \
        loop.AYNA_SINIF_OLCULEMEDI, (
            "silahlılık kanıtı kapı damgasını EZDİ — 'kapıya hiç girmedi' diyen bir sınıf, kapı "
            "damgası taşıyan plana yazıldı")
    # POZİTİF KONTROL (sıra tek yönlü ezmiyor): damga OLMADAN aynı plan silahlılıktan sınıflanır.
    assert loop._ayna_seyrelme_sinifi({k: v for k, v in pl.items() if k != "broker_status"},
                                      silahliydi=True, gonderilmis=False) == \
        loop.AYNA_SINIF_ARMED_NOT_SUBMITTED
    # ve `gonderilmis` her ikisini de ezer (en geç olgu).
    assert loop._ayna_seyrelme_sinifi(pl, silahliydi=True, gonderilmis=True) == \
        loop.AYNA_SINIF_OLCULEMEDI


def test_b4_kapi_disi_damga_ONEKI_TURETILIR_kopya_degil(sandbox_state):
    """ÖNEK ARTIK KOPYA DEĞİL, TÜRETİLMİŞ (düzeltme turu 2, Rol-1 ruling'i).

    ÖNCEKİ HÂL VE NEDEN YETMEZDİ: `_armed_drop_row` öneki `f"armed_dropped_{gate}"` diye KENDİ
    literaliyle yazıyor, `_damga_sinifi` ise `ARMED_DAMGA_ONEKI` sabitiyle okuyordu — iki kopya.
    Koruma bir AST "ayrışma çivisi"ydi ama ISIRMIYORDU: tarama `pl["broker_status"] = status`
    atamasının SAĞ TARAFINI (bir `Name`) görüyor, f-string'in METNİNE hiç bakmıyordu. Yani önek
    üretici tarafta sessizce driftlese çivi YEŞİL kalırdı — kopyayı koruduğunu sanan bir çivi.
    Sabit ve fonksiyon AYNI modülde olduğu için kopya KAÇINILMAZ DEĞİLDİ: üretici artık sabitten
    türetiyor ve bu test kılıf değil DAVRANIŞ ölçüyor.

    (b) kapı hükmü vokabüleri hâlâ türetilemez (başka modül, AST denetimi) — o yarım ayrışma
    çivisi olarak KALIR ve `pitlaw.karar_vokabuleri` ile kıyaslanır."""
    from meridian import pitlaw
    # ---- (a1) DAVRANIŞ: üreticinin BASTIĞI damga, okuyucunun sabitiyle uyumlu mu? ----
    pl = {"id": "P-B4", "ticker": "AAA", "entry_trigger": 10.0}
    loop._armed_drop_row(pl, "2026-09-02", "halt", open_positions=3, eff_max_open=3)
    assert pl["broker_status"].startswith(loop.ARMED_DAMGA_ONEKI), (
        f"üreticinin bastığı damga ({pl['broker_status']!r}) okuyucunun önekiyle "
        f"({loop.ARMED_DAMGA_ONEKI!r}) uyumsuz — iki taraf ayrıştı")
    # TAM ZİNCİR: yazan → sınıflayan → sonuç. Önek driftlerse bu üç satır birlikte düşer.
    assert loop._damga_sinifi(pl["broker_status"]) == "kapi_disi"
    assert loop._ayna_seyrelme_sinifi(pl, silahliydi=False, gonderilmis=False) == \
        loop.AYNA_SINIF_ARMED_NOT_SUBMITTED

    # ---- (a2) TÜRETME GERÇEKTEN KODDA MI: gövde sabiti REFERANSLIYOR, literali TEKRARLAMIYOR ----
    # Davranış çivisi tek başına yetmez: üretici literali geri yazsa da (a1) yeşil kalırdı
    # (bugün iki metin aynı). Kopyanın GERİ GELMESİNİ ancak bu yarım yakalar.
    kaynak = pathlib.Path(loop.__file__).read_text(encoding="utf-8")
    fn = next(n for n in ast.walk(ast.parse(kaynak))
              if isinstance(n, ast.FunctionDef) and n.name == "_armed_drop_row")
    adlar = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}
    sabitler = {n.value for n in ast.walk(fn)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    assert "ARMED_DAMGA_ONEKI" in adlar, (
        "`_armed_drop_row` öneki sabitten TÜRETMİYOR — kopya geri geldi; sabit ve fonksiyon aynı "
        "modülde, türetme kaçınılabilir bir kopya değil")
    assert loop.ARMED_DAMGA_ONEKI not in sabitler, (
        f"`_armed_drop_row` gövdesinde önek literali {loop.ARMED_DAMGA_ONEKI!r} hâlâ yazılı — "
        f"türetme yarım (hem sabit hem literal), ikisi ayrı ayrı driftleyebilir")

    # ---- (a3) TÜRETİLEMEYEN YARIM: iki SABİT damga `mirror_submit_armed`ın içinde yazılı ----
    # Bunlar bu turun DOKUNMA sınırındaki fonksiyonda (`mirror_submit_armed`) doğuyor; kopya
    # burada gerçekten kaçınılmaz, o yüzden ayrışma çivisi KALIR (değer düzeyinde AST taraması).
    agac = ast.parse(kaynak)
    yazilan: set[str] = set()
    for n in ast.walk(agac):
        if not isinstance(n, ast.Assign):
            continue
        for t in n.targets:
            if isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant) \
                    and t.slice.value == "broker_status" \
                    and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
                yazilan.add(n.value.value)
    assert yazilan == set(loop.ARMED_DAMGALARI), (
        f"`broker_status` sabit damga kümesi AYRIŞTI: kaynak={sorted(yazilan)} "
        f"kayıt={sorted(loop.ARMED_DAMGALARI)} — sınıflandırıcı yeni damgayı tanımaz")

    # ---- (b) kapı hükmü vokabüleri ----
    vok = pitlaw.karar_vokabuleri()
    assert vok is not None, "kapı sözleşmesi okunamadı — ayrışma ölçülemez, çivi hüküm vermez"
    assert set(loop.KAPI_HUKUMLERI) == set(vok), (
        f"kapı hükmü vokabüleri AYRIŞTI: loop={sorted(loop.KAPI_HUKUMLERI)} "
        f"kaynak(guard.classify_gate)={sorted(vok)}")


# =================================================================================================
# C — İDEMPOTENS
# =================================================================================================
def test_c1_ayni_seans_iki_kez_kosarsa_satir_EKLENMEZ(ayna):
    """EOD dikişi aynı seans için iki kez koşarsa ikinci koşum satır EKLEMEZ.
    İKİ KATMAN ölçülür: (1) döngünün kendi tekrar kapısı, (2) dikişin plan_id JOIN'i —
    ikincisi tek başına da yeterlidir ve kapı bir gün kalkarsa tek koruma odur."""
    sb, _fake = ayna
    _seed_conf(sb)
    idx, bars, d_str, onceki = _sahne()
    aaa = _plan(f"P-{onceki}-AAA", date=onceki)
    store.write_jsonl("trade_plans.jsonl", [aaa])
    _kitap(last_date=onceki)

    assert loop.daily_cycle(bars, idx, on_date=d_str).get("status") == "ok"
    assert len(_seyrelme()) == 1
    loop.daily_cycle(bars, idx, on_date=d_str)                     # (1) döngü tekrarı
    assert len(_seyrelme()) == 1, "aynı seans ikinci kez koşunca satır EKLENDİ"

    meta = store.read_json("portfolio.json", {})
    loop._ayna_seyrelme_yaz(meta, d_str, onceki, set())            # (2) dikişin kendi JOIN'i
    assert len(_seyrelme()) == 1, \
        "dikiş plan_id JOIN'i tekilliği korumuyor — ikinci çağrı çift satır yazdı"


# =================================================================================================
# D — OKUYUCU (YASA 6): haftalık dönüşüm satırı
# =================================================================================================
def _defter(dstr: str, satirlar: list) -> None:
    store.write_jsonl(loop.ENTRY_LEDGER, [{"ts": f"{dstr}T20:00:00+00:00", "date": dstr, **r}
                                          for r in satirlar])


def test_d1_haftalik_donusum_satiri_defterden_okur(sandbox_state):
    """KART §5: haftalık rapor plan sayısı · dolum sayısı · dönüşmeme sınıf dağılımını taşır.
    EDG-042 hakem takvim sorusunun PAYDASI (plan sayısı) buradan okunur."""
    _seed_conf(sandbox_state)
    bugun = dt.date.today().isoformat()
    _defter(bugun, [
        {"plan_id": "P-1", "ticker": "AAA", "motor": "ayna", "karar": "submitted", "fill": None},
        {"plan_id": "P-1", "ticker": "AAA", "motor": "ic", "karar": "fill", "fill": 101.0},
        {"plan_id": "P-2", "ticker": "BBB", "motor": "ic", "karar": "entry_missed_limit",
         "fill": None},
        {"plan_id": "P-3", "ticker": "CCC", "motor": loop.AYNA_SEYRELME_MOTOR,
         "karar": loop.AYNA_SEYRELME_KARAR, "red_sinifi": loop.AYNA_SINIF_NOT_ARMED},
        {"plan_id": "P-4", "ticker": "DDD", "motor": loop.AYNA_SEYRELME_MOTOR,
         "karar": loop.AYNA_SEYRELME_KARAR, "red_sinifi": loop.AYNA_SINIF_NOT_ARMED},
        {"plan_id": "P-5", "ticker": "EEE", "motor": loop.AYNA_SEYRELME_MOTOR,
         "karar": loop.AYNA_SEYRELME_KARAR, "red_sinifi": loop.AYNA_SINIF_OLCULEMEDI},
    ])
    d = selfreview.build()["week"]["donusum"]
    assert d["plan_n"] == 5, f"payda yanlış (tekil plan kimliği sayılmalı): {d}"
    assert d["dolum_n"] == 1, f"dolum sayısı iç motorun `fill` satırından gelmeli: {d}"
    assert d["dolum_orani"] == 0.2
    assert d["donusmeyen_n"] == 3
    # DONUK SÖZLÜĞÜN TAMAMI yazılır: görülmeyen sınıf 0'dır, "yok" değil.
    assert d["sinif_dagilimi"] == {"not_armed": 2, "armed_not_submitted": 0, "olculemedi": 1}
    assert d["sinif_disi_n"] == 0
    # Defterin tamamı BUGÜNden: haftanın önceki günleri defterde HİÇ yok → pencere kesildi.
    assert d["pencere_kesildi"] is True, "kesik pencere ölçülmüyor — eksik sayı 'yok' okunur"
    assert d["beyan"], "paydanın dürüst sınırı beyansız kaldı"


def test_d2_bos_defterde_None_sifir_DEGIL(sandbox_state):
    """DÜRÜST BOŞLUK: defter boşken 0 basmak "hiçbir plan dönüşmedi" demektir; doğru cevap
    "ölçmedim"dir. Sıfır ile bilmiyorum aynı şey değildir (uydurma yasağı)."""
    _seed_conf(sandbox_state)
    d = selfreview.build()["week"]["donusum"]
    assert d["plan_n"] is None and d["dolum_n"] is None and d["dolum_orani"] is None
    assert d["sinif_dagilimi"] is None and d["pencere_kesildi"] is None
    assert "defter" in (d.get("durum") or "").lower(), "boşluk gerekçesiz bırakıldı"
    # POZİTİF KONTROL: defter DOLU ve haftadan ESKİYE uzanıyor, pencerede satır yok → 0 DÜRÜSTTÜR
    # (baktık, bulamadık). Aynı alanların None ile 0 arasındaki farkı burada ateşlenir.
    _defter("2020-01-02", [{"plan_id": "P-9", "motor": "ic", "karar": "fill", "fill": 10.0}])
    d2 = selfreview.build()["week"]["donusum"]
    assert d2["plan_n"] == 0 and d2["dolum_n"] == 0 and d2["dolum_orani"] is None
    assert d2["pencere_kesildi"] is False, \
        "defter haftadan geriye uzanıyor — pencere KESİK değil; 0 gerçekten 0'dır"


def test_d4_dolum_sayisi_GERCEK_loop_yolundan_yazilan_satiri_sayar(ayna, monkeypatch):
    """K-2 (düzeltme turu 1): okuyucunun PAY süzgeci (`motor="ic"` ∧ `karar="fill"`) `loop`un
    yazdığı literallerin KOPYASIDIR — sabit ihraç etmek üç yazım yerini de değiştirmeyi
    gerektirirdi. Kopya kaçınılmaz olduğuna göre çivi DAVRANIŞSAL olmalı: dolum satırını
    GERÇEK EOD yolu yazar, okuyucu onu saymak ZORUNDADIR. `loop`un literali değişirse bu
    çivi öter — kaynak taraması ötmezdi.

    PENCERE YAMASI BEYANLI: fikstür barları takvimsel olarak eskidir (`make_bars` 2022'den
    başlar), haftalık pencere onları kapsamaz. Yamalanan şey PENCEREdir, ölçülen şey değil."""
    sb, _fake = ayna
    _seed_conf(sb)
    monkeypatch.setattr(selfreview, "_week_ago_iso", lambda: "2000-01-01T00:00:00+00:00")
    idx, bars, d_str, onceki = _sahne()
    acilis = float(bars["AAA"]["open"].iloc[-1])
    plan = _plan(f"P-{onceki}-AAA", date=onceki, verdict="GO",
                 trigger=round(acilis * 0.995, 2), stop=round(acilis * 0.90, 2),
                 target=round(acilis * 1.2, 2))
    store.write_jsonl("trade_plans.jsonl", [plan])
    _kitap(last_date=onceki, armed=[dict(plan)],
           entry_law=_law(plan["id"], trigger=plan["entry_trigger"],
                          ref=plan["entry_trigger"] * 0.995, atr=1.0))

    assert loop.daily_cycle(bars, idx, on_date=d_str).get("status") == "ok"
    # FİKSTÜR SAĞLAMASI: satırı GERÇEKTEN loop yazdı (elle yazılmış bir satırı saymıyoruz).
    ic_satir = [r for r in _e2("ic") if r.get("plan_id") == plan["id"]
                and r.get("karar") == "fill"]
    assert len(ic_satir) == 1, f"fikstür kırık: iç motor dolum satırı yazmadı ({_e2()})"

    d = selfreview.build()["week"]["donusum"]
    assert d["dolum_n"] == 1, (
        f"okuyucunun pay süzgeci loop'un YAZDIĞI satırı saymıyor — literaller ayrıştı: {d}")
    assert plan["id"] and d["plan_n"] >= 1 and d["dolum_orani"] is not None


def test_e1_diagnostics_yuzeyi_donusum_cekirdegini_TASIR(sandbox_state):
    """YASA 6'nın CANLI bacağı (düzeltme turu 1): `week.donusum` bugüne dek yalnız EMEKLİ
    `/api/selfreview` ucundan okunabiliyordu ("yeni tüketici bağlanmaz" şerhli), yani EDG-042
    hakemi paydayı canlı yüzeyden HİÇ okuyamıyordu. Kanonik yüzey `/api/diagnostics`in
    `selfreview_summary` bloğudur; çekirdek dört alan oraya bağlandı."""
    from fastapi.testclient import TestClient
    from meridian import api
    _seed_conf(sandbox_state)
    c = TestClient(api.app)
    store.write_json("self_review.json", {
        "generated": "2026-09-02T00:00:00+00:00", "attention": [], "contradictions": [],
        "week": {"donusum": {"plan_n": 7, "dolum_n": 2, "dolum_orani": 0.2857,
                             "sinif_dagilimi": {"not_armed": 4, "armed_not_submitted": 0,
                                                "olculemedi": 1},
                             "donusmeyen_n": 5, "beyan": "…"}}})
    sr = c.get("/api/diagnostics?taze=1").json()["selfreview_summary"]
    assert sr is not None and "donusum" in sr, "teşhis yüzeyi dönüşüm satırını taşımıyor"
    d = sr["donusum"]
    assert d["plan_n"] == 7 and d["dolum_n"] == 2 and d["dolum_orani"] == 0.2857
    assert d["sinif_dagilimi"] == {"not_armed": 4, "armed_not_submitted": 0, "olculemedi": 1}

    # UYDURMA YASAĞI: alan YOKSA None — 0 basmak "hiç plan yok" demek olurdu.
    store.write_json("self_review.json", {"generated": "2026-09-02T00:00:00+00:00",
                                          "attention": [], "contradictions": []})
    d2 = c.get("/api/diagnostics?taze=1").json()["selfreview_summary"]["donusum"]
    assert d2 == {"plan_n": None, "dolum_n": None, "dolum_orani": None, "sinif_dagilimi": None}, \
        f"eksik alan sayıya çevrildi (uydurma): {d2}"


def test_d3_okuyucu_sozlugu_TURETIR_kendi_kopyasini_tutmaz():
    """TEK-KAYNAK YASASI: motor adı ve sınıf sözlüğü `loop`ta yaşar; okuyucu onları İTHAL eder.
    İkinci bir kopya sessizce ayrışır ve rapor bir gün var olmayan sınıfı sayardı."""
    kaynak = pathlib.Path(selfreview.__file__).read_text(encoding="utf-8")
    for sabit in ("ayna_seyrelme", "not_armed", "armed_not_submitted", "olculemedi"):
        assert f'"{sabit}"' not in kaynak and f"'{sabit}'" not in kaynak, (
            f"okuyucu `{sabit}` değerini KOPYALAMIŞ — sözlüğün ikinci nüshası ayrışır; "
            f"`loop` sabitlerinden türet")
    fn = next(n for n in ast.walk(ast.parse(kaynak))
              if isinstance(n, ast.FunctionDef) and n.name == "_donusum_ozeti")
    assert any(isinstance(n, ast.ImportFrom) or isinstance(n, ast.Import)
               for n in ast.walk(fn)), "okuyucu sözlüğü ithal etmiyor"
