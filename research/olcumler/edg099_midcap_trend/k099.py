"""EDG-2026-099 · ANA ÖLÇÜM — S&P 400 PIT (as-of) KOHORTUNDA UZUN-UFUK TREND KOLU.

Kart: research/cards/EDG-2026-099-midcap-pit-trend-kolu.yaml (`adim_olcum`).
KART DIŞINA ÖLÇÜM YOK; KARTA DOKUNULMAZ; eşik sonradan DEĞİŞMEZ. HÜKÜM YOK — `hukum` alanı
sabit "YOK — Rol-1" (CLAUDE.md §3, §5).

TASARIM: EDG-2026-009'un C/D hücreleri, EVREN S&P 400 PIT KOHORTU. EDG-009'un iki hücresi
(`research/olcumler/trend_rafine/RAPOR.md` §1a/§1b) burada AYNEN yeniden kurulur:
    D = `aylik_rebalans_duraksiz` — ay-sonunda üst-N momentum listesi YENİDEN kurulur; listeden
        düşen pozisyon ertesi seans açılışında satılır (duraksız rotasyon),
    C = `chandelier_mevcut`       — pozisyon YALNIZ chandelier (tepe − K×ATR22), üyelik kaybı ya
        da fiyatsızlık ile kapanır; boşalan slot BİR SONRAKİ ay-sonunda dolar (incumbent akış).
EDG-009'un ölçüm şasisi (engine.py/load.py) DEPODA YOKTUR — yalnız RAPOR/sonuc artefaktları
vardır (kart "KÜNYE BOŞLUĞU" notu). Bu dosya o şasinin YERİNE GEÇMEZ: EDG-009'un sayılarını
yeniden üretmeyi İDDİA ETMEZ (pencere, evren ve bar tabanı farklıdır); PIT kolunu yeniden
üretilebilir kılan YENİ bir şasidir ve sabitleri canlı gölge-kitaptan (tek kaynak) okur.

İTHAL EDİLİR, KOPYALANMAZ (tek-kaynak yasası, CLAUDE.md §4):
  * meridian/trend_shadow.py — sinyal SABİTLERİ (MOM_LOOKBACK, N_SLOTS, FRICTION_BPS, ATR_LEN,
    CHANDELIER_K, DELIST_GRACE, INIT_EQUITY), ay-sonu takvim kapısı (`ay_sonu_mu`, fail-closed),
    panel dilimi (`_dilim` + `dolduruldu_n` köken bayrağı), ATR22 (`_atr`), son-kapanış/bayatlık
    yardımcıları (`_son_kapanis`, `_bayat_mi`), sembol normalizasyonu (`_norm`).
    YALNIZ SABİT VE SAF FONKSİYON İTHAL EDİLİR: `run_cycle`, `_kaydet`, `ozet`, `_uygunluk`
    ÇAĞRILMAZ — ilk ikisi canlı gölge-deftere YAZAR, sonuncusu `obs.warn` yüzeyi taşır.
  * research/olcumler/edg093_midcap_pit/k093.py — `ithal_yuzeyi` (wp2 emsal altyapısı + config
    yönlendirmesi), `ithal_yan_etkisini_geri_al`, `etkin_satirlar`, `uyelik_haritasi`,
    `belirsiz_isimler`, `barlari_yukle`, `yanlilik_gostergesi`, `kullanim_hatasi`.
    Kohort/bar/üyelik sözleşmesi EDG-093'ündür; ikinci bir kopya sessizce ayrışırdı.
  * research/olcumler/edg093_midcap_pit/ortak.py (Parti-1, k093 üzerinden `p1`) — kohort csv
    okuma/as-of çapası, bar dosya adı, kart penceresi.
  * research/olcumler/wp2_olcum/ortak.py (k093 üzerinden `O`) — `BAR_MIN_UZUNLUK`, `BOOT`,
    `json_yaz`.
BU DOSYADA SİNYAL SABİTİ YENİDEN YAZILMAZ ve çivi bunu kaynak metinden ölçer (v497 §T10).

PIT — SIFIR TOLERANS (CLAUDE.md §4):
  * üyelik AS-OF okunur (`k093.uyelik_haritasi`, `asof` kipi): o gün üye OLMAYAN isim sepete
    giremez, üyelikten çıkan isim BİR SONRAKİ ay-sonunda satılır;
  * karar t ay-sonu KAPANIŞI, icra t+1 seans AÇILIŞI — karar gününün kapanışı icra fiyatını
    BELİRLEMEZ (bakma-ileri çivisi v497 §T3);
  * ay-sonu takvimi XNYS'tir ve `trend_shadow.ay_sonu_mu` FAIL-CLOSED'dır — takvim yoksa
    "ay-sonu mu" sorusu CEVAPSIZDIR ve koşum kullanım hatasıyla durur; ay-sonu KOHORT
    BARLARINDAN TÜRETİLMEZ (barlardan türetmek, veri boşluğunu takvim gerçeği sanmaktır).

YAZIM — TEK YER `--cikti` (Yasa 6, okuyanı aşağıda):
  * `<cikti>/sonuc_099_<damga>.json` → okuyan: Rol-1 (hüküm + K defteri) ve RAPOR üreteci;
  * `<cikti>/RAPOR_099_<damga>.md`   → okuyan: Rol-1 / operatör masası;
  * `<cikti>/_state/`                → `meridian.config.STATE` BURAYA çevrilir (k093'ün
    `ithal_yuzeyi`si yapar); canlı boru hattının `obs` yazımları CANLI deftere düşmez.
Repo `state/`ine yazım YOK. Ağa ÇIKILMAZ. Alt süreç YOKTUR. Bekleme döngüsü YOKTUR.

KOMUT SATIRI (sözleşme burasıdır, `main()` değil — CLAUDE.md §1):
    cd <depo kökü> && .venv/bin/python research/olcumler/edg099_midcap_trend/k099.py \\
        --repo <kök> --kohort <sp400_uyelik_tarihi.csv> --bars-dir <bars/> \\
        --kart <EDG-2026-099 yaml> --cikti <dizin> \\
        [--baslangic YYYY-MM-DD] [--bitis YYYY-MM-DD] [--belirsiz dahil|haric|ikisi] \\
        [--esleme <sp400_elle_esleme.yaml>] [--kapsama <kapsama_haritasi.json>] \\
        [--pk-kohort <sp500_uyelik_tarihi.csv> --pk-bars-dir <state/bars>] [--tohum N]
Çıkış kodu: 0 = sonuç yazıldı · 2 = kullanım hatası (eksik/bozuk girdi, kart okunamadı,
eşik bulunamadı, XNYS takvimi yok). `--kart` ZORUNLUDUR: eşikler KARTTAN okunur, koda
GÖMÜLMEZ ve UYDURULMAZ — kartsız koşum eşik icat etmek olurdu.

MODÜL DÜZEYİ TEMİZDİR: argparse `main()` içinde kurulur, G/Ç yoktur, `meridian` ithal EDİLMEZ
(ithal `ithal_yuzeyi` içindedir) — bu dosyayı ithal etmek bir koşum TETİKLEMEZ ve çiviler bu
yüzden saf fonksiyonları DOĞRUDAN çağırabilir.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import pathlib
import sys

KART_ID = "EDG-2026-099"
KART_ADI = "EDG-2026-099-midcap-pit-trend-kolu.yaml"
AILE = "pit_midcap_ust_sinir"
HUKUM = "YOK — Rol-1"

#: `--belirsiz` sözlüğü — k093 ile AYNI lafız. `dahil` = kohort defteri AYNEN (BİRİNCİL),
#: `haric` = belirsiz isimler tüm günlerden düşürülür (DUYARLILIK), `ikisi` = ikisi de koşar.
BELIRSIZ_KIPLERI = ("dahil", "haric", "ikisi")
BIRINCIL_KIP = "dahil"

#: Kart `k_registry` iki deneme kaydeder: D ve C. Sıra RAPOR'da da budur.
HUCRELER = ("D", "C")

#: Blok-bootstrap blok uzunluğu AY cinsinden — kart `adim_olcum` lafzı ("12 aylık blok").
#: Bu bir SİNYAL sabiti DEĞİLDİR (trend_shadow'da karşılığı yoktur); tekrar sayısı ise wp2
#: `ortak.BOOT`tan İTHAL edilir, burada yazılmaz.
BOOTSTRAP_BLOK_AY = 12

#: Newey-West gecikme sayısı — kart `adim_olcum` lafzı ("Newey-West 3 gecikme").
NW_GECIKME = 3

#: Çıta kimlikleri — EDG-009 `sonuc.json` sözleşmesiyle AYNI ADLAR (`cita_esli` / `cita_taban`).
#: Ad seçimi bilinçlidir: iki ölçümün tabloları yan yana okunabilsin.
CITA_ESLI = "cita_esli"
CITA_TABAN = "cita_taban"

#: Çıkış sebepleri — RAPOR'un çıkış-kanalı tablosunun sözlüğü. Sebep UYDURULMAZ: her kapanış
#: BU kümeden bir etiket taşır.
CIKIS_SEBEPLERI = ("chandelier", "rotate", "uyelik", "no_data", "hedef_disi")


# =================================================================================================
# 0. KULLANIM HATASI / KÜÇÜK YARDIMCILAR
# =================================================================================================
def kullanim_hatasi(mesaj: str) -> None:
    """Kullanım hatası = çıkış 2 (argparse ile AYNI kod); neden stderr'e ADIYLA yazılır.

    k093'ün aynı adlı yardımcısı İTHALDEN SONRA erişilebilir; bu dosya ithalden ÖNCE de
    (argparse doğrulaması, kart okuma) çıkış 2 üretebilmeli — o yüzden bootstrap kopyası
    BURADADIR ve gövdesi üç satırdır. Davranış eşitliği `test_edg099_midcap_trend_v497`
    tarafından ölçülür (iki yol da çıkış 2 verir)."""
    print(f"KULLANIM HATASI: {mesaj}", file=sys.stderr)
    raise SystemExit(2)


def damga_uret() -> str:
    """UTC damgası — saat TAHMİNLE değil saatten okunur (hafıza: saat-etiketi ölçülür)."""
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def _sha_veya_neden(p) -> tuple[str | None, str | None]:
    """(sha256, neden) — dosya yoksa sha UYDURULMAZ, neden ADIYLA döner."""
    if p is None:
        return None, "yol verilmedi"
    yol = pathlib.Path(p)
    if not yol.exists():
        return None, f"dosya yok: {yol}"
    return _sha256(yol), None


def _nan(x) -> bool:
    """Değer ÖLÇÜLEMEZ mi? (None ya da NaN). Sıfır ÖLÇÜLMÜŞTÜR — bu ayrım uydurma yasağıdır."""
    return x is None or (isinstance(x, float) and math.isnan(x))


def _sayi(x):
    """JSON'a girecek sayı — NaN/Inf JSON'da GEÇERSİZDİR ve sessizce `NaN` yazılırsa okuyucu
    tarafında ayrıştırma hatası doğar. Ölçülemeyen değer None'dır (uydurma yasağı)."""
    if x is None:
        return None
    try:
        f = float(x)
    except (TypeError, ValueError):  # sessiz-yutma DEĞİL: sayıya çevrilemeyen değer ÖLÇÜLEMEDİ demektir, None döner ve okuyucu farkı görür
        return None
    return None if (math.isnan(f) or math.isinf(f)) else f


# =================================================================================================
# 1. İTHAL YÜZEYİ — k093 + trend_shadow KAYNAKTAN yüklenir (v334: ham `exec_module` YASAK)
# =================================================================================================
def _yukleyici(repo: pathlib.Path):
    """`ops.sasi_yukleyici.kaynaktan_yukle` — ham `exec_module` YASAK (v334 §C).

    BOOTSTRAP ZORUNLULUĞU: k093'ün kendi `_yukleyici`si k093 YÜKLENDİKTEN SONRA erişilebilir,
    ama k093'ü yüklemek için yükleyici ZATEN gerekir. Bu dört satır o yumurta-tavuk halkasıdır
    ve başka hiçbir şey yapmaz.

    `sys.path` eki BİLİNÇLİDİR: bu betik DOĞRUDAN koşulur, o zaman `sys.path[0]` BU dizindir ve
    `ops.` ön eki editable-install `.pth`i üzerinden BAŞKA BİR CHECKOUT'a düşerdi (hafıza:
    worktree-pythonpath-tuzagi). Kök AÇIK verilir ve çözülen yol künyeye yazılır."""
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    from ops.sasi_yukleyici import kaynaktan_yukle
    return kaynaktan_yukle


