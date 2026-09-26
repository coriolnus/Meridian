"""EXE-2026-009 · K1 ayrık-kol raporu + öneri tetiği — HAKEM REVİZYONU (P-2, 2026-09-01).

Kart: research/cards/EXE-2026-009-pencere-kaydirma.yaml, hüküm bloğu `p2_kapanis_2026_09_01`
(DONUK — bu modül karta dokunmaz, hüküm İŞLEMEZ; öneri tetiğinin SONUCUNU beyan eder, geri alma
OTOMATİK DEĞİL, operatör kararıdır).

NE DEĞİŞTİ VE NEDEN (kart p2_kapanis, NEDEN bloğu — burada ÖZETLENİR, yeniden GEREKÇELENDİRİLMEZ):
  BÖLME ANAHTARI `pencere` DAMGASINDAN GÖNDERİM `ts`SİNE GEÇTİ. Damga anahtarıyla kontrol kolu
  (kaydırma öncesi yol) sonsuza dek n=2'de kalırdı: `pencere="1330"` damgalı satır bir daha HİÇ
  üretilmeyecek, çünkü o icra yolu 2026-08-23'te emekli oldu. Öneri tetiği "iki kol da n>=10"
  ister — yani damga anahtarında tetik İNŞAEN erişilemezdi ve kartın success_metric'i ("her
  koşumda beyanlı sonuç") ölü doğardı. `ts` anahtarıyla damgasız 13 kaydırma-öncesi satır ve
  P-1-düzeltmeli DE/PANW kontrol koluna ÖLÇÜLEREK girer (kontrol n=15 → eşik dolu; bekleyen
  yalnız tedavi kolu). Kill#3'e (geriye dönük etiketleme yasağı) GİRMEZ: `ts` ile bölmek etiket
  YAZMAK değil, defterde ZATEN kayıtlı iki ölçülmüş olguyu karşılaştırmaktır.

DEĞİŞMEYEN — TEK KARAKTERİ DEĞİŞMEDİ (kart kill#2 buna bakar): öneri tetiği eşiği (iki kol da
  n>=ALT_BANT_N_ESIK + CI ayrıklığı), bootstrap künyesi (B=5000, seed=20260812, kümeleme=SEANS),
  042-K1 satır filtresi, E2 ikame yasağı, karar metinlerinin GÖVDESİ. Değişen: BÖLME ANAHTARI,
  kolların ADI ve karar metinlerindeki bant VOKABÜLERİ (bant adları + "alt-bant" sözcüğü).

KOL ADLARI, tek sözlük (EDG-2026-042 kartı `p3_karar_ayrik_ts_2026_08_31`): K1-önce (makine
  anahtarı `giris_once`) · K1-1345 (makine anahtarı `giris_1345`). "1330"/"1345" BANT adlandırması
  BIRAKILMIŞTIR — o adlar damga vokabülerindendi ve artık bölmüyorlar.

BÖLÜCÜ İTHAL EDİLİR, KOPYALANMAZ. `gonderim_kolu` + `PENCERE_SINIRI` P-3 reçetesinden
  (edg042_recete_ayrik_2026-08-31/olcum.py) dosya-yolu importuyla gelir. İkinci bir kopya, bu
  deponun tekrar eden "iki kopya sessizce ayrışır" sınıfıdır: sınır bir gün değişirse hakem
  reçeteden BAŞKA bir kolu ölçmeye başlar ve bunu kimse görmez. Yükleme `ops.sasi_yukleyici.
  kaynaktan_yukle` ile yapılır — ham `spec.loader.exec_module` yolu `__pycache__`e bakar ve
  BOYUT-KORUYAN bir düzenleme aynı saniyede kalırsa BAYAT bytecode koşar (ölçüm + gerekçe:
  o dosyanın başlığı; kapı: tests/test_bayat_bytecode_v334.py §C). `yuzdelik` de aynı modülden
  alınır (iki reçetede bayt-özdeş; ikinci kopya yazılmaz).

ÇAPRAZ SÜTUN — DAMGA ARTIK BÖLMEZ, DOĞRULAR: `pencere` damgası E2'ye basılmaya DEVAM eder
  (uygulama sözleşmesi değişmedi). Damgası DOLU her ölçülen satırda damganın işaret ettiği kol
  ile `ts` kolu kıyaslanır; ayrışan satır sayısı VE listesi raporlanır. Tarihli taban (kart,
  2026-08-31): damgalı 4 satırın 4'ünde iki anahtar aynı kolu gösteriyordu — ileride bir ayrışma
  doğarsa "ne zamandan sonra" sorusu buradan okunur.

KOŞUM (haftalık 042 koşumunun ardından, aynı dizinde — sıra KOMUT.txt'de):
    [A] pencere_cek.py ile pencere_ham.json çekilir (ssh-stdin — o dosyanın başlığındaki komut)
    [B] python3 pencere_altbant.py            → pencere_altbant.json + stdout özeti
OKUYUCU (YASA 6): haftalık koşum çıktısı (pencere_altbant.json) + operatör raporu (Rol-1 işler).
UYDURMA YASAĞI: ölçülemeyen kalem None + neden; "varsayılan kol" kabulü YASAK."""
import json
import random
import statistics as st
import sys
from pathlib import Path

