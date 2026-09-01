"""nous_eval.py — NOUS SİSTEM-DEĞERLENDİRME KATMANI: telemetriden kanıt-atıflı iyileştirme önerileri.

SORUN. Hermes bugüne kadar tek bir soruyu soruyordu: "hangi STRATEJİ PARAMETRESİNİ oynatayım?" —
bounds.yaml'ın düğmeleri içinde, aynı ailelerde dönerek. Oysa iyileştirilebilir yüzey çok daha
büyük: kapı kalibrasyonu, veto dağılımı, skill atıfları, ölçülmeyen mekanizmalar, kopuk kablolar,
boş defterler. Bunlar "hipotez" biçimine sığmadığı için hiç önerilmiyordu; sistem kendi kısıtlı
alanının içinde optimize ediyordu.

ÇÖZÜM — DÖRT KATMAN:
  A) TELEMETRİ PAKETİ (`analytics.system_telemetry`) — hepsi MEVCUT üreticilerden; yeni ölçüm
     İCAT EDİLMEZ, "ölçülemedi" dürüstçe taşınır.
  B) MEKANİZMA DEĞERLENDİRMESİ (bu modül; `haftalik_degerlendirme`) — paket + görev şablonu,
     hermes'in yerleşik beyin zinciriyle (`hermes.chain_text`). Çıktı ZORUNLU_ALANLAR şemasıdır
     (`ayristir`) ve KANIT ATIFI olmayan öneri DÜŞÜRÜLÜR (`kanit_jetonlari`/`kanit_atifi`: atıf,
     pakette GERÇEKTEN bulunan alan adı ya da sayıdır). Düşme sayısı ve nedeni kaydedilir.
  C) KÖPRÜ (`koprule`) — `sekil="parametre"`, bounds-içi ve guard-doğrulanabilir öneriler otomatik
     `composite_queue`ya düşer. AYRI BÜTÇE AÇILMAZ: haftalık 3'lük yoklama bütçesine tabidir; bütçe
     doluysa öneri SIRADAKİ HAFTAYA DEVREDER ve devir GÖRÜNÜR (sessiz kuyruk = çöplük).
  D) ANAYASAL KORUMA — çekirdek HAKKINDAKİ öneri (CORE_FILES/CORE_CONCEPTS: kapı yasaları, guard,
     PROTECTED, risk vetoları) YALNIZ rapora gider. Kuyruk yolu YAPISAL olarak imkânsızdır: kuyruğa
     yazan TEK fonksiyon `_kuyruga_yaz`tır, ilk satırı şekil denetimidir ve çekirdek-şekilli deneme
     SESSİZCE DÜŞMEZ — `CekirdekIhlali` fırlatır, AUTHORITY_CHANGE alarmı basar.

`boru()` haftalık koşunun sonunda üç şekli üç yola bağlar: parametre → Katman C kuyruğu, tasarim →
fiş (`nous_fisler.json` + olay; otomatik uygulama yolu YOK), cekirdek_hakkinda → adlı red olayı
(istisnasız — istisna, köprünün yanlış yönlendirmesinin işaretidir). Şekil beynin beyanına
güvenmez: `sekil_sinifla` şekli KODDA yeniden türetir ve muhafazakâr yönde ezer (fazla-sınıflama
bir hafta geciktirir, az-sınıflama anayasayı deler).

YASA: HÂKİM KENDİ YASASINI YAZAMAZ — modül hiçbir şeyi UYGULAMAZ; ship yolu yine kapı + operatördür
ve tek-değişken yasası yerindedir. Çekirdek hakkında KONUŞABİLİR ama çekirdeği DEĞİŞTİREMEZ.
OKUR: telemetri paketi, bounds.yaml, önceki koşular/akıbetler. YAZAR: improvement_proposals.jsonl,
nous_eval_runs.json, nous_fisler.json (+ olay defteri).
"""
from __future__ import annotations

import datetime as dt
import json

from . import mukerrerlik, obs, store

PROPOSALS_FILE = "improvement_proposals.jsonl"
RUNS_FILE = "nous_eval_runs.json"

# ---- KÜNYE BEYANLARI (WP7-40) ------------------------------------------------------------------
# `hermes.chain_text` künyeyi ÜÇ beyanla birlikte döndürür (`model_kaynagi` · `model_olculemedi` ·
# `model_istenen`, bkz. hermes.py künye sözleşmesi bloğu) ve bu modül o zincirin TEK üretim
# tüketicisidir. Beyanlar burada okunmazsa fonksiyon dönüşünde ölür: iki kalıcı defter
# (`nous_eval_runs.json` · `improvement_proposals.jsonl`) yalnız çıplak `model` alanını taşır ve
# çıplak alan "cevap veren mi, istenen mi?" sorusunu CEVAPLAYAMAZ — v245 künye kusurunun deftere
# düşen hâli tam buydu. AŞAĞIDAKİ İKİ SABİT künyenin ölçülemediği iki YOLU adıyla ayırır; ikisi de
# UYDURMA YASAĞININ gereği: ad yoksa alan None kalır ve NEDENİ yanında durur, `active_model()`
# (= yapılandırma = "istenen") künye alanına SESSİZCE yazılmaz.
KUNYE_ZINCIR_CAGRILMADI = ("cevap veren model ölçülemedi: metin ENJEKTE edildi, beyin zinciri hiç "
                           "çağrılmadı (kuru koşum / tekrar-ayrıştırma yolu)")
KUNYE_BEYANSIZ_DONUS = ("cevap veren model ölçülemedi: zincir dönüşü künye için neden BEYAN "
                        "ETMEDİ (eski sözleşme ya da beyansız sarmalayıcı) — ad uydurulmaz")

# ---- ÇIKTI SÖZLEŞMESİ -------------------------------------------------------------------------
# ZORUNLU alanlar: eksik alan taşıyan öneri DÜŞER. Neden zorunlu oldukları tek tek bir karardır:
#   alan            — hangi mekanizma? (öneri adressiz olamaz)
#   gozlem          — KANIT ATIFI burada durur: telemetrideki HANGİ sayı/alan bunu söylüyor
#   oneri           — ne yapılsın
#   beklenen_etki   — falsifiye edilebilir bir iddia (yoksa öneri ölçülemez)
#   onerilen_olcum  — nasıl ölçülür (yoksa öneri "iyi hissettiren bir cümle" olarak kalır)
#   oncelik         — sıralanamayan bir liste, tüketilemeyen bir listedir
#   sekil           — hangi yola gider (kuyruk / rapor / anayasal rapor)
ZORUNLU_ALANLAR: tuple[str, ...] = ("alan", "gozlem", "oneri", "beklenen_etki", "onerilen_olcum",
                                    "oncelik", "sekil")
ONCELIKLER: tuple[str, ...] = ("yuksek", "orta", "dusuk")
SEKILLER: tuple[str, ...] = ("parametre", "tasarim", "cekirdek_hakkinda")

# ---- KATMAN D: ÇEKİRDEK — ADLANDIRILMIŞ SABİT --------------------------------------------------
# "Anayasal çekirdek nous'a KAPALI" cümlesi, çekirdeğin NE OLDUĞU yazılı olmadıkça uygulanamaz bir
# temenniydi. Liste burada, TEK yerde durur ve testi vardır.
#
# DOSYALAR: kapı yasasının, risk zarfının ve doğrulama eşiklerinin YAŞADIĞI dosyalar.
CORE_FILES: tuple[str, ...] = (
    "guard.py", "probgate.py", "reflect.py", "validation.py", "codelaw.py", "prescreen.py",
    "shadowlaw.py", "goal.yaml",
)
# KAVRAMLAR: bir öneri metninde göründüğünde önerinin ÇEKİRDEK HAKKINDA olduğunu gösteren imzalar.
# Küçük harfe indirilmiş ALT DİZE olarak aranır. Liste bilinçli olarak GENİŞ tutulmuştur (bkz.
# modül başlığındaki muhafazakârlık gerekçesi): "veto" gibi bir kelime bir parametre önerisini de
# çekirdek-hakkında yapar, ve bu DOĞRU sonuçtur — risk vetoları anayasadır.
CORE_CONCEPTS: tuple[str, ...] = (
    "guard", "protected", "veto", "kapı yasası", "kapi yasasi", "gate_law", "kapı kanunu",
    "passes semanti", "autonomy_level", "one_variable_only", "tek-değişken", "tek degisken",
    "risk zarfı", "risk zarfi", "gate_margin", "tail_margin", "dsr_hard", "pbo_hard",
    "min_sample", "embargo", "limits bloğu", "limits blogu", "fail-closed", "sert kapı",
    "sert kapi", "hard-gate", "hard gate", "goal.yaml", "kapı eşiği", "kapi esigi",
)

# Kanıt atıfı sayılMAYAN alan adları: her bölümde geçen genel anahtarlar. Bunları saymak, "beyan"
# kelimesini içeren boş bir cümleyi kanıtlı sanmak olurdu — kapı kendi kendini geçersiz kılardı.
_JENERIK_ADLAR = frozenset({
    "beyan", "durum", "neden", "rol", "hafta", "note", "value", "esik", "kaynak", "status",
    "hukum", "detail", "label", "birim", "tarih", "uretildi", "bolumler", "bolum_adlari",
})
_JETON_MIN_AD = 5          # bundan kısa alan adı atıf sayılmaz (n, ok, ts... ayırt edici değil)
_JETON_MIN_SAYI = 3        # "3 kez" her metinde var; ayırt edici sayı en az 3 karakterdir
# TEK KELİMELİK ALAN ADI İÇİN AYRI, DAHA YÜKSEK EŞİK. İlk test koşusunda yakalandı: `genel`
# (profit_waterfall'ın gerçek bir alanı) "sistem GENEL olarak iyi görünüyor" cümlesini KANITLI saydı
# ve kapı kendi kendini geçersiz kıldı — atıfsız bir öneri, tek bir yaygın Türkçe kelime yüzünden
# geçti. Bu depodaki gerçek ölçüm adları neredeyse her zaman BİLEŞİKTİR (`net_r`, `sinyal_mfe_r`,
# `n_plan`, `olu_aileler`); alt çizgisi olmayan kısa bir kelime bir ölçümü ADRESLEMİYOR demektir.
_AD_TEK_KELIME_MIN = 9


def _ayirt_edici_ad(ad: str) -> bool:
    """Bu alan adı bir ölçümü ADRESLİYOR mu? (bkz. `_AD_TEK_KELIME_MIN` notu)"""
    if ad in _JENERIK_ADLAR or len(ad) < _JETON_MIN_AD:
        return False
    return "_" in ad or len(ad) >= _AD_TEK_KELIME_MIN


