# Faz 1 — Bot roster temeli: uygulama planı

> **Ajan işçiler için:** ZORUNLU ALT-SKILL: bu planı görev-görev uygulamak için
> `superpowers:subagent-driven-development` (önerilen) ya da `superpowers:executing-plans`
> kullanın. Adımlar takip için onay kutusu (`- [ ]`) söz dizimindedir.

**Hedef:** Yeni Hermes profili AÇMADAN, botların üstüne kurulacağı üç temeli atmak: güvenlik
duruşunu depoya almak, hesaplanmış ama teslim edilmeyen iki çıktıyı teslim etmek, ve
tekrarlayan canlı-ölçüm kalıbını deterministik bir araca çevirmek.

**Mimari:** Hiçbir yeni üretici eklenmez. Var olan mekanizmalar (`ops/alarm_backlog_digest.py`,
`nous_eval` çıktısı) kadansa asılır; teslimat Meridian'ın `notify.py`'ından geçer (tek giden
yol değişmezi); ölçüm kalıbı LLM'siz bir CLI'ya derlenir.

**Tech Stack:** Python 3.12 · pytest · systemd timer · Hermes Agent v0.19.0 · YAML config

**Spec:** `docs/superpowers/specs/2026-08-27-bot-roster-design.md` (§3 Faz 1, §9 güvenlik)

## Global Constraints

- **UYDURMA YASAĞI.** Ölçülemeyen değer `None` + neden; sayı uydurulmaz. (CLAUDE.md madde 4)
- **YASA 4.** Sessiz-yutma `# sessiz-yutma: <≥20 karakter gerekçe>` ile işaretlenir.
- **YASA 6.** Okuyucusu olmayan artefakt yazılmaz; `codelaw` bunu zorlar.
- **Ajanlar git komutu KOŞMAZ.** commit/push yalnız Rol-1'de. (CLAUDE.md madde 8)
- **`state/` versiyonlanmaz** (istisna: `goal.yaml` + `bounds.yaml`). Sır asla commit'lenmez.
- **Canlı worker koşarken `state/`e YAZMA.** Testler yalnız `sandbox_state` içinde yazar.
- **Tam suite yalnız Rol-1'de, DONMUŞ ağaçta.** Ajanlar kapsam testi koşar.
- **Bekleme betiği YASAK** — `until`/`while` + `sleep` yoklama döngüsü kurulmaz.
- **Çivi önce.** Her davranış değişikliği önce kırmızı bir testle görülür (TDD).
- **Satır çapası yazma.** `dosya.py:123` biçimi çürür; codelaw yorumu hedefleyen çapayı reddeder.
- Dağıtım yalnız `./dagit.sh` ile ve yalnız Rol-1'de. Sistem birimi kurulumu OPERATÖR işidir.

---

## Spec'ten SAPMA — ölçümle gerekçeli

Spec §3 "310 alarm + `self_review.json` + `improvement_proposals.jsonl` → **tek brifing**" diyor.
Plan yazılırken ölçüldü ve bu kısmen YANLIŞ bir hedef:

```
notify.configured()                  True                      → kanal AÇIK
notify_suppressed (14 gün)           10 · window_s=21600       → hız sınırı, ARIZA DEĞİL
selfreview.weekly()                  scheduler.py:1141'de asılı, ZATEN notify.send() çağırıyor
self_review_generated (14 gün)       2                         → koşuyor
alarm_backlog_digest.py              yazılmış, main(--uygula), yeni yoksa SESSİZ dönüyor
                                     ama HİÇBİR KADANSA ASILI DEĞİL
improvement_proposals.jsonl          16 öneri, teslimat yolu YOK
```

Yani teslimatın çoğu çalışıyor. Üçünü tek mesajda birleştirmek, **çalışan bir davranışı
değiştirmek** olurdu. Bu plan bunun yerine: çalışanı bırakır, eksik iki teslimatı ayrı ayrı
ekler — **her biri boşken sessiz**. Birleştirme `@sef`in işidir ve Faz 2'ye aittir.

---

## Dosya yapısı

| dosya | sorumluluğu |
|---|---|
| `deploy/hermes/config.yaml` | **YENİ.** Ajan yapılandırması + §9.2 güvenlik duruşu. Bugün yalnız canlıda, versiyonsuz. |
| `dagit.sh` (F9_LISTE) | üç yeni sürüklenme kaydı |
| `deploy/oracle-a1/meridian-brifing.service` | **YENİ.** oneshot: iki teslimat betiğini koşar |
| `deploy/oracle-a1/meridian-brifing.timer` | **YENİ.** günlük tetik |
| `ops/oneri_brifingi.py` | **YENİ.** okunmamış iyileştirme önerileri → tek mesaj, boşken sessiz |
| `ops/olcum.py` | **YENİ.** tipli canlı-ölçüm CLI'ı (LLM'siz) |
| `deploy/hermes/skills/meridian-olcum/SKILL.md` | **YENİ.** ajana "tahmin etme, `ops/olcum.py` kullan" der |
| `tests/test_hermes_config_durusu_v326.py` | güvenlik duruşu çivileri |
| `tests/test_brifing_kadansi_v327.py` | kadans + sessizlik çivileri |
| `tests/test_olcum_araci_v328.py` | ölçüm CLI çivileri |

