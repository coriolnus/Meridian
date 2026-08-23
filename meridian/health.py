"""health.py — operatörün kontrol durumu: kill-switch, nabız, bayatlık ve silahlanma kilitleri.

Sessiz bir ajan izlenmeyen bir ajandır; bu modül "şu an müdahale gerekiyor mu?" sorusunun
dosya-tabanlı durum katmanıdır. Üç bayrak dosyası tutar (yeniden başlatmada yaşar, elle de
yönetilir): state/HALT — kill-switch, dosya VARSA yeni giriş bir bar içinde durur
(`halted`/`set_halt`); state/LEARN_HALT — işlemler sürer ama yeni sürüm ship edilemez
(`learn_halted`/`set_learn_halt`); state/INTRADAY_ARM — TERS mantık, dosya VARSA silahlı; hiçbir
otomatik yol açamaz, yalnız operatör (`intraday_armed`/`set_intraday_arm`). `write_heartbeat`
nabzı sıfırdan kurmaz, ÜZERİNE BİNDİRİR: nabız çok yazarlıdır ve her yazar yalnız kendi alanını
damgalar — ikinci yazarın birincinin alanlarını sessizce silmesi canlıda yaşandı, bindirme onun
düzeltmesidir. `heartbeat_age_seconds`/`stale` bayatlığı, `circuit_breaker_tripped` günlük kayıp
kesicisini ölçer.

`faz6_kilitleri` otonom intraday silahlanmanın ön-koşulunu BEŞ kilitle rapor eder
(`FAZ6_KILITLERI`: edge_kaniti, sonuc_hukmu, faz5_cikisi, operator_onayi, dsr_gecer): SAF
okumadır — hiçbir şeyi silahlamaz, hiçbir dosyaya yazmaz; ölçülemeyen kilit KAPALIdır
(fail-closed) ve DSR eşiği ship yoluyla AYNI yerden (`validation.DSR_HARD_MIN`) okunur.
Reddedilen gönderimler ack ile SUSTURULUR, SİLİNMEZ (`reject_key`/`split_rejections`;
broker_reject_ack.json'u api yazar, burası okur). Okur/yazar: state bayrak dosyaları,
heartbeat.json ve intraday defter sayımları (store üzerinden)."""
from __future__ import annotations
import datetime as dt
from pathlib import Path

from . import config, store

HEARTBEAT = "heartbeat.json"


def halt_path() -> Path:
    """Kill-switch bayrak dosyasının yolu (`state/HALT`)."""
    return config.STATE / "HALT"


def halted() -> bool:
    """True if the kill-switch file exists. Checked every bar before any new entry."""
    return halt_path().exists()


# Kademeli kriz kontrolleri. Kademe 1 (Soft Halt) mevcut HALT dosyasıdır; kademe 4
# (Halt Learning) ayrı bayrak: işlemler sürer, Hermes YENİ versiyon ship EDEMEZ (rollback güvenlik
# olarak açık kalır). İkisi de dosya-tabanlı: yeniden başlatmada hayatta kalır, elle de yönetilebilir.
def learn_halt_path() -> Path:
    """Kademe-4 (öğrenme durdurma) bayrak dosyasının yolu (`state/LEARN_HALT`)."""
    return config.STATE / "LEARN_HALT"


def learn_halted() -> bool:
    """LEARN_HALT dosyası varsa True: işlemler sürer ama yeni sürüm ship EDİLEMEZ."""
    return learn_halt_path().exists()


def set_halt(on: bool) -> bool:
    """Kill-switch'i açar (dosyayı touch'lar) ya da kapatır (siler); sonuçtaki gerçek durumu döner.

    Dönüş değeri istenen değil ÖLÇÜLEN durumdur (`halted()` yeniden okunur)."""
    p = halt_path()
    if on:
        p.touch(exist_ok=True)
    elif p.exists():
        p.unlink()
    return halted()


def set_learn_halt(on: bool) -> bool:
    """LEARN_HALT bayrağını açar/kapatır ve dosyadan yeniden okunan gerçek durumu döner."""
    p = learn_halt_path()
    if on:
        p.touch(exist_ok=True)
    elif p.exists():
        p.unlink()
    return learn_halted()


