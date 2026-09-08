"""v452 — TSK-176 Faz A1: dağıtım playbook'unun TEK-KAYNAK listeleri + dört çıkarılmış betik.

NUMARA KİMLİKTİR: v452 planda (`docs/superpowers/plans/2026-09-08-ansible-a1-dagit.md`, Global
Constraints) SABİT verildi; ölçüldü (2026-09-08, `ls tests/`): `v45x` aralığında yalnız
`test_edg086_sayim_v450.py` + `test_ansible_a0_v451.py` var, en büyük kullanılan `vNNN` `v451` —
çakışma YOK.

KAPSAM — BÖLÜM A (Task 1). İki iddia ailesi:

  A1..A3  TEK KAYNAK GEÇİŞİNİN KÖPRÜSÜ. `deploy/ansible/vars/dagit_vars.yml` bugün dagit.sh'ın
          listelerinin İKİNCİ kopyasıdır ve iki kopya sessizce ayrışır (Tek-kaynak yasası).
          Geçiş süresince (Task 3'e kadar) ayrışmayı bu çiviler KIRMIZI yapar: küme eşitliği
          hem yön hem içerik ölçer. Task 3'te dagit.sh listeleri SİLİNİNCE bu üç çivi
          `dagit.yml`e taşınır — iddia (playbook ile dagit aynı listeyi kullanır) korunur,
          kaynak değişir.

  A4      DÖRT BETİK GERÇEKTEN KOŞAR. Gömülü çok-satır python/bash dosyaya çıkarıldı (A0 kuralı
          + 2026-07-30 IndentationError vakası). Çıkarılan gövde, ÇAĞRILMADIĞI sürece bir kopya
          değil bir ÖLÜ DOSYADIR: her betik komut satırından, operatörün/playbook'un koşacağı
          BİÇİMDE koşturulur (CLAUDE.md §6: "ops aracı tesliminden önce operatörün koşacağı
          biçimde bir kez koş" — 18 çivi yeşilken `--uygula` sessizce yok sayılıyordu).

YÖNTEM — ÇİVİ YEŞİLİ KANIT DEĞİLDİR. Her betiğin her dalı (KOPYALA/ENGEL · taze/bayat/ölçülemedi ·
VAR/YOK/token-yok · IHLAL/BEKLENEN/temiz) AYRI bir çivi taşır ve hepsi POZİTİF+NEGATİF çifttir:
tek yönlü bir çivi, betik her zaman aynı cevabı verse de yeşil kalırdı.

A1'E HİÇBİR BAĞLANTI YOK. `dogrulama_anahtar.py` gerçek bir HTTP sunucusuna karşı koşar — ama o
sunucu testin KENDİ `http.server`ıdır (127.0.0.1, rastgele port). `kod_tazelik.sh` sahte
`systemctl`/`date` şimleriyle koşar. `dagit.sh` HİÇ koşturulmaz (yalnız `bash -n`).

ÖLÇÜLEN AYRIŞMA — PLAN METNİ ↔ TAŞINAN DAVRANIŞ (dürüst beyan, uydurma yasağı):
  * Plan Task 1 `ops/state_fark_hukmu.py` için `HUKUM=KOPYALA|ENGEL|OPERATOR` diyor; dagit.sh'ın
    gömülü gövdesi YALNIZ `KOPYALA` ve `ENGEL` basıyor ("operatöre bırakılan" bash tarafının
    ETİKETİdir, hükmün kendisi değil). Global Constraint "davranış birebir" ağır bastı:
    üçüncü bir jeton eklenmedi, v172'nin beş davranış çivisi aynı sözlükle konuşmayı sürdürüyor.
  * `dogrulama_anahtar.py` uzak gövdedeki `curl`ü `urllib.request` ile değiştirir (aynı istek:
    GET + `x-meridian-token` başlığı + 90 sn zaman aşımı). Gerekçe dosyanın kendi başlığında.
"""

from __future__ import annotations

import http.server
import json
import os
import pathlib
import re
import subprocess
import sys
import threading

import pytest
import yaml

REPO = pathlib.Path(__file__).resolve().parent.parent
DAGIT = REPO / "dagit.sh"
VARS_YML = REPO / "deploy" / "ansible" / "vars" / "dagit_vars.yml"
STATE_FARK = REPO / "ops" / "state_fark_hukmu.py"
ARTEFAKT = REPO / "ops" / "artefakt_tazelik.py"
DOGRULAMA = REPO / "deploy" / "oracle-a1" / "dogrulama_anahtar.py"
KOD_TAZELIK = REPO / "deploy" / "oracle-a1" / "kod_tazelik.sh"


def _dagit_metin() -> str:
    return DAGIT.read_text(encoding="utf-8")


def _dagit_kod_satirlari() -> list[str]:
    """dagit.sh'ın YORUM OLMAYAN satırları.

    MUTASYONLA ÖLÇÜLDÜ (2026-09-08, bu turun M12/M13 mutasyonları): çağrı çivileri düz
    `"<yol>" in metin` ile yazılmıştı ve betiğin GEREKÇE YORUMLARINDA aynı yol geçtiği için
    çağrıyı bozan mutasyon YEŞİL kaldı — çivi hedefini kaybetmişti. Yorum tarihçedir, kod
    hükümdür (aynı sınıf: "yorum tarihçe, kod hüküm", 2026-09-06)."""
    return [ln for ln in _dagit_metin().splitlines() if not ln.lstrip().startswith("#")]


def _dagit_cagri_satirlari() -> list[str]:
    """dagit.sh'ın yorum OLMAYAN **ve** `echo`/`printf` ile BAŞLAMAYAN satırları.

    İKİNCİ MUTASYON TURU (çekişmeli inceleme, 2026-09-08): yorumları elemek YETMEDİ. [5b]
    fail-closed bloğunun onarım reçetesi bir yorum değil, bir `echo`dur ve aranan yolu AYNEN
    taşır (`Bak: ssh …` satırı). Gerçek çağrı satırı bozulduğunda üç çivi de (A5b · A5d ·
    v266) YEŞİL kaldı — ölçüldü. Operatöre BASILAN bir metin, kapının KOŞTUĞUNUN kanıtı
    değildir."""
    return [ln for ln in _dagit_kod_satirlari() if not re.match(r"\s*(echo|printf)\b", ln)]


#: [5b] ÇAĞRISININ BİÇİMİ — satır başı atama, `${SSH[@]}` sarmalı, betiğin tam yolu. İddia bir
#: dizgenin metinde GEÇMESİNE değil ÇAĞRININ KENDİSİNE bağlanır (yukarıdaki mutasyon kaydı).
#: TEK KAYNAK: `tests/test_dagit_f9_beyan_v266.py` bunu İTHAL eder, kopyalamaz.
KOD_TAZELIK_CAGRI = re.compile(
    r'^\s*_tazelik="\$\("\$\{SSH\[@\]\}"\s+'
    r'"bash /opt/meridian/deploy/oracle-a1/kod_tazelik\.sh"\)"')


def _vars() -> dict:
    veri = yaml.safe_load(VARS_YML.read_text(encoding="utf-8"))
    assert isinstance(veri, dict), f"{VARS_YML}: kök düğüm dict değil"
    return veri


