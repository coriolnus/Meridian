"""auth_cli.py — operatör parolasını ve oturum imza anahtarını kabuktan yöneten CLI.

    .venv/bin/python -m meridian.auth_cli set        # parola belirle / değiştir
    .venv/bin/python -m meridian.auth_cli status     # kurulu mu, dosya izni doğru mu, oturum ömrü
    .venv/bin/python -m meridian.auth_cli logout-all # imza anahtarını döndür → tüm oturumlar düşer

NE YAPAR. `set` parolayı kurar/değiştirir (kuruluysa önce MEVCUT parola doğrulanır); `status`
parolanın kurulu olup olmadığını, `state/auth.json` yolunu ve iznini (0600 olmalı), bağlanma
adresinin genel olup olmadığını ve oturum ömrünü basar; `logout-all` imza anahtarını döndürür —
açık tüm oturumlar düşer, parola DEĞİŞMEZ. Genel arayüz + parolasız durumda `status` 1 döner
(sunucu böyle açılmayı zaten reddeder).

NEDEN KABUKTAN. `POST /api/setup-password` yalnız parola HENÜZ KURULU DEĞİLKEN çalışır;
kurulduktan sonra değiştirmenin tek yolu buradan geçer, yani `state/auth.json`a — dolayısıyla
sunucuya — erişim gerekir. Web üzerinden "parolamı unuttum" akışı BİLEREK yoktur: tek operatörlü
bir sistemde o akış, saldırgan için ikinci bir giriş kapısından başka bir şey değildir.

SIR DİSİPLİNİ. Parola getpass ile alınır: ekrana yazılmaz, kabuk geçmişine düşmez, argüman olarak
da alınmaz; hiçbir değer loglanmaz. `status` çıktısındaki oturum-ömrü sayıları auth sabitlerinden
OKUNUR, metne gömülmez — sabit değişince beyan kendiliğinden doğru kalır (tek sayı basmak kayan
pencereyi ya "12 saatte kapanır" ya "sonsuza dek açık" diye yanlış okuturdu). Okur/yazar: yalnız
auth.py üzerinden `state/auth.json`.
"""
from __future__ import annotations

import getpass
import os
import sys

from . import auth


def _set() -> int:
    if auth.password_set():
        print("Parola zaten kurulu. Değiştirmek için önce MEVCUT parolayı gir.")
        cur = getpass.getpass("Mevcut parola: ")
        if not auth.verify_password(cur):
            print("HATA: mevcut parola yanlış.", file=sys.stderr)
            return 1
    pw = getpass.getpass("Yeni parola (en az 12 karakter): ")
    if pw != getpass.getpass("Tekrar: "):
        print("HATA: parolalar eşleşmedi.", file=sys.stderr)
        return 1
    try:
        auth.set_password(pw)
    except ValueError as e:
        print(f"HATA: {e}", file=sys.stderr)
        return 1
    print(f"✓ parola kuruldu → {auth._auth_file()} (0600)")
    print("  Açık oturumlar DÜŞMEDİ. Düşürmek için: python -m meridian.auth_cli logout-all")
    return 0


def _status() -> int:
    kurulu = auth.password_set()
    print(f"parola      : {'kurulu' if kurulu else 'KURULU DEĞİL'}")
    # `auth._auth_file()` — ÇAĞRI ANINDA çözülür; `status` çıktısı süreç neyi okuyorsa ONU
    # göstermelidir, import anında neyin doğru olduğunu değil (bkz. auth._auth_file gerekçesi).
    path = auth._auth_file()
    print(f"dosya       : {path}")
    if path.exists():
        mode = path.stat().st_mode & 0o777
        ok = mode == 0o600
        print(f"izin        : {oct(mode)} {'✓' if ok else '← 0600 OLMALI (chmod 600)'}")
    else:
        print("izin        : (dosya yok)")
    host = os.environ.get("MERIDIAN_BIND_HOST", "127.0.0.1")
    genel = host not in ("127.0.0.1", "localhost", "::1")
    print(f"bağlanma    : {host}{'  ← GENEL' if genel else '  (loopback)'}")
    # OTURUM ÖMRÜ İKİ SAYIDIR (v245-B kayan oturum; düzeltme 2026-08-14, ROADMAP §2-34b).
    # ÖNCEDEN yalnız "12 saat" basıyordu ve bu artık EKSİKTİ: pencere SABİT değil KAYAN
    # (`auth.refresh_session` yarı-ömürden sonra uzatır) ve kaymanın MUTLAK BİR TAVANI var
    # (`iat + SESSION_ABSOLUTE_MAX_S`). Tek sayı gören operatör, kullandığı panonun 12 saatte
    # kapanacağını sanardı (yanlış) ya da sonsuza dek açık kalacağını (daha tehlikeli yanlış).
    # İKİ SAYI DA KODDAN OKUNUR, METNE GÖMÜLMEZ: sabitler değişirse bu satır kendiliğinden
    # doğru kalır — çivisi tests/test_beyan_bayatligi_v246.py (sabitler saplanır, çıktı izler).
    print(f"oturum ömrü : {auth.SESSION_TTL_S // 3600} saat KAYAN pencere "
          f"(yarı-ömürden sonra her istek uzatır) · mutlak tavan "
          f"{auth.SESSION_ABSOLUTE_MAX_S // 86400} gün (uzatma bunu AŞAMAZ)")
    if genel and not kurulu:
        print("\nUYARI: genel arayüze parolasız bağlanma — sunucu açılmayı REDDEDER.", file=sys.stderr)
        return 1
    return 0


def _logout_all() -> int:
    auth.rotate_key()
    print("✓ imza anahtarı döndürüldü — açık tüm oturumlar düştü. Parola DEĞİŞMEDİ.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    cmd = args[0] if args else "status"
    if cmd == "set":
        return _set()
    if cmd == "status":
        return _status()
    if cmd == "logout-all":
        return _logout_all()
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
