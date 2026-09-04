"""tests/test_hayalet_suzgec_kablolu_v408.py — TSK-074 (2026-09-04): Ö-48 hayalet süzgeci
ÖNERİ katmanına KABLOLANDI (operatör kararı: "kabloya al" + canlı "süzülen hayalet öneri" sayacı;
2 hafta sonra sayaç okunur, sıfırsa geri alınır — EDG-071 KISMİ kanıt).

BAĞLAM. `docs/TASARIM-VIRGIN-KNOB-SUZGECI-2026-08-22.md` Seçenek A: bounds anahtar listesi
`hermes.virgin_knobs()` İÇİNDE `reflect.hayalet_suzgeci(bounds, kaynak="hermes.virgin_knobs")`
ile süzülür — tek boğaz, sıfır yeni import kenarı (`reflect` zaten hermes.py modül-düzeyinde
içe aktarılıyor). Süzgecin KENDİSİ (`reflect.hayalet_suzgeci`, `MOTOR_ZINCIRI`, fail-open) zaten
`tests/test_hayalet_dugme_v263.py`de çivili — BU dosya yalnız KABLOLAMANIN kendisini çiviler:
öneri katmanı (`virgin_knobs` → `propose_virgin_knob`) süzgeci GERÇEKTEN çağırıyor mu.

BU DOSYANIN ÇİVİLEDİĞİ SÖZLEŞME:
  N0 fikstür ölçülür (v263 N0 deseni): GHOST literali motor zincirinde YOK, REAL'in okuyucusu VAR.
  N1 `virgin_knobs()` hayaleti aday listesinden ÇIKARIR, kablolu düğmeyi TAŞIR.
  N2 `propose_virgin_knob()` hayalet AİLESİNİ hiçbir zaman önermez (öneri kablolu düğmeye gider).
  N3 süzüm SESSİZ DEĞİL: `reflect_hayalet_dugme_suzuldu` olayı `kaynak="hermes.virgin_knobs"`.
  N4 CANLI SAYAÇ (D2, YASA 6 okuyucusu): `analytics.learning_scorecard()["hayalet_suzulen_n"]`
     — events.jsonl'deki GERÇEKTEN süzülen adı sayar (uydurma yok): tek hayalet → 1.
     r1 (2026-09-04, Rol-1 review) — sayaç KAYAN 14 gün DEĞİL, KABLOLAMA TARİHİNDEN
     (`analytics.HAYALET_SUZGEC_KABLOLAMA_TARIHI`) beri BİRİKİMLİ: N4c bu tarihten ÖNCEki bir
     olayın sayılmadığını, N4d okuma tavanının (`analytics.HAYALET_SAYAC_N_SATIR`) BEYANLI, ölçülü
     bir sınır olduğunu (aşan eski olay kuyruktan düşer), N4e dict-olmayan satırın PATLAMADIĞINI
     (isinstance süzgeci) çiviler.
  N5 REGRESYON (D3): bugünkü repo bounds.yaml 32/32 motor-okuyuculu (hayalet YOK) — süzgeç
     evrende YANLIŞ-POZİTİF üretmiyor, aday listesi bounds'un TAMAMIYLA birebir eşleşiyor.
  N6 FAIL-OPEN (D1): motor kaynağı ÖLÇÜLEMEZSE liste OLDUĞU GİBİ kalır (hayalet süzülmez),
     `reflect_hayalet_olculemedi` olayı basılır — kör bir tarayıcı aramayı sessizce daraltmaz.

Mutasyon (kapsam dışı ölçüm — bu dosya değil rapor turu ölçer): `virgin_knobs()` içindeki
`hayalet_suzgeci` çağrısı kaldırılırsa N1/N2/N3/N4 kırmızıya döner (D4).
"""
from __future__ import annotations

import json
import pathlib

import pytest

from meridian import analytics, config, hermes, reflect, store

GHOST = "a.hayalet_kablolu_v408"   # motor zincirinde bu literal YOK (N0 kanıtlar); alfabetik EN
                                   # ÖNDE — süzgeç yoksa deterministik döngü GHOST'u İLK dener
                                   # (kırmızı keskin: propose_virgin_knob `kn` sırasına göre yürür)
REAL = "exit.trail_atr_mult"      # motor okuyucusu ÖLÇÜLMÜŞ gerçek düğme; v135'te AYNI knob
                                   # guard'ı sandbox varsayılanlarıyla GEÇTİĞİ kanıtlanmış


def _mini_bounds(sandbox_state) -> pathlib.Path:
    """İki anahtarlı küçük arama uzayı (v263 `_mini_bounds` deseni): boş hipotez defterinde
    ikisi de H2'nin `hic_onerilmemis_dugmeler`ine düşer — ikinci bir sahte-H2 katmanı GEREKMEZ."""
    p = sandbox_state / "bounds.yaml"
    p.write_text(f"{GHOST}: {{min: 0.0, max: 1.0, step: 0.1, type: float}}\n"
                 f"{REAL}: {{min: 1.0, max: 6.0, step: 0.25, type: float}}\n")
    config.bounds.cache_clear()
    return p


