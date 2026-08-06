#!/usr/bin/env python3
"""Renk-rolü emisyon tarayıcısı (D1, 2026-08-07) — meridian/web/*.js.

Bir `class="… pos|neg|warn …"` emisyonu iki sınıftan biridir:

  KOŞULLU  — yalnız bir anomali/hata dalında basılır (ternary dalı, `if (…)` gövdesi,
             `&&`/`||` sağ tarafı, `catch` bloğu). Renk ANOMALİDE çıkar → MEŞRU.
  KOŞULSUZ — veri ne olursa olsun her render'da basılır → SIZINTI ADAYI.

YÖNTEM (iki aşama):
  1. LEKSER — dosya ileri yönde taranır ve her karakter `kod` / `dize` / `yorum`
     olarak damgalanır (şablon literalleri, `${…}` yuvaları, düzenli ifadeler dâhil).
     Bu şart: bir `style="grid-template-columns:64px"` içindeki `:` kod değildir;
     lekser olmadan CSS iki noktası bir ternary dalı sanılır (ölçülmüş yanlış-pozitif).
  2. GERİ YÜRÜYÜŞ — emisyondan geriye, YALNIZ kod damgalı karakterler üzerinde,
     parantez derinliği sayılarak yürünür. Saran ifadedeki (derinlik 0) `?` / `&&` /
     `||` / `if (…)` / `catch` bir KAPI'dır. `??` ve `?.` kapı DEĞİLDİR. Geri-çağrı
     sınırı (`=>`), `${` başı ya da fonksiyon gövdesi kapı BULUNMADAN gelirse emisyon
     KOŞULSUZ sayılır.

Betik yanlış-pozitif tarafına yanlıdır: aday listesi elle adreslenir (hukum.md).
Kullanım: tara_emisyon.py [dosya …] [--liste] [--json ÇIKTI]
"""
import re, sys, json, collections

KOD, DIZE, YORUM = 0, 1, 2
ATTR = re.compile(r'class="([^"]*)"')
TOK = {n: re.compile(r'(?<![\w-])' + n + r'(?![\w-])') for n in ("pos", "neg", "warn")}
INTERP_STRIP = re.compile(r'\$\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}')
OPEN, CLOSE = "([{", ")]}"
KAPI_KW = re.compile(r'\b(if|catch)\s*$')
KAPI_PAR = re.compile(r'\b(if|catch)\s*\([^()]*\)\s*$')
ELSE_KW = re.compile(r'\belse\s*$')
RE_ONCE = re.compile(r'(?:[(,=:\[!&|?{};+\-*%~^]|\b(?:return|typeof|case|in|of|new|delete|void|do|else|yield|await))\s*$')


def lex(src):
    """Her karakteri KOD / DIZE / YORUM olarak damgala.

    Açık yığınlı durum makinesi. Bağlamlar: "kod" (üst düzey ya da `${…}` içi),
    "tmpl" (şablon gövdesi), "kume" (interpolasyon içindeki `{`). Şablon `${…}`
    içi KOD'dur; şablon gövdesi DIZE'dir.
    """
    m = bytearray(len(src))
    tick = {}
    n = len(src)
    yigin = ["kod"]
    i = 0
    while i < n:
        ust = yigin[-1]
        c = src[i]
        if ust == "tmpl":
            if c == "\\":
                m[i] = m[min(i + 1, n - 1)] = DIZE
                i += 2
                continue
            if src[i:i + 2] == "${":
                m[i] = m[i + 1] = KOD
                yigin.append("kod")
                i += 2
                continue
            if c == "`":
                m[i] = DIZE
                tick[i] = "KP"
                yigin.pop()
                i += 1
                continue
            m[i] = DIZE
            i += 1
            continue
        # ---- kod bağlamı ----
        if src[i:i + 2] == "//":
            j = src.find("\n", i)
            j = n if j < 0 else j
            for k in range(i, j):
                m[k] = YORUM
            i = j
            continue
        if src[i:i + 2] == "/*":
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            for k in range(i, j):
                m[k] = YORUM
            i = j
            continue
        if c in "\"'":
            q, j = c, i + 1
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == q or src[j] == "\n":
                    break
                j += 1
            for k in range(i, min(j + 1, n)):
                m[k] = DIZE
            i = min(j + 1, n)
            continue
        if c == "/":
            j = i - 1
            while j >= 0 and (m[j] == YORUM or src[j] in " \t\n"):
                j -= 1
            if j < 0 or RE_ONCE.search(src[max(0, j - 10):j + 1]):
                j, sinif = i + 1, False
                while j < n:
                    if src[j] == "\\":
                        j += 2
                        continue
                    if src[j] == "[":
                        sinif = True
                    elif src[j] == "]":
                        sinif = False
                    elif src[j] == "/" and not sinif:
                        break
                    elif src[j] == "\n":
                        break
                    j += 1
                while j + 1 < n and src[j + 1].isalpha():
                    j += 1
                for k in range(i, min(j + 1, n)):
                    m[k] = DIZE
                i = min(j + 1, n)
                continue
            i += 1
            continue
        if c == "`":
            m[i] = DIZE
            tick[i] = "AC"
            yigin.append("tmpl")
            i += 1
            continue
        if c == "{":
            yigin.append("kume")
            i += 1
            continue
        if c == "}":
            if len(yigin) > 1:
                yigin.pop()          # "kume" ya da interpolasyonun "kod"u
            i += 1
            continue
        i += 1
    return m, tick


