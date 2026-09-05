"""skill_gorus.py — skill'lerin yapılandırılmış GÖRÜŞ yazıp gerçekleşen sonuçla puanlandığı, icraya dokunmayan görüş defteri.

NE YAPAR — KISIR DÖNGÜNÜN GÖLGE TARAFTAN KIRILMASI. Aktif skill kümesinin aday seçimine ölçülebilir
bir katkısı olup olmadığı bilinmiyordu, çünkü skill'ler üretimde koşmuyor ve Eksen-2 (doğru
olarak) kanıtsız öneri üretmeyi reddediyor — "ölçmek için koşmalı, koşturmak için ölçmeli"
döngüsü. Bu katman döngüyü İCRAYA DOKUNMADAN kırar: deterministik motorun fiilen koşturduğu
skill'ler için yüzey başına görüş satırları türetilir, yüzey başına bir ÇÖZÜCÜ o görüşleri
GERÇEKLEŞEN sonuçla puanlar (sıralayıcıda rank-IC, çıkışta kıyas), hüküm tarih-kümeli bootstrap +
BH-FDR süzgeciyle yüzey-başına kanıt olarak operatöre gider. Şemada beş yüzey vardır (YUZEYLER),
ikisi ölçülür (OLCULEN_YUZEYLER); çözücüsü olmayan yüzeye görüş YAZILMAZ (okuyucusuz yazım yok).

KİLİT GİRİŞLER. `kuyruk_kadansi` (öğrenme kadansının BUGÜNKÜ kancası: yalnız snapshot append'i),
`kuyruktan_uret` (seans-dışı toplu üretici; ops betiğinin gövdesi), `topla` (doğrudan defterden
üretim — kuru koşu/ölçüm aracı), `kadans` (tam ölçüm koşusu; ARTIK SCHEDULER'DAN ÇAĞRILMAZ),
`rapor` (FDR-sağkalan hüküm yüzeyi), `evren` (aktif + korumasız + deterministik küme, dışlama
muhasebesiyle), `gorus_satiri` (şema doğrulamalı satır — kusurlu satır atılmaz, ValueError atar),
`cozucu_siralayici`/`cozucu_cikis`, `bootstrap_p`/`bh_fdr`, `defter`, `kuyruk_oku`.

ÜRETİM KADANSTAN ÇIKTI (EDG-2026-019 kill#1 KÖK ÇÖZÜMÜ, 2026-09-01). Kill#1 "gözlem icrayı
yavaşlatamaz" der ve canlıda p95_pay 6,57 ölçüldü: üretim, öğrenme kadansının İÇİNDE senkron
koşuyordu. Bugünkü mimari ikiye ayırır:
  * KADANS İÇİ — `kuyruk_kadansi`: t-anı GİRDİ KESİTİ (`_snapshot`) tek satır olarak
    `skill_gorus_kuyruk.jsonl`e eklenir. Ağır hesap (defter okuma, tekilleştirme, bootstrap,
    `rapor`) bu yolda YOKTUR; yolun kendi süresi aynı p95 düzeneğiyle ölçülmeye devam eder.
  * SEANS DIŞI — `kuyruktan_uret` (ops/skill_gorus_uret.py): işlenmemiş snapshot'ları okur,
    görüşleri türetir, deftere yazar, snapshot'ı İŞLENDİ diye işaretler. İdempotent (hem işaret
    hem anahtar tekilleştirmesi).
t-ÇİTİ: kuyruktan üretilen satırın `ts`'i SNAPSHOT anıdır, üretim anı değil; üretici kesitte
olmayan hiçbir alana bakamaz (`SNAPSHOT_ALANLARI` beyaz listesi — sonradan eklenen alan sayılır
ve düşürülür, canlı deftere geri dönülmez).

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
exit_efficiency.json (girdi bekçisi), kendi snapshot kuyruğu.
YAZAR: kendi ÜÇ defteri `state/skill_gorusleri.jsonl` + `state/skill_gorus_durum.json` +
`state/skill_gorus_kuyruk.jsonl`. Kuyruğun DIŞ okuyucuları: `api._gorus_kuyrugu` (pano derinliği)
ve `ops/skill_gorus_uret.py` (üretici) — YASA 6 karşılığı beyanla değil OKUYUCUYLA kapanır.

GÖLGE SIRALAMA KOLU + PENCERE SAYACI (EDG-2026-078 Aşama A, TSK-126, 2026-09-05) — AYRI KART,
CANLI KARAR YİNE DEĞİŞMEZ. `golge_siralama_kancasi` `loop.py`nin P3 aday kesitine bir YAN defter
(`state/golge_siralama.jsonl`) ekler: MEVCUT (`score`) sıralamasının YANINDA, skill'in ölçülmüş
bilgi değeriyle ağırlıklandırılmış İKİNCİ bir sıralama — gerçek emir hâlâ yalnız MEVCUT'tan çıkar.
`golge_kol_raporu` bu defteri saf okur ve `rapor()["golge_kol"]`e düşer (Z6: okuyucu ilk günden).
`pencere_yaz`/`_pencere_ozeti` EDG-2026-019 kill#3'ün "3 ARDIŞIK pencere" borcunu kapatır: yazan
`ops/skill_gorus_uret.py` (her `--uygula` koşumunda BİR kez, `state/skill_gorus_pencereler.jsonl`e),
okuyan `rapor()` (`terfi_adaylari`/`emeklilik_isaretleri`nin `ardisik_pencere` alanı)."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
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
KUYRUK_DEFTERI = "skill_gorus_kuyruk.jsonl"  # t-anı girdi kesitleri (kadans yazar, ops üretici okur)

# İKİ KADANS YOLU, İKİ AD. p95 örneklemi YOL BAŞINA ayrılır: kuyruk yolunun maliyeti tam koşunun
# maliyeti DEĞİLDİR ve ikisini tek halkada karıştırmak, kill#1'in ölçtüğü sayıyı iki farklı işin
# ortalamasına çevirirdi. `yol` alanı OLMAYAN eski örnekler KADANS sayılır — onlar kuyruk yolundan
# ÖNCE yazıldı; "bilinmiyor" diye atmak canlıdaki kill kaydını sessizce silmek olurdu.
KADANS_YOLU = "kadans"      # topla + rapor (tam koşu) — ARTIK scheduler'dan çağrılmaz
KUYRUK_YOLU = "kuyruk"      # yalnız snapshot append'i — bugünkü kadans adımı

# DURUM DEFTERİNİN İKİ KADANS YOLU DIŞINDA KALAN, EZİLMEMESİ GEREKEN ANAHTARI: seans-dışı gölge
# üreticinin son koşum özeti. Kadans yazımı belgeyi BÜTÜN olarak değiştirir; bu anahtar
# korunmasaydı her gece silinir ve "kota doldu mu / kaç ölçülemedi" sorusu kalıcı okuyucusuz
# kalırdı (YASA 6 alan düzeyinde).
LLM_URETIM_ANAHTARI = "son_llm_uretim"
_DURUM_KORUNAN = (LLM_URETIM_ANAHTARI,)

# KUYRUK BİRİKİM EŞİĞİ — İŞLENMEMİŞ SNAPSHOT SAYISI. Üretim kadanstan çıktı, yani "kadans koştu"
# ile "görüş üretildi" ARTIK AYNI OLAY DEĞİL: üretici hiç koşmazsa kuyruk sessizce birikir ve
# defter donuk kalır. Sessiz birikim tam olarak bu deponun en sık ölçtüğü arıza sınıfıdır
# (dormant_setup dersi), o yüzden birikmenin KENDİSİ alarmdır. Sayı 14: iki haftalık gecelik
# kadans — bir haftalık gecikme normal operatör ritmi içinde kalsın, iki hafta kalmasın.
KUYRUK_BIRIKIM_TAVANI = 14

# SNAPSHOT ŞEMASI — t-ÇİTİNİN KENDİSİ. Üretici bu beyaz listenin DIŞINDAKİ hiçbir alanı okumaz:
# kesit alındıktan SONRA bir gözleme alan eklenirse (elle, başka bir süreçten, ya da şema
# genişlemesiyle) o alan üretime SIZAMAZ — sayılır ve düşürülür. Liste `_gozlemler()`in ürettiği
# alanların TAM kopyasıdır ve ikisi ayrışırsa çivi öter (v356).
SNAPSHOT_ALANLARI = ("skill", "tarih", "hedef", "skor", "karar", "r", "mfe_r", "kaynak")
KUYRUK_SEMA = 1             # snapshot şema sürümü; tanınmayan sürüm ONARILMAZ, adıyla atlanır

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


# EDG-2026-019 KILL#1 KAPATMA OLAYI — TEK ATIŞ (süreç-içi mandal; bekçi mandallarıyla aynı
# gerekçe): kadans günde bir koşar ama api/CLI yolları da buradan geçebilir; olayı her çağrıda
# basmak aynı kapanışı yüzlerce kez tekrarlamak olurdu. Restart mandalı sıfırlar — kabul edilen
# bedel: süreç başına en fazla bir olay (kapanış olgusu değişmez, yalnız kaydı tekrarlanabilir).
_KAPATMA_OLAYI_BASILDI = False


def _kapatma_olayi() -> None:
    global _KAPATMA_OLAYI_BASILDI
    if _KAPATMA_OLAYI_BASILDI:
        return
    _KAPATMA_OLAYI_BASILDI = True
    try:
        from . import obs
        obs.log("skill_gorus_katmani_kapatildi", kart=KART,
                detail=("EDG-2026-019 kill#1 uygulandı: canlı p95_pay 6,57 > tavan 0,10 "
                        "(skill_gorus_durum.json, 2026-08-21'den beri) — görüş ÜRETİMİ durdu; "
                        "defterler dokunulmadı, okuma yüzeyleri açık. Açılış yalnız kartın "
                        "resmileşmiş yeni ölçümüyle (config.SKILL_GORUS_URETIM_ACIK)"))
    except Exception:  # sessiz-yutma: kapanışın KAYDI düşerse kapanışın KENDİSİ yine geçerlidir — olay basımının arızası, katmanı geri açmanın gerekçesi olamaz; obs kendi fail-open sözleşmesini taşır, burada ikinci alarm zinciri kurmak arızayı çoğaltırdı
        pass


def _now() -> str:
    """Şu anki UTC zamanını saniye çözünürlüklü ISO-8601 metni olarak verir."""
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
_ALANLAR = ("skill", "ts", "yuzey", "hedef", "skor", "karar", "gerekce_ozeti", "tarih", "uretici")

# ÜRETİCİ SINIFI — TEK ALAN, İKİ KART. EDG-2026-019 deterministik üreticiyi ölçer, EDG-2026-063
# beyan-only skill'lerin LLM gölge üreticisini. İkinci bir DEFTER açmak ikinci bir hata sınıfı
# olurdu (063 kill-list #1: "defter ya da çözücü 019'dan AYRI ikinci bir kopya olarak kurulursa
# geçersiz"), o yüzden defter TEK ve satır KÜNYE taşır. Varsayılan `det`tir: alanı olmayan eski
# satırlar okunurken deterministik sayılır ve geriye dönük YENİDEN YAZILMAZ.
URETICI_DET, URETICI_LLM = "det", "llm"
URETICILER = (URETICI_DET, URETICI_LLM)


def gorus_satiri(skill: str, yuzey: str, hedef: str, *, tarih: str,
                 skor: float | None = None, karar: str | None = None,
                 gerekce_ozeti: str = "", ts: str | None = None,
                 uretici: str = URETICI_DET) -> dict:
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
    if uretici not in URETICILER:
        raise ValueError(f"bilinmeyen üretici {uretici!r} — sınıflar: {URETICILER}")
    return {"skill": str(skill), "ts": ts or _now(), "yuzey": yuzey, "hedef": str(hedef),
            "skor": (None if skor is None else float(skor)),
            "karar": (str(karar) if karar else None),
            "gerekce_ozeti": str(gerekce_ozeti)[:200], "tarih": str(tarih),
            "uretici": uretici}


def defter() -> list[dict]:
    """Görüş defterinin tamamı (saf okuma)."""
    return store.read_jsonl(GORUS_DEFTERI)


def _anahtar(g: dict) -> tuple:
    """Bir görüş kaydının kimlik anahtarı: (skill, yüzey, hedef) üçlüsü — tekilleştirme/eşleştirme için.

    `uretici` ANAHTARA GİRMEZ, iki nedenle: (1) iki üretici sınıfının EVRENİ ayrıktır (019
    `ENGINE_IMPLEMENTED` içi, 063 dışı), yani skill adı zaten sınıfı ayırır; (2) alanı olmayan
    ESKİ satırlar `None`, yenileri `"det"` taşır — anahtara koymak aynı görüşü iki kez yazdırırdı."""
    return (g.get("skill"), g.get("yuzey"), g.get("hedef"))


def deftere_yaz(satirlar: list[dict]) -> int:
    """Görüş defterinin TEK YAZIM KAPISI — kaç satır yazıldığını döner.

    NEDEN TEK KAPI. Defterin ikinci bir yazarı (`skill_gorus_llm`) doğdu ve `store.append_jsonl`i
    orada tekrarlamak, `codelaw.artifact_graph`ta defterin iki yazarlı görünmesi demekti: "bu
    dosyayı kim yazıyor" sorusunun cevabı ikiye bölünürdü. Yazan modül TEKTİR, çağıran çok."""
    for s in satirlar:
        store.append_jsonl(GORUS_DEFTERI, s)
    return len(satirlar)


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
    """Karşı-olgusal defterin ÇÖZÜLMÜŞ ve girilmiş satırları (görüş türetmenin ham maddesi; saf okuma)."""
    from . import counterfactual
    return counterfactual.resolved_rows(entered_only=True)


