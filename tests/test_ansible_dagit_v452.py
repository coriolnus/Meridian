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

KAPSAM — BÖLÜM B (Task 2, 2026-09-08). `deploy/ansible/dagit.yml` playbook'u. Tek iddia ailesi,
plan Global Constraints'ten: **kapı listesi DÜŞMEZ**. Bir dağıtım betiğini bir araca taşımanın
ölçülen hata sınıfı, kapıların "taşındı" sanılıp aslında düşmesidir.

  B0..B2  ENVANTER ve KURU KOŞUM GÜCÜ — iki play doğru hedeflerde; Play 1 kapıları
          `check_mode: false` + `changed_when: false` (yoksa `--check` HİÇBİR kapıyı ölçmez).
  B3..B7  DAVRANIŞ BİREBİRLİĞİ — stop/start yalnız `birim_adaylari` (şablon ÇÖZÜLEREK);
          [4] `block`/`rescue` reçeteli; [1b]/[5a]/[5b] gövdeleri Task 1 DOSYALARINDAN;
          [B] beyanı dagit.sh `printf` şablonuyla aynı beş alan, AYNI SIRA.
  B8..B9  YÖN ÖLÇÜLÜR, METİN ARANMAZ — `rsync_opts` `rsync_disla`dan ÇÖZÜLEREK türer; [4]
          stop/start `when` ifadeleri altı senaryoluk bir tabloda Jinja ile DEĞERLENDİRİLİR
          (`!= 'inactive'` ile `== 'inactive'` aynı dizgeleri taşır — metin araması kördür).
  B10,B11 ARAÇ GERÇEKTEN KOŞAR — `--syntax-check` + `ansible-lint` (production) temiz;
          `ansible.posix` requirements.yml'de TAM SÜRÜM pinli VE kurulu ("pinledim" != "kurulu").

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
import shutil
import subprocess
import sys
import threading

import jinja2
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


# =================================================================================================
# BÖLÜM B (Task 2) — `deploy/ansible/dagit.yml` playbook'u
# =================================================================================================
# NE ÖLÇER. Bölüm A tek-kaynak listelerini ve dört çıkarılmış betiği ölçtü; bölüm B onları
# KULLANAN playbook'u ölçer. İddia ailesi tektir ve plan Global Constraints'ten gelir:
# **kapı listesi DÜŞMEZ**. Bir dağıtım betiğini bir araca taşımanın ölçülen hata sınıfı, kapıların
# "taşındı" sanılıp aslında düşmesidir — bu yüzden her kapı ADIYLA aranır (B1), yönü Jinja ile
# ÇÖZÜLEREK ölçülür (B9), ve kapı gövdesinin gerçekten Task 1 dosyalarını çağırdığı görülür
# (B5/B6).
#
# A1'E HİÇBİR BAĞLANTI YOK: playbook YALNIZ `--syntax-check` ve `ansible-lint` ile koşturulur
# (B10); `localhost` play'i de KOŞTURULMAZ (kapıları `git`/`uv` çalıştırır ve gerçek ağaca bakar).
# Geri kalan her şey YAML PARSE + Jinja ÇÖZÜMÜDÜR.
#
# NEDEN METİN ARAMASI DEĞİL PARSE. `when: not (x | bool)` ile `when: (x | bool)` aynı dizgeleri
# taşır; metin araması bir kapının YÖNÜNÜ ölçemez (v451'in K2b dersi). B3/B9 bu yüzden şablonları
# `dagit_vars.yml` + rol defaults'undan ÇÖZER ve ifadeyi GERÇEKTEN değerlendirir.

DAGIT_YML = REPO / "deploy" / "ansible" / "dagit.yml"
REQUIREMENTS_YML = REPO / "deploy" / "ansible" / "requirements.yml"
ANSIBLE_README = REPO / "deploy" / "ansible" / "README.md"
INVENTORY_INI = REPO / "deploy" / "ansible" / "inventory.ini"
ROL_DEFAULTS = REPO / "deploy" / "ansible" / "roles" / "meridian_a1" / "defaults" / "main.yml"

#: Plan Global Constraints — SIRA planın Goal satırındaki sıradır, KÜME de o kümedir.
#: `[1]` ile `[1b]` AYRI kapılardır: etiketler TAM eşleşmeyle aranır (alt-dizge araması
#: `[1b]`yi `[1]` sanıp eksik bir kapıyı YEŞİL gösterirdi).
KAPILAR = ("0a", "0b", "0c", "0d", "1", "1b", "1c", "F9", "F10",
           "2", "3", "4", "5", "5a", "5c", "5b", "B")

#: Görev sözlüğünde bir modülün adı bu anahtarlardan biriyle geçer (FQCN'li ve FQCN'siz).
_KOMUT_ANAHTARLARI = ("ansible.builtin.command", "command",
                      "ansible.builtin.shell", "shell")
_SCRIPT_ANAHTARLARI = ("ansible.builtin.script", "script")
_SYSTEMD_ANAHTARLARI = ("ansible.builtin.systemd_service", "systemd_service",
                        "ansible.builtin.systemd", "systemd")
_SYNC_ANAHTARLARI = ("ansible.posix.synchronize", "synchronize")


def _dagit_yml() -> list:
    veri = yaml.safe_load(DAGIT_YML.read_text(encoding="utf-8"))
    assert isinstance(veri, list), f"{DAGIT_YML}: kök düğüm liste (play listesi) değil"
    return veri


def _gorev_listesi(gorevler) -> list[dict]:
    """`block`/`rescue`/`always` içine İNEREK bütün görevleri düzleştirir.

    Düz bir `tasks` gezintisi [4] bakım penceresinin İÇİNİ göremezdi — yani kapının tam da
    stop/start/kopya yaptığı yeri. Kör çivi yasağı: gezilmeyen dal ölçülmemiş daldır."""
    cikti: list[dict] = []
    for gorev in gorevler or []:
        if not isinstance(gorev, dict):
            continue
        cikti.append(gorev)
        for anahtar in ("block", "rescue", "always"):
            cikti.extend(_gorev_listesi(gorev.get(anahtar)))
    return cikti


def _play_gorevleri(play: dict) -> list[dict]:
    cikti: list[dict] = []
    for anahtar in ("pre_tasks", "tasks", "post_tasks", "handlers"):
        cikti.extend(_gorev_listesi(play.get(anahtar)))
    return cikti


def _tum_gorevler() -> list[dict]:
    cikti: list[dict] = []
    for play in _dagit_yml():
        cikti.extend(_play_gorevleri(play))
    return cikti


def _etiketler(gorev: dict) -> set[str]:
    return set(re.findall(r"\[([^\]]+)\]", str(gorev.get("name", ""))))


def _birincil_etiket(gorev: dict) -> str | None:
    """Görevin SAHİBİ olduğu kapı: adın İLK etiketi.

    Bir görev adı başka bir kapıya ATIF yapabilir ("[3] uv sync … [0d]'nin hükmüne dayanır");
    atıf sahiplik değildir ve etiket kümesiyle çalışan bir çivi o atfı sahiplik sanardı."""
    m = re.match(r"\s*\[([^\]]+)\]", str(gorev.get("name", "")))
    return m.group(1) if m else None


def _modul_args(gorev: dict, anahtarlar):
    for anahtar in anahtarlar:
        if anahtar in gorev:
            return gorev[anahtar]
    return None


def _komut_metni(gorev: dict) -> str:
    """Bir command/shell/script görevinin ÇALIŞTIRDIĞI metin (argv birleştirilmiş)."""
    for anahtarlar in (_KOMUT_ANAHTARLARI, _SCRIPT_ANAHTARLARI):
        args = _modul_args(gorev, anahtarlar)
        if args is None:
            continue
        if isinstance(args, str):
            return args
        parcalar: list[str] = []
        for alan in ("cmd", "_raw_params", "argv"):
            deger = args.get(alan)
            if isinstance(deger, str):
                parcalar.append(deger)
            elif isinstance(deger, list):
                parcalar.extend(str(x) for x in deger)
        return " ".join(parcalar)
    return ""


#: `_degiskenler()`in statik olarak ÇÖZEMEDİĞİ türetmeler — B8 bunu OKUR (Yasa 6: raporlanmayan
#: bir "çözemedim" listesi, çözülmüş sanılan bir değerden tehlikelidir).
COZULEMEYEN_TURETMELER: set[str] = set()


def _degiskenler() -> dict:
    """`vars_files`in ikisi birden: `dagit_vars.yml` + A0 rolünün defaults'ı (tek kaynak).

    Ansible vars_files'ı ÖZYİNELEMELİ ve GEÇ çözer: `rsync_opts_disla` bir Jinja DİZGESİDİR ve
    `rsync_disla`dan TÜRER (tek-kaynak). Testin Jinja ortamı bu özyinelemeyi kendiliğinden
    yapmaz, burada iki tur yapılır — yoksa B8 `str + list` ile patlardı, yani çivi kendi
    ölçüm aracının eksikliğinden kırmızı olurdu.

    ÇÖZÜLEMEYEN DEĞER HAM KALIR, ama SESSİZ KALMAZ: `state_versiyonlu`/`dagitim_damgasi`
    koşum-anı register'ına, `repo_kok_yerel` `playbook_dir` sihirli değişkenine bağlıdır ve
    statik olarak çözülemez. Adları `COZULEMEYEN_TURETMELER`e düşer; B8 kendi okuduğu
    anahtarın orada OLMADIĞINI ölçer (aksi hâlde "çözdüm" sanılan bir ham dizge çiviyi
    sessizce kandırırdı)."""
    veri = dict(_vars())
    veri.update(yaml.safe_load(ROL_DEFAULTS.read_text(encoding="utf-8")))
    for _tur in range(2):
        for anahtar, deger in list(veri.items()):
            if not (isinstance(deger, str)
                    and re.fullmatch(r"\{\{.*\}\}", deger.strip(), flags=re.S)):
                continue
            try:
                veri[anahtar] = _cozumle(deger, veri)
                COZULEMEYEN_TURETMELER.discard(anahtar)
            except Exception:  # sessiz-yutma: koşum-anı değişkenine bağlı türetme burada
                # çözülemez; ad `COZULEMEYEN_TURETMELER`e düşer ve B8 tarafından OKUNUR.
                COZULEMEYEN_TURETMELER.add(anahtar)
    return veri


