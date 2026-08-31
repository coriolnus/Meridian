#!/usr/bin/env python3
"""filo.py — A1 bot filosunu TEK komut-satırı sözleşmesinden oku. LLM yok, tahmin yok.

NEDEN VAR (2026-08-31). Üç botun (@sef · @bekci · @karne) canlı durumu, journal kesiti, oturum
defteri ve profil güncellemesi bugüne kadar Rol-1'in ELLE kurduğu ssh satırlarıyla okunuyordu.
Elle kurulan satır, ölçülmüş üç tuzağı her seferinde yeniden açar:

  (1) SAHTE BAŞARI. `hermes profile update <ad>` etkileşimli onay ister. Boş stdin'de
      "Update cancelled" basar ve **RC=0 ile döner**. RC'ye bakan operatör güncellemenin
      YAPILDIĞINI sanır; canlı profil ESKİ kalır ve bunu hiçbir sayaç göstermez. Bu araç
      onayı `printf` ile borular VE hükmü RC'den DEĞİL ÇIKTIDAKİ BAŞARI DİZGESİNDEN verir.
  (2) UZAK SUDO. `sudo systemctl start` bu oturumların izin sınıfında ENGELLİ. "Denemek" bir
      arıza değil bir SESSİZLİK üretir. `test-atesle` bu yüzden KOŞMAZ: operatörün koşacağı
      tek bloğu BASAR; `--kanit` ise koşumdan SONRA salt-okuma doğrulamayı kendi yapar.
  (3) BOT→BİRİM EŞLEMESİ. @sef botunun birimi `meridian-sef` DEĞİL `meridian-brifing`tir.
      Burada eşleme EZBERLENMEZ: birim dosyalarının kendi `Environment=HERMES_HOME=` satırından
      TÜRETİLİR (tek-kaynak yasası) — dördüncü bot doğduğu gün liste kendiliğinden büyür.

YAPI — SAF KURUCU + İNCE KABUK. ssh'a giden komut DİZGESİNİ kuran fonksiyonlar saftır (yan
etkisiz, testte doğrudan ölçülür); alt-süreci koşan tek yer `_kos`. Bu ayrım, çivilerin
alt-süreci MOCK'lamadan gerçek sözleşmeyi ölçmesini sağlar.

`meridian` İTHAL EDİLMEZ ve bu bir üslup tercihi değil: ithal edilseydi `meridian.obs`
erişilebilir olurdu ve bu araç pytest DIŞINDA, operatörün elinde koşuyor — canlı YEREL deftere
yazardı (3 vaka, 2026-08-30). Yalnız stdlib; çivi `tests/test_filo_araci_v348.py` ithal
listesini AST ile tarar.

ÇIKIŞ KODLARI (sözleşme): 0=başarı · 1=doğrulama kırmızısı · 2=kullanım hatası.
"""
from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
#: ROSTER'IN TEK KAYNAĞI — dağıtılan profil dizinleri. Kod içine yazılmış bir bot demeti
#: canlıyla sessizce ayrışırdı (`meridian/api.py::_ajan_bot_koku` aynı kaynaktan türetir).
PROFIL_DIZINI = KOK / "deploy" / "hermes" / "profiles"
#: BOT→BİRİM eşlemesinin TEK KAYNAĞI — dağıtılan systemd birimleri.
BIRIM_DIZINI = KOK / "deploy" / "oracle-a1"

#: A1 KİMLİĞİ — ÜÇ KATMAN, öncelik: CLI bayrağı > ortam değişkeni > sabit varsayılan.
#:
#: Ortam değişkeni adları UYDURULMADI. `ops/pull-a1-backups.sh` ve `ops/state_yetim_temizle.sh`
#: ZATEN bu adları okuyor; dördüncü bir ad icat etmek üçüncü bir gerçek yaratırdı ve A1 taşındığı
#: gün iki betik taşınıp bu araç sessizce eskiye giderdi (tek-kaynak yasası). `meridian` ithal
#: edilemediği için sabit varsayılan yine de burada duruyor — env, o kopyanın kaçış kapısıdır.
ENV_KULLANICI = "MERIDIAN_A1_USER"
ENV_IP = "MERIDIAN_A1_IP"
ENV_ANAHTAR = "MERIDIAN_A1_KEY"
A1_KULLANICI_VARSAYILAN = "ubuntu"
A1_IP_VARSAYILAN = "130.61.126.87"
A1_ANAHTAR_VARSAYILAN = "~/.ssh/oci-a1.key"

#: `systemctl show` çıktısını birimlere bölen işaret. Boş satır ya da sıra varsayımı yerine
#: AÇIK bir ayraç: bir birim hiç konuşmazsa o birim kayıtta HİÇ GÖRÜNMEZ ve hüküm onu
#: "ÖLÇÜLEMEDİ" der — sessizce bir öncekinin alanlarını devralmaz.
AYRAC = "@@BIRIM"
#: Uzak kabuğun bize `hermes`in GERÇEK çıkış kodunu taşıdığı işaret. ssh'ın kendi RC'si burada
#: işe yaramaz: uzak komut bir boru zinciridir ve son halka `echo`dur.
RC_ISARETI = "@@RC"
DOGRULAMA_ISARETI = "@@DOGRULAMA"
#: Yedeğin GERÇEKTEN alındığının tanığı. Yedek bir VAAT değil bir KAPIDIR: yedeksiz bir
#: güncelleme GERİ ALINAMAZ, o yüzden bu işaret yeşil hükmün ŞARTIDIR (dal-sonu incelemesi).
TAR_ISARETI = "@@TAR tamam"

