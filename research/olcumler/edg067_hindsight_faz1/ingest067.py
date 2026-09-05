# EDG-2026-067 arsiv ingest'i — A1'de systemd-run ile SEANS-DISI kosar (kill maddesi).
# Idempotent: document_id=repo-yolu (upsert) + ilerleme dosyasi; yarim kalirsa ayni komutla devam.
# Cikti /opt/hindsight/ingest067/log.txt'e (ssh-pipe kopmasi dersi: stdout'a guvenilmez).
# Bu repo kopyasi REFERANSTIR; kosan kopya A1: /opt/hindsight/ingest067/ingest067.py (yollar A1-sabit).
#
# TSK-115 (2026-09-03): Rol-1 A1 olcumu — 158 OK / 348 HATA (146 tanesi 429 ucretsiz tavan, 1
# gece once; bu gece HTTP 500 "ProviderResponseError"). Uc degisiklik:
#   D1 dilimli ana yol   — buyuk belgeler dilim_sup.dilimle() ile bolunur (ITHAL, kopya degil),
#                          her dilim AYRI document_id (`yol#k/n`); tek dilimli belge `yol` kalir.
#   D2 hata sinifli retry — hata_sinifi() 429'u DURDURUR (retry yok), 500-govde-isaretli/502/503/
#                          504/ag-hatasi GECICI (en cok 3 deneme, backoff 60/120/240 sn), diger
#                          4xx/5xx KALICI (tek deneme, retry yok).
#   D3 kosum tavani       — --cagri-tavani (varsayilan 300 POST); tavana gelince TEMIZ durur.
#   D4 ilerleme.jsonl     — artik basarisizligi da yazar (durum: ok|basarisiz|dur); yeniden
#                          kosumda YALNIZ ok atlanir, basarisiz/dur yeniden denenir.
#   D5 ozet                — ok/gecici-hata/kalici/dur sayimi + boyut bandi x sonuc tablosu.
# Onceki surumden FARK: betik artik ICE AKTARILABILIR (yan etkisiz modul govdesi, main() kapisi)
# — testler `tests/test_ingest067_retry_v387.py` gercek ag/sleep YOK, urllib+time.sleep monkeypatch.
import argparse
import importlib.util
import json
import os
import pathlib
import re
import time
import urllib.error
import urllib.request

KOK = "/opt/hindsight/ingest067"
BASE = "http://127.0.0.1:8888/v1/default"
BANK = "meridian-arsiv"
ENV_YOLU = "/opt/hindsight/.env"
VARSAYILAN_DILIM_BAYT = 32_000  # ESIK_DILIM (dilim_sup.py, 40_000) altinda baslangic degeri — olcumle ayarlanir (TSK-115)
VARSAYILAN_CAGRI_TAVANI = 300   # her deneme (ilk + retry) bir cagri sayilir


# ---- kardes betigi ITHAL et (kopya degil) -------------------------------------------------------
# `research/olcumler/` betikleri paket degil; ops.sasi_yukleyici'ye bagimlilik eklemek yerine
# ayni dans burada TEKRAR yazilir — kiyas_kos.py'deki `_kaynaktan_yukle` ile AYNI desen (TEK
# UYGULAMA ops/sasi_yukleyici.py'de, ama research/ kendi ayagi ustunde durur; iki cagri yeri
# ayni ADIMLARI atar: SourceFileLoader.exec_module DEGIL, compile(dont_inherit=True) + exec).
# KOPYA BEYANI (duzeltme turu 1, ruling KUCUK-2, 2026-09-03): bu desenin UCUNCU kopyasi — kiyas_kos.py
# kartin DONMUS olcum artefakti (kart kodu degismez, o yuzden oradaki kopya yeni bir module
# TASINAMAZ); bu dosyadaki kopya da ayni gerekcedendir. Canonical uygulama ops/sasi_yukleyici.py;
# kaynak dilim_sup.py'nin YANINDA (research/olcumler/edg067_hindsight_faz1/).
_BURASI = pathlib.Path(__file__).resolve().parent


