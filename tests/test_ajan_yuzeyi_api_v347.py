"""test_ajan_yuzeyi_api_v347.py — `/api/ajanlar` ucunun ÜÇ DURUM ve ÜÇ MUTASYON çivisi.

NE ÖLÇÜLÜYOR. Operatör bugün üç botun (`sef`·`bekci`·`karne`) ve ana hermes beyninin ne
konuştuğunu ancak A1'e ssh'layıp `state.db`leri elle açarak görebiliyor. Bu uç o kaynakları
SALT-OKUNUR biçimde tek yüzeye taşır. Uç veri ÜRETMEZ; ölçemediğini `olculemedi` + `neden` ile
söyler.

ÜÇ DURUM (planın şartı):
  · DOLU KAYNAK — oturum/mesaj/model ve teslim damgaları diskten gelir,
  · DOSYA YOK — `durum: olculemedi`, `oturumlar: null`, `neden` yolu ADIYLA söyler,
  · ŞEMA UYUMSUZ — aynı hüküm; eksik tablo/sütun adı `neden`de geçer.

ÜÇ MUTASYON (yeşilden sonra ısırdığı GÖSTERİLDİ, 2026-08-31):
  (a) `mode=ro` kaldırılırsa → `test_baglanti_SALT_OKUNUR_aciliyor` ısırır. Çivi DİZE değil
      DAVRANIŞ ölçer: ucun açtığı GERÇEK bağlantıya yazma denenir. Dize eşleştirmesi tek başına
      kandırılabilirdi (`mode=ro` yorumda da geçebilir); yazma denemesi kandırılamaz.
  (b) şema-uyumsuzda `olculemedi` → boş listeye çevrilirse → `test_sema_uyumsuz_db_...` ısırır.
      "Boş liste" AYRI BİR İDDİADIR: "bu ajanla hiç konuşulmamış" der. Ölçülen şey ise
      "defteri okuyamadım"dır. İkisini aynı şekle sıkıştırmak sessiz körlüktür.
  (c) mesaj kırpma tavanı kaldırılırsa → `test_mesaj_metni_KIRPILIYOR_...` ısırır.

GERÇEK `~/.hermes`E DOKUNULMAZ: her yol çözücüsü (`_ajan_profil_koku`, `_ajan_ana_beyin_db`,
`_ajan_bot_koku`) monkeypatch'lenir ve `test_varsayilan_yollar_GERCEK_HERMESI_gosteriyor`
varsayılanların doğru yeri gösterdiğini AYRI ölçer — yani sentetik ölçüm, canlı yolu doğrulama
görevinden kaçmaz.
"""
from __future__ import annotations

import datetime as _dt
import inspect
import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from meridian import api, auth


UC = "/api/ajanlar"
_GERCEK_CONNECT = sqlite3.connect


# ===================== yardımcılar =====================

def _acik_kapi(monkeypatch) -> TestClient:
    """Yetki kapısı AÇIK istemci (v312 deseni: parola kurulu değil, token yok → `_auth` geçer)."""
    monkeypatch.setattr(auth, "password_set", lambda: False)
    monkeypatch.setattr(api, "DASH_TOKEN", None)
    return TestClient(api.app)


def _kapali_kapi(monkeypatch, token: str = "T0KEN-347"):
    monkeypatch.setattr(auth, "password_set", lambda: False)
    monkeypatch.setattr(api, "DASH_TOKEN", token)
    return TestClient(api.app), token


#: Sentetik `state.db` şeması — CANLI ŞEMANIN ÖLÇÜLMÜŞ ALT KÜMESİ (2026-08-31, `~/.hermes/state.db`
#: `sqlite_master` okundu). Ucun OKUDUĞU sütunlar burada; okumadıklarını taşımak testi canlı
#: şemanın bakım borcuna bağlardı. Alt küme olması bilinçli: uç eksik sütunla düşerse çivi öter.
_SEMA = """
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    model TEXT,
    started_at REAL NOT NULL
);
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT,
    timestamp REAL NOT NULL
);
"""

#: Sabit taban damga — testler DUVAR SAATİNE bağlanmaz. Literal epoch yerine tarihten TÜRETİLİR:
#: elle yazılmış bir epoch sayısının hangi yılı gösterdiği okunamaz ve yanlış yazıldığında testin
#: kendisi sessizce başka bir şey ölçer.
_T0 = _dt.datetime(2026, 8, 30, 9, 0, tzinfo=_dt.timezone.utc).timestamp()


def _db_kur(p: Path, oturumlar) -> None:
    """`oturumlar` = [(oturum_id, model, ts, [(rol, ts, metin), …]), …]."""
    p.parent.mkdir(parents=True, exist_ok=True)
    c = _GERCEK_CONNECT(str(p))
    try:
        c.executescript(_SEMA)
        for oid, model, ts, mesajlar in oturumlar:
            c.execute("INSERT INTO sessions (id, model, started_at) VALUES (?,?,?)",
                      (oid, model, ts))
            for rol, mts, metin in mesajlar:
                c.execute("INSERT INTO messages (session_id, role, content, timestamp) "
                          "VALUES (?,?,?,?)", (oid, rol, metin, mts))
        c.commit()
    finally:
        c.close()


def _oturum(oid: str, model: str, ts: float, n_mesaj: int = 3):
    return (oid, model, ts,
            [("user" if i % 2 == 0 else "assistant", ts + i, f"{oid}-mesaj-{i}")
             for i in range(n_mesaj)])


@pytest.fixture
def filo(tmp_path, monkeypatch, sandbox_state):
    """Sentetik FİLO: bot kökü (roster) + profil kökü (state.db'ler) + ana beyin + events defteri.

    `sandbox_state` ZORUNLU BAĞIMLILIK, kolaylık değil: uç teslim olaylarını `config.STATE`ten
    okur ve sandbox olmadan CANLI `state/events.jsonl` taranırdı — ölçüm makineye bağlanır,
    yeşili hiçbir şey kanıtlamazdı."""
    bot_koku = tmp_path / "deploy-profiles"
    profil_koku = tmp_path / "hermes-profiles"
    ana_db = tmp_path / "ana" / "state.db"
    for ad in ("sef", "bekci", "karne"):
        (bot_koku / ad).mkdir(parents=True)
    monkeypatch.setattr(api, "_ajan_bot_koku", lambda: bot_koku)
    monkeypatch.setattr(api, "_ajan_profil_koku", lambda: profil_koku)
    monkeypatch.setattr(api, "_ajan_ana_beyin_db", lambda: ana_db)
    return {"bot_koku": bot_koku, "profil_koku": profil_koku, "ana_db": ana_db,
            "state": sandbox_state}


def _db_yolu(filo, ad: str) -> Path:
    return filo["profil_koku"] / ad / "state.db"


def _olay_yaz(state: Path, olaylar) -> None:
    p = state / "events.jsonl"
    with open(p, "a", encoding="utf-8") as f:
        for o in olaylar:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")


def _ajan(g: dict, ad: str) -> dict:
    return next(a for a in g["ajanlar"] if a["ad"] == ad)


# ===================== yetki =====================

def test_uc_yetki_istiyor(monkeypatch, filo):
    """Ajan oturumları sistemin iç konuşmasıdır — `/runbook` ve karar arşiviyle AYNI sınıf, yani
    AYNI kapı. Yeni bir yetki mekanizması YOK: mevcut `_auth`."""
    c, token = _kapali_kapi(monkeypatch)
    assert c.get(UC).status_code == 401
    assert c.get(UC, headers={"x-meridian-token": token}).status_code == 200


# ===================== DURUM 1 · dolu kaynak =====================

def test_dolu_kaynak_oturum_mesaj_ve_model_donduruyor(monkeypatch, filo):
    """Üç alan da DİSKTEN gelir: oturum kimliği, model rozeti, mesaj gövdesi.

    Sıra ÇİVİLİ: oturumlar EN YENİ ÖNCE (operatör en son ne konuşulduğunu arar), oturum İÇİNDE
    mesajlar KRONOLOJİK (bir konuşma tersten okunmaz)."""
    _db_kur(_db_yolu(filo, "sef"), [
        _oturum("sef-eski", "gpt-5", _T0),
        _oturum("sef-yeni", "claude-opus-4-1-ultra", _T0 + 3600),
    ])
    c = _acik_kapi(monkeypatch)
    y = c.get(UC)
    assert y.status_code == 200, y.text
    g = y.json()
    a = _ajan(g, "sef")
    assert a["durum"] == "ok", a
    assert a["neden"] is None, a
    assert a["tur"] == "bot", a
    assert [o["id"] for o in a["oturumlar"]] == ["sef-yeni", "sef-eski"], a["oturumlar"]
    assert a["model"] == "claude-opus-4-1-ultra", "ajan modeli EN YENİ oturumdan gelmiyor"
    assert a["son_oturum_ts"] == a["oturumlar"][0]["ts"], a
    mesajlar = a["oturumlar"][0]["mesajlar"]
    assert [m["metin"] for m in mesajlar] == ["sef-yeni-mesaj-0", "sef-yeni-mesaj-1",
                                             "sef-yeni-mesaj-2"], mesajlar
    assert [m["rol"] for m in mesajlar] == ["user", "assistant", "user"], mesajlar


