"""EDG-2026-067 TABAN KOLU — korpus → chunk → bge-m3 ONNX gömme → sqlite-vec indeksi.

NE OLDUĞU. Kart `research/cards/EDG-2026-067-hindsight-faz1-bgem3-recall.yaml` Hindsight
recall'unu MİNİMAL TABAN ÇİZGİye karşı koyar. Bu betik o taban çizgidir: aynı korpus, aynı
soru kümesi, aynı embedder sınıfı — üstüne yalın bir vektör indeksinden başka HİÇBİR ŞEY yok
(reranker yok, BM25 yok, graf yok, zamansal ağırlık yok). Fark ölçülen şeydir.

ADALET ŞARTI (kart, `hipotez`): "AYNI embedder sınıfı". A1'deki canlı Hindsight kurulumu
bge-m3 ONNX'i şu ayarlarla koşar (kart `kurulum_kayitlari.yukseltme_2026_09_01`):
MODEL_ID=BAAI/bge-m3 · DIMENSIONS=1024 · POOLING=cls · PREFIX'ler BOŞ · MAX_TOKENS=512.
Buradaki varsayılanlar o kayıttan TÜRETİLDİ, uydurulmadı — biri değişirse kıyas adil değildir.
`sentence-transformers` BİLEREK kullanılmaz: canlı taraf ONNX koşuyor, taban da ONNX koşar.

KOŞUM YERİ A1, ROL-1. Bu betik `meridian` paketinden HİÇBİR ŞEY import etmez ve `meridian.obs`a
ulaşmaz — pytest dışı koşumun canlı yerel deftere yazma sınıfı (3 vaka, 2026-08-30) böyle
kapatılır. Ağır paketler (`onnxruntime`, `tokenizers`, `sqlite_vec`, `numpy`) TEMBEL import
edilir: çiviler onları kurmadan da koşar ve `--kollar hindsight` turu model dizini istemez.

KULLANIM
    python taban_indeks.py --paket <manifest_uret.py çıktısı> --model-dir <bge-m3 onnx dizini> \
                           --db /opt/hindsight/edg067/taban.sqlite
"""
import argparse
import json
import pathlib
import re
import sqlite3
import struct
import time

#: Canlı Hindsight kurulumundan TÜRETİLEN gömme sözleşmesi (kart kurulum kaydı, 2026-09-01).
#: Kill maddesi "embedding boyutu 1024 doğrulanmadan başlayan ingest geçersiz" tabanda da geçerli.
BOYUT = 1024
MAX_TOKEN = 512

#: Chunk'lama sözleşmesi (brief 2026-09-01). Örtüşme, `sorular.yaml`daki en uzun `dogrulama`
#: alıntısından (95 karakter, ölçüldü) BÜYÜK seçildi: sınırı kesen her alıntı komşu pencerede
#: BÜTÜN kalır, yoksa hakem kuralı (b) modelden değil ölçüm hatasından düşerdi.
PENCERE = 1500
ORTUSME = 200

#: Markdown başlığı: satır başında bir-üç `#` + boşluk. `####` (ROADMAP'te 74 kez) bölmez —
#: her maddeyi kendi başına bırakmak bağlamı yok ederdi.
_BASLIK = re.compile(r"^(#{1,3})[ \t]+(\S.*?)[ \t]*$")
_CIT = ("```", "~~~")

#: `manifest_uret.py` ROADMAP §7 kesitini `ROADMAP.md%237` document_id'siyle paketler
#: (`%23` = `#`). Soru kümesi beklenen dosyayı `ROADMAP.md` diye yazar.
KESIT_AYIRACI = "%23"


# =================================================================================================
# BELGE KİMLİĞİ
# =================================================================================================
def dokuman_taban(document_id):
    """Kesit ekini soyar: `ROADMAP.md%237` → `ROADMAP.md`. İki kolda da AYNI uygulanır."""
    return str(document_id).split(KESIT_AYIRACI, 1)[0]


