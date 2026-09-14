"""v488 — EDG-2026-093 ADIM-0 EKSEN B (`research/olcumler/edg093_midcap_pit/adim0b_kapsama.py`)
bar KAPSAMA sondasının çivileri.

NUMARA TARAMASI (2026-09-14): `grep -rl v488 tests/ docs/ research/ ops/ meridian/` BOŞ döndü →
v488 SERBEST, taşıma gerekmedi (vNNN kimlik kuralı, CLAUDE.md §2).

NE ÇİVİLER — VE NEDEN SUBPROCESS. Betiğin sözleşmesi KOMUT SATIRIdır (CLAUDE.md §1), `main()`
değil; üstelik argparse MODÜL SEVİYESİNDE kurulur (stdin kipi şartı, v480 dersi) — modül olarak
ithal etmek pytest'in argv'siyle bir koşum tetiklerdi. Bu yüzden her çivi betiği GERÇEKTEN
stdin'den, kök dizinden (cwd="/") koşturur. Ham `exec_module` YOKTUR (v334).

AĞ YOK — SENTETİK BİR `meridian` PAKETİ. Sonda dalı `--repo` ile verilen kökü `sys.path`in
BAŞINA koyar; çiviler `--repo`ya sentetik bir `meridian/adapters/alpaca.py` taşıyan tmp ağacı
verir, böylece `daily_bars` çağrısı GERÇEK Alpaca'ya değil sentetik ikameye gider ve her çağrı
bir DEFTERE (JSONL) düşer — "hiç çağrılmadı" iddiası sayaçla ölçülür, varsayılmaz. Alt süreçlerin
ortamından PYTHONPATH SİLİNİR: gerçek depo kökü sızarsa sentetik paket sessizce kaybolurdu.

BEKLENEN SAYILAR ELLE HESAPLANDI (aşağıdaki `_BEKLENEN` şerhinde adım adım).

MUTASYON KANITI (bu dosyada KOŞMAZ, Rol-1'e raporla teslim edilir — CLAUDE.md §6):
  (a) barsız-çıkış tanımındaki 7 takvim günü sabiti 0'a çevrilince
      `test_barsiz_cikis_payi_YEDI_GUN_TOLERANSIYLA_YARIM` kırmızı (0,5 → 1,0),
  (b) çıkış günü hesabı bir gün kaydırılınca (`etkin[i+1]` → tarih+1)
      `test_isim_kumesi_BES_ve_CIKIS_GUNLERI_dogru` kırmızı,
  (c) TUR-2: sınıf-hisse dönüşümü kaldırılınca (`alpaca_anahtari` gövdesi ham sembolü döndürünce)
      `test_sinif_hisse_TIRE_sembolu_ALPACA_NOKTASINA_cevrilir` kırmızı,
  (d) TUR-2: soğuma sıfırlaması kaldırılınca `test_soguma_SIFIRLANIR_sonraki_semboller_CAGRILIR`
      kırmızı,
  (e) TUR-2: yeniden-sonda hedefi `bar_n is None` ile SÜZÜLMEYİNCE (tüm isimler yeniden
      sondalanınca) önceki ÖLÇÜLMÜŞ kayıt bu koşumunkiyle EZİLİR →
      `test_yalniz_olculemeyen_BIRLESIM_onceki_BASARILILARI_EZMEZ` kırmızı.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
BETIK = REPO / "research" / "olcumler" / "edg093_midcap_pit" / "adim0b_kapsama.py"
KART_ADI = "EDG-2026-093-midcap-pit-kohort-sagkalan-ust-sinir.yaml"

#: Sentetik kohort — 3 as-of satırı, 5 sembol, biri (EEE) 2. günde çıkıyor, biri (DDD) 3. günde.
#: Satır anlamı ÖLÇÜLDÜ (as-of: bir satır sonraki satıra kadar geçerli) ve betikte şerhli.
KOHORT_CSV = (
    "date,tickers\n"
    '2020-07-27,"AAA,BBB,CCC,DDD,EEE"\n'
    '2020-08-03,"AAA,BBB,CCC,DDD"\n'
    '2020-08-10,"AAA,BBB,CCC"\n'
)

#: Sentetik KART — eşiklerin gerçekten karttan okunduğunu (koda gömülmediğini) ölçmek için
#: gerçek kartın değerlerini (40 / 3) taşır; `sahte_repo_esik_7_11` fikstürü BAŞKA değerler verir.
SENTETIK_KART = (
    "# SENTETİK kart (v488 fikstürü) — gerçek kart bu ağaçta DEĞİL, yalnız eşik okuma çivisi için.\n"
    "card_id: EDG-2026-093\n"
    "esikler:\n"
    "  kapsanan_isim_alt: 40                 # EDG-018/070 ile AYNI\n"
    "  ortalama_bar_gecmisi_yil_alt: 3       # EDG-018/070 ile AYNI\n"
)

#: SENTETİK Alpaca ikamesi. GERÇEK AĞA ÇIKMAZ; her çağrıyı `SAHTE_ALPACA_DEFTER` dosyasına yazar.
#: Dönen bar sözlüğünün anahtarı ÖLÇÜLDÜ: gerçek `alpaca._to_bar` "date" üretir ("t" ham API
#: alanıdır ve bizim şemamıza girmez) — ikame de "date" yazar ki çivi gerçeğin biçimini ölçsün.
SAHTE_ALPACA = '''
"""SENTETİK Alpaca ikamesi (v488) — ağ YOK, disk defteri VAR.

