# Akıbet Defteri — uygulama planı

> **Ajan işçiler için:** ZORUNLU ALT-SKILL: superpowers:subagent-driven-development.

**Hedef:** Önerilerin (dört kaynak) karar→sonuç zinciri A1'de tek append-only defterde kayıt
altına alınır; `ops/akibet.py` aracı yazar/listeler; sef brifingi "16 yeni" yerine
açık/karara-bağlandı ayrımıyla ve her brifingde yaş listesiyle konuşur.

**Spec:** ROADMAP §7 "AKIBET DEFTERİ TASARIM KARARLARI (2026-08-31 akşam)" — bağlayıcı karar
kaydı. İCRA SIRASI kalemi. Hindsight tasarımı §2 (akibet bank'i buradan ingest edecek — bu
dalgada Hindsight işi YOK).

**Ölçülmüş zemin (2026-08-31):**
- `state/improvement_proposals.jsonl` A1'de: 16 satır, alanlar `ts,id(N#####),hafta,alan,gozlem,oneri,beklenen_etki,onerilen_olcum`. N-serisinin DOĞUM kaydı BURASI — kopyalanmaz.
- Sef önerileri `ops/oneri_brifingi.py::ozet_kur()` üzerinden okur (`sef_brifingi.py:127,299` sevk);
  damga da orada. Süzgeç `ozet_kur`'a girer, sef gövdesi değişmez (KAYNAK_ADLARI metni hariç gerekirse).
- `ops/filo.py` A1-kimlik/ssh kurucularını taşır (`varsayilan_host/varsayilan_anahtar/ssh_sarmali/_kos`)
  — akibet.py bunları İTHAL eder (üçüncü kimlik kopyası YASAK; ops/ paket değil: `sys.path.insert(0,
  os.path.dirname(__file__))` + `import filo` deseni, dosya başında beyanlı).
- Alınmış vNNN: …v348. Bu plan **v349** alır (grep temiz, 2026-08-31).
- Etkileşimsiz ssh PATH dersi (bugün, k1): uzak komutlarda yalnız sistem araçları kullan
  (`sh/flock/tail/cat/date`) — `~/.local/bin` gerekmez, gerekirse PATH öneki.

## Global Constraints

