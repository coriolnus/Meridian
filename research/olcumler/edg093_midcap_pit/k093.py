"""EDG-2026-093 · ANA ÖLÇÜM Parti-2 — TURNOVER ANA ETKİSİ, EVREN = S&P 400 PIT KOHORTU.

Kart: research/cards/EDG-2026-093-midcap-pit-kohort-sagkalan-ust-sinir.yaml (`olcum_plani`).
KART DIŞINA ÖLÇÜM YOK; KARTA DOKUNULMAZ; eşik sonradan DEĞİŞMEZ. HÜKÜM YOK — `hukum` alanı
sabit "YOK — Rol-1" (CLAUDE.md §3, §5).

TASARIM: EDG-2026-016 AYNEN. TEK DEĞİŞKEN EVRENDİR.
    EDG-016 evreni `REPLAY_UNIVERSE` (251 large-cap, SABİT liste) idi; burada evren kohort
    defterinin AS-OF adım fonksiyonudur: bir `(t, isim)` gözlem hücresi ancak isim t gününde
    ÜYE ise panele girer. Özellikler, dilimler, tabanlar, CI şeması, maliyet modeli, tanı
    kesitleri AYNI — çünkü kart "EDG-016 tasarımı AYNEN" yazıyor ve iki evreni kıyaslanabilir
    kılan şey tam olarak budur.

İTHAL EDİLİR, KOPYALANMAZ (tek-kaynak yasası, CLAUDE.md §4):
  * research/olcumler/wp2_olcum/ortak.py — `bar_paneli`, `build_hisse`, `build_split_takvimi`,
    `HisseSerisi.asof`, `fiziksel_bekci`, `mean_with_ci`, `fark_with_ci`, `ic_with_ci`,
    `block_boot`, `_leak_kontrol`, `json_yaz`, `spearman_np` ve TÜM sabitler (BLOCK, BOOT,
    MIN_SLICE, MIN_KESIT, MALIYET_BPS, BAR_MIN_UZUNLUK, BAYAT_GUN, RNG).
  * research/olcumler/wp2_olcum/k016.py — `panel`, `ic_hizli`, `spearman_fast`,
    `ic_block_boot_fast` ve katman sabitleri (HORIZONS, UST_PCT, KONTROL_DILIM, KOVA_MIN).
  * research/olcumler/edg093_midcap_pit/ortak.py — kohort csv okuma/as-of çapası, bar dosya adı,
    sha256, damga (Parti-1 sözleşmeleri).
  * research/olcumler/edg093_midcap_pit/kohort.py → EDG-092 `olc.py` — `bilinen_olaylar`
    ayrıştırıcısı (PK-4) ve PIT-PK tohumu/örneklem büyüklüğü.
BU DOSYADA `def panel` YOKTUR ve olmamalıdır: panel gövdesi k016'nındır, buradaki tek ek
AS-OF ÜYELİK SÜZGECİdir. Çivi bunu kaynak metinden ölçer (v490).

k016'nın katman blokları `main()` İÇİNDE yaşar (ayrı fonksiyon değiller), o yüzden buraya
ORKESTRASYON olarak taşınır; İSTATİSTİK ÇEKİRDEKLERİ ve SABİTLER ithal edilir, yeniden
YAZILMAZ. Ayrışma riski `sabitler` bloğuyla kayda geçer ve v490 çivisi eşitliği ölçer.

PIT — SIFIR TOLERANS (CLAUDE.md §4):
  * üyelik AS-OF okunur: `as_of(t)` = tarihi t'den küçük-eşit olan SON kohort satırı
    (Parti-1 `ortak.kohort_oku`/`pencere_satirlari` sözleşmesi);
  * hisse sayısı `filed` ile seçilir (`build_hisse` → `HisseSerisi.asof`), `end` ile ASLA;
  * ölçülen satırlarda sızıntı sayacı AYRICA koşar (`_leak_kontrol`, üye günler üzerinde).

YAZIM — TEK YER `--cikti` (Yasa 6, okuyanı aşağıda):
  * `<cikti>/sonuc_093_<damga>.json`  → okuyan: Rol-1 (hüküm + K defteri) ve RAPOR üreteci.
  * `<cikti>/RAPOR_093_<damga>.md`    → okuyan: Rol-1 / operatör masası.
  * `<cikti>/_state/`                 → `meridian.config.STATE` BURAYA çevrilir; canlı boru
    hattının (`sanitize_bars`/`measurement_bars`) `obs.warn` çağrıları CANLI deftere değil
    buraya düşer (CLAUDE.md §2 "pytest dışı koşum obs'a ulaşırsa canlı deftere YAZAR").

İTHALİN YAN ETKİSİ ÖLÇÜLÜR VE GERİ ALINIR. wp2 `ortak.py` MODÜL DÜZEYİNDE `_cache/` ve
`_state/` dizinlerini kendi dizininde açar ve (varsa) canlı `bars_integrity.json`ı kopyalar —
ithal etmek bunu tetikler. Bu koşum ikisinin ÖNCEDEN var olup olmadığını kaydeder, config'i
kendi çıktısına çevirir ve koşum sonunda YALNIZ kendi açtığı boş/atfedilebilir dizini siler;
sonuç `ithal_yan_etkisi` alanında ADIYLA durur. Silinemeyen hâl UYDURULMAZ, nedeniyle yazılır.

AĞA ÇIKILMAZ. `meridian.obs` İTHAL EDİLMEZ. Alt süreç YOKTUR. Bekleme döngüsü YOKTUR.

KOMUT SATIRI (sözleşme burasıdır, `main()` değil — CLAUDE.md §1):
    cd <depo kökü> && .venv/bin/python research/olcumler/edg093_midcap_pit/k093.py \\
        --repo <kök> --kohort <sp400_uyelik_tarihi.csv> --bars-dir <bars/> \\
        --shares <shares_outstanding_sp400.csv.gz> --cikti <dizin> [--kapsama <harita.json>]
Çıkış kodu: 0 = sonuç yazıldı · 2 = kullanım hatası (eksik/bozuk girdi).

MODÜL DÜZEYİ TEMİZDİR: argparse `main()` içinde kurulur, G/Ç yoktur, `meridian` ithal
edilmez — ithal etmek bir koşum TETİKLEMEZ (çiviler bu yüzden fonksiyonları doğrudan çağırır).
"""
from __future__ import annotations

import argparse
import bisect
import datetime as dt
import hashlib
import json
import pathlib
import random
import shutil
import sys

KART_ID = "EDG-2026-093"
KART_ADI = "EDG-2026-093-midcap-pit-kohort-sagkalan-ust-sinir.yaml"
HUKUM = "YOK — Rol-1"

#: `--belirsiz` sözlüğü. `dahil` = kohort defteri AYNEN (ADIM-0 A'nın dondurduğu hâl, kartın
#: blob'u); `haric` = belirsiz isimler TÜM günlerden düşürülür; `ikisi` = ikisi de koşar ve
#: BİRİNCİL `dahil`dir (defterin kendisi budur), `haric` DUYARLILIKTIR.
BELIRSIZ_KIPLERI = ("dahil", "haric", "ikisi")
BIRINCIL_KIP = "dahil"

#: PK-2 doğrulama tablosunun satır sayısı — kart `pozitif_kontrol` (2) lafzı ("rastgele 20
#: kohort-gün"). PK-3'ün düşürdüğü isim sayısı kart lafzı ("bilinçli 10 isim").
PK2_SATIR_N = 20
PK3_DUSEN_N = 10

#: A1 ÖLÇÜMÜ (2026-09-14, ADIM-0 EKSEN B): Alpaca IEX barları 2020-07-27'den başlıyor. 21 günlük
#: medyan hacim + rvol20 + mom21 ısınması yüzünden ETKİN ölçüm penceresi ~2020-09'dan başlar.
#: Bu bir VARSAYIM DEĞİL, ölçülen tabandır; gerçek etkin başlangıç panelden AYRICA ölçülür ve
#: `evren_muhasebesi.etkin_baslangic_olculen` alanına yazılır — ikisi yan yana durur.
ISINMA_NOTU = (
    "Alpaca IEX bar tabanı 2020-07-27 (A1 ölçümü 2026-09-14, ADIM-0 EKSEN B kapsama haritası). "
    "turnover21 = medyan21(hacim)/shares, rvol20 ve mom21 ısınma ister; bu yüzden kohort "
    "penceresi 2020-07-27'de başlasa da ETKİN ölçüm penceresi ~2020-09'dan başlar. Ölçülen "
    "etkin başlangıç `etkin_baslangic_olculen` alanındadır — beyan ile ölçüm AYNI piksele "
    "düşmez.")


# =================================================================================================
# 0. KULLANIM HATASI / KÜÇÜK YARDIMCILAR
# =================================================================================================
def kullanim_hatasi(mesaj: str) -> None:
    """Kullanım hatası = çıkış 2 (argparse ile AYNI kod); neden stderr'e ADIYLA yazılır."""
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


# =================================================================================================
# 1. İTHAL YÜZEYİ — wp2 (EDG-016) ve Parti-1 modülleri KAYNAKTAN yüklenir (v334)
# =================================================================================================
def _yukleyici(repo: pathlib.Path):
    """`ops.sasi_yukleyici.kaynaktan_yukle` — ham `exec_module` YASAK (v334 §C).

    `sys.path` eki BİLİNÇLİDİR: bu betik DOĞRUDAN koşulur, o zaman `sys.path[0]` BU dizindir ve
    `ops.` ön eki editable-install `.pth`i üzerinden BAŞKA BİR CHECKOUT'a düşerdi (hafıza:
    worktree-pythonpath-tuzagi). Kök AÇIK verilir ve çözülen yol künyeye yazılır."""
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    from ops.sasi_yukleyici import kaynaktan_yukle
    return kaynaktan_yukle


def ithal_yuzeyi(repo: pathlib.Path, cikti: pathlib.Path, bars_dir: pathlib.Path,
                 defter: pathlib.Path | None) -> dict:
    """wp2 `ortak`/`pk`/`k016` + Parti-1 `ortak` yüklenir; `meridian.config` ÇIKTIYA çevrilir.

    SIRA ZORUNLUDUR: `ortak` ve `pk` ÖNCE `sys.modules`a KAYNAKTAN derlenmiş hâlleriyle
    yazılır; k016'nın `import ortak as O` / `import pk as PK` satırları onları bulur ve
    standart ithal makinesinin `__pycache__` yolu HİÇ devreye girmez (v334'ün kapattığı sınıf).
    """
    yukle = _yukleyici(repo)
    wp2 = repo / "research" / "olcumler" / "wp2_olcum"
    if not (wp2 / "k016.py").exists():
        kullanim_hatasi(f"emsal ölçüm kodu bulunamadı: {wp2 / 'k016.py'} (--repo yanlış olabilir)")

    onceki = {ad: (wp2 / ad).exists() for ad in ("_cache", "_state")}
    if str(wp2) not in sys.path:
        sys.path.insert(0, str(wp2))

    # `meridian` ÖNCE ve `--repo`DAN ithal edilir. Gerekçe ÖLÇÜLDÜ: wp2 `ortak.py` modül
    # düzeyinde MUTLAK bir depo yolunu (`/Users/.../AI-Trading`) `sys.path`in BAŞINA koyup
    # `from meridian import config` yapar — worktree'den koşulduğunda motor ANA CHECKOUT'tan
    # yüklenirdi ve ölçüm, ölçtüğünü sandığı ağaçtan BAŞKA bir ağacın koduyla koşardı (hafıza:
    # worktree-pythonpath-tuzagi). Burada ithal edilince `sys.modules` doludur ve wp2'nin
    # satırı ÖNBELLEKTEN alır. Çözülen yol künyeye yazılır — iddia değil ölçüm.
    from meridian import config
    from meridian.adapters import data as dat

    try:
        O = yukle(wp2 / "ortak.py", "ortak", sys_modules_kaydet=True)
    except OSError as e:
        # sessiz-yutma DEĞİL: wp2 `ortak.py` MODÜL DÜZEYİNDE kendi dizinine `_cache/` açar; o
        # dizin yazılamazsa (A1'de /opt/meridian salt-okunur olabilir) hata ham yığın izi olarak
        # düşerdi. Neden ve ÇÖZÜM adıyla verilir; sessizce başka bir yola düşülmez.
        kullanim_hatasi(
            f"wp2 emsal altyapısı yüklenemedi ({type(e).__name__}: {e}). `ortak.py` modül "
            f"düzeyinde `{wp2}/_cache` ve `_state` dizinlerini AÇAR — o dizin yazılabilir "
            f"olmalı. Çözüm: dizne yazma izni ver, ya da `research/olcumler/wp2_olcum/`u "
            f"yazılabilir bir kopyaya alıp `--repo`yu o kopyanın köküne göster.")
    PK = yukle(wp2 / "pk.py", "pk", sys_modules_kaydet=True)
    k016 = yukle(wp2 / "k016.py", "k016_edg093")
    p1 = yukle(repo / "research" / "olcumler" / "edg093_midcap_pit" / "ortak.py",
               "edg093_ortak_k093")

    state = cikti / "_state"
    state.mkdir(parents=True, exist_ok=True)
    config.STATE = state
    config.HISTORY = state / "history"
    config.BARS = bars_dir

    defter_kaydi = {"yol": None, "sha256": None, "kopyalandi": False,
                    "neden": "--defter verilmedi → bars_integrity defteri YOK; `measurement_bars` "
                             "hiçbir dönemi dışlamaz. EDG-016 turunda defter VARDI (canlı "
                             "S&P 500 sembolleri); bu kohortun sembolleri o defterde yok — "
                             "dışlama farkı `bar_muhasebesi.defter_yolu_dusen` ile ölçülür."}
    if defter is not None:
        d = pathlib.Path(defter)
        if not d.exists():
            kullanim_hatasi(f"--defter dosyası yok: {d}")
        shutil.copy2(d, state / dat.INTEGRITY_FILE)
        defter_kaydi = {"yol": str(d), "sha256": _sha256(d), "kopyalandi": True, "neden": None}

    import meridian
    return {"O": O, "PK": PK, "k016": k016, "p1": p1, "config": config, "dat": dat,
            "wp2_dizin": wp2, "wp2_onceki_durum": onceki, "defter": defter_kaydi,
            "state": state,
            "cozulen_yollar": {
                "repo": str(repo),
                "meridian": str(pathlib.Path(meridian.__file__).resolve().parent),
                "meridian_repo_icinde_mi": bool(
                    pathlib.Path(meridian.__file__).resolve().parent.parent == repo),
                "wp2_ortak": str(pathlib.Path(O.__file__).resolve()),
                "k016": str(pathlib.Path(k016.__file__).resolve()),
                "parti1_ortak": str(pathlib.Path(p1.__file__).resolve()),
                "config_state": str(state), "config_bars": str(bars_dir)}}