SOĞUMA YÜZEYİ GERÇEĞİN İKİZİDİR (ölçüldü 2026-09-14, meridian/adapters/alpaca.py):
`daily_bars` önce `_data_cooled("bars:" + feed)` kapısına bakar ve soğumadaysa İSTEK ATMADAN
None döner; istek arızasında `_DATA_FAIL_AT`/`_DATA_COOLDOWN` (süreç-içi, 300 sn) yazılır.
Bu ikizde arıza sınıfı SEMBOL ADINDAN türer: TİRE taşıyan sınıf-hisse sembolü (`MOG-A`) ve
adında "400" geçen fikstür sembolü, gerçek uçtan ölçülen HTTP 400 gibi davranır (A1 olayı
2026-09-14 14:27:02Z `alpaca_data_failed status=400`); NOKTA biçimi (`MOG.A`) servis edilir.
"""
import datetime as _dt
import json as _json
import os as _os
import time as _time

DEFTER = _os.environ["SAHTE_ALPACA_DEFTER"]

DATA_FEED = "iex"
DATA_FAIL_COOLDOWN_S = 300.0
_DATA_FAIL_AT = {}
_DATA_COOLDOWN = {}


def _mono():
    return _time.monotonic()


def _data_cooled(key):
    at = _DATA_FAIL_AT.get(key)
    return at is not None and (_mono() - at) < _DATA_COOLDOWN.get(key, DATA_FAIL_COOLDOWN_S)


def _seri(n, son):
    """n ardışık TAKVİM günü, sonuncusu `son`. Sentetik: bar sayısı ile tarihlerin gerçekçi
    seans takvimine uyması gerekmez — ölçülen şey bar SAYISI ve İLK/SON tarihtir."""
    s = _dt.date.fromisoformat(son)
    return [{"date": (s - _dt.timedelta(days=n - 1 - i)).isoformat(), "close": 1.0 + i}
            for i in range(n)]


_CEVAP = {
    "AAA": _seri(504, "2026-09-01"),
    "BBB": _seri(756, "2026-09-01"),
    "EEE": _seri(252, "2020-07-30"),
    "DDD": [],
    "AA": _seri(1000, "2026-09-01"),
    "MP": _seri(300, "2026-09-01"),
    "BRK.B": _seri(400, "2026-09-01"),
    "MOG.A": _seri(252, "2026-09-01"),
}


def _dort_yuz(sym):
    """Gerçek uçta HTTP 400 alan sınıf: TİRE taşıyan sembol (ÖLÇÜLEN arıza) + adında 400 geçen
    fikstür sembolü. NOKTA taşıyan sınıf-hisse biçimi bu kapıdan GEÇMEZ — servis edilir."""
    return "-" in sym or "400" in sym


def daily_bars(symbols, start, end, **kw):
    key = "bars:" + DATA_FEED
    soguk = _data_cooled(key)
    with open(DEFTER, "a", encoding="utf-8") as f:
        f.write(_json.dumps({"symbols": list(symbols), "start": start, "end": end,
                             "kw": sorted(kw), "soguk": soguk}) + "\\n")
    if soguk:
        return None                      # gerçeğin soğuma kapısı: İSTEK ATILMAZ, None döner
    sym = list(symbols)[0]
    if sym == "CCC":
        raise RuntimeError("sentetik veri ucu hatasi")
    if _dort_yuz(sym):
        _DATA_FAIL_AT[key] = _mono()
        _DATA_COOLDOWN[key] = DATA_FAIL_COOLDOWN_S
        return None                      # gerçek: `_data_fail(...)` sonrası `return out or None`
    v = _CEVAP.get(sym)
    return {sym: v} if v else {}
'''

# ---------------------------------------------------------------------- ELLE HESAPLANMIŞ BEKLENEN
# İsim kümesi (pencerede en az bir gün listede olan HER sembol): AAA BBB CCC DDD EEE → 5.
# Çıkış günü = sembolün SON göründüğü satırın ERTESİ as-of değişimi:
#   EEE son kez 2020-07-27 satırında → çıkış 2020-08-03
#   DDD son kez 2020-08-03 satırında → çıkış 2020-08-10
#   AAA/BBB/CCC son satırda hâlâ üye  → çıkış YOK (None)
# Sonda (tamamı) sonuçları:
#   AAA 504 bar → 504/252 = 2,0 yıl   · BBB 756 bar → 3,0 yıl · EEE 252 bar → 1,0 yıl
#   CCC RuntimeError → bar_n None (hata alanı dolu)   · DDD boş cevap → bar_n 0 (ÖLÇÜLMÜŞ sıfır)
#   kapsanan_n (bar_n > 0) = 3 ; ortalama bar-geçmişi = (2,0 + 3,0 + 1,0) / 3 = 2,0 yıl
# Barsız-çıkış payı (tanım: bar YOK ya da son_bar < çıkış_günü − 7 takvim günü):
#   DDD → bar YOK → BARSIZ
#   EEE → son_bar 2020-07-30 ; çıkış 2020-08-03 ; eşik 2020-07-27 → 07-30 ≥ 07-27 → BARLI
#   pay = 1 / 2 = 0,5   (7 sabiti 0 olsaydı EEE de barsız olur, pay 1,0 olurdu → mutasyon (a))
_BEKLENEN_ISIM_N = 5
_BEKLENEN_CIKIS = {"AAA": None, "BBB": None, "CCC": None, "DDD": "2020-08-10", "EEE": "2020-08-03"}
_BEKLENEN_KAPSANAN_N = 3
_BEKLENEN_ORT_YIL = 2.0
_BEKLENEN_BARSIZ_PAY = 0.5
_BUGUN = "2026-09-14"


def _stdin_kos(*args: str, cwd: str = "/", defter: pathlib.Path | None = None):
    """Betiği stdin'den koşar. PYTHONPATH SİLİNİR (sentetik paket gerçeğe yenilmesin)."""
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    if defter is not None:
        env["SAHTE_ALPACA_DEFTER"] = str(defter)
    return subprocess.run([sys.executable, "-", *args], input=BETIK.read_bytes(), cwd=cwd,
                          capture_output=True, timeout=180, env=env)


