"""test_wpd_kalanlar_v147.py — WP-D kalan üç kalem (2026-08-01).

A) FAIL-OPEN DARALTMA — kazanç takvimi evrenin 194/251'ini kapsıyor; kalan 57'de karartma kapısı
   SESSİZCE geçirgendi. Artık BEYANLI: kapsam-dışı planın `gate_reasons`ında not var, kapsam-içinde
   YOK, `daily_cycle` olayında sayaç var. KARAR YOLU DEĞİŞMEDİ (not NO_GO değil).

B) SEANS-İÇİ KESİNTİ TESPİTİ (5.3) — `barsarchive.gap_scan` seans içinde eksik dakika penceresi
   arar; sentetik boşlukta olay üretir, boşluksuz akışta SIFIR olay. Yalancı-pozitif kapısı
   (seyrek işlem gören sembol) ayrıca çivilenir.

C) EARNINGS 2-GÜN MARJ — kök neden BMO/AMC belirsizliği ya da tarih kayması DEĞİL, üç sayının
   aritmetiği (ileri pencere − kadans − karartma). Üçü de adlandırıldı, marj TÜRETİLDİ ve
   DAVRANIŞ DEĞİŞMEDİ çivisi burada. BMO/AMC daraltma YOLU var ama anahtarı KAPALI.
"""
from __future__ import annotations

import datetime as dt
import inspect
import json

import pytest

from meridian import barclock, barsarchive, earnings


# =================================================================================================
# A — FAIL-OPEN DARALTMA
# =================================================================================================
def _takvim(sandbox, rows):
    (sandbox / "earnings.csv").write_text("ticker,date\n" + "".join(f"{t},{d}\n" for t, d in rows))
    earnings.clear_cache()


def test_a_kapsam_disi_sembol_isaretlenir_kapsam_ici_isaretlenmez(sandbox_state):
    """İŞARETİN TEMEL SÖZLEŞMESİ: yalnız takvimde HİÇ tarihi olmayan sembol not alır."""
    fut = (dt.date.today() + dt.timedelta(days=40)).isoformat()
    _takvim(sandbox_state, [("AAA", fut)])
    assert earnings.coverage_note("AAA") is None            # kapsam İÇİNDE → not YOK
    assert earnings.coverage_note("BBB") == earnings.COVERAGE_NOTE
    assert earnings.coverage_note("bbb") == earnings.COVERAGE_NOTE   # büyük/küçük harf duyarsız


def test_a_isaret_bir_karar_degil_nottur(sandbox_state):
    """NOT METNİNİN BİÇİMİ SÖZLEŞMEDİR, süs değil.

    `analytics.gate_veto_tally` serbest gerekçe metninin İLK İKİ KELİMESİNİ "veto ailesi" diye
    sayar. Önek olmasaydı bu not, planların ~%23'ünde görünen ve kapının en sık vetosu gibi okunan
    bir kova açardı. İki çivi: (1) metin "NOT: " ile başlar, (2) ilk iki kelimeden oluşan aile
    anahtarı hâlâ NOT olduğunu söyler."""
    assert earnings.COVERAGE_NOTE.startswith("NOT: ")
    aile = " ".join(earnings.COVERAGE_NOTE.split()[:2])[:48]
    assert aile == "NOT: earnings_kapsami_yok"
    assert "NO_GO" not in earnings.COVERAGE_NOTE


def test_a_loop_notu_karar_yoluna_DOKUNMADAN_ekler():
    """KAYNAK ÇİVİSİ: not eklenen dal `verdict`e ASLA yazmaz. Bu, testin sonradan gevşetilmesini
    değil, karar yolunun sertleşmesini engeller — bu tur yalnız GÖRÜNÜRLÜK yetkisi aldı."""
    from meridian import loop
    src = inspect.getsource(loop.daily_cycle)
    i = src.index("if not _ek:")                  # KOD dalı (yorumdaki anmalar değil)
    dal = src[i:i + 220]
    assert "earnings.COVERAGE_NOTE" in dal and "_kapsam_disi += 1" in dal
    assert "verdict" not in dal.split("_kapsam_disi")[0], "not ekleyen dal karar değiştiriyor"


