#!/usr/bin/env python3
"""research/olcumler/edg071_hayalet_suzgec/olcum.py — EDG-2026-071 RESMÎ ÖLÇÜM (KOVA C, 2026-09-04).

NE ÖLÇER. `research/cards/EDG-2026-071-hayalet-dugme-oneri-suzgeci.yaml`nin hipotezi: öneri katmanı
(`hermes.virgin_knobs` → `propose_virgin_knob`) bounds'ta olup motorda OKUYUCUSU OLMAYAN ("hayalet")
düğmelere keşif bütçesi harcıyor mu, ve Ö-48'in okuyucu-tabanlı süzgeci (`reflect.hayalet_suzgeci`)
Seçenek A yerleşimiyle (`hermes.virgin_knobs()` içinde çağrı) uygulanınca hayalet öneri 0'a iniyor mu
VE bugünkü kablolu düğmeleri (32/32) YANLIŞ-POZİTİF olarak süzüyor mu. İki K: K1 tarihsel (donmuş
hipotez defteri, üretici kırılımlı) + K2 sandbox (bugünkü bounds, gerçek süzgeç + gerçek
`propose_virgin_knob` çağrısı + fail-open sınaması). PK yol-tutarlı (D5).

`meridian/*.py` BU TURDA DEĞİŞTİRİLMEZ. Seçenek A'nın davranışı (K2 ikinci bacağı + PK) bu
SÜRECİN belleğinde `hermes.virgin_knobs` adını GEÇİCİ sarmalayarak (gerçek `virgin_knobs()` +
gerçek `reflect.hayalet_suzgeci()`nin BİLEŞİMİ) kurulur ve fonksiyon sonunda GERİ ALINIR — dosyaya
tek bayt yazılmaz (CLAUDE.md ajan sınırı: `meridian/*.py` DOKUNMA).

NEDEN MOTOR FONKSİYONLARI CANLI ÇAĞRILIYOR AMA CANLI STATE'E DOKUNULMUYOR. K2 ve PK
`reflect.hayalet_suzgeci` / `hermes.virgin_knobs` / `hermes.propose_virgin_knob`ı GERÇEKTEN
çağırır (kart D4/D5: "gerçek çağrı") — bu fonksiyonlar `obs.log`/`obs.warn` üzerinden
`state/events.jsonl`a yazar. Bu yüzden her çağrı `_sandbox()` bağlam yöneticisi içinde
`config.STATE`i geçici bir dizine yönlendirerek yapılır (gerçek `goal.yaml`/`bounds.yaml`/
`strategy.yaml` oraya KOPYALANIR, `state/hypotheses.jsonl` sandboxta YOK — H2 boş defterle başlar);
`config.STATE` her çağrının sonunda ESKİ değerine geri alınır. Kanıt uydurulmaz: betik REPO'nun
gerçek `state/*.jsonl` dosyalarının (mtime_ns, satır sayısı) izini ölçüm ÖNCESİ/SONRASI karşılaştırır
(`sandbox_kaniti` alanı) — pytest'in `sandbox_state` fikstürünün pytest-DIŞI karşılığı, elle
try/finally ile (bu betik pytest koşucusu değildir).

K1 — GİT BLOB ARKEOLOJİSİ. Donmuş `hypotheses.jsonl` defterindeki her satırın `ts`sinden ÖNCEKİ en
yakın `main` commit'i (`git rev-list -1 --before=<ts> main`, SALT OKUMA) bulunur; o commit'teki
`meridian/<MOTOR_ZINCIRI modülü>.py` blob'ları (`git show <sha>:<yol>`, SALT OKUMA) okunur ve
`reflect._motor_sabitleri_olc`ün AST çekirdeği METİN üzerinde ÇALIŞAN bir türevle (aşağıda
`_sabitler_metinlerden` — reflect'in kendisi dosya/mtime önbellekli, blob'larla çalışamaz; algoritma
BİREBİR aynı: docstring hariç tüm string sabitleri) o günün motor okuyucu kümesi bulunur. Önerilen
düğmenin (aile = `variable.split("@",1)[0]`, `analytics._knob_family`nin AYNI tek-satır kuralı) o
günkü kümede geçip geçmediği hayalet hükmünü verir. ÖZ-SINAMA: HEAD blob'undan türetilen küme, canlı
`reflect.motor_okunan_sabitler()`in (dosyadan okuyan GERÇEK fonksiyon) sonucuyla birebir eşleşmeli —
eşleşmezse türev bir yerde reflect'ten SAPMIŞ demektir (D2 zorunluluğu, `oz_sinama_head`).

ÖLÇÜM SINIRI (uydurma yasağı — kaydı `girdi/KAYNAK.md`de de var): repo'nun git tarihi
2026-07-31T10:08:23+03:00'te başlıyor. Donmuş defterin 60 satırından 42'si bu tarihten ÖNCEye
damgalı: 9 GÜN TÜMÜYLE öncesi (41 satır, 07-14/19/20/21/22/23/27/28/29) + 2026-07-31'in KENDİSİNİN
erken saati (1 satır, 02:52 UTC) — o günün İKİNCİ satırı (11:34 UTC) İLK repo commit'inden
SONRAdır ve ÇÖZÜLÜR (K1 çözümleme birimi TEK TEK `ts`dir, GÜN DEĞİL — aksi hâlde bu iki satır
yanlışlıkla aynı kovaya düşerdi, bkz. `k1_tarihsel` docstring'i). O tarihten önceki `ts`ler için
`git rev-list --before` BOŞ döner (var olmayan bir commit'e dayanan hüküm ÜRETİLMEZ); bu satırlar
`OLCULEMEDI_GIT_TARIHI_ONCESI` diye AYRI sayılır; K1'in birincil oranı yalnız ÇÖZÜLEBİLEN satırlar
üzerinden hesaplanır, 42/60 ADIYLA raporlanır.

EŞİKLER KARTTAN OKUNUR (`esikler:` bloğu YAPILANDIRILMIŞtır — EDG-019'un serbest-metin regex'i BURADA
GEREKMEZ): `hayalet_payi_alt_anlamli` (K1) ve `yanlis_pozitif_ust` (K2). Eksikse ValueError — betik
eşiği UYDURAMAZ.

KULLANIM:
    .venv/bin/python olcum.py --kuru                       # yalnız şema kontrolü, git/sandbox YOK
    .venv/bin/python olcum.py [--cikti /yol.json]           # tam ölçüm (K1+K2+PK+öz-sınama)

POZİTİF KONTROL (`pk_yol_tutarli`, kart `pozitif_kontrol` + D5, yol-tutarlı — tek-fonksiyon PK
portföy/öneri-yolu hatalarına kördür): sandbox bounds'a okuyucusu OLMAYAN sentetik bir anahtar
(`sentetik.hayalet_x`) ve okuyucusu OLAN gerçek bir anahtar (`entry.w_turnover`, strategy.py'de
okunuyor) konur; GERÇEK `hermes.propose_virgin_knob()` Seçenek A bileşimi üzerinden koşturulur:
hayalet anahtar süzgeç tarafından yakalanmalı ve öneri aday döngüsüne HİÇ girmemeli, kablolu anahtar
döngüye girip GEÇMELİ. Ön koşul (`_pk_govde_kontrolu`, v263'ün N0 deseni): GHOST literali motor
zincirinde YOK, REAL literali VAR — düşerse suçlu süzgeç değil bu betiğin fikstürüdür.

HÜKÜM YAZMAZ (CLAUDE.md §3/§5): eşik-karşılaştırma BOOLEAN'ları hesaplanır (edg019 emsalinin
`etki_esigi_gecti` deseni) ama "süzgeç uygulanır" tarzı bir karar cümlesi YOKTUR — hüküm Rol-1'de,
AYNI turda karta + K defterine işlenir.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict

import yaml

KOK = pathlib.Path(__file__).resolve().parents[3]
KART_YOLU = KOK / "research" / "cards" / "EDG-2026-071-hayalet-dugme-oneri-suzgeci.yaml"
GIRDI_VARSAYILAN = pathlib.Path(__file__).resolve().parent / "girdi" / "hypotheses_donmus_2026-09-04.jsonl"
REPO_STATE = KOK / "state"

ZORUNLU_ALANLAR = ("variable", "ts", "source")

# PK sabitleri (kart `pozitif_kontrol` literalleri, birebir)
GHOST_KNOB = "sentetik.hayalet_x"
REAL_KNOB = "entry.w_turnover"


# ======================================================================================
# EŞİKLER — KARTTAN OKUNUR (bu kartta `esikler:` YAPILANDIRILMIŞ — regex GEREKMEZ)
# ======================================================================================

def esikleri_karttan_oku(kart_yolu: pathlib.Path = KART_YOLU) -> dict:
    kart = yaml.safe_load(kart_yolu.read_text(encoding="utf-8"))
    if not isinstance(kart, dict):
        raise ValueError(f"kart sözlük değil: {kart_yolu}")
    esikler = kart.get("esikler")
    if not isinstance(esikler, dict):
        raise ValueError(f"kart 'esikler' alanı yok/sözlük değil: {kart_yolu}")
    for anahtar in ("hayalet_payi_alt_anlamli", "yanlis_pozitif_ust"):
        if anahtar not in esikler:
            raise ValueError(
                f"kart eşiği '{anahtar}' bulunamadı ({kart_yolu}) — betik eşiği UYDURAMAZ")
    return {
        "hayalet_payi_alt_anlamli": float(esikler["hayalet_payi_alt_anlamli"]),
        "yanlis_pozitif_ust": int(esikler["yanlis_pozitif_ust"]),
        "kart_id": kart.get("card_id"), "kart_yolu": str(kart_yolu),
    }


# ======================================================================================
# GİRDİ OKUMA + ŞEMA DOĞRULAMA (--kuru bunu koşar, git/sandbox/istatistik KOŞMAZ)
# ======================================================================================

def gozlem_satirlarini_oku(girdi_yolu: pathlib.Path) -> list[dict]:
    satirlar: list[dict] = []
    for i, ham in enumerate(girdi_yolu.read_text(encoding="utf-8").splitlines(), start=1):
        ham = ham.strip()
        if not ham:
            continue
        try:
            satirlar.append(json.loads(ham))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{girdi_yolu}:{i} JSON ayrıştırılamadı: {exc}") from exc
    return satirlar


def sema_ihlallerini_bul(satirlar: list[dict]) -> list[str]:
    """Zorunlu alan eksikliği (ADIM-0(a): üretici/kaynak + düğme adı okunabiliyor mu) — YASA 4:
    ihlal ADIYLA raporlanır, satır sessizce atlanmaz."""
    ihlaller: list[str] = []
    for i, s in enumerate(satirlar):
        if not isinstance(s, dict):
            ihlaller.append(f"satır {i}: dict değil ({type(s).__name__})")
            continue
        konum = f"satır {i} [{s.get('variable', '?')}]"
        eksik = [a for a in ZORUNLU_ALANLAR if not s.get(a)]
        if eksik:
            ihlaller.append(f"{konum}: zorunlu alan eksik: {eksik}")
    return ihlaller


# ======================================================================================
# GİT YARDIMCILARI — SALT OKUMA (rev-list / show / rev-parse / log); YAZAN komut YOK
# ======================================================================================

_IZINLI_GIT_KOMUTLARI = {"rev-list", "show", "rev-parse", "log", "status", "diff", "blame"}


def _git(*args: str) -> tuple[int, str, str]:
    if args[0] not in _IZINLI_GIT_KOMUTLARI:
        raise ValueError(f"izinsiz git komutu: {args[0]!r} (yalnız {sorted(_IZINLI_GIT_KOMUTLARI)})")
    p = subprocess.run(["git", *args], cwd=KOK, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def ilk_commit_zamani() -> str:
    """`main`in İLK commit'inin commit zaman damgası — K1'in git-tarihi-öncesi satırları RAPORLARKEN
    bu tarih SABİTLENMEZ, her koşumda git'ten okunur (tek-kaynak yasası)."""
    rc, out, err = _git("log", "--reverse", "--format=%cI", "main")
    if rc != 0 or not out.strip():
        raise RuntimeError(f"git log --reverse başarısız: {err.strip()}")
    return out.strip().splitlines()[0]


