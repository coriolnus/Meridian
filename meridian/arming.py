"""arming.py — silahlanma değerlendiricisi: uyuyan→ölç→silahla döngüsünün kapı-ölçümü halkası.

NE YAPAR. Uyuyan kurulumlar karşı-olgusal defterde ileriye dönük ölçülür; küme SABİT DEĞİL,
`_dormant_setups()` motor listesinden ARMED_SETUPS'ı düşerek TÜRETİR (silahlanan kurulum kümeden
kendiliğinden çıkar). Kanıt YAZILI eşiği geçince (kurulum başına en az MIN_CF_ENTERED=30 girilmiş
cf kaydı VE cf ortalama R'si MIN_CF_AVG_R üstünde) `evaluate` kapı ölçümünü otomatik koşar:
incumbent (mevcut silahlı set) vs aday (aynı parametreler + kurulum silahlı) üretim pencerelerinde
walk edilir ve karar TAMAMEN mevcut yasaya bırakılır (blok-bootstrap + K-ceza + fold çoğunluğu +
kuyruk vetosu). Ölçüm kanalı params["entry.armed_extra"]dır — scan_entry bu listedeki kurulumları
da silahlı sayar; global ARMED_SETUPS'a dokunulmadığı için canlı döngüyle YARIŞMAZ.

DEĞİŞMEZLER. SİLAHLANMA OTOMATİK DEĞİLDİR: kapı GEÇSE bile ARMED_SETUPS değişmez — sonuç rapora
"silahlanmaya hazır (P=…)" düşer, operatör onayı beklenir (canlı davranış değişikliği bilinçli bir
insan kararıdır). ÖLÇÜM TURU BLOKE EDEMEZ: walk çifti bir SÜRE TAVANIYLA koşar (SURE_TAVANI_S=600
sn; env SURE_TAVANI_ENV ile operatör-ayarlı); tavan aşılırsa tur "ölçülemedi" damgasıyla DEVAM
eder, hesap arka planda tek uçuş olarak (nabız atarak) sürer ve bitince raporu KENDİ işler —
ölçüm iptal değil ERTELENMİŞ olur. Tavan aşımı hiçbir kapıyı gevşetmez, hiçbir kurulumu
silahlandırmaz; ölçülemeyen sayı None + neden (UYDURMA YASAĞI). Rapora bar parmak izi damgalanır
(sayıların hangi veri sürümüne ait olduğu okunabilir kalsın).

OKUR: karşı-olgusal defter (kanıt eşiği), barlar/endeks (walk girdisi). YAZAR: arming_report.json
(+ obs olayları); başka hiçbir deftere ya da karara yazmaz."""
from __future__ import annotations

import datetime as _dt
import hashlib
import os
import threading
import time

from . import config, store, obs

REPORT_FILE = "arming_report.json"
MIN_CF_ENTERED = 30        # kapı ölçümünü tetiklemek için kurulum başına en az girilmiş cf kaydı
MIN_CF_AVG_R = 0.0         # ve cf ortalama R'si pozitif olmalı (negatif kanıtla walk yakmayız)

