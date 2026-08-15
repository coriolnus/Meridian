"""skill_gorus.py — skill'lerin yapılandırılmış GÖRÜŞ yazıp gerçekleşen sonuçla puanlandığı, icraya dokunmayan görüş defteri.

NE YAPAR — KISIR DÖNGÜNÜN GÖLGE TARAFTAN KIRILMASI. Aktif skill kümesinin aday seçimine ölçülebilir
bir katkısı olup olmadığı bilinmiyordu, çünkü skill'ler üretimde koşmuyor ve Eksen-2 (doğru
olarak) kanıtsız öneri üretmeyi reddediyor — "ölçmek için koşmalı, koşturmak için ölçmeli"
döngüsü. Bu katman döngüyü İCRAYA DOKUNMADAN kırar: deterministik motorun fiilen koşturduğu
skill'ler için yüzey başına görüş satırları türetilir, yüzey başına bir ÇÖZÜCÜ o görüşleri
GERÇEKLEŞEN sonuçla puanlar (sıralayıcıda rank-IC, çıkışta kıyas), hüküm tarih-kümeli bootstrap +
BH-FDR süzgeciyle yüzey-başına kanıt olarak operatöre gider. Şemada beş yüzey vardır (YUZEYLER),
ikisi ölçülür (OLCULEN_YUZEYLER); çözücüsü olmayan yüzeye görüş YAZILMAZ (okuyucusuz yazım yok).

KİLİT GİRİŞLER. `topla` (görüş üretimi; yazım tavanlı, en eskiden yeniye), `kadans` (öğrenme
kadansı kancası; süre örneklemi + p95 tavanı), `rapor` (FDR-sağkalan hüküm yüzeyi), `evren`
(aktif + korumasız + deterministik küme, dışlama muhasebesiyle), `gorus_satiri` (şema doğrulamalı
satır — kusurlu satır atılmaz, ValueError atar), `cozucu_siralayici`/`cozucu_cikis`,
`bootstrap_p`/`bh_fdr`, `defter`.

DEĞİŞMEZLER — GÖLGE/GÖRÜŞ KATMANI SÖZLEŞMESİ. HİÇBİR TERFİ OTOMATİK DEĞİL: bu modül kayıt
defterine, bayrağa, eşiğe, plana, emre DOKUNMAZ — canlı karara hiçbir yol çıkmaz; FDR-sağkalanlar
yalnız Eksen-2 teşhisine ve rapora düşer (motor-içi bayrak yazımı yasağının devamı). İLERİ-BAKIŞ
YOK: görüş satırı yalnız t ve öncesi veriyi taşır; sonuç, çözücünün ayrıca okuduğu SONUÇ
defterlerindedir — ikisini tek satırda birleştirmek görüşün içine cevabı yazmak olurdu. EŞİK İCAT
ETMEZ: bütün eşikler ön-kayıt kartından gelir ve ölçümden ÖNCE donduruldu (`KART_*` sabitleri —
kod onları değiştiremez). Görüş üretimi kadans süresini tavanın üstünde şişiremez (p95 kill'inin
ön alıcısı yazım tavanıdır). Davranışsal tüketici ilk günden bağlıdır ve modülün DIŞINDADIR:
`api._eksen2_gorus()` (pano) + `scheduler._learning_cadence` (öğrenme defteri).

OKUR: skills.catalog/ENGINE_IMPLEMENTED (evren), counterfactuals + trades sonuç defterleri,
exit_efficiency.json (girdi bekçisi).
YAZAR: yalnız kendi iki defteri `state/skill_gorusleri.jsonl` + `state/skill_gorus_durum.json`.
"""
from __future__ import annotations

import datetime as dt
import time

from . import store

# ==================================================================================================
# KART SABİTLERİ (ÖLÇÜMDEN ÖNCE DONDURULDU; kod bunları değiştiremez)
# ==================================================================================================
KART = "EDG-2026-019"
KART_FDR_Q = 0.10           # Benjamini-Hochberg; aile = O YÜZEYDEKİ tüm aktif-korumasız skill'ler
KART_ETKI_RANK_IC = 0.05    # sıralayıcı etki eşiği: |rank-IC| >= 0.05
KART_N_MIN = 30             # skill+yüzey başına asgari görüş; altı "ÖLÇÜLDÜ — ÖRNEKLEM YETERSİZ"
KART_P95_TAVAN = 0.10       # kill#1: görüş üretimi kadans süresini +%10'dan fazla artıramaz
KART_CI = 0.95              # tarih-kümeli bootstrap güven seviyesi

# ŞEMADA BEŞ YÜZEY, BU KARTTA ÖLÇÜLEN İKİ. Kalan üçü çözücüleriyle birlikte AYRI kart ister —
# adlarını buraya yazmak bir vaat değil, şemanın donmuş hâlidir (yarın gelen yüzey yeni ad icat
# etmesin diye). Ölçülmeyen bir yüzeye görüş YAZILMAZ: okuyucusuz yazım (YASA 6).
YUZEYLER = ("aday-uretec", "aday-siralayici", "cikis", "rejim", "boyut")
OLCULEN_YUZEYLER = ("aday-siralayici", "cikis")

GORUS_DEFTERI = "skill_gorusleri.jsonl"     # LİTERAL ad (codelaw.artifact_graph çözebilsin)
DURUM_DEFTERI = "skill_gorus_durum.json"    # son kadans koşusu + süre örneklemleri (p95 kill'i)

