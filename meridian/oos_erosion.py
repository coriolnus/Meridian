"""oos_erosion.py — OOS AŞINMA DEFTERİ: aynı sınav kâğıdı kaç kez soruldu?
(Kârlılık Programı Aşama 2.2, 2026-07-28)

NEDEN VAR. Bir out-of-sample penceresi "dokunulmamış" olduğu SÜRECE kanıt taşır. Her kapı
değerlendirmesi o pencereye bir soru daha sorar ve her soru onu biraz daha in-sample yapar — kimse
parametreye elle dokunmasa bile, çünkü seçilim zaten "o pencerede iyi görüneni" seçmektir. Canlı
defterde bugüne kadar ~38 hipotez AYNI pencerelere sorulmuş; hiçbiri sayılmamış. Sayılmayan bir
aşınma, kapı hükümlerini sessizce değersizleştirir: kapı hâlâ "OOS'ta kazandı" der, ama o OOS
artık kimsenin görmediği bir sınav değildir.

NE YAPAR. Pencere geometrisinin (IS/OOS/holdout + fold sınırları + ambargo) parmak izini alır ve o
parmak izine ÖMÜR BOYU sorulan soru sayısını tutar. Eşik aşılınca kapıya ek marj bindirir.

--- ÜÇ BEYAN, ÜÇÜ DE KODDA DURUR ---

(1) RETRO DAMGA YASAĞI. Geçmiş ~38 sorgu geriye dönük damgalanMAZ. O sorguların hangi pencere
    geometrisiyle koştuğunu bugün bilmiyoruz (pencereler bu arada değişti) ve tahmin edilmiş bir
    sayacı gerçek sayaç gibi sunmak, tam olarak bu modülün önlemek için var olduğu şeydir. Sayaç
    BUGÜNDEN başlar; bu, aşınmanın olmadığı değil ÖLÇÜLMEDİĞİ anlamına gelir ve rapor bunu söyler.

(2) SANDBOX SAYMAZ — BİLİNÇLİ. `config.STATE` yönlendirilmiş her ölçüm (test, sprint kumu, ön-eleme
    koşusu) sayacı KENDİ kopyasına yazar; resmî defter dokunulmadan kalır. Bu bir kaçak değil,
    tasarımın kendisidir: resmî sayaç yalnız RESMÎ kapı değerlendirmelerini sayar. Ön-elemenin
    çoklu-test yükü ayrı bir kanaldan, `k_probes` beyanıyla taşınır (probgate'in kazananın-laneti
    cezası). İki yükü tek sayaca toplamak, aynı cezayı iki kez kesmek olurdu.

(3) SAYAÇ CEZALANDIRIR, ENGELLEMEZ. Eşik aşımı kapıyı kapatmaz; geçme çıtasını yükseltir. Bir
    pencereyi yakmanın doğru cevabı "artık soru sorma" değil, "artık daha büyük bir fark iste"dir.
"""
from __future__ import annotations

import hashlib
import json

from . import config, store, obs

EROSION_FILE = "oos_erosion.json"

# EŞİK: aynı parmak izine 20 sorgudan fazlası. Gerekçe: kapı zaten oturum içi K aday için
# `probgate.p_required_for(k_probes)` ile ceza kesiyor; bu sayaç OTURUMLAR ARASI, yani aynı pencereye
# aylar boyunca dönmenin yükünü ölçer. 20, canlı defterin bugüne kadarki ~38 sorgusunun yarısı
# civarı — yani "birkaç hipotez normaldir, düzinelercesi pencereyi yakar" ayrımının çizildiği yer.
EROSION_QUERY_LIMIT = 20

# EK MARJ: GATE_MARGIN 0.02'nin yarısı. Yarım marj bilinçli: aşınma cezası kapıyı fiilen kapatan
# değil, ADAYDAN DAHA FAZLASINI İSTEYEN bir çıta olmalı. Tam marj (0.02→0.04) ikiye katlardı ve
# ölçülmemiş bir aşınma miktarı için iki kat ceza, cezanın kendisini uydurma yapardı.
EROSION_EXTRA_MARGIN = 0.01


def fingerprint(is_start, oos_start, oos_end, holdout_end, fold_bounds, embargo_days) -> str:
    """Pencere GEOMETRİSİNİN kimliği. Fold sınırları HASH'E DAHİLDİR: n-dengeli kesim (Aşama 2.1)
    fold sınırlarını incumbent'ın işlemlerinden türetiyor, yani incumbent değişince geometri de
    değişir. Sınırlar hash'in dışında kalsaydı, gerçekte FARKLI bir sınavı aynı sayaca yazardık."""
    ham = json.dumps({"is": str(is_start), "oos": str(oos_start), "oos_end": str(oos_end),
                      "holdout": str(holdout_end), "embargo": int(embargo_days or 0),
                      "folds": [str(b) for b in (fold_bounds or [])]}, sort_keys=True)
    return hashlib.sha256(ham.encode("utf-8")).hexdigest()[:16]


