#!/usr/bin/env python3
"""ops/vault_politika_uret.py — Vault politikaları + Agent yapılandırmasını ÜRET (TSK-064 Faz-2).

NEDEN VAR. Faz-2'nin üç dosyası (iki politika + agent yapılandırması) AYNI gerçeğin üç farklı
yazımıdır: "hangi sır, hangi Vault yolunda durur, hangi dosyaya render edilir". Üçünü elle
yazmak, bu deponun en pahalı tekrarlayan arızasını (aynı gerçeğin iki kopyası sessizce ayrışır)
üç kopyayla çağırmak olurdu — ve ayrışmanın bedeli burada sıradan değildir: politikada eksik
kalan bir yol, Agent'ın o sırrı OKUYAMAMASI; şablonda eksik kalan bir hedef ise o dosyanın
ESKİ değerinde donması demektir. İkisi de sessizdir; ikisi de ancak bir rotasyondan sonra
görülür.

TEK KAYNAK: `deploy/sir_envanteri.yaml` içindeki `vault_kv` (hangi sır kasada hangi yolda,
hangi dosyaya render edilir) ve dalga-2 ile gelen `vault_dosyalar` (Agent hangi SIR-YALNIZ yan
dosyayı hangi SATIRLARLA, kimin için yazar) blokları. Bu betik ikisinden ÜÇ dosya üretir ve üçü
de ÜRETİLMİŞ dosyadır (başlıkları bunu söyler, elle düzenlenmez).

TAKMA AD (`ayni_deger`, Rol-1 hükmü 2026-09-14): aynı DEĞERİ taşıyan sırların TEK kasa yolu
vardır. Takma ad girdisi kendi `vault_yolu`sunu/`hedef`ini TAŞIMAZ — bu betik hem şablon hem
politika yolunu BİRİNCİLİN girdisinden türetir, takma ad için ne `path` bloğu ne tek-değer
`template` üretir. Kural olmasaydı aynı değer kasada iki yolda yaşar ve rotasyondan sonra
sessizce ayrışırdı (biri döner, öteki dönmez).

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

#: KV-v2 STATİK sırların yeniden render aralığı (dalga-2). Varsayılan 5 dk'dır; rotasyon
#: penceresinde beklenen süre budur. TEK yerde yaşar: `deploy/oracle-a1/sir_rotasyon.sh --vault`
#: kendi bekleme TAVANINI bu aralıktan DEĞİL kendi sabitinden alır ve ikisi AYRI gerçeklerdir
#: (biri "ne sıklıkla yenilenir", öteki "ne kadar beklerim") — bu yüzden kopya değil, komşudurlar.
RENDER_ARALIGI = "1m"

#: ÖNEK SÖZLÜĞÜ — DONUK ve iki jetonlu. `deploy/oracle-a1/sir_rotasyon.sh` içindeki `ONEKLER`
#: tablosuyla AYNI vokabülerdir: envanter önek LİTERALİNİ değil JETONUNU taşır. Literal yazılsaydı
#: iki yazım (boşluklu/boşluksuz) sessizce ayrışır ve kapının Authorization başlığı
#: `Bearer<anahtar>` olurdu — upstream 401 verir, arıza kasada aranır.
ONEKLER = {None: "", "Bearer": "Bearer "}

_BASLIK_SABLONU = """{yorum} ÜRETİLDİ — ELLE DÜZENLEME YAPMA.
{yorum} Kaynak : deploy/sir_envanteri.yaml (vault_kv + vault_dosyalar blokları)
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
    indeks(kv)  # takma ad referansları BURADA doğrulanır: her okuyucu fail-closed olsun
    return kv


