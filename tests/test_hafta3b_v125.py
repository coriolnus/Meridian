"""test_hafta3b_v125.py — HAFTA 3b + HERMES ETKİNLEŞTİRME (2026-07-30).

Bu turun çivileri. Beş grup, hepsi deterministik ve HİÇBİRİ canlı state'e YAZMAZ (canlı worker
koşuyor — yazan bir test onun defterini bozardı; yazma yolları `tmp_path` + MERIDIAN_ROOT ile
izole edilir ya da `apply=False` ile kuru çalıştırılır).

  ① BÜYÜKLÜK YASASI: PARA-v3 karar verir, ESKİ bileşik yasa gölgede kayda geçer (yön 2026-07-30'da
     TERSİNE döndü — blok başındaki gerekçeye bak).
  ② HERMES PAKETİ H1-H5: SYSTEM statik (AST), kanıt user-prompt yolundan, kuyruk tek-değişken
     yasasını KALDIRMIYOR, PROTECTED beşlisi asla gölgelenmiyor.
  ③ Y3 DÖRTLÜSÜ: dördü de default-off; VIX bacağı `veri_yok` ve UYDURMA YOK.
  ④ K1 DEVİRLERİ: MAE karnesi, ts-tabanlı otonomi sayımı, hotstate throttle, notify kablosu,
     shadow_variants sözleşmesi + süreli codelaw satırının KALDIRILMIŞ olması.
  ⑤ 2B: benchmark_relative blok-bootstrap'a geçti ve hüküm kayması BEYAN EDİLİYOR.
"""
from __future__ import annotations

import ast
import json
import pathlib

import pytest

from meridian import (analytics, codelaw, config, guard, hermes, hermes_composite, hotstate,
                      ledgers, notify, probgate, regime, score as score_mod, shadowlaw, skills)

SRC = pathlib.Path("meridian")


# ---- CANLI DEFTERLERİN SALT-OKUNUR KOPYASI (2026-07-30, hayalet-seans kapısı turu) --------------
# BULGU (tam suite): bu dosyanın başındaki "HİÇBİRİ canlı state'e YAZMAZ" beyanı iki testte
# TUTMUYORDU. `analytics.benchmark_relative()` ve pano yüzeyleri `sandbox_state` ALMADAN koşuyor,
# yani operatörün CANLI `state/`ini okuyorlardı: canlı `trades.jsonl` + canlı `state/bars/spy.csv`.
# Okuma o güne dek sessizdi, bu yüzden kimse fark etmedi. Bar zincirine takvim kapısı eklenince
# aynı okuma bir OLAY üretti (canlı spy.csv'de iki hayalet seans satırı var: 2018-11-22, 2025-05-26)
# ve olay canlı `events.jsonl`e düştü → conftest sızıntı bekçisi teardown'da ERROR verdi.
#
# HANGİSİ HATA: TESTİN KENDİSİ. Okuma yolunun canlıda kayıt üretmesi TASARIMDIR (sanctioned onarım
# görünür olmalı); testin operatörün canlı defterine dokunması ise hem sızıntı hem de DETERMİNİZM
# kusurudur — testin hükmü operatörün o anki verisine bağlı olurdu.
#
# NEDEN "sadece sandbox_state" YETMİYOR: boş bir kum havuzunda `trades.jsonl` yok → benchmark
# `None` döner → biri no-op'a, diğeri KALICI skip'e dönerdi. Her zaman atlayan bir test, geçtiğinde
# hiçbir şey KANITLAMAZ. Bu yüzden defterler kum havuzuna KOPYALANIR: test aynı şeyi ölçmeye devam
# eder, tek fark yazımların canlı dizine değil kopyaya düşmesidir.
# `events.jsonl` KOPYALANMAZ: bu yüzeylerin hiçbiri onu OKUMAZ, 8,8 MB'tır ve testin YAZIM hedefidir.
_CANLI = pathlib.Path(__file__).resolve().parent.parent / "state"


@pytest.fixture
def canli_defter_kopyasi(sandbox_state):
    """Canlı defterlerin kum havuzuna kopyası + SPY bar önbelleği. Canlı dizine HİÇBİR yazım yok."""
    import shutil
    for p in sorted(_CANLI.glob("*.json*")) + sorted(_CANLI.glob("*.yaml")):
        if p.name == "events.jsonl" or not p.is_file():
            continue
        try:
            shutil.copy2(p, sandbox_state / p.name)
        except OSError:  # sessiz-yutma: tek dosya okunamadı — kopya eksik kalır, test kendi ön koşulunu ayrıca sorar
            pass
    spy = _CANLI / "bars" / "spy.csv"
    if spy.exists():
        shutil.copy2(spy, sandbox_state / "bars" / "spy.csv")
    config.goal.cache_clear()
    config.bounds.cache_clear()
    return sandbox_state


def _goal():
    """ÖLÇÜM TABANI DONMUŞ (2026-08-13): bu dosya 3a **E raporunu** replike ediyor — o rapor
    2026-07-30'da `max_drawdown=0,08` dünyasında ölçüldü ve varyans payları (dusus≈0,82) o bütçenin
    sayıları. Operatör 2026-08-13'te bütçeyi 0,16'ya çıkardı; canlı goal okunsaydı payların TAMAMI
    kayardı (ölçüldü: dusus 0,8195→0,5486) ve donmuş bir tarihsel raporun replikasyonu operatörün
    risk iştahına bağlı hâle gelirdi. Tarihsel taban tarihsel kalır — yürürlükteki eşiğin doğru
    yayıldığı `test_dalga_w1_v216` (C1/C5) ve `test_para_yasasi_v127` tarafından ayrıca çivilidir."""
    return {**config.goal(), "max_drawdown": 0.08}


def _tohumla(st):
    """`sandbox_state` boş bir state verir; bileşik yolun bounds/goal'a ihtiyacı var.
    NOT: env+reload denenmiş ve ÇÖPMÜŞ — reload, monkeypatch env'i geri almadan ÖNCE koştuğu için
    modül global'i canlı state'e dönmüyordu ve SONRAKİ testler boş state görüyordu. Repo'nun
    `sandbox_state` fixture'ı doğru yoldur: yazma-koruması da onu tanır."""
    (st / "bounds.yaml").write_text(pathlib.Path("state/bounds.yaml").read_text())
    (st / "goal.yaml").write_text(pathlib.Path("state/goal.yaml").read_text())
    return st