# =================================================================================================
# A0 — envanter: dosyalar yerinde
# =================================================================================================
def test_A0_task1_dosyalari_YERINDE():
    """Task 1'in üretmesi gereken beş dosya var ve betikler ÇALIŞTIRILABİLİR.

    İzin biti bir ayrıntı değil: `kod_tazelik.sh` A1'e rsync ile gider ve orada `script:`/`bash`
    ile koşar; `dogrulama_anahtar.py` `python3 <yol>` ile çağrılır. Eksik `+x`, kapıyı bakım
    penceresinin ortasında düşürür."""
    eksik = [str(p) for p in (VARS_YML, STATE_FARK, ARTEFAKT, DOGRULAMA, KOD_TAZELIK)
             if not p.is_file()]
    assert not eksik, f"Task 1 dosyaları eksik: {eksik}"
    assert os.access(KOD_TAZELIK, os.X_OK), f"{KOD_TAZELIK} çalıştırılabilir değil (chmod +x)"


# =================================================================================================
# A1 — `rsync_disla` == dagit.sh `RSYNC_EXC`
# =================================================================================================
def _dagit_rsync_exc() -> list[str]:
    """`RSYNC_EXC=( … )` dizisinin `--exclude '…'` öğeleri (dizi gövdesinden, yorumdan DEĞİL)."""
    metin = _dagit_metin()
    m = re.search(r"^RSYNC_EXC=\((.*?)\)", metin, re.M | re.S)
    assert m, "dagit.sh'ta `RSYNC_EXC=(` bulunamadı — çivi bayatlamış"
    return re.findall(r"--exclude '([^']*)'", m.group(1))


def test_A1_rsync_disla_dagit_ile_AYNI_KUME():
    """TEK KAYNAK KÖPRÜSÜ: vars listesi ile dagit.sh listesi KÜME olarak eşit (sıra bağımsız).

    Yön İKİ TARAFLI ölçülür. Yalnız "vars ⊆ dagit" ölçseydik vars'a fazladan bir dışlama
    (canlıda okuyucusu olan bir dizin) sessizce girebilir ve playbook onu dağıtımdan
    düşürürdü — `/ui` ile `meridian/web/pano*` arasındaki fark tam olarak budur. Yalnız
    "dagit ⊆ vars" ölçseydik dagit'e eklenen yeni bir sınıf (2026-08-24 `scratch-*`)
    playbook'ta AÇIK kalırdı."""
    dagit_kume = set(_dagit_rsync_exc())
    vars_liste = _vars()["rsync_disla"]
    assert isinstance(vars_liste, list), "`rsync_disla` liste değil"
    vars_kume = set(vars_liste)
    assert len(vars_liste) == len(vars_kume), \
        f"`rsync_disla` yinelenen öğe taşıyor: {sorted(x for x in vars_liste if vars_liste.count(x) > 1)}"
    assert vars_kume == dagit_kume, (
        "rsync dışlama listesi AYRIŞTI — playbook ile dagit.sh farklı şeyi dağıtır.\n"
        f"  yalnız dagit.sh'ta: {sorted(dagit_kume - vars_kume)}\n"
        f"  yalnız vars'ta    : {sorted(vars_kume - dagit_kume)}")


def test_A1b_rsync_disla_SINIF_KURUCULARI_hala_listede():
    """TABAN (tavan değil): vaka doğurmuş dışlamalar listeden hiç düşmemeli.

    Her biri ölçülmüş bir canlı olaydır — `.dash.env` (2026-08-01 sır silinmesi), `scratch-*`
    (2026-08-24 scratch-panov2 canlıya gidiyordu), `/var` (2026-08-29 bot kum havuzu
    `--delete` ile silinirdi), `/ui` (derlenmemiş kaynak). Küme eşitliği ikisini AYNI ANDA
    düşürmeye karşı kör: bu çivi tabanı ayrıca tutar."""
    vars_kume = set(_vars()["rsync_disla"])
    for kurucu in (".dash.env", ".env", "state", "backups", "/var", "scratch-*", "scratchpad",
                   "/ui", ".git", ".venv"):
        assert kurucu in vars_kume, f"`rsync_disla`da sınıf kurucusu eksik: {kurucu!r}"


# =================================================================================================
# A2 — `f9_ciftleri` == dagit.sh `F9_LISTE`
# =================================================================================================
def _dagit_f9() -> list[tuple[str, str]]:
    govde = _dagit_metin().split('F9_LISTE="', 1)[1].split('"', 1)[0]
    return [(ln.split("|", 1)[0].strip(), ln.split("|", 1)[1].strip())
            for ln in govde.strip().splitlines() if "|" in ln]


def test_A2_f9_ciftleri_dagit_ile_AYNI_KUME():
    """[F9] çiftleri (repo yolu → canlı yol) iki kaynakta BİREBİR aynı.

    Çift olarak ölçülür, yalnız repo yolu olarak değil: canlı hedefi yanlış yazılmış bir çift
    kapıyı "canlıda DOSYA YOK" dalına düşürür ve sürüklenme her dağıtımda ölçülemedi
    gürültüsüne dönüşür — kapının sessizleşmesinin en sessiz biçimi."""
    dagit_kume = set(_dagit_f9())
    ham = _vars()["f9_ciftleri"]
    assert isinstance(ham, list) and ham, "`f9_ciftleri` liste değil ya da boş"
    vars_ciftler = [(c["repo"], c["canli"]) for c in ham]
    vars_kume = set(vars_ciftler)
    assert len(vars_ciftler) == len(vars_kume), "`f9_ciftleri` yinelenen çift taşıyor"
    assert vars_kume == dagit_kume, (
        "[F9] listesi AYRIŞTI — playbook ile dagit.sh farklı artefakt kümesini izler.\n"
        f"  yalnız dagit.sh'ta: {sorted(dagit_kume - vars_kume)}\n"
        f"  yalnız vars'ta    : {sorted(vars_kume - dagit_kume)}")


def test_A2b_f9_repo_taraflari_GERCEKTEN_VAR():
    """Listeye uydurma bir yol girmesin: repo tarafı yoksa kapı kendi "REPODA YOK" dalına düşer
    ve her dağıtımda ölçülemedi basar (v266'nın kurucu çivisiyle aynı gerekçe)."""
    yok = [c["repo"] for c in _vars()["f9_ciftleri"] if not (REPO / c["repo"]).is_file()]
    assert not yok, f"`f9_ciftleri` repo tarafı diskte yok: {yok}"


def test_A2c_f9_canli_yollari_MUTLAK():
    """Canlı yol MUTLAK olmalı — göreli bir yol `slurp`/`cat` çağrısında A1'in o anki cwd'sine
    göre çözülür ve kapı yanlış dosyayı kıyaslar (sessiz yanlış hüküm)."""
    goreli = [c["canli"] for c in _vars()["f9_ciftleri"] if not c["canli"].startswith("/")]
    assert not goreli, f"`f9_ciftleri` canlı yolu mutlak değil: {goreli}"


# =================================================================================================
# A3 — `dogrulama_uclari` == dagit.sh `DOGRULAMA_UCLARI`
# =================================================================================================
def _dagit_dogrulama_uclari() -> list[tuple[str, str, str]]:
    govde = _dagit_metin().split('DOGRULAMA_UCLARI="', 1)[1].split('"', 1)[0]
    cikti = []
    for ln in govde.strip().splitlines():
        if not ln.strip():
            continue
        parca = ln.split("|")
        assert len(parca) == 3, f"DOGRULAMA_UCLARI satırı üç alanlı değil: {ln!r}"
        cikti.append((parca[0].strip(), parca[1].strip(), parca[2].strip()))
    return cikti