def indeks(kv: list[dict]) -> dict[str, dict]:
    """`ad → girdi` indeksi; `ayni_deger` (TAKMA AD) referanslarını DOĞRULAR.

    Doğrulama burada, tek yerde durur çünkü üç çıktı da (iki politika + agent yapılandırması)
    aynı referansları okur ve üçünde ayrı ayrı kontrol etmek, birinde unutulduğunda sessiz bir
    boşluk bırakırdı. Üç hâl PATLAR, hiçbiri "en iyi tahminle devam" ETMEZ:
      · dangling takma ad → şablon kasada OLMAYAN bir yolu okurdu (Agent 403/404, dosya hiç doğmaz)
      · takma ad ZİNCİRİ → "birincil TEK olmalı" kuralı olmadan aynı değer yine iki yola dağılırdı
      · takma adın KENDİ `vault_yolu`su → hükmün tam tersi: kasada ikinci bir yol açılırdı"""
    ind = {g["ad"]: g for g in kv}
    for g in kv:
        birincil = g.get("ayni_deger")
        if birincil is None:
            continue
        if birincil not in ind:
            raise SystemExit(
                f"{g['ad']}: `ayni_deger` {birincil!r} `vault_kv`de YOK (dangling takma ad)")
        if ind[birincil].get("ayni_deger") is not None:
            raise SystemExit(
                f"{g['ad']}: `ayni_deger` ZİNCİRİ ({birincil} da bir takma ad) — birincil TEK olmalı")
        if "vault_yolu" in g or "hedef" in g:
            raise SystemExit(
                f"{g['ad']}: takma ad KENDİ `vault_yolu`/`hedef`ini taşıyamaz — aynı değerin TEK "
                "kasa yolu vardır (Rol-1 hükmü 2026-09-14)")
    return ind


def kendi_yolu_olan(kv: list[dict]) -> list[dict]:
    """Kasada KENDİ yolu olan girdiler — takma adlar (`ayni_deger`) HARİÇ.

    Politika `path` blokları ve tek-değer `template` blokları YALNIZ bunlardan doğar: takma ad
    için ikinci bir `path` yazmak HCL'de yol TEKRARIdır, ikinci bir `template` ise sırrın
    diskteki yüzeyini gereksizce büyüten bir kanonik kopya olurdu."""
    return [g for g in kv if "ayni_deger" not in g]


def _veri_yolu(girdi: dict) -> str:
    """`secret/meridian/<ad>` → `secret/data/meridian/<ad>` (KV-v2 okuma yolu)."""
    yol = girdi["vault_yolu"]
    onek = MONTAJ + "/"
    if not yol.startswith(onek):
        raise SystemExit(f"{girdi['ad']}: vault_yolu {MONTAJ!r} montajında değil: {yol!r}")
    return f"{MONTAJ}/data/{yol[len(onek):]}"


def vault_dosyalar() -> list[dict]:
    """Envanterin `vault_dosyalar` bloğu — dalga-2'nin SIR-YALNIZ yan dosyaları.

    Blok YOKSA PATLAR, boş listeye DÜŞMEZ (`vault_kv` ile aynı gerekçe): sessizce boş dönseydi
    üretici yan dosya şablonlarını HİÇ yazmaz, Agent onları render etmez ve tüketiciler eski
    kanalda kalırdı — geçiş "yapıldı" sanılırken hiçbir şey olmamış olurdu (fail-closed)."""
    veri = yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))
    if "vault_dosyalar" not in veri:
        raise SystemExit("deploy/sir_envanteri.yaml: `vault_dosyalar` bloğu YOK (dalga-2)")
    dosyalar = veri["vault_dosyalar"]
    if not dosyalar:
        raise SystemExit("deploy/sir_envanteri.yaml: `vault_dosyalar` BOŞ — üretilecek yan dosya yok")
    return dosyalar