def commit_oncesi(ts: str) -> str | None:
    """main'de verilen ISO-8601 zaman damgasından ÖNCEKİ en yakın commit; repo tarihinden ÖNCEyse
    None (uydurma yasağı: var olmayan bir commit'e dayanan hüküm üretilmez)."""
    rc, out, err = _git("rev-list", "-1", f"--before={ts}", "main")
    if rc != 0:
        raise RuntimeError(f"git rev-list başarısız (ts={ts}): {err.strip()}")
    return out.strip() or None


_BLOB_CACHE: dict[tuple[str, str], tuple[str | None, str | None]] = {}


def blob_metni(sha: str, modul: str) -> tuple[str | None, str | None]:
    """`git show <sha>:meridian/<modul>.py` → (metin, hata). Dosya o commit'te YOKSA (metin=None,
    hata=None) — motor henüz o modülü içermiyordu, bu bir HATA değil bir TARİHÎ GERÇEKTİR (sıfır
    katkı; günün kaydında `eksik_modul` alanında görünür, sessiz değil). Başka git hatası ayrı
    döner. (sha, modul) başına önbelleklidir — aynı commit'e birden çok gün düşerse tekrar okunmaz."""
    anahtar = (sha, modul)
    if anahtar in _BLOB_CACHE:
        return _BLOB_CACHE[anahtar]
    rc, out, err = _git("show", f"{sha}:meridian/{modul}.py")
    if rc == 0:
        sonuc = (out, None)
    elif "exists on disk, but not in" in err or "does not exist" in err:
        sonuc = (None, None)
    else:
        sonuc = (None, f"git show başarısız ({sha}:meridian/{modul}.py): {err.strip()[:200]}")
    _BLOB_CACHE[anahtar] = sonuc
    return sonuc