def test_damgalar_ISO_metne_ceviriliyor(monkeypatch, filo):
    """`started_at`/`timestamp` sqlite'ta REAL (unix epoch). Uç onları ISO-8601 UTC metne çevirir;
    çeviremezse `None` bırakır — 0 epoch'u "1970" diye yazmak uydurma olurdu."""
    _db_kur(_db_yolu(filo, "sef"), [_oturum("sef-1", "m", _T0)])
    c = _acik_kapi(monkeypatch)
    a = _ajan(c.get(UC).json(), "sef")
    ts = a["oturumlar"][0]["ts"]
    assert isinstance(ts, str) and ts.endswith("+00:00"), ts
    assert ts.startswith("2026-"), f"epoch→ISO çevrimi yanlış: {ts}"


def test_ana_beyin_AYRI_bir_ajan_olarak_geliyor(monkeypatch, filo):
    """Ana `~/.hermes/state.db` dördüncü bir muhataptır ve profil botlarıyla KARIŞTIRILMAZ:
    `tur` alanı ikisini ayırır (`bot` vs `ana`)."""
    _db_kur(filo["ana_db"], [_oturum("ana-1", "opus", _T0 + 10)])
    c = _acik_kapi(monkeypatch)
    g = c.get(UC).json()
    ana = [a for a in g["ajanlar"] if a["tur"] == "ana"]
    assert len(ana) == 1, f"ana beyin tekil değil: {[a['ad'] for a in g['ajanlar']]}"
    assert ana[0]["durum"] == "ok", ana[0]
    assert ana[0]["oturumlar"][0]["id"] == "ana-1", ana[0]


# ===================== DURUM 2 · dosya yok =====================

def test_dosya_yoksa_OLCULEMEDI_ve_neden_yolu_soyluyor(monkeypatch, filo):
    """Profil defteri yoksa cevap "bu ajanla konuşulmamış" DEĞİL, "defteri bulamadım"dır.

    `oturumlar` bu hâlde `null`dır — BOŞ LİSTE DEĞİL. Boş liste iletişimin YOKLUĞUNU iddia eder;
    ölçülen şey ölçümün yokluğudur."""
    c = _acik_kapi(monkeypatch)
    a = _ajan(c.get(UC).json(), "bekci")
    assert a["durum"] == "olculemedi", a
    assert a["oturumlar"] is None, "ölçülemeyen kaynak BOŞ LİSTE ile örtüldü"
    assert a["model"] is None and a["son_oturum_ts"] is None, a
    assert a["neden"] and len(a["neden"]) >= 20, a
    assert "state.db" in a["neden"], f"neden HANGİ dosyayı söylemiyor: {a['neden']}"


# ===================== DURUM 3 · şema uyumsuz =====================

def test_sema_uyumsuz_db_OLCULEMEDI_bos_liste_DEGIL(monkeypatch, filo):
    """MUTASYON (b) ÇİVİSİ. Dosya var, açılıyor, ama beklenen tablolar yok.

    Doğru hüküm `olculemedi` + eksik tablonun ADI. `oturumlar: []`e çevrilirse bu çivi ısırır —
    ve ısırması gerekir: boş liste operatöre "karne botu hiç konuşmamış" der, oysa ölçülen şey
    "defterin şeması tanıdığım şema değil"dir."""
    p = _db_yolu(filo, "karne")
    p.parent.mkdir(parents=True)
    c0 = _GERCEK_CONNECT(str(p))
    c0.executescript("CREATE TABLE baska_bir_sey (x TEXT);")
    c0.commit()
    c0.close()

    c = _acik_kapi(monkeypatch)
    a = _ajan(c.get(UC).json(), "karne")
    assert a["durum"] == "olculemedi", a
    assert a["oturumlar"] is None, "şema uyumsuzken boş liste döndü — ölçülemedi örtüldü"
    assert a["neden"] and len(a["neden"]) >= 20, a
    assert "sessions" in a["neden"] and "messages" in a["neden"], (
        f"neden EKSİK TABLOYU adıyla söylemiyor: {a['neden']}")


def test_sutunu_eksik_db_de_OLCULEMEDI(monkeypatch, filo):
    """Tablo adı doğru ama sütun eksikse de hüküm aynıdır. Yalnız tablo adına bakan bir kontrol,
    `SELECT`in `OperationalError`ını çalışma anında yerdi ve orası bir `except`in içi olurdu."""
    p = _db_yolu(filo, "karne")
    p.parent.mkdir(parents=True)
    c0 = _GERCEK_CONNECT(str(p))
    c0.executescript("CREATE TABLE sessions (id TEXT PRIMARY KEY);"
                     "CREATE TABLE messages (session_id TEXT, role TEXT);")
    c0.commit()
    c0.close()

    c = _acik_kapi(monkeypatch)
    a = _ajan(c.get(UC).json(), "karne")
    assert a["durum"] == "olculemedi", a
    assert a["oturumlar"] is None, a
    assert "started_at" in a["neden"] or "content" in a["neden"], (
        f"neden EKSİK SÜTUNU adıyla söylemiyor: {a['neden']}")


def test_bozuk_dosya_da_OLCULEMEDI_istisna_yutulmuyor(monkeypatch, filo):
    """Dosya sqlite bile değilse: `olculemedi` + istisna TÜRÜ `neden`de. Türü yazmak, bir sonraki
    teşhisi "dosya mı yok, izin mi yok, bozuk mu" sorusundan kurtarır (YASA 4: işaretli kaçış)."""
    p = _db_yolu(filo, "bekci")
    p.parent.mkdir(parents=True)
    p.write_bytes(b"bu bir sqlite dosyasi degil\n" * 40)

    c = _acik_kapi(monkeypatch)
    a = _ajan(c.get(UC).json(), "bekci")
    assert a["durum"] == "olculemedi", a
    assert a["oturumlar"] is None, a
    assert "Error" in a["neden"], f"istisna türü neden'de yok: {a['neden']}"


# ===================== MUTASYON (a) · SALT-OKUMA =====================

class _BaglantiCasusu:
    """Ucun açtığı HER sqlite bağlantısını yakalar ve DAVRANIŞINI ölçer.

    İki ayrı kanıt toplanır ve ikisi de gerekli:
      · `dsn`  — açılış dizgesi (`mode=ro` + `uri=True`): mekanizmayı ADIYLA çiviler,
      · `yazilabilir` — bağlantıya GERÇEKTEN yazma denenir. Dize çivisi tek başına yeterli
        değildi: `mode=ro` bir yorumda ya da ölü bir sabitte de geçebilir."""

    def __init__(self):
        self.dsn: list[tuple] = []
        self.yazilabilir: list[bool] = []

    def __call__(self, dsn, *a, **kw):
        conn = _GERCEK_CONNECT(dsn, *a, **kw)
        self.dsn.append((str(dsn), bool(kw.get("uri", False))))
        self.yazilabilir.append(_yazma_denemesi(conn))
        return conn


def _yazma_denemesi(conn) -> bool:
    """Bağlantı GERÇEKTEN yazabiliyor mu? İz bırakmaz: başarılıysa geri alınır."""
    try:
        conn.execute("CREATE TABLE _civi_yazma_denemesi (x)")
    except sqlite3.OperationalError:
        return False
    conn.rollback()
    try:
        conn.execute("DROP TABLE IF EXISTS _civi_yazma_denemesi")
        conn.commit()
    except sqlite3.OperationalError:
        # sessiz-yutma: temizlik denemesi; hüküm YUKARIDA verildi (yazılabilir=True) ve testin
        # kendisi zaten kırmızıya dönecek — temizliğin başarısızlığı o hükmü değiştirmez
        pass
    return True


def test_yazma_PROBU_kendisi_olculuyor(tmp_path):
    """POZİTİF KONTROL — probun kör olmadığı ölçülür. Bu çivi olmadan aşağıdaki "hiçbir bağlantı
    yazamıyor" iddiası VAKUMDA doğru olabilirdi: `_yazma_denemesi` her zaman False dönseydi
    mutasyon (a) sessizce yeşil kalırdı."""
    p = tmp_path / "yazilabilir.db"
    _db_kur(p, [_oturum("x", "m", _T0)])
    rw = _GERCEK_CONNECT(str(p))
    try:
        assert _yazma_denemesi(rw) is True, "prob YAZILABİLİR bağlantıyı yazılamaz sandı — kör"
    finally:
        rw.close()
    ro = _GERCEK_CONNECT(f"file:{p}?mode=ro", uri=True)
    try:
        assert _yazma_denemesi(ro) is False, "prob SALT-OKUNUR bağlantıyı yazılabilir sandı"
    finally:
        ro.close()


def test_baglanti_SALT_OKUNUR_aciliyor(monkeypatch, filo):
    """MUTASYON (a) ÇİVİSİ. `state.db`ler CANLI hermes'in YAZDIĞI dosyalardır; pano bir okuma
    isteğiyle onların üzerine kilit koyamaz ya da yazamaz.

    `mode=ro` kaldırılırsa iki assert birden ısırır: dizge çivisi ve — asıl olan — davranış
    çivisi."""
    _db_kur(_db_yolu(filo, "sef"), [_oturum("sef-1", "m", _T0)])
    _db_kur(filo["ana_db"], [_oturum("ana-1", "m", _T0)])
    casus = _BaglantiCasusu()
    monkeypatch.setattr(sqlite3, "connect", casus)

    c = _acik_kapi(monkeypatch)
    assert c.get(UC).status_code == 200

    assert len(casus.dsn) >= 2, f"casus bağlantı görmedi, çivi kör: {casus.dsn}"
    for dsn, uri in casus.dsn:
        assert uri is True, f"URI kipi kapalı, `mode=ro` hiç uygulanmaz: {dsn}"
        assert "mode=ro" in dsn, f"salt-okuma kipi istenmemiş: {dsn}"
    assert not any(casus.yazilabilir), (
        "uç YAZILABİLİR bir bağlantı açtı — canlı hermes defterine yazma/kilit riski")


