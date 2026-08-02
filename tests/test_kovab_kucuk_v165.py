"""v165 — KOVA B (küçük kalemler): C1 (MERIDIAN_BIND_HOST hayalet girdi) + C25'in FMP-EŞİĞİ yarısı.

İki düzeltmeyi çiviler. İkisi de "beyan ile davranışı aynı hizaya getirme" işidir:

  A) C1 — `api._auth_posture_check` "loopback DIŞINA parolasız açılma"yı REDDEDEN bir kapıdır ve
     hükmünü `MERIDIAN_BIND_HOST`tan türetir. Ama o değişkeni HİÇBİR başlatıcı YAZMIYORDU: gerçek
     bağ her yerde `--host 127.0.0.1` SABİTİYDİ. Yani kapının var olma nedeni olan tek senaryoda
     (operatör panoyu dışarı açar) değişken boş kalır, `public_bind=False` olur ve ne ret ne uyarı
     ateşlenirdi — okunan değer, korunan olguyu BELİRLEMİYORDU. Yeni yasa: `serve.sh` ve
     `deploy/oracle-a1/meridian.service` uvicorn'un `--host`unu BU değişkenden verir (tek kaynak);
     kapı mantığı BİT-BİT AYNI kaldı, değişen okunan değerin artık GERÇEK olmasıdır.
     ⚠ KAPSAM DÜRÜSTLÜĞÜ: docker-compose.yml / Dockerfile / ops/com.meridian.agent.plist / README
     örneği HÂLÂ sabit `--host 127.0.0.1` taşır (hepsi loopback → bugün fiilî açık yok). Aşağıdaki
     `test_c1_kablolanmamis_baslaticilar_BEYANLI` bunu iddia değil KAYIT olarak tutar.

  B) C25 (FMP yarısı) — SAYAÇ yarısı 2026-08-02'de indi (`stats` + `earnings_refresh_window_partial`)
     ama o yalnız GÖRÜNÜRLÜKTÜ: kısmi pencere (ör. 20 iş gününün 19'u düştü) hâlâ FMP yedeğini
     DENEMİYORDU, çünkü yedek yalnız `not rows` (TAM boşluk) hâlinde çalışıyordu. Operatör kararı:
     gün kapsaması `earnings.EARNINGS_FMP_FALLBACK_COVERAGE`ın (0,90) ALTINDAYSA yedek DENENİR ve
     düşüş `earnings_fallback_partial_window` ile beyan edilir. Nasdaq'ın getirdiği satırlar
     ATILMAZ. Karartma semantiği (`BLACKOUT_DAYS`, `in_blackout`) ve tam-boşluk yolu DEĞİŞMEDİ.

KIRMIZI-ÖNCE: her testin docstring'i düzeltme geri alındığında hangi satırın kırmızıya döneceğini
söyler. Eşik testleri hem ALTINI hem ÜSTÜNÜ hem de TAM DEĞERİNİ sınar — bir eşik yalnız bir yönden
sınandığında "hep tetikler" ile "doğru tetikler" aynı yeşili verir.
"""
from __future__ import annotations

import pathlib
import re

import pytest

from meridian import store

REPO = pathlib.Path(__file__).resolve().parent.parent
SERVE = REPO / "serve.sh"
UNIT = REPO / "deploy" / "oracle-a1" / "meridian.service"
LOOPBACK = ("127.0.0.1", "localhost", "::1")


def _olay(ad: str) -> list[dict]:
    return [e for e in store.read_jsonl("events.jsonl") if (e.get("event") or e.get("kind")) == ad]


def _uvicorn_satiri(metin: str) -> str:
    """serve.sh'in uvicorn'u BAŞLATAN satırı — yorum satırları değil, KOMUT."""
    for line in metin.splitlines():
        kod = line.split("#", 1)[0]
        if "--host" in kod and "uvicorn" in kod:
            return kod
    raise AssertionError("serve.sh: uvicorn'u başlatan `--host`lu satır bulunamadı")


