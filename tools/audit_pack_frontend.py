"""Replay real frontend schemas and independently validate their emitted requests."""

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from packstudio.templates.package_library.catalog import default_request, schema
from packstudio.templates.package_library.core.parameters import TemplateRequest
from tools.pack_catalog_builder import write_json
from tools.pack_interaction_audit import physical_signature


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=root / "docs/validation/pack_frontend_interactions.json"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="require preserved covers and valid emitted backend requests",
    )
    arguments = parser.parse_args()
    harness = root / "tests/frontend/_packInteractionProbe.test.tsx"
    if harness.exists():
        raise ValueError(f"refusing to replace an existing file: {harness}")
    with tempfile.TemporaryDirectory(prefix="pack-interaction-") as directory:
        fixture = Path(directory) / "schemas.json"
        results = Path(directory) / "observed.json"
        write_json(
            fixture,
            {
                identifier: {
                    "fields": [f for step in schema(identifier)["steps"] for f in step["fields"]],
                    "request": default_request(identifier).model_dump(mode="json"),
                }
                for identifier in ("cbga_fc", "pbga_fc")
            },
        )
        environment = dict(
            os.environ, PACK_AUDIT_SCHEMA=str(fixture), PACK_AUDIT_FRONTEND_OUTPUT=str(results)
        )
        shutil.copyfile(root / "tools/pack_frontend_probe.tsx", harness)
        try:
            subprocess.run(
                ["npm.cmd" if os.name == "nt" else "npm", "run", "test", "--", str(harness)],
                cwd=root,
                env=environment,
                check=True,
            )
            findings = json.loads(results.read_text(encoding="utf-8"))
            for finding in findings:
                request = TemplateRequest.model_validate(finding["request"])
                finding["packstudio_error"] = physical_signature(request).get("error")
            write_json(
                arguments.output,
                {
                    "schema_version": "packstudio.frontend-interaction-audit/v1",
                    "observations": findings,
                },
            )
            if arguments.verify:
                for finding in findings:
                    if finding["packstudio_error"]:
                        raise ValueError(f"frontend emitted an invalid request: {finding}")
                    if finding["scenario"] == "footprint_preserves_cover":
                        if finding["after"] != finding["before"]:
                            raise ValueError(f"footprint reset the selected cover: {finding}")
                    elif finding["hidden_target"] in finding["request"]["overrides"]:
                        raise ValueError(f"hidden override was retained: {finding}")
        finally:
            harness.unlink()


if __name__ == "__main__":
    main()
