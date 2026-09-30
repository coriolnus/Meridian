#!/usr/bin/env python3
"""ops/sohbet_profili_uret.py — her aktif bot için SOHBET profilini rapor profilinden ÜRET (Parça 1b G2) + bot ağ
geçidinin KÖK (varsayılan) profilini (G3).

NEDEN VAR. Konuşan filonun her botu iki kipte koşar: zamanlanmış RAPOR (`deploy/hermes/profiles/<ad>/`,
hafızasız, kendi systemd birimi) ve operatörün sorusuna cevap veren SOHBET (`deploy/hermes/sohbet/profiles/<ad>/`,
ayrı Hermes kökünde çoklu ağ geçidi). Parça 0 v3 ölçümü: rapor yolu (`-z`) hafızaya YAZABİLİYOR, yani tek
profil iki işi göremez — ikiz zorunlu. İkizi elle yazmak ise bu deponun baskın arızasını çağırır: aynı duruşun
(guard kancası, onay, kapalı takımlar, model, kapı sağlayıcısı) iki kopyası sessizce ayrışır ve bayatlayan
taraf hep okunmayan taraf olur. Bu betik ikizi TÜRETİR; duruş rapor profilinde yaşar, burada kopyalanmaz.

TEK KAYNAK:
  * duruş ve rapor SOUL'u   → `deploy/hermes/profiles/<ad>/` (`config.yaml`, `SOUL.md`, `distribution.yaml`;
                               manifestten yalnız sürüm tabanı ve kapı anahtarının adı/zorunluluğu —
                               açıklamalar sohbet kipine özgü sabitlerdir)
  * Meridian MCP girdisi     → `deploy/hermes/config.yaml` içindeki mcp_servers → meridian girdisi
                               (`enabled` true olur, argümanlara `--bot <ad>` eklenir, `env:`e birimin credential
                               yolu eklenir)
  * kök (varsayılan) profil  → duruşu `deploy/hermes/profiles/sef/` (kanca, onay, kapalı takımlar, model,
                               sağlayıcılar); çoklu kip, boş platform izin listesi ve yönlendirme SOUL'u bu
                               modülün sabitleri (G3)
  * bot ağ geçidi            → birim adı, ortak kum havuzu ve Hermes kökü BU MODÜLÜN sabitleri (`BOT_BIRIMI`,
                               `BOT_KUM_HAVUZU`, `KOK_DIZIN`; G3)
  * hangi bot, hangi araç    → `deploy/hermes/kadro.yaml` (`meridian.kadro`; yalnız `aktif` satırlar)
  * Hindsight bağlantısı     → kanal katmanının sabitleri: kök URL `meridian.secrets` (HAFIZA_TABAN_URL),
                               zaman aşımı ve recall bütçesi `meridian.bot_hafiza` (spec §3.4 HINDSIGHT_*)
                               — TÜRETİLİR; banka öneki `bot-<ad>` bot_hafiza'nın banka yoluyla v599
                               ayrışma çivisinde bağlı (önek orada sabit değil)
  * sohbet farkları          → BU MODÜLÜN sabitleri (model zaman aşımı, yeniden deneme, Hindsight kipi,
                               SOUL sohbet bölümü) — başka yerde yazılmaz.

KOMUT SATIRI SÖZLEŞMESİ (ops aracı sözleşmesi KOMUT SATIRIdır, `main()` değil):

    python ops/sohbet_profili_uret.py --yaz       # üret ve yaz (yalnız içeriği değişen dosyaya dokunur)
    python ops/sohbet_profili_uret.py --kontrol   # yazMA; diskteki dosyalar güncel mi

Çıkış kodu HÜKÜMDÜR:
    0  yazıldı (`--yaz`) / güncel (`--kontrol`)
    1  BAYAT (yalnız `--kontrol`) — ayrışan/eksik/fazla dosyalar stdout'a, satır başına bir tane
    2  KULLANIM hatası — `--yaz` ile `--kontrol` birlikte ya da hiçbiri (sessiz öncelik kuralı YOK: biri
       SORAR, öteki YAZAR; biri ötekini yutarsa operatör "yazdım" sanır — `ops/jeton_css_uret.py` emsali)

SİLMEZ. Kadroda `aktif`ten çıkan botun sohbet profili SİLİNMEZ, `--kontrol` onu "fazla" diye ADIYLA raporlar
(ve `--yaz` da uyarır). Silme bir karardır, üretecin yan etkisi değil.

RAPOR PROFİLLERİNE YAZMAZ. Yalnız `deploy/hermes/sohbet/**` yazılır (kök profil + sohbet profilleri); o dizinin
tamamı üretecindir — orada üretilmemiş her dosya `--kontrol`de "fazla"dır.

DETERMİNİSTİK: aynı kaynaktan aynı bayt çıkar (sözlük sırası sabit, zaman damgası YOK) — damga olsaydı her
koşum fark üretir ve `--kontrol` kapısı anlamsızlaşırdı.

SIR YOK: hiçbir sır değeri okunmaz, yazılmaz, basılmaz. `hindsight/config.json`da anahtar alanı YOKTUR (değer
profilin `.env`indeki `HINDSIGHT_API_KEY`dir: çoklu kipte sırlar PROFİL `.env`inden okunur, süreç ortamına düşmez);
profil `.env`i üretilmez. MCP `env:`indeki `CREDENTIALS_DIRECTORY` bir YOLdur, değer değil.

`meridian.obs`'A ULAŞMAZ: ithal edilenler `meridian.kadro`, `meridian.secrets`, `meridian.bot_hafiza` (+ onun
`meridian.notify`u); modül düzeylerinde yalnız sabit ve `re.compile` var, `obs` yalnız `meridian.config`in
fonksiyon gövdelerinde ve üreteç onları çağırmaz (`-X importtime` ile ölçüldü, 2026-09-30). Pytest dışı koşum
canlı yerel deftere yazmaz; sır dosyası da OKUNMAZ (bu modüllerden yalnız sabitler okunur).

OKUYUCU (Yasa 6): üretilmiş dosyalar Hermes çoklu ağ geçidinin (`BOT_BIRIMI`, kökü `KOK_DIZIN`) kök ve profil
evleridir; tazelik kapısı `--kontrol` ve `tests/test_sohbet_profili_uret_v599.py`dir.
"""
from __future__ import annotations

