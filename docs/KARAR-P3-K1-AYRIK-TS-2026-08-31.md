# KARAR — P-3: K1 karışık örneklemi AYRIK ölçülür, anahtar `ts` (2026-08-31)

**Karar veren:** operatör · **Verildiği yer:** `ai-trading-85` oturumu · **İşleyen:** Rol-1
(`ai-trading-dc`), oturumlar-arası aktarımla. Birebir söz: **"AYRIK, ts anahtarıyla — ara işaret
koyma."** Ek hüküm (damga biçimi): **"3'te damga biçimine dokunma, ayrı alan koy."**

**Hazırlık:** docs/HAZIRLIK-P3-K1-KARISIK-ORNEKLEM-2026-08-30.md — bu belge onu KAPATIR.
**Uygulama:** EDG-2026-042 kartı `p3_karar_ayrik_ts_2026_08_31` bloğu (tam metin, kanıtlar,
K disiplini, P-2 ayrışma beyanı) + reçete `research/olcumler/edg042_recete_ayrik_2026-08-31/` +
haftalık görev metni revizyonu (bitiş ölçütü (a): ulaşabilen-üç-kova; depo aynası
`deploy/claude-tasks/edg042-friksiyon-haftalik.SKILL.md`) + çiviler `tests/test_p3_ayrik_ts_v340.py`.

## Karar, tek paragrafta
K1 iki icra mekanizmasını tek medyanda topluyordu. Bundan böyle `ts` anahtarıyla (sınır:
2026-08-23T14:53:43Z, canlı barclock inişi) iki kola ayrılır: K1-önce (`giris_once`, n=15'te
donuk — kalıcı betimleyici taban, hüküm üretemez) ve K1-1345 (`giris_1345`, hüküm kolu,
`pending-042-giris` kaydının halefi). Ara işaret KONMAZ — öneri sunuldu, operatör reddetti;
sonradan eklemek sayıya bakarak kural seçmek olur.

## Kabul edilen bedel (açıkça)
Canlı para sorusuna hüküm ~14 haftaya kayar (bant 4,9-14; ≈ Aralık başı). Pooled ~6,5 hafta
olurdu ama hükmün yarısı emekli bir icra yolundan gelirdi. **Hız yerine saflık, bilerek.**

## İlk somut doğrulama
Havuzlanmış medyan (29,8) iki kolun hiçbirine benzemiyor (K1-önce 16,1 · K1-1345 210,1 — n=2,
İŞARET, hüküm değil; betimleyiciler ilk kez 2026-09-05 koşumunda resmî yayımlanır). Ayrıştırma
gerekçesi ilk veride kendini gösterdi.

## Açık kalan (operatör listesi)
P-2'nin yeni çerçevesi: EXE-009 hakemi `pencere` damgasında, EDG-042 `ts`de — 13 damgasız
satırda ayrışırlar (beyan EDG-042 bloğunda). Birleştirme kill#3 çerçevesine dokunur; ayrı karar.
