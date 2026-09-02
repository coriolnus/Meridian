"""v374 — TSK-106: `session_refresh` defteri (ip, yol) başına GÜNLÜK ÖZETe iner.

KİMLİK NOTU (vNNN çakışma kuralı, 2026-09-02): brief bu dosyaya `v371` öneriyordu.
`tests/test_rejim_tam_pencere_v371.py` o numarayı ZATEN taşıyor (v370/v372/v373 de dolu).
Numara KİMLİKTİR ve çakışmada AZ-ÇAPALI taraf taşınır — bu dosya henüz hiçbir yerden
çapalanmamıştı, dolayısıyla taşınan odur: bir sonraki boş numara v374.

SINANAN SÖZLEŞME (`meridian/api.py::_session_refresh_ornekle`, TSK-106 2026-09-02):
  * anahtar (ip, yol) KALIR; pencere UTC TAKVİM GÜNÜdür — monotonic pencere DEĞİL,
  * çiftin İLK olayı (süreç belleğinde kaydı yokken) ANINDA yazılır (`ozet=False`) —
    "tazeleme hiç çalışıyor mu" görünürlüğü asla kaybolmaz,
  * aynı UTC günündeki SONRAKİ olaylar YAZILMAZ; bellekte sayaç + ilk/son damga birikir,
  * gün dönüşünde ÖNCEKİ günün özeti TEK satır yazılır: `ozet=True` + `gun` + `toplam_n`
    + `ilk_ts` + `son_ts`. Olay ADI `session_refresh` KALIR (grep sürekliliği),
  * yeni günün ilk olayı ANINDA YAZILMAZ (çiftin kaydı artık VAR) — sayaçtan başlar,
  * TOPLAM KORUNUMU: bir günün gerçek olay sayısı =
        (o gün anında yazılan ilk satır varsa 1, yoksa 0) + o günün özetindeki `toplam_n`,
  * bellek tavanı (`_REFRESH_TAVAN`) KALIR: EN ESKİ GÖRÜLEN kayıt düşer ve düşen kaydın
    biriken sayacı KAYBOLUR (beyanlı bedel),
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
def test_CIFTIN_ILK_olayi_ANINDA_yazilir(sandbox_state):
    """Madde 2: kaydı olmayan (ip, yol) çiftinin ilk olayı beklemez — görünürlük kapısı."""
    karar = api._session_refresh_ornekle(IP, YOL, now=_epoch(2026, 9, 2, 9))
    assert karar == {"ozet": False}, karar


def test_AYNI_UTC_GUNUNDEKI_sonraki_olaylar_YAZILMAZ(sandbox_state):
    """Madde 3: gün içi kadans deftere DÜŞMEZ; bellekte sayaç + damga birikir."""
    f = api._session_refresh_ornekle
    assert f(IP, YOL, now=_epoch(2026, 9, 2, 0, 0, 1)) == {"ozet": False}
    for saat in (1, 9, 15, 23):
        assert f(IP, YOL, now=_epoch(2026, 9, 2, saat)) is None, saat


def test_anahtar_IP_YOL_CIFTIDIR_ayri_yol_ayri_kayit(sandbox_state):
    """Madde 1: anahtar KALIR — ayrı yol ayrı kayıttır ve kendi ilk olayını anında yazar."""
    f = api._session_refresh_ornekle
    assert f(IP, YOL, now=_epoch(2026, 9, 2, 9)) == {"ozet": False}
    assert f(IP, "/api/today", now=_epoch(2026, 9, 2, 9, 0, 1)) == {"ozet": False}
    assert f("10.0.0.9", YOL, now=_epoch(2026, 9, 2, 9, 0, 2)) == {"ozet": False}
    # üçü de AYRI kayıt: birinin bastırılması diğerini etkilemez
    assert f(IP, YOL, now=_epoch(2026, 9, 2, 10)) is None


def test_GUN_DONUSUNDE_onceki_gunun_OZETI_TEK_satir(sandbox_state):
    """Madde 4: özet `gun` + `toplam_n` + `ilk_ts` + `son_ts` taşır ve `ozet=True` ile ayrılır.

    `ilk_ts` o günün GERÇEK ilk olayıdır (anında yazılan satırın anı dahil) — bir damga,
    bir sayaç değil; `toplam_n` ise anında yazılan satırı SAYMAZ (toplam korunumu formülü)."""
    f = api._session_refresh_ornekle
    assert f(IP, YOL, now=_epoch(2026, 9, 2, 9)) == {"ozet": False}
    assert f(IP, YOL, now=_epoch(2026, 9, 2, 12)) is None
    assert f(IP, YOL, now=_epoch(2026, 9, 2, 23, 59, 59)) is None
    ozet = f(IP, YOL, now=_epoch(2026, 9, 3, 0, 0, 1))
    assert ozet == {"ozet": True, "gun": "2026-09-02", "toplam_n": 2,
                    "ilk_ts": "2026-09-02T09:00:00+00:00",
                    "son_ts": "2026-09-02T23:59:59+00:00"}, ozet


def test_YENI_GUNUN_ilk_olayi_ANINDA_YAZILMAZ_sayactan_baslar(sandbox_state):
    """Madde 4 kuyruğu: özet yazıldıktan sonra yeni gün madde-2 anındalığına DÖNMEZ.

    Kararlı durum çift başına günde ~1 satırdır; yeni günün ilk olayı da anında yazılsaydı
    günde 2 satır olur ve kesimin yarısı geri gelirdi."""
    f = api._session_refresh_ornekle
    f(IP, YOL, now=_epoch(2026, 9, 2, 9))
    f(IP, YOL, now=_epoch(2026, 9, 2, 10))
    assert f(IP, YOL, now=_epoch(2026, 9, 3, 8))["ozet"] is True   # gün dönüşü özeti
    assert f(IP, YOL, now=_epoch(2026, 9, 3, 9)) is None           # yeni gün: SESSİZ
    assert f(IP, YOL, now=_epoch(2026, 9, 3, 10)) is None
    ozet2 = f(IP, YOL, now=_epoch(2026, 9, 4, 1))
    assert ozet2["gun"] == "2026-09-03" and ozet2["toplam_n"] == 3, ozet2
    assert ozet2["ilk_ts"] == "2026-09-03T08:00:00+00:00", ozet2
    assert ozet2["son_ts"] == "2026-09-03T10:00:00+00:00", ozet2


def test_TOPLAM_KORUNUMU_formulu(sandbox_state):
    """Madde 7: gerçek olay sayısı = (anında yazılan ilk satır: 1) + özetteki `toplam_n`.

    İki dünya AYRI ölçülür: çiftin İLK günü (anında satır VAR → pay 1) ve sonraki bir gün
    (anında satır YOK → pay 0). Formül tek dünyada sınanırsa diğerinde sessizce kayar."""
    f = api._session_refresh_ornekle
    # --- 1. gün: 6 gerçek olay, biri anında yazıldı
    anlar = [_epoch(2026, 9, 2, 8, dk) for dk in range(6)]
    yazilan_1 = sum(1 for t in anlar if f(IP, YOL, now=t) is not None)
    assert yazilan_1 == 1, "ilk gün tam bir satır yazmalıydı (anında görünürlük)"
    ozet1 = f(IP, YOL, now=_epoch(2026, 9, 3, 8))
    assert 1 + ozet1["toplam_n"] == len(anlar), ozet1

    # --- 2. gün: 4 gerçek olay (ilki gün dönüşünü tetikleyen), anında satır YOK
    for dk in range(1, 4):
        assert f(IP, YOL, now=_epoch(2026, 9, 3, 8, dk)) is None
    ozet2 = f(IP, YOL, now=_epoch(2026, 9, 4, 8))
    assert 0 + ozet2["toplam_n"] == 4, ozet2


def test_TAVAN_asilinca_EN_ESKI_GORULEN_kayit_duser(sandbox_state, monkeypatch):
    """Madde 5: `_REFRESH_TAVAN` KALIR; düşen kaydın biriken sayacı KAYBOLUR (beyanlı bedel).

    "En eski" YARATILIŞ sırası değil SON GÖRÜLME damgasıdır: canlı yoklayıcı yıllarca aynı
    çifti kullanır, yaratılışa göre düşürmek en CANLI kaydı kurban ederdi."""
    monkeypatch.setattr(api, "_REFRESH_TAVAN", 3)
    f = api._session_refresh_ornekle
    for i, yol in enumerate(("/a", "/b", "/c")):
        assert f(IP, yol, now=_epoch(2026, 9, 2, 9, i)) == {"ozet": False}
    # /a EN SON görülene çekilir → artık en eski O DEĞİL /b'dir
    assert f(IP, "/a", now=_epoch(2026, 9, 2, 9, 3)) is None
    assert f(IP, "/d", now=_epoch(2026, 9, 2, 9, 4)) == {"ozet": False}
    kalanlar = {yol for _ip, yol in api._REFRESH_SON}
    assert kalanlar == {"/a", "/c", "/d"}, kalanlar
    assert len(api._REFRESH_SON) == 3
    # BEYANLI BEDEL: düşen kaydın sayacı gitti — /b yeniden "ilk olay" gibi davranır
    assert f(IP, "/b", now=_epoch(2026, 9, 2, 9, 5)) == {"ozet": False}


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
                  "son_ts": "2026-09-03T01:00:00+00:00"}, o2
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


def test_MIDDLEWARE_gun_donusunde_OZET_satirini_basar(sandbox_state, monkeypatch):
    """Uçtan uca madde 4 — DUVAR SAATİNE BAĞLANMADAN: çiftin kaydı GEÇMİŞ bir güne kurulur,
    tek bir istek gün dönüşünü tetikler. (1970 seçildi: bugünün UTC günü ne olursa olsun
    ondan farklıdır, yani çivi takvimle birlikte kaymaz.)"""
    c, hdr = _tazeleyen_istemci(monkeypatch)
    api._REFRESH_SON[("testclient", YOL)] = ["1970-01-01", 7,
                                             "1970-01-01T00:00:01+00:00",
                                             "1970-01-01T23:59:59+00:00"]
    assert c.get(YOL, headers=hdr).status_code == 200
    ref = [e for e in _olaylar(sandbox_state) if e.get("event") == "session_refresh"]
    assert len(ref) == 1, ref
    assert ref[0]["ozet"] is True and ref[0]["gun"] == "1970-01-01", ref[0]
    assert ref[0]["toplam_n"] == 7, ref[0]
    assert ref[0]["ilk_ts"] == "1970-01-01T00:00:01+00:00", ref[0]
    assert ref[0]["son_ts"] == "1970-01-01T23:59:59+00:00", ref[0]
    assert ref[0]["ip"] == "testclient" and ref[0]["yol"] == YOL, ref[0]


def test_OZET_satiri_JETON_TASIMAZ(sandbox_state, monkeypatch):
    """v245'in jeton çivisi ÖZET satırında da geçerli olmalı — yeni bir satır sınıfı doğdu,
    sır sızıntısı çivisi onunla birlikte doğmazsa yüzey kör kalır."""
    c, hdr = _tazeleyen_istemci(monkeypatch)
    api._REFRESH_SON[("testclient", YOL)] = ["1970-01-01", 3,
                                             "1970-01-01T00:00:01+00:00",
                                             "1970-01-01T00:00:02+00:00"]
    r = c.get(YOL, headers=hdr)
    yeni = [v for v in r.headers.get_list("set-cookie") if v.startswith(auth.COOKIE_NAME)][0]
    yeni_tok = yeni.split(";")[0].split("=", 1)[1]
    ham = (sandbox_state / "events.jsonl").read_text()
    assert hdr["cookie"].split("=", 1)[1] not in ham, "ESKİ jeton özet turunda deftere düştü"
    assert yeni_tok not in ham, "YENİ jeton özet turunda deftere düştü"
    assert "cok-uzun-ve-guclu-parola-123" not in ham


@pytest.mark.parametrize("bozuk", [None, "", "/"])
def test_yol_ve_ip_STR_e_zorlanir(sandbox_state, bozuk):
    """Anahtar `str()`e zorlanır (mevcut sözleşme korunur): `scope.get("path", "")` bir gün
    None dönerse sözlük anahtarı tipi sessizce ayrışmasın."""
    karar = api._session_refresh_ornekle(bozuk, bozuk, now=_epoch(2026, 9, 2, 9))
    assert karar == {"ozet": False}
    assert (str(bozuk), str(bozuk)) in api._REFRESH_SON
