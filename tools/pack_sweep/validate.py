"""Point-level native provenance, XSD and optional public-model validation."""

import json
from collections import Counter, defaultdict
from pathlib import Path

from tools.floscript.des import read_des
from tools.floscript.environment import INSTALLATION
from tools.floscript.script import validate as validate_xml
from tools.pack_sweep.compare import compare_model


def validate_point(
    directory: Path, installation: Path = INSTALLATION, *, reference_root: Path | None = None,
) -> dict:
    case = json.loads((directory / "case.json").read_text(encoding="utf-8"))
    provenance = json.loads((directory / "native_run.json").read_text(encoding="utf-8"))
    checks = provenance["checks"]
    if provenance["status"] != "success" or not checks["script_schema"] or not checks["outputs"]:
        raise ValueError(f"native execution failed: {directory}")
    validate_xml(directory / "script.xml", installation)
    validate_xml(directory / "model.xml", installation, floxml=True)
    parameters = read_des(directory / "model.des")
    if not parameters:
        raise ValueError(f"empty native DES: {directory}")
    result = {
        "template": case["template"],
        "point": case["id"],
        "status": "passed",
        "script_xsd": "passed",
        "floxml_xsd": "passed",
        "provenance": "passed",
        "des_parameter_count": len(parameters),
    }
    metadata = case["metadata"]
    if expected := metadata.get("expected_des"):
        if any(parameters.get(k) != value for k, value in expected.items()):
            raise ValueError(f"DES readback differs from field assertions: {directory}")
        result["des_assertions"] = expected
    if reference_root is not None and "comparison_baseline" in metadata:
        package = reference_root / "packages" / case["template"]
        baseline = (reference_root / metadata["comparison_baseline"]).resolve()
        if not baseline.is_relative_to(package) or not (baseline / "case.json").is_file():
            raise ValueError(f"invalid comparison baseline: {directory}")
        if "expected_des_changes" in metadata:
            previous = read_des(baseline / "model.des")
            changed = {
                k: parameters.get(k)
                for k in previous.keys() | parameters.keys()
                if previous.get(k) != parameters.get(k)
            }
            if changed != metadata["expected_des_changes"]:
                raise ValueError(
                    f"DES differential differs from field assertions: {directory}: {changed}"
                )
            result["des_changes"] = changed
    if case.get("request") is not None:
        result["public_model"] = compare_model(directory / "model.xml", case["request"])
    else:
        result["validation_scope"] = "native export, XSD and DES readback"
    return result


def validate_tree(root: Path, installation: Path = INSTALLATION) -> dict:
    root = root.resolve()
    index = json.loads((root / "index.json").read_text(encoding="utf-8"))
    if index["schema"] != "packstudio.reference-tree/v1":
        raise ValueError("unsupported reference index")
    if len(set(index["points"])) != len(index["points"]):
        raise ValueError("duplicate point in reference index")
    results = []
    packages = set()
    categories = Counter()
    parameter_values = defaultdict(set)
    for relative in index["points"]:
        point = (root / relative).resolve()
        parts = relative.split("/")
        if (
            len(parts) < 4 or parts[0] != "packages"
            or not point.is_relative_to(root / "packages" / parts[1])
        ):
            raise ValueError(f"invalid indexed sample path: {relative}")
        report = validate_point(point, installation, reference_root=root)
        if (report["point"], report["template"]) != (relative, parts[1]):
            raise ValueError(f"indexed sample identity differs: {relative}")
        packages.add(parts[1])
        categories[parts[2]] += 1
        if parts[2] == "parameters":
            metadata = json.loads((point / "case.json").read_text(encoding="utf-8"))["metadata"]
            target = metadata["target"]
            group = parameter_values[point.parent]
            if target["value"] != target["baseline"]:
                group.add(target["value"])
        results.append(report)
    if not results or packages != set(index["packages"]):
        raise ValueError("indexed packages differ from the packages with samples")
    coverage_gaps = [
        {"parameter": group.relative_to(root).as_posix(), "point_count": len(values)}
        for group, values in sorted(parameter_values.items())
        if len(values) < 3
    ]
    screenshots = json.loads((root / "screenshots.json").read_text(encoding="utf-8"))
    for record in screenshots:
        relative = Path(record["path"])
        parts = relative.parts
        path = (root / relative).resolve()
        if (
            len(parts) < 4 or parts[0] != "packages" or parts[1] not in packages
            or parts[2] != "screenshots"
            or not path.is_relative_to(root / "packages" / parts[1] / "screenshots")
            or not path.is_file()
        ):
            raise ValueError(f"invalid indexed screenshot: {relative}")
    return {
        "status": "incomplete" if coverage_gaps else "passed",
        "point_count": len(results),
        "screenshot_count": len(screenshots),
        "categories": dict(categories),
        "coverage_gaps": coverage_gaps,
        "points": results,
    }