def _jinja_ortami():
    """`when:`/`loop:` ifadelerini ÇÖZMEK için Jinja ortamı (v451 ile aynı desen).

    Metin araması bir kapının YÖNÜNÜ ölçemez: `!= 'inactive'` ile `== 'inactive'` aynı
    dizgeleri taşır. Kapı bu yüzden GERÇEKTEN değerlendirilir."""
    ortam = jinja2.Environment(undefined=jinja2.ChainableUndefined, autoescape=False)
    ortam.filters["bool"] = lambda a: a if isinstance(a, bool) else (
        str(a).lower() in ("yes", "on", "1", "true"))
    ortam.filters["regex_replace"] = lambda s, desen, yerine="": re.sub(desen, yerine, str(s))
    ortam.filters["basename"] = lambda p: pathlib.PurePosixPath(str(p)).name
    ortam.filters["dirname"] = lambda p: str(pathlib.PurePosixPath(str(p)).parent)
    ortam.filters["to_json"] = json.dumps
    # Ansible'ın küme filtreleri (Jinja'da YOK): kapı ifadeleri bunları kullanır ve testin
    # ortamı onları tanımazsa çivi HEDEFİNİ değil kendi eksikliğini ölçerdi (v451 K13 dersi).
    ortam.filters["difference"] = lambda a, b: [x for x in a if x not in b]
    ortam.filters["intersect"] = lambda a, b: [x for x in a if x in b]
    ortam.filters["union"] = lambda a, b: list(a) + [x for x in b if x not in a]
    ortam.filters["symmetric_difference"] = lambda a, b: sorted(
        [x for x in a if x not in b] + [x for x in b if x not in a])
    return ortam


def _cozumle(ifade: str, degiskenler: dict):
    """Bir Jinja ifadesini (tek `{{ }}`) PYTHON NESNESİ olarak çözer."""
    ic = ifade.strip()
    m = re.fullmatch(r"\{\{(.*)\}\}", ic, flags=re.S)
    if m:
        ic = m.group(1)
    return _jinja_ortami().compile_expression(ic, undefined_to_none=False)(**degiskenler)


def _when_degerlendir(ifade, degiskenler: dict) -> bool:
    ifadeler = ifade if isinstance(ifade, list) else [ifade]
    for tek in ifadeler:
        sablon = _jinja_ortami().from_string("{{ (" + str(tek) + ") | bool }}")
        if sablon.render(**degiskenler) != "True":
            return False
    return True


def _ansible_ikili(ad: str) -> str:
    """`ansible-*` ikilisini ÖNCE koşan yorumlayıcının yanında, SONRA PATH'te arar (v451 K13d).

    Bulunamazsa `pytest.fail`: "koşamıyorum" ile "kırmızı" bu çivilerde bilerek AYIRT EDİLMEZ."""
    yanindaki = pathlib.Path(sys.executable).parent / ad
    if yanindaki.is_file():
        return str(yanindaki)
    yoldaki = shutil.which(ad)
    if yoldaki is None:
        pytest.fail(f"{ad} ne `{pathlib.Path(sys.executable).parent}` içinde ne de PATH'te bulundu "
                    "(kurulum: `uv sync` dev grubu). 'koşamıyorum' bu çivide 'kırmızı' sayılır.")
    return yoldaki


# =================================================================================================
# B0 — envanter
# =================================================================================================
def test_B0_task2_dosyalari_YERINDE():
    """Task 2'nin üretmesi gereken iki dosya var ve README dağıtım komutunu BELGELER.

    README çivisi bir biçimsellik değil: `dagit.yml` A1'e karşı YALNIZ Rol-1 tarafından
    koşulur ve komut satırı (ops sözleşmesi) yazılı DEĞİLSE her koşum yeniden icat edilir."""
    eksik = [str(p) for p in (DAGIT_YML, REQUIREMENTS_YML) if not p.is_file()]
    assert not eksik, f"Task 2 dosyaları eksik: {eksik}"
    readme = ANSIBLE_README.read_text(encoding="utf-8")
    assert "dagit.yml" in readme, "README `dagit.yml`den hiç söz etmiyor (ops sözleşmesi yazısız)"
    assert "requirements.yml" in readme, "README koleksiyon kurulumunu belgelemiyor"


# =================================================================================================
# B1 — kapı listesi DÜŞMEZ
# =================================================================================================
def test_B1_her_kapi_etiketi_bir_gorev_adinda():
    """Plan Global Constraints: `[0a]…[B]` etiketlerinin HEPSİ bir görev ADInda geçer.

    Etiket GÖREV ADINDA aranır, dosya metninde DEĞİL: bir yorumda "[F10] taşındı" yazmak
    kapıyı taşımaz. Ölçülen sınıf tam olarak budur ("yorum tarihçe, kod hüküm")."""
    bulunan: set[str] = set()
    for gorev in _tum_gorevler():
        bulunan |= _etiketler(gorev)
    eksik = [k for k in KAPILAR if k not in bulunan]
    assert not eksik, (
        f"kapı düştü — görev adında etiketi olmayan kapılar: {eksik}\n"
        f"playbook'ta bulunan etiketler: {sorted(bulunan)}")


def test_B1b_iki_play_ve_hedefleri():
    """İki play: yerel kapılar (`localhost`, `connection: local`) + A1 (`meridian` grubu).

    Envanterdeki GRUP adı `meridian`dir (host `a1`); `hosts: a1` yazmak envanterin grup/host
    ayrımını (v451'in ölçtüğü WARNING vakası) geri açardı."""
    playler = _dagit_yml()
    assert len(playler) == 2, f"iki play bekleniyordu, {len(playler)} var"
    yerel, uzak = playler
    assert yerel.get("hosts") == "localhost", f"Play 1 hedefi: {yerel.get('hosts')!r}"
    assert yerel.get("connection") == "local", "Play 1 `connection: local` DEĞİL"
    assert uzak.get("hosts") == "meridian", f"Play 2 hedefi: {uzak.get('hosts')!r}"
    envanter = INVENTORY_INI.read_text(encoding="utf-8")
    assert "[meridian]" in envanter, "envanterde `[meridian]` grubu yok — Play 2 boş küme koşardı"


# =================================================================================================
# B2 — Play 1 kapıları check-mode'da da ÖLÇER, ama hiçbir şeyi DEĞİŞTİRMEZ
# =================================================================================================
def test_B2_play1_komut_kapilari_check_mode_false_ve_changed_when_false():
    """Plan Architecture: Play 1 kapıları `check_mode: false` + `changed_when: false`.

    İKİ AYRI İDDİA, ikisi de gerekli. (1) `check_mode: false` olmadan `--check` koşumunda
    `command` görevleri ATLANIR ve kuru koşum HİÇBİR kapıyı ölçmez — dagit.sh'ın kuru koşumu
    [0b]/[0c]/[0d]/[5c]'yi GERÇEKTEN koşuyordu, playbook'un kuru koşumu ondan zayıf olamaz.
    (2) `changed_when: false` olmadan salt-okuma kapıları her koşumda `changed=1` raporlar ve
    "ne değişti" sorusunun cevabı gürültüye gömülür (bedel yasası)."""
    play1 = _dagit_yml()[0]
    ihlaller: list[str] = []
    komut_gorevi_sayisi = 0
    for gorev in _play_gorevleri(play1):
        if _modul_args(gorev, _KOMUT_ANAHTARLARI) is None:
            continue
        komut_gorevi_sayisi += 1
        ad = gorev.get("name")
        if gorev.get("check_mode") is not False:
            ihlaller.append(f"{ad!r}: `check_mode: false` YOK → --check'te ATLANIR (kapı ölçmez)")
        if gorev.get("changed_when") is not False:
            ihlaller.append(f"{ad!r}: `changed_when: false` YOK → salt-okuma kapısı changed der")
    assert komut_gorevi_sayisi >= 4, (
        f"Play 1'de yalnız {komut_gorevi_sayisi} komut görevi var — [0a]/[0b]/[0c]/[0d] kapıları "
        "komutla ölçülür; çivi kör kalmasın")
    assert not ihlaller, "Play 1 kapı ihlalleri:\n" + "\n".join(ihlaller)


# =================================================================================================
# B3 — stop/start YALNIZ `birim_adaylari` üzerinde
# =================================================================================================
#: `systemctl <fiil> <birim>` — `command`/`shell` metninde birim durumunu DEĞİŞTİREN fiiller.
#: `is-active`/`is-enabled`/`show` sorgudur ve BU LİSTEDE YOKTUR (ölçüm kapıları [F10]/[4]).
_SYSTEMCTL_DURUM_FIILI = re.compile(
    r"systemctl\s+(?:--\S+\s+)*(stop|start|restart|reload-or-restart|kill)\s+(\S+)")


def _dongu_ogeleri(gorev: dict, degiskenler: dict):
    """Bir görevin `loop`/`with_items`/`with_list` öğeleri (şablonluysa ÇÖZÜLEREK)."""
    for anahtar in ("loop", "with_items", "with_list"):
        if anahtar not in gorev:
            continue
        ham = gorev[anahtar]
        return list(ham) if isinstance(ham, list) else _cozumle(str(ham), degiskenler)
    return None


def _birim_adlari(gorev: dict, ham_ad: str, degiskenler: dict, ortam) -> set[str] | None:
    """Şablonlu birim adını döngü öğeleriyle ÇÖZER; çözülemezse `None` (= ölçemedi)."""
    if "{{" not in ham_ad:
        return {ham_ad}
    ogeler = _dongu_ogeleri(gorev, degiskenler)
    if ogeler is None:
        return None
    return {ortam.from_string(ham_ad).render(item=o, **degiskenler) for o in ogeler}