DIZIN = Path(__file__).resolve().parent
HAM = DIZIN / "pencere_ham.json"
#: Bölücünün kaynağı. Yol BETİĞİN KENDİ konumuna göre türetilir — repo-köke bağlı mutlak yol
#: worktree'de ve cloud klonunda sessizce BAŞKA bir checkout'a düşerdi (ops/replay_sweep.py'de
#: ölçüldü). İki dizin kardeştir; birlikte taşınır, birlikte kırılırlar.
RECETE = DIZIN.parent / "edg042_recete_ayrik_2026-08-31" / "olcum.py"
#: Künyeye basılan depo-göreli yol. İÇE AKTARMA ANINDA bir kez türetilir, rapor üretilirken
#: DEĞİL: `DIZIN` bir modül globali'dir ve raporun içinden ona bakmak, çıktı dizini başka bir
#: yere çevrildiğinde (çivi, kuru koşum, taşınmış dizin) `relative_to`yu PATLATIRDI — künye
#: alanı raporun kendisini düşürürdü. Künye künyedir; ölçümün koşum yerine bağımlılığı olmaz.
BOLUCU_KAYNAGI = str(RECETE.relative_to(DIZIN.parents[2]))

# ── DONUK SABİTLER (öneri tetiği eşiği ölçüm başladıktan sonra DEĞİŞEMEZ — kart kill#2) ────────
ALT_BANT_N_ESIK = 10          # hakem_kurali: "kol n<10 iken kıyas yapılmaz"
B, SEED = 5000, 20260812      # 042 reçetesiyle özdeş bootstrap künyesi
KOLLAR = ("giris_once", "giris_1345")
#: Rapor başlıkları — makine anahtarı ile insan adı arasındaki TEK sözlük (EDG-042 p3 bloğu).
KOL_BASLIK = {"giris_once": "K1-önce", "giris_1345": "K1-1345"}
#: ÇAPRAZ SÜTUN İÇİN — VE YALNIZ ONUN İÇİN. Bu sözlük BÖLMEZ; damga vokabülerini kol
#: vokabülerine çevirir ki iki anahtar kıyaslanabilsin. Bölme TEK yerden yapılır: `gonderim_kolu`.
#: Dayanağı kartın tarihli tabanıdır (DE/PANW ts<sınır ↔ damga "1330" · ECL/CRM ts>=sınır ↔
#: damga "1345"). Sözlükte OLMAYAN damga kıyaslanamaz — ona "ayrışma" demek UYDURMA olurdu.
DAMGA_KOL = {"1330": "giris_once", "1345": "giris_1345"}

# `sys.path` eki ZORUNLU: bu betik DOĞRUDAN koşulur, o zaman `sys.path[0]` BU dizindir ve `ops.`
# ön eki editable-install `.pth`i üzerinden BAŞKA BİR CHECKOUT'a düşer (ops/replay_sweep.py'de
# ölçüldü: worktree'den `ModuleNotFoundError`, ana checkout'ta sessizce ORANIN kopyası).
if str(DIZIN.parents[2]) not in sys.path:
    sys.path.insert(0, str(DIZIN.parents[2]))
from ops.sasi_yukleyici import kaynaktan_yukle                                    # noqa: E402