def test_okuma_YAN_DOSYA_birakmiyor(monkeypatch, filo):
    """Kilidin ikinci izi: `-wal` / `-shm` / `-journal`. Salt-okunur açılış bunları DOĞURMAZ;
    yazma kipinde açılan bir bağlantı doğurabilir. Defterin damgası da değişmemeli."""
    p = _db_yolu(filo, "sef")
    _db_kur(p, [_oturum("sef-1", "m", _T0)])
    once = (p.stat().st_size, p.stat().st_mtime_ns)
    yan_once = sorted(q.name for q in p.parent.iterdir())

    c = _acik_kapi(monkeypatch)
    assert c.get(UC).status_code == 200

    assert sorted(q.name for q in p.parent.iterdir()) == yan_once, (
        f"okuma yan dosya bıraktı: {sorted(q.name for q in p.parent.iterdir())}")
    assert (p.stat().st_size, p.stat().st_mtime_ns) == once, "salt-okuma defteri DEĞİŞTİRDİ"


# ===================== MUTASYON (c) · mesaj kırpma =====================

def test_mesaj_metni_KIRPILIYOR_ve_kirpildigini_soyluyor(monkeypatch, filo):
    """MUTASYON (c) ÇİVİSİ. Bir brifing mesajı on binlerce karakter olabilir; pano zaman
    çizelgesi onu ham taşıyamaz.

    Kırpma SESSİZ DEĞİLDİR: `kirpildi` + `ham_uzunluk` alanları kırpılmış metni tam sanmayı
    imkânsız kılar (`/api/roadmap`in `ham_kirpildi`/`ham_uzunluk` emsali)."""
    uzun = "Ç" * (api.AJAN_MESAJ_TAVANI * 3 + 17)
    _db_kur(_db_yolu(filo, "sef"), [("sef-1", "m", _T0, [("assistant", _T0, uzun)])])

    c = _acik_kapi(monkeypatch)
    m = _ajan(c.get(UC).json(), "sef")["oturumlar"][0]["mesajlar"][0]
    assert len(m["metin"]) <= api.AJAN_MESAJ_TAVANI, (
        f"kırpma tavanı uygulanmadı: {len(m['metin'])} > {api.AJAN_MESAJ_TAVANI}")
    assert m["kirpildi"] is True, "kırpıldı ama söylenmedi — kırpılmış metin tam sanılır"
    assert m["ham_uzunluk"] == len(uzun), m
    assert m["metin"].startswith("ÇÇÇ"), "kırpma metnin BAŞINI almıyor"


def test_kisa_mesaj_KIRPILMIYOR(monkeypatch, filo):
    """Tavanın ALTINDAKİ mesaj olduğu gibi geçer ve `kirpildi` False'tur. Bu çivi olmadan
    "her mesaj kırpıldı" diyen bir uygulama da yukarıdaki testi geçerdi."""
    kisa = "kısa mesaj"
    _db_kur(_db_yolu(filo, "sef"), [("sef-1", "m", _T0, [("assistant", _T0, kisa)])])
    c = _acik_kapi(monkeypatch)
    m = _ajan(c.get(UC).json(), "sef")["oturumlar"][0]["mesajlar"][0]
    assert m["metin"] == kisa and m["kirpildi"] is False, m
    assert m["ham_uzunluk"] == len(kisa), m


def test_tavan_sabiti_BEYANLI(monkeypatch):
    """Planın şartı: "tavan sabiti beyanlı". Sabit modülde ADIYLA durur ve gerekçesi yazılıdır —
    fonksiyon gövdesine gömülmüş bir `[:600]` ölçülemeyen bir karardır."""
    assert isinstance(api.AJAN_MESAJ_TAVANI, int) and api.AJAN_MESAJ_TAVANI > 0
    assert isinstance(api.AJAN_OTURUM_N, int) and isinstance(api.AJAN_MESAJ_N, int)
    assert isinstance(api.AJAN_OTURUM_TAVANI, int)
    assert api.AJAN_OTURUM_TAVANI >= api.AJAN_OTURUM_N


# ===================== teslim olayları =====================

def test_teslim_olaylari_AJANA_baglaniyor(monkeypatch, filo):
    """`state/events.jsonl`daki `<ad>_brifingi_teslim` satırları AJAN ADINDAN türetilerek
    eşleştirilir — elle yazılmış bir haritayla değil. Elle harita, dördüncü bot doğduğu gün
    sessizce eksik kalırdı (TEK-KAYNAK YASASI)."""
    _olay_yaz(filo["state"], [
        {"ts": "2026-08-30T10:00:00+00:00", "level": "info", "event": "sef_brifingi_teslim",
         "damgalanan": ["alarm"], "detail": "sef teslim"},
        {"ts": "2026-08-30T11:00:00+00:00", "level": "info", "event": "bekci_brifingi_teslim",
         "damgalanan": ["nobet"], "detail": "bekci teslim"},
        {"ts": "2026-08-30T12:00:00+00:00", "level": "info", "event": "daily_cycle",
         "date": "2026-08-30"},
    ])
    c = _acik_kapi(monkeypatch)
    g = c.get(UC).json()
    sef = _ajan(g, "sef")["teslimler"]
    assert [t["event"] for t in sef] == ["sef_brifingi_teslim"], sef
    assert sef[0]["damgalanan"] == ["alarm"] and sef[0]["detail"] == "sef teslim", sef
    assert [t["event"] for t in _ajan(g, "bekci")["teslimler"]] == ["bekci_brifingi_teslim"]
    assert _ajan(g, "karne")["teslimler"] == [], "eşleşmeyen ajana teslim uyduruldu"


def test_ROSTER_DISI_teslim_sessizce_dusmuyor(monkeypatch, filo):
    """`oneri_brifingi_teslim` gibi bir bot profiline karşılık GELMEYEN teslim olayı vardır
    (kaynakta ölçüldü: `ops/oneri_brifingi.py`). Böyle bir satır hiçbir ajana bağlanamaz —
    ama SESSİZCE DÜŞMEZ: ayrı bir kovada adıyla durur (YASA 4)."""
    _olay_yaz(filo["state"], [
        {"ts": "2026-08-30T10:00:00+00:00", "level": "info", "event": "oneri_brifingi_teslim",
         "damgalanan": [], "detail": "roster dışı"},
    ])
    c = _acik_kapi(monkeypatch)
    g = c.get(UC).json()
    assert [t["event"] for t in g["eslesmeyen_teslimler"]] == ["oneri_brifingi_teslim"], g
    for a in g["ajanlar"]:
        assert all(t["event"] != "oneri_brifingi_teslim" for t in (a["teslimler"] or [])), a


def test_events_okunamazsa_teslimler_NULL(monkeypatch, filo):
    """Defter yoksa `teslimler` `null`dır — boş liste "hiç teslim yapılmadı" derdi. Neden
    `kaynak.events_neden`de ADIYLA durur."""
    (filo["state"] / "events.jsonl").unlink(missing_ok=True)
    c = _acik_kapi(monkeypatch)
    g = c.get(UC).json()
    assert g["kaynak"]["events_neden"] and len(g["kaynak"]["events_neden"]) >= 20, g["kaynak"]
    for a in g["ajanlar"]:
        assert a["teslimler"] is None, f"{a['ad']}: ölçülemeyen teslim boş listeyle örtüldü"
    assert g["eslesmeyen_teslimler"] is None, g


# ===================== roster (TEK-KAYNAK) =====================

def test_bot_listesi_PROFIL_DIZININDEN_turuyor(monkeypatch, filo):
    """Roster elle yazılmaz: `deploy/hermes/profiles/` altındaki dizinlerden türer. Dördüncü bir
    profil eklendiği gün uç onu KENDİLİĞİNDEN gösterir — ikinci bir liste ayrışamaz."""
    (filo["bot_koku"] / "yeni_bot").mkdir()
    c = _acik_kapi(monkeypatch)
    g = c.get(UC).json()
    botlar = [a["ad"] for a in g["ajanlar"] if a["tur"] == "bot"]
    assert sorted(botlar) == ["bekci", "karne", "sef", "yeni_bot"], botlar
    assert g["kaynak"]["botlar"] == sorted(botlar), g["kaynak"]


