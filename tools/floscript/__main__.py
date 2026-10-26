"""Run with uv run --locked python -m tools.floscript."""

import argparse
import json
import sys
from pathlib import Path

from lxml import etree

from tools.floscript.environment import INSTALLATION, check
from tools.floscript.runner import execute, run_script
from tools.floscript.script import validate


def main() -> int:
    parser = argparse.ArgumentParser(description="Local PACK 2504 FloSCRIPT tools")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("check", help="check the installed runtime and schema files")
    validation = subparsers.add_parser("validate", help="validate FloSCRIPT or FloXML XSD")
    validation.add_argument("--script", type=Path, required=True)
    validation.add_argument("--floxml", action="store_true", help="validate FloXML instead")
    execution = subparsers.add_parser("run", help="prepare and execute an export script once")
    source = execution.add_mutually_exclusive_group(required=True)
    source.add_argument("--script", type=Path)
    source.add_argument(
        "--prepared", type=Path, help="execute a directory prepared by Python tools"
    )
    execution.add_argument("--output", type=Path)
    execution.add_argument("--timeout", type=int, default=60)
    execution.add_argument("--empty-material-library", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "check":
            print(json.dumps(check(), ensure_ascii=False, indent=2))
        elif args.command == "validate":
            validate(args.script, floxml=args.floxml)
            print("XSD validation passed")
        else:
            if args.prepared:
                if args.output or args.empty_material_library:
                    parser.error("--prepared cannot be combined with runtime preparation options")
                result = execute(args.prepared, timeout=args.timeout)
            else:
                if args.output is None:
                    parser.error("--script requires --output")
                result = run_script(
                    args.script.resolve(),
                    args.output.resolve(),
                    INSTALLATION,
                    timeout=args.timeout,
                    copy_materials=not args.empty_material_library,
                )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["status"] == "success" else 1
    except (OSError, ValueError, etree.Error) as exc:
        print(f"FloSCRIPT: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
