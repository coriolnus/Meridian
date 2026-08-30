"""EXE-2026-009 · pencere ALT-BANT raporu + öneri tetiği (EDG-042 haftalık koşumun HAKEM katmanı).

Kart: research/cards/EXE-2026-009-pencere-kaydirma.yaml (DONUK — bu modül karta dokunmaz, hüküm
işlemez; öneri tetiğinin SONUCUNU beyan eder, geri alma OTOMATİK DEĞİL, operatör kararıdır).

MİMARİ (görev [3] "hangisi mimariye uyuyorsa ÖLÇ ve gerekçele" — ölçülen gerekçe):
  * EDG-042'nin reçetesi DONUKTUR (kart status notu: canli_cek.py sha 4c6b85a5…, olcum.py sha
    6d33a58c…; KOMUT.txt [0] bu shaları kayda geçirir). olcum.py'ye dokunmak reçete-sha'sını
    kırardı; "betiğin çağırdığı rapor katmanı" diye bir katman da YOK — olcum.py sonuc.json'u
    kendisi yazar ve satır dökümünde `pencere` alanı taşımaz. Kalan tek dürüst yol: AYRI çekim
    (pencere_cek.py) + AYRI rapor modülü (bu dosya), 042 koşumunun YANINDA koşan bağımsız katman.
  * Ortak biçim ikiz-değer üretmeden alınır: `yuzdelik` 042'nin DONUK betiğinden İTHAL edilir
    (kopya değil — kopya sürüklenirdi); bootstrap deseni 042 `betimleyici` ile özdeş
    (B=5000, seed=20260812, kümeleme birimi=SEANS, yüzdelik CI) ve sabitleri burada DONUKTUR.

HAKEM KURALI (karttan BİREBİR, DONUK — değişirse kart kill#2 tetiklenir):
  * 042-K1 satır filtresi aynen: motor=="ayna" ∧ karar=="submitted" ∧ fill dolu; ölçü E2'de
    KAYITLI `fill_vs_resmi_acilis_bps` (payda yeniden türetilmez; boş → olculemedi kovası).
  * Bantlar `pencere` damgasından: "1330" · "1345". Damgasız satır (kaydırma-öncesi kayıt)
    AYRI sayılır, kıyasa GİRMEZ — geriye dönük etiketleme YASAK (kart kill#3).
  * Alt-bant n<10 → o bantta CI/kıyas YAPILMAZ; sonuç "orneklem_birikimde".
  * İki bant da n≥10 → medyanın seans-kümeli bootstrap CI95'i; 1345 CI'ı 1330 CI'ından YÜKSEK
    yönde AYRIK (alt_1345 > ust_1330, kesişim yok) → "geri_al_onerisi" (operatöre düşer);
    değilse "tetiklenmedi". Sonuç HER koşumda beyan edilir (kartın success_metric'i).

KOŞUM (haftalık 042 koşumunun ardından, aynı dizinde):
    [A] pencere_cek.py ile pencere_ham.json çekilir (ssh-stdin — başlığındaki komut)
    [B] python3 pencere_altbant.py            → pencere_altbant.json + stdout özeti
OKUYUCU (YASA 6): haftalık koşum çıktısı (pencere_altbant.json) + operatör raporu (Rol-1 işler).
UYDURMA YASAĞI: ölçülemeyen kalem None + neden."""
import json
import random
import statistics as st
import sys
from pathlib import Path

DIZIN = Path(__file__).resolve().parent
HAM = DIZIN / "pencere_ham.json"

# ── DONUK SABİTLER (öneri tetiği eşiği ölçüm başladıktan sonra DEĞİŞEMEZ — kart kill#2) ────────
ALT_BANT_N_ESIK = 10          # hakem_kurali: "Alt-bant n<10 iken kıyas yapılmaz"
B, SEED = 5000, 20260812      # 042 reçetesiyle özdeş bootstrap künyesi
BANTLAR = ("1330", "1345")

# `yuzdelik` 042'nin DONUK betiğinden ithal — aynı formülün ikinci bir kopyası yazılmaz
# (EQUIVALENT_TRUTHS sınıfı: iki kopya sessizce ayrışır, hakem iki gerçekle kalırdı).
#
# KAYNAKTAN DERLENİR (2026-08-30). Eski `exec_module` yolu `__pycache__`e bakardı ve zaman
# damgalı pyc'nin geçerlilik kontrolü YALNIZ (tam-saniye mtime, bayt boyutu) çiftidir: boyutu
# değiştirmeyen bir düzenleme aynı saniyede kalırsa BAYAT bytecode koşar. Sonuç, bu satırın
# üstündeki gerekçenin TAM TERSİ olurdu — "tek kopya" diye ithal edilen `yuzdelik`, sessizce
# ESKİ bir sürümden gelirdi ve ayrışma tam da engellemek istediğimiz yerde doğardı.
# Gerekçe + ölçüm: `ops/sasi_yukleyici.py` başlığı · kapı: tests/test_bayat_bytecode_v334.py §C.
#
# `sys.path` eki ZORUNLU: bu betik DOĞRUDAN koşulur, o zaman `sys.path[0]` BU dizindir ve `ops.`
# ön eki editable-install `.pth`i üzerinden BAŞKA BİR CHECKOUT'a düşer (ops/replay_sweep.py'de
# ölçüldü: worktree'den `ModuleNotFoundError`, ana checkout'ta sessizce ORANIN kopyası).
if str(DIZIN.parents[2]) not in sys.path:
    sys.path.insert(0, str(DIZIN.parents[2]))