def test_a_sayac_dogru_sayar(sandbox_state):
    """SAYAÇ: `coverage_tally` bir TURUN planlanan sembollerini ölçer, evreni değil."""
    fut = (dt.date.today() + dt.timedelta(days=10)).isoformat()
    _takvim(sandbox_state, [("AAA", fut), ("BBB", fut)])
    t = earnings.coverage_tally(["AAA", "BBB", "CCC", "DDD", "EEE"])
    assert t["toplam"] == 5 and t["kapsanan"] == 2 and t["kapsam_disi"] == 3
    assert t["kapsam_disi_ornek"] == ["CCC", "DDD", "EEE"]
    assert t["takvim_bos"] is False


def test_a_takvim_bos_ucuncu_hal(sandbox_state):
    """'57 sembol eksik' ile 'takvim HİÇ yok' aynı sayıyla anlatılamaz."""
    earnings.clear_cache()
    t = earnings.coverage_tally(["AAA", "BBB"])
    assert t["kapsam_disi"] == 2 and t["takvim_bos"] is True


def test_a_daily_cycle_olayi_kapsam_sayacini_tasir():
    """OLAY ŞEMASI: `daily_cycle` sayacı taşımalı ve sayaç P3 bloğunun DIŞINDA tanımlanmalı —
    blok `halted`/`data_bad` koşuluna bağlı ve içinde tanımlansaydı halt turunda olay NameError
    ile düşerdi (yani halt günlerinde günlük döngünün kaydı hiç yazılmazdı)."""
    from meridian import loop
    src = inspect.getsource(loop.daily_cycle)
    assert "earnings_kapsami=_kapsam" in src
    assert '"kapsam_disi": _kapsam_disi' in src
    # tanım, P3 bloğundan (`with skills.pipeline_run("P3_PLAN"`) ÖNCE gelmeli
    assert src.index("_kapsam_disi = 0") < src.index('pipeline_run("P3_PLAN"')


# =================================================================================================
# B — SEANS-İÇİ KESİNTİ/BOŞLUK TESPİTİ (5.3)
# =================================================================================================
NY_ACIK = dt.datetime(2026, 7, 30, 14, 30, tzinfo=dt.timezone.utc)   # 09:30 ET (yaz saati), Perşembe


def _akis(baslangic, dakika, semboller=("AAA", "BBB"), atla=()):
    """Sentetik akış: her sembol her dakika bir bar. `atla` = (sembol|None, ilk_dk, son_dk) listesi;
    sembol None ise O DAKİKALARDA HİÇBİR sembol bar üretmez (akış kesintisi)."""
    rows = []
    for i in range(dakika):
        t = (baslangic + dt.timedelta(minutes=i)).isoformat().replace("+00:00", "Z")
        for s in semboller:
            if any((sem is None or sem == s) and a <= i <= b for sem, a, b in atla):
                continue
            rows.append((s, t))
    return rows


def test_b_bosluksuz_akista_sifir_olay():
    """TABAN: kesintisiz akış SIFIR boşluk üretmeli. (Yanlış pozitif = dedektörün ölümü.)"""
    r = barsarchive.gap_scan(as_of=NY_ACIK + dt.timedelta(minutes=62),
                             rows=_akis(NY_ACIK, 62))
    assert r["durum"] == "ok" and r["bosluk_sayisi"] == 0 and r["bosluklar"] == []
    assert r["sembol"] == 2 and r["gelen_bar"] > 0


def test_b_sentetik_akis_kesintisi_yakalanir():
    """AKIŞ KESİNTİSİ: 8 dakika boyunca HİÇBİR sembolden bar gelmedi."""
    rows = _akis(NY_ACIK, 62, atla=[(None, 20, 27)])
    r = barsarchive.gap_scan(as_of=NY_ACIK + dt.timedelta(minutes=62), rows=rows)
    akis = [b for b in r["bosluklar"] if b["tur"] == "akis"]
    assert len(akis) == 1
    b = akis[0]
    assert b["eksik_dk"] == 8 and b["sembol"] is None
    assert b["baslangic"].endswith("14:50:00+00:00") and b["bitis"].endswith("14:57:00+00:00")
    assert b["beklenen"] == r["pencere"]["beklenen_dk"] and b["gelen"] < b["beklenen"]
    # AKIŞ KESİNTİSİ SEMBOL BAŞINA TEKRAR RAPORLANMAZ — tek olay, 250 satır değil
    assert [x for x in r["bosluklar"] if x["tur"] == "sembol"] == []


