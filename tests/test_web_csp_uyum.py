"""Panonun dağıtım CSP'siyle uyumlu KALDIĞINI koruyan testler.

NİYE VAR: `deploy/Caddyfile` `script-src 'self'` gönderiyor. O başlık yalnız harici olmayan
`<script>` bloklarını değil, SATIR İÇİ OLAY ÖZNİTELİKLERİNİ de (`onclick`, `oninput`, …)
bloklar. Bu ayrım gözden kaçtı ve bir süre boyunca CSP satırı "script-src 'self'" diyordu
ama pano 40 satır içi öznitelik taşıyordu — o hâliyle dağıtılsaydı **pano çizilir, hiçbir
düğme çalışmazdı: gezinme, çekmece, KRİZ grubu ve HALT dahil.**

Arıza kod incelemesiyle değil, başlığın ne blokladığı düşünülerek bulundu. Bir daha
düşünmek zorunda kalmamak için kural buraya bağlandı: satır içi işleyici EKLENİRSE test
kırılır ve neden kırıldığını söyler.

Bu testler ağ ya da tarayıcı istemez — kaynak dosyaları okur.
"""
import pathlib
import re

import pytest

WEB = pathlib.Path(__file__).resolve().parents[1] / "meridian" / "web"
CADDY = pathlib.Path(__file__).resolve().parents[1] / "deploy" / "Caddyfile"

# Tarayıcının çalıştırdığı her şey. `.html` içindeki `<style>` blokları style-src'ye tabidir
# ve orada `unsafe-inline` BİLEREK duruyor (app.js satır içi stil üretiyor) — bu dosya
# script tarafını korur.
#
# LİSTE BİR SÜRE SESSİZCE YARIM KOŞTU (2026-08-01'de bulundu). Girdiler arasında VİRGÜL
# EKSİKTİ ve Python iki dizgiyi bitiştirdi: `"workflow.js" "meridian/web/palette.js"` →
# `"workflow.jsmeridian/web/palette.js"`. Sonuç: `workflow.js` hiç sınanmadı, `palette.js` hiç
# sınanmadı, ve var olmayan bitişik ad `pytest.skip` ile SESSİZCE atlandı — yani koruma yeşil
# görünüyordu. Bu, bu deponun tekrar eden kusur sınıfının ta kendisi ("kurulu ≠ çalışır").
# Ayrıca yol biçimi de karışmıştı: `_oku()` adları `WEB / ad` diye çözer, yani girdiler
# DOSYA ADI olmalı — depo-kökü göreli yol değil.
YUZEYLER = ["index.html", "landing.html", "workflow.html", "runbook.html",
            "app.js", "theme.js", "landing.js", "workflow.js",
            "palette.js",  # P7 komut paleti (2026-08-01) — aynı CSP kuralları ev-tarafında da çivili
]

# Yorum ve dizgi içindeki "onclick" kelimesini yakalamamak için özniteliğin gerçek biçimini
# arıyoruz: boşluk + on<ad> + '=' + tırnak.
SATIR_ICI = re.compile(r'\son[a-z]+\s*=\s*["\']')


def _oku(ad):
    p = WEB / ad
    if not p.exists():
        pytest.skip(f"{ad} yok")
    return p.read_text()


@pytest.mark.parametrize("ad", YUZEYLER)
def test_satir_ici_olay_ozniteligi_yok(ad):
    """Hiçbir yüzeyde `onclick="..."` biçiminde işleyici olmamalı.

    Yerine: `data-act="eylemAdi"` + app.js'teki tek delege dinleyici.
    """
    kaynak = _oku(ad)
    bulunan = SATIR_ICI.findall(kaynak)
    assert not bulunan, (
        f"{ad} içinde {len(bulunan)} satır içi olay özniteliği var: {sorted(set(bulunan))}. "
        "CSP `script-src 'self'` bunları BLOKLAR — düğme çalışmaz. "
        'Çözüm: `data-act="ad"` kullan ve adı app.js\'teki EYLEMLER kümesine kaydet.'
    )