from ops.sasi_yukleyici import kaynaktan_yukle                                    # noqa: E402

_olcum = kaynaktan_yukle(DIZIN / "olcum.py", "edg042_olcum_donuk")
yuzdelik = _olcum.yuzdelik


def _medyan_ci(satirlar: list) -> dict:
    """Seans-kümeli yüzdelik bootstrap CI95 (042 `betimleyici` bloğuyla özdeş desen; birim=SEANS)."""
    seanslar: dict = {}
    for r in satirlar:
        seanslar.setdefault(r["tarih"], []).append(r["bps"])
    rng = random.Random(SEED)
    kume = list(seanslar.values())
    medyanlar = []
    for _ in range(B):
        secim = [x for _ in kume for x in kume[rng.randrange(len(kume))]]
        medyanlar.append(st.median(secim))
    medyanlar.sort()
    return {"alt": yuzdelik(medyanlar, 0.025), "ust": yuzdelik(medyanlar, 0.975),
            "B": B, "seed": SEED, "kumeleme": "seans"}


def bant_ozeti(satirlar: list) -> dict:
    """Tek alt-bandın betimleyicisi. `satirlar`: [{ticker, tarih, bps}] — bps hepsinde dolu.

    n < ALT_BANT_N_ESIK → CI YOK, damga "örneklem-birikimde" (hakem kuralı; CI'sız betimleyici
    sayılar yine raporlanır — birikimin kendisi görünür olsun)."""
    n = len(satirlar)
    if n == 0:
        return {"n": 0, "seans_sayisi": 0, "ci": None, "medyan_bps": None,
                "p25_bps": None, "p75_bps": None, "min_bps": None, "maks_bps": None,
                "damga": f"örneklem-birikimde (n=0 < {ALT_BANT_N_ESIK}) — kıyas yapılmaz"}
    bps = sorted(r["bps"] for r in satirlar)
    n_seans = len({r["tarih"] for r in satirlar})
    esik_dolu = n >= ALT_BANT_N_ESIK
    return {"n": n, "seans_sayisi": n_seans,
            "ci": (_medyan_ci(satirlar) if esik_dolu else None),
            "medyan_bps": round(st.median(bps), 3),
            "p25_bps": yuzdelik(bps, 0.25), "p75_bps": yuzdelik(bps, 0.75),
            "min_bps": bps[0], "maks_bps": bps[-1],
            "damga": (f"n={n}, seans={n_seans} — eşik dolu; CI hesaplandı (hüküm DEĞİL, "
                      f"öneri-tetiği girdisi)" if esik_dolu else
                      f"örneklem-birikimde (n={n} < {ALT_BANT_N_ESIK}) — kıyas yapılmaz")}


def oneri_tetigi(b1330: dict, b1345: dict) -> dict:
    """Kartın DONUK öneri tetiği — üç dal, her koşumda beyanlı sonuç (success_metric).

    Karar kuralı UYGULANIR ama HÜKÜM İŞLENMEZ: "geri_al_onerisi" bir operatör önerisidir."""
    if b1330["ci"] is None or b1345["ci"] is None:
        eksik = [ad for ad, b in (("1330", b1330), ("1345", b1345)) if b["ci"] is None]
        return {"sonuc": "orneklem_birikimde",
                "beyan": (f"örneklem-birikimde: alt-bant(lar) {'+'.join(eksik)} eşik altında "
                          f"(n<{ALT_BANT_N_ESIK}) — hakem kuralı gereği kıyas YAPILMADI; "
                          f"birikim sürüyor, sonraki koşumda yeniden değerlendirilir")}
    ayrik_kotu = b1345["ci"]["alt"] > b1330["ci"]["ust"]     # 1345 YÜKSEK yönde ayrık = kötüleşme
    if ayrik_kotu:
        return {"sonuc": "geri_al_onerisi",
                "ci_1330": b1330["ci"], "ci_1345": b1345["ci"],
                "beyan": ("GERİ-AL ÖNERİSİ (operatöre): 1345 alt-bandının medyan CI'ı "
                          f"[{b1345['ci']['alt']}, {b1345['ci']['ust']}] bps, 1330'unkinden "
                          f"[{b1330['ci']['alt']}, {b1330['ci']['ust']}] YÜKSEK yönde AYRIK — "
                          "kaydırma sonrası friksiyon anlamlı kötüleşti. Geri alma otomatik "
                          "DEĞİL; karar operatörde (kart hakem_kurali)")}
    return {"sonuc": "tetiklenmedi",
            "ci_1330": b1330["ci"], "ci_1345": b1345["ci"],
            "beyan": ("tetiklenmedi: iki alt-bandın medyan CI'ları yüksek yönde ayrık değil — "
                      "geri-al önerisi koşulu oluşmadı; kaydırma yürürlükte kalır")}