def ithal_yuzeyi(repo: pathlib.Path, cikti: pathlib.Path, bars_dir: pathlib.Path) -> dict:
    """k093 + wp2 emsal altyapısı + `meridian.trend_shadow` — hepsi `--repo`dan.

    SIRA ZORUNLUDUR: `k093.ithal_yuzeyi` ÖNCE koşar; `meridian.config.STATE` ancak ondan sonra
    çıktı dizinine bakar. `trend_shadow` ithali BUNDAN SONRADIR — modül `obs`/`store`u ithal
    eder ve o modüller yolu ÇAĞRI ANINDA okusa da, sıranın tersine dönmesi ilk yazımın canlı
    deftere düşmesi için yeterli olurdu (CLAUDE.md §2: "pytest dışı koşum obs'a ulaşırsa canlı
    yerel deftere YAZAR")."""
    yukle = _yukleyici(repo)
    k093_yol = repo / "research" / "olcumler" / "edg093_midcap_pit" / "k093.py"
    if not k093_yol.exists():
        kullanim_hatasi(f"EDG-093 boru hattı bulunamadı: {k093_yol} (--repo yanlış olabilir)")
    K = yukle(k093_yol, "k093_edg099")
    yuzey = K.ithal_yuzeyi(repo, cikti, bars_dir, None)

    from meridian import trend_shadow as ts
    yuzey["K"] = K
    yuzey["ts"] = ts
    yuzey["cozulen_yollar"]["k093"] = str(k093_yol.resolve())
    yuzey["cozulen_yollar"]["trend_shadow"] = str(pathlib.Path(ts.__file__).resolve())
    return yuzey


def sabitler_kaydi(ts) -> dict:
    """Sinyal sabitleri — `meridian.trend_shadow`DAN OKUNUR, burada yazılmaz.

    AYRIŞMA ÇİVİSİ (v497 §T1) bu sözlüğü canlı modülle karşılaştırır: bir gün gölge-kitabın
    sabiti değişirse ölçüm sessizce eski sabitle koşmaz, çivi öter."""
    return {
        "kaynak": "meridian/trend_shadow.py — SABİTLER İTHAL EDİLİR, bu dosyada yeniden "
                  "YAZILMAZ; ayrışma çivisi tests/test_edg099_midcap_trend_v497.py",
        "MOM_LOOKBACK": int(ts.MOM_LOOKBACK), "N_SLOTS": int(ts.N_SLOTS),
        "FRICTION_BPS": float(ts.FRICTION_BPS), "ATR_LEN": int(ts.ATR_LEN),
        "CHANDELIER_K": float(ts.CHANDELIER_K), "DELIST_GRACE": int(ts.DELIST_GRACE),
        "INIT_EQUITY": float(ts.INIT_EQUITY),
        "momentum_tanimi": "12-1: P(ay-sonu t-1) / P(ay-sonu t-12) − 1 (şasinin ay-sonu tanımı)",
    }


# =================================================================================================
# 2. KART — EŞİKLER VE KILL-LIST KARTTAN OKUNUR, KODA GÖMÜLMEZ
# =================================================================================================
#: Kartın `esikler` bloğundan okunan SAYISAL eşikler. Metin eşik (`pk1_large_cap`) AYRI durur:
#: sayı değildir, hüküm lafzıdır ve karşılaştırmaya girmez.
SAYISAL_ESIKLER = ("fazla_yillik_alt", "t_alt", "ay_sonu_aday_alt", "olculemeyen_ust_oran")


def kart_oku(kart_yolu: pathlib.Path) -> dict:
    """Kart YAML'i → {esikler, kill_list, pk1_lafzi, veri_penceresi…}. EKSİK EŞİK = ÇIKIŞ 2.

    Eşik SONRADAN DEĞİŞMEZ ve UYDURULMAZ (CLAUDE.md §5): kart okunamıyorsa ya da bir sayısal
    eşik yoksa koşum DURUR. Sessiz varsayılan, ön-kayıtlı eşiği kodun icat ettiği bir sayıyla
    değiştirmek olurdu."""
    yol = pathlib.Path(kart_yolu)
    if not yol.exists():
        kullanim_hatasi(f"--kart dosyası yok: {yol} — eşikler KARTTAN okunur, UYDURULMAZ")
    try:
        import yaml
        govde = yaml.safe_load(yol.read_text(encoding="utf-8"))
    except (OSError, ImportError, ValueError) as e:
        # sessiz-yutma DEĞİL: kart okunamadı — eşik UYDURULMAZ, koşum çıkış 2 ile durur
        kullanim_hatasi(f"--kart okunamadı ({type(e).__name__}: {e}): {yol}")
    if not isinstance(govde, dict):
        kullanim_hatasi(f"--kart YAML sözlüğü değil: {yol}")
    esikler = govde.get("esikler")
    if not isinstance(esikler, dict):
        kullanim_hatasi(f"kartta `esikler` bloğu yok: {yol}")
    eksik = [a for a in SAYISAL_ESIKLER if a not in esikler]
    if eksik:
        kullanim_hatasi(f"kartta sayısal eşik(ler) YOK: {eksik} ({yol}) — eşik UYDURULMAZ")
    try:
        sayisal = {a: float(esikler[a]) for a in SAYISAL_ESIKLER}
    except (TypeError, ValueError) as e:
        # sessiz-yutma DEĞİL: eşik sayıya çevrilemiyorsa kart bozuktur, varsayılana DÜŞÜLMEZ
        kullanim_hatasi(f"kart eşiği sayı değil ({type(e).__name__}: {e}): {yol}")
    kill = govde.get("kill_list")
    if not isinstance(kill, list) or not kill:
        kullanim_hatasi(f"kartta `kill_list` yok ya da boş: {yol}")
    return {
        "yol": str(yol), "card_id": govde.get("card_id"), "family": govde.get("family"),
        "esikler_sayisal": sayisal,
        "pk1_lafzi": esikler.get("pk1_large_cap"),
        "kill_list": [str(x) for x in kill],
        "veri_penceresi": govde.get("veri_penceresi"),
        "k_registry": govde.get("k_registry"),
    }


# =================================================================================================
# 3. TAKVİM — XNYS AY-SONLARI (FAIL-CLOSED; KOHORT BARLARINDAN TÜRETİLMEZ)
# =================================================================================================
def seanslar(dat, baslangic: dt.date, bitis: dt.date) -> list[str]:
    """Pencere içindeki XNYS seansları (artan, ISO metin) — `adapters.data._sessions()` TEK
    KAYNAĞINDAN. Takvim yoksa boş liste döner ve ÇAĞIRAN fail-closed davranır."""
    ses = dat._sessions()
    if not ses:
        return []
    b, s = baslangic.isoformat(), bitis.isoformat()
    return sorted(g for g in ses if b <= g <= s)


def ay_sonlari(ts, gunler: list[str]) -> tuple[list[str], dict]:
    """(ay-sonu seansları, muhasebe) — `trend_shadow.ay_sonu_mu` ile, FAIL-CLOSED.

    Ay-sonu KOHORT BARLARINDAN TÜRETİLMEZ: bir ayın son seansında kohortun hiçbir isminin barı
    olmayabilir ve o ay sessizce kaybolurdu. Takvimin cevap VEREMEDİĞİ gün (`None`) sayılır ve
    muhasebeye yazılır; hiç cevap yoksa çağıran koşumu durdurur."""
    sonlar, cevapsiz = [], []
    for g in gunler:
        cevap = ts.ay_sonu_mu(g)
        if cevap is None:
            cevapsiz.append(g)
            continue
        if cevap:
            sonlar.append(g)
    return sonlar, {"ay_sonu_n": len(sonlar), "cevapsiz_gun_n": len(cevapsiz),
                    "cevapsiz_ornek": cevapsiz[:10],
                    "kaynak": "meridian.trend_shadow.ay_sonu_mu (XNYS, fail-closed)"}


# =================================================================================================
# 4. SİNYAL — 12-1 MOMENTUM SIRALAMASI VE ÜST-N SEÇİMİ (SAF)
# =================================================================================================
def atr_degeri(atr: dict, sembol: str, gun):
    """ATR22'nin `gun`deki değeri, ya da ÖLÇÜLEMEDİYSE None (ısınma dolmadıysa NaN gelir)."""
    seri = atr.get(sembol)
    if seri is None or gun not in seri.index:
        return None
    val = seri.at[gun]
    return None if _nan(val) else float(val)


def momentum_satirlari(dilim: dict, adaylar, a1, a12, rd, atr: dict, per: dict) -> list:
    """[(sembol, 12-1 momentum)] — KART TANIMI: P(ay-sonu t-1) / P(ay-sonu t-12) − 1.

    Aday olabilmenin şartları (şasinin ay-sonu karar bölümüyle aynı sıra):
      * dilim karesi VAR ve üç çapa (t-12, t-1, t) İNDEKSTE — 13 ay-sonu kapanışı şartının
        ölçülebilir karşılığı budur: `_dilim` ömür İÇİNDE ffill ettiği için t-12'de kapanışı
        olan bir seri aradaki her ay-sonunda da kapanış taşır, ömrün DIŞI NaN kalır;
      * üç kapanış da ölçülmüş (NaN değil) ve payda pozitif;
      * `rd` gününde GERÇEK bar var (`per`) — ileri-doldurulmuş bir hücreyle karar alınmaz;
      * ATR22 ölçülmüş (ısınma dolmuş).
    Eleme sebebi UYDURULMAZ: ölçülemeyen isim listeye GİRMEZ ve `aday_n` bunu sayar.

    SIRALAMA DETERMİNİSTİKTİR: birincil anahtar momentum (azalan), ikincil anahtar SEMBOL
    (artan). Gölge-kitap yalnız momentuma göre sıralar ve eşitlikte evren sırasına düşer; bir
    ÖLÇÜM'de o sıra girdi dosyalarının okunma düzenine bağlı olurdu — yeniden üretilebilirlik
    ikinci anahtarı zorunlu kılar (fark yalnız birebir eşit momentumlarda görünür)."""
    rows = []
    for t in sorted(adaylar):
        r = dilim.get(t)
        if r is None:
            continue
        if not (a1 in r.index and a12 in r.index and rd in r.index):
            continue
        p1, p12, pnow = r.at[a1, "close"], r.at[a12, "close"], r.at[rd, "close"]
        if _nan(p1) or _nan(p12) or _nan(pnow):
            continue
        if float(p12) <= 0:
            continue
        df = per.get(t)
        if df is None or rd not in df.index:
            continue
        if atr_degeri(atr, t, rd) is None:
            continue
        rows.append((t, float(p1) / float(p12) - 1.0))
    rows.sort(key=lambda x: (-x[1], x[0]))
    return rows


def ust_n(rows, n: int) -> list:
    """Sıralı momentum satırlarının ilk `n` sembolü. `n <= 0` → boş liste (slot yok)."""
    return [t for t, _ in rows[:max(int(n), 0)]]


# =================================================================================================
# 5. İCRA MOTORU — KARAR t KAPANIŞI, İCRA t+1 AÇILIŞI (SAF)
# =================================================================================================
def icra_fiyati(ts, per: dict, sembol: str, xd, rd):
    """İCRA FİYATI: `xd` seansının AÇILIŞI; yoksa `rd` gününün SON BİLİNEN KAPANIŞI (şasi yedeği).

    BAKMA-İLERİ ÇİVİSİNİN HEDEFİ (v497 §T3): karar günü `rd`nin KAPANIŞI bu fiyatı BELİRLEMEZ —
    yalnız açılış hiç yoksa (sembolün o seansta barı yok) yedek olarak devreye girer. Fiyat
    UYDURULMAZ: her iki hâlde de kaynak gerçek bardır, hiçbiri yoksa None döner ve çağıran
    işlemi YAPMAZ."""
    df = per.get(sembol)
    if df is not None and xd in df.index:
        p = df.at[xd, "open"]
        if not _nan(p) and float(p) > 0:
            return float(p)
    px, _ = ts._son_kapanis(per.get(sembol), rd)
    return px


def yeni_durum(sermaye: float) -> dict:
    """Boş portföy durumu. `equity` GÜNLÜK M2M eğrisidir; `kapanan` işlem defteri."""
    return {"cash": float(sermaye), "pozisyon": {}, "equity": {}, "equity_sira": [],
            "kapanan": [], "sayac": {"giris": 0, "cikis": {}, "friksiyon": 0.0,
                                     "islem_bacagi": 0, "fiyatsiz_cikis": 0,
                                     "fiyatsiz_giris": 0}}


