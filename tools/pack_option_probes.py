"""Read-only reproductions that distinguish missing controls from missing library data."""

import re

from packstudio.preset_catalog import PresetCatalog
from packstudio.templates.package_library.catalog import default_request, definitions, generate
from packstudio.templates.package_library.core.materials import material_id_for_name


def run_probes(root):
    catalog = PresetCatalog()
    active = [
        identifier
        for identifier in catalog.list_ids("pbga_wb")
        if catalog.read_branch(identifier)["groups"]["backsideSpreader"]["properties"][
            "includeBacksideSpreader"
        ].get("value")
    ]
    preset = "PBGA_192_17X17mm"
    properties = catalog.read_branch(preset)["groups"]["backsideSpreader"]["properties"]
    model = generate(
        default_request("pbga_wb").model_copy(
            update={"overrides": {"pbga_wb.footprint.size": preset}}
        )
    )
    materials = []
    for template, group, name in [
        ("bare_die", "group-die", "Gallium Arsenide"),
        ("bare_die", "group-underfill", "Cookson-7115"),
        ("cbga_fc", "group-substrate", "Aluminum Nitride"),
    ]:
        identifier = material_id_for_name(name)
        selection = next(
            m for m in definitions()[template].material_selections if m.group_id == group
        )
        request = default_request(template).model_copy(
            update={
                "material_assignments": {group: identifier},
                "overrides": {"bare_die.bumps.enabled": True} if group == "group-underfill" else {},
            }
        )
        error = None
        try:
            generate(request)
        except ValueError as caught:
            error = str(caught)
        materials.append(
            {
                "template": template,
                "group": group,
                "name": name,
                "id": identifier,
                "allowed": identifier in selection.options,
                "request_error": error,
            }
        )
    inspected = []
    omitted = (
        "realized_geometry|select_starter|modeling_options|staggered|solder_ball_map|"
        "localize|underfill_off|regular_array|flipped_die|exposed_pad_on|model_leads|model_vias"
    )
    for directory in sorted((root / "flotherm_pack_data/templates").iterdir()):
        for path in sorted((directory / "screenshots").glob("*.png")):
            if re.match(r"^(step_|conditional_)", path.name) and not re.search(omitted, path.name):
                inspected.append(path.relative_to(root).as_posix())
    for relative in [
        "bare_die/screenshots/dropdown_die_material.png",
        "bare_die/screenshots/dropdown_underfill_conductivity_resins_01.png",
        "chip_array/screenshots/dropdown_bond_wire_count_relation.png",
    ]:
        inspected.append("flotherm_pack_data/templates/" + relative)
    return {
        "backside_spreader": {
            "default_enabled_presets": active,
            "preset": preset,
            "native": {k: v.get("value") for k, v in properties.items()},
            "generated_spreader_blocks": [b.id for b in model.blocks if "spreader" in b.id.lower()],
            "source": catalog.read(preset)["source"]["path"],
        },
        "material_candidate_checks": materials,
        "visually_reviewed_images": sorted(set(inspected)),
        "visual_method": "分组检查参数面板，关键下拉与居中对话框另外打开原图；未修改原图。",
        "visual_caveat": "starter 截图的背景可能是上一个模板，选项以居中 Customize Template 为准。",
    }