#: ÖLÇÜLEN başarı dizgesi (`hermes profile update`, 2026-08-31). Hermes bu dizgeyi değiştirirse
#: hüküm KIRMIZIYA düşer ve ham çıktı basılır — yani arıza SESSİZ değil GÜRÜLTÜLÜ olur; doğru
#: yön budur. Gevşetip "Updated" aramak, "Update cancelled"a yaklaşmak demekti.
BASARI_DIZGESI = "✓ Updated"
#: İptal izi BİLEREK GENİŞ (yalnız tam cümle değil): belirsizliği FAZLA beyan etmek dürüsttür,
#: AZ beyan etmek tam da düzeltilen arızadır.
IPTAL_IZI = "cancel"

#: Birim dosyasındaki profil evi. `^` şarttır: bu depoda birim dosyaları uzun yorum blokları
#: taşır ve yorumdaki bir örnek satır eşleşseydi eşleme uydurulmuş olurdu.
_EV_DESENI = re.compile(r"^Environment=HERMES_HOME=(?P<kok>\S+)/(?P<bot>[^/\s]+)\s*$", re.M)


# ─────────────────────────────────────────────────────────────────────────────
#  Roster ve eşleme — TÜRETİLİR
# ─────────────────────────────────────────────────────────────────────────────

def botlar() -> list[str]:
    """Dağıtılan profil dizinlerinden roster."""
    return sorted(p.name for p in PROFIL_DIZINI.iterdir() if p.is_dir())


def profiller() -> dict[str, dict]:
    """`{bot: {birim, timer, ev, kok}}` — birim dosyalarından ÖLÇÜLÜR.

    Bir bot burada YOKSA bu "birimi yok" demektir ve o bilgi `durum`da ADIYLA raporlanır;
    sessizce roster'dan düşürülmez (UYDURMA YASAĞI: eksik birim bir dağıtım boşluğudur).
    """
    harita: dict[str, dict] = {}
    for birim in sorted(BIRIM_DIZINI.glob("*.service")):
        m = _EV_DESENI.search(birim.read_text(encoding="utf-8"))
        if not m:
            continue
        taban = birim.stem
        timer = BIRIM_DIZINI / f"{taban}.timer"
        harita[m.group("bot")] = {
            "birim": f"{taban}.service",
            "timer": f"{taban}.timer" if timer.exists() else None,
            # BEKLENEN ad, timer dosyası OLMASA DA bilinir — "hangi birim eksik" sorusunun
            # cevabı, eksikliğin kendisiyle birlikte taşınır.
            "timer_beklenen": f"{taban}.timer",
            "kok": m.group("kok"),
            "ev": f'{m.group("kok")}/{m.group("bot")}',
        }
    return harita


def _profil(bot: str) -> dict:
    p = profiller()
    if bot not in p:
        raise SystemExit(f"[filo] {bot}: birim eşlemesi ÖLÇÜLEMEDİ — {BIRIM_DIZINI} altında "
                         f"HERMES_HOME'u bu profile bakan bir .service yok")
    return p[bot]


def _tamsayi(n) -> int:
    """Uzak programa GÖMÜLEN sayı. Dize kabul etmek bir enjeksiyon yüzeyidir."""
    v = int(n)
    if v <= 0:
        raise ValueError(f"satır sayısı pozitif olmalı: {n!r}")
    return v


# ─────────────────────────────────────────────────────────────────────────────
#  ssh sarmalı
# ─────────────────────────────────────────────────────────────────────────────

def varsayilan_host() -> str:
    """`kullanıcı@ip` — ÇAĞRI ANINDA okunur, modül yüklenirken DEĞİL: sabitlenmiş bir varsayılan
    ortam değişkenini görmezdi."""
    return (f"{os.environ.get(ENV_KULLANICI) or A1_KULLANICI_VARSAYILAN}"
            f"@{os.environ.get(ENV_IP) or A1_IP_VARSAYILAN}")


def varsayilan_anahtar() -> str:
    return os.environ.get(ENV_ANAHTAR) or A1_ANAHTAR_VARSAYILAN


def ssh_sarmali(uzak: str, *, host: str | None = None, anahtar: str | None = None) -> list[str]:
    """`argv` listesi — kabuk YOK (`shell=True` yok), yani yerelde hiçbir genişletme olmaz.

    `~` BURADA genişletilir: `ssh -i ~/...` argv'de tilde'yi kendi çözmez, dosyayı bulamaz ve
    etkileşimsiz koşumda parola sorup ASILIR.
    """
    return ["ssh", "-i", os.path.expanduser(anahtar or varsayilan_anahtar()),
            host or varsayilan_host(), uzak]


