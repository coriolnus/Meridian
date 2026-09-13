"""ablasyon.py — EDG-2026-090 GÖLGE↔GERÇEK AYRIŞMA TEŞHİSİ: üç nedenin ABLASYONLA ölçümü.

SORU. EDG-2026-088'in PK (2) "gerçek" ayağı 2026-09-13'te ÖLÇÜLDÜ ve DÜŞTÜ: son 10 canlı işlemde
ortalama |gölge R − gerçek R| 0,295 (hepsi) / 0,479 (doğrulanmış dolum) vs eşik 0,05. O rapor ÜÇ
aday nedeni ADIYLA verdi ama hangisinin ne kadar taşıdığını ÖLÇMEDİ. Kart `EDG-2026-090` o boşluğu
kapatır: (A) giriş semantiği · (B) E2 ATR/limit enjeksiyonu · (C) `manage_position` paritesi —
her biri AYRI AYRI ve BİRLEŞİK (A+B+C) kapatıldığında ort |Δ R|'de ne kadar düşüş olduğu.

ABLASYONLAR ÖLÇÜM TARAFINDADIR — ÜRETİM KODU DEĞİŞMEZ (kart kill#2: "ablasyon gölge motorunun
ÜRETİM yolunu değiştirirse geçersiz"). Hiçbir ablasyon `meridian/golge_icra.py`, `meridian/broker.py`
ya da `meridian/strategy.py` dosyasına DOKUNMAZ; motorun İÇ yüzeyleri bu SÜRECİN İÇİNDE, `with`
bloğu süresince SARMALANIR (monkeypatch) ve blok bitince BİREBİR geri konur. Sarmalanan yüzeylerin
ADLARI sonuç künyesinde (`enjeksiyon_kunyesi`) durur; üç motor dosyasının sha256'sı koşumdan ÖNCE ve
SONRA ölçülür ve ayrışırsa hiçbir sayı yayılmaz (`kaynak_dokunulmadi`).

TEK KAYNAK — BU DOSYADA YENİDEN YAZILAN HİÇBİR YASA/EŞİK YOKTUR:
  * ŞASİ: `pk2_gercek.kos` (donmuş girdi kimliği → gölge geçişi → `sayim.kontrol_olc`) OLDUĞU GİBİ
    çağrılır. Ablasyon o çağrının ETRAFINA kurulur, İÇİNE kopyalanmaz.
  * EŞİKLER: KARTIN KENDİSİNDEN okunur (`research/cards/EDG-2026-090-…yaml` → `esikler`), bu
    dosyada sayı olarak yazılı DEĞİLDİR. Kartın `ort_fark_r_ust`u ile motorun `golge_icra.FARK_R_UST`
    sabiti ayrıca KARŞILAŞTIRILIR (`esik_ayrismasi`) — ikisi ayrışırsa ölçüm BAŞLAMAZ.
  * GİRİŞ KAPILARI: ablasyon A üretimin gap/limit/stop kapılarını ÜRETİMİN KENDİ fonksiyonlarıyla
    uygular (`broker.entry_law`, `broker.MAX_ENTRY_GAP_PCT`, `broker.entry_limit_price`) ve pozisyon
    sözlüğünü `golge_icra._girisi_dene`nin KENDİSİNE kurdurur — üç alan (giriş fiyatı, hisse başı
    risk, su işaretleri) ablasyonun TANIMI gereği üzerine yazılır ve bu üç alan raporda ADIYLA durur.
  * FRİKSİYON PAYI, "gecti"nin üç değerli mantığı, R paydası hassasiyet kapısı: `sayim` modülünde.

ÜÇ ABLASYON (kart `olcum_plani`; her biri K'de BİR deneme):
  A — GİRİŞ SEMANTİĞİ. Üretimin `PaperBroker.fill_entry`i tetik testi YAPMAZ: silahlı planı ertesi
      açılışta KOŞULSUZ doldurur. Gölge "ilk uygun bar + stop-al" kuralını uygular (`golge_icra`
      beyanlı sapma 3) ve açılışı tetiğin ALTINDA olan seansta HİÇ girmez. A bu kuralı üretimin
      kuralıyla değiştirir; dolum fiyatı donmuş girdinin `e2` satırındaki GERÇEK dolumdur
      (`fill`), yoksa barın açılışı — hangisinin konuştuğu işlem başına `dolum_kaynagi`nda durur.
  B — E2 ATR/LİMİT ENJEKSİYONU. Gölge giriş limitini `entry_limit_price(tetik, None)` ile kurar
      (uyuyan planda ATR yoktur — motorun beyanlı sapması 4); gerçek yolda ATR VARDIR ve `e2`
      satırında ölçülüdür. B o ATR'yi limit hesabına ENJEKTE eder. Enjeksiyonun GERÇEKTEN
      olduğu sayaçla ölçülür (`enjeksiyon_n`) — "bağlanmadı" ile "bağlandı ama yasa gereği atıl"
      ayrı olgulardır ve rapor ikisini KARIŞTIRMAZ.
  C — `manage_position` PARİTESİ. Canlı çıkış zinciri ÜÇLÜDÜR (`strategy.manage_position` +
      `PaperBroker.scale_out` + `PaperBroker._touch_exit`); gölge üçüncüsünü çağırır, ikincisini
      ÇAĞIRMAZ (beyanlı sapma 2: `scale_out` broker DURUMU ister). C ölçüm sürecinde GERÇEK bir
      `PaperBroker` kitabı kurar ve zinciri canlının SIRASIYLA kurar. Zincirin kalan girdileri
      ÖLÇÜLÜR, varsayılmaz (`parite` bloğu): keşif kolu rejim gevşetmesi, `pivot`, çıkış icra
      fiyatı. Ölçülemeyen girdi `None` + ADLI neden ile durur (uydurma yasağı) ve C'nin paritesi
      KISMİ olarak beyan edilir.

ADAY D (TANI — K HARCAMAZ, kart `aday_d_notu_2026_09_13`). Gerçek işlemin R paydası defterde
DOĞRUDAN yoktur; `pnl_dollars / r_multiple / qty` ile geri TÜRETİLİR ve plan satırının stop
mesafesiyle kıyaslanır. İki payda da raporlanır çünkü kartın notu ile brief'in formülü FARKLI
mesafeleri adlandırıyor (`entry − stop` = 29,03 $ vs `entry_trigger − stop` = 26,68 $ — VRTX);
birini seçip ötekini susturmak, okuru bir tarafa sessizce bağlardı. Ayrıca farkın TAM TOPLAMSAL
ayrışması verilir: Δ = (payda etkisi) + (fiyat yolu etkisi), gerçek R'nin plan paydasıyla yeniden
hesabı üzerinden — bu, "kalan fark sınıfı"nı bir beyandan bir ÖLÇÜME çevirir.

POZİTİF KONTROL ÜÇLÜDÜR (kart `pozitif_kontrol`), üçü de yeşil değilse HİÇBİR SAYI YAYILMAZ:
  (1) SENTETİK — ablasyonların YAPISAL OLARAK etkisiz olduğu bir sahnede (e2 satırı YOK → A'nın
      dolumu barın açılışı, B'nin ATR'si None; iki işlem de GİRİŞ barının içinde kapanır → çıkış
      zinciri hiç koşmaz) gölge R'si el hesabıyla birebir ve BEŞ kipte de AYNI: ablasyon bir şeyi
      BOZMUYOR.
  (2) TABAN YENİDEN ÜRETİM — ablasyonsuz koşum, EDG-088'in donmuş sonucuyla (`sonuc_…164520`)
      SKALER BAYT-EŞ. Kıyas dışı bırakılan alanlar SAYI DEĞİLDİR ve adıyla listelenir (duvar
      saati, MUTLAK yollar — bunlar checkout adresidir — ve `rejim_kapisi` META bloğu; sonuncusu
      taban koşumu TSK-184 ÖNCESİ bir ağaçta üretildiği için ayrışır, farkın kendisi raporlanır).
  (3) TERS KONTROL — çıkış kuralı bilerek TERSİNE çevrilince (`manage_position.exit_now` inkâr
      edilir) ort |Δ| ARTMALI. Artmıyorsa ölçüm farkı GÖRMÜYOR demektir ve düşüş iddiaları
      dayanaksız kalır.

OKUR: donmuş girdi artefaktı + manifestosu, donmuş bar önbelleği, donmuş v5 sözleşme kopyası
(hepsi `pk2_gercek`in VARSAYILANLARI — İTHAL edilir, kopyalanmaz), EDG-088'in donmuş taban sonucu
ve EDG-2026-090 kartı (eşikler).
YAZAR: yalnız `--cikti-dizin` altındaki iki artefakt (`sonuc_<utc>.json` + `rapor_<utc>.md`) ve
`--state-dizin` altındaki GEÇİCİ gölge defterleri (ablasyon başına AYRI alt dizin — ortak dizin
kullanılsaydı `golge_icra.adim`in idempotens kapısı ikinci ablasyonun seanslarını sessizce
ATLARDI). Canlı `state/` altına HİÇBİR ŞEY yazmaz; `--state-dizin` deponun `state/` ağacının
altındaysa betik BAŞLAMADAN durur (`_ortak.state_izni`).

KOŞUM (operatörün koşacağı biçim) — `--girdi`, `--bars-dizin`, `--params` VERİLMEZ:
  .venv/bin/python research/olcumler/edg090_golge_ayrisma/ablasyon.py \\
      --state-dizin <tmp> --cikti-dizin research/olcumler/edg090_golge_ayrisma/ablasyon \\
      --ablasyon yok A B C ABC
ÇIKIŞ: 0 rapor yazıldı · 2 PK düştü (sayı yayılmaz) · 1 hata (ön şart tutmadı).
"""
from __future__ import annotations

import argparse
import contextlib
import dataclasses
import datetime as dt
import hashlib
import inspect
import json
import pathlib
import sys

import pandas as pd
import yaml

SANDBOX = pathlib.Path(__file__).resolve().parent
KOK = SANDBOX.parents[2]
#: KARDEŞ ÖLÇÜM DİZİNİ — PK (2) şasisi (`pk2_gercek`, `pk3_selef`, `sayim`, `_ortak`) ORADA yaşar
#: ve BURAYA KOPYALANMAZ. `research/` bir paket DEĞİLDİR (ölçümler birbirinden yalıtık dizinlerdir),
#: o yüzden ithal YOLLA yapılır: önce kardeş dizin `sys.path`e konur, sonra şasi ithal edilir —
#: şasinin kendi bootstrap'ı (`_ortak.yolu_kur`) depo kökünü `sys.path[0]`a alır ve `meridian`
#: ithalini BU ağaca bağlar (kurulu kopya ana checkout'u gösteriyor; ölçüldü 2026-09-13).
EDG088 = KOK / "research" / "olcumler" / "edg088_golge_pilot"
for _p in (str(SANDBOX), str(EDG088)):
    while _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

import _ortak  # noqa: E402            — Blok / yolu_kur / state_izni (PK (2) ile AYNI nesne)
import pk2_gercek as pk2  # noqa: E402  — PK (2) şasisi: donmuş girdi + gölge geçişi + sayım
import pk3_selef as pk3  # noqa: E402   — `_depo_goreli`, sözleşme dosyaları (pk2 üzerinden de gelir)
import sayim  # noqa: E402             — eşik/pay/`gecti` mantığı ORADA
from meridian import broker as brk  # noqa: E402
from meridian import golge_icra as gi  # noqa: E402
from meridian import strategy as strat  # noqa: E402

Blok = _ortak.Blok

KART = "EDG-2026-090"
SELEF = "EDG-2026-088"

#: KART DOSYASI — eşiklerin TEK KAYNAĞI. Ad modül sabitidir ve çağrı anında çözülür.
KART_ADI = "research/cards/EDG-2026-090-golge-gercek-ayrisma-teshisi.yaml"

#: EDG-088'in DONMUŞ TABAN SONUCU — PK (2)'nin kıyas artefaktı (kart `olcum_plani` 1. satır).
TABAN_SONUC_ADI = "pk2_gercek/sonuc_20260913T164520+0000.json"

#: ABLASYON KODLARI — kapalı küme. `ABC` birleşiktir (kart: hüküm TANI'dır, K'ye 1 çarpılır).
ABLASYONLAR = ("yok", "A", "B", "C", "ABC")
TABAN_KODU = ABLASYONLAR[0]

#: TERS KONTROL KODU — komut satırında YOKTUR (bir ablasyon değil, PK (3)'ün aracıdır).
TERS_KODU = "C_TERS"
TERS_NEDEN = "ters_kontrol"

#: ABLASYON KODU → AÇIK BACAKLAR. Kod çözümü KAPALI KÜMEDİR, bir ALT-DİZGE testi DEĞİL: `"C" in
#: kod` deseni `TERS_KODU`nun içindeki "C" harfine bacak açar (bu BİLİNÇLİDİR ve burada KAYITTIR)
#: ama adı olmayan her koda da açardı (`"CB"` → B+C) — ölçüm o zaman künyesinde yazmayan bir kiple
#: koşardı. Küme `ABLASYONLAR` ile AYRI yaşadığı için ayrışma çivisi vardır (tek-kaynak yasası).
BACAKLAR = {
    "yok": frozenset(),
    "A": frozenset({"A"}),
    "B": frozenset({"B"}),
    "C": frozenset({"C"}),
    "ABC": frozenset({"A", "B", "C"}),
    TERS_KODU: frozenset({"C"}),
}

