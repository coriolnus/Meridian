"""test_e2_seyrelme_kovasi_v477.py — E2 ÖZETİNDE AYRI "SEYRELME (AYNA)" KOVASI (TSK-104 b).

ROL-1 KARARI (2026-09-13): `analytics.entry_execution_summary` ayna-satırlarını
(`loop._ayna_seyrelme_yaz` yazar) dolum/ret PAYDASINA bilerek KATMAZ — payda korunumu, EXE-006
dersi. Bu tur o kararı DEĞİŞTİRMEZ; yanına AYRI bir kova koyar ki kapı-öncesi seyrelme panoda
OKUNABİLİR olsun (bugüne kadar yalnız haftalık öz-inceleme raporunda görünüyordu).

AYNA-SATIRININ TANIMI KODDAN ÖLÇÜLDÜ (uydurma yasağı — brief'teki "karar = not_armed /
armed_not_submitted" betimlemesi YAZARIN alanlarıyla uyuşmuyor):
    `motor` = `loop.AYNA_SEYRELME_MOTOR` ("ayna_seyrelme")   ← kovayı BU alan tanımlar
    `karar` = `loop.AYNA_SEYRELME_KARAR` ("donusmedi")       ← icra hükmü değil, DÖNÜŞÜM hükmü
    `red_sinifi` ∈ `loop.AYNA_SEYRELME_SINIFLARI`            ← not_armed / armed_not_submitted /
                                                               olculemedi (DONUK sözlük)
    `red_nedeni` = SERBEST METİN                             ← sayılmaz (kırılım ayrı kart, n≥20)

NE ÇİVİLENİR:
  A1 AYRIŞMA ÇİVİSİ · ayna-satırı eklenince dolum/ret oranları ve kill paydası AYNI kalır,
                      yalnız `seyrelme.n` bir artar (kartın bedel yasası maddesi)
  A2 SINIF DAĞILIMI · donuk sözlüğün ÜÇÜ de yazılır; sözlük DIŞI değer sessizce katlanmaz
  A3 DÜRÜST BOŞLUK  · defter BOŞsa n=None + neden ("ölçmedim"), 0 DEĞİL
  A4 ÖLÇÜLMÜŞ SIFIR · defter DOLU ama ayna-satırı yoksa n=0 — baktık ve bulamadık
  A5 PENCERE        · kova mevcut özetle AYNI pencereyi kullanır (gün süzgeci)
  A6 SON TS         · en yeni ayna-satırının damgası; satır yoksa None
  B1 YOL-TUTARLI PK · satırı GERÇEK yazar (`loop._entry_exec_write` + loop sabitleri) yazınca
                      kova onu sayar — kovanın tanımı yazarın alanlarından TÜRER
  B2 TEK KAYNAK     · sınıf sözlüğü `loop`tan türer; ikinci okuyucu (`selfreview`) ile AYNI
                      satırları AYNI sayar (iki okuyucu sessizce ayrışamaz)
  B3 SERBEST METİN  · `red_nedeni` kova üretmez — yalnız `red_sinifi` sayılır
  C1 YASA 6         · sayının bir OKUYUCUSU var: pano işleme-hazırlık kartı alanı basar

YÖNTEM: ağ yok, canlı `state/` yok — her test `sandbox_state` altında kendi defterini yazar.
"""
from __future__ import annotations

import pathlib

from meridian import analytics as an
from meridian import loop, selfreview, store


PANO_KART = (pathlib.Path(__file__).resolve().parents[1]
             / "ui" / "src" / "pano" / "yuzeyler" / "portfoy" / "SeansIciEmir.tsx")
PANO_YUZEY = (pathlib.Path(__file__).resolve().parents[1]
              / "ui" / "src" / "pano" / "yuzeyler" / "PortfoyYuzey.tsx")

GUN = "2026-09-13"


def _ayna_satiri(pid: str, sinif: str, *, date: str = GUN, ts: str | None = None) -> dict:
    """Yazarın (`loop._ayna_seyrelme_yaz`) ürettiği satırın alan alan aynısı."""
    return {"ts": ts or f"{date}T21:05:00+00:00", "date": date, "plan_id": pid, "ticker": "AAA",
            "motor": loop.AYNA_SEYRELME_MOTOR, "karar": loop.AYNA_SEYRELME_KARAR,
            "entry_trigger": 100.0, "fill": None, "red_sinifi": sinif,
            "red_nedeni": f"sinif={sinif} · gate_verdict='GO' broker_status=None",
            "plan_date": date, "kaynak": "eod_ayna"}


