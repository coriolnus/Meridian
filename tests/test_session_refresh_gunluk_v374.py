"""v374 — `session_refresh` defteri: (ip, yol) → GÜNLÜK ÖZET (TSK-106) → IP BAŞINA (TSK-006).

KİMLİK NOTU (vNNN çakışma kuralı, 2026-09-02): brief bu dosyaya `v371` öneriyordu.
`tests/test_rejim_tam_pencere_v371.py` o numarayı ZATEN taşıyor (v370/v372/v373 de dolu).
Numara KİMLİKTİR ve çakışmada AZ-ÇAPALI taraf taşınır — bu dosya henüz hiçbir yerden
çapalanmamıştı, dolayısıyla taşınan odur: bir sonraki boş numara v374.

SÖZLEŞME İKİNCİ KEZ DARALDI (TSK-006, 2026-09-03 — Rol-1 hükmü). TSK-106 anahtarı (ip, yol)
BIRAKMIŞTI ve canlı ölçüm kalan sınıfı gösterdi (A1, son 24 saat, 2026-09-03 06:3xZ):
977 olayın 106'sı `session_refresh`, 97'si `ozet=False` İLK-SATIR — çünkü restart/pano açılışında
57 AYRI YOL için birer "ilk olay" doğuyordu (saatlik tepe 44). Kararlı durumda günlük özet de yol
başına bir satır olacaktı (57/gün). Anahtar artık YALNIZ IP'dir.

SINANAN SÖZLEŞME (`meridian/api.py::_session_refresh_ornekle`):
  * anahtar IP'dir; pencere UTC TAKVİM GÜNÜdür — monotonic pencere DEĞİL,
  * IP'nin İLK olayı (süreç belleğinde kaydı yokken) ANINDA yazılır (`ozet=False`) ve `yol`
    alanı O olayın yolunu taşır — kaç yol olduğunu SÖYLEMEZ (o an ölçülmemiştir: uydurma yok),
  * aynı UTC günündeki SONRAKİ olaylar YAZILMAZ; bellekte sayaç + damgalar + YOL DAĞILIMI birikir,
  * gün dönüşünde ÖNCEKİ günün özeti TEK satır yazılır: `ozet=True` + `gun` + `toplam_n`
    + `ilk_ts` + `son_ts` + `yollar` ({yol: n}, en sık `_REFRESH_YOL_OZET`) + `diger_n`.
    Olay ADI `session_refresh` KALIR (grep sürekliliği),
  * yeni günün ilk olayı ANINDA YAZILMAZ (IP'nin kaydı artık VAR) — sayaçtan başlar,
  * TOPLAM KORUNUMU (formül TSK-106'dan DEĞİŞMEDİ): bir günün gerçek olay sayısı =
        (o gün anında yazılan ilk satır varsa 1, yoksa 0) + o günün özetindeki `toplam_n`,
  * DAĞILIM KORUNUMU (TSK-006 ile YENİ): `sum(yollar.values()) + diger_n == toplam_n` —
    özet satırı kendi içinde tutarlıdır, yoksa "hangi yol kaç kez" sayısı sessizce ayrışırdı,
  * İKİ TAVAN, İKİSİ DE BEYANLI: `_REFRESH_TAVAN` (bellekte tutulan IP sayısı; EN ESKİ GÖRÜLEN
    düşer, biriken sayacı KAYBOLUR) ve `_REFRESH_YOL_TAVANI` (IP başına bellekte tutulan AYRIK
    yol sayısı; taşan olaylar SAYIYI kaybetmez, `diger_n`e düşer),
  * duvar saati GERİ alınırsa gün anahtarı TEKRARLANABİLİR → aynı `gun` için ikinci bir
    özet satırı doğabilir. Kabul edilmiş, api.py blok yorumunda BEYANLI davranıştır.

ZAMAN ENJEKTE EDİLİR, DUVAR SAATİNE BAĞLANILMAZ: çekirdek örnekleyici `now`u (UTC epoch
saniye) dışarıdan alır ve `gun`/`ilk_ts`/`son_ts` damgalarının HEPSİNİ o TEK değerden türetir.
Testin beklediği tarih dizgileri ELDE yazılır; epoch üreteci `calendar.timegm`tir — üretim
kodunun (`datetime.fromtimestamp`) damga yolundan BAĞIMSIZ bir yol, yoksa aynı hatayı iki
tarafta birden yapıp yeşil kalırdık.
"""
from __future__ import annotations