def test_b_tek_sembol_susarsa_sembol_boslugu_uretilir():
    """SEMBOL BOŞLUĞU: akış akıyor ama BU sembol 6 dakika sustu."""
    rows = _akis(NY_ACIK, 62, atla=[("AAA", 30, 35)])
    r = barsarchive.gap_scan(as_of=NY_ACIK + dt.timedelta(minutes=62), rows=rows)
    sem = [b for b in r["bosluklar"] if b["tur"] == "sembol"]
    assert len(sem) == 1 and sem[0]["sembol"] == "AAA" and sem[0]["eksik_dk"] == 6
    assert [b for b in r["bosluklar"] if b["tur"] == "akis"] == []


def test_b_kisa_delik_gurultu_sayilir():
    """1-2 dakikalık delik BOŞLUK DEĞİLDİR (eşik `GAP_MIN_MIN`); gürültüyü olaya çevirmek,
    gerçek kesintiyi kendi uyarı seliyle gömmenin en hızlı yoludur."""
    rows = _akis(NY_ACIK, 62, atla=[("AAA", 30, 31)])
    r = barsarchive.gap_scan(as_of=NY_ACIK + dt.timedelta(minutes=62), rows=rows)
    assert r["bosluk_sayisi"] == 0


def test_b_seyrek_sembol_yanlis_pozitif_uretmez():
    """YALANCI-POZİTİF KAPISI: dakikalık bar yalnız İŞLEM olunca doğar. Her 3 dakikada bir işlem
    gören bir sembolde eksik dakika NORMALDİR — onu kesinti saymak beklentiyi UYDURMAK olurdu."""
    rows = [(s, (NY_ACIK + dt.timedelta(minutes=i)).isoformat().replace("+00:00", "Z"))
            for i in range(62) for s in ("AAA",) if i % 3 == 0]
    rows += _akis(NY_ACIK, 62, semboller=("BBB",))       # akış canlı: akis boşluğu doğmasın
    r = barsarchive.gap_scan(as_of=NY_ACIK + dt.timedelta(minutes=62), rows=rows)
    assert [b for b in r["bosluklar"] if b["sembol"] == "AAA"] == []


def test_b_seans_disinda_hukum_verilmez():
    """SEANS DIŞI: beklenen bar yoksa 'sıfır boşluk' demek sahte bir sağlık raporudur."""
    gece = dt.datetime(2026, 7, 30, 3, 0, tzinfo=dt.timezone.utc)
    r = barsarchive.gap_scan(as_of=gece, rows=[])
    assert r["durum"] == "seans_disi" and r["bosluklar"] == []
    assert r["pencere"]["beklenen_dk"] == 0


def test_b_arsiv_yoksa_suclama_yok(sandbox_state):
    """ARŞİV HİÇ AÇILMAMIŞ: arşivci koşmuyorsa 'akış koptu' demek yanlış suçlamadır."""
    r = barsarchive.gap_scan(as_of=NY_ACIK + dt.timedelta(minutes=62))
    assert r["durum"] == "arsiv_yok" and r["bosluklar"] == []


def test_b_disk_yolu_kuyruktan_okur_ve_yarim_satiri_dusurmez(sandbox_state):
    """DİSK YOLU: gün dosyasının SONU okunur; yarım ilk satır ATILIR, bozuk satır SAYILIR."""
    d = sandbox_state / barsarchive.ARCHIVE_DIR
    d.mkdir(parents=True)
    gun = barclock.session_date(NY_ACIK)
    satirlar = [json.dumps({"ticker": s, "t": t}) for s, t in _akis(NY_ACIK, 62, atla=[(None, 10, 20)])]
    satirlar.append("{bozuk json")
    (d / f"{gun}.jsonl").write_text("\n".join(satirlar) + "\n")
    r = barsarchive.gap_scan(as_of=NY_ACIK + dt.timedelta(minutes=62))
    assert r["durum"] == "ok" and r["bozuk_satir"] == 1
    assert any(b["tur"] == "akis" and b["eksik_dk"] == 11 for b in r["bosluklar"])


