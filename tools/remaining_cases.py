"""Replay independently specified native inputs for the four wirebond families."""

from xml.etree import ElementTree as ET

from tools.remaining_inputs import case_adder
from tools.remaining_presets import append_presets


def cases():
    result = []

    add = case_adder(result)

    for family in ("pqfp", "sop", "qfn", "pbga_wb"):
        add(family + "-baseline", family)
        for density in ("coarse", "medium"):
            add(
                family + "-grid-" + density,
                family,
                [("modelingOptions", "gridDensity", density)],
                {"grid.density": density},
            )
        add(
            family + "-grid-off",
            family,
            [("modelingOptions", "localizeGrid", False)],
            {"grid.enabled": False},
        )
        if family != "qfn":
            add(
                family + "-wire-isotropic",
                family,
                [("modelingOptions", "modelBondWiresAs", "isotropicCuboid")],
                {"bond_wire.modeling": "isotropicCuboid"},
            )
        if family in {"pqfp", "sop"}:
            add(
                family + "-coverage",
                family,
                [
                    ("leadFrame", "userDefinedLeadframeCoverage", "yes"),
                    ("leadFrame", "leadframeCoveragePercentage", 20),
                ],
                {"leads.custom_coverage": True, "leads.coverage": 20},
            )
            add(
                family + "-exposed",
                family,
                overrides={"package.exposed_pad": True},
                wizard={"exposedPad": "true"},
            )
            add(
                family + "-lead-copper",
                family,
                [("leadFrame", "leadframeMaterial", "Copper (Pure)")],
                assignments={"group-lead-frame": "copper"},
            )
            for coverage in (25, 75):
                add(
                    family + "-flag-" + str(coverage),
                    family,
                    [("dieFlagAndTieBars", "metalCoverageForDieFlagCf", coverage)],
                    {"flag.coverage": coverage},
                )
        if family == "sop":
            add("sop-flag-copper", family,
                [("dieFlagAndTieBars", "dieFlagMaterial", "Copper (Pure)")],
                assignments={"group-die-flag": "copper"})
            for downset in (0.3, 0.414, 0.418, 0.422, 0.5):
                add(
                    "sop-height-" + str(downset),
                    family,
                    [("dieFlagAndTieBars", "dieFlagDownsetDdf", downset)],
                    {"flag.downset": downset},
                )
            add(
                "sop-flag-thickness",
                family,
                [("dieFlagAndTieBars", "dieFlagThicknessTf", 0.25)],
                {"flag.thickness": 0.25},
            )
        if family == "pqfp":
            add(
                "pqfp-rectangle",
                family,
                [
                    ("overallPackage", "lengthD", 11),
                    ("encapsulant", "lengthD1", 8),
                    ("die", "dieLengthLd", 2.4),
                    ("die", "dieWidthWd", 1.8),
                    ("bondWires", "numberOfBondWiresN", 31),
                ],
                {
                    "package.length": 11,
                    "body.length": 8,
                    "die.length": 2.4,
                    "die.width": 1.8,
                    "bond_wire.count": 31,
                },
            )
            add(
                "pqfp-leads-isotropic",
                family,
                [("modelingOptions", "modelLeadFrameAs", "isotropicCuboid")],
                {"leads.modeling": "isotropicCuboid"},
            )
            for downset in (0.25, 0.384, 0.388, 0.392, 0.44):
                add(
                    "pqfp-height-" + str(downset),
                    family,
                    [("dieFlagAndTieBars", "dieFlagDownsetDdf", downset)],
                    {"flag.downset": downset},
                )
            for count in (0, 29, 31, 33, 36):
                add(
                    "pqfp-count-" + str(count),
                    family,
                    [("bondWires", "numberOfBondWiresN", count)],
                    {"bond_wire.count": count},
                )
        if family == "qfn":
            add(
                "qfn-rectangle-stepped",
                family,
                [
                    ("overallPackage", "lengthD", 13),
                    ("die", "dieLengthLd", 5.8),
                    ("modelingOptions", "numberOfDiscreteBondwireSteps", 3),
                ],
                {"package.length": 13, "die.length": 5.8, "bond_wire.steps": 3},
            )
            add(
                "qfn-interconnect-lumped",
                family,
                [("modelingOptions", "modelLeadAndSolderInterconnectAs", "orthotropicCuboid")],
                {"leads.modeling": "orthotropicCuboid"},
            )
            for steps in (2, 3, 5):
                add(
                    "qfn-steps-" + str(steps),
                    family,
                    [("modelingOptions", "numberOfDiscreteBondwireSteps", steps)],
                    {"bond_wire.steps": steps},
                )
            for mode in ("discrete", "lumped"):
                properties = {
                    "modelViasAs": mode,
                    "numberOfViasInXVD": 3,
                    "numberOfViasInYVE": 4,
                    "viasDiameterDv": 0.2,
                    "viasPitchEv": 0.5,
                    "platingThicknessTpl": 0.025,
                    "viasLengthLv": 1.2,
                }
                add(
                    "qfn-vias-" + mode,
                    family,
                    [("vias", k, v) for k, v in properties.items()],
                    {
                        "vias.enabled": True,
                        "vias.modeling": mode,
                        "vias.columns": 3,
                        "vias.rows": 4,
                        "vias.diameter": 0.2,
                        "vias.pitch": 0.5,
                        "vias.plating": 0.025,
                        "vias.length": 1.2,
                    },
                )
        if family == "pbga_wb":
            add(
                "wb-metal-aluminum",
                family,
                [("metalLayers", "materialOfMetal", "Aluminum (Pure)")],
                assignments={"group-traces": "aluminum"},
            )
            add(
                "wb-flag-coverage",
                family,
                [("dieFlagAndSolderMask", "coveragePercentageCf", 25)],
                {"flag.coverage": 25},
            )
            add(
                "wb-four-layer",
                family,
                overrides={"substrate.layers": "4-Layer"},
                wizard={"substrateLayer": "4-Layer", "solidPlaneThickness": "0.036"},
            )
            for mode in ("isotropicCuboid", "orthotropicCuboid"):
                add(
                    "wb-vias-" + mode,
                    family,
                    [("modelingOptions", "modelThermalViasAs", mode)],
                    {"vias.modeling": mode},
                )
            for diameter in (0.2, 0.4):
                add(
                    "wb-disconnect-" + str(diameter),
                    family,
                    [("thermalVias", "viaDiameterDv", diameter)],
                    {"substrate.layers": "4-Layer", "vias.diameter": diameter},
                    wizard={"substrateLayer": "4-Layer", "solidPlaneThickness": "0.036"},
                )
            for adhesive in (False, True):
                props = dict(
                    includeSlug=True,
                    slugLengthLsl=11,
                    slugWidthWsl=10,
                    slugThicknessTsl=0.15,
                    slugDiameterDs=5,
                    slugFootExtendLengthLsf=12,
                    slugFootExtendWidthWsf=11.5,
                    slugOffsetGs=0.1,
                    slugFootClearanceGsf=0.2,
                    slugMaterial="Copper (Pure)",
                    adhesivePresentUnderSlugFoot=adhesive,
                    slugAdhesiveMaterial="QMI 595",
                )
                add(
                    "wb-slug-" + str(adhesive),
                    family,
                    [("dropInSlug", k, v) for k, v in props.items()],
                    {
                        "slug.enabled": True,
                        "slug.length": 11,
                        "slug.width": 10,
                        "slug.thickness": 0.15,
                        "slug.diameter": 5,
                        "slug.foot_length": 12,
                        "slug.foot_width": 11.5,
                        "slug.offset": 0.1,
                        "slug.clearance": 0.2,
                        "slug.adhesive_enabled": adhesive,
                    },
                    assignments={
                        "group-slug": "copper",
                        **({"group-slug-adhesive": "qmi-595"} if adhesive else {}),
                    },
                )
            spreader = dict(
                includeBacksideSpreader=True,
                spreaderLengthLspr=3,
                spreaderWidthWspr=2.5,
                spreaderThicknessTspr=0.1,
                bottomTraceHoleLengthLbt=3.5,
                bottomTraceHoleWidthWbt=3,
                spreaderMaterial="Copper (Pure)",
            )
            add(
                "wb-spreader",
                family,
                [("backsideSpreader", k, v) for k, v in spreader.items()],
                {
                    "spreader.enabled": True,
                    "spreader.length": 3,
                    "spreader.width": 2.5,
                    "spreader.thickness": 0.1,
                    "spreader.hole_length": 3.5,
                    "spreader.hole_width": 3,
                },
                assignments={"group-backside-spreader": "copper"},
            )
            for layer in ("2-Layer", "4-Layer"):
                add(
                    "wb-unequal-" + layer,
                    family,
                    overrides={
                        "substrate.layers": layer,
                        "trace.top_thickness": 0.01,
                        "trace.bottom_thickness": 0.04,
                    },
                    wizard={
                        "substrateLayer": layer,
                        "solidPlaneThickness": "0.036",
                    },
                )
                for row, thickness in [(0, 0.01), (5, 0.04)]:
                    result[-1]["commands"].append(ET.tostring(ET.Element(
                        "modify_component_table_row", name="metalLayers",
                        property_name="metalLayersTable", row=str(row), column="1",
                        new_value=str(thickness)), encoding="unicode"))
    append_presets(add)
    return result
