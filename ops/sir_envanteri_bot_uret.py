#!/usr/bin/env python3
"""ops/sir_envanteri_bot_uret.py — sır envanterinin BOT BAŞI satırlarını rotasyon tablosundan ÜRET (G3b Task 2, 2026-10-01).

NEDEN VAR. Operatör kararı (2026-09-30, kadroda 21 bot — 3 canlı + dalga 1/2/3): "bot sayısından bağımsız tasarım" —
bot başına her tablo satırı TEK bot listesinden türer, ELLE yazılan satır sayısı bot sayısıyla BÜYÜMEZ. Rotasyon aracı
(`deploy/oracle-a1/sir_rotasyon.sh`) bot başı satırlarını kabuktaki TEK listeden (`_SOHBET_BOTLARI`) döngüyle basar; ama
`deploy/sir_envanteri.yaml` o tablonun AYNASIDIR (v447 A1/A2 küme · v520 A3 sıra eşitliği · v491 A5 takma ad kopya
kümesi) ve ayna elle tutulsaydı her yeni bot için birkaç YAML bloğu elle yazılırdı — tam da kararın yasakladığı şey.
Bu betik o blokları tablonun ÇIKTISINDAN (`sir_rotasyon.sh --kopyalar`) üretir; envanterin geri kalanı elle kalır.
Ayna şablonu (envantere `her_bot:` gibi bir şema alanı) REDDEDİLDİ: envanteri okuyan on kadar okuyucunun (v447 · v520 ·
v491 · v565 · v464 · v476 · v554 · v439 · `vault_sir_koy.sh`) her biri şablonu açmak zorunda kalırdı; üretilmiş düz
satırlar o okuyucuların HİÇBİRİNE dokunmaz (ölçüm: Task 2 raporu).

BÖLGE SÖZLEŞMESİ. Envanterde iki tür işaretli bölge vardır; işaretçiler elle yazılır, ARASI üretilir:

    <girinti># >>> ÜRETİLDİ kopyalar <alt komut> <sır> | tuketici: <şablon — {ad} bot adıyla değişir>
    <girinti># <<< ÜRETİLDİ
        → `rotasyon_kopyalari.kopyalar` satırları: tablonun o (alt komut, sır) çiftine ait, sohbet profili `.env`ine
          yazan her satır için bir blok (sıra tablonunki).

    <girinti># >>> ÜRETİLDİ kopya_kaynaklari <sır>
    <girinti># <<< ÜRETİLDİ
        → bir `vault_kv` girdisinin `kopya_kaynaklari` öğeleri: o sırrın tablodaki REFERANS (ilk) satırı DIŞINDAKİ bütün
          `env`/`dosya` satırları (`env_satiri`/`dosya`) — v491 A5'in `{kaynak} ∪ kopya_kaynaklari` = tablo kuralının aynası
          (kaynak = referans, v520 A5). 2026-10-01'e dek "o sırrın sohbet profili satırları"ydı; kiracı anahtarında iki tanım
          AYNI satırları verir (referans render hedefi + yalnız sohbet kopyaları), bot anahtarlarında (G3b Task 3) referans
          dışı kopyalar kapı + rapor + sohbet `.env`idir — genel tanım ikisini birden doğru üretir.

    <girinti># >>> ÜRETİLDİ alt_ailesi <alt komut şablonu — {ad} bot adıyla değişir>
    <girinti># şablon <yol şablonu> | tuketici: <metin şablonu>      (bir ya da daha çok satır — ELLE, korunur)
    <girinti># <<< ÜRETİLDİ
        → BOT BAŞI ALT KOMUT AİLESİ (G3b Task 3, 2026-10-01; Task 2 incelemesi M6): `kapi-bot-<ad>` gibi aile BOT BAŞINA
          bir alt komuttur ve satırlarının hepsi o bota aittir (referans render hedefi · `.env-apisix` · rapor · sohbet).
          Her bot için (liste sırasıyla) tablonun o alt komuta ait satırları SIRAYLA yazılır; tüketici metni satırın
          yolunu karşılayan şablondan gelir. Satırı karşılamayan ya da hiçbir satırı karşılamayan şablon SÖZLEŞME hatasıdır.

"Bot başı satır" = yolu `<_SOHBET_KOKU>/profiles/<bot>/.env` olan satır, `<bot>` ∈ `_SOHBET_BOTLARI`. Tabloda bot başı
satırı olan her (alt komut, sır) çiftinin BİR `kopyalar` bölgesi olmak ZORUNDADIR (yoksa çıkış 1: işaretsiz aile ayna
dışında kalırdı) ve her bölgenin ailesi DOLU olmalıdır (boş bölge = bayat işaretçi, çıkış 1). "Bot başı alt komut" = adı
`<önek>-<bot>` olan alt komut; önek ailesi BÜTÜN botları kapsamak ZORUNDADIR ve BİR `alt_ailesi` bölgesi taşır — o
ailelerin sohbet satırları `kopyalar` ailelerine KARIŞMAZ (aile başına tek bot olurdu: "bot listesini kapsamıyor").

KOMUT SATIRI SÖZLEŞMESİ (ops aracı sözleşmesi KOMUT SATIRIdır, `main()` değil):

    python ops/sir_envanteri_bot_uret.py              # KURU koşum: farkı basar, HİÇBİR ŞEY YAZMAZ
    python ops/sir_envanteri_bot_uret.py --kontrol    # yazMA; envanterin bölgeleri güncel mi
    python ops/sir_envanteri_bot_uret.py --uygula     # YAZ
    (--betik <yol> · --envanter <yol>: çivilerin geçici kopyaları için; varsayılan depo yolları)

Çıkış kodu HÜKÜMDÜR: 0 güncel / yazıldı / kuru tamamlandı · 1 BAYAT (`--kontrol`) ya da bölge/tablo SÖZLEŞME hatası ·
2 KULLANIM (`--kontrol` ile `--uygula` birlikte — biri SORAR öteki YAZAR; `ops/vault_politika_uret.py` emsali).

SIR YOK: betik yalnız AD ve YOL işler; tablo (`--kopyalar`) değer taşımaz ve root istemez. Damga YOK: aynı tablodan aynı
bayt çıkar (`--kontrol` kapısı anlamlı kalsın diye).

OKUYUCU (Yasa 6): yazdığı tek dosya `deploy/sir_envanteri.yaml`dır (okuyucuları yukarıda); tazelik kapısı
`tests/test_bot_agi_sirlari_v604.py` B12. Yeni bot = `_SOHBET_BOTLARI`na bir ad → bu betik `--uygula`.
"""
from __future__ import annotations

