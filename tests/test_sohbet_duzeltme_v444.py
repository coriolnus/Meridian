"""test_sohbet_duzeltme_v444.py — TSK-012 dalga-B / B1 GÜN SONU İNCELEME DÜZELTMELERİ.

NE ÇİVİLENİR (bağımsız çekişmeli incelemenin ayakta bıraktığı 11 bulgu → A1..A8):
  A1 `POST /api/sohbet` olay döngüsünü BLOKLAMAZ (senkron döngü thread havuzuna devredilir),
  A2 `olay_sorgu` aracı KEYFİ YEREL DOSYA OKUYAMAZ (DuckDB harici erişimi motor düzeyinde kapalı),
  A3 sohbet onayının yanıtı ve DEFTER SATIRI aynı künyeyi taşır ("davranış DEĞİŞMEZ" derken icra
     eden yanıt kusuru),
  A4 kota mesaj başında DEĞİL, HER AYAK öncesi ölçülür,
  A5 boş şemalı araca `null` argüman geçerlidir,
  A6 `_defter_tarama`nın "öneri satırı" muafiyeti YALNIZ sohbet öneri satırlarına daralır,
  A7 `_arac_oneri_yaz`ın ikinci (savunmacı) tur kapısı DOĞRUDAN çağrıyla ısırılır,
  A8 gelen kutusundaki sohbet gerekçesi 200 karakterde KIRPILMAZ,
  A9 `kota_durumu()['dolu']` ile `_kota_cevabi(...) is not None` AYNI hükümden türer.

TUR 2 (aynı düzeltmenin çekişmeli incelemesi: 28 ayakta bulgu → 7 kök; A3/A1/A2'nin AÇTIĞI
kusurlar da buradadır):
  K1 sohbet karar satırı `davranissal`ı ARTIK EĞMEZ (`KAPI_OKUYAN_ONEKLER` anlamı korunur); icra
     gerçeği `icra_eder`/`icra_ok` + künye ile söylenir, künye KARARDAN türer (ret ≠ onay) ve
     defter satırı İCRADAN SONRA yazılır,
  K2 A1'in açtığı GERÇEK eşzamanlılığın bedeli ödenir: sohbet turu serileşir, öneri sayacı ve
     defter append'leri kilit altındadır (kimlik çakışması = YANLIŞ planın icrası),
  K3 `bar_sorgu` aracı canlıda HİÇ çalışmıyordu (`barlar` görünümü kurulmuyor, `bosluk` span'sız)
     — üç kol da GERÇEKTEN koşan pozitif kontrollerle çivilenir,
  K4 model yazımı SQL'in bellek/iplik/SÜRE tavanı vardır (tek uvicorn işçisi),
  K5 çözümlenemeyen sorgu SAHTE KAYNAK ATFI üretmez (uydurma sayımının paydası),
  K6 materyalizasyon bedeli ARŞİVLİ dünyada da ölçülür (üretimdeki şekil).

TUR 3 (yeniden incelemenin iki tavsiyesi — bloklayıcı 0, ikisi de ÖLÇÜLMÜŞ BEDEL kalemi):
  M1 `bar_sorgu` MATERYALİZE ETMEZ: o bağlantının SQL'ine modelin denetimindeki hiçbir metin
     ulaşmıyor (enum sorgu + bağlı parametre + tamsayı `n` + glob'dan görünüm), yani kapı SIFIR
     saldırı yüzeyi kapatıp aylık büyüyen arşivin tamamını `SORGU_BELLEK_TAVANI` altında belleğe
     aldırıyordu. Kazanç ölçüldü ve SIFIR; asıl kapı `..._SERBEST_SQL_alani_YOK` çivisidir.
     `olay_sorgu`da kapı KALIR (orada serbest SQL GERÇEKTEN var) — iki ayrı çivi bunu ayırır.
  M2 `_SOHBET_KILIDI` PARK ETMEZ (`acquire(blocking=False)`): kilitte bekleyen iplik paylaşılan
     anyio iş havuzunun bir jetonunu tutuyordu (ölçüldü: 40 jeton; `api.py`de 90+ senkron rota
     o havuzda koşar) ve kilidin en kötü tutuluşu `max_tur × zincir × ZAMAN_ASIMI_S`ydi. İkinci
     mesaj artık SIRAYA GİRMEZ, `mesgul` cevabıyla ANINDA döner: model çağrılmaz, kota harcanmaz
     ve `sohbet.jsonl`e satır YAZILMAZ (ölçüm paydası kirlenmesin).
  Emekliye ayrılan iki çivi (M1 ile konusu kalmayanlar): `test_bar_sorgu_baglantisi_HARICI_
  ERISIMI_kapatir` ve `test_harici_erisim_kapisi_BARLAR_gorunumunde_de_isirir` — ikisi de artık
  üretimde çağıranı olmayan bir yolu ölçüyordu (`_harici_erisimi_kapat`ın `gorunum` parametresi
  de bu turda düştü: tek görünüm, tek çağıran).

MODEL, ARAÇ VE AĞ SAHTEDİR: bu dosya hiçbir gerçek kapı çağrısı yapmaz, hiçbir plan onaylamaz,
hiçbir alarm kapatmaz ve hiçbir gerçek sır okumaz. Yazımlar `sandbox_state` ile tmp'ye düşer.
"""
from __future__ import annotations

import asyncio
import inspect
import json
import re
import time

import httpx
import pytest
from fastapi.testclient import TestClient

from meridian import api, config, notify, sohbet, store

#: A1 ölçümünün blok süresi. İki eşzamanlı istek: thread havuzunda ~`BLOK_S`, olay döngüsünde
#: bloklanırsa ~`2×BLOK_S`. Eşik ikisinin ORTASINDADIR — makine yükü ikisini karıştıramaz.
BLOK_S = 0.4
#: A2 pozitif kontrolü: sahte dosyaya konan BİLİNEN dizge. Modele giden gövdede geçerse sızıntı
#: ölçülmüş demektir (ret metninin "içerik yok" iddiası böyle kanıtlanır).
SIZINTI_IMZASI = "SIZINTI-IMZASI-V444"
#: A2 maliyet tavanı: materyalizasyon canlı defter boyutunda bu süreyi aşarsa sohbet yavaşlar.
MATERYALIZE_TAVANI_S = 2.0
#: Canlı olay defterinin ölçülmüş büyüklüğü (2026-09-03: 27.887 satır / 9,0 MB) — maliyet
#: ölçümünün sentetik eşdeğeri UYDURULMAZ, o sayıdan türetilir.
CANLI_OLAY_SATIRI = 28_000


@pytest.fixture
def kum(sandbox_state):
    return sandbox_state


@pytest.fixture
def istemci(kum, monkeypatch) -> TestClient:
    monkeypatch.setattr(api, "DASH_TOKEN", None)
    return TestClient(api.app)


def _kaynak(fn) -> str:
    return inspect.getsource(fn)


def _seviye(monkeypatch, lvl: int) -> None:
    gercek = dict(config.limits())
    monkeypatch.setattr(config, "limits", lambda: {**gercek, "autonomy_level": lvl})


class SahteModel:
    """`model_cagir(mesajlar, araclar) -> dict` sahtesi (v440 emsali)."""

    def __init__(self, *cevaplar, ayak_kaydi: bool = False):
        self.kuyruk = list(cevaplar)
        self.cagrilar: list[dict] = []
        self.ayak_kaydi = ayak_kaydi

    def __call__(self, mesajlar, araclar):
        self.cagrilar.append({"mesajlar": [dict(m) for m in mesajlar]})
        if self.ayak_kaydi:
            # GERÇEK AYAĞIN MUHASEBESİ: `_kapi_cagir` her denenen model için telemetri satırı
            # yazar ve kota O SATIRLARDAN sayılır. Sahte model bunu taklit etmezse "kota döngü
            # içinde doldu" senaryosu ölçülemezdi.
            store.append_jsonl(sohbet.CAGRI_DEFTERI,
                               {"ts": sohbet._simdi_iso(), "kind": sohbet.CAGRI_KIND,
                                "model": "sahte"})
        if self.kuyruk:
            return self.kuyruk.pop(0)
        return _metin("son cevap")


def _tc(ad, args, cid="c1"):
    ham = args if isinstance(args, str) or args is None else json.dumps(args, ensure_ascii=False)
    return {"id": cid, "type": "function", "function": {"name": ad, "arguments": ham}}


def _arac(*tool_calls, model="sahte-1"):
    return {"mesaj": {"content": "", "tool_calls": list(tool_calls)}, "model": model,
            "jeton_giris": 10, "jeton_cikis": 5}


def _metin(txt, model="sahte-1"):
    return {"mesaj": {"content": txt, "tool_calls": []}, "model": model,
            "jeton_giris": 10, "jeton_cikis": 5}


def _arac_ciktisi(kayit: dict) -> str:
    araclar = [m for m in kayit["mesajlar"] if m.get("role") == "tool"]
    assert araclar, "modele hiç araç sonucu gitmedi"
    return str(araclar[-1]["content"])


def _cagri_yaz(n: int) -> None:
    for i in range(n):
        store.append_jsonl(sohbet.CAGRI_DEFTERI,
                           {"ts": sohbet._simdi_iso(), "kind": sohbet.CAGRI_KIND, "model": "x"})


def _oneri_yaz(tur="plan_onayi", hedef="P-2026-09-07-MU", gerekce="operatör baksın",
               oturum="S1") -> str:
    if tur == "plan_onayi":
        store.append_jsonl("trade_plans.jsonl", {"id": hedef, "ticker": "MU",
                                                 "date": "2026-09-07", "gate_verdict": "REVIEW"})
    sohbet._arac_oneri_yaz({"tur": tur, "hedef": hedef, "gerekce": gerekce}, {"oturum": oturum})
    satirlar = [r for r in store.read_jsonl(sohbet.ONAY_DEFTERI) if r.get("kaynak") == "sohbet"]
    assert satirlar, "öneri yazılmadı"
    return satirlar[-1]["id"]


# =================================================================================================
# A1 — `POST /api/sohbet` OLAY DÖNGÜSÜNÜ BLOKLAMAZ
# =================================================================================================
def _sahte_satir(oturum: str) -> dict:
    return {"ts": "2026-09-08T00:00:00+00:00", "oturum": oturum, "mesaj": "m", "cevap": "c",
            "turlar": [], "kaynaklar": [], "model": "sahte", "sure_s": 0.0,
            "jeton_giris": None, "jeton_cikis": None, "kota_bugun": 0, "oneri_id": None,
            "sema_disi_n": 0, "llm_dustu": False}


