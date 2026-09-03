"""23c DİNLENEN LİMİT — çiviler (H3, kart EXE-2026-005, plan 2026-08-17).

Bu dosya KODDAN ÖNCE yazıldı (HAT H3 kapısı: çivi önce, kırmızıyı gör, sonra kod).

ÖLÇÜLEN KUSUR: `fill_entry` limit girişini YALNIZ bir ana karşı sınıyor — bir sonraki barın
AÇILIŞINA. `next_open > _limit` ise işlem `EV_MISSED_LIMIT` ile "kaçtı" sayılıyor. Gerçek bir limit
emri ise gün boyu DİNLER: fiyat seans içinde limite geri gelirse emir dolar. Hata TEK YÖNLÜDÜR ve
kaçan-işlem maliyetini SİSTEMATİK OLARAK ABARTIR.

KİLL KRİTERİ ÇİVİLENDİ (kart): "limit fiyatı bar aralığının DIŞINDAysa (low > limit) dolduruldu
sayılırsa geçersiz — bu bir UYDURMA DOLUMdur." → `test_low_limitin_ustundeyse_DOLMAZ`.

CANLI DEĞİŞMEZLİĞİ ÇİVİLENDİ (plan §1): kural `fill_entry` içinde TEK yerde yaşar, davranışı
`bar_low` PARAMETRESİ seçer — mod bayrağı DEĞİL. Canlıda "bugünün low'u" karar anında BİLİNMEZ,
o yüzden `loop.py` onu geçemez; değişmezlik disiplinle korunan bir söz değil YAPISAL olgudur.
→ `test_canli_cagiran_bar_low_GECMEZ`.
"""

import pathlib
import re

import pytest


from meridian import broker as B


def _plan(trigger: float, stop: float) -> dict:
    # Alan kümesi `tests/test_batch_l.py`nin BİLİNEN-İYİ kurulumundan alındı (id + stop +
    # profit_target + size_r). Kendi asgari sözlüğümü alan alan tahmin etmek yerine dolum yolunu
    # zaten uçtan uca geçen bir emsali örnek almak, çivinin ölçtüğü şeyi kurulum gürültüsünden ayırır.
    return {"id": "P-23C", "ticker": "TEST", "stop": stop, "profit_target": trigger * 1.30,
            "entry_trigger": trigger, "size_r": 1.0, "score": 1.0}


# DAR TAVANLI YASA — ÖLÇÜLDÜ 2026-08-17, ve bu çivilerin var olma şartı:
# canlı yasa `E1-v2` `limit_pct_cap=0.04` taşıyor ve bu, `MAX_ENTRY_GAP_PCT=0.04` ile BİREBİR
# AYNI. `max_chase` kapısı limit kapısından ÖNCE sınandığı için canlı ayarda `EV_MISSED_LIMIT`
# YAPISAL OLARAK ULAŞILAMAZ — "limit tavanı yüzünden kaçtı" redleri bugün HİÇ DOĞMUYOR.
# (`limit_atr_mult=100.0` olduğu için ATR terimi de hiç bağlamıyor; cap her zaman baskın.)
# Kartın konusu olan redler E1 grid'in süpürdüğü DAR tavanlarda (ör. 100 bps) doğar; çiviler
# bu yüzden dar tavanlı bir yasayla koşar. Bu bir test kolaylığı DEĞİL, ölçümün geçerli olduğu
# tek bölgedir — canlı ayarda ölçüm yapılsaydı örneklem BOŞ çıkardı.
DAR_TAVAN = 0.01          # 100 bps — ARASTIRMA-SLIPAJ-AZALTMA'nın fırsat kanıtı bu tavanda


_ASIL_YASA = B.entry_law          # yamadan ÖNCE yakalanır — yoksa _dar_yasa kendini çağırır


def _dar_yasa() -> dict:
    return {**_ASIL_YASA(), "limit_pct_cap": DAR_TAVAN}


def _limit_of(trigger: float, atr: float | None = None) -> float:
    return B.entry_limit_price(trigger, atr, _dar_yasa())


def _dar_yasa_yama(monkeypatch) -> None:
    """`fill_entry` yasayı KENDİ içinde `entry_law()` ile okur — yerel bir sözlük ona ulaşmaz.
    Bu yüzden yasa modül düzeyinde yamanır. (İlk hâlde yamamamıştım ve çivi `max_chase` alıyordu:
    testin ölçtüğü kapıya hiç gelmiyordu.)"""
    monkeypatch.setattr(B, "entry_law", _dar_yasa)


def _acilis(lim: float) -> float:
    """Açılış, limit KAPISININ ateşlediği pencerede olmalı: `limit < açılış <= trigger*(1+%4)`.
    Dışına çıkarsa `max_chase` ÖNCE yakalar ve test ölçmek istediği kapıya hiç gelmez —
    ilk hâlde `lim+5.0` yazmıştım ve üç çivi de yanlış kapıyı ölçüyordu (2026-08-17)."""
    return lim + 1.0


