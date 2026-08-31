# Ölçüm — bot sunum modeli A/B: Super vs Ultra, GÜNCELLENMİŞ SOUL'la (2026-08-31)

**Soru (operatör):** üslup bloğu eklenmiş SOUL'la hangisi daha iyi sonuç verir —
`nvidia/nemotron-3-super-120b-a12b:free` (bugünkü) mü, `nvidia/nemotron-3-ultra-550b-a55b:free` mı?
**Yöntem:** A1 üzerinde (canlı anahtar/egress ile) doğrudan OpenRouter çağrısı; sistem promptu =
güncellenmiş SOUL; kullanıcı promptu = bugünkü GERÇEK canlı koşumların içeriğinden yeniden kurulmuş
gün-verisi (VERI-çit biçimi aynen) + boş-kaynak SESSIZ senaryosu. Deterministik denetimler:
terim korunumu · çeviri-imzası · en-uzun-cümle · SESSIZ çıplaklığı · süre/token.
Betik `meridian` import etmez (obs'a ulaşamaz); ham çıktılar A1 `/tmp/model_ab/`te, yerel kopya
scratchpad'te. Bu belge `OLCUM-MODEL-BUTCESI-2026-08-27.md`nin devamıdır ve onun bir hükmünü
GÜNCELLER (aşağıda).

## Sonuç tablosu

| Hücre | süre | üretim token | çıktı | terim kaybı | en uzun cümle |
|---|---|---|---|---|---|
| super/sef @1500 | 17,9 sn | 1500 (TAVAN) | 158 krkt KIRPIK | 7/7 KAYIP | — |
| super/sef @8000 (canlı tavan) | 29,0 sn | 1207 | 959 krkt | 0 | 228 |
| super/bekci @1500 | 27,5 sn | 1400 | 606 krkt | 3/5 | 218 |
| super/bekci @8000 | 53,8 sn | **2403** | 403 krkt | 2/5 | 139 |
| ultra/sef @1500 | 19,6 sn | 658 | 880 krkt | 1/7 (reflection; kırpılmadan) | 174 |
| ultra/bekci @1500 | 9,5 sn | 777 | 508 krkt | 2/5 (top-3 seçimi, akıcılık değil) | 92 |
| sessiz senaryosu | ikisi de bir kez ÇIPLAK `SESSIZ` ✓; ikisi de bir kez `:free` API hıçkırığı (KeyError choices — fallback ham teslimi kapsar) | | | | |

## Hüküm: ULTRA — dört eksende de üstün ya da eşit

1. **Verim/maliyet-zaman:** Super gizli akıl-yürütmeye token yakıyor — 403 karakterlik çıktı için
   2.403 token / 53,8 sn (bekci@8000). Ultra aynı sınıf işi 658-777 token / 9,5-19,6 sn'de bitirdi.
   Super'in yakımı gerçek zaman-aşımı riskidir (120 sn profil tavanının yarısına tek hücrede geldi).
2. **Terim sadakati:** eşdeğer (Super@8000 0 kayıp, Ultra 1; bekci kayıpları iki modelde de top-3
   SEÇİMİ, akıcılık arızası değil). Çeviri-imzası ("gemi" sınıfı) İKİSİNDE DE sıfır — yeni üslup
   bloğu bu sınıfı iki modelde de kapattı.
3. **Cümle disiplini:** Ultra belirgin iyi (92-174 vs 218-228).
4. **Nitel:** Ultra çıktıları yayınlanabilir kalitede (doğru süre çevirimi "157 sa=6,5 gün",
   NE·NEDEN·NE YAPMALI yapısı kurulu); Super@1500 dejenere, @8000 kabul edilebilir ama gevşek.

**BÜTÇE BELGESİNİN GÜNCELLENEN HÜKMÜ:** 2026-08-27 ölçümü Ultra'yı 25,8 tok/sn ile "120 sn
tavana sığmaz" diye elemişti — o hüküm 8.000 token'lık TAM ÜRETİM varsayımıyla doğruydu. Bugünkü
ölçüm iki şeyi gösterdi: (a) Ultra bugün 33-82 tok/sn koşuyor, (b) brifing işi doğal olarak
~650-780 token'da bitiyor — tavana hiç yaklaşmıyor. Eleme gerekçesi bugünkü işe uygulanamaz.

## Karar ve yayılım

Üç profilin `model.default`ı `ultra-550b-a55b:free`ya çevrilir (max_tokens aynen — Ultra yakmıyor,
tavan zararsız). Yayılım beyin-zinciri dersiyle: repo config → commit → dağıtım → canlıda
`hermes profile update <ad> --force-config` → elle test-ateşleme → journal'dan üçlü doğrulama.
Bu A/B, "dolu-cevap sınaması"nın kendisidir (canlı anahtar/egress ile koşuldu); test-ateşleme
harness-içi son doğrulamadır. `:free` hıçkırığı iki modelde de var — LLM-düşerse-ham-teslim
sözleşmesi değişmiyor.
