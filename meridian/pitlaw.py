"""pitlaw.py — "PIT'siz fundamentals proxy YASAK" yasasının İLK mekanik denetçisi.

CLAUDE.md §4 bu yasağı sayar ama 2026-08-30 ölçümüne kadar hiçbir kapı onu zorlamıyordu:
`guard.py`de yok, `codelaw.py`da yok, `tests/` altında çivi yok. Yasa tamamen ricaya dayalıydı.
Bu modül onu kaynaktan, çalışma zamanına hiç dokunmadan ölçer.

NEYİ YASAKLIYORUZ — ve neyi yasaklamıyoruz. Geriye-dönük önyargı (look-ahead) PIT olmayan bir
kaynağın KENDİSİNDEN doğmaz; kaynağın GEÇMİŞ BİR TARİHE sorulmasından doğar. Kazanç takvimine
"bugün önümüzdeki 5 gün rapor var mı" diye sormak meşrudur (tarih gerçekten önceden duyurulur);
AYNI takvime "2023-04-11'de önümüzdeki 5 gün rapor var mıydı" diye sormak uydurmadır — dosya o
günü hiç saklamadı, bugünün ileri penceresini gösterir. Bu yüzden hüküm İKİ DÜNYADIR ve ayrıdır
(emsal: `codelaw.stale_line_anchors` sıfır-tolerans vs `stale_tsx_line_anchors` çırçır):

  TARİHSEL YOL (`TARIHSEL_YOL`) — replay/geri-dolum/tohum: SIFIR TOLERANS. Bugünün anlık
  görüntüsü tarihsel bir seansa uygulanamaz. Emsal ZATEN KODDA: `backtest.replay` ve
  `cf_backfill._plans_for_session` `in_blackout`u bilerek kesti ve yerine `olculemedi_replay`/
  `olculemedi_cf` sayacı koydu — bu modül o hükmü GENELLEŞTİRİR.

  CANLI KARAR YOLU (`CANLI_KARAR_YOLU`) — ileri-bakışlı soru meşru, ama SAYILIR: taban
  (`CANLI_TABAN`) tek yönlüdür, borç BÜYÜYEMEZ. Yeni bir PIT-dışı kaynağı canlı kapıya bağlamak
  bilinçli bir karar olmalıdır, sessiz bir ekleme değil.

KAPSAM BEYANI — SIFIR SONUÇ "YOK" DEMEK DEĞİL, "BU KAPSAMDA BULUNAMADI" DEMEKTİR. Tarayıcı
DOĞRUDAN çağrıyı (`earnings.in_blackout(...)`) ve modül-içi kapanımla ULAŞILAN çağrıyı
(`backtest → strategy.scan_entry → … → days_since_report`) görür. GÖREMEDİKLERİ `gorulmeyen`
kovasına ADIYLA yazılır: dinamik erişim (`getattr`), sözlükten çağrı, kaynak kaydında OLMAYAN bir
adaptör. Görülmeyen ihlal SAYILMAZ (uydurma yasağı) ama SAYILIR — `ok`u etkilemez, rapora çıkar.

Modül SAF DENETİMDİR: durum değiştirmez, karar vermez, diske yazmaz; yalnız kaynak ağacını okur.
Dosya kümesi/okuma/AST/çağrı indeksi `codelaw`ın gövdelerinden gelir — ikinci bir kopya aynı
yasanın iki sürümünü doğururdu (`codelaw._py_files`, `_ast_oku`, `_call_index`, `_note_unscanned`,
`_site_key`; emsal: `trend_shadow` → `adapters.data.bars_integrity`)."""
from __future__ import annotations

import ast
import pathlib
from typing import Any

from . import codelaw

#: Üretim kaynak ağacı. Bundan FARKLI bir kök SENTETİKtir ve canlı beyan defterleri orada koşmaz.
VARSAYILAN_KOK = "meridian"

# ---------------------------------------------------------------------------
# (1) KAYNAK KAYDI — ÖLÇÜLDÜ 2026-08-30, kaynak koddan (ağ çağrısı YAPILMADI)
# ---------------------------------------------------------------------------
# `(modül kökü, fonksiyon)` → sınıf + gerekçe. SINIF AYRIMI HÜKMÜ TAŞIR:
#   "karar_etkili" → dönüşü bir veto/sinyal/skor/kapı belirler. Yasanın konusu BUDUR.
#   "bilgi"        → dönüşü yalnız etikete/loga/panoya gider; karar yolunu DEĞİŞTİRMEZ.
# Ayrım UYDURULMADI, çağrı yerinden okundu: `loop.py`de `earnings.known()` dönüşü yalnız
# `greasons`a metin ekler ve `verdict` o satırda yeniden ATANMAZ (`earnings.COVERAGE_NOTE`
# beyanı: "karar yolu DEĞİŞMEZ"); `in_blackout` dönüşü ise `verdict = "NO_GO"` yazar.
PIT_DISI_KAYNAKLAR: dict[tuple[str, str], dict[str, str]] = {
    # --- earnings: state/earnings.csv, İLERİ-PENCERE tazeleme önbelleği --------------------
    # Modülün kendi ölçümü (`earnings.takvim_ufku` docstring'i, kart EDG-2026-060, 2026-08-25):
    # "takvim bir NOKTA-ZAMAN ARŞİVİ DEĞİL, ileriye dönük bir tazeleme önbelleğidir; geçmiş
    # seanslar için çapa sorusu sorulamaz". `refresh` geri çekilen GELECEK tarihleri dosyadan
    # SİLER — dünkü hüküm bugünkü dosyadan yeniden üretilemez.
    ("earnings", "in_blackout"): {
        "sinif": "karar_etkili",
        "gerekce": "dönüşü loop.daily_cycle'da verdict='NO_GO' yazar (sert veto); "
                   "kaynak state/earnings.csv PIT değil, bugünün ileri penceresi"},
    ("earnings", "days_since_report"): {
        "sinif": "karar_etkili",
        "gerekce": "episodic_pivot ve pead kurulumlarının ZORUNLU çapası; False dönerse "
                   "sinyal HİÇ üretilmez (arming.PIT_CAPALI_KURULUMLAR kaydının konusu)"},
    ("earnings", "calendar_untrustworthy"): {
        "sinif": "karar_etkili",
        "gerekce": "True dönerse o turdaki TÜM GO planları REVIEW'e düşer (kapı sıkıştırma)"},
    ("earnings", "known"): {
        "sinif": "bilgi",
        "gerekce": "yalnız gate_reasons'a COVERAGE_NOTE metni ekler; verdict yeniden atanmaz"},
    ("earnings", "coverage"): {
        "sinif": "bilgi", "gerekce": "watchdog açlık dedektörü + rapor sayacı"},
    ("earnings", "blackout_radar"): {
        "sinif": "bilgi", "gerekce": "/api/state panosu — 'bugün kim karartmada' listesi"},
    ("earnings", "takvim_ufku"): {
        "sinif": "bilgi",
        "gerekce": "arming._kanit_durumu'nda insufficient_cf ↔ olculemez_pit_yok ayrımı; "
                   "kurulum ateşlemesini DEĞİL, rapor cümlesini seçer"},
    # --- insider (Form-4): state/insider_signals.json, her koşuda ÜZERİNE YAZILAN anlık özet ---
    # Ham defter (state/insider_trades.json) `filing_tarihi` TAŞIR — yani PIT yeniden kurulabilir;
    # ama `ozet` onu özete taşımaz ve pencereyi `date.today()` ile keser.
    ("insider", "ozet"): {
        "sinif": "bilgi",
        "gerekce": "scheduler._y4_collect → scheduler_status.json → pano; karar tüketicisi YOK "
                   "(codelaw beyanı: sınıflama penceresi dolmadan kapıya bağlanmaz)"},
    ("insider", "durum"): {"sinif": "bilgi", "gerekce": "pano sağlayıcı kartı"},
    # --- short_interest: FINRA, settlement_date TAŞIR ama seri DEĞİL (yalnız son yayın) -------
    ("shortinterest", "ozet"): {
        "sinif": "bilgi",
        "gerekce": "veri ~9 iş günü eski; kaçınma filtresi olarak kapıya bağlanması karşı-olgusal "
                   "ölçümden SONRAKİ turun işi (codelaw beyanı)"},
    ("shortinterest", "durum"): {"sinif": "bilgi", "gerekce": "pano sağlayıcı kartı"},
    ("shortinterest", "float_cek"): {
        "sinif": "bilgi",
        "gerekce": "FMP profile'dan tarihsiz float; önbellek KALICI — bir kez yazılan payda "
                   "hem geçmiş hem bugün için aynı sayıyla kullanılır"},
    # --- FMP: hepsi 'şu an sağlayıcının bildiği' anlık görüntü ------------------------------
    ("fmp", "earnings_dates"): {
        "sinif": "bilgi",
        "gerekce": "earnings.refresh_from_fmp yedek bacağı; dönüş list[str], as-of alanı yok"},
    ("fmp", "profile"): {
        "sinif": "bilgi", "gerekce": "tek tüketici shortinterest.float_cek; tarihsiz snapshot"},
    ("fmp", "sp500_constituents"): {
        "sinif": "bilgi",
        "gerekce": "kendi docstring'i: 'survivorship-biased; use only for a live universe, "
                   "not backtests'"},
    # --- Nasdaq kazanç takvimi (anahtarsız, BİRİNCİL kaynak) -------------------------------
    ("data", "nasdaq_earnings_window"): {
        "sinif": "bilgi",
        "gerekce": "tarih satırdan değil SORGUNUN kendi gününden gelir; duyuru damgası üretmez"},
    # --- finviz: anlık ekran; önbellek anahtarı sunucunun YEREL TAKVİM GÜNÜ -----------------
    ("finviz", "discover"): {
        "sinif": "bilgi", "gerekce": "evren genişletme; ekran anlık, geçmiş gün sorulamaz"},
    ("finviz", "discover_universe"): {
        "sinif": "bilgi",
        "gerekce": "dataset._load_live_inner evrenini genişletir. NOT: filtreleri tamamen "
                   "teknik/likidite (fa_* alanı YOK) — temel-veri kaydında olması kaynağın "
                   "PIT'sizliği yüzündendir, temel-veri taşıdığı için değil"},
    ("constituents", "current"): {
        "sinif": "bilgi", "gerekce": "güncel S&P 500 üyeliği; universe_drift raporu"},
}

