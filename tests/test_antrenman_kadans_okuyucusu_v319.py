"""ESKİ PANO ANTRENMAN KARTI: SABİT SAYI + UYDURMA DURUM · v319

VAKA (2026-08-26, operatör, ekran görüntüsüyle): "eski panodan bakınca düşün pasifte duruyor,
antrenmanı da otomatiğe almış olmamız lazımdı, bütçeyi ve k_max'ı otomatik ayarlayıp."

ÖLÇÜLDÜ — OPERATÖR HAKLI AMA KUSUR SANDIĞI YERDE DEĞİL. Motor ZATEN tam otomatik:
`sprint.auto_config()` bütçeyi/k_max'ı makineden türetir, `sprint.should_run()` her poll'de
adlı bir sebep üretir ve `analytics.learning_scorecard()` ikisini de yüke koyar. Canlı ölçüm
(`/api/hermes` → `learning.besleme.antrenman_sprinti`, 2026-08-26):

    {"kos": false, "sebep": "tetik_yok(gun=4<7, taze=0<5)", "gecen_gun": 4, "taze_hipotez": 0,
     "cfg": {"cekirdek": 4, "isci": 2, "budget": 6, "budget_kaynagi": "turetim",
             "k_max": 2, "k_max_kaynagi": "turetim", "formul": "isci = max(2, min(4, …"},
     "tetik": {"haftalik_gun": 7, "taze_hipotez_esigi": 5, "gece_dilimi": [22, 6]}}

Yani ihtiyaç duyulan HER ŞEY yükte. YENİ PANO (`ui/src/pano/…/antrenman/Sprint.tsx`) bu yolu
DOĞRU okuyor. Kusurun tamamı ESKİ panodadır (`meridian/web/app.js` → `eylemSeridi`), ve
`eylemSeridi(d)` o yükü PARAMETRE OLARAK ALIYOR — veri elinin altında, okumuyor:

  (1) SABİT SAYI — `value="12"` / `value="3"`. Bunlar geliştirme makinesinin (8 çekirdek)
      türetimidir; canlı A1 4 çekirdek → 6/2. Yani ekran YANLIŞ sayı gösteriyor. Dahası
      "Antrenmanı başlat"a basılırsa canlıya `{budget:12, k_max:3}` POST'lanır ve türetilmiş
      yapılandırmayı EZER — pano, motorun otomatiğini elle bozan bir kola dönüşür.
      UYDURMA YASAĞI: ölçülmemiş bir sayıyı ölçülmüş gibi göstermek.
  (2) UYDURMA DURUM — `sp.active` yoksa "kapalı". Sprint'in aktif OLMAMASI NORMAL hâldir
      (gecede en fazla bir kez koşar). "kapalı" açılabilecek bir kapı ima eder; gerçek hâl
      "kadans bekliyor, sebebi şu"dur. BEDELİ ÖLÇÜLDÜ: operatör bu ekrana bakıp sprint'in
      duraklatıldığına inandı ve "bir sonraki dağıtımda tekrar aktif hale getirelim" dedi —
      oysa kadans hiç durmamıştı. Yanlış bir kelime, yanlış bir iş kalemi doğurdu.
  (3) "PASİF" NEYİN PASİFİ SÖYLENMİYOR — `s.active` hermes'in ELLE döngüsüdür ve canlıda
      `MERIDIAN_AUTOSTART_HERMES=0` ile BİLEREK kapalıdır. Cümle teknik olarak doğru, ama
      operatör onu "beyin çalışmıyor" diye okuyor. Doğru olan, neyin kapalı olduğunu yazmaktır.

KAPSAM DAR: bu çivi MOTORA dokunmaz (motor zaten doğru) ve YENİ PANOYA dokunmaz (o zaten
dürüst). Yalnız eski okuyucuyu yükte duran gerçeğe bağlar.
"""
from __future__ import annotations

import pathlib
import re

KOK = pathlib.Path(__file__).resolve().parents[1]
APP = KOK / "meridian/web/app.js"
YENI_PANO = KOK / "ui/src/pano/yuzeyler/antrenman/Sprint.tsx"

#: Yükteki kanonik yol — İKİ okuyucu da BUNU okumalı, yoksa "tek kaynak" iddiası çöker.
KADANS_YOLU = ("learning", "besleme", "antrenman_sprinti")


def _src() -> str:
    return APP.read_text(encoding="utf-8")