def test_A3_dogrulama_uclari_dagit_ile_AYNI():
    """[5a] üç ucu (yol|anahtar|tip) iki kaynakta aynı — ve SIRA da aynı.

    Sıra burada bilgi taşır: uçlar alarm/öğrenme/performans üçlüsü olarak BİLEREK seçildi
    (D2, 2026-09-05) ve çıktı bu sırayla okunur. Küme eşitliği yerine liste eşitliği, sıranın
    sessizce dönmesini de kırmızı yapar."""
    dagit_liste = _dagit_dogrulama_uclari()
    ham = _vars()["dogrulama_uclari"]
    assert isinstance(ham, list) and ham, "`dogrulama_uclari` liste değil ya da boş"
    vars_liste = [(u["yol"], u["anahtar"], u.get("tip") or "") for u in ham]
    assert vars_liste == dagit_liste, (
        "[5a] doğrulama uçları AYRIŞTI.\n"
        f"  dagit.sh: {dagit_liste}\n"
        f"  vars    : {vars_liste}")


def test_A3b_birim_adaylari_dagit_ile_AYNI():
    """`birim_adaylari` üçlüsü dagit.sh'ın `_BIRIM_ADAYLARI`sıyla aynı.

    Aday KÜMESİ 2026-08-24'te bir UNUTMA vakasıyla büyüdü (`meridian-learn` birim doğdu, dagit'te
    adı hiç geçmiyordu; süreç 11 sa 19 dk eski bytecode koştu). İki kaynağa çıkan bir listede
    aynı unutma bir kez daha mümkün — bu çivi onu kırmızı yapar."""
    m = re.search(r'^_BIRIM_ADAYLARI="([^"]*)"', _dagit_metin(), re.M)
    assert m, "dagit.sh'ta `_BIRIM_ADAYLARI` bulunamadı — çivi bayatlamış"
    assert _vars()["birim_adaylari"] == m.group(1).split(), (
        f"birim adayları ayrıştı: vars={_vars()['birim_adaylari']} dagit={m.group(1).split()}")


# =================================================================================================
# A4a — ops/state_fark_hukmu.py: [1b] hükmü DOSYADAN koşar
# =================================================================================================
def _hukum(canli: str, repo: str, tmp_path) -> tuple[str, str]:
    """Betiği operatörün/playbook'un koşacağı BİÇİMDE koştur; (HUKUM=…, insan metni) döndür."""
    a, b = tmp_path / "canli.yaml", tmp_path / "repo.yaml"
    a.write_text(canli, encoding="utf-8")
    b.write_text(repo, encoding="utf-8")
    r = subprocess.run([sys.executable, str(STATE_FARK), str(a), str(b)],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"state_fark_hukmu.py patladı (rc={r.returncode}):\n{r.stderr}"
    satirlar = r.stdout.splitlines()
    hukum = [s for s in satirlar if s.startswith("HUKUM=")]
    assert hukum, f"HUKUM satırı basılmadı — çağıran onu grep'liyor:\n{r.stdout}"
    return hukum[-1], "\n".join(s for s in satirlar if not s.startswith("HUKUM="))


def test_A4a1_hukum_repoda_YENI_anahtar_KOPYALA(tmp_path):
    """ASIL VAKA (`entry.w_turnover`, 2026-08-02): repo ilerledi, canlı hiç görmedi → kopyalanır."""
    h, metin = _hukum("a: 1\n", "a: 1\nentry.w_turnover: {min: 0.0, max: 0.4}\n", tmp_path)
    assert h == "HUKUM=KOPYALA", f"repo ilerlemesi kopyalanmıyor: {h} / {metin}"
    assert "repoda YENİ" in metin and "w_turnover" in metin, \
        f"canlının hiç görmediği düğme adıyla söylenmiyor: {metin!r}"


def test_A4a2_hukum_CANLIDA_repo_disi_anahtar_ENGEL(tmp_path):
    """Canlı elle değişikliği SESSİZCE EZİLMEZ — hüküm operatörün."""
    h, metin = _hukum("a: 1\nelle_eklenen_dugme: 3\n", "a: 1\n", tmp_path)
    assert h == "HUKUM=ENGEL", f"canlı elle değişikliği ezilecekti: {h}"
    assert "REPO-DIŞI" in metin and "elle_eklenen_dugme" in metin, \
        f"engelin SEBEBİ adıyla söylenmiyor: {metin!r}"


def test_A4a3_hukum_YALNIZ_YORUM_farki_KOPYALA(tmp_path):
    """POZİTİF KONTROL: ayrım anahtar düzeyinde — satır bazlı bir kapı hiç kopyalamazdı."""
    h, metin = _hukum("# eski yorum\na: 1\n", "# YENİDEN YAZILMIŞ yorum\na: 1\n", tmp_path)
    assert h == "HUKUM=KOPYALA", f"yalnız yorum farkı ENGEL sayıldı: {h}"
    assert "fark YOK" in metin, f"ayrımın yalnız yorumda olduğu söylenmiyor: {metin!r}"


def test_A4a4_hukum_ic_ice_blok_DEGER_farkini_gorur(tmp_path):
    """goal.yaml iç içedir — düzleştirme olmasa blok içi değer değişikliği 'fark yok' görünürdü."""
    h, metin = _hukum("execution_v2:\n  limit_pct_cap: 0.01\n",
                      "execution_v2:\n  limit_pct_cap: 0.02\n", tmp_path)
    assert h == "HUKUM=KOPYALA"
    assert "execution_v2.limit_pct_cap" in metin, f"iç içe yol görünmüyor: {metin!r}"


def test_A4a5_hukum_BOZUK_yaml_FAIL_CLOSED(tmp_path):
    """Ayrıştırılamayan dosya 'fark yok' DEĞİLDİR — hüküm VERİLEMEDİ, o yüzden ENGEL."""
    h, metin = _hukum("a: [1,\n", "a: 1\n", tmp_path)
    assert h == "HUKUM=ENGEL", f"ayrıştırılamayan dosya sessizce kopyalanacaktı: {h}"
    assert "okunamadı" in metin, f"ayrıştırma hatası beyan edilmiyor: {metin!r}"


# =================================================================================================
# A4b — ops/artefakt_tazelik.py: [5c] kapısı DOSYADAN koşar
# =================================================================================================
def _tazelik_sahne(tmp_path, art_yasi: int | None, kaynak_yasi: int = 1000):
    """`--repo` verilecek sahte kök: `ui/` kaynağı + (istenirse) `meridian/web/pano.html`."""
    kok = tmp_path / "kok"
    (kok / "ui" / "src").mkdir(parents=True)
    (kok / "meridian" / "web").mkdir(parents=True)
    kaynak = kok / "ui" / "src" / "app.tsx"
    kaynak.write_text("export const x = 1\n", encoding="utf-8")
    os.utime(kaynak, (1_700_000_000 - kaynak_yasi, 1_700_000_000 - kaynak_yasi))
    if art_yasi is not None:
        art = kok / "meridian" / "web" / "pano.html"
        art.write_text("<html></html>\n", encoding="utf-8")
        os.utime(art, (1_700_000_000 - art_yasi, 1_700_000_000 - art_yasi))
    return kok


def _tazelik_kos(kok) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ARTEFAKT), "--repo", str(kok)],
                          capture_output=True, text=True, timeout=60)


def test_A4b1_artefakt_TAZE_cikis_0(tmp_path):
    """Artefakt kaynaktan YENİ → 0 (dağıtım sürer)."""
    r = _tazelik_kos(_tazelik_sahne(tmp_path, art_yasi=10, kaynak_yasi=1000))
    assert r.returncode == 0, f"taze artefakt bayat sayıldı:\n{r.stdout}{r.stderr}"
    assert "TAMAM" in r.stdout, f"taze hükmü beyan edilmiyor: {r.stdout!r}"