class CekirdekIhlali(RuntimeError):
    """Çekirdek-şekilli bir öneri kuyruk yoluna sokulmaya çalışıldı.

    İSTİSNA, SESSİZ RET DEĞİL: sessizce `return` etmek, bir gün sınıflandırma bozulduğunda ihlalin
    HİÇ görünmemesi demekti. Anayasa ihlali bir istisna + alarmdır."""


# =================================================================================================
# KALİTE KAPISI: KANIT ATIFI
# =================================================================================================
def kanit_jetonlari(telemetri: dict) -> dict:
    """Telemetri paketinden ATIF YAPILABİLİR jeton kümesi: alan ADLARI + ayırt edici SAYILAR.

    "Kanıt-atıfı zorunlu" cümlesi ancak atfın DENETLENEBİLİR olmasıyla anlam kazanır. Denetim şu:
    gözlem cümlesi, pakette GERÇEKTEN bulunan bir alan adını ya da bir sayıyı içeriyor mu? İçermiyorsa
    o cümle pakete değil MODELİN HAFIZASINA dayanıyor demektir — ve bu sistemde uydurma bir sayıya
    dayanan bir öneri, önerinin en pahalı türüdür (ölçüm bütçesi yakar, hiçbir şey öğretmez)."""
    adlar: set[str] = set()
    sayilar: set[str] = set()

    def _gez(x, derinlik: int = 0):
        """Telemetri ağacında özyinelemeli gezinir: ayırt edici alan ADLARINI `adlar`a, yeterince uzun
        sayı yazımlarını `sayilar`a toplar. Derinlik 8'de durur (derin/döngüsel yapıya karşı).
        """
        if derinlik > 8:
            return
        if isinstance(x, dict):
            for k, v in x.items():
                ks = str(k).lower()
                if _ayirt_edici_ad(ks):
                    adlar.add(ks)
                _gez(v, derinlik + 1)
        elif isinstance(x, (list, tuple)):
            for v in x:
                _gez(v, derinlik + 1)
        elif isinstance(x, bool):
            return                                  # True/False atıf değildir
        elif isinstance(x, (int, float)):
            for s in _sayi_bicimleri(float(x)):
                if len(s.lstrip("-")) >= _JETON_MIN_SAYI:
                    sayilar.add(s)
        elif isinstance(x, str) and len(x) >= _JETON_MIN_AD:
            # Metin içindeki ALAN ADLARI da atıf yapılabilir (ör. `hic_onerilmemis_dugmeler`
            # listesindeki knob adları, `olculemeyenler` listesindeki bölüm adları).
            if x.replace("_", "").isalnum() and "_" in x:
                adlar.add(x.lower())
    _gez(telemetri)
    return {"adlar": adlar, "sayilar": sayilar}


def _sayi_bicimleri(v: float) -> list[str]:
    """Bir sayının prompt'ta görünebilecek yazımları. Model 0.3528'i "0.353" diye anar; tek biçim
    aramak atıfların çoğunu kaçırırdı (ve kapı, dürüst öneriyi düşürürdü)."""
    out = []
    if v == int(v) and abs(v) < 1e15:
        out.append(str(int(v)))
    for basamak in (2, 3, 4):
        out.append(f"{v:.{basamak}f}")
    out.append(repr(v))
    return out


def kanit_atifi(gozlem: str, jetonlar: dict) -> list[str]:
    """Gözlemin telemetriye yaptığı atıflar (boş liste = ATIFSIZ → öneri düşer)."""
    g = str(gozlem or "").lower()
    if not g:
        return []
    bulunan = [a for a in jetonlar.get("adlar", ()) if a in g]
    bulunan += [f"sayı:{s}" for s in jetonlar.get("sayilar", ()) if s in g]
    # UZUN ADLAR ÖNCE: `n_olculemedi` ile `olculemedi` birlikte eşleşirse rapor okunmaz olur.
    bulunan.sort(key=lambda s: (-len(s), s))
    return bulunan[:6]


# =================================================================================================
# KATMAN D: ŞEKİL SINIFLANDIRMASI (BEYNİN ETİKETİNE GÜVENMEZ)
# =================================================================================================
def cekirdek_isaretleri(oneri: dict) -> list[str]:
    """Önerinin metninde çekirdek imzaları. Boş liste = çekirdek HAKKINDA değil."""
    parcalar = [str(oneri.get(k) or "") for k in
                ("alan", "gozlem", "oneri", "beklenen_etki", "onerilen_olcum")]
    parcalar += [str(k) for k in (oneri.get("parametreler") or {})]
    metin = " ".join(parcalar).lower()
    isaretler = [d for d in CORE_FILES if d.lower() in metin]
    isaretler += [c for c in CORE_CONCEPTS if c in metin]
    return sorted(set(isaretler))


def sekil_sinifla(oneri: dict) -> tuple[str, list[str]]:
    """ŞEKLİ KODDA YENİDEN TÜRET. Dönüş: (sekil, çekirdek işaretleri).

    SIRA ÖNEMLİ: çekirdek denetimi ÖNCE gelir ve modelin `sekil` beyanını EZER. Tersi olsaydı
    "sekil=parametre" yazan bir model, kapı yasası hakkındaki bir öneriyi kuyruğa sokabilirdi —
    yani hâkim kendi yasasını, üstüne yanlış bir etiket koyarak yazardı."""
    isaretler = cekirdek_isaretleri(oneri)
    if isaretler:
        return "cekirdek_hakkinda", isaretler
    beyan = str(oneri.get("sekil") or "").strip().lower()
    if beyan == "parametre":
        return "parametre", []
    # Bilinmeyen/eksik etiket `tasarim`a düşer: kuyruk yolu OLMAYAN, en zararsız kova.
    return ("cekirdek_hakkinda" if beyan == "cekirdek_hakkinda" else "tasarim"), []


# =================================================================================================
# KATMAN B: AYRIŞTIRMA + KALİTE KAPISI
# =================================================================================================
def ayristir(text: str, telemetri: dict) -> dict:
    """Beynin metnini önerilere çevir ve KALİTE KAPISINDAN geçir.

    DÜŞME SAYISI VE NEDENİ KAYDA GEÇER. "Beyin bu hafta 4 öneri üretti" ile "9 üretti, 5'i
    kanıt-atıfsız düştü" aynı görünmemelidir: ikincisi beynin karnesi hakkında birincisinden çok
    daha fazla şey söyler ve H1 deseninin (kendi isabetini görmek) mekanizma-düzeyi ikizidir."""
    from . import hermes
    out: dict = {"kabul": [], "n_uretilen": 0, "n_dusen": 0, "dusme_nedenleri": {},
                 "dusenler": [], "durum": "ayristirildi"}
    ham = (text or "").strip()
    if not ham:
        out["durum"] = "cevap_yok"
        return out
    try:
        data = json.loads(hermes._extract_json(ham))
    except (json.JSONDecodeError, ValueError):
        try:
            data = json.loads(hermes._unwrap_strings(hermes._extract_json(ham)))
        except (json.JSONDecodeError, ValueError):
            # AYRIŞTIRILAMAYAN CEVAP: tek tek öneri sayılamaz, o yüzden `n_dusen` ÖNERİ sayısı
            # DEĞİL koşu durumudur. İkisini karıştırmak "0 öneri düştü" yalanını üretirdi.
            out["durum"] = "ayristirilamadi"
            out["dusme_nedenleri"]["cevap_ayristirilamadi"] = 1
            obs.warn("nous_eval_unparseable", uzunluk=len(ham), bas=ham[:200])
            return out
    kalem = data.get("oneriler") if isinstance(data, dict) else data
    if not isinstance(kalem, list):
        out["durum"] = "ayristirilamadi"
        out["dusme_nedenleri"]["oneriler_listesi_yok"] = 1
        return out
    out["n_uretilen"] = len(kalem)
    jetonlar = kanit_jetonlari(telemetri)
    bolumler = set((telemetri or {}).get("bolum_adlari") or ())

    def _dus(neden: str, oneri) -> None:
        """Bir öneriyi kalite kapısından DÜŞÜR: sayacı, neden dökümünü ve düşen satırın özetini `out`a
        yazar — düşme sessiz kalmaz, koşu kaydında sayılı ve gerekçeli durur.
        """
        out["n_dusen"] += 1
        out["dusme_nedenleri"][neden] = out["dusme_nedenleri"].get(neden, 0) + 1
        out["dusenler"].append({"neden": neden,
                                "alan": (oneri.get("alan") if isinstance(oneri, dict) else None),
                                "bas": str(oneri)[:160]})

    for o in kalem:
        if not isinstance(o, dict):
            _dus("sozluk_degil", o)
            continue
        eksik = [k for k in ZORUNLU_ALANLAR if not str(o.get(k) or "").strip()]
        if eksik:
            _dus(f"eksik_alan:{eksik[0]}", o)
            continue
        if str(o.get("oncelik")).strip().lower() not in ONCELIKLER:
            _dus("gecersiz_oncelik", o)
            continue
        if str(o.get("sekil")).strip().lower() not in SEKILLER:
            _dus("gecersiz_sekil", o)
            continue
        atif = kanit_atifi(o.get("gozlem"), jetonlar)
        if not atif:
            # KAPININ ASIL DİŞİ. Kanıt atfı olmayan gözlem, pakete değil modelin hafızasına dayanır.
            _dus("kanit_atifsiz", o)
            continue
        sekil, isaretler = sekil_sinifla(o)
        out["kabul"].append({
            "alan": str(o.get("alan")).strip()[:120],
            "gozlem": str(o.get("gozlem")).strip()[:900],
            "oneri": str(o.get("oneri")).strip()[:900],
            "beklenen_etki": str(o.get("beklenen_etki")).strip()[:500],
            "onerilen_olcum": str(o.get("onerilen_olcum")).strip()[:500],
            "oncelik": str(o.get("oncelik")).strip().lower(),
            "sekil": sekil,
            "sekil_beyan": str(o.get("sekil")).strip().lower(),
            "cekirdek_isaretleri": isaretler,
            "kanit_atifi": atif,
            "alan_bilinen": str(o.get("alan")).strip() in bolumler,
            "parametreler": ({str(k): v for k, v in (o.get("parametreler") or {}).items()}
                             if isinstance(o.get("parametreler"), dict) else None),
        })
    return out


