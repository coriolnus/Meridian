"""dbmigrate.py — dosya defterlerini SQLite'a parite kanıtıyla taşıyan ve geri alan operatör aracı.

NE YAPAR. `storage.ENTITIES` kaydındaki varlıkları (adlar ve sayı YALNIZ orada yazılıdır) `state/meridian.db`ye
TEK transaction'da taşır; ileri yönlü, idempotent ve ARTIMLIDIR — `migrated_at` damgalı varlık
`zaten_tasindi` diye atlanır, yalnız damgasızlar taşınır (Kademe C: A1'de altısı damgalı, iki öğrenme
defteri ikinci koşuda taşınır; şema 1→2 aynı transaction'da yükselir). KURU KOŞU VARSAYILANDIR: veri
taşıyan bir aracın varsayılanı yazmak olamaz (`barrepair`/`ledgerstamp` ile aynı kural) —
`--uygula` olmadan tek bayt yazılmaz. Parite kanıtı İDDİA DEĞİL ÖLÇÜMDÜR: kaynak → DB'ye yaz →
DB'den tekrar oku → normalize digest; digestler eşit değilse TAMAMI geri alınır (yarısı taşınmış
defter, taşınmamış defterden tehlikelidir) ve bu koşuda DOĞAN DB `.failed-<ts>` ile karantinaya
alınır — şema transaction'ın İÇİNDE kurulduğu için düşen migrasyon geride aktif-ama-boş bir DB
bırakamaz. Digest anahtar sırasına duyarsız, DEĞERE ve TİPE duyarlıdır; listeler SIRALANMAZ
(satır sırası defterin anlamıdır — sıralamak ölçümü ölçtüğü şeye kör yapardı).

KAYNAK DOSYALAR SİLİNMEZ: taşıma sonrası `.migrated` ekiyle yerinde durur — silmek geri dönüşü
olan bir adımı geri dönüşsüz yapardı; iki okunabilir gerçek kaynağı bırakmamak için ad değişir.
Kaynak DOĞRUDAN DOSYADAN okunur (store yönlendirmesi bilinçli atlanır: ikinci koşu kendi
çıktısını kaynak sanmasın). PARİTE TURU DA store'u ATLAR (`storage.read_entity`, aynı bağlantı + açık
transaction): Kademe C'nin varlık kapısı (`storage.active`) damgasız varlığı DOSYAYA yönlendirir — parite
o yoldan okusaydı kaynak dosya kendisiyle kıyaslanır ve kanıt SAHTE yeşil olurdu (v579 çivisi).

GERİ DÖNÜŞ KOLU `--geri-al`DIR, `MERIDIAN_DB=off` DEĞİL (eski "acil anahtar" beyanı YANLIŞLANDI:
anahtarı tek başına çeken operatör taşınmış defterleri BOŞ okur ve ayrışık ikinci bir kitap doğar).
`rollback()` veri silmez, yalnız yeniden adlandırır: DB `.rolledback-<ts>` ile kenara (migrasyon
SONRASI yazımların tek kopyası ondadır; `db_n − dosya_n` farkı + digest paritesi rapora basılır),
`.migrated` arşivleri asıl adlarına döner, kanonik adı işgal eden ayrışık dosya `.ayrisik-<ts>`
ile kenara alınır. BU KİP HEPSİ-YA-HİÇ'TİR — Kademe A+B defterlerini de dosyaya döndürür (çıktı bunu
uyarır). KISITLI GERİ ALMA `--geri-al --varlik a,b` (`rollback_kisitli`, Kademe C tur 2 F1): DB YERİNDE
kalır, yalnız listelenen DAMGA KAPILI varlıkların damgası sökülür ve arşivleri kanonik ada döner — okuma
kapısı onları dosyaya çevirir, tablo satırları kanıt olarak kalır. Canlı worker VEYA öğrenme süreci
(`meridian-learn`) koşarken `--uygula` VE `--geri-al` (iki kip) REDDEDİLİR (`--zorla` ezer).

KULLANIM: `python -m meridian.dbmigrate` (kuru koşu) · `--json` · `--uygula` · `--durum` ·
`--geri-al` [`--varlik a,b`]. Okur/yazar: state/ altındaki kaynak dosyalar + `state/meridian.db`; olaylar obs'a.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from . import config, storage

# TEK KAYNAK `storage`tadır: `active()`in `MERIDIAN_DB=off` beyanı (C5) aynı eki ölçer; iki ayrı
# sabit olsaydı biri değiştiğinde uyarı arşivleri sessizce göremez olurdu.
MIGRATED_SUFFIX = storage.MIGRATED_SUFFIX
# Başarısız migrasyondan sonra kenara alınan DB'nin son eki: `meridian.db.failed-<ts>` (C4).
FAILED_SUFFIX = ".failed-"
# `--geri-al` ile kenara alınan (SAĞLAM, taşınmış defter içeren) DB'nin son eki. `FAILED_SUFFIX`ten
# AYRI: biri "bu DB hiç kurulamadı", diğeri "bu DB çalışıyordu ve içinde migrasyon SONRASI yazımlar
# olabilir". İki hâli tek ada toplamak, operatörün hangisini silebileceğini belirsizleştirirdi.
ROLLEDBACK_SUFFIX = ".rolledback-"
# Geri-al sırasında kanonik adı İŞGAL EDEN dosyanın son eki: `MERIDIAN_DB=off` çekiliyken doğan
# ayrışık ikinci kitap. Üzerine yazılmaz — geri-al bir kurtarma koludur, veri silmez.
DIVERGENT_SUFFIX = ".ayrisik-"


# ---- KAYNAK OKUMA (store YÖNLENDİRMESİNİ ATLAR) ------------------------------------------------
# NEDEN DOĞRUDAN DOSYA: `store.read_jsonl` DB varsa DB'den okur. Migrasyonun kaynağı DOSYADIR;
# store üzerinden okumak, taşımanın ikinci koşuda kendi çıktısını kaynak sanmasına yol açardı.
def source_path(name: str) -> Path:
    """Varlığın KAYNAK dosya yolu (`state/<ad>`) — store yönlendirmesini ATLAR: migrasyonun
    kaynağı her zaman dosyadır, yoksa ikinci koşu kendi çıktısını kaynak sanardı."""
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
    """Yükün parite digesti: `normalize` sonrası kanonik JSON'ın sha256'sının ilk 32 karakteri.
    Anahtar sırası/biçim elenir, DEĞER ve TİP korunur — kaynak ile DB'nin aynılığı bununla sınanır."""
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
           "toplam_satir": sum(v["n"] for v in varliklar)}
    damgali: set = set()
    if db_var:
        c = storage.connect(db)
        out["sema_surumu"] = storage.schema_version(c)
        out["db_durumu"] = db_state()
        damgali = {d["varlik"] for d in out["db_durumu"] if d.get("migrated_at")}
    # BEKLENEN KARAR — `apply()`in varlık döngüsüyle AYNI öncelik: damga → zaten_tasindi, kaynak → tasinacak,
    # yoksa kaynak_yok. Kuru koşu bunu söylemiyordu (yalnız "kaynağı olan" sayısı vardı; damgalı ama kanonik
    # dosyası yeniden doğmuş bir varlığı da "taşınacak" sayardı). Kademe C D6-2'nin okuması budur: A1'de
    # iki `tasinacak`, altı `zaten_tasindi`.
    for v in varliklar:
        v["beklenen"] = ("zaten_tasindi" if v["varlik"] in damgali else
                         "tasinacak" if v["kaynak_var"] else "kaynak_yok")
    out["tasinacak"] = sum(1 for v in varliklar if v["beklenen"] == "tasinacak")
    out["zaten_tasindi"] = sum(1 for v in varliklar if v["beklenen"] == "zaten_tasindi")
    return out


