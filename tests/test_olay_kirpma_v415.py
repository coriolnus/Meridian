"""v415 — `ops/olay_sikistir.py --kirp` (adım 3) + `meridian/olaylar.py::tum_olaylar` çivileri
(TSK-137b, 2026-09-05).

NUMARA SEÇİMİ: `ls tests/ | grep -oE "v[0-9]{3}" | sort -u | tail -1` ile ölçüldü — en büyük
alınmış numara v413'tü (2026-09-05). v415 boştu; `ls tests | grep -E "v415|v416"` boş döndü,
çakışma yok.

NEYİ ÇİVİLER (sınıf sınıf, D5 sırasıyla):
  1. KIRPMA ÜÇ AYI İKİYE İNDİRİR: sıkıştır → kırp → jsonl'de yalnız CARİ+ÖNCEKİ ay kalır, EN
     ESKİ ay yalnız parquet'te yaşar; `state/olaylar/manifest.json` doğru kayıt taşır.
  2. UYUMSUZLUK (arşiv/defter içerik olarak EŞLEŞMİYOR — FARK) → kırpma TÜMÜYLE reddedilir,
     jsonl BAYT BAYT dokunulmamış kalır, gerekçe stderr'e ("olay_kirpma_reddedildi") basılır.
  3. BİRLEŞİK GÖRÜNÜM (`meridian.olaylar.tum_olaylar`) sıkıştırma+kırpma ÖNCESİ tam listeyle
     BİREBİR eşittir — hem GEÇİŞ döneminde (sıkıştırılmış ama henüz kırpılmamış: tekilleştirme
     sınanır) hem TAM KIRPMA sonrasında.
  4. `limit=None` OKUYUCU (`watchdog.integrity_report`) kırpma ÖNCESİ/SONRASI AYNI raporu verir
     — kırpma bir okuyucu sözleşmesini SESSİZCE değiştirmemeli.
  5. WORKER AKTİFKEN (`MERIDIAN_KIRPMA_TEST_WORKER_AKTIF=1` — gerçek `systemctl`in test/CI
     seçeneği, subprocess'e env ile kalıtılır) `--kirp` REDDEDİLİR (rc=5), `--zorla` ile geçer.
  6. MUTASYON: `kirpma_hedeflerini_belirle`nin FARK-reddi şartı KALDIRILINCA çivi #2 ÖTER —
     yeşilin doğrulamayı GERÇEKTEN ısırdığının kanıtı.

SÖZLEŞME KOMUT SATIRIDIR (v355/v379'dan devralınan disiplin): ops betiği `subprocess` ile
ÇAĞRILIR, `main()` import EDİLMEZ. GERÇEK DEFTERE DOKUNULMAZ: her çivi `tmp_path` altına kendi
sentetik jsonl'ini yazar; `meridian.olaylar`/`watchdog` çivileri `sandbox_state` fikstürüyle
izole edilir. `state/`e DOKUNMADAN çalışır (ops çivileri `tmp_path`te, meridian çivileri
sandbox'ta) — pytest DIŞI hiçbir koşum yoktur, tamamı bu dosyanın KENDİSİ pytest altında koşar."""

from __future__ import annotations

import datetime as _dt
import json
import pathlib
import subprocess
import sys

import pytest

KOK = pathlib.Path(__file__).resolve().parents[1]
SIKISTIR = KOK / "ops" / "olay_sikistir.py"
SORGU = KOK / "ops" / "olay_sorgu.py"

WORKER_ENV = "MERIDIAN_KIRPMA_TEST_WORKER_AKTIF"

# ---------------------------------------------------------------------------------------------
# Sentetik defter — v379 emsali: aylar KOŞUM ANINA GÖRE türetilir (sabit tarih er ya da geç
# "cari ay" iddiasını kaybeder).
# ---------------------------------------------------------------------------------------------

_SIMDI = _dt.datetime.now(_dt.timezone.utc)


def _ay_kaydir(n: int) -> str:
    t = _SIMDI.year * 12 + (_SIMDI.month - 1) + n
    return f"{t // 12:04d}-{t % 12 + 1:02d}"


CARI = _ay_kaydir(0)
ONCEKI = _ay_kaydir(-1)
ESKI = _ay_kaydir(-2)   # kırpma sonrası jsonl'den DÜŞMESİ gereken TEK ay


def _satir(ay: str, gun: str, saat: str, event: str, **ek) -> dict:
    return {"ts": f"{ay}-{gun}T{saat}+00:00", "level": "info", "event": event, **ek}


