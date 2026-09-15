"""tests/test_edg099_midcap_trend_v497.py — EDG-2026-099 mid-cap PIT trend kolu şasisi çivileri.

vNNN KİMLİK KAYDI: v497 seçildi çünkü ölçüm anında (2026-09-15)
`grep -rl v497 tests/ ops/ meridian/ research/ docs/` YALNIZ bu turda doğan `k099.py`yi
döndürdü — `tests/` altında v497 BOŞ; çakışma yok, taşıma yok (CLAUDE.md §2 vNNN kimlik kuralı).

NE ÇİVİLER. `research/olcumler/edg099_midcap_trend/k099.py`: EDG-2026-009'un C/D hücrelerinin
S&P 400 PIT kohortu üzerinde koşan hâli. Ölçülen şey SAYININ KENDİSİ DEĞİL (o gerçek veriyle
A1'de doğar), SÖZLEŞMELERDİR:
  (T1)  sinyal sabitleri `meridian.trend_shadow` ile BİREBİR (ayrışma çivisi),
  (T2)  12-1 momentum kart tanımı — üç isimde ELLE doğrulanır; üst-N seçim SIRASI,
  (T3)  BAKMA-İLERİ: karar günü `t` KAPANIŞI icra fiyatını DEĞİŞTİRMEZ, `t+1` AÇILIŞI değiştirir,
  (T4)  AS-OF ÜYELİK: üyelikten çıkan isim sonraki ay-sonunda satılır; girmemiş isim sepete girmez,
  (T5)  EW çıtası = o gün as-of ÜYELERİN ortalaması (üye olmayan isim çıtayı OYNATMAZ),
  (T6)  chandelier: çıkış günü doğru ve boşalan slot BİR SONRAKİ ay-sonunda doluyor,
  (T7)  eşikler ve kill-list metinleri KARTTAN (sayısal eşitlik, lafız birebir),
  (T8)  PK-1 alanları ve `gecti` mantığı (koşmayan PK "geçti" de "kaldı" da DEĞİLDİR),
  (T9)  ölçülemeyen isimler None+neden ile sayılır; aday eşiği altındaki ay payı,
  (T10) sinyal sabitleri KOPYALANMAMIŞ (kaynakta literal atama YOK) + canlı deftere yazan yol YOK,
  (T11) CLI: `--kart` YOKSA çıkış 2 (eşik uydurulmaz).

İKİ KOŞUM SINIFI. Saf fonksiyon çivileri (T2-T6, T8, T9 birimi) `k099`u İTHAL EDİP doğrudan
çağırır — modül düzeyi temizdir ve `meridian` ithal etmez. Boru hattı çivileri (T1, T7, T9
bütünü, T11) ALT SÜREÇTE koşar: `k099` wp2 `ortak.py`yi `sys.modules["ortak"]` adıyla kaydeder
ve `meridian.config.STATE`i çıktı dizinine çevirir; bunu pytest sürecinde yapmak komşu testlerin
ortamını kirletirdi (emsal: v488/v489/v490 aynı gerekçeyle alt süreç kullanır).

SENTETİK VERİ — GERÇEK SEANS TAKVİMİYLE. Bar tarihleri `pandas_market_calendars` XNYS
seanslarından alınır; motorun takvim kapısı (`sanitize_bars`) seans olmayan tarihi DÜŞÜRÜR ve
uydurma bir takvimle kurulan fikstür sessizce yarım panel üretirdi. Seri uzunluğu wp2
`ortak.BAR_MIN_UZUNLUK`tan TÜRETİLİR — fikstür sabiti koda GÖMÜLMEZ.

KART GERÇEKTİR, SENTETİK DEĞİL: `--kart` deponun KENDİ EDG-2026-099 kartını gösterir (pencere
`--baslangic`/`--bitis` ile sentetiğe çevrilir). Sentetik bir kartla koşmak, "eşikler karttan
okunuyor" iddiasını sentetik bir dosyaya karşı ölçerdi — yani hiçbir şey ölçmezdi.

AĞ YOK: hiçbir çivi ağ çağrısı yapmaz; `k099` da yapmaz (Alpaca/SEC yolu bu betikte YOKTUR).
CANLI DEFTERE DOKUNULMAZ: `trend_shadow.run_cycle`/`_kaydet` HİÇ çağrılmaz — T10 bunu AST ile ölçer.

MUTASYON KANITI (bu dosyada KOŞMAZ, Rol-1'e raporla teslim edilir — CLAUDE.md §6): rapor
`scratchpad/rapor_edg099_dilim.md` "Mutasyon tablosu" bölümündedir.
"""
from __future__ import annotations

import ast
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys

import pytest

from tests.conftest import betikten_modul_yukle

REPO = pathlib.Path(__file__).resolve().parents[1]
OLCUM = REPO / "research" / "olcumler" / "edg099_midcap_trend"
K099 = OLCUM / "k099.py"
KART = REPO / "research" / "cards" / "EDG-2026-099-midcap-pit-trend-kolu.yaml"
WP2 = REPO / "research" / "olcumler" / "wp2_olcum"

#: KARTIN ÖN-KAYITLI SAYILARI. Kart okunarak DA doğrulanır (aşağıda); bu demet bir ÖN-KAYIT
#: çapasıdır: eşik sonradan DEĞİŞMEZ (CLAUDE.md §5, "yeni eşik = yeni kart"), dolayısıyla kart
#: dosyasındaki sayı değişirse bu çivinin kırmızısı DOĞRU cevaptır.
KART_ESIKLERI = {"fazla_yillik_alt": 0.03, "t_alt": 2.0,
                 "ay_sonu_aday_alt": 30, "olculemeyen_ust_oran": 0.20}

#: Boru hattı fikstürünün ölçüleri. Ay-sonu sayısı `MOM_LOOKBACK` ısınmasının ÜSTÜNE en az 12
#: ölçüm ayı bırakmalı — yoksa blok-bootstrap (12 aylık blok) CI ÜRETEMEZ ve `ci0_disi` None
#: kalır, PK-1 hükmü de ölçülemez hâle gelirdi.
_SEANS_PAYI = 245          # wp2 BAR_MIN_UZUNLUK'un ÜSTÜNE eklenen seans payı (~26 ay toplam)
_SADE_SEMBOL = 34          # kart eşiği `ay_sonu_aday_alt` = 30'un ÜSTÜNDE aday kalsın

ENTRANT = "MZE"            # pencerede SONRADAN giren isim (EN YÜKSEK momentum)
EXITER = "MZX"             # pencerede ÇIKAN isim (ikinci en yüksek momentum)
BELIRSIZ_SEM = "MZB"       # elle eşleme tablosunda `belirsiz` (üçüncü en yüksek momentum)
NOBAR = "MZN"              # kohortta var, BAR DOSYASI YOK → ölçülemeyen
KISA = "MZK"               # bar dosyası BAR_MIN_UZUNLUK'tan kısa → ölçülemeyen
OZEL = (ENTRANT, EXITER, BELIRSIZ_SEM, NOBAR, KISA)

GIRIS_I = 400              # ENTRANT'ın as-of giriş satırı (ilk karar ay-sonundan SONRA)
CIKIS_I = 480              # EXITER'ın as-of çıkış satırı

#: `--kapsama` fikstüründeki pay. GERÇEKTE HESAPLANAMAZ bir değer bilerek seçildi (v490 deseni):
#: 0,4242 görünüyorsa değer HARİTADAN OKUNMUŞ demektir, yeniden hesaplanmış değil.
KAPSAMA_PAYI = 0.4242


# =================================================================================================
# ORTAK YARDIMCILAR
# =================================================================================================
@pytest.fixture(scope="module")
def k099():
    """`k099.py` modülü — KAYNAKTAN derlenir (`__pycache__`e bakılmaz, v334)."""
    return betikten_modul_yukle(K099, "k099_v497")


@pytest.fixture(scope="module")
def ts():
    """Canlı gölge-kitap modülü — SABİT ve SAF fonksiyon kaynağı. `run_cycle` ÇAĞRILMAZ."""
    from meridian import trend_shadow
    return trend_shadow


def _seanslar(n: int, son: str = "2026-09-01") -> list:
    """Son `n` GERÇEK XNYS seansı (artan). Sentetik takvim KURULMAZ: motorun takvim kapısı
    seans olmayan tarihi düşürür ve fikstür sessizce yarım panel üretirdi."""
    import pandas_market_calendars as mcal
    bas = (dt.date.fromisoformat(son) - dt.timedelta(days=int(n * 2.2))).isoformat()
    gunler = [str(d.date()) for d in mcal.get_calendar("XNYS").valid_days(bas, son)]
    assert len(gunler) >= n, f"takvimden {n} seans çıkmadı ({len(gunler)})"
    return gunler[-n:]


