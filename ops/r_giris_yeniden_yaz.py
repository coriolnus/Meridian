"""EDG-2026-094 ADIM-2 — ölçülen `r_multiple_giris` değerini trades defterine YAZAR (extra_json).

SÖZLEŞME KOMUT SATIRIDIR (CLAUDE.md §1, vaka 2026-08-30) — `main()` değil:

    python ops/r_giris_yeniden_yaz.py --db <defter.db> --olcum <sonuc_09N_*.json> \\
        --yedek-dizin <dizin> (--kuru | --uygula)

(`sonuc_09N_*.json` = ADIM-1 çıktısı; N kartın numarasıdır — 094 ya da 095 kipi.)

KİP BAYRAĞI TEKTİR: ikisi de verilmezse ya da ikisi birden verilirse ÇIKIŞ 2 ve DB'ye
DOKUNULMAZ (dagit sarmalayıcısındaki aynı disiplin — çelişen çift sessizce bir kipi seçmez).

NE YAZAR. Yalnız ölçüm JSON'undaki `olculebildi == true` VE `guven != "dusuk"` satırlara, `seq`
ile adreslenerek, `extra_json` içine üç alan: `r_multiple_giris` (ölçülen yeni R),
`r_giris_kaynak` (qty_giris kaynağı + stop kaynağı) ve `r_giris_damga` (kart kimliği + tarih).
`r_multiple` SÜTUNUNA DOKUNULMAZ — eski değer kalır (operatör kararı, kart kill-list 5).

GÜVEN SÜZGECİ (EDG-2026-095 kill-list 5, ardıl dilim 2026-09-15). `koruma_oco`dan türetilmiş
stop GİRİŞ stop'u olmayabilir; o satırın yeni R'si bir ölçüm değil bir TAHMİNDİR ve defterde
kalıcı alan olarak durursa sonraki kıyasları kirletir (KYS-2026-001). Bu satırlar YAZILMAZ ve
AYRICA SAYILIR — atlananın sayısı stdout'a basılır (bedel yasası: neyi dışarıda bıraktığımız da
ölçülür). Süzgeci kapatan bayrak YOKTUR: "istisna kipi" olsaydı kill-list kalemi tavsiyeye
dönüşürdü.

DEFTER BAĞLAMASI (B1, inceleme bulgusu 2026-09-14). Ölçüm JSON'u hangi defter ANINDA üretildiyse
yazım O ANA uygulanır: `girdi_kunyesi.db.sha256` ile `--db` dosyasının GERÇEK sha256'sı eşit
değilse çıkış 1 ve defter AÇILMAZ (`--kuru`da da). Yalnız `seq`e güvenmek yeterli değildi — seq
başka bir defterde başka bir işlemi gösterir ve yazım sessizce yanlış satıra düşerdi. SONUCU:
ADIM-1 ile ADIM-2 AYNI dosya üzerinde, worker DURMUŞKEN koşar; ölçümü bir kopyada yapıp yazımı
canlı dosyaya denemek bu kapıya takılır (v494 T12 bunu açıkça çiviler). İkinci koşum da yeni bir
ölçüm ister — yazımın kendisi idempotenttir (aynı ölçümle 0 satır), ama bağlama yeniden ölçülür.

NE YAPMAZ. Ölçmez (ölçüm ADIM-1'in işidir), hüküm vermez, `state/` içinde bir yol TAHMİN ETMEZ:
defterin yolu argümandır. Worker'ın durmuş olması ÇAĞIRANIN sorumluluğudur (CLAUDE.md §9).

GÜVENLİK SIRASI. (1) DB dosya kopyası yedeklenir ve yedeğin sha256'sı yan dosyaya yazılır —
YEDEK YAZILAMAZSA HİÇBİR ŞEY YAPILMAZ, çıkış 1. (2) Tek transaction'da yazım. (3) Yazılan satır
sayısı beklenenden farklıysa ROLLBACK + çıkış 1. (4) `r_multiple_giris` zaten duran satır
ATLANIR ve sayılır — ikinci koşum 0 satır yazar (idempotent).

OKUYUCUSU KİM (Yasa 6). Girdi `--olcum` JSON'unu ADIM-1 betiği üretir. Yedek dosyasını ve
sha yan dosyasını geri alım yolunda operatör okur; stdout özetini (yazılan/atlanan/yedek yolu)
Rol-1 dağıtım/bakım kaydına işler. Çıktıların hiçbiri okuyucusuz değildir.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import shutil
import sqlite3
import sys

KART_ID = "EDG-2026-094"

#: DÜŞÜK GÜVEN ETİKETİ — ölçüm betiğindeki `GUVEN["koruma_oco"]` değerinin dizge karşılığı.
#: Bu betik ölçüm modülünü İTHAL EDEMEZ (ayrı dünyalar; ops paket değildir), bu yüzden dizge
#: burada tekrarlanır ve eşitliği v494 T7 iki tarafı birlikte koşturarak ölçer.
DUSUK_GUVEN = "dusuk"


def sha256_dosya(yol) -> str:
    """Dosyanın sha256'sı — yedek yan dosyasının ve testlerin ortak ölçüsü."""
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def damga_metni(bugun: str | None = None) -> str:
    """`r_giris_damga` değeri: kart kimliği + tarih."""
    return f"{KART_ID} {bugun or dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')}"