# =================================================================================================
# KATMAN C: KÖPRÜ (parametre → composite_queue, H4 BÜTÇESİ İÇİNDE)
# =================================================================================================
def _kuyruga_yaz(oneri: dict, *, bounds: dict | None = None) -> dict:
    """KUYRUĞA YAZAN TEK FONKSİYON — Katman D'nin yapısal çivisi.

    Modülde `hermes_composite.enqueue` çağrısı YALNIZ burada bulunur (AST testi bunu doğrular) ve
    fonksiyonun İLK işi şekil denetimidir. Böylece "çekirdek-şekilli öneri kuyruğa yazılamaz" bir
    davranış kuralı değil YAPISAL bir olgudur: kuyruğa giden başka bir yol yoktur.

    Çekirdek denemesi SESSİZCE DÜŞMEZ: alarm + istisna. Sessiz ret, sınıflandırma bir gün bozulduğunda
    ihlalin hiç görünmemesi demekti — ve görünmeyen bir anayasa ihlali, olmayan bir anayasadır."""
    sekil, isaretler = sekil_sinifla(oneri)
    if sekil != "parametre":
        obs.alarm(obs.ALARM_AUTHORITY,
                  f"ÇEKİRDEK-ŞEKİLLİ ÖNERİ KUYRUĞA SOKULMAYA ÇALIŞILDI (sekil={sekil})",
                  alan=str(oneri.get("alan"))[:120], sekil=sekil,
                  sekil_beyan=str(oneri.get("sekil"))[:40], cekirdek_isaretleri=isaretler[:6],
                  detail=("Katman D: kapı yasaları/guard/PROTECTED/vetolar hakkındaki öneriler "
                          "YALNIZ rapora gider. Bu çağrı bir KOD HATASIDIR — nous değil, köprü "
                          "yanlış yönlendirdi."))
        raise CekirdekIhlali(f"sekil={sekil} kuyruğa yazılamaz (işaretler: {isaretler})")
    from . import config, hermes_composite
    komp = oneri.get("parametreler") or {}
    return hermes_composite.enqueue(
        komp, rationale=f"[nous_eval] {oneri.get('alan')}: {oneri.get('oneri')}"[:500],
        source="nous_eval", bounds=(bounds if bounds is not None else config.bounds()))


def koprule(kabul: list, *, yaz: bool = True, bounds: dict | None = None) -> dict:
    """Katman C: parametre-şekilli önerileri H4 BÜTÇESİ içinde kuyruğa koy; fazlasını DEVRET.

    AYRI BÜTÇE AÇILMAZ. Kuyruğa giren her satır bir gün bir prescreen ölçümü olur, o ölçüm aşınma
    defterine ve DSR paydasına N olarak girer. `nous_eval` kendine ayrı bir bütçe açsaydı, H4'ün
    "sınırsız otomatik yoklama deflasyonu şişirir" emniyeti ikinci bir kapıdan delinirdi — ve bu
    tam olarak kapının kendi eliyle imkânsızlaştırılması olurdu.

    DEVİR GÖRÜNÜR. Bütçe dolduğunda öneri sessizce kaybolmaz: `kuyruk="devredildi"` damgası alır,
    koşu kaydında `devreden` listesine girer ve pano kartında sayılır. Sessiz bir kuyruk, kuyruk
    değil çöplüktür (`skill_revisions.json` dersinin tersi)."""
    from . import hermes_composite
    durum = hermes_composite.queue_status(store.read_jsonl("composite_queue.jsonl"))
    # BEKLEYEN SATIRLAR BÜTÇEYİ ÖNCE TALEP EDER: kuyrukta 3 pending varsa bu haftanın 3 yoklaması
    # zaten sözlüdür ve yeni bir satır eklemek kuyruğu şişirir, ölçüm hızını artırmaz.
    kalan = max(0, int(durum.get("butce_kalan") or 0) - int(durum.get("n_bekleyen") or 0))
    out = {"n_parametre": 0, "kuyruga_giren": [], "devreden": [], "sekil_disi": [],
           "butce_kalan_baslangic": durum.get("butce_kalan"),
           "n_bekleyen_onceden": durum.get("n_bekleyen"),
           "haftalik_butce": durum.get("haftalik_butce"), "slot": kalan, "yazildi": bool(yaz)}
    for o in kabul:
        # ŞEKİL BURADA DA YENİDEN TÜRETİLİR — `o["sekil"]` alanına GÜVENİLMEZ. İlk test koşusunda
        # yakalandı ve gerçek bir tasarım hatasıydı: süzgeç `ayristir`ın çoktan düzelttiği alanı
        # okuyordu, ama `koprule` DIŞARIDAN da çağrılabilir (CLI, elle kurulmuş öneri, gelecekteki
        # bir çağıran) ve o hâlde alan hâlâ MODELİN etiketiydi. `_kuyruga_yaz` ihlali yakalayıp
        # alarm bastı — yani anayasa delinmedi — ama `n_parametre` sayacı YALAN söylemişti
        # ("1 parametre önerisi geldi", oysa çekirdek önerisiydi). Modülün kendi sözleşmesi
        # "beynin etiketine güvenilmez" diyorsa, o sözleşme TEK bir yerde değil HER yerde geçerlidir.
        sekil, isaretler = sekil_sinifla(o)
        if sekil != o.get("sekil"):
            o["sekil"], o["cekirdek_isaretleri"] = sekil, isaretler
        if sekil != "parametre":
            continue                        # tasarım/çekirdek: kuyruk yolu YOK (Katman D)
        out["n_parametre"] += 1
        komp = o.get("parametreler") or {}
        ok, nedenler = hermes_composite.validate_composite(komp, bounds if bounds is not None
                                                           else _bounds())
        if not ok:
            # ŞEKİL DENETİMİNDEN GEÇMEYEN ÖNERİ DÜŞMEZ, RAPORDA KALIR: fikrin kendisi bilgidir
            # (H3'ün kuruluş gerekçesi). Yalnız KUYRUK yolu kapanır ve nedeni yazılır.
            o["kuyruk"], o["kuyruk_neden"] = "hayir", nedenler[:4]
            out["sekil_disi"].append({"alan": o.get("alan"), "nedenler": nedenler[:4]})
            continue
        if len(out["kuyruga_giren"]) >= kalan:
            o["kuyruk"] = "devredildi"
            o["kuyruk_neden"] = [f"H4 haftalık yoklama bütçesi ({durum.get('haftalik_butce')}) "
                                 f"bu hafta dolu — SIRADAKİ haftaya devredildi"]
            out["devreden"].append({"alan": o.get("alan"), "parametreler": komp})
            continue
        if not yaz:
            o["kuyruk"], o["kuyruk_neden"] = "kuru_kosum", ["yaz=False — kuyruğa YAZILMADI"]
            out["kuyruga_giren"].append({"alan": o.get("alan"), "id": None, "parametreler": komp})
            continue
        try:
            sonuc = _kuyruga_yaz(o, bounds=bounds)
        except CekirdekIhlali as e:
            # BURAYA DÜŞMEK BİR KOD HATASIDIR (üstteki `sekil != parametre` süzgeci onu almalıydı) —
            # ama ikinci zarf kaldırılmaz: alarm zaten basıldı, öneri rapora düşer.
            o["kuyruk"], o["kuyruk_neden"] = "hayir", [f"KATMAN D: {e}"]
            continue
        o["kuyruk"] = "evet" if sonuc.get("queued") else "hayir"
        o["kuyruk_id"] = ((sonuc.get("row") or {}).get("id"))
        o["kuyruk_neden"] = sonuc.get("reasons") or []
        out["kuyruga_giren"].append({"alan": o.get("alan"), "id": o["kuyruk_id"],
                                     "parametreler": komp})
    return out


def _bounds() -> dict:
    """Bounds sözleşmesini config'ten okur; yoksa boş sözlük döner (salt okuma)."""
    from . import config
    return config.bounds() or {}


# =================================================================================================
# OTOMATİK YÖNLENDİRME BORUSU (operatör: "öneriler duruyor, kimse işlemiyor")
# =================================================================================================
# ÖLÇÜLEN KUSUR (canlı defter, 2026-W32): üç öneri kabul edildi, ÜÇÜ DE `sekil="tasarim"`, ÜÇÜNÜN DE
# `kuyruk="yol_yok"`. Yani kalite kapısı çalıştı, defter yazıldı, pano gösterdi — ve sonra HİÇBİR ŞEY
# olmadı. Katman C yalnız `parametre` şeklini taşıyordu; diğer iki şekil için "yol yok" bir DURUM
# etiketi değil bir ÇIKMAZ sokaktı: öneri deftere düşüyor, hiçbir kuyruğa girmiyor, hiçbir olay
# üretmiyor, operatörün önüne bir iş kalemi olarak ÇIKMIYOR. `skill_revisions.json` dersinin aynısı:
# sessiz bir kuyruk kuyruk değil çöplüktür.
#
# BORU ÜÇ SINIFI DA BİR YOLA BAĞLAR — ve üçü AYRI yollardır (tek yola katlamak Katman D'yi silerdi):
#   (a) parametre        → hermes composite kuyruğu. YENİ KOD YOK: yolu `koprule`/`_kuyruga_yaz`
#                          zaten kuruyor (kapı hakem, H4 bütçesi içinde, elle ağırlık YAZILMAZ).
#                          Boru burada yalnız SONUCU okur ve sayar — ikinci bir enqueue çağrısı
#                          aynı öneriyi iki ölçüm sırasına sokardı.
#   (b) tasarim          → FİŞ. Kod/doküman/mimari önerisinin otomatik uygulama yolu YOKTUR ve
#                          olmamalıdır; ama "yol yok" ile "operatörün kuyruğunda" arasında dağlar
#                          kadar fark var. Fiş = görünür iş kalemi: `nous_fisler.json` + olay.
#                          FİŞ, GÖZLEM BAŞINA TEKİLDİR (öneri başına değil): aynı alanın her
#                          koşudaki yeniden bildirimi yeni satır açmaz, mevcut fişin sayacını
#                          artırır — tekrar KAYBOLMAZ, kuyruğu ŞİŞİRMEZ (bkz. `_alan_anahtari`).
#   (c) cekirdek_hakkinda→ ANAYASAL RED. `CekirdekIhlali` FIRLATILMAZ ve ALARM BASILMAZ: o istisna
#                          bir KOD HATASININ (köprünün yanlış yönlendirmesinin) işaretidir — burada
#                          ise sistem DOĞRU çalışıyor, yalnızca sınıf kapalı. Anayasanın normal
#                          işleyişini alarm diye raporlamak, alarm-yorgunluğu
#                          kusurunun ta kendisi olurdu. Sade bir olay yazılır; docstring'in Katman-D
#                          sözü (kuyruk yolu YAPISAL olarak kapalı) DEĞİŞMEDEN durur.
#
# OTOMATİK UYGULAMA (c) SINIFINA ASLA DOKUNMAZ: boru hiçbir sınıf için kod/parametre UYGULAMAZ —
# en fazla yaptığı şey bir kalemi görünür bir kuyruğa koymaktır. `hermes_composite.enqueue` çağrısı
# bu modülde HÂLÂ yalnız `_kuyruga_yaz` içindedir (AST çivisi) ve boru onu ÇAĞIRMAZ.
FISLER_FILE = "nous_fisler.json"

OLAY_FIS = "nous_oneri_fisi"
OLAY_RED_ANAYASAL = "nous_oneri_red_anayasal"

