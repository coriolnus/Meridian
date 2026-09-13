"""v469 — EDG-2026-088 PK (3) SELEF ölçüm betiğinin çivileri
(`research/olcumler/edg088_golge_pilot/pk3_selef.py`).

NE ÇİVİLENİYOR. Betik 049'un uyuyan `pullback` planlarını DONMUŞ `edg032c` parametreleriyle
yeniden doğurup gölge motorundan geçirir ve İŞARET kıyası yapar. Dört yüzey ayrı ayrı ısırır:

  A. DİLİM SÜZGECİ + DONMUŞ GİRDİNİN KİMLİĞİ — gerçek 049 artefaktında `setup=='pullback'` TAM
     6 satır ve toplam R −4,725. Süzgeç gevşerse (başka kurulum sızarsa) bu çivi kırmızıya döner:
     ölçülen POPÜLASYON değişmiş demektir ve kartın PK'sı adı aynı kalan başka bir sınamaya
     dönüşürdü. Aynı bölümde girdinin kimliği de ölçülür: git-izli parametre kopyası hem kendi
     `SHA256SUMS` manifestosuyla hem `edg032c` künyesiyle BAYT-EŞ kalmalıdır (A4, A5).
  B. DOĞUM → GÖLGE → İŞARET ZİNCİRİ — sentetik iki planlık mini-vaka. Barlar UYDURMA ama zincir
     GERÇEK: `cf_backfill._plans_for_session` planı kesitsel `rs_map` ile doğurur,
     `golge_icra.adim` üretimin giriş/çıkış yasalarıyla yürütür. Bir plan bilinen bir STOP
     kırılmasına, öteki bilinen bir HEDEFE koşar; R'ler el hesabıyla birebir doğrulanır.
  C. ÖLÇÜLEMEDİ YOLU — doğmayan plan sessizce DÜŞMEZ: `durum='olculemedi'`, `esles=None` ve komut
     satırı çıkışı 2. "Ayrıştı" ile "koşulmadı" aynı çıkışı paylaşır ama AYNI OLGU DEĞİLDİR ve
     rapor ikisini ayrı adlandırır (kart notu 2026-09-08).
  D. İZOLASYON — betik canlı `state/` altına HİÇBİR ŞEY yazmaz (`sandbox_state` ağacı koşum
     öncesi/sonrası birebir aynı) ve deponun `state/` ağacına yönlendirilirse BAŞLAMAZ.

SKIPIF YOKTUR — VE BU BİR DÜZELTMEDİR. Donmuş sözleşme artık depoda durur
(`research/olcumler/edg088_golge_pilot/pk3_selef/params_donmus/`, git-İZLİ), o yüzden A4/B1/B2/D1
taze bir klonda da koşar. Önceki sürümde bu DÖRT çivi `state/` altındaki izsiz bir yola bağlıydı
ve o yolu görmeyen her checkout'ta `skipif` ile atlanırdı: suite "yeşil" görünürken ölçümün
yarısı hiç koşmazdı (inceleme bulgusu 2026-09-13, kart ilkesi EDG-2026-059 — donmuş girdi çalışma
ağacına değil depoya bağlanır).

BARLAR NEDEN TAKVİMDEN ÜRETİLİYOR: `adapters.data.sanitize_bars` geçerli bir XNYS seansı olmayan
tarihin satırını DÜŞÜRÜR ve `validate_bars` onu SERT bulgu sayar. Sentetik tarihler uydurulsaydı
fikstür ya sessizce kısalır ya da endeks kapısı kapanır ve "plan doğmadı" sonucu ölçümün değil
fikstürün kusuru olurdu. Bu yüzden takvim TEK KAYNAKTAN (`adapters.data._sessions`) alınır.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib

import pandas as pd
import pytest

from meridian import indicators as ind, strategy as strat
from meridian.adapters import data as data_adapter

REPO = pathlib.Path(__file__).resolve().parents[1]
BETIK = REPO / "research/olcumler/edg088_golge_pilot/pk3_selef.py"
KAYNAK_049 = REPO / "research/olcumler/edg049_dormant_2026-08-23/islemler_tam_dormant_acik.json"
#: DONMUŞ SÖZLEŞMENİN GİT-İZLİ KOPYASI — betiğin `--params` varsayılanının işaret ettiği dizin.
#: Yol DEPO KÖKÜNDEN türetilir (mutlak yol gömülü değil): aynı çivi ana checkout'ta, worktree'de
#: ve taze bir klonda AYNI dosyayı ölçer. Kopyanın kendi manifestosu `SHA256SUMS` yanındadır ve
#: A5 onu künyeyle birlikte doğrular.
DONMUS = REPO / "research/olcumler/edg088_golge_pilot/pk3_selef/params_donmus"
SHA256SUMS_YOLU = DONMUS / "SHA256SUMS"

#: Sentetik evren: iki HEDEF (planı doğacak) + dört DOLGU. Dolgular kesitsel `rs_rating`in
#: PAYDASIDIR — tek başına iki sembolle göreli güç sıralaması anlamsızdır ve `entry.rs_rating_min`
#: kapısı fikstürün kendi dar evreninden ötürü kapanırdı.
KAYIP_TK, KAZANC_TK = "AAPL", "MSFT"
DOLGU_TK = ("XOM", "JNJ", "PG", "KO")
D_SEANS = "2024-06-03"          # sentetik doğum günü (gerçek bir XNYS seansı)
N_GECMIS = 340                  # tarama penceresi (`.tail(340)`) + 52 haftalık ısınma için yeterli
N_GELECEK = 6                   # gölge takibi için D sonrası seans sayısı


def _modul():
    """Ölçüm betiğini modül olarak yükle. `research/` bir paket DEĞİLDİR (ölçümler birbirinden
    yalıtık dizinlerdir), o yüzden dosya yolundan yüklenir — `sys.path`e research/ eklemek
    ölçüm dizinlerini birbirinin ithal alanına sokardı."""
    spec = importlib.util.spec_from_file_location("pk3_selef_v469", BETIK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def pk3():
    return _modul()


# ==================================================================================================
# SENTETİK FİKSTÜR
# ==================================================================================================
def _takvim() -> list[str]:
    """D'yi içeren gerçek XNYS seans dizisi: `N_GECMIS` geçmiş (D dahil) + `N_GELECEK` gelecek."""
    ses = sorted(data_adapter._sessions())
    i = ses.index(D_SEANS)
    return ses[i - (N_GECMIS - 1): i + 1 + N_GELECEK]


