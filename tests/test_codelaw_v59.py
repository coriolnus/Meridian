"""test_codelaw_v59.py — İKİ STATİK YASANIN testleri (2026-07-21).

Bu testlerin işi tek cümle: **bir sonraki sessiz yutma ve bir sonraki tüketicisiz artefakt, canlıda
değil BURADA yakalansın.** 2026-07-21'de on üç hata çıktı ve hiçbiri istisna fırlatmadı; 800 test
de yeşildi. Yeşil testin bir şey KANITLADIĞINI iddia edebilmesi için tarayıcının kendisinin
çalıştığını göstermek gerekir — bu yüzden her sıfır iddiasının yanında bir POZİTİF KONTROL var:
tarayıcıya bilerek bozuk bir kaynak verilir ve yakalaması beklenir. Aksi hâlde "sıfır ihlal",
"tarayıcı hiçbir şey görmüyor" ile aynı şey olurdu.
"""
from __future__ import annotations

import textwrap

from meridian import codelaw


# ---------------------------------------------------------------------------
# (4) SESSİZ-YUTMA YASAĞI
# ---------------------------------------------------------------------------

def test_scanner_pozitif_kontrol_ciplak_pass_yakalanir():
    """ÖNCE tarayıcının çalıştığını kanıtla: çıplak `except: pass` yakalanmalı."""
    src = textwrap.dedent("""
        def f(p):
            try:
                return int(open(p).read())
            except Exception:
                pass
            return 0
    """)
    hits = codelaw.scan_source(src, "sentetik.py")
    assert len(hits) == 1, f"çıplak except:pass yakalanamadı: {hits}"
    assert hits[0]["function"] == "f"
    assert hits[0]["marker"] is None


def test_scanner_sinyal_ureten_yakalayiciyi_isaretlemez():
    """Yanlış pozitif olmasın: yeniden fırlatan, obs'a yazan ya da istisnayı KULLANAN handler temizdir."""
    src = textwrap.dedent("""
        from . import obs

        def a(p):
            try:
                return int(p)
            except ValueError:
                raise

        def b(p):
            try:
                return int(p)
            except ValueError as e:
                obs.warn("kotu_sayi", error=str(e))
                return 0

        def c(p, errors):
            try:
                return int(p)
            except ValueError as e:
                errors.append(str(e))     # hata bilgisi bir yere TAŞINIYOR
                return 0
    """)
    assert codelaw.scan_source(src, "sentetik.py") == []


def test_sessiz_yedek_atama_da_ihlaldir():
    """`except: x = None` istisna fırlatmaz ama bilgiyi yok eder — 2026-07-21'in tam deseni."""
    src = textwrap.dedent("""
        def f(p):
            try:
                v = int(p)
            except Exception:
                v = None
            return v
    """)
    assert len(codelaw.scan_source(src, "sentetik.py")) == 1


def test_isaret_kacis_yolu_onurlandirilir_ama_gerekcesiz_isaret_sayilmaz():
    """Kaçış yolu AÇIK bir karar olmalı: gerekçesiz `# sessiz-yutma:` kaçış yolu DEĞİLDİR."""
    gerekceli = textwrap.dedent("""
        def f(p):
            try:
                return int(p)
            except Exception:  # sessiz-yutma: telemetri yolu, karara girmez
                return 0
    """)
    assert codelaw.scan_source(gerekceli, "s.py")[0]["marker"] is not None
    assert codelaw.silent_handlers.__doc__          # (API yüzeyi duruyor)

    ustteki_satirda = textwrap.dedent("""
        def f(p):
            try:
                return int(p)
            # sessiz-yutma: üstteki satırda da geçerli — ast yorumu düşürür, kaynak metni okunur
            except Exception:
                return 0
    """)
    assert codelaw.scan_source(ustteki_satirda, "s.py")[0]["marker"] is not None

    for bos in ("# sessiz-yutma:", "# sessiz-yutma: -", "# sessiz-yutma:   "):
        src = textwrap.dedent(f"""
            def f(p):
                try:
                    return int(p)
                except Exception:  {bos}
                    return 0
        """)
        hit = codelaw.scan_source(src, "s.py")[0]
        assert hit["marker"] is None, f"gerekçesiz işaret kaçış yolu sayıldı: {bos!r}"
        assert hit["bare_marker"] is True