#: MADDE 2 (broker gap/slip) ile MADDE 3 (bar kaynağı) AYNI `delta_fiyat` sayısını taşır; bu veriyle
#: payları AYRIŞMAZ. Sınıf ayrışmasının ölçülemeyen kısmı `None` + BU NEDEN ile durur — ayrıştığı
#: iddia edilseydi, ölçülmemiş bir pay "ölçüldü" diye karta girerdi (uydurma yasağı).
PAYLASIM_NEDENI = ("ölçülemedi: fiyat yolu ile bar kaynağı bu veriyle ayrışmaz — ikisi de AYNI "
                   "`delta_fiyat` sayısını taşır; bps tablosu bar kaynağı ayrışmasının GİRİŞ "
                   "bacağındaki BÜYÜKLÜĞÜNÜ verir, o büyüklüğün Δ_fiyat İÇİNDEKİ PAYINI vermez")

#: KILL#5 (EDG-088 emsali, kart kill#3): PK tutmazsa bu alanların ADLARI durur, DEĞERLERİ durmaz.
BASTIRILAN = ("ort_mutlak_fark_r", "dusus_r", "fark_r", "golge_r", "gercek_r",
              "turetilen_risk_mesafesi", "oran")

#: PK (2) KIYASINDAN DIŞLANAN ALANLAR — hiçbiri SAYI DEĞİLDİR; her biri adıyla + gerekçesiyle.
#: Yol: `/` ile ayrılmış sözlük anahtarı zinciri.
PK2_DISLANAN = {
    "olculdu_utc": "duvar saati — ölçümün kendisi değil, ne zaman koştuğu",
    "motor_yolu": "MUTLAK yol: hangi checkout'un motoru koştu (kanıt alanı, kıyas alanı değil)",
    "girdi/dosya": "MUTLAK yol — donmuş girdinin KİMLİĞİ `sha256` alanındadır ve KIYASA GİRER",
    "girdi/manifest": "MUTLAK yol (manifesto kimliği `sha256` üzerinden kıyaslanır)",
    "parametre_kaynagi/yol": "MUTLAK yol — sözleşmenin kimliği `sha256` alanındadır",
    "parametre_kaynagi/manifest": "MUTLAK yol",
    "bar_kaynagi/dizin": "MUTLAK yol — bar kimliği `son_seans` + girdi manifestosuyla kıyaslanır",
    "rejim_kapisi": ("META blok, sayı DEĞİL: taban koşumu TSK-184 ÖNCESİ bir ağaçta üretildi "
                     "(`motorda_fonksiyon_var=false`), bugünkü ağaçta `regime.regime_ok` bir "
                     "FONKSİYONdur. Farkın kendisi raporda ADIYLA durur; ÖLÇÜLEN SAYILARIN "
                     "bayt-eş çıkması, o taşımanın bu küme üzerinde davranış-koruyucu olduğunun "
                     "BAĞIMSIZ kanıtıdır"),
    "ablasyon": ("ÖLÇÜM HARNESS'İNİN izi (bu kartın eklediği alan), taban artefaktında karşılığı "
                 "YOK. Taban kipinde HİÇBİR yüzeyin sarmalanmadığı ayrıca ZORLANIR "
                 "(`sarmalanan_yuzeyler` boş değilse koşum durur) — yani dışlama bir boşluk "
                 "değil, ayrıca kapatılmış bir kapıdır"),
}

#: SENTETİK SAHNE (PK 1) — EL HESABI. Selef: `tests/test_edg088_pk2_gercek_v472.py` B1 sahnesi
#: (aynı doktrin: iki işlem de GİRİŞ barının İÇİNDE kapanır, `manage_position` ve rejim kapısı
#: sonuca HİÇ karışmaz). BU kartın sorusu farklıdır: R'nin doğruluğu değil, ABLASYONUN ETKİSİZLİĞİ.
#: Sahne bunun için seçilmiştir — `e2` satırı YOK (A'nın dolumu barın açılışına, B'nin ATR'si
#: None'a düşer) ve `exit.scale_out_frac` 0 (C'nin eklediği halka atıl). Üç ablasyonun da
#: YAPISAL olarak etkisiz olduğu bir sahnede çıkan fark, ablasyonun BOZDUĞU bir şeydir.
#:   AAPL: tetik 100 · stop 95 · hedef 115 · giriş barı (o=101, h=116, l=99)
#:         dolum 101 (A'da da 101: açılış ≥ tetik) · r/hisse 6 · faz 2 → hedef 115 · R = 14/6
#:   MSFT: tetik 200 · stop 190 · hedef 230 · giriş barı (o=202, h=205, l=189)
#:         dolum 202 · r/hisse 12 · faz 2 → stop 190 · R = −1,0
SENTETIK_TICKERLAR = ("AAPL", "MSFT")
SENTETIK_D_PLAN = "2026-09-01"
SENTETIK_D_GIRIS = "2026-09-02"
SENTETIK_BEKLENEN_R = {"AAPL": round(14.0 / 6.0, 6), "MSFT": -1.0}
SENTETIK_BEKLENEN_NEDEN = {"AAPL": "target", "MSFT": "stop"}

#: ÜRETİM DOSYALARI — koşum boyunca KAYNAĞININ DEĞİŞMEDİĞİ ölçülür (kart kill#2'nin mekanik kancası).
MOTOR_DOSYALARI = ("meridian/golge_icra.py", "meridian/broker.py", "meridian/strategy.py")

#: A'NIN ÜZERİNE YAZDIĞI POZİSYON ALANLARI — ablasyonun TANIMI budur, raporda ADIYLA durur.
A_YAZILAN_ALANLAR = ("giris_fiyat", "r_per_share", "hi_water", "lo_water")

#: SARMALANAN MOTOR YÜZEYLERİ — ablasyon koduna göre. Künye raporda basılır.
SARMALANAN = {
    "A": ("golge_icra._girisi_dene",),
    "B": ("golge_icra.brk.entry_limit_price", "golge_icra._girisi_dene (yalnız plan kimliği)"),
    "C": ("golge_icra.brk.PaperBroker._touch_exit", "golge_icra.adim (yalnız params yakalama)"),
    TERS_KODU: ("golge_icra.brk.PaperBroker._touch_exit", "golge_icra.adim",
                "golge_icra.strategy.manage_position (exit_now İNKÂR)"),
}

#: Ablasyon bağlamının PAYLAŞILAN durumu. Modül düzeyindedir çünkü sarmalayıcılar `golge_icra`nın
#: İÇİNDEN çağrılır ve oraya ek argüman geçirmenin yolu yoktur (motor imzası DEĞİŞMEZ).
_AKTIF: dict = {}


# ==================================================================================================
# YOL VARSAYILANLARI — HEPSİ `pk2_gercek`TEN İTHAL (ikinci bir yol kopyası sessizce ayrışırdı)
# ==================================================================================================
def girdi_varsayilan() -> pathlib.Path:
    """`--girdi` VARSAYILANI — PK (2)'nin donmuş A1 artefaktı, AYNI nesne."""
    return pk2.girdi_varsayilan()


def bars_varsayilan() -> pathlib.Path:
    """`--bars-dizin` VARSAYILANI — PK (2)'nin donmuş bar önbelleği (SALT-OKUNUR)."""
    return pk2.bars_varsayilan()


def params_varsayilan() -> pathlib.Path:
    """`--params` VARSAYILANI — PK (2)'nin donmuş `canli_v5_donmus` dizini."""
    return pk2.params_varsayilan()


def taban_sonuc_varsayilan() -> pathlib.Path:
    """`--taban-sonuc` VARSAYILANI — EDG-088'in donmuş PK (2) sonucu (kıyas artefaktı)."""
    return EDG088 / TABAN_SONUC_ADI


def kart_yolu() -> pathlib.Path:
    """Kart dosyası — eşiklerin TEK KAYNAĞI."""
    return KOK / KART_ADI


# ==================================================================================================
# EŞİKLER — KARTTAN OKUNUR, BU DOSYADA YAZILI DEĞİL
# ==================================================================================================
def esikler() -> dict:
    """Kartın `esikler` bloğu + motor sabitiyle AYRIŞMA ölçümü.

    Eşiği bu dosyada sayı olarak yazmak, kartın sözleşmesinin İKİNCİ bir kopyası olurdu ve ilk
    düzeltmede çatallanırdı (tek-kaynak yasası). Kart okunamıyorsa ya da eşik motorun kendi
    sabitiyle (`golge_icra.FARK_R_UST`) ayrışıyorsa koşum BAŞLAMAZ: ölçüm hangi eşiğe göre
    hüküm verdiğini bilmeden koşamaz.
    """
    yol = kart_yolu()
    if not yol.exists():
        raise Blok(f"kart dosyası YOK: {yol} — eşiklerin tek kaynağı odur, ölçüm başlamaz")
    kart = yaml.safe_load(yol.read_text(encoding="utf-8")) or {}
    es = kart.get("esikler") or {}
    eksik = [a for a in ("ort_fark_r_ust", "ablasyon_dusus_alt_r", "n_hukum_cifti_alt")
             if es.get(a) is None]
    if eksik:
        raise Blok(f"kartın `esikler` bloğunda alan(lar) YOK: {eksik} ({yol})")
    motor = float(gi.FARK_R_UST)
    ayrisma = (float(es["ort_fark_r_ust"]) != motor)
    if ayrisma:
        raise Blok(f"kart eşiği {es['ort_fark_r_ust']} ile motor sabiti golge_icra.FARK_R_UST "
                   f"{motor} AYRIŞIYOR — hangi eşiğin konuştuğu belirsizken ölçüm başlamaz")
    return {"ort_fark_r_ust": float(es["ort_fark_r_ust"]),
            "ablasyon_dusus_alt_r": float(es["ablasyon_dusus_alt_r"]),
            "n_hukum_cifti_alt": int(es["n_hukum_cifti_alt"]),
            "kaynak": pk3._depo_goreli(yol, KOK),
            "motor_sabiti": motor, "esik_ayrismasi": ayrisma}


def _sha256(yol: pathlib.Path) -> str:
    return hashlib.sha256(pathlib.Path(yol).read_bytes()).hexdigest()


def motor_kaynak_damgasi() -> dict:
    """Üç üretim dosyasının sha256'sı — ablasyonun KAYNAĞA dokunmadığının mekanik kanıtı."""
    return {ad: _sha256(KOK / ad) for ad in MOTOR_DOSYALARI}


# ==================================================================================================
# BAR KAYNAĞI AYRIŞMASI — `acilis` (donmuş CSV) ↔ `e2.resmi_acilis` (gerçek yolun kaydı)
# ==================================================================================================
def _acilis_bps(acilis, resmi_acilis) -> tuple[float | None, str | None]:
    """`(acilis − resmi_acilis) / resmi_acilis × 1e4` — ölçülemezse `None` + ADLI neden.

    İKİ AÇILIŞ İKİ KAYNAKTIR: `acilis` donmuş CSV barının açılışı (gölgenin gördüğü), `resmi_acilis`
    gerçek yolun `e2` satırına yazdığı resmî açılış (canlının gördüğü). Ayrışmaları "bar kaynağı"
    sınıfının TEK DOĞRUDAN ölçüsüdür. Ölçülemeyen satır 0 SAYILMAZ: 0 "iki kaynak aynı" demektir,
    `None` "bilmiyorum" demektir (uydurma yasağı).
    """
    if resmi_acilis is None:
        return None, "e2.resmi_acilis yok (donmuş girdinin e2 satırında alan boş)"
    if isinstance(resmi_acilis, bool) or not isinstance(resmi_acilis, (int, float)):
        return None, f"e2.resmi_acilis sayı değil: {resmi_acilis!r}"
    if float(resmi_acilis) == 0.0:
        return None, "e2.resmi_acilis sıfır — bps paydası tanımsız"
    if acilis is None:
        return None, "bar açılışı yok (donmuş CSV'de o seansın barı bulunamadı)"
    return round((float(acilis) - float(resmi_acilis)) / float(resmi_acilis) * 1e4, 4), None


