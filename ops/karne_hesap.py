#!/usr/bin/env python3
"""karne_hesap.py — `state/goal.yaml`ın DÖRT sorusunun deterministik cevabı. Model YOK, tahmin YOK.

NEDEN VAR. `state/goal.yaml` dört soru soruyor — `target_return_30d`, `min_sharpe`,
`max_drawdown`, `failure_below` — ve bugüne dek hiçbir PERİYODİK teslimat onları cevaplamıyor.
`self_review.json` öğrenme makinesini anlatır (reflections/ships/calibrations), AMAÇ sorusunu
değil. `watchdog.goal_failure_report` yalnız ARIZA anında konuşur (mandallı alarm), yani
"her şey yolunda" hâli SESSİZLİKTİR — ve o sessizlik iki ayrı şey demektir:

    (a) deney hiç başarısız olmadı        (b) hüküm hiç ölçülmedi

Bugün ikisi AYIRT EDİLEMİYOR. Bu dosyanın tek işi o ayrımı YAPISAL kılmaktır: ölçülemeyen hüküm
`OLCULEMEDI` + neden döner, iyi huylu bir sayı DEĞİL (Uydurma yasağı). Sıfır ile "bilmiyorum"
aynı şey değildir.

BU DOSYA CANLI DEFTERİ GÖREMEZ — ölçülen ile çıkarılan ayrıdır. Buradaki hiçbir eşik, sayı ya da
davranış cümlesi A1'de gözlenmiş DEĞİLDİR:
  · ÖLÇÜLEN (bu makinede, salt okuma): `meridian.score`, `meridian.watchdog`,
    `meridian.adapters.data` KAYNAK KODU — hangi fonksiyonun neyi nasıl hesapladığı, hangi
    alanları döndürdüğü. Bu kesindir, çünkü kodun kendisi okundu.
  · ÇIKARILAN: bu hesabın canlı defterde ne DİYECEĞİ. Yerel `state/` bu oturumda test
    artefaktlarıyla kirlendiği ölçülmüştür; "canlıda 30 işlem günü var mı" sorusu A1'de sorulur.
  · DOĞRULANAMAYAN: canlı `trades.jsonl`in gerçek uzunluğu ve dağılımı. İlk canlı koşum bir
    DOĞRULAMA turudur, teslimat turu değil.

TEK-KAYNAK YASASI, ÜÇ YERDE BAĞLAYICI:
  1. `failure_below` hükmünün SAHİBİ `watchdog.goal_failure_report`tır. Burada ÇAĞRILIR,
     pencere/mandal mantığı KOPYALANMAZ. Fonksiyon saf bir okumadır (config + store okur, hiçbir
     şey yazmaz, alarm basmaz — alarmı çağıranı `check_integrity_and_alarm` basar), yani
     çağrılabilir olduğu KAYNAKTAN ölçüldü.
  2. Sharpe / max-drawdown / 30g-getiri TANIMI `score.score_detail`indir — kapının kendi
     skorlayıcısı. Buradan AYNEN alınır. Sistemin skorlayıcısından farklı hesaplayan bir karne,
     kalıcı ve makul görünen bir yalan üretir.
  3. Eşikler `state/goal.yaml`dan okunur (izli SSoT dosya). Koda gömülü eşik dosya değişince
     sessizce ayrışır.
  KOPYA KAÇINILMAZ OLDUĞU TEK YER: `score.score_detail` iki kez değerlendirilir — bir kez burada
  (sharpe/dd için), bir kez `goal_failure_report` içinde (30g getiri için). Watchdog ara sonucunu
  DIŞA VERMİYOR ve onu değiştirmek bu görevin kapsamı dışında (çalışan koddur). Yasanın kendi
  reçetesi uygulanır: türetme + AYRIŞMA ÇİVİSİ — iki okumadan aynı gerçek için iki farklı sayı
  çıkarsa hüküm VERİLMEZ (`kapsam["ayrisma"]`).

PENCERE İŞLEM GÜNÜDÜR, TAKVİM GÜNÜ DEĞİL. `score.score_detail`in `realized_30d`si defterin KENDİ
süresinden 30 güne ÖLÇEKLENMİŞ bir orandır — bir pencere ölçümü değil, bir HIZDIR. Defter 30 işlem
gününden kısaysa o sayı bir ÖLÇÜM değil EKSTRAPOLASYONdur ve karne onu hüküm diye sunamaz.
Mesafe takvim günüyle ölçülemez: cuma→pazartesi 3 takvim günü ama 1 işlem günüdür, ve takvimle
ölçen bir eşik HER PAZARTESİ öter (deponun kendi dersi — `loop._mutabakat_bayatligi`). Takvim
alınamıyorsa cevap YOKTUR, uydurulmaz (`trend_shadow.ay_sonu_mu` emsali: fail-closed None).

ADI İLE ÖLÇTÜĞÜ AYNI ŞEY DEĞİL — ve bu HÜKMÜN YANINDA yazar (denetim MEDIUM-3). "30 günlük
getiri" adı bir TRAILING PENCERE çağrıştırır; ölçülen ise ömür boyu getirinin 30 günlük orana
çevrilmişidir. 500 işlem günlük bir defterde son 30 gün düz geçse bile hüküm GECTI çıkabilir.
Sistemin kendi tanımına sadakat DOĞRU karardır (`score_detail` `span_days` parametresiyle gerçek
bir trailing pencere teknik olarak mümkündü, ama watchdog'unkinden AYRIŞIRDI) — eksik olan,
tanımın hükmün yanında GÖRÜNMESİYDİ: `OLCEK_SERHI` iki hükme de eklenir ve `GOREMEDIGIM`e girer.
Görev 2'nin modeli modül başlığını değil TAM O CÜMLEYİ okur; orada yoksa uyduramaz, susar.

TAZELİK — BAYAT DEFTER GÜNCEL HÜKÜM DOĞURMAZ (denetim MEDIUM-4). İlk sürümde `datetime` ithali
bile yoktu: motor üç ay önce durmuş olsa karne aynı hükmü her hafta GÜNCEL bir cevap gibi
basardı. Bu, kardeş profilin (`@bekci`) avlamak için var olduğu "duran iş" sınıfıdır ve bu botun
kendi gerekçesinin ("hiç başarısız olmadı" ≠ "hiç ölçülmedi") yeni bir kılığıdır.
EŞİK YUVARLAK BİR SAYI DEĞİL, TÜRETİLİR — iki kaynaktan, BÜYÜĞÜ bağlar:
  (a) defterin KENDİ geçmişindeki en uzun sessizlik (işlem günü). Seyrek işleyen bir strateji
      kendi normalinden ötürü yanlış alarm üretmemeli — operatör onu susturur, sonra GERÇEK
      durma görünmez olur (bu deponun tekrar eden sınıfı);
  (b) 30 günlük hüküm penceresinin kendisi. Bu pencereden KISA bir sessizlik, hükmün sorduğu
      dönemi hâlâ kısmen doldurur; orada susmak fazla hassas olurdu.
Sessizlik de İŞLEM GÜNÜYLE ölçülür ve "şimdi" tek saatten gelir (`barclock.session_date`).
Takvim ya da saat alınamazsa tazelik ÖLÇÜLEMEZ ve dört hüküm de susar — bayat olmadığını
KANITLAYAMADIĞIMIZ bir defterden güncel hüküm çıkarmak, tam da kapatmaya çalıştığımız boşluktur.

BİLİNÇLİ ASİMETRİ — RAPOR, ALARMDAN SESSİZ OLAMAZ. Kısa pencere "başarısız DEĞİL" hükmünü
`OLCULEMEDI`ye çevirir (asıl boşluk budur). Ama "BAŞARISIZ" hükmünü SUSTURMAZ: watchdog `failed`
dediyse karne `KALDI` der, pencere kısa olsa bile — kısalık gerekçeye şerh olarak düşer. Rapor
katmanının bir arıza hükmünü yutması, bu botun var oluş gerekçesinin tam tersidir.

META-KAPI İLKESİ — asimetri BİR KAPIYA ÖZGÜ DEĞİL, GENELDİR (denetim MEDIUM-1, 2026-08-30).
Bu dosyada üç meta-kapı var: KISA PENCERE, TEK-KAYNAK AYRIŞMASI, BAYAT DEFTER. Üçü de aynı
kurala tabidir: **bir hükmü ancak CEVABI DEĞİŞTİREBİLECEKLERİ zaman hükümsüz kılarlar.**
`failed=False` ("başarısız değil") kırılgandır — ölçüm eksikse o cevap bir bilgisizliktir ve
yutulur. `failed=True` kırılgan DEĞİLDİR: şüpheli olan taraf karnenin kendi İKİNCİ okumasıdır,
hükmün SAHİBİ (watchdog) değil; şüphe hükmü değil GEREKÇEYİ etkiler, şerh olarak düşer.
İlk sürümde `_failure` `ayrisma`yı `failed`den ÖNCE sınıyordu — yani yukarıdaki paragrafın
MUTLAK biçimde reddettiği şeyi yapıyordu ve hiçbir çivi ısırmıyordu (denetimin bulduğu tek
beyan-kod çelişkisi).

DEFTER İKİ KEZ OKUNUR — KAÇINILMAZ YARIŞ, BEYANLI (denetim INFO-14). Karne `store.read_jsonl`
çağırır, ardından `goal_failure_report` AYNI defteri BAĞIMSIZ olarak yeniden okur. İki okuma
arasına canlı worker bir satır eklerse ayrışma çivisi tetiklenir ve 30g hükümleri hükümsüz
kalır — FAIL-CLOSED, yani yanlış bir sayı basmaktansa susar. Bugün kaçınılmaz: watchdog
fonksiyonu ARGÜMAN ALMIYOR ve onu değiştirmek bu görevin kapsamı dışında (çalışan koddur).
Azaltma Görev 3'ün elindedir: haftalık slot canlı worker'ın yazma pencerelerinden uzak seçilir.

BU ARAÇ YAZMAZ — ve bu söz TAM OLARAK ŞU KADARDIR (kazanç kadar BEDEL de beyan edilir; ölçülmemiş
bir "hiç yazmaz" cümlesi, olmayan bir güvencedir). Hesabın kendisi salt okumadır (`store.read_*`,
`config.goal`, `barclock.session_date`); hiçbir defter, damga ya da hüküm ÜRETMEZ, `--uygula`
gibi bir bayrak bilerek yoktur. ALTI İSTİSNA VARDIR ve altısı da ÇAĞRILAN KATMANLARIN KENDİ
DAVRANIŞIDIR, bu aracın değil. SAYIM ARTIK BEYANIN KENDİSİNDEN DEĞİL ÇAĞRI GRAFİĞİNDEN GELİYOR
(denetim MEDIUM-4, 2026-08-31): önceki sayım DÖRT diyordu ve çivisi beyanı KENDİSİYLE
karşılaştırdığı için eksiği yapısal olarak göremiyordu. Bugün `test_YAZMA_ISTISNALARI_TAM_SAYILIR`
`hesapla()`nın giriş noktalarından AST ile yürüyor; aşağıdaki liste o yürüyüşün ÇIKTISIDIR:
  · `score._span_warn` (`score.score_detail → _span_days`) — defterde bozuk tarih damgası varsa
    `obs.warn("span_days_fallback")` basar;
  · `adapters.data._bar_warn` (`data._sessions`) — XNYS takvimi yüklenemezse `obs`a uyarı basar
    (olay adı ÇAĞRI ARGÜMANIDIR, sabit değil — tarama onu `None` diye sayar, uydurmaz);
  · `store._bozuk_satir_uyar` (`store.read_jsonl` ve `store._read_jsonl_kuyruk`; TSK-137a
    2026-09-04'te `read_jsonl`in gövdesinden bu yardımcıya taşındı — çivi taşınmayı AYNI GÜN
    yakaladı, beyan izledi) — defterde ÇÖZÜLEMEYEN satır varsa `obs.warn("jsonl_rows_skipped")`
    basar (dosya başına bir kez). İlk iki kalemle AYNI SINIF; ilk sayımda ATLANMIŞTI (denetim
    MEDIUM-5) ve eksik bir muhasebe, kendi kuralınca olmayan bir güvencedir;
  · `store._bayat_defter_suzgeci` (`store.db_backed`) — DB devredeyken ilk `db_backed` temasında,
    göçmüş bir varlığın kanonik düz dosyası hâlâ duruyorsa onu `.migrated`a TAŞIR (hiçbir şey
    silinmez/üzerine yazılmaz, idempotenttir) VE bunu İKİ ayrı olayla duyurur
    (`bayat_defter_arsivlendi`, `db_aktif_kanonik_dosya_gocsuz`) — yani altı KAYNAK, yedi YAZIM
    NOKTASI. MARJİNAL ETKİSİ SIFIRDIR: `store.read_jsonl` zaten aynı teması kuruyor;
  · `storage._yerel_defter_beyani` (`store.db_backed → storage.active`) —
    `obs.warn("yerel_donmus_defter")`: `meridian.db` OLMAYAN bir makinede, kanonik defter
    dosyaları dururken (süreç başına bir kez);
  · `storage._acil_anahtar_beyani` (aynı yol) — `obs.warn("db_off_kaynaklar_arsivde")`:
    `MERIDIAN_DB=off` acil anahtarı çekiliyken.
İLK ÜÇÜ VE SON İKİSİ YASA 4'ün sesidir — susturulmaları körlük olurdu; dördüncüsü depolama
katmanının bakımıdır. Son ikisi A1'de ATEŞLEMEZ (DB var, anahtar çekili değil) ama bu araç aynı
zamanda operatörün ELLE koştuğu bir CLI'dır: `meridian.db`si olmayan bir makinede
`uv run python ops/karne_hesap.py` `state/events.jsonl`e YAZAR — CLAUDE.md §2'nin adını koyduğu
"ajan pytest-dışı state yazımı" sınıfının aynısı. Altısı da burada beyan edilmeseydi, "yazmaz"
sözü ölçülmemiş bir iddia olarak kalırdı.
TARAMANIN KAPSAMI DÜRÜSTÇE DARDIR (çivinin kendi beyanı): yalnız BEYAN EDİLEN modül kümesi
(`score`, `store`, `storage`, `config`, `barclock`, `watchdog`, `adapters.data`) ve yalnız
STATİK olarak çözülebilen çağrılar yürünür. Dinamik gönderim, `getattr`, geri çağırma ve bu
kümenin dışına çıkan bir dal taranmaz — kapsam dışı bir yazım bu listede GÖRÜNMEZ.

DÖRDÜNÜN DE HÜKMÜ PYTHON'DA VERİLİR. Model burada yoktur ve bir hükmü ne üretebilir ne
susturabilir; sunum katmanı ayrı dosyadır. Çivi: `tests/test_karne_hesabi_v339.py`.


ÇIKIŞ SÖZLEŞMESİ KİMİN İÇİN (Rol-1 hükmü 2026-08-30 — Görev 3 denetiminin bulgusu üzerine):
bu dosyanın `main()` çıkış kodları (rc 2 = dört hüküm birden OLCULEMEDI) OPERATÖRÜN ELLE
KOŞTUĞU CLI içindir — teşhis aracı. systemd birimi BU dosyayı DEĞİL `karne_brifingi.py`yi
koşar ve onun sözleşmesi TESLİMAT-tabanlıdır: ölçüm kesintisi bile MESAJ olarak gider
(SUSMA-YOK) ve teslim edilen hafta rc 0'dır. İki sözleşme AYRI ÇAĞIRANLARA hizmet eder;
bunu bilmeden birinden ötekinin davranışını beklemek, Görev 3'ün yakaladığı yanılgının
kendisidir. Arızanın görünürlüğü birim durumunda değil MESAJIN İÇİNDEDİR (zorunlu baş).
"""
from __future__ import annotations