def _kare(gunler, kapanislar, acilis_carpani: float = 0.98):
    """Tarih-indeksli OHLCV karesi. AÇILIŞ KAPANIŞTAN FARKLIDIR ve olması ŞART: eşit olsaydı
    bakma-ileri çivisi (T3) iki fiyatı ayırt edemez, yanlış sebeple yeşil olurdu."""
    import pandas as pd
    o = [c * acilis_carpani for c in kapanislar]
    return pd.DataFrame({
        "date": [pd.Timestamp(g) for g in gunler],
        "open": o, "close": list(kapanislar),
        "high": [max(a, b) * 1.002 for a, b in zip(o, kapanislar)],
        "low": [min(a, b) * 0.998 for a, b in zip(o, kapanislar)],
        "volume": [1_000_000] * len(gunler),
    }).set_index("date").sort_index()


def _dunya(ts, k099mod, fiyatlar: dict, gunler: list):
    """Sentetik mini dünya: (master, per, dilim, atr, aylar, ay_sira, mpos).

    `per` NORMALİZE (tarih indeksli) verilir; `dilim`/`atr` canlı gölge-kitabın KENDİ
    fonksiyonlarıyla kurulur — çivi kendi panelini kurmaz (tek-kaynak)."""
    import pandas as pd
    per = {t: _kare(gunler, f) for t, f in fiyatlar.items()}
    master = pd.DatetimeIndex([pd.Timestamp(g) for g in gunler])
    dilim = ts._dilim(per, sorted(per), master)
    atr = {t: ts._atr(r) for t, r in dilim.items()}
    aylar, _ = k099mod.ay_sonlari(ts, gunler)
    return {"master": master, "per": per, "dilim": dilim, "atr": atr, "aylar": aylar,
            "ay_sira": {g: i for i, g in enumerate(aylar)},
            "mpos": {d: i for i, d in enumerate(master)}}


def _uyelik_sabit(gunler, semboller) -> dict:
    return {g: frozenset(semboller) for g in gunler}


def _kart_yaml() -> dict:
    import yaml
    return yaml.safe_load(KART.read_text(encoding="utf-8"))


# =================================================================================================
# BORU HATTI FİKSTÜRÜ — ALT SÜREÇ (bir kez)
# =================================================================================================
def _ust_duzey_ifade(yol: pathlib.Path, ad: str):
    """`<ad> = <ifade>` atamasının AST düğümü. Hedef dosya ÇALIŞTIRILMAZ."""
    for d in ast.parse(yol.read_text(encoding="utf-8"), str(yol)).body:
        if isinstance(d, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == ad for t in d.targets):
            return d.value
    raise AssertionError(f"üst-düzey `{ad}` ataması yok: {yol}")


def _sabit_coz(dugum, ns: dict):
    """Sabit + toplama + `<modül>.<ÜST_AD>` düğümlerini çözer. `eval` YOKTUR ve olmamalı:
    değerlendirilen şey BAŞKA bir dosyanın kaynağıdır."""
    if isinstance(dugum, ast.Constant):
        return dugum.value
    if isinstance(dugum, ast.BinOp) and isinstance(dugum.op, ast.Add):
        return _sabit_coz(dugum.left, ns) + _sabit_coz(dugum.right, ns)
    if isinstance(dugum, ast.Attribute) and isinstance(dugum.value, ast.Name):
        return getattr(ns[dugum.value.id], dugum.attr)
    raise AssertionError(f"çözülemeyen sabit ifadesi: {ast.dump(dugum)}")


def _bar_min_uzunluk() -> int:
    """wp2 `ortak.BAR_MIN_UZUNLUK` — ÜRETİCİDEN, KAYNAK METİNDEN (modül yüklenmez: modül
    düzeyinde kendi dizinine `_cache/`+`_state/` açar ve `git status`u kirletir, v490 D-notu)."""
    from meridian import indicators as ind
    return int(_sabit_coz(_ust_duzey_ifade(WP2 / "ortak.py", "BAR_MIN_UZUNLUK"), {"ind": ind}))


def _bar_csv(sembol: str, gunler: list, tohum: int, egim: float | None = None) -> str:
    """Deterministik seri. Günlük hareket ±%2 ile sınırlı: motorun 'düzeltilmemiş satır'
    karantinası (|hareket| > %35) TETİKLENMEMELİ, yoksa çivi kendi tuzağına düşerdi.

    `egim` verilirse seri MONOTON yükselir — momentum sıralamasının TEPESİNİ deterministik
    kılar; özel isimlerin (ENTRANT/EXITER/BELIRSIZ) sepete girmesi böyle garanti edilir ve
    üyelik çivisi (T4) boş yere yeşil kalmaz."""
    import random as _r
    rnd = _r.Random(tohum)
    sat = ["date,open,high,low,close,volume"]
    fiyat = 40.0 + (tohum % 37)
    for i, g in enumerate(gunler):
        fiyat *= (1.0 + egim) if egim is not None else (1.0 + rnd.uniform(-0.02, 0.02))
        acilis = fiyat * (1.0 + rnd.uniform(-0.004, 0.004))
        yuksek = max(acilis, fiyat) * 1.004
        dusuk = min(acilis, fiyat) * 0.996
        hacim = int(500_000 * (1.0 + 0.6 * rnd.random()))
        sat.append(f"{g},{acilis:.4f},{yuksek:.4f},{dusuk:.4f},{fiyat:.4f},{hacim}")
    return "\n".join(sat) + "\n"


def _girdileri_kur(kok: pathlib.Path) -> dict:
    """Sentetik kohort + barlar + eşleme + kapsama haritası. Kart GERÇEKTİR."""
    n_seans = _bar_min_uzunluk() + _SEANS_PAYI
    gunler = _seanslar(n_seans)
    assert GIRIS_I < CIKIS_I < n_seans, "olay indeksleri seans penceresinin içinde olmalı"

    bars = kok / "bars"
    bars.mkdir(parents=True)
    sade = [f"M{chr(65 + i // 26)}{chr(65 + i % 26)}" for i in range(_SADE_SEMBOL + len(OZEL))]
    sade = [s for s in sade if s not in OZEL][:_SADE_SEMBOL]
    semboller = sade + list(OZEL)
    assert len(set(semboller)) == len(semboller)

    for i, s in enumerate(sade):
        (bars / f"{s.lower()}.csv").write_text(_bar_csv(s, gunler, 7000 + i), encoding="utf-8")
    # ÖZEL İSİMLER: monoton eğimlerle momentum sırası DETERMİNİSTİK kılınır
    (bars / f"{ENTRANT.lower()}.csv").write_text(
        _bar_csv(ENTRANT, gunler, 11, egim=0.0075), encoding="utf-8")
    (bars / f"{EXITER.lower()}.csv").write_text(
        _bar_csv(EXITER, gunler, 12, egim=0.0060), encoding="utf-8")
    (bars / f"{BELIRSIZ_SEM.lower()}.csv").write_text(
        _bar_csv(BELIRSIZ_SEM, gunler, 13, egim=0.0045), encoding="utf-8")
    # KISA: BAR_MIN_UZUNLUK'un ALTINDA → `kisa` sayacına düşer. NOBAR: dosya HİÇ yok.
    (bars / f"{KISA.lower()}.csv").write_text(
        _bar_csv(KISA, gunler[-80:], 14), encoding="utf-8")

    taban = [s for s in semboller if s != ENTRANT]
    giris_sonrasi = list(semboller)
    cikis_sonrasi = [s for s in semboller if s != EXITER]
    kohort = kok / "kohort_sentetik.csv"
    kohort.write_text(
        "date,tickers\n"
        f'{gunler[0]},"{",".join(sorted(taban))}"\n'
        f'{gunler[GIRIS_I]},"{",".join(sorted(giris_sonrasi))}"\n'
        f'{gunler[CIKIS_I]},"{",".join(sorted(cikis_sonrasi))}"\n', encoding="utf-8")

    esleme = kok / "esleme_sentetik.yaml"
    esleme.write_text(
        "- satir:\n"
        f"    tarih: '{gunler[GIRIS_I]}'\n"
        f"    eklenen: {BELIRSIZ_SEM}\n"
        "    cikan: null\n"
        "    etkisiz_semboller:\n"
        f"    - {BELIRSIZ_SEM}\n"
        "  karar: belirsiz\n"
        "  gerekce: sentetik v497 fikstürü\n", encoding="utf-8")

    kapsama = kok / "kapsama_sentetik.json"
    kapsama.write_text(json.dumps({
        "kart": "EDG-2026-099", "damga_utc": "20260914T150444Z",
        "ozet": {"yanlilik_gostergesi_tabani": {
            "tanim": "sentetik v497 — bu sayı YENİDEN HESAPLANAMAZ, yalnız okunabilir",
            "tolerans_gun": 7, "cikan_n": 1, "barsiz_n": 1, "barli_n": 0,
            "barsiz_semboller": ["SENTETIK"], "barsiz_cikis_payi": KAPSAMA_PAYI,
            "barsiz_cikis_payi_neden": None}}}, ensure_ascii=False), encoding="utf-8")

    return {"gunler": gunler, "semboller": semboller, "bars": bars, "kohort": kohort,
            "esleme": esleme, "kapsama": kapsama}