def _broker():
    """`PaperBroker(equity, slippage_bps, commission_per_share)` — `mutation.py::_build_ledgers` ile aynı kurulum.

    SKIP KAÇIŞI BİLEREK YOK (2026-08-17 vakası): ilk hâlde `hasattr(B, "Broker")` yanlış ada
    bakıyordu ve `pytest.skip` üç çiviyi sessizce yuttu — koşum "1 passed, 3 skipped" ile YEŞİL
    göründü. Kurulumu bozuk bir çivi, olmayan bir çividen TEHLİKELİDİR: yokluğu görünür, sahte
    yeşili görünmez. Ad değişirse test ÇÖKSÜN."""
    return B.PaperBroker(100_000.0, 5.0, 0.005)


def test_bar_low_verilmezse_BUGUNKU_DAVRANIS_BIT_OZDES(monkeypatch):
    """A KOLU (şasi kontrolü): `bar_low` GEÇİLMEZSE davranış bugünküyle birebir aynı kalmalı.
    Kart: "A kolu edg032b ile bit-özdeş DEĞİLSE ölçüm DURUR — şasi bozuk, hüküm verilmez"."""
    _dar_yasa_yama(monkeypatch)
    trig, stop = 100.0, 95.0
    lim = _limit_of(trig)
    b, red = _broker(), {}
    pos = b.fill_entry(_plan(trig, stop), _acilis(lim), "2026-01-05", 100_000.0, reject_out=red)
    assert pos is None, "açılış limitin ÜSTÜNDE — bugünkü kural kaçtı demeli"
    assert red.get("reason") == B.EV_MISSED_LIMIT or B.EV_MISSED_LIMIT in str(red), red


def test_low_limite_dokunduysa_LIMIT_FIYATINDAN_DOLAR(monkeypatch):
    """B KOLU: açılış limitin üstünde ama gün içinde `low <= limit` → emir DOLAR.
    DOLUM FİYATI `next_open` DEĞİL `limit`tir: dinlenen bir emir kendi fiyatından dolar."""
    _dar_yasa_yama(monkeypatch)
    trig, stop = 100.0, 95.0
    lim = _limit_of(trig)
    b, red = _broker(), {}
    pos = b.fill_entry(_plan(trig, stop), _acilis(lim), "2026-01-05", 100_000.0,
                       bar_low=lim - 0.50, reject_out=red)
    assert pos is not None, f"low limite dokundu ({lim - 0.5} <= {lim}) — emir DOLMALIYDI · {red}"
    # TOLERANS KAPALI FORMDA (inceleme Önemli 5): ilk hâl `< 0.5*lim` idi — lim=101 için kabul
    # aralığı [50,5 · 151,5], yani `next_open`tan (102 → 102,05) dolsa da geçerdi. Totolojiydi.
    # Beklenen değer hesaplanabilir: adv=None olduğu için ETKİ terimi yok, yalnız sabit slipaj.
    beklenen = lim * (1.0 + b.slip)
    assert float(pos.entry) == pytest.approx(beklenen, abs=0.01), (
        f"dolum LİMİT fiyatından olmalı (slipaj dahil {beklenen:.4f}), açılıştan değil: {pos.entry}")


def test_low_limitin_ustundeyse_DOLMAZ_uydurma_dolum_yasak(monkeypatch):
    """KİLL KRİTERİ: fiyat gün boyunca limite HİÇ dokunmadıysa dolum UYDURMADIR.
    Bu çivi düşerse ölçüm geçersizdir — sonuçlar değil, ölçümün kendisi çöker."""
    _dar_yasa_yama(monkeypatch)
    trig, stop = 100.0, 95.0
    lim = _limit_of(trig)
    b, red = _broker(), {}
    pos = b.fill_entry(_plan(trig, stop), _acilis(lim), "2026-01-05", 100_000.0,
                       bar_low=lim + 0.01, reject_out=red)
    assert pos is None, "low limitin ÜSTÜNDE — dolum UYDURMA olurdu, kart bunu kill kriteri yapıyor"
    # RET NEDENİ DE SINANIR (inceleme Küçük 8): yalnız `pos is None` bakmak yetmez — `qty_zero`,
    # `notional_cap`, `already_open` da None döndürür. Limit kapısı bir gün tamamen kaldırılsa ve
    # dolum başka bir kapıya takılsa, kill-kriteri çivisi YEŞİL raporlardı.
    assert red.get("reason") == B.EV_MISSED_LIMIT, (
        f"ret LİMİT kapısından gelmeli, başka bir kapıdan değil: {red}")


