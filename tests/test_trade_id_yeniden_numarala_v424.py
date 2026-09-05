"""test_trade_id_yeniden_numarala_v424.py — TSK-150(b): 16 çift işlem kimliğinin yeniden
numaralanması ÖLÇÜLÜR (`ops/trade_id_yeniden_numarala.py`).

BAĞLAM: `storage.py` `_COLS[TRADES]` şerhinin ölçtüğü hâl (TSK-150(a)) — canlı işlem defterinde
`trades.id` (`T%05d`) İLERİ YÖNLÜ tekildir ama GEÇMİŞTE yazılmış 16 çift zaten vardır (A1 ölçümü,
2026-09-05: 901 satır / 885 tekil / 16 çift, T00096…T00111 aralığı). Operatör kararı: "Yeniden
numarala, eşleme defteriyle." Bu dosya betiğin YAPTIĞINDAN çok YAPMADIĞINI sınar — CANLI DEFTERE
YAZAN bir aracın en tehlikeli hatası sessiz/yanlış yazımdır.

Betik `meridian` paketini HİÇ İTHAL ETMEZ (izolasyon — betiğin kendi başlığında gerekçeli); bu
testler de bu yüzden SAF `sqlite3` ile tmp dosya kurar, `sandbox_state`/`store` KULLANMAZ —
`--db` doğrudan bir dosya yoluna işaret eder ve canlı `state/`e hiçbir yazım YOKTUR.

K1  kuru koşum (varsayılan): DB bit-bit DEĞİŞMEZ, plan doğru (tohum korunur, canlı seq sırasıyla
    max+1'den ardışık numara alır), rc 0
K1b MUTASYON-1 hedefi: `plan_olustur` tohum yerine CANLI'yı korursa (küçük seq yerine büyük seq)
    kırmızı — doğrudan `plan_olustur` birim testi
K2  `--uygula`: yedek dosyası VAR ve AÇILIYOR; satır sayısı sabit; tekil id == satır sayısı;
    tohum satırları byte-eşit; eşleme defteri 3 satır; ardından `--kontrol` rc 0
K3  MUTASYON-2 hedefi: doğrulama başarısızlığı (enjekte edilen çakışan plan) → ROLLBACK, DB
    (uygulama ÖNCESİYLE) bit-bit aynı, ok=False — doğrudan `uygula_plan` birim testi
K3b uçtan uca: `max_trade_num` sahte-düşük dönerse (gerçek bir hesap hatası senaryosu) CLI
    `--uygula` da aynı şekilde reddeder/geri alır, rc 1
K4  `extra_json` içinde `"id"` VARSA güncellenir; YOKSA dokunulmaz (iki test)
K5  idempotent: ikinci `--uygula` "çift yok" der, DB değişmez, eşleme defterine satır EKLENMEZ
K6  gerçek şema uyumu: `meridian.storage` DDL'iyle kurulmuş bir DB'de de aynı sözleşme geçerli
K7  `--kontrol`: eşleme dosyası yokken (0 çift) TUTARLI; bozulmuş bir eşleme kaydıyla TUTARSIZ
"""
from __future__ import annotations

import json
import pathlib
import sqlite3

import pytest

from tests.conftest import betikten_modul_yukle

BETIK = pathlib.Path(__file__).resolve().parents[1] / "ops" / "trade_id_yeniden_numarala.py"


def _mod():
    assert BETIK.exists(), f"betik YOK: {BETIK}"
    return betikten_modul_yukle(BETIK, "trade_id_yeniden_numarala")


# ---- SENTETİK DB KURULUMU (minimal tablo — brief'in izin verdiği ikinci biçim) -------------------
_MINIMAL_DDL = """
CREATE TABLE trades (
    seq INTEGER PRIMARY KEY,
    id TEXT,
    plan_id TEXT,
    ticker TEXT,
    ts_open TEXT,
    extra_json TEXT
)
"""


def _minimal_db(tmp_path, satirlar: list[dict]) -> pathlib.Path:
    """`satirlar`: `{seq, id, plan_id, ticker, ts_open, extra_json=None}` sözlükleri."""
    yol = tmp_path / "state" / "meridian.db"
    yol.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(yol))
    try:
        conn.execute(_MINIMAL_DDL)
        for r in satirlar:
            conn.execute(
                "INSERT INTO trades (seq, id, plan_id, ticker, ts_open, extra_json) VALUES (?,?,?,?,?,?)",
                (r["seq"], r["id"], r.get("plan_id"), r.get("ticker"), r.get("ts_open"),
                 r.get("extra_json")))
        conn.commit()
    finally:
        conn.close()
    return yol


