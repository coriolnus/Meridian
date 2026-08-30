"""BRİFİNG KADANSI: hesaplanan teslim edilir, boşken SESSİZ — v327 (2026-08-27)

KADANS DEVREDİLDİ (Faz 2, 2026-08-29) ve BU DOSYANIN ÖZNESİ DEĞİŞTİ. Birim artık `ops/
oneri_brifingi.py` ile `ops/alarm_backlog_digest.py`i KOŞTURMUYOR; tek bir harness'ı
(`ops/sef_brifingi.py --uygula`) koşturuyor ve harness o ikisinin `ozet_kur()`unu OKUYUP
teslimden sonra damgalarını KENDİSİ basıyor. Bu dosyadaki çiviler silinmedi, ÖZNELERİ taşındı:
iki kaynak betiğin ÖZET/DAMGA sözleşmesi hâlâ burada ölçülür (onlar hâlâ üretimde, yalnız
çağıranları değişti), birim/timer çivileri de burada — ama artık "ikisini de AYNI birim
koşturur" CÜMLESİ YANLIŞTIR ve bu tur kaldırıldı (denetim 2026-08-30: bir önceki sürümü
anlatan yorum, okuyucuya yanlış mekanizma öğretir).

ÖLÇÜM (2026-08-27, canlı A1):
    notify_undelivered.json   toplam 310 · MECHANISM_STALE 208 · MIRROR_DRIFT 51 · NAKED_POSITION 9
    ops/alarm_backlog_digest.py  YAZILMIŞ, çalışıyor, ama HİÇBİR KADANSA ASILI DEĞİL
    improvement_proposals.jsonl  16 öneri, teslimat yolu YOK

Yani sistem hesaplıyor ve kimse okumuyor — bu deponun ölçülmüş hastalığı (`candidate_review.json`
günde 23 bin karakter üretiyor ve karar hattında okuyucusu yok).

SESSİZLİK ŞARTI PAZARLIĞA KAPALI: karar döndürmeyen zamanlanmış iş bildirim spam'idir. Yeni
bir şey yoksa mesaj YOKTUR.
"""
from __future__ import annotations

import pathlib
import shlex

import pytest

from tests.conftest import betikten_modul_yukle

KOK = pathlib.Path(__file__).resolve().parent.parent
BETIK = KOK / "ops/oneri_brifingi.py"
DIGEST_BETIK = KOK / "ops/alarm_backlog_digest.py"
SERVICE = KOK / "deploy/oracle-a1/meridian-brifing.service"
TIMER = KOK / "deploy/oracle-a1/meridian-brifing.timer"


def _yukle():
    assert BETIK.exists(), f"{BETIK} YOK"
    return betikten_modul_yukle(BETIK, "oneri_brifingi")


def _yukle_digest():
    """Alarm yığını kaynağı. Ayrı bir betiktir ve ayrı bir damga dosyası tutar (kardeşi EN YENİ
    ZAMAN DAMGASINI, bu KÜMÜLATİF SAYACI damgalar — ikisini aynı sanmak birini kalıcı damgasız
    bırakır). Birim bu betiği ARTIK KOŞTURMUYOR: `@sef` yalnız `ozet_kur()`unu okur ve teslimden
    sonra `damgala()`sını çağırır. Çivileri bu dosyada kalır çünkü ölçülen şey KAYNAĞIN kendi
    sözleşmesidir, onu kimin çağırdığı değil."""
    assert DIGEST_BETIK.exists(), f"{DIGEST_BETIK} YOK"
    return betikten_modul_yukle(DIGEST_BETIK, "alarm_backlog_digest")


def test_BOSKEN_SESSIZ(monkeypatch, sandbox_state):
    """Okunmamış öneri yoksa mesaj ÜRETİLMEZ. Karar döndürmeyen bildirim spam'dir."""
    mod = _yukle()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [])
    o = mod.ozet_kur()
    assert o["yeni"] == 0
    assert not o["mesaj"], f"boş defterde mesaj üretildi: {o['mesaj']!r}"


def test_YENI_ONERI_MESAJA_GIRER(monkeypatch, sandbox_state):
    """Okunmamış öneri varsa mesajda kimliği ve alanı geçer."""
    mod = _yukle()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        {"ts": "2026-08-27T10:00:00+00:00", "id": "N00017", "alan": "coverage_ariza.hotstate",
         "oneri": "watchdog hotstate sayacını harici süreçten okunur yap", "oncelik": "yuksek"},
    ])
    o = mod.ozet_kur()
    assert o["yeni"] == 1
    assert "N00017" in o["mesaj"] and "coverage_ariza.hotstate" in o["mesaj"]