def _kos(argv: list[str], girdi: str | None = None) -> subprocess.CompletedProcess:
    """ALT SÜRECİN TEK KOŞTUĞU YER. Kurucuların hepsi saf kalır; çivi bunu AST ile ölçer."""
    return subprocess.run(argv, capture_output=True, text=True, input=girdi)


# ─────────────────────────────────────────────────────────────────────────────
#  durum
# ─────────────────────────────────────────────────────────────────────────────

def durum_birimleri() -> list[tuple[str, str]]:
    """`[(bot, birim), …]` — servis + timer, roster sırasında."""
    p = profiller()
    kayit: list[tuple[str, str]] = []
    for bot in botlar():
        if bot not in p:
            continue
        kayit.append((bot, p[bot]["birim"]))
        if p[bot]["timer"]:
            kayit.append((bot, p[bot]["timer"]))
    return kayit


def birimsiz_botlar() -> list[str]:
    p = profiller()
    return [b for b in botlar() if b not in p]


def eksik_timerlar(p: dict | None = None) -> list[tuple[str, str]]:
    """Servisi VAR ama timer'ı OLMAYAN botlar: `[(bot, beklenen_timer_adı), …]`.

    Bu satır tablodan DÜŞMEZ ve düşmemesi kuralın kendisidir: kadansı hiç açılmamış bir botun
    sessizliği, "boşken sessiz" davranışından AYIRT EDİLEMEZ (profil manifestlerinin ölçülmüş
    uyarısı). Eski hâlde en tehlikeli durum en GÖRÜNMEZ durumdu — satırın olmaması, sorunun
    olmaması gibi okunuyordu.

    `p` enjekte edilebilir ki çivi, bugünkü repoda var olmayan bir hâli ölçebilsin.
    """
    p = profiller() if p is None else p
    return [(bot, bilgi["timer_beklenen"]) for bot, bilgi in sorted(p.items())
            if not bilgi["timer"]]


def durum_komutu(kayitlar: list[tuple[str, str]]) -> str:
    """Tek uzak komut, salt-okuma. `sudo` YOK — `systemctl show` ayrıcalık istemez."""
    parca = []
    for _, birim in kayitlar:
        parca.append(
            f'echo {shlex.quote(f"{AYRAC} {birim}")}; systemctl show {shlex.quote(birim)}'
            " -p ActiveState -p SubState -p Result -p ExecMainStatus"
            " -p ExecMainStartTimestamp -p ExecMainExitTimestamp"
            " -p LastTriggerUSec -p NextElapseUSecRealtime")
    return "; ".join(parca)


def durum_ayristir(cikti: str) -> dict[str, dict[str, str]]:
    """`{birim: {alan: değer}}`. Bulunmayan alan sözlükte YOKTUR — 0/boş ile DOLDURULMAZ."""
    sonuc: dict[str, dict[str, str]] = {}
    simdiki: str | None = None
    for satir in cikti.splitlines():
        if satir.startswith(AYRAC + " "):
            simdiki = satir[len(AYRAC) + 1:].strip()
            sonuc.setdefault(simdiki, {})
        elif simdiki and "=" in satir:
            k, _, v = satir.partition("=")
            if v.strip():
                sonuc[simdiki][k.strip()] = v.strip()
    return sonuc


def durum_hukmu(kayitlar: list[tuple[str, str]],
                olculen: dict[str, dict[str, str]]) -> tuple[int, list[str]]:
    """`(rc, sorunlar)`. Ölçülemeyen birim YEŞİL SAYILMAZ: sessizlik "sorun yok" değildir."""
    sorun: list[str] = []
    for bot, birim in kayitlar:
        d = olculen.get(birim)
        if not d:
            sorun.append(f"{bot}/{birim}: ÖLÇÜLEMEDİ — systemctl bu birim için hiç konuşmadı")
            continue
        aktif = d.get("ActiveState")
        if aktif == "failed":
            sorun.append(f"{bot}/{birim}: ActiveState=failed")
        if birim.endswith(".timer") and aktif != "active":
            # Kapalı timer, "boşken sessiz" davranışından AYIRT EDİLEMEZ bir sessizlik üretir
            # (profil manifestlerinin ölçülmüş uyarısı).
            sorun.append(f"{bot}/{birim}: timer ActiveState={aktif or 'ÖLÇÜLEMEDİ'} (active değil)")
        r = d.get("Result")
        if r is not None and r != "success":
            sorun.append(f"{bot}/{birim}: Result={r}")
        s = d.get("ExecMainStatus")
        if s is not None and s != "0":
            sorun.append(f"{bot}/{birim}: ExecMainStatus={s}")
    return (1 if sorun else 0), sorun