def markdown_mi(document_id):
    """Uzantı bakışı KESİT EKİNDEN SONRA yapılır — `Path("ROADMAP.md%237").suffix` `.md%237`dir
    ve ham bakış §7 kesitini markdown saymaz."""
    return dokuman_taban(document_id).casefold().endswith(".md")


# =================================================================================================
# CHUNK'LAMA
# =================================================================================================
def bolumlere_ayir(metin):
    """[(başlık, gövde)] — `#`/`##`/`###` sınırlarında, kod çitleri KORUNARAK.

    Başlık satırı GÖVDENİN İÇİNDE kalır: hakem kuralı (b) dönen sonucun metninde bölüm
    başlığını arar; başlık gövdeden düşerse taban kolu o kriteri hiç geçemezdi.

    İlk başlıktan önceki metin `""` başlıklı bir önsöz bölümüdür (atılmaz — dosya künyeleri
    ve özetler orada yaşar).
    """
    satirlar = metin.split("\n")
    cit_acik = False
    sinirlar = []
    basliklar = {}
    for i, satir in enumerate(satirlar):
        if satir.lstrip().startswith(_CIT):
            cit_acik = not cit_acik
            continue
        if cit_acik:
            continue                      # çit içindeki `# ...` kabuk yorumudur, başlık değil
        m = _BASLIK.match(satir)
        if m:
            sinirlar.append(i)
            basliklar[i] = m.group(2)

    if not sinirlar:
        return [("", metin)] if metin.strip() else []

    parcalar = []
    if sinirlar[0] > 0:
        onsoz = "\n".join(satirlar[:sinirlar[0]])
        if onsoz.strip():
            parcalar.append(("", onsoz))
    for sira, bas in enumerate(sinirlar):
        son = sinirlar[sira + 1] if sira + 1 < len(sinirlar) else len(satirlar)
        parcalar.append((basliklar[bas], "\n".join(satirlar[bas:son])))
    return parcalar


def kayan_pencere(metin, pencere=PENCERE, ortusme=ORTUSME):
    """Uzun bölümü sabit pencere + sabit örtüşmeyle alt-parçalar. SON pencere metnin SONUNDA
    biter — bitmeseydi her bölümün kuyruğu sessizce indekslenmezdi."""
    if not 0 <= ortusme < pencere:
        raise ValueError(f"örtüşme pencereden KÜÇÜK olmalı: pencere={pencere} örtüşme={ortusme}")
    if len(metin) <= pencere:
        return [metin]
    adim = pencere - ortusme
    parcalar = []
    bas = 0
    while True:
        parcalar.append(metin[bas:bas + pencere])
        if bas + pencere >= len(metin):
            return parcalar
        bas += adim


def chunkla(dosya_yolu, metin, blob_sha, *, pencere=PENCERE, ortusme=ORTUSME):
    """Bir belgenin chunk'ları: (dosya_yolu, bolum_basligi, metin, blob_sha).

    BAŞLIK KURALI YALNIZ MARKDOWN'A UYGULANIR. Korpustaki 80 kart `.yaml`dır ve oradaki
    `# ...` satırı YORUMDUR (kart başlarında 9 ardışık yorum satırı — ölçüldü). Markdown
    kuralını onlara uygulamak her yorumu tek satırlık bir chunk'a çevirir ve TABAN KOLUNU
    kendi aleyhine zayıflatırdı; ölçümün yönü buna duyarlıdır.

    Gömülen metin ham pencere metnidir: bölüm başlığı alt-parçalara AYRICA EKLENMEZ. Eklenseydi
    hakem kuralı (b) taban kolunda otomatik geçerdi (başlık her pencerede bulunurdu) — sayım
    şişer, kıyas bozulurdu.
    """
    bolumler = bolumlere_ayir(metin) if markdown_mi(dosya_yolu) else (
        [("", metin)] if metin.strip() else [])
    chunklar = []
    for baslik, govde in bolumler:
        for parca in kayan_pencere(govde, pencere, ortusme):
            if not parca.strip():
                continue
            chunklar.append({"dosya_yolu": dosya_yolu, "bolum_basligi": baslik,
                             "metin": parca, "blob_sha": blob_sha})
    return chunklar