import calendar
import json
import time

import pytest
from fastapi.testclient import TestClient

from meridian import api, auth

IP = "127.0.0.1"
YOL = "/api/summary"


def _epoch(y: int, ay: int, g: int, sa: int = 0, dk: int = 0, sn: int = 0) -> float:
    """UTC epoch saniye — `calendar.timegm` üzerinden (üretimin damga yolundan bağımsız)."""
    return float(calendar.timegm((y, ay, g, sa, dk, sn, 0, 0, 0)))


def _olaylar(state) -> list[dict]:
    p = state / "events.jsonl"
    if not p.exists():
        return []
    return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]


def test_epoch_uretecinin_kendisi_DOGRU(sandbox_state):
    """Pozitif kontrol: bu dosyanın TÜM beklentileri `_epoch`e dayanıyor. Üreteç kayarsa her
    çivi yanlış tarihe bakar ve sessizce yeşil kalırdı."""
    assert _epoch(2026, 9, 2) == 1788307200.0
    assert _epoch(2026, 9, 3) - _epoch(2026, 9, 2) == 86400.0


# ---- çekirdek örnekleyici: saf, `now` enjekte edilir -------------------------------------------
def test_IPnin_ILK_olayi_ANINDA_yazilir(sandbox_state):
    """Madde 2: kaydı olmayan IP'nin ilk olayı beklemez — görünürlük kapısı."""
    karar = api._session_refresh_ornekle(IP, YOL, now=_epoch(2026, 9, 2, 9))
    assert karar == {"ozet": False}, karar


def test_ANINDA_satiri_YOL_SAYISI_UYDURMAZ(sandbox_state):
    """TSK-006 hükmü: anında satır yalnız `ozet=False` taşır. `yollar_n` gibi bir sayaç,
    O ANDA ölçülmemiş bir büyüklüğü ölçülmüş gibi gösterirdi (uydurma yasağı) — yolun kendisi
    `obs.log`un `yol=` alanında zaten var ve o TEK olayın ölçülmüş yoludur."""
    karar = api._session_refresh_ornekle(IP, YOL, now=_epoch(2026, 9, 2, 9))
    assert set(karar) == {"ozet"}, karar


def test_AYNI_UTC_GUNUNDEKI_sonraki_olaylar_YAZILMAZ(sandbox_state):
    """Madde 3: gün içi kadans deftere DÜŞMEZ; bellekte sayaç + damga + dağılım birikir."""
    f = api._session_refresh_ornekle
    assert f(IP, YOL, now=_epoch(2026, 9, 2, 0, 0, 1)) == {"ozet": False}
    for saat in (1, 9, 15, 23):
        assert f(IP, YOL, now=_epoch(2026, 9, 2, saat)) is None, saat


def test_ANAHTAR_YALNIZ_IP_farkli_yol_YENI_SATIR_URETMEZ(sandbox_state):
    """TSK-006'nın ASIL İDDİASI (canlı ölçüm: 57 yol → 57 anında satır). Aynı IP'nin İKİNCİ
    bir yolu artık kendi "ilk olay" satırını doğurmaz; dağılıma girer."""
    f = api._session_refresh_ornekle
    assert f(IP, YOL, now=_epoch(2026, 9, 2, 9)) == {"ozet": False}
    assert f(IP, "/api/today", now=_epoch(2026, 9, 2, 9, 0, 1)) is None
    assert f(IP, "/api/inbox", now=_epoch(2026, 9, 2, 9, 0, 2)) is None
    assert set(api._REFRESH_SON) == {IP}, api._REFRESH_SON


def test_AYRI_IP_AYRI_KAYIT(sandbox_state):
    """Kesim IP'leri BİRBİRİNE karıştırmaz: ayrı istemcinin görünürlüğü kaybolmamalı."""
    f = api._session_refresh_ornekle
    assert f(IP, YOL, now=_epoch(2026, 9, 2, 9)) == {"ozet": False}
    assert f("10.0.0.9", YOL, now=_epoch(2026, 9, 2, 9, 0, 2)) == {"ozet": False}
    assert f(IP, YOL, now=_epoch(2026, 9, 2, 10)) is None
    assert set(api._REFRESH_SON) == {IP, "10.0.0.9"}