def damga_notu(kayitlar: list[tuple[str, str]],
               olculen: dict[str, dict[str, str]]) -> str | None:
    """ÖLÇÜLDÜ 2026-08-31: A1 13:24'te yeniden başladı; birimler 09:29'da (reboot'tan ÖNCE)
    koştu ve systemd'nin çalışma-anı damgaları BOŞ döndü.

    Bu, `durum`un ölçülmüş KÖR NOKTASIDIR ve sessiz olmamalıdır: reboot'tan sonra HİÇ KOŞMAMIŞ
    bir birim ile BAŞARIYLA koşmuş bir birim `Result=success` + `ExecMainStatus=0` ile AYNI
    görünür. Tabloya bakan operatör "bugün koştu" diye okur. Gerçek son koşum kalıcı journal'da
    durur, bu yüzden not okuyucuyu ORAYA yollar.
    """
    kor = [f"{bot}/{birim}" for bot, birim in kayitlar
           if birim.endswith(".service")
           and not (olculen.get(birim) or {}).get("ExecMainExitTimestamp")]
    if not kor:
        return None
    return ("NOT — `son koşum` boş: systemd bu birimlerin çalışma-anı kaydını TUTMUYOR "
            "(tipik neden: makine yeniden başladı). `Result=success` + `ExecMainStatus=0` bu "
            "durumda HİÇ KOŞMAMIŞ birimde de görünür, yani tablo 'koştu' DEMİYOR. Gerçek son "
            f"koşum: ops/filo.py journal <bot>   ·   etkilenen: {', '.join(kor)}")


def _alan(d: dict, *adlar: str) -> str:
    for a in adlar:
        if d.get(a):
            return d[a]
    return "ÖLÇÜLEMEDİ"


def _durum_tablosu(kayitlar, olculen, eksikler=()) -> str:
    basliklar = ("bot", "birim", "aktif/alt", "Result", "Exec", "son koşum / sıradaki")
    satirlar = [basliklar]
    for bot, birim in kayitlar:
        d = olculen.get(birim) or {}
        satirlar.append((
            bot, birim,
            f'{_alan(d, "ActiveState")}/{_alan(d, "SubState")}',
            _alan(d, "Result"), _alan(d, "ExecMainStatus"),
            _alan(d, "ExecMainExitTimestamp", "NextElapseUSecRealtime", "LastTriggerUSec"),
        ))
    for bot, timer in eksikler:
        # Sorulmadı çünkü SORULACAK BİR ŞEY YOK — ve tam bu yüzden satır tabloda DURUR.
        satirlar.append((bot, timer, "BİRİM YOK", "ÖLÇÜLEMEDİ", "ÖLÇÜLEMEDİ",
                         "timer dosyası dağıtımda yok — kadans HİÇ açılmamış"))
    genislik = [max(len(s[i]) for s in satirlar) for i in range(len(basliklar))]
    ciz = ["  ".join(h.ljust(genislik[i]) for i, h in enumerate(satirlar[0])),
           "  ".join("-" * g for g in genislik)]
    ciz += ["  ".join(h.ljust(genislik[i]) for i, h in enumerate(s)) for s in satirlar[1:]]
    return "\n".join(ciz)


def durum_raporu(kayitlar, olculen, eksikler=(), ek_sorunlar=()) -> tuple[int, str]:
    """`(rc, basılacak_metin)` — SAF. CLI bunu yalnız BASAR.

    Tablo, kör-nokta notu ve hüküm tek yerde birleşir ki çivi CLI'ın gerçekten ne bastığını
    ölçebilsin; `_durum` içine gömülü bir yazım, ancak dize aramasıyla "ölçülebilir" olurdu ve
    o ölçüm yanlış sebeple yeşil kalırdı (bu turda bir kez oldu).
    """
    hukum, sorun = durum_hukmu(kayitlar, olculen)
    parca = [_durum_tablosu(kayitlar, olculen, eksikler)]
    if (not_ := damga_notu(kayitlar, olculen)):
        parca += ["", not_]
    for bot, timer in eksikler:
        sorun.append(f"{bot}/{timer}: BİRİM YOK — servisi var, timer'ı yok; kadans hiç açılmamış")
        hukum = 1
    for s in ek_sorunlar:
        sorun.append(s)
        hukum = 1
    parca += ["", "HÜKÜM: YEŞİL" if hukum == 0 else "HÜKÜM: KIRMIZI"]
    parca += [f"  · {s}" for s in sorun]
    return hukum, "\n".join(parca)


# ─────────────────────────────────────────────────────────────────────────────
#  journal
# ─────────────────────────────────────────────────────────────────────────────

def journal_komutu(bot: str, n: int) -> str:
    """ÖLÇÜLMÜŞ TUZAK (2026-08-23): `journalctl … | grep -q` eşleşince boruyu erken kapatır,
    journalctl SIGPIPE ile ölür ve çıktı YARIM gelir. Bu yüzden burada boru YOKTUR."""
    return f'journalctl -u {shlex.quote(_profil(bot)["birim"])} -n {_tamsayi(n)} --no-pager'


# ─────────────────────────────────────────────────────────────────────────────
#  oturumlar — uzak sqlite, SALT-OKUMA
# ─────────────────────────────────────────────────────────────────────────────

