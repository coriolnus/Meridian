#!/usr/bin/env python3
"""EDG-2026-066 tick-arşiv pilotu — kart: research/cards/EDG-2026-066-tick-arsiv-pilot.yaml

BİR günün IEX TOPS 1.6 pcap.gz dosyasını indirir, akış hâlinde ayrıştırır ve kartın üç
sorusunu ölçer: (1) boyut — ham/Parquet bayt; (2) yoğunluk — sembol×saat kotasyon/işlem
sayıları; (3) seyreltme bedeli — 1/sn ızgaranın kaçırdığı spread değişimleri ve işlem-anı
anlık görüntünün telafisi. Ham dosya varsayılan olarak SİLİNİR (Yasa 6 okuyucuları: kartın
hüküm alanı + pilot raporu; kalıcı artefakt yalnız Parquet + sayim + manifest).

Tasarım notu (karta beyanlı sapma): islem_ani_kotasyon AYRI dosya değil, islem tablosunun
anlık-görüntü SÜTUNLARIdır (alis/satis fiyat-lot + kotasyon_ts) — aynı bilgi, bir birleşim
eksik. Parquet TÜM piyasayı içerir; kapsam (S&P500+NDX) projeksiyonu ayrıştırma SONRASI
DuckDB süzmesiyle ölçülür — kapsam listesi ayrıştırıcıya gömülmez (tek-kaynak: liste ayrı
dosyada yaşar, süzme her listeyle tekrarlanabilir).

Sözleşme KOMUT SATIRIdır:
  pilot.py --gun 2020-09-15 [--kok /opt/veri] [--tut-ham] [--limit-paket N] [--kuru]

Çıktılar ($KOK/tick/ altında):
  kotasyon_1s/GUN.parquet   sembol-saniye son kotasyonu (fiyatlar 1e-4 tamsayı birim)
  islem/GUN.parquet         tüm işlemler + işlem-anı kotasyon anlık görüntüsü
  sayim/GUN.json.gz         sembol başına yoğunluk, seyreltme bedeli, işlemlerden OHLC (PK girdisi)
  manifest.jsonl            gün başına tek satır: kaynak url/sha256/bayt, satır sayıları, süre
"""
import argparse, gzip, hashlib, json, struct, sys, time, urllib.error, urllib.request
from pathlib import Path

HIST_API = "https://iextrading.com/api/1.0/hist?date={g}"
NS = 1_000_000_000


def hist_tops_kaydi(gun: str):
    g = gun.replace("-", "")
    try:
        with urllib.request.urlopen(HIST_API.format(g=g), timeout=60) as r:
            govde = r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # HIST, yayımlanmamış taze günde boş liste DEĞİL 404 döndürüyor (ölçüldü 2026-09-01:
            # 2026-08-31→404, 08-14/08-17→200). Sürücünün boş-gün sözlüğüyle ("boş döndü") konuş —
            # taze/tatil ayrımı sürücüde; 404 dışındaki HTTP hataları gürültülü kalır.
            raise SystemExit(f"KIRMIZI: HIST API {gun} için boş döndü (HTTP 404 — kayıt yok)")
        raise
    if not govde.strip():
        raise SystemExit(f"KIRMIZI: HIST API {gun} için boş döndü (tatil/işlem-dışı gün?)")
    for kayit in json.loads(govde):
        if kayit.get("feed") == "TOPS":
            return kayit
    # Taze günde HIST listesi TOPS'suz da gelebiliyor (kısmî/aşamalı yayın — ölçüldü 2026-09-01:
    # 08-31 önce 404, sonra TOPS'suz 200 verdi). 404 ile aynı sınıf: sürücünün boş-gün
    # sözlüğüyle konuş; taze→koşum-içi atla, eski→gecilen.jsonl tatil kaydı (görünür artefakt).
    raise SystemExit(f"KIRMIZI: HIST API {gun} için boş döndü (listede TOPS yayını yok)")