import argparse
import copy
import json
import pathlib
import sys

import yaml

REPO = pathlib.Path(__file__).resolve().parents[1]
# `python ops/sohbet_profili_uret.py` depo kökünden koşulur ve o hâlde kök `sys.path`te değildir. Kök BAŞA
# eklenir: kurulu (düzenlenebilir) paket başka bir checkout'u gösterebilir; üreteç KENDİ ağacının kadro
# modülünü okumalı.
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from meridian import bot_hafiza, kadro as kadro_mod, secrets  # noqa: E402  (kök sys.path'e eklendikten sonra)

#: Bot ağ geçidinin Hermes kökünün depo aynası: kök (varsayılan) profil dosyaları doğrudan burada, sohbet
#: profilleri `profiles/` altında. Dizinin tamamı üretecindir.
SOHBET_EV = "deploy/hermes/sohbet"
SOHBET_KOK = f"{SOHBET_EV}/profiles"
RAPOR_KOK = "deploy/hermes/profiles"
KOK_YAPILANDIRMA = "deploy/hermes/config.yaml"
KADRO_DOSYASI = "deploy/hermes/kadro.yaml"

#: --- BOT AĞ GEÇİDİ (G3; ölçüm kaynağı: G3 planının Architecture bölümü, A1 Hermes v0.19.0, 2026-09-30) ---
#: Tek Hermes ağ geçidini çoklu kipte koşan systemd birimi. Credential yolu bu ADDAN türer (`BOT_CREDENTIAL_DIZINI`):
#: birim yeniden adlandırılıp yol unutulursa `bot_hafizasi_ara` sessizce "credential yok" döner.
BOT_BIRIMI = "meridian-botlar.service"
#: MCP alt süreç ortamı SÜZÜLÜR (izinli küme + config `env:`) → birimin `CREDENTIALS_DIRECTORY`si MCP sunucusuna
#: geçmez; sohbet profilinin MCP `env:`ine systemd'nin bu birim için kurduğu sabit yol yazılır.
BOT_CREDENTIAL_DIZINI = f"/run/credentials/{BOT_BIRIMI}"
#: `HERMES_WRITE_SAFE_ROOT` SÜREÇ başına okunur → tek ağ geçidinde bot başına kum havuzu İMKÂNSIZ. BEYANLI sapma:
#: bütün sohbet profilleri bu ortak kum havuzunu paylaşır (dosya/terminal takımları zaten kapalı — ikinci katman);
#: rapor kum havuzlarından ayrıdır.
BOT_KUM_HAVUZU = "/opt/meridian/var/bots/sohbet"
#: Ağ geçidinin Hermes kökü (`HERMES_HOME`): `~/.hermes` DIŞINDA olduğu için kendi başına köktür; `SOHBET_EV` onun
#: depo aynasıdır.
KOK_DIZIN = "/home/ubuntu/.hermes-botlar"
#: Kök profilin duruşunu (kanca, onay, kapalı takımlar, model, sağlayıcılar) miras aldığı rapor profili.
KOK_DURUS_PROFILI = "sef"
#: Kök profilin rapor profilinden aldığı üst düzey anahtarlar — BEYAZ LİSTE: rapor profiline ileride eklenen bir
#: blok (hafıza, MCP) araçsız/hafızasız köke sızmasın. Miras alınan anahtar BÜTÜN olarak kopyalanır (alt anahtarlar
#: kendiliğinden yayılır).
KOK_MIRAS_ANAHTARLARI = ("hooks", "hooks_auto_accept", "agent", "approvals", "model", "providers")
#: BEYANLI İSTİSNA — rapor profilinde bulunsa da köke GEÇMEYEN üst anahtarlar: kök bunları kendisi kurar (çoklu
#: kip, boş izin listesi) ya da hiç taşımaz (hafıza, MCP girdisi). Kaynağın bu iki kümenin hiçbirinde olmayan bir
#: üst anahtarı v599 yön çivisinde öter: yeni bir duruş anahtarı köke SESSİZCE eksik kalmaz, bir karar ister.
KOK_MIRAS_DISI = ("mcp_servers", "memory", "platform_toolsets", "platforms", "gateway")
#: `/p/` öneksiz istek kök profile düşer; araçsız model veri UYDURUR (Parça 0). SOUL yalnız yönlendirme cümlesi
#: yazdırır ve hiçbir yetenek (araç, hafıza) vaat etmez.
KOK_SOUL = ("Bu, Meridian bot ağ geçidinin kök profilidir. Bu uç doğrudan kullanılmaz; her soru `/p/<bot>/` "
            "önekiyle bir bota gider. Buraya gelen her mesaja yalnız şunu yaz: Bu kök profil; lütfen bir bot seçin.\n")

