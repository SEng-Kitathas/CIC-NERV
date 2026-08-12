from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from hashlib import sha256
from pathlib import Path
import json
import re
from threading import Thread
from typing import Callable
from urllib.parse import parse_qs, urlsplit

from personal_cic.core.world import WorldState
from .pages import SYSTEMS_HTML, WORLD_HTML
from .traffic_page import TRAFFIC_HTML
from .projection import build_systems_projection, build_traffic_projection, build_world_projection
from .weather_feed import build_weather_feed


class _CICHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def _handler_factory(
    world: WorldState,
    runtime_metadata: Callable[[], dict],
    event_journal_path: Path | None,
    radar_cache_dir: Path | None,
):
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
                "frame-src https://embed.waze.com; "
                "img-src 'self' data:; frame-ancestors 'none';",
            )
            if length:
                self.send_header("Content-Length", str(length))
            self.end_headers()

        def _send_json(self, payload: dict, status: int = 200):
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            self._headers(status, "application/json; charset=utf-8", len(body))
            self.wfile.write(body)

        def _valid_sha(self, value: str | None) -> bool:
            return bool(value and re.fullmatch(r"[0-9a-f]{64}", value))

        def _cached_png(self, relative: Path, expected_sha: str | None):
            if radar_cache_dir is None:
                return None, "not_found", 404
            if not self._valid_sha(expected_sha):
                return None, "invalid_frame_identity", 400
            path = radar_cache_dir / relative
            if not path.exists() or not path.is_file():
                return None, "not_found", 404
            payload = path.read_bytes()
            if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
                return None, "invalid_cached_image", 500
            if sha256(payload).hexdigest() != expected_sha:
                return None, "frame_identity_mismatch", 409
            return payload, None, 200

        def _send_cached_png(self, relative: Path, expected_sha: str | None):
            payload, error, status = self._cached_png(relative, expected_sha)
            if payload is None:
                self._send_json({"error": error}, status)
                return
            self._headers(200, "image/png", len(payload))
            self.wfile.write(payload)

        def _send_hash_named_png(self, directory: str, filename: str):
            match = re.fullmatch(r"([0-9a-f]{64})\.png", filename)
            if match is None:
                self._send_json({"error": "invalid_frame_identity"}, 400)
                return
            expected_sha = match.group(1)
            self._send_cached_png(Path(directory) / filename, expected_sha)

        def _cached_context(self, expected_sha: str | None):
            if radar_cache_dir is None:
                return None, "not_found", 404
            if not self._valid_sha(expected_sha):
                return None, "invalid_context_identity", 400
            path = radar_cache_dir / "context.json"
            if not path.exists() or not path.is_file():
                return None, "not_found", 404
            payload = path.read_bytes()
            if sha256(payload).hexdigest() != expected_sha:
                return None, "context_identity_mismatch", 409
            try:
                value = json.loads(payload.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return None, "invalid_cached_context", 500
            if not isinstance(value, dict):
                return None, "invalid_cached_context", 500
            return payload, None, 200

        def _send_cached_context(self, expected_sha: str | None):
            payload, error, status = self._cached_context(expected_sha)
            if payload is None:
                self._send_json({"error": error}, status)
                return
            self._headers(200, "application/json; charset=utf-8", len(payload))
            self.wfile.write(payload)

        def do_GET(self):
            parsed = urlsplit(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)
            if path in ("/", "/systems"):
                payload = SYSTEMS_HTML.encode("utf-8")
                self._headers(200, "text/html; charset=utf-8", len(payload))
                self.wfile.write(payload)
                return
            if path == "/world":
                payload = WORLD_HTML.encode("utf-8")
                self._headers(200, "text/html; charset=utf-8", len(payload))
                self.wfile.write(payload)
                return
            if path == "/traffic":
                payload = TRAFFIC_HTML.encode("utf-8")
                self._headers(200, "text/html; charset=utf-8", len(payload))
                self.wfile.write(payload)
                return
            if path == "/api/v1/systems":
                metadata = runtime_metadata()
                self._send_json(
                    build_systems_projection(
                        world,
                        runtime_pid=metadata.get("pid"),
                        runtime_started_at=metadata.get("started_at"),
                    )
                )
                return
            if path == "/api/v1/world":
                self._send_json(build_world_projection(world, feed=build_weather_feed(event_journal_path)))
                return
            if path == "/api/v1/traffic":
                self._send_json(build_traffic_projection(world))
                return
            if path == "/radar/latest.png":
                self._send_cached_png(Path("latest.png"), (query.get("sha") or [None])[0])
                return
            if path == "/radar/warnings.png":
                self._send_cached_png(Path("warnings.png"), (query.get("sha") or [None])[0])
                return
            if path == "/radar/legend.png":
                self._send_cached_png(Path("legend.png"), (query.get("sha") or [None])[0])
                return
            if path.startswith("/radar/frames/"):
                self._send_hash_named_png("frames", path.rsplit("/", 1)[-1])
                return
            if path.startswith("/radar/warning-frames/"):
                self._send_hash_named_png("warning_frames", path.rsplit("/", 1)[-1])
                return
            if path == "/radar/context.json":
                self._send_cached_context((query.get("sha") or [None])[0])
                return
            if path == "/favicon.ico":
                self._headers(204, "image/x-icon")
                return
            self._send_json({"error": "not_found"}, 404)

        def do_HEAD(self):
            parsed = urlsplit(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)
            if path in ("/", "/systems", "/world", "/traffic"):
                self._headers(200, "text/html; charset=utf-8")
            elif path in ("/api/v1/systems", "/api/v1/world", "/api/v1/traffic"):
                self._headers(200, "application/json; charset=utf-8")
            elif path in ("/radar/latest.png", "/radar/warnings.png", "/radar/legend.png"):
                filename = {
                    "/radar/latest.png": "latest.png",
                    "/radar/warnings.png": "warnings.png",
                    "/radar/legend.png": "legend.png",
                }[path]
                expected_sha = (query.get("sha") or [None])[0]
                payload, _error, status = self._cached_png(Path(filename), expected_sha)
                if payload is not None:
                    self._headers(200, "image/png", len(payload))
                else:
                    self._headers(status, "application/json; charset=utf-8")
            elif path.startswith("/radar/frames/") or path.startswith("/radar/warning-frames/"):
                filename = path.rsplit("/", 1)[-1]
                match = re.fullmatch(r"([0-9a-f]{64})\.png", filename)
                if match is None:
                    self._headers(400, "application/json; charset=utf-8")
                else:
                    directory = "frames" if path.startswith("/radar/frames/") else "warning_frames"
                    payload, _error, status = self._cached_png(Path(directory) / filename, match.group(1))
                    if payload is not None:
                        self._headers(200, "image/png", len(payload))
                    else:
                        self._headers(status, "application/json; charset=utf-8")
            elif path == "/radar/context.json":
                payload, _error, status = self._cached_context((query.get("sha") or [None])[0])
                if payload is not None:
                    self._headers(200, "application/json; charset=utf-8", len(payload))
                else:
                    self._headers(status, "application/json; charset=utf-8")
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

    def __init__(
        self,
        *,
        world: WorldState,
        host: str,
        port: int,
        runtime_metadata: Callable[[], dict],
        event_journal_path: Path | None = None,
        radar_cache_dir: Path | None = None,
    ) -> None:
        if host != "127.0.0.1":
            raise ValueError("Presentation is intentionally loopback-only")
        self.world = world
        self.host = host
        self.port = port
        self.runtime_metadata = runtime_metadata
        self.event_journal_path = event_journal_path
        self.radar_cache_dir = radar_cache_dir
        self._httpd: _CICHTTPServer | None = None
        self._thread: Thread | None = None

    @property
    def bound_port(self) -> int | None:
        return None if self._httpd is None else int(self._httpd.server_address[1])

    def start(self) -> None:
        if self._httpd is not None:
            return
        self._httpd = _CICHTTPServer(
            (self.host, self.port),
            _handler_factory(
                self.world,
                self.runtime_metadata,
                self.event_journal_path,
                self.radar_cache_dir,
            ),
        )
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