import argparse
import json
import sys

from meridian import barclock, config, score, store, watchdog
from meridian.adapters import data as _veri

# Watchdog `trades.jsonl` adını SABİT okur (`goal_failure_report` gövdesi). Bu yüzden burada bir
# `--defter` bayrağı BİLEREK YOKTUR: iki kaynağa farklı defter okutabilen bir bayrak, tek-kaynak
# ayrışmasını operatörün eline verirdi — ve ayrışma çivisi onu her koşumda hükümsüz kılardı.
DEFTER = "trades.jsonl"

# 30, bir EŞİK değil bir TANIMDIR: `goal.yaml`ın iki sorusu da ("target_return_30d",
# "failure_below" şerhi) 30 GÜNLÜK getiriyi sorar. Bu yüzden CLI'dan ayarlanabilir DEĞİLDİR —
# ayarlanabilir olsaydı "kısa pencereyi geçir" bir bayrak mesafesinde olurdu.
PENCERE_ISLEM_GUNU = 30

# Görev 2 bu demeti okuyacak: soruların LİSTESİ de tek kaynaktan gelmeli, iki yerde elle
# yazılmamalı. Sıra rapor sırasıdır: önce iki başarı ölçütü, sonra iki başarısızlık tavanı.
SORULAR = ("target_return_30d", "min_sharpe", "max_drawdown", "failure_below")