# ======================================================================================
# AST ÇEKİRDEĞİ — `reflect._motor_sabitleri_olc`'ten TÜRETİLDİ (metin üzerinde, mtime önbelleksiz)
# ======================================================================================

def _sabitler_metinlerden(dosya_metinleri: dict[str, str | None]) -> tuple[frozenset | None, str | None]:
    """`meridian.reflect._motor_sabitleri_olc`ün AST çekirdeğinin BİREBİR AYNI mantığı (docstring
    hariç tüm string sabitleri), METİN üzerinde çalışır — reflect kaynağı DOSYADAN/mtime'dan okur,
    git blob'uyla çalışamaz; bu yüzden burada GEREKÇELİ bir KOPYA yaşar (davranış eşliği
    `oz_sinama_head()` ile HEAD'de doğrulanır). `metin=None` = modül o commit'te yoktu → SIFIR
    katkı (hata değil); parse hatası → (None, neden) — reflect'in fail-open sözleşmesiyle aynı."""
    import ast
    sabitler: set[str] = set()
    for modul, metin in dosya_metinleri.items():
        if metin is None:
            continue
        try:
            agac = ast.parse(metin)
        except (SyntaxError, ValueError) as e:
            return None, f"{modul}.py ayrıştırılamadı: {type(e).__name__}: {e}"
        docstringler: set[str] = set()
        for dugum in ast.walk(agac):
            if isinstance(dugum, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                d = ast.get_docstring(dugum, clean=False)
                if d:
                    docstringler.add(d)
        for dugum in ast.walk(agac):
            if isinstance(dugum, ast.Constant) and isinstance(dugum.value, str) \
                    and dugum.value not in docstringler:
                sabitler.add(dugum.value)
    return frozenset(sabitler), None


def oz_sinama_head() -> dict:
    """D2 zorunluluğu: HEAD blob'undan türetilen sabit kümesi == canlı `reflect.motor_okunan_
    sabitler()` (dosyadan okuyan GERÇEK fonksiyon, state'e DOKUNMAZ — güvenli çağrı)."""
    from meridian import reflect
    rc, head, err = _git("rev-parse", "HEAD")
    if rc != 0:
        raise RuntimeError(f"git rev-parse HEAD başarısız: {err.strip()}")
    head = head.strip()
    dosya_metinleri: dict[str, str | None] = {}
    for m in reflect.MOTOR_ZINCIRI:
        metin, hata = blob_metni(head, m)
        if hata is not None:
            return {"gecti": False, "head": head, "neden": hata}
        dosya_metinleri[m] = metin
    turetilen, neden = _sabitler_metinlerden(dosya_metinleri)
    if turetilen is None:
        return {"gecti": False, "head": head, "neden": neden}
    gercek = reflect.motor_okunan_sabitler()
    if gercek is None:
        return {"gecti": False, "head": head,
                "neden": "reflect.motor_okunan_sabitler() None döndü (canlı ölçülemedi)"}
    esit = turetilen == gercek
    return {
        "gecti": esit, "head": head, "n_turetilen": len(turetilen), "n_gercek": len(gercek),
        "fark_turetilen_fazla": ([] if esit else sorted(turetilen - gercek)[:20]),
        "fark_gercek_fazla": ([] if esit else sorted(gercek - turetilen)[:20]),
    }


# ======================================================================================
# K1 — TARİHSEL HAYALET PAYI, ÜRETİCİ KIRILIMI
# ======================================================================================

def k1_tarihsel(satirlar: list[dict], esikler: dict) -> dict:
    """Çözümleme birimi TEK TEK BENZERSİZ `ts`dir, gün DEĞİL. İLK sürüm günün EN ERKEN ts'siyle
    çözüyordu ve bir GÜN İÇİNDE ilk repo commit'inin öncesi/sonrasına düşen iki satırı (2026-07-31:
    02:52 UTC repo-öncesi, 11:34 UTC repo-sonrası) AYNI (yanlış) "ölçülemedi" kovasına düşürdüğü
    ÖLÇÜLEREK bulundu — bu betiğin kendi turunda yakalanan bir kırılganlık, düzeltildi. Bu girdide
    60 satırın 60'ı zaten birbirinden farklı `ts` taşıyor, yani gün-gruplama hiçbir git-çağrısı
    TASARRUFU sağlamıyordu; yalnız YANLIŞ sonuç üretiyordu. `commit_oncesi`/`blob_metni` kendi
    önbellekleriyle (ts başına bir `rev-list`, sha başına bir `git show`) tekrarı zaten önler."""
    from meridian import reflect

    ilk_main_ts = ilk_commit_zamani()
    benzersiz_ts = sorted({s["ts"] for s in satirlar})
    ts_kayitlari: dict[str, dict] = {}
    ts_sabitleri: dict[str, tuple] = {}   # ts -> (sabitler|None, neden|None, sha|None, eksik_moduller)

    for ts in benzersiz_ts:
        sha = commit_oncesi(ts)
        if sha is None:
            ts_kayitlari[ts] = {
                "commit": None, "durum": "OLCULEMEDI_GIT_TARIHI_ONCESI",
                "detay": f"main'de {ts} öncesi commit yok (repo git tarihi {ilk_main_ts}'te başlıyor)",
            }
            ts_sabitleri[ts] = (None, "git-tarihi-öncesi", None, [])
            continue
        dosya_metinleri: dict[str, str | None] = {}
        eksik: list[str] = []
        hata_var = None
        for m in reflect.MOTOR_ZINCIRI:
            metin, hata = blob_metni(sha, m)
            if hata is not None:
                hata_var = hata
                break
            if metin is None:
                eksik.append(m)
            dosya_metinleri[m] = metin
        if hata_var is not None:
            ts_kayitlari[ts] = {"commit": sha, "durum": "OLCULEMEDI_GIT_HATASI", "detay": hata_var}
            ts_sabitleri[ts] = (None, hata_var, sha, eksik)
            continue
        sabitler, neden = _sabitler_metinlerden(dosya_metinleri)
        ts_sabitleri[ts] = (sabitler, neden, sha, eksik)
        ts_kayitlari[ts] = {
            "commit": sha, "durum": ("OLCULEMEDI_PARSE" if sabitler is None else "OLCULDU"),
            "detay": neden, "eksik_modul": eksik,
            "n_sabit": (len(sabitler) if sabitler is not None else None),
        }

    # --- satır bazında hayalet hükmü (aile = analytics._knob_family'nin AYNI tek-satır kuralı) ---
    satir_sonuclari = []
    for s in satirlar:
        sabitler, neden, sha, eksik = ts_sabitleri[s["ts"]]
        aile = str(s["variable"]).split("@", 1)[0]
        if sabitler is None:
            durum, hayalet = "OLCULEMEDI", None
        else:
            hayalet = aile not in sabitler
            durum = "HAYALET" if hayalet else "TEMIZ"
        satir_sonuclari.append({
            "id": s.get("id"), "variable": s["variable"], "aile": aile, "source": s["source"],
            "ts": s["ts"], "gun": str(s["ts"])[:10], "commit": sha, "durum": durum, "hayalet": hayalet,
        })

    # --- gün bazlı ÖZET (yalnız GÖSTERİM/rapor kolaylığı — çözümleme birimi yukarıda ts'dir) ---
    gun_kayitlari: dict[str, dict] = defaultdict(lambda: {"n_satir": 0, "ts_listesi": [],
                                                          "commitler": set(), "durumlar": Counter()})
    for r in satir_sonuclari:
        g = gun_kayitlari[r["gun"]]
        g["n_satir"] += 1
        g["ts_listesi"].append(r["ts"])
        if r["commit"]:
            g["commitler"].add(r["commit"])
        g["durumlar"][r["durum"]] += 1
    gun_kayitlari = {
        gun: {"n_satir": v["n_satir"], "n_benzersiz_ts": len(v["ts_listesi"]),
             "commitler": sorted(v["commitler"]), "durum_dagilimi": dict(v["durumlar"])}
        for gun, v in sorted(gun_kayitlari.items())
    }

    olculen = [r for r in satir_sonuclari if r["hayalet"] is not None]
    hayalet_n = sum(1 for r in olculen if r["hayalet"])
    toplam_olculen = len(olculen)
    olculemedi_n = len(satir_sonuclari) - toplam_olculen
    hayalet_orani = round(hayalet_n / toplam_olculen, 4) if toplam_olculen else None

    uretici_kirilimi: dict[str, dict] = {}
    for src in sorted({r["source"] for r in satir_sonuclari}):
        grup = [r for r in satir_sonuclari if r["source"] == src]
        g_olculen = [r for r in grup if r["hayalet"] is not None]
        g_hayalet = sum(1 for r in g_olculen if r["hayalet"])
        uretici_kirilimi[src] = {
            "toplam": len(grup), "olculen": len(g_olculen), "hayalet": g_hayalet,
            "olculemedi": len(grup) - len(g_olculen),
            "hayalet_orani_olculenden": (round(g_hayalet / len(g_olculen), 4) if g_olculen else None),
        }

    return {
        "pencere": {"ilk_ts": min(s["ts"] for s in satirlar), "son_ts": max(s["ts"] for s in satirlar),
                   "toplam_satir": len(satirlar), "benzersiz_gun": len(gun_kayitlari),
                   "benzersiz_ts": len(benzersiz_ts), "repo_git_tarihi_baslangici": ilk_main_ts},
        "gun_cozumlemesi": gun_kayitlari,
        "commit_cozumleme_sayisi": len(benzersiz_ts),
        "satirlar": satir_sonuclari,
        "toplam_oneri": len(satirlar),
        "olculen_oneri": toplam_olculen,
        "olculemedi_oneri": olculemedi_n,
        "hayalet_oneri": hayalet_n,
        "hayalet_orani_olculenden": hayalet_orani,
        "esik_karsilastirma": {
            "esik": esikler["hayalet_payi_alt_anlamli"],
            "esigi_gecti_mi": (hayalet_orani is not None
                              and hayalet_orani >= esikler["hayalet_payi_alt_anlamli"]),
        },
        "uretici_kirilimi": uretici_kirilimi,
        "beyan": (f"hayalet payı yalnız GİT TARİHİYLE ÇÖZÜLEBİLEN satırlar üzerinden hesaplanır "
                 f"({toplam_olculen}/{len(satirlar)}); {olculemedi_n} satır repo git tarihinden "
                 f"ÖNCEYE damgalı (main {ilk_main_ts}'te başlıyor) ve UYDURULMADI — ayrı sayılır "
                 f"(bkz. girdi/KAYNAK.md)."),
    }


# ======================================================================================
# SANDBOX — pytest-DIŞI `sandbox_state` karşılığı (config.STATE geçici yönlendirme, try/finally)
# ======================================================================================

@contextlib.contextmanager
def _sandbox():
    """`config.STATE`i geçici bir dizine yönlendirir (gerçek goal/bounds/strategy KOPYALANIR,
    `hypotheses.jsonl` sandboxta YOK — H2 boş defterle başlar); bağlam kapanınca `config.STATE`
    ESKİ hâline GERİ ALINIR. pytest'in `sandbox_state` fikstürünün pytest-DIŞI karşılığı — bu betik
    pytest koşucusu DEĞİLDİR (CLAUDE.md D7), monkeypatch fikstürü yok, elle try/finally."""
    from meridian import config
    eski_state, eski_hist, eski_bars = config.STATE, config.HISTORY, config.BARS
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="edg071_sandbox_"))
    try:
        yeni_state = tmp / "state"
        (yeni_state / "history").mkdir(parents=True)
        (yeni_state / "bars").mkdir(parents=True)
        for ad in ("goal.yaml", "bounds.yaml", "strategy.yaml"):
            kaynak = eski_state / ad
            if kaynak.exists():
                shutil.copy2(kaynak, yeni_state / ad)
        config.STATE = yeni_state
        config.HISTORY = yeni_state / "history"
        config.BARS = yeni_state / "bars"
        config.goal.cache_clear()
        config.bounds.cache_clear()
        yield yeni_state
    finally:
        config.STATE, config.HISTORY, config.BARS = eski_state, eski_hist, eski_bars
        config.goal.cache_clear()
        config.bounds.cache_clear()
        shutil.rmtree(tmp, ignore_errors=True)


