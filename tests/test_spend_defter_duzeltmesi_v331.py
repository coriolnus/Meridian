"""test_spend_defter_duzeltmesi_v331.py — CANLI DEFTERDEKİ UYDURMA MALİYETİN ONARIMI.

BAĞLAM: `price_for` ücretsiz OpenRouter slug'larını Opus listesinden fiyatlıyordu (#14'te
düzeltildi, çivi `test_ucretsiz_katman_fiyati_v325.py`). Kod düzeltmesi yalnız GELECEK satırları
düzeltir: `dagit.sh:30` rsync'i `state/`i DIŞLAR, yani diskteki satırlar dağıtımdan sonra da
aynen yanlış kalır ve `/api/spend` → pano onları okumaya devam eder (ölçüm: 13 çağrı / 7.89 USD).

BU BETİK O SATIRLARI ONARIR — ve onarımın kendisi bu deponun en tehlikeli işidir: CANLI DEFTERE
YAZAR. O yüzden çivi, betiğin YAPTIĞINDAN çok YAPMADIĞINI sınar.

EN ÖNEMLİ ÇİVİ SD1'DİR: varsayılan KURU KOŞUdur. Bir onarım betiğinin varsayılanı yazmaksa,
"ne olacağını göreyim" diye koşan operatör defteri değiştirmiş olur — ve bunu ancak sonradan
fark eder. Emsal (`ops/sermaye_beyani_iade.py`) aynı sözleşmeyi taşır: kuru koşu varsayılan,
`--uygula` açık, `--zorla` worker kapısını aşar, çıkış kodu 2 = canlı worker koşuyor.

SD1  varsayılan KURU: defter BİT BİT aynı kalır, çıkış 0, rapor ne DEĞİŞECEĞİNİ söyler
SD2  `--uygula`: yalnız ücretsiz-varyant + cost_usd>0 satırlar; cost_usd→0, `duzeltme` alanı
     eski değeri + gerekçeyi TAŞIR (sessiz düzeltme yok), ts/model/token DEĞİŞMEZ
SD3  satır sayısı DEĞİŞMEZİ: önce == sonra
SD4  ÇÜRÜTME — ücretli satırlara DOKUNULMAZ (betik "her şeyi sıfırla" değil)
SD5  idempotent: ikinci koşu düzeltilecek satır BULAMAZ (çift düzeltme yok)
SD6  canlı worker koşarken REDDEDER (çıkış 2); `--zorla` ile aşılır (CLAUDE.md §5)
SD7  onarım sonrası satırlar defter SÖZLEŞMESİNE uyar (`ledgers.validate_row` boş)
SD8  düzeltilecek bir şey yoksa yazım YOK, çıkış 0
SD9  `--uygula` MANTIKSAL yedek bırakır (defter DB destekliyse dosya kopyası anlamsızdır —
     yedek satırlardan üretilir)
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

import pytest

from meridian import config, ledgers, spend, store

BETIK = pathlib.Path(__file__).resolve().parents[1] / "ops" / "spend_defter_duzeltmesi.py"


def _mod():
    assert BETIK.exists(), f"betik YOK: {BETIK}"
    spec = importlib.util.spec_from_file_location("spend_defter_duzeltmesi", BETIK)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


UCRETSIZ = "nvidia/nemotron-3-super-120b-a12b:free"
UCRETSIZ2 = "tencent/hy3:free"
UCRETLI = "claude-opus-4-8"


@pytest.fixture()
def defter(sandbox_state):
    """Canlı kesitin biçimce aynısı: uydurma maliyet taşıyan ücretsiz satırlar + gerçek ücretli
    satır + zaten 0 olan ücretsiz satır (dokunulmamalı)."""
    rows = [
        {"ts": "2026-08-20T10:00:00+00:00", "model": UCRETSIZ, "in_tokens": 10_000,
         "out_tokens": 2_000, "cost_usd": 0.649, "note": "reflect"},
        {"ts": "2026-08-21T10:00:00+00:00", "model": UCRETSIZ2, "in_tokens": 5_000,
         "out_tokens": 1_000, "cost_usd": 0.15, "note": "review"},
        {"ts": "2026-08-22T10:00:00+00:00", "model": UCRETLI, "in_tokens": 10_000,
         "out_tokens": 2_000, "cost_usd": 0.30, "note": "reflect"},
        {"ts": "2026-08-23T10:00:00+00:00", "model": UCRETSIZ, "in_tokens": 1_000,
         "out_tokens": 100, "cost_usd": 0.0, "note": "zaten dogru"},
    ]
    for r in rows:
        store.append_jsonl("spend.jsonl", r)
    return rows


def _oku():
    return store.read_jsonl("spend.jsonl")


# ---------- SD1: VARSAYILAN KURU KOŞU ----------
def test_sd1_varsayilan_KURU_defteri_DEGISTIRMEZ(defter, monkeypatch):
    m = _mod()
    monkeypatch.setattr(m, "_worker_running", lambda: False)
    once = json.dumps(_oku(), sort_keys=True, ensure_ascii=False)
    rc = m.main([])
    sonra = json.dumps(_oku(), sort_keys=True, ensure_ascii=False)
    assert rc == 0
    assert once == sonra, "VARSAYILAN KOŞU DEFTERİ DEĞİŞTİRDİ — kuru koşu sözleşmesi kırık"


def test_sd1b_kuru_kosu_ne_degisecegini_SOYLER(defter, monkeypatch, capsys):
    """Sessiz kuru koşu işe yaramaz: operatör kararı çıktıya bakarak verir."""
    m = _mod()
    monkeypatch.setattr(m, "_worker_running", lambda: False)
    m.main([])
    cik = capsys.readouterr().out
    assert "2" in cik, "düzeltilecek satır SAYISI basılmıyor"
    assert UCRETSIZ in cik or "nemotron" in cik, "hangi model etkileniyor yazılmıyor"
    assert "KURU" in cik.upper() or "DRY" in cik.upper(), "kuru koşu olduğu ADIYLA söylenmiyor"


# ---------- SD2: --uygula ----------
def test_sd2_uygula_yalniz_ucretsiz_satirlari_duzeltir(defter, monkeypatch):
    m = _mod()
    monkeypatch.setattr(m, "_worker_running", lambda: False)
    assert m.main(["--uygula"]) == 0
    rows = _oku()
    duzeltilen = [r for r in rows if "duzeltme" in r]
    assert len(duzeltilen) == 2, f"beklenen 2 düzeltme, bulunan {len(duzeltilen)}"
    for r in duzeltilen:
        assert r["cost_usd"] == 0.0
        assert spend._is_free_variant(str(r["model"]).lower())


def test_sd2b_duzeltme_alani_ESKI_DEGERI_ve_GEREKCEYI_tasir(defter, monkeypatch):
    """SESSİZ DÜZELTME YOK: defterin kendisi ne olduğunu anlatmalı (UYDURMA YASAĞI komşusu —
    düzeltilmiş bir sayı, düzeltildiği yazılmazsa yine ölçülemeyen bir sayıdır)."""
    m = _mod()
    monkeypatch.setattr(m, "_worker_running", lambda: False)
    m.main(["--uygula"])
    r = next(x for x in _oku() if x["model"] == UCRETSIZ and "duzeltme" in x)
    d = r["duzeltme"]
    assert d["eski_cost_usd"] == 0.649, "eski değer kaybolmuş — düzeltme denetlenemez"
    assert str(d.get("neden", "")).strip(), "gerekçe yok"
    assert str(d.get("tarih", "")).strip(), "tarih yok"


def test_sd2c_ts_model_ve_tokenlar_DEGISMEZ(defter, monkeypatch):
    m = _mod()
    monkeypatch.setattr(m, "_worker_running", lambda: False)
    once = {r["ts"]: (r["model"], r["in_tokens"], r["out_tokens"]) for r in _oku()}
    m.main(["--uygula"])
    sonra = {r["ts"]: (r["model"], r["in_tokens"], r["out_tokens"]) for r in _oku()}
    assert once == sonra, "onarım ölçülmüş alanlara dokundu — yalnız cost_usd düzeltilir"


# ---------- SD3: satır sayısı değişmezi ----------
def test_sd3_satir_sayisi_DEGISMEZ(defter, monkeypatch):
    m = _mod()
    monkeypatch.setattr(m, "_worker_running", lambda: False)
    once = len(_oku())
    m.main(["--uygula"])
    assert len(_oku()) == once, "satır sayısı değişti — onarım satır ekledi/sildi"


# ---------- SD4: ÇÜRÜTME ----------
def test_sd4_ucretli_satira_DOKUNULMAZ(defter, monkeypatch):
    """Boş çivi sınavı: betik her satırı sıfırlasaydı SD2 de geçerdi."""
    m = _mod()
    monkeypatch.setattr(m, "_worker_running", lambda: False)
    m.main(["--uygula"])
    r = next(x for x in _oku() if x["model"] == UCRETLI)
    assert r["cost_usd"] == 0.30, "ÜCRETLİ satır sıfırlandı — harcanmış para defterden silindi"
    assert "duzeltme" not in r


def test_sd4b_zaten_sifir_olan_ucretsiz_satir_DAMGALANMAZ(defter, monkeypatch):
    """`cost_usd > 0` şartı: doğru olan satıra düzeltme damgası basmak, düzeltilmemiş bir şeyi
    düzeltilmiş göstermek olurdu."""
    m = _mod()
    monkeypatch.setattr(m, "_worker_running", lambda: False)
    m.main(["--uygula"])
    r = next(x for x in _oku() if x["note"] == "zaten dogru")
    assert "duzeltme" not in r


# ---------- SD5: idempotent ----------
def test_sd5_ikinci_kosu_DUZELTILECEK_SATIR_BULMAZ(defter, monkeypatch, capsys):
    m = _mod()
    monkeypatch.setattr(m, "_worker_running", lambda: False)
    m.main(["--uygula"])
    once = json.dumps(_oku(), sort_keys=True, ensure_ascii=False)
    capsys.readouterr()
    assert m.main(["--uygula"]) == 0
    assert json.dumps(_oku(), sort_keys=True, ensure_ascii=False) == once, "ikinci koşu defteri değiştirdi"


# ---------- SD6: canlı worker kapısı (CLAUDE.md §5) ----------
def test_sd6_canli_worker_kosarken_REDDEDER(defter, monkeypatch):
    m = _mod()
    monkeypatch.setattr(m, "_worker_running", lambda: True)
    once = json.dumps(_oku(), sort_keys=True, ensure_ascii=False)
    assert m.main(["--uygula"]) == 2, "worker koşarken yazım REDDEDİLMEDİ"
    assert json.dumps(_oku(), sort_keys=True, ensure_ascii=False) == once, "reddettim dedi ama YAZDI"


def test_sd6b_zorla_worker_kapisini_asar(defter, monkeypatch):
    m = _mod()
    monkeypatch.setattr(m, "_worker_running", lambda: True)
    assert m.main(["--uygula", "--zorla"]) == 0
    assert any("duzeltme" in r for r in _oku())


def test_sd6c_worker_kosarken_KURU_kosu_SERBEST(defter, monkeypatch):
    """Kuru koşu yazmaz, dolayısıyla worker'la yarışmaz — engellenmesi gereksiz sürtünme olurdu."""
    m = _mod()
    monkeypatch.setattr(m, "_worker_running", lambda: True)
    assert m.main([]) == 0