def _oku_tum(db_yolu: pathlib.Path) -> list[dict]:
    conn = sqlite3.connect(str(db_yolu))
    try:
        cur = conn.execute("SELECT * FROM trades ORDER BY seq")
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def _dosya_bayt(yol: pathlib.Path) -> bytes:
    return yol.read_bytes()


# ---- SABİT SENTETİK KESİT: 3 çift + 2 tekil (brief'in K1 senaryosu) ------------------------------
# Çiftler: id="T00010" (tohum seq=1, canlı seq=10), id="T00011" (tohum seq=2, canlı seq=11),
# id="T00012" (tohum seq=3, canlı seq=12). Tekiller: id="T00005" (seq=4), id="T00020" (seq=5).
# Mevcut maks numara = 20 (T00020) → yeni numaralar 21'den başlar, CANLI seq sırasıyla (10,11,12).
def _uc_cift_iki_tekil(tmp_path) -> pathlib.Path:
    satirlar = [
        {"seq": 1, "id": "T00010", "plan_id": "P-2023-A", "ticker": "AAPL", "ts_open": "2023-05-01"},
        {"seq": 2, "id": "T00011", "plan_id": "P-2023-B", "ticker": "MSFT", "ts_open": "2023-05-02"},
        {"seq": 3, "id": "T00012", "plan_id": "P-2023-C", "ticker": "NVDA", "ts_open": "2023-05-03"},
        {"seq": 4, "id": "T00005", "plan_id": "P-2023-D", "ticker": "TSLA", "ts_open": "2023-05-04"},
        {"seq": 5, "id": "T00020", "plan_id": "P-2023-E", "ticker": "AMZN", "ts_open": "2023-05-05"},
        {"seq": 10, "id": "T00010", "plan_id": "P-2026-08-A", "ticker": "AAPL", "ts_open": "2026-08-10"},
        {"seq": 11, "id": "T00011", "plan_id": "P-2026-08-B", "ticker": "MSFT", "ts_open": "2026-08-11"},
        {"seq": 12, "id": "T00012", "plan_id": "P-2026-08-C", "ticker": "NVDA", "ts_open": "2026-08-12"},
    ]
    return _minimal_db(tmp_path, satirlar)


# =================================================================================================
# K1 — KURU KOŞU (VARSAYILAN)
# =================================================================================================
def test_k1_kuru_kosu_DB_DEGISMEZ_ve_plan_dogru(tmp_path):
    db = _uc_cift_iki_tekil(tmp_path)
    once = _dosya_bayt(db)
    m = _mod()
    rc = m.main(["--db", str(db)])
    assert rc == 0
    assert _dosya_bayt(db) == once, "KURU KOŞU DB'Yİ DEĞİŞTİRDİ — kuru koşu sözleşmesi kırık"


def test_k1b_varsayilan_davranis_ACIK_kuru_ile_AYNI(tmp_path):
    """`--kuru` bayrağı VARSAYILANLA aynı sonucu vermeli (brief: `--kuru` VARSAYILANDIR)."""
    db1 = _uc_cift_iki_tekil(tmp_path / "a")
    db2 = _uc_cift_iki_tekil(tmp_path / "b")
    m = _mod()
    assert m.main(["--db", str(db1)]) == m.main(["--db", str(db2), "--kuru"]) == 0
    assert _dosya_bayt(db1) == _dosya_bayt(db2)


def test_k1c_plan_tohum_korur_canli_seq_sirasiyla_maks_ustunden(tmp_path):
    db = _uc_cift_iki_tekil(tmp_path)
    conn = sqlite3.connect(str(db))
    try:
        m = _mod()
        rows = m.oku_satirlar(conn)
    finally:
        conn.close()
    plan, ozet = m.plan_olustur(rows)
    assert ozet["cift_id_sayisi"] == 3
    assert ozet["yeniden_numaralanacak"] == 3
    assert ozet["mevcut_maks_numara"] == 20
    assert ozet["tohum_seq"] == [1, 2, 3], "tohum seq'leri (küçük seq) YANLIŞ"
    # CANLI satırlar (seq 10,11,12) seq SIRASIYLA, max+1'den ARDIŞIK numara alır.
    assert [(e["seq"], e["eski_id"], e["yeni_id"]) for e in plan] == [
        (10, "T00010", "T00021"), (11, "T00011", "T00022"), (12, "T00012", "T00023"),
    ]


