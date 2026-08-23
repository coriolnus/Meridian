# ARAÇ: replay-sweep otomasyon iskeleti (`ops/replay_sweep.py`)

**Tarih:** 2026-08-23 · **Kalem:** OPT Faz-1 (2) / WP3-B ("kart→koşum→CI→hüküm şablonu — bu
hafta 5× elle") · **Test:** `tests/test_replay_sweep_v277.py` (20 sınama)

## Ne ve neden

Bu haftanın dört elle-yazılmış replay-sweep ölçümü (edg045 · edg046 · edg048 · exe008,
`research/olcumler/` altında) aynı omurgayı dört kez yeniden yazdı. İskelet o omurgayı BİR
kez dondurur; kart-özgü olan tek parça (enjeksiyon yüzeyi + öz-sınaması) kart-başına küçük
bir python modülüne iner.

**SINIR BEYANI:** iskelet YENİ ölçüm sınıfı icat etmez — dört emsalin ortaklaştırılmasıdır.
Emsalden sapan kart (farklı şasi, şasi-parametre enjeksiyonu, farklı dünya beklentisi, farklı
bootstrap birimi, künye-tazeleme ihtiyacı, çok-fazlı özel akış) iskeleti KULLANMAZ; ölçümü
elle yazılır.

## Omurga (dört emsalden ölçüldü — donmuş)

| Blok | Kaynak emsal | İskeletteki hâli |
|---|---|---|
| Kart okuma: grid→hücre (ÇARPILARAK) · seed · künye yolu | dört kartın şeması ölçüldü | `kart_oku` — ölçülemeyen alan None + neden, koşum BAŞLAMAZ (uydurma yok) |
| Sandbox kurulumu (şasi modül yükleme + `SANDBOX`→ölçüm dizini + `ARMED_BEKLENEN`→B1) | edg046/048/exe008 `referans_modul` AYNEN | `referans_modul` |
| Motor-sha künye kapısı (ÖN-UÇUŞ; 4 dosya ↔ `motor_sha256.kosum1_once`) | edg048 kill#4 ön-uçuş | `motor_kunye_kiyas` — tutarsızsa DURUR ve raporlar; **tazeleme DAHİL DEĞİL** (Rol-1 kararı) |
| Kontrol-hücresi bayt-özdeşlik kapısı (3 defter sha256 + künye çivisi) | edg046/048/exe008 `sasi_kapisi` | `sasi_kapisi` |
| Hücre-başı motor sha önce/sonra | dört emsal | `hucre_motor_kapisi` |
| Eşlenik ay-kümeli bootstrap (birim=AY, B=5000 donmuş, seed KARTTAN) | edg040→045/046/048/exe008 `delta_pnl_ci` AYNEN | `delta_pnl_ci` |
| DURDU + `sonuc_grid{_smoke}.json` damgası, exit 0/2 | edg048 biçimi kanonik | `rapor_yaz` + akış |
| Artık taraması (eski çıktı/state → DUR, silinmez) | edg048 ön-uçuş | `artik_bul` |

Kart-özgü kalan (iskelete girmedi, modüle iner): enjeksiyon yüzeyi ve sarmalayıcısı,
öz-sınama formülleri (deftere çivileme), sentetik ön-sınama, kol kimliği damgası, yüzeye özgü
ek raporlar (yer-değiştirme, medyan çapası, H1/H2/H3 analizleri vb.).

## Enjeksiyon modülü arayüzü (edg046 sarmalayıcı deseni)

Zorunlu: `KONTROL_HUCRE` (dict) · `yeni_kayit()` · `enjekte(hucre, kayit, kontrol=False)`
(context manager; süreç-içi yama, finally ile geri alınır; **kontrol hücresinde bayt-nötr**
olmalı — bayt-özdeşlik kapısı nötrlüğü kanıtlar) · `oz_sinama(hucre, kayit, ciktilar,
kontrol=False)` (dönüşte `kill2_gecti` zorunlu; sayı getirir, hüküm vermez) ·
`kol_kimligi(hucre, kontrol=False)`.

İsteğe bağlı: `on_sinama()` (sentetik ön-uçuş; `gecti` False ise koşum başlamaz) ·
`KUNYE_YOLU` (kart künyeyi anmıyorsa beyanlı yedek — EDG-045 kartı emsal vaka) ·
`run_adi(hucre)`.

## Kullanım

```bash
# 1) örnek enjeksiyon stub'ı üret (stub güvenli: on_sinama gecti=False — doldurulmadan koşamaz)
.venv/bin/python ops/replay_sweep.py --stub research/olcumler/<dizin>/enjeksiyon.py

# 2) stub'ı kartın yüzeyine göre doldur (yüzey KODDAN okunur; satır çivisi/tekillik assert'i)

# 3) duman (kablo sınaması; Δ/CI değerlendirilmez)
.venv/bin/python ops/replay_sweep.py --kart research/cards/X.yaml \
    --enjeksiyon <modul.py> --dizin research/olcumler/<dizin> --smoke

# 4) tam koşum → sonuc_grid.json (exit 0) ya da DURDU damgası (exit 2)
.venv/bin/python ops/replay_sweep.py --kart ... --enjeksiyon ... --dizin ...
```

## Disiplin damgaları

- **HÜKÜM YOK:** rapor `hukum_yok` beyanı taşır; success_metric/kill okuması Rol-1'in.
  Emsallerdeki kill#N numaraları KARTA aittir; iskelet kapıları adla anar.
- **K-defteri:** iskelet K SAYMAZ (`k_defteri_beyani`); hücre listesi karttan çarpılarak
  türetilir, yalnız bilgi. Kart 048 gibi kontrol değerini grid'e yazan kartta o hücre normal
  hücre olarak da koşulur — çakışmayı kart tasarımı/Rol-1 yönetir, iskelet yorum yapmaz.
- **Kart DOKUNULMAZ:** salt okuma; karta tek bayt yazılmaz.
- **UYDURMA YASAĞI / YASA-4:** ölçülemeyen alan None + neden; takvim-dışı işlem, yakalama
  dökülemedi vb. sessiz yutulmaz, adıyla sayılır.
- **Motor importu:** iskeletin importu motor yüklemez; `meridian` yalnız koşum anında,
  salt-okuma amaçlı geç-yüklenir (bootstrap için numpy yeter).

## Doğrulama kanıtı (2026-08-23)

- `tests/test_replay_sweep_v277.py`: 20/20 geçti (`grep -E "FAILED|ERROR"` boş).
- Salt-okuma pozitif kontrol, dört gerçek kart üstünde: hücre sayıları 3/4/2/8 (ÇARPILARAK),
  seed dördünde 20260812, künye 046/048/exe008'de `edg032c_taban_2026-08-22/TABAN_KUNYESI.json`
  olarak tekilleşti; 045 kartı künyeyi anmadığından None + neden (modül yedeği bu vaka için).