# `score.score_detail` BU ÜÇÜNÜ KÖŞELİ PARANTEZLE okur — biri eksikse skorlayıcı KeyError atar.
# Ad listesi burada durur ki eksik anahtar bir ÇÖKME değil bir HÜKÜM üretsin (denetim LOW-9).
SKOR_ZORUNLU_ESIKLER = ("target_return_30d", "max_drawdown", "min_sharpe")

# Hüküm adları TEK yerde. Görev 2 bu demeti ithal eder; aşağıdaki üçlü açılım onu BU modülde de
# okunur kılar — okunmayan bir arayüz sabiti sessizce ayrışabilen ikinci bir gerçektir (YASA 6).
HUKUMLER = ("GECTI", "KALDI", "OLCULEMEDI")
_GECTI, _KALDI, _OLCULEMEDI = HUKUMLER

# ADIN YALANINI HÜKMÜN YANINA KOYAN CÜMLE. İki hükümde birden görünür (hedef + başarısızlık) ve
# bu yüzden SABİTTİR: iki yere elle yazılsaydı biri güncellenip öteki kalırdı.
OLCEK_SERHI = ("bu SON 30 GÜNÜN getirisi DEĞİLDİR — score.score_detail defterin TAMAMINDAN "
               "30 günlük bir orana ölçekler (ömür boyu hız); son 30 gün düz geçse bile bu sayı "
               "yüksek kalabilir")

# Kapsam beyanının sabit yarısı: bu hesabın YAPISAL kör noktaları. Ölçüme değil TASARIMA bağlı
# oldukları için burada durur; koşumdan koşuma değişmezler ve değişirlerse bu satırlar değişmeli.
GOREMEDIGIM = (
    "AÇIK POZİSYON ÇEKİLMESİ: drawdown yalnız KAPANMIŞ işlem eğrisinden ölçülür — "
    "`score.score_detail`in `mtm_equity` (günlük mark-to-market) girdisi bu katmanda YOK. "
    "Açıkken oluşup kapanışta toparlanan bir çekilme bu sayıda GÖRÜNMEZ.",
    "NAKİT HAREKETİ: sermaye eğrisi `pnl_dollars` toplamıdır (`score.equity_curve`); "
    "hesaba para giriş/çıkışı olsaydı eğri onu görmezdi.",
    "SON 30 GÜN: hükümler defterin TAMAMINDAN 30 güne ölçeklenmiş bir HIZDIR, TRAILING PENCERE "
    "DEĞİL. Tanım sistemin kendi kapı skorlayıcısınındır (`score.score_detail`); ayrı bir "
    "gerçek 30-günlük pencere `watchdog.goal_failure_report`unkinden ayrışırdı.",
    "CANLI DEFTER: bu hesap koştuğu MAKİNENİN `state/`ini okur. Yerel defter test "
    "artefaktlarıyla kirlenebilir; canlı hüküm A1'de koşulan karneden okunur.",
    "TAKVİM DIŞI ARA DAMGALAR: kadans ölçümü (tazelik eşiğinin (a) bacağı) yalnız XNYS "
    "takviminde BULUNAN kapanış günlerinden hesaplanır; takvim dışı bir ara damga sessizliği "
    "uzatmış olsa bile o aralığa girmez.",
    "AÇIK PLANLAR: hüküm yalnız KAPANMIŞ işlemlerden kurulur — bekleyen/açık pozisyonların "
    "gerçekleşmemiş sonucu hiçbir hükme girmez.",
)


# ---------------------------------------------------------------------------------------------
# HÜKÜM SÖZLÜĞÜ
# ---------------------------------------------------------------------------------------------
# SÖZLEŞME KAPISININ TEK BEYANLI İSTİSNASI — ve gerekçesi META-KAPI İLKESİNİN kendisidir
# (denetim LOW-1, 2026-08-31). "Değer yoksa hüküm yok" kuralı UYDURMA YASAĞINI korur: sayısız bir
# GECTI, ölçülmemiş bir iyi haberdir. Ama sayısız bir BAŞARISIZLIK hükmü ölçülmemiş DEĞİLDİR —
# hükmün SAHİBİ (watchdog) onu VERDİ; eksik olan yalnız kanıt sayısıdır. Kapıyı orada da
# uygulamak, meta-kapıların yutmasını MUTLAK biçimde reddettiğimiz şeyi (bir `failed=True`nun
# OLCULEMEDI'ye düşmesini) sözleşme kapısı eliyle yapmak olurdu. Bugün erişilemez
# (`watchdog.goal_failure_report` `failed=True`yu yalnız `realized_30d` float'ken döndürür) —
# ama "bugün erişilemez" bir hüküm gerekçesi DEĞİLDİR: sözleşmeler değişir, ilkeler değişmez.
DEGER_OLCULEMEDI_SERHI = (
    "DEĞER ÖLÇÜLEMEDİ (hüküm DÜŞMEDİ): başarısızlık hükmünün sahibi hükmü VERDİ ama gerçekleşen "
    "30g oranı bildirmedi — cevap BİLİNİYOR, sayı EKSİK. Eksik bir sayı bir arıza hükmünü "
    "hükümsüz kılmaz; kılsaydı rapor katmanı alarm katmanını susturmuş olurdu")