# Faz 4 — INTRADAY SİLAHLANMA bayrağı (HALT ikizi, TERS mantık: dosya VARSA silahlı). Otonom intraday
# emir göndermeyi kapılar. Default YOK = SİLAHSIZ (yalnız gözlem). autonomy_level DEĞİL (o gerçek parayı
# kapılar; intraday paper'dır). Hiçbir otomatik yol (döngü/ajan/bekçi) açamaz — yalnız operatörün elle
# touch'ı / panodaki tuş. Faz 4b (gerçek intraday silahlanma) bu bayrak + EOD ile aynı güvenlik kapıları
# olmadan çalışmaz.
def intraday_arm_path() -> Path:
    """Intraday silahlanma bayrak dosyasının yolu (`state/INTRADAY_ARM`)."""
    return config.STATE / "INTRADAY_ARM"


def intraday_armed() -> bool:
    """TERS mantık: dosya VARSA silahlı. Dosya yoksa silahsız (yalnız gözlem) — default kapalıdır."""
    return intraday_arm_path().exists()


def set_intraday_arm(on: bool) -> bool:
    """INTRADAY_ARM bayrağını açar/kapatır ve dosyadan yeniden okunan gerçek durumu döner.

    Yalnız operatör yolu içindir; hiçbir otomatik akış (döngü/ajan/bekçi) bunu çağırmamalıdır."""
    p = intraday_arm_path()
    if on:
        p.touch(exist_ok=True)
    elif p.exists():
        p.unlink()
    return intraday_armed()


# ---- FAZ-6 KİLİT ZİNCİRİ (operatör onaylı) ------------------------------------------------------
# NEDEN BU DOSYADA: Faz-6'nın (otonom intraday emir) fiziksel anahtarı `state/INTRADAY_ARM`dır ve o
# bayrak BU modülde yaşıyor. Kilitleri bayrağın yanında tutmak, "bayrağı açan kişi neyin açıldığını
# aynı dosyada okur" demektir; başka bir modüle koymak, anahtarla kilit listesini iki ayrı yere
# dağıtıp birinin diğerinden habersiz gevşemesine izin verirdi.
#
# KİLİT LİSTESİ TEK YERDE ADLANDIRILDI (`FAZ6_KILITLERI`). Yol haritası "dört kilit" diyordu ama o
# dört kilit hiçbir yerde MAKİNE OKUNUR biçimde yazılı değildi — yani "dolunca silahlan" cümlesinin
# denetçisi yoktu ve bir kilidin sessizce düşmesi kimseye görünmezdi. Bu tur beşinciyi (DSR) ekliyor
# ve aynı hamlede listeyi kodun içine alıyor.
#
#   1. edge_kaniti    — `analytics.edge_verdict`: BEŞ ölçütün BEŞİ de eşiği VE anlamlılığı geçti mi?
#   2. sonuc_hukmu    — `analytics.result_verdict`: DÖRT dolar ölçütünün DÖRDÜ de sağlandı mı?
#                       (rafineri kararları EDGE'e, sermaye/SİLAHLANMA
#                       İKİSİNE bakar — R birimi geniş stopa yapısal önyargılı olduğu için tek
#                       merceğe bırakılamaz)
#   3. faz5_cikisi    — dakikalık kanıt katmanı: 4a saha verisi + "dakika-hassas icra ne
#                       kazandırırdı" CI'lı ölçümü. İKİNCİSİ SONRADAN YAZILDI
#                       (`faz5_cikis.cikis_olcumu`, ön-kayıt kartı EXE-2026-002): eşleştirilmiş
#                       (plan_id) gölge-vs-EOD farkı, TARİH-KÜMELİ bootstrap %95 CI, E3 maliyet
#                       bandı eşiği, n_min=20. Kilit hâlâ kapalı olabilir ama artık ÖLÇÜLMÜŞ bir
#                       gerekçeyle kapalıdır. "Ölçüm yok" ile "ölçüldü ve geçti" arasındaki farkı
#                       silmek, tam olarak bu zincirin engellediği şeydir — `durum` alanı ikisini
#                       ayırmaya devam eder (`olculemedi` = defter boş / kill#4 eşleştirme kırığı).
#   4. operator_onayi — `state/INTRADAY_ARM` (elle touch / panodaki tuş). Hiçbir otomatik yol
#                       (döngü/ajan/bekçi) açamaz; yol haritasının "5.1 runtime (Oracle taşıma)"
#                       ön şartı da OPERATÖR TARAFINDA olduğu için bu kilidin içinde taşınır —
#                       makine tarafında ölçülebilir bir karşılığı yoktur ve uydurulmaz.
#   5. dsr_gecer      — YÜRÜRLÜKTEKİ PENCEREDE (R1+) canlı defterin DSR'si ölçülü VE eşiği geçiyor
#                       mu? (`validation.DSR_HARD_MIN`; ship yolunun okuduğu AYNI eşik ve AYNI
#                       hüküm fonksiyonu). Ölçülemiyorsa FAIL-CLOSED — gerçek-para/silahlanma
#                       tarafında "kanıt yoksa kapı kapalı" kuralı istisnasızdır.
#
# BU FONKSİYON HİÇBİR ŞEY SİLAHLAMAZ VE HİÇBİR DOSYAYA YAZMAZ. Saf okumadır: bugün hiçbir kod yolu
# otonom intraday emir göndermiyor (Faz 4b silahlama bacağı yazılmadı), yani bu zincirin eklenmesi
# canlı davranışı DEĞİŞTİREMEZ. Faz 4b/6 yazıldığında ön-koşul kontrolü BURAYA bağlanır.
# EZER: (ezen kod değil TÜKETİCİ YOKLUĞU) 5 kilit + analytics'in 12 kanıt eşiği ezilen taraf —
# 25d zinciri c-9 (silahlama bacağının ön-koşul kontrolü bu fonksiyona hâlâ bağlanmadı; kilitler
# ölçüyor, kimse hükümlerini tüketip silahlanmıyor. Şerh: 4b gönderim bacağı 2026-08-11'de
# yazıldı ve `intraday_arm_flag_on_but_4b_not_built` olayı 0'a indi — zincirin BİR ucu kapandı,
# kilit→silahlanma kablosu hâlâ yok), 2026-08-23
FAZ6_KILITLERI = ("edge_kaniti", "sonuc_hukmu", "faz5_cikisi", "operator_onayi", "dsr_gecer")