def _cerceve(kapanislar, tarihler, hacim: int = 1_000_000, gerilme: float = 0.0008) -> pd.DataFrame:
    """Kapanış dizisinden OHLCV çerçevesi. Açılış BİR ÖNCEKİ KAPANIŞTIR (boşluksuz) ve bar içi
    gerilme dardır: geniş bir gerilme ATR'yi şişirir, ATR de stop genişliğini — ve `pullback`
    kurulumunun R:R tabanı (`guard.DISCIPLINE_MIN_RR`) o zaman fikstürde asla geçilemezdi."""
    satir, onceki = [], None
    for t, c in zip(tarihler, kapanislar):
        o = onceki if onceki is not None else c * 0.999
        satir.append({"date": pd.Timestamp(t), "open": round(o, 4),
                      "high": round(max(o, c) * (1 + gerilme), 4),
                      "low": round(min(o, c) * (1 - gerilme), 4),
                      "close": round(c, 4), "volume": hacim})
        onceki = c
    return pd.DataFrame(satir)


def _pullback_kapanislari(n: int = N_GECMIS) -> list[float]:
    """`strategy.evaluate_pullback`ı ATEŞLEYEN kapanış yolu — ÖLÇÜLEREK seçildi, ezberden değil.

    Şekil: uzun ve SAKİN bir yükseliş (52 haftalık trend şablonunun altı koşulunu da doldurur),
    sonra 4 barlık keskin ralli (20 barlık swing zirvesini yükseltir → R:R tabanı geçilir), sonra
    6 barlık geri çekilme (fiyat 20 günlük ortalamaya iner → `dist20` bandı) ve D'de yukarı dönüş
    (`close > close[-2]` şartı)."""
    taban = n - 4 - 6 - 1
    c = [100.0 * (1 + 0.0015) ** i for i in range(taban)]
    for _ in range(4):
        c.append(c[-1] * 1.024)
    for _ in range(6):
        c.append(c[-1] * (1 - 0.012))
    c.append(c[-1] * 1.004)
    return c