# ---------- SD7: defter sözleşmesi ----------
def test_sd7_onarilan_satirlar_defter_SOZLESMESINE_uyar(defter, monkeypatch):
    m = _mod()
    monkeypatch.setattr(m, "_worker_running", lambda: False)
    m.main(["--uygula"])
    for r in _oku():
        assert ledgers.validate_row("spend.jsonl", r) == [], f"sözleşme ihlali: {r}"


def test_sd7b_ay_toplami_duser_ve_butce_serbest_kalir(defter, monkeypatch):
    """Onarımın ASIL amacı: harcanmamış para bütçe kapısını beslemesin."""
    m = _mod()
    monkeypatch.setattr(m, "_worker_running", lambda: False)
    m.main(["--uygula"])
    assert spend.month_spend("2026-08") == pytest.approx(0.30), "yalnız gerçek harcama kalmalı"


# ---------- SD8: yapacak iş yok ----------
def test_sd8_duzeltilecek_sey_yoksa_YAZIM_YOK(sandbox_state, monkeypatch):
    store.append_jsonl("spend.jsonl", {"ts": "2026-08-22T10:00:00+00:00", "model": UCRETLI,
                                       "in_tokens": 10, "out_tokens": 2, "cost_usd": 0.3})
    m = _mod()
    monkeypatch.setattr(m, "_worker_running", lambda: False)
    once = json.dumps(_oku(), sort_keys=True, ensure_ascii=False)
    assert m.main(["--uygula"]) == 0
    assert json.dumps(_oku(), sort_keys=True, ensure_ascii=False) == once


