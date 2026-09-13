"""EDG-2026-088 PK (2) GERÇEK AYAĞININ ÇİVİLERİ — `research/olcumler/edg088_golge_pilot/pk2_gercek.py`.

NE ÇİVİLER. Kartın `pozitif_kontrol` (2) ayağı: "canlı NORMAL yolun son 10 gerçek işlemi gölge
motorundan geçirilir; gölge R − gerçek R farkı komisyon+kayma payı içinde
(`esikler.golge_gercek_fark_R_ust`)". Betik ÖLÇÜM üretir, HÜKÜM yazmaz (kart hükmü Rol-1'in).

ÇİVİLERİN HEDEF DALLARI (her biri mutasyonla ısırdığı gösterildi — rapor `rapor_pk2.md` §Mutasyon):
  A1 donmuş girdinin SHA256SUMS manifestosu · A2 "son 10" süzgeci DONUK kümedir (sayı+isim kapısı) ·
  A3 plan satırından TÜRETME YOK · A4 dolum sınıfı ÖLÇÜLÜR (ticker listesi değil, ALAN varlığı) ·
  B1 sentetik iki işlemin gölge R'si EL HESABIYLA birebir + `gecti` · B2 kill#5 (PK düştüyse sayı
  yayılmaz) · B3 çıplak ayna sınıfı DÜŞÜRÜLMEZ (kill#3) ve iki ortalama AYRI paydadan ·
  C1 canlı `state/` altına yazım YOK · C2 rejim kapısının kaynağı BEYANLIDIR ve ölçülenle uyumlu ·
  C3 komut satırı sözleşmesi (ops sözleşmesi `main()` değil KOMUT SATIRIdır).

SENTETİK SAHNE NEDEN GİRİŞ SEANSINDA KAPANIR. İki işlem de girdiği barın İÇİNDE (faz 2,
`broker.PaperBroker._touch_exit`) kapanır; `strategy.manage_position` (faz 3) ve dolayısıyla rejim
kapısı ile çıkış düğmeleri sonuca HİÇ karışmaz. Böylece beklenen R bir el hesabıdır, bir
"motorun bugünkü davranışı"nın kopyası değil — çivi kendi ölçtüğü şeyi doğrulamaz.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

import pandas as pd
import pytest

KOK = pathlib.Path(__file__).resolve().parents[1]
SANDBOX = KOK / "research" / "olcumler" / "edg088_golge_pilot"
for _p in (str(KOK), str(SANDBOX)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pk2_gercek as pk2  # noqa: E402
import sayim  # noqa: E402  — birim kapısının TEK sahibi; `pk2_gercek` de onu çağırır
from meridian import broker as brk  # noqa: E402  — R payda damgası MOTORUN sabiti (TSK-187)
from meridian import golge_icra as gi  # noqa: E402  — ısınma eşiği MOTORUN sabiti

DONMUS_GIRDI = SANDBOX / "pk2_gercek" / "girdi" / "a1_gercek_islemler_2026-09-13.json"
#: `--params` artık bir DİZİNdir (iki donmuş sınıf — §D1). Sentetik sahne PK (3) tabanında koşmaya
#: DEVAM eder: B1'in el hesabı giriş barının İÇİNDE kapanır, yani hangi kuşağın koştuğu R'ye
#: karışmaz; tabanı değiştirmek çivinin ölçtüğü şeyi sessizce kaydırırdı.
DONMUS_PARAMS_DIZIN = SANDBOX / "pk3_selef" / "params_donmus"

# ---- SENTETİK SAHNENİN EL HESABI ----------------------------------------------------------------
# AAPL: tetik 100 · stop 95 · hedef 115 · giriş barı (o=101, h=116, l=99)
#   dolum = max(açılış, tetik) = 101 (stop-al, beyanlı sapma 3) · r_per_share = 101 − 95 = 6
#   faz 2: o>eff_stop, o<hedef, l>eff_stop, h≥hedef → çıkış HEDEFTE (115), neden "target"
#   R = (115 − 101) / 6 = 2,333333
# MSFT: tetik 200 · stop 190 · hedef 230 · giriş barı (o=202, h=205, l=189)
#   dolum = 202 · r_per_share = 12 · faz 2: l≤eff_stop → çıkış STOPTA (190), neden "stop"
#   R = (190 − 202) / 12 = −1,0
BEKLENEN_R = {"AAPL": round(14.0 / 6.0, 6), "MSFT": -1.0}
BEKLENEN_NEDEN = {"AAPL": "target", "MSFT": "stop"}
SENTETIK_TICKERLAR = ("AAPL", "MSFT")
D_PLAN = "2026-09-01"
D_GIRIS = "2026-09-02"


# ==================================================================================================
# SENTETİK SAHNE KURUCULARI
# ==================================================================================================
def _seanslar() -> list[pd.Timestamp]:
    """Sentetik takvim: iş günleri. Takvim-dışı satırı üretimin kendi kapısı
    (`adapters.data.sanitize_bars`) düşürür — çivi kendi takvimini dayatmaz."""
    return list(pd.bdate_range("2025-06-02", D_GIRIS))


def _bar_yaz(dizin: pathlib.Path, ticker: str, satirlar: list[dict]) -> None:
    dizin.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(satirlar).to_csv(dizin / f"{ticker.lower()}.csv", index=False)


def _duz_seri(seanslar, taban: float) -> list[dict]:
    """Isınma barları: yatay seri (ATR ısınması dolsun, düzeltilmemiş-satır kapısı ötmesin)."""
    return [{"date": str(d.date()), "open": taban, "high": taban * 1.004,
             "low": taban * 0.996, "close": taban, "volume": 1_000_000.0} for d in seanslar]


def _sentetik_barlar(bars_dizin: pathlib.Path) -> None:
    """SPY (rejim/takvim) + AAPL + MSFT. Giriş barı (D+1) el hesabının sahnesidir."""
    seanslar = _seanslar()
    isinma = seanslar[:-1]

    spy = []
    fiyat = 400.0
    for d in seanslar:
        spy.append({"date": str(d.date()), "open": fiyat, "high": fiyat * 1.004,
                    "low": fiyat * 0.996, "close": fiyat * 1.001, "volume": 50_000_000.0})
        fiyat *= 1.001
    _bar_yaz(bars_dizin, "SPY", spy)

    aapl = _duz_seri(isinma, 100.0)
    aapl.append({"date": D_GIRIS, "open": 101.0, "high": 116.0, "low": 99.0,
                 "close": 110.0, "volume": 2_000_000.0})
    _bar_yaz(bars_dizin, "AAPL", aapl)

    msft = _duz_seri(isinma, 200.0)
    msft.append({"date": D_GIRIS, "open": 202.0, "high": 205.0, "low": 189.0,
                 "close": 195.0, "volume": 2_000_000.0})
    _bar_yaz(bars_dizin, "MSFT", msft)


def _sentetik_plan(ticker: str, tetik: float, stop: float, hedef: float) -> dict:
    """Plan satırı — canlı `trade_plans` şemasının PK (2)'de tüketilen alanları."""
    return {"id": f"P-{D_PLAN}-{ticker}", "date": D_PLAN, "ticker": ticker, "side": "long",
            "entry_trigger": tetik, "stop": stop, "profit_target": hedef,
            "setup": "momentum_burst", "gate_verdict": "REVIEW", "dormant_setup": 0,
            "strategy_version": 5, "score": 80, "regime_at_plan": "trend_up"}


