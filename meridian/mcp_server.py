"""mcp_server.py — Meridian durumunu yerel hermes-agent'a MCP aracı olarak açan stdio sunucusu.

NE YAPAR. Kanıt paketini prompt'a tıkıştırmak (ne gerekeceğini önceden bizim tahmin etmemiz)
yerine, ajan bir adayı düşünürken İHTİYACI OLAN veriyi kendisi sorgular. Bağımsız bir stdio
JSON-RPC (MCP) sunucusudur: satır-ayrımlı JSON-RPC 2.0 konuşur; hermes `~/.hermes/config.yaml`
içindeki mcp_servers kaydıyla başlatır. `serve()` EOF'a kadar döner; initialize / ping / tools-list /
tools-call metotları desteklenir, bozuk satır parse-error alır.

İKİ KİP (Parça 1b G1, spec 2026-09-29 §3.2):
  * `--bot` YOK — geri uyum (varsayılan Hermes profili; K-1 ile `enabled: false`). Bugünkü altı
    getter, başka hiçbir şey: yazan araç ne listelenir ne koşar; getter çıktısı BAYT-ÖZDEŞ ham JSON'dur
    (çit/scrub bu kipte YOK — G1 öncesi sözleşme aynen); kayıt yalnız getter'lardır ve
    `sohbet`/`kadro` İTHAL EDİLMEZ (ithaller fonksiyon içinde, yalnız `--bot` yolunda) — bu yol G1
    öncesinde o modüllere bağlı değildi, onların arızasıyla (bozuk `SOHBET_*` ortamı, ithal hatası)
    ölmesi geriye dönük bir kırılma olurdu (Tur 2, inceleme M-1).
  * `--bot <ad>` — ad kadroda AKTİF bir bot olmalı. Yazım hatası / sırada / kilitli bot → süreç
    AÇILMAZ (stderr'e ad + neden, çıkış 2): sessizce altı getter'la açılmak botu YANLIŞ araç
    kümesiyle konuştururdu. Sunulan küme = o botun `araclar`ı ∩ kayıt, kadro sırasıyla;
    `YALNIZ_HEPSI_HAFIZALI` araçlar yalnız `hafiza: hepsi` bota (kadroda listelense bile — iki kat).
    Kadronun listelediği ama kayıtta OLMAYAN ad ATLANIR (savunma: bugün aktif botların listelediği her
    ad kayıtta — çivi v597); bilinen kümenin dışındaki adı kadro çivisi (v591) yakalar.

KAYIT (`arac_kaydi`) TEK KAYNAKTAN türer: altı getter aşağıdaki `TOOLS`tan (bu kipte `_getter_araclari`
ile sarılı — gövde aynı, zarf sohbetinki; dal sonu I-1: spec §3.2 bütün okuma araçlarının çıktısını çitli
ister ve sohbet profillerinin SOUL'u modele "veri çitin içinde gelir" der); pano sohbetinin araçları
`sohbet.ARACLAR`dan — şema ve açıklama KOPYALANMAZ, aynı nesnedir; MCP'ye özgü iki araç (`is_iste`,
`bot_hafizasi_ara` = kadronun planlı araçları) `_mcp_araclari`ndan — şemaları bu modülün sabitleridir,
pano sohbetinin kaydına GİRMEZLER (sohbetin beyaz listesi donuk). `--bot` kipinde HER araç (getter,
sohbet aracı, MCP'ye özgü) `sohbet._arac_kos` üzerinden koşar: VERİ çiti + `notify.scrub` + çıktı
tavanı + şema doğrulaması sohbetle birebir aynı gövdedir. Aynı ad iki kaynakta varsa kayıt sessizce EZMEZ, ValueError atar.

İKİ KAT İZİN: `tools/list` yalnız izinli araçları döner; `tools/call` ÖNCE izni sorar — izinli
olmayan araç `isError` + "izinli değil" alır ve KOŞMAZ (model listede görmediği bir adı yine de
çağırabilir). Kayıtta hiç olmayan ad bugünkü gibi -32602 alır.

DEĞİŞMEZLER. Sunucunun KENDİ kodu hiçbir dosyaya yazmaz (AST çivisi `tests/test_mcp_audit_v31.py`).
Getter'lar salt okur. `--bot` kipinde YAZAN iki araç var, ikisi de BAŞKA modülün gövdesiyle yazar:
(1) `is_iste` (`MCP_YAZAN_ARACLAR`) — `is_istek.is_iste` gövdesiyle istek tetik dosyası + kabul defteri;
donuk iş listesi ve 15 dk tavanı aynen. Kanal bu sunucuda BİLİNMEZ (Hermes söylemez) → `kanal: null` +
`cagiran: mcp:<bot>`; kanal ve kimlik şemada YOKTUR, model kendini başka kanal/bot gibi gösteremez; ret
(tavan / bilinmeyen iş) `isError` taşır. (2) `oneri_yaz` (`sohbet.YAZAN_ARACLAR`) —
sohbetin AYNI gövdesiyle onay defterine `durum: "bekliyor"` bir ÖNERİ satırı ekler — bağlamın
`oturum` alanı `mcp:<bot>` taşır, `kaynak` alanı sohbetin `CAGRI_KIND`ı KALIR, çünkü panonun gelen
kutusu ve onay ucu satırı bu alan + kimlik biçiminden tanır (`api._defter_tarama`,
`api._bekleyen_sohbet_onerileri`, `sohbet.oneri_satiri`). İCRA ETMEZ; kararı operatör MEVCUT onay
ucundan verir — ikinci onay yolu YOK. `bot_hafizasi_ara` SALT-OKUR: hedef AKTİF botun `bot-<ad>`
bankasında recall (`bot_hafiza`, HTTP; bellek durumu değişmez). Sohbet ve MCP'ye özgü araçların arıza/red
olayları sohbetin kendi gözlem kaydına düşer. Her araç savunmacıdır: getter istisnası ve sohbet aracının reddi / şema dışılığı /
arızası metne döner (isError), döngü ölmez. Öngörü saflığı: `meridian_candidate_context` sonuç
(r_multiple) DÖNDÜRMEZ.

PROTOKOL AKIŞI YALNIZ JSON-RPC (Tur 2, inceleme I-1). `obs._emit` her olayı `sys.stdout`a basar; MCP
stdio taşımasında stdout protokol kanalıdır ve JSON-RPC olmayan bir satır istemcide ayrıştırma
hatasıdır. `serve` yanıt akışını (`stdout` ya da o anki `sys.stdout`) EN BAŞTA yakalar, sonra
kurulumu ve döngüyü `contextlib.redirect_stdout(sys.stderr)` altında koşar: araç gövdelerinin
(getter'lar dahil) her `print`i ve `obs` satırı stderr'e gider, yanıtlar yakalanmış akışa. Bedel:
`serve` süresince süreç içi `sys.stdout` stderr'dir — tek iplikli stdio sunucusunda başka okuyucusu yok.
Aynı sınıfın GİRDİ yüzü (Görev 2, Rol-1 kararı): stdin JSON-RPC girdisidir — araçların alt süreci onu miras
ALMAZ (`sohbet._arac_hafiza_ara` alt süreci `stdin=DEVNULL`; `bot_hafizasi_ara` HTTP'dir, alt süreç açmaz).

BOZUK GİRDİ DÖNGÜYÜ ÖLDÜRMEZ (dal sonu M-1). Süreç ölürse o Hermes oturumundaki bot ARAÇSIZ kalır ve
araçsız modelin araç sonucu UYDURDUĞU ölçüldü (Parça 0). Ayrıştırılamayan satır → -32700; geçerli JSON
ama nesne olmayan mesaj (dizi — toplu istek desteklenmez —, dizge, sayı, null) ya da nesne olmayan
`params` → -32600 (id varsa o id, yoksa null; `params: null` eksik sayılır); işlemede beklenmeyen istisna
→ -32603 + `mcp_istek_isleme_hatasi` olayı (stderr). Üçünde de döngü sürer.

OKUR: state/ (store/analytics üzerinden: regime.json, kalibrasyon artefaktları, trade_plans.jsonl,
cf_open.json, self_review.json), `deploy/hermes/kadro.yaml` (`kadro.kadro_yukle`), sohbet
araçlarının okuduğu her şey (`sohbet` modül başlığı), `is_iste`nin tavan defteri (`is_istek`) ve
Hindsight `bot-*` bankaları (`bot_hafiza`, HTTP)."""
from __future__ import annotations
import argparse
import contextlib
import dataclasses
import json
import sys