# ---------- SD9: yedek ----------
def test_sd9_uygula_MANTIKSAL_yedek_birakir(defter, monkeypatch):
    """Defter canlıda SQLite destekli olabilir (07-31 göçü) — dosya kopyalamak bayat kalıntıyı
    yedeklemek olurdu. Yedek `store`dan OKUNAN satırlardan üretilir."""
    m = _mod()
    monkeypatch.setattr(m, "_worker_running", lambda: False)
    m.main(["--uygula"])
    yedekler = sorted(pathlib.Path(config.STATE).glob("spend.jsonl.bak-*"))
    assert yedekler, "yedek YOK — geri alma yolu bırakılmamış"
    satirlar = [json.loads(x) for x in yedekler[-1].read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(satirlar) == len(defter), "yedek defterin tamamını taşımıyor"
    assert any(r["cost_usd"] == 0.649 for r in satirlar), "yedek DÜZELTME ÖNCESİ hâli taşımalı"


# ================================================================================================
# SD10 — CLI GİRİŞİ (gerçek koşumda bulundu, 2026-08-29)
# ------------------------------------------------------------------------------------------------
# VAKA: yukarıdaki 16 çivi YEŞİLKEN betik komut satırından `--uygula` ile koşuldu ve
# "KURU KOŞU (varsayılan)" yazıp HİÇBİR ŞEY YAPMADI. Kök neden `main()` içindeydi:
#     ap.parse_args([] if argv is None else argv)
# Betik olarak koşulunca `main()` argv=None alır → `parse_args([])` → `sys.argv` TAMAMEN ATILIR.
# Yani betik komut satırından ASLA uygulayamazdı.
#
# ÇİVİLER NEDEN GÖRMEDİ: hepsi `main(["--uygula"])`ı DOĞRUDAN çağırıyor, yani API'yi sınıyor,
# GİRİŞ NOKTASINI değil. Bir ops betiğinin sözleşmesi ise komut satırıdır — operatör onu
# `python ops/...py --uygula` diye koşar, `main()` diye değil. Aşağıdaki iki çivi o boşluğu
# kapatır ve betiği GERÇEKTEN koşturur (alt süreç + izole MERIDIAN_ROOT).
# ================================================================================================

def _kum(tmp_path: pathlib.Path) -> pathlib.Path:
    """İzole bir MERIDIAN_ROOT: state/ + iki uydurma + bir gerçek satır."""
    (tmp_path / "state").mkdir()
    repo_state = pathlib.Path(__file__).resolve().parents[1] / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        if (repo_state / f).exists():
            (tmp_path / "state" / f).write_bytes((repo_state / f).read_bytes())
    rows = [
        {"ts": "2026-08-20T10:00:00+00:00", "model": UCRETSIZ, "in_tokens": 10_000,
         "out_tokens": 2_000, "cost_usd": 0.649, "note": "reflect"},
        {"ts": "2026-08-21T10:00:00+00:00", "model": UCRETSIZ2, "in_tokens": 5_000,
         "out_tokens": 1_000, "cost_usd": 0.15, "note": "review"},
        {"ts": "2026-08-22T10:00:00+00:00", "model": UCRETLI, "in_tokens": 10_000,
         "out_tokens": 2_000, "cost_usd": 0.30, "note": "gercek"},
    ]
    (tmp_path / "state" / "spend.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    return tmp_path / "state" / "spend.jsonl"


def _kos(kok: pathlib.Path, *bayrak: str):
    import os
    import subprocess
    ort = {**os.environ, "MERIDIAN_ROOT": str(kok), "MERIDIAN_DB": "off"}
    return subprocess.run([sys.executable, str(BETIK), *bayrak],
                          capture_output=True, text=True, env=ort)


def test_sd10_CLI_uygula_bayragini_GERCEKTEN_uygular(tmp_path):
    """GİRİŞ NOKTASI ÇİVİSİ: `main([...])` değil, betiğin KENDİSİ koşulur."""
    defter_yolu = _kum(tmp_path)
    once = defter_yolu.read_text(encoding="utf-8")
    r = _kos(tmp_path, "--uygula")
    assert r.returncode == 0, f"çıkış {r.returncode}\n{r.stdout}\n{r.stderr}"
    sonra = defter_yolu.read_text(encoding="utf-8")
    assert sonra != once, (
        "CLI'dan --uygula HİÇBİR ŞEY YAPMADI — argparse sys.argv'yi görmüyor olabilir\n"
        f"{r.stdout}")
    rows = [json.loads(x) for x in sonra.splitlines() if x.strip()]
    assert sum("duzeltme" in x for x in rows) == 2
    assert next(x for x in rows if x["model"] == UCRETLI)["cost_usd"] == 0.30


def test_sd10b_CLI_bayraksiz_KURU_kalir(tmp_path):
    """Ters yön: bayraksız çağrı komut satırından da YAZMAMALI."""
    defter_yolu = _kum(tmp_path)
    once = defter_yolu.read_text(encoding="utf-8")
    r = _kos(tmp_path)
    assert r.returncode == 0, r.stderr
    assert defter_yolu.read_text(encoding="utf-8") == once, "bayraksız CLI koşusu DEFTERE YAZDI"
    assert "KURU" in r.stdout.upper()