def oturumlar_programi(bot: str, n: int) -> str:
    """Uzak `python3 -c` programı.

    İKİ KISIT KODA GÖMÜLÜ:
      · TEK TIRNAK YOK. Program uzak kabuğa `python3 -c '<program>'` olarak gider; içindeki tek
        bir `'` sarmalı böler ve komut BAŞKA bir şey çalıştırır.
      · SALT ASCII. Uzak `python3` C-locale altında koşabilir; ASCII dışı bir `print` orada
        `UnicodeEncodeError` ile ölür ve bu YEREL tarafta "boş sonuç" gibi görünür.

    Defter SALT-OKUNUR açılır (`mode=ro`): bu dosyaya canlı hermes YAZAR.
    Şema (`sessions.id/model/started_at`) 2026-08-31'de canlı defterden ölçüldü.
    """
    say = _tamsayi(n)
    db = f'{_profil(bot)["ev"]}/state.db'
    return "\n".join([
        "import sqlite3,datetime",
        "def _iso(x):",
        "    try:",
        "        return datetime.datetime.fromtimestamp("
        "float(x),datetime.timezone.utc).isoformat(timespec=\"seconds\")",
        "    except Exception as e:",
        "        return \"ts-OLCULEMEDI(\"+type(e).__name__+\":\"+str(x)[:40]+\")\"",
        f"c=sqlite3.connect(\"file:{db}?mode=ro\",uri=True,timeout=2.0)",
        "for i,m,t in c.execute(\"SELECT id,model,started_at FROM sessions "
        f"ORDER BY started_at DESC, id DESC LIMIT {say}\").fetchall():",
        "    print(_iso(t),\"|\",(m or \"model-OLCULEMEDI\"),\"|\",i)",
    ])


def oturumlar_komutu(bot: str, n: int) -> str:
    prog = oturumlar_programi(bot, n)
    if "'" in prog:
        raise AssertionError("uzak program tek tırnak içeriyor — sarmal bölünür")
    return f"python3 -c '{prog}'"


# ─────────────────────────────────────────────────────────────────────────────
#  test-atesle — KOŞMAZ, BASAR
# ─────────────────────────────────────────────────────────────────────────────

def test_atesle_blogu(bot: str, *, host: str | None = None, anahtar: str | None = None) -> str:
    """Operatörün koşacağı TEK blok + koşum sonrası kanıt adımı.

    ARAÇ BUNU KOŞMAZ. Uzak `sudo` bu oturumların izin sınıfında engellidir; "denemek" bir
    arıza değil bir SESSİZLİK üretirdi (yarım komut, yorumlanamayan çıktı).
    """
    p = _profil(bot)
    # Anahtar BURADA genişletilmez (`ssh_sarmali`nin tersine) ve bu bilinçlidir: bu satırı
    # operatörün KABUĞU koşar, `~`ı o genişletir; genişletilmiş mutlak yol kopyala-yapıştır
    # bir satırı okunmaz yapardı.
    ssh = f"ssh -i {anahtar or varsayilan_anahtar()} {host or varsayilan_host()}"
    return "\n".join([
        f"# ── @{bot} TEST-ATEŞLEME — BU ARAÇ TARAFINDAN KOŞULMADI (uzak sudo engelli) ──",
        "# 1) ateşle (operatör koşar):",
        f'{ssh} \'sudo systemctl start {p["birim"]}\'',
        "",
        "# 2) kanıtı topla (bu araç kendi koşar, salt-okuma):",
        f"   .venv/bin/python ops/filo.py test-atesle {bot} --kanit",
        "",
        f"# NOT: birim {p['birim']} — @{bot} profilinin evi {p['ev']}. Eşleme birim dosyasının",
        "#      HERMES_HOME satırından TÜRETİLDİ, ezberden yazılmadı.",
    ])


def kanit_komutu(bot: str) -> str:
    """Koşum SONRASI salt-okuma doğrulama: systemctl üçlüsü + journal kesiti + defterin son
    oturumu. `sudo` YOK, `start`/`restart` YOK — bu adım hiçbir şeyi tetiklemez."""
    p = _profil(bot)
    return "; ".join([
        durum_komutu([(bot, p["birim"])]),
        f'echo "@@JOURNAL"',
        f'journalctl -u {shlex.quote(p["birim"])} -n 40 --no-pager',
        f'echo "@@OTURUM"',
        oturumlar_komutu(bot, 1),
    ])


# ─────────────────────────────────────────────────────────────────────────────
#  profil-guncelle — SAHTE BAŞARI TUZAĞI BURADA ÇÖZÜLÜR
# ─────────────────────────────────────────────────────────────────────────────

def profil_guncelle_komutu(bot: str) -> str:
    """tar-kopya → `printf` onaylı `--force-config` update → doğrulama grep'i (2026-08-31).

    `--force-config` ŞART: düz `hermes profile update <ad>` `config.yaml`ı KORUR, yani duruş
    ya da model değiştiyse canlıya HİÇ GİTMEZ (ölçülmüş tuzak, `deploy.sh` kaydı).
    `printf y |` ŞART: onaysız çağrı boş stdin'de iptal eder ve RC=0 döner.
    """
    p = _profil(bot)
    yedek = f'/home/ubuntu/backups/profil-{bot}-$(date -u +%Y%m%dT%H%M%SZ).tgz'
    # YEDEK BİR KAPIDIR, VAAT DEĞİL. Zincir `&&` ile bağlı: tar düşerse `hermes profile update`
    # HİÇ KOŞMAZ. Eskiden aralarında `;` vardı — yedek başarısızken güncelleme yine koşuyor ve
    # hüküm yeşil kalabiliyordu, yani geri alınamaz bir değişiklik yedeksiz yapılıyordu.
    # `|` önceliği `&&`den yüksektir, yani zincir `(mkdir && tar && echo) && (printf | hermes)`
    # olarak ayrışır — doğru olan da budur. `$?` ise her hâlükârda basılır (`;` ile ayrık).
    return "; ".join([
        f'mkdir -p /home/ubuntu/backups && tar czf {yedek} -C {p["kok"]} {bot} '
        f'&& echo "{TAR_ISARETI}" '
        f'&& printf "y\\n" | hermes profile update {bot} --force-config',
        f'echo "{RC_ISARETI} $?"',
        f'echo "{DOGRULAMA_ISARETI}"',
        f'grep -nE "^  (provider|default|max_tokens):" {p["ev"]}/config.yaml',
    ])


