# CSC / PDVER Engineering Lineage

This tree preserves the executable and doctrinal ancestry from which CIC's
engineering assurance plane is being recovered.

Artifact class: **AUTHORED ENGINEERING LINEAGE — NON-RUNTIME**.

It is deliberately tracked in the CIC-NERV source repository so the project
does not retain only abstract lessons while losing the implementation lineage
that earned them.

It is deliberately excluded from the CIC runtime/installable Python package.

Boundary:

```text
CSC / PDVER assurance  --->  CIC source and artifacts     allowed to inspect
CIC runtime            -X->  CSC / PDVER assurance       forbidden dependency
```

The `recovered/` tree is donor evidence, not active CIC assurance authority.
Do not import donor modules into `personal_cic`.  Active CIC-native CSC tooling
must be adapted and self-qualified separately under `tools/assurance/csc/`.

Raw historical ZIP archives are not duplicated here. Their exact archive hashes
and selected-member hashes are recorded in the recovered capsule manifest.
