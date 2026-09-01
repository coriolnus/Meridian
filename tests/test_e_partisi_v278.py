"""test_e_partisi_v278.py — operatörün "E-kod partisi" turunun çivileri (2026-08-23).

Tek dosya, altı bağımsız kalem. Ortak sınıf: HEPSİ "beyan ile davranış ayrışmasın" ailesinden.
Her bölüm kendi kaleminin ÖLÇÜLEBİLİR sözünü çakar ve — kapatma/susturma kalemlerinde — bir
POZİTİF KONTROL taşır: bayrak/kapı AÇIKKEN yolun GERÇEKTEN yazdığı gösterilmeden, "kapalıyken
yazmıyor" iddiası boş bir testtir (her zaman geçen bir assert, ölçüm değildir).

  [1] F8-A3 — hermes ÜRETİCİSİ kanonik `halt_learning` yazar; eski `learning_halted` dönem
      sonuna dek EŞANLAMLI-OKUNUR ve okunduğunda SAYILIR (ad ne zaman ölür sorusunun ölçüsü).
  [2] `params_by_regime` DAMGASI — harita boş, ama boşluğu bir POLİTİKA (EDG-2026-048 NO-GO);
      damga koddan okunabilir olmalı, yoksa bir sonraki tur boşluğu "eksik" sanıp doldurur.
  [3] TEK KAYNAK — silahlı kurulum kümesinin ikinci bir SABİT tanımı yok; kırılım
      `strategy.ARMED_SETUPS`ten TÜRER (bayatlama iki yönde de ölçülüyordu: pullback fazladan,
      exhaustion_hammer eksikti).
  [4] AYLIK BUCKET-KOPYA — hedef kova litestream.yml ile aynı; birim YAPISAL olarak yerele
      yazamaz (yerel silme yok); kurulum elle = F9 kapısında kayıtlı.
  [5] DOLUM-ZAMANI (`dolum_ts`) — giriş ve çıkış yamaları ayna dolumunun ZAMANINI da taşır;
      okunamayan zaman UYDURULMAZ (None + neden).
  [9] EDG-2026-019 KILL#1 — skill-görüş YAZIMI varsayılan-KAPALI; defter DOKUNULMAZ; kapanış
      tek `skill_gorus_katmani_kapatildi` olayıyla ADLANDIRILIR.

Kalem [6] (ampirik mini-ölçüm) ve [7] (HUM/NUE teşhisi) SALT-OKUMA canlı raporlardır
(`docs/RAPOR-AMPIRIK-MINI-2026-08-23.md`, `docs/RAPOR-HUM-NUE-2026-08-23.md`) — kod değişikliği
üretmedikleri için burada çivileri YOKTUR; bu cümle o boşluğun beyanıdır (sessiz atlama yasağı).
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

import pytest

from meridian import config, durum_sozlugu, loop, store, strategy, validation_report
from tests.conftest import betikten_modul_yukle

REPO = pathlib.Path(__file__).resolve().parent.parent
ORACLE = REPO / "deploy" / "oracle-a1"


# =================================================================================================
# [1] F8-A3 — HERMES ÜRETİCİSİ KANONİK KOL ADINI YAZAR
# =================================================================================================
def test_1a_uretici_kanonik_ad_yazar_eski_ad_uretimde_kalmadi():
    """İki ÜRETİCİ vardı ve ikisi de eşanlamlıyı basıyordu: hermes ısınma dalı ve `reflect.submit`
    LEARN_HALT dalı. Kanonik ada geçiş, ancak İKİSİ de geçtiyse tamamdır — biri kalsaydı geçiş
    rejimi hiç bitmez, sayaç hiç sıfırlanmazdı."""
    hr = (REPO / "meridian" / "hermes_runtime.py").read_text(encoding="utf-8")
    rf = (REPO / "meridian" / "reflect.py").read_text(encoding="utf-8")
    assert '_state["last_result"] = "halt_learning"' in hr, "hermes üreticisi kanonik ada geçmemiş"
    assert '{"status": "halt_learning"' in rf, "reflect.submit üreticisi kanonik ada geçmemiş"
    for ad, metin in (("hermes_runtime.py", hr), ("reflect.py", rf)):
        uretim = [s for s in metin.splitlines()
                  if '"learning_halted"' in s and not s.lstrip().startswith("#")]
        assert uretim == [], f"{ad}: eski ad hâlâ ÜRETİLİYOR (yorum değil, kod): {uretim}"


def test_1b_eski_ad_esanlamli_okunur_ve_SAYILIR():
    """Eski ad listeden SİLİNMEDİ: diskte restart-öncesi persist edilmiş değerler yaşıyor olabilir.
    Sözleşme "çevir ve SAY"dır — sayaç, adın ölüm tarihini ÖLÇÜLEBİLİR kılan tek şeydir."""
    durum_sozlugu._sifirla_test_icin()
    assert durum_sozlugu.kol_adi("learning_halted") == "halt_learning"
    assert durum_sozlugu.esanlamli_okumalar().get("kol:learning_halted") == 1
    # Kanonik adın kendisi eşanlamlı DEĞİLDİR — sayılmamalı (yoksa sayaç asla sıfıra dönmez ve
    # "eski ad öldü mü?" sorusu yapısal olarak cevapsız kalır).
    assert durum_sozlugu.kol_adi("halt_learning") == "halt_learning"
    assert durum_sozlugu.esanlamli_okumalar().get("kol:learning_halted") == 1
    # Kol OLMAYAN değer aynen geçer ve sayılmaz (hermes `rejected_by_backtest` gibi).
    assert durum_sozlugu.kol_adi("rejected_by_backtest") == "rejected_by_backtest"
    assert "kol:rejected_by_backtest" not in durum_sozlugu.esanlamli_okumalar()


def test_1c_status_diskteki_BAYAT_adi_kanoniklestirir(sandbox_state, monkeypatch):
    """Geçiş okuyucusu DAVRANIŞ olarak ölçülür (metin çivisi değil): diske eski adla yazılmış bir
    durum, `status()` üzerinden kanonik okunur ve okuma sayaca düşer."""
    from meridian import hermes_runtime as hrt
    durum_sozlugu._sifirla_test_icin()
    monkeypatch.setattr(hrt, "_thread", None)      # süreç-dışı: yetkili kaynak DİSK
    store.write_json(hrt.STATUS_FILE, {"last_result": "learning_halted", "poll_seconds": 300})
    assert hrt.status()["last_result"] == "halt_learning"
    assert durum_sozlugu.esanlamli_okumalar().get("kol:learning_halted") == 1


def test_1d_ship_kapisi_LEARN_HALT_altinda_kanonik_hukum_dondurur(sandbox_state, monkeypatch):
    """Davranış çivisi (pozitif kontrol): kapı gerçekten kapanıyor VE hükmün adı kanonik."""
    from meridian import health, reflect
    monkeypatch.setattr(health, "learn_halted", lambda: True)
    res = reflect.submit({"variable": "entry.min_score", "new": 65})
    assert res["status"] == "halt_learning"
    assert "LEARN_HALT" in res["detail"]


# =================================================================================================
# [2] params_by_regime — BİLEREK BOŞ (EDG-2026-048 NO-GO politikası)
# =================================================================================================
def test_2a_harita_bos_ve_bosluk_POLITIKA_olarak_damgali():
    """Boş bir harita iki şeyden biri olabilir: unutulmuş bir kanca ya da ölçülmüş bir karar.
    Damga o ikisini ayırır; damgasız boşluk bir sonraki turda 'doldurulacak eksik' diye okunur."""
    st = config.default_strategy()
    assert st["params_by_regime"] == {r: {} for r in config.VALID_REGIMES}, \
        "harita artık boş değil — damganın gerekçesi (048 NO-GO) yeniden tartılmalı"
    src = (REPO / "meridian" / "config.py").read_text(encoding="utf-8")
    blok = src[src.index("def default_strategy"):]
    blok = blok[:blok.index('"params_by_regime"')]
    for parca in ("BİLEREK BOŞ", "EDG-2026-048", "NO-GO"):
        assert parca in blok, f"damgada eksik: {parca!r} (boşluk politika olarak okunamıyor)"
    assert "YENİ ölçüm kartıyla" in blok or "yeni ölçüm kartıyla" in blok.lower(), \
        "canlanma koşulu (kart-önce) yazılı değil — elle doldurmaya kapı açık kalır"


def test_2b_resolve_params_okuyucu_serhi_damgaya_ATIF_yapar():
    """Damga tanımın yanında durur ama OKUYUCU `resolve_params`tır: haritayı orada gören mühendis
    de boşluğun neden boş olduğunu bulabilmeli (iki yerde iki farklı gerekçe YAZILMAZ — atıf)."""
    doc = config.resolve_params.__doc__ or ""
    assert "EDG-2026-048" in doc and "default_strategy" in doc, \
        "resolve_params şerhi damgaya atıf yapmıyor"


# =================================================================================================
# [3] TEK KAYNAK — silahlı küme `strategy.ARMED_SETUPS`
# =================================================================================================
def test_3a_kirilim_kanonik_kumeden_TUREr():
    """Eski sabit dörtlü iki yönde de bayatlamıştı: `pullback` B1'de silahsızlandı ama listede
    kaldı, `exhaustion_hammer` 2026-08-11'de SİLAHLANDI ama listede hiç olmadı — yani SİLAHLI bir
    kurulumun edge'i bu karşı-yüzeyde ölçülemiyordu. Türetim o sınıfı yapısal olarak kapatır."""
    from meridian import arming
    izlenen = validation_report.izlenen_setuplar()
    assert set(strategy.ARMED_SETUPS) <= set(izlenen), "SİLAHLI bir kurulum kırılımda görünmüyor"
    assert set(arming._dormant_setups()) <= set(izlenen), "uyuyan küme kırılımdan düşmüş"
    assert "exhaustion_hammer" in izlenen, "bayatlamanın ta kendisi geri gelmiş"
    assert len(izlenen) == len(set(izlenen)), f"tekrar eden setup var: {izlenen}"
    assert tuple(izlenen[:len(strategy.ARMED_SETUPS)]) == tuple(strategy.ARMED_SETUPS), \
        "silahlılar önde değil — tuple sırası silahlanma önceliğidir"