# YAZIM TAVANI — kill#1'in ÖN ALICISI, bir kalite ödünü DEĞİL. Defter geçmişe dönük doluyor
# (cf defterinde bugün 7053 çözülmüş satır var); hepsini TEK kadansta yazmak o gecenin döngüsünü
# ölçülebilir biçimde uzatırdı. Tavan EN ESKİDEN yeniye doldurur, yani örneklem tarih sırasını
# korur ve hiçbir gözlem seçilerek atlanmaz. Kuru koşu `tavan=None` ile tamamını yazabilir.
YAZIM_TAVANI = 500
SURE_ORNEK_TAVANI = 60      # süre örneklemi halkası (≈ iki aylık gecelik kadans)
# P95 ÖRNEKLEM TABANI — bir EŞİK DEĞİL, ÖLÇÜLEBİLİRLİK KAPISI (kartın +%10 tavanı DOKUNULMADI).
# Tek gözlemin "p95"i o gözlemin kendisidir; ilk koşu defteri sıfırdan doldurduğu için doğal
# olarak en yavaş koşudur ve ondan verilecek bir KILL hükmü, ölçülmemiş bir kesinliktir
# (`faz5_cikis.MIN_KUME` ile aynı disiplin: tek kümede aralık kurulamaz).
P95_MIN_ORNEK = 5
P_ARAMA_ADIM = 7            # bootstrap p ikili aramasının adım sayısı → çözünürlük 2^-7 ≈ 0,008


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


# ==================================================================================================
# EVREN — AKTİF + KORUMASIZ + DETERMİNİSTİK
# ==================================================================================================
def evren() -> dict:
    """Ölçüm evreni ve DIŞLAMA MUHASEBESİ: kimin neden dışarıda kaldığı sayıyla yazılır.

    ÜÇ KAPI, hepsi mevcut kaynaklardan (bu modül yeni bir sınıflandırma İCAT ETMEZ):
      * AKTİF      → `skills.aktif_katalog()` (yaşam-döngüsü tek yerden; arşiv aday değil),
      * KORUMASIZ  → `skills.PROTECTED` dışında (güvenlik katmanı hakkında hüküm verilmez),
      * DETERMİNİSTİK → `skills.ENGINE_IMPLEMENTED` içinde. Bu küme "motorun FİİLEN koşturduğu"
        skill'lerdir; dışındaki her ad bir SKILL.md klasörüdür, yani bir LLM-ajan bağlamı için
        yazılmıştır ve deterministik motor onu çalıştırmaz. Onlara görüş atfetmek, `skills.py`nin
        baştan beri önlediği "invoked yalanı"nın ta kendisi olurdu.
    """
    from . import skills
    icinde, disarida = [], {}
    for c in skills.catalog():
        ad = c["name"]
        if c.get("yasam_dongusu") == skills.ARSIV:
            disarida[ad] = "arsiv"
        elif c["protected"]:
            disarida[ad] = "korumali"
        elif ad not in skills.ENGINE_IMPLEMENTED:
            # LLM-BAĞLAMLI SKILL: motor koşturmuyor, dolayısıyla ÜRETTİĞİ bir görüş de yok.
            disarida[ad] = "llm_baglamli_motor_kosturmuyor"
        else:
            icinde.append(ad)
    return {"evren": sorted(icinde), "disarida": disarida,
            "sayim": {"evren": len(icinde),
                      **{k: sum(1 for v in disarida.values() if v == k)
                         for k in sorted(set(disarida.values()))}},
            "beyan": ("YALNIZ aktif + korumasız + deterministik. Küme ÖLÇÜM ANINDA kaynaktan "
                      "türetilir — sabit liste yazılmaz (C10).")}


# ==================================================================================================
# GÖRÜŞ SATIRI — ŞEMA VE YAZIM
# ==================================================================================================
_ALANLAR = ("skill", "ts", "yuzey", "hedef", "skor", "karar", "gerekce_ozeti", "tarih")


def gorus_satiri(skill: str, yuzey: str, hedef: str, *, tarih: str,
                 skor: float | None = None, karar: str | None = None,
                 gerekce_ozeti: str = "", ts: str | None = None) -> dict:
    """Tek görüş satırı — şema doğrulamasıyla. Kusurlu satır ATILMAZ, `ValueError` atar.

    `skor` ve `karar` BİRLİKTE de boş olamaz: görüşsüz bir görüş satırı, defteri sayı olarak
    şişirip hükmü sulandırırdı. `tarih` GÖZLEMİN SEANSIDIR (ts değil): tarih-kümeli bootstrap'ın
    yeniden örneklediği birim odur ve iki alanı karıştırmak kümeyi saniyeye böler."""
    if yuzey not in YUZEYLER:
        raise ValueError(f"bilinmeyen yüzey {yuzey!r} — şemadaki beş yüzey: {YUZEYLER}")
    if yuzey not in OLCULEN_YUZEYLER:
        raise ValueError(f"'{yuzey}' yüzeyinin ÇÖZÜCÜSÜ YOK (EDG-2026-019 yalnız "
                         f"{OLCULEN_YUZEYLER} ölçer) — okuyucusuz yazım YASA 6 ihlalidir")
    if not skill or not hedef or not tarih:
        raise ValueError("skill/hedef/tarih zorunlu — kimliksiz görüş çözülemez")
    if skor is None and not karar:
        raise ValueError("skor VEYA karar zorunlu — görüşsüz görüş satırı yazılmaz")
    return {"skill": str(skill), "ts": ts or _now(), "yuzey": yuzey, "hedef": str(hedef),
            "skor": (None if skor is None else float(skor)),
            "karar": (str(karar) if karar else None),
            "gerekce_ozeti": str(gerekce_ozeti)[:200], "tarih": str(tarih)}


def defter() -> list[dict]:
    """Görüş defterinin tamamı (saf okuma)."""
    return store.read_jsonl(GORUS_DEFTERI)


