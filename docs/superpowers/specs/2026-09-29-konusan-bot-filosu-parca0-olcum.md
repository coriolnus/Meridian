# Konuşan bot filosu — Parça 0 ölçüm raporu (bekçi ikizi, A1)

**Plan:** `docs/superpowers/plans/2026-09-29-konusan-filo-parca0-deneme.md` · **Spec:** `docs/superpowers/specs/2026-09-29-konusan-bot-filosu-design.md` §6
**Koşumlar:** v1 2026-09-29 20:20Z (operatör) · v2 2026-09-29 22:12Z (Rol-1, operatörün gece yetkisiyle) · betikler `~/Documents/Claude/meridian-parca0/`
· A1 çıktıları `~/deneme-botlar/sonuc.txt`, `sonuc_v2.txt`, arşiv `~/deneme-botlar/arsiv/` (kalıcı silme yok; Hindsight bankası `bot-deneme-bekci` kayıt olarak kalır).

## Hüküm: DUR → operatör (spec §6: (b) geçmeden Parça 1b açılmaz)

(a) GEÇTİ · (b) ÖLÇÜLEMEDİ — kök neden bulundu, düzeltme bir operatör kararı (aşağıda K-1).

## Sonuçlar

| # | Soru | Sonuç | Kanıt |
|---|---|---|---|
| a | İzin listesi yapısal mı (komut/dosya/web yok) | **GEÇTİ** | `/v1/toolsets`: 26 yerleşik takımın 26'sı kapalı, açık takım yok; enjeksiyon istemine bot "terminal/web araçlarım yok" dedi; oturumda `tool_calls` yok. Geçersiz izin listesi adı Hermes'te AÇIK DEĞİL KAPALI düşüyor + WARNING (`tools_config._get_platform_tools`, #38798) — fail-closed |
| b | Ücretsiz zincir araç çağırabiliyor mu | **ÖLÇÜLEMEDİ** | Model hiç araç görmedi (`tool_turns=0`, girdi 2.684 jeton). KÖK NEDEN: Hermes venv'inde `mcp` paketi YOK (`tools.mcp_tool._MCP_AVAILABLE=False`) → `discover_mcp_tools()` sessizce `[]` (yalnız DEBUG). `meridian.mcp_server` tek başına sağlam (initialize + 6 araç listelendi). Model araç yerine düz metin sahte çağrı yazdı (`{"name": "skill_view", …}`) |
| c | Küçük bankada recall süresi | **GEÇTİ** | 16 sonuç · low 4,2 s · mid 2,4 s (tavan 10 s); boş bankada 0,2–0,4 s |
| d | Zamanlı rapor yolu (`-z`) hafızaya yazıyor mu | **YAZMIYOR** | Sohbet yolu bankaya yazdı (`LACİVERT-KUTUP` 2), `-z` koşumu yazmadı (`ZAMANLI-YOL-İZİ` 0, `z_cikis=0`, hata satırı 0). `-z`nin hafızadan OKUYUP okumadığı ölçülmedi |
| e | Ham araç çıktısı hafızaya sızıyor mu | **ÖLÇÜLEMEDİ** | Araç çağrılmadığı için sızacak çıktı yoktu (ham anahtar sayıları 0 — anlamsız). Tasarım: `sync_turn(user, assistant)` yalnız iki metni alır |
| f | "Unut" yöntemi | **ÖLÇÜLDÜ** | Hindsight: `POST/PATCH/DELETE …/directives`, `PATCH …/memories/{id}`, `GET …/tags`, `GET …/memories/list`; yumuşak "unut" yönerge ya da bellek PATCH ile (kalıcı silme gerekmez) |
| g | Günlük LLM çağrı sayısı | **ÖLÇÜLEMEDİ** | APISIX erişim kaydı konteyner içinde; büyük dosyada grep ssh kopmasıyla düştü (4 asılı grep süreci — 0 CPU; operatör kapatır). Sayaç Parça 1a `bot_sohbet.jsonl`den gelecek |
| h | Bot sunucusu belleği | **ÖLÇÜLDÜ** | tek profil, boşta ~170–173 MB RSS |
| — | Hafızadan geri çağırma | **ÖLÇÜLEMEDİ** | Bot "hafızam sıfırlanır" dedi — bekçi SOUL'u "hafızan yok, dünü görmezsin" diyor (rapor kipi için doğru); sohbet kipi SOUL bölümü Parça 1b işi |
| — | Model hafıza aracı görüyor mu | **GÖRMÜYOR** | `memory_mode: context` → `get_tool_schemas()` `[]` (kaynak okundu); günlükteki "registered (3 tools)" kayıt, modele açılım değil |
| — | Telegram/başka platform açıldı mı | **HAYIR** | yalnız api_server; ortam dosyalarında platform jetonu yok |
| — | İstek dökümü | v1: 401'lerde yazıldı (anahtarsız) · v2: 0 | İçerik denetimi sınıflandırıcıda engellendi → Parça 1b koşulu |

## Bu ölçümün kendi hataları (dürüst kayıt)
- v1: ikiz profile `.env` kopyalanmadığı için botun model kapısı anahtarı `BOT_KEY_BEKCI` eksikti → her model çağrısı APISIX'ten 401; ilk teşhisim
  "api_server anahtarı" idi, günlüğün "API call failed (attempt 1/3)" satırı AJANIN model çağrısı olduğunu gösterdi. v1 temizliğinde sunucu kapanmadan arşive
  taşındı → kapanış artığı klasörü yeniden yarattı (v2 başında arşive alındı).

## Operatör kararları (sabah)
- **K-1 — Hermes'e `mcp` paketini kurmak** (`hermes-agent[mcp]` ekstrası: `mcp==1.26.0` + `starlette==1.3.1`, CVE yamalı). ETKİ (ölçüldü): canlı VARSAYILAN
  profil `~/.hermes/config.yaml` `mcp_servers: [meridian]` taşıyor → kurulunca varsayılan profili kullanan yollar (öğrenme döngüsü, bileşik ön-eleme, pano
  "düşün") Meridian MCP araçlarını İLK KEZ görür — öğrenme boru hattında ölçülmemiş bir davranış değişikliği. Üç bot profilinde `mcp_servers` YOK (etkilenmez).
  Seçenekler: (i) kur + varsayılan profildeki `meridian` girdisine `enabled: false` (bot profilleri kendi izin listesiyle açar) — davranış değişmez; (ii) kur ve
  varsayılan profilin de kullanmasına izin ver (tasarım niyeti `meridian/mcp_server.py` başlığında; ayrı ölçüm); (iii) kurma — mimari yedek yola (pano sohbet
  motoru taşıyıcı) döner. Rol-1 önerisi: (i). Kurulumdan sonra deneme v3 yalnız (b)+(e)+hafızadan geri çağırma için.
- **K-2** — A1'deki 4 asılı grep süreci (tek satır, v1 raporunda).

## Parça 1b'ye taşınan koşullar
Sohbet kipi SOUL bölümü (hafıza var, tarihli atıf, bugünü araçtan) · istek dökümü dosyalarının kapatılması/izni · `-z` yolunun hafızadan OKUMADIĞININ ölçümü ·
kota sayacı (`bot_sohbet.jsonl`) · deneme model çağrıları APISIX'te bekçinin tüketici kimliğiyle sayıldı (yeni bot = yeni APISIX tüketicisi + BOT_KEY).
Ölçüm kartı (plan Görev 8, EDG-2026-107) hafızadan geri çağırma ölçülmeden yazılmadı (ADIM-0 eksik; kural: kill eşiği ADIM-0'da ölçülür).