def test_3b_ayrisma_civisi_kume_degisince_kirilim_PESINDEN_gelir(monkeypatch):
    """AYRIŞMA ÇİVİSİ: kanonik tuple değişince kırılım kendiliğinden değişmeli. Değişmiyorsa
    ortada gizli bir ikinci tanım vardır (tam olarak kaldırılan sınıf)."""
    monkeypatch.setattr(strategy, "ARMED_SETUPS", ("momentum_burst",))
    izlenen = validation_report.izlenen_setuplar()
    assert izlenen[0] == "momentum_burst", "silahlı küme kırılımın başını sürüklemiyor"
    # Silahtan düşen kurulum motor listesindeyse UYUYAN olarak izlenmeye DEVAM eder — edge'i
    # ölçülmeden hiçbir kurulum kırılımdan düşemez (yeniden-silahlanma kapısının girdisi budur).
    assert "breakout_vcp" in izlenen
    monkeypatch.setattr(strategy, "ARMED_SETUPS", ("breakout_vcp", "pullback"))
    izlenen2 = validation_report.izlenen_setuplar()
    assert izlenen2[:2] == ("breakout_vcp", "pullback"), "silahlanan kurulum öne geçmedi"
    assert izlenen2.count("pullback") == 1, "silahlı+uyuyan birleşiminde tekrar üretildi"


