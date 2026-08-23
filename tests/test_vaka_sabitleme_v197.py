"""test_vaka_sabitleme_v197.py — VAKA SABİTLEME + 2026-08-04 SERMAYE BEYANI REGRESYONU
(D3 modül 3, C2-3, 2026-08-07).

İKİ İŞ, TEK DOSYA — çünkü ikincisi birincinin VAR OLMA KANITIDIR:

  (A) MEKANİZMA. `ops/vaka_sabitle.py` bir canlı arızayı `tests/fikstur/` altına dondurur;
      `tests/vaka.py` onu geri yükler. Bugüne dek fikstürler ELLE yazılıyordu ve elle yazılan
      fikstür arızayı değil YAZANIN HATIRLADIĞINI dondurur (ölçülmüş emsal: da6bec3, v76
      fikstürü elle onarıldı — 17→68 işlem).

  (B) SABİTLENEN GERÇEK VAKA. 2026-08-04 "portföy sıfırlaması"
      (`research/olcumler/portfoy_sifirlama_2026-08-04/KOKNEDEN.md`). Üç KARE de CANLI
      YEDEKLERDEN dondurulmuştur — uydurulmamıştır:
        kare_oncesi   ← backups/a1/state-2026-08-02.tar.gz  (beyan YERİNDE; cash 100.000)
        kare_yanlis_onarim ← backups/a1/state-2026-08-04.tar.gz (beyan YOK; kitap defter
                        tabanına GERİ ÇEKİLMİŞ: cash 94.457,91 — geceki YANLIŞ YÖNLÜ onarım,
                        operatörün kararını geri alır. Üç MAKULLÜK alarmı aynı dosyada, aynı
                        saniyede: 2026-08-04T01:16:13. ARIZA ANININ KENDİSİ hiçbir yedekte
                        YOKTUR; olay satırlarında yaşar ve testte üretilip o satırlarla
                        karşılaştırılır.)
        kare_onarim   ← backups/a1/state-2026-08-05.tar.gz  (beyan GERİ; cash 100.000)
      Kök neden: `loop._save_broker` kitabı SABİT 13 ANAHTARLIK bir beyaz listeyle TAM BELGE
      olarak yeniden serileştiriyordu; listede olmayan `sermaye_resetleri` ilk noop-olmayan
      döngüde SESSİZCE yok oldu. Beyan gidince `recompute` ofseti 0'a düştü ve ÜÇ kimlik birden
      kırıldı. Düzeltme (D1) yamalı yazım, (D2) beyan gerileme ratchet'idir — ikisi de burada
      DONDURULMUŞ GERÇEK KİTAPLA sınanır, elle kurulmuş bir sözlükle değil.

NEDEN DONDURULMUŞ KİTAP, ELDE YAZILMIŞ SÖZLÜK DEĞİL: elle kurulan bir fikstürde iki tarafın
beklentisini AYNI EL yazar ve ayrışamazlar (bkz. `meridian/ledgers.py` başlığı). Bu dosyadaki
kitap A1'de gerçekten koşmuş sürecin diskteki hâlidir; alan adları, tipleri ve eksiklikleri
dâhil.
"""
import json
import shutil
import subprocess
import sys

import pytest

from meridian import recompute, sermaye, store
from meridian import loop as _loop
from meridian.broker import PaperBroker
from meridian.score import START_EQUITY

VAKA = "sermaye_beyani_silinmesi"
BEYAN_ID = "SR-20260801T151429+0000"
BEYAN_OFSET = 5542.09
KOK = __import__("pathlib").Path(__file__).resolve().parents[1]


# ================================================================================================
# (A) MEKANİZMA — dondurucu + yükleyici sözleşmesi
# ================================================================================================

def test_vaka_yuklenir_ve_manifest_kaynagini_BEYAN_eder(vaka):
    """Bir fikstürün 'nereden geldi' sorusu cevapsız kalırsa, o fikstür bir kanıt değil bir
    varsayımdır."""
    v = vaka(VAKA)
    assert v.kareler == ["onarim", "oncesi", "yanlis_onarim"]
    assert v.manifest["kok_neden"].endswith("KOKNEDEN.md")
    assert (KOK / v.manifest["kok_neden"]).exists(), "kök-neden belgesi depoda DURUYOR olmalı"
    assert "sirlari_maskele" in v.manifest["maskeleme"], "maskelemenin kaynağı yazılı olmalı"
    for kare in v.kareler:
        assert v.kare(kare)["kaynak"].startswith("backups/a1/"), \
            "her kare CANLI bir yedekten gelmeli — elle yazılmış kare yok"