def ithal_yan_etkisini_geri_al(yuzey: dict) -> dict:
    """wp2 ithalinin açtığı `_cache`/`_state` dizinlerini — YALNIZ bu koşum açtıysa — siler.

    NEDEN: bu dizinler ithal edilen dosyanın MODÜL DÜZEYİNDE açtığı dizinlerdir, ölçümün ürünü
    DEĞİLdir. `_cache` .gitignore'ludur ama `_state` DEĞİLDİR: bırakılırsa Rol-1'in
    `git status --porcelain` kapısını (dagit ön şartı) kirletir. Silme KOŞULLUDUR — dizin
    koşumdan ÖNCE yoksa VE içeriği atfedilebilir kümedeyse. Aksi hâl UYDURULMAZ: dokunulmaz ve
    `neden` yazılır."""
    atfedilebilir = {"bars_integrity.json", "history"}
    out = {}
    for ad, vardi in yuzey["wp2_onceki_durum"].items():
        yol = yuzey["wp2_dizin"] / ad
        if vardi:
            out[ad] = {"koşumdan_once_vardi": True, "silindi": False,
                       "neden": "koşumdan ÖNCE vardı — dokunulmadı"}
            continue
        if not yol.exists():
            out[ad] = {"koşumdan_once_vardi": False, "silindi": False,
                       "neden": "ithal bu dizini açmadı"}
            continue
        icerik = {p.name for p in yol.iterdir()}
        if not icerik <= atfedilebilir:
            out[ad] = {"koşumdan_once_vardi": False, "silindi": False,
                       "icerik": sorted(icerik),
                       "neden": "içerik atfedilebilir kümenin DIŞINDA — silinmedi (başka bir "
                                "koşum yazmış olabilir); Rol-1 bakar"}
            continue
        try:
            shutil.rmtree(yol)
            out[ad] = {"koşumdan_once_vardi": False, "silindi": True,
                       "icerik": sorted(icerik), "neden": None}
        except OSError as e:
            # sessiz-yutma DEĞİL: silme düştü — hâl ADIYLA kayda geçer, "temiz" diye yazılmaz
            out[ad] = {"koşumdan_once_vardi": False, "silindi": False,
                       "neden": f"silinemedi ({type(e).__name__}: {e})"}
    return out


# =================================================================================================
# 2. KOHORT — AS-OF ÜYELİK (Parti-1 sözleşmesi; adım fonksiyonu)
# =================================================================================================
def etkin_satirlar(p1, kohort_csv: pathlib.Path, baslangic: dt.date, bitis: dt.date):
    """(etkin as-of satırları, çapa var mı, ham satır sayısı) — Parti-1 `ortak` sözleşmesiyle.

    Pencere başından ÖNCEKİ son satır bir ÇAPAdır ve tarihi pencere başına KIRPILIR; bu kural
    `ortak.pencere_satirlari`nındır ve burada YENİDEN YAZILMAZ."""
    satirlar = p1.kohort_oku(pathlib.Path(kohort_csv))
    etkin, capa = p1.pencere_satirlari(satirlar, baslangic, bitis)
    if not etkin:
        kullanim_hatasi(f"pencerede ({baslangic} → {bitis}) as-of satırı yok: {kohort_csv}")
    return etkin, capa, len(satirlar)


def uyelik_haritasi(etkin, gunler: list[str], dusur: frozenset[str] = frozenset()) -> dict:
    """gün → o gün ÜYE sembol kümesi. As-of adım fonksiyonu: t'den küçük-eşit SON satır.

    `dusur` kümesi (belirsiz isimler) TÜM günlerden çıkarılır — `haric` duyarlılık koşumu budur.
    Gözlem günü ilk satırdan ÖNCE ise o gün ÜYE YOKTUR (uydurma yasağı: geriye taşınmaz)."""
    tarihler = [d.isoformat() for d, _ in etkin]
    kumeler = [k - dusur if dusur else k for _, k in etkin]
    out = {}
    for g in gunler:
        i = bisect.bisect_right(tarihler, g) - 1
        out[g] = kumeler[i] if i >= 0 else frozenset()
    return out


def belirsiz_isimler(esleme_yaml: pathlib.Path) -> tuple[frozenset[str], str, str | None]:
    """(belirsiz sembol kümesi, kaynak, neden) — ELLE EŞLEME TABLOSUNDAN türetilir, koda GÖMÜLMEZ.

    Kaynak `karar: belirsiz` satırlarının `satir.etkisiz_semboller` alanıdır (ADIM-0 A'nın
    ürettiği tablo; kartın `adim_0a_hukmu` bloğu aynı 8 ismi anar). İkinci bir liste tutmak,
    tablo değiştiğinde sessizce ayrışırdı (tek-kaynak yasası)."""
    yol = pathlib.Path(esleme_yaml)
    if not yol.exists():
        return frozenset(), "türetilemedi", f"elle eşleme tablosu yok: {yol}"
    try:
        import yaml
        tablo = yaml.safe_load(yol.read_text(encoding="utf-8"))
    except (OSError, ImportError, ValueError) as e:
        # sessiz-yutma DEĞİL: tablo okunamadı — küme UYDURULMAZ, neden ADIYLA döner
        return frozenset(), "türetilemedi", f"eşleme tablosu okunamadı ({type(e).__name__}: {e})"
    if not isinstance(tablo, list):
        return frozenset(), "türetilemedi", f"eşleme tablosu liste değil: {yol}"
    isimler = set()
    for kayit in tablo:
        if not isinstance(kayit, dict) or str(kayit.get("karar")) != "belirsiz":
            continue
        for s in (kayit.get("satir") or {}).get("etkisiz_semboller") or []:
            isimler.add(str(s).upper().strip())
    return (frozenset(isimler),
            f"türetildi: {yol} — `karar: belirsiz` satırlarının `satir.etkisiz_semboller` alanı",
            None)


# =================================================================================================
# 3. BAR YÜKLEME — CANLI BORU HATTININ KENDİ FONKSİYONLARIYLA
# =================================================================================================
def barlari_yukle(isimler, bars_dir: pathlib.Path, p1, O, dat, pd):
    """(sembol → temiz bar df, muhasebe). EDG-016 `load_bars` ile AYNI adımlar, tek fark
    evrenin `REPLAY_UNIVERSE` yerine KOHORT olması ve dosyaların `--bars-dir`den gelmesi.

    `integrity_safe_start` (HESAPLANAN yol) UYGULANMAZ ama ÖLÇÜLÜR: kaç satırı dışlayacağı
    sayılır ve muhasebeye yazılır. Gerekçe kartın kendisidir — bu kohortun bütünlük defteri
    YOKTUR; uygulanan dışlama ile ölçülen dışlamanın yan yana durması "bedel yasası"dır
    (kazanç ölçülüp bedel ölçülmezse körlük sessizdir)."""
    per = {}
    acc = {"istenen": 0, "dosya_yok": 0, "okunamadi": 0, "kisa": 0, "yuklendi": 0,
           "hayalet_dusen": 0, "karantina_dusen": 0, "takvim_reddedilen": [],
           "defter_yolu_dusen": 0, "defter_yolu_sembol": 0,
           "hesaplanan_dislanan_satir_UYGULANMADI": 0, "hesaplanan_dislanan_sembol": 0,
           "kirilma_sinifi": {}, "kisa_semboller": [], "dosya_yok_semboller": [],
           "okunamadi_semboller": [], "bar_min_uzunluk": int(O.BAR_MIN_UZUNLUK)}
    for t in sorted(isimler):
        acc["istenen"] += 1
        cp = pathlib.Path(bars_dir) / f"{p1.bar_dosya_adi(t)}.csv"
        if not cp.exists():
            acc["dosya_yok"] += 1
            acc["dosya_yok_semboller"].append(t)
            continue
        try:
            raw = pd.read_csv(cp, parse_dates=["date"])
            df, rep = dat.sanitize_bars(raw, t)
        except (OSError, ValueError, KeyError) as e:
            # sessiz-yutma DEĞİL: bar okunamadı — sembol ADIYLA sayılır, sessizce düşmez
            acc["okunamadi"] += 1
            acc["okunamadi_semboller"].append(f"{t}: {type(e).__name__}: {e}")
            continue
        acc["hayalet_dusen"] += int(rep.get("ghost_session_dropped") or 0)
        acc["karantina_dusen"] += int(rep.get("unadjusted_quarantined") or 0)
        if rep.get("calendar_mismatch_rows"):
            acc["takvim_reddedilen"].append(t)

        n_once = len(df)
        df = dat.measurement_bars(df, t)                      # KANONİK defter yolu
        d_defter = n_once - len(df)
        acc["defter_yolu_dusen"] += d_defter
        acc["defter_yolu_sembol"] += int(d_defter > 0)

        try:                                                  # HESAPLANAN yol — ÖLÇÜLÜR, UYGULANMAZ
            ss, brk = dat.integrity_safe_start(df)
        except (ValueError, KeyError, IndexError) as e:
            # sessiz-yutma DEĞİL: bütünlük taraması düştü — sembol sayılır, ölçüm durmaz
            ss, brk = None, []
            acc["okunamadi_semboller"].append(f"{t}: integrity {type(e).__name__}: {e}")
        for b in (brk or []):
            k = b.get("sinif", "?")
            acc["kirilma_sinifi"][k] = acc["kirilma_sinifi"].get(k, 0) + 1
        if ss:
            ek = int((~(df["date"].astype(str).str.slice(0, 10) >= ss)).sum())
            acc["hesaplanan_dislanan_satir_UYGULANMADI"] += ek
            acc["hesaplanan_dislanan_sembol"] += int(ek > 0)

        if df is None or len(df) < O.BAR_MIN_UZUNLUK:
            acc["kisa"] += 1
            acc["kisa_semboller"].append(t)
            continue
        per[t] = df.reset_index(drop=True)
        acc["yuklendi"] += 1
    acc["takvim_reddedilen_n"] = len(acc["takvim_reddedilen"])
    return per, acc


