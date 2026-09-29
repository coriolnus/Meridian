"""test_akis_anahtari_ttl_v589.py — TSK-249: pazar TTL dolumu KOPUŞ sayılmaz (2026-09-29).

VAKA (Rol-1, A1, 2026-09-28): her pazar ~20:49–21:00Z `mrd:*` bar akışlarının 2 günlük TTL'i doluyor
(cuma kapanışındaki son XADD'den ~48 sa sonra). O anda bloklu XREADGROUP'ta bekleyen istemci Redis
7.0'da `ResponseError: UNBLOCKED the stream key no longer exists` alıyor; worker'daki barfeed
ipliğinin okuyucusu (`hotstate.read_barfeed`) bunu `_note_down`a veriyor → `hotstate_down`
("Redis sıcak katmanı erişilemez") → pazartesi akşam döngüsünde `MAKULLÜK: hotstate_sustained_down`
alarmı. Redis AYAKTAYDI. Altı pazartesi üst üste yanlış alarm.

ÖLÇÜLEN İSTİSNA BİÇİMLERİ (izole redis-server 8.8.0 + redis-py 8.0.1, sonda çıktısı raporda):
  · Redis 7.0 (A1): `ResponseError("UNBLOCKED the stream key no longer exists")`, status_code None.
  · Redis ≥7.2 (ölçülen 8.8.0): AYNI olay (blok ortasında DEL ya da TTL dolumu) →
    `ResponseError("NOGROUP No such key '<anahtar>' or consumer group '<grup>' in XREADGROUP with GROUP option")`.
  · Gerçek kopuş: `ConnectionError` / `TimeoutError` — ikisi de ResponseError'ın ALTINDA DEĞİL.

ÇİVİLENEN İDDİALAR:
  1. SINIFLANDIRICI DAR: yalnız ResponseError tipi + bilinen iki metin; bilinmeyen ResponseError
     (başka UNBLOCKED nedenleri dahil) bugünkü gibi `hotstate_down`a gider (fail-loud).
  2. barfeed yolu: yaşam döngüsü → `hotstate_down` YOK, beyanlı bilgi olayı VAR (sayaçlı, süreç
     kimlikli, sel kısıtlı); istemci bırakılmaz, sağlık DÜŞMEZ.
  3. BEDEL (pozitif kontrol): ConnectionError / TimeoutError / bilinmeyen ResponseError hâlâ
     `hotstate_down` basar ve MAKULLÜK satırı hâlâ doğar.
  4. barsarchive yolu: UNBLOCKED → `bars_archive_read_failed` uyarısı değil bilgi olayı; etkilenen
     grup kayıtları DÜŞER, pazartesi ilk turda grup id=0 ile kurulur (NOGROUP onarım turu yok).
  5. MAKULLÜK dedektörü (DOKUNULMADI) yeni olayı SAYMAZ; telemetri hotstate bloğu SAYAR (Yasa 6).
"""
from __future__ import annotations

import json
import os
import time

import pytest
import redis.exceptions as rex

from meridian import analytics
from meridian import barsarchive as ba
from meridian import hotstate as hs
from meridian import watchdog as wd

# ÖLÇÜLEN metinler (sonda: scratchpad/tsk249-redis/probe*.out). Buraya elle yazıldılar çünkü
# çivinin görevi üretimdeki sınıflandırıcıyı GERÇEK dünyaya karşı sınamaktır — sınıflandırıcının
# kendi sabitinden türetmek, sabit yanlışsa çiviyi de onunla birlikte yanıltırdı.
UNBLOCKED = "UNBLOCKED the stream key no longer exists"
NOGROUP_BLOK = ("NOGROUP No such key 'mrd:barfeed' or consumer group 'meridian-intraday' "
                "in XREADGROUP with GROUP option")
YASAM_OLAYI = "akis_anahtari_suresi_doldu"


def _olaylar(state) -> list[dict]:
    p = state / "events.jsonl"
    if not p.exists():
        return []
    return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]


def _adlar(state) -> list[str]:
    return [str(e.get("event")) for e in _olaylar(state)]