# =================================================================================================
# ① BÜYÜKLÜK YASASI — 3b'de "v2 GÖLGEDE"ydi, **PARA-v3 ile YÖN TERSİNE DÖNDÜ** (2026-07-30)
#
# BU BLOK BİLİNÇLİ OLARAK GÜNCELLENDİ — ve neden güncellendiği burada yazılı olmak ZORUNDA.
# 3b turunda buradaki çiviler şunu tutuyordu: "karar ESKİ bileşik skordadır, v2 yalnız kayda geçer"
# (`extra["shadow_v2"]`, `law == "shadow_v2"`, `law_transition is False`). Operatör onayıyla
# (2026-07-30) yasa YENİDEN TASARLANDI: karar artık PARA-v3'te (`ΔS = ret_c_v3` farkı), ESKİ bileşik
# yasa GÖLGEye geçti (`extra["eski_yasa"]`).
#
# ESKİ ÇİVİLERİ OLDUĞU GİBİ BIRAKMAK EN KÖTÜ SEÇENEKTİ: yürürlükte OLMAYAN bir yasayı çivilerlerdi,
# yani testler yeşil kalırken kod başka bir şey söylerdi — bir çivinin verebileceği en zararlı
# yanlış güvence. Bu yüzden her çivi, YENİ yasayı AYNI SIKILIKTA tutacak biçimde yeniden yazıldı:
# çivilenen ŞEY (karar tek yerden gelir, gölge karara sızmaz, eksik veri uydurulmaz) korundu,
# çivilenen ADRES değişti. v2 rötuşunun ölçüm kaydını çivileyen test AYNEN kaldı çünkü o ölçüm
# hâlâ doğrudur ve v3'ün GEREKÇESİdir.
# =================================================================================================
def test_para_v3_karar_verir_eski_yasa_yalnizca_KAYDA_gecer():
    """ÇİVİ (yön tersine döndü): `passes` YALNIZ PARA-v3'ten gelir; ESKİ yasa kayda geçer, karara
    GİRMEZ. 3b'de bu testin adı `test_v2_karar_vermez...`di ve tam tersini çiviliyordu."""
    tr = [{"ts_open": f"2026-01-{(i % 28) + 1:02d}", "ts_close": f"2026-02-{(i % 28) + 1:02d}",
           "r_multiple": (1.5 if i % 3 else -1.0), "pnl_dollars": (300.0 if i % 3 else -200.0)}
          for i in range(40)]
    cand = [{**t, "pnl_dollars": t["pnl_dollars"] + 50.0} for t in tr]
    g = probgate.PairedProbabilisticGate(_goal(), n_boot=300)
    r = g.evaluate(tr, cand, "2026-01-01", "2026-03-01", k_probes=1)
    sh = r.extra.get("eski_yasa")
    assert sh is not None, "gölge hesap koşmadı — çift hesap yok"
    assert sh["decides"] is False and sh["law"] == "eski_yasa"
    # `passes` YALNIZ para p'sinden türer — gölge would_pass farklı olsa bile
    assert r.passes == bool((r.p or 0) >= r.p_required)
    alan = r.as_gate_fields("search")
    assert "search_eski_yasa" in alan, "eski yasanın hükmü kapı kaydına girmiyor"
    assert "search_passes" not in alan, "gölge alanı passes ailesine sızmış"
    # DAMGA: kaydı sonradan okuyan, p'nin HANGİ yasanın p'si olduğunu tahmin etmek zorunda kalmasın
    assert alan["search_yasa_surumu"] == shadowlaw.YASA_SURUMU == "para_v3"
    # ESKİ ADLAR GERİ GELMESİN: `shadow_v2`, artık var olmayan bir yasanın alan adıdır
    assert "shadow_v2" not in r.extra and "search_shadow_v2" not in alan


def test_ret_c_v3_30_gun_carpitmasi_YOK_ve_adlandirilmis_sabit():
    """PARA-v3'ün terimi: pay HAM bileşik getiri, payda PENCERE-EŞLENİK hedef.

    GÜNCELLEME GEREKÇESİ: 3b'nin `ret_c_v2`si payı YILLIKLANDIRIYORDU ((1+R)^(365/span) − 1). O da
    bir üs alma işlemidir ve uzun pencerede getiriyi ŞİŞİRİR (kısa pencerede söndürür) — yani
    çarpıtmayı kaldırmıyor, YÖNÜNÜ değiştiriyordu. v3'te pay hiç dönüştürülmez; ölçek yalnız
    PAYDAda yaşar. Sonuç: ret_c_v3 getiride DOĞRUSAL."""
    assert shadowlaw.ANNUAL_TARGET_RETURN == 0.25
    assert "yıllık" in shadowlaw.__doc__ and "%25" in shadowlaw.__doc__, "sabit gerekçesiz"
    # (1) BİR YILDA: pencere-eşlenik hedef tam yıllık hedefe eşittir → getiri/hedef birebir
    assert abs(shadowlaw.hedef_pencere(365.0) - 0.25) < 1e-12
    assert abs(shadowlaw.ret_c_v3(0.05, 365.0) - 0.05 / 0.25) < 1e-12
    # (2) PAYDA PENCEREYLE BÜYÜR (uzun pencerede daha çok para beklenir — indirgeme değil)
    assert shadowlaw.hedef_pencere(1274.0) > shadowlaw.hedef_pencere(365.0) > \
        shadowlaw.hedef_pencere(30.0)
    # (3) PAYDA DOĞRUSALLIK: getiri iki katına çıkarsa terim de iki katına çıkar (üs alma YOK).
    #     Eski yasa bunu YAPMIYORDU: (1+2R)^(30/span) ≠ 2·(1+R)^(30/span).
    a, b = shadowlaw.ret_c_v3(0.10, 1274.0), shadowlaw.ret_c_v3(0.20, 1274.0)
    assert abs(b - 2 * a) < 1e-12, "pay dönüştürülüyor — çarpıtma geri geldi"
    # (4) kıstırma [-1, +1] aynen
    assert shadowlaw.ret_c_v3(100.0, 365.0) == 1.0
    assert shadowlaw.ret_c_v3(-0.999, 365.0) >= -1.0
    assert shadowlaw.ret_c_v3(-1.0, 365.0) == -1.0
    # (5) ESKİ ÖLÇEKTEN GERÇEKTEN BÜYÜK: aynı getiri/aynı süre, canlı defterin penceresinde
    eski = ((1.0 + 0.16) ** (30.0 / 1274.0) - 1.0) / 0.07
    assert shadowlaw.ret_c_v3(0.16, 1274.0) > eski, "para terimi hâlâ eziliyor"


def test_para_v3_min_sample_altinda_None_doner_sifir_degil():
    """§4: bilinmeyen skor, vasat skor gibi okunamaz. (Ad değişti: `score_detail_v2` →
    `money_score_detail`; çivilenen davranış AYNI.)"""
    d = shadowlaw.money_score_detail([{"ts_open": "2026-01-01", "ts_close": "2026-01-05",
                                       "r_multiple": 1.0, "pnl_dollars": 100.0}], _goal())
    assert d["score"] is None, "bilinmeyen skor 0.0 gibi okunuyor (§4 ihlali)"
    assert shadowlaw.money_score([], _goal()) is None


