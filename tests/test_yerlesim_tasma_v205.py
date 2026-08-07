"""v205 · YERLEŞİM TAŞMASI — `.trow` ızgara öğelerinde taşma sözleşmesi.

ÖLÇÜLEN KUSUR (operatör ekran görüntüsüyle bildirdi, 2026-08-07). "Bütünlük dedektörleri"
kartındaki **Makullük ihlalleri** paneli iki kolonlu satırlar çiziyor: solda dedektör adı
(`.tick`, mono 14px), sağda açıklama (`.chain`). Sol kolon SABİT 190px idi ve uzun dedektör adları
kolondan taşıp sağdaki açıklamanın ÜSTÜNE biniyordu. Ekran görüntüsünde okunamayan üç ad:

    yeniden_hesap:orphan_state_files             32 kar.
    eleme:component_ic.eslesme:sema_elemesi      39 kar.
    eleme:threshold_curve.eslesme:sema_elemesi   42 kar.

KÖK: bir kuralın yanlışlığı değil, bir kuralın YOKLUĞU — iki CSS varsayılanı üst üste bindi.
  (1) Izgara öğesinin `min-width` varsayılanı `auto`dur (otomatik en küçük boyut = min-content),
      yani esnek kolonlar içeriğinin altına inemez ve satır kabından taşar.
  (2) `overflow-wrap` varsayılanı `normal`dır; kırılma fırsatı OLMAYAN bir jeton hiç sarmalanmaz.
      Bu adlarda kırılma fırsatı yok — UAX#14'e göre `_` AL, `:` ve `.` IS sınıfındadır ve hiçbiri
      satır sonu vermez. Ad tek bir kırılmaz jetondur; sabit px'lik kolonda öğe kutusu 190px kalır,
      İÇERİK kutunun dışına boyanır, komşu kolonun metnine karışır.

SINIF, SATIR DEĞİL. app.js'te 102 `.trow` ızgara emisyonu ve 304 sabit px kolon ölçüldü; düzeltme
öncesi HİÇBİRİNDE taşma kuralı yoktu. Bu yüzden hüküm tek bir sınıf kuralındadır
(`.trow > *{min-width:0;overflow-wrap:anywhere}`) ve bu dosya onu çivilemekle kalmaz, ÖLÇER.

ÖLÇÜM MODELİ — BEYAN (YASA: ölçülemeyen uydurulmaz). Bu koşumda tarayıcı YOK; dolayısıyla burada
ölçülen şey "Chrome'un çizdiği piksel" DEĞİL, **kaynakta yayınlanan geometridir**: emisyonun kendi
`grid-template-columns` değeri + index.html'de yayınlanan `.tick` tipografisi + Recursive Mono'nun
ÖLÇÜLMÜŞ advance'ı. Bu üçü mono metin için geometriyi TAM belirler: yazı tipi sabit-advance'tır
(`research/olcumler/yazi_tipi_2026-08-07`: upem 1000, her advance 600 → 0,6em), yani genişlik
karakter sayısıyla kapalı formda hesaplanır — tahmin girmez. Modelin kusuru görme GÜCÜ ayrıca
sınanır (`test_model_duzeltme_ONCESINI_kirmizi_gorur`): sarma kuralı modelden çekildiğinde model
bindirmeyi YENİDEN üretmek zorundadır, yoksa "her zaman yeşil" bir ölçüm aracı olurdu.

Node koşum deseni test_kart_sozlesmesi_v198'den devralındı: satırı üreten dilim app.js'ten AYNEN
kesilip `node -e` ile koşturulur — kopya şablon ölçülmez, YAYINDAKİ şablon ölçülür.
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess

import pytest

KOK = pathlib.Path(__file__).resolve().parents[1]
WEB = KOK / "meridian" / "web"
APPJS = (WEB / "app.js").read_text()
INDEX = (WEB / "index.html").read_text()

NODE = shutil.which("node")

# Yorumsuz gövde (v139/v191/v198 deseni): bu turun her kuralı gerekçesini kaynakta yazıyor ve o
# gerekçe bir BİLDİRİM sanılmamalı — yoksa doğru davranan kod kendi belgesi yüzünden hem düşer hem
# geçer. (Yorumda "overflow-wrap:anywhere" cümlesi geçiyor; kural sanılmasın.)
KOD = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))
CSS = INDEX[INDEX.index("<style>"):INDEX.index("</style>")]
CSS_KOD = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)

# Ekran görüntüsünde ÖLÇÜLEN üç ad (operatör bildirimi) + kaynaktan türetilen en uzun olası ad.
# Sonuncusu bir tahmin değil: watchdog.py:844 `eleme:{aşama}:{kural}` biçimini kuruyor, aşama adları
# `Sieve("…")` çağrılarından, kural adları sieve.py'den geliyor; çarpımın en uzunu budur.
EKRAN_ADLARI = [
    "yeniden_hesap:orphan_state_files",
    "eleme:component_ic.eslesme:sema_elemesi",
    "eleme:threshold_curve.eslesme:sema_elemesi",
]
EN_UZUN_AD = "eleme:llm_opinion_calibration.gercek:sema_orani_yuksek"
KISA_AD = "scan_yield"  # watchdog.py:701 — evrenin kısa ucu, düzen bozulmadı kontrolü

# ---- ÖLÇÜLMÜŞ TABAN (RATCHET, 2026-08-07) -----------------------------------------------------
# `.tick` kolonuna düşen ad evreni kaynaktan sayıldı (watchdog.py düz `"check": "…"` satırları +
# `yeniden_hesap:` önekli recompute.py `_row("…")` satırları + `eleme:{aşama}:{kural}` çarpımı).
# Bu bir FOTOĞRAFTIR, hedef değil: 190px'in neden yetmediğini ve 340px'in neden seçildiğini
# sayıyla kaydeder. `meridian/*.py` bu turda BAŞKA bir ajanın elinde olduğu için evren testte
# yeniden türetilmez (uçuş sırasında değişebilir) — pinlenir, ve yöntem yukarıda yazılıdır.
MAKULLUK_EVRENI_N = 97
MAKULLUK_MEDYAN_KAR = 38
TEK_SATIR_ORANI = {190: 0.16, 320: 0.39, 340: 0.63}  # ölçülen diz noktası 320→340px arasında
# Panelin bulunduğu en geniş masaüstü satırı: .shell 1320px − 2×24 kenar − 208 ray − 32 boşluk
# − 2×24 kart dolgusu = 984px. Kimlik kolonu bunun %40'ını AŞMAMALI, yoksa açıklama sütunu ezilir.
SATIR_GENISLIGI_PX = 984
KIMLIK_KOLON_TAVAN_ORANI = 0.40

# DÜZELTME ÖNCESİ kolon genişlikleri — BEYAN. Yayındaki şablonu ölçüp "önce böyleydi" demek
# uydurma olurdu; "önce" hâli ancak yazılı bir tarihle ölçülebilir. Bu dört sayı 2026-08-07'de
# app.js'te duran değerlerdir (parityBad 190px yalnızca bu turda 340px'e çıktı; diğer üçünün
# genişliğine DOKUNULMADI — onlarda kusuru kapatan tek şey sınıf kuralıdır).
ONCEKI_KOLON = {"parityBad": 190.0, "lcRows": 170.0, "wv": 170.0, "eleme": 200.0}


# ===============================================================================================
# ÖLÇÜM ALTYAPISI — yazı tipi metriği DİSKTEN okunur, teste yazılmaz
# ===============================================================================================
@pytest.fixture(scope="module")
def mono_advance() -> float:
    """Recursive Mono'nun em başına advance'ı — D4 turunun ÖLÇÜM KAYDINDAN okunur.

    Sayıyı buraya elle yazmak, bu dosyayı yazı tipi değiştiğinde sessizce yalancı yapardı. Kayıt
    yoksa ölçüm YAPILMAZ (ÖLÇÜLEMEDİ ≠ 0) — test atlanır ve nedeni yazılır."""
    olcum = KOK / "research" / "olcumler" / "yazi_tipi_2026-08-07"
    tnum, metrik = olcum / "tnum.json", olcum / "measurements.json"
    if not (tnum.exists() and metrik.exists()):
        pytest.skip(f"yazı tipi ölçüm kaydı yok ({olcum}) — advance ÖLÇÜLEMEDİ, varsayılmaz")
    anahtar = "RecursiveMonoLinear-VF"
    adv = json.loads(tnum.read_text())[anahtar]["default_advances"]
    upem = json.loads(metrik.read_text())[anahtar]["upem"]
    turkce = json.loads(metrik.read_text())[anahtar]["turkish"]
    kume = set(adv.values()) | {v["adv"] for v in turkce.values()}
    assert len(kume) == 1, (
        f"{anahtar} sabit-advance DEĞİL ({sorted(kume)}) — kapalı-form genişlik hesabı geçersiz; "
        "bu model yalnız mono yazı tipi için doğrudur.")
    return kume.pop() / upem


@pytest.fixture(scope="module")
def tipografi() -> dict:
    """`.tick` ve `.chain` tipografisi YAYINDAKİ CSS'ten okunur (ikinci kopya = sessiz bayatlama)."""
    out = {}
    for sinif in ("tick", "chain"):
        m = re.search(r"^\.%s\{([^}]*)\}" % sinif, CSS_KOD, re.M)
        assert m, f".{sinif} kuralı index.html'de bulunamadı"
        govde = m.group(1)
        fs = re.search(r"font-size:(\d+(?:\.\d+)?)px", govde)
        ls = re.search(r"letter-spacing:(-?\.?\d*\.?\d+)em", govde)
        assert fs, f".{sinif}: font-size px cinsinden yazılmamış → {govde!r}"
        out[sinif] = {"fs": float(fs.group(1)), "ls": float(ls.group(1)) if ls else 0.0}
    return out


