"""Verify sealed evidence integrity and an independently rerun offline result directory."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from tools.floxml_validation.cases import ROOT
from tools.floxml_validation.native import fingerprint


def verify(delivery: Path, replay_output: Path):
    summary_path = delivery / "results.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    replay = json.loads((replay_output / "results.json").read_text(encoding="utf-8"))
    bundle = delivery / "evidence.zip"
    if fingerprint(bundle) != summary["evidence_sha256"]:
        raise ValueError("evidence archive fingerprint mismatch")
    source_line_endings = []
    for name, digest in summary["source_sha256"].items():
        if fingerprint(ROOT / name) != digest:
            normalized = hashlib.sha256(
                (ROOT / name).read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest()
            if normalized != summary.get("source_normalized_sha256", {}).get(name):
                raise ValueError(f"source version mismatch: {name}")
            source_line_endings.append(name)
    for name, digest in summary["contract_sha256"].items():
        if fingerprint(ROOT / "output_format/floxml" / name) != digest:
            raise ValueError(f"schema version mismatch: {name}")
    with zipfile.ZipFile(bundle) as archive:
        if archive.testzip() is not None:
            raise ValueError("corrupt evidence archive")
    expected = {c["id"]: c for c in summary["cases"]}
    actual = {c["id"]: c for c in replay["cases"]}
    if expected.keys() != actual.keys():
        raise ValueError("offline replay case coverage mismatch")
    checks = 0
    for identifier, before in expected.items():
        after = actual[identifier]
        for key in ("status", "native_sha256", "input_source_sha256", "request"):
            if before[key] != after[key]:
                raise ValueError(f"offline replay input/status mismatch: {identifier}/{key}")
        if before["status"] == "compared":
            if before["export_sha256"] != after["export_sha256"]:
                raise ValueError(f"export bytes changed: {identifier}")
            for key in ("normalized", "raw", "difference_count"):
                if before[key] != after[key]:
                    raise ValueError(f"offline physical metrics changed: {identifier}/{key}")
            for key in ("pack_power_w", "packstudio_power_w"):
                if before["power"][key] != after["power"][key]:
                    raise ValueError(f"offline power changed: {identifier}/{key}")
            checks += 1
        elif before["error"] != after["error"]:
            raise ValueError(f"generation rejection changed: {identifier}")
    result = {
        "status": "verified",
        "case_count": len(expected),
        "identical_export_bytes_and_physical_metrics": checks,
        "matching_known_rejections": len(expected) - checks,
        "results_sha256": fingerprint(summary_path),
        "evidence_sha256": fingerprint(bundle),
        "replay_results_sha256": fingerprint(replay_output / "results.json"),
        "source_and_schema_fingerprints_verified": True,
        "source_line_ending_differences": source_line_endings,
        "source_policy": "Raw file hashes retained; source text may match the LF-normalized hash. "
        "Schemas and evidence always require byte-identical hashes.",
        "note": "Offline replay performs no PACK execution; metrics equality is repeatability, "
        "not proof of thermal accuracy.",
    }
    (delivery / "replay-check.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8", newline="\n"
    )
    print(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delivery", type=Path, default=ROOT / "docs/validation/floxml")
    parser.add_argument("--replay-output", type=Path, required=True)
    args = parser.parse_args()
    verify(args.delivery, args.replay_output)


if __name__ == "__main__":
    main()