def test_GUN_DONUSUNDE_onceki_gunun_OZETI_TEK_satir_YOL_DAGILIMIYLA(sandbox_state):
    """Madde 4: özet `gun`/`toplam_n`/`ilk_ts`/`son_ts` + `yollar`/`diger_n` taşır.

    `ilk_ts` o günün GERÇEK ilk olayıdır (anında yazılan satırın anı dahil) — bir damga,
    bir sayaç değil; `toplam_n` ise anında yazılan satırı SAYMAZ (toplam korunumu formülü)
    ve `yollar` da onu saymaz (dağılım korunumu `toplam_n` ile hizalıdır)."""
    f = api._session_refresh_ornekle
    assert f(IP, YOL, now=_epoch(2026, 9, 2, 9)) == {"ozet": False}
    assert f(IP, YOL, now=_epoch(2026, 9, 2, 12)) is None
    assert f(IP, "/api/today", now=_epoch(2026, 9, 2, 23, 59, 59)) is None
    ozet = f(IP, YOL, now=_epoch(2026, 9, 3, 0, 0, 1))
    assert ozet == {"ozet": True, "gun": "2026-09-02", "toplam_n": 2,
                    "ilk_ts": "2026-09-02T09:00:00+00:00",
                    "son_ts": "2026-09-02T23:59:59+00:00",
                    "yollar": {YOL: 1, "/api/today": 1}, "diger_n": 0}, ozet


def test_YENI_GUNUN_ilk_olayi_ANINDA_YAZILMAZ_sayactan_baslar(sandbox_state):
    """Madde 4 kuyruğu: özet yazıldıktan sonra yeni gün madde-2 anındalığına DÖNMEZ.

    Kararlı durum IP başına günde ~1 satırdır; yeni günün ilk olayı da anında yazılsaydı
    günde 2 satır olur ve kesimin yarısı geri gelirdi."""
    f = api._session_refresh_ornekle
    f(IP, YOL, now=_epoch(2026, 9, 2, 9))
    f(IP, YOL, now=_epoch(2026, 9, 2, 10))
    assert f(IP, YOL, now=_epoch(2026, 9, 3, 8))["ozet"] is True   # gün dönüşü özeti
    assert f(IP, YOL, now=_epoch(2026, 9, 3, 9)) is None           # yeni gün: SESSİZ
    assert f(IP, "/api/today", now=_epoch(2026, 9, 3, 10)) is None
    ozet2 = f(IP, YOL, now=_epoch(2026, 9, 4, 1))
    assert ozet2["gun"] == "2026-09-03" and ozet2["toplam_n"] == 3, ozet2
    assert ozet2["ilk_ts"] == "2026-09-03T08:00:00+00:00", ozet2
    assert ozet2["son_ts"] == "2026-09-03T10:00:00+00:00", ozet2
    assert ozet2["yollar"] == {YOL: 2, "/api/today": 1}, ozet2


def test_TOPLAM_KORUNUMU_formulu(sandbox_state):
    """Madde 7: gerçek olay sayısı = (anında yazılan ilk satır: 1) + özetteki `toplam_n`.

    İki dünya AYRI ölçülür: IP'nin İLK günü (anında satır VAR → pay 1) ve sonraki bir gün
    (anında satır YOK → pay 0). Formül tek dünyada sınanırsa diğerinde sessizce kayar."""
    f = api._session_refresh_ornekle
    # --- 1. gün: 6 gerçek olay (üç ayrı yol), biri anında yazıldı
    anlar = [(_epoch(2026, 9, 2, 8, dk), f"/api/y{dk % 3}") for dk in range(6)]
    yazilan_1 = sum(1 for t, y in anlar if f(IP, y, now=t) is not None)
    assert yazilan_1 == 1, "ilk gün tam bir satır yazmalıydı (anında görünürlük)"
    ozet1 = f(IP, YOL, now=_epoch(2026, 9, 3, 8))
    assert 1 + ozet1["toplam_n"] == len(anlar), ozet1

    # --- 2. gün: 4 gerçek olay (ilki gün dönüşünü tetikleyen), anında satır YOK
    for dk in range(1, 4):
        assert f(IP, YOL, now=_epoch(2026, 9, 3, 8, dk)) is None
    ozet2 = f(IP, YOL, now=_epoch(2026, 9, 4, 8))
    assert 0 + ozet2["toplam_n"] == 4, ozet2


