"""agent_telemetry.py — AJAN ÇAĞRI TELEMETRİSİ + HAM İZ DEFTERİ (D3 modül 1 ve 2, 2026-08-07).

Kaynak: `docs/PATTERN-ETUDU-2026-08-06.md` C2-1 (S) ve C2-2 (M) · `docs/TASARIM-YONU-2026-08-07.md` §4.

NEDEN VAR — İKİ ÖLÇÜLMÜŞ KÖRLÜK, TEK MODÜL:

  (1) SÜRE TÜRETİLEMEZ. Bugünkü `agent_call` olayı model/deneme/boş/araç taşıyor ama SÜRE
      TAŞIMIYOR. Canlı defterde 2026-08-04T01:14'te iki satır var (attempt=1 @01:14:07,
      attempt=2 @01:14:17) ve aradaki 10 sn'yi ancak ÇIKARSAyabilirsiniz — o farkın içinde
      bütçe bekleyişi, skill senkronu ve iki ayrı süreç doğuşu da vardır. "Gece koşusu neden
      40 dk sürdü, hangi çağrı takıldı" sorusu bu yüzden cevapsızdı. Süre ÖLÇÜM ANINDA yazılır;
      sonradan türetilen bir süre, ölçülmemiş bir süredir (UYDURMA YASAĞI).

  (2) HAM ÇIKTI 200 KARAKTERDE KESİLİYORDU. v193'te `agent_call_empty` olayına eklenen
      `ham_stdout`/`ham_stderr` alanları TEK SATIRLIK olay alanlarıdır ve 200 karakterde
      biter. Bir Python traceback'i ya da bir sağlayıcı hata gövdesi oraya sığmaz — yani
      "boş yanıt, neden bilinmiyor" hâli 200 karakterin ötesinde hâlâ mümkündü. Tam iz AYRI
      bir deftere iner, çünkü `events.jsonl` canlıda zaten ~11 MB (ölçüldü: 2026-08-04
      yedeği, 11.190.074 bayt) ve onu ham izlerle beslemek okunabilir tek defteri öldürürdü.

MASKELEME TEK KAYNAKTIR. Sır desenleri (`_GIZLI_DESENLER` + `_JETON_RE`) ve `maskele()` gövdesi
`hermes._ham_ozet`ten BURAYA TAŞINDI; `hermes._ham_ozet` artık bu modüle DELEGE eden ince bir
sarmalayıcıdır (tarihsel ad ve v193 sözleşmesi korunur). İkinci bir maskeleme uygulaması YASAK:
iki kopya sessizce ayrışır ve ayrışan taraf sızdırır. `sirlari_maskele` ile `maskele` ayrı
işlerdir ve bu bilinçlidir — birincisi YALNIZ sır desenlerini uygular (metnin biçimine dokunmaz,
`ops/vaka_sabitle.py` fikstür dondururken onu kullanır), ikincisi defter-alanı biçimini de
uygular (ANSI sök + satırları katla + kırp).

DEFTERLER (ikisi de append-only JSONL, mevcut `store` desenine uyar; yeni biçim İCAT EDİLMEDİ):
  * `agent_calls.jsonl`  — çağrı başına KÜÇÜK telemetri satırı (süre/deneme/araç/sonuç sınıfı).
  * `agent_traces.jsonl` — çağrı başına BÜYÜK ham iz satırı (sır-maskeli stdout+stderr).
İkisi `iz_id` ile birleşir; `iz_id` ayrıca `spend.jsonl` satırının `note` alanına konabilir
(bugün konmuyor — HTTP bacağının kendi muhasebesi var, bkz. `tasiyici` alanı).

TAVANLAR ÇİVİLİDİR (C2-2'nin "budama kuralı doğuşta yazılmalı" şartı). Sayılar aşağıdaki
sabitlerde yaşar ve `tests/test_ajan_telemetri_v197.py` onları test eder:
  * ham iz: akış başına {IZ_AKIS_TAVANI_KR} karakter (maskeleme SONRASI, kırpma BEYANLI),
  * ham iz defteri: son {IZ_SATIR_TAVANI} satır (halkasal budama),
  * telemetri defteri: son {CAGRI_SATIR_TAVANI} satır,
  * türetilen en kötü hâl: ~{IZ_SATIR_TAVANI} × (2×{IZ_AKIS_TAVANI_KR} + ~600 üstbilgi) ≈ 5 MB.
TAVAN ÖLÇÜLDÜ (2026-08-07, yerel; halka tam dolu + iki akış da tavanda): ham iz defteri
4.887.600 bayt, telemetri defteri 144.460 bayt — yani türetilen 4,98 MB üst sınırı GERÇEKTEN
üst sınırdır, dilek değil. Ölçüm koşumu `tests/test_ajan_telemetri_v197.py` içinde küçültülmüş
sabitlerle tekrarlanır (tam ölçekli koşum bir testin işi değil, bir kez yapılmış bir ölçümdür).

YASA 6 (okuyucusuz yazım yok):
  * `agent_calls.jsonl` — DIŞ okuyucusu `hermes.integrations_status()` (satırları KENDİ okur,
    yorumu `ozet()`e verir) → `/api/hermes` → pano. Bu yüzden `codelaw.DECLARED_SINKS`te
    muafiyeti YOKTUR ve olmamalıdır.
  * `agent_traces.jsonl` — ham satırlar bilerek panoya TAŞINMAZ (5 MB'lık ham izi HTTP'ye
    koymak hem maliyet hem sızıntı yüzeyidir). Tüketicisi `iz_oku()` (teşhis) ve
    `ops/vaka_sabitle.py` (fikstür dondurucusu, `meridian/` DIŞINDA → statik graf göremez);
    DOLULUK durumu `ozet()["iz"]` ile aynı pano yolundan çıkar. Muafiyeti `DECLARED_SINKS`te
    gerekçesiyle beyanlıdır.

PANO NOTU (D3-UI dalgasına devir): bugün bu özet `/api/hermes` gövdesinde AKIYOR ama panoda
ÇİZİLMİYOR — `meridian/web/*` bu turun dokunma yasağındaydı. Kart (④ Öğrenme yüzeyi,
`TASARIM-YONU` §3) D3-UI dalgasının işidir; veri hazır bekliyor.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import re
import time

from . import obs, store

# ---- DEFTER ADLARI (modül düzeyinde SABİT: `codelaw.artifact_graph` adları ancak böyle çözer) ---
CAGRI_DEFTERI = "agent_calls.jsonl"
IZ_DEFTERI = "agent_traces.jsonl"

# ---- TAVANLAR VE BUDAMA (doğuşta yazıldı; disk patlaması bir arıza değil bir TASARIM hatasıdır) -
IZ_AKIS_TAVANI_KR = 8_000      # stdout/stderr BAŞINA karakter (maskeleme sonrası, kırpma beyanlı)
IZ_SATIR_TAVANI = 300          # ham iz defteri halkası — bu sayıdan eskisi düşer
CAGRI_SATIR_TAVANI = 4_000     # telemetri defteri halkası (satır ~300 bayt → ~1,2 MB)
OZET_ORNEK = 500               # `ozet()` için okunan son satır sayısı (pano ucu her istekte çağırır)
# Türetilmiş tavan — ölçü değil HESAP, ve hesabın kendisi testte çivilidir:
IZ_USTBILGI_KR = 600           # iz satırının ham-metin DIŞI alanları (ölçülmedi, ÜST SINIR kabulü)
IZ_DISK_TAVANI_MB = round(IZ_SATIR_TAVANI * (2 * IZ_AKIS_TAVANI_KR + IZ_USTBILGI_KR) / 1_000_000, 2)

# ---- SONUÇ SINIFLARI — ADLI, KAPALI KÜME -------------------------------------------------------
# Sınıf adı "boş" gibi tek kelimeye çökerse teşhis de çöker: v190/v193'ün tüm dersi buydu.
SINIF_DOLU = "dolu"                          # cevap geldi ve kullanılabilir
SINIF_BOS = "bos"                            # rc!=0 ya da boş stdout ya da 'Messages: <=1'
SINIF_YAPILANDIRMASIZ = "yapilandirmasiz"    # CLI ağa hiç çıkmadı (ilk-koşum rehberi bastı)
SINIF_CLI_BAYRAK = "cli_bayrak_desteksiz"    # `-Q` tanınmadı; bütçe iade + bayraksız yeniden koşum
SINIF_ON_UCUS_SKILL = "on_ucus_skill_hatasi" # `Unknown skill(s)`; ağa çıkılmadı, liste onarıldı
SINIF_ZAMAN_ASIMI = "zaman_asimi"            # süreç `timeout` içinde bitmedi (istisna yukarı gider)
SINIFLAR = (SINIF_DOLU, SINIF_BOS, SINIF_YAPILANDIRMASIZ, SINIF_CLI_BAYRAK,
            SINIF_ON_UCUS_SKILL, SINIF_ZAMAN_ASIMI)

# ---- TAŞIYICILAR -------------------------------------------------------------------------------
TASIYICI_AJAN = "yerel_ajan"   # hermes CLI alt süreci (`hermes._agent_call`)
TASIYICI_HTTP = "http"         # doğrudan sağlayıcı çağrısı (Claude SDK / Gemini REST)
TASIYICILAR = (TASIYICI_AJAN, TASIYICI_HTTP)

# `-Q` altında CLI oturum özeti bastırılır → araç sayısı ÖLÇÜLEMEZ. Alan None kalır ve NEDENİ
# satırda yazılı olur; 0 yazmak "araç kullanılmadı" diye okunurdu (eksik alan = sıfır sanılır sınıfı).
ARAC_OLCULEMEDI = "-Q sessiz mod CLI oturum özetini bastırır — araç sayısı bu çağrıda ÖLÇÜLEMEDİ"


# ================================================================================================
# MASKELEME — TEK KAYNAK (gövde `hermes._ham_ozet`ten taşındı, v190/v193 sözleşmesi korunarak)
# ================================================================================================
# ÜÇ DESEN, ÜÇ AYRI SIZINTI BİÇİMİ (ölçülmüş biçimler; sıra ÖNEMLİ — genelden özele):
#   (1) ADLI ATAMA: `GEMINI_API_KEY=…` / `dash_token: …`. Ad `\b`ın içinde kalabilir
#       (GEMINI_API_KEY'de `API_KEY`ten önce word-boundary YOKTUR) — bu yüzden ad çevresi
#       `[\w.\-]*` ile emilir. Ad KORUNUR: hangi sırrın yankılandığını bilmek teşhistir,
#       değerini bilmek sızıntıdır.
#   (2) `Authorization: Bearer <jeton>` — burada ayraç `:`/`=` değil BOŞLUKTUR, (1) yakalayamaz.
#   (3) ÇIPLAK JETON: ≥24 karakterlik sözcük. HEM harf HEM rakam ŞARTI var, çünkü şartsız desen
#       uzun bir İNGİLİZCE sözcüğü ya da yol parçasını da maskeler ve hata mesajını okunmaz
#       yapardı — maskeleme teşhisi öldürürse, körlüğü kapatmak yerine yer değiştirmiş oluruz.
#: "Sır gibi görünen AD" — TEK KAYNAK. Hem (1) numaralı desende hem de yapılandırılmış verinin
#: ANAHTARLARINDA aynı ad kümesi kullanılır; iki ayrı liste tutmak, birinin sessizce eskimesi
#: demekti (bu dosyanın tamamının kaçındığı sınıf).
GIZLI_AD = r"[\w.\-]*(?:api[_-]?key|apikey|token|secret|password|passwd)[\w.\-]*"
_GIZLI_AD_RE = re.compile(rf"(?i)^{GIZLI_AD}$")
_GIZLI_DESENLER = (
    (rf"(?i)\b({GIZLI_AD})\s*[:=]\s*\S+", r"\1=«gizli»"),
    (r"(?i)\bbearer\s+\S+", "Bearer «gizli»"),
)
_JETON_RE = r"[A-Za-z0-9_\-]{24,}"
_ANSI_RE = None


def gizli_ad(ad) -> bool:
    """Bu ALAN ADI bir sır taşıyor mu? (`api_key`, `dash_token`, `GEMINI_API_KEY` …)

    YAPILANDIRILMIŞ VERİNİN AVANTAJI: serbest metinde bir sır adsız durabilir, bir sözlükte
    duramaz — her değerin bir anahtarı vardır. Bu yüzden `ops/vaka_sabitle.py` çıplak-jeton
    sezgisine İHTİYAÇ DUYMAZ ve onu kapatabilir (bkz. `sirlari_maskele(ciplak_jeton=...)`)."""
    return bool(_GIZLI_AD_RE.match(str(ad or "")))


def sirlari_maskele(metin: str | None, *, ciplak_jeton: bool = True) -> str:
    """YALNIZ sır desenlerini uygular — metnin BİÇİMİNE dokunmaz (satır sonları, uzunluk aynen).

    NEDEN AYRI FONKSİYON: fikstür dondurucusu (`ops/vaka_sabitle.py`) bir olay satırındaki
    string'i maskelemek ister ama onu tek satıra KATLAMAK ya da 200 karakterde KIRPMAK istemez —
    o, veriyi bozardı ve dondurulmuş vaka gerçeğe benzemez olurdu. Sır mantığı yine de TEK
    yerdedir: `maskele()` de bu fonksiyonu çağırır, ikinci bir uygulama yoktur.

    `ciplak_jeton` — ÖLÇÜLMÜŞ BİR YANLIŞ POZİTİFİN KAPISI (2026-08-07). Üçüncü desen (≥24
    karakterlik harf+rakam sözcüğü) SERBEST METİN için bir sezgidir: CLI çıktısında bir sır
    adsız/çıplak durabilir ve yakalanmasının tek yolu budur. YAPILANDIRILMIŞ VERİDE ise aynı
    sezgi ZARARLIDIR ve bu ölçüldü: fikstür dondurulurken `plan_id = "P-2026-07-23-TMO-
    momentum_burst"` (32 karakter, harf+rakam) «uzun-jeton» diye maskelendi — yani maskeleme
    bir sırrı değil, vakanın VERİSİNİ sildi. Sözlükte her değerin bir ANAHTARI vardır ve sır
    adıyla yakalanabilir (`gizli_ad`), dolayısıyla çıplak-jeton sezgisine gerek yoktur.
    Varsayılan `True`: defter alanlarının bugünkü davranışı BİREBİR korunur."""
    t = str(metin or "")
    for desen, yerine in _GIZLI_DESENLER:
        t = re.sub(desen, yerine, t)
    if not ciplak_jeton:
        return t
    return re.sub(_JETON_RE,
                  lambda m: ("«uzun-jeton»" if (any(c.isdigit() for c in m.group(0))
                                                and any(c.isalpha() for c in m.group(0)))
                             else m.group(0)), t)


def maskele(metin: str | None, limit: int = 200) -> str:
    """Alt süreç çıktısının DEFTERE YAZILABİLİR biçimi: ANSI sökülür, satır sonları görünür tek
    karaktere katlanır (tek satırlık olay alanı), sır DESENLERİ maskelenir, sonra kırpılır.

    SIRA ÖNEMLİ — maskeleme kırpmadan ÖNCE: önce kırpsaydık `limit`. karakterde ikiye bölünen bir
    anahtarın ilk yarısı maskesiz kalırdı (yarım sır da sırdır: alfabe + uzunluk bilgisi verir).
    Kırpma sonrası uzunluk beyanı da kalır — "…(+N kr)" olmadan okuyucu kısa bir hatayı, kırpılmış
    uzun bir hatadan ayırt edemez."""
    global _ANSI_RE
    if _ANSI_RE is None:
        _ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")
    t = _ANSI_RE.sub("", str(metin or ""))
    t = t.replace("\r", " ").replace("\n", " ⏎ ").replace("\t", " ")
    t = sirlari_maskele(t)
    t = " ".join(t.split())
    if len(t) <= limit:
        return t
    return t[:limit] + f"…(+{len(t) - limit} kr)"


# ================================================================================================
# YAZIM
# ================================================================================================

def _simdi() -> str:
    """UTC — `obs`/`spend`/`memory` ile AYNI saat dilimi ve AYNI çözünürlük ailesi. Mikrosaniye
    TAŞINIR (obs saniyeye yuvarlar): aynı saniye içinde iki deneme olabiliyor (canlı ölçüm:
    `-Q` altında ön-uçuş hatası 0,9 sn'de döner) ve `iz_id` benzersizliği buna dayanır."""
    return dt.datetime.now(dt.timezone.utc).isoformat()


def iz_kimligi(ts: str, kind: str, deneme: int, alt: int) -> str:
    """Telemetri satırı ↔ ham iz satırı BİRLEŞTİRME anahtarı. Türetilmiş ve deterministiktir:
    aynı (ts, kind, deneme, alt) dörtlüsü aynı kimliği verir, rastgelelik YOK (fikstür
    dondurulduğunda kimlikler değişmemeli)."""
    damga = re.sub(r"[^0-9A-Za-z]", "", str(ts))
    return f"AC-{damga}-{re.sub(r'[^0-9A-Za-z_]', '', str(kind)) or 'generic'}-{int(deneme)}.{int(alt)}"


def _budan(defter: str, tavan: int) -> int:
    """Halkasal budama: defter `tavan`ı aşarsa son `tavan` satır kalır. Dönüş: DÜŞEN satır sayısı.

    MALİYET ÖLÇÜLDÜ, TAHMİN EDİLMEDİ (2026-08-07, yerel; halka TAM doluyken, iki akış da tavanda):
    ham iz defteri 4.887.600 bayt (türetilen tavanın altında) · yazım başına 21,7 ms (okuma +
    yeniden yazım dâhil) · `ozet()` 0,9 ms. Ajan çağrısı gecede onlarcadır (canlı ölçüm:
    2026-08-04 penceresinde 2 `agent_call`), yani bu maliyet ölçüm yolunun kendisini yavaşlatmaz.
    Sayaç tabanlı 'her K yazımda bir buda' yaklaşımı REDDEDİLDİ: sayaç süreç-içidir, restart onu
    sıfırlar ve tavan sessizce delinir (tam olarak `_fmp._HEALTH` sınıfının disk karşılığı)."""
    rows = store.read_jsonl(defter)
    if len(rows) <= tavan:
        return 0
    store.write_jsonl(defter, rows[-tavan:])
    return len(rows) - tavan


def kaydet(*, kind: str, model: str | None, deneme: int, alt: int, sure_ms: float,
           sonuc_sinifi: str, tasiyici: str = TASIYICI_AJAN, returncode: int | None = None,
           arac_cagri_n: int | None = None, on_yukleme_n: int = 0, istem: str | None = None,
           stdout: str | None = None, stderr: str | None = None,
           ts: str | None = None, **ek) -> dict | None:
    """BİR alt-süreç/HTTP koşumunun telemetri satırını (+ ham iz satırını) yaz. Dönüş: telemetri
    satırı, ya da yazım düşerse None.

    ÇAĞIRANI ASLA DÜŞÜRMEZ. Telemetri bir ölçüm yoludur; ölçümün arızası ölçülen işi öldürmemeli.
    Ama SESSİZ de kalmaz (YASA 4): düşerse `obs.warn` ile adıyla kaydedilir — sessiz bir telemetri
    arızası, "defterde hiç satır yok" ile "mekanizma hiç koşmadı"yı ayırt edilemez yapardı.

    `arac_cagri_n=None` = ÖLÇÜLEMEDİ (satırda `arac_neden` ile birlikte taşınır), 0 = ölçüldü ve
    araç kullanılmadı. İkisini tek alana katlamak, MCP yatırımının atıl olup olmadığını sonsuza
    dek cevapsız bırakırdı (`agent_tooluse.json`'daki `olculemeyen` sayacının aynı dersi)."""
    ts = ts or _simdi()
    iz_id = iz_kimligi(ts, kind, deneme, alt)
    satir = {"ts": ts, "iz_id": iz_id, "tasiyici": str(tasiyici), "kind": str(kind),
             "model": model or "varsayılan", "deneme": int(deneme), "alt": int(alt),
             "sure_ms": round(float(sure_ms), 1), "sonuc_sinifi": str(sonuc_sinifi),
             "returncode": returncode, "arac_cagri_n": arac_cagri_n,
             "on_yukleme_n": int(on_yukleme_n),
             "cikti_kr": len(stdout or ""), "hata_kr": len(stderr or "")}
    if arac_cagri_n is None:
        satir["arac_neden"] = ARAC_OLCULEMEDI
    if istem is not None:
        # İSTEM GÖVDESİ DEFTERE GİRMEZ, KİMLİĞİ GİRER. Gövde onlarca KB'dır (kanıt paketi +
        # alan sözleşmesi) ve iki çağrının AYNI istemi taşıyıp taşımadığı sorusunu özet cevaplar;
        # gövdeyi saklamak defteri 100 katına çıkarır ve tek kazanç okunabilirlik kaybı olurdu.
        satir["istem_kr"] = len(istem)
        satir["istem_ozet"] = "sha256:" + hashlib.sha256(istem.encode("utf-8")).hexdigest()[:16]
    satir.update({k: v for k, v in ek.items() if v is not None})
    try:
        with store.file_lock(CAGRI_DEFTERI):
            store.append_jsonl(CAGRI_DEFTERI, satir)
            _budan(CAGRI_DEFTERI, CAGRI_SATIR_TAVANI)
    except Exception as e:
        obs.warn("agent_telemetry_write_failed", defter=CAGRI_DEFTERI, iz_id=iz_id,
                 error=f"{type(e).__name__}: {e}",
                 detail="çağrı telemetrisi YAZILAMADI — çağrı normal devam etti; bu satırın "
                        "yokluğu 'çağrı olmadı' DEĞİL 'ölçüm kaydedilemedi' demektir")
        return None
    _iz_yaz(iz_id=iz_id, ts=ts, kind=kind, model=model, deneme=deneme, alt=alt,
            sonuc_sinifi=sonuc_sinifi, returncode=returncode, stdout=stdout, stderr=stderr)
    return satir


def _iz_yaz(*, iz_id: str, ts: str, kind: str, model: str | None, deneme: int, alt: int,
            sonuc_sinifi: str, returncode: int | None,
            stdout: str | None, stderr: str | None) -> None:
    """HAM İZ (modül 2): tam stdout+stderr, sır-maskeli, akış başına tavanlı, halkasal budamalı.

    Boş bir izin satırı YAZILMAZ: iki akış da boşsa taşınacak teşhis yoktur ve halkanın
    yerini dolu izlerden çalardı (300 satırlık pencere teşhisin görüş alanıdır)."""
    if not (stdout or stderr):
        return
    o = maskele(stdout, limit=IZ_AKIS_TAVANI_KR)
    h = maskele(stderr, limit=IZ_AKIS_TAVANI_KR)
    satir = {"ts": ts, "iz_id": iz_id, "kind": str(kind), "model": model or "varsayılan",
             "deneme": int(deneme), "alt": int(alt), "sonuc_sinifi": str(sonuc_sinifi),
             "returncode": returncode, "stdout": o, "stderr": h,
             "ham_kr": {"stdout": len(stdout or ""), "stderr": len(stderr or "")},
             "tavan_kr": IZ_AKIS_TAVANI_KR,
             "kirpildi": bool(len(stdout or "") > IZ_AKIS_TAVANI_KR
                              or len(stderr or "") > IZ_AKIS_TAVANI_KR)}
    try:
        with store.file_lock(IZ_DEFTERI):
            store.append_jsonl(IZ_DEFTERI, satir)
            dusen = _budan(IZ_DEFTERI, IZ_SATIR_TAVANI)
        if dusen:
            # BUDAMA SESSİZ OLMAZ: teşhis penceresinin kaydığı an, "izini aradığım çağrı neden
            # yok" sorusunun cevabıdır. Olay seviyesi `info` — bu bir arıza değil, sözleşme.
            obs.log("agent_trace_pruned", defter=IZ_DEFTERI, dusen=dusen, tavan=IZ_SATIR_TAVANI,
                    detail=f"ham iz defteri halkası doldu — en eski {dusen} satır düştü "
                           f"(tavan {IZ_SATIR_TAVANI} satır · akış başına {IZ_AKIS_TAVANI_KR} kr "
                           f"· türetilen disk tavanı ~{IZ_DISK_TAVANI_MB} MB)")
    except Exception as e:
        obs.warn("agent_trace_write_failed", defter=IZ_DEFTERI, iz_id=iz_id,
                 error=f"{type(e).__name__}: {e}",
                 detail="ham iz YAZILAMADI — telemetri satırı yazıldıysa `iz_id` ile aranan iz "
                        "bulunamayacak; teşhis 200 karakterlik olay özetine geri düşer")


# ================================================================================================
# OKUMA
# ================================================================================================

def iz_oku(iz_id: str | None = None, n: int = 20) -> list[dict]:
    """Ham iz satırları — `iz_id` verilirse yalnız o çağrının izi, yoksa SON `n` iz.

    TEŞHİS UCUDUR, PANO UCU DEĞİL: çağıranı `ops/vaka_sabitle.py` ve operatörün kendi
    incelemesidir. Panoya ham iz taşınmaz (bkz. modül başlığı, YASA 6 notu)."""
    rows = store.read_jsonl(IZ_DEFTERI)
    if iz_id is not None:
        return [r for r in rows if str(r.get("iz_id")) == str(iz_id)]
    return rows[-int(n):] if n else rows


def iz_durum() -> dict:
    """Ham iz defterinin DOLULUĞU — dosyayı OKUMADAN (`store.stamp` damgası: (mtime_ns, bayt)).

    NEDEN OKUMADAN: bu alan pano özetinin içindedir ve pano ucu 20 sn'de bir çağrılır; 5 MB'lık
    bir defteri sırf satır saymak için ayrıştırmak, ölçümün maliyetini ölçtüğü şeyin üstüne
    çıkarırdı. Bayt ÖLÇÜLÜR, satır sayısı ölçülmez ve bu satırda BEYAN edilir — türetilmiş bir
    satır sayısı yazmak uydurma olurdu."""
    _, bayt = store.stamp(IZ_DEFTERI)
    tavan = int(IZ_DISK_TAVANI_MB * 1_000_000)
    return {"bayt": int(bayt or 0), "satir_tavani": IZ_SATIR_TAVANI,
            "akis_tavani_kr": IZ_AKIS_TAVANI_KR, "disk_tavani_mb": IZ_DISK_TAVANI_MB,
            "doluluk": (round(int(bayt or 0) / tavan, 3) if tavan else None),
            "satir_n": None,
            "beyan": "satır sayısı ÖLÇÜLMEDİ (defter ayrıştırılmadan yalnız bayt damgası okunur); "
                     "`bayt` gerçek ölçümdür, `disk_tavani_mb` ise tavan sabitlerinden TÜRETİLMİŞ "
                     "üst sınırdır"}


def _yuzdelik(degerler: list[float], q: float) -> float | None:
    """En yakın-sıra yüzdelik (numpy'sız, deterministik). Boş listede None — 0 DEĞİL."""
    if not degerler:
        return None
    s = sorted(degerler)
    i = min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))
    return round(s[i], 1)