def test_TESLIMDEN_SONRA_TEKRARLAMAZ(monkeypatch, sandbox_state):
    """Damga basıldıktan sonra aynı öneri ikinci kez bildirilmez."""
    mod = _yukle()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        {"ts": "2026-08-27T10:00:00+00:00", "id": "N00017", "alan": "x", "oneri": "y"},
    ])
    gonderilen = []
    monkeypatch.setattr(mod.notify, "configured", lambda: True)
    monkeypatch.setattr(mod.notify, "send", lambda t: gonderilen.append(t) or True)
    assert mod.main(["--uygula"]) == 0
    assert len(gonderilen) == 1
    assert mod.ozet_kur()["yeni"] == 0, "damga basılmamış — aynı öneri yeniden bildirilir"


def test_KURU_KOSUM_VARSAYILAN(monkeypatch, sandbox_state):
    """`--uygula` olmadan HİÇBİR ŞEY gönderilmez ve damga basılmaz."""
    mod = _yukle()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        {"ts": "2026-08-27T10:00:00+00:00", "id": "N00018", "alan": "x", "oneri": "y"},
    ])
    gonderilen = []
    monkeypatch.setattr(mod.notify, "configured", lambda: True)
    monkeypatch.setattr(mod.notify, "send", lambda t: gonderilen.append(t) or True)
    assert mod.main([]) == 0
    assert not gonderilen, "kuru koşumda gönderdi"
    assert mod.ozet_kur()["yeni"] == 1, "kuru koşumda damga bastı"


def _execstart_satirlari() -> list[str]:
    """Birimin `ExecStart` satırları (yorum/boş satır değil)."""
    return [ln.strip() for ln in SERVICE.read_text(encoding="utf-8").splitlines()
            if ln.strip().startswith("ExecStart")]


def _cagri_kuyruklari(betik: str) -> list[str]:
    """`betik`in ExecStart içindeki HER çağrısını, O ÇAĞRIYA AİT argüman kuyruğuyla döndürür
    (bir sonraki komut ayıracına — `;` `||` `&&` `|` ya da satır sonuna — kadar).

    NEDEN KUYRUK: eski çivi `--uygula`yı DOSYANIN HERHANGİ BİR YERİNDE arıyordu. İki çağrı var ve
    bayrak "teslim eder" ile "sessiz kuru koşum" arasındaki TEK farktır — birinden düşerse dosyada
    hâlâ bir `--uygula` görünür, çivi yeşil kalır ve o teslimat KALICI OLARAK SESSİZ olur."""
    import re
    exec_metni = "\n".join(_execstart_satirlari())
    kuyruklar = []
    for m in re.finditer(re.escape(betik), exec_metni):
        kalan = exec_metni[m.end():]
        kes = re.search(r"[;\n|&]", kalan)
        kuyruklar.append(kalan[:kes.start()] if kes else kalan)
    return kuyruklar


def test_BIRIM_SEF_BRIFINGINI_KOSUYOR_ve_ESKI_IKILIYI_KOSMUYOR():
    """KADANS DEVRİ (Faz 2). Birim artık iki betiği değil TEK harness'ı koşar: `sef_brifingi.py`.
    Çivi silinmedi, ÖZNESİ taşındı — teslimatın tetiklendiği gerçeği hâlâ burada ölçülür.

    `--uygula` O ÇAĞRININ kuyruğunda aranır (eski çivinin dersi, korunuyor): bayrak düşerse betik
    kuru koşuma iner — hiçbir şey göndermez, hiçbir hata da vermez. Kayıp KALICI olarak
    SESSİZDİR, yani tam da bu kadansın kapatmak için var olduğu arıza sınıfı.

    İKİNCİ YARI DEVRİN KENDİSİDİR: iki eski betik ARTIK ÇAĞRILMAMALI. `@sef` onların
    `ozet_kur()`unu okur ve teslimden SONRA damgalarını kendisi basar. Birim onları da koşsaydı
    operatör aynı yığını ÜÇ ayrı mesajda görürdü (dikkat bütçesi — botun var oluş sebebinin
    tersi) ve iki damgalayıcı aynı dosyada yarışırdı: hangisi önce damgalarsa öteki mesaj
    "yeni yok" derdi, yani kaynağın biri sessizce boşa konuşurdu."""
    assert SERVICE.exists() and TIMER.exists(), "systemd birimleri yok"
    kuyruklar = _cagri_kuyruklari("sef_brifingi.py")
    assert kuyruklar, "sef_brifingi.py birimin ExecStart'ında hiç çağrılmıyor — kadans devri yarım"
    for k in kuyruklar:
        assert "--uygula" in k, (
            f"sef_brifingi.py çağrısında `--uygula` YOK ({k!r}) — teslimat sessiz KURU KOŞUM olur")
    for eski in ("alarm_backlog_digest.py", "oneri_brifingi.py"):
        assert not _cagri_kuyruklari(eski), (
            f"{eski} birimde HÂLÂ doğrudan çağrılıyor — `@sef` zaten onun özetini taşıyor ve "
            "damgasını basıyor: operatöre çift mesaj gider ve iki damgalayıcı yarışır")


