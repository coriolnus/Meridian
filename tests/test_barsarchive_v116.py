"""test_barsarchive_v116.py — mrd:bars → disk dayanıklı arşivi (Faz 5 ham maddesi, 2026-07-29).

Gerçek Redis GEREKMEZ: stream semantiği (consumer-group teslim konumu + PEL + ACK) sahte bir
istemciyle sürülür — barfeed'in v85 deseni. Buradaki iddialar MEKANİZMA iddialarıdır:
  · şema ÜRETİCİDEN türetilir (kopyalanmaz) → hotstate şeması değişirse bu dosya çakar
  · consumer-group İZOLASYONU (barfeed'in anahtarına/ACK'ine dokunulmaz)
  · fsync → XACK SIRASI (yazım düşerse ACK yok, giriş PEL'de kalır, sonraki tur kurtarır)
  · İDEMPOTENS (yeniden teslim ve yeniden başlatma çift satır üretmez)
  · DÜRÜST ÜÇÜNCÜ HÂL (Redis yok = None ≠ akış boş = sıfırlı sözlük)
  · YAZAR TEKLİĞİ (state/bars_intraday/ adını depoda başka modül üretmez)
"""
import ast
import json
import pathlib

import pytest

from meridian import barsarchive as ba
from meridian import barfeed, hotstate

MERIDIAN = pathlib.Path(__file__).resolve().parent.parent / "meridian"
SRC = (MERIDIAN / "barsarchive.py").read_text()
TREE = ast.parse(SRC)


def _attrs_of(name: str) -> set[str]:
    """`name.<attr>` biçiminde GERÇEKTEN kullanılan öznitelikler (yorum/docstring DEĞİL, AST).

    Neden AST: izolasyon iddiası metin taramasıyla kanıtlanamaz — bu modülün docstring'i tam da
    barfeed'in yüzeyini ANLATIR, yani düz `grep` kendi açıklamasını ihlal sanırdı. Kanıt, kodun
    çağırdığı ADLARIN kendisidir."""
    return {n.attr for n in ast.walk(TREE)
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == name}


# ---------------------------------------------------------------------------------------------
# Sahte Redis: yalnız bu modülün kullandığı beş komut (scan_iter/xgroup_create/xreadgroup/xack/xadd).
# ---------------------------------------------------------------------------------------------
class FakeRedis:
    """Consumer-group semantiğinin İŞE YARAYAN en küçük hâli: grup başına teslim konumu + PEL."""

    def __init__(self):
        self.streams: dict[str, list] = {}          # key -> [(id, fields)]
        self.groups: dict[tuple, dict] = {}         # (key, group) -> {"pos": int, "pel": {id: fields}}
        self.acked: list[tuple] = []                # (key, group, id)
        self.calls: list[tuple] = []                # (komut, ...) — hangi anahtara dokunuldu KANITI
        self.ack_enabled = True                     # False → "ACK'ten önce çöktük" simülasyonu
        self._seq = 0

    # -- üretici tarafı (testin bar yerleştirmesi) --
    def xadd(self, key, fields, **kw):
        self._seq += 1
        _id = f"{self._seq}-0"
        self.streams.setdefault(key, []).append((_id, dict(fields)))
        return _id

    # -- tüketici tarafı (modülün kullandığı) --
    def scan_iter(self, match=None, count=None):
        self.calls.append(("scan", match))
        pre = match[:-1] if match and match.endswith("*") else match
        for k in list(self.streams):
            if pre is None or k.startswith(pre):
                yield k

    def xgroup_create(self, name, groupname, id="0", mkstream=False):
        self.calls.append(("xgroup_create", name, groupname, id))
        if (name, groupname) in self.groups:
            raise RuntimeError("BUSYGROUP Consumer Group name already exists")
        if name not in self.streams:
            if not mkstream:
                raise RuntimeError("NOGROUP no such key")
            self.streams[name] = []
        pos = 0 if str(id) == "0" else len(self.streams[name])
        self.groups[(name, groupname)] = {"pos": pos, "pel": {}}
        return True

    def xreadgroup(self, groupname, consumername, streams, count=None, block=None):
        self.calls.append(("xreadgroup", tuple(sorted(streams)), groupname, block))
        out = []
        for key, sid in streams.items():
            g = self.groups.get((key, groupname))
            if g is None:
                raise RuntimeError("NOGROUP")
            if str(sid) == ">":
                entries = self.streams.get(key, [])[g["pos"]:]
                if count:
                    entries = entries[:count]
                if not entries:
                    continue                      # ">" boş akışı HİÇ döndürmez (redis-py davranışı)
                g["pos"] += len(entries)
                for _id, f in entries:
                    g["pel"][_id] = f
                out.append((key, [(i, dict(f)) for i, f in entries]))
            else:
                pel = [(i, dict(f)) for i, f in g["pel"].items()]
                out.append((key, pel))            # "0" PEL'i döner (boş olsa bile akışı listeler)
        return out

    def xack(self, key, group, *ids):
        self.calls.append(("xack", key, group, ids))
        if not self.ack_enabled:
            return 0                              # ACK "kayboldu" — PEL DOLU kalır (çökme simülasyonu)
        g = self.groups.get((key, group))
        n = 0
        for i in ids:
            if g and i in g["pel"]:
                del g["pel"][i]
                n += 1
            self.acked.append((key, group, i))
        return n


