# Bot roster — tasarım (çalışan belge)

**Durum:** tasarım aşaması. Kod yazılmadı. Bu belge TEK KAYNAKTIR — plan bundan sonra burada
değişir, sohbette değil. (Sebebi kayıtlı: plan 30 mesaj boyunca düzyazıda taşındı ve her
yeniden türetmede sayılar/sıralar kaydı; altı kez tutarsızlık ölçüldü.)

## 0. Amaç

`state/goal.yaml` sistemin amacını beyan ediyor: 30 günde %7 getiri, Sharpe ≥1,2, çekilme ≤%16,
30 günlük getiri −%4'ün altına düşerse **deney başarısızdır**, ve `autonomy_level: 0 → 1 → 2`
merdiveni. Botlar buna hizmet ettiği ölçüde değerlidir; bot kurmak amaç değildir.

Operatörün istediği dört şey ve **bunlar paralel değil, üst üste yığılı**:
```
Doğrulama    ← geçmişte ne iddia edildiğini + kodun anlamını + gözetimsiz koşmayı GEREKTİRİR
Özerklik     ← hafızasız nöbetçi tekrar bildirir; anlamayan triyaj yapamaz
Anlama       ← sorgulanabilir hâle gelmiş SÜREKLİLİKTİR
Süreklilik   ← zemin. Bu yoksa hiçbiri birikmez.
```

## 1. Kapsam kararı

105 aday üretildi (8 yöntem: veri kaynağı · org şeması · analoji · tersine çevirme · şapka
değiştirme · SCAMPER · ilk ilkeler · gözlem). Tekilleştirildi:

| kategori | sayı |
|---|---|
| **BOT** | **21** |
| şapka (çivi/cron, sıfır LLM) | 2 |
| iş (bir kez yapılır) | 7 |
| mekanizma (config/kod kararı) | 3 |
| botlara yutulan | 72 |

Liste **doygun**: son iki tur yeni sınıf değil varyant üretti. Genişletilmeyecek.

### 21 bot
`@kod` · `@karne` · `@nobet` · `@bekci` · `@hipotez` · `@denetci` · `@tasarimci` · `@olay` ·
`@ayna` · `@sef` · `@veri` · `@karar` · `@piyasa` · `@civici` · `@devir` · `@yol` ·
`@derleyici` · `@olcum` · `@kacan` · `@butce` · `@yabanci`

### Sınıflandırma ölçütü (maliyet DEĞİL)
1. Ayrı girdi mi? Aynı kaynağı okuyorsa şapkadır.
2. Tüketicisi var mı? Yoksa `codelaw` zaten ihlal sayar.
3. Birikimli mi? Diskten türetilebiliyorsa bot değil rapordur.
4. Ölçülmüş boşluk mu?
5. Zayıf modelde çalışır mı?

## 2. Hedef roster: 7 rol

**DİKKAT — bunlar ROL, profil DEĞİL.** Kaç tanesinin kendi Hermes
profili olacağı §3'ün kararıdır; cevap uzun süre **bir** olabilir.

Seçim ölçütü "en faydalı yedi" değil, **birbirinden en farklı yedi** — her biri ayrı bir
mimari kalıbı kanıtlar ve dört amacın hepsi kapsanır. Sıra §3'te.