# ================================================================================================
# SÜRE TAVANI (v189, 2026-08-05) — "ölçüm turu bloke edemez"
# ================================================================================================
# ÖLÇÜLEN VAKA, TAHMİN DEĞİL. Canlı A1 olay defteri (`earnings_calendar_refreshed` → o turun
# `arming_measured` olayı arası; ikisi `advance_once` içinde ARDIŞIK bloklardır):
#     2026-07-23  31,0 dk · 2026-07-27  32,1 dk ve 66,0 dk · 2026-07-28  29,7 dk · 2026-07-29
#     27,2 dk ve 27,3 dk   →  ve `deploy/oracle-a1/tick_watchdog.sh` başlığındaki iki ölçülmüş
#     pencere (2026-07-31): 100,3 dk ve 84,6 dk, İKİSİ DE aynı iki olay arasında.
# Yani bir arming turu (incumbent walk + aday walk) canlıda 27-100 DAKİKA sürüyor. Yerel doğrulama:
# tek `walk_forward` (2022-01-01→2026-07-30, 251 sembol, bu depo) 12,1 dk — tur = İKİ walk.
#
# İKİ HİPOTEZ ÖLÇÜLDÜ VE İKİSİ DE YANLIŞLANDI (kayda geçsin ki bir dahaki tur onları tekrar
# kovalamasın):
#   * "2026-08-03 icra yasası (limit min(0,5·ATR,%1) → min(100·ATR,%4)) replay'i AĞIRLAŞTIRDI":
#     HAYIR, HAFİFLETTİ. Aynı pencerede yeni yasa 727,5 sn / 157 işlem / 148.771 `scan_entry`;
#     eski yasa 1116,2 sn / 147 işlem / 152.848 `scan_entry`. Mekanizma: daha çok dolum → portföy
#     daha sık dolu → `slots == 0` → o seans TARAMA HİÇ KOŞMUYOR. Yasa turu %35 KISALTTI.
#     (Yan bulgu, kapı kararı DEĞİL: aynı koşumda OOS skor 0,0221 → 0,0572.)
#   * "`_wf_cached` anahtarı goal/yasa özetini içerdiği için her çağrı önbellek ISKASI": HAYIR,
#     anahtar yasayı HİÇ içermiyordu. Gerçek kusur tersiydi ve DOĞRULUK kusuruydu (bkz. reflect.py
#     v189 bloğu (a)). Önbellek ıskasının GERÇEK sebebi başkaydı: ADAY walk'ı `_wf_cached`e hiç
#     uğramıyordu (anahtar kurucusu `entry.armed_extra` listesinde TypeError fırlatırdı), yani
#     turun yarısı her seferinde sıfırdan hesaplanıyordu.
#
# ÜÇ GERÇEĞİN KESİŞİMİ ASILMAYI ÜRETİYORDU (2026-08-04/05, iki gece üst üste EOD döngüsü bitmedi):
#   1. Bu yol NABIZ ATMIYOR — `scheduler.nabiz` çağrısı yok, yani asılı-tick bekçisi (2700 sn,
#      2026-08-02'de ONARILDI ve KALICI yapıldı) turu ölçümün ORTASINDA öldürüyor.
#   2. `arming_week` damgası `scheduler._DURABLE` listesinde DEĞİL → yeniden başlatma damgayı
#      siler ve bir sonraki taze poll ölçümü SIFIRDAN başlatır.
#   3. Blok `daily_cycle`dan ÖNCEdir → ölçüm bitmeden karar turu HİÇ koşmaz.
# Üçü birlikte bir CANLI KİLİT üretir: ölç → 45 dk'da öldürül → damga silinsin → yeniden ölç…
# Karar yüzeyi (daily_cycle) hiç sıra alamaz. 2 ve 3 `scheduler.py`nin yüzeyidir; bu turda O DOSYA
# AÇILMADI. 1 ve asıl kilit BURADAN kapatılır: ölçüm bir SÜRE TAVANIYLA koşar, tavan aşılırsa tur
# "ölçülemedi" damgasıyla DEVAM EDER (döngü tamamlanır, daily_cycle sıra alır) ve hesap arka planda
# sürüp bittiğinde raporu KENDİ işler — yani ölçüm İPTAL değil ERTELENMİŞ olur.
#
# KARAR YÜZEYİ FAIL-OPEN OLMAZ: bu modülün tek çıktısı bir RAPORDUR ve silahlanma zaten operatör
# onayına bağlıdır. Tavan aşımı hiçbir kapıyı gevşetmez, hiçbir kurulumu silahlandırmaz; yalnız
# "bu tur ölçemedik" der ve nedenini yazar (UYDURMA YASAĞI: ölçülemeyen sayı None + neden).
SURE_TAVANI_ENV = "MERIDIAN_ARMING_TAVAN_S"
# 600 sn = bekçi eşiğinin (2700 sn) ~%22'si. Türetimi: turun geri kalanı (bar yükleme + onarım
# geçidi + kazanç takvimi + daily_cycle) canlıda tek başına 10-25 dk sürebiliyor; ölçüme bekçi
# bütçesinin dörtte birinden fazlasını vermek, o turun TOPLAMINI yine eşiğin üstüne çıkarırdı.
# Bu bir ARAMA EŞİĞİ DEĞİL bir işletim bütçesidir (hiçbir hüküm/kapı bu sayıyı okumaz).
SURE_TAVANI_S = 600.0
NABIZ_ARA_S = 15.0         # bekleyen tur, uçuştaki ölçüm YAŞADIĞI sürece bu aralıkla nabız atar