@pytest.fixture(scope="module")
def boru(tmp_path_factory):
    """k099 KOŞUMU (bir kez, alt süreçte) — `--belirsiz ikisi` + PK-1 kolu AÇIK.

    PK-1 AYNI koşumda açılır: bu dal yalnız `--pk-*` verilince çalışır ve gerçek koşumda (A1)
    İLK KEZ oradaysa, "18 çivi yeşilken `--uygula` sessizce yok sayılıyordu" sınıfının ta
    kendisi olurdu (CLAUDE.md §6). Large-cap evreni olarak AYNI sentetik kohort verilir:
    ölçülen şey SAYI değil, PK-1 dalının KOŞMASI ve hüküm alanlarını kurmasıdır."""
    kok = tmp_path_factory.mktemp("edg099_v497")
    g = _girdileri_kur(kok)
    cikti = kok / "cikti"
    env = dict(os.environ, PYTHONPATH=str(REPO), PYTHONDONTWRITEBYTECODE="1")
    p = subprocess.run(
        [sys.executable, str(K099), "--repo", str(REPO), "--kohort", str(g["kohort"]),
         "--bars-dir", str(g["bars"]), "--kart", str(KART), "--cikti", str(cikti),
         "--baslangic", g["gunler"][0], "--bitis", g["gunler"][-1],
         "--esleme", str(g["esleme"]), "--kapsama", str(g["kapsama"]),
         "--belirsiz", "ikisi",
         "--pk-kohort", str(g["kohort"]), "--pk-bars-dir", str(g["bars"])],
        cwd=str(REPO), env=env, capture_output=True, text=True, timeout=2400)
    assert p.returncode == 0, f"k099 çıkış {p.returncode}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}"
    jsonlar = sorted(cikti.glob("sonuc_099_*.json"))
    assert len(jsonlar) == 1, f"tek sonuç json beklendi, bulunan: {jsonlar}"
    raporlar = sorted(cikti.glob("RAPOR_099_*.md"))
    assert len(raporlar) == 1, f"tek RAPOR beklendi, bulunan: {raporlar}"
    return {"kok": kok, "cikti": cikti, "girdi": g, "stdout": p.stdout,
            "sonuc": json.loads(jsonlar[0].read_text(encoding="utf-8")),
            "rapor": raporlar[0].read_text(encoding="utf-8")}


# =================================================================================================
# T1 — SABİTLER trend_shadow İLE BİREBİR (AYRIŞMA ÇİVİSİ)
# =================================================================================================
def test_T1_sabitler_trend_shadow_ile_BIREBIR(k099, ts):
    """`sabitler_kaydi` canlı gölge-kitabın sabitlerini AYNEN taşır — ikinci bir sürüm YOK."""
    s = k099.sabitler_kaydi(ts)
    assert s["MOM_LOOKBACK"] == ts.MOM_LOOKBACK
    assert s["N_SLOTS"] == ts.N_SLOTS
    assert s["FRICTION_BPS"] == ts.FRICTION_BPS
    assert s["ATR_LEN"] == ts.ATR_LEN
    assert s["CHANDELIER_K"] == ts.CHANDELIER_K
    assert s["DELIST_GRACE"] == ts.DELIST_GRACE
    assert s["INIT_EQUITY"] == ts.INIT_EQUITY


def test_T1_cikti_sabitleri_CANLI_MODULLE_AYNI(boru, ts):
    """Boru hattının YAZDIĞI sabitler de canlı modülle aynı — çıktı bayatlamaz."""
    s = boru["sonuc"]["sabitler"]
    for ad in ("MOM_LOOKBACK", "N_SLOTS", "FRICTION_BPS", "ATR_LEN", "CHANDELIER_K"):
        assert s[ad] == getattr(ts, ad), f"`{ad}` ayrıştı: çıktı {s[ad]} vs modül {getattr(ts, ad)}"


# =================================================================================================
# T2 — 12-1 MOMENTUM (ELLE) VE ÜST-N SEÇİM SIRASI
# =================================================================================================
@pytest.fixture(scope="module")
def mom_dunyasi(k099, ts):
    """Üç isim, ELLE kurulmuş ay-sonu kapanışları. ATR22 ısınması için 40 seans."""
    gunler = _seanslar(40)
    a12_i, a1_i, rd_i = 25, 35, 39
    fiyatlar = {}
    for ad, (p12, p1) in {"AAA": (100.0, 150.0), "BBB": (100.0, 120.0),
                          "CCC": (100.0, 90.0)}.items():
        seri = [100.0] * len(gunler)
        seri[a12_i] = p12
        seri[a1_i] = p1
        fiyatlar[ad] = seri
    d = _dunya(ts, k099, fiyatlar, gunler)
    d["a12"] = gunler[a12_i]
    d["a1"] = gunler[a1_i]
    d["rd"] = gunler[rd_i]
    return d


def test_T2_momentum_12_1_ELLE_DOGRULANIR(k099, mom_dunyasi):
    """12-1 = P(ay-sonu t-1) / P(ay-sonu t-12) − 1 — kartın tanımı, üç isimde elle."""
    d = mom_dunyasi
    rows = k099.momentum_satirlari(
        d["dilim"], ["AAA", "BBB", "CCC"], k099._ts(d["a1"]), k099._ts(d["a12"]),
        k099._ts(d["rd"]), d["atr"], d["per"])
    deger = dict(rows)
    assert deger["AAA"] == pytest.approx(0.50, abs=1e-12), "150/100 − 1 = 0,50"
    assert deger["BBB"] == pytest.approx(0.20, abs=1e-12), "120/100 − 1 = 0,20"
    assert deger["CCC"] == pytest.approx(-0.10, abs=1e-12), "90/100 − 1 = −0,10"


def test_T2_ust_N_SECIM_SIRASI(k099, mom_dunyasi):
    """Sıralama AZALAN momentumdur ve `ust_n` ilk N'i SIRAYLA verir (N=2)."""
    d = mom_dunyasi
    rows = k099.momentum_satirlari(
        d["dilim"], ["AAA", "BBB", "CCC"], k099._ts(d["a1"]), k099._ts(d["a12"]),
        k099._ts(d["rd"]), d["atr"], d["per"])
    assert [t for t, _ in rows] == ["AAA", "BBB", "CCC"]
    assert k099.ust_n(rows, 2) == ["AAA", "BBB"]
    assert k099.ust_n(rows, 0) == []


def test_T2_ADAY_OLMAYAN_SIRALAMAYA_GIRMEZ(k099, mom_dunyasi):
    """Çapası ÖLÇÜLEMEYEN isim satır üretmez — uydurma sıralama yerine SESSİZLİK."""
    d = mom_dunyasi
    yok = k099._ts(d["a1"]) + dt.timedelta(days=4000)      # indekste OLMAYAN çapa
    rows = k099.momentum_satirlari(
        d["dilim"], ["AAA", "BBB"], yok, k099._ts(d["a12"]), k099._ts(d["rd"]),
        d["atr"], d["per"])
    assert rows == []


# =================================================================================================
# T3 — BAKMA-İLERİ: KARAR GÜNÜ KAPANIŞI İCRA FİYATINI BELİRLEMEZ
# =================================================================================================
def test_T3_icra_fiyati_KARAR_GUNU_KAPANISINDAN_BAGIMSIZ(k099, ts):
    """`icra_fiyati` t+1 AÇILIŞINI verir; t kapanışı kaydırılınca fiyat DEĞİŞMEZ."""
    gunler = _seanslar(30)
    per = {"AAA": _kare(gunler, [100.0] * len(gunler))}
    rd, xd = k099._ts(gunler[-2]), k099._ts(gunler[-1])
    taban = k099.icra_fiyati(ts, per, "AAA", xd, rd)
    assert taban == pytest.approx(per["AAA"].at[xd, "open"])

    per["AAA"].at[rd, "close"] = 999.0                      # KARAR GÜNÜ KAPANIŞI kaydırıldı
    assert k099.icra_fiyati(ts, per, "AAA", xd, rd) == pytest.approx(taban), (
        "karar gününün kapanışı icra fiyatını DEĞİŞTİRDİ — bakma-ileri sızıntısı")

    per["AAA"].at[xd, "open"] = 123.5                       # İCRA GÜNÜ AÇILIŞI kaydırıldı
    assert k099.icra_fiyati(ts, per, "AAA", xd, rd) == pytest.approx(123.5)


