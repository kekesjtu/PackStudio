"""Optional native FloSCRIPT replay, with isolated config and hidden Windows process."""

import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from xml.etree import ElementTree as ET

import pefile


def fingerprint(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(installation: Path, cases: list[dict], directory: Path):
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    config = directory / "config"
    config.mkdir(exist_ok=True)
    for path in (installation / "config").iterdir():
        if path.is_file():
            shutil.copy2(path, config / path.name)
    central = directory / "central"
    shutil.copytree(
        installation / "flocentral/flopack",
        central / "flopack",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("Library"),
    )
    (central / "flopack/Library").mkdir(exist_ok=True)
    user = directory / "user"
    user.mkdir(exist_ok=True)
    script = ET.Element("flopack_xml_log_file", version="1.0")
    for case in cases:
        if (directory / f"{case['id']}.xml").exists():
            raise ValueError("native replay already contains exports; use a new directory")
        for command in case["commands"]:
            script.append(ET.fromstring(command))
        ET.SubElement(script, "save_des", filename=str(directory / f"{case['id']}.des"))
        ET.SubElement(script, "export_floxml", filename=str(directory / f"{case['id']}.xml"))
    ET.SubElement(script, "quit")
    script_path = directory / "replay.xml"
    ET.ElementTree(script).write(script_path, encoding="utf-8", xml_declaration=True)
    env = os.environ.copy()
    paths = {
        "FLO_ROOT": installation,
        "FLOPRODUCTDIR": installation / "WinXP",
        "FLO_PATH": installation / "WinXP/bin",
        "FLO_LIBPATH": installation / "WinXP/lib",
        "FLOSCRIPTSCHEMA": installation / "WinXP/lib",
        "FLOPRODUCTCONFIG": config,
        "FLOTRANSLATIONS": config,
        "FLOCENTRALDIR": central,
        "FLOUSERDIR": user,
        "QT_PLUGIN_PATH": installation / "WinXP/64lib/plugins",
        "QT_QPA_PLATFORM_PLUGIN_PATH": installation / "WinXP/64lib/plugins/platforms",
    }
    env.update({key: str(path) for key, path in paths.items()})
    env["PATH"] = (
        str(installation / "WinXP/bin")
        + os.pathsep
        + str(installation / "WinXP/64lib")
        + os.pathsep
        + env["PATH"]
    )
    executable = installation / "WinXP/bin/flopack.exe"
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = 0
    started = time.monotonic()
    with (
        (directory / "stdout.txt").open("w") as stdout,
        (directory / "stderr.txt").open("w") as stderr,
    ):
        process = subprocess.Popen(
            [str(executable), "-f", str(script_path)],
            cwd=directory,
            env=env,
            stdout=stdout,
            stderr=stderr,
            startupinfo=startup,
        )
        try:
            code = process.wait(timeout=55)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
            code = "timeout"
    result = {
        "exit_code": code,
        "seconds": time.monotonic() - started,
        "executable": str(executable),
        "executable_sha256": fingerprint(executable),
        "binary_sha256": {
            name: fingerprint(installation / "WinXP/bin" / name)
            for name in ["flopackrealise.dll", "flopackfloxmlhandling.dll", "flopackmaterials.dll"]
        },
        "script_sha256": fingerprint(script_path),
        "exports": {
            case["id"]: fingerprint(directory / f"{case['id']}.xml")
            for case in cases
            if (directory / f"{case['id']}.xml").exists()
        },
    }
    binary = pefile.PE(str(executable))
    result["file_version"] = next(
        table.entries[b"FileVersion"].decode()
        for group in binary.FileInfo
        for item in group
        for table in getattr(item, "StringTable", [])
        if b"FileVersion" in table.entries
    )
    result["errors"] = [
        element.get("text")
        for path in (directory / "LogFiles").glob("*.xml")
        for element in ET.parse(path).getroot().iter("message")
        if "ERROR" in element.get("text", "")
    ]
    (directory / "run.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
