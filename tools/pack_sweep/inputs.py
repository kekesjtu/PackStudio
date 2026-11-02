"""Shared XML command construction and public requests for all template families."""

from xml.etree import ElementTree as ET

from tools.floscript.script import component_element, new_package_element

FOOTPRINTS = {
    "chip_array": "ChipArray_24_4X4mm_0_8",
    "cbga_fc": "CBGAFC_49_6X6mm",
    "pbga_fc": "PBGAFC_49_6X6mm",
    "pqfp": "LQFP_32_7X7mm",
    "sop": "SOP_8_3_81x4_93",
    "qfn": "QFN_12X12_100",
    "pbga_wb": "PBGA_121_15X15mm",
}


def case_adder(result):
    def add(
        identifier, family, changes=(), overrides=None, ball_layout=None,
        material_assignments=None, wizard=None
    ):
        defaults = {"designName": family}
        if family != "bare_die":
            defaults.update(outlineType="standardOutline", jedecFootprint=FOOTPRINTS[family])
        if family in {"cbga_fc", "pbga_fc"}:
            defaults["topCover"] = "bareDie"
        if family in {"chip_array", "pbga_wb"}:
            defaults.update(
                dieType="actualDie",
                substrateLayer="2-Layer",
                topSignalLayerThickness="0.018",
                bottomSignalLayerThickness="0.018",
            )
        if family in {"pqfp", "sop"}:
            defaults.update(dieType="actualDie", exposedPad="false")
            defaults["pqfpPackageType" if family == "pqfp" else "sopPackageType"] = (
                "lqfp" if family == "pqfp" else "soic/sop/so"
            )
        defaults.update(wizard or {})
        if family in {"pqfp", "sop"}:
            footprint = defaults.pop("jedecFootprint")
            subtype = defaults["pqfpPackageType" if family == "pqfp" else "sopPackageType"]
            defaults[("sop" if subtype == "soic/sop/so" else subtype) + "JedecFootprint"] = (
                footprint
            )
        native = {"bare_die": "Die", "qfn": "QFN", "sop": "tsop_conv"}.get(family, family)
        commands = [ET.tostring(new_package_element(native, defaults), encoding="unicode")]
        commands += [
            ET.tostring(component_element(*change), encoding="unicode") for change in changes
        ]
        request = {
            "template_id": family,
            "overrides": {family + "." + k: v for k, v in (overrides or {}).items()},
            "material_assignments": material_assignments or {},
        }
        if ball_layout is not None:
            request["overrides"].update(
                {family + ".bga." + key: value for key, value in ball_layout.items()}
            )
        result.append({"id": identifier, "commands": commands, "request": request})

    return add
