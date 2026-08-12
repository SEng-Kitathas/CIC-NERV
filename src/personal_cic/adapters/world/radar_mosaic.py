from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from math import cos, radians
from pathlib import Path
import re
from typing import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from personal_cic.core.observations import Observation
from personal_cic.core.world.components import RadarFrameReference, RadarMosaicState


_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_PRODUCT_RE = re.compile(
    r"CONUS_L2_BREF_QCD_(?P<date>\d{8})_(?P<time>\d{6})\.tif\.gz"
)


@dataclass(frozen=True, slots=True)
class RadarImagePaths:
    radar: Path
    warnings: Path
    legend: Path
    frames: Path
    warning_frames: Path
    manifest: Path


def radar_bbox(
    *,
    latitude: float,
    longitude: float,
    range_miles: float,
    image_width: int,
    image_height: int,
) -> tuple[float, float, float, float]:
    """Return an EPSG:4326 bbox whose physical aspect matches the raster."""

    aspect = image_width / image_height
    vertical_half_miles = range_miles
    horizontal_half_miles = range_miles * aspect
    lat_delta = vertical_half_miles / 69.0
    lon_scale = max(0.2, cos(radians(latitude)))
    lon_delta = horizontal_half_miles / (69.0 * lon_scale)
    return (
        longitude - lon_delta,
        latitude - lat_delta,
        longitude + lon_delta,
        latitude + lat_delta,
    )