---

## Görev 1: Ajan yapılandırmasını depoya al ve güvenlik duruşunu yaz

**Files:**
- Create: `deploy/hermes/config.yaml`
- Modify: `dagit.sh` — `F9_LISTE` bloğu (satır aralığı `grep -n 'F9_LISTE=' dagit.sh` ile bulunur)
- Test: `tests/test_hermes_config_durusu_v326.py`

**Interfaces:**
- Consumes: yok (ilk görev)
- Produces: `deploy/hermes/config.yaml` — Görev 2 ve 4 bu dosyanın varlığına dayanmaz, ama
  §9.4 çivileri buradan okur.

**Neden bu görev ilk:** §9'da verilen güvenlik kararlarının bugün depoda evi yok. `dagit` F9
kapısı `SOUL.md`i izliyor ama `config.yaml`ı izlemiyor — yani ajanın izin duruşu sessizce
sürüklenebilir ve kimse fark etmez.

- [ ] **Adım 1: Çiviyi yaz (kırmızı olacak)**

```python
# tests/test_hermes_config_durusu_v326.py
"""HERMES AJAN YAPILANDIRMASI DEPODA VE GÜVENLİ — v326 (2026-08-27)

NEDEN. §9.0 ölçümü: canlıda `approvals` HİÇ TANIMLI DEĞİL, `terminal` tanımsız (→ local),
`security` tanımsız. Tek gerçek savunma `pre_tool_call → meridian-guard.sh` ve o kanca kendi
şerhinde "parse edilemezse FAIL-OPEN" diyor — kalkan değil desen filtresi.

VE ÖLÇÜLEN ASIL RİSK: yeni bir profil bu kancayı OTOMATİK MİRAS ALMAZ. `--clone` taşır,
sıfırdan kurulan profil KORUMASIZ doğar. Bot çoğaltmak kancasız ajan çoğaltmaktır.

Çare kural değil KONTROL: yapılandırma depoya alınır, duruş orada BEYAN edilir, ve bu çivi
beyanın bozulmadığını her koşumda sınar. `dagit` F9 de canlı ile depo arasındaki sürüklenmeyi
raporlar (F9 ENGELLEMEZ, RAPORLAR — kimlik kapısı doğruluk kapısı değildir).
"""
from __future__ import annotations

import pathlib

import pytest

yaml = pytest.importorskip("yaml")

KOK = pathlib.Path(__file__).resolve().parent.parent
CFG = KOK / "deploy/hermes/config.yaml"
DAGIT = KOK / "dagit.sh"

GEREKLI_DENY = ["*dagit.sh*", "git push*", "git commit*", "*systemctl*", "*serve.sh*"]


def _cfg() -> dict:
    assert CFG.exists(), f"{CFG} YOK — ajan yapılandırması versiyonlanmamış"
    return yaml.safe_load(CFG.read_text(encoding="utf-8")) or {}


def test_guard_kancasi_TANIMLI():
    """Kanca yoksa ajan `state/`e, sırlara ve Alpaca emrine dokunabilir."""
    h = (_cfg().get("hooks") or {}).get("pre_tool_call") or []
    kancalar = [str(e.get("command", "")) for e in h]
    assert any("meridian-guard.sh" in c for c in kancalar), (
        f"pre_tool_call kancası meridian-guard.sh'e gitmiyor: {kancalar}")


def test_cron_modu_DENY():
    """Başsız cron tehlikeli komutu ONAYLAYAMAZ. Bu pazarlığa kapalı (§9.2)."""
    a = _cfg().get("approvals") or {}
    assert a.get("cron_mode") == "deny", f"approvals.cron_mode={a.get('cron_mode')!r}, 'deny' olmalı"


def test_deny_listesi_TAM():
    """--yolo'da bile geçersiz olan yasaklar. Eksik biri, o kapının açık olması demektir."""
    a = _cfg().get("approvals") or {}
    deny = [str(x) for x in (a.get("deny") or [])]
    eksik = [d for d in GEREKLI_DENY if d not in deny]
    assert not eksik, f"deny listesinde eksik desen(ler): {eksik} · mevcut: {deny}"


def test_yapilandirmada_SIR_YOK():
    """Bu dosya versiyonlanıyor. İçine bir anahtar sızarsa git geçmişine kalıcı girer."""
    metin = CFG.read_text(encoding="utf-8")
    import re
    supheli = re.findall(r"(?i)(api[_-]?key|secret|token|password)\s*:\s*\S+", metin)
    supheli = [s for s in supheli if "***" not in s]
    assert not supheli, f"yapılandırmada sır görünümlü satır: {supheli}"


def test_dagit_F9_bu_dosyayi_IZLIYOR():
    """Depoda beyan edilen duruş, canlıdakiyle karşılaştırılmıyorsa beyan bir dilektir."""
    metin = DAGIT.read_text(encoding="utf-8")
    assert "deploy/hermes/config.yaml|/home/ubuntu/.hermes/config.yaml" in metin, (
        "F9_LISTE config.yaml'ı izlemiyor — canlı duruş sessizce sürüklenebilir")
```

