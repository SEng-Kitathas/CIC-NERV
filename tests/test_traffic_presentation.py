import json
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from personal_cic.core.events import EventBus
from personal_cic.core.observations import ObservationAvailability
from personal_cic.core.world import WorldState
from personal_cic.core.world.components import (
    GeoPoint,
    ObservationState,
    RadarContextState,
    TrafficCameraCollectionState,
    TrafficCameraObservation,
    TrafficEventCollectionState,
    TrafficEventKernel,
    TrafficEventObservation,
    TrafficFlowCollectionState,
    TrafficFlowProbeObservation,
    TrafficMessageSignCollectionState,
    TrafficMessageSignObservation,
    TrafficSituationState,
)
from personal_cic.presentation import PresentationServer, build_traffic_projection
from personal_cic.core.config import SiteAnchorConfig


class TrafficPresentationTests(unittest.TestCase):
    def setUp(self):
        self.world = WorldState(EventBus())
        self.now = "2026-08-12T05:00:00+00:00"

        event = TrafficEventObservation(
            source_record_id="drive-123",
            source_family="NCDOT/ATMSERS",
            provider="DriveNC Events",
            collection_class="official_report",
            event_type="incident",
            event_subtype="crash",
            description="Crash on I-485 Inner",
            roadway="I-485",
            direction="Inner",
            county="Mecklenburg",
            geometry=(GeoPoint(35.100, -80.700),),
            reported_at="2026-08-12T04:50:00+00:00",
            updated_at="2026-08-12T04:59:00+00:00",
            severity="high",
            full_closure=False,
            lanes_affected="1 Right Lane Affected",
            source_organization="ATMSERS",
            source_id="source-123",
            upstream_event_id="123",
        )
        self._put_event_source(
            "local-traffic-drivenc-events",
            "DriveNC Events",
            "NCDOT/ATMSERS",
            "official_report",
            (event,),
            ObservationAvailability.CURRENT,
            "drivenc.events",
        )
        self._put_event_source(
            "local-traffic-wzdx",
            "DriveNC WZDx",
            "NCDOT/ATMSERS",
            "official_report",
            (),
            ObservationAvailability.CURRENT,
            "drivenc.wzdx",
        )
        self._put_event_source(
            "local-traffic-cmpd-cad",
            "CMPD Traffic CAD",
            "CMPD CAD",
            "official_report",
            (),
            ObservationAvailability.CURRENT,
            "cmpd.traffic_cad",
        )
        self._put_event_source(
            "local-traffic-charlotte-closures",
            "Charlotte Street Closures",
            "City of Charlotte/CDOT",
            "official_report",
            (),
            ObservationAvailability.CURRENT,
            "charlotte.street_closures",
        )

        camera = TrafficCameraObservation(
            camera_id="4020",
            source_family="NCDOT/ATMSERS",
            provider="DriveNC Cameras",
            source_id="5135",
            county="Mecklenburg",
            roadway="I-485",
            direction="Outer",
            location="CCTV10-I485-30.1O_I85",
            latitude=35.35311,
            longitude=-80.73711,
            status="Enabled",
            page_url="https://www.drivenc.gov/map/Cctv/4020",
            video_url="https://camera.example/chan.m3u8",
        )
        self.world.ensure_entity("local-traffic-drivenc-cameras", "DriveNC Cameras")
        self.world.upsert_component(
            "local-traffic-drivenc-cameras",
            TrafficCameraCollectionState(
                "Indian Trail / Charlotte",
                "DriveNC Cameras",
                "NCDOT/ATMSERS",
                35.0768,
                -80.6692,
                75.0,
                1160,
                1,
                (camera,),
            ),
        )
        self._put_obs(
            "local-traffic-drivenc-cameras",
            "drivenc.cameras",
            ObservationAvailability.CURRENT,
        )

        sign = TrafficMessageSignObservation(
            sign_id="ATMS_DMS--794",
            source_family="NCDOT/ATMSERS",
            provider="DriveNC Message Signs",
            county="Mecklenburg",
            roadway="I-277",
            direction="Unknown",
            name="DMS10-I277-0.5O",
            latitude=35.22441,
            longitude=-80.85751,
            updated_at="2026-08-12T04:59:00+00:00",
            messages=("LEFT LANE CLOSED", "REDUCE SPEED"),
        )
        self.world.ensure_entity("local-traffic-drivenc-signs", "DriveNC Message Signs")
        self.world.upsert_component(
            "local-traffic-drivenc-signs",
            TrafficMessageSignCollectionState(
                "Indian Trail / Charlotte",
                "DriveNC Message Signs",
                "NCDOT/ATMSERS",
                35.0768,
                -80.6692,
                75.0,
                400,
                1,
                1,
                (sign,),
            ),
        )
        self._put_obs(
            "local-traffic-drivenc-signs",
            "drivenc.message_signs",
            ObservationAvailability.CURRENT,
        )

        kernel = TrafficEventKernel(
            kernel_id="NCDOT/ATMSERS:123",
            roadway="I-485",
            summary="Crash on I-485 Inner",
            latitude=35.100,
            longitude=-80.700,
            source_families=("NCDOT/ATMSERS",),
            source_record_refs=("drivenc_events:drive-123",),
            association_basis="exact same-lineage upstream event identifier",
        )
        self.world.ensure_entity("local-traffic-situation", "Local Traffic Situation")
        self.world.upsert_component(
            "local-traffic-situation",
            TrafficSituationState(
                location_label="Indian Trail / Charlotte",
                derived_at=self.now,
                scope_center_latitude=35.0768,
                scope_center_longitude=-80.6692,
                scope_radius_miles=75.0,
                source_observation_count=1,
                event_kernel_count=1,
                full_closure_count=0,
                camera_count=1,
                active_message_sign_count=1,
                current_source_families=("NCDOT/ATMSERS", "CMPD CAD", "City of Charlotte/CDOT"),
                collection_gaps=(
                    "No supported normalized Waze crowd machine feed is established; optional Live Map is external visual evidence only.",
                ),
                correlation_mode="exact same-lineage upstream identifiers only; no cross-lineage merge without earned association",
                external_waze_visual_enabled=True,
                external_waze_zoom=11,
                kernels=(kernel,),
            ),
        )
        self._put_obs(
            "local-traffic-situation",
            "personal_cic.traffic_situation",
            ObservationAvailability.CURRENT,
        )

        # Traffic is allowed to reuse the locally cached geographic reference
        # artifact, but that context remains separately sourced and separately
        # authoritative.
        self.world.ensure_entity("local-weather-radar-context", "Radar Context")
        self.world.upsert_component(
            "local-weather-radar-context",
            RadarContextState(
                location_label="Indian Trail / Charlotte",
                provider="U.S. Census Bureau TIGERweb",
                retrieved_at=self.now,
                west=-81.5,
                south=34.4,
                east=-79.8,
                north=35.8,
                county_count=2,
                primary_road_count=3,
                secondary_road_count=4,
                place_count=5,
                context_sha256="a" * 64,
                content_sha256="b" * 64,
            ),
        )
        self._put_obs(
            "local-weather-radar-context",
            "tigerweb.radar_context",
            ObservationAvailability.CURRENT,
        )

    def _put_event_source(
        self,
        entity_id,
        provider,
        source_family,
        collection_class,
        events,
        availability,
        adapter_id,
    ):
        self.world.ensure_entity(entity_id, provider)
        self.world.upsert_component(
            entity_id,
            TrafficEventCollectionState(
                location_label="Indian Trail / Charlotte",
                provider=provider,
                source_family=source_family,
                collection_class=collection_class,
                scope_center_latitude=35.0768,
                scope_center_longitude=-80.6692,
                scope_radius_miles=75.0,
                source_record_count=len(events),
                local_record_count=len(events),
                freshest_source_at=self.now if events else None,
                events=events,
            ),
        )
        self._put_obs(entity_id, adapter_id, availability)

    def _put_obs(self, entity_id, adapter_id, availability):
        self.world.upsert_component(
            entity_id,
            ObservationState(
                adapter_id,
                availability,
                self.now,
                self.now if availability != ObservationAvailability.UNAVAILABLE else None,
                (),
            ),
        )

    def test_projection_is_read_only_and_preserves_source_identity(self):
        before = self.world.snapshot()
        payload = build_traffic_projection(self.world)
        after = self.world.snapshot()

        self.assertEqual(before, after)
        self.assertEqual(payload["api_version"], 2)
        self.assertEqual(payload["presentation"]["mode"], "read-only")
        self.assertEqual(payload["summary"]["availability"], "current")
        self.assertEqual(payload["summary"]["event_kernels"], 1)
        self.assertEqual(payload["events"][0]["source_family"], "NCDOT/ATMSERS")
        self.assertEqual(payload["events"][0]["source_record_id"], "drive-123")
        self.assertTrue(payload["events"][0]["source_authoritative_now"])
        self.assertEqual(payload["kernels"][0]["association_basis"], "exact same-lineage upstream event identifier")
        self.assertIn("CMPD CAD", payload["summary"]["source_families"])

    def test_projection_exposes_cameras_signs_and_valid_negative_collections(self):
        payload = build_traffic_projection(self.world)

        self.assertTrue(payload["cameras"]["authoritative_now"])
        self.assertEqual(payload["cameras"]["cameras"][0]["video_url"], "https://camera.example/chan.m3u8")
        self.assertTrue(payload["message_signs"]["authoritative_now"])
        self.assertEqual(payload["message_signs"]["signs"][0]["messages"], ["LEFT LANE CLOSED", "REDUCE SPEED"])
        self.assertEqual(payload["event_sources"]["cmpd"]["local_record_count"], 0)
        self.assertTrue(payload["event_sources"]["cmpd"]["authoritative_now"])

    def test_unavailable_source_remains_last_known_but_is_not_authoritative(self):
        self._put_obs(
            "local-traffic-drivenc-events",
            "drivenc.events",
            ObservationAvailability.UNAVAILABLE,
        )
        payload = build_traffic_projection(self.world)

        self.assertEqual(payload["event_sources"]["drivenc_events"]["observation"]["availability"], "unavailable")
        self.assertFalse(payload["event_sources"]["drivenc_events"]["authoritative_now"])
        event = next(e for e in payload["events"] if e["source_key"] == "drivenc_events")
        self.assertFalse(event["source_authoritative_now"])
        self.assertEqual(event["source_availability"], "unavailable")

    def test_waze_visual_is_explicitly_external_and_noncanonical(self):
        payload = build_traffic_projection(self.world)
        waze = payload["external_visual_sources"]["waze"]

        self.assertTrue(waze["enabled"])
        self.assertFalse(waze["canonical_worldstate"])
        self.assertEqual(waze["mode"], "operator_opt_in_browser_direct")
        self.assertIn("https://embed.waze.com/iframe?", waze["url"])
        self.assertNotIn("DRIVENC", waze["url"].upper())
        self.assertIn("not normalized into CIC WorldState", waze["disclosure"])

    def test_osm_detail_basemap_is_explicitly_external_reference_and_noncanonical(self):
        payload = build_traffic_projection(self.world)
        osm = payload["external_visual_sources"]["osm_reference"]

        self.assertTrue(osm["enabled"])
        self.assertFalse(osm["canonical_worldstate"])
        self.assertEqual(osm["mode"], "browser_direct_reference")
        self.assertEqual(osm["provider"], "OpenStreetMap standard tile service")
        self.assertEqual(osm["tile_url_template"], "https://tile.openstreetmap.org/{z}/{x}/{y}.png")
        self.assertIn("reference cartography only", osm["disclosure"])
        self.assertIn("not evidence or corroboration", osm["disclosure"])

    def test_local_reference_context_is_hash_bound_and_separate(self):
        payload = build_traffic_projection(self.world)
        context = payload["map_context"]

        self.assertEqual(context["context_state"], "CURRENT")
        self.assertEqual(context["context_url"], "/radar/context.json?sha=" + "a" * 64)
        self.assertEqual(context["provider"], "U.S. Census Bureau TIGERweb")


    def test_projection_preserves_tomtom_commercial_and_flow_semantics(self):
        event = TrafficEventObservation(
            source_record_id="TTI-1", source_family="TomTom Traffic",
            provider="TomTom Orbis Incident Details", collection_class="commercial_report",
            event_type="jam", event_subtype=None, description="Stopped traffic", roadway="US-74",
            direction=None, county=None, geometry=(GeoPoint(35.11, -80.61), GeoPoint(35.12, -80.62)),
            start_at="2026-08-12T15:09:30+00:00", magnitude_of_delay="major", delay_seconds=201,
            length_meters=119.1, road_numbers=("US-74",), from_location="A", to_location="B",
            probability_of_occurrence="certain", time_validity="present", event_details=("Stopped traffic",),
            event_codes=(101,), community_report_count=1, community_last_report_at="2025-06-26T23:36:00+00:00",
            source_organization="TomTom Traffic", source_id="TTI-1", upstream_event_id="TTI-1",
        )
        self._put_event_source(
            "local-traffic-tomtom-incidents", "TomTom Orbis Incident Details", "TomTom Traffic",
            "commercial_report", (event,), ObservationAvailability.CURRENT, "tomtom.incidents",
        )
        flow_probe = TrafficFlowProbeObservation(
            probe_id="ref", label="I-277 Uptown reference", source_family="TomTom Traffic",
            provider="TomTom Flow Segment Data", collection_class="commercial_modeled_telemetry",
            query_latitude=35.22441, query_longitude=-80.85751,
            match_method="nearest_road_fragment_to_query_point", functional_road_class="FRC2",
            current_speed_mph=22, free_flow_speed_mph=44, current_travel_time_seconds=86,
            free_flow_travel_time_seconds=43, confidence=1.0, road_closure=False, openlr="segment",
            geometry=(GeoPoint(35.22448, -80.85910), GeoPoint(35.22366, -80.85613)),
        )
        self.world.ensure_entity("local-traffic-tomtom-flow", "TomTom Flow")
        self.world.upsert_component(
            "local-traffic-tomtom-flow",
            TrafficFlowCollectionState(
                location_label="Indian Trail / Charlotte", provider="TomTom Flow Segment Data",
                source_family="TomTom Traffic", collection_class="commercial_modeled_telemetry",
                scope_center_latitude=35.0768, scope_center_longitude=-80.6692, scope_radius_miles=75,
                configured_probe_count=1, successful_probe_count=1, probes=(flow_probe,),
            ),
        )
        self._put_obs("local-traffic-tomtom-flow", "tomtom.flow", ObservationAvailability.CURRENT)

        payload = build_traffic_projection(self.world)
        tomtom_event = next(e for e in payload["events"] if e["source_key"] == "tomtom_incidents")
        self.assertEqual(tomtom_event["collection_class"], "commercial_report")
        self.assertEqual(tomtom_event["community_report_count"], 1)
        self.assertGreater(tomtom_event["community_last_report_age_seconds"], 0)
        self.assertNotEqual(tomtom_event["collection_class"], "crowd_report")
        flow = payload["flow"]["probes"][0]
        self.assertEqual(flow["match_method"], "nearest_road_fragment_to_query_point")
        self.assertEqual(flow["speed_vs_free_flow"], 0.5)
        self.assertEqual(flow["travel_time_delta_seconds"], 43)
        self.assertTrue(payload["flow"]["authoritative_now"])


    def test_projection_separates_collection_scope_from_fixed_site_anchor(self):
        site = SiteAnchorConfig(
            enabled=True,
            label="CIC SITE",
            address="7004 Dacian Ln, Indian Trail, NC 28079",
            latitude=35.12042277,
            longitude=-80.62950725,
            position_kind="fixed_site_anchor",
            source_lineage="Union County NC GIS Address_Point",
            source_record_id="65294",
            source_verified_at="2026-08-13T15:42:00Z",
            source_artifact_sha256="5cfcd68382511b5639dab09355a8e26919b50bf83f3f5660fb891488dd674d4b",
        )
        payload = build_traffic_projection(self.world, site_anchor=site)
        self.assertEqual(payload["location"]["role"], "collection_scope_center")
        self.assertNotEqual(payload["location"]["latitude"], site.latitude)
        self.assertEqual(payload["operator_context"]["site_anchor"]["position_kind"], "fixed_site_anchor")
        self.assertFalse(payload["operator_context"]["site_anchor"]["live_operator_position"])
        self.assertIsNone(payload["operator_context"]["live_operator_position"])
        self.assertEqual(payload["operator_context"]["site_anchor"]["source_record_id"], "65294")

    def test_http_traffic_projection_receives_site_anchor_from_presentation_server(self):
        site = SiteAnchorConfig(
            enabled=True, label="CIC SITE", address="7004 Dacian Ln, Indian Trail, NC 28079",
            latitude=35.12042277, longitude=-80.62950725, source_record_id="65294",
        )
        server = PresentationServer(
            world=self.world, host="127.0.0.1", port=0, runtime_metadata=lambda: {}, site_anchor=site,
        )
        server.start()
        self.addCleanup(server.stop)
        with urlopen(f"http://127.0.0.1:{server.bound_port}/api/v1/traffic", timeout=2) as response:
            payload = json.loads(response.read())
        self.assertAlmostEqual(payload["operator_context"]["site_anchor"]["latitude"], 35.12042277)
        self.assertAlmostEqual(payload["operator_context"]["site_anchor"]["longitude"], -80.62950725)

    def test_traffic_hmi_labels_fixed_site_anchor_without_calling_it_live_position(self):
        server = PresentationServer(
            world=self.world, host="127.0.0.1", port=0, runtime_metadata=lambda: {},
            site_anchor=SiteAnchorConfig(enabled=True, label="CIC SITE", latitude=35.12042277, longitude=-80.62950725),
        )
        server.start()
        self.addCleanup(server.stop)
        with urlopen(f"http://127.0.0.1:{server.bound_port}/traffic", timeout=2) as response:
            html = response.read().decode("utf-8")
        self.assertIn("SITE 15 MI", html)
        self.assertIn("site-anchor", html)
        self.assertIn("live operator-position observation", html)
        self.assertIn("operator_context?.site_anchor", html)
        self.assertNotIn("class:'home'", html)

    def test_http_traffic_surface_api_and_global_read_only_boundary(self):
        server = PresentationServer(
            world=self.world,
            host="127.0.0.1",
            port=0,
            runtime_metadata=lambda: {},
        )
        server.start()
        self.addCleanup(server.stop)
        port = server.bound_port

        with urlopen(f"http://127.0.0.1:{port}/traffic", timeout=2) as response:
            html = response.read().decode("utf-8")
            csp = response.headers.get("Content-Security-Policy")
            referrer_policy = response.headers.get("Referrer-Policy")

        self.assertIn("PERSONAL CIC // TRAFFIC", html)
        self.assertIn("READ-ONLY", html)
        self.assertIn("/api/v1/traffic", html)
        self.assertIn("id=\"map-engine\"", html)
        self.assertIn("id=\"map-overlay\"", html)
        self.assertIn("id=\"load-waze\"", html)
        self.assertIn("id=\"l-tomtom\"", html)
        self.assertIn("id=\"l-flow\"", html)
        self.assertIn("003f RC2D-R2", html)
        self.assertIn("direct browser egress to Waze", html)
        self.assertNotIn("DRIVENC_API_KEY", html)
        self.assertNotIn("TOMTOM_API_KEY", html)
        self.assertNotIn("fetch('https://api.tomtom.com", html)
        self.assertNotIn('fetch("https://api.tomtom.com', html)
        self.assertNotIn("fetch('https://www.drivenc.gov", html)
        self.assertNotIn('fetch("https://www.drivenc.gov', html)
        self.assertNotIn("fetch('https://cmpdinfo", html)
        self.assertNotIn('fetch("https://cmpdinfo', html)
        self.assertIn("connect-src 'self' https://tile.openstreetmap.org", csp)
        self.assertIn("frame-src https://embed.waze.com", csp)
        self.assertIn("img-src 'self' data: blob: https://tile.openstreetmap.org", csp)
        self.assertIn("worker-src blob:", csp)
        self.assertIn("child-src blob:", csp)
        self.assertEqual(referrer_policy, "strict-origin-when-cross-origin")

        with urlopen(f"http://127.0.0.1:{port}/api/v1/traffic", timeout=2) as response:
            payload = json.loads(response.read())
        self.assertEqual(payload["presentation"]["mode"], "read-only")
        self.assertEqual(payload["summary"]["event_kernels"], 1)

        request = Request(
            f"http://127.0.0.1:{port}/api/v1/traffic",
            method="POST",
            data=b"{}",
        )
        with self.assertRaises(HTTPError) as captured:
            urlopen(request, timeout=2)
        self.assertEqual(captured.exception.code, 405)


    def test_traffic_map_uses_geographic_camera_not_fixed_svg_aspect_projection(self):
        server = PresentationServer(
            world=self.world,
            host="127.0.0.1",
            port=0,
            runtime_metadata=lambda: {},
        )
        server.start()
        self.addCleanup(server.stop)

        with urlopen(f"http://127.0.0.1:{server.bound_port}/traffic", timeout=2) as response:
            html = response.read().decode("utf-8")

        self.assertIn('id="scope-view"', html)
        self.assertIn('id="local-view"', html)
        self.assertIn('id="fit-active"', html)
        self.assertIn('id="l-viewport-list"', html)
        self.assertIn('id="map-engine"', html)
        self.assertIn('id="map-overlay"', html)
        self.assertIn("new maplibregl.Map", html)
        self.assertIn("trackResize:true", html)
        self.assertIn("map.getBounds()", html)
        self.assertIn("map.project([lon,lat])", html)
        self.assertNotIn("const MAP_W=1200,MAP_H=760", html)
        self.assertNotIn('viewBox="0 0 1200 760"', html)
        self.assertNotIn("fitAspect(", html)

    def test_traffic_map_supports_native_camera_pan_zoom_rotation_and_pitch(self):
        server = PresentationServer(
            world=self.world,
            host="127.0.0.1",
            port=0,
            runtime_metadata=lambda: {},
        )
        server.start()
        self.addCleanup(server.stop)

        with urlopen(f"http://127.0.0.1:{server.bound_port}/traffic", timeout=2) as response:
            html = response.read().decode("utf-8")

        self.assertIn("scrollZoom:true", html)
        self.assertIn("dragRotate:true", html)
        self.assertIn("pitchWithRotate:true", html)
        self.assertIn("touchPitch:true", html)
        self.assertIn("visualizePitch:true", html)
        self.assertIn('id="rotate-left"', html)
        self.assertIn('id="rotate-right"', html)
        self.assertIn('id="pitch-up"', html)
        self.assertIn('id="pitch-down"', html)
        self.assertIn('id="north-view"', html)
        self.assertIn("map.easeTo({bearing:", html)
        self.assertIn("map.easeTo({pitch:", html)

    def test_traffic_map_preserves_operator_camera_across_refresh(self):
        server = PresentationServer(
            world=self.world,
            host="127.0.0.1",
            port=0,
            runtime_metadata=lambda: {},
        )
        server.start()
        self.addCleanup(server.stop)

        with urlopen(f"http://127.0.0.1:{server.bound_port}/traffic", timeout=2) as response:
            html = response.read().decode("utf-8")

        self.assertIn("sessionStorage.setItem(VIEW_KEY", html)
        self.assertIn("function savedCamera()", html)
        self.assertIn("map.jumpTo(saved)", html)
        self.assertIn("map.on('moveend'", html)
        self.assertIn("saveCamera()", html)
        self.assertNotIn("if(!geoView||scopeChanged)geoView=[...scopeBounds]", html)

    def test_traffic_map_motion_redraws_overlay_without_rebuilding_list_until_move_end(self):
        server = PresentationServer(
            world=self.world,
            host="127.0.0.1",
            port=0,
            runtime_metadata=lambda: {},
        )
        server.start()
        self.addCleanup(server.stop)

        with urlopen(f"http://127.0.0.1:{server.bound_port}/traffic", timeout=2) as response:
            html = response.read().decode("utf-8")

        self.assertIn("map.on('move',()=>scheduleDraw(false))", html)
        self.assertIn("map.on('moveend',()=>{syncGeoView();saveCamera();draw();populate()})", html)
        self.assertNotIn("pointermove", html)
        self.assertNotIn("{list:false}", html)
    def test_traffic_hmi_exposes_viewport_operational_picture_without_claiming_corroboration(self):
        server = PresentationServer(
            world=self.world,
            host="127.0.0.1",
            port=0,
            runtime_metadata=lambda: {},
        )
        server.start()
        self.addCleanup(server.stop)

        with urlopen(f"http://127.0.0.1:{server.bound_port}/traffic", timeout=2) as response:
            html = response.read().decode("utf-8")

        self.assertIn("VIEWPORT // OPERATIONAL PICTURE", html)
        self.assertIn("function populateViewportIntel(", html)
        self.assertIn("attention order is rule-based presentation, not confidence or independent corroboration", html)
        self.assertIn("function eventAttention(", html)
        self.assertIn("function eventKind(", html)

    def test_traffic_map_encodes_event_effect_and_flow_detail_on_map(self):
        server = PresentationServer(
            world=self.world,
            host="127.0.0.1",
            port=0,
            runtime_metadata=lambda: {},
        )
        server.start()
        self.addCleanup(server.stop)

        with urlopen(f"http://127.0.0.1:{server.bound_port}/traffic", timeout=2) as response:
            html = response.read().decode("utf-8")

        self.assertIn("function markerNode(", html)
        self.assertIn("flow-label", html)
        self.assertIn("current_speed_mph", html)
        self.assertIn("free_flow_speed_mph", html)
        self.assertIn("road-label", html)


    def test_traffic_map_contains_wheel_interaction_inside_map_boundary(self):
        server = PresentationServer(
            world=self.world, host="127.0.0.1", port=0, runtime_metadata=lambda: {},
        )
        server.start()
        self.addCleanup(server.stop)

        with urlopen(f"http://127.0.0.1:{server.bound_port}/traffic", timeout=2) as response:
            html = response.read().decode("utf-8")

        self.assertIn('id="map-wrap"', html)
        self.assertIn("overscroll-behavior:none", html)
        self.assertIn("map.getCanvasContainer()", html)
        self.assertIn("wheelSurface.addEventListener('wheel'", html)
        self.assertIn("$('map-wrap').addEventListener('wheel'", html)
        self.assertIn("e.preventDefault();e.stopPropagation()", html)
        self.assertNotIn("zoomAt(e.deltaY", html)

    def test_traffic_map_has_maplibre_raster_osm_reference_basemap(self):
        server = PresentationServer(
            world=self.world, host="127.0.0.1", port=0, runtime_metadata=lambda: {},
        )
        server.start()
        self.addCleanup(server.stop)

        with urlopen(f"http://127.0.0.1:{server.bound_port}/traffic", timeout=2) as response:
            html = response.read().decode("utf-8")

        self.assertIn('/static/maplibre/maplibre-gl.css', html)
        self.assertIn('/static/maplibre/maplibre-gl.js', html)
        self.assertIn('id="l-detail-base"', html)
        self.assertIn("function mapStyle()", html)
        self.assertIn("type:'raster'", html)
        self.assertIn("https://tile.openstreetmap.org/{z}/{x}/{y}.png", html)
        self.assertIn("function applyDetailVisibility()", html)
        self.assertIn("© OpenStreetMap contributors", html)
        self.assertIn("not canonical WorldState or evidence", html)

    def test_traffic_overlay_projection_delegates_geographic_camera_math_to_map_engine(self):
        server = PresentationServer(
            world=self.world, host="127.0.0.1", port=0, runtime_metadata=lambda: {},
        )
        server.start()
        self.addCleanup(server.stop)

        with urlopen(f"http://127.0.0.1:{server.bound_port}/traffic", timeout=2) as response:
            html = response.read().decode("utf-8")

        self.assertIn("map.project([lon,lat])", html)
        self.assertIn("setOverlayViewBox()", html)
        self.assertIn("map.on('resize',()=>scheduleDraw(false))", html)
        self.assertNotIn("function mercY(lat)", html)
        self.assertNotIn("function tileXY(lon,lat,z)", html)
        self.assertNotIn("sx=displayW", html)

    def test_traffic_maplibre_runtime_contract_is_local_engine_with_browser_direct_tiles(self):
        server = PresentationServer(
            world=self.world, host="127.0.0.1", port=0, runtime_metadata=lambda: {},
        )
        server.start()
        self.addCleanup(server.stop)

        with urlopen(f"http://127.0.0.1:{server.bound_port}/traffic", timeout=2) as response:
            html = response.read().decode("utf-8")
            csp = response.headers.get("Content-Security-Policy")
            referrer_policy = response.headers.get("Referrer-Policy")

        self.assertIn("MapLibre GL JS is a locally served rendering engine", html)
        self.assertIn("worker-src blob:", csp)
        self.assertIn("child-src blob:", csp)
        self.assertIn("connect-src 'self' https://tile.openstreetmap.org", csp)
        self.assertEqual(referrer_policy, "strict-origin-when-cross-origin")
        self.assertNotIn("unpkg.com", html)
        self.assertNotIn("cdn.jsdelivr.net", html)


    def test_page_uses_text_content_for_source_derived_values(self):
        server = PresentationServer(
            world=self.world,
            host="127.0.0.1",
            port=0,
            runtime_metadata=lambda: {},
        )
        server.start()
        self.addCleanup(server.stop)

        with urlopen(f"http://127.0.0.1:{server.bound_port}/traffic", timeout=2) as response:
            html = response.read().decode("utf-8")

        self.assertIn("textContent", html)
        self.assertIn("strong.textContent=String(title)", html)
        self.assertNotIn("innerHTML", html)


if __name__ == "__main__":
    unittest.main()