def test_T3_icra_fiyati_ACILIS_YOKSA_SON_KAPANISA_DUSER(k099, ts):
    """Açılış yoksa şasinin yedeği: KARAR GÜNÜNÜN son bilinen kapanışı (fiyat UYDURULMAZ)."""
    gunler = _seanslar(30)
    per = {"AAA": _kare(gunler, [100.0] * len(gunler))}
    rd = k099._ts(gunler[-1])
    xd_yok = rd + dt.timedelta(days=30)                     # `per`de OLMAYAN seans
    assert k099.icra_fiyati(ts, per, "AAA", xd_yok, rd) == pytest.approx(100.0)
    assert k099.icra_fiyati(ts, per, "YOK", xd_yok, rd) is None


def _d_hucresi_kos(k099, ts, fiyatlar, gunler, *, n_slots=1, mom=2, fee=0.0):
    """Mini dünyada D hücresini koşar → (durum, defter)."""
    d = _dunya(ts, k099, fiyatlar, gunler)
    defter: list = []
    karar_fn, gunluk_fn = k099.hucre_kararcisi(
        ts, "D", aylar=d["aylar"], ay_sira=d["ay_sira"],
        uyelik=_uyelik_sabit(gunler, fiyatlar), dilim=d["dilim"], per=d["per"], atr=d["atr"],
        mpos=d["mpos"], n_slots=n_slots, chandelier_k=float(ts.CHANDELIER_K),
        mom_lookback=mom, defter=defter,
        dolu_kunye=k099.dolduruldu_kunyesi(ts, d["dilim"]))
    durum = k099.simule(ts, d["master"], d["per"], karar_fn, fee_bps=fee,
                        sermaye=float(ts.INIT_EQUITY), gunluk_fn=gunluk_fn)
    return durum, defter, d


def test_T3_SIMULASYON_giris_fiyati_t_arti_1_ACILISIDIR(k099, ts):
    """Boru hattı düzeyinde: ilk girişin fiyatı İCRA GÜNÜNÜN AÇILIŞIDIR.

    (a) karar günü kapanışı kaydırılınca giriş fiyatı DEĞİŞMEZ,
    (b) icra günü açılışı kaydırılınca DEĞİŞİR.
    İkisi birlikte ölçülmezse çivi "hiç fiyat kullanılmıyor" hâliyle de yeşil kalırdı."""
    gunler = _seanslar(150)
    taban_fiyat = {"AAA": [100.0 * (1.004 ** i) for i in range(len(gunler))],
                   "BBB": [100.0 * (1.001 ** i) for i in range(len(gunler))]}
    durum, defter, d = _d_hucresi_kos(k099, ts, taban_fiyat, gunler)
    assert defter, "hiç ay-sonu kararı alınmadı — fikstür kısa"
    ilk_karar = defter[0]["ay_sonu"]
    icra_gunu = gunler[gunler.index(ilk_karar) + 1]
    pozisyon = durum["pozisyon"] or {}
    giris = next(iter(pozisyon.values())) if pozisyon else durum["kapanan"][0]
    giris_px = giris.get("entry_price", giris.get("giris_px"))
    beklenen = float(d["per"]["AAA"].at[k099._ts(icra_gunu), "open"])
    assert giris_px == pytest.approx(beklenen, rel=1e-9), (
        "giriş fiyatı t+1 açılışı DEĞİL")

    # (a) KARAR GÜNÜ KAPANIŞI kaydırıldı → giriş fiyatı AYNI kalmalı
    kayik = {t: list(v) for t, v in taban_fiyat.items()}
    i_rd = gunler.index(ilk_karar)
    for t in kayik:
        kayik[t][i_rd] *= 1.30
    durum2, defter2, _ = _d_hucresi_kos(k099, ts, kayik, gunler)
    g2 = next(iter((durum2["pozisyon"] or {}).values()), None) or durum2["kapanan"][0]
    assert g2.get("entry_price", g2.get("giris_px")) == pytest.approx(beklenen, rel=1e-9), (
        "karar günü KAPANIŞI giriş fiyatını oynattı — bakma-ileri sızıntısı")

    # (b) İCRA GÜNÜ AÇILIŞI kaydırıldı → giriş fiyatı DEĞİŞMELİ
    d3 = _dunya(ts, k099, taban_fiyat, gunler)
    d3["per"]["AAA"].at[k099._ts(icra_gunu), "open"] = 4242.0
    defter3: list = []
    karar_fn, gunluk_fn = k099.hucre_kararcisi(
        ts, "D", aylar=d3["aylar"], ay_sira=d3["ay_sira"],
        uyelik=_uyelik_sabit(gunler, taban_fiyat), dilim=d3["dilim"], per=d3["per"],
        atr=d3["atr"], mpos=d3["mpos"], n_slots=1, chandelier_k=float(ts.CHANDELIER_K),
        mom_lookback=2, defter=defter3, dolu_kunye={})
    durum3 = k099.simule(ts, d3["master"], d3["per"], karar_fn, fee_bps=0.0,
                         sermaye=float(ts.INIT_EQUITY), gunluk_fn=gunluk_fn)
    g3 = next(iter((durum3["pozisyon"] or {}).values()), None) or durum3["kapanan"][0]
    assert g3.get("entry_price", g3.get("giris_px")) == pytest.approx(4242.0), (
        "icra günü AÇILIŞI giriş fiyatını oynatmadı — motor açılışı kullanmıyor olabilir")


# =================================================================================================
# T4 — AS-OF ÜYELİK
# =================================================================================================
@pytest.fixture(scope="module")
def uyelik_dunyasi(k099, ts):
    """Üç isim; `GEC` sonradan üye olur (EN YÜKSEK momentum), `CIK` ortada üyelikten düşer."""
    gunler = _seanslar(200)
    fiyatlar = {
        "GEC": [100.0 * (1.006 ** i) for i in range(len(gunler))],   # en yüksek momentum
        "CIK": [100.0 * (1.004 ** i) for i in range(len(gunler))],   # ikinci
        "KAL": [100.0 * (1.001 ** i) for i in range(len(gunler))],   # üçüncü
    }
    d = _dunya(ts, k099, fiyatlar, gunler)
    gec_i, cik_i = 120, 160
    uyelik = {}
    for i, g in enumerate(gunler):
        kume = {"KAL"}
        if i >= gec_i:
            kume.add("GEC")
        if i < cik_i:
            kume.add("CIK")
        uyelik[g] = frozenset(kume)
    d["uyelik"] = uyelik
    d["gunler"] = gunler
    d["gec_gun"] = gunler[gec_i]
    d["cik_gun"] = gunler[cik_i]
    d["fiyatlar"] = fiyatlar
    return d


def _c_hucresi(k099, ts, d, *, n_slots=1, mom=2, fee=0.0, hucre="C"):
    defter: list = []
    karar_fn, gunluk_fn = k099.hucre_kararcisi(
        ts, hucre, aylar=d["aylar"], ay_sira=d["ay_sira"], uyelik=d["uyelik"],
        dilim=d["dilim"], per=d["per"], atr=d["atr"], mpos=d["mpos"], n_slots=n_slots,
        chandelier_k=float(ts.CHANDELIER_K), mom_lookback=mom, defter=defter, dolu_kunye={})
    durum = k099.simule(ts, d["master"], d["per"], karar_fn, fee_bps=fee,
                        sermaye=float(ts.INIT_EQUITY), gunluk_fn=gunluk_fn)
    return durum, defter


def test_T4_UYE_OLMAYAN_ISIM_SEPETE_GIRMEZ(k099, ts, uyelik_dunyasi):
    """`GEC` en yüksek momentumlu isimdir ama ÜYE OLMADIĞI ay-sonlarında sepette YOKTUR.

    Çivi boş yere yeşil DEĞİL: üye olduktan SONRAKİ ay-sonlarında sepette OLDUĞU da ölçülür —
    yani süzgeç kaldırılırsa (mutasyon) ilk iddia kırılır, isim hiç seçilmiyorsa ikincisi."""
    _, defter = _c_hucresi(k099, ts, uyelik_dunyasi)
    onceki = [r for r in defter if r["ay_sonu"] < uyelik_dunyasi["gec_gun"]]
    sonraki = [r for r in defter if r["ay_sonu"] > uyelik_dunyasi["gec_gun"]]
    assert onceki and sonraki, "fikstür iki tarafı da kapsamalı"
    assert all("GEC" not in r["sepet"] for r in onceki), (
        "üye OLMAYAN isim sepete girdi — as-of süzgeci çalışmıyor")
    assert any("GEC" in r["sepet"] for r in sonraki), (
        "üye OLDUKTAN sonra da hiç seçilmedi — çivi boş yere yeşil olurdu")