- [ ] **Adım 2: Kırmızıyı gör**

Run: `.venv/bin/python -m pytest tests/test_hermes_config_durusu_v326.py -v`
Expected: 5 test de FAIL — ilk dördü `AssertionError: …/deploy/hermes/config.yaml YOK`,
beşincisi `F9_LISTE config.yaml'ı izlemiyor`.

- [ ] **Adım 3: Yapılandırmayı depoya al**

Canlıdaki hâli çek (sır içermiyor — ölçüldü: yalnız model/mcp/hooks/havuz stratejileri):

```bash
scp -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87:/home/ubuntu/.hermes/config.yaml deploy/hermes/config.yaml
```

- [ ] **Adım 4: Güvenlik bloğunu ekle**

`deploy/hermes/config.yaml` dosyasının SONUNA ekle:

```yaml

# --- GÜVENLİK DURUŞU (spec §9.2, operatör kararı 2026-08-27) --------------------------------
# Terminal arka ucu BİLEREK `local`: A1 dört çekirdek ve 8 sa 55 dk CPU yakan sprint koşuyor;
# ayrıca konteyner arka uçlarında Hermes'in KENDİ tehlikeli-komut denetimi ATLANIR (konteyner
# sınır sayılır), yani docker göründüğü kadar net kazanç değil. Karşılığı bu blok + guard hook.
approvals:
  mode: smart
  cron_mode: deny            # başsız cron tehlikeli komutu ONAYLAMAZ — pazarlığa kapalı
  deny:                      # fnmatch; --yolo'da BİLE geçersiz
    - "*dagit.sh*"           # dağıtım yalnız Rol-1'in (CLAUDE.md madde 5)
    - "git push*"
    - "git commit*"          # CLAUDE.md madde 8'in makine karşılığı
    - "*systemctl*"
    - "*serve.sh*"           # CLAUDE.md madde 5: yerelde koşma, çift-emir riski
```

- [ ] **Adım 5: F9 kaydını ekle**

`dagit.sh` içindeki `F9_LISTE="` bloğunda, `deploy/hermes/SOUL.md|…` satırının HEMEN ALTINA
şu satırı ekle (blok satır-başına bir çift okuyor, sıra önemsiz):

```
deploy/hermes/config.yaml|/home/ubuntu/.hermes/config.yaml
```

- [ ] **Adım 6: Yeşili gör**

Run: `.venv/bin/python -m pytest tests/test_hermes_config_durusu_v326.py -v`
Expected: 5 passed

- [ ] **Adım 7: Çürütme — çivi tautoloji değil**

```bash
cp deploy/hermes/config.yaml /tmp/cfg.bak
python3 - <<'EOF'
import pathlib, re
p = pathlib.Path("deploy/hermes/config.yaml")
p.write_text(p.read_text(encoding="utf-8").replace("cron_mode: deny", "cron_mode: approve"), encoding="utf-8")
EOF
.venv/bin/python -m pytest tests/test_hermes_config_durusu_v326.py::test_cron_modu_DENY
cp /tmp/cfg.bak deploy/hermes/config.yaml && rm /tmp/cfg.bak
```
Expected: önce FAIL (`cron_mode='approve'`), geri alınca PASS.

- [ ] **Adım 8: Commit**

```bash
git add deploy/hermes/config.yaml dagit.sh tests/test_hermes_config_durusu_v326.py
git commit -m "Ajan yapılandırması depoya alındı: güvenlik duruşu artık beyanlı ve çivili"
```

---

## Görev 2: Teslim edilmeyen iki çıktıyı kadansa as

**Files:**
- Create: `ops/oneri_brifingi.py`
- Create: `deploy/oracle-a1/meridian-brifing.service`
- Create: `deploy/oracle-a1/meridian-brifing.timer`
- Modify: `dagit.sh` — `F9_LISTE` (iki satır daha)
- Test: `tests/test_brifing_kadansi_v327.py`

**Interfaces:**
- Consumes: `ops/alarm_backlog_digest.py::main(argv)` — mevcut, değiştirilmez.
  `meridian.notify.send(text: str) -> bool` ve `meridian.notify.configured() -> bool`.
- Produces: `ops/oneri_brifingi.py::ozet_kur() -> dict` — anahtarlar:
  `{"toplam": int, "yeni": int, "mesaj": str, "not": str}`; `mesaj` boşsa teslim yoktur.
  `ops/oneri_brifingi.py::main(argv: list[str] | None = None) -> int` — 0 başarı/sessiz,
  2 hata. `--uygula` olmadan KURU KOŞUM.