def test_3c_ikinci_SABIT_tanim_kalmadi():
    """Metin çivisi, ama doğru araç: korunan şey davranıştan önce SÖZLEŞMEdir — 'silahlı küme
    tek yerde tanımlıdır'. Tarama, kurulum adlarını yan yana SABİT DİZİ olarak yazan her
    atama/dönüş/üyelik ifadesini arar (düz anlatı yorumu/docstring'i değil — orada tarihçe yazılı)."""
    desen = re.compile(r"""(?:=|\breturn\b|\bin\b)\s*[\(\[\{]\s*["']"""
                       r"""(?:breakout_vcp|pullback|momentum_burst|episodic_pivot|exhaustion_hammer)"""
                       r"""["']\s*,\s*["']""")
    ihlal = []
    for p in sorted((REPO / "meridian").rglob("*.py")):
        for no, s in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if s.lstrip().startswith("#") or not desen.search(s):
                continue
            ihlal.append(f"{p.relative_to(REPO)}:{no}: {s.strip()[:90]}")
    # İZİNLİ İKİ TANIM, ADIYLA: kanonik kümenin KENDİSİ ve motor listesi (`arming._dormant_setups`
    # — silahlı küme DEĞİL, motorun TANIDIĞI küme; ikisi farklı olgudur ve fark yorumda yazılı).
    izinli = ("meridian/strategy.py", "meridian/arming.py")
    kacak = [i for i in ihlal if not i.startswith(izinli)]
    assert kacak == [], f"silahlı/motor kümesinin izinsiz ikinci sabit tanımı: {kacak}"


def test_3d_motor_listesi_ayrismasi_BEYANLI_ve_BUYUMUYOR():
    """Ölçüm, düzeltme DEĞİL (kapsam: bu tur kırılımın tek-kaynağı; motor listesini genişletmek
    silahlanma kapısının KAPSAMINI değiştirir → kart-önce, Rol-1). Ayrışma `arming` docstring'inde
    ADIYLA yazılı; bu çivi onun BÜYÜMESİNİ yakalar: üçüncü bir ad girerse kırmızı yanar."""
    from meridian import arming, skills
    src = (REPO / "meridian" / "arming.py").read_text(encoding="utf-8")
    elle = set(re.search(r"engine = \(([^)]*)\)", src).group(1).replace('"', "").split(", "))
    kanonik = {s for s, scr in skills._SCREENER_BY_SETUP.items()
               if scr in skills.ENGINE_IMPLEMENTED}
    assert kanonik - elle == {"exhaustion_hammer", "pead"}, (
        f"motor listesi ayrışması DEĞİŞTİ: {sorted(kanonik - elle)} — arming docstring'indeki "
        f"beyan bayatladı, yeniden tartılmalı (kapı kapsamı kararı)")
    assert elle - kanonik == set(), "motor listesinde kanonikte OLMAYAN ad var (hayalet setup)"
    for ad in ("exhaustion_hammer", "pead", "BEYANLI BOŞLUK"):
        assert ad in (arming._dormant_setups.__doc__ or ""), f"ayrışma beyanında eksik: {ad}"


# =================================================================================================
# [4] AYLIK BUCKET-KOPYA BİRİMİ
# =================================================================================================
def _bk_modul():
    return betikten_modul_yukle(ORACLE / "aylik_bucket_kopya.py", "aylik_bucket_kopya")