def test_sifir_isaretsiz_sessiz_yakalayici_duzenlenebilir_yuzeyde():
    """ASIL YASA: düzenlenebilir her modülde işaretsiz sessiz yakalayıcı SIFIR olmalı.

    Yeni bir `except Exception: pass` eklendiği anda bu test kırılır — gerekçeyi yazmak ya da
    obs'a bir sinyal koymak zorunlu hâle gelir. Başka iş kollarına ait dosyalar (bu turda
    düzenlenemeyenler) ayrıca listelenir; allowlist değil, BEYAN — dosya listeden çıkarsa
    ihlalleri anında buraya düşer."""
    ihlaller = codelaw.silent_handlers()
    bizim = [h for h in ihlaller
             if h["file"].rsplit("/", 1)[-1] not in codelaw.OTHER_TRACK_FILES]
    assert bizim == [], "işaretsiz sessiz yakalayıcı: " + "; ".join(
        f"{h['file']}:{h['line']} ({h['function']})" for h in bizim)


def test_baska_is_kolu_ihlalleri_de_kapatildi():
    """Bu test, paralel iş kollarında bırakılan 21 ihlal 2026-07-22'de kapatıldığında yön değiştirdi:
    önce "bulgular sessizce silinmesin" diye VARLIKLARINI kilitliyordu, artık KAPALI kalmalarını
    kilitliyor. En tehlikelileri dedektörlerin kendi içindeydi — okunamayan bir defteri "0 satır"
    diye raporlayan `_n_jsonl`, sızıntıyı fark ettirmeden ambargoyu kapatan `_embargoed_start`."""
    kalan = codelaw.silent_handlers()
    assert not kalan, f"yeni sessiz yutma belirdi: {[(h['file'], h['line']) for h in kalan]}"
    # tarayıcının körleşmediğini KANITLA: sentetik bir ihlal hâlâ yakalanıyor mu?
    assert codelaw.scan_source("try:\n    x = 1\nexcept Exception:\n    pass\n")


def test_isaretli_yakalayicilarin_hepsinin_gercek_bir_gerekcesi_var():
    """İşaret koymak yetmez; her işaretin okunabilir bir gerekçesi olmalı (yoksa `pass` ile eşdeğer)."""
    for h in codelaw.annotated_handlers():
        assert h["marker"] and len(h["marker"]) >= 20, f"içi boş gerekçe: {h['file']}:{h['line']}"


# ---------------------------------------------------------------------------
# (6) ARTEFAKT TÜKETİM GRAFİĞİ
# ---------------------------------------------------------------------------

def test_artifact_graph_pozitif_kontrol_okunmayan_artefakti_bulur(tmp_path):
    """Tarayıcı GERÇEKTEN tüketicisiz artefaktı buluyor mu? Sentetik iki modülle kanıtla."""
    (tmp_path / "yazar.py").write_text(
        "from . import store\n"
        "RAPOR = 'yalniz_rapor.json'\n"
        "def f():\n"
        "    store.write_json(RAPOR, {'x': 1})\n"
        "    store.write_json('okunan.json', {'y': 2})\n")
    (tmp_path / "okuyucu.py").write_text(
        "from . import store\n"
        "def g():\n"
        "    return store.read_json('okunan.json', {})\n")

    g = codelaw.artifact_graph(str(tmp_path))
    assert "yalniz_rapor.json" in g["unread"], "modül düzeyi SABİT ad çözülemedi ya da unread kaçtı"
    assert g["artifacts"]["yalniz_rapor.json"]["writers"] == ["yazar.py"]
    assert "okunan.json" not in g["unread"], "başka modül okuyor — unread sayılmamalı"
    assert "yalniz_rapor.json" in g["violations"], "beyan edilmemiş unread ihlal olmalı"


def test_her_artefakt_ya_okunuyor_ya_beyan_edilmis_bir_lagimdir():
    """ASIL YASA: kimsenin okumadığı bir artefakt, üretilmemiş artefakttan ayırt edilemez.
    Yeni bir dosya yazılıp hiç okunmazsa burada patlar — beyan etmek ZORUNLU olur."""
    g = codelaw.artifact_graph()
    assert g["violations"] == [], (
        "yazılıyor ama hiçbir modül okumuyor ve DECLARED_SINKS'te beyan edilmemiş: "
        + ", ".join(g["violations"]))


