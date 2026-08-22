"""EDG-2026-045 — bar-içi stop-dolum slipajı taraması · ölçüm koşumu (2026-08-22).

KART: research/cards/EDG-2026-045-stop-slip.yaml (OKU-DOKUNMA; eşik/kill/grid ORADA DONUK).
Ölçüm ajanı karta DOKUNMAZ; hükmü Rol-1 işler. Bu betik HÜKÜM VERMEZ, sayı getirir.
Ö2 OKUMA KURALI (kart, donuk): 042-K3 bandı gelmeden bu ölçümle EDG-040 hükmü REVİZE EDİLMEZ.

NE YAPAR: edg032b şasisini (C+mb @5R · 2022-01→2026-07) AYNEN koşar; TEK değişken: yalnız
BAR-İÇİ stop dolumlarına (kademe-2, exit_reason "stop") ek aleyhte slipaj
ek_slip ∈ {5, 10, 20} bps — dolum eff_stop×(1−ek_slip) sayılır. stop_gap (kademe-1, açılış
dolumu) DOKUNULMAZ: zaten gerçek fiyat basar; sızma kill kriteridir ve AYRICA kanıtlanır.

════════ YENİDEN-ÇAPALAMA (2026-08-22, koşum #2 — Rol-1; kart bloğu:
sasi_capasi_guncellemesi_2026_08_22) ════════
İlk koşum kill#1'de DOĞRU durdu (DURDU_kill1_sasi_kapisi.json): B1 kararı (c150902) dünyayı
değiştirdi, edg032b tabanı bugünkü motorla yeniden üretilemez. Rol-1 YENİ TABAN dondurdu:
edg032c_taban_2026-08-22 (kanonik defterler kosum1/, künye TABAN_KUNYESI.json, determinizm
çift-kapılı). BU koşumda kıyas tabanı = edg032c; EŞİK/K/KARAR KURALLARI AYNEN. Betik
farkları (KOMUT.txt'te sha'larla):
  (a) kill#1 bayt-kıyas hedefi edg032b → edg032c/kosum1 (smoke: kosum1_smoke);
  (b) şasinin ARMED_BEKLENEN dünya-beklentisi B1 yasasına çevrilir (edg032c künyesindeki
      BEYANLI TEK UYARLAMA deseni AYNEN — motor DEĞİL, yüklenen modülün beklenti sabiti;
      motor B1'den saparsa koşum BAŞLAMADAN durur);
  (c) referansın ozdeslik() kapısı (032-cmb kıyası) ÇAĞRILMAZ — o kapı ESKİ dünyanın kimlik
      kapısıydı (edg032c künyesi aynı gerekçeyle çağırmadı; kapısı determinizm çift-kapısı).
      kill#1 kimliği edg032c defter bayt-özdeşliğiyle sınanır; edg040'ın DARALTILMIŞ
      n_endeks_satir istisnası da ozdeslik çağrısıyla birlikte düştü — burada istisna YOK;
  (d) motor sha izleme 2 → 4 dosya (broker/backtest/strategy/guard) ve edg032c künyesindeki
      değerlere ÇİVİLİ: koşum başında künyeyle eşleşmezse BAŞLAMADAN DUR, hücre içinde
      değişir ya da künyeden saparsa o hücre geçersiz (kill#4).

════════ TASARIM: DONMUŞ DESENLER BİRLEŞTİRİLDİ, YENİDEN İCAT YOK ════════
edg040_friksiyon_2026-08-22/olcum.py deseni AYNEN: referans şasi (edg032b/olcum.py)
importlib ile modül olarak yüklenir, `SANDBOX`ı BU dizine çevrilir (artefakt koruması
YAPISAL: edg032b'nin donmuş kanıtına tek bayt yazılamaz), `kosum(run, smoke)` yolu OLDUĞU
GİBİ çağrılır (imza tahmini YOK — exe006 2026-08-17 dersi). Şasi kapısı (kill#1, sha256 —
hedef YENİDEN-ÇAPALAMA (a) gereği edg032c/kosum1) ve eşlenik
ay-kümeli bootstrap (B=5000, seed=20260812, birim=AY) edg040'tan HARFİ HARFİNE.

════════ ENJEKSİYON YÜZEYİ (koddan okundu, varsayılmadı) — EDG-040'TAN FARKI ════════
edg040 friksiyonu goal.slippage_bps ile İKİ BACAĞA simetrik enjekte etmişti. BU kart yalnız
bar-içi stop-tetik kanalını sınar. Kanal koddan izlendi:
  broker.py:660 `_touch_exit` — İKİ KADEME:
    :684 `eff_stop = max(pos.stop, pos.trail_stop)`
    :686-687 `if o <= eff_stop: return o, "stop_gap"`      ← kademe-1: AÇILIŞ, gerçek fiyat
    :691-692 `if l <= eff_stop: return eff_stop, "stop"`   ← kademe-2: bar içi, TAM eff_stop
  backtest.py:364-366 `ex = broker._touch_exit(...)` → `broker.close_position(t, ex[0], ex[1], …)`
  broker.py:753 `close_position(ticker, raw_exit, reason, ts)` → :765
    `exit_fill = raw_exit * (1.0 - self.slip)`  (genel maliyet modeli, 5 bps — DOKUNULMAZ)
"stop" reason'ı BAŞKA HİÇBİR YOLDAN üretilmez (strategy.ManageDecision çıkışları:
early_kill_pivot/giveback/time_stop/regime_flip; diğer close reason'ları: stop_gap/
target_gap/target/eod_markout/delisted_markout — grep ile sınandı, ayrıca betik başında
kaynak-çivisi assert'i var). Dolayısıyla ENJEKSİYON: `PaperBroker.close_position` süreç-içi
sarmalanır; reason=="stop" iken raw_exit → raw_exit×(1−ek_slip). Motorun kendi genel
slipajı (5 bps) HER ZAMANKİ GİBİ üstüne işler → defter dolumu
eff_stop×(1−ek_slip)×(1−0.0005). Diğer TÜM reason'larda raw_exit DEĞİŞMEDEN geçer.
KONTROL@0 SARMALAYICI AÇIKKEN koşulur (raw_exit×(1−0.0)=raw_exit — bayt-nötr): bayt-özdeşlik
şasiyi VE enjeksiyon yüzeyinin nötrlüğünü BİRLİKTE kanıtlar (edg040 deseni AYNEN).
goal SÖZLÜĞÜNE DOKUNULMAZ: her koşumda cost_model.slippage_bps == 5.0 assert'lenir.

════════ ÖZ-SINAMA (kill#2) + SIZMAZLIK (kill#3) — kartın uyarlanmış sınamaları ════════
Sarmalayıcı her kapanışta HAM girdileri yakalar (orig raw_exit, enjekte raw_exit, kapanış
ÖNCESİ pos.stop/pos.trail_stop, defter satırının exit/r_multiple/pnl'i). Sınamalar TÜM
kapanışlar üstünde (ilk-N değil — stop dolumu kill yüzeyinin kendisidir):
  S1 (kart formülü)  stop satırlarında |(1 − fill/eff_stop) − ek_slip| ≤ 1e-9
                     (fill = enjekte stop-dolum seviyesi; eff_stop = orig raw_exit)
  S2 (deftere çivili) round((eff_stop×(1−ek_slip))×(1−broker.slip), 4) == defter['exit']
                     — enjeksiyonun motor maliyet zincirinden DEFTERE indiğinin kanıtı
  S3 (kanal kimliği) orig == max(pos.stop, pos.trail_stop) birebir — "stop" satırının
                     gerçekten kademe-2 eff_stop dolumu olduğu, varsayılmadı ölçüldü
  Z1 (kill#3 sızmazlık) stop_gap + DİĞER tüm reason'larda enjekte == orig (fark ≡ 0,
                     max|fark| raporlanır) VE round(orig×(1−slip),4) == defter['exit']
  T  (trail künyesi)  stop satırlarında pos.trail_stop > pos.stop payı — trail_stop'tan
                     gelen dolumlar AYNI kademedir, ayrı kova AÇILMAZ (kartın beyanlı
                     sınırı 2); payı künyelenir, R dağılımı alt-kümede de raporlanır
  A  (ayırt edicilik) aynı S1 farkı ek_slip=0 beklentisiyle: hücrelerde ≈ ek_slip çıkmalı
                     (sınama yanlış enjeksiyonu YAKALAYABİLİR — boş geçen sınama sınama değildir)
broker.slip == 0.0005 her satırda ayrıca sınanır (genel modelin değişmediğinin satır kanıtı).
2026-08-23 ALET DÜZELTMESİ (Rol-1 talimatı; EDG-040 kill#2 emsali — alet GEVŞETİLMEZ,
TAMAMLANIR): S2/Z1'in defter-yeniden-kurma yuvarlaması motorun kendi TİP yoluna eşitlendi
(`defter_yuvarla`, aşağıda beyanıyla) — formüller, S1 toleransı (1e-9) ve sınamalar AYNEN;
hiçbir sınama kaldırılmadı/gevşetilmedi. `--tamamla` akışı: kayıtlı kontrol@0 + stopslip5
düzeltilmiş aletle DİSKTEN yeniden doğrulanır (replay YOK, K harcamaz), stopslip10/20
koşulur, üç hücrenin Δ+CI'sı üretilir.

NET P&L KANONİK ALANDAN: `performans.net_pnl_trades` (islem.net_pnl YOK — exe006 tuzağı).
PF şasi çıktısında yok → tam defterden Σ(pnl>0)/|Σ(pnl<0)| (EDG-037 tanımı; edg040, donmuş
edg032b defterinde 1,1119 doğrulamıştı; edg032c taban PF'i bu koşumda AYNI tanımla taban
defterinden hesaplanıp raporlanır).

SIRALAMA (kill kriterleri zorlar):
  [1] --smoke: kablo (kontrol@0 + stopslip10 hücresi, 2022-01→06) + öz-sınama + sızmazlık
  [2] kontrol@0 TAM → ŞASİ KAPISI: islemler_tam/islemler(slim)/seanslar edg032c/kosum1
      DONMUŞ defterleriyle sha256 BAYT-ÖZDEŞ (referans ozdeslik() ÇAĞRILMAZ — eski dünyanın
      kapısı; YENİDEN-ÇAPALAMA (c)). DÜŞERSE DUR (kill#1).
  [3] ÜÇ HÜCRE ek_slip {5,10,20} bps — her birinde öz-sınama (kill#2) + sızmazlık (kill#3)
      + şasi bütünlüğü + hücre-başı motor sha önce/sonra (kill#4: koşum İÇİNDE değişirse o
      hücre geçersiz — bugünkü uçuş-commit dersi)
  [4] ΔP&L + CI: hücre vs DONMUŞ taban (edg032c/kosum1/islemler_tam_kontrol.json) — EŞLENİK
      ay-kümeli bootstrap B=5000 seed 20260812, birim=AY, iki kol AYNI ayı görür
  [5] motor sha koşum-öncesi/sonrası (broker/backtest/strategy/guard — DÖRDÜ, tam sha,
      edg032c künyesine çivili)

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen None + neden) · YASA-4 (sessiz-yutma işaretli) ·
git KOŞULMAZ · state/ YAZILMAZ (şasi kendi sandbox'ına yönlendirir) · test suite KOŞULMAZ ·
motor dosyalarına DOKUNULMAZ (sarmalayıcı süreç-içi ve bloklu; finally ile geri alınır) ·
karta TEK BAYT yazılmaz.
"""
import contextlib
import datetime as dt
import hashlib
import importlib.util
import json
import pathlib
import sys