def db_state() -> list[dict]:
    """DB'deki varlıkların CANLI sayaçları (iddia değil, tablodan sayım).

    ŞEMA KURMAZ. Eskiden `connect(create=True)` + `ensure_schema(c)` çağırıyordu;
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
        if not storage.table_exists(name, c):
            # ŞEMADA HENÜZ YOK (Kademe C öncesi v1 DB — A1'in 2026-09-28 hâli): tabloyu okumak istisnayla
            # kuru koşuyu, `--durum`u ve `--geri-al`ın ölçümünü DÜŞÜRÜRDÜ. Sayı UYDURULMAZ: n None.
            rows.append({"varlik": name, "tablo_var": False, "present": False, "n": None,
                         "rev": None, "migrated_at": None, "db_digest": None,
                         "kaynak_digest": None})
            continue
        payload = storage.read_entity(name)
        n = (len(payload) if isinstance(payload, list)
             else len((payload or {}).get(storage.POINTS_KEY) or [])
             if storage.kind_of(name) == "series" else (1 if payload is not None else 0))
        rows.append({"varlik": name, "tablo_var": True, "present": bool(m.get("present")), "n": n,
                     "rev": m.get("rev"), "migrated_at": m.get("migrated_at"),
                     "db_digest": digest(payload) if payload is not None else None,
                     "kaynak_digest": m.get("source_digest")})
    return rows


# ---- BAŞARISIZ MİGRASYONDAN SONRA: DB'Yİ KENARA AL ---------------------------------------------
def _karantina(rapor: dict, db_yeni: bool, sebep: str) -> None:
    """Bu koşuda DOĞAN DB'yi `meridian.db.failed-<ts>` diye kenara al ve BEYAN ET.

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
        f"başarısız migrasyondan sonra DB DEVREDE DEĞİL — {len(storage.ENTITIES)} defter dosya arka "
        f"ucundan okunur (kaynak dosyalar yerinde ve .migrated eki almadı)" if not kayit["aktif"] else
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
            # `active()` True dönüyor ve defterler SESSİZCE boş okunuyordu. Şema artık aşağıdaki
            # ROLLBACK'lerin kapsamındadır. `onceki` (entity_meta) okuması da bu yüzden içeri alındı
            # — tablo ancak şema kurulduktan sonra vardır.
            storage.apply_schema(c)
            onceki = {n: (storage.meta(n) or {}) for n in storage.ENTITIES}
            tasinan = []
            ezilen: dict = {}
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
                # EZİLEN KANIT ÖLÇÜLÜR (Kademe C tur 2): damgasız bir varlığın tablosu BOŞ olmayabilir — kısıtlı
                # geri almadan (`--geri-al --varlik`) sonra göç-sonrası DB satırları tabloda KANIT olarak kalır
                # ve aşağıdaki "sil + yaz" onları kaynak dosyayla EZER. Davranış değişmez (parite dosyaya karşı
                # ölçülür); ama ezilen satır sayısı rapora ve obs olayına girer — sessiz kayıp olmasın.
                onceki_n = c.execute(
                    f"SELECT COUNT(*) AS n FROM {storage.table_of(name)}").fetchone()["n"]
                if onceki_n:
                    ezilen[name] = int(onceki_n)
                kind = storage.kind_of(name)
                if kind == "rows":
                    storage.do_replace_rows(c, name, src["payload"])
                elif kind == "series":
                    storage.do_write_series(c, src["payload"], name)
                else:
                    storage.do_write_doc(c, name, src["payload"])
                tasinan.append(name)

            # PARİTE TURU — hâlâ AÇIK transaction içinde okunur (aynı bağlantı kendi yazımını görür),
            # yani eşleşmezse COMMIT hiç olmaz. `storage.read_entity` DB'yi DOĞRUDAN okur; `store.*`
            # KULLANILMAZ: varlık kapısı (Kademe C D2) damgasız varlığı dosyaya yönlendirir ve parite
            # kaynak↔kaynak kıyasına dönüşürdü (SAHTE yeşil — v579 çivisi).
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
                    "kaynak_digest": src_d, "db_digest": db_d,
                    **({"ezilen_db_satiri": ezilen[name]} if name in ezilen else {})})
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
            rapor["ezilen"] = [{"varlik": n, "onceki_db_n": k} for n, k in ezilen.items()]
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
                 ezilen=rapor.get("ezilen") or None,
                 detail="defter çekirdeği SQLite'a taşındı (parite digesti doğrulandı); "
                        "kaynak dosyalar .migrated ekiyle yerinde duruyor")
    except Exception:  # sessiz-yutma: kayıt kanalı düştü; migrasyon COMMIT edildi ve rapor çağırana döndü — kayıt denemesi taşımayı geri alamaz
        pass
    return rapor


