from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Thread
from typing import Callable

from personal_cic.core.world import WorldState
from .pages import SYSTEMS_HTML, WORLD_HTML
from .projection import build_systems_projection, build_world_projection


class _CICHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def _handler_factory(world: WorldState, runtime_metadata: Callable[[], dict]):
    class Handler(BaseHTTPRequestHandler):
        server_version = "PersonalCIC/0.3"

        def _headers(self, status: int, content_type: str, length: int = 0):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; connect-src 'self'; "
                "img-src 'self' data:; frame-ancestors 'none';",
            )
            if length:
                self.send_header("Content-Length", str(length))
            self.end_headers()

        def _send_json(self, payload: dict, status: int = 200):
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            self._headers(status, "application/json; charset=utf-8", len(body))
            self.wfile.write(body)

        def do_GET(self):
            if self.path in ("/", "/systems"):
                payload = SYSTEMS_HTML.encode("utf-8")
                self._headers(200, "text/html; charset=utf-8", len(payload))
                self.wfile.write(payload)
                return
            if self.path == "/world":
                payload = WORLD_HTML.encode("utf-8")
                self._headers(200, "text/html; charset=utf-8", len(payload))
                self.wfile.write(payload)
                return
            if self.path == "/api/v1/systems":
                metadata = runtime_metadata()
                self._send_json(
                    build_systems_projection(
                        world,
                        runtime_pid=metadata.get("pid"),
                        runtime_started_at=metadata.get("started_at"),
                    )
                )
                return
            if self.path == "/api/v1/world":
                self._send_json(build_world_projection(world))
                return
            if self.path == "/favicon.ico":
                self._headers(204, "image/x-icon")
                return
            self._send_json({"error": "not_found"}, 404)

        def do_HEAD(self):
            if self.path in ("/", "/systems", "/world"):
                self._headers(200, "text/html; charset=utf-8")
            elif self.path in ("/api/v1/systems", "/api/v1/world"):
                self._headers(200, "application/json; charset=utf-8")
            else:
                self._headers(404, "application/json; charset=utf-8")

        def _reject_mutation(self):
            payload = b'{"error":"read_only"}'
            self.send_response(405)
            self.send_header("Allow", "GET, HEAD")
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        do_POST = _reject_mutation
        do_PUT = _reject_mutation
        do_PATCH = _reject_mutation
        do_DELETE = _reject_mutation

        def log_message(self, _format, *_args):
            return

    return Handler


class PresentationServer:
    """Loopback-only, read-only projection server for CIC WorldState."""

    def __init__(self, *, world: WorldState, host: str, port: int, runtime_metadata: Callable[[], dict]) -> None:
        if host != "127.0.0.1":
            raise ValueError("Presentation is intentionally loopback-only")
        self.world = world
        self.host = host
        self.port = port
        self.runtime_metadata = runtime_metadata
        self._httpd: _CICHTTPServer | None = None
        self._thread: Thread | None = None

    @property
    def bound_port(self) -> int | None:
        return None if self._httpd is None else int(self._httpd.server_address[1])

    def start(self) -> None:
        if self._httpd is not None:
            return
        self._httpd = _CICHTTPServer((self.host, self.port), _handler_factory(self.world, self.runtime_metadata))
        self._thread = Thread(target=self._httpd.serve_forever, name="personal-cic-presentation", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._httpd is None:
            return
        self._httpd.shutdown()
        self._httpd.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self._httpd = None
        self._thread = None