def test_B3_systemd_durum_YALNIZ_birim_adaylari():
    """`birim_adaylari` DIŞINDA hiçbir birime durum verilmez — İKİ KOL, ikisi de ölçülür.

    TSK-092 semantiği: hindsight/apisix/litestream/timer'lara DOKUNULMAZ. Şablonlu ad
    (`name: "{{ item }}"`) ÇÖZÜLEREK ölçülür — v451'in K6/K11 dersi: çözülmeyen şablon çiviyi
    "0 düğüm eşleşti" diye SAHTE YEŞİL bırakır. Çözülemeyen şablon KIRMIZIDIR.

    TUR 2 (inceleme K8, 2026-09-08) — ÜÇ GENİŞLEME. Çivinin eski hâli YALNIZ `systemd*` modül
    düğümlerine bakıyordu ve `tests/test_ansible_a0_v451.py` `dagit.yml`i kendi geniş
    taramasından ÇIKARDIĞI için bu dosyada tek zorlayıcı burasıydı: ölçüldü ki
    `command: systemctl stop hindsight-api` hiçbir çiviye takılmıyordu.

      (i) `state: restarted` YASAK (aday birim için de): bakım penceresi durdur → kopyala →
          başlat SIRASIDIR; tek `restarted` o sıranın ortasındaki state kopyasını atlar ve
          [1b]'nin bütün kapısını sessizce baypas ederdi.
      (ii) stop/start görevleri `when` TAŞIR: koşulsuz bir stop/start, TSK-092'nin "istenen
          durum systemd'nin KENDİ beyanıdır" kuralını (yalnız aktif olan durur, yalnız enabled
          olan başlar) ortadan kaldırır — operatörün `disable --now` kararını iki gece üst üste
          bozan sabit `start` paketinin ta kendisi.
      (iii) `command`/`shell` metninde `systemctl (stop|start|restart|reload-or-restart|kill)`
          taranır; birim `birim_adaylari` dışındaysa KIRMIZI. Sorgu fiilleri (`is-active`,
          `is-enabled`) listede YOKTUR — [F10]/[4] ölçümleri onlarla yapılır.

    TUR 3 (yeniden inceleme Y1, 2026-09-08) — KOMUT KOLU ARTIK (i) VE (ii)'Yİ DE TAŞIYOR.
    (i)/(ii) tur 2'de yalnız `systemd_service` koluna uygulanıyordu; ölçüldü ki koşulsuz bir
    `command: systemctl start meridian` 120 çivinin hiçbirine takılmıyordu. Artık komut kolunda
    da `when` ZORUNLU ve `restart`/`reload-or-restart` — `state: restarted` ile aynı sınıf —
    aday birimde bile YASAK: durum değişikliği `systemd_service` ile yazılır, senaryo tablosu
    (B9) orada zorlanır."""
    degiskenler = _degiskenler()
    adaylar = set(degiskenler["birim_adaylari"])
    ortam = _jinja_ortami()
    disari_tasan: list[str] = []
    olculemeyen: list[str] = []
    kosulsuz: list[str] = []
    for gorev in _tum_gorevler():
        ad = gorev.get("name")
        args = _modul_args(gorev, _SYSTEMD_ANAHTARLARI)
        if isinstance(args, dict) and args.get("state") is not None:
            durum = args.get("state")
            if durum == "restarted":
                disari_tasan.append(
                    f"{ad!r}: `state: restarted` — bakım penceresi durdur→kopyala→başlat "
                    "sırasıdır, tek adımlık restart [1b] state kopyasını atlar")
            elif durum in ("stopped", "started"):
                ham_ad = str(args.get("name") or args.get("unit") or "")
                if not ham_ad:
                    olculemeyen.append(f"{ad!r}: `state: {durum}` ama birim ADI YOK")
                else:
                    adlar = _birim_adlari(gorev, ham_ad, degiskenler, ortam)
                    if adlar is None:
                        olculemeyen.append(f"{ad!r}: name={ham_ad!r} — döngü çözülemedi")
                    elif adlar - adaylar:
                        disari_tasan.append(
                            f"{ad!r}: state={durum} → {sorted(adlar - adaylar)}")
                if not gorev.get("when"):
                    kosulsuz.append(f"{ad!r}: `state: {durum}` KOŞULSUZ (`when` yok)")
        metin = _komut_metni(gorev)
        for fiil, ham_birim in _SYSTEMCTL_DURUM_FIILI.findall(metin):
            adlar = _birim_adlari(gorev, ham_birim, degiskenler, ortam)
            if adlar is None:
                olculemeyen.append(
                    f"{ad!r}: `systemctl {fiil} {ham_birim}` — döngü çözülemedi")
                continue
            cikplak = {a.removesuffix(".service") for a in adlar}
            if cikplak - adaylar:
                disari_tasan.append(
                    f"{ad!r}: `systemctl {fiil}` → {sorted(cikplak - adaylar)}")
            # TUR 3 (yeniden inceleme Y1, 2026-09-08): (ii) ve (i) kuralları BU KOLA DA uygulanır.
            # ÖLÇÜLDÜ: `[4]`e koşulsuz `ansible.builtin.command: systemctl start meridian`
            # eklendiğinde v452+v451'in 120 çivisi de YEŞİLDİ — yani aynı fiil modül kolunda
            # yasak, komut kolunda serbestti. `when` orada zorlanıyordu çünkü `kosulsuz` YALNIZ
            # `state:` dalının içinde doluyordu; kapı YARIMDI ve TSK-092'nin doğuş vakası
            # (operatörün `disable --now` kararını iki gece üst üste bozan sabit `start`) tam
            # olarak bu delikten geçerdi.
            if fiil in ("restart", "reload-or-restart"):
                disari_tasan.append(
                    f"{ad!r}: `systemctl {fiil}` — `state: restarted` ile AYNI SINIF: bakım "
                    "penceresi durdur→kopyala→başlat sırasıdır, tek adımlık restart [1b] state "
                    "kopyasını atlar (durum değişikliği `systemd_service` ile yazılır)")
            if not gorev.get("when"):
                kosulsuz.append(
                    f"{ad!r}: `systemctl {fiil} {ham_birim}` KOŞULSUZ (`when` yok)")
    assert not olculemeyen, "çivi ölçemedi (kör kalmasın): " + "; ".join(olculemeyen)
    assert not kosulsuz, (
        "[4] stop/start KOŞULSUZ — istenen durum ölçülmeden dayatılıyor (TSK-092; kural İKİ "
        "KOLDA da geçerli: `systemd_service` ve `command`/`shell`): " + "; ".join(kosulsuz))
    assert not disari_tasan, (
        "`birim_adaylari` DIŞINDA birime durum veriliyor (TSK-092 ihlali): "
        + "; ".join(disari_tasan))


# =================================================================================================
# B4 — [4] bakım penceresi block + rescue; rescue REÇETE verir ve DÜŞER
# =================================================================================================
def test_B4_bakim_penceresi_block_rescue_ve_recete():
    """[4] `block` + `rescue`; rescue `fail` içerir, reçete `backups/state` + `systemctl start` anar.

    NEDEN REÇETE ZORUNLU: pencere ortasında düşen bir dağıtım servisleri DURMUŞ hâlde bırakır.
    Sessiz bir `fail`, operatöre "motor kapalı, ne yapacağımı bilmiyorum" der. dagit.sh'ın
    aynı noktadaki çıktısı yedek yolunu ve elle başlatma satırını BASIYORDU; playbook ondan
    zayıf olamaz. `ignore_errors`/`failed_when: false` ile yutmak zaten YASAK (Yasa 4)."""
    dort = [g for g in _tum_gorevler() if "4" in _etiketler(g) and "block" in g]
    assert len(dort) == 1, f"[4] etiketli tek bir `block` görevi bekleniyordu, {len(dort)} var"
    rescue = dort[0].get("rescue")
    assert rescue, "[4] `rescue` YOK — pencere ortasındaki arıza sessiz kalır"
    dusuren = [g for g in _gorev_listesi(rescue)
               if ("ansible.builtin.fail" in g) or ("fail" in g)]
    assert dusuren, "[4] rescue `fail` içermiyor — yarım pencere 'başarılı' sayılırdı"
    metin = yaml.safe_dump(rescue, allow_unicode=True, default_flow_style=False)
    for beklenen in ("backups/state", "systemctl start"):
        assert beklenen in metin, f"[4] rescue reçetesinde {beklenen!r} geçmiyor"


# =================================================================================================
# B5 — [1b] hükmü DOSYADAN gelir; playbook'ta gömülü çok-satır python YOK
# =================================================================================================
def test_B5_1b_hukmu_state_fark_hukmu_py_cagrisindan():
    """[1b] hükmünü `ops/state_fark_hukmu.py` verir — playbook kendi kopyasını TAŞIMAZ.

    A0 kuralı + 2026-07-30 IndentationError vakası: girintisi bozulan gömülü gövde kapıyı
    bakım penceresinin ORTASINDA düşürür. İki iddia: (1) çağrı VAR, (2) hiçbir komut görevi
    çok satırlı bir python/bash gövdesi TAŞIMIYOR."""
    cagiranlar = [g for g in _tum_gorevler()
                  if "1b" in _etiketler(g) and "ops/state_fark_hukmu.py" in _komut_metni(g)]
    assert cagiranlar, ("[1b] hükmü `ops/state_fark_hukmu.py` çağrısından GELMİYOR — "
                        "kapı ya taşınmadı ya da hükmü kendi kopyasından veriyor")
    gomulu: list[str] = []
    for gorev in _tum_gorevler():
        metin = _komut_metni(gorev)
        if not metin:
            continue
        if "\n" in metin.strip() and re.search(r"^\s*(import |def |for |if )", metin, re.M):
            gomulu.append(f"{gorev.get('name')!r}: çok satırlı gömülü gövde")
    assert not gomulu, "playbook gömülü çok-satır python/bash taşıyor: " + "; ".join(gomulu)


# =================================================================================================
# B6 — [5a]/[5b] Task 1'in DOSYALARINI koşturur
# =================================================================================================
def test_B6_5a_5b_script_dosyalari_task1inkiler():
    """[5a] `dogrulama_anahtar.py`, [5b] `kod_tazelik.sh` — `script:` ile, VAR OLAN dosyalar.

    `script:` yolu `repo_kok_yerel` (DAĞITIM KAYNAĞININ ağacı) üzerinden yazılır ve BURADA
    ÇÖZÜLÜR: yanlış derinlikte bir yol sessizce "dosya yok" ile bakım penceresinde düşerdi
    (v451'in `birim_kaynaklari` derinlik dersi).

    TUR 3 (yeniden inceleme Y4, 2026-09-08) — `playbook_dir` TÜREVİ ARTIK YASAK. K1 düzeltmesi
    rsync/[1b]/[1c]/[F9]/[5c]'yi `repo_kok_yerel`e bağlarken bu iki `script:` yolu
    `playbook_dir` türevinde kalmıştı: `-e repo_kok_yerel=<başka checkout>` ya da
    `-e worktree_gec=true` ile koşulan bir turda DAĞITILAN kod bir ağaçtan, DOĞRULAMA betikleri
    başka ağaçtan gelirdi — ve "canlıda hangi ağacın sha'sı koşuyor" sorusu ikiye bölünürdü.
    (`[0a]` kapı ölçümünün kendisi `playbook_dir`i KULLANMAYA devam eder: orada soru zaten
    "bu playbook HANGİ ağaçta duruyor"dur.)"""
    beklenen = {"5a": DOGRULAMA, "5b": KOD_TAZELIK}
    for etiket, dosya in beklenen.items():
        gorevler = [g for g in _tum_gorevler()
                    if etiket in _etiketler(g) and _modul_args(g, _SCRIPT_ANAHTARLARI) is not None]
        assert gorevler, f"[{etiket}] için `script:` görevi YOK"
        cozulen = []
        for gorev in gorevler:
            metin = _komut_metni(gorev)
            assert "playbook_dir" not in metin, (
                f"[{etiket}] `script:` yolu `playbook_dir` türevinde: {metin.split()[0]!r} — "
                "dağıtılan kod ile doğrulama betikleri AYNI ağaçtan gelmeli (`repo_kok_yerel`)")
            cozulen.append(pathlib.Path(
                metin.replace("{{ repo_kok_yerel }}", str(REPO)).split()[0]).resolve())
        assert dosya.resolve() in cozulen, (
            f"[{etiket}] `script:` {dosya} dosyasını çağırmıyor; çözülen yollar: {cozulen}")
        assert dosya.is_file(), f"{dosya} YOK — [{etiket}] bakım penceresinde düşerdi"


# =================================================================================================
# B7 — [B] beyanı dagit.sh printf şablonuyla AYNI BEŞ ALAN
# =================================================================================================
def _dagit_beyan_alanlari() -> list[str]:
    """dagit.sh'ın [B] `printf` şablonundaki JSON alan adları — SIRAYLA."""
    m = re.search(r"printf '(\{[^\n]*\})\\n'", _dagit_metin())
    assert m, "dagit.sh'ta [B] printf şablonu bulunamadı — çivi bayatlamış"
    return re.findall(r'"([a-z_]+)":', m.group(1))


