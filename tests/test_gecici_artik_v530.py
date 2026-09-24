"""test_gecici_artik_v530.py — TSK-209b (2026-09-21): ATOMİK YAZIMIN GEÇİCİ ARTIKLARI
(`tmp*.tmp`, `.secrets_*.tmp`) ad-tabanlı sır sınıflandırmasının GÖREMEDİĞİ dosya ailesiydi.

ÖLÇÜLMÜŞ ZEMİN (Rol-1 + bu ajan, bağımsız; 2026-09-21 — hiçbir GERÇEK sır değeri okunmadan).

  * `store._atomic_write` geçici dosyayı `tempfile.mkstemp(dir=..., suffix=".tmp")` ile açar, yani
    ad `tmpXXXXXXXX.tmp`tır ve `state/` KÖKÜNDE doğar. `auth._write` H9'dan beri
    `store.write_text`e devrettiği için pano oturum imza anahtarının yazımı da bu yoldan geçer:
    artığın İÇERİĞİ yazılan defterin içeriğidir.
  * `secrets._write_file` kendi atomik yazımını kurar: `prefix=".secrets_"`, `suffix=".tmp"` →
    `.secrets_XXXXXX.tmp`. GİZLİ ad (nokta önekli) ve SIR içerikli.
  * `config.sir_dosyasi_mi` NE birini NE ötekini eşler (`SIR_TAM_ADLAR` iki kanonik ad;
    `SIR_DESENLERI` `secrets.json*` / `secrets.*.json` / `auth.json*`). Yani böyle bir artık
    kum havuzuna KOPYALANIRDI; teşhis paketine girmemesi ise DIŞLAMA DEĞİL SÜZGEÇ TESADÜFÜYDÜ
    (`.tmp` izinli uzantı kümesinde değil) — bu deponun beşinci kez ölçtüğü tesadüf sınıfı.

BUGÜN ZARAR YOK, SINIF YAPISAL: canlı `state/` kökünde (ve 1. seviyede) `tmp*`/`.tmp` artığı
2026-09-21 18:25Z ölçümünde SIFIRDI. "Bugün yok" ile "olamaz" aynı şey değildir (uydurma yasağı):
artık ancak `write` ile `os.replace` ARASINDAKİ bir çökmede kalır, yani nadirdir — ama kaldığı gün
bir sır kopyasıdır ve hiçbir kapı onu tanımaz.

HATA DALI ÖLÇÜMÜ (bu turun İLK işi, koddan): İKİ yolda da temizlik VARDIR —
`store._atomic_write` `except BaseException:` dalında, `secrets._write_file` `except Exception:`
dalında `os.unlink(tmp)` çağırır. Dolayısıyla 1. ve 2. çiviler BUGÜN KIRMIZI DEĞİL: onlar
REGRESYON KORUMASIDIR ve bu beyan dürüstlüğün kendisidir (yeşil bir çivi "bozuktu, düzelttim"
diye okunamaz). ASİMETRİ AÇIK KALEM OLARAK BEYAN EDİLİR: `secrets` dalı `Exception` yakalar,
`store` dalı `BaseException`; yani `KeyboardInterrupt`/`SystemExit` ile kesilen bir sır yazımı
SIR İÇERİKLİ artığı diskte bırakır. Bu turda KAYNAK DÜZELTİLMEDİ (Rol-1 kararı: "hata dalı zaten
varsa ölç ve dokunma") — ama bu dilimin sınıflandırması o artığı artık SIR sayar, yani ikinci
savunma hattı kapanır.

NE ÇİVİLENİR
  1. `store` yazımı `os.replace` anında düşerse `state/` kökünde `tmp*.tmp` KALMAZ (regresyon).
  2. Aynısı `secrets` atomik yazımı ve `.secrets_*.tmp` için (regresyon).
  3. Sentetik `state/` ağacında iki artık VARKEN: kum havuzuna GİRMEZ (bugünkü kırmızı) ve teşhis
     paketine GİRMEZ; manifest ikisini AYRI alanlarda taşır — sır ↔ geçici artık karıştırılmaz.
  4. DARALTMA YOK: `template.json`, `tmp_notlar.md`, `stamp.json`, `x.tmp` kopyalanmaya devam eder.
  5. TEK KAYNAK: iki üretim yüzeyi de BİLEŞİK yüklemi çağırır ve tek kaynağı oynatmak İKİSİNİ de
     oynatır (v524 çivi 7a/7b deseninin geçici-artık kardeşi).
  6. BEDEL YASASI: adı önceden bilinmeyen bir artık atlandıysa iz kalır —
     `sprint_kum_havuzu_atlandi` olayı artığı ADIYLA taşır (içerik/değer ASLA).
  7. Yüklem birleşiminin SAF ölçümü: `kopyalanmaz_mi = sir_dosyasi_mi ∨ gecici_artik_mi` ve iki
     sınıf birbirine sızmaz.

CANLIYA DOKUNMAZ: her şey `sandbox_state`in tmp ağacındadır; `monkeypatch.undo()` YOKTUR ve
operatörün gerçek `state/secrets.json` / `state/auth.json` dosyaları hiçbir yerde açılmaz.
"""
from __future__ import annotations