# =================================================================================================
# A — C1: BAĞLANMA ADRESİ TEK KAYNAK
# =================================================================================================
def test_c1_serve_sh_bind_adresini_env_degiskeninden_alir():
    """KIRMIZI-ÖNCE: satır `'--host','127.0.0.1'` sabitine geri dönerse kapı yine ateşlenemez hâle
    gelir — değişken okunur ama BAĞI belirlemez."""
    metin = SERVE.read_text()
    kod = _uvicorn_satiri(metin)
    assert "os.environ['MERIDIAN_BIND_HOST']" in kod or 'os.environ["MERIDIAN_BIND_HOST"]' in kod, \
        f"serve.sh uvicorn satırı bağ adresini MERIDIAN_BIND_HOST'tan ALMIYOR: {kod.strip()}"
    # `--host`tan HEMEN SONRA gelen argüman değişken olmalı; sabit bir IP kalmışsa kapı yine sahte
    assert re.search(r"'--host'\s*,\s*os\.environ\[", kod), \
        "`--host` argümanının HEMEN ardından env okuması gelmiyor — sabit sızmış olabilir"
    # VARSAYILAN DEĞİŞMEDİ: değişken verilmezse loopback (bugünkü davranış bit-bit aynı)
    assert re.search(r'export\s+MERIDIAN_BIND_HOST="\$\{MERIDIAN_BIND_HOST:-127\.0\.0\.1\}"', metin), \
        "serve.sh MERIDIAN_BIND_HOST için 127.0.0.1 VARSAYILANINI export etmiyor"


def test_c1_meridian_service_bind_adresini_env_degiskeninden_alir():
    """KIRMIZI-ÖNCE: ExecStart sabite dönerse ya da `Environment=` satırı silinirse systemd
    değişkeni BOŞ dizeye genişletir — uvicorn kırılır ya da kapı yine hayalet olur."""
    metin = UNIT.read_text()
    exec_satirlari = [l for l in metin.splitlines() if l.startswith("ExecStart=")]
    assert len(exec_satirlari) == 1
    assert "--host ${MERIDIAN_BIND_HOST}" in exec_satirlari[0], \
        f"ExecStart bağ adresini değişkenden ALMIYOR: {exec_satirlari[0]}"

    env_satirlari = [l for l in metin.splitlines() if l.startswith("Environment=MERIDIAN_BIND_HOST=")]
    assert env_satirlari == ["Environment=MERIDIAN_BIND_HOST=127.0.0.1"], \
        f"birim MERIDIAN_BIND_HOST'u loopback VARSAYILANIYLA tanımlamıyor: {env_satirlari}"
    # SYSTEMD TUZAĞI: `Environment=` satırında satır-sonu yorumu DEĞERİN PARÇASI sayılır. Bu satıra
    # bir gün `# ...` eklenirse bağ adresi "127.0.0.1 #" olur ve uvicorn açılmaz.
    assert "#" not in env_satirlari[0]


def test_c1_kapinin_okudugu_ad_ile_baslaticilarin_yazdigi_ad_AYNI():
    """TEK KAYNAK KAYNAK-ÇİVİSİ: kapı ile başlatıcı FARKLI adlara bakarsa (yazım hatası, yeniden
    adlandırma) hiçbir test kırılmadan hayalet girdi GERİ GELİR. Ad api.py'den OKUNUR, elle
    yazılmaz — bu testin kendisi ikinci bir kaynak olmasın diye."""
    import inspect
    from meridian import api
    kaynak = inspect.getsource(api._auth_posture_check)
    adlar = set(re.findall(r'os\.environ\.get\(\s*"([A-Z_]*BIND_HOST[A-Z_]*)"', kaynak))
    assert len(adlar) == 1, f"kapı tek bir bağ değişkeni okumalı, bulunan: {adlar}"
    ad = adlar.pop()
    assert ad in SERVE.read_text(), f"serve.sh kapının okuduğu `{ad}` adını YAZMIYOR"
    assert ad in UNIT.read_text(), f"meridian.service kapının okuduğu `{ad}` adını YAZMIYOR"