def _state_jsonl_izi() -> dict:
    """Repo'nun GERÇEK `state/*.jsonl` dosyalarının (mtime_ns, satır_sayısı) izi — sandbox kuralının
    KANITI (D7): "canlı yerel state'e yazım yok" VARSAYILMAZ, ÖLÇÜLÜR."""
    iz: dict[str, dict] = {}
    for p in sorted(REPO_STATE.glob("*.jsonl")):
        try:
            st = p.stat()
            n = sum(1 for _ in p.open("r", encoding="utf-8", errors="replace"))
            iz[p.name] = {"mtime_ns": st.st_mtime_ns, "satir": n}
        except OSError as e:
            iz[p.name] = {"hata": f"{type(e).__name__}: {e}"}
    return iz


def _state_izi_karsilastir(once: dict, sonra: dict) -> dict:
    degisen = {ad: {"once": once.get(ad), "sonra": sonra.get(ad)}
              for ad in sorted(set(once) | set(sonra)) if once.get(ad) != sonra.get(ad)}
    return {"dosya_sayisi": len(sonra), "degisen": degisen, "temiz_mi": not degisen,
           "beyan": "canlı state/*.jsonl mtime_ns+satır izi ölçüm ÖNCESİ/SONRASI karşılaştırıldı"}


# ======================================================================================
# K2 — SANDBOX: bugünkü bounds, gerçek süzgeç, gerçek propose_virgin_knob, fail-open
# ======================================================================================