def test_roster_okunamazsa_OK_FALSE_ve_botlar_NULL(monkeypatch, filo, tmp_path):
    """Profil dizini okunamıyorsa kaç bot olduğunu BİLMİYORUZDUR. `botlar: null` bunu söyler
    (boş liste "hiç bot yok" derdi) ve `ok` düşer. Ana beyin roster'dan BAĞIMSIZ ölçülür ve
    listede kalır — ölçülebileni ölçülemeyen yüzünden atmak da bir körlüktür."""
    monkeypatch.setattr(api, "_ajan_bot_koku", lambda: tmp_path / "yok-olan-profiller")
    _db_kur(filo["ana_db"], [_oturum("ana-1", "m", _T0)])
    c = _acik_kapi(monkeypatch)
    g = c.get(UC).json()
    assert g["ok"] is False, g
    assert g["kaynak"]["botlar"] is None, g["kaynak"]
    assert g["hata"] and len(g["hata"]) >= 20, g
    assert [a["tur"] for a in g["ajanlar"]] == ["ana"], g["ajanlar"]


# ===================== parametreler ve yüzey =====================

def test_limit_oturum_sayisini_daraltiyor(monkeypatch, filo):
    _db_kur(_db_yolu(filo, "sef"), [_oturum(f"s{i}", "m", _T0 + i) for i in range(8)])
    c = _acik_kapi(monkeypatch)
    assert len(_ajan(c.get(UC).json(), "sef")["oturumlar"]) == api.AJAN_OTURUM_N
    a = _ajan(c.get(f"{UC}?limit=2").json(), "sef")
    assert [o["id"] for o in a["oturumlar"]] == ["s7", "s6"], a["oturumlar"]


def test_limit_TAVANDA_kirpiliyor_ve_kirpildigini_soyluyor(monkeypatch, filo):
    """Sınırsız `limit` bir kaynak tüketim yüzeyidir. Tavan uygulanır ve UYGULANDIĞI söylenir —
    sessiz kırpma, isteyen "500 oturum aldım" sanırdı."""
    c = _acik_kapi(monkeypatch)
    s = c.get(f"{UC}?limit=99999").json()["suzgec"]
    assert s["limit"] == api.AJAN_OTURUM_TAVANI, s
    assert s["limit_istenen"] == 99999, s
    s0 = c.get(f"{UC}?limit=0").json()["suzgec"]
    assert s0["limit"] >= 1, f"limit=0 tüm oturumları sessizce sildi: {s0}"


def test_ajan_parametresi_SUZGECTIR_yol_degil(monkeypatch, filo):
    """`?ajan=` yalnız TÜRETİLMİŞ roster üzerinde bir üyelik süzgecidir; dosya sistemine ham
    geçmez. Yol geçişi denemesi hiçbir şey döndürmez ve HİÇBİR db açılmaz."""
    _db_kur(_db_yolu(filo, "sef"), [_oturum("sef-1", "m", _T0)])
    c = _acik_kapi(monkeypatch)
    g = c.get(f"{UC}?ajan=sef").json()
    assert [a["ad"] for a in g["ajanlar"]] == ["sef"], g["ajanlar"]

    casus = _BaglantiCasusu()
    monkeypatch.setattr(sqlite3, "connect", casus)
    kotu = c.get(f"{UC}?ajan=../../../../etc/passwd").json()
    assert kotu["ajanlar"] == [], kotu
    assert casus.dsn == [], f"süzgeç dışı bir dize dosya sistemine geçti: {casus.dsn}"
    assert kotu["suzgec"]["ajan"] == "../../../../etc/passwd", (
        "istenen süzgeç geri bildirilmiyor — operatör neden boş döndüğünü göremez")


def test_uc_imzasi_YALNIZ_uc_parametre(monkeypatch):
    """YAPISAL KAPI (v312 emsali): uca yeni bir girdi eklendiği gün bu çivi öter ve yol-geçişi
    tartışması BİLEREK yeniden açılır — sessizce açılmaz."""
    assert list(inspect.signature(api.api_ajanlar).parameters) == ["request", "limit", "ajan"]


def test_kaynak_blogu_HER_KAYNAGI_adiyla_sayiyor(monkeypatch, filo):
    """Uç ÜÇ kaynaktan okur (profil defterleri · ana beyin · olay defteri). `kaynak` bloğu
    üçünü de yolu ile söyler; okuduğu ama saymadığı bir kaynak, ölçülemeyen bir bağımlılıktır."""
    c = _acik_kapi(monkeypatch)
    k = c.get(UC).json()["kaynak"]
    for alan in ("profil_koku", "events", "ana_beyin", "bot_koku", "botlar", "events_neden",
                 "teslim_tavani", "eslesmeyen_toplam"):
        assert alan in k, f"kaynak bloğunda `{alan}` yok: {sorted(k)}"
    assert str(filo["profil_koku"]) == k["profil_koku"], k
    assert str(filo["ana_db"]) == k["ana_beyin"], k


def test_varsayilan_yollar_GERCEK_HERMESI_gosteriyor():
    """Yukarıdaki her çivi sentetik köklerle koşar; bu çivi VARSAYILANLARIN doğru yeri
    gösterdiğini ölçer. Olmasaydı tüm dosya yeşil yanarken uç canlıda BOŞ kalabilirdi —
    "sentetikte çalışıyor" ile "canlıda çalışıyor" tam olarak burada ayrışır.

    Dosyaların VARLIĞI iddia EDİLMEZ (bu makinede profil kökü yok, ölçüldü 2026-08-31); iddia
    edilen tek şey ucun DOĞRU YERE baktığıdır."""
    assert api._ajan_profil_koku() == Path.home() / ".hermes" / "profiles"
    assert api._ajan_ana_beyin_db() == Path.home() / ".hermes" / "state.db"
    assert api._ajan_bot_koku() == Path(api.config.ROOT) / "deploy" / "hermes" / "profiles"
    assert sorted(p.name for p in api._ajan_bot_koku().iterdir() if p.is_dir()) == \
        ["bekci", "karne", "sef"], "depodaki bot roster'ı değişti — planın zemini bayatladı"


def test_mesaj_sayisi_TAVANLI_ve_KUYRUKTAN(monkeypatch, filo):
    """Oturum başına son N mesaj alınır (BAŞTAN değil KUYRUKTAN: operatör son konuşulanı arar)
    ve N beyanlı sabittir."""
    n = api.AJAN_MESAJ_N + 5
    _db_kur(_db_yolu(filo, "sef"), [_oturum("sef-1", "m", _T0, n_mesaj=n)])
    c = _acik_kapi(monkeypatch)
    mesajlar = _ajan(c.get(UC).json(), "sef")["oturumlar"][0]["mesajlar"]
    assert len(mesajlar) == api.AJAN_MESAJ_N, len(mesajlar)
    assert mesajlar[-1]["metin"] == f"sef-1-mesaj-{n - 1}", "kuyruk değil baş alınmış"
    assert mesajlar[0]["metin"] == f"sef-1-mesaj-{n - api.AJAN_MESAJ_N}", mesajlar[0]


def test_bos_defter_BOS_LISTE_dondurur(monkeypatch, filo):
    """Şeması DOĞRU ama satırı olmayan defter: `durum: ok` + `oturumlar: []`. Burada boş liste
    DOĞRU cevaptır ve ölçülemedi ile karıştırılmamalıdır — iki hâlin ayrımı ucun tüm anlamıdır."""
    _db_kur(_db_yolu(filo, "sef"), [])
    c = _acik_kapi(monkeypatch)
    a = _ajan(c.get(UC).json(), "sef")
    assert a["durum"] == "ok" and a["oturumlar"] == [], a
    assert a["model"] is None and a["son_oturum_ts"] is None, a
    assert a["neden"] is None, a


# =====================================================================
# DÜZELTME TURU 1 (görev incelemesi, 2026-08-31) — ÖLÇÜLMEMİŞ DALLAR
#
# İnceleme üç örtüsüz yüzey buldu ve hepsi AYNI SINIFTAN: kod doğru davranıyordu ama hiçbir çivi
# davranışı ÖLÇMÜYORDU, yani bozulduğu gün sessizce bozulacaktı.
#   K-2 · teslim kuyruğunun ÜÇ davranışı (sıra · tavan · yarım-satır) — en pahalı gedik: sıra
#         çivisiz olduğu için `reversed` düşse uç DOLU ama EN ESKİ listeyi döndürürdü; operatör
#         hiçbir boşluk görmez, sadece yanlış uçtan bakardı.
#   K-1 · iki `# sessiz-yutma:` işaretli kaçış. Depo kuralı: işaretli kaçış bir BEYANDIR ve
#         beyanın çivisi yoksa davranış ölçülmemiştir.
#   K-5 · teslim projeksiyonunun BEDELİ (`olculemeyen` alanının sessiz düşüşü).
# =====================================================================