def _plan_seviyeleri(gecmis: pd.DataFrame) -> tuple[float, float, float]:
    """Fikstürün doğuracağı planın (tetik, stop, hedef) seviyeleri — ÜRETİMİN KENDİ tarayıcısından.

    Gelecek barlar bu seviyelerden TÜRETİLİR: "bilinen stop kırılması" ve "bilinen hedef" ancak
    seviyeler ölçüldüğünde bilinebilir. `rs_rating_value` burada 90 verilir çünkü seviyeler ondan
    BAĞIMSIZDIR (yalnız skor ve kapı ona bakar); gerçek koşumda kesitsel `rs_map` konuşur ve
    konuşmazsa plan doğmaz — o hâl de bu dosyanın C çivisiyle ayrıca ölçülür."""
    sig = strat.evaluate_pullback(gecmis, {"entry.rs_rating_min": 70, "entry.min_score": 60,
                                           "stop_loss_atr_mult": 2.0, "exit.profit_target_r": 2.5,
                                           "position_size_r": 0.5}, 90, "?")
    assert sig is not None, "sentetik geçmiş pullback sinyali doğurmuyor — fikstür bozuk"
    return float(sig.entry_trigger), float(sig.stop), float(sig.profit_target)


def _gelecek_kayip(tetik: float, stop: float, tarihler, hacim: int) -> list[dict]:
    """D+1'de dolan, D+2'de STOP'a düşen gelecek. Çıkış `stop` seviyesinde olur (açılış stopun
    ÜSTÜNDE, bar içi düşük stopun ALTINDA) → R tam olarak −1,0'dır ve el hesabıyla bilinir."""
    g = [{"date": pd.Timestamp(tarihler[0]), "open": round(tetik * 1.0005, 4),
          "high": round(tetik * 1.004, 4), "low": round(tetik * 0.999, 4),
          "close": round(tetik * 1.002, 4), "volume": hacim},
         {"date": pd.Timestamp(tarihler[1]), "open": round(stop * 1.005, 4),
          "high": round(stop * 1.006, 4), "low": round(stop * 0.97, 4),
          "close": round(stop * 0.975, 4), "volume": hacim}]
    duz = g[-1]["close"]
    for t in tarihler[2:]:
        g.append({"date": pd.Timestamp(t), "open": duz, "high": round(duz * 1.001, 4),
                  "low": round(duz * 0.999, 4), "close": duz, "volume": hacim})
    return g


def _gelecek_kazanc(tetik: float, hedef: float, tarihler, hacim: int) -> list[dict]:
    """D+1'de dolan, D+2'de HEDEFE dokunan gelecek. Açılış hedefin ALTINDA kalır ki çıkış `target`
    (hedef seviyesinden) olsun — açılış hedefin üstünde olsaydı `target_gap` yolundan açılış
    fiyatıyla çıkılır ve R barın uydurma açılışına bağlanırdı."""
    g = [{"date": pd.Timestamp(tarihler[0]), "open": round(tetik * 1.0005, 4),
          "high": round(tetik * 1.004, 4), "low": round(tetik * 0.999, 4),
          "close": round(tetik * 1.002, 4), "volume": hacim},
         {"date": pd.Timestamp(tarihler[1]), "open": round(tetik * 1.005, 4),
          "high": round(hedef * 1.01, 4), "low": round(tetik * 1.004, 4),
          "close": round(hedef * 1.005, 4), "volume": hacim}]
    duz = g[-1]["close"]
    for t in tarihler[2:]:
        g.append({"date": pd.Timestamp(t), "open": duz, "high": round(duz * 1.001, 4),
                  "low": round(duz * 0.999, 4), "close": duz, "volume": hacim})
    return g


def _sentetik_evren(bars_dizin: pathlib.Path) -> dict:
    """Sentetik bar önbelleğini yaz ve fikstürün ölçülmüş seviyelerini döndür.

    Dolgular ve endeks SAKİN bir yükseliştedir: endeks rejimi `trend_up` ve maruziyet bütçesi > 0
    olmalıdır, aksi hâlde gölge kolu `regime_flip` ile erken kapanır ve "bilinen stop / bilinen
    hedef" iddiası fikstürün rejimine kurban giderdi.
    """
    bars_dizin.mkdir(parents=True, exist_ok=True)
    tak = _takvim()
    gecmis_t, gelecek_t = tak[:N_GECMIS], tak[N_GECMIS:]

    gecmis = _cerceve(_pullback_kapanislari(), gecmis_t)
    tetik, stop, hedef = _plan_seviyeleri(gecmis)

    def _yaz(ticker: str, df: pd.DataFrame) -> None:
        df.to_csv(bars_dizin / f"{ticker.lower()}.csv", index=False)

    _yaz(KAYIP_TK, pd.concat([gecmis, pd.DataFrame(
        _gelecek_kayip(tetik, stop, gelecek_t, 1_000_000))], ignore_index=True))
    _yaz(KAZANC_TK, pd.concat([gecmis, pd.DataFrame(
        _gelecek_kazanc(tetik, hedef, gelecek_t, 1_000_000))], ignore_index=True))
    # DOLGULAR: yatay seyir → 63 günlük getirileri ~0, yani iki hedef sıralamanın TEPESİNDE kalır.
    for tk in DOLGU_TK:
        _yaz(tk, _cerceve([50.0] * len(tak), tak))
    # ENDEKS: sakin yükseliş (rejim trend_up, bütçe > 0).
    _yaz(data_adapter.INDEX_SYMBOL,
         _cerceve([400.0 * (1 + 0.0012) ** i for i in range(len(tak))], tak))
    return {"tetik": tetik, "stop": stop, "hedef": hedef, "d": D_SEANS}


