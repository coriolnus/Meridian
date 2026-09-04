"""v177 — SINIF: "TEST GERÇEK AĞA ÇIKAR". Kapsam testi: `tests/conftest.py::_dis_ag_kapali`.

VAKA (2026-08-02, canlı-bekçi avında bulunan açık #1). `test_regime_patch::
test_scheduler_flag_survives_publish_lag` GERÇEK kadans makinesini koşturuyor ve
`scheduler.advance_once → earnings.refresh → adapters.data.nasdaq_earnings_window` yolu
api.nasdaq.com'a GÜN BAŞINA bir HTTP isteği atıyordu. Yol yamalanmamıştı, kimse fark etmemişti,
çünkü test YEŞİLDİ — ve yeşilliği tam da sorunun kendisiydi: ölçtüğü şey kod değil, o günün
interneti. `earnings.refresh` gün kapsaması 0,90 eşiğinin altına düşünce FMP YEDEĞİNE indiği için
aynı yol GERÇEK anahtarla 250/gün kotayı da yakabiliyordu.

SEÇİLEN ADAY: BİRİNCİL — conftest'te autouse SOKET-DÜZEYİ kapı (`socket.socket.connect` /
`connect_ex` sarılır; AF_UNIX + loopback geçer, dış IP bağlantı DENENMEDEN `DisAgErisimiKapali`
ile düşer). Yedek aday (yalnız `data._get_json` saplaması) GEREKMEDİ ve KULLANILMADI: yedek
sınıfın yalnız `data.py` dilimini kapatırdı; ölçüm birincili reddetmedi.

ÖLÇÜM (13 dosyalık süpürme: regime_patch, canli_bekci_v176, denetim_verihatti_v157,
wpd_kalanlar_v147, hotstate_v83, hotstate_bars_v84, marketstream_v84, barsarchive_v116,
loop_gaps_v48, pead_v93, canslim_v94, denetim_gozetim_v158, na_revision_v53 — 226 test):
  · KAPI YOKKEN : 0 FAILED / 0 ERROR · 4 ayrı dış IP'ye 37 TCP bağlantı ·  70,8sn duvar / 20,0sn CPU
  · KAPILIYKEN  : 0 FAILED / 0 ERROR · dış TCP bağlantı 0             · 153,7sn duvar / 22,3sn CPU
  · FAILED KÜME DİFF'İ: BOŞ — yeni kırmızı 0, hiçbir teste yama gerekmedi.
  · HEDEF KANIT : `test_scheduler_flag_survives_publish_lag` tek başına kapıyla YEŞİL (2/2 koşum).

SÜRE ŞİŞMESİ BEYAN EDİLİR (kabul edilmiş bedel, gizlenmez): süpürmenin +82,9sn'sinin TAMAMI tek
teste düşüyor — `test_scheduler_flag_survives_publish_lag` 126,2sn (aynı dosyadaki ikinci en yavaş
test 0,21sn). Artan şey AĞ DEĞİL `time.sleep`tir: kapı `_get_json`ı üç deneme boyunca düşürür
(0,4+0,8+1,6sn geri çekilme + 0,25sn polite_delay) ve `nasdaq_earnings_window` bunu ~20 iş günü
için, iki `refresh` turunda yapar (≈ 2 × 20 × 3,05sn ≈ 122sn — ölçülenle uyuşuyor). CPU'nun
20,0→22,3sn'de kalması bunun kanıtıdır. Yani şişme kapının değil, ÜRETİMDEKİ dürüst yeniden-deneme
merdiveninin artık GERÇEKTEN koşuyor olmasının bedelidir; üretim davranışı DEĞİŞTİRİLMEDİ ve o
testin beklentisine DOKUNULMADI (süre şişmesi bu turda bilerek kabul edildi).
"""
import socket

import pytest

from tests.conftest import DisAgErisimiKapali