def test_A4b2_artefakt_BAYAT_cikis_1(tmp_path):
    """Artefakt kaynaktan ESKİ → 1. ASIL SINIF: kaynak değişti, `npm run build` koşmadı; [5b]
    bunu göremez (o Python mtime'ına bakar) ve doğrulama 'active' der."""
    r = _tazelik_kos(_tazelik_sahne(tmp_path, art_yasi=1000, kaynak_yasi=10))
    assert r.returncode == 1, f"bayat artefakt geçti (rc={r.returncode}):\n{r.stdout}{r.stderr}"
    assert "IHLAL" in r.stdout, f"bayat hükmü beyan edilmiyor: {r.stdout!r}"
    assert "npm run build" in r.stdout, "onarım reçetesi basılmıyor — operatör ne yapacağını bilemez"


def test_A4b3_artefakt_YOK_olculemedi_cikis_2(tmp_path):
    """Artefakt henüz derlenmemişse hüküm ÖLÇÜLEMEDİ'dir (2), 'taze' (0) DEĞİL.

    UYDURMA YASAĞI: ölçülemeyen değer `None` + neden. Çıkış kodu ayrımı çağıranın kararını
    taşır — dagit.sh bugün 2'de dağıtımı SÜRDÜRÜR (mevcut davranış), ama 'TAMAM' da DEMEZ."""
    r = _tazelik_kos(_tazelik_sahne(tmp_path, art_yasi=None))
    assert r.returncode == 2, f"artefakt yokken 'ölçülemedi' denmedi (rc={r.returncode}):\n{r.stdout}"
    assert "ATLANDI" in r.stdout or "ÖLÇÜLEMEDİ" in r.stdout.upper(), \
        f"ölçülemedi nedeni beyan edilmiyor: {r.stdout!r}"


def test_A4b4_artefakt_UI_YOKSA_olculemedi(tmp_path):
    """`ui/` hiç yoksa kapının ölçecek zemini yok → 2 (ölçülemedi), 0 DEĞİL."""
    kok = tmp_path / "kok"
    (kok / "meridian" / "web").mkdir(parents=True)
    (kok / "meridian" / "web" / "pano.html").write_text("x", encoding="utf-8")
    r = _tazelik_kos(kok)
    assert r.returncode == 2, f"ui/ yokken 'ölçülemedi' denmedi (rc={r.returncode}):\n{r.stdout}"


def test_A4b5_artefakt_AYNI_SANIYE_kesir_farki_TAMAM(tmp_path):
    """KIYAS TAM SANİYEDEDİR (davranış birebir kuralı, inceleme bulgusu 2026-09-08).

    Sahne: artefakt ile kaynak AYNI saniyede, kaynak 0,6 s daha yeni. Eski kabuk gövdesi
    `stat -f %m` / `stat -c %Y` / `find -printf '%T@' | cut -d. -f1` ile TAM SANİYE okuyordu →
    `TAMAM`/0. Kesirli kıyas aynı girdide `IHLAL`/1 verir ve dağıtımı DURDURUR — beyan dışı bir
    sapma. Sınıf gerçek: `git checkout <sha>` (dagit.sh'ın kendi geri-alma reçetesi) bütün
    ağacı aynı saniyenin içine yazar; hangi dosyanın kesri büyükse hüküm o yöne kayardı."""
    kok = tmp_path / "kok"
    (kok / "ui" / "src").mkdir(parents=True)
    (kok / "meridian" / "web").mkdir(parents=True)
    art = kok / "meridian" / "web" / "pano.html"
    art.write_text("<html></html>\n", encoding="utf-8")
    kaynak = kok / "ui" / "src" / "app.tsx"
    kaynak.write_text("export const x = 1\n", encoding="utf-8")
    os.utime(art, (1_700_000_000.2, 1_700_000_000.2))
    os.utime(kaynak, (1_700_000_000.8, 1_700_000_000.8))
    # SAHNE DOĞRULAMASI: dosya sistemi kesri yutarsa çivi YANLIŞ SEBEPLE yeşil kalırdı.
    assert int(kaynak.stat().st_mtime) == int(art.stat().st_mtime), "sahne aynı saniyede değil"
    assert kaynak.stat().st_mtime > art.stat().st_mtime, \
        "dosya sistemi kesirli mtime taşımıyor — bu çivi mutasyonu ısıramaz, sahne geçersiz"
    r = _tazelik_kos(kok)
    assert r.returncode == 0, \
        f"aynı saniyedeki kesir farkı dağıtımı DURDURDU (rc={r.returncode}):\n{r.stdout}"
    assert "TAMAM" in r.stdout, f"taze hükmü beyan edilmiyor: {r.stdout!r}"


def test_A4b6_artefakt_NODE_MODULES_kaynak_SAYILMAZ(tmp_path):
    """`ui/node_modules/**` KAYNAK DEĞİLDİR — `npm install` her koşumda oraya taze dosya yazar.

    TAŞIYICI SATIR, SIFIR ÇİVİ (inceleme bulgusu 2026-09-08): dışlama düşerse (ya da `rglob`
    süzgeci değişirse) artefakt GERÇEKTEN tazeyken `IHLAL` basılır ve HER dağıtım [5c]'de durur;
    operatör basılan reçeteyi (`npm run build`) koşar, ihlal GİTMEZ, aynı duvara çarpar."""
    kok = _tazelik_sahne(tmp_path, art_yasi=10, kaynak_yasi=1000)
    paket = kok / "ui" / "node_modules" / "pkg"
    paket.mkdir(parents=True)
    p = paket / "p.json"
    p.write_text("{}\n", encoding="utf-8")
    os.utime(p, (1_700_000_000, 1_700_000_000))       # artefakttan (10 sn eski) DAHA YENİ
    r = _tazelik_kos(kok)
    assert r.returncode == 0, (
        f"node_modules kaynak sayıldı → taze artefakt BAYAT ilan edildi (rc={r.returncode}):\n"
        f"{r.stdout}")
    assert "TAMAM" in r.stdout, f"taze hükmü beyan edilmiyor: {r.stdout!r}"


def test_A4b7_artefakt_UI_KAYNAKSIZSA_olculemedi(tmp_path):
    """`ui/` var ama KAYNAK UZANTILI dosya hiç yok → kıyas zemini yok: 2, 0 DEĞİL.

    Beyanlı dürüstleşme (dosya başlığında yazılı): eski kabuk gövdesi bu hâlde "TAMAM artefakt
    kaynağından taze" basıyordu — ölçülemeyeni taze saymak, uydurma yasağının tam karşıtı.
    `node_modules`ın tek başına kaldığı ağaç da bu daldan geçer (A4b6'nın negatifi)."""
    kok = tmp_path / "kok"
    (kok / "ui" / "node_modules" / "pkg").mkdir(parents=True)
    (kok / "ui" / "node_modules" / "pkg" / "p.json").write_text("{}\n", encoding="utf-8")
    (kok / "ui" / "README.md").write_text("belge\n", encoding="utf-8")
    (kok / "meridian" / "web").mkdir(parents=True)
    (kok / "meridian" / "web" / "pano.html").write_text("x", encoding="utf-8")
    r = _tazelik_kos(kok)
    assert r.returncode == 2, \
        f"kaynaksız ui/ 'ölçülemedi' demedi (rc={r.returncode}):\n{r.stdout}"
    assert "ÖLÇÜLEMEDİ" in r.stdout, f"ölçülemedi nedeni beyan edilmiyor: {r.stdout!r}"