def _isaretle(durum: dict, s, per: dict) -> None:
    """GÜNLÜK M2M + chandelier tepe takibi (şasinin `_isaretle` semantiği).

    Barı olmayan sembol SON BİLİNEN KAPANIŞLA işaretlenir (ffill) — ölçülemeyen bir fiyat
    uydurulmaz, taşınan fiyat ise `dolduruldu` sayacıyla ADIYLA sayılır."""
    v = durum["cash"]
    tasinan = 0
    for t, p in durum["pozisyon"].items():
        df = per.get(t)
        if df is not None and s in df.index:
            c, h = df.at[s, "close"], df.at[s, "high"]
            if not _nan(c):
                p["last_close"] = float(c)
            if not _nan(h):
                p["peak_high"] = max(float(p.get("peak_high") or 0.0), float(h))
        else:
            tasinan += 1
        lc = p.get("last_close")
        if lc:
            v += p["shares"] * lc
    g = str(s.date()) if hasattr(s, "date") else str(s)
    durum["equity"][g] = float(v)
    durum["equity_sira"].append({"date": g, "equity": round(float(v), 4),
                                 "dolduruldu": tasinan})


def _kapat(durum: dict, t: str, p0: dict, fiyat: float, xd, sebep: str, fee: float) -> None:
    """Bir pozisyonu KAPATIR ve işlem defterine ADIYLA yazar (sebep etiketiyle)."""
    gelir = p0["shares"] * fiyat
    durum["cash"] += gelir * (1 - fee)
    durum["sayac"]["friksiyon"] += gelir * fee
    durum["sayac"]["islem_bacagi"] += 1
    durum["sayac"]["cikis"][sebep] = int(durum["sayac"]["cikis"].get(sebep, 0)) + 1
    durum["kapanan"].append({
        "sym": t, "giris": p0["entry_date"], "cikis": str(xd.date()), "sebep": sebep,
        "giris_px": round(float(p0["entry_price"]), 6), "cikis_px": round(float(fiyat), 6),
        "getiri_pct": round((fiyat / p0["entry_price"] - 1.0) * 100.0, 4)})


def icra_et(ts, durum: dict, xd, bekleyen: dict, per: dict, fee_bps: float) -> None:
    """BEKLEYEN KARARIN İCRASI — `xd` seansının AÇILIŞINDA. Sıra: çıkışlar → satışlar → alışlar.

    İKİ AŞAMALI DENKLEŞTİRME (şasinin tek geçişli `_icra`sından BİLİNÇLİ AYRIM ve BEDELİ
    YAZILI): gölge-kitap tek geçişte gezer ve nakit yetmezse alımı KIRPAR — canlı bir defterde
    doğru davranıştır (emir sırası gerçektir). Bir ÖLÇÜMDE ise aynı kırpma, sepetin ağırlığını
    sembol sırasına bağlardı: aynı hücre, dosyaların okunma düzenine göre farklı sonuç verirdi.
    Burada ÖNCE tüm azaltmalar (satış), SONRA tüm artırmalar (alış) koşar; nakit kısıtı hâlâ
    gerçektir (alışlar mevcut nakde kırpılır) ama sıraya bağlı DEĞİLDİR. Kırpma SAYILIR.

    `hedef` None ise YALNIZ çıkışlar işlenir (günlük chandelier icrası) — denkleştirme YOK:
    her chandelier çıkışında bütün sepeti yeniden denkleştirmek, ay-sonu rebalans tanımını
    günlük rebalansa çevirirdi (kart D/C ayrımının kendisi kaybolurdu)."""
    fee = float(fee_bps) / 10_000.0
    rd = bekleyen["date"]
    pos = durum["pozisyon"]

    # ---- 1) ÇIKIŞLAR
    for t, sebep in bekleyen.get("cikislar") or []:
        p0 = pos.get(t)
        if p0 is None:
            continue
        p = icra_fiyati(ts, per, t, xd, rd)
        if p is None or p <= 0:
            # fiyatsız satış UYDURULMAZ — pozisyon durur, hâl SAYILIR (sessiz boşluk yok)
            durum["sayac"]["fiyatsiz_cikis"] += 1
            continue
        pos.pop(t, None)
        _kapat(durum, t, p0, p, xd, sebep, fee)

    hedef = bekleyen.get("hedef")
    if not hedef:
        return

    # ---- 1b) HEDEFTE YERİ OLMAYAN POZİSYON BİR ÇIKIŞTIR (savunma ağı, SESSİZ DEĞİL)
    # Ağırlığı sıfır olan bir isim "küçültülmüş" değil KAPATILMIŞtır ve işlem defterinde
    # sebebiyle durmalıdır. Normal akışta bu dal BOŞtur — D'nin `rotate`, C'nin
    # `uyelik`/`chandelier`, çıtaların `uyelik` çıkışları listeyi zaten kapatır. Dolduğu gün
    # `hedef_disi` sayacı onu ADIYLA sayar ve karar üreticisinde bir boşluk olduğunu söyler.
    for t in sorted(set(pos) - set(hedef)):
        p = icra_fiyati(ts, per, t, xd, rd)
        if p is None or p <= 0:
            durum["sayac"]["fiyatsiz_cikis"] += 1
            continue
        p0 = pos.pop(t)
        _kapat(durum, t, p0, p, xd, "hedef_disi", fee)

    px = {t: icra_fiyati(ts, per, t, xd, rd) for t in set(list(pos) + list(hedef))}
    eq = durum["cash"] + sum(p["shares"] * px[t] for t, p in pos.items() if px.get(t))
    hedef_lot = {}
    for t, w in hedef.items():
        p = px.get(t)
        hedef_lot[t] = (float(w) * eq / p) if (p and p > 0) else None

    # ---- 2) AZALTMALAR (satış) — nakit ÖNCE toplanır
    for t in sorted(pos):
        p = px.get(t)
        if not p or p <= 0:
            continue
        istenen = hedef_lot.get(t)
        if istenen is None:
            continue                        # fiyatsız hedef: lot ÖLÇÜLEMEDİ, uydurulmaz
        d = istenen - pos[t]["shares"]
        if d >= 0 or abs(d * p) < 1e-9:
            continue
        notional = abs(d) * p
        durum["cash"] += notional * (1 - fee)
        durum["sayac"]["friksiyon"] += notional * fee
        durum["sayac"]["islem_bacagi"] += 1
        pos[t]["shares"] += d

    # ---- 3) ARTIRMALAR (alış) — nakit kısıtı GERÇEK, kırpma SAYILIR
    for t in sorted(hedef):
        p = px.get(t)
        if not p or p <= 0:
            if t not in pos:
                durum["sayac"]["fiyatsiz_giris"] += 1
            continue
        istenen = hedef_lot.get(t)
        if istenen is None:
            continue
        mevcut = pos[t]["shares"] if t in pos else 0.0
        d = istenen - mevcut
        if d <= 0 or d * p < 1e-9:
            continue
        maliyet = d * p * (1 + fee)
        if maliyet > durum["cash"]:
            d = max(durum["cash"], 0.0) / (1 + fee) / p
            maliyet = d * p * (1 + fee)
        if d <= 0 or d * p < 1e-9:
            continue
        durum["cash"] -= maliyet
        durum["sayac"]["friksiyon"] += d * p * fee
        durum["sayac"]["islem_bacagi"] += 1
        if t in pos:
            pos[t]["shares"] += d
        else:
            pos[t] = {"shares": d, "entry_date": str(xd.date()), "entry_price": float(p),
                      "peak_high": float(p), "last_close": float(p)}
            durum["sayac"]["giris"] += 1


def simule(ts, master, per: dict, karar_fn, *, fee_bps: float, sermaye: float,
           gunluk_fn=None) -> dict:
    """GENEL İCRA MOTORU. Her seansta: bekleyen icra → M2M → karar (ay-sonu) / günlük kontrol.

    Karar ve icra AYRI SEANSLARDADIR — motor bunu YAPISAL olarak zorlar: `karar_fn` bir
    `bekleyen` döner, `bekleyen` ancak BİR SONRAKİ döngü turunda (ertesi seans) icra edilir.
    Bakma-ileri bu yüzden bir kontrol değil, bir VERİ AKIŞI kısıtıdır."""
    durum = yeni_durum(sermaye)
    bekleyen = None
    for s in master:
        if bekleyen is not None:
            icra_et(ts, durum, s, bekleyen, per, fee_bps)
            bekleyen = None
        _isaretle(durum, s, per)
        karar = karar_fn(s, durum)
        if karar is None and gunluk_fn is not None:
            karar = gunluk_fn(s, durum)
        if karar is not None:
            bekleyen = karar
    durum["sayac"]["friksiyon"] = round(float(durum["sayac"]["friksiyon"]), 4)
    return durum


# =================================================================================================
# 6. KARAR ÜRETİCİLERİ — D / C HÜCRELERİ VE İKİ ÇITA
# =================================================================================================
def _zorunlu_cikislar(ts, durum: dict, rd, per: dict, uyeler, mpos: dict) -> list:
    """Ay-sonunda HER hücrede geçerli zorunlu çıkışlar: fiyatsızlık/bayatlık ve ÜYELİK KAYBI.

    ÜYELİK AS-OF'TUR (PIT): `rd` gününde üye OLMAYAN bir isim tutulamaz — kart lafzı
    "üyelikten çıkan isim bir sonraki ay-sonunda satılır". Satış icrası ertesi seans
    açılışıdır; yani "bir sonraki ay-sonunda karar, ertesi açılışta icra"."""
    out = []
    for t in sorted(durum["pozisyon"]):
        px, bar_t = ts._son_kapanis(per.get(t), rd)
        if px is None or (bar_t is not None and ts._bayat_mi(bar_t, rd, mpos)):
            out.append((t, "no_data"))
            continue
        if t not in uyeler:
            out.append((t, "uyelik"))
    return out


def dolduruldu_kunyesi(ts, dilim: dict) -> dict:
    """Pencere genelinde ileri-doldurulmuş hücre kökeni: {hucre_n, sembol_n}.

    BİR KEZ ÖLÇÜLÜR, HER AY-SONUNDA DEĞİL: `dolduruldu_n` bir sembolün TÜM penceresini sayar
    ve karar gününden bağımsızdır; karar başına yeniden saymak aynı sayıyı ay-sonu sayısı kadar
    yeniden üretirdi (661 sembol × 73 ay = ölçülmüş bir israf)."""
    dolu = {t: ts.dolduruldu_n(r) for t, r in dilim.items()}
    return {"hucre_n": int(sum(dolu.values())),
            "sembol_n": int(sum(1 for v in dolu.values() if v)),
            "tanim": "pencere genelinde ömür-içi ffill edilmiş hücre / en az bir hücresi "
                     "doldurulmuş sembol (trend_shadow.DOLDU_KOL köken bayrağı)"}