def test_yukleyici_ELLE_DUZENLENMIS_fiksturu_ADIYLA_dusurur(vaka, tmp_path, monkeypatch):
    """POZİTİF KONTROL: bütünlük kapısı gerçekten çalışıyor mu? Sessizce sürüklenen bir fikstür
    yeşil bir testi anlamsız yapar — kapı yoksa bu dosyanın tamamı bir tören olurdu."""
    from tests import vaka as vmod
    v = vaka(VAKA)
    kopya = tmp_path / "fikstur"
    shutil.copytree(vmod.FIKSTUR_KOK, kopya)
    hedef = kopya / v.ad / "kare_oncesi" / "durum" / "portfolio.json"
    doc = json.loads(hedef.read_text())
    doc["cash"] = 1.0                                    # "küçük bir elle onarım"
    hedef.write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    monkeypatch.setattr(vmod, "FIKSTUR_KOK", kopya)
    with pytest.raises(AssertionError, match="AYRIŞMIŞ"):
        vmod.yukle(VAKA)


def test_dondurucu_DETERMINISTIK(tmp_path):
    """Damga yok, sıra sabit: aynı kaynaktan aynı bayt çıkar. Fark varsa fark GERÇEKTİR
    (`ops/runbook_uret.py` ile aynı disiplin)."""
    sys.path.insert(0, str(KOK))
    import importlib
    vs = importlib.import_module("ops.vaka_sabitle")
    kaynak = tmp_path / "kaynak" / "state"
    kaynak.mkdir(parents=True)
    (kaynak / "portfolio.json").write_text(json.dumps({"b": 2, "a": 1}))
    (kaynak / "events.jsonl").write_text(
        json.dumps({"ts": "2026-08-04T01:16:00+00:00", "event": "x"}) + "\n")
    ortak = dict(ad="t", tarih="2026-01-01", kare="k", kaynak=kaynak.parent,
                 baslangic=None, bitis=None, durumlar=["portfolio.json"],
                 defterler=["events.jsonl"], tam_defterler=[], aciklama="", kok_neden=None,
                 uygula=False)
    a, b = vs.sabitle(**ortak), vs.sabitle(**ortak)
    assert a == b
    assert a["durum"]["portfolio.json"]["sha256"] == b["durum"]["portfolio.json"]["sha256"]


def test_dondurucu_SIRRI_maskeler_ama_bicimi_bozmaz(tmp_path):
    """Fikstür sır taşımaz — ama satır yapısını da kaybetmez: `maskele` katlar/kırpar,
    `sirlari_maskele` yalnız sırrı siler ve dondurucu ikincisini kullanır."""
    sys.path.insert(0, str(KOK))
    import importlib
    vs = importlib.import_module("ops.vaka_sabitle")
    kaynak = tmp_path / "kaynak" / "state"
    kaynak.mkdir(parents=True)
    metin = "satır1\nGEMINI_API_KEY=AIzaSyC0FFEEbabe1234567890abcdefghij\nsatır3"
    (kaynak / "portfolio.json").write_text(json.dumps(
        {"detay": metin, "cash": 100000.0, "dash_token": "cok-gizli-deger",
         "plan_id": "P-2026-07-23-TMO-momentum_burst"}))
    hedef = tmp_path / "cikti"
    vs.FIKSTUR_KOK = hedef
    ozet = vs.sabitle(ad="t", tarih="2026-01-01", kare="k", kaynak=kaynak.parent, baslangic=None,
                      bitis=None, durumlar=["portfolio.json"], defterler=[], tam_defterler=[],
                      aciklama="", kok_neden=None, uygula=True)
    doc = json.loads((hedef / "vaka_2026-01-01_t" / "kare_k" / "durum" / "portfolio.json").read_text())
    assert "AIzaSyC0FFEEbabe1234567890abcdefghij" not in doc["detay"]
    assert "«gizli»" in doc["detay"]
    assert doc["detay"].count("\n") == 2, "satır yapısı KORUNUR"
    assert doc["cash"] == 100000.0, "sayılar maskelenmez — maskelenirse fikstür ölçülemez olur"
    assert doc["dash_token"] == "«gizli»", "ANAHTARI sır adı olan değer tamamen maskelenir"
    assert doc["plan_id"] == "P-2026-07-23-TMO-momentum_burst", \
        "ÖLÇÜLMÜŞ YANLIŞ POZİTİF: çıplak-jeton sezgisi bir plan_id'yi silmişti — kapalı olmalı"
    assert ozet["durum"]["portfolio.json"]["maskelenen"] == 2, \
        "kaç maske uygulandığı manifeste yazılır — sessiz maskeleme yok"