def _eylem_seridi() -> str:
    """`eylemSeridi` gövdesini döndürür. BLOK BAZINDA ölçüm ZORUNLU: `value="12"` gibi bir
    dize dosyanın başka yerinde masum olarak geçebilir ve düz `in src` araması hem yanlış
    pozitif hem yanlış negatif verir (alt-dize tuzağı, bu turda beş kez yakalandı)."""
    s = _src()
    i = s.index("function eylemSeridi(")
    # Bir sonraki üst-seviye `function` bildirimine kadar.
    j = s.find("\nfunction ", i + 1)
    return s[i: j if j != -1 else len(s)]


def _input_etiketi(eid: str) -> str:
    blok = _eylem_seridi()
    m = re.search(rf'<input\s+id="{re.escape(eid)}"[^>]*>', blok)
    assert m, f'`{eid}` input etiketi `eylemSeridi` içinde bulunamadı'
    return m.group(0)


# ------------------------------------------------------- (1) SABİT SAYI GİTTİ

def test_butce_input_degeri_SABIT_SAYI_DEGIL():
    """ASIL ÇİVİ. `value` bir SAYI LİTERALİ olamaz — türetilmiş değere bağlanmalı."""
    etiket = _input_etiketi("sprint-budget")
    m = re.search(r'value="([^"]*)"', etiket)
    assert m, f"`value` niteliği yok: {etiket}"
    assert not re.fullmatch(r"\s*\d+\s*", m.group(1)), (
        f"bütçe hâlâ SABİT yazılı (`value=\"{m.group(1)}\"`) — canlı A1'de türetim 6, bu ekran "
        f"geliştirme makinesinin 12'sini gösteriyor ve başlat'a basılırsa canlıya onu POST'lar")
    assert "${" in m.group(1), f"`value` bir ifadeye bağlanmamış: {m.group(1)!r}"


def test_kmax_input_degeri_SABIT_SAYI_DEGIL():
    etiket = _input_etiketi("sprint-kmax")
    m = re.search(r'value="([^"]*)"', etiket)
    assert m, f"`value` niteliği yok: {etiket}"
    assert not re.fullmatch(r"\s*\d+\s*", m.group(1)), (
        f"k_max hâlâ SABİT yazılı (`value=\"{m.group(1)}\"`) — canlı türetim 2")
    assert "${" in m.group(1), f"`value` bir ifadeye bağlanmamış: {m.group(1)!r}"


def _sprint_start_govdesi() -> str:
    """`window.sprintStart` gövdesi. ÇIPA KOD ŞEKLİNE DEĞİL ADA BAĞLI: ilk sürümde çivi
    `const budget = … k_max = …;` desenini arıyordu ve düzeltme o satırı yeniden yazınca
    çivi "gönderim satırı bulunamadı" diye düştü — yani kendi düzeltmesini kırdı. Bir çivi
    KUSURU ölçmeli, kusurun bugünkü YAZILIŞINI değil."""
    s = _src()
    i = s.index("window.sprintStart")
    j = s.index("window.sprintStop", i)
    return _serhsiz(s[i:j])


def _serhsiz(kod: str) -> str:
    """`//` satır şerhlerini söker. ZORUNLU, SÜS DEĞİL: bu çivi ilk yazıldığında `|| 3`
    yasağını KENDİ DÜZELTMEMİN ŞERHİNDE yakaladı — şerh eski kodu ANLATIYORDU ("eskiden
    burada `|| 12` ve `|| 3` yedekleri vardı"). Yani doğru düzeltilmiş bir dosya, yalnızca
    neyi düzelttiğini yazdığı için kırmızı veriyordu. Bir çivi KODU ölçmeli; şerh, kodun
    tarihçesini taşır ve o tarihçe yasak deseni içerebilir — içermeli de.
    SINIR: satır-içi `//` yalnız satır başı/boşluk sonrası sökülür, yani `"http://"` gibi
    dizeler korunur. Blok şerh (`/* */`) bu gövdede yok, o yüzden ele alınmıyor."""
    import re as _re
    return "\n".join(_re.sub(r'(^|\s)//.*$', r'\1', satir) for satir in kod.split("\n"))


