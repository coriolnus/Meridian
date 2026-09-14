#!/usr/bin/env python3
"""ops/vault_sagligi.py — Vault sağlık bekçisi (TSK-064 Faz-2, Task 4).

NEDEN VAR. Mühürlenmiş bir kasa SESSİZ bir arızadır ve bu, Faz-2'nin tek yeni körlük sınıfıdır:
Vault mühürlenince Vault Agent render'ı durur, ama ÜRETTİĞİ DOSYALAR yerinde kalır. Tüketiciler
dosyayı okumaya devam eder, her şey çalışır GÖRÜNÜR — ta ki bir sır döndürülene kadar. O anda
eski değer canlıda kalır ve arıza, kasada değil uygulamada aranır. Bekçinin işi o sessizliği
kırmaktır.

Kurucu vaka sınıfı bu depoda zaten ölçüldü: "kurulu ≠ çalışır" (fail-notify H9'dan beri sessiz
arızalıydı, 2026-08-30) ve "canlılık ≠ ilerleme" (asılı-tick bekçisi). Buradaki ayrım üçüncüsü:
KASA AYAKTA ≠ SIR VEREBİLİYOR.

HÜKÜM TABLOSU — `GET <adres>/v1/sys/health`:

    200, 429   SAĞLIKLI   açık ve hizmette (429 = standby; tek düğümde beklenmez ama
                          Vault'un belgelenmiş sağlıklı kodudur ve onu arıza saymak
                          yanlış alarm üretirdi — yasanın en pahalı arızası)
    503, 501   VAULT_SEALED  kasa CEVAP VERİYOR ama sır VEREMİYOR (503 mühürlü, 501 hiç
                          init edilmemiş). İkisi de aynı operatör eylemini ister: mührü aç
                          / kasayı kur. Ayrım kaybolmaz: HTTP kodu olay gövdesinde taşınır.
    başka kod  VAULT_DOWN    tanınmayan bir cevap — adreste Vault olmayan bir şey olabilir
    bağlantı yok VAULT_DOWN  TCP/timeout arızası

ÇIKIŞ KODU HÜKÜMDÜR: 0 sağlıklı, 1 değil. systemd birimi bunu `failed`e çevirir.

OKUYUCU (Yasa 6) — üç tane, üçü de gerçek:
  1. `meridian/obs.py` olay defteri → pano alarm gelen kutusu + bildirim zinciri
     (`NOTIFY_TOKENS` ALARM_ sabitlerinden TÜRER, yani jeton doğduğu gün bildirilir);
  2. çıkış kodu → `vault-sagligi.service` birim durumu → `/api/infra` "arizali" sınıfı;
  3. operatörün eliyle koşumu (bu dosyanın kendi stdout satırı).

NEDEN `obs.alarm`, `obs.warn` DEĞİL (plandan BEYANLI SAPMA, 2026-09-14): `obs.warn`ın kendi
docstring'i "alarm DEĞİLDİR: bildirim zincirini tetiklemez" der. Mühürlü bir kasa, bütün sır
render'ının durduğu hâldir ve operatörü UYANDIRMASI gereken sınıftadır (tasarım §6.2 bunu
"VAULT_SEALED alarm sınıfı" diye adlandırır). `warn` seçilseydi jeton tanımlı ama ATEŞLENMEYEN
bir süs olurdu — "kurulu ≠ çalışır"ın tam olarak kendisi.

BU BETİK PYTEST DIŞINDA KOŞARSA CANLI DEFTERE YAZAR (CLAUDE.md §2): `obs` `state/events.jsonl`e
yazar. Yerelde elle koşum yerel defteri kirletir; koşum yeri A1'dir (timer), testte
`sandbox_state` fikstürü zorunludur.

KULLANIM:
    python ops/vault_sagligi.py                      # VAULT_ADDR ya da varsayılan loopback
    python ops/vault_sagligi.py --adres http://127.0.0.1:8200
    python ops/vault_sagligi.py --zaman-asimi 5
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys
import urllib.error
import urllib.request

KOK = pathlib.Path(__file__).resolve().parents[1]
# `sys.path` eklemesi ZORUNLU: betik depo kökünden `python ops/vault_sagligi.py` ile koşulur ve
# o hâlde kök `sys.path`te olmaz (emsal: ops/runbook_uret.py aynı satırı taşır).
sys.path.insert(0, str(KOK))
from meridian import obs  # noqa: E402 (yol eklemesinden SONRA)

#: Kasanın adresi — `deploy/vault/vault.hcl` listener'ıyla aynı. Ortamdan ezilebilir ki test
#: kendi sahte sunucusuna bakabilsin; varsayılan CANLI değerdir.
VARSAYILAN_ADRES = "http://127.0.0.1:8200"

#: Sağlık ucu — Vault'un belgelenmiş, KİMLİK İSTEMEYEN ucu. Jeton gerektiren bir uç seçilseydi
#: bekçinin kendisi bir sır taşımak zorunda kalırdı: bekçiyi korumak için bir sır daha.
SAGLIK_YOLU = "/v1/sys/health"

#: Sağlıklı kabul edilen HTTP kodları (Vault belgesi).
SAGLIKLI_KODLAR = frozenset({200, 429})

#: "Cevap veriyor ama sır veremiyor" kodları → VAULT_SEALED.
MUHURLU_KODLAR = frozenset({501, 503})

VARSAYILAN_ZAMAN_ASIMI = 5.0


def health_kodu(adres: str, zaman_asimi: float) -> tuple[int | None, str | None]:
    """(http_kod, hata) — ölçülemeyen kod `None`dur, 0 DEĞİL (uydurma yasağı).

    `urllib` 4xx/5xx'i istisnaya çevirir ama `HTTPError`ın kendisi bir cevaptır ve KODU taşır:
    503 tam olarak buradan gelir. Onu bir bağlantı arızasıyla aynı dala koymak, mühürlü bir
    kasayı "ulaşılamıyor" diye raporlamak olurdu — ve operatör yanlış yerde arardı."""
    url = adres.rstrip("/") + SAGLIK_YOLU
    try:
        with urllib.request.urlopen(url, timeout=zaman_asimi) as cevap:  # noqa: S310 (loopback)
            return int(cevap.status), None
    except urllib.error.HTTPError as e:
        return int(e.code), None
    except urllib.error.URLError as e:
        return None, f"{type(e).__name__}: {e.reason}"
    except OSError as e:
        # sessiz-yutma DEĞİL: hata metni çağırana DÖNER ve alarm gövdesine yazılır.
        return None, f"{type(e).__name__}: {e}"


def hukum(kod: int | None, hata: str | None) -> tuple[bool, str | None, str]:
    """(sağlıklı_mı, alarm_jetonu, insan_okunur_özet). Tablo dosyanın başındadır."""
    if kod is None:
        return False, obs.ALARM_VAULT_DOWN, f"kasaya ulaşılamadı ({hata})"
    if kod in SAGLIKLI_KODLAR:
        return True, None, f"kasa açık ve hizmette (HTTP {kod})"
    if kod in MUHURLU_KODLAR:
        ek = "mühürlü" if kod == 503 else "init EDİLMEMİŞ"
        return False, obs.ALARM_VAULT_SEALED, f"kasa {ek} — sır render'ı DURMUŞ (HTTP {kod})"
    return False, obs.ALARM_VAULT_DOWN, f"tanınmayan sağlık cevabı (HTTP {kod})"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--adres", default=os.environ.get("VAULT_ADDR", VARSAYILAN_ADRES),
                    help=f"kasa adresi (varsayılan: VAULT_ADDR ya da {VARSAYILAN_ADRES})")
    ap.add_argument("--zaman-asimi", type=float, default=VARSAYILAN_ZAMAN_ASIMI,
                    help="saniye")
    a = ap.parse_args(argv)

    kod, hata = health_kodu(a.adres, a.zaman_asimi)
    saglikli, jeton, ozet = hukum(kod, hata)

    if saglikli:
        obs.log("vault_saglik", durum="saglikli", http_kod=kod, adres=a.adres)
        print(f"[vault-sagligi] TAMAM — {ozet}")
        return 0

    # ALARM GÖVDESİ KENDİ KANITINI TAŞIR: HTTP kodu ve (varsa) bağlantı hatası olayın içindedir,
    # yani teşhis için journal'a geri dönmek gerekmez.
    obs.alarm(jeton, ozet, http_kod=kod, adres=a.adres, hata=hata)
    print(f"[vault-sagligi] {jeton} — {ozet}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
