"""Independent PACK inputs paired with public PackStudio requests."""

import json
from xml.etree import ElementTree as ET

from tools.floscript.script import component_element, new_package_element


def cases():
    result = []

    def add(
        identifier, family, changes=(), overrides=None, bga=None, assignments=None, wizard=None
    ):
        defaults = {"designName": family, "outlineType": "standardOutline"}
        if family == "bare_die":
            defaults.pop("outlineType")
        if family != "bare_die":
            defaults["jedecFootprint"] = {
                "chip_array": "ChipArray_24_4X4mm_0_8",
                "cbga_fc": "CBGAFC_49_6X6mm",
                "pbga_fc": "PBGAFC_49_6X6mm",
            }[family]
        if family in {"cbga_fc", "pbga_fc"}:
            defaults["topCover"] = "bareDie"
        if family == "chip_array":
            defaults.update(
                dieType="actualDie",
                substrateLayer="2-Layer",
                topSignalLayerThickness="0.018",
                bottomSignalLayerThickness="0.018",
            )
        defaults.update(wizard or {})
        commands = [
            ET.tostring(
                new_package_element("Die" if family == "bare_die" else family, defaults),
                encoding="unicode",
            )
        ]
        commands.extend(
            ET.tostring(component_element(*change), encoding="unicode") for change in changes
        )
        # Heat sources are volumetric by project decision; no collapsed source comparison.
        payload = {
            "template_id": family,
            "overrides": {f"{family}.{k}": v for k, v in (overrides or {}).items()},
            "material_assignments": assignments or {},
        }
        if bga is not None:
            payload["bga"] = bga
        result.append({"id": identifier, "commands": commands, "request": payload})

    for family in ("bare_die", "cbga_fc", "pbga_fc", "chip_array"):
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
    for family in ("cbga_fc", "pbga_fc"):
        add(
            family + "-regular",
            family,
            [
                ("flipChipBumps", "arrayType", "regularArray"),
                ("flipChipBumps", "numberOfBumpsInXMDC4", 3),
                ("flipChipBumps", "numberOfBumpsInYMEC4", 4),
            ],
            {"bumps.array_type": "regular", "bumps.columns": 3, "bumps.rows": 4},
        )
        add(
            family + "-no-underfill",
            family,
            [("flipChipBumps", "underfill", False)],
            {"bumps.underfill": False},
        )
        for cover in ("lid", "plate", "encapsulant"):
            add(
                family + "-" + cover,
                family,
                overrides={"cover.type": cover},
                wizard={"topCover": cover},
            )
        add(
            family + "-flush",
            family,
            [("topCover", "enableDieFlush", True)],
            {"cover.type": "encapsulant", "cover.flush": True},
            wizard={"topCover": "encapsulant"},
        )
        stiff = {
            "stiffenerLengthLs": 5.5,
            "stiffenerWidthWs": 5,
            "stiffenerCavityLengthLsc": 2.8,
            "stiffenerCavityWidthWsc": 2.6,
            "stiffenerAdhesiveThickness": 0.1,
            "stiffener": "yes",
        }
        add(
            family + "-stiffener",
            family,
            [("topCover", k, v) for k, v in stiff.items()],
            {
                "cover.type": "lid",
                "stiffener.enabled": True,
                "stiffener.length": 5.5,
                "stiffener.width": 5,
                "stiffener.cavity_length": 2.8,
                "stiffener.cavity_width": 2.6,
                "stiffener.adhesive": 0.1,
            },
            wizard={"topCover": "lid"},
        )
        for adhesive in (False, True):
            props = {
                "includeSlug": True,
                "slugLengthLsl": 4,
                "slugWidthWsl": 3.8,
                "slugThicknessTsl": 0.4,
                "slugDiameterDs": 2,
                "slugFootExtendLengthLsf": 4.5,
                "slugFootExtendWidthWsf": 4.4,
                "slugOffsetGs": 0.15,
                "slugFootClearanceGsf": 0.2,
                "slugMaterial": "Copper (Pure)",
                "adhesivePresentUnderSlugFoot": adhesive,
                "slugAdhesiveMaterial": "QMI 595",
            }
            add(
                family + "-slug-" + str(adhesive).lower(),
                family,
                [("dropInSlug", k, v) for k, v in props.items()],
                {
                    "cover.type": "encapsulant",
                    "slug.enabled": True,
                    "slug.length": 4,
                    "slug.width": 3.8,
                    "slug.thickness": 0.4,
                    "slug.diameter": 2,
                    "slug.foot_length": 4.5,
                    "slug.foot_width": 4.4,
                    "slug.offset": 0.15,
                    "slug.clearance": 0.2,
                    "slug.adhesive_enabled": adhesive,
                },
                assignments={
                    "group-slug": "copper",
                    **({"group-slug-adhesive": "qmi-595"} if adhesive else {}),
                },
                wizard={"topCover": "encapsulant"},
            )
    for family in ("chip_array", "cbga_fc", "pbga_fc"):
        for representation in ("discrete", "equivalent"):
            native_rep = "discreteCuboids" if representation == "discrete" else "orthotropicCuboid"
            if family == "chip_array" and representation == "equivalent":
                continue  # This project adds equivalent Chip Array balls by decision.
            common = (
                []
                if family == "chip_array"
                else [("modelingOptions", "modelSolderBallArrayAs", native_rep)]
            )
            for rp, cp in ((2, 2), (3, 2), (5, 2), (1, 1)):
                changes = common + [
                    ("solderBallDepopulation", "depopulatedCenter", True),
                    ("solderBallDepopulation", "numberFullyPopulatedRowsMDp", cp),
                    ("solderBallDepopulation", "numberFullyPopulatedRowsMEp", rp),
                ]
                # Use a common 5 x 5 ball grid for parity and frame-boundary checks.
                changes += [
                    ("solderBalls", "numberOfSolderBallsInXMD", 5),
                    ("solderBalls", "numberOfSolderBallsInYME", 5),
                    ("solderBalls", "ballDiameterB", 0.5),
                ]
                add(
                    f"{family}-{representation}-frame-{rp}-{cp}",
                    family,
                    changes,
                    {"bga.columns": 5, "bga.rows": 5, "bga.diameter": 0.5},
                    {
                        "representation": representation,
                        "solder_removal_enabled": True,
                        "populated_rows": rp,
                        "populated_columns": cp,
                    },
                )
            add(
                f"{family}-{representation}-staggered-center",
                family,
                common
                + [
                    ("solderBalls", "staggeredMatrix", True),
                    ("centralBalls", "centralBalls", True),
                    ("centralBalls", "numberCentralRowsMDp", 3),
                    ("centralBalls", "numberCentralRowsMEp", 3),
                    ("centralBalls", "staggeredMatrix", True),
                ],
                bga={
                    "representation": representation,
                    "staggered": True,
                    "center_solder_enabled": True,
                    "center_solder_rows": 3,
                    "center_solder_columns": 3,
                    "center_staggered": True,
                },
            )
    add(
        "chip-four-layer",
        "chip_array",
        overrides={"substrate.layers": "4-Layer"},
        wizard={"substrateLayer": "4-Layer", "solidPlaneThickness": "0.036"},
    )
    for mode in ("accurate", "approximate"):
        for filled in (False, True):
            add(
                f"chip-vias-{mode}-{filled}",
                "chip_array",
                [
                    ("modelingOptions", "viaModeling", mode),
                    ("vias", "filledVias", "yes" if filled else "no"),
                ],
                {"vias.modeling": mode, "vias.filled": filled},
            )
    add(
        "chip-wire-ignore",
        "chip_array",
        [("modelingOptions", "bondWireModeling", "ignore")],
        {"bond_wire.include": False},
    )
    add(
        "chip-wire-count",
        "chip_array",
        [
            ("bondWires", "numberBondWiresEqualsSolderBalls", "no"),
            ("bondWires", "numberOfBondWiresNw", 17),
        ],
        {"bond_wire.auto_count": False, "bond_wire.total": 17},
    )
    for flipped in (False, True):
        add(
            f"bare-bumped-{flipped}",
            "bare_die",
            [
                ("die", "flippedDie", flipped),
                ("bumpedDie", "bumpedDie", True),
                ("bumpedDie", "numberOfSolderBalls", 100),
                ("bumpedDie", "ballDiameterb", 0.12),
                ("bumpedDie", "ballHeight", 0.1),
                ("bumpedDie", "solderConductivity", "Solder (Pb90/Sn10)"),
                ("bumpedDie", "underfillConductivity", "Flip-Chip Underfill (Typical)"),
            ],
            {"bumps.enabled": True, "die.flipped": flipped},
        )
    for mode in ("discrete", "equivalent"):
        add(
            "fc-core-" + mode,
            "pbga_fc",
            [
                ("coreVias", "numberOfThermalViasInXNVx", 3),
                ("coreVias", "numberOfThermalViasInYNVy", 4),
                ("coreVias", "viaDiameterDv", 0.2),
                ("coreVias", "viaPitchEv", 0.5),
                ("coreVias", "platingThicknessTpl", 0.025),
                (
                    "modelingOptions",
                    "modelCoreViasAs",
                    "discreteCuboids" if mode == "discrete" else "orthotropicCuboid",
                ),
            ],
            {
                "vias.enabled": True,
                "vias.columns": 3,
                "vias.rows": 4,
                "vias.diameter": 0.2,
                "vias.pitch": 0.5,
                "vias.plating": 0.025,
                "vias.modeling": mode,
            },
        )
    for region, native, index in [
        ("upper", "upperBuiltUpRegion", 1),
        ("lower", "lowerBuiltUpRegion", 2),
    ]:
        for filled in ("yes", "no"):
            depth = 0.01 if index == 1 else 1.06
            table = [
                {"depth": depth, "thickness": 0.018, "coverage": 20},
                {"depth": depth + 0.05, "thickness": 0.018, "coverage": 90},
            ]
            add(
                f"fc-{region}-{filled}",
                "pbga_fc",
                [
                    (native, "thicknessA2b" + str(index), 0.1),
                    (native, "dielectricMaterial", "BT"),
                    (native, "totalNumberOfMicroViasNb" + str(index), 49),
                    (native, "viaDiameterDvb" + str(index), 0.1),
                    (native, "filledVias", filled),
                    (native, "platingThicknessTpl", 0.025),
                ],
                {
                    region + ".enabled": True,
                    region + ".thickness": 0.1,
                    region + ".count": 49,
                    region + ".diameter": 0.1,
                    region + ".filled": filled == "yes",
                    region + ".plating": 0.025,
                    region + ".layers": json.dumps(table),
                },
                assignments={"group-" + region: "bt"},
            )
            for row, values in enumerate(table):
                for col, value in enumerate(values.values()):
                    element = ET.Element(
                        "modify_component_table_row",
                        name=native,
                        property_name="metalLayersTable",
                        row=str(row),
                        column=str(col),
                        new_value=str(value),
                    )
                    result[-1]["commands"].append(ET.tostring(element, encoding="unicode"))
    return result