def _dolgu(n: int) -> bytes:
    """TAM `n` baytlık dolgu. `_brifingi_teslim` izi TAŞIMAZ — ön süzgece takılsaydı dolgu,
    ölçülen şeyin kendisine karışırdı."""
    satir = (json.dumps({"event": "dolgu", "x": "y" * 200}) + "\n").encode()
    b = satir * (n // len(satir))
    if kalan := n - len(b):
        b += b"z" * (kalan - 1) + b"\n"
    return b


# ---------- K-2 (a) · SIRA ----------

def test_teslimler_YENIDEN_ESKIYE_siralaniyor(monkeypatch, filo):
    """PLAN SÖZLEŞMESİ (T1'DEN MİRAS): `teslimler` YENİDEN→ESKİYE. Defter KRONOLOJİK yazılır,
    yani ters çevirme şarttır.

    Bu, `_ajan_teslimleri`deki `reversed`ın TEK çivisidir ve gerekçesi sinsiliktir: `reversed`
    düşerse uç hata vermez, boş dönmez, kısalmaz — sadece EN ESKİ 25 teslimi döndürür. Operatör
    dolu bir liste görür ve yanlış uçtan bakar."""
    _olay_yaz(filo["state"], [
        {"ts": f"2026-08-{gun:02d}T10:00:00+00:00", "event": "sef_brifingi_teslim",
         "damgalanan": [], "detail": f"gun-{gun}"} for gun in (10, 11, 12)])
    c = _acik_kapi(monkeypatch)
    t = _ajan(c.get(UC).json(), "sef")["teslimler"]
    assert [x["detail"] for x in t] == ["gun-12", "gun-11", "gun-10"], (
        f"teslimler yeniden→eskiye sıralanmıyor: {[x['detail'] for x in t]}")


# ---------- K-2 (b) · TAVAN ----------

def test_teslim_tavani_kesiyor_ve_KESTIGINI_soyluyor(monkeypatch, filo):
    """`_AJAN_TESLIM_N` tavanı kesiyor mu, ve kestiğini SÖYLÜYOR mu?

    İkincisi olmadan birincisi bir kusurdur: sessiz `[:25]`, operatöre "bu ajanın tüm teslim
    tarihçesi bu" sandırırdı. Kesme YENİ UÇTAN tutar — eski uçtan tutsaydı liste yine 25 olurdu
    ve sayı çivisi bunu göremezdi, o yüzden uçlar ayrıca ölçülüyor."""
    n = api._AJAN_TESLIM_N + 7
    _olay_yaz(filo["state"], [
        {"ts": f"2026-08-31T10:{i:02d}:00+00:00", "event": "sef_brifingi_teslim",
         "damgalanan": [], "detail": f"t{i:03d}"} for i in range(n)])
    c = _acik_kapi(monkeypatch)
    g = c.get(UC).json()
    a = _ajan(g, "sef")
    assert len(a["teslimler"]) == api._AJAN_TESLIM_N, len(a["teslimler"])
    assert a["teslim_toplam"] == n, f"gerçek sayı söylenmiyor: {a['teslim_toplam']}"
    assert a["teslim_kirpildi"] is True, "kesildi ama söylenmedi"
    assert g["kaynak"]["teslim_tavani"] == api._AJAN_TESLIM_N, g["kaynak"]
    assert a["teslimler"][0]["detail"] == f"t{n - 1:03d}", "kesme EN YENİYİ düşürdü"
    assert a["teslimler"][-1]["detail"] == f"t{n - api._AJAN_TESLIM_N:03d}", a["teslimler"][-1]
    assert all(x["detail"] != "t000" for x in a["teslimler"]), "en eski olay kesilmemiş"


def test_tavan_altinda_KIRPILMADI_diyor(monkeypatch, filo):
    """Tavanın ALTINDA `teslim_kirpildi` False'tur. Bu çivi olmadan "her zaman kırpıldı" diyen
    bir uygulama da yukarıdakini geçerdi — bayrak ölçmez, sabit yazardı."""
    _olay_yaz(filo["state"], [
        {"ts": "2026-08-30T10:00:00+00:00", "event": "sef_brifingi_teslim", "detail": "a"},
        {"ts": "2026-08-30T11:00:00+00:00", "event": "sef_brifingi_teslim", "detail": "b"}])
    c = _acik_kapi(monkeypatch)
    a = _ajan(c.get(UC).json(), "sef")
    assert a["teslim_kirpildi"] is False and a["teslim_toplam"] == 2, a


# ---------- K-2 (c) · KUYRUK SEEK + YARIM SATIR ----------

def test_teslim_kuyrugu_YARIM_SATIRI_atiyor_ve_PENCERE_gercek(monkeypatch, filo):
    """CANLI ~9 MB `events.jsonl`de HER İSTEKTE koşan yol — ve bugüne kadar hiç ölçülmemişti.

    Kurulum, kuyruk penceresinin başlangıcını (`boyut - _AJAN_TESLIM_KUYRUK`) BİR SATIRIN
    ORTASINA, tam da bir HAYALET olayın ilk baytına düşürür. Yarım satır atılmazsa o hayalet
    GEÇERLİ JSON olarak ayrıştırılır ve `eslesmeyen_teslimler`de belirir — yani `f.readline()`ın
    varlığı doğrudan gözlenebilir hâle gelir. (Rastgele bir yarım satır bozuk JSON verir ve zaten
    yutulurdu; o kurulum `readline()` hakkında HİÇBİR ŞEY söylemezdi.)

    Aynı test pencerenin GERÇEK olduğunu da ölçer: 512 KB'ın dışında kalan bir teslim olayı
    dönmemeli. Seek hiç yapılmasaydı tüm dosya okunur ve o olay da gelirdi."""
    kuyruk = api._AJAN_TESLIM_KUYRUK
    hayalet = json.dumps({"ts": "2026-08-01T00:00:00+00:00",
                          "event": "hayalet_brifingi_teslim",
                          "detail": "YARIM SATIRIN KUYRUGUNDAN geldi"}).encode()
    yeni = json.dumps({"ts": "2026-08-31T00:00:00+00:00", "event": "sef_brifingi_teslim",
                       "detail": "PENCERE ICI"}).encode()
    eski = json.dumps({"ts": "2026-07-01T00:00:00+00:00", "event": "sef_brifingi_teslim",
                       "detail": "PENCERE DISI"}).encode()

    son_dolgu_n = kuyruk - (len(hayalet) + 1 + len(yeni) + 1)
    assert son_dolgu_n > 0, "kurulum kuyruk sabitiyle uyumsuz"
    yarim = b'{"event": "YARIM-SATIR-BASI", "x": "'          # satır sonu YOK — bilerek
    bas = eski + b"\n" + _dolgu(50_000)
    govde = bas + yarim + hayalet + b"\n" + yeni + b"\n" + _dolgu(son_dolgu_n)
    (filo["state"] / "events.jsonl").write_bytes(govde)

    # KURULUM ÇİVİSİ: ölçüm ancak seek noktası hayaletin İLK baytına düşerse anlamlı.
    assert len(govde) - kuyruk == len(bas) + len(yarim), (
        "kurulum kaydı: pencere başlangıcı hayalete düşmüyor, bu ölçüm GEÇERSİZ")

    c = _acik_kapi(monkeypatch)
    g = c.get(UC).json()
    detaylar = [t["detail"] for t in _ajan(g, "sef")["teslimler"]]
    assert "PENCERE ICI" in detaylar, f"kuyruk içindeki teslim kaçırıldı: {detaylar}"
    assert "PENCERE DISI" not in detaylar, (
        "kuyruk-seek yapılmadı: 512 KB penceresinin DIŞINDAKİ olay da okundu")
    assert g["eslesmeyen_teslimler"] == [], (
        f"yarım satırın kuyruğu TAM SATIR sanıldı — `readline()` atmıyor: "
        f"{g['eslesmeyen_teslimler']}")


# ---------- K-1 · İŞARETLİ SESSİZ-YUTMA DALLARI ----------

def test_bozuk_damga_HAM_korunur_ve_ajan_ok_kalir(monkeypatch, filo):
    """`_ajan_ts`in işaretli kaçışı: çevrilemeyen damga `None` olur. Yutulan ŞEY ne oldu?

    Plan sözleşmesi (T1'DEN MİRAS) "ham korunur" der ve `ts_ham` tam olarak bunu yapar — kaçış
    böylece GÖZLENEBİLİR hâle gelir. Ham düşseydi operatör "ts yok" görür, defterde ne yazdığını
    asla öğrenemezdi.

    İkinci hüküm ORANTIDIR: tek bozuk damga TÜM ajanı `olculemedi` yapmaz ve o oturumu listeden
    DÜŞÜRMEZ (sessiz atlama, `_karar_belge_kaydi` ile aynı ders). Üçüncüsü POZİTİF KONTROL:
    sağlam damgada `ts_ham` None'dır — yoksa alan ölçmez, her zaman yazardı.

    sqlite DİNAMİK TİPLİ: `started_at REAL` sütununa metin yazmak mümkündür ve canlıda bozuk bir
    yazımın alacağı biçim tam olarak budur."""
    p = _db_yolu(filo, "sef")
    _db_kur(p, [_oturum("saglam", "m", _T0)])
    c0 = _GERCEK_CONNECT(str(p))
    try:
        c0.execute("INSERT INTO sessions (id, model, started_at) VALUES (?,?,?)",
                   ("bozuk-damgali", "m", "BOZUK-DAMGA"))
        c0.execute("INSERT INTO messages (session_id, role, content, timestamp) VALUES (?,?,?,?)",
                   ("bozuk-damgali", "assistant", "gövde yerinde", "DE-BOZUK"))
        c0.commit()
    finally:
        c0.close()

    c = _acik_kapi(monkeypatch)
    a = _ajan(c.get(UC).json(), "sef")
    assert a["durum"] == "ok", "tek bozuk damga TÜM ajanı ölçülemez yaptı — orantısız"
    kimlikler = [o["id"] for o in a["oturumlar"]]
    assert "bozuk-damgali" in kimlikler, f"bozuk damgalı oturum listeden DÜŞTÜ: {kimlikler}"

    o = next(x for x in a["oturumlar"] if x["id"] == "bozuk-damgali")
    assert o["ts"] is None, o
    assert o["ts_ham"] == "BOZUK-DAMGA", "yutulan ham damga KAYBOLDU — kaçış gözlenemez"
    m = o["mesajlar"][0]
    assert m["ts"] is None and m["ts_ham"] == "DE-BOZUK", m
    assert m["metin"] == "gövde yerinde", "bozuk damga mesaj GÖVDESİNİ de düşürdü"

    saglam = next(x for x in a["oturumlar"] if x["id"] == "saglam")
    assert saglam["ts"] is not None and saglam["ts_ham"] is None, (
        "sağlam damgada da `ts_ham` dolu — alan ölçmüyor, her zaman yazıyor")


def test_bozuk_JSON_satiri_TUM_defteri_dusurmuyor(monkeypatch, filo):
    """`_ajan_teslimleri`nin işaretli kaçışı: bozuk bir JSON satırında `continue`.

    ÖLÇÜLEN ORANTI: bir satır bozuk diye tüm teslim tarihçesini `null` ilan etmek, ölçülebilir
    olanı ölçülemeyen yüzünden atmak olurdu. Bozuk satır SAYILMAZ da (`teslim_toplam`) — yoksa
    listede olmayan bir olay sayıda görünürdü.

    Satır `_brifingi_teslim` İÇERİR, yani ön süzgeci GEÇER ve gerçekten `json.loads`a ulaşır;
    aksi hâlde test yanlış dalı ölçerdi."""
    with open(filo["state"] / "events.jsonl", "a", encoding="utf-8") as f:
        f.write('{"event": "sef_brifingi_teslim", "ts": "2026-08-30T09:00:00+00:00" BOZUK\n')
    _olay_yaz(filo["state"], [
        {"ts": "2026-08-30T10:00:00+00:00", "event": "sef_brifingi_teslim",
         "damgalanan": [], "detail": "saglam"}])

    c = _acik_kapi(monkeypatch)
    a = _ajan(c.get(UC).json(), "sef")
    assert a["teslimler"] is not None, "tek bozuk satır TÜM teslim defterini düşürdü"
    assert [t["detail"] for t in a["teslimler"]] == ["saglam"], a["teslimler"]
    assert a["teslim_toplam"] == 1, f"bozuk satır teslim olarak SAYILDI: {a['teslim_toplam']}"


# ---------- K-5 · BEDEL BEYANI ----------

def test_olculemeyen_alani_TASINIYOR_yoksa_null(monkeypatch, filo):
    """BEDEL YASASI. `ops/sef_brifingi.py::main` teslim olayına `olculemeyen=[…]` basar — "hangi
    kaynaklar ölçülemedi" listesi. Projeksiyon onu sessizce düşürüyordu: ölçülemezliği gösteren
    bir alanın, ölçülemezliği göstermek için yazılmış bir uçta kaybolması.

    UYDURMA YASAĞI ikinci yarısı: alanı BASMAYAN üreticide (bekci/karne) `olculemeyen` `null`dır,
    boş liste DEĞİL — boş liste "hiçbir kaynak ölçülemedi kaldı" derdi ve bu ölçülmemiş bir
    iddiadır."""
    _olay_yaz(filo["state"], [
        {"ts": "2026-08-30T10:00:00+00:00", "event": "sef_brifingi_teslim",
         "damgalanan": ["alarm"], "olculemeyen": ["earnings", "insider"], "detail": "d"},
        {"ts": "2026-08-30T11:00:00+00:00", "event": "bekci_brifingi_teslim",
         "damgalanan": [], "detail": "alanı basmayan üretici"}])
    c = _acik_kapi(monkeypatch)
    g = c.get(UC).json()
    assert _ajan(g, "sef")["teslimler"][0]["olculemeyen"] == ["earnings", "insider"], (
        "`olculemeyen` hâlâ projeksiyonda düşüyor")
    assert _ajan(g, "bekci")["teslimler"][0]["olculemeyen"] is None, (
        "alanı basmayan üreticide `olculemeyen` uydurulmuş")


# =================================================================================================
# T2 · YÜZEY SÖZLEŞMESİ — ucun ürettiği her alanın PANODA okuyucusu var
# =================================================================================================
# YASA 6'NIN KUZENİ, `test_yol_haritasi_tablo_yuzeyi_v343`ün ölçülmüş dersiyle: `/api/roadmap`
# `tablolar[]`ı açıldığı günden beri gönderiyordu ve pano onu HİÇ okumuyordu — `§2 TAHTA` operatörün
# baktığı grafikte BOŞ bir satırdı. Uç kusursuzdu, okuyucusu yoktu. Bu blok aynı sınıfı
# `/api/ajanlar` için kapatır ve beklenen alan kümesini ELLE YAZMAZ: GERÇEK bir yanıttan türetir,
# yani uç büyüdüğünde çivi kendiliğinden büyür.
#
# T1 raporunun Rol-1'e bıraktığı 4 numaralı kalem tam olarak buydu: "`null` ≠ `[]`; pano `null`ı
# 'ölçülemedi + neden' olarak çizmeli, boş durum olarak DEĞİL — bu ucun tüm anlamı o ayrımda."
#
# BU BLOĞUN KENDİ SINIRI BEYANLIDIR: kaynak metnini okuyan bir çivi, ÇALIŞAN arayüzü ölçmez.
# "Alan okunuyor" ile "alan operatöre görünüyor" arasındaki boşluk ancak canlı doğrulamayla
# kapanır (Rol-1'in dağıtım adımı; repo kuralı yerelde pano yüklemeyi yasaklıyor). Çiviler bu
# yüzden okuma DALINI (`filoOku.ts`) ve ÇİZİM DALINI (`Filo.tsx`) AYRI ölçer — birini ötekinin
# yerine saymak, `roadmap.ts`in okuyup çizmediği alanlarla aynı arızayı üretirdi.

import re

_KOK = Path(api.config.ROOT)
_YUZEY_OKUYUCU = _KOK / "ui/src/pano/yuzeyler/ajan/filoOku.ts"
_YUZEY_BILESEN = _KOK / "ui/src/pano/yuzeyler/ajan/Filo.tsx"
_YUZEY_KABUK = _KOK / "ui/src/pano/yuzeyler/Ajan.tsx"
_YUZEY_SOHBET = _KOK / "ui/src/pano/yuzeyler/ajan/SohbetHatti.tsx"
_YUZEY_KAYIT = _KOK / "ui/src/pano/alanlar.ts"

_TS_YORUM = re.compile(r"/\*.*?\*/|(?<![:'\"])//[^\n]*", re.S)


def _soy(metin: str) -> str:
    """TS/TSX yorumlarını ÇIKAR — `test_ui_pilot_kapilari_v286::_soy`nin ölçülmüş dersi.

    Bu deponun belge geleneği kararın gerekçesini yazarken YASAKLANAN ŞEYİ ALINTILAR ve şerhler
    ekranda görünen cümlelerin aynısını taşır. Soymadan ölçen çivi kendi belgesiyle yeşile
    döner: BU DOSYANIN İLK HÂLİNDE tam olarak bu oldu — üç mutasyon (kesme beyanı silindi ·
    "DEĞİLDİR" ekrandan kaldırıldı · gerekçe tarihsizleştirildi) hiçbir çiviyi ısırmadı, çünkü
    aynı sözcükler bileşenin başlık şerhinde duruyordu. Yeşil, ölçümün değil şerhin yeşiliydi."""
    return _TS_YORUM.sub("", metin)


#: BEYAN EDİLMİŞ OKUNMAYANLAR — her biri ≥20 karakter gerekçesiyle (v343 deseni). Boş olması
#: "kural gevşek" demek DEĞİLDİR: bugün ucun HİÇBİR alanı okunmadan bırakılmadı ve testin kendisi
#: bayat beyanı da (gövdede artık olmayan bir alan) kırmızıya çevirir.
YUZEYDE_OKUNMAYAN: dict[str, str] = {}


def _zengin_govde(monkeypatch, filo) -> dict:
    """HER alanı DOLDURAN bir yanıt: üç bot + ana beyin + teslimler + sahipsiz teslim.

    Alan kümesi bu gövdeden TÜRETİLİYOR, elle yazılmıyor — bu yüzden gövdenin gerçekten zengin
    olması testin ön koşuludur ve aşağıda ayrıca ölçülüyor."""
    _db_kur(_db_yolu(filo, "sef"), [_oturum("s-yeni", "opus-ultra", _T0 + 3600),
                                    _oturum("s-eski", "opus", _T0)])
    _db_kur(filo["ana_db"], [_oturum("a-1", "sonnet", _T0 + 60)])
    _olay_yaz(filo["state"], [
        {"ts": "2026-08-30T10:00:00+00:00", "event": "sef_brifingi_teslim",
         "damgalanan": ["alarm"], "olculemeyen": ["earnings"], "detail": "d"},
        # SAHİPSİZ: roster'da karşılığı yok → `eslesmeyen_teslimler` kovası dolar
        {"ts": "2026-08-30T11:00:00+00:00", "event": "oneri_brifingi_teslim",
         "damgalanan": [], "detail": "sahipsiz"}])
    c = _acik_kapi(monkeypatch)
    g = c.get(UC).json()
    assert g["eslesmeyen_teslimler"], "sahipsiz teslim kovası boş — gövde yeterince zengin değil"
    return g


def _alan_kumesi(g: dict) -> set[str]:
    """Gövdedeki TÜM anahtarlar, iç içe. Liste KAPLARI da dâhildir: `oturumlar`/`teslimler`
    okunmadan çizim zaten olamaz, ama okuyucunun onları ADIYLA okuduğunu görmek `?? []` ile
    sessizce boşa düşen bir dalı yakalamanın tek yoludur."""
    bulunan: set[str] = set()

    def gez(x) -> None:
        if isinstance(x, dict):
            bulunan.update(x.keys())
            for v in x.values():
                gez(v)
        elif isinstance(x, list):
            for v in x:
                gez(v)

    gez(g)
    return bulunan


@pytest.fixture(scope="module")
def yuzey() -> dict[str, str]:
    """Yüzey kaynağı, YORUMLARI SOYULMUŞ ve DALLARINA AYRILMIŞ.

    `oku` (okuma) ile `bilesen` (çizim) ayrı tutulur çünkü ikisi AYRI iddiadır: bir alanı
    okuyup çizmemek `roadmap.ts` arızasının ta kendisiydi."""
    for p in (_YUZEY_OKUYUCU, _YUZEY_BILESEN, _YUZEY_KABUK):
        assert p.exists(), f"pano yüzeyi yok: {p} — uç okuyucusuz kaldı (YASA 6)"
    dallar = {"oku": _YUZEY_OKUYUCU, "bilesen": _YUZEY_BILESEN, "kabuk": _YUZEY_KABUK,
              "sohbet": _YUZEY_SOHBET, "kayit": _YUZEY_KAYIT}
    d = {ad: _soy(p.read_text(encoding="utf-8")) for ad, p in dallar.items()}
    d["hepsi"] = "\n".join(d[ad] for ad in ("oku", "bilesen", "kabuk"))
    return d


def test_T2a_uretilen_HER_alanin_panoda_okuyucusu_var(monkeypatch, filo, yuzey):
    """Beklenen küme ELLE YAZILMADI: gerçek bir yanıttan türetildi (v343 deseni)."""
    alanlar = _alan_kumesi(_zengin_govde(monkeypatch, filo))
    assert len(alanlar) >= 30, f"gövde beklenenden dar ({len(alanlar)} alan) — kapı boşa düşüyor olabilir"
    ihlal = [a for a in sorted(alanlar)
             if f'["{a}"]' not in yuzey["hepsi"] and a not in YUZEYDE_OKUNMAYAN]
    assert not ihlal, (
        f"uç bu alanları üretiyor ama pano ne OKUYOR ne de okumadığını BEYAN ediyor: {ihlal}. "
        "Ya `filoOku.ts`te oku, ya `YUZEYDE_OKUNMAYAN`a gerekçesiyle yaz. Okuyucusuz alan "
        "üretilmemiş sayılır (YASA 6 kuzeni — `§2 TAHTA` vakası).")
    bos = [a for a, neden in YUZEYDE_OKUNMAYAN.items() if len(neden) < 20]
    assert not bos, f"beyan gerekçesiz: {bos} (≥20 karakter şart — YASA 4 deseni)"
    olu = [a for a in YUZEYDE_OKUNMAYAN if a not in alanlar]
    assert not olu, f"beyan edilen alan ucun gövdesinde YOK — beyan bayatlamış: {olu}"


def test_T2b_okuyucu_NULL_donduren_dizi_okuyucusunu_kullaniyor(yuzey):
    """`null` ≠ `[]` AYRIMI BİR İTHALAT KARARINA BAĞLI ve bu çivi o kararı tutuyor.

    Depoda İKİ `dizi()` var: `kanban/oku.ts`inki dizi değilse `null` döner (ölçülemedi),
    `ajan/ortak.tsx`inki BOŞ DİZİ döner. İkincisini bu okuyucuya bağlamak tek satırlık, sessiz
    ve ölümcül bir değişikliktir: `oturumlar: null` ekranda "hiç oturum yok" diye çizilir ve
    ucun tüm anlamı — okuyamadığını söyleyebilmesi — kaybolur. Hiçbir tip hatası vermez."""
    s = yuzey["oku"]
    assert 'from "../kanban/oku"' in s, (
        "okuyucu `null` döndüren `dizi()`yi ithal etmiyor — `null` ile `[]` ayrımı düşmüş olabilir")
    assert './ortak"' not in s.replace(" ", ""), (
        "okuyucu `ajan/ortak`tan ithal ediyor: oradaki `dizi()` BOŞ DİZİ döndürür ve "
        "'ölçülemedi' ile 'ölçüldü-boş' aynı kutuya düşer")


def test_T2c_SIRA_yuzeyde_ters_cevrilmiyor(yuzey):
    """SIRA SÖZLEŞMESİ UÇTAN GELİR (oturumlar yeniden→eskiye · mesajlar eskiden→yeniye ·
    teslimler yeniden→eskiye). Yüzeyde tek satırlık bir `sort`/`reverse` hiçbir şeyi kırmaz,
    hata vermez, listeyi KISALTMAZ — yalnız operatöre konuşmayı tersten okutur."""
    for yasak in (".reverse()", ".sort("):
        assert yasak not in yuzey["hepsi"], (
            f"yüzey `{yasak}` çağırıyor — sıra ucun sözleşmesidir ve pano onu DEĞİŞTİRMEZ; "
            "görsel bir tersleme gerekiyorsa BEYANLA yapılır")


def test_T2d_ts_ham_OKUNUYOR_ve_CIZILIYOR(yuzey):
    """Damga çevrilemediğinde pano HAM değeri gösterir. `tsHam`ı okuyup çizmemek, T1'in düzeltme
    turunda koda taşınan sözleşmeyi yüzeyde geri almak olurdu (ölçülemezliği iki kat yapar)."""
    assert '["ts_ham"]' in yuzey["oku"], "`ts_ham` hiç okunmuyor"
    assert "tsHam" in yuzey["bilesen"], "`ts_ham` okunuyor ama BİLEŞENE hiç ulaşmıyor"
    assert "ham damga" in yuzey["bilesen"], (
        "ham değer ekranda ETİKETSİZ — okuyan onu çevrilmiş bir damga sanabilir")


def test_T2e_kirpmalar_CIZIM_DALINDA_beyan_ediliyor(yuzey):
    """Üç kırpmanın üçü de: mesaj gövdesi · oturum sayısı (limit tavanı) · teslim listesi.
    ÖLÇÜM ÇİZİM DALINDA yapılır (`Filo.tsx`), okuma dalında değil: `filoOku.ts` alanı taşıyıp
    bileşen onu hiç kullanmasaydı kırpma yine SESSİZ olurdu ve okuyucu kırpılmış bir listeyi
    'tüm tarihçe' sanardı."""
    for alan, ne in (("kirpildi", "mesaj gövdesi kırpması"),
                     ("limitIstenen", "oturum sayısı tavanı"),
                     ("teslimKirpildi", "teslim listesi tavanı"),
                     ("teslimToplam", "teslim listesinin GERÇEK sayısı")):
        assert alan in yuzey["bilesen"], f"{ne} çizim dalında kullanılmıyor (`{alan}` yok)"
    assert "KESİLDİ" in yuzey["bilesen"], "kesme ekranda SÖYLENMİYOR — okuyan listeyi tam sanar"


def test_T2f_olculemeyen_ajan_BOS_DURUM_gibi_cizilmiyor(yuzey):
    """`durum: olculemedi` bir boş durum DEĞİLDİR ve yüzey `neden`i çizmek ZORUNDA."""
    assert '["neden"]' in yuzey["oku"], "ajanın `neden` alanı hiç okunmuyor"
    assert "a.neden" in yuzey["bilesen"], "`neden` okunuyor ama ÇİZİLMİYOR — okuyucu yüzey değildir"
    assert "DEĞİLDİR" in yuzey["bilesen"], (
        "ölçülemeyen defterin 'iletişim yok' ile aynı şey OLMADIĞI ekranda söylenmiyor; "
        "boş bir kart operatöre ölçülmemiş bir sessizliği ölçülmüş gibi okutur")


def test_T2g_sohbet_kutusu_HALA_KAPALI_ve_gerekce_TARIHLI(yuzey):
    """DALGA-A SÖZLEŞMESİ: uç açıldı, KUTU AÇILMADI. Okuma yolunun varlığı yazma yolunu var
    göstermez — üstelik artık yanındaki sekme gerçek konuşmaları çizdiği için kutuyu açmak daha
    inandırıcı bir yalan olurdu. Gerekçe EKRANDA ölçülür (şerhte değil): operatör şerhi okumaz."""
    ham = _YUZEY_SOHBET.read_text(encoding="utf-8")
    assert "disabled" in ham and "InputGroupTextarea" in ham, "sohbet kutusu artık devre dışı değil"
    s = yuzey["sohbet"]
    assert "2026-08-31" in s, "ekrandaki gerekçe TARİHSİZ — hangi turda ne değiştiği okunamaz"
    assert "dalga-B" in s, "ekrandaki gerekçe kutunun NE ZAMAN açılacağını söylemiyor"
    assert "/api/ajanlar" in s, (
        "ekrandaki gerekçe hâlâ 'hiçbir ajan ucu yok' diyor — bugün AÇILAN uç yazılmamış, metin bayat")


def test_T2h_filo_bolumu_KAYITLI_ve_derin_bag_calisiyor(yuzey):
    """Bölüm kaydı olmadan kenar çubuğu sekmeye bağ üretmez ve `#/dashboard/chat/filo` derin bağı
    sekmeyi hiç açmaz (`bolumSec` bilinmeyen bölümü `sohbet`e düşürür) — sekme sessizce erişilmez
    olurdu."""
    assert '"filo"' in yuzey["kabuk"], "`Ajan.tsx` BOLUMLER listesinde `filo` yok — derin bağ sekmeyi açmaz"
    assert 'kimlik: "filo"' in yuzey["kayit"], (
        "`alanlar.ts` kaydında `filo` bölümü yok — kenar çubuğu bu sekmeye bağ üretmez")


def test_T2i_filo_AYRI_kapida_hipotez_ucundan_bagimsiz(yuzey):
    """İKİ UÇ, İKİ KAPI. `Filo` `/api/ajanlar`dan beslenir; `/api/agent`in düşmesi onu
    GİZLEYEMEZ. Tek kapı tüm yüzeyi sarsaydı, sağlam ve ölçülmüş bir ajan defteri başka bir
    kaynağın arızası yüzünden 'okunamadı' kutusunun arkasında kalırdı."""
    k = yuzey["kabuk"]
    assert '"/api/ajanlar"' in k, "kabuk yeni ucu hiç çekmiyor"
    assert '<Filo ' in k, "`Filo` bileşeni hiç çizilmiyor"
    assert k.index("<Filo ") < k.index('ad="`/api/agent`"'), (
        "`Filo` `/api/agent` kapısının İÇİNDE çiziliyor — hipotez ucu düşerse ajan defteri de kaybolur")


# =================================================================================================
# T2 · DÜZELTME TURU 1 (inceleme `task-2-review.md`, 2026-08-31) — B1 + B2
# =================================================================================================
# İkisi de AYNI SINIFTAN: panonun "sessiz boşluk yok / neden ekranda durur" kuralının iki deliği.
# B1 ekranı sessizce boşaltabiliyordu, B2 ucun kendi hükmünü yutuyordu.
#
# B1'İN ÇİVİSİ KAYNAK METNİ OKUMUYOR, DAVRANIŞI KOŞUYOR. İncelemenin B4 bulgusu tam da bunu
# söylüyordu: `assert "<kimlik>" in kaynak` biçimindeki bir çivi, ifadeyi bozan ama kimliği
# koruyan bir mutasyonda ISIRMAZ. `aktifAnahtar` bu yüzden SAF bir fonksiyon olarak yazıldı ve
# burada `esbuild` + `node` ile gerçekten çağrılıyor — emsal `test_pano_palet_v152` (aynı
# beyanlı atlama disipliniyle: araç yoksa test GEÇMİŞ sayılmaz, ATLANIR).

import shutil
import subprocess
import tempfile

_UI = _KOK / "ui"
_ESBUILD = _UI / "node_modules/.bin/esbuild"


def _js_cekirdek(kod: str):
    """`filoOku.ts`i esbuild ile paketleyip node'da ÇALIŞTIRIR; `kod` son ifadeyi JSON basar.

    Neden esbuild: `filoOku.ts` TypeScript ve `../kanban/oku`yu ithal ediyor — node onu tek
    başına çözemez. Deponun KENDİ araç zinciri kullanılıyor (vite'ın esbuild'i), yani testte
    koşan kod üretimde koşanla aynı dönüşümden geçiyor."""
    node = shutil.which("node")
    if node is None or not _ESBUILD.exists():
        pytest.skip("node ya da esbuild yok — saf çekirdek DAVRANIŞI ölçülemedi (GEÇTİ DEĞİL)")
    with tempfile.TemporaryDirectory() as d:
        paket = Path(d) / "filoOku.mjs"
        yap = subprocess.run(
            [str(_ESBUILD), "src/pano/yuzeyler/ajan/filoOku.ts", "--bundle", "--format=esm",
             "--platform=node", f"--outfile={paket}"],
            cwd=_UI, capture_output=True, text=True)
        assert yap.returncode == 0, f"esbuild düştü:\n{yap.stderr}"
        surucu = Path(d) / "kos.mjs"
        surucu.write_text(
            f'import * as F from "{paket.as_posix()}";\n'
            f"console.log(JSON.stringify({kod}));\n", encoding="utf-8")
        r = subprocess.run([node, str(surucu)], capture_output=True, text=True)
        assert r.returncode == 0, f"node hatası:\n{r.stderr}"
        return json.loads(r.stdout)


def _sahte_ajanlar(*adlar: str) -> str:
    """`aktifAnahtar`ın okuduğu TEK alan `anahtar` — sahte kayıt onu taşır."""
    return json.dumps([{"anahtar": a} for a in adlar])


def test_T2j_saf_cekirdek_KOSULABILIYOR():
    """POZİTİF KONTROL (v152 disiplini): düzenek gerçekten çalışıyor mu?

    Bu olmadan aşağıdaki çiviler, `_js_cekirdek` sessizce boş/aynı şeyi döndürse bile yeşil
    kalabilirdi — "davranışı ölçtüm" cümlesi vakumda doğru olurdu."""
    assert _js_cekirdek('F.aktifAnahtar(%s, null)' % _sahte_ajanlar("bot:sef")) == "bot:sef"
    assert _js_cekirdek("F.aktifAnahtar([], null)") is None, (
        "boş roster'da anahtar UYDURULUYOR — çağıran boş-durumu ayrı çizemez")


def test_T2k_BAYAT_sekme_anahtari_sessiz_bos_panel_URETMIYOR():
    """ROSTER-DEĞİŞİMİ SENARYOSU (inceleme B1) — DAVRANIŞ koşuluyor, kaynak metni değil.

    Operatör `bekci`yi seçer, "Tazele"ye basar, roster değişir (profil silindi/eklendi ya da o
    an ölçülemedi). Bayat anahtar hiçbir sekmeyle eşleşmezse Radix HİÇBİR panel çizmez: ekran
    sessizce boşalır — ne hata, ne 'ölçülemedi' kutusu, ne iz."""
    once = _sahte_ajanlar("bot:bekci", "bot:sef", "ana:hermes")
    sonra = _sahte_ajanlar("bot:sef", "bot:karne", "ana:hermes")

    # (a) GEÇERLİ seçim KORUNUR — düzeltme, çalışan seçimi ezmemeli
    assert _js_cekirdek('F.aktifAnahtar(%s, "bot:bekci")' % once) == "bot:bekci"

    # (b) BAYAT seçim İLK GEÇERLİYE düşer — asıl hüküm
    assert _js_cekirdek('F.aktifAnahtar(%s, "bot:bekci")' % sonra) == "bot:sef", (
        "roster değiştikten sonra bayat anahtar hâlâ dönüyor — panel SESSİZCE boşalır")

    # (c) hiç seçim yokken ilk ajan
    assert _js_cekirdek("F.aktifAnahtar(%s, null)" % sonra) == "bot:sef"

    # (d) KİMLİK ÇİFTİ korunuyor: aynı `ad`, farklı `tur` AYRI anahtarlardır ve biri ötekinin
    #     yerine geçmez (T1'in `(ad, tur)` uyarısı — bir profil `hermes` adını taşıyabilir)
    cift = _sahte_ajanlar("bot:hermes", "ana:hermes")
    assert _js_cekirdek('F.aktifAnahtar(%s, "ana:hermes")' % cift) == "ana:hermes"


def test_T2l_ajanlar_NULL_dalinda_UCUN_HATASI_ekranda(yuzey):
    """B2 — "neden ekranda durur" kuralının tek istisnası kapandı.

    İKİ CÜMLE DE TAŞINIR: şeklin tanınmadığı BİZİM hükmümüz, `hata` UCUN hükmü. Birini ötekinin
    yerine koymak (`yuk.hata ?? taban`) hangi kaynağın düştüğünü ya da şeklin bozulduğunu
    kaybettirirdi."""
    bos = _js_cekirdek('F.ajanListesiNedeni({"hata": null})')
    dolu = _js_cekirdek(
        'F.ajanListesiNedeni({"hata": "bot roster\'ı ÖLÇÜLEMEDİ (PermissionError)"})')
    assert "dizi değil" in bos, "şekil hükmü kayboldu"
    assert "PermissionError" in dolu, (
        "ucun kendi `hata`sı ekrana ulaşmıyor — operatör hangi kaynağın düştüğünü göremez")
    assert "dizi değil" in dolu, "ucun hatası BİZİM hükmümüzün yerine geçti; ikisi ayrı iddiadır"

    # ve dal bunu GERÇEKTEN kullanıyor + kabuğu (hüküm şeridi + kaynak kartı) çiziyor
    b = yuzey["bilesen"]
    dal = b[b.index("if (ajanlar === null)"):b.index("const aktif =")]
    assert "ajanListesiNedeni(yuk)" in dal, "sabit metin geri gelmiş — ucun hatası yine yutuluyor"
    for bilesen in ("<HukumSeridi", "<KaynakKarti"):
        assert bilesen in dal, (
            f"`ajanlar: null` dalı {bilesen} çizmiyor — 'hangi defter okunamadı' sorusunun "
            "cevabı tam da bu dalda gerekli")