def _dilim(ad: str, capa: str | None = None) -> str:
    """`const <ad> = … .join("");` — YAYINDAKİ emisyonun ta kendisi (kopya değil).

    `capa`: aynı adlı birden fazla bağ varsa (`const rows` app.js'te birkaç kez geçer) doğru olanı
    seçen imza. Yanlış dilimi ölçmek sessizce BAŞKA bir paneli ölçmek olurdu."""
    i = -1
    while True:
        i = APPJS.index(f"const {ad} = ", i + 1)
        j = APPJS.index('.join("");', i) + len('.join("");')
        if capa is None or capa in APPJS[i:j]:
            return APPJS[i:j]


def _fn(ad: str) -> str:
    i = APPJS.index(f"function {ad}(")
    return APPJS[i:APPJS.index("\n}", i) + 2]


def _esc() -> str:
    i = APPJS.index("const esc = ")
    return APPJS[i:APPJS.index("\n", i) + 1]


# Node tarafındaki ölçüm makinesi. Model üç girdiyle çalışır: emisyonun ürettiği HTML, yayındaki
# tipografi ve ölçülmüş advance. `sarma` bayrağı DÜZELTME ÖNCESİ/SONRASI ayrımıdır — kapalıyken
# `overflow-wrap:normal` varsayılanı taklit edilir (jeton kırılmaz, tek satır, kutuyu aşar).
_OLCER = r"""
const ADV = %(adv)s, TIPO = %(tipo)s;
const _coz = s => s.replace(/&lt;/g,"<").replace(/&gt;/g,">").replace(/&quot;/g,'"')
                   .replace(/&#39;/g,"'").replace(/&amp;/g,"&");

function kolonlar(html){
  const m = html.match(/grid-template-columns:([^"';]+)/);
  if(!m) throw new Error("grid-template-columns yok: " + html.slice(0,120));
  return m[1].trim().split(/\s+/);
}
// Üst düzey ızgara öğeleri: `.trow`un DOĞRUDAN çocukları (iç içe span'lar öğe değildir).
function ogeler(html){
  const govde = html.slice(html.indexOf(">") + 1);
  const out = []; let derinlik = 0, bas = 0, sinif = null;
  for(const mm of govde.matchAll(/<\/?(span|b|div|button|a)\b([^>]*)>/g)){
    if(mm[0].startsWith("</")){
      derinlik--;
      if(derinlik === 0) out.push({sinif, metin: _coz(govde.slice(bas, mm.index).replace(/<[^>]*>/g,""))});
      continue;
    }
    if(derinlik === 0){
      const c = (mm[2].match(/class="([^"]*)"/) || [,""])[1].trim();
      sinif = c; bas = mm.index + mm[0].length;
    }
    derinlik++;
  }
  return out;
}
function tipo(sinif){
  for(const k of Object.keys(TIPO)) if((" "+sinif+" ").includes(" "+k+" ")) return TIPO[k];
  return TIPO.chain;   // sınıfsız/bilinmeyen öğe: en küçük tipografi (iyimser = kusuru gizler DEĞİL)
}
// Sarma modeli. `overflow-wrap:anywhere` jetonu KUTUYA sığdığı yerden kırar; kapalıyken jeton
// bölünmez ve tek satır kutunun dışına taşar.
function satirlar(metin, kar, kutu, sarma){
  const n = metin.length;
  if(!sarma || kutu <= kar) return [n * kar];
  const sigan = Math.max(1, Math.floor(kutu / kar));
  const out = [];
  for(let i = 0; i < Math.ceil(n / sigan); i++) out.push(Math.min(sigan, n - i * sigan) * kar);
  return out;
}
// `kolonEzme`: DÜZELTME ÖNCESİ kolon genişliği. Kusuru "önce" hâlinde ölçmek için gereklidir —
// yayındaki şablon artık düzeltilmiş kolonu taşıdığı için, onu ölçüp "önce böyleydi" demek
// UYDURMA olurdu. Önceki değer testte BEYANLA (ONCEKI_KOLON) yazılıdır.
function olc(html, sarma, kolonEzme){
  const kol = kolonlar(html), og = ogeler(html);
  const t0 = tipo(og[0].sinif), kar0 = t0.fs * (ADV + t0.ls);
  const k0 = kolonEzme != null ? kolonEzme : parseFloat(kol[0]);
  const st = satirlar(og[0].metin, kar0, k0, sarma);
  const solIcerikSag = Math.max(...st);
  return {
    ad: og[0].metin, kolon1_px: k0, kolon1_sablon: kol[0],
    sol_icerik_sag_px: +solIcerikSag.toFixed(1),
    sag_kolon_basi_px: k0,
    bindirme_px: +(solIcerikSag - k0).toFixed(1),
    satir_sayisi: st.length,
    komsu_sinif: (og[1] || {}).sinif ?? null,
  };
}
%(esc)s
%(chip)s
const ig = %(ig)s, lc = %(lc)s, sv = %(sv)s;
%(emisyon)s
const parcalar = (%(hedef)s).split("</div>").filter(x => x.includes("trow")).map(x => x + "</div>");
const sonuc = {};
for(const p of parcalar){
  // SONRA = yayındaki şablon + YAYINDAKİ sarma kuralı (index.html'den okunur, sabitlenmez —
  // sabitlenseydi kural silindiğinde bu ölçüm yine yeşil kalırdı). ÖNCE = eski kolon + sarma YOK.
  const s = olc(p, %(sarma)s, null), o = olc(p, false, %(once_kolon)s);
  sonuc[s.ad] = {sonra: s, once: o};
}
process.stdout.write(JSON.stringify(sonuc));
"""