#: Model çağrısı başına istek zaman aşımı (sn) — Hermes'in OKUDUĞU yerde yazılır: sağlayıcı girdisinin
#: `request_timeout_seconds` alanı (kökte `timeout` anahtarı YOK; v329 emsali). Parça 0 v3: ücretsiz model
#: çağrı başına ~5 dk asıldı ≈ 3 deneme × 120 sn; 2 × 60 sn en kötü ~2 dk (G4 ara bildirimi bu süreyi karşılar).
SOHBET_ISTEK_ZAMAN_ASIMI_SN = 60
#: `agent.api_max_retries` — Hermes v0.19 varsayılanı 3 (`agent/agent_init.py`).
SOHBET_API_DENEME = 2
#: Sohbet çağrı bütçesi: rapor duruşunun ÜZERİNE yazılan yaprak yollar ve değerleri — TEK KAYNAK. Hem yazım
#: (`_sohbet_cagri_butcesi`) hem de kökün rapor profilinden BİLİNÇLİ farkları (v599 yön çivisinin istisnası) buradan.
#: Zaman aşımı `custom` (kapı sağlayıcısının çözümlendiği ad) ve `openrouter` (geri dönüş evi) girdilerine yazılır.
SOHBET_BUTCESI: dict[tuple[str, ...], int] = {
    ("agent", "api_max_retries"): SOHBET_API_DENEME,
    ("providers", "custom", "request_timeout_seconds"): SOHBET_ISTEK_ZAMAN_ASIMI_SN,
    ("providers", "openrouter", "request_timeout_seconds"): SOHBET_ISTEK_ZAMAN_ASIMI_SN,
}

#: Üretilmiş her dosyanın beyanı (YAML'da baş yorum, JSON'da `_uretildi` alanı).
URETILDI = "ÜRETİLMİŞ — elle düzenlenmez; üreteç `ops/sohbet_profili_uret.py`"

#: Hindsight anahtar kümesi Parça 0 v3'te ÖLÇÜLEREK çalıştı. `memory_mode: context` → hafıza bağlam olarak gelir,
#: modele hafıza ARACI açılmaz. Bağlantı gerçekleri (kök URL, zaman aşımı, recall bütçesi) burada YAZILMAZ —
#: `_hindsight` onları kanal katmanının sabitlerinden türetir (tek kaynak; dal sonu I-2).
#:
#: OTOMATİK KAYIT KAPALI (dal sonu I-1, Rol-1 seçenek A): Hermes'in `auto_retain`i sohbet dönüşünü
#: `notify.scrub`'dan GEÇİRMEDEN kalıcı, silinemez bankaya yazar (spec §3.4 "kayıt öncesi scrub"; `unut`
#: yumuşaktır) — operatörün mesajındaki bir jeton her sonraki turda recall ile dış modele geri giderdi. Sohbet
#: dönüşünü hafızaya YAZAN TEK TARAF kanal katmanıdır (`bota_sor` → `bot_hafiza`, scrub'lı; G4). Hatırlama açık
#: kalır: banka yalnız scrub'lı içerik taşır. BEDEL: G4'e kadar sohbet dönüşleri hafızaya hiç yazılmaz.
#: `retain_*` anahtarları BIRAKILDI: yerel Hermes v0.18.2 kaynağında (plugins/memory/hindsight) otomatik kayıt
#: kapalı + `context` kipte hiçbir yazım yolu onları kullanmaz ve recall süzgeci ayrı anahtardır (`recall_tags`);
#: canlı v0.19.0 ÖLÇÜLMEDİ — bir yazım yolu varsa etiket/kaynak atfı korunmuş olur, yoksa zararsızdır.
HINDSIGHT_OTOMATIK_KAYIT = False
HINDSIGHT_OTOMATIK_HATIRLAMA = True

