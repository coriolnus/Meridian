"""v399 — TSK-117 K-4 (S1=A′, S2): seri rampası 6–10 rol bantları DIŞINDA; huni jetonları seri
değerlerinden TÜRER (kopya değil); Tailwind palet hex'leri testin içinde çözülür (tema.css
var(--color-X-N) → tailwind palet dosyası ölçülerek, `_tailwind_renk_hex`). (TSK-117, 2026-09-04)

TSK-136 (2026-09-04, operatör kararı 10:10Z) HEDEFİ DEĞİŞTİRDİ: K-4'ün rezerve-hue seri
rampası VARSAYILAN `ui/src/tema.css`ten kalktı (orijinale — blue/orange/violet/cyan/pink —
döndü) ve 'Meridian Palet' preset'ine taşındı (`ui/src/styles/presets/meridian-palet.css`).
Bu dosyanın "seri bandın dışında" ve "huni seri'den türer" iddiaları artık PRESET dosyasını
okur, `ui/src/tema.css`i DEĞİL — VARSAYILANIN kendisi bilerek rol bantlarının İÇİNDEDİR
(operatörün kararı, spec S6) ve `test_VARSAYILAN_seri_ROL_BANTLARINDA` bunu düz bir değer
ölçümü olarak (hue-gate DEĞİL) ayrıca doğrular.

NUMARA ÇAKIŞMASI TARANDI (2026-09-04): `ls tests | grep v399` BOŞ döndü.

HUNİ YOLU ÖLÇÜLDÜ, BREF'İN TASLAĞI DEĞİL: `grep -n '"huni-1"' meridian/web/tokens.json` iki kayıt
verdi (`tema/gunduz/murekkep/huni-1`, `tema/gece/murekkep/huni-3`) — brief'in taslak yolu
(`d["rol"]["gunduz"]["huni"]`) bu depoda YOK. Aşağıdaki testler ölçülen gerçek yolu kullanır.
`$value` bir dize değil bir sözlük (`{"hex": "#…", "components": […], …}`) — karşılaştırma
`$value["hex"]` üzerinden.

DÜZELTME TURU 1 (TSK-117 G7 r1, 2026-09-04) — İKİ DÜZELTME:
1. HUNİ EŞLEMESİ (1,6),(2,7),(3,8) → (1,6),(2,8),(3,9): ilk yazım "huni sırayla ilk üç seri"
   diye VARSAYDI. Ölçülen gerçek `ui/src/pano/yuzeyler/kanban/Huni.tsx::RENK_ILK/ORTA/VARIS`
   TAM OLARAK `var(--color-seri-6/8/9)` okuyor (huni-2 seri-7 DEĞİL) — huni tokens.json kaydı bu
   GERÇEK UI'yi tarif etmeli, keyfi bir "ilk üç" kuralını değil (tek-kaynak yasası: iki
   tanım aynı gerçeği İKİ FARKLI biçimde söylerse biri yanlıştır).
2. TEK KAYNAK — `BANTLAR`/`_bantta` SİLİNDİ, v388'İN `ROL_BANTLARI`/`_bantta`SI İTHAL EDİLDİ:
   iki dosya aynı bant tablosunun ayrı kopyalarını taşıyordu (v399 ASCII adlarla `(336,366)`
   sarmalı gösterimi, v388 Türkçe adlarla `(336.0,6.0)` `alt>ust` gösterimi) — FONKSİYONEL
   OLARAK eşdeğerdi ama biri değişip öteki unutulursa sessizce ayrışırdı. v388 SSoT: `_bantta`
   ORADA yaşıyor (`_jeton_hue`/pozitif kontrol de onu kullanıyor), v399 sadece ithal eder.
"""
import colorsys
import json
import pathlib
import re

from meridian import config
from tests.test_hafiza_genel_bakis_v388 import ROL_BANTLARI, _bantta, _tailwind_renk_hex

ROOT = pathlib.Path(config.ROOT)
TEMA = ROOT / "ui" / "src" / "tema.css"
PRESET = ROOT / "ui" / "src" / "styles" / "presets" / "meridian-palet.css"
TOKENS = ROOT / "meridian" / "web" / "tokens.json"

assert ROL_BANTLARI, "v388 ROL_BANTLARI boş — ithalat bayat mı ölçüldü mü?"  # kullanım kanıtı


def _hue(hexstr: str) -> float:
    r, g, b = (int(hexstr[i : i + 2], 16) / 255 for i in (1, 3, 5))
    h, _l, _s = colorsys.rgb_to_hls(r, g, b)
    return h * 360


def _tailwind_hex(ad: str) -> str:
    """`--color-teal-600` → hex: `node_modules/tailwindcss/theme.css` içinden ÖLÇÜLEREK
    (v388'in `_tailwind_renk_hex` yardımcısı — oklch→sRGB dönüşümü orada, tek kaynak)."""
    return _tailwind_renk_hex(ad)


def _seri(kaynak_dosya: pathlib.Path, tema_blok: str) -> dict[int, str]:
    css = kaynak_dosya.read_text(encoding="utf-8")
    m = re.search(rf"{tema_blok}\s*\{{([^}}]*)\}}", css, re.S)
    assert m, f"{tema_blok} bloğu {kaynak_dosya.name}'te bulunamadı — desen bayat"
    blok = m.group(1)
    return {
        int(m2.group(1)): m2.group(2)
        for m2 in re.finditer(r"--seri-(\d+):\s*var\((--color-[a-z]+-\d+)\)", blok)
    }


def _seri_preset(gece: bool) -> dict[int, str]:
    sec = r'\.dark:root\[data-theme-preset="meridian-palet"\]' if gece \
        else r':root\[data-theme-preset="meridian-palet"\]'
    return _seri(PRESET, sec)