def hucre_kararcisi(ts, hucre: str, *, aylar, ay_sira: dict, uyelik: dict, dilim: dict,
                    per: dict, atr: dict, mpos: dict, n_slots: int, chandelier_k: float,
                    mom_lookback: int, defter: list, dolu_kunye: dict | None = None):
    """(karar_fn, gunluk_fn) — `hucre` "D" ya da "C".

    D — AYLIK REBALANS DURAKSIZ: ay-sonunda üst-N listesi YENİDEN kurulur. Listeden düşen
        pozisyon `rotate` sebebiyle kapanır; hedef sepet listenin KENDİSİDİR (1/N).
    C — CHANDELIER MEVCUT: pozisyon rotasyonla KAPANMAZ. Çıkışlar chandelier (GÜNLÜK kontrol),
        üyelik kaybı ve fiyatsızlıktır; boşalan slot BİR SONRAKİ ay-sonunda, listenin en üstünden
        doldurulur (incumbent akış — EDG-009 A/C tanımı).

    `defter` ay-sonu karar kaydını toplar (aday sayısı, seçilenler, ileri-doldurma kökeni) —
    kart `ay_sonu_aday_alt` eşiği ve RAPOR'un isim-sayısı zaman serisi BU defterden okunur.
    Defter HÜCRE BAŞINA doldurulur; çağıran D'ninkini birincil sayar."""
    if hucre not in HUCRELER:
        raise ValueError(f"bilinmeyen hücre {hucre!r} — seçenekler: {HUCRELER}")
    ay_kume = set(aylar)

    def _chandelier(durum: dict, rd) -> list:
        out = []
        for t in sorted(durum["pozisyon"]):
            p = durum["pozisyon"][t]
            a = atr_degeri(atr, t, rd)
            tepe = float(p.get("peak_high") or 0.0)
            px = p.get("last_close")
            if a is None or tepe <= 0 or _nan(px):
                continue                    # ölçülemeyen durakla pozisyon KAPATILMAZ
            if float(px) < tepe - float(chandelier_k) * a:
                out.append((t, "chandelier"))
        return out

    def karar_fn(s, durum):
        g = str(s.date())
        if g not in ay_kume:
            return None
        k = ay_sira[g]
        if k < mom_lookback:
            return None                     # ısınma: 13 ay-sonu çapası yok, karar ALINMAZ
        a1 = aylar[k - 1]
        a12 = aylar[k - mom_lookback]
        uyeler = set(uyelik.get(g, frozenset()))
        rows = momentum_satirlari(dilim, uyeler, _ts(a1), _ts(a12), s, atr, per)
        sirali = [t for t, _ in rows]
        dolu = dolu_kunye or {}

        cikislar = _zorunlu_cikislar(ts, durum, s, per, uyeler, mpos)
        if hucre == "C":
            cikislar += [x for x in _chandelier(durum, s)
                         if x[0] not in {t for t, _ in cikislar}]
            cikan = {t for t, _ in cikislar}
            kalan = [t for t in durum["pozisyon"] if t not in cikan]
            bos = n_slots - len(kalan)
            yeni = [t for t in sirali if t not in durum["pozisyon"]][:max(bos, 0)]
            sepet = sorted(set(kalan) | set(yeni))
        else:
            sepet = ust_n(rows, n_slots)
            cikan = {t for t, _ in cikislar}
            cikislar += [(t, "rotate") for t in sorted(durum["pozisyon"])
                         if t not in cikan and t not in set(sepet)]

        defter.append({"ay_sonu": g, "hucre": hucre, "uye_n": len(uyeler),
                       "aday_n": len(rows), "sepet_n": len(sepet), "sepet": list(sepet),
                       "cikis_n": len(cikislar),
                       "cikis_sebepleri": sorted({sb for _, sb in cikislar}),
                       "dolduruldu_hucre": dolu.get("hucre_n"),
                       "dolduruldu_sembol": dolu.get("sembol_n")})
        hedef = ({t: 1.0 / n_slots for t in sepet} if sepet else {})
        return {"date": s, "cikislar": cikislar, "hedef": hedef}

    def gunluk_fn(s, durum):
        if hucre != "C":
            return None
        cik = _chandelier(durum, s)
        if not cik:
            return None
        return {"date": s, "cikislar": cik, "hedef": None}

    return karar_fn, gunluk_fn


def cita_kararcisi(ts, tur: str, *, aylar, ay_sira: dict, uyelik: dict, per: dict,
                   mpos: dict, mom_lookback: int, defter: list):
    """ÇITA karar üreticisi. `tur`: `cita_esli` (EW AYLIK REBALANS) ya da `cita_taban` (EW BH).

    `cita_esli` — KARTIN ÇITASI: "aynı gün as-of üyelerin EW aylık-rebalans getirisi (aynı
    sürtünme)". Sepet ay-sonunda AS-OF ÜYE ve O GÜN FİYATLANABİLİR isimlerin TAMAMIDIR (aday
    süzgeci UYGULANMAZ: çıta kolun evrenidir, kolun sinyali değil), ağırlık 1/n.

    `cita_taban` — EW BUY&HOLD: İLK karar ay-sonunun as-of üyeleri BİR KEZ alınır ve tutulur;
    sonraki ay-sonlarında yalnız fiyatsız/bayat isimler kapanır (ölü ismi sonsuza taşımamak
    için). Rebalans YOKTUR — EDG-009'un `EW_full_BH` çıtasının bu penceredeki karşılığı."""
    ay_kume = set(aylar)
    kuruldu = {"durum": False}

    def _fiyatlanabilir(t, rd):
        px, bar_t = ts._son_kapanis(per.get(t), rd)
        if px is None:
            return False
        return not (bar_t is not None and ts._bayat_mi(bar_t, rd, mpos))

    def karar_fn(s, durum):
        g = str(s.date())
        if g not in ay_kume:
            return None
        k = ay_sira[g]
        if k < mom_lookback:
            return None                     # hücrelerle AYNI başlangıç: fazla serisi hizalı
        uyeler = sorted(t for t in uyelik.get(g, frozenset()) if _fiyatlanabilir(t, s))
        if tur == CITA_TABAN and kuruldu["durum"]:
            cik = [(t, "no_data") for t in sorted(durum["pozisyon"])
                   if not _fiyatlanabilir(t, s)]
            return {"date": s, "cikislar": cik, "hedef": None} if cik else None
        if not uyeler:
            return None
        kuruldu["durum"] = True
        w = 1.0 / len(uyeler)
        kume = set(uyeler)
        cikislar = [(t, "uyelik") for t in sorted(durum["pozisyon"]) if t not in kume]
        defter.append({"ay_sonu": g, "cita": tur, "uye_n": len(uyeler), "agirlik": w})
        return {"date": s, "cikislar": cikislar, "hedef": {t: w for t in uyeler}}

    return karar_fn


def _cita_uye_sayisi(defter: list, tur: str) -> dict:
    """Bir çıtanın ay-sonu üye sayıları: ilk / son / ortalama. Kayıt yoksa SIFIR YAZILMAZ —
    None + neden (çıta hiç kurulmadıysa "0 üye" ile "ölçülemedi" aynı piksele düşerdi)."""
    n = [r["uye_n"] for r in defter if r.get("cita") == tur]
    if not n:
        return {"ilk": None, "son": None, "ay_ort": None, "ay_n": 0,
                "neden": f"`{tur}` için ay-sonu kaydı YOK — üye sayısı ÖLÇÜLEMEDİ"}
    return {"ilk": n[0], "son": n[-1], "ay_ort": _sayi(sum(n) / len(n)), "ay_n": len(n),
            "neden": None}


def _ts(g):
    """ISO gün metni → pandas Timestamp (dilim indeksi Timestamp taşır). pandas GEÇ ithal edilir:
    modül düzeyi temiz kalsın (bu dosyayı ithal etmek bir koşum tetiklememeli)."""
    import pandas as pd
    return pd.Timestamp(g)


# =================================================================================================
# 7. İSTATİSTİK — AYLIK FAZLA SERİSİ, NEWEY-WEST t, BLOK-BOOTSTRAP CI
# =================================================================================================
def aylik_getiriler(equity: dict, aylar: list[str]) -> list:
    """[(ay-sonu, getiri)] — ardışık ay-sonu özkaynakları arasındaki getiri.

    Ölçülemeyen ay ATLANMAZ, DÜŞÜRÜLÜR ve çağıran hizalamayı `ortak_aylar` ile kurar: iki
    eğrinin farklı aylarda delik taşıması, fazla serisini sessizce kaydırırdı."""
    out = []
    for i in range(1, len(aylar)):
        a, b = aylar[i - 1], aylar[i]
        e0, e1 = equity.get(a), equity.get(b)
        if e0 is None or e1 is None or e0 <= 0:
            continue
        out.append((b, e1 / e0 - 1.0))
    return out


def fazla_serisi(kol: list, cita: list) -> list:
    """[(ay, kol_getirisi − cita_getirisi)] — YALNIZ İKİSİNDE DE ölçülmüş aylar."""
    c = dict(cita)
    return [(a, r - c[a]) for a, r in kol if a in c]


def newey_west_t(x, lag: int = NW_GECIKME):
    """(t, neden) — ortalamanın Newey-West (Bartlett) düzeltilmiş t istatistiği.

    Varyans tahmini POZİTİF ÇIKMAYABİLİR (küçük örneklemde Bartlett toplamı negatife düşebilir);
    o hâlde t UYDURULMAZ, None + neden döner."""
    import numpy as np
    a = np.asarray([float(v) for v in x], dtype=float)
    n = a.size
    if n < 2:
        return None, f"örneklem çok küçük (n={n})"
    mu = float(a.mean())
    e = a - mu
    s = float(e @ e) / n
    for l in range(1, min(int(lag), n - 1) + 1):
        g = float(e[l:] @ e[:-l]) / n
        s += 2.0 * (1.0 - l / (int(lag) + 1.0)) * g
    if s <= 0:
        return None, f"Newey-West varyansı pozitif değil (s={s:.6g}, n={n})"
    se = math.sqrt(s / n)
    if se <= 0:
        return None, "standart hata sıfır"
    return mu / se, None


def blok_bootstrap_ci(x, *, blok: int = BOOTSTRAP_BLOK_AY, tekrar: int = 2000,
                      tohum: int = 0, olcek: float = 12.0):
    """(alt, ust, neden) — dairesel blok-bootstrap ile yıllıklandırılmış ortalamanın %95 CI'si.

    Blok uzunluğu AY cinsindendir (kart lafzı: "12 aylık blok"); dairesel seçim serinin sonunu
    başına bağlar, böylece her gözlem eşit olasılıkla örneklenir. Örneklem bloktan kısaysa CI
    UYDURULMAZ: None + neden."""
    import numpy as np
    a = np.asarray([float(v) for v in x], dtype=float)
    n = a.size
    if n < int(blok) or n < 2:
        return None, None, f"örneklem blok uzunluğundan kısa (n={n}, blok={blok})"
    rng = np.random.default_rng(int(tohum))
    nb = int(math.ceil(n / int(blok)))
    baslar = rng.integers(0, n, size=(int(tekrar), nb))
    ofs = np.arange(int(blok))
    idx = (baslar[:, :, None] + ofs[None, None, :]).reshape(int(tekrar), nb * int(blok)) % n
    ort = a[idx[:, :n]].mean(axis=1) * float(olcek)
    return float(np.percentile(ort, 2.5)), float(np.percentile(ort, 97.5)), None


def fazla_ozeti(fazla: list, *, tohum: int, tekrar: int) -> dict:
    """Kartın istediği fazla bloğu: yıllıklandırılmış ortalama, t (NW-3), blok-bootstrap CI.

    `ci0_disi` = CI'nin sıfırı İÇERMEMESİ (kartın "bootstrap CI-0-dışı" lafzı). Ölçülemeyen
    hiçbir alan 0 yazılmaz — None + neden (sıfır ile 'bilmiyorum' aynı şey değildir)."""
    n = len(fazla)
    if n == 0:
        return {"ann_pct": None, "t_nw": None, "ci95": [None, None], "ci0_disi": None,
                "n_months": 0, "pozitif_ay_pct": None, "fazla_std_yillik_pct": None,
                "neden": "ortak ay YOK — fazla serisi kurulamadı"}
    import numpy as np
    v = np.asarray([r for _, r in fazla], dtype=float)
    t, t_neden = newey_west_t(v)
    alt, ust, ci_neden = blok_bootstrap_ci(v, tohum=tohum, tekrar=tekrar)
    return {
        "ann_pct": _sayi(float(v.mean()) * 12.0 * 100.0),
        "t_nw": _sayi(t), "t_neden": t_neden,
        "ci95": [_sayi(None if alt is None else alt * 100.0),
                 _sayi(None if ust is None else ust * 100.0)],
        "ci0_disi": (None if (alt is None or ust is None) else bool(alt > 0 or ust < 0)),
        "ci_neden": ci_neden,
        "n_months": n,
        "pozitif_ay_pct": _sayi(float((v > 0).mean()) * 100.0),
        "fazla_std_yillik_pct": _sayi(float(v.std(ddof=1)) * math.sqrt(12.0) * 100.0
                                      if n > 1 else None),
        "tanim": "aylık (hücre − çıta) serisi; ann_pct = ortalama × 12; t = Newey-West "
                 f"{NW_GECIKME} gecikme; CI = dairesel blok-bootstrap ({BOOTSTRAP_BLOK_AY} ay "
                 f"blok, {tekrar} tekrar, sabit tohum)",
    }


def egri_ozeti(equity: dict, aylar: list[str], baslangic_gun: str | None = None) -> dict:
    """Eğri istatistikleri — EDG-009 `sonuc.json` alan adlarıyla (total_return/cagr/vol/…).

    `baslangic_gun` ISINMA PENCERESİNİ KESER ve VERİLMESİ ŞARTTIR (çağıran ilk karar ay-sonunu
    verir): ısınma boyunca portföy %100 NAKİTTİR ve eğri düzdür; o düzlüğü CAGR'ın paydasına
    katmak, ölçülmeyen bir dönemi "getiri üretmedi" diye raporlamak olurdu. Kesilen dönem
    `ilk_gun` alanında ADIYLA durur."""
    gunler = [g for g in sorted(equity) if baslangic_gun is None or g >= baslangic_gun]
    if len(gunler) < 2:
        return {"total_return": None, "cagr": None, "vol_ann": None, "sharpe": None,
                "max_dd": None, "years": None, "n_ay": 0,
                "neden": "eğri iki noktadan kısa — istatistik ÖLÇÜLEMEDİ"}
    import numpy as np
    ilk, son = equity[gunler[0]], equity[gunler[-1]]
    yil = (dt.date.fromisoformat(gunler[-1]) - dt.date.fromisoformat(gunler[0])).days / 365.25
    ay = aylik_getiriler(equity, aylar)
    r = np.asarray([x for _, x in ay], dtype=float) if ay else np.asarray([], dtype=float)
    seri = np.asarray([equity[g] for g in gunler], dtype=float)
    tepe = np.maximum.accumulate(seri)
    dd = float((seri / tepe - 1.0).min()) if seri.size else None
    vol = float(r.std(ddof=1)) * math.sqrt(12.0) if r.size > 1 else None
    cagr = ((son / ilk) ** (1.0 / yil) - 1.0) if (ilk > 0 and yil > 0 and son > 0) else None
    return {"total_return": _sayi(son / ilk - 1.0 if ilk > 0 else None),
            "cagr": _sayi(cagr), "vol_ann": _sayi(vol),
            "sharpe": _sayi(cagr / vol if (cagr is not None and vol) else None),
            "max_dd": _sayi(dd), "years": _sayi(yil), "n_ay": len(ay),
            "ilk_gun": gunler[0], "son_gun": gunler[-1],
            "ilk_equity": _sayi(ilk), "son_equity": _sayi(son)}


