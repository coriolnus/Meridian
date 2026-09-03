"""v283 · KORUNUM KOVASI — `uyuyan_kurulum` terminal sınıfı (WP5-F/16, ROADMAP.md §3 "WP5-F ·
KORUNUM SINIFI — uyuyan-kurulum planlarına terminal sınıf" başlığı; TSK-083, 2026-09-03: satır
çapası ROADMAP :1164-1188 çürümüştü, sembole çevrildi).

NİÇİN VAR. `watchdog.conservation_report` bir planı ancak ŞU altı yoldan biriyle açıklayabiliyordu:
işleme döndü · olayla düştü (`dropped`) · kapıda öldü (`NO_GO`) · henüz taze · tetik gelmedi
(`no_fill`) · replay dönemi (`replay_era`). Hiçbirine uymayan plan SESSİZ KAYIP sayılıyordu. Ama
bir yedinci sınıf vardı ve o kayıp DEĞİLDİ: kurulumu o gün SİLAHLI OLMAYAN plan. Böyle bir plan
yapısal olarak silahlanamaz, dolayısıyla hiçbir terminal olaya da ulaşamaz — dedektör onu
"kayıtsız kayboldu" diye sayıyordu. Yerel 2026-07-28 anlık görüntüsünde `unexplained=6`ydı ve
ALTISI DA uyuyan-kurulum planıydı (CSX/UNP/NSC/RTX 07-23 momentum_burst · PKG 07-24
momentum_burst · ROK 07-27 exhaustion_hammer) — yani sayının TAMAMI bu sınıftı.

PIT ÇİVİSİ (bu dosyanın asıl işi). Sınıfı `strategy.ARMED_SETUPS` sabitine bakarak kurmak bir
NOKTA-ZAMANI İHLALİdir: o sabit 2026-08-22 B1 kararıyla değişti (`pullback` çıkarıldı, c150902) ve
yarın yine değişecek. Bugünkü sabitle dünkü planı yargılayan bir dedektör, her silahlanma/
silahsızlanma turunda GEÇMİŞİ yeniden yazar. Kayıt nerede: plan satırının KENDİ damgası
`dormant_setup` (``loop` uyuyan-kurulum korunumu/1870`, `cf_backfill.py:90/117`) — plan üretilirken
`setup not in strat.ARMED_SETUPS` ölçülüp satıra yazılır, yani o günün yasası satırda donar.
Aşağıdaki `test_pit_*` ikilisi tam bunu çiviler: damga ile bugünkü sabit ÇELİŞTİĞİNDE damga kazanır.

UYDURMA YASAĞI. Damgasız satır (alan defter şemasına girmeden önce yazılmış plan; yerel defterde
367/390 satır böyle) "silahlıydı" diye OKUNMAZ — `uyuyan_olculemedi` sayılır, TERMİNAL SAYILMAZ ve
`unexplained`te kalır. Ölçülemeyen bir hükmü temizlik diye yazmak, kovanın kendisini bir yalana
çevirirdi.

YASA 6. İki yeni alanın (`uyuyan_kurulum`, `uyuyan_olculemedi`) okuyucusu `check_integrity_and_alarm`
içindedir: KORUNUM alarmının metni paydayı taşır, sıfırdan büyük kova ayrıca günlük turda
`conservation_uyuyan_kovasi` satırıyla deftere düşer. `test_yasa6_*` bunu davranışla sınar —
kaynak-metin çivisi değil, gerçek çağrı.
"""
from __future__ import annotations

import io
import pathlib
import tokenize

import pytest

from meridian import store
from meridian import watchdog as w

REPO = pathlib.Path(__file__).resolve().parents[1]


def _defter(planlar: list[dict], *, live: str = "2026-07-10", last: str = "2026-07-30") -> None:
    """Kovanın tek değişkenini yalıtan asgari defter: canlı dönem AÇIK, cf kaderi BOŞ, olay YOK.

    Böylece bir planın `unexplained`e mi yoksa yeni kovaya mı düştüğü YALNIZ damgadan çıkar."""
    store.write_json("portfolio.json", {"last_date": last})
    store.write_jsonl("events.jsonl", [{"event": "daily_cycle", "date": live}])
    store.write_jsonl("trades.jsonl", [])
    store.write_jsonl("counterfactuals.jsonl", [])
    store.write_jsonl("trade_plans.jsonl", planlar)


