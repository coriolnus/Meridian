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

## 2. İlk dalga: 7 bot

Seçim ölçütü "en faydalı yedi" değil, **birbirinden en farklı yedi** — her biri ayrı bir
mimari kalıbı kanıtlar ve dört amacın hepsi kapsanır.

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

## 3. Fazlar

**Faz 0 — tesisat** *(iki arka plan görevi koşuyor)*
- uydurma maliyet: `price_for()` `:free` modelleri tanımıyor, Opus fiyatına düşüyor
- `max_tokens` + `timeout` birlikte: ölçüm `docs/OLCUM-MODEL-BUTCESI-2026-08-27.md`

**Faz 1 — `@kod` **VE** var olanı teslim et** *(paralel, çakışmıyorlar)*
- `@kod`: okuma tarafını kurar. Talep üzerine, bildirim üretmez, tüketicisi garantili.
- Teslimat: 310 alarm · `self_review.json` · `improvement_proposals.jsonl` (16 öneri) —
  hepsi HESAPLANMIŞ, hiçbiri teslim edilmemiş. `ops/alarm_backlog_digest.py` yazılmış, koşmuyor.

**Faz 2 — kalan altı bot.** Zincir kanıtlandıktan sonra, `@kod` zemininin üstünde.

## 4. AÇIK KARAR — `@kod`un zemini

Tek kalan tasarım sorusu.

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
- [ ] `@kod` zemin seçimi (§4)
- [ ] Faz 1 teslimat kanalı: Telegram bağlama + bot başına yönlendirme
- [ ] Güvenlik duruşu: `approvals.cron_mode: deny` · `approvals.deny` · `HERMES_WRITE_SAFE_ROOT`
- [ ] Botların depoya yazma yetkisi (soruldu, cevaplanmadı)