def test_varyans_atamasi_hedefi_olcer_ve_tutmadigini_BEYAN_eder():
    """UYDURMA YASAĞI: v2 rötuşunun hedefi tutmadıysa çıktı bunu SÖYLER ve deneme sayısını beyan
    eder. BU TEST AYNEN KALDI: v2 ölçümü hâlâ doğrudur ve v3'e geçişin GEREKÇESİDİR — ölçülmüş bir
    olumsuz sonucu silmek, aynı denemeyi altı ay sonra yeniden yapmak demektir."""
    assert shadowlaw.V2_MONEY_SHARE_TARGET == 0.40
    assert shadowlaw.MEASURED_V2["target_met"] is False
    assert shadowlaw.MEASURED_V2["trials"] == len(shadowlaw.V2_WEIGHT_TRIALS) == 3
    assert shadowlaw.WHY_40_UNREACHABLE and "TUTMADI" in shadowlaw.WHY_40_UNREACHABLE
    # üç denemenin HİÇBİRİ hedefe ulaşmamış olmalı (ulaşan varsa sabit yanlış)
    assert all(pay < 0.40 for _, _, pay in shadowlaw.V2_WEIGHT_TRIALS)
    # ağırlıklar [0.5/0.3/0.2] bandının İÇİNDE kaldı
    for _, w, _ in shadowlaw.V2_WEIGHT_TRIALS:
        assert abs(sum(w) - 1.0) < 1e-9
        assert all(0.2 <= x <= 0.5 for x in w), "ağırlık bandın dışına çıktı"
    # v3'e geçişin BEYANI: rötuşun yetmediği kayıtta yazılı olmak zorunda
    assert "v3" in shadowlaw.MEASURED_V2["hukum"] and "YETMEDİ" in shadowlaw.MEASURED_V2["hukum"]


def test_donmus_TABAN_yalnizca_dusus_butcesini_pinler(monkeypatch):
    """ÇİVİ (2026-08-13, bütçe 0,08→0,16 turunun KALINTI kusuru): `_goal()` tarihsel tabanı
    dondururken goal'un YALNIZ `max_drawdown` anahtarını pinlemek ZORUNDA; geri kalanı CANLI kalır.

    NEDEN AYRI BİR ÇİVİ GEREKİYOR: "tarihsel ölçüm tarihsel goal'le okunsun" cümlesi, fikstürü bir
    gün 2026-07-30'un TÜM goal'una (hedef getiri, min_sharpe, min_sample) dondurmaya davet eder ve
    bu, tek satırlık masum bir "sadeleştirme" gibi görünür. O an bu dosyanın öbür çivileri — başta
    v3'ün TEK-TERİMLİLİĞİ — yürürlükteki yasayı okumayı bırakır ve yasa değişse bile yeşil kalır:
    ① bloğunun başında yazılı olan aynı zarar, yani bir çivinin verebileceği en kötü yanlış güvence.

    DONDURMANIN GEREKTİĞİ TEK ANAHTARIN BU OLDUĞU ÖLÇÜLDÜ (2026-08-13, aynı defter n=95/span=1274g,
    iki bütçe yan yana): `v3_paylar` = {1,0/0,0/0,0}, `para_payi_tek_terim` = True, `sd_dusus` =
    0,0348 ve `dd_veto_gurultunun_disinda` = True — HER İKİ bütçede de BİREBİR aynı. Yani öbür
    anahtarları dondurmanın ölçüsel bir gerekçesi YOK; bütçeye bağlı olan yalnız eski yasanın
    payları (dusus 0,8195→0,5486, çünkü `dd_c = kıs(1 − dd/max_dd)` varyansı 1/max_dd² ölçekler).

    NEDEN DEĞER KIYASI DEĞİL, SAHTE GOAL: ilk yazımı "canlı goal ile donmuş tabanı karşılaştır, tek
    fark max_drawdown olsun" biçimindeydi ve NEGATİF KONTROLDE DÜŞTÜ (2026-08-13): tüm goal'u
    bugünkü değerlerine donduran bir fikstür o çividen SESSİZCE geçiyor, çünkü donmuş literal ile
    canlı değer o gün eşit. Yani çivi ancak operatör o anahtarı değiştirdikten SONRA — yani iş
    işten geçtikten sonra — ısırırdı. Bu yüzden değer değil KÖKEN sınanır: `config.goal()` sahte bir
    sözlük döndürür ve pinlenmemiş HER anahtarın o sahte değeri taşıması beklenir."""
    sahte = {**config.goal(), "target_return_30d": 0.999, "min_sharpe": 9.9, "max_drawdown": 0.99}
    monkeypatch.setattr(config, "goal", lambda: sahte)
    donmus = _goal()
    assert donmus["max_drawdown"] == 0.08, "düşüş bütçesi pini kalkmış ya da başka değere kaymış"
    assert set(donmus) == set(sahte), "donmuş taban goal'un ANAHTAR KÜMESİNİ değiştiriyor"
    kayan = {k for k in sahte if donmus[k] != sahte[k]}
    assert kayan == {"max_drawdown"}, \
        f"düşüş bütçesi DIŞINDA da anahtar donmuş (canlı yasayı okumuyor): {sorted(kayan)}"


def test_varyans_atamasi_E_raporunu_replike_eder_ve_v3_TEK_TERIM():
    """E raporu ESKİ yasa için PARA %0,3 / düşüş %82 / Sharpe %17,7 ölçmüştü. Harness onu ÜRETMELİ
    — yoksa v3 ölçümünün TABANI doğrulanmamış olur.

    GÜNCELLEME GEREKÇESİ: alan adları `v1_shares/v2_shares` → `eski_paylar/v3_paylar` oldu ve ikinci
    çivi değişti: artık "v2 payı v1'den büyük" değil **"v3 payı TAM 1,0"** aranıyor. Bu bir hedef
    değil YAPISAL ÖZDEŞLİKtir (skor tek terimli), dolayısıyla skora bir gün ikinci bir bacak
    sızarsa pay 1,0'ın altına düşer ve bu çivi kırılır — yasanın tek-terimliliğinin bekçisi."""
    r = shadowlaw.variance_attribution(analytics._trades(), _goal(), n_boot=400)
    assert r is not None
    eski = r["eski_paylar"]
    assert eski["para"] < 0.02, f"eski yasa PARA payı E raporuyla uyuşmuyor: {eski}"
    assert eski["dusus"] > 0.70, f"eski yasa düşüş payı E raporuyla uyuşmuyor: {eski}"
    # YENİ YASANIN KENDİ ÇİVİSİ: PARA payı %100 — düşüş ve Sharpe skorda YOK
    assert r["v3_paylar"]["para"] >= 0.999, f"v3 tek terimli değil: {r['v3_paylar']}"
    assert r["v3_paylar"]["dusus"] == 0.0 and r["v3_paylar"]["sharpe"] == 0.0
    assert r["para_payi_tek_terim"] is True
    assert r["yasa_surumu"] == "para_v3"
    # DÜŞÜŞ VETOSU MARJININ TÜRETİM TABANI da aynı ölçümden gelir ve gürültünün DIŞINDA olmalı
    assert r["sd_dusus"] > 0 and r["dd_veto_margin"] > r["sd_dusus"], \
        f"düşüş vetosu kendi ölçüm gürültüsünün İÇİNDE ({r['dd_veto_margin']} vs {r['sd_dusus']})"
    assert r["dd_veto_gurultunun_disinda"] is True