def test_4a_hedef_kova_litestream_yml_ile_AYNI():
    """İki yerde ayrışan bir endpoint, yıllar sonra 'yedek nerede?' sorusunu cevapsız bırakır.
    Sabitler betikte BEYANLIdır (yml ayrıştırıcısı taşımamak için) ama ayrışamazlar."""
    m = _bk_modul()
    yml = (ORACLE / "litestream.yml").read_text(encoding="utf-8")
    for alan, deger in (("bucket", m.BUCKET), ("region", m.REGION), ("endpoint", m.ENDPOINT)):
        bulunan = re.search(rf"^\s*{alan}:\s*(\S+)\s*$", yml, re.M)
        assert bulunan, f"litestream.yml'de `{alan}:` okunamadı — çivi bayatlamış"
        assert bulunan.group(1) == deger, f"`{alan}` ayrışmış: yml={bulunan.group(1)} betik={deger}"
    assert not m.PREFIX.startswith("litestream"), \
        "arşiv öneki litestream'in yoluyla çakışıyor — retention politikası arşivi yiyebilir"


def test_4b_onceki_ay_yil_donumunde_de_dogru():
    """Ocak'ta 'önceki ay' bir önceki YILIN aralığıdır. Naif `month-1` burada 0 üretir ve arşiv
    sessizce hiç koşmaz."""
    import datetime as dt
    m = _bk_modul()
    assert m._onceki_ay(dt.date(2026, 1, 5)) == "2025-12"
    assert m._onceki_ay(dt.date(2026, 3, 1)) == "2026-02"
    assert m._onceki_ay(dt.date(2026, 12, 31)) == "2026-11"


def test_4c_bos_ay_SESSIZ_BASARI_degil(tmp_path, capsys):
    """Ay boyu hiç dosya yoksa bu ya arşivcinin durduğu bir olaydır ya listenin bayatlamasıdır —
    ikisi de iş kalemi. Çıkış kodu 1 + neden; 'yuklendi: true' ASLA."""
    m = _bk_modul()
    m.STATE = tmp_path / "bos"
    assert m.main(["--ay", "2026-07"]) == 1
    rap = json.loads(capsys.readouterr().out)
    assert rap["yuklendi"] is False and len(rap["neden"]) >= 20


def test_4d_kuru_kosum_tar_kurar_ve_OLCER(tmp_path, capsys):
    """POZİTİF KONTROL: mutlu yol gerçekten çalışıyor (yoksa 4c her koşulda geçerdi). İki dizinin
    AYNI tarihli dosyaları arşivde birbirini EZMEZ — dizin adı arşiv-içi yolda korunur."""
    m = _bk_modul()
    st = tmp_path / "state"
    for d in m.DIZINLER:
        (st / d).mkdir(parents=True)
        (st / d / "2026-07-30.jsonl").write_text(f'{{"kim":"{d}"}}\n', encoding="utf-8")
        (st / d / "2026-08-03.jsonl").write_text("{}\n", encoding="utf-8")   # BAŞKA ay — girmemeli
    m.STATE = st
    assert m.main(["--ay", "2026-07", "--kuru"]) == 0
    rap = json.loads(capsys.readouterr().out)
    assert rap["n_dosya"] == 2 and rap["tar_bayt"] > 0
    assert rap["dizinler"] == {d: 1 for d in m.DIZINLER}
    assert rap["yuklendi"] is False and "--kuru" in rap["neden"]
    assert rap["anahtar"] == "arsiv/intraday/2026-07/intraday-2026-07.tar.gz"


def test_4e_YEREL_SILME_YOK_yapisal():
    """Sözün iki bacağı: (a) betikte silme çağrısı yok, (b) birim `ReadWritePaths=` VERMEZ —
    ProtectSystem=strict altında state SALT-OKUNURDUR. (b) olmadan (a) yalnız bir niyettir."""
    src = (ORACLE / "aylik_bucket_kopya.py").read_text(encoding="utf-8")
    kod = [s for s in src.splitlines() if not s.lstrip().startswith("#")]
    for yasak in ("os.remove", "os.unlink", ".unlink(", "shutil.rmtree", "os.rmdir"):
        assert not any(yasak in s for s in kod), f"yükleyici silme çağrısı taşıyor: {yasak}"
    birim = (ORACLE / "meridian-aylik-bucket-kopya.service").read_text(encoding="utf-8")
    direktif = [s for s in birim.splitlines() if not s.lstrip().startswith("#")]
    assert not any(s.startswith("ReadWritePaths=") for s in direktif), \
        "ReadWritePaths verilmiş — yerele yazma yolu açıldı, 'silme yok' yapısal olmaktan çıktı"
    assert "PrivateTmp=true" in direktif and "ProtectSystem=strict" in direktif
    assert "ReadWritePaths" in birim, "satırın YOKLUĞU gerekçesiz — sessiz atlama yasağı"
    assert "EnvironmentFile=-/opt/meridian/state/litestream.env" in direktif, \
        "kimlik zinciri litestream.env'e bağlı değil"