def test_k1d_kuru_kosu_plani_JSON_ozetle_basar(tmp_path, capsys):
    db = _uc_cift_iki_tekil(tmp_path)
    m = _mod()
    m.main(["--db", str(db)])
    cik = capsys.readouterr().out
    assert "KURU" in cik.upper()
    assert "T00021" in cik and "T00010" in cik, "planın kendisi çıktıda görünmüyor"
    # JSON özetin KENDİSİ de basılıyor (brief: "+ JSON özet"); `json.dumps(indent=1)` ÇOK
    # SATIRLI basar VE iç içe "plan" ögeleri de kendi "{" satırlarını açar — kök nesnenin açılışı
    # tek ayırt edici işarettir: SIFIR girintili tam "{" satırı (iç içe ögeler HER ZAMAN girintili).
    satirlar = cik.splitlines()
    baslangic = max(i for i, s in enumerate(satirlar) if s == "{")
    rapor = json.loads("\n".join(satirlar[baslangic:]))
    assert rapor["yeniden_numaralanacak"] == 3
    assert rapor["mod"] == "kuru"


# =================================================================================================
# K1b — MUTASYON-1: tohum yerine CANLI korunursa kırmızı
# =================================================================================================
def test_k1b_mutasyon1_tohum_yaniligi_YAKALANIR(tmp_path):
    """`plan_olustur` KÜÇÜK seq'i (tohum) korumalı. Bu çivi, uygulama küçük yerine BÜYÜK seq'i
    korusaydı (tohum/canlı ters çevrilse) KIRMIZI olurdu — MUTASYON-1 hedefidir."""
    db = _uc_cift_iki_tekil(tmp_path)
    conn = sqlite3.connect(str(db))
    try:
        m = _mod()
        rows = m.oku_satirlar(conn)
    finally:
        conn.close()
    plan, ozet = m.plan_olustur(rows)
    # Tohum (dokunulmayacak) seq'ler KÜÇÜK olanlardır (1,2,3) — büyükler (10,11,12) DEĞİL.
    assert set(ozet["tohum_seq"]) == {1, 2, 3}
    assert set(e["seq"] for e in plan) == {10, 11, 12}
    # Ters çevrilmiş bir uygulama burada {10,11,12} tohum, {1,2,3} plan derdi — YUKARIDAKİ iki
    # assert TERS çevrilmiş bir implementasyonda KIRMIZI olur.