def _kaynaktan_yukle(yol, ad):
    yol = pathlib.Path(yol)
    spec = importlib.util.spec_from_file_location(ad, yol)
    modul = importlib.util.module_from_spec(spec)
    kod = compile(yol.read_text(encoding="utf-8"), str(yol), "exec", dont_inherit=True)
    exec(kod, modul.__dict__)
    return modul


dilim_sup = _kaynaktan_yukle(_BURASI / "dilim_sup.py", "edg067_dilim_sup_ic")


# ---- D2: hata siniflandirma (saf fonksiyon, civilenir) -------------------------------------------

def hata_sinifi(status, govde):
    """429 -> dur (gunluk ucretsiz tavan, retry YOK) — govdede per-min/per-minute isareti varsa
    ISTISNA: gecici (bekle-dene, TSK-151). 500 govdesinde gunluk-kota isareti ('free-models-per-day'
    ya da 'per-day'+'RateLimit' ikilisi) -> dur (retry YOK, TSK-151); yoksa 500 govdesinde
    ProviderResponseError/overloaded/per-min/rate isareti -> gecici. 502/503/504 ve ag-hatasi/timeout
    (status=None) -> gecici. Diger 4xx/5xx -> kalici (TSK-115, 2026-09-03).

    DUZELTME TURU 1 (ruling ONEMLI-1, 2026-09-03): "rate" salt alt-dizge araniyordu — "accurate",
    "separate", "generate", "moderate" gibi YAYGIN kelimeler kalici bir 500 govdesini yanlislikla
    gecici saydirirdi (3 deneme + 420 sn bosa harcanir, tavan sayacindan 2 fazla cagri gider).
    `\\brate\\b` KELIME siniriyla arar: "rate limit asildi" / "rate-limited" gibi "rate" kelimesi
    bir baska kelimenin GOVDESI olmadan gecen govdeler yakalanir, "accurate"/"separate" gibi
    "rate" bitisik-govde iceren kelimeler yakalanmaz.

    DUZELTME TURU 2 (ruling Rol-1, TSK-151, 2026-09-05 — TSK-144 kesfi): EDG-067 r2 olcumunde
    OpenRouter hesap-geneli GUNLUK kota asimi — Hindsight'in sardigi 500 govdesinde
    'RateLimitError' / 'free-models-per-day' metni, bazen 'Rate limit exceeded:
    free-models-per-day...' — `gecici` sayiliyordu: dilim basina 3 deneme x ~200s bosa gidiyordu
    (r2: 14 dilim, 42 cagri, 47 dk). Gunluk kota hesap-geneli VE dakikalik DEGILDIR — bekleyip
    yeniden denemekle GECMEZ, bu yuzden artik `dur`. Per-minute/per-min varyanti (govdede
    'per-min' alt-dizgesi — 'per-minute' de bunu icerir) r2'de GORULMEDI ama mimariye ONDEN
    konur: o VARYANT gercekten bekle-dene sinifidir, `gecici` KALIR (429'da da 500'de de) —
    gunluk-kota isaretiyle CAKISMADIGI surece retry hakkini korur. Nvidia 'Service temporarily
    overloaded' zaten 'overloaded' isaretiyle `gecici` idi, DEGISMEDI."""
    govde_kucuk = (govde or "").casefold()
    gunluk_kota = ("free-models-per-day" in govde_kucuk
                   or ("per-day" in govde_kucuk and "ratelimit" in govde_kucuk))
    dakika_kotasi = "per-min" in govde_kucuk  # "per-minute" bu alt-dizgeyi de icerir
    if status == 429:
        if dakika_kotasi and not gunluk_kota:
            return "gecici"
        return "dur"
    if status is None:
        return "gecici"
    if status in (502, 503, 504):
        return "gecici"
    if status == 500:
        if gunluk_kota and not dakika_kotasi:
            return "dur"
        if "providerresponseerror" in govde_kucuk or "overloaded" in govde_kucuk:
            return "gecici"
        if dakika_kotasi:
            return "gecici"
        if re.search(r"\brate\b", govde_kucuk):
            return "gecici"
        return "kalici"
    return "kalici"