def _kilit(gecer: bool | None, durum: str, olcum, esik: str, neden: str | None = None) -> dict:
    """Tek kilit satırı. `gecer` ÜÇ DEĞERLİ DEĞİLDİR — `None` yoktur: bir kilit ya AÇIKtır ya
    KAPALIdır, ve ölçülemeyen kilit KAPALIdır (fail-closed). `durum` ise ölçümün kendisini ayırır
    ("olculdu" / "olculemedi") ki "kapalı çünkü kaldı" ile "kapalı çünkü hiç ölçülemedi" aynı
    cümleye sıkışmasın — ikisi çok farklı iki eylem gerektirir."""
    return {"gecer": bool(gecer), "durum": durum, "olcum": olcum, "esik": esik, "neden": neden}


def faz6_kilitleri(edge: dict | None = None, sonuc: dict | None = None,
                   trio: dict | None = None) -> dict:
    """FAZ-6 (otonom intraday emir / gerçek-para silahlanma) ÖN-KOŞULU: BEŞ KİLİT.

    Kilitlerin adları ve gerekçeleri `FAZ6_KILITLERI` bloğunda yazılıdır. Dönüş SAF okumadır —
    hiçbir dosyaya yazmaz, hiçbir bayrağı çevirmez, hiçbir emir yolunu açmaz.

    ÜÇ HESAP DIŞARIDAN ENJEKTE EDİLEBİLİR (`edge`/`sonuc`/`trio`): `/api/diagnostics` bu üç hükmü
    ZATEN hesaplıyor ve aynı istekte ikinci kez hesaplamak, blok-bootstrap CI'larını iki kez
    koşturmak demek olurdu. Enjeksiyon bir gevşeklik değil: verilmezse fonksiyon kendi okur, yani
    hüküm her iki yolda AYNI kaynaktan gelir.

    FAIL-CLOSED: ölçülemeyen kilit KAPALIdır. `hepsi_acik` ancak BEŞİ de açıkken True olur."""
    from . import analytics as _an, validation as _val, dataset as _ds

    edge = _an.edge_verdict() if edge is None else edge
    sonuc = _an.result_verdict() if sonuc is None else sonuc
    trio = _an.validation_trio() if trio is None else trio

    e_n = len(edge.get("criteria") or {}) or 5
    e_p = int(edge.get("passed") or 0)
    k_edge = _kilit(e_p >= e_n and e_n > 0, "olculdu", f"{e_p}/{e_n}",
                    "EDGE hükmü: beş ölçütün BEŞİ de eşik+anlamlılık",
                    None if e_p >= e_n else (edge.get("verdict") or "edge kanıtlanmadı"))

    s_n = len(sonuc.get("criteria") or {}) or 4
    s_p = int(sonuc.get("passed") or 0)
    k_sonuc = _kilit(s_p >= s_n and s_n > 0, "olculdu", f"{s_p}/{s_n}",
                     "SONUÇ hükmü: dört DOLAR ölçütünün DÖRDÜ de sağlandı",
                     None if s_p >= s_n else (sonuc.get("verdict") or "dolar hükmü sağlanmadı"))

    # FAZ-5: 4a saha satırı SAYILIR (ölçülebilir) + dakika-hassas icranın CI'lı kazanç ÖLÇÜMÜ.
    # Önceleri bu kilit SABİT `False`/`olculemedi` yazıyordu ve gerekçesi "ölçümü ÜRETEN
    # kod yok"tu. Ölçüm artık var (`faz5_cikis.cikis_olcumu`, ön-kayıt kartı EXE-2026-002) ve kilit
    # GERÇEK bir hesaba bağlı. Kilidin kapalı kalması bir başarısızlık değil: kapalılığın GEREKÇESİ
    # "üreten kod yok"tan ölçülmüş bir cümleye ("örneklem n/20", "CI sıfırı içeriyor", "kill#4
    # eşleştirme kırılması") döndü — ikincisi zamanla kendiliğinden dolar, birincisi dolmaz.
    # HÜKÜM BURADA YENİDEN YAZILMAZ: eşikler ve kill listesi kartta donduruldu ve tek gövdede
    # (`faz5_cikis`) yaşar; ikinci bir eşik kopyası, iki hükmün sessizce ayrışması demekti.
    # GEÇ IMPORT — `edge`/`sonuc`/`trio` üçlüsüyle AYNI desen (bkz. fonksiyon başı).
    from . import faz5_cikis as _f5
    n_4a = len(store.read_jsonl("intraday_decisions.jsonl"))
    _golge = store.read_jsonl("intraday_shadow_orders.jsonl")
    # ÖLÇÜM ÇAĞRISI SARILI — gerekçe: `/api/diagnostics`
    # bu zinciri TEK `return {...}` içinde korumasız çağırıyor ve buradan sızan bir istisna
    # Operasyon sayfasının TAMAMINI karartır (sessiz_hat, watchdog, alarm bütçesi dahil — yani bir
    # şey bozukken operatörün bakacağı satırlar da onunla gider). Yakalayıcı SESSİZ DEĞİL: istisna
    # sınıfı+mesajı kilidin `neden`ine taşınır ve kilit FAIL-CLOSED kapalı kalır.
    try:
        _h = _f5.cikis_olcumu(rows=_golge)
    except Exception as _e:
        _h = {"gecer": False, "durum": "olculemedi", "olcum": None,
              "esik": f"Faz-5 çıkış ölçümü (kart {_f5.KART})",
              "neden": (f"Faz-5 çıkış ölçümü ÇAĞRIDA DÜŞTÜ: {type(_e).__name__}: {_e} — kilit "
                        "FAIL-CLOSED kapalıdır (ölçülemeyen kilit KAPALIdır)")}
    k_faz5 = _kilit(_h["gecer"], _h["durum"],
                    {"intraday_decisions_n": n_4a, "intraday_shadow_orders_n": len(_golge),
                     "cikis_olcumu": _h["olcum"]},
                    "Faz-5 çıkışı: 4a saha verisi + " + _h["esik"],
                    _h["neden"])

    armed = intraday_armed()
    k_op = _kilit(armed, "olculdu", {"intraday_arm": armed},
                  "operatör onayı: state/INTRADAY_ARM elle açık (+ 5.1 runtime ön şartı operatörde)",
                  None if armed else ("state/INTRADAY_ARM YOK — silahsız (yalnız gözlem). Hiçbir "
                                      "otomatik yol bu bayrağı açamaz"))

    # DSR: ship yolunun okuduğu AYNI hüküm fonksiyonu, `live=True` ile — silahlanma/gerçek-para
    # tarafı fail-closed'dır, yani ölçülemeyen DSR burada da KAPALI demektir.
    dsr_deger = ((trio.get("dsr_canli") or {}) or {}).get("dsr")
    dsr_h = _val.dsr_kapi(dsr_deger, live=True)
    k_dsr = _kilit(not dsr_h["ret"], dsr_h["dsr_durum"],
                   {"dsr": dsr_deger, "pencere_id": trio.get("pencere_id") or _ds.ROTATION_ID,
                    "n_trials": trio.get("n_trials")},
                   f"yürürlükteki pencerede DSR > {_val.DSR_HARD_MIN} (ölçülü ve geçer)",
                   dsr_h["neden"])

    kilitler = {"edge_kaniti": k_edge, "sonuc_hukmu": k_sonuc, "faz5_cikisi": k_faz5,
                "operator_onayi": k_op, "dsr_gecer": k_dsr}
    n_acik = sum(1 for k in kilitler.values() if k["gecer"])
    return {"kilitler": kilitler, "adlar": list(FAZ6_KILITLERI),
            # PAYDA LİSTEDEN TÜREVDİR, sabit yazılmaz: altıncı kilit eklendiğinde cümle
            # kendiliğinden düzelsin (EDGE hükmünün 4→5 dersinde payda sabit yazılmıştı ve
            # tüketiciler elle güncellenmek zorunda kaldı).
            "n_kilit": len(kilitler), "n_acik": n_acik,
            "hepsi_acik": n_acik == len(kilitler),
            "hukum": (f"FAZ-6 KİLİT ZİNCİRİ: {n_acik}/{len(kilitler)} açık — "
                      + ("BEŞİ DE AÇIK (silahlanma ön-koşulu sağlandı)" if n_acik == len(kilitler)
                         else "kapalı: " + ", ".join(a for a, k in kilitler.items()
                                                     if not k["gecer"]))),
            "rol": ("SAF OKUMA — hiçbir şey silahlamaz, hiçbir dosyaya yazmaz. Faz 4b/6 emir "
                    "bacağı yazıldığında ön-koşul kontrolü BURAYA bağlanır; bugün hiçbir kod "
                    "yolu otonom intraday emir göndermiyor"),
            "beyan": ("FAIL-CLOSED: ölçülemeyen kilit KAPALIdır. ROADMAP §5.5'in 'dört kilit' "
                      "cümlesi bu turda BEŞE çıktı (DSR) ve ilk kez makine okunur oldu — "
                      "eşikler ship yoluyla AYNI yerden (validation.DSR_HARD_MIN) gelir")}


