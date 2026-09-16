# DEVİR — başka bir ajan aracına (Codex vb.) geçiş kılavuzu

**Yazıldı:** 2026-09-16 04:5xZ (Rol-1, Claude Code oturumu). **Depo durumu:** `main` = `origin/main` = `68de4ce`, ağaç temiz,
CI yeşil, canlı (A1) `deployed_sha` 59cae52 (dağıtım #51).

Bu belge, depo kurallarını TEKRARLAMAZ — onlar `CLAUDE.md`dedir ve `AGENTS.md` ona **symlink**tir (tek-kaynak yasası:
kopya değil, aynı dosya). Burada yalnız **araca bağlı** olan, yani Claude Code'dan başka bir ajan aracına geçerken
karşılığı aranması gereken şeyler var.

---

## 1. Değişmeyen çekirdek (araçtan bağımsız)

`CLAUDE.md` = anayasa: §0 oturum başı, §2 eylem kapıları, §3 roller/konumlar, §4 yasalar, §5 ölçüm/kart, §6 test ve
**üçlü hüküm**, §7 bekleme yasağı, §8 git, §9 canlı/dağıtım, §12 öncelik. Yeni araç bunları AYNEN uygular; bir kuralı
gevşetmeden önce `MERIDIAN_ENGINEERING_LOG.md`deki `(vaka YYYY-AA-GG)` kaydı okunur.

Kritik üç tanesi, araç ne olursa olsun:
- **Üçlü hüküm** (§6): `grep -E "FAILED|ERROR"` boş + "N passed" özet satırı + dosyadaki `PYTEST_EXIT=0`. Aracın
  "komut başarıyla bitti" bildirimi hüküm DEĞİLDİR.
- **Tam suite yalnız Rol-1'de, donmuş ağaçta, arka planda** (~10–22 dk, `-n 4`).
- **Dağıtım yalnız Rol-1** ve `dagit.sh` her zaman ana checkout'un O ANKİ HEAD'ini iter.

## 2. Araca bağlı olan ve karşılığı aranması gereken şeyler

| Claude Code'da | Ne işe yarıyordu | Codex/başka araçta ne yapılmalı |
|---|---|---|
| `CLAUDE.md` otomatik yükleniyor | Kurallar her oturumda bağlamda | `AGENTS.md` symlink'i aynı dosyayı verir; araç AGENTS.md okumuyorsa ilk mesajda dosya elle okutulur |
| `.claude/` (git-ignore) | settings/izinler, skills, worktree'ler | Yeni araçta karşılığı yok; **kural taşıyan hiçbir şey orada değildir** (vaka 2026-08-26), kayıp yok |
| Superpowers skill'leri (§10) | brainstorming · writing-plans · TDD · systematic-debugging · subagent-driven-development · verification-before-completion | Skill mekanizması yoksa §10 bir **kontrol listesi** olarak elle uygulanır: tasarım→plan→görev başına taze ajan/oturum→inceleme→doğrulama. Akış adı değil disiplin bağlayıcıdır |
| Alt ajan modeli (§3: kod yazan = Opus, inceleme = Sonnet, tavanlar 10/25/40) | Paralel implementer + bağımsız incelemeci | Model adları araca özgüdür; **taşınan kural**: (a) kodu yazan ile inceleyen AYNI bağlam olmaz, (b) incelemeci salt-okur, (c) aynı checkout'ta eşzamanlı pytest yok |
| Git worktree izolasyonu (ajan başına) | Ana ağaç donukken paralel iş | Araç worktree açamıyorsa: iş sıralı yapılır ya da worktree elle açılır (`git worktree add`), **ajan git komutu koşmaz** kuralı korunur |
| Oturum scratchpad'i (`/private/tmp/claude-501/...`) | Ledger, brief'ler, merge zinciri betikleri, kapı listeleri | Repo dışıdır ve YENİ ARACA GEÇMEZ. Kalıcı olması gerekenler zaten `MERIDIAN_ENGINEERING_LOG.md` + `ROADMAP.md`de. Yeni araç kendi çalışma defterini kurar |
| Kalıcı hafıza (`~/.claude/projects/.../memory/`) | 90+ ders kaydı (ihlal sınıfları, tuzaklar) | Araç dışıdır; yeni araç okuyamaz. **Önerilen:** devralan araç `memory/MEMORY.md` indeksini bir kez okuyup kendi hafıza yoluna taşısın ya da kritik olanları `MERIDIAN_ENGINEERING_LOG.md`e künyeleyerek geçirsin |
| Zamanlı uyanışlar (ScheduleWakeup) | Gece vardiyası, dağıtım penceresi, kanıt saatleri | Karşılığı yoksa: saatli kritik iş **A1 systemd timer**'ına taşınır (hafıza dersi: oturum cron'u güvenilmez) ya da operatör tetikler |