def _icra_satirlari() -> list:
    """Kovaya GİRMEYEN gerçek icra satırları — payda korunumunun ölçüleceği taban."""
    return [
        {"date": GUN, "plan_id": "P1", "ticker": "A", "motor": "ayna", "karar": "submitted",
         "limit": 100.5, "fill": 100.4, "fill_vs_resmi_acilis_bps": 40.0,
         "fill_vs_limit_bps": -9.9, "emir_tipi": "limit", "tif": "day"},
        {"date": GUN, "plan_id": "P2", "ticker": "B", "motor": "ayna", "karar": "rejected",
         "red_sinifi": "stop_vs_current", "fill": None},
        {"date": GUN, "plan_id": "P1", "ticker": "A", "motor": "ic", "karar": "fill", "fill": 100.4},
        {"date": GUN, "plan_id": "P3", "ticker": "C", "motor": "ic",
         "karar": "entry_missed_limit", "fill": None},
    ]


def _yaz(rows: list) -> None:
    for r in rows:
        store.append_jsonl(loop.ENTRY_LEDGER, r)


# =================================================================================================
# A1 — AYRIŞMA ÇİVİSİ: KOVA AÇILDI, HİÇBİR ORAN KIMILDAMADI
# =================================================================================================
def test_a1_ayna_satiri_paydayi_kaydirmaz_yalniz_seyrelme_artar(sandbox_state):
    """Kartın BEDEL maddesi: yeni kova mevcut hiçbir sayıyı değiştirmez.

    Bu testin asıl çivisi ikinci yarısıdır: aynı defter ayna-satırıyla ZENGİNLEŞTİRİLİNCE dolum
    oranı, ret oranı ve iç motorun kill paydası HARFİYEN aynı kalmalı. Kovayı `ayna` kovasına
    katmak (ya da `motor.startswith("ayna")` yazmak) eşiği kod değişikliğiyle sessizce kaydırırdı
    — kill-list DOKUNULMAZDIR (kart EXE-2026-001)."""
    _yaz(_icra_satirlari())
    once = an.entry_execution_summary(days=None)
    assert once["seyrelme"]["n"] == 0, "ayna-satırı yokken kova ölçülmüş sıfır demeli"

    _yaz([_ayna_satiri("P4", "not_armed")])
    sonra = an.entry_execution_summary(days=None)

    assert sonra["seyrelme"]["n"] == 1, "ayna-satırı eklendi, seyrelme sayacı artmadı"
    for yol in (("ayna", "n"), ("ayna", "red_orani"), ("ic_motor", "n"),
                ("ic_motor", "dolmama_orani"), ("kapi", "n")):
        assert once[yol[0]][yol[1]] == sonra[yol[0]][yol[1]], \
            f"{'.'.join(yol)} ayna-satırından etkilendi — payda korunumu bozuldu"
    assert once["ayna"]["dolum"]["dolum_orani"] == sonra["ayna"]["dolum"]["dolum_orani"] == 1.0
    assert once["ayna"]["dolum"]["n_dolan"] == sonra["ayna"]["dolum"]["n_dolan"] == 1
    assert once["ayna"]["karar_dagilimi"] == sonra["ayna"]["karar_dagilimi"]
    # Üst düzey HAM sayım ayna-satırını GÖRÜR (kova ayrımı satırı saklamaz — v141 deseni).
    assert sonra["n"] == once["n"] + 1


# =================================================================================================
# A2 / A3 / A4 — SINIF DAĞILIMI, DÜRÜST BOŞLUK, ÖLÇÜLMÜŞ SIFIR
# =================================================================================================
def test_a2_sinif_dagilimi_donuk_sozlukten_sayilir_sozluk_disi_adiyla_durur(sandbox_state):
    """Donuk sözlüğün ÜÇÜ de yazılır (görülmeyen sınıf 0 ile durur, alanı hiç doğmaz değil) ve
    sözlük DIŞI bir değer sessizce katlanmaz — `sinif_disi_n` ile ADIYLA sayılır."""
    _yaz([_ayna_satiri("P1", "not_armed"), _ayna_satiri("P2", "not_armed"),
          _ayna_satiri("P3", "armed_not_submitted"), _ayna_satiri("P4", "dorduncu_sinif")])
    s = an.entry_execution_summary(days=None)["seyrelme"]

    assert s["n"] == 4
    assert s["sinif_dagilimi"] == {"not_armed": 2, "armed_not_submitted": 1, "olculemedi": 0}
    assert s["sinif_disi_n"] == 1, "sözlük dışı sınıf yutuldu — bilinmeyen GİZLENMEZ"
    # `karar` alanı DÖNÜŞÜM hükmüdür ve tek değer taşır; sınıfla karıştırılmaz.
    assert s["karar_dagilimi"] == {loop.AYNA_SEYRELME_KARAR: 4}