def test_sohbet_ucu_olay_dongusunu_bloklamaz(istemci, monkeypatch):
    """İKİ EŞZAMANLI İSTEK, TEK OLAY DÖNGÜSÜ. `sohbet_dongusu` senkrondur (`httpx.post`,
    `subprocess.run`); `async def` bir rotanın gövdesinde DOĞRUDAN çağrılırsa olay döngüsünü
    işgal eder ve AYNI worker'daki her uç (halt/ack dahil) o süre boyunca cevapsız kalır.

    ÖLÇÜM: iki istek `asyncio.gather` ile birlikte başlar. Thread havuzuna devredilmişse toplam
    süre ~`BLOK_S`; olay döngüsünde bloklanırsa istekler SIRAYA girer ve ~`2×BLOK_S` olur."""
    monkeypatch.setattr(sohbet, "sohbet_dongusu",
                        lambda mesaj, oturum, **kw: (time.sleep(BLOK_S),
                                                     _sahte_satir(str(oturum)))[1])

    async def kos() -> float:
        tasima = httpx.ASGITransport(app=api.app)
        async with httpx.AsyncClient(transport=tasima, base_url="http://olcum") as c:
            t0 = time.perf_counter()
            yanitlar = await asyncio.gather(
                c.post("/api/sohbet", json={"mesaj": "bir", "oturum": "A"}),
                c.post("/api/sohbet", json={"mesaj": "iki", "oturum": "B"}))
            sure = time.perf_counter() - t0
        assert all(y.status_code == 200 for y in yanitlar), [y.status_code for y in yanitlar]
        return sure

    sure = asyncio.run(kos())
    assert sure < BLOK_S * 1.5, (
        f"iki eşzamanlı sohbet isteği {sure:.3f} s sürdü (eşik {BLOK_S * 1.5:.3f} s) — "
        "istekler SIRAYA girdi, yani olay döngüsü bloklandı")


def test_sohbet_ucu_bloklayici_govdeyi_thread_havuzuna_devreder():
    """YAPISAL ÇİVİ: zamanlama ölçümü makine yüküne duyarlıdır, bu satır değildir. `api.py`nin
    kendi emsali (`hafiza_recall` uçları) aynı sarmalayıcıyı kullanır."""
    assert "run_in_threadpool" in _kaynak(api.api_sohbet), (
        "api_sohbet senkron döngüyü thread havuzuna DEVRETMİYOR")


def test_sohbet_dongusu_SENKRON_kalir():
    """Çiviler (v440 dahil) senkron sözleşmeye bağlıdır: `sohbet_dongusu` async'e ÇEVRİLMEZ —
    dönüşüm sessizce her sahte modeli koroutine borçlu bırakırdı."""
    assert not inspect.iscoroutinefunction(sohbet.sohbet_dongusu)


# =================================================================================================
# A2 — `olay_sorgu` KEYFİ YEREL DOSYA OKUYAMAZ (sızıntı sınıfı; tek istisna yok)
# =================================================================================================
def _olay_defteri_kur(n: int = 3) -> None:
    for i in range(n):
        store.append_jsonl("events.jsonl", {"ts": f"2026-09-08T10:00:0{i}+00:00",
                                            "level": "info", "event": f"olay_{i}"})


def _gizli_dosya(tmp_path, ad: str = "sahte_sir.txt") -> str:
    """SAHTE sır dosyası — hiçbir çivi gerçek `state/secrets.json`/`.env` okumaz."""
    p = tmp_path / ad
    p.write_text(SIZINTI_IMZASI + "\n")
    return str(p)


@pytest.mark.parametrize("kalip", ["read_text({y})", "read_csv_auto({y})", "read_blob({y})"])
def test_olay_sorgu_dosya_okuma_fonksiyonlarini_reddeder(kum, tmp_path, kalip):
    _olay_defteri_kur()
    yol = _gizli_dosya(tmp_path)
    sql = "SELECT * FROM " + kalip.format(y=f"'{yol}'")
    m = SahteModel(_arac(_tc("olay_sorgu", {"sql": sql})), _metin("ok"))
    out = sohbet.sohbet_dongusu("dosyayı oku", "S1", model_cagir=m)
    gorunen = _arac_ciktisi(m.cagrilar[1])
    assert SIZINTI_IMZASI not in gorunen, "DOSYA İÇERİĞİ MODELE GİTTİ: " + gorunen[:300]
    assert "REDDEDİLDİ" in gorunen, gorunen[:300]
    assert out["kaynaklar"] == [], "reddedilen sorgu kaynak atfı üretti"


@pytest.mark.parametrize("ad", ["sahte_sir.json", "sahte_sir.csv"])
def test_olay_sorgu_dizge_literali_kaynagini_reddeder(kum, tmp_path, ad):
    """`SELECT * FROM '<yol>'` bir tablo FONKSİYONU DEĞİLDİR — `read_\\w+` biçiminde bir ad kara
    listesi bu yolu kaçırırdı. Hedef sınıfı gerçektir: `state/secrets.json` tam da bu biçimle
    okunurdu. Motor düzeyindeki kapı kaçırmaz."""
    _olay_defteri_kur()
    yol = _gizli_dosya(tmp_path, ad)
    m = SahteModel(_arac(_tc("olay_sorgu", {"sql": f"SELECT * FROM '{yol}'"})), _metin("ok"))
    out = sohbet.sohbet_dongusu("dosyayı oku", "S1", model_cagir=m)
    gorunen = _arac_ciktisi(m.cagrilar[1])
    assert SIZINTI_IMZASI not in gorunen, "DOSYA İÇERİĞİ MODELE GİTTİ: " + gorunen[:300]
    assert "REDDEDİLDİ" in gorunen, gorunen[:300]
    assert out["kaynaklar"] == []


def test_taninmayan_uzantili_dizge_literali_dosya_OKUMAZ(kum, tmp_path):
    """ÖLÇÜLEN DAVRANIŞ, UYDURULAN DEĞİL (duckdb 1.5.5): tanınmayan uzantılı bir yol (`.txt`,
    uzantısız `/etc/passwd`) DuckDB'de hiç DOSYA sayılmaz — replacement scan devreye girmez ve
    sorgu bir ÇÖZÜMLEME (Binder) hatasıyla düşer. Çivinin hükmü SIZINTI YOK.

    TUR 2 (K5): bu satır eskiden `kaynaklar` İDDİASI TAŞIMIYORDU ve kardeş iki çivinin taşıdığı
    `== []` burada bilerek atlanmıştı — yani çivi kusuru ANLATIYOR ama ISIRMIYORdu. Ölçüldü: o
    iddia eklendiğinde KIRMIZI veriyordu, çünkü çözümleme hatası METİN olarak dönüyor ve
    `_arac_kos` normal dönüşü BAŞARI sayıp `atif=True` veriyordu — hiç veri okunmamış bir çağrı
    EDG-2026-086'nın uydurma sayımının PAYDASINA giriyordu."""
    _olay_defteri_kur()
    yol = _gizli_dosya(tmp_path, "sahte_sir.txt")
    m = SahteModel(_arac(_tc("olay_sorgu", {"sql": f"SELECT * FROM '{yol}'"})), _metin("ok"))
    out = sohbet.sohbet_dongusu("dosyayı oku", "S1", model_cagir=m)
    gorunen = _arac_ciktisi(m.cagrilar[1])
    assert SIZINTI_IMZASI not in gorunen, "DOSYA İÇERİĞİ MODELE GİTTİ: " + gorunen[:300]
    assert "REDDEDİLDİ" in gorunen, gorunen[:300]
    assert out["kaynaklar"] == [], f"SAHTE KAYNAK ATFI ÜRETİLDİ: {out['kaynaklar']}"


def test_olay_sorgu_NORMAL_select_calismaya_devam_eder(kum):
    """POZİTİF KONTROL: kapı meşru sorguyu kesmemeli. Bu çivi aynı zamanda aracın GERÇEKTEN
    koştuğunu ölçer — ret yollarını sınayan çiviler `gorunumu_kur` çağrısına hiç ulaşmıyordu."""
    _olay_defteri_kur(n=3)
    m = SahteModel(_arac(_tc("olay_sorgu", {"sql": "SELECT event FROM olaylar ORDER BY 1"})),
                   _metin("ok"))
    out = sohbet.sohbet_dongusu("olayları say", "S1", model_cagir=m)
    gorunen = _arac_ciktisi(m.cagrilar[1])
    assert "sorgu hatası" not in gorunen and "REDDEDİLDİ" not in gorunen, gorunen[:400]
    assert '"olay_0"' in gorunen or "olay_0" in gorunen, gorunen[:400]
    assert out["kaynaklar"] and out["kaynaklar"][0]["arac"] == "olay_sorgu", out["kaynaklar"]


def test_harici_erisim_kapandiktan_sonra_geri_ACILAMAZ(kum):
    """Ölçüldü (duckdb 1.5.5): `SET enable_external_access=true` çalışan bir veritabanında
    reddedilir. Kapının TEK YÖNLÜ olması, sonraki bir sorgunun ayarı geri açmasını imkânsız kılar."""
    import ops.olay_sorgu as _os_mod
    _olay_defteri_kur()
    con = _os_mod.baglanti_kur()
    try:
        defter = config.STATE / "events.jsonl"
        _os_mod.gorunumu_kur(con, defter, _os_mod.arsiv_dizini(defter))
        sohbet._harici_erisimi_kapat(con)
        assert con.execute("SELECT count(*) FROM olaylar").fetchone()[0] == 3
        with pytest.raises(Exception) as e:
            con.execute("SET enable_external_access=true")
        assert "external access" in str(e.value).lower(), str(e.value)
    finally:
        con.close()


def test_materyalizasyon_maliyeti_olculur_ve_tavanin_altinda(kum):
    """BEDEL ÖLÇÜLÜR: görünüm TEMBEL olduğu için satırlar kapı kapanmadan ÖNCE belleğe alınır.
    Kazanç (sızıntı sınıfı kapandı) ölçülüp bedel ölçülmezse körlük sessiz olurdu."""
    import ops.olay_sorgu as _os_mod
    defter = config.STATE / "events.jsonl"
    with defter.open("w") as f:
        for i in range(CANLI_OLAY_SATIRI):
            f.write(json.dumps({"ts": f"2026-09-0{(i % 7) + 1}T10:00:{i % 60:02d}+00:00",
                                "level": "info", "event": f"olay_{i % 40}",
                                "detail": "x" * 200}) + "\n")
    con = _os_mod.baglanti_kur()
    try:
        _os_mod.gorunumu_kur(con, defter, _os_mod.arsiv_dizini(defter))
        t0 = time.perf_counter()
        sohbet._harici_erisimi_kapat(con)
        sure = time.perf_counter() - t0
        assert con.execute("SELECT count(*) FROM olaylar").fetchone()[0] == CANLI_OLAY_SATIRI
    finally:
        con.close()
    assert sure < MATERYALIZE_TAVANI_S, (
        f"{CANLI_OLAY_SATIRI} satırın materyalizasyonu {sure:.3f} s sürdü "
        f"(tavan {MATERYALIZE_TAVANI_S} s) — sohbet aracı bu bedeli her sorguda öder")