# PIT SÖZLEŞMELİ KAYNAKLAR — beyaz liste. Buradaki bir sembolün tarihsel yolda çağrılması
# İHLAL DEĞİLDİR. Beyaz listeye girmenin şartı bir NİYET değil, kodda okunabilir bir as-of
# seçimidir.
PIT_KAYNAKLAR: dict[tuple[str, str], str] = {
    ("earnings_pit", "days_since_report_pit"):
        "filed <= on_date - 1 gün ile seçim (MUHAFAZAKÂR GÖRÜNÜRLÜK: dosyalamanın KENDİ günü "
        "DAHİL DEĞİL, çünkü 8-K kabul saati çoğunlukla kapanış sonrasıdır ve modül saat "
        "taşımaz). Kaynak `research/edgar_facts/earnings_8k_tarihleri.csv` — EDGAR 8-K item "
        "2.02 dökümü; her satır `report_date` VE `filed` taşır, yani görünürlük uydurulmaz. "
        "GLOBAL ufkun dışı ve arşivde HİÇ olmayan sembol `None` döner, False DEĞİL (uydurma "
        "yasağı: 'rapor yoktu' ile 'bilmiyoruz' ayrı sayılır — `sayac_oku()` üç kovayı okur). "
        "SINIRI KAYIT DA SÖYLER, gizlemez: ufuk GLOBAL ama kapsama SEMBOL-BAZLIdır — sembol "
        "arşivde varken kendi kapsaması o tarihte başlamamışsa cevap `None` değil FALSE'tur "
        "(modülün kendi K-1 ölçümü, `days_since_report_pit` başlığı: en sert vaka BLK, 8 satırın "
        "hepsi 2024-10, 724 seans False, gerçekte 11 rapor). Beyaz listeye girmenin şartı as-of "
        "seçimidir ve o KODDA OKUNUR; kapsama boşluğu ayrı bir eksendir ve kartın ≥%95 kapsama "
        "eşiği onu ölçer",
    ("edgar_shares", "as_of_shares"):
        "filed <= t ile seçim; kendi başlığı: 'end <= t PIT DEĞİLDİR, geleceği sızdırır'",
    ("edgar_shares", "as_of_shares_detay"):
        "as_of_shares'in neden-kodlu biçimi; ölçülemeyen hücre None + neden",
    ("edgar_shares", "as_of_shares_series"):
        "np.searchsorted(filed, d, side='right')-1 — t gününden ÖNCEKİ son dosyalama",
}

# PIT SÖZLEŞMELİ AMA BESLEYENİ KAPALI — ÜÇÜNCÜ KOVA, ve gerekli. `constituents.as_of` değişiklik
# günlüğünü geriye sararak üyeliği yeniden kurar (gerçek PIT iskelesi), AMA günlüğü dolduran
# Wikipedia yolu bu kurulumda HTTP 403 alıyor (modül başlığında ölçülü) ve FMP dalı `changes`
# üretmez. Günlük boşken `as_of(t)` GÜNCEL listeyi döner = survivorship. Beyaz listeye koymak
# "sözleşme var" diye "veri PIT" demek olurdu; kara listeye koymak sözleşmeyi yok saymak olurdu.
PIT_SOZLESMELI_BESLEYENI_KAPALI: dict[tuple[str, str], str] = {
    ("constituents", "as_of"):
        "as_of iskelesi gerçek, ama changes günlüğü boşken güncel listeye düşer (survivorship). "
        "Üretim çağıranı bugün YOK; besleyen açılırsa PIT_KAYNAKLAR'a taşınır",
}

# ---------------------------------------------------------------------------
# (2) İKİ DÜNYA — hangi modülde hangi hüküm koşar
# ---------------------------------------------------------------------------
# TARİHSEL YOL: geçmiş bir seansı yeniden yürüten modüller. Ölçüt bir isim benzerliği değil,
# modülün geçmiş bir TARİHİ argüman olarak dolaştırmasıdır.
TARIHSEL_YOL: dict[str, str] = {
    "backtest.py": "replay: geçmiş barlar üzerinde gün gün yeniden yürütme",
    "cf_backfill.py": "karşı-olgusal defteri TÜM TARİHİ SEANSLARA koşturan geri-dolum",
    "component_ic.py": "bileşen IC'si — tarihsel kesitlerde ileri getiri ölçümü",
    "shadow_lifecycle.py": "gölge kitapları; `_seed` bacağı tarihsel seansları yürütür",
}

# CANLI KARAR YOLU: bugünün kararını üreten modüller. İleri-bakışlı soru meşru; sayım yine tutulur.
CANLI_KARAR_YOLU: dict[str, str] = {
    "loop.py": "daily_cycle — plan, kapı hükmü, silahlanma",
    "strategy.py": "sinyal üreticileri ve skor",
    "guard.py": "classify_gate / check_trade — üç durumlu disiplin",
    "score.py": "skor bileşimi",
    "prescreen.py": "knob ön-elemesi",
    "sieve.py": "aday eleme",
    "probgate.py": "olasılık kapısı",
    "shadow_variants.py": "varyant hükmü (canlı turda canlı kapıların aynısı)",
}

# CANLI TABAN — ÇIRÇIR. Bugün ölçülen karar-etkili canlı çağrı yeri sayısı (2026-08-30).
# Taban TEK YÖNLÜDÜR: düşer, YÜKSELMEZ. Yükseltmek yasanın kendisini gevşetmek olurdu; borcun
# BÜYÜMESİNİ engellemek bu çivinin asıl işidir (emsal: codelaw.TSX_CAPA_TABANI).
# Ölçüm dökümü — dördü de `state/earnings.csv` tüketicisi:
#   loop.py::daily_cycle          → earnings.calendar_untrustworthy   (GO→REVIEW)
#   loop.py::daily_cycle          → earnings.in_blackout              (sert NO_GO)
#   strategy.py::evaluate_episodic_pivot → earnings.days_since_report (zorunlu çapa)
#   strategy.py::evaluate_pead           → earnings.days_since_report (zorunlu çapa)
# `shadow_variants.py::_judge` içindeki `in_blackout` çağrısı da canlı yoldadır ve SAYILIR
# (taban 5'in beşincisi): tohum turunda `if pit:` ile korunur, canlı turda korunmaz.
CANLI_TABAN = 5

# ---------------------------------------------------------------------------
# (3) BİLİNEN İHLALLER — ÖLÇÜLDÜ, DÜZELTİLMEDİ (düzeltme AYRI KARAR)
# ---------------------------------------------------------------------------
# Bu bir allowlist DEĞİLDİR: yasa ihlali saymaya devam eder, `rapor()` onu ADIYLA verir ve
# `bilinen_ihlaller` alanında görünür. Beyanın etkisi yalnız `ok` hükmüne dokunmamasıdır —
# aksi hâlde çivi ilk günden kırmızı doğar ve KAPATILIRDI; kapatılan çivi çivi değildir.
# Kayıt düşerse (`bilinen_ihlal_curudu`) beyan da düşer: ölü muafiyet çürüktür.
#
# BUGÜN BOŞ — VE BOŞLUK BİR BAŞARIDIR, BİR EKSİKLİK DEĞİL (2026-08-31, EDG-2026-062). Defterin
# iki kaydı vardı (`backtest.py` ve `cf_backfill.py` → `earnings.days_since_report`) ve ikisi de
# kaydın kendi yazdığı iki yoldan İKİNCİSİYLE kapandı: "ya çapa replay'de kesilir ya PIT arşivine
# BAĞLANIR". Bağlandı — kayıtlar `PIT_KORUMALI_ZINCIRLER`e TAŞINDI (silinmedi: zincir hâlâ statik
# olarak görünür, hüküm hâlâ beyanla verilir; değişen, beyanın SINIFIdır — borç değil, kapatılmış
# yol). Boş defteri bir yer tutucuyla doldurmak ölü kayıt üretirdi ve bu deponun yasasına göre ölü
# kayıt çürüktür; `test_BEYANLARIN_hepsi_hala_GERCEK` beklentiyi kayıttan TÜRETİR, yani bu sözlük
# yarın yeniden dolarsa çivi kendiliğinden iki yönlü çalışmaya devam eder.
BILINEN_IHLALLER: dict[tuple[str, str, str], str] = {}