## 3. Makine ve erişimler (aynı makinede koşmalı)

| Ne | Yol / komut | Not |
|---|---|---|
| Depo | `$HOME/AI-Trading` | Rol-1 buradadır; başka checkout = yan oturum |
| Python | `.venv/bin/python` (3.12.7) | Her pytest koşumu bununla; sistem python'unda pytest yok |
| Canlı sunucu | `ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87` | A1 komutu HER ZAMAN ssh sarmalı yazılır |
| Dağıtım | `./dagit.sh --dry-run` → `--uygula` | Ansible (`ansible.posix` koleksiyonu kurulu olmalı); temiz ağaç şart |
| GitHub | `gh` CLI (yetkili), `origin git@github.com:coriolnus/Meridian.git` | Push sonrası CI hükmü AYNI turda okunur (§8) |
| Belge eşitleme | `./ops/belge_esitle.sh --uygula` | Tur kapanışında; A1'deki belge kopyasını tazeler |
| Üretilmiş belgeler | `ops/runbook_uret.py --cikti docs/RUNBOOK.md`, `ops/kart_endeksi_uret.py --cikti research/cards/README.md`, tipografi korpusu | Elle düzenlenmez; günlük düzenlemesiyle TEK commit'te |

**Sandbox/izin:** yeni aracın A1'e ssh, `git push`, `gh`, `ansible-playbook` çalıştırabilmesi için ağ ve yazma izni açık
olmalı. Sır DEĞERLERİ hiçbir terminale/loga/argv'ye girmez — yalnız ad/sha basılır (kanal: systemd credential + Vault Agent).

## 4. İki Rol-1 riski (devrin en kritik adımı)

`CLAUDE.md` §3: **iki oturum kendini Rol-1 sayarsa dur, sor.** Ölçülmüş zarar (vaka 2026-08-26): ikisi de commit/suite/dağıtım
başlatır, otoriter suite ortasından kirlenir. Devir sırasında:
1. Eski araç oturumu **kapatılır** ya da açıkça "yan oturum" ilan edilir (git yok, dağıtım yok, tam suite yok).
2. Yeni araç ilk mesajında §0 beyanını yazar: konum (`git rev-parse --show-toplevel`), rol, geçemeyeceği kapılar, CI durumu.
3. Devralma anında `git status` temiz ve `main == origin/main` olmalı (şu an öyle: 68de4ce).

## 5. Devir anındaki açık kuyruk (2026-09-16 05:00Z itibarıyla)

**Zamanlı (operatör girdisi gerekmez):**
- 05:00Z **sabah masası**: günlük `### 2026-09-16 sabah masası` bölümü + RUNBOOK/kart endeksi yeniden üretimi → tek commit → push → `belge_esitle`.
- 06:5xZ **dağıtım #52**: HEAD 68de4ce (TSK-191 alarm eşiği + belgeler) → `--dry-run` (failed=0, `deleting` yok) → `--uygula` → `deployed_sha`/healthz doğrulaması.
- 10:10Z **TSK-138 kanıtı**: bekçi 10:03Z koşumunda `events.jsonl` → `brifing_kural_denetimi.brifing_ilk_satir` dolu mu (dilim-4'ün canlı kanıtı).
- 20:43Z **TSK-191 canlı kanıtı**: akşam döngüsünde `BAYAT TÜREV: self_review.json / arming_report.json` satırlarının SÖNMESİ.

**Takvim kapılı:** 17 Eylül Vault iki-kanal temizliği · 18 Eylül EDG-085 5. taban seansı → 21 Eylül tick pilot bayrağı (kartla) ·
~20 Eylül EDG-2026-089 hükmü (8 Hindsight kalemi + TSK-060/168) · 21 Eylül TSK-162 sayımı · Ekim TSK-137 defter rotasyonu.

**Operatörde (sorulmayacak, yeni kanıt gelene dek):** TSK-065 (Polygon Developer $79) · TSK-176 T2 (OCI müşteri gizli anahtarı) ·
TSK-044/045/084 (FINVIZ/FMP/delist verisi) — hepsi "beklesin" kararlı (2026-09-15).

**Sıradaki sevk edilebilir iş:** EDG-2026-100 (bar arşivi ↔ CSV eşdeğerliği; kart kayıtlı, Opus/implementer dilimi bekliyor).

## 6. Kalıntı / temizlik

- `.claude/worktrees/archify-app-architecture-c14be2` (detached `af02bc3`) — eski, işi bitmiş worktree; yeni araca geçmeden
  `git worktree remove` ile temizlenebilir (içinde commit'lenmemiş iş olmadığı doğrulanmalı).
- `state/trades.jsonl.migrated` — canlı işlem defteri SQLite'a göçtü; EDG-095 tetiği bu yüzden `shadow_trades.jsonl`den
  değil, göç sonrası canlı yoldan ölçülür.
