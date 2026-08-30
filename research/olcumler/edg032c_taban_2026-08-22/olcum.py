"""EDG-032c — YENİ DONMUŞ TABAN (B1-sonrası dünya) · taban dondurma koşumu (2026-08-22).

NİÇİN: Operatör B1 kararı (2026-08-22, commit c150902) pullback'i ARMED_SETUPS'tan çıkardı
(strategy.py:1059 → 3'lü yasa); ayrıca broker.py + guard.py aynı gün değişti (21:19).
Eski donmuş taban edg032b (885 işlem, 6'sı setup=pullback) bugünkü motorla YENİDEN
ÜRETİLEMEZ — EDG-2026-045 bunu kill#1'de YAPISAL düşüşle belgeledi
(edg045_stop_slip_2026-08-22/DURDU_kill1_sasi_kapisi.json). Rol-1 kararı: gelecek kartların
(045/046+) kıyas tabanı olacak YENİ taban bugünkü motor + bugünkü yasayla dondurulur.

ŞASİ: edg032b_tamsatir_2026-08-13/olcum.py YENİDEN KURULMADI — importlib ile modül olarak
yüklenir, `SANDBOX`ı BU dizine çevrilir (artefakt koruması YAPISAL: edg032b'nin donmuş
kanıtına tek bayt yazılamaz), `kosum("kontrol", smoke)` yolu OLDUĞU GİBİ çağrılır
(exe006b/edg040/edg045 deseni AYNEN; imza tahmini YOK).

════════ TEK UYARLAMA — BEYANLI: ARMED_BEKLENEN yeniden çivilenir ════════
Şasinin `ARMED_BEKLENEN` sabiti (edg032b/olcum.py:106) ESKİ dünyanın yasasını
('breakout_vcp','pullback','exhaustion_hammer','momentum_burst') kodlar ve olcum.py:386'da
motora karşı assert'lenir — B1 sonrası motorla çöker (edg045 kanıtı). Bu koşumun işi tanım
gereği YENİ dünyayı dondurmak olduğundan, yüklenen modülün BEKLENTİ sabiti bugünkü yasaya
(B1_YASA, aşağıda çivili) çevrilir. MOTORA DOKUNULMAZ (kill-mtime + sha önce/sonra kanıtlı);
motor ARMED_SETUPS'u B1_YASA'dan saparsa koşum BAŞLAMADAN durur. Şasinin diğer HİÇBİR sabiti,
assert'i, parametresi değiştirilmez — HİÇBİR parametre enjeksiyonu YOK (kontrol hücresi =
merkez: slot 20 · size 0.5R · zarf 5R, şaside olduğu gibi). Şasinin ozdeslik() kapısı
(032-cmb kıyası) ÇAĞRILMAZ: o kapı eski dünyanın kimlik kapısıydı; bu koşumun kapısı
DETERMİNİZM ÇİFT KAPISIDIR (aşağıda).

DETERMİNİZM ÇİFT KAPISI (edg032b'nin kendi standardı, yeni dünyaya uygulanır):
TAM koşum İKİ KEZ, her biri TAZE süreçte + BAKİR sandbox'la (state_kontrol her koşum öncesi
silinir — donmuş EDG-022 config kopyalarından yeniden kurulur). İki koşumun işlem defteri
(islemler_tam + islemler slim) ve seanslar dosyaları sha256 BAYT-ÖZDEŞ olmalı. Değilse taban
DONDURULMAZ (exit 2). Ek kanıt: alan_envanteri baytları + sonuc ölçüm blokları derin-eşit.

DİSİPLİN: git KOŞULMAZ · state/ YAZILMAZ (şasi kendi sandbox'ına yönlendirir; bars symlink
SALT-OKUNUR) · test suite KOŞULMAZ · motor dosyalarına/goal.yaml'a DOKUNULMAZ · kartlara/
ROADMAP'e YAZILMAZ · UYDURMA YASAĞI (ölçülemeyen None + neden) · YASA-4 (sessiz-yutma
işaretli) · HÜKÜM YOK: bu betik "B1 iyi/kötü" DEMEZ; fark özeti BETİMLEYİCİDİR (tek
koşumluk fark, etki ölçümü için TASARLANMADI).

KULLANIM (sıra zorunlu; her adım ayrı süreç):
  olcum.py kosum1 [--smoke]   # 1. tam koşum → kosum1/
  olcum.py kosum2 [--smoke]   # 2. tam koşum → kosum2/
  olcum.py determinizm        # çift kapı: sha256 kıyas → determinizm.json (düşerse exit 2)
  olcum.py kunye              # TABAN_KUNYESI.json (yalnız determinizm GEÇTİYSE)
  olcum.py fark               # eski(edg032b) ↔ yeni fark özeti → fark_ozeti_edg032b.json
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import shutil
import sys

BURASI = pathlib.Path(__file__).resolve().parent
REPO = BURASI.parents[2]
EDG032B = REPO / "research" / "olcumler" / "edg032b_tamsatir_2026-08-13"
REFERANS = EDG032B / "olcum.py"
sys.path.insert(0, str(REPO))

# B1 YASASI — bugünkü motor beklentisi (c150902; strategy.py:1059). Koşumlar arasında motor
# bundan saparsa determinizm iddiası anlamsızlaşır → koşum BAŞLAMADAN durur.
B1_YASA = ("breakout_vcp", "exhaustion_hammer", "momentum_burst")

MOTOR_DOSYALAR = ("broker.py", "backtest.py", "strategy.py", "guard.py")
CIKTI_DOSYALAR = ("sonuc_kontrol.json", "seanslar_kontrol.json", "islemler_kontrol.json",
                  "islemler_tam_kontrol.json", "alan_envanteri_kontrol.json")
KAPI_DOSYALAR = ("islemler_tam_kontrol.json", "islemler_kontrol.json", "seanslar_kontrol.json")
SONUC_OLCUM_BLOKLARI = ("performans", "doluluk", "tepe_isi", "betim",
                        "tasnif_tum_seans", "birincil", "ci95_ay_kumeli",
                        "islem", "replay", "hucre")


def _sha(p: pathlib.Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None    # ölçülemedi (dosya yok/okunamadı)


def motor_kunye() -> dict:
    out = {}
    for f in MOTOR_DOSYALAR:
        p = REPO / "meridian" / f
        s = _sha(p)
        try:
            mt = p.stat().st_mtime_ns
        except OSError:
            mt = None
        out[f] = {"sha256": s, "sha256_16": (s[:16] if s else None), "mtime_ns": mt}
    return out


def referans_modul():
    """Referans şasiyi modül olarak yükler; SANDBOX'ı BU dizine çevirir; ARMED_BEKLENEN'i
    B1 yasasına yeniden çiviler (modül başındaki BEYANLI TEK UYARLAMA)."""
    # Şasi KAYNAKTAN derlenir (2026-08-30): argv/SystemExit dansı AYNEN korunur, ama
    # `__pycache__` okunmaz — bayat bytecode on üç ölçümü birden sessizce bozabilirdi.
    # Yerel ithal: `sys.path` kurulumu modül başında yapılıyor. Gerekçe:
    # `ops/sasi_yukleyici.py` başlığı · kapı: tests/test_bayat_bytecode_v334.py §C.
    from ops.sasi_yukleyici import referans_sasi_yukle
    m = referans_sasi_yukle(REFERANS)
    m.SANDBOX = BURASI                # artefakt koruması: edg032b dizinine ASLA yazılmaz
    # ── TEK UYARLAMA: şasinin dünya-beklentisi eski yasadan B1 yasasına ──
    eski_beklenen = tuple(m.ARMED_BEKLENEN)
    m.ARMED_BEKLENEN = B1_YASA
    # motor gerçekten B1 yasasında mı? (sapma varsa koşum BAŞLAMADAN durur)
    from meridian import strategy as _st
    assert tuple(_st.ARMED_SETUPS) == B1_YASA, \
        f"MOTOR B1 YASASINDAN SAPMIŞ: {_st.ARMED_SETUPS} ≠ {B1_YASA} — koşum durdu"
    return m, {"eski_ARMED_BEKLENEN": list(eski_beklenen), "yeni_ARMED_BEKLENEN": list(B1_YASA),
               "motor_ARMED_SETUPS": list(_st.ARMED_SETUPS)}


def kosum(ad: str, smoke: bool) -> int:
    """Tek tam koşum: bakir sandbox → şasinin kontrol yolu AYNEN → çıktılar kosumN/ altına."""
    ek = "_smoke" if smoke else ""
    hedef = BURASI / (ad + ek)
    if hedef.exists():
        sys.exit(f"{hedef} zaten var — üzerine koşulmaz (elle kaldır, yeniden başlat)")

    m_once = motor_kunye()
    t0 = dt.datetime.now(dt.timezone.utc)
    ref, uyarlama = referans_modul()

    # BAKİR SANDBOX: önceki koşumun state'i determinizm iddiasını kirletmesin
    st_ad = "state_kontrol" + ek
    st_dir = BURASI / st_ad
    bakir = True
    if st_dir.exists():
        shutil.rmtree(st_dir)
    # şasi çıktı adları sabit (duman modunda ad '_smoke' eklidir) — eski artık varsa karışmasın
    kaynak_kok = (BURASI / "smoke") if smoke else BURASI
    adlar = [f.replace(".json", ek + ".json") for f in CIKTI_DOSYALAR]
    for fs in adlar:
        if (kaynak_kok / fs).exists():
            sys.exit(f"kök dizinde eski çıktı duruyor: {kaynak_kok / fs} — arşivlenmemiş koşum var, DUR")

    ref.kosum("kontrol", smoke=smoke)      # ŞASİ: referansın kendi yolu, dokunulmadan

    m_sonra = motor_kunye()
    motor_ayni = (m_once == m_sonra)
    t1 = dt.datetime.now(dt.timezone.utc)

    hedef.mkdir()
    tasinan = {}
    for fs in adlar:
        kk = kaynak_kok / fs
        if not kk.exists():
            tasinan[fs] = None             # ölçülemedi: şasi bu dosyayı üretmedi (raporda görünür)
            continue
        shutil.move(str(kk), str(hedef / fs))
        tasinan[fs] = _sha(hedef / fs)
    if any(v is None for v in tasinan.values()):
        print(f"[{ad}{ek}] UYARI: üretilmeyen çıktı var: "
              f"{[k for k, v in tasinan.items() if v is None]} — koşum taban olamaz")

    run_kunye = {
        "ad": ad + ek, "smoke": smoke,
        "baslangic_utc": t0.isoformat(timespec="seconds"),
        "bitis_utc": t1.isoformat(timespec="seconds"),
        "sure_sn": round((t1 - t0).total_seconds(), 1),
        "sasi": {"yol": str(REFERANS), "sha256": _sha(REFERANS)},
        "uyarlama_beyani": {**uyarlama,
                            "beyan": ("TEK uyarlama: yüklenen şasi modülünün ARMED_BEKLENEN "
                                      "sabiti B1 yasasına çevrildi (dünya-beklentisi; motor "
                                      "DEĞİL). Başka hiçbir sabit/assert/parametre değişmedi; "
                                      "parametre enjeksiyonu YOK (merkez hücre olduğu gibi).")},
        "motor_sha_once": m_once, "motor_sha_sonra": m_sonra,
        "motor_ayni_kosum_icinde": motor_ayni,
        "sandbox": {"state_dizini": st_ad, "bakir_baslatildi": bakir,
                    "beyan": "koşum öncesi silindi; şasi hazirla() donmuş EDG-022 kopyalarından yeniden kurdu"},
        "tasinan_dosyalar_sha256": tasinan,
    }
    (hedef / "run_kunye.json").write_text(
        json.dumps(run_kunye, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[{ad}{ek}] bitti · süre={run_kunye['sure_sn']}s · motor_ayni={motor_ayni} "
          f"→ {hedef}")
    if not motor_ayni:
        print(f"[{ad}{ek}] UYARI: motor sha koşum İÇİNDE değişti — bu koşum taban olamaz")
        return 2
    return 0


def determinizm(smoke: bool = False) -> int:
    ek = "_smoke" if smoke else ""
    k1, k2 = BURASI / f"kosum1{ek}", BURASI / f"kosum2{ek}"
    for d in (k1, k2):
        if not d.exists():
            sys.exit(f"determinizm: koşum dizini yok: {d}")

    kapi = {}
    for f in KAPI_DOSYALAR:
        fs = f.replace(".json", ek + ".json")
        s1, s2 = _sha(k1 / fs), _sha(k2 / fs)
        kapi[f] = {"kosum1_sha256": s1, "kosum2_sha256": s2,
                   "bayt_ozdes": (s1 is not None and s1 == s2)}
    kapi_gecti = all(v["bayt_ozdes"] for v in kapi.values())

    # ek kanıt 1: alan envanteri baytları
    ae_ad = "alan_envanteri_kontrol" + ek + ".json"
    ae1, ae2 = _sha(k1 / ae_ad), _sha(k2 / ae_ad)
    # ek kanıt 2: sonuc ölçüm blokları derin-eşit (sonuc'un kendisi bayt-özdeş OLAMAZ:
    # olcum_zamani/sure_sn/mtime koşum kimliğidir — edg032b beyanı AYNEN)
    s1 = json.loads((k1 / ("sonuc_kontrol" + ek + ".json")).read_text())
    s2 = json.loads((k2 / ("sonuc_kontrol" + ek + ".json")).read_text())
    blok = {}
    blok_fark = {}
    for b in SONUC_OLCUM_BLOKLARI:
        blok[b] = (s1.get(b) == s2.get(b))
        if not blok[b]:
            blok_fark[b] = {"kosum1": s1.get(b), "kosum2": s2.get(b)}
    bloklar_esit = all(blok.values())

    # koşumlar ARASI motor sürüklenmesi (koşum-içi zaten run_kunye'de)
    rk1 = json.loads((k1 / "run_kunye.json").read_text())
    rk2 = json.loads((k2 / "run_kunye.json").read_text())
    motor_arasi_ayni = (rk1["motor_sha_sonra"] == rk2["motor_sha_once"] ==
                        rk1["motor_sha_once"] == rk2["motor_sha_sonra"])

    gecti = bool(kapi_gecti and bloklar_esit and motor_arasi_ayni
                 and rk1["motor_ayni_kosum_icinde"] and rk2["motor_ayni_kosum_icinde"])
    out = {
        "adim": f"EDG-032c DETERMİNİZM ÇİFT KAPISI{ek}",
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "tanim": ("TAM koşum iki kez, taze süreç + bakir sandbox; işlem defteri (tam+slim) ve "
                  "seanslar sha256 BAYT-ÖZDEŞ olmalı. Ek kanıt: alan_envanteri baytları + "
                  "sonuc ölçüm blokları derin-eşit + motor sha dört noktada sabit."),
        "kapi_dosyalari": kapi, "kapi_bayt_ozdes": kapi_gecti,
        "ek_kanit_alan_envanteri": {"kosum1_sha256": ae1, "kosum2_sha256": ae2,
                                    "bayt_ozdes": (ae1 is not None and ae1 == ae2)},
        "ek_kanit_sonuc_bloklari_esit": blok,
        "sonuc_blok_fark": blok_fark or None,
        "motor_dort_noktada_sabit": motor_arasi_ayni,
        "kosum_icinde_motor_ayni": {"kosum1": rk1["motor_ayni_kosum_icinde"],
                                    "kosum2": rk2["motor_ayni_kosum_icinde"]},
        "DETERMINIZM_GECTI": gecti,
        "hukum": None,   # hüküm Rol-1'in; bu bayrak mekanik sha kıyasıdır
    }
    (BURASI / f"determinizm{ek}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"DETERMİNİZM{ek}: kapı(bayt)={kapi_gecti} bloklar={bloklar_esit} "
          f"motor_sabit={motor_arasi_ayni} → {'GEÇTİ' if gecti else 'DÜŞTÜ — taban DONDURULMAZ'}")
    print(f"yazıldı: {BURASI / f'determinizm{ek}.json'}")
    return 0 if gecti else 2


def kunye() -> int:
    det = json.loads((BURASI / "determinizm.json").read_text())
    if not det["DETERMINIZM_GECTI"]:
        sys.exit("kunye: determinizm kapısı GEÇMEDİ — künye yazılmaz, taban dondurulmaz")
    k1 = BURASI / "kosum1"
    rk1 = json.loads((k1 / "run_kunye.json").read_text())
    rk2 = json.loads((BURASI / "kosum2" / "run_kunye.json").read_text())
    sonuc = json.loads((k1 / "sonuc_kontrol.json").read_text())
    defter = json.loads((k1 / "islemler_tam_kontrol.json").read_text())
    setup_n: dict[str, int] = {}
    for t in defter:
        setup_n[t.get("setup") or "?"] = setup_n.get(t.get("setup") or "?", 0) + 1

    st_yollar = {
        "sandbox_kaynagi_edg022": {f: _sha(REPO / "research/olcumler/edg022_evren_kisit_2026-08-09/state" / f)
                                   for f in ("goal.yaml", "strategy.yaml", "bounds.yaml")},
        "repo_state_bugun": {f: _sha(REPO / "state" / f) for f in ("goal.yaml", "bounds.yaml")},
    }
    out = {
        "taban": "edg032c — B1-sonrası dünya DONMUŞ TABANI",
        "dondurma_tarihi_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "neden": ("Operatör B1 kararı (2026-08-22, c150902) pullback'i ARMED_SETUPS'tan çıkardı; "
                  "broker.py+guard.py de aynı gün değişti (21:19). Eski taban edg032b bugünkü "
                  "motorla yeniden üretilemez (EDG-2026-045 kill#1 YAPISAL düşüş kaydı). "
                  "Rol-1 kararı: gelecek kartlar (045/046+) BU tabana kıyaslanır."),
        "kanonik_taban_dosyalari": {
            "islemler_tam": str(k1 / "islemler_tam_kontrol.json"),
            "islemler_slim": str(k1 / "islemler_kontrol.json"),
            "seanslar": str(k1 / "seanslar_kontrol.json"),
            "sonuc": str(k1 / "sonuc_kontrol.json"),
            "not": "kosum2/ aynı dosyaların bayt-özdeş ikinci üretimi (determinizm tanığı)",
        },
        "determinizm_kaniti": {
            "dosya": str(BURASI / "determinizm.json"),
            "kapi_sha256": {f: det["kapi_dosyalari"][f]["kosum1_sha256"] for f in KAPI_DOSYALAR},
            "gecti": det["DETERMINIZM_GECTI"],
        },
        "motor_sha256": {
            "kosum1_once": rk1["motor_sha_once"], "kosum2_sonra": rk2["motor_sha_sonra"],
            "dort_noktada_sabit": det["motor_dort_noktada_sabit"],
        },
        "sasi": {"yol": str(REFERANS), "sha256": rk1["sasi"]["sha256"],
                 "uyarlama": rk1["uyarlama_beyani"]},
        "yasa": {"ARMED_SETUPS": list(B1_YASA),
                 "kaynak": "meridian/strategy.py:1059 (B1, c150902)"},
        "config_sha256": {**st_yollar,
                          "sasi_kaydi_sha16": sonuc.get("config_sha256_16"),
                          "not": ("koşum EDG-022 DONMUŞ kopyalarıyla koşar (şasi hazirla()); "
                                  "repo state/goal+bounds bugünkü İZLİ değerler bağlam içindir, "
                                  "koşumda OKUNMAZ")},
        "pencere": {"start": sonuc["replay"]["start"], "end": sonuc["replay"]["end"],
                    "strategy_version": sonuc["replay"]["strategy_version"]},
        "evren": {"n_sembol": sonuc["replay"]["n_sembol"],
                  "n_endeks_satir": sonuc["replay"]["n_endeks_satir"],
                  "not": ("n_endeks_satir koşum-günü önbellek uzunluğudur, pencereye kırpılmaz "
                          "(edg040 daraltılmış-istisna dersi)")},
        "hucre": sonuc.get("hucre"),
        "cost_model": (sonuc.get("replay") or {}).get("cost_model"),
        "butunluk_gecerli": (sonuc.get("butunluk") or {}).get("gecerli"),
        "taban_ozeti_betimleyici": {
            "islem_n": len(defter), "setup_dagilimi": dict(sorted(setup_n.items())),
            "net_pnl_trades": sonuc["performans"]["net_pnl_trades"],
            "net_pnl_equity": sonuc["performans"]["net_pnl_equity"],
            "maxdd_kanonik": sonuc["performans"]["maxdd_kanonik"],
            "sharpe": sonuc["performans"]["sharpe"],
            "avg_r": sonuc["performans"]["avg_r"],
            "win_rate": sonuc["performans"]["win_rate"],
        },
        "hukum_yok": ("Bu künye HÜKÜM İÇERMEZ; taban kimliği + determinizm kanıtıdır. "
                      "B1'in etkisine dair çıkarım bu koşumun işi DEĞİLDİR."),
    }
    (BURASI / "TABAN_KUNYESI.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"yazıldı: {BURASI / 'TABAN_KUNYESI.json'} · n={len(defter)} "
          f"net={out['taban_ozeti_betimleyici']['net_pnl_trades']}")
    return 0


def fark() -> int:
    """ESKİ (edg032b donmuş) ↔ YENİ (edg032c kosum1) BETİMLEYİCİ fark özeti. HÜKÜM YOK."""
    det = json.loads((BURASI / "determinizm.json").read_text())
    if not det["DETERMINIZM_GECTI"]:
        sys.exit("fark: determinizm kapısı GEÇMEDİ — fark özeti donmamış deftere yazılmaz")
    eski = json.loads((EDG032B / "islemler_tam_kontrol.json").read_text())
    yeni = json.loads((BURASI / "kosum1" / "islemler_tam_kontrol.json").read_text())
    es = json.loads((EDG032B / "sonuc_kontrol.json").read_text())
    ys = json.loads((BURASI / "kosum1" / "sonuc_kontrol.json").read_text())

    def _setup_n(defter):
        c: dict[str, int] = {}
        for t in defter:
            c[t.get("setup") or "?"] = c.get(t.get("setup") or "?", 0) + 1
        return dict(sorted(c.items()))

    def _exit_n(defter):
        c: dict[str, int] = {}
        for t in defter:
            c[str(t.get("exit_reason"))] = c.get(str(t.get("exit_reason")), 0) + 1
        return dict(sorted(c.items(), key=lambda kv: -kv[1]))

    def _pnl(defter):
        return round(sum(float(t.get("pnl_dollars") or 0.0) for t in defter), 2)

    def _yillik_pnl(defter):
        c: dict[str, float] = {}
        for t in defter:
            y = str(t["ts_open"])[:4]
            c[y] = c.get(y, 0.0) + float(t.get("pnl_dollars") or 0.0)
        return {y: round(v, 2) for y, v in sorted(c.items())}

    # eşleme anahtarı: (ticker, ts_open) — çakışmalar sıra içinde eşlenir, sayısı raporlanır
    def _anahtarla(defter):
        d: dict[tuple, list] = {}
        for t in defter:
            d.setdefault((t["ticker"], str(t["ts_open"])), []).append(t)
        return d

    ae, ay = _anahtarla(eski), _anahtarla(yeni)
    cok_anahtar = {"eski": sum(1 for v in ae.values() if len(v) > 1),
                   "yeni": sum(1 for v in ay.values() if len(v) > 1)}
    ortak_ayni, ortak_farkli = 0, 0
    farkli_alan_n: dict[str, int] = {}
    yalniz_eski, yalniz_yeni = [], []
    for k in set(ae) | set(ay):
        le, ly = ae.get(k, []), ay.get(k, [])
        n_ortak = min(len(le), len(ly))
        for i in range(n_ortak):
            if le[i] == ly[i]:
                ortak_ayni += 1
            else:
                ortak_farkli += 1
                for alan in set(le[i]) | set(ly[i]):
                    if le[i].get(alan) != ly[i].get(alan):
                        farkli_alan_n[alan] = farkli_alan_n.get(alan, 0) + 1
        yalniz_eski.extend(le[n_ortak:])
        yalniz_yeni.extend(ly[n_ortak:])

    # ilk ayrışma: defterler kapanış-sırasıyla yazılır; baştan ilk eşit-olmayan satır
    ilk_ayrisma = None
    for i in range(min(len(eski), len(yeni))):
        if eski[i] != yeni[i]:
            ilk_ayrisma = {
                "indeks": i,
                "eski": {k: eski[i].get(k) for k in ("ticker", "ts_open", "ts_close", "setup",
                                                     "exit_reason", "pnl_dollars")},
                "yeni": {k: yeni[i].get(k) for k in ("ticker", "ts_open", "ts_close", "setup",
                                                     "exit_reason", "pnl_dollars")},
            }
            break

    # seans-düzeyi doluluk farkı (slot/ısı doldurma etkisinin seans izdüşümü)
    se = json.loads((EDG032B / "seanslar_kontrol.json").read_text())
    sy_ = json.loads((BURASI / "kosum1" / "seanslar_kontrol.json").read_text())
    se_d = {r["date"]: r for r in se}
    sy_d = {r["date"]: r for r in sy_}
    ortak_gun = sorted(set(se_d) & set(sy_d))
    n_acik_farkli = [d for d in ortak_gun if se_d[d]["n_acik"] != sy_d[d]["n_acik"]]
    max_fark = max((abs(se_d[d]["n_acik"] - sy_d[d]["n_acik"]) for d in n_acik_farkli), default=0)

    ep, yp = es["performans"], ys["performans"]
    out = {
        "adim": "EDG-032c ESKİ↔YENİ FARK ÖZETİ (BETİMLEYİCİ — hüküm yok)",
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "beyan": ("Tek koşumluk fark betimleyicidir; 'B1 iyi/kötü etki etti' çıkarımı bu "
                  "koşumun işi DEĞİLDİR ve bu dosyadan yapılamaz (CI yok, tasarım yok)."),
        "n": {"eski_edg032b": len(eski), "yeni_edg032c": len(yeni),
              "fark": len(yeni) - len(eski)},
        "setup_dagilimi": {"eski": _setup_n(eski), "yeni": _setup_n(yeni)},
        "pullback": {"eski_n": _setup_n(eski).get("pullback", 0),
                     "yeni_n": _setup_n(yeni).get("pullback", 0),
                     "eski_pullback_pnl": _pnl([t for t in eski if t.get("setup") == "pullback"])},
        "net_pnl_trades": {"eski": ep["net_pnl_trades"], "yeni": yp["net_pnl_trades"],
                           "fark": round(yp["net_pnl_trades"] - ep["net_pnl_trades"], 2)},
        "performans_kiyas": {k: {"eski": ep.get(k), "yeni": yp.get(k)}
                             for k in ("net_pnl_equity", "maxdd_kanonik", "maxdd_m2m", "sharpe",
                                       "avg_r", "win_rate", "total_return", "score")},
        "exit_reason": {"eski": _exit_n(eski), "yeni": _exit_n(yeni)},
        "yillik_pnl": {"eski": _yillik_pnl(eski), "yeni": _yillik_pnl(yeni)},
        "islem_eslemesi": {
            "anahtar": "(ticker, ts_open); çok-satırlı anahtarlar sıra içinde eşlendi",
            "cok_satirli_anahtar_n": cok_anahtar,
            "ortak_ayni_satir_n": ortak_ayni,
            "ortak_farkli_satir_n": ortak_farkli,
            "farkli_alan_frekansi": dict(sorted(farkli_alan_n.items(), key=lambda kv: -kv[1])),
            "yalniz_eskide_n": len(yalniz_eski),
            "yalniz_eskide_setup": _setup_n(yalniz_eski),
            "yalniz_eskide_pnl": _pnl(yalniz_eski),
            "yalniz_yenide_n": len(yalniz_yeni),
            "yalniz_yenide_setup": _setup_n(yalniz_yeni),
            "yalniz_yenide_pnl": _pnl(yalniz_yeni),
        },
        "doldurma_etkisi_seans_izdusumu": {
            "tanim": ("pullback'in boşalttığı slot/ısıyı başka işlemlerin doldurup doldurmadığının "
                      "seans izdüşümü: aynı günün n_acik (açık pozisyon) kıyası + doluluk blokları"),
            "ortak_gun_n": len(ortak_gun),
            "n_acik_farkli_gun_n": len(n_acik_farkli),
            "n_acik_max_mutlak_fark": max_fark,
            "n_acik_farkli_ilk10": n_acik_farkli[:10],
            "doluluk": {"eski": es.get("doluluk"), "yeni": ys.get("doluluk")},
            "eszamanli_poz_max": {"eski": (es.get("tepe_isi") or {}).get("eszamanli_poz_max"),
                                  "yeni": (ys.get("tepe_isi") or {}).get("eszamanli_poz_max")},
        },
        "ilk_ayrisma": ilk_ayrisma,
    }
    (BURASI / "fark_ozeti_edg032b.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"FARK: n {len(eski)}→{len(yeni)} · pullback {out['pullback']['eski_n']}→"
          f"{out['pullback']['yeni_n']} · net {ep['net_pnl_trades']}→{yp['net_pnl_trades']} "
          f"(Δ{out['net_pnl_trades']['fark']}) · yalnız-eski={len(yalniz_eski)} "
          f"yalnız-yeni={len(yalniz_yeni)} · ortak-farklı={ortak_farkli}")
    print(f"yazıldı: {BURASI / 'fark_ozeti_edg032b.json'}")
    return 0


if __name__ == "__main__":
    mod = sys.argv[1] if len(sys.argv) > 1 else ""
    smoke = "--smoke" in sys.argv
    if mod in ("kosum1", "kosum2"):
        raise SystemExit(kosum(mod, smoke))
    elif mod == "determinizm":
        raise SystemExit(determinizm(smoke))
    elif mod == "kunye":
        raise SystemExit(kunye())
    elif mod == "fark":
        raise SystemExit(fark())
    else:
        sys.exit("kullanım: olcum.py {kosum1|kosum2|determinizm|kunye|fark} [--smoke]")