# =================================================================================================
# KORPUS
# =================================================================================================
def manifest_oku(paket_dizini):
    """`manifest_uret.py` çıktısındaki `manifest.json` — şema DOĞRULANARAK."""
    yol = pathlib.Path(paket_dizini) / "manifest.json"
    if not yol.exists():
        raise FileNotFoundError(f"manifest YOK: {yol} (önce manifest_uret.py koşulmalı)")
    manifest = json.loads(yol.read_text(encoding="utf-8"))
    if not manifest.get("head_commit"):
        raise ValueError(f"{yol}: `head_commit` yok — korpusun provenansı ölçülemez")
    dosyalar = manifest.get("dosyalar")
    if not dosyalar:
        raise ValueError(f"{yol}: `dosyalar` boş")
    for kayit in dosyalar:
        eksik = [alan for alan in ("yol", "blob", "bayt") if alan not in kayit]
        if eksik:
            raise ValueError(f"{yol}: manifest kaydında eksik alan {eksik}: {kayit}")
    return manifest


def korpus_chunklari(paket_dizini, *, pencere=PENCERE, ortusme=ORTUSME):
    """(manifest, chunk listesi). Her dosyanın BAYT BOYUTU manifestle karşılaştırılır —
    kill maddesi "taban çizgi AYNI korpusla koşmazsa kıyas geçersiz" burada ölçülür."""
    paket = pathlib.Path(paket_dizini)
    manifest = manifest_oku(paket)
    chunklar = []
    for kayit in manifest["dosyalar"]:
        yol = paket / "korpus" / kayit["yol"]
        if not yol.exists():
            raise FileNotFoundError(f"korpus dosyası YOK: {yol} (manifestte var)")
        ham = yol.read_bytes()
        if len(ham) != kayit["bayt"]:
            raise ValueError(
                f"KORPUS AYRIŞTI: {kayit['yol']} manifestte {kayit['bayt']} bayt, diskte "
                f"{len(ham)} bayt — Hindsight'a giden korpusla taban korpusu AYNI DEĞİL")
        chunklar.extend(chunkla(kayit["yol"], ham.decode("utf-8"), kayit["blob"],
                                pencere=pencere, ortusme=ortusme))
    return manifest, chunklar


# =================================================================================================
# GÖMME — bge-m3 ONNX (cls havuzlama, L2 normalize, prefix YOK)
# =================================================================================================
def cls_havuzla(son_gizli):
    """[B, T, H] → [B, H]: İLK token. Canlı kurulum POOLING=cls (kart kurulum kaydı) —
    ortalama havuzlama başka bir vektör uzayı üretir ve kıyası adaletsiz kılar."""
    return son_gizli[:, 0, :]


def l2_normalize(vektorler):
    """Satır bazında birim uzunluk. Sıfır vektör 0'a bölünmez (NaN sessizce yayılırdı)."""
    norm = (vektorler * vektorler).sum(axis=-1, keepdims=True) ** 0.5
    norm = norm.copy()
    norm[norm == 0] = 1.0
    return vektorler / norm


def boyut_dogrula(vektorler, boyut=BOYUT):
    """Kill maddesinin taban tarafı: 1024 dışındaki bir çıktı vec0 şemasına sessizce sığmaz."""
    gercek = int(vektorler.shape[-1])
    if gercek != boyut:
        raise ValueError(f"gömme boyutu {gercek}, beklenen {boyut} — model/şema ayrışmış")
    return vektorler