# =================================================================================================
# 4a. VERİ HAZIRLIĞI — barlar + hisse serisi + HAM panel (ÜYELİK SÜZGECİ YOK)
# =================================================================================================
def veri_hazirla(isimler, bars_dir: pathlib.Path, shares_csv: pathlib.Path,
                 yuzey: dict, np, pd) -> dict:
    """Pahalı adımlar (661 bar csv'si, split takvimi, as-of seri, ham panel) BİR KEZ koşar.

    Üyelik süzgeci BURADA UYGULANMAZ: `dahil` ve `haric` koşumları AYNI ham panelden türer,
    yoksa iki koşum aynı barları iki kez okur ve ikisinin AYNI veriden geldiği bir VARSAYIM
    olurdu (duyarlılık okuması tam da bunu varsayamaz)."""
    O, k016, p1, dat = yuzey["O"], yuzey["k016"], yuzey["p1"], yuzey["dat"]

    per, bar_acc = barlari_yukle(isimler, bars_dir, p1, O, dat, pd)
    if not per:
        return {"DURUM": "OLCULEMEDI", "bar_muhasebesi": bar_acc,
                "neden": "hiçbir sembolün kullanılabilir bar serisi yok"}
    pan = O.bar_paneli(per)

    S = pd.read_csv(shares_csv)
    if "start" in S.columns:
        S["start"] = S["start"].fillna("")
    eksik = [k for k in ("symbol", "tag", "unit", "val", "filed", "donem_turu")
             if k not in S.columns]
    if eksik:
        kullanim_hatasi(f"--shares csv'sinde zorunlu kolon(lar) yok: {eksik} ({shares_csv})")
    ser, birincil, sh_acc = O.build_hisse(S)
    fiz = O.fiziksel_bekci(ser, pan)
    sh_acc["fiziksel_bekci"] = fiz
    # `build_hisse` muhasebesindeki `seri_olmayan_sembol` REPLAY_UNIVERSE'e göre hesaplanır
    # (EDG-016 evreni). Bu kohort için o sayı ANLAMSIZDIR — DÜZELTİLİR ve ikisi de yazılır.
    sh_acc["seri_olmayan_sembol_REPLAY_UNIVERSE_n"] = len(sh_acc.pop("seri_olmayan_sembol", []))
    sh_acc["seri_olmayan_sembol_KOHORT"] = sorted(set(pan) - set(birincil))
    sh_acc["seri_olmayan_sembol_KOHORT_n"] = len(sh_acc["seri_olmayan_sembol_KOHORT"])

    OBS = O.ortak_takvim(pan)
    D_ham, pacc = k016.panel(pan, ser, OBS)                   # GÖVDE k016'NIN — kopya YOK
    return {"DURUM": "HAZIR", "pan": pan, "ser": ser, "OBS": OBS, "D_ham": D_ham,
            "gunler": sorted(set(str(x) for x in OBS)),
            "bar_muhasebesi": bar_acc,
            "hisse_muhasebesi": {k: v for k, v in sh_acc.items() if k != "split_takvimi"},
            "split_takvimi_muhasebesi": {k: v for k, v in (sh_acc.get("split_takvimi") or {}).items()
                                         if not isinstance(v, list)},
            "panel_muhasebesi": {k: v for k, v in pacc.items() if k != "bayat_seri_sembol"},
            "_pacc": pacc, "_fiz": fiz}