from . import store, analytics, obs
# `sohbet` ve `kadro` BURADA İTHAL EDİLMEZ — yalnız `--bot` yolunun fonksiyonlarında (modül başlığı, İKİ KİP).


def _regime(_args: dict) -> dict:
    """Güncel rejim kaydı: tarih, rejim, maruziyet bütçesi/skoru, dağıtım günleri ve genişlik skoru.
    SALT OKUMA."""
    r = store.read_json("regime.json", {})
    return {k: r.get(k) for k in ("date", "regime", "exposure_budget_pct", "exposure_score",
                                  "min_exposure_score", "distribution_days", "breadth_score")}


def _calibrations(_args: dict) -> dict:
    """Kalibrasyon artefaktlarını tek sözlükte toplar (skor IC, LLM görüşü, kapı meta, çıkış verimliliği,
    cf sadakati). Bulunmayan artefakt None kalır — uydurma değer yok. SALT OKUMA."""
    return {
        "score": store.read_json("score_calibration.json", None),
        "llm_opinion": store.read_json("llm_calibration.json", None),
        "gate_meta": store.read_json("gate_calibration.json", None),
        "exit_efficiency": store.read_json("exit_efficiency.json", None),
        "cf_fidelity": store.read_json("cf_fidelity.json", None),
        "note": "cf-beslemeli kalibrasyonları cf_fidelity onaysızsa iskontolu oku",
    }