import io
import json
import os
import re
import zipfile

import pytest
from fastapi.testclient import TestClient

from meridian import api, auth, config, secrets as secrets_mod, sprint, store

# Sentetik artık ADLARI. Gerçek `mkstemp` adları rastgeledir; buradaki iki ad o BİÇİMİN
# temsilcisidir (`tmp` öneki + `.tmp` uzantısı / `.secrets_` öneki + `.tmp` uzantısı).
TMP_ARTIGI = "tmpab12cd.tmp"
SIR_ARTIGI = ".secrets_x1.tmp"

# Artıkların İÇERİĞİ yerine kullanılan NİŞAN — pakette/manifeste/olay kaydında görünürse sızıntı
# var. Gerçek sır değeri bu dosyanın hiçbir yerinde okunmaz.
NISAN = "V530-SIZINTI-NISANI"

# Pano parolası: uç `_auth` ile korumalıdır ve testin düzeneği ucu GERÇEK duruşuyla çağırır.
PAROLA = "v530-sentetik-parola"

#: DARALTMA SINIRI — bu adlar geçici artık DEĞİLDİR ve kopyalanmaya devam etmelidir. `tmp*.tmp`
#: deseni `tmp` ile BAŞLAYIP `.tmp` ile BİTEN adları yakalar; dördü de o kalıbın dışındadır ama
#: DÖRDÜ FARKLI YÖNDEN DIŞARIDADIR (mutasyonla ölçüldü, 2026-09-21):
#:   `tmp_notlar.md` önek VAR/uzantı YOK — deseni `tmp*`a indiren mutasyon (M2) bunu düşürdü;
#:   `x.tmp` uzantı VAR/önek YOK — `*.tmp` mutasyonu (M3) bunu düşürdü;
#:   `stamp.json` ikisini de tutturmaz (tek kaynağı oynatan 5b çivisinin taşıyıcısı);
#:   `template.json` NEAR-MISS'tir: göz `temp`i `tmp` diye okur, desen okumaz — M2 bunu ISIRMADI
#:   ve ısırmaması DOĞRUDUR. Kayıt burada duruyor ki okuyucu onu "önek var" sanıp deseni gevşetmesin.
ARTIK_OLMAYANLAR = ("template.json", "tmp_notlar.md", "stamp.json", "x.tmp")


class _ReplaceKesilir:
    """`os.replace` ANINDA `KeyboardInterrupt` yükselten sarmalayıcı (tur 2).

    `OSError` DEĞİL BİR `BaseException` SEÇİLDİ ve seçim ölçümdendir: `KeyboardInterrupt`
    `Exception`ın ALTINDA DEĞİLDİR, dolayısıyla `except Exception:` yazan bir temizlik dalı onu
    HİÇ GÖRMEZ. Operatörün Ctrl-C'si ya da `systemctl stop` penceresinde kesilen bir yazım tam
    olarak bu sınıftır."""

    def __init__(self, gercek):
        self._gercek = gercek

    def __getattr__(self, ad):
        return getattr(self._gercek, ad)

    def replace(self, *a, **kw):
        raise KeyboardInterrupt("v530: os.replace sentetik kesinti — operatör Ctrl-C sınıfı")


class _ReplacePatlar:
    """`os` modülünün `replace` DIŞINDA her şeyi geçiren sarmalayıcı.

    NEDEN SARMALAYICI, NEDEN `monkeypatch.setattr(os, "replace", ...)` DEĞİL: `os` süreç
    genelinde paylaşılan bir modüldür ve onu doğrudan patch'lemek aynı pencerede koşan HER kodu
    (pytest'in kendi dosya işlemleri dâhil) etkiler. Sarmalayıcı yalnız ÖLÇÜLEN modülün `os`
    adına bağlanır, yani ısırık hedefin içinde kalır."""

    def __init__(self, gercek):
        self._gercek = gercek

    def __getattr__(self, ad):
        return getattr(self._gercek, ad)

    def replace(self, *a, **kw):
        raise OSError("v530: os.replace sentetik arıza — write ile replace ARASINDA çökme")


def _artiklar(desen: str) -> list[str]:
    """`state/` KÖKÜNDEKİ artık adları (alt dizinler değil — artık kökte doğar)."""
    import fnmatch
    return sorted(f.name for f in config.STATE.iterdir()
                  if f.is_file() and fnmatch.fnmatchcase(f.name, desen))