def test_gecis_satiri_IKI_yasayi_ayri_ayri_OLCER_ters_cevirmez():
    """GÜNCELLEME GEREKÇESİ — BU BİR DÜRÜSTLÜK DÜZELTMESİDİR. 3b'nin `divergence_row`u TERS ÇEVRİM
    yapıyordu: kaydedilen p ve mean'den σ'yı geri çıkarıp v2 hükmünü MODELLE tahmin ediyordu. O
    meşruydu çünkü v2, v1'in tek terimini ölçekleyen bir PERTÜRBASYONdu (doğrusal → tersinir).
    v3 ise üç terimden İKİSİNİ ATIYOR; ΔS_v3, ΔS_eski'nin hiçbir doğrusal dönüşümü DEĞİLDİR ve tek
    bir bileşik sayıdan çıkarılamaz. Ters çevrim denemek UYDURMA olurdu → yol kapatıldı, tablo
    yalnız ÇİFT ÖLÇÜLMÜŞ kayıtları puanlar."""
    r = shadowlaw.gecis_satiri("test", p_v3=0.97, p_eski=0.62, p_required=0.90)
    assert r["basis"] == "olculdu_cift_hesap"
    assert r["verdict_v3"] is True and r["verdict_eski"] is False
    assert r["flip"] == "RET→GEÇER", "hüküm dönüşü etiketlenmiyor"
    # ters yön de etiketlenir
    r2 = shadowlaw.gecis_satiri("test2", p_v3=0.10, p_eski=0.95, p_required=0.90)
    assert r2["flip"] == "GEÇER→RET"
    # aynı hüküm → dönüş YOK
    assert shadowlaw.gecis_satiri("t3", 0.99, 0.99, 0.90)["flip"] == "YOK"


def test_gecis_satiri_eksik_veriyi_UYDURMAZ():
    """Çivilenen davranış 3b'dekiyle AYNI (eksik girdi → beyan, uydurma yok); yalnız fonksiyon adı
    ve alan adları yeni yasaya taşındı."""
    r = shadowlaw.gecis_satiri("veri yok", None, None, 0.80)
    assert r["verdict_v3"] is None and r["basis"] == "olculemedi"
    assert "TANIMSIZ" in r["note"], "ters çevrimin neden yapılmadığı satırda yazılı değil"
    # tek taraf ölçülmüşse de hüküm KIYASLANMAZ (yarım kanıtla dönüş iddia edilemez)
    yarim = shadowlaw.gecis_satiri("yarim", 0.95, None, 0.80)
    assert yarim["flip"] is None and yarim["basis"] == "olculemedi"
    # E raporunun P1-P3'ü mean_delta taşımıyor → satır görünür ama sayı YOK
    p1 = [c for c in shadowlaw.E_REPORT_CANDIDATES if c["etiket"].startswith("G3a P1")][0]
    assert p1.get("mean_delta") is None and p1.get("sigma_declared") is None


def test_gecis_tablosu_canli_defterden_kosar_ve_GECIS_BEYAN_EDER():
    """GÜNCELLEME GEREKÇESİ: 3b'de `law_transition is False` çivilenmişti ("yasa geçişi YAPILMADI").
    Geçiş YAPILDI; aynı alanın artık True olması çivilenir. `n_scored >= 10` çivisi DÜŞTÜ ve yerine
    dürüst olan geldi: geçiş öncesi kayıtların v3 hükmü ters çevrilemez, dolayısıyla puanlanabilir
    satır sayısı geçişten SONRA birikir — 15 eski kayıt `gecis_oncesi` olarak SAYILIR ve
    sayılmalarının kendisi bulgudur (retro damga yasağı)."""
    t = shadowlaw.divergence_table()
    assert t["law_transition"] is True and t["decides"] is True
    assert t["yasa_surumu"] == "para_v3" and t["gecis_tarihi"] == "2026-07-30"
    assert t["n_gecis_oncesi"] >= 1, "geçiş öncesi kayıtlar sayılmıyor — eksiklik görünmüyor"
    assert "Ters çevrim YOK" in t["model"]
    # her satır ya hüküm ya BEYAN taşır — sessiz satır YOK
    for r in t["gate_records"]:
        assert r.get("verdict_v3") is not None or r.get("basis") in ("olculemedi", "gecis_oncesi")
    # geçiş öncesi satırlar hüküm İDDİA ETMEZ
    for r in t["gate_records"]:
        if r.get("basis") == "gecis_oncesi":
            assert r.get("verdict_v3") is None and r.get("flip") is None


# =================================================================================================
# ② HERMES PAKETİ H1-H5
# =================================================================================================
def test_SYSTEM_statik_kalir_AST():
    """SYSTEM prompt'u SABİT bir dize olmalı: içine f-string/`+`/`.format()` girdiği gün önbellek
    (cache_control) her turda ıskalanır ve maliyet sessizce katlanır. H-paketinin TAMAMI
    user-prompt yolundan girer."""
    tree = ast.parse((SRC / "hermes.py").read_text())
    atama = [n for n in ast.walk(tree)
             if isinstance(n, ast.Assign)
             and any(getattr(t, "id", None) == "SYSTEM" for t in n.targets)]
    assert len(atama) == 1, "SYSTEM birden fazla yerde atanıyor"
    assert isinstance(atama[0].value, ast.Constant) and isinstance(atama[0].value.value, str), \
        "SYSTEM artık sabit bir dize DEĞİL — önbellek kırılır"
    # yeni kanıt adları SYSTEM'in İÇİNDE olmamalı (oraya girmiş olsalar statik dize kalırdı ama
    # her tur değişen içerik prompt'a kaçmış olurdu)
    for ad in ("dead_knob_families", "your_prediction_accuracy", "composite_queue"):
        assert ad not in atama[0].value.value, f"{ad} SYSTEM'e sızmış"


def test_H1_karne_tek_ciftte_SAYI_uydurmaz():
    b = analytics.prediction_accuracy_band()
    assert b["min_n"] >= 3
    if b["n"] < b["min_n"]:
        assert b["band"] is None and "ÖLÇÜLEMEDİ" in b["hukum"], \
            "yetersiz örneklemde bant SAYI uyduruyor"
    # yön isabeti büyüklük hatasından AYRI sayılır
    if b["n"]:
        assert b["yon_isabeti"] and set(b["yon_isabeti"]) >= {"dogru", "n", "oran"}


def test_H2_olu_aileler_ve_hic_onerilmemis_dugmeler_DINAMIK():
    f = analytics.dead_families()
    assert f["n_hipotez"] > 0
    # sayı SABİTLENMEZ: bounds'a satır eklendikçe payda büyür
    assert "/" in f["hic_onerilmemis_sayi"]
    payda = int(f["hic_onerilmemis_sayi"].split("/")[1])
    assert payda == len(config.bounds()), "hiç-önerilmemiş paydası bounds ile senkron değil"
    # ölü aile tanımı: >= eşik deneme VE 0 ship
    for ad, v in f["olu_aileler"].items():
        assert v["denendi"] >= analytics.DEAD_FAMILY_MIN_N and v["ship"] == 0
    assert "YASAK DEĞİL" in f["beyan"], "ölü aile bir yasak gibi sunulmuş (kapı tek hakem)"


