#!/usr/bin/env python3
"""ops/replay_sweep.py — REPLAY-SWEEP OTOMASYON İSKELETİ (OPT Faz-1/WP3-B, 2026-08-23).

SINIR BEYANI (önce bu okunur):
  Bu iskelet YENİ ölçüm sınıfı İCAT ETMEZ. Dört emsalin — edg045_stop_slip_2026-08-22,
  edg046_secilim_2026-08-23, edg048_chop_tabani_2026-08-23, exe008_limit_yeni_dunya_2026-08-23 —
  ORTAK omurgasının ortaklaştırılmasıdır. Emsalden sapan kart (farklı şasi, şasi-parametre
  enjeksiyonu, farklı dünya beklentisi, farklı bootstrap birimi/yöntemi, künye-tazeleme
  ihtiyacı, çok-fazlı özel akış vb.) bu iskeleti KULLANMAZ — ölçümü elle yazılır.

NE YAPAR — kart-güdümlü koşum iskeleti:
  (a) Ön-kayıt kartının YAML'ından okur (kart şeması mevcut kartlardan ÖLÇÜLDÜ, varsayılmadı):
      · hücre listesi: `parameter_grid` eksenlerinin kartezyen çarpımı (K ÇARPILARAK sayılır —
        EXE-008 emsali; tek eksen dejenere hâl). Eksen/değer sırası karttaki sırayla.
      · seed: kart metninden ("seed 20260812" / "seed=20260812" — dört emsal kartın dördünde
        serbest metinde). Ölçülemezse UYDURULMAZ: None + neden, koşum BAŞLAMADAN DURUR.
      · künye yolu: kart metnindeki `*KUNYESI*.json` adı `research/olcumler/` altında
        tekilleştirilir; tekilleşmezse enjeksiyon modülünün beyanlı `KUNYE_YOLU`su; o da yoksa
        None + neden → DURUR. Kaynağı raporda beyan edilir.
  (b) DONMUŞ ORTAK BLOKLAR (dört emsalden harfi harfine; kanonik biçim edg048):
      · sandbox kurulumu: edg032b şasisi KAYNAKTAN derlenerek modül olarak yüklenir
        (`ops.sasi_yukleyici`; `__pycache__` OKUNMAZ — 2026-08-30 bayat-bytecode ölçümü),
        `SANDBOX`ı ölçüm dizinine çevrilir (artefakt koruması YAPISAL), `ARMED_BEKLENEN` B1
        yasasına çevrilir (edg032c'nin BEYANLI TEK UYARLAMASI; motor ARMED_SETUPS B1'den
        saparsa BAŞLAMADAN durur), `kosum(run, smoke)` yolu OLDUĞU GİBİ çağrılır. Şasi-parametre
        enjeksiyonu YOK (merkez hücre) — buna ihtiyaç duyan kart iskeleti kullanmaz (sınır beyanı).
      · motor-sha künye kapısı (ÖN-UÇUŞ): 4 dosya (broker/backtest/strategy/guard) künyenin
        `motor_sha256.kosum1_once` kaydıyla birebir değilse koşum YAPILMADAN DURUR ve raporlar.
        TAZELEME PROTOKOLÜ DAHİL DEĞİL — künye tazelemek Rol-1 kararıdır (edg048 protokol
        emsali); iskelet yalnız DURUR.
      · kontrol-hücresi bayt-özdeşlik kapısı: kontrol koşumu taban dizinin (künye dizini /
        kosum1[_smoke]) ÜÇ defteriyle (islemler_tam + islemler slim + seanslar) sha256
        BAYT-ÖZDEŞ olmalı; tam koşumda künye çivisi (`determinizm_kaniti.kapi_sha256`) ayrıca
        sınanır (edg046/048/exe008 AYNEN). Düşerse DURUR.
      · hücre-başı motor sha önce/sonra: koşum içinde değişen ya da künyeden sapan hücre
        geçersiz → DURUR.
      · eşlenik ay-kümeli bootstrap: birim=AY, iki kol AYNI ayı görür, B=5000 (DONMUŞ),
        seed KARTTAN, yüzdelik CI (edg040/045/046/048 `delta_pnl_ci` AYNEN).
      · damga biçimleri: DURDU anahtarı + `sonuc_grid{_smoke}.json` + exit 2 (edg048 kanonik);
        temiz koşum exit 0. Duman koşumunda Δ/CI değerlendirilmez (kablo sınaması).
  (c) HÜCRE-ÖZGÜ ENJEKSİYON NOKTASI: kart-başına küçük bir python modülü (edg046 süreç-içi
      sarmalayıcı deseni). Arayüz aşağıda; `--stub` örnek modül üretir. Motor DOSYASINA
      dokunulmaz; tüm yamalar süreç-içi ve finally ile geri alınır (kanıtı sha kapıları).
  (d) HÜKÜM YOK: iskelet SAYI üretir, karar kuralı UYGULAMAZ — success_metric/kill okuması
      Rol-1'in işidir. Emsallerdeki kill#N numaraları KARTA aittir; iskelet kapıları adla anar
      (motor-künye / bayt-özdeşlik / öz-sınama / hücre-sha), numara eşlemesini Rol-1 yapar.

K-DEFTERİ DİSİPLİNİ: iskelet K SAYMAZ — K muhasebesi kartın `k_registry`sindedir; hücre
listesi karttan ÇARPILARAK türetilir ve yalnız bilgi olarak raporlanır. Kart DOKUNULMAZDIR:
iskelet karta TEK BAYT yazmaz.

ENJEKSİYON MODÜLÜ ARAYÜZÜ (zorunlu adlar `ZORUNLU_ARAYUZ`te; eksikse BAŞLAMADAN durur):
  KONTROL_HUCRE: dict                     — kontrol hücresi parametreleri (şasi kapısı hücresi)
  yeni_kayit() -> dict                    — hücre-başı ham yakalama kabı
  enjekte(hucre, kayit, kontrol=False)    — context manager; süreç-içi yama. KONTROL hücresinde
                                            BAYT-NÖTR olmalı: bayt-özdeşlik kapısı şasiyi VE
                                            yüzey nötrlüğünü BİRLİKTE kanıtlar (edg040/045).
  oz_sinama(hucre, kayit, ciktilar, kontrol=False) -> dict
                                          — "kill2_gecti" (bool) anahtarı ZORUNLU; sayı getirir,
                                            hüküm vermez. ciktilar = {sonuc, defter, seanslar,
                                            outdir, run, ek}.
  kol_kimligi(hucre, kontrol=False) -> dict — kol kimliği damgası (exe006 Kritik-1 emsali).
  İsteğe bağlı: on_sinama() -> {"gecti": bool, ...} (sentetik ön-uçuş; düşerse DURUR) ·
  KUNYE_YOLU: str (karttan çözülemezse beyanlı yedek) · run_adi(hucre) -> str.

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen None + neden) · YASA-4 (sessiz-yutma işaretli) · git
KOŞULMAZ · state/ YAZILMAZ (şasi kendi sandbox'ına yönlendirir) · test suite KOŞULMAZ · motor
ve kart dosyalarına DOKUNULMAZ.

KULLANIM:
  ops/replay_sweep.py --stub <yol.py>          # örnek enjeksiyon modülü stub'ı üret
  ops/replay_sweep.py --kart research/cards/X.yaml --enjeksiyon <modul.py> \
                      --dizin research/olcumler/<olcum_dizini> [--smoke]
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import itertools
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]


def _sasi_yukleyici():
    """`ops.sasi_yukleyici`yi KENDİ checkout'undan çözer.

    NEDEN FONKSİYON, NEDEN `sys.path` EKİ — ÖLÇÜLDÜ (2026-08-30). Bu dosya DOĞRUDAN koşuluyor
    (`.venv/bin/python ops/replay_sweep.py --kart …`, `docs/ARAC-REPLAY-SWEEP-2026-08-23.md`);
    o durumda `sys.path[0]` kök DEĞİL, `ops/` DİZİNİdir. `ops.` ön eki o zaman editable-install
    `.pth`i üzerinden BAŞKA BİR CHECKOUT'a düşer: worktree'den koşarken `ModuleNotFoundError`
    alındı (ölçüldü), ana checkout'ta ise hata bile vermez — sessizce ORANIN kopyasını yüklerdi,
    yani bu deponun "iki kopya sessizce ayrışır" sınıfı. Kök önce eklenir.

    İki yükleyici de (şasi + enjeksiyon) buradan geçer; gerekçe tek yerde durur.
    """
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    import ops.sasi_yukleyici as _sy          # kaynaktan derler; `__pycache__` okunmaz/yazılmaz
    return _sy


# ── DONMUŞ OMURGA SABİTLERİ (dört emsalden; sapan kart iskeleti kullanmaz) ────────────────────
REFERANS_SASI = REPO / "research" / "olcumler" / "edg032b_tamsatir_2026-08-13" / "olcum.py"
B1_YASA = ("breakout_vcp", "exhaustion_hammer", "momentum_burst")   # edg032c uyarlaması AYNEN
MOTOR_SHA_DOSYALAR = ("broker.py", "backtest.py", "strategy.py", "guard.py")
BOOT_ITER = 5000                      # DONMUŞ (dört emsal); seed KARTTAN okunur
KONTROL_RUN = "kontrol"               # taban defter adları *_kontrol*.json — ad sözleşmesi
KAPI_DEFTERLER = ("islemler_tam_kontrol.json", "islemler_kontrol.json", "seanslar_kontrol.json")
ZORUNLU_ARAYUZ = ("KONTROL_HUCRE", "yeni_kayit", "enjekte", "oz_sinama", "kol_kimligi")
ISTEGE_BAGLI_ARAYUZ = ("on_sinama", "KUNYE_YOLU", "run_adi")
HUKUM_YOK_BEYANI = ("Bu rapor HÜKÜM İÇERMEZ. Karar kuralının (success_metric) okunması ve "
                    "kill eşlemesi Rol-1'in işidir; iskelet yalnız sayı getirir.")
K_DEFTERI_BEYANI = ("iskelet K SAYMAZ — K muhasebesi kartın k_registry'sindedir; hücre listesi "
                    "karttan ÇARPILARAK türetildi ve yalnız bilgi olarak raporlanır.")

_SEED_DESENI = re.compile(r"seed[\s=:]{0,3}(\d{4,})")
_KUNYE_DESENI = re.compile(r"\b[\w.]*KUNYESI\w*\.json\b")


# ---------------------------------------------------------------------------------------------
# (a) KART OKUMA — şema mevcut kartlardan ÖLÇÜLDÜ (parameter_grid yapısal; seed/künye metinde)
# ---------------------------------------------------------------------------------------------
def kart_oku(kart_yolu: pathlib.Path, arama_koku: pathlib.Path | None = None) -> dict:
    """Ön-kayıt kartını okur: hücre listesi (kartezyen ÇARPIM), seed, künye yolu.

    UYDURMA YASAĞI: ölçülemeyen alan None + neden döner; koşucu bu alanlarla BAŞLAMAZ.
    Karta TEK BAYT yazılmaz (salt okuma)."""
    import yaml   # geç-yükleme: iskeletin importu yaml'sız ortamda da çalışsın

    kart_yolu = pathlib.Path(kart_yolu)
    metin = kart_yolu.read_text(encoding="utf-8")
    kart = yaml.safe_load(metin)

    # hücre listesi — parameter_grid eksenlerinin kartezyen çarpımı (K ÇARPILARAK; EXE-008 emsali)
    grid = kart.get("parameter_grid")
    hucreler: list[dict] | None = None
    grid_nedeni = None
    if isinstance(grid, dict) and grid and all(isinstance(v, list) and v for v in grid.values()):
        adlar = list(grid.keys())                      # karttaki eksen sırası korunur
        hucreler = [dict(zip(adlar, kombo))
                    for kombo in itertools.product(*(grid[a] for a in adlar))]
    else:
        grid_nedeni = ("kartta parameter_grid ölçülemedi: eksen→liste sözlüğü bekleniyor, "
                       f"bulunan: {type(grid).__name__}")

    # seed — kart metninden (dört emsal kartın dördünde serbest metinde; satır sarkması dahil)
    seed_adaylari = sorted({int(x) for x in _SEED_DESENI.findall(metin)})
    if len(seed_adaylari) == 1:
        seed, seed_nedeni = seed_adaylari[0], None
    elif not seed_adaylari:
        seed, seed_nedeni = None, "kart metninde seed ölçülemedi (desen: 'seed <sayı>')"
    else:
        seed, seed_nedeni = None, (f"kart metninde ÇELİŞEN seed'ler: {seed_adaylari} — "
                                   "tekilleşmedi, uydurulmaz")

    # künye yolu — kart metnindeki *KUNYESI*.json adı research/olcumler altında tekilleştirilir
    kunye_yolu, kunye_nedeni = _kunye_coz(metin, arama_koku)

    return {
        "kart_yolu": str(kart_yolu),
        "kart_id": kart.get("card_id"),
        "status": kart.get("status"),
        "k_registry": kart.get("k_registry"),
        "eksenler": (list(grid.keys()) if isinstance(grid, dict) else None),
        "hucreler": hucreler,
        "hucre_n": (len(hucreler) if hucreler is not None else None),
        "hucreler_olculemedi_nedeni": grid_nedeni,
        "seed": seed,
        "seed_olculemedi_nedeni": seed_nedeni,
        "kunye_yolu": (str(kunye_yolu) if kunye_yolu else None),
        "kunye_olculemedi_nedeni": kunye_nedeni,
    }


def _kunye_coz(metin: str, arama_koku: pathlib.Path | None) -> tuple[pathlib.Path | None, str | None]:
    """Kart metnindeki künye dosya adını (`*KUNYESI*.json`) diskte tekilleştirir.

    Tekilleşme sırası: (1) ad tek dizinde bulunuyorsa o; (2) birden çok dizinde bulunuyorsa
    dizin adı kart metninde ANILAN tek aday; (3) yoksa None + neden (modülün beyanlı
    KUNYE_YOLU'su devreye girebilir — koşucu kaynağı raporlar)."""
    kok = pathlib.Path(arama_koku) if arama_koku else (REPO / "research" / "olcumler")
    adlar = sorted(set(_KUNYE_DESENI.findall(metin)))
    if not adlar:
        return None, "kart metninde künye dosya adı ölçülemedi (desen: *KUNYESI*.json)"
    if len(adlar) > 1:
        return None, f"kart metninde birden çok künye adı: {adlar} — tekilleşmedi"
    ad = adlar[0]
    adaylar = sorted(kok.glob(f"*/{ad}"))
    if len(adaylar) == 1:
        return adaylar[0], None
    if not adaylar:
        return None, f"künye adı '{ad}' {kok} altında bulunamadı"
    metinde = [a for a in adaylar if a.parent.name.split("_")[0] in metin]
    if len(metinde) == 1:
        return metinde[0], None
    return None, (f"künye adı '{ad}' birden çok dizinde: {[str(a) for a in adaylar]} — "
                  "kart metniyle tekilleşmedi")


# ---------------------------------------------------------------------------------------------
# (b) DONMUŞ ORTAK BLOKLAR — sha yardımcıları + kapılar
# ---------------------------------------------------------------------------------------------
def _sha_full(p: pathlib.Path) -> str | None:
    try:
        return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
    except OSError:
        return None    # ölçülemedi (dosya yok/okunamadı)


def motor_sha(motor_dizini: pathlib.Path | None = None) -> dict:
    d = pathlib.Path(motor_dizini) if motor_dizini else (REPO / "meridian")
    return {f: _sha_full(d / f) for f in MOTOR_SHA_DOSYALAR}


def motor_kunye_kiyas(m: dict, kunye_yolu: pathlib.Path) -> dict:
    """Motor sha (4 dosya) ↔ künye `motor_sha256.kosum1_once` kaydı (edg048/exe008 AYNEN)."""
    kunye = json.loads(pathlib.Path(kunye_yolu).read_text())
    ref = kunye["motor_sha256"]["kosum1_once"]
    kiyas = {f: {"olculen": m[f], "kunye": ref[f]["sha256"], "esit": m[f] == ref[f]["sha256"]}
             for f in MOTOR_SHA_DOSYALAR}
    return {"dosyalar": kiyas, "kunyeyle_ayni": all(v["esit"] for v in kiyas.values())}


def hucre_motor_kapisi(m_once: dict, m_sonra: dict, kunye_yolu: pathlib.Path) -> dict:
    """Hücre-başı sha kapısı: koşum İÇİNDE değişmemiş VE iki uçta künyeyle birebir olmalı."""
    k_once = motor_kunye_kiyas(m_once, kunye_yolu)
    k_sonra = motor_kunye_kiyas(m_sonra, kunye_yolu)
    ayni = m_once == m_sonra
    return {"motor_sha_ayni": ayni,
            "kunye_once": k_once, "kunye_sonra": k_sonra,
            "gecti": bool(ayni and k_once["kunyeyle_ayni"] and k_sonra["kunyeyle_ayni"])}


def sasi_kapisi(yerel_dir: pathlib.Path, taban_dir: pathlib.Path,
                kunye_yolu: pathlib.Path | None, smoke: bool, yaz: bool = True) -> dict:
    """Kontrol-hücresi BAYT-ÖZDEŞLİK kapısı (edg046/048/exe008 AYNEN): üç defter sha256
    bayt-özdeş + (tam koşumda) künye çivisi — referans dosyalar künyenin `determinizm_kaniti.
    kapi_sha256` kaydının KENDİSİ olmalı. Düşerse koşucu DURUR."""
    yerel_dir, taban_dir = pathlib.Path(yerel_dir), pathlib.Path(taban_dir)
    ek = "_smoke" if smoke else ""
    sonuc = {}
    for ad_tam in KAPI_DEFTERLER:
        govde = ad_tam[:-len(".json")]
        y = yerel_dir / f"{govde}{ek}.json"
        r = taban_dir / f"{govde}{ek}.json"
        sy, sr = _sha_full(y), _sha_full(r)
        sonuc[ad_tam] = {"yerel_sha256": sy, "taban_sha256": sr,
                         "bayt_ozdes": (sy is not None and sy == sr),
                         "olculemedi_nedeni": (None if (sy and sr) else
                                               f"dosya okunamadı: yerel={bool(sy)} taban={bool(sr)}")}
    kunye_tutarli = None
    if not smoke and kunye_yolu is not None:
        kunye = json.loads(pathlib.Path(kunye_yolu).read_text())
        ks = kunye["determinizm_kaniti"]["kapi_sha256"]
        kunye_tutarli = all(sonuc[f]["taban_sha256"] == ks[f] for f in KAPI_DEFTERLER)
    gecti = all(v["bayt_ozdes"] for v in sonuc.values()) and (kunye_tutarli is not False)
    out = {"taban": str(taban_dir), "bayt_kiyas": sonuc,
           "kunye_sha_tutarli": kunye_tutarli, "kill1_gecti": bool(gecti)}
    if yaz:
        (yerel_dir / f"sasi_kapisi{ek}.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  ŞASİ KAPISI{ek}: bayt={all(v['bayt_ozdes'] for v in sonuc.values())} "
          f"künye_tutarlı={kunye_tutarli} → {'GEÇTİ' if gecti else 'DÜŞTÜ — ölçüm DURUR'}")
    return out


def delta_pnl_ci(taban_defter: list, hucre_defter: list, aylar: list[str], seed: int) -> dict:
    """EŞLENİK ay-kümeli bootstrap (edg040/045/046/048 AYNEN): birim = AY, iki kol AYNI ayı
    görür, B=5000 (DONMUŞ), seed KARTTAN, yüzdelik CI."""
    import numpy as np
    M = len(aylar)

    def seri(defter):
        pnl = {a: 0.0 for a in aylar}
        disi = 0
        for t in defter:
            a = str(t["ts_open"])[:7]
            if a not in pnl:
                disi += 1                  # takvim dışı ay — sayılır, sessiz düşmez (YASA-4)
                continue
            pnl[a] += float(t.get("pnl_dollars") or 0.0)
        return np.array([pnl[a] for a in aylar], dtype=float), disi

    A_t, disi_t = seri(taban_defter)
    A_h, disi_h = seri(hucre_defter)
    rng = np.random.default_rng(int(seed))
    idx = np.arange(M)
    f = np.empty(BOOT_ITER)
    for i in range(BOOT_ITER):
        pick = rng.choice(idx, size=M, replace=True)     # EŞLENİK: aynı çekiliş iki kola
        f[i] = float(A_h[pick].sum()) - float(A_t[pick].sum())
    lo = round(float(np.percentile(f, 2.5)), 2)
    hi = round(float(np.percentile(f, 97.5)), 2)
    nokta = round(float(A_h.sum() - A_t.sum()), 2)
    return {"delta_pnl": nokta, "ci95": [lo, hi], "n_ay": M,
            "takvim_disi_islem": {"taban": disi_t, "hucre": disi_h},
            "sifir_disinda": ("evet (CI-alt > 0)" if lo > 0 else
                              "evet (CI-üst < 0)" if hi < 0 else "hayır (0 içinde)"),
            "yontem": ("EŞLENİK ay-kümeli bootstrap · birim = AY (iki kol AYNI ayı görür) · "
                       f"B={BOOT_ITER} · seed={int(seed)} (karttan) · yüzdelik")}


def rapor_yaz(rapor: dict, yol: pathlib.Path) -> int:
    """DAMGA (edg048 kanonik): DURDU anahtarı varsa exit 2, yoksa 0; her iki hâlde de
    sonuc_grid dosyası yazılır — DURDU raporu da KANIT'tır, sessiz kaybolmaz."""
    yol = pathlib.Path(yol)
    yol.write_text(json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"yazıldı: {yol}")
    return 2 if "DURDU" in rapor else 0


def artik_bul(dizin: pathlib.Path, outdir: pathlib.Path, run: str, ek: str) -> list[str]:
    """Ön-uçuş artık taraması (edg048 deseni): eski koşum çıktısı/state'i DURDURUR — iskelet
    SİLMEZ (yıkıcı değil), elle kaldırılması istenir."""
    artiklar = []
    if (pathlib.Path(dizin) / f"state_{run}{ek}").exists():
        artiklar.append(f"state_{run}{ek}")
    if (pathlib.Path(outdir) / f"sonuc_{run}{ek}.json").exists():
        artiklar.append(f"sonuc_{run}{ek}.json")
    return artiklar


def _pf(defter: list) -> tuple[float | None, str | None]:
    """PF tam defterden (EDG-037 tanımı; dört emsal AYNEN)."""
    poz = sum(float(t["pnl_dollars"]) for t in defter if float(t["pnl_dollars"]) > 0)
    neg = sum(float(t["pnl_dollars"]) for t in defter if float(t["pnl_dollars"]) < 0)
    if neg < 0:
        return round(poz / abs(neg), 4), None
    return None, "kayıp bacağı boş (Σpnl<0 yok) — PF paydası sıfır, TANIMSIZ"


# ---------------------------------------------------------------------------------------------
# (b) sandbox kurulumu — şasi modül olarak yüklenir (edg046/048/exe008 `referans_modul` AYNEN)
# ---------------------------------------------------------------------------------------------
def referans_modul(sandbox: pathlib.Path):
    """edg032b şasisini modül olarak yükler; SANDBOX'ı ölçüm dizinine çevirir; ARMED_BEKLENEN'i
    B1 yasasına çevirir (edg032c'nin beyanlı TEK uyarlaması AYNEN); motoru B1'e assert'ler."""
    # Şasi KAYNAKTAN derlenir: argv/SystemExit dansı AYNEN korunur, `__pycache__` okunmaz.
    m = _sasi_yukleyici().referans_sasi_yukle(REFERANS_SASI)
    m.SANDBOX = pathlib.Path(sandbox)   # artefakt koruması: referans dizinlere ASLA yazılmaz
    eski_beklenen = tuple(m.ARMED_BEKLENEN)
    m.ARMED_BEKLENEN = B1_YASA
    from meridian import strategy as _st          # motor importu: geç-yükleme, salt okuma
    assert tuple(_st.ARMED_SETUPS) == B1_YASA, \
        f"MOTOR B1 YASASINDAN SAPMIŞ: {_st.ARMED_SETUPS} ≠ {B1_YASA} — koşum durdu"
    return m, {"eski_ARMED_BEKLENEN": list(eski_beklenen),
               "yeni_ARMED_BEKLENEN": list(B1_YASA),
               "motor_ARMED_SETUPS": list(_st.ARMED_SETUPS),
               "beyan": ("edg032c TEK uyarlaması AYNEN: yüklenen şasi modülünün ARMED_BEKLENEN "
                         "sabiti B1 yasasına çevrildi (dünya-beklentisi; motor DEĞİL). "
                         "Şasi-parametre enjeksiyonu YOK (merkez hücre).")}


# ---------------------------------------------------------------------------------------------
# (c) enjeksiyon modülü — arayüz doğrulama + yükleme + örnek stub
# ---------------------------------------------------------------------------------------------
def arayuz_dogrula(modul) -> dict:
    """Enjeksiyon modülü sözleşmesi ÖLÇÜLÜR, varsayılmaz: zorunlu adlar eksikse koşum başlamaz."""
    eksik = [ad for ad in ZORUNLU_ARAYUZ if not hasattr(modul, ad)]
    return {"eksik": eksik, "gecerli": not eksik,
            "istege_bagli_var": {ad: hasattr(modul, ad) for ad in ISTEGE_BAGLI_ARAYUZ}}

def enjeksiyon_modulu_yukle(yol: pathlib.Path):
    yol = pathlib.Path(yol)
    # KAYNAKTAN derlenir (2026-08-30) — bu yükleyicide risk EN YÜKSEĞİDİR ve sebebi yapısaldır:
    # enjeksiyon modülü ölçümün DEĞİŞKEN parçasıdır (şasi donuk, enjeksiyon her kart için yazılır
    # ve kolları ayarlanırken tekrar tekrar düzenlenir). Yani "aynı saniyede boyut-koruyan
    # düzenleme" önkoşulu tam da burada, düzenle-koş-düzenle döngüsünde doğar. Bayat bytecode
    # koşsaydı `oz_sinama`/`kol_kimligi` ESKİ sürümden gelir, aşağıdaki arayüz kapısı yine
    # GEÇERDİ (arayüz adları değişmez, davranış değişir) ve ölçüm sessizce yanlış kolu ölçerdi.
    m = _sasi_yukleyici().kaynaktan_yukle(yol, "replay_sweep_enjeksiyon")
    a = arayuz_dogrula(m)
    assert a["gecerli"], (f"enjeksiyon modülü arayüzü EKSİK: {a['eksik']} — koşum BAŞLAMADAN "
                          f"durdu (modül: {yol})")
    return m


def run_adi(modul, hucre: dict) -> str:
    """Hücre → koşum adı. Modül `run_adi` veriyorsa onunki; yoksa deterministik varsayılan.
    'kontrol' adı REZERVE (taban defter ad sözleşmesi)."""
    if hasattr(modul, "run_adi"):
        ad = str(modul.run_adi(hucre))
    else:
        ad = "_".join(f"{k}{v}" for k, v in hucre.items())
    ad = re.sub(r"[^A-Za-z0-9._-]", "-", ad)
    assert ad and ad != KONTROL_RUN, f"geçersiz run adı: {ad!r} ('kontrol' rezerve)"
    return ad


ORNEK_STUB = '''\
"""<KART-ID> — hücre-özgü enjeksiyon modülü (ops/replay_sweep.py arayüzü) · STUB.

Bu dosya `ops/replay_sweep.py --stub` çıktısıdır: ölçüme girmeden önce kartın enjeksiyon
yüzeyi KODDAN OKUNARAK doldurulur (varsayılmaz — satır çivisi/tekillik assert'i önerilir,
edg045 `kaynak_civisi_kontrol` ve edg046 `sort_lambda_bul` emsalleri). Desen: edg046
süreç-içi sarmalayıcı — motor DOSYASINA dokunulmaz, yama finally ile geri alınır.

GÜVENLİK: `on_sinama()` doldurulana dek `gecti: False` döner — stub yanlışlıkla ölçüme
GİREMEZ (iskelet ön-sınama düşerse koşumu başlatmaz).
"""
import contextlib

# kontrol hücresi parametreleri — enjekte() bu parametrelerle BAYT-NÖTR olmalı
# (bayt-özdeşlik kapısı şasiyi VE yüzey nötrlüğünü birlikte kanıtlar — edg040/045 deseni)
KONTROL_HUCRE = {"ek_slip_bps": 0.0}


def yeni_kayit() -> dict:
    return {"cikis": []}


@contextlib.contextmanager
def enjekte(hucre, kayit, kontrol=False):
    """Süreç-içi yama örneği (edg045 close_position sarmalayıcısı): reason=='stop' iken
    raw_exit → raw_exit×(1−ek). Kendi kartının yüzeyine göre YENİDEN yazılır."""
    from meridian import broker as B              # geç-yükleme: motor importu yalnız koşumda
    asil = B.PaperBroker.close_position
    ek = float(hucre["ek_slip_bps"]) / 10000.0

    def sarmal(self, ticker, raw_exit, reason, ts):   # imza motorla BİREBİR (ad uydurma yok)
        enj = raw_exit * (1.0 - ek) if reason == "stop" else raw_exit
        row = asil(self, ticker, enj, reason, ts)
        kayit["cikis"].append({"ticker": ticker, "ts": ts, "reason": reason,
                               "raw_exit_orig": float(raw_exit),
                               "raw_exit_enjekte": float(enj),
                               "defter_exit": float(row["exit"])})
        return row

    B.PaperBroker.close_position = sarmal
    try:
        yield
    finally:
        B.PaperBroker.close_position = asil


def oz_sinama(hucre, kayit, ciktilar, kontrol=False) -> dict:
    """Öz-sınama: SAYI getirir, hüküm vermez; TÜM satırlar sınanır (ilk-N değil).
    Gerçek kartta deftere çivilenir (edg045 S2/edg046 Ç1 emsali)."""
    ek = float(hucre["ek_slip_bps"]) / 10000.0
    bozuk = []
    for c in kayit["cikis"]:
        beklenen = (c["raw_exit_orig"] * (1.0 - ek)
                    if c["reason"] == "stop" else c["raw_exit_orig"])
        if abs(c["raw_exit_enjekte"] - beklenen) > 1e-9:
            bozuk.append(c)
    return {"n_cikis": len(kayit["cikis"]), "bozuk_n": len(bozuk), "bozuk_ilk50": bozuk[:50],
            "kill2_gecti": (len(kayit["cikis"]) > 0 and not bozuk),
            "kill2_olculemedi_nedeni": (None if kayit["cikis"] else
                                        "yakalanan çıkış yok — sınama boş, sınama değildir"),
            "beyan": "STUB sınaması — kartın gerçek öz-sınaması yazılmadan ölçüm koşulamaz"}


def kol_kimligi(hucre, kontrol=False) -> dict:
    return {"hucre": dict(hucre), "kontrol": bool(kontrol),
            "enjeksiyon": "STUB — doldurulmadan ölçümde kullanılamaz"}


def on_sinama() -> dict:
    """Sentetik ön-uçuş (edg046 ceza_on_sinama / edg048 replika_on_sinama emsali):
    motor koşmadan enjeksiyonun doğruluğu VE ayırt ediciliği sınanır."""
    return {"gecti": False,
            "neden": "STUB doldurulmadı — gerçek ön-sınama yazılmadan koşum başlamaz"}
'''


def ornek_stub_uret(yol: pathlib.Path) -> pathlib.Path:
    yol = pathlib.Path(yol)
    assert not yol.exists(), f"{yol} zaten var — üzerine yazılmaz (elle kaldır)"
    yol.write_text(ORNEK_STUB, encoding="utf-8")
    print(f"örnek enjeksiyon stub'ı yazıldı: {yol}")
    return yol


# ---------------------------------------------------------------------------------------------
# HÜCRE KOŞUMU + SWEEP AKIŞI (sıra DONMUŞ: ön-uçuş → ön-sınama → kontrol+bayt → hücreler → Δ+CI)
# ---------------------------------------------------------------------------------------------
def hucre_kos(ref, modul, hucre: dict | None, run: str, smoke: bool,
              kunye_yolu: pathlib.Path, outdir: pathlib.Path) -> dict:
    """Tek hücre: enjekte → ŞASİYİ ÇAĞIR → öz-sınama + sha kapıları + özet damga."""
    kontrol = hucre is None
    params = dict(modul.KONTROL_HUCRE) if kontrol else dict(hucre)
    ek = "_smoke" if smoke else ""
    ref.HUCRELER.setdefault(run, {})       # merkez hücre — şasi-parametre enjeksiyonu YOK
    kayit = modul.yeni_kayit()
    m_once = motor_sha()
    with modul.enjekte(params, kayit, kontrol=kontrol):
        ref.kosum(run, smoke=smoke)        # ŞASİ: referansın kendi yolu, dokunulmadan
    m_sonra = motor_sha()
    kapi = hucre_motor_kapisi(m_once, m_sonra, kunye_yolu)

    d = json.loads((outdir / f"sonuc_{run}{ek}.json").read_text())
    defter = json.loads((outdir / f"islemler_tam_{run}{ek}.json").read_text())
    seans_yolu = outdir / f"seanslar_{run}{ek}.json"
    seanslar = json.loads(seans_yolu.read_text()) if seans_yolu.exists() else None
    ciktilar = {"sonuc": d, "defter": defter, "seanslar": seanslar,
                "outdir": outdir, "run": run, "ek": ek}

    oz = modul.oz_sinama(params, kayit, ciktilar, kontrol=kontrol)
    assert isinstance(oz, dict) and "kill2_gecti" in oz, \
        f"öz-sınama sözleşmesi bozuk ({run}): 'kill2_gecti' anahtarı yok — arayüz ihlali, DUR"
    (outdir / f"oz_sinama_{run}{ek}.json").write_text(
        json.dumps(oz, ensure_ascii=False, indent=1), encoding="utf-8")
    try:   # HAM yakalama diske — teşhis yeniden-koşum istemesin (edg040 dersi)
        (outdir / f"yakalama_{run}{ek}.json").write_text(
            json.dumps(kayit, ensure_ascii=False), encoding="utf-8")
        yakalama_notu = None
    except TypeError as e:                 # sessiz-yutma DEĞİL: adıyla raporlanır (YASA-4)
        yakalama_notu = f"yakalama json'a dökülemedi: {e} — modül kendi dökümünden sorumlu"

    perf = d.get("performans") or {}
    islem = d.get("islem") or {}
    pf, pf_neden = _pf(defter)
    ozet = {
        "kosum": run, "smoke": smoke,
        "hucre_parametreleri": params, "kontrol_hucresi": kontrol,
        "kol_kimligi": modul.kol_kimligi(params, kontrol=kontrol),
        "hucre_sasi": d.get("hucre"),
        "islem_n": islem.get("n"),
        "net_pnl_trades": perf.get("net_pnl_trades"),   # KANONİK (islem.net_pnl YOK — exe006 tuzağı)
        "net_pnl_equity": perf.get("net_pnl_equity"),
        "pf": pf, "pf_olculemedi_nedeni": pf_neden,
        "maxdd_kanonik": perf.get("maxdd_kanonik"), "maxdd_m2m": perf.get("maxdd_m2m"),
        "sharpe": perf.get("sharpe"), "avg_r": perf.get("avg_r"),
        "win_rate": perf.get("win_rate"), "total_return": perf.get("total_return"),
        "exit_reason_dagilim": islem.get("exit_reason_dagilim"),
        "setup_bazinda": islem.get("setup_bazinda"),
        "butunluk_gecerli": (d.get("butunluk") or {}).get("gecerli"),
        "sasi_kill3_temiz": (d.get("kill3_mtime") or {}).get("temiz"),
        "oz_sinama_kill2_gecti": bool(oz["kill2_gecti"]),
        "motor_sha_once": m_once, "motor_sha_sonra": m_sonra,
        "motor_kapisi": kapi, "motor_kapisi_gecti": kapi["gecti"],
        "yakalama_notu": yakalama_notu,
    }
    (outdir / f"hucre_{run}{ek}.json").write_text(
        json.dumps(ozet, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [{run}{ek}] n={ozet['islem_n']} net={ozet['net_pnl_trades']} pf={pf} "
          f"dd={ozet['maxdd_kanonik']} kill2={ozet['oz_sinama_kill2_gecti']} "
          f"bütünlük={ozet['butunluk_gecerli']} motor_kapisi={kapi['gecti']}", flush=True)
    return ozet


def sweep_kos(kart_yolu: pathlib.Path, enjeksiyon_yolu: pathlib.Path,
              dizin: pathlib.Path, smoke: bool) -> int:
    dizin = pathlib.Path(dizin)
    ek = "_smoke" if smoke else ""
    outdir = (dizin / "smoke") if smoke else dizin
    outdir.mkdir(parents=True, exist_ok=True)
    grid_yolu = dizin / f"sonuc_grid{ek}.json"

    ko = kart_oku(kart_yolu)
    modul = enjeksiyon_modulu_yukle(enjeksiyon_yolu)   # eksik arayüz → BAŞLAMADAN durur
    kunye_kaynagi = "kart" if ko["kunye_yolu"] else (
        "enjeksiyon_modulu" if getattr(modul, "KUNYE_YOLU", None) else None)
    kunye_yolu = ko["kunye_yolu"] or getattr(modul, "KUNYE_YOLU", None)

    rapor: dict = {
        "kart": ko["kart_id"], "smoke": smoke,
        "iskelet": "ops/replay_sweep.py (WP3-B; dört emsalin ortaklaştırılması — sınır beyanı "
                   "docstring'de)",
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "kart_okuma": {**ko, "kunye_kaynagi": kunye_kaynagi},
        "enjeksiyon_modulu": str(enjeksiyon_yolu),
        "k_defteri_beyani": K_DEFTERI_BEYANI,
        "hukum_yok": HUKUM_YOK_BEYANI,
    }

    def yaz() -> int:
        rapor["motor_sha256_sonra"] = motor_sha()
        # koşum motor kapısına varmadan durduysa 'önce' ölçülmemiştir → None (uydurma yok)
        rapor["motor_sha_ayni_toplam"] = (
            (rapor["motor_sha256_once"] == rapor["motor_sha256_sonra"])
            if "motor_sha256_once" in rapor else None)
        return rapor_yaz(rapor, grid_yolu)

    # [0] kart alanları ölçüldü mü — UYDURMA YASAĞI: eksikle koşulmaz
    if ko["hucreler"] is None:
        rapor["DURDU"] = f"kart okuma: {ko['hucreler_olculemedi_nedeni']} — koşum YAPILMADI"
        return yaz()
    if ko["seed"] is None:
        rapor["DURDU"] = (f"kart okuma: {ko['seed_olculemedi_nedeni']} — bootstrap seed'siz "
                          "koşulamaz, koşum YAPILMADI")
        return yaz()
    if kunye_yolu is None:
        rapor["DURDU"] = (f"künye yolu ölçülemedi (kart: {ko['kunye_olculemedi_nedeni']}; "
                          "modülde KUNYE_YOLU yok) — motor kapısı kurulamaz, koşum YAPILMADI")
        return yaz()
    kunye_yolu = pathlib.Path(kunye_yolu)
    taban_dir = kunye_yolu.parent / ("kosum1_smoke" if smoke else "kosum1")

    # [1] MOTOR-SHA KÜNYE KAPISI (ÖN-UÇUŞ) — tazeleme YOK (Rol-1); iskelet yalnız DURUR
    m0 = motor_sha()
    rapor["motor_sha256_once"] = m0
    kiyas = motor_kunye_kiyas(m0, kunye_yolu)
    rapor["motor_kunye_kapisi"] = kiyas
    if not kiyas["kunyeyle_ayni"]:
        rapor["DURDU"] = ("motor-künye kapısı (ÖN-UÇUŞ): motor sha künyenin kosum1_once "
                          "kaydıyla tutarsız — iskelet KÜNYE TAZELEMEZ (Rol-1 kararı; edg048 "
                          "protokol emsali). Koşum YAPILMADI, K harcanmadı; teşhis Rol-1'e.")
        print("MOTOR-KÜNYE KAPISI DÜŞTÜ — koşum yapılmadı; teşhis Rol-1'e")
        return yaz()

    # [2] run adları + artık taraması (iskelet SİLMEZ — elle kaldırılır)
    runlar = [(None, KONTROL_RUN)] + [(h, run_adi(modul, h)) for h in ko["hucreler"]]
    adlar = [r for _, r in runlar]
    assert len(set(adlar)) == len(adlar), f"run adları tekil değil: {adlar} — DUR"
    artiklar = [a for _, r in runlar for a in artik_bul(dizin, outdir, r, ek)]
    if artiklar:
        rapor["DURDU"] = (f"önceki koşum artığı duruyor: {artiklar} — elle kaldır, yeniden "
                          "başlat (iskelet yıkıcı silme yapmaz)")
        return yaz()

    # [3] sandbox kurulumu + enjeksiyon ön-sınaması
    ref, uyarlama = referans_modul(dizin)
    rapor["uyarlama_beyani"] = uyarlama
    print(f"referans şasi yüklendi · SANDBOX={ref.SANDBOX} · ARMED_BEKLENEN→B1 · "
          f"künye={kunye_yolu.parent.name} ({kunye_kaynagi})", flush=True)
    if hasattr(modul, "on_sinama"):
        on = modul.on_sinama()
        rapor["on_sinama"] = on
        if not on.get("gecti"):
            rapor["DURDU"] = f"enjeksiyon ön-sınaması düştü: {on} — koşum YAPILMADI"
            return yaz()
    else:
        rapor["on_sinama"] = {"olculemedi_nedeni": ("enjeksiyon modülü on_sinama vermiyor "
                                                    "(isteğe bağlı) — sentetik ön-uçuş YOK, "
                                                    "beyanlı")}

    # [4] kontrol hücresi → BAYT-ÖZDEŞLİK kapısı
    hucreler: dict = {}
    rapor["hucreler"] = hucreler
    hucreler[KONTROL_RUN] = hucre_kos(ref, modul, None, KONTROL_RUN, smoke, kunye_yolu, outdir)
    sk = sasi_kapisi(outdir, taban_dir, kunye_yolu, smoke)
    rapor["sasi_kapisi"] = sk
    if not sk["kill1_gecti"]:
        rapor["DURDU"] = ("bayt-özdeşlik kapısı: kontrol hücresi taban defterleriyle bayt-özdeş "
                          "DEĞİL — hücreler koşulmadı; şasi teşhisi Rol-1'e")
        return yaz()
    if not hucreler[KONTROL_RUN]["oz_sinama_kill2_gecti"]:
        rapor["DURDU"] = "öz-sınama (kontrol) düştü — kablo tutmuyor, hücreler koşulmadı"
        return yaz()
    if not hucreler[KONTROL_RUN]["motor_kapisi_gecti"]:
        rapor["DURDU"] = "hücre-sha kapısı (kontrol): motor sha değişti/künyeden saptı — geçersiz"
        return yaz()

    # [5] hücreler — her biri kapılı; düşen kapıda DURUR (sonrakiler koşulmaz)
    for h, run in runlar[1:]:
        ozet = hucre_kos(ref, modul, h, run, smoke, kunye_yolu, outdir)
        hucreler[run] = ozet
        if not ozet["oz_sinama_kill2_gecti"]:
            rapor["DURDU"] = f"öz-sınama ({run}) düştü — hücre geçersiz, sonraki hücre koşulmadı"
            return yaz()
        if not ozet["motor_kapisi_gecti"]:
            rapor["DURDU"] = (f"hücre-sha kapısı ({run}): motor sha koşum içinde değişti ya da "
                              "künyeden saptı — hücre geçersiz, DUR")
            return yaz()

    # [6] Δ+CI — eşlenik ay-kümeli bootstrap (taban = künyeli kosum1 defteri; aylar kontrol
    #     seanslarından — edg048 reçetesi). Duman: kablo sınaması, Δ/CI değerlendirilmez.
    if not smoke:
        taban_defter = json.loads((taban_dir / "islemler_tam_kontrol.json").read_text())
        seanslar = json.loads((outdir / "seanslar_kontrol.json").read_text())
        aylar = sorted({str(r["date"])[:7] for r in seanslar})
        delta = {}
        for h, run in runlar[1:]:
            hd = json.loads((outdir / f"islemler_tam_{run}.json").read_text())
            delta[run] = delta_pnl_ci(taban_defter, hd, aylar, ko["seed"])
            print(f"  Δ[{run}]: {delta[run]['delta_pnl']} CI95={delta[run]['ci95']} "
                  f"({delta[run]['sifir_disinda']})")
        rapor["delta_ci"] = delta
        rapor["taban_kaynagi"] = (f"{taban_dir / 'islemler_tam_kontrol.json'} "
                                  "(DONMUŞ; bayt-özdeşlik kapısından)")
    else:
        rapor["delta_ci"] = {"degerlendirilmedi": "duman — kablo sınaması; Δ/CI yalnız TAM koşumda"}

    return yaz()


# ---------------------------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="replay-sweep iskeleti (WP3-B) — HÜKÜM VERMEZ")
    p.add_argument("--kart", help="ön-kayıt kartı YAML yolu (research/cards/...)")
    p.add_argument("--enjeksiyon", help="kart-özgü enjeksiyon modülü (.py)")
    p.add_argument("--dizin", help="ölçüm dizini (research/olcumler/<ad>)")
    p.add_argument("--smoke", action="store_true", help="dar pencere kablo sınaması")
    p.add_argument("--stub", help="örnek enjeksiyon modülü stub'ı üret ve çık")
    a = p.parse_args(argv)
    if a.stub:
        ornek_stub_uret(a.stub)
        return 0
    if not (a.kart and a.enjeksiyon and a.dizin):
        p.error("--kart, --enjeksiyon ve --dizin zorunlu (ya da --stub)")
    return sweep_kos(pathlib.Path(a.kart), pathlib.Path(a.enjeksiyon),
                     pathlib.Path(a.dizin), a.smoke)


if __name__ == "__main__":
    raise SystemExit(main())