- AJAN GİT: yalnız salt-okunur beyaz liste; commit Rol-1'in. TEK pytest, ardışık, hedefli.
- `ops/akibet.py` `meridian` İTHAL ETMEZ (stdlib + `import filo`); sözleşmesi KOMUT SATIRIdır;
  teslimden önce `listele` operatör biçiminde BİR kez gerçekten koşulur (18-çivi vakası).
  Gerçek ssh testte ÇAĞRILMAZ (v348'in nişancı deseni aynen).
- DEFTER: `/opt/meridian/state/oneri_akibet.jsonl`, append-only, UTF-8, satır=JSON. Uzak yazım
  `flock` ile ve YAZIM DOĞRULANIR: append sonrası `tail -1` geri okunur, yazılan satırla bayt
  kıyaslanır — eşleşmezse KIRMIZI (sahte-başarı sınıfı; RC'ye güvenilmez).
- Satır şeması (üç olay türü):
  `{"ts": "...", "olay": "oneri|karar|sonuc", "oneri_id": "...", "kaynak": "hermes_reflect|rol1|operator|sef|bekci|karne", ...}`
  · `olay=oneri` (yalnız N-serisi DIŞI kaynaklar — metin alanı `oneri`, kimlik `AKB-####` sıralı)
  · `olay=karar`: + `karar: "uygulandi|reddedildi|ertelendi"`, `gerekce` (≥20 karakter), `karar_veren: "operator|rol1"`
  · `olay=sonuc`: + `ozet`, opsiyonel `ref` (commit/kart/yol).
  Aynı `oneri_id` için SON karar satırı geçerlidir (düzeltme = yeni satır; silme yok).
- AÇIK tanımı TÜRETİLİR: (improvement_proposals'taki N-id'ler ∪ defterdeki `olay=oneri` id'leri)
  − (defterde `olay=karar` taşıyanlar). İki dosya tek gerçeğin iki YARISIDIR, kopya değil.
- Yasa 4 işaretli except; Yasa 6: her yeni alanın okuyucusu bu dalgada var (listele + sef).
- Uydurma yasağı: defter okunamazsa/`olculemedi` ise sef öneri bölümü "akıbet ölçülemedi —
  ham sayım: N" der; ESKİ davranışa sessizce düşmez, düştüğünü SÖYLER.

### Task 1: `ops/akibet.py` + `tests/test_akibet_defteri_v349.py` (bölüm A-D)

**Üretilen arayüz (T2 buna bağlanır):**
```python
# akibet.py içinde, saf (ssh'sız) çekirdek — T2 oneri_brifingi bunu İTHAL eder:
def akibet_turet(proposals_satirlari: list[dict], defter_satirlari: list[dict],
                 simdi_ts: str) -> dict:
    """→ {"acik": [{"oneri_id","kaynak","yas_gun","ozet"}...],   # yaş = doğumdan bugüne, tam gün
         "kararlar": [{"oneri_id","karar","karar_veren","ts","gerekce"}...],  # ts sıralı, TÜM tarihçe
         "sayilar": {"acik": n, "uygulandi": n, "reddedildi": n, "ertelendi": n}}
    Bozuk satır DÜŞÜRÜLMEZ: {"olculemeyen": [satir_no...]} alanına sayılır (v347 emsali)."""
```
- Alt komutlar (hepsi `--host/--anahtar` + `MERIDIAN_A1_*` env destekli, filo deseni):
  · `listele` — açık öneriler yaşlarıyla + son 5 karar (uzak: iki dosyayı `cat` ile çeker,
    türetim YEREL `akibet_turet` ile; çıktı tablo + `AKIBET: <acik> açık` özet satırı)
  · `oneri "<metin>" --kaynak rol1|operator` — AKB-#### kimlik üretir (defterdeki en büyük+1),
    doğum satırı append eder
  · `karar <id> uygulandi|reddedildi|ertelendi --gerekce "..." --veren operator|rol1` —
    id açıklar arasında değilse KIRMIZI (var olmayan/zaten kapalı öneriye karar yazılmaz;
    `--zorla` ile karar DEĞİŞTİRME beyanlı)
  · `sonuc <id> --ozet "..." [--ref ...]` — id defterde karar taşımıyorsa KIRMIZI (sonuç karardan önce gelmez)
  · ortak `--komut-yaz` (v348 sözleşmesi: BASAR, KOŞMAZ — her dalda, `--zorla` dahil; j2 sınıfı çivi)
- Uzak append tek şablon: `flock /opt/meridian/state/oneri_akibet.jsonl.lock sh -c 'printf %s\\n <json> >> defter && tail -1 defter'` — kurucu saf fonksiyon, JSON kabuk-güvenli tek-tırnak kaçışıyla (shlex.quote; v348 enjeksiyon çivisi sınıfı `"; DROP` metinli öneriyle).
- TDD sırası: her alt komut için önce kırmızı çivi. Zorunlu çiviler: yazım-doğrulama (tail
  eşleşmezse KIRMIZI — mutasyonla ısırt) · AÇIK türetimi (karar alınca düşer; `ertelendi`
  AÇIK SAYILMAZ ama sayilar'da görünür) · AKB sayaç çakışmasızlığı · bozuk-satır olculemeyen ·
  ssh nişancısı (testte gerçek ssh yok) · `--komut-yaz` her dalda.
- Mutasyon asgarisi 8; hedefler: tail-doğrulama kaldır · flock kaldır · açık-türetimde karar
  süzgecini kaldır · AKB sayacını sabitle · gerekce-uzunluk denetimi kaldır.

### Task 2: `ops/oneri_brifingi.py` süzgeci + `tests/test_akibet_defteri_v349.py` (bölüm E)

- `ozet_kur()` akıbet defterini okur (dosya yolu sabiti `sef_brifingi` ile AYNI kaynaktan;
  A1'de yerel dosya okuması — bu kod A1'de koşar, ssh GEREKMEZ) ve `akibet_turet` ile birleştirir.
  Çıktı özetine üç blok girer: `yeni` (son damgadan beri doğan — mevcut damga mekanizması) ·
  `karara_baglanan` (son damgadan beri karar satırı yazılanlar, birer cümle) · `acik_yas_satiri`
  (HER brifingde: "3 açık: N00005 21g · N00012 9g · AKB-0003 2g" — tek kompakt satır, yaş sırasına
  göre azalan). Karara bağlanmış öneri "yeni" LİSTESİNE BİR DAHA GİRMEZ.
- Defter YOKSA (henüz hiç karar yazılmadıysa dosya olmayabilir): boş defter = herkes açık —
  bu ÖLÇÜLMÜŞ durumdur, `olculemedi` DEĞİL; dosya var ama OKUNAMIYORSA `olculemedi` + neden
  (Global Constraints'teki dürüst-düşüş cümlesi).
- Damga sözleşmesi DEĞİŞMEZ (damgalanan=["oneri"] mekaniği aynen); LLM prompt'una giren veri
  bloğu bu üç bloğu VERİ olarak taşır (çit mevcut desenle).
- Çiviler (bölüm E): karara-bağlananın yeniden-"yeni"-sayılmaması (asıl çivi — mutasyonla) ·
  yaş satırının her koşumda üretilmesi · boş-defter/ok, bozuk-defter/olculemedi ayrımı ·
  sef mevcut aile yeşil kalır (`test_sef_*` ilgili dosyalar koşulur).

## Görev sonrası — Rol-1
`listele` gerçek koşum (operatör biçiminde) · A1'de defter dosyasını İLK kararla açma (ilk
gerçek kayıt: bu akşamki brifingden sonra operatörle) · dağıtım (oneri_brifingi A1'de koşar —
dagit) · tahta/İCRA SIRASI işareti · Hindsight tasarımına "akibet bank hazır-kaynak" notu.