def _hukum(deger, esik, gecti, neden: str, *, deger_zorunlu: bool = True) -> dict:
    """Tek hüküm: `{deger, esik, hukum, neden}` — Görev 2'nin bağlandığı şekil.

    DEĞİŞMEZ: `hukum == "OLCULEMEDI"` ⟹ `deger is None` HER ZAMAN; ters yön (`deger is None` ⟹
    `OLCULEMEDI`) TEK bir BEYANLI istisna taşır (`deger_zorunlu=False`, yalnız `_failure`ın
    `failed=True` dalı — bkz. `DEGER_OLCULEMEDI_SERHI`). Ölçülemeyen bir hükmün yanında duran
    sayı panoda ÖLÇÜM gibi okunur; bu botun kapatmak için var olduğu boşluğun ta kendisi o
    okumadır. Elde bir ham sayı varsa yeri `deger` değil `neden`dir — orada "bu bir ölçüm
    değildir" cümlesiyle birlikte durur.

    `gecti is None` = hüküm kurulamadı. True/False = kuruldu.

    DEĞİŞMEZ ARTIK BELGEDE DEĞİL KODDA (denetim LOW-8): eskiden yalnız ÇAĞIRANLARIN disiplini
    sağlıyordu. Bugünkü watchdog sözleşmesinde erişilemeyen ama yarın açılabilecek bir dal —
    `failed=False` + `realized_30d=None` — `{"hukum": "GECTI", "deger": None}` üretirdi: hem
    değişmezin hem uydurma yasağının ihlali, tek satırda. Kapı çökertmez, HÜKMÜ DÜŞÜRÜR: bir
    rapor aracının haftalık koşumunu istisna ile öldürmek, sessiz yalandan daha iyi değildir.
    """
    if gecti is not None and deger is None:
        if not deger_zorunlu:
            return {"deger": None, "esik": esik, "hukum": _GECTI if gecti else _KALDI,
                    "neden": f"{neden} — {DEGER_OLCULEMEDI_SERHI}"}
        return {"deger": None, "esik": esik, "hukum": _OLCULEMEDI,
                "neden": (f"SÖZLEŞME İHLALİ: hüküm kuruldu ama DEĞER YOK — sayısız bir "
                          f"GECTI/KALDI uydurma yasağını çiğnerdi. Özgün gerekçe: {neden}")}
    if gecti is None:
        return {"deger": None, "esik": esik, "hukum": _OLCULEMEDI, "neden": neden}
    return {"deger": deger, "esik": esik, "hukum": _GECTI if gecti else _KALDI, "neden": neden}


def _oran(x) -> str:
    """Oranı okunur yüzdeye çevirir; None ise sayı UYDURMAZ."""
    return "—" if x is None else f"{float(x):+.2%}"


# ---------------------------------------------------------------------------------------------
# PENCERE — İŞLEM GÜNÜ
# ---------------------------------------------------------------------------------------------
def _kapanis_gunleri(islemler: list[dict]) -> list[str]:
    """Defterdeki kapanış damgalarının `YYYY-MM-DD` hâli, sıralı. Damgasız satır ATLANIR ve bu
    sessiz değildir: sayısı kapsam beyanına düşer (`damgasiz_satir`)."""
    return sorted(str(t.get("ts_close"))[:10] for t in islemler if t.get("ts_close"))


def _pencere(kapanislar: list[str], seanslar) -> tuple:
    """Defterin kapsadığı İŞLEM GÜNÜ sayısı → `(gun, neden)`. Ölçülemezse `(None, neden)`.

    KAYNAK: `adapters.data._sessions()` — bu depodaki TEK XNYS seans kümesi (süreç başına bir kez
    üretilir). İkinci bir `pandas_market_calendars` çağrısı açmak "aynı zaman iki kaynak"
    ayrışmasıdır; `trend_shadow.ay_sonu_mu` aynı gerekçeyle aynı kaynağa bağlanır.

    ÖLÇÜLEMEZSE UYDURULMAZ (`loop._mutabakat_bayatligi` deseni birebir): takvim yoksa ya da
    defterin uçları takvimde bulunamıyorsa `(None, neden)`. Takvim GÜNÜNE düşmek burada sessiz
    bir yanlış cevaptır — cevapsızlık dürüsttür.
    """
    if not kapanislar:
        return None, "defterde kapanış damgası yok — pencere ölçülemez"
    if not seanslar:
        return None, ("XNYS işlem takvimi yüklenemedi — pencere İŞLEM GÜNÜ olarak ölçülemez; "
                      "takvim gününe düşmek her pazartesi öten bir eşik üretirdi")
    ilk, son = kapanislar[0], kapanislar[-1]
    disarida = [g for g in (ilk, son) if g not in seanslar]
    if disarida:
        return None, (f"defterin ilk ({ilk}) ya da son ({son}) kapanış günü XNYS takviminde yok "
                      f"[{', '.join(disarida)}] — mesafe işlem günü olarak ölçülemez")
    return sum(1 for s in seanslar if ilk <= s <= son), None


def _pencere_yetersiz(gun, neden: str | None) -> str | None:
    """Pencere 30 işlem gününü DOLDURMUYORSA gerekçe, dolduruyorsa None.

    SINIR DAHİLDİR: tam 30 işlem günü YETERLİDİR — kapı `gun < PENCERE_ISLEM_GUNU` sorar, yani
    yetersizlik KESİN EŞİĞİN ALTINDA başlar. (Cümle düzeltildi, denetim LOW-8: eskiden "`<`
    değil `<=` karşılaştırması" diyordu ve kodda öyle bir operatör YOKTU — davranış doğruydu,
    tarif yanlıştı. Bir sonraki okuyucuyu kodu "düzeltmeye" davet eden cümle sınıfı.)"""
    if gun is None:
        return neden or "pencere ölçülemedi"
    if gun < PENCERE_ISLEM_GUNU:
        return (f"defter {gun} işlem günü kapsıyor, {PENCERE_ISLEM_GUNU} gerekiyor")
    return None


