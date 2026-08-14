# CSC Lineage Recovery Capsule V1

This capsule preserves the recovered CSC/PDVER implementation lineage needed to
reintegrate generalized assurance guarantees into CIC-NERV.

It intentionally separates:
- historical donor evidence,
- latest known CSC SOP/control-surface doctrine,
- a standalone project-agnostic `universal_csc` donor,
- PCMMAD V28/V29 execution/report anchors.

It is **not** a drop-in CIC runtime dependency.

Required boundary:

`CSC -> inspects/verifies CIC`

`CIC runtime -X-> CSC`

The recovered standalone universal engine still contains a few PCMMAD/receiver
residues and therefore requires receiver-independent adaptation and self-
qualification before becoming active CIC assurance tooling.

Raw donor archives are identified by exact SHA-256 in `MANIFEST.json`; they are
not duplicated into this compact capsule.
