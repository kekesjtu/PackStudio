"""One PACK launch route and a common execution/evidence contract."""

import hashlib
import json
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import BadZipFile

from lxml import etree

from tools.floscript.des import read_des
from tools.floscript.environment import INSTALLATION, paths, prepare_environment
from tools.floscript.script import files, normalize, replay_script, validate, write_xml


def fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _prepare(root, source, directory, installation, copy_materials):
    directory = directory.resolve()
    if (directory / "replay.xml").exists():
        raise FileExistsError("script already prepared; use a new directory")
    root = normalize(root, source.resolve(), directory)
    _, outputs = files(root, directory)
    write_xml(root, directory / "replay.xml")
    validate(directory / "replay.xml", installation)
    prepare_environment(installation, directory, copy_materials=copy_materials)
    for _, path in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
    return directory


def prepare_replay(
    installation: Path, cases: list[dict], directory: Path, *, copy_materials: bool = True
) -> Path:
    """Prepare case commands and DES/FloXML saves without launching PACK."""
    directory = directory.resolve()
    return _prepare(
        replay_script(cases, directory),
        directory / "replay.xml",
        directory,
        installation,
        copy_materials,
    )


def _launch(directory: Path, installation: Path, timeout: int) -> dict:
    command = [
        str(paths(installation)["powershell"]),
        "-NoProfile",
        "-NonInteractive",
        "-File",
        str(directory / "run_pack.ps1"),
        "-Installation",
        str(installation),
        "-Directory",
        str(directory),
        "-TimeoutSeconds",
        str(timeout),
    ]
    # Hide the PowerShell host too. PACK itself is hidden by run_pack.ps1.
    with subprocess.Popen(
        command,
        cwd=directory,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW,
    ) as process:
        try:
            stdout, stderr = process.communicate(timeout=timeout + 30)
        except subprocess.TimeoutExpired:
            subprocess.run(
                ["taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True,
                check=False,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            process.kill()
            process.communicate(timeout=10)
            return {"exit_code": "timeout", "errors": ["PowerShell launcher timed out"]}
    (directory / "launcher-stdout.txt").write_bytes(stdout)
    (directory / "launcher-stderr.txt").write_bytes(stderr)
    try:
        result = json.loads((directory / "process.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        detail = stderr.decode("utf-8", errors="replace").strip()
        return {
            "exit_code": None,
            "errors": [f"missing or invalid process result: {exc}; launcher: {detail}"],
        }
    if process.returncode != 0 and not result.get("errors") and result.get("exit_code") == 0:
        result["errors"] = [f"PowerShell launcher exited with {process.returncode}"]
    return result


def _log_errors(directory: Path) -> list[str]:
    errors = []
    logs = list((directory / "LogFiles").glob("*.xml"))
    if not logs:
        errors.append("native XML logs missing")
    for path in logs:
        try:
            for message in ET.parse(path).getroot().iter("message"):
                value = message.get("text", "")
                if "ERROR" in value.upper():
                    errors.append(value)
        except (OSError, ET.ParseError) as exc:
            errors.append(f"invalid native log {path.name}: {exc}")
    return errors


def execute(directory: Path, installation: Path = INSTALLATION, *, timeout: int = 60) -> dict:
    """Execute a prepared run once, retaining reports even on native failure."""
    if not isinstance(timeout, int) or not 1 <= timeout <= 86400:
        raise ValueError("timeout must be an integer between 1 and 86400 seconds")
    directory, installation = directory.resolve(), installation.resolve()
    if any((directory / name).exists() for name in ("process.json", "run.json")):
        raise FileExistsError("run already executed; use a new directory")
    runtime = json.loads((directory / "runtime.json").read_text(encoding="utf-8"))
    if (
        not isinstance(runtime, dict)
        or not isinstance(runtime.get("installation"), str)
        or not isinstance(runtime.get("copy_materials"), bool)
    ):
        raise ValueError("invalid prepared runtime metadata")
    if Path(runtime["installation"]) != installation:
        raise ValueError("installation differs from the prepared runtime")
    validate(directory / "replay.xml", installation)
    root = normalize(
        ET.parse(directory / "replay.xml").getroot(), directory / "replay.xml", directory
    )
    write_xml(root, directory / "replay.xml")
    inputs, outputs = files(root, directory)
    if fingerprint(directory / "run_pack.ps1") != fingerprint(
        Path(__file__).with_name("run_pack.ps1")
    ):
        raise ValueError("prepared launcher differs from the current tool; prepare a new run")
    result = {
        "format_version": 1,
        "exit_code": None,
        "seconds": 0,
        "errors": [],
        "launcher": "PowerShell Start-Process -WindowStyle Hidden",
        "powershell": str(paths(installation)["powershell"]),
        "launcher_file": "run_pack.ps1",
        "launcher_sha256": fingerprint(directory / "run_pack.ps1"),
        "script_sha256": fingerprint(directory / "replay.xml"),
        "executable": str(paths(installation)["executable"]),
        "executable_sha256": fingerprint(paths(installation)["executable"]),
        "binary_sha256": {
            name: fingerprint(installation / "WinXP/bin" / name)
            for name in ("flopackrealise.dll", "flopackfloxmlhandling.dll", "flopackmaterials.dll")
        },
        "inputs": {str(path): fingerprint(path) for path in inputs},
        "exports": {},
        "outputs": [],
        "timeout_seconds": timeout,
        "copy_materials": runtime["copy_materials"],
        "checks": {"script_schema": True, "outputs": False, "floxml_schema": False},
    }
    try:
        result.update(_launch(directory, installation, timeout))
    except (OSError, subprocess.SubprocessError) as exc:
        result["errors"].append(f"launcher failure: {exc}")
    result["errors"].extend(_log_errors(directory))
    for kind, path in outputs:
        try:
            if not path.is_file() or path.stat().st_size == 0:
                raise ValueError("missing or empty output")
            if kind == "export_floxml":
                validate(path, installation, floxml=True)
                result["exports"][path.stem] = fingerprint(path)
            else:
                read_des(path)
            result["outputs"].append(
                {
                    "kind": kind,
                    "path": str(path),
                    "bytes": path.stat().st_size,
                    "sha256": fingerprint(path),
                }
            )
        except (OSError, ValueError, BadZipFile, etree.Error) as exc:
            result["errors"].append(f"invalid {kind} output {path}: {exc}")
    result["checks"]["outputs"] = len(result["outputs"]) == len(outputs)
    result["checks"]["floxml_schema"] = len(result["exports"]) == sum(
        kind == "export_floxml" for kind, _ in outputs
    )
    if result["exit_code"] == "timeout":
        result["status"] = "timed_out"
    elif result["exit_code"] == 0 and not result["errors"]:
        result["status"] = "success"
    else:
        result["status"] = "failed"
    (directory / "run.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
    )
    return result


def run_script(
    source: Path,
    directory: Path,
    installation: Path = INSTALLATION,
    *,
    timeout: int = 60,
    copy_materials: bool = True,
) -> dict:
    if directory.exists():
        raise FileExistsError("output directory already exists; use a new directory")
    validate(source, installation)
    directory = _prepare(
        ET.parse(source).getroot(), source, directory, installation, copy_materials
    )
    return execute(directory, installation, timeout=timeout)


def replay(
    installation: Path,
    cases: list[dict],
    directory: Path,
    *,
    timeout: int = 60,
    copy_materials: bool = True,
) -> dict:
    prepare_replay(installation, cases, directory, copy_materials=copy_materials)
    return execute(directory, installation, timeout=timeout)