# =================================================================================================
# K2 — --uygula
# =================================================================================================
def test_k2_uygula_yedek_satir_sayisi_tekillik_tohum_esitligi_eslesme(tmp_path):
    db = _uc_cift_iki_tekil(tmp_path)
    once_satirlar = {r["seq"]: dict(r) for r in _oku_tum(db)}
    once_n = len(once_satirlar)

    m = _mod()
    rc = m.main(["--db", str(db), "--uygula"])
    assert rc == 0

    # (a) yedek dosyası VAR ve AÇILIYOR
    yedekler = sorted(db.parent.glob("meridian.db.*.bak"))
    assert yedekler, "yedek dosyası YOK"
    yedek_conn = sqlite3.connect(str(yedekler[-1]))
    try:
        n_yedek = yedek_conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
        assert n_yedek == once_n, "yedek defterin TAMAMINI taşımıyor"
        # yedek UYGULAMA ÖNCESİ hâli taşımalı (hâlâ çift id var)
        cift_yedek = yedek_conn.execute(
            "SELECT COUNT(*) FROM (SELECT id FROM trades GROUP BY id HAVING COUNT(*)>1)").fetchone()[0]
        assert cift_yedek == 3, "yedek UYGULAMA SONRASI hâli taşıyor gibi görünüyor"
    finally:
        yedek_conn.close()

    sonra = _oku_tum(db)
    # (b) satır sayısı sabit
    assert len(sonra) == once_n
    # (c) tekil id == satır sayısı
    assert len({r["id"] for r in sonra}) == len(sonra)
    # (d) tohum satırları (seq 1,2,3) byte-eşit (tüm kolonlar)
    for seq in (1, 2, 3):
        assert next(r for r in sonra if r["seq"] == seq) == once_satirlar[seq], \
            f"TOHUM satırı (seq={seq}) DEĞİŞTİ"
    # canlı satırlar yeni id aldı
    yeni_idler = {r["seq"]: r["id"] for r in sonra if r["seq"] in (10, 11, 12)}
    assert yeni_idler == {10: "T00021", 11: "T00022", 12: "T00023"}

    # (e) eşleme defteri 3 satır
    eslesme = db.parent / "trade_id_eslesme.jsonl"
    assert eslesme.exists()
    kayitlar = [json.loads(x) for x in eslesme.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(kayitlar) == 3
    for k in kayitlar:
        assert set(k) >= {"seq", "eski_id", "yeni_id", "plan_id", "ticker", "ts_open",
                          "uygulandi_at", "betik"}
        assert k["betik"] == "ops/trade_id_yeniden_numarala.py"

    # (f) ardından --kontrol rc 0
    rc_kontrol = m.main(["--db", str(db), "--kontrol"])
    assert rc_kontrol == 0


def test_k2b_uygula_worker_kapisi_YOK_dokumante(tmp_path):
    """Brief madde 4: betik `state/`e karşı bir kilit/healthz kontrolü YAPMAZ — bu bilinçli bir
    tasarım kararıdır ve bu test onu ADIYLA sabitler (yarın sessizce bir kapı eklenip
    davranış değişirse bu test onu FARK EDER)."""
    db = _uc_cift_iki_tekil(tmp_path)
    m = _mod()
    assert not hasattr(m, "_worker_running"), (
        "betik bir worker-kapısı fonksiyonu kazandı ama docstring hâlâ 'kapı YOK' diyor — "
        "ikisi ayrıştı, dokümantasyon güncellenmeli")
    assert m.main(["--db", str(db), "--uygula"]) == 0


# =================================================================================================
# K3 — MUTASYON-2: doğrulama başarısızlığı → ROLLBACK
# =================================================================================================
def test_k3_mutasyon2_cakisan_plan_ROLLBACK_edilir(tmp_path):
    """`uygula_plan`e DOĞRUDAN kasıtlı ÇAKIŞAN bir plan verilir (seq=10'a, seq=4'ün MEVCUT id'si
    'T00005' atanır) — `plan_olustur`un kendi ön-denetimini BİLEREK ATLAR, yalnız uygulama+
    doğrulama+rollback KATMANINI sınar. ROLLBACK kaldırılırsa (ya da hiç çağrılmazsa) seq=10'un
    id'si çağrı SONRASINDA 'T00005' olarak KALIR ve bu test KIRMIZI olur — MUTASYON-2 hedefidir."""
    db = _uc_cift_iki_tekil(tmp_path)
    once_bayt = _dosya_bayt(db)
    once_satirlar = {r["seq"]: dict(r) for r in _oku_tum(db)}

    m = _mod()
    conn = sqlite3.connect(str(db))
    try:
        kotu_plan = [{"seq": 10, "eski_id": "T00010", "yeni_id": "T00005",  # T00005 (seq=4) ile ÇAKIŞIR
                     "plan_id": "P-x", "ticker": "AAPL", "ts_open": "2026-08-10"}]
        once = m._snapshot(conn, tohum_seq=[1, 2, 3])
        sonuc = m.uygula_plan(conn, kotu_plan, once)
    finally:
        conn.close()

    assert sonuc["ok"] is False
    assert sonuc["hatalar"], "çakışma HATA ÜRETMEDİ — doğrulama kör"
    assert any("tekillik" in h for h in sonuc["hatalar"])

    # DB, ÇAĞRI ÖNCESİYLE bit-bit aynı (dosya düzeyinde VE satır düzeyinde).
    assert _dosya_bayt(db) == once_bayt, "ROLLBACK sonrası DB dosyası DEĞİŞTİ"
    sonra_satirlar = {r["seq"]: dict(r) for r in _oku_tum(db)}
    assert sonra_satirlar == once_satirlar, "ROLLBACK sonrası satırlar DEĞİŞTİ"


def test_k3b_ucdaneuca_sahte_dusuk_maks_CLI_uzerinden_reddedilir(tmp_path, monkeypatch):
    """Gerçekçi hata senaryosu: `max_trade_num` (bir nedenle) OLMASI GEREKENDEN düşük dönerse,
    üretilecek `yeni_id` mevcut bir id ile çakışır. Bu, `plan_olustur`un KENDİ ön-denetiminde
    (`ValueError`) yakalanır — CLI bunu rc=1 ile raporlar ve DB'ye TEK BAYT yazılmaz.

    Sahte maks BİLEREK 4 seçildi (gerçeği: 20): sonraki numara 5'ten başlar ve mevcut TEKİL satır
    `T00005` (seq=4) ile ÇARPIŞIR — 0 gibi rastgele düşük bir değer hiçbir mevcut id ile
    çarpışmayabilirdi ve testi SESSİZCE anlamsızlaştırırdı."""
    db = _uc_cift_iki_tekil(tmp_path)
    once = _dosya_bayt(db)
    m = _mod()
    monkeypatch.setattr(m, "max_trade_num", lambda rows: 4)   # OLMASI GEREKEN 20 yerine 4
    rc = m.main(["--db", str(db), "--uygula"])
    assert rc == 1
    assert _dosya_bayt(db) == once, "plan kurulamadığı hâlde DB'ye yazıldı"


# =================================================================================================
# K4 — extra_json içinde "id"
# =================================================================================================
def test_k4a_extra_json_icinde_id_VARSA_guncellenir(tmp_path):
    satirlar = [
        {"seq": 1, "id": "T00010", "plan_id": "P-2023-A"},
        {"seq": 10, "id": "T00010", "plan_id": "P-2026-A",
         "extra_json": json.dumps({"id": "T00010", "not": "eski kopya"})},
    ]
    db = _minimal_db(tmp_path, satirlar)
    m = _mod()
    assert m.main(["--db", str(db), "--uygula"]) == 0
    sonra = {r["seq"]: r for r in _oku_tum(db)}
    yuk = json.loads(sonra[10]["extra_json"])
    # Bu iki satırlık defterde mevcut maks numara 10 ("T00010") — yeni numara 11'den başlar.
    assert yuk["id"] == "T00011", "extra_json içindeki id GÜNCELLENMEDİ"
    assert yuk["not"] == "eski kopya", "extra_json'un GERİ KALANI bozuldu"
    assert sonra[10]["id"] == "T00011"


def test_k4b_extra_json_icinde_id_YOKSA_DOKUNULMAZ(tmp_path):
    satirlar = [
        {"seq": 1, "id": "T00010", "plan_id": "P-2023-A"},
        {"seq": 10, "id": "T00010", "plan_id": "P-2026-A",
         "extra_json": json.dumps({"not": "id alanı yok"})},
    ]
    db = _minimal_db(tmp_path, satirlar)
    once_extra = json.dumps({"not": "id alanı yok"})
    m = _mod()
    assert m.main(["--db", str(db), "--uygula"]) == 0
    sonra = {r["seq"]: r for r in _oku_tum(db)}
    assert sonra[10]["extra_json"] == once_extra, "id alanı YOKKEN extra_json yine de değişti"
    assert sonra[10]["id"] == "T00011"


# =================================================================================================
# K5 — idempotent
# =================================================================================================
def test_k5_ikinci_uygula_cift_yok_der_DB_DEGISMEZ_eslesme_BUYUMEZ(tmp_path):
    db = _uc_cift_iki_tekil(tmp_path)
    m = _mod()
    assert m.main(["--db", str(db), "--uygula"]) == 0
    eslesme = db.parent / "trade_id_eslesme.jsonl"
    once_eslesme = eslesme.read_text(encoding="utf-8")
    once_bayt = _dosya_bayt(db)

    rc2 = m.main(["--db", str(db), "--uygula"])
    assert rc2 == 0
    assert _dosya_bayt(db) == once_bayt, "ikinci --uygula DB'yi değiştirdi"
    assert eslesme.read_text(encoding="utf-8") == once_eslesme, "ikinci --uygula eşleme defterine satır EKLEDİ"


def test_k5b_ikinci_uygula_cift_yok_capsys(tmp_path, capsys):
    db = _uc_cift_iki_tekil(tmp_path)
    m = _mod()
    m.main(["--db", str(db), "--uygula"])
    capsys.readouterr()
    m.main(["--db", str(db), "--uygula"])
    cik = capsys.readouterr().out
    assert "YOK" in cik.upper() or "yapılacak bir şey yok" in cik


# =================================================================================================
# K6 — GERÇEK ŞEMA (meridian.storage DDL) UYUMU
# =================================================================================================
def test_k6_gercek_storage_semasiyla_da_calisir(tmp_path):
    """Brief: tmp DB `meridian/storage.py` DDL'i kullanılarak da kurulabilir. Bu test betiğin
    minimal test tablosuna GİZLİCE bağlı KALMADIĞINI (yalnız beş kolonu OKUDUĞUNU, `SELECT *`
    yapmadığını) 30+ kolonlu GERÇEK şemaya karşı doğrular."""
    from meridian import storage
    yol = tmp_path / "state" / "meridian.db"
    yol.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(yol))
    # `storage.apply_schema` `row["v"]` gibi İSİMLE erişir (bkz. `storage._dict_row`) —
    # `storage.connect()`i ATLAYIP kendi bağlantımızı kurduğumuz için row_factory'yi BİZ kurarız.
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("BEGIN")
        storage.apply_schema(conn)
        conn.execute("COMMIT")
        # TOHUM + CANLI çift: yalnız id/plan_id/ticker/ts_open dolduruluyor, GERİ KALAN kolonlar
        # NULL kalır — gerçek defterde de birçok alan opsiyoneldir.
        conn.execute("INSERT INTO trades (seq, id, plan_id, ticker, ts_open) VALUES "
                     "(92, 'T00096', 'P-2023-X', 'AAPL', '2023-05-10')")
        conn.execute("INSERT INTO trades (seq, id, plan_id, ticker, ts_open) VALUES "
                     "(886, 'T00096', 'P-2026-08-05-X', 'AAPL', '2026-08-05')")
        conn.execute("INSERT INTO trades (seq, id, plan_id, ticker, ts_open) VALUES "
                     "(887, 'T00900', 'P-2026-tekil', 'MSFT', '2026-08-06')")
        conn.commit()
    finally:
        conn.close()

    m = _mod()
    assert m.main(["--db", str(yol)]) == 0          # kuru koşu geçmeli
    assert m.main(["--db", str(yol), "--uygula"]) == 0

    conn = sqlite3.connect(str(yol))
    try:
        cur = conn.execute("SELECT seq, id FROM trades ORDER BY seq")
        satirlar = dict(cur.fetchall())
    finally:
        conn.close()
    assert satirlar[92] == "T00096", "TOHUM (seq=92) değişti"
    assert satirlar[886] == "T00901", "CANLI satır (seq=886) beklenen yeni numarayı ALMADI"
    assert satirlar[887] == "T00900", "tekil satıra DOKUNULDU"
    assert m.main(["--db", str(yol), "--kontrol"]) == 0