_UCUS: dict = {}           # {"slot": {...}} — TEK uçuş: aynı anda en fazla bir arka plan ölçümü
_UCUS_KILIT = threading.Lock()


def _tavan_s() -> float:
    """Yürürlükteki süre tavanı (env ile operatör değiştirebilir). Bozuk/negatif değer sessizce
    geçmez, varsayılana düşer — `broker.entry_law` kelepçesiyle aynı yasa."""
    try:
        v = float(os.environ.get(SURE_TAVANI_ENV, SURE_TAVANI_S))
    except (TypeError, ValueError):  # sessiz-yutma: biçimsiz env değeri = yasa yok değil, varsayılan; yürürlükteki değer raporun `tavan_s` alanında YAZILI
        return SURE_TAVANI_S
    return v if v > 0 else SURE_TAVANI_S


def _nabiz(asama: str) -> None:
    """İLERLEME NABZI — biçim kararları `loop._nabiz` / `adapters.data._nabiz` ile
    AYNI (fonksiyon-içi geç import, hüküm zamanlayıcıda, istisna yutulur).

    NEDEN BURADA MEŞRU: nabız yalnız ölçüm ipliği YAŞARKEN ve yalnız SÜRE TAVANI dolana kadar
    atılır — yani bekçiyi körleştirebileceği pencere yapısal olarak tavanla sınırlıdır. Gerçekten
    tek bir çağrıda asılan bir süreç tavanı aşar, nabız DURUR ve bekçi onu eskisi gibi yakalar."""
    try:
        from . import scheduler
        scheduler.nabiz(asama)
    except Exception:  # sessiz-yutma: nabız saf telemetridir — zamanlayıcı bu süreçte yüklü olmayabilir (test/sprint/replay) ve bir damga denemesi ölçümü ASLA düşüremez
        pass


def _simdi() -> str:
    """Şu anki UTC zamanını saniye çözünürlüklü ISO-8601 metni olarak verir."""
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def _bar_parmak(bars) -> str:
    """Ölçümün HANGİ bar sürümüyle koştuğunun parmak izi (sembol · satır sayısı · son tarih).
    Arka planda biten bir ölçüm rapora yazılırken bu damga da yazılır: sayıların hangi veriye ait
    olduğu okunabilir olmalıdır (barlar arada tazelenmiş olabilir)."""
    h = hashlib.sha256()
    try:
        for t in sorted(bars or {}):
            df = bars[t]
            try:
                son = df["date"].iloc[-1] if "date" in getattr(df, "columns", []) else df.index[-1]
                h.update(f"{t}|{len(df)}|{son}|".encode("utf-8"))
            except Exception:  # sessiz-yutma: tek sembolün biçimi beklenmedik — parmak izi TELEMETRİDİR, bir sembol yüzünden ölçüm düşemez; belirsizlik damgaya '?' olarak girer
                h.update(f"{t}|?|?|".encode("utf-8"))
    except Exception:  # sessiz-yutma: sözlük hiç gezilemedi (None/beklenmedik tip) — dürüst yanıt "ölçülemedi", uydurma bir damga değil
        return "olculemedi"
    return h.hexdigest()[:16]