def test_b_scheduler_kancasi_olay_basar_ve_tekrarlamaz(sandbox_state, monkeypatch):
    """KANCA: ilk turda uyarı basılır, İKİNCİ turda AYNI boşluk için basılmaz (imza defteri)."""
    from meridian import scheduler
    rapor = barsarchive.gap_scan(as_of=NY_ACIK + dt.timedelta(minutes=62),
                                 rows=_akis(NY_ACIK, 62, atla=[(None, 20, 27)]))
    monkeypatch.setattr(barsarchive, "gap_scan", lambda *a, **k: rapor)
    gorulen = []
    monkeypatch.setattr(scheduler.store, "write_json", lambda *a, **k: None)
    import meridian.obs as obs
    monkeypatch.setattr(obs, "warn", lambda ev, **kw: gorulen.append((ev, kw)))
    scheduler._state.pop("intraday_gap_seen", None)
    scheduler._intraday_gap_check()
    assert [e for e, _ in gorulen] == ["intraday_gap_detected"]
    assert gorulen[0][1]["tur"] == "akis" and gorulen[0][1]["eksik_dk"] == 8
    assert gorulen[0][1]["aralik"] == "14:50-14:57Z"
    scheduler._intraday_gap_check()
    assert len(gorulen) == 1, "aynı boşluk her poll'de yeniden uyarı basıyor"
    assert scheduler._state["intraday_gap"]["bosluk_sayisi"] == 1
    scheduler._state.pop("intraday_gap_seen", None)
    scheduler._state.pop("intraday_gap", None)


def test_b_imza_defteri_sinirsiz_buyumez():
    from meridian import scheduler
    assert scheduler.GAP_SEEN_MAX <= 500
    src = inspect.getsource(scheduler._intraday_gap_check)
    assert "gorulen[-GAP_SEEN_MAX:]" in src, "imza defteri budanmıyor — uzun koşan worker'da sızıntı"


def test_b_pano_tuketicisi_bagli():
    """YASA 6: ölçüm üretiliyor ve OKUNUYOR — api `/api/diagnostics` → pano `RENDER.intraday`."""
    import pathlib
    api = (pathlib.Path(__file__).resolve().parent.parent / "meridian" / "api.py").read_text()
    js = (pathlib.Path(__file__).resolve().parent.parent / "meridian" / "web" / "app.js").read_text()
    assert '_intra["akis_boslugu"] = sched.get("intraday_gap")' in api
    assert "_gapRows(iq.akis_boslugu)" in js and "function _gapRows(" in js


def test_b_gap_scan_saf_kalir():
    """SAFLIK: ölçüm fonksiyonu olay BASMAZ ve dosya YAZMAZ — kayıt çağıranın işi. Aksi hâlde her
    pano anketi olay defterine satır düşerdi (ve testler canlı events.jsonl'a yazardı)."""
    src = inspect.getsource(barsarchive.gap_scan)
    assert "obs.warn" not in src and "obs.log" not in src and "write_json" not in src


# =================================================================================================
# C — EARNINGS 2-GÜN MARJ: KÖK NEDEN, TÜRETME, DAVRANIŞ-DEĞİŞMEDİ ÇİVİSİ
# =================================================================================================
def test_c_marj_turetilir_ve_bugunku_deger_iki_gundur():
    """TÜRETME ÇİVİSİ: marj SABİT YAZILMADI, üç girdiden TÜRETİLDİ — girdilerden biri değişirse
    marj kendiliğinden değişir. Bu testin beklentisi de LİTERAL DEĞİL, aynı aritmetiktir;
    beklenen değeri elle yazmak, türetmeyi test eden bir testte ikinci bir sabit doğururdu.

    GİRDİLER AYRICA KİLİTLİ: hangi üç sayının yürürlükte olduğu bir DAVRANIŞ kararıdır ve sessizce
    değişemez. 2026-08-01 mikro-turunda `REFRESH_FWD_DAYS` 14 → 21 yapıldı (Rol-1 kararı, yalnız
    FETCH penceresi; karartma semantiği DEĞİŞMEDİ) → marj 2 günden 9 güne çıktı."""
    assert (earnings.REFRESH_FWD_DAYS, earnings.REFRESH_CADENCE_DAYS, earnings.BLACKOUT_DAYS) == (21, 7, 5)
    assert earnings.margin_days() == (earnings.REFRESH_FWD_DAYS
                                      - earnings.REFRESH_CADENCE_DAYS
                                      - earnings.BLACKOUT_DAYS)
    # MARJIN İŞARETİ BİR DAVRANIŞ SÖZLEŞMESİDİR: marj ≤ 0 olduğu an `in_blackout` veri yokken
    # FAIL-OPEN'a düşer ve motor bilanço gününe pozisyonla girebilir (bkz. margin_days docstring).
    assert earnings.margin_days() > 0, "marj tükendi — karartma guard'ı fail-open'a düşer"
    src = inspect.getsource(earnings.margin_days)
    for yasak in ("return 2", "return 9"):
        assert yasak not in src, f"marj sabit yazılmış — türetme yok ({yasak})"