@pytest.fixture(autouse=True)
def _saglik_yalitildi(monkeypatch):
    """`_HEALTH` ve iki basım saati modül-globaldir; komşu testten devralınan artık bu dosyanın
    sayaç hükümlerini yalanlardı. Bloklu istemci VARSAYILAN YOK — canlı/yerel Redis'e asla uzanılmaz."""
    onceki = dict(hs._HEALTH)
    hs._HEALTH.clear()
    hs._HEALTH.update(ok=None, reads=0, writes=0, fails=0, last_error="", at=None, down_since=None)
    monkeypatch.setattr(hs, "_LAST_DOWN_EMIT", 0.0)
    monkeypatch.setattr(hs, "_LAST_EXPIRY_EMIT", None, raising=False)
    monkeypatch.setattr(hs, "_blocking_redis", lambda: None)
    monkeypatch.setattr(hs, "_redis", lambda: None)
    yield
    hs._HEALTH.clear()
    hs._HEALTH.update(onceki)


class _BlokluSahte:
    """`read_barfeed`in kullandığı tek komut (xreadgroup): verilen istisnayı fırlatır."""

    def __init__(self, hata: BaseException):
        self.hata = hata
        self.cagri = 0

    def xreadgroup(self, *a, **k):
        self.cagri += 1
        raise self.hata


def _barfeed_oku(monkeypatch, hata):
    """`hotstate.read_barfeed`i verilen istisnayla sür. İki istemci GÖZCÜ nesneyle doldurulur:
    `_note_down` bağlantı hatasında ikisini de bırakır (None'a çeker) — gözcü yerinde duruyorsa
    istemci BIRAKILMAMIŞTIR."""
    sahte = _BlokluSahte(hata)
    gozcu = object()
    monkeypatch.setattr(hs, "_client", gozcu)
    monkeypatch.setattr(hs, "_blocking_client", gozcu)
    monkeypatch.setattr(hs, "_blocking_redis", lambda: sahte)
    sonuc = hs.read_barfeed("meridian-intraday", "c1", count=50, block_ms=2000)
    return sonuc, gozcu


# =================================================================================================
# 1) SINIFLANDIRICI — GERÇEK redis-py istisna nesneleriyle, DAR
# =================================================================================================
def test_redis70_unblocked_metni_yasam_dongusu_sayilir():
    assert hs.akis_yasam_dongusu_hatasi(rex.ResponseError(UNBLOCKED)) == "unblocked"


def test_redis72_ve_sonrasi_nogroup_metni_yasam_dongusu_sayilir():
    """Redis ≥7.2 aynı olayı (blok ortasında anahtar silindi) NOGROUP ile bildirir — ÖLÇÜLDÜ.
    Yalnız UNBLOCKED'u tanımak, A1'in Redis'i yükseldiği gün aynı yanlış alarmı geri getirirdi."""
    assert hs.akis_yasam_dongusu_hatasi(rex.ResponseError(NOGROUP_BLOK)) == "nogroup"


def test_ileride_kod_ayristirilirsa_status_code_bicimi_de_taninir():
    """redis-py bilinen hata kodlarını mesajdan AYIRIP `status_code`a koyar (EXCEPTION_CLASSES).
    UNBLOCKED bir gün o sözlüğe girerse mesaj yalnız gövdeyi taşır; sınıflandırıcı iki biçimi de
    aynı olay olarak okumalı, yoksa kütüphane güncellemesi alarmı sessizce geri getirir."""
    e = rex.ResponseError("the stream key no longer exists", status_code="UNBLOCKED")
    assert hs.akis_yasam_dongusu_hatasi(e) == "unblocked"


@pytest.mark.parametrize("metin", [
    "UNBLOCKED client unblocked via CLIENT UNBLOCK",
    "UNBLOCKED force unblock from blocking operation, instance state changed (master -> replica?)",
    "ERR syntax error",
    "WRONGTYPE Operation against a key holding the wrong kind of value",
    "the stream key no longer exists",
])
def test_bilinmeyen_response_error_siniflanmaz(metin):
    """DARLIK: aynı `UNBLOCKED` kodunu taşıyan BAŞKA nedenler (yönetici müdahalesi, rol değişimi)
    yaşam döngüsü DEĞİLDİR; kod önekiz gövde de tek başına yetmez."""
    assert hs.akis_yasam_dongusu_hatasi(rex.ResponseError(metin)) is None