def _trade_satirlari() -> list[dict]:
    """Gerçek işlem defterinin `r_multiple`ı ölçülmüş satırları (sonucu olmayan işlem görüş üretmez; saf okuma)."""
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


def _gorusleri_tureti(gozlemler: list[dict], izinli: set, var: set, *,
                      ts: str | None = None) -> tuple[list[dict], dict]:
    """Gözlem kesitinden görüş satırları — İKİ ÜRETİM YOLUNUN TEK KAYNAĞI (tek-kaynak yasası).

    `topla` (canlı defterden) ve `kuyruktan_uret` (snapshot'tan) AYNI türetimi kullanır; ikinci
    bir kopya yazılsaydı iki yol aynı gözlemden farklı satır üretmeye başlar ve fark ancak
    defterde görünürdü.

    t-ÇİTİ İKİ PARÇALI:
      1. `ts` verilirse satırın damgası SNAPSHOT anıdır (üretim anı değil) — seans-dışı üretim,
         görüşü üretildiği geceye değil GÖZLENDİĞİ ana bağlar;
      2. her gözlem `SNAPSHOT_ALANLARI` beyaz listesine İNDİRGENİR. Kesit alındıktan sonra
         eklenmiş bir alan (`skor_v2`, düzeltilmiş `r`, …) üretime SIZAMAZ: sayılır (`cit_disi_alan`)
         ve düşürülür. Eksik kanonik alan ONARILMAZ — kendi kovasına adıyla düşer."""
    yeni: list[dict] = []
    atlanan = {"evren_disi": 0, "zaten_var": 0, "skorsuz": 0, "cikis_olcusuz": 0,
               "kimliksiz": 0, "cit_disi_alan": 0}
    for ham in sorted(gozlemler, key=lambda x: (str(x.get("tarih") or ""), str(x.get("hedef") or ""))):
        atlanan["cit_disi_alan"] += sum(1 for k in ham if k not in SNAPSHOT_ALANLARI)
        g = {k: ham.get(k) for k in SNAPSHOT_ALANLARI}
        sk = g.get("skill")
        if sk not in izinli:
            atlanan["evren_disi"] += 1
            continue
        if not g.get("hedef") or not g.get("tarih"):
            atlanan["kimliksiz"] += 1        # kimliksiz görüş çözülemez — uydurulmaz, sayılır
            continue
        # --- aday-siralayici: skill'in plan anındaki SKOR görüşü -----------------------------
        if g.get("skor") is None:
            atlanan["skorsuz"] += 1
        else:
            s = gorus_satiri(sk, "aday-siralayici", g["hedef"], tarih=g["tarih"],
                             skor=g["skor"], ts=ts,
                             gerekce_ozeti=f"aday skoru (plan anı) · kaynak={g.get('kaynak')}")
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
        c = gorus_satiri(sk, "cikis", g["hedef"], tarih=g["tarih"], ts=ts,
                         karar=str(g.get("karar") or "?"),
                         gerekce_ozeti=("motor çıkış kuralı, aday bu skill'den · "
                                        f"kaynak={g.get('kaynak')}"))
        if _anahtar(c) in var:
            atlanan["zaten_var"] += 1
        else:
            yeni.append(c); var.add(_anahtar(c))
    return yeni, atlanan


def topla(apply: bool = True, tavan: int | None = YAZIM_TAVANI) -> dict:
    """Evrendeki skill'lerin görüşlerini CANLI defterlerden türetip defterle — yalnız YENİ olanları.

    `apply=False`: hiçbir şey yazılmaz, ne yazılacağı döner (testler + kuru koşu).

    BU YOL ARTIK KADANSTA DEĞİL (2026-09-01, kill#1 kök çözümü): scheduler `kuyruk_kadansi`
    çağırır. Burası bilinçli/elle koşulan ÖLÇÜM yoludur — t-çiti YOKTUR (satır ÜRETİM anını
    damgalar), çünkü kesit ile üretim arasında zaman geçmez.

    KATMAN KAPISI (EDG-2026-019 kill#1, Rol-1 hükmü 2026-08-23): `config.SKILL_GORUS_URETIM_ACIK`
    kapalıyken YAZIM YOLU ÖLÜDÜR — apply=True bile deftere dokunmaz (gerekçe bayrağın kendi
    yorumunda; gözlem icrayı yavaşlatamaz). apply=False kuru koşusu ölçüm aracı olarak açık kalır."""
    from . import config as _cfg
    if apply and not _cfg.SKILL_GORUS_URETIM_ACIK:
        _kapatma_olayi()
        return {"yazilan": 0, "kirpilan": 0, "tavan": tavan, "atlanan": None, "evren": None,
                "uygulandi_mi": False, "defter_toplam": None, "kapali": True,
                "neden": ("EDG-2026-019 kill#1: katman KAPALI (p95_pay 6,57 > 0,10 canlıda "
                          "ölçüldü) — yazım durdu, defterlere dokunulmadı")}
    ev = evren()
    izinli = set(ev["evren"])
    var = {_anahtar(g) for g in defter()}
    gz = _gozlemler()
    yeni, atl = _gorusleri_tureti(gz["satirlar"], izinli, var)
    # ELEME MUHASEBESİ TEK SÖZLÜKTE: kaynak defterde düşen satır ile burada düşen satır AYRI
    # sebeplerdir ve ikisi de görünür kalmalı — "az görüş yazıldı"nın nedeni ikisinden biridir.
    atlanan = {**atl, **gz["atlanan"]}
    kirpilan = 0
    if tavan is not None and len(yeni) > tavan:
        kirpilan = len(yeni) - tavan
        yeni = yeni[:tavan]              # EN ESKİDEN yeniye (liste tarih sıralı) — seçim yok
    if apply:
        deftere_yaz(yeni)
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
# ÜRETİCİ KIRILIMI — İKİ KARTIN SATIRLARI AYNI DEFTERDE, AMA AYRI SAYILIR
# ==================================================================================================
def satir_uretici(g: dict) -> str:
    """Bir görüş satırının üretici sınıfı. Alanı OLMAYAN eski satırlar `det` sayılır.

    GERİYE DÖNÜK YENİDEN YAZIM YOK: canlıdaki 5.500 satır bu alan doğmadan önce yazıldı ve
    hepsi deterministik üreticidendi; onlara alan EKLEMEK defteri tahrif etmek olurdu. Varsayım
    burada TEK yerde durur ve adıyla beyan edilir."""
    return str(g.get("uretici") or URETICI_DET)


