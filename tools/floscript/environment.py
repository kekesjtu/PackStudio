"""Paths and isolated runtime files for the installed PACK 2504."""

import json
import shutil
from pathlib import Path

INSTALLATION = Path("E:/Program Files/Siemens/SimcenterFlotherm/2504")
POWERSHELL = Path(
    "C:/Users/mydearlong/.cache/codex-runtimes/codex-primary-runtime/"
    "dependencies/native/powershell/pwsh.exe"
)
LAUNCHER = Path(__file__).with_name("run_pack.ps1")


def paths(installation: Path = INSTALLATION) -> dict[str, Path]:
    installation = installation.resolve()
    return {
        "installation": installation,
        "powershell": POWERSHELL,
        "executable": installation / "WinXP/bin/flopack.exe",
        "script_schema": installation / "examples/FloSCRIPT/Schema/FlopackFloSCRIPTSchema.xsd",
        "floxml_schema": installation / "WinXP/PlugIns/XML_PLUGIN_SCHEMA/xmlSchema.xsd",
        "config": installation / "config",
        "central": installation / "flocentral/flopack",
        "platforms": installation / "WinXP/64lib/plugins/platforms",
    }


def check(installation: Path = INSTALLATION) -> dict[str, str]:
    locations = paths(installation)
    missing = [str(path) for path in locations.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("PACK runtime files missing: " + ", ".join(missing))
    return {key: str(value) for key, value in locations.items()}


def prepare_environment(installation: Path, directory: Path, *, copy_materials: bool) -> None:
    check(installation)
    locations = paths(installation)
    # Input DES files may already be present, but a runtime must never be reused.
    reserved = (
        "config",
        "central",
        "user",
        "temp",
        "run_pack.ps1",
        "runtime.json",
        "process.json",
        "run.json",
    )
    if any((directory / name).exists() for name in reserved):
        raise FileExistsError("runtime already prepared; use a new directory")
    directory.mkdir(parents=True, exist_ok=True)
    config = directory / "config"
    config.mkdir()
    for source in locations["config"].iterdir():
        if source.is_file():
            shutil.copy2(source, config / source.name)
    shutil.copytree(
        locations["central"],
        directory / "central/flopack",
        ignore=None if copy_materials else shutil.ignore_patterns("Library"),
    )
    (directory / "central/flopack/Library").mkdir(exist_ok=True)
    (directory / "user").mkdir()
    (directory / "temp").mkdir()
    shutil.copy2(LAUNCHER, directory / LAUNCHER.name)
    (directory / "runtime.json").write_text(
        json.dumps({"installation": str(installation.resolve()), "copy_materials": copy_materials}),
        encoding="utf-8",
    )