def _anahtar(g: dict) -> tuple:
    return (g.get("skill"), g.get("yuzey"), g.get("hedef"))


# ==================================================================================================
# ÜRETİM — GÖRÜŞLER MEVCUT DEFTERLERDEN TÜRETİLİR (yeni bir veri yolu AÇILMAZ)
# ==================================================================================================
# NEREDEN GELİYOR. İki yüzeyin ham maddesi ZATEN yazılı ve iki defterde duruyor:
#   * karşı-olgusal defter (`counterfactual.resolved_rows`) — her satır `screener` alanıyla HANGİ
#     skill'in adayı olduğunu taşır, `score` alanıyla o skill'in plan anındaki
#     SIRALAMA GÖRÜŞÜNÜ, `date` ile seansı;
#   * gerçek işlem defteri (`trades.jsonl`) — `skill_chain[0]` aynı atfı, `score` aynı görüşü taşır.
# Yani görüş defteri yeni bir ölçüm ALETİ değil, dağınık duran bir görüşün YAPILANDIRILMIŞ hâlidir.
# `setup`tan skill'e düşme yolu BİLEREK kullanılmaz: `screener`/`skill_chain` YAZILI atıftır,
# `screener_for(setup)` ise bir TAHMİNDİR ve tahmini kanıt gibi deftere yazmak uydurmadır.
def _cf_satirlari() -> list[dict]:
    from . import counterfactual
    return counterfactual.resolved_rows(entered_only=True)


def _trade_satirlari() -> list[dict]:
    return [t for t in store.read_jsonl("trades.jsonl") if t.get("r_multiple") is not None]


# ==================================================================================================
# ALAN SEÇİMİ: KANONİK AD TEKTİR, YEDEK-AD ZİNCİRİ YOKTUR (parity)
# ==================================================================================================
# İlk yazımda iki `a or b` takası vardı ve İKİSİ DE sessiz bir ölçüm hatasıydı — kozmetik değil:
#
#   (1) `ts_open or ts_close` → TARİH KÜMESİNİ YANLIŞ SEÇER. Kümeli bootstrap'ın yeniden
#       örneklediği birim SEANStır ve görüşün seansı AÇILIŞ günüdür. Pazartesi açılıp cuma kapanan
#       bir işlem `ts_close`a düşseydi cuma kümesine yazılırdı: gözlem, hiç görüş üretilmemiş bir
#       güne bağlanır ve küme yapısı — yani aralığın GENİŞLİĞİ — bozulurdu. Hata tek yönlü de
#       değildir, yani "muhafazakâr" savunması da yok.
#   (2) `plan_id or id` → İKİ AYRI VARLIĞI tek anahtara katlar. `hedef` görüşün NEYE dair
#       olduğudur ve görüş PLANA (adaya) dairdir; `trades.id` işlemin kendi kimliğidir. İkisini
#       yedeklemek, join anahtarının şemaya göre sessizce tür değiştirmesi demekti.
#
# KURAL: her alanın TEK kanonik adı vardır; kanonik ad yoksa satır ÖLÇÜLEMEZ sayılır, ADIYLA
# sayılır ve düşürülür. Sessiz düşürme yok, yedek-ad zinciri yok (defterlerin `rr_expected` ↔
# `r_multiple_expected` dersi: yaması olmayan tüketici satırı sessizce eler).
_KANONIK = {"tarih": "ts_open", "hedef": "plan_id"}


def _gozlemler() -> dict:
    """{"satirlar": [...], "atlanan": {...}} — İKİ defterin ortak dili + ELEME MUHASEBESİ.

    `kaynak` DÜŞMEZ: cf satırı statik-bracket simülasyonudur ve gerçek çıkışı sistematik farklı
    ölçer; iki katmanı tek havuza atıp künyeyi atmak, simüle kanıtı gerçek gibi göstermekti."""
    out: list[dict] = []
    atlanan = {"cf_screenersiz_veya_rsiz": 0, "trade_skill_zinciri_yok": 0,
               "trade_kanonik_tarih_yok": 0, "trade_kanonik_hedef_yok": 0}
    for r in _cf_satirlari():
        sk = r.get("screener")
        if not sk or r.get("r_multiple") is None:
            atlanan["cf_screenersiz_veya_rsiz"] += 1
            continue
        out.append({"skill": sk, "tarih": str(r.get("date") or "?"), "hedef": str(r.get("id")),
                    "skor": r.get("score"), "karar": r.get("exit_reason"),
                    "r": r.get("r_multiple"), "mfe_r": r.get("mfe_r"), "kaynak": "cf"})
    for t in _trade_satirlari():
        zincir = t.get("skill_chain") or []
        sk = zincir[0] if zincir else None
        if not sk:
            atlanan["trade_skill_zinciri_yok"] += 1
            continue
        ts = t.get(_KANONIK["tarih"])          # AÇILIŞ — görüşün seansı; kapanış BAŞKA bir olgudur
        if not ts:
            atlanan["trade_kanonik_tarih_yok"] += 1
            continue
        pid = t.get(_KANONIK["hedef"])         # PLAN kimliği — görüş plana dairdir, işleme değil
        if not pid:
            atlanan["trade_kanonik_hedef_yok"] += 1
            continue
        out.append({"skill": sk, "tarih": str(ts)[:10], "hedef": str(pid),
                    "skor": t.get("score"), "karar": t.get("exit_reason"),
                    "r": t.get("r_multiple"), "mfe_r": t.get("mfe_r"), "kaynak": "gercek"})
    return {"satirlar": out, "atlanan": atlanan}