def test_H2_rejim_eki_aileyi_bolmez():
    assert analytics._knob_family("entry.rs_rating_min@trend_up") == "entry.rs_rating_min"
    assert analytics._knob_family("exit.profit_target_r") == "exit.profit_target_r"


def test_kanit_paketi_ONCELIKLI_duser_ortadan_KESILMEZ():
    """Eski kod `dumps(pack)[:1400]` idi: (a) JSON ortadan kesiliyordu, (b) EN YENİ kanıt (tam
    olarak H1/H2 karnesi) her turda ilk düşen şeydi."""
    pack = {k: "x" * 400 for k in ("score_calibration", "component_ic", "shadow_model")}
    pack["your_prediction_accuracy"] = {"n_pairs": 1}
    pack["dead_knob_families"] = {"families": {}}
    out = hermes._render_pack(pack)
    govde = out.split("\n", 3)[-1].split("\n[NOT:")[0]
    d = json.loads(govde)                      # ORTADAN KESİLMEMİŞ → geçerli JSON
    assert "your_prediction_accuracy" in d and "dead_knob_families" in d, \
        "öncelik sırası korunmadı — karne yine ilk düşen şey"
    assert hermes.EVIDENCE_PRIORITY[0] == "your_prediction_accuracy"


def test_canli_kanit_paketi_H_paketini_TASIR():
    p = hermes.evidence_pack()
    for ad in ("your_prediction_accuracy", "dead_knob_families", "do_not_propose",
               "never_proposed_knobs"):
        assert ad in p, f"{ad} canlı kanıt paketine girmiyor"
    assert len(p) <= hermes.EVIDENCE_CAP + 400


def test_H3_bilesik_guard_tarafindan_REDDEDILMEZ_kuyruga_YONLENDIRILIR(sandbox_state):
    """Tek-değişken yasası KALKMADI: dönüş yine ok=False (canlıya girmez) ama neden
    `composite_pending_queue`dur — "more than one variable" değil.

    GUARD KUYRUĞA YAZMAZ. İlk yazımda buradan `enqueue` çağrılıyordu ve `test_gate_statistics_v74`
    haklı olarak kırmızıya döndü: guard'ın sert-zarf yasası o modülde hiçbir defter/ağ/LLM kanalı
    olmamasını çiviliyor. Yazımı ÇAĞIRAN (`reflect.submit`) yapar."""
    _tohumla(sandbox_state)
    v = guard.validate_change({"composite": {"stop_mode": 1, "stop_buffer_atr": 0.4}},
                              {}, config.bounds(), _goal(), [], 0)
    assert v.ok is False, "bileşik öneri CANLIYA geçti — tek-değişken yasası kalkmış"
    assert any("composite_pending_queue" in r for r in v.reasons)
    assert not any("one_variable_only" in r for r in v.reasons), "hâlâ çöpe atılıyor"
    # guard SAF: kuyruk dosyası OLUŞMAMIŞ olmalı
    assert not (sandbox_state / hermes_composite.QUEUE_FILE).exists(), \
        "guard deftere yazdı — sert zarf yasası (saf fonksiyon) ihlali"
    # yazımı ÇAĞIRAN yapar: reflect.submit'in guard-ret dalında enqueue çağrısı var
    rsrc = (SRC / "reflect.py").read_text()
    assert "hermes_composite.enqueue(" in rsrc, "kuyruk yazımı hiçbir çağırana bağlanmamış"
    assert "queued_composite" in rsrc, "bileşik statüsü rejected_by_guard'a yazılıyor (mezarlık kirlenir)"
    # ve enqueue GERÇEKTEN kuyruğa yazıyor
    res = hermes_composite.enqueue({"stop_mode": 1, "stop_buffer_atr": 0.4}, bounds=config.bounds())
    assert res["queued"] is True
    q = hermes_composite.queue_status(__import__("meridian.store", fromlist=["read_jsonl"])
                                      .read_jsonl("composite_queue.jsonl"))
    assert q["n_bekleyen"] == 1 and q["n"] == 1


def test_H3_bilesik_sekil_denetimi_bounds_disini_gecirmez():
    b = config.bounds()
    ok, nedenler = hermes_composite.validate_composite({"stop_mode": 1, "stop_buffer_atr": 0.44}, b)
    assert not ok and any("adım" in n for n in nedenler)
    ok2, n2 = hermes_composite.validate_composite({"stop_mode": 99}, b)
    assert not ok2
    ok3, n3 = hermes_composite.validate_composite({"bilinmeyen.knob": 1, "stop_mode": 1}, b)
    assert not ok3 and any("bounds" in n for n in n3)
    # tek düğme bileşik DEĞİLDİR
    ok4, n4 = hermes_composite.validate_composite({"stop_mode": 1}, b)
    assert not ok4 and any("tek düğme" in n for n in n4)


def test_H4_haftalik_butce_adlandirilmis_ve_asilamaz(sandbox_state):
    _tohumla(sandbox_state)
    assert hermes_composite.WEEKLY_PROBE_BUDGET == 3
    for _ in range(5):
        hermes_composite.enqueue({"stop_mode": 1, "stop_buffer_atr": 0.4}, bounds=config.bounds())
    alinan = sum(1 for _ in range(10) if hermes_composite._budget_take())
    assert alinan == hermes_composite.WEEKLY_PROBE_BUDGET, "bütçe aşıldı"
    r = hermes_composite.spawn_pending(limit=3, dry_run=True)
    assert r["spawned"] == [] and r["atlanan"], "bütçe dolu ama ölçüm başlatıldı"


def test_H4_spawn_prescreen_SOZLESMESINE_uyar(sandbox_state):
    """`;` bir adayın DÜĞMELERİNİ ayırır ve `--workdir` ZORUNLUdur (prescreen sözleşmesi)."""
    _tohumla(sandbox_state)
    hermes_composite.enqueue({"stop_mode": 1, "stop_buffer_atr": 0.4}, bounds=config.bounds())
    r = hermes_composite.spawn_pending(limit=1, dry_run=True)
    cmd = r["spawned"][0]["cmd"]
    assert "--composite" in cmd and "--workdir" in cmd
    arg = cmd[cmd.index("--composite") + 1]
    assert ";" in arg and "|" not in arg, "bileşik ayracı prescreen sözleşmesine uymuyor"


def test_H5_PROTECTED_besli_ASLA_otomatik_golgelenmez():
    r = skills.auto_shadow_from_evidence(apply=False)
    korunan = set(r["korunanlar"])
    assert korunan == set(skills.PROTECTED) and len(korunan) == 5
    for kova in ("uygulanan", "advisory", "atlanan", "motor_ici_esik_asan"):
        for satir in r[kova]:
            assert satir["skill"] not in skills.PROTECTED, "korumalı skill karara girdi"
    assert r["uygulandi_mi"] is False


