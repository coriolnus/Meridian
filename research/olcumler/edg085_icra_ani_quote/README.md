# EDG-2026-085 Senaryo-A — icra-anı IEX quote kaydı (tick pilotu)

Kart: `research/cards/EDG-2026-085-icra-ani-quote-kaydi-senaryo-a.yaml` (eşik/pencere/kill listesi
ORADA; burada DEĞİŞTİRİLMEZ). Plan: `docs/superpowers/plans/2026-09-13-tick-pilot-senaryo-a.md`.

## Parçalar

| Dosya | Ne |
|---|---|
| `taban_orneklem.sh` | ADIM-0 (3) pilot ÖNCESİ taban örnekleyicisi (A1 timer'ı; çıktı `/opt/veri/olcum/edg085/taban.jsonl`) |
| `rapor.py` | ÇEVRİMDIŞI rapor aracı — kayıt + defterler → `sonuc_<bitis>.json` + `rapor_<bitis>.md` |
| `meridian/quotecapture.py` | motor tarafı: halka tamponu · emir pencereleri · abone kümesi · JSONL yazıcı |
| `deploy/oracle-a1/meridian.service.d/55-edg085-quote.conf` | pilot bayrağı + kayıt dizini (varsayılan KAPALI) |

## Pilot AÇMA reçetesi (Rol-1; en erken 2026-09-21, 5 geçerli CPU taban seansı şartıyla)

1. Drop-in'de bayrağı çevir: `Environment=MERIDIAN_QUOTE_CAPTURE=1`
   (`deploy/oracle-a1/meridian.service.d/55-edg085-quote.conf`; kayıt dizini satırına DOKUNMA).
2. Commit + push → A0 rolü: `ansible-playbook deploy/ansible/site.yml` (drop-in glob'u `.conf`
   dosyasını otomatik alır; `dropin_kaynaklari` tek kaynaktır).
3. A1'de birimi yeniden başlat — komut HER ZAMAN ssh sarmalı yazılır:
   `ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'sudo systemctl daemon-reload && sudo systemctl restart meridian'`
4. DOĞRULA (kurulu ≠ çalışır): `/api/diagnostics` → `marketstream.quote_capture.aktif == true`,
   `quote_capture.dizin == "/opt/veri/olcum/edg085/kayit"`. İlk dolumdan sonra
   `quote_capture.satir_bugun > 0` ve kayıt dizininde `edg085_<gün>.jsonl` + `edg085_ham_<gün>.jsonl`.
5. Pilot günlüğünü karta yaz (`adim_0_kaydi_*` desenindeki gibi: tarih + doğrulanan alanlar).

## Pilot KAPATMA (kill#8 — fizibilite tavanı aşılırsa ya da pencere dolunca)

Aynı adımlar, bayrak `MERIDIAN_QUOTE_CAPTURE=0`. Kapalıyken motorun davranışı bit-özdeştir:
abonelik mesajı gönderilmez, `q` çerçeveleri yok sayılır, mirror kancası erken döner ve sağlık
`{"aktif": false}` der. Kayıt dosyaları SİLİNMEZ (kanıt); rapor aracı onları sonradan da okur.

## Rapor koşumu (A1'de salt-okur; çıktı repo DIŞI bir dizine)

```
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 \
  'cd /opt/meridian && .venv/bin/python -m research.olcumler.edg085_icra_ani_quote.rapor \
     --kayit-dizin /opt/veri/olcum/edg085/kayit --state-dizin /opt/meridian/state \
     --baslangic 2026-09-21 --bitis 2026-10-17 \
     --taban /opt/veri/olcum/edg085/taban.jsonl --pilot-taban /opt/veri/olcum/edg085/taban.jsonl \
     --cikti-dizin /opt/veri/olcum/edg085 --pk-sentetik'
```

`--taban` ile `--pilot-taban` AYNI dosya olabilir: araç pencereyi tarihe göre değil VERİLEN
dosyaya göre ayırır, yani pilot öncesi/sonrası kesitleri ayrı dosyalara ayırmak (ya da iki kez
koşmak) Rol-1'in işidir — araç bunu kendiliğinden bölmez ve bölüyormuş gibi de yapmaz.

Çıkış kodları: `0` rapor yazıldı · `1` hata · `2` pozitif kontrol KALDI (kill#7: sayı yayılmaz).

## PK-2 (gerçek) ELLE yapılır

Rastgele 5 canlı dolumun kayıt satırı `edg085_ham_<gün>.jsonl` çerçevesiyle ELLE eşlenir. Araç bunu
otomatik saymaz; `sonuc.json` içinde `pk.gercek.hukum` None'dır ve nedeni "elle — Rol-1" yazar.
Üç PK'dan biri KALDIysa hiçbir K sayısı yayılmaz (kart kill#7).