def _canli_state_kur(artiklar: bool = True) -> dict[str, bytes]:
    """Sentetik CANLI `state/` ağacı kurar; "kopyalanması/pakete girmesi GEREKEN" defterleri döner.

    `sandbox_state` `config.STATE`i tmp'ye çevirmiş, `history/`+`bars/` dizinlerini ve depodaki
    `goal.yaml`/`bounds.yaml`ı oraya koymuştur; buraya yalnız bu turun ölçtüğü girdiler eklenir."""
    live = config.STATE
    (live / "events.jsonl").write_text('{"event":"v530_isaret"}\n')
    (live / "portfolio.json").write_text('{"positions":{},"realized_pnl":0.0}')
    girmeli = {ad: (live / ad).read_bytes()
               for ad in ("goal.yaml", "bounds.yaml", "events.jsonl", "portfolio.json")
               if (live / ad).exists()}
    assert len(girmeli) == 4, f"kurulum çipası: sentetik ağaçta normal defter eksik ({sorted(girmeli)})"

    (live / "secrets.json").write_text('{"ALPACA_KEY":"%s-secrets"}' % NISAN)
    if artiklar:
        (live / TMP_ARTIGI).write_text('{"key":"%s-store-artigi"}' % NISAN)
        (live / SIR_ARTIGI).write_text('{"ALPACA_KEY":"%s-secrets-artigi"}' % NISAN)
    # PANO KİMLİK KAYDI GERÇEK YOLDAN DOĞAR (v524 emsali): elle sahte bir sözlük yazmak dosyanın
    # ŞEKLİNİ taklit eder ama `password_set()` yanlış dallanırdı.
    auth.set_password(PAROLA)
    assert auth.password_set(), "kurulum çipası: sentetik ağaçta parola kurulmadı"
    return girmeli


def _kum_havuzu(sid: str = "20990101-000000"):
    return sprint._kur_kum_havuzu(sid) / "state"


def _client() -> TestClient:
    """Yaşam döngüsü BAŞLATILMADAN istemci (v287/v454/v524 emsali): `with TestClient(app)`
    scheduler ve hermes ipliklerini ayağa kaldırır — bu uç için gereksiz."""
    c = TestClient(api.app)
    c.cookies.set(auth.COOKIE_NAME, auth.issue_session())
    return c


def _paket() -> tuple[zipfile.ZipFile, bytes, int]:
    r = _client().get("/api/debug_export")
    if r.status_code != 200:
        return None, r.content, r.status_code          # type: ignore[return-value]
    return zipfile.ZipFile(io.BytesIO(r.content)), r.content, r.status_code


# ==================================================================================================
# 1 — `store` yazımı ORTADA düşerse artık KALMAZ (REGRESYON KORUMASI — bugün yeşil, beyanlı)
# ==================================================================================================
def test_1_store_yazimi_replace_aninda_duserse_tmp_artigi_KALMAZ(sandbox_state, monkeypatch):
    """ÖLÇÜLDÜ (kod, 2026-09-21): `store._atomic_write` `except BaseException:` dalında
    `os.unlink(tmp)` çağırır — yani bu çivi BUGÜN KIRMIZI DEĞİLDİR ve öyle olduğu BEYAN EDİLİR.

    NEDEN YİNE DE YAZILDI: temizlik bu dilimin kaynak-tarafı sözleşmesidir ve sözleşmenin
    ölçülebilir hâli olmadan bir sonraki yeniden yazımda sessizce kaybolur. Artığın kalması hâlinde
    kaybedilen şey ölçülmüştür: `auth.json`/`secrets.json` yazımı da bu kapıdan geçer, yani artık
    bir SIR KOPYASIDIR.

    `os.replace` BİLEREK seçildi: `write`+`fsync` TAMAMLANDIKTAN sonra, yer değiştirmeden ÖNCE
    düşen bir yazım tam olarak artığın doğduğu penceredir."""
    monkeypatch.setattr(store, "os", _ReplacePatlar(os))
    assert _artiklar("tmp*.tmp") == [], "kurulum çipası: sentetik ağaçta zaten artık var"

    with pytest.raises(OSError):
        store.write_text("v530_defter.txt", "v530 gövde")

    assert _artiklar("tmp*.tmp") == [], (
        "`store` atomik yazımı düştü ve geçici dosya `state/` kökünde KALDI — içeriği yazılan "
        "defterin içeriğidir (`auth.json`/`secrets.json` dâhil) ve hiçbir ad deseni onu tanımaz")
    assert not (config.STATE / "v530_defter.txt").exists(), (
        "kurulum çipası: hedef dosya yazılmış — sentetik arıza `os.replace`i durdurmamış, yani "
        "bu çivi artığın doğduğu pencereyi hiç ölçmüyor")