def k2_olc() -> dict:
    from meridian import config, hermes, reflect, store

    with _sandbox():
        b = config.bounds()
        n_bounds = len(b)
        temiz, hayalet = reflect.hayalet_suzgeci(b, kaynak="hermes.virgin_knobs")
        yanlis_pozitif = list(hayalet or [])

        try:
            oneri = hermes.propose_virgin_knob()
            oneri_hata = None
        except Exception as e:  # sessiz-yutma DEĞİL: ölçüm burada dursa da nedeni ADIYLA aşağıda döner, yutulmaz
            oneri = None
            oneri_hata = f"{type(e).__name__}: {e}"

        # --- fail-open: motor okuyucu kümesi ÖLÇÜLEMEDİ senaryosu (v263 N5 deseni) ---
        eski_zincir = reflect.MOTOR_ZINCIRI
        try:
            reflect.MOTOR_ZINCIRI = ("boyle_bir_motor_modulu_yok_edg071",)
            temiz_fo, hayalet_fo = reflect.hayalet_suzgeci(b, kaynak="hermes.virgin_knobs")
        finally:
            reflect.MOTOR_ZINCIRI = eski_zincir

        olculemedi_olaylari = [e for e in store.read_jsonl("events.jsonl")
                               if e.get("event") == "reflect_hayalet_olculemedi"]

        return {
            "n_bounds": n_bounds,
            "yanlis_pozitif_sayisi": len(yanlis_pozitif),
            "yanlis_pozitif_liste": yanlis_pozitif,
            "temiz_sayisi": len(temiz),
            "propose_virgin_knob_gercek_cagri": {
                "oneri": oneri, "hata": oneri_hata,
                "beyan": ("bugünkü PROD davranışı — süzgeç henüz virgin_knobs() içine KABLOLANMADI, "
                         "bu tur yalnız ÖLÇÜM (meridian/*.py DEĞİŞTİRİLMEDİ)"),
            },
            "fail_open": {
                "hayalet_none_mu": hayalet_fo is None,
                "temiz_tum_anahtarlari_kapsadi_mi": sorted(temiz_fo) == sorted(b.keys()),
                "olay_yazildi_mi": bool(olculemedi_olaylari),
                "son_olay": (olculemedi_olaylari[-1] if olculemedi_olaylari else None),
                "sessizlesmedi_mi": bool(hayalet_fo is None
                                        and sorted(temiz_fo) == sorted(b.keys())
                                        and olculemedi_olaylari),
            },
        }