def _sentetik_049(yol: pathlib.Path, tickerlar) -> pathlib.Path:
    """Sentetik bir 049 dilimi: her sembol için bir satır (`plan_id` doğum gününü taşır)."""
    yol.write_text(json.dumps([
        {"plan_id": f"P-{D_SEANS}-{tk}", "ticker": tk, "setup": "pullback",
         "r_multiple": -0.5, "exit_reason": "stop", "ts_open": D_SEANS, "ts_close": D_SEANS,
         "score": 90} for tk in tickerlar], ensure_ascii=False))
    return yol


def _dilim_boyutu(pk3, n: int) -> None:
    """Sentetik fikstürün dilim boyutunu modül sabitine yaz.

    NEDEN MODÜL SABİTİNE VE NEDEN GÜVENLİ: `BEKLENEN_N` Rol-1 hükmünün dondurduğu ÜRETİM
    değeridir (6) ve KOMUT SATIRINDAN gevşetilemez — sentetik fikstür 2-3 planlıktır, yani üretim
    kapısı olduğu gibi dursaydı mini-vaka hiç koşamazdı. `pk3` fikstürü her testte TAZE bir modül
    yükler (`importlib`), o yüzden bu yazım başka bir teste SIZMAZ; `test_A1` taze modülde değerin
    hâlâ 6 olduğunu ayrıca ölçer."""
    pk3.BEKLENEN_N = n


# ==================================================================================================
# A. DİLİM SÜZGECİ — gerçek artefakt
# ==================================================================================================
def test_A1_dilim_suzgeci_GERCEK_049_artefaktinda_TAM_ALTI_SATIR_verir(pk3):
    """049'un `pullback` dilimi TAM 6 satır, toplam R −4,725 ve altı sembol Rol-1 hükmündekiler.

    SÜZGEÇ GEVŞERSE BU ÇİVİ ÖTER: `suz_049` kurulumu süzmeyi bırakırsa 885 satır döner ve boyut
    kapısı `Blok` atar; bir başka kurulum sızarsa sayı 6'dan çıkar. Ölçülen popülasyonun kimliği
    budur — kartın PK'sı onun üstüne kuruludur."""
    assert pk3.BEKLENEN_N == 6, "üretim dilimi Rol-1 hükmüyle 6'ya donuktur"
    satirlar = json.loads(KAYNAK_049.read_text())
    dilim = pk3.suz_049(satirlar)
    assert len(dilim) == 6
    assert sorted(s["ticker"] for s in dilim) == ["F", "LNG", "OXY", "V", "WBD", "ZBH"]
    assert round(sum(s["r_multiple"] for s in dilim), 4) == pk3.BEKLENEN_TOPLAM_R
    assert all(s["setup"] == "pullback" for s in dilim)
    # 049 satırlarında stop/profit_target YOKTUR — Rol-1 hükmü "türetme YOK" der, bu çivi o
    # yokluğun ölçüsüdür: alan doğarsa türetme cazibesi de doğar ve hüküm sessizce ihlal edilir.
    assert not any("stop" in s or "profit_target" in s for s in dilim)


def test_A2_dilim_BOYUT_KAPISI_baska_kurulumda_BLOK_atar(pk3):
    """Boyut kapısı GERÇEKTEN bir kapıdır: aynı artefakt başka bir kurulumla süzülünce 6 çıkmaz
    ve betik BAŞLAMAZ. Kapı yoksa betik sessizce başka bir popülasyonu ölçerdi."""
    satirlar = json.loads(KAYNAK_049.read_text())
    with pytest.raises(pk3.Blok, match="beklenen boyutta değil"):
        pk3.suz_049(satirlar, kurulum="breakout_vcp")
    with pytest.raises(pk3.Blok, match="beklenen boyutta değil"):
        pk3.suz_049(satirlar, beklenen_n=5)