def setup_report() -> dict:
    """Karşı-olgusal defterin kurulum kırılımı: n (girilmiş), kazanma, ort. R, rejim dağılımı.
    Panel + eşik kararı buradan okur; hiçbir karar yetkisi yok."""
    from . import counterfactual as cf
    by: dict[str, dict] = {}
    for r in cf.resolved_rows(entered_only=True):
        s = str(r.get("setup") or "?")
        b = by.setdefault(s, {"n": 0, "wins": 0, "sum_r": 0.0, "regimes": {}})
        b["n"] += 1
        rm = float(r.get("r_multiple") or 0.0)
        b["wins"] += 1 if rm > 0 else 0
        b["sum_r"] += rm
        reg = str(r.get("regime") or "?")
        b["regimes"][reg] = b["regimes"].get(reg, 0) + 1
    return {s: {"n": b["n"], "win_rate": round(b["wins"] / b["n"], 3),
                "avg_r": round(b["sum_r"] / b["n"], 3), "regimes": b["regimes"]}
            for s, b in by.items() if b["n"]}


def _dormant_setups() -> list[str]:
    """Motorun tanıdığı ama HENÜZ SİLAHLANMAMIŞ (canlı deftere risk yazmayan) setup adlarını verir.

    BEYANLI BOŞLUK — E-kod [3] ölçümü (2026-08-23), DAVRANIŞ BU TURDA DEĞİŞMEDİ. Aşağıdaki
    `engine` tuple'ı elle yazılmıştır ve kanonik türetimden (setup→screener eşlemesi
    `skills._SCREENER_BY_SETUP` ∩ `skills.ENGINE_IMPLEMENTED`) İKİ adla ayrışır:
      * `exhaustion_hammer` — 2026-08-11'de motor-uygulandı VE silahlandı. Bugün ZARARSIZ
        (silahlı olduğu için türetim de onu uyuyan saymazdı) ama LATENT: bir gün silahtan
        düşerse hem uyuyan kümeden hem kurulum kırılımından SESSİZCE kaybolurdu.
      * `pead` — motor-uygulanmış (strategy.py:883 `setup="pead"`, screener ENGINE_IMPLEMENTED)
        ve SİLAHSIZ, yani TANIM GEREĞİ uyuyandır; karşı-olgusal deftere satır yazar ama
        silahlanma kapısı onu HİÇ değerlendirmiyor.
    İkinci adı eklemek uyuyan-kanıt kanalının kapsamını genişletir (kapı yeni bir kurulumu
    tartmaya başlar) — bu bir ÖLÇÜM/KAPI kararıdır, kart-önce ve Rol-1'de. Bu yüzden burada
    yalnız BEYAN var, değişiklik yok; ayrışmanın büyümesi `tests/test_e_partisi_v278.py`
    (test_3d) ile çivili: kümeye üçüncü bir ad girerse kırmızı yanar.
    `canslim` BİLEREK dışarıda: motor onu koşturur ama `evaluate_canslim` daima None döner
    (strategy.py:900) — ENGINE_IMPLEMENTED'a da bu yüzden alınmadı."""
    from . import strategy as strat
    engine = ("breakout_vcp", "momentum_burst", "pullback", "episodic_pivot")
    return [s for s in engine if s not in strat.ARMED_SETUPS]


# KURULUM → ZORUNLU NOKTA-ZAMAN ÇAPASI. Bu kurulumlar çapa çözülemeyince ATEŞLEMEZ; dışarıdan
# "sinyal vermedi" gibi görünürler ve rapor onları "örneklem dolmadı" diye yazıyordu. Kayıt bir
# İDDİA değildir: v301 çivisi her iki yönü de bağlar — kayıttaki her ad çapayı GERÇEKTEN çağırmalı,
# ve çapayı çağıran her kurulum kayıtta OLMALI (yeni bir kazanç-çapalı kurulum eklenirse çivi öter).
PIT_CAPALI_KURULUMLAR = {
    "episodic_pivot": "earnings.days_since_report",
    "pead": "earnings.days_since_report",
}