_recete = kaynaktan_yukle(RECETE, "edg042_recete_ayrik_donuk")
gonderim_kolu = _recete.gonderim_kolu       # `ts` → kol | None  (İTHAL — kopya YOK)
PENCERE_SINIRI = _recete.PENCERE_SINIRI     # sınır metni de İTHAL — literal buraya YAZILMAZ
yuzdelik = _recete.yuzdelik


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


def kol_ozeti(satirlar: list) -> dict:
    """Tek kolun betimleyicisi. `satirlar`: [{ticker, tarih, bps}] — bps hepsinde dolu.

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


def oneri_tetigi(once: dict, y1345: dict) -> dict:
    """Kartın DONUK öneri tetiği — üç dal, her koşumda beyanlı sonuç (success_metric).

    EŞİK SAYISI, KARŞILAŞTIRMA YÖNÜ VE ÜÇ DALIN ANLAMI DEĞİŞMEDİ. Taşınan metinlerde değişen
    tek şey VOKABÜLERDİR: bant adları ("1330"/"1345") ve "alt-bant" sözcüğü kol vokabülerine
    çevrildi (kart p2_kapanis: "hakem raporu '1330/1345' bant adlarını bırakır"). Bu ayrımı
    bulanık bırakmak kill#2'yi ölçülemez kılardı — eşik değişmedi, ADLANDIRMA değişti.
    Karar kuralı UYGULANIR ama HÜKÜM İŞLENMEZ: "geri_al_onerisi" bir operatör önerisidir."""
    if once["ci"] is None or y1345["ci"] is None:
        eksik = [KOL_BASLIK[ad] for ad, b in zip(KOLLAR, (once, y1345)) if b["ci"] is None]
        return {"sonuc": "orneklem_birikimde",
                "beyan": (f"örneklem-birikimde: kol(lar) {'+'.join(eksik)} eşik altında "
                          f"(n<{ALT_BANT_N_ESIK}) — hakem kuralı gereği kıyas YAPILMADI; "
                          f"birikim sürüyor, sonraki koşumda yeniden değerlendirilir")}
    ayrik_kotu = y1345["ci"]["alt"] > once["ci"]["ust"]   # 1345 YÜKSEK yönde ayrık = kötüleşme
    if ayrik_kotu:
        return {"sonuc": "geri_al_onerisi",
                "ci_giris_once": once["ci"], "ci_giris_1345": y1345["ci"],
                "beyan": ("GERİ-AL ÖNERİSİ (operatöre): K1-1345 kolunun medyan CI'ı "
                          f"[{y1345['ci']['alt']}, {y1345['ci']['ust']}] bps, K1-önce'ninkinden "
                          f"[{once['ci']['alt']}, {once['ci']['ust']}] YÜKSEK yönde AYRIK — "
                          "kaydırma sonrası friksiyon anlamlı kötüleşti. Geri alma otomatik "
                          "DEĞİL; karar operatörde (kart hakem_kurali)")}
    return {"sonuc": "tetiklenmedi",
            "ci_giris_once": once["ci"], "ci_giris_1345": y1345["ci"],
            "beyan": ("tetiklenmedi: iki kolun medyan CI'ları yüksek yönde ayrık değil — "
                      "geri-al önerisi koşulu oluşmadı; kaydırma yürürlükte kalır")}


def altbant_raporu(e2_satirlar: list, yururluk_rejimi: str | None = None) -> dict:
    """E2 satırlarından tam ayrık-kol raporu: 042-K1 filtresi → `ts` bölmesi → betimleyici → tetik.

    Damga↔ts çaprazı YALNIZ kola ATANMIŞ satırlarda hesaplanır: kolu belirlenemeyen satırın
    damgasıyla kıyaslanacak bir `ts` kolu YOKTUR (kıyas paydası raporda beyanlıdır)."""
    ayna_fill = [r for r in e2_satirlar
                 if r.get("motor") == "ayna" and r.get("karar") == "submitted"
                 and r.get("fill") is not None]
    kol_olcum: dict = {k: [] for k in KOLLAR}
    olculemedi, ayrisan, damga_bilinmeyen = [], [], []
    damgasiz_n = kiyaslanan_n = 0
    for r in ayna_fill:
        v = r.get("fill_vs_resmi_acilis_bps")
        kayit = {"ticker": r.get("ticker"), "tarih": r.get("date"), "plan_id": r.get("plan_id")}
        if v is None:                        # 042 kill#2 aynen: tahmin YOK, ikame YOK
            olculemedi.append({**kayit, "neden": "fill dolu ama fill_vs_resmi_acilis_bps boş — "
                                                 "payda yeniden türetilmez (042 kill#1/#2)"})
            continue
        kol = gonderim_kolu(r.get("ts"))     # P-2/P-3: bölme anahtarı GÖNDERİM anı
        if kol is None:
            olculemedi.append({**kayit, "ts": r.get("ts"),
                               "neden": "gönderim damgası `ts` okunamadı (yok/boş/biçimsiz/saat "
                                        "dilimsiz) — kol belirlenemedi. Varsayılan kol kabulü "
                                        "YASAK (EXE-009 P-1 sınıfı); satır hiçbir kola atanmadı, "
                                        "kıyasa girmedi."})
            continue
        kol_olcum[kol].append({**kayit, "bps": float(v)})
        # ── ÇAPRAZ SÜTUN: damga BÖLMEZ, `ts` kolunu DOĞRULAR ──────────────────────────────
        p = r.get("pencere")
        if p is None:                        # kaydırma-öncesi kayıt: damgasız — AYRIŞMA DEĞİL
            damgasiz_n += 1
        elif p not in DAMGA_KOL:             # bilinmeyen damga: kıyaslanamaz, adıyla raporlanır
            damga_bilinmeyen.append({**kayit, "pencere": p})
        else:
            kiyaslanan_n += 1
            if DAMGA_KOL[p] != kol:
                ayrisan.append({**kayit, "pencere": p, "damga_kolu": DAMGA_KOL[p],
                                "ts": r.get("ts"), "ts_kolu": kol})
    kollar = {k: kol_ozeti(kol_olcum[k]) for k in KOLLAR}
    return {"kart": "EXE-2026-009", "hakem": "EDG-2026-042 K1 ayrık-kol katmani",
            "yururluk_rejimi": yururluk_rejimi,
            "bolme_anahtari": "ts (gönderim anı) — `pencere` damgası DEĞİL",
            "pencere_siniri": PENCERE_SINIRI,
            "kollar": kollar,
            "kol_basliklari": KOL_BASLIK,
            "oneri_tetigi": oneri_tetigi(kollar["giris_once"], kollar["giris_1345"]),
            "damga_ts_caprazi": {
                "kiyaslanan": kiyaslanan_n,
                "damgasiz": damgasiz_n,
                "damga_bilinmeyen": {"n": len(damga_bilinmeyen), "satirlar": damga_bilinmeyen},
                "ayrisan": {"n": len(ayrisan), "satirlar": ayrisan},
                "not": ("payda = kola ATANMIŞ ve damgası DOLU satırlar. Damgasız satır ayrışma "
                        "DEĞİLDİR (kaydırma-öncesi kayıt); bilinmeyen damga kıyaslanamaz. "
                        "Tarihli taban (kart, 2026-08-31): damgalı 4 satırın 4'ünde iki anahtar "
                        "AYNI kolu gösteriyordu — ayrışma doğarsa 'ne zamandan sonra' sorusu "
                        "buradan okunur.")},
            "olculemedi": {"n": len(olculemedi), "satirlar": olculemedi},
            "donuk_kunye": {"alt_bant_n_esik": ALT_BANT_N_ESIK, "B": B, "seed": SEED,
                            "kumeleme": "seans",
                            "kural": ("alt_giris_1345 > ust_giris_once (kesişimsiz, yüksek yön) "
                                      "→ geri-al önerisi"),
                            "bolucu_kaynagi": BOLUCU_KAYNAGI,
                            "kol_donuklugu": ("`giris_once` kolunun KALICI TABAN oluşu reçetenin "
                                              "`kalici_taban` alanında beyanlıdır (EDG-042 "
                                              "p3_karar_ayrik_ts_2026_08_31) — burada "
                                              "tekrarlanmaz (tek-kaynak yasası)")}}


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
                      "n_giris_once": out["kollar"]["giris_once"]["n"],
                      "n_giris_1345": out["kollar"]["giris_1345"]["n"],
                      "damgasiz": out["damga_ts_caprazi"]["damgasiz"],
                      "damga_ts_ayrisan": out["damga_ts_caprazi"]["ayrisan"]["n"],
                      "olculemedi": out["olculemedi"]["n"],
                      "oneri_tetigi": out["oneri_tetigi"]["sonuc"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