def test_A3_dogum_gunu_PLAN_KIMLIGINDEN_okunur(pk3):
    """D planın TARAMA seansıdır ve kimlikte durur; `ts_open` (dolum günü) DEĞİLDİR."""
    assert pk3.dogum_gunu("P-2023-02-13-V") == "2023-02-13"
    assert pk3.dogum_gunu("P-2026-06-11-F") == "2026-06-11"
    assert pk3.dogum_gunu("P-2024-06-03-AAPL-pullback") == "2024-06-03"
    with pytest.raises(pk3.Blok):
        pk3.dogum_gunu("T00001")


def test_A4_donmus_parametreler_KUNYE_SHA_ILE_dogrulanir(pk3, tmp_path):
    """Parametrelerin kimliği KÜNYEDEN doğrulanır: `edg032c` künyesi EDG-022 kopyalarının
    sha256'larını kendi içinde taşır ve betik onları ölçerek karşılaştırır. Hücre değerleri de
    (slot / boyut / ısı zarfı) künyeden OKUNUR — bu dosyada da, betikte de sayı olarak yazılı
    değildir (TEK-KAYNAK YASASI)."""
    taban = pk3.donmus_parametreler(DONMUS / "strategy.yaml")
    assert taban["version"] == 3
    assert taban["params"]["position_size_r"] == taban["hucre"]["position_size_r"]
    assert taban["sha256"]["strategy.yaml"].startswith("9f3e4732315abe52")
    assert taban["by_regime"] and all(not v for v in taban["by_regime"].values())

    # KURCALANMIŞ KOPYA REDDEDİLİR: sha kapısı bir etiket değil bir ölçüdür.
    sahte = tmp_path / "donmus"
    sahte.mkdir()
    for f in ("goal.yaml", "bounds.yaml", "strategy.yaml"):
        (sahte / f).write_text((DONMUS / f).read_text())
    (sahte / "strategy.yaml").write_text((DONMUS / "strategy.yaml").read_text() + "\n# kurcalandı\n")
    with pytest.raises(pk3.Blok, match="sha uyuşmuyor"):
        pk3.donmus_parametreler(sahte / "strategy.yaml")


def test_A5_gitizli_kopya_SHA256SUMS_ve_KUNYE_ile_BAYT_ES_varsayilan_ORAYA_bakar(pk3):
    """Git-izli donmuş kopya İKİ BAĞIMSIZ kayıtla bayt-eş kalır ve `--params` varsayılanı onu
    gösterir.

    NEDEN İKİ KAYIT BİRDEN: `SHA256SUMS` kopyanın KENDİ beyanıdır, `edg032c` künyesi donmuş
    tabanın BİRİNCİL kaydıdır. Yalnız birine bakmak ötekinin sessizce kaymasına izin verirdi;
    ikisi birden ölçülünce kopyayı kurcalayan her değişiklik en az bir kaydı yalanlar. Manifest
    bozulursa (ya da kopya değişirse) bu çivi kırmızıya döner — kart girdisi "donmuş" iddiasını
    ancak ölçülen bir eşitlik taşıyabilir.

    VARSAYILAN YOL da burada ısırılır: betik mutlak yol gömmemeli, kendi dizininden türetmelidir.
    Türetme kırılırsa taze bir klonda koşum sessizce eski (izsiz) yola düşerdi."""
    beyan = {}
    for satir in SHA256SUMS_YOLU.read_text().splitlines():
        if satir.strip():
            sha, ad = satir.split()
            beyan[ad] = sha
    assert sorted(beyan) == ["bounds.yaml", "goal.yaml", "strategy.yaml"]

    olculen = {ad: pk3.sha256(DONMUS / ad) for ad in beyan}
    assert olculen == beyan, "git-izli donmuş kopya SHA256SUMS manifestosuyla bayt-eş değil"

    kunye = json.loads(pk3.kunye_yolu(BETIK).read_text())
    kayit = kunye["config_sha256"]["sandbox_kaynagi_edg022"]
    assert {ad: kayit[ad] for ad in beyan} == beyan, "manifest ile edg032c künyesi ayrıştı"

    # `--params` varsayılanı: git-izli kopyayı gösterir, mutlak yol GÖMÜLÜ DEĞİLDİR.
    assert pk3.params_varsayilan(BETIK) == DONMUS / "strategy.yaml"
    assert pk3.params_varsayilan(BETIK).exists()
    # Betik metninde ana checkout'un izsiz `state/` yoluna ATIF KALMADI (reçete + sabitler dâhil).
    assert "edg022_evren_kisit" not in BETIK.read_text()