# ---- GERİ AL (kurtarma kolu) -------------------------------------------------------------------
def _kenara(p: Path, hedef: Path, kayit: dict) -> bool:
    """Tek dosyayı yeniden adlandır; sonucu `kayit`a yaz. SİLMEZ ve ÜZERİNE YAZMAZ."""
    if not p.exists():
        return False
    if hedef.exists():
        kayit.setdefault("hatalar", []).append(f"{hedef.name} zaten var — {p.name} taşınmadı")
        return False
    try:
        p.rename(hedef)
        kayit.setdefault("tasinan", []).append(f"{p.name} → {hedef.name}")
        return True
    except OSError as e:  # sessiz-yutma: sonuç KAYDA GEÇİYOR (rapor `hatalar` + çağıranda ok=False) — taşınamayan dosya bir istisnayla tüm kurtarmayı düşürmemeli, kalan adımlar operatöre daha çok geri kazandırır
        kayit.setdefault("hatalar", []).append(f"{p.name}: {type(e).__name__}: {e}")
        return False


def rollback() -> dict:
    """`--geri-al`: DB'yi kenara al, `.migrated` arşivlerini ASIL adlarına döndür, PARİTEYİ raporla.

    NEDEN BU KOL VAR (C5). `MERIDIAN_DB=off` "acil geri dönüş" diye belgelenmişti ama tek başına
    defterleri BOŞ okutuyordu: kaynaklar `.migrated` adında duruyor, `store._path` kanonik ada
    bakıyor, bulamıyor ve çağıranın varsayılanına düşüyordu (ölçüldü: trades n=0, portfolio/
    scoreboard/equity VARSAYILAN). Eksik olan elle `mv` adımıydı ve hiçbir yerde yazılı değildi.

    SIRA BİLEREK BÖYLEDİR:
      1. ÖLÇÜM ÖNCE — DB satır sayıları/digestleri okunur. Dosya kenara alındıktan SONRA bu ölçüm
         alınamaz; alınamayan ölçüm rapora "None" diye girer ve operatör farkı göremez.
      2. BAĞLANTILARI KAPAT — açık bir tanıtıcı yeniden adlandırılmış dosyaya WAL geri yazabilir ve
         `_SCHEMA_OK` önbelleği "şema tamam" demeye devam ederdi (`_karantina` ile aynı gerekçe).
      3. DB KENARA — `-wal`/`-shm` dahil; ana ad değişip yan dosyalar kalsaydı ileride doğacak taze
         bir `meridian.db` BAYAT bir WAL'la eşleşirdi.
      4. ARŞİVLER ASIL ADINA — kanonik adı işgal eden bir dosya varsa o da silinmez, `.ayrisik-<ts>`
         ile kenara alınır.
    Adım 3 ile 4 arasındaki pencerede süreç çökerse hâl DÜRÜSTTÜR: DB kenarda, arşivler `.migrated`
    adında — yani `active()` False, defterler boş okunur ve komut yeniden koşturulabilir (idempotent).

    PARİTE RAPORU BİR UYARIDIR, BİR ONAY DEĞİL: `db_n − dosya_n` farkı, migrasyondan SONRA DB'ye
    yazılmış ve arşivde BULUNMAYAN satırların sayısıdır. O satırların TEK kopyası kenara alınan
    DB'dedir — bu yüzden dosya silinmez ve fark raporun en üstüne basılır."""
    ts = time.strftime("%Y%m%d-%H%M%S")
    db = storage.db_path()
    rapor: dict = {"geri_al": True, "kip": "tam", "ts": ts, "db": str(db), "db_var_idi": db.exists(),
                   "db_kenara": {"yapildi": False, "hedef": None}, "varliklar": [], "ok": True,
                   "kapsam_uyarisi": _tam_kip_uyarisi()}

    # 1) ÖLÇÜM ÖNCE (bkz. docstring). Şemasız/yoksa `db_state()` BOŞ liste döner — uydurulmuş
    #    sıfır sayaç yazılmaz, alanlar None kalır.
    db_once = {r["varlik"]: r for r in db_state()}

    # 2) BAĞLANTILARI KAPAT
    try:
        storage.close_connections()
    except Exception as e:  # sessiz-yutma: sonuç KAYDA GEÇİYOR (kapatma_hatasi raporda) — kapatılamayan bir tanıtıcı kurtarma kararını geri aldıramaz ve süreç sonu onu toplar
        rapor["kapatma_hatasi"] = f"{type(e).__name__}: {e}"

    # 3) DB KENARA
    kayit: dict = {"yapildi": False, "hedef": None}
    if db.exists():
        hedef = db.with_name(db.name + ROLLEDBACK_SUFFIX + ts)
        kayit["hedef"] = str(hedef)
        for ek in ("", "-wal", "-shm"):
            _kenara(db.with_name(db.name + ek), hedef.with_name(hedef.name + ek), kayit)
        kayit["yapildi"] = not db.exists()
        if not kayit["yapildi"]:
            rapor["ok"] = False
    rapor["db_kenara"] = kayit

    # 4) ARŞİVLER ASIL ADINA + parite sayımı
    for name in storage.ENTITIES:
        p = source_path(name)
        ars = p.with_name(name + MIGRATED_SUFFIX)
        onceki = db_once.get(name) or {}
        rec: dict = {"varlik": name, "arsiv_var_idi": ars.exists(), "geri_donen": False,
                     "db_n": onceki.get("n") if onceki else None,
                     "db_digest": onceki.get("db_digest") if onceki else None,
                     "ayrisik_kenara": None, "dosya_n": None, "dosya_digest": None, "fark": None}
        if ars.exists():
            if p.exists():
                # KANONİK AD İŞGAL EDİLMİŞ: anahtar çekiliyken doğmuş AYRIŞIK ikinci kitap.
                # Üzerine yazmak, kurtarma kolunu veri kaybına çevirirdi.
                ayr = p.with_name(name + DIVERGENT_SUFFIX + ts)
                if _kenara(p, ayr, rec):
                    rec["ayrisik_kenara"] = ayr.name
            if not p.exists():
                rec["geri_donen"] = _kenara(ars, p, rec)
        if rec.get("hatalar"):
            rapor["ok"] = False
        src = read_source(name)
        if src["present"]:
            rec["dosya_n"] = src["n"]
            rec["dosya_digest"] = digest(src["payload"]) if src["payload"] is not None else None
            if rec["db_n"] is not None:
                rec["fark"] = int(rec["db_n"]) - int(src["n"])
        # SAYI TEK BAŞINA YETMEZ: tekil belgeler (`scoreboard`/`portfolio`/`shadow_books`) için `n`
        # HER ZAMAN 1'dir, yani `fark` içerik değişimine KÖRDÜR. Ayrışmayı görebilen tek ölçüm
        # digesttir — migrasyonun kendi parite kanıtıyla aynı fonksiyon, aynı normalizasyon.
        rec["digest_esit"] = (None if (rec["db_digest"] is None or rec["dosya_digest"] is None)
                              else rec["db_digest"] == rec["dosya_digest"])
        rapor["varliklar"].append(rec)

    rapor["geri_donen"] = [v["varlik"] for v in rapor["varliklar"] if v["geri_donen"]]
    rapor["yapildi"] = bool(kayit["yapildi"] or rapor["geri_donen"])
    rapor["aktif"] = storage.active(storage.TRADES)
    rapor["db_dosyasi_var"] = db.exists()
    farkli = [v for v in rapor["varliklar"] if v["fark"] or v["digest_esit"] is False]
    rapor["fark_var"] = [{"varlik": v["varlik"], "db_n": v["db_n"], "dosya_n": v["dosya_n"],
                          "fark": v["fark"], "digest_esit": v["digest_esit"]} for v in farkli]
    # BEYAN DALDAN TÜRETİLİR, SABİT DEĞİL (`_karantina` ile aynı kural): raporun kendi ölçümüyle
    # çelişen bir cümle, kapatmaya çalıştığımız sınıfın ta kendisi olurdu.
    if not rapor["yapildi"]:
        rapor["beyan"] = ("GERİ ALINACAK BİR ŞEY YOK — kenara alınacak DB dosyası ve asıl adına "
                          "dönecek `.migrated` arşivi bulunamadı; defterler ZATEN dosyadan okunuyor.")
    elif rapor["db_dosyasi_var"]:
        # `aktif` TEK BAŞINA YETMEZ: `MERIDIAN_DB=off` çekiliyken taşınamamış bir DB de `aktif=False`
        # gösterir ve "geri alındı" cümlesi anahtar kapanır kapanmaz YALAN olurdu. Ölçülen şey
        # dosyanın kanonik adda DURUYOR olmasıdır.
        rapor["beyan"] = (f"EKSİK GERİ ALMA: DB dosyası HÂLÂ kanonik adında ({db.name}) — kenara "
                          f"alınamadı (bkz. hatalar). Şu an aktif={rapor['aktif']}; dosya elle "
                          f"taşınmadıkça DB devreye geri döner.")
    else:
        rapor["beyan"] = (f"GERİ ALINDI — DB devrede DEĞİL, {len(rapor['geri_donen'])} defter asıl "
                          f"adına döndü ve dosya arka ucundan okunuyor. Kenara alınan DB SİLİNMEDİ: "
                          f"{kayit['hedef'] or '(DB yoktu)'}")
    if rapor["fark_var"]:
        rapor["beyan"] += (" | DİKKAT: DB ile geri dönen dosya AYNI DEĞİL (migrasyon SONRASI "
                           "yazımlar arşivde yok) — "
                           + ", ".join(
                               f"{f['varlik']}: DB {f['db_n']} vs dosya {f['dosya_n']} satır"
                               + ("" if f["fark"] else " (sayı aynı, İÇERİK farklı)")
                               for f in rapor["fark_var"])
                           + ". O yazımların TEK kopyası kenara alınan DB'dedir; SİLME.")
    try:
        from . import obs
        obs.warn("sqlite_ledger_rolled_back", geri_donen=rapor["geri_donen"],
                 db_kenara=kayit.get("hedef"), aktif=rapor["aktif"],
                 fark=rapor["fark_var"], detail=rapor["beyan"])
    except Exception:  # sessiz-yutma: kayıt kanalı düştü; geri alma DİSKTE zaten uygulandı ve rapora yazıldı — kayıt denemesi onu geri alamaz
        pass
    return rapor


