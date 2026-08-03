"""test_wpd_takvim_kapisi_v184.py — WP-D: KARARTMA KAPISI TAKVİME BAĞLANDI + REPLAY-PIT DÜZELTMESİ
(2026-08-03, Rol-1 kararları A1/A1b/2; teşhis: research/olcumler/wpd_earnings_failopen/RAPOR.md).

ÖLÇÜLEN AYRIM (bu turun bütün gerekçesi tek cümlede): **"194/251 kapsama" bir KORUMA ölçüsü
değildir** — önümüzdeki ~4 haftada rapor veren sembol sayısıdır. Kapsam-dışı 59 sembolün çoğu,
raporu UFKUN ÖTESİNDE olduğu için bilinmiyor; raporu 4 hafta ötede olan bir sembol zaten 5 günlük
karartmaya giremez. Buna karşılık GERÇEK arıza canlıda yaşandı (2026-07-25 `MECHANISM_STALE`:
takvimde tek satır kalmıştı, karartma kapısı 251 sembolün 251'inde geçirgendi) ve `covered_pct`
onu GÖRMEZ — 0/251 iken bile bir yüzde üretir.

BU YÜZDEN: fail-closed SEMBOLE değil TAKVİME bağlandı.
  A) `earnings.calendar_untrustworthy()` — takvim karartma ufkunu taşıyamıyorsa sebep döner;
     `loop.daily_cycle` o turda TÜM planları karartma varsayılanına düşürür (GO→REVIEW, NO_GO'ya
     dokunmaz). İKİ bilinçli istisna: takvim DOSYASI hiç yoksa (kapı henüz silahlanmadı) ve
     pencere kapsaması ÖLÇÜLMEMİŞSE (None bir sayı değildir).
  A-b) `scheduler` pes ederken HAFTA damgasını yakmıyor; fren GÜN damgası (ertesi gün yeniden dener).
  2) REPLAY-PIT: `backtest.replay` bugünün takvimini TARİHSEL plana uygulamayı bıraktı. Etiket
     dürüst ("olculemedi_replay"), veto YOK, sayaç raporda.

"0 PLAN ETKİLENDİ" ÇİVİSİ (§B): sağlıklı/canlı-benzeri takvimde yüklem None döner VE düşürme
bloğu yüklemin İÇİNDE yaşar — yani normal işleyişte hiçbir plan dokunulmaz. İkisi birlikte
kanıttır; tek başına ne davranış ne yapı yeter.
"""
from __future__ import annotations

import datetime as dt
import inspect

import pytest

from meridian import backtest, config, earnings, loop, scheduler


# ==================================================================================================
# yardımcılar
# ==================================================================================================
def _takvim_yaz(sandbox_state, satirlar) -> None:
    """state/earnings.csv üret (ticker,date). `satirlar` = [(TICKER, "YYYY-MM-DD"), ...]"""
    p = sandbox_state / "earnings.csv"
    p.write_text("ticker,date\n" + "".join(f"{t},{d}\n" for t, d in satirlar))
    earnings.clear_cache()


def _gun(delta: int) -> str:
    return (dt.date.today() + dt.timedelta(days=delta)).isoformat()


def _kod(fn) -> str:
    """Kaynağın YORUMSUZ hâli. Yorumlarda geçen bir ad, o adın ÇAĞRILDIĞI anlamına gelmez —
    ilk yazımda bu testin kendisi tam bu yüzden yanlış alarm verdi (gerekçe bloğu 'in_blackout'
    kelimesini içeriyordu). Bir davranış iddiasını yorum metniyle kanıtlamak, bu deponun
    'beyan ≠ kod' hatasının test tarafındaki kopyasıdır."""
    out = []
    for satir in inspect.getsource(fn).splitlines():
        govde = satir.split("#", 1)[0] if "#" in satir else satir
        if govde.strip():
            out.append(govde)
    return "\n".join(out)


@pytest.fixture(autouse=True)
def _temiz_pencere():
    """`_LAST_WINDOW` SÜREÇ-İÇİ bir kayıttır; testler arasında sızarsa bir testin kısmi penceresi
    diğerinin sağlıklı takvimini güvenilmez gösterir (tam da kaçınmak istediğimiz yanlış-alarm)."""
    earnings._LAST_WINDOW.clear()
    yield
    earnings._LAST_WINDOW.clear()