def extra_margin(queries: int) -> float:
    """Yürürlükteki ek marj. Eşiğin ALTINDA 0.0 — ceza kademeli değil eşikli: kademeli bir ceza,
    kaçıncı sorguda ne kadar aşınma olduğuna dair ölçmediğimiz bir eğri iddia ederdi."""
    return EROSION_EXTRA_MARGIN if int(queries or 0) > EROSION_QUERY_LIMIT else 0.0


def arsivle(doc: dict) -> int:
    """ROTASYON ARŞİVİ: yürürlükteki pencereden ÖNCE yazılmış kayıtlara arşiv İŞARETİ koyar.
    Değiştirilen kayıt sayısını döner. İDEMPOTENT — ikinci çağrı hiçbir şey yapmaz.

    RETRO DAMGA YASAĞINI İHLAL ETMEZ, ONU KORUR. Yasak, geçmiş kayıtların İÇERİĞİNİ (hangi pencerede
    kaç sorgu soruldu) geriye dönük UYDURMAYI yasaklar. Burada hiçbir sayı, tarih ya da geometri
    değişmez: `queries`, `first_seen`, `last_seen`, `pencere` alanlarına DOKUNULMAZ. Eklenen tek şey
    `arsiv` işaretidir ve o işaret bir ölçüm değil bir ETİKETTİR — "bu satır artık yürürlükte olmayan
    bir sınav kâğıdına ait" der.

    İŞARET NEDEN GEREKLİ: R1'den sonra defter iki farklı sınavın sayaçlarını yan yana taşır. İşaret
    olmadan bir okuyucu (pano, 2D değerlendiricisi, gelecekteki bir tur raporu) 434'lük R0 sayacını
    R1'in sayacı sanabilir ve "aşınma hâlâ 21×" diye YANLIŞ bir hüküm kurabilir — rotasyonun tam
    tersi sonuç. Kayıtları SİLMEK de çözüm değildi: 434 sorgu OLDU, ve olmuş bir aşınmayı defterden
    kaldırmak onu ölçülmemiş yapmaz, GÖRÜNMEZ yapar.

    ETİKET ÖLÇÜMDEN TÜRETİLİR, VARSAYILMAZ: satırın kendi `pencere` meta'sı `dataset.ARSIV_GEOMETRILER`
    içindeki bir geometriyle eşleşiyorsa o kimlik yazılır (`arsiv_R0`). Eşleşmiyorsa —meta yok ya da
    tanınmayan bir geometri— `arsiv_bilinmeyen` yazılır. UYDURMA YASAĞI: hangi pencere olduğunu
    bilmediğimiz bir satıra "R0" demek, modülün başındaki (1) numaralı beyanın ihlali olurdu."""
    from . import dataset
    n = 0
    for w in (doc.get("windows") or {}).values():
        if not isinstance(w, dict):
            continue
        # İKİ ATLAMA SEBEBİ, İKİ AYRI SORU — TEK BİR `or` ZİNCİRİNDE BİRLEŞTİRİLMEZ. İlk hâli tek
        # satırda iki alanı ardışık okuyordu ve şema-takası dedektörü (test_parity_v56
        # `_alias_scan`) o kalıbı haklı olarak "aynı alanın iki adı" adayı diye yakaladı. Takas
        # DEĞİL: `pencere_id` "bu satır YÜRÜRLÜKTEKİ sınava ait" der, arşiv işareti "bu satır DAHA
        # ÖNCE damgalandı" der — biri diğerinin yedeği değil. Envantere yanlış bir takas yazmak
        # yerine kalıp açıldı: iki soru iki ayrı adla, hem dedektör hem insan için okunur.
        yururlukteki_pencere = bool(w.get("pencere_id"))
        zaten_isaretli = bool(w.get("arsiv"))
        if yururlukteki_pencere or zaten_isaretli:
            continue
        p = w.get("pencere") or {}
        etiket = "arsiv_bilinmeyen"
        for pid, g in (dataset.ARSIV_GEOMETRILER or {}).items():
            if all(str(p.get(k) or "") == str(g.get(k) or "")
                   for k in ("is_start", "oos_start", "oos_end", "holdout_end")):
                etiket = f"arsiv_{pid}"
                break
        w["arsiv"] = etiket
        w["arsiv_tarihi"] = dataset.ROTATION_DATE
        w["arsiv_beyan"] = ("içerik DEĞİŞMEDİ (retro damga yasağı) — yalnız arşiv işareti eklendi; "
                            "bu satırın sayısı yürürlükteki pencereyle KARŞILAŞTIRILAMAZ")
        n += 1
    return n