YOL_KUYRUK = "hermes_kuyrugu"       # (a) bounds-içi düğme → composite_queue (gölge/prescreen ölçümü)
YOL_FIS = "fis"                     # (b) kod/doküman/mimari → operatör kuyruğu
YOL_RED = "anayasal_red"            # (c) CORE/Katman-D → yalnız rapor


# ---- FİŞ TEKİLLEŞTİRME: KİMLİK ÖNERİ DEĞİL, GÖZLEMİN ADRESİDİR ---------------------------------
# ÖLÇÜLEN KUSUR (canlı `nous_fisler.json`): defterde 12 fiş vardı ama DÖRT gerçek kalem —
# `backtest_full.avg_r eksik` üç kez, `tahmin_isabeti n=1` üç kez, `hotstate surec_ici_sayac null`
# iki kez fişlenmişti. KÖK NEDEN: tekilleştirme ÖNERİ KİMLİĞİ (`anahtar` = N00007) üzerinden
# çalışıyordu; oysa beyin her haftalık koşuda AYNI gözlem için YENİ bir öneri satırı üretiyor ve
# `_oneri_kaydet` ona YENİ bir id veriyor. Yani anahtar her hafta değişiyordu ve "aynı öneri iki fiş
# üretmez" kapısı HİÇ kapanmıyordu. Bedeli iki katmanlıydı: kuyruk üç kat şişik görünüyordu
# (operatör "12 açık iş" sanıyordu, gerçek dört) ve tekrarlar önceliği bozuyordu — tek bir sorun üç
# YÜKSEK satır üretiyordu.
#
# FİŞİN KİMLİĞİ ARTIK GÖZLEMİN ADRESİDİR (`alan`). BU BİR SUSTURMA DEĞİL BİR TEKİLLEŞTİRMEDİR —
# hiçbir gözlem düşmez, yalnız aynı gözlemin N. kopyası AYRI BİR KUYRUK SATIRI olmaz:
#   · `gorulme`   — alanın kaç DİSTİNCT bildirimle görüldüğü. Tekrar bir SİNYALDİR: her koşuda
#                   yeniden görülen bir sorun, bir kez görülenden farklıdır. Sayı kaybolmaz.
#   · `tekrarlar` — katlanan her bildirimin kimliği + haftası. Kimlik `improvement_proposals.jsonl`
#                   satırının TAM metnine (gözlem/öneri/etki/ölçüm/atıf) işaret eder; kuyruk satırı
#                   bu yüzden metni ÇOĞALTMAZ. İZ BİR PENCEREDİR (`TEKRAR_TAVANI`), SAYAÇ DEĞİL:
#                   `gorulme` kırpılmaz, iz kırpılır — ikisi ayrılmazsa defter sınırsız büyürdü.
#   · baş satır   — EN YENİ bildirimi taşır (gözlem değişmiş olabilir; en yenisi kalır) ve EN AĞIR
#                   önceliği tutar (bir tekrar, açık bir kalemin önceliğini sessizce DÜŞÜREMEZ).
#   · `anahtar`   — baş satırla birlikte EN YENİ öneri kimliğine döner. Sabit kalsaydı pano kartı
#                   (`app.js`: `fis.anahtarlar` içinde önerinin id'sini arar) bu haftanın önerisine
#                   "fişlenmedi — boru bu satırı işlemedi" YANLIŞ uyarısı basardı: boru doğru
#                   çalışırken ekranda alarm görünürdü. Eski kimlikler ize düşer, kaybolmaz.
# KAPANAN FİŞ YENİDEN AÇILIR: katlama YALNIZ AÇIK satırlara bakar (`_fis_acik`). Kapanmış bir fiş
# yeni bir gözlemi yutsaydı tekilleştirme kalıcı bir susturmaya dönerdi.
TEKRAR_TAVANI = 8                   # `tekrarlar` izinde tutulan EN SON bildirim sayısı

FIS_SAYAC_KURU_KOSUM = ("kuru koşum (`yaz=False`): fiş defteri ne okundu ne yazıldı — tekrar sayacı "
                        "ÖLÇÜLEMEZ ('1' yazmak 'ölçtük, ilk kez görüldü' demek olurdu)")


def _fis_anahtari(o: dict, hafta: str) -> str:
    """Fişi BİLDİREN önerinin kimliği (N00001) — `improvement_proposals.jsonl` satırına işaret eder
    ve pano rozeti bununla eşleşir. `yaz=False` kuru koşumda id henüz atanmamış olur ve o hâlde
    hafta+alan kullanılır. TEKİLLEŞTİRME ANAHTARI BU DEĞİL `_alan_anahtari`DIR (bkz. üstteki blok):
    bu kimlik her koşuda değişir, gözlemin adresi değişmez."""
    return str(o.get("id") or f"{hafta}:{o.get('alan')}")


def _alan_anahtari(alan) -> str:
    """Fişin TEKİLLEŞTİRME kimliği: gözlemin adresi, normalize edilmiş (boşluklar sadeleşir, küçük
    harfe iner). BOŞ dönerse katlanacak bir adres YOKTUR ve eski kimlik-tekilliği yürürlükte kalır —
    adressiz bildirimleri tek kovaya yığmak, farklı gözlemleri birbirine susturmak olurdu."""
    return " ".join(str(alan or "").split()).lower()


def _fis_acik(f: dict) -> bool:
    """Fiş hâlâ açık mı? Varsayılan `api._nous_fisler` ile AYNIdır: damgasız satır AÇIK sayılır."""
    return str(f.get("durum") or "fislendi") == "fislendi"


def _bildiren_kimlikler(f: dict) -> set[str]:
    """Bu fişi bugüne kadar bildiren TÜM öneri kimlikleri (baş satır + iz penceresi)."""
    k = {str(f.get("anahtar"))}
    k.update(str(t.get("anahtar")) for t in (f.get("tekrarlar") or []) if isinstance(t, dict))
    return k


def _agir_oncelik(a, b):
    """İkisinden AĞIR olanı döner (`ONCELIKLER` sırası). Bilinmeyen değer en hafif sayılır,
    eşitlikte yeni bildirim kalır. Tekrar önceliği YÜKSELTEBİLİR, sessizce DÜŞÜREMEZ."""
    def _r(v) -> int:
        return ONCELIKLER.index(str(v)) if str(v) in ONCELIKLER else len(ONCELIKLER)
    return a if _r(a) < _r(b) else b


def _fis_ilk_kayit(s: dict) -> dict:
    """Bir fiş satırının tekrar alanlarını başlatır (ilk görülme = son görülme, sayaç 1). Mevcut
    değerlere DOKUNMAZ: katlanan eski satırlar kendi sayaçlarını korur."""
    s.setdefault("gorulme", 1)
    s.setdefault("son_gorulme", s.get("ts"))
    s.setdefault("son_hafta", s.get("hafta"))
    return s


def _fis_birlestir(f: dict, s: dict) -> None:
    """`s` bildirimini `f` fişine KATLA: eski baş ize düşer, baş satır tazelenir, sayaç artar."""
    iz = [t for t in (f.get("tekrarlar") or []) if isinstance(t, dict)]
    iz.append({"anahtar": f.get("anahtar"), "hafta": f.get("son_hafta") or f.get("hafta"),
               "ts": f.get("son_gorulme") or f.get("ts")})
    iz.extend(t for t in (s.get("tekrarlar") or []) if isinstance(t, dict))
    f["tekrarlar"] = iz[-TEKRAR_TAVANI:]
    f["gorulme"] = int(f.get("gorulme") or 1) + int(s.get("gorulme") or 1)
    f["oncelik"] = _agir_oncelik(f.get("oncelik"), s.get("oncelik"))
    # BİLDİRİM YÜKÜ BİR BÜTÜN OLARAK TAZELENİR: gözlemi yenileyip öneriyi/atfı eskide bırakmak, iki
    # AYRI bildirimden dikilmiş bir satır üretirdi ve operatör hangi metnin hangi koşudan geldiğini
    # ayırt edemezdi. Eski yükün tamamı `improvement_proposals.jsonl` satırında durmaya devam eder.
    for k in ("anahtar", "id", "gozlem", "oneri", "beklenen_etki", "onerilen_olcum", "kanit_atifi"):
        f[k] = s.get(k)
    f["son_gorulme"] = s.get("son_gorulme") or s.get("ts")
    f["son_hafta"] = s.get("son_hafta") or s.get("hafta")


def _tekillestir(fisler: list) -> tuple[list, int]:
    """DEFTERDE HÂLİHAZIRDA DURAN tekrarları katlar (yalnız AÇIK satırlar); (kalan, katlanan) döner.

    Yalnız ileriye dönük bir tekilleştirme canlıdaki 12 satırı 12 bırakırdı — kusurun ölçülen bedeli
    (operatörün gördüğü sayı) hiç değişmezdi. Katlama SIRA KORUR: hayatta kalan satır alanın İLK
    açılan fişidir, baş yükü ise en son bildirimindir."""
    kalan: list = []
    bas: dict[str, dict] = {}
    katlanan = 0
    for f in fisler:
        if not isinstance(f, dict):
            kalan.append(f)
            continue
        k = _alan_anahtari(f.get("alan"))
        if not k or not _fis_acik(f):
            kalan.append(f)                 # adressiz ya da KAPANMIŞ satıra dokunulmaz
            continue
        onceki = bas.get(k)
        if onceki is None:
            bas[k] = _fis_ilk_kayit(f)
            kalan.append(f)
            continue
        katlanan += 1
        if str(f.get("anahtar")) in _bildiren_kimlikler(onceki):
            continue                        # AYNI bildirim iki kez yazılmış: satır düşer, sayaç DEĞİL
        _fis_birlestir(onceki, _fis_ilk_kayit(f))
    return kalan, katlanan