def yil_yil(kol: list, cita: list) -> dict:
    """Yıl-yıl dilim: {yıl: {kol_pct, cita_pct, fazla_puan, n_ay}} — aylık getirilerden bileşik.

    EDG-009 `yil_yil_esli_citaya` bloğuyla AYNI alan adları; birim PUANDIR (yüzde farkı)."""
    c = dict(cita)
    yillar: dict = {}
    for a, r in kol:
        if a not in c:
            continue
        y = a[:4]
        d = yillar.setdefault(y, {"k": 1.0, "c": 1.0, "n": 0})
        d["k"] *= (1.0 + r)
        d["c"] *= (1.0 + c[a])
        d["n"] += 1
    return {y: {"kol_pct": _sayi((d["k"] - 1.0) * 100.0),
                "cita_pct": _sayi((d["c"] - 1.0) * 100.0),
                "fazla_puan": _sayi((d["k"] - d["c"]) * 100.0),
                "n_ay": d["n"]}
            for y, d in sorted(yillar.items())}


# =================================================================================================
# 8. EŞİK HÜKMÜ VE KILL-LIST — HEPSİ KARTTAN
# =================================================================================================
def esik_hukmu(kart: dict, hucreler: dict, olculemeyen: dict, aday: dict) -> dict:
    """Kart eşiklerinin {deger, esik, gecti} okuması. EŞİK KARTTANDIR, burada UYDURULMAZ.

    `fazla_yillik_alt` / `t_alt`: kart lafzı "D ya da C hücresi" — yani eşiği SAĞLAYAN hücre
    varsa geçer; hangi hücrelerin sağladığı `saglayan` alanında ADIYLA durur.
    `ay_sonu_aday_alt`: ölçülen değer ay-sonu aday sayılarının ASGARİSİdir; kart lafzı "her
    ay-sonunda ≥ 30". Kill-list'in %10'luk "düşük ay payı" lafzı AYRI bir satırdır ve
    `kill_list_tetik`te durur.
    `olculemeyen_ust_oran`: ölçülemeyen isim payı ≤ eşik."""
    e = kart["esikler_sayisal"]
    fazla = {h: (hucreler.get(h) or {}).get("fazla") or {} for h in HUCRELER}
    saglayan = [h for h in HUCRELER
                if (fazla[h].get("ann_pct") is not None
                    and fazla[h]["ann_pct"] / 100.0 >= e["fazla_yillik_alt"])]
    t_saglayan = [h for h in HUCRELER
                  if (fazla[h].get("t_nw") is not None and fazla[h]["t_nw"] >= e["t_alt"])]
    en_iyi = [fazla[h]["ann_pct"] for h in HUCRELER if fazla[h].get("ann_pct") is not None]
    en_iyi_t = [fazla[h]["t_nw"] for h in HUCRELER if fazla[h].get("t_nw") is not None]
    asgari = aday.get("aday_n_min")
    oran = olculemeyen.get("oran")
    return {
        "fazla_yillik_alt": {
            "deger": _sayi(max(en_iyi) / 100.0 if en_iyi else None), "esik": e["fazla_yillik_alt"],
            "gecti": bool(saglayan) if en_iyi else None,
            "saglayan": saglayan, "birim": "oran (0,03 = +3 puan/yıl)",
            "neden": None if en_iyi else "hiçbir hücrede fazla ÖLÇÜLEMEDİ"},
        "t_alt": {
            "deger": _sayi(max(en_iyi_t) if en_iyi_t else None), "esik": e["t_alt"],
            "gecti": bool(t_saglayan) if en_iyi_t else None, "saglayan": t_saglayan,
            "neden": None if en_iyi_t else "hiçbir hücrede t ÖLÇÜLEMEDİ"},
        "ay_sonu_aday_alt": {
            "deger": _sayi(asgari), "esik": e["ay_sonu_aday_alt"],
            "gecti": (None if asgari is None else bool(asgari >= e["ay_sonu_aday_alt"])),
            "tanim": "ay-sonu aday sayılarının ASGARİSİ (kart: her ay-sonunda ≥ eşik)",
            "dusuk_ay_n": aday.get("dusuk_ay_n"), "dusuk_ay_payi": _sayi(aday.get("dusuk_ay_payi")),
            "ay_n": aday.get("ay_n"),
            "neden": None if asgari is not None else "ay-sonu kararı YOK — aday sayısı ölçülemedi"},
        "olculemeyen_ust_oran": {
            "deger": _sayi(oran), "esik": e["olculemeyen_ust_oran"],
            "gecti": (None if oran is None else bool(oran <= e["olculemeyen_ust_oran"])),
            "neden": olculemeyen.get("neden")},
    }


def kill_list_tetikleri(kart: dict, esik: dict, pk1: dict, aday: dict,
                        olculemeyen: dict) -> list:
    """Kartın kill-list SATIRLARI + ölçülen değer + tetik. METİN KARTTANDIR, yeniden yazılmaz.

    TETİK YALNIZ `esikler` BLOĞUNDAN TÜRETİLEBİLDİĞİNDE KURULUR. Kartın üçüncü kill-list
    satırı ("aday sayısı < 30 olan ay payı > %10") bir SAYI taşır ama o sayı `esikler`de
    YOKTUR — kod onu kart düzyazısından çıkarmaz (eşik icat etmenin kılık değiştirmiş hâli
    olurdu). O satırda `tetik: None` durur, ölçülen pay (`dusuk_ay_payi`) ADIYLA yanındadır ve
    hükmü Rol-1 kartın lafzıyla işler."""
    out = []
    for satir in kart["kill_list"]:
        kayit = {"lafiz": satir, "tetik": None, "olculen": None, "neden": None}
        d = satir.lower()
        if d.startswith("pk-1"):
            kayit["olculen"] = {"kosdu": pk1.get("kosdu"), "gecti": pk1.get("gecti")}
            kayit["tetik"] = (None if pk1.get("gecti") is None else (not pk1["gecti"]))
            kayit["neden"] = pk1.get("neden")
        elif d.startswith("d ve c"):
            fa, ta = esik["fazla_yillik_alt"], esik["t_alt"]
            kayit["olculen"] = {"fazla_saglayan": fa.get("saglayan"),
                                "t_saglayan": ta.get("saglayan")}
            kayit["tetik"] = (None if (fa.get("gecti") is None or ta.get("gecti") is None)
                              else not (fa["gecti"] and ta["gecti"]))
        elif "ay payı" in d:
            kayit["olculen"] = {"dusuk_ay_n": aday.get("dusuk_ay_n"),
                                "dusuk_ay_payi": _sayi(aday.get("dusuk_ay_payi")),
                                "ay_n": aday.get("ay_n")}
            kayit["neden"] = ("pay eşiği (%10) kartın `esikler` bloğunda YOK — kod onu "
                              "düzyazıdan TÜRETMEZ (eşik icat etmek olurdu); ölçülen pay "
                              "yanındadır, hükmü Rol-1 kart lafzıyla işler")
        elif "ölçülemeyen" in d:
            kayit["olculen"] = {"oran": _sayi(olculemeyen.get("oran")),
                                "esik": esik["olculemeyen_ust_oran"]["esik"]}
            g = esik["olculemeyen_ust_oran"].get("gecti")
            kayit["tetik"] = (None if g is None else (not g))
        elif "bakma-ileri" in d:
            kayit["olculen"] = {"yapisal_kisit": "karar t kapanışı → icra t+1 açılışı; motor "
                                                 "bekleyen kararı BİR SONRAKİ seansta icra eder"}
            kayit["neden"] = ("bu satır bir KOD SÖZLEŞMESİdir, koşum çıktısından ölçülmez — "
                              "çivisi tests/test_edg099_midcap_trend_v497.py (§T3, §T4)")
        out.append(kayit)
    return out


def pk1_hukmu(pk_sonuc: dict | None, neden: str | None = None) -> dict:
    """PK-1 (large-cap as-of, AYNI KOD) hükmü: D fazla > 0 ∧ CI-0-dışı.

    Kart lafzı: "D hücresi fazla > 0 ve CI-0-dışı (yön + anlamlılık; büyüklük EDG-009 ile
    kıyaslanır, eşitlik istenmez)". C hücresi K'ye girmez ama YÖNÜ raporlanır — kart
    `pozitif_kontrol` (1) "C hücresinin yönü EDG-009 C ile aynı" der ve kıyası Rol-1 yapar.
    Koşmadıysa `gecti` None'dır: koşmamış bir PK "geçti" de "kaldı" da DEĞİLDİR."""
    if not pk_sonuc:
        return {"kosdu": False, "gecti": None, "D": None, "C": None,
                "neden": neden or "--pk-kohort/--pk-bars-dir verilmedi — PK-1 KOŞMADI"}
    out = {"kosdu": True, "neden": None}
    for h in HUCRELER:
        f = ((pk_sonuc.get(h) or {}).get("fazla")) or {}
        out[h] = {"fazla": f.get("ann_pct"), "t_nw": f.get("t_nw"), "ci": f.get("ci95"),
                  "ci0_disi": f.get("ci0_disi"), "n_months": f.get("n_months")}
    d = out.get("D") or {}
    out["gecti"] = (None if (d.get("fazla") is None or d.get("ci0_disi") is None)
                    else bool(d["fazla"] > 0 and d["ci0_disi"]))
    out["lafiz"] = ("kart `esikler.pk1_large_cap`: D hücresi fazla > 0 ve CI-0-dışı "
                    "(yön + anlamlılık; büyüklük eşitliği İSTENMEZ)")
    return out


