"""WP6 dört küçük kalem (v268) — çapa bayatlığı (A17) · P2 damgası · #16 latent yedek · #11 ölü sabitler.

Kaynak: ROADMAP WP6 + docs/ENVANTER-DEGER-ESITLIGI-2026-08-22.md. Dört çivi + bir birim testi:

(a) `state/goal.yaml` sektör-tavanı yorumundaki `guard.py:N` çapası GERÇEK satırı gösterir —
    testte sabit satır numarası YOK: iki dosya okunur, çapa metinden çıkarılır ve kural-metni
    aramasıyla (`def sector_cap_basis`) çapraz doğrulanır. Satırlar birlikte kayarsa test
    değişmeden geçer; çapa geride kalırsa ADIYLA düşer (A17 sınıfının kapısı budur).
(b) `meridian/api.py` slippage çapası (`goal.yaml:N slippage_bps: V`) goal'daki gerçek satır ve
    gerçek değerle tutarlıdır — aynı çapraz-doğrulama deseni.
(c) `score.py` + `shadow_variants.py` `min_sample` çağrı-içi yedeği 30'dur ve goal ile EŞİTTİR
    (envanter #16 latent ayrıklığı: anahtar goal'dan düşerse yedek konuşur — yanlış tabana
    dönmemeli). Desen-geneli kardeşi: test_deger_esitligi_deseni_v239::test_8a.
(d) `guard.py`de SECTOR_CAP_DEFAULT_PCT / HEAT_CAP_DEFAULT_PCT TANIMI yok (sessiz diriliş
    kapısı) ve mezar taşı + envanter atfı DURUR (emsal: bounds.yaml `spy_sma_gate` taşı).
(e) P2 `yerel_donmus_defter` damgası: DB'siz dünyada kanonik defter dosyası okunurken teşhis
    yüzeyine (obs → state/events.jsonl) süreç başına BİR KEZ düşer; boş sandbox'ta düşmez.
"""
import json
import re
from pathlib import Path

import yaml

from meridian import storage

REPO = Path(__file__).resolve().parent.parent


# ==================================================================================================
# (a) + (b) — A17 çapa bayatlığı: kaynak-içi satır çapaları gerçek satırla çapraz doğrulanır
# ==================================================================================================

def test_a_goal_sektor_tavani_capasi_gercek_guard_satirini_gosterir():
    """goal.yaml'daki sektör-tavanı yorumu `guard.py:N` çapası taşır; N, `def sector_cap_basis`ın
    BUGÜNKÜ satırı olmalı. Eski `:352` çapası bayatlamıştı (denetim A17, 2026-08-13) — bu test o
    sınıfın nöbetçisidir: guard.py kayar da çapa güncellenmezse adıyla düşer."""
    goal_satirlar = (REPO / "state" / "goal.yaml").read_text().splitlines()
    capali = [s for s in goal_satirlar if "sector_cap_basis" in s and "guard.py:" in s]
    assert len(capali) == 1, f"sektör-tavanı çapa satırı TEK olmalı, bulunan: {capali!r}"
    n = int(re.search(r"guard\.py:(\d+)", capali[0]).group(1))

    guard_satirlar = (REPO / "meridian" / "guard.py").read_text().splitlines()
    gercek = [i + 1 for i, s in enumerate(guard_satirlar)
              if s.startswith("def sector_cap_basis(")]
    assert len(gercek) == 1, f"`def sector_cap_basis` tek olmalı, bulunan satırlar: {gercek}"
    assert n == gercek[0], (f"A17 çapa BAYAT: goal.yaml `guard.py:{n}` diyor, "
                            f"`def sector_cap_basis` gerçekte guard.py:{gercek[0]} — çapayı düzelt")


