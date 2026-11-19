"""Offline map server. Serves this folder on http://127.0.0.1:8765 with HTTP Range
support (PMTiles needs it) and lists every *.pmtiles file here at /maps.json.
Python standard library only, so it runs on any Mac with python3."""
import json
import os
import re
import sys
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = 8765


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, *a):
        pass

    def translate_path(self, path):
        # The map uses the app's shared files at /hub/. In the app they sit next to it.
        # Standalone, look for them in a "hub" folder beside this one, then in the repo layout.
        clean = path.split("?")[0].split("#")[0]
        if clean.startswith("/hub/"):
            name = os.path.basename(clean)
            for base in (os.path.join(ROOT, "hub"), os.path.join(ROOT, "..")):
                cand = os.path.join(base, name)
                if os.path.isfile(cand):
                    return cand
        return super().translate_path(path)

    def do_GET(self):
        if self.path.split("?")[0] == "/maps.json":
            maps = sorted(f for f in os.listdir(ROOT) if f.endswith(".pmtiles"))
            body = json.dumps(maps).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        rng = self.headers.get("Range")
        path = self.translate_path(self.path)
        if not rng or not os.path.isfile(path):
            return super().do_GET()
        m = re.match(r"bytes=(\d*)-(\d*)", rng)
        size = os.path.getsize(path)
        if not m:
            self.send_error(416)
            return
        start = int(m.group(1)) if m.group(1) else size - int(m.group(2))
        end = int(m.group(2)) if m.group(1) and m.group(2) else size - 1
        end = min(end, size - 1)
        if start > end or start >= size:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.end_headers()
            return
        length = end - start + 1
        self.send_response(206)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        with open(path, "rb") as f:
            f.seek(start)
            self.wfile.write(f.read(length))


if __name__ == "__main__":
    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}/index.html"
    print(f"Offline maps running at {url}\nClose this window to stop.")
    if "--no-browser" not in sys.argv:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    httpd.serve_forever()