def test_c1_kapi_env_degiskeniyle_ATESLENIR(sandbox_state, monkeypatch):
    """ÇEKİRDEK ÇİVİ: genel arayüz + parola YOK → süreç AÇILMAZ. Bu, C1'den önce YAPISAL olarak
    imkânsızdı (değişkeni kimse yazmadığı için kapı hiç ateşlenemezdi)."""
    from meridian import api, auth
    assert auth.password_set() is False, "sandbox parolasız başlamalı (fikstür sızıntısı)"
    monkeypatch.setenv("MERIDIAN_BIND_HOST", "0.0.0.0")
    with pytest.raises(RuntimeError) as ex:
        api._auth_posture_check()
    assert "0.0.0.0" in str(ex.value) and "auth_cli" in str(ex.value), \
        "ret mesajı ne bağ adresini ne çözümü söylüyor — okunmayan bir ret, uyarıdan iyi değildir"


@pytest.mark.parametrize("host", LOOPBACK)
def test_c1_loopback_kapiyi_ateslemez(sandbox_state, monkeypatch, host):
    """GÜRÜLTÜ/YANLIŞ-ALARM KAPISI: bugünkü dağıtım loopback'tedir ve DEĞİŞMEDİ — kapı burada
    ne ret ne `public_bind` uyarısı üretmeli, yoksa düzeltme canlıyı kırardı."""
    from meridian import api
    monkeypatch.setenv("MERIDIAN_BIND_HOST", host)
    api._auth_posture_check()                      # istisna YOK
    assert not _olay("public_bind")


def test_c1_degisken_hic_verilmezse_davranis_BIT_BIT_AYNI(sandbox_state, monkeypatch):
    """GERİYE UYUM: değişkeni vermeyen her çağıran (docker-compose, plist, elle uvicorn) eskisi
    gibi loopback varsayar — düzeltme yeni bir ZORUNLULUK getirmedi."""
    from meridian import api
    monkeypatch.delenv("MERIDIAN_BIND_HOST", raising=False)
    api._auth_posture_check()
    assert not _olay("public_bind")


def test_c1_parola_kuruluysa_genel_bag_UYARIYLA_gecer(sandbox_state, monkeypatch):
    """KAPI BİR YASAK DEĞİL, BİR ŞARTTIR: parola kuruluysa genel bağ AÇILIR ama sessiz kalmaz —
    TLS'in ters vekilde sonlandığı operatöre hatırlatılır."""
    from meridian import api, auth
    auth.set_password("uzun-yeterince-parola")
    monkeypatch.setenv("MERIDIAN_BIND_HOST", "0.0.0.0")
    api._auth_posture_check()                      # istisna YOK
    ev = _olay("public_bind")
    assert ev and "0.0.0.0" in ev[-1]["detail"]


def test_c1_baslaticilarin_varsayilani_hala_LOOPBACK():
    """v77'nin yasası KORUNUYOR: başlatıcı dosyalarının hiçbiri 0.0.0.0'ı KENDİLİĞİNDEN seçmez.
    C1 düzeltmesi savunmayı dosya-taramasından KAPIYA taşıdı; taşımak, eskisini bırakmak değildir."""
    for p in (SERVE, UNIT):
        for line in p.read_text().splitlines():
            kod = line.split("#", 1)[0]
            if "--host" in kod or kod.startswith("Environment=MERIDIAN_BIND_HOST"):
                assert "0.0.0.0" not in kod, f"{p.name}: {line.strip()}"


def test_c1_kablolanmamis_baslaticilar_BEYANLI():
    """UYDURMA YASAĞI / KAPSAM KAYDI: "tüm başlatıcılar tek kaynağa bağlandı" DEMİYORUZ. Bu tur
    yalnız serve.sh + meridian.service'i bağladı; kalanlar sabit loopback taşır ve api.py bunu
    ADIYLA beyan eder. Beyan silinirse bu test kırılır — sessiz bir 'hepsi kapsandı' izlenimi
    tam olarak C1'in kendisidir."""
    import inspect
    from meridian import api
    kaynak = inspect.getsource(api._auth_posture_check)
    for dosya in ("docker-compose.yml", "Dockerfile", "ops/com.meridian.agent.plist"):
        assert dosya in kaynak, f"kapsam DIŞI kalan `{dosya}` api.py'de beyan edilmiyor"
    # ve beyan DOĞRU olmalı: o dosyalar gerçekten sabit loopback taşıyor (beyan çürüdüyse kırıl)
    for dosya in ("docker-compose.yml", "Dockerfile", "ops/com.meridian.agent.plist"):
        p = REPO / dosya
        if p.exists():
            assert "MERIDIAN_BIND_HOST" not in p.read_text(), \
                f"{dosya} artık değişkeni KULLANIYOR — api.py'deki 'kablolanmamış' beyanı BAYAT"