def topla(apply: bool = True, tavan: int | None = YAZIM_TAVANI) -> dict:
    """Evrendeki skill'lerin görüşlerini defterle — yalnız YENİ olanları (anahtar: skill+yüzey+hedef).

    `apply=False`: hiçbir şey yazılmaz, ne yazılacağı döner (testler + kuru koşu)."""
    ev = evren()
    izinli = set(ev["evren"])
    var = {_anahtar(g) for g in defter()}
    yeni: list[dict] = []
    gz = _gozlemler()
    # ELEME MUHASEBESİ TEK SÖZLÜKTE: kaynak defterde düşen satır ile burada düşen satır AYRI
    # sebeplerdir ve ikisi de görünür kalmalı — "az görüş yazıldı"nın nedeni ikisinden biridir.
    atlanan = {"evren_disi": 0, "zaten_var": 0, "skorsuz": 0, "cikis_olcusuz": 0, **gz["atlanan"]}
    for g in sorted(gz["satirlar"], key=lambda x: (x["tarih"], x["hedef"])):
        sk = g["skill"]
        if sk not in izinli:
            atlanan["evren_disi"] += 1
            continue
        # --- aday-siralayici: skill'in plan anındaki SKOR görüşü -----------------------------
        if g.get("skor") is None:
            atlanan["skorsuz"] += 1
        else:
            s = gorus_satiri(sk, "aday-siralayici", g["hedef"], tarih=g["tarih"],
                             skor=g["skor"],
                             gerekce_ozeti=f"aday skoru (plan anı) · kaynak={g['kaynak']}")
            if _anahtar(s) in var:
                atlanan["zaten_var"] += 1
            else:
                yeni.append(s); var.add(_anahtar(s))
        # --- cikis: adayın çıkış kararı ------------------------------------------------------
        # ATIF DÜRÜSTÇE YAZILIR: çıkış kuralı MOTORUNdur, aday bu skill'indir. Gerekçe özeti bunu
        # satırın kendi üstünde söyler — "skill'in çıkış kuralı" diye okunursa ölçüm yalan söyler.
        if g.get("mfe_r") is None or g.get("r") is None:
            atlanan["cikis_olcusuz"] += 1
            continue
        c = gorus_satiri(sk, "cikis", g["hedef"], tarih=g["tarih"],
                         karar=str(g.get("karar") or "?"),
                         gerekce_ozeti=("motor çıkış kuralı, aday bu skill'den · "
                                        f"kaynak={g['kaynak']}"))
        if _anahtar(c) in var:
            atlanan["zaten_var"] += 1
        else:
            yeni.append(c); var.add(_anahtar(c))
    kirpilan = 0
    if tavan is not None and len(yeni) > tavan:
        kirpilan = len(yeni) - tavan
        yeni = yeni[:tavan]              # EN ESKİDEN yeniye (liste tarih sıralı) — seçim yok
    if apply:
        for s in yeni:
            store.append_jsonl(GORUS_DEFTERI, s)
    return {"yazilan": len(yeni), "kirpilan": kirpilan, "tavan": tavan,
            "atlanan": atlanan, "evren": ev["evren"], "uygulandi_mi": bool(apply),
            "defter_toplam": len(var)}


# ==================================================================================================
# İSTATİSTİK — TARİH-KÜMELİ BOOTSTRAP (YENİDEN KULLANIM) + BOOTSTRAP p + BH-FDR
# ==================================================================================================
def _ci(degerler, tarihler, seviye: float = KART_CI) -> dict:
    """`faz5_cikis.tarih_kumeli_bootstrap` — YENİDEN YAZILMAZ, ÇAĞRILIR.

    Aynı seansta üretilen görüşler aynı açılışı/rejimi paylaşır ve BAĞIMSIZ SAYILAMAZ; düz (IID)
    bootstrap aralığı sistematik olarak daraltır ve hükmü kilidi AÇMA yönünde kaydırır. Yöntem
    kartla dondurulmuştur; ikinci bir uygulama, iki farklı aralık demekti."""
    from .faz5_cikis import tarih_kumeli_bootstrap
    return tarih_kumeli_bootstrap(degerler, tarihler, seviye=seviye)


def bootstrap_p(degerler, tarihler) -> dict:
    """İki yönlü bootstrap p — AYNI kümeli bootstrap'tan, GÜVEN SEVİYESİ üzerinde ikili arama ile.

    NEDEN BÖYLE. `tarih_kumeli_bootstrap` replikasyonları döndürmez, ARALIK döndürür; ama tohum
    sabit olduğu için replikasyon havuzu her seviyede AYNIDIR ve "aralık sıfırı dışlıyor mu?"
    sorusu seviyede MONOTONDUR. p = 1 − sup{s : CI(s) sıfırı dışlıyor}. Yani bu, ikinci bir
    yöntem değil, BİRİNCİ yöntemin tersten okunmasıdır — kartın dondurduğu bootstrap'ın dışına
    çıkılmaz ve ikinci bir yeniden-örnekleme uygulaması doğmaz.

    ÇÖZÜNÜRLÜK BEYANLI ve ÇIKTIDA (`cozunurluk`): `P_ARAMA_ADIM` adım → 2^-adım. Dönen `p`
    bracket'in ÜST ucudur, yani HER ZAMAN muhafazakârdır (kilidi açma yönünde asla yanılmaz)."""
    taban = _ci(degerler, tarihler)
    if taban.get("lo") is None:
        return {"p": None, "n": taban.get("n"), "n_kume": taban.get("n_kume"), "ort": taban.get("ort"),
                "neden": taban.get("neden") or "aralık kurulamadı — p ÖLÇÜLEMEDİ"}
    # 1) En sert uçtan başla: burada bile dışlıyorsa p çözünürlüğün altındadır.
    en_sert = 1.0 - 2.0 ** -P_ARAMA_ADIM
    if _ci(degerler, tarihler, seviye=en_sert).get("sifiri_disliyor"):
        return {"p": round(1.0 - en_sert, 4), "ust_sinir": True, "n": taban["n"],
                "n_kume": taban["n_kume"], "ort": taban["ort"], "neden": None,
                "cozunurluk": round(2.0 ** -P_ARAMA_ADIM, 4)}
    lo, hi = 0.0, en_sert          # CI(lo) dışlar (varsayım), CI(hi) dışlamaz
    if not _ci(degerler, tarihler, seviye=lo).get("sifiri_disliyor"):
        # Medyan replikasyon sıfırın karşı tarafında bile değil → p, ölçülebilir en büyük değerde.
        return {"p": 1.0, "n": taban["n"], "n_kume": taban["n_kume"], "ort": taban["ort"],
                "neden": None, "cozunurluk": round(2.0 ** -P_ARAMA_ADIM, 4)}
    for _ in range(P_ARAMA_ADIM):
        orta = (lo + hi) / 2.0
        if _ci(degerler, tarihler, seviye=orta).get("sifiri_disliyor"):
            lo = orta
        else:
            hi = orta
    return {"p": round(1.0 - lo, 4), "n": taban["n"], "n_kume": taban["n_kume"],
            "ort": taban["ort"], "neden": None, "cozunurluk": round(2.0 ** -P_ARAMA_ADIM, 4)}