def uzak_rc(cikti: str) -> int | None:
    """`@@RC <n>` işaretinden uzak komutun GERÇEK çıkış kodu. ssh'ın kendi RC'si burada
    yanıltıcıdır: uzak komut bir zincirdir ve son halkası `echo`dur (hep 0)."""
    for satir in cikti.splitlines():
        if satir.startswith(RC_ISARETI + " "):
            try:
                return int(satir[len(RC_ISARETI) + 1:].strip())
            except ValueError:
                # sessiz-yutma: uzak kabuk RC yerine anlamsız bir şey bastı; None dönmek
                # "ölçülemedi" der ve hüküm kırmızıya düşer — 0 varsaymak SAHTE BAŞARI olurdu
                return None
    return None


def guncelleme_hukmu(cikti: str, rc: int | None) -> tuple[bool, str]:
    """ARACIN KALBİ: hüküm RC'DEN DEĞİL ÇIKTIDAN verilir.

    Sıra bilinçlidir. İptal kontrolü ÖNCE gelir; çünkü iptal edilmiş bir koşumun çıktısında
    başarı dizgesi de zaten yoktur — ikinci kontrol onu YAKALAR ama "dizge yok" der. O teşhis
    bir sonraki adımı hiçbir yere götürmez: operatör hermes'in dizgeyi değiştirdiğini sanır,
    oysa ölçülen şey ONAYIN VERİLMEDİĞİDİR.
    """
    if IPTAL_IZI in cikti.lower():
        return False, (f"SAHTE BAŞARI: çıktı İPTAL diyor ({IPTAL_IZI!r}) ama uzak RC={rc}. "
                       "RC'ye bakan operatör güncellemeyi YAPILMIŞ sanardı; canlı profil ESKİ.")
    if TAR_ISARETI not in cikti:
        # İptalden SONRA, başarı dizgesinden ÖNCE. Sonra olsaydı yedeksiz bir koşum "dizge yok"
        # diye teşhis edilirdi ve operatör hermes'i suçlardı; oysa ölçülen şey YEDEĞİN
        # ALINAMADIĞIDIR ve zincir bu yüzden hiç ilerlememiştir.
        return False, (f"YEDEK ALINAMADI ({TAR_ISARETI!r} işareti yok) — tar düştüğü için "
                       "güncelleme zinciri koşmadı. Yedeksiz güncelleme GERİ ALINAMAZ.")
    if rc is None:
        return False, (f"uzak çıkış kodu ÖLÇÜLEMEDİ ({RC_ISARETI} işareti yok) — ssh'ın kendi "
                       "RC'si bu zincirde hep 0'dır, ona güvenmek sahte başarıdır")
    if BASARI_DIZGESI not in cikti:
        return False, (f"başarı dizgesi ({BASARI_DIZGESI!r}) çıktıda YOK — güncelleme "
                       "DOĞRULANAMADI (hermes dizgeyi değiştirmiş de olabilir; ham çıktı yukarıda)")
    if rc != 0:
        return False, (f"başarı dizgesi VAR ama uzak RC={rc} — iki tanık ÇELİŞİYOR, "
                       "yeşil sayılmaz")
    return True, f"doğrulandı: {TAR_ISARETI!r} + {BASARI_DIZGESI!r} + uzak RC=0"


def canli_model_varsayilani(dogrulama_ciktisi: str) -> str | None:
    """Doğrulama grep'inin `default:` DEĞERİ. Bulunamazsa `None` — "aynı" DEMEZ.

    Neden ayrıştırılıp EŞİTLİKLE kıyaslanıyor: alt-dizge kıyası (`beklenen in canli`) ÖNEK
    vakasında sahte-aynılık verir. `opus-4-1` beklenirken canlı `opus-4-1-ultra` ise alt-dizge
    "AYNI" der — ve bu tam da bugünkü Ultra-geçişinin sınıfıdır (aynı ad, uzatılmış sürüm).
    """
    m = re.search(r"^\s*(?:\d+:)?\s*default:\s*(\S+)\s*$", dogrulama_ciktisi, re.M)
    return m.group(1) if m else None