# =================================================================================================
# B — C25 (FMP YARISI): KISMİ PENCEREDE YEDEK EŞİĞİ
# =================================================================================================
def _nasdaq_faki(veri: dict, *, istenen=100, dusen=0):
    """Adaptörün `stats` sözleşmesini birebir taklit eder (bkz. data.nasdaq_earnings_window)."""
    def _f(s, e, **k):
        st = k.get("stats")
        if st is not None:
            st.update(istenen=istenen, cevaplayan=istenen - dusen, dusen=dusen,
                      dusen_gunler=[f"2026-07-{20 + i:02d}" for i in range(min(dusen, 8))],
                      son_hata=("FetchError" if dusen else None),
                      kapsama=(round((istenen - dusen) / istenen, 4) if istenen else None),
                      kapsama_yok_nedeni=(None if istenen else "pencerede iş günü yok"))
        return veri

    return _f


def _yedek_izle(monkeypatch, doner=0):
    """`refresh_from_fmp`i sahteleyip ÇAĞRILDI MI sorusunu ölçer (gerçek uca hiç çıkılmaz)."""
    from meridian import earnings
    cagrildi: list = []
    monkeypatch.setattr(earnings, "refresh_from_fmp", lambda t: cagrildi.append(list(t)) or doner)
    return cagrildi


def test_c25_esik_ADIYLA_sabit_ve_gerekcesi_yazili():
    """SABİT SEÇİLMEZ, GEREKÇELENİR: eşik satır-içi bir literal olsaydı (`< 0.9`) bir sonraki tur
    onu ölçmeden değiştirirdi — bu depodaki 'üç sayı üç dosyada gömülü' kusurunun aynısı."""
    import inspect
    from meridian import earnings
    assert earnings.EARNINGS_FMP_FALLBACK_COVERAGE == 0.90
    kaynak = inspect.getsource(earnings)
    assert "EARNINGS_FMP_FALLBACK_COVERAGE" in inspect.getsource(earnings.refresh), \
        "refresh() eşiği ADIYLA okumuyor — literal sızmış"
    i = kaynak.index("EARNINGS_FMP_FALLBACK_COVERAGE")
    gerekce = kaynak[max(0, i - 2000):i]
    assert "KOTA" in gerekce and "250" in gerekce, "eşiğin kota gerekçesi yazılı değil"


def test_c25_kapsama_esigin_ALTINDA_yedek_denenir_ve_beyan_edilir(sandbox_state, monkeypatch):
    """KIRMIZI-ÖNCE: eski yasa (`if not rows`) geri gelirse burada FMP HİÇ çağrılmaz ve kısmi
    pencere yine sessizce 'başarı' sayılır — karartma o gün-diliminde fail-open kalır."""
    from meridian import earnings
    from meridian.adapters import data as da
    cagrildi = _yedek_izle(monkeypatch, doner=3)
    monkeypatch.setattr(da, "nasdaq_earnings_window",
                        _nasdaq_faki({"AAA": [("2026-08-05", "amc")]}, istenen=100, dusen=11))
    n = earnings.refresh(["AAA"])

    assert cagrildi == [["AAA"]], "kapsama 0,89 < 0,90 iken yedek DENENMEDİ"
    assert n == 1, "dönüş sözleşmesi DEĞİŞMEMELİ: Nasdaq yolunda hâlâ Nasdaq satır sayısı"

    ev = _olay("earnings_fallback_partial_window")
    assert ev, "yedeğe düşüş SESSİZ oldu — hangi turun kotadan harcadığı bilinmez"
    assert ev[-1]["kapsama"] == 0.89 and ev[-1]["esik"] == 0.90
    assert ev[-1]["dusen"] == 11 and ev[-1]["cevaplayan"] == 89
    assert ev[-1]["fmp_satir"] == 3
    assert len(ev[-1]["neden"]) >= 20 and len(ev[-1]["detail"]) >= 20

    ref = _olay("earnings_refreshed")
    assert ref[-1]["source"] == "nasdaq+fmp", "kaynak damgası KARIŞIMI söylemeli"
    assert ref[-1]["fmp_yedek"] == 3 and ref[-1]["fmp_yedek_esigi"] == 0.90