def test_BIRIM_ARIZAYI_YUTMAZ_ve_BIR_KAYNAK_DUSSE_OTEKI_TESLIM_EDILIR(monkeypatch, sandbox_state):
    """SARMALAYICININ İKİ ŞARTI, YENİ ŞEKİL ALTINDA. Çivi silinmedi; ÖZNESİ TAŞINDI.

    ÖZNESİ `sef_brifingi` ama EVİ v327 (denetim 2026-08-30 bunu bir dikiş olarak işaretledi).
    BİLEREK BURADA KALIYOR: ölçtüğü şey harness'ın içi değil KADANSIN iki şartıdır ve o iki şart
    bu dosyanın konusudur — birim şekli + betiğin çıkış kodları. Taşımak, "çivi silinmedi, öznesi
    taşındı" anlatısını ikinci kez kopararak izlenemez kılardı.

    Eski şekil iki betiği tek bir `/bin/sh -c` sarmalayıcıyla koşturuyordu ve iki şartı O
    sarmalayıcı taşıyordu:
      (a) ilk teslimat düşse bile İKİNCİSİ KOŞAR — biri sussa öteki teslim etsin,
      (b) HERHANGİ biri düşerse birim `failed` biter.
    Kadans `@sef`e devredilince (a) sarmalayıcıdan ÇIKIP HARNESS'IN İÇİNE girdi ve (b) düz bir
    `ExecStart`a indi. Şartlar KALKMADI, yer değiştirdi — bu yüzden çivi de yer değiştirir.
    Öznesi taşınan bir çivi silinmez, yeniden yazılır.

    (b) BİRİNCİ YARI — ŞEKİL. `-` öneksiz TEK `ExecStart`. `-` öneki çıkış kodunu YUTAR ve birim
    ASLA `failed` görmez; oysa `failed`in okuyucusu ölçülü (`/api/infra` `ActiveState=failed`i
    "arizali" sayıyor), yani teslimat kanalı kırıldığında arızayı görünür kılan TEK şey odur.
    Kabuk sarmalayıcı da artık GEREKMEZ ve BULUNMAMALI: tek komut için `/bin/sh -c` yalnız bir
    `$` ikame yüzeyi ekler (systemd kaçırılmamış `$`i boşaltır — kardeş çivi
    `tests/test_kucuk_kuyruk_v179.py` bunu zaten biliyor) ve karşılığında hiçbir şey kazandırmaz.

    (b) İKİNCİ YARI — DAVRANIŞ. Düz `ExecStart` ancak betik GERÇEKTEN sıfırdan farklı dönerse
    `failed` üretir; yani (b) yarısı birimde, yarısı betiktedir. Kanal yapılandırılmamışsa 2,
    gönderim düşerse 1 — ikisi de burada KOŞTURULARAK ölçülür, metin aranarak değil.

    (a) ARTIK HARNESS'IN İÇİNDE. Bir kaynağın `ozet_kur()`u PATLASA bile öteki kaynak toplanır ve
    teslim edilir; patlayan kaynak "ölçülemedi" diye ADIYLA basılır — sıfır sanılmaz (UYDURMA
    YASAĞI). Tek mesaj tek gönderime indiği için eski (a) "iki gönderim" değil "iki KAYNAK"
    düzeyinde yaşar: koruduğu arıza aynıdır — bir tarafın kırılması ötekini sustursun.
    """
    satirlar = _execstart_satirlari()
    assert len(satirlar) == 1, (
        f"tek bir ExecStart bekleniyordu, {len(satirlar)} satır var: {satirlar!r} — ayrı "
        "`ExecStart=` satırları arızayı ya yutar ya da ilkinde durur")
    assert not satirlar[0].startswith("ExecStart=-"), (
        "`ExecStart=-` çıkış kodunu YUTAR — birim hiçbir zaman `failed` olmaz ve Telegram "
        "kırıldığında iş HER GÜN sessizce düşer")
    parcalar = shlex.split(satirlar[0].split("=", 1)[1])
    assert "sh" not in pathlib.Path(parcalar[0]).name, (
        f"ExecStart hâlâ bir kabuk sarmalayıcı: {parcalar!r} — tek komut için kabuk yalnız bir "
        "`$` ikame yüzeyi ekler, hiçbir şart kazandırmaz")
    assert "$" not in satirlar[0], (
        f"ExecStart `$` taşıyor — systemd onu ikame eder/boşaltır: {satirlar[0]!r}")
    assert parcalar[0].endswith("/python") and parcalar[1].endswith("/ops/sef_brifingi.py"), (
        f"ExecStart doğrudan `.venv/bin/python ops/sef_brifingi.py` çağırmıyor: {parcalar!r}")

    # --- (b) İKİNCİ YARI + (a): betiğin KENDİSİ koşturulur -------------------------------------
    import importlib
    sef = importlib.reload(importlib.import_module("ops.sef_brifingi"))

    def _alarm_patlar():
        raise RuntimeError("notify_undelivered.json okunamadı")

    monkeypatch.setattr(sef, "_alarm_ozeti", _alarm_patlar)
    monkeypatch.setattr(sef, "_oneri_ozeti",
                        lambda: {"toplam": 1, "yeni": 1, "mesaj": "1 okunmamış öneri: N00017"})
    monkeypatch.setattr(sef, "_self_review", lambda: {})
    monkeypatch.setattr(sef, "_son_brifing", lambda: "")

    ham = sef.topla()
    assert not ham["bos"], (
        f"bir kaynak patlayınca brifing SUSTU: {ham!r} — ölçüm zincirinin kırıldığı gün "
        "susmak, sustuğunu 'bugün bir şey yoktu' diye raporlamaktır")
    assert [k["kaynak"] for k in ham["teslim_edilecek"]] == ["oneri"], (
        f"patlayan kaynak ÖTEKİNİ de düşürdü: {ham['teslim_edilecek']!r} — eski sarmalayıcının "
        "(a) şartı harness'ta korunmadı")
    assert [k["kaynak"] for k in ham["olculemeyen"]] == ["alarm"], (
        f"patlayan kaynak ADIYLA beyan edilmedi: {ham['olculemeyen']!r} — ölçülemeyen bir kaynak "
        "sıfır gibi görünemez")

    monkeypatch.setattr(sef, "_profili_cagir", lambda _p: "- okunmamış öneri N00017 bekliyor")
    monkeypatch.setattr(sef.notify, "configured", lambda: False)
    assert sef.main(["--uygula"]) != 0, (
        "kanal yapılandırılmamışken betik 0 döndü — düz `ExecStart` bunu `failed`e çeviremez ve "
        "teslimatsız kadans BAŞARILI görünür")

    monkeypatch.setattr(sef.notify, "configured", lambda: True)
    monkeypatch.setattr(sef.notify, "send", lambda _t: False)
    assert sef.main(["--uygula"]) != 0, (
        "gönderim düştüğü hâlde betik 0 döndü — birim `failed` olmaz, panoda hiçbir şey "
        "kırmızıya dönmez ve yığın sessizce büyür")