def test_POST_UYDURMA_YEDEK_SAYI_gondermiyor():
    """İkinci sabit sayı yuvası: gönderim yolundaki `|| 12` / `|| 3` yedekleri. Input
    düzeltilip burası unutulursa, alan boşaltıldığı anda yine uydurma sayı gider."""
    g = _sprint_start_govdesi()
    for desen, ad in ((r'\|\|\s*12\b', "|| 12"), (r'\|\|\s*3\b', "|| 3")):
        assert not re.search(desen, g), (
            f"gönderim yolunda sabit yedek var ({ad}) — alan boşken canlıya ölçülmemiş sayı gider")


def test_BOS_alan_govdeden_DUSUYOR():
    """ASIL DAVRANIŞ: boş alan "sen karar ver" demektir. Alan gövdeye KOŞULLU eklenmeli;
    koşulsuz `{budget, k_max}` göndermek, boş alanı `NaN`/`0` olarak canlıya taşırdı."""
    g = _sprint_start_govdesi()
    assert re.search(r'JSON\.stringify\(\s*\{\s*budget\s*,', g) is None, (
        "gövde hâlâ koşulsuz `{budget, k_max}` gönderiyor — boş alan uydurma değere dönüşür")
    assert re.search(r'if\s*\(.*\)\s*\w+\.(budget|k_max)\s*=', g), (
        "alanlar gövdeye KOŞULLU eklenmiyor — boş bırakma yolu yok, yani 'otomatik' seçilemez")


# --------------------------------------------- (2) "KAPALI" UYDURMASI GİTTİ

def test_KAPALI_uydurmasi_gitti():
    """`kapalı` açılabilir bir kapı ima eder; sprint'in aktif olmaması NORMALDİR."""
    blok = _eylem_seridi()
    m = re.search(r'const antDurum\s*=(.*?);\n', blok, re.S)
    assert m, "`antDurum` bulunamadı"
    assert '"kapalı"' not in m.group(1), (
        "antrenman durumu hâlâ 'kapalı' diyor — operatörü sprint'in duraklatıldığına inandıran "
        "cümle bu (2026-08-26 vakası: hiç durmamış bir kadans için 'tekrar aktif edelim' iş "
        "kalemi doğdu)")


def test_antrenman_durumu_KADANS_SEBEBINI_okuyor():
    """Doğru cümlenin kaynağı `sebep` alanıdır — 'tetik_yok(gun=4<7, taze=0<5)' gibi."""
    blok = _eylem_seridi()
    assert re.search(r'\.sebep\b', blok), (
        "kadans `sebep` alanı hiç okunmuyor — durum satırı yükte duran gerçeği görmezden geliyor")


def test_kadans_yolu_TAM_okunuyor():
    """Yol BİREBİR `learning.besleme.antrenman_sprinti` olmalı. Yanlış derinlikte okumak
    sessizce `undefined` verir ve kart 'ölçülemedi'ye düşer — yani düzeltme görünmez biçimde
    hiç çalışmaz (canlı ölçümle sabitlenen yol)."""
    blok = _eylem_seridi()
    for alan in KADANS_YOLU:
        assert alan in blok, f"kadans yolunun `{alan}` bacağı `eylemSeridi` içinde yok"


# ----------------------------------------- (3) ÖLÇÜLEMEDİĞİNDE UYDURMA YOK

def test_kadans_OLCULEMEDIGINDE_UYDURMUYOR():
    """UYDURMA YASAĞI: `antrenman_sprinti` null gelebilir (analytics o hâli açıkça üretir).
    O zaman kart 'kapalı' ya da bir sayı UYDURMAMALI — ölçülemediğini söylemeli."""
    blok = _eylem_seridi()
    m = re.search(r'const antDurum\s*=(.*?);\n', blok, re.S)
    assert m, "`antDurum` bulunamadı"
    assert re.search(r'ölçülemedi|ölçülmedi', m.group(1)), (
        "kadans okunamadığında söylenecek dürüst cümle yok — sessizce bir hâl uydurulur")


def test_butce_KAYNAGI_ekranda_yaziyor():
    """`budget_kaynagi` 'turetim' | 'env:…' olabilir. Operatör 6'nın NEREDEN geldiğini
    görmeden 'otomatik mi, biri elle mi koydu?' sorusunu cevaplayamaz."""
    blok = _eylem_seridi()
    assert "budget_kaynagi" in blok or "kaynagi" in blok, (
        "bütçenin kaynağı (türetim mi env override mı) ekranda yok — sayı görünür, "
        "otoritesi görünmez")


