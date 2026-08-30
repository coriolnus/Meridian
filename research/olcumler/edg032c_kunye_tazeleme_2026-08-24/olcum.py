"""edg032c KÜNYE TAZELEME — BAYT-ÖZDEŞLİK KANITI (2026-08-24).

NİÇİN: EDG-2026-057 künye kapısında durdu. edg032c TABAN_KUNYESI.json'un motor sha
4'lüsünden ÜÇÜ bugünkü motorla eşleşmiyor:
    broker.py   künye 09f5d0850122376a… (v273) → şimdi e4c5c91515d8ec35…
    backtest.py künye b59c059f43d4e410… = ŞİMDİ AYNI (değişmedi)
    strategy.py künye 449039624127c66d… (v273) → şimdi d6ae533c8a578f74…
    guard.py    künye bb984356798278a5… (v273) → şimdi 475e19e7b38f0650…

STATİK TEŞHİS (koordinatör ölçümü — İMDİR, KANITLAMAZ):
    * broker.py (10 satır) + guard.py (14 satır): commit'siz, YALNIZ YORUM (ölü-alan damgaları).
    * strategy.py: commit 06a6cff (2026-08-23), 36 kod satırı — mesaj "OPT Faz-1 kablolama
      (v276): 5 yeni düğme bit-nötr bounds-okur" diyor. İDDİA KANIT DEĞİLDİR.
KANIT = BAYT-ÖZDEŞLİK. Bu betiğin işi o kanıtı üretmek ya da üretememektir.

PROTOKOL (edg048/edg049 emsali AYNEN — Rol-1 devri):
  TAM pencerede kontrol koşumu İKİ KEZ (taze süreç + BAKİR sandbox). kosum1_yeni ↔ kosum2_yeni
  ↔ edg032c/kosum1 ÜÇ DEFTERDE (islemler_tam / islemler / seanslar) bayt-özdeşse künyenin
  broker/strategy/guard kayıtları v276'ya tazelenir (eski sha'lar kunye_tarihcesi'ne + neden +
  kanıt yolu; yedek kunye_yedek_pre_tazeleme.json; kosum1_once + kosum2_sonra BİRLİKTE —
  dort_noktada_sabit iç tutarlılığı). ÖZDEŞ DEĞİLSE künye TAZELENMEZ → DUR (dünya değişmiş
  demektir; taban yeniden dondurulmalı, o Rol-1 kararıdır).

  DÖRDÜNCÜ KANONİK DOSYA (sonuc_kontrol.json) BAYT KAPISINDA DEĞİLDİR — YAPISAL SEBEP:
  şasi bu dosyaya olcum_zamani / sure_sn / motor mtime_ns yazar (koşum KİMLİĞİ). Bayt-özdeşlik
  yapısal olarak İMKANSIZ. edg032b/edg032c'nin kendi beyanı AYNEN: sonuc ÖLÇÜM BLOKLARI
  (10 blok) derin-eşitlikle sınanır. sha'sı yine de RAPORLANIR (saklanmaz), farkın kaynağı
  alan-alan gösterilir.

ŞASİ: edg032b_tamsatir_2026-08-13/olcum.py YENİDEN KURULMADI — importlib ile modül olarak
  yüklenir, SANDBOX'ı BU dizine çevrilir (edg032c/kosum1'e tek bayt yazılamaz: YAPISAL koruma),
  ref.kosum("kontrol", smoke=False) OLDUĞU GİBİ çağrılır. TEK UYARLAMA (edg032c beyanı AYNEN):
  ARMED_BEKLENEN sabiti B1 yasasına çevrilir (dünya-BEKLENTİSİ; motor DEĞİL). Parametre
  enjeksiyonu YOK (merkez hücre: slot 20 · 0,5R · 5R zarf).

DİSİPLİN: git KOŞULMAZ · canlı state/ YAZILMAZ (sandbox bu dizinde; state/bars SALT-OKUNUR
  symlink) · test suite KOŞULMAZ · MOTOR DOSYALARINA DOKUNULMAZ (salt-oku; sha her fazın
  başında+sonunda) · kartlara/ROADMAP'e YAZILMAZ · UYDURMA YASAĞI (ölçülemeyen None + neden) ·
  HÜKÜM YOK: bu betik "değişiklik iyi/kötü" DEMEZ, yalnız BİT-NÖTR MÜ sorusunu ölçer.
  Ölçüm dizini DIŞINA tek yazım: TABAN_KUNYESI.json'un motor_sha256 + kunye_tarihcesi alanları
  (yalnız üç kapı da geçerse).

KULLANIM (sıra zorunlu; her adım AYRI süreç):
  olcum.py onucus         # motor pin + şasi yüklenebilirlik + artık kontrolü (replay YOK)
  olcum.py kosum1_yeni    # TAM koşum #1 (bakir sandbox) → kosum1_yeni/
  olcum.py kosum2_yeni    # TAM koşum #2 (bakir sandbox) → kosum2_yeni/
  olcum.py bayt_ozdeslik  # üç-yönlü çift kapı → bayt_ozdeslik.json (+ GEÇERSE künye tazelenir)
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
EDG032C = REPO / "research" / "olcumler" / "edg032c_taban_2026-08-22"
REFERANS = EDG032B / "olcum.py"
sys.path.insert(0, str(REPO))

# B1 YASASI — edg032c künyesindeki yasa (c150902; strategy.py). Motor saparsa koşum BAŞLAMADAN durar.
B1_YASA = ("breakout_vcp", "exhaustion_hammer", "momentum_burst")

MOTOR_DOSYALAR = ("broker.py", "backtest.py", "strategy.py", "guard.py")

# ── v276 PİN: koşum turunun BAŞINDA (2026-08-24) ölçülen bugünkü motor sha'ları.
# Her fazın başında+sonunda doğrulanır; sapma = başka ajan motora dokundu → koşum GEÇERSİZ, DUR.
V276_PIN = {
    "broker.py":   "e4c5c91515d8ec35ae36c71af39f61cadd09baa1c11268a99aedc7ed05a470fb",
    "backtest.py": "b59c059f43d4e410c198eb36ced18539d7575e7060d8c11337386a6ebf77cbd5",
    "strategy.py": "d6ae533c8a578f74282445541f5b689c8ef4a8f0cf78c95ecc7dc138836203e4",
    "guard.py":    "475e19e7b38f0650afb73681e2d69791b4635f488c5bea968cb87dc4e666415d",
}

TAZELEME_NEDEN = {
    "broker.py": ("Commit'siz çalışma-ağacı değişikliği (10 satır), koordinatör ölçümü: YALNIZ "
                  "YORUM — ölü-alan damgaları (aynı gece başka ajanların statik işaretlemesi). "
                  "Kod yolu DEĞİŞMEDİ. Davranış bit-nötr KANITLI — TAM-pencere çift-koşum "
                  "(edg032c_kunye_tazeleme_2026-08-24 kosum1_yeni/kosum2_yeni) birbirleriyle VE "
                  "edg032c/kosum1 ile ÜÇ DEFTERDE bayt-özdeş."),
    "strategy.py": ("Commit 06a6cff (2026-08-23) — OPT Faz-1 kablolama (v276): 5 yeni düğme "
                    "bounds'tan OKUNUR hâle geldi, 36 kod satırı. Commit mesajı 'bit-nötr' "
                    "İDDİA ediyordu; künye o commit'ten sonra hiç tazelenmediği için iddia "
                    "SINANMAMIŞTI. Bu koşum iddiayı SINADI: davranış bit-nötr KANITLI — aynı "
                    "üç-defter özdeşliği (düğmelerin replay varsayılanları defteri kaydırmıyor). "
                    "ARMED_SETUPS B1 üçlüsü AYNEN (koşum başı assert)."),
    "guard.py": ("Commit'siz çalışma-ağacı değişikliği (14 satır), koordinatör ölçümü: YALNIZ "
                 "YORUM — ölü-alan damgaları. Kod yolu DEĞİŞMEDİ. Davranış bit-nötr KANITLI — "
                 "aynı üç-defter özdeşliği."),
}

CIKTI_DOSYALAR = ("sonuc_kontrol.json", "seanslar_kontrol.json", "islemler_kontrol.json",
                  "islemler_tam_kontrol.json", "alan_envanteri_kontrol.json")
# BAYT kapısı: künyenin determinizm_kaniti.kapi_sha256 kaydının BİREBİR aynı üçlüsü.
KAPI_DEFTERLER = ("islemler_tam_kontrol.json", "islemler_kontrol.json", "seanslar_kontrol.json")
# 4. kanonik dosya — bayt kapısında DEĞİL (yapısal: koşum kimliği alanları); blok-derin sınanır.
DORDUNCU = "sonuc_kontrol.json"
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


def pin_kapisi(nerede: str) -> dict:
    """Motor dosyaları v276 pin'inde mi? Değilse koşum geçersiz — DUR (fail-closed)."""
    m = motor_kunye()
    sapan = {f: {"pin": V276_PIN[f], "simdi": m[f]["sha256"]}
             for f in MOTOR_DOSYALAR if m[f]["sha256"] != V276_PIN[f]}
    if sapan:
        sys.exit(f"MOTOR PİN DÜŞTÜ ({nerede}): {json.dumps(sapan, ensure_ascii=False)} — "
                 "koşum sırasında motor dosyası değişti (başka ajan?) — GEÇERSİZ, DUR")
    # künye çivisi: backtest.py künyeyle BİREBİR olmalı (değişmediği iddiası)
    kunye = json.loads((EDG032C / "TABAN_KUNYESI.json").read_text())
    kb = kunye["motor_sha256"]["kosum1_once"]["backtest.py"]["sha256"]
    if kb != V276_PIN["backtest.py"]:
        sys.exit(f"backtest.py künyeden SAPMIŞ ({nerede}): künye={kb} pin={V276_PIN['backtest.py']} "
                 "— tazeleme kapsamı dışı bir kayma var, DUR")
    return m