def _fis_yaz(satirlar: list[dict]) -> dict:
    """Fişleri kuyruğa ekle — TEKİL OLAN ALANDIR, öneri kimliği DEĞİL (üstteki tekilleştirme bloğu).
    Aynı alanın ikinci bildirimi YENİ SATIR AÇMAZ: baş satır tazelenir, sayaç artar, kimlik ize düşer.

    DÖNÜŞ: {"doc", "yeni", "birlesen", "katlanan", "gorulme": {öneri kimliği → sayaç}}. Sayaç olaya
    ve boru kalemine BURADAN taşınır — okunmayan bir sayaç YASA 6 ihlalidir ve tekrar bilgisi
    kuyruğu şişirmeden görünür olmak zorundadır."""
    sonuc: dict = {"yeni": 0, "birlesen": 0, "katlanan": 0, "gorulme": {}}

    def _mut(cur):
        """Fiş defterini yerinde günceller: mevcut tekrarları katlar, her yeni bildirimi ya AÇIK bir
        fişe katlar ya da yeni satır açar, sayacı ve güncelleme damgasını tazeler.
        `store.update_json` çağrısının değiştiricisi.
        """
        if not isinstance(cur.get("fisler"), list):
            cur["fisler"] = []
        cur["fisler"], sonuc["katlanan"] = _tekillestir(cur["fisler"])
        acik: dict[str, dict] = {}
        kimlikler: set[str] = set()
        for f in cur["fisler"]:
            if not isinstance(f, dict) or not _fis_acik(f):
                continue
            kimlikler |= _bildiren_kimlikler(f)
            k = _alan_anahtari(f.get("alan"))
            if k:
                acik.setdefault(k, f)
        for s in satirlar:
            kimlik = str(s.get("anahtar"))
            k = _alan_anahtari(s.get("alan"))
            mevcut = acik.get(k) if k else None
            if kimlik in kimlikler:
                # AYNI BİLDİRİM YENİDEN İŞLENDİ (boru iki kez koştu / tekrar-ayrıştırma yolu): bu
                # YENİ bir gözlem değildir — ne satır açılır ne sayaç artar. Eski kimlik-tekilliği
                # sözleşmesi burada aynen yaşar.
                sonuc["gorulme"][kimlik] = int((mevcut or {}).get("gorulme") or 1)
                continue
            if mevcut is None:
                cur["fisler"].append(_fis_ilk_kayit(s))
                kimlikler.add(kimlik)
                if k:
                    acik.setdefault(k, s)
                sonuc["yeni"] += 1
                sonuc["gorulme"][kimlik] = 1
                continue
            _fis_birlestir(mevcut, _fis_ilk_kayit(s))
            kimlikler.add(kimlik)
            sonuc["birlesen"] += 1
            sonuc["gorulme"][kimlik] = int(mevcut.get("gorulme") or 1)
        cur["guncellendi"] = _now()
        cur["n"] = len(cur["fisler"])
        return True                         # `guncellendi` her koşuda tazelenir
    sonuc["doc"] = store.update_json(FISLER_FILE, _mut, {"fisler": [], "n": 0})
    return sonuc


def boru(kabul: list, *, hafta: str, yaz: bool = True) -> dict:
    """ÜÇ SINIFI YÖNLENDİREN OTOMATİK BORU. Haftalık koşunun SONUNDA çalışır.

    ŞEKİL BURADA DA YENİDEN TÜRETİLİR (`sekil_sinifla`) — modülün kendi yasası "beynin etiketine
    güvenilmez" ve o yasa TEK bir yerde değil HER yerde geçerlidir (`koprule`nin aynı notu). Boru
    dışarıdan da çağrılabilir ve o hâlde `o["sekil"]` hâlâ modelin etiketi olabilirdi.

    DÖNÜŞ: {"ozet": {...sayaçlar...}, "kalemler": [{"anahtar", "yol", "alan", "sekil", ...}]}."""
    fisler, kalemler, fis_kalemleri = [], [], []
    ozet = {"n": len(kabul), YOL_KUYRUK: 0, YOL_FIS: 0, YOL_RED: 0, "yazildi": bool(yaz),
            # TEKİLLEŞTİRME SAYAÇLARI (v296): "üç fiş yazıldı" ile "bir fiş açıldı, ikisi mevcut
            # satıra katlandı" aynı ekranda aynı şeye benzemesin. `fis_katlanan` DEFTERDE hazır
            # duran eski tekrarların katlanmasıdır (bir kereye mahsus, kusurun geriye dönük payı).
            "fis_yeni": 0, "fis_birlesen": 0, "fis_katlanan": 0}
    for o in kabul:
        sekil, isaretler = sekil_sinifla(o)
        if sekil != o.get("sekil"):
            o["sekil"], o["cekirdek_isaretleri"] = sekil, isaretler
        anahtar = _fis_anahtari(o, hafta)
        if sekil == "cekirdek_hakkinda":
            # (c) KATMAN D — RED. İstisna YOK, alarm YOK: sistem doğru çalışıyor, sınıf kapalı.
            ozet[YOL_RED] += 1
            kalemler.append({"anahtar": anahtar, "yol": YOL_RED, "alan": o.get("alan"),
                             "sekil": sekil, "cekirdek_isaretleri": isaretler[:6]})
            o["yol"] = YOL_RED
            obs.log(OLAY_RED_ANAYASAL, hafta=hafta, anahtar=anahtar,
                    alan=str(o.get("alan"))[:120], oncelik=o.get("oncelik"),
                    cekirdek_isaretleri=isaretler[:6],
                    detail=("Katman D: çekirdek (kapı yasaları · guard · PROTECTED · risk vetoları) "
                            "hakkındaki öneri YALNIZ rapora gider. Otomatik uygulama bu sınıfa ASLA "
                            "dokunmaz; öneri metni defterde durur ve Rol-1/operatör tüketir."))
            continue
        if sekil == "parametre":
            # (a) KÖPRÜ ZATEN KOŞTU — boru burada YALNIZ SONUCU OKUR. İkinci bir enqueue, aynı
            # öneriyi iki ölçüm sırasına sokar ve H4 bütçesini iki kez harcardı.
            ozet[YOL_KUYRUK] += 1
            o["yol"] = YOL_KUYRUK
            kalemler.append({"anahtar": anahtar, "yol": YOL_KUYRUK, "alan": o.get("alan"),
                             "sekil": sekil, "kuyruk": o.get("kuyruk"),
                             "kuyruk_id": o.get("kuyruk_id")})
            continue
        # (b) TASARIM → FİŞ.
        ozet[YOL_FIS] += 1
        o["yol"] = YOL_FIS
        satir = {"anahtar": anahtar, "ts": _now(), "hafta": hafta, "id": o.get("id"),
                 "alan": o.get("alan"), "oneri": str(o.get("oneri") or "")[:900],
                 "gozlem": str(o.get("gozlem") or "")[:900],
                 "beklenen_etki": str(o.get("beklenen_etki") or "")[:500],
                 "onerilen_olcum": str(o.get("onerilen_olcum") or "")[:500],
                 "oncelik": o.get("oncelik"), "sekil": sekil, "durum": "fislendi",
                 "kanit_atifi": o.get("kanit_atifi")}
        fisler.append(satir)
        kalem = {"anahtar": anahtar, "yol": YOL_FIS, "alan": o.get("alan"),
                 "sekil": sekil, "oncelik": o.get("oncelik")}
        kalemler.append(kalem)
        fis_kalemleri.append((satir, kalem))
    # DEFTER ÖNCE, OLAY SONRA (v296): tekrar sayacı defterin İÇİNDE doğar (`_fis_yaz`), bu yüzden
    # olay ancak yazımdan sonra "kaçıncı kez" diyebilir. Ters sıra sayacı olaya HİÇ taşıyamaz ve
    # tekrar bilgisi yalnız defterde kalırdı — ekranda okunmayan bir sayaç YASA 6 ihlalidir.
    yazim = _fis_yaz(fisler) if (yaz and fisler) else None
    if yazim:
        ozet.update({"fis_yeni": yazim["yeni"], "fis_birlesen": yazim["birlesen"],
                     "fis_katlanan": yazim["katlanan"]})
    elif fisler:
        # UYDURMA YASAĞI: kuru koşumda defter okunmaz — sayaçlar ÖLÇÜLEMEZ, sıfır YAZILMAZ.
        ozet.update({"fis_yeni": None, "fis_birlesen": None, "fis_katlanan": None,
                     "fis_tekil_olculemedi": FIS_SAYAC_KURU_KOSUM})
    for satir, kalem in fis_kalemleri:
        g = yazim["gorulme"].get(str(satir["anahtar"])) if yazim else None
        kalem["gorulme"] = g
        tekrar = (f"bu gözlem {g}. kez fişlendi — AYNI ALAN için YENİ SATIR AÇILMADI, sayaç arttı "
                  f"(TEKİLLEŞTİRME, susturma DEĞİL: her bildirimin kimliği izde durur ve tekrar "
                  f"sayısı bir sinyaldir). " if (g or 0) > 1 else "")
        obs.log(OLAY_FIS, hafta=hafta, anahtar=satir["anahtar"], alan=str(satir.get("alan"))[:120],
                oncelik=satir.get("oncelik"), yazildi=bool(yaz), gorulme=g,
                gorulme_olculemedi=(None if yazim else FIS_SAYAC_KURU_KOSUM),
                detail=(tekrar + "tasarım/kod/doküman önerisi FİŞLENDİ — otomatik uygulama yolu "
                        "YOK (ve olmamalı); operatör kuyruğunda görünür bir iş kalemi olarak durur."))
    return {"ozet": ozet, "kalemler": kalemler}


# =================================================================================================
# ⑤ GERİ BESLEME: ÖNCEKİ ÖNERİLERİN AKIBETİ
# =================================================================================================
def onceki_akibet(n_hafta: int = 2, hafta: str | None = None) -> dict:
    """Geçen haftaların önerilerine NE OLDU — beynin KENDİ önerilerinin karnesi.

    AKIBET CANLI HESAPLANIR, GERİYE DÖNÜK DAMGALANMAZ: kuyruk satırının bugünkü `status`ü okunur.
    Retro damga yasağının yanı sıra pratik bir sebep de var — akıbet ZAMANLA değişir (pending →
    measuring → measured) ve deftere yazılan bir damga bir hafta sonra yalan söylerdi.

    NEDEN PROMPT'A GİRER: H1 hermes'e kendi TAHMİN isabetini gösteriyor. Bu, aynı fikrin mekanizma
    düzeyindeki ikizidir: "geçen hafta şunu önerdin, ölçüldü ve tutmadı" bilgisi olmadan beyin her
    hafta aynı öneriyi yeniden üretir (H2'nin ölçtüğü "15 gündür aynı 14 düğme" hastalığının
    mekanizma sürümü)."""
    from . import hermes_composite
    rows = store.read_jsonl(PROPOSALS_FILE)
    if not rows:
        return {"durum": "gecmis_yok", "n": 0, "haftalar": [], "kalemler": [],
                "not": "ilk koşu — geri besleme YOK (uydurma ders yazılmaz)"}
    simdi = hafta or hermes_composite.week_key()
    haftalar = sorted({str(r.get("hafta") or "?") for r in rows if str(r.get("hafta")) != simdi})
    sec = set(haftalar[-max(1, n_hafta):])
    kuyruk = {str(q.get("id")): q for q in store.read_jsonl("composite_queue.jsonl")}
    kalemler = []
    for r in rows:
        if str(r.get("hafta") or "?") not in sec:
            continue
        kalemler.append({"hafta": r.get("hafta"), "alan": r.get("alan"),
                         "oneri": str(r.get("oneri") or "")[:200], "sekil": r.get("sekil"),
                         "oncelik": r.get("oncelik"), "akibet": _akibet(r, kuyruk)})
    return {"durum": "dolu", "n": len(kalemler), "haftalar": sorted(sec), "kalemler": kalemler[:20],
            "not": ("akıbet CANLI okunur (kuyruk satırının bugünkü durumu) — deftere geriye dönük "
                    "damga YAZILMAZ")}


