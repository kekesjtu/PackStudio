"""Native commands paired with public generation requests."""

from xml.etree import ElementTree as ET

from tools.floscript.script import component_element, new_package_element


def case_adder(result):
    def add(identifier, family, changes=(), overrides=None, wizard=None, assignments=None):
        defaults = {
            "designName": family,
            "outlineType": "standardOutline",
            "jedecFootprint": {
                "pqfp": "LQFP_32_7X7mm",
                "sop": "SOP_8_3_81x4_93",
                "qfn": "QFN_12X12_100",
                "pbga_wb": "PBGA_121_15X15mm",
            }[family],
        }
        if family in {"pqfp", "sop"}:
            defaults.update(dieType="actualDie", exposedPad="false")
            defaults["pqfpPackageType" if family == "pqfp" else "sopPackageType"] = (
                "lqfp" if family == "pqfp" else "soic/sop/so"
            )
        if family == "pbga_wb":
            defaults.update(
                dieType="actualDie",
                substrateLayer="2-Layer",
                topSignalLayerThickness="0.018",
                bottomSignalLayerThickness="0.018",
            )
        defaults.update(wizard or {})
        if family in {"pqfp", "sop"}:
            footprint = defaults.pop("jedecFootprint")
            subtype = defaults["pqfpPackageType" if family == "pqfp" else "sopPackageType"]
            prefix = "sop" if subtype == "soic/sop/so" else subtype
            defaults[prefix + "JedecFootprint"] = footprint
        native_family = {"qfn": "QFN", "sop": "tsop_conv"}.get(family, family)
        commands = [ET.tostring(new_package_element(native_family, defaults), encoding="unicode")]
        commands += [ET.tostring(component_element(*c), encoding="unicode") for c in changes]
        result.append(
            {
                "id": identifier,
                "commands": commands,
                "request": {
                    "template_id": family,
                    "overrides": {family + "." + k: v for k, v in (overrides or {}).items()},
                    "material_assignments": assignments or {},
                },
            }
        )

    return add