# =================================================================================================
# A4c — deploy/oracle-a1/dogrulama_anahtar.py: [5a] kapısı DOSYADAN koşar
# =================================================================================================
class _SahteUc(http.server.BaseHTTPRequestHandler):
    """Uçları taklit eder: token başlığı YOKSA yetkisiz gövde, VARSA yollara göre JSON."""

    GOVDELER: dict[str, dict] = {}
    #: Doluysa HER istek 302 ile bu adrese yönlendirilir (A4c6: yönlendirme izlenmemeli).
    YONLENDIR: str | None = None

    def do_GET(self):                                              # noqa: N802 (http.server API)
        if self.YONLENDIR:
            self.send_response(302)
            self.send_header("Location", self.YONLENDIR)
            self.end_headers()
            return
        if self.headers.get("x-meridian-token") != "SIR":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"detail": "yetkisiz"}).encode())
            return
        govde = self.GOVDELER.get(self.path)
        if govde is None:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"detail": "yok"}')
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(govde).encode())

    def log_message(self, *_a):                                    # noqa: D102 (test gürültüsü)
        return


@pytest.fixture
def sahte_sunucu():
    # SINIF DURUMU HER ÇİVİDE SIFIRLANIR: `GOVDELER`/`YONLENDIR` sınıf nitelikleridir ve
    # sızarlarsa bir çivi ötekinin sahnesini miras alır (yanlış sebeple yeşil/kırmızı).
    _SahteUc.GOVDELER, _SahteUc.YONLENDIR = {}, None
    sunucu = http.server.HTTPServer(("127.0.0.1", 0), _SahteUc)
    is_parcacigi = threading.Thread(target=sunucu.serve_forever, daemon=True)
    is_parcacigi.start()
    yield sunucu
    sunucu.shutdown()
    sunucu.server_close()
    _SahteUc.GOVDELER, _SahteUc.YONLENDIR = {}, None


def _dogrulama_kos(tmp_path, sunucu, token: str | None, uclar: list[str]):
    env_dosya = tmp_path / "dash.env"
    if token is not None:
        env_dosya.write_text(f'MERIDIAN_DASH_TOKEN="{token}"\n', encoding="utf-8")
    arg = [sys.executable, str(DOGRULAMA), "--env-dosya", str(env_dosya),
           "--taban", f"http://127.0.0.1:{sunucu.server_port}"]
    for u in uclar:
        arg += ["--uc", u]
    return subprocess.run(arg, capture_output=True, text=True, timeout=120)


def test_A4c1_dogrulama_VAR_cikis_0(tmp_path, sahte_sunucu):
    """Anahtar VAR + tip doğru → her uç `VAR|…`, çıkış 0."""
    _SahteUc.GOVDELER = {"/api/alerts": {"pending": 3},
                         "/api/hermes": {"learning": {"hayalet_suzulen_n": 7}}}
    r = _dogrulama_kos(tmp_path, sahte_sunucu, "SIR",
                       ["/api/alerts|pending|int", "/api/hermes|learning.hayalet_suzulen_n|"])
    assert r.returncode == 0, f"sağlam gövde YOK sayıldı:\n{r.stdout}{r.stderr}"
    assert r.stdout.count("VAR|") == 2, f"iki uç da VAR basmadı: {r.stdout!r}"
    assert "YOK|" not in r.stdout


def test_A4c2_dogrulama_YETKISIZ_govde_YOK_cikis_1(tmp_path, sahte_sunucu):
    """ASIL VAKA (dağıtım #13, 2026-09-04): token'sız istek 200 döner, gövdesi `{"detail": …}`.
    "200 döndü" ≠ "doğru gövde döndü" — anahtar yoksa kapı DÜŞER (beyan yazılmaz)."""
    _SahteUc.GOVDELER = {"/api/alerts": {"pending": 3}}
    r = _dogrulama_kos(tmp_path, sahte_sunucu, "YANLIS-TOKEN", ["/api/alerts|pending|int"])
    assert r.returncode == 1, f"yetkisiz gövde geçti (rc={r.returncode}):\n{r.stdout}"
    assert "YOK|/api/alerts|pending" in r.stdout, f"YOK satırı uç/anahtar taşımıyor: {r.stdout!r}"


def test_A4c3_dogrulama_TIP_yanlissa_YOK(tmp_path, sahte_sunucu):
    """`tip=int` verilmişse anahtarın VARLIĞI yetmez — `pending: null` (sahte "boş") YOK'tur.
    Tip zorlanmayan uçta ise `None` MEŞRU değerdir (`tohum_siniri` ölçülü istisnası)."""
    _SahteUc.GOVDELER = {"/api/alerts": {"pending": None},
                         "/api/performance": {"equity_curve_beyani": {"tohum_siniri": None}}}
    r_int = _dogrulama_kos(tmp_path, sahte_sunucu, "SIR", ["/api/alerts|pending|int"])
    assert r_int.returncode == 1, f"tip ihlali geçti:\n{r_int.stdout}"
    r_tipsiz = _dogrulama_kos(tmp_path, sahte_sunucu, "SIR",
                              ["/api/performance|equity_curve_beyani.tohum_siniri|"])
    assert r_tipsiz.returncode == 0, f"tipsiz uçta None reddedildi:\n{r_tipsiz.stdout}"


def test_A4c4_dogrulama_TOKEN_YOKSA_fail_open(tmp_path, sahte_sunucu):
    """FAIL-OPEN, BEYANLI: token dosyası okunamazsa ölçüm YOKTUR, "ihlal" DEĞİLDİR — dağıtım
    durmaz. Jeton dizgesi tam olarak `OLCULEMEDI token yok`: çağıran onu eşitlikle karşılaştırır."""
    _SahteUc.GOVDELER = {"/api/alerts": {"pending": 3}}
    r = _dogrulama_kos(tmp_path, sahte_sunucu, None, ["/api/alerts|pending|int"])
    assert r.returncode == 0, f"token yokken dağıtım düştü (fail-open bozuldu): {r.stdout}"
    assert r.stdout.strip() == "OLCULEMEDI token yok", f"jeton dizgesi değişti: {r.stdout!r}"


def test_A4c5_dogrulama_TOKEN_DEGERI_ciktida_GECMEZ(tmp_path, sahte_sunucu):
    """SIR SÜZGECİ: dagit çıktısı günlüğe kopyalanır — token DEĞERİ hiçbir satıra girmez.
    Yalnız VAR/YOK hükmü döner (uç gövdeleri de dışarı sızmaz)."""
    _SahteUc.GOVDELER = {"/api/alerts": {"pending": 3, "gizli_alan": "SIR-GOVDE"}}
    r = _dogrulama_kos(tmp_path, sahte_sunucu, "SIR", ["/api/alerts|pending|int"])
    assert "SIR" not in r.stdout and "SIR" not in r.stderr, \
        f"token değeri çıktıya sızdı: {r.stdout!r} / {r.stderr!r}"
    assert "SIR-GOVDE" not in r.stdout, "uç gövdesi çıktıya sızdı"


