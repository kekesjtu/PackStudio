"""Corroborate inert model fields with existing FloXML sweeps; do not run exports."""

import hashlib
import json
from pathlib import Path

from packstudio.templates.package_library.core.native_presets import read_binding


def corroborate_inert(fields: dict) -> list[dict]:
    root = Path(__file__).resolve().parents[1]
    result = []
    for template, rows in fields.items():
        binding = read_binding(template)
        manifest = root / "flotherm_pack_data/templates" / template / "xml_variations.json"
        variations = json.loads(manifest.read_text(encoding="utf-8"))["variations"]
        for row in rows:
            if row.get("model_changed") is not False:
                continue
            location = binding["parameters"].get(row["field"]) if binding else None
            prop = (
                location[-1]
                if location
                else "flippedDie"
                if row["field"] == "die.flipped"
                else None
            )
            matches = [v for v in variations if v.get("target", {}).get("property") == prop]
            evidence = []
            for match in matches:
                diff = manifest.parent / match["artifacts"]["diff"]
                evidence.append(
                    {
                        "value": match["target"]["value"],
                        "outcome": match["outcome"],
                        "diff": diff.relative_to(root).as_posix(),
                        "diff_sha256": hashlib.sha256(diff.read_bytes()).hexdigest(),
                        "summary": match["summary"],
                    }
                )
            result.append(
                {
                    "template": template,
                    "field": row["field"],
                    "native_property": prop,
                    "archived_evidence": evidence,
                }
            )
    return result
