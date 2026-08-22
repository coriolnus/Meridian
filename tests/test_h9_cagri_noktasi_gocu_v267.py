"""WP6-A / H9 Kademe B AÇIK KUYRUK KAPANIŞI — çağrı-noktası göçünün ENVANTER + EŞZAMANLILIK çivileri (v267).

Fonksiyon-başına çiviler zaten var: `test_wph_kapi_disi_yazim.py` (Kademe A/B: auth/memory/config/run)
ve `test_wph_kapi_disi_yazim_kademe_c.py` (Kademe C: skill_evolve/sprint_run/earnings/data/hermes)
taşınan her yolun kapıdan geçtiğini, biçim round-trip'ini ve replace-düşerse-eski-kalır atomikliğini
tek tek ölçer. Bu dosya o ikisinin ölçmediği ÜÇ sınıfı kapatır:

  1. ENVANTER ÇİVİSİ — fonksiyon-başına çivi yalnız ADI GEÇEN fonksiyonu korur; göç edilen bir
     MODÜLE yarın eklenen YENİ bir çıplak `open(...,'w')` / `Path.write_text` / elle `mkstemp`
     hiçbir mevcut çiviye takılmadan kapı-dışı sınıfını yeniden açardı. Burada göç edilen dokuz
     modülün TAMAMI AST ile taranır: Call düğümleri sayılır (docstring/yorum metnindeki eski kalıp
     adları SAYILMAZ — mezar taşı anlatısı yasal), çıplak yazım sıfır olmalı.
  2. POZİTİF KONTROL — "tarayıcı hiçbir şey bulamadı" ile "tarayıcı kör" ayırt edilemez (totoloji
     riski). Dedektör, eski kalıpların dördünü de içeren sentetik kaynağa karşı koşulur ve DÖRDÜNÜ
     de yakalamak zorundadır.
  3. auth._write EŞZAMANLI İKİ YAZAR — eski `_write` SABİT tmp adı (`.json.tmp`) kullanıyordu: iki
     yazar aynı geçici dosyaya yazar, biri diğerinin baytlarını ezer ve `os.replace` yarı-yazılmış
     kimlik defterini yerine koyardı. Kapı (benzersiz mkstemp + flock + süreç-içi RLock) bunu
     yapısal olarak kapatır. Burada iki İPLİK aynı anda yazıp her aralıkta defterin GEÇERLİ ve TAM
     tek bir yazarın kaydı olduğu ölçülür; süreçler-ARASI katman ayrıca
     `test_wph_store_kapi.py::test_flock_SURECLER_ARASI_gercekten_bekletir`te kanıtlıdır (auth da
     aynı `store.write_text`e indiği için o garantiyi devralır).

ÖLÇÜLEMEYENLER (UYDURMA YASAĞI — bilerek burada YOK): `run.replay_seed` uçtan-uca davranışı (bars
yükleme + tam backtest gerektirir; arşiv yazımının yapısal çivisi Kademe B'de) ve
`skill_evolve.draft_revision` uçtan-uca (hermes ajan çağrısı gerektirir; stub'lı round-trip çivisi
Kademe C'de). İkisini burada tekrar ölçmek kanıt eklemez, süre ekler.

YASA-6 OKUYUCU: bu çivilerin okuyucusu H9 kapanış hükmü (Rol-1) + gelecekteki kapı-dışı regresyonun
ilk tanığı olan CI koşusu.
"""
from __future__ import annotations

import ast
import json
import pathlib
import textwrap
import threading

from meridian import auth

MERIDIAN = pathlib.Path(__file__).resolve().parent.parent / "meridian"

# H9 göç envanterinin TAMAMI (Kademe A/B: auth, memory, run, config · Kademe C: skill_evolve,
# sprint_run, earnings, adapters/data, hermes). store.py kapının KENDİSİdir, taranmaz;
# secrets.py kapıyı BİLEREK kullanmaz (0600 + log'a hiç dokunmama sözleşmesi, modülün kendi
# docstring'i) ve envanterde hiç yer almadı — listede yokluğu bilinçli.
GOC_EDILEN_MODULLER = [
    "auth.py", "memory.py", "run.py", "config.py",
    "skill_evolve.py", "sprint_run.py", "earnings.py", "hermes.py",
    "adapters/data.py",
]

# Kapı çağrısının yasal tabanları: `store.write_text(...)` ve data.py'deki `_st.write_text(...)`.
# Bunun DIŞINDA bir tabana asılı `.write_text` (ör. `path.write_text`) KIRPMA sınıfıdır.
_KAPI_TABANLARI = {"store", "_st"}


