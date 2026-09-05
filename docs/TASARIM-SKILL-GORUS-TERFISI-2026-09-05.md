# TASARIM — Skill görüşünün TERFİSİ: görüş gerçek kararı nasıl etkiler (TSK-126)

**Tarih:** 2026-09-05 · **Rol-1 tasarımı (H1)** · **Kod YOK — bu belge operatör onayı bekler** · **Tetik:** EDG-2026-019
resmî koşum #1 (2026-09-03) iki terfi adayı + bir emeklilik işareti verdi; "terfi" bugün yalnız bir LİSTEDİR, eylemi yoktur.
**Sahibi:** WP7 (skill katmanı) + WP3 (öğrenme döngüsü). **Ref:** `research/cards/EDG-2026-019-skill-gorus-defteri.yaml`
(`hukum_2026_09_03`), `research/olcumler/edg019_skill_gorus_etki/sonuc_2026-09-03.json`, TSK-073 (DONE 2026-09-03).

---

## 1 · Bugünkü durum (ölçüldü, iddia edilmedi)

| Ne | Değer / yer |
|---|---|
| Terfi adayı 1 | `stockbee-exhaustion-hammer-screener` · yüzey **aday-siralayici** · n=245 · rank-IC **+0,169** CI[+0,038; +0,299] · p=0,0156 · FDR-sağkalan |
| Terfi adayı 2 | `vcp-screener` · yüzey **cikis** · n=1337 · çıkış katkısı **+0,144** CI[+0,104; +0,183] · p=0,0078 · FDR-sağkalan |
| Emeklilik işareti | `stockbee-exhaustion-hammer-screener` · yüzey **cikis** · katkı **−0,428** CI[−0,686; −0,209] · **1/3 pencere** (kart kill#3 üç ardışık pencere ister; pencere sayacı kodda YOK — `rapor()` bunu beyanla söyler) |
| "Terfi" bugün ne | `skill_gorus.rapor()` → `terfi_adaylari` listesi → tek okuyucu `api._eksen2_gorus` (pano Eksen-2). Hiçbir bayrak, eşik, plan, emir değişmez |
| Yasa | Motor-içi otomatik bayrak yazımı YASAĞI (Eksen-2 kararı 2026-08-06); `skill_gorus` sözleşmesi: "kayıt defterine, bayrağa, eşiğe, plana, emre DOKUNMAZ" |
| Canlı karar noktası — giriş | `loop` aday kesiti: `candidates.sort(key=score)` — `strategy.EntrySignal.score` (bileşenleri defterde, metinde değil) |
| Canlı karar noktası — çıkış | `strategy.structural_stop` · `strategy.early_kill_pivot_exit` · trail yaması — kural tabanlı, görüş okumaz |
| Görüşün t-çiti | Görüş satırı kuyruk snapshot'ından üretilir (`SNAPSHOT_ALANLARI` beyaz listesi); ileri-bakış yok — bu belge o çiti korur |

**Emsaller (deponun kendi kalıpları, yeniden icat edilmez):**
- *Yetkisi uykuda yazılı terfi kuralı:* `analytics` LLM danışman terfisi — `LLM_PROMOTE_MIN_PAIRS=30`, `MIN_BUCKET=8`,
  `R_GAP=0,3`; kural şimdiden yazılı, yetki operatörde. Aynı biçim burada da geçerli.
- *Varsayılan-kapalı bayrak + kart açılış kaydı:* `config.SKILL_GORUS_URETIM_ACIK` — elle True yasak, açılış yalnız kartın
  resmî kaydıyla; çivi `tests/test_e_partisi_v278.py` bayrak↔kart bağını zorlar.
- *Gölge ölçüm sınırı:* `faz5_cikis` — gölge dolum ↔ EOD dolum kıyası MODEL-MODEL'dir, gerçeklik çapası `hukme_girmez`.
- *Uyuyan yol dersi:* `dormant_setup` 31 plan / 0 işlem — önden bağlı arkadan bağsız yüzey inşa edilmez; tüketici ilk günden.
- *Bedel yasası:* çıktı değiştiren her değişiklik ne KAYBETTİĞİNİ de ölçer (vaka @bekci).

## 2 · İlke — terfi bir "yetki" değil, ÖLÇÜLMÜŞ BİR KANALDIR

Görüş katmanı (gölge) ile karar yüzeyi (canlı) arasında bir kanal açılacaksa, kanal şu yedi şartı taşır; taşımayan
tasarım bu belgeyle reddedilir:

| # | Şart | Neden |
|---|---|---|
| Z1 | Terfi kararı OPERATÖRÜNDÜR; motor kendi kendine bayrak çevirmez | Eksen-2 yasağı (2026-08-06) |
| Z2 | Kart-önce: eşik/kill/PK ölçümden önce donuk | CLAUDE.md §5 |
| Z3 | Varsayılan-KAPALI bayrak; açılış yalnız kart kaydıyla (v278 emsali) | elle açma yasağı |
| Z4 | Bayrak kapalıyken davranış BİREBİR eski (byte-eşit sıralama çivisi) | geri alınabilirlik |
| Z5 | İleri-bakış yok: görüş t-anında mevcut olmalı (kuyruk snapshot çiti) | görüşün içine cevabı yazmamak |
| Z6 | Uyuyan yol yok: kanalın okuyucusu (çözücü + pano alanı) kanalla AYNI GÜN doğar | Yasa 6, dormant_setup |
| Z7 | Bedel ölçülür: sıralamada kaç aday yer değiştirdi, üst-N kesişimi, kadans p95 | bedel yasası, kill#1 |

## 3 · Reddedilen yaklaşımlar

- **R1 — Doğrudan ağırlık canlıda** (`score += w·görüş`): tek adımda canlı davranış değişir; ölçüm ve karar aynı yola
  biner, "işe yaradı mı" sorusu cevaplanamaz hâle gelir (Ö-39'un kök kusuru: model değişti–isabet arttı okuması sahte).
  İlk adım olarak reddedildi; Aşama B'de SINIRLI hâliyle döner.
- **R2 — Veto** (görüş "zayıf" derse adayı ele / "çık" derse çık): ikili ve asimetriktir — yanlış görüş işlem kaçırtır, görüş
  yokluğu "veto yok" demektir, emeklilik yönü için kullanılamaz. Reddedildi.
- **R3 — Skill'in kendisini üretime alma** (skill dosyasını canlı döngüde koşturmak): görüşler zaten deterministik motor
  türevi; skill koşturmak kill#1'in (p95 +%557, 2026-08-23 kapanış) aynısını üretir. Reddedildi.
- **R4 — LLM görüşünü doğrudan karara bağlama:** `skill_gorus_llm` görüşleri ayrı FDR ailesindedir (üretici `llm`),
  kalibrasyon defteri kuraklıkta (n_live=0/30). Bu belgenin kapsamı DIŞI; ayrı kart.

## 4 · Tasarım — iki aşama: GÖLGE KOL → SINIRLI AĞIRLIK

### Aşama A — Gölge sıralama kolu (canlı karar DEĞİŞMEZ)

**Ne:** her aday kesitinde iki sıralama üretilir — mevcut (`score`) ve görüşlü (`score' = score + w·z(görüş_skoru)`; `w` karttan,
TEK değer, grid yok; `z` görüş skorunun kesit-içi standartlaştırması). Gerçek emir MEVCUT sıralamadan çıkar. İki sıralama
`state/golge_siralama.jsonl` defterine yazılır: `{tarih, hedef, sira_mevcut, sira_gorus, delta, ustN_kesisim}` — yalnız
üst-N kesiti (defter süresiz büyümez; N mevcut plan tavanı).

**Çözücü:** gerçekleşen R (cf + gerçek, `skill_gorus._gozlemler` ile AYNI sonuç defterleri) üzerinden iki sıralamanın
rank-IC'si; hüküm **Δrank-IC = IC(görüşlü) − IC(mevcut)**, tarih-kümeli bootstrap %95 CI, seans başına kümeleme.

**Okuyucu ilk günden (Z6):** `rapor()`a `golge_kol` alanı, `api._eksen2_gorus` aynı alanı taşır, pano Eksen-2'de
"gölge kol: Δrank-IC, n seans, üst-N kesişimi" satırı. Bekçi (`ops/bekci_tarama.py`) "defter yazılıyor ama okunmuyor" sınıfını
zaten tarar — bu defter de o taramaya girer.

**Pencere sayacı (kill#3 borcu, aynı dilim):** `rapor()` bugün "pencere sayacı bu turda YOK" der. Aşama A ile birlikte
`state/skill_gorus_pencereler.jsonl` — her resmî koşumda skill×yüzey başına `{koşum_ts, yon, sagkalan}`; ardışık pencere
sayısı buradan türetilir (terfi için de emeklilik için de). Bu sayaç olmadan ne terfi ne emeklilik "3 pencere" şartını
ölçebilir.

**Çıkış yüzeyi (vcp cikis adayı) için gölge:** görüş "daha erken çık" dediğinde gölge çıkış EOD fiyatıyla kaydedilir, gerçek
pozisyona dokunulmaz; kıyas `faz5_cikis._cift` kalıbıyla (bps, tarih-kümeli bootstrap, MODEL-MODEL sınırı beyanlı).
**Öneri:** ayrı kart (sıralayıcı önce; çıkış gölgesi ikinci kart) — iki yüzeyi tek kartta karıştırmak K sayımını bulandırır.

### Aşama B — Sınırlı ağırlık canlıda (yalnız Aşama A kartı GEÇTİYSE + operatör onayı)

- Bayrak `SKILL_GORUS_TERFI_ACIK` varsayılan-KAPALI; açılış kartın açılış kaydıyla (v278 emsali çivi). Kapalıyken sıralama
  byte-eşit (çivi). `w` karttan (Aşama A'nın aynı değeri — yeni değer = yeni kart).
- Kapsam: yalnız FDR-sağkalan ∧ **en az 2 ardışık pencere aynı yönde** skill'ler (emeklilik 3 pencere ister; terfi için
  2'nin altı "tek pencere şansı"dır). Skill başına ayrı `w` YOK (grid çarpımı).
- Ship kapısı: görüş ağırlığı bir STRATEJİ PARAMETRESİDİR — `reflect` ship yolunun DSR/PBO kapılarından geçer
  (`validation.dsr_kapi`/`pbo_kapi`), ayrı bir kapı icat edilmez.
- Emeklilik simetrisi: 3 ardışık negatif pencere → o skill için görüş ÜRETİMİ durur (yazım durur, defter kalır) — yine
  bayrak + kart kaydıyla, motor kendi kendine kapatmaz (Z1).

## 5 · Ölçüm kartı şablonu (EDG-2026-077 taslağı — kart yazılmadan kod yok)

- **Hipotez:** exhaustion-hammer'ın aday-siralayici görüşü sıralamaya `w` ağırlığıyla eklenince üst-N adayların
  gerçekleşen R rank-IC'si artar (Δrank-IC > 0).
- **K:** 1 (tek `w`, tek yüzey). **n_min:** 30 seans (EDG-019 ile aynı taban). **Eşik:** Δrank-IC CI-altı > 0 ∧ üst-N
  kesişimi ≥ %50 (kol "başka bir strateji" olmamalı — bedel). **Pencere:** 40 seans (kill#2 ile aynı ufuk).
- **Kill-list:** (1) kadans p95 +%10 → kol kapanır (kill#1 aynen); (2) üst-N kesişimi < %50 → kol bir ağırlık değil
  yeni stratejidir, kart 'kaldı'; (3) Δrank-IC CI-üstü < 0 → görüş zararlı, emeklilik sayacına negatif pencere;
  (4) girdi bekçisi (cf/exit_efficiency) bayat → hüküm yok.
- **PK (yol-tutarlı):** aynı çözücüye (a) RASTGELE görüş → Δ ≈ 0 (CI sıfırı içermeli); (b) sonucu BİLEN sentetik
  görüş (yalnız test, deftere yazılmaz) → Δ > 0 belirgin. Ayrışmıyorsa çözücü kör.
- **`w` nasıl seçilir:** ölçümle — son 60 seansın `score` kesit dağılımından, görüş z=±1'in medyan sırayı ≈1 basamak
  kaydıracağı büyüklük; kartta donar (sayı bu belgede uydurulmaz).

## 6 · Bedel — ne kaybederiz, ne riske gireriz

| Bedel | Ölçüm |
|---|---|
| Kod yüzeyi | loop aday kesitine 1 kanca (gölge sıralama), 1 defter, 1 çözücü, 1 pano alanı, 1 sayaç defteri |
| Kadans süresi | görüş katmanı p95 kill#1 mandalı AYNEN — gölge sıralama kadans-içi yalnız append (kuyruk deseni) |
| Yanlış terfi | FDR q=0,10 → aile başına %10 yanlış keşif; 2 ardışık pencere şartı bunu düşürür, sıfırlamaz |
| Görüş kuraklığı | n_min 30 seans; bugün exhaustion-hammer n=245 yeterli, pead/pullback/episodic yetersiz (kova adıyla raporlanır) |
| Yanlış hipotez | Aşama A'da canlı karar değişmediği için bedel yalnız kod + disk (defter üst-N kesitli) |

## 7 · Operatör kararları (bu belgeyle masaya)

1. **Aşama A açılsın mı?** (gölge sıralama kolu — canlı karar değişmez; kod kart-sonrası) — öneri: EVET.
2. **Çıkış yüzeyi gölgesi** aynı kartta mı, ayrı kartta mı? — öneri: AYRI (sıralayıcı önce).
3. **Pencere sayacı** Aşama A dilimiyle birlikte mi? — öneri: EVET (kill#3 ve terfinin "2 pencere" şartı onsuz ölçülemez).
4. **Aşama B'nin ön şartı** olarak "Aşama A kartı geçti + operatör onayı" yeterli mi, ek olarak canlı DSR/PBO kapısı da
   istensin mi? — öneri: İKİSİ DE (ağırlık bir strateji parametresidir).

## 8 · Uygulama sırası (onay SONRASI; bu belge kod üretmez)

S1 kart EDG-2026-077 (Rol-1) → S2 pencere sayacı + gölge sıralama defteri (ajan, TDD; loop kanca kadans-içi yalnız append)
→ S3 çözücü + `rapor().golge_kol` + pano alanı (aynı dilim — Z6) → S4 40 seans ölçüm (07:30Z üretim timer'ıyla aynı ritim)
→ S5 hüküm karta → Aşama B ayrı kart (bayrak + ship kapısı entegrasyonu). Emeklilik yolu S2'deki sayaçla aynı gün ölçülür
hâle gelir; exhaustion-hammer cikis işareti 1/3 → sayaç doğunca ikinci pencere okunur.