class KesikIndirme(RuntimeError):
    """İnen bayt sayısı HIST'in bildirdiği boyutla uyuşmadı (TSK-107, vaka 2026-09-02 07:08Z).

    O vakada kesik gz sessizce diske yazıldı, ~8 dk ayrıştırma CPU'sundan SONRA gzip
    `EOFError` ile patladı ve arıza YANLIŞ ADLA (gzip iç hatası gibi) göründü. Bu sınıf
    arızayı doğduğu yerde ve doğru adla söyler; yarım dosya önbellekte BIRAKILMAZ."""


def _boyut_uyar(hedef: Path, beklenen_bayt):
    """Tek kaynak: hem önbellek kapısı hem indirme-sonrası doğrulama BUNU çağırır — aynı
    gerçeğin iki kopyası sessizce ayrışır (tek-kaynak yasası).

    True = boyut tuttu · False = tutmadı · None = HÜKÜM YOK (beklenen bilinmiyor). Üçüncü
    hâl uydurma yasağıdır: 'bilmiyorum' ile 'eşit değil' aynı şey değildir."""
    if not beklenen_bayt:
        return None
    if not hedef.exists():
        return False
    return hedef.stat().st_size == beklenen_bayt


def indir(url: str, hedef: Path, beklenen_bayt: int):
    if _boyut_uyar(hedef, beklenen_bayt) is None:
        # Yasa 6: kıyasın ATLANDIĞI görünür olmalı — sessiz atlama, geçmiş kıyastan
        # ayırt edilemez. Çağrı başına bir kez (iki kapı da aynı yardımcıdan besleniyor).
        print(f"  NOT: beklenen boyut bilinmiyor ({beklenen_bayt!r}) — boyut kıyası atlandı "
              f"(önbellek kapısı da, indirme-sonrası doğrulama da)")
    elif _boyut_uyar(hedef, beklenen_bayt):
        print(f"  ham dosya zaten var ({beklenen_bayt}b) — indirme atlandı")
        return
    h = hashlib.sha256()
    t0 = time.time()
    with urllib.request.urlopen(url, timeout=120) as r, open(hedef, "wb") as f:
        while parca := r.read(1 << 22):
            h.update(parca)
            f.write(parca)
    inen = hedef.stat().st_size
    if _boyut_uyar(hedef, beklenen_bayt) is False:
        hedef.unlink()   # yarım gz önbellekte kalırsa sonraki tur yine EOFError'a yürür
        raise KesikIndirme(f"KIRMIZI: kesik indirme {hedef.name} {inen}/{beklenen_bayt} bayt")
    print(f"  indirildi: {inen}b {time.time()-t0:.0f}sn sha256={h.hexdigest()[:16]}…")


def paketler(f):
    """Yakalama akışından ham Ethernet çerçeveleri üretir. İEX arşivi pcapng'dir (ölçüldü
    2026-08-31, duman testi: sihir 0a0d0d0a); klasik pcap da desteklenir. Tek-bölümlü pcapng
    varsayılır — bölüm ortasında ikinci SHB gelirse uzunluk alanı yanlış çözülür ve yürüyüş
    gürültüyle kırılır (sessiz atlama YOKTUR)."""
    bas = f.read(4)
    if len(bas) < 4:
        return
    if bas == b"\x0a\x0d\x0d\x0a":                      # pcapng Bölüm Başlığı Bloğu
        tlen_ham, bom = f.read(4), f.read(4)
        if bom == b"\x4d\x3c\x2b\x1a":
            uc = "<"
        elif bom == b"\x1a\x2b\x3c\x4d":
            uc = ">"
        else:
            raise SystemExit(f"KIRMIZI: pcapng bayt-sırası sihri tanınmadı: {bom.hex()}")
        f.read(struct.unpack(uc + "I", tlen_ham)[0] - 12)   # SHB'nin kalanı
        blok = struct.Struct(uc + "II")
        cap_oku = struct.Struct(uc + "I")
        while True:
            b8 = f.read(8)
            if len(b8) < 8:
                return
            btip, btlen = blok.unpack(b8)
            govde = f.read(btlen - 8)
            if len(govde) < btlen - 8:
                return
            if btip == 6:                               # Enhanced Packet Block
                cap = cap_oku.unpack_from(govde, 12)[0]  # iface(4)+ts(8) sonrası captured_len
                yield govde[20:20 + cap]
    else:                                               # klasik pcap (24 bayt başlık)
        bas += f.read(20)
        if struct.unpack("<I", bas[:4])[0] in (0xA1B2C3D4, 0xA1B23C4D):
            uc = "<"
        elif struct.unpack(">I", bas[:4])[0] in (0xA1B2C3D4, 0xA1B23C4D):
            uc = ">"
        else:
            raise SystemExit(f"KIRMIZI: yakalama biçimi tanınmadı: {bas[:4].hex()}")
        rec = struct.Struct(uc + "IIII")
        while True:
            rb = f.read(16)
            if len(rb) < 16:
                return
            _, _, dahil, _ = rec.unpack(rb)
            veri = f.read(dahil)
            if len(veri) < dahil:
                return
            yield veri


