#!/usr/bin/env python3
"""alarm_backlog_digest.py — kanal-öncesi biriken TESLİM EDİLMEMİŞ alarmların TEK-mesajlık özeti.

NEDEN VAR (2026-08-23 canlı pano ihlal triyajı, kalem 5). Bildirim kanalı yapılandırılmadan
(ya da kanal düşükken) üretilen her alarm `state/notify_undelivered.json` sayacına düşer
(gerçek dosya adı KODDAN ölçüldü: `obs._maybe_notify` iki dalı da bu adı yazar; "kanal yok"
ve "kanal bağlıyken teslim düştü" ayrı sayaçlar). Kanal sonradan açıldığında bu yığın kendi
kendine TESLİM EDİLMEZ: `_maybe_notify` yalnız YENİ alarmları iter, birikmiş yüzlercesi yerel
gelen kutusunda kalır. Yığını tek tek yeniden göndermek 300 bildirimlik bir spam olurdu
(alarm_delivery dersi: gürültüye karşı kurulan mekanizma gürültü üretemez) — bu betik yığını
TEK özet mesaja katlar (jeton×adet + ilk/son görülme), mevcut notify yolundan gönderir ve
teslim damgası basar.

DAMGA SÖZLEŞMESİ. Sayaçlar ASLA sıfırlanmaz ve azalmaz (kümülatif — test_alarm_delivery_v71
bunu çiviliyor; yapısal boşluğun tarihi kaybolmaz). Damga aynı dosyada `_digest` anahtarıdır:
{ts, toplam_kapsanan}. Alt çizgiyle başlar — jeton listesi basan yüzeyler (`watchdog.
parity_report`, olay metinleri) `_` önekli anahtarları zaten eler, yani damga hiçbir jeton
sayımını bozmaz. OKUYUCUSU (YASA 6): bu betiğin kendisi — yeniden koşum, damganın kapsadığı
toplamın ÜZERİNE yeni birikme yoksa mesaj GÖNDERMEZ (idempotens; "aynı yığını iki kez özetleme"
sınıfı). ACK'ye DOKUNULMAZ: `alerts_ack.json` operatörün "GÖRDÜM" beyanıdır, teslim onun yerine
geçemez ("ulaştı ≠ gördü").

İLK/SON ZAMANLAR ÖLÇÜLÜR, UYDURULMAZ: sayaç dosyası zaman taşımaz; ilk/son görülme
`events.jsonl`daki alarm satırlarından okunur. Defterde satırı kalmamış bir jeton için zaman
"ölçülemedi" yazılır (olay defteri o pencereyi artık taşımıyor olabilir) — sayı yine basılır.

KULLANIM:
    uv run python ops/alarm_backlog_digest.py             # KURU KOŞU: mesajı basar, göndermez
    uv run python ops/alarm_backlog_digest.py --uygula    # gönder + damga (kanal yoksa reddeder)
    MERIDIAN_ROOT=/yol/kopya ...                          # sandbox'ta dene

ÇIKIŞ KODU: 0 = gönderildi ya da gönderilecek yeni birikme yok · 1 = gönderim düştü (damga
basılmadı; sonraki koşum yeniden dener) · 2 = kanal yapılandırılmamış / sayaç okunamadı.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from meridian import memory, notify, obs, store  # noqa: E402

UNDELIVERED = "notify_undelivered.json"
DAMGA = "_digest"
MESAJ_TAVAN = 3500          # Telegram gövde sınırı 4096; tek mesaj sözü taşmayla bozulmasın


def _ilk_son(token: str, olaylar: list[dict]) -> tuple[str | None, str | None]:
    """Jetonun olay defterindeki İLK ve SON görülme zamanı; defterde satırı yoksa (None, None)."""
    ts = [str(e.get("ts") or "") for e in olaylar
          if e.get("level") == "alarm" and e.get("alarm") == token and e.get("ts")]
    return (min(ts), max(ts)) if ts else (None, None)


def ozet_kur() -> dict:
    """Yığını ölçer ve TEK mesajın metnini kurar; hiçbir bayt yazmaz, hiçbir şey göndermez."""
    d = store.read_json(UNDELIVERED, None)
    if not isinstance(d, dict):
        return {"hata": f"state/{UNDELIVERED} yok ya da okunamadı — özetlenecek yığın ölçülemedi"}
    toplam = int(d.get("_toplam") or 0)
    kapsanan = int(((d.get(DAMGA) or {}) if isinstance(d.get(DAMGA), dict) else {})
                   .get("toplam_kapsanan") or 0)
    # İMKÂNSIZ DURUM AYRI DALDIR (denetim 2026-08-29). `_toplam` yalnız ARTAN bir sayaçtır
    # (`meridian/obs.py` `_bump`/`_bump_fail` — azaltan tek bir yol yok), yani `kapsanan`ın onu
    # AŞMASI sözleşme ihlalidir: sayaç sıfırlanmış, dosya elle düzenlenmiş ya da eski bir
    # `notify_undelivered.json` geri yüklenmiştir. Bu dal olmasaydı `yeni` negatife düşer,
    # aşağıdaki `yeni <= 0` yakalar ve özet KALICI OLARAK susup sustuğunu "iyi huylu idempotens"
    # diye raporlardı — ölçülemeyen bir durumun iyi huylu bir hiçlik gibi görünmesi (UYDURMA
    # YASAĞI). Sıfır ile 'bilmiyorum' aynı şey değildir; çivi:
    # tests/test_brifing_kadansi_v327.py::test_DAMGA_SAYACI_ASARSA_IYI_HUYLU_HICLIK_GIBI_GORUNMEZ
    if kapsanan > toplam:
        return {"hata": f"damganın kapsadığı sayı ({kapsanan}) birikmiş toplamı ({toplam}) AŞIYOR — "
                        f"`_toplam` yalnız artan bir sayaçtır, bu durum sözleşme ihlalidir "
                        f"(sayaç sıfırlanmış / dosya elle düzenlenmiş / eski state geri yüklenmiş). "
                        f"Yığın ölçülemedi; damga elle düzeltilmeden özet güvenilmez."}
    yeni = toplam - kapsanan
    jetonlar = {k: int(v) for k, v in d.items()
                if not k.startswith("_") and isinstance(v, (int, float))}
    if yeni <= 0:
        return {"toplam": toplam, "kapsanan": kapsanan, "yeni": 0, "mesaj": None,
                "not": "damgadan beri yeni birikme yok — gönderilecek şey yok (idempotent)"}

    olaylar = store.read_jsonl("events.jsonl")
    satirlar = []
    for tok, n in sorted(jetonlar.items(), key=lambda kv: -kv[1]):
        ilk, son = _ilk_son(tok, olaylar)
        zaman = (f"ilk {ilk[:16]} · son {son[:16]}" if ilk else
                 "ilk/son ölçülemedi: olay defterinde satırı kalmamış")
        satirlar.append(f"• {tok} ×{n} ({zaman})")
    hata_n = int(d.get("_teslim_hatasi") or 0)
    govde = "\n".join(satirlar)
    mesaj = (f"📦 Meridian alarm backlog özeti — {toplam} teslim edilmemiş alarm "
             f"({yeni} tanesi son damgadan beri).\n{govde}\n"
             + (f"Not: {hata_n} tanesi kanal BAĞLIYKEN teslim edilememişti (uzak uç düşmüştü); "
                if hata_n else "Yığın kanal yapılandırılmadan önce birikti; ")
             + "tam liste panonun alarm gelen kutusunda. Bu TEK özet mesajıdır — "
               "alarmlar tek tek yeniden GÖNDERİLMEZ.")
    if len(mesaj) > MESAJ_TAVAN:
        mesaj = mesaj[:MESAJ_TAVAN - 60] + f"\n… (kesildi; {len(jetonlar)} jetonun tamamı panoda)"
    return {"toplam": toplam, "kapsanan": kapsanan, "yeni": yeni,
            "jeton_n": len(jetonlar), "mesaj": mesaj}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--uygula", action="store_true",
                    help="gönder + teslim damgası bas (varsayılan KURU KOŞU)")
    args = ap.parse_args(argv)

    o = ozet_kur()
    if o.get("hata"):
        print(o["hata"])
        return 2
    print(f"birikmiş toplam: {o['toplam']} · damganın kapsadığı: {o['kapsanan']} · yeni: {o['yeni']}")
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
        print("KANAL YOK: Telegram/webhook yapılandırılmamış — özet teslim EDİLEMEZ. "
              "Önce anahtarları gir (pano Ayarlar → Bildirim).")
        return 2
    if not notify.send(o["mesaj"]):          # scrub + teslim-hatası kaydı notify.send'in içinde
        print("GÖNDERİM DÜŞTÜ: damga basılmadı — sonraki koşum aynı yığını yeniden dener "
              "(yarım teslim 'teslim edildi' sayılmaz)")
        return 1

    def _damgala(d: dict) -> bool:
        """`store.update_json` sözleşmesi: belgeyi YERİNDE değiştir ve True dön (yeni sözlük
        döndürmek sessizce hiçbir şey yazmaz — obs._maybe_notify'ın kendi dersi). Sayaçlara
        DOKUNULMAZ: yalnız damga anahtarı güncellenir.

        `toplam_kapsanan` GÖNDERİLEN mesajı üreten AYNI `o` enstantanesinden gelir — burada `d`ye
        (kilit altındaki TAZE okuma) BAKILMAZ (denetim bulgusu 2026-08-29). Eski kod
        `int(d.get("_toplam"))` yazıyordu: mesajın kurulmasıyla damganın basılması arasında tam bir
        `events.jsonl` taraması VE bir ağ POST'u var, ve o pencerede `obs._maybe_notify`ın sayaca
        yazdığı her alarm, kendisinden HİÇ SÖZ ETMEYEN bir mesajla "kapsandı" damgası yerdi.
        Sayaçlar asla azalmadığı ve `yeni = toplam - kapsanan` olduğu için o alarm bir daha
        HİÇBİR özete giremezdi — kalıcı sessiz kayıp. Kardeş betikteki (`oneri_brifingi.py`
        `son_ts: o["en_yeni"]`) düzeltmenin birebir aynısı; çivi:
        `test_DIGEST_GONDERIM_PENCERESINDE_ARTAN_SAYAC_KACIRILMAZ`."""
        d[DAMGA] = {"ts": memory.now_iso(), "toplam_kapsanan": int(o["toplam"])}
        return True

    store.update_json(UNDELIVERED, _damgala, {})
    obs.log("alarm_backlog_digest_teslim", toplam=o["toplam"], yeni=o["yeni"],
            jeton_n=o.get("jeton_n"),
            detail="birikmiş teslim-edilmemiş alarmlar TEK özet mesajla teslim edildi ve damgalandı")
    print(f"TESLİM EDİLDİ ve damgalandı (toplam_kapsanan={o['toplam']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
