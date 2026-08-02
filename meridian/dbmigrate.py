"""dbmigrate.py — DOSYA DEFTERİ → SQLite, PARİTE KANITIYLA (WP-H/H9, Kademe A4).

NE YAPAR. Altı varlığı (`trades.jsonl`, `trade_plans.jsonl`, `scoreboard.json`, `portfolio.json`,
`equity_curve.json`, `shadow_books.json`) `state/meridian.db`ye taşır. İLERİ YÖNLÜ ve İDEMPOTENT:
ikinci koşu hiçbir şeyi tekrarlamaz, aynı raporu üretir.

KURU KOŞU VARSAYILANDIR. Veri taşıyan bir aracın varsayılanı yazmak olamaz (`barrepair` /
`ledgerstamp` ile aynı kural). `--uygula` olmadan tek bayt yazılmaz; kuru koşu ne taşınacağını
SAYAR ve KAYNAK PARİTE-DİGESTİNİ basar.

PARİTE KANITI ZORUNLUDUR — İDDİA DEĞİL ÖLÇÜM. Her varlık için:

    JSON kaynak → DB'ye yaz → DB'den TEKRAR oku → yeniden serileştir → normalize digest

İki digest EŞİT DEĞİLSE migrasyon BAŞARISIZ sayılır ve TAMAMI geri alınır (altı varlık TEK
transaction'dadır — yarısı taşınmış bir defter, taşınmamış bir defterden daha tehlikelidir).
Digest anahtar sırasına duyarsızdır (`sort_keys`) ama DEĞERE ve TİPE duyarlıdır: SQLite'ın tip
afinitesi bir int'i float'a çevirseydi (60 → 60.0) bu ölçüm onu YAKALAR. Bu yüzden `storage`
tip uyuşmazlığında alanı ayrıca `extra_json`a yazar ve okumada `extra_json` kazanır.

KAYNAK DOSYALAR SİLİNMEZ. Taşıma sonrası aynı dizinde `.migrated` son-ekiyle bırakılır. Silmek,
geri dönüşü olan bir adımı geri dönüşü olmayan bir adıma çevirirdi; `MERIDIAN_DB=off` acil
anahtarının anlamlı olması için dosyaların DURMASI gerekir. (Adı değiştirilir, çünkü aynı anda
İKİ okunabilir gerçek kaynağı bırakmak, hangisinin doğru olduğunu belirsizleştirirdi.)

CANLI WORKER KOŞARKEN YAZMA. `ledgerstamp`/`barrepair` ile AYNI desen ve AYNI ölçüm fonksiyonu:
canlı süreç görülürse `--uygula` REDDEDİLİR (`--zorla` ile ezilir).

KULLANIM:
    python -m meridian.dbmigrate                 # kuru koşu — sayım + parite digestleri
    python -m meridian.dbmigrate --json          # aynı rapor, makine-okunur
    python -m meridian.dbmigrate --uygula        # TAŞI (worker durdurulmuş olmalı)
    python -m meridian.dbmigrate --durum         # yalnız DB durumu (şema sürümü, varlık sayaçları)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

from . import config, storage

MIGRATED_SUFFIX = ".migrated"
# Başarısız migrasyondan sonra kenara alınan DB'nin son eki: `meridian.db.failed-<ts>` (C4).
FAILED_SUFFIX = ".failed-"


# ---- KAYNAK OKUMA (store YÖNLENDİRMESİNİ ATLAR) ------------------------------------------------
# NEDEN DOĞRUDAN DOSYA: `store.read_jsonl` DB varsa DB'den okur. Migrasyonun kaynağı DOSYADIR;
# store üzerinden okumak, taşımanın ikinci koşuda kendi çıktısını kaynak sanmasına yol açardı.
def source_path(name: str) -> Path:
    return Path(config.STATE) / name


def read_source(name: str) -> dict:
    """Kaynağı HAM oku. Dönüş: {present, payload, n, bozuk_satir}."""
    p = source_path(name)
    kind = storage.kind_of(name)
    if not p.exists():
        return {"present": False, "payload": None, "n": 0, "bozuk_satir": 0}
    if kind == "rows":
        rows, bad = [], 0
        with open(p) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:  # sessiz-yutma: SESSİZ DEĞİL — sayaç `bozuk_satir` olarak RAPORA çıkar ve kuru koşuda operatörün önüne gelir; `store.read_jsonl` de aynı satırı atlıyordu, yani migrasyon defterin BUGÜN OKUNAN hâlini taşır
                    bad += 1
        return {"present": True, "payload": rows, "n": len(rows), "bozuk_satir": bad}
    try:
        with open(p) as f:
            doc = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return {"present": True, "payload": None, "n": 0, "bozuk_satir": 0,
                "hata": f"{type(e).__name__}: {e}"}
    n = len((doc or {}).get(storage.POINTS_KEY) or []) if kind == "series" else 1
    return {"present": True, "payload": doc, "n": n, "bozuk_satir": 0}


# ---- NORMALİZE DİGEST --------------------------------------------------------------------------
def normalize(payload: Any) -> Any:
    """Digest öncesi normalizasyon. Anahtar sırası ve JSON metin biçimi ELENİR; değer ve TİP KALIR.

    Listeler SIRALANMAZ: defterin satır sırası anlamlıdır (`trades.jsonl` kronolojiktir ve
    `ledgerstamp.classify` sırayı okur). Sıralamak, taşımanın satırları karıştırmasını görünmez
    kılardı — yani ölçümü ölçtüğü şeye kör yapardı."""
    if isinstance(payload, dict):
        return {k: normalize(v) for k, v in sorted(payload.items())}
    if isinstance(payload, (list, tuple)):
        return [normalize(v) for v in payload]
    # TİP KORUNUR: `json.dumps` zaten `true` ile `1`i, `60` ile `60.0`ı farklı metne çevirir —
    # yani digest tip değişimine DUYARLIDIR. Ek bir sarmalayıcı gerekmez ve olsaydı digesti
    # okunamaz yapardı.
    return payload


def digest(payload: Any) -> str:
    blob = json.dumps(normalize(payload), sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]


# ---- PLAN (kuru koşu) --------------------------------------------------------------------------
def plan() -> dict:
    """Ne taşınacak? Hiçbir bayt yazılmaz, DB açılmaz (yoksa yaratılmaz)."""
    db = storage.db_path()
    db_var = db.exists()
    varliklar = []
    for name in storage.ENTITIES:
        src = read_source(name)
        rec = {"varlik": name, "tablo": storage.table_of(name), "tur": storage.kind_of(name),
               "kaynak_var": src["present"], "n": src["n"], "bozuk_satir": src["bozuk_satir"],
               "kaynak_digest": digest(src["payload"]) if src["present"] else None,
               "arsiv_var": source_path(name).with_name(name + MIGRATED_SUFFIX).exists()}
        if src.get("hata"):
            rec["hata"] = src["hata"]
        varliklar.append(rec)
    out = {"db": str(db), "db_var": db_var, "sema_surumu": None, "varliklar": varliklar,
           "toplam_satir": sum(v["n"] for v in varliklar),
           "tasinacak": sum(1 for v in varliklar if v["kaynak_var"])}
    if db_var:
        c = storage.connect(db)
        out["sema_surumu"] = storage.schema_version(c)
        out["db_durumu"] = db_state()
    return out


def db_state() -> list[dict]:
    """DB'deki varlıkların CANLI sayaçları (iddia değil, tablodan sayım).

    ŞEMA KURMAZ (C4, 2026-08-02). Eskiden `connect(create=True)` + `ensure_schema(c)` çağırıyordu;
    yani SALT-OKUMA diye çağrılan bir rapor, DB dosyasını yaratıp şemayı KALICI COMMIT ediyordu.
    İki sonucu vardı: (1) `plan()` "hiçbir bayt yazılmaz, DB açılmaz" diye beyan ederken bu yoldan
    geçtiğinde tam tersini yapıyordu, (2) `apply()`in şemayı transaction'ın İÇİNE alan düzeltmesi
    aynı kapıdan delinirdi (plan zaten şemayı dışarıda COMMIT etmiş olurdu). Şema yoksa dönüş BOŞ
    LİSTEdir — "DB henüz devrede değil" hükmünü uydurulmuş sıfır sayaçlarla karıştırmamak için."""
    if not storage.db_path().exists() or storage.schema_version() is None:
        return []
    c = storage.connect()
    rows = []
    for name in storage.ENTITIES:
        m = storage.meta(name) or {}
        payload = storage.read_entity(name)
        n = (len(payload) if isinstance(payload, list)
             else len((payload or {}).get(storage.POINTS_KEY) or [])
             if storage.kind_of(name) == "series" else (1 if payload is not None else 0))
        rows.append({"varlik": name, "present": bool(m.get("present")), "n": n,
                     "rev": m.get("rev"), "migrated_at": m.get("migrated_at"),
                     "db_digest": digest(payload) if payload is not None else None,
                     "kaynak_digest": m.get("source_digest")})
    return rows


# ---- BAŞARISIZ MİGRASYONDAN SONRA: DB'Yİ KENARA AL ---------------------------------------------
def _karantina(rapor: dict, db_yeni: bool, sebep: str) -> None:
    """Bu koşuda DOĞAN DB'yi `meridian.db.failed-<ts>` diye kenara al ve BEYAN ET (C4, 2026-08-02).

    NEDEN GEREKLİ. Şema artık migrasyon transaction'ının içinde kurulduğu için geri alma onu da
    götürür ve `active()` zaten False döner — ama geride ŞEMASIZ bir `meridian.db` DOSYASI kalır.
    O dosya iki yerde yanlış okunur: `serve.sh`in `[ ! -s state/meridian.db ]` kapısı ("DB var,
    tohum koşmasın") ve operatörün gözü. Kenara almak, hata yolunu tek bir cümleye indirger:
    başarısız migrasyondan sonra DB YOKTUR, defterler DOSYADAN okunur.

    NEDEN YALNIZ 'YENİ DOĞAN' DB. Dosya bu koşudan ÖNCE de varsa içinde DAHA ÖNCE taşınmış
    (`migrated_at` damgalı) defterler olabilir; onu kenara almak, hata yolunu veri kaybına
    çevirirdi — yani düzeltmenin kapatmaya çalıştığı sınıfın daha kötüsünü üretirdi. O hâlde
    hüküm rapora yazılır, dosyaya dokunulmaz.

    `close_connections()` HER İKİ DALDA. Açık bir bağlantı (a) yeniden adlandırılmış dosyaya WAL
    geri yazabilir, (b) `_SCHEMA_OK` önbelleğini diskteki gerçeğin ötesinde tutar — önbellek "şema
    tamam" derken şema geri alınmış olabilir. `close_connections` ikisini birden temizler."""
    db = storage.db_path()
    kayit: dict = {"yapildi": False, "db_yeni": db_yeni, "sebep": sebep,
                   "hedef": None, "tasinan": []}
    try:
        storage.close_connections()
    except Exception as e:  # sessiz-yutma: sonuç KAYDA GEÇİYOR (kapatma_hatasi raporda) — kapatılamayan bir tanıtıcı, dosyayı kenara alma kararını geri aldıramaz ve süreç sonu onu toplar
        kayit["kapatma_hatasi"] = f"{type(e).__name__}: {e}"
    if not db_yeni:
        kayit["not"] = ("DB bu koşudan ÖNCE de vardı — daha önce taşınmış defterler içerebilir, "
                        "kenara almak veri kaybı olurdu. Şema bu koşuda transaction İÇİNDE "
                        "kurulduğu için geri alma yalnız bu koşunun eklediğini götürdü.")
    else:
        ts = time.strftime("%Y%m%d-%H%M%S")
        hedef = db.with_name(db.name + FAILED_SUFFIX + ts)
        # `-wal`/`-shm` de taşınır: ana dosya adı değişip yan dosyalar `meridian.db-wal` adıyla
        # kalsaydı, İLERİDE doğacak taze bir `meridian.db` bayat bir WAL'la eşleşirdi.
        for ek in ("", "-wal", "-shm"):
            kaynak = db.with_name(db.name + ek)
            if not kaynak.exists():
                continue
            try:
                kaynak.rename(hedef.with_name(hedef.name + ek))
                kayit["tasinan"].append(hedef.name + ek)
            except OSError as e:  # sessiz-yutma: sonuç KAYDA GEÇİYOR (tasima_hatasi raporda + obs olayı) — dosya taşınamasa bile şema geri alındığı için `active()` yine False; operatör dosyayı elle kaldırır
                kayit["tasima_hatasi"] = f"{type(e).__name__}: {e}"
        kayit["yapildi"] = bool(kayit["tasinan"])
        kayit["hedef"] = str(hedef)
    kayit["aktif"] = storage.active(storage.TRADES)
    # BEYAN DALDAN TÜRETİLİR, SABİT DEĞİL: `aktif=True` iken "DB devrede değil" yazmak, raporun
    # kendi ölçümüyle çelişen bir cümle olurdu (bu turda kapatılan sınıfın ta kendisi).
    kayit["beyan"] = (
        "başarısız migrasyondan sonra DB DEVREDE DEĞİL — altı defter dosya arka ucundan okunur "
        "(kaynak dosyalar yerinde ve .migrated eki almadı)" if not kayit["aktif"] else
        "DB DEVREDE KALDI — içinde daha önce taşınmış defterler var; bu koşunun taşımaya "
        "çalıştığı varlıklar taşınmadı ve kaynakları .migrated eki almadı")
    rapor["karantina"] = kayit
    try:
        from . import obs
        obs.warn("sqlite_migration_failed_db_quarantined", sebep=sebep, db_yeni=db_yeni,
                 hedef=kayit["hedef"], aktif=kayit["aktif"], detail=kayit["beyan"])
    except Exception:  # sessiz-yutma: kayıt kanalı düştü; karantina kararı DİSKTE zaten uygulandı ve rapora yazıldı — kayıt denemesi onu geri alamaz
        pass


# ---- UYGULA ------------------------------------------------------------------------------------
def apply() -> dict:
    """TEK TRANSACTION + PARİTE KANITI. Digest tutmazsa hiçbir varlık taşınmaz."""
    # DB BU KOŞUDA MI DOĞUYOR? ÖLÇÜM, ilk `connect(create=True)`dan ÖNCE alınır — sonrasında
    # sorulsaydı cevap HER ZAMAN "var" olurdu ve hata yolu, taşınmış defter içeren bir DB'yi de
    # kenara alabilirdi (bkz. `_karantina`).
    db_yeni = not storage.db_path().exists()
    rapor = plan()
    rapor["applied"] = True
    rapor["yazildi"] = False
    rapor["parite"] = []
    rapor["arsivlenen"] = []
    rapor["db_yeni"] = db_yeni

    kaynaklar = {n: read_source(n) for n in storage.ENTITIES}
    c = storage.connect(create=True)

    # `_GUARD` tüm transaction boyunca tutulur: aynı süreçteki başka bir iplik araya bir
    # BEGIN/COMMIT sokarsa transaction'ın atomikliği (ve dolayısıyla geri alma sözü) kalmaz.
    with storage._GUARD:
        c.execute("BEGIN IMMEDIATE")
        try:
            # ŞEMA TRANSACTION'IN İÇİNDE (C4). Eskiden `storage.ensure_schema(c)` BURADAN ÖNCE
            # çağrılıyordu ve kendi COMMIT'ini atıyordu: migrasyon düşse bile şema diskte kalıyor,
            # `active()` True dönüyor ve altı defter SESSİZCE boş okunuyordu. Şema artık aşağıdaki
            # ROLLBACK'lerin kapsamındadır. `onceki` (entity_meta) okuması da bu yüzden içeri alındı
            # — tablo ancak şema kurulduktan sonra vardır.
            storage.apply_schema(c)
            onceki = {n: (storage.meta(n) or {}) for n in storage.ENTITIES}
            tasinan = []
            for name in storage.ENTITIES:
                m = onceki.get(name) or {}
                src = kaynaklar[name]
                if m.get("migrated_at"):
                    rapor["parite"].append({"varlik": name, "durum": "zaten_tasindi",
                                            "kaynak_digest": m.get("source_digest"), "ok": True})
                    continue
                if not src["present"]:
                    rapor["parite"].append({"varlik": name, "durum": "kaynak_yok", "ok": True,
                                            "not": "dosya yok — boş varlık olarak bırakıldı "
                                                   "(uydurulmuş bir belge yazılmadı)"})
                    continue
                if src["payload"] is None:
                    # Dosya VAR ama okunamıyor. Bu bir "yok" hâli DEĞİLDİR ve öyle raporlanamaz:
                    # taşıma yapılmaz, migrasyon BAŞARISIZ sayılır ve operatör önce dosyayı
                    # onarır. Bozuk bir kaynağı sessizce atlamak, defteri kaybetmenin adı olurdu.
                    rapor["parite"].append({"varlik": name, "durum": "KAYNAK_BOZUK", "ok": False,
                                            "hata": src.get("hata")})
                    c.execute("ROLLBACK")
                    rapor["ok"] = False
                    rapor["hata"] = (f"{name} okunamadı ({src.get('hata')}) — hiçbir varlık "
                                     f"taşınmadı. Önce kaynağı onar.")
                    _karantina(rapor, db_yeni, "KAYNAK_BOZUK")
                    return rapor
                kind = storage.kind_of(name)
                if kind == "rows":
                    storage.do_replace_rows(c, name, src["payload"])
                elif kind == "series":
                    storage.do_write_series(c, src["payload"], name)
                else:
                    storage.do_write_doc(c, name, src["payload"])
                tasinan.append(name)

            # PARİTE TURU — hâlâ AÇIK transaction içinde okunur (aynı bağlantı kendi yazımını görür),
            # yani eşleşmezse COMMIT hiç olmaz.
            hatali = []
            for name in tasinan:
                src_d = digest(kaynaklar[name]["payload"])
                db_payload = storage.read_entity(name)
                db_d = digest(db_payload)
                ok = (src_d == db_d)
                rapor["parite"].append({
                    "varlik": name, "durum": "tasindi" if ok else "PARİTE_TUTMADI", "ok": ok,
                    "n_kaynak": kaynaklar[name]["n"],
                    "n_db": (len(db_payload) if isinstance(db_payload, list) else
                             len((db_payload or {}).get(storage.POINTS_KEY) or [])
                             if storage.kind_of(name) == "series" else 1),
                    "kaynak_digest": src_d, "db_digest": db_d})
                if ok:
                    storage.mark_migrated(name, digest=src_d, conn=c)
                else:
                    hatali.append(name)
            if hatali:
                c.execute("ROLLBACK")
                rapor["ok"] = False
                rapor["hata"] = (f"PARİTE TUTMADI: {hatali} — hiçbir varlık taşınmadı (tek "
                                 f"transaction geri alındı). Kaynak dosyalar YERİNDE.")
                _karantina(rapor, db_yeni, "PARİTE_TUTMADI")
                return rapor
            c.execute("COMMIT")
            rapor["yazildi"] = bool(tasinan)
            rapor["tasinan"] = tasinan
        except BaseException as e:
            try:
                c.execute("ROLLBACK")
            except Exception:  # sessiz-yutma: transaction zaten kapanmış olabilir (ör. hata COMMIT'in kendisinde); asıl istisna yukarı çıkmaya devam eder ve rapor onu taşır
                pass
            rapor["ok"] = False
            rapor["hata"] = f"{type(e).__name__}: {e}"
            # BEKLENMEDİK İSTİSNA DA BİR HATA-DÖNÜŞ YOLUDUR: istisna yukarı çıkarken geride
            # yarım doğmuş bir DB bırakmak, iki bilinen hata dalını kapatıp üçüncüsünü açık
            # tutmak olurdu. `rapor` çağırana ulaşmaz (aşağıda `raise` var) — bu yüzden karar
            # obs olayına da yazılır.
            _karantina(rapor, db_yeni, f"istisna:{type(e).__name__}")
            raise

    # ARŞİVLEME COMMIT'TEN SONRA. Sıra bilerek böyledir: dosyalar önce yeniden adlandırılıp
    # sonra transaction düşseydi, ne DB'de ne beklenen adında veri kalırdı.
    for name in rapor.get("tasinan", []):
        p = source_path(name)
        hedef = p.with_name(name + MIGRATED_SUFFIX)
        if p.exists() and not hedef.exists():
            p.rename(hedef)
            rapor["arsivlenen"].append(hedef.name)

    rapor["ok"] = True
    rapor["db_durumu"] = db_state()
    try:
        from . import obs
        obs.warn("sqlite_ledger_migrated", tasinan=len(rapor.get("tasinan", [])),
                 satir=rapor["toplam_satir"], db=str(storage.db_path()),
                 detail="defter çekirdeği SQLite'a taşındı (parite digesti doğrulandı); "
                        "kaynak dosyalar .migrated ekiyle yerinde duruyor")
    except Exception:  # sessiz-yutma: kayıt kanalı düştü; migrasyon COMMIT edildi ve rapor çağırana döndü — kayıt denemesi taşımayı geri alamaz
        pass
    return rapor


def _worker_running() -> bool:
    """Canlı Meridian süreci var mı? `barrepair`in AYNI ölçümü — kopyalanmaz, çağrılır."""
    from .barrepair import _worker_running as _wr
    return _wr()


def _print(rapor: dict) -> None:
    mod = ("UYGULANDI" if rapor.get("yazildi") else
           ("UYGULAMA İSTENDİ ama taşınacak varlık yok" if rapor.get("applied")
            else "KURU KOŞU (hiçbir bayt yazılmadı)"))
    print(f"[dbmigrate] {mod}")
    print(f"  db: {rapor['db']}  (var: {rapor['db_var']}, şema sürümü: {rapor.get('sema_surumu')})")
    print(f"  {'varlık':22s} {'n':>7s}  {'kaynak':>6s}  kaynak_digest")
    for v in rapor["varliklar"]:
        print(f"  {v['varlik']:22s} {v['n']:>7d}  {str(v['kaynak_var']):>6s}  "
              f"{v['kaynak_digest'] or '-'}"
              + (f"  [BOZUK SATIR: {v['bozuk_satir']}]" if v["bozuk_satir"] else "")
              + ("  [arşiv var]" if v["arsiv_var"] else ""))
    print(f"  toplam satır: {rapor['toplam_satir']}, taşınacak varlık: {rapor['tasinacak']}")
    for p in rapor.get("parite") or []:
        isaret = "OK " if p.get("ok") else "!! "
        print(f"   {isaret}{p['varlik']:22s} {p['durum']:16s} "
              f"kaynak={p.get('kaynak_digest') or '-'} db={p.get('db_digest') or '-'}")
    if rapor.get("arsivlenen"):
        print(f"  arşivlenen kaynak: {rapor['arsivlenen']}")
    if rapor.get("hata"):
        print(f"  HATA: {rapor['hata']}")
    k = rapor.get("karantina")
    if k:
        # Hata yolunun DB'ye ne yaptığı operatörün önüne ÇIKAR: "hiçbir varlık taşınmadı" cümlesi
        # tek başına, geride aktif-ama-boş bir DB kalıp kalmadığını söylemiyordu (C4).
        print(f"  KARANTİNA: {'DB kenara alındı' if k.get('yapildi') else 'DB taşınmadı'}"
              f"  (db_yeni={k.get('db_yeni')}, aktif={k.get('aktif')})")
        if k.get("hedef"):
            print(f"    → {k['hedef']}  {k.get('tasinan') or ''}")
        for anahtar in ("not", "kapatma_hatasi", "tasima_hatasi"):
            if k.get(anahtar):
                print(f"    {anahtar}: {k[anahtar]}")
        print(f"    {k.get('beyan')}")
    if not rapor.get("applied"):
        print("  → uygulamak için: python -m meridian.dbmigrate --uygula  "
              "(worker DURDURULMUŞ olmalı)")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m meridian.dbmigrate",
        description="defter çekirdeğini (6 varlık) SQLite'a taşır — parite digesti zorunlu")
    ap.add_argument("--uygula", action="store_true", help="TAŞI (varsayılan: kuru koşu)")
    ap.add_argument("--json", action="store_true", help="raporu JSON olarak bas")
    ap.add_argument("--durum", action="store_true", help="yalnız DB durumunu bas")
    ap.add_argument("--zorla", action="store_true",
                    help="canlı süreç görülse de taşı (riski sen alırsın)")
    a = ap.parse_args(argv)
    if a.durum:
        out = {"db": str(storage.db_path()), "db_var": storage.db_path().exists(),
               "sema_surumu": storage.schema_version() if storage.db_path().exists() else None,
               "aktif": storage.active(storage.TRADES),
               "durum": db_state() if storage.db_path().exists() else []}
        print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
        return 0
    if a.uygula and not a.zorla and _worker_running():
        print("[dbmigrate] REDDEDİLDİ: canlı Meridian süreci görülüyor. Defter taşınırken canlı "
              "yazar olamaz. Önce `./ops/stop-worker.sh`, sonra tekrar dene (ya da --zorla).",
              file=sys.stderr)
        return 2
    rapor = apply() if a.uygula else plan()
    if a.json:
        print(json.dumps(rapor, ensure_ascii=False, indent=1, default=str))
    else:
        _print(rapor)
    return 0 if rapor.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