def _bar(t, o=10.0, h=10.5, l=9.9, c=10.2, v=1000, vw=10.1, n=42):
    """hotstate._bar_wire'ın ürettiği TELE biçim: değerler Redis'te dizedir."""
    return {"o": str(o), "h": str(h), "l": str(l), "c": str(c), "v": str(v), "vw": str(vw),
            "n": str(n), "t": t}


@pytest.fixture(autouse=True)
def _no_real_redis(monkeypatch):
    """VARSAYILAN: Redis YOK. `conftest._hotstate_off_by_default` yalnız `hotstate._redis`i keser;
    bu modül `_blocking_redis` kullanır — yamalanmazsa testler CANLI Redis'e bağlanırdı."""
    monkeypatch.setattr(hotstate, "_blocking_redis", lambda: None)


# DOSYAYA-ÖZEL SIZINTI BEKÇİSİ GENELE KATILDI (2026-07-29): burada `_canli_arsive_sizinti_bekcisi`
# duruyordu — `state/bars_intraday/` canlı dizinin test sırasında OLUŞUP OLUŞMADIĞINA bakan bir
# autouse fikstürü. Kapattığı iki yapısal delik artık conftest'te kapalı: KATMAN 1'e `builtins.open`
# / `io.open` kancası eklendi (ham `open()`+`fsync` yazarları artık boğazdan geçiyor), KATMAN 2'nin
# parmak izi `os.scandir` yığınıyla ÖZYİNELEMELİ yapıldı (alt dizinler de taranıyor). Bekçi tek
# dosyaya değil TÜM suite'e uygulandığı için burada tutulması yalnız kopya olurdu. 16 MB kazasının
# hikâyesi aşağıda `test_yazim_basarisizsa_ack_atilmaz_ve_sonraki_tur_kurtarir` docstring'inde durur.