import argparse
import difflib
import os
import pathlib
import re
import subprocess
import sys

import yaml

KOK = pathlib.Path(__file__).resolve().parents[1]
BETIK = KOK / "deploy" / "oracle-a1" / "sir_rotasyon.sh"
ENVANTER = KOK / "deploy" / "sir_envanteri.yaml"

BAS_RE = re.compile(r"^(?P<girinti>[ ]*)# >>> ÜRETİLDİ (?P<tur>kopyalar|kopya_kaynaklari|alt_ailesi) (?P<arg>.+?)\s*$")
SON_RE = re.compile(r"^[ ]*# <<< ÜRETİLDİ\s*$")
SABLON_RE = re.compile(r"^[ ]*# şablon (?P<yol>\S+) \| tuketici: (?P<metin>.+?)\s*$")


class Sozlesme(Exception):
    """Bölge ya da tablo sözleşmesi bozuk — üretim YAPILMAZ (çıkış 1, sebep adıyla)."""


def _sabit(metin: str, ad: str) -> str:
    bulunan = re.findall(rf'^{ad}="([^"]*)"$', metin, re.M)
    if len(bulunan) != 1:
        raise Sozlesme(f"betikte TEK `{ad}=\"…\"` ataması yok (bulunan {len(bulunan)})")
    return bulunan[0]


