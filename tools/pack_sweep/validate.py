"""Point-level native provenance, XSD and optional public-model validation."""

import json
from pathlib import Path

from lxml import etree

from tools.floscript.des import read_des
from tools.floscript.environment import INSTALLATION
from tools.floscript.script import validate as validate_xml
from tools.pack_sweep.archive import digest
from tools.pack_sweep.compare import compare_model


def validate_point(directory: Path, installation: Path = INSTALLATION) -> dict:
    case = json.loads((directory / "case.json").read_text(encoding="utf-8"))
    provenance = json.loads((directory / "native_run.json").read_text(encoding="utf-8"))
    checks = provenance["checks"]
    if provenance["status"] != "success" or not checks["script_schema"] or not checks["outputs"]:
        raise ValueError(f"native execution failed: {directory}")
    for name, expected in provenance["files"].items():
        if digest(directory / name) != expected:
            raise ValueError(f"native output fingerprint differs: {directory / name}")
    validate_xml(directory / "script.xml", installation)
    schema_error = None
    try:
        validate_xml(directory / "model.xml", installation, floxml=True)
    except etree.DocumentInvalid as error:
        if case["origin"] != "legacy" or not provenance.get("native_schema_error"):
            raise
        schema_error = str(error)
    if (schema_error is None) != checks["floxml_schema"]:
        raise ValueError("schema result differs from captured native provenance")
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
    if case.get("request") is not None:
        result["public_model"] = compare_model(directory / "model.xml", case["request"])
    else:
        result["validation_scope"] = "native export, XSD, DES readback and output fingerprints"
    if schema_error:
        result.update(status="native_schema_error", floxml_xsd="failed", error=schema_error)
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
        if not path.is_relative_to(root.resolve()) or digest(path) != record["sha256"]:
            raise ValueError(f"screenshot fingerprint differs: {record['path']}")
    errors = sum(r["status"] == "native_schema_error" for r in results)
    return {
        "status": "passed_with_native_schema_errors" if errors else "passed",
        "native_schema_errors": errors,
        "point_count": len(results),
        "screenshot_count": len(screenshots),
        "points": results,
    }