def test_a3_bos_defter_none_der_sifir_demez(sandbox_state):
    """Defter BOŞken n=0 basmak "hiçbir plan seyrelmedi" demek olurdu; doğru cevap "ölçmedim".
    (Aynı ayrım `selfreview._donusum_ozeti`te de yazılı — sıfır ile bilinmiyor ayrı şeylerdir.)"""
    s = an.entry_execution_summary()["seyrelme"]
    assert s["n"] is None and s["sinif_dagilimi"] is None and s["karar_dagilimi"] is None
    assert s["son_ts"] is None
    assert "ÖLÇÜLMEDİ" in s["durum"] and "0 DEĞİL" in s["durum"]


def test_a4_defter_dolu_ayna_satiri_yoksa_sifir_durusttur(sandbox_state):
    """Defter DOLU ama pencerede ayna-satırı yok → 0 dürüsttür: baktık ve bulamadık."""
    _yaz(_icra_satirlari())
    s = an.entry_execution_summary(days=None)["seyrelme"]
    assert s["n"] == 0
    assert s["sinif_dagilimi"] == {"not_armed": 0, "armed_not_submitted": 0, "olculemedi": 0}
    assert s["sinif_disi_n"] == 0 and s["son_ts"] is None
    assert "ölçüldü" in s["durum"]


# =================================================================================================
# A5 / A6 — PENCERE VE DAMGA
# =================================================================================================
def test_a5_kova_ozetin_penceresini_kullanir(sandbox_state):
    """Kovanın penceresi mevcut özetinkiyle AYNIdır (ikinci bir pencere tanımı ikinci bir gerçek
    üretirdi). Pencere dışındaki ayna-satırı sayılmaz ama defterde DURUR."""
    _yaz([_ayna_satiri("P_eski", "not_armed", date="2020-01-01"),
          _ayna_satiri("P_yeni", "armed_not_submitted")])
    dar = an.entry_execution_summary()["seyrelme"]          # varsayılan 7 günlük pencere
    genis = an.entry_execution_summary(days=None)["seyrelme"]

    assert dar["n"] == 1 and dar["sinif_dagilimi"]["armed_not_submitted"] == 1
    assert dar["pencere_gun"] == an.ENTRY_SUMMARY_DAYS
    assert genis["n"] == 2 and genis["pencere_gun"] is None


def test_a6_son_ts_en_yeni_ayna_satirindan_okunur(sandbox_state):
    _yaz([_ayna_satiri("P1", "not_armed", ts="2026-09-11T21:00:00+00:00"),
          _ayna_satiri("P2", "not_armed", ts="2026-09-12T21:00:00+00:00")])
    s = an.entry_execution_summary(days=None)["seyrelme"]
    assert s["son_ts"] == "2026-09-12T21:00:00+00:00"


# =================================================================================================
# B1 — YOL-TUTARLI POZİTİF KONTROL: SATIRI GERÇEK YAZAR YAZAR
# =================================================================================================
def test_b1_gercek_yazarin_yazdigi_satir_kovaya_dusser(sandbox_state):
    """Kovanın tanımı YAZARIN alanlarından türer. Satır burada elle kurulmaz: `loop`un kendi
    yazma yolu (`_entry_exec_write` + `loop` sabitleri) kullanılır. Yazar `motor`/`karar`
    literallerini değiştirirse bu çivi öter — okuyucu sessizce boş kova basamaz."""
    loop._entry_exec_write({"date": GUN, "plan_id": "PK1", "ticker": "ZZZ",
                            "motor": loop.AYNA_SEYRELME_MOTOR, "karar": loop.AYNA_SEYRELME_KARAR,
                            "fill": None, "red_sinifi": loop.AYNA_SINIF_NOT_ARMED,
                            "red_nedeni": "sinif=not_armed", "plan_date": GUN,
                            "kaynak": "eod_ayna"})
    s = an.entry_execution_summary(days=None)["seyrelme"]
    assert s["n"] == 1 and s["sinif_dagilimi"]["not_armed"] == 1
    assert s["son_ts"] is not None, "yazarın bastığı `ts` damgası okunamadı"