def _sahte_repo(tmp_path: pathlib.Path, kart_metni: str = SENTETIK_KART) -> pathlib.Path:
    repo = tmp_path / "sahte_repo"
    (repo / "meridian" / "adapters").mkdir(parents=True)
    (repo / "meridian" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "meridian" / "adapters" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "meridian" / "adapters" / "alpaca.py").write_text(SAHTE_ALPACA, encoding="utf-8")
    (repo / "research" / "cards").mkdir(parents=True)
    (repo / "research" / "cards" / KART_ADI).write_text(kart_metni, encoding="utf-8")
    return repo


@pytest.fixture
def duzen(tmp_path):
    """(repo, kohort csv, çıktı dizini, çağrı defteri) — her çivi kendi tmp ağacında."""
    kohort = tmp_path / "sp400_uyelik_tarihi.csv"
    kohort.write_text(KOHORT_CSV, encoding="utf-8")
    cikti = tmp_path / "cikti"
    return _sahte_repo(tmp_path), kohort, cikti, tmp_path / "alpaca_cagrilari.jsonl"


def _kos_ve_oku(duzen, *ek: str):
    repo, kohort, cikti, defter = duzen
    r = _stdin_kos("--repo", str(repo), "--cikti", str(cikti), "--kohort", str(kohort),
                   "--bugun", _BUGUN, "--bekleme-sn", "0", *ek, defter=defter)
    assert r.returncode == 0, (r.returncode, r.stderr.decode()[-1500:])
    uretilen = sorted(cikti.glob("kapsama_haritasi_*.json"))
    assert len(uretilen) == 1, [p.name for p in uretilen]
    return r, json.loads(uretilen[0].read_text(encoding="utf-8")), defter


# =============================================================== A. STDIN KİPİ / KULLANIM HATASI
def test_stdin_kipi_kok_dizinden_help_KURULUR():
    r = _stdin_kos("--help")
    assert r.returncode == 0, r.stderr.decode()[-400:]
    cikti = r.stdout
    for bayrak in (b"--repo", b"--cikti", b"--kohort", b"--alpaca-sonda", b"--bekleme-sn",
                   b"--baslangic", b"--bugun"):
        assert bayrak in cikti, bayrak
    assert b"IndexError" not in r.stderr


def test_stdin_kipi_repo_verilmezse_KULLANIM_HATASI_cikis_2():
    r = _stdin_kos()
    assert r.returncode == 2 and b"--repo zorunlu" in r.stderr, (r.returncode, r.stderr.decode()[-400:])


def test_stdin_kipi_cikti_verilmezse_KULLANIM_HATASI_cikis_2(tmp_path):
    r = _stdin_kos("--repo", str(tmp_path))
    assert r.returncode == 2 and b"--cikti zorunlu" in r.stderr, (r.returncode, r.stderr.decode()[-400:])


# =================================================================== B. KOHORT OKUMA / ÇIKIŞ GÜNÜ
def test_isim_kumesi_BES_ve_CIKIS_GUNLERI_dogru(duzen):
    """MUTASYON HEDEFİ (b): çıkış günü = SON görülme satırının ERTESİ as-of değişimi.
    Bir gün kaydırılırsa 2020-08-03 → 2020-08-04 olur ve bu çivi kırmızıya döner."""
    _, rapor, _ = _kos_ve_oku(duzen)
    assert rapor["ozet"]["isim_n"] == _BEKLENEN_ISIM_N
    assert {s["sembol"]: s["cikis_gunu"] for s in rapor["harita"]} == _BEKLENEN_CIKIS


# ============================================================ C. SONDA 0 — AĞ ÇAĞRISI HİÇ YOK
def test_sonda_SIFIR_daily_bars_HIC_CAGRILMAZ_ve_harita_OLCULMEDI(duzen):
    _, rapor, defter = _kos_ve_oku(duzen)          # --alpaca-sonda varsayılanı 0
    assert not defter.exists(), defter.read_text(encoding="utf-8")[:400]
    assert rapor["ozet"]["sonda_cagrildi"] is False
    for s in rapor["harita"]:
        assert s["bar_n"] is None and s["neden"], s
        assert "ölçülmedi" in s["neden"]
    assert rapor["ozet"]["kapsanan_n"] is None and rapor["ozet"]["kapsanan_n_neden"]


