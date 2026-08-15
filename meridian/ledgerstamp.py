"""ledgerstamp.py — işlem defterine kaynak damgası: canlı kanıt ile tohum simülasyonunu ayırır.

`state/trades.jsonl` iki ayrı yazardan beslenir: canlı kâğıt döngünün kapattığı işlem (GERÇEK
KANIT; `loop._persist_trade` → append) ve replay tohumunun tek toplu yazımla ürettiği satır
(SİMÜLASYON; `run.replay_seed` — bugünkü evrenle koşulduğu için survivorship taşır). Damga
(`kaynak` alanı: live_paper | replay_seed | belirsiz) olmadan karne, skor kalibrasyonu ve
alfa/beta ölçümü tüm defteri "canlı" sanır. Modül üç şey yapar: (1) ileri yolun damgasını sağlar
(`stamp`/`stamp_rows` — var olan damga ASLA ezilmez), (2) mevcut satırları kanıta dayanarak
geriye dönük damgalar (`migrate` — kuru koşu varsayılan, tek atomik yazım, süreçler-arası kilit),
(3) okuyucuların payda ayırdığı tek sayaç yüzeyini verir (`counts`/`split`/`kaynak_of`).

TOHUM SINIRI UYDURULMAZ, DONMUŞ KANITTAN OKUNUR (`seed_boundary`), sırayla: eğri zarfındaki SON
reset işaretinin `egri_son_nokta` alanı (bir kez yazılır; eğriye nokta eklemek onu kıpırdatmaz) →
yedek yol `trades.kaynak`: `replay_seed` damgalı satırların en geç `ts_close`u → hiçbiri
ölçülemezse `replay_end` None'dır ve TÜM satırlar `belirsiz` kalır ("sınır 0" ya da "bugün"
uydurulmaz); hangi yolun konuştuğu `kaynak`/`yollar` alanlarında beyanlıdır. Eğrinin SON
NOKTASINDAN okuma YANLIŞLANDI: eğrinin kadanslı bir yazarı var, oradan okunan sınır her seans
bugüne kayar ve her canlı satırı tohum diye damgalardı. Toplu-yazım mtime imzası da aynı nedenle
İKİNCİL ve ZAYIFTIR: sınırı belirlemez, yalnız `classify`ın çelişki kuralını besler; çelişki
`live_paper`a değil `belirsiz`e çözülür — sınıflandırıcı kendi kanıtını yalanlayamaz.

CANLI WORKER KOŞARKEN YAZMAZ: CLI canlı süreç görürse `--uygula`yı reddeder (`--zorla` ile
ezilir) — kilit yarışı önler ama defteri iki farklı NİYETLE yeniden yazmayı önlemez. Kullanım:
`python -m meridian.ledgerstamp [--json | --uygula | --zorla]`. Okur: trades.jsonl +
equity_curve.json; yalnız `--uygula` yolunda trades.jsonl'ı yeniden yazar.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys

from . import config, store

# ---- ŞEMA ------------------------------------------------------------------------------------
FIELD = "kaynak"
LIVE_PAPER = "live_paper"        # canlı kâğıt döngünün kapattığı işlem — GERÇEK kanıt
REPLAY_SEED = "replay_seed"      # replay tohumunun ürettiği işlem — "training", canlı DEĞİL
BELIRSIZ = "belirsiz"            # ayırt edilemedi; uydurma yerine dürüst boşluk
GECERLI = frozenset({LIVE_PAPER, REPLAY_SEED, BELIRSIZ})

LEDGER = "trades.jsonl"
EQUITY = "equity_curve.json"

# ---- SINIRIN KAYNAKLARI. Hangi yolun konuştuğu her raporda ADIYLA yazar. -------
KAYNAK_RESET = "reset_isareti"   # eğri zarfındaki SON reset işaretinin `egri_son_nokta` alanı
KAYNAK_DAMGA = "trades.kaynak"   # yedek yol: `replay_seed` damgalı satırların en geç `ts_close`u
KAYNAK_YOK = "yok"               # üçüncü hâl: ölçülemedi — `replay_end` None (SIFIR ya da bugün DEĞİL)

# İKİ YAZIMIN "AYNI ANDA" SAYILDIĞI PENCERE. `run.replay_seed`in `trades.jsonl` ve
# `equity_curve.json` yazımları ardışıktır; aradaki tek iş bir
# sözlük kurmaktır (canlı defterde ölçülen fark 4 ms). 5 sn hem yavaş diskte hem yüklü bir VM'de
# rahat pay bırakır, ama bir sonraki SEANSIN append'iyle karışacak kadar geniş değildir.
BULK_WRITE_TOLERANCE_S = 5.0


def stamp(row: dict, kaynak: str) -> dict:
    """Satıra kaynak damgasını bas. VAR OLAN DAMGA EZİLMEZ — bir satırın kökeni bir kez ölçülür;
    ikinci bir yazar onu 'düzeltmeye' kalkarsa migrasyonun kanıtı sessizce kaybolur."""
    if kaynak not in GECERLI:
        raise ValueError(f"geçersiz kaynak damgası: {kaynak!r} (geçerli: {sorted(GECERLI)})")
    if not isinstance(row, dict):
        raise TypeError(f"satır sözlük olmalı, {type(row).__name__} geldi")
    if row.get(FIELD) in GECERLI:
        return row
    row[FIELD] = kaynak
    return row


def stamp_rows(rows: list[dict], kaynak: str) -> list[dict]:
    """Toplu damga — tohum yolunun (`run.replay_seed`) tek çağrısı."""
    return [stamp(r, kaynak) for r in rows]


def kaynak_of(row: dict) -> str:
    """Satırın damgası; yoksa/tanınmıyorsa BELİRSİZ (uydurma yok)."""
    v = row.get(FIELD)
    return v if v in GECERLI else BELIRSIZ


def counts(rows: list[dict] | None = None) -> dict:
    """DEFTER SAYAÇLARI — panonun ve karnenin okuduğu TEK yüzey.

    `belirsiz_n` "kökeni ayırt edilemeyen satır" sayısıdır ve DAMGASIZ satırları da KAPSAR: pano
    açısından ikisi aynı soruya çıkar ("bu satır kanıt mı, simülasyon mu — bilmiyoruz"). Alt kırılım
    `damgasiz_n` ile yanında durur, çünkü ikisi farklı EYLEM gerektirir: damgasız satır migrasyonla
    kapanabilir, açıkça `belirsiz` damgalı satır ise ölçüldü ve ayrılamadı."""
    rows = store.read_jsonl(LEDGER) if rows is None else rows
    live = seed = belirsiz = damgasiz = 0
    for r in rows:
        v = r.get(FIELD)
        if v == LIVE_PAPER:
            live += 1
        elif v == REPLAY_SEED:
            seed += 1
        else:
            belirsiz += 1
            if v is None:
                damgasiz += 1
    return {"live_paper_n": live, "replay_seed_n": seed, "belirsiz_n": belirsiz,
            "damgasiz_n": damgasiz, "toplam": len(rows),
            # OKURA TEK CÜMLE: "training" tohum satırlarının etiketidir (denetim dili).
            "training_n": seed,
            "kapsam": ("live_paper = canlı kâğıt döngünün kapattığı işlem; replay_seed = tohum "
                       "koşusunun ÜRETTİĞİ işlem (training, survivorship'li); belirsiz = kökeni "
                       "ölçülemeyen satır (damgasızlar dahil)")}


def split(rows: list[dict] | None = None) -> dict[str, list[dict]]:
    """Defteri damgaya göre ayır — kalibrasyon/atribüsyon okuyucularının payda ayırma yolu."""
    rows = store.read_jsonl(LEDGER) if rows is None else rows
    out: dict[str, list[dict]] = {LIVE_PAPER: [], REPLAY_SEED: [], BELIRSIZ: []}
    for r in rows:
        out[kaynak_of(r)].append(r)
    return out


# ---- GERİYE DÖNÜK SINIR ÖLÇÜMÜ ----------------------------------------------------------------
def _mtime(name: str) -> float | None:
    """Arka uçtan bağımsız son-yazım zamanı (`store.mtime`). DOSYA çağında `stat().st_mtime`,
    SQLite çağında `entity_meta.updated_at`. Ölçülemezse None — uydurma yok."""
    return store.mtime(name)


def _toplu_yazim_olculebilir() -> bool:
    """TOPLU YAZIM İMZASI YALNIZ DOSYA ÇAĞINDA ANLAMLIDIR.

    İmza şuna dayanır: `run.replay_seed` önce defteri, hemen ardından eğriyi yazar; iki AYRI dosyanın mtime'ı
    saniyeler içindeyse defter o toplu yazımdan beri hiç `append` almamıştır. SQLite'a taşındıktan
    sonra iki varlığın damgası TEK migrasyon transaction'ında AYNI ana düşer — yani fark her zaman
    ~0 çıkar ve imza "defter hiç eklenmedi" diye OKUNURDU. Bu bir ölçüm değil, migrasyonun kendi
    gölgesidir. Ölçülemeyen bir imzayı VAR saymak, tam olarak denetimin şikâyet ettiği hatadır.

    İMZANIN İKİNCİ AŞINMASI: dosya çağında bile imza artık ZAYIFTIR —
    `loop.daily_cycle` eğriye her seans nokta ekliyor, yani `equity_curve.json` mtime'ı defterden
    bağımsız ilerliyor. Bu fonksiyon "ölçülebilir mi" sorusunu (arka uç) cevaplar; "ne kadar
    kanıt" sorusunun cevabı artık `kaynak` alanındadır. İmza SINIRI BELİRLEMEZ; yalnız
    `classify`ın çelişki kuralını besler ve o kural her zaman MUHAFAZAKÂR tarafa (`belirsiz`)
    düşer — zayıflayan bir imza yanlış bir `live_paper` damgası üretemez."""
    return not (store.db_backed(LEDGER) or store.db_backed(EQUITY))


def _tarih(v) -> str | None:
    """Ham bir değerden (eğri noktası, liste, dize) ISO tarih çıkar; çıkaramazsan None.

    Nokta şekli `["2026-07-20", 94457.91]`dır (`sermaye.uygula` işarete `list(pts[-1])` yazar), ama
    zarf anahtarları serbest biçimlidir ve SQLite çağı ham nesneyi `extra_json`dan geri verir: boş
    liste, düz dize ya da bozuk bir değer de gelebilir. AYRIŞTIRILAMAYAN değer None döner —
    "okunamadı" ile "yok" aynı kovaya girer ve ikisi de UYDURULMAZ."""
    if isinstance(v, (list, tuple)):
        v = v[0] if v else None
    if v is None:
        return None
    s = str(v)[:10]
    try:
        _dt.date.fromisoformat(s)
    except ValueError:  # sessiz-yutma: SESSİZ DEĞİL — biçimsiz değer çağırana None olarak döner ve `neden` metnine girer; saf ölçüm fonksiyonunu kayıt kanalına bağlamak `classify`ın sözleşmesini kırardı
        return None
    return s


def _sinir_reset_isaretinden(eq: dict | None) -> tuple[str | None, dict]:
    """YOL-1 — SON reset işaretinin `egri_son_nokta` alanı. ONARIMIN TA KENDİSİ.

    İşaret DONMUŞ bir kanıttır: `sermaye.uygula` onu bir kez yazar, bir daha
    yeniden yazmaz ve `points`e dokunmaz. Eğriye kaç nokta eklenirse eklensin bu alan kıpırdamaz —
    sınır da kıpırdamaz. Eğrinin son noktasından okumak tam tersiydi: her yeni nokta sınırı ileri
    taşır, köken defteri her seans yeniden yazılırdı.

    İŞARETİN ADI/ŞEKLİ KOPYALANMAZ, ÇAĞRILIR (`sermaye._egri_isaretleri`): iki modül aynı zarf
    anahtarını iki ayrı yerde tanımlasaydı biri değiştiğinde öteki sessizce boş dönerdi — bu
    deponun "aynı yasanın iki uygulaması" sınıfı.

    SONDAN GERİYE taranır: reset ANINDA eğri boşsa `sermaye.uygula` alana None yazar,
    yani son işaret konuşamayabilir. Konuşabilen EN SON işaret alınır; hiçbiri konuşamazsa None
    döner ve YOL-2 devreye girer."""
    from .sermaye import _egri_isaretleri          # TEK KAYNAK: işareti YAZAN modülün okuyucusu
    isaretler = _egri_isaretleri(eq or {})
    for m in reversed(isaretler):
        d = _tarih(m.get("egri_son_nokta"))
        if d:
            return d, {"n_isaret": len(isaretler), "isaret_id": m.get("id"),
                       "isaret_tarihi": m.get("tarih")}
    return None, {"n_isaret": len(isaretler), "isaret_id": None, "isaret_tarihi": None}


def _sinir_damgadan(rows: list[dict]) -> tuple[str | None, dict]:
    """YOL-2 (YEDEK) — `replay_seed` damgalı satırların EN GEÇ `ts_close`u.

    Kartın KENDİ yazılı çaresi ("o güne dek tohum sınırı `trades.kaynak`
    damgasından okunur"). Reset işareti hiç yazılmamış bir depoda (ör. tohumlanmış ama sermaye
    ayrıştırması yapılmamış kurulum) tohum penceresini ölçen tek DONMUŞ kanıt budur: damga satır
    diske düşmeden basılır (`run.replay_seed` → `stamp_rows`) ve `stamp` var olan damgayı EZMEZ.

    SINIRI DAR TUTAN KABUL: bu yol yalnız ZATEN DAMGALI satırlardan türer, yani damgasız satırları
    sınıflandırmak için kullanıldığında bir tür dairesellik taşır — sınır, damgalı dilimin sonudur;
    damgasız satır o sınırın ötesindeyse "sonradan eklendi" der. Dairesellik ZARARSIZ ama ZAYIF
    olduğu için güven `orta`dır ve `kaynak` alanı hangi yolun konuştuğunu söyler.

    `ts_close`u ayrıştırılamayan tohum satırı SESSİZCE ATLANMAZ: sayılır (`ts_olculemeyen`) ve
    raporda durur — sınır o satırlar kadar eksik ölçülmüş olabilir ve bunu söylemek zorundadır."""
    n = olculebilen = 0
    en_gec = None
    for r in rows or []:
        if not isinstance(r, dict) or r.get(FIELD) != REPLAY_SEED:
            continue
        n += 1
        d = _tarih(r.get("ts_close"))
        if d is None:
            continue
        olculebilen += 1
        if en_gec is None or d > en_gec:
            en_gec = d
    return en_gec, {"damgali_n": n, "ts_olculebilen": olculebilen,
                    "ts_olculemeyen": n - olculebilen}


def seed_boundary(rows: list[dict] | None = None) -> dict:
    """TOHUM PENCERESİNİN SINIRI — DONMUŞ kanıttan, tahminsiz.

    ÜÇ YOL, SIRAYLA (modül başlığındaki onarım gerekçesi):
      1. `reset_isareti` — eğri zarfındaki son reset işaretinin `egri_son_nokta`sı (güven: yuksek).
      2. `trades.kaynak` — `replay_seed` damgalı satırların en geç `ts_close`u (güven: orta).
      3. `yok`           — hiçbiri ölçülemedi: `replay_end` None, her satır `belirsiz` (güven: yok).

    HANGİ YOLUN KONUŞTUĞU `kaynak` ALANINDA YAZAR ve `yollar` ikisinin değerini yan yana taşır:
    iki yol aynı sayıyı verse bile okuyucu hangisine baktığını görmek zorundadır (aynı sayıya iki
    ayrı kanıttan varmak ile tek kanıta mahkûm olmak farklı şeylerdir).

    `egri_son_nokta` alanı BİLGİ OLARAK taşınır ama SINIRI BELİRLEMEZ — eski yolun bugün ne
    diyeceği görünsün diye (canlıda 2026-08-13'te ikisi ayrışmıştı; eski yol sınırı 2026-07-20'de
    donduruyordu). Kadanslı yazar (bacak-2) bu alanı her seans ileri taşır; `replay_end`i TAŞIMAZ.

    `rows` verilirse defter yeniden okunmaz (çağıran zaten elinde tutuyorsa — `_migrate_locked`
    kilidin içinde tam olarak bunu yapar); verilmezse diskten okunur."""
    eq = store.read_json(EQUITY, None)
    pts = (eq or {}).get("points") or []
    egri_son = _tarih(pts[-1]) if pts else None
    d_reset, m_reset = _sinir_reset_isaretinden(eq)
    rows = store.read_jsonl(LEDGER) if rows is None else rows
    d_damga, m_damga = _sinir_damgadan(rows)

    _olculebilir = _toplu_yazim_olculebilir()
    t_led, t_eq = (_mtime(LEDGER), _mtime(EQUITY)) if _olculebilir else (None, None)
    delta = None if (t_led is None or t_eq is None) else round(abs(t_led - t_eq), 3)
    toplu = None if delta is None else bool(delta <= BULK_WRITE_TOLERANCE_S)
    _imza = (f"toplu yazım imzası: {'VAR' if toplu else 'YOK'} (mtime farkı {delta}sn)"
             if toplu is not None else
             ("toplu yazım imzası ÖLÇÜLEMEZ (varlıklar SQLite arka ucunda: iki damga tek "
              "transaction'da aynı ana düşer)" if not _olculebilir
              else "toplu yazım imzası ÖLÇÜLEMEDİ (mtime okunamadı)"))

    # İKİ YOL AYRIŞIRSA BU SESSİZ KALAMAZ. Canlıda ÖLÇÜLEN hâl: işaret 2026-08-01'de
    # donmuş ve eğrinin O ANDAKİ son noktasını (2026-07-20) taşıyor; oysa 2026-08-13 tohum
    # yenilemesi defterine en geç 2026-07-24 kapanışlı satırlar girdi. Yani DONMUŞ sınır, tohumun
    # GERÇEK penceresinden 4 gün geride. Sıra bilinçlidir (donma > tazelik: sınırın kaymaması
    # köken defterinin ta kendisidir) ama fark ADIYLA görünmeli — yoksa okuyucu tek bir tarihe
    # bakıp iki kanıtın anlaştığını sanar.
    _ayrisma = ("" if not (d_reset and d_damga) or d_reset == d_damga else
                (f" · AYRIŞMA: yedek yol (`{KAYNAK_DAMGA}`) {d_damga} diyor — tohum defteri "
                 f"işaretin donduğu tarihten SONRAsına uzanıyor; sınır bilerek DONMUŞ olanı "
                 f"alır, fark burada beyanlıdır"))
    if d_reset:
        replay_end, kaynak, guven = d_reset, KAYNAK_RESET, "yuksek"
        neden = (f"sınır SON reset işaretinin `egri_son_nokta` alanından okundu "
                 f"({m_reset['isaret_id']}, işaret tarihi {m_reset['isaret_tarihi']}): "
                 f"{replay_end}. Bu alan DONMUŞTUR — eğriye yeni nokta eklenmesi sınırı "
                 f"kaydırmaz.{_ayrisma} [{_imza}; imza sınırı BELİRLEMEZ]")
    elif d_damga:
        replay_end, kaynak, guven = d_damga, KAYNAK_DAMGA, "orta"
        neden = (f"eğride reset işareti yok ya da `egri_son_nokta` okunamadı "
                 f"({m_reset['n_isaret']} işaret görüldü) — YEDEK YOL: sınır `trades.kaynak` "
                 f"damgasından okundu; {m_damga['damgali_n']} replay_seed satırının en geç "
                 f"ts_close'u {replay_end} "
                 f"({m_damga['ts_olculemeyen']} satırın ts_close'u ayrıştırılamadı). [{_imza}]")
    else:
        replay_end, kaynak, guven = None, KAYNAK_YOK, "yok"
        neden = (f"tohum penceresinin sınırı ÖLÇÜLEMEDİ: eğride konuşabilen reset işareti yok "
                 f"({m_reset['n_isaret']} işaret) ve defterde `replay_seed` damgalı ölçülebilir "
                 f"satır yok ({m_damga['damgali_n']} damgalı, {m_damga['ts_olculemeyen']} biçimsiz "
                 f"ts_close) — hiçbir satır sınıflanamaz. Eğrinin son noktası "
                 f"({egri_son}) SINIR SAYILMAZ: kadanslı yazar onu her seans ileri taşır.")
    return {"replay_end": replay_end, "kaynak": kaynak,
            "yollar": {KAYNAK_RESET: d_reset, KAYNAK_DAMGA: d_damga},
            # İKİ KANIT ANLAŞMIYOR MU? Makine-okunur bayrak (metin `neden`de ayrıca durur).
            "yollar_ayrisik": bool(d_reset and d_damga and d_reset != d_damga),
            "reset_isareti": m_reset, "damga_olcumu": m_damga,
            "toplu_yazim": toplu, "mtime_delta_s": delta,
            "n_equity_points": len(pts), "guven": guven, "neden": neden,
            "kanit": ((f"eğri zarfındaki son reset işaretinin `egri_son_nokta` alanı "
                       f"(yazar: sermaye.uygula) — DONMUŞ") if kaynak == KAYNAK_RESET else
                      (f"`{LEDGER}` içindeki replay_seed damgalarının en geç ts_close'u "
                       f"(yazar: run.replay_seed → stamp_rows) — YEDEK YOL"
                       if kaynak == KAYNAK_DAMGA else "kanıt YOK — sınır ölçülemedi")),
            # ESKİ YOLUN BUGÜNKÜ DEĞERİ — bilgi; sınırı BELİRLEMEZ (bkz. modül başlığı).
            "egri_son_nokta": egri_son,
            "equity_ilk_nokta": (_tarih(pts[0]) if pts else None)}


def classify(rows: list[dict], boundary: dict | None = None) -> list[dict]:
    """Her satır için (kaynak, gerekçe) — SAF fonksiyon, hiçbir şey yazmaz.

    KURALLAR, sırasıyla:
      0. Satırda GEÇERLİ bir damga varsa DOKUNULMAZ (migrasyon idempotenttir).
      1. Sınır ölçülemediyse → `belirsiz`.
      2. `ts_close` yoksa/ayrıştırılamıyorsa → `belirsiz` (satırın hangi tarafta olduğu bilinmez).
      3. `ts_close <= replay_end` → `replay_seed`. Tohum yazımı defterin TAMAMINI yeniden yazar;
         o pencereye düşen her satır o yazımdan çıkmıştır.
      4. `ts_close > replay_end` → `live_paper` — YALNIZ defter tohum yazımından sonra da
         yazılmışsa. Toplu yazım imzası VARSA böyle bir satırın var olması ÇELİŞKİDİR (defter o
         yazımdan beri dokunulmamış olmalıydı) ve çelişki `live_paper` diye çözülmez: `belirsiz`
         kalır. Sınıflandırıcı kendi kanıtını yalanlayamaz.

    KURAL-4'ÜN İMZASI ZAYIFLADI, KURALIN YÖNÜ DEĞİŞMEDİ: eğrinin artık
    kadanslı bir yazarı var, yani mtime çifti "defter hiç eklenmedi" kanıtı değil. Kural yine de
    KALDI çünkü hatası tek yönlü: imza yanlışlıkla VAR görünürse satır `live_paper` yerine
    `belirsiz` olur — pozitif bir iddia ölçülmemiş kanıtla BASILMAZ. Ters yönde (kuralı kaldırmak)
    zayıflayan bir imza doğrudan yanlış `live_paper` damgası üretirdi."""
    b = boundary if boundary is not None else seed_boundary()
    end = b.get("replay_end")
    toplu = b.get("toplu_yazim")
    out = []

    def _k(kaynak, sinif, gerekce, degisti=True):
        # `sinif` GRUPLANABİLİR kural adıdır, `gerekce` o SATIRIN kanıtıdır. İkisi ayrı olmasaydı
        # rapor 95 satırı 90 ayrı "gerekçe"ye bölerdi (her tarih kendi başına bir metin) ve
        # okuyan "hangi KURAL kaç satırı damgaladı?" sorusunu hiç göremezdi.
        out.append({FIELD: kaynak, "sinif": sinif, "gerekce": gerekce, "degisti": degisti})

    for r in rows:
        mevcut = r.get(FIELD)
        if mevcut in GECERLI:
            _k(mevcut, "zaten_damgali", "satır zaten damgalı — dokunulmadı", degisti=False)
            continue
        if not end:
            _k(BELIRSIZ, "sinir_olculemedi", b.get("neden") or "tohum sınırı ölçülemedi")
            continue
        ts = str(r.get("ts_close") or "")[:10]
        try:
            _dt.date.fromisoformat(ts)
        except ValueError:  # sessiz-yutma: SESSİZ DEĞİL — istisnanın kendisi ÇIKTIYA çevriliyor (satır `belirsiz` damgalanır, `sinif=ts_close_ayristirilamadi` rapordaki sayaca girer ve gerekçe metni satırın yanında durur); ayrıca uyarı basmak, `classify`ın saf-fonksiyon sözleşmesini kırardı
            _k(BELIRSIZ, "ts_close_ayristirilamadi", f"ts_close ayrıştırılamadı ({ts!r})")
            continue
        if ts <= end:
            _k(REPLAY_SEED, "sinir_icinde", f"ts_close {ts} ≤ tohum sınırı {end}")
        elif toplu:
            _k(BELIRSIZ, "celiski_toplu_yazim",
               f"ÇELİŞKİ: ts_close {ts} > tohum sınırı {end} ama toplu yazım imzası defterin o "
               f"yazımdan beri değişmediğini söylüyor")
        else:
            _k(LIVE_PAPER, "sinir_disinda",
               f"ts_close {ts} > tohum sınırı {end} (tohum yazımından sonra eklenmiş)")
    return out


def migrate(apply: bool = False) -> dict:
    """TEK SEFERLİK GERİYE MİGRASYON. Kuru koşu VARSAYILANDIR (`barrepair` kuralı: veri yazan bir
    aracın varsayılanı yazmak olamaz). Uygulama tek atomik `write_jsonl` ile biter."""
    # KİLİT: oku-değiştir-yaz. `store.file_lock` artık SÜREÇLER ARASIdır
    # (fcntl.flock), yani modülün başındaki "store kilidi süreç-içidir" uyarısının dayandığı
    # boşluk kapandı — CLI ile canlı worker aynı sırayı paylaşır. Süreç kontrolü (main) yine
    # durur: kilit yarışı önler, ama defteri iki farklı NİYETLE yeniden yazmayı önlemez.
    with store.file_lock(LEDGER):
        return _migrate_locked(apply)


def _migrate_locked(apply: bool) -> dict:
    rows = store.read_jsonl(LEDGER)
    # SINIR, RAPORUN ÖLÇTÜĞÜ DEFTERİN TA KENDİSİNDEN türetilir (yedek yol `trades.kaynak`ı okur):
    # `rows` geçilmeseydi defter kilidin içinde İKİNCİ KEZ okunurdu ve rapor iki farklı anın
    # karışımı olurdu — aynı kritik bölgede iki ayrı gerçek.
    b = seed_boundary(rows)
    kararlar = classify(rows, b)
    dagilim: dict[str, int] = {}
    siniflar: dict[str, int] = {}
    for k in kararlar:
        dagilim[k[FIELD]] = dagilim.get(k[FIELD], 0) + 1
        siniflar[k["sinif"]] = siniflar.get(k["sinif"], 0) + 1
    degisecek = sum(1 for k in kararlar if k["degisti"])
    rapor = {"applied": bool(apply), "n": len(rows), "sinir": b, "dagilim": dagilim,
             "degisecek": degisecek, "sinif_ozeti": siniflar,
             "onceki_sayaclar": counts(rows), "yazildi": False,
             "ornek": [{"id": r.get("id"), "ts_close": r.get("ts_close"), **k}
                       for r, k in list(zip(rows, kararlar))[:5]]}
    if not apply or not degisecek:
        return rapor
    yeni = [dict(r, **{FIELD: k[FIELD]}) for r, k in zip(rows, kararlar)]
    store.write_jsonl(LEDGER, yeni)
    rapor["yazildi"] = True
    rapor["sonraki_sayaclar"] = counts(yeni)
    try:
        from . import obs
        obs.warn("ledger_source_stamp_migrated", n=len(yeni), degisen=degisecek,
                 replay_end=b.get("replay_end"), guven=b.get("guven"),
                 sinir_kaynagi=b.get("kaynak"),
                 **{k: int(v) for k, v in dagilim.items()},
                 detail="BT-1 kapanışı: işlem defteri satırları kaynak damgası kazandı; "
                        "learning_scorecard/skor kalibrasyonu/alfa-beta artık gerçek-canlı n'i "
                        "tohumdan ayırıyor")
    except Exception:  # sessiz-yutma: kayıt kanalı düştü; migrasyonun kendisi diske ATOMİK yazıldı ve rapor çağırana döndü — kayıt denemesi yazımı geri alamaz
        pass
    return rapor


def _worker_running() -> bool:
    """Canlı Meridian süreci var mı? `barrepair`in AYNI ölçümü — kopyalanmaz, çağrılır."""
    from .barrepair import _worker_running as _wr
    return _wr()


def _print(rapor: dict) -> None:
    mod = "UYGULANDI" if rapor.get("yazildi") else ("UYGULAMA İSTENDİ ama değişecek satır yok"
                                                    if rapor.get("applied")
                                                    else "KURU KOŞU (hiçbir bayt yazılmadı)")
    b = rapor["sinir"]
    print(f"[ledgerstamp] {mod}")
    print(f"  tohum sınırı: {b['replay_end']}  (kaynak: {b.get('kaynak')} · güven: {b['guven']}) "
          f"— {b['neden']}")
    print(f"  kanıt: {b['kanit']}")
    # İKİ YOL YAN YANA: aynı sayıya iki kanıttan varmak ile tek kanıta mahkûm olmak farklıdır.
    _y = b.get("yollar") or {}
    print(f"  yollar: {KAYNAK_RESET}={_y.get(KAYNAK_RESET)} · {KAYNAK_DAMGA}={_y.get(KAYNAK_DAMGA)}"
          f"  (eğri son noktası: {b.get('egri_son_nokta')} — SINIR DEĞİL)")
    print(f"  defter satırı: {rapor['n']}, damgası değişecek: {rapor['degisecek']}")
    for k, v in sorted(rapor["dagilim"].items()):
        print(f"   {k:14s} {v}")
    for g, v in sorted(rapor["sinif_ozeti"].items(), key=lambda x: -x[1]):
        print(f"      · {v:4d} × kural: {g}")
    for e in rapor.get("ornek") or []:
        print(f"      örnek: {e.get('id')} ts_close={e.get('ts_close')} → {e[FIELD]} ({e['gerekce']})")
    if not rapor.get("applied") and rapor["degisecek"]:
        print("  → uygulamak için: python -m meridian.ledgerstamp --uygula  "
              "(worker DURDURULMUŞ olmalı)")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m meridian.ledgerstamp",
        description="trades.jsonl satırlarına kaynak damgası (live_paper/replay_seed/belirsiz) basar")
    ap.add_argument("--uygula", action="store_true", help="YAZ (varsayılan: kuru koşu)")
    ap.add_argument("--json", action="store_true", help="raporu JSON olarak bas")
    ap.add_argument("--zorla", action="store_true", help="canlı süreç görülse de yaz (riski sen alırsın)")
    a = ap.parse_args(argv)
    if a.uygula and not a.zorla and _worker_running():
        print("[ledgerstamp] REDDEDİLDİ: canlı Meridian süreci görülüyor. Aynı defteri iki süreç "
              "yeniden yazamaz — kilit yarışı önler ama iki farklı NİYETLE yeniden yazmayı "
              "önlemez. Önce `./ops/stop-worker.sh`, "
              "sonra tekrar dene (ya da --zorla).", file=sys.stderr)
        return 2
    rapor = migrate(apply=a.uygula)
    if a.json:
        print(json.dumps(rapor, ensure_ascii=False, indent=1, default=str))
    else:
        _print(rapor)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