def test_TIMER_GUNLUK():
    t = TIMER.read_text(encoding="utf-8")
    assert "OnCalendar=" in t, "timer takvim tanımı yok"
    assert "Persistent=true" in t, (
        "Persistent yok — makine kapalıyken kaçan tetik telafi edilmez")


def test_TIMER_KIS_SAATINDE_DE_KAPANISTAN_SONRA():
    """DST TUZAĞI (denetim 2026-08-29). ABD kapanışı 16:00 ET SABİTTİR ama UTC karşılığı DEĞİL:
    EDT'de 20:00 UTC, EST'de (Kasım–Mart, yılın BEŞ AYI) 21:00 UTC. 21:00 UTC'lik bir tetik kış
    boyunca TAM KAPANIŞ ZİLİNDE, EOD turundan ÖNCE ateşlerdi — ve birim yorumu bunun tersini
    iddia ediyordu. Kapı: tetik saati her iki rejimde de kapanıştan SONRA olmalı, yani
    >= 22:00 UTC (EST kapanışı 21:00 UTC + EOD turu için pay). Emsal ve gerekçe biçimi:
    `meridian-backup.timer` (23:30 UTC = 18:30/19:30 NY)."""
    import re
    t = TIMER.read_text(encoding="utf-8")
    m = re.search(r"^OnCalendar=\S+ (\d{2}):(\d{2}):(\d{2}) UTC\s*$", t, re.M)
    assert m, f"OnCalendar açıkça UTC saatiyle yazılmalı (sunucu TZ'sine güvenilmez): {t!r}"
    saat = int(m.group(1))
    assert saat >= 22, (
        f"{saat:02d}:00 UTC — EST rejiminde (Kasım–Mart) ABD kapanışı 21:00 UTC'dir; bu tetik "
        f"kapanış zilinde ya da öncesinde ateşler, EOD turu daha bitmemiştir")