def _sentetik_islem(ticker: str, r: float, giris: float, cikis: float, qty: int,
                    neden: str, ciplak: bool, damga: str | None = brk.R_PAYDA_GIRIS) -> dict:
    """Gerçek işlem satırı — `broker.PaperBroker.close_position` alan kümesiyle aynı adlar.

    `entry`/`exit` KAYMALI fiyatlardır (giriş `×(1+slip)`, çıkış `×(1−slip)`, slip 5 bps);
    `pnl_dollars` o fiyatlardan türer. Payı `sayim._friksiyon_payi` bu alanlardan ölçer.

    R PAYDA DAMGASI (TSK-187) `extra_json`a girer — çünkü `close_position` onu TİPSİZ alan olarak
    yazar ve `storage` tipsiz alanı oraya düşürür. Damga sentetik sahnenin süsü DEĞİL: `sayim`in
    birim kapısı onu arar ve damgasız satır PK (2) kıyasının DIŞINDA kalır. `damga=None` o ESKİ
    kuşağı (bütçe paydalı, TSK-187 öncesi) kurar.
    """
    e, x = round(giris * 1.0005, 4), round(cikis * 0.9995, 4)
    extra = {"skill_chain": ["x"], "broker_teyit": "teyitli"}
    if damga is not None:
        extra["r_payda"] = damga
    if not ciplak:
        extra.update({"alpaca_fill_price": x, "mirror_divergence": 0.0005,
                      "dolum_ts": f"{D_GIRIS}T13:35:00Z"})
    return {"id": f"T-{ticker}", "plan_id": f"P-{D_PLAN}-{ticker}", "ticker": ticker,
            "side": "long", "ts_open": D_GIRIS, "ts_close": D_GIRIS,
            "entry": e, "exit": x, "qty": qty, "r_multiple": r,
            "pnl_dollars": round(qty * (x - e), 4), "costs": None,
            "exit_reason": neden, "bars_held": 1, "scaled_out": 0,
            "strategy_version": 5, "setup": "momentum_burst", "kaynak": "live_paper",
            "extra_json": json.dumps(extra)}


def _sentetik_girdi(dizin: pathlib.Path, r_kaydirma: float = 0.0) -> pathlib.Path:
    """Donmuş girdinin sentetik ikizi + manifestosu. `r_kaydirma` GERÇEK R'yi oynatır."""
    dizin.mkdir(parents=True, exist_ok=True)
    islemler = [
        _sentetik_islem("AAPL", round(BEKLENEN_R["AAPL"] + r_kaydirma, 3),
                        101.0, 115.0, 165, "target", ciplak=False),
        _sentetik_islem("MSFT", round(BEKLENEN_R["MSFT"] + r_kaydirma, 3),
                        202.0, 190.0, 50, "stop", ciplak=True),
    ]
    veri = {"trades": islemler,
            "plans": [_sentetik_plan("AAPL", 100.0, 95.0, 115.0),
                      _sentetik_plan("MSFT", 200.0, 190.0, 230.0)],
            "e2": [], "cekim_utc": "2026-09-13T00:00:00"}
    yol = dizin / "sentetik.json"
    yol.write_text(json.dumps(veri, ensure_ascii=False), encoding="utf-8")
    (dizin / pk2.MANIFEST_ADI).write_text(
        f"{hashlib.sha256(yol.read_bytes()).hexdigest()}  {yol.name}\n", encoding="utf-8")
    return yol


def _sentetik_v5_dizin(kok: pathlib.Path, monkeypatch) -> pathlib.Path:
    """`canli_v5_donmus` SINIFININ sentetik ikizi: gerçek v5 dosyalarının kopyası + ÜST dizinde
    `SHA256SUMS`. Sınıf çözücüsü modül sabitinden ÇAĞRI ANINDA türer, o yüzden yamalanabilir."""
    dizin = kok / "params_v5"
    dizin.mkdir(parents=True, exist_ok=True)
    for ad in ("strategy.yaml", "goal.yaml", "bounds.yaml"):
        (dizin / ad).write_bytes((pk2.params_v5_dizin() / ad).read_bytes())
    (kok / pk2.MANIFEST_ADI).write_text("".join(
        f"{hashlib.sha256((dizin / ad).read_bytes()).hexdigest()}  params_v5/{ad}\n"
        for ad in ("strategy.yaml", "goal.yaml", "bounds.yaml")), encoding="utf-8")
    monkeypatch.setattr(pk2, "params_v5_dizin", lambda betik=None: dizin)
    return dizin


def _kos(tmp_path: pathlib.Path, r_kaydirma: float = 0.0,
         params_dizin: pathlib.Path | None = None) -> dict:
    bars = tmp_path / "barlar"
    _sentetik_barlar(bars)
    girdi = _sentetik_girdi(tmp_path / "girdi", r_kaydirma)
    return pk2.kos(girdi, bars, params_dizin or DONMUS_PARAMS_DIZIN, tmp_path / "gecici_state",
                   n_gercek=2, beklenen_tickerlar=SENTETIK_TICKERLAR)


# ==================================================================================================
# A1 — DONMUŞ GİRDİNİN KİMLİĞİ
# ==================================================================================================
def test_A1_donmus_girdi_MANIFESTOYLA_dogrulanir():
    """Kart girdiyi dondurur; kimlik bir beyan değil bir ÖLÇÜMdür (SHA256SUMS)."""
    kimlik = pk2.manifest_dogrula(DONMUS_GIRDI)
    assert kimlik["sha256"] == hashlib.sha256(DONMUS_GIRDI.read_bytes()).hexdigest()
    assert kimlik["manifest"].endswith(pk2.MANIFEST_ADI)