def _kanit_durumu(setup: str, r: dict) -> dict:
    """Eşiği geçemeyen UYUYAN kurulum için DOĞRU cümleyi seçer.

    İKİ DÜNYA, İKİ CÜMLE (kart EDG-2026-060, 2026-08-25):
      · seyrek ateşleyen ama ÖLÇÜLEBİLEN kurulum → `insufficient_cf`: kanıt birikiyor, bekle.
      · PIT çapası çözülemeyen kurulum          → `olculemez_pit_yok`: kanıt BİRİKEMEZ, bekleme
        boşuna. Geri dolumu tekrar koşturmak bunu ASLA çözmez; arşiv gerekir.
    Tek etikete toplamak `_olculemedi`nin şerhindeki hatanın aynısıydı: "ölçülemedi = reddedildi".

    KAPSAM DAR TUTULDU: PIT kaydında OLMAYAN hiçbir kurulumun cümlesi değişmez (çivi v301)."""
    n, avg = r.get("n", 0), r.get("avg_r")
    capa = PIT_CAPALI_KURULUMLAR.get(setup)
    if capa is None:
        return {"status": "insufficient_cf", "n": n, "avg_r": avg}

    from . import counterfactual as cf, earnings as earn
    takvim, defter = earn.takvim_ufku(), cf.defter_ufku()
    # İKİ ALT SEBEP, İKİ AYRI ÇARE — tek cümleye toplamak operatörü yanlış işe yollar:
    #   takvim_bos → takvim hiç çekilmemiş; çare BUGÜN uygulanabilir (`earnings.refresh`).
    #   arsiv_yok  → takvim var ama ileriye dönük bir tazeleme önbelleği; çare bir PIT ARŞİVİdir.
    # Hüküm SINIFI ikisinde de aynıdır (kanıt BİRİKEMEZ, "birikiyor" değil) ve bu bilinçli:
    # ikisinde de `days_since_report` her gün False döner, yani kurulum ateşleyemez.
    if takvim["n_tarih"] == 0:
        alt, cumle = "takvim_bos", (
            f"kazanç takvimi BOŞ ({takvim['neden']}) → çapa HİÇBİR gün için çözülemez. "
            "Bu bir örneklem sorunu değil: takvim çekilene kadar kurulum hiç ateşleyemez.")
    elif takvim["ilk"] and defter["ilk"] and takvim["ilk"] > defter["ilk"]:
        alt, cumle = "arsiv_yok", (
            f"kazanç takvimi bir NOKTA-ZAMAN ARŞİVİ değil, ileriye dönük tazeleme önbelleği: "
            f"takvim {takvim['ilk']}→{takvim['son']} ({takvim['n_tarih']} tarih), "
            f"defter {defter['ilk']}→{defter['son']} ({defter['n']} satır). Defterin "
            "başındaki seanslar için çapa sorusu SORULAMAZ; geri dolumu tekrar koşturmak "
            "kanıt üretmez, ARŞİV gerekir.")
    else:
        # Çapa defterin tamamını kapsıyor → kuraklık GERÇEKTEN örneklem sorunudur.
        # Arşiv gelirse cümle KENDİLİĞİNDEN buraya döner; mazeret kalıcılaşmaz.
        return {"status": "insufficient_cf", "n": n, "avg_r": avg}
    return {"status": "olculemez_pit_yok", "alt_sebep": alt, "n": n, "avg_r": avg,
            "capa": capa, "takvim": takvim, "defter": defter,
            "neden": f"{setup} çapasız ateşlemez ({capa}) ve {cumle}"}


def _olculemedi(neden: str, **ek) -> dict:
    """"ÖLÇÜLEMEDİ" terminali — `gate_undefined`in (ölçüm YAPILDI, sayı tanımsız) AKRABASI ama
    AYNISI DEĞİL: burada ölçüm HİÇ tamamlanmadı. İkisini tek etikete toplamak, "ölçülemedi = reddedildi" hatasının yeni bir kopyası olurdu. Sayı alanları
    None kalır (UYDURMA YASAĞI) ve `neden` her zaman yazılıdır."""
    return {"status": "olculemedi", "neden": neden,
            "search_p": None, "p_required": None,
            "incumbent_oos": None, "candidate_oos": None, "fold_wins": None,
            "tavan_s": _tavan_s(), **ek}