def _tam_kip_uyarisi() -> dict:
    """Tam `--geri-al`ın KAPSAM beyanı — kayıttan türer (el listesi değil). Okuyucusu `_print_geri_al` + `--json`."""
    eski = [n for n in storage.ENTITIES if n not in storage.DAMGA_KAPILI]
    return {"eski_varliklar": eski,
            "metin": (f"bu kip Kademe A+B'yi de geri alır — DB'nin TAMAMI kenara alınır ve {len(eski)} "
                      f"eski defter ({', '.join(eski)}) dosyaya döner; onların göç-sonrası DB yazımları "
                      f"arşivde YOKTUR. Yalnız Kademe C defterleri için: `--geri-al --varlik "
                      f"{','.join(storage.DAMGA_KAPILI)}`")}


def _kisitli_adlar(varliklar) -> list[str]:
    """Kısıtlı geri almanın ad listesi — doğrular, tekilleştirir (sıra korunur). Hatada `ValueError`.

    YALNIZ DAMGA KAPILI VARLIK: eski varlıkların okuma kapısı yoktur — damgaları sökülse de DB'den okunmaya
    devam ederler (dosyaya DÖNEMEZLER) ve bir sonraki `--uygula` tablolarını kaynak dosyayla ezerdi."""
    adlar: list[str] = []
    for ad in varliklar or []:
        ad = str(ad).strip()
        if ad and ad not in adlar:
            adlar.append(ad)
    if not adlar:
        raise ValueError("kısıtlı geri alma için en az bir varlık adı gerekli")
    bilinmeyen = [a for a in adlar if a not in storage.ENTITIES]
    if bilinmeyen:
        raise ValueError(f"bilinmeyen varlık: {bilinmeyen} — kayıt: {list(storage.ENTITIES)}")
    kapisiz = [a for a in adlar if a not in storage.DAMGA_KAPILI]
    if kapisiz:
        raise ValueError(f"kısıtlı geri alma yalnız şemaya sonradan giren (damga kapılı) varlıklar içindir: "
                         f"{list(storage.DAMGA_KAPILI)} — {kapisiz} eski varlık: okuma kapıları yok, dosyaya "
                         f"DÖNEMEZLER (tam `--geri-al` Kademe A+B'nin tamamını geri alır)")
    return adlar