def test_A4c6_dogrulama_YONLENDIRME_izlenmez_FAIL_CLOSED(tmp_path, sahte_sunucu):
    """SIR SIZINTISI SINIFI (inceleme bulgusu 2026-09-08): `curl -s` yönlendirmeyi İZLEMİYORDU
    (`-L` yok), urllib'in VARSAYILAN opener'ı izler — ve `x-meridian-token`ı yönlendirmenin
    HEDEFİNE taşır. `Location`da hangi host yazılıysa pano token'ı oraya gider; "kontrol tamamen
    A1'in içinde koşuyor" güvencesi orada biter.

    HÜKÜM: 3xx bir ÖLÇÜM DEĞİLDİR. Kapı fail-closed düşer (`OLCULEMEDI yonlendirme <kod>`, 1) —
    eski `curl` davranışı boş gövde + "YOK" idi, yani o da dağıtımı durduruyordu; değişen tek
    şey operatörün okuduğu cümledir (beyanlı sapma, betiğin başlığında yazılı)."""
    gelen: list[str] = []

    class _Hedef(http.server.BaseHTTPRequestHandler):
        """Yönlendirmenin HEDEFİ: hiçbir istek görmemeli (token buraya taşınmamalı)."""

        def do_GET(self):                                          # noqa: N802 (http.server API)
            gelen.append(self.headers.get("x-meridian-token") or "")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"pending": 3}')

        def log_message(self, *_a):                                # noqa: D102 (test gürültüsü)
            return

    hedef = http.server.HTTPServer(("127.0.0.1", 0), _Hedef)
    threading.Thread(target=hedef.serve_forever, daemon=True).start()
    try:
        _SahteUc.YONLENDIR = f"http://127.0.0.1:{hedef.server_port}/api/alerts"
        r = _dogrulama_kos(tmp_path, sahte_sunucu, "SIR", ["/api/alerts|pending|int"])
    finally:
        hedef.shutdown()
        hedef.server_close()
    assert not gelen, (
        f"yönlendirme İZLENDİ — pano token'ı {len(gelen)} kez yönlendirme hedefine taşındı "
        "(sır sızıntısı)")
    assert r.returncode == 1, f"yönlendirme 'ölçüldü' sayıldı (rc={r.returncode}):\n{r.stdout}"
    assert "OLCULEMEDI yonlendirme 302" in r.stdout, \
        f"yönlendirme hükmü beyan edilmiyor: {r.stdout!r}"
    assert "SIR" not in r.stdout and "SIR" not in r.stderr, \
        f"token değeri çıktıya sızdı: {r.stdout!r} / {r.stderr!r}"


# =================================================================================================
# A4d — deploy/oracle-a1/kod_tazelik.sh: [5b] kapısı DOSYADAN koşar
# =================================================================================================
#: Sahnenin taklit ettiği iki platform. `"gnu"` A1'in (Ubuntu) yoludur — kapının GERÇEKTEN
#: koştuğu TEK makine; `"bsd"` bu geliştirici makinesinin yoludur. İkisi de ölçülür: tur-1'de
#: yalnız BSD dalı sınanmıştı ve GNU dalında kapı sessizce "temiz" diyordu — mutasyon ölçümü de
#: aynı körlüğün içinden geçti ("13/13 ısırdı" hepsi BSD dalındaydı, inceleme 2026-09-08).
PLATFORMLAR = ("bsd", "gnu")

#: GNU `find` şimi: `-printf` GNU'ya özgüdür, macOS find onu "unknown primary" ile REDDEDER.
_GNU_FIND_SIM = '''#!/usr/bin/env python3
"""GNU `find` şimi — yalnız v452 A4d "gnu" sahnesi.

`-printf` görürse GNU çıktısını üretir (kesirli epoch + yol, `sort -rn` ile sıralanabilir);
başka her çağrıyı gerçek find'e devreder."""
import pathlib
import subprocess
import sys

argv = sys.argv[1:]
if "-printf" in argv:
    for p in sorted(pathlib.Path(argv[0]).rglob("*.py")):
        print(f"{p.stat().st_mtime:.7f} {p}")
    sys.exit(0)
sys.exit(subprocess.run(["/usr/bin/find", *argv]).returncode)
'''

#: BSD `find` şimi: `-printf`i macOS gibi REDDEDER. A4d6'da GNU `stat` şimiyle birlikte
#: kullanılır — GNU dalı boş döner, BSD dalı SAYI OLMAYAN bir şey döndürür.
_BSD_FIND_SIM = '''#!/usr/bin/env python3
"""BSD `find` şimi — `-printf`i macOS gibi reddeder (rc 1, boş stdout)."""
import subprocess
import sys

argv = sys.argv[1:]
if "-printf" in argv:
    print("find: -printf: unknown primary or operator", file=sys.stderr)
    sys.exit(1)
sys.exit(subprocess.run(["/usr/bin/find", *argv]).returncode)
'''

#: GNU `stat` şimi — bulgunun ta kendisi: GNU'da `-f` FORMAT DEĞİL `--file-system`tir.
_GNU_STAT_SIM = '''#!/usr/bin/env python3
"""GNU `stat` şimi — yalnız v452 A4d "gnu" sahnesi.

ÖLÇÜLEN BULGU (2026-09-08): `stat -f '%m %N' <dosya>` GNU'da BAŞARISIZ OLMAZ. Format dizgesi bir
OPERAND sayılıp stderr'e hata düşer (dagit'in sondasında `2>/dev/null` yutar), gerçek dosya için
ise dosya-sistemi raporu STDOUT'a basılır. Yani BSD sondası GNU'da BOŞ DÖNMEZ: `[ -z ... ]`
yedeği hiç çalışmaz ve `_YENI` bir sayı değil `Inodes:` olur.

`-f` DIŞINDAKİ her çağrı GÜRÜLTÜLÜ düşer (rc 1 + stderr): betik yarın `stat -c` çağırmaya
başlarsa sahne sessizce "geçti" dememeli — şimlenmemiş bir yol, ölçülmemiş bir yoldur."""
import sys

argv = sys.argv[1:]
if "-f" in argv:
    print('  File: "/"')
    print("Inodes: Total: 442313334  Free: 440716360")
    sys.exit(0)
print(f"stat şimi yalnız -f taklit eder, gelen: {argv}", file=sys.stderr)
sys.exit(1)
'''