def test_4g_PUT_govdesi_ve_uzunlugu_ISTEKTE_birlikte_durur(tmp_path):
    """GERÇEK VAKA ÇİVİSİ (2026-08-23, yerel sahte-S3 koşumu): gövde kurucudan SONRA
    `req.data = f` ile veriliyordu; `Request.data` setter'ı `Content-length`i SİLİYOR ve urllib
    dosya nesnesi için uzunluk türetemeyince gövde HİÇ GİTMİYORDU — sunucu 0 bayt aldı. Hata
    yalnız ETag doğrulamasında yakalandı, yani doğrulama olmasa SESSİZ BOŞ NESNE üretilecekti.
    Çivi o değişmezi tutar: istekte gövde VE uzunluk BİRLİKTE bulunur, imza da uzunluğu kapsar."""
    m = _bk_modul()
    monkey = {"LITESTREAM_ACCESS_KEY_ID": "K", "LITESTREAM_SECRET_ACCESS_KEY": "S"}
    import os as _os
    eski = {k: _os.environ.get(k) for k in monkey}
    _os.environ.update(monkey)
    try:
        p = tmp_path / "x.tar.gz"
        p.write_bytes(b"0123456789")
        with p.open("rb") as f:
            req = m._istek("PUT", "arsiv/intraday/2026-07/x.tar.gz", govde_sha="ab" * 32,
                           uzunluk=10, govde=f, ek_baslik={"content-type": "application/gzip"})
            assert req.data is not None, "gövde düşmüş — boş nesne yüklenirdi"
            assert req.get_header("Content-length") == "10", \
                "Content-length silinmiş (data setter tuzağı) — gövde taşınmaz"
        assert req.get_full_url().endswith("/meridian-bucket/arsiv/intraday/2026-07/x.tar.gz"), \
            "path-style URL bozuldu (force-path-style sözleşmesi)"
        yetki = req.get_header("Authorization")
        assert yetki.startswith(f"AWS4-HMAC-SHA256 Credential=K/") and f"/{m.REGION}/s3/" in yetki
        imzali = yetki.split("SignedHeaders=")[1].split(",")[0]
        assert "content-length" in imzali and "host" in imzali and "x-amz-content-sha256" in imzali, \
            f"imza kapsamı eksik: {imzali}"
        # KİMLİKSİZ ÇAĞRI SESSİZ GEÇMEZ: sır yoksa istek hiç kurulmaz (boş imzayla 403 yerine
        # okunabilir bir hata — 'birim litestream.env'i yüklüyor mu?' sorusu doğrudan sorulur).
        _os.environ.pop("LITESTREAM_ACCESS_KEY_ID")
        with pytest.raises(SystemExit, match="kimlik YOK"):
            m._istek("HEAD", "a", govde_sha="00" * 32)
    finally:
        for k, v in eski.items():
            if v is None:
                _os.environ.pop(k, None)
            else:
                _os.environ[k] = v


def test_4f_kurulum_ELLE_ve_F9_kapisinda_kayitli():
    """F9 SINIFI: dagit bu iki dosyayı TAŞIMAZ. Kapıya yazılmazsa 'repo ilerler, canlı yerinde
    sayar ve kimse bağırmaz' (OB-2'yi doğuran sınıf) buraya da geri gelir."""
    dagit = (REPO / "dagit.sh").read_text(encoding="utf-8")
    for ad in ("meridian-aylik-bucket-kopya.service", "meridian-aylik-bucket-kopya.timer"):
        assert f"deploy/oracle-a1/{ad}|/etc/systemd/system/{ad}" in dagit, \
            f"[F9] içerik kapısında kayıtlı değil: {ad}"
        assert (ORACLE / ad).is_file()
    r = subprocess.run(["bash", "-n", str(REPO / "dagit.sh")], capture_output=True, text=True)
    assert r.returncode == 0, f"dagit.sh sözdizimi bozuldu:\n{r.stderr}"
    timer = (ORACLE / "meridian-aylik-bucket-kopya.timer").read_text(encoding="utf-8")
    bolumler = [s.strip() for s in timer.splitlines() if not s.lstrip().startswith("#")]
    assert "[Service]" not in bolumler, "timer'a sertleştirme sızmış (yanlış dosya)"
    assert "Persistent=true" in bolumler, "kaçan aylık atış telafi edilmiyor"


# =================================================================================================
# [5] DOLUM-ZAMANI (`dolum_ts`) — GÖRÜNÜRLÜK, DAVRANIŞ DEĞİL
# =================================================================================================
def test_5a_giris_yamasi_dolum_zamanini_yazar(sandbox_state):
    """E2 giriş defteri artık "ne ödedik" yanında "NE ZAMAN doldu"yu da taşır. Okuyucusu
    EDG-2026-052'nin haftalık tekrarı; yazım DAVRANIŞ DEĞİŞTİRMEZ (fiyat alanları aynı)."""
    store.append_jsonl(loop.ENTRY_LEDGER, {
        "date": "2026-08-20", "plan_id": "P-A", "ticker": "AAA", "motor": "ayna",
        "limit": 100.5, "karar": "submitted", "fill": None})
    rap = loop._patch_entry_slippage(
        {"P-A": {"status": "filled", "filled_avg_price": "100.40", "filled_qty": "50",
                 "filled_at": "2026-08-20T13:31:02.113Z"}}, {"AAA": 100.0}, "2026-08-20")
    assert rap["yazilan"] == 1
    row = store.read_jsonl(loop.ENTRY_LEDGER)[0]
    assert row["dolum_ts"] == "2026-08-20T13:31:02.113Z"
    assert "dolum_ts_neden" not in row
    assert row["fill"] == 100.4                      # davranış aynı: fiyat bacağı bozulmadı