#: Beyanın dagit.sh printf'ine göre BEYANLI uzantısı (TUR 2, inceleme K1 hükmü 2026-09-08):
#: `worktree_gec` — ana-checkout kapısının bilinçli istisnası KULLANILDIYSA beyana girer.
#: Kapının kendisi bir kayıt bırakmasaydı, "hangi ağaç dağıtıldı" sorusu ancak canlıdaki kodu
#: okuyarak cevaplanabilirdi (2026-08-26 vaka sınıfı). Uzantı LİSTELİDİR: adı buraya YAZILMAYAN
#: altıncı bir alan çiviyi kırar — beyan sözleşmesi sessizce büyüyemez.
BEYAN_EK_ALANLARI = ("worktree_gec",)


def test_B7_B_beyani_dagit_printf_ile_AYNI_BES_ALAN():
    """Beyanın alan kümesi VE SIRASI dagit.sh ile aynı (ortamlar-arası kıyasın sözleşmesi).

    Okuyucu (Yasa 6) envanter/denetim turlarının ortamlar-arası kıyasıdır ve o kıyas ALAN
    ADIYLA okur: bir alanın adı değişirse kıyas sessizce 'ölçemedi'ye düşer. Sıra da ölçülür —
    iki üreticinin (dagit.sh printf · playbook) geçiş süresince kıyaslanabilir beyan üretmesi
    Task 3'e kadar tek güvencedir."""
    beklenen = _dagit_beyan_alanlari()
    assert len(beklenen) == 5, f"dagit.sh printf'inde 5 alan bekleniyordu: {beklenen}"
    adaylar = []
    for gorev in _tum_gorevler():
        if "B" not in _etiketler(gorev):
            continue
        args = gorev.get("ansible.builtin.set_fact") or gorev.get("set_fact")
        if not isinstance(args, dict):
            continue
        for deger in args.values():
            if isinstance(deger, dict) and set(deger) >= set(beklenen):
                adaylar.append(list(deger))
    assert adaylar, f"[B] beyanını kuran `set_fact` yok ya da alanları farklı; beklenen: {beklenen}"
    for alanlar in adaylar:
        assert alanlar[:len(beklenen)] == beklenen, (
            f"[B] ilk beş alanın SIRASI dagit.sh printf'inden farklı: {alanlar} != {beklenen}")
        ek = tuple(alanlar[len(beklenen):])
        assert ek == BEYAN_EK_ALANLARI[:len(ek)] and set(ek) <= set(BEYAN_EK_ALANLARI), (
            f"[B] beyanında BEYANSIZ ek alan: {ek} — izinli uzantı: {BEYAN_EK_ALANLARI} "
            "(yeni alan bir sözleşme değişikliğidir: README 'BEYANLI farklar'a yazılır)")


# =================================================================================================
# B8 — `synchronize` dışlamaları `rsync_disla`dan TÜRER, `delete: true`
# =================================================================================================
#: `[1]` kuru koşumun rsync bayrakları — dışlama türetmelerinin DIŞINDA izinli olan TEK küme.
#: `[2]` için bu küme BOŞTUR: gerçek koşum yalnız dışlamalarla koşar.
RSYNC_BAYRAK_BEYAZ_LISTESI = {"1": {"--dry-run", "--itemize-changes"}, "2": set()}


def test_B8_synchronize_rsync_opts_rsync_disladan_turer_ve_delete():
    """İki `synchronize` görevi ([1] kuru + [2] gerçek): `--delete` AÇIK, dışlamalar vars'tan.

    `--delete` ile koşan bir rsync'te dışlama listesi bir KONFOR değil GÜVENLİK sınırıdır
    (vars dosyasının başlığı: `.dash.env` 2026-08-01'de bu yüzden SİLİNDİ). Liste playbook'a
    ELLE yazılırsa iki kaynak doğar ve biri sessizce eskir; bu yüzden `rsync_opts` ifadesi
    ÇÖZÜLÜR ve `rsync_disla`nın tam kümesini ürettiği ölçülür.

    TUR 2 (inceleme K3, 2026-09-08) — ÇİVİ ARTIK İKİ YÖNLÜ. Eski hâli yalnız `beklenen - çözülen`
    (EKSİK) ölçüyordu; ölçüldü ki `--delete-excluded` EKLEMEK 62 çivinin hiçbirini kırmıyordu —
    yani listeye bir bayrak eklemenin bedeli sıfırdı ve o bayrak dışlanmış her şeyi (state,
    backups, `.dash.env`) canlıdan SİLERDİ. Artık `çözülen - beklenen` de ölçülür ve yalnız
    BEYAZ LİSTEdeki bayraklara izin verilir.

    Ayrıca kapıların YÖNÜ etikete bağlandı (inceleme K3'ün ikinci kolu): `[1]` kuru koşumdur ve
    `--dry-run` + `--itemize-changes` ZORUNLUDUR; `[2]` gerçek koşumdur ve `--dry-run` YASAKTIR
    (`check_mode` anahtarı da bulunamaz — modül check-mode'da kendi `--dry-run`ını ekler; elle
    bir `check_mode: false` gerçek dağıtımı kuru koşuma çevirir ve HİÇBİR çivi bunu görmezdi)."""
    degiskenler = _degiskenler()
    assert "rsync_opts_disla" not in COZULEMEYEN_TURETMELER, (
        "`rsync_opts_disla` türetmesi ÇÖZÜLEMEDİ — bu çivi aşağıda ham bir dizgeyi ölçerdi "
        "(kör çivi yasağı). Türetme ifadesi bozulmuş olabilir: deploy/ansible/vars/dagit_vars.yml")
    beklenen = {f"--exclude={x}" for x in degiskenler["rsync_disla"]}
    sync_gorevleri = [g for g in _tum_gorevler()
                      if _modul_args(g, _SYNC_ANAHTARLARI) is not None]
    assert len(sync_gorevleri) == 2, (
        f"iki `synchronize` görevi bekleniyordu ([1] kuru + [2] gerçek), {len(sync_gorevleri)} var")
    etiketlenen: dict[str, dict] = {}
    for gorev in sync_gorevleri:
        ortak = _etiketler(gorev) & set(RSYNC_BAYRAK_BEYAZ_LISTESI)
        assert len(ortak) == 1, (
            f"{gorev.get('name')!r}: `synchronize` görevi tam olarak bir [1]/[2] etiketi "
            f"taşımalı (bulunan: {sorted(_etiketler(gorev))})")
        etiketlenen[ortak.pop()] = gorev
    assert set(etiketlenen) == set(RSYNC_BAYRAK_BEYAZ_LISTESI), (
        f"[1] kuru + [2] gerçek `synchronize` görevleri eksik: {sorted(etiketlenen)}")
    for etiket, gorev in etiketlenen.items():
        args = _modul_args(gorev, _SYNC_ANAHTARLARI)
        assert args.get("delete") is True, f"{gorev.get('name')!r}: `delete: true` YOK"
        ham = args.get("rsync_opts")
        assert ham is not None, f"{gorev.get('name')!r}: `rsync_opts` YOK"
        cozulen = _cozumle(str(ham), degiskenler) if isinstance(ham, str) else list(ham)
        cozulen = [str(x) for x in cozulen]
        eksik = beklenen - set(cozulen)
        assert not eksik, (f"{gorev.get('name')!r}: `rsync_disla` öğeleri rsync_opts'a GİRMEDİ: "
                           f"{sorted(eksik)}")
        fazla = set(cozulen) - beklenen - RSYNC_BAYRAK_BEYAZ_LISTESI[etiket]
        assert not fazla, (
            f"{gorev.get('name')!r}: BEYAZ LİSTE DIŞI rsync bayrağı: {sorted(fazla)}. "
            "Yeni bir bayrak bilinçli bir karardır ve `--delete` ile koşan bir rsync'te "
            "dışlama sınırını (state/backups/.dash.env) delebilir — çiviyi de güncelleyin.")
        if etiket == "1":
            for zorunlu in ("--dry-run", "--itemize-changes"):
                assert zorunlu in cozulen, (
                    f"[1] kuru koşumda {zorunlu} YOK — 'ne değişecek' okunamaz")
        else:
            assert "--dry-run" not in cozulen, (
                "[2] GERÇEK rsync `--dry-run` taşıyor — dağıtım sessizce hiçbir şey taşımaz")
            assert "check_mode" not in gorev, (
                "[2]'de `check_mode` anahtarı YASAK: `check_mode: false` gerçek koşumu değil "
                "KURU koşumu bozardı; modül check-mode'da kendi `--dry-run`ını zaten ekler")


# =================================================================================================
# B9 — [4] stop/start `when` ifadeleri: SENARYO TABLOSU (Jinja ile GERÇEKTEN değerlendirilir)
# =================================================================================================
#: (aktiflik, etkinlik) → (durdurulmalı mı, başlatılmalı mı). Kaynak: dagit.sh [4] şerhi.
#: `activating`/`deactivating`/`failed` DURDURULUR — ölçüt `!= inactive`, `= active` DEĞİL
#: ("süreç ya da artık durum vardır ve durdurmak GÜVENLİ yöndür"). `disabled` BAŞLATILMAZ
#: (TSK-092: sabit `start` paketi operatörün `disable --now` kararını iki gece üst üste bozdu).
B9_SENARYOLAR = (
    ("active", "enabled", True, True),
    ("inactive", "enabled", False, True),
    ("inactive", "disabled", False, False),
    ("active", "disabled", True, False),
    ("failed", "enabled", True, True),
    ("activating", "enabled", True, True),
)


def _dort_durum_gorevi(durum: str) -> dict:
    gorevler = [g for g in _tum_gorevler()
                if "4" in _etiketler(g)
                and isinstance(_modul_args(g, _SYSTEMD_ANAHTARLARI), dict)
                and _modul_args(g, _SYSTEMD_ANAHTARLARI).get("state") == durum]
    assert len(gorevler) == 1, f"[4] içinde `state: {durum}` görevi tek olmalı, {len(gorevler)} var"
    return gorevler[0]