def tablo(betik: pathlib.Path) -> tuple[list[str], str, list[list[str]]]:
    """(botlar, sohbet kökü, tablo satırları) — satırlar betiğin KENDİ çıktısıdır (`--kopyalar`, root istemez)."""
    metin = betik.read_text(encoding="utf-8")
    botlar = _sabit(metin, "_SOHBET_BOTLARI").split()
    kok = _sabit(metin, "_SOHBET_KOKU")
    if not botlar or not kok.startswith("/"):
        raise Sozlesme(f"bot listesi boş ya da kök mutlak değil: {botlar!r} {kok!r}")
    ortam = {k: v for k, v in os.environ.items() if not k.startswith("SIR_ROT_")}
    r = subprocess.run(["bash", str(betik), "--kopyalar"], capture_output=True, text=True, env=ortam)
    if r.returncode != 0:
        raise Sozlesme(f"`{betik.name} --kopyalar` çıkış {r.returncode}: {r.stderr.strip()[:300]}")
    satirlar = [s.split() for s in r.stdout.splitlines() if s.strip()]
    bozuk = [s for s in satirlar if len(s) != 8]
    if bozuk:
        raise Sozlesme(f"tablo satırı 8 sütun değil: {bozuk[:2]}")
    return botlar, kok, satirlar


def bot_alt_onekleri(botlar: list[str], satirlar: list[list[str]]) -> set[str]:
    """BOT BAŞI ALT KOMUT aileleri — adı `<önek>-<bot>` olan alt komutların önekleri. Önek ailesi BÜTÜN botları kapsamak
    zorundadır: bir botun alt komutu eksikse o bot ayna dışında kalırdı (SÖZLEŞME). Sıra/kapsam tablodan ölçülür."""
    altlar = list(dict.fromkeys(s[0] for s in satirlar))
    onekler = {a[: -len(b) - 1] for a in altlar for b in botlar if a.endswith("-" + b) and len(a) > len(b) + 1}
    for onek in sorted(onekler):
        eksik = [b for b in botlar if f"{onek}-{b}" not in altlar]
        if eksik:
            raise Sozlesme(f"bot başı alt komut ailesi `{onek}-<bot>` bot listesini kapsamıyor — eksik: {eksik}")
    return onekler


def bot_aileleri(botlar: list[str], kok: str, satirlar: list[list[str]]) -> dict[tuple[str, str], list[tuple[str, list[str]]]]:
    """(alt komut, sır) → [(bot, satır)] — yalnız sohbet profili `.env`ine yazan satırlar, tablo sırasıyla. Bot başı alt
    komut ailelerinin (`bot_alt_onekleri`) satırları HARİÇ: onların aynası `alt_ailesi` bölgesidir."""
    desen = re.compile(re.escape(kok) + r"/profiles/([^/]+)/\.env")
    bot_altlari = {f"{o}-{b}" for o in bot_alt_onekleri(botlar, satirlar) for b in botlar}
    aileler: dict[tuple[str, str], list[tuple[str, list[str]]]] = {}
    for s in satirlar:
        if s[0] in bot_altlari:
            continue
        m = desen.fullmatch(s[3])
        if not m:
            continue
        if m.group(1) not in botlar:
            raise Sozlesme(f"listede OLMAYAN bot için satır: {' '.join(s)}")
        if s[2] != "env" or s[5] != "koru" or s[6] != "koru":
            raise Sozlesme(f"bot başı satır `env … koru koru` değil (üreteç yalnız onu tanır): {' '.join(s)}")
        aileler.setdefault((s[0], s[1]), []).append((m.group(1), s))
    for (alt, sir), aile in aileler.items():
        if [b for b, _ in aile] != botlar:
            raise Sozlesme(f"{alt}/{sir}: aile bot listesini SIRAYLA kapsamıyor: {[b for b, _ in aile]} ≠ {botlar}")
    return aileler