def test_DAGILIM_KORUNUMU_yollar_artı_diger_n_toplam_n_eder(sandbox_state):
    """TSK-006 ile YENİ: özet satırı KENDİ İÇİNDE tutarlıdır. `yollar` kırpılınca kaybolan
    sayı `diger_n`e düşer — kırpma bir SAYIYI değil yalnız AYRINTIYI eksiltir."""
    f = api._session_refresh_ornekle
    f(IP, "/a", now=_epoch(2026, 9, 2, 8))                       # anında satır (sayılmaz)
    n = api._REFRESH_YOL_OZET + 5                                # özet kırpmasını AŞ
    for i in range(n):
        for tekrar in range(i % 3 + 1):                          # farklı frekanslar
            f(IP, f"/y{i}", now=_epoch(2026, 9, 2, 9, i, tekrar))
    ozet = f(IP, YOL, now=_epoch(2026, 9, 3, 1))
    assert len(ozet["yollar"]) == api._REFRESH_YOL_OZET, len(ozet["yollar"])
    assert sum(ozet["yollar"].values()) + ozet["diger_n"] == ozet["toplam_n"], ozet
    assert ozet["diger_n"] > 0, "kırpma oldu ama `diger_n` sıfır — sayı sessizce kayboldu"


def test_OZET_EN_SIK_yollari_tutar(sandbox_state):
    """Kırpma keyfî değil: en SIK yollar kalır (operatör "en çok hangi uç yokladı" sorusunu
    sorar; rastgele 20 yol o soruya cevap vermezdi)."""
    f = api._session_refresh_ornekle
    f(IP, "/ilk", now=_epoch(2026, 9, 2, 8))
    for i in range(api._REFRESH_YOL_OZET + 3):
        for tekrar in range(i + 1):                              # /y0 en seyrek, sonuncusu en sık
            f(IP, f"/y{i}", now=_epoch(2026, 9, 2, 9, i, tekrar % 60))
    ozet = f(IP, YOL, now=_epoch(2026, 9, 3, 1))
    en_sik = f"/y{api._REFRESH_YOL_OZET + 2}"
    assert en_sik in ozet["yollar"], ozet["yollar"]
    assert "/y0" not in ozet["yollar"], "en SEYREK yol kırpılmadı"


def test_YOL_TAVANI_asilinca_SAYI_KAYBOLMAZ_diger_n_e_duser(sandbox_state, monkeypatch):
    """İKİNCİ TAVAN (TSK-006 ile yeni, BEDEL BEYANI'nın parçası): anahtar IP olunca tek bir
    kaydın yol sözlüğü sınırsız büyüyebilirdi — eski (ip, yol) anahtarında `_REFRESH_TAVAN`
    bunu dolaylı sınırlıyordu. Tavan AYRINTIYI keser, SAYIYI kesmez."""
    monkeypatch.setattr(api, "_REFRESH_YOL_TAVANI", 3)
    f = api._session_refresh_ornekle
    f(IP, "/ilk", now=_epoch(2026, 9, 2, 8))
    for i in range(6):
        assert f(IP, f"/y{i}", now=_epoch(2026, 9, 2, 9, i)) is None
    ozet = f(IP, YOL, now=_epoch(2026, 9, 3, 1))
    assert len(ozet["yollar"]) == 3, ozet["yollar"]
    assert ozet["diger_n"] == 3, ozet
    assert sum(ozet["yollar"].values()) + ozet["diger_n"] == ozet["toplam_n"] == 6, ozet