def _ciplak_yazimlar(kaynak: str, dosya: str) -> list[str]:
    """Kaynaktaki kapı-dışı yazım ÇAĞRILARINI listeler (yalnız ast.Call — yorum/docstring metni
    sayılmaz). Dört eski kalıp aranır: (1) yazma modlu open/fdopen, (2) elle mkstemp,
    (3) elle NamedTemporaryFile, (4) kapı-tabanı olmayan .write_text/.write_bytes."""
    bulgular: list[str] = []
    for node in ast.walk(ast.parse(kaynak, filename=dosya)):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if isinstance(f, ast.Name):
            ad = f.id
        elif isinstance(f, ast.Attribute):
            ad = f.attr
        else:
            continue
        if ad in ("mkstemp", "NamedTemporaryFile"):
            bulgular.append(f"{dosya}:{node.lineno}: elle tmp kalıbı ({ad})")
        elif ad in ("open", "fdopen"):
            mod = None
            if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                mod = node.args[1].value
            for kw in node.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mod = kw.value.value
            if isinstance(mod, str) and "w" in mod:
                bulgular.append(f"{dosya}:{node.lineno}: {ad}(mode={mod!r})")
        elif ad in ("write_text", "write_bytes"):
            taban = f.value.id if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) else None
            if taban not in _KAPI_TABANLARI:
                bulgular.append(f"{dosya}:{node.lineno}: kapı-dışı .{ad} (taban={taban})")
    return bulgular


# =================================================================================================
# 1) ENVANTER ÇİVİSİ — göç edilen dokuz modülde çıplak yazım çağrısı KALMADI
# =================================================================================================
def test_envanter_goc_edilen_modullerde_ciplak_yazim_kalmadi():
    """Modül GENİŞLİĞİNDE tarama: fonksiyon-başına çivilerin kör noktası olan "yeni eklenen çıplak
    yazım" sınıfını kapatır. hermes.py de listede — sahibi başka tur olsa da ölçüm salt-okurdur ve
    bugünkü gerçek (iki yazımı da kapıdan geçmiş) çiviye dönüşür."""
    bulgular: list[str] = []
    for m in GOC_EDILEN_MODULLER:
        p = MERIDIAN / m
        assert p.is_file(), f"envanter modülü kayıp: {p} — liste bayatladıysa GERÇEĞİ yaz, çiviyi silme"
        bulgular += _ciplak_yazimlar(p.read_text(), m)
    assert bulgular == [], (
        "H9 kapı-dışı yazım sınıfı YENİDEN AÇILDI — bu yollar store.write_text/write_json "
        "kapısına taşınmalı (atomik tmp+fsync+os.replace + flock):\n  " + "\n  ".join(bulgular))


def test_envanter_skill_evolve_replace_yalniz_onay_yolunda():
    """`skill_evolve` içindeki iki `os.replace` bilinçli İSTİSNADIR: apply_revision'ın TAM-dosya
    yer değiştirmeleri (SKILL.md ↔ .bak/.v2-draft) — kısmi yazım değil atomik rename. Bu çivi
    istisnanın BÜYÜMEDİĞİNİ ölçer: modülde ikiden fazla os.replace belirirse ya yeni bir elle
    yazım kalıbıdır ya da envanter bilinçli genişletilmiştir; ikisi de görünür olmalı."""
    kaynak = (MERIDIAN / "skill_evolve.py").read_text()
    n = sum(1 for node in ast.walk(ast.parse(kaynak))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "replace"
            and isinstance(node.func.value, ast.Name) and node.func.value.id == "os")
    assert n == 2, f"skill_evolve'de os.replace sayısı {n} (beklenen 2: apply_revision'ın rename çifti)"


# =================================================================================================
# 2) POZİTİF KONTROL — dedektör dört eski kalıbı da gerçekten YAKALIYOR
# =================================================================================================
def test_envanter_dedektoru_pozitif_kontrol():
    """"Sıfır bulgu" ancak dedektörün gördüğü kanıtlanınca anlam taşır. Sentetik kaynak, göçten
    ÖNCEKİ dört kalıbı birebir içerir; dördü de yakalanmak zorunda. Docstring içindeki kalıp adı
    ise YAKALANMAMALI (mezar taşı anlatısı yasaldır — Call değildir)."""
    sentetik = textwrap.dedent('''
        def eski_yazim(path, veri):
            """docstring'de open(p, "w") ve mkstemp GEÇER ama sayılMAZ."""
            fd, tmp = tempfile.mkstemp(dir=".")
            with os.fdopen(fd, "w") as f:
                f.write(veri)
            path.write_text(veri)
            tempfile.NamedTemporaryFile(dir=".", delete=False)
    ''')
    bulgular = _ciplak_yazimlar(sentetik, "sentetik.py")
    assert len(bulgular) == 4, f"dedektör kör: 4 kalıptan {len(bulgular)} yakalandı — {bulgular}"
    for kalip in ("mkstemp", "fdopen", "write_text", "NamedTemporaryFile"):
        assert any(kalip in b for b in bulgular), f"dedektör {kalip} kalıbını kaçırdı: {bulgular}"


