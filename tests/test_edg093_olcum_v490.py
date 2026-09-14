"""tests/test_edg093_olcum_v490.py — EDG-2026-093 ANA ÖLÇÜM Parti-2 (`k093.py`) çivileri.

vNNN KİMLİK KAYDI: v490 seçildi çünkü ölçüm anında (2026-09-14)
`grep -rl v490 tests/ ops/ meridian/ research/ docs/` HİÇBİR eşleşme vermedi — `tests/` altında
v490 BOŞ; çakışma yok, taşıma yok (CLAUDE.md §2 vNNN kimlik kuralı).

NE ÇİVİLER. `research/olcumler/edg093_midcap_pit/k093.py`: EDG-016 tasarımının S&P 400 PIT
kohortu üzerinde koşan hâli. Ölçülen şey SAYININ KENDİSİ DEĞİL (o gerçek veriyle A1'de doğar),
SÖZLEŞMELERDİR:
  (1) PANEL AS-OF ÜYE GÜNLERLE SINIRLI — çıkış gününden SONRA satır YOK, girişten ÖNCE satır YOK;
  (2) turnover21/dilim/CI gövdesi k016'DAN İTHAL — `k093` kaynağında `def panel` YOKTUR ve
      sabitler k016/ortak ile BİREBİR aynıdır (ayrışma çivisi, tek-kaynak yasası);
  (3) PIT: hisse sayısı `filed` ile seçilir — `filed`ı gözlem gününden SONRA olan kayıt as-of
      okumasına GİRMEZ (`dosyalama_yok` hücreleri) ve sızıntı sayacı SIFIR;
  (4) `--belirsiz ikisi` İKİ koşum üretir ve `haric` koşumunda belirsiz isim ölçülen sembol
      listesinde YOKTUR;
  (5) barsız-çıkış payı ADIM-0 B haritasından OKUNUR, yeniden HESAPLANMAZ;
  (6) PK-1 girdisiz → `kosdu: false` beyanı; PK-3 iki yönlü; PK-4 sentetik olaylar panelde;
  (7) çıktı JSON'unda `hukum` "YOK — Rol-1" ve girdi sha'ları.

NEDEN SUBPROCESS. `k093.py`nin MODÜL DÜZEYİ TEMİZDİR (argparse `main()` içinde, G/Ç yok) —
yani ithal edilebilir. Yine de boru hattı ALT SÜREÇTE koşturulur: `k093` wp2 `ortak.py`yi
`sys.modules["ortak"]` adıyla kaydeder ve `meridian.config.STATE`i çıktı dizinine çevirir; bunu
pytest sürecinde yapmak komşu testlerin ortamını kirletirdi (emsal: v488/v489 aynı gerekçeyle
alt süreç kullanır). Saf sözleşme çivileri (kaynak taraması, sabit eşitliği) ithalle koşar.

SENTETİK VERİ — GERÇEK SEANS TAKVİMİYLE. Bar tarihleri `pandas_market_calendars` XNYS
seanslarından alınır; motorun takvim kapısı (`sanitize_bars`) seans olmayan tarihi DÜŞÜRÜR ve
uydurma bir takvimle kurulan fikstür sessizce yarım panel üretirdi. Seri uzunluğu `ortak.py`nin
`BAR_MIN_UZUNLUK`undan (252+60+5 = 317) ve kesit tabanı `MIN_KESIT`ten (50) TÜRETİLİR —
fikstür sabitleri koda GÖMÜLMEZ, üretici dosyadan okunur.

AĞ YOK: hiçbir çivi ağ çağrısı yapmaz; `k093` da yapmaz (Alpaca/SEC yolu bu betikte YOKTUR).

MUTASYON KANITI (bu dosyada KOŞMAZ, Rol-1'e raporla teslim edilir — CLAUDE.md §6):
  (a) üyelik süzgeci kaldırılınca (`D = D_ham`) `test_PANEL_CIKIS_GUNUNDEN_SONRA_SATIR_YOK`,
      `test_PANEL_GIRISTEN_ONCE_SATIR_YOK` ve `test_pk4_SENTETIK_OLAYLAR_PANELDE_YANSIR` kırmızı,
  (b) belirsiz süzgeci kaldırılınca (`dusur` daima boş) `test_BELIRSIZ_HARIC_KOSUMDA_ISIM_YOK`
      kırmızı,
  (c) as-of `filed` yerine `end` ile yapılınca `test_PIT_FILED_ONCESI_HUCRE_DOSYALAMA_YOK` kırmızı,
  (d) barsız-çıkış payı yeniden hesaplanınca (harita okunmayınca)
      `test_BARSIZ_CIKIS_PAYI_HARITADAN_OKUNUR` kırmızı.
"""
from __future__ import annotations

import datetime as dt
import gzip
import json
import os
import pathlib
import subprocess
import sys

import pytest

from tests.conftest import betikten_modul_yukle

REPO = pathlib.Path(__file__).resolve().parents[1]
OLCUM = REPO / "research" / "olcumler" / "edg093_midcap_pit"
K093 = OLCUM / "k093.py"
WP2 = REPO / "research" / "olcumler" / "wp2_olcum"

#: Fikstür ölçüleri ÜRETİCİ DOSYADAN türetilir (kopya sabit YOK — tek-kaynak yasası).
#: `BAR_MIN_UZUNLUK = TREND_TEMPLATE_WARMUP + 60 + 5` ve `MIN_KESIT` wp2 `ortak.py`dedir; ikisini
#: de kaynak metinden okumak yerine modülü yükleyip SORARIZ (v490 bu iki sayıya bağımlıdır).
_SEANS_PAYI = 200          # asgari seri uzunluğunun ÜSTÜNE eklenen kullanılabilir gün payı
_SEMBOL_PAYI = 5           # asgari kesitin ÜSTÜNE eklenen sembol payı (giren/çıkan/belirsiz için)

ENTRANT = "MZE"            # pencerede SONRADAN giren isim
EXITER = "MZX"             # pencerede ÇIKAN isim
PIT_SEM = "MZP"            # ilk dosyalaması pencere başından SONRA olan isim (PIT çivisi)
BELIRSIZ_SEM = "MZB"       # elle eşleme tablosunda `belirsiz` işaretli isim
OZEL = (ENTRANT, EXITER, PIT_SEM, BELIRSIZ_SEM)

#: Sentetik olayların as-of satırlarındaki yeri (seans indeksi). İkisi de ısınma penceresinin
#: İÇİNDE seçilir: panel satırı ısınmadan bağımsız doğar, yani çivi kesit eşiğine bağlı DEĞİLDİR.
GIRIS_I = 120
CIKIS_I = 330

#: `PIT_SEM`in İLK dosyalaması bu seans indeksindedir; ondan ÖNCEKİ hücreler `dosyalama_yok`.
GEC_DOSYALAMA_I = 30