def repo_model_varsayilani(bot: str) -> str | None:
    """Repo'daki `config.yaml`ın `model.default`ı — canlıyla KIYAS için. Okunamazsa `None`."""
    yol = PROFIL_DIZINI / bot / "config.yaml"
    try:
        icerik = yol.read_text(encoding="utf-8")
    except OSError:
        # sessiz-yutma: repo config'i okunamadı; kıyas YAPILMAZ ve bu açıkça basılır —
        # istisnayı yukarı taşımak güncellemenin kendi hükmünü de yok ederdi
        return None
    m = re.search(r"^model:\s*$.*?^\s+default:\s*(?P<v>\S+)\s*$", icerik, re.M | re.S)
    return m.group("v") if m else None


# ─────────────────────────────────────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────────────────────────────────────

def _arg_pozitif(ham: str) -> int:
    """argparse `type=` — hatayı KULLANIM HATASI sınıfına sokar (argparse exit 2 + tek satır).

    Doğrulama BURADA, ayrıştırma anında yapılır: `_tamsayi`nin `ValueError`ı komut koşarken
    patlasaydı operatör ham bir traceback + exit 1 görürdü, yani beyan edilen "2=kullanım
    hatası" sözleşmesi tutmazdı ve arıza "araç çöktü" diye okunurdu.
    """
    try:
        return _tamsayi(ham)
    except (ValueError, TypeError) as e:
        raise argparse.ArgumentTypeError(str(e)) from e


SON_SOZ = ("çıkış kodları: 0=başarı · 1=doğrulama kırmızısı · 2=kullanım hatası\n"
           "not: `test-atesle` uzak sudo KOŞMAZ, bloğu basar. `profil-guncelle` bayraksız KURUdur.")


def _ssh_kos(uzak: str, a) -> tuple[int, str, str] | None:
    """`--komut-yaz` ise komutu basar ve `None` döner (koşum YOK)."""
    argv = ssh_sarmali(uzak, host=a.host, anahtar=a.anahtar)
    if a.komut_yaz:
        print(shlex.join(argv))
        return None
    p = _kos(argv)
    return p.returncode, p.stdout, p.stderr


def _durum(a) -> int:
    kayit = durum_birimleri()
    sonuc = _ssh_kos(durum_komutu(kayit), a)
    if sonuc is None:
        return 0
    rc, cikti, hata = sonuc
    ek = [f"{b}: roster'da VAR ama systemd birimi YOK — dağıtım boşluğu"
          for b in birimsiz_botlar()]
    if rc != 0:
        ek.insert(0, f"ssh RC={rc}: {hata.strip() or 'stderr boş'}")
    hukum, metin = durum_raporu(kayit, durum_ayristir(cikti), eksik_timerlar(), ek)
    print(metin)
    return hukum


def _journal(a) -> int:
    sonuc = _ssh_kos(journal_komutu(a.bot, a.satir), a)
    if sonuc is None:
        return 0
    rc, cikti, hata = sonuc
    print(cikti, end="")
    if rc != 0:
        print(f"[filo] journal ÖLÇÜLEMEDİ (ssh RC={rc}): {hata.strip()}", file=sys.stderr)
        return 1
    return 0


def _oturumlar(a) -> int:
    sonuc = _ssh_kos(oturumlar_komutu(a.bot, a.satir), a)
    if sonuc is None:
        return 0
    rc, cikti, hata = sonuc
    print(cikti, end="")
    if rc != 0:
        print(f"[filo] oturum defteri ÖLÇÜLEMEDİ (ssh RC={rc}): {hata.strip()}", file=sys.stderr)
        return 1
    if not cikti.strip():
        print(f"[filo] {a.bot}: defter okundu ama HİÇ OTURUM YOK — bu, 'ölçülemedi' DEĞİL")
    return 0


def _test_atesle(a) -> int:
    if not a.kanit:
        print(test_atesle_blogu(a.bot, host=a.host, anahtar=a.anahtar))
        return 0
    sonuc = _ssh_kos(kanit_komutu(a.bot), a)
    if sonuc is None:
        return 0
    rc, cikti, hata = sonuc
    print(cikti, end="")
    birim = _profil(a.bot)["birim"]
    hukum, sorun = durum_hukmu([(a.bot, birim)], durum_ayristir(cikti))
    if rc != 0:
        sorun.insert(0, f"ssh RC={rc}: {hata.strip() or 'stderr boş'}")
        hukum = 1
    print()
    print("KANIT: YEŞİL" if hukum == 0 else "KANIT: KIRMIZI")
    for s in sorun:
        print(f"  · {s}")
    return hukum