#: Manifest `env_requires` — kapı anahtarının ADI ve `required` alanı rapor manifestinden gelir (aynı APISIX
#: tüketicisi); AÇIKLAMA sohbet kipine özgüdür: rapor açıklaması rapor düşüş yolunu anlatır ve kurulu profilin
#: `.env.EXAMPLE`ını okuyan operatörü rapor akışına yönlendirir (Rol-1 Tur 2).
SOHBET_KAPI_ANAHTARI_ACIKLAMASI = (
    "Kapı anahtarı — rapor profiliyle AYNI APISIX tüketicisi. Sohbet profili bu anahtarla model çağırır; değer "
    "profilin kendi .env dosyasında durur, depoya yazılmaz. Anahtar yoksa ya da yanlışsa kapı 401 döner ve bot "
    "sohbet cevabı veremez.")
SOHBET_YAZMA_KOKU_ACIKLAMASI = (
    "Ağ geçidinin yazabileceği tek dizin; tanımsız değişken sınırsız yazma demektir. Değişken süreç başına okunur, "
    "bu yüzden tek ağ geçidindeki bütün sohbet profilleri bu ortak kum havuzunu paylaşır; dosya ve terminal "
    "takımları zaten kapalıdır.")
SOHBET_HAFIZA_ANAHTARI_ACIKLAMASI = (
    "Hindsight kiracı anahtarı; değer profilin kendi .env dosyasında durur (çoklu ağ geçidinde sırlar profilin "
    ".env dosyasından okunur), depoya yazılmaz.")

SOHBET_BOLUMU_BASLIGI = "## Sohbet kipi"
#: Açılış bir ÖNCELİK kuralıdır, sıra değil: bölüm rapor metninin SONUNA eklenir, çelişkide bölüm geçerlidir
#: (Rol-1 Tur 2 — "önce gelir" konumsal olarak yanlış okunabiliyordu).
_ACILIS = (
    SOHBET_BOLUMU_BASLIGI,
    "",
    "Bu bölüm yukarıdaki rapor talimatlarıyla çelişirse bu bölüm geçerlidir. Burada zamanlanmış bir rapor "
    "yazmıyorsun: operatörün sorusuna cevap veriyorsun.",
    "",
)
#: Rapor SOUL'ları "araçların yok", "hafızan yok", "deftere kendin bakamazsın" der; sohbette bu cümleler aracı
#: reddettirebilir. Ezme maddesi YETENEĞİ MEKANİZMAYA BAĞLAR: araç listesi boş botta "araçların var" denmez.
_EZME_ARACLI = ("- Yukarıda araçların ya da hafızan olmadığı yazıyorsa, o cümleler zamanlanmış rapor içindir. "
                "Bu kipte Meridian araçların ve geçmiş konuşmalarından gelen notlar var.")