@pytest.mark.parametrize("aktiflik,etkinlik,durmali,baslamali", B9_SENARYOLAR)
def test_B9_pencere_when_ifadeleri_senaryo_tablosu(aktiflik, etkinlik, durmali, baslamali):
    """[4] stop/start kapılarının YÖNÜ altı senaryoda Jinja ile ÇÖZÜLEREK ölçülür.

    Metin araması burada işe yaramaz: `!= 'inactive'` ile `== 'inactive'` aynı dizgeleri
    taşır ve ters çevrilmiş bir kapı YEŞİL kalırdı. Tablo dagit.sh [4] şerhinden türer."""
    degiskenler = dict(_degiskenler())
    degiskenler.update({
        "item": "meridian",
        "pencere_aktif": {"meridian": aktiflik},
        "pencere_etkin": {"meridian": etkinlik},
    })
    dur = _dort_durum_gorevi("stopped")
    bas = _dort_durum_gorevi("started")
    assert _when_degerlendir(dur.get("when"), degiskenler) is durmali, (
        f"[4] stop kapısı yanlış yön: aktiflik={aktiflik} → beklenen durmalı={durmali} "
        f"(`when`: {dur.get('when')!r})")
    assert _when_degerlendir(bas.get("when"), degiskenler) is baslamali, (
        f"[4] start kapısı yanlış yön: etkinlik={etkinlik} → beklenen başlamalı={baslamali} "
        f"(`when`: {bas.get('when')!r})")


# =================================================================================================
# B10 — `--syntax-check` + `ansible-lint` temiz
# =================================================================================================
def test_B10a_dagit_yml_syntax_check_gecer():
    """`ansible-playbook --syntax-check` çıkış 0 (A1'e BAĞLANMAZ — salt ayrıştırma)."""
    ikili = _ansible_ikili("ansible-playbook")
    sonuc = subprocess.run([ikili, "--syntax-check", "-i", str(INVENTORY_INI), str(DAGIT_YML)],
                           cwd=REPO, capture_output=True, text=True, timeout=120)
    assert sonuc.returncode == 0, (
        f"--syntax-check çıkış {sonuc.returncode}\n--- stdout ---\n{sonuc.stdout}"
        f"\n--- stderr ---\n{sonuc.stderr}")


def test_B10b_dagit_yml_ansible_lint_production_temiz():
    """`ansible-lint deploy/ansible/dagit.yml` temiz (profil kaynağı: repo kökü `.ansible-lint`)."""
    ikili = _ansible_ikili("ansible-lint")
    sonuc = subprocess.run([ikili, "deploy/ansible/dagit.yml"],
                           cwd=REPO, capture_output=True, text=True, timeout=300)
    assert sonuc.returncode == 0, (
        f"ansible-lint çıkış {sonuc.returncode} (production profili temiz DEĞİL)\n"
        f"--- stdout ---\n{sonuc.stdout}\n--- stderr ---\n{sonuc.stderr}")


# =================================================================================================
# B11 — `ansible.posix` koleksiyonu PİNLİ ve KURULU
# =================================================================================================
def test_B11a_requirements_yml_ansible_posix_PINLI():
    """`requirements.yml` `ansible.posix`i TAM SÜRÜMLE pinler.

    Pinsiz bir koleksiyon, dağıtım aracının davranışını kurulum GÜNÜNE bağlar: aynı playbook
    iki makinede iki farklı `synchronize` sürümüyle koşar ve fark ancak bakım penceresinde
    görülür. `>=`/`*` bir pin DEĞİLDİR."""
    veri = yaml.safe_load(REQUIREMENTS_YML.read_text(encoding="utf-8"))
    kolleksiyonlar = {k["name"]: k for k in veri.get("collections", [])}
    assert "ansible.posix" in kolleksiyonlar, (
        f"{REQUIREMENTS_YML}: `ansible.posix` yok — `synchronize` modülü çözülemez")
    surum = str(kolleksiyonlar["ansible.posix"].get("version", ""))
    assert re.fullmatch(r"\d+\.\d+\.\d+", surum), f"pin TAM SÜRÜM değil: {surum!r}"


def test_B11b_ansible_posix_KURULU_ve_requirements_ile_AYNI_SURUM():
    """`ansible-galaxy collection list` `ansible.posix`i requirements.yml'deki sürümle gösterir.

    "Pinledim" ile "kurulu" AYNI ŞEY DEĞİLDİR: kurulu olmayan koleksiyonla `--syntax-check`
    bile `synchronize`i çözemez ve kapı [1]/[2] doğduğu gün düşer."""
    veri = yaml.safe_load(REQUIREMENTS_YML.read_text(encoding="utf-8"))
    beklenen = str({k["name"]: k for k in veri["collections"]}["ansible.posix"]["version"])
    ikili = _ansible_ikili("ansible-galaxy")
    sonuc = subprocess.run([ikili, "collection", "list"],
                           cwd=REPO, capture_output=True, text=True, timeout=120)
    eslesme = re.search(r"^ansible\.posix\s+(\S+)", sonuc.stdout, flags=re.MULTILINE)
    assert eslesme, (
        "ansible.posix KURULU DEĞİL. Kurulum (kullanıcı düzeyine gider):\n"
        "  ansible-galaxy collection install -r deploy/ansible/requirements.yml\n"
        f"--- stdout ---\n{sonuc.stdout}\n--- stderr ---\n{sonuc.stderr}")
    assert eslesme.group(1) == beklenen, (
        f"kurulu sürüm {eslesme.group(1)} != requirements.yml pini {beklenen}")


# =================================================================================================
# B12 — dağıtım KAYNAĞI ana checkout'tur; worktree'den koşum BEYANLI istisnadır
# =================================================================================================
def _play1_assertler() -> list[dict]:
    return [g for g in _play_gorevleri(_dagit_yml()[0])
            if isinstance(g.get("ansible.builtin.assert") or g.get("assert"), dict)]


def _assert_args(gorev: dict) -> dict:
    return gorev.get("ansible.builtin.assert") or gorev.get("assert")


#: `repo_kok_yerel` kapısının senaryo tablosu: (ana checkout toplevel, playbook toplevel,
#: `-e worktree_gec=`) → kapı GEÇER mi. Kaynak: dagit.sh `REPO="$HOME/AI-Trading"` (CWD'ye
#: BAKMAZ) + CLAUDE.md §9 ("dagit.sh HER ZAMAN ana checkout HEAD'ini iter, senin ağacını değil").
_ANA = "/home/kullanici/AI-Trading"
_WT = "/home/kullanici/AI-Trading/.claude/worktrees/agent-xyz"
B12_SENARYOLAR = (
    (_ANA, _ANA, False, True),      # ana checkout'tan koşum — geçer
    (_ANA, _WT, False, False),      # worktree'den koşum — DÜŞER (2026-08-26 vaka sınıfı)
    (_ANA, _WT, True, True),        # bilinçli istisna BEYAN edilmiş — geçer
    (_WT, _WT, False, False),       # repo kökü bir worktree'ye çözülüyor — DÜŞER
)


def test_B12_repo_koku_ANA_CHECKOUT_ve_worktree_kapisi():
    """`repo_kok_yerel` playbook'un KENDİ ağacı OLAMAZ; Play 1'de ana-checkout kapısı vardır.

    ÖLÇÜLEN SINIF (2026-08-26, CLAUDE.md §9): `dagit.sh` NEREDEN çağrılırsa çağrılsın ana
    checkout'un O ANKİ HEAD'ini iter — "ağacım temiz" bir güvence DEĞİLDİR. `playbook_dir`den
    türetilmiş bir depo kökü bu güvenceyi tersine çevirir: bir worktree'de commit edilmiş
    (ama BİRLEŞMEMİŞ) bir dal, [0a] temiz-ağaç kapısından geçer, canlıya gider ve [B] beyanı
    onu `deployed_sha` diye yazar; ana checkout'un tepesi hiç dağıtılmaz.

    ÜÇ İDDİA: (1) `repo_kok_yerel` `playbook_dir` TÜREVİ DEĞİLDİR ve varsayılanı dagit.sh'ın
    `REPO="$HOME/AI-Trading"` satırıyla aynı yeri gösterir; (2) hiçbir `synchronize` `src`i
    `playbook_dir`den türemez; (3) Play 1'de `worktree_gec` istisnasını tanıyan bir `assert`
    vardır ve YÖNÜ dört senaryoda Jinja ile ÇÖZÜLEREK ölçülür (metin araması bir kapının yönünü
    ölçemez)."""
    ham = str(_vars()["repo_kok_yerel"])
    assert "playbook_dir" not in ham, (
        f"`repo_kok_yerel` `playbook_dir`den TÜRÜYOR ({ham!r}) — playbook kendi ağacını dağıtır. "
        "dagit.sh CWD'ye bakmaz (REPO=\"$HOME/AI-Trading\"); playbook da bakmamalı.")
    dagit_repo = re.search(r'REPO="\$HOME/([^"]+)"', _dagit_metin())
    assert dagit_repo, "dagit.sh'ta `REPO=\"$HOME/…\"` satırı bulunamadı — çivi bayatlamış"
    assert "env" in ham and "HOME" in ham and dagit_repo.group(1) in ham, (
        f"`repo_kok_yerel` dagit.sh'ın kökünü ($HOME/{dagit_repo.group(1)}) göstermiyor: {ham!r}")

    for gorev in _tum_gorevler():
        args = _modul_args(gorev, _SYNC_ANAHTARLARI)
        if not isinstance(args, dict):
            continue
        assert "playbook_dir" not in str(args.get("src")), (
            f"{gorev.get('name')!r}: rsync KAYNAĞI `playbook_dir` türevi — koşan ağaç dağıtılır")

    kapilar = [g for g in _play1_assertler()
               if "worktree_gec" in yaml.safe_dump(_assert_args(g), allow_unicode=True)]
    assert len(kapilar) == 1, (
        f"Play 1'de `worktree_gec` istisnasını tanıyan tek bir `assert` bekleniyordu, "
        f"{len(kapilar)} var — ana-checkout kapısı YOK ya da iki kaynağa bölünmüş")
    kapi = _assert_args(kapilar[0])
    mesaj = str(kapi.get("fail_msg", ""))
    assert "worktree_gec=true" in mesaj, (
        "kapının `fail_msg`i bilinçli istisnanın REÇETESİNİ (`-e worktree_gec=true`) vermiyor")
    for senaryo in B12_SENARYOLAR:
        ana, playbook, gec, gecmeli = senaryo
        degiskenler = dict(_degiskenler())
        degiskenler.update({
            "repo_kok_yerel": _ANA,
            "toplevel_ana": {"stdout": ana},
            "toplevel_playbook": {"stdout": playbook},
            "worktree_gec": gec,
        })
        assert _when_degerlendir(kapi["that"], degiskenler) is gecmeli, (
            f"ana-checkout kapısı yanlış yön: ana={ana!r} playbook={playbook!r} "
            f"worktree_gec={gec} → beklenen geçer={gecmeli} (`that`: {kapi['that']!r})")


# =================================================================================================
# B13 — [B] bayt-özdeşlik kıyası GERÇEKTEN tutuyor mu (sentetik localhost play'i, gerçek ansible)
# =================================================================================================
def _play2() -> dict:
    return _dagit_yml()[1]


def _b_gorevi(kosul) -> dict:
    adaylar = [g for g in _tum_gorevler() if "B" in _etiketler(g) and kosul(g)]
    assert len(adaylar) == 1, f"[B] için tek bir eşleşen görev bekleniyordu, {len(adaylar)} var"
    return adaylar[0]