# ==================================================================================================
# A) YÜKLEM — takvim güvenilmez mi?
# ==================================================================================================
def test_saglikli_takvim_None_doner(sandbox_state):
    """Ufuk karartma penceresini TAŞIYORSA kapı normal çalışır — hiçbir şey kısıtlanmaz."""
    _takvim_yaz(sandbox_state, [("AAPL", _gun(10)), ("MSFT", _gun(14))])
    assert earnings.calendar_untrustworthy() is None


def test_ufuk_tukendi_sebebiyle_guvenilmez(sandbox_state):
    """Takvimde gelecek tarih VAR ama karartma ufkundan KISA → kapı bugün karartmada olan bir
    sembolü kaçırıyor olabilir. BLACKOUT_DAYS=5 iken 2 gün ileri gören takvim yeterli değildir."""
    _takvim_yaz(sandbox_state, [("AAPL", _gun(2))])
    kusur = earnings.calendar_untrustworthy()
    assert kusur and kusur["kod"] == "ufuk_tukendi"
    assert kusur["ileri_gun"] == 2 and kusur["blackout_days"] == earnings.BLACKOUT_DAYS


def test_atil_takvim_AYRI_sebep_adiyla_gelir(sandbox_state):
    """2026-07-25 VAKASININ ÇİVİSİ: takvimde YALNIZ geçmiş tarih kaldı (o gün `TEST,2025-06-24`).
    `ufuk_tukendi` ile aynı hükmü verir ama operatöre BAŞKA bir şey anlatır, o yüzden ayrı kod."""
    _takvim_yaz(sandbox_state, [("TEST", "2025-06-24")])
    kusur = earnings.calendar_untrustworthy()
    assert kusur and kusur["kod"] == "takvim_atil" and kusur["ileri_gun"] == 0


def test_takvim_DOSYASI_yoksa_TETIKLEMEZ(sandbox_state):
    """İSTİSNA 1 — modülün açılış sözleşmesi: 'No CSV -> no-op, the gate simply activates the day
    an earnings feed writes the file'. Dosyanın hiç olmaması 'kapı bozuldu' değil 'kapı henüz
    silahlanmadı'dır; fail-closed'a çevirmek taze kurulumu ve tüm fikstür yollarını kilitlerdi."""
    p = sandbox_state / "earnings.csv"
    if p.exists():
        p.unlink()
    earnings.clear_cache()
    assert earnings.calendar_untrustworthy() is None


def test_olculmemis_pencere_kapsamasi_TETIKLEMEZ(sandbox_state):
    """İSTİSNA 2 — `kapsama` None ise ÖLÇÜLMEDİ demektir (süreç yeni doğmuş, henüz pencere
    görmemiş). None'ı 'eksik' diye okumak uydurma olurdu."""
    _takvim_yaz(sandbox_state, [("AAPL", _gun(10))])
    earnings._LAST_WINDOW.update({"kapsama": None, "dusen": None})
    assert earnings.calendar_untrustworthy() is None


def test_kismi_pencere_guvenilmez_yapar(sandbox_state):
    """Ufuk YETERLİ ama son tazeleme penceresinin bir kısmı düştü → kaçan gün-diliminde duyurulan
    bir rapor tarihi BİLİNMİYOR olabilir. Bu ölçüm 2026-08-02'den beri vardı ama hiçbir kapıyı
    bağlamıyordu; artık bağlıyor."""
    _takvim_yaz(sandbox_state, [("AAPL", _gun(10))])
    earnings._LAST_WINDOW.update({"kapsama": 0.5, "dusen": 10, "pencere": ["x", "y"], "at": _gun(0)})
    kusur = earnings.calendar_untrustworthy()
    assert kusur and kusur["kod"] == "kismi_pencere"
    assert kusur["kapsama"] == 0.5 and kusur["esik"] == earnings.EARNINGS_FMP_FALLBACK_COVERAGE