def _kod_tazelik_sahne(tmp_path, birimler: list[dict], kaynak_mtime: int = 1_700_000_000,
                       platform: str = "bsd"):
    """Sahte `/opt/meridian` kökü + PATH'e `systemctl`/`date` (+ platforma göre `find`/`stat`) şimleri.

    ŞİM GEREKÇESİ (dürüst beyan): `systemctl` bu makinede YOK ve `date -u -d` GNU'ya özgüdür
    (macOS'ta `-d` desteklenmez) — şimsiz koşumda betik HER dalda "OLCULEMEDI" verirdi ve
    IHLAL/BEKLENEN ayrımı hiç ölçülmezdi. Şimlenen şey ORTAM; betiğin KENDİ mantığı
    (mtime kıyası + kum-havuzu ayrımı + ExecStart süzgeci) gerçekten koşar.

    PLATFORM (düzeltme turu 2): ortamın YARISINI hedef platforma çevirip (date → GNU) öteki
    yarısını geliştirici makinesinde (stat/find → BSD) bırakmak, kapının koştuğu tek makineyi
    hiç ölçmemekti. `"gnu"` sahnesi `find`/`stat`ı da A1'in semantiğine çevirir."""
    kok = tmp_path / "opt" / "meridian"
    (kok / "meridian").mkdir(parents=True)
    py = kok / "meridian" / "loop.py"
    py.write_text("x = 1\n", encoding="utf-8")
    os.utime(py, (kaynak_mtime, kaynak_mtime))

    bin_dizin = tmp_path / "bin"
    bin_dizin.mkdir()
    veri = tmp_path / "birimler.txt"
    # `%KOK%` yer tutucusu: ExecStart süzgeci KURULUM KÖKÜNÜ arar (canlıda `/opt/meridian`),
    # sahnede o kök tmp altındadır — literal bir `/opt/meridian` yazsaydık süzgeç hiç eşleşmez ve
    # çivi "kapsam dışı" diye YANLIŞ SEBEPLE yeşil kalırdı.
    veri.write_text("".join(
        f"{b['ad']}\t{b['execstart'].replace('%KOK%', str(kok))}\t{b['baslangic']}"
        f"\t{b.get('aciklama', 'Meridian')}\n"
        for b in birimler), encoding="utf-8")

    (bin_dizin / "systemctl").write_text(f"""#!/usr/bin/env bash
VERI="{veri}"
case "$1" in
  list-units) cut -f1 "$VERI" | sed 's/$/ loaded active running -/' ;;
  show)
    _u="$2"; _p="$4"
    while IFS=$'\\t' read -r ad es bas ack; do
      [ "$ad" = "$_u" ] || continue
      case "$_p" in
        ExecStart) echo "$es" ;;
        ExecMainStartTimestamp) echo "$bas" ;;
        Description) echo "$ack" ;;
      esac
    done < "$VERI" ;;
esac
""", encoding="utf-8")
    (bin_dizin / "date").write_text("""#!/usr/bin/env bash
# `date -u -d "<epoch-olarak-yazilmis-damga>" +%s` → damganin kendisi (GNU -d şimi).
if [ "$2" = "-d" ]; then echo "$3"; else /bin/date "$@"; fi
""", encoding="utf-8")
    for f in ("systemctl", "date"):
        (bin_dizin / f).chmod(0o755)

    if platform == "gnu":
        (bin_dizin / "find").write_text(_GNU_FIND_SIM, encoding="utf-8")
        (bin_dizin / "stat").write_text(_GNU_STAT_SIM, encoding="utf-8")
        for f in ("find", "stat"):
            (bin_dizin / f).chmod(0o755)
    elif platform != "bsd":
        raise AssertionError(f"bilinmeyen platform: {platform!r} (beklenen: {PLATFORMLAR})")
    return kok, bin_dizin


def _kod_tazelik_kos(kok, bin_dizin):
    ortam = dict(os.environ)
    ortam["PATH"] = f"{bin_dizin}:{ortam['PATH']}"
    return subprocess.run(["bash", str(KOD_TAZELIK), str(kok)],
                          capture_output=True, text=True, timeout=120, env=ortam)


@pytest.mark.parametrize("platform", PLATFORMLAR)
def test_A4d1_kod_tazelik_TEMIZ_cikis_0(tmp_path, platform):
    """Süreç kaynaktan YENİ → hiçbir satır, çıkış 0."""
    kok, b = _kod_tazelik_sahne(tmp_path, [
        {"ad": "meridian.service", "execstart": "%KOK%/.venv/bin/python -m meridian",
         "baslangic": "1700000500"}], platform=platform)
    r = _kod_tazelik_kos(kok, b)
    assert r.returncode == 0, f"temiz durumda düştü:\n{r.stdout}{r.stderr}"
    assert "IHLAL" not in r.stdout, f"temiz durumda IHLAL basıldı: {r.stdout!r}"
    assert "OLCULEMEDI" not in r.stdout, \
        f"[{platform}] mtime sondası ölçemedi — 'temiz' sanılan hâl aslında KÖRLÜK: {r.stdout!r}"


@pytest.mark.parametrize("platform", PLATFORMLAR)
def test_A4d2_kod_tazelik_IHLAL_cikis_1(tmp_path, platform):
    """ÖLÇÜLEN VAKA (2026-08-24): birim `active` ama süreç 11 sa 19 dk ESKİ kodu koşuyor.
    "active" ≠ "yeni kodu koşuyor" — kapı düşer, beyan ([B]) yazılmaz.

    `platform="gnu"` KAPININ KOŞTUĞU TEK MAKİNEDİR (A1/Ubuntu): tur-1'de bu dal hiç ölçülmedi
    ve BSD-öncelikli mtime sondası orada sessizce "temiz" diyordu."""
    kok, b = _kod_tazelik_sahne(tmp_path, [
        {"ad": "meridian-learn.service", "execstart": "%KOK%/.venv/bin/python -m learn",
         "baslangic": "1699000000"}], platform=platform)
    r = _kod_tazelik_kos(kok, b)
    assert r.returncode == 1, f"eski kod koşan süreç geçti (rc={r.returncode}):\n{r.stdout}"
    assert r.stdout.startswith("IHLAL meridian-learn.service"), \
        f"IHLAL satırı birimi adıyla söylemiyor: {r.stdout!r}"


@pytest.mark.parametrize("platform", PLATFORMLAR)
def test_A4d3_kod_tazelik_KUM_HAVUZU_BEKLENEN_cikis_0(tmp_path, platform):
    """TSK-140: kum-havuzu birimi başlangıç kodunu taşır — bu IHLAL değil BEKLENEN'dir.
    Ayrım birimin KENDİ beyanından (Description) türer, ad listesinden DEĞİL."""
    kok, b = _kod_tazelik_sahne(tmp_path, [
        {"ad": "meridian-sprint@x.service", "execstart": "%KOK%/.venv/bin/python -m sprint",
         "baslangic": "1699000000", "aciklama": "Meridian sprint (kum havuzunda)"}],
        platform=platform)
    r = _kod_tazelik_kos(kok, b)
    assert r.returncode == 0, f"kum-havuzu birimi dağıtımı düşürdü:\n{r.stdout}"
    assert r.stdout.startswith("BEKLENEN meridian-sprint@x.service"), \
        f"BEKLENEN satırı basılmıyor: {r.stdout!r}"


@pytest.mark.parametrize("platform", PLATFORMLAR)
def test_A4d4_kod_tazelik_LITESTREAM_kapsam_DISI(tmp_path, platform):
    """Kapsam ExecStart'tan TÜRER: litestream (Python değil) kendiliğinden dışarıda kalır —
    ad listesi olsaydı yarın eklenen bir birim aynı sessizlikle unutulurdu."""
    kok, b = _kod_tazelik_sahne(tmp_path, [
        {"ad": "meridian-litestream.service",
         "execstart": "/usr/bin/litestream replicate -config /etc/litestream.yml",
         "baslangic": "1699000000"}], platform=platform)
    r = _kod_tazelik_kos(kok, b)
    assert r.returncode == 0 and not r.stdout.strip(), \
        f"litestream kapsama girdi: rc={r.returncode} {r.stdout!r}"


@pytest.mark.parametrize("platform", PLATFORMLAR)
def test_A4d5_kod_tazelik_KAYNAK_YOKSA_olculemedi(tmp_path, platform):
    """Kaynak mtime okunamazsa hüküm "temiz" DEĞİL "ölçülemedi"dir (uydurma yasağı)."""
    kok, b = _kod_tazelik_sahne(tmp_path, [], platform=platform)
    for p in sorted((kok / "meridian").glob("*.py")):
        p.unlink()
    r = _kod_tazelik_kos(kok, b)
    assert "OLCULEMEDI" in r.stdout, f"kaynaksız kökte ölçülemedi denmiyor: {r.stdout!r}"


