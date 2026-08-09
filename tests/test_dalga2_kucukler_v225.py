"""test_dalga2_kucukler_v225.py — DALGA-2 AJAN D (küçükler): üç AYRI dosya, üç ölçülmüş borç.

BU DOSYANIN ÇİVİLEDİĞİ ÜÇ KUSUR (docs/SABAH-TRIYAJI-2026-08-09.md kalem 1 / 12 / 10):

  1. KALEM 1 — systemd exit-143. Her `systemctl restart`/`stop` durdurmada SIGTERM yollar;
     ExecStart'taki ana süreç `uv run`dır ve çocuğu (uvicorn) SIGTERM'le ölünce KENDİSİ 143
     (128+SIGTERM) EXIT KODUYLA çıkar. Varsayılan SuccessExitStatus SIGTERM SİNYALİNİ temiz sayar
     ama `uv`nin PROPAGE ETTİĞİ 143 KODUNU saymaz → birim "failed" → OnFailure her dağıtımda ateşler.
     `SuccessExitStatus=143` temiz durdurmayı susturur, GERÇEK çöküşü (başka kod / SIGKILL 137) DEĞİL.

  2. KALEM 12 — skills.py `envanter()` mezar-taşı docstring'i bayattı: `skills/_emekli/shadow`
     hayaletini present-tense ("da sayar") örnek olarak anıyordu ama o dizin v121'de HAYALET sınıfına
     alınıp kaldırıldı. Tarihçe cümlesi ölçülen gerçekle (envanter()'in kendi `fark` kovaları +
     docs/CIFT-KAYNAK-TARAMASI-2026-08-09.md §245) tazelendi. Assert/DAVRANIŞ değişmedi, yalnız yorum.

  3. KALEM 10 — pano `opCancelOpen` + süpürücü olay çekmecesi v220/v221'in `siniflar` /
     `mirror_cancel_sinif_dokumu` alanını GÖSTERMİYORDU (YASA-6: yazılan alanın okuyucusu yok).
     Sınıf dökümü (giris/koruma/yabanci) artık hem iptal tuşunun sonucunda hem olay akışında OKUNUR;
     renk yalnız anomalide (süpürücü bilgi olayı `mut` çizilir), satır-içi script yok (CSP).

TESTLER KAYNAĞA + DAVRANIŞA BAKAR (repo deseni v139/v199/v219): saf EV_TR üreteci Node'da GERÇEKTEN
koşturulur. UYGULAMA YÜKLENMEZ (oturum sözleşmesi §5 + iş emri): statik dilim + Node harness.
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
WEB = REPO / "meridian" / "web"
APPJS = (WEB / "app.js").read_text()
SKILLSPY = (REPO / "meridian" / "skills.py").read_text()
ALPACAPY = (REPO / "meridian" / "adapters" / "alpaca.py").read_text()
APIPY = (REPO / "meridian" / "api.py").read_text()
LOOPPY = (REPO / "meridian" / "loop.py").read_text()
SERVICE = (REPO / "deploy" / "oracle-a1" / "meridian.service").read_text()

NODE = shutil.which("node")


# =================================================================================================
# 0 · DİLİM ÇIKARICI — saf üreteçleri Node'da koşturmak için (v219/v200 `_fn`i)
# =================================================================================================
def _fn(ad: str, kaynak: str = APPJS) -> str:
    for bas in (f"async function {ad}(", f"function {ad}(", f"class {ad} "):
        if bas in kaynak:
            i = kaynak.index(bas)
            parcalar = []
            for ln in kaynak[i:].splitlines(keepends=True):
                parcalar.append(ln)
                if ln.rstrip("\n") == "}":
                    break
            return "".join(parcalar)
    for anahtar in (f"window.{ad} = ", f"const {ad} = "):
        if anahtar in kaynak:
            break
    else:
        raise AssertionError(f"{ad}: kaynakta tanım bulunamadı")
    i = kaynak.index(anahtar)
    parcalar, derinlik = [], 0
    for ln in kaynak[i:].splitlines(keepends=True):
        parcalar.append(ln)
        govde = re.sub(r'"[^"]*"|\'[^\']*\'|`[^`]*`', "", ln)
        govde = re.sub(r"//.*$", "", govde)
        derinlik += sum(govde.count(c) for c in "([{") - sum(govde.count(c) for c in ")]}")
        if derinlik <= 0 and govde.rstrip().endswith(";"):
            break
    return "".join(parcalar)


# =================================================================================================
# 1 · KALEM 1 — systemd SuccessExitStatus=143 (kaynak)
# =================================================================================================
def _service_bolum(bolum_ad: str = "Service") -> list[tuple[str, str]]:
    """systemd birim ayrıştırıcısı — satır-sonu `#` KIRPILMAZ (değerin parçasıdır)."""
    out, bolum = [], None
    for ham in SERVICE.splitlines():
        s = ham.strip()
        if not s or s.startswith("#") or s.startswith(";"):
            continue
        if s.startswith("[") and s.endswith("]"):
            bolum = s[1:-1]
            continue
        if bolum == bolum_ad and "=" in s:
            k, _, v = s.partition("=")
            out.append((k.strip(), v.strip()))
    return out


def test_kalem1_success_exit_status_143():
    """`SuccessExitStatus=143` [Service]'te ve DEĞERİ tam 143 (128+SIGTERM). Yoksa her restart
    OnFailure'ı yanlış ateşler; N1 kanalı açılınca gerçek arıza gürültüde boğulur."""
    degerler = [v for k, v in _service_bolum() if k == "SuccessExitStatus"]
    assert degerler == ["143"], f"SuccessExitStatus tam '143' değil: {degerler}"