def test_c_tazeleme_penceresi_sabitlerden_okunur(monkeypatch, sandbox_state):
    """PENCERE TEK TANIMDAN: `refresh` artık satır-içi 7/14 literali taşımaz; `refresh_window`
    ile aynı kaynaktan okur. İki yerde iki pencere, `margin_days`ı sessizce yalan yapardı."""
    bugun = dt.date(2026, 7, 30)
    s, e = earnings.refresh_window(bugun)
    # BEKLENTİ DE SABİTLERDEN TÜRETİLİR: literal bir tarih yazmak, pencere sabiti değiştiği gün
    # (14→21, 2026-08-01) testin kendisini ikinci bir gerçek kaynağı hâline getirirdi.
    assert (s, e) == (str(bugun - dt.timedelta(days=earnings.REFRESH_BACK_DAYS)),
                      str(bugun + dt.timedelta(days=earnings.REFRESH_FWD_DAYS)))
    assert (s, e) == ("2026-07-23", "2026-08-20"), "bugünkü sabitlerle beklenen pencere değişti"
    gorulen = {}
    from meridian.adapters import data as da

    def _sahte(start, end, **k):
        gorulen.update(start=start, end=end, kw=k)
        return {}
    monkeypatch.setattr(da, "nasdaq_earnings_window", _sahte)
    monkeypatch.setattr(earnings, "refresh_from_fmp", lambda t: 0)
    earnings.refresh(["AAA"])
    bs, be = earnings.refresh_window()
    assert gorulen["start"] == bs and gorulen["end"] == be
    assert gorulen["kw"].get("with_time") is True

    src = inspect.getsource(earnings.refresh)
    for lit in ("timedelta(days=7)", "timedelta(days=14)", "timedelta(days=21)"):
        assert lit not in src, f"`refresh` satır-içi pencere literali taşıyor ({lit})"


def test_c_kok_neden_bmo_amc_degil_yazili():
    """KÖK NEDEN BEYANI: iki aday (BMO/AMC belirsizliği, tarih kayması) ELENDİ ve elenme gerekçesi
    kodda YAZILI. Beyan kaybolursa bir sonraki okur aynı iki adayı yeniden avlar."""
    import pathlib
    src = (pathlib.Path(earnings.__file__)).read_text()
    assert "BMO/AMC belirsizliği DEĞİL" in src and "Tarih kayması DEĞİL" in src
    assert "ARİTMETİĞİ" in src


def test_c_bmo_amc_yolu_var_ama_anahtar_kapali(sandbox_state):
    """DARALTMA YOLU: veri VARSA marj daralabilir — ama varsayılan KAPALI, yani davranış bit-bit
    aynı. Anahtar açıldığında yol GERÇEKTEN çalışıyor (testte açılıp kapatılıyor)."""
    bugun = dt.date.today().isoformat()
    (sandbox_state / "earnings.csv").write_text(
        f"ticker,date,time\nAAA,{bugun},bmo\nBBB,{bugun},amc\nCCC,{bugun},\n")
    earnings.clear_cache()
    assert earnings.TIME_TIGHTEN is False
    # KAPALI: üçü de karartmada (bugünkü davranış)
    assert all(earnings.in_blackout(t, bugun) is True for t in ("AAA", "BBB", "CCC"))
    # AÇIK: yalnız BMO daralır; AMC ve saati BİLİNMEYEN aynen karartmada kalır (None mantığı)
    import meridian.earnings as e
    eski = e.TIME_TIGHTEN
    try:
        e.TIME_TIGHTEN = True
        assert e.in_blackout("AAA", bugun) is False       # baskı bugünün AÇILIŞINDAN önce düştü
        assert e.in_blackout("BBB", bugun) is True        # AMC: baskı bugünün kapanışından sonra
        assert e.in_blackout("CCC", bugun) is True        # saat BİLİNMİYOR → hiçbir şey daralmaz
    finally:
        e.TIME_TIGHTEN = eski


def test_c_report_time_veri_yoksa_none(sandbox_state):
    """UYDURMA YASAĞI: kaynağın söylemediği saat None'dır — 'bmo say' varsayılanı YOK."""
    bugun = dt.date.today().isoformat()
    (sandbox_state / "earnings.csv").write_text(f"ticker,date,time\nAAA,{bugun},bmo\nBBB,{bugun},\n")
    earnings.clear_cache()
    assert earnings.report_time("AAA", bugun) == "bmo"
    assert earnings.report_time("BBB", bugun) is None
    assert earnings.report_time("YOK", bugun) is None
    # tanınmayan değer de None (sağlayıcı yeni bir dize basarsa sessizce "bmo" olmaz)
    (sandbox_state / "earnings.csv").write_text(f"ticker,date,time\nAAA,{bugun},time-not-supplied\n")
    earnings.clear_cache()
    assert earnings.report_time("AAA", bugun) is None