**Tasarım kararı:** `alarm_backlog_digest.py` ÇALIŞIYOR ve dokunulmaz. Yeni betik onun
şeklini birebir taklit eder (kuru koşum varsayılan · boşken sessiz · teslimden sonra damga)
çünkü o şekil bu depoda zaten sınanmış.

- [ ] **Adım 1: Çiviyi yaz (kırmızı olacak)**

```python
# tests/test_brifing_kadansi_v327.py
"""BRİFİNG KADANSI: hesaplanan teslim edilir, boşken SESSİZ — v327 (2026-08-27)

ÖLÇÜM (2026-08-27, canlı A1):
    notify_undelivered.json   toplam 310 · MECHANISM_STALE 208 · MIRROR_DRIFT 51 · NAKED_POSITION 9
    ops/alarm_backlog_digest.py  YAZILMIŞ, çalışıyor, ama HİÇBİR KADANSA ASILI DEĞİL
    improvement_proposals.jsonl  16 öneri, teslimat yolu YOK

Yani sistem hesaplıyor ve kimse okumuyor — bu deponun ölçülmüş hastalığı (`candidate_review.json`
günde 23 bin karakter üretiyor ve karar hattında okuyucusu yok).

SESSİZLİK ŞARTI PAZARLIĞA KAPALI: karar döndürmeyen zamanlanmış iş bildirim spam'idir. Yeni
bir şey yoksa mesaj YOKTUR.
"""
from __future__ import annotations

import importlib.util
import pathlib

import pytest

KOK = pathlib.Path(__file__).resolve().parent.parent
BETIK = KOK / "ops/oneri_brifingi.py"
SERVICE = KOK / "deploy/oracle-a1/meridian-brifing.service"
TIMER = KOK / "deploy/oracle-a1/meridian-brifing.timer"


def _yukle():
    assert BETIK.exists(), f"{BETIK} YOK"
    spec = importlib.util.spec_from_file_location("oneri_brifingi", BETIK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_BOSKEN_SESSIZ(monkeypatch, sandbox_state):
    """Okunmamış öneri yoksa mesaj ÜRETİLMEZ. Karar döndürmeyen bildirim spam'dir."""
    mod = _yukle()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [])
    o = mod.ozet_kur()
    assert o["yeni"] == 0
    assert not o["mesaj"], f"boş defterde mesaj üretildi: {o['mesaj']!r}"


def test_YENI_ONERI_MESAJA_GIRER(monkeypatch, sandbox_state):
    """Okunmamış öneri varsa mesajda kimliği ve alanı geçer."""
    mod = _yukle()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        {"ts": "2026-08-27T10:00:00+00:00", "id": "N00017", "alan": "coverage_ariza.hotstate",
         "oneri": "watchdog hotstate sayacını harici süreçten okunur yap", "oncelik": "yuksek"},
    ])
    o = mod.ozet_kur()
    assert o["yeni"] == 1
    assert "N00017" in o["mesaj"] and "coverage_ariza.hotstate" in o["mesaj"]


def test_TESLIMDEN_SONRA_TEKRARLAMAZ(monkeypatch, sandbox_state):
    """Damga basıldıktan sonra aynı öneri ikinci kez bildirilmez."""
    mod = _yukle()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        {"ts": "2026-08-27T10:00:00+00:00", "id": "N00017", "alan": "x", "oneri": "y"},
    ])
    gonderilen = []
    monkeypatch.setattr(mod.notify, "configured", lambda: True)
    monkeypatch.setattr(mod.notify, "send", lambda t: gonderilen.append(t) or True)
    assert mod.main(["--uygula"]) == 0
    assert len(gonderilen) == 1
    assert mod.ozet_kur()["yeni"] == 0, "damga basılmamış — aynı öneri yeniden bildirilir"


def test_KURU_KOSUM_VARSAYILAN(monkeypatch, sandbox_state):
    """`--uygula` olmadan HİÇBİR ŞEY gönderilmez ve damga basılmaz."""
    mod = _yukle()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        {"ts": "2026-08-27T10:00:00+00:00", "id": "N00018", "alan": "x", "oneri": "y"},
    ])
    gonderilen = []
    monkeypatch.setattr(mod.notify, "configured", lambda: True)
    monkeypatch.setattr(mod.notify, "send", lambda t: gonderilen.append(t) or True)
    assert mod.main([]) == 0
    assert not gonderilen, "kuru koşumda gönderdi"
    assert mod.ozet_kur()["yeni"] == 1, "kuru koşumda damga bastı"


def test_BIRIM_ALARM_DIGESTINI_DE_KOSUYOR():
    """Kadans iki teslimatı da tetiklemeli; biri unutulursa 310'luk yığın orada kalır."""
    assert SERVICE.exists() and TIMER.exists(), "systemd birimleri yok"
    s = SERVICE.read_text(encoding="utf-8")
    assert "alarm_backlog_digest.py" in s and "--uygula" in s, "alarm yığını koşulmuyor"
    assert "oneri_brifingi.py" in s, "öneri brifingi koşulmuyor"


def test_TIMER_GUNLUK():
    t = TIMER.read_text(encoding="utf-8")
    assert "OnCalendar=" in t, "timer takvim tanımı yok"
    assert "Persistent=true" in t, (
        "Persistent yok — makine kapalıyken kaçan tetik telafi edilmez")


def test_dagit_F9_birimleri_IZLIYOR():
    metin = (KOK / "dagit.sh").read_text(encoding="utf-8")
    for ad in ("meridian-brifing.service", "meridian-brifing.timer"):
        assert f"deploy/oracle-a1/{ad}|/etc/systemd/system/{ad}" in metin, f"F9 {ad}'i izlemiyor"
```