def _profil_guncelle(a) -> int:
    uzak = profil_guncelle_komutu(a.bot)
    beklenen = repo_model_varsayilani(a.bot)
    if not a.uygula:
        print(f"# ── @{a.bot} PROFİL GÜNCELLEME — KURU (koşulmadı) ──")
        print(shlex.join(ssh_sarmali(uzak, host=a.host, anahtar=a.anahtar)))
        print()
        print(f"# repo model.default: {beklenen or 'ÖLÇÜLEMEDİ'}")
        print("# koşmak için: aynı komuta --uygula ekle "
              "(canlı profili DEĞİŞTİRİR; tar kopyası önce alınır)")
        return 0
    # BU DAL DA `_ssh_kos`TAN GEÇER — diğer dördü gibi. Eskiden `_kos`u DOĞRUDAN çağırıyordu ve
    # `--komut-yaz` burada SESSİZCE YOK SAYILIYORDU: önizleme bekleyen operatör canlı profili
    # değiştiriyordu (inceleme, düzeltme turu 1). Etkisiz kalan bayrak GÜVENLİK bayrağıydı, yani
    # 18-çivi vakasının ters ve daha tehlikeli yönü.
    sonuc = _ssh_kos(uzak, a)
    if sonuc is None:
        return 0
    rc_ssh, cikti, hata = sonuc
    print(cikti, end="")
    if hata.strip():
        print(hata, end="", file=sys.stderr)
    ok, neden = guncelleme_hukmu(cikti, uzak_rc(cikti))
    if rc_ssh != 0:
        # Zincirin son halkası `echo`dur, yani ssh RC'si normalde 0'dır. 0 DEĞİLSE ssh'ın KENDİSİ
        # düşmüştür (255 = bağlanamadı) ve bu bilgi hükümden AYRI taşınır.
        ok, neden = False, f"ssh'ın KENDİSİ düştü (RC={rc_ssh}) — uzak komut hiç koşmamış olabilir"
    print()
    print(f"HÜKÜM: {'YEŞİL' if ok else 'KIRMIZI'} — {neden}")
    canli = (canli_model_varsayilani(cikti.split(DOGRULAMA_ISARETI, 1)[1])
             if DOGRULAMA_ISARETI in cikti else None)
    if beklenen and canli:
        # EŞİTLİK, alt-dizge DEĞİL: `in` kıyası `opus-4-1` beklerken canlı `opus-4-1-ultra`
        # olduğunda "AYNI" derdi — sahte aynılık (dal-sonu incelemesi Important-2).
        if canli == beklenen:
            print(f"  · model.default canlıda repo ile AYNI: {beklenen}")
        else:
            print(f"  · model.default AYRIŞTI — repo: {beklenen}; canlı: {canli}")
            ok = False
    else:
        print(f"  · model kıyası YAPILMADI (repo: {beklenen or 'ÖLÇÜLEMEDİ'}; "
              f"canlı: {canli or 'ÖLÇÜLEMEDİ'})")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="filo.py", description=__doc__.splitlines()[0], epilog=SON_SOZ,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ortak = argparse.ArgumentParser(add_help=False)
    # VARSAYILAN `None`: çözüm `ssh_sarmali`de, ÇAĞRI ANINDA yapılır. Burada bir değer koymak
    # ortam değişkenini ayrıştırma anında dondururdu ve "CLI > env > sabit" sırası bozulurdu.
    ortak.add_argument("--host", default=None,
                       help=f"ssh hedefi (env {ENV_KULLANICI}/{ENV_IP}; "
                            f"şu an: {varsayilan_host()})")
    ortak.add_argument("--anahtar", default=None,
                       help=f"ssh özel anahtarı (env {ENV_ANAHTAR}; şu an: {varsayilan_anahtar()})")
    ortak.add_argument("--komut-yaz", dest="komut_yaz", action="store_true",
                       help="kurulan ssh komutunu BAS, KOŞMA")
    alt = ap.add_subparsers(dest="komut", required=True)

    alt.add_parser("durum", parents=[ortak],
                   help="üç bot birimi + timer + son koşum sonuçları tek tabloda (salt-okuma)")

    j = alt.add_parser("journal", parents=[ortak], help="son koşum journal kesiti")
    j.add_argument("bot", choices=botlar())
    j.add_argument("-n", "--satir", type=_arg_pozitif, default=40,
                   help="satır sayısı, pozitif (varsayılan 40)")

    o = alt.add_parser("oturumlar", parents=[ortak],
                       help="state.db'den son oturum/model listesi (uzak, SALT-OKUMA)")
    o.add_argument("bot", choices=botlar())
    o.add_argument("-n", "--satir", type=_arg_pozitif, default=10,
                   help="oturum sayısı, pozitif (varsayılan 10)")

    t = alt.add_parser("test-atesle", parents=[ortak],
                       help="ateşleme bloğunu BASAR (koşmaz); --kanit koşum sonrası doğrular")
    t.add_argument("bot", choices=botlar())
    t.add_argument("--kanit", action="store_true",
                   help="ateşlemeden SONRA salt-okuma doğrulamayı koş")

    g = alt.add_parser("profil-guncelle", parents=[ortak],
                       help="tar-kopya + onaylı --force-config update + doğrulama (kuru)")
    g.add_argument("bot", choices=botlar())
    g.add_argument("--uygula", action="store_true", help="KOŞ (canlı profili değiştirir)")

    a = ap.parse_args(argv)
    try:
        return {"durum": _durum, "journal": _journal, "oturumlar": _oturumlar,
                "test-atesle": _test_atesle, "profil-guncelle": _profil_guncelle}[a.komut](a)
    except (ValueError, TypeError) as e:
        # SAVUNMA KATMANI. `_arg_pozitif` bugün tek girdi yolunu kapatıyor; yarın `_tamsayi`ye
        # başka bir yoldan geçilirse operatör yine KULLANIM HATASI görmeli, ham traceback değil.
        print(f"filo.py: kullanım hatası — {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