def test_kalem1_direktif_satir_sonu_yorumu_tasimaz():
    """systemd `SuccessExitStatus=143  # ...` satırındaki `#`i değerin parçası sayar (test_h3_tur2
    4. sınıfı). Gerekçe ÖNCEKİ yorum satırlarında durur, direktifin sonunda DEĞİL."""
    for ham in SERVICE.splitlines():
        if ham.strip().startswith("SuccessExitStatus"):
            assert "#" not in ham, f"direktif satırında satır-sonu yorumu: {ham!r}"


def test_kalem1_gerekce_yazili_YASA4():
    """Sessiz ekleme yok (YASA 4 ruhu). Gerekçe ExecStart ile direktif arasındaki yorum bloğunda:
    neden-kapı (OnFailure) + arıza şekli (SIGTERM/143/128+15) beyanlı."""
    i = SERVICE.index("SuccessExitStatus=143")
    blok = SERVICE[SERVICE.rindex("ExecStart", 0, i):i]
    assert len(blok) > 200, "SuccessExitStatus gerekçe bloğu şüpheli derecede kısa"
    for kanit in ("OnFailure", "SIGTERM", "143", "128+15"):
        assert kanit in blok, f"gerekçe `{kanit}` dayanağını taşımıyor"


def test_kalem1_kardes_birimlere_sizmadi():
    """İş emri YALNIZ meridian.service'i yazılabilir kıldı. 143 kardeş birimlere kopyalanmadı
    (barsarchive/backup restart'ta 143 üretmez; oraya eklemek ölçülmemiş bir varsayım olurdu)."""
    for kardes in ("meridian-barsarchive.service", "meridian-backup.service"):
        p = REPO / "deploy" / "oracle-a1" / kardes
        if p.exists():
            assert "SuccessExitStatus" not in p.read_text(), f"{kardes}: ölçülmeden 143 sızmış"


# =================================================================================================
# 2 · KALEM 12 — skills.py envanter() mezar-taşı docstring'i (yalnız yorum)
# =================================================================================================
def _envanter_docstring() -> str:
    m = re.search(r'def envanter\(\) -> dict:\n\s*"""(.*?)"""', SKILLSPY, re.S)
    assert m, "envanter() docstring bulunamadı"
    return m.group(1)


def test_kalem12_hayalet_dizin_GERCEKTEN_yok():
    """Docstring'in yeni iddiasının DAYANAĞI: mezar taşı gerçekten kaldırıldı. Dizin geri gelirse
    bu test kırmızı olur ve 'v121'de kaldırıldı' cümlesi yalana döner (test_skill_cleanup_v121
    ile aynı hüküm, farklı kapıdan)."""
    assert not (REPO / "skills" / "_emekli" / "shadow").exists(), \
        "shadow hayalet dizini geri gelmiş — docstring'i ve v121 hükmünü yalanlar"


def test_kalem12_docstring_hayaleti_PRESENT_TENSE_saymiyor():
    """Bayat cümle 'da sayar' idi (present-tense, dizin varmış gibi). Artık geçmiş zaman +
    kaldırma beyanı; örnek tarihçeden DÜŞMEDİ (bağlam korunur) ama canlıymış gibi okunMUYOR."""
    ds = _envanter_docstring()
    assert "da sayar" not in ds, "docstring hayaleti hâlâ present-tense sayıyor"
    assert "skills/_emekli/shadow" in ds, "mezar taşı örneği tarihçeden silinmiş (bağlam kayboldu)"
    assert "v121" in ds and ("HAYALET" in ds or "kaldırıl" in ds), \
        "hayaletin v121'de kaldırıldığı beyan edilmiyor"