def test_c25_kapsama_esigin_USTUNDE_yedek_denenMEZ(sandbox_state, monkeypatch):
    """KOTA KAPISI: eşik yalnız alt yönden sınanırsa 'hep tetikler' de yeşil verir. 0,91 kapsamada
    yedek çağrılırsa 250 isteklik günlük kota HER kısmi turda yanar."""
    from meridian import earnings
    from meridian.adapters import data as da
    cagrildi = _yedek_izle(monkeypatch)
    monkeypatch.setattr(da, "nasdaq_earnings_window",
                        _nasdaq_faki({"AAA": [("2026-08-05", "amc")]}, istenen=100, dusen=9))
    earnings.refresh(["AAA"])
    assert cagrildi == [], "kapsama 0,91 > 0,90 iken yedek DENENDİ — kota sürüklenmesi"
    assert not _olay("earnings_fallback_partial_window")
    # ama SAYAÇ yarısı hâlâ konuşur: eksik pencere görünürdür, yalnız yedeği hak etmez
    assert _olay("earnings_refresh_window_partial")
    assert _olay("earnings_refreshed")[-1]["fmp_yedek"] is None


def test_c25_esik_TAM_degerinde_yedek_denenMEZ(sandbox_state, monkeypatch):
    """SINIR ÇİVİSİ: karşılaştırma KESİN KÜÇÜKTÜR (`<`). Eşiğin kendisi 'yeterli kapsama'dır;
    `<=` yazılırsa eşik sessizce 0,90'ın bir tık üstüne kayar."""
    from meridian import earnings
    from meridian.adapters import data as da
    cagrildi = _yedek_izle(monkeypatch)
    monkeypatch.setattr(da, "nasdaq_earnings_window",
                        _nasdaq_faki({"AAA": [("2026-08-05", None)]}, istenen=10, dusen=1))
    earnings.refresh(["AAA"])
    assert cagrildi == [], "kapsama TAM eşikte (0,90) iken yedeğe düşüldü"


def test_c25_olculemeyen_kapsama_esigi_TETIKLEMEZ(sandbox_state, monkeypatch):
    """UYDURMA YASAĞI: `kapsama=None` bir sayı DEĞİLDİR. 'Ölçülmedi'yi 'eksik' diye okumak, her
    hafta sonu penceresinde ve her eski/sahte adaptörde kotayı boşa yakardı."""
    from meridian import earnings
    from meridian.adapters import data as da

    cagrildi = _yedek_izle(monkeypatch)
    monkeypatch.setattr(da, "nasdaq_earnings_window",       # SAYAÇ HİÇ DOLMADI (eski uygulama)
                        lambda s, e, **k: {"AAA": ["2026-08-05"]})
    earnings.refresh(["AAA"])
    assert cagrildi == []
    assert _olay("earnings_refreshed")[-1]["gun_olcum_yok"]

    monkeypatch.setattr(da, "nasdaq_earnings_window",       # PENCEREDE İŞ GÜNÜ YOK → kapsama None
                        _nasdaq_faki({"AAA": [("2026-08-06", None)]}, istenen=0, dusen=0))
    earnings.refresh(["AAA"])
    assert cagrildi == [], "ölçülemeyen kapsama eşiği tetikledi"