def test_c_iki_sutunlu_eski_dosya_aynen_okunur(sandbox_state):
    """GERİYE UYUMLULUK: canlıdaki dosya 2 sütunlu ve bu tur onu yeniden yazmaz."""
    fut = (dt.date.today() + dt.timedelta(days=3)).isoformat()
    (sandbox_state / "earnings.csv").write_text(f"ticker,date\nAAA,{fut}\n")
    earnings.clear_cache()
    assert earnings.in_blackout("AAA", dt.date.today().isoformat()) is True
    assert earnings.report_time("AAA", fut) is None


def test_c_adaptor_time_alanini_kanoniklestirir():
    """ÖLÇÜLMÜŞ HARİTA (2026-08-01, 6 iş günü / 1307 satır): time-not-supplied %65,7 ·
    time-after-hours %19,7 · time-pre-market %14,5. Haritada olmayan her değer None'a düşer."""
    from meridian.adapters import data as da
    assert da.NASDAQ_EARNINGS_TIME == {"time-pre-market": "bmo", "time-after-hours": "amc"}
    assert da.NASDAQ_EARNINGS_TIME.get("time-not-supplied") is None
    # VARSAYILAN ŞEKİL DEĞİŞMEDİ: `with_time` verilmezse eski sözlük şekli döner
    sig = inspect.signature(da.nasdaq_earnings_window)
    assert sig.parameters["with_time"].default is False


def test_c_birlestirme_saati_bilineni_ezmez(sandbox_state, monkeypatch):
    """BİLGİ KAZANIMI GERİ ALINMAZ: aynı (ticker,date) hem saatli hem saatsiz gelirse tek satır
    kalır ve BİLİNEN saat kazanır. Aksi hâlde `coverage().future_dates` şişer ve `_load` aynı
    tarihi iki kez listeler."""
    from meridian.adapters import data as da
    (sandbox_state / "earnings.csv").write_text("ticker,date\nAAA,2026-08-05\n")
    earnings.clear_cache()
    monkeypatch.setattr(da, "nasdaq_earnings_window",
                        lambda s, e, **k: {"AAA": [("2026-08-05", "amc")]})
    earnings.refresh(["AAA"])
    satirlar = [x for x in (sandbox_state / "earnings.csv").read_text().splitlines() if "AAA" in x]
    assert satirlar == ["AAA,2026-08-05,amc"]
    assert earnings._load()["AAA"] == ["2026-08-05"]      # tek tarih, çift değil


def test_c_fmp_yolu_saat_sutununu_silmez(sandbox_state, monkeypatch):
    """SÜTUN ÖLÇEĞİNDE 'YAZ DEĞİL BİRLEŞTİR': FMP ucu BMO/AMC vermez ama dosyayı BAŞTAN yazar.
    Eskiden 2 sütun yazdığı için Nasdaq'ın biriktirdiği saat bilgisini bir FMP tazelemesi
    SESSİZCE silerdi — kısmi-başarısızlık dersinin sütun hâli."""
    from meridian.adapters import fmp
    (sandbox_state / "earnings.csv").write_text("ticker,date,time\nAAA,2026-08-05,amc\n")
    earnings.clear_cache()
    monkeypatch.setattr(fmp, "available", lambda: True)
    monkeypatch.setattr(fmp, "earnings_dates", lambda t, strict=False: ["2026-08-05"])
    earnings.refresh_from_fmp(["AAA"])
    assert "AAA,2026-08-05,amc" in (sandbox_state / "earnings.csv").read_text()
    earnings.clear_cache()
    assert earnings.report_time("AAA", "2026-08-05") == "amc"