def kapi_ara(src, m, tick, idx, limit=20000, dis_butce=200):
    """Emisyondan geriye yürü; SARAN ifadenin kapısını döndür ya da None.

    İKİ SINIR:
      1. Kardeş şablonlar ŞEFFAFTIR — kapanış backtick'i şablon-derinliğini artırır,
         açılış azaltır; yalnız SARAN şablonun açılışı yürüyüşü "dışarı" çıkarır.
      2. Şablonun DIŞINDA yalnız `dis_butce` kadar kod karakteri yoklanır. Sınırsız
         yürüyüş, alakasız bir üst ternary'yi statik nesir emisyonunun kapısı
         sanıyordu (ölçülmüş yanlış-negatif: `SERT (fail-closed)` satırları).
    """
    depth, sab, disari, harcanan = 0, 0, False, 0
    i = idx
    stop = max(0, idx - limit)
    while i > stop:
        i -= 1
        if m[i] == YORUM:
            continue
        ch = src[i]
        if m[i] == DIZE:
            k = tick.get(i)
            if k and depth == 0:
                if k == "KP":
                    sab += 1
                elif sab:
                    sab -= 1
                else:
                    disari = True            # saran şablonun açılışı
            continue
        if sab:
            continue                          # kardeş şablonun içi
        if disari:
            harcanan += 1
            if harcanan > dis_butce:
                return None
        if ch in CLOSE:
            depth += 1
            continue
        if ch in OPEN:
            if depth:
                depth -= 1
                continue
            if ch == "{":
                if i and src[i - 1] == "$":
                    return None               # ${ … } başı — içeride kapı yok
                onc = _kod_onc(src, m, i, 120)
                if KAPI_PAR.search(onc):
                    return "if/catch-blok"
                if ELSE_KW.search(onc):
                    return "else-blok"
                return None
            if ch == "(":
                if KAPI_KW.search(_kod_onc(src, m, i, 40)):
                    return "if/catch"
                continue                      # çağrı parantezi — şeffaf
            continue                          # `[` — şeffaf
        if depth:
            continue
        if ch == "?":
            if src[i - 1:i + 1] == "??" or src[i + 1:i + 2] in ("?", "."):
                continue
            return "ternary"
        if ch == "&" and src[i - 1:i + 1] == "&&":
            return "&&"
        if ch == "|" and src[i - 1:i + 1] == "||":
            return "||"
        if ch == ">" and src[i - 1:i + 1] == "=>":
            return None
        if ch == ";":
            return None
        if ch == "n" and re.search(r'\breturn$', _kod_onc(src, m, i + 1, 8)):
            return _if_bloklu_mu(src, i)
    return None


def _if_bloklu_mu(src, idx):
    """`return`ün üstünde tek satırlık ya da çok satırlı bir `if (...)` var mı?"""
    bas = src.rfind("\n", 0, idx) + 1
    if re.search(r'^\s*\}?\s*(else\s+)?(if|catch)\s*\(', src[bas:idx]):
        return "if/catch-satir"
    onceki = src[:bas].rstrip("\n").rsplit("\n", 1)[-1].strip()
    if re.match(r'^\}?\s*(else\s+)?(if|catch)\s*\(.*\)\s*$', onceki):
        return "if/catch-onceki-satir"
    return None


def _kod_onc(src, m, i, k):
    """i'den geriye k adet KOD karakteri (dize/yorum atlanır)."""
    out, j = [], i - 1
    while j >= 0 and len(out) < k:
        if m[j] == KOD:
            out.append(src[j])
        j -= 1
    return "".join(reversed(out))


def satir_kapisi(src, idx):
    bas = src.rfind("\n", 0, idx) + 1
    head = src[bas:idx]
    if re.search(r'^\s*\}?\s*(else\s+)?(if|catch)\s*\(', head) or re.search(r'^\s*\}?\s*else\b', head):
        return "if/catch-satir"
    return None


def scan(path):
    src = open(path, encoding="utf-8").read()
    m, tick = lex(src)
    lineno, n = [], 1
    for ch in src:
        lineno.append(n)
        if ch == "\n":
            n += 1
    lineno.append(n)
    ks, kl = [], []
    for mt in ATTR.finditer(src):
        body, bstart = mt.group(1), mt.start(1)
        if m[bstart] != DIZE:
            continue
        lit = INTERP_STRIP.sub("\x00", body)
        for name, rx in TOK.items():
            if not rx.search(lit):
                continue
            hb = rx.search(body)
            idx = bstart + (hb.start() if hb else 0)
            g = kapi_ara(src, m, tick, idx) or satir_kapisi(src, idx)
            son = src.find("\n", idx)
            rec = {"dosya": path.rsplit("/", 1)[-1], "satir": lineno[idx], "sinif": name, "kapi": g,
                   "kod": src[src.rfind("\n", 0, idx) + 1:son if son > 0 else len(src)].strip()[:170]}
            (kl if g else ks).append(rec)
    return ks, kl


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--json" in sys.argv:
        args = [a for a in args if a != sys.argv[sys.argv.index("--json") + 1]]
    paths = args or ["/Users/erdemozturk/AI-Trading/meridian/web/app.js"]
    KS, KL = [], []
    for p in paths:
        a, b = scan(p)
        KS += a
        KL += b
    print(f"KOŞULSUZ (sızıntı adayı): {len(KS)}")
    print(f"KOŞULLU  (anomali dalı, meşru): {len(KL)}")
    print(f"TOPLAM literal emisyon: {len(KS) + len(KL)}")
    print("koşulsuz kırılım:", dict(collections.Counter(x["sinif"] for x in KS)))
    if "--liste" in sys.argv:
        for x in KS:
            print(f'{x["dosya"]}:{x["satir"]:<5} {x["sinif"]:<5} {x["kod"]}')
    if "--json" in sys.argv:
        json.dump({"kosulsuz": KS, "kosullu": KL},
                  open(sys.argv[sys.argv.index("--json") + 1], "w"), ensure_ascii=False, indent=1)
