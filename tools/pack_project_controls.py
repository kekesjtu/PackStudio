"""Exercise project-specific BGA composition and component material assignments."""

from packstudio.templates.package_library.catalog import default_request, definitions, generate
from packstudio.templates.package_library.core.parameters import BgaConfiguration
from packstudio.templates.package_library.core.preset_request import resolve_preset_request
from tools.pack_interaction_audit import physical_signature


def audit_project_controls() -> dict:
    materials, bga = {}, {}
    for identifier, definition in definitions().items():
        initial = default_request(identifier)
        rows = []
        for selection in definition.material_selections:
            request = initial.model_copy(
                update={
                    "overrides": {
                        f"{identifier}.{key}": value
                        for key, value in selection.visible_when.items()
                    }
                }
            )
            resolved, preset = resolve_preset_request(definition, request)
            definition.validate_request(resolved)
            default = (
                preset.material_assignments.get(selection.group_id, selection.default)
                if preset
                else selection.default
            )
            alternate = next((v for v in selection.options if v != default), None)
            single_material = alternate is None
            if single_material:
                alternate = default
            changed = request.model_copy(
                update={
                    "material_assignments": {
                        selection.group_id: alternate,
                    }
                }
            )
            before, after = physical_signature(request), physical_signature(changed)
            assigned = [
                b["material_id"]
                for b in after.get("blocks", [])
                if b["parent_group_id"] == selection.group_id
            ]
            rows.append(
                {
                    "group": selection.group_id,
                    "status": "single_material" if single_material else "alternate_material",
                    "context": selection.visible_when,
                    "material": alternate,
                    "model_changed": before != after,
                    "assigned_block_count": len(assigned),
                    "all_blocks_assigned": bool(assigned) and all(v == alternate for v in assigned),
                    "error": after.get("error"),
                }
            )
        materials[identifier] = rows
        if not definition.has_bga:
            continue
        resolved, _ = resolve_preset_request(definition, initial)
        baseline = resolved.bga
        variants = {
            "representation": {
                "representation": "discrete"
                if baseline.representation.value == "equivalent"
                else "equivalent"
            },
            "center_solder_enabled": {"center_solder_enabled": True},
            "center_solder_rows": {"center_solder_enabled": True, "center_solder_rows": 3},
            "center_solder_columns": {"center_solder_enabled": True, "center_solder_columns": 3},
            "solder_removal_enabled": {"solder_removal_enabled": True},
            "removal_rows": {"solder_removal_enabled": True, "removal_rows": 5},
            "removal_columns": {"solder_removal_enabled": True, "removal_columns": 5},
            "omitted_cells": {
                "solder_removal_enabled": True,
                "removal_rows": 0,
                "removal_columns": 0,
                "omitted_cells": [{"row": 0, "column": 0}],
            },
            "allow_asymmetric_regions": {"allow_asymmetric_regions": True},
        }
        probes = []
        before = physical_signature(resolved)
        for field, updates in variants.items():
            pattern = BgaConfiguration.model_validate({**baseline.model_dump(), **updates})
            changed = resolved.model_copy(update={"bga": pattern})
            after = physical_signature(changed)
            count = (
                generate(changed).metadata["solder_ball_count"] if not after.get("error") else None
            )
            probes.append(
                {
                    "control": field,
                    "updates": updates,
                    "model_changed": before != after,
                    "solder_ball_count": count,
                    "error": after.get("error"),
                }
            )
        bga[identifier] = probes
    return {"material_assignments": materials, "project_bga_controls": bga}