def _kopyalar_blogu(girinti: str, sablon: str, aile: list[tuple[str, list[str]]]) -> list[str]:
    if '"' in sablon or "\\" in sablon or "{ad}" not in sablon:
        raise Sozlesme(f"tüketici şablonu çift tırnak/ters bölü taşıyamaz ve {{ad}} içermeli: {sablon!r}")
    out: list[str] = []
    for bot, (alt, sir, tur, yol, alan, _m, _s, onek) in aile:
        out += [f"{girinti}- alt_komut: {alt}", f"{girinti}  sir: {sir}", f"{girinti}  tur: {tur}",
                f'{girinti}  yol: "{yol}"', f"{girinti}  alan: {alan}", f"{girinti}  mod: null",
                f"{girinti}  sahip: null"]
        if onek != "-":
            out.append(f"{girinti}  onek: {onek}")
        out.append(f'{girinti}  tuketici: "{sablon.replace("{ad}", bot)}"')
    return out


def _kopya_kaynaklari_blogu(girinti: str, sir: str, satirlar: list[list[str]]) -> list[str]:
    """`sir`in tablodaki REFERANS (ilk okunabilir) satırı DIŞINDAKİ `env`/`dosya` satırları — v491 A5 eşleme sözlüğüyle."""
    okunur = [s for s in satirlar if s[1] == sir and s[2] in ("env", "dosya", "url")]
    if not okunur:
        raise Sozlesme(f"{sir} sırrının tabloda okunabilir satırı YOK (bayat işaretçi)")
    out: list[str] = []
    for _alt, _sir, tur, yol, alan, _m, _s, onek in okunur[1:]:
        if tur not in ("env", "dosya"):
            raise Sozlesme(f"{sir}: referans dışı `{tur}` satırı kopya kaynağı olamaz (v491 A5 sözlüğü env|dosya): {yol}")
        onek_j = "null" if onek == "-" else f'"{onek}"'
        alan_j = "null" if alan == "-" else alan
        tur_j = "env_satiri" if tur == "env" else "dosya"
        out.append(f'{girinti}- {{tur: {tur_j}, dosya: "{yol}", alan: {alan_j}, onek: {onek_j}}}')
    if not out:
        raise Sozlesme(f"{sir} sırrının referans dışı kopyası YOK (bayat işaretçi)")
    return out


def _alt_ailesi_blogu(girinti: str, sablon_alt: str, sablonlar: list[tuple[str, str]], botlar: list[str],
                      satirlar: list[list[str]]) -> list[str]:
    """Bot başı alt komut ailesi: her bot için (liste sırasıyla) tablonun `sablon_alt.replace("{ad}", bot)` satırları
    SIRAYLA; tüketici yolu karşılayan TEK şablondan. Mod/sahip tablonun açık değerinden (`0400 root:root` → "400"/"root"),
    `koru` → null (envanterin elle yazılmış emsal satırlarıyla aynı biçim)."""
    if "{ad}" not in sablon_alt:
        raise Sozlesme(f"alt_ailesi şablonu {{ad}} içermeli: {sablon_alt!r}")
    if not sablonlar:
        raise Sozlesme(f"alt_ailesi {sablon_alt}: hiç `# şablon <yol> | tuketici: <metin>` satırı yok")
    for _yol, metin in sablonlar:
        if '"' in metin or "\\" in metin:
            raise Sozlesme(f"tüketici şablonu çift tırnak/ters bölü taşıyamaz: {metin!r}")
    kullanilan: set[str] = set()
    out: list[str] = []
    for bot in botlar:
        alt = sablon_alt.replace("{ad}", bot)
        blok = [s for s in satirlar if s[0] == alt]
        if not blok:
            raise Sozlesme(f"alt_ailesi {sablon_alt}: tabloda `{alt}` satırı YOK")
        for _alt, sir, tur, yol, alan, mod, sahip, onek in blok:
            eslesen = [(ys, m) for ys, m in sablonlar if ys.replace("{ad}", bot) == yol]
            if len(eslesen) != 1:
                raise Sozlesme(f"alt_ailesi {sablon_alt}: `{yol}` satırını karşılayan TEK şablon yok ({len(eslesen)})")
            kullanilan.add(eslesen[0][0])
            mod_j = "null" if mod == "koru" else f'"{mod.lstrip("0") or "0"}"'
            sahip_j = "null" if sahip == "koru" else f'"{sahip.split(":", 1)[0]}"'
            out += [f"{girinti}- alt_komut: {alt}", f"{girinti}  sir: {sir}", f"{girinti}  tur: {tur}",
                    f'{girinti}  yol: "{yol}"', f"{girinti}  alan: {'null' if alan == '-' else alan}",
                    f"{girinti}  mod: {mod_j}", f"{girinti}  sahip: {sahip_j}"]
            if onek != "-":
                out.append(f"{girinti}  onek: {onek}")
            out.append(f'{girinti}  tuketici: "{eslesen[0][1].replace("{ad}", bot)}"')
    bos = [ys for ys, _ in sablonlar if ys not in kullanilan]
    if bos:
        raise Sozlesme(f"alt_ailesi {sablon_alt}: hiçbir satırı karşılamayan (bayat) şablon: {bos}")
    return out