class OnnxGomucu:
    """bge-m3 ONNX gömücüsü. `onnxruntime` + `tokenizers` TEMBEL import edilir."""

    #: Aranan ONNX yolları — SIRA ÖNEMLİ (nicelenmiş sürüm ASLA otomatik seçilmez: canlı taraf
    #: tam duyarlıklı koşuyor, nicelenmişi seçmek adalet şartını sessizce kırardı).
    ONNX_ADAYLARI = ("onnx/model.onnx", "model.onnx", "onnx/model_fp16.onnx")

    def __init__(self, model_dir, *, boyut=BOYUT, max_token=MAX_TOKEN):
        self.model_dir = pathlib.Path(model_dir)
        self.boyut = boyut
        self.max_token = max_token
        if not self.model_dir.is_dir():
            raise FileNotFoundError(f"model dizini YOK: {self.model_dir}")
        self.onnx_yolu = self._onnx_bul()
        self.tokenizer_yolu = self.model_dir / "tokenizer.json"
        if not self.tokenizer_yolu.exists():
            raise FileNotFoundError(
                f"tokenizer.json YOK: {self.tokenizer_yolu} — bge-m3 snapshot'ı eksik indirilmiş "
                f"olabilir; A1'deki canlı model dizinini göster")
        import onnxruntime
        import tokenizers
        self.oturum = onnxruntime.InferenceSession(
            str(self.onnx_yolu), providers=["CPUExecutionProvider"])
        self.girdi_adlari = [g.name for g in self.oturum.get_inputs()]
        self.cikti_adlari = [c.name for c in self.oturum.get_outputs()]
        self.tokenizer = tokenizers.Tokenizer.from_file(str(self.tokenizer_yolu))
        self.tokenizer.enable_truncation(max_length=self.max_token)
        self.tokenizer.enable_padding()

    def _onnx_bul(self):
        for aday in self.ONNX_ADAYLARI:
            yol = self.model_dir / aday
            if yol.exists():
                return yol
        bulunan = sorted(self.model_dir.rglob("*.onnx"))
        if len(bulunan) == 1:
            return bulunan[0]
        raise FileNotFoundError(
            f"ONNX modeli TEK OLARAK bulunamadı: {self.model_dir} · arananlar="
            f"{list(self.ONNX_ADAYLARI)} · ağaçta bulunan={[str(b) for b in bulunan]}. "
            f"Birden çoksa hangisinin canlı taraftakiyle aynı olduğu ÖLÇÜLMEDEN seçilemez.")

    def __call__(self, metinler):
        """[metin] → [1024'lük normalize float listesi]. Prefix EKLENMEZ (canlı .env'de
        PREFIX'ler boşaltıldı — kart kurulum kaydı)."""
        import numpy
        metinler = list(metinler)
        if not metinler:
            return []
        kodlar = self.tokenizer.encode_batch(metinler)
        besleme = {}
        if "input_ids" in self.girdi_adlari:
            besleme["input_ids"] = numpy.array([k.ids for k in kodlar], dtype="int64")
        if "attention_mask" in self.girdi_adlari:
            besleme["attention_mask"] = numpy.array([k.attention_mask for k in kodlar],
                                                    dtype="int64")
        if "token_type_ids" in self.girdi_adlari:
            besleme["token_type_ids"] = numpy.zeros_like(besleme["input_ids"])
        eksik = [ad for ad in self.girdi_adlari if ad not in besleme]
        if eksik:
            raise RuntimeError(f"ONNX modeli bilinmeyen girdi istiyor: {eksik} "
                               f"(bilinen: input_ids/attention_mask/token_type_ids)")

        ciktilar = self.oturum.run(None, besleme)
        if "sentence_embedding" in self.cikti_adlari:
            gomme = ciktilar[self.cikti_adlari.index("sentence_embedding")]
        else:
            ucboyutlu = [c for c in ciktilar if getattr(c, "ndim", 0) == 3]
            if not ucboyutlu:
                raise RuntimeError(
                    f"ONNX çıktılarında [B,T,H] gizli-durum yok: {self.cikti_adlari} — "
                    f"havuzlama ÖLÇÜLEMEZ, tahmin edilmez")
            gomme = cls_havuzla(ucboyutlu[0])
        gomme = l2_normalize(gomme.astype("float32"))
        boyut_dogrula(gomme, self.boyut)
        return [[float(x) for x in satir] for satir in gomme]


