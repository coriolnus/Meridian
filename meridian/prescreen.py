"""prescreen.py — HİPOTEZ ÖN-ELEMESİ: adayları KAPININ KENDİ YASASIYLA ölç, canlıya dokunma.
(Kârlılık Programı Aşama 2.6, 2026-07-29 — scratchpad'deki `onelem.py` deseninin kalıcılaştırılması)

NE İŞE YARAR. Bir hipotezi canlı döngüye sokmadan önce "kapıdan geçer mi?" sorusunun cevabı bugün
yalnız P5 turunu bekleyerek ya da elle bir script yazarak alınabiliyordu. Elle yazılan script her
seferinde biraz farklı oluyordu (farklı pencere, farklı k_probes, farklı fold) — yani ÖLÇÜM ARACININ
KENDİSİ turdan tura değişiyordu ve iki turun sonucu kıyaslanamıyordu. Bu modül o aracı sabitler.

ÜÇ SIKI KURAL — ÜÇÜ DE ÖLÇÜMÜN GEÇERLİLİĞİ İÇİN:

(1) CANLI STATE'E TEK BAYT YAZILMAZ. Canlı worker koşarken `walk_forward`/`reflect` yolundaki her
    yazım (`inc_cache.json`, `events.jsonl`, `sieve.json`, `score_calibration.json` ...) canlı
    deftere düşerdi. Çözüm: canlı `state/` çalışma dizinine KOPYALANIR ve `config.STATE/HISTORY/BARS`
    kopyaya çevrilir. `store._state()` config.STATE'i ÇAĞRI ANINDA okuduğu için bütün yazımlar
    kopyaya iner. Koşu sonunda canlı state'in mtime PARMAK İZİ karşılaştırılır ve rapora yazılır —
    "dokunmadım" bir iddia değil, ÖLÇÜLMÜŞ bir olgu olsun diye.

(2) KAPININ YASASI KOPYALANMAZ, ÇAĞRILIR. Pencereler `reflect._default_windows()`, parametreler
    `reflect.params_of`, ölçüm `backtest.walk_forward`, hüküm `reflect._gate_eval`. İkinci bir kapı
    yasası yazmak, ön-elemenin GEÇTİ dediği bir adayın canlı kapıda KALMASI (ya da tersi) demekti.

(3) `k_probes` DENENEN ADAY SAYISIDIR — ölçülen değil. `--resume` ile yarıda kalan bir koşu devam
    ettiğinde, daha önce ölçülmüş adaylar atlanır ama k_probes DEĞİŞMEZ. Kazananın-laneti cezası
    "bu turda kaç kapı yoklaması yaptık"a göredir; bir süreç kazası yüzünden cezayı düşürmek,
    istatistiksel çıtayı kazara gevşetmek olurdu (ve tam olarak böyle bir gevşetme fark edilmez).

KULLANIM:
    .venv/bin/python -m meridian.prescreen \
        --candidates 'entry.min_score=80,exit.breakeven_r=0.5' \
        --workdir /tmp/prescreen-001
    .venv/bin/python -m meridian.prescreen --candidates '...' --workdir /tmp/prescreen-001 --resume

Her aday TEK DEĞİŞKENdir (`knob=deger`), virgül ayraçlı liste AYRI adaylar demektir — birleşik bir
değişiklik değil. Tek değişken disiplini burada da geçerlidir: iki düğmeyi birlikte çeviren bir
ölçüm, hangisinin işe yaradığını söyleyemez.

BİLEŞİK ADAYLAR (`--composite`, 2026-07-30 — sadeleştirme turu ③). Tek-değişken disiplini bir ÖLÇÜM
kuralıdır, bir yasak değil: bazı hipotezler ancak iki düğme BİRLİKTE çevrildiğinde anlam taşır
(ör. "geniş stop + breakeven kapalı" ya da "hacim tabanını gevşet ↔ rvol tabanı koy" TAKASI). Bu
ölçüm bugüne dek scratchpad'de elle yazılan `g3a_bilesik.py` betiğiyle yapılıyordu — yani ölçüm aracı
yine turdan tura değişiyordu (modül başlığının çözdüğü sorunun aynısı, bir kat aşağıda). Artık kalıcı:

    .venv/bin/python -m meridian.prescreen \
        --composite 'stop_loss_atr_mult=3.0;exit.breakeven_r=0.0|entry.min_volume_ratio=1.0;entry.min_rvol=1.5' \
        --workdir /tmp/prescreen-bilesik

`|` ADAYLARI, `;` bir adayın DÜĞMELERİNİ ayırır. ÜÇ KURAL BİLEŞİKTE DE AYNEN GEÇERLİ:
  (1) Doğrulama DÜĞME DÜZEYİNDEdir: `guard.validate_change` her düğme için AYRI çağrılır (aralık +
      adım + tip). Bileşik olmak bir düğmeyi bounds dışına çıkarma ruhsatı değildir; bir düğme
      reddedilirse ADAYIN TAMAMI reddedilir ve hangi düğme yüzünden olduğu rapora yazılır.
  (2) `k_probes` YİNE ADAY SAYISIDIR — düğme sayısı değil. Bir bileşik aday kapıya BİR yoklama
      gönderir; düğme başına saymak kazananın-laneti cezasını sahte biçimde ŞİŞİRİRDİ.
  (3) Satır `bilesik=True` + `knobs={...}` taşır. Bir bileşik sonucu tek-değişkenli bir sonuç gibi
      okunursa "hangi düğme işe yaradı?" sorusunun cevabı YOK sanılır — oysa cevap "bu ölçüm onu
      sormadı"dır ve bunun satırda yazılı olması gerekir.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import sys
import time

KISMI_DOSYA = "prescreen_kismi.json"     # her adaydan SONRA yazılır (süreç ölürse ölçüm kaybolmasın)
SONUC_DOSYA = "prescreen_sonuc.json"
FINGERPRINT_DOSYA = "canli_fingerprint.json"


def _parse_deger(ham: str):
    """'80' → 80, '0.5' → 0.5, 'true' → True, 'pivot' → 'pivot'.

    SIRA ÖNEMLİ: int denemesi float'tan ÖNCE gelir, yoksa `min_score=80` düğmesi 80.0 olarak
    yazılır ve `guard`ın adım (step) kontrolü tam sayı bekleyen bir düğmede kayar."""
    s = ham.strip()
    dusuk = s.lower()
    if dusuk in ("true", "false"):
        return dusuk == "true"
    if dusuk in ("none", "null"):
        return None
    try:
        return int(s)
    except ValueError:  # sessiz-yutma: tip TESPİTİ — 'int değil' bir hata değil, sıradaki adaya (float) geçme sinyalidir
        pass
    try:
        return float(s)
    except ValueError:  # sessiz-yutma: tip TESPİTİ — sayı değilse değer DİZGİdir (ör. bir kategori düğmesi); guard zaten tipi/aralığı doğrular ve reddi gerekçesiyle rapora yazar
        return s


def parse_candidates(spec: str) -> list[tuple[str, object]]:
    """'a=1,b=2' → [('a',1), ('b',2)]. Biçimsiz parça SESSİZCE ATLANMAZ — patlar.

    Sessiz atlama burada özellikle tehlikeli: kullanıcı üç aday verdiğini sanır, ikisi ölçülür ve
    `k_probes` de ikiye düşer; yani hem eksik ölçüm hem gevşemiş çıta, ikisi de görünmeden."""
    out = []
    for parca in (spec or "").split(","):
        p = parca.strip()
        if not p:
            continue
        if "=" not in p:
            raise ValueError(f"aday biçimi 'knob=deger' olmalı, alınan: {p!r}")
        k, v = p.split("=", 1)
        k = k.strip()
        if not k:
            raise ValueError(f"aday adı boş: {p!r}")
        out.append((k, _parse_deger(v)))
    if not out:
        raise ValueError("en az bir aday gerekli (--candidates 'knob=deger')")
    return out


def parse_composite(spec: str) -> list[dict]:
    """`'a=1;b=2|c=3'` → [{'a':1,'b':2}, {'c':3}]. Her parça BİR bileşik adaydır.

    Biçimsiz parça yine PATLAR (tek-değişkenli yolla aynı gerekçe). Ek olarak: bir aday içinde AYNI
    düğme iki kez verilirse hata — `{'a':1,'a':2}` sessizce ikinciyi tutar ve kullanıcı çevirdiğini
    sandığı değeri hiç ölçmemiş olurdu. Tek düğmeli bir bileşik aday MEŞRUDUR (`--composite 'a=1'`):
    o hâlde ölçüm tek-değişkenlidir ve satır bunu `bilesik=True, n_knobs=1` ile söyler."""
    out = []
    for grup in (spec or "").split("|"):
        g = grup.strip()
        if not g:
            continue
        knobs: dict = {}
        for parca in g.split(";"):
            p = parca.strip()
            if not p:
                continue
            if "=" not in p:
                raise ValueError(f"bileşik düğme biçimi 'knob=deger' olmalı, alınan: {p!r}")
            k, v = p.split("=", 1)
            k = k.strip()
            if not k:
                raise ValueError(f"düğme adı boş: {p!r}")
            if k in knobs:
                raise ValueError(f"aynı adayda düğme iki kez verildi: {k!r} ({g!r})")
            knobs[k] = _parse_deger(v)
        if not knobs:
            raise ValueError(f"boş bileşik aday: {grup!r}")
        out.append(knobs)
    if not out:
        raise ValueError("en az bir bileşik aday gerekli (--composite 'k1=v1;k2=v2')")
    return out


def _normalize(candidates) -> list[dict]:
    """Tek-değişkenli (`[(k, v)]`) ve bileşik (`[{k: v}]`) girdiyi TEK iç biçime indirir.

    İki ayrı ölçüm gövdesi yazmak, bileşik yolun tek-değişkenli yoldan sessizce ayrışması demekti
    (aynı `_wf`, aynı `_gate_eval`, aynı `k_probes` kuralı geçerli olmalı). Anahtar (`key`) kısmi
    dosyanın/`--resume`ın dedup anahtarıdır ve DETERMİNİSTİKtir: düğmeler ada göre sıralı yazılır,
    yoksa aynı aday iki farklı sırada verildiğinde iki kez ölçülürdü."""
    out = []
    for c in candidates:
        if isinstance(c, dict):
            knobs = dict(c)
            out.append({"key": ";".join(f"{k}={knobs[k]}" for k in sorted(knobs)),
                        "knobs": knobs, "bilesik": True})
        else:
            k, v = c
            out.append({"key": k, "knobs": {k: v}, "bilesik": False})
    return out


def live_fingerprint(live: pathlib.Path) -> dict:
    """Canlı state'in mtime parmak izi. `bars/` HARİÇ: canlı worker bar dosyalarını kendi akışında
    sürekli tazeler; onları izlemek her koşuda sahte bir "değişti" listesi üretirdi. İzlenen şey
    BİZİM yazabileceğimiz defterlerdir."""
    out = {}
    for p in sorted(live.rglob("*")):
        if p.is_file() and "bars" not in p.parts:
            try:
                out[str(p.relative_to(live))] = p.stat().st_mtime_ns
            except OSError:  # sessiz-yutma: dosya tam o an worker tarafından döndürülüyor olabilir; parmak izi bir KANIT katmanıdır, eksik tek satır ölçümü düşürmez ve fark listesinde zaten görünür
                pass
    return out


def _sandbox(workdir: pathlib.Path, live: pathlib.Path) -> pathlib.Path:
    """Çalışma dizinindeki state kopyası (varsa YENİDEN KULLANILIR).

    Yeniden kullanım `--resume`un ön şartıdır: yeni bir kopya, önceki koşunun `inc_cache.json`ını
    da silerdi ve "atlanan" adaylar aslında yeniden ölçülürdü."""
    hedef = workdir / "state"
    if hedef.exists():
        return hedef
    workdir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(live, hedef, symlinks=False)
    return hedef


def _oku_kismi(workdir: pathlib.Path) -> dict:
    try:
        return json.loads((workdir / KISMI_DOSYA).read_text())
    except (OSError, ValueError):  # sessiz-yutma: kısmi dosya YOKSA ya da bozuksa devam etmenin tek dürüst yolu sıfırdan ölçmektir; --resume zaten "varsa atla" demek, "olmalı" değil
        return {}


def run(candidates: list[tuple[str, object]], workdir: pathlib.Path,
        live: pathlib.Path, resume: bool = False, log=print) -> dict:
    """Ön-elemeyi koş ve raporu döndür. `log` enjekte edilebilir (test sessiz koşsun diye)."""
    t0 = time.time()
    before = live_fingerprint(live)
    state = _sandbox(workdir, live)
    (workdir / FINGERPRINT_DOSYA).write_text(json.dumps({"before": before}))
    log(f"[sandbox] state kopyası: {state}")

    from . import config
    config.STATE = state
    config.HISTORY = state / "history"
    config.BARS = state / "bars"
    config.goal.cache_clear()
    config.bounds.cache_clear()

    from . import backtest, dataset, guard, reflect

    strat = config.load_strategy()
    inc_params = reflect.params_of(strat)
    ver = int(strat.get("version", 1))
    goal, bounds = config.goal(), config.bounds()
    w = reflect._default_windows()
    log(f"[taban] v{ver} · IS={w[0]} OOS={w[1]}→{w[2]} holdout={w[3]} folds={len(w[4])} embargo={w[5]}")

    # ---- GUARD: aday geçerli mi? (aralık + adım; bileşikte DÜĞME DÜZEYİNDE) --------------------
    adaylar = _normalize(candidates)
    gecerli, reddedilen = [], []
    for a in adaylar:
        nedenler = []
        for k, v in a["knobs"].items():
            ok = guard.validate_change({"variable": k, "new": v}, inc_params, bounds, goal, [], 0)
            if not ok.ok:
                # HANGİ DÜĞME yüzünden reddedildiği taşınır: bileşik bir adayda "reddedildi" tek
                # başına teşhis değildir, kullanıcı hangi düğmeyi düzeltmesi gerektiğini bilemez.
                nedenler.append({"knob": k, "yeni": v, "reasons": list(ok.reasons)})
        if nedenler:
            # `yeni` TEK DEĞİŞKENLİ REDDE KORUNUR (eski okuyucu/raporlar kırılmasın); bileşikte skaler
            # bir "yeni" yoktur → None, gerçek içerik `knobs`/`dugme_redleri`nde.
            reddedilen.append({"knob": a["key"], "bilesik": a["bilesik"],
                               "yeni": (None if a["bilesik"] else nedenler[0]["yeni"]),
                               "knobs": a["knobs"], "dugme_redleri": nedenler,
                               "reasons": [r for n in nedenler for r in n["reasons"]]})
        else:
            gecerli.append(a)
        log(f"[guard] {a['key']}  {'GEÇTİ' if not nedenler else 'RED ' + str(nedenler)}")
    if not gecerli:
        return {"hata": "guard_hepsini_reddetti", "reddedilen": reddedilen,
                "n_denenen": len(adaylar)}

    # K_PROBES BURADA DONDURULUR — `--resume` bu sayıyı DEĞİŞTİRMEZ (modül başlığı, kural 3).
    # Guard'ın reddettikleri sayılmaz: onlar kapıya hiç YOKLAMA göndermedi.
    k_probes = len(gecerli)

    kismi = _oku_kismi(workdir) if resume else {}
    olculmus = {a["knob"]: a for a in kismi.get("adaylar", [])} if resume else {}
    if olculmus:
        log(f"[resume] daha önce ölçülmüş {len(olculmus)} aday atlanacak "
            f"(k_probes={k_probes} DEĞİŞMEDİ)")

    bars, index = dataset.load()
    log(f"[veri] {len(bars)} sembol ({time.time() - t0:.1f}s)")

    def _wf(params):
        return backtest.walk_forward(params, bars, index, goal, w[0], w[1], w[2], w[3],
                                     strategy_version=ver, oos_folds=w[4], embargo_days=w[5],
                                     params_by_regime=strat.get("params_by_regime"))

    log("[ölçüm] incumbent…")
    inc = _wf(inc_params)
    inc_n = sum(int(f.get("n") or 0) for f in inc["oos_folds"])
    log(f"   incumbent OOS={inc['oos_score']} n={inc_n} folds={[f.get('n') for f in inc['oos_folds']]}")

    def _yaz_kismi(adaylar, kalan):
        (workdir / KISMI_DOSYA).write_text(json.dumps(
            {"incumbent": {"version": ver, "oos_score": inc["oos_score"], "n": inc_n,
                           "folds": [f.get("n") for f in inc["oos_folds"]]},
             "k_probes": k_probes, "adaylar": adaylar, "kalan": kalan},
            indent=1, ensure_ascii=False))

    sonuc = []
    _yaz_kismi(sonuc, [a["key"] for a in gecerli])
    for i, a in enumerate(gecerli):
        k = a["key"]
        if k in olculmus:
            log(f"[ölçüm] {k}: önceki koşuda ölçüldü — atlanıyor")
            sonuc.append(olculmus[k])
            _yaz_kismi(sonuc, [b["key"] for b in gecerli[i + 1:]])
            continue
        log(f"[ölçüm] {k} …")
        cand = _wf({**inc_params, **a["knobs"]})
        cand_n = sum(int(f.get("n") or 0) for f in cand["oos_folds"])
        # DAVRANIŞSAL ÖN KOŞUL: hiçbir fold'un işlem seti/skoru değişmediyse düğme replay motorunda
        # ÖLÜdür. Bunu ölçmeden "kapıdan geçmedi" demek, işlenmeyen bir düğmeyi çürütülmüş bir
        # hipotez sanmaktır — canlıda bu tuzağa bir kez düşüldü.
        etkili = ([f.get("n") for f in cand["oos_folds"]] != [f.get("n") for f in inc["oos_folds"]]
                  or [f.get("avg_r") for f in cand["oos_folds"]] != [f.get("avg_r") for f in inc["oos_folds"]]
                  or cand["oos_score"] != inc["oos_score"])
        passes, gate, why = reflect._gate_eval(inc, cand, k_probes=k_probes)
        it, ct = inc.get("oos_tail_risk"), cand.get("oos_tail_risk")
        kuyruk = ({"var_r": round(ct["var_r"] - it["var_r"], 4),
                   "cvar_r": round(ct["cvar_r"] - it["cvar_r"], 4)} if it and ct else None)
        delta = (None if (cand["oos_score"] is None or inc["oos_score"] is None)
                 else round(cand["oos_score"] - inc["oos_score"], 4))
        sonuc.append({
            "knob": k,
            # TEK DEĞİŞKENLİ SATIR BİÇİMİ KORUNDU (eski okuyucular kırılmasın): `eski`/`yeni` skaler
            # kalır. Bileşikte skaler bir "yeni" YOKTUR, o yüzden None olur ve gerçek içerik
            # `knobs`/`eski_knobs` alanlarında durur — uydurma bir tek-değişken görüntüsü yok.
            "eski": inc_params.get(k) if not a["bilesik"] else None,
            "yeni": a["knobs"][k] if not a["bilesik"] else None,
            "bilesik": a["bilesik"], "n_knobs": len(a["knobs"]), "knobs": dict(a["knobs"]),
            "eski_knobs": {kk: inc_params.get(kk) for kk in a["knobs"]},
            "motor_isliyor": bool(etkili),
            "inc_oos": inc["oos_score"], "cand_oos": cand["oos_score"], "delta": delta,
            "inc_n": inc_n, "cand_n": cand_n,
            "inc_folds": [f.get("n") for f in inc["oos_folds"]],
            "cand_folds": [f.get("n") for f in cand["oos_folds"]],
            "fold_wins": gate.get("fold_wins"), "fold_law": gate.get("fold_law"),
            "tail_delta": kuyruk, "tail_ok": gate.get("tail_ok"),
            "gate_law": gate.get("gate_law"), "k_probes": gate.get("k_probes"),
            "passes": bool(passes), "why": why, "margin": gate.get("margin"),
            # ---- PARA-v3 (2026-07-30): ÖN-ELEME ARTIK YASANIN GERÇEK SAYILARINI KAYDEDER ----
            # Bu satır bugüne dek yalnız BİLEŞİK `oos_score` farkını (`delta`) yazıyordu. O sayı
            # artık kapının KARAR değişkeni DEĞİL — bir RAPOR metriği. Kaydı olduğu gibi bırakmak,
            # ölçüm aracının yasadan geri kalması olurdu: rapor "Δ −0,03 → geçmez" der, oysa hüküm
            # PARA farkından ve P(ΔS>0)'dan gelir; hangi terimin reddettiği okunamaz hâle gelirdi
            # (modül başlığındaki "ölçüm aracı turdan tura değişmesin" ilkesinin ta kendisi —
            # değişen ölçüm aracı değil YASA olduğunda araç ONU izlemek zorundadır).
            "yasa_surumu": gate.get("yasa_surumu"),
            # PENCERE DAMGASI (HOLDOUT ROTASYONU R1, 2026-07-30): ön-eleme satırları tur raporlarına
            # elle taşınıyor ve orada başka turların sayılarıyla yan yana duruyor. Damgasız bir satır,
            # R0'da ölçülmüş bir Δ'yı R1 Δ'sıyla kıyaslamayı DAVET eder — pencere kimliği satırın
            # kendisinde durmak zorunda (rapor envelope'undaki `pencereler` bloğu satır kopyalanınca
            # geride kalıyor).
            "pencere_id": gate.get("pencere_id"),
            "inc_para": gate.get("incumbent_para"), "cand_para": gate.get("candidate_para"),
            "para_delta": (None if gate.get("candidate_para") is None
                           or gate.get("incumbent_para") is None
                           else round(gate["candidate_para"] - gate["incumbent_para"], 5)),
            "p": gate.get("search_p"), "p_required": gate.get("search_p_required"),
            "mean_delta": gate.get("search_mean_delta"),
            # DÜŞÜŞ VETOSU (tek yönlü) — hangi adayın hangi bacaktan kaldığı satırda görünsün
            "inc_dd": gate.get("incumbent_dd"), "cand_dd": gate.get("candidate_dd"),
            "dd_ok": gate.get("dd_ok"), "dd_durum": gate.get("dd_durum"),
            # ESKİ YASANIN GÖLGE HÜKMÜ — geçişin sürekliliği: aynı aday, iki yasa, ÇİFT ÖLÇÜM
            "eski_yasa_p": (gate.get("search_eski_yasa") or {}).get("p"),
            "eski_yasa_mean_delta": (gate.get("search_eski_yasa") or {}).get("mean_delta"),
            "eski_yasa_gecerdi": (gate.get("search_eski_yasa") or {}).get("would_pass"),
            "iki_yasa_ayni_hukum": (gate.get("search_eski_yasa") or {}).get("agrees_with_law"),
        })
        log(f"   OOS={cand['oos_score']} Δ={delta} folds={gate.get('fold_wins')} "
            f"kapı={'GEÇER' if passes else 'GEÇMEZ'} ({gate.get('gate_law')}) motor={etkili}")
        # PARA-v3 satırı AYRI basılır: bileşik Δ ile karar değişkeni aynı satırda yan yana durursa
        # okuyan ikisini karıştırır — hangisinin HÜKÜM verdiği yazılı olmak zorunda.
        log(f"   [yasa {gate.get('yasa_surumu')}] PARA {gate.get('incumbent_para')}→"
            f"{gate.get('candidate_para')} · P={gate.get('search_p')} "
            f"(gerekli {gate.get('search_p_required')}) · düşüş {gate.get('incumbent_dd')}→"
            f"{gate.get('candidate_dd')} [{gate.get('dd_durum')}] · eski yasa P="
            f"{(gate.get('search_eski_yasa') or {}).get('p')} "
            f"({'GEÇERDİ' if (gate.get('search_eski_yasa') or {}).get('would_pass') else 'REDDEDERDİ'})")
        _yaz_kismi(sonuc, [b["key"] for b in gecerli[i + 1:]])

    after = live_fingerprint(live)
    degisen = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    rapor = {
        "incumbent": {"version": ver, "oos_score": inc["oos_score"], "n": inc_n,
                      "folds": [f.get("n") for f in inc["oos_folds"]]},
        # k_probes = KAPIYA YOKLAMA GÖNDEREN ADAY sayısı. Bileşik bir aday, kaç düğme çevirse de
        # BİR yoklamadır (modül başlığı, bileşik kural 2).
        "k_probes": k_probes, "n_denenen": len(adaylar),
        "n_bilesik": sum(1 for a in adaylar if a["bilesik"]),
        "adaylar": sonuc, "guard_reddi": reddedilen,
        "pencereler": {"is_start": w[0], "oos_start": w[1], "oos_end": w[2], "holdout_end": w[3],
                       "folds": w[4], "embargo_days": w[5],
                       # PENCERE KİMLİĞİ + HABERSİZ KIYAS YASAĞI raporun İÇİNDE (R1, 2026-07-30):
                       # tarihler zaten yazılıydı ama "bu tarihler hangi rotasyon" ve "eski
                       # sayılarla kıyaslanamaz" cümleleri yazılı DEĞİLDİ — raporu okuyanın o
                       # çıkarımı kendi yapmasını beklemek, tam olarak habersiz kıyasın yolu.
                       "pencere_id": dataset.ROTATION_ID,
                       "rotasyon_tarihi": dataset.ROTATION_DATE,
                       "kiyas_uyarisi": dataset.PENCERE_KIYAS_UYARISI},
        # CANLI STATE KANITI RAPORUN İÇİNDE: "dokunmadım" iddiası, raporu okuyanın kontrol
        # edebileceği bir sayıya bağlanır. Boş liste = tek bayt yazılmadı.
        "canli_state_degisen_dosyalar": degisen,
        "workdir": str(workdir), "sure_s": round(time.time() - t0, 1),
    }
    (workdir / SONUC_DOSYA).write_text(json.dumps(rapor, indent=1, ensure_ascii=False))
    (workdir / FINGERPRINT_DOSYA).write_text(json.dumps({"before": before, "after": after,
                                                         "degisen": degisen}))
    log(f"[canlı state] değişen dosya: {degisen or 'YOK — tek bayt yazılmadı'}")
    return rapor


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="meridian.prescreen",
                                 description="Aday parametreleri kapının yasasıyla ön-ele "
                                             "(canlı state'e yazmaz).")
    ap.add_argument("--candidates", default=None,
                    help="'knob=deger,knob2=deger2' — her biri AYRI ve TEK değişkenli aday")
    ap.add_argument("--composite", default=None,
                    help="'k1=v1;k2=v2|k3=v3' — BİLEŞİK adaylar ('|' aday, ';' düğme ayracı). "
                         "Doğrulama düğme düzeyinde, k_probes yine ADAY sayısıdır.")
    ap.add_argument("--workdir", required=True, help="çalışma dizini (state kopyası burada durur)")
    ap.add_argument("--resume", action="store_true",
                    help="daha önce ölçülmüş adayları atla (k_probes DEĞİŞMEZ)")
    ap.add_argument("--live-state", default=None,
                    help="canlı state dizini (varsayılan: config.STATE)")
    ns = ap.parse_args(argv)
    if not ns.candidates and not ns.composite:
        ap.error("--candidates ya da --composite gerekli (ikisi birlikte de verilebilir)")

    # İKİSİ BİRLİKTE MEŞRU ve tek koşuda ölçülür: aynı incumbent, aynı pencereler, aynı k_probes
    # paydası. İki ayrı koşuda ölçmek, tek-değişkenli ve bileşik sonuçları farklı bir çoklu-
    # karşılaştırma paydasıyla üretip yan yana koymak olurdu.
    adaylar: list = []
    if ns.candidates:
        adaylar += parse_candidates(ns.candidates)
    if ns.composite:
        adaylar += parse_composite(ns.composite)

    from . import config as _cfg
    live = pathlib.Path(ns.live_state) if ns.live_state else _cfg.STATE
    rapor = run(adaylar, pathlib.Path(ns.workdir), pathlib.Path(live), resume=ns.resume)
    print(json.dumps(rapor, indent=1, ensure_ascii=False))
    return 0 if not rapor.get("hata") else 1


if __name__ == "__main__":
    sys.exit(main())
