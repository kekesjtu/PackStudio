"""Build the desktop backend with its portable JSON default library."""

import os
from pathlib import Path

from PyInstaller.__main__ import run


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    # PyInstaller resolves relative data paths against specpath, not the shell cwd.
    run(
        [
            "--noconfirm",
            "--clean",
            "--name",
            "packstudio-backend",
            "--onedir",
            "--paths",
            str(root / "src"),
            "--add-data",
            f"{root / 'default_parameters'}{os.pathsep}default_parameters",
            "--exclude-module",
            "uvloop",
            "--specpath",
            str(root / "build"),
            "--distpath",
            str(root / "release/backend"),
            "--workpath",
            str(root / "build/pyinstaller"),
            str(root / "src/packstudio/__main__.py"),
        ]
    )


if __name__ == "__main__":
    main()