BURASI = pathlib.Path(__file__).resolve().parent
REPO = BURASI.parents[2]
REFERANS = REPO / "research" / "olcumler" / "edg032b_tamsatir_2026-08-13" / "olcum.py"
EDG032B = REFERANS.parent               # ŞASİ dizini (betik burada; artık kıyas TABANI DEĞİL)
EDG032C = REPO / "research" / "olcumler" / "edg032c_taban_2026-08-22"
TABAN_DIR = EDG032C / "kosum1"          # KANONİK taban defterleri (TABAN_KUNYESI.json)
TABAN_DIR_SMOKE = EDG032C / "kosum1_smoke"
sys.path.insert(0, str(REPO))

TABAN_EK_BPS = 0.0                      # kontrol: enjeksiyon yüzeyi AÇIK, ek slipaj SIFIR
HUCRE_EK_BPS = [5.0, 10.0, 20.0]        # kartın parameter_grid'i stop_ek_slip_bps — DEĞİŞTİRİLEMEZ (K=3)
SLIP_TABAN_BEKLENEN = 0.0005            # taban dünyasının genel maliyet modeli (5 bps) — assert
BOOT_SEED = 20260812
BOOT_ITER = 5000
MOTOR_SHA_DOSYALAR = ("broker.py", "backtest.py", "strategy.py", "guard.py")

# B1 YASASI — bugünkü motor beklentisi (c150902; strategy.py:1059); edg032c künyesiyle tutarlı.
# Şasinin ARMED_BEKLENEN dünya-beklentisi buna çevrilir (motor DEĞİL — edg032c deseni AYNEN).
B1_YASA = ("breakout_vcp", "exhaustion_hammer", "momentum_burst")

# TABAN MOTOR KİMLİĞİ — edg032c/TABAN_KUNYESI.json motor_sha256 (kosum1_once == kosum2_sonra,
# dort_noktada_sabit=true). Koşum başında eşleşmezse ölçüm BAŞLAMADAN DURUR (dünya kimliği —
# ilk koşumun kill#1 dersi); hücre içinde sapma = kill#4.
TABAN_MOTOR_SHA = {
    "broker.py": "52e67c5db43f52d5978927c3a7acba8c46b769d1f79fc1ebccdd55e67b5929ac",
    "backtest.py": "b59c059f43d4e410c198eb36ced18539d7575e7060d8c11337386a6ebf77cbd5",
    "strategy.py": "263eb8fef7d10089653bc72fd7dd86ba1ee3f3003c2e28ea2c915569af8b8140",
    "guard.py": "467034e580311150b2b0b9d441c7e83b4a396688e6506c8001f0f9cc2912db6c",
}

# KAYNAK ÇİVİLERİ — enjeksiyon yüzeyinin kod satırları (broker.py'de birebir aranır; yoksa
# motor değişmiş demektir ve ölçüm başlamadan DURUR — satır varsayılmaz, sınanır)
KAYNAK_CIVILERI = (
    'return o, "stop_gap"',                            # kademe-1 (broker.py:687) — DOKUNULMAZ
    'return eff_stop, "stop"',                         # kademe-2 (broker.py:692) — enjeksiyon hedefi
    "exit_fill = raw_exit * (1.0 - self.slip)",        # genel maliyet modeli (broker.py:765)
    "eff_stop = max(pos.stop, pos.trail_stop)",        # eff_stop tanımı (broker.py:684)
)