# =================================================================================================
# 4b. KATMANLAR — EDG-016 blokları, ithal çekirdek ve SABİTLERLE
# =================================================================================================
def katmanlari_olc(kip: str, hazir: dict, uyelik: dict, yuzey: dict, np, pd) -> dict:
    """Bir evren için katman i/ii/iii/iv. `kip` yalnız etikettir — hesap AYNIDIR."""
    O, k016 = yuzey["O"], yuzey["k016"]
    pan, ser, OBS = hazir["pan"], hazir["ser"], hazir["OBS"]
    D_ham, pacc, fiz, bar_acc = (hazir["D_ham"], hazir["_pacc"], hazir["_fiz"],
                                 hazir["bar_muhasebesi"])

    # ---------- TEK FARK: AS-OF ÜYELİK SÜZGECİ ----------
    d_arr = D_ham["date"].to_numpy()
    t_arr = D_ham["ticker"].to_numpy()
    uye = np.fromiter((t in uyelik.get(d, frozenset()) for d, t in zip(d_arr, t_arr)),
                      dtype=bool, count=len(D_ham))
    D = D_ham.loc[uye].reset_index(drop=True)
    uyelik_acc = {
        "tanim": "bir (t, isim) hücresi ancak isim t gününde AS-OF ÜYE ise panele girer — "
                 "EDG-016'dan TEK FARK budur (orada evren SABİT REPLAY_UNIVERSE listesiydi).",
        "panel_satir_suzgecten_once": int(len(D_ham)),
        "panel_satir_uye": int(len(D)),
        "dusen_satir_uye_degil": int(len(D_ham) - len(D)),
        "gozlem_gunu_suzgecten_once": int(D_ham["date"].nunique()),
        "gozlem_gunu_uye": int(D["date"].nunique()) if len(D) else 0,
        "sembol_suzgecten_once": int(D_ham["ticker"].nunique()),
        "sembol_uye": int(D["ticker"].nunique()) if len(D) else 0,
    }
    # OKUYAN (Yasa 6): Rol-1 — "hangi isim HANGİ günler ölçüme girdi" sorusunun cevabı; PK-2'nin
    # elle doğrulaması ve PIT tartışması bu aralıklardan yürür. Çivi (v490) giriş/çıkış günlerini
    # tam BURADAN ölçer: üyelik süzgeci kalkarsa aralıklar pencerenin tamamına yayılır.
    if len(D):
        ara = D.groupby("ticker")["date"].agg(["min", "max", "size"])
        uyelik_acc["olculen_semboller"] = sorted(ara.index.astype(str).tolist())
        uyelik_acc["sembol_uye_gun_araligi"] = {
            str(s): {"ilk": str(r["min"]), "son": str(r["max"]), "gun_n": int(r["size"])}
            for s, r in ara.iterrows()}
    else:
        uyelik_acc["olculen_semboller"] = []
        uyelik_acc["sembol_uye_gun_araligi"] = {}
    if D.empty:
        return {"kip": kip, "DURUM": "OLCULEMEDI", "bar_muhasebesi": bar_acc,
                "uyelik_suzgeci": uyelik_acc, "neden": "üyelik süzgecinden sonra panel BOŞ"}

    # ---------- PIT SIZINTI — ÖLÇÜLEN satırlar üzerinde (üye günler) ----------
    sizinti, sizinti_sembol = 0, 0
    for sym, g in D.groupby("ticker"):
        s = ser.get(sym)
        if s is None:
            continue
        _sh, f, _nd = s.asof(g["date"].to_numpy())
        n = O._leak_kontrol(f, g["date"].to_numpy())
        sizinti += n
        sizinti_sembol += int(n > 0)

    # ---------- tabanlar: AYNI-GÜN KOHORT ortalaması ----------
    tab = {}
    for h in k016.HORIZONS:
        tab[h] = D[["date", f"fwd{h}"]].dropna().groupby("date")[f"fwd{h}"].mean()

    # ---------- kesit (k016 ile birebir) ----------
    V = D[D["turnover21"].notna() & D["rvol20"].notna() & D["mom21"].notna()].copy()
    kesit = V.groupby("date").size()
    kullanilan = kesit[kesit >= O.MIN_KESIT].index
    V = V[V["date"].isin(kullanilan)].copy()
    if V.empty:
        return {"kip": kip, "DURUM": "OLCULEMEDI", "bar_muhasebesi": bar_acc,
                "uyelik_suzgeci": uyelik_acc,
                "neden": f"hiçbir günün kesiti {O.MIN_KESIT} sembole ulaşmadı"}
    V["to_pct"] = V.groupby("date")["turnover21"].rank(pct=True, method="first")
    V["rvol_pct"] = V.groupby("date")["rvol20"].rank(pct=True, method="first")
    V["mom_pct"] = V.groupby("date")["mom21"].rank(pct=True, method="first")
    V["ust"] = V["to_pct"] > 1 - k016.UST_PCT
    V["b_rvol"] = np.clip((V["rvol_pct"] * k016.KONTROL_DILIM).astype(int), 0, k016.KONTROL_DILIM - 1)
    V["b_mom"] = np.clip((V["mom_pct"] * k016.KONTROL_DILIM).astype(int), 0, k016.KONTROL_DILIM - 1)
    V["kova"] = V["b_rvol"] * k016.KONTROL_DILIM + V["b_mom"]
    kk = kesit[kesit >= O.MIN_KESIT]
    kesit_acc = {
        "gozlem_gunu_toplam": int(D["date"].nunique()),
        "kesit_yeterli_gun": int(len(kullanilan)), "min_kesit": int(O.MIN_KESIT),
        "kesit_buyuklugu": {"medyan": O._r6(kk.median()), "min": int(kk.min()),
                            "maks": int(kk.max())},
        "tarih_araligi": [str(V["date"].min()), str(V["date"].max())],
        "n_satir": int(len(V)), "n_sembol": int(V["ticker"].nunique()),
        "turnover21_dagilimi": {str(q): O._r6(V["turnover21"].quantile(q))
                                for q in (0.01, 0.25, 0.5, 0.75, 0.99)},
        "kova_buyuklugu": {"medyan": O._r6(V.groupby(["date", "kova"]).size().median()),
                           "n_kova": int(k016.KONTROL_DILIM ** 2)},
    }

    orn = V[["turnover21", "rvol20", "mom21"]].sample(n=min(200000, len(V)), random_state=11)
    akrabalik = {
        "not": "rvol20 ZATEN skorda; kontrol değişkenleriyle akrabalık beyan edilir (EDG-016).",
        "n_ornek": int(len(orn)),
        "spearman_turnover_rvol20": O._r6(O.spearman_np(orn["turnover21"], orn["rvol20"])),
        "spearman_turnover_mom21": O._r6(O.spearman_np(orn["turnover21"], orn["mom21"])),
    }

    # ================= I. KATMAN — turnover_ust20, KOHORT tabanı =================
    sub = V[V["ust"]]
    kat1 = {"n_sembol_gun": int(len(sub)), "n_gun": int(sub["date"].nunique()),
            "n_sembol": int(sub["ticker"].nunique()),
            "taban_tanimi": "aynı-gün KOHORT (as-of üye) ortalaması. EDG-016'da bu taban SABİT "
                            "evrenin ortalamasıydı; şema anahtarı (`evren_fazlasi`) kıyas "
                            "yapılabilsin diye KORUNDU, tanım burada kohorttur.",
            "turnover21_medyan": O._r6(sub["turnover21"].median()),
            "turnover21_ort": O._r6(sub["turnover21"].mean()),
            "mom21_ort": O._r6(sub["mom21"].mean()), "rvol20_ort": O._r6(sub["rvol20"].mean()),
            "ufuklar": {}}
    for h in k016.HORIZONS:
        s2 = sub[["date", f"fwd{h}"]].dropna()
        y = s2[f"fwd{h}"].to_numpy(float)
        dts = s2["date"].to_numpy()
        base = s2["date"].map(tab[h]).to_numpy(float)
        ok = np.isfinite(base)
        kat1["ufuklar"][str(h)] = {"ham": O.mean_with_ci(y, dts),
                                   "evren_fazlasi": O.mean_with_ci((y - base)[ok], dts[ok])}

    # ================= II. KATMAN — ARTIK (kontrol: rvol20 × mom21) =================
    art = {"kontrol": f"rvol20 terzili × mom21 terzili (gün bazlı kesit), "
                      f"{k016.KONTROL_DILIM ** 2} kova"}
    a1 = {"tanim": "KAYITLI dilim (turnover üst %20) — taban AYNI-GÜN AYNI-KOVA leave-one-out "
                   "ortalaması. Katman 1 ile TEK farkı tabandır.", "ufuklar": {}}
    for h in k016.HORIZONS:
        g = V[["date", "kova", "ust", f"fwd{h}"]].dropna(subset=[f"fwd{h}"]).copy()
        grp = g.groupby(["date", "kova"])[f"fwd{h}"]
        n_k = grp.transform("size").to_numpy(float)
        s_k = grp.transform("sum").to_numpy(float)
        yv = g[f"fwd{h}"].to_numpy(float)
        with np.errstate(divide="ignore", invalid="ignore"):
            loo = (s_k - yv) / (n_k - 1.0)
            ici = s_k / n_k
        yeter = n_k >= k016.KOVA_MIN
        m = g["ust"].to_numpy(bool) & yeter & np.isfinite(loo)
        a1["ufuklar"][str(h)] = {
            "kova_yetersiz_dusen_satir": int((~yeter).sum()),
            "loo_kova_fazlasi": O.mean_with_ci(yv[m] - loo[m], g["date"].to_numpy()[m]),
            "kendini_iceren_kova_fazlasi_ort_CI_YOK": O._r6(float(np.mean(
                (yv - ici)[g["ust"].to_numpy(bool) & yeter]))),
        }
    art["A1_kova_tabanli_ust20_fazlasi"] = a1

    a2 = {"tanim": "EDG-007 çift-sıralama şablonu: her kontrol kovasında O KOVANIN turnover üst "
                   "%20'si vs kalanı; hücre farkları + kova-içi merkezlenmiş havuzlanmış yayılım.",
          "ufuklar": {}}
    V["to_pct_kova"] = V.groupby(["date", "kova"])["turnover21"].rank(pct=True, method="first")
    V["ust_kova"] = V["to_pct_kova"] > 1 - k016.UST_PCT
    for h in k016.HORIZONS:
        g = V[["date", "kova", "b_rvol", "b_mom", "ust_kova", f"fwd{h}"]] \
            .dropna(subset=[f"fwd{h}"]).copy()
        grp = g.groupby(["date", "kova"])[f"fwd{h}"]
        n_k = grp.transform("size").to_numpy(float)
        s_k = grp.transform("sum").to_numpy(float)
        yv = g[f"fwd{h}"].to_numpy(float)
        with np.errstate(divide="ignore", invalid="ignore"):
            loo = (s_k - yv) / (n_k - 1.0)
        yeter = n_k >= k016.KOVA_MIN
        g = g.assign(_merkezli=yv - loo, _yeter=yeter)
        hucre = {}
        for kv, gg in g[g["_yeter"]].groupby("kova"):
            hi = gg[gg["ust_kova"]]
            lo = gg[~gg["ust_kova"]]
            ad = f"rvol_t{int(gg['b_rvol'].iloc[0]) + 1}_mom_t{int(gg['b_mom'].iloc[0]) + 1}"
            if len(hi) < O.MIN_SLICE or len(lo) < O.MIN_SLICE:
                hucre[str(int(kv))] = {"ad": ad, "n_yuksek": int(len(hi)), "n_kalan": int(len(lo)),
                                       "fark": None, "ci": None, "anlamli": None,
                                       "neden": f"dilim < {O.MIN_SLICE}"}
                continue
            r = O.fark_with_ci(hi[f"fwd{h}"].to_numpy(float), hi["date"].to_numpy(),
                               lo[f"fwd{h}"].to_numpy(float), lo["date"].to_numpy())
            r["ad"] = ad
            r["ort_yuksek"] = O._r6(hi[f"fwd{h}"].mean())
            r["ort_kalan"] = O._r6(lo[f"fwd{h}"].mean())
            hucre[str(int(kv))] = r
        gy = g[g["_yeter"]]
        hi, lo = gy[gy["ust_kova"]], gy[~gy["ust_kova"]]
        hav = O.fark_with_ci(hi["_merkezli"].to_numpy(float), hi["date"].to_numpy(),
                             lo["_merkezli"].to_numpy(float), lo["date"].to_numpy())
        hav["aciklama"] = ("kova-içi (leave-one-out) MERKEZLENMİŞ getirilerde üst%20 − kalan: "
                           "kova bileşimi farkından arınmış havuzlanmış yayılım")
        a2["ufuklar"][str(h)] = {"kovalar": hucre, "havuzlanmis": hav}
    art["A2_edg007_kova_ici_ust20_eksi_kalan"] = a2

    # --- B: ARTIK-IC (gün bazlı kesit OLS artığı) ---
    e = np.full(len(V), np.nan)
    ortog = {"maks_mutlak_kova_korelasyon": None, "maks_mutlak_gun_ici_ortalama": None,
             "tekil_gun": 0, "gun": 0}
    x_all = V["to_pct"].to_numpy(float)
    z1_all = V["rvol_pct"].to_numpy(float)
    z2_all = V["mom_pct"].to_numpy(float)
    kod = V["date"].to_numpy()
    _, inv = np.unique(kod, return_inverse=True)
    order = np.argsort(inv, kind="stable")
    cnt = np.bincount(inv)
    start = np.concatenate([[0], np.cumsum(cnt)[:-1]])
    for gi in range(len(cnt)):
        ii = order[start[gi]:start[gi] + cnt[gi]]
        if len(ii) < 4:
            ortog["tekil_gun"] += 1
            continue
        A = np.column_stack([np.ones(len(ii)), z1_all[ii], z2_all[ii]])
        try:
            beta, *_ = np.linalg.lstsq(A, x_all[ii], rcond=None)
        except np.linalg.LinAlgError:
            # sessiz-yutma DEĞİL: tekil gün SAYILIR ve `tekil_gun` alanında raporlanır
            ortog["tekil_gun"] += 1
            continue
        e[ii] = x_all[ii] - A @ beta
        ortog["gun"] += 1
    V["artik"] = e
    okv = V[["date", "artik", "rvol_pct", "mom_pct"]].dropna()
    c1, c2, m0 = [], [], []
    for _, gg in okv.groupby("date"):
        if len(gg) < 10:
            continue
        a = gg["artik"].to_numpy()
        c1.append(abs(np.corrcoef(a, gg["rvol_pct"].to_numpy())[0, 1]))
        c2.append(abs(np.corrcoef(a, gg["mom_pct"].to_numpy())[0, 1]))
        m0.append(abs(a.mean()))
    if c1 and c2 and m0:
        ortog["maks_mutlak_kova_korelasyon"] = O._r6(max(max(c1), max(c2)))
        ortog["maks_mutlak_gun_ici_ortalama"] = O._r6(max(m0))
        ortog["gecti"] = bool(max(max(c1), max(c2)) < 1e-8 and max(m0) < 1e-8)
    else:
        ortog["gecti"] = None
        ortog["neden"] = "ortogonallik okuması için ≥10 üyeli gün yok — ÖLÇÜLEMEDİ"
    ortog["tanim"] = ("gün bazlı OLS artığı: kontrol değişkenlerine kesit-içi TAM dik ve gün-içi "
                      "ortalaması 0 olmalı; değilse artıklaştırma yapılmamıştır")

    icb = {"tanim": "havuzlanmış Spearman IC. HEADLINE: artık ↔ FAZLA getiri (kohort tabanı "
                    "düşülmüş). Ham getiriye karşı okuma TANI (CI'sız).", "ufuklar": {}}
    for h in k016.HORIZONS:
        g = V[["date", "artik", "to_pct", f"fwd{h}"]].dropna().copy()
        base = g["date"].map(tab[h]).to_numpy(float)
        ok = np.isfinite(base)
        g = g[ok].copy()
        fz = g[f"fwd{h}"].to_numpy(float) - base[ok]
        dts = g["date"].to_numpy()
        icb["ufuklar"][str(h)] = {
            "artik_ic_fazla": k016.ic_hizli(g["artik"].to_numpy(float), fz, dts),
            "ham_turnover_ic_fazla": k016.ic_hizli(g["to_pct"].to_numpy(float), fz, dts),
            "artik_ic_HAM_getiri_TANI_CI_YOK": k016.ic_hizli(
                g["artik"].to_numpy(float), g[f"fwd{h}"].to_numpy(float), dts, ci=False),
        }
    art["B_artik_ic"] = icb
    art["artik_ortogonallik_bekcisi"] = ortog

    # ================= III. MALİYET-SONRASI NET =================
    c1_ = O.MALIYET_BPS / 10000.0
    c2_ = 2 * O.MALIYET_BPS / 10000.0

    def net(blok, c):
        if blok.get("ort") is None or not blok.get("ci"):
            return {"brut": blok.get("ort"), "net": None, "ci": None,
                    "neden": blok.get("neden") or "brüt ölçülemedi"}
        return {"brut": blok["ort"], "maliyet": O._r6(c), "net": O._r6(blok["ort"] - c),
                "ci": {"lo": O._r6(blok["ci"]["lo"] - c), "hi": O._r6(blok["ci"]["hi"] - c),
                       "seviye": 0.95},
                "net_pozitif_anlamli": bool(blok["ci"]["lo"] - c > 0),
                "net_ort_pozitif": bool(blok["ort"] - c > 0), "neden": None}

    mal = {"tanim": "Maliyet bir SABİT olduğundan CI aynı sabitle ötelenir (cebirsel özdeş). "
                    "Kart modeli tek-yön; gidiş-dönüş BEYANLI duyarlılıktır.",
           "kart_modeli_tek_yon_bps": O.MALIYET_BPS,
           "duyarlilik_gidis_donus_bps": 2 * O.MALIYET_BPS,
           "mid_cap_notu": "Kart: 'mid-cap likidite farkı NOT'a, modele değil (tek değişken "
                           "evren)'. Maliyet EDG-016'nınkiyle AYNI 10 bps'tir; mid-cap "
                           "likiditesinin daha düşük olması bir MODEL değişikliği DEĞİL, "
                           "bu notun konusudur.",
           "ufuklar": {}}
    for h in k016.HORIZONS:
        mal["ufuklar"][str(h)] = {
            "katman1_evren_fazlasi": {
                "kart_modeli": net(kat1["ufuklar"][str(h)]["evren_fazlasi"], c1_),
                "gidis_donus_duyarlilik": net(kat1["ufuklar"][str(h)]["evren_fazlasi"], c2_)},
            "katman2_kova_fazlasi_A1": {
                "kart_modeli": net(a1["ufuklar"][str(h)]["loo_kova_fazlasi"], c1_),
                "gidis_donus_duyarlilik": net(a1["ufuklar"][str(h)]["loo_kova_fazlasi"], c2_)},
        }
    V["dolar_hacim"] = V["med_hacim21"] * V["close"]
    mal["likidite_beyani"] = {
        "not": "Betimleyici kanıt (CI YOK, kart bacağı DEĞİL): dilimin medyan-21g DOLAR hacmi.",
        "ust20_medyan_dolar_hacim": O._r6(V.loc[V["ust"], "dolar_hacim"].median()),
        "kohort_medyan_dolar_hacim": O._r6(V["dolar_hacim"].median()),
        "ust20_medyan_dolar_hacim_orani": O._r6(
            V.loc[V["ust"], "dolar_hacim"].median() / V["dolar_hacim"].median()),
        "ust20_medyan_kapanis": O._r6(V.loc[V["ust"], "close"].median()),
        "kohort_medyan_kapanis": O._r6(V["close"].median()),
    }

    # ================= IV. TANI (K harcanmaz, CI YOK) =================
    tani = {"not": "TANI — kart grid'inde OLMAYAN kesitler. CI BİLEREK hesaplanmadı; CI'lı "
                   "sınansaydı K çarpılırdı. Üst %20 dilimi kartın KAYITLI katmanıdır ve CI'sı "
                   "I. bölümdedir. @10 ufku da TANIdır (kart success_metric'i @20 yazıyor)."}
    V["to_q5"] = V.groupby("date")["turnover21"].transform(
        lambda s: pd.qcut(s.rank(method="first"), 5, labels=False, duplicates="drop"))
    q5 = {}
    for h in k016.HORIZONS:
        g = V[["to_q5", "date", "turnover21", f"fwd{h}"]].dropna()
        g = g.assign(fazla=g[f"fwd{h}"].to_numpy(float) - g["date"].map(tab[h]).to_numpy(float))
        g = g.dropna(subset=["fazla"])
        q5[str(h)] = {str(int(k)): {"n": int(len(v)), "fazla_ort": O._r6(v["fazla"].mean()),
                                    "turnover_ort": O._r6(v["turnover21"].mean())}
                      for k, v in g.groupby("to_q5")}
    tani["turnover_q5_kohort_fazlasi"] = {"aciklama": "0 = en düşük turnover, 4 = en yüksek",
                                          "ufuklar": q5}

    # ================= BEKÇİLER =================
    rng = np.random.default_rng(16)
    gg = V[["artik", "fwd20"]].dropna()
    xs, ys = gg["artik"].to_numpy(float), gg["fwd20"].to_numpy(float)
    farklar = []
    for n in (5000, 50000, len(xs)):
        if n > len(xs):
            continue
        i = rng.choice(len(xs), size=n, replace=False) if n < len(xs) else np.arange(len(xs))
        kan = O.spearman_ic(list(zip(xs[i].tolist(), ys[i].tolist())))
        hiz = k016.spearman_fast(xs[i], ys[i])
        if kan is None or hiz is None:
            continue
        farklar.append(abs(kan - hiz))
    bekciler = {
        "fiziksel_devir_bekcisi": fiz,
        "bayatlik_bekcisi": {
            "kural": f"son dosyalama t'den {O.BAYAT_GUN} günden eskiyse as-of None + "
                     f"neden='bayat_seri'",
            "bayat_seri_hucre": pacc["neden_sayimi"].get("bayat_seri"),
            "etkilenen_sembol_sayisi": len(pacc["bayat_seri_sembol"]),
            "en_cok_etkilenen_sembol_ilk10": pacc["bayat_seri_sembol_ilk10"],
        },
        "pit_sizinti_HAM_PANEL": {
            "kural": "seçilen as-of kaydının `filed`ı gözlem gününü ASLA aşamaz",
            "ihlal_satir": pacc["pit_sizinti_satir"],
            "gecti": bool(pacc["pit_sizinti_satir"] == 0)},
        "pit_sizinti_OLCULEN_UYE_SATIRLAR": {
            "kural": "aynı kural, YALNIZ üyelik süzgecinden geçen (ölçüme giren) satırlarda",
            "ihlal_satir": int(sizinti), "etkilenen_sembol": int(sizinti_sembol),
            "gecti": bool(sizinti == 0)},
        "artik_ortogonallik": ortog,
        "hizli_spearman_ozdesligi": {
            "tanim": "IC bootstrap'ının hızlı yolu kanonik `spearman_ic` ile BİREBİR aynı sayıyı "
                     "vermeli",
            "n_ornek": len(farklar),
            "maks_mutlak_fark": O._r6(max(farklar)) if farklar else None,
            "gecti": bool(max(farklar) < 1e-12) if farklar else None,
            "neden": None if farklar else "özdeşlik örneği kurulamadı (artık/fwd20 kesişimi boş)"},
    }

    # ================= BACAKLAR (OLGU — HÜKÜM DEĞİL) =================
    def gk(d, *ks):
        for k in ks:
            if d is None:
                return None
            d = d.get(k)
        return d

    alanlar = ("n", "ort", "ci", "anlamli", "pozitif_anlamli", "negatif_anlamli")
    bacaklar = {
        "i_ust20_kohort_fazlasi": {
            str(h): {k: gk(kat1, "ufuklar", str(h), "evren_fazlasi", k) for k in alanlar}
            for h in k016.HORIZONS},
        "ii_a1_kova_tabanli_fazla": {
            str(h): {k: gk(a1, "ufuklar", str(h), "loo_kova_fazlasi", k) for k in alanlar}
            for h in k016.HORIZONS},
        "ii_a2_edg007_havuzlanmis_yayilim": {
            str(h): {k: gk(a2, "ufuklar", str(h), "havuzlanmis", k)
                     for k in ("nA", "nB", "fark", "ci", "anlamli", "pozitif_anlamli",
                               "negatif_anlamli")} for h in k016.HORIZONS},
        "ii_b_artik_ic_fazla": {
            str(h): {k: gk(icb, "ufuklar", str(h), "artik_ic_fazla", k)
                     for k in ("ic", "n", "ci", "anlamli", "pozitif_anlamli", "negatif_anlamli")}
            for h in k016.HORIZONS},
        "iii_maliyet_sonrasi_net": {str(h): gk(mal, "ufuklar", str(h)) for h in k016.HORIZONS},
    }

    return {
        "kip": kip, "DURUM": "OLCULDU",
        "bar_muhasebesi": bar_acc,
        "hisse_muhasebesi": hazir["hisse_muhasebesi"],
        "split_takvimi_muhasebesi": hazir["split_takvimi_muhasebesi"],
        "panel_muhasebesi": hazir["panel_muhasebesi"],
        "uyelik_suzgeci": uyelik_acc,
        "kesit_muhasebesi": kesit_acc,
        "akrabalik_beyani": akrabalik,
        "i_katman_turnover_ust20": kat1,
        "ii_katman_turnover_artik_rvol_mom_kontrollu": art,
        "iii_maliyet_sonrasi_net": mal,
        "iv_tani": tani,
        "bekciler": bekciler,
        "bacaklar": bacaklar,
        "_ic": {"V": V, "pan": pan, "D": D, "OBS": OBS},     # ÇIKTIYA YAZILMAZ — PK'ler kullanır
    }


