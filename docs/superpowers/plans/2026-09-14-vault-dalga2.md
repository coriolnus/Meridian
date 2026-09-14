# Vault dalga-2 uygulama planı (repo tarafı — Opus; A1 uygulaması Rol-1)

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development. Steps use `- [ ]`.

**Goal:** Kalan bütün sırları (8 yeni kv girdisi) Vault'a taşıyıp Agent'ın sır-yalnız yan dosyalar (`<dosya>.vault`) render etmesini,
tüketicilerin iki kaynağı birlikte okumasını ve rotasyonun kasadan başlamasını sağlamak.
**Spec:** docs/superpowers/specs/2026-09-14-vault-dalga2-design.md (bağlayıcı).

## Global Constraints
- Envanterde DEĞER YOK; sır değeri argv/ortam/log'a girmez (boru + stdin). `set -x` yok.
- Üretilmiş dosyalar (agent.hcl, policies) elle düzenlenmez; üretici deterministik.
- Agent `exec` yalnız `chown` (sabit argüman listesi); tüketici restart'ı Agent'ta DEĞİL rotasyon aracında.
- ReadWritePaths kümesi envanter hedef dizinlerinden türetilir (çivi); ikinci kopya yok.
- PIT/pitlaw ilgisiz; motor (`meridian/`) dosyasına dokunulmaz → tam suite gerekmez (kapsam + tarama çivileri).

### Task 1 — Envanter + üretici (`deploy/sir_envanteri.yaml`, `ops/vault_politika_uret.py`, üretilen `deploy/vault/agent.hcl` + `policies/*.hcl`)
- [ ] Kırmızı çivi (v491 A-serisi): `vault_kv` 8 yeni ad; `vault_dosyalar` bloğu şeması; referans bütünlüğü; önek; sahip sözlüğü.
- [ ] Envanter yazımı (spec §2) — değer YOK.
- [ ] Üretici: `vault_dosyalar` template blokları + exec chown (ubuntu) + `template_config { static_secret_render_interval = "1m" }` + policy yolları; `--kontrol` bayatlık aynen.
- [ ] Yeniden üret, çivi yeşil, mutasyon (referans/önek/chown).

### Task 2 — Agent birimi + tüketici bağlama (`deploy/vault/vault-agent.service`, docker/hindsight birim drop-in'leri)
- [ ] Kırmızı çivi: ReadWritePaths = envanter dizin kümesi; drop-in'ler (`deploy/oracle-a1/apisix.service.d/…`, hindsight-cp, hindsight-api `EnvironmentFile=-<dosya>.vault`) mevcut mu ve yol envanterle eşit mi.
- [ ] Birim/drop-in yazımı (docker `--env-file` ekleme biçimini mevcut apisix/hindsight-cp birimlerinden ÖLÇ; A0 rolü glob'larına ekle; dagit_vars f9 çiftleri; deploy.sh başlığı — v266).
- [ ] v446 birim şerhleri (saat değeri yok), v485 E-serisi güncel, mutasyon.

### Task 3 — `vault_sir_koy.sh` env_satiri kaynağı + kopya eşitliği kapısı
- [ ] Kırmızı çivi (v485 I/J-serisi genişler): env satırı boruyla okunur (`$(cat` yok), `Bearer ` öneki soyulur, tırnak kırpılır; aynı sırrın diğer kopyalarıyla sha eşitliği — ayrışınca DURUR (adıyla); kuru koşum kasaya dokunmaz.
- [ ] Betik değişikliği + mutasyon.

### Task 4 — `sir_rotasyon.sh --vault` kipi
- [ ] Kırmızı çivi (v447 genişler): `--vault` kipinde değer stdin'den kasaya; render bekleme ≤90 s (sınırlı, adıyla); restart listesi envanter `yeniden_baslat`tan; eski `--esitle` KALIR; kuru koşumda hiçbir komut çağrılmaz.
- [ ] Betik + mutasyon.

### Kapsam koşumu
tests/test_vault_faz2_v485.py tests/test_vault_dalga2_v491.py tests/test_sir_rotasyon_v447.py tests/test_ops_duzeltme_v446.py tests/test_dagit_f9_beyan_v266.py tests/test_bayat_bytecode_v334.py tests/test_review_backlog_v98.py tests/test_kovab_dilim_v382.py tests/test_tests_ops_satir_capasi_v401.py tests/test_yorum_sembol_capasi_v402.py

### A1 (Rol-1, plan dışı adımlar — spec §5): sir_koy → agent restart → render kanıtı → drop-in'ler → docker/hindsight restart (20:05Z sonrası) → canary → iki-kanal dönemi.
