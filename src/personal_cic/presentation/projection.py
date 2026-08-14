from datetime import datetime, timezone
import statistics
from enum import Enum
from typing import Any, Mapping

from personal_cic.core.config import SiteAnchorConfig
from personal_cic.core.world import WorldState
from personal_cic.semantics import (
    SemanticAssertion,
    SemanticKind,
    SemanticSourceRole,
    project_world_semantics,
)


_HEALTH_ORDER = {
    "unknown": 0,
    "nominal": 1,
    "warning": 2,
    "critical": 3,
}

_OBS_ORDER = {
    "current": 0,
    "degraded": 1,
    "unavailable": 2,
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _freshness_seconds(checked_at: str | None) -> float | None:
    if not checked_at:
        return None
    try:
        checked = datetime.fromisoformat(checked_at)
    except ValueError:
        return None
    if checked.tzinfo is None:
        checked = checked.replace(tzinfo=timezone.utc)
    return max(
        0.0,
        round((datetime.now(timezone.utc) - checked).total_seconds(), 3),
    )


def _component(entity: dict[str, Any], name: str) -> dict[str, Any] | None:
    value = entity.get("components", {}).get(name)
    return value if isinstance(value, dict) else None


def _worst(values: list[str], order: dict[str, int], default: str) -> str:
    known = [value for value in values if value in order]
    if not known:
        return default
    return max(known, key=lambda value: order[value])


def build_systems_projection(
    world: WorldState,
    *,
    runtime_pid: int | None = None,
    runtime_started_at: str | None = None,
) -> dict[str, Any]:
    """Build a read-only operator projection from one atomic WorldState snapshot.

    Presentation owns no device truth and performs no hardware queries.  Every
    displayed domain value comes from the CIC WorldState snapshot.
    """

    snapshot = world.snapshot()
    entities = snapshot.get("entities", {})

    host = entities.get("engage-one", {})
    tenda = entities.get("tenda-u11-pro", {})

    host_obs = _component(host, "ObservationState") or {}
    host_health = _component(host, "HealthState") or {}
    compute = _component(host, "ComputeState") or {}
    memory = _component(host, "MemoryState") or {}
    storage = _component(host, "StorageState") or {}
    temperature = _component(host, "TemperatureState") or {}
    uptime = _component(host, "UptimeState") or {}

    tenda_obs = _component(tenda, "ObservationState") or {}
    tenda_health = _component(tenda, "HealthState") or {}
    usb = _component(tenda, "UsbDeviceState") or {}
    wifi = _component(tenda, "WifiLinkState") or {}

    health_values = [
        str(host_health.get("status", "unknown")),
        str(tenda_health.get("status", "unknown")),
    ]
    observation_values = [
        str(host_obs.get("availability", "unavailable")),
        str(tenda_obs.get("availability", "unavailable")),
    ]

    frequency = wifi.get("frequency_mhz")
    if isinstance(frequency, (int, float)):
        if frequency >= 5925:
            band = "6 GHz"
        elif frequency >= 4900:
            band = "5 GHz"
        elif frequency >= 2400:
            band = "2.4 GHz"
        else:
            band = "other"
    else:
        band = None

    return {
        "api_version": 1,
        "presentation": {
            "mode": "read-only",
            "generated_at": _now_iso(),
            "world_schema_version": snapshot.get("schema_version"),
        },
        "runtime": {
            "pid": runtime_pid,
            "started_at": runtime_started_at,
        },
        "summary": {
            "health": _worst(health_values, _HEALTH_ORDER, "unknown"),
            "observation": _worst(
                observation_values,
                _OBS_ORDER,
                "unavailable",
            ),
            "wlan_connected": bool(wifi.get("connected", False)),
        },
        "host": {
            "entity_id": "engage-one",
            "label": host.get("label", "engage-one"),
            "health": {
                "status": host_health.get("status", "unknown"),
                "reasons": host_health.get("reasons", []),
            },
            "observation": {
                "availability": host_obs.get("availability", "unavailable"),
                "adapter_id": host_obs.get("adapter_id"),
                "checked_at": host_obs.get("checked_at"),
                "last_success_at": host_obs.get("last_success_at"),
                "freshness_seconds": _freshness_seconds(
                    host_obs.get("checked_at")
                ),
                "reasons": host_obs.get("reasons", []),
            },
            "compute": compute,
            "memory": memory,
            "storage": storage,
            "temperature": temperature,
            "uptime": uptime,
        },
        "tenda": {
            "entity_id": "tenda-u11-pro",
            "label": tenda.get("label", "tenda-u11-pro"),
            "health": {
                "status": tenda_health.get("status", "unknown"),
                "reasons": tenda_health.get("reasons", []),
            },
            "observation": {
                "availability": tenda_obs.get(
                    "availability",
                    "unavailable",
                ),
                "adapter_id": tenda_obs.get("adapter_id"),
                "checked_at": tenda_obs.get("checked_at"),
                "last_success_at": tenda_obs.get("last_success_at"),
                "freshness_seconds": _freshness_seconds(
                    tenda_obs.get("checked_at")
                ),
                "reasons": tenda_obs.get("reasons", []),
            },
            "usb": usb,
            "wifi": {
                **wifi,
                "band": band,
            },
        },
    }


_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    56: "Light freezing drizzle",
    57: "Freezing drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Freezing rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Light showers",
    81: "Showers",
    82: "Heavy showers",
    85: "Light snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Severe thunderstorm with hail",
}


