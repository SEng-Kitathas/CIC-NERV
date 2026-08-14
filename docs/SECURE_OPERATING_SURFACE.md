# Secure Operating Surface

**Status:** 003g Runtime Authority RC4 source candidate. RC7 remains target-verified authority.

Personal CIC is intended to be an operator-owned local system, not a launchpad that silently exports operator context, credentials, or provider access into arbitrary browser pages. Security therefore has two distinct boundaries:

1. **world / mutation authority** — who may alter CIC state; and
2. **operator-surface confidentiality / egress authority** — what local context, credentials, requests, and visual resources may leave the CIC process or browser.

Loopback binding and read-only HTTP methods defend the first boundary well, but they do not by themselves close the second.

## Current RC4 hardening

The presentation server now validates the HTTP `Host` header and accepts only explicit local names (`127.0.0.1` or `localhost`). This closes the classical DNS-rebinding shape in which an attacker-controlled hostname resolves to loopback but retains the hostile hostname in `Host`.

The existing global `Referrer-Policy: strict-origin-when-cross-origin` is intentionally preserved. RC2D-R1 target evidence already proved that `no-referrer` breaks the browser-direct OpenStreetMap standard-tile contract with 403 responses. Reusing the apparently stronger policy here would repeat an assimilated failure. The current policy therefore permits origin-level disclosure to browser-direct reference providers until those resources are locally mediated.

These measures do not turn the current browser-direct OpenStreetMap/Waze references into locally mediated resources. They are transitional controls around the existing architecture.

## Secure Reference Gateway — earned next mechanism

Direct camera/video/reference feeds should enter through a **provider-specific server-side reference gateway**, not through a generic arbitrary-URL proxy. A gateway implementation must earn all of the following before use:

- HTTPS-only provider allowlist;
- explicit host and path families per provider;
- GET/HEAD-only remote methods unless a separate mutation capability is intentionally authorized;
- credentials injected server-side from environment/secret storage and never returned to browser JavaScript, WorldState, logs, exception text, or URLs;
- bounded connect/read timeouts;
- bounded response sizes and accepted content types;
- redirect validation against the same allowlist;
- no forwarding of arbitrary browser cookies, Authorization headers, or request headers;
- source/provenance identity retained separately from CIC authority;
- cache/expiry policy tied to the resource semantics;
- failure represented explicitly rather than replaced by stale or fabricated live imagery.

### HLS/video special case

HLS is not one URL fetch. A local relay must validate and rewrite manifests so every playlist/segment/key URI remains inside the provider policy. A generic `/proxy?url=` endpoint is therefore forbidden. If DriveNC/TravelIQ exposes a lawful public or credentialed stream contract, CIC should implement that contract as a named connector with provider-owned credentials; it must not bypass a login wall or scrape an authenticated web session merely to make a camera appear local.

## Browser-direct references

Browser-direct references remain explicitly non-canonical and opt-in. Their existence must be visible to the operator because they create direct network egress from the browser. As secure local mediation is earned for a source, the browser-direct path should be retired rather than kept as an invisible fallback.

## Remote access is a separate future proposition

Nothing in this candidate authorizes LAN or Internet exposure. If CIC later leaves loopback, authentication, transport security, origin policy, session/capability design, and network segmentation become prerequisite work. A loopback security argument must never be silently reused for a remotely reachable deployment.