def test_TAVAN_asilinca_EN_ESKI_GORULEN_kayit_duser(sandbox_state, monkeypatch):
    """Madde 5: `_REFRESH_TAVAN` KALIR (artık IP sayar); düşen kaydın biriken sayacı KAYBOLUR
    (beyanlı bedel).

    "En eski" YARATILIŞ sırası değil SON GÖRÜLME damgasıdır: canlı yoklayıcı yıllarca aynı
    IP'yi kullanır, yaratılışa göre düşürmek en CANLI kaydı kurban ederdi."""
    monkeypatch.setattr(api, "_REFRESH_TAVAN", 3)
    f = api._session_refresh_ornekle
    for i, ip in enumerate(("10.0.0.1", "10.0.0.2", "10.0.0.3")):
        assert f(ip, YOL, now=_epoch(2026, 9, 2, 9, i)) == {"ozet": False}
    # 10.0.0.1 EN SON görülene çekilir → artık en eski O DEĞİL 10.0.0.2'dir
    assert f("10.0.0.1", YOL, now=_epoch(2026, 9, 2, 9, 3)) is None
    assert f("10.0.0.4", YOL, now=_epoch(2026, 9, 2, 9, 4)) == {"ozet": False}
    assert set(api._REFRESH_SON) == {"10.0.0.1", "10.0.0.3", "10.0.0.4"}, api._REFRESH_SON
    # BEYANLI BEDEL: düşen kaydın sayacı gitti — 10.0.0.2 yeniden "ilk olay" gibi davranır
    assert f("10.0.0.2", YOL, now=_epoch(2026, 9, 2, 9, 5)) == {"ozet": False}


def test_DUVAR_SAATI_GERI_ALINIRSA_gun_anahtari_TEKRARLANIR_BEYANLI(sandbox_state):
    """Madde 6 bedeli: gün anahtarı monotonic değildir; geri alınan saat aynı `gun` için
    İKİNCİ bir özet satırı doğurabilir. Bu bir arıza değil, BEYANLI davranıştır — çivi onu
    yakalar ki bir gün sessizce değişmesin."""
    f = api._session_refresh_ornekle
    f(IP, YOL, now=_epoch(2026, 9, 2, 10))
    assert f(IP, YOL, now=_epoch(2026, 9, 2, 11)) is None
    o1 = f(IP, YOL, now=_epoch(2026, 9, 3, 1))
    assert o1["gun"] == "2026-09-02" and o1["toplam_n"] == 1, o1
    # saat GERİ alındı: 03 kaydı 02'ye döner → 03'ün (kısacık) özeti yazılır
    o2 = f(IP, YOL, now=_epoch(2026, 9, 2, 12))
    assert o2 == {"ozet": True, "gun": "2026-09-03", "toplam_n": 1,
                  "ilk_ts": "2026-09-03T01:00:00+00:00",
                  "son_ts": "2026-09-03T01:00:00+00:00",
                  "yollar": {YOL: 1}, "diger_n": 0}, o2
    # saat ileri sarınca 2026-09-02 için İKİNCİ özet satırı doğar — kabul edilmiş bedel
    o3 = f(IP, YOL, now=_epoch(2026, 9, 3, 2))
    assert o3["gun"] == "2026-09-02" and o3["toplam_n"] == 1, o3


# ---- middleware yüzeyi: özet satırı GERÇEKTEN deftere düşüyor mu -------------------------------
def _tazeleyen_istemci(monkeypatch):
    """Yarı-ömrünü geçmiş çerezle `/api/summary` çağıran istemci (tazeleme tetiklenir)."""
    auth.set_password("cok-uzun-ve-guclu-parola-123")
    iat = int(time.time()) - 7 * 3600
    tok = auth._sign(iat + 12 * 3600, iat)
    monkeypatch.setattr(api, "DASH_TOKEN", None)
    return TestClient(api.app), {"cookie": f"{auth.COOKIE_NAME}={tok}"}


def test_MIDDLEWARE_ilk_tazeleme_ANINDA_satiri_basar(sandbox_state, monkeypatch):
    """Uçtan uca madde 2: emeklilen `atlanan_n`/`orneklem_s` alanları ARTIK YOK, ayırt edici
    `ozet` alanı VAR — ve satır hâlâ `session_refresh` adıyla basılıyor (grep sürekliliği)."""
    c, hdr = _tazeleyen_istemci(monkeypatch)
    assert c.get(YOL, headers=hdr).status_code == 200
    ref = [e for e in _olaylar(sandbox_state) if e.get("event") == "session_refresh"]
    assert len(ref) == 1, [e.get("event") for e in _olaylar(sandbox_state)]
    assert ref[0]["ozet"] is False, ref[0]
    assert ref[0]["ip"] == "testclient" and ref[0]["yol"] == YOL, ref[0]
    assert isinstance(ref[0]["kalan_s"], int), ref[0]
    assert "atlanan_n" not in ref[0] and "orneklem_s" not in ref[0], ref[0]