def record(fp: str, meta: dict | None = None) -> dict:
    """Bir kapı değerlendirmesini deftere işler ve GÜNCEL durumu döner.

    Yazım, kapı değerlendirmesinin koştuğu SÜREÇTE olur (reflect yolu) — ayrı bir toplayıcıya
    bırakılsaydı, çöken ya da yarıda kesilen bir arama oturumu sayaca hiç düşmezdi ve tam da en çok
    sorgu üreten koşular görünmez kalırdı."""
    from . import dataset
    doc = store.read_json(EROSION_FILE, None) or {
        "windows": {},
        # SAYACIN NE ZAMAN BAŞLADIĞI DEFTERİN İÇİNDE: "3 sorgu" ile "ölçmeye 3 sorgu önce başladık"
        # aynı şey değil ve ikisini ayırt edecek tek yer bu alan.
        "sayac_baslangici": None,
        "beyan": ("geçmiş sorgular geriye dönük damgalanmadı (retro damga yasağı) — sayaç bu "
                  "dosyanın ilk yazımından itibaren sayar"),
    }
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc) \
        .isoformat(timespec="seconds")
    if not doc.get("sayac_baslangici"):
        doc["sayac_baslangici"] = now
    # ARŞİV GEÇİŞİ RESMÎ YAZIM YOLUNDA, AYRI BİR GÖÇ ADIMINDA DEĞİL: ayrı bir betiğe bırakılsaydı
    # o betiğin koşulup koşulmadığı defterden okunamazdı ve işaretsiz bir R0 satırı R1 sayacı gibi
    # okunabilirdi. Burada zaten oku-değiştir-yaz yapıyoruz; geçiş bedava ve idempotent.
    doc["arsiv_gecis"] = {"pencere_id": dataset.ROTATION_ID, "tarih": dataset.ROTATION_DATE,
                          "isaretlenen": int(arsivle(doc)) + int(
                              (doc.get("arsiv_gecis") or {}).get("isaretlenen") or 0)}
    w = doc["windows"].setdefault(fp, {"queries": 0, "first_seen": now, "last_seen": now})
    w["queries"] = int(w.get("queries") or 0) + 1
    w["last_seen"] = now
    # PENCERE DAMGASI: bu satır HANGİ rotasyona ait. Damgasız satır = R1 öncesi (bkz. arsivle).
    w["pencere_id"] = dataset.ROTATION_ID
    if meta:
        w["pencere"] = meta            # okunabilirlik: hash tek başına hangi sınav olduğunu söylemez
    store.write_json(EROSION_FILE, doc)
    return {"fingerprint": fp, "queries": w["queries"], "limit": EROSION_QUERY_LIMIT,
            "extra_margin": extra_margin(w["queries"]), "sayac_baslangici": doc["sayac_baslangici"],
            "pencere_id": dataset.ROTATION_ID}


def status(fp: str) -> dict:
    """SALT OKUMA: sayacı ARTIRMADAN mevcut durumu döner.

    Neden ayrı bir fonksiyon: kapı yasası (`_gate_eval`) aşınma marjını UYGULAMAK zorunda ama
    SAYMAK zorunda değil — ve saymak bir yan etkidir. `_gate_eval` arama döngüsünde, silahlanma
    yolunda ve onlarca testte çağrılıyor; her çağrıda yazan bir yasa, sayacı "kaç kez resmî soru
    soruldu" olmaktan çıkarıp "kaç kez fonksiyon çağrıldı"ya çevirirdi. Sayım RESMÎ giriş
    noktalarında açıkça istenir (`record_erosion=True`), okuma her yerde serbesttir."""
    from . import dataset
    doc = store.read_json(EROSION_FILE, None) or {}
    w = (doc.get("windows") or {}).get(fp) or {}
    q = int(w.get("queries") or 0)
    return {"fingerprint": fp, "queries": q, "limit": EROSION_QUERY_LIMIT,
            "extra_margin": extra_margin(q), "sayac_baslangici": doc.get("sayac_baslangici"),
            "kaydedildi": False, "pencere_id": dataset.ROTATION_ID}