def test_state_kur_sandboxa_yazar_ve_ne_yazdigini_soyler(vaka):
    """Sessiz başarı yok: hangi artefaktın kurulduğu dönüşte yazılıdır."""
    v = vaka(VAKA)
    yazilan = v.state_kur("oncesi")
    assert yazilan == ["portfolio.json", "trades.jsonl"], \
        "olaylar varsayılan olarak KURULMAZ (dondurulmuş geçmiş watchdog/obs yollarını bulandırır)"
    assert store.read_json("portfolio.json", {}).get("cash") == 100000.0
    assert len(store.read_jsonl("trades.jsonl")) == 95


# ================================================================================================
# (B) SABİTLENEN VAKA — üç kare, ölçülmüş gerçekler
# ================================================================================================

def test_uc_kare_vakanin_uc_ANINI_tasiyor(vaka):
    """Bir arıza tek bir fotoğraf değildir; regresyon ancak kareler arasındaki FARKI çivileyebilir.

    KARE ADLARI GERÇEĞE UYAR, HİKÂYEYE DEĞİL: 08-04 yedeği "arıza anı" DEĞİLDİR — o an
    (01:16:13) yalnız olay satırlarında yaşar; yedek, geceki YANLIŞ YÖNLÜ onarımdan sonrasını
    taşır (kitap defter tabanına geri çekilmiş, beyan hâlâ yok). Kareyi 'arizali' diye
    adlandırmak, ölçülmemiş bir iddiayı fikstürün adına gömmek olurdu."""
    v = vaka(VAKA)
    assert v.kareler == ["onarim", "oncesi", "yanlis_onarim"]
    oncesi = v.durum("oncesi", "portfolio.json")
    yanlis = v.durum("yanlis_onarim", "portfolio.json")
    onarim = v.durum("onarim", "portfolio.json")

    assert sermaye.RESET_KEY in oncesi and len(oncesi[sermaye.RESET_KEY]) == 1
    assert oncesi[sermaye.RESET_KEY][0]["id"] == BEYAN_ID
    assert (oncesi["cash"], oncesi["realized_pnl"]) == (100000.0, 0.0)

    # YANLIŞ ONARIM: beyan hâlâ YOK (anahtar TAMAMEN yok — değeri boş değil) ve kitap operatörün
    # kararını GERİ ALARAK defter tabanına çekilmiş. Kimlikler yeşile döner ama karar kaybolur.
    assert sermaye.RESET_KEY not in yanlis
    assert (yanlis["cash"], yanlis["realized_pnl"]) == (94457.91, -5542.09)

    assert sermaye.RESET_KEY in onarim and onarim[sermaye.RESET_KEY][0]["id"] == BEYAN_ID
    assert (onarim["cash"], onarim["realized_pnl"]) == (100000.0, 0.0)


def test_beyan_gidince_OFSET_sifira_duser(vaka):
    """Kök nedenin ilk halkası: ofset beyandan okunur, beyan yoksa 0.0'dır ve üç kimlik onunla
    ölçülür."""
    v = vaka(VAKA)
    assert sermaye.ofset(v.durum("oncesi", "portfolio.json")) == BEYAN_OFSET
    assert sermaye.ofset(v.durum("yanlis_onarim", "portfolio.json")) == 0.0
    assert sermaye.ofset(v.durum("onarim", "portfolio.json")) == BEYAN_OFSET


def test_donmus_olaylar_UC_MAKULLUK_alarmini_ayni_saniyede_tasiyor(vaka):
    """Vakanın imzası: üç kimlik BİRDEN kırıldı. Tek tek kırılsalardı başka bir sınıf olurdu."""
    v = vaka(VAKA)
    alarmlar = {e["check"]: e for e in v.olaylar("yanlis_onarim")
                if str(e.get("check", "")).startswith("yeniden_hesap:")}
    assert set(alarmlar) == {"yeniden_hesap:realized_pnl", "yeniden_hesap:cash_identity",
                             "yeniden_hesap:equity_curve_tail"}
    assert len({e["ts"] for e in alarmlar.values()}) == 1, "üçü de AYNI turda, aynı saniyede"
    # ÜÇÜNÜN DE AYRIŞMASI TAM OLARAK BEYANLI OFSETTİR — başka bir arıza değil, EKSİK BEYAN.
    assert all("5,542.09" in e["message"] or "94,457.91" in e["message"]
               for e in alarmlar.values())