def _ad_veri_yolu(ad: str, ind: dict[str, dict]) -> str:
    """Bir `satirlar[].sir` referansını KV-v2 okuma yoluna çevirir — dangling referans PATLAR.

    Sessizce atlamak, o ALANIN yan dosyada HİÇ doğmaması demektir: tüketici değişkeni eski
    kanaldan okumaya devam eder ve geçişin yarım kaldığı ancak eski kanal kapatıldığında,
    yani en pahalı anda görünür.

    TAKMA AD (`ayni_deger`) BURADA ÇÖZÜLÜR: referans bir takma adsa yol BİRİNCİLİNDİR. Aynı
    değeri taşıyan iki ALAN adı (ör. `OPENROUTER_API_KEY` ile `HINDSIGHT_API_REFLECT_LLM_1_API_KEY`)
    böylece tek kasa yolunda buluşur ve rotasyondan sonra ayrışamazlar — hükmün bütün mekaniği
    bu tek satırdır."""
    if ad not in ind:
        raise SystemExit(f"`vault_dosyalar` {ad!r} sırrına referans veriyor ama `vault_kv`de YOK")
    girdi = ind[ad]
    birincil = girdi.get("ayni_deger")
    return _veri_yolu(ind[birincil] if birincil else girdi)


def _yan_dosya_sablonlari() -> list[str]:
    """Her yan dosya için BİR `template` bloğu: satır satır `ALAN=<kasa değeri>`.

    İçerik HEREDOC ile yazılır (`<<EOT`), tek satırlık kaçışlı bir dizgeyle değil: sekiz alanlı
    bir dosyanın tek satıra sıkıştırılmış hâli okunamaz olurdu ve bu dosyayı bakım penceresinde
    okuyan operatör, hangi alanın hangi kasa yolundan geldiğini göremezdi (üretilmiş dosya da
    okunmak içindir). Heredoc gövdesi sondaki yeni satırı TAŞIR — `.env` sözleşmesi budur.

    `exec` YALNIZ `sahip: ubuntu` olan dosyada doğar ve komut KABUKSUZ + SABİT argüman
    listesidir: tek iş sahipliği düzeltmektir, restart DEĞİL (tasarım §6.4)."""
    ind = indeks(vault_kv())
    satirlar: list[str] = []
    for d in vault_dosyalar():
        satirlar.append("")
        satirlar.append(f'# {d["yol"]} — tüketici: {d["tuketici"]}')
        satirlar.append("template {")
        satirlar.append("  contents    = <<EOT")
        for s in d["satirlar"]:
            onek = ONEKLER[s.get("onek")]
            satirlar.append(
                '%s=%s{{ with secret "%s" }}{{ .Data.data.value }}{{ end }}'
                % (s["alan"], onek, _ad_veri_yolu(s["sir"], ind)))
        satirlar.append("EOT")
        satirlar.append(f'  destination = "{d["yol"]}"')
        satirlar.append(f'  perms       = {d["mod"]}')
        satirlar.append("  error_on_missing_key = true")
        if d["sahip"] != "root":
            sahip = d["sahip"]
            satirlar.append("  exec {")
            satirlar.append(
                f'    command = ["chown", "{sahip}:{sahip}", "{d["yol"]}"]')
            satirlar.append('    timeout = "10s"')
            satirlar.append("  }")
        satirlar.append("}")
    return satirlar