def _sarma_yururlukte() -> bool:
    """Yayındaki CSS gerçekten sarmalıyor mu? Ölçüm bunu VARSAYMAZ, OKUR.

    Sabitlenseydi kural bir gün silindiğinde Node ölçümü yine yeşil kalır ve yalnız kaynak
    taraması kırmızıya dönerdi — yani "gerçek ölçüm" adı altında bir tören koşardı."""
    m = re.search(r"\.trow\s*>\s*\*\{([^}]*)\}", CSS_KOD)
    return bool(m) and "overflow-wrap:anywhere" in m.group(1)


def _kosum(emisyon: str, hedef: str, ig, lc, sv, adv: float, tipo: dict,
           once_kolon: float | None = None) -> dict:
    if NODE is None:
        pytest.skip("node yok — GERÇEK emisyon koşturulamadı (ÖLÇÜLEMEDİ)")
    betik = _OLCER % {
        "sarma": "true" if _sarma_yururlukte() else "false",
        "adv": adv,
        "tipo": json.dumps(tipo),
        "esc": _esc(), "chip": _fn("_chip"),
        "ig": json.dumps(ig, ensure_ascii=False),
        "lc": json.dumps(lc, ensure_ascii=False),
        "sv": json.dumps(sv, ensure_ascii=False),
        "emisyon": emisyon, "hedef": hedef,
        "once_kolon": "null" if once_kolon is None else repr(float(once_kolon)),
    }
    p = subprocess.run([NODE, "-e", betik], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, f"emisyon Node'da patladı:\n{p.stderr}"
    return json.loads(p.stdout)


@pytest.fixture(scope="module")
def makulluk_olcumu(mono_advance, tipografi) -> dict:
    """`parityBad` — kusurun BİLDİRİLDİĞİ emisyon. Ekran görüntüsündeki üç ad + kısa ve en uzun uç."""
    adlar = EKRAN_ADLARI + [EN_UZUN_AD, KISA_AD]
    ig = {"parity": {"rows": [{"check": a, "ok": False, "detail":
                               "artefakt okunmadı — üreten var, tüketen yok"} for a in adlar]}}
    return _kosum(_dilim("parityBad"), "parityBad", ig, {}, {}, mono_advance, tipografi,
                  once_kolon=ONCEKI_KOLON["parityBad"])


@pytest.fixture(scope="module")
def kardes_olcumu(mono_advance, tipografi) -> dict:
    """Aynı karttaki üç kardeş panel — defter sözleşmesi (5845), yazar ihlalleri (5851),
    eleme muhasebesi (5903). Hepsi sabit kolonda kimlik taşır; sınıf kuralı hepsini kapsamalı."""
    defterler = ["score_calibration_history.jsonl", "intraday_decisions.jsonl", "trades.jsonl"]
    lc = {"detail": {d: {"ok": False, "rows": 12, "violations": {"eksik_alan": 3}} for d in defterler},
          "writer_violations": {d: {"beyan_edilmemis_yazar": ["loop"]} for d in defterler}}
    sv = {"stages": {s: {"in": 250, "out": 0, "sema_drops": 250, "piyasa_drops": 0} for s in
                     ("llm_opinion_calibration.gercek", "component_ic.eslesme", "regime_edge")}}
    out = {}
    for emis in ("lcRows", "wv"):
        out[emis] = _kosum(_dilim(emis), emis, {}, lc, sv, mono_advance, tipografi,
                           once_kolon=ONCEKI_KOLON[emis])
    # Eleme muhasebesi bir IIFE içinde `const rows = …` diye yaşıyor ve app.js'te birkaç `const rows`
    # var; ÇAPA ile doğru olanı seçilir — yanlış dilim sessizce BAŞKA bir paneli ölçerdi.
    out["eleme"] = _kosum(_dilim("rows", capa="sv.stages"), "rows", {}, lc, sv,
                          mono_advance, tipografi, once_kolon=ONCEKI_KOLON["eleme"])
    return out


# ===============================================================================================
# 1 · KAYNAK TARAMASI — sınıf kuralı VAR ve her ızgara öğesine ULAŞIYOR
# ===============================================================================================
def test_trow_ogelerinde_TASMA_KURALI_var():
    """`.trow > *` hem `min-width:0` hem `overflow-wrap:anywhere` taşımak ZORUNDA.

    İkisi AYRI kusuru kapatır ve biri diğerinin yerine geçmez: `min-width:0` esnek kolonun
    içeriğinin altına inebilmesini sağlar (satırın kaptan taşmaması), `overflow-wrap` ise SABİT
    kolondaki kırılmaz jetonun kutu dışına boyanmasını engeller. Bindirmeyi ikincisi kapatır."""
    m = re.search(r"\.trow\s*>\s*\*\{([^}]*)\}", CSS_KOD)
    assert m, ("`.trow > *` kuralı yok — 102 ızgara emisyonunun ÖĞELERİNDE taşma sözleşmesi "
               "bulunmuyor demektir (v205'in kapattığı kusur).")
    govde = m.group(1)
    assert "min-width:0" in govde, f".trow > * : min-width:0 yok → {govde!r}"
    assert "overflow-wrap:anywhere" in govde, (
        f".trow > * : overflow-wrap:anywhere yok → {govde!r}. `break-word` yetmez — yalnız "
        "`anywhere` öğenin min-content katkısını da düşürür.")


def test_sabit_kolona_dusen_her_oge_DOGRUDAN_cocuk():
    """Kural `> *` ile yazıldı; öyleyse sabit kolona düşen her öğe `.trow`un DOĞRUDAN çocuğu olmalı.

    Bir emisyon öğelerini fazladan bir sarmalayıcının içine koyarsa kural o öğeye ULAŞIR (devralınan
    `overflow-wrap` sayesinde) ama `min-width:0` ULAŞMAZ. Bu tarama, sözleşmenin sessizce delinmesini
    yakalar: `.trow` açılışını izleyen ilk etiket bir ızgara öğesi olmak zorundadır."""
    kacak = []
    satirlar = KOD.splitlines()
    for i, ln in enumerate(satirlar, 1):
        if 'class="trow' not in ln and "trow rowbtn" not in ln:
            continue
        blob = "\n".join(satirlar[i - 1:i + 3])
        j = blob.find('class="trow')
        kapanis = blob.find(">", blob.find("grid-template-columns", j))
        if kapanis < 0:
            continue
        kalan = blob[kapanis + 1:].lstrip()
        if kalan.startswith("$") or kalan.startswith("`") or not kalan.startswith("<"):
            continue  # şablon değişkeni: içeriği başka emisyondan gelir, orada sayılır
        if not re.match(r"<(span|b|div|button|a)\b", kalan):
            kacak.append((i, kalan[:60]))
    assert not kacak, f"`.trow` açılışından sonra ızgara ÖĞESİ olmayan düğüm: {kacak}"


def test_sarmalamayi_GERI_ALAN_kural_yok():
    """Hiçbir `.trow` kapsamlı kural sarmalamayı geri almamalı.

    `white-space:nowrap` ya da `overflow-wrap:normal` bir ızgara öğesine geri gelirse bindirme
    aynen döner — ve kaynakta "kural var" göründüğü için kimse bakmaz. Tek meşru istisna
    `.trow > .num`: orada `white-space:normal` YAZILI (yani nowrap'ı geri alan yönde)."""
    for m in re.finditer(r"(\.trow[^{;]*)\{([^}]*)\}", CSS_KOD):
        secici, govde = m.group(1).strip(), m.group(2)
        assert "white-space:nowrap" not in govde, f"{secici}: nowrap sarmalamayı geri alıyor"
        assert "overflow-wrap:normal" not in govde, f"{secici}: overflow-wrap:normal"
        assert "text-overflow:ellipsis" not in govde, (
            f"{secici}: kırpma. Bu panelin sözleşmesi (app.js:5809-5812) ekrandaki adın "
            "günlükte greplenen adla AYNI olmasıdır; yarım ad greplenemez.")


def test_kimlik_kolonu_satirin_dortte_birinden_genis_AMA_TAVANI_var():
    """Makullük kolonu ölçüyle genişletildi — ve tavanı var.

    340px seçimi keyfi değil (bkz. app.js'teki gerekçe: evrenin medyanı 38 karakter ≈ 330px).
    Ama sınırsız genişleme de bir kusurdur: açıklama sütunu ezilirdi. Tavan, en geniş masaüstü
    satırının %40'ıdır."""
    m = re.search(r"parityBad = .*?grid-template-columns:(\d+)px", KOD, re.S)
    assert m, "parityBad emisyonunda sabit ilk kolon bulunamadı"
    px = int(m.group(1))
    assert px == 340, f"makullük kimlik kolonu {px}px — ölçülen diz noktası 340px (v205 ratchet)"
    oran = px / SATIR_GENISLIGI_PX
    assert oran <= KIMLIK_KOLON_TAVAN_ORANI, (
        f"kimlik kolonu satırın %{100*oran:.0f}'ı — tavan %{100*KIMLIK_KOLON_TAVAN_ORANI:.0f}")


def test_190px_ratchet_beyani_KAYNAKTA_duruyor():
    """Genişletmenin gerekçesi kodda yazılı olmak zorunda (YASA 6: okuyucusuz yazım yok).

    Bir sayının neden değiştiğini yalnız commit mesajı biliyorsa, üç ay sonra "bu 340 nereden
    geldi?" sorusunun cevabı yoktur ve sayı sessizce geri alınır."""
    i = APPJS.index("const parityBad = ")
    onceki = APPJS[max(0, i - 1400):i]
    assert "%84" in onceki or "84" in onceki, "190px'in taşma oranı (%84) kaynakta beyan edilmemiş"
    assert "340px" in onceki, "340px'in ölçülen diz noktası olduğu kaynakta yazılmamış"


# ===============================================================================================
# 2 · GERÇEK ÖLÇÜM (Node) — satır ÇİZİLİR, kolonlar KARŞILAŞTIRILIR
# ===============================================================================================
@pytest.mark.parametrize("ad", EKRAN_ADLARI + [EN_UZUN_AD])
def test_uzun_ad_ACIKLAMANIN_USTUNE_BINMIYOR(makulluk_olcumu, ad):
    """Ekran görüntüsündeki üç ad + evrenin en uzunu: sol kolonun içeriği sağ kolonun BAŞLANGICINI
    geçmemeli. Bindirme > 0 = operatörün bildirdiği kusur."""
    s = makulluk_olcumu[ad]["sonra"]
    assert s["bindirme_px"] <= 0, (
        f"{ad}: sol içerik {s['sol_icerik_sag_px']}px'e ulaşıyor, sağ kolon {s['sag_kolon_basi_px']}px'te "
        f"başlıyor → {s['bindirme_px']}px BİNDİRME (komşu: .{s['komsu_sinif']})")


@pytest.mark.parametrize("ad", EKRAN_ADLARI)
def test_model_duzeltme_ONCESINI_kirmizi_gorur(makulluk_olcumu, ad):
    """ÖLÇÜM ARACININ KENDİSİ SINANIR. Sarma kuralı modelden çekildiğinde (düzeltme öncesi hâl)
    model bindirmeyi YENİDEN üretmek zorunda. Aksi hâlde "hep yeşil" bir ölçer olurdu ve yukarıdaki
    testler hiçbir şey kanıtlamazdı."""
    o = makulluk_olcumu[ad]["once"]
    assert o["bindirme_px"] > 0, (
        f"{ad}: sarma kuralı olmadan da bindirme yok ({o['bindirme_px']}px) — ölçüm modeli bu "
        "kusuru göremiyor demektir, dolayısıyla 'geçti' hükmü de dayanaksızdır.")


def test_kisa_ad_TEK_SATIR_duzen_bozulmadi(makulluk_olcumu):
    """Kısa adda hiçbir şey değişmedi: tek satır, bindirme yok, satır yüksekliği büyümedi."""
    s = makulluk_olcumu[KISA_AD]["sonra"]
    assert s["satir_sayisi"] == 1, f"{KISA_AD}: {s['satir_sayisi']} satıra sarmış — düzen bozuldu"
    assert s["bindirme_px"] <= 0
    o = makulluk_olcumu[KISA_AD]["once"]
    assert o["satir_sayisi"] == 1 and o["bindirme_px"] <= 0, (
        "kısa ad düzeltme öncesi de sorunsuzdu; sonrasında da aynı kalmalı (regresyon kapısı)")


def test_medyan_ad_TEK_SATIRDA_kaliyor(makulluk_olcumu):
    """340px'in amacı bindirmeyi kapatmak DEĞİL (onu sınıf kuralı kapatıyor), sarmayı İSTİSNA
    tutmaktı. Ekran görüntüsündeki iki ad (32 ve 39 karakter — evren medyanı 38) tek satırda
    kalmalı; yoksa genişletme parasını ödedik, malı almadık."""
    for ad in ("yeniden_hesap:orphan_state_files", "eleme:component_ic.eslesme:sema_elemesi"):
        s = makulluk_olcumu[ad]["sonra"]
        assert s["satir_sayisi"] == 1, f"{ad} ({len(ad)} kar.): {s['satir_sayisi']} satır"


def test_en_uzun_ad_SARAR_ama_kirpilmaz(makulluk_olcumu):
    """Evrenin en uzunu (54 karakter) sarar — ve TAMAMI ekranda kalır. Kırpma olsaydı ad
    greplenemezdi; iki satır olması bilinçli bedeldir."""
    s = makulluk_olcumu[EN_UZUN_AD]["sonra"]
    assert s["satir_sayisi"] == 2, f"beklenen 2 satır, ölçülen {s['satir_sayisi']}"
    assert s["ad"] == EN_UZUN_AD, "ad emisyonda kısaltılmış — kırpma sözleşmeyi bozar"


@pytest.mark.parametrize("panel", ["lcRows", "wv", "eleme"])
def test_kardes_panellerde_de_BINDIRME_yok(kardes_olcumu, panel):
    """AYNI SINIF TARAMASI — kusur tek panelde değil. Aynı kartın üç kardeş paneli de sabit
    kolonda kimlik taşıyor ve ölçüldü: `score_calibration_history.jsonl` (31 kar. = 269px) 170px'lik
    kolonda, `llm_opinion_calibration.gercek` (30 kar. = 260px) 200px'lik kolonda taşıyordu.
    Sınıf kuralı üçünü de kapsar — kolon genişliklerine DOKUNULMADAN."""
    olcum = kardes_olcumu[panel]
    assert olcum, f"{panel}: emisyon hiç satır üretmedi — ölçüm YAPILAMADI"
    for ad, o in olcum.items():
        assert o["sonra"]["bindirme_px"] <= 0, (
            f"{panel}/{ad}: {o['sonra']['bindirme_px']}px bindirme "
            f"(kolon {o['sonra']['kolon1_px']}px)")


@pytest.mark.parametrize("panel,ad", [("wv", "score_calibration_history.jsonl"),
                                      ("eleme", "llm_opinion_calibration.gercek")])
def test_kardes_paneller_duzeltme_ONCESI_biniyordu(kardes_olcumu, panel, ad):
    """Kardeş panellerin de GERÇEKTEN kusurlu olduğu ölçülür — yoksa `test_kardes_…_yok` boş bir
    tören olurdu. Bu iki ad düzeltme öncesi kendi kolonlarını aşıyordu."""
    o = kardes_olcumu[panel][ad]["once"]
    assert o["bindirme_px"] > 0, f"{panel}/{ad}: öncesinde de bindirme yokmuş ({o['bindirme_px']}px)"


# ===============================================================================================
# 3 · SINIF KAPSAMI — 102 emisyonun HEPSİ tek kuralın altında
# ===============================================================================================
def test_sabit_kolonlu_emisyonlarin_HEPSI_trow_ailesinde():
    """Sabit px kolon kullanan her ızgara emisyonu `.trow` olmalı — yoksa sınıf kuralının dışında
    kalır ve aynı kusur `.trow` olmayan bir satırda sessizce yeniden doğar."""
    disarida = []
    satirlar = KOD.splitlines()
    for i, ln in enumerate(satirlar, 1):
        for m in re.finditer(r'grid-template-columns:([^"`;]+)', ln):
            if not any(re.fullmatch(r"\d+px", t) for t in m.group(1).split()):
                continue
            baglam = "\n".join(satirlar[max(0, i - 3):i + 1])
            if "trow" in baglam:
                continue
            # Izgara bir SABİTTE tanımlanmış olabilir (`const CAPKOL = "grid-template-columns:…"`);
            # o zaman kapsam sabiti TÜKETEN emisyonlardan gelir. Sabitin her kullanımı `.trow`
            # değilse kapsam dışıdır — bu yüzden hepsi tek tek sınanır.
            sabit = re.match(r"\s*(?:const|let)\s+(\w+)\s*=", ln)
            if sabit:
                # Yalnız `${AD}` ARA-DEĞERLERİ sayılır: çıplak ad araması `kol`u `kolonlar`ın
                # içinde de bulur ve kapsamı olduğundan geniş gösterirdi.
                ad = "${%s}" % sabit.group(1)
                kul = [k for k, l in enumerate(satirlar, 1) if k != i and ad in l]
                if kul and all("trow" in "\n".join(satirlar[max(0, k - 3):k + 1]) for k in kul):
                    continue
            disarida.append((i, m.group(1).strip()[:60]))
    assert not disarida, (
        f"`.trow` ailesi DIŞINDA sabit kolonlu ızgara: {disarida} — bunlar `.trow > *` kuralının "
        "kapsamı dışındadır ve taşma sözleşmesi onlar için YOK demektir.")


def test_emisyon_ve_sabit_kolon_sayimi_RATCHET():
    """Ölçülen kapsam fotoğrafı. Sayılar büyüyebilir (yeni panel), ama DÜŞERSE ya emisyon silinmiş
    ya da tarama körelmiştir; ikisi de sessizce olmamalı."""
    emisyon = len(re.findall(r"grid-template-columns:", KOD))
    sabit = sum(1 for m in re.finditer(r'grid-template-columns:([^"`;]+)', KOD)
                for t in m.group(1).split() if re.fullmatch(r"\d+px", t))
    assert emisyon >= 100, f"ızgara emisyonu {emisyon} — ölçülen taban 102"
    assert sabit >= 300, f"sabit px kolon {sabit} — ölçülen taban 304"