@pytest.mark.parametrize("ad", ["index.html", "landing.html", "workflow.html", "runbook.html"])
def test_satir_ici_script_blogu_yok(ad):
    """`<script>` yalnız `src` ile gelmeli; gövdeli blok CSP'ye takılır."""
    kaynak = _oku(ad)
    govdeli = re.findall(r"<script(?![^>]*\ssrc=)[^>]*>", kaynak)
    assert not govdeli, (
        f"{ad} içinde gövdeli <script> var: {govdeli}. CSP bunu bloklar — "
        "kodu ayrı bir .js dosyasına al ve api.py'de yolunu tanımla."
    )


def test_her_data_act_kayitli():
    """Kullanılan her `data-act` adı EYLEMLER izin listesinde olmalı.

    Kayıtsız bir ad sessizce DÜŞER (dinleyici onu çalıştırmaz), yani düğme ölü görünür ama
    hiçbir hata vermez — tam olarak fark edilmesi en zor arıza türü.
    """
    app = _oku("app.js")
    m = re.search(r"const EYLEMLER = new Set\(\[(.*?)\]\);", app, re.S)
    assert m, "app.js içinde EYLEMLER kümesi bulunamadı — delegasyon katmanı kaldırılmış olabilir"
    kayitli = set(re.findall(r'"([A-Za-z_$][\w$]*)"', m.group(1)))

    kullanilan = set()
    for ad in YUZEYLER:
        p = WEB / ad
        if p.exists():
            kullanilan |= set(re.findall(r'data-act="([A-Za-z_$][\w$]*)"', p.read_text()))

    eksik = kullanilan - kayitli
    assert not eksik, (
        f"kayıtsız data-act: {sorted(eksik)} — bu düğmeler SESSİZCE ölü. "
        "app.js'teki EYLEMLER kümesine ekle."
    )


def test_kayitli_her_eylem_tanimli():
    """İzin listesindeki her ad app.js'te gerçekten tanımlı olmalı.

    Kayıtlı ama tanımsız bir ad, listenin kodla ayrıştığını gösterir; dinleyici bunu
    çalışma anında console.error ile bildirir ama o noktada düğme zaten ölüdür.
    """
    app = _oku("app.js")
    m = re.search(r"const EYLEMLER = new Set\(\[(.*?)\]\);", app, re.S)
    assert m
    kayitli = sorted(re.findall(r'"([A-Za-z_$][\w$]*)"', m.group(1)))
    tanimsiz = [
        a for a in kayitli
        if not re.search(rf"(window\.{re.escape(a)}\s*=|function\s+{re.escape(a)}\s*\()", app)
    ]
    assert not tanimsiz, f"EYLEMLER'de kayıtlı ama tanımı yok: {tanimsiz}"


def test_csp_script_src_gevsetilmemis():
    """Caddyfile'ın script-src'sinde `unsafe-inline` OLMAMALI.

    Bu satıra `unsafe-inline` eklemek zorunda kalındıysa sebep neredeyse kesinlikle bir
    yere satır içi `onclick`in geri gelmesidir — doğru çözüm başlığı gevşetmek değil,
    eylemi kaydetmektir. (style-src'deki `unsafe-inline` ayrı bir borçtur ve BU TESTİN
    KAPSAMINDA DEĞİLDİR.)
    """
    if not CADDY.exists():
        pytest.skip("deploy/Caddyfile yok")
    m = re.search(r"script-src ([^;]+);", CADDY.read_text())
    assert m, "Caddyfile'da script-src yönergesi bulunamadı"
    assert "unsafe-inline" not in m.group(1), (
        f"script-src gevşetilmiş: {m.group(1).strip()!r}. "
        "Satır içi bir işleyici geri gelmiş olabilir — testleri yukarıdan oku."
    )
    assert "unsafe-eval" not in m.group(1), "script-src'de unsafe-eval — panoda eval kullanımı yok"


@pytest.mark.parametrize("ad", YUZEYLER)
def test_dinamik_kod_yurutme_yok(ad):
    """eval / new Function / javascript: — CSP bunları da bloklar, ve zaten hiçbiri gerekmiyor."""
    kaynak = _oku(ad)
    for desen, aciklama in ((r"\beval\s*\(", "eval()"),
                            (r"\bnew\s+Function\s*\(", "new Function()"),
                            (r"javascript:", "javascript: URL")):
        assert not re.search(desen, kaynak), f"{ad} içinde {aciklama} var — CSP bloklar"