def kaynak_etiketi(satir: dict) -> str:
    """`r_giris_kaynak`: qty_giris kaynağı ile stop kaynağı BİRLİKTE — biri olmadan diğeri
    satırın nasıl türediğini anlatmaz."""
    return f"{satir.get('qty_giris_kaynak')}+{satir.get('stop_kaynak')}"


def hedefleri_sec(olcum: dict) -> tuple:
    """Ölçüm JSON'undan yazılacak satırlar: `olculebildi == true` VE `guven != "dusuk"`.

    (hedefler, atlanan_dusuk_guven_sayisi) döner — dışlananın SAYISI çağırana verilir, çünkü
    sessizce kısalan bir hedef listesi "zaten o kadardı" diye okunurdu."""
    satirlar = olcum.get("satirlar")
    if not isinstance(satirlar, list):
        raise ValueError("ölçüm JSON'unda `satirlar` listesi yok — yanlış dosya mı?")
    olculen = [s for s in satirlar if s.get("olculebildi") is True]
    hedefler = [s for s in olculen if s.get("guven") != DUSUK_GUVEN]
    return hedefler, len(olculen) - len(hedefler)


def baglama_hatasi(db_yolu: pathlib.Path, olcum: dict):
    """B1: ölçüm JSON'u `--db` dosyasının BU ANINA mı ait? Uymuyorsa hata METNİ, uyuyorsa None.

    Künyede sha256 YOKSA da hata döner: "belki doğrudur" diye geçirmek, ölçülemeyen bir şeyi
    ölçülmüş saymak olurdu (uydurma yasağı)."""
    kunye = olcum.get("girdi_kunyesi")
    kayit = kunye.get("db") if isinstance(kunye, dict) else None
    beklenen = kayit.get("sha256") if isinstance(kayit, dict) else None
    if not beklenen:
        return ("ölçüm JSON'unda `girdi_kunyesi.db.sha256` YOK — bu ölçümün hangi defter anına "
                "ait olduğu ÖLÇÜLEMİYOR, yazım yapılmaz")
    gercek = sha256_dosya(db_yolu)
    if gercek != beklenen:
        return (f"ölçüm başka bir defter anına ait — ölçüm künyesi sha256={beklenen}, "
                f"--db sha256={gercek}. ADIM-1 ile ADIM-2 AYNI dosya üzerinde koşar.")
    return None


def yedekle(db_yolu: pathlib.Path, yedek_dizin: pathlib.Path) -> tuple:
    """DB'nin DOSYA KOPYASI yedeği + sha256 yan dosyası. Başarısızlık ÇAĞIRANA yükselir —
    yedeksiz yazım bu betikte yoktur."""
    yedek_dizin.mkdir(parents=True, exist_ok=True)
    damga = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    hedef = yedek_dizin / f"{db_yolu.name}.{damga}.edg094.bak"
    shutil.copy2(db_yolu, hedef)
    sha = sha256_dosya(hedef)
    yan = pathlib.Path(str(hedef) + ".sha256")
    yan.write_text(f"{sha}  {hedef.name}\n", encoding="utf-8")
    return hedef, yan, sha


def kuru_satirlar(hedefler: list, bugun: str | None = None) -> list:
    """`--kuru` çıktısı: hangi seq'e ne yazılacaktı. HİÇBİR G/Ç yapılmaz."""
    d = damga_metni(bugun)
    return [f"  seq={s.get('seq')} id={s.get('id')} ticker={s.get('ticker')} "
            f"r_multiple_giris={s.get('r_yeni')} r_giris_kaynak={kaynak_etiketi(s)} "
            f"r_giris_damga={d}" for s in hedefler]