def test_beyan_edilen_lagimlarin_hepsi_hala_lagim():
    """Beyan bayatlamasın: bir artefakta gerçek bir tüketici eklendiyse beyanı kaldırılmalı,
    yoksa liste zamanla 'kimsenin bakmadığı muafiyet çöplüğüne' döner."""
    g = codelaw.artifact_graph()
    assert g["stale_sinks"] == [], "artık okunuyor, beyanı kaldır: " + ", ".join(g["stale_sinks"])


def test_her_beyanin_turkce_bir_gerekcesi_var():
    for name, gerekce in codelaw.DECLARED_SINKS.items():
        assert len(gerekce) >= 30, f"{name}: gerekçe bir cümle bile değil"


def test_pano_tuketicisi_iddialari_app_js_ile_dogrulanir():
    """'Panoda gösteriliyor' gerekçesi KANITLANABİLİR olmalı — app.js salt okunur taranır.
    (2026-07-21'in dersi: rapor üretiliyordu, API servis ediyordu, panoda paneli YOKTU.)"""
    for terim in ("approvals", "skill_recommendations", "sprint"):
        assert codelaw.dashboard_mentions(terim), \
            f"pano tüketicisi iddiası doğrulanamadı: app.js içinde '{terim}' geçmiyor"


# ---------------------------------------------------------------------------
# TARAYICILARIN KENDİ SINIRLARI HAKKINDA DÜRÜSTLÜĞÜ
# ---------------------------------------------------------------------------

def test_dinamik_adli_artefaktlar_unresolved_olarak_raporlanir(tmp_path):
    """Değişkenle çağrılan bir ad ÇÖZÜLEMEZ. Onu sessizce atlamak, tam da bu modülün yasakladığı
    şeydir: tarayıcı kendi körlüğünü gizleyemez, `unresolved` listesine yazar."""
    (tmp_path / "dinamik.py").write_text(
        "from . import store\n"
        "def f(ad, i):\n"
        "    store.write_json(ad, {})\n"
        "    store.read_json(f'parca_{i}.json', {})\n")
    g = codelaw.artifact_graph(str(tmp_path))
    assert len(g["unresolved"]) == 2, g["unresolved"]
    roller = sorted(u["role"] for u in g["unresolved"])
    assert roller == ["reader", "writer"]
    assert all(u["line"] > 0 and u["file"].endswith("dinamik.py") for u in g["unresolved"])
    assert g["artifacts"] == {}, "çözülemeyen ad artefakt gibi sayılmamalı"


def test_canli_taramada_da_cozulemeyenler_gizlenmiyor():
    """Gerçek kod tabanında da çözülemeyen çağrılar VAR (ör. ledger adı parametre olarak gelir).
    Sayının sıfır olmaması bir kusur değil; RAPOR EDİLMEMESİ kusur olurdu."""
    g = codelaw.artifact_graph()
    assert isinstance(g["unresolved"], list)
    for u in g["unresolved"]:
        assert {"file", "line", "call", "role", "arg"} <= set(u)


def test_ayristirilamayan_dosya_sessizce_atlanmaz(tmp_path):
    """Sözdizimi bozuk bir modül taranamaz. Eskiden `except SyntaxError: continue` idi — yani
    dedektör, tam da var oluş sebebi olan hatayı yapıyordu. Artık körlük UNSCANNED'a yazılır."""
    (tmp_path / "bozuk.py").write_text("def f(:\n    pass\n")
    codelaw.UNSCANNED.clear()
    try:
        assert codelaw.silent_handlers(str(tmp_path)) == []
        assert any(r["file"].endswith("bozuk.py") for r in codelaw.UNSCANNED), \
            "ayrıştırılamayan dosya sessizce atlandı — sıfır ihlal raporu vakumdur"
        codelaw.artifact_graph(str(tmp_path))
        assert any(r["phase"].startswith("artifact_graph") for r in codelaw.UNSCANNED)
    finally:
        codelaw.UNSCANNED.clear()


def test_canli_kod_tabaninda_taranamayan_dosya_yok():
    codelaw.UNSCANNED.clear()
    codelaw.silent_handlers()
    codelaw.artifact_graph()
    assert codelaw.UNSCANNED == [], f"taranamayan modül: {codelaw.UNSCANNED}"


def test_report_iki_yasayi_birlikte_ozetler():
    r = codelaw.report()
    assert set(r) >= {"silent_handlers", "annotated_handlers", "artifacts",
                      "unread", "artifact_violations", "unresolved_artifact_calls",
                      "unscanned", "ok"}
    assert r["artifacts"] > 30 and r["annotated_handlers"] > 0