# ==================================================================================================
# B. DOĞUM → GÖLGE → İŞARET — sentetik iki planlık mini-vaka
# ==================================================================================================
def test_B1_sentetik_iki_plan_DOGUM_GOLGE_ISARET_zincirini_kosar(pk3, tmp_path, sandbox_state):
    """İki sentetik plan doğar, gölgeden geçer ve R'leri EL HESABIYLA doğrulanır.

    KAYIP kolu stopa düşer → R tam `−1,0` (çıkış stop seviyesinde, giriş fiyatı da stop da
    defterde yazılı). KAZANÇ kolu hedefe dokunur → R pozitif ve satırın KENDİ alanlarından
    yeniden hesaplanabilir. İşaret kıyası bu yüzden bir kol için True, öteki için False'tur —
    kıyas ters çevrilirse İKİSİ BİRDEN döner ve bu çivi kırmızıya gider."""
    _dilim_boyutu(pk3, 2)
    sev = _sentetik_evren(tmp_path / "bars")
    kaynak = _sentetik_049(tmp_path / "049.json", (KAYIP_TK, KAZANC_TK))

    sonuc = pk3.kos(kaynak, tmp_path / "bars", DONMUS / "strategy.yaml",
                    tmp_path / "golge_state", kunye_p=pk3.kunye_yolu(BETIK))

    assert sonuc["n_ref"] == 2
    assert sonuc["n_olculen"] == 2, f"plan doğmadı/ölçülemedi: {sonuc['satirlar']}"
    by = {s["ticker"]: s for s in sonuc["satirlar"]}

    kayip = by[KAYIP_TK]
    assert kayip["cikis_neden_golge"] == "stop"
    assert kayip["r_golge"] == pytest.approx(-1.0, abs=1e-9)
    assert kayip["kayip_golge"] is True

    kazanc = by[KAZANC_TK]
    assert kazanc["cikis_neden_golge"] == "target"
    assert kazanc["r_golge"] > 0
    assert kazanc["kayip_golge"] is False

    # EL HESABI KİMLİĞİ: R satırın KENDİ fiyatlarından türer — betik ikinci bir R tanımı taşımaz.
    for tk in (KAYIP_TK, KAZANC_TK):
        satir = sonuc["golge"][f"P-{D_SEANS}-{tk}"]["satir"]
        beklenen = (satir["cikis_fiyat"] - satir["giris_fiyat"]) / (satir["giris_fiyat"] - satir["stop"])
        assert satir["R"] == pytest.approx(beklenen, abs=5e-5)
        assert satir["kurulum"] == "pullback" and satir["kol"] == "dormant"
        assert satir["bar_kaynak"] == pk3.BAR_KAYNAK
        assert satir["kaynak_bar_hash"], "PIT çapası kurulamadı — satır K dışına düşerdi"

    # DOĞUM ÜRETİM ŞEMASINDAN GELİR: plan sözlüğü betiğin kendi kurduğu bir şey DEĞİLDİR.
    plan = sonuc["golge"][f"P-{D_SEANS}-{KAYIP_TK}"]["plan"]
    assert plan["dormant_setup"] is True and plan["setup"] == "pullback"
    assert plan["id"] == f"P-{D_SEANS}-{KAYIP_TK}-pullback"
    assert plan["entry_trigger"] == pytest.approx(sev["tetik"], abs=1e-6)
    assert plan["stop"] == pytest.approx(sev["stop"], abs=1e-6)
    assert plan["gate_verdict"] in ("GO", "REVIEW", "NO_GO")

    # HÜKÜM: bir kol kazandı → 2/2 kayıp DEĞİL → AYRIŞTI (kör), ölçülemedi değil.
    assert sonuc["durum"] == "ayristi"
    assert sonuc["esles"] is False
    assert sonuc["n_kayip_golge"] == 1