def ozet(satirlar: list[dict] | None = None, pencere_s: float | None = 86_400.0) -> dict:
    """Telemetri defterinin ÖZETİ — "gece koşusu neden 40 dk sürdü, hangi çağrı takıldı".

    `satirlar=None` ise defteri kendi okur; verilirse OKUMA ÇAĞIRANDA olur ve bu bilinçlidir:
    `hermes.integrations_status()` satırları `store.read_jsonl(CAGRI_DEFTERI, ...)` ile okuyup
    buraya verir, böylece `codelaw.artifact_graph` bu defteri "dış okuyucusu var" görür — YASA 6
    muafiyetiyle değil, GERÇEK bir tüketiciyle kapanır.

    `pencere_s=None` → tüm satırlar. Pencere dışı satırlar sayılmaz ama ELENDİKLERİ de yazılır
    (`pencere_disi`): boş bir özet, "hiç çağrı olmadı" ile "hepsi pencerenin dışında" arasındaki
    farkı söyleyemezse yanlış güven üretir."""
    rows = store.read_jsonl(CAGRI_DEFTERI, limit=OZET_ORNEK) if satirlar is None else list(satirlar)
    disi = 0
    if pencere_s:
        sinir = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=float(pencere_s))).isoformat()
        icinde = [r for r in rows if str(r.get("ts", "")) >= sinir]
        disi, rows = len(rows) - len(icinde), icinde
    sureler = [float(r["sure_ms"]) for r in rows if isinstance(r.get("sure_ms"), (int, float))]
    sinif: dict[str, int] = {}
    model: dict[str, int] = {}
    tasiyici: dict[str, int] = {}
    arac_olculen = arac_toplam = arac_olculemeyen = 0
    for r in rows:
        sinif[str(r.get("sonuc_sinifi", "?"))] = sinif.get(str(r.get("sonuc_sinifi", "?")), 0) + 1
        model[str(r.get("model", "?"))] = model.get(str(r.get("model", "?")), 0) + 1
        tasiyici[str(r.get("tasiyici", "?"))] = tasiyici.get(str(r.get("tasiyici", "?")), 0) + 1
        a = r.get("arac_cagri_n")
        if isinstance(a, int) and a >= 0:
            arac_olculen += 1
            arac_toplam += a
        else:
            arac_olculemeyen += 1
    en_yavas = max(rows, key=lambda r: float(r.get("sure_ms") or 0.0), default=None)
    return {
        "n": len(rows), "pencere_s": pencere_s, "pencere_disi": disi,
        "sure_ms": {"p50": _yuzdelik(sureler, 0.5), "p95": _yuzdelik(sureler, 0.95),
                    "max": (round(max(sureler), 1) if sureler else None),
                    "toplam": (round(sum(sureler), 1) if sureler else None)},
        "sinif": sinif, "model": model, "tasiyici": tasiyici,
        "arac": {"olculen": arac_olculen, "olculemeyen": arac_olculemeyen,
                 "toplam_arac": arac_toplam,
                 # ORAN YALNIZ ÖLÇÜLENİN İÇİNDE: `-Q` yüzünden ölçülemeyenleri paydaya katmak
                 # oranı sessizce seyreltirdi (`agent_tooluse.json`'ın aynı dersi).
                 "ort": (round(arac_toplam / arac_olculen, 2) if arac_olculen else None)},
        "en_yavas": ({"iz_id": en_yavas.get("iz_id"), "kind": en_yavas.get("kind"),
                      "model": en_yavas.get("model"), "sure_ms": en_yavas.get("sure_ms"),
                      "sonuc_sinifi": en_yavas.get("sonuc_sinifi")} if en_yavas else None),
        "iz": iz_durum(),
        "beyan": "süre ÖLÇÜM ANINDA yazılır (türetilemez); `arac_cagri_n=None` ÖLÇÜLEMEDİ demektir "
                 "(0 DEĞİL); ham iz satırları burada TAŞINMAZ — `agent_telemetry.iz_oku(iz_id)`",
    }