# =================================================================================================
# K7 — --kontrol
# =================================================================================================
def test_k7a_kontrol_cift_yokken_eslesme_dosyasi_da_yokken_TUTARLI(tmp_path):
    satirlar = [{"seq": 1, "id": "T00001"}, {"seq": 2, "id": "T00002"}]
    db = _minimal_db(tmp_path, satirlar)
    m = _mod()
    rc = m.main(["--db", str(db), "--kontrol"])
    assert rc == 0


def test_k7b_kontrol_bozuk_eslesme_kaydiyla_TUTARSIZ(tmp_path):
    db = _uc_cift_iki_tekil(tmp_path)
    m = _mod()
    m.main(["--db", str(db), "--uygula"])
    eslesme = db.parent / "trade_id_eslesme.jsonl"
    # Bir kaydı BOZ: yeni_id'yi DB'de hiç olmayan bir değere çevir.
    satirlar = [json.loads(x) for x in eslesme.read_text(encoding="utf-8").splitlines() if x.strip()]
    satirlar[0]["yeni_id"] = "T99999"
    eslesme.write_text("\n".join(json.dumps(s) for s in satirlar) + "\n", encoding="utf-8")
    rc = m.main(["--db", str(db), "--kontrol"])
    assert rc == 1


def test_k7c_uygula_uygula_kontrol_birlikte_KULLANIM_HATASI(tmp_path):
    db = _uc_cift_iki_tekil(tmp_path)
    m = _mod()
    rc = m.main(["--db", str(db), "--uygula", "--kontrol"])
    assert rc == 2


def test_k7d_db_yok_KULLANIM_HATASI(tmp_path):
    m = _mod()
    rc = m.main(["--db", str(tmp_path / "yok.db")])
    assert rc == 2