def test_c_coverage_marji_ve_ileri_gunu_soyler(sandbox_state):
    """GÖRÜNÜRLÜK: marj ve GERÇEK ileri kapsama yan yana. `ileri_gun < BLACKOUT_DAYS` = guard
    bugün fiilen kör; bu cümle bugüne dek hiçbir yüzeyde yoktu."""
    # İKİ SAYI BİLEREK FARKLI: `marj_gun` sabitlerden TÜRETİLİR (bugün 9), `ileri_gun` takvimin
    # ÖLÇÜLEN ucudur (burada 11). Eşit seçilirlerse test hangisini doğruladığını söyleyemez.
    ILERI = 11
    fut = (dt.date.today() + dt.timedelta(days=ILERI)).isoformat()
    _takvim(sandbox_state, [("AAA", fut)])
    cov = earnings.coverage(["AAA", "BBB"])
    assert cov["marj_gun"] == earnings.margin_days() and cov["marj_gun"] != ILERI
    assert cov["ileri_gun"] == ILERI and cov["saat_bilinen"] == 0
    past = (dt.date.today() - dt.timedelta(days=3)).isoformat()
    _takvim(sandbox_state, [("AAA", past)])
    assert earnings.coverage()["ileri_gun"] == 0 and earnings.coverage()["inert"] is True


def test_c_gave_up_uyarisi_marji_turetmeden_okur():
    """UYARI DA AYNI TÜRETMEDEN OKUR: `earnings_calendar_gave_up` marjı sabit yazmaz."""
    from meridian import scheduler
    src = inspect.getsource(scheduler.advance_once)
    i = src.index("earnings_calendar_gave_up")
    blok = src[i:i + 500]
    assert 'marj_gun=_cov.get("marj_gun")' in blok and "2 GÜN" not in blok


# =================================================================================================
# D — PIT BİRİKİM DEFTERİ (earnings.csv tek anlık görüntüydü; EDG-011'i ASKI'ya düşüren delik)
# =================================================================================================
def _nasdaq(monkeypatch, veri):
    from meridian.adapters import data as da
    monkeypatch.setattr(da, "nasdaq_earnings_window", lambda s, e, **k: veri)


def test_d_tazeleme_pit_anlik_goruntusu_ekler(sandbox_state, monkeypatch):
    """TAZELEME DEFTERE YAZAR: fetch damgası + o an bilinen ÜÇLÜLER."""
    from meridian import store
    _nasdaq(monkeypatch, {"AAA": [("2026-08-20", "amc")], "BBB": [("2026-08-21", None)]})
    earnings.refresh(["AAA", "BBB"])
    rows = store.read_jsonl(earnings.SNAPSHOT_FILE)
    assert len(rows) == 1
    r = rows[0]
    assert r["fetch_date"] == dt.date.today().isoformat() and r["source"] == "nasdaq"
    assert r["tickers"] == 2 and r["rows"] == 2 and r["time_known"] == 1
    assert ["AAA", "2026-08-20", "amc"] in r["kayitlar"]
    assert ["BBB", "2026-08-21", None] in r["kayitlar"]
    assert "fetched_at" in r and r["fetched_at"].endswith("+00:00")


def test_d_defter_append_only_eski_satirlar_ezilmez(sandbox_state, monkeypatch):
    """ÇEKİRDEK ÇİVİ: ikinci tazeleme BİRİNCİSİNİ EZMEZ. `earnings.csv` ezilir (os.replace) —
    defter ezilmez, revizyon tarihi ancak böyle ölçülebilir."""
    from meridian import store
    _nasdaq(monkeypatch, {"AAA": [("2026-08-20", None)]})
    earnings.refresh(["AAA"])
    # takvim REVİZE oldu: aynı şirket, KAYMIŞ tarih (ölçmek istediğimiz olgunun ta kendisi)
    _nasdaq(monkeypatch, {"AAA": [("2026-08-27", "bmo")]})
    earnings.refresh(["AAA"])
    rows = store.read_jsonl(earnings.SNAPSHOT_FILE)
    assert len(rows) == 2, "ikinci anlık görüntü birincisini ezdi — defter append-only değil"
    assert [k[1] for k in rows[0]["kayitlar"]] == ["2026-08-20"]
    # ikinci görüntüde İKİ tarih var: takvim birleştirilir (eski çapa silinmez), defter bunu görür
    assert sorted(k[1] for k in rows[1]["kayitlar"]) == ["2026-08-20", "2026-08-27"]
    assert rows[1]["kayitlar"][1][2] == "bmo"