def _satir_uretici_sinifi(gorusler: list[dict], skill: str) -> str | None:
    """Bir skill'in satırlarının üretici sınıfı — KARIŞIKSA None (hüküm verilmez).

    Evrenler ayrık olduğu için bir skill normalde TEK sınıfa aittir. Karışım bir arıza işaretidir
    (019 evreni genişledi ya da bir satır yanlış künyeyle yazıldı) ve o skill hiçbir aileye
    sokulmaz: yanlış aileye koymak, çokluk düzeltmesini sessizce kaydırırdı."""
    siniflar = {satir_uretici(g) for g in gorusler if g.get("skill") == skill}
    return siniflar.pop() if len(siniflar) == 1 else None


def uretici_kirilimi(gorusler: list[dict] | None = None) -> dict:
    """Defterin üretici × yüzey sayımı — 063'ün gölge serisi 019'un yanında ADIYLA durur.

    OKUYUCU: `rapor()` (dolayısıyla `api._eksen2_gorus`) ve ops üreticisinin özeti. Künyenin
    kendisi bir alan olarak yazıldıysa okunabilir de olmalı (YASA 6 alan düzeyinde)."""
    satirlar = defter() if gorusler is None else gorusler
    out: dict[str, dict] = {}
    for g in satirlar:
        u = satir_uretici(g)
        y = str(g.get("yuzey") or "?")
        kova = out.setdefault(u, {"n": 0, "yuzey": {}, "skill": {}})
        kova["n"] += 1
        kova["yuzey"][y] = kova["yuzey"].get(y, 0) + 1
        sk = str(g.get("skill") or "?")
        kova["skill"][sk] = kova["skill"].get(sk, 0) + 1
    for kova in out.values():
        kova["yuzey"] = dict(sorted(kova["yuzey"].items()))
        kova["skill"] = dict(sorted(kova["skill"].items()))
    return dict(sorted(out.items()))


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
    # PENCERE SAYACI (EDG-2026-078, kill#3 borcunun kapanışı): saf okuma — `rapor()` deftere
    # YAZMAZ, yalnız `ops/skill_gorus_uret.py`nin yazdığı `PENCERE_DEFTERI`yi okur.
    pencere = _pencere_ozeti()
    yuzeyler: dict[str, dict] = {}
    terfi, emeklilik = [], []
    for yuzey, cozucu in (("aday-siralayici", cozucu_siralayici), ("cikis", cozucu_cikis)):
        if not bekci[yuzey]["saglikli"]:
            yuzeyler[yuzey] = {"durum": "HÜKÜM YOK", "neden": bekci[yuzey]["neden"],
                               "skiller": {}, "fdr": None}
            continue
        # AİLE ÜRETİCİ BAŞINA AYRILIR (Rol-1 hükmü 2026-09-01). BH-FDR'nin eşiği `q·i/m`dir, yani
        # AİLE BÜYÜKLÜĞÜNE bağlıdır: 063'ün gölge satırları 019'un defterine düştükçe `m` büyür,
        # `kritik_p` kayar ve 019'un ÖLÇÜMDEN ÖNCE DONDURULMUŞ hükmü — hiçbir eşik elle
        # değiştirilmeden — sessizce başkalaşırdı. İki üretici sınıfı iki AYRI ailedir; kıyas
        # zemini (aynı defter, aynı çözücü, aynı eşik) bozulmaz, çünkü ayrılan şey EŞİK DEĞİL
        # ÇOKLUK DÜZELTMESİNİN PAYDASIDIR. `skiller` haritası birleşik kalır (iki sınıfın skill
        # adları evrenleri gereği ayrık) ve her kayıt kendi `uretici` künyesini taşır.
        c = cozucu(gorusler, sonuclar)
        aile_uretici = {sk: _satir_uretici_sinifi(gorusler, sk) for sk in c["skiller"]}
        fdr_aileleri: dict[str, dict] = {}
        for sinif in URETICILER:
            uyeler = {sk: v.get("p") for sk, v in c["skiller"].items()
                      if aile_uretici.get(sk) == sinif}
            if uyeler:
                fdr_aileleri[sinif] = bh_fdr(uyeler)
        for sk, v in c["skiller"].items():
            # KARIŞIM `det`E ÇEVRİLMEZ (Rol-1 hükmü 2026-09-01). `_satir_uretici_sinifi` karışımda
            # BİLEREK None döner; `or URETICI_DET` yazmak o "ölçemedim"i bir hükme çevirir ve
            # okuyucu `uretici="det"` + `fdr=null` görüp nedeni hiçbir yüzeyde bulamazdı. Ölçülemeyen
            # değer None + NEDEN (uydurma yasağı). Fail-closed davranış korunur: sınıf None ise
            # skill hiçbir FDR ailesine girmez → `fdr` None → sagkalan False → ne terfi ne emeklilik.
            sinif = aile_uretici.get(sk)
            v["uretici"] = sinif
            # AYRI ANAHTAR (`neden` DEĞİL): skill sözlüğünde `neden` zaten ÖLÇÜM tarafının gerekçesini
            # taşıyor ("rank-IC tanımsız…"); üzerine yazmak iki farklı ölçülemezliği tek alanda
            # katlardı. Rol-1'in beyan hükmü aynen, çakışmasız anahtarla.
            v["uretici_neden"] = None if sinif else "karisik_uretici"
            v["fdr"] = (fdr_aileleri.get(sinif) or {"aile": {}})["aile"].get(sk)
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
            # PENCERE SAYACI (EDG-2026-078): (skill, yüzey) için ölçülmüş ARDIŞIK pencere sayısı +
            # toplam pencere sayısı. Sayaç YOKSA (henüz hiç `pencere_yaz()` koşmadıysa) ikisi de 0 —
            # 0 "ölçüldü, hiç yok" değil "henüz sayaç yok" demektir; `pencere_n=0` bunu açıkça taşır.
            pb = pencere.get((sk, yuzey)) or {"ardisik_pencere": 0, "pencere_n": 0}
            if v["terfi_adayi"]:
                terfi.append({"skill": sk, "yuzey": yuzey, "n": v["n"], "etki": etki,
                              "p": v.get("p"), "uretici": sinif,
                              "ardisik_pencere": pb["ardisik_pencere"], "pencere_n": pb["pencere_n"]})
            elif v["emeklilik_isareti"]:
                emeklilik.append({"skill": sk, "yuzey": yuzey, "n": v["n"], "etki": etki,
                                  "p": v.get("p"), "uretici": sinif,
                                  "ardisik_pencere": pb["ardisik_pencere"], "pencere_n": pb["pencere_n"],
                                  "beyan": (f"FDR-sağkalan NEGATİF — kart 3 ARDIŞIK pencere ister; "
                                            f"ölçülen ardışık pencere {pb['ardisik_pencere']}/3 "
                                            f"(toplam {pb['pencere_n']} pencere) — bu satır bir "
                                            f"İŞARETTİR, emeklilik ÖNERİSİ değildir")})
        yuzeyler[yuzey] = {"durum": "ölçüldü", "neden": None, "skiller": c["skiller"],
                           # KÜNYE ÜRETİCİ BAŞINA: tek bir `m`/`kritik_p` basmak, iki ailenin
                           # hükmünü tek sayıya katlayıp hangisinin geçerli olduğunu ölçülemez
                           # yapardı (tek-kaynak yasasının aynı dersi).
                           "fdr": {sinif: {k: f[k] for k in ("m", "q", "kritik_p")}
                                   for sinif, f in fdr_aileleri.items()},
                           "metrik": c.get("metrik"), "eslesmeyen_gorus": c.get("eslesmeyen_gorus")}
    kovalar: dict[str, int] = {}
    for y in yuzeyler.values():
        for v in y.get("skiller", {}).values():
            kovalar[v.get("kova", "?")] = kovalar.get(v.get("kova", "?"), 0) + 1
    return {
        "kart": KART, "ts": _now(),
        "defter_n": len(gorusler), "evren": evren(),
        "yuzeyler": yuzeyler, "kova_sayimi": kovalar,
        # ÜRETİCİ KIRILIMI RAPORDA: künye yazıldıysa okunur da olmalı. "Defterde 5.500 satır var"
        # ile "5.500'ün 80'i gölge LLM satırı" aynı ekranda aynı şeye benzeyemez.
        "uretici_kirilimi": uretici_kirilimi(gorusler),
        # SEANS-DIŞI GÖLGE ÜRETİCİNİN SON KOŞUMU (EDG-2026-063): kota, ölçülemedi ve şema
        # sayaçları. Ayrı bir rapor yüzeyi açmak, aynı defterin iki hükmü demekti.
        "llm_uretim": (store.read_json(DURUM_DEFTERI, None) or {}).get(LLM_URETIM_ANAHTARI),
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
        # GÖLGE SIRALAMA KOLU (EDG-2026-078 Aşama A) — AYRI KART, AYRI HÜKÜM: aynı raporun
        # yanında durur ki "skill görüşü canlı sıralamayı etkileseydi ne olurdu?" sorusunun
        # ölçümü, "bugün ne söylüyor" sorusunun yanında okunabilsin (Z6: okuyucu ilk günden).
        # Düşerse TÜM raporu düşürmez — kendi try/except'i içinde, "ÖLÇÜLEMEDİ" ile devam eder.
        "golge_kol": _golge_kol_guvenli(),
        "beyan": ("HİÇBİR TERFİ/EMEKLİLİK OTOMATİK DEĞİL: bu rapor kayıt defterine, bayrağa, "
                  "eşiğe ya da plana DOKUNMAZ. FDR-sağkalanlar Eksen-2 teşhisine ve operatöre "
                  "KANITLA gider (2026-08-06 kararının devamı)."),
    }