# ==================================================================================================
# 2 — `secrets` yazımı ORTADA düşerse GİZLİ artık KALMAZ (REGRESYON KORUMASI — bugün yeşil)
# ==================================================================================================
def test_2_secrets_yazimi_replace_aninda_duserse_gizli_artik_KALMAZ(sandbox_state, monkeypatch):
    """`secrets._write_file` `store`u BİLEREK kullanmaz (0600 + telemetriye/loga hiç dokunmama),
    dolayısıyla dayanıklılık orada ELDE tekrarlanır — ve tekrarlanan her kalıp ayrı ayrı ölçülmek
    zorundadır (tek-kaynak yasasının istisnası: kopya kaçınılmazsa ayrışma çivisi).

    ÖLÇÜLDÜ (kod, 2026-09-21): temizlik VARDIR, ama dal `except Exception:`tir — `store`daki
    `except BaseException:` ile AYRIŞIKTIR. `KeyboardInterrupt` ile kesilen bir sır yazımı bu
    yüzden SIR İÇERİKLİ bir `.secrets_*.tmp` bırakır. Bu tur kaynağa DOKUNMADI (Rol-1 kararı);
    açık kalem olarak beyan edilir ve 3. çivi o artığın hiç değilse SIR SAYILDIĞINI ölçer.

    YAZILAN DEĞER SENTETİKTİR: operatörün gerçek sır deposu ne okunur ne yazılır — `config.STATE`
    `sandbox_state` tarafından tmp'ye çevrilmiştir."""
    monkeypatch.setattr(secrets_mod, "os", _ReplacePatlar(os))
    assert _artiklar(".secrets_*.tmp") == [], "kurulum çipası: sentetik ağaçta zaten artık var"

    with pytest.raises(OSError):
        secrets_mod._write_file({"V530_SENTETIK": NISAN})

    assert _artiklar(".secrets_*.tmp") == [], (
        "`secrets` atomik yazımı düştü ve GİZLİ geçici dosya `state/` kökünde KALDI — içeriği "
        "operatör anahtar deposunun kendisidir")
    assert not (config.STATE / "secrets.json").exists(), (
        "kurulum çipası: sır dosyası yazılmış — sentetik arıza `os.replace`i durdurmamış")


# ==================================================================================================
# 2b — TUR 2: KESİNTİ de bir hatadır — `BaseException` hizalaması (Rol-1 kararı, 2026-09-21)
# ==================================================================================================
#: TUR 1 ÖLÇÜMÜ (bu dosyanın başlık beyanı): iki temizlik dalı AYRIŞIKTI. `store._atomic_write`
#: `except BaseException:` yazar, `secrets._write_file` `except Exception:` yazıyordu; ikisi de
#: `os.unlink(tmp)` çağırıp `raise` ile YENİDEN YÜKSELTİYORDU (ölçüldü — dolayısıyla ikisi de
#: Yasa 4 anlamında sessiz DEĞİL, `# sessiz-yutma` işareti GEREKMEZ). Fark yalnız YAKALANAN
#: SINIFTAYDI ve bedeli ölçülmüştü: `KeyboardInterrupt` `Exception`ın altında olmadığı için
#: kesilen bir SIR yazımı `.secrets_*.tmp` artığını diskte bırakıyordu. Rol-1 kararı: hizala.
def test_2b_secrets_yazimi_KESILIRSE_de_gizli_artik_KALMAZ(sandbox_state, monkeypatch):
    """TUR 2'NİN KIRMIZISI. `os.replace` bir `KeyboardInterrupt` yükseltir — yani `write`+`fsync`
    bitmiş, yer değiştirme başlamamıştır ve süreç kesilmektedir.

    İKİ İDDİA BİRDEN, ve ikincisi taşıyıcıdır:
      (a) `.secrets_*.tmp` artığı KALMAZ — içeriği operatör anahtar deposudur;
      (b) İSTİSNA YENİDEN YÜKSELİR. Temizliği "yakalayıp yut" biçiminde yazmak artığı silerdi ama
          kesintinin kendisini YUTARDI: Ctrl-C'ye cevap vermeyen bir süreç, kirli bir tmp'den
          beterdir ve Yasa 4'ün tam olarak yasakladığı şeydir. `pytest.raises` bu yüzden burada
          bir kurulum ayrıntısı değil ÇİVİNİN İKİNCİ AYAĞIDIR.

    `store` tarafı bu sınıfı ZATEN kapsıyordu (`except BaseException:`); 1. çivi onun OSError
    bacağını ölçer, hizalamadan sonra iki yol AYNI sözleşmeyi taşır."""
    monkeypatch.setattr(secrets_mod, "os", _ReplaceKesilir(os))
    assert _artiklar(".secrets_*.tmp") == [], "kurulum çipası: sentetik ağaçta zaten artık var"

    with pytest.raises(KeyboardInterrupt):
        secrets_mod._write_file({"V530_SENTETIK": NISAN})

    assert _artiklar(".secrets_*.tmp") == [], (
        "sır yazımı KESİLDİ ve GİZLİ geçici dosya `state/` kökünde KALDI — `KeyboardInterrupt` "
        "`Exception`ın altında değildir, yani `except Exception:` yazan bir temizlik dalı bu "
        "sınıfı hiç görmez; `store._atomic_write` aynı senaryoyu temizler (ayrışma)")
    assert not (config.STATE / "secrets.json").exists(), (
        "kurulum çipası: sır dosyası yazılmış — sentetik kesinti `os.replace`i durdurmamış")


