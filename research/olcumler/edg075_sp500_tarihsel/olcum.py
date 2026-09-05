"""research/olcumler/edg075_sp500_tarihsel/olcum.py — EDG-2026-075 ÖLÇÜM aracı (TSK-156, 2026-09-05).

NE ÖLÇER. Kart `research/cards/EDG-2026-075-sp500-tarihsel-bilesenler-pit-kaynagi.yaml`nin
hipotezi: Wikipedia'nın AYRI maddesi "Historical components of the S&P 500" (`meridian/adapters/
constituents.py::_fetch_tables`in bugün baktığı `List_of_S%26P_500_companies` DEĞİL — o sayfanın
'Selected changes' tablosu TSK-154'te kalktı) S&P 500 üyelik değişikliklerini (eklenen/çıkarılan +
yürürlük tarihi) 2020-01-01'den bugüne EKSİKSİZ verir mi; bu tablo `as_of(date)` PIT üyelik
yeniden kurulumuna kaynak olabilir mi.

ROL: ÖLÇÜM ajanı. Bu modül HÜKÜM VERMEZ, karta DOKUNMAZ, `meridian/*.py`ye DOKUNMAZ, canlı state'e
YAZMAZ. Eşikler (`esikler.k1_gecti`, `esikler.k2_gecti`) kartın `esikler:` alanından ÇALIŞMA ANINDA
okunur, koda kopyalanmaz (`esikleri_karttan_oku` — edg071 emsali, `research/olcumler/
edg071_hayalet_suzgec/olcum.py::esikleri_karttan_oku` ile AYNI desen: kart sözlük değilse/eşik
alanı yoksa ValueError, UYDURMA YOK).

AĞ YALNIZ `--cek`TE. `cek()` fonksiyonu iki HTTP GET yapar: (1) maddenin GÜNCEL sürümünü çekip
`oldid_bul()` ile `wgRevisionId`i okur (JS config literali — `action=info` sayfası MediaWiki
sürümüne göre biçim değiştirebildiği için daha kırılgan; gömülü `mw.config` JSON'u DEĞİŞMEDİ), (2)
`?oldid=<N>` ile o sürümü SABİTLEYEREK yeniden çeker (EDG-059 dersi: girdi çalışma ağacına değil
içerik-adresli bir şeye bağlanmalı — burada "içerik" MediaWiki'nin kendi revizyon numarasıdır).
HTML `ham/<oldid>_<sha256[:16]>.html` olarak İÇERİK-ADRESLİ kaydedilir (`.gitignore`: bu dizin
git-izli DEĞİL — TSK-156 briefi: "benzer dizinler nasıl ignore edilmiş" ölçüldü, emsal
`research/olcumler/*/state/` ve `research/olcumler/**/_cache/`: ham/yeniden-üretilebilir/büyük
ölçüm girdileri commit'lenmez, `olcum.py` + `sonuc.json` KAYNAK olarak kalır).

`--olc` AĞA ÇIKMAZ: yalnız diskteki (veya `--girdi` ile verilen) ham HTML'i okur. Bu betiğin BU
turdaki testi (`tests/test_edg075_olcum_v420.py`) YALNIZ sentetik fikstür HTML'iyle koşar — gerçek
Wikipedia sayfası bu ajan turunda HİÇ çekilmedi (CLAUDE.md ajan kuralı: pytest-dışı, ağa/obs'a
ulaşan koşum yasak). Gerçek `--cek` + `--olc` koşumu Rol-1'e bırakılır.

SÜTUN EŞLEŞMESİ ÖLÇÜLÜR, VARSAYILMAZ (`_kolon_bul`/`hedef_tablo_bul`): `_fetch_tables`teki
(`meridian/adapters/constituents.py`) alt-dizge eşleştirme deseni AYNEN devralındı ("Date" in c,
"Added" in c, vb. — tuple/MultiIndex kolonlar `"_".join(...)` ile düzleştirilir). Bu sayfanın
kolonları `List_of_S%26P_500_companies`ninkinden FARKLI olabilir (kart notu: 'Effective Date'/
'Added'/'Removed'/'Reason' — belki de 'Added'/'Removed' altında ayrı 'Ticker'/'Security' alt-
kolonları, rowspan'lı iki satır başlık) — bu yüzden eşleşen kolon ADLARI `sonuc.json`a YAZILIR
(Yasa 6: okuyucusuz ölçüm yok — Rol-1 gerçek `--cek` sonrası bunu okur ve karttaki adım_0(a)yı
buradan doğrular).

HAYALET-SATIR SÜZGECİ (TSK-154 dersi AYNEN, `constituents.py` şerhi (e)): bir satırın tarih/eklenen
/çıkan/neden alanlarının HEPSİ boşsa (rowspan/birleşik hücre artığı) `degisiklikler`e YAZILMAZ.
FARK: bu sayfanın gerçek tablosu "yalnız eklenen" ya da "yalnız çıkan" satırlar barındırabilir
(aynı yürürlük tarihinde birden çok değişiklik ayrı satırlarda, tarih hücresi rowspan'lı) — böyle
bir satır HAYALET DEĞİLDİR, iki alanından biri dolu olduğu sürece TUTULUR (yalnız TÜMÜ boş satır
atılır).

K1 (BİLİNEN OLAYLAR — TÜRETME BEYANI). Kartın `olcum_plani`si "BİLİNEN 10 olay" der, ama kartın
PROSE'unda (`card_id`den ÖNCEKİ başlık yorumu, "K1: ... BİLİNEN 10 olayla çapraz-doğrulama"
cümlesi) sayılabilen ayrık (sembol, yön, tarih) olgusu 14'TÜR: EA(çıkış)/FERG(giriş) 2026-08-05; AVB(çıkış)/EQR(çıkış)/RDDT(giriş)/VMRK(giriş) 2026-08-18;
CAG 2026-06-30, MTCH 2026-03-09, ENPH 2025-09-22 (yön kartta YAZILI DEĞİL — üçü de tek başına
anılmış, "çıkış/giriş" sözcüğü yok); VFC(çıkış)/SOLV(giriş) 2024-04-01; BE/P/ILMN(hepsi giriş)
2026-09-04. UYDURMA YASAĞI gereği yönü belirtilmeyen 3 olay `yon=None` + `yon_kaynak="kartta
belirtilmedi"` ile taşınır (K1 yön-doğruluğu kontrolü bu 3ü için None döner, True/False UYDURULMAZ).
Bu betik 14 olguyu da `BILINEN_OLAYLAR`da tutar ve `k1_bilinen_olaylar()` çıktısında hem 14'ü hem
kartın beyan ettiği "10"u (`kart_beyan_n`) yan yana raporlar — SAYI UYUŞMAZLIĞI Rol-1'e AÇIK KALEM
olarak taşınır, betik kendi başına 10'a ZORLAMAZ (bu da uydurma olurdu).

K2 (`as_of` yeniden kurulum): `meridian/adapters/constituents.py::as_of`in AYNI geri-sarma algoritması (bir değişiklik
`tarih`ten SONRAysa: eklenen sembol o tarihte üye DEĞİLDİ → çıkar; çıkarılan sembol o tarihte
üyeydi → ekle) — ŞASİ farklı: bu modül `constituents`i import ETMEZ (ayrı sayfa, ayrı veri), aynı
mantığı BAĞIMSIZ uygular (tek-kaynak yasası ihlali değil: iki modül iki FARKLI Wikipedia sayfasını
okuyor, algoritma paylaşımı isteniyorsa bu KOVA B sonrası ayrı iştir). Güncel üyelik listesi bu
betiğe `--guncel-liste <json>` ile DIŞARIDAN verilir (bu sayfa güncel liste taşımaz); verilmezse
K2 "çalışmadı + neden" ile None taşır (uydurma yok).

POZİTİF KONTROL: `enjekte_pk_satiri()` ham HTML'deki HEDEF tabloya (`hedef_tablo_bul` ile
BULUNMUŞ — indeksi varsayılmaz) sentetik bir `<tr>` ekler (ZZQ1, giriş, 2026-07-01) ve AYNI
`tabloyu_ayristir()` ile yeniden ayrıştırır: K1 eşleşme sayısı DEĞİŞMEMELİ (ZZQ1 bilinen olay
değil), `as_of(2026-07-02)` ZZQ1'i içermeli, `as_of(2026-06-30)` içermemeli (kart `pozitif_kontrol`
birebir). Enjeksiyon RAW HTML üzerinde yapılır (DataFrame'e değil) — parser'ın GERÇEKTEN tabloyu
okuduğunun kanıtı budur (yol-tutarlı, edg072/edg071 PK felsefesiyle aynı).

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen `None` + neden — yön bilinmeyen 3 olay, K2 güncel-listesiz).
YASA 4 (sessiz-yutma işaretli + gerekçe — `_tarihi_isoya_cevir`, `_kolon_bul`). YASA 6 (okuyucu:
`sonuc.json` → Rol-1 karta+K defterine işler; RAPOR.md bu betik tarafından YAZILMAZ).

======================================================================================
EDG-2026-076 EKLERİ (ajan dilimi, 2026-09-05) — AYNI betik, kartı DEĞİŞTİRİLDİ.
======================================================================================
Kart `EDG-2026-076-sp500-tarihsel-bilesenler-dogrulanmis-olay-kumesi.yaml`nin önsözü: EDG-075'in
K1 kalışları (7/14) KART-VERİ hatasıydı (rename ticker'ı giriş/çıkış sayılmış, duyuru/yürürlük
tarihi karıştırılmış) — §5 "ölçümle çürüyen kriter YERİNDE düzeltilmez" gereği bu betik
DEĞİŞTİRİLMEDİ, YENİ bir kart + betiğin dört yeni yüzeyi eklendi:

  (a) K1 OLAY KÜMESİ KARTTAN (`k1_olaylari_ve_beyan`): `--kart` kartı `bilinen_olaylar` YAML
      listesi taşıyorsa K1 olayları ORADAN kurulur (kart alanı `kaynak` → betiğin iç şeması
      `yon_kaynak`a YENİDEN ADLANDIRILIR, kopyalanmaz — tek-kaynak yasası). Kart bu alanı
      TAŞIMIYORSA (EDG-075 kartı) modülün sabit `BILINEN_OLAYLAR`/`KART_BEYAN_N`si AYNEN döner —
      EDG-075 ölçümü GERİYE DÖNÜK bozulmadı. `k1_bilinen_olaylar` artık `kart_beyan_n`i PARAMETRE
      olarak alır (önceden modül sabiti `KART_BEYAN_N`e SABİTLENMİŞTİ).

  (b) K1n GELECEK OLAYLAR (`k1n_gelecek_olaylar`): kartın `gelecek_olaylar` listesindeki, henüz
      YÜRÜRLÜĞE GİRMEMİŞ olguları sınar — iki koşulun VE'si: (i) tabloda yürürlük satırı YOK
      (±1 iş günü, BEKLENEN False — henüz gerçekleşmedi), (ii) `as_of(bugün)` yönle TUTARLI
      (yön=çıkış ise sembol HÂLÂ üye, yön=giriş ise HENÜZ üye DEĞİL). Yön belirtilmemiş olguda
      (ii) `None` kalır — UYDURULMAZ, 'geçti' otomatik False'a düşer (bilinmeyeni doğru SAYMAZ).

  (c) rename_siniri RAPORU (`rename_siniri_raporu`): K DEĞİL, eşik YOK — kartın `rename_siniri`
      kaydı için `as_of(t1)`/`as_of(bugün)`de eski/yeni sembol üyeliğini yalnız RAPORLAR (kaynak
      sınırı ölçümü, TSK-156 tasarımına girdi — kart notu).

  (d) KART İÇ TUTARLILIĞI + `--beklenen-sha` (`kart_ic_tutarliligi`, `adim0` genişlemesi):
      `bilinen_olaylar`daki HER tarih `--bugun`e eşit ya da öncesi, `gelecek_olaylar`daki HER
      tarih `--bugun`den SONRA olmalı — değilse (ya da verilen `--beklenen-sha` ham dosyanın
      GERÇEK sha256'sıyla eşleşmiyorsa) `adim_0_fizibilite.gecerli=False` + `neden`, ve
      K1/K1n/K2/pozitif_kontrol o turda KOŞMAZ — ilgili dört alan `None` yazılır (sonuç YİNE
      üretilir, Yasa 6; "hüküm koşulamaz" DEMEZ, yalnız "burada koşulmadı + nedeni budur" der).
      `rename_siniri_raporu` bu kapının DIŞINDA kalır (K değil — kartın kendi tasarımı, brief).
      NOT: `adim0`nun ESKİ `a`-`d` kriterleri (tablo okunuyor mu / oldid sabit mi / pencere ≥100
      satır mı / tüm tarihler ayrıştı mı) hâlâ RAPORLANIR ama artık genel `gecerli`ye KATILMAZ
      (o kriterler EDG-075'in GERÇEK tam sayfası için bir zenginlik ölçütüydü, hiçbir sürümde
      K1/K2/PK'yi KAPATMADI — EDG-076'nın yeni `gecerli` alanı yalnız sha+kart-tutarlılığını
      kapı yapar, `tests/test_edg075_olcum_v420.py`nin küçük sentetik fikstürü hâlâ AYNEN geçer).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import pathlib
import re
import sys

import pandas as pd
import yaml

KOK = pathlib.Path(__file__).resolve().parents[3]
KART_YOLU = KOK / "research" / "cards" / "EDG-2026-075-sp500-tarihsel-bilesenler-pit-kaynagi.yaml"
SANDBOX = pathlib.Path(__file__).resolve().parent
HAM_DIR = SANDBOX / "ham"

WIKI_TITLE = "Historical_components_of_the_S%26P_500"
WIKI_URL = f"https://en.wikipedia.org/wiki/{WIKI_TITLE}"
PENCERE_BASLANGIC = "2020-01-01"          # kart `veri_penceresi`

# ======================================================================================
# BİLİNEN OLAYLAR — kart prose'undan TÜRETİLDİ (modül başlığı "K1" bölümü — TÜRETME BEYANI).
# Yön bilinmeyen üç olay (CAG/MTCH/ENPH) `yon=None` — UYDURULMADI.
# ======================================================================================
KART_BEYAN_N = 10          # kartın `olcum_plani`sindeki literal sayı (prose, alan DEĞİL)
BILINEN_OLAYLAR: list[dict] = [
    {"sembol": "EA",   "yon": "cikis", "tarih": "2026-08-05", "yon_kaynak": "kart: 'EA ... çıkış'"},
    {"sembol": "FERG", "yon": "giris", "tarih": "2026-08-05", "yon_kaynak": "kart: 'FERG giriş'"},
    {"sembol": "AVB",  "yon": "cikis", "tarih": "2026-08-18", "yon_kaynak": "kart: 'AVB+EQR ... çıkış'"},
    {"sembol": "EQR",  "yon": "cikis", "tarih": "2026-08-18", "yon_kaynak": "kart: 'AVB+EQR ... çıkış'"},
    {"sembol": "RDDT", "yon": "giris", "tarih": "2026-08-18", "yon_kaynak": "kart: '.../RDDT+VMRK' (giriş, çıkış/giriş çiftinin ikinci yarısı)"},
    {"sembol": "VMRK", "yon": "giris", "tarih": "2026-08-18", "yon_kaynak": "kart: '.../RDDT+VMRK' (giriş, aynen)"},
    {"sembol": "CAG",  "yon": None,    "tarih": "2026-06-30", "yon_kaynak": "kartta belirtilmedi (tek başına anılmış)"},
    {"sembol": "MTCH", "yon": None,    "tarih": "2026-03-09", "yon_kaynak": "kartta belirtilmedi (tek başına anılmış)"},
    {"sembol": "ENPH", "yon": None,    "tarih": "2025-09-22", "yon_kaynak": "kartta belirtilmedi (tek başına anılmış)"},
    {"sembol": "VFC",  "yon": "cikis", "tarih": "2024-04-01", "yon_kaynak": "kart: 'VFC .../SOLV' (çıkış/giriş çiftinin ilk yarısı)"},
    {"sembol": "SOLV", "yon": "giris", "tarih": "2024-04-01", "yon_kaynak": "kart: 'VFC .../SOLV' (giriş, aynen)"},
    {"sembol": "BE",   "yon": "giris", "tarih": "2026-09-04", "yon_kaynak": "kart: 'BE/P/ILMN girişleri'"},
    {"sembol": "P",    "yon": "giris", "tarih": "2026-09-04", "yon_kaynak": "kart: 'BE/P/ILMN girişleri'"},
    {"sembol": "ILMN", "yon": "giris", "tarih": "2026-09-04", "yon_kaynak": "kart: 'BE/P/ILMN girişleri'"},
]

# PK sabitleri (kart `pozitif_kontrol` literalleri, birebir)
PK_SEMBOL = "ZZQ1"
PK_TARIH = "2026-07-01"


# ======================================================================================
# EŞİKLER — KARTTAN OKUNUR (edg071 emsali — `esikleri_karttan_oku`)
# ======================================================================================

def esikleri_karttan_oku(kart_yolu: pathlib.Path = KART_YOLU) -> dict:
    kart = yaml.safe_load(kart_yolu.read_text(encoding="utf-8"))
    if not isinstance(kart, dict):
        raise ValueError(f"kart sözlük değil: {kart_yolu}")
    esikler = kart.get("esikler")
    if not isinstance(esikler, dict):
        raise ValueError(f"kart 'esikler' alanı yok/sözlük değil: {kart_yolu}")
    for anahtar in ("k1_gecti", "k2_gecti"):
        if anahtar not in esikler:
            raise ValueError(f"kart eşiği '{anahtar}' bulunamadı ({kart_yolu}) — betik eşiği UYDURAMAZ")
    sonuc = {
        "k1_gecti": str(esikler["k1_gecti"]), "k2_gecti": str(esikler["k2_gecti"]),
        "kart_id": kart.get("card_id"), "kart_yolu": str(kart_yolu),
    }
    if "k1n_gecti" in esikler:               # EDG-076: yeni anahtar VARSA geçirilir — ZORUNLU
        sonuc["k1n_gecti"] = str(esikler["k1n_gecti"])   # DEĞİL (EDG-075 kartı bunu taşımaz, geriye dönük kırılmaz)
    return sonuc


def kart_yukle(kart_yolu: pathlib.Path) -> dict:
    """Kart YAML'ının TAMAMINI okur (`esikleri_karttan_oku` yalnız `esikler:` alanını döner). K1
    (`bilinen_olaylar`), K1n (`gelecek_olaylar`), rename raporu (`rename_siniri`) ve kart-iç-
    tutarlılığı buradan okunur. Sözlük değilse ValueError (UYDURMA YOK — `esikleri_karttan_oku`
    ile AYNI disiplin)."""
    kart = yaml.safe_load(pathlib.Path(kart_yolu).read_text(encoding="utf-8"))
    if not isinstance(kart, dict):
        raise ValueError(f"kart sözlük değil: {kart_yolu}")
    return kart


# ======================================================================================
# --cek: AĞ (yalnız bu bölüm HTTP yapar)
# ======================================================================================

def oldid_bul(html: str) -> int | None:
    """Güncel sayfa HTML'inden MediaWiki `wgRevisionId`sini okur — `mw.config.set({"wgRevisionId":N,
    ...})` gömülü JS'i (biçimi `action=info`den daha kararlı; sürüm numarası MediaWiki'nin kendi
    revizyon kimliğidir). Bulunamazsa None (UYDURMA YOK — çağıran `--cek`i başarısız sayar)."""
    m = re.search(r'"wgRevisionId":\s*(\d+)', html)
    return int(m.group(1)) if m else None


def cek(oldid: int | None = None, ham_dir: pathlib.Path = HAM_DIR) -> dict:
    """Sayfayı oldid ile SABİTLEYEREK çeker; `ham/<oldid>_<sha256[:16]>.html`e yazar. `oldid`
    verilmezse önce güncel sürümden okunur (iki GET). Yalnız `--cek` bunu çağırır — pytest bunu
    ÇAĞIRMAZ (ağa çıkmaz, monkeypatch da yok: bu fonksiyon testin kapsamı DIŞINDA — modül başlığı)."""
    import httpx
    if oldid is None:
        r0 = httpx.get(WIKI_URL, timeout=20, headers={"User-Agent": "Meridian/1.0"}, follow_redirects=True)
        if r0.status_code >= 400:
            return {"ok": False, "adim": "guncel_cek", "hata": f"HTTP {r0.status_code}"}
        oldid = oldid_bul(r0.text)
        if oldid is None:
            return {"ok": False, "adim": "oldid_bul", "hata": "wgRevisionId bulunamadı"}
    r = httpx.get(f"{WIKI_URL}?oldid={oldid}", timeout=20, headers={"User-Agent": "Meridian/1.0"},
                  follow_redirects=True)
    if r.status_code >= 400:
        return {"ok": False, "adim": "oldid_cek", "oldid": oldid, "hata": f"HTTP {r.status_code}"}
    html = r.text
    sha = hashlib.sha256(html.encode("utf-8")).hexdigest()
    ham_dir.mkdir(parents=True, exist_ok=True)
    yol = ham_dir / f"{oldid}_{sha[:16]}.html"
    yol.write_text(html, encoding="utf-8")
    return {"ok": True, "oldid": oldid, "sha256": sha, "ham_yol": str(yol),
            "cekildi_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


def en_yeni_ham_dosya(ham_dir: pathlib.Path = HAM_DIR) -> pathlib.Path | None:
    dosyalar = sorted(ham_dir.glob("*.html"), key=lambda p: p.stat().st_mtime) if ham_dir.exists() else []
    return dosyalar[-1] if dosyalar else None


# ======================================================================================
# TARİH/SEMBOL NORMALİZASYONU
# ======================================================================================

def _tarihi_isoya_cevir(ham: str) -> str | None:
    """'March 18, 2024' / 'YYYY-MM-DD' / footnote'lu ('September 23, 2024[1]') → ISO. Ayrıştırılamazsa
    None (YASA 4: sessiz atlama değil — çağıran None'ı 'tarih yok' diye sayar ve satırı raporlar)."""
    s = re.sub(r"\[[^\]]*\]", "", str(ham or "")).strip()
    s = re.sub(r"\s+", " ", s)
    if not s:
        return None
    try:
        return dt.date.fromisoformat(s[:10]).isoformat()
    except ValueError:  # sessiz-yutma: ISO değil — insan-okunur biçim aşağıda ayrıca denenir, iki deneme de düşerse None
        pass
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%B %d %Y"):
        try:
            return dt.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:  # sessiz-yutma: biçim adaylarından biri — sıradaki denenir, hiçbiri tutmazsa pandas'a düşülür
            continue
    try:
        ts = pd.to_datetime(s, errors="coerce")
        return None if ts is None or pd.isna(ts) else ts.date().isoformat()
    except Exception:  # sessiz-yutma: pandas da çözemedi — None + çağıran satırı 'tarih_ayristirilamadi' diye sayar
        return None


def _tick(v) -> str | None:
    """Ticker hücresi → temiz sembol; NaN/boş/'—' → None (constituents.py::_tick ile aynı ruh,
    None döner çünkü burada 'üye değildi' ile 'hücre boş' AYRI anlam taşır — [] yerine None)."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = re.sub(r"\[[^\]]*\]", "", str(v)).strip().upper().replace(".", "-")
    return None if s in ("", "NAN", "NONE", "N/A", "-", "—") else s


def _hucre(v) -> str:
    return "" if v is None or (isinstance(v, float) and pd.isna(v)) else re.sub(r"\[[^\]]*\]", "", str(v)).strip()


# ======================================================================================
# TABLO AYRIŞTIRMA — kolon eşleşmesi ÖLÇÜLÜR (varsayılmaz), hayalet-satır süzgeci
# ======================================================================================

def _kolon_adi(c) -> str:
    return "_".join(str(x) for x in c) if isinstance(c, tuple) else str(c)


def _kolon_bul(kolonlar: list[str], *gerekli: str, haric: str = "") -> str | None:
    """Alt-dizge eşleşmesi (case-insensitive) — `meridian/adapters/constituents.py::_fetch_tables`in `"Date" in c`
    deseninin genellenmiş hâli. `haric` verilirse o alt-dizgeyi TAŞIYAN kolonlar elenir (ör.
    'added' ararken 'ticker' TAŞIMAYANI istemek için `haric='ticker'` — Security alt-kolonunu
    Ticker'dan ayırmak için)."""
    for c in kolonlar:
        lc = c.lower()
        if all(g.lower() in lc for g in gerekli) and (not haric or haric.lower() not in lc):
            return c
    return None


def hedef_tablo_bul(html: str) -> tuple[int, "pd.DataFrame", dict] | tuple[None, None, dict]:
    """Sayfadaki TÜM tabloları okur, değişiklik-günlüğü ŞEMASINA (tarih + en az bir yön kolonu)
    uyan İLK tabloyu döndürür. Uymayan (`(None, None, meta)`) — kart adım_0(a) burada DÜŞER."""
    try:
        tables = pd.read_html(io.StringIO(html), flavor="lxml")
    except ValueError as e:  # sessiz-yutma: gövdede HİÇ tablo yok (403 gövdesi vb.) — adım_0(a) bunu 'a_tablo_okunuyor=False' + hata metniyle görür
        return None, None, {"tablo_index": None, "n_tablo": 0, "kolonlar_ham": [],
                            "hata": f"{type(e).__name__}: {e}"}
    for i, df in enumerate(tables):
        kolonlar = [_kolon_adi(c) for c in df.columns]
        dcol = _kolon_bul(kolonlar, "date")
        acol_ticker = _kolon_bul(kolonlar, "added", "ticker")
        rcol_ticker = _kolon_bul(kolonlar, "removed", "ticker")
        acol_any = acol_ticker or _kolon_bul(kolonlar, "added")
        rcol_any = rcol_ticker or _kolon_bul(kolonlar, "removed")
        if dcol and (acol_any or rcol_any):
            # ad/isim alt-kolonu YALNIZ 'added'/'removed' bir TİCKER alt-kolonuyla eşleştiyse aranır
            # (yani ayrı Ticker/Security alt-başlıkları GERÇEKTEN var) — tek düz 'Added' kolonu
            # varsa (alt-kolon YOK) `acol_any` zaten o kolonun kendisidir, ikinci bir isim kolonu YOK.
            acol_n = _kolon_bul(kolonlar, "added", haric="ticker") if acol_ticker else None
            rcol_n = _kolon_bul(kolonlar, "removed", haric="ticker") if rcol_ticker else None
            reason_col = _kolon_bul(kolonlar, "reason")
            meta = {"tablo_index": i, "n_tablo": len(tables), "kolonlar_ham": kolonlar,
                    "eslenen": {"tarih": dcol, "eklenen_ticker": acol_any, "eklenen_ad": acol_n,
                               "cikan_ticker": rcol_any, "cikan_ad": rcol_n, "neden": reason_col}}
            # MultiIndex/tuple kolonlar (rowspan'lı iki-satır başlık) DÜZLEŞTİRİLİR — `meta['eslenen']`
            # yukarıda `kolonlar` (düz string) üzerinden hesaplandı; `row.get(...)` aşağıda AYNI düz
            # adlarla arayacağı için `df.columns`un kendisi de düzleştirilmeden `.get()` HİÇBİR
            # zaman eşleşmez (orijinal kolonlar hâlâ tuple) — constituents.py::_fetch_tables'taki
            # `ch.columns = [...]` ATAMASIYLA AYNI adım, burada AYRICA yapılır.
            df = df.copy()
            df.columns = kolonlar
            return i, df, meta
    return None, None, {"tablo_index": None, "n_tablo": len(tables),
                        "kolonlar_ham": [[_kolon_adi(c) for c in t.columns] for t in tables]}


def tabloyu_ayristir(html: str) -> tuple[list[dict], dict]:
    """(degisiklikler, meta). `degisiklikler`in her satırı: {tarih(ISO|None), tarih_ham, eklenen,
    cikan, neden}. TÜMÜ boş satır (hayalet — rowspan/birleşik hücre artığı) ATLANIR; yalnız-eklenen
    ya da yalnız-çıkan satır GERÇEK VERİDİR, tutulur (modül başlığı 'HAYALET-SATIR SÜZGECİ')."""
    idx, df, meta = hedef_tablo_bul(html)
    if idx is None:
        return [], meta
    e = meta["eslenen"]
    rows: list[dict] = []
    n_hayalet = 0
    for _, row in df.iterrows():
        tarih_ham = _hucre(row.get(e["tarih"]))
        eklenen = _tick(row.get(e["eklenen_ticker"])) if e["eklenen_ticker"] else None
        cikan = _tick(row.get(e["cikan_ticker"])) if e["cikan_ticker"] else None
        neden = _hucre(row.get(e["neden"])) if e["neden"] else ""
        if not (tarih_ham or eklenen or cikan or neden):
            n_hayalet += 1
            continue
        rows.append({"tarih": _tarihi_isoya_cevir(tarih_ham), "tarih_ham": tarih_ham,
                    "eklenen": eklenen, "cikan": cikan, "neden": neden or None})
    meta["n_satir_ham"] = len(df)
    meta["n_hayalet_atlanan"] = n_hayalet
    meta["n_satir_gecerli"] = len(rows)
    meta["n_tarih_ayristirilamadi"] = sum(1 for r in rows if r["tarih"] is None)
    return rows, meta


def pencereye_kirp(degisiklikler: list[dict], baslangic: str = PENCERE_BASLANGIC,
                   bitis: str | None = None) -> list[dict]:
    """`[baslangic, bitis]` (ISO, ikisi de dahil) içindeki, tarihi AYRIŞTIRILABİLEN satırlar."""
    return [r for r in degisiklikler if r["tarih"] and baslangic <= r["tarih"] <= (bitis or dt.date.today().isoformat())]


# ======================================================================================
# K1 — BİLİNEN OLAYLAR ÇAPRAZ-DOĞRULAMA
# ======================================================================================

def _is_gunu_farki_icinde(a: str, b: str, tolerans_gun: int) -> bool:
    """İki ISO tarih arasındaki İŞ GÜNÜ (Pzt-Cum) farkı <= tolerans_gun mı. Hafta sonu köprüsü
    (Cuma→Pazartesi) 1 iş günü sayılır — takvim günü DEĞİL."""
    da, db = dt.date.fromisoformat(a), dt.date.fromisoformat(b)
    lo, hi = (da, db) if da <= db else (db, da)
    gun = 0
    d = lo
    while d < hi:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            gun += 1
    return gun <= tolerans_gun


def k1_olaylari_ve_beyan(kart: dict | None) -> tuple[list[dict], int]:
    """K1 olay kümesi KARTTAN okunur (EDG-076): kart `bilinen_olaylar` YAML listesi taşıyorsa K1
    olayları ORADAN kurulur (kart alanı `kaynak` → betiğin iç şeması `yon_kaynak`a YENİDEN
    ADLANDIRILIR, kopyalanmaz — tek-kaynak yasası), `kart_beyan_n = len(bilinen_olaylar)`. Kart bu
    alanı TAŞIMIYORSA ya da liste BOŞSA (ör. EDG-075 kartı) modülün sabit `BILINEN_OLAYLAR` +
    `KART_BEYAN_N`si AYNEN döner — EDG-075 ölçümü GERİYE DÖNÜK bozulmaz (modül başlığı EDG-2026-076
    EKLERİ (a))."""
    bilinen = kart.get("bilinen_olaylar") if isinstance(kart, dict) else None
    if not isinstance(bilinen, list) or not bilinen:
        return list(BILINEN_OLAYLAR), KART_BEYAN_N
    olaylar = [
        {"sembol": o["sembol"], "yon": o.get("yon"), "tarih": o["tarih"], "yon_kaynak": o.get("kaynak")}
        for o in bilinen
    ]
    return olaylar, len(bilinen)


def k1_bilinen_olaylar(degisiklikler: list[dict], olaylar: list[dict] = BILINEN_OLAYLAR,
                       tolerans_gun: int = 1, kart_beyan_n: int = KART_BEYAN_N) -> dict:
    """Her bilinen olay için: satır var mı (sembol eklenen/çıkan sütununda VE tarih ±tolerans_gun
    içinde bir satırda geçiyor mu), tarih toleransı, yön doğru mu (yön=None ise UYDURULMAZ —
    `yon_dogru=None`). `tolerans_gun=0` VERİLİRSE mutasyon sınaması: tam ±1 gün sapan bir olay
    artık 'satır yok' sayılır (tests/test_edg075_olcum_v420.py bunu doğrudan çağırarak sınar).
    `kart_beyan_n` EDG-076'da `k1_olaylari_ve_beyan`den gelir (önceden modül sabiti `KART_BEYAN_N`e
    SABİTLENMİŞTİ) — varsayılan hâlâ `KART_BEYAN_N`, EDG-075 çağrı yeri DEĞİŞMEDEN çalışır."""
    detay = []
    for olay in olaylar:
        adaylar = [r for r in degisiklikler if r["tarih"] and olay["sembol"] in (r["eklenen"], r["cikan"])]
        en_yakin = None
        for r in adaylar:
            if en_yakin is None or abs((dt.date.fromisoformat(r["tarih"]) - dt.date.fromisoformat(olay["tarih"])).days) < \
                    abs((dt.date.fromisoformat(en_yakin["tarih"]) - dt.date.fromisoformat(olay["tarih"])).days):
                en_yakin = r
        satir_var = en_yakin is not None
        tarih_ok = bool(satir_var and _is_gunu_farki_icinde(en_yakin["tarih"], olay["tarih"], tolerans_gun))
        if not satir_var:
            yon_dogru = False
        elif olay["yon"] is None:
            yon_dogru = None            # UYDURMA YASAĞI — kart bu olay için yön vermedi
        else:
            gercek_yon = "giris" if en_yakin["eklenen"] == olay["sembol"] else "cikis"
            yon_dogru = gercek_yon == olay["yon"]
        detay.append({"sembol": olay["sembol"], "beklenen_tarih": olay["tarih"], "beklenen_yon": olay["yon"],
                      "yon_kaynak": olay["yon_kaynak"], "bulunan_tarih": en_yakin["tarih"] if en_yakin else None,
                      "satir_var": satir_var, "tarih_tolerans_icinde": tarih_ok, "yon_dogru": yon_dogru})
    n = len(detay)
    # `yon_dogru is not False` — yani None (yön kartta belirtilmedi) DİSKALİFİYE ETMEZ, yalnız
    # AÇIKÇA YANLIŞ ölçülen yön diskalifiye eder. Rol-1 `detay`deki None'ları AYRICA görür (Yasa 6).
    n_tam_gecti = sum(1 for d in detay if d["satir_var"] and d["tarih_tolerans_icinde"] and d["yon_dogru"] is not False)
    return {"tolerans_gun": tolerans_gun, "kart_beyan_n": kart_beyan_n, "olculen_n": n,
            "n_tam_gecti": n_tam_gecti, "detay": detay,
            "sayim_notu": (f"kart 'kart_beyan_n' {kart_beyan_n} olay der; bu betik {n} ayrık "
                          "(sembol,yön,tarih) olgusu ÖLÇTÜ (`k1_olaylari_ve_beyan`: kart "
                          "'bilinen_olaylar' varsa ORADAN, yoksa modül başlığı K1 türetme "
                          "beyanından) — SAYI UYUŞMAZLIĞI varsa Rol-1'e açık kalem, betik ZORLAMADI")}


# ======================================================================================
# K2 — as_of YENİDEN KURULUM (constituents.py::as_of ile AYNI algoritma, BAĞIMSIZ uygulama)
# ======================================================================================

def as_of(degisiklikler: list[dict], guncel_uyeler: set[str], tarih: str) -> set[str]:
    """`guncel_uyeler`den geriye sararak `tarih`teki üyeliği kurar: bir değişiklik `tarih`ten
    SONRAysa geri alınır (eklenen → o tarihte üye değildi, çıkar; çıkarılan → üyeydi, ekle)."""
    uyeler = set(guncel_uyeler)
    for r in degisiklikler:
        if r["tarih"] and r["tarih"] > tarih:
            if r["eklenen"]:
                uyeler.discard(r["eklenen"])
            if r["cikan"]:
                uyeler.add(r["cikan"])
    return uyeler


def k2_as_of_yeniden_kurulum(degisiklikler: list[dict], guncel_uyeler: list[str] | None,
                             t1: str, t2: str, bugun: str) -> dict:
    """Kart tarifi: as_of(t1) ∖ as_of(t2) simetrik farkı = o aralıkta tabloda yazan değişiklikler
    BİREBİR; as_of(bugün) == güncel liste. `guncel_uyeler=None` → 'çalışmadı + neden' (UYDURMA YOK,
    bu sayfa güncel liste taşımaz — `--guncel-liste` ile dışarıdan verilir)."""
    if guncel_uyeler is None:
        return {"calisti": False, "neden": "güncel liste sağlanmadı (--guncel-liste)",
                "as_of_bugun_esit_mi": None, "simetrik_fark_birebir_mi": None}
    gu = {_tick(s) for s in guncel_uyeler if _tick(s)}
    a1, a2 = as_of(degisiklikler, gu, t1), as_of(degisiklikler, gu, t2)
    simetrik_fark = a1 ^ a2
    beklenen_fark: set[str] = set()
    for r in degisiklikler:
        if r["tarih"] and min(t1, t2) < r["tarih"] <= max(t1, t2):
            if r["eklenen"]:
                beklenen_fark.add(r["eklenen"])
            if r["cikan"]:
                beklenen_fark.add(r["cikan"])
    a_bugun = as_of(degisiklikler, gu, bugun)
    return {"calisti": True, "t1": t1, "t2": t2, "as_of_t1_n": len(a1), "as_of_t2_n": len(a2),
            "simetrik_fark": sorted(simetrik_fark), "beklenen_fark": sorted(beklenen_fark),
            "simetrik_fark_birebir_mi": simetrik_fark == beklenen_fark,
            "as_of_bugun_n": len(a_bugun), "guncel_liste_n": len(gu),
            "as_of_bugun_esit_mi": a_bugun == gu}


# ======================================================================================
# K1n — GELECEK OLAYLAR (EDG-076): tabloda HENÜZ görünmemeli + as_of(bugün) yönle tutarlı olmalı
# ======================================================================================

def k1n_gelecek_olaylar(degisiklikler: list[dict], kart: dict, guncel_uyeler: list[str] | None,
                        bugun: str, tolerans_gun: int = 1) -> dict:
    """Kartın `gelecek_olaylar` listesindeki, henüz YÜRÜRLÜĞE GİRMEMİŞ olguları sınar: olgu 'geçti'
    = (a) tabloda yürürlük satırı YOK (`yururluk_satiri_var`, ±`tolerans_gun` — BEKLENEN False) VE
    (b) `as_of(bugün)` yönle TUTARLI (`as_of_beklenen_gibi`: yön=cikis ise sembol HÂLÂ üye, yön=
    giris ise HENÜZ üye DEĞİL). Yön belirtilmemiş olguda (b) `None` kalır — UYDURULMAZ, 'geçti'
    otomatik False'a düşer (modül başlığı EDG-2026-076 EKLERİ (b)). Kartta `gelecek_olaylar` yoksa
    ya da `guncel_uyeler` verilmemişse 'çalışmadı + neden' (UYDURMA YOK — `k2_as_of_yeniden_kurulum`
    ile AYNI disiplin)."""
    olaylar = kart.get("gelecek_olaylar") if isinstance(kart, dict) else None
    if not isinstance(olaylar, list) or not olaylar:
        return {"calisti": False, "neden": "kartta gelecek_olaylar yok"}
    if guncel_uyeler is None:
        return {"calisti": False, "neden": "güncel liste sağlanmadı (--guncel-liste) — as_of(bugün) hesaplanamaz"}
    gu = {_tick(s) for s in guncel_uyeler if _tick(s)}
    a_bugun = as_of(degisiklikler, gu, bugun)
    detay = []
    for olay in olaylar:
        sembol, yon, tarih = olay["sembol"], olay.get("yon"), olay["tarih"]
        yururluk_satiri_var = any(
            r["tarih"] and sembol in (r["eklenen"], r["cikan"]) and _is_gunu_farki_icinde(r["tarih"], tarih, tolerans_gun)
            for r in degisiklikler
        )
        if yon == "cikis":
            as_of_beklenen_gibi = sembol in a_bugun
        elif yon == "giris":
            as_of_beklenen_gibi = sembol not in a_bugun
        else:
            as_of_beklenen_gibi = None            # UYDURMA YASAĞI — kart bu olgu için yön vermedi
        gecti = (yururluk_satiri_var is False) and (as_of_beklenen_gibi is True)
        detay.append({"sembol": sembol, "yon": yon, "tarih": tarih,
                     "yururluk_satiri_var": yururluk_satiri_var,
                     "as_of_beklenen_gibi": as_of_beklenen_gibi, "gecti": gecti})
    n = len(detay)
    n_gecti = sum(1 for d in detay if d["gecti"])
    return {"calisti": True, "n": n, "n_gecti": n_gecti, "detay": detay}


# ======================================================================================
# rename_siniri RAPORU (EDG-076) — K DEĞİL, eşik YOK, yalnız as_of(t1)/as_of(bugün) RAPORU
# ======================================================================================

def rename_siniri_raporu(degisiklikler: list[dict], kart: dict, guncel_uyeler: list[str] | None,
                         t1: str, bugun: str) -> dict:
    """Kartın `rename_siniri` kaydı (eski/yeni ticker, ör. EQR→VMRK) için `as_of(t1)` ve
    `as_of(bugün)`de eski/yeni sembolün üye olup olmadığını yalnız RAPORLAR — eşik YOK, K'ya
    SAYILMAZ (kart notu: 'kaynak sınırı ölçümü, TSK-156 tasarımına girdi'). Kartta yoksa/güncel
    liste verilmemişse 'çalışmadı + neden' (UYDURMA YOK)."""
    kayitlar = kart.get("rename_siniri") if isinstance(kart, dict) else None
    if not isinstance(kayitlar, list) or not kayitlar:
        return {"calisti": False, "neden": "kartta rename_siniri yok"}
    if guncel_uyeler is None:
        return {"calisti": False, "neden": "güncel liste sağlanmadı (--guncel-liste) — as_of hesaplanamaz"}
    gu = {_tick(s) for s in guncel_uyeler if _tick(s)}
    a_t1 = as_of(degisiklikler, gu, t1)
    a_bugun = as_of(degisiklikler, gu, bugun)
    detay = [
        {"eski": r["eski"], "yeni": r["yeni"], "tarih": r.get("tarih"),
         "as_of_t1_eski_var": r["eski"] in a_t1, "as_of_t1_yeni_var": r["yeni"] in a_t1,
         "as_of_bugun_eski_var": r["eski"] in a_bugun, "as_of_bugun_yeni_var": r["yeni"] in a_bugun}
        for r in kayitlar
    ]
    return {"calisti": True, "detay": detay}


# ======================================================================================
# KART İÇ TUTARLILIĞI (EDG-076, adım-0 (b)) — bilinen ≤ bugün, gelecek > bugün
# ======================================================================================

def kart_ic_tutarliligi(kart: dict | None, bugun: str) -> dict:
    """Kart adım-0(b): `bilinen_olaylar`daki HER tarih `bugun`e eşit ya da öncesi, `gelecek_olaylar`
    daki HER tarih `bugun`den KESİNLİKLE SONRA olmalı — değilse kart-veri hatası (EDG-076 önsözü:
    EDG-075'in K1 kalışları TAM DA böyle bir kart hatasıydı; bu betik BOZUK KARTI ÇALIŞTIRMADAN
    yakalar, §5 'kart bir artefaktı donduruyorsa... ağaç değişir kart sessizce ölmez' ruhu)."""
    ihlaller: list[str] = []
    bilinen = kart.get("bilinen_olaylar") if isinstance(kart, dict) else None
    if isinstance(bilinen, list):
        for o in bilinen:
            t = o.get("tarih")
            if t and t > bugun:
                ihlaller.append(f"bilinen_olaylar: {o.get('sembol')} tarihi {t} > bugün {bugun}")
    gelecek = kart.get("gelecek_olaylar") if isinstance(kart, dict) else None
    if isinstance(gelecek, list):
        for o in gelecek:
            t = o.get("tarih")
            if t and t <= bugun:
                ihlaller.append(f"gelecek_olaylar: {o.get('sembol')} tarihi {t} <= bugün {bugun}")
    return {"gecerli": len(ihlaller) == 0, "ihlaller": ihlaller}


# ======================================================================================
# POZİTİF KONTROL — RAW HTML'e sentetik satır enjeksiyonu (yol-tutarlı, DataFrame'e DEĞİL)
# ======================================================================================

def enjekte_pk_satiri(html: str, sembol: str = PK_SEMBOL, tarih: str = PK_TARIH) -> str:
    """`hedef_tablo_bul` ile bulunan tablonun HTML'ine, GERÇEK bir satırın hücre sayısını taklit
    eden sentetik bir `<tr>` ekler (RAW METİN düzeyinde — `tabloyu_ayristir` bunu AYNI koddan
    yeniden okur). Tablo bulunamazsa ValueError (PK ön-koşulu düşmüş demektir, sessizce
    atlanmaz)."""
    idx, df, meta = hedef_tablo_bul(html)
    if idx is None:
        raise ValueError("PK enjeksiyonu: hedef değişiklik tablosu bulunamadı")
    e = meta["eslenen"]
    kolon_sirasi = list(_kolon_adi(c) for c in df.columns)
    n_kolon = len(kolon_sirasi)
    hucreler = ["" for _ in range(n_kolon)]
    for ad, deger in ((e["tarih"], "July 1, 2026"), (e["eklenen_ticker"], sembol)):
        if ad and ad in kolon_sirasi:
            hucreler[kolon_sirasi.index(ad)] = deger
    yeni_satir = "<tr>" + "".join(f"<td>{h}</td>" for h in hucreler) + "</tr>"

    tablolar = list(re.finditer(r"<table[\s\S]*?</table>", html))
    if idx >= len(tablolar):
        raise ValueError(f"PK enjeksiyonu: tablo indeksi {idx} ham HTML'de yok ({len(tablolar)} tablo)")
    hedef = tablolar[idx]
    govde = hedef.group(0)
    if "</tbody>" in govde:
        yeni_govde = govde.replace("</tbody>", yeni_satir + "</tbody>", 1)
    else:
        yeni_govde = govde[: -len("</table>")] + yeni_satir + "</table>"
    return html[: hedef.start()] + yeni_govde + html[hedef.end():]


def pozitif_kontrol(html: str, bugun: str, olaylar: list[dict] = BILINEN_OLAYLAR) -> dict:
    """Kart `pozitif_kontrol`: enjekte edilmiş kopyada K1 eşleşme sayısı DEĞİŞMEMELİ,
    as_of(2026-07-02) PK_SEMBOL'ü İÇERMELİ, as_of(2026-06-30) İÇERMEMELİ (`guncel_uyeler`e
    PK_SEMBOL DAHİL edilir — kart'ın betimlediği 'şu an üye' varsayımı)."""
    ham_degisiklikler, _ = tabloyu_ayristir(html)
    enjekteli_html = enjekte_pk_satiri(html)
    pk_degisiklikler, pk_meta = tabloyu_ayristir(enjekteli_html)

    k1_once = k1_bilinen_olaylar(ham_degisiklikler, olaylar)
    k1_sonra = k1_bilinen_olaylar(pk_degisiklikler, olaylar)
    k1_degismedi = k1_once["n_tam_gecti"] == k1_sonra["n_tam_gecti"]

    guncel_uyeler_ham = {r["eklenen"] for r in ham_degisiklikler if r["eklenen"]} | \
                        {r["cikan"] for r in ham_degisiklikler if r["cikan"]} | {PK_SEMBOL}
    sonra_tarih = "2026-07-02"
    once_tarih = "2026-06-30"
    a_sonra = as_of(pk_degisiklikler, guncel_uyeler_ham, sonra_tarih)
    a_once = as_of(pk_degisiklikler, guncel_uyeler_ham, once_tarih)

    icerir_sonra = PK_SEMBOL in a_sonra
    icermez_once = PK_SEMBOL not in a_once
    return {"k1_n_tam_gecti_once": k1_once["n_tam_gecti"], "k1_n_tam_gecti_sonra": k1_sonra["n_tam_gecti"],
            "k1_degismedi": k1_degismedi, "as_of_sonra_tarih": sonra_tarih, "as_of_once_tarih": once_tarih,
            "pk_sembol_as_of_sonra_icerir_mi": icerir_sonra, "pk_sembol_as_of_once_icermez_mi": icermez_once,
            "tuttu": bool(k1_degismedi and icerir_sonra and icermez_once), "enjekte_meta": pk_meta}


# ======================================================================================
# ADIM-0 FİZİBİLİTE (kart `adim_0_fizibilite`)
# ======================================================================================

def adim0(html: str, girdi_kimligi: dict, bugun: str | None = None,
         beklenen_sha: str | None = None, kart: dict | None = None) -> dict:
    """`a`-`d`: EDG-075'in ORİJİNAL kriterleri (tablo okunuyor mu / oldid sabit mi / pencere ≥100
    satır mı / tüm tarihler ayrıştı mı) — hâlâ RAPORLANIR, hiçbir sürümde tek başına K1/K2/PK'yi
    KAPATMADI (bu tiny sentetik test fikstüründe `c_yeterli_100_ustu` zaten False'tur — GERÇEK
    tam sayfada değil). `e`/`f`: EDG-076 EKLERİ — `--beklenen-sha` verilip ham dosyanın GERÇEK
    sha256'sıyla eşleşmiyorsa YA DA kart iç tutarsızsa (`kart_ic_tutarliligi`) genel `gecerli`
    FALSE'a düşer + `neden` yazılır (yalnız BU İKİ yeni kriter `gecerli`ye KATILIR — modül başlığı
    EDG-2026-076 EKLERİ (d))."""
    bugun = bugun or dt.date.today().isoformat()
    idx, df, meta = hedef_tablo_bul(html)
    a_okunuyor = idx is not None
    degisiklikler, _ = tabloyu_ayristir(html) if a_okunuyor else ([], {})
    pencere = pencereye_kirp(degisiklikler, bitis=bugun)
    c_yeterli = len(pencere) >= 100
    d_hepsi_ayristi = bool(degisiklikler) and all(r["tarih"] for r in degisiklikler)

    sha_hesaplanan = hashlib.sha256(html.encode("utf-8")).hexdigest()
    sha_esit_mi = None if beklenen_sha is None else (sha_hesaplanan == beklenen_sha)
    tutarlilik = kart_ic_tutarliligi(kart, bugun) if isinstance(kart, dict) else {"gecerli": True, "ihlaller": []}

    nedenler: list[str] = []
    if not a_okunuyor:
        nedenler.append("hedef değişiklik tablosu bulunamadı")
    if not girdi_kimligi.get("oldid"):
        nedenler.append("girdi oldid ile sabitlenmemiş")
    if sha_esit_mi is False:
        nedenler.append(f"--beklenen-sha uyuşmuyor: beklenen={beklenen_sha} hesaplanan={sha_hesaplanan}")
    if not tutarlilik["gecerli"]:
        nedenler.extend(tutarlilik["ihlaller"])

    gecerli = bool(a_okunuyor and girdi_kimligi.get("oldid") and sha_esit_mi is not False and tutarlilik["gecerli"])
    return {"a_tablo_okunuyor": a_okunuyor, "a_meta": meta,
            "b_oldid_ile_sabit": bool(girdi_kimligi.get("oldid")),
            "c_pencere_n": len(pencere), "c_yeterli_100_ustu": c_yeterli,
            "d_tum_tarihler_ayristi": d_hepsi_ayristi,
            "d_ayristirilamadi_n": sum(1 for r in degisiklikler if not r["tarih"]),
            "e_sha_beklenen": beklenen_sha, "e_sha_hesaplanan": sha_hesaplanan, "e_sha_esit_mi": sha_esit_mi,
            "f_kart_ic_tutarli": tutarlilik["gecerli"], "f_kart_ic_tutarli_ihlaller": tutarlilik["ihlaller"],
            "gecerli": gecerli, "neden": None if gecerli else "; ".join(nedenler)}


# ======================================================================================
# --olc: TAM ÖLÇÜM (ağ YOK — yalnız diskteki/verilen HTML)
# ======================================================================================

def olc(html: str, esikler: dict, girdi_kimligi: dict, guncel_uyeler: list[str] | None,
       kart: dict | None = None, bugun: str | None = None, t1: str = "2026-06-01",
       beklenen_sha: str | None = None) -> dict:
    """`kart` EDG-076 EKLERİ: `kart_yukle` ile okunmuş TAM kart sözlüğü (`None`/kart taşımıyorsa
    boş sözlük sayılır — `k1_olaylari_ve_beyan` EDG-075 fallback'ine düşer). `adim_0_fizibilite.
    gecerli` False İSE (sha uyuşmazlığı ya da kart iç tutarsızlığı) K1/K1n/K2/pozitif_kontrol
    KOŞMAZ, dört alan `None` yazılır — `rename_siniri_raporu` bu kapının DIŞINDA (K değil, kart
    notu). Sonuç HER durumda üretilir (Yasa 6 — modül başlığı EDG-2026-076 EKLERİ (d))."""
    bugun = bugun or dt.date.today().isoformat()
    kart = kart if isinstance(kart, dict) else {}
    degisiklikler, meta = tabloyu_ayristir(html)
    pencere = pencereye_kirp(degisiklikler, bitis=bugun)
    a0 = adim0(html, girdi_kimligi, bugun=bugun, beklenen_sha=beklenen_sha, kart=kart)
    olaylar, kart_beyan_n = k1_olaylari_ve_beyan(kart)

    if a0["gecerli"]:
        k1 = k1_bilinen_olaylar(pencere, olaylar, kart_beyan_n=kart_beyan_n)
        k1n = k1n_gelecek_olaylar(degisiklikler, kart, guncel_uyeler, bugun)
        k2 = k2_as_of_yeniden_kurulum(degisiklikler, guncel_uyeler, t1, bugun, bugun)
        pk = pozitif_kontrol(html, bugun, olaylar)
    else:
        k1 = k1n = k2 = pk = None       # adim_0_fizibilite.neden'de GEREKÇE var (Yasa 6, uydurma yok)

    rename_raporu = rename_siniri_raporu(degisiklikler, kart, guncel_uyeler, t1, bugun)

    return {
        "kart": esikler.get("kart_id"), "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "girdi_kimligi": girdi_kimligi,
        "tablo_meta": meta,
        "adim_0_fizibilite": a0,
        "degisiklikler_n_pencere": len(pencere),
        "k1_bilinen_olaylar": k1,
        "k1n_gelecek_olaylar": k1n,
        "k2_as_of_yeniden_kurulum": k2,
        "rename_siniri_raporu": rename_raporu,
        "pozitif_kontrol": pk,
        "esikler": esikler,
        "beyan": ("Bu betik yalnız ÖLÇER; hüküm Rol-1'de, AYNI turda karta + K defterine işlenir "
                 "(CLAUDE.md §3/§5). meridian/*.py bu turda DEĞİŞTİRİLMEDİ, `--cek` bu ajan "
                 "turunda hiç çağrılmadı (ağa çıkmadı)."),
    }


# ======================================================================================
# CLI
# ======================================================================================

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="EDG-2026-075/076 S&P 500 tarihsel bileşenler PIT kaynağı ölçümü "
                                              "(EDG-076: karttan K1 olay kümesi + K1n gelecek-olay + rename raporu + --beklenen-sha)")
    ap.add_argument("--cek", action="store_true", help="Wikipedia'yı oldid ile sabitleyerek çeker (AĞ — Rol-1)")
    ap.add_argument("--olc", action="store_true", help="ham HTML'i ayrıştırır + K1/K1n/K2/PK ölçer (AĞ YOK)")
    ap.add_argument("--oldid", type=int, default=None, help="--cek: belirli bir revizyonu çek (varsayılan: güncel)")
    ap.add_argument("--girdi", default=None, help="--olc: ham HTML yolu (varsayılan: ham/ altında en yeni dosya)")
    ap.add_argument("--kart", default=str(KART_YOLU), help="kart yolu (varsayılan EDG-2026-075; EDG-076 için --kart ile verilir)")
    ap.add_argument("--guncel-liste", default=None, help="K2/K1n/rename-raporu için güncel üyelik JSON'u (liste[str])")
    ap.add_argument("--bugun", default=None, help="K2/pencere/K1n/kart-tutarlılığı referans tarihi (ISO) — varsayılan bugün")
    ap.add_argument("--t1", default="2026-06-01", help="K2 simetrik-fark başlangıcı (kart örneği: 2026-06-01)")
    ap.add_argument("--beklenen-sha", default=None, help="EDG-076: ham dosyanın beklenen sha256'sı — eşleşmezse ölçüm geçersiz, K1/K1n/K2/PK koşmaz")
    ap.add_argument("--cikti", default=str(SANDBOX / "sonuc.json"), help="sonuc.json çıktı yolu")
    a = ap.parse_args(argv)

    if not a.cek and not a.olc:
        ap.error("--cek veya --olc verilmeli")

    if a.cek:
        sonuc = cek(oldid=a.oldid)
        print(json.dumps(sonuc, ensure_ascii=False, indent=2))
        if not sonuc.get("ok"):
            return 1
        if not a.olc:
            return 0
        girdi_yolu = pathlib.Path(sonuc["ham_yol"])
        girdi_kimligi = {"oldid": sonuc["oldid"], "html_sha256": sonuc["sha256"], "ham_yol": sonuc["ham_yol"]}
    else:
        girdi_yolu = pathlib.Path(a.girdi) if a.girdi else en_yeni_ham_dosya()
        if girdi_yolu is None or not girdi_yolu.exists():
            print(f"ham HTML yok: {a.girdi or HAM_DIR} — önce --cek (Rol-1) koşulmalı", file=sys.stderr)
            return 1
        html_ic = girdi_yolu.read_text(encoding="utf-8")
        m = re.match(r"(\d+)_([0-9a-f]{16})\.html$", girdi_yolu.name)
        girdi_kimligi = {"oldid": int(m.group(1)) if m else None,
                         "html_sha256_prefix16": m.group(2) if m else None,
                         "html_sha256_tam": hashlib.sha256(html_ic.encode("utf-8")).hexdigest(),
                         "ham_yol": str(girdi_yolu)}

    html = girdi_yolu.read_text(encoding="utf-8")
    esikler = esikleri_karttan_oku(pathlib.Path(a.kart))
    kart = kart_yukle(pathlib.Path(a.kart))
    guncel_uyeler = json.loads(pathlib.Path(a.guncel_liste).read_text()) if a.guncel_liste else None
    sonuc = olc(html, esikler, girdi_kimligi, guncel_uyeler, kart, bugun=a.bugun, t1=a.t1,
               beklenen_sha=a.beklenen_sha)
    cikti = json.dumps(sonuc, ensure_ascii=False, indent=2, sort_keys=True, default=str)
    pathlib.Path(a.cikti).write_text(cikti + "\n", encoding="utf-8")
    print(f"yazıldı: {a.cikti}")
    print(cikti)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
