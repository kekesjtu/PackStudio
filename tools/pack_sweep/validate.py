"""Point-level native provenance, XSD and optional public-model validation."""

import json
from pathlib import Path

from tools.floscript.des import read_des
from tools.floscript.environment import INSTALLATION
from tools.floscript.script import validate as validate_xml
from tools.pack_sweep.compare import compare_model


def validate_point(directory: Path, installation: Path = INSTALLATION) -> dict:
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
    if case["origin"] == "field_probe":
        metadata = case["metadata"]
        expected = metadata.get("expected_des", {})
        if any(parameters.get(k) != value for k, value in expected.items()):
            raise ValueError(f"DES readback differs from field assertions: {directory}")
        result["des_assertions"] = expected
        if "expected_des_changes" in metadata:
            baseline = (directory.parent / metadata["comparison_baseline"]).resolve()
            if not baseline.is_relative_to(directory.parent.resolve()):
                raise ValueError("field comparison baseline escapes template directory")
            previous = read_des(baseline)
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
    index = json.loads((root / "index.json").read_text(encoding="utf-8"))
    if index["schema"] != "packstudio.reference-tree/v1":
        raise ValueError("unsupported reference index")
    if len(set(index["points"])) != len(index["points"]):
        raise ValueError("duplicate point in reference index")
    results = []
    for relative in index["points"]:
        point = (root / relative).resolve()
        if not point.is_relative_to(root.resolve()):
            raise ValueError("point escapes reference root")
        results.append(validate_point(point, installation))
    screenshots = json.loads((root / "screenshots.json").read_text(encoding="utf-8"))
    for record in screenshots:
        path = (root / record["path"]).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError(f"screenshot path escapes reference root: {record['path']}")
    return {
        "status": "passed",
        "point_count": len(results),
        "screenshot_count": len(screenshots),
        "points": results,
    }