def _near_miss(_args: dict) -> dict:
    """Hangi giriş eşiği masada para bırakıyor? blocked_by kovası başına adet/giriş/ort.R."""
    return store.read_json("near_miss.json", {"resolved_total": 0, "buckets": {},
                                              "note": "henüz çözülmüş eşik-altı satır yok"})


def _cf_summary(_args: dict) -> dict:
    """Karşı-olgusal defter + skill katkısı — hangi ekran/kurulum gerçekten para kazanıyor."""
    try:
        attr = analytics.skill_attribution()
    except Exception:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
        attr = None
    op = store.read_json("cf_open.json", [])
    return {"open_rows": len(op),
            "skill_attribution": attr if isinstance(attr, (list, dict)) else None,
            "note": "cf statik-bracket simülasyonu; canlı yasadan sapma cf_fidelity'de"}


def _selfreview(_args: dict) -> dict:
    """Haftalık öz-değerlendirmenin özeti: üretim damgası, dikkat maddeleri, çelişkiler ve ilerleme.
    SALT OKUMA."""
    r = store.read_json("self_review.json", {})
    return {"generated": r.get("generated"), "attention": r.get("attention", []),
            "contradictions": r.get("contradictions", []),
            "progress": r.get("progress", {})}


def _candidate_context(args: dict) -> dict:
    """Belirli bir ticker için BUGÜNÜN karar-anı planı (varsa) + son görüşü — ajan kendi kararını
    Meridian'ın kapı gerekçeleriyle çapraz okuyabilsin. Sonuç (r_multiple) DÖNMEZ (öngörü saflığı)."""
    tk = str(args.get("ticker", "")).upper()
    if not tk:
        return {"error": "ticker gerekli"}
    plans = store.read_jsonl("trade_plans.jsonl")
    mine = [p for p in plans if str(p.get("ticker", "")).upper() == tk]
    if not mine:
        return {"ticker": tk, "found": False}
    p = mine[-1]
    return {"ticker": tk, "found": True,
            "plan": {k: p.get(k) for k in ("date", "setup", "entry_trigger", "stop", "profit_target",
                                           "size_r", "score", "gate_verdict", "gate_reasons",
                                           "skill_chain", "llm_opinion", "p_win_shadow")}}