def test_B2_dogmayan_plan_OLCULEMEDI_diye_raporlanir_ve_CIKIS_2(pk3, tmp_path, sandbox_state):
    """Doğmayan plan SESSİZCE DÜŞMEZ: `durum='olculemedi'`, `esles=None`, çıkış 2 ve tanı satırı
    o seansta ne olduğunu söyler. Sessiz düşürme, PK'yı doğan planların üzerinden hüküm veren —
    yani eşiği hak etmeden geçen — bir sınamaya çevirirdi."""
    _dilim_boyutu(pk3, 3)
    _sentetik_evren(tmp_path / "bars")
    # Üçüncü sembol bir DOLGUDUR (yatay seyir): pullback tarayıcısı orada sinyal üretemez.
    kaynak = _sentetik_049(tmp_path / "049.json", (KAYIP_TK, KAZANC_TK, DOLGU_TK[0]))

    sonuc = pk3.kos(kaynak, tmp_path / "bars", DONMUS / "strategy.yaml",
                    tmp_path / "golge_state", kunye_p=pk3.kunye_yolu(BETIK))
    assert sonuc["durum"] == "olculemedi"
    assert sonuc["esles"] is None
    assert sonuc["n_olculen"] == 2 and sonuc["n_ref"] == 3

    dolgu = sonuc["golge"][f"P-{D_SEANS}-{DOLGU_TK[0]}"]
    assert dolgu["olculemedi"] == "dogmadi"
    assert dolgu["dogum_tani"]["sembol_bari_var"] is True          # bar VARDI, sinyal yoktu
    assert dolgu["dogum_tani"]["rejim"]

    # KOMUT SATIRI ÇIKIŞI: ölçülemedi → 2 (eşleşti yalnız 0 verir).
    # `--params` BİLEREK VERİLMİYOR: operatörün koşacağı biçim budur ve varsayılanın git-izli
    # kopyayı bulduğu ancak böyle ölçülür (varsayılan kırılırsa bu çağrı `Blok` ile çıkış 1 verir).
    rc = pk3.main(["--kaynak", str(kaynak), "--bars-dizin", str(tmp_path / "bars"),
                   "--state-dizin", str(tmp_path / "golge_state2"),
                   "--cikti-dizin", str(tmp_path / "cikti")])
    assert rc == 2
    uretilen = sorted(p.name for p in (tmp_path / "cikti").iterdir())
    assert any(a.startswith("sonuc_") and a.endswith(".json") for a in uretilen)
    assert any(a.startswith("rapor_") and a.endswith(".md") for a in uretilen)
    rapor = next((tmp_path / "cikti").glob("rapor_*.md")).read_text()
    assert "ÖLÇÜLEMEDİ" in rapor and "esles=None" in rapor


# ==================================================================================================
# C. İŞARET YÜKLEMİ — kıyasın kendisi
# ==================================================================================================
def test_C1_kiyasla_ISARET_YUKLEMI_uc_degerlidir(pk3):
    """`kiyasla` üç hükmü de AYIRIR. Bu çivi işaret kıyasının MUTASYON yüzeyidir: `R < 0`
    yüklemi ters çevrilirse "hepsi kayıp" dalı yanlış tarafa düşer ve üç iddiadan en az ikisi
    kırmızıya gider."""
    ref = [{"plan_id": "P-2024-01-02-AA", "ticker": "AA", "r_multiple": -1.0,
            "exit_reason": "stop", "ts_open": "2024-01-03", "ts_close": "2024-01-04"},
           {"plan_id": "P-2024-01-02-BB", "ticker": "BB", "r_multiple": -0.5,
            "exit_reason": "stop", "ts_open": "2024-01-03", "ts_close": "2024-01-04"}]

    def _golge(r1, r2):
        return {"P-2024-01-02-AA": {"satir": {"R": r1, "cikis_neden": "stop"}, "plan": {"id": "x"}},
                "P-2024-01-02-BB": {"satir": {"R": r2, "cikis_neden": "stop"}, "plan": {"id": "y"}}}

    hepsi_kayip = pk3.kiyasla(ref, _golge(-0.9, -0.4))
    assert hepsi_kayip["durum"] == "eslesti" and hepsi_kayip["esles"] is True
    assert hepsi_kayip["n_kayip_golge"] == 2
    assert all(s["isaret_esit"] for s in hepsi_kayip["satirlar"])

    biri_kazandi = pk3.kiyasla(ref, _golge(-0.9, +0.4))
    assert biri_kazandi["durum"] == "ayristi" and biri_kazandi["esles"] is False
    assert biri_kazandi["n_kayip_golge"] == 1
    assert [s["isaret_esit"] for s in biri_kazandi["satirlar"]] == [True, False]

    biri_olculemedi = pk3.kiyasla(ref, _golge(-0.9, None))
    assert biri_olculemedi["durum"] == "olculemedi" and biri_olculemedi["esles"] is None
    assert biri_olculemedi["n_olculen"] == 1
    assert biri_olculemedi["satirlar"][1]["isaret_esit"] is None

    # Sıfır KAYIP DEĞİLDİR (uydurma yasağının işaret tarafı): R=0 bir kazanç/kayıp değil, düz çıkış.
    assert pk3.kayip_mi(0.0) is False and pk3.kayip_mi(None) is None and pk3.kayip_mi(-1e-9) is True