# ==================================================================================================
# KADANS + p95 ÖLÇÜM DÜZENEĞİ (kill#1)
# ==================================================================================================
def _yuzdelik(vals: list[float], q: float):
    """Sıralı listenin q yüzdeliği (en yakın-sıra yöntemi, 2 ondalık). Liste boşsa None — değer uydurulmaz."""
    if not vals:
        return None
    s = sorted(vals)
    return round(s[min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))], 2)


def _durum_yaz(out: dict) -> None:
    """Durum defterini yaz — ama KADANS DIŞI anahtarları EZMEDEN.

    İki kadans yolu belgeyi bütün olarak yeniler; gölge üreticinin özeti (`son_llm_uretim`) o
    yolların ürettiği bir şey DEĞİLDİR ve her gece silinseydi kota/ölçülemedi sayaçları kalıcı
    okuyucusuz kalırdı.

    GÜVENCENİN KAPSAMI (daraltıldı, Rol-1 hükmü 2026-09-01): `store.update_json` kilitli
    oku-değiştir-yaz olduğu için kayıp-güncelleme YALNIZ `_DURUM_KORUNAN` anahtarları için yapısal
    olarak imkânsızdır — birleştirme kilidin İÇİNDE, belgenin o anki hâli üzerinde koşar. `out`un
    kendi alanları (özellikle `ornekler` halkası) bu güvencenin DIŞINDADIR: `_sure_kaydi` halkayı
    kilitten ÖNCE okur, dolayısıyla iki kadans yolu aynı anda koşarsa biri ötekinin örneğini
    düşürebilir. Bugün ölçülmüş bir arıza değil (tek gece döngüsü, tek süreç) ama güvence diye
    yazılırsa yarın sessizce yanlış olur."""
    def _birlestir(doc):
        korunan = {k: (doc or {}).get(k) for k in _DURUM_KORUNAN if (doc or {}).get(k) is not None}
        doc.clear()
        doc.update({**out, **korunan})
        return True
    store.update_json(DURUM_DEFTERI, _birlestir, {})


def llm_uretim_kaydi(ozet: dict) -> None:
    """Gölge üreticinin son koşum özetini durum defterine yazar — DEFTERİN TEK YAZARI BURASI.

    `skill_gorus_llm` bu kapıdan geçer; orada `store.write_*` çağırmak, aynı artefaktın iki
    yazarlı görünmesi ve "bu dosyayı kim yazıyor" sorusunun ikiye bölünmesi demekti."""
    store.update_json(DURUM_DEFTERI, lambda doc: doc.update({LLM_URETIM_ANAHTARI: ozet}) or True,
                      {})


def _sure_kaydi(*, yol: str, sure_ms: float, oncesi_ms: float | None, ek: dict) -> dict:
    """Süre örneklemi halkası + kill#1 p95 hükmü — İKİ KADANS YOLUNUN ORTAK DÜZENEĞİ.

    TEK KAYNAK: eşik okuması, örneklem tabanı ve "ÖLÇÜLEMEDİ ≠ 0" ayrımı tek gövdede durur; iki
    yol için iki kopya yazılsaydı biri düzeltildiğinde öteki sessizce eski kuralla hüküm verirdi.

    p95 YOL BAŞINA hesaplanır (halka ORTAK, hüküm AYRI): kuyruk yolunun payı ile tam koşunun payı
    farklı işlerin ölçüsüdür. `yol` alanı taşımayan eski örnekler KADANS sayılır — canlıdaki
    kill kaydı öyle yazıldı ve "bilinmiyor" diye atmak kanıtı silmek olurdu."""
    pay = (round(sure_ms / oncesi_ms, 4) if (oncesi_ms and oncesi_ms > 0) else None)
    d = store.read_json(DURUM_DEFTERI, None) or {}
    ornek = [x for x in (d.get("ornekler") or []) if isinstance(x, dict)]
    ornek.append({"ts": _now(), "yol": yol, "sure_ms": sure_ms, "oncesi_ms": oncesi_ms,
                  "pay": pay, **ek})
    ornek = ornek[-SURE_ORNEK_TAVANI:]
    ayni = [x for x in ornek if (x.get("yol") or KADANS_YOLU) == yol]
    sureler = [float(x["sure_ms"]) for x in ayni if x.get("sure_ms") is not None]
    paylar = [float(x["pay"]) for x in ayni if x.get("pay") is not None]
    p95_pay = _yuzdelik(paylar, 0.95)
    if p95_pay is None:
        kill = {"durum": "ÖLÇÜLEMEDİ", "p95_pay": None, "tavan": KART_P95_TAVAN,
                "n_ornek": len(paylar), "yol": yol,
                "neden": "kadans süresi (`oncesi_ms`) ölçülmedi — pay kurulamadı, 0 SAYILMAZ"}
    elif len(paylar) < P95_MIN_ORNEK:
        kill = {"durum": "ÖLÇÜLÜYOR", "p95_pay": p95_pay, "tavan": KART_P95_TAVAN,
                "n_ornek": len(paylar), "yol": yol,
                "neden": (f"örneklem {len(paylar)}/{P95_MIN_ORNEK} — tek/az koşudan p95 hükmü "
                          f"VERİLMEZ (ilk koşu defteri sıfırdan doldurur, doğal olarak en "
                          f"yavaşıdır). Ölçülen pay {p95_pay} kayda geçer, KILL geçmez.")}
    else:
        kill = {"durum": ("KILL" if p95_pay > KART_P95_TAVAN else "temiz"),
                "p95_pay": p95_pay, "tavan": KART_P95_TAVAN, "n_ornek": len(paylar), "yol": yol,
                "neden": (f"p95 pay {p95_pay} {'>' if p95_pay > KART_P95_TAVAN else '<='} "
                          f"{KART_P95_TAVAN} — kill#1")}
    return {"pay": pay, "sure_p50_ms": _yuzdelik(sureler, 0.5),
            "sure_p95_ms": _yuzdelik(sureler, 0.95), "kill_p95": kill, "ornekler": ornek}