class MRMSRadarMosaicAdapter:
    """Normalize NOAA/NWS MRMS reflectivity into a bounded local frame sequence.

    WorldState owns typed frame/provenance metadata. Image bytes and the small
    loop manifest are adapter-owned cache artifacts. The RIDGEII product index is
    only a source-stream freshness witness; each WMS frame remains independently
    identified by retrieval time and content hash.
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
        loop_frame_capacity: int = 15,
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
        self.loop_frame_capacity = loop_frame_capacity
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
            frames=self.cache_dir / "frames",
            warning_frames=self.cache_dir / "warning_frames",
            manifest=self.cache_dir / "frames.json",
        )

    def _request(self, url: str, accept: str) -> bytes:
        request = Request(
            url,
            headers={"User-Agent": self.user_agent, "Accept": accept},
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
        return radar_bbox(
            latitude=self.latitude,
            longitude=self.longitude,
            range_miles=self.range_miles,
            image_width=self.image_width,
            image_height=self.image_height,
        )

    def _wms_url(self, base_url: str, *, layer: str, transparent: bool) -> str:
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

    @staticmethod
    def _utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def _file_matches_hash(path: Path, expected_sha: str) -> bool:
        try:
            return path.is_file() and sha256(path.read_bytes()).hexdigest() == expected_sha
        except OSError:
            return False

    @staticmethod
    def _valid_frame_ref(frame: RadarFrameReference) -> bool:
        if re.fullmatch(r"[0-9a-f]{64}", frame.image_sha256) is None:
            return False
        if (
            frame.warning_image_sha256 is not None
            and re.fullmatch(r"[0-9a-f]{64}", frame.warning_image_sha256) is None
        ):
            return False
        try:
            datetime.fromisoformat(frame.retrieved_at)
            datetime.fromisoformat(frame.stream_witness_at)
        except ValueError:
            return False
        return True

    def _load_manifest(self) -> list[RadarFrameReference]:
        path = self.image_paths.manifest
        if not path.exists():
            return []
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        result: list[RadarFrameReference] = []
        for item in payload.get("frames", []):
            if not isinstance(item, dict):
                continue
            try:
                frame = RadarFrameReference(
                    retrieved_at=str(item["retrieved_at"]),
                    image_sha256=str(item["image_sha256"]),
                    warning_image_sha256=(
                        None
                        if item.get("warning_image_sha256") is None
                        else str(item.get("warning_image_sha256"))
                    ),
                    stream_witness_at=str(item["stream_witness_at"]),
                )
            except KeyError:
                continue
            if not self._valid_frame_ref(frame):
                continue
            image_path = self.image_paths.frames / f"{frame.image_sha256}.png"
            if not self._file_matches_hash(image_path, frame.image_sha256):
                continue
            if frame.warning_image_sha256:
                warning_path = (
                    self.image_paths.warning_frames
                    / f"{frame.warning_image_sha256}.png"
                )
                if not self._file_matches_hash(
                    warning_path, frame.warning_image_sha256
                ):
                    frame = RadarFrameReference(
                        retrieved_at=frame.retrieved_at,
                        image_sha256=frame.image_sha256,
                        warning_image_sha256=None,
                        stream_witness_at=frame.stream_witness_at,
                    )
            result.append(frame)
        return result[-self.loop_frame_capacity :]

    def _write_manifest(self, frames: list[RadarFrameReference]) -> None:
        payload = {
            "frames": [
                {
                    "retrieved_at": frame.retrieved_at,
                    "image_sha256": frame.image_sha256,
                    "warning_image_sha256": frame.warning_image_sha256,
                    "stream_witness_at": frame.stream_witness_at,
                }
                for frame in frames
            ]
        }
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        self._atomic_write(self.image_paths.manifest, encoded)

    def _prune_immutable_cache(self, frames: list[RadarFrameReference]) -> None:
        keep_radar = {frame.image_sha256 for frame in frames}
        keep_warning = {
            frame.warning_image_sha256
            for frame in frames
            if frame.warning_image_sha256
        }
        for directory, keep in (
            (self.image_paths.frames, keep_radar),
            (self.image_paths.warning_frames, keep_warning),
        ):
            if not directory.exists():
                continue
            for path in directory.glob("*.png"):
                if path.stem not in keep:
                    path.unlink(missing_ok=True)

    def _record_frame(
        self,
        *,
        radar_payload: bytes,
        warning_payload: bytes | None,
        frame_retrieved_at: datetime,
        stream_witness_at: datetime,
    ) -> tuple[RadarFrameReference, ...]:
        radar_hash = sha256(radar_payload).hexdigest()
        warning_hash = (
            None if warning_payload is None else sha256(warning_payload).hexdigest()
        )
        paths = self.image_paths
        self._atomic_write(paths.frames / f"{radar_hash}.png", radar_payload)
        if warning_payload is not None and warning_hash is not None:
            self._atomic_write(
                paths.warning_frames / f"{warning_hash}.png",
                warning_payload,
            )

        frame = RadarFrameReference(
            retrieved_at=frame_retrieved_at.isoformat(),
            image_sha256=radar_hash,
            warning_image_sha256=warning_hash,
            stream_witness_at=stream_witness_at.isoformat(),
        )
        previous_frames = self._load_manifest()
        frames = list(previous_frames)
        signature = (frame.image_sha256, frame.warning_image_sha256)
        if frames and (
            frames[-1].image_sha256,
            frames[-1].warning_image_sha256,
        ) == signature:
            # Do not fill the operator loop with visually identical adjacent
            # frames. Update only the retrieval/witness timestamp for that slot.
            frames[-1] = frame
        else:
            frames.append(frame)
        frames = frames[-self.loop_frame_capacity :]
        self._write_manifest(frames)
        # HTTP readers can observe the previous WorldState concurrently with
        # collection/ingest. Keep the immediately previous manifest's immutable
        # files for one additional collection generation so a newly pruned
        # oldest frame cannot transiently turn a still-published URL into 404.
        # The next cycle drops that grace generation, bounding files at roughly
        # loop capacity + one distinct frame.
        self._prune_immutable_cache([*previous_frames, *frames])
        return tuple(frames)

    def collect(self) -> tuple[Observation[object], ...]:
        try:
            listing_bytes = self._request(self.metadata_url, "text/html")
            latest = self._parse_latest_product(
                listing_bytes.decode("utf-8", errors="replace")
            )
            if latest is None:
                raise ValueError("MRMS listing contained no BREF.QCD products")

            filename, stream_time = latest
            now = self._utc(self.now())
            age_seconds = (now - stream_time).total_seconds()
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
            frame_retrieved_at = self._utc(self.now())

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
            except Exception as exc:
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

            frames = self._record_frame(
                radar_payload=radar_payload,
                warning_payload=warning_payload,
                frame_retrieved_at=frame_retrieved_at,
                stream_witness_at=stream_time,
            )

            west, south, east, north = self._bbox()
            state = RadarMosaicState(
                location_label=self.location_label,
                provider=self.PROVIDER,
                product=self.PRODUCT,
                layer=self.LAYER,
                stream_latest_filename=filename,
                stream_latest_at=stream_time.isoformat(),
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
                    None
                    if warning_payload is None
                    else sha256(warning_payload).hexdigest()
                ),
                legend_available=legend_payload is not None,
                legend_image_sha256=(
                    None
                    if legend_payload is None
                    else sha256(legend_payload).hexdigest()
                ),
                frames=frames,
                loop_frame_capacity=self.loop_frame_capacity,
            )
            if warning_error:
                return (
                    Observation.partial(
                        self.ADAPTER_ID,
                        state,
                        f"warning overlay unavailable: {warning_error}",
                    ),
                )
            return (Observation.observed(self.ADAPTER_ID, state),)
        except Exception as exc:
            return (
                Observation.unavailable(
                    self.ADAPTER_ID,
                    f"radar fetch failed: {exc}",
                ),
            )