# =================================================================================================
# A3 (+ TUR-2 K1) — SOHBET ONAYININ KÜNYESİ: yanıt ↔ defter TEK KAYNAK, `davranissal` DOKUNULMAZ
# =================================================================================================
def test_plan_onayi_kararinda_icra_eder_TRUE_ve_sohbet_notu(istemci, monkeypatch):
    """"davranış DEĞİŞMEZ" derken `icra` alanında plan onaylayan yanıt, operatörü "hiçbir şey
    olmadı" sanmaya sürüklerdi ve defterdeki karar kaydı KALICI olarak yanlış künye taşırdı.

    TUR 2 (K1): icra gerçeği `davranissal`a YAZILMAZ. O alanın anlamı "bir L1+ UYGULAMA KAPISI
    bu satırı okur mu"dur (`KAPI_OKUYAN_ONEKLER`, v240'ta çivili) ve `SO-…` kimliğini hiçbir kapı
    okumaz — pano tam o anlamı okuduğu için alanı eğmek panoya ölçülmüş bir YANLIŞ cümle
    kurdururdu. İcra AYRI alanla (`icra_eder`) söylenir; sonucu `icra_ok` taşır."""
    _seviye(monkeypatch, 0)
    oid = _oneri_yaz()
    from meridian import loop as _loop
    monkeypatch.setattr(_loop, "operator_onay_ver", lambda plan_id, **kw: {"ok": True})
    y = istemci.post(f"/api/approvals/{oid}", json={"decision": "approve", "reason": "uygun"})
    assert y.status_code == 200, y.text
    govde = y.json()
    assert govde["davranissal"] is False, "sohbet kimliğini hiçbir L1 kapısı okumaz: " + str(govde)
    assert govde["icra_eder"] is True and govde["icra_ok"] is True, govde
    assert govde["not"] == api.SOHBET_KARARI_NOT, govde.get("not")
    assert govde["icra"]["ok"] is True
    # ALAN ADLARI B2 UI'ININ SÖZLEŞMESİDİR — biçim değişmez.
    assert set(govde["oneri"]) == {"tur", "hedef", "gerekce", "oturum"}, govde["oneri"]


def test_alarm_ack_kararinda_da_icra_eder_TRUE(istemci, monkeypatch):
    _seviye(monkeypatch, 0)
    monkeypatch.setattr(notify, "inbox",
                        lambda limit=60: {"pending": 1, "ack_ts": None, "channel_configured": True,
                                          "groups": [{"token": "DATA_QUALITY", "n": 1,
                                                      "last_ts": "2026-09-07T10:00:00+00:00",
                                                      "message": "m"}]})
    oid = _oneri_yaz(tur="alarm_ack", hedef="DATA_QUALITY")
    monkeypatch.setattr(api, "_alarm_ack_uygula", lambda **kw: {"acked": True, "ok": True})
    govde = istemci.post(f"/api/approvals/{oid}",
                         json={"decision": "approve", "reason": "gördüm"}).json()
    assert govde["davranissal"] is False, govde
    assert govde["icra_eder"] is True and govde["not"] == api.SOHBET_KARARI_NOT, govde


def test_not_turu_KAYIT_KARARI_olarak_kalir(istemci, monkeypatch):
    """`not` türünün icrası YOKTUR — künyesi de kayıt künyesi kalmalı; aksi hâlde bu sefer TERS
    yönde yalan söylerdik."""
    _seviye(monkeypatch, 0)
    oid = _oneri_yaz(tur="not", hedef="", gerekce="MU'ya dikkat")
    govde = istemci.post(f"/api/approvals/{oid}",
                         json={"decision": "approve", "reason": "ok"}).json()
    assert govde["davranissal"] is False and govde["not"] == api.KAYIT_KARARI_NOT, govde
    assert govde["icra_eder"] is False and govde["icra_ok"] is False, govde
    assert govde["icra"]["icra"] == "yok", govde


@pytest.mark.parametrize("tur,hedef,beklenen", [("plan_onayi", "P-2026-09-07-MU", True),
                                                ("not", "", False)])
def test_yanit_ve_DEFTER_SATIRI_ayni_kunyeyi_tasir(istemci, monkeypatch, tur, hedef, beklenen):
    """TEK KAYNAK: yanıtın söylediği ile deftere yazılanın ayrışması, defteri sonradan okuyanı
    (insan ya da kapı) yanıltırdı. `davranissal` İKİSİNDE DE False'tur (K1) — ayrışan alan
    `icra_eder`dir ve o da iki yerde AYNI sözlükten okunur."""
    _seviye(monkeypatch, 0)
    oid = _oneri_yaz(tur=tur, hedef=hedef, gerekce="gerekçe")
    from meridian import loop as _loop
    monkeypatch.setattr(_loop, "operator_onay_ver", lambda plan_id, **kw: {"ok": True})
    govde = istemci.post(f"/api/approvals/{oid}", json={"decision": "approve"}).json()
    karar = [r for r in store.read_jsonl(api.APPROVALS_LEDGER)
             if r.get("id") == oid and "decision" in r]
    assert len(karar) == 1, karar
    assert karar[0]["davranissal"] is False is govde["davranissal"], (karar[0], govde)
    assert karar[0]["icra_eder"] is beklenen is govde["icra_eder"], (karar[0], govde)
    assert karar[0]["icra_ok"] is beklenen is govde["icra_ok"], (karar[0], govde)
    assert karar[0]["not"] == govde["not"], (karar[0].get("not"), govde.get("not"))


def test_icra_eden_turler_DONUK_sozlukten_ayrismaz(kum):
    """TEK KAYNAK: `SOHBET_ICRA_EDEN_TURLER`, `sohbet.ONERI_TURLERI` donuk demetinin ALT
    KÜMESİDİR. Yarın yeni bir tür eklenip burada unutulursa künye sessizce yanlışa döner — ve
    dışarıda kalan her türün GERÇEKTEN icrasız olduğu iddia değil ÖLÇÜMdür."""
    assert api.SOHBET_ICRA_EDEN_TURLER <= set(sohbet.ONERI_TURLERI), (
        api.SOHBET_ICRA_EDEN_TURLER - set(sohbet.ONERI_TURLERI))
    disarida = set(sohbet.ONERI_TURLERI) - set(api.SOHBET_ICRA_EDEN_TURLER)
    assert disarida == {"not"}, disarida
    for tur in sorted(disarida):
        assert api._sohbet_icra({"tur": tur, "hedef": ""})["icra"] == "yok", tur


def test_sohbet_disi_kayit_karari_notu_DEGISMEDI(istemci, monkeypatch):
    """Gevşetme sohbete ÖZGÜDÜR: `kayit:` uzayı hâlâ davranışsal DEĞİLDİR."""
    _seviye(monkeypatch, 0)
    govde = istemci.post("/api/approvals/kayit:skill_x:lean_in",
                         json={"decision": "approve"}).json()
    assert govde["davranissal"] is False and govde["not"] == api.KAYIT_KARARI_NOT, govde


# =================================================================================================
# A4 — KOTA HER AYAK ÖNCESİ ÖLÇÜLÜR (mesaj başına bir kez DEĞİL)
# =================================================================================================
def test_kota_dongu_icinde_dolunca_sonraki_ayak_cagrilmaz(kum):
    """Kota 119/120'de başlar; ilk ayak hakkı harcar ve tavanı doldurur. İkinci tur ÇAĞRILMAZ,
    cevap kotayı ADIYLA beyan eder ve O ANA KADARKİ turlar defter satırında KALIR."""
    _cagri_yaz(119)
    m = SahteModel(_arac(_tc("pano_ozeti", {})), _metin("ikinci tur cevabı"), ayak_kaydi=True)
    out = sohbet.sohbet_dongusu("panoyu özetle", "S1", model_cagir=m)
    assert len(m.cagrilar) == 1, f"kota dolmuşken {len(m.cagrilar)} ayak çağrıldı"
    assert "kota dolu" in out["cevap"] and "120/120" in out["cevap"], out["cevap"]
    assert len(out["turlar"]) == 1, out["turlar"]
    assert out["llm_dustu"] is False, "kota kapısı bir MODEL ARIZASI değildir"
    assert out["kota_bugun"] == 120, out["kota_bugun"]


def test_kota_dolmamissa_dongu_devam_eder(kum):
    """NEGATİF KONTROL: yeni kapı meşru çok-turlu sohbeti kesmemeli."""
    _cagri_yaz(1)
    m = SahteModel(_arac(_tc("pano_ozeti", {})), _metin("bitti"), ayak_kaydi=True)
    out = sohbet.sohbet_dongusu("panoyu özetle", "S1", model_cagir=m)
    assert len(m.cagrilar) == 2 and out["cevap"] == "bitti", (len(m.cagrilar), out["cevap"])


def test_zincir_ayagi_oncesi_de_kota_yeniden_olculur(kum, monkeypatch):
    """`_kapi_cagir` bir mesaj için zincirdeki modelleri SIRAYLA dener; kota ayak başına
    harcanır, dolayısıyla ayak başına da SORULMALIDIR."""
    from meridian import hermes
    monkeypatch.setattr(hermes, "_nous_headers", lambda: {"Authorization": "Bearer x"})
    monkeypatch.setenv("SOHBET_MODEL_ZINCIRI", "m-bir,m-iki,m-uc")
    _cagri_yaz(119)
    cagrilan: list[str] = []

    class _Yanit:
        status_code = 429

        def json(self):
            return {}

    def sahte_post(url, **kw):
        cagrilan.append(kw["json"]["model"])
        return _Yanit()

    monkeypatch.setattr(httpx, "post", sahte_post)
    out = sohbet._kapi_cagir([{"role": "user", "content": "selam"}], [])
    assert cagrilan == ["m-bir"], f"kota dolduktan sonra da ayak denendi: {cagrilan}"
    assert out["mesaj"] is None and out.get("kota_engeli"), out
    assert "kota dolu" in str(out.get("kota_engeli")), out.get("kota_engeli")


# =================================================================================================
# A5 — BOŞ ŞEMALI ARACA `null`/EKSİK ARGÜMAN GEÇERLİDİR
# =================================================================================================
@pytest.mark.parametrize("ham", [None, "null", ""])
def test_bos_semali_araca_null_arguman_calisir(kum, ham):
    """Zincirdeki free-tier modeller parametresiz araç için `arguments: null` gönderiyor
    (EDG-074 ailesi). Şema hiçbir alan GEREKTİRMİYORSA bu geçerli bir çağrıdır."""
    m = SahteModel(_arac(_tc("pano_ozeti", ham)), _metin("ok"))
    out = sohbet.sohbet_dongusu("pano özeti nedir", "S1", model_cagir=m)
    assert out["sema_disi_n"] == 0, _arac_ciktisi(m.cagrilar[1])[:300]
    assert out["kaynaklar"] and out["kaynaklar"][0]["arac"] == "pano_ozeti", out["kaynaklar"]
    assert "ŞEMA DIŞI" not in _arac_ciktisi(m.cagrilar[1])


def test_zorunlu_alanli_araca_null_arguman_HALA_sema_disi(kum):
    """NEGATİF KONTROL: gevşetme YALNIZ hiçbir şey gerektirmeyen şemalar içindir."""
    m = SahteModel(_arac(_tc("kart_oku", None)), _metin("ok"))
    out = sohbet.sohbet_dongusu("kartı oku", "S1", model_cagir=m)
    assert out["sema_disi_n"] == 1, _arac_ciktisi(m.cagrilar[1])[:300]


def test_anyof_semali_araca_null_arguman_HALA_sema_disi(kum):
    """`plan_oku` `anyOf` ile "ikisinden biri" der — `{}` o koşulu SAĞLAMAZ."""
    m = SahteModel(_arac(_tc("plan_oku", None)), _metin("ok"))
    out = sohbet.sohbet_dongusu("planı oku", "S1", model_cagir=m)
    assert out["sema_disi_n"] == 1, _arac_ciktisi(m.cagrilar[1])[:300]


