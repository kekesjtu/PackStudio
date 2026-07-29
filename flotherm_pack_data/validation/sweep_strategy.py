"""Constraint-aware branch contexts for comprehensive single-variable sweeps."""

from __future__ import annotations

from typing import Any

Command = tuple[str, str, Any]

NUMERIC_VALUE_OVERRIDES = {
    ("qfp_family", "bondWires", "numberOfBondWiresN"): [30, 31],
    ("soic_family", "leadFrame", "totalNumberOfLeadsMT"): [6, 10],
    ("soic_family", "bondWires", "bondWireLengthLbw"): [0.3, 0.4],
}

NUMERIC_VALUE_REASONS = {
    ("qfp_family", "bondWires", "numberOfBondWiresN"): (
        "The JEDEC baseline already uses the 32-lead upper bound; 33 is "
        "normalized back to 32 by PACK."
    ),
    ("soic_family", "leadFrame", "totalNumberOfLeadsMT"): (
        "PACK normalizes unsupported odd lead counts, so representative even counts are used."
    ),
    ("soic_family", "bondWires", "bondWireLengthLbw"): (
        "PACK normalizes the generic plus/minus 10 percent values; 0.3 mm was "
        "confirmed through a direct GUI FloSCRIPT recording."
    ),
}

FLOXML_EFFECT_EXPECTATIONS = {
    ("soic_family", "new_package", "dieType"): {
        "expectation": "no_change_at_default_substate",
        "reason": (
            "PACK accepts thermalDie, but with the default uniform heat source "
            "the exported FloXML is identical to actualDie."
        ),
        "evidence": ["templates/soic_family/xml_variations.json"],
    },
    ("soic_family", "bondWires", "bondWireLengthLbw"): {
        "expectation": "no_change_at_default_substate",
        "reason": (
            "PACK records and displays the changed length, but the default "
            "standard-outline orthotropic-cuboid export remains byte-identical."
        ),
        "evidence": [
            "validation/recorded_soic_bond_wire_length.xml",
            "validation/targeted_replay_soic_bond_wire_length.xml",
        ],
    },
}


def command(component: str, prop: str, value: Any) -> Command:
    return component, prop, value


def slug_context(include_top_cover: bool) -> list[Command]:
    result = []
    if include_top_cover:
        result.append(command("topCover", "topCover", "encapsulant"))
    result.extend(
        [
            command("dropInSlug", "includeSlug", True),
            command("dropInSlug", "slugLengthLsl", 4),
            command("dropInSlug", "slugWidthWsl", 4),
            command("dropInSlug", "slugThicknessTsl", 0.4),
            command("dropInSlug", "slugDiameterDs", 2),
            command("dropInSlug", "slugFootExtendLengthLsf", 4.5),
            command("dropInSlug", "slugFootExtendWidthWsf", 4.5),
            command("dropInSlug", "slugOffsetGs", 0.1),
            command("dropInSlug", "slugFootClearanceGsf", 0.1),
        ]
    )
    return result