def bh_fdr(pler: dict, q: float = KART_FDR_Q) -> dict:
    """Benjamini-Hochberg — aile başına. `pler`: {ad: p}. Dönen: {ad: {p, sira, esik, sagkalan}}.

    ÖLÇÜLEMEYEN p AİLEYE GİRMEZ (paydayı şişirmez) ve `sagkalan=None` ile ADIYLA durur: bir
    ölçülememişliği "elendi" saymak, ölçülmemiş bir sonucu ölçülmüş göstermektir."""
    olculen = {a: float(p) for a, p in pler.items() if p is not None}
    m = len(olculen)
    out: dict[str, dict] = {a: {"p": None, "sira": None, "esik": None, "sagkalan": None,
                                "neden": "p ÖLÇÜLEMEDİ — aileye girmez"}
                            for a, p in pler.items() if p is None}
    if not m:
        return {"aile": out, "m": 0, "q": q, "kritik_p": None}
    sirali = sorted(olculen.items(), key=lambda kv: kv[1])
    kritik = None
    for i, (_, p) in enumerate(sirali, start=1):
        if p <= q * i / m:
            kritik = p                 # BH: en büyük p_(i) <= q·i/m — ve ONUN ALTINDAKİ HEPSİ geçer
    for i, (ad, p) in enumerate(sirali, start=1):
        out[ad] = {"p": p, "sira": i, "esik": round(q * i / m, 6),
                   "sagkalan": bool(kritik is not None and p <= kritik), "neden": None}
    return {"aile": out, "m": m, "q": q, "kritik_p": kritik}


# ==================================================================================================
# ÇÖZÜCÜ 1 — ADAY SIRALAYICI (skor → gerçekleşen R, rank-IC)
# ==================================================================================================
def _rank_ic_ayristir(ciftler: list[tuple[float, float]]) -> tuple:
    """rank-IC'yi GÖZLEM BAŞINA katkılara ayrıştır: IC = ort(z_i).

    NEDEN GEREKLİ. `tarih_kumeli_bootstrap` ORTALAMANIN aralığını verir; rank-IC bir ortalama
    değildir. Standartlaştırılmış rütbelerin çarpımı (`z_i`) alınınca IC TAM OLARAK o çarpımların
    ortalamasıdır ve kümeli bootstrap aynen uygulanabilir.
    BEYANLI SINIR: rütbeler TAM ÖRNEKLEMDE bir kez hesaplanır, her replikasyonda yeniden
    hesaplanmaz. Bu standart "sabit-rütbe" yaklaşımıdır; rütbeleri de yeniden hesaplayan bir
    bootstrap ham çiftleri yeniden örnekleyen bir ilkel isterdi ve o ilkel kartta DONDURULMUŞ
    olanın dışındadır. Yaklaşımın yönü beyan edilir, gizlenmez.

    Dönen: (z listesi, nokta_tahmini) — tutarsızlık varsa nokta tahmini None."""
    from . import analytics
    import numpy as np
    if len(ciftler) < 2:
        return [], None
    a = np.asarray(ciftler, float)
    rx, ry = analytics._rank_avg(a[:, 0]), analytics._rank_avg(a[:, 1])
    den = rx.std() * ry.std()
    if den <= 0:
        return [], None                # tek taraf sabit → korelasyon TANIMSIZ (0.0 DEĞİL)
    z = ((rx - rx.mean()) * (ry - ry.mean())) / den
    ic = analytics.spearman_ic(ciftler)          # modülün TEK rütbeleme yöntemi (çapraz doğrulama)
    if ic is None or abs(float(z.mean()) - ic) > 1e-9 * max(1.0, abs(ic)):
        return [], None                # iki hesap ayrışıyorsa hüküm VERİLMEZ
    return [float(v) for v in z], float(ic)