# =================================================================================================
# A6 — `_defter_tarama` MUAFİYETİ SOHBET ÖNERİ SATIRINA DARALIR
# =================================================================================================
def test_kaynak_alanli_sohbet_DISI_satir_muaf_degildir(kum):
    """Muafiyet jenerikken, `kaynak` taşıyan ve `decision` taşımayan HERHANGİ bir bozuk satır
    sessizce eleniyordu — defterin kirliliği görünmez olurdu (Yasa 6 ruhu)."""
    store.append_jsonl(api.APPROVALS_LEDGER, {"id": "rev:x", "kaynak": "baska-uretici",
                                              "ts": "2026-09-08T00:00:00+00:00"})
    t = api._defter_tarama()
    assert (t["kararlar"].get("rev:x") or {}).get("karar") == "bozuk", t["kararlar"]


def test_sohbet_kimligi_TASIMAYAN_sohbet_kaynakli_satir_da_muaf_degildir(kum):
    """Muafiyetin İKİ koşulu vardır: kaynak sohbet OLACAK **ve** kimlik bir SOHBET ÖNERİSİ
    kimliği olacak. Elle düzenlenmiş/yarım yazılmış bir satır ikisini birden taşıyamaz."""
    store.append_jsonl(api.APPROVALS_LEDGER, {"id": "rev:y", "kaynak": sohbet.CAGRI_KIND,
                                              "ts": "2026-09-08T00:00:00+00:00"})
    t = api._defter_tarama()
    assert (t["kararlar"].get("rev:y") or {}).get("karar") == "bozuk", t["kararlar"]


def test_GERCEK_sohbet_oneri_satiri_hala_muaftir(kum):
    """POZİTİF KONTROL: daraltma öneriyi doğduğu anda "bozuk karar" saymamalı."""
    oid = _oneri_yaz()
    t = api._defter_tarama()
    assert oid not in (t["kararlar"] or {}), t["kararlar"]
    assert t["atfedilemeyen"] == 0, t


# =================================================================================================
# A7 — `_arac_oneri_yaz` İKİNCİ (SAVUNMACI) TUR KAPISI
# =================================================================================================
def test_oneri_yaz_ic_kapisi_semayi_ATLAYAN_cagriyi_reddeder(kum):
    """Şema `enum`u bu çağrıyı zaten eler; bu yüzden `sohbet_dongusu` üzerinden gelen hiçbir
    çivi iç kapının gövdesine ULAŞMIYORDU (satır silinse kimse kırmızı vermezdi). Doğrudan
    çağrı kapıyı ADIYLA ısırır."""
    with pytest.raises(sohbet.AracReddi) as e:
        sohbet._arac_oneri_yaz({"tur": "emir_ver", "hedef": "MU", "gerekce": "model istedi"},
                               {"oturum": "S1"})
    assert "DONUK" in str(e.value), str(e.value)
    assert store.read_jsonl(sohbet.ONAY_DEFTERI) == [], "reddedilen öneri deftere YAZILDI"


def test_oneri_yaz_ic_kapisi_gecerli_turu_GECIRIR(kum):
    """NEGATİF KONTROL: kapı donuk sözlükteki türü kesmez."""
    store.append_jsonl("trade_plans.jsonl", {"id": "P-1", "ticker": "MU"})
    sonuc = sohbet._arac_oneri_yaz({"tur": "plan_onayi", "hedef": "P-1", "gerekce": "bak"},
                                   {"oturum": "S1"})
    assert json.loads(sonuc)["yazildi"] is True


# =================================================================================================
# A8 — GELEN KUTUSUNDAKİ SOHBET GEREKÇESİ KIRPILMAZ
# =================================================================================================
def test_sohbet_onerisinin_gerekcesi_gelen_kutusunda_TAM_gider(istemci, monkeypatch):
    """Gerekçe operatörün karar VERECEĞİ metindir; 200 karakterde kesilmesi kararı sakat
    bırakırdı. Yazan taraf zaten 800'de kesiyor (tek kaynak: `_arac_oneri_yaz`)."""
    _seviye(monkeypatch, 0)
    uzun = "G" * 600
    _oneri_yaz(gerekce=uzun)
    kutu = istemci.get("/api/approvals").json()["inbox"]
    oge = next(o for o in kutu if o.get("type") == "sohbet_onerisi")
    assert oge["evidence"] == uzun, (len(oge["evidence"]), oge["evidence"][:60])


def test_esc_ev_SOHBET_DISI_satirlarda_hala_200de_kirpar(kum):
    """BEDEL: kırpma kalkarsa gelen kutusu zarfı büyür. Gevşetme sohbet satırlarına ÖZGÜDÜR;
    ortak yardımcı DEĞİŞMEDİ."""
    assert len(api.esc_ev("x" * 500)) == 200


# =================================================================================================
# A9 — `kota_durumu()['dolu']`: `_kota_cevabi(kota) is not None` İLE BİREBİR AYNI HÜKÜM (TEK KAYNAK)
# =================================================================================================
# B2 UI incelemesi: pano `dolu === true` iken sohbet girişini kapatıyor. `dolu` ayrı bir eşik
# hesabıyla YAZILIRSA (ör. `bugun >= tavan` burada TEKRAR yazılırsa) döngünün gerçek kapı kararı
# (`_kota_cevabi`) ile UI'ın kapı kararı sessizce AYRIŞABİLİR — döngü hâlâ çağırırken UI kapanır
# ya da tersi. Tek kaynak: `dolu` `_kota_cevabi`nin KENDİSİNİ çağırarak türer.
def test_kota_durumu_dolu_ALTINDAYKEN_false_ve_kota_cevabi_None(kum):
    """Tavanın altında: `dolu` False, `_kota_cevabi(k)` None — ikisi AYNI hükmün iki yüzü."""
    _cagri_yaz(5)
    k = sohbet.kota_durumu()
    assert k["dolu"] is False, k
    assert sohbet._kota_cevabi(k) is None, sohbet._kota_cevabi(k)


def test_kota_durumu_dolu_TAVANDAYKEN_true_ve_kota_cevabi_dolu(kum):
    """Sayaç tavanda: `dolu` True **ve** `_kota_cevabi(k)` None DEĞİL — BİREBİR AYNI HÜKÜM."""
    _cagri_yaz(120)
    k = sohbet.kota_durumu()
    assert k["dolu"] is True, k
    assert sohbet._kota_cevabi(k) is not None, "dolu True ama _kota_cevabi None döndü"


def test_kota_durumu_KAYNAGI_kota_cevabiyi_DOGRUDAN_CAGIRIR(kum):
    """YAPISAL ÇİVİ (Tek-kaynak yasası): `dolu` ATAMASININ KENDİSİ `_kota_cevabi(` çağrısını
    TAŞIMALI. Aranan dizge docstring/yorum METNİNDE de geçebileceğinden (ki bu çiviyi ISIRMAZ),
    hedef genel kaynak metni değil ATAMA SATIRININ KENDİSİDİR — `["dolu"] = _kota_cevabi(`
    kalıbı yalnız gerçek çağrıda oluşur."""
    kaynak = _kaynak(sohbet.kota_durumu)
    assert re.search(r'\["dolu"\]\s*=\s*_kota_cevabi\(', kaynak), (
        "kota_durumu() 'dolu' atamasında _kota_cevabi DOĞRUDAN çağrılmıyor:\n" + kaynak)


def test_api_sohbet_kota_dolu_alanini_OLDUGU_GIBI_tasir(istemci):
    """`GET /api/sohbet/kota` gövdesi `kota_durumu()`nun TA KENDİSİDİR — `dolu` ek işlem
    GEREKMEDEN aynen taşınır; bu ölçüm `api_sohbet_kota`ya dokunulmadığı iddiasını kanıtlar."""
    _cagri_yaz(120)
    govde = istemci.get("/api/sohbet/kota").json()
    assert govde["dolu"] is True, govde
    assert govde["bugun"] == 120 and govde["tavan"] == 120, govde


# =================================================================================================
# TUR 2 — çekişmeli incelemenin ayakta bıraktığı 7 kök (K1..K7)
# =================================================================================================
#
# TUR-1 DÜZELTMELERİNİN KENDİSİ ÜÇ KUSUR AÇTI ve üçü de ölçüldü: A3 `davranissal`ı anlamından
# etti (K1), A1 eşzamanlılığı GERÇEK kıldı ve kimlik/kota yarışlarını açtı (K2), A2 aynı sınıfın
# kardeşini (`bar_sorgu`) ve kaynak tavanlarını (K3/K4) yerinde bıraktı.


# ---- K1 — SOHBET KARAR KÜNYESİ: `davranissal` DOKUNULMAZ, icra AYRI ALANLA söylenir -------------
def test_reddedilen_sohbet_onerisi_ICRA_ETMEZ_ve_kunyesi_RED_der(istemci, monkeypatch):
    """RET HİÇBİR ŞEY İCRA ETMEZ. Eskiden künye YALNIZ `tur`dan türüyordu ve `decision` gövdeden
    OKUNMADAN ÖNCE hesaplanıyordu: `reject` kararı da "onay İCRA eder" cümlesini alıyordu. Defter
    SALT-EKLEMEDİR, yani o cümle KALICI — sicili yarın okuyan, hiçbir şey yapmamış bir satırı
    "bir kapı açtı" diye okurdu."""
    _seviye(monkeypatch, 0)
    oid = _oneri_yaz()
    from meridian import loop as _loop
    monkeypatch.setattr(_loop, "operator_onay_ver",
                        lambda plan_id, **kw: pytest.fail("RET İCRA ETTİ: " + str(plan_id)))
    govde = istemci.post(f"/api/approvals/{oid}",
                         json={"decision": "reject", "reason": "olmaz"}).json()
    assert govde["icra_eder"] is False and govde["icra_ok"] is False, govde
    assert govde["not"] == api.SOHBET_RED_NOT, govde.get("not")
    assert "icra" not in govde, "ret yanıtı bir icra sonucu taşıdı: " + str(govde.get("icra"))
    satir = _karar_satiri(oid)
    assert satir["icra_eder"] is False and satir["not"] == api.SOHBET_RED_NOT, satir


def test_ICRA_DUSERSE_defter_satiri_ICRA_ETTIGINI_IDDIA_ETMEZ(istemci, monkeypatch):
    """`loop.operator_onay_ver` İSTİSNA ATMAZ: plan defterde yoksa 404, NO_GO/REVIEW-dışı/HALT/
    pozisyon çakışmasında 409 ile `{"ok": False}` döner. Satır icradan ÖNCE yazıldığı sürece
    künye sonucu bilemezdi ve `ok:false` dönen bir icra sicilde KALICI olarak "İCRA eder" diye
    dururdu. Şimdi: `icra_eder` True KALIR (denendi) ama `icra_ok` False ve künye düşüşü ADIYLA
    beyan eder — üç hâl (denenmedi · başardı · düştü) iki boolean'la ayrışır."""
    _seviye(monkeypatch, 0)
    oid = _oneri_yaz()
    from meridian import loop as _loop
    monkeypatch.setattr(_loop, "operator_onay_ver",
                        lambda plan_id, **kw: {"ok": False, "kod": 409,
                                               "neden": "NO_GO onaylanamaz"})
    govde = istemci.post(f"/api/approvals/{oid}", json={"decision": "approve"}).json()
    assert govde["icra_eder"] is True and govde["icra_ok"] is False, govde
    assert govde["icra"]["ok"] is False and govde["icra"]["kod"] == 409, govde["icra"]
    satir = _karar_satiri(oid)
    assert satir["icra_ok"] is False, satir
    assert "icra DÜŞTÜ" in satir["not"] and "409" in satir["not"], satir["not"]
    assert "NO_GO onaylanamaz" in satir["not"], satir["not"]
    assert satir["not"] == govde["not"], (satir["not"], govde["not"])