def kadans(apply: bool = True, oncesi_ms: float | None = None,
           tavan: int | None = YAZIM_TAVANI) -> dict:
    """TAM ÖLÇÜM KOŞUSU: görüş topla → rapor et → SÜRESİNİ ÖLÇ. Deterministik, kotasız, LLM'siz.

    ARTIK ÖĞRENME KADANSINDAN ÇAĞRILMAZ (2026-09-01, kill#1 kök çözümü). Gece döngüsünün adımı
    `kuyruk_kadansi`dir; burası bilinçli bir ölçüm/kuru-koşu yoludur ve kartın yeniden açılışı
    için gereken "tam koşu ne kadar sürüyor" sayısını üretmeye devam eder (bedel yasası: kuyruk
    yolunun ucuzluğu ancak tam koşuyla KIYASLANARAK bir sayı olur).

    p95 ÖLÇÜM DÜZENEĞİ (kill#1: "+%10'dan fazla artırırsa katman KAPATILIR"). Ölçülen iki sayı:
      * `sure_ms` — bu adımın kendi süresi (her koşuda halkaya yazılır, tavanı `SURE_ORNEK_TAVANI`),
      * `pay` = sure_ms / oncesi_ms — adımın, KENDİSİNDEN ÖNCE koşan kadansın üstüne eklediği oran.
    Kill hükmü `p95(pay) > KART_P95_TAVAN` ile verilir. `oncesi_ms` ölçülemediyse `pay` None'dır
    ve kill "ÖLÇÜLEMEDİ" der — 0 demez (uydurma yasağı: ölçülmemiş bir gecikme, yok sayılmaz).

    KATMAN KAPISI (EDG-2026-019 kill#1 TETİKLENDİ — Rol-1 hükmü 2026-08-23): bayrak kapalıyken
    bu adım HİÇ KOŞMAZ — ne görüş toplanır ne DURUM_DEFTERI yazılır (son KILL kaydı kanıt olarak
    yerinde kalır). Kadans defterine `kapali` beyanı döner ki gece döngüsü kapanışı sessizce
    değil ADIYLA taşısın. MANDAL `apply` BİÇİMİNDE (K4, 2026-09-01) — `topla` ve `kuyruk_kadansi`
    ile aynı hizada: kapatılan şey YAZIMDIR, ÖLÇÜM DEĞİL. Kuru koşu bayraktan bağımsız yürür,
    çünkü kartın yeniden açılışı "tam koşu ne kadar sürüyor" sayısını ister ve o sayıyı kapının
    kendisi imkânsız kılarsa katman bir daha ÖLÇÜLEREK açılamaz."""
    from . import config as _cfg
    if apply and not _cfg.SKILL_GORUS_URETIM_ACIK:
        _kapatma_olayi()
        return {"ts": _now(), "kart": KART, "yol": KADANS_YOLU, "kapali": True,
                "uygulandi_mi": False,
                "sure_ms": None, "oncesi_ms": oncesi_ms, "pay": None,
                "neden": ("EDG-2026-019 kill#1: p95_pay 6,57 > tavan 0,10 canlıda ölçüldü "
                          "(skill_gorus_durum.json, 2026-08-21'den beri) — katman KAPALI; "
                          "açılış yalnız kartın resmileşmiş yeni ölçümüyle")}
    t0 = time.perf_counter()
    t = topla(apply=apply, tavan=tavan)
    r = rapor()
    sure_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    k = _sure_kaydi(yol=KADANS_YOLU, sure_ms=sure_ms, oncesi_ms=oncesi_ms,
                    ek={"yazilan": t["yazilan"]})
    out = {"ts": _now(), "kart": KART, "yol": KADANS_YOLU,
           "sure_ms": sure_ms, "oncesi_ms": oncesi_ms, "pay": k["pay"],
           "sure_p50_ms": k["sure_p50_ms"], "sure_p95_ms": k["sure_p95_ms"],
           "kill_p95": k["kill_p95"], "toplama": t, "rapor": r, "ornekler": k["ornekler"],
           "uygulandi_mi": bool(apply)}
    if apply:
        _durum_yaz(out)
    return out


# ==================================================================================================
# KADANS İÇİ YOL — YALNIZ SNAPSHOT APPEND'İ (kill#1 kök çözümü)
# ==================================================================================================
def _snapshot(ts: str | None = None) -> dict:
    """t-ANI GİRDİ KESİTİ — üretimin İHTİYACI kadarı, bir satır.

    NE VAR: o andaki evren (küme ölçüm anında kaynaktan türetilir — C10) ve evren-içi gözlemler,
    `SNAPSHOT_ALANLARI` şemasıyla. NE YOK: görüş defteri okuması, tekilleştirme, çözücü, bootstrap,
    `rapor()` — yani kill#1'in ölçtüğü maliyetin tamamı. Kalan iş SERİLEŞTİR + APPEND'tir.

    ELEME MUHASEBESİ KESİTİN İÇİNDE TAŞINIR (`atlanan`): evren dışı kalan gözlem sayısı ÜRETİM
    anında değil GÖZLEM anında bilinir; sonradan sayılsaydı o günün evreni değil bugünkü evren
    sayılırdı."""
    ev = evren()
    izinli = set(ev["evren"])
    gz = _gozlemler()
    kesit, disarida = [], 0
    for g in gz["satirlar"]:
        if g.get("skill") not in izinli:
            disarida += 1
            continue
        kesit.append({k: g.get(k) for k in SNAPSHOT_ALANLARI})
    return {"ts": ts or _now(), "sema": KUYRUK_SEMA, "islendi": False,
            "evren": sorted(izinli), "n_gozlem": len(kesit), "gozlemler": kesit,
            "atlanan": {**gz["atlanan"], "evren_disi": disarida}}


def kuyruk_oku() -> list[dict]:
    """Snapshot kuyruğunun tamamı (saf okuma). Okuyucular: `kuyruktan_uret`, `api._gorus_kuyrugu`."""
    return store.read_jsonl(KUYRUK_DEFTERI)


def kuyruk_kadansi(apply: bool = True, oncesi_ms: float | None = None) -> dict:
    """ÖĞRENME KADANSININ GÖRÜŞ ADIMI — t-anı kesitini kuyruğa yazar, GÖRÜŞ ÜRETMEZ.

    KİLL#1'İN KÖK ÇÖZÜMÜ BURADA: eski adım `topla()` + `rapor()` koşturuyordu ve canlıda kadans
    süresini ×6,6 katlamıştı. Üretim seans dışına (`kuyruktan_uret`) taşındı; kadansta kalan iş
    kesiti serileştirip eklemektir. Ölçüm düzeneği AYNEN kalır (`_sure_kaydi`) — çünkü "ucuzladı"
    bir iddiadır ve iddia ölçülmeden yaşayamaz; p95 payı bu yol için ayrıca birikir.

    KATMAN KAPISI AYNI BAYRAK: `config.SKILL_GORUS_URETIM_ACIK` kapalıyken bu yol da ÖLÜDÜR —
    kuyruğa da durum defterine de dokunulmaz. Kapatma hükmü "yazım durur" der ve kuyruk yazımı
    da yazımdır; bayrağı yalnız üretim tarafına uygulamak, kapalı katmanın her gece dosya
    büyütmesi olurdu."""
    from . import config as _cfg
    # MANDAL `apply` BİÇİMİNDE (K4, 2026-09-01): kapatılan şey YAZIMDIR, ÖLÇÜM DEĞİL — `topla`nın
    # kapısıyla aynı hizada. Kuru koşu kapalı katmanda da "ne yazılacaktı" sorusunu cevaplar ve
    # kartın yeniden açılışı için gereken ölçüm, kapının kendisi tarafından imkânsız kılınmaz
    # (v278 9e'nin aynı hükmü).
    if apply and not _cfg.SKILL_GORUS_URETIM_ACIK:
        _kapatma_olayi()
        return {"ts": _now(), "kart": KART, "yol": KUYRUK_YOLU, "kapali": True,
                "uygulandi_mi": False, "sure_ms": None, "oncesi_ms": oncesi_ms, "pay": None,
                "gozetim_ms": None, "kuyruk": None,
                "neden": ("EDG-2026-019 kill#1: p95_pay 6,57 > tavan 0,10 canlıda ölçüldü "
                          "(skill_gorus_durum.json, 2026-08-21'den beri) — katman KAPALI; "
                          "açılış yalnız kartın resmileşmiş yeni ölçümüyle")}
    t0 = time.perf_counter()
    snap = _snapshot()
    if apply:
        store.append_jsonl(KUYRUK_DEFTERI, snap)
    sure_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    k = _sure_kaydi(yol=KUYRUK_YOLU, sure_ms=sure_ms, oncesi_ms=oncesi_ms,
                    ek={"n_gozlem": snap["n_gozlem"]})
    # BİRİKİM ÖLÇÜMÜ SÜRE ÖLÇÜMÜNÜN DIŞINDA (BİLEREK): kill#1 "gözlem icrayı yavaşlatamaz" der ve
    # bu okuma bir GÖZETİM işidir, append'in kendisi değil. `sure_ms` yukarıda kapandı, yani
    # kadansın ölçülen maliyeti bu satırlarla DEĞİŞMEZ.
    #
    # AMA ÖLÇÜM PENCERESİNİN DIŞINDA OLMAK "BEDAVA" DEMEK DEĞİLDİR (bedel yasası, Rol-1 hükmü
    # 2026-09-01): kuyruk her gece bir satır uzuyor ve bu okuma dosyanın TAMAMINI ayrıştırıyor.
    # `gozetim_ms` AYRI bir alan olarak ölçülür — `sure_ms`/`pay`/p95 tanımı DEĞİŞMEZ (kill hükmü
    # aynı büyüklüğün ölçüsü kalır), ama gözetimin kendi maliyeti sayısız da kalmaz.
    g0 = time.perf_counter()
    bekleyen = sum(1 for s in kuyruk_oku() if isinstance(s, dict) and not s.get("islendi"))
    gozetim_ms = round((time.perf_counter() - g0) * 1000.0, 2)
    if apply and bekleyen > KUYRUK_BIRIKIM_TAVANI:
        from . import obs
        obs.alarm(obs.ALARM_MECHANISM_STALE,
                  f"skill-görüş kuyruğunda {bekleyen} işlenmemiş kesit (tavan "
                  f"{KUYRUK_BIRIKIM_TAVANI}) — seans-dışı üretici koşmuyor",
                  mechanism="skill_gorus_kuyruk", kart=KART, bekleyen=bekleyen,
                  tavan=KUYRUK_BIRIKIM_TAVANI,
                  detail=("üretim kadanstan çıkarıldı (kill#1 kök çözümü); kesit her gece "
                          "birikiyor ama `ops/skill_gorus_uret.py` işlemiyor. Defter DONUK: "
                          "kadans koşuyor olması görüş üretildiği anlamına GELMEZ"))
    out = {"ts": _now(), "kart": KART, "yol": KUYRUK_YOLU,
           "sure_ms": sure_ms, "oncesi_ms": oncesi_ms, "pay": k["pay"],
           "sure_p50_ms": k["sure_p50_ms"], "sure_p95_ms": k["sure_p95_ms"],
           "kill_p95": k["kill_p95"], "ornekler": k["ornekler"], "uygulandi_mi": bool(apply),
           # GÖZETİM MALİYETİ ADIYLA DURUR — `sure_ms`e KATILMAZ, onun yanında raporlanır.
           "gozetim_ms": gozetim_ms,
           "kuyruk": {"snapshot_ts": snap["ts"], "n_gozlem": snap["n_gozlem"],
                      "evren_n": len(snap["evren"]), "atlanan": snap["atlanan"],
                      "bekleyen": bekleyen, "birikim_tavani": KUYRUK_BIRIKIM_TAVANI}}
    if apply:
        _durum_yaz(out)
    return out