# ---------------- SINIFIN KENDİSİ ----------------
def test_uyuyan_kurulum_terminaldir_ve_kayip_sayilmaz(sandbox_state):
    """Damgalı uyuyan plan: AÇIKLANMIŞ ÇIKIŞ. Kovaya girer, `unexplained`ten düşer, hüküm temizlenir."""
    _defter([{"id": "P-2026-07-23-CSX-momentum_burst", "date": "2026-07-23", "ticker": "CSX",
              "setup": "momentum_burst", "gate_verdict": "REVIEW", "dormant_setup": True}])
    rep = w.conservation_report()
    assert rep["uyuyan_kurulum"] == 1
    assert rep["unexplained"] == 0 and rep["rows"] == []
    assert rep["ok"] is True
    assert rep["uyuyan_olculemedi"] == 0


def test_silahli_plan_hala_aciklanamayandir(sandbox_state):
    """POZİTİF KONTROL — kova her şeyi yutan bir çöp kutusu OLAMAZ. Aynı satır, damga `False`:
    plan silahlıydı, silahlandı da denemedi, hiçbir olay yazmadı → SESSİZ KAYIP olarak KALIR.
    Bu test olmasaydı `uyuyan_kurulum`u koşulsuz saymak da yeşil geçerdi."""
    _defter([{"id": "P-2026-07-23-CSX", "date": "2026-07-23", "ticker": "CSX",
              "setup": "breakout_vcp", "gate_verdict": "GO", "dormant_setup": False}])
    rep = w.conservation_report()
    assert rep["uyuyan_kurulum"] == 0
    assert rep["unexplained"] == 1 and rep["rows"][0]["ticker"] == "CSX"
    assert rep["ok"] is False


def test_damgasiz_plan_olculemedi_olur_terminal_sayilmaz(sandbox_state):
    """UYDURMA YASAĞI. Damga YOKSA silahlanma tarihçesi OKUNAMAZ. 'Okuyamadım' ≠ 'silahlıydı' ve
    ≠ 'uyuyandı': plan `uyuyan_olculemedi` paydasına yazılır ama `unexplained`te KALIR."""
    _defter([{"id": "P-2025-11-03-OLD", "date": "2026-07-15", "ticker": "OLD",
              "setup": "breakout_vcp", "gate_verdict": "GO"}])          # `dormant_setup` YOK
    rep = w.conservation_report()
    assert rep["uyuyan_olculemedi"] == 1
    assert rep["uyuyan_kurulum"] == 0
    assert rep["unexplained"] == 1, "ölçülemeyen hüküm terminal sayıldı — uydurma"
    assert rep["ok"] is False


def test_payda_iki_taraflidir(sandbox_state):
    """PAYDA BEYANI: kaç plan terminal sayıldı, kaçı ölçülemedi — ikisi de AYNI raporda."""
    _defter([
        {"id": "U-1", "date": "2026-07-23", "ticker": "AAA", "setup": "momentum_burst",
         "gate_verdict": "REVIEW", "dormant_setup": True},
        {"id": "U-2", "date": "2026-07-24", "ticker": "BBB", "setup": "exhaustion_hammer",
         "gate_verdict": "REVIEW", "dormant_setup": True},
        {"id": "X-1", "date": "2026-07-25", "ticker": "CCC", "setup": "breakout_vcp",
         "gate_verdict": "GO"},                                          # damgasız → ölçülemedi
        {"id": "S-1", "date": "2026-07-26", "ticker": "DDD", "setup": "breakout_vcp",
         "gate_verdict": "GO", "dormant_setup": False},                  # gerçek sessiz kayıp
    ])
    rep = w.conservation_report()
    assert (rep["uyuyan_kurulum"], rep["uyuyan_olculemedi"]) == (2, 1)
    assert rep["unexplained"] == 2                                        # CCC (ölçülemedi) + DDD
    assert {r["ticker"] for r in rep["rows"]} == {"CCC", "DDD"}