def test_5b_zaman_yoksa_UYDURULMAZ(sandbox_state):
    """`filled_at` boşsa (kısmi dolum / iptal-artığı) alan None kalır ve NEDEN yazılır. `ts` ya da
    `fill_kaydedildi` ile ikame etmek, dolum anını GÖZLEM anıyla karıştırmak olurdu."""
    store.append_jsonl(loop.ENTRY_LEDGER, {
        "ts": "2026-08-19T20:31:00+00:00", "date": "2026-08-20", "plan_id": "P-B",
        "ticker": "BBB", "motor": "ayna", "limit": 50.0, "karar": "submitted", "fill": None})
    loop._patch_entry_slippage({"P-B": {"status": "filled", "filled_avg_price": "49.9",
                                        "filled_qty": "10"}}, {"BBB": 50.0}, "2026-08-20")
    row = store.read_jsonl(loop.ENTRY_LEDGER)[0]
    assert row["dolum_ts"] is None
    assert len(row["dolum_ts_neden"]) >= 20 and "uydurulmadı" in row["dolum_ts_neden"]
    # İKAME YASAĞI: gönderim damgası (`ts`) ve GÖZLEM damgası (`fill_kaydedildi`) yerinde durur
    # ama hiçbiri dolum anının yerine geçmez — üçü AYRI olguların adıdır.
    assert row["ts"] == "2026-08-19T20:31:00+00:00" and row["fill_kaydedildi"] == "2026-08-20"


def test_5c_exit_fill_ts_fiyatla_AYNI_bacagi_secer():
    """Zaman ikizinin tek işi budur: fiyat bir bacaktan, zaman başka bacaktan gelirse ikisi bir
    arada YALAN söyler. Dolmamış bacak seçilmez; `filled_at` yoksa None (zaman uydurulmaz)."""
    from meridian.adapters import alpaca
    emir = {"legs": [
        {"status": "canceled", "filled_avg_price": None, "filled_at": "2026-08-17T13:37:24Z"},
        {"status": "filled", "filled_avg_price": "380", "filled_at": "2026-08-17T13:37:47Z"}]}
    assert alpaca.exit_fill_price(emir) == 380.0
    assert alpaca.exit_fill_ts(emir) == "2026-08-17T13:37:47Z"
    zamansiz = {"legs": [{"status": "filled", "filled_avg_price": "380"}]}
    assert alpaca.exit_fill_price(zamansiz) == 380.0 and alpaca.exit_fill_ts(zamansiz) is None
    assert alpaca.exit_fill_ts({"legs": []}) is None
    assert alpaca.exit_fill_ts(None) is None


def test_5d_cikis_yamasi_zamani_satira_tasir(sandbox_state):
    """Çıkış yolunda da aynı söz: gerçek dolum satıra yamalanırken ZAMANI da gider. Fiyat
    ölçülüp zaman ölçülemezse yama YİNE işlenir + neden yazılır (zamansız gerçek fiyat,
    fiyatsız zamandan değerlidir)."""
    from meridian.adapters import alpaca
    store.append_jsonl("trades.jsonl", {"id": "T1", "plan_id": "P-X", "ticker": "XXX",
                                        "exit": 380.0992, "exit_reason": "stop"})
    meta = {loop.EXIT_FILL_KEY: {"P-X": {"ticker": "XXX", "kaynak": "bacak", "reason": "stop",
                                         "since": "2026-08-19", "tries": 0}}}
    parent = {"legs": [{"status": "filled", "filled_avg_price": "380",
                        "filled_at": "2026-08-17T13:37:47Z"}]}
    out: dict = {"drift": []}
    loop._exit_fill_yamasi(meta, {"P-X": parent}, {}, "2026-08-19", out, alpaca)
    assert out["exit_fill"]["yamalanan"] == 1
    row = store.read_jsonl("trades.jsonl")[0]
    assert row["alpaca_fill_price"] == 380.0
    assert row["dolum_ts"] == "2026-08-17T13:37:47Z"
    assert "dolum_ts_neden" not in row


def test_5e_cikis_yamasinda_zaman_olculemezse_fiyat_YINE_islenir(sandbox_state):
    from meridian.adapters import alpaca
    store.append_jsonl("trades.jsonl", {"id": "T2", "plan_id": "P-Y", "ticker": "YYY",
                                        "exit": 100.0, "exit_reason": "stop"})
    meta = {loop.EXIT_FILL_KEY: {"P-Y": {"ticker": "YYY", "kaynak": "bacak", "reason": "stop",
                                         "since": "2026-08-19", "tries": 0}}}
    out: dict = {"drift": []}
    loop._exit_fill_yamasi(meta, {"P-Y": {"legs": [{"status": "filled",
                                                    "filled_avg_price": "100.02"}]}},
                           {}, "2026-08-19", out, alpaca)
    row = store.read_jsonl("trades.jsonl")[0]
    assert row["alpaca_fill_price"] == 100.02          # fiyat ölçümü KAYBEDİLMEDİ
    assert row["dolum_ts"] is None and len(row["dolum_ts_neden"]) >= 20


