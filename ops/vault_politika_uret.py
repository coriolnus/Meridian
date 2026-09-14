#!/usr/bin/env python3
"""ops/vault_politika_uret.py — Vault politikaları + Agent yapılandırmasını ÜRET (TSK-064 Faz-2).

NEDEN VAR. Faz-2'nin üç dosyası (iki politika + agent yapılandırması) AYNI gerçeğin üç farklı
yazımıdır: "hangi sır, hangi Vault yolunda durur, hangi dosyaya render edilir". Üçünü elle
yazmak, bu deponun en pahalı tekrarlayan arızasını (aynı gerçeğin iki kopyası sessizce ayrışır)
üç kopyayla çağırmak olurdu — ve ayrışmanın bedeli burada sıradan değildir: politikada eksik
kalan bir yol, Agent'ın o sırrı OKUYAMAMASI; şablonda eksik kalan bir hedef ise o dosyanın
ESKİ değerinde donması demektir. İkisi de sessizdir; ikisi de ancak bir rotasyondan sonra
görülür.

TEK KAYNAK: `deploy/sir_envanteri.yaml` içindeki `vault_kv` bloğu. Bu betik ondan ÜÇ dosya
üretir ve üçü de ÜRETİLMİŞ dosyadır (başlıkları bunu söyler, elle düzenlenmez).

KOMUT SATIRI SÖZLEŞMESİ (ops aracı sözleşmesi KOMUT SATIRIdır, `main()` değil):

    python ops/vault_politika_uret.py              # KURU koşum: farkı basar, HİÇBİR ŞEY YAZMAZ
    python ops/vault_politika_uret.py --kontrol    # yazMA; diskteki dosyalar güncel mi
    python ops/vault_politika_uret.py --uygula     # YAZ

Çıkış kodu HÜKÜMDÜR:
    0  güncel / yazıldı / kuru koşum tamamlandı
    1  BAYAT (yalnız `--kontrol`) — en az bir üretilmiş dosya kaynaktan geride
    2  KULLANIM hatası (`--kontrol` ile `--uygula` birlikte)

`--kontrol` İLE `--uygula` BİRLİKTE VERİLEMEZ ve bu sessiz bir öncelik kuralı DEĞİL, açık bir
kullanım hatasıdır (çıkış 2). Emsal ve gerekçe: `ops/jeton_css_uret.py` C4a bulgusu — biri
SORAR, öteki YAZAR; sessizce biri ötekini yutarsa operatör "yazdım" sanır ve hiçbir şey
yazılmamış olur (ölçülmüş vaka, 2026-08-30 ops aracı sınıfı).

DAMGA YOK, DETERMİNİSTİK ÇIKTI: aynı envanterden aynı bayt çıkar. Damga olsaydı her koşum bir
fark üretir ve `--kontrol` kapısı anlamsızlaşırdı.

SIR YOK: bu betik hiçbir sır DEĞERİ okumaz, yazmaz, basmaz — yalnız AD ve YOL işler. Değerleri
kasaya koyan ayrı bir betiktir (`deploy/vault/vault_sir_koy.sh`) ve o da `read -s`/stdin
disipliniyle çalışır.

OKUYUCU (Yasa 6): `deploy/vault/policies/*.hcl` ve `deploy/vault/agent.hcl` A1'de
`deploy/vault/vault_kur.sh` tarafından kasaya/diske kurulur; tazelik kapısı
`tests/test_vault_faz2_v485.py` bölüm G'dir.
"""
from __future__ import annotations

import argparse
import difflib
import pathlib
import sys

import yaml

KOK = pathlib.Path(__file__).resolve().parents[1]
ENVANTER = KOK / "deploy" / "sir_envanteri.yaml"
VAULT_DIZIN = KOK / "deploy" / "vault"
POLITIKA_DIZIN = VAULT_DIZIN / "policies"

#: KV-v2 montaj adı. Vault'ta okuma/yazma yolu `<mount>/data/<yol>`, meta yolu
#: `<mount>/metadata/<yol>`dur — `data/` ara segmentini unutmak KV-v2'nin en sık hatasıdır ve
#: sonucu "politika yazıldı ama Agent 403 alıyor"dur. Segment BURADA, tek yerde eklenir.
MONTAJ = "secret"

#: Kasanın adresi — `deploy/vault/vault.hcl` listener'ı ile AYNI olmak zorundadır. İkisi
#: ayrışırsa Agent hiçbir zaman login olamaz; çivi ikisini karşılaştırır.
VAULT_ADRESI = "http://127.0.0.1:8200"

#: AppRole bootstrap dosyaları (tasarım §6.3 "sıfırıncı sır"). `role_id` sır DEĞİLDİR,
#: `secret_id` sırdır ve 0400 root:root durur.
ROLE_ID_DOSYASI = "/etc/vault/agent.role-id"
SECRET_ID_DOSYASI = "/etc/vault/agent.secret-id"

#: AppRole'ün adı — politika (`secret-id` yenileme yolu) ve kurulum betiği AYNI adı kullanır.
APPROLE_ADI = "agent"

