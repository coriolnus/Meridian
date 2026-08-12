"""sonuclandir.py — EDG-2026-025 üç bacağı sonuc.json'da birleştirir + kartın üç silahlanma
ölçütünün MEKANİK durumunu üretir. HÜKÜM VERMEZ: statüler kart success_metric'in düz okumasıdır,
silahlanma/karta-işleme Rol-1'in; (iii)'ün "açıklıyor mu" hükmü de Rol-1'in (burada yalnız bulgu).
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib

import olcum_edg025 as o

BURASI = pathlib.Path(__file__).resolve().parent


BELGESEL_C = {
    "soru": "EDG-2026-019 kuru-koşumunun −0.114R'si NEREDEN geldi; (a)/(b) ile neden ayrışıyor?",
    "kaynak_zinciri": [
        {"kaynak": "research/cards/EDG-2026-025-momentum-burst-karne.yaml:4-5,14",
         "icerik": "−0.114R = 'skill-görüş defterinin İLK KURU-KOŞUMU' (EDG-2026-019 dry-run, "
                   "kalibrasyonsuz); 'canlı gorusleri.jsonl o gün 0 satırdı'"},
        {"kaynak": "ROADMAP.md:891-894 (aynısı 2133-2139, N2b bloğu)",
         "icerik": "v218 kodu indi; 'CANLI KANIT KURU-KOŞU: terfi/emeklilik R-figürleri (vcp "
                   "+0,116R / momentum-burst −0,114R) canlı state'te yeniden-üretilemedi "
                   "(eksen2.uretilen=0, gorusleri.jsonl beslenmedi, kadans koşmadı)'"},
        {"kaynak": "docs/SABAH-TRIYAJI-2026-08-09.md:114-118, 130-132",
         "icerik": "'promptta anılan figürler ... canlı state'te YENİDEN-ÜRETİLEMEDİ'; canlıda "
                   "eşik-aşan tek skill pullback-screener (n_cf=21, cf_avg_r=−0,968) — mb DEĞİL; "
                   "'EDG-2026-019 ölçüm kodu yazılmadan bu R-figürleri doğrulanamaz ... "
                   "uydurmuyorum: ölçülemedi'"},
        {"kaynak": "docs/KESIF-WP-MKP-2026-08-09.md:159-161",
         "icerik": "kart registered, ölçüm kodu HENÜZ YAZILMADI; R-figürleri canlıda "
                   "YENİDEN-ÜRETİLEMEDİ (eksen2.uretilen=0)"},
        {"kaynak": "meridian/skill_gorus.py:517-533 (v218)",
         "icerik": "'emeklilik_isareti' mekanizması gerçekten v218'de var (iki yönlü kesim) — "
                   "−0.114'ün SÖZCÜK DAĞARI buradan; ama işaret üretmek için görüş DEFTERİ satırı "
                   "gerekir ve canlı defter o gün 0 satırdı"},
        {"kaynak": "artefakt taraması (bu tur)",
         "icerik": "research/ altında EDG-019 ölçüm/kuru-koşum çıktısı YOK (find '*gorus*' → yalnız "
                   "kart + modül + test); yerel state'te skill_gorusleri.jsonl YOK; −0.114'ü üreten "
                   "hesap hiçbir artefakta yazılmamış"},
        {"kaynak": "meridian/strategy.py:995-1000 (tarihsel bağlam)",
         "icerik": "mb'nin dormant kalışının ORİJİNAL ölçümü BAŞKA bir metrik: tam-replay BİLEŞİK "
                   "SKOR katkısı (breakout+pullback 0.281 → +mb 0.100; 'it HURTS −0.18') — o da "
                   "−0.114 değil; 'mb negatif' anlatısının üçüncü, ayrı-metrikli soyu"},
    ],
    "evren_pencere_metrik_cevabi": (
        "Hangi evren/pencere/metrik: BİLİNMİYOR-ÇÜNKÜ-KAYITSIZ. −0.114R bir defter ölçümü değil, "
        "v218 turunda PROMPT'ta anılan kalibrasyonsuz kuru-koşum figürüdür; girdisi olacak görüş "
        "defteri canlıda 0 satırdı, ölçüm kodu yazılmamıştı ve üç çağdaş doküman figürü "
        "'yeniden-üretilemedi' diye kayda geçirdi. Üreten hesabın artefaktı yok."),
    "ayrisma_aciklamasi_adiyla": [
        "(a) ile ayrışma: (a) cf defterinin tüketici-görünür 1080 mb satırının 4,5+ yıllık ortalama "
        "R'sidir (+0.0921); −0.114 ise defter-dışı, artefaktsız bir kuru-koşum değeri. AYNI ölçüm "
        "uzayında değiller — çelişki iki ölçümün çelişkisi değil, bir ölçümle bir doğrulanamayan "
        "alıntının yan yana düşmesi.",
        "İşaret-çevrimi mekanizması ADIYLA: mb cf performansı pencereye GÜÇLÜ bağımlı — 2022 "
        "−0.258 (n=172), 2025 +0.293 (n=212), son-37-giriş −0.718, 2026-H2 −1.030 (n=7). Küçük ya "
        "da yakın-pencere bir kuru-koşumun NEGATİF görmesi mekanik olarak mümkün; AMA −0.114'ün "
        "kendisi hiçbir taranan dilimden (kuyruk k=5..1080, yıl/yarıyıl/çeyrek, ±0.0005) çıkmadı — "
        "sayısal köken BAĞDAŞTIRILAMADI (uydurma yasak; en yakın: 2022-H2 −0.1327, n=63).",
        "(b) ile ayrışma: (b) motorun GERÇEK yasasıyla (slot/kapı/maliyet/çıkış şelalesi) replay'dir "
        "— kartın karar metriği budur ve kendi CI'ıyla ayakta durur; kuru-koşum figürünün bu uzayda "
        "bir karşılığı hiç üretilmedi.",
        "near_miss AÇIKLAMA DEĞİL: mb'de near_miss-entered satır 0 → N4 dışlama kuralı mb "
        "örneklemini değiştirmiyor; '−0.114 near_miss dahil evrenden geldi' hipotezi KAPALI.",
    ],
    "sinif": ("belgesel köken NET (prompt-alıntısı, defter-dışı, artefaktsız) + sayısal türetim "
              "BAĞDAŞTIRILAMADI. 'Açıklıyor mu' hükmü Rol-1'in — kill#1 cümlesi 'iki kanıt kaynağı "
              "bağdaştırılamıyorsa silahlanma YAPILMAZ' der; buradaki bulgu 'iki kanıt kaynağı yok: "
              "biri kanıt, öteki kayıtsız alıntı' şeklindedir."),
}


def olcutler(a: dict, b: dict, c_say: dict) -> dict:
    mb = b["mb_islemleri"]
    ci = mb["ci95_tarih_kumeli_cikis_gunu"]
    bil = b["bilesik_portfoy"]
    slot = b["slot_calma"]
    n_mb = mb["n"]

    kill3_gecerli = b["sasi_dogrulamasi_kill3"]["gecerli"]
    kill2 = n_mb < 30

    # (i) replay ort-R CI 0-üstünde
    if not kill3_gecerli:
        durum_i = {"durum": "olculemedi", "neden": "kill#3 — şasi taban davranışını yeniden üretemedi"}
    elif kill2:
        durum_i = {"durum": "olculemedi", "neden": f"kill#2 — mb işlem {n_mb} < 30"}
    elif ci.get("ci_low") is None:
        durum_i = {"durum": "olculemedi", "neden": ci.get("neden", "CI kurulamadı")}
    else:
        durum_i = {"durum": "gecti" if ci["ci_low"] > 0 else "dustu",
                   "deger": {"avg_r": mb["avg_r"], "ci": [ci["ci_low"], ci["ci_high"]], "n": n_mb}}

    # (ii) bileşik P&L farkı negatif değil VE diğer kurulum kârı CI ile düşmüyor
    if not kill3_gecerli or kill2:
        durum_ii = {"durum": "olculemedi", "neden": "kill#2/kill#3 (yukarıyla aynı)"}
    else:
        d_pnl = bil["delta_son_equity"]
        ci_d = slot["ci95_gun_kumeli_toplam_fark"]
        diger_ci_ile_dusuyor = (ci_d.get("ci_high") is not None and ci_d["ci_high"] < 0)
        gecti = (d_pnl is not None and d_pnl >= 0) and not diger_ci_ile_dusuyor
        durum_ii = {"durum": "gecti" if gecti else "dustu",
                    "deger": {"delta_pnl_bilesik": d_pnl,
                              "bilesik_ci": [bil["ci95_gun_kumeli_toplam_fark"].get("ci_low"),
                                             bil["ci95_gun_kumeli_toplam_fark"].get("ci_high")],
                              "diger_kurulum_delta_pnl": slot["delta_diger_pnl"],
                              "diger_ci": [ci_d.get("ci_low"), ci_d.get("ci_high")],
                              "diger_ci_ile_dusuyor": diger_ci_ile_dusuyor},
                    "okuma_beyani": ("MEKANİK okuma: ΔP&L_nokta>=0 VE diğer-kurulum ΔP&L CI-üstü<0 "
                                     "DEĞİL. 'negatif değil'in CI'lı okuması Rol-1'e bırakıldı — "
                                     "bileşik CI da raporda.")}

    # (iii) çelişki teşhisi — bulgu üretildi; hüküm Rol-1
    durum_iii = {"durum": "bulgu_uretildi_hukum_rol1",
                 "iki_katman": {
                     "belgesel_koken": "aciklandi — defter-dışı prompt-alıntısı; kaynak zinciri "
                                       "satır-atıflı (bacak_c.belgesel.kaynak_zinciri)",
                     "sayisal_turetim": "bagdastirilamadi — taranan hiçbir dilim −0.114 vermiyor "
                                        "(en yakın 2022-H2 −0.1327, n=63; tolerans ±0.0005)"},
                 "ozet": ("belgesel köken NET (defter-dışı prompt-alıntısı; 3 çağdaş doküman "
                          "'yeniden-üretilemedi'), sayısal türetim BAĞDAŞTIRILAMADI "
                          "(hiçbir dilim −0.114 vermiyor; en yakın 2022-H2 −0.1327)"),
                 "not": "kill#1 cümlesinin uygulanıp uygulanmayacağı Rol-1 kararı"}

    return {"i_replay_ci_0_ustunde": durum_i,
            "ii_bilesik_pnl_negatif_degil": durum_ii,
            "iii_celiski_teshisi": durum_iii,
            "kill2_mb_islem_30": {"tetiklendi": kill2, "n_mb": n_mb},
            "kill3_sasi": {"gecerli": kill3_gecerli,
                           "detay": b["sasi_dogrulamasi_kill3"]["determinizm_pk"]}}


def main() -> None:
    a = o.bacak_a()
    c_say = o.bacak_c_sayisal()
    b = o.bacak_b()
    sonuc = {
        "kart": "EDG-2026-025 momentum_burst kanonik karne — ÜÇ BACAK ÖLÇÜMÜ",
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "olcum_ajani_beyani": (
            "SALT-ÖLÇÜM: karta/ARMED_SETUPS'a/gerçek state'e DOKUNULMADI; git/ssh/serve.sh YOK. "
            "Replay kolları sandbox'ta koştu (MERIDIAN_ROOT yönlendirmesi; kod_damgasi.json motor "
            "bayt-eşitliği; barlar salt-okunur sembolik bağ). loop/counterfactual/cf_backfill/"
            "hermes İTHAL EDİLMEDİ (koşum-içi sys.modules tripwire her kolda 'temiz'); cf verisi "
            "DOSYADAN okundu, tüketici mantığı satır-atıfla aynalandı (N4 emsali). "
            "HÜKÜM/SİLAHLANMA YAZILMADI — Rol-1 işler."),
        "bacak_a_cf_karne": a,
        "bacak_b_replay_karne": b,
        "bacak_c_celiski_teshisi": {"belgesel": BELGESEL_C, "sayisal_tarama": c_say},
        "silahlanma_olcutleri_mekanik": olcutler(a, b, c_say),
    }
    (BURASI / "sonuc.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1))
    print("sonuc.json yazıldı")
    m = sonuc["silahlanma_olcutleri_mekanik"]
    for k in ("i_replay_ci_0_ustunde", "ii_bilesik_pnl_negatif_degil", "iii_celiski_teshisi"):
        print(k, "→", m[k]["durum"])


if __name__ == "__main__":
    main()