- [ ] **Adım 2: Kırmızıyı gör**

Run: `.venv/bin/python -m pytest tests/test_brifing_kadansi_v327.py -v`
Expected: 7 test de FAIL (`ops/oneri_brifingi.py YOK`, `systemd birimleri yok`,
`F9 … izlemiyor`).

- [ ] **Adım 3: `ops/oneri_brifingi.py` yaz**

```python
#!/usr/bin/env python3
"""oneri_brifingi.py — okunmamış İYİLEŞTİRME ÖNERİLERİNİN tek-mesajlık özeti.

NEDEN VAR (2026-08-27 ölçümü). `nous_eval.py` (1098 satır) telemetriden kanıt-atıflı yapısal
öneriler üretiyor ve `state/improvement_proposals.jsonl`a yazıyor — canlıda 16 öneri, sonuncusu
24 Ağustos. TESLİMAT YOLU YOK: hiçbir kod bu defteri okuyup operatöre iletmiyor. Sistem
düşünüyor ve kimse dinlemiyor.

ŞEKİL `alarm_backlog_digest.py`den KOPYALANDI ve bu bilinçlidir: kuru koşum varsayılan ·
boşken SESSİZ · teslimden sonra damga · teslim düşerse damga BASILMAZ (yarım teslim "teslim
edildi" sayılmaz). O şekil bu depoda zaten sınanmış; ikinci bir tasarım ikinci bir hata sınıfıdır.

Okur: state/improvement_proposals.jsonl · Yazar: aynı dosyanın DAMGA anahtarı (öneri satırlarına
DOKUNMAZ). Teslimat: meridian.notify.send (scrub + teslim-hatası kaydı orada).
"""
from __future__ import annotations

import argparse
import sys

from meridian import memory, notify, obs, store

DEFTER = "improvement_proposals.jsonl"
DAMGA_DOSYA = "oneri_brifingi_damga.json"
DAMGA = "son_teslim"
LISTE_TAVANI = 8          # mesaj uzunluk zarfı — kalanlar sayıyla beyan edilir


def ozet_kur() -> dict:
    """(toplam, yeni, mesaj, not). `mesaj` boşsa teslim edilecek bir şey YOKTUR."""
    satirlar = [r for r in store.read_jsonl(DEFTER) if isinstance(r, dict)]
    damga = (store.read_json(DAMGA_DOSYA, {}) or {}).get(DAMGA) or {}
    son_ts = str(damga.get("son_ts") or "")
    yeni = [r for r in satirlar if str(r.get("ts") or "") > son_ts]
    if not yeni:
        return {"toplam": len(satirlar), "yeni": 0, "mesaj": "",
                "not": f"yeni öneri yok (defter {len(satirlar)}, damga {son_ts or 'hiç'})"}
    bas = [f"🧠 {len(yeni)} yeni iyileştirme önerisi (defter toplam {len(satirlar)})"]
    for r in yeni[:LISTE_TAVANI]:
        oncelik = r.get("oncelik")
        etiket = f"[{oncelik}] " if oncelik else ""
        bas.append(f"· {r.get('id')} {etiket}{r.get('alan')}: {str(r.get('oneri') or '')[:140]}")
    if len(yeni) > LISTE_TAVANI:
        bas.append(f"… ve {len(yeni) - LISTE_TAVANI} tane daha (state/{DEFTER})")
    return {"toplam": len(satirlar), "yeni": len(yeni), "mesaj": "\n".join(bas), "not": ""}


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

    en_yeni = max(str(r.get("ts") or "") for r in store.read_jsonl(DEFTER) if isinstance(r, dict))

    def _damgala(d: dict) -> bool:
        """`store.update_json` sözleşmesi: belgeyi YERİNDE değiştir ve True dön — yeni sözlük
        döndürmek sessizce hiçbir şey yazmaz."""
        d[DAMGA] = {"ts": memory.now_iso(), "son_ts": en_yeni, "kapsanan": o["yeni"]}
        return True

    store.update_json(DAMGA_DOSYA, _damgala, {})
    obs.log("oneri_brifingi_teslim", yeni=o["yeni"], toplam=o["toplam"], son_ts=en_yeni,
            detail="okunmamış iyileştirme önerileri TEK özet mesajla teslim edildi ve damgalandı")
    print(f"TESLİM EDİLDİ ve damgalandı (yeni={o['yeni']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Adım 4: systemd birimlerini yaz**

`deploy/oracle-a1/meridian-brifing.service`:

```ini
[Unit]
# Hesaplanmış ama teslim edilmemiş çıktıları operatöre iletir. İKİSİ DE boşken SESSİZDİR —
# karar döndürmeyen zamanlanmış iş bildirim spam'idir (spec §8, hata 4).
Description=Meridian brifing — alarm yığını + iyileştirme önerileri (boşken sessiz)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=ubuntu
WorkingDirectory=/opt/meridian
# İki teslimat AYRI: biri düşerse öteki yine koşar (`;` değil ayrı ExecStart satırları
# kullanılmadı — systemd ilk başarısızlıkta durur; `-` öneki hatayı yutar ve devam ettirir).
ExecStart=-/opt/meridian/.venv/bin/python /opt/meridian/ops/alarm_backlog_digest.py --uygula
ExecStart=-/opt/meridian/.venv/bin/python /opt/meridian/ops/oneri_brifingi.py --uygula