@pytest.mark.parametrize("tip", [rex.ConnectionError, rex.TimeoutError, RuntimeError, OSError])
def test_baglanti_hatasi_ayni_metni_tasisa_bile_siniflanmaz(tip):
    """TİP KAPISI: ResponseError olmayan hiçbir istisna — metni ne olursa olsun — sınıflanmaz.
    Bağlantı arızası `hotstate_down` yolunda kalmalı."""
    assert hs.akis_yasam_dongusu_hatasi(tip(UNBLOCKED)) is None
    assert hs.akis_yasam_dongusu_hatasi(tip(NOGROUP_BLOK)) is None


# =================================================================================================
# 2) barfeed OKUYUCUSU — yaşam döngüsü kopuş DEĞİL
# =================================================================================================
@pytest.mark.parametrize("metin,sinif", [(UNBLOCKED, "unblocked"), (NOGROUP_BLOK, "nogroup")])
def test_barfeed_yasam_dongusu_down_basmaz_bilgi_olayi_basar(sandbox_state, monkeypatch, metin, sinif):
    sonuc, gozcu = _barfeed_oku(monkeypatch, rex.ResponseError(metin))

    assert sonuc is None, "tüketici döngüsü None'la grubu yeniden kurar — dönüş sözleşmesi aynı kalmalı"
    adlar = _adlar(sandbox_state)
    assert "hotstate_down" not in adlar, "TTL dolumu 'Redis erişilemez' diye basıldı"
    olay = [e for e in _olaylar(sandbox_state) if e.get("event") == YASAM_OLAYI]
    assert len(olay) == 1, f"beyanlı yaşam döngüsü olayı yok: {adlar}"
    o = olay[0]
    assert o["level"] == "info"
    assert o["sinif"] == sinif and o["kaynak"] == "barfeed" and o["anahtar"] == hs.BARFEED
    assert o["pid"] == os.getpid() and o["toplam"] == 1 and o["bastirilan"] == 0
    assert hs.health().get("ok") is not False, "sağlık DOWN'a düşürüldü — Redis cevap verdi"
    assert hs._client is gozcu and hs._blocking_client is gozcu, "istemci bırakıldı (kopuş yolu)"
    assert hs.health().get("stream_expired_total") == 1


def test_barfeed_yasam_dongusu_seli_kisitlanir_ve_bastirilan_sayilir(sandbox_state, monkeypatch):
    """SEL KORUMASI kaybolmamalı: eski yol (`_note_down`) DOWN_REASSERT_S kısıtlıydı. Patolojik
    tekrar (biri anahtarı durmadan siliyor) bilgi olayı seline dönmesin — pencere içindeki tekrar
    SAYILIR ve bir sonraki basımda `bastirilan` olarak görünür; toplam hiç kaybolmaz."""
    _barfeed_oku(monkeypatch, rex.ResponseError(UNBLOCKED))
    _barfeed_oku(monkeypatch, rex.ResponseError(UNBLOCKED))
    assert [a for a in _adlar(sandbox_state) if a == YASAM_OLAYI] == [YASAM_OLAYI], \
        "pencere içindeki ikinci tekrar da basıldı — sel kısıtı yok"

    monkeypatch.setattr(hs, "_LAST_EXPIRY_EMIT", time.monotonic() - hs.DOWN_REASSERT_S - 1)
    _barfeed_oku(monkeypatch, rex.ResponseError(UNBLOCKED))
    olay = [e for e in _olaylar(sandbox_state) if e.get("event") == YASAM_OLAYI]
    assert len(olay) == 2
    assert olay[-1]["bastirilan"] == 1 and olay[-1]["toplam"] == 3