TOOLS = [
    {"name": "meridian_regime", "fn": _regime,
     "description": "Güncel piyasa rejimi ve maruziyet bütçesi (chop/trend_up, bütçe %, eşik).",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "meridian_calibrations", "fn": _calibrations,
     "description": "Tüm kalibrasyon özetleri: skor IC, LLM görüş, kapı meta, çıkış verimliliği, cf sadakati.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "meridian_near_miss", "fn": _near_miss,
     "description": "Hangi giriş eşiği masada para bırakıyor — eşik-altı adayların ölüm-nedeni karnesi.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "meridian_cf_summary", "fn": _cf_summary,
     "description": "Karşı-olgusal defter özeti + skill/ekran katkısı (hangi kurulum para kazanıyor).",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "meridian_selfreview", "fn": _selfreview,
     "description": "En son haftalık öz-değerlendirme: DİKKAT satırları, katmanlar-arası çelişkiler, ilerleme.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "meridian_candidate_context", "fn": _candidate_context,
     "description": "Bir ticker için karar-anı planı ve kapı gerekçeleri (sonuç dönmez).",
     "inputSchema": {"type": "object",
                     "properties": {"ticker": {"type": "string", "description": "Sembol, ör. NVDA"}},
                     "required": ["ticker"]}},
]
_BY_NAME = {t["name"]: t for t in TOOLS}
PROTOCOL_VERSION = "2024-11-05"

#: Yalnız `hafiza: hepsi` bota listelenen araçlar (spec §3.2: bütün botların hafızasını okuyan
#: araç yalnız @sef'e). Kadro `araclar`ında listelense bile `hafiza` koşulu ayrıca sorulur — iki kat.
#: Ad KAYITTA olmalı (çivi v597): yazım hatası kapıyı sessizce açardı.
YALNIZ_HEPSI_HAFIZALI = ("bot_hafizasi_ara",)

#: MCP'ye özgü araçlardan YAZAN(lar) — `sohbet.YAZAN_ARACLAR`ın bu sunucudaki eşi. Liste ADIYLA beyanlıdır:
#: yazmadığı beyan edilen her MCP'ye özgü araç diske dokunmadan koşmalı (çivi v597); yeni bir yazan araç
#: buraya girmeden o çivi öter.
MCP_YAZAN_ARACLAR = ("is_iste",)

#: MCP'ye özgü araçların şemaları MODÜL SABİTİDİR: kayıt ve çağrı anı doğrulaması AYNI nesneyi görür.
#: Kanal ve çağıran kimliği şemada YOK — ikisi de sunucunun bilgisidir (modül başlığı, DEĞİŞMEZLER).
_IS_ISTE_SEMA = {"type": "object",
                 "properties": {"ad": {"type": "string",
                                       "description": "zamanlı işi şimdi koşturulacak botun adı, ör. karne "
                                                      "(liste kadrodan türer)"}},
                 "required": ["ad"], "additionalProperties": False}
_BOT_HAFIZASI_ARA_SEMA = {"type": "object",
                          "properties": {"bot": {"type": "string",
                                                 "description": "hafızası aranacak AKTİF bot, ör. bekci"},
                                         "soru": {"type": "string"}},
                          "required": ["bot", "soru"], "additionalProperties": False}


class BotAcilamaz(ValueError):
    """`--bot` adı kadroda AKTİF bir bot değil — sunucu açılmaz (sessiz altı-getter kipine düşmez)."""