def test_dagit_F9_birimleri_IZLIYOR():
    metin = (KOK / "dagit.sh").read_text(encoding="utf-8")
    for ad in ("meridian-brifing.service", "meridian-brifing.timer"):
        assert f"deploy/oracle-a1/{ad}|/etc/systemd/system/{ad}" in metin, f"F9 {ad}'i izlemiyor"


# ---- DÜZELTME TURU 1 (2026-08-29 denetimi) — iki çivi, ikisi de "öneri KALICI kaybolabilir" ----

def test_TS_SIZ_SATIR_SESSIZCE_DUSMEZ(monkeypatch, sandbox_state):
    """ts alanı olmayan/boş bir öneri sessizce dışlanamaz: `"" > ""` her zaman False olduğu için
    eski kod böyle bir satırı NE İLK TURDA NE DE HİÇBİR ZAMAN bildirmiyordu — `toplam`a sayılmaya
    devam ederken mesajda hiç görünmüyordu (kalıcı sessiz dışlama). Düzeltme: ts'siz satır
    KOŞULSUZ `yeni`ye girer ve mesajda ölçülemediği açıkça işaretlenir (UYDURMA YASAĞI: eksik
    alan gizlenmez, beyan edilir; ts UYDURULMAZ)."""
    mod = _yukle()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        {"id": "N00099", "alan": "ts_eksik.alani", "oneri": "ts alanı olmadan üretilmiş satır"},
    ])
    o = mod.ozet_kur()
    assert o["yeni"] == 1, f"ts'siz satır sessizce düşürüldü: {o}"
    assert "N00099" in o["mesaj"] and "ts_eksik.alani" in o["mesaj"]


def test_GONDERIM_PENCERESINDE_EKLENEN_SATIR_KACIRILMAZ(monkeypatch, sandbox_state):
    """Gönderim SIRASINDA (network POST penceresinde) deftere düşen bir satır, mesaj zaten
    KURULDUKTAN sonra geldiği için o turun mesajında YOKTUR. Eski kod damgayı `notify.send`
    DÖNDÜKTEN SONRA yapılan İKİNCİ bir okumadan hesaplıyordu — bu ikinci okuma pencere
    içinde eklenen satırı da görüyor ve damga onu "gördüm" sayıyordu, hiç bildirmemiş olarak.
    Düzeltme: damga yalnız GÖNDERİLEN mesajı üreten enstantaneden ilerler; gönderim sonrası
    ikinci bir defter okuması YOK."""
    mod = _yukle()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        {"ts": "2026-08-27T10:00:00+00:00", "id": "N00020", "alan": "x", "oneri": "ilk satır"},
    ])

    def _sahte_gonder(text):
        # notify.send'in GERÇEK ağ çağrısı sırasında BAŞKA bir yazar (nous_eval.py gibi) deftere
        # yeni bir satır ekliyor — bu satır gönderilen `text`te YOKTUR.
        store.write_jsonl("improvement_proposals.jsonl", [
            {"ts": "2026-08-27T10:00:00+00:00", "id": "N00020", "alan": "x", "oneri": "ilk satır"},
            {"ts": "2026-08-27T10:05:00+00:00", "id": "N00021", "alan": "y",
             "oneri": "gönderim sırasında eklendi"},
        ])
        return True

    monkeypatch.setattr(mod.notify, "configured", lambda: True)
    monkeypatch.setattr(mod.notify, "send", _sahte_gonder)
    assert mod.main(["--uygula"]) == 0

    o2 = mod.ozet_kur()
    assert o2["yeni"] == 1, (
        f"gönderim penceresinde eklenen satır bir sonraki turda KAÇIRILDI: {o2}")
    assert "N00021" in o2["mesaj"]