def test_T4_UYELIKTEN_CIKAN_ISIM_SONRAKI_AY_SONUNDA_SATILIR(k099, ts, uyelik_dunyasi):
    """`CIK` üyelikten düşünce İLK ay-sonunda `uyelik` sebebiyle kapanır (icra ertesi açılış)."""
    durum, defter = _c_hucresi(k099, ts, uyelik_dunyasi, n_slots=2)
    assert any("CIK" in r["sepet"] for r in defter
               if r["ay_sonu"] < uyelik_dunyasi["cik_gun"]), "CIK hiç tutulmadı — fikstür zayıf"
    assert all("CIK" not in r["sepet"] for r in defter
               if r["ay_sonu"] >= uyelik_dunyasi["cik_gun"])
    uyelik_cikislari = [k for k in durum["kapanan"] if k["sebep"] == "uyelik" and k["sym"] == "CIK"]
    assert uyelik_cikislari, "üyelikten çıkan isim `uyelik` sebebiyle kapanmadı"
    ilk_ay_sonu = min(r["ay_sonu"] for r in defter if r["ay_sonu"] >= uyelik_dunyasi["cik_gun"])
    gunler = uyelik_dunyasi["gunler"]
    beklenen_icra = gunler[gunler.index(ilk_ay_sonu) + 1]
    assert uyelik_cikislari[0]["cikis"] == beklenen_icra, (
        "satış AY-SONUNUN ERTESİ SEANSINDA icra edilmedi")


# =================================================================================================
# T5 — EW ÇITASI = AS-OF ÜYELERİN ORTALAMASI
# =================================================================================================
def test_T5_EW_CITASI_AGIRLIKLARI_AS_OF_UYELERDE_ESIT(k099, ts, uyelik_dunyasi):
    """Çıtanın hedef ağırlıkları O GÜNÜN as-of üyeleri üzerinde 1/n'dir — üye olmayan yok."""
    d = uyelik_dunyasi
    defter: list = []
    karar_fn = k099.cita_kararcisi(
        ts, k099.CITA_ESLI, aylar=d["aylar"], ay_sira=d["ay_sira"], uyelik=d["uyelik"],
        per=d["per"], mpos=d["mpos"], mom_lookback=2, defter=defter)
    ilk = [g for g in d["aylar"] if d["ay_sira"][g] >= 2][0]
    durum = k099.yeni_durum(float(ts.INIT_EQUITY))
    karar = karar_fn(k099._ts(ilk), durum)
    uyeler = set(d["uyelik"][ilk])
    assert set(karar["hedef"]) == uyeler, "çıta sepeti as-of üye kümesi DEĞİL"
    assert all(w == pytest.approx(1.0 / len(uyeler)) for w in karar["hedef"].values())


def test_T5_EW_CITASI_GETIRISI_UYE_ORTALAMASIDIR(k099, ts):
    """İki üye + BİR ÜYE OLMAYAN isim. Sürtünmesiz çıtanın ay getirisi, üyelerin
    (kapanış(t+1 ay-sonu) / açılış(icra günü)) oranlarının ARİTMETİK ORTALAMASIDIR.

    Üye olmayan `DIS` kasten EN OYNAK seridir: süzgeç kaldırılırsa (mutasyon) ortalama
    kayar ve çivi kırılır."""
    gunler = _seanslar(200)
    fiyatlar = {
        "AAA": [100.0 * (1.002 ** i) for i in range(len(gunler))],
        "BBB": [100.0 * (0.999 ** i) for i in range(len(gunler))],
        "DIS": [100.0 * (1.010 ** i) for i in range(len(gunler))],
    }
    d = _dunya(ts, k099, fiyatlar, gunler)
    uyelik = {g: frozenset({"AAA", "BBB"}) for g in gunler}
    defter: list = []
    karar_fn = k099.cita_kararcisi(
        ts, k099.CITA_ESLI, aylar=d["aylar"], ay_sira=d["ay_sira"], uyelik=uyelik,
        per=d["per"], mpos=d["mpos"], mom_lookback=2, defter=defter)
    durum = k099.simule(ts, d["master"], d["per"], karar_fn, fee_bps=0.0,
                        sermaye=float(ts.INIT_EQUITY))
    olcum = [g for g in d["aylar"] if d["ay_sira"][g] >= 2]
    assert len(olcum) >= 2, "en az iki ölçüm ayı gerek"
    ilk, ikinci = olcum[0], olcum[1]
    icra = gunler[gunler.index(ilk) + 1]
    beklenen = sum(
        float(d["per"][t].at[k099._ts(ikinci), "close"])
        / float(d["per"][t].at[k099._ts(icra), "open"]) for t in ("AAA", "BBB")) / 2.0
    olculen = durum["equity"][ikinci] / durum["equity"][ilk]
    assert olculen == pytest.approx(beklenen, rel=1e-9), (
        "EW çıtası as-of üyelerin ortalaması DEĞİL")


# =================================================================================================
# T6 — CHANDELIER: ÇIKIŞ GÜNÜ VE SLOT DOLUMU
# =================================================================================================
@pytest.fixture(scope="module")
def cokus_dunyasi(k099, ts):
    """`AAA` yükselir, `COKUS_I` gününde SERT düşer; `BBB` yavaş yükselir (yedek slot adayı)."""
    gunler = _seanslar(200)
    cokus_i = 150
    aaa = []
    p = 100.0
    for i in range(len(gunler)):
        p *= 1.004
        aaa.append(p if i < cokus_i else p * 0.55)
    d = _dunya(ts, k099, {"AAA": aaa,
                          "BBB": [100.0 * (1.0015 ** i) for i in range(len(gunler))]}, gunler)
    d["gunler"] = gunler
    d["cokus_gun"] = gunler[cokus_i]
    d["uyelik"] = _uyelik_sabit(gunler, ["AAA", "BBB"])
    return d


def test_T6_chandelier_CIKIS_GUNU_DOGRU(k099, ts, cokus_dunyasi):
    """Çöküş günü tepe − K×ATR22 eşiğini kırar; SATIŞ ERTESİ SEANSIN AÇILIŞINDA icra edilir."""
    d = cokus_dunyasi
    durum, _ = _c_hucresi(k099, ts, d, n_slots=1)
    cikislar = [k for k in durum["kapanan"] if k["sebep"] == "chandelier"]
    assert cikislar, "chandelier çıkışı HİÇ olmadı — eşik ya da fikstür zayıf"
    gunler = d["gunler"]
    beklenen = gunler[gunler.index(d["cokus_gun"]) + 1]
    assert cikislar[0]["cikis"] == beklenen, (
        f"chandelier çıkışı yanlış seansta: {cikislar[0]['cikis']} ≠ {beklenen}")


def test_T6_bosalan_slot_SONRAKI_AY_SONUNDA_DOLAR(k099, ts, cokus_dunyasi):
    """Chandelier boşalttığı slotu ANINDA doldurmaz: dolum BİR SONRAKİ ay-sonunun ERTESİ
    seansındadır (incumbent akış — EDG-009 A/C tanımı)."""
    d = cokus_dunyasi
    durum, defter = _c_hucresi(k099, ts, d, n_slots=1)
    cikis = [k for k in durum["kapanan"] if k["sebep"] == "chandelier"][0]
    gunler = d["gunler"]
    sonraki_ay = min((r["ay_sonu"] for r in defter if r["ay_sonu"] > cikis["cikis"]),
                     default=None)
    assert sonraki_ay is not None, "çıkıştan sonra ay-sonu kalmadı — fikstür kısa"
    beklenen_giris = gunler[gunler.index(sonraki_ay) + 1]
    girisler = sorted({p["entry_date"] for p in durum["pozisyon"].values()}
                      | {k["giris"] for k in durum["kapanan"]})
    sonrakiler = [g for g in girisler if g > cikis["cikis"]]
    assert sonrakiler, "slot HİÇ dolmadı"
    assert sonrakiler[0] == beklenen_giris, (
        f"boşalan slot ay-sonu beklemeden doldu: {sonrakiler[0]} ≠ {beklenen_giris}")