def backoff_sn(deneme):
    """60*2^(deneme-1): 1->60, 2->120, 3->240 (TSK-115, ölçüm 2026-09-03 vakasi 30*n yerine)."""
    return 60 * (2 ** (deneme - 1))


# ---- D1: dilim planlama (saf, dilim_sup.dilimle uzerine ince katman) -----------------------------

def belge_planla(yol, icerik, dilim_bayt):
    """(document_id, icerik, dilim_bilgi) uclulerini dondurur. Tek dilimse document_id `yol`
    olarak KALIR (idempotent upsert korunur); coklu dilimde `yol#k/n` (1-tabanli). Kayipsizlik
    dilim_sup.dilimle()'nin kendi sozlesmesidir (v366); birlesim burada da == icerik kalir."""
    dilimler = dilim_sup.dilimle(icerik, esik=dilim_bayt)
    n = len(dilimler)
    if n == 1:
        return [(yol, icerik, None)]
    return [(f"{yol}#{i}/{n}", d["metin"], f"{i}/{n}") for i, d in enumerate(dilimler, 1)]


def bant_adi(bayt):
    if bayt <= 8_000:
        return "<=8k"
    if bayt <= 16_000:
        return "<=16k"
    if bayt <= 32_000:
        return "<=32k"
    return ">32k"


# ---- ag katmani: TEK hata sinifina cevrilir -------------------------------------------------------

class _CagriHatasi(Exception):
    """HTTPError VE ag/timeout sinifi (status=None) TEK istisnaya cevrilir — hata_sinifi() tek
    noktadan siniflandirir (TSK-115, 2026-09-03)."""

    def __init__(self, status, govde):
        self.status = status
        self.govde = govde
        super().__init__(f"HTTP {status}: {govde}" if status is not None else govde)