def test_d_ayni_gun_ayni_icerik_ikinci_satir_yazmaz(sandbox_state, monkeypatch):
    """GÜRÜLTÜ KAPISI: içerik değişmediyse ikinci satır bilgi taşımaz, yalnız defteri şişirir
    ve 'kaç kez revize oldu' sayacını yalan yapar. İçerik DEĞİŞİRSE aynı gün ikinci satır YAZILIR."""
    from meridian import store
    _nasdaq(monkeypatch, {"AAA": [("2026-08-20", None)]})
    earnings.refresh(["AAA"])
    earnings.refresh(["AAA"])
    assert len(store.read_jsonl(earnings.SNAPSHOT_FILE)) == 1
    _nasdaq(monkeypatch, {"AAA": [("2026-08-20", "amc")]})     # saat bilgisi KAZANILDI = değişim
    earnings.refresh(["AAA"])
    assert len(store.read_jsonl(earnings.SNAPSHOT_FILE)) == 2


def test_d_fmp_yolu_da_anlik_goruntu_birakir(sandbox_state, monkeypatch):
    """FMP yolu da `earnings.csv`i BAŞTAN yazar — o yol da PIT damgası bırakmalı."""
    from meridian import store
    from meridian.adapters import fmp
    monkeypatch.setattr(fmp, "available", lambda: True)
    monkeypatch.setattr(fmp, "earnings_dates", lambda t, strict=False: ["2026-08-20"])
    earnings.refresh_from_fmp(["AAA"])
    rows = store.read_jsonl(earnings.SNAPSHOT_FILE)
    assert len(rows) == 1 and rows[0]["source"] == "fmp"


def test_d_yazim_dusse_tazeleme_dusmez(sandbox_state, monkeypatch):
    """YASA 4: defter bir BİRİKİMDİR, tazelemenin kendisi değil. Yazım düşerse anlık görüntü
    KAYIPtır (ve uyarı basılır) ama takvim yine tazelenir — karartma guard'ı etkilenmez."""
    from meridian import store
    uyari = []
    monkeypatch.setattr(store, "append_jsonl",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("disk dolu")))
    import meridian.obs as obs
    monkeypatch.setattr(obs, "warn", lambda ev, **kw: uyari.append(ev))
    _nasdaq(monkeypatch, {"AAA": [("2026-08-20", None)]})
    assert earnings.refresh(["AAA"]) == 1                       # tazeleme BAŞARILI
    assert earnings.in_blackout("AAA", "2026-08-18") is True    # guard çalışıyor
    assert "earnings_snapshot_failed" in uyari                  # ama sessiz DEĞİL


def test_d_sayac_ucu_defteri_tasimaz(sandbox_state, monkeypatch):
    """SAYAÇ UCU AĞIR ALANI DÖNMEZ: `kayitlar` 200+ üçlü taşır; sayaç ucuna koymak, panonun her
    anketinde defterin tamamını tele koymak olurdu."""
    assert earnings.snapshot_stats()["anlik_goruntu"] == 0      # defter yok → dürüst sıfır
    assert earnings.snapshot_stats()["ilk"] is None
    _nasdaq(monkeypatch, {"AAA": [("2026-08-20", "amc")]})
    earnings.refresh(["AAA"])
    s = earnings.snapshot_stats()
    assert s["anlik_goruntu"] == 1 and s["farkli_gun"] == 1
    assert s["son_kayit"] == 1 and s["son_saat_bilinen"] == 1
    assert "kayitlar" not in s and s["dosya"] == "history/earnings_snapshots.jsonl"


def test_d_pano_tuketicisi_bagli_ve_kod_grafi_gorüyor():
    """YASA 6 iki katman: (1) sayaç `/api/diagnostics` `risk` bloğundan servis edilir, (2) dosya
    adı ORADA LİTERAL geçer — `codelaw.artifact_graph` statik bir graftır ve okuma `earnings`in
    içinde kalsaydı defter "yazılıyor ama kimse okumuyor" (unread) görünürdü.
    İkinci çivi grafın KENDİSİYLE atılır, metin eşleşmesiyle değil."""
    import pathlib
    from meridian import codelaw
    api = (pathlib.Path(__file__).resolve().parent.parent / "meridian" / "api.py").read_text()
    assert '"earnings_pit": earnings.snapshot_stats(' in api
    assert 'store.read_jsonl("history/earnings_snapshots.jsonl")' in api
    g = codelaw.artifact_graph()
    kayit = g["artifacts"][earnings.SNAPSHOT_FILE]
    assert "api.py" in kayit["external_readers"] and "earnings.py" in kayit["writers"]


def test_d_defter_history_altinda_durur():
    """YER SÖZLEŞMESİ: birikim defteri `state/history/` altındadır — canlı state'in kök dizini
    döngünün her turda yeniden yazdığı dosyalarındır, birikim oraya karışmaz."""
    assert earnings.SNAPSHOT_FILE.startswith("history/")