_EZME_ARACSIZ = "- Bu kipte geçmiş konuşmalarından gelen notlar var; aracın yok."
_BOLUM_BASI = (
    #: Rapor biçimi ve uzunluk payları (ör. karne'nin karakter payı) sohbet cevabını kırpmasın.
    "- Rapor biçimi ve uzunluk kuralları (karakter payı, bölüm düzeni) bu kipte uygulanmaz.",
    "- Bugünün durumu hakkında yalnız araçlarından gelen veriyle konuş. Araç çağırmadan hiçbir sayı, yüzde, "
    "sembol ya da kaynak yazma.",
    "- Aracın yoksa ya da araç cevap vermediyse bilmediğini söyle ve nedenini yaz. Araç sonucu uydurma; "
    "çağırmadığın bir aracın adını anma.",
    "- Geçmiş konuşmalarından notlar bağlam olarak gelebilir. Oradan aktardığın her şeyin tarihini ver ve onu "
    "bugün için hüküm sayma.",
    "- Ayar değiştiremez, komut çalıştıramazsın.",
)
#: Koşullu satırlar: SOUL botun kadroda OLMAYAN aracını vaat ederse model yeteneği uydurur — satır yalnız araç
#: kadrodaysa (ve başka botların hafızası için hafıza kipi `hepsi` ise) yazılır. Karar `_vaat_edilir`de.
_KOSULLU_SATIRLAR = (
    ("oneri_yaz", "- Bir değişiklik gerekiyorsa oneri_yaz aracıyla öneri yaz; onayı operatör verir."),
    ("is_iste", "- Bir raporun yeniden üretilmesi gerekiyorsa is_iste aracıyla iste; işi Meridian koşar."),
    ("bot_hafizasi_ara", "- Başka bir botun geçmiş konuşmalarına bot_hafizasi_ara aracıyla bakabilirsin; oradan "
                         "aktardığın her şeyin hangi bota ve hangi tarihe ait olduğunu yaz."),
)
#: Rapor SOUL'undaki tek başına şablon satırı sohbette uygulanırsa bot soruya o jetonla cevap verir — bölüm onu
#: cümle içinde AÇIKÇA geçersiz kılar (tek başına satır olarak YAZILMAZ).
_BOLUM_SONU = (
    "- Bu kipte SESSIZ yazmazsın: her soruya cevap verirsin.",
    "- Kısa yaz; birkaç paragrafı geçme.",
)


def _yaml_oku(yol: pathlib.Path) -> dict:
    veri = yaml.safe_load(yol.read_text(encoding="utf-8"))
    if not isinstance(veri, dict):
        raise ValueError(f"{yol}: YAML bir eşleme değil ({type(veri).__name__}) — sohbet profili türetilemez")
    return veri


def _yaml_yaz(baslik: tuple[str, ...], veri: dict) -> bytes:
    govde = yaml.safe_dump(veri, allow_unicode=True, sort_keys=False)
    return ("".join(f"# {s}\n" for s in baslik) + govde).encode("utf-8")


def _vaat_edilir(bot: kadro_mod.Bot, arac: str) -> bool:
    return arac in bot.araclar and (arac != "bot_hafizasi_ara" or bot.hafiza == "hepsi")


def sohbet_bolumu(bot: kadro_mod.Bot) -> str:
    """Botun SOUL'una eklenen sohbet bölümü — sabit metin + araç listesine bağlı ezme maddesi + yalnız kadrodaki
    araçlar için koşullu satırlar."""
    ezme = _EZME_ARACLI if bot.araclar else _EZME_ARACSIZ
    kosullu = tuple(satir for arac, satir in _KOSULLU_SATIRLAR if _vaat_edilir(bot, arac))
    return "\n".join(_ACILIS + (ezme,) + _BOLUM_BASI + kosullu + _BOLUM_SONU) + "\n"


def _kadro(kok: pathlib.Path, kadro) -> tuple[kadro_mod.Bot, ...]:
    return kadro_mod.aktif_botlar(kadro if kadro is not None else kadro_mod.kadro_yukle(kok / KADRO_DOSYASI))


def _sohbet_cagri_butcesi(cfg: dict, kaynak: str) -> None:
    """Sohbet ağ geçidinde çağrılan her profile (kök dahil) sohbet zaman aşımı ve yeniden deneme sayısı — YERİNDE."""
    if not isinstance(cfg.get("agent"), dict):
        raise ValueError(f"{kaynak}: 'agent' eşlemesi yok — duruş (kapalı takımlar) miras alınamaz")
    for yol, deger in SOHBET_BUTCESI.items():
        hedef = cfg
        for parca in yol[:-1]:
            hedef = hedef.setdefault(parca, {})
        hedef[yol[-1]] = deger


def _config(rapor_evi: pathlib.Path, bot: kadro_mod.Bot, kok_meridian: dict) -> bytes:
    cfg = copy.deepcopy(_yaml_oku(rapor_evi / "config.yaml"))
    girdi = copy.deepcopy(kok_meridian)
    cfg["mcp_servers"] = {"meridian": {
        **girdi, "enabled": True, "args": list(girdi["args"]) + ["--bot", bot.ad],
        # Değişken ADI okuyucunun sabitinden (`secrets.credential_oku` onu okur): ad ayrışırsa araç sessizce
        # "credential yok" döner — literal yazılmaz (tek kaynak).
        "env": {**(girdi.get("env") or {}), secrets.CREDENTIAL_DIZIN_ENV: BOT_CREDENTIAL_DIZINI}}}
    cfg["platform_toolsets"] = {"api_server": ["meridian"]}
    # İkincil profil dinleyici AÇMAZ: süreç ortamındaki dinleyici anahtarı aksi hâlde burada da dinleyici açmaya
    # zorlar ve ağ geçidi açılışta düşer (çoklu kip yapılandırma hatası). Dinleyiciyi kök profil tutar.
    cfg["platforms"] = {"api_server": {"enabled": False}}
    cfg["memory"] = {"provider": "hindsight"}
    _sohbet_cagri_butcesi(cfg, f"{rapor_evi}/config.yaml")
    baslik = (
        URETILDI + ".",
        f"Kaynak: {RAPOR_KOK}/{bot.ad}/config.yaml (duruş: kanca, onay, kapalı takımlar, model, sağlayıcılar —",
        f"gerekçeleri orada) + {KOK_YAPILANDIRMA} içindeki mcp_servers → meridian girdisi (--bot {bot.ad} ekiyle)",
        "+ üretecin sohbet sabitleri (zaman aşımı, yeniden deneme, hafıza sağlayıcısı, platform izin listesi,",
        f"ikincil profilde api_server kapalı, MCP credential yolu {BOT_CREDENTIAL_DIZINI}).",
        "Değiştirmek için kaynağı düzenle ve üreteci --yaz ile koş; tazelik kapısı --kontrol.",
    )
    return _yaml_yaz(baslik, cfg)