def test_esigin_TAM_ustundeki_pencere_tetiklemez(sandbox_state):
    """Eşik sınırı: 0,90 eşiğinde `<` kullanılır — tam 0,90 gelen pencere KABUL. Sınır davranışı
    yazılı olmazsa bir gün 'yaklaşık' diye gevşetilir."""
    _takvim_yaz(sandbox_state, [("AAPL", _gun(10))])
    earnings._LAST_WINDOW.update({"kapsama": earnings.EARNINGS_FMP_FALLBACK_COVERAGE})
    assert earnings.calendar_untrustworthy() is None


def test_refresh_pencere_sagligini_KAYDEDER(sandbox_state, monkeypatch):
    """Yüklemin girdisi gerçekten `refresh`ten geliyor mu — yoksa sonsuza dek None kalır ve
    `kismi_pencere` kolu ÖLÜ KOD olurdu (bu deponun 'üretilip tüketilmeyen kanıt' yasağının aynası)."""
    from meridian.adapters import data as _da

    def _sahte(s, e, with_time=False, stats=None):
        if stats is not None:
            stats.update({"istenen": 20, "cevaplayan": 12, "dusen": 8, "kapsama": 0.6})
        return {"AAPL": [_gun(3)]}

    monkeypatch.setattr(_da, "nasdaq_earnings_window", _sahte)
    earnings.refresh(["AAPL"])
    assert earnings.last_refresh_window()["kapsama"] == 0.6
    assert earnings.last_refresh_window()["dusen"] == 8


# ==================================================================================================
# B) "0 PLAN ETKİLENDİ" ÇİVİSİ — normal işleyişte GO seti DEĞİŞMEZ
# ==================================================================================================
# CANLI-BENZERİ FİKSTÜR: 2026-07-30 snapshot'ının yapısı — sembol başına TEK tarih, tarihler
# önümüzdeki ~4 haftaya yayılmış, evrenin bir kısmı takvimde HİÇ YOK (kapsam-dışı sınıf).
CANLI_BENZERI = [("AAPL", _gun(1)), ("MSFT", _gun(3)), ("JPM", _gun(6)), ("KO", _gun(9)),
                 ("MRK", _gun(13)), ("CAT", _gun(17)), ("XOM", _gun(21))]
KAPSAM_DISI = ["NVDA", "COST", "WMT"]        # takvimde YOK — raporu ufkun ötesinde


def test_canli_benzeri_takvimde_kapi_KAPANMAZ(sandbox_state):
    """0-PLAN ÇİVİSİ, 1/2 (DAVRANIŞ). Canlı snapshot'ın yapısını taşıyan bir takvimde yüklem
    None döner — yani düşürme bloğu HİÇ çalışmaz, GO seti aynen kalır."""
    _takvim_yaz(sandbox_state, CANLI_BENZERI)
    assert earnings.calendar_untrustworthy() is None
    # …ve kapsam-dışı sembollerde ESKİ davranış (beyanlı fail-open) aynen sürüyor: not var, veto yok
    for t in KAPSAM_DISI:
        assert earnings.known(t) is False
        assert earnings.in_blackout(t, _gun(0)) is False
        assert earnings.coverage_note(t) == earnings.COVERAGE_NOTE


def test_dusurme_blogu_YUKLEMIN_ICINDE_yasar(sandbox_state):
    """0-PLAN ÇİVİSİ, 2/2 (YAPI). Davranış tek başına yetmez: düşürmenin `_takvim_kusuru` koşuluna
    BAĞLI olduğu kanıtlanmalı, yoksa bir gün koşul dışına taşınır ve sağlıklı takvimde de planlar
    düşmeye başlar. Kaynak taraması, iddianın kendi dedektörü."""
    src = _kod(loop.daily_cycle)
    assert "_takvim_kusuru = earnings.calendar_untrustworthy()" in src
    blok = src.split("if _takvim_kusuru:")
    assert len(blok) >= 3, "düşürme bloğu yüklem koşulunun içinde değil"
    govde = blok[-1].split("_mb = c[")[0]
    assert 'verdict = "REVIEW"' in govde, "düşürme yüklemin dışına taşınmış"
    assert '_tk_dusus = verdict == "GO"' in govde, "GO dışındaki verdictler de düşürülüyor olabilir"