def cozucu_siralayici(gorusler: list[dict], sonuclar: dict) -> dict:
    """Skill başına: skor görüşü ile GERÇEKLEŞEN R arasındaki rank-IC + kümeli CI + bootstrap p."""
    per: dict[str, list] = {}
    eslesmeyen = 0
    for g in gorusler:
        if g.get("yuzey") != "aday-siralayici" or g.get("skor") is None:
            continue
        s = sonuclar.get(g.get("hedef"))
        if s is None or s.get("r") is None:
            eslesmeyen += 1
            continue
        per.setdefault(g["skill"], []).append((float(g["skor"]), float(s["r"]), str(g.get("tarih"))))
    out: dict[str, dict] = {}
    for sk, rows in sorted(per.items()):
        n = len(rows)
        if n < KART_N_MIN:
            out[sk] = {"n": n, "kova": f"ÖRNEKLEM YETERSİZ {n}/{KART_N_MIN}",
                       "olcum": None, "p": None}
            continue
        z, ic = _rank_ic_ayristir([(a, b) for a, b, _ in rows])
        if ic is None:
            out[sk] = {"n": n, "kova": "ÖLÇÜLEMEDİ", "olcum": None, "p": None,
                       "neden": "rank-IC tanımsız (skor ya da R rütbelerinde değişim yok)"}
            continue
        tarihler = [t for *_, t in rows]
        ci, pp = _ci(z, tarihler), bootstrap_p(z, tarihler)
        out[sk] = {"n": n, "kova": "OLCULDU",
                   "olcum": {"rank_ic": round(ic, 4), "lo": ci.get("lo"), "hi": ci.get("hi"),
                             "n_kume": ci.get("n_kume"), "yontem": ci.get("yontem")},
                   "p": pp.get("p"), "p_detay": pp,
                   # KART: |rank-IC| >= 0.05 — MUTLAK değer, yani eşiği geçmek iki yönde de
                   # mümkündür. Yön ayrı bir alanda durur ki terfi ile emeklilik karışmasın.
                   "etki_esigi_gecti": bool(abs(ic) >= KART_ETKI_RANK_IC),
                   "yon": (1 if ic > 0 else (-1 if ic < 0 else 0))}
    return {"skiller": out, "eslesmeyen_gorus": eslesmeyen,
            "metrik": "rank-IC (skor → gerçekleşen R)", "etki_esigi": KART_ETKI_RANK_IC}


# ==================================================================================================
# ÇÖZÜCÜ 2 — ÇIKIŞ (exit_efficiency: masada bırakılan R)
# ==================================================================================================
# METRİK TANIMI VE NEDENİ. `analytics.exit_efficiency` çıkış nedeni başına `left_r = MFE − R`
# ("masada bırakılan ödül") ölçer; DÜŞÜK olan iyidir. Kart "çıkış-katkısı > 0 CI-altı" ister, yani
# YÜKSEK olanın iyi olduğu bir büyüklük. İkisini bağlayan tek dürüst dönüşüm HAVUZA GÖRE FARKtır:
#     katki_i = ort_left_r(HAVUZ) − left_r_i
# Pozitif katkı = "bu skill'in adayları havuz ortalamasından DAHA AZ ödül bırakıyor". Havuz
# ortalaması aynı örneklemden kestirilir ve bu BEYAN EDİLİR (kestirim hatası aralığa girmez);
# mutlak bir `left_r` eşiği icat etmek ise kartta olmayan bir eşik yazmak olurdu.
def cozucu_cikis(gorusler: list[dict], sonuclar: dict) -> dict:
    """Skill başına: havuza göre çıkış katkısı (−left_r farkı) + kümeli CI + bootstrap p."""
    per: dict[str, list] = {}
    eslesmeyen, havuz = 0, []
    for g in gorusler:
        if g.get("yuzey") != "cikis":
            continue
        s = sonuclar.get(g.get("hedef"))
        if s is None or s.get("r") is None or s.get("mfe_r") is None:
            eslesmeyen += 1
            continue
        left = float(s["mfe_r"]) - float(s["r"])
        per.setdefault(g["skill"], []).append((left, str(g.get("tarih"))))
        havuz.append(left)
    if not havuz:
        return {"skiller": {}, "eslesmeyen_gorus": eslesmeyen, "havuz_ort_left_r": None,
                "metrik": "çıkış katkısı = havuz ort. left_r − skill left_r"}
    havuz_ort = sum(havuz) / len(havuz)
    out: dict[str, dict] = {}
    for sk, rows in sorted(per.items()):
        n = len(rows)
        if n < KART_N_MIN:
            out[sk] = {"n": n, "kova": f"ÖRNEKLEM YETERSİZ {n}/{KART_N_MIN}",
                       "olcum": None, "p": None}
            continue
        katkilar = [havuz_ort - left for left, _ in rows]
        tarihler = [t for _, t in rows]
        ci, pp = _ci(katkilar, tarihler), bootstrap_p(katkilar, tarihler)
        out[sk] = {"n": n, "kova": "OLCULDU",
                   "olcum": {"katki": round(sum(katkilar) / n, 4),
                             "left_r": round(sum(l for l, _ in rows) / n, 4),
                             "lo": ci.get("lo"), "hi": ci.get("hi"),
                             "n_kume": ci.get("n_kume"), "yontem": ci.get("yontem")},
                   "p": pp.get("p"), "p_detay": pp,
                   # KART: çıkış tarafında etki eşiği "CI-altı > 0" — ayrı bir sayı DEĞİL.
                   # SİMETRİĞİ (CI-üstü < 0) TERFİ değil EMEKLİLİK işaretidir; kart bu katmanın
                   # "iki yönlü kestiğini" açıkça yazar, o yüzden yön AYRI alanda taşınır.
                   "etki_esigi_gecti": bool(ci.get("lo") is not None and ci["lo"] > 0),
                   "yon": (1 if (ci.get("lo") is not None and ci["lo"] > 0) else
                           (-1 if (ci.get("hi") is not None and ci["hi"] < 0) else 0))}
    return {"skiller": out, "eslesmeyen_gorus": eslesmeyen,
            "havuz_ort_left_r": round(havuz_ort, 4),
            "metrik": "çıkış katkısı = havuz ort. left_r − skill left_r (POZİTİF = daha az ödül bıraktı)",
            "beyan": ("havuz ortalaması AYNI örneklemden kestirilir; kestirim hatası aralığa "
                      "GİRMEZ ve bu bir yaklaşımdır — mutlak bir left_r eşiği kartta YOK")}