def test_A4d6_kod_tazelik_MTIME_SAYI_DEGILSE_olculemedi(tmp_path):
    """Sonda BOŞ değil ama SAYI da değilse hüküm "temiz" DEĞİL "ölçülemedi"dir.

    ÖLÇÜLEN SINIF (inceleme 2026-09-08): boş-mu kontrolü bu hâli GÖRMEZ. `_YENI="Inodes:"` iken
    `[ 1699000000 -lt "Inodes:" ]` bash'te "integer expression expected" ile hata verip YANLIŞ
    döner, döngü sessizce dönmeye devam eder ve betik `exit 0` ile "IHLAL yok" der — betiğin
    KENDİ başlık sözleşmesine ("OLCULEMEDI <ne> — 'temiz' DEĞİLDİR") aykırı. dagit.sh'ın [5b]
    fail-closed dalı da bu hâli yakalayamaz: o dal yalnız `rc≠0 && çıktı boş` hâline bakar.

    SAHNE: GNU `stat` şimi (dosya-sistemi raporu basar) + BSD `find` şimi (`-printf` reddeder),
    yani her iki sonda da "sayı olmayan bir şey" üretir."""
    kok, b = _kod_tazelik_sahne(tmp_path, [
        {"ad": "meridian-learn.service", "execstart": "%KOK%/.venv/bin/python -m learn",
         "baslangic": "1699000000"}], platform="gnu")
    (b / "find").write_text(_BSD_FIND_SIM, encoding="utf-8")
    (b / "find").chmod(0o755)
    r = _kod_tazelik_kos(kok, b)
    assert r.returncode == 0, \
        f"ölçülemeyen mtime ihlal sayıldı (rc={r.returncode}):\n{r.stdout}{r.stderr}"
    assert r.stdout.strip() == "OLCULEMEDI kaynak-mtime-sayisal-degil", (
        "sayısal olmayan mtime 'temiz' sayıldı — kapı sessizce kör "
        f"(çıktı: {r.stdout!r})")


def test_A4d7_kod_tazelik_SUREC_BASLANGICI_SAYI_DEGILSE_olculemedi(tmp_path):
    """Aynı sınıfın ikinci yarısı: `ExecMainStartTimestamp` sayıya çevrilemezse o BİRİM
    ölçülememiştir. Boş dönüş zaten ayrılıyordu; boş OLMAYAN ama sayı olmayan hâl (yerelleştirme,
    `date` sürümü, biçim değişikliği) `[ "x" -lt N ]` hatasına düşüp sessizce "temiz" sayılırdı."""
    kok, b = _kod_tazelik_sahne(tmp_path, [
        {"ad": "meridian-learn.service", "execstart": "%KOK%/.venv/bin/python -m learn",
         "baslangic": "Pzt 2026-09-08 10:00:00 UTC"}])
    r = _kod_tazelik_kos(kok, b)
    assert r.returncode == 0, f"ölçülemeyen birim ihlal sayıldı:\n{r.stdout}{r.stderr}"
    assert r.stdout.strip() == "OLCULEMEDI meridian-learn.service sureç-baslangici-sayisal-degil", (
        "sayısal olmayan süreç başlangıcı sessizce 'temiz' sayıldı "
        f"(çıktı: {r.stdout!r})")


# =================================================================================================
# A5 — dagit.sh: gömülü gövdeler GİTTİ, dosyalar ÇAĞRILIYOR
# =================================================================================================
def test_A5a_dagit_GOMULU_govdeleri_TASIMIYOR():
    """A0 kuralı + 2026-07-30 IndentationError vakası: gömülü çok-satır python/bash YOK.

    ÖLÇÜ HEREDOC'un KENDİSİDİR, "python" kelimesi değil: `<<'PY'` / `<<'REMOTE'` gövdeleri
    betiğin içinde yaşadığı sürece dosyaya çıkarılan kopya İKİNCİ kaynak olur (tek-kaynak
    yasası) ve ikisi sessizce ayrışır."""
    metin = _dagit_metin()
    for isaret in ("<<'PY'", "<<'REMOTE'"):
        assert isaret not in metin, \
            f"dagit.sh hâlâ gömülü gövde taşıyor ({isaret}) — dosyaya çıkarılan kopya ikinci kaynak"


def test_A5b_dagit_DORT_BETIGI_CAGIRIYOR():
    """Çıkarılan gövde ÇAĞRILMAZSA ölü dosyadır (YASA 6: okuyucusuz yazım yok).

    İDDİA ÇAĞRI BİÇİMİNE BAĞLI (düzeltme turu 2): yorumları elemek yetmiyordu — [5b]'nin
    onarım reçetesi `echo` satırı aynı yolu taşıyor ve çağrı bozulunca çivi yeşil kalıyordu.
    `echo`/`printf` satırları da elenir; [5b] için ayrıca çağrının BİÇİMİ ölçülür."""
    kod = "\n".join(_dagit_cagri_satirlari())
    for yol in ("ops/state_fark_hukmu.py", "ops/artefakt_tazelik.py",
                "deploy/oracle-a1/dogrulama_anahtar.py", "deploy/oracle-a1/kod_tazelik.sh"):
        assert yol in kod, (
            f"dagit.sh {yol} betiğini KOD satırında çağırmıyor — dosya okuyucusuz kaldı "
            "(gerekçe yorumunda ya da operatöre basılan bir `echo`da adının geçmesi bir "
            "çağrı DEĞİLDİR)")
        assert (REPO / yol).is_file(), f"çağrılan betik diskte yok: {yol}"
    assert any(KOD_TAZELIK_CAGRI.match(s) for s in _dagit_cagri_satirlari()), (
        "[5b] çağrısı beklenen BİÇİMDE yok: `_tazelik=\"$(\"${SSH[@]}\" \"bash "
        "/opt/meridian/deploy/oracle-a1/kod_tazelik.sh\")\"` — kapı ssh sarmalını kaybetmiş "
        "olabilir (yerelde koşan bir kapı canlıyı ÖLÇMEZ)")


def test_A5c_dagit_sozdizimi_TEMIZ():
    """`bash -n`: dağıtım betiğinin sözdizimi hatası, bakım penceresinin ortasında öğrenilecek
    en pahalı şeydir (v172/v266 çivisinin ikizi — bu dosya tek başına koşulduğunda da ölçülsün)."""
    r = subprocess.run(["bash", "-n", str(DAGIT)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"dagit.sh sözdizimi bozuk:\n{r.stderr}"


def test_A5d_dagit_KURU_KOSUMDA_yazan_cagri_YOK():
    """Kuru koşum sınırı korunur: `--uygula` kapısından ÖNCE canlıya yazan bir çağrı olmamalı.
    Çıkarılan betikler bu sınırı taşımaz — [1b] hükmü kapıdan ÖNCE (salt okuma), kopya SONRA."""
    # yorumlar VE operatöre basılan `echo`lar SAYILMAZ: sıra iddiası ÇAĞRI sırasıdır. Düz dizge
    # araması [5b]'nin onarım reçetesi `echo`unu bulup çivinin hedefini kaçırıyordu (ölçüldü).
    satirlar = _dagit_cagri_satirlari()
    kapi = next(i for i, s in enumerate(satirlar) if '!= "--uygula" ]]' in s)
    hukum = next(i for i, s in enumerate(satirlar) if "ops/state_fark_hukmu.py" in s)
    assert hukum < kapi, "[1b] hüküm çağrısı kuru koşum kapısından SONRA — kuru koşumda diff yok"
    kod_tazelik = next((i for i, s in enumerate(satirlar) if KOD_TAZELIK_CAGRI.match(s)), None)
    assert kod_tazelik is not None, "[5b] çağrısı beklenen biçimde yok — sıra ölçülemez"
    assert kod_tazelik > kapi, "[5b] çağrısı kuru koşumda koşuyor — canlı süreçleri sorguluyor"