def _isci(setup: str, bars, index, kutu: dict, parmak: str) -> None:
    """ÖLÇÜM İPLİĞİ. Sonucu kutuya bırakır; tur onu tavan içinde ALMADIYSA (`devredildi`) raporu
    KENDİSİ işler — yani tavan aşımı ölçümü İPTAL değil ERTELER."""
    try:
        sonuc = _measure(setup, bars, index)
    except Exception as e:
        sonuc = {"error": f"{type(e).__name__}: {e}"}      # eski davranışla aynı şekil
    with _UCUS_KILIT:                     # ATOMİK: tur "devrettim" derken işçi "bitirdim" diyemez
        kutu["sonuc"] = sonuc
        kutu["bitti"] = True
        devredildi = bool(kutu.get("devredildi"))
    if devredildi:
        _rapora_isle(setup, sonuc, parmak)


def _rapora_isle(setup: str, sonuc: dict, parmak: str) -> None:
    """Arka planda BİTEN ölçümü rapora işler. Çağıran tur çoktan döndü, yani raporu O yazdı; bu
    yüzden dosya KİLİT ALTINDA oku-değiştir-yaz ile güncellenir (kayıp-güncelleme imkânsız).
    Kayıt `arka_plan` ve `bar_parmak` damgalarını taşır: sayının hangi turda ve hangi bar
    sürümüyle üretildiği okunabilir olmalıdır."""
    kayit = {**sonuc, "arka_plan": True, "bar_parmak": parmak, "olculdu_at": _simdi()}
    onceki: dict = {}

    def _degistir(doc: dict) -> bool:
        """Rapor sözlüğünün yamacı: `measurements[setup]` satırını yeni kayıtla değiştirir ve önceki
        durumu (`onceki`) yan not olarak saklar."""
        doc.setdefault("measurements", {})
        onceki["status"] = (doc["measurements"].get(setup) or {}).get("status")
        doc["measurements"][setup] = kayit
        return True

    try:
        store.update_json(REPORT_FILE, _degistir, {})
    except Exception as e:
        # YASA 4: burada sessiz kalmak, SAATLERCE koşmuş bir ölçümün sonucunu yok etmek olurdu ve
        # rapor "olculemedi" damgasında donardı — yani hesap yapıldı ama kimse öğrenemedi.
        obs.warn("arming_arka_plan_yazilamadi", setup=setup, error=f"{type(e).__name__}: {e}",
                 status=str(sonuc.get("status")),
                 detail="tavanı aşıp arka planda biten arming ölçümü rapora İŞLENEMEDİ")
        return
    obs.log("arming_arka_plan_bitti", setup=setup, status=str(sonuc.get("status")),
            bar_parmak=parmak,
            detail="süre tavanı aşıldığı için devredilen ölçüm arka planda tamamlandı ve rapora işlendi")
    if kayit.get("status") == "gate_passed" and onceki.get("status") != "gate_passed":
        obs.alarm("ARMING_READY", f"uyuyan kurulum kapıyı GEÇTİ: {setup} — silahlanma operatör onayı bekliyor",
                  setup=setup, p=kayit.get("search_p"))


def _ucus_setup() -> str | None:
    """Şu an arka planda ölçülen kurulum (yoksa None). TEK UÇUŞ kuralı: ikinci bir ölçüm
    başlatmak, canlıda 30+ dakikalık İKİ walk'ı aynı anda koşturmak demektir — asılmayı
    çözerken CPU'yu ikiye bölmek, düzeltmeyi kendi kusuruna çevirirdi."""
    with _UCUS_KILIT:
        u = _UCUS.get("slot")
        if not u:
            return None
        return None if u["kutu"].get("bitti") else str(u["setup"])


def ucus_bekle(timeout: float | None = None) -> bool:
    """Uçuştaki ölçüm ipliğini bekle. YALNIZ testler ve elle teşhis içindir (canlı tur ASLA
    beklemez — tavanın var oluş sebebi budur). True = uçuşta iplik kalmadı."""
    with _UCUS_KILIT:
        u = _UCUS.get("slot")
    if not u:
        return True
    u["th"].join(timeout)
    return not u["th"].is_alive()