# =================================================================================================
# [9] EDG-2026-019 KILL#1 — SKILL-GÖRÜŞ YAZIMI KAPALI
# =================================================================================================
@pytest.fixture
def sg_kapali(monkeypatch):
    """Süreç-içi mandal testler arası SIZAR (tek-atış olay). Her çivi kendi mandalıyla koşar.
    2026-09-01 açılışından beri üretim varsayılanı AÇIK — 'kapalı' durumu artık varsayılan
    değil, bu fixture'ın KURDUĞU durumdur (kapalı-yol çivileri açılıştan sonra da yaşar)."""
    from meridian import skill_gorus as sg
    monkeypatch.setattr(config, "SKILL_GORUS_URETIM_ACIK", False)
    monkeypatch.setattr(sg, "_KAPATMA_OLAYI_BASILDI", False)
    return sg


def _gorus_evreni(monkeypatch, sg):
    """Toplama yolunu ağdan/kayıt defterinden bağımsız kılar: kapının ölçtüğü şey YAZIM
    KARARIDIR, evrenin içeriği değil."""
    monkeypatch.setattr(sg, "evren", lambda: {"evren": ["vcp-screener"]})
    monkeypatch.setattr(sg, "_gozlemler", lambda: {
        "satirlar": [{"skill": "vcp-screener", "hedef": "AAA", "tarih": "2026-08-20",
                      "skor": 80, "kaynak": "test", "mfe_r": 1.0, "r": 0.5, "karar": "stop"}],
        "atlanan": {}})


def test_9a_bayrak_ACIK_ve_kart_acilis_kaydina_BAGLI():
    """Varsayılanın kendisi hükümdür — iki yönde de. Kill#1 döneminde bu çivi 'varsayılan
    KAPALI'yı korudu; 2026-09-01 açılışından beri koruduğu şey AÇIKLIĞIN MEŞRUİYETİ: bayrak
    ancak kartta resmî açılış kaydı VARKEN açık olabilir (elle-True yasağının çivisi budur —
    kaydı silip bayrağı açık bırakan tur burada kırılır). Kill#1 tarihçesi yorumdan silinemez."""
    assert config.SKILL_GORUS_URETIM_ACIK is True
    src = (REPO / "meridian" / "config.py").read_text(encoding="utf-8")
    blok = src[:src.index("SKILL_GORUS_URETIM_ACIK = True")]
    blok = blok[blok.rindex("# ── SKILL-GÖRÜŞ"):]
    for parca in ("EDG-2026-019", "kill#1", "GÖZLEM İCRAYI YAVAŞLATAMAZ",
                  "acilis_kaydi_2026_09_01"):
        assert parca in blok, f"bayrağın gerekçesinde eksik: {parca!r}"
    kart = (REPO / "research" / "cards" / "EDG-2026-019-skill-gorus-defteri.yaml"
            ).read_text(encoding="utf-8")
    assert "acilis_kaydi_2026_09_01" in kart, \
        "bayrak açık ama kartta açılış kaydı yok — açılışın meşruiyet zinciri kopuk"
    assert "kill1_kaydi_2026_08_23" in kart, "kill#1 kaydı karttan silinmiş — tarihçe kanıttır"


def test_9b_KAPALIYKEN_yazim_yolu_olu_ve_defter_DOKUNULMAMIS(sandbox_state, monkeypatch, sg_kapali):
    """Kalemin asıl sözü: yalnız YAZIM durur — defterlere DOKUNULMAZ (son KILL kaydı kanıt olarak
    yerinde kalır). Ölçü bayt-özdeşliktir: 'satır sayısı aynı' silinip yeniden yazılmayı yakalamaz."""
    sg = sg_kapali
    _gorus_evreni(monkeypatch, sg)
    store.append_jsonl(sg.GORUS_DEFTERI, {"skill": "eski", "yuzey": "cikis", "hedef": "ZZZ"})
    store.write_json(sg.DURUM_DEFTERI, {"kart": sg.KART, "kill_p95": {"durum": "KILL"}})
    g_once = (config.STATE / sg.GORUS_DEFTERI).read_bytes()
    d_once = (config.STATE / sg.DURUM_DEFTERI).read_bytes()

    t = sg.topla(apply=True)
    assert t == {**t, "kapali": True, "yazilan": 0, "uygulandi_mi": False}
    assert "EDG-2026-019" in t["neden"] and len(t["neden"]) >= 20
    k = sg.kadans(apply=True, oncesi_ms=1000.0)
    assert k["kapali"] is True and k["uygulandi_mi"] is False and k["pay"] is None

    assert (config.STATE / sg.GORUS_DEFTERI).read_bytes() == g_once, "görüş defterine dokunuldu"
    assert (config.STATE / sg.DURUM_DEFTERI).read_bytes() == d_once, \
        "durum defteri ezildi — son KILL kaydı kanıt olarak kalmalıydı"
    assert store.read_json(sg.DURUM_DEFTERI, {})["kill_p95"]["durum"] == "KILL"