# =================================================================================================
# 3) BEDEL YASASI — gerçek kopuş hâlâ `hotstate_down`
# =================================================================================================
@pytest.mark.parametrize("hata", [
    rex.ConnectionError("Error 111 connecting to 127.0.0.1:6379. Connection refused."),
    rex.TimeoutError("Timeout reading from socket"),
    rex.ResponseError("ERR unknown command 'XREADGROUP'"),
    rex.ResponseError("UNBLOCKED force unblock from blocking operation, instance state changed (master -> replica?)"),
])
def test_gercek_kopus_ve_bilinmeyen_hata_hala_down_basar(sandbox_state, monkeypatch, hata):
    """POZİTİF KONTROL. Sınıflandırma bir SUSTURUCUYA dönüşmemeli: bağlantı/zaman aşımı ve
    tanınmayan her yanıt hatası bugünkü gibi `hotstate_down` basar ve istemciyi bırakır."""
    sonuc, _gozcu = _barfeed_oku(monkeypatch, hata)

    assert sonuc is None
    adlar = _adlar(sandbox_state)
    assert "hotstate_down" in adlar, f"gerçek arıza SUSTU: {type(hata).__name__}"
    assert YASAM_OLAYI not in adlar
    assert hs.health()["ok"] is False
    assert hs._client is None and hs._blocking_client is None


# =================================================================================================
# 4) MAKULLÜK DEDEKTÖRÜ (DOKUNULMADI) — yeni olay girmez, gerçek kopuş girer
# =================================================================================================
def _makulluk_satiri(olaylar):
    for r in wd.parity_report(olaylar=olaylar)["rows"]:
        if r["check"] == "hotstate_sustained_down":
            return r
    return None


def test_makulluk_dedektoru_ttl_dolumunu_saymaz(sandbox_state, monkeypatch):
    """Uçtan uca: GERÇEK üretim yolundan (read_barfeed) düşen satırlar dedektöre verilir.
    Pazar TTL dolumu artık pazartesi alarmı DOĞURMAZ."""
    _barfeed_oku(monkeypatch, rex.ResponseError(UNBLOCKED))
    olaylar = _olaylar(sandbox_state)

    assert _makulluk_satiri(olaylar) is None, "TTL dolumu hâlâ MAKULLÜK hotstate_sustained_down doğuruyor"
    assert any(e.get("event") == YASAM_OLAYI for e in olaylar), \
        "dedektör sustu ama olay da yok — kör yeşil (olay hiç basılmamış olabilir)"


def test_makulluk_dedektoru_gercek_kopusu_hala_gorur(sandbox_state, monkeypatch):
    """Aynı uçtan uca yol, gerçek kopuşla: MAKULLÜK satırı DOĞAR (bedel ölçümü — alarm körleşmedi)."""
    _barfeed_oku(monkeypatch, rex.ConnectionError("Error 111 connecting. Connection refused."))
    r = _makulluk_satiri(_olaylar(sandbox_state))

    assert r is not None and r["ok"] is False, "gerçek Redis kopuşu artık alarm üretmiyor"


# =================================================================================================
# 5) YASA 6 — hafta sonu sayacı GÖRÜNÜR (telemetri hotstate bloğu)
# =================================================================================================
def test_telemetri_hotstate_blogu_ttl_dolumunu_sayar(sandbox_state, monkeypatch):
    """Olay `hotstate_down` adından çıkınca eski okuyucusunu (hotstate bloğu) kaybetmemeli:
    aynı blokta ADIYLA sayılır, `hotstate_down` sayımından AYRI."""
    _barfeed_oku(monkeypatch, rex.ResponseError(UNBLOCKED))
    monkeypatch.setattr(hs, "_LAST_EXPIRY_EMIT", None)
    _barfeed_oku(monkeypatch, rex.ResponseError(NOGROUP_BLOK))

    blok = analytics.coverage_breakage_counters(days=1)["hotstate"]

    assert blok[YASAM_OLAYI] == 2
    assert blok["hotstate_down"] == 0


def test_telemetri_sayaci_olay_yokken_sifir(sandbox_state):
    """Defter OKUNDU ve satır yok: ölçülmüş 0 (hotstate bloğunun `hotstate_down` sayımıyla aynı dil)."""
    assert analytics.coverage_breakage_counters(days=1)["hotstate"][YASAM_OLAYI] == 0