#: `--kapsama` fikstüründeki pay. GERÇEKTE HESAPLANAMAZ bir değer bilerek seçildi: sentetik
#: kohortta çıkan tek isim vardır ve onun barı VARDIR, yani yeniden hesaplansaydı 0,0 çıkardı.
#: 0,4242 görünüyorsa değer HARİTADAN OKUNMUŞ demektir.
KAPSAMA_PAYI = 0.4242


# =================================================================================================
# FİKSTÜR
# =================================================================================================
def _ust_duzey_ifade(yol: pathlib.Path, ad: str):
    """`<ad> = <ifade>` atamasının AST düğümü. Hedef dosya ÇALIŞTIRILMAZ."""
    import ast
    for d in ast.parse(yol.read_text(encoding="utf-8"), str(yol)).body:
        if isinstance(d, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == ad for t in d.targets):
            return d.value
    raise AssertionError(f"üst-düzey `{ad}` ataması yok: {yol}")


def _sabit_coz(dugum, ns: dict):
    """Sabit + toplama + `<modül>.<ÜST_AD>` düğümlerini çözer. `eval` YOKTUR ve olmamalı:
    değerlendirilen şey BAŞKA bir dosyanın kaynağıdır."""
    import ast
    if isinstance(dugum, ast.Constant):
        return dugum.value
    if isinstance(dugum, (ast.Tuple, ast.List)):
        return [_sabit_coz(e, ns) for e in dugum.elts]
    if isinstance(dugum, ast.BinOp) and isinstance(dugum.op, ast.Add):
        return _sabit_coz(dugum.left, ns) + _sabit_coz(dugum.right, ns)
    if isinstance(dugum, ast.Attribute) and isinstance(dugum.value, ast.Name):
        return getattr(ns[dugum.value.id], dugum.attr)
    raise AssertionError(f"çözülemeyen sabit ifadesi: {ast.dump(dugum)}")


def _wp2_sabitleri():
    """wp2 `ortak.py`nin ölçü sabitleri — ÜRETİCİDEN, KAYNAK METİNDEN okunur.

    NEDEN MODÜL YÜKLENMİYOR (ölçüldü 2026-09-14): wp2 `ortak.py` MODÜL DÜZEYİNDE kendi
    dizininde `_cache/` ve `_state/` açar ve `meridian.config.STATE`i oraya çevirir. Pytest
    sürecinde yüklemek hem `git status`u kirletir (`_state/` .gitignore'lu DEĞİLDİR — ölçüldü)
    hem de komşu testlerin state yolunu oynatır. Sabitler zaten SABİTTİR: kaynaktan çözülür."""
    from meridian import indicators as ind
    bar_min = int(_sabit_coz(_ust_duzey_ifade(WP2 / "ortak.py", "BAR_MIN_UZUNLUK"), {"ind": ind}))
    min_kesit = int(_sabit_coz(_ust_duzey_ifade(WP2 / "ortak.py", "MIN_KESIT"), {}))
    return bar_min, min_kesit


def _sabit(yol: pathlib.Path, ad: str, ns: dict | None = None):
    return _sabit_coz(_ust_duzey_ifade(yol, ad), ns or {})


def _seanslar(n: int, son: str = "2026-09-01") -> list[str]:
    """Son `n` GERÇEK XNYS seansı (artan). Sentetik takvim KURULMAZ: motorun takvim kapısı
    seans olmayan tarihi düşürür ve fikstür sessizce yarım panel üretirdi."""
    import pandas_market_calendars as mcal
    bas = (dt.date.fromisoformat(son) - dt.timedelta(days=int(n * 2.2))).isoformat()
    gunler = [str(d.date()) for d in mcal.get_calendar("XNYS").valid_days(bas, son)]
    assert len(gunler) >= n, f"takvimden {n} seans çıkmadı ({len(gunler)})"
    return gunler[-n:]


def _bar_csv(sembol: str, seanslar: list[str], tohum: int) -> str:
    """Deterministik, YUMUŞAK seri. Günlük hareket ±%2 ile sınırlı: motorun 'düzeltilmemiş satır'
    karantinası (|hareket| > %35 + geri dönüş + hacim tutarsızlığı) TETİKLENMEMELİ, yoksa çivi
    kendi kurduğu tuzağa düşerdi. Hacim sembole göre DEĞİŞİR — turnover/rvol rütbeleri ancak
    böyle ayrışır ve dilimler anlamlı olur."""
    import random as _r
    rnd = _r.Random(tohum)
    sat = ["date,open,high,low,close,volume"]
    fiyat = 40.0 + (tohum % 37)
    hacim_taban = 300_000 + (tohum % 11) * 90_000
    for i, g in enumerate(seanslar):
        fiyat *= 1.0 + rnd.uniform(-0.02, 0.02)
        acilis = fiyat * (1.0 + rnd.uniform(-0.004, 0.004))
        yuksek = max(acilis, fiyat) * 1.004
        dusuk = min(acilis, fiyat) * 0.996
        hacim = int(hacim_taban * (1.0 + 0.6 * rnd.random()) * (1.0 + 0.3 * ((i % 17) / 17.0)))
        sat.append(f"{g},{acilis:.4f},{yuksek:.4f},{dusuk:.4f},{fiyat:.4f},{hacim}")
    return "\n".join(sat) + "\n"