def context_for(
    template_id: str,
    component: str,
    prop: str,
    location: str,
) -> list[Command]:
    if component == "bumpedDie":
        return [
            command(component, "bumpedDie", True),
            command(component, "numberOfSolderBalls", 25),
            command(component, "ballDiameterb", 0.3),
            command(component, "ballHeight", 0.2),
        ]
    if component == "metalLayers" and prop in {"lengthLml", "widthWml"}:
        return [
            command(component, "lengthLml", 1),
            command(component, "widthWml", 1),
        ]
    if component == "solderBallDepopulation":
        return [
            command(component, "depopulatedCenter", True),
            command(component, "numberFullyPopulatedRowsMDp", 2),
            command(component, "numberFullyPopulatedRowsMEp", 2),
        ]
    if component == "centralBalls":
        return [
            command(component, "centralBalls", True),
            command(component, "numberCentralRowsMDp", 2),
            command(component, "numberCentralRowsMEp", 2),
        ]
    if component == "flipChipBumps" and prop in {
        "arrayType",
        "numberOfBumpsInXMDC4",
        "numberOfBumpsInYMEC4",
    }:
        return [
            command(component, "arrayType", "regularArray"),
            command(component, "numberOfBumpsInXMDC4", 6),
            command(component, "numberOfBumpsInYMEC4", 6),
        ]
    if component == "dropInSlug":
        return slug_context(template_id in {"flip_chip_cbga", "flip_chip_pbga"})
    if component == "topCover":
        if location.startswith("top_cover.lid"):
            result = [command(component, "topCover", "lid")]
            if location == "top_cover.lid_stiffener" or prop == "stiffener":
                result.extend(
                    [
                        command(component, "stiffener", "yes"),
                        command(component, "stiffenerLengthLs", 6),
                        command(component, "stiffenerWidthWs", 6),
                        command(component, "stiffenerCavityLengthLsc", 3),
                        command(component, "stiffenerCavityWidthWsc", 3),
                        command(component, "stiffenerAdhesiveThickness", 0.1),
                    ]
                )
            return result
        if location.startswith("top_cover.plate"):
            return [command(component, "topCover", "plate")]
        if location.startswith("top_cover.encapsulant"):
            return [command(component, "topCover", "encapsulant")]
    if component == "coreVias":
        return [
            command(component, "numberOfThermalViasInXNVx", 5),
            command(component, "numberOfThermalViasInYNVy", 5),
            command(component, "viaDiameterDv", 0.2),
            command(component, "viaPitchEv", 0.8),
            command(component, "platingThicknessTpl", 0.025),
        ]
    if component == "upperBuiltUpRegion":
        return [
            command(component, "thicknessA2b1", 0.1),
            command(component, "totalNumberOfMicroViasNb1", 49),
            command(component, "viaDiameterDvb1", 0.1),
        ]
    if component == "lowerBuiltUpRegion":
        return [
            command(component, "thicknessA2b2", 0.1),
            command(component, "totalNumberOfMicroViasNb2", 49),
            command(component, "viaDiameterDvb2", 0.1),
        ]
    if component == "thermalLand":
        return [
            command(component, "includeLand", True),
            command(component, "landThickness", 0.05),
        ]
    if component == "vias" and template_id == "qfn":
        return [
            command(component, "modelViasAs", "discrete"),
            command(component, "viasLengthLv", 0.85),
            command(component, "viasDiameterDv", 0.2),
            command(component, "platingThicknessTpl", 0.02),
            command(component, "viasPitchEv", 0.5),
            command(component, "numberOfViasInXVD", 5),
            command(component, "numberOfViasInYVE", 5),
        ]
    if component == "modelingOptions" and prop == "numberOfDiscreteBondwireSteps":
        return [command(component, prop, 5)]
    if component == "modelingOptions" and prop == "modelCoreViasAs":
        return [
            command("coreVias", "numberOfThermalViasInXNVx", 5),
            command("coreVias", "numberOfThermalViasInYNVy", 5),
            command("coreVias", "viaDiameterDv", 0.2),
            command("coreVias", "viaPitchEv", 0.8),
            command("coreVias", "platingThicknessTpl", 0.025),
        ]
    if component == "leadFrame" and prop in {
        "userDefinedLeadframeCoverage",
        "leadframeCoveragePercentage",
    }:
        return [
            command(component, "userDefinedLeadframeCoverage", "yes"),
            command(component, "leadframeCoveragePercentage", 40),
        ]
    if component == "thermalLandAndSolder":
        return [
            command(component, "includeThermalLandAndSolder", True),
            command(component, "landThickness", 0.05),
        ]
    if component == "backsideSpreader":
        return [
            command(component, "includeBacksideSpreader", True),
            command(component, "spreaderLengthLspr", 8),
            command(component, "spreaderWidthWspr", 8),
            command(component, "spreaderThicknessTspr", 0.5),
            command(component, "bottomTraceHoleLengthLbt", 5),
            command(component, "bottomTraceHoleWidthWbt", 5),
        ]
    if component == "bondWires" and prop == "numberBondWiresEqualsSolderBalls":
        return [command(component, "numberOfBondWiresNw", 16)]
    return []


def numeric_value_override(
    template_id: str,
    component: str | None,
    prop: str,
) -> tuple[list[int | float] | None, str | None]:
    key = (template_id, component, prop)
    return NUMERIC_VALUE_OVERRIDES.get(key), NUMERIC_VALUE_REASONS.get(key)


def floxml_effect_expectation(
    template_id: str,
    component: str,
    prop: str,
) -> dict[str, Any] | None:
    return FLOXML_EFFECT_EXPECTATIONS.get((template_id, component, prop))


def seed_from_context(context: list[Command], component: str, prop: str) -> Any:
    for item_component, item_property, value in reversed(context):
        if item_component == component and item_property == prop:
            return value
    return None


def prerequisite_context_needed(
    component: str,
    prop: str,
    location: str,
    default: Any,
) -> bool:
    return (
        default is None
        or component
        in {
            "bumpedDie",
            "dropInSlug",
            "coreVias",
            "upperBuiltUpRegion",
            "lowerBuiltUpRegion",
            "thermalLand",
            "vias",
            "thermalLandAndSolder",
            "backsideSpreader",
        }
        or component == "topCover"
        and location.startswith("top_cover.")
        or component == "centralBalls"
        and prop in {"centralBalls", "staggeredMatrix"}
        or component == "solderBallDepopulation"
        and prop == "depopulatedCenter"
        or component == "flipChipBumps"
        and prop == "arrayType"
        or component == "leadFrame"
        and prop == "userDefinedLeadframeCoverage"
        or component == "bondWires"
        and prop == "numberBondWiresEqualsSolderBalls"
        or component == "modelingOptions"
        and prop == "modelCoreViasAs"
    )