# ==================================================================================================
# D. İZOLASYON — canlı defter
# ==================================================================================================
def test_D1_kos_STATE_AGACINA_YAZMAZ(pk3, tmp_path, sandbox_state):
    """Koşum `sandbox_state` ağacına TEK BİR BAYT yazmaz: gölge defteri de SQLite arka ucu da
    `--state-dizin`e düşer (`store._state`/`storage.db_path` her çağrıda `config.STATE`ten türer).
    Ölçüm betiklerinin canlı deftere yazması bu deponun ölçülmüş bir vakasıdır — bu çivi onun
    tekrarını yapısal olarak yakalar."""
    _dilim_boyutu(pk3, 2)
    _sentetik_evren(tmp_path / "bars")
    kaynak = _sentetik_049(tmp_path / "049.json", (KAYIP_TK, KAZANC_TK))
    once = sorted(str(p.relative_to(sandbox_state)) for p in sandbox_state.rglob("*"))

    sonuc = pk3.kos(kaynak, tmp_path / "bars", DONMUS / "strategy.yaml",
                    tmp_path / "golge_state", kunye_p=pk3.kunye_yolu(BETIK))

    sonra = sorted(str(p.relative_to(sandbox_state)) for p in sandbox_state.rglob("*"))
    assert sonra == once, f"sandbox state ağacı değişti: {set(sonra) - set(once)}"
    # Gölge defteri GERÇEKTEN yazıldı — "hiçbir şey yazmadı" ile "doğru yere yazdı" AYRI olgudur.
    assert sonuc["n_olculen"] == 2
    assert list((tmp_path / "golge_state").rglob("golge_icra.jsonl")), \
        "gölge defteri --state-dizin altında yok — izolasyon çivisi boşta ölçüyor olabilir"


def test_D2_state_dizini_DEPONUN_state_agacinda_olamaz(pk3, tmp_path):
    """`--state-dizin` deponun `state/` ağacına yönlendirilirse betik BAŞLAMAZ. Kapı yoksa bir
    yazım hatası canlı gölge defterini sentetik satırlarla kirletirdi."""
    with pytest.raises(pk3.Blok, match="state/ ağacının altında"):
        pk3.kos(KAYNAK_049, tmp_path / "bars", DONMUS / "strategy.yaml", REPO / "state" / "gecici")
    with pytest.raises(pk3.Blok, match="state/ ağacının altında"):
        pk3.kos(KAYNAK_049, tmp_path / "bars", DONMUS / "strategy.yaml", REPO / "state")


# ==================================================================================================
# TARAYICI PK — fikstürün kendisi ölçüldü mü?
# ==================================================================================================
def test_E1_sentetik_gecmis_GERCEKTEN_pullback_dogurur():
    """FİKSTÜRÜN POZİTİF KONTROLÜ: sentetik geçmiş `evaluate_pullback`ı gerçekten ateşliyor ve
    kesitsel RS eşiği (`entry.rs_rating_min`, donmuş sözleşmede 70) sentetik evrende geçiliyor.

    Bu çivi olmadan B/C testleri "plan doğmadı" diye kırmızıya döndüğünde suçun FİKSTÜRDE mi
    BETİKTE mi olduğu bilinemezdi — ve yeşilken de tarayıcının çalıştığı ile hiçbir şey görmediği
    ayırt edilemezdi (v382'nin "boşta temiz" dersi)."""
    tak = _takvim()
    gecmis = _cerceve(_pullback_kapanislari(), tak[:N_GECMIS])
    assert ind.trend_template(gecmis).iloc[-1] >= 0.6
    tetik, stop, hedef = _plan_seviyeleri(gecmis)
    assert stop < tetik < hedef
    assert (hedef - tetik) / (tetik - stop) >= 2.0          # guard.DISCIPLINE_MIN_RR tabanı

    # Kesitsel RS: iki hedef sembol yatay dolguların ÜSTÜNDE sıralanır.
    son = gecmis["close"]
    getiri = {KAYIP_TK: float(son.iloc[-1] / son.iloc[-1 - strat.RS_LOOKBACK] - 1.0),
              KAZANC_TK: float(son.iloc[-1] / son.iloc[-1 - strat.RS_LOOKBACK] - 1.0)}
    getiri.update({tk: 0.0 for tk in DOLGU_TK})
    rs = ind.rs_rating(getiri)
    assert rs[KAYIP_TK] >= 70 and rs[KAZANC_TK] >= 70, f"sentetik RS eşiği geçmiyor: {rs}"
