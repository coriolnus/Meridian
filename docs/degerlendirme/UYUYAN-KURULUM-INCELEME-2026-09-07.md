# Uyuyan kurulum yolu (`dormant_setup`) — ayrıntılı inceleme (TSK-175)

**Tarih:** 2026-09-07 12:3xZ · **Yazan:** Rol-1 · **Okuyucu:** operatör (karar burada verilecek, bu belge karar VERMEZ) ·
**Neden var:** operatör 10:49Z "buna daha detaylı bakalım, şimdilik kalsın". **Girdi:** A1 salt-okunur taze sayım (11:59–12:1xZ) +
üç ajanlı kod/belge taraması (salt-okunur) + `docs/KORUNUM-KOK-2026-08-07.md`. Sayılar A1 canlı defterindendir; kod atıfları
sembol adıyla.

## 0. Otuz saniyelik özet

- **7 Ağustos öncülü bugün geçerli değil.** O gün "31 plan / 0 işlem / 1 GO tüketilmedi / açıklanamayan 14 = uyuyan" ölçülmüştü. Bugün:
  uyuyan plan **10** (defter 13 Ağustos tohumuyla sıfırlandı, planlar 07-24'ten başlıyor), hüküm **REVIEW 6 · NO_GO 3 · GO 1**, GO alan plan
  (CRM, 27 Ağustos) **keşif sondasıyla silahlandı** (`exploration_armed`, 0,25R), bir uyuyan plan (**VLO, 7 Ağustos**) işleme dönüp
  +0,92R ile kapandı, bir plan (VRTX, 2 Eylül) silahlanma yoluna girip "zaten açık" diye düştü. Bekçinin **açıklanamayan 7** satırının
  **hiçbiri uyuyan değil** (normal planlar; uyuyan kova artık ayrı sayılıyor: 4).
- **Yol "arkadan bağsız" değil, iki bağı var:** (A) kurulum-seviyeli terfi kapısı (`arming.py`) — çalıştı, iki kurulumu (momentum_burst,
  exhaustion_hammer) 11-12 Ağustos'ta canlıya aldı; (B) plan-seviyeli 0,25R keşif sondası — kablo canlı, üretim kurak (13 Ağustos'tan
  beri 1 kez: CRM).
- **Tavsiye (Rol-1, bağlayıcı değil):** olduğu gibi kalsın; yalnız iki küçük hijyen işi (§6). Üç seçeneğin bedeli §4'te.

## 1. Arka plan — 7 Ağustos kök nedeni

`docs/KORUNUM-KOK-2026-08-07.md`: `conservation.unexplained = 14` alarmının kökü uyuyan yoldu (31 uyuyan − 17 NO_GO = 14); üç makul
hipotez (kümülatif sayaç · iki kimlik şeması · K1 düzeltmesi) ölçümle çürütülmüştü. §3 kararı operatöre bırakıldı: (a) icraya bağla
(kart-önce), (b) tavsiye kalsın ama kapı GO vermesin, (c) geri al. §4 gözlemlenebilirlik önerilerinden **(2) ayrı bekçi kovası YAPILDI**
(`watchdog.conservation_report` → `uyuyan_kurulum` / `uyuyan_olculemedi`; çivi `tests/test_korunum_uyuyan_kurulum_v283.py`),
**(1) terminal olay (`dormant_plan_lapsed`) yapılmadı** (bekçi geriye dönük sınıflıyor, eşdeğer bilgi var), **(3) pano** yalnız
KURULUM-seviyeli geçiş oranını gösteriyor (`web/app.js` "Uyuyan kurulumlar" kartı = `arming.setup_report`), PLAN-seviyeli "0/N" yok.

## 2. Taze sayım (A1, salt-okunur, 2026-09-07 11:59–12:1xZ)