def test_B13_B_beyani_BAYT_OZDES_kiyasi_GERCEK_ansible_ile(tmp_path):
    """Beyanın "bayt-özdeş doğrulandı" dalı GERÇEKTEN ulaşılabilir mi — ölçülür, varsayılmaz.

    ÖLÇÜLEN SINIF (inceleme K2, 2026-09-08): kıyas ifadesi bir FOLDED skalerin içinde `'\\n'`
    yazıyordu; Ansible o iki karakteri satır sonuna ÇEVİRMEZ, yani `<json>` + `\\n` ile
    `<json>` + `<yeni satır>` hiçbir zaman eşit olmaz ve kapı HER KOŞUMDA "YAZILAMADI" derdi —
    B7 alan adlarını ölçtüğü için bu dal hiç ölçülmemişti (kapının kendisi kör).

    YÖNTEM: playbook'un KENDİ `satir_sonu`/`beyan_metni` değerleri ve `tee` argümanları
    ÇIKARILIR, `tmp_path`te SENTETİK bir `localhost` play'ine konur ve GERÇEK `ansible-playbook`
    ile koşturulur (gerçek `dagit.yml` A1'e/gerçek ağaca KOŞULMAZ). Dosyaya yazılan bayt ile
    kıyas ifadesinin beklediği bayt aynıysa play `EŞİT` basar."""
    play2 = _play2()
    play_vars = play2.get("vars") or {}
    assert "satir_sonu" in play_vars and "beyan_metni" in play_vars, (
        "[B] beklenen içeriği play `vars`ında TEK YERDE kurulmuyor "
        f"(`satir_sonu` + `beyan_metni`); bulunan: {sorted(play_vars)}")

    tee = _b_gorevi(lambda g: "tee" in _komut_metni(g))
    tee_args = _modul_args(tee, _KOMUT_ANAHTARLARI)
    assert str(tee_args.get("stdin")).strip() == "{{ beyan_metni }}", (
        f"[B] `tee` görevi beklenen içeriği YENİDEN kuruyor: {tee_args.get('stdin')!r} — "
        "iki kaynak sessizce ayrışır (tek-kaynak yasası)")
    assert tee_args.get("stdin_add_newline") is False, (
        "[B] `tee` görevinde `stdin_add_newline: false` YOK — modül kendi satır sonunu ekler ve "
        "beklenen içerik ile yazılan bayt AYRIŞIR")

    kiyas = _b_gorevi(lambda g: "b64decode" in _debug_msg(g))
    kiyas_metni = " ".join(_debug_msg(kiyas).split())
    assert "(beyan_canli.content | b64decode) == beyan_metni" in kiyas_metni, (
        "[B] bayt kıyası `beyan_metni` ile yapılmıyor — beklenen içerik ikinci kez kuruluyor")

    ornek = {}
    for alan in _dagit_beyan_alanlari() + list(BEYAN_EK_ALANLARI):
        if alan == "sandbox_eski_kod":
            ornek[alan] = []
        elif alan in ("kirli_gec_kullanildi", "worktree_gec"):
            ornek[alan] = False
        else:
            ornek[alan] = "ornek"

    hedef = tmp_path / "dagitim.json"
    sentetik = tmp_path / "beyan_kiyasi.yml"
    gorevler = "\n".join(
        f"          {alan}: {json.dumps(deger)}" for alan, deger in ornek.items())
    sentetik.write_text(
        "---\n"
        "- name: \"[B] bayt-ozdeslik kiyasi (SENTETIK — dagit.yml'in KENDI ifadeleri)\"\n"
        "  hosts: localhost\n"
        "  connection: local\n"
        "  gather_facts: false\n"
        "  vars:\n"
        f"    satir_sonu: {json.dumps(play_vars['satir_sonu'])}\n"
        f"    beyan_metni: {json.dumps(play_vars['beyan_metni'])}\n"
        # ÇİVİNİN KENDİ satır sonu: playbook'unkinden BAĞIMSIZ ve her zaman GERÇEK bir `\n`.
        # Bağımsız olmasaydı, `satir_sonu`nu bozan bir mutasyon her iki tarafı birden bozar ve
        # kıyas KENDİ İÇİNDE tutarlı kalırdı — dosyaya iki karakterlik `\\n` yazılmış olmasına
        # rağmen çivi YEŞİL kalırdı (kendi kopyasını doğrulayan kıyas).
        "    dogru_satir_sonu: \"\\n\"\n"
        f"    hedef: {json.dumps(str(hedef))}\n"
        "  tasks:\n"
        "    - name: Beyan olgusu (alanlar dagit.sh printf sablonundan)\n"
        "      ansible.builtin.set_fact:\n"
        "        dagitim_beyani:\n"
        f"{gorevler}\n"
        "    - name: Gecici dosyaya yaz\n"
        "      ansible.builtin.command:\n"
        "        argv:\n"
        "          - tee\n"
        "          - \"{{ hedef }}\"\n"
        "        stdin: \"{{ beyan_metni }}\"\n"
        "        stdin_add_newline: false\n"
        "      changed_when: true\n"
        "    - name: Yazilan beyan okunur\n"
        "      ansible.builtin.slurp:\n"
        "        src: \"{{ hedef }}\"\n"
        "      register: beyan_canli\n"
        "    - name: Hukum\n"
        "      ansible.builtin.debug:\n"
        "        msg: \"{{ 'EŞİT' if ((beyan_metni is string)"
        " and ((beyan_canli.content | b64decode) == beyan_metni)"
        " and ((beyan_canli.content | b64decode)"
        " == ((dagitim_beyani | to_json) ~ dogru_satir_sonu))) else 'AYRIK' }}\"\n",
        encoding="utf-8")
    ikili = _ansible_ikili("ansible-playbook")
    ortam = dict(os.environ, ANSIBLE_LOCALHOST_WARNING="False",
                 ANSIBLE_INVENTORY_UNPARSED_WARNING="False")
    sonuc = subprocess.run([ikili, "-i", "localhost,", "-c", "local", str(sentetik)],
                           cwd=str(tmp_path), capture_output=True, text=True,
                           encoding="utf-8", timeout=180, env=ortam)
    assert sonuc.returncode == 0, (
        f"sentetik kıyas play'i çıkış {sonuc.returncode}\n{sonuc.stdout}\n{sonuc.stderr}")
    assert "AYRIK" not in sonuc.stdout and "EŞİT" in sonuc.stdout, (
        "[B] bayt kıyası TUTMUYOR: yazılan dosya JSON+`\\n` değil ya da kıyas kendi kopyasını "
        "doğruluyor — kapı her koşumda 'YAZILAMADI' derdi (ya da canlıya bozuk bayt yazardı)."
        f"\n--- stdout ---\n{sonuc.stdout}")


# =================================================================================================
# B14 — check-mode: her atlanan kapının ADIYLA raporlanan bir karşılığı var
# =================================================================================================
def _debug_msg(gorev: dict) -> str:
    args = gorev.get("ansible.builtin.debug") or gorev.get("debug")
    return str(args.get("msg", "")) if isinstance(args, dict) else ""


def _when_maddeleri(gorev: dict) -> list[str]:
    """`when:` maddeleri TEK TEK (liste yazımı bir VE zinciridir; madde madde ölçülür)."""
    ham = gorev.get("when")
    if ham is None:
        return []
    return [str(x).strip() for x in (ham if isinstance(ham, list) else [ham])]


def _when_metni(gorev: dict) -> str:
    return " ; ".join(_when_maddeleri(gorev))


def test_B14_check_mode_karsiliklari_ve_5_healthz_RAPOR():
    """`when: not ansible_check_mode` taşıyan HER kapı etiketinin check-mode karşılığı vardır.

    A0 K4 deseni: atlanan bir kapı bir sağlık hükmü DEĞİLDİR, soru cevapsız kalmıştır — ve
    cevapsızlık ADIYLA basılmazsa kuru koşum "temiz" görünür. Ölçüldü (inceleme K4, 2026-09-08):
    `[5]` healthz check-mode'da SESSİZCE atlanıyordu, oysa README ve rapor "ÖLÇÜLMEDİ diye
    raporlar" diyordu — beyan ile davranış ayrışmıştı.

    İkinci iddia `[5]`in DAVRANIŞIDIR: dagit.sh healthz'i yalnız BASAR (`curl -s -o /dev/null
    -w`; `-f` YOK, çıkış kodu yutulur) — hüküm `[5a]`/`[5b]`dedir. Playbook da düşürmemeli:
    `status_code` 503'ü KABUL eder ve `until`/`retries` ile bir kapıya dönüşmez.

    TUR 3 (yeniden inceleme Y7, 2026-09-08) — YAZIM ARTIK KANONİK OLMAK ZORUNDA. Tarama METİN
    tabanlıdır ve öyle kalıyor (bir `when`i iki kez değerlendirmek, koşum-anı register'ları
    tanımsızken kapının YÖNÜNÜ değil testin eksikliğini ölçerdi); ama eşdeğer-farklı bir yazım
    (`ansible_check_mode | bool == false`) taramanın DIŞINDA kalıyordu ve o görevin karşılığı
    silinse çivi ancak KARDEŞ görevin kanonik yazımı sayesinde ötüyordu — koruma TESADÜFİYDİ.
    Artık `ansible_check_mode` geçen her `when` maddesi ya `not ansible_check_mode` ya
    `ansible_check_mode` olmak zorunda; üçüncü bir yazım ADIYLA KIRMIZIdır (fail-closed)."""
    atlanan_etiketler: set[str] = set()
    raporlanan_etiketler: set[str] = set()
    beyansiz: list[str] = []
    for gorev in _tum_gorevler():
        etiket = _birincil_etiket(gorev)
        if etiket is None:
            continue
        for madde in _when_maddeleri(gorev):
            if "ansible_check_mode" not in madde:
                continue
            if madde == "not ansible_check_mode":
                atlanan_etiketler.add(etiket)
            elif madde == "ansible_check_mode":
                raporlanan_etiketler.add(etiket)
            else:
                beyansiz.append(f"{gorev.get('name')!r}: {madde!r}")
    assert not beyansiz, (
        "KANONİK OLMAYAN check-mode yazımı (yalnız `not ansible_check_mode` / "
        "`ansible_check_mode` maddeleri; bileşik koşul AYRI madde olarak yazılır): "
        + "; ".join(beyansiz))
    assert atlanan_etiketler, "hiçbir görev `not ansible_check_mode` taşımıyor — çivi kör"
    eksik = sorted(atlanan_etiketler - raporlanan_etiketler)
    assert not eksik, (
        f"check-mode'da ATLANAN ama 'ÖLÇÜLMEDİ' demeyen kapılar: {eksik} — kuru koşum bu "
        "kapılar hakkında sessiz kalır ve sessizlik 'temiz' diye okunur")

    healthz = [g for g in _tum_gorevler()
               if "5" in _etiketler(g)
               and isinstance(g.get("ansible.builtin.uri") or g.get("uri"), dict)]
    assert len(healthz) == 1, f"[5] healthz `uri` görevi tek olmalı, {len(healthz)} var"
    args = healthz[0].get("ansible.builtin.uri") or healthz[0].get("uri")
    kodlar = args.get("status_code")
    kodlar = kodlar if isinstance(kodlar, list) else [kodlar]
    assert 200 in kodlar and 503 in kodlar, (
        f"[5] `status_code`: {kodlar} — dagit.sh healthz'i DÜŞÜRMEZ (yalnız basar). 503 "
        "('bayat nabız, süreç canlı') burada dağıtımı durdurursa [5a]/[5b]/[B] hiç koşmaz ve "
        "yeni kod canlıdayken beyan eski sha'da kalır.")
    for anahtar in ("until", "retries", "delay"):
        assert anahtar not in healthz[0], (
            f"[5] `{anahtar}` taşıyor — dagit.sh'ta tek atımlık bir RAPOR'dur, yeniden deneyen "
            "bir kapı değil")


