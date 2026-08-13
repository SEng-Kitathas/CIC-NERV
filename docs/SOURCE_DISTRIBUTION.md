# Source Distribution and Third-Party Runtime Materialization

## Authority

The Personal CIC source tree is configuration-controlled independently from third-party
presentation-runtime bytes. A source archive must never imply that an external runtime
was bundled when it was not.

## MapLibre

RC2D introduced a locally served MapLibre GL JS camera/runtime. The qualified dependency
is pinned in `src/personal_cic/presentation/vendor/maplibre/LOCK.json`. The archive digest
is a supply-chain identity, not world authority.

The authored source tree can be audited without network access. To create a directly
runnable tree, materialize the exact vendor release:

```bash
python tools/install-maplibre-vendor.py
python tools/verify-source-distribution.py --require-runtime-vendor
```

An existing `dist.zip` can be supplied with `--archive` for offline/replayable builds.
The installer verifies the pinned archive size and SHA-256 before extracting only the three admitted
runtime files under explicit size bounds and preserving the upstream license.

## Python dependency policy

`pyproject.toml` declares the supported compatibility range. `requirements-target.lock`
records the directly observed target Python dependency version used by the current Engage
One environment. These are different claims and must not be collapsed.

## Build hygiene

Generated build products, interpreter caches, coverage databases/reports, wheels and
`*.egg-info` metadata are not authored source and must not enter configuration-controlled
source captures.

## Verification scope: source capture vs embodied working tree

A sealed source capture and an embodied editable checkout are different propositions.

`verify-source-distribution.py` therefore has two explicit scopes:

- **source-capture** (default): rejects generated products under project/authored roots;
- **working-tree** (`--working-tree`): tolerates caches, `*.egg-info`, build products and
  similar generated runtime metadata because those files are not members of the sealed
  authored-source proposition.

`.venv/` and other local tool/runtime roots are outside authored-source authority in both
modes. Their existence beside the checkout does not make them source distribution content.

This does **not** weaken capture hygiene. Release/source artifacts are still extracted and
verified in the default strict source-capture scope before embodiment. The working-tree
scope exists only so target verification does not mistake normal interpreter/build residue
for configuration-controlled source.

Constitutional assurance distinction:

> **RUNTIME RESIDUE IS NOT SOURCE CONTENT. SOURCE-CAPTURE HYGIENE IS NOT WORKING-TREE CLEANLINESS.**

## Service-install verification scope

`tools/install-user-service.sh` operates on an embodied editable checkout, not a sealed
source capture. It therefore invokes the source verifier with both:

```bash
--working-tree --require-runtime-vendor
```

The first flag selects the correct artifact class; the second still requires the exact
pinned MapLibre runtime before the service may be installed or started. A strict
source-capture check remains mandatory on extracted/sealed source before target mutation.

This caller-level distinction is configuration-controlled and regression-tested. Fixing a
verifier mode is insufficient if a composed tool silently invokes the wrong mode.

