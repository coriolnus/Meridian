#!/usr/bin/env python3
"""oneri_brifingi.py — okunmamış İYİLEŞTİRME ÖNERİLERİNİN tek-mesajlık özeti.

NEDEN VAR (2026-08-27 ölçümü). `nous_eval.py` (1098 satır) telemetriden kanıt-atıflı yapısal
öneriler üretiyor ve `state/improvement_proposals.jsonl`a yazıyor — canlıda 16 öneri, sonuncusu
24 Ağustos. TESLİMAT YOLU YOK: hiçbir kod bu defteri okuyup operatöre iletmiyor. Sistem
düşünüyor ve kimse dinlemiyor.

ŞEKİL `alarm_backlog_digest.py`den KOPYALANDI ve bu bilinçlidir: kuru koşum varsayılan ·
boşken SESSİZ · teslimden sonra damga · teslim düşerse damga BASILMAZ (yarım teslim "teslim
edildi" sayılmaz). O şekil bu depoda zaten sınanmış; ikinci bir tasarım ikinci bir hata sınıfıdır.

OKUR: `state/improvement_proposals.jsonl` — ve ona ASLA YAZMAZ (öneri satırlarına dokunulmaz).
İKİNCİ OKUMA (2026-08-31, akıbet defteri dalgası Görev 2): `state/oneri_akibet.jsonl` — öneri
akıbet defteri; ona da ASLA YAZILMAZ (yazan taraf `ops/akibet.py`dir ve o A1'e uzaktan, `flock`
altında yazar). Bu betik defterin YANINDA koşar (A1), o yüzden okuma YEREL dosyadandır: ssh YOK.
İki dosya TEK GERÇEĞİN İKİ YARISIDIR (kopya değil): öneri defteri DOĞUMU, akıbet defteri
KARAR/SONUÇ zincirini taşır. Türetim `ops/akibet.py::akibet_turet` (SAF çekirdek) ile yapılır —
"açık öneri" tanımı bu betikte İKİNCİ KEZ yazılmaz.
YAZAR (denetim 2026-08-29 düzeltmesi — bu satır kardeş betikten kopyalanmış ve "aynı dosyanın
DAMGA anahtarı" diyordu; YANLIŞTI, o `alarm_backlog_digest.py`nin şeklidir): damga AYRI bir
dosyada tutulur, `state/oneri_brifingi_damga.json` (`DAMGA_DOSYA`) — okunan defter JSONL'dir,
içine bir damga anahtarı KOYULAMAZ. İkinci yazım `state/events.jsonl`dir (`obs.log` ile
`oneri_brifingi_teslim` olayı). Teslimat: `meridian.notify.send` (scrub + teslim-hatası kaydı orada).

DAMGA SÖZLEŞMESİ DEĞİŞMEDİ (akıbet dalgası, BAĞLAYICI): damga hâlâ TEK bir zaman damgasıdır
(`son_ts`), hâlâ yalnız ÖNERİ satırlarından ilerler ve hâlâ yalnız teslimattan SONRA basılır.
Akıbet katmanı damgaya hiçbir anahtar EKLEMEZ — ikinci bir damga, "hangi kaynak nereye kadar
bildirildi" sorusunu ölçülemez hâle getirirdi.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ops/ altından doğrudan koşulduğunda `meridian` paketi bulunabilsin. Bugün canlıda editable
# kurulum (`_editable_impl_meridian.pth`) bunu zaten sağlıyor — ama kardeş betik
# (`alarm_backlog_digest.py`) bu satırı taşıyor ve ikisini AYNI birim koşturuyor: bootstrap yalnız
# birinde olsaydı yeniden kurulmuş/bozulmuş bir .venv kadansın YARISINI öldürür, öteki yarısı
# çalışmaya devam ederdi — teşhis edilmesi en zor arıza şekli.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from meridian import config, memory, notify, obs, store  # noqa: E402
from ops import akibet as _akibet  # noqa: E402

DEFTER = "improvement_proposals.jsonl"
DAMGA_DOSYA = "oneri_brifingi_damga.json"
DAMGA = "son_teslim"
LISTE_TAVANI = 8          # mesaj uzunluk zarfı — kalanlar sayıyla beyan edilir

# AKIBET DEFTERİNİN ADI, TEK KAYNAKTAN TÜRETİLİR — ikinci bir yol sabiti YAZILMAZ (tek-kaynak
# yasası: aynı gerçeğin iki kopyası sessizce ayrışır). `ops/akibet.py::DEFTER` MUTLAK yazılmıştır
# çünkü o araç `meridian`i ithal EDEMEZ (kendi `obs`una ulaşıp canlı deftere yazmasın diye).
# BURADA `config` VAR: aynı dosya `state/` altındaki ADIYLA okunur — A1'de `config.STATE`
# `/opt/meridian/state`tir, yani ADRES AYNI dosyadır; testlerde sandbox'a düşer (çivi canlı
# dosyaya bakamaz). Türetimin GEÇERLİLİK ŞARTI — defterin `state/` dizininde durması — ayrıca
# çivilenir: akibet.py yolu bir gün taşırsa bu okuma sessizce YANLIŞ dosyaya bakardı.
AKIBET_DEFTER = Path(_akibet.DEFTER).name

# OPERATÖR DİLİ (v323 disiplini): defterdeki değer ASCII bir KİMLİKTİR, brifingde okunacak cümle
# değil. Türkçe karşılık ölçülemez, o yüzden burada YAZILIR — ama `ops/akibet.py`nin sabitlerine
# KARŞI DENETLENİR (çivi): yeni bir karar değeri/karar vereni eklenip burası unutulursa, brifing
# ham kimliği basmaya başlar ve bunu kimse görmez.
KARAR_SOZCUKLERI = {"uygulandi": "uygulandı", "reddedildi": "reddedildi", "ertelendi": "ertelendi"}
VEREN_SOZCUKLERI = {"operator": "operatör", "rol1": "Rol-1"}


def _ts_degeri(row: dict) -> str:
    """Satırın KULLANILABİLİR zaman damgası; alan yoksa/boşsa "" (UYDURULMAZ — ölçülemedi
    sayılır, bir şey İCAT edilmez)."""
    return str(row.get("ts") or "").strip()


def _akibet_defteri() -> tuple[list[dict] | None, str | None]:
    """`(defter_satirlari, olculemedi_nedeni)` — tam biri doludur.

    DEFTER YOKSA BU BİR ARIZA DEĞİL, ÖLÇÜLMÜŞ BİR DURUMDUR: henüz hiç karar yazılmamışsa dosya
    doğmamıştır ve o gün gerçekten "herkes açık"tır — boş liste bunu DOĞRU söyler. Dosya VAR ama
    okunamıyorsa (izin, bozuk kodlama, disk) bu SIFIR DEĞİL BİLMİYORUM'dur: neden çağırana taşınır
    ve brifingde ADIYLA basılır. İkisini aynı boşluğa çöktürmek, bir izin hatasını "hiç karar
    verilmemiş" diye okumak olurdu (aynı ayrımı `ops/akibet.py` uzak okumada da yapar).

    Satırlar `akibet._jsonl_satirlari` ile ayrıştırılır, `json.loads` ile DEĞİL: çözülemeyen satır
    DÜŞÜRÜLMEZ, yerine boş sözlük konur ve `akibet_turet` onu `olculemeyen`e sayar. Kendi
    ayrıştırıcımızı yazmak o sözleşmenin ikinci bir kopyası olurdu — ve o kopya, bozuk satırı
    sessizce atan bir kopya olurdu."""
    yol = config.STATE / AKIBET_DEFTER
    try:
        if not yol.exists():
            return [], None
        return _akibet._jsonl_satirlari(yol.read_text(encoding="utf-8")), None
    except (OSError, UnicodeDecodeError) as e:
        return None, f"{type(e).__name__}: {e}"


def _karar_bildirilecek_mi(karar: dict, son_ts: str) -> bool:
    """Bu karar satırı SON DAMGADAN BERİ mi yazıldı?

    Kıyas GERÇEK zamanladır (`akibet._ts_sira_anahtari`), dizgeyle değil — farklı UTC ofsetli iki
    damgada dizge sırası kronolojiyle çelişebilir.

    ZAMANI ÇÖZÜLEMEYEN KARAR KOŞULSUZ BİLDİRİLİR ve bu bu dosyanın KURULU disiplinidir (ts'siz
    öneri satırı da koşulsuz `yeni`ye girer): bilinmeyen bir an "damgadan önce" SAYILAMAZ, aksi
    hâlde o karar hiçbir turda görünmezdi — kalıcı sessiz kayıp. Cümlede ölçülemediği işaretlenir."""
    if _akibet._ts_ayristir(karar.get("ts")) is None:
        return True
    return _akibet._ts_sira_anahtari(karar["ts"]) > _akibet._ts_sira_anahtari(son_ts)


def _oneri_metinleri(satirlar: list[dict], defter_satirlari: list[dict]) -> dict:
    """`oneri_id` → önerinin METNİ (R1/Kü3).

    NEDEN YEREL BİR HARİTA. `akibet_turet` metni yalnız `acik` kaleminde verir — oysa karara
    BAĞLANAN öneri tanımı gereği artık açık DEĞİLDİR, yani karar bloğuna metin oradan gelemez;
    `kararlar` şeması ise metin taşımıyor ve DONUK (T1 sözleşmesi). İki brifing arasında doğup
    karara bağlanan bir öneri, metni olmadan operatöre yalnız bir KİMLİK olarak ulaşırdı —
    "kaybolmaz, yer değiştirir" iddiası tam da orada yarım kalırdı.

    Doğumun İKİ kaynağı da taranır (öneri defteri N-serisi + akıbet defterinin doğum satırları),
    çünkü açıklığın tanımı da o iki yarıdan türer. Bu, `akibet_turet`in doğum haritasının küçük
    bir kopyasıdır ve KAÇINILMAZDIR: dönüş şeması metni yüzeye çıkarmıyor ve şema donuk."""
    metinler: dict = {}
    for r in satirlar:
        if isinstance(r, dict) and r.get("id") is not None:
            metinler[r["id"]] = r.get("oneri")
    for r in defter_satirlari:
        if isinstance(r, dict) and r.get("olay") == "oneri" and r.get("oneri_id") is not None:
            metinler[r["oneri_id"]] = r.get("oneri")
    return metinler


def _kimlik(deger) -> str:
    """Operatör metnine giren KİMLİK (R2/Y4).

    YAZILMAMIŞ KİMLİK `None` DİYE BASILMAZ: Python literali kullanıcı metni değildir (v323; bu
    dosyanın kendi çivisi `e11b` o kelimeyi zaten yasaklıyor) ve bu satırın var oluş sebebi tam
    tersidir — kimliksiz satır GÖRÜNÜR kalsın diye `kapali` kümesinden `None` ayıklandı (Ö2).
    Görünürlüğü kazanıp okunabilirliği kaybetmek yarım düzeltme olurdu. Ev dilinde söylenir;
    kimlik UYDURULMAZ. Üç yüzeyin (yeni · karar · yaş satırı) TEK uygulaması."""
    return "kimliği yazılmamış" if deger is None else str(deger)


def _karar_cumlesi(karar: dict, metinler: dict) -> str:
    """Bir karar satırının operatör cümlesi. Alan adı/backtick TAŞIMAZ (v323): okuyan kişi
    defterin şemasını bilmek zorunda değildir. Eksik alan UYDURULMAZ, söylenir; bilinmeyen konu
    metni ise SESSİZCE atlanır (uydurulmuş bir konu, konusuzluktan beterdir)."""
    hangi = KARAR_SOZCUKLERI.get(karar.get("karar"), str(karar.get("karar")))
    veren = VEREN_SOZCUKLERI.get(karar.get("karar_veren"),
                                 str(karar.get("karar_veren") or "kimin verdiği yazılmamış"))
    zaman_uyari = "" if _akibet._ts_ayristir(karar.get("ts")) is not None else " [tarihi ölçülemedi]"
    konu_metni = str(metinler.get(karar.get("oneri_id")) or "").strip()
    konu = f" (konu: {konu_metni[:60]})" if konu_metni else ""
    gerekce = str(karar.get("gerekce") or "").strip()
    kuyruk = f": {gerekce[:90]}" if gerekce else " (gerekçe yazılmamış)"
    return f"· {_kimlik(karar.get('oneri_id'))}{konu} {hangi} — {veren}{zaman_uyari}{kuyruk}"


def _karar_secimi(kararlar: list[dict]) -> tuple[list[dict], int]:
    """Zarfa girecek kararlar + gösterilmeyen sayısı (R2/Y1).

    İKİ KURALIN ÇELİŞTİĞİ YER BURASIYDI. `kararlar` artan gerçek zamanla sıralıdır ve tarihi
    ÇÖZÜLEMEYENLER en başta durur (`akibet._ts_sira_anahtari` kutbu). Kü2 taşmada baştan değil
    SONDAN kesmeyi getirmişti (en yeniler görünsün diye) — ama o kesim, tarihi ölçülemeyen
    kararları taşma olan HER turda kesilen tarafta bırakıyordu; oysa `_karar_bildirilecek_mi`
    onları "hiçbir turda görünmesinler" diye KOŞULSUZ bildiriyor. İki kural aynı anda ancak
    ÖNCELİK sırasıyla tutulabilir: önce tarihi ölçülemeyenler (koşulsuz bildirim garantisi),
    kalan slotlar en YENİ kararlara.

    Tarihi ölçülemeyenler tavanı tek başına doldurursa onlar da kesilir — ama o zaman kesilen
    taraf da AYNI sınıftır, yani sistematik bir ayrımcalık kalmaz."""
    bozuk = [k for k in kararlar if _akibet._ts_ayristir(k.get("ts")) is None]
    saglam = [k for k in kararlar if _akibet._ts_ayristir(k.get("ts")) is not None]
    kalan = LISTE_TAVANI - len(bozuk)
    if kalan <= 0:
        gosterilen = bozuk[:LISTE_TAVANI]
    else:
        gosterilen = bozuk + saglam[-kalan:]
    return gosterilen, len(kararlar) - len(gosterilen)


def _yas_satiri(acik: list[dict], ertelenen: int = 0) -> str:
    """Açık önerilerin TEK KOMPAKT satırı: "3 açık: N00005 21g · N00012 9g · AKB-0003 2g".

    SIRA `akibet_turet`ten GELDİĞİ GİBİ korunur (en eski önce) — burada yeniden sıralamak, aynı
    sıralama kuralının ikinci bir kopyası olurdu. Yaşı ölçülemeyen kalem gizlenmez: sayı
    uydurmak yerine ölçülemediği yazılır. Zarf için tavan uygulanır ve DÜŞEN sayı beyan edilir.

    ERTELENENLER BURADA SAYILIR (R1/Kü4). "Sonra bakarız" denen öneri açık SAYILMAZ (tanım,
    brief) ve karar bloğunda da yalnız damga ilerleyene kadar görünür — yani başka hiçbir yüzeyi
    olmadan sistemin TAMAMINDAN kaybolurdu. Tam da bu kadansın var oluş sebebi olan "unutulan
    öneri" sınıfı. Sayı `akibet_turet`in kendi sayacından gelir, yeniden hesaplanmaz.

    "AÇIK ÖNERİ YOK" DALI GERÇEKTEN ERİŞİLİR (R2/Y5): çağıran bu satırı mesaj üretilen HER turda
    ekler, `acik` boş olsa bile. Kapı koşullu olsaydı bu dal ölü kalırdı — ve dahası, yığının
    BOŞALDIĞI gün (her şey karara bağlandı) operatör bunu hiçbir yerde görmezdi; oysa o, bu
    kadansın anlatabileceği en iyi haberdir."""
    ek = (f" · ayrıca {ertelenen} ertelenmiş öneri var (açık sayılmıyor)" if ertelenen else "")
    if not acik:
        return f"📌 açık öneri yok{ek}"
    parcalar = []
    for a in acik[:LISTE_TAVANI]:
        yas = a.get("yas_gun")
        parcalar.append(f"{_kimlik(a.get('oneri_id'))} {yas}g" if isinstance(yas, int)
                        else f"{_kimlik(a.get('oneri_id'))} yaşı ölçülemedi")
    kuyruk = f" · … +{len(acik) - LISTE_TAVANI} daha" if len(acik) > LISTE_TAVANI else ""
    return f"📌 {len(acik)} açık: " + " · ".join(parcalar) + kuyruk + ek


def _olculemedi_cumlesi(ham_sayim: int, neden: str) -> str:
    """Akıbet katmanı ölçülemediğinde `@sef`in DÜŞMEYEN kanalına giden cümle (R1/Ö1).

    İKİ KATMANLI (v323 sözleşmesi, R1/Kü1): önce operatörün okuduğu İNSAN CÜMLESİ — iç ayrıntı
    yok; sonra `Teşhis:` etiketiyle AYRILMIŞ teknik katman (istisna metni, dosya yolu). Eskiden
    ham istisna dizgesi cümlenin ortasındaydı ve operatör metnine mutlak yol + Python sınıf adı
    sızıyordu.

    "Ham sayım" karara bağlananlar AYIKLANMADAN yapılan sayımdır — sıfırla karıştırılmasın diye
    ne yapılamadığı tek tek söylenir."""
    return (f"akıbet ölçülemedi — ham sayım: {ham_sayim}. Karara bağlananlar ayıklanamadı, açık "
            f"listesi çıkarılamadı; öneri listesi bu tur teslim edilmedi (damga basılmaz, "
            f"yarın yeniden denenir). Teşhis: {neden[:200]}")


def ozet_kur() -> dict:
    """(toplam, yeni, mesaj, not, en_yeni, acik_sayi, akibet_olculemedi). `mesaj` boşsa teslim
    edilecek bir şey YOKTUR.

    AKIBET KATMANI (2026-08-31). Mesaj artık ÜÇ blok taşır: `yeni` (son damgadan beri doğan,
    mevcut damga mekanizması) · karara bağlananlar (son damgadan beri yazılan karar satırları,
    birer cümle) · açık yaş satırı (mesaj üretilen HER turda, tek kompakt satır). KARARA BAĞLANMIŞ
    BİR ÖNERİ `yeni` LİSTESİNE BİR DAHA GİRMEZ — bu betiğin var oluş sebebindeki kusur tam olarak
    buydu: sef her brifingde aynı "16 yeni öneri"yi tekrarlıyordu çünkü karara bağlanmış bir
    önerinin bunu söyleyecek hiçbir yeri yoktu.

    AÇIKLIK ÖLÇÜLÜR, VARSAYILMAZ: defter yoksa/boşsa herkes açıktır (ölçülmüş açıklık); defter
    okunamıyorsa akıbet ÖLÇÜLEMEDİ sayılır ve bu `hata` ANAHTARIYLA döner (R1/Ö1).

    NEDEN `hata` (ve neden `mesaj` İÇİNDE BİR SATIR DEĞİL). `@sef`in İKİ kanalı EŞİT DEĞİLDİR:
    `mesaj` kanalı LLM dalında MODELİN kalemindedir (SOUL kalem tavanı 3) ve zarf taşmasında
    tamamen düşebilir; `hata` kanalı `_kaynak_oku` üzerinden `olculemeyen`e girer ve orada
    ZORUNLU parçadır — üstelik prompt modele "bunları SUSTURAMAZSIN" der (çivisi
    `test_sef_brifingi_v330.py::test_LLM_OLCULEMEYEN_KAYNAGI_SUSTURAMAZ`). Ölçüm zincirinin
    kırıldığının beyanı bir ÖNCELİK YARGISI değildir; susturulabilir bir kanaldan gidemez.
    BEDELİ ÖLÇÜLDÜ ve KABUL EDİLDİ: o tur öneri LİSTESİ teslim edilmez. Kayıp değildir —
    `olculemeyen` kaynağı damgalanmaz, yani liste ertesi turda yeniden bildirilir; defter
    onarılana kadar operatör her gün arızayı görür. Ters tercih (listeyi teslim edip beyanı
    modele emanet etmek) arızayı görünmez yapabilirdi.

    TS'Sİ OLMAYAN SATIR SESSİZCE DÜŞÜRÜLMEZ (denetim bulgusu 2026-08-29). Eski karşılaştırma
    `ts > son_ts` ts'siz satırı ("" > "") HER ZAMAN False'a düşürüyordu — o satır ne ilk turda ne
    başka hiçbir turda bildiriliyordu, ama `toplam`a sayılmaya devam ediyordu: KALICI sessiz
    dışlama, tam da bu betiğin var oluş nedenine ("hesaplanan teslim edilir") aykırı. Düzeltme:
    ts'siz satır KOŞULSUZ `yeni`ye girer ve mesajda ölçülemediği açıkça işaretlenir (UYDURMA
    YASAĞI: eksik alan gizlenmez, beyan edilir) — düzeltilene kadar HER turda yeniden görünür;
    bu BİLİNÇLİDİR: veri kusurunu gizlemek kaybolmasından beterdir.

    `en_yeni` bu ÇAĞRININ gördüğü (`yeni` listesindeki) satırlardan, YALNIZ gerçek ts taşıyanlar
    üzerinden hesaplanır — akıbet katmanı BURAYA DOKUNMAZ (damga sözleşmesi değişmedi). ts'siz bir
    satır damganın `son_ts`ini ASLA GERİYE SARAMAZ: bildirilen satırların hiçbirinde gerçek ts
    yoksa `en_yeni` eski `son_ts`te KALIR (ilerlemez) — aksi hâlde `max()` boş kümede patlar ya da
    "" damganın gerçek sınırını SİLER, ki bu da zaten bildirilmiş TARİHLİ satırların bir sonraki
    turda `> son_ts` görünüp YENİDEN bildirilmesi demek olurdu (damganın "wedge"lenmesi). ts'siz
    satır zaten kendi koşulsuz kuralıyla bir sonraki turda da yakalanır — ayrı bir iz sürmeye
    gerek yok."""
    satirlar = [r for r in store.read_jsonl(DEFTER) if isinstance(r, dict)]
    damga = (store.read_json(DAMGA_DOSYA, {}) or {}).get(DAMGA) or {}
    son_ts = str(damga.get("son_ts") or "")

    defter_satirlari, akibet_neden = _akibet_defteri()
    akibet = None
    if akibet_neden is None:
        try:
            akibet = _akibet.akibet_turet(satirlar, defter_satirlari, memory.now_iso())
        except Exception as e:
            # YUTMA DEĞİL: neden bir dizgeye çevrilip aşağıda mesaja BASILIYOR. Türetim
            # patlarsa (ör. elle düzenlenmiş bir satırın anahtarı çözülemiyor) ÖNERİ TESLİMATI
            # DÜŞMEZ — yalnız akıbet katmanı ölçülemedi sayılır. Ters tercih, bir defter
            # kusurunun tüm brifingi susturması olurdu.
            akibet, akibet_neden = None, f"{type(e).__name__}: {e}"

    if akibet_neden is not None:
        # DÜŞMEYEN KANAL (R1/Ö1): `hata` → `@sef._kaynak_oku` → `olculemeyen` (zorunlu parça,
        # model susturamaz, kaynak DAMGALANMAZ). Ham sayım karara bağlananlar AYIKLANMADAN
        # yapılır — bu sayının ne olduğu cümlede AÇIKÇA söylenir, sessizce eski davranışa
        # düşülmez.
        ham_sayim = len([r for r in satirlar
                         if not _ts_degeri(r) or _ts_degeri(r) > son_ts])
        cumle = _olculemedi_cumlesi(ham_sayim, akibet_neden)
        return {"toplam": len(satirlar), "yeni": ham_sayim, "mesaj": "", "en_yeni": son_ts,
                "acik_sayi": None, "akibet_olculemedi": akibet_neden, "hata": cumle,
                "not": cumle}

    # ASIL DAVRANIŞ: karara bağlanmış öneri `yeni` sayılmaz. Küme `kararlar`dan (TÜM tarihçe)
    # türer — `acik` listesinden değil: ts'si çözülemediği için `acik`e hiç giremeyen bir öneri
    # de, kararı varsa, "yeni" DEĞİLDİR. `None` KİMLİK KÜMEYE GİRMEZ (R1/Ö2): `akibet_turet` bir
    # karar satırını yalnız alanın VARLIĞINA bakarak kabul eder, DEĞERİNİ denetlemez — elle
    # düzenlenmiş bir defterde `oneri_id: null` taşıyan tek bir karar, kümeye `None` sokup
    # kimliksiz HER öneri satırını `yeni`den SESSİZCE düşürürdü (kalıcı görünmezlik; bu dosyanın
    # her yerinde yasakladığı sınıf).
    kapali = {k.get("oneri_id") for k in akibet["kararlar"] if k.get("oneri_id") is not None}
    yeni = [r for r in satirlar
            if (not _ts_degeri(r) or _ts_degeri(r) > son_ts) and r.get("id") not in kapali]
    kararlar = [k for k in akibet["kararlar"] if _karar_bildirilecek_mi(k, son_ts)]
    acik_sayi = akibet["sayilar"]["acik"]
    metinler = _oneri_metinleri(satirlar, defter_satirlari)

    bloklar: list[str] = []
    if yeni:
        bas = [f"🧠 {len(yeni)} yeni iyileştirme önerisi (defter toplam {len(satirlar)})"]
        for r in yeni[:LISTE_TAVANI]:
            oncelik = r.get("oncelik")
            etiket = f"[{oncelik}] " if oncelik else ""
            ts_uyari = "" if _ts_degeri(r) else " [ts YOK — ölçülemedi, sıralama garantisiz]"
            bas.append(f"· {_kimlik(r.get('id'))} {etiket}{r.get('alan')}: "
                       f"{str(r.get('oneri') or '')[:140]}{ts_uyari}")
        if len(yeni) > LISTE_TAVANI:
            bas.append(f"… ve {len(yeni) - LISTE_TAVANI} tane daha (state/{DEFTER})")
        bloklar.append("\n".join(bas))
    if kararlar:
        bas = [f"✅ {len(kararlar)} öneri karara bağlandı (son teslimden beri)"]
        # TAŞMA SEÇİMİ `_karar_secimi`de (R1/Kü2 + R2/Y1) — iki kural ÖNCELİKLE uzlaştırılır.
        # DÜŞENLER "eski" DİYE ADLANDIRILMAZ (R2/Y1): tarihi ölçülemeyen bir karar için "eski"
        # ÖLÇÜLMEMİŞ bir iddiadır. Söylenen şey ölçülmüş olandır: kaç tanesinin gösterilmediği
        # ve hangi ÖNCELİKLE seçildikleri.
        gosterilen, dusen = _karar_secimi(kararlar)
        if dusen:
            bas.append(f"… +{dusen} karar daha gösterilmiyor (önce tarihi ölçülemeyenler, "
                       f"sonra en yeniler)")
        bas += [_karar_cumlesi(k, metinler) for k in gosterilen]
        bloklar.append("\n".join(bas))
    # KOŞULSUZ (R2/Y5): mesaj üretilen her turda yaş satırı basılır — "açık öneri yok" dalı da
    # böylece gerçekten erişilir ve yığının boşaldığı gün operatör bunu görür.
    bloklar.append(_yas_satiri(akibet["acik"], akibet["sayilar"]["ertelendi"]))
    if akibet["olculemeyen"]:
        # BEDEL YASASI: akıbet katmanının kazancı (açık/karar ayrımı) ölçülüyorsa BEDELİ de
        # ölçülür — çözülemeyen satırlar açık sayısını ve yaşları EKSİK bırakır ve bu sessiz
        # kalamaz.
        bloklar.append(f"⚠ {len(akibet['olculemeyen'])} satır çözülemedi (öneri/akıbet "
                       f"defterlerinde) — açık sayısı ve yaşlar o kadar satır EKSİK ölçüldü")

    # SESSİZLİK ŞARTI KORUNUR: yaş satırı ve çözülemeyen-satır uyarısı TEK BAŞLARINA mesaj
    # DOĞURMAZ (yeni bir şey yoksa mesaj yoktur — v327). Ölçüm zincirinin kırılması bu kapıya
    # HİÇ GELMEZ: o dal yukarıda `hata` ile döner ve `@sef` onu susturulamaz kanaldan taşır.
    if not (yeni or kararlar):
        return {"toplam": len(satirlar), "yeni": 0, "mesaj": "", "en_yeni": son_ts,
                "acik_sayi": acik_sayi, "akibet_olculemedi": None, "hata": None,
                "not": (f"yeni öneri yok (defter {len(satirlar)}, "
                        f"damga {son_ts or 'hiç'}, {acik_sayi} açık)")}
    ts_degerli = [_ts_degeri(r) for r in yeni if _ts_degeri(r)]
    en_yeni = max(ts_degerli) if ts_degerli else son_ts
    return {"toplam": len(satirlar), "yeni": len(yeni), "mesaj": "\n".join(bloklar),
            "en_yeni": en_yeni, "acik_sayi": acik_sayi, "akibet_olculemedi": None,
            "hata": None, "not": ""}


def damgala(o: dict) -> bool:
    """Teslim damgasını basar; damga gerçekten yazıldıysa True. `o` = GÖNDERİLEN mesajı üreten
    `ozet_kur()` enstantanesi.

    MODÜL DÜZEYİNE ÇIKARILDI (denetim 2026-08-29) — gerekçesi kardeş betikte (`alarm_backlog_
    digest.damgala`) tam metniyle yazılı: gövde `main()` içinde bir kapanıştı, `@sef` onu
    çağıramadığı için sözleşmenin ikinci bir kopyasını yazmak zorunda kalmıştı.

    KARDEŞİNDEN FARKLI ŞEY DAMGALAR ve bu ayrım korunur: alarm tarafı KÜMÜLATİF SAYACIN kapsanan
    değerini kendi sayaç dosyasının İÇİNE yazar; burada damga EN YENİ ZAMAN DAMGASIDIR ve AYRI bir
    dosyada durur (okunan defter JSONL'dir, içine bir damga anahtarı koyulamaz). İkisini aynı
    sanmak birini kalıcı olarak damgasız bırakırdı.

    `store.update_json` sözleşmesi: belgeyi YERİNDE değiştir ve True dön — yeni sözlük döndürmek
    sessizce hiçbir şey yazmaz. `en_yeni` GÖNDERİLEN mesajı üreten AYNI enstantaneden gelir; send
    SONRASI ikinci bir defter okuması YOK (denetim bulgusu 2026-08-29): eski kod burada deftere
    yeniden bakıyordu ve gönderim penceresinde (ağ POST'u sürerken) eklenmiş bir satırı, o satır
    hiç mesajda YOKKEN 'gördüm' diye damgalıyordu — yarı-teslim'in ikinci bir türü, yalnızca
    ledger okuma zamanlamasından doğan.

    Dönüş değeri kayıt dürüstlüğü içindir: çağıranlar "damgalandı" diye olay yazar; yazım
    gerçekleşmediyse o olay yazılmamalıdır."""
    def _yaz(d: dict) -> bool:
        d[DAMGA] = {"ts": memory.now_iso(), "son_ts": o["en_yeni"], "kapsanan": o.get("yeni")}
        return True

    belge = store.update_json(DAMGA_DOSYA, _yaz, {}) or {}
    return isinstance(belge.get(DAMGA), dict)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--uygula", action="store_true",
                    help="gönder + teslim damgası bas (varsayılan KURU KOŞU)")
    args = ap.parse_args(argv)

    o = ozet_kur()
    # AKIBETİN OPERATÖR YÜZEYİ (Yasa 6 — yeni alanların okuyucusu): kuru koşumda da görünür.
    # "0 açık" ile "ölçülemedi" AYNI SATIRDA ayrışır; sıfır ile bilmiyorum karıştırılmaz.
    akibet_durum = (f"ÖLÇÜLEMEDİ ({o['akibet_olculemedi']})" if o["akibet_olculemedi"]
                    else f"{o['acik_sayi']} açık")
    print(f"defter: {o['toplam']} · yeni: {o['yeni']} · akıbet: {akibet_durum}")
    if o.get("hata"):
        # ÖLÇÜM ZİNCİRİ KIRIK: bu betik de `@sef` ile AYNI hükmü verir — hiçbir şey gönderilmez,
        # hiçbir damga basılmaz. İki yüzeyin aynı durumda farklı davranması (biri susup ötekinin
        # göndermesi) tek bir gerçeğin iki kopyası olurdu. Çıkış kodu sıfırdan FARKLIDIR: teslim
        # edilemeyen bir kadans "başarılı" görünemez (kanal-yok dalıyla aynı sınıf).
        print(f"ÖLÇÜLEMEDİ: {o['hata']}")
        print("gönderilmedi, damga basılmadı — @sef aynı beyanı susturulamaz kanaldan taşır "
              "(kaynak damgalanmadığı için öneri listesi bir sonraki turda yeniden bildirilir)")
        return 2
    if not o["mesaj"]:
        print(o["not"])
        return 0
    print("--- MESAJ ---")
    print(o["mesaj"])
    print("-------------")
    if not args.uygula:
        print("KURU KOŞU: gönderilmedi, damga basılmadı (--uygula ile gönderir)")
        return 0
    if not notify.configured():
        print("KANAL YOK: Telegram/webhook yapılandırılmamış — özet teslim EDİLEMEZ.")
        return 2
    if not notify.send(o["mesaj"]):
        print("GÖNDERİM DÜŞTÜ: damga basılmadı — sonraki koşum aynı yığını yeniden dener "
              "(yarım teslim 'teslim edildi' sayılmaz)")
        return 2

    damgala(o)          # gövde ve gerekçesi modül düzeyinde — tek uygulama, üç çağıran
    obs.log("oneri_brifingi_teslim", yeni=o["yeni"], toplam=o["toplam"], son_ts=o["en_yeni"],
            detail="okunmamış iyileştirme önerileri TEK özet mesajla teslim edildi ve damgalandı")
    print(f"TESLİM EDİLDİ ve damgalandı (yeni={o['yeni']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
