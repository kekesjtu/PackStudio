"""Archive, rebuild and validate the local native PACK reference library."""

import argparse
import json
from datetime import datetime
from pathlib import Path

from tools.floscript.environment import INSTALLATION
from tools.pack_sweep.archive import archive_tree
from tools.pack_sweep.rebuild import rebuild
from tools.pack_sweep.validate import validate_point, validate_tree

REPOSITORY = Path(__file__).resolve().parents[2]


def workspace_path(path):
    path = path.resolve()
    if not path.is_relative_to(REPOSITORY) or path == REPOSITORY:
        raise ValueError("write paths must stay inside the repository")
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    archive = commands.add_parser("archive", help="create a ZIP backup of the data tree")
    archive.add_argument("--source", type=Path, default=REPOSITORY / "flotherm_pack_data")
    archive.add_argument("--archive", type=Path, required=True)
    build = commands.add_parser("rebuild", help="replay native inputs and publish verified data")
    build.add_argument("--source", type=Path, default=REPOSITORY / "flotherm_pack_data")
    build.add_argument("--output", type=Path, default=REPOSITORY / "flotherm_pack_data")
    build.add_argument(
        "--work",
        type=Path,
        default=REPOSITORY / "tmp" / (datetime.now().strftime("%Y-%m-%d") + "-pack-sweep"),
    )
    build.add_argument("--package", action="append", dest="packages")
    build.add_argument("--batch-size", type=int, default=64)
    build.add_argument("--timeout", type=int, default=180)
    build.add_argument("--installation", type=Path, default=INSTALLATION)
    validate = commands.add_parser("validate", help="validate a point or the complete data tree")
    target = validate.add_mutually_exclusive_group()
    target.add_argument("--point", type=Path)
    target.add_argument("--root", type=Path, default=REPOSITORY / "flotherm_pack_data")
    validate.add_argument("--installation", type=Path, default=INSTALLATION)
    args = parser.parse_args(argv)
    if args.command == "archive":
        result = archive_tree(args.source, workspace_path(args.archive))
    elif args.command == "rebuild":
        output, work = workspace_path(args.output), workspace_path(args.work)
        if output != REPOSITORY / "flotherm_pack_data" and not output.is_relative_to(
            REPOSITORY / "tmp"
        ):
            raise ValueError("--output must be flotherm_pack_data or a directory under tmp/")
        if not work.is_relative_to(REPOSITORY / "tmp") or work == REPOSITORY / "tmp":
            raise ValueError("--work must be a task directory under tmp/")
        if args.packages and output == REPOSITORY / "flotherm_pack_data":
            raise ValueError("selected packages require a separate --output under tmp/")
        result = rebuild(
            args.source,
            output,
            work,
            args.installation.resolve(),
            args.packages,
            args.batch_size,
            args.timeout,
        )
    else:
        if args.point:
            point = args.point.resolve()
            packages = next((path for path in point.parents if path.name == "packages"), None)
            result = validate_point(
                point, args.installation, reference_root=packages.parent if packages else None,
            )
        else:
            result = validate_tree(args.root.resolve(), args.installation)
            result = {k: v for k, v in result.items() if k != "points"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(result.get("status") == "incomplete")


if __name__ == "__main__":
    raise SystemExit(main())