def test_DIGEST_GONDERIM_PENCERESINDE_ARTAN_SAYAC_KACIRILMAZ(monkeypatch, sandbox_state):
    """`test_GONDERIM_PENCERESINDE_EKLENEN_SATIR_KACIRILMAZ`ın İKİZİ — bu kez alarm yığını için.
    Aynı kusur (2026-08-29 denetiminde ayrı kalem olarak kaydedilmişti, bu turda kapatıldı).

    `alarm_backlog_digest.py` damgayı `_damgala` İÇİNDE, kilitli güncellemenin TAZE okumasından
    hesaplıyordu (`int(d.get("_toplam"))`) — GÖNDERİLEN mesajı üreten enstantaneden değil. Mesajın
    kurulmasıyla damganın basılması arasında tam bir `events.jsonl` taraması VE 8 saniyelik bir ağ
    POST'u var. O pencerede `obs._maybe_notify`ın sayaca yazdığı her alarm, kendisinden hiç söz
    ETMEYEN bir mesajla "kapsandı" damgası yerdi. Ve sayaçlar ASLA azalmadığı için
    (`yeni = toplam - kapsanan`) o alarm bir daha HİÇBİR özete giremezdi — kalıcı sessiz kayıp,
    üstelik alarm yığınının kendi teslimat mekanizmasında.

    Düzeltme: damga `o` enstantanesinden basılır. Kardeş betikteki (`oneri_brifingi.py`) çözümün
    birebir aynısı."""
    mod = _yukle_digest()
    from meridian import store
    store.write_json("notify_undelivered.json", {"_toplam": 5, "MECHANISM_STALE": 5})

    def _sahte_gonder(text):
        # notify.send'in ağ POST'u sürerken canlı worker yeni bir alarmı sayaca yazıyor. Bu
        # alarm gönderilen `text`te YOKTUR — mesaj çoktan kurulmuştu.
        assert "MIRROR_DRIFT" not in text, "kurgu hatası: yeni alarm mesajda görünmemeli"
        store.write_json("notify_undelivered.json",
                         {"_toplam": 8, "MECHANISM_STALE": 5, "MIRROR_DRIFT": 3})
        return True

    monkeypatch.setattr(mod.notify, "configured", lambda: True)
    monkeypatch.setattr(mod.notify, "send", _sahte_gonder)
    assert mod.main(["--uygula"]) == 0

    o2 = mod.ozet_kur()
    assert o2["yeni"] == 3, (
        f"gönderim penceresinde biriken alarmlar 'kapsandı' damgası yedi ve KALICI olarak "
        f"kayboldu: {o2}")
    assert "MIRROR_DRIFT" in o2["mesaj"]


def test_BIRIM_YANLISLIKLA_ENABLE_EDILEMEZ():
    """Servis birimi `[Install]` TAŞIMAZ — tetiği YALNIZ timer'dır.

    NEDEN. `deploy.sh` bilerek yalnız `meridian-brifing.timer`ı enable eder (birimin kendisini
    DEĞİL, yorumunda da yazılı). Ama serviste bir `[Install] WantedBy=multi-user.target`
    dururken `systemctl enable meridian-brifing.service` SESSİZCE başarılı olur ve birime
    kimsenin istemediği bir AÇILIŞ KOŞUMU ekler — timer'ın kadansının dışında, `Persistent`
    telafisiyle karışan ikinci bir tetik. `[Install]` yokken aynı komut "no installation config"
    diye DÜŞER: operatör hatası sessiz davranış değişikliği değil, görünür bir hata olur.

    FİLO ÖLÇÜMÜ (varsayılmadı): timer-tetikli oneshot kardeşlerden `meridian-backup.service` ve
    `meridian-tick-watchdog.service` `[Install]` TAŞIMIYOR. `meridian-aylik-bucket-kopya.service`
    taşıyor — konvansiyon filoda AYRIK, bu yüzden çivi sınıf değil BU birime kapsanmıştır;
    çalışan dağıtılmış bir birimi bu turda değiştirmek kapsam dışıdır.
    """
    # BÖLÜM BAŞLIĞI aranır, ALT-DİZGE DEĞİL: dosyanın kendisi bölümün NEDEN olmadığını yorumda
    # anlatıyor ve o yorum "[Install]" dizgesini İÇERİYOR. Alt-dizge araması bu çiviyi, bölüm
    # gerçekten kaldırıldıktan SONRA bile kırmızı tutardı — ölçtüğünü sandığı şeyi ölçmeyen
    # çivi sınıfı. systemd bölüm başlığı satırın TAMAMIDIR; `#`/`;` ile başlayan satır yorumdur.
    satirlar = [ln.strip() for ln in SERVICE.read_text(encoding="utf-8").splitlines()]
    bolumler = [ln for ln in satirlar if ln and not ln.startswith(("#", ";"))]
    assert "[Install]" not in bolumler, (
        "meridian-brifing.service bir `[Install]` BÖLÜMÜ taşıyor — `systemctl enable "
        "meridian-brifing.service` sessizce geçer ve timer'dan bağımsız bir açılış koşumu ekler; "
        "tetik YALNIZ meridian-brifing.timer olmalı"
    )