def rollback_kisitli(varliklar) -> dict:
    """`--geri-al --varlik a,b` (Kademe C tur 2, F1): YALNIZ listelenen kapılı varlıkları dosyaya döndür.

    NEDEN (tur 1 ölçümü). Tam `rollback()` HEPSİ-YA-HİÇ'tir: DB'nin tamamını kenara alır ve Kademe A+B'nin
    altı defterini de dosyaya döndürür — onların 2026-07-31'den beri DB'ye yazılmış satırları arşivde YOKTUR.
    Kademe C'nin geri alınması o kitabı iki ay geriye saramaz. Varlık kapısı (`storage.active`, D2) burada
    kolu verir: damgası sökülen kapılı varlık DOSYADAN okunur, diğerleri DB'de yaşamaya devam eder.

    SIRA BİLEREK BÖYLEDİR (tasarımın "anahtar COMMIT'tir" ilkesi, `apply()` ile simetrik):
      1. ÖLÇÜM ÖNCE — DB satır sayısı/digest (`db_state`); anahtar değiştikten sonra aynı soru farklı katmana gider.
      2. ARŞİVLER ASIL ADINA — damga HÂLÂ doluyken (okuma DB'de, davranış değişmez); kanonik adı işgal eden
         ayrışık dosya `.ayrisik-<ts>` ile kenara (ezilmez).
      3. DAMGA SÖKÜLÜR — tek transaction; COMMIT anında kanonik dosya ZATEN hazırdır → boş okuma anı yok.
         Kanonik dosyası olmayan varlığın damgası SÖKÜLMEZ (boş okuma = R1'in kendisi), rapor düşer.
    Adım 2 ile 3 arasında çökme: damga dolu + kanonik dosya duruyor — okuma DB'den (doğru); komut yeniden
    koşturulabilir (idempotent). DB dosyası TAŞINMAZ, tablo satırları SİLİNMEZ (kanıt).

    ÇALIŞAN SÜREÇLER damga önbelleği (`storage._DAMGA_OK`) taşır: geri almadan sonra servisler YENİDEN
    başlatılmalıdır (canlı-süreç kapısı zaten durmuş olmalarını ister; beyan bunu söyler)."""
    adlar = _kisitli_adlar(varliklar)
    ts = time.strftime("%Y%m%d-%H%M%S")
    db = storage.db_path()
    rapor: dict = {"geri_al": True, "kip": "kisitli", "istenen": adlar, "ts": ts, "db": str(db),
                   "db_var_idi": db.exists(),
                   "db_kenara": {"yapildi": False, "hedef": None,
                                 "not": "kısıtlı kip — DB TAŞINMAZ; listelenmeyen varlıklar DB'de kalır"},
                   "varliklar": [], "geri_donen": [], "damgasi_kaldirilan": [], "ok": True}
    # 1) ÖLÇÜM ÖNCE (şemasız/yoksa boş — uydurulmuş sayaç yazılmaz)
    durum = {r["varlik"]: r for r in db_state()}
    for name in adlar:
        p = source_path(name)
        ars = p.with_name(name + MIGRATED_SUFFIX)
        d = durum.get(name) or {}
        rec: dict = {"varlik": name, "tablo": storage.table_of(name),
                     "damgali_idi": bool(d.get("migrated_at")), "arsiv_var_idi": ars.exists(),
                     "geri_donen": False, "ayrisik_kenara": None, "damga_kaldirildi": False,
                     "db_n": d.get("n"), "db_digest": d.get("db_digest"),
                     "dosya_n": None, "dosya_digest": None, "fark": None}
        # 2) ARŞİV ASIL ADINA (damga hâlâ dolu)
        if ars.exists():
            if p.exists():
                ayr = p.with_name(name + DIVERGENT_SUFFIX + ts)
                if _kenara(p, ayr, rec):
                    rec["ayrisik_kenara"] = ayr.name
            if not p.exists():
                rec["geri_donen"] = _kenara(ars, p, rec)
        rapor["varliklar"].append(rec)
    # 3) DAMGA SÖKÜLÜR — yalnız kanonik dosyası HAZIR olanlar, tek transaction
    sokulecek = [r for r in rapor["varliklar"] if r["damgali_idi"] and source_path(r["varlik"]).exists()]
    sokulecek_adlar = {r["varlik"] for r in sokulecek}
    for r in rapor["varliklar"]:
        if r["damgali_idi"] and r["varlik"] not in sokulecek_adlar:
            r.setdefault("hatalar", []).append(
                "kanonik dosya YOK (arşiv de yok) — damga SÖKÜLMEDİ: dosyaya çevirmek BOŞ okuma olurdu")
    if sokulecek:
        c = storage.connect()
        with storage._GUARD:
            c.execute("BEGIN IMMEDIATE")
            try:
                for r in sokulecek:
                    storage.unmark_migrated(r["varlik"], conn=c)
                c.execute("COMMIT")
            except BaseException:
                c.execute("ROLLBACK")
                raise
        for r in sokulecek:
            r["damga_kaldirildi"] = True
    # Bu süreçteki önbellek (damga + şema) disk gerçeğinin ötesinde kalmasın
    storage.close_connections()
    # 4) ÖLÇÜM SONRA — dosya tarafı (artık OTORİTER olan) ↔ DB tablosu
    for r in rapor["varliklar"]:
        src = read_source(r["varlik"])
        if src["present"]:
            r["dosya_n"] = src["n"]
            r["dosya_digest"] = digest(src["payload"]) if src["payload"] is not None else None
            if r["db_n"] is not None:
                r["fark"] = int(r["db_n"]) - int(src["n"])
        r["digest_esit"] = (None if (r["db_digest"] is None or r["dosya_digest"] is None)
                            else r["db_digest"] == r["dosya_digest"])
        if r.get("hatalar"):
            rapor["ok"] = False
    rapor["geri_donen"] = [r["varlik"] for r in rapor["varliklar"] if r["geri_donen"]]
    rapor["damgasi_kaldirilan"] = [r["varlik"] for r in rapor["varliklar"] if r["damga_kaldirildi"]]
    rapor["yapildi"] = bool(rapor["geri_donen"] or rapor["damgasi_kaldirilan"])
    rapor["aktif"] = {n: storage.active(n) for n in adlar}
    rapor["db_dosyasi_var"] = db.exists()
    farkli = [r for r in rapor["varliklar"]
              if r["damga_kaldirildi"] and (r["fark"] or r["digest_esit"] is False)]
    rapor["fark_var"] = [{"varlik": r["varlik"], "tablo": r["tablo"], "db_n": r["db_n"],
                          "dosya_n": r["dosya_n"], "fark": r["fark"], "digest_esit": r["digest_esit"]}
                         for r in farkli]
    # BEYAN DALDAN TÜRETİLİR (rollback/_karantina kuralı)
    if not rapor["yapildi"]:
        rapor["beyan"] = ("GERİ ALINACAK BİR ŞEY YOK — " + ", ".join(adlar) + " için sökülecek damga ya da "
                          "asıl adına dönecek `.migrated` arşivi yok; " +
                          ("bu varlıklar ZATEN dosyadan okunuyor." if not any(rapor["aktif"].values())
                           else "DİKKAT: bazıları hâlâ DB'den okunuyor (bkz. hatalar)."))
    else:
        rapor["beyan"] = (f"KISITLI GERİ ALINDI — {', '.join(rapor['damgasi_kaldirilan']) or '-'} artık "
                          f"DOSYADAN okunuyor; DB dosyası YERİNDE, listelenmeyen varlıklar DB'de. Tablo "
                          f"satırları SİLİNMEDİ (kanıt). Çalışan süreçler damgayı önbelleğe almış olabilir — "
                          f"servisleri yeniden başlat.")
    if rapor["fark_var"]:
        rapor["beyan"] += (" | DİKKAT: " + "; ".join(
            f"{f['varlik']}: DB {f['db_n']} vs dosya {f['dosya_n']} satır"
            + (f" — göç sonrası DB'ye yazılmış {f['fark']} satır arşivde YOK" if f["fark"]
               else " (sayı aynı, İÇERİK farklı)")
            + f": kayıp değil, `{f['tablo']}` tablosunda DB'de duruyor"
            for f in rapor["fark_var"])
            + ". Yeniden `--uygula` bu tabloları kaynak dosyayla EZER — önce dışa al.")
    try:
        from . import obs
        obs.warn("sqlite_ledger_rolled_back_kisitli", istenen=adlar,
                 damgasi_kaldirilan=rapor["damgasi_kaldirilan"], geri_donen=rapor["geri_donen"],
                 fark=rapor["fark_var"], detail=rapor["beyan"])
    except Exception:  # sessiz-yutma: kayıt kanalı düştü; kısıtlı geri alma DİSKTE zaten uygulandı ve rapora yazıldı — kayıt denemesi onu geri alamaz
        pass
    return rapor