# =================================================================================================
# SQLITE-VEC KATMANI
# =================================================================================================
def paketle(vektor):
    """sqlite-vec'in beklediği küçük-endian float32 blob'u. `sqlite_vec.serialize_float32`
    ile aynı gövde; burada AÇIKÇA yazılır ki çiviler uzantı kurulu olmadan da ölçebilsin."""
    degerler = [float(x) for x in vektor]
    return struct.pack("<%df" % len(degerler), *degerler)


def vec_baglan(db_yolu):
    """sqlite-vec uzantısı YÜKLÜ bir bağlantı. İki arıza AYRI AYRI adlandırılır — "bu Python
    uzantı yükleyemiyor" ile "sqlite-vec kurulu değil" farklı reçeteler ister."""
    db = sqlite3.connect(str(db_yolu))
    if not hasattr(db, "enable_load_extension"):
        raise RuntimeError(
            "bu Python'ın `sqlite3` modülü `enable_load_extension` desteği OLMADAN derlenmiş — "
            "sqlite-vec yüklenemez (yerel macOS kurulumunda ölçüldü, 2026-09-01). Koşum, "
            "uzantı destekli Python'ın olduğu A1'de yapılır.")
    try:
        import sqlite_vec
    except ImportError as e:
        raise RuntimeError(
            f"`sqlite_vec` kurulu değil ({e}) — A1'de `pip install sqlite-vec`. Bu, uzantı "
            f"desteğinin yokluğundan FARKLI bir arızadır.") from e
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)
    return db


def sema_kur(db, boyut=BOYUT):
    """İki tablo + künye. Künye kurulum süresini ve head_commit'i TAŞIR: rapor onu buradan
    okur (tek-kaynak yasası — ikinci bir yerde tutulsa sessizce ayrışırdı)."""
    db.execute("CREATE TABLE IF NOT EXISTS chunk("
               " id INTEGER PRIMARY KEY,"
               " dosya_yolu TEXT NOT NULL,"
               " bolum_basligi TEXT NOT NULL,"
               " metin TEXT NOT NULL,"
               " blob_sha TEXT NOT NULL)")
    db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS chunk_vec USING vec0("
               f" id INTEGER PRIMARY KEY, gomme FLOAT[{boyut}])")
    db.execute("CREATE TABLE IF NOT EXISTS kunye("
               " anahtar TEXT PRIMARY KEY, deger TEXT NOT NULL)")


def kunye_yaz(db, kayitlar):
    db.executemany("INSERT OR REPLACE INTO kunye(anahtar, deger) VALUES(?, ?)",
                   [(k, json.dumps(v, ensure_ascii=False)) for k, v in kayitlar.items()])


def kunye_oku(db):
    satirlar = db.execute("SELECT anahtar, deger FROM kunye").fetchall()
    return {a: json.loads(d) for a, d in satirlar}


def indeks_kur(db, chunklar, gomucu, *, boyut=BOYUT, yigin=32):
    """Chunk'ları yığın yığın gömer ve İKİ tabloya AYNI id'lerle yazar."""
    sema_kur(db, boyut)
    yazilan = 0
    for bas in range(0, len(chunklar), yigin):
        dilim = chunklar[bas:bas + yigin]
        vektorler = gomucu([c["metin"] for c in dilim])
        if len(vektorler) != len(dilim):
            raise RuntimeError(f"gömücü {len(dilim)} metne {len(vektorler)} vektör döndürdü")
        chunk_satirlari = []
        vec_satirlari = []
        for kayma, (chunk, vektor) in enumerate(zip(dilim, vektorler)):
            if len(vektor) != boyut:
                raise ValueError(f"gömme boyutu {len(vektor)}, beklenen {boyut}")
            kimlik = yazilan + kayma + 1
            chunk_satirlari.append((kimlik, chunk["dosya_yolu"], chunk["bolum_basligi"],
                                    chunk["metin"], chunk["blob_sha"]))
            vec_satirlari.append((kimlik, paketle(vektor)))
        db.executemany("INSERT INTO chunk(id, dosya_yolu, bolum_basligi, metin, blob_sha)"
                       " VALUES(?, ?, ?, ?, ?)", chunk_satirlari)
        db.executemany("INSERT INTO chunk_vec(id, gomme) VALUES(?, ?)", vec_satirlari)
        yazilan += len(dilim)
    db.commit()
    return {"chunk_sayisi": yazilan}


