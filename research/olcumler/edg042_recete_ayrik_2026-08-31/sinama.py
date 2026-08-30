"""P-3 / AYRIK — `ts` bölme anahtarının SENTETİK sınaması. SAYILAR ÖLÇÜM DEĞİLDİR.

Gerçek veriyle sınanamayan iki dal var: (a) sınırın tam üstü/altı — canlı örneklemde sınıra
saniye hassasiyetinde yakın satır yok; (b) `ts` okunamayan satır — bugün 17/17 satırda `ts` dolu.
Bu dosya o dalları sentetik girdiyle ateşler. Emsal: R2'nin sinama.py/sinama.json'u.
"""
import json
from pathlib import Path

import olcum

SINIR = olcum.PENCERE_SINIRI          # "2026-08-23T14:53:43+00:00"
VAKALAR = [
    ("SNR-1sn-once", "2026-08-23T14:53:42+00:00", "giris_once",
     "sınırdan 1 sn ÖNCE gönderildi — eski rejim"),
    ("SNR-tam",      SINIR,                        "giris_1345",
     "sınırın TAM ÜSTÜ — sınır dahil yeni rejime sayılır (ts >= sınır)"),
    ("SNR-1sn-sonra","2026-08-23T14:53:44+00:00", "giris_1345",
     "sınırdan 1 sn SONRA — yeni rejim"),
    ("GERCEK-DE",    "2026-08-21T20:32:22+00:00", "giris_once",
     "DE/PANW'nin gerçek gönderim damgası — eski EOD-GTC yolu"),
    ("GERCEK-CRM",   "2026-08-28T13:45:00+00:00", "giris_1345",
     "CRM'nin gerçek gönderim damgası — 13:45 penceresi"),
    ("TZ-FARKLI",    "2026-08-23T10:53:42-04:00", "giris_once",
     "saat dilimi farklı ama AYNI an-1sn — karşılaştırma UTC'ye normalize olur"),
    ("YOK",          None,                         None, "ts yok → kol belirlenemez"),
    ("BOS",          "   ",                        None, "ts boş → kol belirlenemez"),
    ("BICIMSIZ",     "21 Ağustos 2026",            None, "ts biçimsiz → kol belirlenemez"),
    ("TZ-SIZ",       "2026-08-21T20:32:22",        None,
     "saat dilimSİZ damga kıyaslanamaz → kol belirlenemez (uydurma yok)"),
]

sonuc, gecti = [], True
for ad, ts, beklenen, aciklama in VAKALAR:
    olculen = olcum.gonderim_kolu(ts)
    ok = (olculen == beklenen)
    gecti &= ok
    sonuc.append({"vaka": ad, "ts": ts, "beklenen": beklenen, "olculen": olculen,
                  "gecti": ok, "aciklama": aciklama})

rapor = {"kart": "EDG-2026-042", "konu": "P-3/AYRIK — ts bölme anahtarı sentetik sınaması",
         "sinir": SINIR, "hukum": "GEÇTİ" if gecti else "KALDI",
         "beyan": ("SAYILAR ÖLÇÜM DEĞİLDİR — sentetik girdilerle yalnız KOL ATAMA mantığı "
                   "sınanır. 'Varsayılan kol' kabulünün YASAK olduğu dört vakayla çivilenir "
                   "(YOK/BOS/BICIMSIZ/TZ-SIZ): dördünde de kol None döner, satır olculemedi'ye "
                   "düşer ve bps hesaplanmaz."),
         "vakalar": sonuc}
Path("sinama.json").write_text(json.dumps(rapor, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"hukum": rapor["hukum"], "gecen": sum(1 for v in sonuc if v["gecti"]),
                  "toplam": len(sonuc)}, ensure_ascii=False))