# ESKİ 4 satır, ÖNCEKİ 3 satır, CARİ 2 satır — hepsi ts ARTAN sırada (dosya doğal sırası =
# ts sırası, `tum_olaylar`in açık sıralamasıyla BİREBİR aynı sonucu vermesi için).
UC_AY_SATIRLARI = [
    _satir(ESKI, "01", "09:00:00", "daily_cycle", candidates=3),
    _satir(ESKI, "02", "10:00:00", "hotstate_down", url="http://a"),
    _satir(ESKI, "03", "08:00:00", "breaker_trip", detail="kapak attı"),
    _satir(ESKI, "04", "07:00:00", "daily_cycle", candidates=1),
    _satir(ONCEKI, "01", "09:00:00", "daily_cycle", candidates=2),
    _satir(ONCEKI, "02", "10:00:00", "hotstate_down", url="http://b"),
    _satir(ONCEKI, "03", "11:00:00", "breaker_trip", detail="ikinci kapak"),
    _satir(CARI, "01", "09:00:00", "daily_cycle", candidates=7),
    _satir(CARI, "01", "10:00:00", "hotstate_down", url="http://c"),
]
AY_ADEDI = {ESKI: 4, ONCEKI: 3, CARI: 2}


def _defter_yaz(dizin: pathlib.Path, satirlar=None) -> pathlib.Path:
    p = dizin / "olaylar.jsonl"
    govde = [json.dumps(s) for s in (UC_AY_SATIRLARI if satirlar is None else satirlar)]
    p.write_text("\n".join(govde) + "\n", encoding="utf-8")
    return p