def test_ICRA_ISTISNA_ATSA_BILE_karar_defterde_KALIR(istemci, monkeypatch):
    """Satır icradan SONRA yazıldığı için istisna bu kez KARARI kaybettirebilirdi. Kayıp sessiz
    olmaz: yanıt `ok:false` ile döner, künye "icra DÜŞTÜ" der ve satır deftere YAZILIR."""
    _seviye(monkeypatch, 0)
    oid = _oneri_yaz()
    from meridian import loop as _loop

    def _patlat(plan_id, **kw):
        raise RuntimeError("broker aynası düştü")

    monkeypatch.setattr(_loop, "operator_onay_ver", _patlat)
    y = istemci.post(f"/api/approvals/{oid}", json={"decision": "approve"})
    assert y.status_code == 200, y.text
    govde = y.json()
    assert govde["icra_eder"] is True and govde["icra_ok"] is False, govde
    assert govde["icra"]["ok"] is False and "RuntimeError" in str(govde["icra"]["neden"]), govde
    satir = _karar_satiri(oid)
    assert "icra DÜŞTÜ" in satir["not"], satir["not"]


def test_defter_satiri_ICRADAN_SONRA_yazilir(istemci, monkeypatch):
    """SIRA ÖLÇÜLÜR, İDDİA EDİLMEZ: icra çağrısı koştuğu ANDA defterde bu kimliğe ait bir KARAR
    satırı olmamalı. Sıra ters olsaydı künye sonucu bilemezdi (yukarıdaki iki çivinin ön koşulu)."""
    _seviye(monkeypatch, 0)
    oid = _oneri_yaz()
    gorulen: list[int] = []
    from meridian import loop as _loop

    def _olc(plan_id, **kw):
        gorulen.append(len([r for r in store.read_jsonl(api.APPROVALS_LEDGER)
                            if r.get("id") == oid and "decision" in r]))
        return {"ok": True}

    monkeypatch.setattr(_loop, "operator_onay_ver", _olc)
    istemci.post(f"/api/approvals/{oid}", json={"decision": "approve"})
    assert gorulen == [0], f"icra anında defterde zaten {gorulen} karar satırı vardı"
    assert len([r for r in store.read_jsonl(api.APPROVALS_LEDGER)
                if r.get("id") == oid and "decision" in r]) == 1


def test_SOHBET_satiri_davranissal_alanini_ASLA_TRUE_yapmaz(istemci, monkeypatch):
    """`davranissal`ın anlamı `KAPI_OKUYAN_ONEKLER`e BAĞLIDIR ve o küme v240'ta çivilidir; `SO-…`
    kimliği o kümede DEĞİLDİR. Pano (`KararPaneli.tsx`, `OnayDefteri.tsx`, `web/app.js`) alanı tam
    o anlamda okuyor — eğmek panoya ölçülmüş bir YANLIŞ cümle kurdururdu. Dört kombinasyon da
    ölçülür (tür × karar)."""
    _seviye(monkeypatch, 0)
    from meridian import loop as _loop
    monkeypatch.setattr(_loop, "operator_onay_ver", lambda plan_id, **kw: {"ok": True})
    assert not any(sohbet.oneri_kimligi_mi(o) for o in api.KAPI_OKUYAN_ONEKLER)
    for tur, hedef in (("plan_onayi", "P-2026-09-07-MU"), ("not", "")):
        for karar in ("approve", "reject"):
            oid = _oneri_yaz(tur=tur, hedef=hedef, gerekce="g")
            govde = istemci.post(f"/api/approvals/{oid}", json={"decision": karar}).json()
            assert govde["davranissal"] is False, (tur, karar, govde)
            assert _karar_satiri(oid)["davranissal"] is False, (tur, karar)


def test_kunye_sozlugu_UC_HALI_AYRI_cumlelerle_soyler():
    """TEK KAYNAK + AYRIŞMA: üç künye BİRBİRİNDEN farklı olmalı, yoksa defteri okuyan ret ile
    onayı ayıramaz. `SOHBET_KARAR_ALANLARI` de donuk: pano/sayım o iki adı okur."""
    kunyeler = [api.SOHBET_KARARI_NOT, api.SOHBET_RED_NOT, api.KAYIT_KARARI_NOT]
    assert len(set(kunyeler)) == 3, kunyeler
    assert "REDDEDİLDİ" in api.SOHBET_RED_NOT and "icra YOK" in api.SOHBET_RED_NOT
    assert api.SOHBET_KARAR_ALANLARI == ("icra_eder", "icra_ok"), api.SOHBET_KARAR_ALANLARI


def _karar_satiri(oid: str) -> dict:
    satirlar = [r for r in store.read_jsonl(api.APPROVALS_LEDGER)
                if r.get("id") == oid and "decision" in r]
    assert len(satirlar) == 1, satirlar
    return satirlar[0]


# ---- K2 — A1'İN AÇTIĞI GERÇEK EŞZAMANLILIĞIN BEDELİ: SERİLEŞTİRME + KİLİTLER --------------------
#: K2 ölçümlerinde sayım ile ekleme ARASINA enjekte edilen gecikme. Yarışın penceresi gerçekte
#: mikrosaniyeliktir; onu GÖRÜNÜR yapmadan "kilit çalışıyor" demek ölçüm değil temenni olurdu.
YARIS_PENCERESI_S = 0.25


class _GecikmeliSayim:
    """`store.read_jsonl` sarmalayıcısı: onay defteri İLK KEZ okunduğunda gecikir.

    Yarışın penceresi "say" ile "ekle" arasındadır. Kilit VARSA ikinci iplik bu pencereye hiç
    giremez (birinci bitene kadar bekler) ve farklı bir sayım görür; kilit YOKSA ikisi de aynı
    sayımı okur ve AYNI `SO-…` kimliğini üretir. Gecikme yalnız ilk okumaya konur, yoksa
    kilitli koşum da gereksizce iki kat yavaşlardı."""

    def __init__(self, gercek, saniye: float = YARIS_PENCERESI_S):
        self._gercek = gercek
        self._saniye = saniye
        self._geciktirildi = False

    def __call__(self, ad, *a, **kw):
        sonuc = self._gercek(ad, *a, **kw)
        if ad == sohbet.ONAY_DEFTERI and not self._geciktirildi:
            self._geciktirildi = True
            time.sleep(self._saniye)
        return sonuc


def _paralel_oneri_yaz(monkeypatch, kilitsiz: bool = False) -> list[str]:
    """İki iplikten `_arac_oneri_yaz` — üretilen öneri kimliklerini döndürür."""
    import threading
    store.append_jsonl("trade_plans.jsonl", {"id": "P-1", "ticker": "MU"})
    monkeypatch.setattr(store, "read_jsonl", _GecikmeliSayim(store.read_jsonl))
    if kilitsiz:
        import contextlib

        @contextlib.contextmanager
        def _kilitsiz(ad):
            yield None

        monkeypatch.setattr(store, "file_lock", _kilitsiz)
    hatalar: list[BaseException] = []

    def _yaz(i: int) -> None:
        try:
            sohbet._arac_oneri_yaz({"tur": "plan_onayi", "hedef": "P-1", "gerekce": f"g{i}"},
                                   {"oturum": f"S{i}"})
        except BaseException as e:      # sessiz-yutma: iplikteki istisna ANA ipliğe taşınır ve orada YÜKSELTİLİR — yutulmaz, yalnız taşınır (thread gövdesinde raise etmek sessizce kaybolurdu)
            hatalar.append(e)

    iplikler = [threading.Thread(target=_yaz, args=(i,)) for i in (1, 2)]
    for t in iplikler:
        t.start()
    for t in iplikler:
        t.join(timeout=30)
    assert not hatalar, hatalar
    return [r["id"] for r in store.read_jsonl(sohbet.ONAY_DEFTERI)
            if r.get("kaynak") == sohbet.CAGRI_KIND]


def test_iki_eszamanli_oneri_yazimi_FARKLI_kimlik_alir(kum, monkeypatch):
    """KİMLİK ÇAKIŞMASI YANLIŞ PLANIN İCRASIDIR. `oneri_satiri` defteri TERSTEN tarayıp SON
    eşleşeni döndürür: iki öneri aynı `SO-…` kimliğini alırsa operatörün gelen kutusunda GÖRDÜĞÜ
    öneriyi onaylaması ÖTEKİNİN hedefini icra ettirir (`loop.operator_onay_ver`in dedup'ı yalnız
    AYNI planın ikinci silahlanmasını engeller, YANLIŞ planı değil)."""
    kimlikler = _paralel_oneri_yaz(monkeypatch)
    assert len(kimlikler) == 2, kimlikler
    assert len(set(kimlikler)) == 2, f"İKİ ÖNERİ AYNI KİMLİĞİ ALDI: {kimlikler}"


def test_MUTASYON_kilit_kaldirilinca_ayni_kimlik_uretilir(kum, monkeypatch):
    """ÇİVİ YEŞİLİ KANIT DEĞİLDİR: yukarıdaki çivinin GERÇEKTEN kilidi ısırdığını, kilidi
    kaldırıp aynı ölçümü tekrarlayarak gösteriyoruz. `store.file_lock` boş bir bağlam yöneticisiyle
    değiştirildiğinde iki iplik aynı sayımı okur ve AYNI kimlik iki kez deftere düşer."""
    kimlikler = _paralel_oneri_yaz(monkeypatch, kilitsiz=True)
    assert len(kimlikler) == 2, kimlikler
    assert len(set(kimlikler)) == 1, (
        "MUTASYON ISIRMADI: kilit kaldırıldığı hâlde kimlikler ayrıştı — "
        f"çakışma penceresi ölçülemedi: {kimlikler}")