def test_H5_esik_advisory_esiginden_SERT_ve_iki_katmanli():
    assert skills.AUTO_AVG_R <= -0.30 and skills.AUTO_CF_MIN_N >= 20
    assert skills.AUTO_MAX_PER_RUN == 1
    src = (SRC / "skills.py").read_text()
    blok = src.split("def auto_shadow_from_evidence")[1].split("\ndef ")[0]
    assert "apply_skill_action" in blok, "registry yazımı kilitli desenden GEÇMİYOR"
    # DOCSTRING/YORUM AYIKLANIR: gerekçe metni yasak deseni ALINTILIYOR (kasıtlı — neden yapılmadığını
    # anlatıyor). Çivi KODA bakar. AST ile: fonksiyon gövdesindeki gerçek çağrıları tara.
    fn = [n for n in ast.walk(ast.parse(src))
          if isinstance(n, ast.FunctionDef) and n.name == "auto_shadow_from_evidence"][0]
    yazimlar = [n for n in ast.walk(fn) if isinstance(n, ast.Call)
                and getattr(getattr(n.func, "attr", None), "__str__", str)() == "write_json"
                and any(getattr(a, "id", None) == "REGISTRY" for a in n.args)]
    assert not yazimlar, "registry DOĞRUDAN yazılıyor (kilit atlanmış)"


def test_H5_motor_ici_skill_kozmetik_bayrak_YAZMAZ():
    """Motor-içi bir skill'e `shadow` yazmak davranışı DEĞİŞTİRMEZ — sistem yapmadığı bir şeyi
    yaptığını kaydetmemeli. Kanıt eşiğini aşarsa AYRI kovada raporlanır."""
    r = skills.auto_shadow_from_evidence(apply=False)
    for satir in r["motor_ici_esik_asan"]:
        assert satir["skill"] in skills.ENGINE_IMPLEMENTED
        assert "DEĞİŞTİRMEZ" in satir["why"]
    for satir in r["uygulanan"]:
        assert satir["skill"] not in skills.ENGINE_IMPLEMENTED


def test_katalog_cf_katmanini_tasir():
    """H5'in kanıt eşiği cf katmanını okur; katalog onu düşürüyorsa mekanizma SESSİZCE hiç çalışmaz
    (bu turda tam olarak bu hata bulundu)."""
    kat = skills.catalog()
    assert kat and all("n_cf" in s and "cf_avg_r" in s for s in kat)


# =================================================================================================
# ③ Y3 DÖRTLÜSÜ — HEPSİ DEFAULT-OFF
# =================================================================================================
def test_Y3_dort_knob_bounds_ta_var_ve_varsayilan_KAPALI():
    b = config.bounds()
    # `regime.spy_sma_gate` BU LİSTEDE DEĞİL: EDG-005 ile EMEKLİ (gösterge, kapı değil) ve karar
    # yolunda karşılığı yok. Satır 8b6bbbc (2026-08-01) ile bounds'tan DÜŞTÜ ve YOKLUĞU artık
    # çivili — ama BU dosyada değil: `tests/test_altyapi_kucukler_v172.py::
    # test_wpg_bounds_ta_spy_sma_gate_SATIRI_YOK`. Burada ölçülen şey ETKİSİZLİĞİDİR
    # (test_Y3_sma_gostergesi_yeni_girisi_KAPATMAZ) — yani satır bir gün geri gelse DAHİ karar
    # yolunun değişmediği. İki çivi AYRI KALIR: biri arama uzayını, diğeri karar yolunu korur.
    #
    # BAYAT GEREKÇE DÜZELTİLDİ (2026-08-02): bu blok eskiden yokluk assert'inden KAÇINIYORDU ve
    # gerekçesi "canlı dosya repodan bağımsız yaşar, çünkü o dizin versiyona girmez" idi. İddia
    # c783442'den beri YANLIŞ: `.gitignore` ölü-negasyon düzeltmesi `state/goal.yaml` ile
    # `state/bounds.yaml`ı GERÇEKTEN versiyona aldı. Kaçınmanın gerekçesi düşünce çivi kondu (v172).
    # NOT: yanlış gerekçenin bedeli, yanlış olduğu süre boyunca ÇİVİSİZ geçen bir emeklilikti.
    for k in ("regime.vix_backwardation_gate", "portfolio.sector_cap", "portfolio.heat_cap"):
        assert k in b, f"{k} bounds'ta yok"
        assert float(b[k]["min"]) == 0, f"{k} kapalı konumu (0) bounds'ta yok"
    # canlı strateji onları TAŞIMIYOR → canlı etki SIFIR (Batch L deseni)
    params = (config.load_strategy() or {}).get("params") or {}
    for k in ("regime.spy_sma_gate", "regime.vix_backwardation_gate",
              "portfolio.sector_cap", "portfolio.heat_cap"):
        assert not float(params.get(k, 0) or 0), f"{k} CANLI stratejide açık — default-off ihlali"


def test_Y3_kapali_knoblar_kapi_hukmunu_DEGISTIRMEZ():
    plan = {"sector": "Tech", "r_multiple_expected": 2.5, "size_r": 0.5, "score": 80,
            "notional": 90_000, "risk_dollars": 5_000}
    pf = {"open_positions": 1, "sector_counts": {}, "open_risk_r": 1.0, "max_corr": 0.1,
          "equity": 100_000, "sector_notional": {"Tech": 90_000}, "heat_pct": 20.0}
    reg = {"exposure_budget_pct": 80, "leading_sectors": []}
    v_kapali, _ = guard.classify_gate(plan, pf, reg, _goal(), params={})
    assert v_kapali == "GO", "knoblar kapalıyken bile hüküm değişti — default-off ihlali"
    v_acik, nedenler = guard.classify_gate(plan, pf, reg, _goal(),
                                          params={"portfolio.sector_cap": 25.0})
    assert v_acik == "NO_GO" and any("sektör tavanı" in n for n in nedenler)


def test_Y3_isi_tavani_olculemezse_UYGULANMAZ_ve_SESSIZ_KALMAZ():
    plan = {"sector": "Tech", "r_multiple_expected": 2.5, "size_r": 0.5, "score": 80}
    pf = {"open_positions": 1, "sector_counts": {}, "open_risk_r": 1.0, "max_corr": 0.1,
          "equity": 100_000, "heat_pct": None}
    reg = {"exposure_budget_pct": 80, "leading_sectors": []}
    detay = []
    guard.classify_gate(plan, pf, reg, _goal(), params={"portfolio.heat_cap": 6.0},
                        detail_out=detay)
    satir = [d for d in detay if d["check"] == "y3_heat_cap"]
    assert satir, "açık bir knob ölçüm yapamadı ve karar ağacında HİÇ görünmedi"


def test_Y3_VIX_veri_yok_ve_ORAN_UYDURULMAZ():
    ts = regime.vix_term_structure()
    assert ts["oran"] is None and ts["available"] is False and ts["reason"] == "veri_yok"
    assert "403" in ts["massive"] and "BOŞ" in ts["fmp"], "kaynak doğrulaması kayıtlı değil"
    g = regime.vix_backwardation_gate({"regime.vix_backwardation_gate": 1})
    assert g["enabled"] is True and g["blocks_new_entries"] is False, \
        "kaynak yokken kapı karar üretti (uydurma)"
    assert g["hukum"] is None


