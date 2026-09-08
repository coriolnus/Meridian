#!/usr/bin/env python3
"""deploy/oracle-a1/dogrulama_anahtar.py — [5a] doğrulama-token anahtar kontrolü (A1'de koşar).

NEREDEN GELDİ. Gövde `dagit.sh`ın [5a] adımında İKİ KAT gömülüydü: bir `ssh bash -s <<'REMOTE'`
kabuk gövdesi ve onun içinde bir `python3 -c "…"` JSON kontrolü (dizge içinde dizge — kaçış
katmanı iki kat, tam olarak 2026-07-30 IndentationError vakasının sınıfı). TSK-176 Faz A1'de tek
dosyaya çıkarıldı: `deploy/ansible/dagit.yml` bunu `script:` ile koşturacak.

NEDEN VAR (TSK-148, dağıtım #13 vakası, 2026-09-04 20:04Z). healthz YALNIZ "200 döndü" der,
GÖVDEYİ doğrulamaz: token'sız istek de çoğu zaman 200 döner, gövdesi `{"detail": ...}` (yetkisiz
cevap) olur. Rol-1 elle doğrularken tam bunu yaşadı — token'sız `/api/alerts` çağrısı "pending
None" diye okundu (sahte "boş"). Sınıf, [5b]'nin "active ≠ yeni kod"unun uç-katmanı eşidir:
"200 döndü" ≠ "doğru gövde döndü".

A1'DE KOŞAR, STDLIB'DEN BAŞKA BİR ŞEY İSTEMEZ: `/opt/meridian`daki sanal ortam dev grubunu
taşımaz ([3] daraltması) ve bu betik `uv` çağrılmadan `python3 <yol>` ile koşabilmelidir.

KOMUT SATIRI SÖZLEŞMESİ:

    python3 deploy/oracle-a1/dogrulama_anahtar.py \\
        --uc '/api/alerts|pending|int' --uc '/api/hermes|learning.hayalet_suzulen_n|' [...]
        [--env-dosya /opt/meridian/.dash.env] [--taban http://127.0.0.1:8080]

Uç biçimi `<yol>|<nokta-ayraçlı-anahtar-yolu>|<beklenen-tip>`; tip BOŞSA yalnız anahtarın VARLIĞI
ölçülür (`equity_curve_beyani.tohum_siniri` ölçülü İSTİSNA: değeri canlıda GERÇEKTEN `None`
olabilir). Uç listesinin TEK KAYNAĞI `deploy/ansible/vars/dagit_vars.yml::dogrulama_uclari`.

ÇIKTI — satır başına bir uç: `VAR|<yol>|<anahtar>` ya da `YOK|<yol>|<anahtar>`.
ÇIKIŞ KODU:
    0  her uç VAR  → dağıtım sürer
    1  en az bir uç YOK (yetkisiz/eski gövde) → çağıran DÜŞER, beyan ([B]) YAZILMAZ
    0  + tek satır `OLCULEMEDI token yok` → FAIL-OPEN (aşağıda)
    1  + tek satır `OLCULEMEDI yonlendirme <kod>` → 3xx görüldü, ölçüm YOK (fail-closed, aşağıda)

FAIL-CLOSED / FAIL-OPEN AYRIMI BİLİNÇLİ. Anahtar eksikse [5b] gibi DÜŞER: "dağıtıldı" cümlesi
doğrulanamamış bir gövdeye dayanırdı. Token DOSYASI okunamazsa DÜŞMEZ — token yerel geliştirme
makinesinde de olmayabilir ve o durumda ölçüm YOKTUR, "ihlal" DEĞİLDİR (uydurma yasağı:
ölçülemeyen değer None + neden). Jeton dizgesi `OLCULEMEDI token yok` ÇAĞIRANIN SÖZLEŞMESİDİR —
tam eşitlikle karşılaştırılır, sessizce değiştirilemez.

SIR SÜZGECİ. Token DEĞERİ hiçbir çıktı satırına GİRMEZ (dagit çıktısı günlüğe kopyalanıyor ve sır
süzgeci yalnız beyaz-liste adları basar) — yalnız VAR/YOK hükmü döner. Uç GÖVDELERİ de sızmaz:
JSON süreç içinde ayrıştırılır, hiçbir yerde basılmaz. Token AĞDA da tek bir hedefe gider:
yönlendirme İZLENMEZ (aşağıda).

`curl` DEĞİL `urllib` (beyanlı taşıma farkı, ölçüldü 2026-09-08): kabuk gövdesi `curl -s -m 90 -H
"x-meridian-token: $T"` çağırıyordu. Aynı istek stdlib ile kurulur (GET + aynı başlık + 90 sn
zaman aşımı) ve tek dosya kuralı korunur; ayrıca yetkisiz cevabın gövdesi `curl`de olduğu gibi
OKUNUR (HTTPError gövdesi), yani 401/403 de "YOK" hükmüne aynı yoldan varır.

YÖNLENDİRME İZLENMEZ — İKİNCİ BEYANLI SAPMA (düzeltme turu 2, ölçüldü 2026-09-08). `curl -s`
çağrısında `-L` YOKTU: 3xx'te gövde boş dönüyor, hüküm "YOK" oluyor ve dağıtım duruyordu.
`urllib`in VARSAYILAN opener'ı ise yönlendirmeyi izler ve `x-meridian-token` başlığını
YÖNLENDİRMENİN HEDEFİNE taşır — `Location`da hangi host yazılıysa pano token'ı oraya gider ve
"kontrol tamamen A1'in içinde koşuyor" güvencesi orada biter (ölçüldü: iki yerel sunucu, hedefe
ulaşan başlıklar arasında token VARDI). Bu yüzden opener yönlendirmesizdir ve 3xx bir ÖLÇÜM
sayılmaz: `OLCULEMEDI yonlendirme <kod>` + çıkış 1 (fail-closed). Eski davranıştan tek farkı
operatörün okuduğu cümledir — ikisi de dağıtımı DURDURUR.

OKUYUCU (YASA 6): `dagit.sh` [5a] adımı · `deploy/ansible/dagit.yml` (Task 2) ·
`tests/test_ansible_dagit_v452.py` bölüm A4c.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

#: `.dash.env` içindeki token satırının anahtarı ve HTTP başlığı.
TOKEN_ANAHTAR = "MERIDIAN_DASH_TOKEN="
TOKEN_BASLIK = "x-meridian-token"
#: `/api/hermes` ağır olabilir — kabuk gövdesindeki `curl -m 90` ile aynı tavan.
ZAMAN_ASIMI_SN = 90
#: Token okunamadığında basılan jeton — ÇAĞIRAN BUNU TAM EŞİTLİKLE KARŞILAŞTIRIR.
OLCULEMEDI = "OLCULEMEDI token yok"
#: 3xx görüldüğünde basılan jetonun ÖNEKİ (arkasına durum kodu eklenir): `OLCULEMEDI yonlendirme 302`.
OLCULEMEDI_YONLENDIRME = "OLCULEMEDI yonlendirme"


class Yonlendirme(Exception):
    """3xx görüldü: token'ın taşınacağı İKİNCİ bir hedef var — ölçüm YAPILMAZ (fail-closed)."""

    def __init__(self, kod: int) -> None:
        super().__init__(kod)
        self.kod = kod