def test_iki_eszamanli_sohbet_turu_ORTUSMEZ_ikincisi_MESGUL_doner(kum):
    """İKİ SOHBET TURU ÖRTÜŞMEZ. `run_in_threadpool`dan beri iki `POST /api/sohbet` gerçekten
    paralel koşuyor; tek operatörlü bu yüzeyde eşzamanlılığın kazancı yok, kaybı VAR (kimlik
    yarışı + kota TOCTOU).

    TUR 3 (M2): dışlama artık SIRAYA SOKARAK değil REDDEDEREK sağlanır — ikinci istek kilitte
    park edip anyio iş havuzunun jetonunu tutmaz, `mesgul` cevabıyla döner. Ölçülen şey aynı:
    ikinci turun gövdesi birinci sürerken KOŞMAZ (model hiç çağrılmaz) ve deftere tek satır düşer.
    Yarış penceresi temenniyle değil OLAYLA açılır: ikinci çağrı, birincinin modeli gerçekten
    kilidin içine girdiğini bildirene kadar bekler."""
    import threading
    girdi = threading.Event()
    ikinci_model_cagrildi: list[int] = []
    sonuclar: dict[str, dict] = {}

    def _yavas_model(mesajlar, araclar):
        girdi.set()
        time.sleep(YARIS_PENCERESI_S)
        return _metin("birinci tur")

    def _asla(mesajlar, araclar):
        ikinci_model_cagrildi.append(1)
        return _metin("bu cevap ASLA üretilmemeliydi")

    def _birinci() -> None:
        sonuclar["1"] = sohbet.sohbet_dongusu("soru 1", "S1", model_cagir=_yavas_model)

    def _ikinci() -> None:
        assert girdi.wait(timeout=10), "birinci tur kilide hiç girmedi — ölçüm penceresi açılmadı"
        sonuclar["2"] = sohbet.sohbet_dongusu("soru 2", "S2", model_cagir=_asla)

    iplikler = [threading.Thread(target=_birinci), threading.Thread(target=_ikinci)]
    for t in iplikler:
        t.start()
    for t in iplikler:
        t.join(timeout=30)
    assert not any(t.is_alive() for t in iplikler), "sohbet turu 30 s'de bitmedi (kilit park etti?)"
    assert set(sonuclar) == {"1", "2"}, sonuclar
    assert sonuclar["2"].get("mesgul") is True, (
        "İKİNCİ TUR SIRAYA GİRDİ: kilit `blocking=False` alınmıyor — bekleyen iplik anyio iş "
        f"havuzunun jetonunu tutar: {sonuclar['2']}")
    assert ikinci_model_cagrildi == [], "MEŞGUL DÖNÜŞTE MODEL ÇAĞRILDI — kota boşa harcandı"
    assert not sonuclar["1"].get("mesgul"), sonuclar["1"]
    satirlar = store.read_jsonl(sohbet.SOHBET_DEFTERI)
    assert len(satirlar) == 1, f"MEŞGUL cevabı deftere yazıldı (ölçüm paydası kirlendi): {satirlar}"
    assert satirlar[0]["oturum"] == "S1", satirlar


def test_sohbet_govdesi_KILIT_ALTINDA_cagrilir():
    """YAPISAL ÇİVİ (tek-kaynak): gövdenin tek çağrı yeri `sohbet_dongusu`nun kilitli bloğudur.
    İkinci bir doğrudan çağrı yolu açılırsa serileştirme sessizce kaybolurdu.

    TUR 3 (M2): kilit BLOKLAMADAN alınır ve `finally` ile bırakılır — `release` bir istisna
    yolunda atlanırsa sohbet yüzeyi kalıcı olarak "meşgul" kalırdı (kendi kendini kilitleyen
    arıza, hiçbir davranışsal çivinin tek koşumda göremeyeceği sınıf)."""
    kaynak = _kaynak(sohbet.sohbet_dongusu)
    assert "_SOHBET_KILIDI.acquire(blocking=False)" in kaynak, kaynak
    assert re.search(r"try:\s*\n\s*return _sohbet_turu\(", kaynak), kaynak
    assert re.search(r"finally:\s*\n\s*_SOHBET_KILIDI\.release\(\)", kaynak), kaynak


def test_defter_appendleri_KILIT_ALTINDA():
    """`store.append_jsonl` çıplak `open(path, "a")`dır ve sohbet satırı (mesaj + 20.000 karakterlik
    cevap) varsayılan metin tamponunu aşıp birden çok `write()`e bölünebilir — iki yazıcı satırları
    iç içe geçirirse o satır ölçülemez hâle gelir. İki append de kilit altındadır."""
    assert re.search(r"with store\.file_lock\(SOHBET_DEFTERI\):\s*\n\s*store\.append_jsonl\(",
                     _kaynak(sohbet._kaydet)), _kaynak(sohbet._kaydet)
    assert "with store.file_lock(ONAY_DEFTERI):" in _kaynak(sohbet._arac_oneri_yaz)
    assert "with store.file_lock(APPROVALS_LEDGER):" in _kaynak(api.api_approve)


# ---- K3 — `bar_sorgu` ARACI CANLIDA HİÇ ÇALIŞMIYORDU: üç kol da GERÇEKTEN koşar ------------------
#: Sentetik bar arşivi: dört seans, ortada BİR eksik gün (`bosluk` pozitif kontrolü) ve ölçek
#: değişimi (`dikis` pozitif kontrolü). Tarihler UYDURMA DEĞİL, çivinin kendi takvimidir: seans
#: kümesi de span de aşağıda AYNI listeden türer (tek kaynak).
BAR_SEANSLARI = ("2026-07-01", "2026-07-02", "2026-07-03", "2026-07-06")
#: Arşivde barı OLMAYAN seans — `bosluk` bu günü bulmalı.
BAR_EKSIK_GUN = "2026-07-03"
BAR_SPAN = ("2026-01-01", "2026-12-31")


def _bar_arsivi_kur(sembol: str = "mu") -> "object":
    """`state/barlar/<sembol>.parquet` — `ops.bar_arsivle`ın yerleşimi (sembol dosya ADINDAN gelir).

    Parquet DuckDB ile yazılır: gerçek yazıcıyı (`bar_arsivle.main`) çağırmak ağa/CSV önbelleğine
    bağlanırdı ve bu çivi ARACIN kendisini ölçüyor, yazıcıyı değil."""
    import duckdb

    import ops.bar_arsivle as _ba
    dizin = config.STATE / _ba.VARSAYILAN_HEDEF_ALT
    dizin.mkdir(parents=True, exist_ok=True)
    yol = dizin / f"{sembol}.parquet"
    satirlar = []
    for i, gun in enumerate(g for g in BAR_SEANSLARI if g != BAR_EKSIK_GUN):
        olcek = 1.0 if i < 1 else 2.0     # ilk bardan sonra DEĞİŞİR → `dikis` bir satır döndürür
        satirlar.append(f"(DATE '{gun}', 10.0, 11.0, 9.0, 10.5, 1000, 'sahte', {olcek})")
    sutunlar = ", ".join(_ba.SUTUNLAR)
    con = duckdb.connect()
    try:
        con.execute(f"COPY (SELECT * FROM (VALUES {', '.join(satirlar)}) AS t({sutunlar})) "
                    f"TO '{yol}' (FORMAT PARQUET)")
    finally:
        con.close()
    return yol


def _takvimi_sabitle(monkeypatch) -> None:
    """XNYS takvimini çiviye sabitler — `pandas_market_calendars`ın kurulu olup olmaması bu
    ölçümün sonucunu DEĞİŞTİRMEMELİ (aynı test iki makinede iki sonuç verirdi)."""
    from meridian.adapters import data as _data
    monkeypatch.setattr(_data, "_sessions", lambda: frozenset(BAR_SEANSLARI))
    monkeypatch.setattr(_data, "_SESSION_SPAN", BAR_SPAN)


def _bar_cagir(sorgu: str, **ek) -> tuple[dict, str]:
    """Aracı SOHBET DÖNGÜSÜ ÜZERİNDEN çağırır (kaynak atfı da ölçülsün) → (defter satırı, çıktı)."""
    m = SahteModel(_arac(_tc("bar_sorgu", {"sorgu": sorgu, **ek})), _metin("ok"))
    out = sohbet.sohbet_dongusu(f"bar {sorgu}", "S1", model_cagir=m)
    return out, _arac_ciktisi(m.cagrilar[1])


def test_bar_sorgu_kapsam_GERCEKTEN_kosar(kum):
    """`gorunum_sql` ÇIPLAK bir SELECT metnidir, görünüm DEĞİL. Eski gövde onu koşup ATIYOR, sonra
    `… FROM barlar` diye soruyordu → `CatalogException: Table with name barlar does not exist`.
    Araç canlıda HİÇ çalışmıyordu ve tek çivisi yoktu (`grep bar_sorgu tests/` → 0)."""
    _bar_arsivi_kur()
    out, gorunen = _bar_cagir("kapsam")
    assert "sorgu hatası" not in gorunen and "REDDEDİLDİ" not in gorunen, gorunen[:400]
    assert "MU" in gorunen, gorunen[:400]
    assert out["kaynaklar"] and out["kaynaklar"][0]["arac"] == "bar_sorgu", out["kaynaklar"]


def test_bar_sorgu_dikis_GERCEKTEN_kosar(kum):
    _bar_arsivi_kur()
    out, gorunen = _bar_cagir("dikis")
    assert "sorgu hatası" not in gorunen and "REDDEDİLDİ" not in gorunen, gorunen[:400]
    assert "MU" in gorunen, gorunen[:400]
    assert out["kaynaklar"], out["kaynaklar"]


def test_bar_sorgu_bosluk_GERCEKTEN_kosar_ve_EKSIK_GUNU_bulur(kum, monkeypatch):
    """`bosluk` kolu canlıda HER ZAMAN düşüyordu: `sorgu_bosluk(..., span=None)` çağrılıyor ve
    fonksiyonun ilk satırı `lo, hi = span` → `TypeError: cannot unpack non-iterable NoneType`.
    Span'in kaynağı `takvim_yukle`dir ve o çağrı aynı zamanda sorgunun ihtiyaç duyduğu `seanslar`
    geçici tablosunu kurar — CLI ile AYNI sıra (tek kaynak)."""
    _bar_arsivi_kur()
    _takvimi_sabitle(monkeypatch)
    out, gorunen = _bar_cagir("bosluk")
    assert "sorgu hatası" not in gorunen and "REDDEDİLDİ" not in gorunen, gorunen[:400]
    assert BAR_EKSIK_GUN in gorunen, f"eksik seans bulunamadı: {gorunen[:400]}"
    assert out["kaynaklar"], out["kaynaklar"]


def test_bar_sorgu_TAKVIM_olculemezse_HUKUM_VERMEZ_ve_atif_uretmez(kum, monkeypatch):
    """"0 eksik" basmak bilmediğimizi bilir gibi göstermek olurdu (CLI'nin rc 4 beyanının aynısı).
    "ölçülemedi" de ATIFSIZ döner: hiç veri okunmadı."""
    _bar_arsivi_kur()
    from meridian.adapters import data as _data
    monkeypatch.setattr(_data, "_sessions", lambda: frozenset())
    monkeypatch.setattr(_data, "_SESSION_SPAN", ())
    out, gorunen = _bar_cagir("bosluk")
    assert "ölçülemedi" in gorunen and "hüküm VERMEZ" in gorunen, gorunen[:400]
    assert out["kaynaklar"] == [], f"SAHTE KAYNAK ATFI: {out['kaynaklar']}"


def test_bar_sorgu_ARSIV_YOKSA_atif_uretmez(kum):
    """Arşiv yoksa "veri yok" DEĞİL "ölçülemedi" denir — ve metin dönüşü `_arac_kos`ta BAŞARI
    sayılıp kaynak atfı üretmemeli."""
    out, gorunen = _bar_cagir("kapsam")
    assert "ölçülemedi" in gorunen and "parquet yok" in gorunen, gorunen[:300]
    assert out["kaynaklar"] == [], out["kaynaklar"]