# =================================================================================================
# T7 — EŞİKLER VE KILL-LIST KARTTAN
# =================================================================================================
def test_T7_kart_esikleri_ON_KAYITLI_SAYILAR(k099):
    """Kart dosyasındaki sayısal eşikler ön-kayıtla BİREBİR. Eşik sonradan DEĞİŞMEZ (§5)."""
    kart = k099.kart_oku(KART)
    assert kart["esikler_sayisal"] == pytest.approx(
        {k: float(v) for k, v in KART_ESIKLERI.items()}), (
        "kartın eşikleri ön-kayıtlı sayılardan ayrıştı — yeni eşik YENİ KART ister")


def test_T7_cikti_esikleri_KARTTAN_OKUNUR(boru):
    """Çıktıdaki `esikler` bloğu kartın sayılarını taşır ve {deger, esik, gecti} üçlüsüdür."""
    e = boru["sonuc"]["esikler"]
    kart = _kart_yaml()["esikler"]
    for ad, beklenen in KART_ESIKLERI.items():
        assert ad in e, f"`{ad}` eşiği çıktıda YOK"
        assert float(e[ad]["esik"]) == pytest.approx(float(beklenen))
        assert float(kart[ad]) == pytest.approx(float(beklenen))
        assert set(("deger", "esik", "gecti")) <= set(e[ad]), f"`{ad}` üçlüsü eksik"


def test_T7_kill_list_METINLERI_KARTTAN_BIREBIR(boru):
    """`kill_list_tetik` satırlarının lafzı kartın `kill_list`i ile BİREBİR aynıdır (sıra dahil).

    Metin yeniden yazılsaydı kartın kill-list'i koda kopyalanmış olurdu ve iki metin sessizce
    ayrışırdı (tek-kaynak yasası)."""
    kart = _kart_yaml()["kill_list"]
    lafizlar = [k["lafiz"] for k in boru["sonuc"]["kill_list_tetik"]]
    assert lafizlar == [str(x) for x in kart]


def test_T7_kartta_SAYISI_OLMAYAN_kill_satiri_TETIK_UYDURMAZ(boru):
    """"aday sayısı < 30 olan ay payı > %10" satırının sayısı `esikler`de YOK → `tetik` None,
    ölçülen pay ADIYLA yanında durur. Kod kart düzyazısından eşik TÜRETMEZ."""
    satir = [k for k in boru["sonuc"]["kill_list_tetik"] if "ay payı" in k["lafiz"].lower()]
    assert len(satir) == 1, "kartın ay-payı kill-list satırı bulunamadı"
    assert satir[0]["tetik"] is None
    assert satir[0]["neden"], "sayı neden türetilmediği YAZILMALI (uydurma yasağı)"
    assert "dusuk_ay_payi" in (satir[0]["olculen"] or {})


def test_T7_hukum_alani_SABIT(boru):
    """`hukum` alanı sabittir: ölçüm ajanı hüküm VERMEZ (CLAUDE.md §3, §5)."""
    assert boru["sonuc"]["hukum"] == "YOK — Rol-1"
    assert "HÜKÜM: YOK — Rol-1" in boru["rapor"]


# =================================================================================================
# T8 — PK-1
# =================================================================================================
@pytest.mark.parametrize("fazla,ci0,beklenen", [
    (7.25, True, True),        # yön + anlamlılık → GEÇTİ
    (7.25, False, False),      # yön var, CI sıfırı içeriyor → KALDI
    (-3.0, True, False),       # anlamlı ama YÖN ters → KALDI
    (None, True, None),        # fazla ölçülemedi → hüküm YOK (0 değil)
    (7.25, None, None),        # CI ölçülemedi → hüküm YOK
])
def test_T8_pk1_gecti_MANTIGI(k099, fazla, ci0, beklenen):
    """Kart lafzı: "D hücresi fazla > 0 VE CI-0-dışı". Ölçülemeyen alan hüküm ÜRETMEZ."""
    pk = k099.pk1_hukmu({"D": {"fazla": {"ann_pct": fazla, "ci0_disi": ci0, "t_nw": 2.1,
                                         "ci95": [1.0, 9.0], "n_months": 60}},
                         "C": {"fazla": {"ann_pct": 6.0, "ci0_disi": True, "t_nw": 1.8,
                                         "ci95": [0.5, 8.0], "n_months": 60}}})
    assert pk["kosdu"] is True
    assert pk["gecti"] is beklenen


def test_T8_pk1_KOSMADIYSA_gecti_None(k099):
    """Koşmayan PK "geçti" de "kaldı" da DEĞİLDİR — None + neden."""
    pk = k099.pk1_hukmu(None)
    assert pk["kosdu"] is False and pk["gecti"] is None and pk["neden"]


def test_T8_boru_hatti_PK1_DALI_KOSTU(boru):
    """`--pk-*` verilince PK-1 dalı GERÇEKTEN koşar ve D/C alanlarını kurar."""
    pk = boru["sonuc"]["pk1"]
    assert pk["kosdu"] is True, f"PK-1 koşmadı: {pk.get('neden')}"
    for h in ("D", "C"):
        assert set(("fazla", "t_nw", "ci", "ci0_disi", "n_months")) <= set(pk[h])
    assert pk["gecti"] in (True, False, None)
    assert pk["evren"]["olcum_ay_n"] >= 12, (
        "PK penceresi 12 aydan kısa — blok-bootstrap CI üretemez, hüküm ölçülemez")


# =================================================================================================
# T9 — ÖLÇÜLEMEYEN İSİMLER VE ADAY PAYI
# =================================================================================================
def test_T9_aday_payi_ESIK_ALTINDA_KALAN_AY(k099):
    """Eşiğin ALTINDA kalan ay payı = (aday_n < eşik) ay / toplam ay. Eşik DIŞARIDAN gelir."""
    blok = {"aday": {"seri": [{"ay_sonu": "2021-01-29", "aday_n": 12},
                              {"ay_sonu": "2021-02-26", "aday_n": 44},
                              {"ay_sonu": "2021-03-31", "aday_n": 29},
                              {"ay_sonu": "2021-04-30", "aday_n": 30}]}}
    k099._aday_payini_isle(blok, 30)
    assert blok["aday"]["dusuk_ay_n"] == 2          # 12 ve 29
    assert blok["aday"]["dusuk_ay_payi"] == pytest.approx(0.5)
    assert blok["aday"]["dusuk_ay_esigi"] == 30.0


def test_T9_aday_payi_AY_YOKSA_SIFIR_YAZILMAZ(k099):
    """Ay-sonu kararı yoksa pay SIFIR değil None + nedendir (uydurma yasağı)."""
    blok = {"aday": {"seri": []}}
    k099._aday_payini_isle(blok, 30)
    assert blok["aday"]["dusuk_ay_payi"] is None and blok["aday"]["dusuk_ay_neden"]


def test_T9_olculemeyen_isimler_ADIYLA_SAYILIR(boru):
    """Bar dosyası OLMAYAN ve KISA seri ADIYLA ayrı ayrı sayılır; pay birleşime göredir."""
    o = boru["sonuc"]["olculemeyen"]
    assert o["neden_dagilimi"]["bar_dosyasi_yok"]["n"] == 1, (
        f"bar dosyası olmayan isim sayısı yanlış: {o['neden_dagilimi']['bar_dosyasi_yok']}")
    assert NOBAR in o["neden_dagilimi"]["bar_dosyasi_yok"]["semboller"]
    assert o["neden_dagilimi"]["kisa_seri"]["n"] == 1
    assert KISA in o["neden_dagilimi"]["kisa_seri"]["semboller"]
    assert o["n"] == 2 and o["birlesim_n"] == _SADE_SEMBOL + len(OZEL)
    assert o["oran"] == pytest.approx(2.0 / (_SADE_SEMBOL + len(OZEL)))


def test_T9_ust_sinir_damgasi_HARITADAN_OKUNUR(boru):
    """Barsız-çıkış payı ADIM-0 B haritasından OKUNUR, YENİDEN HESAPLANMAZ (tek-kaynak).

    Fikstürdeki 0,4242 sentetik kohortta yeniden hesaplanamaz bir değerdir — görünüyorsa
    değer haritadan gelmiştir."""
    u = boru["sonuc"]["ust_sinir_damgasi"]["b_barsiz_cikis_payi"]
    assert u["payi"] == pytest.approx(KAPSAMA_PAYI)
    assert "YENİDEN HESAPLANMADI" in (u.get("kaynak") or "")