# ------------------------------------------- (4) "PASİF" NEYİN PASİFİ SÖYLENİYOR

def test_PASIF_neyin_pasif_oldugunu_soyluyor():
    """`s.active` hermes'in ELLE döngüsüdür; canlıda MERIDIAN_AUTOSTART_HERMES=0 ile bilerek
    kapalıdır. Çıplak 'pasif' operatöre 'beyin çalışmıyor' dedirtiyor."""
    blok = _eylem_seridi()
    m = re.search(r'const dusunDurum\s*=(.*?);\n', blok, re.S)
    assert m, "`dusunDurum` bulunamadı"
    ifade = m.group(1)
    assert not re.search(r':\s*"pasif"', ifade), (
        f"durum hâlâ çıplak 'pasif' — neyin pasif olduğu söylenmiyor:\n{ifade}")


# ------------------------------------------------ (5) İKİ OKUYUCU AYRIŞMASIN

def test_YENI_PANO_AYNI_YOLU_okuyor():
    """Tek kaynak çivisi: yeni pano bu yolu zaten okuyor. Biri yolu değiştirirse diğeri
    sessizce 'ölçülemedi'ye düşer — ayrışmayı BURADA yakala."""
    yeni = YENI_PANO.read_text(encoding="utf-8")
    assert "besleme" in yeni and "antrenman_sprinti" in yeni, (
        "yeni pano artık bu yolu okumuyor — iki okuyucu ayrışmış, kanonik yol kaymış olabilir")


# ============================================================================================
# (6) MOTOR TARAFI — ELLE BAŞLATMA DA TÜRETİMİ GÖRMELİ
# --------------------------------------------------------------------------------------------
# BU ÇİVİ PANO TURUNDA DOĞDU AMA PANODA DEĞİL. Kusuru ararken ölçüldü:
#     sprint.py::start →  conf = {"k_max": int(cfg.get("k_max", 3)),
#                                 "budget": int(cfg.get("budget", 12))}
# Yani AYNI MAKİNEDE iki farklı bütçe yürürlükte:
#     kadans yolu  →  maybe_start() → start(auto_config())      → canlı A1'de 6/2  (türetim)
#     elle yol     →  start({}) ya da eksik alanlı cfg           → 12/3            (SABİT)
# 12 ve 3, sekiz çekirdekli bir geliştirme makinesinin türetimidir; canlı A1 dört çekirdek.
# Operatör "Antrenmanı başlat"a bastığında makinenin kaldıramayacağı bir yükle koşuluyordu ve
# hiçbir yerde bu YAZMIYORDU — `auto_config`in "çipa dürüstlüğü" şerhi (o makinede formül
# birebir 12/3 üretir) tam da bu iki sayının nereden geldiğini açıklar.
# DOĞRU DAVRANIŞ: cfg'de alan YOKSA türetim kullanılır; VARSA operatör override'ı kazanır
# (`auto_config`in env override sözleşmesiyle aynı ruh).
from meridian import sprint as _sprint  # noqa: E402


def test_start_VARSAYILANI_SABIT_DEGIL_TURETIM():
    """ASIL MOTOR ÇİVİSİ: `start()`in varsayılanı `auto_config()`ten gelmeli."""
    import inspect
    src = inspect.getsource(_sprint.start)
    m = re.search(r'conf\s*=\s*\{[^}]*\}', src)
    assert m, "`conf` sözlüğü `start()` içinde bulunamadı"
    conf_satiri = m.group(0)
    assert not re.search(r'get\(\s*"k_max"\s*,\s*\d+\s*\)', conf_satiri), (
        f"elle başlatma k_max'ı SABİT sayıya düşüyor — kadans türetimi (canlıda 2) ile ayrışır:"
        f"\n{conf_satiri}")
    assert not re.search(r'get\(\s*"budget"\s*,\s*\d+\s*\)', conf_satiri), (
        f"elle başlatma bütçesi SABİT sayıya düşüyor — kadans türetimi (canlıda 6) ile ayrışır:"
        f"\n{conf_satiri}")