# =================================================================================================
# 9. ANA ÖLÇÜM — TEK EVREN, TEK PENCERE (hücreler + çıtalar + istatistik)
# =================================================================================================
def olc(yuzey: dict, *, kohort_csv, bars_dir, baslangic, bitis, dusur, tohum: int,
        etiket: str) -> dict:
    """Bir EVREN üzerinde D ve C hücrelerini + iki çıtayı koşar; istatistikleri üretir.

    `dusur` = tüm günlerden düşürülecek (belirsiz) semboller. `etiket` koşumun adıdır
    (`dahil`/`haric`/`pk1`) ve çıktıda ADIYLA durur — üç koşum aynı dosyada yaşar, etiketsiz
    sayılar birbirine karışırdı."""
    K, ts, O, p1, dat = yuzey["K"], yuzey["ts"], yuzey["O"], yuzey["p1"], yuzey["dat"]
    import pandas as pd

    etkin, capa, ham_n = K.etkin_satirlar(p1, pathlib.Path(kohort_csv), baslangic, bitis)
    birlesim = set()
    for _, k in etkin:
        birlesim |= set(k)
    olculecek = sorted(birlesim - set(dusur))

    gunler = seanslar(dat, baslangic, bitis)
    if not gunler:
        kullanim_hatasi(
            "XNYS seans takvimi ÜRETİLEMEDİ (adapters.data._sessions boş) — ay-sonu sorusu "
            "CEVAPSIZDIR ve karar alınamaz (fail-closed). Ay-sonu KOHORT BARLARINDAN "
            "TÜRETİLMEZ: `pandas_market_calendars` kurulu mu?")
    aylar, takvim = ay_sonlari(ts, gunler)
    if not aylar:
        kullanim_hatasi(f"pencerede XNYS ay-sonu seansı BULUNAMADI ({baslangic} → {bitis})")

    uyelik = K.uyelik_haritasi(etkin, gunler, frozenset(dusur))
    per_ham, bar_acc = K.barlari_yukle(olculecek, pathlib.Path(bars_dir), p1, O, dat, pd)
    per = ts._norm(per_ham)

    master = pd.DatetimeIndex([pd.Timestamp(g) for g in gunler])
    mpos = {d: i for i, d in enumerate(master)}
    dilim = ts._dilim(per, sorted(per), master)
    atr = {t: ts._atr(r) for t, r in dilim.items()}
    ay_sira = {g: i for i, g in enumerate(aylar)}

    n_slots = int(ts.N_SLOTS)
    mom = int(ts.MOM_LOOKBACK)
    fee = float(ts.FRICTION_BPS)
    sermaye = float(ts.INIT_EQUITY)

    # ---------- hücreler ----------
    dolu_kunye = dolduruldu_kunyesi(ts, dilim)
    defterler = {h: [] for h in HUCRELER}
    durumlar = {}
    for h in HUCRELER:
        karar_fn, gunluk_fn = hucre_kararcisi(
            ts, h, aylar=aylar, ay_sira=ay_sira, uyelik=uyelik, dilim=dilim, per=per, atr=atr,
            mpos=mpos, n_slots=n_slots, chandelier_k=float(ts.CHANDELIER_K), mom_lookback=mom,
            defter=defterler[h], dolu_kunye=dolu_kunye)
        durumlar[h] = simule(ts, master, per, karar_fn, fee_bps=fee, sermaye=sermaye,
                             gunluk_fn=gunluk_fn)

    # ---------- çıtalar ----------
    cita_defteri: list = []
    cita_durum = {}
    for tur in (CITA_ESLI, CITA_TABAN):
        kf = cita_kararcisi(ts, tur, aylar=aylar, ay_sira=ay_sira, uyelik=uyelik, per=per,
                            mpos=mpos, mom_lookback=mom, defter=cita_defteri)
        cita_durum[tur] = simule(ts, master, per, kf, fee_bps=fee, sermaye=sermaye)

    # ---------- istatistik ----------
    olcum_aylari = [g for g in aylar if ay_sira[g] >= mom]
    olcum_bas = olcum_aylari[0] if olcum_aylari else None
    cita_ay = {t: aylik_getiriler(cita_durum[t]["equity"], olcum_aylari)
               for t in (CITA_ESLI, CITA_TABAN)}
    tekrar = int(O.BOOT)

    hucreler = {}
    for h in HUCRELER:
        kol_ay = aylik_getiriler(durumlar[h]["equity"], olcum_aylari)
        f_esli = fazla_serisi(kol_ay, cita_ay[CITA_ESLI])
        f_taban = fazla_serisi(kol_ay, cita_ay[CITA_TABAN])
        d = defterler[h]
        hucreler[h] = {
            "tanim": {"ad": ("D_rotate_pit_midcap" if h == "D" else "C_chandelier_pit_midcap"),
                      "cikis": ("aylik_rebalans_duraksiz" if h == "D" else "chandelier_mevcut"),
                      "evren": "sp400_pit_asof", "cita_esli": CITA_ESLI,
                      "cita_taban": CITA_TABAN},
            "stats": egri_ozeti(durumlar[h]["equity"], olcum_aylari, olcum_bas),
            "fazla": fazla_ozeti(f_esli, tohum=tohum, tekrar=tekrar),
            "fazla_taban_citaya": fazla_ozeti(f_taban, tohum=tohum, tekrar=tekrar),
            "yil_yil_esli_citaya": yil_yil(kol_ay, cita_ay[CITA_ESLI]),
            "devir": {
                "n_rebalans": len(d), "islem_bacagi": durumlar[h]["sayac"]["islem_bacagi"],
                "n_giris": durumlar[h]["sayac"]["giris"],
                "n_kapanan_islem": len(durumlar[h]["kapanan"]),
                "cikislar": {s: int(durumlar[h]["sayac"]["cikis"].get(s, 0))
                             for s in CIKIS_SEBEPLERI},
                "friksiyon_usd": _sayi(durumlar[h]["sayac"]["friksiyon"]),
                "fiyatsiz_cikis": durumlar[h]["sayac"]["fiyatsiz_cikis"],
                "fiyatsiz_giris": durumlar[h]["sayac"]["fiyatsiz_giris"]},
            "islem_ornegi": durumlar[h]["kapanan"][:25],
            "ay_sonu_defteri": d,
        }

    citalar = {}
    for tur in (CITA_ESLI, CITA_TABAN):
        citalar[tur] = {
            "tanim": ("aynı gün AS-OF üyelerin EW aylık-rebalans getirisi (aynı sürtünme) — "
                      "kart çıtası" if tur == CITA_ESLI else
                      "EW BUY&HOLD: ilk karar ay-sonunun as-of üyeleri bir kez alınır, tutulur "
                      "(rebalans YOK); yalnız fiyatsız/bayat isim kapanır"),
            "stats": egri_ozeti(cita_durum[tur]["equity"], olcum_aylari, olcum_bas),
            "uye_sayisi": _cita_uye_sayisi(cita_defteri, tur),
            "friksiyon_usd": _sayi(cita_durum[tur]["sayac"]["friksiyon"]),
            "islem_bacagi": cita_durum[tur]["sayac"]["islem_bacagi"],
        }

    # ---------- aday muhasebesi (kart `ay_sonu_aday_alt`) ----------
    d0 = defterler["D"]
    aday_n = [r["aday_n"] for r in d0]
    aday = {"ay_n": len(aday_n),
            "aday_n_min": (min(aday_n) if aday_n else None),
            "aday_n_ort": _sayi(sum(aday_n) / len(aday_n) if aday_n else None),
            "aday_n_son": (aday_n[-1] if aday_n else None),
            "seri": [{"ay_sonu": r["ay_sonu"], "aday_n": r["aday_n"], "uye_n": r["uye_n"]}
                     for r in d0],
            "kaynak": "D hücresinin ay-sonu defteri (aday süzgeci iki hücrede AYNIdır)"}

    # ---------- ölçülemeyen isimler ----------
    yok = sorted(set(bar_acc.get("dosya_yok_semboller") or []))
    kisa = sorted(set(bar_acc.get("kisa_semboller") or []))
    okunamadi = sorted({s.split(":", 1)[0] for s in (bar_acc.get("okunamadi_semboller") or [])})
    olculemeyen_kume = set(yok) | set(kisa) | set(okunamadi)
    olculemeyen = {
        "n": len(olculemeyen_kume), "birlesim_n": len(birlesim),
        "oran": (len(olculemeyen_kume) / len(birlesim)) if birlesim else None,
        "neden_dagilimi": {
            "bar_dosyasi_yok": {"n": len(yok), "semboller": yok[:40],
                                "neden": "kohort ismi için bar csv'si YOK (--bars-dir)"},
            "kisa_seri": {"n": len(kisa), "semboller": kisa[:40],
                          "neden": f"seri {bar_acc.get('bar_min_uzunluk')} bardan KISA "
                                   f"(wp2 ortak.BAR_MIN_UZUNLUK — EDG-016 ile AYNI taban)"},
            "okunamadi": {"n": len(okunamadi), "ornek": (bar_acc.get("okunamadi_semboller")
                                                         or [])[:10],
                          "neden": "bar csv'si okunamadı / bütünlük taraması düştü"}},
        "neden": (None if birlesim else "kohort birleşimi BOŞ — pay ÖLÇÜLEMEDİ"),
        "not": "sayılar `k093.barlari_yukle` muhasebesinden okunur; yeniden hesaplanmaz "
               "(tek-kaynak yasası). Ölçülemeyen isim UYDURULMAZ, ADIYLA sayılır.",
    }
    # EŞİĞE BAĞLI ALANLAR BURADA DOLDURULMAZ: `olc` KART OKUMAZ (saf ölçüm, eşiksiz) — kart
    # eşiğinin altında kalan ay payını `_aday_payini_isle` doldurur. Alan BOŞ BIRAKILMAZ,
    # None + tanımla durur: yokluğu "ölçtük, sıfırdı" ile karıştırılabilirdi.
    aday["dusuk_ay_n"] = None
    aday["dusuk_ay_payi"] = None
    aday["dusuk_ay_neden"] = ("kart eşiği uygulanmadı (saf ölçüm bloğu) — `_aday_payini_isle` "
                              "birincil koşumda doldurur")

    return {
        "etiket": etiket,
        "pencere": {"baslangic": baslangic.isoformat(), "bitis": bitis.isoformat(),
                    "seans_n": len(gunler), "ay_sonu_n": len(aylar),
                    "ilk_karar_ay_sonu": (olcum_aylari[0] if olcum_aylari else None),
                    "olcum_ay_n": len(olcum_aylari),
                    "isinma_ay_n": min(mom, len(aylar)),
                    "takvim": takvim},
        "evren": {"as_of_satir_n": len(etkin), "kohort_ham_satir_n": ham_n,
                  "pencere_oncesi_capa_satiri_var_mi": capa,
                  "isim_n_birlesim": len(birlesim), "dusurulen_n": len(dusur),
                  "olculecek_n": len(olculecek), "bar_yuklenen_n": bar_acc.get("yuklendi")},
        "bar_muhasebesi": {k: v for k, v in bar_acc.items()
                           if not k.endswith("_semboller")},
        "hucreler": hucreler, "citalar": citalar,
        "aday": aday, "olculemeyen": olculemeyen,
        "_etkin": etkin, "_uyelik": uyelik, "_gunler": gunler, "_bar_acc": bar_acc,
    }


def kosum_ozeti(blok: dict) -> dict:
    """Bir koşumun KOMPAKT özeti — `kosumlar` bloğuna girer.

    BEDEL YASASI (kazanç ölçülüp bedel ölçülmezse körlük sessizdir): tam blok üç kez
    (top-level + `kosumlar[kip]` + duyarlılık) yazılsaydı dosya üç katına çıkardı; özet ise
    `haric` koşumunun ay-sonu sepetlerini KAYBEDERDİ. Kaybı KAPATIYORUZ: sepet defteri özete
    DAHİLDİR (belirsiz-isim süzgecinin gerçekten uygulandığı oradan ölçülür), düşen tek şey
    işlem örneği ve eğri ayrıntısıdır — ikisi de BİRİNCİL koşumda top-level'da durur."""
    return {
        "etiket": blok["etiket"],
        "pencere": {k: v for k, v in blok["pencere"].items() if k != "takvim"},
        "evren": blok["evren"],
        "hucreler": {h: {"stats": c["stats"], "fazla": c["fazla"],
                         "devir": c["devir"], "ay_sonu_defteri": c["ay_sonu_defteri"]}
                     for h, c in blok["hucreler"].items()},
        "citalar": {t: {"stats": c["stats"], "uye_sayisi": c["uye_sayisi"]}
                    for t, c in blok["citalar"].items()},
        "aday": {k: v for k, v in blok["aday"].items() if k != "seri"},
        "olculemeyen": {k: v for k, v in blok["olculemeyen"].items()
                        if k != "neden_dagilimi"},
    }


def _aday_payini_isle(blok: dict, esik_deger: float) -> None:
    """Ay-sonu aday serisinin kart eşiğinin ALTINDA kalan ay payını doldurur.

    Eşik DIŞARIDAN (karttan) gelir; bu yüzden hesap `olc` içinde değil burada durur — `olc`
    kart okumaz ve okumamalıdır (saf ölçüm, eşiksiz)."""
    seri = blok["aday"]["seri"]
    n = len(seri)
    dusuk = sum(1 for r in seri if r["aday_n"] < esik_deger)
    blok["aday"]["dusuk_ay_n"] = dusuk
    blok["aday"]["dusuk_ay_payi"] = (dusuk / n) if n else None
    blok["aday"]["dusuk_ay_neden"] = (None if n else "ay-sonu kararı YOK — pay ÖLÇÜLEMEDİ")
    blok["aday"]["dusuk_ay_esigi"] = float(esik_deger)


# =================================================================================================
# 10. RAPOR
# =================================================================================================
def _p(x, nd=2):
    return "—" if x is None else f"{float(x):.{nd}f}"


