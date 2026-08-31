# Ajan Yüzeyi Dalga-A + ops/filo.py — uygulama planı

> **Ajan işçiler için:** ZORUNLU ALT-SKILL: superpowers:subagent-driven-development.

**Hedef:** Operatör panoda TÜM ajan iletişimini görür (salt-okunur): üç bot + ana hermes
beyninin oturum/mesajları, Telegram teslim olayları, son brifing arşivi — tek zaman çizelgesi.
Artı `ops/filo.py`: bugünkü elle-ssh filo kalıplarını tek komut-satırı aracına toplar.
SOHBET BU DALGADA AÇILMAZ — mevcut dürüst-devre-dışı kutu kalır, nedeni "dalga-B" olarak güncellenir.

**Spec:** ROADMAP §2 H1 "Ajan iletişim yüzeyi" satırı (kapsam+muhatap operatör onaylı) + §4 havuz
girdisi. Mevcut yüzey: `ui/src/pano/yuzeyler/Ajan.tsx` (+ `ajan/SohbetHatti.tsx` — dürüst-disabled).

**Ölçülmüş zemin (2026-08-31):**
- Veri kaynağı HAZIR: her profil `~/.hermes/profiles/<ad>/state.db` — tablolar `sessions`,
  `messages`, `session_model_usage` (bugün canlıda doğrulandı; bekci'de ultra kaydı okundu).
  Ana beyin: `~/.hermes/state.db` (AYNI şema varsayımı ÖLÇÜLEREK doğrulanacak — yoksa o kaynak
  `olculemedi` döner, uydurulmaz).
- Teslim olayları: `state/events.jsonl` → `sef_brifingi_teslim` · `bekci_brifingi_teslim` ·
  `karne_brifingi_teslim` (bugünkü journal'da üçü de görüldü).
- API deseni: `@app.get("/api/roadmap")` sınıfı; auth mevcut dash-token katmanı (yeni mekanizma YOK).
- api.py MOTOR kaynağıdır → dalga sonunda TAM SUITE, push ondan sonra (§8).
- Pano Vite-artefaktı: kaynak değişince `cd ui && npm run build` + eski hash'li paket temizliği
  (bugünün ölçülmüş dersi: paket yenilenmeden dağıtım düzeltmeyi canlıya GÖTÜRMEZ).
- Alınmış vNNN: …v346. Bu plan v347 (api), v348 (filo) alır — oluşturmadan önce grep zorunlu.

## Global Constraints (tümü bugünün ölçülmüş vakalarıyla)

- AJAN GİT: yalnız salt-okunur beyaz liste (`log·show·blame·diff·rev-parse·status`); `stash`
  dahil YAZAN her şey yasak. Commit Rol-1'in.
- pytest DIŞINDA `meridian.obs`a ulaşabilecek koşum YOK; davranış için `sandbox_state` çivisi.
  `monkeypatch.undo()` yasak. TEK pytest, ardışık. Arka plan koşum başlatırsan BEKLEME.
- SQLITE SALT-OKUMA: state.db'ler canlı hermes'in yazdığı dosyalar — API `mode=ro` URI ile
  açar, kilit tutmaz, dosya yoksa/şema farklıysa kaynak `olculemedi` + neden (uydurma yasağı;
  boş liste "iletişim yok" iddiasıdır, ayrı şey).
- Yasa 6: her yeni alanın okuyucusu yüzeyde; Yasa 4: except işaretli (≥20 karakter).
- `ops/filo.py` `meridian` İMPORT ETMEZ (obs'a ulaşamasın — stdlib + ssh alt-süreci);
  sözleşmesi KOMUT SATIRIdır ve teslimden önce bir kez operatörün koşacağı BİÇİMDE koşulur
  (18-yeşil-çivi vakası). profil-guncelle alt komutu stdin-onay tuzağını içeriden çözer
  (bugünün ölçülmüş sahte-başarısı: boş stdin'de "cancelled"+RC=0).
- Sohbet ucu AÇILMAZ; Ajan.tsx'in devre-dışı gerekçe metni güncellenir ama kutu disabled kalır.

### Task 1: `/api/ajanlar` ucu (api.py) + `tests/test_ajan_yuzeyi_api_v347.py`

**Üretilen arayüz (T2 buna bağlanır):** `GET /api/ajanlar` →
```json
{"ajanlar": [{"ad": "sef", "tur": "bot", "model": "...|null", "son_oturum_ts": "...|null",
  "oturumlar": [{"id": "...", "ts": "...", "model": "...",
                  "mesajlar": [{"rol": "assistant|user|system", "ts": "...", "metin": "..."}]}],
  "teslimler": [{"ts": "...", "event": "sef_brifingi_teslim", "damgalanan": [...], "detail": "..."}],
  "durum": "ok|olculemedi", "neden": "...|null"}],
 "kaynak": {"profil_koku": "...", "events": "..."}}
```
- Kaynaklar: profil state.db ×3 + ana `~/.hermes/state.db` (şema doğrulanarak) + events.jsonl
  son N teslim olayı. Mesaj metni kırpılır (satır başına tavan; tavan sabiti beyanlı).
- `limit`/`ajan` query paramları; varsayılan hafif (son 5 oturum, oturum başına son 20 mesaj).
- TDD: sentetik profil kökü fixture'ı (tmp_path'te mini sqlite'lar + sahte events) —
  `sandbox_state` ile; gerçek ~/.hermes'e DOKUNULMAZ. Üç durum çivisi: dolu kaynak · dosya yok
  (olculemedi+neden) · şema-uyumsuz db (olculemedi, exception yutulmaz-işaretli).
- Mutasyon: mode=ro kaldırılınca kilit çivisi ısırır (yazma-kipinde açılmadığı ölçülür) ·
  şema-uyumsuzda olculemedi→bos-liste çevirisi ısırır.

### Task 2: Ajan.tsx gerçek veriye bağlanır + paket yeniden üretimi

**T1'DEN MİRAS SÖZLEŞME (inceleme N-1 — T2 bunu birebir uygular):**
- `null` ≠ `[]`: liste alanlarında `null` = ÖLÇÜLEMEDİ (neden'le çizilir), `[]` = ölçüldü-boş.
- Skaler null anlamları: `model`=oturum kaydı yok · `son_oturum_ts`=hiç oturum görülmedi ·
  `oturum.ts`/`mesaj.ts`=damga çevrilemedi (ham korunur) · `damgalanan`/`detail`=alan olayda yok.
- SIRA sözleşmesi: `oturumlar` YENİDEN→ESKİYE · `mesajlar` ESKİDEN→YENİYE (okuma akışı) ·
  `teslimler` YENİDEN→ESKİYE. Pano bu sırayı DEĞİŞTİRMEZ; tersleme gerekirse görsel katmanda
  beyanla yapılır.
- `kirpildi/ham_uzunluk` alanları varsa kırpma GÖSTERİLİR (…devamı işareti), sessiz kısaltma yok.
- DÜZELTME-TURU EKLERİ (T1 turu 1): `oturum`/`mesaj` → `ts_ham` (başarıda null; ts çevrilemezse ham
  burada korunur ve pano HAM'ı gösterir) · ajan → `teslim_toplam` + `teslim_kirpildi` (tavan kesmesi
  BEYANLI çizilir) · `kaynak` → `teslim_tavani` + `eslesmeyen_toplam` · teslim → `olculemeyen`
  (sef teslimlerinin ölçülemeyen-kaynak listesi — pano düşürmez, rozetle gösterir).



- `Ajan.tsx` + `ajan/` bileşenleri `/api/ajanlar`ı çeker: ajan başına sekme/kart, oturum zaman
  çizelgesi (model rozeti dahil — bugünkü Ultra geçişi görünür olsun), teslim damgaları satırı.
  Şablon-veri kalıntısı varsa sökülür (yerine gerçek uç; sahte sayı bırakılmaz).
- SohbetHatti: disabled kalır; gerekçe metni "dalga-B: uç + duruş çivileri gelince açılacak"
  olarak güncellenir (tarihli).
- `cd ui && npm run build` + eski hash'li pano paketi `git rm` (bugünkü ders) — artefakt commit'e girer.
- Çiviler: mevcut pano test ailesi (`test_pano_altyapi_v287` vb.) + varsa Ajan yüzeyine dokunan
  testler koşulur; yeni çivi yüzey-sözleşmesi sınıfında gerekiyorsa v347 dosyasına eklenir.
- Yerel görsel doğrulama YAPILMAZ (repo kuralı: pano UI yerelde uygulama yüklenerek sınanmaz);
  kanıt = testler + build çıktısı. Canlı doğrulama dağıtım adımının işi (Rol-1).

### Task 3: `ops/filo.py` + `tests/test_filo_araci_v348.py`

Alt komutlar (hepsi ssh sarmalı, A1 hedefli; `--host` varsayılan A1):
- `durum` — üç bot birimi + timer + son koşum sonuçları (systemctl show üçlüsü) tek tablo
- `journal <bot> [-n N]` — son koşum journal kesiti
- `oturumlar <bot> [-n N]` — state.db'den son oturum/model listesi (uzak python -c ile, salt-okuma)
- `test-atesle <bot>` — `sudo systemctl start` KOMUTUNU BASAR ama KOŞMAZ (uzak-sudo Rol-1 izin
  sınıfında engelli — bugün ölçüldü); "koş ve kanıtı topla" akışını operatöre tek blok verir,
  `--kanit` alt adımı koşum SONRASI salt-okuma doğrulamayı kendisi yapar
- `profil-guncelle <bot>` — tar-kopya + `printf y |` onaylı update + doğrulama grep'leri
  (bugünkü kanıtlı prosedür, sahte-başarı tuzağı çözülmüş)
TDD: komut-satırı sözleşmesi çivileri (arg ayrıştırma, ssh komut dizgelerinin kuruluşu —
alt-süreç MOCK'lanmaz, kurulan komut dizgesi ölçülür; gerçek ssh testte ÇAĞRILMAZ). Teslim
öncesi bir kez gerçek koşum: `durum` alt komutu (salt-okuma) operatör biçiminde.

## Görev sonrası — Rol-1
Tahta satırı güncelle · dağıtım (api+pano canlıya; filo yerel araç) · canlı doğrulama
(`/api/ajanlar` gerçek state.db'lerle + panoda Ajan yüzeyi) · TAM SUITE dalga sonunda,
push ondan önce atılmaz (§8) · sohbet-B tahta satırında sırada.