# =================================================================================================
# B2 — TEK KAYNAK: SÖZLÜK LOOP'TAN TÜRER, İKİ OKUYUCU AYNI SAYIYI VERİR
# =================================================================================================
def test_b2_sozluk_loop_tan_turer_ve_ikinci_okuyucuyla_ayrismaz(sandbox_state):
    """Sözlüğün kopyası TUTULMAZ: kova anahtarları `loop.AYNA_SEYRELME_SINIFLARI`nın ta kendisi
    olmalı. Ayrıca AYNI defteri okuyan ikinci yüzey (`selfreview._donusum_ozeti`, haftalık rapor)
    aynı satırları AYNI saymalı — iki okuyucu sessizce ayrışırsa hangi sayının doğru olduğu
    ölçülemez hâle gelir."""
    _yaz([_ayna_satiri("P1", "not_armed"), _ayna_satiri("P2", "armed_not_submitted"),
          _ayna_satiri("P3", "olculemedi")])
    s = an.entry_execution_summary(days=None)["seyrelme"]

    assert tuple(s["sinif_dagilimi"]) == loop.AYNA_SEYRELME_SINIFLARI, \
        "kova kendi sınıf kopyasını tutuyor — sözlük loop'tan TÜREMELİ"
    rapor = selfreview._donusum_ozeti("2020-01-01")
    assert s["sinif_dagilimi"] == rapor["sinif_dagilimi"] and s["n"] == rapor["donusmeyen_n"], \
        "aynı defteri okuyan iki yüzey farklı sayı veriyor (tek-kaynak ayrışması)"


# =================================================================================================
# B3 — SERBEST METİN SAYILMAZ
# =================================================================================================
def test_b3_red_nedeni_serbest_metni_kova_uretmez(sandbox_state):
    """Kırılım `red_nedeni`den DEĞİL `red_sinifi`nden doğar (serbest metin her satırda tekildir;
    ondan kova üretmek n=1'lik sahte bir dağılım basardı). Alt-neden kırılımı AYRI kartın işi."""
    rows = [_ayna_satiri("P1", "not_armed"), _ayna_satiri("P2", "not_armed")]
    rows[0]["red_nedeni"] = "bambaşka bir serbest metin"
    rows[1]["red_nedeni"] = "bir başkası daha"
    _yaz(rows)
    s = an.entry_execution_summary(days=None)["seyrelme"]
    assert s["sinif_dagilimi"]["not_armed"] == 2
    assert "bambaşka" not in repr(s), "serbest metin kovaya sızdı"


# =================================================================================================
# C1 — YASA 6: SAYININ OKUYUCUSU VAR
# =================================================================================================
def test_c1_seyrelme_kovasinin_pano_okuyucusu_var(sandbox_state):
    """Okunmayan artefakt üretilmemişten farksızdır. Zincir: analytics sayar → `/api/diagnostics`
    `icra.slipaj.seyrelme` altında servis eder (`entry_execution_summary` gövdesinin İÇİNDE, yani
    ayrı bir uç kablosu YOK) → pano işleme-hazırlık kartı basar."""
    import inspect

    from meridian import api
    src = inspect.getsource(api.api_diagnostics)
    assert "entry_execution_summary" in src and '"icra"' in src

    # ÇİVİ KODU ARAR, ŞERHİ DEĞİL (mutasyon turu 1: kabloyu kesince çivi ÖTMEDİ, çünkü
    # "seyrelme" kelimesi düzyazı şerhte de geçiyordu — bir yorum okuyucu sayılmaz).
    kart = PANO_KART.read_text()
    assert "<SeyrelmeSatiri s={seyrelme} />" in kart, \
        "kart satırı ÇİZMİYOR — ölçüm okuyucusuz (YASA 6); şerhte adı geçmesi okuyucu değildir"
    assert "sinif_dagilimi" in kart, "kart kırılımı okumuyor (yalnız toplamı basmak kovayı yarım okur)"
    for alan in ("not_armed", "armed_not_submitted"):
        assert alan in kart, f"pano `{alan}` kırılımını basmıyor"
    yuzey = PANO_YUZEY.read_text()
    assert "seyrelme={teshis.veri?.icra?.slipaj?.seyrelme}" in yuzey, \
        "üst yüzey kovayı karta GEÇİRMİYOR — kart 'alan yok' çizerdi (kablo arızası)"
