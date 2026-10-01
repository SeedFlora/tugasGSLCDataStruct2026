"""Reproduce and validate the group exploration's Bike Sharing inputs.

Usage:
    python prepare_dataset.py          # download if needed, then regenerate outputs
    python prepare_dataset.py --check  # validate all files without network access

Only Python's standard library is required. Paths are relative to this script.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import random
import tempfile
from typing import Dict, List, Optional, Set, Tuple
from urllib.request import Request, urlopen
import zipfile
from datetime import date


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SOURCE_PAGE = "https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset"
SOURCE_ZIP = "https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
ORIGINAL_SHA256 = "e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f"
EXPECTED_ROWS = 17_379
SHUFFLE_SEED = 20261001
QUERY_SEED = 20261002
SIZES = (5_000, 15_000)
HITS_PER_SIZE = 1_000
MISSES_PER_SIZE = 1_000
EXPECTED_COLUMNS = (
    "instant", "dteday", "season", "yr", "mnth", "hr", "holiday",
    "weekday", "workingday", "weathersit", "temp", "atemp", "hum",
    "windspeed", "casual", "registered", "cnt",
)


def sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def source_bytes() -> bytes:
    original_path = DATA / "hour.csv"
    if original_path.is_file():
        existing = original_path.read_bytes()
        if sha256(existing) == ORIGINAL_SHA256:
            return existing
        print("Local hour.csv has the wrong SHA-256; fetching the pinned source again.")

    request = Request(SOURCE_ZIP, headers={"User-Agent": "group-exploration-data-preparer/1.0"})
    with urlopen(request, timeout=60) as response:
        archive_bytes = response.read()
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        matches = [name for name in archive.namelist() if name.rsplit("/", 1)[-1] == "hour.csv"]
        if len(matches) != 1:
            raise ValueError(f"Expected one hour.csv in UCI archive, found {matches!r}")
        original = archive.read(matches[0])
    if sha256(original) != ORIGINAL_SHA256:
        raise ValueError("Downloaded hour.csv does not match the pinned SHA-256; no file was changed")
    return original


def read_records(original: bytes) -> Tuple[bytes, List[Tuple[bytes, Dict[str, str]]]]:
    if sha256(original) != ORIGINAL_SHA256:
        raise ValueError("hour.csv SHA-256 mismatch")
    raw_lines = original.splitlines()
    if len(raw_lines) != EXPECTED_ROWS + 1:
        raise ValueError(f"Expected {EXPECTED_ROWS} physical data lines, found {len(raw_lines) - 1}")
    try:
        reader = csv.DictReader(io.StringIO(original.decode("utf-8-sig"), newline=""))
        if tuple(reader.fieldnames or ()) != EXPECTED_COLUMNS:
            raise ValueError(f"Unexpected hour.csv columns: {reader.fieldnames!r}")
        parsed = list(reader)
    except UnicodeDecodeError as exc:
        raise ValueError("hour.csv is not UTF-8") from exc
    if len(parsed) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} parsed records, found {len(parsed)}")

    keys: Set[Tuple[str, int]] = set()
    for row_number, row in enumerate(parsed, start=2):
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"Malformed CSV at line {row_number}")
        try:
            date.fromisoformat(row["dteday"])
            hour = int(row["hr"])
            count = int(row["cnt"])
            casual = int(row["casual"])
            registered = int(row["registered"])
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid date, hour, or count at line {row_number}") from exc
        if not 0 <= hour <= 23 or min(count, casual, registered) < 0 or count != casual + registered:
            raise ValueError(f"Hour or rental counts invalid at line {row_number}")
        key = (row["dteday"], hour)
        if key in keys:
            raise ValueError(f"Duplicate date-hour key at line {row_number}: {key!r}")
        keys.add(key)
    return raw_lines[0], list(zip(raw_lines[1:], parsed))


def query_bytes(
    inserted: List[Tuple[bytes, Dict[str, str]]],
    held_out: List[Tuple[bytes, Dict[str, str]]],
) -> bytes:
    rng = random.Random(QUERY_SEED)
    hits = rng.sample(inserted, HITS_PER_SIZE)
    misses = rng.sample(held_out, MISSES_PER_SIZE)
    entries = [(row, int(row["cnt"])) for _, row in hits]
    entries.extend((row, -1) for _, row in misses)
    rng.shuffle(entries)
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
    writer.writerow(("dteday", "hr", "expected_cnt"))
    for row, expected in entries:
        writer.writerow((row["dteday"], int(row["hr"]), expected))
    return stream.getvalue().encode("utf-8")


def make_outputs(original: bytes) -> Tuple[Dict[str, bytes], Dict[str, object]]:
    header, records = read_records(original)
    rng = random.Random(SHUFFLE_SEED)
    rng.shuffle(records)
    shuffled = b"\n".join((header, *(line for line, _ in records))) + b"\n"
    outputs = {"hour.csv": original, "hour_shuffled.csv": shuffled}
    checks: Dict[str, object] = {
        "original_rows": EXPECTED_ROWS,
        "unique_date_hour_keys": EXPECTED_ROWS,
        "shuffled_is_exact_row_permutation": True,
        "queries": {},
    }
    for size in SIZES:
        inserted = records[:size]
        held_out = records[size:]
        inserted_keys = {(row["dteday"], int(row["hr"])) for _, row in inserted}
        held_out_keys = {(row["dteday"], int(row["hr"])) for _, row in held_out}
        if len(inserted_keys) != size or inserted_keys & held_out_keys:
            raise ValueError(f"Invalid inserted/held-out partition for n={size}")
        name = f"queries_n{size}.tsv"
        outputs[name] = query_bytes(inserted, held_out)
        checks["queries"][name] = {  # type: ignore[index]
            "inserted_records": size,
            "held_out_records": EXPECTED_ROWS - size,
            "query_rows": HITS_PER_SIZE + MISSES_PER_SIZE,
            "hits": HITS_PER_SIZE,
            "misses": MISSES_PER_SIZE,
            "unique_date_hour_keys": HITS_PER_SIZE + MISSES_PER_SIZE,
            "miss_keys_are_valid_source_rows_outside_first_n": True,
        }

    files = {}
    for name, blob in outputs.items():
        files[name] = {
            "sha256": sha256(blob),
            "bytes": len(blob),
            "data_rows": EXPECTED_ROWS if name.endswith(".csv") else HITS_PER_SIZE + MISSES_PER_SIZE,
        }
    manifest: Dict[str, object] = {
        "source": {
            "title": "Bike Sharing (hourly observations)",
            "repository": "UCI Machine Learning Repository",
            "page": SOURCE_PAGE,
            "archive_url": SOURCE_ZIP,
            "archive_member": "hour.csv",
            "original_hour_csv_sha256": ORIGINAL_SHA256,
            "citation": "Fanaee-T, H. (2013). Bike Sharing [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5W894",
        },
        "license": {
            "name": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
            "url": LICENSE_URL,
            "attribution": "Hadi Fanaee-T, Bike Sharing, UCI Machine Learning Repository (2013)",
            "changes": "hour.csv is unmodified. hour_shuffled.csv reorders complete rows with Python Random(20261001) and normalizes line endings to LF; query TSV files select hit rows from the first n shuffled rows and valid miss rows from the remaining source rows, then shuffle query order with Random(20261002).",
        },
        "recipe": {
            "script": "../prepare_dataset.py",
            "row_shuffle_seed": SHUFFLE_SEED,
            "query_seed_reset_per_size": QUERY_SEED,
            "sizes": list(SIZES),
            "key_fields": ["dteday", "hr"],
            "value_field": "cnt",
            "queries_per_size": HITS_PER_SIZE + MISSES_PER_SIZE,
            "miss_expected_cnt": -1,
            "interpretation": "A miss is a genuine date-hour pair in the original dataset, absent from the first n shuffled rows used to build that experiment's index.",
        },
        "files": files,
        "checks": checks,
    }
    outputs["manifest.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return outputs, manifest


def write_atomic(path: Path, blob: bytes) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    temporary: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=DATA, prefix=".prepare-", delete=False) as stream:
            temporary = stream.name
            stream.write(blob)
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def verify(outputs: Dict[str, bytes]) -> None:
    problems = []
    for name, expected in outputs.items():
        path = DATA / name
        if not path.is_file():
            problems.append(f"missing: {path}")
            continue
        actual = path.read_bytes()
        if actual != expected:
            problems.append(f"content mismatch: {path} (SHA-256 {sha256(actual)})")
    if problems:
        raise ValueError("Dataset validation failed:\n" + "\n".join(problems))
    audit_semantics()


def audit_semantics() -> None:
    """Check the generated files by their public key/value meaning, not only hashes."""
    original = (DATA / "hour.csv").read_bytes()
    shuffled = (DATA / "hour_shuffled.csv").read_bytes()
    original_lines = original.splitlines()
    shuffled_lines = shuffled.splitlines()
    if original_lines[0] != shuffled_lines[0] or sorted(original_lines[1:]) != sorted(shuffled_lines[1:]):
        raise ValueError("Shuffled CSV is not an exact permutation of the source rows")

    reader = csv.DictReader(io.StringIO(shuffled.decode("utf-8"), newline=""))
    ordered_rows = list(reader)
    if len(ordered_rows) != EXPECTED_ROWS:
        raise ValueError("Shuffled CSV row count mismatch")
    for size in SIZES:
        indexed = {(row["dteday"], int(row["hr"])): int(row["cnt"]) for row in ordered_rows[:size]}
        held_out = {(row["dteday"], int(row["hr"])) for row in ordered_rows[size:]}
        if len(indexed) != size or len(held_out) != EXPECTED_ROWS - size or set(indexed) & held_out:
            raise ValueError(f"Invalid partition in shuffled CSV for n={size}")
        path = DATA / f"queries_n{size}.tsv"
        query_reader = csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"), newline=""), delimiter="\t")
        if query_reader.fieldnames != ["dteday", "hr", "expected_cnt"]:
            raise ValueError(f"Unexpected query columns in {path}")
        seen: Set[Tuple[str, int]] = set()
        hits = misses = 0
        for row in query_reader:
            key = (row["dteday"], int(row["hr"]))
            expected_count = int(row["expected_cnt"])
            if key in seen:
                raise ValueError(f"Duplicate query key in {path}: {key!r}")
            seen.add(key)
            if key in indexed:
                if expected_count != indexed[key]:
                    raise ValueError(f"Wrong hit answer in {path}: {key!r}")
                hits += 1
            elif key in held_out and expected_count == -1:
                misses += 1
            else:
                raise ValueError(f"Miss key is not held out or has wrong answer in {path}: {key!r}")
        if hits != HITS_PER_SIZE or misses != MISSES_PER_SIZE or len(seen) != HITS_PER_SIZE + MISSES_PER_SIZE:
            raise ValueError(f"Wrong hit/miss counts in {path}: {hits}/{misses}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate the local dataset and manifest without downloading or changing files")
    args = parser.parse_args()
    if args.check:
        original_path = DATA / "hour.csv"
        if not original_path.is_file():
            raise SystemExit(f"Missing {original_path}; run this script without --check first")
        original = original_path.read_bytes()
    else:
        original = source_bytes()
    outputs, manifest = make_outputs(original)
    if args.check:
        verify(outputs)
        print("OK: all four data files and manifest match the pinned source and deterministic recipe.")
    else:
        for name, blob in outputs.items():
            write_atomic(DATA / name, blob)
        verify(outputs)
        print("Prepared and verified:")
        for name, info in manifest["files"].items():  # type: ignore[union-attr]
            print(f"  data/{name}: {info['data_rows']} rows, SHA-256 {info['sha256']}")


if __name__ == "__main__":
    main()
