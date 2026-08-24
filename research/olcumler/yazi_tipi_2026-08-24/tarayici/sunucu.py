#!/usr/bin/env python3
"""Ölçüm sayfası için YEREL, GEÇİCİ statik sunucu + tek yazma ucu.

Neden `serve.sh` DEĞİL: CLAUDE.md §5 yerelde uygulamayı koşmayı yasaklıyor (çift emir riski).
Bu sunucu yalnız bu klasörü servis eder; Meridian uygulaması yüklenmez, hiçbir /api/* ucu yok.
`POST /kaydet` yalnız TEK dosyaya yazar: olcum_sonucu.json — 35 KB'lik ölçüm kaydını
tarayıcıdan diske almanın yolu. Başka yol yazılamaz.
"""
import http.server, json, os, socketserver

KOK = os.path.dirname(os.path.abspath(__file__))
HEDEF = os.path.join(KOK, "olcum_sonucu.json")

class Islem(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=KOK, **k)

    def do_POST(self):
        if self.path.split("?")[0] != "/kaydet":
            self.send_error(404, "yalnizca /kaydet"); return
        n = int(self.headers.get("Content-Length", 0))
        ham = self.rfile.read(n).decode("utf-8")
        veri = json.loads(ham)                      # bozuk JSON diske YAZILMAZ
        with open(HEDEF, "w", encoding="utf-8") as f:
            json.dump(veri, f, ensure_ascii=False, indent=1)
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(f"yazildi {os.path.getsize(HEDEF)} bayt".encode())

    def log_message(self, *a): pass

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", 8791), Islem) as s:
    s.serve_forever()