def _worker_running() -> bool:
    """Canlı Meridian süreci var mı? `barrepair`in AYNI ölçümü — kopyalanmaz, çağrılır."""
    from .barrepair import _worker_running as _wr
    return _wr()


# ÖĞRENME SÜRECİ YOKLAMASI (Kademe C tur 2, F2). `memory.record` ve `validation.record_candidate`
# `meridian-learn` biriminde yazar; `_worker_running` (barrepair'in PAYLAŞILAN ölçümü, üç tüketicisi var)
# yalnız `uvicorn meridian.api`yi arar — anlamı DEĞİŞTİRİLMEDİ, bu yoklama dbmigrate'e ÖZGÜDÜR.
# DESEN UYDURULMADI: `deploy/oracle-a1/meridian-learn.service` ExecStart =
# `/opt/meridian/.venv/bin/python -m meridian.learn_run` (okundu 2026-09-28; ayrışma çivisi v582 birimden
# türetip kıyaslar). `[.]` LİTERAL noktadır: dosya YOLUNU (`meridian/learn_run.py` — editör, grep) eşlemez.
OGRENME_SURECI_DESENI = "meridian[.]learn_run"


def _ogrenme_sureci_kosuyor() -> bool:
    """Öğrenme süreci (`python -m meridian.learn_run`) koşuyor mu? Ölçülemezse KOŞUYOR sayılır (muhafazakâr
    taraf — barrepair'in aynı kuralı): yazan bir koşunun kapısında "bilmiyorum" GEÇ demek olamaz."""
    try:
        r = subprocess.run(["pgrep", "-f", OGRENME_SURECI_DESENI], capture_output=True,
                           text=True, timeout=5)
        return bool((r.stdout or "").strip())
    except (OSError, subprocess.SubprocessError):  # sessiz-yutma: pgrep yoksa/zaman aşımı — ölçüm yapılamadı; dönen True kararı TAŞIR ("koşuyor say" → ret), çağıran mesajı basar ve --zorla kolu açık
        return True