def bar_kaynagi_ozeti(a_izi: list) -> dict:
    """Ablasyon A izinin `acilis_vs_resmi_acilis_bps` ÖZETİ — "bar kaynağı" sınıfının SAYISI.

    n / ort / medyan / ort |·| AYNI kümeden gelir; ölçülemeyen satırlar paydadan sessizce
    DÜŞMEZ, sayılır ve nedenleriyle durur. ORTALAMA İLE MEDYAN BİRLİKTE basılır: tek bir aykırı
    sembol ortalamayı taşır, medyanı taşımaz — tek sayı basmak bu körlüğü gizlerdi. Liste |bps|
    AZALAN sıradadır (en çok ayrışan sembol başta), sıra bir SONUÇ değil bir okuma kolaylığıdır.
    """
    olculen = [r for r in a_izi if r.get("acilis_vs_resmi_acilis_bps") is not None]
    olculemeyen = [r for r in a_izi if r.get("acilis_vs_resmi_acilis_bps") is None]
    d = sorted(float(r["acilis_vs_resmi_acilis_bps"]) for r in olculen)
    n = len(d)
    medyan = None if not n else (d[n // 2] if n % 2 else (d[n // 2 - 1] + d[n // 2]) / 2.0)
    return {
        "n": n,
        "ort_bps": (round(sum(d) / n, 4) if n else None),
        "medyan_bps": (round(medyan, 4) if n else None),
        "ort_mutlak_bps": (round(sum(abs(x) for x in d) / n, 4) if n else None),
        "olculemedi_neden": (None if n else "ablasyon A izinde `acilis_vs_resmi_acilis_bps` "
                             "taşıyan SATIR YOK (A bacağı koşmadı ya da hiçbir e2 satırında "
                             "resmi_acilis yok) — bar kaynağı ayrışması ölçülemedi"),
        "olculemeyen_n": len(olculemeyen),
        "olculemeyen_nedenler": sorted({(r.get("bps_olculemedi") or "neden YAZILMADI")
                                        for r in olculemeyen}),
        "sembol_bazli": [
            {"ticker": r.get("ticker"), "plan_id": r.get("plan_id"), "seans": r.get("seans"),
             "red": r.get("red"), "acilis": r.get("acilis"), "resmi_acilis": r.get("resmi_acilis"),
             "bps": r.get("acilis_vs_resmi_acilis_bps")}
            for r in sorted(olculen, key=lambda x: -abs(float(x["acilis_vs_resmi_acilis_bps"])))],
    }


# ==================================================================================================
# ENJEKSİYON HARİTASI — `e2` SATIRLARI (gerçek yolun İCRA GİRDİLERİ)
# ==================================================================================================
def enjeksiyon_haritasi(veri: dict) -> dict:
    """`plan_id → {fill, atr, limit, resmi_acilis, gap_at_submit}` — donmuş girdinin `e2` satırından.

    Harita `pk2._e2_harita` ile kurulur (İÇ motorun satırı, yoksa ayna satırı): ikinci bir seçim
    kuralı yazmak, iki ölçümün aynı plana farklı satır bağlaması demekti. Sözlük DAR tutulur —
    ablasyonların TÜKETTİĞİ alanlar dışında hiçbir şey gölgeye giremesin diye.
    """
    ham = pk2._e2_harita(veri.get("e2") or [])
    return {pid: {"fill": r.get("fill"), "atr": r.get("atr"), "limit": r.get("limit"),
                  "resmi_acilis": r.get("resmi_acilis"),
                  "gap_at_submit": r.get("gap_at_submit"), "motor": r.get("motor")}
            for pid, r in ham.items()}


# ==================================================================================================
# ABLASYON A — GİRİŞ SEMANTİĞİ (üretim: ertesi açılışta KOŞULSUZ dolum)
# ==================================================================================================
def _giris_ablasyonu(orijinal, enj: dict, iz: list):
    """`golge_icra._girisi_dene`nin ÖLÇÜM SARMALAYICISI: üretimin giriş semantiği.

    ÜÇ PARÇA, ÜÇÜ DE ÜRETİMİN KENDİSİ:
      1. KAPILAR — `broker.entry_law` (gap vetosu), `broker.MAX_ENTRY_GAP_PCT` (kovalama tavanı),
         `broker.entry_limit_price` (limit tavanı) ve açılış≤stop kapısı, `fill_entry`in SIRASIYLA.
         Sıra korunur ki iki motorun REDDİ aynı ADI taşısın. Limit `gi.brk` ÜZERİNDEN çağrılır:
         ablasyon B açıkken o ad E2 ATR'sini enjekte eden sarmalayıcıya çözülür (A+B birleşimi
         böylece kendiliğinden doğru olur, ikinci bir enjeksiyon yolu yazılmaz).
      2. POZİSYON — `golge_icra._girisi_dene`nin KENDİSİ kurar (tetiği 0'a çekilmiş bir kayıtla:
         motorun kendi kodunda "tetik ÖLÇÜLEMEMİŞSE tetik yasası hiç uygulanmaz ve üretimin
         davranışı kalır: açılıştan dolum" dalı budur). Böylece `tuketilen` kesitler, PIT çapası
         ve satır şeması motorun kendi gövdesinden gelir; ablasyon bir KOPYA üretmez.
      3. DOLUM FİYATI — `e2.fill` (gerçek yolun KAYDEDİLMİŞ dolumu), yoksa barın açılışı. Üç
         pozisyon alanı (`A_YAZILAN_ALANLAR`) bu fiyattan yeniden yazılır; dördüncüsü olan
         `trail_stop` DEĞİŞMEZ (üretimde de `Position.trail_stop = stop`).

    Neden barın açılışı DOKTORLANMADI: açılışı fiyata çevirmek `tuketilen` kesitlere ve dolayısıyla
    `kaynak_bar_hash`e sızardı — PIT çapası donmuş barların kanıtı olmaktan çıkar, ablasyonun
    uydurduğu bir barın kanıtı olurdu.
    """
    def _dene(kayit, d, dstr, bars_of, simdi, bar_kaynak):
        _AKTIF["plan_id"] = kayit["plan_id"]
        e2 = enj.get(kayit["plan_id"]) or {}
        df = bars_of(kayit["ticker"])
        bar, kesit = gi._bar_kesiti(df, d, kayit["ticker"])
        if bar is None:
            return gi._giris_yok_satiri(kayit, dstr, "bar_yok", [], simdi, bar_kaynak,
                                        olculemedi="bar_yok"), None
        tetik, stop = float(kayit["tetik"]), float(kayit["stop"])
        acilis = float(bar["open"])
        yasa = gi.brk.entry_law()
        red = None
        if e2.get("gap_at_submit") and yasa["gap_behavior"] == brk.GAP_VETO:
            red = "gap_asildi"
        elif tetik > 0 and acilis > tetik * (1.0 + gi.brk.MAX_ENTRY_GAP_PCT):
            red = "gap_asildi"
        elif tetik > 0 and acilis > gi.brk.entry_limit_price(tetik, None, yasa):
            red = "limit_asildi"
        elif acilis <= stop:
            red = "acilis_stop_altinda"
        bps, bps_neden = _acilis_bps(acilis, e2.get("resmi_acilis"))
        if red is not None:
            iz.append({"plan_id": kayit["plan_id"], "ticker": kayit["ticker"], "seans": str(dstr),
                       "red": red, "acilis": acilis, "tetik": tetik, "dolum": None,
                       "dolum_kaynagi": None, "golge_kuralinda_girerdi": None,
                       "golge_kuralinin_dolumu": None,
                       # BAR KAYNAĞI: ret satırı da taşır — ret kararının KENDİSİ (açılış ≤ stop)
                       # bu açılıştan çıkar, satır düşseydi tablo yalnız GİRENLERİ ölçerdi.
                       "resmi_acilis": e2.get("resmi_acilis"),
                       "acilis_vs_resmi_acilis_bps": bps, "bps_olculemedi": bps_neden})
            return gi._giris_yok_satiri(kayit, dstr, red, [kesit], simdi, bar_kaynak), None
        dolum = float(e2["fill"]) if e2.get("fill") is not None else acilis
        kaynak_ad = "e2_fill" if e2.get("fill") is not None else "bar_acilis"
        satir, poz = orijinal(dict(kayit, tetik=0.0), d, dstr, bars_of, simdi, bar_kaynak)
        if poz is not None:
            poz["giris_fiyat"] = dolum
            poz["r_per_share"] = dolum - stop
            poz["hi_water"] = dolum
            poz["lo_water"] = dolum
        iz.append({"plan_id": kayit["plan_id"], "ticker": kayit["ticker"], "seans": str(dstr),
                   "red": None, "acilis": acilis, "tetik": tetik, "dolum": dolum,
                   "dolum_kaynagi": kaynak_ad,
                   # GÖLGENİN KENDİ KURALI bu barda ne yapardı — A'nın DEĞİŞTİRDİĞİ şeyin ölçüsü.
                   "golge_kuralinda_girerdi": (bool(float(bar["high"]) >= tetik) if tetik > 0
                                               else True),
                   "golge_kuralinin_dolumu": (max(acilis, tetik) if tetik > 0 else acilis),
                   # BAR KAYNAĞI SINIFININ ÖLÇÜSÜ: donmuş CSV'nin açılışı ile gerçek yolun resmî
                   # açılışı arasındaki bps. `enjeksiyon_haritasi` bu alanı ZATEN taşıyordu ama
                   # TÜKETİLMİYORDU — kanıt bir cümleydi, artık bir SAYI (inceleme §4, 2026-09-13).
                   "resmi_acilis": e2.get("resmi_acilis"),
                   "acilis_vs_resmi_acilis_bps": bps, "bps_olculemedi": bps_neden})
        return satir, poz
    return _dene


def _kimlik_sarmali(orijinal):
    """`_girisi_dene`nin İNCE sarmalayıcısı: yalnız AKTİF plan kimliğini yazar, davranışa dokunmaz.

    Ablasyon B tek başına koşarken de limit sarmalayıcısının HANGİ planın ATR'sini enjekte
    edeceğini bilmesi gerekir; motorun imzası değiştirilemeyeceği için kimlik bu sarmalayıcıyla
    taşınır. Gövde ORİJİNALDİR — bu sarmalayıcı ölçülen hiçbir şeyi değiştirmez (kendi izi de
    yoktur: enjeksiyonun izi zaten limit sarmalayıcısında sayılır).
    """
    def _dene(kayit, d, dstr, bars_of, simdi, bar_kaynak):
        _AKTIF["plan_id"] = kayit["plan_id"]
        return orijinal(kayit, d, dstr, bars_of, simdi, bar_kaynak)
    return _dene


# ==================================================================================================
# ABLASYON B — E2 ATR ENJEKSİYONU (limit tavanı)
# ==================================================================================================
def _limit_ablasyonu(enj: dict, iz: list):
    """`broker.entry_limit_price`in ÖLÇÜM SARMALAYICISI: ATR'siz çağrıya E2'nin ATR'sini verir.

    Hesabı ÜRETİM yapar (`brk.entry_limit_price`); sarmalayıcı yalnız eksik argümanı doldurur.
    Her çağrıda ATR'Lİ ve ATR'SİZ limit AYRI AYRI ölçülür ve `e2.limit` ile kıyaslanır: enjeksiyonun
    GERÇEKLEŞTİĞİ (sayaç) ile enjeksiyonun bir FARK yarattığı (limit kayması) AYRI olgulardır —
    ikisini tek sayıya sıkıştırmak, "bağlanmadı" ile "bağlandı ama yasa gereği atıl"ı karıştırırdı.
    """
    def _elp(trigger, atr=None, cfg=None):
        pid = _AKTIF.get("plan_id")
        e2 = enj.get(pid) or {}
        kullanilan = e2.get("atr") if atr is None else atr
        atrsiz = brk.entry_limit_price(trigger, None, cfg)
        atrli = brk.entry_limit_price(trigger, kullanilan, cfg)
        iz.append({"plan_id": pid, "tetik": trigger,
                   "enjekte_atr": (None if kullanilan is None else float(kullanilan)),
                   "limit_atrsiz": round(float(atrsiz), 6), "limit_atrli": round(float(atrli), 6),
                   "e2_limit": e2.get("limit"),
                   "limit_degisti": bool(round(float(atrli), 6) != round(float(atrsiz), 6))})
        return atrli
    return _elp


class _BrokerVekili:
    """`golge_icra`nın gördüğü `broker` modülünün ÖLÇÜM VEKİLİ.

    Motorun içindeki `brk.X` erişimleri bu nesneye düşer; üzerine YAZILMAYAN her ad GERÇEK modüle
    delege edilir. Modülün kendisini yamamak (ör. `broker.entry_limit_price = …`) canlı yola açık
    bir süreçte üretim davranışını değiştirirdi; vekil yalnız GÖLGE motorunun gördüğü adı değiştirir.
    """

    def __init__(self, gercek, ustler: dict):
        self._gercek = gercek
        self._ustler = dict(ustler)

    def __getattr__(self, ad):
        ustler = object.__getattribute__(self, "_ustler")
        if ad in ustler:
            return ustler[ad]
        return getattr(object.__getattribute__(self, "_gercek"), ad)


class _StratejiVekili(_BrokerVekili):
    """`golge_icra`nın gördüğü `strategy` modülünün vekili (ters kontrol için)."""


# ==================================================================================================
# ABLASYON C — `manage_position` + `_touch_exit` PARİTESİ
# ==================================================================================================
def _parite_touch(kitap, iz: list, ters: bool = False):
    """Canlı çıkış zincirinin GÖLGEDEKİ karşılığı: `scale_out` → `_touch_exit`, canlının SIRASIYLA.

    `golge_icra.adim` bu adı `brk.PaperBroker._touch_exit(None, poz, bar)` diye çağırır (broker
    DURUMU olmadan); C ölçüm sürecinde GERÇEK bir kitap kurar ve aynı çağrıyı o kitapla yapar —
    yani gölgenin beyanlı sapması (2) ölçüm tarafında KAPANIR. Bankalama gerçekleşirse ADIYLA
    sayılır; `exit.scale_out_frac` 0 iken üretim fonksiyonu ilk satırda False döner ve halka ATIL
    olur — ama HALKA VARDIR ve sayacı bunu gösterir ("çağrılmadı" ile "çağrıldı, ateşlemedi"
    ayrı olgulardır).
    """
    # SAYAÇ HALKANIN İÇİNDE: `scale_out`un KENDİSİ sarmalanır, `_touch_exit` sarmalayıcısı değil.
    # Sayaç dışarıda olsaydı halkayı zincirden çıkaran bir değişiklik sayacı DEĞİŞTİRMEZDİ ve
    # "çağrıldı" iddiası `_touch_exit` çağrılarını sayan bir totolojiye dönerdi (mutasyon m3 bunu
    # gösterdi: halka kaldırıldığında sayaç aynı kaldı).
    gercek_scale_out = kitap.scale_out

    def _scale_out(poz, bar_sozlugu, params):
        bankaladi = gercek_scale_out(poz, bar_sozlugu, params)
        iz.append({"halka": "scale_out", "plan_id": getattr(poz, "plan_id", None),
                   "bankaladi": bool(bankaladi), "ters": ters})
        return bankaladi

    def _touch(_yok, poz, bar):
        p = {"high": bar["high"], "low": bar["low"], "open": bar["open"]}
        _scale_out(poz, p, _AKTIF.get("params") or {})
        return brk.PaperBroker._touch_exit(kitap, poz, bar)
    return _touch


def _adim_sarmali(orijinal):
    """`golge_icra.adim`ın İNCE sarmalayıcısı: o seansın ETKİN düğmelerini yakalar, davranışa
    dokunmaz. `scale_out` canlıda `params` ister ve motorun imzası bunu dışarı vermez."""
    def _adim(dstr, **kw):
        _AKTIF["params"] = kw.get("params") or {}
        return orijinal(dstr, **kw)
    return _adim


def _manage_ters(iz: list):
    """`strategy.manage_position`ın TERS KONTROL sarmalayıcısı — PK (3)'ün aracı.

    Kararı ÜRETİM verir, sarmalayıcı yalnız `exit_now`u İNKÂR eder: çıkması gereken pozisyon
    tutulur, tutulması gereken çıkar. Ölçüm bir fark GÖRÜYORSA bu bozma ort |Δ|'yi ARTIRMALIDIR;
    artmıyorsa düşüş iddialarının hiçbiri dayanak taşımaz.
    """
    def _manage(bars, position, params, bars_held, regime_ok):
        dec = strat.manage_position(bars, position, params, bars_held, regime_ok)
        ters = not bool(dec.exit_now)
        iz.append({"orijinal_exit_now": bool(dec.exit_now), "ters_exit_now": ters})
        return dataclasses.replace(dec, exit_now=ters,
                                   exit_reason=(TERS_NEDEN if ters else None))
    return _manage


@contextlib.contextmanager
def ablasyon_kur(kod: str, enj: dict, goal: dict):
    """Ablasyonu KUR, `yield` boyunca koştur, sonra motoru BİREBİR geri koy.

    Kod KAPALI KÜMEDEN (`BACAKLAR`) çözülür; kümede olmayan kod `Blok` atar — alt-dizge testi
    adı olmayan bir koda sessizce bacak açardı ve ölçüm künyesinde yazmayan bir kiple koşardı.

    Geri koyma `finally`dedir ve HER adı ayrı ayrı geri yazar: kısmi bir geri alım, sonraki
    ablasyonu sessizce kirletirdi (ölçüm sırası sonucu belirlerdi). Sarmalanan adların kimliği
    `iz` sözlüğünde sayılır ve sonuç künyesine girer — "sarmaladım" bir iddia değil bir ÖLÇÜM olur.
    """
    if kod not in BACAKLAR:
        raise Blok(f"bilinmeyen ablasyon kodu {kod!r} — kapalı küme {sorted(BACAKLAR)}")
    bacak = BACAKLAR[kod]
    iz = {"A": [], "B": [], "C": [], "ters": [], "sarmalanan": []}
    orij_girisi_dene, orij_brk, orij_adim, orij_strategy = (gi._girisi_dene, gi.brk, gi.adim,
                                                            gi.strategy)
    try:
        brk_ustler: dict = {}
        if "B" in bacak:
            brk_ustler["entry_limit_price"] = _limit_ablasyonu(enj, iz["B"])
            iz["sarmalanan"].extend(SARMALANAN["B"])
        if "C" in bacak:
            # KİTAP NOMİNALDİR (emsal `sayim._broker_surtunmesi`: sürtünmeyi okumak için kurulan
            # kitap da `equity=1.0` alır). Boyutlandırma yolu gölge defterinde KOŞMAZ — defter
            # plan düzeyindedir (beyanlı sapma 1) ve `scale_out` sermayeye bakmaz.
            kitap = brk.PaperBroker(equity=1.0,
                                    slippage_bps=float(goal["slippage_bps"]),
                                    commission_per_share=float(goal["commission_per_share"]))
            ters = kod == TERS_KODU
            brk_ustler["PaperBroker"] = type(
                "_PaperBrokerParite", (), {"_touch_exit": staticmethod(
                    _parite_touch(kitap, iz["C"], ters=ters))})
            gi.adim = _adim_sarmali(orij_adim)
            iz["sarmalanan"].extend(SARMALANAN[TERS_KODU if ters else "C"])
            if ters:
                gi.strategy = _StratejiVekili(orij_strategy,
                                              {"manage_position": _manage_ters(iz["ters"])})
        if brk_ustler:
            gi.brk = _BrokerVekili(orij_brk, brk_ustler)
        if "A" in bacak:
            gi._girisi_dene = _giris_ablasyonu(orij_girisi_dene, enj, iz["A"])
            iz["sarmalanan"].extend(SARMALANAN["A"])
        elif "B" in bacak:
            gi._girisi_dene = _kimlik_sarmali(orij_girisi_dene)
        yield iz
    finally:
        gi._girisi_dene = orij_girisi_dene
        gi.brk = orij_brk
        gi.adim = orij_adim
        gi.strategy = orij_strategy
        _AKTIF.clear()


# ==================================================================================================
# BİR ABLASYON KOŞUMU
# ==================================================================================================
def kos_ablasyon(kod: str, girdi: pathlib.Path, bars_dizin: pathlib.Path,
                 params_dizin: pathlib.Path, state_koku: pathlib.Path, enj: dict, goal: dict,
                 seans_tavani: int | None = None, n_gercek: int | None = None,
                 beklenen_tickerlar: tuple[str, ...] | None = None) -> dict:
    """PK (2) şasisini `kod` ablasyonu altında koşar. Dönüş: `pk2.kos`un sonucu + ablasyon izi.

    HER ABLASYON KENDİ STATE ALT DİZİNİNDE koşar: ortak bir kök kullanılsaydı `golge_icra.adim`in
    idempotens kapısı (`dstr <= son_seans`) ikinci ablasyonun seanslarını sessizce ATLAR ve ikinci
    ölçüm birincinin defterini okurdu.
    """
    state = pathlib.Path(state_koku) / kod
    with ablasyon_kur(kod, enj, goal) as iz:
        sonuc = pk2.kos(girdi, bars_dizin, params_dizin, state, seans_tavani,
                        n_gercek=n_gercek, beklenen_tickerlar=beklenen_tickerlar)
    sonuc["ablasyon"] = {
        "kod": kod,
        "sarmalanan_yuzeyler": sorted(set(iz["sarmalanan"])),
        "a_izi": iz["A"], "b_izi": iz["B"],
        "c_scale_out_cagrisi": sum(1 for r in iz["C"] if r.get("halka") == "scale_out"),
        "c_scale_out_atesledi": sum(1 for r in iz["C"]
                                    if r.get("halka") == "scale_out" and r["bankaladi"]),
        "ters_cagri": len(iz["ters"]),
        "ters_inkar_edilen_cikis": sum(1 for r in iz["ters"] if r["orijinal_exit_now"]),
        "b_enjeksiyon_n": sum(1 for r in iz["B"] if r.get("enjekte_atr") is not None),
        "b_limit_degisen_n": sum(1 for r in iz["B"] if r.get("limit_degisti")),
    }
    # TABAN KİPİ SAF OLMAK ZORUNDA: PK (2) tabanı ablasyon künyesi DIŞLANARAK kıyaslar, o yüzden
    # "ablasyonsuz" iddiası ayrıca ZORLANIR — bir sarmalayıcı sızsaydı kıyas onu görmezdi.
    if kod == TABAN_KODU and sonuc["ablasyon"]["sarmalanan_yuzeyler"]:
        raise Blok(f"taban kipinde SARMALAYICI var: {sonuc['ablasyon']['sarmalanan_yuzeyler']} — "
                   "ablasyonsuz koşum ablasyonlu koşmuş olurdu")
    return sonuc


def _ozet(sonuc: dict) -> dict:
    """Bir koşumun HÜKÜM SAYILARI — iki paydadan (hepsi / doğrulanmış), kart kill#3 gereği."""
    k, kd = sonuc["kontrol"], sonuc["kontrol_dogrulanmis"]
    return {"n_cift": k["n_cift"], "n_hukum_cifti": k["n_hukum_cifti"],
            "ort_fark_r": k["ort_fark_r"], "ort_mutlak_fark_r": k["ort_mutlak_fark_r"],
            "komisyon_kayma_payi": k["komisyon_kayma_payi"], "gecti": k["gecti"],
            "giris_yok_n": k["giris_yok_n"], "n_payi_olculemeyen": k["n_payi_olculemeyen"],
            "dogrulanmis": {"n_cift": kd["n_cift"], "n_hukum_cifti": kd["n_hukum_cifti"],
                            "ort_mutlak_fark_r": kd["ort_mutlak_fark_r"],
                            "gecti": kd["gecti"]},
            "n_olculemeyen": sonuc["n_olculemeyen"],
            "cikis_neden_eslesme": _eslesme_orani(sonuc)}


def _eslesme_orani(sonuc: dict) -> dict:
    """Çıkış nedeni eşleşmesi — ölçülebilen çiftlerin kaçında gölge ile gerçek AYNI nedeni yazdı."""
    olculen = [r for r in sonuc["islemler"] if r.get("cikis_neden_eslesti") is not None]
    return {"n": len(olculen), "eslesen": sum(1 for r in olculen if r["cikis_neden_eslesti"]),
            "oran": (round(sum(1 for r in olculen if r["cikis_neden_eslesti"]) / len(olculen), 6)
                     if olculen else None)}


def _cift_haritasi(sonuc: dict) -> dict:
    """`plan_id → çift` — yalnız HÜKÜM çiftleri (payı ÖLÇÜLEBİLEN), kıyasın paydası budur."""
    return {str(c["plan_id"]): c for c in (sonuc["kontrol"].get("ciftler") or [])
            if c.get("friksiyon_payi_r") is not None}


def kiyas_kur(kosumlar: dict, esik_dusus: float, taban_kodu: str = TABAN_KODU) -> dict:
    """Ablasyonların TABANA göre düşüşü — İKİ PAYDADAN, ikisi de raporda.

    KENDİ KÜMESİ: ablasyonun kendi hüküm çiftleri (kartın `ort_fark_r_ust` eşiğinin uygulandığı
    istatistiğin ta kendisi; `ablasyon_dusus_alt_r` hükmü BUNA bakar).
    ORTAK KÜME: tabanın ve TÜM ablasyonların ORTAK plan kimlikleri. Neden ayrıca gerekli: bir
    ablasyon paydaya YENİ bir çift ekleyebilir (A'da tetiği gelmeyen plan girer) ve o zaman
    ortalamadaki düşüşün ne kadarının FARKIN küçülmesinden, ne kadarının PAYDANIN büyümesinden
    geldiği tek sayıdan okunamaz. İkisini birlikte basmak bu körlüğü kapatır (bedel yasası).
    """
    taban = kosumlar[taban_kodu]
    ciftler = {kod: _cift_haritasi(s) for kod, s in kosumlar.items()}
    ortak = sorted(set.intersection(*[set(c) for c in ciftler.values()])) if ciftler else []

    def _ort(kod, kume):
        c = ciftler[kod]
        secim = [abs(float(c[p]["fark_r"])) for p in kume if p in c]
        return (round(sum(secim) / len(secim), 6) if secim else None), len(secim)

    tablo = []
    taban_kendi = taban["kontrol"]["ort_mutlak_fark_r"]
    taban_ortak, _ = _ort(taban_kodu, ortak)
    taban_tum = (taban["kontrol"].get("tum_ciftler") or {}).get("ort_mutlak_fark_r")
    for kod, s in kosumlar.items():
        kendi = s["kontrol"]["ort_mutlak_fark_r"]
        ortak_ort, ortak_n = _ort(kod, ortak)
        tum = (s["kontrol"].get("tum_ciftler") or {}).get("ort_mutlak_fark_r")
        d_kendi = (None if (kendi is None or taban_kendi is None)
                   else round(taban_kendi - kendi, 6))
        d_ortak = (None if (ortak_ort is None or taban_ortak is None)
                   else round(taban_ortak - ortak_ort, 6))
        tablo.append({
            "kod": kod,
            "n_hukum_cifti": s["kontrol"]["n_hukum_cifti"],
            "ort_mutlak_fark_r": kendi,
            "dusus_kendi_kumesi": d_kendi,
            # KARTIN HÜKMÜ: "katkı var" = ort |Δ|'de en az `ablasyon_dusus_alt_r` düşüş. Eşik
            # KENDİ KÜMESİNE uygulanır (kartın `ort_fark_r_ust`unun uygulandığı istatistiğin
            # ta kendisi); ortak küme aynı hükmü CONFOUND'suz paydada tekrarlar.
            "katki_var_kendi": (None if d_kendi is None else bool(d_kendi >= esik_dusus)),
            "ortak_n": ortak_n, "ort_mutlak_fark_r_ortak": ortak_ort,
            "dusus_ortak_kume": d_ortak,
            "katki_var_ortak": (None if d_ortak is None else bool(d_ortak >= esik_dusus)),
            # TÜM ÇİFTLER (payı ölçülemeyen dahil): TANI, hükme GİRMEZ — ama basılmazsa
            # ablasyonun hüküm kümesi DIŞINDAKİ etkisi görünmez kalırdı (bedel yasası).
            "tum_cift_ort_mutlak": tum,
            "tum_cift_dusus": (None if (tum is None or taban_tum is None)
                               else round(taban_tum - tum, 6)),
            "tum_cift_n": (s["kontrol"].get("tum_ciftler") or {}).get("n"),
            "dogrulanmis_ort_mutlak": s["kontrol_dogrulanmis"]["ort_mutlak_fark_r"],
            "cikis_neden_eslesme": _eslesme_orani(s),
            **_yon_sayaci(ciftler[taban_kodu], ciftler[kod], ortak),
        })
    return {"ortak_kume": ortak, "taban_kodu": taban_kodu, "tablo": tablo,
            "esik_dusus": esik_dusus, "islem_basina": _islem_basina(kosumlar, ciftler)}


def _yon_sayaci(taban_ciftler: dict, ciftler: dict, ortak: list) -> dict:
    """Ortak kümede KAÇ işlemin |Δ|'si düştü, kaçının ARTTI — ortalama ikisini de yutabilir.

    Bir ablasyon bazı işlemleri düzeltip bazılarını bozabilir; yalnız ortalamayı basmak bu iki
    yönü tek sayıda toplar ve "hiçbir şey değişmedi" ile "eşit ve zıt değişti" aynı görünürdü.
    """
    iyi = kotu = ayni = 0
    for p in ortak:
        a, b = taban_ciftler.get(p), ciftler.get(p)
        if a is None or b is None or a.get("fark_r") is None or b.get("fark_r") is None:
            continue
        fa, fb = abs(float(a["fark_r"])), abs(float(b["fark_r"]))
        if round(fb - fa, 9) < 0:
            iyi += 1
        elif round(fb - fa, 9) > 0:
            kotu += 1
        else:
            ayni += 1
    return {"n_iyilesen": iyi, "n_kotulesen": kotu, "n_degismeyen": ayni}


def _islem_basina(kosumlar: dict, ciftler: dict) -> list:
    """İşlem başına Δ tablosu: her plan için her kipin farkı (ölçülemeyen kip ADIYLA)."""
    planlar: dict = {}
    for kod, s in kosumlar.items():
        for r in s["islemler"]:
            planlar.setdefault(str(r["plan_id"]), {"ticker": r["ticker"], "kipler": {}})
            planlar[str(r["plan_id"])]["kipler"][kod] = {
                "golge_r": r["golge_r"], "gercek_r": r["gercek_r"], "fark_r": r["fark_r"],
                "golge_giris_fiyat": r["golge_giris_fiyat"],
                "golge_cikis_neden": r["golge_cikis_neden"] or r["golge_giris_reddi"],
                "hukum_ciftinde": str(r["plan_id"]) in ciftler[kod],
                "olculemedi": r["olculemedi"],
                "golge_seans_n": r["golge_seans_n"], "gercek_seans_n": r["gercek_seans_n"]}
    return [{"plan_id": pid, **d} for pid, d in sorted(planlar.items())]


# ==================================================================================================
# ADAY D — RİSK PAYDASI TANISI (K HARCAMAZ) + FARKIN TOPLAMSAL AYRIŞMASI
# ==================================================================================================
def tani_d(secilen: list, planlar: dict) -> list:
    """Her gerçek işlem için: türetilen risk mesafesi vs plan stop mesafesi + Δ'nın ayrışması.

    TÜRETME. Gerçek R'nin paydası (`Position.risk_dollars`) defterde YOKTUR; `pnl_dollars /
    r_multiple` ile geri türetilir ve hisse başına `qty` ile bölünür. |r_multiple| çok küçükse
    (3 ondalıklı R) türetim hassasiyetsizdir — `sayim.R_MULTIPLE_ALT` kapısı BURADA DA geçerlidir
    ve altındaki işlem `None` + ADLI neden ile durur (ikinci bir hassasiyet yorumu yazılmaz).

    İKİ PAYDA. Kartın notu 29,03 $ der (= `gerçek entry − plan.stop`), brief'in formülü
    `entry_trigger − stop` (= 26,68 $) der. İkisi FARKLI mesafelerdir; biri seçilip öteki
    susturulsaydı okur bir tarafa sessizce bağlanırdı. İkisi de sütundur, oranları da.

    AYRIŞMA (kalan fark sınıfının ÖLÇÜMÜ). Gerçek R'yi GÖLGENİN paydasıyla yeniden hesaplarsak
    (`(exit − entry) / (entry − plan.stop)`) fark İKİYE ve TAM TOPLAMSAL olarak bölünür:
      Δ_payda = gerçek_r_plan_paydasıyla − gerçek_r      (canlı stop ≠ plan.stop sınıfı)
      Δ_fiyat = gölge_r − gerçek_r_plan_paydasıyla       (dolum/çıkış fiyat yolu + bar kaynağı)
      Δ_toplam = gölge_r − gerçek_r = Δ_payda + Δ_fiyat  (özdeşlik; sütunda ayrıca doğrulanır)
    """
    out = []
    for t in secilen:
        pid = str(t.get("plan_id") or "")
        p = planlar.get(pid) or {}
        r, q = t.get("r_multiple"), t.get("qty")
        pnl, giris, cikis = t.get("pnl_dollars"), t.get("entry"), t.get("exit")
        stop, tetik = p.get("stop"), p.get("entry_trigger")
        kayit = {"plan_id": pid, "ticker": t.get("ticker"), "gercek_r": r, "qty": q,
                 "pnl_dollars": pnl, "gercek_entry": giris, "gercek_exit": cikis,
                 "plan_stop": stop, "entry_trigger": tetik,
                 "turetilen_risk_mesafesi": None, "turetilemedi": None,
                 "mesafe_giris_stop": None, "mesafe_tetik_stop": None,
                 "oran_giris": None, "oran_tetik": None,
                 "gercek_r_plan_paydasiyla": None, "delta_payda": None}
        if r is None or q in (None, 0) or pnl is None:
            kayit["turetilemedi"] = "gerçek satırda `r_multiple`/`qty`/`pnl_dollars` YOK"
            out.append(kayit)
            continue
        if abs(float(r)) < sayim.R_MULTIPLE_ALT:
            kayit["turetilemedi"] = (f"|r_multiple|={abs(float(r)):.3f} < "
                                     f"{sayim.R_MULTIPLE_ALT} — 3 ondalıklı R ile türetilen payda "
                                     "hassasiyetsiz (sayim.R_MULTIPLE_ALT)")
            out.append(kayit)
            continue
        turetilen = abs(float(pnl) / (float(r) * float(q)))
        kayit["turetilen_risk_mesafesi"] = round(turetilen, 6)
        if stop is not None and giris is not None:
            kayit["mesafe_giris_stop"] = round(abs(float(giris) - float(stop)), 6)
            kayit["oran_giris"] = round(kayit["mesafe_giris_stop"] / turetilen, 6)
            payda = float(giris) - float(stop)
            if payda > 0 and cikis is not None:
                yeniden = (float(cikis) - float(giris)) / payda
                kayit["gercek_r_plan_paydasiyla"] = round(yeniden, 6)
                kayit["delta_payda"] = round(yeniden - float(r), 6)
        if stop is not None and tetik is not None:
            kayit["mesafe_tetik_stop"] = round(abs(float(tetik) - float(stop)), 6)
            kayit["oran_tetik"] = round(kayit["mesafe_tetik_stop"] / turetilen, 6)
        out.append(kayit)
    return out


def ayrisma_tablosu(tani: list, sonuc: dict) -> list:
    """Δ'nın payda/fiyat ayrışması — BİR ablasyon koşumunun işlem satırlarıyla eşleştirilmiş."""
    islem = {str(r["plan_id"]): r for r in sonuc["islemler"]}
    out = []
    for d in tani:
        r = islem.get(d["plan_id"]) or {}
        golge_r, fark = r.get("golge_r"), r.get("fark_r")
        payda = d.get("delta_payda")
        fiyat = (None if (golge_r is None or d.get("gercek_r_plan_paydasiyla") is None)
                 else round(float(golge_r) - float(d["gercek_r_plan_paydasiyla"]), 6))
        toplam = (None if (payda is None or fiyat is None) else round(payda + fiyat, 6))
        out.append({"plan_id": d["plan_id"], "ticker": d["ticker"],
                    "fark_r": fark, "delta_payda": payda, "delta_fiyat": fiyat,
                    "delta_toplam_kontrol": toplam,
                    "ozdeslik_tuttu": (None if (toplam is None or fark is None)
                                       else bool(abs(toplam - float(fark)) < 1e-6))})
    return out


# ==================================================================================================
# C PARİTESİNİN ÖLÇÜMÜ — VARSAYILMAZ
# ==================================================================================================
def parite_olc(secilen: list, taban: dict, enj: dict) -> dict:
    """Canlı çıkış zincirinin gölgeyle AYRIŞABİLECEĞİ girdileri ÖLÇER (beyan değil ölçüm).

    Ölçülemeyen girdi `None` + ADLI neden ile durur ve C'nin paritesi KISMİ olarak beyan edilir:
    "kapattım" demek, kapatılamayanı sessizce kapatılmış göstermek olurdu.
    """
    kesif = [str(t.get("plan_id")) for t in secilen if t.get("exploration")]
    scaled = [str(t.get("plan_id")) for t in secilen if t.get("scaled_out")]
    params = taban["params"]
    by_regime = taban.get("by_regime") or {}
    frac_rejim = {rej: (hucre or {}).get("exit.scale_out_frac", params.get("exit.scale_out_frac"))
                  for rej, hucre in by_regime.items()}
    pivot_var = any("pivot" in (e or {}) for e in enj.values())
    return {
        "kesif_kolu": {
            "n_exploration": len(kesif), "plan_idler": kesif,
            "hukum": ("canlı GEVŞEK rejim dalı (`loop.daily_cycle` keşif pozisyonları) bu kümede "
                      "HİÇ kullanılmadı → gölgenin SIKI küresel kapısı zaten PARİTE"
                      if not kesif else
                      "kümede keşif kökenli pozisyon VAR — gevşek dal gölgeye uygulanmadı, C'nin "
                      "paritesi bu işlemlerde KISMİdir"),
            "parite": not kesif},
        "scale_out": {
            "frac_taban": params.get("exit.scale_out_frac"),
            "frac_rejim": frac_rejim,
            "gercekte_atesleyen_islem": scaled,
            "zincire_eklendi": True,
            "parite": (float(params.get("exit.scale_out_frac") or 0.0) <= 0.0
                       and not scaled),
            "hukum": ("C zinciri canlının SIRASINI kurar (scale_out → _touch_exit); donmuş v5 "
                      "sözleşmesinde `exit.scale_out_frac` 0 olduğu için halka ATIL koşar — "
                      "çağrı sayacı halkanın VAR olduğunu, ateşleme sayacı 0 olduğunu ölçer")},
        "pivot": {
            "olculdu": pivot_var, "golge_degeri": 0.0,
            "neden": (None if pivot_var else
                      "donmuş girdinin `e2` satırları `pivot` TAŞIMAZ; canlı `Position.pivot` "
                      "`entry_law` yan tablosundan gelir ve o tablo donmuş artefaktın DIŞINDADIR "
                      "— C'nin bu bacağı ÖLÇÜLEMEDİ (uydurma yasağı), parite KISMİ"),
            "parite": None if not pivot_var else True},
        "cikis_icra_fiyati": _dikisi_olc(
            'close_position(t, per[t].loc[d, "open"]',
            "canlı bekleyen çıkışlar D'nin AÇILIŞINDA icra edilir — gölge faz 1a ile AYNI"),
        "zincir_sirasi": _sira_olc(
            "b.scale_out(", "b._touch_exit(",
            "canlı gün-içi zincirde `scale_out` `_touch_exit`ten ÖNCE çağrılır — C aynı sırayı kurar"),
    }


def _loop_kaynagi() -> tuple[str | None, str | None]:
    """`loop.daily_cycle`ın KAYNAĞI (metin) ya da `(None, neden)`.

    Neden kaynak okuması: canlı `loop.daily_cycle` bu ölçüm sürecinde ÇAĞRILAMAZ (emir/onay
    yüzeyine ulaşır). Davranışı bir BEYANLA yazmak, canlı değişince beyanın sessizce bayatlaması
    demekti; kaynaktaki dikişin VARLIĞI ve SIRASI ölçülürse beyan kendi çürümesini haber verir.
    """
    try:
        from meridian import loop as _loop
        return inspect.getsource(_loop.daily_cycle), None
    except (ImportError, OSError, TypeError, AttributeError) as e:  # sessiz-yutma: kaynak okunamadıysa davranış ÖLÇÜLEMEDİ demektir; uydurulmuş bir "parite var" beyanı canlı ayrışmayı gizlerdi
        return None, f"loop.daily_cycle kaynağı okunamadı: {type(e).__name__}"


def _dikisi_olc(aranan: str, beyan: str) -> dict:
    """Canlı gövdede bir dikişin VARLIĞINI ölçer; yoksa `parite=None` + ADLI neden."""
    kaynak, neden = _loop_kaynagi()
    if kaynak is None:
        return {"olculdu": False, "parite": None, "neden": neden, "beyan": beyan}
    var = aranan in kaynak
    return {"olculdu": True, "parite": var, "aranan": aranan,
            "neden": (None if var else f"`{aranan}` dikişi loop.daily_cycle gövdesinde "
                                       "BULUNAMADI — canlı yol değişmiş, beyan BAYAT sayılır"),
            "beyan": beyan}


def _sira_olc(once: str, sonra: str, beyan: str) -> dict:
    """İki dikişin canlı gövdedeki SIRASINI ölçer — varlık tek başına sıra demek değildir."""
    kaynak, neden = _loop_kaynagi()
    if kaynak is None:
        return {"olculdu": False, "parite": None, "neden": neden, "beyan": beyan}
    i, j = kaynak.find(once), kaynak.find(sonra)
    if i < 0 or j < 0:
        return {"olculdu": True, "parite": None, "aranan": [once, sonra],
                "neden": f"dikişlerden biri BULUNAMADI (once={i >= 0}, sonra={j >= 0})",
                "beyan": beyan}
    return {"olculdu": True, "parite": bool(i < j), "aranan": [once, sonra],
            "neden": (None if i < j else "canlı gövdede sıra TERS ölçüldü — C'nin kurduğu zincir "
                                         "canlının sırası DEĞİL"),
            "beyan": beyan}


# ==================================================================================================
# POZİTİF KONTROL (1) — SENTETİK SAHNE
# ==================================================================================================
def _sentetik_barlar(bars_dizin: pathlib.Path) -> None:
    """SPY (rejim/takvim) + AAPL + MSFT. Giriş barı (D+1) el hesabının sahnesidir."""
    seanslar = list(pd.bdate_range("2025-06-02", SENTETIK_D_GIRIS))
    isinma = seanslar[:-1]
    bars_dizin.mkdir(parents=True, exist_ok=True)

    def _yaz(ticker, satirlar):
        pd.DataFrame(satirlar).to_csv(bars_dizin / f"{ticker.lower()}.csv", index=False)

    spy, fiyat = [], 400.0
    for d in seanslar:
        spy.append({"date": str(d.date()), "open": fiyat, "high": fiyat * 1.004,
                    "low": fiyat * 0.996, "close": fiyat * 1.001, "volume": 50_000_000.0})
        fiyat *= 1.001
    _yaz("SPY", spy)

    def _duz(taban):
        return [{"date": str(d.date()), "open": taban, "high": taban * 1.004,
                 "low": taban * 0.996, "close": taban, "volume": 1_000_000.0} for d in isinma]

    _yaz("AAPL", _duz(100.0) + [{"date": SENTETIK_D_GIRIS, "open": 101.0, "high": 116.0,
                                 "low": 99.0, "close": 110.0, "volume": 2_000_000.0}])
    _yaz("MSFT", _duz(200.0) + [{"date": SENTETIK_D_GIRIS, "open": 202.0, "high": 205.0,
                                 "low": 189.0, "close": 195.0, "volume": 2_000_000.0}])


def _sentetik_girdi(dizin: pathlib.Path) -> pathlib.Path:
    """Donmuş girdinin sentetik ikizi + manifestosu. `e2` BOŞTUR: A'nın dolumu barın açılışına,
    B'nin ATR'si `None`a düşer — ablasyonlar YAPISAL olarak etkisizdir ve PK tam bunu sınar."""
    dizin.mkdir(parents=True, exist_ok=True)

    def _plan(ticker, tetik, stop, hedef):
        return {"id": f"P-{SENTETIK_D_PLAN}-{ticker}", "date": SENTETIK_D_PLAN, "ticker": ticker,
                "side": "long", "entry_trigger": tetik, "stop": stop, "profit_target": hedef,
                "setup": "momentum_burst", "gate_verdict": "REVIEW", "dormant_setup": 0,
                "strategy_version": 5, "score": 80, "regime_at_plan": "trend_up"}

    def _islem(ticker, r, giris, cikis, qty, neden):
        e, x = round(giris * 1.0005, 4), round(cikis * 0.9995, 4)
        return {"id": f"T-{ticker}", "plan_id": f"P-{SENTETIK_D_PLAN}-{ticker}", "ticker": ticker,
                "side": "long", "ts_open": SENTETIK_D_GIRIS, "ts_close": SENTETIK_D_GIRIS,
                "entry": e, "exit": x, "qty": qty, "r_multiple": r,
                "pnl_dollars": round(qty * (x - e), 4), "costs": None, "exit_reason": neden,
                "bars_held": 1, "scaled_out": 0, "exploration": 0, "strategy_version": 5,
                "setup": "momentum_burst", "kaynak": "live_paper",
                "extra_json": json.dumps({"alpaca_fill_price": x, "dolum_ts": "x"})}

    veri = {"trades": [_islem("AAPL", SENTETIK_BEKLENEN_R["AAPL"], 101.0, 115.0, 165, "target"),
                       _islem("MSFT", SENTETIK_BEKLENEN_R["MSFT"], 202.0, 190.0, 50, "stop")],
            "plans": [_plan("AAPL", 100.0, 95.0, 115.0), _plan("MSFT", 200.0, 190.0, 230.0)],
            "e2": [], "cekim_utc": "2026-09-13T00:00:00"}
    yol = dizin / "sentetik.json"
    yol.write_text(json.dumps(veri, ensure_ascii=False), encoding="utf-8")
    (dizin / pk2.MANIFEST_ADI).write_text(
        f"{hashlib.sha256(yol.read_bytes()).hexdigest()}  {yol.name}\n", encoding="utf-8")
    return yol


def sentetik_sahne(kok: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    """`(girdi, bars_dizin)` — sentetik sahneyi `kok` altına kurar."""
    bars = pathlib.Path(kok) / "barlar"
    _sentetik_barlar(bars)
    return _sentetik_girdi(pathlib.Path(kok) / "girdi"), bars


def pk_sentetik(kok: pathlib.Path, params_dizin: pathlib.Path, goal: dict,
                kodlar: tuple[str, ...] = ABLASYONLAR) -> dict:
    """PK (1): sentetik sahnede gölge R el hesabıyla birebir VE BÜTÜN kiplerde AYNI."""
    girdi, bars = sentetik_sahne(kok)
    kipler, sapan = {}, []
    for kod in kodlar:
        s = kos_ablasyon(kod, girdi, bars, params_dizin, pathlib.Path(kok) / "state", {}, goal,
                         n_gercek=len(SENTETIK_TICKERLAR),
                         beklenen_tickerlar=SENTETIK_TICKERLAR)
        olculen = {r["ticker"]: {"golge_r": r["golge_r"], "neden": r["golge_cikis_neden"]}
                   for r in s["islemler"]}
        kipler[kod] = olculen
        for tic, beklenen in SENTETIK_BEKLENEN_R.items():
            g = olculen.get(tic) or {}
            if g.get("golge_r") is None or round(float(g["golge_r"]), 6) != round(beklenen, 6):
                sapan.append({"kod": kod, "ticker": tic, "beklenen_r": beklenen,
                              "olculen_r": g.get("golge_r")})
            if g.get("neden") != SENTETIK_BEKLENEN_NEDEN[tic]:
                sapan.append({"kod": kod, "ticker": tic,
                              "beklenen_neden": SENTETIK_BEKLENEN_NEDEN[tic],
                              "olculen_neden": g.get("neden")})
    return {"gecti": not sapan, "kipler": kipler, "sapan": sapan,
            "beklenen_r": SENTETIK_BEKLENEN_R, "beklenen_neden": SENTETIK_BEKLENEN_NEDEN,
            "beyan": ("sentetik sahnede `e2` satırı YOK ve `exit.scale_out_frac` 0 — A/B/C "
                      "yapısal olarak etkisizdir; kiplerin herhangi birinde R'nin kayması, "
                      "ablasyonun ölçtüğü şeyi değil BOZDUĞU şeyi gösterirdi")}


# ==================================================================================================
# POZİTİF KONTROL (2) — TABANIN YENİDEN ÜRETİMİ (SKALER BAYT-EŞ)
# ==================================================================================================
def _dusur(d, yol: str = ""):
    """`PK2_DISLANAN` yollarını düşürerek sözlüğün SKALER izdüşümünü kurar."""
    if isinstance(d, dict):
        out = {}
        for k, v in d.items():
            alt = f"{yol}/{k}" if yol else k
            if alt in PK2_DISLANAN:
                continue
            out[k] = _dusur(v, alt)
        return out
    if isinstance(d, list):
        return [_dusur(x, yol) for x in d]
    return d


def skaler_izdusum(sonuc: dict) -> str:
    """Ölçülen SAYILARIN kanonik bayt dizisi — PK (2)'nin kıyas nesnesi."""
    return json.dumps(_dusur(dict(sonuc)), ensure_ascii=False, sort_keys=True, default=str)


def pk_taban(taban_sonuc: dict, taban_artefakt: pathlib.Path) -> dict:
    """PK (2): ablasyonsuz koşum ile EDG-088'in donmuş sonucunun SKALER BAYT-EŞLİĞİ."""
    yol = pathlib.Path(taban_artefakt)
    if not yol.exists():
        raise Blok(f"EDG-088 taban sonucu YOK: {yol} — PK (2) kıyassız ölçülemez")
    donmus = json.loads(yol.read_text(encoding="utf-8"))
    a, b = skaler_izdusum(donmus), skaler_izdusum(taban_sonuc)
    farklar = [] if a == b else _fark_bul(_dusur(donmus), _dusur(dict(taban_sonuc)))
    return {"gecti": a == b,
            "artefakt": pk3._depo_goreli(yol, KOK),
            "artefakt_sha256": _sha256(yol),
            "izdusum_sha256": {"donmus": hashlib.sha256(a.encode()).hexdigest(),
                               "yeniden": hashlib.sha256(b.encode()).hexdigest()},
            "farklar": farklar[:40],
            "dislanan": PK2_DISLANAN,
            "meta_farklari": _meta_farklari(donmus, taban_sonuc)}


def _fark_bul(x, y, yol: str = "") -> list:
    """İki sözlük arasındaki İLK farkları ADIYLA — "eşit değil" tek başına teşhis değildir."""
    out: list = []
    if type(x) is not type(y):
        return [{"yol": yol, "donmus": str(x)[:120], "yeniden": str(y)[:120], "sinif": "tip"}]
    if isinstance(x, dict):
        for k in sorted(set(x) | set(y)):
            if k not in x or k not in y:
                out.append({"yol": f"{yol}/{k}", "sinif": "eksik_anahtar",
                            "donmus": k in x, "yeniden": k in y})
            else:
                out.extend(_fark_bul(x[k], y[k], f"{yol}/{k}"))
    elif isinstance(x, list):
        if len(x) != len(y):
            out.append({"yol": yol, "sinif": "uzunluk", "donmus": len(x), "yeniden": len(y)})
        else:
            for i, (u, v) in enumerate(zip(x, y)):
                out.extend(_fark_bul(u, v, f"{yol}[{i}]"))
    elif x != y:
        out.append({"yol": yol, "sinif": "deger", "donmus": str(x)[:120], "yeniden": str(y)[:120]})
    return out


def _meta_farklari(donmus: dict, yeniden: dict) -> list:
    """Kıyas DIŞI bırakılan META alanlarının farkı — dışlamak susturmak DEĞİLDİR."""
    out = []
    for yol in sorted(PK2_DISLANAN):
        parca = yol.split("/")
        a, b = donmus, yeniden
        for p in parca:
            a = (a or {}).get(p) if isinstance(a, dict) else None
            b = (b or {}).get(p) if isinstance(b, dict) else None
        if a != b:
            out.append({"alan": yol, "donmus": str(a)[:200], "yeniden": str(b)[:200],
                        "gerekce": PK2_DISLANAN[yol]})
    return out


# ==================================================================================================
# POZİTİF KONTROL (3) — TERS KONTROL
# ==================================================================================================
def pk_ters(taban_sonuc: dict, ters_sonuc: dict) -> dict:
    """PK (3): çıkış kuralı bilerek TERS uygulanınca ort |Δ| ARTMALI (ölçümün YÖN kanıtı)."""
    t = taban_sonuc["kontrol"]["ort_mutlak_fark_r"]
    x = ters_sonuc["kontrol"]["ort_mutlak_fark_r"]
    olculdu = t is not None and x is not None
    return {"gecti": bool(olculdu and float(x) > float(t)),
            "taban_ort_mutlak": t, "ters_ort_mutlak": x,
            "artis": (None if not olculdu else round(float(x) - float(t), 6)),
            "inkar_edilen_cikis_karari": ters_sonuc["ablasyon"]["ters_inkar_edilen_cikis"],
            "manage_cagrisi": ters_sonuc["ablasyon"]["ters_cagri"],
            "neden": (None if olculdu else
                      "taban ya da ters koşumda ort |Δ| ÖLÇÜLEMEDİ — yön sınanamadı"),
            "beyan": ("`strategy.manage_position.exit_now` İNKÂR edilir: çıkması gereken pozisyon "
                      "tutulur, tutulması gereken çıkar. Ölçüm bir fark GÖRÜYORSA bu bozma "
                      "ortalamayı ARTIRMALIDIR")}


# ==================================================================================================
# KOŞUM — HEPSİ
# ==================================================================================================
def kos(girdi: pathlib.Path, bars_dizin: pathlib.Path, params_dizin: pathlib.Path,
        state_dizin: pathlib.Path, kodlar: tuple[str, ...],
        taban_artefakt: pathlib.Path | None = None, seans_tavani: int | None = None) -> dict:
    """Ablasyon ölçümünün tamamı: PK üçlüsü + istenen ablasyonlar + tanı. Dönüş: sonuç sözlüğü."""
    es = esikler()
    kaynak_once = motor_kaynak_damgasi()
    state_dizin = _ortak.state_izni(state_dizin, KOK)
    girdi, bars_dizin = pathlib.Path(girdi), pathlib.Path(bars_dizin)
    params_dizin = pathlib.Path(params_dizin)

    veri = pk2.girdi_oku(girdi)
    secilen = pk2.son_n_gercek(veri["trades"])
    planlar = pk2.plan_haritasi(veri["plans"])
    enj = enjeksiyon_haritasi(veri)
    taban_params = pk2.parametre_tabani(params_dizin)
    goal = yaml.safe_load((params_dizin / "goal.yaml").read_text(encoding="utf-8")) or {}

    # ---- ABLASYONLAR (taban DAİMA koşar: PK (2)'nin ve kıyasın çapası) -----------------------
    istenen = tuple(dict.fromkeys((TABAN_KODU,) + tuple(kodlar)))
    kosumlar: dict = {}
    for kod in istenen:
        kosumlar[kod] = kos_ablasyon(kod, girdi, bars_dizin, params_dizin,
                                     state_dizin / "gercek", enj, goal, seans_tavani)

    # ---- POZİTİF KONTROL ÜÇLÜSÜ ---------------------------------------------------------------
    pk1 = pk_sentetik(state_dizin / "sentetik", params_dizin, goal)
    pk2_ = pk_taban(kosumlar[TABAN_KODU], taban_artefakt or taban_sonuc_varsayilan())
    ters = kos_ablasyon(TERS_KODU, girdi, bars_dizin, params_dizin, state_dizin / "gercek",
                        enj, goal, seans_tavani)
    pk3_ = pk_ters(kosumlar[TABAN_KODU], ters)

    kaynak_sonra = motor_kaynak_damgasi()
    dokunulmadi = kaynak_once == kaynak_sonra

    tani = tani_d(secilen, planlar)
    birlesik = "ABC" if "ABC" in kosumlar else TABAN_KODU
    kiyas = kiyas_kur(kosumlar, es["ablasyon_dusus_alt_r"])
    n_hukum = kosumlar[TABAN_KODU]["kontrol"]["n_hukum_cifti"]

    yayin_engeli = []
    if not pk1["gecti"]:
        yayin_engeli.append(f"PK (1) SENTETİK DÜŞTÜ — ablasyon sahneyi BOZUYOR: {pk1['sapan'][:3]}")
    if not pk2_["gecti"]:
        yayin_engeli.append("PK (2) TABAN YENİDEN ÜRETİM DÜŞTÜ — ablasyonsuz koşum EDG-088'in "
                            f"donmuş sonucuyla SKALER BAYT-EŞ DEĞİL: {pk2_['farklar'][:3]}")
    if not pk3_["gecti"]:
        yayin_engeli.append("PK (3) TERS KONTROL DÜŞTÜ — çıkış kuralı bilerek bozulduğu hâlde "
                            f"ort |Δ| ARTMADI ({pk3_['taban_ort_mutlak']} → "
                            f"{pk3_['ters_ort_mutlak']}): ölçüm farkı GÖRMÜYOR")
    if not dokunulmadi:
        yayin_engeli.append("KILL#2 — koşum sırasında ÜRETİM KAYNAĞI DEĞİŞTİ (sha256 ayrıştı): "
                            f"{[a for a in kaynak_once if kaynak_once[a] != kaynak_sonra[a]]}")
    if n_hukum < es["n_hukum_cifti_alt"]:
        yayin_engeli.append(f"ADIM-0 KAPISI DÜŞTÜ — hüküm çifti n={n_hukum} < "
                            f"{es['n_hukum_cifti_alt']} (kart `n_hukum_cifti_alt`)")

    import meridian as _meridian

    return {
        "kart": KART, "selef": SELEF,
        "olculdu_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "gecti": (None if yayin_engeli else True),
        "yayin_engeli": yayin_engeli, "bastirilan": list(BASTIRILAN),
        "esikler": es,
        "istenen_ablasyonlar": list(istenen),
        "birlesik_kodu": birlesik,
        "ozetler": {kod: _ozet(s) for kod, s in kosumlar.items()},
        "kiyas": kiyas,
        "tani_d": tani,
        "ayrisma": ayrisma_tablosu(tani, kosumlar[birlesik]),
        "ayrisma_kipi": birlesik,
        "parite": parite_olc(secilen, taban_params, enj),
        "pk": {"sentetik": pk1, "taban": pk2_, "ters": pk3_},
        "enjeksiyon_kunyesi": {kod: s["ablasyon"] for kod, s in kosumlar.items()},
        "ters_kunyesi": ters["ablasyon"],
        "kaynak_dokunulmadi": {"gecti": dokunulmadi, "once": kaynak_once, "sonra": kaynak_sonra},
        "girdi": kosumlar[TABAN_KODU]["girdi"],
        "girdi_cekim_utc": veri.get("cekim_utc"),
        "parametre_kaynagi": kosumlar[TABAN_KODU]["parametre_kaynagi"],
        "bar_kaynagi": kosumlar[TABAN_KODU]["bar_kaynagi"],
        "rejim_kapisi": kosumlar[TABAN_KODU]["rejim_kapisi"],
        "motor_yolu": getattr(_meridian, "__file__", None),
        "seans_tavani": kosumlar[TABAN_KODU]["seans_tavani"],
        "sapmalar": kosumlar[TABAN_KODU]["sapmalar"],
        "kalan_fark_sinifi": kalan_fark_sinifi(kosumlar[birlesik], tani, es),
    }


def kalan_fark_sinifi(sonuc: dict, tani: list, es: dict) -> dict:
    """Birleşik ablasyondan SONRA kalan farkın SINIFI — kanıtla, beyanla değil.

    Dört aday sınıf kartın `olcum_plani` son satırından + `aday_d_notu`ndan gelir. Her birinin
    KANITI ölçülmüş bir sayıdır; ölçülemeyeni `None` + neden ile durur.

    DÖRT SINIF BİRBİRİNDEN TAM BAĞIMSIZ ÖLÇÜLMÜŞ DEĞİLDİR ve bu AÇIKÇA yazılır: madde 2 (broker
    gap/slip) ile madde 3 (bar kaynağı) AYNI `delta_fiyat` sayısını paylaşır. Madde 3'ün kendi
    SAYISI vardır (A izinin `acilis_vs_resmi_acilis_bps` tablosu: donmuş CSV açılışı ↔ E2 resmî
    açılışı) ama o bps'in `Δ_fiyat` içindeki PAYI bu veriyle ayrışmaz — pay `None` + `PAYLASIM_NEDENI`
    ile durur. Tur-1'de madde 3'ün "kanıtı" statik bir CÜMLEYDİ ve işaret ettiği karşılaştırma
    kodda HİÇ hesaplanmıyordu (inceleme §4, 2026-09-13); artık sayıdır.
    """
    cift = {str(c["plan_id"]): c for c in (sonuc["kontrol"].get("ciftler") or [])
            if c.get("friksiyon_payi_r") is not None}
    tani_h = {d["plan_id"]: d for d in tani}
    payda_toplam, fiyat_toplam, n = 0.0, 0.0, 0
    for pid, c in cift.items():
        d = tani_h.get(pid) or {}
        if d.get("delta_payda") is None or c.get("fark_r") is None:
            continue
        payda_toplam += abs(float(d["delta_payda"]))
        fiyat_toplam += abs(float(c["fark_r"]) - float(d["delta_payda"]))
        n += 1
    ort_payda = (round(payda_toplam / n, 6) if n else None)
    ort_fiyat = (round(fiyat_toplam / n, 6) if n else None)
    bar = bar_kaynagi_ozeti((sonuc.get("ablasyon") or {}).get("a_izi") or [])
    gap_slip = "broker gap/slip (EDG-2026-045 sınıfı)"
    bar_sinif = "bar kaynağı (donmuş CSV açılışı ↔ E2 resmî açılışı)"
    return {
        "n": n,
        "ort_mutlak_delta_payda": ort_payda,
        "ort_mutlak_delta_fiyat": ort_fiyat,
        "bar_kaynagi_bps": bar,
        "siniflar": [
            {"sinif": "canlı stop ≠ plan.stop (risk paydası — kaynağı loop/broker boyutlandırma)",
             "kanit": (f"ort |Δ payda| = {ort_payda} R (n={n}) — `tani_d.oran_giris` / "
                       "`delta_payda` sütunları (ADAY D, kart aday_d_notu)"),
             "paylasilan_sayi": None},
            {"sinif": gap_slip,
             "kanit": (f"ort |Δ fiyat| = {ort_fiyat} R (n={n}) — birleşik kipte dolum fiyatı + "
                       "çıkış fiyatı yolunun kalıntısı"),
             "paylasilan_sayi": "delta_fiyat", "paylastigi_sinif": bar_sinif,
             "ayrisan_pay_r": None, "ayrisan_pay_neden": PAYLASIM_NEDENI},
            {"sinif": bar_sinif,
             "kanit": (f"ablasyon A izi `acilis_vs_resmi_acilis_bps`: n={bar['n']} · ort "
                       f"{bar['ort_bps']} bps · medyan {bar['medyan_bps']} bps · ort |·| "
                       f"{bar['ort_mutlak_bps']} bps (ölçülemeyen satır {bar['olculemeyen_n']}); "
                       "dolum_kaynagi=e2_fill iken GİRİŞ bacağı bu sınıftan ARINIR, ÇIKIŞ bacağı "
                       "arınmaz"
                       if bar["n"] else f"ÖLÇÜLEMEDİ — {bar['olculemedi_neden']}"),
             "sembol_bazli_bps": bar["sembol_bazli"], "olculemeyen_n": bar["olculemeyen_n"],
             "paylasilan_sayi": "delta_fiyat", "paylastigi_sinif": gap_slip,
             "ayrisan_pay_r": None, "ayrisan_pay_neden": PAYLASIM_NEDENI},
            {"sinif": "parametre kuşağı",
             "kanit": f"parametre_uyumu={sonuc['parametre_ayrismasi']['parametre_uyumu']} "
                      f"(ayrışan işlem {sonuc['parametre_ayrismasi']['n_ayrisan']})",
             "paylasilan_sayi": None},
        ],
        "esik": es["ort_fark_r_ust"],
        "birlesik_ort_mutlak": sonuc["kontrol"]["ort_mutlak_fark_r"],
        "esigin_altina_indi": (None if sonuc["kontrol"]["ort_mutlak_fark_r"] is None
                               else bool(float(sonuc["kontrol"]["ort_mutlak_fark_r"])
                                         <= es["ort_fark_r_ust"])),
    }


# ==================================================================================================
# RAPOR
# ==================================================================================================
def _s(x, basamak: int = 6) -> str:
    if x is None:
        return "—"
    if isinstance(x, bool):
        return "evet" if x else "hayır"
    if isinstance(x, (int, float)):
        return f"{float(x):.{basamak}f}".rstrip("0").rstrip(".") or "0"
    return str(x)


def rapor_metni(sonuc: dict) -> str:
    """Sonuç sözlüğünün Markdown karşılığı. TEK KAYNAK sözlüktür: hiçbir sayı yeniden
    HESAPLANMAZ, yalnız biçimlendirilir (ve PK düştüyse BASTIRILIR)."""
    d = sonuc
    bas = [f"# {d['kart']} — gölge↔gerçek ayrışma teşhisi (ablasyon A/B/C, selef {d['selef']})", "",
           f"**Ölçüm {d['olculdu_utc']}** · kart hükmü Rol-1'indir (bu rapor SAYI üretir, HÜKÜM "
           "YAZMAZ)", ""]
    pk = d["pk"]
    pk_satiri = [
        "## Pozitif kontrol üçlüsü", "",
        f"- **(1) sentetik**: `gecti={pk['sentetik']['gecti']}` — beş kipte de gölge R el hesabı "
        f"({SENTETIK_BEKLENEN_R}) ile birebir" + (f" · SAPAN: {pk['sentetik']['sapan'][:3]}"
                                                  if pk['sentetik']['sapan'] else ""),
        f"- **(2) taban yeniden üretim**: `gecti={pk['taban']['gecti']}` — ablasyonsuz koşum "
        f"`{pk['taban']['artefakt']}` ile skaler bayt-eş "
        f"(izdüşüm sha `{pk['taban']['izdusum_sha256']['yeniden'][:16]}…`)",
        f"- **(3) ters kontrol**: `gecti={pk['ters']['gecti']}` — taban ort |Δ| "
        f"{_s(pk['ters']['taban_ort_mutlak'])} → ters {_s(pk['ters']['ters_ort_mutlak'])} "
        f"(artış {_s(pk['ters']['artis'])}; `manage_position` kararı "
        f"{pk['ters']['manage_cagrisi']} kez çevrildi — bunların "
        f"{pk['ters']['inkar_edilen_cikis_karari']}'i orijinalinde `exit_now=True` idi)",
        f"- **kaynak dokunulmadı**: `{d['kaynak_dokunulmadi']['gecti']}` — "
        f"{', '.join(MOTOR_DOSYALARI)} sha256 koşum öncesi/sonrası",
        "",
    ]

    if d["yayin_engeli"]:
        s = bas + ["## PK DÜŞTÜ — SAYI YAYILMAZ", ""]
        s += [f"* {x}" for x in d["yayin_engeli"]]
        s += ["", f"Bastırılan alanlar: `{'`, `'.join(d['bastirilan'])}` (ablasyon tablosu, tanı "
                  "sütunları ve işlem başına Δ TAMAMEN bastırıldı).", ""] + pk_satiri
        s += ["## Kimlik", ""] + _kimlik_satirlari(d)
        return "\n".join(s) + "\n"

    es = d["esikler"]
    k = d["kiyas"]
    sat = ["| kip | hüküm çifti | ort \\|Δ\\| (kendi) | düşüş (kendi) | **katkı var?** | "
           "ort \\|Δ\\| (ortak n={}) | düşüş (ortak) | katkı var (ortak)? | tüm çift ort \\|Δ\\| | "
           "düşüş (tüm) | iyileşen/kötüleşen | doğrulanmış ort \\|Δ\\| | çıkış nedeni eşleşme |"
           .format(len(k["ortak_kume"])),
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in k["tablo"]:
        e = r["cikis_neden_eslesme"]
        sat.append("| `{}` | {} | {} | {} | **{}** | {} | {} | {} | {} | {} | {}/{} | {} | "
                   "{}/{} ({}) |".format(
                       r["kod"], r["n_hukum_cifti"], _s(r["ort_mutlak_fark_r"]),
                       _s(r["dusus_kendi_kumesi"]), _s(r["katki_var_kendi"]),
                       _s(r["ort_mutlak_fark_r_ortak"]), _s(r["dusus_ortak_kume"]),
                       _s(r["katki_var_ortak"]), _s(r["tum_cift_ort_mutlak"]),
                       _s(r["tum_cift_dusus"]), r["n_iyilesen"], r["n_kotulesen"],
                       _s(r["dogrulanmis_ort_mutlak"]), e["eslesen"], e["n"], _s(e["oran"])))

    tani_sat = ["| sembol | gerçek R | türetilen risk mesafesi | giriş−stop | oran (giriş) | "
                "tetik−stop | oran (tetik) | Δ payda | not |",
                "|---|---|---|---|---|---|---|---|---|"]
    for t in d["tani_d"]:
        tani_sat.append("| {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            t["ticker"], _s(t["gercek_r"], 3), _s(t["turetilen_risk_mesafesi"], 4),
            _s(t["mesafe_giris_stop"], 4), _s(t["oran_giris"], 3),
            _s(t["mesafe_tetik_stop"], 4), _s(t["oran_tetik"], 3),
            _s(t["delta_payda"], 4), t["turetilemedi"] or "—"))

    ayr = ["| sembol | Δ toplam | Δ payda | Δ fiyat | özdeşlik |", "|---|---|---|---|---|"]
    for a in d["ayrisma"]:
        ayr.append(f"| {a['ticker']} | {_s(a['fark_r'])} | {_s(a['delta_payda'])} | "
                   f"{_s(a['delta_fiyat'])} | {_s(a['ozdeslik_tuttu'])} |")

    ib = ["| sembol | plan | " + " | ".join(f"`{c}` Δ" for c in d["istenen_ablasyonlar"]) + " |",
          "|---|---|" + "---|" * len(d["istenen_ablasyonlar"])]
    for r in k["islem_basina"]:
        hucre = []
        for kod in d["istenen_ablasyonlar"]:
            c = r["kipler"].get(kod) or {}
            hucre.append(_s(c.get("fark_r")) if c.get("fark_r") is not None
                         else (c.get("olculemedi") or "—"))
        ib.append(f"| {r['ticker']} | `{r['plan_id']}` | " + " | ".join(hucre) + " |")

    kf = d["kalan_fark_sinifi"]
    bk = kf["bar_kaynagi_bps"]
    if bk["n"]:
        bps_sat = ["| sembol | plan | seans | CSV açılışı | E2 resmî açılış | Δ (bps) | ret |",
                   "|---|---|---|---|---|---|---|"]
        for r in bk["sembol_bazli"]:
            bps_sat.append(f"| {r['ticker']} | `{r['plan_id']}` | {r['seans']} | "
                           f"{_s(r['acilis'], 4)} | {_s(r['resmi_acilis'], 4)} | "
                           f"{_s(r['bps'], 1)} | {r['red'] or '—'} |")
        bps_sat += ["", f"- n={bk['n']} · ort {_s(bk['ort_bps'], 1)} bps · medyan "
                    f"{_s(bk['medyan_bps'], 1)} bps · ort |·| {_s(bk['ort_mutlak_bps'], 1)} bps "
                    "— ORTALAMA İLE MEDYAN BİRLİKTE: tek aykırı sembol ortalamayı taşır, "
                    "medyanı taşımaz."]
        if bk["olculemeyen_n"]:
            bps_sat.append(f"- ÖLÇÜLEMEYEN {bk['olculemeyen_n']} satır (0 SAYILMADI): "
                           + " · ".join(bk["olculemeyen_nedenler"]))
    else:
        bps_sat = [f"- ÖLÇÜLEMEDİ — {bk['olculemedi_neden']}"]
    par = d["parite"]
    kun = d["enjeksiyon_kunyesi"]
    return "\n".join(bas + pk_satiri + [
        "## Ablasyon tablosu — İKİ PAYDA", "", *sat, "",
        f"- eşik (kart `ort_fark_r_ust` = motor `golge_icra.FARK_R_UST`): "
        f"{_s(es['ort_fark_r_ust'])}R · katkı eşiği (`ablasyon_dusus_alt_r`): "
        f"{_s(es['ablasyon_dusus_alt_r'])}R · ADIM-0 kapısı (`n_hukum_cifti_alt`): "
        f"{es['n_hukum_cifti_alt']} · kaynak `{es['kaynak']}`",
        "- **kendi kümesi** kartın eşiğinin uygulandığı istatistiktir; **ortak küme** tabanla "
        "aynı plan kimliklerini kullanır. İkisi ayrışıyorsa düşüşün bir kısmı PAYDANIN "
        "değişmesindendir (ör. A'da tetiği gelmeyen plan hüküm kümesine girer) — tek sayı "
        "basmak bu körlüğü gizlerdi.",
        "- **tüm çift** sütunu payı ÖLÇÜLEMEYEN çiftleri de içerir (TANI, hükme GİRMEZ): bir "
        "ablasyonun hüküm kümesi DIŞINDAKİ etkisi ancak orada görünür. **iyileşen/kötüleşen** "
        "ortak kümede |Δ|'si düşen/artan işlem sayısıdır — ortalama, eşit ve zıt iki değişimi "
        "tek sayıda yutabilir.",
        "",
        "## ADAY D — risk paydası tanısı (K harcamaz)", "", *tani_sat, "",
        "- türetilen risk mesafesi = `|pnl_dollars / (r_multiple × qty)|`; iki mesafe de "
        "basılır (kartın notu `giriş−stop`, brief'in formülü `tetik−stop` der).",
        "",
        f"## Farkın toplamsal ayrışması (kip `{d['ayrisma_kipi']}`)", "", *ayr, "",
        f"- ortalama |Δ payda| {_s(kf['ort_mutlak_delta_payda'])} · ortalama |Δ fiyat| "
        f"{_s(kf['ort_mutlak_delta_fiyat'])} · n={kf['n']}",
        f"- birleşik ort |Δ| {_s(kf['birlesik_ort_mutlak'])} · eşiğin altına indi: "
        f"{_s(kf['esigin_altina_indi'])}",
        "",
        "## Kalan fark sınıfı — kanıtla", "",
        *[f"- **{x['sinif']}** — kanıt: {x['kanit']}"
          + (f" · **`{x['paylasilan_sayi']}` sayısını «{x['paylastigi_sinif']}» ile PAYLAŞIR** — "
             f"ayrışan pay: {_s(x['ayrisan_pay_r'])} ({x['ayrisan_pay_neden']})"
             if x.get("paylasilan_sayi") else "")
          for x in kf["siniflar"]],
        "",
        "### Bar kaynağı ayrışması — `acilis` (donmuş CSV) ↔ `e2.resmi_acilis` (gerçek yol)", "",
        *bps_sat,
        "",
        "## İşlem başına Δ", "", *ib, "",
        "## C paritesinin ölçümü", "",
        f"- keşif kolu: `n_exploration={par['kesif_kolu']['n_exploration']}` · "
        f"parite={par['kesif_kolu']['parite']} — {par['kesif_kolu']['hukum']}",
        f"- `scale_out`: frac={par['scale_out']['frac_taban']} · rejim hücreleri "
        f"{par['scale_out']['frac_rejim']} · parite={par['scale_out']['parite']} — "
        f"{par['scale_out']['hukum']}",
        f"- `pivot`: ölçüldü={par['pivot']['olculdu']} — {par['pivot']['neden'] or 'parite'}",
        f"- çıkış icra fiyatı: parite={par['cikis_icra_fiyati']['parite']} "
        f"({par['cikis_icra_fiyati']['beyan']})",
        f"- zincir sırası: parite={par['zincir_sirasi']['parite']} "
        f"({par['zincir_sirasi']['beyan']})",
        "",
        "## Enjeksiyon künyesi — hangi yüzey, hangi sembol", "",
        *[f"- `{kod}`: yüzeyler {a['sarmalanan_yuzeyler'] or '—'} · A izi "
          f"{[x['ticker'] for x in a['a_izi']] or '—'} · B enjeksiyonu {a['b_enjeksiyon_n']} "
          f"(limit değişen {a['b_limit_degisen_n']}) · C `scale_out` çağrısı "
          f"{a['c_scale_out_cagrisi']} (ateşleyen {a['c_scale_out_atesledi']})"
          for kod, a in kun.items()],
        f"- A'nın ÜZERİNE YAZDIĞI pozisyon alanları: `{'`, `'.join(A_YAZILAN_ALANLAR)}` "
        "(`trail_stop` DEĞİŞMEZ — üretimde de `Position.trail_stop = stop`)",
        "",
        "## Kimlik", "", *_kimlik_satirlari(d),
        "",
        "## Beyanlı sapmalar (taban koşumundan devralınan)", "",
        *[f"- {x}" for x in d["sapmalar"]],
        "",
        "## PK (2) kıyasından dışlanan META alanlar (hiçbiri SAYI değildir)", "",
        *[f"- `{m['alan']}`: `{m['donmus']}` → `{m['yeniden']}` — {m['gerekce']}"
          for m in d["pk"]["taban"]["meta_farklari"]],
        "",
    ]) + "\n"


def _kimlik_satirlari(d: dict) -> list:
    p, b = d["parametre_kaynagi"], d["bar_kaynagi"]
    return [
        f"- **donmuş girdi**: `{d['girdi'].get('dosya_goreli')}` sha256 "
        f"`{d['girdi']['sha256'][:16]}…` · A1 çekimi {d['girdi_cekim_utc']}",
        f"- **donmuş parametreler** (`{p['sinif']}`): `{p.get('yol_goreli')}` "
        f"strategy sha `{p['sha256']['strategy.yaml'][:16]}…` · `strategy_version` "
        f"{p['strategy_version']} · kimlik kapısı: {p['kimlik_kapisi']}",
        f"- **bar kaynağı**: `{b.get('dizin_goreli')}` (`bar_kaynak=\"{b['etiket']}\"`) — "
        f"sembol son seansı {b['son_seans']['sembol_son_seans_min']}…"
        f"{b['son_seans']['sembol_son_seans_max']}",
        f"- **motor**: `{d['motor_yolu']}` · seans tavanı {d['seans_tavani']} · "
        f"rejim kapısı: `{d['rejim_kapisi']['kullanilan']}`",
        f"- **üretim kaynağı (sha256, koşum sonrası)**: "
        + " · ".join(f"`{a}` {h[:12]}…" for a, h in d["kaynak_dokunulmadi"]["sonra"].items()),
    ]


# ==================================================================================================
# KOMUT SATIRI
# ==================================================================================================
def main(argv: list[str] | None = None) -> int:
    """KOMUT SATIRI sözleşmesi. Çıkış: 0 rapor yazıldı · 2 PK düştü · 1 hata (ön şart tutmadı)."""
    ap = argparse.ArgumentParser(
        description=f"{KART} — gölge↔gerçek ayrışmanın ablasyonla teşhisi (A/B/C + birleşik)")
    ap.add_argument("--girdi", type=pathlib.Path, default=None,
                    help="donmuş A1 artefaktı — VARSAYILAN PK (2)'nin git-izli kopyası")
    ap.add_argument("--bars-dizin", type=pathlib.Path, default=None,
                    help="bar önbelleği (SALT-OKUNUR) — VARSAYILAN PK (2)'nin donmuş kopyası")
    ap.add_argument("--params", type=pathlib.Path, default=None,
                    help="donmuş parametre DİZİNİ — VARSAYILAN PK (2)'nin canlı v5 kopyası")
    ap.add_argument("--state-dizin", required=True, type=pathlib.Path,
                    help="GEÇİCİ state kökü — ablasyon başına ALT DİZİN (canlı state YASAK)")
    ap.add_argument("--cikti-dizin", required=True, type=pathlib.Path,
                    help="sonuc_<utc>.json + rapor_<utc>.md buraya yazılır")
    ap.add_argument("--ablasyon", nargs="+", choices=list(ABLASYONLAR), default=[TABAN_KODU],
                    help=f"koşulacak kipler ({' · '.join(ABLASYONLAR)}); taban DAİMA koşar")
    ap.add_argument("--taban-sonuc", type=pathlib.Path, default=None,
                    help="PK (2) kıyas artefaktı — VARSAYILAN EDG-088'in donmuş sonucu")
    ap.add_argument("--seans-tavani", type=int, default=None,
                    help=f"gölge takibinin beyanlı üst sınırı (varsayılan {pk2.SEANS_TAVANI})")
    a = ap.parse_args(argv)

    try:
        sonuc = kos(a.girdi or girdi_varsayilan(), a.bars_dizin or bars_varsayilan(),
                    a.params or params_varsayilan(), a.state_dizin, tuple(a.ablasyon),
                    a.taban_sonuc or taban_sonuc_varsayilan(), a.seans_tavani)
    except Blok as e:
        print(f"BLOKLANDI: {e}", file=sys.stderr)
        return 1

    a.cikti_dizin.mkdir(parents=True, exist_ok=True)
    damga = sonuc["olculdu_utc"].replace(":", "").replace("-", "")
    (a.cikti_dizin / f"sonuc_{damga}.json").write_text(
        json.dumps(sonuc, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    (a.cikti_dizin / f"rapor_{damga}.md").write_text(rapor_metni(sonuc), encoding="utf-8")
    if sonuc["yayin_engeli"]:
        print(f"{KART}: PK DÜŞTÜ — SAYI YAYILMAZ · {sonuc['yayin_engeli'][0]}")
    else:
        tablo = {r["kod"]: r["dusus_kendi_kumesi"] for r in sonuc["kiyas"]["tablo"]}
        print(f"{KART}: ölçüldü · kipler {sonuc['istenen_ablasyonlar']} · düşüş (kendi kümesi) "
              f"{tablo} · birleşik ort |Δ| "
              f"{_s(sonuc['kalan_fark_sinifi']['birlesik_ort_mutlak'])}R "
              f"(eşik {_s(sonuc['esikler']['ort_fark_r_ust'])}R)")
    print(f"çıktı: {a.cikti_dizin}/sonuc_{damga}.json + rapor_{damga}.md")
    return 2 if sonuc["yayin_engeli"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