def test_T9_belirsiz_HARIC_kosumda_ISIM_SEPETTE_YOK(boru):
    """`haric` koşumunda belirsiz isim HİÇBİR ay-sonu sepetinde yoktur; `dahil`de VARDIR."""
    k = boru["sonuc"]["kosumlar"]
    assert set(k) == {"dahil", "haric"}
    haric = [r for r in k["haric"]["hucreler"]["D"]["ay_sonu_defteri"]]
    dahil = [r for r in k["dahil"]["hucreler"]["D"]["ay_sonu_defteri"]]
    assert dahil and haric
    assert any(BELIRSIZ_SEM in r["sepet"] for r in dahil), (
        "belirsiz isim `dahil` koşumunda hiç seçilmedi — çivi boş yere yeşil olurdu")
    assert all(BELIRSIZ_SEM not in r["sepet"] for r in haric), (
        "belirsiz isim `haric` koşumunda sepete girdi — süzgeç uygulanmıyor")


def test_T9_as_of_uyelik_BORU_HATTINDA_da_gecerli(boru):
    """Boru hattı düzeyinde as-of üyelik: sonradan giren isim giriş ÖNCESİ sepetlerde yok,
    üyelikten çıkan isim çıkıştan sonra yok ve `uyelik` sebebi SAYILMIŞ."""
    s = boru["sonuc"]
    g = boru["girdi"]
    giris_gun, cikis_gun = g["gunler"][GIRIS_I], g["gunler"][CIKIS_I]
    defter = s["hucreler"]["D"]["ay_sonu_defteri"]
    assert defter, "ay-sonu kararı yok"
    onceki = [r for r in defter if r["ay_sonu"] < giris_gun]
    sonraki = [r for r in defter if r["ay_sonu"] >= giris_gun]
    assert onceki and sonraki
    assert all(ENTRANT not in r["sepet"] for r in onceki)
    assert any(ENTRANT in r["sepet"] for r in sonraki), "ENTRANT hiç seçilmedi — fikstür zayıf"
    assert any(EXITER in r["sepet"] for r in defter if r["ay_sonu"] < cikis_gun)
    assert all(EXITER not in r["sepet"] for r in defter if r["ay_sonu"] >= cikis_gun)
    assert s["hucreler"]["D"]["devir"]["cikislar"]["uyelik"] >= 1


# =================================================================================================
# T10 — KOPYALANMAMIŞ SABİT + CANLI DEFTERE YAZAN YOL YOK
# =================================================================================================
_SINYAL_SABITLERI = ("MOM_LOOKBACK", "N_SLOTS", "FRICTION_BPS", "ATR_LEN", "CHANDELIER_K",
                     "DELIST_GRACE", "INIT_EQUITY")


def test_T10_k099_KAYNAGINDA_SINYAL_SABITI_ATAMASI_YOK():
    """Sabitler İTHAL edilir, kopyalanmaz: `k099` kaynağında bu adlara ATAMA olamaz.

    ÖLÇÜM AST İLEDİR, METİN DEĞİL: düz metin taraması dosyanın KENDİ ŞERHİNİ ("sabitler
    yeniden yazılmaz") yakalayıp kendi kendine kırmızı verirdi."""
    agac = ast.parse(K099.read_text(encoding="utf-8"), str(K099))
    bulunan = []
    for d in ast.walk(agac):
        if isinstance(d, (ast.Assign, ast.AnnAssign)):
            hedefler = d.targets if isinstance(d, ast.Assign) else [d.target]
            for h in hedefler:
                if isinstance(h, ast.Name) and h.id in _SINYAL_SABITLERI:
                    bulunan.append(h.id)
    assert not bulunan, (
        f"sinyal sabiti KOPYALANMIŞ: {sorted(set(bulunan))} — `meridian.trend_shadow`dan "
        f"ithal edilmeli (tek-kaynak yasası)")


def test_T10_k099_SABITLERI_trend_shadowDAN_OKUR():
    """CANLI TABAN ÖLÇÜSÜ: her sinyal sabiti GERÇEKTEN `ts.<AD>` niteliğinden okunuyor.

    M10a ("atama yok") tek başına BOŞTA TEMİZ diyebilirdi — sabit hiç kullanılmasaydı da
    yeşil kalırdı. Bu çivi tarayıcının kör olmadığını ölçer (v382'nin "sentetik pozitif kontrol
    + canlı taban" deseni).

    KAPSAM SINIRI YAZILI (mutasyonla ölçüldü 2026-09-15): sabit BİRDEN ÇOK yerde okunuyorsa
    bu çivi yalnız SONUNCU okuma da kaybolduğunda öter — tek bir çağrı yerinin dinamik
    `getattr`a çevrilmesini GÖRMEZ. O sınıfı kapatan şey M10a'nın atama yasağıdır; burada
    ölçülemeyen bir kapsamı "kapalı" saymak yerine AÇIKÇA yazılır."""
    agac = ast.parse(K099.read_text(encoding="utf-8"), str(K099))
    okunan = {d.attr for d in ast.walk(agac)
              if isinstance(d, ast.Attribute) and isinstance(d.value, ast.Name)
              and d.value.id == "ts"}
    for ad in ("MOM_LOOKBACK", "N_SLOTS", "FRICTION_BPS", "ATR_LEN", "CHANDELIER_K"):
        assert ad in okunan, f"`ts.{ad}` okuması YOK — sabit nereden geliyor?"


_YASAK_CAGRILAR = ("run_cycle", "_kaydet", "ozet", "_uygunluk", "write_json")


def test_T10_k099_CANLI_GOLGE_DEFTERINE_YAZAN_YOL_TASIMAZ():
    """`trend_shadow`dan YALNIZ sabit ve saf fonksiyon alınır: yazan yol HİÇ çağrılmaz.

    `run_cycle`/`_kaydet` canlı `state/trend_book.json`a yazar; `_uygunluk` `obs.warn` yüzeyi
    taşır. Bir ölçüm betiğinde bunların çağrılması, ölçümün canlı deftere dokunması demektir
    (CLAUDE.md §2: "pytest dışı koşum obs'a ulaşırsa canlı yerel deftere YAZAR")."""
    agac = ast.parse(K099.read_text(encoding="utf-8"), str(K099))
    bulunan = []
    for d in ast.walk(agac):
        if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute):
            if d.func.attr in _YASAK_CAGRILAR:
                bulunan.append(d.func.attr)
        if isinstance(d, ast.Call) and isinstance(d.func, ast.Name):
            if d.func.id in _YASAK_CAGRILAR:
                bulunan.append(d.func.id)
    assert not bulunan, f"canlı deftere/obs'a giden çağrı: {sorted(set(bulunan))}"


def test_T10_k099_MODUL_DUZEYI_TEMIZ():
    """Modül düzeyinde `meridian` ithali ve G/Ç YOKTUR — ithal etmek koşum TETİKLEMEZ."""
    agac = ast.parse(K099.read_text(encoding="utf-8"), str(K099))
    for d in agac.body:
        if isinstance(d, ast.ImportFrom):
            assert not (d.module or "").startswith("meridian"), (
                f"modül düzeyinde meridian ithali: {d.module}")
        if isinstance(d, ast.Import):
            assert all(not a.name.startswith("meridian") for a in d.names)
        assert not (isinstance(d, ast.Expr) and isinstance(d.value, ast.Call)), (
            "modül düzeyinde çağrı var — ithal bir koşum tetikleyebilir")


def test_T10_ham_exec_module_YOK():
    """v334 §C: `__pycache__` kaynağın önüne geçmesin — `ops.sasi_yukleyici` kullanılır.

    TARAYICI v334'TEN İTHAL EDİLİR, KOPYALANMAZ (v401'in v382'den ithal deseni): kopya düz
    metin taramasına düşerse yasağı ANLATAN docstring'i suçlu sayar — bu deponun ölçülmüş
    tuzağı (v334 başlığı). Buradaki ilk hâl tam olarak o tuzağa düştü (2026-09-15)."""
    from tests.test_bayat_bytecode_v334 import _exec_module_cagrilari
    satirlar = _exec_module_cagrilari(K099.read_text(encoding="utf-8"))
    assert not satirlar, f"ham `exec_module` çağrısı var (satır: {satirlar})"
    assert "kaynaktan_yukle" in K099.read_text(encoding="utf-8")