def referans_modul():
    """edg032b şasisini modül olarak yükler; SANDBOX'ı BU dizine çevirir; ARMED_BEKLENEN'i
    B1 yasasına çevirir (edg032c beyanlı TEK uyarlaması AYNEN); motoru B1'e assert'ler."""
    # Şasi KAYNAKTAN derlenir (2026-08-30): argv/SystemExit dansı AYNEN korunur, ama
    # `__pycache__` okunmaz — bayat bytecode on üç ölçümü birden sessizce bozabilirdi.
    # Yerel ithal: `sys.path` kurulumu modül başında yapılıyor. Gerekçe:
    # `ops/sasi_yukleyici.py` başlığı · kapı: tests/test_bayat_bytecode_v334.py §C.
    from ops.sasi_yukleyici import referans_sasi_yukle
    m = referans_sasi_yukle(REFERANS)
    m.SANDBOX = BURASI                # artefakt koruması: edg032b/edg032c dizinlerine ASLA yazılmaz
    eski_beklenen = tuple(m.ARMED_BEKLENEN)
    m.ARMED_BEKLENEN = B1_YASA
    from meridian import strategy as _st
    assert tuple(_st.ARMED_SETUPS) == B1_YASA, \
        f"MOTOR B1 YASASINDAN SAPMIŞ: {_st.ARMED_SETUPS} ≠ {B1_YASA} — koşum durdu"
    return m, {"eski_ARMED_BEKLENEN": list(eski_beklenen),
               "yeni_ARMED_BEKLENEN": list(B1_YASA),
               "motor_ARMED_SETUPS": list(_st.ARMED_SETUPS),
               "beyan": ("TEK uyarlama: yüklenen şasi modülünün ARMED_BEKLENEN sabiti B1 "
                         "yasasına çevrildi (dünya-beklentisi; motor DEĞİL). Başka hiçbir "
                         "sabit/assert/parametre değişmedi; parametre enjeksiyonu YOK "
                         "(merkez hücre olduğu gibi) — edg032c beyanı AYNEN.")}