def rapor_metni(sonuc: dict) -> str:
    """RAPOR_099_<damga>.md — okuyanı Rol-1 / operatör masası (Yasa 6)."""
    S = sonuc
    b = S                          # birincil koşumun blokları TOP-LEVEL'DADIR (tek kopya)
    sat = [f"# EDG-2026-099 — S&P 400 PIT (as-of) MID-CAP TREND KOLU · ÖLÇÜM RAPORU",
           "",
           f"Damga `{S['damga_utc']}` · üretici `{S['uretici']}` · **HÜKÜM: {S['hukum']}**",
           "",
           "Bu rapor kartın ölçütlerini ÖLÇER; hükmü Rol-1 yazar. Karta DOKUNULMADI.",
           "",
           "## 0. PENCERE VE EVREN", ""]
    p, e = b["pencere"], b["evren"]
    sat += [f"- pencere: {p['baslangic']} → {p['bitis']} · {p['seans_n']} XNYS seansı · "
            f"{p['ay_sonu_n']} ay-sonu",
            f"- ısınma {p['isinma_ay_n']} ay → ilk karar ay-sonu **{p['ilk_karar_ay_sonu']}** "
            f"· ölçülen ay {p['olcum_ay_n']}",
            f"- kohort: {e['isim_n_birlesim']} isim (birleşim) · barı yüklenen "
            f"{e['bar_yuklenen_n']} · düşürülen (belirsiz) {e['dusurulen_n']}",
            f"- takvim: {p['takvim']['kaynak']} · cevapsız gün {p['takvim']['cevapsiz_gun_n']}",
            "", "## 1. HÜCRE × ÖLÇÜ (K = 2)", "",
            "| hücre | çıkış | CAGR | vol | Sharpe | maxDD | fazla (eşli çıta) | t (NW-3) | "
            "%95 CI | CI-0-dışı |", "|---|---|---|---|---|---|---|---|---|---|"]
    for h in HUCRELER:
        c = b["hucreler"][h]
        st, f = c["stats"], c["fazla"]
        ci = f.get("ci95") or [None, None]
        sat.append(
            f"| **{c['tanim']['ad']}** | {c['tanim']['cikis']} | "
            f"{_p(None if st['cagr'] is None else st['cagr']*100)}% | "
            f"{_p(None if st['vol_ann'] is None else st['vol_ann']*100)}% | "
            f"{_p(st['sharpe'])} | "
            f"{_p(None if st['max_dd'] is None else st['max_dd']*100)}% | "
            f"{_p(f['ann_pct'])}% | {_p(f['t_nw'])} | "
            f"[{_p(ci[0])}, {_p(ci[1])}] | {f.get('ci0_disi')} |")
    sat += ["", "### Çıtalar", "",
            "| çıta | CAGR | vol | maxDD | üye (ay ort.) |", "|---|---|---|---|---|"]
    for t in (CITA_ESLI, CITA_TABAN):
        c = b["citalar"][t]
        st = c["stats"]
        sat.append(f"| {t} | {_p(None if st['cagr'] is None else st['cagr']*100)}% | "
                   f"{_p(None if st['vol_ann'] is None else st['vol_ann']*100)}% | "
                   f"{_p(None if st['max_dd'] is None else st['max_dd']*100)}% | "
                   f"{_p(c['uye_sayisi']['ay_ort'], 1)} |")
    sat += ["", "## 2. YIL-YIL FAZLA (eşli çıtaya karşı, puan)", "",
            "| yıl | " + " | ".join(HUCRELER) + " | ay |", "|---|" + "---|" * (len(HUCRELER) + 1)]
    yillar = sorted({y for h in HUCRELER for y in b["hucreler"][h]["yil_yil_esli_citaya"]})
    for y in yillar:
        hucre_y = [b["hucreler"][h]["yil_yil_esli_citaya"].get(y) or {} for h in HUCRELER]
        sat.append(f"| {y} | " + " | ".join(_p(x.get("fazla_puan"), 1) for x in hucre_y)
                   + f" | {(hucre_y[0] or {}).get('n_ay', '—')} |")
    sat += ["", "## 3. ÇIKIŞ KANALLARI VE DEVİR", "",
            "| hücre | kapanan | " + " | ".join(CIKIS_SEBEPLERI) + " | bacak | friksiyon $ |",
            "|---|---|" + "---|" * (len(CIKIS_SEBEPLERI) + 2)]
    for h in HUCRELER:
        d = b["hucreler"][h]["devir"]
        sat.append(f"| {h} | {d['n_kapanan_islem']} | "
                   + " | ".join(str(d["cikislar"][s]) for s in CIKIS_SEBEPLERI)
                   + f" | {d['islem_bacagi']} | {_p(d['friksiyon_usd'], 0)} |")
    a = b["aday"]
    sat += ["", "## 4. AY-SONU ADAY SAYISI (kart `ay_sonu_aday_alt`)", "",
            f"- ay sayısı {a['ay_n']} · asgari aday **{a['aday_n_min']}** · ortalama "
            f"{_p(a['aday_n_ort'], 1)} · son {a['aday_n_son']}",
            f"- eşiğin ALTINDA kalan ay: {a['dusuk_ay_n']} (pay {_p(a['dusuk_ay_payi'], 4)})",
            "", "## 5. ÖLÇÜLEMEYEN İSİMLER", ""]
    o = b["olculemeyen"]
    sat += [f"- ölçülemeyen {o['n']} / {o['birlesim_n']} · pay {_p(o['oran'], 4)}"]
    for ad, v in o["neden_dagilimi"].items():
        sat.append(f"  - `{ad}`: {v['n']} — {v['neden']}")
    sat += ["", "## 6. KART EŞİKLERİ", "", "| eşik | ölçülen | kart eşiği | geçti |",
            "|---|---|---|---|"]
    for ad, v in S["esikler"].items():
        sat.append(f"| `{ad}` | {_p(v.get('deger'), 4)} | {v.get('esik')} | {v.get('gecti')} |")
    sat += ["", "## 7. KILL-LIST (metinler KARTTAN)", ""]
    for k in S["kill_list_tetik"]:
        sat.append(f"- **tetik={k['tetik']}** — {k['lafiz']}")
        if k.get("neden"):
            sat.append(f"  - şerh: {k['neden']}")
    pk = S["pk1"]
    sat += ["", "## 8. PK-1 — LARGE-CAP AS-OF (AYNI KOD)", "",
            f"- koştu: **{pk.get('kosdu')}** · geçti: **{pk.get('gecti')}**"
            + (f" · neden: {pk.get('neden')}" if pk.get("neden") else "")]
    for h in HUCRELER:
        v = pk.get(h)
        if v:
            sat.append(f"  - {h}: fazla {_p(v.get('fazla'))}% · t {_p(v.get('t_nw'))} · "
                       f"CI {v.get('ci')} · CI-0-dışı {v.get('ci0_disi')}")
    u = S["ust_sinir_damgasi"]["b_barsiz_cikis_payi"]
    sat += ["", "## 9. ÜST-SINIR DAMGASI", "",
            "> **PIT kolu bir ÜST SINIRDIR.** Üyelik tarihi PIT'tir, FİYATLAR DEĞİLDİR: barı "
            "olmayan (delist/iflas/satın alınan) isimler ne kola ne çıtaya girer. Gerçek PIT "
            "getirisi bu ölçümden DÜŞÜK olabilir.",
            "",
            f"- barsız-çıkış payı: **{_p(u.get('payi'), 4)}** · kaynak: {u.get('kaynak')}",
            f"- neden (varsa): {u.get('neden')}",
            "", "## 10. DUYARLILIK — BELİRSİZ İSİMLER", ""]
    duy = S.get("duyarlilik_belirsiz") or {}
    sat.append(f"- kip: {duy.get('kip')} · birincil: {duy.get('birincil')} · belirsiz "
               f"{duy.get('belirsiz_n')} isim")
    for satir in (duy.get("kiyas") or []):
        sat.append(f"  - {satir['hucre']}: dahil {_p(satir['dahil_fazla'])}% "
                   f"(t {_p(satir['dahil_t'])}) vs hariç {_p(satir['haric_fazla'])}% "
                   f"(t {_p(satir['haric_t'])}) · işaret aynı: {satir['isaret_ayni']}")
    sat += ["", "## 11. SABİTLER (trend_shadow'dan İTHAL)", ""]
    for k, v in S["sabitler"].items():
        sat.append(f"- `{k}` = {v}")
    sat += ["", "## 12. GİRDİ DAMGASI", ""]
    for ad, v in S["girdi_damgasi"].items():
        sat.append(f"- `{ad}`: {v.get('yol')} · sha256 {v.get('sha256')}"
                   + (f" · {v.get('neden')}" if v.get("neden") else ""))
    sat += ["", f"**HÜKÜM: {S['hukum']}** — bu rapor hüküm ÖNERİSİ DE yazmaz.", ""]
    return "\n".join(sat)


# =================================================================================================
# 11. KOMUT SATIRI
# =================================================================================================
def _ayristirici() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="k099.py",
        description="EDG-2026-099 ANA ÖLÇÜM — S&P 400 PIT kohortunda uzun-ufuk trend kolu "
                    "(EDG-009 C/D hücreleri). HÜKÜM YOK.")
    ap.add_argument("--repo", type=pathlib.Path, required=True, help="depo kökü")
    ap.add_argument("--kohort", type=pathlib.Path, required=True,
                    help="sp400_uyelik_tarihi.csv (as-of adım fonksiyonu)")
    ap.add_argument("--bars-dir", type=pathlib.Path, required=True,
                    help="EDG-093 Parti-1'in yazdığı bars/ dizini")
    ap.add_argument("--kart", type=pathlib.Path, required=True,
                    help="EDG-2026-099 kart yaml'i — EŞİKLER VE KILL-LIST BURADAN OKUNUR "
                         "(zorunlu: eşik koda gömülmez, uydurulmaz)")
    ap.add_argument("--cikti", type=pathlib.Path, required=True, help="çıktı dizini")
    ap.add_argument("--baslangic", default=None,
                    help="pencere başı; VERİLMEZSE karttan (`veri_penceresi`) türetilir")
    ap.add_argument("--bitis", default=None,
                    help="pencere sonu; varsayılan kohort defterinin SON günü")
    ap.add_argument("--belirsiz", choices=BELIRSIZ_KIPLERI, default="ikisi",
                    help="belirsiz isimler: dahil | haric | ikisi (varsayılan)")
    ap.add_argument("--esleme", type=pathlib.Path, default=None,
                    help="sp400_elle_esleme.yaml (belirsiz isimler BURADAN türetilir)")
    ap.add_argument("--kapsama", type=pathlib.Path, default=None,
                    help="ADIM-0 B kapsama haritası json — barsız-çıkış payı (üst-sınır "
                         "damgası) BURADAN OKUNUR, yeniden HESAPLANMAZ")
    ap.add_argument("--pk-kohort", type=pathlib.Path, default=None,
                    help="PK-1 large-cap as-of kohortu (sp500_uyelik_tarihi.csv)")
    ap.add_argument("--pk-bars-dir", type=pathlib.Path, default=None,
                    help="PK-1 bar dizini (state/bars)")
    ap.add_argument("--tohum", type=int, default=None,
                    help="blok-bootstrap tohumu; verilmezse kart kimliğinden TÜRETİLİR")
    return ap


def tohum_coz(verilen) -> tuple[int, str]:
    """(tohum, kaynak). Verilmezse KART KİMLİĞİNDEN türetilir — rastgele bir sayı, koşumlar
    arası yeniden üretilebilirliği sessizce kırardı."""
    if verilen is not None:
        return int(verilen), "--tohum ile ELLE verildi"
    h = hashlib.sha256(KART_ID.encode("utf-8")).hexdigest()[:8]
    return int(h, 16), f"kart kimliğinden türetildi: sha256('{KART_ID}')[:8]"


def main(argv=None) -> int:
    """CLI → kart/bayrak doğrulaması → ithal → ölçüm gövdesi. YAN ETKİ SIRASI SÖZLEŞMEDİR.

    İKİ KAPI, İKİ YER:
      (1) KART VE BAYRAK TUTARLILIĞI İTHALDEN ÖNCE — hiçbir yan etki doğmadan. Eşik
          okunamıyorsa koşum HİÇ başlamamalı ve çıktı dizini bile AÇILMAMALIDIR.
      (2) İTHALDEN SONRAKİ kullanım hatası TEMİZLİK GEREKTİRİR: wp2 `ortak.py` modül düzeyinde
          kendi dizininde `_cache/`+`_state/` açar; çıkış 2 ile dönen bir koşum onları geride
          bırakır ve Rol-1'in `git status --porcelain` kapısını (dagit ön şartı) kirletir.
          ÖLÇÜLDÜ 2026-09-15: mutasyon koşumundan sonra ağaçta `wp2_olcum/_state/` kaldı.
          `except SystemExit` YUTMAZ — `raise` her yolda koşar, yakalanan şey yalnız temizlik
          fırsatıdır."""
    ap = _ayristirici()
    ARGV = ap.parse_args(argv)
    repo = ARGV.repo.resolve()
    cikti = ARGV.cikti.resolve()

    kart = kart_oku(ARGV.kart)
    if ARGV.pk_kohort is not None and ARGV.pk_bars_dir is None:
        kullanim_hatasi("--pk-kohort verildi ama --pk-bars-dir YOK — PK-1 bayrağı sessizce "
                        "YOK SAYILMAZ")
    if ARGV.pk_bars_dir is not None and ARGV.pk_kohort is None:
        kullanim_hatasi("--pk-bars-dir verildi ama --pk-kohort YOK — bayrak sessizce YOK "
                        "SAYILMAZ")
    cikti.mkdir(parents=True, exist_ok=True)
    damga = damga_uret()
    tohum, tohum_kaynak = tohum_coz(ARGV.tohum)

    yuzey = ithal_yuzeyi(repo, cikti, ARGV.bars_dir.resolve())
    try:
        return olcum_govdesi(ARGV, kart, yuzey, repo=repo, cikti=cikti, damga=damga,
                             tohum=tohum, tohum_kaynak=tohum_kaynak)
    except SystemExit:
        # sessiz-yutma DEĞİL: hata AYNEN yukarı çıkar (`raise` aşağıda). Yakalanan tek şey
        # temizlik fırsatıdır — ithalin açtığı dizinler geride kalmasın.
        temizlik = yuzey["K"].ithal_yan_etkisini_geri_al(yuzey)
        print(f"ithal yan etkisi temizliği (kullanım hatası yolu): {temizlik}", file=sys.stderr)
        raise


