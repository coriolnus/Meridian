# DEVİR NOTU — 2026-08-17 gecesi (operatör uyudu, iş sürüyor)

Bu dosya, oturum tıkanırsa yeni bir oturumun **tam olarak kaldığı yerden** devralması için var.
Operatör talimatı: *"suite bitince kırmızıları listele, ben yatıyorum, dağıtımı yap ve roadmap
itemlerini de düzenle."*

## DURUM ÖZETİ

**Canlı sistem GÜVENDE.** Canlıda `v248` koşuyor, sağlıklı (healthz 200), ve bu gecenin hiçbir
değişikliği dağıtılmadı. Aşağıdaki kırmızılar YALNIZ yerel ağaçta.

**Kesin kural: KIRMIZI SUITE İLE DAĞITIM YOK.** Operatör dağıtım yetkisi verdi ama kapının varlık
sebebi bu; yeşile ulaşılmadan `dagit.sh --uygula` koşulmaz.

## COMMIT'LENMİŞ İŞ (hiçbiri havada değil)

| commit | iş |
|---|---|
| `2849b23` | §7 karar günlüğü: cloud↔yerel ayrışması kapandı, v248 dağıtıldı |
| `9cc1fc4` | ROADMAP Ö-50 (eski §2-50): öğrenme API sürecinde — GIL panoyu boğuyor |
| `842cddf` | Ö-50 kalem 4: `SEARCH_PROGRESS` süreçler-arası olgu (EMNİYET kalemi) |
| _(sonraki)_ | Ö-50 kalem 1-3: `meridian-learn` birimi + `learn_run.py` + 10 çivi |
| _(sonraki)_ | Ö-50 kalem 5 + yasa borçları (codelaw beyanı, SINK_TABANI, YASA 4) |
| _(sonraki)_ | ROADMAP yeniden numaralandırma (kayıpsızlık kanıtlı) |

## AÇIK KALEM 1 — SUITE KIRMIZILARI (dağıtımı BLOKE EDİYOR)

Son tam suite (merge sonrası, Ö-50 ÖNCESİ): **6213 geçti / 0 kırmızı.** Yani kırmızılar Ö-50
değişikliğinden geliyor; arada başka bir şey yok.

Ö-50'nin dokunduğu dosyalar: `meridian/hermes.py` · `meridian/hermes_runtime.py` ·
`meridian/sprint.py` · `meridian/api.py` · `meridian/codelaw.py` · `tests/test_codelaw_kor_nokta_v214.py`
· yeni `meridian/learn_run.py` · yeni `tests/test_ogrenme_birimi_ayrimi_v249.py`

**EN OLASI KÖK (ÖLÇÜLMEDİ — doğrulanmadan düzeltme yapma):** `hermes._progress_aynala()` artık
HER `_progress()` çağrısında `state/search_progress.json` yazıyor. Sandbox kullanmayan testler
canlı `state/`e yazıyor olabilir ve conftest'in `_no_live_state_writes` autouse bekçisi bunu
yakalıyor olabilir. **Bu bir HİPOTEZDİR.** Bu oturumda aynı sınıfta iki hipotez zaten çürüdü
(`barsarchive` çekişmesi, `warnings` filtresi) — önce `grep -E "^(FAILED|ERROR)"` ile ADLARI al.

Çözüm olursa muhtemel yön: aynayı yalnız `config.STATE` sandbox'a yönlendirilmişken ya da bir
ortam bayrağıyla yaz; ya da conftest'e beyanlı muafiyet ekle (ama muafiyet BEYANLI olmalı).

**Çıktı dosyası:** `/private/tmp/claude-501/-Users-erdemozturk-AI-Trading/f323a729-1d39-4530-b645-7c71fa2ed997/scratchpad/suite_v4.txt`

## AÇIK KALEM 2 — DAĞITIM (kırmızılar kapanınca)

1. `./dagit.sh` (kuru koşum) → kapılar yeşil mi
2. `./dagit.sh --uygula`
3. **Birim kurulumu ELLE gerekiyor** (rsync `/opt/meridian`e yazar, systemd `/etc`ten okur —
   bu tuzak 2026-08-14'te ölçüldü, `dagit [1c]` kapısı o yüzden var):
   ```
   ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 \
     'sudo install -m 0644 /opt/meridian/deploy/oracle-a1/meridian-learn.service /etc/systemd/system/ && \
      sudo cp -p /etc/systemd/system/meridian.service /etc/systemd/system/meridian.service.bak-$(date -u +%Y%m%dT%H%M%SZ) && \
      sudo install -m 0644 /opt/meridian/deploy/oracle-a1/meridian.service /etc/systemd/system/ && \
      sudo systemctl daemon-reload && sudo systemctl enable --now meridian-learn'
   ```
4. **DOĞRULAMA (Ö-50 kartındaki kabul ölçütleri):**
   - `/api/public/summary` p95 arama koşarken **< 1,0 sn** (taban: 14,0 sn)
   - toplam CPU kullanımı **> %40** (taban: %25, 4 çekirdeğin biri)
   - `systemctl is-active meridian meridian-learn` → ikisi de active
   - sprint kapısı koşan aramada BAŞLAMAMALI (kill ölçütü)

## AÇIK KALEM 3 — ROADMAP

Yeniden numaralandırma İNDİ ve kayıpsızlığı kanıtlı (maskeli sha `e842246dcb29e7ad`, 3658→3658).
Eşleme tablosu belgenin tepesinde (`§∞`). Kalanlar:

- **§1 HAT** ve **§2 TAHTA** bölümlerinin METNİ yazılmadı (harita hazır, bkz. bu oturumun
  bölüm-haritası mesajı ve `docs/TASARIM-OGRENME-SURECI-AYRIMI-2026-08-17.md` deseni)
- `meridian/` (72) + `tests/` (140) §-atıf çevrimi — dönüşüm betiği hazır:
  `scratchpad/roadmap_donusum.py` (kayıpsızlık kanıtı ve kasıtlı-kırmızı sınaması içinde)
- Operatör bloklarının kimliklendirilmesi (`§5`/A1 → `B-A1`) — Ö-N ile aynı gerekçe

## SÜREÇ KARARI (2026-08-17, kalıcı)

Operatör: *"bundan sonra superpowers roadmapten bağımsız olarak bütün geliştirme cycle'inin
belkemiği olacak."* Hat: **H0 fikir → H1 tasarım → H2 plan → H3 icra (çivi ÖNCE) → H4 doğrulama →
H5 inceleme → H6 kapanış.** Depo yasası skill'i EZER (tasarım `docs/TASARIM-*.md`'ye, ölçüm işinde
spec yerine `research/cards/` ön-kaydı). Hafızada: `superpowers-gelistirme-belkemigi`.

## ORTAM

`caffeinate -dimsu -t 25200` çalışıyor (7 saat) — laptop uyumaz. İş bitince öldürülebilir.