| bot | kanıtladığı kalıp | amaç |
|---|---|---|
| `@kod` | zemin: paylaşımlı bilgi, MCP ile hem operatöre hem Claude'a | süreklilik + anlama |
| `@hipotez` | en büyük ölçülmüş boşluk (5 günde 0 hipotez, 20 Tem'den beri 0 ship) | öğrenme |
| `@karne` | zamanlanmış rapor + `goal.yaml`ın sorduğu soru | amaç |
| `@nobet` | talep üzerine + LLM'siz teslimat | özerklik |
| `@bekci` | sessiz arıza sınıfı (bugünkü üç bulgunun üçü de bu) | özerklik |
| `@ayna` | roster'ın kendi değerini ölçer — çok bot kuruluyorsa ZORUNLU | doğrulama |
| `@sef` | yönlendirme + dikkat bütçesi | yüzey |

**Değişmez şart:** her bot, **okuyucusu beyan edilmiş** bir artefaktın tek yazarı olarak doğar.
`codelaw` bunu zorlar. Böylece "kimsenin okumadığı çıktı" arızası yapısal olarak imkânsızlaşır.

## 3. Fazlar — İŞ AKIŞI ÖNCE, PROFİL SONRA

**Bu sıra 2026-08-27'de DEĞİŞTİ.** Eski hâli "ilk dalgada 7 profil" idi. Kaynak ve gerekçe §8'de:
kanıt, planımızın tam bu noktasını çürüttü.

**Faz 0 — tesisat** *(iki arka plan görevi koşuyor)*
- uydurma maliyet: `price_for()` `:free` modelleri tanımıyor, Opus fiyatına düşüyor
- `max_tokens` + `timeout` BİRLİKTE: ölçüm `docs/OLCUM-MODEL-BUTCESI-2026-08-27.md`

Tesisat inmeden üstüne bot koymak, ölçülen **%54 kesilme** oranına yatırım yapmaktır.

**Faz 1 — İŞ AKIŞI. YENİ PROFİL YOK.** Her şey ana profilde kanıtlanır.
- **BİR skill:** tekrarlayan ölçüm kalıbı (ssh + journalctl + state okuma + olay adını
  KODDAN bulma). Ölçüldü: bu oturumda ~60 komut, beş kalıp, iki sahte-sıfır.
- **BİR zamanlanmış iş, ve KARAR döndürür:** 310 teslim edilmemiş alarm +
  `self_review.json` + `improvement_proposals.jsonl` (16 öneri) → tek brifing.
  **Hiçbir şey yoksa SESSİZ.** Hepsi zaten hesaplanmış; `ops/alarm_backlog_digest.py`
  yazılmış ama koşmuyor.

Bu faz teslimat zincirinin tamamını sınar (Telegram bağlama, yönlendirme, dikkat bütçesi) ve
hiçbir yeni üretici eklemez — bu sistemin ölçülmüş hastalığı üretmemek değil, ürettiğini
okumamaktır.

**Faz 2 — İLK profil.** Faz 1'de iş akışı kanıtlanmış olan. Tek.

**Faz 3 — kalan roster**, her biri kanıtlandıkça.

## 4. `@kod`un zemini — KARAR: hafif başla, tetikle yükselt

Kanıtın hafıza yığını (§8) bu soruyu büyük ölçüde cevaplıyor ve içinde **kod grafiği yok**:

> sabit olgu → **hafıza** · prosedür → **skill** · uzun araştırma notu → **wiki** ·
> geçmiş konuşma → **oturum araması**

Meridian'ın şerh külliyatı ve `docs/` tam olarak "uzun araştırma notu"dur.

**Seçim: `qmd` + `codelaw` + `/learn` + `session_search`.**
`qmd` official/MIT, yerel, MCP, **tünel yok**; `codelaw` artefakt grafiğini zaten tutuyor.
Ayak izi: bir yerel gömme modeli. A1'e genç bağımlılık girmiyor.

**ELENEN — `official/research/gitnexus-explorer`:** Cloudflare tüneli gerektiriyor ve
`cloudflared`ı **otomatik kuruyor**. Alpaca anahtarlarının durduğu makineye tünel açmak ayrı
ve bilinçli bir karar olmalı. Ayrıca insan için görsel arayüz, ajan için sorgu API'si değil.

**ENGRAPHIS'E YÜKSELTME TETİĞİ** (his değil, sayı): bir soru **getirme** ile değil **gezinme**
ile cevaplanıyorsa — *"bunu kim çağırıyor"*, *"bu neyi besliyor"*, *"bu sembolü hangi commit
getirdi"* — ve bu **üç kez** tekrarlanmışsa, Engraphis kurulur. Ölçüm: 2026-08-27'de beş
gerçek sorudan yalnız biri o sınıftaydı, o da diller arası olduğu için Engraphis'in de tam
çözmesi şüpheliydi.

### Eski seçenek karşılaştırması (kayıt)

| seçenek | ne getirir | riski |
|---|---|---|
| **Engraphis** | 11 dilde sembol/çağrı/import grafiği, kod↔hafıza, git/PR etki, supersession, yerel SQLite, MCP 29 araç | en ağır; canlı işlem kutusuna yeni bağımlılık |
| **Mnemosyne** | yerel SQLite, `pre_llm_call` kancası, `hermes memory setup` entegre | kod-farkında DEĞİL |
| **Hafif** | `/learn` + skill'ler + `session_search` (FTS5) + `codelaw` artefakt grafiği | sıfır yeni bağımlılık; grafik yok |

## 5. Ölçülmüş kısıtlar

```
sağlayıcı kotası   20/dk · 1.000/gün        →  %0,1'indeyiz, BAĞLAMIYOR
para               usage = 0                →  BAĞLAMIYOR
Meridian AGENT_RPD 150/gün, kullanım 1      →  tek satır config
A1                 4 çekirdek               →  eşzamanlılığı kısıtlar
operatör dikkati                            →  ASIL KISIT
okunmayan çıktı riski                       →  ASIL KISIT (ölçüldü)
```

Model bütçesi: `docs/OLCUM-MODEL-BUTCESI-2026-08-27.md` (Super 131 tok/sn, Ultra 26 tok/sn,
model × çağrı sınıfı → max_tokens/timeout tablosu).

## 6. Hazır parçalar — yazılacak olan az

```
Meridian'da VAR   selfreview.py 519 · nous_eval.py 1098 · agent_telemetry.py 462
                  baseline.py 332 · ops/alarm_backlog_digest.py · watchdog · codelaw
Hermes'te VAR     bot-mode · profil+clone · cron · send (LLM'siz) · mcp serve
                  session_search (FTS5) · /learn · skills.external_dirs
Hub'dan           official/mlops/guidance · instructor (garantili JSON — zayıf model için temel)
                  official/dogfood/adversarial-ux-test (@yabanci'nin düşman modu, yazılmış)
                  official/devops/watchers (watermark dedup) · research/qmd · research/gitnexus-explorer
GERÇEKTEN YAZILACAK   okuma · yorumlama · teslimat katmanı  +  @hipotez'in besleyicisi
```

## 7. Açık kalanlar
- [x] ~~`@kod` zemin seçimi~~ → §4, karara bağlandı
- [ ] Faz 1 teslimat kanalı: Telegram bağlama + bot başına yönlendirme
- [ ] Güvenlik duruşu: `approvals.cron_mode: deny` · `approvals.deny` · `HERMES_WRITE_SAFE_ROOT`
- [ ] Botların depoya yazma yetkisi (soruldu, cevaplanmadı)

## 8. Kaynak: "Learn 95% of Hermes Agent in 31 Minutes" (Sharbel A., 31:28)

Transkriptin tamamı okundu (303 segment). Bağımsız bir kaynak olduğu için ayrı tutuluyor.

**DOĞRULADIKLARI** — bizim analizimize bağımsız destek:
- Hafıza yığını (§4'te alıntılandı). Kod grafiği içermiyor.
- İstisna izleme: *"yalnız önemli bir şey değiştiğinde uyandır… hiçbir şey olmayınca sessiz
  kal, ve yalnız hüküm gerektiğinde token harca."* — `@nobet` için önerdiğimiz desenin aynısı.
- Model kuralı: *"En iyi model hangisi diye sorma; bu model hangi işte iyi olmalı diye sor."*
- Geliştirici/ops işi, ajanın deponun yanında yaşaması: kurulacak ilk ciddi iş akışı olarak
  sayılıyor.

**ÇÜRÜTTÜĞÜ — ve planımız buna göre değişti:**
> *"Mistake six: building profiles before workflows. Do not create five specialist agents
> before you know what those specialist agents are actually here to do."*

Yedi günlük plan da aynı sırayı veriyor: gün 3 **bir** skill · gün 5 KARAR döndüren **bir**
zamanlanmış iş · gün 6 **bir** subagent akışı · gün 7 **İLK** uzman profili.

Karşı argüman tartıldı ve kısmen geçerli: uyarı "ne işe yaradığını bilmeden" diyor, biz ise
rolleri ölçülmüş boşluklara dayandırdık. Ama daha derin nokta ayakta kalıyor — **profil bir
KAPtır**; içine gireceği iş akışı ana profilde kanıtlanmadan kap yapmak, boş kap yapmaktır.
Ve bu, bizim kendi ölçtüğümüz "okunmayan çıktı" arızasıyla aynı yöne bakıyor.

**BİZE ÖZEL UYARI** — hata 3: *"zor iş için en ucuz modeli kullanmak: zayıf model, güçlü
modelin baştan tutacağı parayı yeniden denemelerde harcar."* Ölçümümüz bunun faturası:
7/13 kesilme + 709 `agent_call_empty` + 459 `review_fallback_empty`.

**Diğer hatalar:** (1) çok erken çok araç · (2) her şeyi hafızaya yazmak · (4) her fikri cron
yapmak — *"karar ve çıktı döndürmeyen zamanlanmış iş, bildirim spam'idir"* · (5) subagent
çıktısını doğrulamadan güvenmek · (7) *"iyi talimat, iyi araç, iyi hafıza, iyi skill, iyi
DOĞRULAMA — asıl oyun bu."*