def olcum_govdesi(ARGV, kart: dict, yuzey: dict, *, repo, cikti, damga, tohum,
                  tohum_kaynak) -> int:
    """İTHALDEN SONRAKİ HER ŞEY: pencere → koşumlar → PK → eşikler → yazım.

    AYRI FONKSİYON OLMASININ GEREKÇESİ `main`in docstring'inde (2) maddesidir: gövde ayrı
    durunca `main` onu `except SystemExit` ile sarabilir. Buradaki her `kullanim_hatasi`
    çağrısı hâlâ çıkış 2 üretir — değişen tek şey, ağacın geride KİRLİ kalmamasıdır."""
    K, ts, O, p1 = yuzey["K"], yuzey["ts"], yuzey["O"], yuzey["p1"]

    # ---------- pencere ----------
    if ARGV.baslangic:
        bas_s, bas_kaynak = ARGV.baslangic, "--baslangic ile ELLE verildi"
    else:
        bas_s, bas_neden = p1.kart_pencere_baslangici(pathlib.Path(ARGV.kart))
        bas_kaynak = f"karttan türetildi: {ARGV.kart} `veri_penceresi`"
        if bas_s is None:
            kullanim_hatasi(f"pencere başı karttan okunamadı ({bas_neden}) — sessiz varsayılan YOK")
    try:
        baslangic = dt.date.fromisoformat(bas_s)
    except ValueError as e:
        # sessiz-yutma DEĞİL: bozuk tarih kullanım hatasıdır, varsayılana DÜŞÜLMEZ
        kullanim_hatasi(f"pencere başı ISO tarih olmalı ({e}): {bas_s!r}")

    ham_satirlar = p1.kohort_oku(pathlib.Path(ARGV.kohort))
    bitis_s = ARGV.bitis or ham_satirlar[-1][0].isoformat()
    bitis_kaynak = ("--bitis ile ELLE verildi" if ARGV.bitis
                    else "kohort defterinin SON as-of satırı (varsayılan)")
    try:
        bitis = dt.date.fromisoformat(bitis_s)
    except ValueError as e:
        # sessiz-yutma DEĞİL: aynı sınıf — sessiz varsayılan yok
        kullanim_hatasi(f"--bitis ISO tarih olmalı ({e}): {bitis_s!r}")
    if bitis < baslangic:
        kullanim_hatasi(f"--bitis ({bitis}) pencere başından ({baslangic}) ÖNCE olamaz")

    esleme = ARGV.esleme or (repo / "research" / "pit_universe" / "sp400_elle_esleme.yaml")
    belirsiz, bel_kaynak, bel_neden = K.belirsiz_isimler(esleme)

    # ---------- koşumlar ----------
    kipler = (BIRINCIL_KIP,) if ARGV.belirsiz == BIRINCIL_KIP else (
        ("haric",) if ARGV.belirsiz == "haric" else (BIRINCIL_KIP, "haric"))
    kosumlar = {}
    for kip in kipler:
        kosumlar[kip] = olc(yuzey, kohort_csv=ARGV.kohort, bars_dir=ARGV.bars_dir,
                            baslangic=baslangic, bitis=bitis,
                            dusur=(frozenset() if kip == BIRINCIL_KIP else belirsiz),
                            tohum=tohum, etiket=kip)
    birincil = kosumlar.get(BIRINCIL_KIP) or kosumlar[kipler[0]]
    _aday_payini_isle(birincil, kart["esikler_sayisal"]["ay_sonu_aday_alt"])

    # ---------- PK-1 ----------
    pk_blok, pk_neden = None, None
    if ARGV.pk_kohort is not None:
        pk = olc(yuzey, kohort_csv=ARGV.pk_kohort, bars_dir=ARGV.pk_bars_dir,
                 baslangic=baslangic, bitis=bitis, dusur=frozenset(), tohum=tohum,
                 etiket="pk1")
        pk_blok = pk["hucreler"]
        pk_neden = None
    pk1 = pk1_hukmu(pk_blok, pk_neden)
    if pk_blok is not None:
        pk1["evren"] = {"kohort": str(ARGV.pk_kohort), "bars_dir": str(ARGV.pk_bars_dir),
                        "isim_n": pk["evren"]["isim_n_birlesim"],
                        "bar_yuklenen_n": pk["evren"]["bar_yuklenen_n"],
                        "olcum_ay_n": pk["pencere"]["olcum_ay_n"]}

    # ---------- eşikler + kill-list ----------
    esikler = esik_hukmu(kart, birincil["hucreler"], birincil["olculemeyen"], birincil["aday"])
    kill = kill_list_tetikleri(kart, esikler, pk1, birincil["aday"], birincil["olculemeyen"])

    # ---------- üst-sınır damgası + yanlılık göstergeleri (k093'ten, YENİDEN HESAPLANMAZ) ----
    yanlilik = K.yanlilik_gostergesi(birincil["_etkin"], birincil["_uyelik"],
                                     birincil["_gunler"], birincil["_bar_acc"],
                                     ARGV.kapsama, belirsiz)

    # ---------- duyarlılık ----------
    duyarlilik = {"kip": ARGV.belirsiz, "birincil": BIRINCIL_KIP, "belirsiz_n": len(belirsiz),
                  "belirsiz_semboller": sorted(belirsiz), "belirsiz_kaynak": bel_kaynak,
                  "belirsiz_neden": bel_neden, "kiyas": []}
    if "haric" in kosumlar and BIRINCIL_KIP in kosumlar:
        for h in HUCRELER:
            d = (kosumlar[BIRINCIL_KIP]["hucreler"][h]["fazla"])
            x = (kosumlar["haric"]["hucreler"][h]["fazla"])
            duyarlilik["kiyas"].append({
                "hucre": h, "dahil_fazla": d.get("ann_pct"), "dahil_t": d.get("t_nw"),
                "haric_fazla": x.get("ann_pct"), "haric_t": x.get("t_nw"),
                "isaret_ayni": (None if (d.get("ann_pct") is None or x.get("ann_pct") is None)
                                else bool((d["ann_pct"] > 0) == (x["ann_pct"] > 0)))})

    # ---------- girdi damgası ----------
    def dmg(yol):
        sha, neden = _sha_veya_neden(yol)
        return {"yol": None if yol is None else str(yol), "sha256": sha, "neden": neden}

    edg093 = repo / "research" / "olcumler" / "edg093_midcap_pit"
    girdi = {
        "kohort_csv": dmg(ARGV.kohort), "kart": dmg(ARGV.kart), "elle_esleme": dmg(esleme),
        "kapsama_haritasi": dmg(ARGV.kapsama), "pk_kohort_csv": dmg(ARGV.pk_kohort),
        "bars_dizin": {"yol": str(ARGV.bars_dir), "sha256": None,
                       "neden": "dizin — tek sha yok; isim başına sha bars_manifest'tedir"},
        "olcum_kodu": dmg(pathlib.Path(__file__).resolve()),
        "k093": dmg(edg093 / "k093.py"), "parti1_ortak": dmg(edg093 / "ortak.py"),
        "trend_shadow": dmg(repo / "meridian" / "trend_shadow.py"),
        "wp2_ortak": dmg(yuzey["wp2_dizin"] / "ortak.py"),
    }

    sonuc = {
        "kart": KART_ID, "aile": AILE,
        "asama": "ANA ÖLÇÜM — mid-cap PIT trend kolu (EDG-009 C/D hücreleri, evren S&P 400 PIT)",
        "hukum": HUKUM,
        "rol": "ölçüm ajanı — HÜKÜM VERMEZ, hüküm ÖNERİSİ DE YAZMAZ; kart dosyasına DOKUNULMADI",
        "okuyan": "(1) Rol-1: hüküm AYNI turda karta + K defterine işlenir (CLAUDE.md §5); "
                  "(2) RAPOR_099_<damga>.md bu dosyadan üretilir.",
        "yazim_beyani": "YAZILAN HER ŞEY --cikti altındadır: sonuc_099_<damga>.json, "
                        "RAPOR_099_<damga>.md ve _state/ (config.STATE buraya çevrildi). "
                        "repo/state'e yazım YOK; canlı gölge-defterine (trend_book.json) "
                        "DOKUNULMADI — `run_cycle`/`_kaydet` ÇAĞRILMADI; ağa çıkılmadı.",
        "damga_utc": damga, "olcum_tarihi": dt.datetime.now(dt.timezone.utc).isoformat(),
        "uretici": "research/olcumler/edg099_midcap_trend/k099.py",
        "cozulen_yollar": yuzey["cozulen_yollar"],
        "DURUM": ("OLCULDU" if (birincil["hucreler"]["D"]["fazla"].get("ann_pct") is not None)
                  else "OLCULEMEDI"),
        "kart_kaydi": {k: v for k, v in kart.items() if k != "kill_list"},
        "girdi_damgasi": girdi,
        "sabitler": sabitler_kaydi(ts),
        "pencere_kaynagi": {"baslangic": bas_kaynak, "bitis": bitis_kaynak},
        "tohum": {"deger": tohum, "kaynak": tohum_kaynak, "tekrar": int(O.BOOT),
                  "blok_ay": BOOTSTRAP_BLOK_AY, "nw_gecikme": NW_GECIKME},
        "pencere": birincil["pencere"],
        "evren": birincil["evren"],
        "bar_muhasebesi": birincil["bar_muhasebesi"],
        "hucreler": birincil["hucreler"],
        "citalar": birincil["citalar"],
        "aday": birincil["aday"],
        "olculemeyen": birincil["olculemeyen"],
        "esikler": esikler,
        "kill_list_tetik": kill,
        "pk1": pk1,
        "ust_sinir_damgasi": yanlilik,
        "duyarlilik_belirsiz": duyarlilik,
        "kosumlar": {k: kosum_ozeti(v) for k, v in kosumlar.items()},
        "k_beyani": {"satirlar": [
            "K = 2 (kart `k_registry`): EDG-099-midcap-D-aylik-rebalans-fazla ve "
            "EDG-099-midcap-C-chandelier-fazla — BİRİNCİL koşumdan (belirsiz `dahil`).",
            "PK-1 (large-cap as-of), yanlılık göstergeleri, taban çıtasına karşı fazla, "
            "yıl-yıl dilim ve belirsiz-isim duyarlılığı TANIdır — K harcamaz.",
            "Eşik kartın ön-kayıtlı tanımıdır ve bu dosya YENİ EŞİK UYDURMAZ; kartta sayısı "
            "olmayan kill-list lafzı `tetik: None` ile durur.",
        ]},
        "ithal_yan_etkisi": K.ithal_yan_etkisini_geri_al(yuzey),
    }

    json_yolu = cikti / f"sonuc_099_{damga}.json"
    O.json_yaz(json_yolu, sonuc)
    rapor_yolu = cikti / f"RAPOR_099_{damga}.md"
    rapor_yolu.write_text(rapor_metni(sonuc), encoding="utf-8")

    print(f"YAZILDI: {json_yolu}")
    print(f"YAZILDI: {rapor_yolu}")
    d_fazla = birincil["hucreler"]["D"]["fazla"].get("ann_pct")
    c_fazla = birincil["hucreler"]["C"]["fazla"].get("ann_pct")
    print(f"durum={sonuc['DURUM']} · koşum={list(kosumlar)} · D fazla={d_fazla} · "
          f"C fazla={c_fazla} · PK-1 geçti={pk1.get('gecti')} · hüküm={HUKUM}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