def test_deploy_sh_BIRIMLERI_KURAR_ama_KADANSI_ACMAZ():
    """`deploy.sh` iki birimi + hermes config'ini KURAR, ama kadansı KOŞULSUZ AÇMAZ.

    İKİ AYRI ARIZA, tek çivi. (a) Kurulum adımının unutulması: bulgu 6'nın kendisi buydu ve
    emsali `test_kucuk_kuyruk_v179.py::test_deploy_sh_bekciyi_KURAR` — bekçi 2026-07-31'de
    CANLIDA elle doğmuş, depoya hiç girmemişti. (b) Kurulumun ETKİNLEŞTİRME ile aynı eylem
    olması: `cutover.sh` adım 4 `deploy.sh`i çağırır, yani ilgisiz bir sebeple koşan tek bir
    dağıtım operatöre GÜNLÜK TELEGRAM kadansı açardı — kimse karar vermeden. Kurulum zararsız,
    teslimat değil; kapı `is-enabled` üstünde ve İLK açılışa bakar (sonrası idempotent).
    """
    d = (KOK / "deploy/oracle-a1/deploy.sh").read_text(encoding="utf-8")
    for parca in ("meridian-brifing.service       /etc/systemd/system/",
                  "meridian-brifing.timer         /etc/systemd/system/",
                  'cp deploy/hermes/config.yaml "$HOME/.hermes/config.yaml"'):
        assert parca in d, f"deploy.sh kurmuyor: {parca}"

    # KOŞULSUZ enable YASAK: `enable --now meridian-brifing.timer` geçen HER satır bir `if`
    # gövdesinin İÇİNDE olmalı. Girinti ölçülür — kardeş timer'lar sütun 0'da, bu değil.
    satirlar = [ln for ln in d.splitlines()
                if "enable --now meridian-brifing.timer" in ln and not ln.lstrip().startswith(("#", "echo"))]
    assert satirlar, "deploy.sh brifing timer'ını hiç enable etmiyor — açıldıktan sonra dağıtımlar onu kapatır"
    for ln in satirlar:
        assert ln.startswith((" ", "\t")), (
            "brifing timer'ı KOŞULSUZ enable ediliyor — ilgisiz bir deploy.sh koşumu günlük "
            f"Telegram kadansını operatör kararı olmadan açar: {ln!r}")
    assert "is-enabled meridian-brifing.timer" in d, \
        "kapı `is-enabled` üstünde kurulmamış — 'zaten açıksa açık tut' davranışı ölçülemez"
    # Kapalı dalda operatöre TAM komut verilir: 'bir yerde yazılıdır' yetmez, ekranda olmalı.
    assert "sudo systemctl enable --now meridian-brifing.timer" in d, \
        "kapalı dal operatöre açma komutunu BASMIYOR"