# ==================================================================================================
# GİRDİ BEKÇİSİ (kill#4) — ÇÖP GİRDİ, ÇÖP HÜKÜM ZİNCİRİ KAPALI
# ==================================================================================================
def _girdi_bekcisi() -> dict:
    """Çözücü girdileri sağlam mı? Bozuksa O YÜZEYİN hükmü VERİLMEZ (kill#4).

    "Hüküm yok" ile "hüküm olumsuz" AYRI hâllerdir: bayat bir defterle verilen olumsuz hüküm,
    bir skill'i olmayan bir kanıtla emekliye yollardı."""
    cf_n = len(_cf_satirlari())
    ee = store.read_json("exit_efficiency.json", None)
    return {
        "aday-siralayici": ({"saglikli": True, "neden": None} if cf_n
                            else {"saglikli": False,
                                  "neden": "karşı-olgusal defter BOŞ — skor↔R eşleşmesi kurulamaz"}),
        "cikis": ({"saglikli": True, "neden": None}
                  if isinstance(ee, dict) and (ee.get("n") or 0) > 0 else
                  {"saglikli": False,
                   "neden": ("`exit_efficiency.json` yok/boş — çıkış çözücüsünün girdisi kendi "
                             "bekçisinde ÜRETMEMİŞ işaretli; hüküm VERİLMEZ")}),
    }


# ==================================================================================================
# RAPOR — SAF OKUMA, HİÇBİR TERFİ OTOMATİK DEĞİL
# ==================================================================================================
def rapor() -> dict:
    """Görüş defterinin hükmü: yüzey → skill → kova + FDR ailesi. HİÇBİR ŞEY UYGULAMAZ.

    `terfi_adaylari` bir EYLEM DEĞİL bir LİSTEDİR: FDR-sağkalan + etki eşiği + n_min üçünü birden
    geçen skill'ler operatöre KANITLA gider. Bu modül ne kayıt defterine ne bir bayrağa yazar."""
    gorusler = defter()
    gz = _gozlemler()
    sonuclar = {g["hedef"]: g for g in gz["satirlar"]}
    bekci = _girdi_bekcisi()
    yuzeyler: dict[str, dict] = {}
    terfi, emeklilik = [], []
    for yuzey, cozucu in (("aday-siralayici", cozucu_siralayici), ("cikis", cozucu_cikis)):
        if not bekci[yuzey]["saglikli"]:
            yuzeyler[yuzey] = {"durum": "HÜKÜM YOK", "neden": bekci[yuzey]["neden"],
                               "skiller": {}, "fdr": None}
            continue
        c = cozucu(gorusler, sonuclar)
        fdr = bh_fdr({sk: v.get("p") for sk, v in c["skiller"].items()})
        for sk, v in c["skiller"].items():
            v["fdr"] = fdr["aile"].get(sk)
            sagkalan = bool((v.get("fdr") or {}).get("sagkalan"))
            yeterli = sagkalan and (v.get("n") or 0) >= KART_N_MIN
            etki = ((v.get("olcum") or {}).get("rank_ic")
                    if yuzey == "aday-siralayici" else (v.get("olcum") or {}).get("katki"))
            # İKİ YÖNLÜ KESİM (kart): aynı üç kapı (FDR + etki + n_min) POZİTİF yönde terfi
            # ADAYI, NEGATİF yönde emeklilik İŞARETİ üretir. Tek yön kodlanmış olsaydı katman
            # yalnız iyi haberi görürdü — kartın "değeri terfi kadar EMEKLİLİK" cümlesinin
            # kodda karşılığı kalmazdı ve negatif kanıt sessizce düşerdi.
            v["terfi_adayi"] = bool(yeterli and v.get("etki_esigi_gecti") and (v.get("yon") or 0) > 0)
            v["emeklilik_isareti"] = bool(yeterli and (v.get("yon") or 0) < 0
                                          and (abs(etki) >= KART_ETKI_RANK_IC
                                               if yuzey == "aday-siralayici" else True))
            if v["terfi_adayi"]:
                terfi.append({"skill": sk, "yuzey": yuzey, "n": v["n"], "etki": etki,
                              "p": v.get("p")})
            elif v["emeklilik_isareti"]:
                emeklilik.append({"skill": sk, "yuzey": yuzey, "n": v["n"], "etki": etki,
                                  "p": v.get("p"),
                                  "beyan": ("FDR-sağkalan NEGATİF — kart 3 ARDIŞIK pencere ister; "
                                            "pencere sayacı bu turda YOK, bu satır bir İŞARETTİR, "
                                            "emeklilik ÖNERİSİ değildir")})
        yuzeyler[yuzey] = {"durum": "ölçüldü", "neden": None, "skiller": c["skiller"],
                           "fdr": {k: fdr[k] for k in ("m", "q", "kritik_p")},
                           "metrik": c.get("metrik"), "eslesmeyen_gorus": c.get("eslesmeyen_gorus")}
    kovalar: dict[str, int] = {}
    for y in yuzeyler.values():
        for v in y.get("skiller", {}).values():
            kovalar[v.get("kova", "?")] = kovalar.get(v.get("kova", "?"), 0) + 1
    return {
        "kart": KART, "ts": _now(),
        "defter_n": len(gorusler), "evren": evren(),
        "yuzeyler": yuzeyler, "kova_sayimi": kovalar,
        # SONUÇ TARAFININ ELEMESİ DE RAPORDA: bir yüzeyin örneklemi beklenenden küçükse sebep
        # görüş tarafında değil SONUÇ tarafında olabilir (kanonik alanı olmayan satırlar).
        "sonuc_elemesi": gz["atlanan"],
        "girdi_bekcisi": bekci,
        # İKİ YÖNLÜ KESER (kart): FDR-sağkalan NEGATİF etki bir EMEKLİLİK kanıtıdır. Bu liste de
        # yalnız bir listedir — kartın "3 ardışık pencere" kuralı pencere sayımı ister ve o sayım
        # bu turda YOK; liste "aday" der, "emekli et" DEMEZ.
        "terfi_adaylari": terfi, "emeklilik_isaretleri": emeklilik,
        "esikler": {"fdr_q": KART_FDR_Q, "rank_ic": KART_ETKI_RANK_IC, "n_min": KART_N_MIN,
                    "ci": KART_CI, "p95_tavan": KART_P95_TAVAN},
        "beyan": ("HİÇBİR TERFİ/EMEKLİLİK OTOMATİK DEĞİL: bu rapor kayıt defterine, bayrağa, "
                  "eşiğe ya da plana DOKUNMAZ. FDR-sağkalanlar Eksen-2 teşhisine ve operatöre "
                  "KANITLA gider (2026-08-06 kararının devamı)."),
    }