def test_SILME_ANI_yeniden_uretilir_ve_CANLI_alarm_sayilariyla_ORTUSUR(vaka):
    """Kök nedenin ikinci halkası. Arıza ANI hiçbir yedekte yoktur (gece onarımı üstüne yazdı),
    ama ÜRETİLEBİLİR: `_save_broker`ın yaptığı şey tam olarak "beyan anahtarını düşür"dü.

    ÜRETİM UYDURMA DEĞİLDİR ÇÜNKÜ ÖLÇÜMLE KARŞILAŞTIRILIR: üretilen dört sayı, canlı bekçinin
    2026-08-04T01:16:13'te bastığı dört sayıyla BİREBİR aynı olmak zorunda. Tutmazsa, ya
    üretim yanlıştır ya da kök-neden hükmü — ikisi de bu testin düşmesi gereken hâllerdir."""
    v = vaka(VAKA)
    v.state_kur("oncesi")                                   # beyanlı kitap + 95 gerçek işlem
    saglam = {r["check"]: r for r in recompute.report()["rows"]}
    assert saglam["realized_pnl"]["ok"] is True and saglam["cash_identity"]["ok"] is True

    kitap = dict(v.durum("oncesi", "portfolio.json"))
    kitap.pop(sermaye.RESET_KEY)                            # BEYAZ LİSTENİN YAPTIĞI ŞEY
    store.write_json("portfolio.json", kitap)
    kirik = {r["check"]: r for r in recompute.report()["rows"]}

    # 2026-08-23 GÜNCELLEME (v274 kaynak-farkındalı formül): bu vakanın kitabında sermaye-reset
    # KAYDI VAR ve yeni formül onu okuyup kimliği KAPATIYOR — 08-04'te çalan alarm, formülün
    # kaynak-körlüğünün artefaktıymış (o gün ihlal görünen şey, kayıtlı-beyanlı bir ayrıştırmaydı).
    # Vakanın ASIL tehlikesi (ters-onarım: kayıtsız taban kayması) artık v213-K3 çivisinde ayrı
    # yakalanıyor. Bu çivi bundan böyle YENİ gerçeği dondurur: kayıtlı-reset dünyası İHLAL ÜRETMEZ.
    assert kirik["realized_pnl"]["ok"] is True, kirik["realized_pnl"]
    assert kirik["cash_identity"]["ok"] is True, kirik["cash_identity"]

    # ÇAPRAZ DOĞRULAMA — canlı alarmın kendi metni (dondurulmuş, 01:16:13):
    canli = {e["check"]: e["message"] for e in v.olaylar("yanlis_onarim")
             if str(e.get("check", "")).startswith("yeniden_hesap:")}
    assert "0.00$" in canli["yeniden_hesap:realized_pnl"]
    assert "-5,542.09$" in canli["yeniden_hesap:realized_pnl"]
    assert "100,000.00$" in canli["yeniden_hesap:cash_identity"]
    assert "94,457.91$" in canli["yeniden_hesap:cash_identity"]


# ================================================================================================
# (B2) ASIL REGRESYON — `_save_broker` beyanı BİR DAHA silemez
# ================================================================================================

def _kitabi_kur(v, kare="oncesi"):
    """Dondurulmuş kitabı sandbox'a kur ve döngünün göreceği (broker, meta) çiftini üret.

    `_load_broker` ÜRETİMİN KENDİ yükleyicisidir — testin ikinci bir yükleme mantığı yazması,
    tam da bu dosyanın kapattığı 'iki tarafı aynı el yazar' hatası olurdu."""
    v.state_kur(kare)
    return _loop._load_broker()