def _bayatlik(kapanislar: list[str], seanslar, bugun: str) -> tuple:
    """Defter GÜNCEL mi? → `(bayat, neden, sessizlik, esik, gecmis_en_uzun)`.

    `bayat is None` = ölçülemedi (takvim yok, damga takvim dışı, saat tutarsız). Uydurulmaz.

    EŞİK TÜRETİLİR, SEÇİLMEZ — iki bacağın BÜYÜĞÜ bağlar:
      (a) `gecmis_en_uzun`: defterin KENDİ geçmişindeki en uzun sessizlik. Seyrek işleyen bir
          strateji kendi normali yüzünden alarm üretmemeli; üretirse operatör susturur ve
          GERÇEK durma görünmez olur.
      (b) `PENCERE_ISLEM_GUNU`: hükmün sorduğu pencerenin kendisi. Ondan kısa bir sessizlik
          pencereyi hâlâ kısmen doldurur — orada susmak fazla hassas olurdu.
    Yuvarlak bir sayı SEÇİLMEDİ: (a) ölçülür, (b) `goal.yaml`ın sorusunun tanımıdır.
    """
    if not kapanislar:
        return None, "defterde kapanış damgası yok — tazelik ölçülemez", None, None, None
    if not seanslar:
        return None, ("XNYS işlem takvimi yüklenemedi — sessizlik İŞLEM GÜNÜ olarak ölçülemez; "
                      "defterin GÜNCEL olup olmadığı bilinmiyor"), None, None, None
    son = kapanislar[-1]
    if son not in seanslar:
        return None, (f"defterin son kapanışı ({son}) XNYS takviminde yok — sessizlik işlem günü "
                      f"olarak ölçülemez"), None, None, None
    if son > bugun:
        return None, (f"defterin son kapanışı ({son}) BUGÜNDEN ({bugun}) SONRA — damga ya da saat "
                      f"tutarsız; '0 gün sessizlik' demek ölçülemeyeni en iyi hâliyle uydurmak "
                      f"olurdu"), None, None, None
    sessizlik = sum(1 for s in seanslar if son < s <= bugun)

    # Kadans yalnız TAKVİMDE BULUNAN kapanış günlerinden ölçülür — takvim dışı bir ara damga
    # sıralamaya sokulamaz. Kayıp, `GOREMEDIGIM` içinde adıyla beyanlıdır.
    gunler = sorted({g for g in kapanislar if g in seanslar})
    gecmis = None
    if len(gunler) >= 2:
        sirali = sorted(s for s in seanslar if gunler[0] <= s <= gunler[-1])
        yer = {g: i for i, g in enumerate(sirali)}
        gecmis = max(yer[gunler[i + 1]] - yer[gunler[i]] for i in range(len(gunler) - 1))

    esik = max(gecmis or 0, PENCERE_ISLEM_GUNU)
    if sessizlik > esik:
        return True, (f"defterin son kapanışı {son}; o günden bu yana {sessizlik} İŞLEM GÜNÜ "
                      f"geçti — eşik {esik} (defterin kendi en uzun sessizliği "
                      f"{gecmis if gecmis is not None else '—'} ile {PENCERE_ISLEM_GUNU} günlük "
                      f"hüküm penceresinin BÜYÜĞÜ). Karne bayat defterden GÜNCEL hüküm vermez"
                      ), sessizlik, esik, gecmis
    return False, None, sessizlik, esik, gecmis


# ---------------------------------------------------------------------------------------------
# HESAP
# ---------------------------------------------------------------------------------------------
def hesapla() -> dict:
    """Dört hüküm + kapsam beyanı. SAF: okur, hesaplar, döner — hiçbir defter yazmaz.

    Dönen şekil:
        {"hukumler": {<soru>: {"deger","esik","hukum","neden"}, ...}, "kapsam": {...}}
    """
    goal = config.goal()
    islemler = store.read_jsonl(DEFTER)
    kapanislar = _kapanis_gunleri(islemler)

    # TAKVİM BİR KEZ OKUNUR, İKİ KAPI ONU PAYLAŞIR: pencere ve tazelik ayrı ayrı `_sessions()`
    # çağırsaydı iki kapı farklı takvimle hüküm verebilirdi — aynı koşumun içinde ayrışan
    # iki gerçek. Saat de tektir (`barclock`), ikinci bir saat kaynağı açılmaz.
    seanslar = _veri._sessions()
    bugun = barclock.session_date()

    pencere_gun, pencere_neden = _pencere(kapanislar, seanslar)
    yetersiz = _pencere_yetersiz(pencere_gun, pencere_neden)
    bayat, bayat_neden, sessizlik, bayat_esik, gecmis_sessizlik = _bayatlik(
        kapanislar, seanslar, bugun)

    # EKSİK EŞİK ÇÖKME DEĞİL HÜKÜM ÜRETİR (denetim LOW-9): `score.score_detail` üç anahtarı
    # KÖŞELİ PARANTEZLE okur ve `hesapla()` onu dört hükümden ÖNCE çağırır — biri eksikse eskiden
    # KeyError uçuyor, "goal.yaml'da … yok" dalları HİÇ koşmuyordu. Kapı önce burada sorulur.
    eksik = [k for k in SKOR_ZORUNLU_ESIKLER if goal.get(k) is None]
    if eksik:
        sd = {}
        sd_hata = (f"score.score_detail koşamadı: goal.yaml'da {', '.join(eksik)} YOK "
                   f"(skorlayıcı bu anahtarları köşeli parantezle okur)")
    else:
        sd, sd_hata = score.score_detail(islemler, goal), None

    try:
        gf = watchdog.goal_failure_report()
        gf_hata = None
    except Exception as e:
        # YASA 4 sinyali: istisna YUTULMUYOR, hükmün gerekçesine TAŞINIYOR. Tek kaynağın düşmesi
        # "başarısız değil" demek değildir; "başarısızlık kriterini ölçemedim" demektir.
        gf, gf_hata = {}, f"{type(e).__name__}: {e}"

    # --- AYRIŞMA ÇİVİSİ (tek-kaynak yasasının kendi reçetesi) ---------------------------------
    ayrisma = None
    sd_r30, gf_r30 = sd.get("realized_30d"), gf.get("realized_30d")
    if sd_r30 is not None and gf_r30 is not None and float(sd_r30) != float(gf_r30):
        ayrisma = (f"TEK-KAYNAK AYRIŞMASI: aynı 30g getiri iki okumada farklı — "
                   f"score.score_detail {_oran(sd_r30)} vs watchdog.goal_failure_report "
                   f"{_oran(gf_r30)}. En olası sebep iki okuma arasına düşen bir defter "
                   f"eklemesidir, yani `sd`den gelen HER sayı şüphelidir")

    n, min_ornek = sd.get("n"), sd.get("min_sample")
    ornek_neden = sd_hata or sd.get("reason")   # score_detail min_sample altında YALNIZ `reason` döner

    # META-KAPILAR TEK DEMETTE: üçü de aynı ilkeye tabidir (bkz. modül başlığı), o yüzden
    # hükümlere birlikte geçerler — biri unutulursa kapı dağılımı yine tutarsızlaşır.
    meta = (ayrisma, bayat_neden if bayat is not False else None)

    hukumler = {
        "target_return_30d": _target(goal, sd, gf_hata, meta, yetersiz, pencere_gun, n,
                                     ornek_neden),
        "min_sharpe": _sharpe(goal, sd, meta, yetersiz, pencere_gun, ornek_neden),
        "max_drawdown": _drawdown(goal, sd, meta, ornek_neden),
        "failure_below": _failure(goal, gf, gf_hata, meta, yetersiz, pencere_gun),
    }

    return {
        "hukumler": hukumler,
        "kapsam": {
            "defter": DEFTER,
            "defter_db_destekli": bool(store.db_backed(DEFTER)),
            "islem_sayisi": len(islemler),
            "damgasiz_satir": len(islemler) - len(kapanislar),
            "min_ornek": min_ornek,
            "ornek_yeterli": ornek_neden is None,
            # NEDEN DE TAŞINIR (denetim LOW-7): `ornek_yeterli=False`ın İKİ ayrı sebebi var —
            # örneklem gerçekten kısa olabilir YA DA `score.score_detail` hiç koşamamış olabilir
            # (eksik eşik). İkisini tek cümleye indiren kapsam beyanı, olmayan bir arızayı
            # (yetersiz örneklem) suçluyordu; sebep alanı olmadan doğrusu SÖYLENEMEZ.
            "ornek_neden": ornek_neden,
            "ilk_kapanis": kapanislar[0] if kapanislar else None,
            "son_kapanis": kapanislar[-1] if kapanislar else None,
            "bugun": bugun,
            "bayat": bayat,
            "bayat_neden": bayat_neden,
            "sessizlik_islem_gunu": sessizlik,
            "bayat_esik_gun": bayat_esik,
            "gecmis_en_uzun_sessizlik": gecmis_sessizlik,
            "pencere_islem_gunu": pencere_gun,
            "pencere_gereken": PENCERE_ISLEM_GUNU,
            "pencere_neden": pencere_neden,
            "takvim_kaynagi": "meridian.adapters.data._sessions (XNYS) — deponun tek seans kümesi",
            "ayrisma": ayrisma,
            "goremedigim": list(GOREMEDIGIM),
        },
    }