def test_envanter_dedektoru_kapiyi_yasal_sayar():
    """Ters yönlü kontrol: kapı çağrıları (store/_st.write_text) ve okuma-modlu open BULGU DEĞİL —
    aksi hâlde envanter çivisi geçerli kodu da kırmızıya boyar ve gevşetilirdi."""
    sentetik = textwrap.dedent('''
        def yasal(path):
            store.write_text("lessons.md", "x")
            _st.write_text("bars/AAPL.csv", "y")
            with open(path) as f:
                return f.read()
    ''')
    assert _ciplak_yazimlar(sentetik, "sentetik.py") == []


# =================================================================================================
# 3) auth._write — EŞZAMANLI İKİ YAZAR ÇARPIŞMAZ (eski sabit-tmp arızasının çivisi)
# =================================================================================================
def _defteri_ham_oku(sandbox_state) -> dict:
    """auth.json'u `auth._read`ın SESSİZ `{}` yedeğine düşmeden okur: bozuk JSON burada test
    HATASIDIR, gizlenen bir arıza değil (dedektör kendi ölçtüğünü yutmasın)."""
    return json.loads((sandbox_state / "auth.json").read_text())


def test_auth_write_eszamanli_iki_yazar_carpismaz(sandbox_state):
    """İki iplik aynı anda `auth._write` çağırır; her yazımdan sonra defter GEÇERLİ JSON ve TAM
    olarak tek bir yazarın kaydıdır (bayt karışımı/yarım dosya = eski sabit-tmp arızası). Sonda:
    tmp artığı yok, 0600 korunur. Süreç-içi serileşme kapının RLock'undandır; süreçler-arası
    eşdeğeri test_wph_store_kapi'daki flock kanıtından devralınır."""
    dolgu = 512     # kısa yazım yarım-dosyayı yakalayamaz; iki payload aynı boyda ama farklı bayt
    payloads = {
        "A": {"yazar": "A", "dolgu": "a" * dolgu},
        "B": {"yazar": "B", "dolgu": "b" * dolgu},
    }
    hatalar: list[BaseException] = []

    def yaz(kim: str) -> None:
        try:
            for _ in range(20):
                auth._write(payloads[kim])
                d = _defteri_ham_oku(sandbox_state)         # bozuksa json.loads BURADA patlar
                # o an diskte HANGİ yazarın kaydı olursa olsun kayıt TAM olmalı
                assert d in payloads.values(), f"karışık/yarım kayıt: {str(d)[:120]}"
        except BaseException as e:                           # iplikteki assert ana ipliğe taşınmalı
            hatalar.append(e)

    t1 = threading.Thread(target=yaz, args=("A",))
    t2 = threading.Thread(target=yaz, args=("B",))
    t1.start(); t2.start()
    t1.join(timeout=60); t2.join(timeout=60)
    assert not (t1.is_alive() or t2.is_alive()), "yazar iplikleri kilitlendi (deadlock şüphesi)"
    assert hatalar == [], f"eşzamanlı yazımda çarpışma: {hatalar[:3]}"
    assert _defteri_ham_oku(sandbox_state) in payloads.values()
    artik = [p.name for p in sandbox_state.iterdir() if p.name.endswith(".tmp")]
    assert artik == [], f"tmp artığı sızdı: {artik}"
    mode = (sandbox_state / "auth.json").stat().st_mode & 0o777
    assert mode == 0o600, f"auth.json izni {oct(mode)} — eşzamanlı yazım 0600 sözleşmesini bozdu"


def test_auth_write_davranis_karakutu_pozitif_kontrol(sandbox_state):
    """Eşzamanlılık testinin ölçüm düzeneği VAKUMDA geçmesin: tek yazım sonrası diskteki baytlar
    `json.dumps(payload, indent=2)` ile BİREBİR (biçim sözleşmesi: _read/json.loads round-trip'i)
    ve tmp artığı yok. Kapı sarmalanmadan (monkeypatch'siz) ölçülür — kara kutu."""
    payload = {"yazar": "tek", "algo": "scrypt-n15-r8-p1"}
    auth._write(payload)
    assert (sandbox_state / "auth.json").read_text() == json.dumps(payload, indent=2)
    assert [p.name for p in sandbox_state.iterdir() if p.name.endswith(".tmp")] == []