def _conf_yakala(monkeypatch, cfg):
    """`start(cfg)`in ÜRETTİĞİ conf'u döndürür — HİÇBİR SÜREÇ DOĞURMADAN.

    NEDEN `_systemd_baslat` SAHTE BİR **PID** DÖNDÜRÜYOR (None DEĞİL): `start()` None görünce
    `Popen` yedek yoluna DÜŞER ve GERÇEKTEN çocuk doğurur. Bu çivi ilk yazıldığında tam olarak
    o oldu: `_popen_baslat` diye VAR OLMAYAN bir ada `raising=False` ile yama konmuştu, yama
    sessizce hiçbir şey yapmadı ve test 4 işçilik gerçek bir antrenman başlattı — gerçek
    `state/`e kum havuzu açtı ve `state/sprint_status.json`u EZDİ. Sahte pid, systemd dalını
    seçtirir ve doğurma yoluna HİÇ girilmez. `sandbox_state` ikinci savunmadır: yazımlar tmp'ye
    gider. İki savunma da GEREKLİDİR ve ikisi AYRI şeyi korur (biri süreci, diğeri diski)."""
    yakalanan = {}

    def _sahte_systemd(sid, sbroot, ortam):
        yakalanan["conf"] = ortam.get("MERIDIAN_SPRINT_CONF")
        return 999999, "sinama", ""          # pid NOT-None → systemd dalı → doğurma YOK

    monkeypatch.setattr(_sprint, "_systemd_baslat", _sahte_systemd)
    _sprint.start(cfg)
    assert "conf" in yakalanan, "conf hiç üretilmedi — çivi ölçemedi (start erken döndü mü?)"
    import json as _json
    return _json.loads(yakalanan["conf"])


def test_HICBIR_SUREC_DOGMADI_civisi(sandbox_state, monkeypatch):
    """META-ÇİVİ: yukarıdaki iki çivi kazayla süreç doğurursa BU çivi bağırır. Çivinin
    kendisinin güvenliğini ölçen bir çivi — çünkü ilk sürümü tam da bunu yaptı."""
    import subprocess
    cagrildi = []
    monkeypatch.setattr(subprocess, "Popen",
                        lambda *a, **k: cagrildi.append(a) or (_ for _ in ()).throw(
                            AssertionError("TEST SÜREÇ DOĞURDU — kum havuzu/CPU kazası")))
    _conf_yakala(monkeypatch, {})
    assert not cagrildi, "subprocess.Popen çağrıldı — doğurma yolu kapatılmamış"


def test_bos_cfg_TURETILMIS_degeri_kullanir(sandbox_state, monkeypatch):
    """DAVRANIŞ ÇİVİSİ: `start({})` türetilmiş conf üretmeli, sabit 12/3 değil.

    İŞÇİ SAYISI ZORLA 2'YE SABİTLENİR — VE BU ÇİVİNİN YARISIDIR. `auto_config` bu depoda
    "çipa dürüst"tür: SEKİZ çekirdekli bir makinede formül birebir budget=12, k_max=3 üretir,
    yani tam olarak eski SABİT değerler. Zorlamasaydık çivi geliştirme makinesinde SAHTE
    YEŞİL verirdi (türetim = sabit, ayrım ölçülemez) ve yalnız dört çekirdekli canlıda
    kırmızıya dönerdi. Rastlantı yüzünden geçen bir test hiçbir şey kanıtlamaz — bu tuzağa
    çivi yazılırken bir kez düşüldü ve buradaki iki satır onun kalıcı panzehiri.
    2 işçi → budget=6, k_max=2 (canlı A1 ile aynı) — sabitlerden AYRIŞIR."""
    monkeypatch.setattr(_sprint, "_workers", lambda: 2)
    beklenen = _sprint.auto_config()
    assert (beklenen["budget"], beklenen["k_max"]) != (12, 3), (
        "türetim hâlâ eski sabitlerle aynı — çivi ayrımı ölçemez, zorlama işe yaramamış")
    conf = _conf_yakala(monkeypatch, {})
    assert conf["budget"] == beklenen["budget"], (
        f"boş cfg türetimi kullanmadı: conf={conf}, türetim budget={beklenen['budget']}")
    assert conf["k_max"] == beklenen["k_max"], (
        f"boş cfg türetimi kullanmadı: conf={conf}, türetim k_max={beklenen['k_max']}")


def test_ACIK_cfg_HALA_kazanir(sandbox_state, monkeypatch):
    """Aşırıya kaçma çivisi: operatörün açık override'ı türetime EZDİRİLMEZ."""
    conf = _conf_yakala(monkeypatch, {"budget": 21, "k_max": 4})
    assert conf == {"k_max": 4, "budget": 21}, f"operatör override'ı kayboldu: {conf}"
