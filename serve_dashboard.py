#!/usr/bin/env python3
"""Serve the generated dashboard.html as a small local web server."""

from argparse import ArgumentParser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self):
        if self.path in {"/", "/index.html"}:
            self.path = "/dashboard.html"
        return super().do_GET()

    def end_headers(self):
        # Avoid stale dashboard content in browsers.
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


def main():
    parser = ArgumentParser(description="Serve dashboard.html over HTTP")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=8000, help="Bind port")
    args = parser.parse_args()

    handler = partial(DashboardHandler, directory=str(ROOT))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving {ROOT / 'dashboard.html'} on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