# ======================================================================================
# PK — YOL-TUTARLI POZİTİF KONTROL (kart `pozitif_kontrol` + D5)
# ======================================================================================

def _pk_govde_kontrolu() -> None:
    """v263 N0 deseni: GHOST_KNOB literali motor zincirinde YOK, REAL_KNOB literali VAR — düşerse
    suçlu süzgeç değil bu betiğin PK fikstürüdür."""
    from meridian import reflect
    src_dir = pathlib.Path(reflect.__file__).resolve().parent
    for m in reflect.MOTOR_ZINCIRI:
        kaynak = (src_dir / f"{m}.py").read_text()
        if GHOST_KNOB in kaynak:
            raise AssertionError(f"PK fikstürü bozuk: {GHOST_KNOB!r} literali {m}.py'de geçiyor")
    if not any(REAL_KNOB in (src_dir / f"{m}.py").read_text() for m in reflect.MOTOR_ZINCIRI):
        raise AssertionError(f"PK fikstürü bozuk: {REAL_KNOB!r} literali hiçbir motor modülünde geçmiyor")


def pk_yol_tutarli() -> dict:
    """Sentetik hayalet düğme süzgeç tarafından YAKALANIR, sentetik kablolu düğme GEÇER — GERÇEK
    `hermes.propose_virgin_knob()` (gövdesi hiç değişmedi) Seçenek A bileşimi üzerinden koşturulur.
    Bileşim: `hermes.virgin_knobs` adı bu SÜRECİN belleğinde GEÇİCİ olarak gerçek `virgin_knobs()` +
    gerçek `reflect.hayalet_suzgeci()`nin bileşimiyle değiştirilir, sonda ORİJİNAL isim GERİ TAKILIR
    — `meridian/hermes.py` dosyası HİÇ DEĞİŞMEZ."""
    from meridian import config, hermes, reflect

    _pk_govde_kontrolu()

    with _sandbox() as state_dir:
        (state_dir / "bounds.yaml").write_text(
            f"{GHOST_KNOB}: {{min: 0.0, max: 1.0, step: 0.1, type: float}}\n"
            f"{REAL_KNOB}: {{min: 0.00, max: 0.40, step: 0.05, type: float}}\n"
        )
        (state_dir / "hypotheses.jsonl").write_text("")   # boş defter — ikisi de H2-bakir
        config.bounds.cache_clear()

        orijinal_kn = hermes.virgin_knobs()   # GERÇEK çağrı — sandbox bounds'unun 2 anahtarını görür
        adlar = {r["knob"] for r in orijinal_kn}
        eksik = {GHOST_KNOB, REAL_KNOB} - adlar
        if eksik:
            return {"pk_gecti": False, "on_kosul_dustu": sorted(eksik),
                    "detay": "virgin_knobs() beklenen iki sentetik anahtarı döndürmedi — PK koşulamadı"}

        bounds_gorunumu = {r["knob"]: {"min": r["min"], "max": r["max"], "step": r["step"],
                                       "type": r["type"]} for r in orijinal_kn}
        temiz, hayalet = reflect.hayalet_suzgeci(bounds_gorunumu, kaynak="hermes.virgin_knobs")
        yakalandi_mi = GHOST_KNOB in (hayalet or [])
        gecti_mi = REAL_KNOB in temiz

        cagrilan_adlar: list[str] = []

        def _secenek_a_sarmalayici():
            # aynı süreçte H2'yi İKİNCİ kez okumamak için ilk (GERÇEK) çağrının sonucu yeniden
            # kullanılır — reflect.hayalet_suzgeci yine GERÇEK, kaynak="hermes.virgin_knobs" (Seçenek A)
            b = {r["knob"]: {"min": r["min"], "max": r["max"], "step": r["step"], "type": r["type"]}
                 for r in orijinal_kn}
            t, _h = reflect.hayalet_suzgeci(b, kaynak="hermes.virgin_knobs")
            filtreli = [r for r in orijinal_kn if r["knob"] in t]
            cagrilan_adlar.extend(r["knob"] for r in filtreli)
            return filtreli

        eski_virgin_knobs = hermes.virgin_knobs
        try:
            hermes.virgin_knobs = _secenek_a_sarmalayici
            oneri = hermes.propose_virgin_knob()   # GERÇEK, DEĞİŞMEMİŞ fonksiyon gövdesi
        finally:
            hermes.virgin_knobs = eski_virgin_knobs   # meridian/hermes.py dosyasına dokunulmadı; bellek geri alındı

        oneri_aile = (str(oneri.get("variable", "")).split("@", 1)[0] if oneri else None)
        ghost_gorundu = GHOST_KNOB in cagrilan_adlar
        real_gorundu = REAL_KNOB in cagrilan_adlar
        oneri_hayalet_mi = oneri_aile == GHOST_KNOB

        return {
            "on_kosul": {"virgin_knobs_iki_dugmeyi_de_dondurdu": not eksik},
            "izole_suzgec": {"hayalet_yakalandi": yakalandi_mi, "kablolu_gecti": gecti_mi,
                             "hayalet_listesi": list(hayalet or [])},
            "secenek_a_bilesimi": {
                "candidate_loop_gordugu_adlar": cagrilan_adlar,
                "ghost_candidate_loopta_gorundu_mu": ghost_gorundu,
                "real_candidate_loopta_gorundu_mu": real_gorundu,
            },
            "oneri": oneri, "oneri_hayalet_mi": oneri_hayalet_mi,
            "pk_gecti": bool(yakalandi_mi and gecti_mi and not ghost_gorundu and not oneri_hayalet_mi),
        }