# ==================================================================================================
# KADANS + p95 ÖLÇÜM DÜZENEĞİ (kill#1)
# ==================================================================================================
def _yuzdelik(vals: list[float], q: float):
    if not vals:
        return None
    s = sorted(vals)
    return round(s[min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))], 2)


def kadans(apply: bool = True, oncesi_ms: float | None = None,
           tavan: int | None = YAZIM_TAVANI) -> dict:
    """Kadans adımı: görüş topla → rapor et → SÜRESİNİ ÖLÇ. Deterministik, kotasız, LLM'siz.

    p95 ÖLÇÜM DÜZENEĞİ (kill#1: "+%10'dan fazla artırırsa katman KAPATILIR"). Ölçülen iki sayı:
      * `sure_ms` — bu adımın kendi süresi (her koşuda halkaya yazılır, tavanı `SURE_ORNEK_TAVANI`),
      * `pay` = sure_ms / oncesi_ms — adımın, KENDİSİNDEN ÖNCE koşan kadansın üstüne eklediği oran.
    Kill hükmü `p95(pay) > KART_P95_TAVAN` ile verilir. `oncesi_ms` ölçülemediyse `pay` None'dır
    ve kill "ÖLÇÜLEMEDİ" der — 0 demez (uydurma yasağı: ölçülmemiş bir gecikme, yok sayılmaz)."""
    t0 = time.perf_counter()
    t = topla(apply=apply, tavan=tavan)
    r = rapor()
    sure_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    pay = (round(sure_ms / oncesi_ms, 4) if (oncesi_ms and oncesi_ms > 0) else None)
    d = store.read_json(DURUM_DEFTERI, None) or {}
    ornek = [x for x in (d.get("ornekler") or []) if isinstance(x, dict)]
    ornek.append({"ts": _now(), "sure_ms": sure_ms, "oncesi_ms": oncesi_ms, "pay": pay,
                  "yazilan": t["yazilan"]})
    ornek = ornek[-SURE_ORNEK_TAVANI:]
    sureler = [float(x["sure_ms"]) for x in ornek if x.get("sure_ms") is not None]
    paylar = [float(x["pay"]) for x in ornek if x.get("pay") is not None]
    p95_pay = _yuzdelik(paylar, 0.95)
    if p95_pay is None:
        kill = {"durum": "ÖLÇÜLEMEDİ", "p95_pay": None, "tavan": KART_P95_TAVAN,
                "n_ornek": len(paylar),
                "neden": "kadans süresi (`oncesi_ms`) ölçülmedi — pay kurulamadı, 0 SAYILMAZ"}
    elif len(paylar) < P95_MIN_ORNEK:
        kill = {"durum": "ÖLÇÜLÜYOR", "p95_pay": p95_pay, "tavan": KART_P95_TAVAN,
                "n_ornek": len(paylar),
                "neden": (f"örneklem {len(paylar)}/{P95_MIN_ORNEK} — tek/az koşudan p95 hükmü "
                          f"VERİLMEZ (ilk koşu defteri sıfırdan doldurur, doğal olarak en "
                          f"yavaşıdır). Ölçülen pay {p95_pay} kayda geçer, KILL geçmez.")}
    else:
        kill = {"durum": ("KILL" if p95_pay > KART_P95_TAVAN else "temiz"),
                "p95_pay": p95_pay, "tavan": KART_P95_TAVAN, "n_ornek": len(paylar),
                "neden": (f"p95 pay {p95_pay} {'>' if p95_pay > KART_P95_TAVAN else '<='} "
                          f"{KART_P95_TAVAN} — kill#1")}
    out = {"ts": _now(), "kart": KART, "sure_ms": sure_ms, "oncesi_ms": oncesi_ms, "pay": pay,
           "sure_p50_ms": _yuzdelik(sureler, 0.5), "sure_p95_ms": _yuzdelik(sureler, 0.95),
           "kill_p95": kill, "toplama": t, "rapor": r, "ornekler": ornek,
           "uygulandi_mi": bool(apply)}
    if apply:
        store.write_json(DURUM_DEFTERI, out)
    return out