def build_world_projection(world: WorldState, *, feed: list[dict] | None = None) -> dict[str, Any]:
    """Project source-aware world observations without promoting them beyond scope."""

    snapshot = world.snapshot()
    entities = snapshot.get("entities", {})
    weather_entity = entities.get("local-weather", {})
    alerts_entity = entities.get("local-weather-alerts", {})
    surface_entity = entities.get("local-weather-surface", {})
    forecast_entity = entities.get("local-weather-nws-forecast", {})
    estimate_entity = entities.get("local-weather-estimate", {})
    radar_entity = entities.get("local-weather-radar", {})
    radar_context_entity = entities.get("local-weather-radar-context", {})

    weather = _component(weather_entity, "WeatherState") or {}
    forecast_daily = _component(weather_entity, "WeatherForecastState") or {}
    weather_obs = _component(weather_entity, "ObservationState") or {}
    alerts = _component(alerts_entity, "WeatherAlertState") or {}
    alerts_obs = _component(alerts_entity, "ObservationState") or {}
    surface = _component(surface_entity, "SurfaceObservationNetworkState") or {}
    surface_obs = _component(surface_entity, "ObservationState") or {}
    nws_forecast = _component(forecast_entity, "NWSHourlyForecastState") or {}
    forecast_obs = _component(forecast_entity, "ObservationState") or {}
    estimate = _component(estimate_entity, "CurrentWeatherEstimateState") or {}
    estimate_obs = _component(estimate_entity, "ObservationState") or {}
    radar = _component(radar_entity, "RadarMosaicState") or {}
    radar_obs = _component(radar_entity, "ObservationState") or {}
    radar_context = _component(radar_context_entity, "RadarContextState") or {}
    radar_context_obs = _component(radar_context_entity, "ObservationState") or {}

    weather_code = weather.get("weather_code")
    location = (
        estimate.get("location_label") or surface.get("location_label") or weather.get("location_label")
        or alerts.get("location_label") or "configured local area"
    )

    def obs(value):
        return {
            "availability": value.get("availability", "unavailable"),
            "adapter_id": value.get("adapter_id"),
            "checked_at": value.get("checked_at"),
            "last_success_at": value.get("last_success_at"),
            "freshness_seconds": _freshness_seconds(value.get("checked_at")),
            "last_success_age_seconds": _freshness_seconds(value.get("last_success_at")),
            "reasons": value.get("reasons", []),
        }

    stations = surface.get("stations") or []

    def station_values(key):
        return [float(station[key]) for station in stations if isinstance(station, dict) and isinstance(station.get(key), (int, float))]

    wind_speeds = station_values("wind_speed_mph")
    gusts = station_values("wind_gust_mph")
    visibilities = station_values("visibility_sm")
    ceilings = station_values("ceiling_ft_agl")
    surface_projection = {
        **surface,
        "wind_speed_median_mph": None if not wind_speeds else statistics.median(wind_speeds),
        "wind_gust_max_mph": None if not gusts else max(gusts),
        "visibility_min_sm": None if not visibilities else min(visibilities),
        "ceiling_min_ft_agl": None if not ceilings else int(min(ceilings)),
        "observation": obs(surface_obs),
    }

    return {
        "api_version": 4,
        "presentation": {
            "mode": "read-only",
            "generated_at": _now_iso(),
            "world_schema_version": snapshot.get("schema_version"),
        },
        "location": {"label": location},
        "estimate": {
            **estimate,
            "current_now": estimate_obs.get("availability") == "current",
            "observation": obs(estimate_obs),
        },
        "surface": surface_projection,
        "weather": {
            **weather,
            "condition": _WEATHER_CODES.get(weather_code, "Unknown") if weather_code is not None else None,
            "observation": obs(weather_obs),
            "forecast": forecast_daily,
        },
        "nws_forecast": {**nws_forecast, "observation": obs(forecast_obs)},
        "alerts": {
            **alerts,
            "authoritative_now": alerts_obs.get("availability") == "current",
            "observation": obs(alerts_obs),
        },
        "radar": {
            **radar,
            "frames": [
                {
                    **frame,
                    "image_url": "/radar/frames/" + str(frame.get("image_sha256")) + ".png",
                    "warning_image_url": (
                        None
                        if not frame.get("warning_image_sha256")
                        else "/radar/warning-frames/"
                        + str(frame.get("warning_image_sha256"))
                        + ".png"
                    ),
                }
                for frame in (radar.get("frames") or [])
                if isinstance(frame, dict) and frame.get("image_sha256")
            ],
            "current_now": radar_obs.get("availability") == "current",
            "displayable_now": bool(radar.get("image_sha256"))
            and radar_obs.get("availability") in ("current", "degraded"),
            "frame_state": (
                "CURRENT"
                if radar.get("image_sha256")
                and radar_obs.get("availability") == "current"
                else "DEGRADED"
                if radar.get("image_sha256")
                and radar_obs.get("availability") == "degraded"
                else "LAST KNOWN"
                if radar.get("image_sha256")
                else "UNAVAILABLE"
            ),
            "warning_overlay_current": bool(radar.get("warning_overlay_available"))
            and radar_obs.get("availability") in ("current", "degraded"),
            "warning_overlay_state": (
                "CURRENT"
                if radar.get("warning_overlay_available")
                and radar_obs.get("availability") in ("current", "degraded")
                else "LAST KNOWN"
                if radar.get("warning_overlay_available")
                else "UNAVAILABLE"
            ),
            "stream_age_seconds": _freshness_seconds(
                radar.get("stream_latest_at")
            ),
            "frame_retrieval_age_seconds": _freshness_seconds(
                radar.get("frame_retrieved_at")
            ),
            "last_success_age_seconds": _freshness_seconds(
                radar_obs.get("last_success_at")
            ),
            "image_url": (
                None
                if not radar.get("image_sha256")
                else "/radar/frames/" + str(radar.get("image_sha256")) + ".png"
            ),
            "warning_image_url": (
                None
                if not radar.get("warning_image_sha256")
                or not (
                    radar.get("warning_overlay_available")
                    and radar_obs.get("availability") in ("current", "degraded")
                )
                else "/radar/warning-frames/"
                + str(radar.get("warning_image_sha256"))
                + ".png"
            ),
            "legend_image_url": (
                None
                if not radar.get("legend_image_sha256")
                else "/radar/legend.png?sha="
                + str(radar.get("legend_image_sha256"))
            ),
            "observation": obs(radar_obs),
        },
        "radar_context": {
            **radar_context,
            "displayable_now": bool(radar_context.get("context_sha256")),
            "context_state": (
                "CURRENT"
                if radar_context.get("context_sha256")
                and radar_context_obs.get("availability") == "current"
                else "DEGRADED"
                if radar_context.get("context_sha256")
                and radar_context_obs.get("availability") == "degraded"
                else "LAST KNOWN"
                if radar_context.get("context_sha256")
                else "UNAVAILABLE"
            ),
            "context_age_seconds": _freshness_seconds(
                radar_context.get("retrieved_at")
            ),
            "context_url": (
                None
                if not radar_context.get("context_sha256")
                else "/radar/context.json?sha="
                + str(radar_context.get("context_sha256"))
            ),
            "observation": obs(radar_context_obs),
        },
        "feed": list(feed or []),
    }