def _print(rapor: dict) -> None:
    """Plan/uygula raporunu insan-okur tabloya basar: mod (kuru koşu/uygulandı), DB yolu ve şema
    sürümü, varlık başına satır+digest, parite satırları, arşivlenen kaynaklar, hata ve karantina
    hükmü. Yalnız BASAR — hiçbir karar vermez, hiçbir bayt yazmaz."""
    mod = ("UYGULANDI" if rapor.get("yazildi") else
           ("UYGULAMA İSTENDİ ama taşınacak varlık yok" if rapor.get("applied")
            else "KURU KOŞU (hiçbir bayt yazılmadı)"))
    print(f"[dbmigrate] {mod}")
    print(f"  db: {rapor['db']}  (var: {rapor['db_var']}, şema sürümü: {rapor.get('sema_surumu')})")
    print(f"  {'varlık':24s} {'n':>7s}  {'kaynak':>6s}  {'beklenen':14s} kaynak_digest")
    for v in rapor["varliklar"]:
        print(f"  {v['varlik']:24s} {v['n']:>7d}  {str(v['kaynak_var']):>6s}  "
              f"{v.get('beklenen', '-'):14s} {v['kaynak_digest'] or '-'}"
              + (f"  [BOZUK SATIR: {v['bozuk_satir']}]" if v["bozuk_satir"] else "")
              + ("  [arşiv var]" if v["arsiv_var"] else ""))
    print(f"  toplam satır: {rapor['toplam_satir']}, taşınacak varlık: {rapor['tasinacak']}, "
          f"zaten taşınmış: {rapor.get('zaten_tasindi')}")
    for p in rapor.get("parite") or []:
        isaret = "OK " if p.get("ok") else "!! "
        print(f"   {isaret}{p['varlik']:24s} {p['durum']:16s} "
              f"kaynak={p.get('kaynak_digest') or '-'} db={p.get('db_digest') or '-'}")
    if rapor.get("arsivlenen"):
        print(f"  arşivlenen kaynak: {rapor['arsivlenen']}")
    if rapor.get("ezilen"):
        # Kısıtlı geri almanın bıraktığı kanıt satırları (ya da damgasız ama dolu bir tablo) bu koşuda
        # kaynak dosyayla EZİLDİ — sayı operatörün önüne gelir (sessiz kayıp yok).
        print("  UYARI: tablo BOŞ DEĞİLDİ, kaynakla EZİLDİ: "
              + ", ".join(f"{e['varlik']} (önceki {e['onceki_db_n']} satır)" for e in rapor["ezilen"]))
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


def _print_geri_al(rapor: dict) -> None:
    """`--geri-al` raporunu insan-okur tabloya basar: DB'nin kenara alınıp alınmadığı, varlık
    başına arşiv/geri-dönüş durumu, DB-dosya satır farkı ve digest eşitliği, hatalar ve beyan."""
    print(f"[dbmigrate] GERİ AL ({rapor['ts']})")
    k = rapor["db_kenara"]
    print(f"  db: {rapor['db']}  (koşu öncesi vardı: {rapor['db_var_idi']})")
    if rapor.get("kip") == "kisitli":
        print(f"  KISITLI KİP: yalnız {', '.join(rapor['istenen'])} — DB YERİNDE, listelenmeyen varlıklar "
              f"dokunulmadı; damgası sökülen: {', '.join(rapor['damgasi_kaldirilan']) or '-'}")
    elif rapor.get("kapsam_uyarisi"):
        # Tam kip HEPSİ-YA-HİÇ'tir — operatörün önüne KOMUTUN kendi çıktısında gelir (Kademe C tur 2 F1).
        print(f"  UYARI: {rapor['kapsam_uyarisi']['metin']}")
    print(f"  DB kenara: {'EVET' if k.get('yapildi') else 'HAYIR'}"
          + (f"  → {k['hedef']}" if k.get("hedef") else ""))
    for t in k.get("tasinan") or []:
        print(f"    {t}")
    print(f"  {'varlık':24s} {'arşiv':>6s} {'geri':>5s} {'db_n':>7s} {'dosya_n':>8s} {'fark':>6s}  digest")
    for v in rapor["varliklar"]:
        d = {True: "eşit", False: "AYRIŞIK", None: "-"}[v["digest_esit"]]
        print(f"  {v['varlik']:24s} {str(v['arsiv_var_idi']):>6s} {str(v['geri_donen']):>5s} "
              f"{str(v['db_n'] if v['db_n'] is not None else '-'):>7s} "
              f"{str(v['dosya_n'] if v['dosya_n'] is not None else '-'):>8s} "
              f"{str(v['fark'] if v['fark'] is not None else '-'):>6s}  {d}"
              + (f"  [ayrışık kenara: {v['ayrisik_kenara']}]" if v["ayrisik_kenara"] else ""))
        for h in v.get("hatalar") or []:
            print(f"      HATA: {h}")
    for h in k.get("hatalar") or []:
        print(f"  HATA: {h}")
    if rapor.get("kapatma_hatasi"):
        print(f"  kapatma_hatasi: {rapor['kapatma_hatasi']}")
    print(f"  aktif (DB'den mi okunuyor): {rapor['aktif']}")
    print(f"  {rapor['beyan']}")