def _temizlik_dallari(fn) -> list:
    """`fn` içindeki "geçici dosyayı sil ve YENİDEN YÜKSELT" dallarını AST'den döndürür.

    NEDEN AST, NEDEN DÜZ METİN DEĞİL — BU ÇİVİ BİR MUTASYONLA DÜZELTİLDİ (2026-09-21). İlk yazım
    `inspect.getsource(fn)` metninde `"except BaseException:"` dizgesini arıyordu ve M11
    mutasyonu (hizalamayı geri alma) onu ISIRMADI: `secrets._write_file`in DOCSTRING'i hizalamayı
    ANLATIRKEN o dizgeyi zaten içeriyordu, yani çivi kodu değil DÜZYAZIYI ölçüyordu. Klasik sahte
    yeşil — ve tam olarak "çivi yeşili kanıt değildir" kuralının ölçtüğü sınıf. AST'de docstring
    bir `ast.Constant`tır ve `ast.ExceptHandler.type` ile karışamaz.

    Aday tanımı DAVRANIŞSALDIR, satır/biçim değil: gövdesinde `…unlink(…)` çağrısı GEÇEN ve
    ÇIPLAK `raise` ile BİTEN bir `except` dalı."""
    import ast
    import inspect
    import textwrap
    fndef = ast.parse(textwrap.dedent(inspect.getsource(fn))).body[0]
    dallar = []
    for dugum in ast.walk(fndef):
        if not isinstance(dugum, ast.Try):
            continue
        for h in dugum.handlers:
            siler = any(isinstance(n, ast.Attribute) and n.attr == "unlink" for n in ast.walk(h))
            yeniden = bool(h.body) and isinstance(h.body[-1], ast.Raise) and h.body[-1].exc is None
            if siler and yeniden:
                dallar.append(h)
    return dallar


def test_2c_iki_atomik_yazim_yolu_AYNI_istisna_sinifini_temizler():
    """YAPISAL KAYNAK ÖLÇÜMÜ — iki yolun sözleşmesi yan yana konur (AYRIŞMA ÇİVİSİ).

    Tek-kaynak yasası burada TEK GÖVDEYİ MÜMKÜN KILMAZ ve bu bilinçlidir: `secrets._write_file`
    `store`u KULLANMAZ (0600 + telemetriye/loga hiç dokunmama, gerekçe o fonksiyonun
    docstring'inde). Kopya kaçınılmaz → yasanın istisnası uygulanır: biri yakaladığı sınıfı
    daraltırsa burası kırmızıya döner.

    `raise` AYRICA ölçülür ve ayrı bir iddiadır: temizliğin istisnayı YUTMAMASI, dalın
    `# sessiz-yutma` işareti GEREKTİRMEMESİNİN de sebebidir (Yasa 4). İşaret ARANMAZ, YENİDEN
    YÜKSELTME aranır — `_temizlik_dallari` zaten yalnız yeniden yükselten dalları toplar, yani
    `raise` sökülürse aday SIFIRA düşer ve ilk iddia kırmızıya döner."""
    for fn, ad in ((store._atomic_write, "store._atomic_write"),
                   (secrets_mod._write_file, "secrets._write_file")):
        dallar = _temizlik_dallari(fn)
        assert len(dallar) == 1, (
            f"`{ad}` içinde 'geçici dosyayı sil + YENİDEN YÜKSELT' dalı tam bir tane değil "
            f"({len(dallar)}) — ya temizlik yok, ya istisna YUTULUYOR (artık silinir, arıza ve "
            f"Ctrl-C kaybolur: Yasa 4'ün yasakladığı sınıf)")
        tip = dallar[0].type
        assert getattr(tip, "id", None) == "BaseException", (
            f"`{ad}` temizlik dalı `BaseException` yerine "
            f"`{getattr(tip, 'id', tip)}` yakalıyor — `KeyboardInterrupt` `Exception`ın ALTINDA "
            f"DEĞİLDİR, yani Ctrl-C ile kesilen bir yazım geçici dosyayı diskte bırakır ve iki "
            f"atomik yazım yolu ayrışır")


# ==================================================================================================
# 3 — SINIFLANDIRMA: iki artık VARKEN kum havuzuna ve teşhis paketine GİRMEZ (BUGÜNKÜ KIRMIZI)
# ==================================================================================================
def test_3a_gecici_artiklar_kum_havuzuna_GIRMEZ(sandbox_state):
    """BUGÜNKÜ KIRMIZI. `sprint._atlanir` yalnız `SKIP_COPY` ∪ `SIR_DESENLERI` sorar; ne
    `tmpab12cd.tmp` ne `.secrets_x1.tmp` hiçbiriyle eşleşir. Kum havuzu kopyası bu yüzden artığı
    `state/sprint/<sid>/state/` altına taşır ve orada SANDBOX_KEEP kadar çoğalır — TSK-208'in
    `secrets.json.bak-…` ile ölçtüğü sınıfın ADSIZ kardeşi."""
    _canli_state_kur()
    sb = _kum_havuzu()
    for ad in (TMP_ARTIGI, SIR_ARTIGI):
        assert not (sb / ad).exists(), (
            f"`{ad}` kum havuzuna kopyalandı — atomik yazımın geçici artığı, içeriği yazılan "
            f"defterin (sır olabilir) kendisidir ve adı hiçbir desenle eşleşmiyor")