def test_Y3_spy_sma_isinma_dolmadan_HUKUM_URETMEZ():
    import pandas as pd
    kisa = pd.DataFrame({"close": [100.0] * 50})
    g = regime.spy_sma_gate(kisa, {"regime.spy_sma_gate": 1})
    assert g["hukum"] is None and g["blocks_new_entries"] is False
    assert "ısınma" in g["why"]


def test_Y3_zorla_tasfiye_YOK():
    import pandas as pd
    bars = pd.DataFrame({"close": [100.0 - i * 0.1 for i in range(260)]})
    eg = regime.entry_gates(bars, {"regime.spy_sma_gate": 1})
    assert eg["forced_liquidation"] is False
    assert eg["spy_sma_gate"]["forced_liquidation"] is False
    assert eg["vix_backwardation_gate"]["forced_liquidation"] is False
    src = (SRC / "regime.py").read_text()
    assert "zorla tasfiye YOK" in src


def test_Y3_sma_gostergesi_yeni_girisi_KAPATMAZ():
    """EDG-005 hükmü (2026-08-01): SMA bacağı GÖSTERGE, kapı DEĞİL.

    ÇİVİ ELDE KURULMUŞ `entry_gates` NESNESİYLE: knob 1 + endeks 200-SMA'nın ALTINDA + sözlük
    guard'a `entry_gates` anahtarıyla ELDEN verilmiş — yani kapının ateşlemesi için gereken her
    koşul sağlanmış hâlde. Hüküm yine de GO'dur, çünkü tüketici kaldırıldı. Eski test bu satırların
    NO_GO ürettiğini ölçüyordu; hükmü değişen bir yasanın çivisi de değişir, gevşemez."""
    import pandas as pd
    dusen = pd.DataFrame({"close": [200.0 - i * 0.3 for i in range(260)]})
    eg = regime.entry_gates(dusen, {"regime.spy_sma_gate": 1})
    assert eg["spy_sma_gate"]["hukum"] == "altinda"            # ÖLÇÜLDÜ (gösterge yaşıyor)
    assert eg["blocks_new_entries"] is False and eg["blocking"] == []
    plan = {"sector": "Tech", "r_multiple_expected": 2.5, "size_r": 0.5, "score": 80}
    pf = {"open_positions": 1, "sector_counts": {}, "open_risk_r": 1.0, "max_corr": 0.1}
    reg = {"exposure_budget_pct": 80, "leading_sectors": [], "entry_gates": eg}
    v, nedenler = guard.classify_gate(plan, pf, reg, _goal(),
                                      params={"regime.spy_sma_gate": 1})
    assert v == "GO" and not any("rejim kapısı" in n for n in nedenler)
    # ve knob'suz hâlle BİREBİR aynı hüküm (emekli düğme hiçbir yolu değiştirmez)
    reg_temiz = {"exposure_budget_pct": 80, "leading_sectors": []}
    assert guard.classify_gate(plan, pf, reg_temiz, _goal(), params={}) == (v, nedenler)


# =================================================================================================
# ④ K1 DEVİRLERİ
# =================================================================================================
def test_MAE_karnesi_kazanan_kaybeden_AYRI_olcer(sandbox_state):
    # `mae_profile` state'e YAZAR → sandbox'ta koşar (canlı defter operatörün kanıtı; test artefaktı
    # oraya düşerse üretim arızası gibi okunur — conftest bunu yakalıyor ve haklı).
    (sandbox_state / "trades.jsonl").write_text(pathlib.Path("state/trades.jsonl").read_text())
    m = analytics.mae_profile()
    assert m is not None and m["n"] >= analytics.MAE_MIN_N
    assert m["kazananlar"] and m["kaybedenler"], "tek ortalama iki soruyu gizliyor"
    assert m["kazananlar"]["n"] + m["kaybedenler"]["n"] == m["n"]
    assert "POZİTİF büyüklük" in m["birim"], "işaret sözleşmesi çıktıda yazılı değil"
    assert m["hukum"], "hüküm YOK — ölçüm tüketiciye bir şey söylemiyor"


def test_otonomi_sayimi_TS_TABANLI_satir_penceresi_DEGIL():
    src = (SRC / "analytics.py").read_text()
    blok = src.split("def autonomy_ladder")[1].split("\ndef ")[0]
    # YORUM SATIRLARI AYIKLANIR: gerekçe metni eski çağrıyı ALINTILIYOR (kasıtlı — neden
    # değiştiğini anlatıyor). Çivi KODA bakmalı, anlatıya değil.
    kod = "\n".join(l for l in blok.splitlines() if not l.strip().startswith("#"))
    assert "obs.recent(400)" not in kod, "satır penceresi hâlâ yerinde"
    assert "_breaker_trips_since" in blok
    n, pencere = analytics._breaker_trips_since(30)
    assert pencere["days"] == 30 and "kapsam" in pencere
    # pencere satır penceresinden ÇOK daha geniş olmalı (K1'in ölçtüğü sel yüzünden)
    assert pencere["n_scanned"] > 400 or pencere["oldest"] is None


def test_hotstate_DOWN_REASSERT_throttle_seli_keser(monkeypatch):
    from meridian import obs
    yazilan = []
    monkeypatch.setattr(obs, "warn", lambda ev, **f: yazilan.append((ev, f)))
    monkeypatch.setattr(obs, "alarm", lambda tok, msg, **f: yazilan.append(("ALARM", f)))
    monkeypatch.setattr(hotstate, "_LAST_DOWN_EMIT", 0.0, raising=False)
    hotstate._HEALTH["ok"] = True
    hotstate._HEALTH["reassert_suppressed"] = 0
    for _ in range(300):
        hotstate._note_down(ConnectionError("conn refused"))
    down = [x for x in yazilan if x[0] == "hotstate_down"]
    assert len(down) == 1, f"throttle çalışmadı — {len(down)} olay yazıldı (K1: 6.834/24s)"
    assert hotstate._HEALTH["reassert_suppressed"] == 299, "bastırılan sayılmıyor — GERÇEK kayboldu"
    assert hotstate.DOWN_REASSERT_S == 300, "streamhealth deseniyle aynı değer olmalı"


def test_hotstate_girdi_hatasi_sagligi_DUSURMEZ():
    """KURT MASALI YASAĞI korunuyor: TypeError/ValueError/KeyError Redis'i DOWN yapmaz."""
    hotstate._HEALTH["ok"] = True
    hotstate._note_down(ValueError("float(None)"))
    assert hotstate._HEALTH["ok"] is True


def test_notify_new_plan_loop_a_BAGLANDI():
    lp = (SRC / "loop.py").read_text()
    assert "notify.new_plan(" in lp, "K1-NOTU hâlâ bağlanmamış"
    # ham `send` metni kaldırılmış olmalı — aynı olguyu iki metin anlatmasın
    assert "yeni plan kuruldu" not in lp
    assert "HENÜZ BAĞLI DEĞİL" not in (SRC / "notify.py").read_text()