def _akibet(satir: dict, kuyruk: dict) -> str:
    """Tek önerinin bugünkü akıbeti — ÖLÇÜLDÜ / ÖLÇÜLÜYOR / SIRADA / DEVREDİLDİ / YALNIZ RAPOR.

    ŞEKİL ÖNCE, KUYRUK DAMGASI SONRA. Ters sıra denendi ve YANLIŞTI: tasarım-şekilli bir öneri de
    `kuyruk="hayir"` taşır (kuyruk yolu ona hiç açık değildi) ve damgaya önce bakan bir okuma onu
    "şekil denetiminden düştü" diye rapor ediyordu. Üç farklı "kuyrukta değil" hâli üç ayrı şey
    söyler — tek cümleye katlanırsa beyin "önerim yok sayıldı" diye okur ve aynı öneriyi tekrar
    üretir (tam olarak kaçınmak istediğimiz döngü)."""
    sekil = str(satir.get("sekil") or "")
    if sekil == "cekirdek_hakkinda":
        return ("YALNIZ RAPOR (anayasal çekirdek — Katman D: öneri yazılabilir, değişiklik "
                "tetiklenemez)")
    if sekil != "parametre":
        return "YALNIZ RAPOR (tasarım-şekilli — otomatik ölçüm yolu yok, operatör/Rol 1 tüketir)"
    k = str(satir.get("kuyruk") or "")
    if k == "devredildi":
        return "DEVREDİLDİ — H4 bütçesi o hafta doluydu, sıradaki haftaya taşındı"
    if k == "hayir":
        return f"KUYRUK YOLU KAPALI — {'; '.join(str(x) for x in (satir.get('kuyruk_neden') or []))[:160]}"
    if k == "kuru_kosum":
        return "KURU KOŞUM — köprü hesaplandı ama kuyruğa YAZILMADI (yaz=False)"
    if k != "evet":
        return f"KUYRUK DAMGASI OKUNAMADI ({k or '—'}) — bu bir KOPUKLUK işaretidir"
    q = kuyruk.get(str(satir.get("kuyruk_id")))
    if not q:
        return (f"KUYRUKTA BULUNAMADI ({satir.get('kuyruk_id')}) — kuyruk satırı silinmiş ya da "
                f"kimlik ayrışmış (bu bir KOPUKLUK işaretidir, 'ölçülmedi' değil)")
    st = str(q.get("status") or "?")
    if st == "measured":
        r = q.get("result")
        return f"ÖLÇÜLDÜ → {json.dumps(r, ensure_ascii=False)[:220] if r is not None else 'sonuç alanı BOŞ'}"
    if st == "measuring":
        return "ÖLÇÜLÜYOR (prescreen süreci koşuyor)"
    if st == "pending":
        return "SIRADA (bütçe açıldığında ölçülecek)"
    if st == "measure_failed":
        # Kuyruk durum alfabesine `measure_failed` eklendi; bu okuma eskiden genel
        # dala düşüyordu ("kuyruk durumu: measure_failed"). Teknik olarak doğru, PRATİKTE ÖLÜ:
        # beyin bir sonraki haftanın önerisini `neden`e göre değiştirir ve iki başarısızlık İKİ AYRI
        # derstir — "guard bütün adayları reddetti" (öneri fizibilitesizdi, ŞEKLİNİ değiştir) ile
        # "ölçüm süreci ÖLÜ" (öneri sağlamdı, ALTYAPI düştü — aynısını tekrar öner) aynı cümleye
        # katlanırsa H1'in kendi isabet karnesi okunamaz hâle gelir.
        # Neden alanı BOŞ olabilir: o zaman "boş" DENİR, doldurulmaz (UYDURMA YASAĞI).
        _n = q.get("neden")
        return (f"ÖLÇÜM DÜŞTÜ: {str(_n)[:220]}" if _n else
                "ÖLÇÜM DÜŞTÜ — `neden` alanı BOŞ (damgayı basan taraf gerekçe yazmamış; "
                "bu bir KOPUKLUK işaretidir)")
    return f"kuyruk durumu: {st}"


# =================================================================================================
# KATMAN B: GÖREV ŞABLONU + KOŞU
# =================================================================================================
# GÖREV METNİ STATİK BİR SABİTTİR ve `hermes.SYSTEM`e DOKUNMAZ: her şey user-prompt yolundan girer.
# SYSTEM'e bir kelime eklemek `cache_control` isabetini kırar ve maliyeti sessizce katlar (AST
# testiyle çivili). Ayrıca SYSTEM hipotez üreticisinin sözleşmesidir; buraya mekanizma-değerlendirme
# görevi girse iki farklı görev tek talimatta karışırdı.
TASK = """SYSTEM prompt'undaki görev (tek parametre hipotezi) BU TURDA GEÇERLİ DEĞİL. Bu tur farklı
bir iştir ve çıktı biçimi aşağıda tanımlıdır.

GÖREV: Meridian'ın haftalık SİSTEM TELEMETRİSİNİ oku ve MEKANİZMA düzeyinde iyileştirme önerileri
üret. Sen bir strateji parametresi aramıyorsun; SİSTEMİN KENDİSİNİ değerlendiriyorsun: hangi
mekanizma üretmiyor, hangi defter boş, hangi kanıt üretilip tüketilmiyor, hangi kapı neyi eliyor,
hangi ölçüm hiç yapılmıyor.

EN DEĞERLİ ÖNERİ TÜRÜ "ÖLÇÜLEMEDİ" DİYEN BÖLÜMLERDEN ÇIKAR. Bir bölümün ölçülememesi iki farklı
şey olabilir ve ikisi ayrı öneri gerektirir: (a) taban henüz dolmadı — sabırlı beklemek doğru
cevaptır, öneri "beklemeyi hızlandır" olur; (b) mekanizma KOPUK — kimse yazmıyor ya da kimse
okumuyor, öneri "kabloyu bağla" olur. Hangisi olduğunu telemetrideki `neden` alanları söyler.

KURALLAR:
1. HER gözlem telemetrideki BELİRLİ bir sayıya ya da alan adına atıf yapmak ZORUNDADIR. Atıfı
   olmayan öneri okunmadan DÜŞÜRÜLÜR (bu bir kod kapısıdır, bir ricaya değil). Sayıyı ya da alan
   adını gözlem cümlesinin İÇİNDE yaz.
2. SAYI UYDURMAK YASAK. Telemetride olmayan bir ölçümden bahsetme; onun yerine "bu ölçülmüyor"
   gözlemini yap ve ölçümü öner.
3. Her öneri için `sekil` alanını doldur:
   - "parametre": bounds.yaml'da TANIMLI düğmelerin değerlerini değiştirmek. Bu şekli seçersen
     ayrıca `parametreler` alanını ver: 2 ya da 3 düğmelik bir demet ({"knob": sayı, ...}), her
     düğme bounds'ta tanımlı ve aralık+adım içinde. Demet otomatik olarak ÖLÇÜM SIRASINA girer.
   - "tasarim": kod/mekanizma/gösterge tasarımı — yeni bir ölçüm, kopuk bir kablonun bağlanması,
     bir defterin doldurulması, bir panonun bir sayıyı göstermesi. Rapora gider.
   - "cekirdek_hakkinda": kapı yasaları, guard, PROTECTED skill'ler, risk vetoları, eşikler,
     tek-değişken yasası, autonomy_level hakkında. BUNLARI YAZMAN İSTENİR — kör nokta oradadır —
     ama YALNIZ rapora giderler ve hiçbir değişiklik tetiklemezler. Hâkim kendi yasasını yazamaz.
4. `beklenen_etki` FALSİFİYE EDİLEBİLİR olmalı: hangi sayı hangi yöne, kabaca ne kadar.
5. `onerilen_olcum`: bu öneri işe yaradı mı, NASIL anlarız? Var olan bir mekanizmayla ölç.
6. AZ VE TAM-DÖNGÜLÜ. En fazla 8 öneri. Beş sağlam öneri, on beş temenniden iyidir.
7. Önceki haftaların önerilerinin akıbeti aşağıda. Ölçülüp TUTMAYAN bir öneriyi tekrar önermek bir
   ölçüm bütçesi yakar ve hiçbir şey öğretmez. Devredilmiş bir öneriyi tekrar yazmaya gerek yok.

ÇIKTI: YALNIZCA şu JSON nesnesi — öncesinde ve sonrasında hiçbir metin, markdown ya da açıklama yok.
{"oneriler": [{"alan": "hangi mekanizma (tercihen telemetri bölüm adı)",
               "gozlem": "telemetrideki HANGİ sayı/alan bunu söylüyor — sayıyı cümlenin içine yaz",
               "oneri": "ne yapılsın",
               "beklenen_etki": "hangi sayı hangi yöne, kabaca ne kadar",
               "onerilen_olcum": "nasıl doğrulanır",
               "oncelik": "yuksek|orta|dusuk",
               "sekil": "parametre|tasarim|cekirdek_hakkinda",
               "parametreler": {"knob_adi": 0.4}}]}
`parametreler` YALNIZ sekil="parametre" iken verilir; diğer şekillerde alanı hiç yazma."""


def _prompt(telemetri: dict, akibet: dict) -> str:
    """Katman B'nin user-prompt'u: görev + telemetri + kendi karnesi. SYSTEM'e DOKUNULMAZ."""
    return (TASK
            + "\n\n===== HAFTALIK SİSTEM TELEMETRİSİ ("
            + str(telemetri.get("hafta")) + ") =====\n"
            + json.dumps(telemetri, ensure_ascii=False, default=str)
            + "\n\n===== ÖNCEKİ ÖNERİLERİNİN AKIBETİ (kendi karnen) =====\n"
            + json.dumps(akibet, ensure_ascii=False, default=str))