def _sureli_olc(setup: str, bars, index, kalan: float) -> dict:
    """Ölçümü AYRI bir iplikte koşturur ve en çok `kalan` saniye bekler.

    NEDEN İPLİK: tavanın işe yaraması için ölçümün UÇUŞ HÂLİNDE bırakılabilmesi gerekir. Ölçümün
    içi (`reflect._wf_cached` → `backtest.walk_forward` → `replay`) tek bir uzun çağrıdır ve bu
    turda `backtest/strategy/scheduler` AÇILMADI — yani işbirlikçi bir iptal noktası koyacak
    yüzey yok. `signal.setitimer` de kullanılamaz: zamanlayıcı ANA İPLİKTE koşmuyor. Geriye tek
    dürüst seçenek kalır: turu serbest bırak, hesabı bırakma."""
    kutu: dict = {}
    parmak = _bar_parmak(bars)
    th = threading.Thread(target=_isci, args=(setup, bars, index, kutu, parmak),
                          name=f"arming-olcum-{setup}", daemon=True)
    with _UCUS_KILIT:
        _UCUS["slot"] = {"setup": setup, "th": th, "kutu": kutu, "parmak": parmak,
                         "basladi": _simdi()}
    th.start()
    son = time.monotonic() + max(0.0, kalan)
    while th.is_alive():
        pay = son - time.monotonic()
        if pay <= 0:
            break
        th.join(min(NABIZ_ARA_S, pay))
        _nabiz(f"arming_olcum:{setup}")
    with _UCUS_KILIT:
        if kutu.get("bitti"):                      # tavan içinde bitti → ESKİ DAVRANIŞ, bit-bit
            _UCUS.pop("slot", None)
            return kutu["sonuc"]
        kutu["devredildi"] = True                  # bitmedi → hesap sürer, raporu işçi işler
    obs.warn("arming_sure_tavani_asildi", setup=setup, tavan_s=round(max(0.0, kalan), 1),
             detail="kapı ölçümü tavanı aştı — TUR DEVAM EDİYOR (daily_cycle bloke olmaz); hesap "
                    "arka planda sürüyor ve bittiğinde raporu kendisi işleyecek")
    return _olculemedi("sure_tavani_asildi", devir="arka_plan")


def evaluate(bars=None, index=None) -> dict:
    """Haftalık değerlendirme: eşiği geçen her uyuyan kurulum için kapı ölçümü. Dönen rapor
    arming_report.json'a yazılır; loop/scheduler dönüşü görmezden gelir (yalnız sinyal).

    v189: ölçüm SÜRE TAVANIYLA koşar (bkz. dosya başındaki blok). Tavan aşılırsa o kurulum
    "olculemedi" damgasını alır ve fonksiyon DÖNER — çağıran turun geri kalanı (özellikle
    `daily_cycle`) sıraya girer."""
    rep = setup_report()
    out = {"checked_at": store.read_json("heartbeat.json", {}).get("ts"),
           "cf_report": rep, "measurements": {}, "tavan_s": _tavan_s(),
           "rule": f"cf n>={MIN_CF_ENTERED} ve ort.R>{MIN_CF_AVG_R} → kapı ölçümü; silahlanma operatör onayı"}
    eligible = [s for s in _dormant_setups()
                if rep.get(s, {}).get("n", 0) >= MIN_CF_ENTERED
                and rep.get(s, {}).get("avg_r", -1) > MIN_CF_AVG_R]
    prev = store.read_json(REPORT_FILE, {})
    son = time.monotonic() + _tavan_s()            # TAVAN TÜM TURA aittir, ölçüm BAŞINA değil
    for setup in eligible:
        ucus = _ucus_setup()
        if ucus is not None:
            out["measurements"][setup] = _olculemedi(
                "onceki_tur_arka_planda", arka_plandaki=ucus)
            continue
        kalan = son - time.monotonic()
        if kalan <= 0:
            out["measurements"][setup] = _olculemedi("tur_tavani_doldu")
            continue
        out["measurements"][setup] = _sureli_olc(setup, bars, index, kalan)
    # eşiği geçemeyenlerin durumu da dürüstçe raporda (neden ölçülmedi görünür olsun).
    # v301: "birikiyor" ile "birikemez" AYRI cümleler — seçim `_kanit_durumu`da.
    for setup in _dormant_setups():
        if setup not in out["measurements"]:
            out["measurements"][setup] = _kanit_durumu(setup, rep.get(setup, {}))
    store.write_json(REPORT_FILE, out)
    for setup, m in out["measurements"].items():
        if m.get("status") == "gate_passed" and (prev.get("measurements", {}).get(setup) or {}).get("status") != "gate_passed":
            obs.alarm("ARMING_READY", f"uyuyan kurulum kapıyı GEÇTİ: {setup} — silahlanma operatör onayı bekliyor",
                      setup=setup, p=m.get("search_p"))
    return out


