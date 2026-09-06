# TASARIM — Tohum/replay defterinin PIT üyelikle yeniden kurulumu (TSK-159)

**Tarih:** 2026-09-06 · **Rol-1 tasarımı (H1)** · **Kod YOK — kart (EDG-082) ve operatör kararı bekler** · **Tetik:** EDG-2026-079
hükmü (2026-09-05): tohum defterinde işlem tarihinde S&P 500 üyesi olmayan sembol payı **p = 0,107** (kart eşiği 0,10 → bant 3).
**Ref:** `research/cards/EDG-2026-079-replay-defteri-pit-uyelik-denetimi.yaml`, `research/olcumler/edg079_replay_pit_denetimi/sonuc_2026-09-05.json`,
EDG-2026-076 (kaynak PIT'e uygun), TSK-156 dilim-1 (as_of canlı, tüketicisi yok), TSK-065 (delist-bar kilidi), EDG-2026-070 (üst-sınır asimetrisi).

---

## 1 · Ölçülen zemin

| Ne | Değer |
|---|---|
| Tohum işlemi | 885 (2022–2026) · canlı 16 |
| İşlem tarihinde üye olmayan sembolde açılan | **95 (%10,7)** |
| — sonradan endekse giren (geç katılan) | 42 · MRVL 24 (giriş 2026-06-22) · APO 8 · KKR 5 · BX 3 · DECK 1 · PANW 1 |
| — endeksten çıktıktan sonra | 14 · VFC 11 (çıkış 2024-04-03) · ENPH 3 (çıkış 2025-09-22) |
| — hiç üye olmamış | 39 · ROKU 11 · SPOT 10 · SNAP 8 · BURL 5 · PINS 4 · LNG 1 |
| Sızan işlemlerin medyan R'si | −0,884 (kalanlar −0,168) — sızıntı getiriyi şişirmiyor |
| REPLAY_UNIVERSE 248'in 2022-01-01'de üye olmayanı | 21 (q = 0,085) |
| Replay evreninin kaynağı | `data.REPLAY_UNIVERSE` = bugünkü üyelik + emekliler (elle bakımlı liste); `backtest.replay` evreni `bars` sözlüğünün anahtarlarından alır, tarihe göre süzmez |
| PIT üyelik kaynağı | `constituents.as_of(t)` (TSK-156 dilim-1, canlı #19; tarihsel tablo oldid/sha damgalı; rename eşlemesi EQR→VMRK) — üretim tüketicisi YOK |

**Ne demek:** evren bugünkü listeden kurulduğu için tohum, 2022–2024'te henüz endekste olmayan isimlerin sinyallerini de içeriyor
(seçim yanlılığı: bugün "başarılı" olup endekse giren isimler geçmişe sızıyor). Bu sızıntı burada getiriyi ŞİŞİRMEMİŞ (sızanlar daha
kötü), ama kurulum PIT değil ve OOS/DSR/PBO kapılarını besleyen tohum kanıtı bu şerhle askıda.

## 2 · Asimetri beyanı (bu tasarımın dürüst sınırı)

Üye olmayanı **düşürmek** kolaydır (üyelik listesi var). O tarihte üye olup **bugün listede olmayan** isimleri (2022'den beri
çıkan ~80 isim; emekli 11'i dışında çoğunun barı yok — TSK-065 B-DELIST-KAYNAK, operatör kararı beklemede) **eklemek** mümkün
değildir. Yani PIT-süzülmüş tohum hâlâ bir ÜST SINIRDIR: kaybedenlerin bir kısmı hâlâ eksik. EDG-070'in aynı asimetrisi burada da
beyanlıdır: negatif/bilgisiz sonuç güçlü, pozitif sonuç "en iyi ihtimalle".

## 3 · Tasarım

### 3.1 Motor: opsiyonel üyelik süzgeci (replay/walk_forward)
- `backtest.replay(..., uyelik=None)`: `uyelik(d) -> set[str]` verilirse CLOSE(D) aday taramasında `t ∉ uyelik(d)` olan semboller
  **taranmaz**; açık pozisyonların çıkışları **süzülmez** (endeksten çıkan bir isim pozisyondaysa kuralına göre kapanır).
- `walk_forward` aynı parametreyi geçirir; `reflect`/öneri yolları DOKUNULMAZ (varsayılan `None` = bugünkü davranış birebir; çivi).
- Üyelik sağlayıcısı: `constituents.as_of` (tarih başına önbellek; rename eşlemesi içinde). Ölçüm koşumunda girdi EDG-076'nın
  içerik-adresli HTML'i + donuk güncel liste (research `as_of` ile aynı algoritma — iki uygulama, fark 0 çivisi EDG-076 K2).
- Bayrak yok; süzgeç parametreyle gelir. Canlı P3 taraması `LIVE_UNIVERSE` ile ayrı (TSK-143 kararı: 6 hiç-üye canlıda).

### 3.2 Yeniden tohumlama (bakım penceresi)
- Aynı parametre seti, aynı takvim (2022→2026), `uyelik=as_of` ile replay → yeni tohum defteri `kaynak="replay_seed_pit"`
  (ledgerstamp `kaynak` damgası; eski `replay_seed` satırları SİLİNMEZ, tohum sınırı korunur — TSK-035 retro-damga yasağı).
- İki varyant (operatör sorusu, K grid ×2): (A) hiç-üye 6 sembol replay'de **hariç** (saf S&P PIT); (B) 6'sı **dahil** (canlı evrenle
  tutarlı: "üyelik + beyanlı hiç-üye"). Varsayılan öneri: **A** ölçüm için, **B** canlıyla kıyas için.

### 3.3 Kapı hükümlerinin yeniden okunması
- Eski tohum vs PIT tohum: işlem sayısı, avg_r/medyan R, OOS composite, DSR/PBO kapı hükümleri; hüküm SINIFI değişiyor mu
  ("ship" hakkı olan sürüm aynı mı). Değişmiyorsa tohum PIT-süzgeçli sürümle DEĞİŞTİRİLİR ve şerh kalkar; değişiyorsa hangi
  hükümler askıda kalır kartta listelenir (öğrenme kapısı 0,80 sürümü dahil).

## 4 · Kart taslağı — EDG-2026-082 (kod bundan SONRA)
- **Hipotez:** PIT süzgeçli tohum, eski tohumla aynı kapı hüküm sınıfını verir (survivorship ikinci dereceden); aksi hâlde hükümler askıda.
- **K = 2** (varyant A / B). **Ölçüm:** işlem sayısı Δ, R medyan/avg Δ, OOS composite Δ, DSR/PBO hüküm eşitliği; sızan 95 işlemin
  kaçı gerçekten düşüyor (beklenen: hepsi varyant A'da).
- **Eşik:** kapı hüküm sınıfı 3/3 aynı → "tohum değiştirilir, şerh kalkar"; 1–2/3 farklı → "askıda kalanlar listelenir"; 0/3 → "replay
  hükümleri geçersiz, yeniden değerlendirme".
- **PK (yol-tutarlı):** `uyelik=lambda d: set()` → 0 işlem; `uyelik=lambda d: tüm evren` → eski tohumla birebir (byte-eşit) —
  ikisi ayrışmıyorsa süzgeç çalışmıyor.
- **Kill:** as_of kuramama > %5 · rename eşlemesi eksik (VMRK/EQR çift sayım) · replay süresi ×2'yi aşarsa (önbellek şart).
- **Bedel:** replay süresi (as_of önbellekli, tarih başına bir set); tohum çiftleşmesi (iki kaynak damgası) — okuyucular `kaynak`
  ayrımını zaten tanıyor (analytics `replay_seed` payda dışı).

## 5 · Operatör kararları
1. Replay'de 6 hiç-üye sembol: hariç (A) mi, dahil (B) mi, ikisi de ölçülsün mü (öneri: ikisi, K=2)?
2. Delist barları (TSK-065) için ücretli kaynak: bu tasarımı üst-sınırdan tam PIT'e çıkaran tek şey; karar beklemede.
3. Sıra: EDG-082 ölçümü (yalnız ölçüm, tohum değişmez) → hüküm → tohum değişimi ayrı bakım penceresi.

## 6 · Uygulama sırası (onay sonrası)
S1 kart EDG-082 (Rol-1) → S2 motor süzgeci `uyelik` + PK çivileri (ajan, TDD; varsayılan davranış byte-eşit çivisi) → S3 ölçüm
koşumu (research; girdi donuk) → S4 hüküm karta + ROADMAP → S5 tohum değişimi (bakım penceresi, ledgerstamp) → pitlaw sınıfı
('constituents','as_of') tüketiciyle 'açık'a (TSK-156 dilim-2 b).