def _meta_engel(meta) -> str | None:
    """Meta-kapılardan (ayrışma, bayatlık) ilk KONUŞANIN gerekçesi; ikisi de sessizse None.
    Hükmü YUTAN kapı burasıdır — `failure_below`un `failed=True` dalı bunu BİLEREK çağırmaz
    (bkz. modül başlığı, META-KAPI İLKESİ)."""
    return next((m for m in meta if m), None)


def _meta_serh(meta) -> str:
    """Aynı kapıların ŞERH biçimi: hükmü yutmaz, gerekçeye eklenir. Yutulmayan bir şüphenin
    GÖRÜNMEZ kalması, yutulmasından farklı ama yine de bir körlüktür."""
    konusan = [m for m in meta if m]
    return "" if not konusan else " — ŞERH (hüküm SUSTURULMADI): " + " · ".join(konusan)


def _target(goal, sd, gf_hata, meta, yetersiz, pencere_gun, n, ornek_neden) -> dict:
    """`target_return_30d` — 30 günlük gerçekleşen getiri hedefi AŞTI mı?

    SAYI `sd`DEN GELİR, `gf`DEN DEĞİL (denetim MEDIUM-2). Eskiden `gf["realized_30d"]` okunuyordu
    ve bu, HEDEF hükmünü `failure_below`un YAPILANDIRMASINA bağlıyordu: goal.yaml'dan
    `failure_below` düşerse watchdog `kapsam_disi` döner, `gf["realized_30d"]` None olur ve hedef
    — eşiği yerinde, sayısı `sd`de HAZIR olduğu hâlde — "failure_below tanımlı değil" gerekçesiyle
    hükümsüz kalırdı. Tek-kaynak kaygısı bu bağı GEREKTİRMİYOR: ayrışma çivisi iki okumanın
    eşitliğini zaten garanti eder."""
    esik = goal.get("target_return_30d")
    if esik is None:
        return _hukum(None, None, None,
                      "goal.yaml'da `target_return_30d` yok — hüküm verilecek eşik yok")
    esik = float(esik)
    if ornek_neden:
        return _hukum(None, esik, None, ornek_neden)
    engel = _meta_engel(meta)
    if engel:
        return _hukum(None, esik, None, engel)
    r30 = sd.get("realized_30d")
    if r30 is None:
        return _hukum(None, esik, None,
                      "score.score_detail 30g getiri döndürmedi — hüküm kurulamadı")
    if yetersiz:
        return _hukum(None, esik, None,
                      f"{yetersiz} — ham oran {_oran(r30)} bir ÖLÇÜM DEĞİL, kısa defterin 30 güne "
                      f"ÖLÇEKLENMİŞ hâlidir (defterin süresine göre gerilir ya da SIKIŞIR: "
                      f"{PENCERE_ISLEM_GUNU} işlem günü ≈ 42 takvim günüdür, yani bu bantta "
                      f"sıkışma yönündedir). {OLCEK_SERHI}")
    r30 = float(r30)
    gecti = r30 >= esik
    # ÇAPRAZ DOĞRULAMA KOŞAMADIYSA BU SÖYLENİR (denetim MEDIUM-7): hüküm yine kurulur — sayı
    # `sd`dedir — ama watchdog'un ikinci okuması yoksa ayrışma çivisi o koşumda KÖRDÜR ve
    # istisnanın ADI gerekçeden düşerse geriye sessiz bir güven kalır.
    capraz = "" if not gf_hata else (
        f" — DİKKAT: çapraz doğrulama KOŞAMADI (watchdog.goal_failure_report düştü: {gf_hata}), "
        f"bu sayı bu koşumda ikinci bir okumayla karşılaştırılmadı")
    return _hukum(r30, esik, gecti,
                  f"defterin TAMAMINDAN 30 güne ölçeklenmiş getiri {_oran(r30)} "
                  f"{'≥' if gecti else '<'} hedef {_oran(esik)} ({pencere_gun} işlem günü, "
                  f"{n} defter satırı) — {OLCEK_SERHI}{capraz}")


def _sharpe(goal, sd, meta, yetersiz, pencere_gun, ornek_neden) -> dict:
    """`min_sharpe` — kapının kendi skorlayıcısındaki sharpe tabanı GEÇİLDİ mi?

    `score.score_detail` ölçülemeyen sharpe'ı MUHAFAZAKÂR 0.0 döndürür ve gerçeği ayrı bir
    bayrakta taşır (`sharpe_measurable`). Bayrağı okumayan bir tüketici "0.0 < taban → KALDI"
    der; bu, ölçülmemiş bir şeyi ÖLÇÜLMÜŞ VE BAŞARISIZ gibi raporlamaktır."""
    esik = goal.get("min_sharpe")
    if esik is None:
        return _hukum(None, None, None, "goal.yaml'da `min_sharpe` yok — hüküm verilecek eşik yok")
    esik = float(esik)
    if ornek_neden:
        return _hukum(None, esik, None, ornek_neden)
    engel = _meta_engel(meta)
    if engel:
        return _hukum(None, esik, None, engel)
    if not sd.get("sharpe_measurable"):
        return _hukum(None, esik, None,
                      f"işlem getirilerinin varyansı ölçülemedi (n={sd.get('n')}) — "
                      f"score.score_detail bu hâlde 0.0 döndürür ama bu 'ölçüldü sıfır' değil "
                      f"'ÖLÇÜLEMEDİ'dir")
    if yetersiz:
        # Sharpe da pencereye bağlıdır: `score.score_detail` onu defterin süresinden türettiği
        # yıllık işlem sayısının KAREKÖKÜYLE ölçekler — kısa defterde sayı absürtleşir (fonksiyonun
        # kendi şerhi: 183 günlük pencere içindeki 20 günlük küme sharpe'ı absürt ölçekliyordu).
        return _hukum(None, esik, None,
                      f"{yetersiz} — sharpe defterin süresinden yıllıklandırılır, kısa pencerede "
                      f"karekök ölçeği sayıyı ölçüm olmaktan çıkarır")
    sharpe = float(sd["sharpe"])
    gecti = sharpe >= esik
    return _hukum(sharpe, esik, gecti,
                  f"sharpe {sharpe:.3f} {'≥' if gecti else '<'} taban {esik:.3f} "
                  f"({pencere_gun} işlem günü, {sd.get('n')} defter satırı)")