def test_shadow_variants_SOZLESMEDE_ve_codelaw_SURELI_satiri_KALDIRILDI():
    assert "shadow_variants.jsonl" in ledgers.CONTRACTS
    c = ledgers.CONTRACTS["shadow_variants.jsonl"]
    assert "k_variants" in c.required, "çoklu-karşılaştırma paydası zorunlu alan değil"
    assert c.writers == ("shadow_variants.py",)
    # SÜRELİ BEYAN KALDIRILDI: devri yapıldıysa satır listede DURAMAZ (stale_sinks kuralı)
    assert "shadow_variants.jsonl" not in codelaw.DECLARED_SINKS, \
        "süreli beyan işi bittikten sonra da yerinde — liste çöplüğe dönüyor"
    # ve DIŞ okuyucu gerçekten var
    assert "shadow_variants.jsonl" in (SRC / "analytics.py").read_text()


def test_composite_queue_SOZLESMESI():
    assert "composite_queue.jsonl" in ledgers.CONTRACTS
    c = ledgers.CONTRACTS["composite_queue.jsonl"]
    assert "composite" in c.required and "status" in c.required
    assert c.writers == ("hermes_composite.py",)


# =================================================================================================
# ⑤ 2B — BLOK BOOTSTRAP STANDARDI
# =================================================================================================
def test_2B_benchmark_blok_bootstrapa_gecti_ve_kayma_BEYAN_EDILIYOR(canli_defter_kopyasi):
    r = analytics.benchmark_relative()
    if r is None or r.get("ci") is None:
        pytest.skip("SPY kıyası ölçülemedi (endeks verisi yok) — bu çivi veri ister")
    assert "blok bootstrap" in r["ci"]["yontem"], "hâlâ IID"
    assert r.get("ci_iid_karsilastirma"), "eski yöntemin aralığı yok — kayma KANITSIZ"
    assert "hukum_kaymasi" in r, "hüküm kayması beyan edilmiyor (habersiz kayma yasağı)"
    # blok aralığı IID'den GENİŞ olmalı (bağımlılık kırılmadığı için)
    genis = (r["ci"]["hi"] - r["ci"]["lo"])
    iid = (r["ci_iid_karsilastirma"]["hi"] - r["ci_iid_karsilastirma"]["lo"])
    assert genis >= iid, "blok aralık IID'den DAR — bağımlılık yanlış modellenmiş"


def test_pano_yuzeyleri_JSON_guvenli(canli_defter_kopyasi):
    """Panonun okuduğu her yeni alan JSON'a serileşmeli (numpy sızması 500 döndürür).

    Defter kopyası ZORUNLU: numpy sızması boş girdide değil, GERÇEK satırlar üzerinde hesap yapılınca
    olur — kum havuzu boş bırakılsaydı test yeşil kalır ama sızmayı bir daha hiç göremezdi."""
    from meridian import api
    for ad, f in (("shadow_law", analytics.shadow_law_row),
                  ("hermes_scorecard", analytics.hermes_scorecard),
                  ("shadow_variants", analytics.shadow_variant_summary),
                  ("y3_entry_gates", api._y3_gate_row)):
        json.dumps(f(), ensure_ascii=False)      # AssertionError yerine TypeError fırlatır — kasıtlı


# =================================================================================================
# ⑤b 2C EMPİRİK BAYES + 2D HOLDOUT ROTASYONU
# =================================================================================================
def test_2C_kucultme_verdict_TABANLARINA_girmez():
    """ÇİVİ: küçültülmüş değer `edge_verdict`/`result_verdict`in tabanlarını DEĞİŞTİRMEZ. Küçültme
    n'i büyütmez; küçültülmüş sayıyı tabana sokmak örneklem yokluğunu istatistik hilesiyle örtmekti."""
    r = analytics.shrunk_regime_cells()
    assert "verdict TABANLARINA GİREMEZ" in r["beyan"]
    # verdict fonksiyonları küçültme fonksiyonlarını ÇAĞIRMAMALI
    src = (SRC / "analytics.py").read_text()
    for ad in ("def edge_verdict", "def result_verdict"):
        blok = src.split(ad)[1].split("\ndef ")[0]
        assert "shrunk_" not in blok, f"{ad} küçültülmüş değer okuyor — taban kaydı"


def test_2C_yetersiz_hucrede_KUCULTMEZ_ve_neden_soyler():
    r = analytics._empirical_bayes({"a": {"mean": 0.1, "n": 5}})
    assert r["kucultuldu"] is False and "tahmin EDİLEMEZ" in r["neden"]
    # küçültme yapılmadıysa ham = küçültülmüş (sessiz bir sahte küçültme YOK)
    assert r["hucreler"]["a"]["ham"] == r["hucreler"]["a"]["kucultulmus"]


def test_2C_tau2_sifirsa_TAM_kucultur():
    """τ²=0 ⇒ hücreler arasında ölçülebilir gerçek fark YOK ⇒ her hücre genel ortalamaya TAM çekilir.
    Dürüst cevap budur; kısmi küçültme ölçülmemiş bir fark iddia ederdi."""
    r = analytics.shrunk_regime_cells()
    if r.get("tau2") == 0.0 and r.get("kucultuldu"):
        genel = r["genel_ortalama"]
        for v in r["hucreler"].values():
            assert v["agirlik"] == 0.0 and abs(v["kucultulmus"] - genel) < 1e-9


def test_2C_component_ic_SEMASI_kaynaktan_dogrulandi():
    """Tahmin edilen bir şema 0 hücre verip 'küçültme yapılmadı' diyerek DOĞRU ama YANLIŞ NEDENLE
    dürüst kalıyordu (ilk koşuda yakalandı) — çivi hücrelerin GERÇEKTEN dolduğunu ister."""
    r = analytics.shrunk_component_ic()
    doc = json.loads(pathlib.Path("state/component_ic.json").read_text())
    beklenen = sum(1 for u in (doc["tablo"]["gercek"] or {}).values() if isinstance(u, dict)
                   for h in u.values() if isinstance(h, dict) and h.get("ic") is not None and h.get("n"))
    assert r["n_hucre"] == beklenen and beklenen > 0, "gerçek katman hücreleri okunmuyor"
    assert "cf hariç" in r["kaynak"], "cf katmanı havuza karışmış (farklı popülasyon)"


def test_2D_rotasyon_ONERIR_uygulamaz():
    r = analytics.holdout_rotation_advice()
    assert r["uygular_mi"] is False and "UYGULAMAZ" in r["beyan"]
    src = (SRC / "analytics.py").read_text()
    blok = src.split("def holdout_rotation_advice")[1].split("\ndef ")[0]
    for yasak in ("write_json", "update_json", "append_jsonl"):
        assert yasak not in blok, f"rotasyon değerlendiricisi state'e YAZIYOR ({yasak})"
    if r.get("oran") is not None and r["oran"] >= analytics.ROTATION_RECOMMEND_RATIO:
        assert r["oneri"] and r["oneri"]["maliyet"], "eşik aşıldı ama öneri/maliyet yok"