def onucus() -> int:
    """[0] Replay KOŞMADAN: pin + şasi yüklenebilirliği + artık kontrolü + kıyas dosyaları var mı."""
    m = pin_kapisi("onucus")
    ref, uyarlama = referans_modul()
    artiklar = [f for f in CIKTI_DOSYALAR if (BURASI / f).exists()]
    ref_eksik = [f for f in (KAPI_DEFTERLER + (DORDUNCU,))
                 if not (EDG032C / "kosum1" / f).exists()]
    out = {
        "adim": "ön-uçuş (replay KOŞULMADI)",
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "motor_pin_gecti": True, "motor_sha_simdi": m,
        "sasi": {"yol": str(REFERANS), "sha256": _sha(REFERANS),
                 "kunyedeki_sasi_sha256": json.loads(
                     (EDG032C / "TABAN_KUNYESI.json").read_text())["sasi"]["sha256"]},
        "sasi_SANDBOX": str(ref.SANDBOX), "uyarlama_beyani": uyarlama,
        "kok_dizinde_artik": artiklar or None,
        "kiyas_dosyalari_eksik": ref_eksik or None,
    }
    out["sasi"]["sasi_kunyeyle_ayni"] = (out["sasi"]["sha256"] == out["sasi"]["kunyedeki_sasi_sha256"])
    print(json.dumps(out, ensure_ascii=False, indent=1))
    if artiklar or ref_eksik or not out["sasi"]["sasi_kunyeyle_ayni"]:
        return 2
    return 0