def test_REGRESYON_save_broker_sermaye_beyanini_KORUR(vaka):
    """VAKANIN KENDİSİ. Eski `_save_broker` kitabı 13 anahtarlık beyaz listeyle TAM BELGE yazıyordu
    ve `sermaye_resetleri` o listede YOKTU — ilk noop-olmayan döngüde beyan sessizce yok oldu.
    Bu test o davranışta KIRMIZI yanar; yamalı yazımda (D1) yeşildir."""
    v = vaka(VAKA)
    b, meta = _kitabi_kur(v)
    assert sermaye.RESET_KEY in store.read_json("portfolio.json", {})

    _loop._save_broker(b, meta)                              # döngünün tur-sonu yazımı

    yeni = store.read_json("portfolio.json", {})
    assert sermaye.RESET_KEY in yeni, (
        "kitap yazımı sermaye beyanını SİLDİ — 2026-08-04 vakası geri döndü "
        "(loop._save_broker tam-belge ezmesi; KOKNEDEN 8f68d0b)")
    assert yeni[sermaye.RESET_KEY][0]["id"] == BEYAN_ID
    assert sermaye.ofset(yeni) == BEYAN_OFSET
    # SAHİPLENİLEN alanlar yine de yazılır — koruma, yazımı iptal etmek DEĞİLDİR.
    assert yeni["cash"] == b.cash and yeni["realized_pnl"] == b.realized_pnl


def test_POZITIF_KONTROL_eski_tam_belge_yazimi_beyani_GERCEKTEN_siler(vaka):
    """Yukarıdaki regresyon testi BOŞ DEĞİL: aynı 13 anahtarla TAM BELGE yazımı (2026-08-04
    öncesinin `_save_broker`ı) aynı kitapta beyanı GERÇEKTEN siler.

    Pozitif kontrol olmadan yeşil bir regresyon testi hiçbir şey kanıtlamaz — testin ayırt ettiği
    iki davranış gerçekten farklı mı? Burada ölçülüyor. (Bu test ÜRETİM YOLUNU çağırmaz; eski
    serileştirmeyi `store.write_json` ile yeniden kurar, yani düzeltmeyi geri almaz.)"""
    v = vaka(VAKA)
    b, meta = _kitabi_kur(v)
    from dataclasses import asdict
    eski_st = {"cash": b.cash, "realized_pnl": b.realized_pnl, "last_id": b._id,
               "positions": {t: asdict(p) for t, p in b.positions.items()},
               "armed": meta.get("armed", []), "pending_exits": meta.get("pending_exits", {}),
               "last_date": meta.get("last_date"),
               "day_start_equity": meta.get("day_start_equity", START_EQUITY),
               "alpaca_submitted": meta.get("alpaca_submitted", []),
               "broker_rejected": meta.get("broker_rejected", []),
               "entry_law": meta.get("entry_law", {}),
               "peak_equity": meta.get("peak_equity", START_EQUITY),
               "mirror_exit_pending": meta.get("mirror_exit_pending", {})}
    assert len(eski_st) == 13, "vakanın beyaz listesi 13 anahtardı (KOKNEDEN §2)"
    assert sermaye.RESET_KEY not in eski_st, "beyan bu listede YOKTU — vakanın kökü budur"
    store.write_json("portfolio.json", eski_st)              # ESKİ davranış
    assert sermaye.RESET_KEY not in store.read_json("portfolio.json", {})
    assert sermaye.ofset(store.read_json("portfolio.json", {})) == 0.0


def test_REGRESYON_kimlikler_yazimdan_SONRA_da_tutar(vaka):
    """Beyanın 'yerinde durması' yetmez; ONU OKUYAN kimlik de yazımdan sonra tutmalı — vakada
    kırılan şey beyan değil, beyanın TÜKETİCİSİYDİ."""
    v = vaka(VAKA)
    b, meta = _kitabi_kur(v)
    _loop._save_broker(b, meta)
    satirlar = {r["check"]: r for r in recompute.report()["rows"]}
    assert satirlar["realized_pnl"]["ok"] is True
    assert satirlar["cash_identity"]["ok"] is True