# =================================================================================================
# 5. YANLILIK GÖSTERGELERİ
# =================================================================================================
def yanlilik_gostergesi(etkin, uyelik: dict, gunler: list[str], bar_acc: dict,
                        kapsama_json, belirsiz: frozenset) -> dict:
    """Üç gösterge + bar-uzunluk süzgecinin bedeli. (b) YENİDEN HESAPLANMAZ, ADIM-0 B'nin
    kapsama haritasından OKUNUR — iki kopya sessizce ayrışırdı (tek-kaynak yasası)."""
    birlesim = set()
    for _, k in etkin:
        birlesim |= set(k)
    son_gun = gunler[-1] if gunler else None
    son_uyeler = set(uyelik.get(son_gun, frozenset())) if son_gun else set()
    hala = (len(son_uyeler & birlesim) / len(birlesim)) if birlesim else None

    barsiz = {"payi": None, "kaynak": None,
              "neden": "--kapsama verilmedi → ADIM-0 B haritası okunamadı; pay UYDURULMAZ"}
    if kapsama_json is not None:
        yol = pathlib.Path(kapsama_json)
        try:
            harita = json.loads(yol.read_text(encoding="utf-8"))
            taban = (harita.get("ozet") or {}).get("yanlilik_gostergesi_tabani") or {}
            barsiz = {"payi": taban.get("barsiz_cikis_payi"),
                      "tanim": taban.get("tanim"), "tolerans_gun": taban.get("tolerans_gun"),
                      "cikan_n": taban.get("cikan_n"), "barsiz_n": taban.get("barsiz_n"),
                      "barsiz_semboller": taban.get("barsiz_semboller"),
                      "kaynak": f"{yol} (damga {harita.get('damga_utc')}) — ADIM-0 EKSEN B; "
                                f"BURADA YENİDEN HESAPLANMADI",
                      "neden": taban.get("barsiz_cikis_payi_neden")}
        except (OSError, ValueError, KeyError, AttributeError) as e:
            # sessiz-yutma DEĞİL: harita okunamadı — pay UYDURULMAZ, neden ADIYLA yazılır
            barsiz = {"payi": None, "kaynak": str(yol),
                      "neden": f"kapsama haritası okunamadı ({type(e).__name__}: {e})"}

    kisa = set(bar_acc.get("kisa_semboller") or [])
    yok = set(bar_acc.get("dosya_yok_semboller") or [])
    cikanlar = birlesim - son_uyeler
    return {
        "a_hala_listede_orani": {
            "deger": None if hala is None else round(hala, 6),
            "tanim": "son gün AS-OF üye olan isim / pencerede en az bir gün üye olan isim "
                     "(birleşim)",
            "son_gun": son_gun, "son_gun_uye_n": len(son_uyeler), "birlesim_n": len(birlesim),
            "cikan_n": len(cikanlar)},
        "b_barsiz_cikis_payi": barsiz,
        "c_belirsiz_isim": {
            "n": len(belirsiz), "semboller": sorted(belirsiz),
            "payi_birlesime_gore": round(len(belirsiz & birlesim) / len(birlesim), 6)
                                   if birlesim else None,
            "not": "duyarlılık (dahil vs hariç) `duyarlilik_belirsiz` bloğundadır"},
        "d_bar_uzunluk_suzgecinin_bedeli": {
            "tanim": f"EDG-016 ile AYNI asgari seri uzunluğu ({bar_acc.get('bar_min_uzunluk')} "
                     f"bar) uygulandı — TEK DEĞİŞKEN EVREN kuralı. Bedeli: kısa seriyle düşen "
                     f"isimler ölçüme HİÇ girmez ve bunların çoğu ERKEN ÇIKAN isimlerdir; bu, "
                     f"(b) göstergesinin ÜSTÜNE binen ikinci bir sağkalan yanlılığı kanalıdır.",
            "kisa_dusen_n": len(kisa), "kisa_dusen_cikan_n": len(kisa & cikanlar),
            "kisa_dusen_semboller": sorted(kisa),
            "bar_dosyasi_olmayan_n": len(yok), "bar_dosyasi_olmayan_cikan_n": len(yok & cikanlar),
        },
    }


# =================================================================================================
# 6. POZİTİF KONTROLLER (kart `pozitif_kontrol` — DÖRT PARÇA)
# =================================================================================================
def pk1_large_cap(pk_sonuc: dict | None, sonuc016_yolu, O) -> dict:
    """PK-1 — aynı kodun S&P 500 PIT kohortunda EDG-016'nın YÖNÜNÜ ve CI-0-DIŞILIĞINI yeniden
    üretmesi. Sayı EŞİTLİĞİ beklenmez (evren as-of, EDG-016'nınki sabit listeydi); beklenen
    kartın yazdığı şeydir: "kayıtlı sayıları (yön + CI-0-dışılık) YENİDEN ÜRETMELİ"."""
    if pk_sonuc is None:
        return {"kosdu": False, "yon_esit": None, "ci0_disi_esit": None,
                "neden": "--pk-kohort/--pk-bars-dir/--pk-shares verilmedi — PK-1 KOŞMADI"}
    if pk_sonuc.get("DURUM") != "OLCULDU":
        return {"kosdu": False, "yon_esit": None, "ci0_disi_esit": None,
                "neden": f"PK-1 evreni ölçülemedi: {pk_sonuc.get('neden')}"}
    if sonuc016_yolu is None or not pathlib.Path(sonuc016_yolu).exists():
        return {"kosdu": True, "yon_esit": None, "ci0_disi_esit": None,
                "neden": f"referans sonuc_016.json bulunamadı ({sonuc016_yolu}) — kıyas YAPILAMADI"}
    try:
        ref = json.loads(pathlib.Path(sonuc016_yolu).read_text(encoding="utf-8"))
        rb = ref["hukum_onerisi"]["bacaklar"]
    except (OSError, ValueError, KeyError) as e:
        # sessiz-yutma DEĞİL: referans okunamadı — kıyas UYDURULMAZ, neden ADIYLA döner
        return {"kosdu": True, "yon_esit": None, "ci0_disi_esit": None,
                "neden": f"referans okunamadı ({type(e).__name__}: {e})"}

    esleme = [("i_ust20_kohort_fazlasi", "i_ust20_evren_fazlasi", "ort"),
              ("ii_a1_kova_tabanli_fazla", "ii_a1_kova_tabanli_fazla", "ort"),
              ("ii_b_artik_ic_fazla", "ii_b_artik_ic_fazla", "ic")]
    detay, yon_ok, ci_ok = [], [], []
    for benim_ad, ref_ad, deger_alani in esleme:
        for h in ("10", "20"):
            b = (pk_sonuc["bacaklar"].get(benim_ad) or {}).get(h) or {}
            r = (rb.get(ref_ad) or {}).get(h) or {}
            bv, rv = b.get(deger_alani), r.get(deger_alani)
            yon = None if (bv is None or rv is None) else bool((bv > 0) == (rv > 0))
            ci = None if (b.get("anlamli") is None or r.get("anlamli") is None) \
                else bool(b["anlamli"] == r["anlamli"])
            detay.append({"bacak": benim_ad, "ufuk": h, "pk1_deger": bv, "edg016_deger": rv,
                          "yon_esit": yon, "pk1_anlamli": b.get("anlamli"),
                          "edg016_anlamli": r.get("anlamli"), "ci0_disi_esit": ci})
            if yon is not None:
                yon_ok.append(yon)
            if ci is not None:
                ci_ok.append(ci)
    return {"kosdu": True,
            "yon_esit": bool(yon_ok) and all(yon_ok),
            "ci0_disi_esit": bool(ci_ok) and all(ci_ok),
            "kiyaslanan_bacak_n": len(detay), "referans": str(sonuc016_yolu),
            "not": "SAYI eşitliği beklenmez (PK-1 evreni as-of S&P 500 kohortu, EDG-016'nınki "
                   "sabit 251 sembollük REPLAY_UNIVERSE listesiydi) — kartın istediği YÖN ve "
                   "CI-0-dışılıktır.",
            "detay": detay, "neden": None}


def pk2_dogrulama_tablosu(ic: dict, p1, tohum: int, np, pd, n: int = PK2_SATIR_N) -> dict:
    """PK-2 — rastgele `n` kohort-gün için ELLE doğrulama tablosu (Rol-1 bar dosyasından okur).

    Tablo `fwd20`yi bar dosyasından okunabilecek iki fiyatla YAN YANA verir; koşum ayrıca kendi
    içinde tutarlılığı ölçer (`ic_tutarli`), ama HÜKÜM ELLE doğrulamanındır."""
    V, pan = ic["V"], ic["pan"]
    alt = V[["date", "ticker", "to_pct", "turnover21", "close", "fwd20"]].dropna(subset=["fwd20"])
    if alt.empty:
        return {"n": 0, "tohum": tohum, "satirlar": [],
                "neden": "fwd20 tanımlı üye satır yok — tablo kurulamadı"}
    # pandas `random_state` 32 bitle sınırlıdır; tohum sha türevi olabilir → daraltılır ve
    # daraltma kayda geçer (aynı tohum → aynı örneklem; belirlenimcilik korunur).
    ornek = alt.sample(n=min(n, len(alt)),
                       random_state=int(tohum) % (2 ** 32)).sort_values(["date", "ticker"])
    satirlar, tutarli = [], []
    for _, r in ornek.iterrows():
        sym, t = str(r["ticker"]), str(r["date"])
        v = pan.get(sym) or {}
        d = v.get("dates")
        c20, kaydirma = None, None
        if d is not None:
            i = int(np.searchsorted(d, t))
            if i < len(d) and d[i] == t and i + 20 < len(d):
                c20 = float(v["close"][i + 20])
                kaydirma = str(d[i + 20])
        beklenen = None if c20 is None else (c20 / float(r["close"]) - 1.0)
        ok = None if beklenen is None else bool(abs(beklenen - float(r["fwd20"])) < 1e-9)
        if ok is not None:
            tutarli.append(ok)
        satirlar.append({
            "sembol": sym, "t": t, "bar_dosyasi": f"{p1.bar_dosya_adi(sym)}.csv",
            "turnover_pct_rutbe": round(float(r["to_pct"]), 6),
            "dilim_ust20_mu": bool(float(r["to_pct"]) > 1 - 0.20),
            "turnover21": round(float(r["turnover21"]), 8),
            "close_t": round(float(r["close"]), 6), "close_t_arti_20": c20,
            "t_arti_20_tarihi": kaydirma, "fwd20": round(float(r["fwd20"]), 8),
            "ic_tutarli": ok,
            "neden": None if c20 is not None else "t+20 barı seride yok — ÖLÇÜLEMEDİ"})
    return {"n": len(satirlar), "tohum": tohum,
            "aciklama": "ELLE DOĞRULAMA İÇİN: bar dosyasında `t` ve `t_arti_20_tarihi` "
                        "satırlarının `close` değerleri `close_t`/`close_t_arti_20` ile "
                        "eşleşmeli ve fwd20 = close_t+20/close_t − 1 olmalı.",
            "ic_tutarli_n": int(sum(tutarli)), "ic_olculen_n": len(tutarli),
            "ic_hepsi_tutarli": bool(tutarli) and all(tutarli),
            "satirlar": satirlar}


