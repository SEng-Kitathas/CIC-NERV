from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Thread
from typing import Callable

from personal_cic.core.world import WorldState
from .projection import build_systems_projection


SYSTEMS_HTML = '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>Personal CIC // Systems</title>\n<style>\n:root {\n  color-scheme: dark;\n  --bg: #080c10;\n  --panel: #0f151b;\n  --panel2: #121b22;\n  --line: #25323d;\n  --text: #e7edf2;\n  --muted: #8da0af;\n  --good: #74d99f;\n  --warn: #e8c56d;\n  --bad: #ef7e7e;\n  --unknown: #9aa7b2;\n  --accent: #79b8ff;\n}\n* { box-sizing: border-box; }\nbody {\n  margin: 0;\n  background: var(--bg);\n  color: var(--text);\n  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;\n}\nheader {\n  position: sticky;\n  top: 0;\n  z-index: 10;\n  background: rgba(8,12,16,.96);\n  border-bottom: 1px solid var(--line);\n  backdrop-filter: blur(10px);\n}\n.brand {\n  display: flex;\n  align-items: baseline;\n  gap: 14px;\n  padding: 16px 20px 10px;\n}\n.brand h1 { margin: 0; font-size: 18px; letter-spacing: .12em; }\n.readonly {\n  color: var(--accent);\n  border: 1px solid #2d5f8a;\n  border-radius: 999px;\n  padding: 2px 8px;\n  font-size: 10px;\n  letter-spacing: .08em;\n}\nnav {\n  display: flex;\n  gap: 8px;\n  padding: 0 20px 12px;\n  overflow-x: auto;\n}\nnav span {\n  color: var(--muted);\n  border: 1px solid var(--line);\n  padding: 6px 9px;\n  border-radius: 4px;\n  white-space: nowrap;\n  font-size: 11px;\n}\nnav .active { color: var(--text); border-color: #466174; background: #111b23; }\nnav .future { opacity: .45; }\n.status-strip {\n  display: grid;\n  grid-template-columns: repeat(4, minmax(0, 1fr));\n  gap: 8px;\n  padding: 12px 20px 0;\n}\n.status {\n  background: var(--panel);\n  border: 1px solid var(--line);\n  border-radius: 6px;\n  padding: 10px 12px;\n}\n.label { color: var(--muted); font-size: 10px; letter-spacing: .1em; }\n.value { font-size: 14px; margin-top: 4px; }\n.nominal, .current, .connected { color: var(--good); }\n.warning, .degraded { color: var(--warn); }\n.critical, .unavailable, .disconnected { color: var(--bad); }\n.unknown { color: var(--unknown); }\nmain { padding: 14px 20px 28px; }\n.grid {\n  display: grid;\n  grid-template-columns: repeat(2, minmax(0, 1fr));\n  gap: 12px;\n}\n.card {\n  border: 1px solid var(--line);\n  background: var(--panel);\n  border-radius: 8px;\n  overflow: hidden;\n}\n.card h2 {\n  margin: 0;\n  padding: 12px 14px;\n  font-size: 12px;\n  letter-spacing: .08em;\n  border-bottom: 1px solid var(--line);\n  background: var(--panel2);\n}\n.metrics {\n  display: grid;\n  grid-template-columns: repeat(2, minmax(0, 1fr));\n}\n.metric {\n  min-height: 72px;\n  padding: 12px 14px;\n  border-right: 1px solid var(--line);\n  border-bottom: 1px solid var(--line);\n}\n.metric:nth-child(even) { border-right: 0; }\n.metric .v {\n  display: block;\n  margin-top: 5px;\n  font-size: 17px;\n  overflow-wrap: anywhere;\n}\n.metric .sub {\n  color: var(--muted);\n  display: block;\n  margin-top: 4px;\n  font-size: 10px;\n  line-height: 1.45;\n}\n.foot {\n  color: var(--muted);\n  padding: 12px 20px 24px;\n  font-size: 10px;\n}\n.reason {\n  padding: 10px 14px;\n  border-top: 1px solid var(--line);\n  color: var(--warn);\n  font-size: 11px;\n}\n@media (max-width: 760px) {\n  .status-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }\n  .grid { grid-template-columns: 1fr; }\n}\n</style>\n</head>\n<body>\n<header>\n  <div class="brand">\n    <h1>PERSONAL CIC // SYSTEMS</h1>\n    <span class="readonly">READ-ONLY</span>\n  </div>\n  <nav>\n    <span class="active">SYSTEMS</span>\n    <span class="future">WORLD</span>\n    <span class="future">HOUSE</span>\n    <span class="future">SENSORS</span>\n    <span class="future">SYSTEM / AI</span>\n  </nav>\n</header>\n\n<section class="status-strip">\n  <div class="status"><div class="label">CIC HEALTH</div><div id="s-health" class="value unknown">--</div></div>\n  <div class="status"><div class="label">OBSERVATION</div><div id="s-obs" class="value unknown">--</div></div>\n  <div class="status"><div class="label">WLAN</div><div id="s-wlan" class="value unknown">--</div></div>\n  <div class="status"><div class="label">API</div><div id="s-api" class="value unknown">CONNECTING</div></div>\n</section>\n\n<main>\n  <div class="grid">\n    <section class="card">\n      <h2>ENGAGE ONE // HOST</h2>\n      <div class="metrics">\n        <div class="metric"><span class="label">CPU</span><span id="cpu" class="v">--</span><span id="load" class="sub">--</span></div>\n        <div class="metric"><span class="label">MEMORY</span><span id="mem" class="v">--</span><span id="memsub" class="sub">--</span></div>\n        <div class="metric"><span class="label">STORAGE</span><span id="disk" class="v">--</span><span id="disksub" class="sub">--</span></div>\n        <div class="metric"><span class="label">TEMPERATURE</span><span id="temp" class="v">--</span><span id="tempsub" class="sub">--</span></div>\n        <div class="metric"><span class="label">UPTIME</span><span id="uptime" class="v">--</span><span class="sub">host uptime</span></div>\n        <div class="metric"><span class="label">OBSERVATION</span><span id="hostobs" class="v">--</span><span id="hostfresh" class="sub">--</span></div>\n      </div>\n      <div id="hostreason" class="reason" hidden></div>\n    </section>\n\n    <section class="card">\n      <h2>TENDA U11 PRO // WLAN PROVIDER</h2>\n      <div class="metrics">\n        <div class="metric"><span class="label">LINK</span><span id="link" class="v">--</span><span id="ssid" class="sub">--</span></div>\n        <div class="metric"><span class="label">SIGNAL</span><span id="signal" class="v">--</span><span id="band" class="sub">--</span></div>\n        <div class="metric"><span class="label">RX</span><span id="rx" class="v">--</span><span class="sub">Mbps</span></div>\n        <div class="metric"><span class="label">TX</span><span id="tx" class="v">--</span><span class="sub">Mbps</span></div>\n        <div class="metric"><span class="label">USB</span><span id="usb" class="v">--</span><span id="usbsub" class="sub">--</span></div>\n        <div class="metric"><span class="label">IPv4</span><span id="ipv4" class="v">--</span><span id="tendafresh" class="sub">--</span></div>\n      </div>\n      <div id="tendareason" class="reason" hidden></div>\n    </section>\n  </div>\n</main>\n\n<div class="foot">\n  Projection only. Browser performs no hardware, kernel, NetworkManager, or actuator queries.\n  <span id="generated"></span>\n</div>\n\n<script>\nconst $ = (id) => document.getElementById(id);\nconst cls = (el, value) => {\n  el.className = "value " + String(value || "unknown").toLowerCase();\n};\nconst pct = (v) => Number.isFinite(v) ? v.toFixed(1) + "%" : "--";\nconst num = (v, digits=1) => Number.isFinite(v) ? v.toFixed(digits) : "--";\nconst gib = (v) => Number.isFinite(v) ? (v / 1073741824).toFixed(1) + " GiB" : "--";\nconst uptime = (s) => {\n  if (!Number.isFinite(s)) return "--";\n  const d = Math.floor(s / 86400);\n  const h = Math.floor((s % 86400) / 3600);\n  const m = Math.floor((s % 3600) / 60);\n  return d ? `${d}d ${h}h ${m}m` : `${h}h ${m}m`;\n};\nconst reasons = (el, health, obs) => {\n  const values = [...(health?.reasons || []), ...(obs?.reasons || [])];\n  el.hidden = values.length === 0;\n  el.textContent = values.join(" // ");\n};\nasync function refresh() {\n  try {\n    const response = await fetch("/api/v1/systems", {cache: "no-store"});\n    if (!response.ok) throw new Error("HTTP " + response.status);\n    const d = await response.json();\n\n    $("s-api").textContent = "LIVE";\n    cls($("s-api"), "current");\n\n    $("s-health").textContent = String(d.summary.health).toUpperCase();\n    cls($("s-health"), d.summary.health);\n\n    $("s-obs").textContent = String(d.summary.observation).toUpperCase();\n    cls($("s-obs"), d.summary.observation);\n\n    $("s-wlan").textContent = d.summary.wlan_connected ? "CONNECTED" : "DISCONNECTED";\n    cls($("s-wlan"), d.summary.wlan_connected ? "connected" : "disconnected");\n\n    const h = d.host;\n    $("cpu").textContent = pct(h.compute.cpu_percent);\n    $("load").textContent = `load ${num(h.compute.load_1m, 2)} // ${h.compute.logical_cpus ?? "--"} logical CPUs`;\n    $("mem").textContent = pct(h.memory.used_percent);\n    $("memsub").textContent = `${gib(h.memory.available_bytes)} available`;\n    $("disk").textContent = pct(h.storage.used_percent);\n    $("disksub").textContent = `${gib(h.storage.free_bytes)} free`;\n    $("temp").textContent = Number.isFinite(h.temperature.celsius) ? num(h.temperature.celsius) + " °C" : "--";\n    $("tempsub").textContent = h.temperature.source || "--";\n    $("uptime").textContent = uptime(h.uptime.uptime_seconds);\n    $("hostobs").textContent = String(h.observation.availability).toUpperCase();\n    $("hostfresh").textContent = `${num(h.observation.freshness_seconds, 1)} s since observation`;\n    reasons($("hostreason"), h.health, h.observation);\n\n    const t = d.tenda;\n    $("link").textContent = t.wifi.connected ? "CONNECTED" : "DISCONNECTED";\n    $("link").className = "v " + (t.wifi.connected ? "connected" : "disconnected");\n    $("ssid").textContent = t.wifi.ssid || "--";\n    $("signal").textContent = Number.isFinite(t.wifi.signal_dbm) ? `${t.wifi.signal_dbm} dBm` : "--";\n    $("band").textContent = [t.wifi.band, Number.isFinite(t.wifi.frequency_mhz) ? `${t.wifi.frequency_mhz} MHz` : null].filter(Boolean).join(" // ") || "--";\n    $("rx").textContent = num(t.wifi.rx_mbps);\n    $("tx").textContent = num(t.wifi.tx_mbps);\n    $("usb").textContent = t.usb.present ? "PRESENT" : "ABSENT";\n    $("usbsub").textContent = [t.usb.usb_id, t.usb.mode].filter(Boolean).join(" // ") || "--";\n    $("ipv4").textContent = t.wifi.ipv4 || "--";\n    $("tendafresh").textContent = `${num(t.observation.freshness_seconds, 1)} s since observation`;\n    reasons($("tendareason"), t.health, t.observation);\n\n    $("generated").textContent = " // served " + d.presentation.generated_at;\n  } catch (error) {\n    $("s-api").textContent = "UNAVAILABLE";\n    cls($("s-api"), "unavailable");\n    $("generated").textContent = " // " + error;\n  }\n}\nrefresh();\nsetInterval(refresh, 2000);\n</script>\n</body>\n</html>\n'