def main(argv: list[str] | None = None) -> int:
    """Komut satırı girişi: `--durum` / `--geri-al` [`--varlik a,b`] / `--uygula` (varsayılan kuru koşu),
    `--json`, `--zorla`. Çelişkili niyet (`--uygula` + `--geri-al`), `--geri-al`sız `--varlik`, geçersiz
    varlık listesi ve canlı worker YA DA öğrenme süreci görülen yazan koşular REDDEDİLİR (çıkış 2).
    Dönüş: 0 başarı, 1 raporun `ok=False` hükmü, 2 ret."""
    ap = argparse.ArgumentParser(
        prog="python -m meridian.dbmigrate",
        description=f"defterleri ({len(storage.ENTITIES)} varlık) SQLite'a taşır — parite digesti "
                    f"zorunlu, taşınmış varlık atlanır (artımlı)")
    ap.add_argument("--uygula", action="store_true", help="TAŞI (varsayılan: kuru koşu)")
    ap.add_argument("--json", action="store_true", help="raporu JSON olarak bas")
    ap.add_argument("--durum", action="store_true", help="yalnız DB durumunu bas")
    ap.add_argument("--geri-al", dest="geri_al", action="store_true",
                    help="GERİ DÖN: DB'yi kenara al, `.migrated` arşivlerini asıl adlarına döndür")
    ap.add_argument("--varlik", default=None,
                    help=("--geri-al ile: YALNIZ bu varlıkları (virgüllü) geri al — DB yerinde kalır, "
                          "yalnız şemaya sonradan giren (damga kapılı) varlıklar: "
                          + ",".join(storage.DAMGA_KAPILI)))
    ap.add_argument("--zorla", action="store_true",
                    help="canlı süreç görülse de taşı/geri al (riski sen alırsın)")
    a = ap.parse_args(argv)
    if a.uygula and a.geri_al:
        # ÇELİŞKİLİ NİYET SESSİZCE SIRALANMAZ: hangisinin önce koştuğuna bağlı olarak sonuç
        # "taşındı" ya da "geri alındı" olurdu ve operatör hangisini istediğini raporda göremezdi.
        print("[dbmigrate] REDDEDİLDİ: --uygula ile --geri-al aynı koşuda verilemez (çelişkili "
              "niyet). Önce birini koş, raporu oku, sonra karar ver.", file=sys.stderr)
        return 2
    if a.varlik is not None and not a.geri_al:
        # KAPSAM KISITI YALNIZ GERİ ALMANIN: `--uygula` zaten artımlıdır (damgalıyı atlar); `--varlik`i
        # sessizce yok saymak, operatöre "yalnız bunları taşıdım" sandırırdı.
        print("[dbmigrate] REDDEDİLDİ: --varlik yalnız --geri-al ile anlamlıdır (kısıtlı geri alma).",
              file=sys.stderr)
        return 2
    kisitli = None
    if a.geri_al and a.varlik is not None:
        try:
            kisitli = _kisitli_adlar(a.varlik.split(","))
        except ValueError as e:
            print(f"[dbmigrate] REDDEDİLDİ: {e}", file=sys.stderr)
            return 2
    if a.durum:
        out = {"db": str(storage.db_path()), "db_var": storage.db_path().exists(),
               "sema_surumu": storage.schema_version() if storage.db_path().exists() else None,
               "aktif": storage.active(storage.TRADES),
               "durum": db_state() if storage.db_path().exists() else []}
        print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
        return 0
    # TEK KAPI, İKİ YAZAN YOL: `--geri-al` de arka ucu ayağının altından çeker (DB kenara alınır),
    # yani `--uygula` ile AYNI korumayı hak eder. Ayrı bir kapı yazmak, korumanın ikisinden birinde
    # sessizce eskimesine açık kapı bırakırdı.
    if (a.uygula or a.geri_al) and not a.zorla and _worker_running():
        print("[dbmigrate] REDDEDİLDİ: canlı Meridian süreci görülüyor. Defter taşınırken ya da "
              "GERİ ALINIRKEN canlı yazar olamaz — arka uç ayağının altından çekilir. "
              "Önce `./ops/stop-worker.sh`, sonra tekrar dene (ya da --zorla).", file=sys.stderr)
        return 2
    # İKİNCİ YAZAR SÜRECİ (Kademe C tur 2 F2): öğrenme defterlerine `meridian-learn` yazar; yukarıdaki kapı
    # onu GÖRMEZ (paylaşılan ölçüm yalnız uvicorn arar). Aynı kural, aynı `--zorla` kolu.
    if (a.uygula or a.geri_al) and not a.zorla and _ogrenme_sureci_kosuyor():
        print("[dbmigrate] REDDEDİLDİ: öğrenme süreci (meridian-learn: `python -m meridian.learn_run`) "
              "görülüyor ya da yoklama ölçülemedi — `memory.record`/`validation.record_candidate` bu "
              "süreçte deftere yazar; taşıma/geri alma sırasında yazar olamaz. Önce öğrenme birimini "
              "durdur (`systemctl stop meridian-learn`), sonra tekrar dene (ya da --zorla).",
              file=sys.stderr)
        return 2
    if a.geri_al:
        rapor = rollback_kisitli(kisitli) if kisitli is not None else rollback()
        if a.json:
            print(json.dumps(rapor, ensure_ascii=False, indent=1, default=str))
        else:
            _print_geri_al(rapor)
        return 0 if rapor.get("ok", True) else 1
    rapor = apply() if a.uygula else plan()
    if a.json:
        print(json.dumps(rapor, ensure_ascii=False, indent=1, default=str))
    else:
        _print(rapor)
    return 0 if rapor.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
