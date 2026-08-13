# Gece raporu — 2026-08-14

**Operatör talimatı:** *"WP'leri öneri sırana göre sabaha kadar kesintisiz uygula; anahtar/üyelik
gerektirenler hariç. Laptop açık, ben uyuyacağım."* · **Yetki:** dağıtım + restart + model seçimi.

Bu belge sabah tek okumada durumu vermek için yazıldı. Sıra: **ne yapıldı · ne ölçüldü ·
ne yapılamadı ve neden · seni bekleyenler.**

---

## 0. Bir cümlelik durum

Sistem ayakta ve gece boyunca kesinti yaşamadı; beyin zinciri ilk kez gerçekten iki bağımsız
ayaklı ve **24 kat hızlandı**; pano tıkanıklığı, alarm gürültüsünün %68'i ve öğrenme borusunun
görünmez süzgeci kök nedenleriyle kapatıldı. **Hiçbir iddia ölçülmeden yazılmadı** — çürüyen üç
iddia aşağıda adıyla duruyor, biri benim kendi brief'imdi.

## 1. Dağıtılan turlar

| tur | ne | doğrulama |
|---|---|---|
| **v243** | pano açılış tıkanıklığı | canlı `parity_report` **17,4 → 7,8 sn** soğuk · **11,9 → 2,1 sn** sıcak; sayfa artık teşhis ucunu beklemiyor (`analytics.today()` 122 ms) |
| **v244** | `--provider` yönlendirmesi · alarm K1+K2 · ölü model adı · ajan bütçesi 600 | otoriter suite `rc=0`, tam grep sıfır eşleşme; canlı `_agent_call` **attempt=1 empty=false** |
| **birim** | `MERIDIAN_AGENT_RPD=600` `/etc/systemd/system`e kuruldu | worker `/proc/<pid>/environ`dan doğrulandı |
| **v245** | (aşağıda — ajanlar koşuyor) | — |

**Kök nedenler, sırayla:**

- **Pano:** brief'imdeki dört adayın **dördü de masumdu**. Gerçek suçlu, tohum yenilemesinin
  (97→887 satır) `recompute.report()` içindeki bar okumasını **95'ten 400 çağrıya** çıkarmasıydı —
  yani panoyu yavaşlatan şey, dün "iyileştirme" diye yapılan işin yan etkisiydi.
- **Beyin zinciri:** `tencent/hy3:free` OpenRouter'ın **411 modelinden hiçbiri değil** — hiç var
  olmamış. 24 saatte 33/33 boş, çağrıların %46'sı. Üstelik hatalı model künyesi (istenen ↔ cevap
  veren) bu arızayı **gizlemişti**: pano haftalarca `TENCENT/HY3:FREE` yazıyordu.
- **Alarm kutusu:** günde 408 `intraday_gap_detected` = uyarıların %68'i, ve **15/15 örneklemle**
  IEX seyrekliği (LMT 13:34-37: iex boş, sip dolu). Arıza değil, ölçüt kalibrasyonu.

## 2. Ölçümler ve hükümler

**EDG-2026-041 — görünmez süzgeç (28a).** ROADMAP "kod kendi karşı-gerekçesini taşıyor, KART-ÖNCE"
diyordu; karşı-gerekçe okundu ve **geçerli bulundu**. Ölçüm kapının **körlükten değil
ayrımsızlıktan** kestiğini gösterdi: `bg_regime` 47/47'de biliniyordu, 46/47 yeniden yazılabilir.
Hüküm D1+D2: reddedilen öneri deftere REDDEDİLDİ damgasıyla girer, ve `@`siz öneri atılmak yerine
`x@<certified>`e çivilenir — korkuluk bozulmaz, **güçlenir**.

**C6 uzlaştırma — "evren mi ısı mı".** Çelişki değilmiş: seans düzeyinde %99,55 evren, plan
düzeyinde 607/607 ısı. Ardışık darboğaz. **15c askısı kalktı** ama gerekçesi değişti — başarı
ölçütü "daha çok işlem" değil işlem-başı R + sharpe (mb emsali: arz 3,5× red, 1,15× işlem).

**WP7-24b — teşhis değişti.** Kilitli olan araç değil **skill yolu**: model 202 kez araç çağırmış
ama %85'i ham dosya araması, `skill_view` yalnız 5 (%2,5). SOUL düzeltmesi bir **kesintinin içine
indi** (o gün 550× 404), o yüzden hâlâ sınanmadı. Ayrıca `tool_calls` yapısal −1 (`-Q` özeti
bastırıyor) — Meridian kendi defterinden bunu ölçemiyor.

**Model gecikmesi.** Ham API'de üç aday da ~4 sn; skill'li gerçek biçimde **ultra 455,8 sn ↔
super 18,7 sn (24×)**. Darboğaz CLI yükü değil, ultra'nın akıl yürütme uzunluğu (24.213 ↔ 3.732
karakter). `AGENT_RPD=600` ultra ile **76 saat** ederdi — yani bütçe ulaşılamazdı. Model super'e
çekildi, canlı doğrulama **5,6 sn** (öncesi 116-133).

## 3. Çürüyen iddialar — adıyla

1. **Benim brief'im:** "`llm_opinion_calibration` bu künyeye bakıyor" → **BAKMIYOR**. Hatalı
   künyenin tek tüketicisi pano başlığıydı. Kusur gerçekti, yayılma alanı iddia ettiğimden dar.
2. **`model.provider auto` hipotezim:** canlıda denendi, **çalışan Gemini ayağını da düşürdü**
   (ikisi de 401). 50 saniyede geri alındı; karşı-sınama aynı komutta olduğu için yakalandı.
3. **Hafızadaki eski tavsiye:** *"`NOUS_MODEL`'i Google dışı bir modele çevir, ölçüm kendiliğinden
   düzelir"* — harfiyen uygulandı ve **sistemi bozdu**. Ölçüt yeşillenirken (`same_model_ids`
   boşaldı) sistem bozuluyordu. Hafıza düzeltildi.

## 4. Seni bekleyenler

| # | ne | neden bende değil |
|---|---|---|
| 1 | **4 pozisyonun koruma kurulumu** (NUE/EMR/BKNG/AMGN) | broker'a emir göndermek — icra bende değil |
| 2 | **Bildirim kanalı kimliği** (Telegram/webhook) | kimlik |
| 3 | **Pullback silahsızlanma kararı** (EDG-039 ölçüldü) | strateji kimliği değişikliği |
| 4 | **Koruma otomatikleşsin mi** (kalıcı politika) | politika kararı |
| 5 | FINVIZ · FMP · QC login | üyelik/para |

## 5. Açık kalan doğrulamalar

- **Alarm K1+K2 sınanmadı:** dağıtıldı ama piyasa kapalı; boşluk taraması yalnız seans içinde
  koşuyor. İlk gerçek sınav **13:30 UTC**.
- **Model kalitesi ölçülmedi:** super seçimi süre + biçim geçerliliğine dayanıyor. "Görüşleri ultra
  kadar iyi mi" cevaplanmadı; ölçütü `llm_opinion_calibration` + `probgate`e ulaşan öneri sayısı,
  bir öğrenme penceresi sonra.
- **24b hâlâ açık:** düzeltme sonrası ilk tam öğrenme penceresi gerekiyor.