def _shares_satirlari(sembol: str, seanslar: list[str], gec_dosyalama_i: int | None):
    """EDGAR şemasıyla `anlik` hisse-adedi satırları. `filed` HER SATIRDA VARDIR ve `end`den
    SONRADIR (gerçek dünyada da öyledir: değer `end` gününe aittir, `filed` gününde BİLİNİR olur).

    `gec_dosyalama_i` verilirse ilk dosyalama O SEANSA çekilir — pencere başı ile o gün arasındaki
    hücreler as-of okumasında `dosyalama_yok` olmalıdır. Mutasyon (`end` ile as-of) bu hücreleri
    doldurur ve çivi kırılır."""
    ilk = gec_dosyalama_i if gec_dosyalama_i is not None else 0
    n_dosyalama = 12
    adim = max((len(seanslar) - ilk - 1) // n_dosyalama, 1)
    out = []
    for k in range(n_dosyalama):
        i = min(ilk + k * adim, len(seanslar) - 1)
        filed = seanslar[i]
        bitis = (dt.date.fromisoformat(filed) - dt.timedelta(days=40)).isoformat()
        out.append({"symbol": sembol, "cik": 1000 + (hash(sembol) % 9000), "taxonomy": "dei",
                    "tag": "EntityCommonStockSharesOutstanding", "unit": "shares",
                    "start": "", "end": bitis, "filed": filed,
                    "val": 100_000_000 + k * 250_000, "form": "10-Q", "fy": filed[:4], "fp": "Q1",
                    "donem_gun": "", "donem_turu": "anlik", "accn": f"{sembol}-{k}",
                    "frame": ""})
    return out


@pytest.fixture(scope="module")
def sentetik(tmp_path_factory):
    """Sentetik depo girdileri + k093 KOŞUMU (bir kez). Dönen: (kok, sonuc_json, stdout)."""
    bar_min, min_kesit = _wp2_sabitleri()
    n_seans = bar_min + _SEANS_PAYI
    n_sembol = min_kesit + _SEMBOL_PAYI
    seanslar = _seanslar(n_seans)
    assert GIRIS_I < CIKIS_I < n_seans, "olay indeksleri seans penceresinin içinde olmalı"

    kok = tmp_path_factory.mktemp("edg093_v490")
    bars = kok / "bars"
    bars.mkdir()

    sade = [f"M{chr(65 + i // 26)}{chr(65 + i % 26)}" for i in range(n_sembol)]
    sade = [s for s in sade if s not in OZEL][:n_sembol - len(OZEL)]
    semboller = sade + list(OZEL)
    assert len(set(semboller)) == len(semboller) >= min_kesit + 1

    for i, s in enumerate(semboller):
        (bars / f"{s.lower()}.csv").write_text(_bar_csv(s, seanslar, 7000 + i), encoding="utf-8")

    # --- shares csv.gz (EDGAR şeması, `filed` zorunlu) ---
    kolonlar = ["symbol", "cik", "taxonomy", "tag", "unit", "start", "end", "filed", "val",
                "form", "fy", "fp", "donem_gun", "donem_turu", "accn", "frame"]
    satirlar = []
    for s in semboller:
        satirlar += _shares_satirlari(s, seanslar, GEC_DOSYALAMA_I if s == PIT_SEM else None)
    shares = kok / "shares_sentetik.csv.gz"
    with gzip.open(shares, "wt", encoding="utf-8", newline="") as fh:
        fh.write(",".join(kolonlar) + "\n")
        for r in satirlar:
            fh.write(",".join(str(r[k]) for k in kolonlar) + "\n")

    # --- kohort csv: üç as-of satırı (adım fonksiyonu) ---
    taban = [s for s in semboller if s != ENTRANT]
    giris_sonrasi = list(semboller)
    cikis_sonrasi = [s for s in semboller if s != EXITER]
    kohort = kok / "kohort_sentetik.csv"
    kohort.write_text(
        "date,tickers\n"
        f'{seanslar[0]},"{",".join(sorted(taban))}"\n'
        f'{seanslar[GIRIS_I]},"{",".join(sorted(giris_sonrasi))}"\n'
        f'{seanslar[CIKIS_I]},"{",".join(sorted(cikis_sonrasi))}"\n', encoding="utf-8")

    # --- kart (pencere başı BURADAN türetilir) ---
    kart = kok / "kart_sentetik.yaml"
    kart.write_text("card_id: EDG-2026-093\n"
                    f'veri_penceresi: "{seanslar[0]} (sentetik) → ölçüm günü"\n', encoding="utf-8")

    # --- EDG-092 kartı: PK-4 olay kümesi (BOŞ liste OLAMAZ; boşsa ayrıştırıcı EDG-075'in
    #     GERÇEK olay kümesine düşer ve çivi sentetik değil canlı veriyi ölçerdi) ---
    kart092 = kok / "kart092_sentetik.yaml"
    kart092.write_text(
        "card_id: EDG-2026-092\n"
        "bilinen_olaylar:\n"
        f'  - {{sembol: "{ENTRANT}", yon: giris, tarih: "{seanslar[GIRIS_I]}", '
        'kaynak: "sentetik v490"}\n'
        f'  - {{sembol: "{EXITER}", yon: cikis, tarih: "{seanslar[CIKIS_I]}", '
        'kaynak: "sentetik v490"}\n', encoding="utf-8")

    # --- elle eşleme: BELIRSIZ_SEM `belirsiz` ---
    esleme = kok / "esleme_sentetik.yaml"
    esleme.write_text(
        "- satir:\n"
        f"    tarih: '{seanslar[GIRIS_I]}'\n"
        f"    eklenen: {BELIRSIZ_SEM}\n"
        "    cikan: null\n"
        "    etkisiz_semboller:\n"
        f"    - {BELIRSIZ_SEM}\n"
        "  karar: belirsiz\n"
        "  gerekce: sentetik v490 fikstürü\n", encoding="utf-8")

    # --- ADIM-0 B kapsama haritası (barsız-çıkış payı BURADAN OKUNUR) ---
    kapsama = kok / "kapsama_sentetik.json"
    kapsama.write_text(json.dumps({
        "kart": "EDG-2026-093", "damga_utc": "20260914T150444Z",
        "ozet": {"yanlilik_gostergesi_tabani": {
            "tanim": "sentetik v490 — bu sayı YENİDEN HESAPLANAMAZ, yalnız okunabilir",
            "tolerans_gun": 7, "cikan_n": 1, "barsiz_n": 1, "barli_n": 0,
            "barsiz_semboller": ["SENTETIK"], "barsiz_cikis_payi": KAPSAMA_PAYI,
            "barsiz_cikis_payi_neden": None}}}, ensure_ascii=False), encoding="utf-8")

    cikti = kok / "cikti"
    env = dict(os.environ, PYTHONPATH=str(REPO), PYTHONDONTWRITEBYTECODE="1")
    p = subprocess.run(
        [sys.executable, str(K093), "--repo", str(REPO), "--kohort", str(kohort),
         "--bars-dir", str(bars), "--shares", str(shares), "--cikti", str(cikti),
         "--kart", str(kart), "--kart092", str(kart092), "--esleme", str(esleme),
         "--kapsama", str(kapsama), "--bitis", seanslar[-1], "--belirsiz", "ikisi"],
        cwd=str(REPO), env=env, capture_output=True, text=True, timeout=1800)
    assert p.returncode == 0, f"k093 çıkış {p.returncode}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}"
    jsonlar = sorted(cikti.glob("sonuc_093_*.json"))
    assert len(jsonlar) == 1, f"tek sonuç json beklendi, bulunan: {jsonlar}"
    sonuc = json.loads(jsonlar[0].read_text(encoding="utf-8"))
    raporlar = sorted(cikti.glob("RAPOR_093_*.md"))
    assert len(raporlar) == 1, f"tek RAPOR beklendi, bulunan: {raporlar}"
    return {"kok": kok, "sonuc": sonuc, "stdout": p.stdout, "seanslar": seanslar,
            "semboller": semboller, "cikti": cikti, "rapor": raporlar[0],
            "bar_min": bar_min, "min_kesit": min_kesit,
            "girdiler": {"kohort": kohort, "bars": bars, "shares": shares, "kart": kart,
                         "kart092": kart092, "esleme": esleme, "kapsama": kapsama}}


@pytest.fixture(scope="module")
def pk1_kosumu(sentetik):
    """PK-1 KOLU AYRICA KOŞTURULUR — bu dal yalnız `--pk-*` verilince çalışır ve gerçek koşumda
    (A1) İLK KEZ oradaysa, "18 çivi yeşilken `--uygula` sessizce yok sayılıyordu" sınıfının ta
    kendisi olurdu (CLAUDE.md §6). Large-cap evreni olarak AYNI sentetik kohort verilir: ölçülen
    şey SAYI değil, PK-1 dalının koşması ve kıyas tablosunu kurmasıdır."""
    g = sentetik["girdiler"]
    kok = sentetik["kok"]
    ref = kok / "sonuc_016_sentetik.json"
    ref.write_text(json.dumps({"hukum_onerisi": {"bacaklar": {
        "i_ust20_evren_fazlasi": {h: {"ort": 0.0065, "anlamli": True} for h in ("10", "20")},
        "ii_a1_kova_tabanli_fazla": {h: {"ort": 0.0056, "anlamli": True} for h in ("10", "20")},
        "ii_b_artik_ic_fazla": {h: {"ic": 0.0284, "anlamli": True} for h in ("10", "20")},
    }}}, ensure_ascii=False), encoding="utf-8")
    cikti = kok / "cikti_pk1"
    env = dict(os.environ, PYTHONPATH=str(REPO), PYTHONDONTWRITEBYTECODE="1")
    p = subprocess.run(
        [sys.executable, str(K093), "--repo", str(REPO), "--kohort", str(g["kohort"]),
         "--bars-dir", str(g["bars"]), "--shares", str(g["shares"]), "--cikti", str(cikti),
         "--kart", str(g["kart"]), "--kart092", str(g["kart092"]), "--esleme", str(g["esleme"]),
         "--kapsama", str(g["kapsama"]), "--bitis", sentetik["seanslar"][-1],
         "--belirsiz", "dahil", "--sonuc016", str(ref),
         "--pk-kohort", str(g["kohort"]), "--pk-bars-dir", str(g["bars"]),
         "--pk-shares", str(g["shares"])],
        cwd=str(REPO), env=env, capture_output=True, text=True, timeout=1800)
    assert p.returncode == 0, f"k093 (PK-1) çıkış {p.returncode}\nSTDERR:\n{p.stderr}"
    return json.loads(sorted(cikti.glob("sonuc_093_*.json"))[-1].read_text(encoding="utf-8"))


# =================================================================================================
# A. KAYNAK SÖZLEŞMELERİ — ithalle koşar, alt süreç gerekmez
# =================================================================================================
def test_k093_KAYNAGINDA_def_panel_YOK_govde_k016dan_ITHAL():
    """Panel gövdesi k016'nındır. `k093` kendi `panel`ini tanımlarsa iki kopya doğar ve
    turnover21/özellik tanımları sessizce ayrışır (tek-kaynak yasası).

    ÖLÇÜM AST İLEDİR, METİN DEĞİL: düz `"def panel" in kaynak` taraması dosyanın KENDİ
    ŞERHİNİ (\"`def panel` YOKTUR\") yakalayıp kendi kendine kırmızı veriyordu — çivi
    tanımları ölçmeli, tanımdan söz eden düzyazıyı değil."""
    import ast
    agac = ast.parse(K093.read_text(encoding="utf-8"), str(K093))
    tanimlar = {d.name for d in ast.walk(agac)
                if isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert "panel" not in tanimlar, (
        "k093 kendi `panel` fonksiyonunu tanımlıyor — gövde k016'dan İTHAL EDİLMELİ")
    cagri = [n for n in ast.walk(agac)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
             and n.func.attr == "panel"]
    assert cagri, "k016.panel çağrısı yok — panel nereden geliyor?"


def test_k093_MODUL_DUZEYI_TEMIZ_ithal_kosum_tetiklemez():
    """Modül düzeyinde argparse/G/Ç YOKTUR: ithal etmek bir koşum tetiklemez. `parse_args`
    `main()` içindedir (emsalin tersi: veri_bar.py stdin kipi için modül düzeyinde kurar)."""
    mod = betikten_modul_yukle(K093, "v490_k093_modul")
    assert callable(mod.main) and mod.HUKUM == "YOK — Rol-1"
    assert not hasattr(mod, "ARGV"), "modül düzeyinde argparse sonucu var — ithal koşum tetikler"
    kaynak = K093.read_text(encoding="utf-8")
    ust_duzey = [s for s in kaynak.splitlines() if s.startswith("ARGV") or s.startswith("_ARGS")]
    assert not ust_duzey, f"modül düzeyi argparse kalıntısı: {ust_duzey}"


def test_k093_HAM_exec_module_KULLANMAZ_v334():
    """Yükleme `ops.sasi_yukleyici` üzerindendir: ham `exec_module` `__pycache__`e bakar ve
    boyut-koruyan bir düzenlemede BAYAT bytecode koşar (v334 sınıfı).

    DEDEKTÖR İTHAL EDİLİR, YENİDEN YAZILMAZ: v334'ün `_exec_module_cagrilari`si AST tabanlıdır
    ve çağrı ile çağrıdan SÖZ ETMEYİ ayırır (düz metin taraması bu dosyanın kendi şerhini
    suçluyordu — v334 başlığının anlattığı tuzağın aynısı)."""
    from tests.test_bayat_bytecode_v334 import _exec_module_cagrilari
    satirlar = _exec_module_cagrilari(K093.read_text(encoding="utf-8"))
    assert not satirlar, f"ham exec_module çağrısı (satır {satirlar}) — v334 §C envanteri öter"
    assert "kaynaktan_yukle" in K093.read_text(encoding="utf-8")


def test_SABITLER_k016_ve_ortaktan_TURETILIR_ayrisma_civisi(sentetik):
    """AYRIŞMA ÇİVİSİ: sonuçtaki `sabitler` bloğu k016/wp2-ortak'ın O ANKİ değerleriyle BİREBİR
    aynı olmalı. Kopya kaçınılmazsa türetme + ayrışma çivisi (CLAUDE.md §4).

    Değerler KAYNAK METİNDEN çözülür, modül YÜKLENMEZ (`_wp2_sabitleri` şerhi: yükleme
    `_state/` açar ve `config.STATE`i oynatır)."""
    from meridian import indicators as ind
    s = sentetik["sonuc"]["sabitler"]
    ortak_yolu, k016_yolu = WP2 / "ortak.py", WP2 / "k016.py"
    assert s["HORIZONS"] == _sabit(k016_yolu, "HORIZONS")
    assert s["UST_PCT"] == _sabit(k016_yolu, "UST_PCT")
    assert s["KONTROL_DILIM"] == _sabit(k016_yolu, "KONTROL_DILIM")
    assert s["KOVA_MIN"] == _sabit(k016_yolu, "KOVA_MIN")
    for ad in ("BLOCK", "BOOT", "BOOT_IC", "MIN_SLICE", "MIN_KESIT", "MALIYET_BPS", "BAYAT_GUN"):
        assert s[ad] == _sabit(ortak_yolu, ad), f"{ad} AYRIŞTI: {s[ad]}"
    assert s["BAR_MIN_UZUNLUK"] == int(_sabit(ortak_yolu, "BAR_MIN_UZUNLUK", {"ind": ind}))


# =================================================================================================
# B. PIT — AS-OF ÜYELİK SÜZGECİ (bu kartın EDG-016'dan TEK farkı)
# =================================================================================================
def test_PANEL_CIKIS_GUNUNDEN_SONRA_SATIR_YOK(sentetik):
    """ÇIKAN isim çıkış gününden İTİBAREN panelde OLMAMALI — barı olsa bile. Süzgeç kalkarsa
    aralık pencerenin sonuna kadar uzar ve ölçüm sağkalan evrenle koşar."""
    u = sentetik["sonuc"]["kosumlar"]["dahil"]["uyelik_suzgeci"]
    cikis_gunu = sentetik["seanslar"][CIKIS_I]
    ara = u["sembol_uye_gun_araligi"][EXITER]
    assert ara["son"] < cikis_gunu, (
        f"{EXITER} çıkış gününde ({cikis_gunu}) ya da sonrasında panelde: son={ara['son']}")
    assert ara["son"] == sentetik["seanslar"][CIKIS_I - 1]


def test_PANEL_GIRISTEN_ONCE_SATIR_YOK(sentetik):
    """GİREN isim giriş gününden ÖNCE panelde OLMAMALI — barı pencerenin başından beri var."""
    u = sentetik["sonuc"]["kosumlar"]["dahil"]["uyelik_suzgeci"]
    ara = u["sembol_uye_gun_araligi"][ENTRANT]
    assert ara["ilk"] == sentetik["seanslar"][GIRIS_I], (
        f"{ENTRANT} giriş gününden önce panelde: ilk={ara['ilk']}")


def test_UYELIK_SUZGECI_SATIR_DUSURUR_ve_sayisi_KAYITTA(sentetik):
    """Süzgecin ISIRDIĞI ölçülür: düşen satır sayısı, giren ismin girişten önceki günleri ile
    çıkan ismin çıkıştan sonraki günlerinin TOPLAMIdır."""
    u = sentetik["sonuc"]["kosumlar"]["dahil"]["uyelik_suzgeci"]
    n = len(sentetik["seanslar"])
    beklenen = GIRIS_I + (n - CIKIS_I)
    assert u["dusen_satir_uye_degil"] == beklenen, (
        f"düşen satır {u['dusen_satir_uye_degil']} ≠ beklenen {beklenen}")
    assert u["panel_satir_uye"] == u["panel_satir_suzgecten_once"] - beklenen


def test_PIT_FILED_ONCESI_HUCRE_DOSYALAMA_YOK(sentetik):
    """PIT ÇİVİSİ — as-of `filed` iledir, `end` ile DEĞİL.

    `PIT_SEM`in ilk dosyalaması `GEC_DOSYALAMA_I` seansındadır; ondan önceki her gözlem günü
    as-of okumasında `dosyalama_yok` üretmelidir. `end` ile as-of yapan bir mutasyonda o
    hücreler DOLARdı (her `end`, `filed`den 40 gün ÖNCEdir) ve sayı SIFIRA inerdi.

    ÖLÇÜLEN KALEM (k016 davranışı, DÜZELTİLMEDİ): `k016.panel` `dosyalama_yok`u İKİ KEZ sayar —
    bir kez `np.unique` döngüsünde, bir kez açık satırda. Sayı bu yüzden 2× beklenendir; bu bir
    ÖLÇÜMDÜR, çivi onu gizlemez (rapora da düşer)."""
    p = sentetik["sonuc"]["kosumlar"]["dahil"]["panel_muhasebesi"]["neden_sayimi"]
    assert p.get("dosyalama_yok") == 2 * GEC_DOSYALAMA_I, (
        f"dosyalama_yok={p.get('dosyalama_yok')} — beklenen {2 * GEC_DOSYALAMA_I} "
        f"(k016 çift sayar); `end` ile as-of yapılıyorsa bu sayı 0'a iner")


def test_PIT_SIZINTI_SAYACLARI_SIFIR(sentetik):
    """Seçilen as-of kaydının `filed`ı gözlem gününü ASLA aşamaz — hem ham panelde hem
    ölçüme giren üye satırlarda."""
    b = sentetik["sonuc"]["kosumlar"]["dahil"]["bekciler"]
    assert b["pit_sizinti_HAM_PANEL"]["ihlal_satir"] == 0
    assert b["pit_sizinti_HAM_PANEL"]["gecti"] is True
    assert b["pit_sizinti_OLCULEN_UYE_SATIRLAR"]["ihlal_satir"] == 0
    assert b["pit_sizinti_OLCULEN_UYE_SATIRLAR"]["gecti"] is True


# =================================================================================================
# C. KATMAN ŞEMASI — CI sözlükleri ve ölçülen büyüklükler
# =================================================================================================
def _ci_semasi(blok, alan="ci"):
    c = blok.get(alan)
    assert isinstance(c, dict), f"CI sözlüğü yok: {blok}"
    assert set(c) == {"lo", "hi", "seviye"}, f"CI anahtarları beklenmedik: {sorted(c)}"
    assert c["seviye"] == 0.95 and c["lo"] <= c["hi"]


def test_KATMAN_I_ve_II_CI_SOZLUKLERI_SEMAYA_UYAR(sentetik):
    """Katman i (kohort fazlası) ve katman ii (A1/A2/artık-IC) her ufukta CI taşımalı ve CI
    şeması `{lo, hi, seviye}` olmalı — hüküm bu sözlükten okunacak."""
    k = sentetik["sonuc"]["kosumlar"]["dahil"]
    assert k["DURUM"] == "OLCULDU", k.get("neden")
    for h in ("10", "20"):
        _ci_semasi(k["i_katman_turnover_ust20"]["ufuklar"][h]["evren_fazlasi"])
        ii = k["ii_katman_turnover_artik_rvol_mom_kontrollu"]
        _ci_semasi(ii["A1_kova_tabanli_ust20_fazlasi"]["ufuklar"][h]["loo_kova_fazlasi"])
        _ci_semasi(ii["A2_edg007_kova_ici_ust20_eksi_kalan"]["ufuklar"][h]["havuzlanmis"])
        _ci_semasi(ii["B_artik_ic"]["ufuklar"][h]["artik_ic_fazla"])


def test_BACAKLAR_OLGU_TASIR_ve_HUKUM_ONERISI_YOK(sentetik):
    """Ajan HÜKÜM YAZMAZ: `bacaklar` yalnız olgu (n/ort/ci/anlamlı) taşır; `oneri`,
    `success_metric`, `ARŞİV`/`SUCCESS` gibi hüküm sözcükleri çıktıda OLMAMALI."""
    s = sentetik["sonuc"]
    assert s["hukum"] == "YOK — Rol-1"
    assert "hukum_onerisi" not in s
    ham = json.dumps(s, ensure_ascii=False)
    for yasak in ("\"oneri\"", "SUCCESS —", "ARŞİV —", "success_metric_KARSILANDI"):
        assert yasak not in ham, f"çıktıda hüküm kalıntısı: {yasak}"
    b = s["kosumlar"]["dahil"]["bacaklar"]["i_ust20_kohort_fazlasi"]["20"]
    assert set(b) == {"n", "ort", "ci", "anlamli", "pozitif_anlamli", "negatif_anlamli"}
    assert isinstance(b["n"], int) and b["n"] > 0


def test_MALIYET_KATMANI_kart_modeli_ve_gidis_donus(sentetik):
    """Maliyet kartın modeliyle (tek yön 10 bps) düşülür; gidiş-dönüş BEYANLI duyarlılıktır ve
    net = brüt − maliyet cebirsel özdeşliği tutmalı."""
    m = sentetik["sonuc"]["kosumlar"]["dahil"]["iii_maliyet_sonrasi_net"]
    assert m["kart_modeli_tek_yon_bps"] == 10.0
    assert m["duyarlilik_gidis_donus_bps"] == 20.0
    n = m["ufuklar"]["20"]["katman1_evren_fazlasi"]["kart_modeli"]
    assert abs((n["brut"] - n["maliyet"]) - n["net"]) < 1e-9


def test_TANI_BES_LI_TABLO_ve_DOKUZ_KOVA(sentetik):
    """Tanı: 5'li turnover tablosu + 9 kontrol kovası + 10g ufku — üçü de K harcamaz."""
    k = sentetik["sonuc"]["kosumlar"]["dahil"]
    q5 = k["iv_tani"]["turnover_q5_kohort_fazlasi"]["ufuklar"]["20"]
    assert sorted(q5) == ["0", "1", "2", "3", "4"], f"5'li tablo değil: {sorted(q5)}"
    kovalar = k["ii_katman_turnover_artik_rvol_mom_kontrollu"][
        "A2_edg007_kova_ici_ust20_eksi_kalan"]["ufuklar"]["20"]["kovalar"]
    assert len(kovalar) == 9, f"9 kova beklendi, {len(kovalar)} bulundu"


# =================================================================================================
# D. BELİRSİZ-İSİM DUYARLILIĞI
# =================================================================================================
def test_BELIRSIZ_ISIMLER_ELLE_ESLEME_TABLOSUNDAN_TURETILIR(sentetik):
    """Belirsiz küme koda GÖMÜLMEZ: `karar: belirsiz` satırlarının `etkisiz_semboller` alanından
    türetilir ve kaynağı kayda yazılır."""
    em = sentetik["sonuc"]["evren_muhasebesi"]
    assert em["belirsiz_semboller"] == [BELIRSIZ_SEM]
    assert em["belirsiz_neden"] is None
    assert "etkisiz_semboller" in em["belirsiz_kaynak"]


def test_BELIRSIZ_IKISI_IKI_KOSUM_URETIR(sentetik):
    """`--belirsiz ikisi` İKİ koşum üretir; BİRİNCİL `dahil`dir (kohort defteri AYNEN)."""
    k = sentetik["sonuc"]["kosumlar"]
    assert sorted(k) == ["dahil", "haric"]
    assert sentetik["sonuc"]["duyarlilik_belirsiz"]["birincil"] == "dahil"
    assert k["dahil"]["DURUM"] == k["haric"]["DURUM"] == "OLCULDU"


def test_BELIRSIZ_HARIC_KOSUMDA_ISIM_YOK(sentetik):
    """`haric` koşumunda belirsiz isim ölçülen sembol listesinde OLMAMALI; `dahil`de OLMALI.
    Süzgeç kalkarsa iki liste eşitlenir ve duyarlılık okuması anlamını kaybeder."""
    d = sentetik["sonuc"]["kosumlar"]["dahil"]["uyelik_suzgeci"]
    h = sentetik["sonuc"]["kosumlar"]["haric"]["uyelik_suzgeci"]
    assert BELIRSIZ_SEM in d["olculen_semboller"]
    assert BELIRSIZ_SEM not in h["olculen_semboller"], (
        f"{BELIRSIZ_SEM} `haric` koşumunda ölçülmüş — belirsiz süzgeci çalışmıyor")
    assert h["sembol_uye"] == d["sembol_uye"] - 1


def test_DUYARLILIK_KIYASI_DAHIL_VE_HARICI_YAN_YANA_VERIR(sentetik):
    """Duyarlılık tablosu katman i/ii sayılarını yan yana verir — Rol-1 damgayı bundan okur."""
    kiyas = sentetik["sonuc"]["duyarlilik_belirsiz"]["kiyas"]
    assert kiyas, "duyarlılık kıyası boş"
    bacaklar = {r["bacak"] for r in kiyas}
    assert {"i_ust20_kohort_fazlasi", "ii_a1_kova_tabanli_fazla", "ii_b_artik_ic_fazla"} <= bacaklar
    for r in kiyas:
        assert set(r) >= {"dahil_deger", "dahil_anlamli", "haric_deger", "haric_anlamli", "ufuk"}


# =================================================================================================
# E. YANLILIK GÖSTERGELERİ
# =================================================================================================
def test_HALA_LISTEDE_ORANI_OLCULUR(sentetik):
    """(a) göstergesi: son gün üye / pencere birleşimi. Sentetik kohortta tam olarak bir isim
    çıkmıştır, yani oran (n−1)/n olmalıdır."""
    g = sentetik["sonuc"]["yanlilik_gostergesi"]["a_hala_listede_orani"]
    n = len(sentetik["semboller"])
    assert g["birlesim_n"] == n and g["son_gun_uye_n"] == n - 1 and g["cikan_n"] == 1
    # `deger` kayda 6 haneye yuvarlanmış yazılır — tolerans o yuvarlamanındır
    assert abs(g["deger"] - (n - 1) / n) < 1e-6


def test_BARSIZ_CIKIS_PAYI_HARITADAN_OKUNUR(sentetik):
    """(b) göstergesi ADIM-0 B haritasından OKUNUR, yeniden HESAPLANMAZ. Fikstürdeki pay
    sentetik veriden TÜRETİLEMEZ (çıkan tek ismin barı vardır → hesaplansaydı 0,0 olurdu)."""
    b = sentetik["sonuc"]["yanlilik_gostergesi"]["b_barsiz_cikis_payi"]
    assert b["payi"] == KAPSAMA_PAYI, (
        f"barsız-çıkış payı {b['payi']} — haritadaki {KAPSAMA_PAYI} değil, yani YENİDEN "
        f"HESAPLANMIŞ olabilir")
    assert "YENİDEN HESAPLANMADI" in (b["kaynak"] or "")


def test_BAR_UZUNLUK_SUZGECININ_BEDELI_OLCULUR(sentetik):
    """(d) — kazanç ölçülüp bedel ölçülmezse körlük sessizdir: EDG-016 ile aynı asgari seri
    uzunluğu uygulandı, kaç ismin (ve kaç ÇIKAN ismin) düştüğü sayıyla durur."""
    d = sentetik["sonuc"]["yanlilik_gostergesi"]["d_bar_uzunluk_suzgecinin_bedeli"]
    assert set(d) >= {"kisa_dusen_n", "kisa_dusen_cikan_n", "bar_dosyasi_olmayan_n"}
    assert d["kisa_dusen_n"] == 0 and d["bar_dosyasi_olmayan_n"] == 0
    assert str(sentetik["bar_min"]) in d["tanim"]


def test_EVREN_MUHASEBESI_ISINMA_NOTU_ve_ETKIN_BASLANGIC(sentetik):
    """Isınma BEYANDIR (A1 ölçümü), etkin başlangıç ÖLÇÜMDÜR — ikisi AYNI piksele düşmez."""
    em = sentetik["sonuc"]["evren_muhasebesi"]
    assert "2020-07-27" in em["isinma_notu"] and "A1 ölçümü" in em["isinma_notu"]
    etkin = em["etkin_baslangic_olculen"]
    assert etkin is not None and em["etkin_baslangic_neden"] is None
    # ÖLÇÜLEN ISINMA: kesit ancak turnover21 (medyan-21g hacim), rvol20 ve mom21 TANIMLI
    # olduğunda kurulur — yani pencere başından ~21 SEANS sonra. `BAR_MIN_UZUNLUK` (317) bir
    # SERİ UZUNLUĞU süzgecidir, kesitin başladığı günü belirlemez; ikisini karıştırmak bu
    # çivinin ilk hâlinin hatasıydı (ölçüldü 2026-09-14).
    assert etkin > em["pencere_baslangic"]
    i = sentetik["seanslar"].index(etkin)
    assert 20 <= i <= 25, f"etkin başlangıç {etkin} seans indeksi {i} — ısınma ~21 seans olmalı"


# =================================================================================================
# F. POZİTİF KONTROLLER
# =================================================================================================
def test_pk1_GIRDISIZ_KOSMADI_BEYANI(sentetik):
    """`--pk-*` verilmedi → PK-1 KOŞMADI; sonuç UYDURULMAZ (None + neden)."""
    p = sentetik["sonuc"]["pk"]["pk1"]
    assert p["kosdu"] is False
    assert p["yon_esit"] is None and p["ci0_disi_esit"] is None
    assert "--pk-kohort" in p["neden"]


def test_pk1_GIRDILIYSE_KOSAR_ve_KIYAS_TABLOSU_KURAR(pk1_kosumu):
    """`--pk-*` verilince PK-1 KOŞAR: kıyas tablosu üç bacak × iki ufuk = 6 satır kurar ve her
    satır kendi yön/CI kıyasını taşır. Sayı EŞİTLİĞİ beklenmez — kartın istediği YÖN ve
    CI-0-dışılıktır (sentetik veride yön ayrışabilir; ölçülen şey DALIN KOŞMASIDIR)."""
    p = pk1_kosumu["pk"]["pk1"]
    assert p["kosdu"] is True, p.get("neden")
    assert p["neden"] is None
    assert p["kiyaslanan_bacak_n"] == 6, f"kıyas satırı {p['kiyaslanan_bacak_n']}"
    assert isinstance(p["yon_esit"], bool) and isinstance(p["ci0_disi_esit"], bool)
    for r in p["detay"]:
        assert set(r) >= {"bacak", "ufuk", "pk1_deger", "edg016_deger", "yon_esit",
                          "ci0_disi_esit"}
        assert r["edg016_deger"] is not None, "referans değeri okunamamış"


def test_pk1_TEK_KOSUM_KIPINDE_DUYARLILIK_KIYASI_BOS(pk1_kosumu):
    """`--belirsiz dahil` tek koşum üretir; duyarlılık kıyası o hâlde BOŞ kalır ve bu bir
    eksiklik değil BEYANdır (kıyas için iki koşum gerekir)."""
    assert sorted(pk1_kosumu["kosumlar"]) == ["dahil"]
    assert pk1_kosumu["duyarlilik_belirsiz"]["kiyas"] == []
    assert pk1_kosumu["duyarlilik_belirsiz"]["kip"] == "dahil"


def test_pk2_DOGRULAMA_TABLOSU_YIRMI_SATIR_ve_ELLE_OKUNABILIR(sentetik):
    """PK-2 tablosu Rol-1'in bar dosyasından ELLE doğrulayacağı alanları taşır; koşumun kendi
    iç tutarlılığı da ölçülür (fwd20 = close_t+20/close_t − 1)."""
    p = sentetik["sonuc"]["pk"]["pk2"]
    assert p["n"] == 20, f"PK-2 tablosu {p['n']} satır"
    assert p["ic_hepsi_tutarli"] is True, "fwd20 ile bar fiyatları AYRIŞIYOR"
    r = p["satirlar"][0]
    assert set(r) >= {"sembol", "t", "bar_dosyasi", "dilim_ust20_mu", "close_t",
                      "close_t_arti_20", "fwd20"}
    assert r["bar_dosyasi"].endswith(".csv")


def test_pk3_SENTETIK_ISIM_DUSURME_IKI_YONLU(sentetik):
    """PK-3 iki yönlüdür: hâlâ listede olanlardan düşürmek oranı DÜŞÜRÜR, çıkmışlardan düşürmek
    YÜKSELTİR. Tek yönlü bir sınav, oranı sabit döndüren hataya kör kalırdı."""
    p = sentetik["sonuc"]["pk"]["pk3"]
    assert p["kalanlardan_dusurulunce"]["gecti"] is True
    assert p["kalanlardan_dusurulunce"]["oran"] < p["taban_oran"]
    # sentetik kohortta çıkan isim TEK olduğu için çıkan havuzu 10'dan küçüktür — düşen sayı
    # havuzla sınırlanır ve yön yine YÜKSELİŞ olmalıdır
    assert p["cikanlardan_dusurulunce"]["gecti"] is True
    assert p["cikanlardan_dusurulunce"]["oran"] > p["taban_oran"]
    assert p["gecti"] is True


def test_pk4_SENTETIK_OLAYLAR_PANELDE_YANSIR(sentetik):
    """PK-4: sentetik giriş/çıkış olayları PANELDE t-1 yok / t var (ve tersi) olmalı. Üyelik
    süzgeci kalkarsa giriş olayı t-1'de de panelde görünür ve strict sayaç düşer."""
    p = sentetik["sonuc"]["pk"]["pk4"]
    assert p["ornek_n"] == 2, f"sentetik olay kümesi 2 olmalı (bulunan {p['ornek_n']})"
    assert p["olculemedi_n"] == 0, f"ölçülemeyen olay var: {p['detay']}"
    assert p["gecti_strict_n"] == 2, f"strict geçmeyen olay: {p['detay']}"
    d = {x["sembol"]: x for x in p["detay"]}
    assert d[ENTRANT]["t_1_panelde"] is False and d[ENTRANT]["t_panelde"] is True
    assert d[EXITER]["t_1_panelde"] is True and d[EXITER]["t_panelde"] is False


def test_pk4_OLAY_KUMESI_EDG092_AYRISTIRICISINDAN_GELIR(sentetik):
    """Olay kümesi EDG-092 `olc.py` ayrıştırıcısıyla okunur (kopya YOK) ve kaynağı kayda düşer."""
    meta = sentetik["sonuc"]["pk"]["olay_kumesi_meta"]
    assert meta["neden"] is None, meta["neden"]
    assert "olay_kumesi" in meta["kaynak"] and meta["olay_n"] == 2
    assert isinstance(meta["tohum"], int) and meta["ornek_n"] >= 2


# =================================================================================================
# G. ÇIKTI — künye, damga, yazım beyanı, yan etki
# =================================================================================================
def test_CIKTI_GIRDI_SHA_TASIR_ve_OLCULEMEYEN_NEDENI_YAZAR(sentetik):
    """Girdi damgası: var olan her girdi sha256 taşır; olmayan için sha UYDURULMAZ, neden yazılır."""
    g = sentetik["sonuc"]["girdi_damgasi"]
    for ad in ("kohort_csv", "shares_csv", "kart", "kart092", "elle_esleme",
               "kapsama_haritasi", "olcum_kodu", "k016", "wp2_ortak", "parti1_ortak"):
        assert g[ad]["sha256"] and len(g[ad]["sha256"]) == 64, f"{ad} sha yok: {g[ad]}"
        assert g[ad]["neden"] is None
    assert g["bars_dizin"]["sha256"] is None and g["bars_dizin"]["neden"]
    assert g["bars_manifest"]["sha256"] is None, "sentetik fikstürde manifest YOK"
    assert "dosya yok" in (g["bars_manifest"]["neden"] or "") or \
           "yol verilmedi" in (g["bars_manifest"]["neden"] or "")


def test_CIKTI_YALNIZ_CIKTI_DIZININE_YAZAR(sentetik):
    """Yazım beyanı ÖLÇÜLÜR: çıktı dizininde yalnız sonuç json'u, RAPOR ve `_state/` olmalı."""
    icerik = sorted(p.name for p in sentetik["cikti"].iterdir())
    for ad in icerik:
        assert ad.startswith(("sonuc_093_", "RAPOR_093_", "_state")), f"beklenmedik çıktı: {ad}"
    assert any(a.startswith("sonuc_093_") for a in icerik)
    assert any(a.startswith("RAPOR_093_") for a in icerik)


def test_ITHAL_YAN_ETKISI_OLCULUR_ve_GERI_ALINIR(sentetik):
    """wp2 ithali `_cache`/`_state` açar; koşum kendi açtığını siler ve hâli ADIYLA yazar.
    Bırakılsaydı Rol-1'in `git status --porcelain` kapısı (dağıtım ön şartı) kirlenirdi."""
    y = sentetik["sonuc"]["ithal_yan_etkisi"]
    assert set(y) == {"_cache", "_state"}
    for ad, v in y.items():
        assert "koşumdan_once_vardi" in v and "silindi" in v
        if v["koşumdan_once_vardi"] is False and v["silindi"] is False:
            assert v["neden"], f"{ad}: silinmedi ama neden yok"
    assert not (WP2 / "_state").exists() or y["_state"]["koşumdan_once_vardi"] is True


def test_COZULEN_YOLLAR_MERIDIAN_REPO_ICINDEN(sentetik):
    """Motor `--repo`dan yüklenmeli. wp2 `ortak.py` modül düzeyinde MUTLAK bir depo yolunu
    `sys.path`in başına koyar; sıra yanlış olsaydı worktree'den koşan ölçüm ANA CHECKOUT'un
    koduyla koşardı (hafıza: worktree-pythonpath-tuzagi)."""
    c = sentetik["sonuc"]["cozulen_yollar"]
    assert c["meridian_repo_icinde_mi"] is True, (
        f"meridian {c['meridian']} — beklenen kök {c['repo']}")
    assert c["config_state"].endswith("_state")


def test_RAPOR_TABLOLARI_ve_HUKUM_SATIRI(sentetik):
    """RAPOR okunabilir olmalı: hüküm satırı, katman tabloları, yanlılık ve PK bölümleri."""
    metin = sentetik["rapor"].read_text(encoding="utf-8")
    for parca in ("**Hüküm:** YOK — Rol-1", "## Girdi damgaları", "## Evren muhasebesi",
                  "### Katman I", "### Katman II", "### Katman III",
                  "## Yanlılık göstergeleri", "## Pozitif kontroller", "## K beyanı"):
        assert parca in metin, f"RAPOR'da eksik bölüm: {parca}"
    assert "SUCCESS" not in metin and "ARŞİV" not in metin, "RAPOR hüküm yazıyor"


def test_K_BEYANI_IKI_TRIAL_ve_DUYARLILIK_K_HARCAMAZ(sentetik):
    """K = 2 (kart `k_registry`); tanı ve yanlılık/duyarlılık BEYANdır, K'ye girmez."""
    satirlar = "\n".join(sentetik["sonuc"]["k_beyani"]["satirlar"])
    assert "K = 2" in satirlar
    assert "EDG-093-midcap-ust-dilim-fazlasi-20g" in satirlar
    assert "EDG-093-midcap-artik-katki-20g" in satirlar
    assert "K'ye GİRMEZ" in satirlar and "TANI" in satirlar


def test_DAMGA_UTC_ve_DOSYA_ADI_AYNI(sentetik):
    """Damga saatten okunur ve dosya adıyla AYNI olmalı — etiket ile dosya ayrışırsa hangi
    koşumun hangi sonucu ürettiği kaybolur (hafıza: saat-etiketi ölçülür)."""
    damga = sentetik["sonuc"]["damga_utc"]
    assert (sentetik["cikti"] / f"sonuc_093_{damga}.json").exists()
    assert (sentetik["cikti"] / f"RAPOR_093_{damga}.md").exists()
    assert len(damga) == 16 and damga.endswith("Z")