def pk3_sentetik(etkin, uyelik: dict, gunler: list[str], tohum: int,
                 dusen_n: int = PK3_DUSEN_N) -> dict:
    """PK-3 — kohorttan bilinçli `dusen_n` isim düşürülünce 'hâlâ listede' oranı BEKLENEN YÖNDE.

    İKİ YÖNLÜ: hâlâ listede olanlardan düşürmek oranı DÜŞÜRMELİ (pay ve payda birlikte azalır,
    oran < 1); ÇIKMIŞ isimlerden düşürmek oranı YÜKSELTMELİ (yalnız payda azalır). Tek yönlü bir
    sınav, oranı sabit döndüren bir hataya kör kalırdı."""
    birlesim = set()
    for _, k in etkin:
        birlesim |= set(k)
    son = set(uyelik.get(gunler[-1], frozenset())) if gunler else set()
    kalan, cikan = sorted(son & birlesim), sorted(birlesim - son)

    def oran(dusur: set):
        b = birlesim - dusur
        return (len((son - dusur) & b) / len(b)) if b else None

    r0 = oran(set())
    rnd = random.Random(tohum)
    d_kalan = set(rnd.sample(kalan, min(dusen_n, len(kalan))))
    d_cikan = set(rnd.sample(cikan, min(dusen_n, len(cikan))))
    r_kalan, r_cikan = oran(d_kalan), oran(d_cikan)
    return {
        "tohum": tohum, "dusen_n": dusen_n, "taban_oran": None if r0 is None else round(r0, 6),
        "kalan_havuz_n": len(kalan), "cikan_havuz_n": len(cikan),
        "kalanlardan_dusurulunce": {
            "dusen": sorted(d_kalan), "oran": None if r_kalan is None else round(r_kalan, 6),
            "beklenen_yon": "düşer",
            "gecti": None if (r0 is None or r_kalan is None) else bool(r_kalan < r0)},
        "cikanlardan_dusurulunce": {
            "dusen": sorted(d_cikan), "oran": None if r_cikan is None else round(r_cikan, 6),
            "beklenen_yon": "yükselir",
            "gecti": None if (r0 is None or r_cikan is None) else bool(r_cikan > r0)},
        "gecti": None if (r0 is None or r_kalan is None or r_cikan is None)
                 else bool(r_kalan < r0 < r_cikan),
    }


def pk4_olay_yansimasi(ic: dict, olaylar: list[dict], tohum: int, n: int, tolerans: int,
                       pd) -> dict:
    """PK-4 — EDG-092 `bilinen_olaylar`ından `n` olay PANELDE yansımalı: giriş olayında sembol
    t-1'de YOK / t'de VAR, çıkış olayında tersi.

    PANEL ÜZERİNDE ölçülür (kohort serisi üzerinde DEĞİL): EDG-093'ün ölçtüğü şey panelin
    kendisidir; kohort defterinin doğruluğu ADIM-0 A'nın PIT-PK'sında zaten ölçüldü. Takvim
    GÜNÜ değil GÖZLEM GÜNÜ kullanılır — yürürlük günü seans olmayabilir. Pencere dışında kalan
    ya da barı olmayan olay `olculemedi`dir ve `gecti` None KALIR (uydurma yasağı)."""
    D = ic["D"]
    if D.empty:
        return {"ornek_n": 0, "neden": "panel boş"}
    gunler = sorted(set(D["date"].astype(str).tolist()))
    var = set(zip(D["date"].astype(str).tolist(), D["ticker"].astype(str).tolist()))
    panel_semboller = set(D["ticker"].astype(str).tolist())

    havuz = [o for o in olaylar if o.get("tarih") and o.get("sembol") and o.get("yon")]
    havuz.sort(key=lambda o: (str(o["tarih"]), str(o["sembol"]), str(o["yon"])))
    ornek = random.Random(tohum).sample(havuz, min(n, len(havuz)))
    ornek.sort(key=lambda o: (str(o["tarih"]), str(o["sembol"])))

    detay = []
    for o in ornek:
        s, t, giris = str(o["sembol"]).upper(), str(o["tarih"]), str(o["yon"]) == "giris"
        kayit = {"sembol": s, "yon": o["yon"], "yurulukte": t, "t_gozlem": None,
                 "t_onceki_gozlem": None, "t_1_panelde": None, "t_panelde": None,
                 "gecti_strict": None, "gecti_toleransli": None, "neden": None}
        if s not in panel_semboller:
            kayit["neden"] = "sembol panelde YOK (bar/uzunluk süzgeci ya da hiç üye olmadı) — " \
                             "ÖLÇÜLEMEDİ"
            detay.append(kayit)
            continue
        i = bisect.bisect_left(gunler, t)
        if i == 0 or i >= len(gunler):
            kayit["neden"] = "yürürlük günü panel takviminin DIŞINDA — ÖLÇÜLEMEDİ"
            detay.append(kayit)
            continue
        t_cur, t_prev = gunler[i], gunler[i - 1]
        kayit["t_gozlem"], kayit["t_onceki_gozlem"] = t_cur, t_prev
        kayit["t_1_panelde"] = (t_prev, s) in var
        kayit["t_panelde"] = (t_cur, s) in var
        kayit["gecti_strict"] = bool((not kayit["t_1_panelde"] and kayit["t_panelde"]) if giris
                                     else (kayit["t_1_panelde"] and not kayit["t_panelde"]))
        gecis = None
        for k in range(-tolerans, tolerans + 1):
            j = i + k
            if j <= 0 or j >= len(gunler):
                continue
            a, b = (gunler[j - 1], s) in var, (gunler[j], s) in var
            if (giris and not a and b) or (not giris and a and not b):
                gecis = gunler[j]
                break
        kayit["gecis_gozlem_gunu"] = gecis
        kayit["gecti_toleransli"] = bool(gecis is not None)
        detay.append(kayit)
    olculen = [d for d in detay if d["gecti_strict"] is not None]
    return {"ornek_n": len(ornek), "olay_havuzu_n": len(havuz), "tohum": tohum,
            "tolerans_gozlem_gunu": tolerans,
            "olculemedi_n": len(detay) - len(olculen),
            "gecti_strict_n": sum(1 for d in olculen if d["gecti_strict"]),
            "gecti_toleransli_n": sum(1 for d in olculen if d["gecti_toleransli"]),
            "hepsi_gecti_toleransli": bool(olculen) and all(d["gecti_toleransli"] for d in olculen),
            "detay": detay}


def olay_kumesi_yukle(repo: pathlib.Path, kart092: pathlib.Path) -> tuple[list, dict]:
    """EDG-092 `bilinen_olaylar` — EDG-092 `olc.py` AYRIŞTIRICISIYLA (kopya YOK, ithal).

    Yükleme `kohort.py` üzerinden yapılır çünkü PIT-PK tohumu ve örneklem büyüklüğü de oradadır
    (tek-kaynak). Yükleme düşerse olay kümesi BOŞ döner ve `neden` ADIYLA kayda geçer — PK-4
    'koşmadı' olur, sayı UYDURULMAZ."""
    meta = {"kaynak": None, "tohum": None, "ornek_n": None, "tolerans": None, "neden": None}
    try:
        yukle = _yukleyici(repo)
        kohort = yukle(repo / "research" / "olcumler" / "edg093_midcap_pit" / "kohort.py",
                       "edg093_kohort_k093")
        kart = kohort.OLC.kart_yukle(pathlib.Path(kart092))
        olaylar, beyan_n, _norm = kohort.OLC.olay_kumesi(kart)
        meta.update({"kaynak": f"{kart092} `bilinen_olaylar` → EDG-092 olc.olay_kumesi "
                               f"(kohort.py üzerinden ithal)",
                     "kart_beyan_n": beyan_n, "olay_n": len(olaylar),
                     "tohum": int(kohort.TOHUM), "ornek_n": int(kohort.PK_OLAY_N),
                     "tolerans": int(kohort.PK_TOLERANS_GUN)})
        return olaylar, meta
    except (OSError, ImportError, AttributeError, ValueError, KeyError, TypeError) as e:
        # sessiz-yutma DEĞİL: olay kümesi yüklenemedi — PK-4 KOŞMAZ ve neden ADIYLA yazılır
        meta["neden"] = f"olay kümesi yüklenemedi ({type(e).__name__}: {e})"
        return [], meta


# =================================================================================================
# 7. RAPOR
# =================================================================================================
def _yuzde(x, nd=3):
    return "—" if x is None else f"{100.0 * float(x):.{nd}f}%"


def _ci(c):
    return "—" if not c else f"[{100 * c['lo']:.3f}% · {100 * c['hi']:.3f}%]"


def _sayi(x, nd=4):
    return "—" if x is None else f"{float(x):.{nd}f}"


def _ic_ci(c):
    return "—" if not c else f"[{c['lo']:.4f} · {c['hi']:.4f}]"


def _isaret(x):
    return {True: "EVET", False: "hayır", None: "—"}.get(x, str(x))