def _olaylar(ad: str) -> list:
    return [e for e in store.read_jsonl("events.jsonl") if e.get("event") == ad]


# ---------------- N0: ölçüm ön koşulları ----------------
def test_N0_ghost_literali_motor_zincirinde_yok():
    src_dir = pathlib.Path(reflect.__file__).resolve().parent
    for mod in reflect.MOTOR_ZINCIRI:
        kaynak = (src_dir / f"{mod}.py").read_text()
        assert GHOST not in kaynak, f"fikstür bozuk: {GHOST} literali {mod}.py'de geçiyor"
    assert any(REAL in (src_dir / f"{m}.py").read_text() for m in reflect.MOTOR_ZINCIRI), \
        "fikstür bozuk: REAL hiçbir motor modülünde okunmuyor"


# ---------------- N1: virgin_knobs() hayaleti süzer, kablolu geçirir ----------------
def test_N1_virgin_knobs_hayaleti_suzer_kabloluyu_gecirir(sandbox_state):
    _mini_bounds(sandbox_state)
    kn = hermes.virgin_knobs()
    adlar = {r["knob"] for r in kn}
    assert GHOST not in adlar, "hayalet aday listesine sızdı — süzgeç virgin_knobs'a kablolanmadı"
    assert REAL in adlar, "kablolu gerçek düğme yanlış-pozitif süzüldü"


# ---------------- N2: propose_virgin_knob() hayalet önermez ----------------
def test_N2_propose_virgin_knob_hayalet_onermez(sandbox_state):
    _mini_bounds(sandbox_state)
    p = hermes.propose_virgin_knob()
    assert p is not None, "ön koşul: kablolu düğme guard'dan geçmedi — test fikstürü bozuk"
    aile = str(p["variable"]).split("@", 1)[0]
    assert aile != GHOST, "deterministik yol HAYALET düğme önerdi"
    assert aile == REAL, f"beklenmeyen aday: {aile}"


# ---------------- N3: süzüm olayla görünür (YASA 6) ----------------
def test_N3_suzum_olayla_gorunur_kaynak_hermes_virgin_knobs(sandbox_state):
    _mini_bounds(sandbox_state)
    hermes.virgin_knobs()
    evs = _olaylar("reflect_hayalet_dugme_suzuldu")
    assert evs, "süzüm olaysız — sessiz daraltma (YASA 6 ihlali)"
    e = evs[-1]
    assert e.get("kaynak") == "hermes.virgin_knobs", \
        f"tek boğaz etiketi yanlış/eksik: {e.get('kaynak')!r}"
    assert GHOST in (e.get("hayalet") or []), "olay süzülen anahtarın ADINI taşımıyor"


# ---------------- N4: canlı sayaç, KÜMÜLATİF (r1) ----------------
def test_N4_sayac_hayalet_suzulen_n_bir(sandbox_state):
    """Varsayılan `baslangic` kablolama günüdür (`HAYALET_SUZGEC_KABLOLAMA_TARIHI`); test-anı
    `ts` gerçek saatle basılır (bugün >= kablolama günü) — tek hayalet → 1, tek-günlük fark
    burada gözükmez (bkz. N4c/N4d, tarih/kuyruk sınırları için)."""
    _mini_bounds(sandbox_state)
    hermes.virgin_knobs()
    sc = analytics.learning_scorecard()
    assert "hayalet_suzulen_n" in sc, "`learning_scorecard` sayaç alanını hiç taşımıyor (D2)"
    assert sc["hayalet_suzulen_n"] == 1, \
        f"sayaç gerçekten süzülen TEK hayalet adını yansıtmıyor: {sc['hayalet_suzulen_n']}"


def test_N4b_sayac_hayalet_yokken_sifir(sandbox_state):
    """Uydurma yasağı: hiçbir hayalet süzülmediyse sayaç 0'dır — None ya da eksik alan DEĞİL."""
    sc = analytics.learning_scorecard()
    assert sc.get("hayalet_suzulen_n") == 0


def test_N4c_baslangictan_ONCEKI_olay_sayilmaz(sandbox_state):
    """r1: sayaç KAYAN pencere DEĞİL — `baslangic`tan (varsayılan kablolama günü) ÖNCEki bir
    hayalet olayı KÜMÜLATİF sayaca hiç girmemeli (operatörün geç sorduğu "2 hafta sonra sıfırsa
    geri al" sorusunun DOĞRU cevabı için — kablolamadan önceki gürültü sayılmaz)."""
    store.append_jsonl("events.jsonl", {
        "ts": "2026-09-03T23:59:59+00:00", "level": "warn",
        "event": "reflect_hayalet_dugme_suzuldu", "kaynak": "hermes.virgin_knobs",
        "hayalet": ["a.baslangic_oncesi_v408"], "n_hayalet": 1, "n_bounds": 1,
        "sayac_toplam": 1, "detail": "kablolama gününden ÖNCE yazıldı — sayılmamalı",
    })
    assert analytics._hayalet_suzulen_n() == 0, \
        "kablolama gününden ÖNCEki olay sayaca sızdı — kümülatif başlangıç filtresi çalışmıyor"