| Ölçüm | 7 Ağustos | Bugün |
|---|---|---|
| Uyuyan plan (`dormant_setup=1`) | 31 (→32) | **10** (07-24 → 09-02) |
| Hüküm dağılımı | NO_GO 17 · REVIEW 13 · GO 1 | **REVIEW 6 · NO_GO 3 · GO 1** |
| Normal plan hüküm | — | REVIEW 371 · NO_GO 111 · GO 19 (501 plan) |
| Uyuyan → işlem | 0 | **1** (VLO, `P-2026-08-07-VLO-exhaustion_hammer` → T00887, 08-10→08-11, target, +0,918R, live_paper) |
| GO alan uyuyan planın akıbeti | tüketilmedi | **CRM 08-27 GO → `exploration_armed` 20:43Z (slot 1, 0,25R, llm_ranked false)**; broker_status None, işlem yok |
| Silahlanma yoluna giren | — | VRTX 09-02 `armed_dropped_already_open` |
| Bekçi `conservation_report` | unexplained 14 (= uyuyan) | plans 511 · traded 363 · no_fill 7 · replay_era 15 · **uyuyan_kurulum 4** · **unexplained 7 — hepsi NORMAL plan** (MRNA/MRK/BDX 08-19, DE 08-21, MPC 09-01 GO, VRTX/REGN 09-02) |
| Uyuyan kurulum kırılımı | pullback/episodic_pivot ağırlıklı | exhaustion_hammer 3 (07-24..08-07, terfi ÖNCESİ — PIT-doğru damga) · episodic_pivot 3 · pead 3 · momentum_burst 1 (07-24, terfi öncesi) |
| Canlı `ARMED_SETUPS` | breakout_vcp + (terfi 08-11/12) | **breakout_vcp · exhaustion_hammer · momentum_burst** |
| `arming._dormant_setups()` | — | **pullback · episodic_pivot** (pead motor demetinde YOK — beyanlı boşluk sürüyor) |
| `cf_report` (terfi eşiği MIN_CF_ENTERED=30) | — | pullback n=21 avg_r **−0,968** · episodic_pivot n=3 avg_r 1,211 · pead n=1 −1,005 · (exhaustion_hammer 16/0,975 · momentum_burst 1095/0,085 · breakout_vcp 1017/0,002) |
| Keşif olayları (08-13'ten beri) | — | `exploration_armed` 1 · `explore_slot_llm_pick` 0 · `ARMING_READY` 0 |
| Operatör onayı (approvals.jsonl) | — | 2 satır, uyuyan plana **0** → REVIEW dalı uyuyanlar için fiilen ölü |

**VLO işlemi notu:** T00887 `exploration=0`, `broker_teyit=karsiliksiz`, `skill_chain` damgalı (stockbee-exhaustion-hammer-screener →
position-sizer → pre-trade-discipline-gate) → motorun keşif havuzundan DEĞİL, skill zincirinden (bot yolu) yazılmış; ayna teyidi yok.
Yani "uyuyan plan icraya döndü" cümlesi motor yolunu değil bot yolunu anlatır — açık soru §5-1.

## 3. Mekanizma haritası (koddan)

| Bileşen | Rol | Durum |
|---|---|---|
| `meridian/loop.py::daily_cycle` P2 bloğu | `strat.scan_all()` sinyallerinden `setup ∉ ARMED_SETUPS` olanları `dormant_setup=True` ile aday/plan yapar; plan kimliği `P-<tarih>-<ticker>-<setup>` | çalışıyor |
| `meridian/guard.py::classify_gate` | GO/NO_GO/REVIEW hükmü — `dormant_setup` alanını OKUMAZ; uyuyan plan normal planla aynı kapılardan geçer | çalışıyor |
| `meridian/loop.py::girise_uygun` | NO_GO → asla; GO → evet; REVIEW → yalnız operatör onayıyla | uyuyan için GO 1, onay 0 |
| `meridian/loop.py` keşif havuzu (`EXPLORE_MAX_POS`=5 · `EXPLORE_MAX_R`=0,25R · `EXPLORE_TOTAL_R`=1,25R) | GO alan uyuyan plan buraya girer; ≥2 adayda `hermes.rank_explore` sıralar | 13 Ağustos'tan beri 1 silahlanma (CRM) |
| `meridian/counterfactual.py::collect` + `cf_backfill.py` | uyuyan planların karşı-olgusal sonuçlarını (`cf_report`) biriktirir | besleniyor (n'ler yukarıda) |
| `meridian/arming.py::evaluate` | kurulum-seviyeli terfi kapısı: n ≥ 30 ∧ avg_r eşiği ∧ K-cezası ∧ kuyruk vetosu → `ARMING_READY` → operatör onayı → `ARMED_SETUPS` | çalıştı (2 terfi); pead demette yok |
| `meridian/watchdog.py::conservation_report` | uyuyan kovasını ayrı sayar; ihlal yoksa `conservation_uyuyan_kovasi` bilgi olayı | çalışıyor; olay sayısı 0 (ihlal yok → bilgi olayı da yazılmıyor — okuyucu: rapor alanı) |
| `meridian/hermes.py` `dormant_setup_evidence` | brifing kanıt paketine uyuyan n/avg_r | çalışıyor |

Sonuç: uyuyan yolun **asıl tüketicisi** icra değil, **kurulum terfi kapısıdır** (A). Plan-seviyeli 0,25R sondası (B) ikincil ve kuraktır;
kuraklığın nedeni bütçe değil, GO'nun nadirliği + REVIEW onayının hiç gelmemesi (loop.py "kablo canlı, üretim kurak" şerhi, KOVA-6).

## 4. Üç seçenek — bedel ve kazanç

| | (a) İcraya bağla (kart-önce) | (b) Tavsiye kalsın, kapı GO vermesin | (c) Geri al |
|---|---|---|---|
| Ne değişir | Uyuyan GO planları normal silahlanma yoluna / genişletilmiş keşif bütçesine girer; sistemin ne alıp sattığı genişler | Uyuyan plan GO alsa da REVIEW'e düşer; 0,25R sondası da kapanır (CRM sınıfı olay biter) | Üretim + keşif dalı + cf besleme + bekçi kovası + brifing kanıtı kaldırılır (6 dosya) |
| Kazanç | Yeni sinyal ailesi canlı kanıt biriktirir (bugün 0,25R ile ayda ~1) | "GO ama icra yok" yanıltıcılığı biter; sermaye maruziyeti sıfır | Kod ve pano sadeleşir |
| Bedel | Yüksek: episodic_pivot (n=3) ve pead (n=1) kanıtsız; pullback avg_r −0,97; PIT-çapalı kurulumlar (earnings) hata yüzeyini büyütür; ön-kayıt kartı + kill-list + tam suite + dağıtım (L) | Terfi kapısını BESLEYEN cf ledger etkilenmez ama 0,25R canlı sondası kaybolur (terfi kararı yalnız karşı-olgusal kanıtla verilir) (S) | **Terfi yolu kapanır**: exhaustion_hammer/momentum_burst'ün terfi ettiği mekanizma ortadan kalkar, yeni kurulum organik terfi edemez; v283 çivileri + DECLARED_SINKS gözden geçirilir (M) |
| Sermaye riski | YÜKSEK (bilinçli) | sıfır | sıfır (kaldırma sonrası) |
| Geri dönüş | zor (kart hükmü) | kolay (tek koşul) | zor (yeniden yazım) |
| Bugünkü kanıtla | erken: terfi eşiği (30) dolmadan icraya bağlamak, kartın var olma sebebini atlar | davranış zaten neredeyse aynı (onay 0) | 7 Ağustos'un "arkadan bağsız" gerekçesi bugün yok |

## 5. Karara varmadan önce ölçülmesi gerekenler (açık sorular)

1. VLO T00887 hangi yoldan yazıldı: bot/skill zinciri mi, elle mi? (`events.jsonl` 08-10 kayıtları + hermes bot kum havuzu; broker teyidi
   yok — "canlı kanıt" sayılmamalı.) Cevap, (a) seçeneğinin "bot yolu zaten uyuyanı icra ediyor" riskini belirler.
2. CRM keşif silahlanması (08-27) neden işleme dönmedi (no_fill? gap? seans?) — `entry_execution.jsonl` 08-27/28 satırları.
3. pead'in motor demetinde olmaması (beyanlı boşluk) kapatılacak mı — 3 uyuyan pead planı cf'ye giriyor ama terfi edemez.
4. pano "Uyuyan kurulumlar" kartının KURULUM-seviyeli oranı, operatörün beklediği PLAN-seviyeli "işleme dönen/uyuyan" oranıyla
   karıştırılıyor mu — etiket düzeltmesi (TSK-175 hijyen).
5. pitlaw: episodic_pivot/pead için sözleşme kaydı A1'de `meridian/pitlaw.py::rapor` ile doğrulanmalı (ajan yalnız `arming.PIT_CAPALI_KURULUMLAR`
   sözlüğünü gördü).

## 6. Rol-1 önerisi (bağlayıcı değil)

- **Durum: olduğu gibi kalsın** — 7 Ağustos'un gerekçesi (arkadan bağsız, açıklanamayan 14) bugün ölçülemiyor; yol, kurulum terfi kapısını
  besliyor ve o kapı kanıtla çalıştı. (a) için terfi eşiği zaten var (30 karşı-olgusal işlem + avg_r), kart-önce o kapının kendisidir;
  (c) terfi mekanizmasını öldürür.
- Düzeltme 13:5xZ (kod okundu): pano Muhafaza raporu satırı `açıklanamayan N · uyuyan-kurulum K` ile PLAN-seviyeli paydayı ZATEN basıyor ve
  "Uyuyan kurulumlar · silahlanma ölçümü" başlığı kurulum-seviyeli olduğunu söylüyor → hijyen-(i) daralır: yalnız "uyuyan → işleme dönen n"
  sayısı eksik (watchdog alanı + pano; motor dosyası → tam suite). Değeri düşük; TSK-175 kapsamından çıkarıldı, istenirse ayrı kalem.
- **İki hijyen işi (S, otonom uygulanabilir, sermaye etkisi yok):** (i) pano kartı etiketini "kurulum terfi oranı" yap, plan-seviyeli
  "uyuyan: işleme dönen / toplam" satırını payda-beyanlı ekle (KORUNUM-KOK §4-3 harfi); (ii) `conservation_report`'ta uyuyan kovasının
  okuyucusu var (rapor alanı) — bilgi olayı yalnız ihlalde yazılıyor, bu tasarım gereği; not düşülür, değişiklik yok.
- Karar sorusu **yeniden sorulmaz**; operatör isterse §4 tablosuyla verir. Açık sorular §5-1/§5-2 bir sonraki sakin günde ölçülür ve bu
  belgeye eklenir.

## 7. Kaynaklar

A1: `state/meridian.db` (trade_plans 511 · trades · portfolio), `state/arming_report.json`, `state/events.jsonl`, `state/approvals.jsonl`,
`watchdog.conservation_report()`, `strategy.ARMED_SETUPS`, `arming._dormant_setups()`. Repo: `docs/KORUNUM-KOK-2026-08-07.md`;
`meridian/{loop,guard,arming,counterfactual,cf_backfill,watchdog,hermes}.py`; `meridian/web/app.js` uyuyan kartı;
`tests/test_korunum_uyuyan_kurulum_v283.py`; ROADMAP §2 TAHTA 🔒 satırı, TSK-175. Hafıza: `uyuyan-kurulum-yolu` (güncellendi 2026-09-07).