def test_sonda_SIFIR_meridian_adapters_alpaca_ITHAL_bile_EDILMEZ(duzen):
    """Kuru koşumun sözleşmesi "çağrı yok"tan FAZLASIDIR: `meridian.adapters.alpaca` HİÇ İTHAL
    EDİLMEZ (ithal etmek httpx/secrets/config zincirini ayağa kaldırır — pytest dışı koşumun
    obs'a yaklaşmaması kuralının özü). Ölçüm: ikame modül ithal ANINDA `SAHTE_ALPACA_DEFTER`
    ortam değişkenini okur; o değişken VERİLMEZ. İthal olsaydı KeyError ile koşum düşerdi."""
    repo, kohort, cikti, _ = duzen
    r = _stdin_kos("--repo", str(repo), "--cikti", str(cikti), "--kohort", str(kohort),
                   "--bugun", _BUGUN, "--bekleme-sn", "0")          # defter=None → env YOK
    assert r.returncode == 0, (r.returncode, r.stderr.decode()[-800:])
    assert b"KeyError" not in r.stderr


# ================================================ D. SONDA -1 — KAPSAMA, ORTALAMA YIL, HATA, PAY
def test_sonda_TAMAMI_kapsanan_n_ve_ORTALAMA_YIL_elle_hesaplanmis(duzen):
    _, rapor, defter = _kos_ve_oku(duzen, "--alpaca-sonda", "-1")
    assert defter.exists()
    assert rapor["ozet"]["sonda_cagrildi"] is True
    assert rapor["ozet"]["sonda_n"] == 5
    assert rapor["ozet"]["kapsanan_n"] == _BEKLENEN_KAPSANAN_N
    assert rapor["ozet"]["ortalama_bar_gecmisi_yil"] == pytest.approx(_BEKLENEN_ORT_YIL)
    bar_n = {s["sembol"]: s["bar_n"] for s in rapor["harita"]}
    assert bar_n == {"AAA": 504, "BBB": 756, "CCC": None, "DDD": 0, "EEE": 252}


def test_hata_veren_sembol_NONE_ve_HATA_alani_KOSUM_dusmez(duzen):
    _, rapor, _ = _kos_ve_oku(duzen, "--alpaca-sonda", "-1")
    ccc = next(s for s in rapor["harita"] if s["sembol"] == "CCC")
    assert ccc["bar_n"] is None and ccc["bar_gecmisi_yil"] is None
    assert ccc["hata"] and ccc["hata"].startswith("RuntimeError: sentetik veri ucu hatasi")
    # ÖLÇÜLMÜŞ SIFIR ile BİLİNMİYOR aynı şey değildir (uydurma yasağı):
    ddd = next(s for s in rapor["harita"] if s["sembol"] == "DDD")
    assert ddd["bar_n"] == 0 and ddd["hata"] is None


def test_barsiz_cikis_payi_YEDI_GUN_TOLERANSIYLA_YARIM(duzen):
    """MUTASYON HEDEFİ (a): tolerans sabiti 7 → 0 olursa EEE de barsız sayılır, pay 1,0 olur."""
    _, rapor, _ = _kos_ve_oku(duzen, "--alpaca-sonda", "-1")
    y = rapor["ozet"]["yanlilik_gostergesi_tabani"]
    assert y["tolerans_gun"] == 7
    assert y["cikan_n"] == 2 and y["olculemeyen_n"] == 0
    assert sorted(y["barsiz_semboller"]) == ["DDD"]
    assert y["barsiz_cikis_payi"] == pytest.approx(_BEKLENEN_BARSIZ_PAY)