def uygula(db_yolu: pathlib.Path, hedefler: list, bugun: str | None = None) -> dict:
    """Tek transaction'da yazım. Sayı tutmazsa ROLLBACK ve hata. `r_multiple` sütununa
    DOKUNULMAZ — güncellenen tek sütun `extra_json`dur."""
    d = damga_metni(bugun)
    con = sqlite3.connect(str(db_yolu))
    con.isolation_level = None          # transaction'ı AÇIKÇA biz yönetiriz
    yazilan = atlanan = 0
    try:
        con.execute("BEGIN IMMEDIATE")
        for s in hedefler:
            seq = s.get("seq")
            sat = con.execute("SELECT extra_json FROM trades WHERE seq = ?", (seq,)).fetchone()
            if sat is None:
                raise RuntimeError(f"ölçümdeki seq={seq} defterde YOK — ölçüm ile defter ayrışmış")
            ham = sat[0]
            extra = json.loads(ham) if ham else {}
            if not isinstance(extra, dict):
                raise RuntimeError(f"seq={seq} extra_json sözlük değil — yazım güvenli değil")
            if "r_multiple_giris" in extra:
                atlanan += 1
                continue
            extra["r_multiple_giris"] = s.get("r_yeni")
            extra["r_giris_kaynak"] = kaynak_etiketi(s)
            extra["r_giris_damga"] = d
            cur = con.execute("UPDATE trades SET extra_json = ? WHERE seq = ?",
                              (json.dumps(extra, ensure_ascii=False), seq))
            yazilan += cur.rowcount
        beklenen = len(hedefler) - atlanan
        if yazilan != beklenen:
            raise RuntimeError(f"yazılan satır ({yazilan}) beklenenden ({beklenen}) FARKLI "
                               f"— geri alındı, defter değişmedi")
        con.execute("COMMIT")
    except BaseException:
        con.execute("ROLLBACK")
        con.close()
        raise
    con.close()
    return {"yazilan": yazilan, "atlanan": atlanan, "hedef": len(hedefler)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=f"{KART_ID} ADIM-2: ölçülen r_multiple_giris'i trades.extra_json'a yazar.")
    ap.add_argument("--db", required=True)
    ap.add_argument("--olcum", required=True, help="ADIM-1 sonuc_094_*.json")
    ap.add_argument("--yedek-dizin", required=True)
    ap.add_argument("--kuru", action="store_true", help="hiçbir yazım yok; ne yazacağını basar")
    ap.add_argument("--uygula", action="store_true", help="yedek al, sonra yaz")
    ap.add_argument("--bugun", default=None, help="damga tarihi (test/yeniden üretim için)")
    a = ap.parse_args(argv)

    if a.kuru == a.uygula:      # ikisi de yok YA DA ikisi birden → kip belirsiz
        print("KİP BELİRSİZ: --kuru ile --uygula'dan TAM BİRİ verilmeli (çelişen çift ya da "
              "eksik bayrak defteri açmaz).", file=sys.stderr)
        return 2

    db_yolu = pathlib.Path(a.db)
    if not db_yolu.exists():
        print(f"defter YOK: {db_yolu}", file=sys.stderr)
        return 1
    with open(a.olcum, "r", encoding="utf-8") as f:
        olcum = json.load(f)

    # B1 — DEFTER BAĞLAMASI: kip bayrağından SONRA, yedekten ÖNCE; kuru koşum da geçer.
    hata = baglama_hatasi(db_yolu, olcum)
    if hata:
        print(f"DEFTER BAĞLAMASI TUTMADI: {hata}", file=sys.stderr)
        return 1

    hedefler, atlanan_dusuk = hedefleri_sec(olcum)

    if a.kuru:
        print(f"KURU KOŞUM — yazım YOK. Hedef satır: {len(hedefler)} "
              f"atlanan_dusuk_guven={atlanan_dusuk}")
        for s in kuru_satirlar(hedefler, a.bugun):
            print(s)
        print(f"db={db_yolu} (yalnız sha256 için okundu) yedek-dizin={a.yedek_dizin} "
              f"(kullanılmadı)")
        return 0

    try:
        yedek, yan, sha = yedekle(db_yolu, pathlib.Path(a.yedek_dizin))
    except OSError as e:
        print(f"YEDEK ALINAMADI ({type(e).__name__}: {e}) — defter AÇILMADI, yazım YOK.",
              file=sys.stderr)
        return 1
    print(f"yedek: {yedek}")
    print(f"yedek_sha256: {sha} ({yan})")

    try:
        sonuc = uygula(db_yolu, hedefler, a.bugun)
    except (RuntimeError, ValueError, sqlite3.Error) as e:
        print(f"YAZIM DURDU ({type(e).__name__}: {e}) — geri alındı. Yedek: {yedek}",
              file=sys.stderr)
        return 1
    print(f"yazilan={sonuc['yazilan']} atlanan={sonuc['atlanan']} hedef={sonuc['hedef']} "
          f"atlanan_dusuk_guven={atlanan_dusuk}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