# ======================================================================================
# ÖLÇÜM — K1 + K2 + PK + öz-sınama + sandbox kanıtı (kartın basari_tanimi bileşenleri)
# ======================================================================================

def olc(satirlar: list[dict], esikler: dict) -> dict:
    baslangic = time.perf_counter()
    once = _state_jsonl_izi()

    oz = oz_sinama_head()
    k1 = k1_tarihsel(satirlar, esikler)
    k2 = k2_olc()
    pk = pk_yol_tutarli()

    sonra = _state_jsonl_izi()
    sandbox_kaniti = _state_izi_karsilastir(once, sonra)
    sure = round(time.perf_counter() - baslangic, 3)

    return {
        "kart": esikler.get("kart_id"), "esikler": esikler,
        "oz_sinama_head": oz,
        "k1_tarihsel": k1,
        "k2_sandbox": k2,
        "k2_esik_karsilastirma": {
            "esik": esikler["yanlis_pozitif_ust"],
            "yanlis_pozitif_esigi_gecti_mi": k2["yanlis_pozitif_sayisi"] > esikler["yanlis_pozitif_ust"],
        },
        "pozitif_kontrol": pk,
        "sandbox_kaniti": sandbox_kaniti,
        "sure_saniye": sure,
        "beyan": ("Bu betik yalnız ÖLÇER; hüküm Rol-1'de, AYNI turda karta + K defterine işlenir "
                 "(CLAUDE.md §3/§5). meridian/*.py bu turda DEĞİŞTİRİLMEDİ."),
    }