#: vec0 KNN sorgusu. `k` PARAMETRE OLARAK bağlanır — dizgeye gömülmesi enjeksiyon yüzeyi olurdu.
EN_YAKIN_SQL = (
    "SELECT c.id, c.dosya_yolu, c.bolum_basligi, c.metin, c.blob_sha, v.distance"
    "  FROM chunk_vec v JOIN chunk c ON c.id = v.id"
    " WHERE v.gomme MATCH ? AND k = ?"
    " ORDER BY v.distance")


def en_yakin(db, vektor, k=3):
    satirlar = db.execute(EN_YAKIN_SQL, (paketle(vektor), k)).fetchall()
    return [{"id": s[0], "dosya": s[1], "bolum": s[2], "metin": s[3],
             "blob_sha": s[4], "mesafe": s[5]} for s in satirlar]


# =================================================================================================
# KOMUT SATIRI
# =================================================================================================
def main(argv=None):
    ap = argparse.ArgumentParser(description="EDG-067 taban indeksi (sqlite-vec + bge-m3 ONNX)")
    ap.add_argument("--paket", required=True, help="manifest_uret.py çıktı dizini")
    ap.add_argument("--model-dir", required=True, help="bge-m3 ONNX dizini (A1 canlı kurulum)")
    ap.add_argument("--db", required=True, help="üretilecek sqlite dosyası")
    ap.add_argument("--boyut", type=int, default=BOYUT)
    ap.add_argument("--max-token", type=int, default=MAX_TOKEN)
    ap.add_argument("--pencere", type=int, default=PENCERE)
    ap.add_argument("--ortusme", type=int, default=ORTUSME)
    ap.add_argument("--yigin", type=int, default=32)
    a = ap.parse_args(argv)

    db_yolu = pathlib.Path(a.db)
    if db_yolu.exists():
        raise SystemExit(f"HEDEF VAR: {db_yolu} — üstüne yazılmaz (yarım indeks sessizce "
                         f"karışırdı). Silmek operatörün kararı.")
    baslangic = time.time()
    manifest, chunklar = korpus_chunklari(a.paket, pencere=a.pencere, ortusme=a.ortusme)
    gomucu = OnnxGomucu(a.model_dir, boyut=a.boyut, max_token=a.max_token)
    db = vec_baglan(db_yolu)
    try:
        ist = indeks_kur(db, chunklar, gomucu, boyut=a.boyut, yigin=a.yigin)
        sure = round(time.time() - baslangic, 1)
        kunye_yaz(db, {
            "head_commit": manifest["head_commit"],
            "dosya_sayisi": len(manifest["dosyalar"]),
            "chunk_sayisi": ist["chunk_sayisi"],
            "kurulum_suresi_s": sure,
            "model_dir": str(gomucu.onnx_yolu),
            "boyut": a.boyut,
            "max_token": a.max_token,
            "pencere": a.pencere,
            "ortusme": a.ortusme,
            "uretim_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        db.commit()
    finally:
        db.close()
    print(json.dumps({"db": str(db_yolu), "head_commit": manifest["head_commit"],
                      "dosya_sayisi": len(manifest["dosyalar"]),
                      "chunk_sayisi": ist["chunk_sayisi"], "kurulum_suresi_s": sure},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