def haftalik_degerlendirme(*, telemetri: dict | None = None, yaz: bool = True,
                           kuyruk: bool = True, hafta: str | None = None,
                           text: str | None = None) -> dict:
    """KATMAN B'NİN HAFTALIK KOŞUSU. Scheduler'ın haftalık kadansı buraya asılır.

    `telemetri` ENJEKTE EDİLEBİLİR: ⑥ ilk koşusu paketi CANLI state'ten derleyip değerlendirmeyi
    KUM HAVUZUNDA koşturdu (canlı state'e yazmadan). Enjeksiyon o ayrımı mümkün kılan tek şeydir.
    `text` de enjekte edilebilir (testler ve tekrar-ayrıştırma) — verilirse LLM ÇAĞRILMAZ.

    `yaz=False`: defter yazılmaz (kuru koşum). `kuyruk=False`: köprü hesaplanır ama kuyruğa
    yazılmaz — "ne olurdu" görünür, hiçbir ölçüm sırası tüketilmez."""
    from . import analytics, hermes, hermes_composite
    h = hafta or hermes_composite.week_key()
    tel = telemetri if telemetri is not None else analytics.system_telemetry()
    ak = onceki_akibet(hafta=h)
    kayit: dict = {"hafta": h, "ts": _now(), "durum": "kosuldu", "beyin": None, "model": None,
                   # KÜNYE BEYANLARI HER KAYITTA DURUR (bkz. üstteki KUNYE_* bloğu): zincir
                   # çağrılmadığı yolda bile alanlar VAR ve `model_olculemedi` niçin ad olmadığını
                   # söyler — sessiz bir None "ölçtük, çıkmadı" diye okunurdu.
                   "model_kaynagi": None, "model_olculemedi": KUNYE_ZINCIR_CAGRILMADI,
                   "model_istenen": None,
                   "telemetri_hafta": tel.get("hafta"),
                   # İKİ SAYAÇ AYRI TAŞINIR (bkz. analytics.system_telemetry notu): "bölüm boş" ile
                   # "üretici kendi içinde ölçemedim dedi" farklı sorulardır ve Katman B'nin en
                   # verimli öneri kaynağı ikincisidir — ilk koşuda 6 önerinin 5'i oradan çıktı.
                   "n_olculemedi": tel.get("n_olculemedi"),
                   "olculemeyenler": tel.get("olculemeyenler"),
                   "n_beyan_edilen_bosluk": tel.get("n_beyan_edilen_bosluk"),
                   "beyan_edilen_bosluklar": tel.get("beyan_edilen_bosluklar")}
    if text is None:
        cevap = hermes.chain_text(_prompt(tel, ak), kind="system_eval", note="nous_eval",
                                 preload=(), timeout=420, max_wait=45.0)
        text, kayit["beyin"], kayit["model"] = (cevap.get("text"), cevap.get("beyin"),
                                               cevap.get("model"))
        kayit["zincir_neden"] = cevap.get("neden")
        # ÜÇ BEYAN OLDUĞU GİBİ TAŞINIR (WP7-40). `model_kaynagi` VARSA `model` = cevabı veren;
        # yoksa kayıt beyansız bir dönüşten gelir ve o hâl de ADIYLA yazılır. Ad ölçülemediyse
        # nedeni zincirden gelir; zincir neden de vermediyse burada UYDURULMAZ, "beyansız dönüş"
        # diye kaydedilir — `active_model()`e (yapılandırma) sessizce dönmek YASAK.
        kayit["model_kaynagi"] = cevap.get("model_kaynagi")
        kayit["model_istenen"] = cevap.get("model_istenen")
        kayit["model_olculemedi"] = (cevap.get("model_olculemedi")
                                     or (None if kayit["model"] else KUNYE_BEYANSIZ_DONUS))
        if not text:
            # LLM ERİŞİMİ YOK/KESİNTİLİ: ŞABLON ÇIKTI UYDURULMAZ. Koşu "koşulamadı" olarak kaydedilir
            # ve hangi ayağın niçin cevap vermediği yazılır (UYDURMA YASAĞI).
            kayit.update({"durum": "kosulamadi", "n_uretilen": 0, "n_kabul": 0, "n_dusen": 0,
                          "dusme_nedenleri": {}, "devreden": []})
            if yaz:
                _kosu_kaydet(kayit)
            obs.warn("nous_eval_no_brain", hafta=h, neden=cevap.get("neden"),
                     detail="beyin zinciri metin döndürmedi — haftalık mekanizma değerlendirmesi "
                            "KOŞULAMADI (şablon öneri üretilmez)")
            return {"kosu": kayit, "kabul": [], "telemetri": tel, "akibet": ak, "kopru": None}
    ayr = ayristir(text, tel)
    # MÜKERRERLİK KAPISI, ÜÇ YOLUN AYRIM NOKTASINDA (2026-09-01). Kapı BİLEREK `_oneri_kaydet`in
    # append'ine değil BURAYA konur: `koprule` ondan ÖNCE, `boru` ondan SONRA koşar ve fiş satırı
    # `_oneri_kaydet`in ürettiği `id`yi taşır. Yalnız append'i korumak, mükerrer öneriye (i) bir
    # H4 ölçüm sırası harcatır, (ii) `id: None` taşıyan — hiçbir öneriye işaret etmeyen — bir fiş
    # doğururdu. Burada düşen öneri kalite kapısından düşenle AYNI muameleyi görür: sayılı, adlı.
    _mukerrer_ele(ayr, hafta=h)
    kabul = ayr["kabul"]
    kopru = koprule(kabul, yaz=bool(kuyruk and yaz))
    kayit.update({"durum": ayr["durum"], "n_uretilen": ayr["n_uretilen"],
                  "n_kabul": len(kabul), "n_dusen": ayr["n_dusen"],
                  "dusme_nedenleri": ayr["dusme_nedenleri"],
                  "sekil_dagilimi": _say(kabul, "sekil"), "oncelik_dagilimi": _say(kabul, "oncelik"),
                  "n_kuyruk": len(kopru["kuyruga_giren"]), "devreden": kopru["devreden"],
                  "slot": kopru["slot"], "haftalik_butce": kopru["haftalik_butce"]})
    # DEFTER ÖNCE, BORU SONRA: fiş satırı önerinin `id`sini taşımalı ve o kimlik burada,
    # `_oneri_kaydet` içinde doğuyor. Ters sıra fişleri kimliksiz bırakırdı — kimlik hem önerinin
    # TAM metnine (`improvement_proposals.jsonl`) işaret eden tek bağ, hem de pano rozetinin eşleşme
    # anahtarıdır. (Fiş TEKİLLEŞTİRMESİ bu kimlikle DEĞİL gözlemin adresiyle yapılır — kimlik her
    # koşuda yenilendiği için tekilleştirme hiç kapanmıyordu; bkz. `_alan_anahtari` bloğu.)
    if yaz:
        for o in kabul:
            _oneri_kaydet(o, h, kayit)
    brs = boru(kabul, hafta=h, yaz=yaz)
    kayit["boru"] = brs["ozet"]
    if yaz:
        _kosu_kaydet(kayit)
    obs.log("nous_eval_done", hafta=h, beyin=kayit["beyin"], uretilen=ayr["n_uretilen"],
            kabul=len(kabul), dusen=ayr["n_dusen"], kuyruk=len(kopru["kuyruga_giren"]),
            devreden=len(kopru["devreden"]), yazildi=bool(yaz),
            boru=brs["ozet"])
    return {"kosu": kayit, "kabul": kabul, "dusenler": ayr["dusenler"], "telemetri": tel,
            "akibet": ak, "kopru": kopru, "boru": brs}


def _mukerrer_ele(ayr: dict, *, hafta: str) -> None:
    """AKIBET DEFTERİ KAPISI: daha önce doğmuş bir fikri yeniden doğuran öneriyi `kabul`den DÜŞÜR.

    NEDEN VAR (ölçüldü 2026-09-01, ilk akıbet karar turu): 22 önerinin ~%45'i bellek-yokluğu
    israfıydı — reddedilmiş ya da zaten karara bağlanmış bir fikir, bunu söyleyecek hiçbir yer
    olmadığı için ertesi tur yeniden doğuyordu. Hüküm `mukerrerlik.mukerrer_mi`nindir; burada
    yalnız BASTIRMA kararı ve muhasebesi yaşar.

    DÜŞÜŞ SESSİZ DEĞİLDİR — üç yerde birden görünür: (a) `dusme_nedenleri` sayacı (koşu kaydı →
    pano), (b) `dusenler` özeti, (c) `OLAY_BASTIRILDI` olayı (eşleşen kimlik + benzerlik). Bedel
    yasasının gereği: gürültüyü azaltan değişiklik ne KAYBETTİĞİNİ de ölçer, yoksa kapı bir gün
    fazla ısırdığında belirti hiçbir şey olur.

    FAIL-OPEN: hüküm `None` (ölçülemedi) ise öneri GEÇER ve körlük `OLAY_OLCULEMEDI` ile adıyla
    kaydedilir — ölçülemeyen benzerlikle bastırmak sahte hüküm olurdu (uydurma yasağı)."""
    kalan: list[dict] = []
    for o in ayr.get("kabul") or []:
        h = mukerrerlik.mukerrer_mi(o.get("oneri"))
        # KÖRLÜK HÜKÜMDEN BAĞIMSIZ LOGLANIR: bir kaynak okunamamışken öteki mükerreri gösterebilir
        # (hüküm True) ya da göstermeyebilir (hüküm False) — iki hâlde de "neyi göremedik" sorusu
        # cevaplanabilir olmalı, yoksa eksik taramaya dayanan sessiz bir "temiz" iddiası doğar.
        korluk = h.get("olculemeyen") or {}
        tam = h["mukerrer"] is None
        for kaynak, neden in sorted(korluk.items()):
            obs.log(mukerrerlik.OLAY_OLCULEMEDI, hafta=hafta, alan=str(o.get("alan"))[:120],
                    kaynak=kaynak, neden=neden, tam_korluk=tam,
                    detail=("mükerrerlik kaynağı OKUNAMADI. Tam körlükte öneri GEÇER "
                            "(fail-open, beyanlı): ölçülemeyen benzerlikle bastırmak sahte bir "
                            "hüküm olurdu. Kısmi körlükte okunabilen kaynakla devam edilir."))
        if tam:
            if not korluk:
                obs.log(mukerrerlik.OLAY_OLCULEMEDI, hafta=hafta, alan=str(o.get("alan"))[:120],
                        kaynak=None, neden=h["neden"], tam_korluk=True,
                        detail=("mükerrerlik ÖLÇÜLEMEDİ (kaynak arızası DEĞİL — öneri metni "
                                "karşılaştırılabilir jeton taşımıyor); öneri GEÇTİ"))
            kalan.append(o)
            continue
        if not h["mukerrer"]:
            kalan.append(o)
            continue
        ayr["n_dusen"] = ayr.get("n_dusen", 0) + 1
        ayr.setdefault("dusme_nedenleri", {})
        ayr["dusme_nedenleri"][mukerrerlik.DUSME_NEDENI] = \
            ayr["dusme_nedenleri"].get(mukerrerlik.DUSME_NEDENI, 0) + 1
        ayr.setdefault("dusenler", []).append(
            {"neden": mukerrerlik.DUSME_NEDENI, "alan": o.get("alan"), "bas": str(o)[:160]})
        obs.log(mukerrerlik.OLAY_BASTIRILDI, hafta=hafta, alan=str(o.get("alan"))[:120],
                eslesen_id=h["eslesen_id"], eslesen_kaynak=h["eslesen_kaynak"],
                benzerlik=h["benzerlik"], esik=mukerrerlik.ESIK,
                bas=str(o.get("oneri"))[:200],
                detail=("AKIBET DEFTERİNDE EŞİ VAR — öneri DOĞMADI (deftere yazılmaz, kuyruğa "
                        "girmez, fişlenmez). Aynı fikrin yeniden doğması ölçülmüş bir israftır "
                        "(2026-09-01 karar turu: 22 önerinin ~%45'i bellek-yokluğu)."))
    ayr["kabul"] = kalan