def _cagri_yap(anahtar, base, method, path, body=None, timeout=3600):
    req = urllib.request.Request(
        base + path,
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers={"Authorization": f"Bearer {anahtar}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        raise _CagriHatasi(e.code, e.read()[:500].decode(errors="replace")) from e
    except Exception as e:  # sessiz-yutma: ag/timeout sinifi tek _CagriHatasi'na cevrilir, siniflandirma hata_sinifi'ndadir (TSK-115, 2026-09-03)
        raise _CagriHatasi(None, f"{type(e).__name__}: {e}") from e


# ---- D2+D3: tek belge/dilim gonderimi + hata-sinifli retry + cagri tavani ------------------------

def belge_isle(anahtar, base, bank, document_id, govde, cagri_sayaci, cagri_tavani):
    """En cok 3 GECICI deneme; backoff 60/120 sn YALNIZ bir SONRAKI deneme varsa (deneme<3).
    `dur` sinifinda (429 ya da cagri-tavani doldu) ANINDA doner, retry/sleep YOK.

    DUZELTME TURU 1 (ruling KUCUK-1, 2026-09-03): orijinal betik 3. (son) denemeden SONRA da
    kosulsuz `time.sleep(30*3)` cagiriyordu — bu bekleme SONUCSUZDU (deneme zaten bitiyor, bir
    sonraki deneme yok). Yeni davranis: `deneme < 3` iken bekle (60, 120), 3. deneme basarisiz
    olunca HEMEN don — A1'de her "3 denemede tukenen" belge icin bosa giden 240 sn kalkti.

    Doner: (durum, sinif, neden, yeni_cagri_sayaci, (girdi_tok, cikti_tok)).
      durum : ok | basarisiz | dur   -> ilerleme.jsonl semasi (D4)
      sinif : ok | gecici_hata | kalici | dur -> ozet sayimi (D5)
    """
    son_neden = None
    for deneme in (1, 2, 3):
        if cagri_sayaci >= cagri_tavani:
            return "dur", "dur", "cagri-tavani doldu", cagri_sayaci, (0, 0)
        cagri_sayaci += 1
        try:
            st, r = _cagri_yap(anahtar, base, "POST", f"/banks/{bank}/memories", govde)
        except _CagriHatasi as e:
            sinif = hata_sinifi(e.status, e.govde)
            son_neden = (f"HTTP {e.status} {(e.govde or '')[:150]}" if e.status is not None
                         else f"ag-hatasi {(e.govde or '')[:150]}")
            if sinif == "dur":
                return "dur", "dur", son_neden, cagri_sayaci, (0, 0)
            if sinif == "kalici":
                return "basarisiz", "kalici", son_neden, cagri_sayaci, (0, 0)
            if deneme < 3:  # son denemeden sonra bekleme YOK (KUCUK-1 duzeltmesi, TSK-115)
                time.sleep(backoff_sn(deneme))  # free-model dalgalanmasi (vaka 2026-09-01/03)
            continue
        u = r.get("usage") or {}
        gi, ci = u.get("input_tokens", 0) or 0, u.get("output_tokens", 0) or 0
        return "ok", "ok", None, cagri_sayaci, (gi, ci)
    return "basarisiz", "gecici_hata", son_neden, cagri_sayaci, (0, 0)


# ---- kill maddesi: "embedding boyutu 1024 dogrulanmadan baslayan ingest gecersiz" ----------------

def on_kontroller(anahtar, base, bank, env_metni, kayit):
    if "HINDSIGHT_API_EMBEDDINGS_ONNX_DIMENSIONS=1024" not in env_metni:
        kayit("ABORT: DIMENSIONS=1024 .env'de dogrulanamadi")
        raise SystemExit(3)
    _cagri_yap(anahtar, base, "GET", "/banks")  # servis ayakta degilse burada duser
    kayit("boyut=1024 (.env) + servis ayakta dogrulandi")
    _cagri_yap(anahtar, base, "PUT", f"/banks/{bank}", {"name": bank})
    _cagri_yap(anahtar, base, "PATCH", f"/banks/{bank}/config",
              {"updates": {"memory_defense": {"enabled": True,
                           "rules": [{"on": "sensitive_data", "action": "redact"}]}}})
    st, cfg = _cagri_yap(anahtar, base, "GET", f"/banks/{bank}/config")
    md = (cfg.get("config") or {}).get("memory_defense") or cfg.get("memory_defense") or {}
    if md.get("enabled") is not True:
        kayit("ABORT: Memory Defense acilamadi:", json.dumps(md)[:200])
        raise SystemExit(2)
    kayit("defense enabled=true dogrulandi")


def _anahtar_al(env_dosya):
    return os.environ.get("HS_KEY") or open(env_dosya, encoding="utf-8").read().split(
        "HINDSIGHT_API_TENANT_API_KEY=")[1].splitlines()[0]


# ---- is plani + ilerleme defteri -----------------------------------------------------------------

def _is_plani(kok, manifest, dilim_bayt, tamamlanan):
    """BELGE duzeyinde atlama (duzeltme turu 2, ruling K-1, TSK-115 2026-09-03): cIPLAK `yol`
    (eski sema YA DA yeni tek-dilim) `tamamlanan`da ise, bu kosumun URETTIGI dilim plani NE OLURSA
    OLSUN belge TAMAMEN atlanir — aksi halde 32-60KB bandindaki eski "ok" belgeler yeni
    `--dilim-bayt` esigini asinca `yol#k/n` kimlikleri uretilir, cIPLAK `yol` ile hic eslesmez ve
    belge parca parca TEKRAR gonderilir (KRITIK-1 ile ayni cift-LLM-maliyeti sinifi, esigi kaymis
    hali). cIPLAK `yol` tamamlanmamissa DILIM-duzeyinde filtre uygulanir: `#1/n..#n/n` HEPSI
    tamamlanan'daysa hicbiri eklenmez (belge zaten tam yuklu), EKSIK dilimler ise DENENIR."""
    isler = []
    for d in manifest["dosyalar"]:
        yol = d["yol"]
        if yol in tamamlanan:  # cIPLAK yol ok -> belge duzeyinde atla, plani hic hesaplama
            continue
        icerik = open(f"{kok}/korpus/{yol}", encoding="utf-8").read()
        for doc_id, parca, dilim_bilgi in belge_planla(yol, icerik, dilim_bayt):
            if doc_id in tamamlanan:  # bu dilim onceki kosumda ok olmus — atla, eksikler denenir
                continue
            isler.append((doc_id, parca, dilim_bilgi, d["blob"]))
    return isler


def _tamamlanan_oku(ilerleme_yolu, kayit):
    """Yalniz durum==ok olan document_id'ler atlanir (D4) — basarisiz/dur YENIDEN denenir.

    DUZELTME TURU 1 (ruling KRITIK-1, 2026-09-03): A1'in gercek `ilerleme.jsonl`'i (146 satir,
    olcum 12:52Z) ESKI semayla yazildi — `{yol, blob, sure_s, girdi_tok, cikti_tok}`, "durum" alani
    HIC YOK (eski betik yalniz BASARIYI yaziyordu, basarisizlik satiri hic dusmuyordu). `.get("durum")
    == "ok"` bu satirlari `None != "ok"` ile "bitmemis" sayardi — A1'e tasindiktan sonraki ILK
    kosumda 146 belge GEREKSIZ yeniden POST edilir, LLM sentezi ikinci kez ateslenir (gercek
    para/kota kaybi — MERIDIAN_ENGINEERING_LOG.md'deki asili ssh komutu yeniden kosulunca ingest'in
    iki surec olup "idempotent upsert bankayi korudu ama maliyeti ikiye katladi" vakasinin
    sema-gocu tekrari). Eski satirda "durum" alani YOKSA (eski semanin kendi invaryanti: yalniz
    basari yazilirdi) `ok` sayilir — `.get("durum", "ok")`."""
    tamamlanan = set()
    if os.path.exists(ilerleme_yolu):
        for satir in open(ilerleme_yolu, encoding="utf-8"):
            try:
                kayit_json = json.loads(satir)
                if kayit_json.get("durum", "ok") == "ok":
                    tamamlanan.add(kayit_json["yol"])
            except Exception as e:  # sessiz-yutma: bozuk ilerleme satiri yalnizca yeniden-isleme demektir, kayit dusuyoruz (TSK-115, 2026-09-03)
                kayit("ilerleme satiri bozuk, yok sayildi:", e)
    return tamamlanan


def _govde_kur(document_id, icerik, blob, head_commit, dilim_bilgi):
    ustveri = {"blob": blob, "commit": head_commit}
    if dilim_bilgi:
        ustveri["dilim"] = dilim_bilgi
    return {"items": [{"content": icerik, "document_id": document_id,
                       "context": "arsiv-ingest EDG-2026-067", "metadata": ustveri}],
            "async": False}


def ozet_metni(sayimlar, bant_sonuc, cagri_sayaci, sure_s):
    satirlar = [
        f"OZET: ok={sayimlar['ok']} gecici-hata={sayimlar['gecici_hata']} "
        f"kalici={sayimlar['kalici']} dur={sayimlar['dur']} "
        f"· toplam-cagri={cagri_sayaci} · sure={sure_s}s",
        "bant dagilimi:",
    ]
    for bant in ("<=8k", "<=16k", "<=32k", ">32k"):
        if bant not in bant_sonuc:
            continue
        parcalar = ", ".join(f"{d}={n}" for d, n in sorted(bant_sonuc[bant].items()))
        satirlar.append(f"  {bant}: {parcalar}")
    return "\n".join(satirlar)


def calistir(kok, dilim_bayt, cagri_tavani, anahtar, base, bank, kayit):
    """Ana kosum dongusu — kill maddesinden BAGIMSIZ, dogrudan testlenir (TSK-115, 2026-09-03)."""
    manifest = json.load(open(f"{kok}/manifest.json", encoding="utf-8"))
    ilerleme_yolu = f"{kok}/ilerleme.jsonl"
    tamamlanan = _tamamlanan_oku(ilerleme_yolu, kayit)
    isler = _is_plani(kok, manifest, dilim_bayt, tamamlanan)

    ilerleme = open(ilerleme_yolu, "a", buffering=1)
    cagri_sayaci = 0
    sayimlar = {"ok": 0, "gecici_hata": 0, "kalici": 0, "dur": 0}
    bant_sonuc = {}
    baslangic = time.time()
    for document_id, parca, dilim_bilgi, blob in isler:
        govde = _govde_kur(document_id, parca, blob, manifest["head_commit"], dilim_bilgi)
        t0 = time.time()
        durum, sinif, neden, cagri_sayaci, (gi, ci) = belge_isle(
            anahtar, base, bank, document_id, govde, cagri_sayaci, cagri_tavani)
        sure = round(time.time() - t0, 1)
        bayt = len(parca.encode())
        if durum == "ok":
            kayit(f"OK {document_id} {sure}s tok={gi}/{ci}")
        else:
            kayit(f"{durum.upper()} {document_id} sinif={sinif} neden={neden}")
        ilerleme.write(json.dumps({"yol": document_id, "dilim": dilim_bilgi, "durum": durum,
                                   "neden": neden, "bayt": bayt,
                                   "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                                  ensure_ascii=False) + "\n")
        sayimlar[sinif] += 1
        bant = bant_adi(bayt)
        bant_sonuc.setdefault(bant, {}).setdefault(sinif, 0)
        bant_sonuc[bant][sinif] += 1
        if durum == "dur":
            break
    ozet = ozet_metni(sayimlar, bant_sonuc, cagri_sayaci, round(time.time() - baslangic, 1))
    kayit(ozet)
    print(ozet)
    return sayimlar, cagri_sayaci


def _kuru_yazdir(isler):
    bant_sayim = {}
    for document_id, parca, _dilim_bilgi, _blob in isler:
        bayt = len(parca.encode())
        print(f"{document_id}  {bayt}B")
        bant = bant_adi(bayt)
        bant_sayim[bant] = bant_sayim.get(bant, 0) + 1
    print("bant dagilimi:")
    for bant in ("<=8k", "<=16k", "<=32k", ">32k"):
        if bant in bant_sayim:
            print(f"  {bant}: {bant_sayim[bant]}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--kuru", action="store_true", help="POST yok; dilim plani + bant dagilimi basar")
    ap.add_argument("--dilim-bayt", type=int, default=VARSAYILAN_DILIM_BAYT,
                    help=f"dilim esigi (bayt); varsayilan {VARSAYILAN_DILIM_BAYT}")
    ap.add_argument("--cagri-tavani", type=int, default=VARSAYILAN_CAGRI_TAVANI,
                    help=f"kosum basina en cok POST denemesi; varsayilan {VARSAYILAN_CAGRI_TAVANI}")
    ap.add_argument("--kok", default=KOK, help=f"manifest/korpus/ilerleme koku; varsayilan {KOK}")
    ap.add_argument("--env-dosya", default=ENV_YOLU,
                    help=f"HINDSIGHT_API_TENANT_API_KEY icin .env yolu; varsayilan {ENV_YOLU}")
    ns = ap.parse_args(argv)

    log = open(f"{ns.kok}/log.txt", "a", buffering=1)

    def kayit(*a):
        log.write(time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a) + "\n")

    manifest = json.load(open(f"{ns.kok}/manifest.json", encoding="utf-8"))

    if ns.kuru:
        tamamlanan = _tamamlanan_oku(f"{ns.kok}/ilerleme.jsonl", kayit)
        isler = _is_plani(ns.kok, manifest, ns.dilim_bayt, tamamlanan)
        _kuru_yazdir(isler)
        return 0

    anahtar = _anahtar_al(ns.env_dosya)
    env_metni = open(ns.env_dosya, encoding="utf-8").read()
    on_kontroller(anahtar, BASE, BANK, env_metni, kayit)
    sayimlar, _cagri_sayaci = calistir(ns.kok, ns.dilim_bayt, ns.cagri_tavani, anahtar,
                                       BASE, BANK, kayit)
    return 0 if (sayimlar["gecici_hata"] == 0 and sayimlar["kalici"] == 0
                and sayimlar["dur"] == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