# KOŞUL-KORUMALI ZİNCİRLER — İHLAL DEĞİL, ama tarayıcı BUNU GÖREMEZ.
# Statik tarayıcı bir çağrının hangi koşul altında koştuğunu DEĞERLENDİREMEZ. İKİ KORUMA BİÇİMİ
# ölçüldü ve ikisi de aynı sınıftadır (zincir görünür, PIT'siz kaynağa VARILMAZ):
#   · KOŞUL — `shadow_variants._judge` `in_blackout`u `if pit:` bloğunun içinde çağırır: canlı
#     turda çalışır, TOHUM (tarihsel) turunda hiç çağrılmaz ve `earnings_blackout` False değil
#     None kalır ("karartma yok" ile "ölçemedik" aynı şey değildir — kardeş-PIT düzeltmesi).
#   · SEVK — `backtest`/`cf_backfill` çapayı `params["earnings.pit_arsiv"]` ile PIT arşivine
#     yönlendirir (EDG-2026-062): PIT'siz dal tarihsel yolda hiç koşmaz.
# Yani zincir görünür ama yasa ihlal edilmez. Bunu `BILINEN_IHLALLER`e koymak yanlış olurdu:
# orası DÜZELTİLMEMİŞ borcun defteri, burası ise ÖLÇÜLMÜŞ ve KAPATILMIŞ bir yolun kaydı. Ayrımı
# silmek, düzeltilmiş işi borç gibi göstermek olurdu.
# HER İKİ BİÇİMDE DE BEYAN KORUMANIN KENDİSİNE BAĞLIDIR ve bu bir dilek değil bir ölçümdür:
# koruma kalktığı gün kayıt ÇÜRÜR.
#
# ÇİVİ ALANI — VE NEDEN KAYDIN İÇİNDE (2026-08-31, EDG-2026-062 düzeltme turu 1). "Koruma
# kalkarsa kayıt çürür" cümlesi 2026-08-30'da MEKANİK DEĞİLDİ ve bu ÖLÇÜLDÜ: sevk `strategy`den
# kaldırıldığında `rapor()["ok"]` YEŞİL KALIYOR, `tarihsel_dolayli_korumali` birebir aynı
# basılıyor — çünkü kova seçimi (`_kayitta`) yalnız ANAHTAR aramasıdır ve korumayı hiç sormaz.
# O gün üç kaydın üçünün de bir çivisi olması bir GELENEKTİ, bir YAPI değil: dördüncü kayıt
# hiçbir çivi talep etmeden doğabilir ve doğduğu gün kendi kendini doğrulayan beyan olurdu.
# Her kayıt artık korumasını çürütebilen çiviyi ADIYLA taşır (`civi`) ve `koruma_civisi_denetimi`
# o sembolün kaynakta GERÇEKTEN var olduğunu ölçer — emsal `KAPI_SOZLESMELERI` /
# `SINYAL_SOZLESMELERI` denetimi ("kayıtsız kapı yüzeyi doğduğu gün çivi öter", CLAUDE.md §4).
# ÇAPA SEMBOLDÜR, SATIR DEĞİL (`dosya::test_fn`): satır kayar, sembol kaymaz.
#
# İKİ YÖN DE BAĞLI — ve ikinci yön ZATEN vardı, bu tur birinciyi ekledi:
#   ileri  → kayıttaki her koruma bir çivi ADI taşır ve o çivi kaynakta vardır (`koruma_civisi_
#            denetimi`); yoksa `ok` düşer.
#   geri   → kayıtta OLMAYAN bir korumalı zincir zaten `tarihsel_dolayli_beyansiz`a düşer ve
#            `ok`u sıfır toleransla kırar; yani "beyansız koruma" hiçbir zaman sessiz kalmadı.
# KAPSAM BEYANI: denetim çivinin VARLIĞINI ölçer, DOĞRULUĞUNU değil — adı taşınan bir test
# fonksiyonu gövdesi boşaltılırsa bu denetim sessiz kalır. Gövdenin ısırdığını gösteren şey
# mutasyondur (§6) ve o insan disiplinidir; buradaki mekanik, "hiç çivi yok" hâlini imkânsız kılar.
PIT_KORUMALI_ZINCIRLER: dict[tuple[str, str, str], dict[str, str]] = {
    ("shadow_lifecycle.py", "earnings", "in_blackout"): {
        "gerekce":
        "ÖLÇÜLDÜ 2026-08-30 — shadow_lifecycle._seed → shadow_variants._judge zinciri görünür, "
        "ama `_judge` çağrıyı `if pit:` ile korur (kardeş-PIT düzeltmesi): tarihsel turda "
        "`in_blackout` HİÇ çağrılmaz, satır `olculemedi_seed` sayılır. Koruma kalkarsa bu kayıt "
        "ÇÜRÜR ve çivi öter — beyan, korumanın kendisine bağlıdır.",
        # Çivi bu turdan ÖNCE de vardı (2026-08-03, kardeş-PIT düzeltmesiyle birlikte); eksik olan
        # kayıt ile çivi arasındaki MEKANİK BAĞDI — ikisi iki ayrı dosyada birbirini bilmeden
        # duruyordu. Bağ artık burada.
        "civi": "tests/test_wpd_kardes_pit_v185.py"
                "::test_shadow_kapi_cagrisi_PIT_KOSULUNUN_ICINDE_yasar"},
    # --- EDG-2026-062: BORÇTAN KAPATILMIŞ YOLA. İkisi de 2026-08-30'da `BILINEN_IHLALLER`deydi;
    # koruma biçimi shadow_lifecycle'ınkinden FARKLIDIR (koşul değil SEVK) ama sınıf AYNIDIR:
    # zincir görünür, çağrı PIT'siz kaynağa varmaz, ve beyan korumanın kendisine bağlıdır.
    ("backtest.py", "earnings", "days_since_report"): {
        "gerekce":
        "ÖLÇÜLDÜ 2026-08-31 (EDG-2026-062) — zincir görünür (backtest.replay → strat.scan_entry "
        "→ scan_all → evaluate_episodic_pivot/evaluate_pead → earnings.days_since_report) ve "
        "statik tarayıcı onu değerlendiremez; ama `replay` çapayı SEVK EDER: "
        "`eff['earnings.pit_arsiv'] = True` yazar ve iki değerlendirici o param altında "
        "`earnings_pit.days_since_report_pit`i çağırır (EDGAR 8-K defteri, `filed <= seans-1`; "
        "PIT_KAYNAKLAR kaydı). PIT'siz `state/earnings.csv` dalı tarihsel yolda HİÇ koşmaz — "
        "canlı dal (param YOK) ise aynen durur ve CANLI_TABAN'da sayılıdır; bu tur canlı yolu "
        "DEĞİŞTİRMEDİ. KORUMA (sevk) KALKARSA BU KAYIT ÇÜRÜR VE ÇİVİ ÖTER — beyan, sevkin "
        "KENDİSİNE bağlıdır (sevksiz zincir yeniden BORÇTUR ve buraya değil "
        "`BILINEN_IHLALLER`e aittir).",
        "civi": "tests/test_pit_yasasi_v341.py::test_PIT_SEVKI_capa_blogunda_DURUYOR"},
    ("cf_backfill.py", "earnings", "days_since_report"): {
        "gerekce":
        "ÖLÇÜLDÜ 2026-08-31 (EDG-2026-062) — yukarıdakinin KARDEŞİ, AYNI sevk: "
        "`_plans_for_session` `eff['earnings.pit_arsiv'] = True` yazar ve anahtar İKİ tarama "
        "koluna da ulaşır (karar kolu `eff` + near-miss `rx`, `rx` `eff`ten türetilir; çivi "
        "`test_cf_param_IKI_scan_all_cagrisina_da_ulasir`, v345) — yani zincirin ucu "
        "`earnings_pit`tir. KAPSAM 2026-09-02'DE GENİŞLEDİ (EDG-2026-068 kartı, TSK-011): "
        "kuyruk artık `date`i SÜTUN olarak taşır (`reset_index()`, kardeş `backtest.replay` "
        "biçimi) ve iki kazanç-çapalı üretici cf'nin KENDİ ürettiği tarama satırlarında da "
        "çapaya ulaşır — fikstür kolunda ölçüldü: `pit_arsiv` {0,0,0} → "
        "{true:54, false:126, olculemedi:180}; beyanlı-sıfır çivisi kart kararıyla ters yöne "
        "devredildi (`test_cf_taramasi_KAZANC_CAPASINA_ULASIR`, v345 — eski ad tarihçe "
        "bloğunda). 2026-08-31 tarihli 'çapa HİÇ SORULMAZ / sayaç {0,0,0}' beyanı O GÜNÜN "
        "ölçümüydü ve kartla kapandı; gerçek-veri kolunun bileşim kıyası kartın açık kalemi. "
        "KORUMA (sevk) KALKARSA BU KAYIT ÇÜRÜR VE ÇİVİ ÖTER — beyan, sevkin KENDİSİNE bağlıdır.",
        # Kardeş kayıtla AYNI çivi ve bu doğru: çivi `arming.PIT_CAPALI_KURULUMLAR`tan türetilen
        # İKİ değerlendiriciyi de gezer, yani sevk hangi tarihsel motorun kolundan kalkarsa kalksın
        # aynı yerden ölçülür. Sevkin `cf_backfill` tarafına ULAŞTIĞI ise ayrı bir çividir
        # (`test_cf_param_IKI_scan_all_cagrisina_da_ulasir`, v345) — bu alan TEK ad taşır, o yüzden
        # buraya kaydın kendi gerekçesinde adıyla yazıldı.
        "civi": "tests/test_pit_yasasi_v341.py::test_PIT_SEVKI_capa_blogunda_DURUYOR"},
}

# ---------------------------------------------------------------------------
# (2b) SINIF ATAMASININ MEKANİK DENETİMİ — "ELLE BEYAN, MEKANİK ÇÜRÜTME"
# ---------------------------------------------------------------------------
# İLK ÇİVİNİN EN ZAYIF HALKASI BURASIYDI (2026-08-30 devir notu, §5): `karar_etkili` / `bilgi`
# ayrımı çağrı yerinden OKUNARAK yapılıyordu ama MEKANİK DEĞİLDİ. Bir `bilgi` sembolünün dönüşü
# yarın bir `verdict`e bağlanırsa kayıt sessizce yanlışlanır ve yasa o kaynağı bir daha hiç
# görmez — çünkü `karar_etkili()` süzgeci onu dışarıda bırakır. Yanlış sınıf, yasanın kendisini
# kapatan tek satırdır.
#
# BEYAN KALKMADI, ÇÜRÜTMESİ MEKANİKLEŞTİ (codelaw.declared_claims disiplini): kayıt gerekçeyi ve
# okunabilirliği taşımaya devam eder; `sinif_turet` aynı soruyu KAYNAKTAN sorar ve ikisi
# ayrışırsa suite kırmızıya döner. Otomatik türetimi TEK OTORİTE yapmak yanlış olurdu — türetim
# ölçemediği yerde `None` döner ve "ölçemedim"i "bilgi" saymak tam olarak uydurma olurdu.
#
# TÜRETİM KURALI (ölçülen çağrı yerlerinden çıkarıldı, uydurulmadı):
#   Bir sembol `karar_etkili`dir eğer bir KARAR MODÜLÜNDE, çağrısının sonucu (doğrudan ya da
#   atandığı ad üzerinden) bir `if`/`while` TESTİNE giriyorsa VE o dalın içinde bir KARAR EYLEMİ
#   varsa. Karar eylemi iki biçimdir: `KARAR_ADLARI`ndan birine atama, ya da erken `return`
#   (sinyal üretmemek de bir karardır — `evaluate_pead`in `return None`u tam olarak budur).
# Ölçülen üç biçim ve neden ayrıştıkları:
#   `strategy.evaluate_pead`      → çağrı DOĞRUDAN `if` testinde, dalda `return None`     → KARAR
#   `loop.daily_cycle::in_blackout` → `_bl = ...`, `if ... and _bl:` dalında `verdict = "NO_GO"` → KARAR
#   `loop.daily_cycle::known`     → `_ek = ...` hiçbir `if` TESTİNE girmez; yalnız üçlü ifade ve
#                                   `_checks.append({...})` sözlüğüne akar                 → BİLGİ
#: KAPI HÜKMÜNÜN TEK KAYNAĞI. Karar adları ELLE YAZILMAZ, buradan TÜRETİLİR.
#: `guard.classify_gate` docstring'i sözleşmeyi kendisi söyler: "Return (verdict, reasons) where
#: verdict ∈ {GO, REVIEW, NO_GO}" ve gövdesi üç yerde `return "<KARAR>", <gerekçe>` yapar. Kendi
#: beyanı da bunu pekiştirir: "BU FONKSİYON SERT ZARFIN TEK KAYNAĞIDIR" — `check_trade` bile
#: kopya tutmayı bırakıp onu çağırır, "iki yüzeyin ayrışması yapısal olarak imkânsız" olsun diye.
#: Karar adlarını ayrı bir listede tutmak, tam da o kopyayı yasa katmanında yeniden doğurmak olurdu.
#: LİSTE, TEK TUPLE DEĞİL — ve bugün TEK eleman taşıyor. Ölçüldü (2026-08-31): `meridian/` ağacında
#: karar sabiti döndüren tek fonksiyon `guard.classify_gate`tir, yani ikinci bir kapı yüzeyi BUGÜN
#: YOKTUR. Liste spekülatif bir genişletme değil: asıl kazanç `kapi_sozlesme_denetimi`nin İKİ YÖNLÜ
#: tamlığıdır (emsal: `arming.PIT_CAPALI_KURULUMLAR` / çivi v301) — kayıttaki her sözleşme kodda
#: GERÇEKTEN olmalı, VE karar sabiti döndüren her fonksiyon kayıtta olmalı. İkinci kapı yüzeyi
#: doğduğu gün çivi onu ADIYLA gösterir; bugün boş bir yer tutucu eklenmedi (ölü kayıt çürüktür).
KAPI_SOZLESMELERI: tuple[tuple[str, str], ...] = (
    ("guard.py", "classify_gate"),
)

