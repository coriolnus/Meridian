# EDG-2026-051 — genişlik (breadth) dilim ölçümü (ölçüm kaydı, 2026-08-23)

HÜKÜM YOK — hüküm Rol-1'in. Bu dosya yalnız ölçümdür. Kart: `research/cards/EDG-2026-051-genislik-dilimi.yaml` (dokunulmadı).

## Taban ve girdiler (hepsi SALT-OKUMA, teşhis artefaktları EZİLMEDİ)
- **Vekil işlem tabanı (28g teşhisiyle AYNI):** `research/olcumler/exe003_golge_kapsam_2026-08-22/canli_state/meridian.db`
  (sha256 `e4cce480…7782467e`, sonuc.json'da tam). Holdout dilimi `wp3_holdout_teshis_2026-08-22/04_canli_holdout_islemler.py`
  ile AYNI `_in_segment` yasasıyla: `lo <= ts_open[:10] < hi and (not ts_close or ts_close[:10] <= hi)`,
  pencere 2026-04-30..2026-07-30 → **n=87** (kod-içi assert; 87 tutmasa ölçüm durur). Giriş günleri 2026-04-30..2026-07-22, 40 farklı seans.
- **Bar arşivi:** `state/bars/*.csv`, KANONİK ölçüm kapısıyla: `data.REPLAY_UNIVERSE` (251 sembol)
  + `sanitize_bars` + `measurement_bars` (`component_ic._load_universe` ile aynı yol; bütünlük defteri uygulanır, ağ yok).
- **State'e dokunmama:** `meridian.obs._emit` normalde `state/events.jsonl`'a aynalar; ölçümde süreç-içi olarak
  bu dizindeki `obs_events.jsonl`'a yönlendirildi (68 olay; kapı dışlamaları orada, kaybolmadı). Motor dosyası değişmedi.

## Breadth tanımı ve PIT kanıtı (kart kill#3)
- **Tanım:** breadth(t) = t'den ÖNCEKİ son seansın (d\*) kapanışlarıyla, `close(d*) > MA50(d*)` olan sembollerin
  ölçülebilir paydaya oranı (%). Payda: d\*'de barı olan ve d\*'ye dek ≥50 kapanışı olan semboller.
  MA50 penceresi d\*'de biter (yalnız geriye bakar). Yani seri **yalnız t−1'e dek barlarla** — kartın harfiyen kuralı.
- **Kod-içi assert'ler (üçü de GEÇTİ, `kosum.log`):**
  1. Her `breadth_asof(t)` çağrısında `assert d_star < t` (gelecek-bar erişimi kapalı).
  2. MA-pencere öz-sınaması: tohumlu 10 (sembol, gün) örneğinde MA50, "son 50 kapanış, gün dahil, gelecek yok"
     el hesabıyla birebir (tolerans 1e-9).
  3. Nokta-sınama: tohumlu 12 giriş gününde breadth, ham verinin **t-ÖNCESİ dilimiyle** (`df[date < t]`) sıfırdan
     yeniden hesaplandı ve seri değeriyle birebir örtüştü (tolerans 1e-6). Döküm sonuc.json `pit_oz_sinama`da.

## Bölme beyanı (FAZ-A: ölçüm-ÖNCE diske yazıldı)
- Sıralama kanıtı: FAZ-A yalnız `id, ticker, ts_open, ts_close` okur (r_multiple/exit_reason/setup FAZ-A'da HİÇ okunmaz);
  beyan `sonuc.json`'a fsync'le yazıldı (o anki disk sha256 `bolme_beyani_disk_sha256_fazB_oncesi` alanında),
  FAZ-B beyanı diskten geri okuyup değişmediğini assert'ledikten sonra metrikleri ekledi.
- **Medyan = 54,4** (87 giriş-günü breadth değerinin medyanı; tüm giriş günleri holdout penceresi içinde).
  Kural (kart, değişmedi): genis: breadth ≥ medyan · dar: breadth < medyan.
- **n_genis = 54 · n_dar = 33.** Dengesizliğin nedeni mekanik: 11 işlem tam medyan değerinde (aynı giriş-günü kohortu)
  ve beyanlı kural gereği genis'e düşer. **Kill#1 (n<20) TETİKLENMEDİ** — iki dilim de ≥20; bölme değişmedi.
- İşlem-düzeyi döküm (87 satır: id · ticker · giriş günü · kaynak seans d\* · payda · breadth · dilim) sonuc.json'da.
- Kovaryat sağlığı: 87 işlemin TÜMÜ payda **250** seanslardan besleniyor (aşağıda ölçüm-kalitesi notu).

## Dilim tablosu

| dilim | n | toplam R | ort R | stop payı | stop_gap payı | stop∪gap | kazanma | çıkış dağılımı | setup dağılımı |
|---|---|---|---|---|---|---|---|---|---|
| **genis** (breadth ≥ 54,4; değerler 54,4..62,8; 23 gün) | 54 | −14,47 | **−0,2679** | %61,1 | %9,3 | %70,4 | %20,4 | stop 33 · regime_flip 10 · stop_gap 5 · target 4 · target_gap 2 | exhaustion_hammer 25 · momentum_burst 17 · breakout_vcp 11 · pullback 1 |
| **dar** (breadth < 54,4; değerler 47,6..54,0; 17 gün) | 33 | −14,05 | **−0,4258** | %57,6 | %18,2 | %75,8 | %24,2 | stop 19 · stop_gap 6 · target 3 · regime_flip 2 · time_stop 2 · target_gap 1 | exhaustion_hammer 14 · momentum_burst 13 · breakout_vcp 6 |

## Ayrışma ölçüsü (kartın donuk ölçüsü)
- **ΔortR(dar − genis) = −0,1579**
- İşlem-düzeyi bootstrap (B=5000, seed 20260812, dilim-içi yeniden örnekleme, yüzdelik CI):
  **%95 CI = [−0,6516, +0,3354]**
- Karar kuralına dokunmadan mekanik okuma: CI 0'ı İÇERİYOR (CI-üst = +0,3354 > 0). Hükmü Rol-1 işler.

## Betimleyiciler (HÜKÜM DEĞİL)
- **Breadth'in holdout penceresindeki seyri** (2026-04-30..2026-07-30, 62 seans):
  min **47,6** (2026-05-13) · q25 52,9 · **medyan 56,2** · q75 59,5 · maks **68,4** (2026-07-28).
- **Tam-pencere kıyası** (beyanlı tanım: inc-cache geometrisinin tamamı, 2022-01-01..2026-07-30, 1146 seans):
  min 2,0 · q25 42,4 · medyan 55,4 · q75 67,2 · maks 94,0.
  Holdout medyanı tam pencerenin **%51,6 yüzdeliğinde** — yani holdout, tarihsel dağılıma göre "dar genişlik" dönemi DEĞİL;
  penceredeki oynaklık dar bir bantta (47,6–68,4), tarihsel uçların (2–94) çok içinde. İşlem kovaryatının tüm aralığı
  47,6–62,8: dilimler bu DAR bandın iç medyanına göredir, tarihsel anlamda "dar breadth" rejimi holdout'ta hiç oluşmadı.

## Ölçüm-kalitesi notları (sayıların bağlamı — ölçüm bağlamı tuzağına karşı beyan)
- Payda 251 değil **250**: HON, bütünlük defteri (`safe_start=2026-06-30`) sonrası <50 barla hiçbir seansta MA50 üretemedi →
  ölçülebilir evrenden düşer, sessiz değil (sonuc.json `ma_hic_olusamayan` + obs olayı). Diğer 250 sembolün kapsamı tam;
  arşivde eksik CSV yok.
- Pencere içinde payda<240 olan TEK seans **2026-07-29** (arşivin son günü; yalnız 44 sembolde bar var → payda 44,
  breadth 59,1). Bu seans hiçbir işlemin kovaryatına girmedi (işlemlerin d\* aralığı 2026-04-29..2026-07-21, hepsinde payda 250) ve
  betimleyicileri de değiştirmiyor: 2026-07-29 hariç holdout seyri min 47,6 · medyan 56,0 · maks 68,4 (aynı uçlar).
- Bar arşivi 2026-07-28/29'da bitiyor; son giriş günü 2026-07-22 → tüm gerekli d\* mevcut.

## Ölçülemeyenler (uydurma yasağı)
- Yok: 87/87 işlemin giriş-günü breadth'i ölçüldü (r_multiple None yok, breadth None yok).
  Tek düşüm yukarıda beyanlı HON (payda tarafı); işlem tarafında düşüm yok.

## Dosyalar
- Betik: `research/olcumler/edg051_breadth_2026-08-23/olcum.py` — sha256 `75a24a4171a2216cbbc0281c578e49a0f37dc7ebb0da79b88cb5a371d63969ef`
- Sonuç: `research/olcumler/edg051_breadth_2026-08-23/sonuc.json` — sha256 `d7cb527fdb2bd73308714a7f43d5770e75fad20b2168fec9637c44f7cdff0efe`
  (beyan-anı disk sha'sı dosyanın içinde: `bolme_beyani_disk_sha256_fazB_oncesi`)
- Koşum kaydı: `kosum.log` · obs olayları: `obs_events.jsonl` (68 satır)
- Girdi sha'sı: vekil DB `e4cce4804ca2e17ddd5c602588fd3c3d4e45f4ffe97dd67a6110b5db7782467e`