# ── DEFTER-YENİDEN-KURMA YUVARLAMASI (alet düzeltmesi 2026-08-23 — Rol-1 talimatı;
#    EDG-040 kill#2 emsali: alet GEVŞETİLMEZ, TAMAMLANIR) ──
# Motorun defter yazımı: broker.py:790 `"exit": round(exit_fill, 4)`; exit_fill = raw_exit ×
# (1−self.slip) (broker.py:765). Mekanizma round() AMA işlenen TİPİ reason yoluna göre değişir
# ve .xxxx5 bağ değerlerinde sonucu değiştirir (KODDAN OKUNDU + kayıtlı defterde doğrulandı):
#   · BAR-FİYATI basan yollar → pandas .loc → np.float64 → round(np.float64) =
#     np.float64.__round__ (ölçek-çarpımlı): stop_gap/target_gap (backtest.py:364 →
#     _touch_exit `o`), time_stop/regime_flip (backtest.py:312 `per[t].loc[d,"open"]`),
#     eod_markout/delisted_markout (backtest.py:556/563 `close`).
#   · PLAN-ALANI basan yollar → strategy.py:333/335 round(float,4) → Python float →
#     Python round() (doğru-yuvarlamalı): stop (eff_stop = max(pos.stop, pos.trail_stop),
#     broker.py:684) ve target (pos.target, broker.py:693).
# DOĞRULAMA (tahmin değil, ölçüm): 13 bağ satırının 13'ü np yolunda deftere birebir; META
# 2025-02-14 'target' Python yolunda birebir (np yolunda DEĞİL); karma model kontrol@0 ve
# stopslip5 kayıtlı defterlerinde 885/885. Tolerans (1e-9) ve tüm formüller DEĞİŞMEDİ —
# yalnız yeniden-kurma yuvarlaması motorunkine eşitlendi; hiçbir sınama kaldırılmadı.
NP_YUVARLANAN_REASONLAR = frozenset(
    {"stop_gap", "target_gap", "time_stop", "regime_flip", "eod_markout", "delisted_markout"})


def defter_yuvarla(x: float, reason: str) -> float:
    """Motorun round(exit_fill, 4) yazımını reason'ın TİP yoluyla birebir yeniden kurar."""
    import numpy as np
    if reason in NP_YUVARLANAN_REASONLAR:
        return float(round(np.float64(x), 4))
    return round(x, 4)


