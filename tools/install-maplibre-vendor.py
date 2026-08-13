#!/usr/bin/env python3
"""Materialize the exact MapLibre runtime pinned by presentation/vendor/maplibre/LOCK.json."""

from __future__ import annotations

from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json
import os
import tempfile
from urllib.request import Request, urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "src/personal_cic/presentation/vendor/maplibre"
LOCK_PATH = VENDOR / "LOCK.json"
MAX_ARCHIVE_BYTES = 32 * 1024 * 1024
MAX_MEMBER_BYTES = 16 * 1024 * 1024


def digest(path: Path) -> str:
    h = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_lock() -> dict:
    data = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    required = {"version", "release_url", "release_archive_sha256", "release_archive_size_bytes", "required_files"}
    missing = sorted(required - data.keys())
    if missing:
        raise SystemExit(f"invalid MapLibre lock; missing {missing}")
    expected = str(data["release_archive_sha256"]).lower()
    if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        raise SystemExit("invalid MapLibre lock archive SHA-256")
    expected_size = data["release_archive_size_bytes"]
    if isinstance(expected_size, bool) or not isinstance(expected_size, int) or not 0 < expected_size <= MAX_ARCHIVE_BYTES:
        raise SystemExit("invalid MapLibre lock archive size")
    files = data["required_files"]
    if not isinstance(files, list) or not files or not all(isinstance(x, str) for x in files):
        raise SystemExit("invalid MapLibre lock required_files")
    if len(files) != len(set(files)):
        raise SystemExit("invalid MapLibre lock required_files contains duplicates")
    if any(Path(name).name != name or name in {".", ".."} for name in files):
        raise SystemExit("invalid MapLibre lock required_files must be basenames")
    return data


def acquire(url: str, destination: Path) -> None:
    request = Request(url, headers={"User-Agent": "Personal-CIC-vendor-materializer/0.3.6"})
    with urlopen(request, timeout=180) as response, destination.open("wb") as output:
        content_length = response.headers.get("Content-Length")
        if content_length is not None:
            try:
                declared = int(content_length)
            except ValueError as exc:
                raise SystemExit("MapLibre response Content-Length is invalid") from exc
            if declared > MAX_ARCHIVE_BYTES:
                raise SystemExit("MapLibre archive exceeds configured acquisition size bound")
        total = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_ARCHIVE_BYTES:
                raise SystemExit("MapLibre archive exceeded configured acquisition size bound")
            output.write(chunk)


def extract_exact(archive: Path, required_files: list[str], destination: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    with zipfile.ZipFile(archive) as zf:
        names = zf.namelist()
        for filename in required_files:
            matches = [name for name in names if name == filename or name.endswith("/" + filename)]
            if len(matches) != 1:
                raise SystemExit(f"expected exactly one {filename!r} in archive, found {matches}")
            info = zf.getinfo(matches[0])
            if info.file_size <= 0:
                raise SystemExit(f"pinned vendor file {filename!r} is empty")
            if info.file_size > MAX_MEMBER_BYTES:
                raise SystemExit(f"pinned vendor file {filename!r} exceeds size bound")
            payload = zf.read(info)
            if len(payload) != info.file_size:
                raise SystemExit(f"pinned vendor file {filename!r} size changed during extraction")
            target = destination / filename
            target.write_bytes(payload)
            hashes[filename] = sha256(payload).hexdigest()
    license_path = destination / "LICENSE.txt"
    if "Redistribution and use in source and binary forms" not in license_path.read_text(
        encoding="utf-8", errors="replace"
    ):
        raise SystemExit("MapLibre license content was not recognized")
    return hashes


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive",
        type=Path,
        help="use an existing pinned dist.zip instead of network acquisition",
    )
    args = parser.parse_args()
    lock = load_lock()

    with tempfile.TemporaryDirectory(prefix="personal-cic-maplibre-") as tmp_name:
        tmp = Path(tmp_name)
        archive = tmp / "dist.zip"
        if args.archive is None:
            acquire(str(lock["release_url"]), archive)
        else:
            source = args.archive.resolve()
            if not source.is_file():
                raise SystemExit(f"archive does not exist: {source}")
            if source.stat().st_size > MAX_ARCHIVE_BYTES:
                raise SystemExit("MapLibre archive exceeds configured acquisition size bound")
            archive.write_bytes(source.read_bytes())

        expected_size = int(lock["release_archive_size_bytes"])
        if archive.stat().st_size != expected_size:
            raise SystemExit(
                f"MapLibre archive size mismatch: expected {expected_size}, got {archive.stat().st_size}"
            )
        actual = digest(archive)
        expected = str(lock["release_archive_sha256"]).lower()
        if actual != expected:
            raise SystemExit(f"MapLibre archive SHA mismatch: expected {expected}, got {actual}")

        stage = tmp / "stage"
        stage.mkdir()
        hashes = extract_exact(archive, list(lock["required_files"]), stage)

        VENDOR.mkdir(parents=True, exist_ok=True)
        for filename in lock["required_files"]:
            source = stage / filename
            temporary = VENDOR / (filename + ".tmp")
            temporary.write_bytes(source.read_bytes())
            os.replace(temporary, VENDOR / filename)

        materialized = {
            "schema_version": 1,
            "dependency": lock.get("dependency"),
            "version": lock["version"],
            "release_archive_sha256": actual,
            "files": hashes,
        }
        temporary = VENDOR / "MATERIALIZED.json.tmp"
        temporary.write_text(json.dumps(materialized, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, VENDOR / "MATERIALIZED.json")

    print(f"PASS: materialized MapLibre GL JS {lock['version']}")
    print(f"archive_sha256={expected}")
    for filename in lock["required_files"]:
        print(f"{filename}={hashes[filename]}")


if __name__ == "__main__":
    main()