def test_DAMGA_SAYACI_ASARSA_IYI_HUYLU_HICLIK_GIBI_GORUNMEZ(sandbox_state):
    """`kapsanan > toplam` İMKÂNSIZ bir durumdur ve İMKÂNSIZ diye rapor edilmeli.

    NEDEN. Damga artık `o["toplam"]`dan basılıyor (denetimin CRITICAL'ı) ve bu doğru: `_toplam`
    yalnız ARTAN bir sayaçtır (`meridian/obs.py` `_bump`/`_bump_fail`: `int(...) + 1`, azaltan
    tek bir yol yok). Ama sözleşme bir gün kırılırsa — sayaç sıfırlanır, dosya elle düzenlenir,
    bir geri yükleme eski `notify_undelivered.json`u koyar — `yeni = toplam - kapsanan` NEGATİF
    olur ve eski kod `yeni <= 0` dalına düşüp *"damgadan beri yeni birikme yok"* derdi. Yani
    özet KALICI OLARAK susar ve sustuğunu **iyi huylu bir idempotens** diye rapor eder.

    Bu, bu depoda adı konmuş sınıftır: ölçülemeyen bir durum iyi huylu bir hiçlik gibi
    görünemez (UYDURMA YASAĞI; aynı turda `_mutabakat_bayatligi` da bu yüzden `None + neden`
    döndürecek şekilde yazıldı). Sıfır ile 'bilmiyorum' aynı şey değildir.
    """
    from meridian import store as _store
    import importlib
    m = importlib.import_module("ops.alarm_backlog_digest")
    importlib.reload(m)

    # Damga sayacı AŞIYOR: 5 kapsanmış, ama toplam 3 (sayaç geri gitmiş).
    _store.write_json(m.UNDELIVERED, {
        "_toplam": 3, "MECHANISM_STALE": 3,
        m.DAMGA: {"ts": "2026-08-29T00:00:00Z", "toplam_kapsanan": 5},
    })
    o = m.ozet_kur()
    assert o.get("hata"), (
        "kapsanan(5) > toplam(3) İMKÂNSIZ durumu hata olarak raporlanmadı — özet sessizce "
        f"'yeni birikme yok' diyor ve bir daha hiç konuşmaz: {o!r}")
    assert "3" in str(o["hata"]) and "5" in str(o["hata"]), \
        f"hata mesajı iki sayıyı da taşımalı (teşhis edilemez hata işe yaramaz): {o['hata']!r}"


def test_deploy_sh_BIRIM_DOSYASINI_DA_KOSULSUZ_DEVRETMEZ():
    """KURULUM KAPISI, BİR KATMAN YUKARISI — `enable` kapısının ikizi (denetim 2026-08-30).

    KAPATILAN ARIZA. Kardeş çivi (`test_deploy_sh_BIRIMLERI_KURAR_ama_KADANSI_ACMAZ`) yalnız
    timer'ın AÇILMASINI koruyordu; birim DOSYASI koşulsuz kopyalanıp `daemon-reload` ediliyordu.
    Timer A1'de ZATEN AÇIKSA — ki bir kez açıldıktan sonra öyle kalır, kapı bilerek "açık tut"
    diyor — ilgisiz bir sebeple koşan tek bir `deploy.sh` (ve `cutover.sh` adım 4 onu ÇAĞIRIR)
    günlük teslimatın ExecStart'ını sessizce `@sef`e çevirirdi: profil kurulu olmadığı için HAM
    modda, ve kimse bu devri KARAR OLARAK vermemişken. Kurulum zararsız DEĞİLDİR: bu dosya
    ÇALIŞAN bir kadansın ne koşturacağını belirler.

    KAPININ ŞEKLİ. Kopyalama, kardeşiyle AYNI `is-enabled` ölçümüne bağlanır ve girinti ölçülür —
    kardeş birimler sütun 0'da kopyalanır, bu değil.
    """
    d = (KOK / "deploy/oracle-a1/deploy.sh").read_text(encoding="utf-8")
    satirlar = [ln for ln in d.splitlines()
                if "meridian-brifing.service" in ln and " cp " in ln
                and not ln.lstrip().startswith("#")]
    assert satirlar, "deploy.sh brifing birimini hiç kurmuyor — taze kurulumda kadans dosyasız kalır"
    for ln in satirlar:
        assert ln.startswith((" ", "\t")), (
            "brifing BİRİM DOSYASI koşulsuz kopyalanıyor — timer zaten açıksa ilgisiz bir "
            f"dağıtım günlük teslimatı kimse karar vermeden @sef'e çevirir: {ln!r}")


def test_deploy_sh_HANGI_TESLIMATIN_YURURLUKTE_OLDUGUNU_BASAR():
    """Kapı sessiz kalırsa operatör hangi teslimatın koştuğunu BİLMEZ.

    Devir kapısı bir dağıtımı "yapmadım" diye bitirebilir; bu doğru davranış ama YARIM: operatör
    ekranda YÜRÜRLÜKTEKİ ExecStart'ı görmeli, yoksa "kurdum" ile "kurulu olan hâlâ eski" aynı
    görünür — bu betiğin her yerde kapattığı sınıf."""
    d = (KOK / "deploy/oracle-a1/deploy.sh").read_text(encoding="utf-8")
    assert "systemctl cat meridian-brifing.service" in d, (
        "deploy.sh canlıdaki birimin ExecStart'ını HİÇ okumuyor — hangi teslimatın yürürlükte "
        "olduğu ölçülmeden raporlanamaz")
    assert "YÜRÜRLÜKTEKİ" in d or "yürürlükte" in d, (
        "deploy.sh yürürlükteki teslimatı operatöre BASMIYOR")