def _measure(setup: str, bars=None, index=None) -> dict:
    """Kapı ölçümü: incumbent vs (+setup silahlı) — üretim pencereleri, mevcut yasa, K=1.
    entry.armed_extra param kanalıyla; global duruma dokunulmaz."""
    from . import reflect, dataset
    from .oos_pipeline import OutOfSamplePipeline
    if bars is None or index is None:
        bars, index = dataset.load(use_cache=True)
    goal = config.goal()
    cur = config.load_strategy()
    params = dict(cur["params"])
    w = reflect._default_windows()
    inc = reflect._wf_cached(params, int(cur.get("version", 1)), bars, index, goal,
                             cur.get("params_by_regime"), windows=w)
    cand_params = {**params, "entry.armed_extra": [setup]}
    # ADAY WALK'I DA ÖNBELLEKTEN (v189): eskiden `backtest.walk_forward` DOĞRUDAN çağrılıyordu ve
    # sebebi kazaydı — `_wf_cached`in anahtar kurucusu `float(x)` yaptığı için `entry.armed_extra`
    # LİSTESİ TypeError fırlatırdı. Sonuç: aynı kurulumun aday walk'ı HER turda sıfırdan koşuyordu
    # (canlıda ölçülen 27-100 dk'lık turun yarısı bu). Anahtar artık sayısal olmayan değeri de
    # temsil ediyor; incumbent'la AYNI önbelleğe düşer (anahtar farkı `entry.armed_extra`dır,
    # çakışma yapısal olarak imkânsız) ve tavan aşıp arka planda biten bir hesap, bir sonraki
    # turda YENİDEN yapılmaz.
    cand = reflect._wf_cached(cand_params, int(cur.get("version", 1)), bars, index, goal,
                              cur.get("params_by_regime"), windows=w)
    passes, gate, why = reflect._gate_eval(inc, cand, k_probes=1)
    # ÖLÇÜLEMEDİ ≠ REDDEDİLDİ (canlıda yakalandı):
    # momentum_burst raporda "gate_rejected" görünüyordu ama gerekçe "candidate OOS score undefined
    # (below min_sample)" idi; yani kapı ölçüm YAPAMAMIŞTI. Bu, "denedik ve kaybetti" diye okunuyor,
    # kurulumu haksızca gömüyor ve "neden hâlâ uyuyor" sorusunu yanlış cevaplıyordu.
    undefined = (gate.get("incumbent_oos") is None or gate.get("candidate_oos") is None
                 or gate.get("search_p") is None)
    status = "gate_passed" if passes else ("gate_undefined" if undefined else "gate_rejected")
    result = {"status": status,
              "search_p": gate.get("search_p"), "p_required": gate.get("search_p_required"),
              "incumbent_oos": gate.get("incumbent_oos"), "candidate_oos": gate.get("candidate_oos"),
              "fold_wins": gate.get("fold_wins"), "why": why or None}
    if passes:                                              # onay yürüyüşü de aynen (arama iyimserliği kırpılır)
        pipe = OutOfSamplePipeline(goal)
        conf = pipe.confirm(inc, cand)
        result["confirm_p"] = conf.p
        if not conf.passes:
            result["status"] = "gate_rejected_confirmation"
            result["why"] = conf.why
    obs.log("arming_measured", setup=setup, **{k: v for k, v in result.items() if k != "why"})
    return result