_BASLIK_SABLONU = """{yorum} ÜRETİLDİ — ELLE DÜZENLEME YAPMA.
{yorum} Kaynak : deploy/sir_envanteri.yaml (vault_kv bloğu)
{yorum} Üreten : ops/vault_politika_uret.py — deterministik, damgasız (her koşu aynı bayt)
{yorum} Tazelik: python ops/vault_politika_uret.py --kontrol   (çıkış 1 = bayat)
{yorum}
{yorum} Bu dosyayı düzenlersen bir sonraki üretim değişikliği siler. Değişmesi gereken şey
{yorum} envanterdir: yeni bir sır oraya girer, bu dosya yeniden üretilir.
"""


def _baslik(yorum: str = "#") -> str:
    return _BASLIK_SABLONU.format(yorum=yorum)


def vault_kv() -> list[dict]:
    """Envanterin `vault_kv` bloğu — üretimin TEK girdisi.

    Blok yoksa PATLAR, boş listeye DÜŞMEZ: `| default([])` yazsaydık envanter bozulduğunda
    üretici sessizce BOŞ bir politika yazar ve Agent hiçbir sırrı okuyamaz hâle gelirdi —
    "ölçüm hiç yapılmamışken hüküm vermek" sınıfı (fail-closed)."""
    veri = yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))
    kv = veri["vault_kv"]
    if not kv:
        raise SystemExit("deploy/sir_envanteri.yaml: `vault_kv` BOŞ — üretilecek bir şey yok")
    return kv


def _veri_yolu(girdi: dict) -> str:
    """`secret/meridian/<ad>` → `secret/data/meridian/<ad>` (KV-v2 okuma yolu)."""
    yol = girdi["vault_yolu"]
    onek = MONTAJ + "/"
    if not yol.startswith(onek):
        raise SystemExit(f"{girdi['ad']}: vault_yolu {MONTAJ!r} montajında değil: {yol!r}")
    return f"{MONTAJ}/data/{yol[len(onek):]}"


def politika_agent() -> str:
    """Agent'ın politikası: YALNIZ dalga-1 yollarını, YALNIZ `read`.

    Joker YOK (`secret/data/meridian/*` yazılmadı) ve bu bilinçlidir: joker bir politika, kasaya
    yarın konacak HER sırrı da Agent'a açardı — oysa Agent'ın okuduğu küme envanterde YAZILIDIR
    ve o kümeyi genişletmek bir KARAR olmalıdır, bir yan etki değil."""
    satirlar = [_baslik(), ""]
    satirlar.append("# Dalga-1: yedi tek-değer sırrı, yalnız okuma. Liste envanterin SIRASINI korur.")
    for g in vault_kv():
        satirlar.append("")
        satirlar.append(f'# {g["ad"]} → {g["hedef"]}')
        satirlar.append(f'path "{_veri_yolu(g)}" {{')
        satirlar.append('  capabilities = ["read"]')
        satirlar.append("}")
    return "\n".join(satirlar) + "\n"


def politika_admin() -> str:
    """Yönetici politikası: sırları KOYMAK ve kasayı yönetmek için — Agent bunu ASLA taşımaz.

    Kök jetonu kurulum sonunda İPTAL EDİLİR (tasarım §6.2); günlük yönetim bu dar politikayla
    yapılır. `sys/health` okuması bekçinin (ops/vault_sagligi.py) jetonlu koşumu için değil —
    bekçi jetonsuz koşar — operatörün `vault status` çağrısı için buradadır."""
    yollar = [
        (f'{MONTAJ}/data/meridian/*',
         ["create", "read", "update", "delete"],
         "sır DEĞERLERİ: koy/oku/güncelle/sil (vault_sir_koy.sh bu yolu kullanır)"),
        (f'{MONTAJ}/metadata/meridian/*',
         ["read", "list", "delete"],
         "KV-v2 meta: sürüm listesi ve kalıcı silme AYRI yoldur (data/ ile karıştırmak "
         "'sildim ama duruyor' üretir)"),
        ("sys/health",
         ["read"],
         "mühür durumu — operatörün `vault status` çağrısı"),
        (f"auth/approle/role/{APPROLE_ADI}/secret-id",
         ["update"],
         "Agent'ın secret-id'sini ELLE yenileme yolu (secret_id_ttl=0, kendiliğinden dönmez)"),
    ]
    satirlar = [_baslik(), ""]
    satirlar.append("# Yönetim politikası — kök jetonun YERİNE geçer (kök iptal edilir).")
    for yol, yetenekler, gerekce in yollar:
        satirlar.append("")
        satirlar.append(f"# {gerekce}")
        satirlar.append(f'path "{yol}" {{')
        liste = ", ".join(f'"{y}"' for y in yetenekler)
        satirlar.append(f"  capabilities = [{liste}]")
        satirlar.append("}")
    return "\n".join(satirlar) + "\n"