[Install]
WantedBy=multi-user.target
```

`deploy/oracle-a1/meridian-brifing.timer`:

```ini
[Unit]
Description=Meridian brifing tetiği (günlük, seans kapanışından sonra)

[Timer]
# 21:00 UTC = ABD kapanışından ~1 saat sonra; EOD turu (~20:30 UTC) bitmiş olur.
OnCalendar=*-*-* 21:00:00 UTC
# Makine kapalıysa açılışta telafi edilir — kaçan tetik sessizce kaybolmaz.
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
```

- [ ] **Adım 5: F9 kayıtlarını ekle**

`dagit.sh` `F9_LISTE` bloğuna iki satır:

```
deploy/oracle-a1/meridian-brifing.service|/etc/systemd/system/meridian-brifing.service
deploy/oracle-a1/meridian-brifing.timer|/etc/systemd/system/meridian-brifing.timer
```

- [ ] **Adım 6: Yeşili gör**

Run: `.venv/bin/python -m pytest tests/test_brifing_kadansi_v327.py -v`
Expected: 7 passed

- [ ] **Adım 7: Kuru koşumla canlı veriye karşı doğrula**

```bash
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'cd /opt/meridian && ./.venv/bin/python ops/oneri_brifingi.py'
```
Expected: `defter: 16 · yeni: 16` ve mesaj basılır; `KURU KOŞU: gönderilmedi` ile biter.
(Betik canlıda henüz YOK — bu adım dağıtımdan SONRA koşulur; Görev 2 commit'i dağıtımı içermez.)

- [ ] **Adım 8: Commit**

```bash
git add ops/oneri_brifingi.py deploy/oracle-a1/meridian-brifing.service \
        deploy/oracle-a1/meridian-brifing.timer dagit.sh tests/test_brifing_kadansi_v327.py
git commit -m "Hesaplanan teslim edilir oldu: alarm yığını + öneri brifingi kadansa asıldı"
```

---

## Görev 3: Tekrarlayan canlı-ölçüm kalıbını araca çevir

**Files:**
- Create: `ops/olcum.py`
- Create: `deploy/hermes/skills/meridian-olcum/SKILL.md`
- Test: `tests/test_olcum_araci_v328.py`

**Interfaces:**
- Consumes: `meridian.codelaw.artifact_graph() -> dict` (anahtarlar `artifacts`, `unread`,
  `violations`) — mevcut.
- Produces: `ops/olcum.py::olay_adlari(desen: str) -> list[str]` — kaynak koddaki
  `obs.log/warn/error/alarm` çağrılarından GERÇEK olay adlarını çıkarır.
  `ops/olcum.py::main(argv) -> int`.

**Neden bu görev:** 2026-08-27 oturumunda canlıya karşı ~60 komut koşuldu; kod anlama tarafında
asıl yavaşlatan şey grep'in yetersizliği DEĞİL, **hangi olay adının aranacağını bilmemekti** —
iki kez tahmin edildi, iki kez SAHTE SIFIR alındı, sonra ad koddan bulundu. Bu, tipli bir
araçla yapısal olarak kapanır. (Zayıf model dersi: tekrarlanan prosedürü koda derle, LLM'i
yalnız karar noktasında çağır.)

- [ ] **Adım 1: Çiviyi yaz (kırmızı olacak)**

```python
# tests/test_olcum_araci_v328.py
"""ÖLÇÜM ARACI: olay adı TAHMİN EDİLMEZ, KODDAN BULUNUR — v328 (2026-08-27)

ÖLÇÜLMÜŞ VAKA (2026-08-27). Canlı teşhis sırasında olay adı iki kez tahmin edildi:
    grep "pozisyon_adet_benimsendi"  → 0   (gerçek ad: `adet_benimsendi`)
    grep "position_drift"            → 0   (öyle bir OLAY yok, o bir ALAN)
Sahte sıfır, "arıza yok" diye okunur. Bu, deponun kayıtlı `olcum-baglami-tuzagi` dersinin
canlı tekrarıdır.

ÇARE ARAÇ: olay adları kaynaktaki `obs.log/warn/error/alarm` çağrılarından ÇIKARILIR; tahmin
edilecek bir şey kalmaz.
"""
from __future__ import annotations