def note(fp: str, meta: dict | None = None) -> dict:
    """`record` ama ASLA yükseltmez: yazım başarısız olursa kapı kararı düşmez, uyarı düşer.
    Bir telemetri defterinin kapıyı durdurma yetkisi yoktur (ama sessiz de kalamaz — YASA 4)."""
    try:
        return {**record(fp, meta), "kaydedildi": True}
    except Exception as e:
        obs.warn("oos_erosion_write_failed", fingerprint=str(fp), error=f"{type(e).__name__}: {e}",
                 detail="aşınma sayacı bu değerlendirmeyi kaydedemedi — sayı EKSİK kalır")
        return {"fingerprint": fp, "queries": None, "limit": EROSION_QUERY_LIMIT,
                "extra_margin": 0.0, "sayac_baslangici": None, "kaydedildi": False}


def report() -> dict:
    """Pano/diagnostics için özet: en çok sorulmuş pencereler + yürürlükteki ek marj.
    Dosya yoksa sayılar SIFIR değil None: "hiç sorgu olmadı" ile "henüz ölçmüyoruz" ayrı hâllerdir.

    ROTASYONDAN SONRA `en_cok` YALNIZ YÜRÜRLÜKTEKİ PENCEREDEN SEÇİLİR (R1, 2026-07-30). Eski hâli
    defterin TAMAMINDA maksimum arıyordu ve rotasyondan sonra bu SESSİZ BİR YANLIŞ HÜKÜM üretirdi:
    arşivlenmiş R0 satırı 434 sorgu taşıyor, R1 ise sıfırdan başlıyor — `max` R0'ı seçer, pano
    "aşınma 434/20, ek marj yürürlükte" yazar ve rotasyonun SONUCU rotasyonun GEREKÇESİ gibi
    görünürdü. Yani panonun okuduğu sayı, kapının uyguladığı marjın (yürürlükteki parmak izinden
    okunur, `status()`) tam tersini söylerdi. Arşiv KAYBOLMUYOR: `arsiv` bloğunda, kendi adıyla ve
    "karşılaştırılamaz" uyarısıyla durur."""
    from . import dataset
    doc = store.read_json(EROSION_FILE, None)
    if not doc or not doc.get("windows"):
        return {"n_pencere": 0, "toplam_sorgu": None, "en_cok": None, "limit": EROSION_QUERY_LIMIT,
                "extra_margin_yururlukte": 0.0, "sayac_baslangici": (doc or {}).get("sayac_baslangici"),
                "pencere_id": dataset.ROTATION_ID, "arsiv": None,
                "kiyas_uyarisi": dataset.PENCERE_KIYAS_UYARISI,
                "beyan": (doc or {}).get("beyan") or
                         "aşınma defteri henüz yazılmadı — ilk resmî kapı değerlendirmesinde doğar"}
    ws = doc["windows"]
    # YÜRÜRLÜKTEKİ = bu rotasyonun damgasını taşıyan. Damgasız satır R1 ÖNCESİdir (arşiv).
    guncel = {k: v for k, v in ws.items() if v.get("pencere_id") == dataset.ROTATION_ID}
    arsiv = {k: v for k, v in ws.items() if k not in guncel}
    en = (max(guncel.items(), key=lambda kv: int(kv[1].get("queries") or 0)) if guncel else None)
    return {"n_pencere": len(guncel),
            # TOPLAM DA YÜRÜRLÜKTEKİ PENCEREDEN: iki sınavın sorgularını toplamak, iki farklı
            # kâğıdın sorularını tek sınavın yükü gibi sunmak olurdu.
            "toplam_sorgu": (sum(int(v.get("queries") or 0) for v in guncel.values())
                             if guncel else None),
            "en_cok": (None if en is None else
                       {"fingerprint": en[0], "queries": en[1].get("queries"),
                        "first_seen": en[1].get("first_seen"), "last_seen": en[1].get("last_seen"),
                        "pencere_id": en[1].get("pencere_id"), "pencere": en[1].get("pencere")}),
            "limit": EROSION_QUERY_LIMIT,
            "extra_margin_yururlukte": (0.0 if en is None else extra_margin(en[1].get("queries"))),
            "sayac_baslangici": doc.get("sayac_baslangici"),
            "pencere_id": dataset.ROTATION_ID, "rotasyon_tarihi": dataset.ROTATION_DATE,
            # ARŞİV AYRI SATIR, AYRI DİL: silinmedi, toplanmadı, kıyaslanmadı.
            "arsiv": ({"n_pencere": len(arsiv),
                       "toplam_sorgu": sum(int(v.get("queries") or 0) for v in arsiv.values()),
                       "pencereler": {k: {"queries": v.get("queries"), "arsiv": v.get("arsiv"),
                                          "last_seen": v.get("last_seen")}
                                      for k, v in arsiv.items()}} if arsiv else None),
            "kiyas_uyarisi": dataset.PENCERE_KIYAS_UYARISI,
            "arsiv_gecis": doc.get("arsiv_gecis"), "beyan": doc.get("beyan")}