def build_traffic_projection(
    world: WorldState,
    *,
    site_anchor: SiteAnchorConfig | None = None,
) -> dict[str, Any]:
    """Project source-preserving local traffic state for an operator map.

    The projection deliberately keeps each provider observation separate. Event
    kernels are a derived convenience layer and never replace their source records.
    """

    snapshot = world.snapshot()
    entities = snapshot.get("entities", {})

    def entity_component(entity_id: str, component_name: str) -> dict[str, Any]:
        return _component(entities.get(entity_id, {}), component_name) or {}

    def obs(entity_id: str) -> dict[str, Any]:
        value = entity_component(entity_id, "ObservationState")
        return {
            "availability": value.get("availability", "unavailable"),
            "adapter_id": value.get("adapter_id"),
            "checked_at": value.get("checked_at"),
            "last_success_at": value.get("last_success_at"),
            "freshness_seconds": _freshness_seconds(value.get("checked_at")),
            "last_success_age_seconds": _freshness_seconds(value.get("last_success_at")),
            "reasons": value.get("reasons", []),
        }

    source_entities = {
        "drivenc_events": "local-traffic-drivenc-events",
        "wzdx": "local-traffic-wzdx",
        "cmpd": "local-traffic-cmpd-cad",
        "charlotte_closures": "local-traffic-charlotte-closures",
        "tomtom_incidents": "local-traffic-tomtom-incidents",
        "tomtom_flow": "local-traffic-tomtom-flow",
        "cameras": "local-traffic-drivenc-cameras",
        "message_signs": "local-traffic-drivenc-signs",
    }

    event_sources: dict[str, dict[str, Any]] = {}
    flat_events: list[dict[str, Any]] = []
    for key in ("drivenc_events", "wzdx", "cmpd", "charlotte_closures", "tomtom_incidents"):
        entity_id = source_entities[key]
        state = entity_component(entity_id, "TrafficEventCollectionState")
        observation = obs(entity_id)
        usable = observation["availability"] in ("current", "degraded")
        event_sources[key] = {
            **state,
            "authoritative_now": usable,
            "observation": observation,
        }
        for event in state.get("events") or []:
            if not isinstance(event, dict):
                continue
            flat_events.append(
                {
                    **event,
                    "source_key": key,
                    "source_authoritative_now": usable,
                    "source_availability": observation["availability"],
                    "community_last_report_age_seconds": _freshness_seconds(event.get("community_last_report_at")),
                }
            )

    flow_state = entity_component(source_entities["tomtom_flow"], "TrafficFlowCollectionState")
    flow_obs = obs(source_entities["tomtom_flow"])
    flow_usable = flow_obs["availability"] in ("current", "degraded")
    flow_probes = []
    for probe in flow_state.get("probes") or []:
        if not isinstance(probe, dict):
            continue
        current_speed = probe.get("current_speed_mph")
        free_flow_speed = probe.get("free_flow_speed_mph")
        speed_ratio = None
        if isinstance(current_speed, (int, float)) and isinstance(free_flow_speed, (int, float)) and free_flow_speed > 0:
            speed_ratio = current_speed / free_flow_speed
        current_time = probe.get("current_travel_time_seconds")
        free_time = probe.get("free_flow_travel_time_seconds")
        travel_delay = None
        if isinstance(current_time, (int, float)) and isinstance(free_time, (int, float)):
            travel_delay = current_time - free_time
        flow_probes.append({
            **probe,
            "speed_vs_free_flow": speed_ratio,
            "travel_time_delta_seconds": travel_delay,
            "source_authoritative_now": flow_usable,
            "source_availability": flow_obs["availability"],
        })
    flow = {
        **flow_state,
        "probes": flow_probes,
        "authoritative_now": flow_usable,
        "observation": flow_obs,
    }

    cameras_state = entity_component(source_entities["cameras"], "TrafficCameraCollectionState")
    cameras_obs = obs(source_entities["cameras"])
    cameras_usable = cameras_obs["availability"] in ("current", "degraded")
    cameras = {
        **cameras_state,
        "authoritative_now": cameras_usable,
        "observation": cameras_obs,
    }

    signs_state = entity_component(source_entities["message_signs"], "TrafficMessageSignCollectionState")
    signs_obs = obs(source_entities["message_signs"])
    signs_usable = signs_obs["availability"] in ("current", "degraded")
    signs = {
        **signs_state,
        "authoritative_now": signs_usable,
        "observation": signs_obs,
    }

    situation_entity = "local-traffic-situation"
    situation = entity_component(situation_entity, "TrafficSituationState")
    situation_obs = obs(situation_entity)

    radar_context_entity = entities.get("local-weather-radar-context", {})
    radar_context = _component(radar_context_entity, "RadarContextState") or {}
    radar_context_obs = _component(radar_context_entity, "ObservationState") or {}
    context_sha = radar_context.get("context_sha256")

    center_lat = situation.get("scope_center_latitude")
    center_lon = situation.get("scope_center_longitude")
    waze_url = None
    if (
        situation.get("external_waze_visual_enabled")
        and isinstance(center_lat, (int, float))
        and isinstance(center_lon, (int, float))
    ):
        zoom = int(situation.get("external_waze_zoom") or 11)
        waze_url = (
            "https://embed.waze.com/iframe?zoom="
            + str(zoom)
            + "&lat="
            + str(center_lat)
            + "&lon="
            + str(center_lon)
        )

    site = None
    if (
        site_anchor is not None
        and site_anchor.enabled
        and isinstance(site_anchor.latitude, (int, float))
        and isinstance(site_anchor.longitude, (int, float))
    ):
        site = {
            "label": site_anchor.label,
            "address": site_anchor.address,
            "latitude": site_anchor.latitude,
            "longitude": site_anchor.longitude,
            "position_kind": site_anchor.position_kind,
            "source_lineage": site_anchor.source_lineage,
            "source_record_id": site_anchor.source_record_id,
            "source_verified_at": site_anchor.source_verified_at,
            "source_artifact_sha256": site_anchor.source_artifact_sha256,
            "live_operator_position": False,
        }

    return {
        "api_version": 2,
        "presentation": {
            "mode": "read-only",
            "generated_at": _now_iso(),
            "world_schema_version": snapshot.get("schema_version"),
        },
        "location": {
            "label": situation.get("location_label") or "configured local area",
            "latitude": center_lat,
            "longitude": center_lon,
            "radius_miles": situation.get("scope_radius_miles"),
            "role": "collection_scope_center",
        },
        "operator_context": {
            "site_anchor": site,
            "live_operator_position": None,
        },
        "summary": {
            "availability": situation_obs["availability"],
            "event_kernels": situation.get("event_kernel_count"),
            "source_observations": situation.get("source_observation_count"),
            "full_closures": situation.get("full_closure_count"),
            "cameras": situation.get("camera_count"),
            "active_message_signs": situation.get("active_message_sign_count"),
            "flow_probes": situation.get("flow_probe_count", 0),
            "source_families": situation.get("current_source_families", []),
            "correlation_mode": situation.get("correlation_mode"),
            "collection_gaps": situation.get("collection_gaps", []),
            "observation": situation_obs,
        },
        "event_sources": event_sources,
        "events": flat_events,
        "kernels": situation.get("kernels", []),
        "cameras": cameras,
        "message_signs": signs,
        "flow": flow,
        "map_context": {
            **radar_context,
            "displayable_now": bool(context_sha),
            "context_state": (
                "CURRENT"
                if context_sha and radar_context_obs.get("availability") == "current"
                else "DEGRADED"
                if context_sha and radar_context_obs.get("availability") == "degraded"
                else "LAST KNOWN"
                if context_sha
                else "UNAVAILABLE"
            ),
            "context_url": None if not context_sha else "/radar/context.json?sha=" + str(context_sha),
            "observation": {
                "availability": radar_context_obs.get("availability", "unavailable"),
                "adapter_id": radar_context_obs.get("adapter_id"),
                "checked_at": radar_context_obs.get("checked_at"),
                "last_success_at": radar_context_obs.get("last_success_at"),
                "freshness_seconds": _freshness_seconds(radar_context_obs.get("checked_at")),
                "last_success_age_seconds": _freshness_seconds(radar_context_obs.get("last_success_at")),
                "reasons": radar_context_obs.get("reasons", []),
            },
        },
        "external_visual_sources": {
            "osm_reference": {
                "enabled": True,
                "mode": "browser_direct_reference",
                "canonical_worldstate": False,
                "provider": "OpenStreetMap standard tile service",
                "tile_url_template": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                "max_zoom": 19,
                "disclosure": (
                    "OpenStreetMap standard tiles are browser-direct reference cartography only. "
                    "They are not normalized into CIC WorldState and are not evidence or corroboration."
                ),
            },
            "waze": {
                "enabled": bool(waze_url),
                "mode": "operator_opt_in_browser_direct",
                "canonical_worldstate": False,
                "url": waze_url,
                "disclosure": (
                    "Waze Live Map is an external browser-direct visual source. "
                    "Its crowd reports are not normalized into CIC WorldState in RC2."
                ),
            }
        },
    }