def test_B14b_5c_kuru_kosumda_UYARI_gercek_kosumda_KAPI():
    """[5c] kuru koşumu DÜŞÜRMEZ ama sessiz de kalmaz; gerçek koşumda DURDURUR.

    ÖLÇÜLDÜ (inceleme K6, 2026-09-08): dagit.sh'ın kuru koşumu [5c]'yi HİÇ koşmuyordu (kuru
    koşum `exit 0` ile biter, [5c] bloğu dağıtımın SONUNDADIR) — playbook onu Play 1'e aldığı
    için kuru koşumda da ölçer. Bu bir kazançtır ama bedeli ödenmeden alınamaz: `ui/`
    düzenlenmiş ve `npm run build` henüz koşmamışken (UI turlarının normal ara hâli) kuru koşum
    Play 1'de düşerdi ve [1]/[1b]/[1c]/[F9]/[F10] — A1 hakkında SORULAN HER ŞEY — hiç ölçülmezdi.
    Bu yüzden kuru koşumda BAYAT artefakt bir UYARIdır; gerçek koşumda dagit.sh gibi DURDURUR."""
    olcum = [g for g in _tum_gorevler()
             if _birincil_etiket(g) == "5c" and "failed_when" in g]
    assert len(olcum) == 1, f"[5c] `failed_when` taşıyan tek görev bekleniyordu, {len(olcum)} var"
    kosul = str(olcum[0]["failed_when"])
    assert "not ansible_check_mode" in kosul, (
        f"[5c] `failed_when`: {kosul!r} — kuru koşumda BAYAT artefakt Play 1'i düşürür ve A1 "
        "hakkında hiçbir kapı ölçülmez (dagit.sh'ın kuru koşumu [5c]'yi hiç koşmuyordu)")
    uyari = [g for g in _tum_gorevler()
             if _birincil_etiket(g) == "5c"
             and re.search(r"(^|\s|;)ansible_check_mode\s*($|;)", _when_metni(g))]
    assert uyari, (
        "[5c] kuru koşumda BAYAT artefaktı ADIYLA basan bir görev YOK — kuru koşum sessizce "
        "geçerdi ve o sessizlik 'taze' diye okunurdu (bedel yasası)")


# =================================================================================================
# B15 — [5a]/[5b] betikleri `ubuntu` olarak koşar (en az yetki, dagit.sh ile birebir)
# =================================================================================================
def test_B15_script_gorevleri_become_false():
    """Her `ansible.builtin.script` görevi `become: false` taşır.

    dagit.sh ikisini de `ssh ubuntu@…` ile, yani `ubuntu` olarak koşturuyordu (`sudo` YOK).
    Play 2 `become: true` olduğu için beyansız bir `script` ROOT koşar: `[5a]` betiği
    `.dash.env`i okur (ubuntu'nun 0600 dosyası) ve `[5b]` `/proc/<pid>` gezer — ikisi de root
    yetkisi GEREKTİRMEZ. En az yetki bir tercih değil, dagit.sh ile birebirliğin parçasıdır."""
    ihlal = [g.get("name") for g in _tum_gorevler()
             if _modul_args(g, _SCRIPT_ANAHTARLARI) is not None and g.get("become") is not False]
    assert not ihlal, (
        f"`script` görevleri ROOT koşuyor (`become: false` YOK): {ihlal} — dagit.sh bunları "
        "`ubuntu` olarak koşturuyordu")


# =================================================================================================
# B16 — check-mode'da CANLIYA yazan görev YOK (A5d'nin playbook karşılığı)
# =================================================================================================
#: Canlıyı DEĞİŞTİREN komut fiilleri. `check_mode: false` ile işaretlenmiş bir görev kuru
#: koşumda GERÇEKTEN koşar; bu listedeki bir fiili taşıyorsa kuru koşum bir DAĞITIMDIR.
_YAZAN_KOMUT = re.compile(r"(^|\s|/)(tee|mv|cp|rm|install|chmod|chown|ln)\s|uv\s+sync|"
                          r"systemctl\s+(?:--\S+\s+)*(stop|start|restart|kill|daemon-reload)")


def test_B16_check_modda_canliya_yazan_gorev_YOK():
    """Play 2'nin her `command`/`shell`/`script` görevi check-mode duruşunu BEYAN eder.

    `tests/test_ansible_dagit_v452.py::test_A5d_dagit_KURU_KOSUMDA_yazan_cagri_YOK` dagit.sh
    için aynı iddiayı ölçüyor ve Task 3'te dagit.sh gövdesi silinince ÖLECEK; bu çivi onun
    playbook karşılığıdır (kapı listesi düşmez — çivi listesi de düşmez).

    KURAL İKİ DALLI ve beyan ZORUNLU: bir komut görevi ya `check_mode: false` taşır (kuru
    koşumda da koşar → SALT OKUMA olmak zorundadır) ya da `when: not ansible_check_mode`
    taşır (kuru koşumda atlanır). İkisini de taşımayan bir görev kuru koşumda sessizce
    atlanır ve o sessizlik 'ölçüldü' diye okunur. Yazan fiil taşıyan bir görev `check_mode:
    false` ile İŞARETLENEMEZ: `--check` o hâlde canlıya yazardı."""
    ihlal: list[str] = []
    for gorev in _play_gorevleri(_play2()):
        if (_modul_args(gorev, _KOMUT_ANAHTARLARI) is None
                and _modul_args(gorev, _SCRIPT_ANAHTARLARI) is None):
            continue
        ad = gorev.get("name")
        kuru_kosar = gorev.get("check_mode") is False
        atlanir = "not ansible_check_mode" in _when_metni(gorev)
        metin = _komut_metni(gorev)
        yazan = bool(_YAZAN_KOMUT.search(metin))
        if not kuru_kosar and not atlanir:
            ihlal.append(f"{ad!r}: ne `check_mode: false` ne `not ansible_check_mode` — "
                         "kuru koşumdaki duruşu BEYANSIZ")
        if yazan and kuru_kosar:
            ihlal.append(f"{ad!r}: YAZAN komut (`{metin.strip()[:60]}…`) `check_mode: false` "
                         "ile işaretli — `--check` canlıya YAZARDI")
        if yazan and not atlanir:
            ihlal.append(f"{ad!r}: YAZAN komut `when: not ansible_check_mode` taşımıyor")
    assert not ihlal, "check-mode duruşu ihlalleri:\n" + "\n".join(ihlal)


# =================================================================================================
# B17 — [1c] kapısı: yönerge farkı DÜŞÜRÜR, kadans birimi 'hiç kurulmamış' RAPORdur
# =================================================================================================
#: (`birim_ayrik`, `birim_kurulmamis`) → kapı GEÇER mi. Kaynak: dagit.sh [1c] (yalnız RAPOR) +
#: plan Architecture ("burada ASSERT … DUR") + A0 rolünün kadans kapısı (`brifing_devri`).
B17_SENARYOLAR = (
    ([], [], True),
    (["meridian.service"], [], False),                    # yönerge farkı → DUR
    (["meridian-brifing.service"], [], False),            # kadans birimi de AYRIKSA → DUR
    ([], ["meridian.service"], False),                    # kadans DIŞI kurulu değil → DUR
    ([], ["meridian-brifing.service"], True),             # kadans kapalı olabilir → RAPOR
    ([], ["meridian-bekci.service", "meridian-karne.service"], True),
    ([], ["meridian-brifing.service", "meridian.service"], False),
)


@pytest.mark.parametrize("ayrik,kurulmamis,gecmeli", B17_SENARYOLAR)
def test_B17_1c_kapisi_kadans_ve_yonerge_farki(ayrik, kurulmamis, gecmeli):
    """[1c] DÜŞÜREN bir kapıdır (plan kararı) ama kadans birimlerinin YOKLUĞU onu düşürmez.

    A0 rolünün kadans kapısı (`brifing_devri: false`) brifing/bekçi/karne birimlerini BİLEREK
    kurmaz; [1c] "hepsi /etc'de olacak" derse ilk kuru koşum kilitlenir ve bastığı reçete
    (`site.yml`) o birimleri kuramaz — kapı, çaresi kendisinde olmayan bir kapıya dönüşürdü.
    Ayrım: YÖNERGE FARKI (sessiz etkisizlik, 2026-08-14 vakası) DÜŞÜRÜR; kadans biriminin hiç
    kurulmamış olması RAPORdur."""
    kapilar = [g for g in _tum_gorevler()
               if "1c" in _etiketler(g) and isinstance(_assert_args(g), dict)]
    assert len(kapilar) == 1, f"[1c] `assert` kapısı tek olmalı, {len(kapilar)} var"
    kapi = _assert_args(kapilar[0])
    degiskenler = dict(_degiskenler())
    degiskenler.update({"birim_ayrik": ayrik, "birim_kurulmamis": kurulmamis})
    assert _when_degerlendir(kapi["that"], degiskenler) is gecmeli, (
        f"[1c] kapısı yanlış yön: ayrık={ayrik} kurulmamış={kurulmamis} → "
        f"beklenen geçer={gecmeli} (`that`: {kapi['that']!r})")


def test_B17b_1c_fail_msg_YONERGE_farkini_ve_kadans_recetesini_TASIR():
    """[1c] düştüğünde operatörün elinde HANGİ yönergenin ayrık olduğu vardır.

    BEDEL YASASI (inceleme K5): dagit.sh ayrık birimde `diff | grep '^[<>]'` ile SATIRI
    basıyordu ve DURDURMUYORDU; playbook kapıyı sertleştirip çıktıyı kısarsa operatör en sert
    anda en az bilgiyle kalır (kazanç ölçüldü, kayıp ölçülmedi). İki taraf zaten `slurp`
    edilmiş durumda — ek ölçüm maliyeti sıfırdır. Kadans kolu için reçete kaçışı ADIYLA
    yazılır: `site.yml` tek başına yeterli değildir, `brifing_devri` gerekir."""
    kapi = _assert_args(next(g for g in _tum_gorevler()
                             if "1c" in _etiketler(g) and isinstance(_assert_args(g), dict)))
    mesaj = str(kapi.get("fail_msg", ""))
    assert "birim_ayrik_fark" in mesaj, (
        "[1c] `fail_msg` yalnız birim ADLARINI basıyor — yönerge farkı (`birim_ayrik_fark`) yok")
    assert "site.yml" in mesaj and "brifing_devri" in mesaj, (
        "[1c] reçetesi kadans kaçışını ADIYLA yazmıyor (`site.yml … -e brifing_devri=true`)")
    fark = [g for g in _tum_gorevler()
            if "1c" in _etiketler(g)
            and "birim_ayrik_fark" in yaml.safe_dump(
                (g.get("ansible.builtin.set_fact") or g.get("set_fact") or {}),
                allow_unicode=True)]
    assert fark, "[1c] `birim_ayrik_fark`ı kuran `set_fact` yok — fail_msg tanımsız değer basardı"