def test_b_api_slippage_capasi_goal_gercek_satiriyla_tutarli():
    """api.py `_slippage_measured` docstring'i `goal.yaml:N slippage_bps: V` çapası taşır; N'inci
    satır gerçekten `slippage_bps:` olmalı ve değeri V ile (ve goal'un parse edilmiş değeriyle)
    eşit olmalı. Eski `:27` çapası bayatlamıştı — aynı A17 nöbeti."""
    api_txt = (REPO / "meridian" / "api.py").read_text()
    capalar = re.findall(r"goal\.yaml:(\d+)\s+slippage_bps:\s*(\d+)", api_txt)
    assert len(capalar) == 1, f"slippage çapası TEK olmalı, bulunan: {capalar}"
    satir_no, beyan = int(capalar[0][0]), int(capalar[0][1])

    goal_metin = (REPO / "state" / "goal.yaml").read_text()
    hedef = goal_metin.splitlines()[satir_no - 1]
    assert re.match(r"^slippage_bps:", hedef), (
        f"A17 çapa BAYAT: api.py `goal.yaml:{satir_no}` diyor ama o satır: {hedef!r}")
    gercek = int(yaml.safe_load(goal_metin)["slippage_bps"])
    assert beyan == gercek, (f"api.py çapası değeri {beyan} beyan ediyor, "
                             f"goal.yaml gerçekte {gercek} diyor")


# ==================================================================================================
# (c) — envanter #16: min_sample çağrı-içi yedeği (latent ayrıklık)
# ==================================================================================================

def test_c_min_sample_yedegi_30_ve_goal_ile_esit():
    """Yazım varsayılanı 20 idi, gerçek taban 30 (goal.yaml `min_sample`). Anahtar goal'dan
    düşerse yedek KONUŞUR — iki modül sessizce 20 tabanına dönmemeli. 30 literali BİLEREK
    çivili: goal'daki taban değişirse bu test düşer ve yedeğin de bilinçli güncellenmesini
    zorlar (desen-geneli eşitlik kardeşi v239::test_8a'da, o literal çivilemez)."""
    gercek = int(yaml.safe_load((REPO / "state" / "goal.yaml").read_text())["min_sample"])
    assert gercek == 30, f"goal.yaml min_sample {gercek} — taban bilinçli değiştiyse bu çiviyi güncelle"

    desen = re.compile(r'\.get\(\s*"min_sample"\s*,\s*(\d+)')
    for ad in ("score.py", "shadow_variants.py"):
        yedekler = [int(v) for v in desen.findall((REPO / "meridian" / ad).read_text())]
        assert yedekler, f"{ad}: `min_sample` yedek literali bulunamadı — desen mi kod mu değişti?"
        assert all(v == gercek for v in yedekler), (
            f"{ad}: min_sample yedeği goal tabanından ({gercek}) ayrık: {yedekler} — latent #16 geri açılmış")


# ==================================================================================================
# (d) — envanter #11: okuyucusuz iki ölü sabit KALKTI, mezar taşı DURUR
# ==================================================================================================

def test_d_guard_olu_sabitler_yok_mezar_tasi_var():
    """`SECTOR_CAP_DEFAULT_PCT` / `HEAT_CAP_DEFAULT_PCT` repo+test genelinde OKUYUCUSUZDU
    (YASA 6) — KALDIRILDILAR, bağlanmadılar (bağlamak kart-önce strateji-kimliği değişikliği
    olurdu). Sessiz diriliş kapısı: tanım satırı GERİ GELEMEZ; taş ve envanter atfı DURUR."""
    src = (REPO / "meridian" / "guard.py").read_text()
    for ad in ("SECTOR_CAP_DEFAULT_PCT", "HEAT_CAP_DEFAULT_PCT"):
        assert not re.search(rf"^\s*{ad}\s*=", src, re.M), (
            f"{ad} tanımı guard.py'ye GERİ gelmiş — sessiz diriliş; okuyucusu yoksa YASA 6, "
            f"okuyucusu olacaksa kart-önce ölçüm gerekir (mezar taşına bak)")
    assert "MEZAR TAŞI: SECTOR_CAP_DEFAULT_PCT / HEAT_CAP_DEFAULT_PCT" in src, "mezar taşı silinmiş"
    assert "ENVANTER-DEGER-ESITLIGI-2026-08-22" in src, "mezar taşındaki envanter #11 atfı silinmiş"

    import meridian.guard as guard
    assert not hasattr(guard, "SECTOR_CAP_DEFAULT_PCT")
    assert not hasattr(guard, "HEAT_CAP_DEFAULT_PCT")