def test_MIDDLEWARE_RESTART_SONRASI_COK_YOL_TEK_SATIR(sandbox_state, monkeypatch):
    """TSK-006'nın CANLI ÖLÇÜMÜ (A1, 2026-09-03): restart/pano açılışında 57 ayrı yol için
    57 anında satır doğuyordu. Bu çivi aynı IP'den ÜÇ ayrı yolu tazeletir ve deftere TEK
    satır düşmesini bekler — kesimin asıl kazancı budur."""
    c, hdr = _tazeleyen_istemci(monkeypatch)
    for yol in (YOL, "/api/today", "/api/skills"):
        assert c.get(yol, headers=hdr).status_code == 200, yol
    ref = [e for e in _olaylar(sandbox_state) if e.get("event") == "session_refresh"]
    assert len(ref) == 1, [(e.get("yol"), e.get("ozet")) for e in ref]
    assert ref[0]["ozet"] is False and ref[0]["yol"] == YOL, ref[0]


def test_MIDDLEWARE_gun_donusunde_OZET_satirini_basar(sandbox_state, monkeypatch):
    """Uçtan uca madde 4 — DUVAR SAATİNE BAĞLANMADAN: IP'nin kaydı GEÇMİŞ bir güne kurulur,
    tek bir istek gün dönüşünü tetikler. (1970 seçildi: bugünün UTC günü ne olursa olsun
    ondan farklıdır, yani çivi takvimle birlikte kaymaz.)"""
    c, hdr = _tazeleyen_istemci(monkeypatch)
    api._REFRESH_SON["testclient"] = ["1970-01-01", 7,
                                      "1970-01-01T00:00:01+00:00",
                                      "1970-01-01T23:59:59+00:00",
                                      {YOL: 5, "/api/today": 2}, 0]
    assert c.get(YOL, headers=hdr).status_code == 200
    ref = [e for e in _olaylar(sandbox_state) if e.get("event") == "session_refresh"]
    assert len(ref) == 1, ref
    assert ref[0]["ozet"] is True and ref[0]["gun"] == "1970-01-01", ref[0]
    assert ref[0]["toplam_n"] == 7, ref[0]
    assert ref[0]["ilk_ts"] == "1970-01-01T00:00:01+00:00", ref[0]
    assert ref[0]["son_ts"] == "1970-01-01T23:59:59+00:00", ref[0]
    assert ref[0]["yollar"] == {YOL: 5, "/api/today": 2} and ref[0]["diger_n"] == 0, ref[0]
    assert ref[0]["ip"] == "testclient" and ref[0]["yol"] == YOL, ref[0]


def test_OZET_satiri_JETON_TASIMAZ(sandbox_state, monkeypatch):
    """v245'in jeton çivisi ÖZET satırında da geçerli olmalı — yeni bir satır sınıfı doğdu,
    sır sızıntısı çivisi onunla birlikte doğmazsa yüzey kör kalır."""
    c, hdr = _tazeleyen_istemci(monkeypatch)
    api._REFRESH_SON["testclient"] = ["1970-01-01", 3,
                                      "1970-01-01T00:00:01+00:00",
                                      "1970-01-01T00:00:02+00:00",
                                      {YOL: 3}, 0]
    r = c.get(YOL, headers=hdr)
    yeni = [v for v in r.headers.get_list("set-cookie") if v.startswith(auth.COOKIE_NAME)][0]
    yeni_tok = yeni.split(";")[0].split("=", 1)[1]
    ham = (sandbox_state / "events.jsonl").read_text()
    assert hdr["cookie"].split("=", 1)[1] not in ham, "ESKİ jeton özet turunda deftere düştü"
    assert yeni_tok not in ham, "YENİ jeton özet turunda deftere düştü"
    assert "cok-uzun-ve-guclu-parola-123" not in ham


@pytest.mark.parametrize("bozuk", [None, "", "/"])
def test_ip_ve_yol_STR_e_zorlanir(sandbox_state, bozuk):
    """Anahtar `str()`e zorlanır (mevcut sözleşme korunur): `scope.get("path", "")` bir gün
    None dönerse sözlük anahtarı tipi sessizce ayrışmasın."""
    karar = api._session_refresh_ornekle(bozuk, bozuk, now=_epoch(2026, 9, 2, 9))
    assert karar == {"ozet": False}
    assert str(bozuk) in api._REFRESH_SON
