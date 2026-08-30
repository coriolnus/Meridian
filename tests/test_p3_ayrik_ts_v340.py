"""test_p3_ayrik_ts_v340.py — P-3 kararının (AYRIK, ts anahtarı, 2026-08-31) kapanış çivileri.

Operatör kararı `ai-trading-85` oturumunda verildi, oturumlar-arası aktarımla Rol-1 işledi.
Bu dosya kararın KENDİSİNİ değil, kararın depoya İŞLENMİŞLİĞİNİ çiviler: işaretçi yük taşır
hâle geldi (görev metni reçeteyi karttan okur — tek-kaynak), ve yük taşıyan işaretçi çivisiz
kalamaz.
"""
from __future__ import annotations

import pathlib
import re

import pytest

KOK = pathlib.Path(__file__).resolve().parent.parent
KART = KOK / "research/cards/EDG-2026-042-gercek-friksiyon-tahmini.yaml"
EXE009 = KOK / "research/cards/EXE-2026-009-pencere-kaydirma.yaml"
RECETE = KOK / "research/olcumler/edg042_recete_ayrik_2026-08-31"


def test_ISARETCI_YUK_TASIR_hedefi_var_ve_ts_cekiyor():
    """Kartın GÜNCEL DONUK REÇETE İŞARETÇİSİ artık YÜK TAŞIYOR: haftalık görev reçeteyi
    ondan okur (görev metni 2026-08-31'de dizin/sha taşımayı bıraktı — iki kez bayatlamıştı).
    Yük taşıyan işaretçi iki şeyi garanti etmeli: hedef dizin VAR, ve reçetesi `ts` alanını
    GERÇEKTEN çekiyor — yoksa Cumartesi koşumu ayrık kolları üretemeyen bir reçeteye gider
    ve tur sessizce anlamsızlaşır (yan oturumun atomiklik uyarısı, 2026-08-31)."""
    kart = KART.read_text(encoding="utf-8")
    m = re.search(r"GÜNCEL DONUK REÇETE İŞARETÇİSİ[^\n]*?(research/olcumler/[A-Za-z0-9_./-]+)",
                  kart[kart.index("p3_karar_ayrik_ts_2026_08_31"):])
    assert m, "p3 bloğu GÜNCEL DONUK REÇETE İŞARETÇİSİ satırı taşımıyor — görev reçeteyi bulamaz"
    hedef = KOK / m.group(1).rstrip("/")
    assert hedef.is_dir(), f"işaretçinin hedefi YOK: {m.group(1)} — Cumartesi koşumu kör"
    cek = (hedef / "canli_cek.py").read_text(encoding="utf-8")
    assert re.search(r"['\"]ts['\"]", cek), (
        "işaretçinin gösterdiği reçetenin canli_cek.py'si `ts` alanını çekmiyor — AYRIK karar "
        "bu alana dayanır; reçete-işaretçi ayrışması tam da yasaklanan sınıf")


def test_P3_BLOGU_ZORUNLU_OGELERI_TASIR():
    """Kararın dört taşıyıcı ögesi kartta ADIYLA durmalı: tek-sınır beyanı · kalici_taban
    alanı (damga biçimi EDG-037 DEĞİŞMEDİ) · K disiplini (bölünme K'yı çarpmaz) · kabul
    edilen bedel. Herhangi biri düşerse: sınırsız reçete genişletme / 'yakında dolacak'
    yanlış okuması / bir sonraki denetimin K 3→4 diye kill'e sokması / sessiz bedel."""
    kart = KART.read_text(encoding="utf-8")
    assert "p3_karar_ayrik_ts_2026_08_31" in kart, "p3 karar bloğu kartta YOK"
    blok = kart[kart.index("p3_karar_ayrik_ts_2026_08_31"):]
    for oge, neden in [
        ("2026-08-23T14:53:43Z", "sınır sabiti (canlı barclock mtime) yazılı değil"),
        ("kalici_taban", "giris_once'un donukluk alanı ilan edilmemiş — '< eşik' bekleyiş okunur"),
        ("K TOPLAM = 3", "K disiplini cümlesi yok — sonraki denetim bölünmeyi K 3→4 okur"),
        ("KABUL EDİLEN BEDEL", "bedel beyanı yok — hız/saflık takası sessizleşir"),
        ("ARA İŞARET", "ara-işaret-yok KARARI kayıtsız — altı hafta sonra biri sayıya bakıp ekler"),
    ]:
        assert oge in blok, f"p3 bloğunda eksik öge: {oge!r} — {neden}"