def test_taranan_dosyalar_YERINDE():
    """KÖRLÜK ALARMI: yol bayatlarsa aşağıdaki `_seri`/tokens okuması sessizce boş/hatalı döner."""
    for p in (TEMA, TOKENS, PRESET):
        assert p.is_file(), f"ölçülecek dosya yok: {p}"


def test_seri_6_10_PRESETTE_rol_bantlarinda_DEGIL():
    """TSK-136 (2026-09-04): rezerve-hue rampası artık VARSAYILANDA değil, 'Meridian Palet'
    preset'inde — bu test preset CSS'ini okur."""
    for gece, ad in ((False, "gündüz"), (True, "gece")):
        seri = _seri_preset(gece)
        assert seri, f"preset {ad} bloğunda hiç --seri-N okunamadı — desen bayat"
        for k, tw in seri.items():
            if k < 6:
                continue
            h = _hue(_tailwind_hex(tw))
            assert _bantta(h) is None, f"preset {ad} seri-{k} ({tw}, {h:.1f}°) rol bandında: {_bantta(h)}"


def test_VARSAYILAN_seri_ROL_BANTLARINDA():
    """DEĞER ÖLÇÜMÜ (hue-gate DEĞİL): VARSAYILAN `ui/src/tema.css` orijinale (blue/orange/
    violet/cyan/pink) döndü — bu eski K-4'ün ÖLÇTÜĞÜ kusurun (rol×veri-kimliği çakışması)
    varsayılan temada BİLİNÇLİ olarak geri gelmesidir (operatör kararı, TSK-136 2026-09-04);
    düzeltme preset'te yaşar. ÖLÇÜLEN (bu testin ÖLÇÜMÜ, tahmin DEĞİL): 7/10 (5 seri × 2 tema)
    bantta — blue (GEZİNME, iki temada), violet (MOD, iki temada), cyan (BİLGİ, iki temada),
    orange yalnız gündüzde (UYARI+YÖN-EKSİ; gece 400 tonu bandın 1° dışında ölçüldü), pink
    HİÇBİR temada bantta değil (iki temada da serbest). Sayı DEĞİŞİRSE tema.css sessizce
    değişmiş olabilir; bu satır o sürüklenmeyi yakalar."""
    ihlalde = []
    for blok in (":root", r"\.dark"):
        seri = _seri(TEMA, blok)
        assert seri, f"{blok} bloğunda hiç --seri-N okunamadı — desen bayat"
        for k, tw in seri.items():
            if k < 6:
                continue
            h = _hue(_tailwind_hex(tw))
            if _bantta(h) is not None:
                ihlalde.append((blok, k, tw, round(h, 1), _bantta(h)))
    assert len(ihlalde) == 7, (
        f"VARSAYILAN seri-bant-içi sayısı {len(ihlalde)} ≠ ölçülen 7 (2026-09-04) — "
        f"tema.css sessizce değişmiş olabilir: {ihlalde}")


def test_huni_jetonlari_PRESETTE_seri_referansi_TASIYOR():
    """Eşleme (1,6),(2,8),(3,9) — `ui/src/pano/yuzeyler/kanban/Huni.tsx::RENK_ILK/ORTA/VARIS`
    (ÖLÇÜLEN gerçek UI) ile BİREBİR. TSK-136 (2026-09-04): bu türetim artık VARSAYILANDA
    (tokens.json) değil — preset CSS'i `--huni-N: var(--seri-M)` REFERANSI taşır (statik hex
    DEĞİL, canlı CSS değişkeni — preset seçiliyken seri değişirse huni de değişir)."""
    css = PRESET.read_text(encoding="utf-8")
    for i, k in ((1, 6), (2, 8), (3, 9)):
        assert re.search(rf"--huni-{i}:\s*var\(--seri-{k}\)", css), (
            f"preset --huni-{i} → var(--seri-{k}) referansı yok — kopya/türetim ayrışmış olabilir"
        )


def test_huni_jetonlari_VARSAYILANDA_sabit_dub_hex_TASIYOR():
    """DEĞER ÖLÇÜMÜ: VARSAYILAN tokens.json huni-1/2/3 artık seri'den TÜREMİYOR — orijinal
    (referans commit 4bfa113) sabit Dub hex'lerine geri döndü (TSK-136, 2026-09-04). Bu BİLEREK
    seri-6/8/9'un (blue/violet/cyan) hex'inden FARKLI olabilir — huni maketten birebir sabit bir
    palettir, VARSAYILANDA seri türetimi YOK."""
    d = json.loads(TOKENS.read_text(encoding="utf-8"))
    beklenen = {
        "gunduz": {"huni-1": "#2563eb", "huni-2": "#7c3aed", "huni-3": "#16a34a"},
        "gece": {"huni-1": "#60a5fa", "huni-2": "#a78bfa", "huni-3": "#4ade80"},
    }
    for tema_adi, huniler in beklenen.items():
        murekkep = d["tema"][tema_adi]["murekkep"]
        for ad, hex_ in huniler.items():
            gercek = murekkep[ad]["$value"]["hex"].lower()
            assert gercek == hex_, f"{tema_adi}.{ad} = {gercek} ≠ beklenen sabit {hex_}"
            literal = murekkep[ad].get("$extensions", {}).get("org.meridian.css", {}).get("literal")
            assert literal is not None and literal.lower() == hex_, (
                f"{tema_adi}.{ad} literal ({literal}) ≠ $value.hex ({hex_})"
            )


def test_dugum_stili_istisnasi_KAPANDI():
    from tests.test_hafiza_genel_bakis_v388 import ISTISNALAR

    assert ISTISNALAR == {}, "palet turu bitti — DUGUM_STILI istisnası ölü muafiyet olmamalı"