# =================================================================================================
# T11 — CLI KULLANIM HATALARI
# =================================================================================================
def _cli(argv, tmp_path):
    env = dict(os.environ, PYTHONPATH=str(REPO), PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([sys.executable, str(K099)] + argv, cwd=str(REPO), env=env,
                          capture_output=True, text=True, timeout=300)


def test_T11_KART_YOKSA_CIKIS_2(tmp_path):
    """`--kart` ZORUNLUDUR: eşikler karttan okunur ve UYDURULMAZ (kartsız koşum = çıkış 2)."""
    p = _cli(["--repo", str(REPO), "--kohort", str(tmp_path / "yok.csv"),
              "--bars-dir", str(tmp_path), "--cikti", str(tmp_path / "c")], tmp_path)
    assert p.returncode == 2, f"beklenen çıkış 2, görülen {p.returncode}\n{p.stderr}"
    assert not (tmp_path / "c").exists(), "kullanım hatasında çıktı dizini AÇILMAMALI"


def test_T11_KART_DOSYASI_YOKSA_CIKIS_2(tmp_path):
    """Kart yolu verilip dosya yoksa da çıkış 2 — sessiz varsayılan eşik YOK.

    ÇIKTI DİZİNİ AÇILMAMIŞ OLMALI: kart kontrolü HER ŞEYDEN ÖNCE koşar. Yalnız çıkış kodu
    ölçülseydi çivi kör kalırdı — mutasyon ölçüldü (2026-09-15): kart okunamayınca depodaki
    GERÇEK karta düşen bir sürüm de çıkış 2 veriyordu (pencere adımında), yani "eşik
    uydurulmadı" iddiası yanlış sebeple yeşil oluyordu. Yan etkinin YOKLUĞU ayrımı kurar."""
    p = _cli(["--repo", str(REPO), "--kohort", str(tmp_path / "yok.csv"),
              "--bars-dir", str(tmp_path), "--kart", str(tmp_path / "yok.yaml"),
              "--cikti", str(tmp_path / "c")], tmp_path)
    assert p.returncode == 2
    assert "--kart dosyası yok" in (p.stderr or ""), f"beklenen kart hatası değil: {p.stderr}"
    assert not (tmp_path / "c").exists(), (
        "kart reddedilmeden ÖNCE çıktı dizini açıldı — kontrol yan etkiden SONRA koşuyor")


def test_T11_PK_BAYRAGI_TEK_BASINA_SESSIZCE_YOK_SAYILMAZ(tmp_path):
    """`--pk-kohort` verilip `--pk-bars-dir` verilmezse koşum DURUR: yarım PK sessizce
    atlanırsa koşum "başarılı" görünürken pozitif kontrol HİÇ koşmamış olurdu.

    MESAJ ADIYLA ARANIR, `"pk" in stderr` İLE DEĞİL: mutasyon ölçüldü (2026-09-15) —
    `tmp_path` adı testin KENDİ adından türüyor ve içinde "PK" geçiyordu, yani gevşek arama
    BAŞKA bir hatanın yol dizgesiyle yeşil kalıyordu (yanlış sebeple yeşil çivi sınıfı)."""
    p = _cli(["--repo", str(REPO), "--kohort", str(tmp_path / "yok.csv"),
              "--bars-dir", str(tmp_path), "--kart", str(KART),
              "--cikti", str(tmp_path / "c"), "--pk-kohort", str(tmp_path / "pk.csv")],
             tmp_path)
    assert p.returncode == 2
    assert "--pk-bars-dir" in (p.stderr or ""), f"beklenen PK bayrak hatası değil: {p.stderr}"
    assert not (tmp_path / "c").exists(), (
        "bayrak tutarlılığı yan etkiden SONRA sınanıyor — çıktı dizini açılmış")


def test_T11_ITHALDEN_SONRAKI_KULLANIM_HATASI_AGACI_KIRLETMEZ(tmp_path):
    """İTHALDEN SONRA çıkış 2 veren koşum wp2 `_cache/`+`_state/`ini GERİDE BIRAKMAZ.

    ÖLÇÜLDÜ 2026-09-15 (mutasyon koşumu): wp2 `ortak.py` modül düzeyinde kendi dizininde bu iki
    dizini açar; ithalden sonra kullanım hatasıyla dönen bir koşum onları bırakıyordu ve
    `research/olcumler/wp2_olcum/_state/` çalışma ağacında untracked olarak kalıyordu — Rol-1'in
    `git status --porcelain` kapısı (dagit ön şartı) tam olarak bunu reddeder.

    ÇİVİ ÇIRÇIR DEĞİL: dizinlerin koşumdan ÖNCEKİ hâli kaydedilir ve yalnız BU koşumun açtığı
    dizin sorulur. Başka bir oturum onları önceden açmışsa k093'ün geri-alma kuralı onlara
    dokunmaz (ve bu çivi de dokunulmamasını bekler) — aksi hâlde paralel oturumda çırçır olurdu.
    """
    wp2_cache, wp2_state = WP2 / "_cache", WP2 / "_state"
    onceki = {p: p.exists() for p in (wp2_cache, wp2_state)}
    kohort = tmp_path / "kohort.csv"
    kohort.write_text('date,tickers\n2021-01-04,"AAA,BBB"\n', encoding="utf-8")
    p = _cli(["--repo", str(REPO), "--kohort", str(kohort), "--bars-dir", str(tmp_path),
              "--kart", str(KART), "--cikti", str(tmp_path / "c"),
              "--baslangic", "2021-01-04", "--bitis", "2020-01-02"], tmp_path)
    assert p.returncode == 2, f"beklenen çıkış 2, görülen {p.returncode}\n{p.stderr}"
    assert "ÖNCE olamaz" in (p.stderr or ""), f"beklenen pencere hatası değil: {p.stderr}"
    for yol, vardi in onceki.items():
        if not vardi:
            assert not yol.exists(), (
                f"kullanım hatası yolunda ithal artefaktı GERİDE KALDI: {yol} — Rol-1'in "
                f"`git status --porcelain` kapısı kirlenir")


# =================================================================================================
# EK — ÇIKTI SÖZLEŞMESİ (okuyanı Rol-1)
# =================================================================================================
def test_cikti_ALANLARI_SOZLESMEYE_UYGUN(boru):
    """Rol-1'in hüküm için okuduğu alanlar YERİNDE ve girdi sha'ları dolu."""
    s = boru["sonuc"]
    for ad in ("kart", "hukum", "sabitler", "girdi_damgasi", "hucreler", "citalar", "esikler",
               "kill_list_tetik", "pk1", "ust_sinir_damgasi", "kosumlar", "tohum",
               "ithal_yan_etkisi", "cozulen_yollar", "DURUM"):
        assert ad in s, f"çıktıda `{ad}` YOK"
    assert s["kart"] == "EDG-2026-099"
    assert set(s["hucreler"]) == {"C", "D"}
    assert set(s["citalar"]) == {"cita_esli", "cita_taban"}
    for ad in ("kohort_csv", "kart", "olcum_kodu", "k093", "trend_shadow"):
        assert s["girdi_damgasi"][ad]["sha256"], f"`{ad}` sha256 BOŞ"
    assert s["DURUM"] == "OLCULDU"
    assert s["tohum"]["deger"] is not None and s["tohum"]["kaynak"]


def test_cikti_FAZLA_BLOGU_CI_URETTI(boru):
    """Blok-bootstrap CI ve Newey-West t GERÇEKTEN ölçüldü (None kalmadı) — yoksa hüküm
    yüzeyi sessizce boş kalırdı."""
    for h in ("C", "D"):
        f = boru["sonuc"]["hucreler"][h]["fazla"]
        assert f["n_months"] >= 12, f"{h}: ölçüm ayı 12'den az ({f['n_months']})"
        assert f["ann_pct"] is not None and f["t_nw"] is not None, f"{h}: {f.get('t_neden')}"
        assert all(x is not None for x in f["ci95"]), f"{h}: CI ölçülemedi ({f.get('ci_neden')})"
        assert f["ci0_disi"] in (True, False)


def test_cikti_ITHAL_YAN_ETKISI_GERI_ALINDI(boru):
    """wp2 ithalinin açtığı dizinler kayda geçer — Rol-1'in `git status` kapısı kirlenmesin."""
    ye = boru["sonuc"]["ithal_yan_etkisi"]
    assert set(ye) == {"_cache", "_state"}
    for ad, kayit in ye.items():
        assert "silindi" in kayit and "koşumdan_once_vardi" in kayit


def test_RAPOR_uretildi_ve_HUKUM_ONERISI_YOK(boru):
    """RAPOR üretildi; ölçüm ajanı hüküm ÖNERİSİ de yazmaz."""
    r = boru["rapor"]
    for baslik in ("## 1. HÜCRE × ÖLÇÜ", "## 6. KART EŞİKLERİ", "## 7. KILL-LIST",
                   "## 8. PK-1", "## 9. ÜST-SINIR DAMGASI"):
        assert baslik in r, f"RAPOR'da `{baslik}` bölümü YOK"
    assert "hüküm ÖNERİSİ DE yazmaz" in r