def altbant_raporu(e2_satirlar: list, yururluk_rejimi: str | None = None) -> dict:
    """E2 satırlarından tam alt-bant raporu: 042-K1 filtresi → bantlama → betimleyici → tetik."""
    ayna_fill = [r for r in e2_satirlar
                 if r.get("motor") == "ayna" and r.get("karar") == "submitted"
                 and r.get("fill") is not None]
    bant_olcum: dict = {b: [] for b in BANTLAR}
    damgasiz, olculemedi, bant_disi = [], [], []
    for r in ayna_fill:
        v = r.get("fill_vs_resmi_acilis_bps")
        kayit = {"ticker": r.get("ticker"), "tarih": r.get("date"), "plan_id": r.get("plan_id")}
        if v is None:                        # 042 kill#2 aynen: tahmin YOK, ikame YOK
            olculemedi.append({**kayit, "neden": "fill dolu ama fill_vs_resmi_acilis_bps boş — "
                                                 "payda yeniden türetilmez (042 kill#1/#2)"})
            continue
        p = r.get("pencere")
        if p is None:
            damgasiz.append(kayit)           # kaydırma-öncesi kayıt: damgasız KALIR (kill#3)
        elif p in BANTLAR:
            bant_olcum[p].append({**kayit, "bps": float(v)})
        else:                                # bilinmeyen damga: kıyasa sokulmaz, adıyla raporlanır
            bant_disi.append({**kayit, "pencere": p})
    bantlar = {b: bant_ozeti(bant_olcum[b]) for b in BANTLAR}
    return {"kart": "EXE-2026-009", "hakem": "EDG-2026-042 K1 alt-bant katmani",
            "yururluk_rejimi": yururluk_rejimi,
            "bantlar": bantlar,
            "oneri_tetigi": oneri_tetigi(bantlar["1330"], bantlar["1345"]),
            "damgasiz": {"n": len(damgasiz), "satirlar": damgasiz,
                         "not": "kaydırma-öncesi dolumlar — geriye dönük etiketlenMEZ (kill#3), "
                                "kıyasa girmez"},
            "bant_disi": {"n": len(bant_disi), "satirlar": bant_disi},
            "olculemedi": {"n": len(olculemedi), "satirlar": olculemedi},
            "donuk_kunye": {"alt_bant_n_esik": ALT_BANT_N_ESIK, "B": B, "seed": SEED,
                            "kumeleme": "seans",
                            "kural": "alt_1345 > ust_1330 (kesişimsiz, yüksek yön) → geri-al önerisi"}}


def main():
    if not HAM.exists():
        # UYDURMA YASAĞI: çekim yoksa rapor üretilmez — "ölçülemedi + neden" beyanla çıkılır
        print(json.dumps({"olculemedi": True,
                          "neden": f"{HAM.name} yok — önce pencere_cek.py çekimi (başlıktaki "
                                   f"ssh-stdin komutu) koşulmalı"}, ensure_ascii=False))
        raise SystemExit(2)
    ham = json.loads(HAM.read_text())
    e2 = (ham.get("entry_execution") or {})
    satirlar = e2.get("satirlar")
    if satirlar is None:
        print(json.dumps({"olculemedi": True,
                          "neden": e2.get("_hata") or "entry_execution çekilemedi"},
                         ensure_ascii=False))
        raise SystemExit(2)
    out = {"cekim_kunyesi": {"dosya": HAM.name, "cekim_zamani": ham.get("cekim_zamani"),
                             "makine": ham.get("makine")},
           **altbant_raporu(satirlar, yururluk_rejimi=ham.get("yururluk_rejimi"))}
    (DIZIN / "pencere_altbant.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"yazildi": "pencere_altbant.json",
                      "n_1330": out["bantlar"]["1330"]["n"],
                      "n_1345": out["bantlar"]["1345"]["n"],
                      "damgasiz": out["damgasiz"]["n"],
                      "oneri_tetigi": out["oneri_tetigi"]["sonuc"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
