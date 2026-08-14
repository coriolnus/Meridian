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

## 3b. v245 — beş cephe, paralel, dosya-ayrık

| cephe | ne yapıldı | doğrulama |
|---|---|---|
| **WP6-26** değer-eşitliği kapısı | 26 çift envanteri: **13'ü kaynağında zaten kapanmış · 4+1 bağlandı · 9'u bağlanmadı (her biri NEDENİYLE)** | 436 test yeşil · **maliyet DÜŞTÜ**: 9,10 → 7,13 ms (okuma kutusu + libyaml) · canlı `total 9 · esit 7 · ayrik 0` |
| **WP3-28c** öğrenme hafızası | `already_failed` exploit yoluna; iki tanım **bire indi**; adım merdiveni; kısırlık görünür | ~810 test yeşil · gizli `KeyError` (`x@rejim` son-eki) testle yakalandı |
| **WP3** model künyesi | `candidate_review.json` artık **cevap veren** modeli taşıyor; `model_kaynagi`/`model_istenen` ile iki anlam iki ada ayrıldı; ayrışma olayı | 20 çivi; bu gecenin vakası (birinci boş → ikinci dolu) doğrudan çivili |
| **WP8** kayan oturum | v2 jeton `<exp>.<iat>.<nonce>.<imza>`; yarı-ömürde tazelenir, **7 gün mutlak tavan**; v1 doğrulanır ama yenilenmez | 758 test · **yakalanan tuzak:** tazeleyici `/api/logout`un silme başlığını ezecekti → çıkış sessizce çalışmaz olurdu |
| **WP8** kimlik olayları | `login_ok` · `session_refresh` · `session_drop` · `login_locked_out` (kilit devreye girince defter tamamen susuyordu) | parola/jeton hiçbir olayda geçmiyor (dizgi çivisi) |
| **WP2-D** equity_curve | bacak-1 `seed_boundary` **son noktadan okumayı bıraktı** (reset işareti → damga → `None`+neden); bacak-2 kadanslı yazar (`file_lock`, idempotent, ölçülemezse yazmaz) | 1822 test yeşil · `lint-imports` 5 KEPT / 0 broken · `silent_handlers 0` |
| **WP11-15g** slot↔sektör | sektör tavanının paydası `max_open_positions`tan **ayrıldı** (`sector_cap_basis`, operatör-only) | **620 hücrelik** kalıcı eşdeğerlik matrisi + tek seferlik **17.856 hücrelik** diferansiyel kıyas → sıfır ayrışma; canlıda **no-op** (anahtar yok → türetilmiş payda) |

**Yöntem notu — beş ajanın beşi de kendi enstrümanını sınadı:** kapının gerçekten kıyas ürettiği
ayrı çiviyle · tazeleyicinin logout'u ezmediği olguya bakarak · boş `grep`e güvenmeden önce
**bilerek kırmızı dosyayla** `FAILED`in göründüğü · sökülen kodun gizli çökmesi iddia yerine testle.
Bu, gecenin başındaki `tool_calls: −1` dersinin karşılığı: **hep aynı şeyi söyleyen gösterge kanıt
değildir.** (Aynı tuzağa ben de düştüm: "pytest koşuyor mu" bekçim `grep -c '[p]ytest'` ile
**kendini** sayıyordu.)

## 3c. Dağıtım sonrası ölçüldü — ve çerçevem DÜZELDİ

Dağıtımdan hemen sonra canlıda ölçtüm; **ilk çerçevem fazla dramatikti, düzeltiyorum.**

**ÖNCE ne demiştim:** *"Faz-6 kilidi meşru biçimde düşebilir."*
**ÖLÇÜLEN:** `edge_verdict` canlıda **zaten 2/5** — yani kilit **hâlihazırda kapalı**
(`skor_sonuc` geçti · `rejim_edge` geçti · `spy_ustu` sağlanmadı · `tahmin_isabeti` ve `kuyruk`
**ölçülemedi**). `kuyruk` ölçütünün içindeki `max_dd` canlıda **0,1156**.

**DOĞRU CÜMLE:** kadanslı yazar devreye girince bir kilit *düşmeyecek* — **bir ölçüt
"ölçülemedi"den "ölçüldü ve geçmedi"ye dönecek.** Geçen ölçüt sayısı değişmez (2/5 kalır);
değişen, kapalı olmanın artık **ölçülmüş** bir gerekçesi olmasıdır. Bu bir kayıp değil kazanç:
"bilmiyoruz" ile "ölçtük ve geçmedi" aynı şey değildir ve bugüne kadar aynı kovaya düşüyordu.

Eşiğe dokunulmadı ve dokunulmayacak (EDG-037'nin `RESULT_PF_MIN` emsali: *"kilidin kapalı kalması
ARIZA DEĞİL KORUMA"*). **Ne zaman görünür:** yazar seans sonunda yazar, yani ilk nokta bugünkü
seansın kapanışında düşer — o ana kadar `kuyruk` hâlâ `olculemedi` görünecektir.

### Dağıtım sonrası doğrulama (04:20 UTC+3, canlı)

| ne | sonuç |
|---|---|
| `seed_boundary` | `replay_end 2026-07-20` · `kaynak: reset_isareti` · **`yollar_ayrisik: true`** (reset 07-20 ↔ trades 07-24) · `guven: yuksek` — ayrışma artık **görünür**, sessiz seçim yok |
| değer-eşitliği kapısı | **9 çift · 7 eşit · 0 ayrık · 0 ölçülemeyen · 2 beyanlı-ayrı** (gerekçeleri yazılı) |
| servis | `active` · healthz **18 ms** |
| dagit [1c] | 7 birimin 7'si birebir — gece kurulan birim tuttu |

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