def test_kalem12_docstring_OLCUM_referansi_tasiyor():
    """Tarihçe ölçülen gerçeğe bağlanır: envanter()'in KENDİ fark kovaları + CIFT-KAYNAK dokümanı.
    Bir tahmin değil, yeniden ölçülebilir bir hüküm."""
    ds = _envanter_docstring()
    assert "arsiv_dizin_ama_kayitsiz" in ds and "arsiv_dizin_skill_md_yok" in ds, \
        "hayaleti yakalayan `fark` kovaları referans verilmemiş"
    assert "CIFT-KAYNAK-TARAMASI-2026-08-09" in ds, "CIFT-KAYNAK dokümanı (§245) referansı yok"


def test_kalem12_DAVRANIS_degismedi():
    """YALNIZ docstring: fark kovalarının ADLARI kodda AYNEN, AKTIF/ARSIV sabitleri yerinde,
    envanter() saf-okuma (hiçbir yazım eklenmedi)."""
    for kova in ("arsiv_dizin_ama_kayitsiz", "kayitli_arsiv_ama_dizinsiz", "arsiv_dizin_skill_md_yok",
                 "kayitsiz_klasor", "kayitli_aktif_klasorsuz", "arsiv_disi_girdi"):
        assert f'"{kova}"' in SKILLSPY, f"fark kovası kodda yok — davranış değişmiş: {kova}"
    assert 'AKTIF, ARSIV = "aktif", "arsiv"' in SKILLSPY
    govde = SKILLSPY[SKILLSPY.index("def envanter() -> dict:"):SKILLSPY.index("def catalog()")]
    assert "store.write" not in govde and "append_jsonl" not in govde, \
        "envanter() bir yere yazıyor — 'SAF OKUMA' beyanı bozuldu"


# =================================================================================================
# 3 · KALEM 10 — pano: opCancelOpen sınıf dökümü + süpürücü olay çekmecesi (kaynak + Node)
# =================================================================================================
def test_kalem10_opCancelOpen_siniflari_OKUR():
    """İptal tuşunun sonucu artık `siniflar`(giris/koruma/yabanci) + `foreign` + korunan bacağın
    `neden`ini basar (triyaj kalem 10). Eski satır yalnız 'İptal: N · Korunan: M' diyordu —
    korumanın DOKUNULMADIĞI görünmezdi."""
    g = _fn("opCancelOpen")
    assert "r.siniflar" in g, "opCancelOpen `siniflar` alanını okumuyor"
    for alan in ("s.giris", "s.koruma", "s.yabanci"):
        assert alan in g, f"opCancelOpen sınıf dökümünü çizmiyor: `{alan}`"
    assert "foreign" in g, "opCancelOpen yabancı (operatör) emirlerini göstermiyor"
    assert "neden" in g and '"koruma"' in g, "korunan koruma bacağının gerekçesi okunmuyor"
    assert "?? 0" in g, "ölçülemeyen sınıf sayısı 0'a düşürülmeden basılıyor (UYDURMA riski)"
    # CSP + alarm bütçesi: alert yolu; satır-içi script YOK, kendi anomali rengini KATMAZ.
    assert "<script" not in g and "onclick=" not in g
    for renk in ('class="neg"', 'class="warn"', "var(--red)"):
        assert renk not in g, f"iptal özetine anomali rengi sızmış: {renk}"


# Süpürücü ailesinin olay gövdeleri UÇTAN alındı (kwargs adları birebir; aşağıda üretici de doğrulanır).
_SUPURUCU_OLAYLARI = {
    "mirror_cancel_sinif_dokumu": {"giris": 3, "koruma": 4, "yabanci": 1, "cancelled": 3,
                                   "iptal_coidler": ["P-x", "P-y", "P-z"],
                                   "korunan_coidler": ["P-KORUMA-a", "P-KORUMA-b"]},
    "control_cancel_open": {"cancelled": 2, "kept": 4, "ok": True},
    "mirror_stale_entries_cancelled": {"gate": "gunluk_kadans", "date": "2026-08-09",
                                       "cancelled": 1, "kept": 4, "foreign": 1},
    "mirror_entries_cancelled": {"gate": "halt", "date": "2026-08-09",
                                 "cancelled": 0, "kept": 4, "foreign": 0},
}