#: SİNYAL ÜRETİMİNİN TEK KAYNAĞI. Erken `return` karar eylemi sayılır ama YALNIZ bir sinyal
#: üreticisinin içindeyse — bu küme de elle yazılmaz, `strategy.scan_all`dan türetilir.
#: `scan_all` değerlendiricilerin TEK kaydıdır ve kendi docstring'i bunu söyler: "Her ekran BU
#: ticker'da HER ZAMAN koşar (kısa devre yok) → {setup: EntrySignal}". Bir değerlendirici o
#: demete girmeden sinyal üretemez, dolayısıyla üreticiliğin ölçüsü o demettir.
#: LİSTE — kapı tarafıyla SİMETRİK. Bugün tek eleman: ölçüldü (2026-08-31), `strategy.py` dışında
#: hiçbir modülde değerlendirici adı bir `ast.Name` olarak geçmiyor (diğer tüm eşleşmeler yorum ya
#: da docstring), yani ikinci bir tarayıcı BUGÜN YOKTUR. Boş yer tutucu eklenmedi.
SINYAL_SOZLESMELERI: tuple[tuple[str, str], ...] = (
    ("strategy.py", "scan_all"),
)

#: "İKİNCİ TARAYICI" EŞİĞİ. Bir fonksiyon üretici kümesinden EN AZ bu kadar adı anıyorsa
#: değerlendiricileri BİR ARADA koşturuyor demektir. Eşik 1 olsaydı tek bir değerlendiriciyi
#: çağıran her sarmalayıcı (ve her test yardımcısı) tarayıcı sayılırdı; 2, "bir arada koşturma"nın
#: en küçük gözlemlenebilir biçimidir.
_TARAYICI_ESIGI = 2

# ELLE YAZILMIŞ KARAR ADI LİSTESİ KALDIRILDI (2026-08-31) ve bu bir ÖLÇÜMÜN sonucudur.
# Liste `{"verdict", "score", "score_num", "size_r"}` idi; kaynak taraması kapı vokabülerine
# (`"GO"`/`"NO_GO"`/`"REVIEW"`) atanan TEK ad olarak `verdict`i buldu (5 yer: `loop.py` ×4,
# `shadow_variants.py` ×1). Diğer üçü hiçbir karar dalında kanıt üretmiyordu — yani ölü kayıttı ve
# bu deponun yasasına göre ölü muafiyet/ölü kayıt ÇÜRÜKTÜR. Onları "ileride lazım olur" diye
# tutmak, yasanın kendi kaydını bir dilek listesine çevirirdi.

#: Sınıf türetiminin KOŞTUĞU yer. Sınıf, sembolün doğası hakkında soyut bir iddia değil, "karar
#: yüzeyinde bir karar eylemine bağlanıyor mu" sorusudur — bu yüzden yalnız karar modüllerinde
#: sorulur. `api.py`deki bir `if ...: return` bir HTTP yanıtı döndürür, bir emri değil.
def _sinif_kapsami() -> dict[str, str]:
    return {**CANLI_KARAR_YOLU, **TARIHSEL_YOL}


# MODÜL-İÇİ KAPANIM SINIRI. `codelaw._reach_in_module` `_HOP=1` kullanır ve o KENDİ sorusu için
# doğrudur; burada YETMEZ, çünkü ölçülen gerçek zincir İKİ sıçramadır:
#   evaluate_pead (çağırır earnings.days_since_report) ← scan_all ← scan_entry ← backtest.replay
# Bu yüzden kapanım modül İÇİNDE fixpoint'tir. codelaw'ın fixpoint'ten kaçınma gerekçesi
# (35 beyanın 28'i gürültüye boğuluyordu) burada geçerli DEĞİL: orada hedef "modülün herhangi bir
# artefakt okuması"ydı, burada hedef `karar_etkili` PIT-dışı sembollerin DAR kümesidir. Kapanımın
# büyüklüğü yine de raporda görünür (`kapanim_boyu`) — gürültü sessizce büyüyemesin.
_KAPANIM_TAVANI = 40


def _mods(root: str = VARSAYILAN_KOK) -> dict[str, tuple]:
    """`{dosya_adı: (ağaç, yol)}` — `codelaw`ın memolu okuyucusundan. Ayrıştırılamayan dosya
    `codelaw.UNSCANNED`e düşer ve `rapor()` onu dışarı verir: eksik tarama, sıfır-ihlal
    iddiasının şartıdır."""
    out: dict[str, tuple] = {}
    for f in codelaw._py_files(root):
        try:
            out[f.name] = (codelaw._ast_oku(f), f)
        except (SyntaxError, OSError, ValueError) as e:   # ValueError: UnicodeDecodeError dâhil
            codelaw._note_unscanned(f, e, "pitlaw")
    return out


def karar_etkili() -> dict[tuple[str, str], dict[str, str]]:
    """Kayıttaki YALNIZ `karar_etkili` semboller. Yasanın konusu bunlardır: `bilgi` sınıfı bir
    kaynağın tarihsel yolda okunması geriye-dönük önyargı ÜRETMEZ (dönüşü bir hükme girmez)."""
    return {k: v for k, v in PIT_DISI_KAYNAKLAR.items() if v["sinif"] == "karar_etkili"}


def dogrudan_cagrilar(root: str = VARSAYILAN_KOK) -> dict[tuple[str, str], list[str]]:
    """`(modül kökü, fonksiyon)` → çağrı yerleri — YALNIZ `karar_etkili` PIT-dışı semboller için.

    Çözüm gövdesi `codelaw._call_index`tir: `import x as y`, `meridian.x.y()`, `from . import x
    as y` ve `__import__(...).y()` biçimlerini çözer. Çözemediği biçim (dinamik/`getattr`)
    burada da çözülmez ve `gorulmeyen` kovasında sayılır."""
    idx = codelaw._call_index(_mods(root))
    return {k: sorted(v, key=codelaw._site_key) for k, v in idx.items() if k in karar_etkili()}


