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
      `test_isim_kumesi_BES_ve_CIKIS_GUNLERI_dogru` kırmızı.
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
"""SENTETİK Alpaca ikamesi (v488) — ağ YOK, disk defteri VAR."""
import datetime as _dt
import json as _json
import os as _os

DEFTER = _os.environ["SAHTE_ALPACA_DEFTER"]


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
}


def daily_bars(symbols, start, end, **kw):
    with open(DEFTER, "a", encoding="utf-8") as f:
        f.write(_json.dumps({"symbols": list(symbols), "start": start, "end": end,
                             "kw": sorted(kw)}) + "\\n")
    sym = list(symbols)[0]
    if sym == "CCC":
        raise RuntimeError("sentetik veri ucu hatasi")
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
    """EDG-070 emsalinde `.`/`-` dönüşümü YOKTUR (ölçüldü); tek normalizasyon
    `alpaca.daily_bars` içindeki upper/strip'tir. Kayıt bunu BEYAN eder, uydurmaz."""
    _, rapor, _ = _kos_ve_oku(duzen)
    n = rapor["sozlesmeler"]["sembol_normalizasyonu"]
    assert n["uygulanan"] == "upper().strip()"
    assert n["nokta_tire_donusumu"] is None and n["nokta_tire_donusumu_neden"]
    assert {s["sembol"]: s["alpaca_anahtar"] for s in rapor["harita"]}["AAA"] == "AAA"