import importlib.util
import pathlib

KOK = pathlib.Path(__file__).resolve().parent.parent
BETIK = KOK / "ops/olcum.py"


def _yukle():
    assert BETIK.exists(), f"{BETIK} YOK"
    spec = importlib.util.spec_from_file_location("olcum", BETIK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_GERCEK_OLAY_ADINI_BULUR():
    """`benimse` desenini arayan, gerçek ad olan `adet_benimsendi`yi bulmalı."""
    mod = _yukle()
    adlar = mod.olay_adlari("benimse")
    assert "adet_benimsendi" in adlar, f"gerçek ad bulunamadı: {adlar}"


def test_OLMAYAN_ADI_UYDURMAZ():
    """`position_drift` bir ALAN adıdır, olay değil. Araç onu olay diye döndürmemeli."""
    mod = _yukle()
    assert "position_drift" not in mod.olay_adlari("drift")


def test_AYRISTIRICI_BAYAT_DEGIL():
    """Regex hiçbir şey görmezse yukarıdaki iki çivi de TRIVIAL geçer — nöbetçi bu."""
    mod = _yukle()
    assert len(mod.olay_adlari("")) >= 200, "olay adı ayrıştırıcısı bayat"


def test_SKILL_ARACA_YONLENDIRIYOR():
    """Skill, ajana 'tahmin etme' demeli — yoksa araç var ama kullanılmaz."""
    s = (KOK / "deploy/hermes/skills/meridian-olcum/SKILL.md").read_text(encoding="utf-8")
    assert "ops/olcum.py" in s, "skill aracı adıyla göstermiyor"
    assert "name:" in s and "description:" in s, "SKILL.md frontmatter eksik"
```

- [ ] **Adım 2: Kırmızıyı gör**

Run: `.venv/bin/python -m pytest tests/test_olcum_araci_v328.py -v`
Expected: 4 FAIL — `ops/olcum.py YOK`.

- [ ] **Adım 3: `ops/olcum.py` yaz**

```python
#!/usr/bin/env python3
"""olcum.py — canlı sistemi TİPLİ sorgulama aracı. LLM yok, tahmin yok.

NEDEN VAR (2026-08-27). Canlı teşhiste olay adı iki kez tahmin edildi ve iki kez SAHTE SIFIR
alındı (`pozisyon_adet_benimsendi` → gerçek ad `adet_benimsendi`; `position_drift` → o bir ALAN,
olay değil). Sahte sıfır "arıza yok" diye okunur — deponun `olcum-baglami-tuzagi` dersi.

Alt komutlar:
    olay <desen>       kaynaktaki GERÇEK olay adlarını listeler (obs.log/warn/error/alarm)

KAPSAM DAR TUTULDU (YAGNI): "bu artefaktı kim okuyor" sorusunu `codelaw` ZATEN cevaplıyor;
ikinci bir sarmalayıcı ikinci bir gerçek olurdu. Ölçülmüş acı olay-adı tahminiydi — araç onu
kapatır, fazlasını değil.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

KOK = pathlib.Path(__file__).resolve().parent.parent
# `obs.log("ad", …)` / `obs.warn('ad')` / `obs.alarm("TOKEN", …)` — ilk konumsal dize.
CAGRI = re.compile(r"""\bobs\.(?:log|warn|error|alarm)\(\s*["']([A-Za-z_][A-Za-z0-9_]*)["']""")


def olay_adlari(desen: str = "") -> list[str]:
    """Kaynakta GERÇEKTEN basılan olay adları; `desen` alt-dizge süzgecidir (boş = hepsi)."""
    adlar: set[str] = set()
    for p in sorted((KOK / "meridian").rglob("*.py")):
        adlar.update(CAGRI.findall(p.read_text(encoding="utf-8", errors="ignore")))
    d = desen.lower()
    return sorted(a for a in adlar if d in a.lower())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    alt = ap.add_subparsers(dest="komut", required=True)
    a1 = alt.add_parser("olay", help="gerçek olay adlarını listele")
    a1.add_argument("desen", nargs="?", default="")
    args = ap.parse_args(argv)

    adlar = olay_adlari(args.desen)
    if not adlar:
        print(f"'{args.desen}' desenine uyan OLAY YOK. Bu bir ALAN adı olabilir — "
              f"defterdeki alanlar olay adı değildir.")
        return 1
    for a in adlar:
        print(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Adım 4: Skill'i yaz**

`deploy/hermes/skills/meridian-olcum/SKILL.md`:

```markdown
---
name: meridian-olcum
description: Meridian olay/artefakt sorgularında tahmin yerine ops/olcum.py kullan
version: 1.0.0
metadata:
  hermes:
    tags: [meridian, olcum, teshis]
---

# Meridian ölçümü — tahmin etme, sor

## Ne zaman kullanılır

- Bir olay defterinde bir şey aranacağı zaman
- "Bu artefaktı kim okuyor / yazıyor" sorusunda
- Bir teşhis sırasında "şu olay hiç basılmış mı" sorusunda

## Kural

**Olay adını TAHMİN ETME.** Önce gerçek adı bul:

    /opt/meridian/.venv/bin/python /opt/meridian/ops/olcum.py olay <desen>

Sonra o adı ara. Tahmin edilen bir ad SIFIR sonuç döndürür ve sıfır "arıza yok" diye okunur.

## Ölçülmüş tuzak

2026-08-27 canlı teşhisinde iki kez tahmin edildi, iki kez sahte sıfır alındı:

    aranan `pozisyon_adet_benimsendi` → 0     gerçek ad: `adet_benimsendi`
    aranan `position_drift`          → 0     o bir ALAN adı, olay değil

## Artefakt okuyucuları

Bu araç o soruyu CEVAPLAMAZ — `codelaw` zaten cevaplıyor ve ikinci bir sarmalayıcı ikinci bir
gerçek olurdu. `codelaw.artifact_graph()` kullan.

## Doğrulama

Araç boş liste döndürürse bu "olay yok" demektir, "aramayı beceremedim" demek değildir —
desen daraltılıp yeniden sorulur.
```

- [ ] **Adım 5: Yeşili gör**

Run: `.venv/bin/python -m pytest tests/test_olcum_araci_v328.py -v`
Expected: 4 passed

- [ ] **Adım 6: Araç gerçekten çalışıyor mu — elle doğrula**

```bash
.venv/bin/python ops/olcum.py olay benimse
.venv/bin/python ops/olcum.py olay reconcile
```
Expected: birincisi `adet_benimsendi` yazar; ikincisi `reconcile_atlandi`, `reconcile_failed`
gibi gerçek adları listeler.

- [ ] **Adım 7: Commit**

```bash
git add ops/olcum.py deploy/hermes/skills/meridian-olcum/SKILL.md tests/test_olcum_araci_v328.py
git commit -m "Ölçüm kalıbı araca derlendi: olay adı artık tahmin edilmiyor, koddan çıkarılıyor"
```

---

## Faz 2'ye bırakılanlar — SESSİZ boşluk değil, beyanlı

Öz-inceleme spec kapsamasını taradı; şu üç madde Faz 1'de KARŞILIKSIZ ve sebebi aynı:
**Faz 1'de profil yok, dolayısıyla kapsanacak bir şey de yok.**

| spec | neden şimdi değil |
|---|---|
| §9.3 `HERMES_WRITE_SAFE_ROOT` bot başına | bot yok — kapsanacak artefakt yok |
| §9.4 çivi 1: HER profil guard kancasını taşır | tek profil var ve Görev 1 onu çiviliyor; "her profil" ancak ikinci profille anlam kazanır |
| §9.4 çivi 3: her botun write-root'u kendi artefaktıyla sınırlı | aynı sebep |

§9.4 çivi 2 (`cron_mode: deny`) Faz 1'de KARŞILANDI (Görev 1).

## Kapanış (Rol-1)

- [ ] **Tam suite, DONMUŞ ağaçta, arka planda**

```bash
.venv/bin/python -m pytest tests/ --durations=25 > /tmp/suite_faz1.txt 2>&1; echo "PYTEST_EXIT=$?" >> /tmp/suite_faz1.txt
```
Bitince: `grep PYTEST_EXIT /tmp/suite_faz1.txt` ve `grep -cE "FAILED|ERROR" /tmp/suite_faz1.txt`.
Yeşil ışığı sarmala sorma, dosyaya sor.

- [ ] **Üretilmiş belgeleri bir kez tazele**

```bash
.venv/bin/python ops/runbook_uret.py
```

- [ ] **Dağıtım** — `./dagit.sh` (kuru koşum) → `./dagit.sh --uygula`

- [ ] **Systemd birimleri OPERATÖR kurar** (dagit bu dosyaları TAŞIMAZ):

```bash
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'sudo install -m 0644 /opt/meridian/deploy/oracle-a1/meridian-brifing.service /etc/systemd/system/ && sudo install -m 0644 /opt/meridian/deploy/oracle-a1/meridian-brifing.timer /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now meridian-brifing.timer'
```

- [ ] **Ajan yapılandırmasını canlıya al** (dagit taşımaz — F9 yalnız RAPORLAR):

```bash
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'cp -p ~/.hermes/config.yaml ~/.hermes/config.yaml.bak-$(date -u +%Y%m%dT%H%M%SZ) && cp /opt/meridian/deploy/hermes/config.yaml ~/.hermes/config.yaml'
```

- [ ] **Doğrula: brifing gerçekten düştü mü**

```bash
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'systemctl status meridian-brifing.timer --no-pager | head -6; journalctl -u meridian-brifing --no-pager -n 20'
```
Beklenen: ilk koşumda 310'luk yığın TEK mesajla teslim edilir ve damgalanır; öneri brifingi
16 öneriyi iletir. İkinci koşumda İKİSİ DE sessizdir — bu, sessizlik şartının kanıtıdır.