class _AracBasarisiz(Exception):
    """Sohbet aracı `_arac_kos`tan RED / ŞEMA DIŞI / ARIZA ile döndü. `metin` modele gidecek çitli
    metnin kendisidir; `_handle` onu `isError: true` ile aynen iletir (getter istisnasıyla aynı
    sözleşme — "araç başarısız" bilgisi MCP istemcisine de ulaşır)."""

    def __init__(self, metin: str):
        super().__init__(metin)
        self.metin = metin


def _getter_cagir(ad: str):
    """Getter'ı `_BY_NAME` üzerinden GEÇ bağlar: kayıt girdisi fonksiyonu kopyalamaz, çağrı anında
    `TOOLS` kaydındaki `fn`i okur (o kayda yapılan her değişiklik tek yerden görünür)."""
    def cagir(args, baglam=None):
        return json.dumps(_BY_NAME[ad]["fn"](args or {}), ensure_ascii=False, default=str)
    return cagir


def _arac_kos_cagir(ad: str, kaynak):
    """Aracı `sohbet._arac_kos` ile koşturur — çit/scrub/tavan/şema KOPYALANMAZ. `kaynak()` araç sözlüğünü
    ÇAĞRI ANINDA döner (sohbet araçları için `sohbet.ARACLAR`, MCP'ye özgüler için `_mcp_araclari`).
    Başarısız dönüş (şema dışı, ret ya da arıza — atıfsız) `_AracBasarisiz`."""
    def cagir(args, baglam=None):
        from . import sohbet                         # yalnız `--bot` yolu (modül başlığı, İKİ KİP)
        metin, sema_disi, atif, _kesit = sohbet._arac_kos(ad, args, baglam if baglam is not None
                                                          else {}, kaynak())
        if sema_disi or not atif:
            raise _AracBasarisiz(metin)
        return metin
    return cagir


def _arac_is_iste(args: dict, baglam: dict | None = None) -> str:
    """`is_istek.is_iste` — kanal BU SUNUCUDA BİLİNMEZ: `kanal=None` + `cagiran` = oturum (`mcp:<bot>`); oturum
    yoksa `is_iste` kimliksiz isteği reddeder. Ret (tavan / bilinmeyen iş) `AracReddi`dir: sonuç metni aynen
    modele gider ama MCP istemcisi `isError` görür — "iş tetiklendi" diye okunamaz."""
    from . import is_istek, sohbet                   # yalnız `--bot` yolu (modül başlığı, İKİ KİP)
    s = is_istek.is_iste(str(args.get("ad") or ""), None, cagiran=(baglam or {}).get("oturum"))
    metin = json.dumps(dataclasses.asdict(s), ensure_ascii=False)
    if not s.kabul:
        raise sohbet.AracReddi(metin)
    return metin


def _arac_bot_hafizasi_ara(args: dict, baglam: dict | None = None) -> str:
    """Hedef botun `bot-<ad>` bankasında SALT-OKUR recall (`bot_hafiza`, HTTP — alt süreç YOK). Hedef kadroda
    AKTİF değilse HTTP'den ÖNCE ret. Sonuç yoksa bunu ölçülmüş sıfır olarak SÖYLER."""
    from . import bot_hafiza, kadro as _kadro, sohbet  # yalnız `--bot` yolu (modül başlığı, İKİ KİP)
    ham = str(args.get("bot") or "")
    hedef = _kadro.bot_bul(ham)
    if hedef is None or hedef.durum != "aktif":
        durum = "kadroda yok" if hedef is None else f"durum={hedef.durum}"
        raise sohbet.AracReddi(f"bot {ham!r} kadroda 'aktif' değil ({durum}) — yalnız aktif botların hafıza "
                               "bankası aranır")
    soru = str(args.get("soru") or "")
    sonuclar = bot_hafiza.HindsightHafiza().ara(hedef.ad, soru)
    satirlar = [f"bot-{hedef.ad} hafızası · soru {soru.strip()!r} · {len(sonuclar)} sonuç (tarih · metin)"]
    satirlar += [f"[{i}] {tarih} · {metin}" for i, (tarih, metin) in enumerate(sonuclar, 1)]
    if not sonuclar:
        satirlar.append("(recall bu soru için bellek döndürmedi)")
    return "\n".join(satirlar)