def test_3b_gecici_artiklar_teshis_paketine_GIRMEZ_ve_manifestte_AYRI_alanlardadir(sandbox_state):
    """İKİ İDDİA. (a) Artık pakete girmez — ve bunun SEBEBİ uzantı süzgeci TESADÜFÜ olamaz:
    manifest'te adıyla görünmesi, kararın sınıflandırma kapısında verildiğinin kanıtıdır.
    (b) İki artık AYRI alanlarda raporlanır: `.secrets_*.tmp` GERÇEK SIRDIR (`disarida_
    birakilan_sirlar`), `tmp*.tmp` ise sır DEĞİL geçici artıktır (`disarida_birakilan_gecici`).
    Tek alana yığmak, "pakette kaç sır vardı" sorusunun cevabını sessizce şişirirdi."""
    _canli_state_kur()
    z, govde, kod = _paket()
    assert kod == 200, f"uç {kod} döndü — paket ölçülemez: {govde[:300]!r}"
    adlar = z.namelist()
    manifest = json.loads(z.read("manifest.json"))

    for ad in (TMP_ARTIGI, SIR_ARTIGI):
        assert f"state/{ad}" not in adlar, f"`{ad}` teşhis paketine girdi"
    assert SIR_ARTIGI in manifest.get("disarida_birakilan_sirlar", []), (
        f"`{SIR_ARTIGI}` SIR olarak dışlanmadı — `secrets` yazımının geçici dosyası operatör "
        f"anahtar deposunun İÇERİĞİNİ taşır: {manifest!r}")
    assert manifest.get("disarida_birakilan_gecici") == [TMP_ARTIGI], (
        f"geçici artıklar AYRI alanda ADIYLA raporlanmadı — atlama ya sessiz ya da sır sayımıyla "
        f"karışmış: {manifest!r}")
    assert TMP_ARTIGI not in manifest.get("disarida_birakilan_sirlar", []), (
        f"`{TMP_ARTIGI}` SIR alanına yazıldı — sır DEĞİL geçici artıktır; iki sınıf karışırsa "
        f"'kaç sır dışarıda kaldı' sayısı sessizce şişer")
    assert NISAN.encode() not in govde, "artıkların İÇERİĞİ zip gövdesinde"
    assert NISAN not in json.dumps(manifest), f"manifest artık İÇERİĞİ taşıyor: {manifest!r}"


# ==================================================================================================
# 4 — DARALTMA YOK (bedel yasası)
# ==================================================================================================
@pytest.mark.parametrize("ad", ARTIK_OLMAYANLAR)
def test_4_desen_mesru_defterleri_YAKALAMAZ(sandbox_state, ad):
    """`tmp*` ya da `*.tmp` yazmak hiçbir testi kırmadan kum havuzunu EKSİK doğururdu ve sprint
    sessizce yanlış ölçerdi (HALT vakasının sınıfı). Desen İKİ UCA birden bağlıdır: `tmp` ÖNEKİ ve
    `.tmp` UZANTISI. Dört adın her biri FARKLI bir yönden dışarıdadır — hangisinin hangi
    mutasyonla ısırdığı `ARTIK_OLMAYANLAR` şerhinde tek tek yazılıdır.

    SAF YÜZEY + ÜRETİM YOLU birlikte ölçülür: yüklem yeşil olup kopyalama yine de daralmışsa
    (ör. ikinci bir yerel desen listesi) ikinci bacak kırmızıya döner."""
    assert not config.gecici_artik_mi(ad), (
        f"`{ad}` geçici artık sayılıyor — desen GENİŞ yazılmış; meşru bir defter hem kum "
        f"havuzundan hem teşhis paketinden sessizce düşer")
    assert not config.kopyalanmaz_mi(ad), f"`{ad}` bileşik yüklemde de yakalanıyor"
    assert not sprint._atlanir(ad), f"`{ad}` kum havuzuna girmiyor — desen kopyalamayı daralttı"

    _canli_state_kur()
    (config.STATE / ad).write_text('{"v530":"mesru-defter"}')
    assert (_kum_havuzu() / ad).exists(), (
        f"`{ad}` kum havuzuna GİRMEDİ — düzeltme paketi kopyalamayı daralttı")


