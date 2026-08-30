#!/usr/bin/env python3
"""spend_defter_duzeltmesi.py — ÜCRETSİZ KATMANIN UYDURMA MALİYETİNİN DEFTERDEN SİLİNMESİ.

NEDEN VAR — ÖLÇÜLEN VAKA (2026-08-27, canlı A1 `state/spend.jsonl`):
    10 çağrı   6.49 USD   nvidia/nemotron-3-super-120b-a12b:free
     3 çağrı   1.40 USD   nvidia/nemotron-3-ultra-550b-a55b:free
İkisi de OpenRouter ÜCRETSİZ katman; gerçek maliyet 0. Deftere ve panoya 7.89 USD UYDURULDU.
Kök neden `spend.price_for`ın alt-dizge tablosuydu ve KOD TARAFI KAPANDI (`:free` varyant
soneki; çivi `tests/test_ucretsiz_katman_fiyati_v325.py`).

KOD DÜZELTMESİ BU SATIRLARI ONARMAZ — YAPISAL, tercih değil: `dagit.sh` rsync'i `state/`i
DIŞLAR (`RSYNC_EXC`), yani dağıtım yalnız GELECEK satırları düzeltir. Diskteki satırlar
dağıtımdan sonra da aynen yanlış kalır ve `/api/spend` → pano onları okumaya devam eder.
Dahası `spend.over_budget()` üç ücretli yolu kapatır (`hermes.py`de claude bacağı, BEYİN
ZİNCİRİNİN TAMAMI, nous zinciri), yani harcanmamış para gerçek bir kapıyı besler.

NE YAPAR — DAR VE DENETLENEBİLİR:
  · YALNIZ `spend._is_free_variant` doğru olan VE `cost_usd > 0` olan satırlara dokunur.
  · `cost_usd`u `spend.estimate_cost(in_tokens, out_tokens, model)` ile YENİDEN HESAPLAR
    (bugünkü kuralla 0). Sabit 0 yazmaz — fiyat tablosu yarın değişirse doğru sayı çıksın.
  · Satıra `duzeltme` alanı yazar: eski değer + gerekçe + tarih + betik adı. SESSİZ DÜZELTME
    YOK — düzeltildiği yazılmayan bir sayı yine ölçülemeyen bir sayıdır (UYDURMA YASAĞI komşusu).
  · `ts` / `model` / `in_tokens` / `out_tokens` / `note` alanlarına DOKUNMAZ.
  · Satır EKLEMEZ, SİLMEZ. Değişmez: satır sayısı önce == sonra (yazımdan sonra doğrulanır).

NE YAPMAZ: emir göndermez, brokera dokunmaz, `state/`in başka hiçbir dosyasına yazmaz.

NEDEN NEGATİF TELAFİ SATIRI DEĞİL (reddedilen alternatif): append-only'i korurdu ama
`spend.summary()` satır SAYAR (`calls_this_month`) — 13 hayalet çağrı doğardı; ayrıca "maliyeti
−0.649 USD olan bir çağrı" ölçülmemiş bir olgudur. Uydurmayı uydurmayla kapatmak olurdu.

DEFTER DOSYA DEĞİL OLABİLİR: defterler 2026-07-31'de SQLite'a göçtü. Bu betik dosyaya DEĞİL
`store` üzerinden yazar (`store.write_jsonl` DB aktifse `storage.replace_rows`a yönlenir), yani
`state/spend.jsonl` bayat bir kalıntıysa bile doğru kaynağı onarır (`trades.jsonl` kalıntı
vakasının dersi, bkz. `store._bayat_defter_suzgeci`). Aynı sebeple YEDEK de MANTIKSALdır:
dosya kopyalamak yerine `store`dan OKUNAN satırlar bir `.bak-<damga>` dosyasına dökülür.

KULLANIM:
    python ops/spend_defter_duzeltmesi.py                 # KURU KOŞU (VARSAYILAN — yazmaz)
    python ops/spend_defter_duzeltmesi.py --uygula        # YAZ (worker DURMUŞ olmalı)
    python ops/spend_defter_duzeltmesi.py --uygula --zorla   # worker kapısını aş (CLAUDE.md §5)
    MERIDIAN_ROOT=/yol/kopya python ops/spend_defter_duzeltmesi.py --uygula   # kopyada dene

ÇIKIŞ KODU: 0 = ok (ya da yapacak iş yok) · 1 = doğrulama düştü · 2 = canlı worker koşuyor.

Çivi: tests/test_spend_defter_duzeltmesi_v331.py
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from meridian import config, ledgers, spend, store  # noqa: E402

DEFTER = "spend.jsonl"
NEDEN = ("ucretsiz_varyant_opus_fiyatina_yazilmisti — price_for alt-dizge tablosu `:free` "
         "slug'ini tutmuyordu ve muhafazakar varsayilana (Opus listesi) dusuyordu")
BETIK_ADI = "ops/spend_defter_duzeltmesi.py"


def _worker_running() -> bool:
    """Canlı Meridian süreci var mı? `sermaye`nin AYNI ölçümü — kopyalanmaz, çağrılır.
    (Testler bunu monkeypatch'ler; import edilemezse ölçemedik = koşuyor SAYMAYIZ ama
    kuru koşu zaten yazmaz, `--uygula` yolunda operatör `--zorla` ile bilinçli geçer.)"""
    try:
        from meridian.sermaye import _worker_running as _wr
        return bool(_wr())
    except Exception:            # YASA 4: sessiz-yutma DEĞİL — ölçülemedi, aşağıda ADIYLA basılır
        return False


def duzeltilecek(row: dict) -> bool:
    """Bu satır onarılmalı mı? İKİ ŞART BİRDEN: ücretsiz varyant VE sıfırdan büyük maliyet.

    İkinci şart bilinçli: zaten 0 olan bir satıra düzeltme damgası basmak, düzeltilmemiş bir
    şeyi düzeltilmiş göstermek olurdu. Zaten `duzeltme` taşıyan satır da atlanır — betik
    idempotenttir, ikinci koşu çift damga basmaz."""
    if "duzeltme" in row:
        return False
    if not spend._is_free_variant(str(row.get("model") or "").strip().lower()):
        return False
    try:
        return float(row.get("cost_usd", 0.0)) > 0.0
    except (TypeError, ValueError):   # YASA 4: cost_usd okunamıyorsa ONARIM KAPSAMI DIŞIDIR —
        return False                  # bilinmeyen bir değeri 0'a çekmek ölçmeden yazmak olurdu


def duzeltilmis(row: dict) -> dict:
    """Satırın onarılmış kopyası. Yalnız `cost_usd` değişir; `duzeltme` alanı eski değeri taşır."""
    yeni = copy.deepcopy(dict(row))
    eski = float(row.get("cost_usd", 0.0))
    yeni["cost_usd"] = spend.estimate_cost(int(row.get("in_tokens", 0) or 0),
                                           int(row.get("out_tokens", 0) or 0),
                                           str(row.get("model") or ""))
    yeni["duzeltme"] = {"eski_cost_usd": eski, "neden": NEDEN,
                        "tarih": dt.datetime.now(dt.timezone.utc).date().isoformat(),
                        "betik": BETIK_ADI}
    return yeni


def _yedek_yaz(rows: list[dict]) -> Path:
    """MANTIKSAL yedek: `store`dan okunan satırlar tek dosyaya dökülür (defter DB destekli
    olabilir; dosya kopyalamak bayat kalıntıyı yedeklemek olurdu)."""
    damga = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    yol = Path(config.STATE) / f"{DEFTER}.bak-{damga}"
    yol.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n"
                           for r in rows), encoding="utf-8")
    return yol


def _rapor(rows: list[dict], hedef: list[int], uygula: bool) -> None:
    print(f"=== spend defter düzeltmesi — {'UYGULA' if uygula else 'KURU KOŞU (varsayılan)'} ===")
    print(f"defter satırı: {len(rows)} · düzeltilecek: {len(hedef)}")
    if not hedef:
        print("düzeltilecek satır YOK — defter bu kural açısından temiz.")
        return
    toplam = 0.0
    ozet: dict[str, list[int]] = {}
    for i in hedef:
        r = rows[i]
        toplam += float(r.get("cost_usd", 0.0))
        ozet.setdefault(str(r.get("model")), []).append(i)
    for model, idx in sorted(ozet.items()):
        tut = sum(float(rows[i].get("cost_usd", 0.0)) for i in idx)
        print(f"  {len(idx):>4} satır  {tut:>9.4f} USD  {model}")
    print(f"  {'':>4}         {toplam:>9.4f} USD  TOPLAM (defterden düşecek uydurma maliyet)")
    if not uygula:
        print("\nHiçbir şey YAZILMADI. Uygulamak için: --uygula (canlı worker DURMUŞ olmalı).")


def _dogrula(once: list[dict], sonra: list[dict]) -> list[str]:
    """Yazımdan SONRA koşar. Kırmızı dönerse çıkış kodu 1 olur ve operatör yedekten döner."""
    h = []
    if len(once) != len(sonra):
        h.append(f"satır sayısı değişmezi KIRILDI: {len(once)} → {len(sonra)}")
    for r in sonra:
        ihlal = ledgers.validate_row(DEFTER, r)
        if ihlal:
            h.append(f"defter sözleşmesi ihlali: {ihlal} — {r.get('ts')}")
    kalan = [r for r in sonra if duzeltilecek(r)]
    if kalan:
        h.append(f"onarımdan sonra HÂLÂ {len(kalan)} düzeltilecek satır var")
    for a, b in zip(once, sonra):
        if (a.get("ts"), a.get("model"), a.get("in_tokens"), a.get("out_tokens")) != \
           (b.get("ts"), b.get("model"), b.get("in_tokens"), b.get("out_tokens")):
            h.append(f"ölçülmüş alan değişti: {a.get('ts')}")
    return h


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="spend.jsonl ücretsiz-katman maliyet onarımı")
    ap.add_argument("--uygula", action="store_true",
                    help="YAZ (varsayılan: kuru koşu — hiçbir şey yazılmaz)")
    ap.add_argument("--zorla", action="store_true",
                    help="canlı worker kapısını aş (CLAUDE.md §5 — bilinçli istisna)")
    # `argv=None` argparse'a "sys.argv'yi oku" demektir ve DOĞRU varsayılandır. İlk sürüm
    # `[] if argv is None else argv` yazıyordu: betik olarak koşulunca main() None alıyor,
    # parse_args([]) çağrılıyor ve KOMUT SATIRI TAMAMEN ATILIYORDU — yani `--uygula` sessizce
    # yok sayılıp betik hep kuru koşuyordu. Çiviler görmedi çünkü hepsi main([...])'i doğrudan
    # çağırıyordu; giriş noktasını sınayan çivi SD10'dur.
    a = ap.parse_args(argv)

    rows = [dict(r) for r in store.read_jsonl(DEFTER)]
    hedef = [i for i, r in enumerate(rows) if duzeltilecek(r)]
    _rapor(rows, hedef, a.uygula)

    if not a.uygula:
        return 0                       # KURU KOŞU: worker kapısı bile sorulmaz — yazım yok
    if not hedef:
        return 0                       # yapacak iş yok → yazım YOK (boş yazım da bir yazımdır)

    if _worker_running() and not a.zorla:
        print("\nREDDEDİLDİ: canlı Meridian süreci görülüyor. Worker koşarken deftere yazılmaz — "
              "aynı anda `spend.record` satır ekleyebilir ve tam-defter yazımı o satırı EZER "
              "(CLAUDE.md §5). Önce `./ops/stop-worker.sh`, sonra tekrar dene (ya da --zorla).",
              file=sys.stderr)
        return 2

    yedek = _yedek_yaz(rows)
    print(f"\nyedek: {yedek}")

    yeni = [duzeltilmis(r) if i in set(hedef) else r for i, r in enumerate(rows)]
    store.write_jsonl(DEFTER, yeni)

    sonra = [dict(r) for r in store.read_jsonl(DEFTER)]
    hatalar = _dogrula(rows, sonra)
    if hatalar:
        print("\n!! DOĞRULAMA DÜŞTÜ — yedekten dön: " + str(yedek), file=sys.stderr)
        for h in hatalar:
            print(f"   · {h}", file=sys.stderr)
        return 1

    ozet = spend.summary()
    print(f"\n{len(hedef)} satır onarıldı · doğrulama geçti.")
    print(f"ay özeti: spent={ozet['spent_usd']} USD · çağrı={ozet['calls_this_month']} · "
          f"bütçe aşımı={ozet['over_budget']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