def _kapi_casusu(monkeypatch) -> list[str]:
    """`_harici_erisimi_kapat` çağrılarını sayar (gerçeği çağırmaya devam eder — pozitif kontrol
    kolu ölmesin). Dönen liste her çağrı için bir öğe taşır."""
    cagrilar: list[str] = []
    gercek = sohbet._harici_erisimi_kapat

    def _casus(con):
        cagrilar.append("olaylar")
        return gercek(con)

    monkeypatch.setattr(sohbet, "_harici_erisimi_kapat", _casus)
    return cagrilar


@pytest.mark.parametrize("sorgu", ["kapsam", "dikis", "bosluk"])
def test_bar_sorgu_HARICI_ERISIM_kapisini_CAGIRMAZ_ve_kol_YINE_KOSAR(kum, monkeypatch, sorgu):
    """TUR 3 / M1 — GEREKSİZ BEDEL KALDIRILDI (yeniden inceleme tavsiyesi, 2026-09-08).

    Kapının kazancı bu araçta ÖLÇÜLDÜ ve SIFIR: `_arac_bar_sorgu`ya modelden giren her girdi
    sayıldı — `sorgu` beyaz listeden dal seçer (`SORGULAR` enum'u), `sembol`/`ay` bağlı parametre
    olarak gider, `n` `int()`e zorlanır, görünüm metni dosya sistemi glob'undan gelir. Modelin
    denetimindeki HİÇBİR metin bu bağlantının SQL'ine ulaşmaz. Karşılığında ödenen bedel ise
    büyüyor: `barlar` `read_parquet` üstünde TEMBEL bir görünümdür ve kapı kapanmadan önce
    MATERYALİZE edilmek zorundaydı — yani her çağrı, aylık büyüyen arşivin tamamını K4'ün
    `memory_limit='512MB'` bütçesinden yiyordu (bir `min/max/count` bile olsa).

    ASIL KAPI `test_bar_sorgu_semasinda_SERBEST_SQL_alani_YOK`tur: yarın bir `sql` alanı eklendiği
    gün o çivi öter ve kapı O GÜN, ölçülmüş bir gerekçeyle geri konur.

    ÖLÇÜM İKİ AYAKLI: (a) kapı GERÇEKTEN çağrılmıyor, (b) kol yine de GERÇEK sonuç döndürüyor —
    "hiç koşmuyor" ile "kapısız koşuyor" karışmasın."""
    _bar_arsivi_kur()
    if sorgu == "bosluk":
        _takvimi_sabitle(monkeypatch)
    cagrilar = _kapi_casusu(monkeypatch)
    out, gorunen = _bar_cagir(sorgu)
    assert cagrilar == [], (
        "bar_sorgu HÂLÂ materyalize ediyor: kazancı sıfır ölçülen kapı arşivin tamamını "
        f"belleğe alıyor ({cagrilar})")
    assert "sorgu hatası" not in gorunen and "REDDEDİLDİ" not in gorunen, gorunen[:400]
    assert "MU" in gorunen, gorunen[:400]
    assert out["kaynaklar"] and out["kaynaklar"][0]["arac"] == "bar_sorgu", out["kaynaklar"]


def test_olay_sorgu_HARICI_ERISIM_kapisini_HALA_CAGIRIR(kum, monkeypatch):
    """M1'İN KAPSAMI ÖLÇÜLÜR: kaldırma YALNIZ `bar_sorgu`dadır. `olay_sorgu` modelin YAZDIĞI
    serbest SQL'i koşar — orada kapı gerçek bir saldırı yüzeyini kapatır ve KALIR.
    (Mutasyon: `_arac_olay_sorgu`dan çağrıyı kaldırınca bu çivi ve A2 ailesi kırmızıya döner.)"""
    _olay_defteri_kur()
    cagrilar = _kapi_casusu(monkeypatch)
    m = SahteModel(_arac(_tc("olay_sorgu", {"sql": "SELECT count(*) AS n FROM olaylar"})),
                   _metin("ok"))
    out = sohbet.sohbet_dongusu("kaç olay", "S1", model_cagir=m)
    assert cagrilar == ["olaylar"], f"olay_sorgu kapısı DÜŞTÜ: {cagrilar}"
    assert out["kaynaklar"] and out["kaynaklar"][0]["arac"] == "olay_sorgu", out["kaynaklar"]


def test_bar_sorgu_semasinda_SERBEST_SQL_alani_YOK():
    """BEYAN ÖLÇÜLÜR: yukarıdaki kapının gerekçesi "bugün serbest SQL yok"tur. Yarın bir `sql`
    alanı eklenirse bu çivi öter ve o kolun da kapıdan geçtiği ADIYLA gösterilmek zorunda kalır."""
    sema = sohbet.ARACLAR["bar_sorgu"].sema
    assert set(sema["properties"]) == {"sorgu", "sembol", "ay", "n"}, sema["properties"]
    assert sema.get("additionalProperties") is False, sema
    import ops.bar_sorgu as _bs
    assert sema["properties"]["sorgu"]["enum"] == list(_bs.SORGULAR), sema["properties"]["sorgu"]


# ---- K4 — MODEL YAZIMI SQL'İN KAYNAK TAVANLARI (tek uvicorn işçisi) -----------------------------
def test_olay_sorgu_KENDI_baglantisinda_bellek_ve_iplik_tavanli(kum):
    """TAVAN ARACIN KENDİ BAĞLANTISINDA ÖLÇÜLÜR — sorgunun kendisi `current_setting` ile sorar,
    yani ölçüm yapısal değil DAVRANIŞSALDIR. Ölçüldü (duckdb 1.5.5): sertleştirilmemiş bir
    bağlantıda varsayılan `memory_limit` sistem RAM'inin ~%80'i, `threads` çekirdek sayısıdır."""
    _olay_defteri_kur()
    sql = "SELECT current_setting('threads') AS t, current_setting('memory_limit') AS m"
    m = SahteModel(_arac(_tc("olay_sorgu", {"sql": sql})), _metin("ok"))
    out = sohbet.sohbet_dongusu("ayarları göster", "S1", model_cagir=m)
    gorunen = _arac_ciktisi(m.cagrilar[1])
    assert "REDDEDİLDİ" not in gorunen, gorunen[:300]
    veri = json.loads(re.search(r'\{.*\}', gorunen, re.S).group(0))
    iplik, bellek = veri["satirlar"][0]
    assert int(iplik) == sohbet.SORGU_IPLIK_TAVANI, veri
    sayi, birim = str(bellek).split()
    mib = float(sayi) * (1024.0 if birim.startswith("GiB") else 1.0)
    assert mib <= 512.0, f"bellek tavanı konmamış: {bellek}"
    assert out["kaynaklar"], out["kaynaklar"]


def test_olay_sorgu_ZAMAN_TAVANI_asilinca_REDDEDILIR_ve_atif_uretmez(kum, monkeypatch):
    """Zincirdeki model (kendi kararıyla ya da bir araç çıktısına gömülü enjeksiyonla) sonu
    gelmeyen bir sorgu yazabilir; `serve.sh` TEK uvicorn işçisi koştuğu için o iplikteki tükeniş
    panonun tamamını (halt/ack dahil) düşürürdü. Tavan çiviye 0,5 s'ye indirilir ki ölçüm 20 s
    beklemesin — SINANAN MEKANİZMA aynıdır (`threading.Timer` → `con.interrupt()`)."""
    monkeypatch.setattr(sohbet, "SORGU_TAVANI_S", 0.5)
    _olay_defteri_kur()
    # SORGUNUN KESİLMEDİĞİNDEKİ MALİYETİ ÖLÇÜLDÜ (bu makine, duckdb 1.5.5, threads=1):
    # `range(4e9)` 3,4 s. `1e10` ~8,5 s'dir — yani tavan çalışmazsa süre eşiği DE kırılır ve
    # çivi iki ayrı sebeple kırmızı verir (mutasyon böyle ısırır). Sonsuz bir sorgu seçmek
    # mutasyon koşumunu ASACAKTI; "ölçülemeyen kırmızı" ile "yeşil" aynı görünürdü.
    sql = "SELECT sum(x) FROM range(10000000000) t(x)"
    m = SahteModel(_arac(_tc("olay_sorgu", {"sql": sql})), _metin("ok"))
    t0 = time.perf_counter()
    out = sohbet.sohbet_dongusu("sonsuz sorgu", "S1", model_cagir=m)
    sure = time.perf_counter() - t0
    gorunen = _arac_ciktisi(m.cagrilar[1])
    assert "REDDEDİLDİ" in gorunen and "zaman tavanı" in gorunen, gorunen[:300]
    assert out["kaynaklar"] == [], f"kesilen sorgu kaynak atfı üretti: {out['kaynaklar']}"
    assert sure < 4.0, f"tavan ateşlenmedi, sorgu {sure:.1f} s koştu (kesilmemiş maliyet ~8,5 s)"


def test_ZAMAN_TAVANI_altindaki_sorgu_KESILMEZ(kum, monkeypatch):
    """NEGATİF KONTROL: tavan meşru sorguyu kesmemeli (yoksa çivi 'her şeyi reddet' ile de yeşil
    olurdu). Zamanlayıcı gövde biterken İPTAL EDİLİR — geç ateşlenen bir `interrupt` aynı
    bağlantıdaki bir sonraki sorguyu keserdi."""
    monkeypatch.setattr(sohbet, "SORGU_TAVANI_S", 5.0)
    _olay_defteri_kur(n=3)
    m = SahteModel(_arac(_tc("olay_sorgu", {"sql": "SELECT event FROM olaylar ORDER BY 1"})),
                   _metin("ok"))
    out = sohbet.sohbet_dongusu("olayları listele", "S1", model_cagir=m)
    gorunen = _arac_ciktisi(m.cagrilar[1])
    assert "REDDEDİLDİ" not in gorunen and "olay_0" in gorunen, gorunen[:300]
    assert out["kaynaklar"], out["kaynaklar"]


# ---- K5 — ÇÖZÜMLENEMEYEN SORGU SAHTE KAYNAK ATFI ÜRETMEZ ----------------------------------------
@pytest.mark.parametrize("sql,neden", [
    ("SELECT bilinmeyen_sutun FROM olaylar", "binder"),
    ("SELECT * FROM boyle_bir_tablo_yok", "katalog"),
])
def test_cozumlenemeyen_sorgu_REDDEDILIR_ve_kaynak_atfi_URETMEZ(kum, sql, neden):
    """ATIF = "bu veriye BAKILDI" İDDİASIDIR ve EDG-2026-086'nın uydurma sayımının PAYDASIDIR.
    Çözümleme hatasında HİÇBİR satır okunmaz: sınıfı `AracReddi` olmalı ki `_arac_kos` atıf
    üretmesin. Hata metni modele yine gider — model neyi düzelteceğini görür."""
    _olay_defteri_kur()
    m = SahteModel(_arac(_tc("olay_sorgu", {"sql": sql})), _metin("ok"))
    out = sohbet.sohbet_dongusu("kötü sorgu", "S1", model_cagir=m)
    gorunen = _arac_ciktisi(m.cagrilar[1])
    assert "REDDEDİLDİ" in gorunen and "çözümlenemedi" in gorunen, (neden, gorunen[:300])
    assert out["kaynaklar"] == [], f"({neden}) SAHTE KAYNAK ATFI: {out['kaynaklar']}"