def _mcp_araclari() -> dict:
    """MCP'ye özgü araçlar: ad → `sohbet.Arac`. Adlar kadronun planlı araçlarıdır (çivi v597); gövde ve şema bu
    modülde, koşum `sohbet._arac_kos`ta. `sohbet` ithali burada (yalnız `--bot` yolu)."""
    from . import sohbet
    return {a.ad: a for a in (
        sohbet.Arac("is_iste", "Bir botun zamanlı işini ŞİMDİ koşturma isteği (donuk iş listesi, iş başına "
                               "15 dk tavanı). Sonuç: kabul/ret + neden.",
                    _IS_ISTE_SEMA, _arac_is_iste, lambda args: str(args.get("ad") or "-")),
        sohbet.Arac("bot_hafizasi_ara", "Bir AKTİF botun hafıza bankasında salt-okur arama (tarih · metin).",
                    _BOT_HAFIZASI_ARA_SEMA, _arac_bot_hafizasi_ara,
                    lambda args: f"bot-{args.get('bot') or '-'}"),
    )}


def _getter_araclari() -> dict:
    """`--bot` kipinde altı getter: ad → `sohbet.Arac`, gövde `_getter_cagir` (ham JSON'u üreten AYNI
    fonksiyon), şema/açıklama `TOOLS`taki AYNI nesne. `_arac_kos` onu sohbet aracı gibi koşar: çit + scrub +
    tavan + şema doğrulaması. `--bot`suz kip bu sarmalayıcıyı HİÇ görmez (`_getter_kaydi`, bayt-özdeş)."""
    from . import sohbet                             # yalnız `--bot` yolu (modül başlığı, İKİ KİP)
    return {t["name"]: sohbet.Arac(t["name"], t["description"], t["inputSchema"], _getter_cagir(t["name"]),
                                   lambda args: "-")
            for t in TOOLS}


def _getter_kaydi() -> dict[str, dict]:
    """Yalnız altı getter'ın kaydı — `--bot`suz kipin TÜM kaydı. `sohbet`/`kadro` ithal etmez."""
    return {t["name"]: {"name": t["name"], "description": t["description"],
                        "inputSchema": t["inputSchema"], "cagir": _getter_cagir(t["name"])}
            for t in TOOLS}


def arac_kaydi() -> dict[str, dict]:
    """ad → `{"name", "description", "inputSchema", "cagir"}`; `cagir(args, baglam) -> str`.

    TEK KAYNAK: altı getter `TOOLS`tan (`_getter_araclari` ile sarılı), sohbet araçları
    `sohbet.ARACLAR`dan, MCP'ye özgüler `_mcp_araclari`ndan (şema/açıklama AYNI nesne); HEPSİ
    `sohbet._arac_kos` zarfından geçer. Önbellek YOK — kayıt her `serve` açılışında kaynaktan türer,
    bayat kopya olamaz. Tam kayıt yalnız `--bot` kipinin kaydıdır; `sohbet` ithali burada, ilk kullanımda."""
    from . import sohbet
    kayit: dict[str, dict] = {}
    for kaynak in (_getter_araclari, lambda: sohbet.ARACLAR, _mcp_araclari):
        for ad, a in kaynak().items():
            if ad in kayit:
                raise ValueError(f"araç adı çakışması: {ad!r} iki kaynakta (getter · sohbet · MCP'ye "
                                 "özgü) — kayıt sessizce ezilmez")
            kayit[ad] = {"name": ad, "description": a.aciklama, "inputSchema": a.sema,
                         "cagir": _arac_kos_cagir(ad, kaynak)}
    return kayit