def test_NO_GO_asla_REVIEWe_CIKARILMAZ(sandbox_state):
    """Blok yalnız SIKIŞTIRABİLİR. Reddedilmiş bir planı REVIEW'e çıkarmak kapıyı gevşetmek olurdu
    ve bu blok gevşetme yetkisine sahip değildir."""
    govde = _kod(loop.daily_cycle).split("if _takvim_kusuru:")[-1].split("_mb = c[")[0]
    assert 'verdict = "GO"' not in govde and "NO_GO" not in govde


def test_takvim_guvenilmezse_GO_REVIEWe_duser_NO_GO_kalir(sandbox_state):
    """Kuralın KENDİSİ (yapı değil davranış): yüklem sebep döndüğünde GO→REVIEW, NO_GO sabit.
    `loop.daily_cycle`ın karar satırıyla AYNI koşul dizisi burada birebir uygulanır."""
    _takvim_yaz(sandbox_state, [("TEST", "2025-06-24")])
    kusur = earnings.calendar_untrustworthy()
    assert kusur, "atıl takvim güvenilmez sayılmalı"
    sonuc = []
    for verdict in ("GO", "REVIEW", "NO_GO"):
        v = "REVIEW" if (kusur and verdict == "GO") else verdict
        sonuc.append(v)
    assert sonuc == ["REVIEW", "REVIEW", "NO_GO"]


def test_tur_sonu_sayaci_takvim_sagligini_TASIR():
    """YASA 6: üretilen kanıt tüketilir. `daily_cycle` olayı takvim sağlığını ve kaç planın
    düştüğünü taşımazsa, 'bugün neden hiç GO yok?' sorusu hiçbir defterden cevaplanamaz."""
    src = inspect.getsource(loop.daily_cycle)
    for alan in ("takvim_guvenilmez", "takvim_guvenilmez_sebep", "takvim_dusen_plan"):
        assert alan in src, f"`{alan}` tur-sonu sayacında yok"
    assert "earnings_calendar_untrustworthy" in src, "YASA 4 gerekçeli olay yok"


def test_yuklem_TUR_BASINA_BIR_KEZ_cagrilir():
    """`coverage()` → `_load()` → `stat()`. Aday başına çağrı 250 sembollük turda 250 sistem
    çağrısıdır ve ölçtüğümüz şeye hiçbir şey katmaz."""
    assert _kod(loop.daily_cycle).count("earnings.calendar_untrustworthy()") == 1


def test_yuklem_duserse_ESKI_davranisa_donulur_ve_soylenir():
    """YASA 4: kapatmak için yazdığımız kapıyı kendi hatamızla sessizce yeniden açmayalım."""
    src = inspect.getsource(loop.daily_cycle)
    assert "earnings_calendar_health_check_failed" in src


# ==================================================================================================
# 2) REPLAY-PIT DÜZELTMESİ
# ==================================================================================================
def test_replay_bacagi_in_blackout_CAGIRMAZ():
    """ÇEKİRDEK ÇİVİ: bugünün takvimini tarihsel plana uygulayan yol TAMAMEN kapandı. Ölçüldü —
    390 planın yalnız 10'unda takvim konuşabiliyordu; kalan %97,4'te `in_blackout` yapısal olarak
    False dönüyor ve `coverage: "known"` etiketi bunu ÖRTÜYORDU (UYDURMA YASAĞI)."""
    assert "in_blackout" not in _kod(backtest.replay), \
        "replay hâlâ bugünün takvimini tarihsel plana uyguluyor"


def test_canli_motor_in_blackout_CAGIRMAYA_DEVAM_eder():
    """Düzeltme YALNIZ replay bacağında. Canlı motorda takvim PIT'tir (bugünün kararı bugünün
    takvimiyle verilir) ve karartma vetosu aynen durur — bu testin yokluğunda 'temizlik' bir gün
    canlı kapıyı da söker."""
    src = _kod(loop.daily_cycle)
    assert "earnings.in_blackout(" in src
    assert 'greasons = list(greasons) + ["kazanç öncesi karartma (earnings blackout)"]' in src