def test_c25_fmp_kismi_yolunda_NASDAQ_satirlari_korunur(sandbox_state, monkeypatch):
    """ÇEKİRDEK ÇİVİ (operatör şartı): yedek Nasdaq'ı EZMEZ. `refresh_from_fmp` dosyayı BAŞTAN
    yazar (o kusur bu turun kapsamı DIŞINDA, davranışı değişmedi) — bu yüzden kısmi yol, yedeği
    çağırmadan ÖNCE takvimin anlık görüntüsünü alır ve Nasdaq satırlarını EN SON uygular.
    KIRMIZI-ÖNCE: sıra bozulursa hem yeni Nasdaq satırı hem ESKİ çapa kaybolur."""
    from meridian import earnings
    from meridian.adapters import data as da
    from meridian.adapters import fmp

    # 1) TAM kapsamalı bir tur: takvimde ESKİ bir çapa oluşsun (yedek yolu tetiklenmez)
    monkeypatch.setattr(da, "nasdaq_earnings_window",
                        _nasdaq_faki({"OLD": [("2026-09-01", "bmo")]}, istenen=100, dusen=0))
    earnings.refresh(["OLD"])

    # 2) KISMİ tur: Nasdaq tek satır getirir, FMP yedeği BAŞKA tarihler döner
    monkeypatch.setattr(fmp, "available", lambda: True)
    monkeypatch.setattr(fmp, "quota_blocked", lambda: False)
    monkeypatch.setattr(fmp, "earnings_dates", lambda t, strict=False: ["2026-08-20"])
    monkeypatch.setattr(da, "nasdaq_earnings_window",
                        _nasdaq_faki({"AAA": [("2026-08-05", "amc")]}, istenen=100, dusen=50))
    earnings.refresh(["AAA", "BBB"])

    takvim = earnings._load()
    assert "2026-08-05" in takvim.get("AAA", []), "NASDAQ satırı FMP yazımıyla EZİLDİ"
    assert earnings.report_time("AAA", "2026-08-05") == "amc", "Nasdaq'ın SAAT bilgisi kayboldu"
    assert "2026-08-20" in takvim.get("AAA", []), "FMP satırı eklenmedi"
    assert "2026-08-20" in takvim.get("BBB", []), "FMP'nin YENİ sembolü eklenmedi"
    assert "2026-09-01" in takvim.get("OLD", []), "ESKİ çapa düştü — yazım üst küme değil"
    assert earnings.report_time("OLD", "2026-09-01") == "bmo"


def test_c25_TAM_BOSLUK_davranisi_degismedi(sandbox_state, monkeypatch):
    """REGRESYON: eşiğin diğer ucu. Nasdaq HİÇ satır döndürmezse yol eskisi gibi FMP'ye düşer,
    FMP'nin sayısını DÖNDÜRÜR ve iki kaynak da boşsa `earnings_refresh_empty` basar."""
    from meridian import earnings
    from meridian.adapters import data as da

    cagrildi = _yedek_izle(monkeypatch, doner=7)
    monkeypatch.setattr(da, "nasdaq_earnings_window", _nasdaq_faki({}, istenen=100, dusen=100))
    assert earnings.refresh(["AAA"]) == 7 and cagrildi == [["AAA"]]
    # tam-boşluk yolu KENDİ olayını basar; kısmi-pencere olayı bu yolda ÇIKMAZ (iki olgu ayrı)
    assert not _olay("earnings_fallback_partial_window")
    assert not _olay("earnings_refresh_empty")

    cagrildi2 = _yedek_izle(monkeypatch, doner=0)
    earnings.refresh(["AAA"])
    assert cagrildi2 == [["AAA"]]
    assert _olay("earnings_refresh_empty"), "İKİ KAYNAK DA BOŞ sessiz geçti"


def test_c25_karartma_semantigi_DEGISMEDI(sandbox_state, monkeypatch):
    """KAPSAM ÇİVİSİ: bu tur FETCH tarafına dokundu, KARAR tarafına değil. `in_blackout` bit-bit
    aynı kalmalı — yedeğe düşmek hangi planın karartıldığını DEĞİŞTİRMEZ."""
    from meridian import earnings
    from meridian.adapters import data as da
    assert earnings.BLACKOUT_DAYS == 5 and earnings.TIME_TIGHTEN is False

    _yedek_izle(monkeypatch, doner=0)
    monkeypatch.setattr(da, "nasdaq_earnings_window",
                        _nasdaq_faki({"AAA": [("2026-08-20", "bmo")]}, istenen=100, dusen=50))
    earnings.refresh(["AAA"])                       # yedek yolu KOŞTU (kapsama 0,50)
    assert earnings.in_blackout("AAA", "2026-08-16") is True     # 4 gün önce → karartma
    assert earnings.in_blackout("AAA", "2026-08-14") is False    # 6 gün önce → serbest
    assert earnings.in_blackout("AAA", "2026-08-20") is True     # rapor günü (TIME_TIGHTEN kapalı)
    assert earnings.in_blackout("YOK", "2026-08-16") is False    # kapsam dışı → fail-open (beyanlı)
