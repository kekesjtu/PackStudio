"""Invoke the shared C# model core from native PACK research tools."""

import json
import os
import subprocess
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / "src/PackStudio.Cli/bin/Release/net10.0/PackStudio.Cli.dll"


def _binary():
    binary = Path(os.environ.get("PACKSTUDIO_CLI_BINARY", BINARY)).resolve()
    if not binary.is_file():
        raise FileNotFoundError(
            f"C# CLI binary not found: {binary}\n"
            "Run .\\build.ps1 -Target Cli before invoking research tools."
        )
    return binary


def invoke(command, request):
    binary = _binary()
    directory = ROOT / "tmp" / f"{date.today().isoformat()}-native-cli"
    directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=directory) as temporary:
        work = Path(temporary)
        source, output = work / "request.json", work / "model.floxml"
        source.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
        try:
            result = subprocess.run(
                ["dotnet", str(binary), command, str(source), str(output)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        except subprocess.CalledProcessError as error:
            diagnostic = "\n".join(part.strip() for part in (error.stdout, error.stderr) if part)
            raise RuntimeError(
                f"C# CLI {command} failed ({error.returncode}):\n{diagnostic}"
            ) from error
        return output.read_bytes() if command == "generate" else json.loads(result.stdout)


def export_floxml(request):
    return invoke("generate", request)


def resolve_values(request):
    return invoke("values", request)