def test_SIFIR_SATIR_donduren_sorgu_OKUNMUS_sayilir(kum):
    """SIFIR BİR ÖLÇÜMDÜR, HATA DEĞİLDİR (uydurma yasağının diğer yüzü): süzgeci hiçbir satırın
    geçmediği MEŞRU bir sorgu `n: 0` ile döner ve atıf ÜRETİR — "baktım, yoktu" ile "bakamadım"
    aynı görünmemeli."""
    _olay_defteri_kur()
    m = SahteModel(_arac(_tc("olay_sorgu",
                             {"sql": "SELECT event FROM olaylar WHERE event = 'boyle_olay_yok'"})),
                   _metin("ok"))
    out = sohbet.sohbet_dongusu("boş sonuç", "S1", model_cagir=m)
    gorunen = _arac_ciktisi(m.cagrilar[1])
    assert "REDDEDİLDİ" not in gorunen and '"n": 0' in gorunen, gorunen[:300]
    assert out["kaynaklar"] and out["kaynaklar"][0]["arac"] == "olay_sorgu", out["kaynaklar"]


# ---- K6 — MATERYALİZASYON BEDELİ ARŞİVLİ DÜNYADA DA ÖLÇÜLÜR -------------------------------------
#: Arşive konan sentetik ay. Canlıda `ops/olay_sikistir.py` aylık parquet üretir ve JSONL'den
#: SÜZÜLEN her ay görünümde parquet'ten gelir — yani üretimdeki `olaylar` bir BİRLEŞİMDİR.
ARSIV_OLAY_SATIRI = 28_000


def _olay_arsivi_kur(n: int = ARSIV_OLAY_SATIRI, ay: str = "2026-07") -> None:
    """`state/olaylar/<ay>.parquet` — `ops.olay_sorgu.parquet_kaynak_sql`in beklediği `(ay, ham)`
    yüzeyi. Sıkıştırıcıyı (`ops/olay_sikistir.py`) çağırmak bu çivinin ölçtüğü şeyi değiştirmezdi
    ama koşumu ona bağlardı; şema burada TEK kaynaktan (o modülün yüzeyi) türetilir."""
    import duckdb

    import ops.olay_sorgu as _os_mod
    dizin = _os_mod.arsiv_dizini(config.STATE / "events.jsonl")
    dizin.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    try:
        con.execute(
            f"COPY (SELECT '{ay}' AS ay, "
            f"      '{{\"ts\": \"{ay}-01T10:00:00+00:00\", \"level\": \"info\", "
            f"\"event\": \"arsiv_olay\", \"detail\": \"' || repeat('x', 200) || '\"}}' AS ham "
            f"      FROM range({int(n)})) TO '{dizin / (ay + '.parquet')}' (FORMAT PARQUET)")
    finally:
        con.close()


def test_materyalizasyon_maliyeti_ARSIVLI_dunyada_da_tavanin_altinda(kum):
    """ÜRETİMDEKİ ŞEKİL ÖLÇÜLÜR (Bedel yasası). Önceki ölçüm yalnız `state/events.jsonl`e yazıyordu
    ve `state/olaylar/` hiç oluşmadığı için `parquet_dosyalari()` BOŞ dönüyordu: tavan "arşivin
    SIFIR olduğu" dünyada konmuştu. Canlıda görünüm jsonl UNION arşivdir ve arşiv AYLIK BÜYÜR —
    bu çivi birleşim dalını ölçer. CANLI ölçek ölçümü dağıtımda Rol-1'in işidir; buradaki sayı
    sentetik ölçeğin hükmüdür."""
    import ops.olay_sorgu as _os_mod
    defter = config.STATE / "events.jsonl"
    with defter.open("w") as f:
        for i in range(CANLI_OLAY_SATIRI):
            f.write(json.dumps({"ts": f"2026-09-0{(i % 7) + 1}T10:00:{i % 60:02d}+00:00",
                                "level": "info", "event": f"olay_{i % 40}",
                                "detail": "x" * 200}) + "\n")
    _olay_arsivi_kur()
    con = _os_mod.baglanti_kur()
    try:
        kaynak = _os_mod.gorunumu_kur(con, defter, _os_mod.arsiv_dizini(defter))
        assert kaynak.parquetler, "arşiv dalı hiç kurulmadı — ölçüm yine jsonl-yalnız dünyada"
        sohbet._sorgu_sinirlari(con)
        t0 = time.perf_counter()
        sohbet._harici_erisimi_kapat(con)
        sure = time.perf_counter() - t0
        toplam = con.execute("SELECT count(*) FROM olaylar").fetchone()[0]
        parquetten = con.execute(
            "SELECT count(*) FROM olaylar WHERE kaynak = 'parquet'").fetchone()[0]
    finally:
        con.close()
    assert toplam == CANLI_OLAY_SATIRI + ARSIV_OLAY_SATIRI, toplam
    assert parquetten == ARSIV_OLAY_SATIRI, parquetten
    assert sure < MATERYALIZE_TAVANI_S, (
        f"{toplam} satırın (jsonl UNION arşiv) materyalizasyonu {sure:.3f} s sürdü "
        f"(tavan {MATERYALIZE_TAVANI_S} s) — sohbet aracı bu bedeli HER sorguda öder ve arşiv "
        "aylık büyür")


# =================================================================================================
# TUR 3 / M2 — `_SOHBET_KILIDI` PARK ETMEZ: MEŞGULKEN HIZLI, DÜRÜST VE DEFTERSİZ CEVAP
# =================================================================================================
#: MEŞGUL cevabının tavanı. Ölçülen şey "model çağrılmadı"dır; süre onun GÖZLENEBİLİR imzasıdır —
#: kilit park etseydi cevap `max_tur × zincir × ZAMAN_ASIMI_S` (varsayılanda ~54 dk) sürebilirdi.
MESGUL_TAVANI_S = 0.1


def _mesgul_cagrisi() -> tuple[dict, float, list[int]]:
    """Kilit BAŞKASINDAYKEN bir sohbet turu dener → (cevap, süre, model çağrı kaydı).

    Çağrı AYRI BİR İPLİKTE koşar ve `join(timeout=...)` ile sınırlanır: `blocking=True`
    mutasyonu bu kurulumda ASILIRDI ve asılan bir çivi kırmızı DEĞİL, ölçümsüzdür — burada
    "iplik hâlâ yaşıyor" iddiası mutasyonu KIRMIZIYA çevirir."""
    import threading
    cagrildi: list[int] = []
    kutu: dict = {}

    def _asla(mesajlar, araclar):
        cagrildi.append(1)
        return _metin("bu cevap ASLA üretilmemeliydi")

    def _dene() -> None:
        t0 = time.perf_counter()
        kutu["satir"] = sohbet.sohbet_dongusu("meşgulken soru", "S9", model_cagir=_asla)
        kutu["sure"] = time.perf_counter() - t0

    assert sohbet._SOHBET_KILIDI.acquire(blocking=False), "kilit çiviye girmeden ÖNCE tutuluyordu"
    ip = threading.Thread(target=_dene)
    try:
        ip.start()
        ip.join(timeout=5.0)
        assert not ip.is_alive(), (
            "KİLİT PARK ETTİ: ikinci çağrı kilidi bekleyerek anyio iş havuzunun jetonunu tutuyor "
            "(`acquire(blocking=False)` değil) — 40 jetonluk havuzda yığılan istekler senkron "
            "rota yüzeyinin tamamını susturur")
    finally:
        sohbet._SOHBET_KILIDI.release()
    ip.join(timeout=5.0)
    return kutu["satir"], kutu["sure"], cagrildi


def test_kilit_MESGULKEN_cevap_ANINDA_doner_MODEL_CAGRILMAZ_DEFTERE_YAZILMAZ(kum):
    """ÜÇ İDDİA, ÜÇÜ DE AYRI BİR BEDELİ ÖLÇER:
      * `mesgul: True` + hızlı dönüş → iplik kilitte park etmiyor (Y2'nin kapattığı sınıf),
      * model ÇAĞRILMADI → meşgul bir yüzey kotayı (filo kovası) harcamıyor,
      * `sohbet.jsonl` BOŞ → reddedilen istek B3 ölçümünün PAYDASINI kirletmiyor ("kaç mesaj
        soruldu" sorusu cevaplanan mesajları sayar; cevaplanmayan bir deneme mesaj değildir)."""
    satir, sure, cagrildi = _mesgul_cagrisi()
    assert satir.get("mesgul") is True, satir
    assert cagrildi == [], "MEŞGUL DÖNÜŞTE MODEL ÇAĞRILDI — kota boşa harcandı"
    assert sure <= MESGUL_TAVANI_S, f"meşgul cevabı {sure:.3f} s sürdü (tavan {MESGUL_TAVANI_S} s)"
    assert store.read_jsonl(sohbet.SOHBET_DEFTERI) == [], store.read_jsonl(sohbet.SOHBET_DEFTERI)
    assert sohbet.MESGUL_CEVABI in str(satir.get("cevap")), satir


def test_MESGUL_cevabi_DEFTER_SEKLINI_tasir(kum):
    """UÇ NOKTA BU SÖZLÜĞÜ AYNEN SERVİS EDER (`api_sohbet`). Şekil `DEFTER_ALANLARI`dan eksik
    olsaydı pano bir sohbet turunun ortasında tanımsız alan okurdu; `mesgul` bayrağı EKTİR,
    ikame DEĞİL."""
    satir, _sure, _cagrildi = _mesgul_cagrisi()
    assert set(sohbet.DEFTER_ALANLARI) <= set(satir), (
        set(sohbet.DEFTER_ALANLARI) - set(satir))
    assert satir["model"] is None and satir["turlar"] == [] and satir["kaynaklar"] == [], satir
    assert satir["oneri_id"] is None and satir["llm_dustu"] is False, satir


def test_MESGUL_donusunden_SONRA_kilit_SERBEST_kalir(kum):
    """POZİTİF KONTROL: "her şeye meşgul de" diyen bir gövde yukarıdaki çivileri de geçerdi.
    Kilit bırakıldıktan sonra normal tur KOŞAR ve deftere YAZAR."""
    _satir, _sure, _cagrildi = _mesgul_cagrisi()
    m = SahteModel(_metin("normal cevap"))
    out = sohbet.sohbet_dongusu("kilit serbest mi", "S1", model_cagir=m)
    assert not out.get("mesgul"), out
    assert out["cevap"] == "normal cevap", out
    satirlar = store.read_jsonl(sohbet.SOHBET_DEFTERI)
    assert len(satirlar) == 1 and satirlar[0]["oturum"] == "S1", satirlar


def test_api_sohbet_MESGUL_cevabini_200_ile_OLDUGU_GIBI_doner(istemci, monkeypatch):
    """HTTP 200 + `mesgul` alanı: 5xx demek "sunucu arızalandı" demek olurdu — burada sunucu
    çalışıyor ve DÜRÜST bir hâl bildiriyor. Uç ikinci bir cümle KURMAZ, sözlüğü taşır."""
    beklenen = {**_sahte_satir("S9"), "cevap": sohbet.MESGUL_CEVABI, "mesgul": True}
    monkeypatch.setattr(sohbet, "sohbet_dongusu", lambda *a, **k: beklenen)
    r = istemci.post("/api/sohbet", json={"mesaj": "meşgulken", "oturum": "S9"})
    assert r.status_code == 200, r.text
    assert r.json() == beklenen, r.json()