# ======================================================================================
# CLI
# ======================================================================================

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="EDG-2026-071 hayalet düğme öneri süzgeci ölçümü (git blob arkeolojisi + sandbox)")
    ap.add_argument("--girdi", default=str(GIRDI_VARSAYILAN),
                    help="donmuş hypotheses.jsonl (şema: variable, ts, source zorunlu)")
    ap.add_argument("--kart", default=str(KART_YOLU), help="kart yolu (varsayılan EDG-2026-071)")
    ap.add_argument("--kuru", action="store_true",
                    help="yalnız şema + kart-eşik kontrolü — git/sandbox/istatistik KOŞMAZ")
    ap.add_argument("--cikti", default=None, help="JSON çıktısını dosyaya yaz (varsayılan: stdout)")
    a = ap.parse_args(argv)

    girdi_yolu = pathlib.Path(a.girdi)
    satirlar = gozlem_satirlarini_oku(girdi_yolu)
    ihlaller = sema_ihlallerini_bul(satirlar)

    if a.kuru:
        try:
            esikleri_karttan_oku(pathlib.Path(a.kart))
        except ValueError as e:
            ihlaller.append(f"kart eşikleri: {e}")
        if ihlaller:
            print(f"BOZUK-ŞEMA · {girdi_yolu} — {len(ihlaller)} ihlal:", file=sys.stderr)
            for i in ihlaller[:50]:
                print(f"  - {i}", file=sys.stderr)
            return 1
        print(f"GÜNCEL-ŞEMA · {girdi_yolu} — {len(satirlar)} satır, ihlal yok, kart eşikleri OKUNABİLİR")
        return 0

    if ihlaller:
        print(f"ŞEMA BOZUK, ölçüm KOŞULMADI: {ihlaller[:5]}", file=sys.stderr)
        return 1

    esikler = esikleri_karttan_oku(pathlib.Path(a.kart))
    sonuc = olc(satirlar, esikler)
    cikti = json.dumps(sonuc, ensure_ascii=False, indent=2, sort_keys=True)
    if a.cikti:
        pathlib.Path(a.cikti).write_text(cikti + "\n", encoding="utf-8")
        print(f"yazıldı: {a.cikti}")
    else:
        print(cikti)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
