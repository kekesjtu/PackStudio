"""Two-stage native replay with DES readback and isolated custom materials."""

import json
import zipfile
from math import isclose
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.floxml_validation.native import fingerprint, replay


def read_des(path):
    with zipfile.ZipFile(path) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".des"))
        return dict(
            line.split("|", 1) for line in archive.read(name).decode().splitlines() if "|" in line
        )


def _prepare_input(case, directory, baselines):
    changes = case.get("des_changes")
    if changes is None:
        return
    values = read_des(baselines / f"fresh-{case['template']}.des")
    values.update(changes)
    path = directory / f"{case['id']}-input.des"
    directory.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(path.name, "\n".join(f"{k}|{v}" for k, v in values.items()) + "\n")
    case["commands"] = [ET.tostring(ET.Element("load_des", filename=str(path)), encoding="unicode")]
    if material := case.get("native_custom_material"):
        commands = ['<create_material group_name="Metals"/>']
        for prop, value in [
            ("name", "AuditMaterial"),
            ("conductivity", material.conductivity.x),
            ("density", material.density),
            ("specificHeat", material.specific_heat),
        ]:
            command = ET.Element("modify_material", property_name=prop, new_value=str(value))
            ET.SubElement(
                command, "material_name", name="Material" if prop == "name" else "AuditMaterial"
            )
            commands.append(ET.tostring(command, encoding="unicode"))
        case["commands"] = commands + case["commands"]


def suite(installation: Path | None, cases, directory: Path):
    baseline_cases = [c for c in cases if c["kind"] == "fresh_baseline"]
    probes = [
        c for c in cases if c["kind"] != "fresh_baseline" and not c.get("native_custom_material")
    ]
    custom = [c for c in cases if c.get("native_custom_material")]
    runs = []
    for batch, members in [
        ("baselines", baseline_cases),
        ("probes", probes),
        *[(c["id"], [c]) for c in custom],
    ]:
        target = directory / batch
        for case in members:
            case["native"] = target / f"{case['id']}.xml"
            case["source"] = target / "replay.xml"
            if installation:
                _prepare_input(case, target, directory / "baselines")
        if installation:
            result = replay(installation, members, target)
        else:
            result = json.loads((target / "run.json").read_text(encoding="utf-8"))
        runs.append(result)
        if result["errors"] or result["exit_code"] != 0:
            raise ValueError(f"native replay failed: {batch}: {result}")
        for case in members:
            values = read_des(target / f"{case['id']}.des")
            for key, expected in case.get("des_changes", {}).items():
                if values.get(key) != expected:
                    raise ValueError(f"native input not applied: {case['id']}/{key}")
            expected_values = {
                "qfp-negative": {"ddf": 0.44},
                "qfp-small-height": {"ddf": 0.384},
                "qfp-rectangle": {"D1": 8, "cf": 50},
                "wb-copper-asymmetry": {"tz1": 0.01, "tz6": 0.04},
                "chip-attach-thick": {"tda": 0.2},
                "sop-attach-thick": {"tda": 0.2},
                "qfp-count-33": {"N": 33},
            }.get(case["id"], {})
            for key, expected in expected_values.items():
                if not isclose(float(values[key]), expected, rel_tol=1e-12):
                    raise ValueError(f"native numeric input not applied: {case['id']}/{key}")
            if material := case.get("native_custom_material"):
                files = list((target / "central/flopack/Library").glob("*.mat"))
                record = dict(line.split("|", 1) for line in files[0].read_text().splitlines())
                for key, value in {
                    "conduct": material.conductivity.x,
                    "density": material.density,
                    "specific_heat": material.specific_heat,
                }.items():
                    if not isclose(float(record[key]), value, rel_tol=1e-12):
                        raise ValueError(f"native material not applied: {case['id']}/{key}")
                case["native_material_sha256"] = fingerprint(files[0])
            case["native_des_sha256"] = fingerprint(target / f"{case['id']}.des")
    return {
        "runs": runs,
        "input_readback": "DES selection keys checked; material fields read in XML",
    }