# ================================================================================================
# ÖLÇÜM SARMALAYICISI — çağıran tarafın tek satırla ölçmesi için
# ================================================================================================

class Kronometre:
    """`with Kronometre() as k: ...` → `k.ms` (milisaniye, `perf_counter` tabanlı).

    NEDEN `perf_counter`: duvar saati (`time.time`) NTP düzeltmesiyle geriye gidebilir ve bir
    çağrının süresi NEGATİF çıkabilirdi. Defterdeki `ts` duvar saatidir (olaylarla hizalanmak
    için), SÜRE ise monotonik saattendir — ikisi ayrı işler ve ayrı saat ister.

    `dur()` AYRI VE AÇIK: istisna yolunda (zaman aşımı) `__exit__` çalışmadan ÖNCE süreyi okumak
    gerekir — telemetri satırı istisna yukarı gitmeden yazılır."""

    __slots__ = ("_t0", "ms")

    def __init__(self):
        self._t0 = time.perf_counter()
        self.ms = 0.0

    def dur(self) -> float:
        """Ölçümü kapat ve milisaniyeyi döndür (yeniden çağrılırsa süre UZAR — tek atımlık kullan)."""
        self.ms = (time.perf_counter() - self._t0) * 1000.0
        return self.ms

    def __enter__(self):
        self._t0 = time.perf_counter()
        self.ms = 0.0
        return self

    def __exit__(self, *exc):
        self.dur()
        return False