# ---- (a) DIŞ ADRES: BAĞLANMADAN DÜŞER -----------------------------------------------------------
# HEDEFLER BİLEREK SAHTE: 203.0.113.0/24 (RFC 5737 TEST-NET-3) ve 2001:db8::/32 (RFC 3849) belge/
# test için AYRILMIŞ bloklardır — yönlendirilmezler. Yani bu test, kapı BOZUK OLSA BİLE gerçek bir
# dış makineye paket göndermez. Ağ kapısını sınayan bir testin kendisinin ağa çıkması, ölçtüğü
# kusurun ta kendisi olurdu.
@pytest.mark.parametrize("aile,adres", [
    (socket.AF_INET, ("203.0.113.7", 80)),
    (socket.AF_INET6, ("2001:db8::1", 80)),
    # ÇÖZÜMLENMEMİŞ AD: kapı ad çözmez ve çözemediği bir adı YEREL SAYMAZ. Bu dal olmasaydı,
    # hostname ile bağlanan bir istemci (adı kendi çözen kütüphaneler) kapıdan sızardı.
    (socket.AF_INET, ("api.nasdaq.com", 443)),
])
def test_dis_adres_baglanmadan_adli_istisnayla_duser(aile, adres):
    """Dış adres BAĞLANTI DENENMEDEN düşer ve istisna ADLIDIR (sessiz errno ya da genel OSError değil)."""
    s = socket.socket(aile, socket.SOCK_STREAM)
    try:
        with pytest.raises(DisAgErisimiKapali) as ei:
            s.connect(adres)
        # PAKET GİTMEDİ: bağlantı kurulmuş olsa `getpeername` uzak ucu verirdi; kurulmadıysa atar.
        with pytest.raises(OSError):
            s.getpeername()
        # MESAJ YOLU TARİF EDER — kapı "hayır" demekle yetinmez, ne yapılacağını söyler. Bu satır
        # kozmetik değil: bir bekçi, nasıl aşılacağını söylemiyorsa aşılmak yerine SÖKÜLÜR.
        m = str(ei.value)
        assert "_get_json" in m and "monkeypatch" in m and "loopback" in m

        # `connect_ex` de ATAR (errno DÖNDÜRMEZ): sessiz bir errno, bulunan yamalanmamış yolu
        # çağıranın "bağlanamadım" dalına gömer ve kapı kurulu ama görünmez olurdu.
        s2 = socket.socket(aile, socket.SOCK_STREAM)
        try:
            with pytest.raises(DisAgErisimiKapali):
                s2.connect_ex(adres)
        finally:
            s2.close()
    finally:
        s.close()


def test_istisna_genel_yutuculardan_gecer_ama_osError_degildir():
    """SÖZLEŞMENİN İKİ UCU: `Exception` türevidir (üretimin dürüst fail-open yolları — `_get_json`
    üç denemeyi `FetchError`a çevirir, `nasdaq_earnings_window` günü gün-bazında yutar — KIRILMAZ),
    ama `OSError` DEĞİLDİR (httpx/httpcore bağlantı-hatası eşlemesine takılıp `ConnectError`e
    dönüşseydi kapı, kapattığı ağ yokluğunu TAKLİT eder ve görünmez olurdu)."""
    assert issubclass(DisAgErisimiKapali, Exception)
    assert not issubclass(DisAgErisimiKapali, OSError)


# ---- (b) MAKİNE İÇİ TRAFİK GEÇER ----------------------------------------------------------------
def test_loopback_gercek_dinleyiciye_baglanabilir():
    """LOOPBACK GEÇER — ve bu SAHTE bir geçiş değil: gerçek bir dinleyici kurulur, gerçekten
    bağlanılır, gerçekten veri akar. Gerekçe kolaylık değil ZORUNLULUK: `hotstate` kendi testleri
    (v83/v84) `redis://127.0.0.1:6379` ile GERÇEK Redis'e gider ve bu kapı onların ÜSTÜNDE durur.
    Kapı loopback'i kesseydi o iki dosya toptan kırmızıya dönerdi."""
    with socket.create_server(("127.0.0.1", 0)) as srv:
        host, port = srv.getsockname()[:2]
        with socket.create_connection((host, port), timeout=5) as istemci:
            kabul, _ = srv.accept()
            with kabul:
                kabul.sendall(b"meridian")
                assert istemci.recv(16) == b"meridian"


def test_af_unix_gecer(tmp_path, monkeypatch):
    """AF_UNIX GEÇER: yerel IPC hiç IP trafiği DEĞİLDİR, kapının konusu dışıdır. Adres bir dosya
    yoludur — `adres[0]` okuması oraya hiç inmemelidir (aile kontrolü ÖNCE gelir).

    NEDEN GÖRELİ AD + `chdir`, MUTLAK `tmp_path` DEĞİL: `sun_path` macOS'ta 104 BAYTLA sınırlıdır ve
    pytest'in `/var/folders/.../pytest-of-<kullanıcı>/pytest-N/<test adı>0/` yolu tek başına o
    sınırı aşıyor ("OSError: AF_UNIX path too long" — bu testi yazarken ölçüldü). Göreli ad bağlama
    kısa kalır ve soket dosyası yine tmp_path içinde doğar; `monkeypatch.chdir` cwd'yi söküm
    sırasında geri koyar (elle `os.chdir` komşu testlerin çalışma dizinini sızdırırdı)."""
    monkeypatch.chdir(tmp_path)
    yol = "s.sock"
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as srv:
        srv.bind(yol)
        srv.listen(1)
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as istemci:
            istemci.connect(yol)                      # kapıdan geçmeli — istisna ATMAMALI
            kabul, _ = srv.accept()
            with kabul:
                kabul.sendall(b"ok")
                assert istemci.recv(8) == b"ok"