def uret(envanter_metni: str, botlar: list[str], kok: str, satirlar: list[list[str]]) -> str:
    """Envanter metnindeki her işaretli bölgenin İÇİNİ yeniden yazar; işaretçiler, şablon satırları ve bölge dışı AYNEN kalır."""
    aileler = bot_aileleri(botlar, kok, satirlar)
    onekler = bot_alt_onekleri(botlar, satirlar)
    girdi = envanter_metni.splitlines(keepends=True)
    cikti: list[str] = []
    kullanilan: set[tuple[str, str]] = set()
    kullanilan_onek: set[str] = set()
    i = 0
    while i < len(girdi):
        satir = girdi[i]
        m = BAS_RE.match(satir.rstrip("\n"))
        if not m:
            if SON_RE.match(satir.rstrip("\n")):
                raise Sozlesme(f"satır {i + 1}: açılışsız `<<< ÜRETİLDİ`")
            cikti.append(satir)
            i += 1
            continue
        cikti.append(satir)
        j = i + 1
        while j < len(girdi) and not SON_RE.match(girdi[j].rstrip("\n")):
            if BAS_RE.match(girdi[j].rstrip("\n")):
                raise Sozlesme(f"satır {j + 1}: kapanmamış bölgenin içinde yeni `>>> ÜRETİLDİ`")
            j += 1
        if j >= len(girdi):
            raise Sozlesme(f"satır {i + 1}: bölge kapanmıyor (`# <<< ÜRETİLDİ` yok)")
        girinti, tur, arg = m.group("girinti"), m.group("tur"), m.group("arg")
        if tur == "alt_ailesi":
            # Şablon satırları başlığın PARÇASIDIR (elle, korunur); üretilen blok onlardan sonra başlar.
            k = i + 1
            sablonlar: list[tuple[str, str]] = []
            while k < j and SABLON_RE.match(girdi[k].rstrip("\n")):
                sm = SABLON_RE.match(girdi[k].rstrip("\n"))
                sablonlar.append((sm.group("yol"), sm.group("metin")))
                cikti.append(girdi[k])
                k += 1
            sablon_alt = arg.strip()
            onek = sablon_alt.replace("-{ad}", "") if sablon_alt.endswith("-{ad}") else None
            if onek is None or onek not in onekler:
                raise Sozlesme(f"satır {i + 1}: alt_ailesi {sablon_alt} tabloda bot başı alt komut ailesi DEĞİL (bayat işaretçi)")
            kullanilan_onek.add(onek)
            yeni = _alt_ailesi_blogu(girinti, sablon_alt, sablonlar, botlar, satirlar)
            cikti.extend(s + "\n" for s in yeni)
            cikti.append(girdi[j])
            i = j + 1
            continue
        if tur == "kopyalar":
            if " | tuketici: " not in arg:
                raise Sozlesme(f"satır {i + 1}: `kopyalar` işaretçisi `| tuketici: <şablon>` taşımıyor")
            anahtar_metni, sablon = arg.split(" | tuketici: ", 1)
            parca = anahtar_metni.split()
            if len(parca) != 2:
                raise Sozlesme(f"satır {i + 1}: `kopyalar <alt komut> <sır>` bekleniyordu: {anahtar_metni!r}")
            anahtar = (parca[0], parca[1])
            if anahtar not in aileler:
                raise Sozlesme(f"satır {i + 1}: {anahtar[0]}/{anahtar[1]} için tabloda bot başı satır YOK (bayat işaretçi)")
            kullanilan.add(anahtar)
            yeni = _kopyalar_blogu(girinti, sablon.strip(), aileler[anahtar])
        else:
            sir = arg.split()[0] if arg.split() else ""
            try:
                yeni = _kopya_kaynaklari_blogu(girinti, sir, satirlar)
            except Sozlesme as e:
                raise Sozlesme(f"satır {i + 1}: {e}") from e
        cikti.extend(s + "\n" for s in yeni)
        cikti.append(girdi[j])
        i = j + 1
    eksik = sorted(set(aileler) - kullanilan)
    if eksik:
        raise Sozlesme(f"bot başı satır ailesinin envanterde `kopyalar` bölgesi YOK: {eksik} — ayna dışında kalırdı")
    eksik_onek = sorted(onekler - kullanilan_onek)
    if eksik_onek:
        raise Sozlesme(f"bot başı alt komut ailesinin envanterde `alt_ailesi` bölgesi YOK: "
                       f"{[o + '-{ad}' for o in eksik_onek]} — ayna dışında kalırdı")
    metin = "".join(cikti)
    yaml.safe_load(metin)          # sözdizimi kapısı: üretim bozuk YAML YAZAMAZ (hata çıkış 1'e döner — main)
    return metin


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--kontrol", action="store_true", help="yazMA; bölgeler güncel mi (çıkış 1 = bayat)")
    ap.add_argument("--uygula", action="store_true", help="envanteri YAZ")
    ap.add_argument("--betik", type=pathlib.Path, default=BETIK, help="rotasyon aracı (çivi kopyaları için)")
    ap.add_argument("--envanter", type=pathlib.Path, default=ENVANTER, help="envanter (çivi kopyaları için)")
    a = ap.parse_args(argv)
    if a.kontrol and a.uygula:
        print("KULLANIM: --kontrol ile --uygula birlikte verilemez (biri SORAR, diğeri YAZAR — sessiz öncelik yok)")
        return 2
    try:
        botlar, kok, satirlar = tablo(a.betik)
        eski = a.envanter.read_text(encoding="utf-8")
        yeni = uret(eski, botlar, kok, satirlar)
    except (Sozlesme, yaml.YAMLError, OSError) as e:
        print(f"SÖZLEŞME HATASI — üretim YAPILMADI: {e}", file=sys.stderr)
        return 1
    if yeni == eski:
        print(f"GÜNCEL: {a.envanter} bot başı bölgeleri tabloyla uyumlu ({len(botlar)} bot)")
        return 0
    fark = "".join(difflib.unified_diff(eski.splitlines(keepends=True), yeni.splitlines(keepends=True),
                                        str(a.envanter), str(a.envanter) + " (üretilen)"))
    if a.kontrol:
        print(f"BAYAT: {a.envanter} bot başı bölgeleri tablodan geride — `python ops/sir_envanteri_bot_uret.py --uygula`")
        print(fark)
        return 1
    if a.uygula:
        a.envanter.write_text(yeni, encoding="utf-8")
        print(f"yazıldı: {a.envanter} ({len(botlar)} bot)")
        return 0
    print(fark)
    print("KURU koşum — hiçbir şey yazılmadı (yazmak için --uygula)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