def test_EXE009_AYRISMA_BEYANI_ISARETCIYLE():
    """P-2 etkileşimi: iki kart aynı olguyu iki anahtarla böler (EDG-042 `ts`, EXE-009 damga)
    ve 13 damgasız satırda AYRIŞIRLAR. Beyan TEK yerde yaşar (EDG-042 p3 bloğu); EXE-009
    yalnız İŞARET eder — aynı beyanı iki kez yazmak EQUIVALENT_TRUTHS tuzağının kendisidir
    (yan oturumun uyarısı, kabul edildi 2026-08-31)."""
    exe = EXE009.read_text(encoding="utf-8")
    assert "p3_karar_ayrik_ts_2026_08_31" in exe, (
        "EXE-009 ayrışma beyanına işaret etmiyor — iki kart aynı olguya iki farklı sayı verir "
        "ve bunu kimse görmez")
    i = exe.index("p3_karar_ayrik_ts_2026_08_31")
    assert "pencere" in exe[max(0, i-600):i+600].lower(), (
        "işaretçi bloğu kendi anahtarının (pencere damgası) bilinçli olduğunu söylemiyor")


def test_KARAR_BELGESI_RAFA_GIRDI_ve_HAZIRLIGI_KAPATIR():
    """Karar verilmeden raf HAZIRLIK- taşıyordu (yan oturumun Yasa-6 refleksi); karar verilince
    gerçek KARAR-*.md doğar ve hazırlık belgesine işaret eder — raf, verilmiş kararla
    hazırlığı ayırt eder."""
    karar = KOK / "docs/KARAR-P3-K1-AYRIK-TS-2026-08-31.md"
    assert karar.is_file(), "KARAR belgesi yok — raf hâlâ 'karar verilmedi' gösteriyor"
    icerik = karar.read_text(encoding="utf-8")
    assert "HAZIRLIK-P3-K1-KARISIK-ORNEKLEM-2026-08-30" in icerik, (
        "KARAR belgesi hazırlık belgesine işaret etmiyor — karar zinciri kopuk")
    assert "AYRIK" in icerik and "ts" in icerik


def test_GOREV_AYNASI_DEPODA_ve_YEREL_KOPYAYLA_OZDES():
    """Görev dosyası ~/.claude altında yaşar — versiyonsuz, cloud'a gitmez (CLAUDE.md harita
    satırının tarif ettiği tuzak). Depo aynası TEK KAYNAKTIR; yerel kopya ondan türer.
    Yerel kopya bu makinede varsa bayt-özdeş olmalı; yoksa (CI/cloud klonu) atlanır —
    ayrışma yalnız operatör makinesinde ölçülebilir ve orada ölçülür."""
    ayna = KOK / "deploy/claude-tasks/edg042-friksiyon-haftalik.SKILL.md"
    assert ayna.is_file(), "görev dosyasının depo aynası yok — ayrışma depoda görünmez kalır"
    yerel = pathlib.Path.home() / ".claude/scheduled-tasks/edg042-friksiyon-haftalik/SKILL.md"
    if not yerel.is_file():
        pytest.skip("yerel görev kopyası bu makinede yok — ayna karşılaştırması operatör makinesine özgü")
    assert ayna.read_bytes() == yerel.read_bytes(), (
        "depo aynası ile ~/.claude kopyası AYRIŞMIŞ — Cumartesi koşumu depoda görünmeyen bir "
        "metne göre çalışacak; aynayı güncelleyip yerel kopyayı ondan türet")