def _bot_coz(bot: str | None, kadro=None):
    """`--bot` adını kadrodaki AKTİF bota çözer; bot yoksa None. Bulunamayan ya da aktif olmayan ad
    → `BotAcilamaz` (neden adıyla)."""
    if bot is None:
        return None
    from . import kadro as _kadro                    # yalnız `--bot` yolu (modül başlığı, İKİ KİP)
    b = _kadro.bot_bul(bot, kadro)
    if b is None:
        raise BotAcilamaz(f"--bot {bot!r}: kadroda böyle bir bot yok ({_kadro.KADRO_YOLU.name})")
    if b.durum != "aktif":
        raise BotAcilamaz(f"--bot {b.ad!r}: kadroda durum={b.durum!r} — yalnız 'aktif' bot araç "
                          "sunucusu açabilir")
    return b


def _kip_kaydi(b) -> dict[str, dict]:
    """Kipin kaydı: bot yoksa yalnız getter'lar (`sohbet` ithal edilmez), bot varsa tam kayıt."""
    return arac_kaydi() if b is not None else _getter_kaydi()


def _izinli(b, kayit: dict) -> list[str]:
    if b is None:
        return [t["name"] for t in TOOLS]
    return [a for a in b.araclar
            if a in kayit and (a not in YALNIZ_HEPSI_HAFIZALI or b.hafiza == "hepsi")]


def izinli_araclar(bot: str | None, kadro=None) -> list[str]:
    """Botun göreceği araç adları (kadro sırasıyla). `bot` None → bugünkü altı getter; aksi hâlde
    botun kadro satırındaki araç listesi ∩ kayıt, `YALNIZ_HEPSI_HAFIZALI` yalnız `hafiza == "hepsi"`
    bota. Kayıtta olmayan kadro adı atlanır. Aktif olmayan / bilinmeyen bot → `BotAcilamaz`."""
    b = _bot_coz(bot, kadro)
    return _izinli(b, _kip_kaydi(b))


def _handle(msg: dict, kayit: dict | None = None, izinli: list[str] | None = None,
            oturum: str = "mcp") -> dict | None:
    """Bir JSON-RPC isteğini işle. Bildirim (id yok) → None (yanıt yazılmaz). `kayit`/`izinli`
    verilmezse bugünkü kip (altı getter); `serve` bunları bot başına bir kez hesaplayıp geçirir."""
    kayit = _getter_kaydi() if kayit is None else kayit
    izinli = _izinli(None, kayit) if izinli is None else izinli
    if not isinstance(msg, dict):                    # dizi/dizge/sayı/null — JSON-RPC isteği değil (M-1)
        return {"jsonrpc": "2.0", "id": None,
                "error": {"code": -32600, "message": "geçersiz istek: mesaj bir JSON nesnesi değil"}}
    mid = msg.get("id")
    if msg.get("params") is not None and not isinstance(msg["params"], dict):
        return {"jsonrpc": "2.0", "id": mid,
                "error": {"code": -32600, "message": "geçersiz istek: params bir JSON nesnesi değil"}}
    method = msg.get("method")
    if method == "initialize":
        client_pv = (msg.get("params") or {}).get("protocolVersion") or PROTOCOL_VERSION
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": client_pv,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "meridian", "version": "1.0.0"}}}
    if method in ("notifications/initialized", "initialized"):
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "tools": [{"name": kayit[ad]["name"], "description": kayit[ad]["description"],
                       "inputSchema": kayit[ad]["inputSchema"]} for ad in izinli]}}
    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        if not isinstance(name, str) or name not in kayit:
            return {"jsonrpc": "2.0", "id": mid,
                    "error": {"code": -32602, "message": f"bilinmeyen araç: {name}"}}
        if name not in izinli:                       # İKİNCİ KAT: listede olmayan ad KOŞMAZ
            return {"jsonrpc": "2.0", "id": mid, "result": {
                "content": [{"type": "text",
                             "text": f"reddedildi: {name!r} bu bot için izinli değil "
                                     f"(oturum {oturum}; izinli: {', '.join(izinli)})"}],
                "isError": True}}
        try:
            text = kayit[name]["cagir"](params.get("arguments"), {"oturum": oturum})
            return {"jsonrpc": "2.0", "id": mid, "result": {
                "content": [{"type": "text", "text": text}], "isError": False}}
        except _AracBasarisiz as e:                  # sohbet aracı red/şema dışı/arıza — çitli metin aynen
            return {"jsonrpc": "2.0", "id": mid, "result": {
                "content": [{"type": "text", "text": e.metin}], "isError": True}}
        except Exception as e:                       # araç asla döngüyü düşürmez — hata metne döner
            return {"jsonrpc": "2.0", "id": mid, "result": {
                "content": [{"type": "text", "text": f"hata: {type(e).__name__}: {e}"}],
                "isError": True}}
    if mid is not None:                              # bilinmeyen METOT (bildirim değil) → standart hata
        return {"jsonrpc": "2.0", "id": mid,
                "error": {"code": -32601, "message": f"bilinmeyen metot: {method}"}}
    return None