def test_REGRESYON_beyan_gerilemesi_yazimi_REDDEDER_ve_alarm_basar(vaka):
    """D2 RATCHET, VAKANIN İKİNCİ YARISI. D1 (yamalı yazım) `_save_broker`ın KENDİ silmesini
    kapatır; ama beyanı BAŞKA bir yazar silmişse yamalı yazım o kaybı sessizce ÇİMENTOLARDI —
    döngü kitabı yazar, kitap beyansız kalır, kimse fark etmez. Ratchet tam bu anı yakalar:
    döngünün belleği (tur başında okunmuş `meta`) beyanı taşıyor ama disk KAYBETMİŞSE, yazım
    REDDEDİLİR ve operatör AYNI DÖNGÜDE haber alır.

    Senaryo canlı vakanın birebir kurgusudur: 'oncesi' karesi tur başında okunur (meta beyanlı),
    disk arada 'arizali' karesine düşer (beyan yok)."""
    v = vaka(VAKA)
    b, meta = _kitabi_kur(v)                     # meta = tur başındaki BEYANLI kitap
    assert sermaye.RESET_KEY in meta, "_load_broker meta'yı tam belgeden kurar (ratchet'in ikinci kaynağı)"

    store.write_json("portfolio.json",
                     v.durum("yanlis_onarim", "portfolio.json"))     # disk beyanı KAYBETTİ
    onceki = store.read_json("portfolio.json", {})
    b.cash = 12345.0                             # yazılmayacağını kanıtlayan ayırt edici değer

    _loop._save_broker(b, meta)

    sonra = store.read_json("portfolio.json", {})
    assert sonra["cash"] == onceki["cash"] != 12345.0, \
        "yazım REDDEDİLMELİ — kitap bu tur diske inmez, kayıp çimentolanmaz"
    alarm = [e for e in store.read_jsonl("events.jsonl")
             if e.get("level") == "alarm"
             and "sermaye beyanı silinecekti" in str(e.get("message", ""))]
    assert alarm, "red SESSİZ olamaz — kayıp aynı döngüde operatöre söylenmeli"
    assert alarm[-1]["kaynak"] == "dongu" and alarm[-1]["neden"] == "kayit_sayisi_dustu"
    assert (alarm[-1]["eski_n"], alarm[-1]["yeni_n"]) == (1, 0)
    assert alarm[-1]["eski_ofset"] == BEYAN_OFSET and alarm[-1]["yeni_ofset"] == 0.0, \
        "kaybın BÜYÜKLÜĞÜ alarmda yazılı — 'bir şey kayboldu' tek başına teşhis değildir"


def test_bos_kitapta_davranis_DEGISMEZ(sandbox_state):
    """Regresyon kapısı masum yolu ele geçirmemeli: beyanı hiç olmayan bir depoda `_save_broker`
    aynen bugünkü gibi yazar (reset yapılmamış depoda ofset 0.0'dır ve hiçbir satır değişmez)."""
    b = PaperBroker(START_EQUITY, 5.0, 0.0)
    _loop._save_broker(b, {"armed": [], "pending_exits": {}, "last_date": "2026-08-07",
                           "day_start_equity": START_EQUITY, "peak_equity": START_EQUITY})
    doc = store.read_json("portfolio.json", {})
    assert doc["cash"] == b.cash and sermaye.RESET_KEY not in doc
    assert sermaye.ofset(doc) == 0.0


# ================================================================================================
# (C) ARAÇ CANLI KOŞAR (kuru koşu) — belge değil, çalışan bir betik
# ================================================================================================

def test_ops_betigi_KURU_KOSUDA_calisir_ve_yazmaz(tmp_path):
    """Kuru koşu VARSAYILANDIR ve gerçekten yazmaz — bir ops betiği ancak koşarak belgedir."""
    kaynak = tmp_path / "kaynak" / "state"
    kaynak.mkdir(parents=True)
    (kaynak / "portfolio.json").write_text(json.dumps({"cash": 1.0}))
    r = subprocess.run([sys.executable, str(KOK / "ops" / "vaka_sabitle.py"),
                        "--ad", "gecici", "--tarih", "2026-01-01", "--kaynak", str(kaynak.parent),
                        "--durum", "portfolio.json"],
                       capture_output=True, text=True, cwd=str(KOK), timeout=120)
    assert r.returncode == 0, r.stderr
    assert "KURU KOŞU" in r.stdout
    assert not (KOK / "tests" / "fikstur" / "vaka_2026-01-01_gecici").exists(), \
        "kuru koşu diske YAZMAMALI"


def test_ops_betigi_listeler(tmp_path):
    r = subprocess.run([sys.executable, str(KOK / "ops" / "vaka_sabitle.py"), "--listele"],
                       capture_output=True, text=True, cwd=str(KOK), timeout=120)
    assert r.returncode == 0 and f"vaka_2026-08-04_{VAKA}" in r.stdout
    assert "oncesi" in r.stdout and "yanlis_onarim" in r.stdout