def test_A1_kurcalanmis_girdi_BLOK_ve_manifest_yoksa_BLOK(tmp_path):
    """Sessiz devam etmek, DEĞİŞMİŞ bir girdiyi donmuş gibi ölçmek olurdu."""
    yol = _sentetik_girdi(tmp_path)
    yol.write_text(yol.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(pk2.Blok, match="sha256"):
        pk2.manifest_dogrula(yol)

    (yol.parent / pk2.MANIFEST_ADI).unlink()
    with pytest.raises(pk2.Blok, match="manifest"):
        pk2.manifest_dogrula(yol)


# ==================================================================================================
# A2 — "SON 10" DONUK BİR KÜMEDİR
# ==================================================================================================
def test_A2_son_10_gercek_islem_TAM_ve_kume_DONUK():
    """Sayı DA isim DE kapıdır: girdi değişirse başka bir popülasyon ölçülür ve PK adı aynı
    kalarak başka bir sınamaya dönüşürdü (emsal: `pk3_selef.suz_049`)."""
    veri = pk2.girdi_oku(DONMUS_GIRDI)
    secilen = pk2.son_n_gercek(veri["trades"])
    assert len(secilen) == pk2.N_GERCEK == 10
    assert tuple(t["ticker"] for t in secilen) == pk2.BEKLENEN_TICKERLAR
    # 11-12 (LLY, BDX) YEDEKTİR ve kümeye girmez.
    assert {"LLY", "BDX"}.isdisjoint({t["ticker"] for t in secilen})


def test_A2_DONMUS_girdi_TSK187_ONCESI_kusaktir_ve_R_KIYASINA_giremez():
    """BEDEL YASASI (TSK-187 tur 2). Donmuş A1 girdisi 2026-09-13 çekimidir — payda değişikliğinden
    ÖNCE kapanmış işlemler, yani `r_payda` damgası TAŞIMAZ. `sayim.kontrol_olc`in birim kapısı bu
    on satırı R kıyasının DIŞINDA bırakır: PK (2) bu donmuş girdide artık "ölçülemedi"dir
    (`birim_eski_n`), "geçti/kaldı" DEĞİL. Bu bir kayıptır ve SAYILIR — gizlenirse kapı sessizce
    bir PK'yı boşaltmış olurdu. Yeni bir donmuş çekim geldiğinde bu çivi kırmızıya döner ve kartın
    PK (2) ayağı damgalı kuşakla YENİDEN ölçülmelidir.
    """
    veri = pk2.girdi_oku(DONMUS_GIRDI)
    secilen = pk2.son_n_gercek(veri["trades"])
    damgalar = [sayim.r_payda_damgasi(t) for t in secilen]
    assert damgalar == [None] * len(secilen), damgalar
    assert all(d != brk.R_PAYDA_GIRIS for d in damgalar)


def test_A2_kume_ayrisirsa_BLOK():
    veri = pk2.girdi_oku(DONMUS_GIRDI)
    bozuk = [dict(t) for t in veri["trades"]]
    bozuk[0]["ticker"] = "XXX"
    with pytest.raises(pk2.Blok, match="donuk küme"):
        pk2.son_n_gercek(bozuk)
    with pytest.raises(pk2.Blok, match="yeterli"):
        pk2.son_n_gercek(veri["trades"][:3])


# ==================================================================================================
# A3 — PLAN SATIRINDAN TÜRETME YOK
# ==================================================================================================
def test_A3_golge_plani_alanlari_PLAN_SATIRINDAN_birebir():
    """`entry_trigger`/`stop`/`profit_target` plan tablosundan gelir; işlemin gerçekleşmiş
    `entry`/`exit`i gölge planına SIZMAZ (türetilen bir tetik, ölçüleni uydurulana çevirirdi)."""
    veri = pk2.girdi_oku(DONMUS_GIRDI)
    planlar = pk2.plan_haritasi(veri["plans"])
    ham = planlar["P-2026-09-04-MU"]
    p = pk2.golge_plani(ham)
    for alan in ("id", "ticker", "date", "entry_trigger", "stop", "profit_target",
                 "setup", "gate_verdict", "dormant_setup", "strategy_version"):
        assert p[alan] == ham[alan], alan
    islem_alanlari = {"entry", "exit", "r_multiple", "exit_reason", "qty", "pnl_dollars"}
    assert islem_alanlari.isdisjoint(set(p)), p


def test_A3_dormant_damgasi_0_ise_KONTROL_kolu():
    """PK (2) kontrol kolundadır: `sayim.kontrol_olc` paydasını `kol == "kontrol"` ile kurar."""
    from meridian import golge_icra as gi
    veri = pk2.girdi_oku(DONMUS_GIRDI)
    p = pk2.golge_plani(pk2.plan_haritasi(veri["plans"])["P-2026-09-04-MU"])
    assert p["dormant_setup"] == 0
    assert gi._bekleyen_kayit(p, D_PLAN)["kol"] == gi.KOLLAR[1] == "kontrol"


# ==================================================================================================
# A4 — DOLUM SINIFI ÖLÇÜLÜR
# ==================================================================================================
def test_A4_dolum_sinifi_ALAN_VARLIGINDAN_olculur_ticker_listesinden_degil():
    """Sınıf bir isim listesi olsaydı girdi değişince sessizce bayatlardı."""
    assert pk2.dolum_sinifi({"extra_json": json.dumps(
        {"alpaca_fill_price": 1.0, "dolum_ts": "x"})}) == "dogrulanmis"
    assert pk2.dolum_sinifi({"extra_json": json.dumps({"alpaca_fill_price": 1.0})}) == "kismi"
    assert pk2.dolum_sinifi({"extra_json": json.dumps({"broker_teyit": "teyitli"})}) == "ciplak"
    assert pk2.dolum_sinifi({"extra_json": "{bozuk"}) == "ciplak"


def test_A4_donmus_girdide_ciplak_sinif_OLCULEN_kumedir():
    """Brief'in saydığı MU/MPC/DE çıplak; MRVL `alpaca_fill_price` taşır ama `dolum_ts` YOK →
    KISMİ. Sınıflar ölçülür, brief'in listesi kopyalanmaz."""
    veri = pk2.girdi_oku(DONMUS_GIRDI)
    secilen = pk2.son_n_gercek(veri["trades"])
    sinif = {t["ticker"]: pk2.dolum_sinifi(t) for t in secilen}
    assert {t for t, s in sinif.items() if s == "ciplak"} == {"MU", "MPC", "DE"}
    assert sinif["MRVL"] == "kismi"
    assert sinif["VRTX"] == "dogrulanmis"


# ==================================================================================================
# B1 — SENTETİK: GÖLGE R EL HESABIYLA
# ==================================================================================================
def test_B1_sentetik_golge_R_EL_HESABIYLA_birebir_ve_gecti(tmp_path, sandbox_state):
    sonuc = _kos(tmp_path)
    satir = {s["ticker"]: s for s in sonuc["islemler"]}
    for tk in SENTETIK_TICKERLAR:
        assert satir[tk]["olculemedi"] is None, satir[tk]
        assert satir[tk]["golge_r"] == pytest.approx(BEKLENEN_R[tk], abs=1e-6), satir[tk]
        assert satir[tk]["golge_cikis_neden"] == BEKLENEN_NEDEN[tk], satir[tk]
    k = sonuc["kontrol"]
    assert k["n_cift"] == 2 and k["gecti"] is True, k
    assert k["esik"] == 0.05
    assert k["ort_mutlak_fark_r"] <= k["komisyon_kayma_payi"], k
    assert sonuc["gecti"] is True


def test_B1_tutma_penceresi_TAKVIMDEN_sayilir_bar_n_ile_KARISTIRILMAZ(tmp_path, sandbox_state):
    """Gölge defter satırı `bars_held` TAŞIMAZ (ölçüldü); taşıdığı `bar_n` ATR ısınmasını da
    içerir. İki tarafı da AYNI takvimden sayan tutma penceresi karşılaştırılabilir tek
    büyüklüktür; `bar_n − trades.bars_held` adı "bar farkı" olan ama hiçbir şey ölçmeyen bir
    sayıdır (ilk gerçek koşumda −13 yazdı)."""
    from meridian import golge_icra as gi
    assert "bars_held" not in gi.SATIR_ALANLARI and "bar_n" in gi.SATIR_ALANLARI

    sonuc = _kos(tmp_path)
    for r in sonuc["islemler"]:
        # Sentetik sahnede giriş ve çıkış AYNI seanstadır → iki tarafta da 0 seans.
        assert r["golge_seans_n"] == 0 and r["gercek_seans_n"] == 0, r
        assert r["seans_farki"] == 0, r
        # `bar_n` ISINMA penceresini taşır: tutma penceresiyle AYNI sayı DEĞİLDİR.
        assert r["golge_bar_n"] > r["golge_seans_n"], r


def test_B1_takvim_kapsamiyorsa_tutma_penceresi_NONE(tmp_path, sandbox_state):
    """Uydurma yasağı: uç noktalardan biri takvimde yoksa pencere 0 değil `None`."""
    import pandas as _pd
    say = pk2._seans_sayaci(_pd.DataFrame(index=_pd.DatetimeIndex(["2026-09-01", "2026-09-02"])))
    assert say("2026-09-01", "2026-09-02") == 1
    assert say("2026-09-01", "2026-09-30") is None
    assert say(None, "2026-09-02") is None
    assert say("bozuk", "2026-09-02") is None


def test_B1_esik_ve_pay_MOTORUN_KENDI_sabitinden(tmp_path, sandbox_state):
    """Eşik betikte sayı olarak yazılı DEĞİLDİR: `golge_icra.FARK_R_UST`tan gelir (tek-kaynak).
    Mutasyon hedefi: `pk2_gercek.fark_ust` gevşetilirse bu çivi ısırır."""
    from meridian import golge_icra as gi
    assert pk2.fark_ust() == gi.FARK_R_UST == 0.05
    sonuc = _kos(tmp_path)
    assert sonuc["kontrol"]["esik"] == gi.FARK_R_UST
    assert "PaperBroker" in sonuc["kontrol"]["pay_kaynagi"]


# ==================================================================================================
# B2 — KILL#5: PK DÜŞTÜYSE SAYI YAYILMAZ
# ==================================================================================================
def test_B2_gercek_R_006_oynayinca_DUSER_ve_HICBIR_SAYI_YAYILMAZ(tmp_path, sandbox_state):
    sonuc = _kos(tmp_path, r_kaydirma=0.06)
    assert sonuc["kontrol"]["gecti"] is False, sonuc["kontrol"]
    assert sonuc["gecti"] is False
    assert sonuc["yayin_engeli"], sonuc
    assert any("kill#5" in x for x in sonuc["yayin_engeli"])

    md = pk2.rapor_metni(sonuc)
    assert "PK DÜŞTÜ" in md
    # İŞLEM BAŞINA HİÇBİR SAYI: gölge R, gerçek R, giriş fiyatı, çıkış nedeni tablosu YOK.
    for tk in SENTETIK_TICKERLAR:
        assert f"{BEKLENEN_R[tk]:.6f}" not in md, (tk, md)
    assert "## İşlem başına" not in md
    assert "101.0" not in md and "202.0" not in md
    for alan in pk2.BASTIRILAN:
        assert alan in md.split("Bastırılan alanlar")[-1][:400], alan


def test_B2_gecti_True_ise_tablo_YAYILIR(tmp_path, sandbox_state):
    """Bastırma yalnız DÜŞTÜĞÜNDE: geçen bir PK'nın sayısını saklamak da körlük olurdu."""
    md = pk2.rapor_metni(_kos(tmp_path))
    assert "PK DÜŞTÜ" not in md
    assert "## İşlem başına" in md
    assert f"{BEKLENEN_R['AAPL']:.6f}" in md


# ==================================================================================================
# B3 — ÇIPLAK AYNA SINIFI DÜŞÜRÜLMEZ (kill#3), İKİ ORTALAMA AYRI PAYDADAN
# ==================================================================================================
def test_B3_ciplak_sinif_AYRI_sayilir_ama_DUSURULMEZ(tmp_path, sandbox_state):
    sonuc = _kos(tmp_path)
    assert sonuc["dolum_sinifi_dagilimi"] == {"dogrulanmis": 1, "kismi": 0, "ciplak": 1}
    # KILL#3: çıplak işlem HEPSİ paydasında DURUR.
    assert sonuc["kontrol"]["n_cift"] == 2
    assert "MSFT" in {c["ticker"] for c in sonuc["kontrol"]["ciftler"]}
    # İKİNCİ ORTALAMA AYRI PAYDADAN: yalnız doğrulanmış dolumlu çiftler.
    d = sonuc["kontrol_dogrulanmis"]
    assert d["n_cift"] == 1 and {c["ticker"] for c in d["ciftler"]} == {"AAPL"}
    assert d["ort_mutlak_fark_r"] != sonuc["kontrol"]["ort_mutlak_fark_r"] or d["n_cift"] == 2


def test_B3_iki_ortalama_da_raporda_ADIYLA_durur(tmp_path, sandbox_state):
    md = pk2.rapor_metni(_kos(tmp_path))
    assert "hepsi" in md and "doğrulanmış dolum" in md


# ==================================================================================================
# C1 — CANLI state/ ALTINA YAZIM YOK
# ==================================================================================================
def test_C1_repo_state_altindaki_state_dizini_BLOK(tmp_path):
    kok = pk2.depo_koku()
    with pytest.raises(pk2.Blok, match="state/"):
        pk2._state_izni(kok / "state")
    with pytest.raises(pk2.Blok, match="state/"):
        pk2._state_izni(kok / "state" / "pk2")
    pk2._state_izni(tmp_path / "gecici")      # kök dışı: geçer


def test_C1_kosum_CANLI_state_agacini_DEGISTIRMEZ(tmp_path, sandbox_state):
    canli = pk2.depo_koku() / "state"
    once = sorted(p.name for p in canli.iterdir())
    _kos(tmp_path)
    assert sorted(p.name for p in canli.iterdir()) == once
    assert not (canli / "golge_icra.jsonl").exists()
    assert not (canli / "golge_icra_acik.json").exists()


# ==================================================================================================
# C2 — REJİM KAPISININ KAYNAĞI BEYANLIDIR
# ==================================================================================================
def test_C2_rejim_kapisi_kaynagi_OLCULENLE_uyumlu(tmp_path, sandbox_state):
    """Bugün `meridian.regime.regime_ok` YOK (TSK-184 uçuşta) → beyanlı kopya. Yarın doğarsa bu
    çivi kırmızıya DÖNMEZ: beyanı ÖLÇÜLENLE karşılaştırır, sabit bir cevabı dayatmaz."""
    from meridian import regime as regime_mod
    kaynak = pk2.rejim_kapisi_kaynagi()
    assert kaynak["motorda_fonksiyon_var"] is hasattr(regime_mod, "regime_ok")
    assert kaynak["kullanilan"] in ("meridian.regime.regime_ok",
                                    "pk3_selef.rejim_of (beyanlı kopya)")
    assert _kos(tmp_path)["rejim_kapisi"]["kullanilan"] == kaynak["kullanilan"]


# ==================================================================================================
# C3 — KOMUT SATIRI SÖZLEŞMESİ (ops sözleşmesi `main()` değil KOMUT SATIRIdır)
# ==================================================================================================
def test_C3_son_10_KOMUT_SATIRINDAN_gevsetilemez():
    """Küme sayısı ve isimleri bir bayrakla değiştirilemez (eşik/popülasyon gevşetme yasağı)."""
    yardim = pk2.main.__doc__ or ""
    assert "0 geçti" in yardim
    with pytest.raises(SystemExit):
        pk2.main(["--bars-dizin", "x", "--state-dizin", "y", "--cikti-dizin", "z",
                  "--n-gercek", "2"])


def test_C3_main_operatorun_kosacagi_BICIMDE_0_ve_2(tmp_path, sandbox_state, monkeypatch):
    """Sabitler YAMANIR, bayrak eklenmez: `son_n_gercek` onları ÇAĞRI ANINDA çözdüğü için
    mini-vaka gerçekten yamayı ölçer (emsal: `pk3_selef.suz_049`)."""
    monkeypatch.setattr(pk2, "N_GERCEK", 2)
    monkeypatch.setattr(pk2, "BEKLENEN_TICKERLAR", SENTETIK_TICKERLAR)
    bars = tmp_path / "barlar"
    _sentetik_barlar(bars)
    cikti = tmp_path / "cikti"

    def _argv(girdi, st):
        return ["--girdi", str(girdi), "--bars-dizin", str(bars),
                "--params", str(DONMUS_PARAMS_DIZIN), "--state-dizin", str(tmp_path / st),
                "--cikti-dizin", str(cikti)]

    assert pk2.main(_argv(_sentetik_girdi(tmp_path / "g0"), "st0")) == 0
    assert pk2.main(_argv(_sentetik_girdi(tmp_path / "g1", r_kaydirma=0.06), "st1")) == 2
    yazilan = sorted(p.name for p in cikti.iterdir())
    assert sum(1 for a in yazilan if a.startswith("sonuc_")) >= 1, yazilan
    assert sum(1 for a in yazilan if a.startswith("rapor_")) >= 1, yazilan


def test_C1_ithal_meridian_obs_u_TETIKLEMEZ_ve_state_ACMAZ(tmp_path):
    """Betiği İTHAL ETMEK canlı deftere yazan modülü yüklememeli (emsal: v461'in aynı çivisi).

    Modül başında `meridian` ithalleri var; `obs`/`loop`/`alpaca` zinciri açılsaydı bir `import`
    bile canlı `state/`e yazabilirdi — ajanın pytest-dışı koşumu vakasının sınıfı.
    """
    import os
    import subprocess

    betik = SANDBOX / "pk2_gercek.py"
    ortam = dict(os.environ, MERIDIAN_ROOT=str(tmp_path), PYTHONPATH=str(KOK))
    kod = ("import sys, json, importlib.util;"
           f"spec=importlib.util.spec_from_file_location('p', r'{betik}');"
           "m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m);"
           "print(json.dumps({'obs': 'meridian.obs' in sys.modules,"
           " 'loop': 'meridian.loop' in sys.modules,"
           " 'alpaca': 'meridian.adapters.alpaca' in sys.modules}))")
    r = subprocess.run([sys.executable, "-c", kod], capture_output=True, text=True,
                       cwd=str(tmp_path), env=ortam)
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert json.loads(r.stdout.strip().splitlines()[-1]) == {
        "obs": False, "loop": False, "alpaca": False}
    assert not (tmp_path / "state").exists(), "ithal `state/` açtı"


def test_C3_girdi_varsayilani_DONMUS_dosyadir():
    """`--girdi` verilmezse reçete taze bir klonda da aynı girdiyi okur (mutlak yol gömülmez)."""
    assert pk2.girdi_varsayilan() == DONMUS_GIRDI
    # PK (2)'NİN VARSAYILANI CANLI v5'TİR (§D1): gerçek işlemler o kuşakta doğdu.
    assert pk2.params_varsayilan() == pk2.params_v5_dizin()
    assert pk2.params_varsayilan() == SANDBOX / "pk2_gercek" / "girdi" / "params_v5"
    assert pk2.bars_varsayilan() == SANDBOX / "pk2_gercek" / "girdi" / "bars"


# ==================================================================================================
# D1 — PARAMETRE SINIFI: İKİ DONMUŞ KAYNAK, İKİ AYRI KİMLİK KAPISI
# ==================================================================================================
# NİÇİN İKİ SINIF (tur-1 §Kaygı 2, Rol-1'in koşumunu DURDURAN hata). PK (3) "selef" ayağı
# EDG-049'un planlarını yeniden doğurur ve o planlar `edg032c` düğme kuşağında (v3) doğdu; o ayağın
# parametre kimliği künye kıyasıdır. PK (2) "gerçek" ayağı ise CANLI yolun kendi işlemlerini ölçer
# ve o işlemler `strategy_version=5` ile doğdu. İkisini TEK kaynağa bağlamak, gölgeyi gerçek
# işlemin doğmadığı bir kuşakla yönetmek demekti — Rol-1'in koşumu tam da bu yüzden
# "BLOKLANDI: donmuş sözleşme sha uyuşmuyor (goal.yaml)" ile durdu: v5 dizininin goal'ü edg032c
# künyesinin kaydıyla elbette tutmaz. Kimlik kapısı SINIFA GÖRE değişir, GEVŞEMEZ:
#   `edg032c_donmus`   → künye kıyası AYNEN (pk3_selef.donmus_parametreler)
#   `canli_v5_donmus`  → künye kıyası YOK, girdi manifestosu (`girdi/SHA256SUMS`) kıyası VAR
# Üçüncü bir dizin ya da bir DOSYA verilirse hata AÇIKTIR: "hangi sınıf" sorusu tahmin edilmez.
def test_D1_iki_donmus_dizin_SINIFIYLA_cozulur():
    """İki kabul edilen kaynak ADIYLA çözülür; ikisi de gerçekten var."""
    assert pk2.parametre_sinifi_coz(pk2.params_edg032c_dizin()) == "edg032c_donmus"
    assert pk2.parametre_sinifi_coz(pk2.params_v5_dizin()) == "canli_v5_donmus"
    assert pk2.PARAMS_SINIFLARI == ("edg032c_donmus", "canli_v5_donmus")
    for d in (pk2.params_edg032c_dizin(), pk2.params_v5_dizin()):
        assert d.is_dir(), d
        for ad in ("strategy.yaml", "goal.yaml", "bounds.yaml"):
            assert (d / ad).exists(), (d, ad)


def test_D1_params_DOSYA_ya_da_UCUNCU_dizin_verilince_ACIK_HATA(tmp_path):
    """`--params` bir DİZİN alır. Dosya ya da tanınmayan dizin → `Blok`, ve mesaj İKİ kabul edilen
    kaynağı da ADIYLA sayar (sessizce birine düşmek, ölçüleni uydurulana çevirirdi)."""
    with pytest.raises(pk2.Blok, match="DİZİN"):
        pk2.parametre_sinifi_coz(pk2.params_v5_dizin() / "strategy.yaml")
    with pytest.raises(pk2.Blok, match="tanınmayan parametre dizini"):
        pk2.parametre_sinifi_coz(tmp_path)
    try:
        pk2.parametre_sinifi_coz(tmp_path)
    except pk2.Blok as e:
        assert "params_v5" in str(e) and "params_donmus" in str(e), str(e)


def test_D1_v5_sinifi_KUNYE_KIYASINI_ATLAR_ama_MANIFESTOYU_dogrular():
    """PK (2)'nin DOĞRU kaynağı: canlı v5. Künye kıyası ATLANIR (yoksa koşum hiç başlamaz) ama
    kimlik kapısı KALKMAZ — girdi manifestosu doğrulanır ve sha'lar sonuca yazılır."""
    taban = pk2.parametre_tabani(pk2.params_v5_dizin())
    assert taban["sinif"] == "canli_v5_donmus"
    assert taban["version"] == 5
    assert taban["kunye_yolu"] is None, "v5 sınıfında künye kıyası olmamalı"
    assert set(taban["sha256"]) == {"goal.yaml", "strategy.yaml", "bounds.yaml"}
    man = pk2.params_v5_dizin().parent / pk2.MANIFEST_ADI
    satirlar = dict((p.split()[1], p.split()[0]) for p in man.read_text().splitlines() if p.split())
    for ad, sha in taban["sha256"].items():
        assert satirlar[f"{pk2.params_v5_dizin().name}/{ad}"] == sha
    # hücre UYDURULMAZ: v5'te goal/strategy'nin KENDİ değerleri ölçülür, künyeden enjekte edilmez
    assert taban["hucre_kaynagi"] == "canli_v5_dosyalari"
    assert taban["params"]["position_size_r"] == 0.5


def test_D1_v5_sinifinda_MANIFESTO_BOZULUNCA_kirmizi(tmp_path, monkeypatch):
    """SHA256SUMS bir BEYAN değil bir KAPIdır: v5 dosyalarından biri kurcalanırsa koşum BAŞLAMAZ."""
    girdi = tmp_path / "girdi"
    sahte = girdi / "params_v5"
    sahte.mkdir(parents=True)
    for ad in ("strategy.yaml", "goal.yaml", "bounds.yaml"):
        (sahte / ad).write_bytes((pk2.params_v5_dizin() / ad).read_bytes())
    (girdi / pk2.MANIFEST_ADI).write_text("".join(
        f"{hashlib.sha256((sahte / ad).read_bytes()).hexdigest()}  params_v5/{ad}\n"
        for ad in ("strategy.yaml", "goal.yaml", "bounds.yaml")), encoding="utf-8")
    monkeypatch.setattr(pk2, "params_v5_dizin", lambda betik=None: sahte)
    assert pk2.parametre_tabani(sahte)["sinif"] == "canli_v5_donmus"   # temizken geçer

    (sahte / "goal.yaml").write_text((sahte / "goal.yaml").read_text() + "\n# kurcalandı\n")
    with pytest.raises(pk2.Blok, match="sha256 uyuşmuyor"):
        pk2.parametre_tabani(sahte)


def test_D1_v5_dizininde_MANIFESTO_YOKSA_BLOK(tmp_path, monkeypatch):
    """"Ölçemedim" ile "eşleşmedi" AYRI hükümdür — ikisi de `Blok`."""
    sahte = tmp_path / "girdi" / "params_v5"
    sahte.mkdir(parents=True)
    for ad in ("strategy.yaml", "goal.yaml", "bounds.yaml"):
        (sahte / ad).write_bytes((pk2.params_v5_dizin() / ad).read_bytes())
    monkeypatch.setattr(pk2, "params_v5_dizin", lambda betik=None: sahte)
    with pytest.raises(pk2.Blok, match="manifestosu"):
        pk2.parametre_tabani(sahte)


def test_D1_edg032c_sinifi_KUNYE_KIYASINI_SURDURUR(tmp_path, monkeypatch):
    """PK (3) kaynağında künye kapısı AYNEN durur — v5 için gevşetilen şey oraya sızmaz."""
    taban = pk2.parametre_tabani(pk2.params_edg032c_dizin())
    assert taban["sinif"] == "edg032c_donmus" and taban["version"] == 3
    assert taban["kunye_yolu"] and taban["kunye_taban"], "künye kıyası kayboldu"

    sahte = tmp_path / "params_donmus"
    sahte.mkdir(parents=True)
    for ad in ("strategy.yaml", "goal.yaml", "bounds.yaml"):
        (sahte / ad).write_bytes((pk2.params_edg032c_dizin() / ad).read_bytes())
    (sahte / "goal.yaml").write_text((sahte / "goal.yaml").read_text() + "\n# kurcalandı\n")
    monkeypatch.setattr(pk2, "params_edg032c_dizin", lambda betik=None: sahte)
    with pytest.raises(pk2.Blok, match="sha uyuşmuyor"):
        pk2.parametre_tabani(sahte)


def test_D1_sonuc_kunyesinde_SINIF_ve_UYUM_durur(tmp_path, sandbox_state, monkeypatch):
    """Sonuç künyesi hangi kuşağın koştuğunu SÖYLER: sınıf adı + sha'lar + `parametre_uyumu`.
    Sentetik planlar `strategy_version=5` taşır → v5 kaynağıyla uyum TRUE, v3 ile FALSE."""
    s5 = _sentetik_v5_dizin(tmp_path / "g5", monkeypatch)
    d5 = _kos(tmp_path / "k5", params_dizin=s5)
    assert d5["parametre_kaynagi"]["sinif"] == "canli_v5_donmus"
    assert d5["parametre_kaynagi"]["strategy_version"] == 5
    assert d5["parametre_kaynagi"]["sha256"]["strategy.yaml"]
    assert d5["parametre_ayrismasi"]["parametre_uyumu"] is True
    assert d5["parametre_ayrismasi"]["n_ayrisan"] == 0

    d3 = _kos(tmp_path / "k3", params_dizin=pk2.params_edg032c_dizin())
    assert d3["parametre_kaynagi"]["sinif"] == "edg032c_donmus"
    assert d3["parametre_ayrismasi"]["parametre_uyumu"] is False
    assert d3["parametre_ayrismasi"]["n_ayrisan"] == 2


# ==================================================================================================
# D2 — BAR VARSAYILANI: DONMUŞ DİZİN, KÜÇÜK HARF, KAPSAM ÖLÇÜLÜR
# ==================================================================================================
def test_D2_bars_varsayilani_DONMUS_dizindir_ve_KUCUK_HARFTIR():
    """Yükleyicinin beklediği ad biçimi ÖLÇÜLÜR, varsayılmaz (`adapters.data._cache_path`)."""
    from meridian.adapters import data as data_adapter

    bars = pk2.bars_varsayilan()
    assert bars == SANDBOX / "pk2_gercek" / "girdi" / "bars"
    assert bars.is_dir()
    adlar = sorted(p.name for p in bars.glob("*.csv"))
    assert adlar == [f"{t.lower()}.csv" for t in sorted(
        (*pk2.BEKLENEN_TICKERLAR, "BDX", "LLY", data_adapter.INDEX_SYMBOL))]
    assert data_adapter._cache_path("SPY").name == "spy.csv", "yükleyici küçük harf beklemiyor"


def test_D2_donmus_barlar_ISLEM_PENCERESINI_kapsar():
    """Tur-1 PK (2)'yi ölçemedi çünkü yerel önbellek 2026-07-28'de bitiyordu. Donmuş girdi o
    boşluğu kapatıyor mu — ÖLÇÜLÜR (uydurma yasağı: kapsam tahmin edilmez)."""
    veri = json.loads(DONMUS_GIRDI.read_text(encoding="utf-8"))
    secilen = pk2.son_n_gercek(veri["trades"])
    planlar = pk2.plan_haritasi(veri["plans"])
    d_ilk = min(str(planlar[str(t["plan_id"])]["date"]) for t in secilen)
    cikis_son = max(str(t["ts_close"])[:10] for t in secilen)
    assert (d_ilk, cikis_son) == ("2026-08-19", "2026-09-11")

    bars = pk2.bars_varsayilan()
    for t in (*pk2.BEKLENEN_TICKERLAR, "SPY"):
        df = pd.read_csv(bars / f"{t.lower()}.csv", parse_dates=["date"])
        assert str(df["date"].max().date()) >= cikis_son, (t, str(df["date"].max().date()))
        # ATR ısınması: D'den ÖNCE en az LOOKBACK_BAR seans olmalı
        assert int((df["date"] < d_ilk).sum()) >= gi.LOOKBACK_BAR, t


def test_D2_kapsamayan_bar_SESSIZCE_DUSMEZ_sinifiyla_durur(tmp_path, sandbox_state, monkeypatch):
    """Barı işlem penceresini karşılamayan işlem `bar_yok` sınıfıyla RAPORDA durur; listeden
    silinmez ve ortalamanın paydasını sessizce küçültmez (tur-1'in `endeks_seansi_yok` ikizi).

    NE ÖLÇER, NE ÖLÇMEZ (ölçüldü — mutasyon m17b, tur-2). Bu çivi RAPORLAMA SÖZLEŞMESİNİ ölçer
    ("ölçülemeyen işlem listede DURUR"), kapsam KAPISINI değil: sembolün CSV'si hiç yoksa kapı
    kaldırılsa bile gölge motoru aynı hükmü `giris_reddi="bar_yok"` ile aşağıda söyler, yani
    kapıyı kaldıran mutasyon bu çiviyi YEŞİL bırakır. Isırdığı mutasyon işlemi listeden
    DÜŞÜRENdir (m17c); kapının kendi dalını bir sonraki çivi (ATR ısınması) ölçer. Bu ayrım
    yazılı: beyansız bir "yeşil", ölçülmemiş bir kapıyı ölçülmüş gösterirdi."""
    bars = tmp_path / "barlar"
    _sentetik_barlar(bars)
    (bars / "msft.csv").unlink()                      # MSFT'in barı YOK
    girdi = _sentetik_girdi(tmp_path / "girdi")
    d = pk2.kos(girdi, bars, _sentetik_v5_dizin(tmp_path / "g5", monkeypatch),
                tmp_path / "gecici_state", n_gercek=2, beklenen_tickerlar=SENTETIK_TICKERLAR)
    kayit = {k["ticker"]: k for k in d["islemler"]}
    assert set(kayit) == set(SENTETIK_TICKERLAR), "işlem listeden DÜŞTÜ"
    assert str(kayit["MSFT"]["olculemedi"]).startswith("bar_yok"), kayit["MSFT"]["olculemedi"]
    assert kayit["MSFT"]["bar_kapsami"] == {"var": False, "son_seans": None, "isinma_n": 0,
                                            "yeterli": False}
    assert kayit["AAPL"]["bar_kapsami"]["var"] is True
    assert kayit["AAPL"]["bar_kapsami"]["yeterli"] is True
    assert kayit["AAPL"]["bar_kapsami"]["isinma_n"] >= gi.LOOKBACK_BAR
    assert d["n_olculemeyen"] == 1 and d["n_gercek"] == 2


def test_D2_ATR_ISINMASI_yetmeyen_bar_da_kapsam_sinifiyla_durur(tmp_path, sandbox_state,
                                                                monkeypatch):
    """KAPININ AYIRT EDİCİ DALI. "Dosya hiç yok" hâlini gölge motoru zaten `giris_reddi="bar_yok"`
    ile söyler — o dalda kapı bir şey EKLEMEZ. Barlar VAR ama ATR ısınması yetmiyorsa gölge
    motorunun söyleyeceği şey başkadır; kapı bu hâli `bar_yok:<sembol>:isinma_<n><<eşik>` diye
    ADIYLA sınıflar ve ısınma eşiği MOTORUN KENDİ sabitinden (`golge_icra.LOOKBACK_BAR`) gelir.
    Bu çivi olmasaydı kapıyı kaldıran bir mutasyon YEŞİL kalırdı (ölçüldü: m17, tur-2)."""
    bars = tmp_path / "barlar"
    _sentetik_barlar(bars)
    tam = pd.read_csv(bars / "msft.csv")
    tam.tail(6).to_csv(bars / "msft.csv", index=False)   # D'den önce yalnız 4 seans kalır
    girdi = _sentetik_girdi(tmp_path / "girdi")
    d = pk2.kos(girdi, bars, _sentetik_v5_dizin(tmp_path / "g5", monkeypatch),
                tmp_path / "gecici_state", n_gercek=2, beklenen_tickerlar=SENTETIK_TICKERLAR)
    kayit = {k["ticker"]: k for k in d["islemler"]}
    assert kayit["MSFT"]["olculemedi"] == f"bar_yok:MSFT:isinma_4<{gi.LOOKBACK_BAR}"
    assert kayit["MSFT"]["bar_kapsami"] == {"var": True, "son_seans": D_GIRIS, "isinma_n": 4,
                                            "yeterli": False}
    assert kayit["MSFT"]["golge_r"] is None and kayit["MSFT"]["golge_tani"] is None, \
        "kapı geçildi — gölge geçişi hiç DENENMEMELİYDİ"
    assert d["n_olculemeyen"] == 1


# ==================================================================================================
# D3 — ORTAK YARDIMCI: İKİ BETİK TEK KAYNAKTAN (tur-1 §Kaygı 4 ve 9)
# ==================================================================================================
def test_D3_iki_betik_AYNI_ortak_modulu_kullanir():
    """`_state_izni`nin ikinci kopyası kaldırıldı: iki betik de AYNI modül nesnesini taşır."""
    import pk3_selef as pk3

    assert pk2._ortak is pk3._ortak
    assert pk2.Blok is pk3.Blok is pk2._ortak.Blok


def test_D3_state_kapisi_TEK_KAYNAKTAN_iki_betigi_de_isirir(tmp_path, monkeypatch):
    """AYRIŞMA ÇİVİSİ: ortak yardımcı yamandığında İKİ betik de yamayı görmeli. Kopya geri
    gelirse (ya da biri kendi satır-içi kapısına dönerse) bu çivi kırmızıya döner."""
    import pk3_selef as pk3

    class Nisan(Exception):
        pass

    cagrilan: list = []

    def sahte(state_dizin, kok=None):
        cagrilan.append(str(state_dizin))
        raise Nisan("ortak kapı")

    monkeypatch.setattr(pk2._ortak, "state_izni", sahte)
    with pytest.raises(Nisan):
        pk2.kos(DONMUS_GIRDI, tmp_path / "bars", pk2.params_v5_dizin(), tmp_path / "s1")
    with pytest.raises(Nisan):
        pk3.kos(tmp_path / "yok.json", tmp_path / "bars",
                SANDBOX / "pk3_selef" / "params_donmus" / "strategy.yaml", tmp_path / "s2")
    assert len(cagrilan) == 2, cagrilan


def test_D3_ortak_kapi_DEPONUN_state_agacini_reddeder(tmp_path):
    """Kapının KENDİSİ gevşemedi: mesaj ve hüküm iki betikte de aynı (v469 D2 ile aynı ölçü)."""
    with pytest.raises(pk2.Blok, match="state/ ağacının altında"):
        pk2._ortak.state_izni(KOK / "state" / "gecici")
    with pytest.raises(pk2.Blok, match="state/ ağacının altında"):
        pk2._ortak.state_izni(KOK / "state")
    assert pk2._ortak.state_izni(tmp_path / "disarida") == tmp_path / "disarida"


def test_D3_iki_betik_de_DEPO_KOKUNU_yola_koyar():
    """Kaygı 9: `meridian` ithali cwd'ye BIRAKILMAZ — iki betik de kökü `sys.path[0]`a koyar."""
    import pk3_selef as pk3

    assert pk2.YOL == pk3.YOL == (str(KOK), str(SANDBOX))
    sys.path.remove(str(KOK))
    try:
        assert pk2._ortak.yolu_kur(pk2.__file__) == (str(KOK), str(SANDBOX))
        assert sys.path[0] == str(KOK)
    finally:
        if str(KOK) not in sys.path:
            sys.path.insert(0, str(KOK))
