"""prescreen.py — hipotez ön-elemesi: adayları kapının KENDİ yasasıyla ölç, canlı state'e dokunma.

Ne yapar: "Bu düğme kapıdan geçer mi?" sorusunu canlı turu beklemeden, sabit ve tekrarlanabilir bir
araçla cevaplar. Elle yazılan ölçüm betikleri her seferinde biraz farklı oluyordu (farklı pencere,
farklı k_probes, farklı fold) — yani ölçüm aracının KENDİSİ turdan tura değişiyor ve iki turun
sonucu kıyaslanamıyordu; bu modül o aracı sabitler. Canlı state çalışma dizinine kopyalanır,
config.STATE/HISTORY/BARS kopyaya çevrilir (store çağrı anında okur → bütün yazımlar kuma iner);
koşu sonunda canlı state'in mtime parmak izi karşılaştırılıp rapora yazılır — "dokunmadım" bir
iddia değil, ÖLÇÜLMÜŞ bir olgudur.

Kilit girişler: `run(candidates, workdir, live, resume)` ölçümün gövdesi; CLI: `python -m
meridian.prescreen --candidates 'knob=deger,knob2=deger2' --workdir ...` (virgül = AYRI tek-değişkenli
adaylar), `--composite 'k1=v1;k2=v2|k3=v3'` bileşik adaylar ('|' adayları, ';' bir adayın
düğmelerini ayırır; ikisi birlikte verilebilir ve tek koşuda, aynı k_probes paydasıyla ölçülür),
`--resume` ölçülmüş adayları atlar, `--queue-id` bileşik kuyruk satırını ölçüm bitişinde damgalar
(`kuyruk_geri_yaz` → measured / measure_failed).

Değişmezler: (1) `run()` canlı state'e TEK BAYT yazmaz; tek adlandırılmış delik `--queue-id`
geri-yazımıdır — run() dışında, parmak izi alındıktan SONRA, config.STATE geçici olarak canlıya
çevrilerek tek satır damgalanır (yazılmazsa ölmüş süreçler sonsuza dek "ölçülüyor" görünürdü).
(2) Kapının yasası KOPYALANMAZ, ÇAĞRILIR: pencereler reflect._default_windows, parametreler
reflect.params_of, ölçüm backtest.walk_forward, hüküm reflect._gate_eval — ikinci bir yasa,
ön-elemenin GEÇTİ dediği adayın canlı kapıda kalması demekti. (3) `k_probes` DENENEN aday
sayısıdır ve `--resume` onu DEĞİŞTİRMEZ: süreç kazası kazananın-laneti cezasını gevşetemez;
bileşik aday kaç düğme çevirse de BİR yoklamadır, doğrulama ise düğme düzeyindedir
(guard.validate_change) ve tek düğme reddi adayın tamamını gerekçesiyle düşürür.
Okur: canlı state (kopyalamak için) + bar önbelleği; yazar: workdir'e prescreen_kismi.json /
prescreen_sonuc.json / canli_fingerprint.json, ve yalnız --queue-id ile composite_queue damgası."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import shutil
import sys
import time

# SAF YAPRAK — döngüsel bağımlılık yok, canlı state'e dokunmaz, yalnız damga üretir (WP-M 2026-08-02).
from . import olcum_araclari

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
    # Damga KOŞU BAŞINDA bir kez alınır: hem kısmi hem nihai rapora AYNI kimlik yazılsın (koşu
    # ortasında checkout yapılırsa iki rapor iki farklı SHA gösterirdi), hem de aday başına bir
    # `git` alt süreci koşmayalım.
    damga = olcum_araclari.kod_surumu_damgasi()
    # ÜRETİM ZAMANI, DAMGANIN İKİNCİ YARISI (WP-M, 2026-08-03). SHA "hangi kod" sorusunu
    # cevaplıyordu; "NE ZAMAN" sorusunun cevabı hâlâ raporun DIŞINDAYDI (dosya mtime'ı — kopyalanan,
    # rsync'lenen, arşivden çıkarılan bir raporda mtime YENİDEN YAZILIR ve sessizce yalan söyler).
    # Aynı SHA'da iki kez koşulmuş bir ön-eleme de yalnız SHA ile ayırt edilemez. Damgayla AYNI ANDA
    # ve TEK KEZ donar (kısmi + nihai rapor aynı koşuyu adlandırsın); koşunun bitişi `sure_s` ile
    # zaten yeniden kurulabildiği için ikinci bir bitiş damgası yazılmaz.
    uretim_zamani = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
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
        # BAŞARISIZ KOŞU DA DAMGALANIR (WP-M, 2026-08-03): bu dal `kuyruk_geri_yaz`ın hata yoluna
        # gider ve kuyrukta kalıcı bir satır bırakır. Damgasız bırakmak, "hangi bounds/kod hâlinde
        # reddedildi?" sorusunu cevapsız bırakırdı — guard redleri tam olarak kod/bounds değişince
        # anlam değiştiren kayıtlardır.
        return {"hata": "guard_hepsini_reddetti", "reddedilen": reddedilen,
                "n_denenen": len(adaylar),
                "kod_surumu": damga, "uretim_zamani": uretim_zamani}

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
             "k_probes": k_probes, "adaylar": adaylar, "kalan": kalan,
             "kod_surumu": damga, "uretim_zamani": uretim_zamani},
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
        # KOD-SÜRÜMÜ DAMGASI (WP-M, 2026-08-02): "bu rapor hangi kod hâliyle üretildi?" sorusu
        # bugüne kadar raporun DIŞINDA aranıyordu (dosya tarihi, oturum kaydı, hafıza) ve orada
        # tahmine dönüşüyordu. git HEAD + `kirli_agac` + ölçüm-araçları sürüm listesi artık raporun
        # İÇİNDE durur. Git yoksa/başarısızsa alan None + neden'dir (UYDURMA YASAĞI) — rapor yine
        # üretilir, çünkü damga bir ÖLÇÜM değil bir KİMLİKTİR ve yokluğu ölçümü geçersizleştirmez.
        "kod_surumu": damga,
        # ÜRETİM ZAMANI (UTC, koşu BAŞLANGICI — damgayla aynı anda dondu). `sure_s` ile birlikte
        # koşunun penceresi rapordan yeniden kurulur; dosya mtime'ına güvenmek gerekmez.
        "uretim_zamani": uretim_zamani,
        "workdir": str(workdir), "sure_s": round(time.time() - t0, 1),
    }
    (workdir / SONUC_DOSYA).write_text(json.dumps(rapor, indent=1, ensure_ascii=False))
    (workdir / FINGERPRINT_DOSYA).write_text(json.dumps({"before": before, "after": after,
                                                         "degisen": degisen}))
    log(f"[canlı state] değişen dosya: {degisen or 'YOK — tek bayt yazılmadı'}")
    return rapor


def kuyruk_ozeti(rapor: dict) -> dict:
    """Kuyruk satırına giren ÖZET — tam rapor DEĞİL, ama hükmü taşıyan alanların hepsi.

    NEDEN ÖZET: tam rapor (fold dizileri, guard redleri, parmak izi) kuyruk satırını onlarca kat
    büyütürdü ve kuyruk bir DURUM defteridir, bir ölçüm arşivi değil. Tam rapor `workdir`de durur ve
    özet ona İŞARET EDER (`workdir` alanı) — yani hiçbir bilgi kaybolmaz, yalnız yerinde kalır.

    NEDEN BU ALANLAR: `passes` hükmün kendisi; `para_delta`/`p` PARA-v3 yasasının KARAR değişkenleri
    (bileşik `delta` yalnız rapor metriğidir ve tek başına yazılırsa okuyucu onu hüküm sanır);
    `motor_isliyor` "düğme replay motorunda ölü mü" ön koşulu — False ise 'geçmedi' bir ÇÜRÜTME
    DEĞİLDİR; `pencere_id` habersiz kıyas yasağının taşıyıcısı (R0 sayısıyla R1 sayısı yan yana
    konamaz); `why` reddin gerekçesi. Ölçülemeyen alan None kalır ve None "0" demek DEĞİLDİR.

    KOD KİMLİĞİ ÖZETE DE GİRER (WP-M, 2026-08-03): tam damga (`kod_surumu`) `workdir`de kalır ama
    kuyruk satırını okuyan (pano/analytics) "bu sonuç hangi kodla, ne zaman üretildi?" sorusunu
    workdir'e gitmeden cevaplayabilmeli — kum havuzu silinmiş olabilir, satır kalıcıdır. Bu yüzden
    KISA sha + üretim zamanı özete kopyalanır; git ölçülemediyse alan None'dır (damganın kendi
    `git_neden`i tam raporda durur, burada tahmin yazılmaz)."""
    adaylar = rapor.get("adaylar") or []
    _damga = rapor.get("kod_surumu") or {}
    return {
        "n_aday": len(adaylar),
        "k_probes": rapor.get("k_probes"),
        "workdir": rapor.get("workdir"),
        "sure_s": rapor.get("sure_s"),
        "uretim_zamani": rapor.get("uretim_zamani"),
        "kod_surumu_kisa": _damga.get("git_head_kisa"),
        "kirli_agac": _damga.get("kirli_agac"),
        "pencere_id": (rapor.get("pencereler") or {}).get("pencere_id"),
        "adaylar": [{"knobs": a.get("knobs"), "passes": a.get("passes"),
                     "motor_isliyor": a.get("motor_isliyor"),
                     "inc_oos": a.get("inc_oos"), "cand_oos": a.get("cand_oos"),
                     "delta": a.get("delta"), "para_delta": a.get("para_delta"),
                     "p": a.get("p"), "p_required": a.get("p_required"),
                     "dd_durum": a.get("dd_durum"), "gate_law": a.get("gate_law"),
                     "yasa_surumu": a.get("yasa_surumu"),
                     "why": (a.get("why") or "")[:240]} for a in adaylar],
        "guard_reddi": [{"knob": g.get("knob"), "reasons": g.get("reasons")}
                        for g in (rapor.get("guard_reddi") or [])],
    }


def kuyruk_geri_yaz(queue_id: str, live: pathlib.Path, rapor: dict) -> dict | None:
    """Ölçüm bitişini kuyruk satırına damgala (C14). Dönen: yazılan alanlar ya da None (yazılamadı).

    ASLA YÜKSELTMEZ: bir durum defterinin, tamamlanmış bir ölçümün raporunu düşürme yetkisi yoktur
    (YASA 4: sessiz de kalmaz — uyarı defterine düşer). Rapor `--workdir`de zaten duruyor.

    DAMGA ÖLÇÜMÜN GERÇEĞİNİ SÖYLER: sonuç üretildiyse `measured`; guard bütün adayları reddettiyse
    ya da süreç patladıysa `measure_failed` + `neden`. "Ölçüldü" demek, ölçüm YAPILMADIĞI hâlde
    halkayı kapanmış göstermek olurdu — kapanmış görünen açık bir halka, açık halkadan beterdir."""
    from . import config
    onceki = (config.STATE, config.HISTORY, config.BARS)
    try:
        # CANLI STATE'E GERİ DÖN: `run()` config.STATE'i sandbox kopyasına çevirdi ve `store` onu
        # ÇAĞRI ANINDA okur — geri çevirmeden yazsaydık damga /tmp'deki kopyaya düşer, kuyruğu okuyan
        # (analytics/nous_eval/evidence_pack) onu HİÇ görmezdi.
        config.STATE = pathlib.Path(live)
        config.HISTORY = pathlib.Path(live) / "history"
        config.BARS = pathlib.Path(live) / "bars"
        config.goal.cache_clear()
        config.bounds.cache_clear()
        from . import hermes_composite
        hata = rapor.get("hata")
        if hata:
            alanlar = {"neden": str(hata)[:200], "result": kuyruk_ozeti(rapor),
                       "olcum_k_probes": rapor.get("k_probes")}
            hermes_composite.mark(str(queue_id), "measure_failed", **alanlar)
            return {"status": "measure_failed", **alanlar}
        # `olcum_k_probes` AYRI ALAN: satırdaki `k_probes` H4 BÜTÇE dilidir ("bu satır bütçeden bir
        # yoklama yedi"); prescreen'in `k_probes`ı KAPI dilidir ("bu ölçümde kapıya kaç aday gitti").
        # Tek alana yazmak iki farklı sayacı sessizce birbirine çevirirdi.
        alanlar = {"result": kuyruk_ozeti(rapor), "olcum_k_probes": rapor.get("k_probes"),
                   "workdir": rapor.get("workdir")}
        hermes_composite.mark(str(queue_id), "measured", **alanlar)
        return {"status": "measured", **alanlar}
    except Exception as e:
        try:
            from . import obs
            obs.warn("composite_queue_writeback_failed", queue_id=str(queue_id),
                     error=f"{type(e).__name__}: {e}",
                     detail="bileşik ölçüm bitti ama kuyruk satırı damgalanamadı — satır 'measuring' "
                            "kalır ve gece kancasının pid yoklaması onu measure_failed yapar")
        except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok ve geri-yazım denemesi tamamlanmış ölçümün raporunu düşüremez
            pass
        return None
    finally:
        config.STATE, config.HISTORY, config.BARS = onceki
        config.goal.cache_clear()
        config.bounds.cache_clear()


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
    ap.add_argument("--queue-id", default=None,
                    help="bileşik öneri kuyruğu satır kimliği (C00001…) — ölçüm bitişinde o satır "
                         "'measured' damgalanır (öner→ölç→öğren halkasının kapanışı)")
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
    # ÇÖKME DE BİR AKIBETTİR: ölçüm patlarsa satır 'measuring' asılı kalırdı ve gece kancasının pid
    # yoklaması onu ancak ERTESİ gece damgalayabilirdi. Burada damgalanır, istisna AYNEN yükseltilir
    # (yutulmaz — çıkış kodu ve log'daki iz olduğu gibi kalsın). `BaseException`: SIGINT/SystemExit
    # ile sonlanan bir ölçüm de "sonuç yok" demektir ve satırın bunu söylemesi gerekir.
    try:
        rapor = run(adaylar, pathlib.Path(ns.workdir), pathlib.Path(live), resume=ns.resume)
    except BaseException as e:
        if ns.queue_id:
            kuyruk_geri_yaz(ns.queue_id, pathlib.Path(live),
                            {"hata": f"{type(e).__name__}: {e}"})
        raise
    if ns.queue_id:
        rapor["kuyruk_geri_yazim"] = kuyruk_geri_yaz(ns.queue_id, pathlib.Path(live), rapor)
    print(json.dumps(rapor, indent=1, ensure_ascii=False))
    return 0 if not rapor.get("hata") else 1


if __name__ == "__main__":
    sys.exit(main())