def _dokunulan_adlar(node: ast.AST) -> set[str]:
    """Bu gövdenin DOKUNDUĞU adlar: çağrılanlar (`codelaw._called_names`) ARTI değer olarak
    geçirilen fonksiyon referansları (`ast.Name`).

    REFERANS BACAĞI ÖLÇÜMLE EKLENDİ (2026-08-30) ve zincirin taşıyıcısı odur. `strategy.scan_all`
    değerlendiricileri şöyle koşturur:
        for fn in (evaluate_entry, ..., evaluate_pead, ...):
            sig = fn(bars, params, rs_rating_value, ticker)
    Burada `evaluate_pead` bir ÇAĞRI değil bir AD'dır; tek `ast.Call` düğümü `fn(...)`tir.
    Yalnız çağrılara bakan bir kapanım tam da ölçülen ihlalin geçtiği yerde kopuyordu —
    `backtest.replay → scan_entry → scan_all → evaluate_pead → days_since_report` zinciri
    görünmezdi. Ad referansı erişimdir: bir fonksiyonun adını değer olarak geçiren gövde, o
    fonksiyonun koşmasına sebep olabilir."""
    return codelaw._called_names(node) | {n.id for n in ast.walk(node)
                                          if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


def _erisenler(tree: ast.AST, hedefler: set[str]) -> tuple[set[str], int]:
    """Bu modül İÇİNDE `hedefler` kümesindeki adlardan birine ULAŞAN fonksiyon adları (fixpoint)
    ve kapanım turu sayısı. Doğrudan çağıran/dokunan fonksiyonlarla başlar, sonra onlara
    dokunanları ekler; küme büyümeyince durur.

    BAŞLANGIÇ KÜMESİ ÇAĞRIYLA KURULUR (`_called_names`), GENİŞLEME DOKUNUŞLA (`_dokunulan_adlar`):
    PIT'siz kaynağa erişim gerçek bir ÇAĞRI olmalıdır (`earn.days_since_report(...)`) — adını
    anmak yetmez, yoksa docstring'de adı geçen her fonksiyon erişimci sayılırdı."""
    defs = codelaw._func_index(tree)
    reach = {fn for fn, nodes in defs.items()
             if any(codelaw._called_names(nd) & hedefler for nd in nodes)}
    for tur in range(_KAPANIM_TAVANI):
        yeni = {fn for fn, nodes in defs.items()
                if any(_dokunulan_adlar(nd) & reach for nd in nodes)} - reach
        if not yeni:
            return reach, tur
        reach |= yeni
    return reach, _KAPANIM_TAVANI


def dolayli_zincirler(root: str = VARSAYILAN_KOK) -> list[dict]:
    """Tarihsel yol modülünün, PIT-dışı bir `karar_etkili` sembole ULAŞAN bir başka modül
    fonksiyonunu çağırdığı yerler.

    Bu, `in_blackout` sınıfı doğrudan çağrılar kesildikten SONRA geriye kalan yoldur ve ölçülmüş
    gerçek ihlal buradan çıktı (`BILINEN_IHLALLER`). Doğrudan çağrıyla aynı zarar, farklı biçim:
    tarihsel bir seansa bugünün anlık görüntüsü uygulanır."""
    mods = _mods(root)
    idx = codelaw._call_index(mods)
    hedef = karar_etkili()
    out: list[dict] = []
    for m, (tree, _p) in sorted(mods.items()):
        if m in TARIHSEL_YOL or m not in CANLI_KARAR_YOLU:
            # Kapanım YALNIZ ara modüllerde kurulur: tarihsel modülün KENDİ içindeki erişim
            # zaten `dogrudan_cagrilar`ın konusudur ve iki kez sayılmamalıdır.
            continue
        stem = m[:-3]
        # HEDEF AD KÜMESİ NİTELENMEMİŞTİR (`days_since_report`), çünkü `_called_names` de
        # nitelenmemiş ad döndürür (`earn.days_since_report` → `days_since_report`). BEDELİ
        # BEYANLI: ara modülde AYNI ADLA yerel bir fonksiyon tanımlıysa zincir yanlış pozitif
        # verir. Kayıt dar (bugün 3 ad) ve çakışma `test_kayittaki_ad_ara_modulde_YEREL_DEGIL`
        # ile çivilidir — sessiz kalmaz.
        reach, turlar = _erisenler(tree, {fn for (_mk, fn) in hedef})
        for fn in sorted(reach):
            for yer in sorted(idx.get((stem, fn), []), key=codelaw._site_key):
                cagiran = yer.split(":")[0]
                if cagiran not in TARIHSEL_YOL:
                    continue
                # Hangi PIT-dışı sembole ulaşıyor: ara modülün doğrudan çağırdıkları
                uclar = sorted({f"{mk}.{f}" for (mk, f) in hedef
                                if (mk, f) in idx and any(s.startswith(f"{m}:")
                                                          for s in idx[(mk, f)])})
                out.append({"tarihsel_modul": cagiran, "yer": yer,
                            "ara_modul": m, "ara_fonksiyon": fn,
                            "uclar": uclar, "kapanim_turu": turlar})
    return out


def _gerekce(deger: Any) -> str:
    """Bir defter kaydının gerekçe metni. İKİ BİÇİM BİLİNÇLİ OLARAK KABUL EDİLİR:
    `PIT_KORUMALI_ZINCIRLER` alanlı (`{"gerekce", "civi"}`), `BILINEN_IHLALLER` düz metin — ve
    sentetik testler `rapor(bilinen=..., korumali=...)` ile düz metin enjekte eder. Enjeksiyonun
    değeri hükme GİRMEZ (kova seçimi yalnız ANAHTARla yapılır), yalnız rapora basılır; biçimi
    zorlamak testleri kaydın iç yapısına bağlardı."""
    return deger.get("gerekce", "") if isinstance(deger, dict) else str(deger)


def koruma_civisi_denetimi(root: str = VARSAYILAN_KOK,
                           korumali: dict | None = None) -> list[dict]:
    """KORUMALI-ZİNCİR KAYDININ KENDİ DENETİMİ — `kapi_sozlesme_denetimi`nin kardeşi, aynı
    disiplin: kayıt bir İDDİA değildir, kaynaktan çürütülebilir olmalıdır.

    Her kayıt korumasını çürütebilen çiviyi `civi` alanında `dosya::test_fn` biçiminde taşır.
    Burada sorulan tek soru şudur: **o sembol kaynakta gerçekten var mı?** Çürüme nedenleri
    ADIYLA döner — `civi_beyani_yok` (alan boş: kayıt korumasını kimseye bağlamamış),
    `dosya_yok`, `sembol_yok` (çivi silinmiş ya da adı değişmiş).

    NEDEN ÇİVİNİN VARLIĞI YETER (kapsam beyanı): bu denetim gövdenin ısırdığını ölçemez — onu
    ölçen şey mutasyondur ve o insan disiplinidir (§6). Ölçtüğü şey daha dar ama tam olarak
    eksik olandı: "hiç çivi yok" hâli artık imkânsızdır. Boş küme "koruma doğrulandı" demez,
    "her kaydın bir çivisi VAR" der.

    YOL ÇÖZÜMÜ kökün EBEVEYNİNDEN yapılır (`meridian` → depo kökü) — `codelaw._py_files`in
    zaten dayandığı varsayımın aynısı; ikinci bir kök kavramı üretmemek için."""
    kayit = PIT_KORUMALI_ZINCIRLER if korumali is None else korumali
    depo = pathlib.Path(root).parent
    curuk: list[dict] = []
    for (m, mk, fn), deger in sorted(kayit.items()):
        ad = f"{m}→{mk}.{fn}"
        civi = deger.get("civi") if isinstance(deger, dict) else None
        if not civi or "::" not in civi:
            curuk.append({"kayit": ad, "civi": civi, "neden": "civi_beyani_yok"})
            continue
        dosya, _, test_fn = civi.partition("::")
        yol = depo / dosya
        if not yol.exists():
            curuk.append({"kayit": ad, "civi": civi, "neden": "dosya_yok"})
            continue
        try:
            tree = codelaw._ast_oku(yol)
        except (SyntaxError, OSError, ValueError) as e:   # ValueError: UnicodeDecodeError dâhil
            codelaw._note_unscanned(yol, e, "pitlaw")
            continue                    # taranamayan dosya `unscanned` üzerinden `ok`u zaten düşürür
        if test_fn not in {n.name for n in ast.walk(tree)
                           if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}:
            curuk.append({"kayit": ad, "civi": civi, "neden": "sembol_yok"})
    return curuk


def _kayitta(kayit: dict, defter: dict) -> tuple[str, str, str] | None:
    """Bir dolaylı zincir kaydının `defter`deki anahtarı (yoksa None)."""
    for uc in kayit["uclar"]:
        mk, _, fn = uc.partition(".")
        anahtar = (kayit["tarihsel_modul"], mk, fn)
        if anahtar in defter:
            return anahtar
    return None


def _cagri_dugumleri(tree: ast.AST, satir: int, fn: str) -> list[ast.Call]:
    """`codelaw._call_index`in verdiği `dosya.py:SATIR` yerinden GERÇEK çağrı düğümüne iner.

    Alias çözümü (`from . import earnings as earn`, `__import__(...)`) KOPYALANMAZ: o mantığın tek
    otoritesi `_call_index`tir ve ikinci bir kopya aynı yasanın iki sürümünü doğururdu. Buradaki
    iş yalnız "o satırdaki, adı `fn` olan çağrıyı bul". Aynı satırda birden çok çağrı olabilir
    (`f(g(x))`), o yüzden ad da eşleştirilir ve liste dönülür."""
    return [n for n in ast.walk(tree)
            if isinstance(n, ast.Call) and getattr(n, "lineno", None) == satir
            and ((isinstance(n.func, ast.Attribute) and n.func.attr == fn)
                 or (isinstance(n.func, ast.Name) and n.func.id == fn))]


def _kapsayan_fonksiyon(tree: ast.AST, dugum: ast.AST) -> ast.AST:
    """Düğümü içeren EN İÇTEKİ fonksiyon tanımı (yoksa modülün kendisi). Etki izlemesi fonksiyon
    sınırında tutulur: aynı ad başka bir fonksiyonda başka bir şeydir."""
    en_ic = None
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and n.lineno <= dugum.lineno <= (getattr(n, "end_lineno", None) or n.lineno) \
                and (en_ic is None or n.lineno > en_ic.lineno):
            en_ic = n
    return en_ic if en_ic is not None else tree


def karar_vokabuleri(root: str = VARSAYILAN_KOK) -> frozenset[str] | None:
    """`guard.classify_gate`in DÖNDÜRDÜĞÜ karar sabitleri — kaynaktan okunur, elle yazılmaz.

    Sözleşme fonksiyonun kendi gövdesindedir: her `return`ün İLK pozisyonundaki string sabit bir
    karar hükmüdür (`return "NO_GO", hard` → `"NO_GO"`); ikinci pozisyon gerekçedir ve karar
    taşımaz. Bugün ölçülen küme: `{"GO", "NO_GO", "REVIEW"}`.

    Kayıttaki TÜM sözleşmelerin BİRLEŞİMİ alınır — ikinci bir kapı yüzeyi kendi vokabülerini
    getirebilir. Hiçbiri okunamazsa `None`; biri okunup öteki okunamazsa okunanın kümesi döner
    ve eksik olan `kapi_sozlesme_denetimi()["curuk"]`ta ADIYLA görünür.

    ÖLÇÜLEMEZSE `None` — boş küme DEĞİL (uydurma yasağı). Boş küme "kapı hiç karar döndürmüyor"
    der; `guard.py` okunamadıysa ya da `classify_gate` adı değiştiyse doğru cevap "sözleşmeyi
    bulamadım"dır ve o durumda sınıf hükmü HİÇ verilmez."""
    mods = _mods(root)
    out: set[str] = set()
    for dosya, fn_adi in KAPI_SOZLESMELERI:
        out |= _bir_sozlesmenin_sabitleri(mods, dosya, fn_adi)
    return frozenset(out) or None


def _donen_sabitler(fn_node: ast.AST) -> set[str]:
    """Bir fonksiyonun döndürdüğü string sabitler — her `return`ün İLK pozisyonundan.

    `return "NO_GO", hard` → `{"NO_GO"}`. İkinci pozisyon GEREKÇEDİR ve alınmaz; onu da toplamak
    gerekçe listesine atanan her adı karar adı yapardı."""
    return {ilk.value for r in ast.walk(fn_node)
            if isinstance(r, ast.Return) and r.value is not None
            for ilk in [(r.value.elts[0] if isinstance(r.value, ast.Tuple) and r.value.elts
                         else r.value)]
            if isinstance(ilk, ast.Constant) and isinstance(ilk.value, str)}


def _bir_sozlesmenin_sabitleri(mods: dict, dosya: str, fn_adi: str) -> set[str]:
    """Tek bir kapı fonksiyonunun döndürdüğü string sabitler (bulunamazsa boş küme)."""
    if dosya not in mods:
        return set()
    tree, _p = mods[dosya]
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == fn_adi:
            return _donen_sabitler(n)
    return set()


def kapi_sozlesme_denetimi(root: str = VARSAYILAN_KOK) -> dict[str, list]:
    """KAYDIN KENDİSİNİN DENETİMİ — iki yönlü, `arming.PIT_CAPALI_KURULUMLAR` (çivi v301) deseni.

      `curuk`    — kayıtta duran ama kodda bulunamayan sözleşme (modül yok, ya da fonksiyon adı
                   değişti). Ölü kayıt çürüktür; yasa var olmayan bir sözleşmeye dayanamaz.
      `kayitsiz` — KAYITTA OLMAYAN ama karar sabiti DÖNDÜREN fonksiyon. İkinci bir kapı yüzeyi
                   doğduğu gün buradan görünür; kayıt elle genişletilene kadar onun hükümleri
                   sınıf türetimine girmez, yani yasa o yüzeyde sessizce kör kalırdı.

    KAPSAM BEYANI: `kayitsiz` taraması BİLİNEN vokabülerle yapılır. Tamamen yeni sabitlerle
    (`"BLOCK"` gibi) konuşan bir kapı yüzeyi bu tarayıcıya GÖRÜNMEZ — o gün kayıt elle açılmalıdır.
    Sıfır sonuç "başka kapı yok" değil, "bilinen vokabülerle konuşan başka kapı bulunamadı"dır."""
    mods = _mods(root)
    vok = karar_vokabuleri(root)
    curuk = [f"{d}::{f}" for d, f in KAPI_SOZLESMELERI
             if not _bir_sozlesmenin_sabitleri(mods, d, f)]
    kayitli = set(KAPI_SOZLESMELERI)
    kayitsiz: list[dict] = []
    if vok:
        for m, (tree, _p) in sorted(mods.items()):
            for n in ast.walk(tree):
                if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                        or (m, n.name) in kayitli:
                    continue
                if ortak := (_donen_sabitler(n) & vok):
                    kayitsiz.append({"yer": f"{m}::{n.name}", "satir": n.lineno,
                                     "sabitler": sorted(ortak)})
    return {"curuk": sorted(curuk), "kayitsiz": kayitsiz}


def sinyal_ureticileri(root: str = VARSAYILAN_KOK) -> frozenset[str] | None:
    """`strategy.scan_all`ın koşturduğu değerlendiriciler — "sinyal üreten fonksiyon"un tanımı.

    Gövdedeki fonksiyon ADI referansları alınır (`for fn in (evaluate_entry, …, evaluate_pead, …)`)
    ve aynı modülde TANIMLI fonksiyonlarla kesiştirilir; `by_setup`/`sig` gibi yerel adlar böyle
    elenir. Kayıt kodun kendisidir: bir değerlendirici bu demete girmeden sinyal üretemez.

    Kayıttaki TÜM tarayıcıların BİRLEŞİMİ alınır — ikinci bir tarayıcı kendi değerlendiricilerini
    getirebilir.

    ÖLÇÜLEMEZSE `None` — boş küme DEĞİL. `strategy.py` okunamadıysa ya da `scan_all` adı
    değiştiyse doğru cevap "üreticileri bulamadım"dır; boş küme "hiçbir fonksiyon sinyal
    üretmiyor" derdi ve her erken `return`ü sessizce kararsız ilan ederdi."""
    mods = _mods(root)
    out: set[str] = set()
    for dosya, fn_adi in SINYAL_SOZLESMELERI:
        out |= _bir_tarayicinin_ureticileri(mods, dosya, fn_adi)
    return frozenset(out) or None


def _anilan_adlar(fn_node: ast.AST) -> set[str]:
    """Bu fonksiyonun gövdesinde DEĞER olarak anılan adlar (`ast.Name`, Load).

    Docstring ve yorumlar BURAYA GİRMEZ ve bu ayrım ölçümle önemlidir: depoda `evaluate_pead`
    gibi adlar onlarca yorum satırında geçiyor (`watchdog`, `indicators`, `component_ic`,
    `reflect`, `ledgers`, `arming`…). Metin taraması onların hepsini "tarayıcı" sanırdı; AST
    yalnız gerçek kod referansını görür."""
    return {m.id for m in ast.walk(fn_node)
            if isinstance(m, ast.Name) and isinstance(m.ctx, ast.Load)}


def _bir_tarayicinin_ureticileri(mods: dict, dosya: str, fn_adi: str) -> set[str]:
    """Tek bir tarayıcının koşturduğu, AYNI modülde tanımlı değerlendiriciler (bulunamazsa boş)."""
    if dosya not in mods:
        return set()
    tree, _p = mods[dosya]
    tanimli = set(codelaw._func_index(tree))
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == fn_adi:
            return _anilan_adlar(n) & tanimli
    return set()


def sinyal_sozlesme_denetimi(root: str = VARSAYILAN_KOK) -> dict[str, list]:
    """SİNYAL KAYDININ İKİ YÖNLÜ DENETİMİ — `kapi_sozlesme_denetimi`nin birebir kardeşi.
    Asimetri bırakmak, iki sözleşmeden birini korumasız bırakmak olurdu.

      `curuk`    — kayıtta duran ama kodda bulunamayan tarayıcı (modül yok ya da ad değişti).
      `kayitsiz` — kayıtta OLMAYAN ama üretici kümesinden `_TARAYICI_ESIGI` kadar adı anan
                   fonksiyon: İKİNCİ BİR TARAYICI. Bulunmazsa onun koşturduğu değerlendiricilerin
                   erken `return`leri karar sayılmaz ve PIT'siz bir kaynak sessizce `bilgi`
                   sınıfına düşer — yasanın o yüzeydeki kör noktası budur.

    KAPSAM BEYANI: tarama BİLİNEN üreticilerle yapılır. Tamamen farklı değerlendiricileri
    koşturan bir tarayıcı GÖRÜNMEZ (kapı tarafındaki "yeni vokabüler" sınırının kardeşi).
    Sıfır sonuç "başka tarayıcı yok" değil, "bilinen değerlendiricileri koşturan başka tarayıcı
    bulunamadı"dır."""
    mods = _mods(root)
    ureticiler = sinyal_ureticileri(root)
    curuk = [f"{d}::{f}" for d, f in SINYAL_SOZLESMELERI
             if not _bir_tarayicinin_ureticileri(mods, d, f)]
    kayitli = set(SINYAL_SOZLESMELERI)
    kayitsiz: list[dict] = []
    if ureticiler:
        for m, (tree, _p) in sorted(mods.items()):
            for n in ast.walk(tree):
                if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                        or (m, n.name) in kayitli:
                    continue
                if len(ortak := (_anilan_adlar(n) & ureticiler)) >= _TARAYICI_ESIGI:
                    kayitsiz.append({"yer": f"{m}::{n.name}", "satir": n.lineno,
                                     "ureticiler": sorted(ortak)})
    return {"curuk": sorted(curuk), "kayitsiz": kayitsiz}


def _sabit_atamalari(n: ast.AST) -> list[tuple[str, str]]:
    """Bir atamadaki `(ad, string sabit)` çiftleri. Tuple açımı POZİSYONEL eşleştirilir:
    `verdict, reasons = "NO_GO", list(...)` → yalnız `("verdict", "NO_GO")`; `reasons` bir çağrı
    alır, sabit almaz ve karar adı sayılmaz."""
    hedef = (n.targets[0] if isinstance(n, ast.Assign) and n.targets
             else getattr(n, "target", None))
    deger = getattr(n, "value", None)
    if hedef is None or deger is None:
        return []
    ciftler = (list(zip(hedef.elts, deger.elts))
               if isinstance(hedef, ast.Tuple) and isinstance(deger, ast.Tuple)
               else [(hedef, deger)])
    return [(h.id, d.value) for h, d in ciftler
            if isinstance(h, ast.Name) and isinstance(d, ast.Constant)
            and isinstance(d.value, str)]


def karar_adlari(root: str = VARSAYILAN_KOK) -> dict[str, Any]:
    """Karar modüllerinde kapı vokabülerinden bir sabite atanan adlar — yani "kapı hükmünün
    aktığı değişkenler". `KARAR_ADLARI` sabitinin yerini alır.

    Dönüş: `{"vokabuler": frozenset|None, "adlar": frozenset|None, "kanit": [...]}`.
    Vokabüler ölçülemezse ikisi de `None`: sözleşme okunamadan karar adı türetilemez."""
    vok = karar_vokabuleri(root)
    if vok is None:
        return {"vokabuler": None, "adlar": None, "kanit": []}
    mods = _mods(root)
    adlar: set[str] = set()
    kanit: list[dict] = []
    for m in sorted(_sinif_kapsami()):
        if m not in mods:
            continue
        tree, _p = mods[m]
        for n in ast.walk(tree):
            if not isinstance(n, (ast.Assign, ast.AnnAssign)):
                continue
            for ad, sabit in _sabit_atamalari(n):
                if sabit in vok:
                    adlar.add(ad)
                    kanit.append({"ad": ad, "sabit": sabit, "yer": f"{m}:{n.lineno}"})
    # BOŞ KÜME `None` DEĞİLDİR — iki ayrı durum, iki ayrı cevap (ölçülmüş tuzak):
    #   `adlar is None`      → SÖZLEŞME OKUNAMADI; sınıf hükmü hiç verilemez.
    #   `adlar == frozenset()` → sözleşme okundu, ama bu ağaçta kapı hükmü hiçbir ada AKMIYOR.
    #     Bu meşru bir ağaçtır (ör. yalnız erken-`return` ile karar veren bir alt küme) ve
    #     `_karar_eylemi`nin `return` bacağı orada çalışmaya devam etmelidir.
    # `frozenset(...) or None` yazmak ikisini tek değere toplardı ve sözleşmesi SAĞLAM bir ağaçta
    # "sözleşme okunamadı" hükmü ürettirirdi.
    return {"vokabuler": vok, "adlar": frozenset(adlar),
            "kanit": sorted(kanit, key=lambda k: codelaw._site_key(k["yer"]))}


def _atanan_adlar(n: ast.AST) -> set[str]:
    """Bir atama ifadesinin hedef adları (tuple hedefler dâhil: `verdict, reasons = ...`)."""
    hedefler = (n.targets if isinstance(n, ast.Assign)
                else [n.target] if isinstance(n, (ast.AugAssign, ast.AnnAssign)) else [])
    return {m.id for h in hedefler for m in ast.walk(h)
            if isinstance(m, ast.Name) and isinstance(m.ctx, ast.Store)}


def _tohumlar(kapsam: ast.AST, cagri: ast.Call) -> set[str]:
    """Çağrının sonucunun atandığı ad(lar) — `_bl = earnings.in_blackout(...)` → `{"_bl"}`.
    Kimlik (`is`) ile eşleşir: aynı satırdaki başka bir çağrının sonucu tohum sayılmaz."""
    out: set[str] = set()
    for n in ast.walk(kapsam):
        if isinstance(n, (ast.Assign, ast.AnnAssign)) and getattr(n, "value", None) is cagri:
            out |= _atanan_adlar(n)
    return out


def _testte_gecer(test: ast.AST, cagri: ast.Call, tohumlar: set[str]) -> bool:
    """Bu `if`/`while` testi, çağrının sonucuna bakıyor mu? İki biçim: çağrının KENDİSİ testin
    içinde (`if not earn.days_since_report(...)`) ya da sonucunun atandığı ad (`if ... and _bl`)."""
    for n in ast.walk(test):
        if n is cagri:
            return True
        if isinstance(n, ast.Name) and n.id in tohumlar:
            return True
    return False


def _karar_eylemi(dal: list, adlar: frozenset[str], uretici: bool) -> tuple[str, int] | None:
    """Bu dalın İÇİNDE (özyineli, iç içe `if`ler dâhil) bir karar eylemi var mı?

    İKİ BİÇİM, İKİ AYRI KAYNAK — ve ayrımı silmemek önemli:
      · `adlar`a atama — KAPI HÜKMÜ. Ad kümesi `guard.classify_gate` sözleşmesinden TÜRETİLİR
        (`karar_adlari`), bu modülde elle yazılmaz.
      · erken `return`  — SİNYAL ÜRETMEME kararı. Bu guard'dan GELMEZ ve gelemez: `evaluate_pead`
        kapıya hiç ulaşmadan, çapası çözülmediği için `None` döner. Kurulum o gün ateşleyemez;
        bu da bir karardır, ama kapı hükmü değildir. Ayrı gerekçe, ayrı kaynak, bilinçli olarak
        ayrı tutuldu. DARALTILDI (2026-08-31): yalnız `uretici` — yani kapsayan fonksiyon
        `sinyal_ureticileri` kaydındaysa. Önceki hâl HER erken `return`ü karar sayıyordu ve
        `if not veri: return` gibi bir bakım/koruma dönüşü ile "kurulum ateşleyemez" hükmünü
        ayırt edemiyordu.

    ÖZYİNELİ olması ölçümden geldi: `calendar_untrustworthy`nin karar eylemi İKİ sıçrama ötede
    (`if _takvim_kusuru:` → `_tk_dusus = verdict == "GO"` → `if _tk_dusus:` → `verdict = "REVIEW"`).
    Yalnız dalın ilk seviyesine bakan bir tarayıcı onu `bilgi` sanırdı."""
    for st in dal:
        for m in ast.walk(st):
            if isinstance(m, ast.Return) and uretici:
                return ("return", m.lineno)
            if isinstance(m, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
                if ortak := (_atanan_adlar(m) & adlar):
                    return (sorted(ortak)[0], m.lineno)
    return None


def sinif_turet(root: str = VARSAYILAN_KOK,
                kaynaklar: dict | None = None) -> dict[tuple[str, str], dict[str, Any]]:
    """Her PIT-dışı sembolün sınıfını KAYNAKTAN ölçer.

    Dönüş: `(modül kökü, fonksiyon)` → `{"turetilen": "karar_etkili"|"bilgi"|None,
    "kanit": [...], "yerler": [...]}`.

    `turetilen is None` = ÖLÇÜLEMEDİ, "bilgi" DEĞİL (uydurma yasağı): sembolün hiçbir karar
    modülünde çağrısı yok, dolayısıyla sınıfı hakkında hüküm KURULAMAZ. Boş liste "baktım, karar
    değil" der; doğru cevap "bu kapsamda çağrısı yok"tur.

    `kaynaklar` verilirse canlı kayıt yerine O taranır (ENJEKSİYON = YALITIM)."""
    mods = _mods(root)
    kapsam_mod = _sinif_kapsami()
    idx = codelaw._call_index(mods)
    kayit = PIT_DISI_KAYNAKLAR if kaynaklar is None else kaynaklar
    # KARAR ADLARI TÜRETİLİR. Sözleşme okunamazsa hiçbir sembol için hüküm KURULMAZ: `adlar`
    # boş sayılıp yalnız `return` bacağıyla devam etmek, kapı hükmüne bağlı her sembolü sessizce
    # `bilgi` ilan ederdi — yasayı kapatan tam da o satır olurdu.
    _adlar = karar_adlari(root)["adlar"]
    _ureticiler = sinyal_ureticileri(root)
    out: dict[tuple[str, str], dict[str, Any]] = {}
    # HER İKİ SÖZLEŞME DE GEREKLİ. Karar eyleminin iki biçimi iki ayrı kayıttan gelir; biri
    # okunamazsa türetim EKSİKTİR ve eksik türetimle sınıf hükmü vermek, ölçemediğini "bilgi"
    # saymakla aynı kapıya çıkar. Hangi sembolün hangi bacağa bağlı olduğu önceden bilinemez.
    if _adlar is None or _ureticiler is None:
        eksik = ("kapi_sozlesmesi_okunamadi" if _adlar is None
                 else "sinyal_sozlesmesi_okunamadi")
        return {k: {"turetilen": None, "kanit": [], "yerler": [], "neden": eksik} for k in kayit}
    for (mk, fn) in kayit:
        yerler = [y for y in idx.get((mk, fn), []) if y.split(":")[0] in kapsam_mod]
        kanit: list[dict] = []
        for yer in sorted(yerler, key=codelaw._site_key):
            dosya, _, satir_s = yer.rpartition(":")
            if dosya not in mods:
                continue
            tree, _p = mods[dosya]
            for cagri in _cagri_dugumleri(tree, int(satir_s), fn):
                kapsam = _kapsayan_fonksiyon(tree, cagri)
                tohum = _tohumlar(kapsam, cagri)
                for n in ast.walk(kapsam):
                    if not isinstance(n, (ast.If, ast.While)) \
                            or not _testte_gecer(n.test, cagri, tohum):
                        continue
                    _uretici = getattr(kapsam, "name", None) in _ureticiler
                    for dal in (n.body, n.orelse):
                        if eylem := _karar_eylemi(dal, _adlar, _uretici):
                            kanit.append({"yer": yer, "test_satiri": n.lineno,
                                          "eylem": eylem[0], "eylem_satiri": eylem[1]})
                            break
        out[(mk, fn)] = {
            "turetilen": ("karar_etkili" if kanit else "bilgi") if yerler else None,
            "kanit": kanit, "yerler": sorted(yerler, key=codelaw._site_key)}
    return out


def sinif_celiskileri(root: str = VARSAYILAN_KOK, kaynaklar: dict | None = None) -> list[dict]:
    """Beyan edilen sınıf ile kaynaktan türetilen sınıfın AYRIŞTIĞI kayıtlar — İKİ YÖNLÜ.

      `beyan_bilgi_gercek_karar` — EN TEHLİKELİ YÖN. Kayıt "bilgi" diyor ama dönüş bir karar
        eylemine bağlanmış: yasa o kaynağı `karar_etkili()` süzgecinde dışarıda bırakır, yani
        PIT'siz veri sessizce karara girer ve çivi bunu HİÇ göremez.
      `beyan_karar_gercek_bilgi` — kayıt fazla katı: ölçülebilir bir karar bağı yokken sembolü
        yasağın konusu sayıyor. Gereksiz kısıt da bir hatadır (arming v301'in ikinci yönü);
        kaydın gerçeği yansıtması iki yönde de şarttır."""
    kayit = PIT_DISI_KAYNAKLAR if kaynaklar is None else kaynaklar
    out: list[dict] = []
    for (mk, fn), t in sorted(sinif_turet(root, kaynaklar).items()):
        beyan = kayit[(mk, fn)]["sinif"]
        tur = t["turetilen"]
        if tur is None or tur == beyan:
            continue
        out.append({"sembol": f"{mk}.{fn}", "beyan": beyan, "turetilen": tur,
                    "neden": ("beyan_bilgi_gercek_karar" if beyan == "bilgi"
                              else "beyan_karar_gercek_bilgi"),
                    "kanit": t["kanit"], "yerler": t["yerler"]})
    return out


def gorulmeyen(root: str = VARSAYILAN_KOK) -> list[dict]:
    """TARAYICININ KENDİ KÖRLÜĞÜ — adlandırılmış kova. Sıfır ihlal iddiası, kaçının ölçülemediği
    bilinmeden okunamaz.

    İki sınıf sayılır:
      `dinamik_erisim` — tarihsel/karar modülünde `getattr(<modül>, "<ad>")` biçimi: hedef ad
                         çalışma zamanında kurulur, statik çağrı indeksi göremez.
      `kayitta_yok`    — `adapters/` altında kaynak kaydında HİÇ geçmeyen modül: PIT durumu
                         hakkında hüküm KURULMADI (yeni bir adaptör sessizce muaf kalmasın).
    İkisi de `ok`u ETKİLEMEZ: ölçülemeyen şey ihlal değildir (UYDURMA YASAĞI)."""
    mods = _mods(root)
    kayitli = {mk for (mk, _fn) in PIT_DISI_KAYNAKLAR} | {mk for (mk, _fn) in PIT_KAYNAKLAR} \
        | {mk for (mk, _fn) in PIT_SOZLESMELI_BESLEYENI_KAPALI}
    out: list[dict] = []
    for m, (tree, yol) in sorted(mods.items()):
        if m in TARIHSEL_YOL or m in CANLI_KARAR_YOLU:
            for n in ast.walk(tree):
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                        and n.func.id == "getattr" and len(n.args) >= 2:
                    hedef = n.args[1]
                    ad = hedef.value if isinstance(hedef, ast.Constant) else None
                    out.append({"neden": "dinamik_erisim", "file": m, "line": n.lineno,
                                "ad": ad if isinstance(ad, str) else "<sabit-değil>"})
        if "adapters" in yol.parts and m.endswith(".py") and m != "__init__.py" \
                and m[:-3] not in kayitli:
            out.append({"neden": "kayitta_yok", "file": m, "line": 0, "ad": m[:-3]})
    return out


def rapor(root: str = VARSAYILAN_KOK, bilinen: dict | None = None,
          korumali: dict | None = None, kaynaklar: dict | None = None) -> dict[str, Any]:
    """İki dünyanın birlikte hükmü — tek bakışta 'yasa tutuyor mu' cevabı.

    `ok` ÜÇ ŞARTIN birleşimidir ve her biri ayrı bir hükümdür:
      · tarihsel yolda BEYANSIZ ihlal YOK (sıfır tolerans),
      · canlı borç tabanı AŞILMADI (çırçır),
      · beyan edilmiş kayıtların hepsi HÂLÂ GERÇEK (ölü muafiyet çürüktür),
      · KAYDIN SINIF ATAMASI kaynakla UYUŞUYOR (`sinif_celiskileri` boş),
      · her KORUMALI ZİNCİR kaydı, korumasını çürütebilen bir çiviyi ADIYLA taşıyor ve o çivi
        kaynakta var (`korumali_civi_curuk` boş) — çivisiz koruma beyanı ölçülemez beyandır.
    Taranamayan dosya (`unscanned`) da `ok`u düşürür: eksik tarama sıfır-ihlal iddiasının şartıdır.

    ENJEKSİYON = YALITIM (codelaw.declared_claims emsali, ve BU TURDA ÖLÇÜLDÜ). Canlı defterler
    yalnız ÜRETİM ağacında (`root == VARSAYILAN_KOK`) ya da açıkça enjekte edildiğinde koşar.
    İlk koşumda bu yalıtım YOKTU ve canlı `BILINEN_IHLALLER` kaydı sentetik testleri kirletti:
    tmp ağacında kurulan `backtest.py → earnings.days_since_report` zinciri "beyanlı" sayıldı,
    pozitif kontrol sessizce YEŞİLE döndü — dedektörün kendi testini kirletmesi."""
    _canli = root == VARSAYILAN_KOK and bilinen is None and korumali is None
    bil = BILINEN_IHLALLER if _canli else (bilinen or {})
    kor_kayit = PIT_KORUMALI_ZINCIRLER if _canli else (korumali or {})
    dogrudan = dogrudan_cagrilar(root)
    dolayli = dolayli_zincirler(root)
    kor = gorulmeyen(root)
    # SINIF HÜKMÜ SENTETİK KÖKTE VERİLMEZ — ve boş liste DEĞİL `None` döner (uydurma yasağı,
    # `codelaw.report`un tsx kalıbı). Sınıf beyanı CANLI AĞAÇ hakkındadır: kayıt, sembolün
    # üretimdeki TÜM çağrı yerlerine bakılarak yazılmıştır. Bir tmp ağacında o yerlerin ancak
    # biri bulunur ve "beyan karar diyor ama burada karar bağı yok" hükmü kurulursa, bu bir
    # ÇELİŞKİ değil bir KATEGORİ HATASIdır. Boş liste "baktım, uyumlu" derdi; doğru cevap
    # "bu ağaçta sorulamaz"dır. (Bu tuzak ölçüldü: v337'nin iki çivisi bu yüzden kırmızı verdi.)
    _sinif_sorulabilir = root == VARSAYILAN_KOK or kaynaklar is not None
    turetim = sinif_turet(root, kaynaklar) if _sinif_sorulabilir else None
    celiskiler = sinif_celiskileri(root, kaynaklar) if _sinif_sorulabilir else None

    tarihsel_dogrudan = [{"sembol": f"{mk}.{fn}", "yer": y}
                         for (mk, fn), yerler in sorted(dogrudan.items())
                         for y in yerler if y.split(":")[0] in TARIHSEL_YOL]
    canli = [{"sembol": f"{mk}.{fn}", "yer": y}
             for (mk, fn), yerler in sorted(dogrudan.items())
             for y in yerler if y.split(":")[0] in CANLI_KARAR_YOLU]

    beyanli, korumali_bulunan, beyansiz = [], [], []
    for k in dolayli:
        if _kayitta(k, kor_kayit):
            korumali_bulunan.append(k)
        elif _kayitta(k, bil):
            beyanli.append(k)
        else:
            beyansiz.append(k)
    # ÖLÜ BEYAN: kayıtta duran ama kodda karşılığı kalmayan beyan. `codelaw.py::stale_claims` ile aynı
    # disiplin — beyan, işi bitince kalmaz. İki defter de denetlenir: düzeltilen bir borç kaydı da,
    # kaldırılan bir koruma kaydı da çürüktür.
    gorulen = {_kayitta(k, bil) for k in beyanli} | {_kayitta(k, kor_kayit)
                                                    for k in korumali_bulunan}
    curuk_beyan = sorted([k for k in bil if k not in gorulen]
                         + [k for k in kor_kayit if k not in gorulen])

    return {
        # TARİHSEL DÜNYA — SIFIR TOLERANS
        "tarihsel_dogrudan": tarihsel_dogrudan,
        "tarihsel_dolayli_beyansiz": beyansiz,
        "tarihsel_dolayli_beyanli": beyanli,
        "tarihsel_dolayli_korumali": korumali_bulunan,
        "bilinen_ihlaller": {f"{m}→{mk}.{fn}": _gerekce(g) for (m, mk, fn), g in sorted(bil.items())},
        "korumali_zincirler": {f"{m}→{mk}.{fn}": _gerekce(g)
                               for (m, mk, fn), g in sorted(kor_kayit.items())},
        # KORUMA ÇİVİLERİ — kayıt hangi çiviye dayanıyor, ve o çivi kaynakta duruyor mu.
        # Denetim YALNIZ canlı kayıtta koşar (`_canli`): sentetik bir defterden gerçek bir çivi
        # adı beklemek, sınıf hükmündeki kategori hatasının aynısı olurdu (§ `_sinif_sorulabilir`).
        # `_ksd`/`_ssd`nin `root == VARSAYILAN_KOK` kapısından FARKI bilinçli: onlar KODU denetler
        # (kod her ağaçta vardır), bu ise KAYDIN kendisini — enjekte edilmiş kayıt denetlenemez.
        "korumali_civiler": {f"{m}→{mk}.{fn}": (g.get("civi") if isinstance(g, dict) else None)
                             for (m, mk, fn), g in sorted(kor_kayit.items())},
        "korumali_civi_curuk": (_kcd := koruma_civisi_denetimi(root) if _canli else []),
        "curuk_beyan": [f"{m}→{mk}.{fn}" for (m, mk, fn) in curuk_beyan],
        # CANLI DÜNYA — ÇIRÇIR
        "canli_karar_cagrilari": canli,
        "canli_taban": CANLI_TABAN,
        "canli_nuks": len(canli) > CANLI_TABAN,
        # KAPI SÖZLEŞMESİNDEN TÜRETİLEN KARAR ADLARI — elle liste YOK. `None` = sözleşme
        # okunamadı ve o durumda sınıf hükmü hiç verilmez (aşağıdaki üç alan da None olur).
        "karar_vokabuleri": None if (_ka := karar_adlari(root))["vokabuler"] is None
                            else sorted(_ka["vokabuler"]),
        "karar_adlari": None if _ka["adlar"] is None else sorted(_ka["adlar"]),
        "karar_adlari_kanit": _ka["kanit"],
        # SİNYAL ÜRETİCİLERİ — erken `return`ün karar sayıldığı DAR küme (strategy.scan_all'dan).
        "sinyal_ureticileri": None if (_su := sinyal_ureticileri(root)) is None else sorted(_su),
        # KAPI SÖZLEŞMESİ KAYDININ DENETİMİ — iki yönlü.
        "kapi_sozlesmeleri": [f"{d}::{f}" for d, f in KAPI_SOZLESMELERI],
        "kapi_sozlesmesi_curuk": (_ksd := kapi_sozlesme_denetimi(root))["curuk"],
        "kapi_sozlesmesi_kayitsiz": _ksd["kayitsiz"],
        # SİNYAL SÖZLEŞMESİ KAYDININ DENETİMİ — kapı tarafıyla simetrik, aynı iki yön.
        "sinyal_sozlesmeleri": [f"{d}::{f}" for d, f in SINYAL_SOZLESMELERI],
        "sinyal_sozlesmesi_curuk": (_ssd := sinyal_sozlesme_denetimi(root))["curuk"],
        "sinyal_sozlesmesi_kayitsiz": _ssd["kayitsiz"],
        # SINIF ATAMASININ DENETİMİ — beyan elle, çürütmesi mekanik.
        "sinif_celiskileri": celiskiler,
        # SINIFI ÖLÇÜLEMEYEN SEMBOLLER: karar modüllerinde hiç çağrısı yok, dolayısıyla beyan
        # bu kapsamda ÇÜRÜTÜLEMEDİ. "Doğrulandı" DEĞİL — `ok`u etkilemez ama ADIYLA sayılır,
        # yoksa "sıfır çelişki" cümlesi kaçının hiç sınanmadığını gizlerdi.
        "sinif_olculemedi": None if turetim is None else sorted(
            f"{mk}.{fn}" for (mk, fn), t in turetim.items() if t["turetilen"] is None),
        "sinif_dogrulandi": None if turetim is None else sorted(
            f"{mk}.{fn}" for (mk, fn), t in turetim.items() if t["turetilen"] is not None),
        # KAPSAM — "neyi göremedim". Sıfır ihlal iddiası bunlar olmadan okunamaz.
        "gorulmeyen": kor,
        "gorulmeyen_by_reason": {n: sum(1 for g in kor if g["neden"] == n)
                                 for n in sorted({g["neden"] for g in kor})},
        "unscanned": list(codelaw.UNSCANNED),
        # KAYIT BÜYÜKLÜKLERİ — kapsamın kendisi de okunabilir olmalı
        "kayit_boyu": {"pit_disi": len(PIT_DISI_KAYNAKLAR),
                       "karar_etkili": len(karar_etkili()),
                       "pit": len(PIT_KAYNAKLAR),
                       "sozlesmeli_kapali": len(PIT_SOZLESMELI_BESLEYENI_KAPALI)},
        # `sinif_celiskileri` DE `ok`u DÜŞÜRÜR ve bu, çivinin ikinci yarısıdır: yanlış sınıf,
        # yasayı sessizce kapatan tek satırdır (`karar_etkili()` süzgeci o sembolü dışarıda
        # bırakır). Yasanın kendi kaydı yanlışsa geri kalan her hüküm vakumdur.
        # `celiskiler` ÖLÇÜLMEDİYSE (None) bu bileşen hükme GİRMEZ — `codelaw.report`un
        # `tsx_nuks is not True` disiplini: ölçülmemiş bir şeyi yeşile yazmak uydurma olurdu,
        # ama kırmızıya yazmak da hüküm kurulamayan bir şeyi ihlal saymak olurdu.
        # KAYIT DENETİMİ DE `ok`u DÜŞÜRÜR — ama YALNIZ üretim ağacında. Sentetik köklerde kayıt
        # sözleşmeleri (canlı `guard.py`) bulunamaz ve orada "çürük" hükmü kurmak, sınıf
        # hükmündeki kategori hatasının aynısı olurdu (§ `_sinif_sorulabilir`).
        # KORUMA ÇİVİSİ ÇÜRÜMESİ DE `ok`u DÜŞÜRÜR: çivisiz bir korumalı-zincir kaydı, kendi
        # kendini doğrulayan bir beyandır — ve bu defterin varlık sebebi tam olarak "beyan
        # ölçülebilir olsun"dur (ölçüldü: sevk kalkınca rapor hiç değişmiyor).
        "ok": not tarihsel_dogrudan and not beyansiz and not curuk_beyan and not (celiskiler or [])
              and not _kcd
              and len(canli) <= CANLI_TABAN and not codelaw.UNSCANNED
              and not (_ksd["curuk"] if root == VARSAYILAN_KOK else [])
              and not (_ksd["kayitsiz"] if root == VARSAYILAN_KOK else [])
              and not (_ssd["curuk"] if root == VARSAYILAN_KOK else [])
              and not (_ssd["kayitsiz"] if root == VARSAYILAN_KOK else []),
    }