def test_9c_POZITIF_KONTROL_bayrak_acikken_yazim_GERCEKTEN_olur(sandbox_state, monkeypatch,
                                                                sg_kapali):
    """9b'yi anlamlı kılan çivi. Bu geçmezse 'kapalıyken yazmıyor' iddiası boştur: yol zaten
    hiçbir koşulda yazmıyor olabilirdi."""
    sg = sg_kapali
    _gorus_evreni(monkeypatch, sg)
    monkeypatch.setattr(config, "SKILL_GORUS_URETIM_ACIK", True)
    t = sg.topla(apply=True)
    assert t.get("kapali") is None and t["uygulandi_mi"] is True
    assert t["yazilan"] >= 1, "açıkken de yazmıyor — kapı testi hiçbir şey ölçmüyordu"
    assert len(store.read_jsonl(sg.GORUS_DEFTERI)) == t["yazilan"]


def test_9d_kapanis_TEK_olayla_adlandirilir(sandbox_state, monkeypatch, sg_kapali):
    """Sessiz kapanış yok (YASA 4/6): olay ADIYLA düşer. Ama SÜREÇ BAŞINA BİR KEZ — kadans günde
    bir koşsa da api/CLI yolları da buradan geçer; her çağrıda basmak aynı kapanışı yüzlerce kez
    tekrarlamak olurdu."""
    sg = sg_kapali
    _gorus_evreni(monkeypatch, sg)
    sg.topla(apply=True)
    sg.topla(apply=True)
    sg.kadans(apply=True, oncesi_ms=1000.0)
    olaylar = [e for e in store.read_jsonl("events.jsonl")
               if e.get("event") == "skill_gorus_katmani_kapatildi"]
    assert len(olaylar) == 1, f"tek-atış mandalı tutmadı: {len(olaylar)} olay"
    assert olaylar[0]["kart"] == "EDG-2026-019"
    assert "SKILL_GORUS_URETIM_ACIK" in olaylar[0]["detail"], "açılış kapısı olayda adlandırılmamış"


def test_9e_kuru_kosu_OLCUM_araci_olarak_acik_kalir(sandbox_state, monkeypatch, sg_kapali):
    """`apply=False` yazmaz — kapatılan şey YAZIMDIR, ÖLÇÜM DEĞİL. Kartın yeniden açılışı için
    gereken yeni ölçüm, kapının kendisi tarafından imkânsız kılınmamalı."""
    sg = sg_kapali
    _gorus_evreni(monkeypatch, sg)
    t = sg.topla(apply=False)
    assert t.get("kapali") is None and t["uygulandi_mi"] is False
    assert t["yazilan"] >= 1, "kuru koşu ne yazılacağını göstermiyor — ölçüm aracı ölmüş"
    assert not (config.STATE / sg.GORUS_DEFTERI).exists(), "kuru koşu deftere yazdı"


def test_9f_mekanizma_testleri_URETIM_varsayilanini_degistirmiyor():
    """v218 dosyası mekanizmayı ölçmek için bayrağı SÜREÇ-YEREL açar (autouse fixture). O fixture
    `monkeypatch` kullanmalı — düz atama yapsaydı üretim varsayılanı suite boyunca sızardı."""
    src = (REPO / "tests" / "test_skill_gorus_v218.py").read_text(encoding="utf-8")
    assert "monkeypatch.setattr(_cfg, \"SKILL_GORUS_URETIM_ACIK\", True)" in src
    assert "autouse=True" in src
    assert "_cfg.SKILL_GORUS_URETIM_ACIK = True" not in src, \
        "düz atama — bayrak suite'e sızar ve kapanış hükmü ölçülemez hâle gelir"


def test_9g_defter_ve_durum_dosyalari_SILINMEDI():
    """Hüküm 'yazım durur', 'kanıt silinir' DEĞİL: okuma yüzeyleri ve dosya adları yerinde."""
    from meridian import skill_gorus as sg
    assert sg.GORUS_DEFTERI == "skill_gorusleri.jsonl" and sg.DURUM_DEFTERI == "skill_gorus_durum.json"
    for ad in ("defter", "rapor", "evren"):
        assert callable(getattr(sg, ad)), f"okuma yüzeyi kaldırılmış: {ad}"
    src = (REPO / "meridian" / "skill_gorus.py").read_text(encoding="utf-8")
    kod = [s for s in src.splitlines() if not s.lstrip().startswith("#")]
    assert not any("store.sil" in s or "os.remove" in s or "unlink" in s for s in kod), \
        "kapatma turuna silme sızmış — defter kanıttır"


if __name__ == "__main__":                                  # pragma: no cover
    sys.exit(pytest.main([__file__, "-q"]))