def test_N4d_limit_disina_ittirilen_eski_olay_BEYANLI_sayilmaz(sandbox_state):
    """r1: kuyruk-sınırlı okuma (`analytics.HAYALET_SAYAC_N_SATIR`, docstring'inde ÖLÇÜLÜ) BİLİNEN
    bir sınır taşır — kablolama gününden bugüne o tavanı aşan toplam (herhangi türden) olay
    birikirse en eski hayalet olayı kuyruktan sessizce düşer. Bu test sınırın GERÇEKTEN var
    olduğunu kanıtlar (gizli davranış değil, ÖLÇÜLMÜŞ ve beyanlı)."""
    n = analytics.HAYALET_SAYAC_N_SATIR
    store.append_jsonl("events.jsonl", {
        "ts": "2026-09-04T00:00:01+00:00", "level": "warn",
        "event": "reflect_hayalet_dugme_suzuldu", "kaynak": "hermes.virgin_knobs",
        "hayalet": ["a.limit_disi_v408"], "n_hayalet": 1, "n_bounds": 1,
        "sayac_toplam": 1, "detail": "kuyruk dolgusuyla iterilecek — pencerede ama limit dışında",
    })
    # dolgu: limit'i AŞACAK kadar ilgisiz satır — doğrudan dosyaya (N+5 ayrı store.append_jsonl
    # çağrısı test süresini gereksiz şişirirdi; biçim aynı JSONL, yalnız I/O yolu farklı)
    yol = sandbox_state / "events.jsonl"
    with open(yol, "a") as f:
        f.writelines(
            json.dumps({"ts": "2026-09-04T00:00:02+00:00", "level": "info",
                       "event": "dolgu_v408", "i": i}) + "\n"
            for i in range(n + 5)
        )
    assert analytics._hayalet_suzulen_n() == 0, \
        "eski hayalet olayı kuyruk-sınırlı okumanın DIŞINA çıkmadı — N ölçümü ya da davranış değişti"


def test_N4e_dict_olmayan_satir_patlamiyor(sandbox_state):
    """r1 KÜÇÜK: JSON satırı dict DEĞİLSE (liste/skaler) `.get()` AttributeError atardı —
    `isinstance(e, dict)` süzgeci onu güvenle atlar, sayaç PATLAMAZ ve yine 0 döner."""
    yol = sandbox_state / "events.jsonl"
    with open(yol, "a") as f:
        f.write(json.dumps([1, 2, 3]) + "\n")          # dict DEĞİL
        f.write(json.dumps("duz-metin-satiri") + "\n")  # dict DEĞİL
    assert analytics._hayalet_suzulen_n() == 0


# ---------------- N5: kablolu evrende REGRESYON YOK (D3) ----------------
def test_N5_kablolu_32_evrende_aday_listesi_bounds_ile_birebir(sandbox_state):
    """Bugünkü repo bounds.yaml'ın TAMAMI (32/32) motor-okuyuculu — süzgeç eklenmeden önceki
    davranışla aday listesi AYNI olmalı: hiçbir gerçek düğme yanlış-pozitif süzülmemeli."""
    b = config.bounds()
    assert len(b) >= 30, "ön koşul: gerçek repo bounds.yaml yüklenmedi"
    kn = hermes.virgin_knobs()
    adlar = sorted(r["knob"] for r in kn)
    assert adlar == sorted(b.keys()), \
        "kablolu (hayaletsiz) evrende süzgeç aday listesini DEĞİŞTİRDİ — yanlış-pozitif"
    assert not _olaylar("reflect_hayalet_dugme_suzuldu"), \
        "hiçbir hayalet yokken süzüm olayı basıldı — sahte pozitif"


# ---------------- N6: fail-open — ölçülemedi listeyi süzmez ----------------
def test_N6_olculemedi_fail_open_listeyi_suzmez(sandbox_state, monkeypatch):
    _mini_bounds(sandbox_state)
    monkeypatch.setattr(reflect, "MOTOR_ZINCIRI", ("boyle_bir_motor_modulu_yok_v408",))
    kn = hermes.virgin_knobs()
    adlar = {r["knob"] for r in kn}
    assert GHOST in adlar, "süzgeç KÖRKEN hayaleti süzdü — fail-open ihlali (null=ölçülemedi≠0)"
    assert REAL in adlar
    evs = _olaylar("reflect_hayalet_olculemedi")
    assert evs, "ölçüm düştü ve kimse duymadı (YASA 4)"
