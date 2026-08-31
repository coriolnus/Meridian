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
import argparse, gzip, hashlib, json, struct, sys, time, urllib.request
from pathlib import Path

HIST_API = "https://iextrading.com/api/1.0/hist?date={g}"
NS = 1_000_000_000


def hist_tops_kaydi(gun: str):
    g = gun.replace("-", "")
    with urllib.request.urlopen(HIST_API.format(g=g), timeout=60) as r:
        govde = r.read()
    if not govde.strip():
        raise SystemExit(f"KIRMIZI: HIST API {gun} için boş döndü (tatil/işlem-dışı gün?)")
    for kayit in json.loads(govde):
        if kayit.get("feed") == "TOPS":
            return kayit
    raise SystemExit(f"KIRMIZI: {gun} listesinde TOPS yayını yok")


def indir(url: str, hedef: Path, beklenen_bayt: int):
    if hedef.exists() and hedef.stat().st_size == beklenen_bayt:
        print(f"  ham dosya zaten var ({beklenen_bayt}b) — indirme atlandı")
        return
    h = hashlib.sha256()
    t0 = time.time()
    with urllib.request.urlopen(url, timeout=120) as r, open(hedef, "wb") as f:
        while parca := r.read(1 << 22):
            h.update(parca)
            f.write(parca)
    print(f"  indirildi: {hedef.stat().st_size}b {time.time()-t0:.0f}sn sha256={h.hexdigest()[:16]}…")


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


def ayristir(ham: Path, kok: Path, gun: str, limit_paket: int):
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
                            "spread_1s": 0, "spread_islem_ek": 0, "saat_q": [0] * 24,
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
                    kq = son_kotasyon.get(sym)
                    if kq is None:
                        ty.ekle(ts, sym, fiyat, lot, bayrak, None, None, None, None, None)
                    else:
                        ty.ekle(ts, sym, fiyat, lot, bayrak, kq[0], kq[1], kq[2], kq[3], kq[4])
                        b = bekleyen.get(sym)
                        if b is not None and (kq[3] - kq[1]) != (b[4] - b[2]):
                            k["spread_islem_ek"] += 1
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
    a = ap.parse_args(argv)

    kayit = hist_tops_kaydi(a.gun)
    print(f"GUN={a.gun} TOPS v{kayit['version']} ham={int(kayit['size'])}b")
    if a.kuru:
        return 0
    ham = a.kok / "tick" / "ham" / f"{a.gun}.pcap.gz"
    ham.parent.mkdir(parents=True, exist_ok=True)
    indir(kayit["link"], ham, int(kayit["size"]))
    oz = ayristir(ham, a.kok, a.gun, a.limit_paket)

    ist = oz.pop("ist")
    sayim_yol = a.kok / "tick" / "sayim" / f"{a.gun}.json.gz"
    sayim_yol.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(sayim_yol, "wt", encoding="utf-8") as f:
        json.dump({"gun": a.gun, "ozet": oz, "sembol": ist}, f, ensure_ascii=False)

    man = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "gun": a.gun,
           "kaynak": kayit["link"].split("?")[0], "ham_bayt": int(kayit["size"]),
           "limit_paket": a.limit_paket or None, **oz, "sembol_sayisi": len(ist)}
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