# =================================================================================================
# 6) barsarchive — UNBLOCKED bilgi olayı + grup kaydı düşer + pazartesi ilk turda kurulur
# =================================================================================================
class _ArsivSahte:
    """barsarchive'in dört komutu (scan_iter/xgroup_create/xreadgroup/xack) — v116 sahtesinin
    küçük hâli. `blok_kancasi` verilirse BİR SONRAKİ bloklu '>' okumasında çağrılır ve döndürdüğü
    istisna fırlatılır (blok ortasında TTL dolumunun taklidi)."""

    def __init__(self):
        self.streams: dict[str, list] = {}
        self.groups: dict[tuple, dict] = {}
        self.calls: list[tuple] = []
        self.blok_kancasi = None
        self._seq = 0

    def xadd(self, key, fields):
        self._seq += 1
        _id = f"{self._seq}-0"
        self.streams.setdefault(key, []).append((_id, dict(fields)))
        return _id

    def sil(self, key):
        """TTL dolumu: anahtar ve ona bağlı TÜM gruplar yok olur."""
        self.streams.pop(key, None)
        for g in [g for g in self.groups if g[0] == key]:
            del self.groups[g]

    def scan_iter(self, match=None, count=None):
        pre = match[:-1] if match and match.endswith("*") else match
        return [k for k in list(self.streams) if pre is None or k.startswith(pre)]

    def xgroup_create(self, name, groupname, id="0", mkstream=False):
        self.calls.append(("xgroup_create", name, str(id)))
        if (name, groupname) in self.groups:
            raise rex.ResponseError("BUSYGROUP Consumer Group name already exists")
        if name not in self.streams:
            if not mkstream:
                raise rex.ResponseError(f"NOGROUP No such key '{name}'")
            self.streams[name] = []
        pos = 0 if str(id) == "0" else len(self.streams[name])
        self.groups[(name, groupname)] = {"pos": pos, "pel": {}}
        return True

    def xreadgroup(self, groupname, consumername, streams, count=None, block=None):
        if block is not None and self.blok_kancasi is not None:
            kanca, self.blok_kancasi = self.blok_kancasi, None
            raise kanca()
        out = []
        for key, sid in streams.items():
            g = self.groups.get((key, groupname))
            if g is None:
                raise rex.ResponseError(f"NOGROUP No such key '{key}' or consumer group "
                                        f"'{groupname}' in XREADGROUP with GROUP option")
            if str(sid) == ">":
                entries = self.streams.get(key, [])[g["pos"]:]
                if not entries:
                    continue
                g["pos"] += len(entries)
                for _id, f in entries:
                    g["pel"][_id] = f
                out.append((key, [(i, dict(f)) for i, f in entries]))
            else:
                out.append((key, [(i, dict(f)) for i, f in g["pel"].items()]))
        return out

    def xack(self, key, group, *ids):
        g = self.groups.get((key, group))
        n = 0
        for i in ids:
            if g and i in g["pel"]:
                del g["pel"][i]
                n += 1
        return n


def _bar(t):
    return {"o": "10", "h": "10.5", "l": "9.9", "c": "10.2", "v": "1000", "vw": "10.1", "n": "42", "t": t}


@pytest.fixture
def arsiv(monkeypatch):
    r = _ArsivSahte()
    monkeypatch.setattr(hs, "_blocking_redis", lambda: r)
    uyarilar: list = []
    monkeypatch.setattr(ba.obs, "warn", lambda ev, **k: uyarilar.append((ev, k)))
    r.uyarilar = uyarilar
    return r


def _cuma_kapanisi(r, a):
    """İki akış, gruplar kurulmuş, cuma barları arşivlenmiş."""
    r.xadd("mrd:bars:AAPL", _bar("2026-09-25T19:59:00Z"))
    r.xadd("mrd:bars:MSFT", _bar("2026-09-25T19:59:00Z"))
    assert a.poll()["written"] == 2