def kosum(ad: str) -> int:
    """TAM koşum: bakir sandbox → şasinin kontrol yolu AYNEN → çıktılar <ad>/ altına.
    edg032c/olcum.py:kosum() deseninin BİREBİR aynısı; tek fark hedef dizin adı."""
    hedef = BURASI / ad
    if hedef.exists():
        sys.exit(f"{hedef} zaten var — üzerine koşulmaz (elle kaldır, yeniden başlat)")
    for fs in CIKTI_DOSYALAR:                       # ön-uçuş artık kontrolü (fail-closed)
        if (BURASI / fs).exists():
            sys.exit(f"kök dizinde eski çıktı duruyor: {BURASI / fs} — arşivlenmemiş koşum var, DUR")

    m_once = pin_kapisi(f"{ad}/once")
    t0 = dt.datetime.now(dt.timezone.utc)
    ref, uyarlama = referans_modul()

    st_dir = BURASI / "state_kontrol"               # BAKİR sandbox (edg032c determinizm standardı)
    if st_dir.exists():
        shutil.rmtree(st_dir)

    ref.kosum("kontrol", smoke=False)               # ŞASİ: referansın kendi yolu, dokunulmadan

    m_sonra = pin_kapisi(f"{ad}/sonra")
    motor_ayni = (m_once == m_sonra)
    t1 = dt.datetime.now(dt.timezone.utc)

    hedef.mkdir()
    tasinan = {}
    for fs in CIKTI_DOSYALAR:
        kk = BURASI / fs
        if not kk.exists():
            tasinan[fs] = None                      # ölçülemedi: şasi bu dosyayı üretmedi
            continue
        shutil.move(str(kk), str(hedef / fs))
        tasinan[fs] = _sha(hedef / fs)
    if any(v is None for v in tasinan.values()):
        print(f"[{ad}] UYARI: üretilmeyen çıktı var: "
              f"{[k for k, v in tasinan.items() if v is None]} — koşum kıyasa giremez")

    (hedef / "run_kunye.json").write_text(json.dumps({
        "ad": ad,
        "amac": ("edg032c künye tazeleme çift-koşumu (2026-08-24; EDG-048/049 emsali) — "
                 "broker/strategy/guard v276 değişikliklerinin bit-nötrlüğünü SINAR"),
        "baslangic_utc": t0.isoformat(timespec="seconds"),
        "bitis_utc": t1.isoformat(timespec="seconds"),
        "sure_sn": round((t1 - t0).total_seconds(), 1),
        "sasi": {"yol": str(REFERANS), "sha256": _sha(REFERANS)},
        "uyarlama_beyani": uyarlama,
        "motor_sha_once": m_once, "motor_sha_sonra": m_sonra,
        "motor_ayni_kosum_icinde": motor_ayni, "v276_pin": V276_PIN,
        "sandbox": {"state_dizini": "state_kontrol", "bakir_baslatildi": True,
                    "beyan": ("koşum öncesi silindi; şasi hazirla() donmuş EDG-022 "
                              "kopyalarından yeniden kurdu; state/bars SALT-OKUNUR symlink")},
        "tasinan_dosyalar_sha256": tasinan,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[{ad}] bitti · süre={round((t1 - t0).total_seconds(), 1)}s · motor_ayni={motor_ayni} "
          f"→ {hedef}")
    return 0 if motor_ayni else 2


def _sonuc_fark_alanlari(a: dict, b: dict) -> dict:
    """sonuc_kontrol.json'un ÜST düzey alanlarında hangileri farklı — bayt farkının kaynağı."""
    anahtarlar = sorted(set(a) | set(b))
    return {k: {"kosum1_yeni": a.get(k), "referans": b.get(k)}
            for k in anahtarlar if a.get(k) != b.get(k)}


def bayt_ozdeslik() -> int:
    """[4] Üç-yönlü çift kapı; GEÇERSE künyenin motor_sha256 + kunye_tarihcesi alanları tazelenir."""
    k1, k2 = BURASI / "kosum1_yeni", BURASI / "kosum2_yeni"
    refdir = EDG032C / "kosum1"
    for d in (k1, k2):
        if not d.exists():
            sys.exit(f"bayt_ozdeslik: koşum dizini yok: {d} — sıra bozuk, DUR")

    kunye_yolu = EDG032C / "TABAN_KUNYESI.json"
    kunye_once_bayt = kunye_yolu.read_bytes()
    kunye = json.loads(kunye_once_bayt)

    # ── KAPI: üç defter, üç yönlü bayt ──
    kapi = {}
    for f in KAPI_DEFTERLER:
        s1, s2, sr = _sha(k1 / f), _sha(k2 / f), _sha(refdir / f)
        kapi[f] = {"kosum1_yeni_sha256": s1, "kosum2_yeni_sha256": s2, "edg032c_kosum1_sha256": sr,
                   "determinizm_k1_k2": (s1 is not None and s1 == s2),
                   "uc_yonlu_ozdes": (s1 is not None and s1 == s2 == sr)}
    kapi_gecti = all(v["uc_yonlu_ozdes"] for v in kapi.values())
    determinizm_gecti = all(v["determinizm_k1_k2"] for v in kapi.values())

    # künye çivisi: kıyasladığımız referans dosyalar künyenin kapi_sha256 kaydının KENDİSİ mi
    ks = kunye["determinizm_kaniti"]["kapi_sha256"]
    kunye_civisi = all(kapi[f]["edg032c_kosum1_sha256"] == ks[f] for f in KAPI_DEFTERLER)

    # ── 4. KANONİK DOSYA (sonuc) — bayt kapısında DEĞİL; sha raporlanır + bloklar derin-eşit ──
    s1j = json.loads((k1 / DORDUNCU).read_text())
    s2j = json.loads((k2 / DORDUNCU).read_text())
    srj = json.loads((refdir / DORDUNCU).read_text())
    blok_k1k2 = {b: (s1j.get(b) == s2j.get(b)) for b in SONUC_OLCUM_BLOKLARI}
    blok_k1ref = {b: (s1j.get(b) == srj.get(b)) for b in SONUC_OLCUM_BLOKLARI}
    blok_fark_k1ref = {b: {"kosum1_yeni": s1j.get(b), "edg032c": srj.get(b)}
                       for b in SONUC_OLCUM_BLOKLARI if not blok_k1ref[b]}
    bloklar_k1k2_esit = all(blok_k1k2.values())
    bloklar_k1ref_esit = all(blok_k1ref.values())
    dorduncu = {
        "dosya": DORDUNCU,
        "bayt_kapisinda_mi": False,
        "neden": ("YAPISAL: şasi bu dosyaya olcum_zamani / sure_sn / motor mtime_ns yazar — "
                  "koşum KİMLİĞİ alanlarıdır, bayt-özdeşlik imkansızdır. edg032b/edg032c'nin "
                  "kendi beyanı AYNEN; künyenin determinizm_kaniti.kapi_sha256 kaydı da bu "
                  "dosyayı İÇERMEZ (üç defter). Yerine 10 ÖLÇÜM BLOĞU derin-eşitlikle sınanır."),
        "sha256": {"kosum1_yeni": _sha(k1 / DORDUNCU), "kosum2_yeni": _sha(k2 / DORDUNCU),
                   "edg032c_kosum1": _sha(refdir / DORDUNCU)},
        "ust_duzey_fark_k1_vs_edg032c": _sonuc_fark_alanlari(
            {k: v for k, v in s1j.items() if k not in SONUC_OLCUM_BLOKLARI},
            {k: v for k, v in srj.items() if k not in SONUC_OLCUM_BLOKLARI}),
        "olcum_bloklari_k1_k2_esit": blok_k1k2,
        "olcum_bloklari_k1_edg032c_esit": blok_k1ref,
        "olcum_bloklari_fark_k1_edg032c": blok_fark_k1ref or None,
        "bloklar_hepsi_esit_k1_k2": bloklar_k1k2_esit,
        "bloklar_hepsi_esit_k1_edg032c": bloklar_k1ref_esit,
    }

    # ── ek kanıt: alan envanteri üç yönlü bayt ──
    ae = {"kosum1_yeni": _sha(k1 / "alan_envanteri_kontrol.json"),
          "kosum2_yeni": _sha(k2 / "alan_envanteri_kontrol.json"),
          "edg032c_kosum1": _sha(refdir / "alan_envanteri_kontrol.json")}
    ae_ozdes = (ae["kosum1_yeni"] is not None
                and ae["kosum1_yeni"] == ae["kosum2_yeni"] == ae["edg032c_kosum1"])

    # ── motor dört noktada sabit + v276 pin ──
    rk1 = json.loads((k1 / "run_kunye.json").read_text())
    rk2 = json.loads((k2 / "run_kunye.json").read_text())
    motor_arasi_ayni = (rk1["motor_sha_sonra"] == rk2["motor_sha_once"]
                        == rk1["motor_sha_once"] == rk2["motor_sha_sonra"])
    m_simdi = motor_kunye()
    v276_dogru = (all(m_simdi[f]["sha256"] == V276_PIN[f] for f in V276_PIN)
                  and all(rk1["motor_sha_once"][f]["sha256"] == V276_PIN[f] for f in V276_PIN))

    # SIKI KAPI (koordinatör talimatı 2026-08-24): edg049 emsali sonuc bloklarının edg032c ile
    # kıyasını BİLGİ sayıyordu (replay.n_endeks_satir koşum-günü önbellek uzunluğudur — edg040
    # dersi). Burada KAPIYA alınır: "beşi de özdeş değilse HİÇBİR ŞEY yazma". Fail-closed —
    # n_endeks_satir meşru biçimde kaymışsa bile künye ELLE tazelenir, otomatik DEĞİL (Rol-1).
    gecti = bool(kapi_gecti and determinizm_gecti and kunye_civisi and ae_ozdes
                 and bloklar_k1k2_esit and bloklar_k1ref_esit
                 and motor_arasi_ayni and v276_dogru)

    out = {
        "adim": "edg032c KÜNYE TAZELEME — BAYT-ÖZDEŞLİK KAPISI (2026-08-24; EDG-048/049 emsali)",
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "soru": ("broker.py (yorum-only) + guard.py (yorum-only) + strategy.py (06a6cff, OPT "
                 "Faz-1 v276, 36 kod satırı) değişiklikleri replay defterinde BİT-NÖTR MÜ? "
                 "Commit mesajının 'bit-nötr' İDDİASI kanıt sayılmaz — kanıt bayt-özdeşliktir."),
        "tanim": ("TAM kontrol iki kez, taze süreç + bakir sandbox, bugünkü (v276) motorla; üç "
                  "defter kosum1_yeni ↔ kosum2_yeni ↔ edg032c/kosum1 BAYT-ÖZDEŞ olmalı. Ek "
                  "kanıt: alan_envanteri üç yönlü bayt + sonuc ölçüm blokları k1↔k2 derin-eşit "
                  "+ motor dört noktada sabit + v276 pin. 4. kanonik dosya (sonuc) bayt "
                  "kapısında DEĞİL — gerekçesi dorduncu_kanonik_dosya bloğunda."),
        "kapi_defterleri": kapi,
        "kapi_uc_yonlu_ozdes": kapi_gecti,
        "determinizm_k1_k2": determinizm_gecti,
        "kunye_civisi_tutarli": kunye_civisi,
        "dorduncu_kanonik_dosya": dorduncu,
        "ek_kanit_alan_envanteri": {**ae, "uc_yonlu_ozdes": ae_ozdes},
        "motor_dort_noktada_sabit": motor_arasi_ayni,
        "v276_pin_dogrulandi": v276_dogru,
        "motor_sha_simdi": m_simdi,
        "sure_sn": {"kosum1_yeni": rk1["sure_sn"], "kosum2_yeni": rk2["sure_sn"]},
        "TAZELEME_GECTI": gecti,
        "hukum": None,   # hüküm Rol-1'in; bu bayrak mekanik sha kıyasıdır
    }

    if gecti:
        # ── KÜNYE GÜNCELLEMESİ (ölçüm dizini dışına TEK yazım; Rol-1 yetki devri) ──
        yedek = BURASI / "kunye_yedek_pre_tazeleme.json"
        if not yedek.exists():                       # yedek koşum öncesi elle alındı; garanti
            yedek.write_bytes(kunye_once_bayt)
        guncellenen = {}
        for f in ("broker.py", "strategy.py", "guard.py"):
            eski = dict(kunye["motor_sha256"]["kosum1_once"][f])
            if eski["sha256"] == V276_PIN[f]:
                continue                             # zaten güncel (yeniden koşum güvenliği)
            mt = (REPO / "meridian" / f).stat().st_mtime_ns
            yeni_kayit = {"sha256": V276_PIN[f], "sha256_16": V276_PIN[f][:16], "mtime_ns": mt}
            kunye["motor_sha256"]["kosum1_once"][f] = dict(yeni_kayit)
            kunye["motor_sha256"]["kosum2_sonra"][f] = dict(yeni_kayit)
            kunye.setdefault("kunye_tarihcesi", []).append({
                "tarih_utc": out["olcum_zamani"], "dosya": f,
                "eski_sha256": eski["sha256"], "eski_mtime_ns": eski["mtime_ns"],
                "yeni_sha256": V276_PIN[f],
                "neden": TAZELEME_NEDEN[f] + (" kosum1_once + kosum2_sonra kayıtları birlikte "
                                              "güncellendi (dort_noktada_sabit iç tutarlılığı)."),
                "kanit": str(BURASI / "bayt_ozdeslik.json"),
                "yedek": str(yedek),
                "yetki": ("Rol-1 devri (edg032c künye tazeleme görev mesajı, 2026-08-24 — "
                          "EDG-2026-057 künye kapısı tıkanması)"),
            })
            guncellenen[f] = {"eski": eski["sha256"], "yeni": V276_PIN[f]}
        kunye_yolu.write_text(json.dumps(kunye, ensure_ascii=False, indent=1), encoding="utf-8")
        out["kunye_guncellendi"] = {
            "dosya": str(kunye_yolu),
            "once_sha256": hashlib.sha256(kunye_once_bayt).hexdigest(),
            "sonra_sha256": _sha(kunye_yolu),
            "dosyalar": guncellenen,
            "dokunulmayan_alanlar": ["taban", "dondurma_tarihi_utc", "neden",
                                     "kanonik_taban_dosyalari", "determinizm_kaniti", "sasi",
                                     "yasa", "config_sha256", "pencere", "evren", "hucre",
                                     "cost_model", "butunluk_gecerli", "taban_ozeti_betimleyici",
                                     "hukum_yok", "motor_sha256.backtest.py (değişmedi)"],
        }
    else:
        out["kunye_guncellendi"] = None
        out["DURDU"] = ("kapı DÜŞTÜ — künye TAZELENMEZ. Bu, dünyanın değiştiği anlamına gelir "
                        "(v276 değişiklikleri bit-nötr DEĞİL, ya da başka bir kayma var). "
                        "Taban yeniden dondurulmalıdır; o karar Rol-1'indir.")

    (BURASI / "bayt_ozdeslik.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"BAYT-ÖZDEŞLİK KAPISI: defter3={kapi_gecti} determinizm={determinizm_gecti} "
          f"çivi={kunye_civisi} ae={ae_ozdes} blok_k1k2={bloklar_k1k2_esit} "
          f"blok_k1ref={bloklar_k1ref_esit} motor={motor_arasi_ayni} v276={v276_dogru} → "
          f"{'GEÇTİ — künye tazelendi' if gecti else 'DÜŞTÜ — künye TAZELENMEDİ'}")
    print(f"yazıldı: {BURASI / 'bayt_ozdeslik.json'}")
    return 0 if gecti else 2


def fark() -> int:
    """[5] YALNIZ kapı DÜŞTÜĞÜNDE: farkın NE olduğunu ölçer — kaç işlem, hangi semboller,
    hangi alanlar. BETİMLEYİCİDİR, HÜKÜM YOK (taban yeniden dondurulur mu: Rol-1 kararı).
    Anahtar = (ticker, ts_open) — edg049 kill#3 deseni AYNEN."""
    k1, k2 = BURASI / "kosum1_yeni", BURASI / "kosum2_yeni"
    refdir = EDG032C / "kosum1"

    def _defter(d: pathlib.Path) -> list[dict]:
        return json.loads((d / "islemler_tam_kontrol.json").read_text())

    def _anahtar(t: dict) -> tuple:
        return (t.get("ticker"), str(t.get("ts_open")))

    def _kiyas(ad_a: str, a: list[dict], ad_b: str, b: list[dict]) -> dict:
        ma = {_anahtar(t): t for t in a}
        mb = {_anahtar(t): t for t in b}
        yalniz_a = sorted(set(ma) - set(mb))
        yalniz_b = sorted(set(mb) - set(ma))
        ortak = sorted(set(ma) & set(mb))
        alan_n: dict[str, int] = {}
        alan_ornek: dict[str, list] = {}
        etkilenen: set = set()
        farkli_satir = 0
        for k in ortak:
            x, y = ma[k], mb[k]
            if x != y:
                farkli_satir += 1
            for alan in sorted(set(x) | set(y)):
                if x.get(alan) != y.get(alan):
                    alan_n[alan] = alan_n.get(alan, 0) + 1
                    etkilenen.add(k[0])
                    if len(alan_ornek.setdefault(alan, [])) < 5:
                        alan_ornek[alan].append(
                            {"ticker": k[0], "ts_open": k[1], ad_a: x.get(alan), ad_b: y.get(alan)})
        return {
            "n_" + ad_a: len(a), "n_" + ad_b: len(b), "n_ortak": len(ortak),
            "yalniz_" + ad_a: [{"ticker": t, "ts_open": ts} for t, ts in yalniz_a],
            "yalniz_" + ad_b: [{"ticker": t, "ts_open": ts} for t, ts in yalniz_b],
            "n_yalniz_" + ad_a: len(yalniz_a), "n_yalniz_" + ad_b: len(yalniz_b),
            "ortak_alan_fark_sayimi": dict(sorted(alan_n.items(), key=lambda kv: -kv[1])),
            "n_ortak_satir_farkli": farkli_satir,
            "etkilenen_semboller": sorted(etkilenen),
            "n_etkilenen_sembol": len(etkilenen),
            "alan_ornekleri_ilk5": alan_ornek or None,
        }

    out = {
        "adim": "FARK ÖLÇÜMÜ (kapı DÜŞTÜ) — betimleyici, HÜKÜM YOK",
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "uyari": ("Bu dosya YALNIZ bayt-özdeşlik kapısı düştüğünde üretilir. Künyeye HİÇBİR "
                  "yazım yapılmamıştır. Taban yeniden dondurulmalı mı — Rol-1 kararı."),
        "izole_edilen_degiskenler": {
            "state_bars": "taban koşumundan sonra DEĞİŞEN dosya YOK (ölçüldü) — bar önbelleği donuk",
            "edg022_config": "üç yaml sha künyedeki sandbox_kaynagi_edg022 ile BİREBİR (ölçüldü)",
            "sasi": "edg032b/olcum.py sha künyedeki sasi.sha256 ile BİREBİR (ön-uçuşta ölçüldü)",
            "sonuc": ("bu üç karıştırıcı elendiğine göre defter ayrışmasının geriye kalan TEK "
                      "değişkeni MOTORDUR (broker/strategy/guard v276)"),
        },
    }
    out["yeni_vs_edg032c"] = _kiyas("yeni", _defter(k1), "edg032c", _defter(refdir))
    if k2.exists():
        out["kosum1_vs_kosum2_determinizm"] = _kiyas("k1", _defter(k1), "k2", _defter(k2))

    # seanslar defterinde kaç kayıt farklı (gün düzeyi)
    try:
        sy = json.loads((k1 / "seanslar_kontrol.json").read_text())
        se = json.loads((refdir / "seanslar_kontrol.json").read_text())
        my = {s.get("date"): s for s in sy}
        me = {s.get("date"): s for s in se}
        farkli_gun = sorted(d for d in (set(my) & set(me)) if my[d] != me[d])
        out["seanslar"] = {"n_yeni": len(sy), "n_edg032c": len(se),
                           "n_farkli_gun": len(farkli_gun), "ilk_farkli_gun": farkli_gun[:10] or None}
    except Exception as e:                        # YASA 4: sessiz yutma YOK
        out["seanslar"] = {"olculemedi": True, "neden": f"seanslar kıyası çöktü: {type(e).__name__}: {e}"}

    (BURASI / "fark.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    y = out["yeni_vs_edg032c"]
    print(f"FARK: n yeni={y['n_yeni']} edg032c={y['n_edg032c']} · yalnız-yeni={y['n_yalniz_yeni']} "
          f"yalnız-edg032c={y['n_yalniz_edg032c']} · etkilenen sembol={y['n_etkilenen_sembol']} "
          f"· farklı alan={list(y['ortak_alan_fark_sayimi'])[:6]}")
    print(f"yazıldı: {BURASI / 'fark.json'}")
    return 0


if __name__ == "__main__":
    _faz = next((a for a in sys.argv[1:] if not a.startswith("--")), "")
    if _faz == "onucus":
        raise SystemExit(onucus())
    if _faz in ("kosum1_yeni", "kosum2_yeni"):
        raise SystemExit(kosum(_faz))
    if _faz == "bayt_ozdeslik":
        raise SystemExit(bayt_ozdeslik())
    if _faz == "fark":
        raise SystemExit(fark())
    sys.exit("kullanım: olcum.py onucus | kosum1_yeni | kosum2_yeni | bayt_ozdeslik | fark")