def serve(stdin=None, stdout=None, bot: str | None = None) -> None:
    """Satır-ayrımlı JSON-RPC döngüsü. EOF'ta çıkar. Bozuk satır → parse error (id yoksa sessiz geç).

    `bot` verilirse kadro çözümü ve izin kümesi TEK SATIR OKUNMADAN hesaplanır: aktif olmayan bot
    `BotAcilamaz` ile döngüye hiç girmez. Oturum bağlamı kadronun kanonik adıyla `mcp:<ad>`dır.

    Yanıt akışı `outp` yönlendirmeden ÖNCE yakalanır; kurulum ve döngü `sys.stdout` stderr'e
    yönlenmişken koşar — araç gövdesinin `obs` satırı protokol akışına karışmaz (modül başlığı)."""
    inp = stdin or sys.stdin
    outp = stdout or sys.stdout                      # PROTOKOL AKIŞI — yalnız JSON-RPC yanıtı yazılır
    with contextlib.redirect_stdout(sys.stderr):
        b = _bot_coz(bot)
        kayit = _kip_kaydi(b)
        izinli = _izinli(b, kayit)
        oturum = f"mcp:{b.ad}" if b is not None else "mcp"
        for line in inp:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
                outp.write(json.dumps({"jsonrpc": "2.0", "id": None,
                                       "error": {"code": -32700, "message": "parse error"}}) + "\n")
                outp.flush()
                continue
            try:
                resp = _handle(msg, kayit, izinli, oturum)
            except Exception as e:                   # son savunma (M-1): döngü ölürse bot ARAÇSIZ kalır
                obs.warn("mcp_istek_isleme_hatasi", oturum=oturum, error=f"{type(e).__name__}: {e}"[:300],
                         detail="JSON-RPC isteği işlenirken beklenmeyen istisna — -32603 döndü, döngü sürüyor")
                resp = {"jsonrpc": "2.0", "id": msg.get("id") if isinstance(msg, dict) else None,
                        "error": {"code": -32603, "message": f"iç hata: {type(e).__name__}"}}
            if resp is not None:
                outp.write(json.dumps(resp, ensure_ascii=False) + "\n")
                outp.flush()


def main(argv: list[str] | None = None) -> int:
    """`python -m meridian.mcp_server [--bot <ad>]`. Kadroda aktif olmayan bot → stderr'e ad + neden,
    çıkış 2, stdin OKUNMAZ (hermes süreci "açılamadı" görür; sessiz altı-getter kipi yok)."""
    ap = argparse.ArgumentParser(prog="python -m meridian.mcp_server",
                                 description="Meridian MCP araç sunucusu (stdio JSON-RPC).")
    ap.add_argument("--bot", default=None,
                    help="kadrodaki AKTİF bot adı; yalnız o botun araçları sunulur. Verilmezse "
                         "bugünkü altı getter.")
    ns = ap.parse_args(argv)
    try:
        _bot_coz(ns.bot)
    except BotAcilamaz as e:
        print(f"meridian.mcp_server açılmadı: {e}", file=sys.stderr)
        return 2
    serve(bot=ns.bot)
    return 0


if __name__ == "__main__":
    sys.exit(main())