def test_arsivci_unblocked_bilgi_olayi_basar_okuma_hatasi_basmaz(sandbox_state, arsiv):
    a = ba.BarsArchiver(poll_ms=100)
    _cuma_kapanisi(arsiv, a)

    def _pazar():
        arsiv.sil("mrd:bars:AAPL")
        return rex.ResponseError(UNBLOCKED)
    arsiv.blok_kancasi = _pazar

    res = a.poll()

    assert res is not None, "Redis cevap verdi — 'Redis yok' (None) dönmek YASA 4 üçüncü-hâl ihlali"
    assert res["read"] == 0 and res["written"] == 0
    assert [ev for ev, _ in arsiv.uyarilar] == [], f"TTL dolumu uyarı olarak basıldı: {arsiv.uyarilar}"
    olay = [e for e in _olaylar(sandbox_state) if e.get("event") == YASAM_OLAYI]
    assert len(olay) == 1 and olay[0]["level"] == "info"
    assert olay[0]["kaynak"] == "barsarchive" and olay[0]["sinif"] == "unblocked"
    assert olay[0]["streams"] == 2 and olay[0]["toplam"] == 1 and olay[0]["pid"] == os.getpid()
    assert "hotstate_down" not in _adlar(sandbox_state)
    assert "mrd:bars:AAPL" not in a._groups and "mrd:bars:AAPL" not in a._drained
    snap = a.snapshot()
    assert snap["stream_expiries"] == 1 and snap["group_resets"] == 0


def test_arsivci_pazartesi_ilk_turda_grubu_kurar_nogroup_turu_yok(sandbox_state, arsiv):
    """ONARIMIN AMACI: pazartesi ilk bar anahtarı grupsuz yeniden yaratır. Grup kaydı pazar
    düşürüldüğü için ilk tur grubu id=0 ile KURAR ve barı AYNI turda arşivler — NOGROUP hata
    turu (ve onun `bars_archive_group_reset` uyarısı) hiç yaşanmaz."""
    a = ba.BarsArchiver(poll_ms=100)
    _cuma_kapanisi(arsiv, a)

    def _pazar():
        arsiv.sil("mrd:bars:AAPL")
        return rex.ResponseError(UNBLOCKED)
    arsiv.blok_kancasi = _pazar
    a.poll()
    arsiv.calls.clear()

    arsiv.xadd("mrd:bars:AAPL", _bar("2026-09-28T13:30:00Z"))    # pazartesi: grupsuz yeniden doğdu
    res = a.poll()

    assert res is not None and res["written"] == 1, "pazartesi ilk barı ilk turda arşivlenmedi"
    assert ("xgroup_create", "mrd:bars:AAPL", "0") in arsiv.calls
    assert a.snapshot()["group_resets"] == 0, "NOGROUP onarım turu yaşandı — grup kaydı pazar düşmemiş"
    assert [ev for ev, _ in arsiv.uyarilar] == []


def test_arsivci_bilinmeyen_okuma_hatasi_bugunku_gibi_uyarir(sandbox_state, arsiv):
    """BEDEL: tanınmayan ResponseError sınıflanmaz — `bars_archive_read_failed` + None, grup
    kayıtları yerinde, yaşam döngüsü sayacı 0."""
    a = ba.BarsArchiver(poll_ms=100)
    _cuma_kapanisi(arsiv, a)
    arsiv.blok_kancasi = lambda: rex.ResponseError("ERR something else")

    res = a.poll()

    assert res is None
    assert [ev for ev, _ in arsiv.uyarilar] == ["bars_archive_read_failed"]
    assert YASAM_OLAYI not in _adlar(sandbox_state)
    assert {"mrd:bars:AAPL", "mrd:bars:MSFT"} <= a._groups
    assert a.snapshot()["stream_expiries"] == 0


def test_arsivci_nogroup_mevcut_onarim_yolunda_kalir(sandbox_state, arsiv):
    """Redis ≥7.2'de aynı pazar olayı NOGROUP gelir; arşivcide bunun ZATEN bir onarım yolu var
    (`group_resets` + uyarı). Bu tur o yola dokunmaz — yaşam döngüsü sayacına karışmamalı."""
    a = ba.BarsArchiver(poll_ms=100)
    _cuma_kapanisi(arsiv, a)

    def _pazar():
        arsiv.sil("mrd:bars:AAPL")
        return rex.ResponseError("NOGROUP No such key 'mrd:bars:AAPL' or consumer group 'archive' "
                                 "in XREADGROUP with GROUP option")
    arsiv.blok_kancasi = _pazar

    assert a.poll() is None
    assert [ev for ev, _ in arsiv.uyarilar] == ["bars_archive_group_reset"]
    assert a.snapshot()["group_resets"] == 1 and a.snapshot()["stream_expiries"] == 0