def _sha_full(p: pathlib.Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None    # ölçülemedi (dosya yok/okunamadı)


def motor_sha() -> dict:
    return {f: _sha_full(REPO / "meridian" / f) for f in MOTOR_SHA_DOSYALAR}


def kaynak_civisi_kontrol() -> dict:
    """Enjeksiyon yüzeyi satırları broker.py'de HÂLÂ var mı? (varsayım değil, sınama)."""
    src = (REPO / "meridian" / "broker.py").read_text(encoding="utf-8")
    eksik = [c for c in KAYNAK_CIVILERI if c not in src]
    if eksik:
        raise AssertionError(
            f"KAYNAK ÇİVİSİ TUTMADI — broker.py'de bulunamayan satır(lar): {eksik} — "
            f"enjeksiyon yüzeyi değişmiş, ölçüm başlamadan DURUR (kartın uçuş-commit dersi)")
    return {"civiler": list(KAYNAK_CIVILERI), "hepsi_bulundu": True}


def referans_modul():
    """Referans koşumu (edg032b) modül olarak yükler ve `SANDBOX`ını BU dizine çevirir.

    `__main__` bloğu `sys.argv`e bakıp iş yapıyor; modül olarak yüklerken argv geçici olarak
    boşaltılır ki içe aktarma bir koşum TETİKLEMESİN (exe006b/edg040 deseni AYNEN)."""
    sp = importlib.util.spec_from_file_location("edg032b_ref", REFERANS)
    m = importlib.util.module_from_spec(sp)
    eski_argv = sys.argv
    sys.argv = [str(REFERANS)]
    try:
        sp.loader.exec_module(m)
    except SystemExit:                # `raise SystemExit(main())` deseni — içe aktarmada beklenir
        pass
    finally:
        sys.argv = eski_argv
    m.SANDBOX = BURASI                # ← artefakt koruması: referans dizine ASLA yazılmaz
    # ── YENİDEN-ÇAPALAMA (b): şasinin dünya-beklentisi B1 yasasına — edg032c künyesindeki
    # BEYANLI TEK UYARLAMA deseni AYNEN (motor DEĞİL, yüklenen modülün beklenti sabiti;
    # şasinin diğer HİÇBİR sabiti/assert'i/parametresi değiştirilmez)
    eski_beklenen = tuple(m.ARMED_BEKLENEN)
    m.ARMED_BEKLENEN = B1_YASA
    from meridian import strategy as _st
    assert tuple(_st.ARMED_SETUPS) == B1_YASA, \
        f"MOTOR B1 YASASINDAN SAPMIŞ: {_st.ARMED_SETUPS} ≠ {B1_YASA} — koşum BAŞLAMADAN durdu"
    m._edg045_armed_uyarlama = {
        "eski_ARMED_BEKLENEN": list(eski_beklenen), "yeni_ARMED_BEKLENEN": list(B1_YASA),
        "motor_ARMED_SETUPS": list(_st.ARMED_SETUPS)}
    return m


@contextlib.contextmanager
def stop_slip_enjekte(kayit: dict, ek: float):
    """`PaperBroker.close_position` sarmalanır: reason=="stop" (kademe-2) iken raw_exit →
    raw_exit×(1−ek). BAŞKA HİÇBİR reason'a dokunulmaz (stop_gap sızmazlığı kill#3).
    Kapanış ÖNCESİ pozisyon durumu (stop/trail_stop) ve defter satırı yakalanır — öz-sınamanın
    tek dürüst kaynağı. Süreç-içi sınıf-yaması; motor DOSYASI yamasız (kill#4 sha kontrolü).
    ek=0.0 iken raw_exit×1.0 bayt-nötrdür → kontrol@0 bayt-özdeşliği yüzey nötrlüğünü kanıtlar.

    Parametre adları motor imzasıyla BİREBİR (broker.py:753) — ad uydurma yok."""
    from meridian import broker as B
    asil = B.PaperBroker.close_position

    def close(self, ticker, raw_exit, reason, ts):
        pos = self.positions.get(ticker)          # asıl fonksiyon pop etmeden ÖNCE oku
        p_stop = float(pos.stop) if pos is not None else None
        p_trail = float(pos.trail_stop) if pos is not None else None
        enj = raw_exit * (1.0 - ek) if reason == "stop" else raw_exit
        row = asil(self, ticker, enj, reason, ts)
        kayit["cikis"].append({
            "ticker": ticker, "ts": ts, "reason": reason,
            "raw_exit_orig": float(raw_exit), "raw_exit_enjekte": float(enj),
            "defter_exit": float(row["exit"]), "qty": int(row["qty"]),
            "broker_slip": float(self.slip),
            "pos_stop": p_stop, "pos_trail": p_trail,
            "pos_okunamadi": pos is None,          # sessiz-yutma DEĞİL: adıyla sayılır (YASA-4)
            "r_multiple": (float(row["r_multiple"]) if row.get("r_multiple") is not None else None),
            "pnl_dollars": (float(row["pnl_dollars"]) if row.get("pnl_dollars") is not None else None),
            "scaled_out": bool(row.get("scaled_out"))})
        return row

    B.PaperBroker.close_position = close
    try:
        yield
    finally:
        B.PaperBroker.close_position = asil


def _r_dagilim(rler: list) -> dict | None:
    import numpy as np
    r = [x for x in rler if x is not None]
    if not r:
        return None
    a = np.asarray(r, dtype=float)
    q = {f"p{p}": round(float(np.percentile(a, p)), 4) for p in (10, 25, 50, 75, 90)}
    return {"n": int(len(a)), "ort": round(float(a.mean()), 4),
            "min": round(float(a.min()), 4), "max": round(float(a.max()), 4), **q,
            "r_none_n": len(rler) - len(r)}


def oz_sinama(kayit: dict, ek: float) -> dict:
    """kill#2 (S1/S2/S3) + kill#3 sızmazlık (Z1) + trail künyesi (T) + ayırt edicilik (A).
    TÜM kapanışlar sınanır (ilk-N değil). Dönen sözlük mekanik sayımdır; geçti/düştü bayrağı
    taşır ama HÜKÜM Rol-1'in."""
    cikislar = kayit["cikis"]
    stoplar = [c for c in cikislar if c["reason"] == "stop"]
    gapler = [c for c in cikislar if c["reason"] == "stop_gap"]
    digerler = [c for c in cikislar if c["reason"] not in ("stop", "stop_gap")]

    def s_satir(c):
        orig, enj = c["raw_exit_orig"], c["raw_exit_enjekte"]
        s1_fark = (1.0 - enj / orig) - ek if orig else None
        # enj == orig×(1−ek) bit-birebir (sarmalayıcı aynı ifadeyle üretti); motor tip-yolu
        # yuvarlamasıyla yeniden kurulur (alet düzeltmesi 2026-08-23 — formül AYNEN)
        beklenen_defter = defter_yuvarla(enj * (1.0 - c["broker_slip"]), c["reason"])
        eff = (max(c["pos_stop"], c["pos_trail"])
               if (c["pos_stop"] is not None and c["pos_trail"] is not None) else None)
        trail_ustte = (c["pos_trail"] > c["pos_stop"]
                       if (c["pos_stop"] is not None and c["pos_trail"] is not None) else None)
        return {
            "ticker": c["ticker"], "ts": c["ts"],
            "S1_fark": s1_fark, "S1_gecti": (s1_fark is not None and abs(s1_fark) <= 1e-9),
            "S2_beklenen_defter": beklenen_defter, "S2_defter_exit": c["defter_exit"],
            "S2_gecti": beklenen_defter == c["defter_exit"],
            "S3_orig_eff_stop_esit": (eff is not None and orig == eff),
            "slip_taban_esit": c["broker_slip"] == SLIP_TABAN_BEKLENEN,
            "trail_ustte": trail_ustte, "r_multiple": c["r_multiple"],
            "A_ayirt_fark_ek0_beklentisiyle": (1.0 - enj / orig) if orig else None}

    def z_satir(c):
        orig, enj = c["raw_exit_orig"], c["raw_exit_enjekte"]
        beklenen_defter = defter_yuvarla(orig * (1.0 - c["broker_slip"]), c["reason"])
        return {
            "ticker": c["ticker"], "ts": c["ts"], "reason": c["reason"],
            "Z1_fark": abs(enj - orig), "Z1_gecti": enj == orig,
            "Z1_defter_beklenen": beklenen_defter, "Z1_defter_exit": c["defter_exit"],
            "Z1_defter_gecti": beklenen_defter == c["defter_exit"],
            "slip_taban_esit": c["broker_slip"] == SLIP_TABAN_BEKLENEN}

    s_detay = [s_satir(c) for c in stoplar]
    z_gap = [z_satir(c) for c in gapler]
    z_diger = [z_satir(c) for c in digerler]

    s_bozuk = [d for d in s_detay if not (d["S1_gecti"] and d["S2_gecti"]
                                          and d["S3_orig_eff_stop_esit"] and d["slip_taban_esit"])]
    z_bozuk = [d for d in (z_gap + z_diger)
               if not (d["Z1_gecti"] and d["Z1_defter_gecti"] and d["slip_taban_esit"])]
    okunamadi = sum(1 for c in cikislar if c["pos_okunamadi"])

    n_stop = len(stoplar)
    trail_n = sum(1 for d in s_detay if d["trail_ustte"] is True)
    hard_n = sum(1 for d in s_detay if d["trail_ustte"] is False)
    kill2 = (n_stop > 0 and not s_bozuk and okunamadi == 0)
    kill3_sizinti_yok = (not z_bozuk and okunamadi == 0)

    reason_n: dict[str, int] = {}
    for c in cikislar:
        reason_n[c["reason"]] = reason_n.get(c["reason"], 0) + 1

    return {
        "beklenen_ek_slip": ek,
        "n_cikis_yakalanan": len(cikislar), "reason_dagilim_yakalanan": reason_n,
        "n_stop": n_stop, "n_stop_gap": len(gapler), "n_diger": len(digerler),
        "pos_okunamadi_n": okunamadi,
        # kill#2 — kart formülü S1 + deftere çivili S2 + kanal kimliği S3
        "S1_max_mutlak_fark": max((abs(d["S1_fark"]) for d in s_detay
                                   if d["S1_fark"] is not None), default=None),
        "S2_defter_esit_n": sum(1 for d in s_detay if d["S2_gecti"]),
        "S3_eff_stop_esit_n": sum(1 for d in s_detay if d["S3_orig_eff_stop_esit"]),
        "stop_bozuk_satirlar": s_bozuk, "stop_bozuk_n": len(s_bozuk),
        "kill2_gecti": kill2,
        "kill2_olculemedi_nedeni": (None if n_stop > 0 else
                                    "yakalanan stop dolumu YOK — pencere kısa (duman?); sınama boş"),
        # kill#3 — sızmazlık: stop_gap + diğer TÜM reason'lar değişmeden geçmeli
        "Z1_stop_gap_max_fark": max((d["Z1_fark"] for d in z_gap), default=None),
        "Z1_diger_max_fark": max((d["Z1_fark"] for d in z_diger), default=None),
        "Z1_defter_esit_n": sum(1 for d in (z_gap + z_diger) if d["Z1_defter_gecti"]),
        "sizinti_bozuk_satirlar": z_bozuk, "sizinti_bozuk_n": len(z_bozuk),
        "kill3_sizinti_yok": kill3_sizinti_yok,
        # T — trail künyesi (ayrı kova YOK; kart beyanlı sınır 2)
        "trail_kunyesi": {
            "stop_trail_ustte_n": trail_n, "stop_hard_n": hard_n,
            "trail_pay_pct": round(100.0 * trail_n / n_stop, 2) if n_stop else None,
            "belirsiz_n": n_stop - trail_n - hard_n,
            "beyan": ("trail_ustte = kapanış ANINDA pos.trail_stop > pos.stop (breakeven "
                      "kilidi dahil) — aynı kademe-2 kanalı, künye amaçlı; ayrı kova açılmadı")},
        # A — ayırt edicilik: hücrelerde S1 farkı ek=0 beklentisiyle ≈ ek_slip çıkmalı
        "A_ayirt_min": min((d["A_ayirt_fark_ek0_beklentisiyle"] for d in s_detay
                            if d["A_ayirt_fark_ek0_beklentisiyle"] is not None), default=None),
        "A_ayirt_max": max((d["A_ayirt_fark_ek0_beklentisiyle"] for d in s_detay
                            if d["A_ayirt_fark_ek0_beklentisiyle"] is not None), default=None),
        # stop-çıkış R dağılımı (kart features_asof) — toplam + trail/hard alt-kümeleri
        "stop_r_dagilim": _r_dagilim([d["r_multiple"] for d in s_detay]),
        "stop_r_dagilim_trail": _r_dagilim([d["r_multiple"] for d in s_detay
                                            if d["trail_ustte"] is True]),
        "stop_r_dagilim_hard": _r_dagilim([d["r_multiple"] for d in s_detay
                                           if d["trail_ustte"] is False]),
        "beyan": ("S1 kart formülü: fill = enjekte stop-dolum seviyesi (genel 5bps modelinden "
                  "ÖNCE), eff_stop = orig raw_exit (= broker.py:692'nin döndürdüğü değer; S3 bunu "
                  "max(stop,trail)'e karşı ayrıca sınar). S2 defterin KENDİSİNE çivili: enjekte "
                  "seviye × (1−broker.slip) 4 hanede defter['exit'] ile birebir. Z1 sızmazlık: "
                  "stop dışı HİÇBİR kapanışta raw_exit değişmedi (fark ≡ 0) ve defter, motorun "
                  "yamasız aritmetiğiyle birebir. Tüm sınamalar TÜM kapanışlar üstünde."),
    }


def hucre_kos(ref, run: str, ek_bps: float, smoke: bool) -> dict:
    """Tek hücre: stop-slip sarmalayıcısı tak → ŞASİYİ ÇAĞIR → öz-sınama + özet çıkar.
    Hücre-başı motor sha önce/sonra (kill#4: koşum İÇİNDE değişirse o hücre geçersiz)."""
    ref.HUCRELER.setdefault(run, {})       # tüm hücreler MERKEZ dünyası (slot20+0,5R+5R) — sapma yok
    ek = ek_bps / 10000.0
    kayit: dict = {"cikis": []}
    m_once = motor_sha()
    with stop_slip_enjekte(kayit, ek):
        ref.kosum(run, smoke=smoke)        # ŞASİ: referansın kendi yolu, dokunulmadan
    m_sonra = motor_sha()
    hucre_motor_ayni = (m_once == m_sonra)
    hucre_motor_kunye_esit = (m_once == TABAN_MOTOR_SHA and m_sonra == TABAN_MOTOR_SHA)

    ek_ad = "_smoke" if smoke else ""
    outdir = (BURASI / "smoke") if smoke else BURASI
    d = json.loads((outdir / f"sonuc_{run}{ek_ad}.json").read_text())
    defter = json.loads((outdir / f"islemler_tam_{run}{ek_ad}.json").read_text())

    perf = d.get("performans") or {}
    islem = d.get("islem") or {}
    # genel maliyet modeli DOKUNULMADI kanıtı: şasinin kendi kaydı 5.0 kalmalı (bu kartın
    # enjeksiyonu goal'e DEĞMEZ — edg040'ın tersine; değişmişse yüzey karışmış demektir, DUR)
    kayitli_bps = ((d.get("replay") or {}).get("cost_model") or {}).get("slippage_bps")
    if kayitli_bps != 5.0:
        raise AssertionError(
            f"GENEL MALİYET MODELİ DEĞİŞMİŞ: cost_model.slippage_bps={kayitli_bps} beklenen=5.0 "
            f"— bu kartın enjeksiyonu goal'e değmemeliydi, yüzey karışmış — DUR")

    oz = oz_sinama(kayit, ek)
    (outdir / f"oz_sinama_{run}{ek_ad}.json").write_text(
        json.dumps(oz, ensure_ascii=False, indent=1), encoding="utf-8")
    # HAM yakalama da diske: teşhis yeniden-koşum istemesin (edg040 dersi)
    (outdir / f"yakalama_{run}{ek_ad}.json").write_text(
        json.dumps(kayit, ensure_ascii=False), encoding="utf-8")

    # PF tam defterden (EDG-037 tanımı; donmuş edg032b defterinde 1,1119 doğrulandı — edg040)
    poz = sum(float(t["pnl_dollars"]) for t in defter if float(t["pnl_dollars"]) > 0)
    neg = sum(float(t["pnl_dollars"]) for t in defter if float(t["pnl_dollars"]) < 0)
    pf = round(poz / abs(neg), 4) if neg < 0 else None
    pf_neden = None if neg < 0 else "kayıp bacağı boş (Σpnl<0 yok) — PF payda sıfır, TANIMSIZ"

    exit_dist = islem.get("exit_reason_dagilim") or {}
    ozet = {
        "kosum": run, "stop_ek_slip_bps": float(ek_bps), "smoke": smoke,
        "hucre_sasi": d.get("hucre"),
        "islem_n": islem.get("n"),
        "net_pnl_trades": perf.get("net_pnl_trades"),     # KANONİK (islem.net_pnl YOK — bilinen tuzak)
        "net_pnl_equity": perf.get("net_pnl_equity"),
        "pf": pf, "pf_olculemedi_nedeni": pf_neden,
        "maxdd_kanonik": perf.get("maxdd_kanonik"), "maxdd_m2m": perf.get("maxdd_m2m"),
        "sharpe": perf.get("sharpe"), "sharpe_measurable": perf.get("sharpe_measurable"),
        "avg_r": perf.get("avg_r"), "win_rate": perf.get("win_rate"),
        "total_return": perf.get("total_return"),
        "exit_reason_dagilim": exit_dist,
        "stop_kirilimi": {
            "stop_n": exit_dist.get("stop"), "stop_gap_n": exit_dist.get("stop_gap"),
            "trail_kunyesi": oz["trail_kunyesi"]},
        "stop_r_dagilim": oz["stop_r_dagilim"],
        "stop_r_dagilim_trail": oz["stop_r_dagilim_trail"],
        "stop_r_dagilim_hard": oz["stop_r_dagilim_hard"],
        "butunluk_gecerli": (d.get("butunluk") or {}).get("gecerli"),
        "kill3_sasi_mtime_temiz": (d.get("kill3_mtime") or {}).get("temiz"),
        "oz_sinama_kill2_gecti": oz["kill2_gecti"],
        "oz_sinama_kill2_olculemedi": oz["kill2_olculemedi_nedeni"],
        "sizinti_yok_kill3": oz["kill3_sizinti_yok"],
        "hucre_motor_sha_once": m_once, "hucre_motor_sha_sonra": m_sonra,
        "hucre_motor_ayni_kill4": hucre_motor_ayni,
        "hucre_motor_kunye_esit_edg032c": hucre_motor_kunye_esit,
        "cost_model_kaydi": (d.get("replay") or {}).get("cost_model"),
    }
    (outdir / f"hucre_{run}{ek_ad}.json").write_text(
        json.dumps(ozet, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [{run}{ek_ad}] ek={ek_bps}bps n={ozet['islem_n']} net={ozet['net_pnl_trades']} "
          f"pf={pf} dd={ozet['maxdd_kanonik']} stop_n={exit_dist.get('stop')} "
          f"gap_n={exit_dist.get('stop_gap')} kill2={oz['kill2_gecti']} "
          f"sizinti_yok={oz['kill3_sizinti_yok']} bütünlük={ozet['butunluk_gecerli']} "
          f"motor_ayni={hucre_motor_ayni} kunye_esit={hucre_motor_kunye_esit}")
    return ozet


def sasi_kontrolu(ref, smoke: bool) -> dict:
    """kill#1 (YENİDEN-ÇAPALANMIŞ): kontrol@0 koşumu edg032c'nin KANONİK defterleriyle
    (kosum1/; smoke: kosum1_smoke/) BAYT-ÖZDEŞ mi (sha256)?

    Referansın ozdeslik() kapısı (032-cmb kıyası) BİLEREK ÇAĞRILMAZ: o kapı ESKİ dünyanın
    kimlik kapısıydı; edg032c tabanı da aynı gerekçeyle onu çağırmadan determinizm çift
    kapısıyla donduruldu (TABAN_KUNYESI.json). Onunla birlikte edg040'ın DARALTILMIŞ
    n_endeks_satir istisnası da düştü — burada istisna YOK: üç defter dosyası bayt-özdeş
    değilse kill#1 DÜŞER. (`ref` parametresi imza uyumu için duruyor; artık kullanılmıyor.)"""
    ek = "_smoke" if smoke else ""
    yerel_dir = (BURASI / "smoke") if smoke else BURASI
    ref_dir = TABAN_DIR_SMOKE if smoke else TABAN_DIR
    ciftler = {
        "islemler_tam": (yerel_dir / f"islemler_tam_kontrol{ek}.json",
                         ref_dir / f"islemler_tam_kontrol{ek}.json"),
        "islemler_slim": (yerel_dir / f"islemler_kontrol{ek}.json",
                          ref_dir / f"islemler_kontrol{ek}.json"),
        "seanslar": (yerel_dir / f"seanslar_kontrol{ek}.json",
                     ref_dir / f"seanslar_kontrol{ek}.json"),
    }
    sonuc = {}
    for ad, (y, r) in ciftler.items():
        sy, sr = _sha_full(y), _sha_full(r)
        sonuc[ad] = {"yerel_sha256": sy, "edg032c_sha256": sr,
                     "bayt_ozdes": (sy is not None and sy == sr),
                     "olculemedi_nedeni": (None if (sy and sr) else
                                           f"dosya okunamadı: yerel={bool(sy)} ref={bool(sr)}")}
    gecti = all(v["bayt_ozdes"] for v in sonuc.values())

    out = {"taban": str(ref_dir), "bayt_kiyas_edg032c": sonuc, "kill1_bayt_gecti": gecti,
           "referans_ozdeslik_032cmb": {
               "kostu": False,
               "neden": ("BİLEREK ÇAĞRILMADI — 032-cmb kapısı ESKİ dünyanın kimlik kapısıydı; "
                         "yeniden-çapalama (kart bloğu sasi_capasi_guncellemesi_2026_08_22) "
                         "sonrası kill#1 kimliği edg032c defter bayt-özdeşliğidir. edg032c "
                         "künyesi de aynı gerekçeyle bu kapıyı çağırmadan determinizm "
                         "çift-kapısıyla donduruldu. n_endeks_satir istisnası da onunla "
                         "birlikte düştü — bu kıyasta istisna YOK.")},
           "kill1_gecti": bool(gecti)}
    (yerel_dir / f"sasi_kontrolu{ek}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  ŞASİ KAPISI{ek} (taban=edg032c/kosum1{ek}): bayt={gecti} → "
          f"{'GEÇTİ' if out['kill1_gecti'] else 'DÜŞTÜ — ölçüm DURUR'}")
    return out


def delta_pnl_ci(taban_defter: list, hucre_defter: list, aylar: list[str]) -> dict:
    """EŞLENİK ay-kümeli bootstrap (edg035 yöntemi, exe006 O3 biçimi; edg040 kodu AYNEN):
    birim = AY, iki kol AYNI ayı görür, B=5000, seed=20260812, yüzdelik CI."""
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
    rng = np.random.default_rng(BOOT_SEED)
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
            "yontem": ("EŞLENİK ay-kümeli bootstrap · yeniden örneklenen birim = AY "
                       "(iki kol AYNI ayı görür) · B=5000 · seed=20260812 · yüzdelik")}


def main() -> int:
    smoke = "--smoke" in sys.argv
    ek_ad = "_smoke" if smoke else ""
    motor_once = motor_sha()
    # YENİDEN-ÇAPALAMA (d): dünya kimliği — motor DÖRT dosyada edg032c künyesiyle birebir
    # eşleşmeli; eşleşmiyorsa ölçüm BAŞLAMADAN durur (ilk koşumun kill#1 dersi).
    if motor_once != TABAN_MOTOR_SHA:
        fark = {f: {"simdi": motor_once.get(f), "kunye": TABAN_MOTOR_SHA.get(f)}
                for f in TABAN_MOTOR_SHA if motor_once.get(f) != TABAN_MOTOR_SHA.get(f)}
        raise AssertionError(
            f"MOTOR, edg032c TABAN KÜNYESİNDEN FARKLI — ölçüm BAŞLAMADAN DURUR "
            f"(dünya kimliği; TABAN_KUNYESI.json motor_sha256). Farklar: {fark}")
    civiler = kaynak_civisi_kontrol()      # yüzey değişmişse burada DURUR (assert)
    ref = referans_modul()
    print(f"referans şasi yüklendi · SANDBOX={ref.SANDBOX} (edg032b dizinine YAZILMAZ) · "
          f"ARMED_BEKLENEN→B1 uyarlandı · motor künyesi edg032c ile birebir")

    rapor: dict = {
        "kart": "EDG-2026-045", "smoke": smoke,
        "kosum_no": 2,
        "taban": "edg032c_taban_2026-08-22 (Rol-1 yeniden-çapalama; kart bloğu "
                 "sasi_capasi_guncellemesi_2026_08_22; künye TABAN_KUNYESI.json)",
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "motor_sha256_once": motor_once,
        "motor_kunye_esit_edg032c": True,   # yukarıdaki kapıdan geçildi (dört dosya birebir)
        "armed_uyarlama": ref._edg045_armed_uyarlama,
        "kaynak_civileri": civiler,
        "enjeksiyon_beyani": ("PaperBroker.close_position süreç-içi sarmal: reason=='stop' "
                              "(kademe-2, broker.py:692) iken raw_exit → raw_exit×(1−ek_slip); "
                              "stop_gap (kademe-1, broker.py:687) ve diğer TÜM reason'lar "
                              "DEĞİŞMEDEN geçer. Genel 5bps modeli (broker.py:765) DOKUNULMADI "
                              "— cost_model.slippage_bps==5.0 her koşumda assert'li."),
    }

    # [1]+[2] KONTROL@0 (sarmalayıcı AÇIK — nötrlük de sınanır) → ŞASİ KAPISI (kill#1)
    kontrol = hucre_kos(ref, "kontrol", TABAN_EK_BPS, smoke)
    rapor["kontrol_ek0"] = kontrol
    sk = sasi_kontrolu(ref, smoke)
    rapor["sasi_kontrolu"] = sk
    if not sk["kill1_gecti"]:
        rapor["DURDU"] = "kill#1: kontrol@0 edg032c/kosum1 ile bayt-özdeş DEĞİL — hücre koşulmadı"
        (BURASI / f"sonuc_grid{ek_ad}.json").write_text(
            json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
        print("KILL#1 DÜŞTÜ — ölçüm DURDU (hücre koşulmadı); şasi teşhisi Rol-1'e")
        return 2

    outdir = (BURASI / "smoke") if smoke else BURASI
    # TABAN = edg032c'nin KANONİK defteri (görev [4]); yerel kontrol onunla bayt-özdeş (kill#1)
    taban_yol = (TABAN_DIR_SMOKE if smoke else TABAN_DIR) / f"islemler_tam_kontrol{ek_ad}.json"
    taban_defter = json.loads(taban_yol.read_text())
    # taban PF — AYNI EDG-037 tanımıyla taban defterinden (betimleyici; kıyas bağlamı için)
    t_poz = sum(float(t["pnl_dollars"]) for t in taban_defter if float(t["pnl_dollars"]) > 0)
    t_neg = sum(float(t["pnl_dollars"]) for t in taban_defter if float(t["pnl_dollars"]) < 0)
    rapor["taban_ozeti_betimleyici"] = {
        "islem_n": len(taban_defter),
        "defter_pnl_toplami": round(t_poz + t_neg, 2),
        "pf": (round(t_poz / abs(t_neg), 4) if t_neg < 0 else None),
        "pf_olculemedi_nedeni": (None if t_neg < 0 else
                                 "kayıp bacağı boş (Σpnl<0 yok) — PF payda sıfır, TANIMSIZ"),
        "kaynak": str(taban_yol),
        "not": "kanonik taban performansı TABAN_KUNYESI.json + kosum1/sonuc_kontrol.json'dadır"}
    seanslar = json.loads((outdir / f"seanslar_kontrol{ek_ad}.json").read_text())
    aylar = sorted({str(r["date"])[:7] for r in seanslar})

    # [3]+[4] hücreler (smoke'ta yalnız stopslip10 — Ö1 hücresi, kablo; tamda üçü de)
    bps_liste = [10.0] if smoke else HUCRE_EK_BPS
    hucreler = {}
    delta = {}
    for bps in bps_liste:
        run = f"stopslip{int(bps)}"
        h = hucre_kos(ref, run, bps, smoke)
        hucreler[run] = h
        if not smoke:
            if not h["oz_sinama_kill2_gecti"]:
                rapor["DURDU"] = f"kill#2: {run} öz-sınaması düştü — sonraki hücre koşulmadı"
            elif not h["sizinti_yok_kill3"]:
                rapor["DURDU"] = f"kill#3: {run} stop_gap/diğer kanala SIZINTI — hücre geçersiz, DUR"
            elif not (h["hucre_motor_ayni_kill4"] and h["hucre_motor_kunye_esit_edg032c"]):
                rapor["DURDU"] = (f"kill#4: {run} motor sha koşum içinde değişti ya da edg032c "
                                  f"künyesinden saptı — hücre geçersiz, DUR")
            if "DURDU" in rapor:
                rapor["hucreler"] = hucreler
                (BURASI / f"sonuc_grid{ek_ad}.json").write_text(
                    json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"KILL DÜŞTÜ ({run}) — ölçüm DURDU: {rapor['DURDU']}")
                return 2
        hd = json.loads((outdir / f"islemler_tam_{run}{ek_ad}.json").read_text())
        delta[run] = delta_pnl_ci(taban_defter, hd, aylar)
        print(f"  Δ[{run}]: {delta[run]['delta_pnl']} CI95={delta[run]['ci95']} "
              f"({delta[run]['sifir_disinda']})")
    rapor["hucreler"] = hucreler
    rapor["delta_pnl_vs_donmus_taban"] = delta
    rapor["taban_kaynagi"] = f"{taban_yol} (DONMUŞ; kill#1 bayt-özdeş)"

    # [5] motor sha koşum-sonrası (küresel; hücre-başı kayıtlar hucre_*.json içinde)
    motor_sonra = motor_sha()
    rapor["motor_sha256_sonra"] = motor_sonra
    rapor["kill4_motor_ayni"] = (motor_once == motor_sonra)
    rapor["kill4_motor_kunye_esit_edg032c"] = (motor_sonra == TABAN_MOTOR_SHA)
    if motor_once != motor_sonra:
        print("KILL#4: motor sha koşum sırasında DEĞİŞTİ — ilgili hücreler geçersiz (raporda)")

    yol = BURASI / f"sonuc_grid{ek_ad}.json"
    yol.write_text(json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"yazıldı: {yol}")
    return 0


def alet_dogrulama(kayitli_kosumlar) -> dict:
    """Rol-1 talimatı [2]+[3] (2026-08-23): KAYDEDİLMİŞ koşumların yakalama dosyaları
    düzeltilmiş yeniden-kurma aletiyle DİSKTEN yeniden doğrulanır. Replay YOK — alet
    doğrulaması ölçüm değildir, K harcamaz. Çıktı: oz_sinama_{run}_duzeltilmis.json
    (orijinal oz_sinama_{run}.json kill tarihçesi olarak DOKUNULMADAN kalır)."""
    out = {}
    for run, bps in kayitli_kosumlar:
        ek = bps / 10000.0
        kayit = json.loads((BURASI / f"yakalama_{run}.json").read_text())
        oz = oz_sinama(kayit, ek)
        (BURASI / f"oz_sinama_{run}_duzeltilmis.json").write_text(
            json.dumps(oz, ensure_ascii=False, indent=1), encoding="utf-8")
        n_stop_disi = oz["n_stop_gap"] + oz["n_diger"]
        out[run] = {
            "stop_ek_slip_bps": bps,
            "kill2_gecti": oz["kill2_gecti"], "kill3_sizinti_yok": oz["kill3_sizinti_yok"],
            "S1_max_mutlak_fark": oz["S1_max_mutlak_fark"],
            "S2_defter_esit_n": oz["S2_defter_esit_n"], "n_stop": oz["n_stop"],
            "S3_eff_stop_esit_n": oz["S3_eff_stop_esit_n"],
            "Z1_defter_esit_n": oz["Z1_defter_esit_n"], "n_stop_disi": n_stop_disi,
            "stop_bozuk_n": oz["stop_bozuk_n"], "sizinti_bozuk_n": oz["sizinti_bozuk_n"]}
        print(f"  ALET DOĞRULAMA [{run}] ek={bps}bps: kill2={oz['kill2_gecti']} "
              f"sizinti_yok={oz['kill3_sizinti_yok']} S2={oz['S2_defter_esit_n']}/{oz['n_stop']} "
              f"Z1_defter={oz['Z1_defter_esit_n']}/{n_stop_disi} "
              f"(bozuk: stop={oz['stop_bozuk_n']} sizinti={oz['sizinti_bozuk_n']})")
    return out


def tamamla() -> int:
    """ROL-1 TALİMATI (2026-08-23; EDG-040 kill#2 emsali — alet GEVŞETİLMEZ, TAMAMLANIR):
    kill#3 hükmü Rol-1'de düştü (alt-sınama (ii) kartın kill#3'üne DAHİL DEĞİL; kartın
    ölçütü 505/505 temizdi). Akış: [2] kontrol@0 kayıtlı defteri düzeltilmiş aletle 505/505
    kanıtlanır · [3] stopslip5 YENİDEN KOŞULMAZ, kayıtlı defteri yeniden doğrulanır ·
    [4] stopslip10+stopslip20 koşulur (aynı kapılar) + ÜÇ hücrenin Δ+CI'sı · önceki DURDU
    grid'i arşiv kopyasıyla korunur. K muhasebesi DEĞİŞMEZ (aynı hücreler)."""
    motor_once = motor_sha()
    if motor_once != TABAN_MOTOR_SHA:
        fark = {f: {"simdi": motor_once.get(f), "kunye": TABAN_MOTOR_SHA.get(f)}
                for f in TABAN_MOTOR_SHA if motor_once.get(f) != TABAN_MOTOR_SHA.get(f)}
        raise AssertionError(
            f"MOTOR, edg032c TABAN KÜNYESİNDEN FARKLI — tamamlama BAŞLAMADAN DURUR. Farklar: {fark}")
    civiler = kaynak_civisi_kontrol()
    ref = referans_modul()
    print(f"referans şasi yüklendi · SANDBOX={ref.SANDBOX} · ARMED_BEKLENEN→B1 · "
          f"motor künyesi edg032c ile birebir · MOD=tamamla (Rol-1 2026-08-23)")

    rapor: dict = {
        "kart": "EDG-2026-045", "smoke": False, "kosum_no": "2-tamamlama",
        "taban": "edg032c_taban_2026-08-22 (künye TABAN_KUNYESI.json)",
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "rol1_talimati": ("2026-08-23: kill#3 bayrağı aletin bağ-yuvarlama kusuruydu (kartın "
                          "sızıntı ölçütü 505/505 temiz); alet düzeltildi (defter_yuvarla), "
                          "kayıtlı koşumlar diskten yeniden doğrulandı, kalan hücreler koşuldu. "
                          "K muhasebesi değişmedi. Tarihçe: DURDU_kill3_z1_defter_yenidenkurma.json"),
        "motor_sha256_once": motor_once,
        "motor_kunye_esit_edg032c": True,
        "armed_uyarlama": ref._edg045_armed_uyarlama,
        "kaynak_civileri": civiler,
    }

    # [2]+[3] kayıtlı koşumların diskten yeniden doğrulaması (K harcamaz)
    dogrulama = alet_dogrulama([("kontrol", 0.0), ("stopslip5", 5.0)])
    rapor["alet_dogrulama_kayitli"] = dogrulama
    dk = dogrulama["kontrol"]
    if not (dk["sizinti_bozuk_n"] == 0 and dk["stop_bozuk_n"] == 0):
        rapor["DURDU"] = ("alet düzeltmesi kontrol@0'ı temizlemedi (Rol-1 şartı [2]: 505/505 + "
                          "380/380) — yeniden-kurma modeli hâlâ yanlış, DUR")
    elif not (dogrulama["stopslip5"]["kill2_gecti"] and dogrulama["stopslip5"]["kill3_sizinti_yok"]):
        rapor["DURDU"] = "stopslip5 kayıtlı defteri düzeltilmiş aletle de temiz değil — DUR (Rol-1'e)"
    if "DURDU" in rapor:
        (BURASI / "sonuc_grid_tamamlama.json").write_text(
            json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"TAMAMLAMA DURDU: {rapor['DURDU']}")
        return 2

    # kill#1 — DİSKTEN bayt kıyası (kontrol@0 çıktıları yerinde; yeniden koşum YOK)
    sk = sasi_kontrolu(ref, smoke=False)
    rapor["sasi_kontrolu"] = sk
    if not sk["kill1_gecti"]:
        rapor["DURDU"] = "kill#1: diskteki kontrol@0 edg032c/kosum1 ile bayt-özdeş DEĞİL — DUR"
        (BURASI / "sonuc_grid_tamamlama.json").write_text(
            json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
        print("KILL#1 DÜŞTÜ — tamamlama DURDU")
        return 2

    # önceki hücreler diskten; stopslip5 bayrakları düzeltilmiş doğrulamayla güncellenir
    rapor["kontrol_ek0"] = json.loads((BURASI / "hucre_kontrol.json").read_text())
    h5 = json.loads((BURASI / "hucre_stopslip5.json").read_text())
    h5["oz_sinama_kill2_gecti"] = dogrulama["stopslip5"]["kill2_gecti"]
    h5["sizinti_yok_kill3"] = dogrulama["stopslip5"]["kill3_sizinti_yok"]
    h5["alet_dogrulamasi"] = ("2026-08-23: eski kill#3 bayrağı aletin defter-yeniden-kurma "
                              "bağ-yuvarlama kusuruydu; kayıtlı defter düzeltilmiş aletle "
                              "yeniden doğrulandı (yeniden KOŞULMADI — Rol-1 talimatı [3])")
    (BURASI / "hucre_stopslip5_duzeltilmis.json").write_text(
        json.dumps(h5, ensure_ascii=False, indent=1), encoding="utf-8")
    hucreler = {"stopslip5": h5}

    taban_defter = json.loads((TABAN_DIR / "islemler_tam_kontrol.json").read_text())
    seanslar = json.loads((BURASI / "seanslar_kontrol.json").read_text())
    aylar = sorted({str(r["date"])[:7] for r in seanslar})

    delta = {}
    hd5 = json.loads((BURASI / "islemler_tam_stopslip5.json").read_text())
    delta["stopslip5"] = delta_pnl_ci(taban_defter, hd5, aylar)
    print(f"  Δ[stopslip5]: {delta['stopslip5']['delta_pnl']} CI95={delta['stopslip5']['ci95']} "
          f"({delta['stopslip5']['sifir_disinda']})")

    # [4] kalan iki hücre — kapılar AYNEN (kill#2/3/4 zinciri)
    for bps in (10.0, 20.0):
        run = f"stopslip{int(bps)}"
        h = hucre_kos(ref, run, bps, smoke=False)
        hucreler[run] = h
        if not h["oz_sinama_kill2_gecti"]:
            rapor["DURDU"] = f"kill#2: {run} öz-sınaması düştü — sonraki hücre koşulmadı"
        elif not h["sizinti_yok_kill3"]:
            rapor["DURDU"] = f"kill#3: {run} stop_gap/diğer kanala SIZINTI — hücre geçersiz, DUR"
        elif not (h["hucre_motor_ayni_kill4"] and h["hucre_motor_kunye_esit_edg032c"]):
            rapor["DURDU"] = (f"kill#4: {run} motor sha koşum içinde değişti ya da edg032c "
                              f"künyesinden saptı — hücre geçersiz, DUR")
        if "DURDU" in rapor:
            rapor["hucreler"] = hucreler
            (BURASI / "sonuc_grid_tamamlama.json").write_text(
                json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"KILL DÜŞTÜ ({run}) — tamamlama DURDU: {rapor['DURDU']}")
            return 2
        hd = json.loads((BURASI / f"islemler_tam_{run}.json").read_text())
        delta[run] = delta_pnl_ci(taban_defter, hd, aylar)
        print(f"  Δ[{run}]: {delta[run]['delta_pnl']} CI95={delta[run]['ci95']} "
              f"({delta[run]['sifir_disinda']})")

    rapor["hucreler"] = hucreler
    rapor["delta_pnl_vs_donmus_taban"] = delta
    rapor["taban_kaynagi"] = f"{TABAN_DIR / 'islemler_tam_kontrol.json'} (DONMUŞ; kill#1 bayt-özdeş)"

    motor_sonra = motor_sha()
    rapor["motor_sha256_sonra"] = motor_sonra
    rapor["kill4_motor_ayni"] = (motor_once == motor_sonra)
    rapor["kill4_motor_kunye_esit_edg032c"] = (motor_sonra == TABAN_MOTOR_SHA)
    if motor_once != motor_sonra:
        print("KILL#4: motor sha koşum sırasında DEĞİŞTİ — ilgili hücreler geçersiz (raporda)")

    # önceki DURDU'lu grid TARİHÇE olarak korunur (kopya); tam grid kanonik ada yazılır
    eski = BURASI / "sonuc_grid.json"
    arsiv = BURASI / "sonuc_grid_kill3_durdu_arsiv.json"
    if eski.exists() and not arsiv.exists():
        arsiv.write_bytes(eski.read_bytes())
    eski.write_text(json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"yazıldı: {eski} (önceki DURDU grid arşivi: {arsiv.name})")
    return 0


if __name__ == "__main__":
    if "--tamamla" in sys.argv:
        raise SystemExit(tamamla())
    raise SystemExit(main())