def _drawdown(goal, sd, meta, ornek_neden) -> dict:
    """`max_drawdown` — azami tepe-dip düşüşü tavanı AŞMADI mı?

    YÖN TERSTİR: diğer üç soruda büyük iyidir, burada KÜÇÜK iyidir. Karşılaştırma çevrilirse
    karne, tavanı aşan her defteri "geçti" diye raporlar — üstelik tam da alarmın sustuğu yerde.

    PENCERE UZUNLUĞUNA BAĞLANMAZ, BİLİNÇLİ: drawdown bir YOL istatistiğidir (`score.max_drawdown`
    eğri üzerinde tepe-dip tarar), 30 güne ölçeklenmiş bir oran değil. Kısa defterde de gerçek
    bir ölçümdür — yalnız defterin GÖRDÜĞÜ yol kadarını görür ve o kısıt kapsam beyanındadır.

    AMA META-KAPILARA TABİDİR (denetim MEDIUM-6): eskiden `ayrisma` parametresini HİÇ almıyordu,
    `_sharpe` ise alıyordu — kapı tutarsız dağıtılmıştı. Nedensel okuma tutarsızlığı çözer:
    ayrışmanın en olası sebebi iki okumanın DEFTERİNİN farklı olmasıdır, ve o hâlde `sd`den gelen
    her sayı şüphelidir. Tazelik de aynı: bayat bir yol istatistiği GÜNCEL bir hüküm değildir."""
    esik = goal.get("max_drawdown")
    if esik is None:
        return _hukum(None, None, None,
                      "goal.yaml'da `max_drawdown` yok — hüküm verilecek eşik yok")
    esik = float(esik)
    if ornek_neden:
        return _hukum(None, esik, None, ornek_neden)
    engel = _meta_engel(meta)
    if engel:
        return _hukum(None, esik, None, engel)
    dd = sd.get("max_drawdown")
    if dd is None:
        return _hukum(None, esik, None,
                      "score.score_detail drawdown döndürmedi — hüküm kurulamadı")
    dd = float(dd)
    gecti = dd <= esik
    return _hukum(dd, esik, gecti,
                  f"azami çekilme {dd:.2%} {'≤' if gecti else '>'} tavan {esik:.2%} "
                  f"(KAPANMIŞ işlem eğrisi; açık pozisyon çekilmesi bu sayıda görünmez)")


def _failure(goal, gf, gf_hata, meta, yetersiz, pencere_gun) -> dict:
    """`failure_below` — SÖZLEŞMENİN BAŞARISIZLIK HÜKMÜ. Sahibi `watchdog.goal_failure_report`.

    Eşik de oradan alınır (`threshold`): watchdog goal.yaml'ı zaten okudu, ikinci kez okumak
    ikinci bir kaynak olurdu.

    SIRA TAŞIYICIDIR — `failed` META-KAPILARDAN ÖNCE SORULUR (denetim MEDIUM-1). İlk sürümde
    `ayrisma` daha önce geliyordu, yani ayrışma günü watchdog'un `failed=True`si OLCULEMEDI'ye
    çevriliyordu: modül başlığının MUTLAK biçimde reddettiği şey. Meta-kapı bir hükmü ancak
    CEVABI DEĞİŞTİREBİLECEKSE yutar:
      · `failed=True`  → KALDI, meta-kapılar ŞERH olarak düşer (hüküm susturulmaz);
      · `failed=False` → kırılgan cevap; kısa pencere / ayrışma / bayatlık onu hükümsüz kılar.
        "Hiç başarısız olmadı" ile "hiç ölçülmedi" ayrımı tam burada yaşar.
    """
    if gf_hata:
        return _hukum(None, goal.get("failure_below"), None,
                      f"başarısızlık hükmünün tek kaynağı (watchdog.goal_failure_report) düştü: "
                      f"{gf_hata} — 'başarısız değil' DEĞİL, 'ölçemedim'")
    esik = gf.get("threshold")
    if gf.get("kapsam_disi"):
        return _hukum(None, esik, None, gf.get("neden") or "başarısızlık eşiği tanımlı değil")
    failed = gf.get("failed")
    if failed is None:
        return _hukum(None, esik, None,
                      (gf.get("neden") or "watchdog hüküm veremedi (gerekçe bildirilmedi)")
                      + _meta_serh(meta))
    r30 = gf.get("realized_30d")
    if failed:
        # META-KAPILAR BURADA KONUŞUR AMA YUTMAZ — bu dal `_meta_engel`i BİLEREK çağırmaz.
        # `deger_zorunlu=False` AYNI İLKENİN ÜÇÜNCÜ AYAĞIDIR (denetim LOW-1): `r30 is None`
        # hâlinde sözleşme kapısı hükmü OLCULEMEDI'ye düşürürdü — yani meta-kapıların yapmasını
        # yasakladığımız şeyi sözleşme kapısı yapardı. Eksik sayı ŞERH olarak gider.
        serh = _meta_serh(tuple(meta) + ((f"pencere yetersiz: {yetersiz}",) if yetersiz else ()))
        return _hukum(None if r30 is None else float(r30), esik, False,
                      f"{gf.get('neden')} — {OLCEK_SERHI}{serh}", deger_zorunlu=False)
    engel = _meta_engel(meta)
    if engel:
        return _hukum(None, esik, None, engel)
    if yetersiz:
        return _hukum(None, esik, None,
                      f"{yetersiz} — 'başarısız DEĞİL' ile 'HENÜZ ÖLÇÜLEMEDİ' bu pencerede ayırt "
                      f"edilemez; ham oran {_oran(r30)} bir ölçüm değildir")
    return _hukum(None if r30 is None else float(r30), esik, True,
                  f"{gf.get('neden')} ({pencere_gun} işlem günü) — {OLCEK_SERHI}")