# ==================================================================================================
# (e) — P2: `yerel_donmus_defter` damgası (storage teşhisi, birim)
# ==================================================================================================

def _olaylar(state, event: str) -> list[dict]:
    """Ad-filtreli olay okuma — test_kovab_yapi_v163 ile aynı desen (obs → state/events.jsonl)."""
    p = state / "events.jsonl"
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text().splitlines()
            if x.strip() and json.loads(x).get("event") == event]


def test_e_yerel_donmus_defter_damgasi_uretiliyor(sandbox_state, monkeypatch):
    """P2 (denetim §3.4 → envanter §4.2-#4): DB dosyası YOKKEN kanonik defter dosyası okunuyorsa
    `yerel_donmus_defter` damgası teşhis yüzeyine düşer — `db_off_kaynaklar_arsivde`nin simetriği.
    Üç hâl: (i) boş sandbox → damga YOK (anlatılacak hâl yok, önbellek alınmaz); (ii) kanonik
    dosya varken ilk okuma → damga BİR KEZ, davranış değişmeden (okuma dosyadan sürer);
    (iii) sonraki okumalar olay defterini sele çevirmez (süreç başına bir kez)."""
    monkeypatch.delenv("MERIDIAN_DB", raising=False)   # env kabuktan sızıp yönü değiştirmesin
    storage.close_connections()
    monkeypatch.setattr(storage, "_YEREL_OLCULDU", set())   # süreç-önbelleği bu teste ait olsun

    # (i) boş sandbox: DB yok AMA kanonik dosya da yok → susar
    assert storage.active("trades.jsonl") is False
    assert _olaylar(sandbox_state, "yerel_donmus_defter") == []

    # (ii) kanonik dosya doğunca damga düşer — (i)'in susması önbellekten DEĞİLDİ (aynı süreç)
    (sandbox_state / "trades.jsonl").write_text('{"id": 1}\n')
    assert storage.active("trades.jsonl") is False, "damga karar DEĞİL beyan: dosya yolu sürmeli"
    kayit = _olaylar(sandbox_state, "yerel_donmus_defter")
    assert len(kayit) == 1, f"damga yok ya da tekrarlıyor: {len(kayit)}"
    assert kayit[0]["mevcut"] == ["trades.jsonl"]
    assert "fotoğraf" in kayit[0]["detail"], "damga 'donmuş fotoğraf olabilir' uyarısını anlatmıyor"

    # (iii) süreç başına bir kez: sonraki okumalar sel üretmez
    for _ in range(5):
        storage.active("trades.jsonl")
        storage.active("portfolio.json")
    assert len(_olaylar(sandbox_state, "yerel_donmus_defter")) == 1


def test_e2_db_varken_damga_yanmaz(sandbox_state, monkeypatch):
    """Karşı-durum: DB dosyası VARSA dünya DB dünyasıdır — `yerel_donmus_defter` yanmamalı
    (o dünyanın yarım-hâl beyanı `db_off_kaynaklar_arsivde`nindir, test_kovab_yapi_v163 C5)."""
    monkeypatch.delenv("MERIDIAN_DB", raising=False)
    storage.close_connections()
    monkeypatch.setattr(storage, "_YEREL_OLCULDU", set())
    (sandbox_state / "trades.jsonl").write_text('{"id": 1}\n')
    storage.ensure_schema()                            # DB'yi şemasıyla yaratır
    try:
        assert storage.active("trades.jsonl") is True
        assert _olaylar(sandbox_state, "yerel_donmus_defter") == []
    finally:
        storage.close_connections()