@pytest.fixture(scope="module")
def ev_tr_ciktilari():
    if NODE is None:
        pytest.skip("node yok")
    betik = (_fn("EV_TR") + "\nconst V = " + json.dumps(_SUPURUCU_OLAYLARI, ensure_ascii=False) + ";\n"
             + "const out = {};\n"
             + "for (const [ad, e] of Object.entries(V)) out[ad] = EV_TR[ad] ? EV_TR[ad](e) : null;\n"
             + "out._bilinmeyen = EV_TR['bu_olay_yok'] ? 'VAR' : null;\n"
             + "process.stdout.write(JSON.stringify(out));")
    p = subprocess.run([NODE, "-e", betik], capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, f"EV_TR harness Node'da patladı:\n{p.stderr[-3000:]}"
    return json.loads(p.stdout)


@pytest.mark.parametrize("ad", list(_SUPURUCU_OLAYLARI))
def test_kalem10_supurucu_olayi_TURKCE_cumleye_baglandi(ad, ev_tr_ciktilari):
    """Her süpürücü olayı bir CÜMLEdir, ham bir jeton değil: en az üç kelime, ham olay adını
    İÇERMEZ. Yoksa 'süpürücü olay çekmecesi görünür' iddiası sessizce yanlış olurdu."""
    c = ev_tr_ciktilari[ad]
    assert c, f"{ad}: EV_TR'de çevirisi yok — çekmecede ham adla akıyor"
    assert ad not in c, f"{ad}: cümle hâlâ ham olay adını basıyor"
    assert len(c.split()) >= 3, f"{ad}: cümle değil, jeton: {c!r}"


def test_kalem10_sinif_dokumu_CUMLEDE_gorunur(ev_tr_ciktilari):
    """v220 sınıf dökümü akışta OKUNUR: üç sınıf da sayısıyla cümlede; `foreign` de (stale/HALT)."""
    c = ev_tr_ciktilari["mirror_cancel_sinif_dokumu"]
    assert "giriş 3" in c and "koruma 4" in c and "yabancı 1" in c, \
        f"sınıf dökümü (giris/koruma/yabanci) cümlede yok: {c!r}"
    assert "korunan bacak: 2" in c, "korunan koruma bacağı sayısı okunmuyor"
    assert "1 yabancı" in ev_tr_ciktilari["mirror_stale_entries_cancelled"], \
        "günlük kadans süpürücüsü `foreign` alanını göstermiyor"


def test_kalem10_supurucu_cevirileri_ANOMALI_rengi_KATMAZ(ev_tr_ciktilari):
    """RENK YALNIZ ANOMALİDE: süpürücü bir BİLGİ olayıdır (koruma DOKUNULMADI'yı raporlar),
    obs.log ile `mut` çizilir. Çeviri kendi içinde renk sınıfı/jetonu ENJEKTE ETMEZ."""
    for ad, c in ev_tr_ciktilari.items():
        if not isinstance(c, str):
            continue
        for renk in ('class="neg"', 'class="warn"', 'class="pos"', "var(--red)", "var(--amber)"):
            assert renk not in c, f"{ad}: bilgi olayına anomali rengi sızmış: {renk}"


def test_kalem10_cevirisiz_olay_HAM_ADLA_akmaya_DEVAM_eder(ev_tr_ciktilari):
    """Mevcut davranış KORUNUR: sözlükte olmayan olay gizlenmez, ham adıyla akar."""
    assert ev_tr_ciktilari["_bilinmeyen"] is None
    assert 'class="chain">${esc(name)}' in _fn("eventsFeed"), "çevirisiz olay ham adla çizilmiyor"


def test_kalem10_UYDURMA_YASAGI_her_ceviri_URETICI_tasir():
    """Ölü çeviri yok (test_gorunurluk_v219 UYDURMA çivisiyle aynı ruh): çevirdiğim her süpürücü
    olayının GERÇEK bir `obs.log` üreticisi var (adlar UÇTAN, varsayılmadı)."""
    assert 'EV_SUPURME_SINIFLARI = "mirror_cancel_sinif_dokumu"' in ALPACAPY
    assert "obs.log(EV_SUPURME_SINIFLARI" in ALPACAPY, "sınıf dökümü olayının üreticisi yok"
    assert 'obs.log("control_cancel_open"' in APIPY, "pano-tuşu olayının üreticisi yok"
    assert 'EV_STALE_ENTRIES_CANCELLED = "mirror_stale_entries_cancelled"' in LOOPPY
    assert 'EV_MIRROR_ENTRIES_CANCELLED = "mirror_entries_cancelled"' in LOOPPY
    assert "obs.log(olay" in LOOPPY, "iki kadans olayı da bu tek `obs.log(olay, ...)`den düşer"


def test_kalem10_node_check_temiz():
    """Satır-içi script yok + geçerli sözdizimi (CSP + node --check)."""
    if NODE is None:
        pytest.skip("node yok")
    p = subprocess.run([NODE, "--check", str(WEB / "app.js")], capture_output=True, text=True)
    assert p.returncode == 0, f"node --check app.js patladı:\n{p.stderr[-2000:]}"
