"""Separate initialization rules, editing rules and absent active default structures."""

from packstudio.preset_catalog import PresetCatalog
from packstudio.templates.package_library.catalog import default_request, generate
from tools.pack_interaction_audit import changed_properties


def coupled_probes(native) -> dict:
    path = native.installation / "flocentral/flopack/pbga_wb/PBGA_121_15X15mm.des"
    baseline = native.probe(path)
    edits = []
    for scenario, values in (
        ("edit_substrate_length_crosses_wizard_threshold", {"substrateLengthD": 24}),
        ("edit_ball_pitch", {"ballPitchE": 1.3}),
        ("edit_ball_columns", {"numberOfSolderBallsInXMD": 10}),
    ):
        snapshot = native.probe(path, edits=values)
        edits.append(
            {
                "scenario": scenario,
                "edits": values,
                "native_property_changes": changed_properties(baseline, snapshot),
            }
        )
    catalog = PresetCatalog()
    spreaders = []
    for identifier in catalog.list_ids("pbga_wb"):
        branch = catalog.read_branch(identifier)
        properties = branch["groups"]["backsideSpreader"]["properties"]
        if properties["includeBacksideSpreader"]["value"]:
            spreaders.append(
                {
                    "preset": identifier,
                    "length_mm": properties["spreaderLengthLspr"]["value"],
                    "width_mm": properties["spreaderWidthWspr"]["value"],
                    "thickness_mm": properties["spreaderThicknessTspr"]["value"],
                }
            )
    representative = spreaders[0]["preset"]
    model = generate(
        default_request("pbga_wb").model_copy(
            update={
                "overrides": {
                    "pbga_wb.footprint.size": representative,
                }
            }
        )
    )
    return {
        "wirebond_editing": edits,
        "wirebond_enabled_backside_spreaders": spreaders,
        "representative_spreader_model": {
            "preset": representative,
            "generated_groups": [g.id for g in model.groups],
        },
    }