# ---- REDDEDİLEN GÖNDERİMLERİN KAPATILMASI -------------------------------------------------------
# Operatör şikâyeti: triyaj şeridi "senden bir şey bekliyor · 4 emir reddedildi" diyordu ve o retler
# BEŞ GÜNLÜKTÜ. Kapatmanın hiçbir yolu yoktu, yani kırmızı bant sonsuza dek kalıyordu — ve KALICI
# bir kırmızı, hiç kırmızı olmamakla aynı bilgiyi taşır: kimse bakmaz. Şeridin tek işi "şu an
# müdahale gerekiyor mu?" sorusunu cevaplamaktır; geçmişte kalmış bir ret o soruya "evet" diyemez.
#
# ACK SİLMEZ, SUSTURUR (alerts_ack.json emsali): satır defterde tam alanlarıyla kalır, yalnız
# şeridi besleyen sayının dışına çıkar. "Gördüm" bir kaydı yok etmez.
#
# NEDEN BURADA: bu dosya operatörün KONTROL DURUMUNU tutar (HALT, LEARN_HALT, INTRADAY_ARM) — ack de
# tam olarak odur: dosya tabanlı, yeniden başlatmada yaşar, elle de düzenlenebilir. Yazan taraf
# api.py'dir (alerts_ack.json ile birebir aynı desen: uç YAZAR, alan modülü OKUR).
REJECT_ACK_FILE = "broker_reject_ack.json"