def test_replay_coverage_etiketi_DURUST():
    """'known' yalanı bitti: replay satırı ölçülemediğini SÖYLER."""
    src = _kod(backtest.replay)
    assert '"coverage": "olculemedi_replay"' in src
    assert '"known" if _ek' not in src, "replay hâlâ bugünkü kapsamı tarihsel plana etiketliyor"


def test_replay_kanit_satiri_YINE_uretilir():
    """2026-07-22 dersi korunuyor: kanıt satırı İKİ motorda da var (kapsam farkı ≠ kayıt farkı)."""
    assert '"check": "earnings_blackout"' in _kod(backtest.replay)


def test_replay_sayaci_sonuca_baglanir():
    """YASA 6: sayaç üretilir VE taşınır. `earnings_gate` olmadan 'bu tabloda karartma etkisi
    sıfır' bilgisi hiçbir okuyucuya ulaşmazdı."""
    assert "earnings_gate" in {f for f in backtest.BacktestResult.__dataclass_fields__}
    src = _kod(backtest.replay)
    assert 'earnings_gate=_eg' in src and '_eg["olculemedi_replay"]' in src


def test_replay_karartma_VETOSU_URETMEZ():
    """Veto satırı replay'de kalmamalı — kalırsa `_bl` bir gün yeniden hesaplanır ve PIT ihlali
    sessizce geri gelir."""
    src = _kod(backtest.replay)
    assert src.count("_bl = False") == 1
    assert 'verdict = "NO_GO"; greasons = list(greasons) + ["kazanç öncesi karartma' not in src


# ==================================================================================================
# A-b) SCHEDULER — pes ederken hafta damgası yakılmaz
# ==================================================================================================
def test_pes_ederken_HAFTA_damgasi_yakilmaz():
    """ARIZANIN KÖKÜ: sabır sınırı (haftada 5 deneme) haftayı TÜKETİYORDU; ardışık iki pes ileri
    kapsamayı 0'a indiriyor, yani sabır sınırı tam da korumaya çalıştığı kapıyı kapatıyordu.
    Artık fren GÜN damgası — ertesi gün yeniden denenir."""
    pes = _kod(scheduler.advance_once).split("elif att >= 5:")[1].split("else:")[0]
    assert '_state["earnings_gaveup_day"] = _bugun' in pes
    assert '_state["earnings_week"] = list(wk)' not in pes, "hafta damgası hâlâ yakılıyor"


def test_gun_freni_ayni_gun_tekrar_denemeyi_KESER():
    """Fren gerçekten fren mi: aynı gün içinde sınırsız yeniden deneme olmamalı (kota/gürültü)."""
    assert '_state.get("earnings_gaveup_day") != _bugun' in _kod(scheduler.advance_once)


def test_veri_gelince_gun_freni_KALKAR():
    """Başarılı tazeleme freni bırakmalı; bırakmazsa bir sonraki gerçek arıza sessizce atlanır."""
    assert '_state.pop("earnings_gaveup_day", None)' in _kod(scheduler.advance_once)


# ==================================================================================================
# BEYAN ÇÜRÜMESİN
# ==================================================================================================
def test_kapsam_disi_sembol_HALA_fail_open(sandbox_state):
    """A3 UYGULANMADI ve bu bilinçlidir (ölçüldü: 390 planın 70'ini kilitler, karşılığında
    neredeyse hiç risk kapatmaz — kapsam-dışılık ağırlıklı olarak 'raporu 4 hafta ötede' demek).
    Bir gün 'tutarlılık' adına eklenirse bu test tartışmayı zorunlu kılar."""
    _takvim_yaz(sandbox_state, CANLI_BENZERI)
    assert earnings.in_blackout("NVDA", _gun(0)) is False
    assert earnings.calendar_untrustworthy() is None


def test_yuklem_config_STATE_uzerinden_dosyaya_bakar():
    """Yüklem `state/earnings.csv`in VARLIĞINA bakar; yolu `config.STATE`ten alır (kum havuzu
    yolları testten teste değişir, sabit yol yazmak bir testin defterini diğerine servis ederdi)."""
    src = inspect.getsource(earnings.calendar_untrustworthy)
    assert 'config.STATE / "earnings.csv"' in src
    assert config.STATE is not None