class _CICHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def _handler_factory(
    world: WorldState,
    runtime_metadata: Callable[[], dict],
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
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "connect-src 'self'; "
                "img-src 'self' data:; "
                "frame-ancestors 'none';"
            )
            if length:
                self.send_header("Content-Length", str(length))
            self.end_headers()

        def do_GET(self):
            if self.path in ("/", "/systems"):
                payload = SYSTEMS_HTML.encode("utf-8")
                self._headers(
                    200,
                    "text/html; charset=utf-8",
                    len(payload),
                )
                self.wfile.write(payload)
                return

            if self.path == "/api/v1/systems":
                metadata = runtime_metadata()
                projection = build_systems_projection(
                    world,
                    runtime_pid=metadata.get("pid"),
                    runtime_started_at=metadata.get("started_at"),
                )
                payload = json.dumps(
                    projection,
                    separators=(",", ":"),
                ).encode("utf-8")
                self._headers(
                    200,
                    "application/json; charset=utf-8",
                    len(payload),
                )
                self.wfile.write(payload)
                return

            if self.path == "/favicon.ico":
                self._headers(204, "image/x-icon")
                return

            payload = b'{"error":"not_found"}'
            self._headers(
                404,
                "application/json; charset=utf-8",
                len(payload),
            )
            self.wfile.write(payload)

        def do_HEAD(self):
            if self.path in ("/", "/systems"):
                self._headers(200, "text/html; charset=utf-8")
            elif self.path == "/api/v1/systems":
                self._headers(200, "application/json; charset=utf-8")
            else:
                self._headers(404, "application/json; charset=utf-8")

        def _reject_mutation(self):
            payload = b'{"error":"read_only"}'
            self.send_response(405)
            self.send_header("Allow", "GET, HEAD")
            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8",
            )
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        do_POST = _reject_mutation
        do_PUT = _reject_mutation
        do_PATCH = _reject_mutation
        do_DELETE = _reject_mutation

        def log_message(self, _format, *_args):
            # Polling the read-only local display should not flood service logs.
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
    ) -> None:
        if host != "127.0.0.1":
            raise ValueError(
                "Slice 003 presentation is intentionally loopback-only"
            )

        self.world = world
        self.host = host
        self.port = port
        self.runtime_metadata = runtime_metadata
        self._httpd: _CICHTTPServer | None = None
        self._thread: Thread | None = None

    @property
    def bound_port(self) -> int | None:
        if self._httpd is None:
            return None
        return int(self._httpd.server_address[1])

    def start(self) -> None:
        if self._httpd is not None:
            return

        handler = _handler_factory(
            self.world,
            self.runtime_metadata,
        )
        self._httpd = _CICHTTPServer(
            (self.host, self.port),
            handler,
        )
        self._thread = Thread(
            target=self._httpd.serve_forever,
            name="personal-cic-presentation",
            daemon=True,
        )
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