def politika_agent() -> str:
    """Agent'ın politikası: YALNIZ envanterdeki yolları, YALNIZ `read`.

    Joker YOK (`secret/data/meridian/*` yazılmadı) ve bu bilinçlidir: joker bir politika, kasaya
    yarın konacak HER sırrı da Agent'a açardı — oysa Agent'ın okuduğu küme envanterde YAZILIDIR
    ve o kümeyi genişletmek bir KARAR olmalıdır, bir yan etki değil.

    TAKMA ADLAR (`ayni_deger`) BURADA YOL ÜRETMEZ: yolları birincilinkidir ve o yol listede
    ZATEN vardır. İkinci bir `path` bloğu HCL'de yol TEKRARIdır — politikayı okuyan mühendise
    iki AYRI sır varmış gibi görünür ve hükmün kendisini (aynı değer = tek yol) yalanlardı."""
    satirlar = [_baslik(), ""]
    satirlar.append("# Yalnız okuma. Liste `vault_kv`den TÜRER ve envanterin SIRASINI korur —")
    satirlar.append("# düzyazıya gömülü bir sayım (kaç sır) dalga-2'de sessizce yalan olurdu.")
    satirlar.append("# TAKMA ADLAR (`ayni_deger`) YOL AÇMAZ: birincilin yolunu okurlar, tekrar YOK.")
    for g in kendi_yolu_olan(vault_kv()):
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
    """Vault Agent yapılandırması: AppRole ile login + her hedef için bir `template` bloğu.

    `error_on_missing_key = true` ZORUNLUDUR ve ölçülmemiş bir iyimserliğe karşıdır: anahtar
    yoksa şablon BOŞ render ederdi ve boş bir credential dosyası, systemd'nin "başarıyla
    yüklediği" ama hiçbir şey içermeyen bir sır demektir — tüketici 401 alır ve arıza kasada
    değil uygulamada aranır.

    `remove_secret_id_file_after_reading = false`: dosya silinirse Agent yeniden başladığında
    login EDEMEZ (secret_id_ttl=0, dönmez). Tasarım §6.3'ün bilinçli kararı.

    DALGA-2 (2026-09-14) İKİ ŞEY EKLEDİ, BİRİ BİR YETKİ GENİŞLEMESİDİR ve adıyla yazılıdır:
      · `template_config { static_secret_render_interval }` — KV-v2 STATİK sırlar varsayılan
        5 dk'da yeniden render edilir; rotasyon penceresindeki bekleme o süreyle SINIRLIDIR.
      · `exec { command = ["chown", ...] }` — YALNIZ `sahip: ubuntu` olan yan dosyalarda.
        `template` bloğunda dosya SAHİBİ parametresi YOKTUR (yalnız `perms`; resmî belge,
        ölçüldü 2026-09-14) ve Agent root koşar → render edilen dosya root:root olur. Tüketicisi
        `ubuntu` olan hermes profil dosyaları o hâlde OKUNAMAZ. Komut KABUKSUZ ve SABİT argüman
        listesiyle verilir: kabuk olsaydı şablon içeriği komut satırına sızabilirdi.

    HÂLÂ BİLEREK YOK — RESTART: Agent render sonrası tüketiciyi YENİDEN BAŞLATMAZ. `chown` bir
    restart DEĞİLDİR; bir render'ın bakım penceresi dışında worker'ı düşürmesi bu depoda hiçbir
    yerde verilmemiş bir yetkidir ve restart operatörün/rotasyonun reçetesindedir (tasarım §6.4)."""
    satirlar = [_baslik(), ""]
    satirlar.append("# Kasa adresi — deploy/vault/vault.hcl listener'ı ile TEK KAYNAK.")
    satirlar.append("vault {")
    satirlar.append(f'  address = "{VAULT_ADRESI}"')
    satirlar.append("}")
    satirlar.append("")
    satirlar.append("# STATİK (KV-v2) sırların yeniden render aralığı. Varsayılan 5 dk'dır ve")
    satirlar.append("# rotasyon penceresinde beklenen süre TAM OLARAK budur — değer TEK yerde")
    satirlar.append("# yaşar, şerhte tekrarlanmaz (tekrarlanan bir süre kadans değişince yalan olur).")
    satirlar.append("template_config {")
    satirlar.append(f'  static_secret_render_interval = "{RENDER_ARALIGI}"')
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
    # TAKMA ADLAR (`ayni_deger`) KENDİ tek-değer şablonunu ÜRETMEZ: kasa yolu birincilindir ve
    # ikinci bir kanonik kopya, sırrın diskteki yüzeyini bir dosya daha büyütürdü. Render kanıtı
    # da birincilin `hedef`idir (rotasyon betiği onu okur).
    for g in kendi_yolu_olan(vault_kv()):
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
    satirlar.extend(_yan_dosya_sablonlari())
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