# ---------------- PIT: DAMGA KAZANIR, BUGÜNKÜ SABİT DEĞİL ----------------
def test_pit_bugun_silahli_bir_kurulum_gecmiste_uyuyan_olabilir(sandbox_state):
    """`breakout_vcp` BUGÜN silahlıdır. Plan satırı yine de `dormant_setup: True` diyorsa o gün
    silahsızdı demektir (kurulum sonradan silahlandı) — kayıt kazanır, sabit değil."""
    _defter([{"id": "P-2026-07-23-AAA-breakout_vcp", "date": "2026-07-23", "ticker": "AAA",
              "setup": "breakout_vcp", "gate_verdict": "REVIEW", "dormant_setup": True}])
    rep = w.conservation_report()
    assert rep["uyuyan_kurulum"] == 1 and rep["unexplained"] == 0


def test_pit_bugun_uyuyan_bir_kurulum_gecmiste_silahli_olabilir(sandbox_state):
    """Simetrik yön ve ASIL TEHLİKE: `pullback` 2026-08-22 B1 kararıyla SİLAHTAN DÜŞTÜ. Bugünkü
    `ARMED_SETUPS`e bakan bir dedektör, B1'den ÖNCE silahlıyken kaybolmuş bir pullback planını
    geriye dönük olarak 'zaten uyuyandı' diye affederdi — kararın kendisi geçmişi temizlerdi.
    Damga `False` olduğu sürece plan SESSİZ KAYIP olarak kalmalı."""
    _defter([{"id": "P-2026-07-23-BBB", "date": "2026-07-23", "ticker": "BBB",
              "setup": "pullback", "gate_verdict": "GO", "dormant_setup": False}])
    rep = w.conservation_report()
    assert rep["uyuyan_kurulum"] == 0
    assert rep["unexplained"] == 1 and rep["rows"][0]["ticker"] == "BBB"


def _kod_govdesi() -> str:
    """`conservation_report`ın YORUMSUZ kodu. Ham metinde arama yapmak burada işe yaramaz:
    gövdenin gerekçe bloğu PIT ihlalini ANLATMAK için `ARMED_SETUPS`i adıyla anıyor — kuralı
    açıklayan cümleyi kuralın ihlali sanan bir çivi, doğru yorumu yazmayı cezalandırırdı.
    Metin sabitleri KALIR: aranan damga adı (`"dormant_setup"`) bir sözlük anahtarıdır ve
    onu da eleyen bir süzgeç, sınıfın kaynağını çivileyemezdi."""
    src = (REPO / "meridian" / "watchdog.py").read_text()
    govde = src.split("def conservation_report")[1].split("\nFINGERPRINT_FILE")[0]
    okunur = io.StringIO("def conservation_report" + govde).readline
    return "\n".join(t.string for t in tokenize.generate_tokens(okunur)
                     if t.type != tokenize.COMMENT)


def test_sinif_kaynagi_koda_gomulu_degil(sandbox_state):
    """KAYNAK ÇİVİSİ: `conservation_report` gövdesi `ARMED_SETUPS`e (ya da `strategy`ye) DOKUNMAZ.
    Bir gün biri 'kolay yol'u seçip bugünkü sabiti import ederse PIT ihlali sessizce geri gelir;
    davranış testleri o gün hâlâ yeşil olurdu (bugünkü sabitle bugünkü damga çoğu satırda aynı)."""
    kod = _kod_govdesi()
    assert "ARMED_SETUPS" not in kod, "korunum kovası bugünkü silah listesine bakıyor — PIT ihlali"
    assert "strategy" not in kod, "kova strateji modülüne bağlandı — silah yasası KAYITTAN okunmalı"
    assert "dormant_setup" in kod, "damga okuması kayboldu — sınıf başka bir kaynağa kaymış olabilir"