# ==================================================================================================
# 5 — TEK KAYNAK: iki yüzey, tek BİLEŞİK yüklem
# ==================================================================================================
def test_5a_iki_uretim_yuzeyi_de_BILESIK_yuklemi_cagirir():
    """KAYNAK DENETİMİ (v21 p3 emsali): karar iki yüzeyde de `config.kopyalanmaz_mi` ile sorulur.
    Sır bacağının AYRICA sorulması meşrudur ve gereklidir (manifest iki alanı ayırır), ama atlama
    KARARI bileşik yüklemden gelmelidir — yoksa bir yüzey geçici artığı öğrenir, diğeri öğrenmez
    ve TSK-209'da ölçülen ayrışma bu kez artık ailesinde yeniden doğar."""
    import inspect
    sprint_govde = inspect.getsource(sprint._desen_atlar)
    assert "config.kopyalanmaz_mi(" in sprint_govde, (
        "`sprint._desen_atlar` bileşik yüklemi çağırmıyor — kum havuzu geçici artığı kopyalar")

    api_kaynak = inspect.getsource(api)
    # Seçici dekoratördür (TSK-219): yol literali `GZIP_HARIC_YOLLAR`da da geçer (v21 p3 notu).
    blk = next(b for b in re.split(r"\n(?=@app\.)", api_kaynak)
               if '@app.get("/api/debug_export")' in b)
    assert "config.kopyalanmaz_mi(" in blk, (
        "`api.api_debug_export` bileşik yüklemi çağırmıyor — teşhis paketi kararı yalnız sır "
        "bacağını soruyor")
    bilesik_konumu = blk.index("config.kopyalanmaz_mi(")
    uzanti_konumu = blk.index('f.suffix not in (".json"')
    assert bilesik_konumu < uzanti_konumu, (
        "bileşik kapı uzantı süzgecinden SONRA geliyor — izinli uzantı taşıyan bir artık "
        "(`tmp1234.json` biçimi bir gün doğarsa) süzgeçten geçip pakete girer")


def test_5b_tek_kaynagi_oynatmak_IKI_yuzeyi_de_oynatir(sandbox_state, monkeypatch):
    """5a'nın DAVRANIŞ kardeşi ve asıl ısırığı: iki yüzey sınıflandırmayı ÇAĞRI ANINDA tek
    kaynaktan mı soruyor, yoksa kendi yerel kopyalarından mı?

    `stamp.json` BİLEREK seçildi: 4. çivi onun kopyalandığını ölçüyor, yani buradaki dışlanma
    yalnızca monkeypatch'ten gelebilir. Aynı anda `tmpab12cd.tmp` GERİ GELMELİDİR — tek kaynak
    boşaltıldığında davranışın da boşalması, desenin gerçekten taşıyıcı olduğunu gösterir
    (v523 çivi 4 deseni)."""
    monkeypatch.setattr(config, "GECICI_ARTIK_DESENLERI", ("stamp.json",))
    _canli_state_kur()
    (config.STATE / "stamp.json").write_text('{"v530":"damga"}')

    sb = _kum_havuzu()
    assert not (sb / "stamp.json").exists(), (
        "tek kaynağa eklenen desen kum havuzunda hüküm doğurmadı — `sprint` geçici artık "
        "desenlerinin İKİNCİ bir tanımını taşıyor (tek-kaynak yasası)")
    assert (sb / TMP_ARTIGI).exists(), (
        "tek kaynak `tmp*.tmp`i KAYBETTİĞİ hâlde artık hâlâ atlanıyor — `sprint` deseni kendi "
        "gövdesine kopyalamış, çivi yanlış sebeple yeşil kalırdı")

    z, _, kod = _paket()
    assert kod == 200, f"uç {kod} döndü"
    assert "state/stamp.json" not in z.namelist(), (
        "tek kaynağa eklenen desen UÇTA hüküm doğurmadı — `api_debug_export` ikinci bir tanım "
        "taşıyor")
    assert "stamp.json" in json.loads(z.read("manifest.json")).get("disarida_birakilan_gecici", []), (
        "dışlama olmuş ama manifest'e yazılmamış — beyansız atlama")


# ==================================================================================================
# 6 — BEDEL YASASI: adı önceden bilinmeyen artık atlandıysa İZ kalır
# ==================================================================================================
def test_6_olay_gecici_artiklari_ADIYLA_tasir_icerik_TASIMAZ(sandbox_state):
    """Kum havuzu kopyası bir dosyayı atladığında tek iz `sprint_kum_havuzu_atlandi` olayıdır ve o
    olay YALNIZ "adı önceden bilinmeyen" girdileri taşır (`_yalniz_desenle_atlanir`). Geçici
    artığın adı tanım gereği önceden bilinemez — `mkstemp` rastgele üretir — yani BİLDİRİMİN
    ASIL MÜŞTERİSİDİR. Bildirilmezse kopyalanmayan dosya izsiz yok olur ve desen bir gün meşru bir
    defteri yakalarsa körlük sessiz kalır.

    ALANLARDA YALNIZ AD: olay defteri panoya ve `ops/` sorgularına açıktır."""
    _canli_state_kur()
    _kum_havuzu()
    olaylar = [e for e in store.read_jsonl("events.jsonl")
               if e.get("event") == "sprint_kum_havuzu_atlandi"]
    assert len(olaylar) == 1, (
        f"kurulum desenle dosya atladı ama bilgi olayı TAM BİR kez yazılmadı ({len(olaylar)}) — "
        f"atlama sessiz, körlük ölçülemez")
    kayit = olaylar[0]
    adlar = kayit.get("adlar", [])
    for ad in (TMP_ARTIGI, SIR_ARTIGI):
        assert ad in adlar, (
            f"`{ad}` atlandı ama olayda YOK — adı `mkstemp` üretir, kodda YAZILI DEĞİLDİR; "
            f"bildirilmezse hiçbir iz kalmaz: {kayit!r}")
    assert "secrets.json" not in adlar, (
        f"`secrets.json` olayda — TAM AD kümesinde, adı kodda yazılı; bildirimde yeri yok: {kayit!r}")
    assert kayit.get("adet") == len(adlar), f"adet ↔ adlar ayrışık: {kayit!r}"
    assert NISAN not in str(kayit), f"olay kaydı dosya İÇERİĞİ taşıyor: {kayit!r}"