def _kok_config(kok: pathlib.Path) -> bytes:
    """Bot ağ geçidinin kök (varsayılan) profili: dinleyiciyi tutar, çoklu kipte sohbet profillerini `/p/<ad>/`
    altında sunar. ARAÇSIZ (boş platform izin listesi, MCP girdisi yok) ve HAFIZASIZ (hafıza sağlayıcısı yok):
    `/p/` öneksiz bir istek buraya düşer ve araçlı/hafızalı bir kök veri uydururdu (Parça 0). Duruş rapor
    profilinden BEYAZ LİSTEYLE miras alınır — kök de aynı süreçte koşar."""
    kaynak = kok / RAPOR_KOK / KOK_DURUS_PROFILI / "config.yaml"
    rapor = _yaml_oku(kaynak)
    eksik = [a for a in KOK_MIRAS_ANAHTARLARI if a not in rapor]
    if eksik:
        raise ValueError(f"{kaynak}: kök profilin duruşu için {eksik} yok — kök profil türetilemez")
    cfg = {a: copy.deepcopy(rapor[a]) for a in KOK_MIRAS_ANAHTARLARI}
    _sohbet_cagri_butcesi(cfg, str(kaynak))
    cfg["gateway"] = {"multiplex_profiles": True}
    cfg["platform_toolsets"] = {"api_server": []}
    baslik = (
        URETILDI + ".",
        "Bot ağ geçidinin KÖK (varsayılan) profili.",
        f"Birim {BOT_BIRIMI}, Hermes kökü {KOK_DIZIN} (bu dosya oranın config.yaml'ıdır).",
        "Dinleyiciyi bu profil tutar; sohbet profilleri çoklu kipte /p/<ad>/ altında sunulur. ARAÇSIZ ve HAFIZASIZ:",
        "/p/ öneksiz istek buraya düşer ve araçlı ya da hafızalı bir kök veri uydururdu — platform izin listesi boş,",
        "Meridian MCP girdisi ve hafıza sağlayıcısı YOK; SOUL yalnız yönlendirme cümlesi yazdırır.",
        "Kökün .env'ine model anahtarı (providers.kapi.key_env) BİLİNÇLİ konmaz: öneksiz istek kapıda 401 ile düşer",
        "(model çağrılmaz — uydurma yok, kota yok); SOUL'daki ret cümlesi ikinci katmandır (Rol-1 hükmü, 2026-09-30).",
        f"Kaynak: {RAPOR_KOK}/{KOK_DURUS_PROFILI}/config.yaml (duruş: kanca, onay, kapalı takımlar, model,",
        "sağlayıcılar — gerekçeleri orada) + üretecin sabitleri (zaman aşımı, yeniden deneme, çoklu kip).",
        "Değiştirmek için kaynağı düzenle ve üreteci --yaz ile koş; tazelik kapısı --kontrol.",
    )
    return _yaml_yaz(baslik, cfg)


def _hindsight_zaman_asimi() -> int:
    """`bot_hafiza.HAFIZA_ZAMAN_ASIMI_S` → Hermes eklentisinin tamsayı `timeout`u. Eklenti değeri `int()` ile
    okur (yerel v0.18.2 `_parse_int_setting`): kesirli bir değer SESSİZCE kırpılırdı — o yüzden açık hata."""
    deger = bot_hafiza.HAFIZA_ZAMAN_ASIMI_S
    if isinstance(deger, bool) or not isinstance(deger, (int, float)) or not float(deger).is_integer():
        raise ValueError(f"bot_hafiza.HAFIZA_ZAMAN_ASIMI_S={deger!r} tamsayı sn değil — Hermes Hindsight eklentisi "
                         "zaman aşımını int()'e kırpar, sohbet profili kanal katmanından farklı süre kullanırdı")
    return int(deger)