_SEMANTIC_DEFAULT_LIMIT = 500
_SEMANTIC_MAX_LIMIT = 2000


def _semantic_json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _semantic_json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_semantic_json_value(item) for item in value]
    return value


def _semantic_entity_id(assertion: SemanticAssertion) -> str | None:
    for source in assertion.provenance.sources:
        if source.role is SemanticSourceRole.WORLD_ENTITY_REFERENCE:
            return source.native_id or source.ref_id
    return None


def _semantic_assertion_json(assertion: SemanticAssertion) -> dict[str, Any]:
    return {
        "assertion_id": assertion.assertion_id,
        "proposition_key": assertion.proposition_key,
        "entity_id": _semantic_entity_id(assertion),
        "kind": assertion.kind.value,
        "home": assertion.home,
        "subject_ref": assertion.subject_ref,
        "predicate": assertion.predicate,
        "value": _semantic_json_value(assertion.value),
        "provenance": {
            "origin": assertion.provenance.origin.value,
            "derivation_ref": assertion.provenance.derivation_ref,
            "sources": [
                {
                    "ref_id": source.ref_id,
                    "role": source.role.value,
                    "authority": source.authority,
                    "native_id": source.native_id,
                }
                for source in assertion.provenance.sources
            ],
        },
        "temporal": {
            "phenomenon_time": assertion.temporal.phenomenon_time,
            "source_time": assertion.temporal.source_time,
            "observed_at": assertion.temporal.observed_at,
            "retrieved_at": assertion.temporal.retrieved_at,
            "derived_at": assertion.temporal.derived_at,
        },
        "qualifiers": _semantic_json_value(assertion.qualifiers),
    }