# =================================================================================================
# B18 — README "BEYANLI farklar" listesi ↔ playbook `# BEYANLI-FARK n` şerhleri (İKİ YÖNLÜ)
# =================================================================================================
#: README'de SAYI VEREREK sunulan bir liste eksik olduğunda okuyucu "başka fark yok" hükmünü
#: çıkarır — tur-1 ve tur-2 incelemelerinin aynı bulgusu (tek-kaynak + bedel yasası). Liste ile
#: davranış arasındaki bağ bu yüzden ölçülür: her madde playbook'ta `# BEYANLI-FARK n` şerhiyle
#: DURDUĞU YERİ gösterir, her şerh de README'de bir maddeye karşılık gelir. Tek yönlü bir kıyas
#: yetmez: yalnız "madde → şerh" ölçülseydi playbook'a şerhsiz bir sapma eklemek serbest kalırdı;
#: yalnız "şerh → madde" ölçülseydi listeden madde silmek serbest kalırdı.
BEYANLI_FARK_BASLIK = "## `dagit.sh`a göre BEYANLI farklar"
_BEYANLI_FARK_ISARET = re.compile(r"^\s*#\s*BEYANLI-FARK\s+(\d+)\s*$", re.M)


def _readme_beyanli_fark_bolumu() -> str:
    metin = ANSIBLE_README.read_text(encoding="utf-8")
    bas = metin.find(BEYANLI_FARK_BASLIK)
    assert bas >= 0, f"README'de {BEYANLI_FARK_BASLIK!r} bölümü YOK — çivi bayatlamış"
    son = metin.find("\n## ", bas + 1)
    return metin[bas:son if son > 0 else len(metin)]


def _readme_madde_numaralari() -> list[int]:
    return [int(n) for n in re.findall(r"^(\d+)\.\s", _readme_beyanli_fark_bolumu(), re.M)]


def test_B18_beyanli_farklar_README_maddeleri_playbook_SERHLERIYLE_ESIT():
    """README'nin numaralı "BEYANLI farklar" listesi ile playbook'un şerhleri BİRE BİR.

    ÖLÇÜLDÜ (yeniden inceleme Y2, 2026-09-08): liste 10 maddeye çıkmıştı ama üç sapma dışarıda
    kalmıştı (`[F9]` ikinci özetinin düşmesi · `[F9]` diff gövdesinin basılmaması · `[1b]`
    `mktemp -d` dizininin hiç silinmemesi). İlk ve üçüncüsü playbook'ta KAPATILDI (dagit.sh ile
    birebirlik), ikincisi bilinçli bir sapmadır ve artık listede. Bu çivi listenin bir daha
    sessizce ayrışmamasını sağlar."""
    maddeler = _readme_madde_numaralari()
    assert maddeler, "README 'BEYANLI farklar' bölümünde numaralı madde YOK"
    assert maddeler == list(range(1, len(maddeler) + 1)), (
        f"README madde numaraları 1..N ARDIŞIK değil: {maddeler} — şerh eşleşmesi kimliğe bağlı")

    isaretler = [int(n) for n in _BEYANLI_FARK_ISARET.findall(
        DAGIT_YML.read_text(encoding="utf-8"))]
    tekrar = sorted({n for n in isaretler if isaretler.count(n) > 1})
    assert not tekrar, f"playbook'ta TEKRARLAYAN `# BEYANLI-FARK` şerhi: {tekrar}"
    eksik = sorted(set(maddeler) - set(isaretler))
    fazla = sorted(set(isaretler) - set(maddeler))
    assert not eksik, (
        f"README'de olup playbook'ta ŞERHSİZ maddeler: {eksik} — madde hangi görevde "
        "gerçekleştiğini göstermiyor; okuyucu davranışı dosyada bulamaz")
    assert not fazla, (
        f"playbook'ta şerhli olup README listesinde OLMAYAN sapmalar: {fazla} — sayı vererek "
        "sunulan liste eksikse okuyucu 'başka fark yok' hükmünü çıkarır")


def test_B18b_dagit_sh_ile_kapanan_IKI_SAPMA_yerinde():
    """(a) `[F9]` özeti dağıtımın SONUNDA tekrarlanır; (b) `[1b]` geçici dizini SİLİNİR.

    (a) dagit.sh özeti iki kez basar ve nedenini kendi metninde yazar ("Dağıtım ENGELLENMEDİ —
    özet sonda tekrarlanır"): uzun bir dağıtım çıktısında ilk özet kaydırılıp gider ve
    raporlanan ama görülmeyen sürüklenme, hiç raporlanmamış gibidir (bedel yasası). Tekrar
    dağıtım-sonu görevidir: kuru koşumda BASILMAZ (dagit.sh kuru koşumu `exit 0` ile daha
    önce biter) ve atlandığını ADIYLA söyler (B14 sözleşmesi).

    (b) dagit.sh `trap 'rm -rf "$STATE_TMP"' EXIT` ile temizler; playbook'un `tempfile`ı
    `check_mode: false` taşır, yani KURU KOŞUMDA DA gerçekten açılır. Silinmeseydi kontrolcünün
    `/tmp`inde canlı `goal.yaml`/`bounds.yaml` kopyaları her koşumda birikirdi."""
    f9_ozetleri = [g for g in _tum_gorevler()
                   if _birincil_etiket(g) == "F9"
                   and (g.get("ansible.builtin.debug") or g.get("debug")) is not None
                   and "Özet" in str(g.get("name"))]
    assert len(f9_ozetleri) == 2, (
        f"[F9] özeti {len(f9_ozetleri)} kez basılıyor, 2 bekleniyordu (kapı tarafı + dağıtım "
        "sonu tekrarı — dagit.sh ikisini de basar)")
    play2 = _play_gorevleri(_play2())
    adlar = [str(g.get("name")) for g in play2]
    tekrar_sirasi = adlar.index(str(f9_ozetleri[1].get("name")))
    son_5b = max(i for i, g in enumerate(play2) if _birincil_etiket(g) == "5b")
    assert tekrar_sirasi > son_5b, (
        "[F9] tekrar özeti [5b]'den ÖNCE — dagit.sh'ta dağıtımın SONUNDA, 'DAĞITIM TAMAM'ı "
        "okuyan gözün kaçırmayacağı yerdedir")
    tekrar_kosul = _when_metni(f9_ozetleri[1])
    for alan in ("f9_ayrik", "f9_repo_yok", "f9_canli_yok"):
        assert alan in tekrar_kosul, (
            f"[F9] tekrar özeti `{alan}` koşulunu taşımıyor — dagit.sh özeti YALNIZ bulgu "
            f"varken basar ({tekrar_kosul!r})")

    silen = [g for g in _tum_gorevler()
             if isinstance(g.get("ansible.builtin.file") or g.get("file"), dict)
             and (g.get("ansible.builtin.file") or g.get("file")).get("state") == "absent"
             and "state_tmp" in str((g.get("ansible.builtin.file") or g.get("file")).get("path"))]
    assert len(silen) == 1, (
        f"[1b] `mktemp -d` dizinini SİLEN görev {len(silen)} tane (1 bekleniyordu) — dagit.sh "
        "`trap rm -rf` ile temizliyordu; kontrolcünün /tmp'inde canlı state kopyaları birikir")
    temizlik = silen[0]
    assert temizlik.get("delegate_to") == "localhost" and temizlik.get("become") is False, (
        "[1b] temizlik görevi kontrolcüde ve `become: false` ile koşmalı (dizin KONTROLCÜDE)")
    assert temizlik.get("check_mode") is False, (
        "[1b] temizlik `check_mode: false` taşımıyor — dizin `check_mode: false` ile AÇILDIĞI "
        "için kuru koşumda gerçekten var olur ve silinmeden kalırdı")
    always_adlari = {str(g.get("name")) for play in _dagit_yml()
                     for kok in _play_gorevleri(play)
                     for g in _gorev_listesi(kok.get("always"))}
    assert str(temizlik.get("name")) in always_adlari, (
        "[1b] temizlik bir `always:` bloğunda DEĞİL — hüküm süreci düştüğünde (rescue) dizin "
        "kalırdı; dagit.sh'ın `trap … EXIT`i her yolda temizler")


# =================================================================================================
# B19 — [B] okuma/kıyas kolu, beyan YAZILMADIĞINDA bir ARIZAYA dönüşmez
# =================================================================================================
def test_B19_B_slurp_ve_kiyas_beyan_metni_is_string_KOSULLU():
    """`slurp` ve bayt kıyası, `tee`/`mv` ile AYNI koşulu taşır (`beyan_metni is string`).

    ÖLÇÜLDÜ (yeniden inceleme Y6, 2026-09-08, sentetik play): `| string` düşerse yazım kolu
    atlanır ve durum ADIYLA basılır (Yasa 6 sağlanır, sessiz eksik beyan YOK) — ama hemen
    ardından gelen `slurp` hedef dosya YOKSA `file not found` ile DÜŞER. A1'de dosya bugün var
    (dagit.sh yazıyor) ve kıyas doğru şekilde "YAZILAMADI" der; TAZE bir hostta ise yüksek sesle
    raporlanmış bir kol bir ARIZAYA dönüşürdü. Koşul üç görevde de aynı olmalı."""
    b_gorevleri = [g for g in _tum_gorevler() if _birincil_etiket(g) == "B"]
    slurp = [g for g in b_gorevleri
             if isinstance(g.get("ansible.builtin.slurp") or g.get("slurp"), dict)]
    assert len(slurp) == 1, f"[B] `slurp` görevi tek olmalı, {len(slurp)} var"
    kiyas = [g for g in b_gorevleri
             if "beyan_canli" in str((g.get("ansible.builtin.debug") or g.get("debug") or {}))]
    assert len(kiyas) == 1, f"[B] bayt kıyası görevi tek olmalı, {len(kiyas)} var"
    for gorev in slurp + kiyas:
        assert "beyan_metni is string" in _when_maddeleri(gorev), (
            f"{gorev.get('name')!r}: `beyan_metni is string` koşulu YOK — beyan yazılmadığında "
            "(yerel-tip dönüşümü) bu görev taze bir hostta 'file not found' ile DÜŞERDİ")