def test_canli_cagiran_bar_low_GECMEZ():
    """Kartın ayrışma kill kriteri: "dolum kuralı İKİ yerde uygulanırsa (canlı ↔ replay) geçersiz".

    `fill_entry`nin ALTI çağıranı var; YALNIZ replay (`backtest.py`) `bar_low` geçebilir. Canlı
    (`loop.py`) ve gölge yolları geçemez — ve bu bir tercih değil olgudur: canlıda karar anında
    o günün low'u BİLİNMEZ.

    AST İLE TARANIR, DÜZ METİNLE DEĞİL (2026-08-17 inceleme bulgusu — Kritik 2). İlk hâl
    `metin.split(")")[0]` ile çağrıyı İLK KAPANAN PARANTEZDE kesiyordu; ``loop.daily_cycle` dinlenen-limit bloğu` için
    çivinin gördüğü metin `adv=_adv(per[t], d`'de bitiyordu. Yani CANLI çağrıya `bar_low=`
    eklenebilir ve çivi YEŞİL kalırdı — kartın 1 numaralı kill kriterinin tek bekçisi, korumakla
    görevli olduğu yerde KÖRDÜ. AST üç sızıntı yolunu birden görür: anahtar sözcük, `**sözlük`,
    ve KONUMSAL (imzada `bar_low` 9. argüman). Ayrıştırılamayan dosya da körlüktür → çivi düşer."""
    import ast
    kok = pathlib.Path(__file__).resolve().parents[1] / "meridian"
    izinli = {"backtest.py", "broker.py"}
    suclular = []
    for py in sorted(kok.rglob("*.py")):
        if py.name in izinli:
            continue
        try:
            agac = ast.parse(py.read_text(encoding="utf-8"))
        except SyntaxError as e:      # sessiz-yutma DEĞİL: ayrıştırılamayan dosya körlüktür, ÇİVİ DÜŞER
            raise AssertionError(f"{py.name} ayrıştırılamadı, tarama KÖR kalırdı: {e}") from e
        for d in ast.walk(agac):
            if not isinstance(d, ast.Call):
                continue
            f = d.func
            ad = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
            if ad != "fill_entry":
                continue
            # (a) anahtar sözcükle: bar_low=...   (b) **sozluk ile dolaylı  (c) KONUMSAL: imzada
            # `bar_low` 9. parametre (self hariç 8.) — o kadar konumsal argüman verilirse de sızar.
            if any(k.arg == "bar_low" for k in d.keywords):
                suclular.append(f"{py.name}:{d.lineno} (bar_low=)")
            elif any(k.arg is None for k in d.keywords):
                suclular.append(f"{py.name}:{d.lineno} (**sözlük — bar_low taşıyor OLABİLİR, tarama kesin diyemez)")
            elif len(d.args) >= 9:
                suclular.append(f"{py.name}:{d.lineno} (KONUMSAL {len(d.args)} argüman — bar_low konumuna ulaşıyor)")
    assert not suclular, (
        f"CANLI/GÖLGE yol `bar_low` geçiyor: {suclular} — replay sadakat düzeltmesi canlı davranışa "
        f"SIZDI; kartın ayrışma kill kriteri tetiklendi")


def test_kol_kimligi_SONUCA_damgalanir_ve_backtest_baglantisi_YASAR():
    """KRİTİK 1 (inceleme, 2026-08-17): B kolunun koştuğunun KANITI olmalı.

    İlk B kolu koşumunda A↔B çıktıları YALNIZ zaman damgasında farklıydı; "bayrak açıktı ama
    vaka yoktu" ile "bayrak hiç uygulanmadı" AYIRT EDİLEMİYORDU. Damga o ayrımı yapar.

    İkinci ayak: `backtest.py`nin `bar_low`u GERÇEKTEN barın `low`undan aldığını sınar. Bu
    bağlantının hiç kapsamı yoktu — `"low"` yerine `"close"` yazılsa hiçbir çivi ötmezdi ve
    B koşumu bayt-özdeş çıktığı için ölçüm de yakalamazdı."""
    import ast
    from meridian import backtest as BT

    # (a) DAMGA ALANI VAR ve iki kolu ayırt eder
    assert "dolum_kurali" in BT.BacktestResult.__dataclass_fields__, (
        "kol kimliği sonuca damgalanmıyor — B kolunun koştuğu KANITLANAMAZ")

    # (b) BAĞLANTI: fill_entry çağrısı bar_low'u barın `low` SÜTUNUNDAN alıyor mu?
    kaynak = pathlib.Path(BT.__file__).read_text(encoding="utf-8")
    cagri = next(d for d in ast.walk(ast.parse(kaynak))
                 if isinstance(d, ast.Call)
                 and getattr(d.func, "attr", None) == "fill_entry"
                 and any(k.arg == "bar_low" for k in d.keywords))
    kw = next(k for k in cagri.keywords if k.arg == "bar_low")
    sabitler = [n.value for n in ast.walk(kw.value) if isinstance(n, ast.Constant)]
    assert "low" in sabitler, (
        f"backtest fill_entry çağrısı `bar_low`u 'low' sütunundan ALMIYOR (gördüğüm sabitler: "
        f"{sabitler}) — dinlenen limit yanlış seriye bakıyor olabilir ve bu SESSİZ bir kusurdur")

    # (c) bayrak damgayı GERÇEKTEN sürüyor mu — iki yönü de
    assert BT.DINLENEN_LIMIT is False, "test ortamında A kolu beklenir (bayrak ayarsız)"
