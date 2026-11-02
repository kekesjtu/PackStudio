"""Invoke the shared C# model core from native PACK research tools."""

import json
import subprocess
import tempfile
from datetime import date
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "src/PackStudio.Cli/PackStudio.Cli.csproj"
BINARY = ROOT / "src/PackStudio.Cli/bin/Release/net10.0/PackStudio.Cli.dll"


@cache
def _ensure_build():
    directories = [ROOT / "src/PackStudio.Core", ROOT / "src/PackStudio.Cli"]
    sources = [path for directory in directories for path in directory.rglob("*")
               if path.suffix in {".cs", ".csproj"} and not {"bin", "obj"}.intersection(path.parts)]
    sources += [ROOT / "Directory.Build.props", ROOT / "global.json"]
    if not BINARY.exists() or any(
        p.stat().st_mtime > BINARY.stat().st_mtime for p in sources if "obj" not in p.parts
    ):
        subprocess.run(
            ["dotnet", "build", str(PROJECT), "-c", "Release", "--nologo"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )


def invoke(command, request):
    _ensure_build()
    directory = ROOT / "tmp" / f"{date.today().isoformat()}-native-cli"
    directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=directory) as temporary:
        work = Path(temporary)
        source, output = work / "request.json", work / "model.floxml"
        source.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
        result = subprocess.run(
            ["dotnet", str(BINARY), command, str(source), str(output)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return output.read_bytes() if command == "generate" else json.loads(result.stdout)


def export_floxml(request):
    return invoke("generate", request)


def resolve_values(request):
    return invoke("values", request)
