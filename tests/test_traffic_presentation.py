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
    TrafficMessageSignCollectionState,
    TrafficMessageSignObservation,
    TrafficSituationState,
)
from personal_cic.presentation import PresentationServer, build_traffic_projection


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

    def test_local_reference_context_is_hash_bound_and_separate(self):
        payload = build_traffic_projection(self.world)
        context = payload["map_context"]

        self.assertEqual(context["context_state"], "CURRENT")
        self.assertEqual(context["context_url"], "/radar/context.json?sha=" + "a" * 64)
        self.assertEqual(context["provider"], "U.S. Census Bureau TIGERweb")

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

        self.assertIn("PERSONAL CIC // TRAFFIC", html)
        self.assertIn("READ-ONLY", html)
        self.assertIn("/api/v1/traffic", html)
        self.assertIn("id=\"map\"", html)
        self.assertIn("id=\"load-waze\"", html)
        self.assertIn("direct browser egress to Waze", html)
        self.assertNotIn("DRIVENC_API_KEY", html)
        self.assertNotIn("fetch('https://www.drivenc.gov", html)
        self.assertNotIn('fetch("https://www.drivenc.gov', html)
        self.assertNotIn("fetch('https://cmpdinfo", html)
        self.assertNotIn('fetch("https://cmpdinfo', html)
        self.assertIn("connect-src 'self'", csp)
        self.assertIn("frame-src https://embed.waze.com", csp)

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
