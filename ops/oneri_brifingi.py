#!/usr/bin/env python3
"""oneri_brifingi.py — okunmamış İYİLEŞTİRME ÖNERİLERİNİN tek-mesajlık özeti.

NEDEN VAR (2026-08-27 ölçümü). `nous_eval.py` (1098 satır) telemetriden kanıt-atıflı yapısal
öneriler üretiyor ve `state/improvement_proposals.jsonl`a yazıyor — canlıda 16 öneri, sonuncusu
24 Ağustos. TESLİMAT YOLU YOK: hiçbir kod bu defteri okuyup operatöre iletmiyor. Sistem
düşünüyor ve kimse dinlemiyor.

ŞEKİL `alarm_backlog_digest.py`den KOPYALANDI ve bu bilinçlidir: kuru koşum varsayılan ·
boşken SESSİZ · teslimden sonra damga · teslim düşerse damga BASILMAZ (yarım teslim "teslim
edildi" sayılmaz). O şekil bu depoda zaten sınanmış; ikinci bir tasarım ikinci bir hata sınıfıdır.

OKUR: `state/improvement_proposals.jsonl` — ve ona ASLA YAZMAZ (öneri satırlarına dokunulmaz).
YAZAR (denetim 2026-08-29 düzeltmesi — bu satır kardeş betikten kopyalanmış ve "aynı dosyanın
DAMGA anahtarı" diyordu; YANLIŞTI, o `alarm_backlog_digest.py`nin şeklidir): damga AYRI bir
dosyada tutulur, `state/oneri_brifingi_damga.json` (`DAMGA_DOSYA`) — okunan defter JSONL'dir,
içine bir damga anahtarı KOYULAMAZ. İkinci yazım `state/events.jsonl`dir (`obs.log` ile
`oneri_brifingi_teslim` olayı). Teslimat: `meridian.notify.send` (scrub + teslim-hatası kaydı orada).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ops/ altından doğrudan koşulduğunda `meridian` paketi bulunabilsin. Bugün canlıda editable
# kurulum (`_editable_impl_meridian.pth`) bunu zaten sağlıyor — ama kardeş betik
# (`alarm_backlog_digest.py`) bu satırı taşıyor ve ikisini AYNI birim koşturuyor: bootstrap yalnız
# birinde olsaydı yeniden kurulmuş/bozulmuş bir .venv kadansın YARISINI öldürür, öteki yarısı
# çalışmaya devam ederdi — teşhis edilmesi en zor arıza şekli.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from meridian import memory, notify, obs, store  # noqa: E402

DEFTER = "improvement_proposals.jsonl"
DAMGA_DOSYA = "oneri_brifingi_damga.json"
DAMGA = "son_teslim"
LISTE_TAVANI = 8          # mesaj uzunluk zarfı — kalanlar sayıyla beyan edilir


def _ts_degeri(row: dict) -> str:
    """Satırın KULLANILABİLİR zaman damgası; alan yoksa/boşsa "" (UYDURULMAZ — ölçülemedi
    sayılır, bir şey İCAT edilmez)."""
    return str(row.get("ts") or "").strip()


def ozet_kur() -> dict:
    """(toplam, yeni, mesaj, not, en_yeni). `mesaj` boşsa teslim edilecek bir şey YOKTUR.

    TS'Sİ OLMAYAN SATIR SESSİZCE DÜŞÜRÜLMEZ (denetim bulgusu 2026-08-29). Eski karşılaştırma
    `ts > son_ts` ts'siz satırı ("" > "") HER ZAMAN False'a düşürüyordu — o satır ne ilk turda ne
    başka hiçbir turda bildiriliyordu, ama `toplam`a sayılmaya devam ediyordu: KALICI sessiz
    dışlama, tam da bu betiğin var oluş nedenine ("hesaplanan teslim edilir") aykırı. Düzeltme:
    ts'siz satır KOŞULSUZ `yeni`ye girer ve mesajda ölçülemediği açıkça işaretlenir (UYDURMA
    YASAĞI: eksik alan gizlenmez, beyan edilir) — düzeltilene kadar HER turda yeniden görünür;
    bu BİLİNÇLİDİR: veri kusurunu gizlemek kaybolmasından beterdir.

    `en_yeni` bu ÇAĞRININ gördüğü (`yeni` listesindeki) satırlardan, YALNIZ gerçek ts taşıyanlar
    üzerinden hesaplanır. ts'siz bir satır damganın `son_ts`ini ASLA GERİYE SARAMAZ: bildirilen
    satırların hiçbirinde gerçek ts yoksa `en_yeni` eski `son_ts`te KALIR (ilerlemez) — aksi
    hâlde `max()` boş kümede patlar ya da "" damganın gerçek sınırını SİLER, ki bu da zaten
    bildirilmiş TARİHLİ satırların bir sonraki turda `> son_ts` görünüp YENİDEN bildirilmesi
    demek olurdu (damganın "wedge"lenmesi). ts'siz satır zaten kendi koşulsuz kuralıyla bir
    sonraki turda da yakalanır — ayrı bir iz sürmeye gerek yok."""
    satirlar = [r for r in store.read_jsonl(DEFTER) if isinstance(r, dict)]
    damga = (store.read_json(DAMGA_DOSYA, {}) or {}).get(DAMGA) or {}
    son_ts = str(damga.get("son_ts") or "")
    yeni = [r for r in satirlar if not _ts_degeri(r) or _ts_degeri(r) > son_ts]
    if not yeni:
        return {"toplam": len(satirlar), "yeni": 0, "mesaj": "", "en_yeni": son_ts,
                "not": f"yeni öneri yok (defter {len(satirlar)}, damga {son_ts or 'hiç'})"}
    bas = [f"🧠 {len(yeni)} yeni iyileştirme önerisi (defter toplam {len(satirlar)})"]
    for r in yeni[:LISTE_TAVANI]:
        oncelik = r.get("oncelik")
        etiket = f"[{oncelik}] " if oncelik else ""
        ts_uyari = "" if _ts_degeri(r) else " [ts YOK — ölçülemedi, sıralama garantisiz]"
        bas.append(f"· {r.get('id')} {etiket}{r.get('alan')}: "
                   f"{str(r.get('oneri') or '')[:140]}{ts_uyari}")
    if len(yeni) > LISTE_TAVANI:
        bas.append(f"… ve {len(yeni) - LISTE_TAVANI} tane daha (state/{DEFTER})")
    ts_degerli = [_ts_degeri(r) for r in yeni if _ts_degeri(r)]
    en_yeni = max(ts_degerli) if ts_degerli else son_ts
    return {"toplam": len(satirlar), "yeni": len(yeni), "mesaj": "\n".join(bas),
            "en_yeni": en_yeni, "not": ""}


def damgala(o: dict) -> bool:
    """Teslim damgasını basar; damga gerçekten yazıldıysa True. `o` = GÖNDERİLEN mesajı üreten
    `ozet_kur()` enstantanesi.

    MODÜL DÜZEYİNE ÇIKARILDI (denetim 2026-08-29) — gerekçesi kardeş betikte (`alarm_backlog_
    digest.damgala`) tam metniyle yazılı: gövde `main()` içinde bir kapanıştı, `@sef` onu
    çağıramadığı için sözleşmenin ikinci bir kopyasını yazmak zorunda kalmıştı.

    KARDEŞİNDEN FARKLI ŞEY DAMGALAR ve bu ayrım korunur: alarm tarafı KÜMÜLATİF SAYACIN kapsanan
    değerini kendi sayaç dosyasının İÇİNE yazar; burada damga EN YENİ ZAMAN DAMGASIDIR ve AYRI bir
    dosyada durur (okunan defter JSONL'dir, içine bir damga anahtarı koyulamaz). İkisini aynı
    sanmak birini kalıcı olarak damgasız bırakırdı.

    `store.update_json` sözleşmesi: belgeyi YERİNDE değiştir ve True dön — yeni sözlük döndürmek
    sessizce hiçbir şey yazmaz. `en_yeni` GÖNDERİLEN mesajı üreten AYNI enstantaneden gelir; send
    SONRASI ikinci bir defter okuması YOK (denetim bulgusu 2026-08-29): eski kod burada deftere
    yeniden bakıyordu ve gönderim penceresinde (ağ POST'u sürerken) eklenmiş bir satırı, o satır
    hiç mesajda YOKKEN 'gördüm' diye damgalıyordu — yarı-teslim'in ikinci bir türü, yalnızca
    ledger okuma zamanlamasından doğan.

    Dönüş değeri kayıt dürüstlüğü içindir: çağıranlar "damgalandı" diye olay yazar; yazım
    gerçekleşmediyse o olay yazılmamalıdır."""
    def _yaz(d: dict) -> bool:
        d[DAMGA] = {"ts": memory.now_iso(), "son_ts": o["en_yeni"], "kapsanan": o.get("yeni")}
        return True

    belge = store.update_json(DAMGA_DOSYA, _yaz, {}) or {}
    return isinstance(belge.get(DAMGA), dict)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--uygula", action="store_true",
                    help="gönder + teslim damgası bas (varsayılan KURU KOŞU)")
    args = ap.parse_args(argv)

    o = ozet_kur()
    print(f"defter: {o['toplam']} · yeni: {o['yeni']}")
    if not o["mesaj"]:
        print(o["not"])
        return 0
    print("--- MESAJ ---")
    print(o["mesaj"])
    print("-------------")
    if not args.uygula:
        print("KURU KOŞU: gönderilmedi, damga basılmadı (--uygula ile gönderir)")
        return 0
    if not notify.configured():
        print("KANAL YOK: Telegram/webhook yapılandırılmamış — özet teslim EDİLEMEZ.")
        return 2
    if not notify.send(o["mesaj"]):
        print("GÖNDERİM DÜŞTÜ: damga basılmadı — sonraki koşum aynı yığını yeniden dener "
              "(yarım teslim 'teslim edildi' sayılmaz)")
        return 2

    damgala(o)          # gövde ve gerekçesi modül düzeyinde — tek uygulama, üç çağıran
    obs.log("oneri_brifingi_teslim", yeni=o["yeni"], toplam=o["toplam"], son_ts=o["en_yeni"],
            detail="okunmamış iyileştirme önerileri TEK özet mesajla teslim edildi ve damgalandı")
    print(f"TESLİM EDİLDİ ve damgalandı (yeni={o['yeni']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