def reject_key(row: dict | None) -> str:
    """Bir reddin kimliği: `plan_id·date`. İkisi birlikte gerekir — aynı plan farklı seanslarda
    yeniden silahlanıp yeniden reddedilebilir ve o YENİ bir olaydır, kapatılmış olan değil."""
    r = row or {}
    return f"{r.get('plan_id') or '?'}·{r.get('date') or '?'}"


def split_rejections(rows: list | None) -> dict:
    """Reddedilen gönderimleri AÇIK / KAPATILMIŞ diye ayır — hiçbirini SİLMEDEN.

    Şeridi ve rozetleri yalnız `open` besler; `acked` pakette kalır ki pano "kapatıldı" listesini
    ack zamanıyla gösterebilsin. Tarihçenin kaybolması, sesinin kısılmasıyla aynı şey değildir."""
    ack = store.read_json(REJECT_ACK_FILE, {}) or {}
    acik, kapali = [], []
    for r in rows or []:
        kayit = ack.get(reject_key(r))
        if kayit:
            kapali.append({**r, "ack_ts": (kayit or {}).get("ack_ts")})
        else:
            acik.append(r)
    return {"open": acik, "acked": kapali}


def write_heartbeat(**fields) -> dict:
    """Nabzı güncelle. ALAN SAHİPLİĞİ (sahiplik dedektörü canlıda yakaladı): nabız TEK
    dosya ama ÇOK yazarlı — günlük döngü `regime/equity/last_bar/exposure_budget_pct` damgalar,
    replay tohumu ve worker yalnız kendi alanlarını yazar. Dosya her seferinde SIFIRDAN kurulduğu
    için ikinci yazar birincinin alanlarını sessizce siliyordu: pano "rejim yok / sermaye yok"
    gösteriyor, hiçbir istisna fırlamıyordu. Artık mevcut nabız üzerine BİNDİRİLİR.

    BİNDİRME KİLİT ALTINDA YAPILIR (2026-08-16). İlk düzeltme `read_json` + `write_json`
    çiftiydi; bu, TAM OLARAK onardığı hatanın daha dar bir penceresidir: iki yazar aynı anda
    okursa ikisi de ESKİ belgeyi görür, ikincinin yazımı birincinin alanını yine siler — yalnız
    çakışma penceresi milisaniyelere iner, kaybolmaz. Nabzın çok yazarlı olduğu bu docstring'in
    kendi konusu olduğu için "nadiren olur" bir gerekçe değildir. `store.update_json` bu iş için
    var; burada `update_json` yerine `file_lock` DOĞRUDAN kullanılıyor çünkü `update_json`
    belgeyi YERİNDE değiştirmeyi şart koşar ve diskteki nabız bozulup sözlük OLMAYAN bir değere
    dönmüşse (aşağıdaki `isinstance` kapısı) yerinde onarılamaz — o hâlde belge DEĞİŞTİRİLMEZ,
    YENİDEN KURULUR. Kilidin kapsamı ikisinde de aynıdır: oku + değiştir + yaz."""
    with store.file_lock(HEARTBEAT):
        hb = store.read_json(HEARTBEAT, {}) or {}
        if not isinstance(hb, dict):
            hb = {}
        hb.update({
            "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "mode": config.MODE,
            "autonomy_level": config.limits()["autonomy_level"],
            "halted": halted(),
        })
        hb.update(fields)
        store.write_json(HEARTBEAT, hb)
    return hb


