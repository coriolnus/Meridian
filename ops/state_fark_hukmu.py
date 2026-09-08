#!/usr/bin/env python3
"""ops/state_fark_hukmu.py — versiyonlu state dosyası için canlı↔repo HÜKMÜ ([1b] kapısı).

NEREDEN GELDİ. Gövde `dagit.sh`ın [1b] adımında `uv run python - <<'PY'` heredoc'u olarak
yaşıyordu. TSK-176 Faz A1'de dosyaya çıkarıldı: `deploy/ansible/dagit.yml` playbook'u aynı hükmü
verecek ve gömülü çok-satır python bir Ansible görevinde YASAK (A0 kuralı + 2026-07-30
IndentationError vakası — girintisi bozulan gömülü gövde, kapıyı bakım penceresinin ortasında
düşürür). DAVRANIŞ BİREBİR TAŞINDI, bir satır bile eklenmedi: aynı düzleştirme, aynı üç rapor
satırı, aynı iki hüküm jetonu.

KOMUT SATIRI SÖZLEŞMESİ (ops/ betiklerinin sözleşmesi `main()` değil KOMUT SATIRIdır):

    python ops/state_fark_hukmu.py <canlı-dosya> <repo-dosya>

Çıkış kodu HER ZAMAN 0 — hüküm ÇIKIŞ KODUYLA değil son satırdaki jetonla söylenir:

    HUKUM=KOPYALA   canlıda repo-dışı anahtar YOK → fark repo'nun ilerlemesidir
    HUKUM=ENGEL     canlıda repo-dışı anahtar VAR, ya da dosya AYRIŞTIRILAMADI (fail-closed)

Öncesindeki satırlar insan içindir (repoda YENİ / DEĞER farkı / CANLIDA REPO-DIŞI ANAHTAR).
Çağıran son `HUKUM=` satırını okur; kalanını operatöre basar.

NEDEN İKİ JETON, ÜÇ DEĞİL. Plan metni bir üçüncü jetondan (`OPERATOR`) söz ediyordu; ölçüldü
(2026-09-08, dagit.sh gömülü gövdesi): "operatöre bırakılan" ÇAĞIRANIN etiketidir — `ENGEL`
zaten "hüküm operatörün" demektir ve bash tarafı onu öyle basar. Üçüncü bir jeton eklemek,
sözlüğü okuyan çivileri (v172 davranış ailesi) ve dagit'in `grep '^HUKUM='` dalını sessizce
ayrıştırırdı. Davranış birebir kuralı ağır bastı.

NEDEN ANAHTAR DÜZEYİ, HAM SATIR DEĞİL. `goal.yaml`/`bounds.yaml` yorum ağırlıklıdır (mezar
taşları, kanıt blokları); repo tarafında bir yorumun yeniden yazılması `diff`te "canlıda olup
repoda olmayan satır" gibi görünür. Satır bazlı bir kapı her yorum düzenlemesinde ENGEL derdi —
yani hiç kopyalamazdı, kapı olmayan bir kapı.

OKUYUCU (YASA 6): `dagit.sh` [1b] adımı · `deploy/ansible/dagit.yml` (Task 2) ·
`tests/test_ansible_dagit_v452.py` bölüm A4a · `tests/test_altyapi_kucukler_v172.py` ⑤ ailesi.
"""

from __future__ import annotations

import sys

import yaml


def duz(d, on: str = "") -> dict:
    """Yaprak yollara düzleştir — iç içe blok (goal.execution_v2) da anahtar düzeyinde kıyaslansın."""
    out: dict = {}
    if isinstance(d, dict):
        for k, v in d.items():
            yol = f"{on}{k}"
            if isinstance(v, dict):
                out.update(duz(v, yol + "."))
            else:
                out[yol] = v
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(f"kullanım: {argv[0]} <canlı-dosya> <repo-dosya>", file=sys.stderr)
        return 2
    try:
        canli = duz(yaml.safe_load(open(argv[1], encoding="utf-8")) or {})
        repo = duz(yaml.safe_load(open(argv[2], encoding="utf-8")) or {})
    except Exception as e:  # sessiz-yutma DEĞİL: hata türü+metni ADIYLA basılır ve hüküm ENGEL olur
        # AYRIŞTIRILAMAYAN DOSYA "fark yok" DEĞİLDİR: hüküm verilemedi → ENGEL (fail-closed).
        print(f"      YAML okunamadı: {type(e).__name__}: {e}")
        print("HUKUM=ENGEL")
        return 0

    canli_fazla = sorted(set(canli) - set(repo))       # canlıda VAR, repoda YOK → elle değişiklik
    repo_yeni = sorted(set(repo) - set(canli))         # repoda VAR, canlıda YOK → w_turnover sınıfı
    deger = sorted(k for k in set(canli) & set(repo) if canli[k] != repo[k])
    if repo_yeni:
        print(f"      repoda YENİ (canlı hiç görmedi): {', '.join(repo_yeni[:12])}"
              + (f" (+{len(repo_yeni) - 12})" if len(repo_yeni) > 12 else ""))
    if deger:
        print("      DEĞER farkı: " + ", ".join(f"{k}: canlı={canli[k]!r} repo={repo[k]!r}"
                                                for k in deger[:8])
              + (f" (+{len(deger) - 8})" if len(deger) > 8 else ""))
    if not (repo_yeni or deger or canli_fazla):
        print("      anahtar/değer düzeyinde fark YOK — ayrım yalnız yorum/biçim")
    if canli_fazla:
        print(f"      CANLIDA REPO-DIŞI ANAHTAR: {', '.join(canli_fazla[:12])}"
              + (f" (+{len(canli_fazla) - 12})" if len(canli_fazla) > 12 else ""))
        print("HUKUM=ENGEL")
    else:
        print("HUKUM=KOPYALA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