class ParquetYazici:
    """pyarrow ParquetWriter sarmalayıcısı — satırlar bellekte birikmez, parça parça basılır."""

    def __init__(self, yol: Path, alanlar):
        import pyarrow as pa
        import pyarrow.parquet as pq
        self._pa, self._alanlar = pa, alanlar
        self._sema = pa.schema(alanlar)
        self._w = pq.ParquetWriter(yol, self._sema, compression="zstd")
        self._sutun = [[] for _ in alanlar]
        self.satir = 0

    def ekle(self, *degerler):
        for i, d in enumerate(degerler):
            self._sutun[i].append(d)
        self.satir += 1
        if self.satir % 2_000_000 == 0:
            self._bas()

    def _bas(self):
        if self._sutun[0]:
            t = self._pa.table(
                {ad: self._pa.array(s, tip) for (ad, tip), s in zip(self._alanlar, self._sutun)})
            self._w.write_table(t)
            self._sutun = [[] for _ in self._alanlar]

    def kapat(self):
        self._bas()
        self._w.close()


def ayristir(ham: Path, kok: Path, gun: str, limit_paket: int, kapsam=None):
    """kapsam=None → tüm piyasa Parquet'e yazılır (pilot davranışı). kapsam=set(sembol) →
    Parquet YALNIZ kapsamı yazar (geri-dolum programı; boyut sözleşmesi kapsam-süzgeçlidir),
    sayım tablosu (q/t/hacim/saatlik/ohlc) HER ZAMAN tüm piyasayı sayar — kartın 'yoğunluk
    tablosu bedava' değeri korunur. q1s/spread_1s sayaçları ızgara-emisyonuna bağlı olduğu
    için kapsamlı koşumda yalnız kapsam için anlamlıdır."""
    import pyarrow as pa
    ts64, s32, u8 = pa.int64(), pa.int32(), pa.uint8()
    metin = pa.string()
    q_yol = kok / "tick" / "kotasyon_1s" / f"{gun}.parquet"
    t_yol = kok / "tick" / "islem" / f"{gun}.parquet"
    for y in (q_yol, t_yol):
        y.parent.mkdir(parents=True, exist_ok=True)
    qy = ParquetYazici(q_yol, [("ts", ts64), ("sembol", metin), ("alis_fiyat", ts64),
                               ("alis_lot", s32), ("satis_fiyat", ts64), ("satis_lot", s32)])
    ty = ParquetYazici(t_yol, [("ts", ts64), ("sembol", metin), ("fiyat", ts64), ("lot", s32),
                               ("kosul", u8), ("k_ts", ts64), ("k_alis_fiyat", ts64),
                               ("k_alis_lot", s32), ("k_satis_fiyat", ts64), ("k_satis_lot", s32)])

    bekleyen = {}      # sembol -> [saniye, ts, af, al, sf, sl]  (1/sn ızgara adayı)
    son_kotasyon = {}  # sembol -> (ts, af, al, sf, sl)          (işlem-anı anlık görüntü)
    son_spread = {}    # sembol -> spread                         (ham spread-değişim sayacı)
    ist = {}           # sembol -> istatistik sözlüğü

    def kayit(sym):
        k = ist.get(sym)
        if k is None:
            k = ist[sym] = {"q": 0, "q1s": 0, "t": 0, "hacim": 0, "spread_degisim": 0,
                            "spread_1s": 0, "saat_q": [0] * 24,
                            "saat_t": [0] * 24, "ohlc": None}
        return k

    qup = struct.Struct("<Bq8sIqqI").unpack_from   # QuoteUpdate: flags ts sembol al af sf sl
    tup = struct.Struct("<Bq8sIqq").unpack_from    # TradeReport: flags ts sembol lot fiyat id

    paket = mesaj = 0
    t0 = time.time()
    with gzip.open(ham, "rb") as f:
        for veri in paketler(f):
            paket += 1
            if limit_paket and paket > limit_paket:
                break
            # Ethernet(14)+IPv4(IHL)+UDP(8) -> IEX-TP başlığı(40) -> len-önekli mesajlar
            if len(veri) < 60 or veri[12:14] != b"\x08\x00":
                continue
            ip_bas = 14 + ((veri[14] & 0x0F) << 2)
            yuk = memoryview(veri)[ip_bas + 8:]
            if len(yuk) < 40:
                continue
            adet = struct.unpack_from("<H", yuk, 14)[0]
            poz = 40
            for _ in range(adet):
                mlen = struct.unpack_from("<H", yuk, poz)[0]
                m = yuk[poz + 2: poz + 2 + mlen]
                poz += 2 + mlen
                tip = m[0]
                mesaj += 1
                if tip == 0x51 and mlen >= 42:      # 'Q' kotasyon — tip baytı atlanır (ofset 1)
                    _, ts, sraw, al, af, sf, sl = qup(m, 1)
                    sym = sraw.rstrip().decode("ascii", "replace")
                    k = kayit(sym)
                    k["q"] += 1
                    k["saat_q"][(ts // NS % 86400) // 3600] += 1
                    sp = sf - af
                    if son_spread.get(sym) != sp:
                        son_spread[sym] = sp
                        k["spread_degisim"] += 1
                    son_kotasyon[sym] = (ts, af, al, sf, sl)
                    if kapsam is None or sym in kapsam:
                        sn = ts // NS
                        b = bekleyen.get(sym)
                        if b is not None and b[0] != sn:
                            qy.ekle(b[1], sym, b[2], b[3], b[4], b[5])
                            k["q1s"] += 1
                            if (b[4] - b[2]) != (sf - af):
                                k["spread_1s"] += 1
                        bekleyen[sym] = [sn, ts, af, al, sf, sl]
                elif tip == 0x54 and mlen >= 38:    # 'T' işlem — tip baytı atlanır (ofset 1)
                    bayrak, ts, sraw, lot, fiyat, _ = tup(m, 1)
                    sym = sraw.rstrip().decode("ascii", "replace")
                    k = kayit(sym)
                    k["t"] += 1
                    k["hacim"] += lot
                    k["saat_t"][(ts // NS % 86400) // 3600] += 1
                    if kapsam is None or sym in kapsam:
                        kq = son_kotasyon.get(sym)
                        if kq is None:
                            ty.ekle(ts, sym, fiyat, lot, bayrak, None, None, None, None, None)
                        else:
                            ty.ekle(ts, sym, fiyat, lot, bayrak, kq[0], kq[1], kq[2], kq[3], kq[4])
                        # işlem-anı ek-yakalama SAYACI YOK: akış-içi sayaç totolojik çıktı
                        # (bekleyen ve son_kotasyon aynı mesajla güncellenir — kıyas hep eşit,
                        # 0 ölçtü; vaka EDG-066 hükmü). Gerçek ölçüm Parquet'ten ASOF join'le
                        # yapılır (islem.k_* ↔ kotasyon_1s) — tek kaynak odur, kopya sayaç yasak.
                    o = k["ohlc"]
                    if o is None:
                        k["ohlc"] = [fiyat, fiyat, fiyat, fiyat, ts, ts]
                    else:
                        o[1] = max(o[1], fiyat)
                        o[2] = min(o[2], fiyat)
                        if ts >= o[5]:
                            o[3], o[5] = fiyat, ts
            if paket % 5_000_000 == 0:
                print(f"  … paket={paket} mesaj={mesaj} q_satir={qy.satir} "
                      f"t_satir={ty.satir} {time.time()-t0:.0f}sn", flush=True)
    for sym, b in bekleyen.items():   # gün sonu: her sembolün son saniyesi de basılır
        qy.ekle(b[1], sym, b[2], b[3], b[4], b[5])
        ist[sym]["q1s"] += 1
    qy.kapat()
    ty.kapat()
    return {"paket": paket, "mesaj": mesaj, "q_satir": qy.satir, "t_satir": ty.satir,
            "sure_sn": round(time.time() - t0, 1), "ist": ist,
            "q_bayt": q_yol.stat().st_size, "t_bayt": t_yol.stat().st_size}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--gun", required=True, help="YYYY-MM-DD")
    ap.add_argument("--kok", default="/opt/veri", type=Path)
    ap.add_argument("--tut-ham", action="store_true", help="ham gz dosyasını SİLME")
    ap.add_argument("--limit-paket", type=int, default=0, help="duman testi: N paketten sonra dur")
    ap.add_argument("--kuru", action="store_true", help="yalnız HIST kaydını göster, indirme yok")
    ap.add_argument("--kapsam", type=Path, default=None,
                    help="sembol listesi dosyası (satır başına bir sembol, # yorum); "
                         "verilirse Parquet YALNIZ bu kapsamı yazar, sayım tüm piyasayı sayar")
    a = ap.parse_args(argv)

    kapsam = None
    if a.kapsam is not None:
        kapsam = {s.strip().upper() for s in a.kapsam.read_text().splitlines()
                  if s.strip() and not s.strip().startswith("#")}
        if not kapsam:
            raise SystemExit(f"KIRMIZI: kapsam dosyası boş: {a.kapsam}")

    kayit = hist_tops_kaydi(a.gun)
    print(f"GUN={a.gun} TOPS v{kayit['version']} ham={int(kayit['size'])}b")
    if a.kuru:
        return 0
    ham = a.kok / "tick" / "ham" / f"{a.gun}.pcap.gz"
    ham.parent.mkdir(parents=True, exist_ok=True)
    try:
        indir(kayit["link"], ham, int(kayit["size"]))
    except KesikIndirme as e:
        # inceleme Minor-2 (2026-09-03): journald'e ham traceback düşmesin — arıza TEK satırda
        # ve doğru adıyla okunur. Sınıflama DEĞİŞMEZ: satır "kesik indirme" taşır, geri-dolum
        # sürücüsü (_ariza_sinifi) onu aynı şekilde tanır. Yarım gz'yi indir() zaten sildi.
        print(e, flush=True)
        return 1
    oz = ayristir(ham, a.kok, a.gun, a.limit_paket, kapsam)

    ist = oz.pop("ist")
    sayim_yol = a.kok / "tick" / "sayim" / f"{a.gun}.json.gz"
    sayim_yol.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(sayim_yol, "wt", encoding="utf-8") as f:
        json.dump({"gun": a.gun, "ozet": oz, "sembol": ist}, f, ensure_ascii=False)

    man = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "gun": a.gun,
           "kaynak": kayit["link"].split("?")[0], "ham_bayt": int(kayit["size"]),
           "limit_paket": a.limit_paket or None,
           "kapsam": str(a.kapsam) if a.kapsam else None,
           "kapsam_n": len(kapsam) if kapsam else None,
           **oz, "sembol_sayisi": len(ist)}
    with (a.kok / "tick" / "manifest.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(man, ensure_ascii=False) + "\n")

    if not a.tut_ham:
        ham.unlink()
        print("  ham dosya silindi (kart: kalıcı artefakt yalnız Parquet+sayım)")
    print(f"OZET gun={a.gun} mesaj={oz['mesaj']} kotasyon_1s={oz['q_satir']} islem={oz['t_satir']} "
          f"parquet={(oz['q_bayt']+oz['t_bayt'])//(1<<20)}MiB sure={oz['sure_sn']}sn")
    return 0


if __name__ == "__main__":
    sys.exit(main())