def _say(rows: list, alan: str) -> dict:
    """Satırlarda verilen alanın değerlerini sayar (değer → adet); boş/None değerler '?' kovasına düşer."""
    out: dict[str, int] = {}
    for r in rows:
        out[str(r.get(alan) or "?")] = out.get(str(r.get(alan) or "?"), 0) + 1
    return out


def _now() -> str:
    """Şimdiki UTC zamanı, saniye çözünürlüklü ISO-8601 metni olarak."""
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _oneri_kaydet(o: dict, hafta: str, kayit: dict) -> None:
    """Kabul edilen öneriyi deftere yaz (ledgers sözleşmeli).

    DÜŞEN ÖNERİ DEFTERE YAZILMAZ: defter KABUL EDİLENLERİN kaydıdır. Düşenlerin SAYISI ve NEDENİ
    koşu kaydında (`nous_eval_runs.json`) durur ve panoda görünür — yani düşme sessiz değildir, ama
    kanıt-atıfsız bir cümle de kalıcı bir öneri gibi durmaz (o cümlenin tüketicisi yoktur)."""
    row = {"ts": _now(), "id": f"N{_next_seq():05d}", "hafta": hafta,
           "alan": o.get("alan"), "gozlem": o.get("gozlem"), "oneri": o.get("oneri"),
           "beklenen_etki": o.get("beklenen_etki"), "onerilen_olcum": o.get("onerilen_olcum"),
           "oncelik": o.get("oncelik"), "sekil": o.get("sekil"),
           "kanit_atifi": o.get("kanit_atifi"),
           "sekil_beyan": o.get("sekil_beyan"),
           "cekirdek_isaretleri": o.get("cekirdek_isaretleri"),
           "alan_bilinen": o.get("alan_bilinen"),
           "parametreler": o.get("parametreler"),
           # KUYRUK DAMGASININ VARSAYILANI ŞEKLE BAĞLIDIR: parametre-şekilli bir öneride damga
           # köprüden gelir; tasarım/çekirdek şekillerinde kuyruk yolu HİÇ açık değildi ve onu
           # "hayir" (= şekil denetiminden düştü) diye damgalamak, olmayan bir reddi kaydetmekti.
           "kuyruk": o.get("kuyruk", "hayir" if o.get("sekil") == "parametre" else "yol_yok"),
           "kuyruk_id": o.get("kuyruk_id"),
           "kuyruk_neden": o.get("kuyruk_neden"),
           # KÜNYE, KOŞU KAYDIYLA AYNI ÜÇ BEYANI TAŞIR (WP7-40): öneri satırından "bu öneriyi
           # hangi model yazdı, ad ölçülebildi mi, istenen ad neydi?" sorusu CEVAPLANABİLİR olmalı.
           # Alanlar ledgers sözleşmesinde ZORUNLU DEĞİL (None meşru, eski satırlarda hiç yok) ve
           # `required` kümesi DEĞİŞMEDİ — geriye dönük satırlar ihlal ilan edilmez, retro damga yok.
           "beyin": kayit.get("beyin"), "model": kayit.get("model"),
           "model_kaynagi": kayit.get("model_kaynagi"),
           "model_olculemedi": kayit.get("model_olculemedi"),
           "model_istenen": kayit.get("model_istenen")}
    store.append_jsonl(PROPOSALS_FILE, row)
    o["id"] = row["id"]


def _next_seq() -> int:
    """Sıradaki öneri numarası: defterdeki satır sayısı + 1 (N00001 kimliğinin sayacı)."""
    return len(store.read_jsonl(PROPOSALS_FILE)) + 1


def _kosu_kaydet(kayit: dict) -> None:
    """Haftalık koşu kaydını `nous_eval_runs.json` içine hafta anahtarıyla yazar (kilitli
    oku-değiştir-yaz) ve `son` damgasını tazeler.
    """
    def _f(st):
        """Koşu belgesini yerinde günceller: kaydı `haftalar[hafta]` altına koyar, `son` damgasını atar."""
        if st is None:
            return False
        st.setdefault("haftalar", {})[str(kayit.get("hafta"))] = kayit
        st["son"] = _now()
        return True
    store.update_json(RUNS_FILE, _f, {})


# =================================================================================================
# ⑤ TÜKETİCİ: --ozet CLI (Rol 1 haftalık denetimi)
# =================================================================================================
def ozet_metni(limit_hafta: int = 3) -> str:
    """`--ozet` metni. BOŞ DEFTER SAHTE BİR 'HER ŞEY YOLUNDA' GÖSTERMEZ — ne eksik olduğunu söyler."""
    from . import analytics
    d = analytics.improvement_proposals_status(limit_hafta=limit_hafta)
    L = ["NOUS SİSTEM-DEĞERLENDİRMESİ — SİSTEM ÖNERİLERİ"]
    if d.get("durum") != "dolu":
        L.append(f"  {d.get('durum')}")
        L.append(f"  {d.get('rol')}")
        return "\n".join(L)
    L.append(f"  defter: {d['n']} öneri · haftalar: {', '.join(d.get('haftalar') or [])}")
    L.append(f"  son hafta {d.get('son_hafta')}: {d.get('n_son_hafta')} öneri · "
             f"beyin={d.get('beyin')} model={d.get('model')} · koşu={d.get('kosu_durumu')}")
    L.append(f"  KALİTE KAPISI: üretilen={d.get('n_uretilen')} · düşen={d.get('n_dusen')} "
             f"{d.get('dusme_nedenleri') or ''}")
    L.append(f"  şekil: {d.get('sekil_dagilimi')} · öncelik: {d.get('oncelik_dagilimi')}")
    if d.get("devreden"):
        L.append(f"  DEVREDEN (H4 bütçesi doluydu): {len(d['devreden'])} öneri sıradaki haftaya")
    L.append("")
    for o in d.get("oneriler") or []:
        L.append(f"  [{o.get('oncelik','?').upper():>6}] [{o.get('sekil')}] {o.get('alan')}"
                 f"  ({o.get('id')})")
        L.append(f"      gözlem : {str(o.get('gozlem') or '')[:200]}")
        L.append(f"      öneri  : {str(o.get('oneri') or '')[:200]}")
        L.append(f"      etki   : {str(o.get('beklenen_etki') or '')[:160]}")
        L.append(f"      ölçüm  : {str(o.get('onerilen_olcum') or '')[:160]}")
        L.append(f"      atıf   : {', '.join(str(x) for x in (o.get('kanit_atifi') or []))[:160]}")
        L.append(f"      kuyruk : {o.get('kuyruk')} {o.get('kuyruk_id') or ''}")
    L.append("")
    L.append(f"  {d.get('rol')}")
    return "\n".join(L)


def _cli() -> int:
    """CLI girişi (`python -m meridian.nous_eval`).

    `--boru` defterdeki kabul edilmiş önerileri yönlendirme borusundan geçirir (LLM ÇAĞIRMAZ),
    `--telemetri` paketi basar, `--kosu` haftalık değerlendirmeyi koşturur (LLM çağırır), `--json`
    durum özetini JSON verir; bayraksız çağrı defter özetini yazar. `--kuru` verildiğinde deftere
    ve kuyruğa YAZILMAZ.
    """
    import argparse
    ap = argparse.ArgumentParser(description="Nous sistem-değerlendirme katmanı (Katman B/C/D)")
    ap.add_argument("--ozet", action="store_true",
                    help="defter özetini yaz ve çık (Rol 1 haftalık denetimi)")
    ap.add_argument("--hafta", type=int, default=3, metavar="N",
                    help="--ozet: son N haftayı listele")
    ap.add_argument("--telemetri", action="store_true",
                    help="telemetri paketini JSON olarak yaz (koşu YOK, LLM YOK)")
    ap.add_argument("--kosu", action="store_true",
                    help="haftalık değerlendirmeyi KOŞTUR (LLM çağrısı yapar)")
    ap.add_argument("--kuru", action="store_true",
                    help="--kosu: deftere ve kuyruğa YAZMA (yalnız çıktı)")
    ap.add_argument("--boru", metavar="HAFTA", nargs="?", const="__son__",
                    help="DEFTERDEKİ kabul edilmiş önerileri yönlendirme borusundan geçir "
                         "(hafta verilmezse defterdeki SON hafta). Boru v192'de eklendi; ondan "
                         "ÖNCE kabul edilmiş satırlar hiçbir yola bağlanmamıştı — bu tek-atışlık "
                         "yol onları fiş/red kuyruklarına taşır. LLM ÇAĞIRMAZ, öneri ÜRETMEZ.")
    ap.add_argument("--json", action="store_true", help="çıktıyı JSON olarak ver")
    a = ap.parse_args()
    if a.boru:
        rows = store.read_jsonl(PROPOSALS_FILE)
        if not rows:
            print("defter BOŞ — yönlendirilecek öneri yok"); return 0
        h = a.boru if a.boru != "__son__" else sorted({str(r.get("hafta") or "?") for r in rows})[-1]
        kabul = [r for r in rows if str(r.get("hafta") or "?") == h]
        # KURU KOŞUM VARSAYILAN DEĞİL, AMA `--kuru` ONURLANDIRILIR: bu yol canlı state'e yazar
        # (fiş defteri) ve o yüzden ne yaptığı ÖNCE ekrana basılır.
        out = boru(kabul, hafta=h, yaz=not a.kuru)
        print(json.dumps({"hafta": h, "n_defter_satiri": len(kabul), **out},
                         ensure_ascii=False, indent=1, default=str))
        return 0
    if a.telemetri:
        from . import analytics
        print(json.dumps(analytics.system_telemetry(), ensure_ascii=False, indent=1, default=str))
        return 0
    if a.kosu:
        out = haftalik_degerlendirme(yaz=not a.kuru, kuyruk=not a.kuru)
        print(json.dumps({k: out[k] for k in ("kosu", "kabul", "kopru")},
                         ensure_ascii=False, indent=1, default=str))
        return 0
    if a.json:
        from . import analytics
        print(json.dumps(analytics.improvement_proposals_status(limit_hafta=a.hafta),
                         ensure_ascii=False, indent=1, default=str))
        return 0
    print(ozet_metni(limit_hafta=a.hafta))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
