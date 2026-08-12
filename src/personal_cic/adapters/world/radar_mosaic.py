from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from math import cos, radians
from pathlib import Path
import re
from typing import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from personal_cic.core.observations import Observation
from personal_cic.core.world.components import RadarMosaicState


_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_PRODUCT_RE = re.compile(
    r"CONUS_L2_BREF_QCD_(?P<date>\d{8})_(?P<time>\d{6})\.tif\.gz"
)


@dataclass(frozen=True, slots=True)
class RadarImagePaths:
    radar: Path
    warnings: Path
    legend: Path


class MRMSRadarMosaicAdapter:
    """Normalize the latest NOAA/NWS CONUS MRMS base-reflectivity mosaic.

    Domain truth is metadata in WorldState. Rendered PNGs are adapter-owned cache
    artifacts served read-only by the local presentation boundary; image bytes do
    not become giant WorldState/snapshot components.

    The RIDGEII filename/timestamp is a source-stream freshness witness. The WMS
    image request is an independently retrieved latest render and is not claimed
    to be byte-for-byte or temporally bound to that specific GeoTIFF product.
    """

    ADAPTER_ID = "nws.mrms.radar"
    PROVIDER = "NOAA/NWS MRMS + NWS GeoServer"
    PRODUCT = "BREF.QCD"
    LAYER = "conus_bref_qcd"
    WARNING_LAYER = "warnings"

    def __init__(
        self,
        *,
        location_label: str,
        latitude: float,
        longitude: float,
        range_miles: float,
        image_width: int,
        image_height: int,
        max_age_minutes: float,
        cache_dir: Path,
        user_agent: str,
        timeout_seconds: float = 8.0,
        metadata_url: str = "https://mrms.ncep.noaa.gov/RIDGEII/L2/CONUS/BREF_QCD/",
        radar_wms_url: str = "https://opengeo.ncep.noaa.gov/geoserver/conus/conus_bref_qcd/ows",
        warnings_wms_url: str = "https://opengeo.ncep.noaa.gov/geoserver/wwa/warnings/ows",
        opener: Callable = urlopen,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.location_label = location_label
        self.latitude = latitude
        self.longitude = longitude
        self.range_miles = range_miles
        self.image_width = image_width
        self.image_height = image_height
        self.max_age_minutes = max_age_minutes
        self.cache_dir = Path(cache_dir)
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.metadata_url = metadata_url
        self.radar_wms_url = radar_wms_url
        self.warnings_wms_url = warnings_wms_url
        self.opener = opener
        self.now = now or (lambda: datetime.now(timezone.utc))

    @property
    def image_paths(self) -> RadarImagePaths:
        return RadarImagePaths(
            radar=self.cache_dir / "latest.png",
            warnings=self.cache_dir / "warnings.png",
            legend=self.cache_dir / "legend.png",
        )

    def _request(self, url: str, accept: str) -> bytes:
        request = Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": accept,
            },
        )
        with self.opener(request, timeout=self.timeout_seconds) as response:
            return response.read()

    @staticmethod
    def _parse_latest_product(listing: str) -> tuple[str, datetime] | None:
        matches: list[tuple[datetime, str]] = []
        for match in _PRODUCT_RE.finditer(listing):
            stamp = match.group("date") + match.group("time")
            try:
                observed = datetime.strptime(stamp, "%Y%m%d%H%M%S").replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                continue
            matches.append((observed, match.group(0)))
        if not matches:
            return None
        observed, filename = max(matches)
        return filename, observed

    def _bbox(self) -> tuple[float, float, float, float]:
        # `range_miles` is the radius of the largest centered range ring and
        # therefore the vertical half-extent of the image. Expand the horizontal
        # geographic extent by the pixel aspect ratio so the WMS render has
        # approximately equal miles-per-pixel in both axes instead of stretching
        # a square physical area into a 3:2 image.
        aspect = self.image_width / self.image_height
        vertical_half_miles = self.range_miles
        horizontal_half_miles = self.range_miles * aspect
        lat_delta = vertical_half_miles / 69.0
        lon_scale = max(0.2, cos(radians(self.latitude)))
        lon_delta = horizontal_half_miles / (69.0 * lon_scale)
        return (
            self.longitude - lon_delta,
            self.latitude - lat_delta,
            self.longitude + lon_delta,
            self.latitude + lat_delta,
        )

    def _wms_url(
        self,
        base_url: str,
        *,
        layer: str,
        transparent: bool,
    ) -> str:
        west, south, east, north = self._bbox()
        params = {
            "SERVICE": "WMS",
            "VERSION": "1.1.1",
            "REQUEST": "GetMap",
            "LAYERS": layer,
            "STYLES": "",
            "SRS": "EPSG:4326",
            "BBOX": f"{west:.6f},{south:.6f},{east:.6f},{north:.6f}",
            "WIDTH": str(self.image_width),
            "HEIGHT": str(self.image_height),
            "FORMAT": "image/png",
            "TRANSPARENT": "TRUE" if transparent else "FALSE",
            "BGCOLOR": "0x05080c",
        }
        return base_url + "?" + urlencode(params)

    def _legend_url(self) -> str:
        return self.radar_wms_url + "?" + urlencode(
            {
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetLegendGraphic",
                "FORMAT": "image/png",
                "WIDTH": "500",
                "HEIGHT": "30",
                "LAYER": self.LAYER,
            }
        )

    @staticmethod
    def _validate_png(payload: bytes, label: str) -> None:
        if not payload.startswith(_PNG_SIGNATURE):
            raise ValueError(f"{label} response is not PNG image data")

    @staticmethod
    def _atomic_write(path: Path, payload: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_bytes(payload)
        tmp.replace(path)

    def collect(self) -> tuple[Observation[object], ...]:
        try:
            listing_bytes = self._request(self.metadata_url, "text/html")
            latest = self._parse_latest_product(
                listing_bytes.decode("utf-8", errors="replace")
            )
            if latest is None:
                raise ValueError("MRMS listing contained no BREF.QCD products")

            filename, source_time = latest
            now = self.now()
            if now.tzinfo is None:
                now = now.replace(tzinfo=timezone.utc)
            now = now.astimezone(timezone.utc)
            age_seconds = (now - source_time).total_seconds()
            if age_seconds < -300:
                raise ValueError("MRMS source product timestamp is implausibly in the future")
            if age_seconds > self.max_age_minutes * 60:
                raise ValueError(
                    f"MRMS latest source product is stale ({age_seconds / 60:.1f} min)"
                )

            radar_payload = self._request(
                self._wms_url(
                    self.radar_wms_url,
                    layer=self.LAYER,
                    transparent=False,
                ),
                "image/png",
            )
            self._validate_png(radar_payload, "radar")
            frame_retrieved_at = self.now()
            if frame_retrieved_at.tzinfo is None:
                frame_retrieved_at = frame_retrieved_at.replace(tzinfo=timezone.utc)
            frame_retrieved_at = frame_retrieved_at.astimezone(timezone.utc)

            warning_payload: bytes | None = None
            warning_error: str | None = None
            try:
                warning_payload = self._request(
                    self._wms_url(
                        self.warnings_wms_url,
                        layer=self.WARNING_LAYER,
                        transparent=True,
                    ),
                    "image/png",
                )
                self._validate_png(warning_payload, "warning overlay")
            except Exception as exc:  # preserve useful radar without fabricating overlay state
                warning_error = str(exc)

            paths = self.image_paths
            legend_payload: bytes | None = None
            if paths.legend.exists():
                try:
                    cached_legend = paths.legend.read_bytes()
                    self._validate_png(cached_legend, "cached radar legend")
                    legend_payload = cached_legend
                except Exception:
                    paths.legend.unlink(missing_ok=True)
            if legend_payload is None:
                try:
                    legend_payload = self._request(self._legend_url(), "image/png")
                    self._validate_png(legend_payload, "radar legend")
                except Exception:
                    legend_payload = None

            self._atomic_write(paths.radar, radar_payload)
            if warning_payload is not None:
                self._atomic_write(paths.warnings, warning_payload)
            else:
                paths.warnings.unlink(missing_ok=True)
            if legend_payload is not None:
                self._atomic_write(paths.legend, legend_payload)
            else:
                paths.legend.unlink(missing_ok=True)

            west, south, east, north = self._bbox()
            state = RadarMosaicState(
                location_label=self.location_label,
                provider=self.PROVIDER,
                product=self.PRODUCT,
                layer=self.LAYER,
                stream_latest_filename=filename,
                stream_latest_at=source_time.isoformat(),
                frame_retrieved_at=frame_retrieved_at.isoformat(),
                west=west,
                south=south,
                east=east,
                north=north,
                range_miles=self.range_miles,
                image_width=self.image_width,
                image_height=self.image_height,
                image_sha256=sha256(radar_payload).hexdigest(),
                warning_overlay_available=warning_payload is not None,
                warning_image_sha256=(
                    None if warning_payload is None else sha256(warning_payload).hexdigest()
                ),
                legend_available=legend_payload is not None,
                legend_image_sha256=(
                    None if legend_payload is None else sha256(legend_payload).hexdigest()
                ),
            )
            if warning_error:
                return (
                    Observation.partial(
                        "nws.mrms.radar",
                        state,
                        f"warning overlay unavailable: {warning_error}",
                    ),
                )
            return (Observation.observed("nws.mrms.radar", state),)
        except Exception as exc:
            return (
                Observation.unavailable(
                    "nws.mrms.radar",
                    f"radar fetch failed: {exc}",
                ),
            )
