"""Native-only probes for DES keys, component properties and FC region activation."""

from xml.etree import ElementTree as ET

from tools.pack_sweep.inputs import case_adder


def cases():
    result = []

    def add(identifier, family, edits=(), *, wizard=None, setup=(), metadata=None):
        rows = []
        case_adder(rows)(identifier, family, changes=list(setup) + list(edits), wizard=wizard)
        row = rows[0]
        result.append(
            {
                "template": family,
                "id": identifier,
                "commands": row["commands"],
                "metadata": {
                    "kind": "field_correspondence",
                    "validation_scope": (
                        "native property assignment, DES readback and FloXML; no public-model claim"
                    ),
                    **(metadata or {}),
                },
            }
        )
        return result[-1]

    add(
        "field-die-material-gaas",
        "bare_die",
        [("die", "dieMaterial", "GaAs")],
        metadata={"expected_des": {"radio_die": "2"}},
    )
    for layers, encoded in [("2-Layer", "1"), ("4-Layer", "2")]:
        add(
            "field-component-layer-" + encoded,
            "chip_array",
            [("metalLayers", "substrateLayer", layers)],
            metadata={
                "expected_des": {"num_metal_layers": encoded},
                "component_property": "metalLayers.substrateLayer",
                "comparison_baseline": "field-component-layer-1/model.des",
                "expected_des_changes": {} if encoded == "1" else {"num_metal_layers": encoded},
            },
        )
    for thickness in [0.05, 0.08, 0.12]:
        add(
            f"field-land-thickness-{str(thickness).replace('.', '_')}",
            "qfn",
            [("thermalLand", "landThickness", thickness)],
            setup=[
                ("thermalLand", "includeLand", True),
                ("thermalLand", "material", "Copper (Pure)"),
            ],
            metadata={
                "expected_des": {"ts": str(thickness), "isLand": "CHECKED"},
                "comparison_baseline": "field-land-thickness-0_05/model.des",
                "expected_des_changes": {} if thickness == 0.05 else {"ts": str(thickness)},
            },
        )

    table = [[0.1, 0.018, 30], [0.4, 0.025, 65]]
    for name, change in [
        ("baseline", None),
        ("depth", (0, 0, 0.2)),
        ("thickness", (0, 1, 0.02)),
        ("coverage", (0, 2, 40)),
    ]:
        values = [list(r) for r in table]
        if change:
            row, col, value = change
            values[row][col] = value
        point = add(
            "field-core-metal-" + name,
            "pbga_fc",
            metadata={
                "comparison_baseline": "field-core-metal-baseline/model.des",
                "expected_des": {
                    prefix + str(i + 1): str(v)
                    for i, row in enumerate(values)
                    for prefix, v in zip(("z", "tz", "coverage"), row, strict=True)
                },
                "expected_des_changes": {}
                if change is None
                else {("z", "tz", "coverage")[change[1]] + str(change[0] + 1): str(change[2])},
            },
        )
        for row, values_row in enumerate(values):
            for col, value in enumerate(values_row):
                point["commands"].append(
                    ET.tostring(
                        ET.Element(
                            "modify_component_table_row",
                            name="metalLayers",
                            property_name="metalLayersTable",
                            row=str(row),
                            column=str(col),
                            new_value=str(value),
                        ),
                        encoding="unicode",
                    )
                )

    add("field-activation-default", "pbga_fc", metadata={"activation_scenario": "unassigned"})
    core = [
        ("coreVias", "numberOfThermalViasInXNVx", 3),
        ("coreVias", "numberOfThermalViasInYNVy", 4),
        ("coreVias", "viaDiameterDv", 0.2),
        ("coreVias", "viaPitchEv", 0.5),
        ("coreVias", "platingThicknessTpl", 0.025),
    ]
    for name, count in [("defined", None), ("zero-count", 0)]:
        edits = list(core)
        if count == 0:
            edits = [(g, p, 0 if p.startswith("numberOfThermal") else v) for g, p, v in edits]
        add(
            "field-core-" + name, "pbga_fc", edits, metadata={"activation_scenario": "core-" + name}
        )
    for region, component, suffix in [
        ("upper", "upperBuiltUpRegion", "1"),
        ("lower", "lowerBuiltUpRegion", "2"),
    ]:
        setup = [
            (component, "thicknessA2b" + suffix, 0.1),
            (component, "dielectricMaterial", "BT"),
            (component, "filledVias", "yes"),
        ]
        for name, count in [("region-only", None), ("zero-count", 0), ("defined", 49)]:
            edits = (
                []
                if count is None
                else [
                    (component, "totalNumberOfMicroViasNb" + suffix, count),
                    (component, "viaDiameterDvb" + suffix, 0.1),
                ]
            )
            add(
                "field-" + region + "-" + name,
                "pbga_fc",
                edits,
                setup=setup,
                metadata={"activation_scenario": region + "-" + name},
            )
    return result