def build_semantic_projection(
    world: WorldState,
    *,
    entity_id: str | None = None,
    kind: str | None = None,
    predicate: str | None = None,
    limit: int = _SEMANTIC_DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Build a bounded, read-only inspection view over semantic assertions."""
    if isinstance(limit, bool) or not isinstance(limit, int) or not (1 <= limit <= _SEMANTIC_MAX_LIMIT):
        raise ValueError(f"limit must be an integer from 1 to {_SEMANTIC_MAX_LIMIT}")

    valid_kinds = {item.value for item in SemanticKind}
    if kind is not None and kind not in valid_kinds:
        raise ValueError("unknown semantic kind")

    assertions = list(project_world_semantics(world))
    projected_count = len(assertions)

    if entity_id is not None:
        assertions = [item for item in assertions if _semantic_entity_id(item) == entity_id]
    if kind is not None:
        assertions = [item for item in assertions if item.kind.value == kind]
    if predicate is not None:
        assertions = [item for item in assertions if item.predicate == predicate]

    assertions.sort(
        key=lambda item: (
            _semantic_entity_id(item) or "",
            item.home,
            item.kind.value,
            item.predicate,
            item.assertion_id,
        )
    )
    total_count = len(assertions)
    selected = assertions[:limit]

    return {
        "api_version": 1,
        "presentation": {
            "mode": "read-only",
            "generated_at": _now_iso(),
            "world_authority": False,
            "semantic_persistence": False,
            "semantic_projection_source": "stable_typed_world_read_snapshot",
        },
        "filters": {
            "entity_id": entity_id,
            "kind": kind,
            "predicate": predicate,
            "limit": limit,
        },
        "projected_count": projected_count,
        "total_count": total_count,
        "returned_count": len(selected),
        "truncated": total_count > len(selected),
        "assertions": [_semantic_assertion_json(item) for item in selected],
    }