# ---- (c) TESTİN KENDİ YAMASI KAZANIR (v157 sözleşmesi) ------------------------------------------
def test_testin_kendi_get_json_yamasi_kazanir(sandbox_state, monkeypatch):
    """Kapı, ADAPTÖRÜNÜ YAMALAYAN bir testin yoluna ÇIKMAZ ve onu yavaşlatmaz.

    Rekabet yoktur çünkü katmanlar farklıdır: yama `data._get_json`da, kapı soketin kendisinde —
    yamalanmış yol soket katmanına hiç İNMEZ ve kapı sessiz kalır. v157'nin (denetim C25) kayıtlı
    deseni budur; bu test o desenin kapı ALTINDA da geçerli kaldığını sabitler, yoksa v177 kapısı
    v157'nin `stats` ölçümünü sessizce başka bir şeye çevirirdi."""
    from meridian.adapters import data

    cagrilar = []

    class _Cevap:
        @staticmethod
        def json():
            return {"data": {"rows": [{"symbol": "AAA", "time": "time-pre-market"}]}}

    def _sahte(url, timeout, attempts=3):
        cagrilar.append(url)
        return _Cevap()

    monkeypatch.setattr(data, "_get_json", _sahte)

    stats: dict = {}
    out = data.nasdaq_earnings_window("2026-07-27", "2026-07-28", polite_delay=0.0, stats=stats)

    assert cagrilar and all(u.startswith("https://api.nasdaq.com/") for u in cagrilar)
    assert out == {"AAA": ["2026-07-27", "2026-07-28"]}
    assert stats["istenen"] == 2 and stats["cevaplayan"] == 2 and stats["dusen"] == 0
    assert stats["kapsama"] == 1.0 and stats["son_hata"] is None


# ---- (d) YAMALANMAMIŞ YOL: KAPI DÜŞÜRÜR, ÜRETİM DÜRÜSTÇE DEĞERSİZLEŞİR --------------------------
def test_refresh_kapiyla_istisnasiz_dusup_kismi_pencereyi_beyan_eder(sandbox_state, monkeypatch):
    """Vakanın KENDİSİ, kum havuzunda: `earnings.refresh` HİÇ yamalanmadan çağrılır.

    BEKLENEN DAVRANIŞ ÜÇ PARÇALI ve üçü de üretimin ZATEN yazılı yolu (kapı hiçbirini değiştirmez):
      (1) İSTİSNA SIZMAZ — `_get_json` üç denemeyi `FetchError`a çevirir, `nasdaq_earnings_window`
          günü GÜN BAZINDA yutar. Kapının `Exception` türevi olmasının sınandığı yer burasıdır.
      (2) SESSİZ DEĞİL — `stats` düşen günü sayar ve `earnings_refresh_window_partial` uyarısı
          basılır; ardından iki kaynak da boş kaldığı için `earnings_refresh_empty` gelir. "Yeni
          satır yok" ile "İKİ KAYNAK DA KONUŞMADI" aynı sayıyla anlatılamaz (bkz. refresh, YASA 4).
      (3) SATIR YOK — dönüş 0. FMP yedeği de kapının altındadır, yani kota YANMAZ: bu test
          operatörün makinesinde FMP anahtarı OLSA DA OLMASA DA aynı sonucu verir (makineye bağlı
          bir test, geçtiğinde de hiçbir şey kanıtlamaz — `_yerel_ajan_ikilisi_kapali` dersi).

    PENCERE DARALTILDI (`refresh_window` yamalı, TEK İŞ GÜNÜ): gerçek pencere -7/+21 gün ≈ 20 iş
    günüdür ve her günü üç kez denemek bu tek testi ~60sn'ye çıkarırdı. Daraltılan şey ÖLÇÜLEN
    DAVRANIŞ değil, onun tekrar SAYISIdır — merdivenin kendisi (3 deneme, gerçek geri çekilme)
    aynen koşar."""
    from meridian import earnings, obs

    monkeypatch.setattr(earnings, "refresh_window", lambda today=None: ("2026-07-27", "2026-07-27"))
    uyarilar = []
    monkeypatch.setattr(obs, "warn", lambda ev, **kw: uyarilar.append((ev, kw)))

    n = earnings.refresh(["AAPL"])                     # İSTİSNA ATMAMALI

    assert n == 0
    olaylar = [e for e, _ in uyarilar]
    assert "earnings_refresh_window_partial" in olaylar
    assert "earnings_refresh_empty" in olaylar

    kismi = dict(next(kw for e, kw in uyarilar if e == "earnings_refresh_window_partial"))
    assert kismi["istenen"] == 1 and kismi["cevaplayan"] == 0 and kismi["dusen"] == 1
    assert kismi["kapsama"] == 0.0                    # ÖLÇÜLDÜ ve 0 — "ölçülmedi" (None) DEĞİL
    # Düşüşün nedeni KAYDA GEÇER: `_get_json` son istisnayı `FetchError`a sarar, yani günün düşme
    # sebebi "ağ kapalıydı" diye okunabilir kalır — sessiz bir boşluk değil.
    assert kismi["son_hata"] == "FetchError"

    bos = dict(next(kw for e, kw in uyarilar if e == "earnings_refresh_empty"))
    assert bos["sources"] == "nasdaq+fmp" and bos["universe"] == 1