# ---------------------------------------------------------------------------------------------
# KAPSAM BEYANI ve CLI
# ---------------------------------------------------------------------------------------------
def kapsam_beyani(sonuc: dict) -> str:
    """HER koşumda basılan cümle: NEREYE baktım, orada NEyi göremedim.

    Boş/hükümsüz bir karne "sistem iyi" demek DEĞİLDİR ve bunu söyleyecek tek yer burasıdır;
    kapsamsız bir sonuç, tamlık ima ederek yanıltır.

    YENİ ALANLAR `.get()` İLE OKUNUR — sözleşme gereği: Görev 2'nin çivileri bu fonksiyonu KENDİ
    sentetik `kapsam` sözlükleriyle çağırıyor (taklit yazmamak için, doğru karar). Köşeli parantez
    kullanmak, Görev 1'e eklenen her alanı Görev 2'de KeyError'a çevirirdi."""
    k = sonuc["kapsam"]
    pencere = (f"{k['pencere_islem_gunu']}/{k['pencere_gereken']} işlem günü"
               if k["pencere_islem_gunu"] is not None else f"ÖLÇÜLEMEDİ ({k['pencere_neden']})")
    # SESSİZLİK: `bayat is None` ile `bayat is False` AYNI CÜMLEYE indirgenemez — biri "ölçtüm,
    # taze", öteki "ölçemedim". Bu dosyanın tamamı o ayrımın üstüne kurulu.
    if k.get("bayat") is None:
        sessizlik = f"ÖLÇÜLEMEDİ ({k.get('bayat_neden') or 'gerekçe yok'})"
    else:
        sessizlik = (f"{k.get('sessizlik_islem_gunu')} işlem günü / eşik "
                     f"{k.get('bayat_esik_gun')} → {'BAYAT' if k['bayat'] else 'taze'}")
    # ÖRNEKLEM CÜMLESİ ÜÇ HÂLLİDİR, İKİ DEĞİL (denetim LOW-7). `ornek_yeterli=False` iken eşik
    # yoksa (`min_ornek is None`) suçlanan şey ÖRNEKLEM olamaz: örneklem bol olabilir, eksik olan
    # `goal.yaml` anahtarıdır ve `score.score_detail` hiç koşmamıştır. Eski cümle "örneklem
    # YETERSİZ (asgari None)" basıyordu — yanlış boşluğu, yanlış sebeple.
    if k.get("ornek_yeterli"):
        ornek = f"örneklem YETERLİ (asgari {k['min_ornek']})"
    elif k.get("min_ornek") is not None:
        ornek = f"örneklem YETERSİZ (asgari {k['min_ornek']})"
    else:
        ornek = ("örneklem ÖLÇÜLEMEDİ (asgari eşik de yok — bu bir örneklem kıtlığı DEĞİL): "
                 + (k.get("ornek_neden") or "gerekçe bildirilmedi"))
    return (
        f"{k['defter']} ({'SQLite' if k['defter_db_destekli'] else 'dosya'} katmanı) — "
        f"{k['islem_sayisi']} defter satırı, {ornek}; "
        # DAMGASIZ SATIRLAR TOPLAMIN İÇİNDEDİR ve bu AÇIKÇA söylenir: eski cümle aynı toplamı
        # "kapanan işlem" diye etiketleyip damgasızları ayrıca sayıyordu — iki iddia tek cümlede
        # birbirini yalanlıyordu (denetim LOW-13). `ts_close`suz satır pencereye giremez ama
        # score.score_detail'in `n`ine GİRER; ikisi farklı sayılardır.
        f"bunların {k['damgasiz_satir']} tanesinde `ts_close` YOK (pencere/tazelik hesabına "
        f"girmediler, skorlayıcının örneklemine GİRDİLER) · "
        f"pencere {k['ilk_kapanis']} → {k['son_kapanis']} = {pencere} · "
        f"sessizlik ({k.get('son_kapanis')} → bugün {k.get('bugun')}): {sessizlik} "
        f"[takvim: {k['takvim_kaynagi']}]"
        + (f" · {k['ayrisma']}" if k["ayrisma"] else "")
        + " · BU KAPSAMIN DIŞI GÖRÜLMEDİ: " + " | ".join(k["goremedigim"])
    )


def _bas(sonuc: dict) -> None:
    print("# KARNE — state/goal.yaml'ın dört sorusu (deterministik hesap, model yok)")
    for ad in SORULAR:
        h = sonuc["hukumler"][ad]
        deger = "—" if h["deger"] is None else f"{float(h['deger']):.4f}"
        esik = "—" if h["esik"] is None else f"{float(h['esik']):.4f}"
        print(f"\n## {ad}: {h['hukum']}")
        print(f"    deger : {deger}")
        print(f"    esik  : {esik}")
        print(f"    neden : {h['neden']}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    # `--uygula` / `--defter` BİLEREK YOK: bkz. modül başlığı ("BU ARAÇ YAZMAZ") ve DEFTER şerhi.
    ap.add_argument("--json", action="store_true", help="ham sonucu JSON olarak bas")
    args = ap.parse_args(argv)

    try:
        sonuc = hesapla()
    except Exception as e:
        # Sinyal: istisna operatöre ADIYLA gider. Sessiz bir "hüküm yok" çıktısı, karneyi
        # koşmamakla koşup ölçememeyi aynı görüntüye indirirdi.
        print(f"KARNE HESAPLANAMADI: {type(e).__name__}: {e} — HİÇBİR HÜKÜM VERİLMEDİ. Bu "
              f"'deney iyi gidiyor' DEĞİL, 'ölçüm koşamadı' demektir.", file=sys.stderr)
        return 2

    olculemedi = [a for a in SORULAR if sonuc["hukumler"][a]["hukum"] == _OLCULEMEDI]
    # ÇIKIŞ KODU — SUBSTRATIN SÖZLEŞMESİ, BEYANLI SAPMAYLA (denetim LOW-12).
    # `ops/bekci_tarama.py`: 0 = ölçüm KOŞTU (bulgu olsun olmasın), 2 = ölçüm KOŞAMADI. Karne
    # eskiden yalnız `hesapla()` istisna atarsa 2 dönüyordu; takvim düşse ya da defter boş olsa
    # DÖRT hüküm de OLCULEMEDI oluyor ve çıkış yine 0 kalıyordu — yani Görev 3'ün birimi TAM
    # ÖLÇÜM KESİNTİSİNDE sonsuza dek yeşil görünürdü. Tam kesinti bir MEKANİZMA ARIZASIDIR.
    # SAPMA (bilinçli): TEK bir KALDI hâlâ 0 döner. Rapor aracında bulgu ≠ arıza; aksi hâlde
    # deneyin kötü geçen her haftası "birim arızası" diye görünür ve operatör birimi susturur.
    rc = 2 if len(olculemedi) == len(SORULAR) else 0
    if args.json:
        # KAPSAM HER KOŞUMDA GİDER — JSON kipinde de. Metin satırlarını stdout'a karıştırmak
        # çıktıyı ayrıştırılamaz yapardı; kapsam bu yüzden YÜKÜN İÇİNDE taşınır. Böylece
        # `--json > dosya` diyen operatör de "neyi göremedim"i dosyada bulur.
        print(json.dumps(dict(sonuc, kapsam_beyani=kapsam_beyani(sonuc), olculemedi=olculemedi),
                         ensure_ascii=False, indent=2, default=str))
        return rc

    _bas(sonuc)
    print(f"\n# kapsam: {kapsam_beyani(sonuc)}")
    print(f"# ölçülemedi: {len(olculemedi)}/{len(SORULAR)} hüküm "
          f"({', '.join(olculemedi) if olculemedi else '—'}) — SIFIR SAYILMADI"
          + (" · TAM ÖLÇÜM KESİNTİSİ (çıkış 2): hiçbir soru cevaplanamadı, bu 'deney iyi "
             "gidiyor' DEĞİL 'karne ölçemedi' demektir" if rc else ""))
    return rc


if __name__ == "__main__":
    sys.exit(main())