def _hedef(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path / "olaylar"


def kos(betik: pathlib.Path, *argv: str, env: dict | None = None):
    """Aracı OPERATÖRÜN koşacağı biçimde çağırır: komut satırı, `main()` değil."""
    return subprocess.run([sys.executable, str(betik), *argv],
                          capture_output=True, text=True, cwd=str(KOK), env=env)


def sikistir(*argv: str, env: dict | None = None):
    return kos(SIKISTIR, *argv, env=env)


def sorgula(*argv: str, env: dict | None = None):
    return kos(SORGU, *argv, env=env)


def _jsonl_cikti(r) -> list[dict]:
    return [json.loads(s) for s in r.stdout.splitlines() if s.strip()]


def _aylar_jsonlde(p: pathlib.Path) -> dict:
    """Dosyadaki her AY için satır sayısı — bağımsız (olay_sorgu/olay_sikistir'e GÜVENMEDEN)
    ölçüm: doğrudan `ts` alanının ilk 7 karakteri (`AAAA-AA`, `_satir`in ürettiği biçimle
    BİREBİR uyumlu)."""
    sayac: dict[str, int] = {}
    for satir in p.read_text(encoding="utf-8").splitlines():
        if not satir.strip():
            continue
        d = json.loads(satir)
        ay = str(d.get("ts") or "")[:7]
        sayac[ay] = sayac.get(ay, 0) + 1
    return sayac


# ---------------------------------------------------------------------------------------------
# 1. KIRPMA — üç aydan ikiye iner, manifest doğru
# ---------------------------------------------------------------------------------------------

def test_kirpma_uc_aydan_ikiye_indirir_manifest_dogru(tmp_path, monkeypatch):
    monkeypatch.setenv(WORKER_ENV, "0")   # worker DURGUN — gerçek kapı bu dalı test eder
    p = _defter_yaz(tmp_path)
    once_bayt = len(p.read_bytes())

    r_sik = sikistir("--dosya", str(p))
    assert r_sik.returncode == 0, r_sik.stderr
    assert sorted(f.name for f in _hedef(tmp_path).iterdir()) == [
        f"{ESKI}.parquet", f"{ONCEKI}.parquet"]

    r = sikistir("--dosya", str(p), "--kirp", "--json")
    assert r.returncode == 0, r.stdout + r.stderr

    kalan = _aylar_jsonlde(p)
    assert kalan == {ONCEKI: AY_ADEDI[ONCEKI], CARI: AY_ADEDI[CARI]}, kalan
    assert ESKI not in kalan, "en eski ay jsonl'de HÂLÂ duruyor — kırpma çalışmadı"
    assert len(p.read_bytes()) < once_bayt, "dosya küçülmedi"

    # Parquet dizini DOKUNULMADI (kırpma yalnız jsonl'i değiştirir, arşivi DEĞİL).
    assert sorted(f.name for f in _hedef(tmp_path).iterdir() if f.suffix == ".parquet") == [
        f"{ESKI}.parquet", f"{ONCEKI}.parquet"]

    manifest = json.loads((_hedef(tmp_path) / "manifest.json").read_text(encoding="utf-8"))
    kayit = manifest["kirpilan_aylar"][ESKI]
    assert kayit["satir"] == AY_ADEDI[ESKI], kayit
    assert kayit["dosya"].endswith(f"{ESKI}.parquet"), kayit
    assert isinstance(kayit["damga"], str) and len(kayit["damga"]) >= 32, kayit
    assert kayit.get("kirpma_ts"), "kırpma zamanı manifestte YOK"
    assert ONCEKI not in manifest["kirpilan_aylar"], "önceki ay kırpma HEDEFİ değildi"


def test_kirpma_hicbir_ay_hedef_degilse_hicbir_sey_silmez(tmp_path, monkeypatch):
    """Defter zaten cari+önceki aydan İBARETSE kırpılacak ay YOKTUR — rc=0, jsonl DOKUNULMAZ."""
    monkeypatch.setenv(WORKER_ENV, "0")
    iki_ay = [s for s in UC_AY_SATIRLARI if not s["ts"].startswith(ESKI)]
    p = _defter_yaz(tmp_path, satirlar=iki_ay)
    once = p.read_bytes()
    r = sikistir("--dosya", str(p), "--kirp")
    assert r.returncode == 0, r.stdout + r.stderr
    assert p.read_bytes() == once
    assert "yok" in r.stderr.lower()


def test_kirp_kuru_kosum_onizler_hicbir_sey_silmez(tmp_path, monkeypatch):
    monkeypatch.setenv(WORKER_ENV, "0")
    p = _defter_yaz(tmp_path)
    assert sikistir("--dosya", str(p)).returncode == 0
    once = p.read_bytes()
    r = sikistir("--dosya", str(p), "--kirp", "--kuru")
    assert r.returncode == 0, r.stdout + r.stderr
    assert p.read_bytes() == once, "kuru koşum jsonl'e DOKUNDU"
    assert ESKI in r.stderr, r.stderr


def test_kirp_ile_ay_bayragi_birlikte_reddedilir(tmp_path):
    p = _defter_yaz(tmp_path)
    r = sikistir("--dosya", str(p), "--kirp", "--ay", ONCEKI)
    assert r.returncode == 2, r.stdout + r.stderr
    assert "--kirp" in r.stderr and "--ay" in r.stderr


def test_kirp_TEK_COSUMDA_onceki_sikistirma_olmadan_da_calisir(tmp_path, monkeypatch):
    """GERÇEKÇİ KULLANIM: operatör `--kirp`i AYRI bir sıkıştırma koşumu YAPMADAN doğrudan
    çağırabilmeli — sıkıştırma adımı `--kirp`in İÇİNDE ZATEN koşuyor (main()'in tek akışı)."""
    monkeypatch.setenv(WORKER_ENV, "0")
    p = _defter_yaz(tmp_path)
    assert not _hedef(tmp_path).exists(), "arşiv daha koşum ÖNCESİ var olmamalı"

    r = sikistir("--dosya", str(p), "--kirp", "--json")
    assert r.returncode == 0, r.stdout + r.stderr

    assert sorted(f.name for f in _hedef(tmp_path).iterdir() if f.suffix == ".parquet") == [
        f"{ESKI}.parquet", f"{ONCEKI}.parquet"]
    kalan = _aylar_jsonlde(p)
    assert kalan == {ONCEKI: AY_ADEDI[ONCEKI], CARI: AY_ADEDI[CARI]}, kalan


# ---------------------------------------------------------------------------------------------
# 2. UYUMSUZLUK — FARK bulunan ay varsa TÜM kırpma reddedilir, hiçbir şey silinmez
# ---------------------------------------------------------------------------------------------

def test_uyumsuzlukta_kirpma_tumuyle_reddedilir_hicbir_sey_silinmez(tmp_path, monkeypatch):
    """`ESKİ` ayı ÖNCE sıkıştırılır (arşiv jsonl'le eşleşir), SONRA jsonl'deki o ayın içeriği
    DEĞİŞTİRİLİR (arşiv artık BAYAT) — `--kirp` bu FARK'ı `kirpma_hedeflerini_belirle`nin FARK
    kapısında yakalamalı: TÜM kırpma reddedilir (yalnız ESKİ değil), jsonl BAYT BAYT aynı kalır,
    `.yeni` sıkıştırma sözleşmesi gereği yazılır ama jsonl'e KESİNLİKLE dokunulmaz."""
    monkeypatch.setenv(WORKER_ENV, "0")
    p = _defter_yaz(tmp_path)
    assert sikistir("--dosya", str(p)).returncode == 0   # ESKİ+ÖNCEKİ arşivlenir (eşleşir)

    # ESKİ ayına SONRADAN bir satır ekle — arşiv artık jsonl'le UYUŞMUYOR.
    degisik = UC_AY_SATIRLARI + [_satir(ESKI, "05", "12:00:00", "sonradan_geldi")]
    _defter_yaz(tmp_path, satirlar=degisik)
    once_bayt = p.read_bytes()

    r = sikistir("--dosya", str(p), "--kirp", "--json")
    assert r.returncode == 5, r.stdout + r.stderr
    assert "olay_kirpma_reddedildi" in r.stderr, r.stderr
    assert ESKI in r.stderr, r.stderr

    assert p.read_bytes() == once_bayt, "jsonl UYUMSUZLUK sırasında DEĞİŞTİ"
    # Sıkıştırma sözleşmesi (v379) hâlâ geçerli: `.yeni` yazıldı, eski dosya dokunulmadı.
    assert (_hedef(tmp_path) / f"{ESKI}.parquet.yeni").exists()


# ---------------------------------------------------------------------------------------------
# 3. BİRLEŞİK GÖRÜNÜM — kırpma öncesi tam listeyle BİREBİR
# ---------------------------------------------------------------------------------------------

def test_birlesik_gorunum_geciste_ve_kirpma_sonrasi_birebir_esittir(sandbox_state, monkeypatch):
    monkeypatch.setenv(WORKER_ENV, "0")
    from meridian import olaylar, store

    store.write_jsonl("events.jsonl", UC_AY_SATIRLARI)
    once = store.read_jsonl("events.jsonl")
    assert len(once) == len(UC_AY_SATIRLARI)

    p = sandbox_state / "events.jsonl"
    assert sikistir("--dosya", str(p)).returncode == 0
    # GEÇİŞ DÖNEMİ: sıkıştırılmış ama HENÜZ KIRPILMAMIŞ — jsonl'de ESKİ+ÖNCEKİ hâlâ duruyor,
    # arşivde de duruyor. Tekilleştirme (parquet kazanır) burada sınanır.
    gecis = olaylar.tum_olaylar()
    assert gecis == once, "geçiş döneminde birleşik görünüm çift saydı ya da bir şey kaybetti"

    assert sikistir("--dosya", str(p), "--kirp").returncode == 0
    sonra = olaylar.tum_olaylar()
    assert sonra == once, "kırpma SONRASI birleşik görünüm tam listeyle birebir eşleşmiyor"


def test_birlesik_gorunum_baslangic_bitis_suzgeci(sandbox_state, monkeypatch):
    """`baslangic`/`bitis` (ISO-8601, dahil sınırlar) BİRLEŞTİRME SONRASI uygulanır — kırpılmış
    bir defterde de arşivden gelen satırları süzebilmeli."""
    monkeypatch.setenv(WORKER_ENV, "0")
    from meridian import olaylar, store

    store.write_jsonl("events.jsonl", UC_AY_SATIRLARI)
    p = sandbox_state / "events.jsonl"
    assert sikistir("--dosya", str(p)).returncode == 0
    assert sikistir("--dosya", str(p), "--kirp").returncode == 0

    yalniz_eski = olaylar.tum_olaylar(bitis=f"{ESKI}-99")
    assert {e["event"] for e in yalniz_eski} == {"daily_cycle", "hotstate_down", "breaker_trip"}
    assert all(str(e["ts"]).startswith(ESKI) for e in yalniz_eski), yalniz_eski


# ---------------------------------------------------------------------------------------------
# 4. limit=None OKUYUCU — integrity_report kırpma öncesi/sonrası AYNI
# ---------------------------------------------------------------------------------------------

@pytest.fixture
def uc_ay_ortami(sandbox_state):
    from meridian import store
    store.write_jsonl("events.jsonl", UC_AY_SATIRLARI)
    store.write_jsonl("trade_plans.jsonl", [])
    store.write_jsonl("trades.jsonl", [])
    store.write_jsonl("counterfactuals.jsonl", [])
    store.write_json("portfolio.json", {"last_date": _dt.date.today().isoformat(),
                                        "positions": {}, "armed": []})
    return sandbox_state


def _parity_satirlarini_adiyla_indeksle(rep: dict) -> dict:
    return {row["check"]: row for row in rep["parity"]["rows"]}


def test_integrity_report_kirpma_oncesi_sonrasi_ayni_sonucu_verir(uc_ay_ortami, monkeypatch):
    """`limit=None` PAYLAŞILAN okuma (bu turun D2 hedefi) kırpma öncesi/sonrası AYNI sonucu
    vermeli. TEK BİLİNEN/KABUL EDİLMİŞ İSTİSNA: `parity.rows`in `ledger_contract:events` satırı
    — bu satır `meridian.ledgers.validate_live("events.jsonl", sample=200)` üzerinden GELİR,
    yani `limit=200` SINIRLI bir okumadır (D2 kapsamı yalnız `limit=None` okuyucuları taşıdı;
    bu ZATEN sınırlı bir okuma, taşınmadı). Kırpma sonrası FİZİKSEL dosyanın satır sayısı GERÇEKTEN
    azaldığı için bu satırın `detail`indeki sayı (9→5) DEĞİŞİR — bu bir regresyon DEĞİL, sözleşme
    denetiminin doğru çalıştığının kanıtıdır (`ok` alanı İKİSİNDE de True kalmalı)."""
    monkeypatch.setenv(WORKER_ENV, "0")
    from meridian import watchdog as wd

    once = wd.integrity_report()
    p = uc_ay_ortami / "events.jsonl"
    assert sikistir("--dosya", str(p)).returncode == 0
    assert sikistir("--dosya", str(p), "--kirp").returncode == 0
    sonra = wd.integrity_report()

    bilinen_ad = "ledger_contract:events"
    pr_once, pr_sonra = _parity_satirlarini_adiyla_indeksle(once), _parity_satirlarini_adiyla_indeksle(sonra)
    assert pr_once.get(bilinen_ad, {}).get("ok") is True
    assert pr_sonra.get(bilinen_ad, {}).get("ok") is True, (
        "kırpma sonrası events sözleşme denetimi KIRMIZI oldu — bu regresyon, bilinen istisna değil")

    def _normalize(rep: dict) -> dict:
        rep = json.loads(json.dumps(rep))   # derin kopya — orijinali BOZMADAN normalize et
        for row in rep["parity"]["rows"]:
            if row["check"] == bilinen_ad:
                row["detail"] = "<BİLİNEN İSTİSNA: fiziksel satır sayısı kırpmayla değişir>"
                row["neden"] = row["detail"]
        return rep

    assert _normalize(once) == _normalize(sonra), (
        "kırpma sonrası integrity_report BİLİNEN istisna DIŞINDA FARKLI bir hüküm verdi")


# ---------------------------------------------------------------------------------------------
# 5. WORKER KAPISI — aktifken reddeder, `--zorla` ile geçer
# ---------------------------------------------------------------------------------------------

def test_worker_aktifken_kirp_reddedilir(tmp_path, monkeypatch):
    p = _defter_yaz(tmp_path)
    assert sikistir("--dosya", str(p)).returncode == 0
    once_bayt = p.read_bytes()

    monkeypatch.setenv(WORKER_ENV, "1")
    r = sikistir("--dosya", str(p), "--kirp")
    assert r.returncode == 5, r.stdout + r.stderr
    assert "olay_kirpma_reddedildi" in r.stderr, r.stderr
    assert "AKTİF" in r.stderr, r.stderr
    assert p.read_bytes() == once_bayt, "worker AKTİFKEN jsonl DEĞİŞTİ"


def test_worker_durumu_olculemezse_de_reddedilir(tmp_path, monkeypatch):
    """`MERIDIAN_KIRPMA_TEST_WORKER_AKTIF` VERİLMEZSE ve `systemctl` yoksa (yerel makine)
    durum ÖLÇÜLEMEZ — fail-safe: `--zorla` olmadan REDDEDİLİR (aktifmiş gibi davranılır)."""
    p = _defter_yaz(tmp_path)
    assert sikistir("--dosya", str(p)).returncode == 0
    monkeypatch.delenv(WORKER_ENV, raising=False)
    if shutil_which_systemctl():
        pytest.skip("bu makinede systemctl VAR — 'ölçülemedi' yolu sınanamaz")
    r = sikistir("--dosya", str(p), "--kirp")
    assert r.returncode == 5, r.stdout + r.stderr
    assert "ÖLÇÜLEMEDİ" in r.stderr, r.stderr


def shutil_which_systemctl() -> bool:
    import shutil
    return shutil.which("systemctl") is not None


def test_zorla_worker_aktifken_bile_kirpmaya_izin_verir(tmp_path, monkeypatch):
    p = _defter_yaz(tmp_path)
    assert sikistir("--dosya", str(p)).returncode == 0
    monkeypatch.setenv(WORKER_ENV, "1")
    r = sikistir("--dosya", str(p), "--kirp", "--zorla")
    assert r.returncode == 0, r.stdout + r.stderr
    assert ESKI not in _aylar_jsonlde(p)