def rapor_metni(sonuc: dict) -> str:
    """RAPOR_093 — okuyan Rol-1 / operatör masası. HÜKÜM YOK: yalnız sayı, CI ve beyan."""
    s: list[str] = []
    a = s.append
    a(f"# EDG-2026-093 · ANA ÖLÇÜM — S&P 400 PIT kohortunda turnover ana etkisi")
    a("")
    a(f"**Hüküm:** {sonuc['hukum']} · **Damga:** {sonuc['damga_utc']} · "
      f"**Durum:** {sonuc['DURUM']}")
    a("")
    a("> Tasarım EDG-2026-016 AYNEN; TEK DEĞİŞKEN EVRENDİR (sabit liste → as-of PIT kohortu). "
      "Eşik kartın ön-kayıtlı tanımıdır: 'anlamlı pozitif' = %95 blok-CI alt sınırı > 0; "
      "sayısal bps eşiği YOKTUR.")
    a("")

    a("## Girdi damgaları")
    a("")
    a("| Girdi | Yol | sha256 |")
    a("|---|---|---|")
    for ad, g in (sonuc.get("girdi_damgasi") or {}).items():
        if not isinstance(g, dict):
            continue
        # Hücre içeriği ters-tırnak TAŞIYAMAZ: `neden` metinleri kod parçaları anıyor ve tablo
        # hücresi kod aralığıyla sarıldığı için içerideki ters-tırnak aralığı ERKEN kapatır
        # (satır okunmaz hâle gelir). Ayıklama yapılır ve bu bir BİLGİ KAYBI değildir: tam metin
        # JSON'da durur (rapor JSON'un ÖZETİdir, kaynağı değil).
        hucre = str(g.get("sha256") or g.get("neden") or "—").replace("`", "'")
        a(f"| {ad} | `{g.get('yol')}` | `{hucre}` |")
    a("")

    em = sonuc.get("evren_muhasebesi") or {}
    a("## Evren muhasebesi")
    a("")
    a(f"- Kohort penceresi: **{em.get('pencere_baslangic')} → {em.get('pencere_bitis')}** "
      f"({em.get('as_of_satir_n')} etkin as-of satırı)")
    a(f"- Pencerede en az bir gün üye olan isim: **{em.get('isim_n_birlesim')}** · "
      f"son gün üye: **{em.get('son_gun_uye_n')}**")
    a(f"- AS-OF ÜYE GÜN (sembol-gün hücresi, ölçüme giren): **{em.get('uye_gun_hucre')}**")
    a(f"- Etkin ölçüm başlangıcı (ÖLÇÜLDÜ): **{em.get('etkin_baslangic_olculen')}** — "
      f"{em.get('isinma_notu')}")
    a(f"- Belirsiz isim: **{em.get('belirsiz_n')}** ({', '.join(em.get('belirsiz_semboller') or []) or '—'})")
    a("")

    for kip, kosum_s in (sonuc.get("kosumlar") or {}).items():
        etiket = "BİRİNCİL" if kip == BIRINCIL_KIP else "DUYARLILIK"
        a(f"## Koşum `{kip}` ({etiket})")
        a("")
        if kosum_s.get("DURUM") != "OLCULDU":
            a(f"ÖLÇÜLEMEDİ — {kosum_s.get('neden')}")
            a("")
            continue
        km = kosum_s["kesit_muhasebesi"]
        a(f"Kesit: {km['n_satir']} satır · {km['n_sembol']} sembol · "
          f"{km['kesit_yeterli_gun']}/{km['gozlem_gunu_toplam']} gün "
          f"(asgari kesit {km['min_kesit']}) · {km['tarih_araligi'][0]} → {km['tarih_araligi'][1]}")
        a("")
        a("### Katman I — turnover üst %20, aynı-gün kohort fazlası")
        a("")
        a("| Ufuk | n | Fazla (ort) | %95 blok-CI | CI-0-dışı | Poz. anlamlı |")
        a("|---|---:|---:|---|---|---|")
        for h, blok in kosum_s["i_katman_turnover_ust20"]["ufuklar"].items():
            f = blok["evren_fazlasi"]
            a(f"| {h}g | {f.get('n')} | {_yuzde(f.get('ort'))} | {_ci(f.get('ci'))} | "
              f"{_isaret(f.get('anlamli'))} | {_isaret(f.get('pozitif_anlamli'))} |")
        a("")
        a("### Katman II — artık katkı (rvol20 × mom21 kontrolü)")
        a("")
        a("| Ufuk | A1 kova fazlası | A1 CI | A2 havuzlanmış | A2 CI | Artık-IC | IC CI |")
        a("|---|---:|---|---:|---|---:|---|")
        ii = kosum_s["ii_katman_turnover_artik_rvol_mom_kontrollu"]
        for h in ii["A1_kova_tabanli_ust20_fazlasi"]["ufuklar"]:
            x = ii["A1_kova_tabanli_ust20_fazlasi"]["ufuklar"][h]["loo_kova_fazlasi"]
            y = ii["A2_edg007_kova_ici_ust20_eksi_kalan"]["ufuklar"][h]["havuzlanmis"]
            z = ii["B_artik_ic"]["ufuklar"][h]["artik_ic_fazla"]
            a(f"| {h}g | {_yuzde(x.get('ort'))} | {_ci(x.get('ci'))} | "
              f"{_yuzde(y.get('fark'))} | {_ci(y.get('ci'))} | "
              f"{_sayi(z.get('ic'))} | {_ic_ci(z.get('ci'))} |")
        a("")
        a("### Katman III — maliyet sonrası net (kart modeli: 10 bps tek yön)")
        a("")
        a("| Ufuk | Katman | Brüt | Net | Net CI | Net poz. anlamlı |")
        a("|---|---|---:|---:|---|---|")
        for h, blok in kosum_s["iii_maliyet_sonrasi_net"]["ufuklar"].items():
            for ad, kk in blok.items():
                n = kk["kart_modeli"]
                a(f"| {h}g | {ad} | {_yuzde(n.get('brut'))} | {_yuzde(n.get('net'))} | "
                  f"{_ci(n.get('ci'))} | {_isaret(n.get('net_pozitif_anlamli'))} |")
        a("")
        a("### Bekçiler")
        a("")
        b = kosum_s["bekciler"]
        a(f"- PIT sızıntı (ham panel): {b['pit_sizinti_HAM_PANEL']['ihlal_satir']} satır · "
          f"geçti={_isaret(b['pit_sizinti_HAM_PANEL']['gecti'])}")
        a(f"- PIT sızıntı (ölçülen üye satırlar): "
          f"{b['pit_sizinti_OLCULEN_UYE_SATIRLAR']['ihlal_satir']} satır · "
          f"geçti={_isaret(b['pit_sizinti_OLCULEN_UYE_SATIRLAR']['gecti'])}")
        a(f"- Artık ortogonallik: geçti={_isaret(b['artik_ortogonallik'].get('gecti'))}")
        a(f"- Hızlı Spearman ≡ kanonik: geçti={_isaret(b['hizli_spearman_ozdesligi'].get('gecti'))}")
        a(f"- Fiziksel devir bekçisi: {b['fiziksel_devir_bekcisi'].get('gecersiz_kayit')} kayıt "
          f"geçersizlendi")
        a("")

    y = sonuc.get("yanlilik_gostergesi") or {}
    a("## Yanlılık göstergeleri (BEYAN — hüküm değil, K'ye girmez)")
    a("")
    a(f"- (a) 'hâlâ listede' oranı: **{_yuzde((y.get('a_hala_listede_orani') or {}).get('deger'))}** "
      f"({(y.get('a_hala_listede_orani') or {}).get('son_gun_uye_n')}/"
      f"{(y.get('a_hala_listede_orani') or {}).get('birlesim_n')})")
    bb = y.get("b_barsiz_cikis_payi") or {}
    a(f"- (b) barsız-çıkış payı: **{_yuzde(bb.get('payi'))}** — kaynak: "
      f"`{bb.get('kaynak') or bb.get('neden')}` (BURADA YENİDEN HESAPLANMADI)")
    cc = y.get("c_belirsiz_isim") or {}
    a(f"- (c) belirsiz isim: **{cc.get('n')}** · birleşime oranı {_yuzde(cc.get('payi_birlesime_gore'))}")
    dd = y.get("d_bar_uzunluk_suzgecinin_bedeli") or {}
    a(f"- (d) bar-uzunluk süzgecinin bedeli: {dd.get('kisa_dusen_n')} isim kısa seriyle düştü "
      f"(bunların {dd.get('kisa_dusen_cikan_n')}'i ÇIKAN isim) · bar dosyası olmayan "
      f"{dd.get('bar_dosyasi_olmayan_n')}")
    a("")

    d = sonuc.get("duyarlilik_belirsiz") or {}
    if d.get("kiyas"):
        a("## Belirsiz-isim duyarlılığı (dahil vs hariç)")
        a("")
        a("| Bacak | Ufuk | dahil | dahil CI-0-dışı | hariç | hariç CI-0-dışı |")
        a("|---|---|---:|---|---:|---|")
        for r in d["kiyas"]:
            a(f"| {r['bacak']} | {r['ufuk']}g | {_yuzde(r['dahil_deger'])} | "
              f"{_isaret(r['dahil_anlamli'])} | {_yuzde(r['haric_deger'])} | "
              f"{_isaret(r['haric_anlamli'])} |")
        a("")

    pk = sonuc.get("pk") or {}
    a("## Pozitif kontroller")
    a("")
    a("| PK | Ne | Sonuç |")
    a("|---|---|---|")
    p1_ = pk.get("pk1") or {}
    a(f"| PK-1 | large-cap yeniden üretim | koştu={_isaret(p1_.get('kosdu'))} · "
      f"yön eşit={_isaret(p1_.get('yon_esit'))} · CI-0-dışılık eşit="
      f"{_isaret(p1_.get('ci0_disi_esit'))} {('· ' + str(p1_.get('neden'))) if p1_.get('neden') else ''} |")
    p2 = pk.get("pk2") or {}
    a(f"| PK-2 | {p2.get('n')} kohort-gün elle doğrulama tablosu | iç tutarlılık "
      f"{p2.get('ic_tutarli_n')}/{p2.get('ic_olculen_n')} · ELLE doğrulama Rol-1'de |")
    p3 = pk.get("pk3") or {}
    a(f"| PK-3 | sentetik isim düşürme | geçti={_isaret(p3.get('gecti'))} "
      f"(kalanlardan→düşer {_isaret((p3.get('kalanlardan_dusurulunce') or {}).get('gecti'))}, "
      f"çıkanlardan→yükselir {_isaret((p3.get('cikanlardan_dusurulunce') or {}).get('gecti'))}) |")
    p4 = pk.get("pk4") or {}
    a(f"| PK-4 | {p4.get('ornek_n')} bilinen olay panelde yansıyor mu | "
      f"strict {p4.get('gecti_strict_n')} · toleranslı {p4.get('gecti_toleransli_n')} · "
      f"ölçülemedi {p4.get('olculemedi_n')} |")
    a("")

    a("## K beyanı")
    a("")
    for satir in (sonuc.get("k_beyani") or {}).get("satirlar", []):
        a(f"- {satir}")
    a("")
    a("## İthalin yan etkisi")
    a("")
    for ad, v in (sonuc.get("ithal_yan_etkisi") or {}).items():
        a(f"- `{ad}`: koşumdan önce vardı={_isaret(v.get('koşumdan_once_vardi'))} · "
          f"silindi={_isaret(v.get('silindi'))} · {v.get('neden') or '—'}")
    a("")
    a(f"_Üretici: `research/olcumler/edg093_midcap_pit/k093.py` · hüküm {sonuc['hukum']}._")
    return "\n".join(s) + "\n"


# =================================================================================================
# 8. ANA AKIŞ
# =================================================================================================
def _ayristirici() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="k093.py",
        description="EDG-2026-093 ANA ÖLÇÜM — S&P 400 PIT kohortunda turnover ana etkisi "
                    "(EDG-016 tasarımı aynen). HÜKÜM YOK.")
    ap.add_argument("--repo", type=pathlib.Path, required=True, help="depo kökü")
    ap.add_argument("--kohort", type=pathlib.Path, required=True,
                    help="sp400_uyelik_tarihi.csv (as-of adım fonksiyonu)")
    ap.add_argument("--bars-dir", type=pathlib.Path, required=True,
                    help="Parti-1'in yazdığı bars/ dizini")
    ap.add_argument("--shares", type=pathlib.Path, required=True,
                    help="shares_outstanding_sp400.csv.gz (EDGAR şeması, `filed` zorunlu)")
    ap.add_argument("--cikti", type=pathlib.Path, required=True, help="çıktı dizini")
    ap.add_argument("--baslangic", default=None,
                    help="kohort penceresinin başı; VERİLMEZSE karttan (`veri_penceresi`) "
                         "türetilir (kart değeri 2020-07-27)")
    ap.add_argument("--bitis", default=None,
                    help="pencere sonu; varsayılan kohort defterinin SON günü")
    ap.add_argument("--belirsiz", choices=BELIRSIZ_KIPLERI, default="ikisi",
                    help="belirsiz isimler: dahil | haric | ikisi (varsayılan)")
    ap.add_argument("--esleme", type=pathlib.Path, default=None,
                    help="sp400_elle_esleme.yaml (belirsiz isimler BURADAN türetilir)")
    ap.add_argument("--kapsama", type=pathlib.Path, default=None,
                    help="ADIM-0 B kapsama haritası json — barsız-çıkış payı BURADAN OKUNUR")
    ap.add_argument("--kart", type=pathlib.Path, default=None, help="EDG-093 kart yaml'i")
    ap.add_argument("--kart092", type=pathlib.Path, default=None,
                    help="EDG-092 kart yaml'i (PK-4 olay kümesi)")
    ap.add_argument("--defter", type=pathlib.Path, default=None,
                    help="bars_integrity.json — verilmezse defter YOK ve dışlama uygulanmaz")
    ap.add_argument("--sonuc016", type=pathlib.Path, default=None,
                    help="PK-1 kıyas referansı (wp2_olcum/sonuc_016.json)")
    ap.add_argument("--pk-kohort", type=pathlib.Path, default=None,
                    help="PK-1 large-cap kohortu (sp500_uyelik_tarihi.csv)")
    ap.add_argument("--pk-bars-dir", type=pathlib.Path, default=None)
    ap.add_argument("--pk-shares", type=pathlib.Path, default=None)
    ap.add_argument("--tohum", type=int, default=None,
                    help="PK örnekleme tohumu; verilmezse kohort.py'nin kart kimliğinden "
                         "türettiği SABİT tohum")
    return ap


