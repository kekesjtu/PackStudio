"""Portable per-point artifacts and compact native provenance."""

import json
import shutil
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from lxml import etree

from tools.floscript.environment import INSTALLATION
from tools.floscript.script import validate as validate_xml
from tools.floscript.script import write_xml
from tools.pack_sweep.archive import digest

VALIDATOR = '''"""Validate this native reference point from the repository environment."""
from pathlib import Path
import sys

point = Path(__file__).resolve().parent
repository = next(p for p in point.parents if (p / "tools/pack_sweep").is_dir())
sys.path.insert(0, str(repository))
from tools.pack_sweep.__main__ import main
raise SystemExit(main(["validate", "--point", str(point)]))
'''


def dump(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def point_payload(point):
    commands = []
    for text in point.commands:
        element = ET.fromstring(text)
        if element.tag == "load_des":
            if point.input_des is None:
                raise ValueError(f"load_des requires a declared input: {point.key}")
            element.set("filename", "input.des")
        commands.append(ET.tostring(element, encoding="unicode"))
    payload = {
        "template": point.template,
        "id": point.id,
        "origin": point.origin,
        "commands": commands,
        "request": point.request,
        "metadata": point.metadata,
    }
    if point.input_des:
        import hashlib

        with ZipFile(point.input_des) as archive:
            payload["input_members"] = {
                n: hashlib.sha256(archive.read(n)).hexdigest() for n in archive.namelist()
            }
    return payload


def write_point(point, destination, runtime, token, run, installation=INSTALLATION):
    destination.mkdir(parents=True, exist_ok=True)
    payload = point_payload(point)
    dump(destination / "case.json", payload)
    root = ET.Element("flopack_xml_log_file", version="1.0")
    root.extend(ET.fromstring(c) for c in payload["commands"])
    ET.SubElement(root, "save_des", filename="model.des")
    ET.SubElement(root, "export_floxml", filename="model.xml")
    ET.SubElement(root, "quit")
    write_xml(root, destination / "script.xml")
    for extension in (".xml", ".des"):
        shutil.copy2(runtime / (token + extension), destination / ("model" + extension))
    if point.input_des:
        shutil.copy2(point.input_des, destination / "input.des")
    (destination / "validate.py").write_text(VALIDATOR, encoding="utf-8")
    names = ["model.xml", "model.des", "case.json", "script.xml"]
    if point.input_des:
        names.append("input.des")
    provenance = {
        k: run[k]
        for k in (
            "status",
            "checks",
            "file_version",
            "executable_sha256",
            "binary_sha256",
            "launcher_sha256",
        )
    }
    provenance.update(
        batch_script_sha256=run["script_sha256"],
        native_case_id=token,
        files={name: digest(destination / name) for name in names},
    )
    schema_error = None
    try:
        validate_xml(destination / "model.xml", installation, floxml=True)
    except etree.DocumentInvalid as error:
        if point.origin != "legacy":
            raise
        schema_error = str(error)
    provenance.update(
        status="success",
        batch_status=run["status"],
        native_schema_error=schema_error,
        checks={"script_schema": True, "outputs": True, "floxml_schema": schema_error is None},
    )
    dump(destination / "native_run.json", provenance)


def write_indexes(root, points, snapshot):
    families = sorted({p.template for p in points})
    dump(
        root / "index.json",
        {
            "schema": "packstudio.reference-tree/v1",
            "snapshot": snapshot,
            "templates": families,
            "points": ["template/" + p.key for p in points],
        },
    )
    for family in families:
        members = [p for p in points if p.template == family]
        variations = [
            {
                "variation_id": p.id,
                **p.metadata,
                "artifacts": {"model": p.id + "/model.xml", "script": p.id + "/script.xml"},
            }
            for p in members
            if p.origin == "legacy" and "kind" in p.metadata
        ]
        dump(
            root / "template" / family / "index.json",
            {
                "template_id": family,
                "baseline": {"model": "baseline/model.xml"},
                "points": [p.id for p in members],
                "variations": variations,
            },
        )