class _YonlendirmeYok(urllib.request.HTTPRedirectHandler):
    """Yönlendirmeyi İZLEMEYEN handler — `curl -s` (`-L` yok) davranışının karşılığı.

    `redirect_request` `None` döndüğünde urllib yeni istek KURMAZ ve 3xx cevabı hata zincirine
    düşer (`HTTPError`, kodu korunur). Böylece `x-meridian-token` başlığı `Location`daki hedefe
    ASLA taşınmaz. Gerekçe dosya başlığında; çivi `tests/test_ansible_dagit_v452.py` A4c6."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):    # noqa: D102 (urllib API)
        return None


#: Yönlendirmesiz opener — modül düzeyinde BİR kez kurulur, her uç aynı sözleşmeyle çağrılır.
_ACICI = urllib.request.build_opener(_YonlendirmeYok)


def token_oku(env_dosya: str) -> str:
    """`.dash.env`ten token DEĞERİNİ okur; okunamazsa boş dizge (fail-open kararı çağıranın)."""
    try:
        with open(env_dosya, encoding="utf-8") as f:
            for satir in f:
                if satir.startswith(TOKEN_ANAHTAR):
                    return satir[len(TOKEN_ANAHTAR):].strip().strip('"').strip("'")
    except OSError:  # sessiz-yutma DEĞİL: boş dönüş çağıranda `OLCULEMEDI token yok` olarak BASILIR
        return ""
    return ""


def govde_getir(taban: str, yol: str, token: str) -> dict | None:
    """Ucu çağır ve JSON gövdeyi döndür; ayrıştırılamazsa None (çağıran YOK hükmü verir).

    3xx'te `Yonlendirme` YÜKSELİR: yönlendirme izlenmediği için ölçüm YAPILAMAMIŞTIR ve bu
    "gövde bozuk" (YOK) ile aynı şey değildir — çağıran ayrı bir jeton basar."""
    istek = urllib.request.Request(f"{taban}{yol}", headers={TOKEN_BASLIK: token})
    try:
        with _ACICI.open(istek, timeout=ZAMAN_ASIMI_SN) as cevap:
            ham = cevap.read()
    except urllib.error.HTTPError as e:
        if 300 <= e.code < 400:
            # Yönlendirme İZLENMEDİ (token ikinci hedefe taşınmaz) — ölçüm yok, hüküm de yok.
            raise Yonlendirme(e.code) from None
        # `curl -s` gövdeyi durum kodundan bağımsız basar — yetkisiz cevap da AYRIŞTIRILIR ve
        # anahtar yokluğu üzerinden YOK hükmüne varır (davranış birebir).
        ham = e.read()
    except (urllib.error.URLError, OSError):
        # sessiz-yutma DEĞİL: bağlantı kurulamayan uç `YOK` hükmüne düşer ve çağıran DAĞITIMI DURDURUR
        return None
    try:
        veri = json.loads(ham)
    except (ValueError, TypeError):
        # sessiz-yutma DEĞİL: ayrıştırılamayan gövde `YOK`tur — çağıran bunu ihlal sayar ve düşer
        return None
    return veri if isinstance(veri, dict) else None


def anahtar_var(govde: dict | None, anahtar_yolu: str, tip: str) -> bool:
    """Nokta-ayraçlı anahtar yolu gövdede var mı (ve `tip=int` istendiyse tamsayı mı)?"""
    if govde is None:
        return False
    imlec = govde
    for k in anahtar_yolu.split("."):
        if not isinstance(imlec, dict) or k not in imlec:
            return False
        imlec = imlec[k]
    if tip == "int" and not isinstance(imlec, int):
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="[5a] doğrulama-token anahtar kontrolü")
    ap.add_argument("--uc", action="append", default=[], metavar="YOL|ANAHTAR|TIP",
                    help="ölçülecek uç (tekrarlanabilir); tip boşsa yalnız VARLIK ölçülür")
    ap.add_argument("--env-dosya", default="/opt/meridian/.dash.env")
    ap.add_argument("--taban", default="http://127.0.0.1:8080")
    a = ap.parse_args(argv)

    if not a.uc:
        print("kullanım: --uc '<yol>|<anahtar>|<tip>' (en az bir kez)", file=sys.stderr)
        return 2

    token = token_oku(a.env_dosya)
    if not token:
        print(OLCULEMEDI)
        return 0

    ihlal = False
    for ham_uc in a.uc:
        parca = ham_uc.split("|")
        if len(parca) != 3:
            print(f"uç biçimi üç alanlı değil: {ham_uc!r}", file=sys.stderr)
            return 2
        yol, anahtar, tip = (p.strip() for p in parca)
        try:
            govde = govde_getir(a.taban, yol, token)
        except Yonlendirme as y:
            # FAIL-CLOSED: 3xx bir ölçüm değildir. Uç yolu/anahtarı BASILMAZ — hüküm yok, sayfa
            # da başka bir yerdedir; basılacak tek şey NEDEN ölçülemediğidir.
            print(f"{OLCULEMEDI_YONLENDIRME} {y.kod}")
            return 1
        tamam = anahtar_var(govde, anahtar, tip)
        print(f"{'VAR' if tamam else 'YOK'}|{yol}|{anahtar}")
        if not tamam:
            ihlal = True
    return 1 if ihlal else 0


if __name__ == "__main__":
    sys.exit(main())