def _hindsight(bot: kadro_mod.Bot) -> bytes:
    veri = {
        "_uretildi": URETILDI,
        "mode": "local_external",
        # Kök URL (yolsuz): eklenti banka yolunu kendisi ekler, kanal katmanı da `bot_hafiza.BANKA_KOKU`yu.
        "api_url": secrets.HAFIZA_TABAN_URL,
        # Önek `bot_hafiza`nın banka yolunda (`HindsightHafiza._banka_yolu`) — eşitliği v599 çiviler.
        "bank_id": f"bot-{bot.ad}",
        "recall_budget": bot_hafiza.UNUT_RECALL_BUTCESI,
        "memory_mode": "context",
        "auto_recall": HINDSIGHT_OTOMATIK_HATIRLAMA,
        "auto_retain": HINDSIGHT_OTOMATIK_KAYIT,
        "retain_tags": f"bot:{bot.ad},kaynak:sohbet",
        "retain_source": bot.ad,
        "retain_async": False,
        "timeout": _hindsight_zaman_asimi(),
    }
    return (json.dumps(veri, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _soul(rapor_evi: pathlib.Path, bot: kadro_mod.Bot) -> bytes:
    rapor = (rapor_evi / "SOUL.md").read_text(encoding="utf-8").rstrip()
    return (rapor + "\n\n" + sohbet_bolumu(bot)).encode("utf-8")


def _tek_girdi(manifest: dict, ad: str, alan: str, rapor_evi: pathlib.Path) -> dict:
    """Rapor manifestinin `env_requires` listesindeki TEK `ad` girdisi; `alan` taşımalı. Yoksa açık hata."""
    girdiler = [g for g in (manifest.get("env_requires") or []) if isinstance(g, dict) and g.get("name") == ad]
    if len(girdiler) != 1 or alan not in girdiler[0]:
        raise ValueError(f"{rapor_evi}/distribution.yaml: env_requires içinde '{alan}' alanlı tek bir {ad} girdisi "
                         f"beklenirdi ({len(girdiler)} girdi bulundu) — beyan miras alınamaz")
    return girdiler[0]


def _dagitim(rapor_evi: pathlib.Path, bot: kadro_mod.Bot) -> bytes:
    manifest = _yaml_oku(rapor_evi / "distribution.yaml")
    anahtar_adi = f"BOT_KEY_{bot.ad.upper()}"
    kapi = _tek_girdi(manifest, anahtar_adi, "required", rapor_evi)
    if "hermes_requires" not in manifest:
        raise ValueError(f"{rapor_evi}/distribution.yaml: hermes_requires yok — sürüm tabanı miras alınamaz")
    veri = {
        "name": bot.ad,
        "version": "0.1.0",
        "description": f"{bot.ad} sohbet profili — ÜRETİLMİŞ (rapor profilinden türetildi)",
        "hermes_requires": manifest["hermes_requires"],
        "env_requires": [
            {"name": "HERMES_WRITE_SAFE_ROOT", "description": SOHBET_YAZMA_KOKU_ACIKLAMASI, "required": True,
             "default": BOT_KUM_HAVUZU},
            {"name": anahtar_adi, "description": SOHBET_KAPI_ANAHTARI_ACIKLAMASI, "required": kapi["required"]},
            {"name": "HINDSIGHT_API_KEY", "required": True, "description": SOHBET_HAFIZA_ANAHTARI_ACIKLAMASI},
        ],
        "distribution_owned": ["SOUL.md", "config.yaml", "hindsight/config.json"],
    }
    baslik = (URETILDI + ".",
              f"Kaynak: {RAPOR_KOK}/{bot.ad}/distribution.yaml (sürüm tabanı, kapı anahtarının adı ve zorunluluğu);",
              "yazma kökü ağ geçidinin ortak kum havuzu, açıklamalar üretecin sohbet sabitleri.")
    return _yaml_yaz(baslik, veri)


def uret(kok: pathlib.Path = REPO, kadro=None) -> dict[str, bytes]:
    """Göreli yol → içerik. YAZMAZ."""
    kok = pathlib.Path(kok)
    kok_cfg = _yaml_oku(kok / KOK_YAPILANDIRMA)
    kok_meridian = (kok_cfg.get("mcp_servers") or {}).get("meridian")
    if not isinstance(kok_meridian, dict) or not isinstance(kok_meridian.get("args"), list):
        raise ValueError(f"{KOK_YAPILANDIRMA}: mcp_servers → meridian girdisi (args listesiyle) yok — "
                         "sohbet profilinin araç sunucusu türetilemez")
    cikti: dict[str, bytes] = {
        f"{SOHBET_EV}/config.yaml": _kok_config(kok),
        f"{SOHBET_EV}/SOUL.md": KOK_SOUL.encode("utf-8"),
    }
    for bot in sorted(_kadro(kok, kadro), key=lambda b: b.ad):
        rapor_evi = kok / RAPOR_KOK / bot.ad
        if not rapor_evi.is_dir():
            raise ValueError(f"aktif @{bot.ad} için rapor profili yok ({RAPOR_KOK}/{bot.ad}) — "
                             "sohbet profili türetilemez")
        hedef = f"{SOHBET_KOK}/{bot.ad}"
        cikti[f"{hedef}/SOUL.md"] = _soul(rapor_evi, bot)
        cikti[f"{hedef}/config.yaml"] = _config(rapor_evi, bot, kok_meridian)
        cikti[f"{hedef}/distribution.yaml"] = _dagitim(rapor_evi, bot)
        cikti[f"{hedef}/hindsight/config.json"] = _hindsight(bot)
    return cikti


#: `fazla` sayılmayan dosya ADLARI — yalnız macOS Finder'ın dizin önbelleği: sohbet kökü yerelde Finder'la
#: açılınca oluşur ve `--kontrol`u sahte kırmızıya çevirirdi. Liste bilerek TEK ad: başka gizli dosya (`.env` dahil)
#: fazla sayılmaya DEVAM eder — Hermes köküne taşınacak elle dosya görünmez olmamalı.
FAZLA_SAYILMAZ = frozenset({".DS_Store"})


def _fazlalar(kok: pathlib.Path, beklenen: dict[str, bytes]) -> list[str]:
    taban = kok / SOHBET_EV
    if not taban.is_dir():
        return []
    return sorted(str(p.relative_to(kok)) for p in taban.rglob("*")
                  if p.is_file() and p.name not in FAZLA_SAYILMAZ and str(p.relative_to(kok)) not in beklenen)


def yaz(kok: pathlib.Path = REPO, kadro=None) -> list[str]:
    """Üretir ve YALNIZ içeriği değişen dosyaları yazar (dokunulmayan dosyanın mtime'ı korunur). Yazılan
    göreli yollar döner. Hiçbir şey SİLMEZ."""
    kok = pathlib.Path(kok)
    yazilan = []
    for goreli, icerik in uret(kok, kadro).items():
        hedef = kok / goreli
        if hedef.is_file() and hedef.read_bytes() == icerik:
            continue
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_bytes(icerik)
        yazilan.append(goreli)
    return yazilan


def kontrol(kok: pathlib.Path = REPO, kadro=None) -> list[str]:
    """Ayrışan/eksik/fazla dosya açıklamaları; boş liste = güncel. YAZMAZ."""
    kok = pathlib.Path(kok)
    beklenen = uret(kok, kadro)
    bulgular = []
    for goreli, icerik in beklenen.items():
        hedef = kok / goreli
        if not hedef.is_file():
            bulgular.append(f"eksik: {goreli} — üretilmemiş (--yaz)")
        elif hedef.read_bytes() != icerik:
            bulgular.append(f"ayrışan: {goreli} — kaynaktan geride ya da elle düzenlenmiş (--yaz)")
    for goreli in _fazlalar(kok, beklenen):
        bulgular.append(f"fazla: {goreli} — ne kök profilin ne kadroda aktif bir botun üretilmiş dosyası "
                        "(üreteç SİLMEZ; kaldırmak bir karardır)")
    return bulgular


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Bot ağ geçidinin kök profilini ve aktif botların sohbet profillerini "
                                             "rapor profillerinden üret.")
    ap.add_argument("--yaz", action="store_true", help="üret ve yaz (yalnız içeriği değişen dosyalar)")
    ap.add_argument("--kontrol", action="store_true", help="yazma; diskteki dosyalar güncel mi (0/1)")
    ns = ap.parse_args(argv)
    if ns.yaz == ns.kontrol:
        print("kullanım: tam olarak biri — --yaz ya da --kontrol (ikisi birden ya da hiçbiri geçersiz)",
              file=sys.stderr)
        return 2
    if ns.kontrol:
        bulgular = kontrol()
        for b in bulgular:
            print(b)
        if not bulgular:
            print(f"güncel: {SOHBET_EV}")
        return 1 if bulgular else 0
    yazilan = yaz()
    for y in yazilan:
        print(f"yazıldı: {y}")
    if not yazilan:
        print(f"değişiklik yok: {SOHBET_EV}")
    fazla = [b for b in kontrol() if b.startswith("fazla:")]
    for b in fazla:
        print(f"UYARI {b}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