@pytest.fixture
def fake(monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(hotstate, "_blocking_redis", lambda: r)
    return r


@pytest.fixture
def quiet(monkeypatch):
    """obs.warn'ı sustur — uyarı bekleyen testler CANLI events.jsonl'a yazmasın (conftest dersi)."""
    seen = []
    monkeypatch.setattr(ba.obs, "warn", lambda ev, **k: seen.append((ev, k)))
    return seen


def _lines(state, day):
    p = state / "bars_intraday" / f"{day}.jsonl"
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


# ---------------------------------------------------------------------------------------------
# 1. ŞEMA — üreticiden TÜRETİLİR, kopyalanmaz
# ---------------------------------------------------------------------------------------------
def test_sema_hotstate_uretiminden_turetilir_kopyalanmaz():
    """Alan listesi hotstate._BAR_FIELDS'in TA KENDİSİDİR. Üretici şemayı değiştirirse burası çakar
    — arşiv sessizce eski şemayla yazmaya devam EDEMEZ (uydurma yasağının yapısal hâli)."""
    assert ba.BAR_FIELDS == tuple(hotstate._BAR_FIELDS)
    assert ba.BAR_FIELDS == ("o", "h", "l", "c", "v", "vw", "n", "t")
    # Liste bir SABİT OLARAK yeniden yazılmamış olmalı: kaynak hotstate'ten okumalı.
    assert "hotstate._BAR_FIELDS" in SRC, "şema kopyalanmış — üreticiden türetilmiyor"
    # Ayrıştırma da üreticinin kendi ayrıştırıcısı olmalı (float dönüşümü tek yerde tanımlı).
    assert "hotstate._bar_parse" in SRC


def test_yazilan_satir_yalniz_sema_alanlari_ve_ticker_icerir(sandbox_state, fake):
    """Satır = ticker + şema alanları. Uydurulmuş tek bir alan bile YOK; sayısallar float."""
    fake.xadd("mrd:bars:AAPL", _bar("2026-07-29T14:31:00Z"))
    arch = ba.BarsArchiver()
    res = arch.poll()
    arch.close()
    assert res["written"] == 1
    rows = _lines(sandbox_state, "2026-07-29")
    assert len(rows) == 1
    assert set(rows[0]) == {"ticker", *ba.BAR_FIELDS}
    assert rows[0]["ticker"] == "AAPL"
    assert rows[0]["t"] == "2026-07-29T14:31:00Z"          # damga DİZE kalır (look-ahead sözleşmesi)
    assert rows[0]["c"] == 10.2 and isinstance(rows[0]["c"], float)
    assert rows[0]["n"] == 42.0


def test_eksik_alan_uydurulmaz_atlanir(sandbox_state, fake):
    """`_bar_wire` None alanları düşürür → arşivde de YOKTUR. Boş/0 ile DOLDURULMAZ."""
    fake.xadd("mrd:bars:MSFT", {"c": "5.0", "t": "2026-07-29T14:32:00Z"})
    arch = ba.BarsArchiver()
    arch.poll()
    arch.close()
    row = _lines(sandbox_state, "2026-07-29")[0]
    assert set(row) == {"ticker", "c", "t"}
    assert "vw" not in row and "o" not in row


def test_t_siz_giris_yazilmaz_ama_ack_lenir_sonsuz_teslim_kilidi_yok(sandbox_state, fake):
    """`t` yoksa bar arşivde kimliksizdir: yazılmaz, SAYILIR, ama ACK'lenir — aksi hâlde PEL'de
    sonsuza dek birikip her turda yeniden işlenirdi."""
    fake.xadd("mrd:bars:NVDA", {"c": "1.0"})
    arch = ba.BarsArchiver()
    res = arch.poll()
    arch.close()
    assert res["written"] == 0 and arch.skipped_no_t == 1
    assert res["skipped_no_t"] == 1
    assert len(fake.acked) == 1
    assert not (sandbox_state / "bars_intraday").exists() or _lines(sandbox_state, "2026-07-29") == []


# ---------------------------------------------------------------------------------------------
# 2. CONSUMER-GROUP İZOLASYONU
# ---------------------------------------------------------------------------------------------
def test_grup_barfeed_grubundan_ayri_ve_farkli_anahtarda(sandbox_state, fake):
    """İzolasyonun BİRİNCİ kanıtı: farklı grup adı VE farklı anahtar ailesi."""
    assert ba.GROUP == "archive"
    assert ba.GROUP != barfeed.GROUP == "meridian-intraday"
    fake.xadd("mrd:bars:AAPL", _bar("2026-07-29T14:31:00Z"))
    arch = ba.BarsArchiver()
    arch.poll()
    arch.close()
    touched = {c[1] for c in fake.calls if c[0] in ("xgroup_create", "xack")}
    assert touched == {"mrd:bars:AAPL"}
    # mrd:barfeed'e HİÇBİR komut gitmedi — barfeed'in PEL'i/ACK'i etkilenemez.
    assert all(hotstate.BARFEED not in str(c) for c in fake.calls)
    assert all(ba.GROUP == g for _, keys, g, _ in
               [c for c in fake.calls if c[0] == "xreadgroup"])


def test_hotstate_yuzeyi_salt_okunur_ve_barfeed_api_si_hic_cagrilmaz():
    """İzolasyonun İKİNCİ kanıtı — YAPISAL, AST ile: modülün hotstate'ten kullandığı adların TAMAMI.
    barfeed'in akış/grup/ACK API'sinden HİÇBİRİ listede değildir; kullanılanların hepsi salt-okunur
    sabit ya da ayrıştırıcıdır (tek 'bağlantı' `_blocking_redis`, o da yalnız istemci döndürür)."""
    used = _attrs_of("hotstate")
    assert used == {"PREFIX", "_BAR_FIELDS", "_bar_parse", "_blocking_redis",
                    "BLOCKING_SOCKET_TIMEOUT"}, f"hotstate yüzeyi genişledi: {sorted(used)}"
    for yasak in ("BARFEED", "read_barfeed", "ack_barfeed", "ensure_barfeed_group",
                  "claim_and_drop_stale_barfeed", "barfeed_pending", "append_bar", "ingest_bars"):
        assert yasak not in used, f"barsarchive barfeed/yazma yüzeyine dokunuyor: {yasak}"


def test_redis_komut_yuzeyi_dort_komutla_sinirli_ve_hicbiri_yazmaz():
    """İzolasyonun ÜÇÜNCÜ kanıtı: istemci üzerinde çağrılan TÜM komutlar. XADD/DEL/EXPIRE/XTRIM yok
    → canlı akışın içeriğini değiştirmek yapısal olarak imkânsız. Yeni bir komut eklenirse çakar."""
    used = _attrs_of("r")
    assert used == {"scan_iter", "xgroup_create", "xreadgroup", "xack"}, \
        f"Redis komut yüzeyi değişti: {sorted(used)}"
    for yazma in ("xadd", "delete", "expire", "xtrim", "flushdb", "xgroup_destroy", "set", "hset"):
        assert yazma not in used, f"arşivci canlı akışa YAZIYOR: {yazma}"


def test_grup_baslangici_sifir_ring_de_duran_gecmisi_de_alir(sandbox_state, fake):
    """barfeed `$` (yalnız yeni) kullanır çünkü TETİKTİR; arşiv `0` kullanır çünkü ARŞİVDİR —
    ilk koşuda ring'de HÂLÂ duran ~2 seans da kurtarılır."""
    fake.xadd("mrd:bars:AAPL", _bar("2026-07-29T14:30:00Z"))   # arşivci HİÇ koşmadan ÖNCE gelmiş
    fake.xadd("mrd:bars:AAPL", _bar("2026-07-29T14:31:00Z"))
    arch = ba.BarsArchiver()
    res = arch.poll()
    arch.close()
    assert res["written"] == 2, "grup '$' ile kurulmuş — ring'deki geçmiş kanıt kaybedildi"
    assert [c for c in fake.calls if c[0] == "xgroup_create"][0][3] == "0"


def test_busygroup_hata_degil_yeniden_kurmaz(sandbox_state, fake, quiet):
    """Grup zaten varsa (BUSYGROUP) bu bir hata DEĞİLDİR ve uyarı üretmez."""
    fake.xadd("mrd:bars:AAPL", _bar("2026-07-29T14:31:00Z"))
    fake.xgroup_create("mrd:bars:AAPL", ba.GROUP, id="0")
    arch = ba.BarsArchiver()
    assert arch.poll()["written"] == 1
    arch.close()
    assert quiet == []


# ---------------------------------------------------------------------------------------------
# 3. İDEMPOTENS — yeniden teslim ve YENİDEN BAŞLATMA çift satır üretmez
# ---------------------------------------------------------------------------------------------
def test_ayni_bar_iki_kez_teslim_edilse_de_tek_satir(sandbox_state, fake):
    """Aynı (ticker,t) ikinci kez gelirse DÜŞÜRÜLÜR ve SAYILIR (duplicate) — sessizce değil."""
    fake.xadd("mrd:bars:AAPL", _bar("2026-07-29T14:31:00Z"))
    arch = ba.BarsArchiver()
    arch.poll()
    fake.xadd("mrd:bars:AAPL", _bar("2026-07-29T14:31:00Z", c=99.0))   # aynı dakika yeniden yayınlandı
    res2 = arch.poll()
    arch.close()
    assert res2["written"] == 0 and res2["duplicate"] == 1
    rows = _lines(sandbox_state, "2026-07-29")
    assert len(rows) == 1 and rows[0]["c"] == 10.2      # İLK yazım kalır, üzerine yazılmaz


def test_yeniden_baslatmada_pel_yeniden_teslimi_cift_satir_yazmaz(sandbox_state, fake):
    """KRİTİK İDEMPOTENS: fsync ile XACK ARASINDA çökme. Satır diskte, giriş PEL'de. Yeni süreç
    PEL'i tahliye edince aynı barları yeniden görür — küme DİSKTEN kurulduğu için hepsi düşer."""
    fake.xadd("mrd:bars:AAPL", _bar("2026-07-29T14:31:00Z"))
    fake.xadd("mrd:bars:AAPL", _bar("2026-07-29T14:32:00Z"))
    fake.ack_enabled = False                 # ACK "kayboldu" → PEL dolu kalır (çökme anı)
    a1 = ba.BarsArchiver()
    assert a1.poll()["written"] == 2
    a1.close()
    assert len(_lines(sandbox_state, "2026-07-29")) == 2
    assert len(fake.groups[("mrd:bars:AAPL", ba.GROUP)]["pel"]) == 2, "test kurgusu: PEL dolu olmalı"

    fake.ack_enabled = True
    a2 = ba.BarsArchiver()                   # YENİDEN BAŞLATMA: bellek sıfır, disk duruyor
    res = a2.poll()
    a2.close()
    assert res["duplicate"] == 2 and res["written"] == 0
    assert len(_lines(sandbox_state, "2026-07-29")) == 2, "yeniden başlatma ÇİFT SATIR yazdı"
    assert fake.groups[("mrd:bars:AAPL", ba.GROUP)]["pel"] == {}, "PEL nihayet temizlenmeli"


def test_bozuk_yarim_satir_indeks_kurulumunu_dusurmez(sandbox_state, fake):
    """Çökmeden kalan yarım satır dosyayı okunamaz yapmaz; sağlam satırlar tekilleştirmeye girer."""
    d = sandbox_state / "bars_intraday"
    d.mkdir(parents=True)
    (d / "2026-07-29.jsonl").write_text(
        json.dumps({"ticker": "AAPL", "t": "2026-07-29T14:31:00Z", "c": 1.0}) + "\n"
        + '{"ticker": "AAPL", "t": "2026-07-29T14:3')          # yarım yazım
    fake.xadd("mrd:bars:AAPL", _bar("2026-07-29T14:31:00Z"))
    fake.xadd("mrd:bars:AAPL", _bar("2026-07-29T14:33:00Z"))
    arch = ba.BarsArchiver()
    res = arch.poll()
    arch.close()
    assert res["duplicate"] == 1 and res["written"] == 1


# ---------------------------------------------------------------------------------------------
# 4. CRASH-SAFE SIRA — fsync → XACK (yazım düşerse ACK YOK)
# ---------------------------------------------------------------------------------------------
def test_yazim_basarisizsa_ack_atilmaz_ve_sonraki_tur_kurtarir(sandbox_state, fake, quiet,
                                                               monkeypatch):
    """Diske yazım patlarsa giriş PEL'de KALIR. Arıza geçince sonraki tur onu kurtarır — kayıp YOK.

    DİKKAT — `monkeypatch.undo()` KULLANILMAZ: undo PAYLAŞILAN fikstür örneğindeki TÜM yamaları
    söker (`_blocking_redis` → GERÇEK Redis, `config.STATE` → CANLI dizin) ve bu test tam olarak
    onu yaptığında canlı `state/bars_intraday/`a 16 MB yazıldı. Arıza bir BAYRAKLA kaldırılır."""
    fake.xadd("mrd:bars:AAPL", _bar("2026-07-29T14:31:00Z"))
    disk_bozuk = {"v": True}
    _asil = ba._DayIndex.write

    def belki_patla(self, rows):
        if disk_bozuk["v"]:
            raise OSError("No space left on device")
        return _asil(self, rows)

    monkeypatch.setattr(ba._DayIndex, "write", belki_patla)
    arch = ba.BarsArchiver()
    res = arch.poll()
    assert res["written"] == 0 and arch.write_failures == 1
    assert fake.acked == [], "yazım düşmüşken ACK atıldı — bar TEMELLİ kaybolurdu"
    assert len(fake.groups[("mrd:bars:AAPL", ba.GROUP)]["pel"]) == 1
    assert any(e == "bars_archive_write_failed" for e, _ in quiet)   # YASA 4: görünür başarısızlık

    disk_bozuk["v"] = False                  # disk düzeldi (yamalar YERİNDE kalır)
    arch2 = ba.BarsArchiver()                # PEL tahliyesi girişi yeniden getirir
    res2 = arch2.poll()
    arch2.close()
    assert res2["written"] == 1
    assert len(_lines(sandbox_state, "2026-07-29")) == 1


def test_kaynakta_fsync_ack_ten_once_gelir():
    """SIRA İDDİASI kaynakta da doğrulanır: `os.fsync` `write()` içindedir ve `xack` ONDAN SONRA
    ayrı bir adımdır. Ters sıra ACK'lenmiş-ama-diskte-olmayan bar üretirdi."""
    assert "os.fsync(fh.fileno())" in SRC
    assert SRC.index("os.fsync(fh.fileno())") < SRC.index("r.xack(")


# ---------------------------------------------------------------------------------------------
# 5. DÜRÜST ÜÇÜNCÜ HÂL (YASA 4)
# ---------------------------------------------------------------------------------------------
def test_redis_yoksa_none_doner_sifir_degil(sandbox_state):
    """"Redis'e ulaşamadım" ile "yazacak bar yoktu" AYNI DEĞERİ dönemez."""
    arch = ba.BarsArchiver()
    assert arch.poll() is None
    assert arch.polls == 0 and arch.written == 0


def test_akis_bos_ise_sifirli_sozluk_doner_none_degil(sandbox_state, fake):
    """Redis VAR ama hiç mrd:bars akışı yok (seans dışı / taze kurulum) → ölçüm döner, None değil."""
    arch = ba.BarsArchiver()
    res = arch.poll()
    arch.close()
    assert res is not None
    assert res == {"streams": 0, "read": 0, "written": 0, "duplicate": 0,
                   "skipped_no_t": 0, "acked": 0, "idle": True}


def test_akis_var_bar_yok_ise_idle_ama_streams_sayilir(sandbox_state, fake):
    """Akış var, yeni bar yok: idle=True ama streams>0 — ikisi farklı olgu, ikisi de görünür."""
    fake.xadd("mrd:bars:AAPL", _bar("2026-07-29T14:31:00Z"))
    arch = ba.BarsArchiver()
    arch.poll()
    res = arch.poll()
    arch.close()
    assert res["streams"] == 1 and res["read"] == 0 and res["idle"] is True


def test_scan_hatasi_yutulmaz(sandbox_state, fake, quiet, monkeypatch):
    """Keşif patlarsa poll None döner VE uyarı düşer — sessiz 'bar yoktu' YASAK."""
    def patla(*a, **k):
        raise ConnectionError("reset by peer")
    monkeypatch.setattr(fake, "scan_iter", patla)
    arch = ba.BarsArchiver()
    assert arch.poll() is None
    assert any(e == "bars_archive_scan_failed" for e, _ in quiet)
    assert arch.last_error.startswith("ConnectionError")


# ---------------------------------------------------------------------------------------------
# 6. GÜN ROTASYONU
# ---------------------------------------------------------------------------------------------
def test_gun_rotasyonu_t_nin_utc_gunune_gore(sandbox_state, fake):
    """Hedef dosya `t[:10]`. NY seansı (13:30-20:00 UTC) tek UTC gününe düşer — gün sınırı seansı
    ortadan bölmez. İki farklı gün → iki dosya, tek turda bile."""
    fake.xadd("mrd:bars:AAPL", _bar("2026-07-28T19:59:00Z"))
    fake.xadd("mrd:bars:AAPL", _bar("2026-07-29T14:31:00Z"))
    arch = ba.BarsArchiver()
    assert arch.poll()["written"] == 2
    arch.close()
    assert len(_lines(sandbox_state, "2026-07-28")) == 1
    assert len(_lines(sandbox_state, "2026-07-29")) == 1


def test_cok_sembol_tek_gun_dosyasinda_yan_yana(sandbox_state, fake):
    fake.xadd("mrd:bars:AAPL", _bar("2026-07-29T14:31:00Z"))
    fake.xadd("mrd:bars:MSFT", _bar("2026-07-29T14:31:00Z"))
    fake.xadd("mrd:bars:NVDA", _bar("2026-07-29T14:32:00Z"))
    arch = ba.BarsArchiver()
    assert arch.poll()["written"] == 3
    arch.close()
    assert {r["ticker"] for r in _lines(sandbox_state, "2026-07-29")} == {"AAPL", "MSFT", "NVDA"}


# ---------------------------------------------------------------------------------------------
# 7. UCUZ BEKLEME (seans dışı)
# ---------------------------------------------------------------------------------------------
def test_akis_varken_bekleme_sunucuda_yapilir_uyku_yok(sandbox_state, fake, monkeypatch):
    """Akış varken istemci UYUMAZ: bekleme XREADGROUP BLOCK ile sunucuda olur (tek bloklu soket
    okuması), meşgul döngü değil."""
    fake.xadd("mrd:bars:AAPL", _bar("2026-07-29T14:31:00Z"))
    uykular = []
    monkeypatch.setattr(ba.BarsArchiver, "_sleep", lambda self, s: uykular.append(s))
    arch = ba.BarsArchiver(poll_ms=1500)
    arch.run(max_polls=3)
    assert uykular == [], "akış varken istemci uyudu — BLOCK yerine meşgul bekleme"
    blocks = [c[3] for c in fake.calls if c[0] == "xreadgroup" and c[3] is not None]
    assert blocks and set(blocks) == {1500}


def test_hic_akis_yokken_ucuz_uyku(sandbox_state, fake, monkeypatch):
    """Hiç akış yoksa BLOCK yapılacak bir şey de yoktur → idle_s uykusu (SCAN seli değil)."""
    uykular = []
    monkeypatch.setattr(ba.BarsArchiver, "_sleep", lambda self, s: uykular.append(s))
    arch = ba.BarsArchiver(idle_s=7.0)
    arch.run(max_polls=3)
    assert uykular == [7.0, 7.0, 7.0]


def test_redis_yokken_de_uyur_yeniden_baglanma_seli_yok(sandbox_state, monkeypatch):
    uykular = []
    monkeypatch.setattr(ba.BarsArchiver, "_sleep", lambda self, s: uykular.append(s))
    arch = ba.BarsArchiver(idle_s=3.0)
    arch.run(max_polls=2)
    assert uykular == [3.0, 3.0]


def test_poll_ms_soket_timeout_altinda_kirpilir():
    """BLOCK > socket_timeout olursa bloklu okuma soket-timeout'la kesilir ve sahte 'Redis down'
    churn'ü doğar (barfeed'in canlı restart'ta öğrendiği ders). Tavan YAPISAL olarak uygulanır."""
    assert ba.MAX_POLL_MS < hotstate.BLOCKING_SOCKET_TIMEOUT * 1000
    assert ba.BarsArchiver(poll_ms=99000).poll_ms == ba.MAX_POLL_MS
    assert ba.BarsArchiver(poll_ms=1).poll_ms == 100


# ---------------------------------------------------------------------------------------------
# 8. YAZAR TEKLİĞİ
# ---------------------------------------------------------------------------------------------
def test_bars_intraday_dizinine_yalniz_bu_modul_yazar():
    """YAZAR TEKLİĞİ — iddia değil TARAMA: `bars_intraday` adını meridian/ altında başka hiçbir
    modül üretmez. (Komşu `bararchive.py` AYRI bir dizine — `intraday_bars` — yazar.)"""
    suclular = [p.name for p in MERIDIAN.rglob("*.py")
                if "bars_intraday" in p.read_text() and p.name != "barsarchive.py"]
    assert suclular == [], f"state/bars_intraday/ tek yazarlı değil: {suclular}"
    # Komşu arşivin dizini AYRI olmalı — ikisi birbirinin dosyasına yazamaz.
    from meridian import bararchive
    assert bararchive.ARCHIVE_DIR != ba.ARCHIVE_DIR


def test_modul_paralel_ajanin_yuzeyine_dokunmaz():
    """İTHAL YÜZEYİ KİLİTLİ — liste BÜYÜDÜ ve büyümesi gerekçelidir (2026-08-01).

    Üçtü, dörde çıktı: `barclock`. Gerekçe, testin kendi amacıyla AYNI YÖNDE — seans-içi boşluk
    dedektörü (5.3) "hangi dakika BEKLENİYOR" sorusunu cevaplamak zorunda ve o cevabın iki bileşeni
    (dakika damgası ayrıştırma + NY seans sınırı, DST-farkında) `barclock`ta TEK yerde yaşıyor.
    Alternatif, 9:30-16:00 kapısını buraya KOPYALAMAKtı; bu depoda "aynı yasa iki yerde, biri
    güncellenmemiş" baskın kusur sınıfıdır. Yani ithal eklemek, kopyayı önlemenin bedeli.
    Kilit KALDIRILMADI: liste hâlâ tam eşleşme — beşinci bir ithal yine bu testi çakar."""
    import ast
    mod = ast.parse(SRC)
    yerel = set()
    for node in ast.walk(mod):
        if isinstance(node, ast.ImportFrom) and node.level == 1:
            yerel |= {a.name for a in node.names}
    assert yerel == {"barclock", "config", "hotstate", "obs"}
    # SEANS YASASI KOPYALANMADI: saat sınırı burada literal olarak yeniden yazılmamalı.
    assert "is_market_open" in SRC and "9, 30" not in SRC and "9 * 60 + 30" not in SRC


# ---------------------------------------------------------------------------------------------
# 9. --ozet (YASA 6 tüketicisi)
# ---------------------------------------------------------------------------------------------
def test_ozet_arsiv_yokken_durust_konusur(sandbox_state):
    """"Arşiv hiç açılmamış" ile "arşiv boş" farkı çağırana AÇIK gösterilir."""
    s = ba.summary()
    assert s["exists"] is False and s["days"] == 0 and s["rows"] == 0
    assert "YOK" in ba.render_summary()


def test_ozet_gun_satir_sembol_sayar(sandbox_state, fake):
    fake.xadd("mrd:bars:AAPL", _bar("2026-07-28T19:30:00Z"))
    fake.xadd("mrd:bars:AAPL", _bar("2026-07-29T14:31:00Z"))
    fake.xadd("mrd:bars:MSFT", _bar("2026-07-29T14:31:00Z"))
    arch = ba.BarsArchiver()
    arch.poll()
    arch.close()
    s = ba.summary()
    assert s["exists"] is True
    assert s["days"] == 2 and s["rows"] == 3 and s["symbols"] == 2
    assert s["first_day"] == "2026-07-28" and s["last_day"] == "2026-07-29"
    assert s["bad_lines"] == 0 and s["bytes"] > 0
    txt = ba.render_summary()
    assert "gun      : 2" in txt and "satir    : 3" in txt and "sembol   : 2" in txt


def test_ozet_bozuk_satiri_sayar_ve_soyler(sandbox_state):
    d = sandbox_state / "bars_intraday"
    d.mkdir(parents=True)
    (d / "2026-07-29.jsonl").write_text(
        json.dumps({"ticker": "AAPL", "t": "2026-07-29T14:31:00Z"}) + "\n{yarim")
    s = ba.summary()
    assert s["rows"] == 1 and s["bad_lines"] == 1
    assert "BOZUK SATIR: 1" in ba.render_summary()


def test_cli_ozet_calisir(sandbox_state, capsys):
    assert ba.main(["--ozet"]) == 0
    assert "bars_intraday" in capsys.readouterr().out


def test_cli_once_redis_yokken_durust_hata_kodu(sandbox_state, capsys):
    """Sessiz başarı YOK: Redis yoksa çıkış kodu 2 ve gerekçe metni."""
    assert ba.main(["--once"]) == 2
    assert "REDIS YOK" in capsys.readouterr().out


def test_cli_once_yazar_ve_olcum_basar(sandbox_state, fake, capsys):
    fake.xadd("mrd:bars:AAPL", _bar("2026-07-29T14:31:00Z"))
    assert ba.main(["--once"]) == 0
    res = json.loads(capsys.readouterr().out.strip())
    assert res["written"] == 1 and res["streams"] == 1
    assert len(_lines(sandbox_state, "2026-07-29")) == 1


def test_poll_sozlugu_TUR_DELTASI_dir_kumulatif_degil(sandbox_state, fake):
    """`poll()` sözlüğünün HER alanı "bu turda" demektir; kümülatif toplamlar `snapshot()`tadır.
    İkisi karışırsa `--once` çıktısı bütün koşunun toplamını tek turmuş gibi gösterirdi."""
    fake.xadd("mrd:bars:AAPL", {"c": "1.0"})                      # t'siz → skipped
    arch = ba.BarsArchiver()
    assert arch.poll()["skipped_no_t"] == 1
    fake.xadd("mrd:bars:AAPL", _bar("2026-07-29T14:31:00Z"))
    res2 = arch.poll()
    arch.close()
    assert res2["skipped_no_t"] == 0, "kümülatif sızdı — ikinci turda yeni atlama yoktu"
    assert res2["written"] == 1
    assert arch.snapshot()["skipped_no_t"] == 1                   # kümülatif BURADA yaşar
