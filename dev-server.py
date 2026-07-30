#!/usr/bin/env python3
"""Local live-reload preview server for this folder.

Not part of the deliverable — just for editing. Run it, then keep the
browser tab open; it auto-refreshes a second or two after you save any
file in this folder. Stop it with Ctrl+C.
"""
import http.server
import os
import socketserver
import sys

PORT = 5500
WATCH_EXT = {".html", ".css", ".js", ".mp3", ".wav", ".m4a", ".ogg"}
ROOT = os.path.dirname(os.path.abspath(__file__))

RELOAD_SNIPPET = b"""
<script>
(function(){
  let last = null;
  async function poll(){
    try{
      const res = await fetch('/__mtime__', {cache:'no-store'});
      const val = await res.text();
      if(last !== null && val !== last){ location.reload(); return; }
      last = val;
    }catch(e){}
    setTimeout(poll, 1000);
  }
  poll();
})();
</script>
</body>
"""

def folder_fingerprint():
    parts = []
    for name in sorted(os.listdir(ROOT)):
        path = os.path.join(ROOT, name)
        if os.path.isfile(path) and os.path.splitext(name)[1].lower() in WATCH_EXT:
            parts.append(f"{name}:{os.path.getmtime(path)}")
    return "|".join(parts)

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):
        if self.path == "/__mtime__":
            body = folder_fingerprint().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return

        path = self.translate_path(self.path)
        if os.path.isdir(path):
            path = os.path.join(path, "index.html")
        if path.lower().endswith(".html") and os.path.isfile(path):
            with open(path, "rb") as f:
                content = f.read()
            if b"</body>" in content:
                content = content.replace(b"</body>", RELOAD_SNIPPET, 1)
            else:
                content += RELOAD_SNIPPET
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(content)
            return

        super().do_GET()

    def log_message(self, fmt, *args):
        pass

if __name__ == "__main__":
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        url = f"http://127.0.0.1:{PORT}/"
        print(f"Serving {ROOT}")
        print(f"Open {url} and leave it open while you edit index.html")
        print("Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")
            sys.exit(0)
