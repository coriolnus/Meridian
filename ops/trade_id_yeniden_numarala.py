"""ops/trade_id_yeniden_numarala.py — TSK-150(b): 16 ÇİFT işlem kimliğinin yeniden numaralanması.

OPERATÖR KARARI (2026-09-05, ~18:3xZ): "Yeniden numarala, eşleme defteriyle." `storage.py`
`_COLS[TRADES]` şerhinin ölçtüğü hâl (TSK-150(a)): işlem defterinde (`trades` tablosu, gerçek
anahtar `seq`) `id` (`T%05d` biçimi) İLERİ YÖNLÜ tekildir ama GEÇMİŞTE (tohum genişletme, last_id
gerisi) yazılmış 16 çift zaten vardır. 2026-09-05 A1 ölçümü (salt-okuma): 901 satır / 885 tekil
id / 16 çift (T00096…T00111 aralığı), her çift = TOHUM satırı (küçük seq, 2023-05/06, `plan_id`
`P-2023-…`) + CANLI satır (büyük seq, `plan_id` `P-2026-08-05…09-01-…`). BU SAYILAR BAĞLAMDIR,
GİRDİ DEĞİL — betik hiçbir sayıyı sabitlemez, her koşuda verilen `--db`den TÜRETİR.

NE YAPAR (özet — ayrıntı: `plan_olustur`/`uygula_plan` docstring'leri):
  1. `id` başına birden çok satır bulunan her grupta TOHUM (küçük `seq`) kimliğini KORUR; kalan
     (CANLI, büyük `seq`) satır(lar) mevcut en büyük `T%05d` numarasının ÜSTÜNDEN, TÜM çiftler
     birleştirilip `seq` sırasına göre ARDIŞIK yeni numara alır — iki çift asla aynı numarayı
     paylaşamaz ve yeni numara mevcut hiçbir id ile çakışamaz (inşa + çift doğrulama).
  2. `--kuru` (VARSAYILAN): yalnız planı basar, DB'YE DOKUNMAZ.
  3. `--uygula`: önce DB'nin ÇEVRİMİÇİ YEDEĞİni alır (`sqlite3` backup API — `storage.backup_to`
     ile AYNI gerekçe: WAL modunda dosya kopyalamak eksik/yarışlı olur), sonra TEK transaction'da
     `id`leri günceller (+ `extra_json` içinde `"id"` alanı VARSA onu da), uygulama SONRASI dört
     DEĞİŞMEZİ ölçer (satır sayısı, tekillik, TOHUM satırlarının byte-eşitliği) ve biri bile
     tutmazsa ROLLBACK eder. Başarılıysa eşleme defterine (append-only jsonl) satır yazar.
  4. `--kontrol`: DB'de çift id kalmadı mı VE eşleme defteri DB ile TUTARLI mı (her `yeni_id`
     DB'de var, `eski_id` o `seq`'te yok) — bu, eşleme defterinin YASA-6 OKUYUCUSUDUR.

İZOLASYON (bilinçli tasarım — brief şartı): bu betik `meridian` PAKETİNİ HİÇ İTHAL ETMEZ. Saf
`sqlite3` + `json` + stdlib. Nedeni ikili: (a) `meridian.obs`a ULAŞMAZ, yani canlı yerel deftere
(`state/events.jsonl`) YAZMAZ — betiğin girdisi `--db` argümanıdır, `meridian.config.STATE`
DEĞİL; (b) `meridian.loop`/`meridian.storage` gibi modüller broker/guard/scheduler/adapters'ı da
sürükler ve bu betiğin taşıması gereken YEGÂNE mantık (aşağıdaki `max_trade_num`) üç satırlık
DONMUŞ bir tel biçimidir (`storage.py` `_COLS[TRADES]` şerhi: `T` + TÜM rakamlar, sabit uzunluk
YOK). `max_trade_num` bu yüzden `loop._max_trade_num`ın BİLİNÇLİ bir tekrarıdır (tek-kaynak
yasasına istisna — kopyanın riski, izolasyon şartının kaybından KÜÇÜK): biçim ayrışırsa ölçülür
(brief teslimi bu kararı devretti; ayrışma çivisi açık kalem olarak devir raporunda durur).

LEDGERSTAMP ÖLÇÜMÜ (brief madde 3 — betik teslimi ÖNCESİ okundu, `meridian/ledgerstamp.py`):
damga alanı `FIELD = "kaynak"`tır ve `id` alanını KAPSAMAZ. `stamp`/`classify`/`seed_boundary`
YALNIZ `ts_close` ve VAR OLAN `kaynak` değerine bakar; hiçbiri `id`yi OKUMAZ (görüntüleme dışı —
`_migrate_locked`in `ornek` alanı yalnız RAPOR için `id`yi taşır, hükmü ETKİLEMEZ). Bu betiğin
SQL'i de yalnız `id` (+ koşullu `extra_json`) kolonunu değiştirir, `kaynak` kolonuna HİÇ
DOKUNMAZ. Sonuç: `id` yeniden numaralaması canlı satırların `kaynak` damgasını BOZMAZ — ledger-
stamp'in kendi resmî yolundan yeniden damgalamaya GEREK YOKTUR. (Kapsıyor olsaydı bu betik
etkilenen satırları raporlayıp yeniden damgalamayı `python -m meridian.ledgerstamp`e
DEVREDERDİ — o yol burada YOKTUR çünkü ölçüm "kapsamıyor" dedi.)

WORKER KAPISI YOK (bilinçli — brief madde 4): bu betik `state/` yanında bir kilit/`healthz`
kontrolü YAPMAZ. Rol-1 `--uygula`den ÖNCE canlı worker'ı KENDİSİ durdurur (`./ops/stop-worker.sh`)
— `ledgerstamp.py`/`spend_defter_duzeltmesi.py`nin aksine burada otomatik bir kapı YOKTUR, bunu
YALNIZ bu docstring ve `--uygula` çıktısındaki satır söyler.

KULLANIM:
    python ops/trade_id_yeniden_numarala.py --db state/meridian.db                    # KURU (varsayılan)
    python ops/trade_id_yeniden_numarala.py --db state/meridian.db --kuru             # aynı, açık
    python ops/trade_id_yeniden_numarala.py --db state/meridian.db --uygula \\
        [--eslesme state/trade_id_eslesme.jsonl] [--yedek-dizin backups]              # YAZ
    python ops/trade_id_yeniden_numarala.py --db state/meridian.db --kontrol \\
        [--eslesme state/trade_id_eslesme.jsonl]                                      # DOĞRULA

VARSAYILAN YOLLAR (`--db`nin dizinine göre — brief): `--eslesme` verilmezse
`<db-dizini>/trade_id_eslesme.jsonl`; `--yedek-dizin` verilmezse `<db-dizini>` (A1'de bu `state/`
demektir — Rol-1 ayrı bir yedek köşesi istiyorsa `--yedek-dizin backups` ile aşar).

ÇIKIŞ KODU: 0 = ok (kuru koşu her zaman; uygula/kontrol başarılı ya da yapacak iş yok) ·
1 = doğrulama düştü (uygula → ROLLBACK yapıldı) ya da kontrol tutarsız · 2 = kullanım hatası
(DB yok, `--uygula`+`--kontrol` birlikte).

Çivi: tests/test_trade_id_yeniden_numarala_v424.py
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sqlite3
import sys
from pathlib import Path

BETIK_ADI = "ops/trade_id_yeniden_numarala.py"

# `T` + TÜM rakamlar. UZUNLUK SABİTLENMEZ (`loop._max_trade_num` şerhi, birebir gerekçe): sabit
# `\d{5}` denseydi 100.000. işlemden sonra numara altı haneye taşınca sessizce 0 katkı verirdi.
_ID_DESENI = re.compile(r"^T(\d+)$")


# ---- SAF HESAP (DB'YE DOKUNMAZ) ----------------------------------------------------------------
def max_trade_num(rows: list[dict]) -> int:
    """Verilen satırlardaki en büyük `T00042` biçimli id NUMARASI; hiçbiri uymuyorsa 0.

    `loop._max_trade_num`ın BİLİNÇLİ tekrarıdır — bu dosyanın başlığındaki İZOLASYON gerekçesiyle:
    `meridian.loop`u ithal etmek broker/guard/scheduler/obs'u da sürükler ve bu betiğin "saf
    sqlite3+json, obs'a ULAŞMAZ" şartını kırardı. Biçim (`T` + tüm rakamlar) `storage.py`
    `_COLS[TRADES]` sözleşmesinde DONMUŞ bir tel biçimidir; iki kopyanın ayrışma riski taşıdığı
    tek an biçimin KENDİSİ değişirse olur ve bu, betiğin teslim raporunda AÇIK KALEM olarak durur
    (tek-kaynak yasasına bilinçli istisna, CLAUDE.md §4)."""
    maks = 0
    for r in rows:
        m = _ID_DESENI.match(str(r.get("id") or ""))
        if m:
            n = int(m.group(1))
            if n > maks:
                maks = n
    return maks


def plan_olustur(rows: list[dict]) -> tuple[list[dict], dict]:
    """Çift `id`leri bulur ve yeniden-numaralama PLANINI kurar — DB'ye dokunmaz, SAF fonksiyon.

    Her id GRUBUNDA (aynı `id`yi taşıyan satırlar) TOHUM (en küçük `seq`) kimliğini KORUR; kalan
    (CANLI, büyük `seq`) satırlar TÜM gruplardan BİRLEŞTİRİLİP `seq` sırasına göre sıralanır ve
    mevcut en büyük numaranın (`max_trade_num`) ÜSTÜNDEN ARDIŞIK numara alır — iki AYRI çift asla
    aynı numarayı paylaşmaz (numara havuzu TEK, gruplar arasında PAYLAŞILIR).

    Dönüş: `(plan, ozet)`. `plan`ın her ögesi `{seq, eski_id, yeni_id, plan_id, ticker, ts_open}`
    (seq ARTAN sırada). `ozet`: `{defter_satiri, cift_id_sayisi, yeniden_numaralanacak,
    tohum_seq, mevcut_maks_numara}` — `tohum_seq` DOKUNULMAYACAK (byte-eşit kalması gereken)
    seq'lerin sıralı listesidir; `uygula_plan`in doğrulama anındaki TOHUM anlığı buradan gelir.

    ValueError: üretilen bir `yeni_id` MEVCUT (yeniden-numaralama öncesi) herhangi bir id ile
    çakışırsa — `max_trade_num` doğru hesaplandığı sürece bu asla TETİKLENMEZ (yeni numaralar
    her zaman mevcut maksimumun üstündedir), ama brief'in "doğrulanır" şartı GEREĞİ açıkça
    ölçülür: sessizce çakışan bir plan hiçbir satıra YAZILMADAN reddedilir."""
    gruplar: dict[str, list[dict]] = {}
    for r in rows:
        gruplar.setdefault(r["id"], []).append(r)
    tum_id = {r["id"] for r in rows}
    maks = max_trade_num(rows)

    canli_satirlar: list[dict] = []
    tohum_seq: list[int] = []
    cift_id_n = 0
    for id_, grup in gruplar.items():
        if len(grup) <= 1:
            continue
        cift_id_n += 1
        siral = sorted(grup, key=lambda r: r["seq"])
        tohum_seq.append(siral[0]["seq"])          # TOHUM: en küçük seq, kimliği KORUNUR
        canli_satirlar.extend(siral[1:])            # CANLI: kalanlar, yeniden numaralanacak
    canli_satirlar.sort(key=lambda r: r["seq"])
    tohum_seq.sort()

    plan: list[dict] = []
    sonraki = maks + 1
    for r in canli_satirlar:
        yeni_id = f"T{sonraki:05d}"
        if yeni_id in tum_id:
            raise ValueError(
                f"üretilen kimlik {yeni_id!r} (seq={r['seq']}) ZATEN defterde var — yeniden "
                "numaralama GÜVENSİZ, hiçbir satıra yazılmadı (max_trade_num hesabı yanlış olabilir)")
        plan.append({"seq": r["seq"], "eski_id": r["id"], "yeni_id": yeni_id,
                     "plan_id": r.get("plan_id"), "ticker": r.get("ticker"),
                     "ts_open": r.get("ts_open")})
        sonraki += 1

    ozet = {"defter_satiri": len(rows), "cift_id_sayisi": cift_id_n,
            "yeniden_numaralanacak": len(plan), "tohum_seq": tohum_seq,
            "mevcut_maks_numara": maks}
    return plan, ozet


def extra_json_guncelle(extra_json: str | None, yeni_id: str) -> tuple[str | None, bool]:
    """`extra_json` içinde `"id"` ALANI taşıyan bir satırın o alanını da YENİ kimliğe çevirir.

    Brief madde 2: bu alan storage.py'nin tipli `id` kolonuyla NORMALDE örtüşmez (bir string HER
    ZAMAN TEXT kolonuna sığar, `_matches` asla `extra_json`a düşürmez) — ama betik VARSAYMAZ,
    ÖLÇER: alan varsa günceller, yoksa (ya da `extra_json` None/boş/bozuksa) SATIRA DOKUNMAZ ve
    (None, False) döner — çağıran bu durumda `UPDATE ... SET extra_json=` bile ÇALIŞTIRMAZ."""
    if not extra_json:
        return extra_json, False
    try:
        veri = json.loads(extra_json)
    except json.JSONDecodeError:  # sessiz-yutma: bozuk extra_json bu betiğin KAPSAMI DIŞI — yalnız "id" alanını hedefler, bozuk JSON'u onarmaya kalkışmaz ve satırı OLDUĞU GİBİ bırakır (extra_json'a dokunulmaz)
        return extra_json, False
    if not isinstance(veri, dict) or "id" not in veri:
        return extra_json, False
    veri["id"] = yeni_id
    return json.dumps(veri, ensure_ascii=False), True


# ---- DB OKUMA -----------------------------------------------------------------------------------
def oku_satirlar(conn: sqlite3.Connection) -> list[dict]:
    """`trades` tablosunun plan için gereken beş alanını `seq` sırasıyla okur.

    YALNIZ BU BEŞ KOLON: gerçek `meridian.storage` şeması yaklaşık 30 kolon taşır, sentetik test
    tablosu yalnız bunları taşıyabilir — `SELECT *` her iki dünyada da FARKLI kolon kümesi
    döndürür ve çağıranı şema varsayımına bağlardı."""
    cur = conn.execute("SELECT seq, id, plan_id, ticker, ts_open, extra_json FROM trades ORDER BY seq")
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _tam_satir(conn: sqlite3.Connection, seq: int) -> dict | None:
    """Bir `seq`in TÜM kolonları (`SELECT *`) — TOHUM byte-eşitlik kıyası için (şema NE OLURSA
    OLSUN, gerçek DB'de 30 kolon, sentetik testte 6 — kıyas her iki dünyada da doğru çalışır)."""
    cur = conn.execute("SELECT * FROM trades WHERE seq=?", (seq,))
    cols = [d[0] for d in cur.description]
    row = cur.fetchone()
    return dict(zip(cols, row)) if row is not None else None


def _snapshot(conn: sqlite3.Connection, tohum_seq: list[int]) -> dict:
    """Uygulama ÖNCESİ anlık görüntü: satır sayısı + her TOHUM seq'in TAM satırı. `uygula_plan`
    bu anlığı YAZDIKTAN SONRA tekrar ölçüp kıyaslar (byte-eşitlik değişmezi)."""
    n = conn.execute("SELECT COUNT(*) AS n FROM trades").fetchone()[0]
    return {"row_count": n, "tohum_seq": list(tohum_seq),
            "tohum_rows": {seq: _tam_satir(conn, seq) for seq in tohum_seq}}


# ---- UYGULAMA + DOĞRULAMA (TEK TRANSACTION) ------------------------------------------------------
def _dogrula_sonrasi(conn: sqlite3.Connection, once: dict) -> list[str]:
    """Yazımdan SONRA (henüz COMMIT edilmemiş transaction içinde) dört DEĞİŞMEZİ ölçer. Boş liste
    dönerse `uygula_plan` COMMIT eder; aksi hâlde ROLLBACK."""
    hatalar: list[str] = []
    n_sonra = conn.execute("SELECT COUNT(*) AS n FROM trades").fetchone()[0]
    if n_sonra != once["row_count"]:
        hatalar.append(f"satır sayısı değişmezi KIRILDI: {once['row_count']} → {n_sonra}")
        return hatalar          # satır sayısı kırıksa aşağıdaki kıyaslar anlamsız — erken çık
    n_tekil = conn.execute("SELECT COUNT(DISTINCT id) AS n FROM trades").fetchone()[0]
    if n_tekil != n_sonra:
        hatalar.append(
            f"tekillik değişmezi KIRILDI: {n_tekil} tekil id / {n_sonra} satır — çift id kaldı "
            "ya da yeni bir çakışma üretildi")
    for seq, once_row in once["tohum_rows"].items():
        sonra_row = _tam_satir(conn, seq)
        if sonra_row != once_row:
            hatalar.append(f"TOHUM satırı (seq={seq}) DEĞİŞTİ — byte-eşit kalması gerekiyordu")
    return hatalar


def uygula_plan(conn: sqlite3.Connection, plan: list[dict], once: dict) -> dict:
    """Planı TEK `BEGIN IMMEDIATE…COMMIT/ROLLBACK` transaction'ında uygular.

    SAF UYGULAYICIDIR: planın GÜVENLİĞİNİ (çakışma yok, tohum doğru seçildi) SORGULAMAZ —
    `plan_olustur` zaten bunu inşa anında garanti eder. Bu fonksiyon yalnız YAZAR ve SONUÇTAKİ DB
    durumuna bakarak hükmü verir (`_dogrula_sonrasi`); bu ayrım BİLİNÇLİDİR — testler kasıtlı
    ÇAKIŞAN bir plan verip ROLLBACK'in GERÇEKTEN çalıştığını bu fonksiyonun kendisinde ölçebilir,
    `plan_olustur`un kendi ön-denetimini atlayarak (brief MUTASYON-2: rollback kaldırılırsa
    kırmızı).

    Dönüş: `{ok, hatalar, extra_json_guncellenen}`. `ok=False` ise transaction ROLLBACK edilmiştir
    ve DB, çağrı ÖNCESİYLE bit-bit aynıdır."""
    ext_degisen = 0
    conn.execute("BEGIN IMMEDIATE")
    try:
        for e in plan:
            conn.execute("UPDATE trades SET id=? WHERE seq=?", (e["yeni_id"], e["seq"]))
            row = conn.execute("SELECT extra_json FROM trades WHERE seq=?", (e["seq"],)).fetchone()
            eski_extra = row[0] if row else None
            yeni_extra, degisti = extra_json_guncelle(eski_extra, e["yeni_id"])
            if degisti:
                conn.execute("UPDATE trades SET extra_json=? WHERE seq=?", (yeni_extra, e["seq"]))
                ext_degisen += 1
        hatalar = _dogrula_sonrasi(conn, once)
        if hatalar:
            conn.execute("ROLLBACK")
            return {"ok": False, "hatalar": hatalar, "extra_json_guncellenen": ext_degisen}
        conn.execute("COMMIT")
        return {"ok": True, "hatalar": [], "extra_json_guncellenen": ext_degisen}
    except BaseException:
        conn.execute("ROLLBACK")
        raise


def yedek_al(conn: sqlite3.Connection, db_yolu: Path, yedek_dizin: Path) -> Path:
    """`sqlite3` ÇEVRİMİÇİ YEDEK API'siyle TUTARLI kopya (`storage.backup_to` ile AYNI gerekçe:
    WAL modunda `cp`/`tar` EKSİK ya da YARIŞLI bir kopya verir). Yazımdan hemen sonra AÇILABİLİRLİK
    doğrulanır — sessizce bozuk bir yedek, yedek olmamasından DAHA KÖTÜdür (görünmez gün gelene
    kadar)."""
    yedek_dizin.mkdir(parents=True, exist_ok=True)
    damga = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    hedef = yedek_dizin / f"{db_yolu.name}.{damga}.bak"
    dst = sqlite3.connect(str(hedef))
    try:
        conn.backup(dst)
    finally:
        dst.close()
    dogrula = sqlite3.connect(str(hedef))
    try:
        dogrula.execute("SELECT COUNT(*) FROM trades").fetchone()
    finally:
        dogrula.close()
    return hedef


def eslesme_yaz(yol: Path, plan: list[dict], betik_adi: str = BETIK_ADI) -> None:
    """Eşleme defterine (append-only jsonl) plan satırlarını yazar. Her satır:
    `{seq, eski_id, yeni_id, plan_id, ticker, ts_open, uygulandi_at, betik}`. OKUYUCUSU (YASA 6):
    bu betiğin `--kontrol` alt komutu (`_kontrol_calistir`)."""
    simdi = dt.datetime.now(dt.timezone.utc).isoformat()
    yol.parent.mkdir(parents=True, exist_ok=True)
    with open(yol, "a", encoding="utf-8") as f:
        for e in plan:
            satir = {"seq": e["seq"], "eski_id": e["eski_id"], "yeni_id": e["yeni_id"],
                     "plan_id": e.get("plan_id"), "ticker": e.get("ticker"),
                     "ts_open": e.get("ts_open"), "uygulandi_at": simdi, "betik": betik_adi}
            f.write(json.dumps(satir, ensure_ascii=False, sort_keys=True) + "\n")


# ---- --kontrol: EŞLEME DEFTERİNİN OKUYUCUSU (YASA 6) ---------------------------------------------
def kontrol_et(conn: sqlite3.Connection, eslesme_yolu: Path) -> dict:
    """İki şart: (1) DB'de çift id KALMADI mı, (2) eşleme defteri DB ile TUTARLI mı — her
    `yeni_id` DB'de var VE `eski_id` o `seq`'te YOK. Eşleme dosyası YOKSA (2) kontrolü boş kümede
    VAKUM OLARAK geçer (kontrol edilecek kayıt yok) ama bu SESSİZCE olmaz: `eslesme_var` alanı
    raporda durur — "hiç bakmadım" ile "0 tutarsızlık buldum" burada AYRIŞIR."""
    ciftler = conn.execute(
        "SELECT id, COUNT(*) AS c FROM trades GROUP BY id HAVING c > 1").fetchall()
    hatalar: list[str] = []
    if ciftler:
        hatalar.append(f"DB'de HÂLÂ {len(ciftler)} çift id var: {sorted(r[0] for r in ciftler)}")

    kayitlar: list[dict] = []
    eslesme_var = eslesme_yolu.exists()
    if eslesme_var:
        with open(eslesme_yolu, encoding="utf-8") as f:
            for i, satir in enumerate(f, 1):
                satir = satir.strip()
                if not satir:
                    continue
                try:
                    kayitlar.append(json.loads(satir))
                except json.JSONDecodeError:  # sessiz-yutma: bozuk satır ATLANMAZ — aşağıdaki hatalar listesine ADIYLA girer, kontrol bu yüzden TUTARSIZ döner (uydurma yok: bozuk kaydı "tutarlı" saymak yanlış-yeşil olurdu)
                    hatalar.append(f"eşleme defteri satır {i}: bozuk JSON")

    for k in kayitlar:
        seq, eski, yeni = k.get("seq"), k.get("eski_id"), k.get("yeni_id")
        row = conn.execute("SELECT id FROM trades WHERE seq=?", (seq,)).fetchone()
        guncel = row[0] if row else None
        if guncel is None:
            hatalar.append(f"seq={seq}: DB'de bu seq YOK (eşleme kaydı hayalet)")
            continue
        if guncel != yeni:
            hatalar.append(f"seq={seq}: eşleme yeni_id={yeni!r} ama DB'de id={guncel!r}")
        if guncel == eski:
            hatalar.append(f"seq={seq}: eski_id={eski!r} HÂLÂ DB'DE — yeniden numaralama uygulanmamış görünüyor")
        if not conn.execute("SELECT 1 FROM trades WHERE id=?", (yeni,)).fetchone():
            hatalar.append(f"yeni_id={yeni!r} DB'DE HİÇ YOK (seq={seq})")

    return {"cift_id_sayisi": len(ciftler), "eslesme_dosyasi": str(eslesme_yolu),
            "eslesme_var": eslesme_var, "eslesme_kayit_sayisi": len(kayitlar),
            "hatalar": hatalar, "tutarli": not hatalar}


# ---- CLI --------------------------------------------------------------------------------------
def _varsayilan_yollar(db_yolu: Path, a: argparse.Namespace) -> tuple[Path, Path]:
    """`--eslesme`/`--yedek-dizin` verilmezse İKİSİ DE `--db`nin DİZİNİNE GÖRE türetilir (brief)."""
    eslesme = Path(a.eslesme) if a.eslesme else db_yolu.parent / "trade_id_eslesme.jsonl"
    yedek_dizin = Path(a.yedek_dizin) if a.yedek_dizin else db_yolu.parent
    return eslesme, yedek_dizin


def _kuru_calistir(plan: list[dict], ozet: dict, db_yolu: Path) -> int:
    print("=== trade_id_yeniden_numarala — KURU KOŞU (varsayılan, DB'ye DOKUNULMADI) ===")
    print(f"db: {db_yolu}")
    print(f"defter satırı: {ozet['defter_satiri']} · çift id: {ozet['cift_id_sayisi']} · "
          f"yeniden numaralanacak: {ozet['yeniden_numaralanacak']} · "
          f"mevcut maks numara: {ozet['mevcut_maks_numara']}")
    if not plan:
        print("çift id YOK — yapılacak bir şey yok.")
    else:
        print(f"{'seq':>8}  {'eski_id':10}  {'yeni_id':10}  {'plan_id':32}  ticker")
        for e in plan:
            print(f"{e['seq']:>8}  {str(e['eski_id']):10}  {str(e['yeni_id']):10}  "
                  f"{str(e.get('plan_id')):32}  {e.get('ticker')}")
        print("\nHiçbir şey YAZILMADI. Uygulamak için: --uygula (yedek alınır; bu betik canlı "
              "worker'ın durup durmadığını KENDİSİ KONTROL ETMEZ — Rol-1 önce worker'ı durdurmalı).")
    print(json.dumps({"mod": "kuru", **ozet, "plan": plan}, ensure_ascii=False, indent=1, default=str))
    return 0


def _uygula_calistir(conn: sqlite3.Connection, db_yolu: Path, yedek_dizin: Path,
                     eslesme_yolu: Path, plan: list[dict], ozet: dict) -> int:
    print("=== trade_id_yeniden_numarala — UYGULA ===")
    print(f"db: {db_yolu}")
    if not plan:
        print("çift id YOK — yazılacak bir şey yok (yedek alınmadı, eşleme defterine dokunulmadı).")
        print(json.dumps({"mod": "uygula", "yazildi": False, **ozet}, ensure_ascii=False, indent=1))
        return 0

    yedek = yedek_al(conn, db_yolu, yedek_dizin)
    print(f"yedek: {yedek}")
    once = _snapshot(conn, ozet["tohum_seq"])
    sonuc = uygula_plan(conn, plan, once)

    if not sonuc["ok"]:
        print("\n!! DOĞRULAMA DÜŞTÜ — ROLLBACK yapıldı, DB DEĞİŞMEDİ:", file=sys.stderr)
        for h in sonuc["hatalar"]:
            print(f"   · {h}", file=sys.stderr)
        print(json.dumps({"mod": "uygula", "yazildi": False, "yedek": str(yedek),
                          "hatalar": sonuc["hatalar"], **ozet}, ensure_ascii=False, indent=1, default=str))
        return 1

    eslesme_yaz(eslesme_yolu, plan)
    print(f"eşleme defteri: {eslesme_yolu} (+{len(plan)} satır)")
    print(f"extra_json güncellenen satır: {sonuc['extra_json_guncellenen']}")
    print(f"{ozet['yeniden_numaralanacak']} satır yeniden numaralandı · doğrulama GEÇTİ.")
    print(json.dumps({"mod": "uygula", "yazildi": True, "yedek": str(yedek),
                      "eslesme_defteri": str(eslesme_yolu),
                      "extra_json_guncellenen": sonuc["extra_json_guncellenen"], **ozet},
                     ensure_ascii=False, indent=1, default=str))
    return 0


def _kontrol_calistir(conn: sqlite3.Connection, eslesme_yolu: Path) -> int:
    rapor = kontrol_et(conn, eslesme_yolu)
    print("=== trade_id_yeniden_numarala — KONTROL ===")
    print(f"çift id sayısı: {rapor['cift_id_sayisi']}")
    print(f"eşleme defteri: {eslesme_yolu} "
          f"({'VAR, ' + str(rapor['eslesme_kayit_sayisi']) + ' kayıt' if rapor['eslesme_var'] else 'YOK'})")
    for h in rapor["hatalar"]:
        print(f"  · {h}")
    print("SONUÇ: " + ("TUTARLI" if rapor["tutarli"] else "TUTARSIZ"))
    print(json.dumps(rapor, ensure_ascii=False, indent=1))
    return 0 if rapor["tutarli"] else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python ops/trade_id_yeniden_numarala.py",
        description="16 çift işlem kimliğini yeniden numaralar (TSK-150(b)) — kuru koşu varsayılan")
    ap.add_argument("--db", required=True, help="SQLite işlem defteri yolu (örn. state/meridian.db)")
    ap.add_argument("--kuru", action="store_true", help="yalnız planı bas, DB'ye dokunma (VARSAYILAN davranış)")
    ap.add_argument("--uygula", action="store_true", help="YAZ: yedek al, id'leri yeniden numarala, eşleme defterine yaz")
    ap.add_argument("--kontrol", action="store_true",
                    help="DB'de çift id kaldı mı VE eşleme defteri DB ile tutarlı mı (rc 0/1)")
    ap.add_argument("--eslesme", default=None,
                    help="eşleme defteri jsonl yolu (varsayılan: <db-dizini>/trade_id_eslesme.jsonl)")
    ap.add_argument("--yedek-dizin", default=None,
                    help="yedek DB'nin yazılacağı dizin (varsayılan: <db-dizini>)")
    a = ap.parse_args(argv)

    if a.uygula and a.kontrol:
        print("KULLANIM HATASI: --uygula ve --kontrol birlikte verilemez", file=sys.stderr)
        return 2

    db_yolu = Path(a.db)
    if not db_yolu.exists():
        print(f"DB bulunamadı: {db_yolu}", file=sys.stderr)
        return 2

    eslesme_yolu, yedek_dizin = _varsayilan_yollar(db_yolu, a)

    conn = sqlite3.connect(str(db_yolu))
    try:
        if a.kontrol:
            return _kontrol_calistir(conn, eslesme_yolu)

        rows = oku_satirlar(conn)
        try:
            plan, ozet = plan_olustur(rows)
        except ValueError as e:
            print(f"PLAN KURULAMADI: {e}", file=sys.stderr)
            return 1

        if a.uygula:
            return _uygula_calistir(conn, db_yolu, yedek_dizin, eslesme_yolu, plan, ozet)
        return _kuru_calistir(plan, ozet, db_yolu)
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
