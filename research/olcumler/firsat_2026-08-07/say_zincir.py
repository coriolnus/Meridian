#!/usr/bin/env python3
"""D3-UI · FIRSAT YÜZEYLERİ — "ÜRETİLİYOR AMA GÖRÜNMÜYOR" ZİNCİRİ SAYIMI (2026-08-07).

NEDEN BU BETİK VAR
------------------
`docs/PATTERN-ETUDU-2026-08-06.md` §C1'in on işi tek bir kusur sınıfını adlandırıyor: bir defter
diske YAZILIYOR, hiçbir uç onu SERVİS ETMİYOR ya da servis ediyor ama hiçbir pano yüzeyi onu
OKUMUYOR. Repo bu zincirin ilk iki halkasını zaten zorluyor (`codelaw.artifact_graph` +
`ledgers.declared_writers` + YASA 6 denetimi), ama üçüncü halka — **HTTP → DOM** — statik Python
grafının GÖREMEDİĞİ yerde yaşıyor. K1 turunun kendi ifadesiyle: "artefakt yasası tatmin
görünüyordu, ama zincir bir kat yukarıda kopuktu; statik Python grafı JS'i göremez."

Bu betik o üçüncü halkayı sayar. Üç dosyaya birden bakar:
  1. `state/<defter>`         — defter diskte var mı (yoksa "ölçülemedi" DÜRÜST bir cevap)
  2. `meridian/api.py`        — defteri okuyan ÜRETİCİ + servis edildiği ALAN adı
  3. `meridian/web/app.js`    — o alanı okuyan TÜKETİCİ + yazdığı RENDER bölümü

SINIR — BEYAN: sayım METİN eşleşmesidir, çalışma zamanı izlemesi değil. Yanlış-NEGATİF tarafına
yanlıdır: bir alan dolaylı yoldan (değişkene alınıp taşınarak) okunuyorsa betik onu göremeyebilir.
Bu yüzden ölçüm bir KAPI değil bir ENVANTERdir; hüküm (testin assert'i) `beklenen` sütunuyla
karşılaştırılarak verilir ve o sütun bu dosyada ELLE yazılıdır — kaynaktan türetilseydi test
"kod kendine uyuyor mu?" diye sorardı ve kopuk bir zincir yeşil kalırdı.

Koşum:  python3 research/olcumler/firsat_2026-08-07/say_zincir.py [ÇIKTI.json]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
API = KOK / "meridian" / "api.py"
APPJS = KOK / "meridian" / "web" / "app.js"
STATE = KOK / "state"

# ---- ON İŞİN ZİNCİRİ — ELLE YAZILI BEKLENTİ (testin iddiası, kaynağın değil) -----------------
# Sütunlar:
#   is        · C1 numarası ve adı
#   yuzey     · docs/TASARIM-YONU-2026-08-07.md §3'ün BAĞLAYICI yüzey ataması
#   bolum     · `ALAN_BOLUMLERI`deki bölüm (kartın fiilen çizildiği yer)
#   defter    · state/ altındaki kaynak dosya ("—" = birden çok defterden türer)
#   uc_alan   · API yanıtındaki nokta-yollu alan adı
#   uretici   · api.py'deki üretici fonksiyon (uç zenginleştirmesi)
#   tuketici  · app.js'teki kart üreteci (tek okuyucu)
#   kart      · KART_KAYDI anahtarı (kapak sözleşmesinin çıpası)
# 2026-08-24 (operatör): BAĞLAYICI YÜZEY ATAMALARI GÜNCELLENDİ — beş yüzey YEDİ oldu ve
# iki işin evi DEĞİŞTİ (bölümleri taşındığı için, atama tercihi değiştiği için değil):
#   C1-2 emir yaşam-döngüsü → `mutabakat` ② Portföy'e taşındı  (karar → portfoy)
#   C1-9 çıkış nedeni       → `performans` ④ Analiz'e taşındı  (karar → analiz)
# İŞİN KENDİSİ DEĞİŞMEDİ; hangi sorunun cevabı olduğu netleşti (bkz. docs/KARAR-2026-08-24-C).
ZINCIR = [
    {"is": "C1-1 · reddedilen kararların karnesi", "yuzey": "karar", "bolum": "kapilar",
     "defter": "near_miss.json", "uc_alan": "mlops.near_miss", "uretici": "_near_miss_karne",
     "tuketici": "firsatRetKarnesi", "kart": "kapilar:retkarne"},
    {"is": "C1-2 · emir yaşam-döngüsü izi", "yuzey": "portfoy", "bolum": "mutabakat",
     "defter": "mirror_orders.json", "uc_alan": "reconcile.emir_yasam", "uretici": "_emir_yasam",
     "tuketici": "firsatEmirYasam", "kart": "mutabakat:emiryasam"},
    {"is": "C1-3 · gece maliyet/token karnesi", "yuzey": "ogrenme", "bolum": "hermes",
     "defter": "spend.jsonl", "uc_alan": "spend_detay", "uretici": "_spend_detay",
     "tuketici": "firsatMaliyetKarnesi", "kart": "hermes:maliyet"},
    {"is": "C1-4 · canlı zaman çizelgesi (damgalar)", "yuzey": "saglik", "bolum": "cizelge",
     "defter": "mechanism_beats.json", "uc_alan": "cizelge", "uretici": "_hat_cizelgesi",
     "tuketici": "firsatCizelgeIzi", "kart": "cizelge:damga"},
    {"is": "C1-5 · rollback sicili", "yuzey": "ogrenme", "bolum": "ajan",
     "defter": "scoreboard.json", "uc_alan": "rollback", "uretici": "_rollback_sicili",
     "tuketici": "firsatRollbackSicili", "kart": "ajan:rollback"},
    {"is": "C1-6 · regresyon kırılımı", "yuzey": "ogrenme", "bolum": "ajan",
     "defter": "trades.jsonl", "uc_alan": "regresyon", "uretici": "_regresyon_kirilimi",
     "tuketici": "firsatRegresyon", "kart": "ajan:regresyon"},
    {"is": "C1-7 · denetim izinin tamamı", "yuzey": "karar", "bolum": "adaylar",
     "defter": "trade_plans.jsonl", "uc_alan": "/api/audit_trail", "uretici": "api_audit_trail",
     "tuketici": "firsatDenetimIzi", "kart": "adaylar:denetim"},
    {"is": "C1-8 · bugün neden hiçbir şey olmadı", "yuzey": "karar", "bolum": "kapilar",
     "defter": "—", "uc_alan": "risk.eylemsizlik", "uretici": "_eylemsizlik",
     "tuketici": "firsatEylemsizlik", "kart": "kapilar:eylemsizlik"},
    {"is": "C1-9 · çıkış nedeni kırılımı", "yuzey": "analiz", "bolum": "performans",
     "defter": "exit_efficiency.json", "uc_alan": "mlops.exit_efficiency", "uretici": None,
     "tuketici": "firsatCikisNedeni", "kart": "performans:cikis"},
    {"is": "C1-10 · skorun olgunlaşması", "yuzey": "ogrenme", "bolum": "karne",
     "defter": "—", "uc_alan": "score_detail", "uretici": None,
     "tuketici": "firsatOlgunlasma", "kart": "karne:olgunlasma"},
]


def _yorumsuz(metin: str, isaret: str) -> str:
    """Yorum satırları KURAL SAYILMAZ (repo deseni v139/v154/v191): bu turun her kararı
    gerekçesiyle yazıldı ve o gerekçe bir BİLDİRİM sanılmamalı — yoksa silinmiş bir zincir
    kendi mezar taşı yüzünden "hâlâ bağlı" görünürdü."""
    return "\n".join(l for l in metin.splitlines() if not l.lstrip().startswith(isaret))


def olc(api_src: str | None = None, app_src: str | None = None) -> list[dict]:
    api = _yorumsuz(api_src if api_src is not None else API.read_text(), "#")
    app = _yorumsuz(app_src if app_src is not None else APPJS.read_text(), "//")
    out = []
    for z in ZINCIR:
        son = z["uc_alan"].split(".")[-1]
        uretici_var = (z["uretici"] is None) or bool(
            re.search(r"^def %s\(" % re.escape(z["uretici"]), api, re.M))
        # Uç bağı: üretici bir yanıt sözlüğüne ANAHTARLA giriyor mu (ya da rota olarak tanımlı mı)?
        if z["uc_alan"].startswith("/api/"):
            uc_bagli = ('"%s"' % z["uc_alan"]) in api
        elif z["uretici"]:
            uc_bagli = bool(re.search(r'"%s":\s*%s\(' % (re.escape(son), re.escape(z["uretici"])), api))
        else:
            uc_bagli = ('"%s"' % son) in api
        tuketici_var = bool(re.search(r"^function %s\(" % re.escape(z["tuketici"]), app, re.M))
        # Pano bağı: kart üreteci bir RENDER gövdesinden ÇAĞRILIYOR mu? (tanımlı ama çağrılmayan
        # bir üreteç, tam olarak bu turun kapattığı "ölü yüzey" sınıfıdır.)
        cagri_n = len(re.findall(r"(?<![\w$.])%s\s*\(" % re.escape(z["tuketici"]), app)) - 1
        alan_okunuyor = son in app or z["uc_alan"].split("/")[-1] in app
        kart_kayitli = ('"%s":' % z["kart"]) in app
        kart_kullaniliyor = ('katKart("%s")' % z["kart"]) in app
        defter_var = None if z["defter"] == "—" else (STATE / z["defter"]).exists()
        out.append({**z, "uretici_var": uretici_var, "uc_bagli": uc_bagli,
                    "tuketici_var": tuketici_var, "pano_cagri_n": max(0, cagri_n),
                    "alan_okunuyor": alan_okunuyor, "kart_kayitli": kart_kayitli,
                    "kart_kullaniliyor": kart_kullaniliyor, "defter_var": defter_var,
                    "zincir_tam": bool(uretici_var and uc_bagli and tuketici_var
                                       and cagri_n >= 1 and kart_kayitli and kart_kullaniliyor)})
    return out


# ---- KAPANAN İKİ SINIFIN SAYACI --------------------------------------------------------------
# Etüdün iki cümlesi doğrudan SAYILABİLİR bir iddiaydı ve ikisi de o gün DOĞRUYDU:
#   * "app.js içinde 'rollback' kelimesi SIFIR kez geçiyor"
#   * "/api/spend ucunun web tarafında hiç çağıranı yok (app.js içinde /api/spend sıfır geçiyor)"
# İkincisi bir tuzak taşır: doğru düzeltme `/api/spend`e tüketici bağlamak DEĞİL (o uç K1'de
# EMEKLİ), harcama KIRILIMINI kanonik uca (`/api/hermes`) taşımaktır. Bu yüzden sayaç iki şeyi
# birden ölçer: emekli uca çağıran EKLENMEMİŞ olmalı, kırılım ise panoda GÖRÜNÜYOR olmalı.
def sinif_sayaci(app_src: str | None = None, api_src: str | None = None) -> dict:
    app = _yorumsuz(app_src if app_src is not None else APPJS.read_text(), "//")
    api = _yorumsuz(api_src if api_src is not None else API.read_text(), "#")
    return {
        "rollback_gecisi": len(re.findall(r"rollback", app, re.I)),
        "spend_ucu_cagirani": len(re.findall(r'"/api/spend"|/api/spend', app)),
        "spend_detay_tuketicisi": len(re.findall(r"spend_detay", app)),
        "spend_detay_ucta": len(re.findall(r'"spend_detay"', api)),
    }


def main() -> int:
    sonuc = olc()
    say = sinif_sayaci()
    print("D3-UI · FIRSAT ZİNCİRİ (defter → uç → pano)\n")
    print(f"{'iş':44s} {'yüzey':9s} {'bölüm':11s} {'uç':7s} {'pano':6s} {'kapak':6s} {'tam':4s}")
    for z in sonuc:
        print(f"{z['is'][:44]:44s} {z['yuzey']:9s} {z['bolum']:11s} "
              f"{('✓' if z['uc_bagli'] else '✗'):7s} {('✓' if z['pano_cagri_n'] else '✗'):6s} "
              f"{('✓' if z['kart_kullaniliyor'] else '✗'):6s} {('TAM' if z['zincir_tam'] else 'KOPUK'):4s}")
    tam = sum(1 for z in sonuc if z["zincir_tam"])
    print(f"\nΣ zincir TAM = {tam}/{len(sonuc)}")
    print("\nKAPANAN SINIFLARIN SAYACI (etüdün iki ölçülebilir iddiası):")
    print(f"  app.js'te 'rollback' geçişi        : {say['rollback_gecisi']}  (etüt günü: 0)")
    print(f"  app.js'te '/api/spend' çağırısı    : {say['spend_ucu_cagirani']}  (K1 hükmü: EMEKLİ — 0 KALMALI)")
    print(f"  app.js'te 'spend_detay' okuması    : {say['spend_detay_tuketicisi']}  (kanonik uçtaki kırılım)")
    print(f"  api.py'de 'spend_detay' servisi    : {say['spend_detay_ucta']}")
    hedef = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "zincir.json"
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(json.dumps({"zincir": sonuc, "sinif_sayaci": say}, ensure_ascii=False, indent=1))
    print(f"\nyazıldı: {hedef}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