def heartbeat_age_seconds() -> float | None:
    """Nabzın (`heartbeat.json`) `ts` damgası üstünden geçen saniye; ölçülemezse None.

    Salt-okuma. Kayıt yoksa, `ts` alanı yoksa ya da damga ayrıştırılamıyorsa UYDURMA yerine None."""
    hb = store.read_json(HEARTBEAT)
    if not hb or "ts" not in hb:
        return None
    try:
        t = dt.datetime.fromisoformat(hb["ts"])
        now = dt.datetime.now(dt.timezone.utc)
        return (now - t).total_seconds()
    except Exception:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
        return None


def stale(threshold_seconds: float = 900) -> bool:
    """Nabız eşikten eski mi? Yaş ölçülemiyorsa BAYAT sayar (fail-closed)."""
    age = heartbeat_age_seconds()
    return age is None or age > threshold_seconds


def circuit_breaker_tripped(day_pnl_pct: float, goal: dict | None = None) -> bool:
    """Günlük kayıp, hedefteki `limits.max_daily_loss_pct` tavanına ulaştıysa (ya da aştıysa) True.

    Salt-okuma karar fonksiyonu: eşiği hedef sözleşmesinden okur, hiçbir bayrak yazmaz."""
    goal = goal or config.goal()
    return day_pnl_pct <= -goal["limits"]["max_daily_loss_pct"] / 100.0