def main(argv=None) -> int:
    ap = _ayristirici()
    ARGV = ap.parse_args(argv)
    repo = ARGV.repo.resolve()
    cikti = ARGV.cikti.resolve()
    cikti.mkdir(parents=True, exist_ok=True)
    damga = damga_uret()

    kart = ARGV.kart or (repo / "research" / "cards" / KART_ADI)
    kart092 = ARGV.kart092 or (repo / "research" / "cards" /
                               "EDG-2026-092-sp400-uyelik-tarihcesi-ucretsiz-kaynak-fizibilite.yaml")
    esleme = ARGV.esleme or (repo / "research" / "pit_universe" / "sp400_elle_esleme.yaml")
    sonuc016 = ARGV.sonuc016 or (repo / "research" / "olcumler" / "wp2_olcum" / "sonuc_016.json")

    yuzey = ithal_yuzeyi(repo, cikti, ARGV.bars_dir.resolve(), ARGV.defter)
    O, p1 = yuzey["O"], yuzey["p1"]
    import numpy as np
    import pandas as pd

    # ---------- pencere ----------
    if ARGV.baslangic:
        bas_s, bas_kaynak, bas_neden = ARGV.baslangic, "--baslangic ile ELLE verildi", None
    else:
        bas_s, bas_neden = p1.kart_pencere_baslangici(pathlib.Path(kart))
        bas_kaynak = f"karttan türetildi: {kart} `veri_penceresi`"
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

    etkin, capa, ham_n = etkin_satirlar(p1, ARGV.kohort, baslangic, bitis)
    belirsiz, bel_kaynak, bel_neden = belirsiz_isimler(esleme)

    birlesim = set()
    for _, k in etkin:
        birlesim |= set(k)

    # ---------- olay kümesi + tohum ----------
    olaylar, olay_meta = olay_kumesi_yukle(repo, kart092)
    tohum = ARGV.tohum if ARGV.tohum is not None else olay_meta.get("tohum")
    tohum_kaynak = "--tohum ile ELLE verildi" if ARGV.tohum is not None else olay_meta.get("kaynak")
    if tohum is None:
        tohum = int(hashlib.sha256(KART_ID.encode("utf-8")).hexdigest()[:8], 16)
        tohum_kaynak = (f"BEYANLI TABAN — kohort.py yüklenemedi ({olay_meta.get('neden')}); "
                        f"tohum kart kimliğinden ({KART_ID}) türetildi")

    # ---------- koşumlar ----------
    # VERİ BİR KEZ hazırlanır: `dahil` ve `haric` AYNI ham panelden türer (barlar ikinci kez
    # okunmaz). `haric` yalnız ÜYELİK haritasından isim düşürür — evren dışındaki bir isim
    # panelde satır taşısa bile süzgeçten geçemez, yani sonuç aynıdır ve bedel yarıya iner.
    kipler = [BIRINCIL_KIP] if ARGV.belirsiz == BIRINCIL_KIP else (
        ["haric"] if ARGV.belirsiz == "haric" else [BIRINCIL_KIP, "haric"])
    hazir = veri_hazirla(sorted(birlesim), ARGV.bars_dir, ARGV.shares, yuzey, np, pd)
    kosumlar: dict[str, dict] = {}
    uyelikler: dict[str, dict] = {}
    for kip in kipler:
        dusur = belirsiz if kip == "haric" else frozenset()
        if hazir.get("DURUM") != "HAZIR":
            kosumlar[kip] = {"kip": kip, "DURUM": "OLCULEMEDI",
                             "bar_muhasebesi": hazir.get("bar_muhasebesi"),
                             "neden": hazir.get("neden")}
            uyelikler[kip] = {}
            continue
        uyelikler[kip] = uyelik_haritasi(etkin, hazir["gunler"], dusur)
        kosumlar[kip] = katmanlari_olc(kip, hazir, uyelikler[kip], yuzey, np, pd)

    birincil = kosumlar.get(BIRINCIL_KIP) or kosumlar[kipler[0]]
    b_gunler = hazir.get("gunler") or []
    b_uyelik = uyelikler.get(BIRINCIL_KIP) or uyelikler.get(kipler[0]) or {}

    # ---------- PK ----------
    pk1_kosum = None
    if ARGV.pk_kohort and ARGV.pk_bars_dir and ARGV.pk_shares:
        pk_etkin, _c, _n = etkin_satirlar(p1, ARGV.pk_kohort, baslangic, bitis)
        pk_birlesim = set()
        for _, k in pk_etkin:
            pk_birlesim |= set(k)
        pk_hazir = veri_hazirla(sorted(pk_birlesim), ARGV.pk_bars_dir, ARGV.pk_shares,
                                yuzey, np, pd)
        if pk_hazir.get("DURUM") == "HAZIR":
            pk1_kosum = katmanlari_olc(
                "pk1", pk_hazir, uyelik_haritasi(pk_etkin, pk_hazir["gunler"]), yuzey, np, pd)
        else:
            pk1_kosum = {"kip": "pk1", "DURUM": "OLCULEMEDI", "neden": pk_hazir.get("neden")}

    pk = {
        "pk1": pk1_large_cap(pk1_kosum, sonuc016, O),
        "pk2": (pk2_dogrulama_tablosu(birincil["_ic"], p1, tohum, np, pd)
                if birincil.get("_ic") else {"n": 0, "neden": birincil.get("neden")}),
        "pk3": pk3_sentetik(etkin, b_uyelik, b_gunler, tohum),
        "pk4": (pk4_olay_yansimasi(birincil["_ic"], olaylar, tohum,
                                   olay_meta.get("ornek_n") or 10,
                                   olay_meta.get("tolerans") or 1, pd)
                if (birincil.get("_ic") and olaylar)
                else {"ornek_n": 0, "neden": olay_meta.get("neden") or "panel ölçülemedi"}),
        "olay_kumesi_meta": olay_meta,
    }

    # ---------- duyarlılık ----------
    duyarlilik = {"kip": ARGV.belirsiz, "birincil": BIRINCIL_KIP,
                  "belirsiz_semboller": sorted(belirsiz),
                  "belirsiz_kaynak": bel_kaynak, "belirsiz_neden": bel_neden, "kiyas": []}
    if "haric" in kosumlar and BIRINCIL_KIP in kosumlar:
        d_, h_ = kosumlar[BIRINCIL_KIP], kosumlar["haric"]
        for bacak, alan in (("i_ust20_kohort_fazlasi", "ort"),
                            ("ii_a1_kova_tabanli_fazla", "ort"),
                            ("ii_b_artik_ic_fazla", "ic")):
            for h in ("10", "20"):
                dv = ((d_.get("bacaklar") or {}).get(bacak) or {}).get(h) or {}
                hv = ((h_.get("bacaklar") or {}).get(bacak) or {}).get(h) or {}
                duyarlilik["kiyas"].append({
                    "bacak": bacak, "ufuk": h,
                    "dahil_deger": dv.get(alan), "dahil_anlamli": dv.get("anlamli"),
                    "haric_deger": hv.get(alan), "haric_anlamli": hv.get("anlamli"),
                    "isaret_ayni": None if (dv.get("anlamli") is None or hv.get("anlamli") is None)
                                   else bool(dv.get("anlamli") == hv.get("anlamli"))})

    # ---------- evren muhasebesi ----------
    V = (birincil.get("_ic") or {}).get("V")
    em = {
        "pencere_baslangic": baslangic.isoformat(), "pencere_baslangic_kaynak": bas_kaynak,
        "pencere_bitis": bitis.isoformat(), "pencere_bitis_kaynak": bitis_kaynak,
        "as_of_satir_n": len(etkin), "kohort_ham_satir_n": ham_n,
        "pencere_oncesi_capa_satiri_var_mi": capa,
        "isim_n_birlesim": len(birlesim),
        "son_gun_uye_n": len(b_uyelik.get(b_gunler[-1], frozenset())) if b_gunler else None,
        "gozlem_gunu_n": len(b_gunler),
        "uye_gun_hucre": (birincil.get("uyelik_suzgeci") or {}).get("panel_satir_uye"),
        "olculen_sembol_n": (birincil.get("uyelik_suzgeci") or {}).get("sembol_uye"),
        "etkin_baslangic_olculen": (str(V["date"].min()) if V is not None and not V.empty
                                    else None),
        "etkin_baslangic_neden": (None if V is not None and not V.empty
                                  else "kesit kurulamadı — etkin başlangıç ÖLÇÜLEMEDİ"),
        "isinma_notu": ISINMA_NOTU,
        "belirsiz_n": len(belirsiz), "belirsiz_semboller": sorted(belirsiz),
        "belirsiz_kaynak": bel_kaynak, "belirsiz_neden": bel_neden,
    }

    # ---------- girdi damgası ----------
    def dmg(yol):
        sha, neden = _sha_veya_neden(yol)
        return {"yol": None if yol is None else str(yol), "sha256": sha, "neden": neden}

    bars_manifestleri = sorted(pathlib.Path(ARGV.bars_dir).parent.glob("bars_manifest_*.json"))
    girdi = {
        "kohort_csv": dmg(ARGV.kohort), "shares_csv": dmg(ARGV.shares),
        "kart": dmg(kart), "kart092": dmg(kart092), "elle_esleme": dmg(esleme),
        "kapsama_haritasi": dmg(ARGV.kapsama), "sonuc_016_referans": dmg(sonuc016),
        "bars_manifest": dmg(bars_manifestleri[-1] if bars_manifestleri else None),
        "bars_dizin": {"yol": str(ARGV.bars_dir), "sha256": None,
                       "neden": "dizin — tek sha yok; isim başına sha bars_manifest'tedir"},
        "olcum_kodu": dmg(pathlib.Path(__file__).resolve()),
        "k016": dmg(yuzey["wp2_dizin"] / "k016.py"),
        "wp2_ortak": dmg(yuzey["wp2_dizin"] / "ortak.py"),
        "parti1_ortak": dmg(repo / "research" / "olcumler" / "edg093_midcap_pit" / "ortak.py"),
        "bars_integrity_defteri": yuzey["defter"],
    }

    k016 = yuzey["k016"]
    sabitler = {
        "kaynak": "SABİTLER İTHAL EDİLİR — bu dosyada yeniden yazılmaz; v490 çivisi eşitliği ölçer",
        "HORIZONS": list(k016.HORIZONS), "UST_PCT": k016.UST_PCT,
        "KONTROL_DILIM": k016.KONTROL_DILIM, "KOVA_MIN": k016.KOVA_MIN,
        "BLOCK": O.BLOCK, "BOOT": O.BOOT, "BOOT_IC": O.BOOT_IC, "MIN_SLICE": O.MIN_SLICE,
        "MIN_KESIT": O.MIN_KESIT, "MALIYET_BPS": O.MALIYET_BPS,
        "BAR_MIN_UZUNLUK": int(O.BAR_MIN_UZUNLUK), "BAYAT_GUN": O.BAYAT_GUN,
    }

    sonuc = {
        "kart": KART_ID, "aile": "pit_midcap_ust_sinir",
        "asama": "ANA ÖLÇÜM Parti-2 — turnover ana etkisi (EDG-016 tasarımı aynen)",
        "hukum": HUKUM,
        "rol": "ölçüm ajanı — HÜKÜM VERMEZ, hüküm ÖNERİSİ DE YAZMAZ; kart dosyasına DOKUNULMADI",
        "okuyan": "(1) Rol-1: hüküm AYNI turda karta + K defterine işlenir (CLAUDE.md §5); "
                  "(2) RAPOR_093_<damga>.md üreteci bu dosyayı okur.",
        "yazim_beyani": "YAZILAN HER ŞEY --cikti altındadır: sonuc_093_<damga>.json, "
                        "RAPOR_093_<damga>.md ve _state/ (config.STATE buraya çevrildi — canlı "
                        "boru hattının obs yazımları canlı deftere DÜŞMESİN diye). repo/state'e "
                        "yazım YOK; meridian.obs İTHAL EDİLMEDİ; ağa çıkılmadı.",
        "damga_utc": damga, "olcum_tarihi": dt.datetime.now(dt.timezone.utc).isoformat(),
        "uretici": "research/olcumler/edg093_midcap_pit/k093.py",
        "cozulen_yollar": yuzey["cozulen_yollar"],
        "DURUM": "OLCULDU" if birincil.get("DURUM") == "OLCULDU" else "OLCULEMEDI",
        "girdi_damgasi": girdi,
        "sabitler": sabitler,
        "evren_muhasebesi": em,
        "kosumlar": {k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")}
                     for k, v in kosumlar.items()},
        "yanlilik_gostergesi": yanlilik_gostergesi(
            etkin, b_uyelik, b_gunler, birincil.get("bar_muhasebesi") or {},
            ARGV.kapsama, belirsiz),
        "duyarlilik_belirsiz": duyarlilik,
        "pk": pk,
        "tohum": {"deger": tohum, "kaynak": tohum_kaynak},
        "k_beyani": {"satirlar": [
            "K = 2 (kart `k_registry`): EDG-093-midcap-ust-dilim-fazlasi-20g ve "
            "EDG-093-midcap-artik-katki-20g — BİRİNCİL koşumdan (belirsiz `dahil`, kohort "
            "defteri AYNEN).",
            "@10 ufku TANIdır (kart: 1×2 olarak çarpılır); 5'li tablo, 9 kova hücresi ve "
            "likidite beyanı TANIdır, K harcamaz.",
            "Yanlılık göstergeleri, kohort istatistikleri ve belirsiz-isim duyarlılığı kartın "
            "lafzıyla BEYAN alanıdır — K'ye GİRMEZ (kart `k_registry` şerhi).",
            "Eşik kartın ön-kayıtlı tanımıdır: 'anlamlı pozitif' = %95 blok-CI alt sınırı > 0; "
            "sayısal bps eşiği YOKTUR ve bu kart yeni eşik UYDURMAZ.",
        ]},
        "ithal_yan_etkisi": ithal_yan_etkisini_geri_al(yuzey),
    }

    json_yolu = cikti / f"sonuc_093_{damga}.json"
    O.json_yaz(json_yolu, sonuc)
    rapor_yolu = cikti / f"RAPOR_093_{damga}.md"
    rapor_yolu.write_text(rapor_metni(sonuc), encoding="utf-8")

    print(f"YAZILDI: {json_yolu}")
    print(f"YAZILDI: {rapor_yolu}")
    print(f"durum={sonuc['DURUM']} · koşum={list(kosumlar)} · üye-gün="
          f"{em.get('uye_gun_hucre')} · hüküm={HUKUM}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