# ================================================================= E. ALPACA ÇAĞRI BİÇİMİ
def test_alpaca_CAGRI_BICIMI_sembol_basina_TEK_ve_pencere_2020_07_01(duzen):
    _, _, defter = _kos_ve_oku(duzen, "--alpaca-sonda", "-1")
    cagrilar = [json.loads(x) for x in defter.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(cagrilar) == 5                       # isim başına TEK çağrı (bekleme bu aralıkta)
    assert sorted(c["symbols"][0] for c in cagrilar) == ["AAA", "BBB", "CCC", "DDD", "EEE"]
    for c in cagrilar:
        assert len(c["symbols"]) == 1
        assert c["start"] == "2020-07-01" and c["end"] == _BUGUN
        assert c["kw"] == []                        # feed/adjustment daily_bars'ın KENDİ varsayılanı


def test_sonda_N_POZITIF_ilk_N_ismi_sorar(duzen):
    _, rapor, defter = _kos_ve_oku(duzen, "--alpaca-sonda", "2")
    cagrilar = [json.loads(x) for x in defter.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert [c["symbols"][0] for c in cagrilar] == ["AAA", "BBB"]
    assert rapor["ozet"]["sonda_n"] == 2 and rapor["ozet"]["orneklem_mi"] is True


# ================================================================= F. KAYIT: SHA256 · HÜKÜM · EŞİK
def test_json_girdi_SHA256_ve_HUKUM_YOK_satiri(duzen):
    import hashlib
    _, kohort, _, _ = duzen
    _, rapor, _ = _kos_ve_oku(duzen)
    assert rapor["hukum"] == "YOK — Rol-1"
    beklenen = hashlib.sha256(kohort.read_bytes()).hexdigest()
    assert rapor["girdi"]["kohort_csv_sha256"] == beklenen
    assert rapor["girdi"]["kohort_csv"] == str(kohort)
    assert rapor["yazim_beyani"] and rapor["okuyan"]


def test_esikler_KARTTAN_okunur_koda_GOMULU_degil(tmp_path):
    """Eşik değerleri kart dosyasından türetilir (tek-kaynak yasası). Sentetik kart 7/11 taşır;
    çıktı 40/3 yazıyorsa değerler koda gömülmüş demektir."""
    kohort = tmp_path / "k.csv"
    kohort.write_text(KOHORT_CSV, encoding="utf-8")
    repo = _sahte_repo(tmp_path, "esikler:\n  kapsanan_isim_alt: 7\n"
                                 "  ortalama_bar_gecmisi_yil_alt: 11\n")
    cikti = tmp_path / "c"
    r = _stdin_kos("--repo", str(repo), "--cikti", str(cikti), "--kohort", str(kohort),
                   "--bugun", _BUGUN, "--bekleme-sn", "0")
    assert r.returncode == 0, r.stderr.decode()[-800:]
    rapor = json.loads(sorted(cikti.glob("kapsama_haritasi_*.json"))[0].read_text(encoding="utf-8"))
    e = rapor["ozet"]["esik_kiyasi"]
    assert e["kapsanan_isim_alt"] == 7 and e["ortalama_bar_gecmisi_yil_alt"] == 11
    assert e["hukum"] == "YOK — kıyas satırı; hüküm Rol-1'in"


def test_kart_YOKSA_esik_NONE_ve_NEDEN_kosum_dusmez(tmp_path):
    kohort = tmp_path / "k.csv"
    kohort.write_text(KOHORT_CSV, encoding="utf-8")
    repo = tmp_path / "kartsiz_repo"
    repo.mkdir()
    cikti = tmp_path / "c"
    r = _stdin_kos("--repo", str(repo), "--cikti", str(cikti), "--kohort", str(kohort),
                   "--bugun", _BUGUN, "--bekleme-sn", "0")
    assert r.returncode == 0, r.stderr.decode()[-800:]
    rapor = json.loads(sorted(cikti.glob("kapsama_haritasi_*.json"))[0].read_text(encoding="utf-8"))
    e = rapor["ozet"]["esik_kiyasi"]
    assert e["kapsanan_isim_alt"] is None and e["kapsanan_isim_alt_neden"]


# ================================================================= G. GİRDİ SÖZLEŞMESİ SAVUNMASI
def test_baslik_YANLISSA_kullanim_hatasi(tmp_path):
    kohort = tmp_path / "k.csv"
    kohort.write_text("gun,semboller\n2020-07-27,AAA\n", encoding="utf-8")
    r = _stdin_kos("--repo", str(tmp_path), "--cikti", str(tmp_path / "c"),
                   "--kohort", str(kohort), "--bugun", _BUGUN)
    assert r.returncode == 2 and b"date,tickers" in r.stderr, r.stderr.decode()[-400:]


def test_sembol_normalizasyonu_OLCULEN_bicimiyle_KAYDA_yazilir(duzen):
    """TUR-2: tur-1'de `nokta_tire_donusumu` None + neden ("ölçülmedi") idi; bu tur ÖLÇÜLDÜ ve
    kural yazıldı — kayıt artık kuralı VE kaynağını taşır, kaynak listesi BOŞ OLAMAZ."""
    _, rapor, _ = _kos_ve_oku(duzen)
    n = rapor["sozlesmeler"]["sembol_normalizasyonu"]
    assert n["uygulanan"] == "upper().strip() + sınıf-hisse tire→nokta dönüşümü"
    assert n["nokta_tire_donusumu"] and "MOG-A" in n["nokta_tire_donusumu"]
    assert n["nokta_tire_donusumu_neden"] is None
    assert isinstance(n["sembol_bicimi_kaynagi"], list) and n["sembol_bicimi_kaynagi"]
    assert {s["sembol"]: s["alpaca_anahtar"] for s in rapor["harita"]}["AAA"] == "AAA"


# =========================================================== H. SINIF-HİSSE SEMBOLÜ (TUR-2)
#: Tur-1'in ölçülen arızası: kohort defteri sınıf hissesini TİRE ile yazar (`MOG-A`), Alpaca
#: veri ucu NOKTA ister — tire biçimi HTTP 400 alır ve süreç-içi soğuma 298 ismi ölçülemez yapar
#: (A1 koşumu 2026-09-14 14:20–14:31Z). `TST-AB` deseni SINAR: kural yalnız TEK harflik sınıf
#: son ekine (`^[A-Z]+-[A-Z]$`) uygulanır, iki harfli son ek DÖNÜŞTÜRÜLMEZ.
KOHORT_SINIF_CSV = (
    "date,tickers\n"
    '2020-07-27,"AA,BRK-B,MOG-A,MP,TST-AB"\n'
)

#: Soğuma zehirlenmesi fikstürü: alfabetik olarak İLK gelen `A400` sentetik uçtan 400 alır ve
#: uç soğumaya girer; sonraki iki isim SIFIRLAMA olmadan HİÇ ölçülemezdi (tur-1 arızası).
KOHORT_SOGUMA_CSV = (
    "date,tickers\n"
    '2020-07-27,"A400,AAA,BBB"\n'
)

#: Ardışık-ölçülemeyen üst sınırı çivisi: 30 sembolün HEPSİ 400 alır. Sınır (25) aşılınca
#: sıfırlama DURUR — sağlayıcıyı dövmemek gerçeğin kendi kuralıdır (`alpaca._data_fail` şerhi).
_CAP_SEMBOLLER = [f"Z{i:02d}400" for i in range(30)]
KOHORT_CAP_CSV = "date,tickers\n" + '2020-07-27,"%s"\n' % ",".join(_CAP_SEMBOLLER)
_BEKLENEN_CAP_SINIRI = 25


def _duzen_ozel(tmp_path: pathlib.Path, kohort_metni: str):
    """`duzen` fikstürünün kohort metnini DIŞARIDAN alan ikizi (aynı tmp ağacı sözleşmesi)."""
    kohort = tmp_path / "sp400_uyelik_tarihi.csv"
    kohort.write_text(kohort_metni, encoding="utf-8")
    return (_sahte_repo(tmp_path), kohort, tmp_path / "cikti",
            tmp_path / "alpaca_cagrilari.jsonl")


def _cagrilar(defter: pathlib.Path) -> list[dict]:
    return [json.loads(x) for x in defter.read_text(encoding="utf-8").splitlines() if x.strip()]


def test_sinif_hisse_TIRE_sembolu_ALPACA_NOKTASINA_cevrilir(tmp_path):
    """MUTASYON HEDEFİ (c): dönüşüm kaldırılırsa `BRK-B`/`MOG-A` sentetik uca TİRE ile gider,
    400 alır ve bar_n None olur — bu çivi kırmızıya döner.

    ELLE HESAPLANMIŞ BEKLENEN: AA→AA (desen dışı) · BRK-B→BRK.B · MOG-A→MOG.A · MP→MP (desen
    dışı, tek harf ama tire YOK) · TST-AB→TST-AB (iki harflik son ek DESEN DIŞI → tire kalır →
    sentetik uçta 400 → bar_n None). Bar sayıları sentetik cevaptan: 1000/400/252/300/None."""
    duzen = _duzen_ozel(tmp_path, KOHORT_SINIF_CSV)
    _, rapor, defter = _kos_ve_oku(duzen, "--alpaca-sonda", "-1")
    anahtar = {s["sembol"]: s["alpaca_anahtar"] for s in rapor["harita"]}
    assert anahtar == {"AA": "AA", "BRK-B": "BRK.B", "MOG-A": "MOG.A", "MP": "MP",
                       "TST-AB": "TST-AB"}
    assert [c["symbols"][0] for c in _cagrilar(defter)] == ["AA", "BRK.B", "MOG.A", "MP", "TST-AB"]
    assert {s["sembol"]: s["bar_n"] for s in rapor["harita"]} == {
        "AA": 1000, "BRK-B": 400, "MOG-A": 252, "MP": 300, "TST-AB": None}
    d = rapor["sozlesmeler"]["sembol_normalizasyonu"]["sinif_hisse_donusumu"]
    assert d == {"BRK-B": "BRK.B", "MOG-A": "MOG.A"}      # desen DIŞI olanlar listede YOK


# ================================================= I. SOĞUMA ZEHİRLENMESİ / SIFIRLAMA (TUR-2)
def test_soguma_SIFIRLANIR_sonraki_semboller_CAGRILIR(tmp_path):
    """MUTASYON HEDEFİ (d): sıfırlama kaldırılırsa `A400`ün açtığı soğuma penceresi AAA ve
    BBB'yi de None yapar (tur-1'in 298 ismi) — bu çivi kırmızıya döner."""
    duzen = _duzen_ozel(tmp_path, KOHORT_SOGUMA_CSV)
    _, rapor, defter = _kos_ve_oku(duzen, "--alpaca-sonda", "-1")
    cagrilar = _cagrilar(defter)
    assert [c["symbols"][0] for c in cagrilar] == ["A400", "AAA", "BBB"]
    assert [c["soguk"] for c in cagrilar] == [False, False, False]   # her çağrı SICAK uca gitti
    assert {s["sembol"]: s["bar_n"] for s in rapor["harita"]} == {
        "A400": None, "AAA": 504, "BBB": 756}
    assert {s["sembol"]: s["soguma_aktif"] for s in rapor["harita"]} == {
        "A400": False, "AAA": False, "BBB": False}
    assert {s["sembol"]: s["soguma_yazildi"] for s in rapor["harita"]} == {
        "A400": True, "AAA": False, "BBB": False}       # soğumayı YAZAN sembol adıyla görünür
    s = rapor["ozet"]["soguma"]
    assert s["yuzey_olculdu"] is True and s["anahtar"] == "bars:iex"
    assert s["sifirlama_n"] == 1 and s["sifirlama_durdu"] is False


def test_soguma_ARDISIK_OLCULEMEYEN_UST_SINIRINDA_sifirlama_DURUR(tmp_path):
    """BEDEL YASASI: sıfırlama sınırsız olsaydı gerçekten düşmüş bir uç 661 kez dövülürdü
    (`alpaca._data_fail` şerhinin reddettiği şey). 30 sembolün hepsi 400 alır: ilk 25'i SICAK
    uca gider (sıfırlama), 26.'dan itibaren soğuma DURUR ve kayıt bunu ADIYLA söyler."""
    duzen = _duzen_ozel(tmp_path, KOHORT_CAP_CSV)
    _, rapor, defter = _kos_ve_oku(duzen, "--alpaca-sonda", "-1")
    aktif = [s["soguma_aktif"] for s in rapor["harita"]]
    assert aktif.count(False) == _BEKLENEN_CAP_SINIRI
    assert aktif.count(True) == len(_CAP_SEMBOLLER) - _BEKLENEN_CAP_SINIRI
    assert all(s["bar_n"] is None for s in rapor["harita"])
    soguk_kayit = [s for s in rapor["harita"] if s["soguma_aktif"]][0]
    assert "SOĞUMADA" in soguk_kayit["neden"]           # "veri yok" ile KARIŞMAZ
    s = rapor["ozet"]["soguma"]
    assert s["ust_sinir"] == _BEKLENEN_CAP_SINIRI
    assert s["sifirlama_n"] == _BEKLENEN_CAP_SINIRI - 1   # ilk sembolde silinecek kayıt YOKTU
    assert s["sifirlama_durdu"] is True
    assert [c["soguk"] for c in _cagrilar(defter)].count(True) == 5


# ======================================== K. --yalniz-olculemeyen: YENİDEN SONDA + BİRLEŞTİRME
# ELLE HESAPLANMIŞ BEKLENEN (aşağıdaki sahte önceki harita ile):
#   önceki: AAA 999 bar (ÖLÇÜLMÜŞ) · BBB None · CCC None · DDD 0 (ÖLÇÜLMÜŞ SIFIR) · EEE None
#   yeniden sondalanan = yalnız bar_n None olanlar → BBB, CCC, EEE  (AAA ve DDD ÇAĞRILMAZ)
#   bu koşum: BBB 756 · CCC RuntimeError → None · EEE 252
#   BİRLEŞİK bar_n: AAA 999 (KORUNDU) · BBB 756 · CCC None · DDD 0 · EEE 252
#   kapsanan_n = 3 (999, 756, 252) ; ort yıl = (999 + 756 + 252) / 252 / 3 = 2007/756
#   ölçülemeyen_n = 1 (CCC) ; barsız pay: DDD barsız, EEE barlı → 1/2 = 0,5
_ONCEKI_DAMGA = "20260101T000000Z"
_BEKLENEN_BIRLESIK_ORT_YIL = (999 + 756 + 252) / 252 / 3


def _onceki_json(tmp_path: pathlib.Path, kohort: pathlib.Path, sha: str | None = None):
    """Sahte ÖNCEKİ harita (tmp'de). Gerçek A1 çıktısının şemasından yalnız birleştirmenin
    okuduğu alanları taşır — çivi şemanın TAMAMINI değil, SÖZLEŞMEyi ölçer."""
    import hashlib
    kayit = {"AAA": {"bar_n": 999, "ilk_bar": "2019-01-02", "son_bar": "2026-09-01",
                     "bar_gecmisi_yil": 999 / 252, "hata": None, "neden": None},
             "BBB": {"bar_n": None, "ilk_bar": None, "son_bar": None, "bar_gecmisi_yil": None,
                     "hata": None, "neden": "daily_bars None döndü"},
             "CCC": {"bar_n": None, "ilk_bar": None, "son_bar": None, "bar_gecmisi_yil": None,
                     "hata": None, "neden": "daily_bars None döndü"},
             "DDD": {"bar_n": 0, "ilk_bar": None, "son_bar": None, "bar_gecmisi_yil": 0.0,
                     "hata": None, "neden": "satır taşımıyor"},
             "EEE": {"bar_n": None, "ilk_bar": None, "son_bar": None, "bar_gecmisi_yil": None,
                     "hata": None, "neden": "daily_bars None döndü"}}
    rapor = {"damga_utc": _ONCEKI_DAMGA,
             "girdi": {"kohort_csv": str(kohort),
                       "kohort_csv_sha256": sha or hashlib.sha256(kohort.read_bytes()).hexdigest()},
             "harita": [{"sembol": s, "alpaca_anahtar": s, "cikis_gunu": None, **k}
                        for s, k in kayit.items()]}
    yol = tmp_path / "onceki_kapsama_haritasi.json"
    yol.write_text(json.dumps(rapor, ensure_ascii=False), encoding="utf-8")
    return yol


def test_yalniz_olculemeyen_BIRLESIM_onceki_BASARILILARI_EZMEZ(duzen, tmp_path):
    """MUTASYON HEDEFİ (e): hedef süzgeci (`bar_n is None`) kalkarsa AAA yeniden sondalanır ve
    999 → 504 olur; DDD de yeniden sorulur. Bu çivi ikisini de kırmızıya çevirir."""
    _, kohort, _, defter = duzen
    onceki = _onceki_json(tmp_path, kohort)
    _, rapor, _ = _kos_ve_oku(duzen, "--alpaca-sonda", "-1", "--yalniz-olculemeyen", str(onceki))
    assert [c["symbols"][0] for c in _cagrilar(defter)] == ["BBB", "CCC", "EEE"]
    assert {s["sembol"]: s["bar_n"] for s in rapor["harita"]} == {
        "AAA": 999, "BBB": 756, "CCC": None, "DDD": 0, "EEE": 252}
    aaa = next(s for s in rapor["harita"] if s["sembol"] == "AAA")
    assert aaa["ilk_bar"] == "2019-01-02"               # önceki koşumun ölçümü AYNEN durdu
    assert rapor["birlesim_kaynagi"] == [_ONCEKI_DAMGA, rapor["damga_utc"]]
    b = rapor["birlesim"]
    assert b["yeniden_sondalanan_semboller"] == ["BBB", "CCC", "EEE"]
    assert b["oncekinden_devralinan_n"] == 2 and b["onceki_damga"] == _ONCEKI_DAMGA


def test_yalniz_olculemeyen_OZET_ve_YANLILIK_TABANI_BIRLESIK_harita_uzerinden(duzen, tmp_path):
    _, kohort, _, _ = duzen
    onceki = _onceki_json(tmp_path, kohort)
    _, rapor, _ = _kos_ve_oku(duzen, "--alpaca-sonda", "-1", "--yalniz-olculemeyen", str(onceki))
    o = rapor["ozet"]
    assert o["sonda_n"] == 3 and o["isim_n"] == _BEKLENEN_ISIM_N
    assert o["kapsanan_n"] == 3 and o["olculemeyen_n"] == 1
    assert o["ortalama_bar_gecmisi_yil"] == pytest.approx(_BEKLENEN_BIRLESIK_ORT_YIL)
    y = o["yanlilik_gostergesi_tabani"]
    assert sorted(y["barsiz_semboller"]) == ["DDD"] and y["olculemeyen_n"] == 0
    assert y["barsiz_cikis_payi"] == pytest.approx(_BEKLENEN_BARSIZ_PAY)


def test_yalniz_olculemeyen_CSV_SHA_UYUSMAZSA_kullanim_hatasi_cikis_2(duzen, tmp_path):
    """Kohort değiştiyse birleştirme İKİ FARKLI evreni tek haritada karıştırırdı — durur."""
    repo, kohort, cikti, defter = duzen
    onceki = _onceki_json(tmp_path, kohort, sha="0" * 64)
    r = _stdin_kos("--repo", str(repo), "--cikti", str(cikti), "--kohort", str(kohort),
                   "--bugun", _BUGUN, "--bekleme-sn", "0", "--alpaca-sonda", "-1",
                   "--yalniz-olculemeyen", str(onceki), defter=defter)
    assert r.returncode == 2, (r.returncode, r.stdout.decode()[-400:])
    assert b"sha256" in r.stderr and onceki.name.encode() in r.stderr, r.stderr.decode()[-400:]
    assert not defter.exists()                      # sha kapısı ÇAĞRIDAN ÖNCE kapanır


def test_yalniz_olculemeyen_SONDA_SIFIR_ile_kullanim_hatasi_cikis_2(duzen, tmp_path):
    """Çağrısız yeniden-sonda sessiz bir NO-OP olurdu (harita yeniden yazılır, ölçüm yok)."""
    repo, kohort, cikti, _ = duzen
    onceki = _onceki_json(tmp_path, kohort)
    r = _stdin_kos("--repo", str(repo), "--cikti", str(cikti), "--kohort", str(kohort),
                   "--bugun", _BUGUN, "--bekleme-sn", "0", "--yalniz-olculemeyen", str(onceki))
    assert r.returncode == 2, (r.returncode, r.stderr.decode()[-400:])
    assert b"yeniden sonda" in r.stderr, r.stderr.decode()[-400:]


def test_yalniz_olculemeyen_DOSYA_YOKSA_kullanim_hatasi_cikis_2(duzen, tmp_path):
    repo, kohort, cikti, _ = duzen
    r = _stdin_kos("--repo", str(repo), "--cikti", str(cikti), "--kohort", str(kohort),
                   "--bugun", _BUGUN, "--bekleme-sn", "0", "--alpaca-sonda", "-1",
                   "--yalniz-olculemeyen", str(tmp_path / "yok.json"))
    assert r.returncode == 2, (r.returncode, r.stderr.decode()[-400:])
    assert b"okunamad" in r.stderr and b"yok.json" in r.stderr, r.stderr.decode()[-400:]


def test_BIRLESIM_YOKKEN_birlesim_kaynagi_TEK_damga(duzen):
    """Şema birleştirme olmadan da AYNI: alan var, listede tek damga (kopya sözleşme yok)."""
    _, rapor, _ = _kos_ve_oku(duzen, "--alpaca-sonda", "-1")
    assert rapor["birlesim_kaynagi"] == [rapor["damga_utc"]]
    assert rapor["birlesim"] is None and rapor["birlesim_neden"]