def agent_yapilandirmasi() -> str:
    """Vault Agent yapılandırması: AppRole ile login + her sır için bir `template` bloğu.

    `error_on_missing_key = true` ZORUNLUDUR ve ölçülmemiş bir iyimserliğe karşıdır: anahtar
    yoksa şablon BOŞ render ederdi ve boş bir credential dosyası, systemd'nin "başarıyla
    yüklediği" ama hiçbir şey içermeyen bir sır demektir — tüketici 401 alır ve arıza kasada
    değil uygulamada aranır.

    `remove_secret_id_file_after_reading = false`: dosya silinirse Agent yeniden başladığında
    login EDEMEZ (secret_id_ttl=0, dönmez). Tasarım §6.3'ün bilinçli kararı.

    BİLEREK YOK — `exec`/`command` bloğu: Agent render sonrası tüketiciyi YENİDEN BAŞLATMAZ.
    Bir render'ın bakım penceresi dışında worker'ı düşürmesi, bu depoda hiçbir yerde verilmemiş
    bir yetkidir; restart operatörün reçetesindedir (tasarım §6.4 "Agent'a bağlama adımı
    meridian/hindsight restart'ı ister, worker o an durur")."""
    satirlar = [_baslik(), ""]
    satirlar.append("# Kasa adresi — deploy/vault/vault.hcl listener'ı ile TEK KAYNAK.")
    satirlar.append("vault {")
    satirlar.append(f'  address = "{VAULT_ADRESI}"')
    satirlar.append("}")
    satirlar.append("")
    satirlar.append("# Sıfırıncı sır (tasarım §6.3): role_id sır DEĞİL, secret_id 0400 root:root.")
    satirlar.append("auto_auth {")
    satirlar.append('  method "approle" {')
    satirlar.append('    mount_path = "auth/approle"')
    satirlar.append("    config = {")
    satirlar.append(f'      role_id_file_path                   = "{ROLE_ID_DOSYASI}"')
    satirlar.append(f'      secret_id_file_path                 = "{SECRET_ID_DOSYASI}"')
    satirlar.append("      remove_secret_id_file_after_reading = false")
    satirlar.append("    }")
    satirlar.append("  }")
    satirlar.append("}")
    for g in vault_kv():
        satirlar.append("")
        satirlar.append(f'# {g["ad"]} — tüketici: {g["tuketici"]}')
        satirlar.append("template {")
        satirlar.append(
            '  contents    = "{{ with secret \\"%s\\" }}{{ .Data.data.value }}{{ end }}"'
            % _veri_yolu(g))
        satirlar.append(f'  destination = "{g["hedef"]}"')
        satirlar.append(f'  perms       = {g["mod"]}')
        satirlar.append("  error_on_missing_key = true")
        satirlar.append("}")
    return "\n".join(satirlar) + "\n"


#: ÜRETİLEN DOSYALAR — hedef ↔ üretici eşlemesi. Çivi bu tabloyu gezer; elle yazılmış ikinci
#: bir liste, bir dosya eklendiğinde sessizce bayatlardı.
CIKTILAR: tuple[tuple[pathlib.Path, str], ...] = (
    (POLITIKA_DIZIN / "meridian-agent.hcl", "politika_agent"),
    (POLITIKA_DIZIN / "meridian-admin.hcl", "politika_admin"),
    (VAULT_DIZIN / "agent.hcl", "agent_yapilandirmasi"),
)


def beklenen() -> list[tuple[pathlib.Path, str]]:
    return [(yol, globals()[fn]()) for yol, fn in CIKTILAR]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--kontrol", action="store_true",
                    help="yazMA; diskteki üretilmiş dosyalar güncel mi (çıkış 1 = bayat)")
    ap.add_argument("--uygula", action="store_true", help="üretilmiş dosyaları YAZ")
    a = ap.parse_args(argv)

    if a.kontrol and a.uygula:
        print("KULLANIM: --kontrol ile --uygula birlikte verilemez (biri SORAR, diğeri YAZAR — "
              "sessizce biri diğerini geçersiz kılmaz)", file=sys.stderr)
        return 2

    bayat: list[str] = []
    for yol, icerik in beklenen():
        mevcut = yol.read_text(encoding="utf-8") if yol.exists() else None
        if mevcut == icerik:
            continue
        bayat.append(str(yol.relative_to(KOK)))
        if not a.uygula:
            fark = difflib.unified_diff(
                (mevcut or "").splitlines(keepends=True), icerik.splitlines(keepends=True),
                fromfile=f"{yol.name} (disk)", tofile=f"{yol.name} (üretilen)")
            sys.stdout.writelines(fark)

    if a.uygula:
        for yol, icerik in beklenen():
            yol.parent.mkdir(parents=True, exist_ok=True)
            yol.write_text(icerik, encoding="utf-8")
        print(f"yazıldı: {len(CIKTILAR)} dosya"
              + (f" ({len(bayat)} değişti: {', '.join(bayat)})" if bayat else " (değişiklik yok)"))
        return 0

    if a.kontrol:
        if bayat:
            print("BAYAT: " + ", ".join(bayat), file=sys.stderr)
            return 1
        print(f"GÜNCEL: {len(CIKTILAR)} üretilmiş dosya envanterle uyumlu")
        return 0

    print(f"KURU KOŞUM — hiçbir şey yazılmadı. Bayat dosya: {len(bayat)}"
          + (f" ({', '.join(bayat)})" if bayat else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