# ==================================================================================================
# SEANS DIŞI TOPLU ÜRETİM — KUYRUKTAN, t-ÇİTİYLE, İDEMPOTENT
# ==================================================================================================
def _ozet_damgasi(gozlemler: list[dict]) -> str:
    """İşlenen kesitin içerik damgası (sha256/16) — yükü düşürülen snapshot'ın kimliği.

    NEDEN YÜK DÜŞÜYOR: kuyruk bir TAŞIMA hattıdır, kanıt defteri değil. Kanıt (a) üretilen görüş
    satırlarıdır — her biri snapshot anını `ts` olarak taşır — ve (b) bu damga + sayımlardır.
    Yükü sonsuza dek saklamak her gece yüz kilobaytlarca tekrar biriktirirdi; damga, işlenmiş bir
    kesitin AYNI kesit olup olmadığını hâlâ ölçülebilir kılar."""
    ham = json.dumps(gozlemler, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(ham.encode("utf-8")).hexdigest()[:16]


def kuyruktan_uret(apply: bool = True, tavan: int | None = None) -> dict:
    """İŞLENMEMİŞ SNAPSHOT'LARDAN GÖRÜŞ ÜRET — seans dışı, toplu, idempotent.

    İDEMPOTENS İKİ KATLI: (1) işlenen snapshot `islendi=True` damgası alır; (2) satırlar zaten
    (skill, yüzey, hedef) anahtarıyla tekilleştirilir. Birinci kat düşse bile (yazımdan sonra
    işaretleme düşerse) ikinci kat mükerrer satır YAZILMASINI engeller — bu yüzden sıra şudur:
    ÖNCE defter, SONRA işaret.

    TAVAN VE İŞARET BİRLİKTE ÇALIŞIR: tavana çarpan snapshot İŞARETLENMEZ (yarısı yazılmış bir
    kesit "işlendi" sayılsaydı kalan gözlemler sessizce kaybolurdu). Varsayılan tavan YOKTUR;
    seans dışı koşumun bütçesi kadans bütçesi değildir."""
    from . import config as _cfg
    if apply and not _cfg.SKILL_GORUS_URETIM_ACIK:
        _kapatma_olayi()
        return {"yazilan": 0, "islenen_snapshot": 0, "bekleyen": None, "atlanan": None,
                "uygulandi_mi": False, "kapali": True,
                "neden": ("EDG-2026-019 kill#1: katman KAPALI (p95_pay 6,57 > 0,10 canlıda "
                          "ölçüldü) — üretim durdu, defterlere dokunulmadı")}
    kuyruk = kuyruk_oku()
    var = {_anahtar(g) for g in defter()}
    toplam = {"evren_disi": 0, "zaten_var": 0, "skorsuz": 0, "cikis_olcusuz": 0,
              "kimliksiz": 0, "cit_disi_alan": 0, "sema_uyumsuz_snapshot": 0,
              "yuksuz_snapshot": 0}
    yazilacak: list[dict] = []
    islenen: dict[int, dict] = {}
    kirpildi = False
    for i, snap in enumerate(kuyruk):
        if not isinstance(snap, dict) or snap.get("islendi"):
            continue
        if snap.get("sema") != KUYRUK_SEMA:
            # ŞEMA UYUMSUZ SNAPSHOT ONARILMAZ ve İŞARETLENMEZ: tanımadığımız bir kesitten görüş
            # türetmek, bilinmeyen bir sözleşmeyi varsaymaktır. Adıyla sayılır, kuyrukta kalır.
            toplam["sema_uyumsuz_snapshot"] += 1
            continue
        gz = snap.get("gozlemler")
        if gz is None:
            toplam["yuksuz_snapshot"] += 1     # yükü düşürülmüş ama işaretsiz — yeniden üretilemez
            continue
        satirlar, atl = _gorusleri_tureti(gz, set(snap.get("evren") or []), var,
                                          ts=snap.get("ts"))    # t-ÇİTİ: damga SNAPSHOT anı
        if tavan is not None and len(yazilacak) + len(satirlar) > tavan:
            # BU SNAPSHOT HİÇ İŞLENMEDİ SAYILIR: ne satırı yazılır, ne elemesi sayılır, ne
            # işaretlenir. Yarım işlenmiş bir kesit "işlendi" damgası alsaydı kalan gözlemler
            # sessizce kaybolurdu — kırpma bir SEÇİM değil, ERTELEMEDİR.
            kirpildi = True
            break
        for k, v in atl.items():
            toplam[k] = toplam.get(k, 0) + v
        yazilacak.extend(satirlar)
        islenen[i] = {"uretilen": len(satirlar), "atlanan": atl,
                      "gozlem_ozeti": _ozet_damgasi(gz), "n_gozlem": len(gz)}
    yazilan = deftere_yaz(yazilacak) if apply else 0
    if apply and islenen:
        def _isaretle(rows: list) -> bool:
            for i, bilgi in islenen.items():
                if i >= len(rows) or not isinstance(rows[i], dict):
                    continue                   # kuyruk aramızda değişti — sıra kaydı çürüdü, yazma
                rows[i] = {k: v for k, v in rows[i].items() if k != "gozlemler"}
                rows[i].update({"islendi": True, "islendi_ts": _now(), **bilgi})
            return True
        store.update_jsonl(KUYRUK_DEFTERI, _isaretle)
    bekleyen = sum(1 for s in kuyruk_oku() if isinstance(s, dict) and not s.get("islendi"))
    return {"yazilan": yazilan, "hazirlanan": len(yazilacak),
            "islenen_snapshot": (len(islenen) if apply else 0), "aday_snapshot": len(islenen),
            "bekleyen": bekleyen, "kirpildi": kirpildi, "tavan": tavan,
            "atlanan": toplam, "uygulandi_mi": bool(apply), "defter_toplam": len(var)}


# ==================================================================================================
# GÖLGE SIRALAMA KOLU (EDG-2026-078 Aşama A, TSK-126) — CANLI KARAR DEĞİŞMEZ
# ==================================================================================================
# ÖN-KAYIT: `research/cards/EDG-2026-078-skill-gorus-golge-siralama-kolu.yaml`. NE YAPAR: P3'ün
# ZATEN sıraladığı (`candidates.sort(key=score)`) aynı aday kesitine in-memory İKİNCİ, GÖLGE bir
# sıralama üretilir — `score_golge = score + w_skill · z_skill(score) · sd_kesit`. `w_skill` KART
# SABİTİDİR (kod değiştiremez) ve yalnız EDG-2026-019'un FDR-sağkalan bulduğu tek skill için
# sıfırdan farklıdır; diğer HER skill için `w=0`, yani `score_golge == score` — bugünkü davranış
# BİREBİR (MUTASYON 1 çivisi bunu ölçer). Gerçek emir HÂLÂ MEVCUT (`score`) sıralamasından çıkar;
# bu kol yalnız YAN deftere (`GOLGE_SIRALAMA_DEFTERI`) yazar, `candidates`/`plans` listesini asla
# mutasyona uğratmaz.
#
# HEDEF EŞLEŞTİRME — CF HEDEFİ SEÇİLDİ, GERÇEK DEĞİL (beyanlı sınır). Bir adayın gerçekleşen R'si
# iki farklı biçimde var olabilir: karşı-olgusal simülasyon (`CF-{tarih}-{ticker}-{setup}`, HER
# adayda vardır — bu id biçimini üreten yerel yardımcı `counterfactual.collect`in İÇİNDEDİR) ve,
# silahlanmışsa, gerçek işlem (`P-{tarih}-{ticker}[-{setup}]`, yalnız ARMED adaylarda vardır). Bu
# satır YAZILDIĞI ANDA (P2 tarama bitişinde) aday henüz silahlanıp silahlanmayacağını bilmiyor —
# o yüzden HER zaman var olan TEK biçim (CF) seçilmiştir. Payda tutarlılığı (her aday ölçülebilir) gerçek P&L'in
# inceliğine (yalnız birkaç adayda var) BİLEREK tercih edilmiştir; `golge_kol_raporu`nun kendi
# çıktısındaki `beyan` alanı bunu TEKRARLAR (gizlenmez).
GOLGE_SIRALAMA_DEFTERI = "golge_siralama.jsonl"    # LİTERAL ad (codelaw.artifact_graph çözebilsin)
PENCERE_DEFTERI = "skill_gorus_pencereler.jsonl"   # EDG-2026-019 kill#3'ün "ardışık pencere" borcu

KART_GOLGE_ID = "EDG-2026-078"
# KART SABİTLERİ — ÖLÇÜMDEN ÖNCE DONDURULDU (kart `agirliklar`/`esikler`); kod bunları
# DEĞİŞTİREMEZ. Kart eşitliği çivisi (`tests/test_golge_siralama_kolu_v425.py`) bu sabitleri kart
# YAML'ının METNİYLE karşılaştırır.
KART_GOLGE_AGIRLIKLARI = {"stockbee-exhaustion-hammer-screener": 0.169}   # diğer HER skill 0.0
KART_N_MIN_SEANS = 30              # n_seans < bu → "ÖLÇÜLDÜ — ÖRNEKLEM YETERSİZ" (hüküm YOK)
KART_GOLGE_USTN_KESISIM_MIN = 0.50   # kart eşiği: üst-N kesişimi ort ≥ bu (kol "yeni strateji" olmasın)


def golge_siralama_kancasi(candidates: list[dict], N: int, dstr: str) -> dict:
    """P3 aday kesitine gölge (görüşlü) ikinci sıralama yazar — CANLI SIRALAMAYI DEĞİŞTİRMEZ.

    `candidates` YALNIZ OKUNUR: ne yeniden sıralanır ne satırları değiştirilir. `sira_mevcut`,
    listenin KENDİ indeksinden çıkar (`candidates` çağrıya girdiğinde ZATEN `score` azalan sırada
    — P3'ün az önce yaptığı sort) — burada AYRICA sıralanmaz; bu, MUTASYON 1 çivisinin dayanağıdır
    (bu fonksiyon kaldırılsa/`KART_GOLGE_AGIRLIKLARI` sıfırlansa `candidates`in KENDİSİ hiç
    değişmemiş olur, çünkü zaten değiştirilmiyordu).

    `N` çağıranın ölçtüğü o seansın açık slot sayısıdır (`limits["max_open_positions"] -
    len(b.positions)`) — burada YENİDEN hesaplanmaz (tek-kaynak yasası). N ≤ 0 ise 0'a ÇEKİLİR ve
    defter satırı YİNE yazılır (kart adım_0: "N=0 ve satır yine yazılır" — o seansta yeni aday için
    yer yoktur ama gölge ölçümü kesintiye uğramaz).

    Defter yalnız `sira_mevcut ≤ max(2N,20) VEYA sira_golge ≤ max(2N,20)` olan adayları taşır
    (kart adım_0: "defter satırı üst max(2N,20) ile sınırlı") — süresiz büyümesin diye.

    `sure_ms` YALNIZ hesaplama bloğunu (z/score_golge/sıra/eşik) ölçer, YAZIMI DEĞİL — aynı
    gerekçeyle bu modülün `kuyruk_kadansi`sindeki `gozetim_ms` ayrımı: yazım maliyeti (küçük,
    aday sayısından bağımsız satır başına sabit `append_jsonl`) DEĞİŞKEN olan hesaplama
    maliyetinden AYRI tutulur — ikisini karıştırmak kill#1 tarzı bir pay ölçümünü bulandırırdı."""
    t0 = time.perf_counter()
    n_gun = max(0, int(N))
    n = len(candidates)
    if n == 0:
        return {"yazilan": 0, "n_aday": 0, "N": n_gun,
                "sure_ms": round((time.perf_counter() - t0) * 1000.0, 2)}
    import numpy as np
    skorlar = np.asarray([float(c["score"]) for c in candidates], dtype=float)
    sd_kesit = float(skorlar.std())
    per_skill: dict[str, list[float]] = {}
    for c in candidates:
        per_skill.setdefault(c.get("source_skill"), []).append(float(c["score"]))
    # KESİT İSTATİSTİĞİ YOKSA z=0 (kart formülü): <3 aday ya da sd==0 — bölme sıfıra DÜŞMEZ,
    # görüş basitçe SESSİZDİR (skoru değiştirmez), UYDURULMAZ (None ya da hata değil, tanımlı 0).
    skill_istat: dict[str | None, tuple[float, float] | None] = {}
    for sk, degerler in per_skill.items():
        arr = np.asarray(degerler, dtype=float)
        sd = float(arr.std())
        skill_istat[sk] = (float(arr.mean()), sd) if len(arr) >= 3 and sd > 0 else None

    z_ler: list[float] = []
    golge_skorlar: list[float] = []
    for c in candidates:
        istat = skill_istat.get(c.get("source_skill"))
        skor = float(c["score"])
        z = 0.0 if istat is None else (skor - istat[0]) / istat[1]
        w = KART_GOLGE_AGIRLIKLARI.get(c.get("source_skill"), 0.0)
        z_ler.append(z)
        golge_skorlar.append(skor + w * z * sd_kesit)

    sira_mevcut = list(range(1, n + 1))                          # candidates ZATEN score-desc
    golge_index = sorted(range(n), key=lambda i: golge_skorlar[i], reverse=True)
    sira_golge = [0] * n
    for rank, idx in enumerate(golge_index, start=1):
        sira_golge[idx] = rank

    esik = max(2 * n_gun, 20)
    yazilacak: list[dict] = []
    for i, c in enumerate(candidates):
        sm, sg = sira_mevcut[i], sira_golge[i]
        if sm > esik and sg > esik:
            continue
        setup = c.get("setup") or "?"
        yazilacak.append({
            "date": dstr, "ticker": c.get("ticker"), "source_skill": c.get("source_skill"),
            # HEDEF: cf'nin kendi id biçimiyle BİREBİR (modül başlığındaki BEYAN) — okuyucu
            # (`golge_kol_raporu`) `_gozlemler()`in cf-kaynaklı satırlarıyla bunu STRING eşitliğiyle
            # eşler, geri-ayrıştırma (parse) YOKTUR.
            "hedef": f"CF-{dstr}-{c.get('ticker')}-{setup}",
            "score": float(c["score"]), "z_skill": round(z_ler[i], 6),
            "score_golge": round(golge_skorlar[i], 6),
            "sira_mevcut": sm, "sira_golge": sg, "N": n_gun,
            "ustN_mevcut": bool(n_gun > 0 and sm <= n_gun),
            "ustN_golge": bool(n_gun > 0 and sg <= n_gun),
        })
    sure_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    for row in yazilacak:
        row["sure_ms"] = sure_ms
        store.append_jsonl(GOLGE_SIRALAMA_DEFTERI, row)
    return {"yazilan": len(yazilacak), "n_aday": n, "N": n_gun, "sure_ms": sure_ms}


def golge_kol_raporu() -> dict:
    """GÖLGE SIRALAMA KOLUNUN HÜKMÜ (EDG-2026-078 Aşama A) — SAF OKUMA, CANLI KARARA DOKUNMAZ.

    `GOLGE_SIRALAMA_DEFTERI`ni okur, seans başına (date) gerçekleşen R'yi `_gozlemler()` ile eşler
    (anahtar: (tarih, hedef); `_gozlemler`in hedef alanı NE İSE O kullanılır — bkz. modül başlığı
    BEYANI: yalnız CF-kaynaklı gözlemler eşleşir). Eşleşmeyen `eslesmeyen_n`de sayılır, sessizce
    düşmez.

    Seans başına rank-IC(mevcut) = spearman(−sira_mevcut, R), rank-IC(gölge) = spearman(−sira_golge,
    R); Δ = gölge − mevcut. `_ci` (`faz5_cikis.tarih_kumeli_bootstrap` — YENİDEN KULLANILIR, ikinci
    bir bootstrap İCAT edilmez) Δ listesini seans tarihleriyle kümeler — burada küme birimi zaten
    SEANSTIR ve her seansın TEK bir Δ'sı vardır, yani kümeleme kümeler-arası dağılıma düşer (aynı
    yöntem, aynı dürüstlük: `n_kume < 2` ise aralık kurulmaz).

    `n_seans < KART_N_MIN_SEANS` → durum "ÖLÇÜLDÜ — ÖRNEKLEM YETERSİZ" (sayı YİNE basılır, HÜKÜM
    YOK — kartın eşiğini işlemek Rol-1'e aittir, bu fonksiyon bir GEÇTİ/KALDI döndürmez)."""
    satirlar = store.read_jsonl(GOLGE_SIRALAMA_DEFTERI)
    if not satirlar:
        return {"durum": "ÖLÇÜLEMEDİ", "kart": KART_GOLGE_ID,
                "neden": f"`{GOLGE_SIRALAMA_DEFTERI}` boş — gölge sıralama kancası hiç yazmadı",
                "n_seans": 0, "n_min_seans": KART_N_MIN_SEANS, "delta_rank_ic": None,
                "ustN_kesisim_ort": None, "sure_p95_ms": None, "eslesmeyen_n": None}
    gz = _gozlemler()
    sonuclar = {(str(g.get("tarih")), str(g.get("hedef"))): g for g in gz["satirlar"]}
    seanslar: dict[str, list[dict]] = {}
    for r in satirlar:
        seanslar.setdefault(str(r.get("date")), []).append(r)
    from . import analytics
    eslesmeyen_n = 0
    delta_list: list[float] = []
    tarih_list: list[str] = []
    kesisim_list: list[float] = []
    sure_list: list[float] = []
    for tarih, rows in sorted(seanslar.items()):
        ciftler_mevcut, ciftler_golge = [], []
        ustN_mevcut_kume: set = set()
        ustN_golge_kume: set = set()
        n_gun = None
        for r in rows:
            if r.get("sure_ms") is not None:
                sure_list.append(float(r["sure_ms"]))
            s = sonuclar.get((tarih, r.get("hedef")))
            if s is None or s.get("r") is None:
                eslesmeyen_n += 1
                continue
            R = float(s["r"])
            ciftler_mevcut.append((-float(r["sira_mevcut"]), R))
            ciftler_golge.append((-float(r["sira_golge"]), R))
            if r.get("ustN_mevcut"):
                ustN_mevcut_kume.add(r.get("ticker"))
            if r.get("ustN_golge"):
                ustN_golge_kume.add(r.get("ticker"))
            n_gun = r.get("N")
        if len(ciftler_mevcut) < 2:
            continue                      # rank-IC en az 2 gözlem ister (tekli rütbe tanımsız)
        ic_mevcut = analytics.spearman_ic(ciftler_mevcut)
        ic_golge = analytics.spearman_ic(ciftler_golge)
        if ic_mevcut is None or ic_golge is None:
            continue                      # o seansın rank-IC'i tanımsız (sabit sıra/R) — SAYILMAZ
        delta_list.append(ic_golge - ic_mevcut)
        tarih_list.append(tarih)
        if n_gun and n_gun > 0:
            kesisim_list.append(len(ustN_mevcut_kume & ustN_golge_kume) / n_gun)
    n_seans = len(delta_list)
    sure_p95 = _yuzdelik(sure_list, 0.95)
    if n_seans == 0:
        return {"durum": "ÖLÇÜLEMEDİ", "kart": KART_GOLGE_ID,
                "neden": "hiçbir seansta ≥2 eşleşen (sıra, R) çifti kurulamadı — rank-IC tanımsız",
                "n_seans": 0, "n_min_seans": KART_N_MIN_SEANS, "delta_rank_ic": None,
                "ustN_kesisim_ort": None, "sure_p95_ms": sure_p95, "eslesmeyen_n": eslesmeyen_n}
    ci = _ci(delta_list, tarih_list)
    ustN_kesisim_ort = (sum(kesisim_list) / len(kesisim_list)) if kesisim_list else None
    return {
        "durum": ("ölçüldü" if n_seans >= KART_N_MIN_SEANS else "ÖLÇÜLDÜ — ÖRNEKLEM YETERSİZ"),
        "kart": KART_GOLGE_ID, "neden": None,
        "n_seans": n_seans, "n_min_seans": KART_N_MIN_SEANS,
        "delta_rank_ic": {"ort": ci.get("ort"), "lo": ci.get("lo"), "hi": ci.get("hi"),
                          "n_kume": ci.get("n_kume"), "yontem": ci.get("yontem")},
        "ustN_kesisim_ort": ustN_kesisim_ort, "n_kesisim_seans": len(kesisim_list),
        "ustN_kesisim_esik": KART_GOLGE_USTN_KESISIM_MIN,
        "ustN_kesisim_esigi_gecti": (None if ustN_kesisim_ort is None
                                     else bool(ustN_kesisim_ort >= KART_GOLGE_USTN_KESISIM_MIN)),
        "sure_p95_ms": sure_p95, "eslesmeyen_n": eslesmeyen_n,
        "beyan": ("Gerçekleşen R KAYNAĞI yalnız CF simülasyonudur (adayın silahlanıp "
                  "silahlanmadığından BAĞIMSIZ, her adayda var); gerçek işlem sonucu bu ölçümde "
                  "KULLANILMAZ (modül başlığı BEYANI). Δrank-IC CI-altı > 0 ∧ üst-N kesişimi ≥ "
                  f"{KART_GOLGE_USTN_KESISIM_MIN} HÜKMÜNÜ bu fonksiyon VERMEZ — kartın eşiğini "
                  "işlemek Rol-1'e aittir (CLAUDE.md §5)."),
    }


def _golge_kol_guvenli() -> dict:
    """`golge_kol_raporu()`yu `rapor()`ın GERİSİNE düşürmeden çağırır.

    YASA 4: bu ÖLÇÜM yeni (2026-09-05) ve düşerse `rapor()`ın — EDG-2026-019'un ÜÇ AYLIK kararlı
    yüzeyinin — TAMAMINI 'ÖLÇÜLEMEDİ'ye çekmemeli. Kendi try/except'i, kendi olayı."""
    try:
        return golge_kol_raporu()
    except Exception as e:
        from . import obs
        obs.warn("golge_kol_raporu_failed", error=f"{type(e).__name__}: {e}",
                 detail="EDG-2026-078 gölge kol hükmü bu turda ÖLÇÜLEMEDİ — skill_gorus.rapor()ın "
                        "kalanı ETKİLENMEDİ")
        return {"durum": "ÖLÇÜLEMEDİ", "kart": KART_GOLGE_ID, "neden": f"{type(e).__name__}: {e}",
                "n_seans": None, "n_min_seans": KART_N_MIN_SEANS, "delta_rank_ic": None,
                "ustN_kesisim_ort": None, "sure_p95_ms": None, "eslesmeyen_n": None}


# ==================================================================================================
# PENCERE SAYACI (EDG-2026-019 kill#3 borcu, EDG-2026-078 dilimiyle kapatıldı)
# ==================================================================================================
# NEDEN VAR. Kart kill#3 "3 ARDIŞIK pencere" ister ama `rapor()` bugüne dek "pencere sayacı bu
# turda YOK" diyordu — ne terfinin "2 pencere" (Aşama B ön şartı) ne emekliliğin "3 pencere"si
# ÖLÇÜLEBİLİYORDU. Yazan TEK yer `pencere_yaz()` (çağıran: `ops/skill_gorus_uret.py`, her
# `--uygula` koşumunda BİR kez); `rapor()` yalnız OKUR (`_pencere_ozeti`, saf okuma) — saf okuma
# sözleşmesi bozulmaz.
def pencere_yaz(rapor_sonucu: dict | None = None, *, kosum_tarihi: str | None = None) -> dict:
    """`rapor()`ın O ANKİ hükmünden skill×yüzey başına bir PENCERE satırı türetir ve deftere ekler.

    İDEMPOTENT — GÜN ANAHTARI: bu güne ait ZATEN bir satır varsa (herhangi bir skill/yüzey için)
    HİÇBİR ŞEY YAZILMAZ; aynı günün ikinci koşumu sayacı ÇİFTLEMEZ. `rapor_sonucu` verilmezse
    `rapor()` burada çağrılır (ops betiği zaten kendi `rapor()`ını hesapladıysa TEKRAR
    hesaplatmadan geçebilir).

    HER ÖLÇÜLEN SKİLL YAZILIR — `yon` SIFIR OLSA BİLE: bir günü ATLAMAK, o günün "sağkalmadı"
    bilgisini SESSİZCE KAYBEDER ve `_pencere_ozeti`nin ardışıklık sayımını YANLIŞ UZATIR (aradaki
    boşluk hiç olmamış gibi görünür). "ölçüldü" OLMAYAN yüzeyler (`durum != "ölçüldü"`) o gün için
    hiç yazılmaz — orada bir yön HÜKMÜ yoktur, uydurulmaz."""
    gun = str(kosum_tarihi or _now())[:10]
    mevcut = store.read_jsonl(PENCERE_DEFTERI)
    if any(r.get("kosum_tarihi") == gun for r in mevcut):
        return {"yazilan": 0, "kosum_tarihi": gun, "atlandi": True,
                "neden": "bu gün için zaten yazılmış (idempotent, gün anahtarı)"}
    r = rapor_sonucu if rapor_sonucu is not None else rapor()
    yazilan = 0
    for yuzey, y in (r.get("yuzeyler") or {}).items():
        if y.get("durum") != "ölçüldü":
            continue
        for sk, v in (y.get("skiller") or {}).items():
            store.append_jsonl(PENCERE_DEFTERI, {
                "kosum_tarihi": gun, "skill": sk, "yuzey": yuzey,
                "yon": v.get("yon") or 0,
                "sagkalan": bool((v.get("fdr") or {}).get("sagkalan")),
                "n": v.get("n"),
            })
            yazilan += 1
    return {"yazilan": yazilan, "kosum_tarihi": gun, "atlandi": False}


def _pencere_ozeti() -> dict[tuple, dict]:
    """(skill, yüzey) → {"ardisik_pencere": int, "pencere_n": int} — saf okuma.

    `ardisik_pencere`: EN SON pencereden GERİYE, `sagkalan=True` ∧ `yon` en son pencereninkiyle AYNI
    olduğu sürece sayılır; ilk uyumsuzlukta (yön değişti YA DA sağkalmadı) durur. Yön DEĞİŞTİĞİNDE
    eski seri TAŞINMAZ — sayaç yeni yönle YENİDEN başlar (bugünkü tek pencere zaten sağkalmışsa 1'den)."""
    per: dict[tuple, list[dict]] = {}
    for row in store.read_jsonl(PENCERE_DEFTERI):
        per.setdefault((row.get("skill"), row.get("yuzey")), []).append(row)
    out: dict[tuple, dict] = {}
    for anahtar, satirlar in per.items():
        satirlar = sorted(satirlar, key=lambda r: str(r.get("kosum_tarihi") or ""))
        ardisik = 0
        if satirlar:
            son_yon = satirlar[-1].get("yon")
            for row in reversed(satirlar):
                if row.get("sagkalan") and row.get("yon") == son_yon:
                    ardisik += 1
                else:
                    break
        out[anahtar] = {"ardisik_pencere": ardisik, "pencere_n": len(satirlar)}
    return out
