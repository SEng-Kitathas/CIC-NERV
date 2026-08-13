# MapLibre runtime vendor slot

Personal CIC uses a **locally served, version-pinned** MapLibre GL JS runtime.
The map engine is presentation execution machinery only; it has no authority over
CIC/NERV world truth.

Pinned dependency identity is stored in `LOCK.json`. The expected upstream release is
MapLibre GL JS `v5.24.0`; its `dist.zip` SHA-256 is verified before any files are
installed. Only these files are admitted:

- `maplibre-gl.js`
- `maplibre-gl.css`
- `LICENSE.txt`

Materialize the vendor runtime with:

```bash
python tools/install-maplibre-vendor.py
```

For an offline/replayable installation, provide an already acquired release archive:

```bash
python tools/install-maplibre-vendor.py --archive /path/to/dist.zip
```

The authored CIC source package intentionally does not pretend third-party binary bytes
are present when they are not. A release/capture intended to be directly runnable must
materialize the pinned runtime first and then pass `tools/verify-source-distribution.py
--require-runtime-vendor`.
