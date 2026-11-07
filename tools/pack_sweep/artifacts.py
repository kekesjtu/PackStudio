"""Portable per-point artifacts and compact native provenance."""

import json
import shutil
from xml.etree import ElementTree as ET

from tools.floscript.environment import INSTALLATION
from tools.floscript.script import validate as validate_xml
from tools.floscript.script import write_xml


def dump(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def point_payload(point, sample_id):
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
        "id": sample_id,
        "origin": point.origin,
        "commands": commands,
        "request": point.request,
        "metadata": point.metadata,
    }
    return payload


def write_point(point, destination, runtime, token, run, installation=INSTALLATION, *, sample_id):
    destination.mkdir(parents=True, exist_ok=True)
    payload = point_payload(point, sample_id)
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
        native_case_id=token,
        files=names,
    )
    validate_xml(destination / "model.xml", installation, floxml=True)
    dump(destination / "native_run.json", provenance)


def write_indexes(root, samples):
    families = sorted({point.template for _, point in samples})
    dump(
        root / "index.json",
        {
            "schema": "packstudio.reference-tree/v1",
            "packages": families,
            "points": [path for path, _ in samples],
        },
    )
    for family in families:
        members = [path for path, point in samples if point.template == family]
        dump(
            root / "packages" / family / "index.json",
            {
                "package": family,
                "baselines": [path for path in members if "/baselines/" in path],
                "points": members,
            },
        )
