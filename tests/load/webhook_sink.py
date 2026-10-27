import random
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

FLAKY_RATE = 0.1


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        flaky = self.path == "/flaky" and random.random() < FLAKY_RATE
        self.send_response(500 if flaky else 200)
        self.end_headers()

    def log_message(self, *args: object) -> None:
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