# ---------------- YASA 6: ALANLARIN OKUYUCUSU ----------------
def _sahte_rapor(**kon) -> dict:
    """`check_integrity_and_alarm`ın indekslediği altı anahtarı taşıyan asgari iskelet."""
    return {"production": {"starved": []}, "determinism": {"ok": True},
            "coherence": {"stale": []}, "monotonicity": {"regressions": []},
            "ownership": {"lost": []}, "parity": {"rows": []}, "divergence": {"ayrik": []},
            "conservation": {"ok": not kon.get("unexplained"), "plans": 9, "traded": 1,
                             "no_fill": 0, "replay_era": 0, "live_start": "2026-07-10",
                             "rows": [], "unexplained": 0, "uyuyan_kurulum": 0,
                             "uyuyan_olculemedi": 0, **kon}}


@pytest.fixture()
def _obs_yakala(monkeypatch):
    """obs'u YAKALA (no-op değil): alarm/log çağrıları listeye düşer, deftere hiçbir şey yazılmaz."""
    from meridian import obs
    kayit: list[tuple] = []
    monkeypatch.setattr(obs, "alarm", lambda tok, msg, **f: kayit.append(("alarm", tok, msg, f)))
    monkeypatch.setattr(obs, "log", lambda ev, **f: kayit.append(("log", ev, "", f)))
    monkeypatch.setattr(obs, "warn", lambda ev, **f: kayit.append(("warn", ev, "", f)))
    return kayit


def test_yasa6_korunum_alarmi_paydayi_tasir(sandbox_state, monkeypatch, _obs_yakala):
    """Alarm 'N plan kayıtsız kayboldu' diyorsa operatörün BİRLİKTE görmesi gereken iki sayı var:
    kaçı uyuyan-kurulum diye terminal sayıldı, kaçının tarihçesi OKUNAMADI. İkincisi olmadan
    'kayıtsız kayboldu' cümlesi fazla kesin olur — belki yalnız ölçemedik."""
    monkeypatch.setattr(w, "integrity_report",
                        lambda persist=False: _sahte_rapor(unexplained=3, uyuyan_kurulum=6,
                                                           uyuyan_olculemedi=2))
    w.check_integrity_and_alarm()
    alarmlar = [k for k in _obs_yakala if k[0] == "alarm" and k[3].get("kind") == "conservation"]
    assert len(alarmlar) == 1, "KORUNUM alarmı üretilmedi"
    msg, alanlar = alarmlar[0][2], alarmlar[0][3]
    assert "6" in msg and "2" in msg, f"payda alarm metninde yok: {msg}"
    assert alanlar.get("uyuyan_kurulum") == 6 and alanlar.get("uyuyan_olculemedi") == 2


def test_yasa6_ihlalsiz_dolu_kova_da_deftere_dusar(sandbox_state, monkeypatch, _obs_yakala):
    """`unexplained==0` iken alarm SUSAR — o hâlde kova sessizce 6 planı yeniden sınıflasaydı
    alanın okuyucusu kalmazdı (YASA 6 ihlali). Günlük turda bir kayıt satırı düşer."""
    monkeypatch.setattr(w, "integrity_report",
                        lambda persist=False: _sahte_rapor(unexplained=0, uyuyan_kurulum=6))
    w.check_integrity_and_alarm()
    satir = [k for k in _obs_yakala if k[0] == "log" and k[1] == "conservation_uyuyan_kovasi"]
    assert len(satir) == 1, "dolu kova hiçbir okuyucuya gitmedi"
    assert satir[0][3].get("uyuyan_kurulum") == 6
    assert not [k for k in _obs_yakala if k[0] == "alarm" and k[3].get("kind") == "conservation"]


def test_yasa6_bos_kova_gurultu_uretmez(sandbox_state, monkeypatch, _obs_yakala):
    """Sıfır bir olgu değildir: boş kova ne alarm ne kayıt satırı üretir (EEMUA bütçesi)."""
    monkeypatch.setattr(w, "integrity_report", lambda persist=False: _sahte_rapor())
    w.check_integrity_and_alarm()
    assert not [k for k in _obs_yakala if k[1] == "conservation_uyuyan_kovasi"]