# ==================================================================================================
# 7 — YÜKLEM BİRLEŞİMİNİN SAF ÖLÇÜMÜ: iki sınıf birbirine sızmaz
# ==================================================================================================
def test_7a_bilesik_yuklem_iki_bacagin_BIRLESIMIDIR():
    """`kopyalanmaz_mi` iki soruyu TOPLAR, birini ötekinin yerine geçirmez. Birleşim yerine tek
    bacak yazılsaydı (ör. sır desenine `tmp*.tmp` eklemek) artık SIR SAYILIRDI ve manifest'in
    "kaç sır dışarıda kaldı" sayısı her artıkta sessizce şişerdi."""
    for ad in ("secrets.json", "auth.json", "secrets.json.bak-20260915T073825Z-tsk189",
               SIR_ARTIGI, TMP_ARTIGI):
        assert config.kopyalanmaz_mi(ad), f"`{ad}` bileşik yüklemde yakalanmıyor"
    for ad in ("portfolio.json", "goal.yaml", "events.jsonl") + ARTIK_OLMAYANLAR:
        assert not config.kopyalanmaz_mi(ad), f"`{ad}` bileşik yüklemde yakalanıyor — daraltma"


def test_7b_iki_sinif_birbirine_SIZMAZ():
    """SINIR ÖLÇÜMÜ. `.secrets_*.tmp` bir SIRDIR (içeriği operatör anahtar deposudur) ve sır
    bacağına aittir; `tmp*.tmp` sır DEĞİLDİR (içeriği HERHANGİ bir defter olabilir — sır da,
    `portfolio.json` da) ve geçici artık bacağına aittir. Sınıflar karışırsa iki bilgi birden
    kaybolur: manifest'in sır sayımı ve "bu artık gerçekten sır mı" sorusunun cevabı."""
    assert config.sir_dosyasi_mi(SIR_ARTIGI), (
        f"`{SIR_ARTIGI}` sır sayılmıyor — `secrets` atomik yazımının geçici dosyası operatör "
        f"anahtar deposunun İÇERİĞİNİ taşır ve adı `mkstemp` ile rastgeledir")
    assert not config.gecici_artik_mi(SIR_ARTIGI), (
        f"`{SIR_ARTIGI}` geçici artık bacağında da yakalanıyor — sınıf sınırı yok, manifest "
        f"alanları ayrışamaz")
    assert config.gecici_artik_mi(TMP_ARTIGI), f"`{TMP_ARTIGI}` geçici artık sayılmıyor"
    assert not config.sir_dosyasi_mi(TMP_ARTIGI), (
        f"`{TMP_ARTIGI}` SIR sayılıyor — sır değildir (içeriği herhangi bir defter olabilir); "
        f"sır sayılırsa manifest'in sır sayımı her artıkta şişer")


def test_7c_sir_deseni_gecici_artik_desenini_TASIMAZ():
    """TEK KAYNAK İKİ SABİTTİR, BİRİ DEĞİL: `SIR_DESENLERI` sır ailesini, `GECICI_ARTIK_DESENLERI`
    geçici artık ailesini tanımlar. Kolaycı çözüm (`tmp*.tmp`i sır desenine eklemek) 7b'yi kırar;
    bu çivi o çözümün sabit tarafını da kapatır ve `sprint.SKIP_COPY_PATTERNS`in sır desenlerinden
    türemeye DEVAM ettiğini ölçer (v524 çivi 7a ile aynı kimlik ölçümü)."""
    assert "tmp*.tmp" not in config.SIR_DESENLERI, (
        "geçici artık deseni SIR desen ailesine yazılmış — artık sır sayılır ve manifest'in sır "
        "sayımı şişer")
    assert ".secrets_*.tmp" in config.SIR_DESENLERI, (
        "`secrets` yazımının geçici dosyası sır desen ailesinde değil")
    assert sprint.SKIP_COPY_PATTERNS is config.SIR_DESENLERI, (
        "`sprint.SKIP_COPY_PATTERNS` `config.SIR_DESENLERI`den TÜREMİYOR — ikinci bir tanım var")
