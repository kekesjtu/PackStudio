"""UI classification constants and synthetic PACK fields."""

from __future__ import annotations

from typing import Any

MATERIAL_MARKERS = ("material", "conductivity")

METADATA_FIELDS = {
    "Design Name",
    "Part Number",
    "Vendor Name",
    "Max Power",
    "Max Operating Junction Temperature",
    "Max Case Temperature",
    "Notes",
}

TOP_COVER_VARIANT_FIELDS = {
    "lid": [
        ("Lid Length Lc", "number", 6),
        ("Lid Width Wc", "number", 6),
        ("Lid Thickness Tc", "number", 1),
        ("Lid Base Thickness Tcb", "number", 2.5),
        ("Die Attach Thickness tda", "number", 0.05),
        ("Lid Adhesive Thickness", "number", 0.2),
        ("Stiffener", "select", "no"),
    ],
    "lid_stiffener": [
        ("Stiffener Length Ls", "number", None),
        ("Stiffener Width Ws", "number", None),
        ("Stiffener Cavity Length Lsc", "number", None),
        ("Stiffener Cavity Width Wsc", "number", None),
        ("Stiffener Adhesive Thickness", "number", None),
    ],
    "plate": [
        ("Plate Length Lc", "number", 6),
        ("Plate Width Wc", "number", 6),
        ("Plate Thickness Tc", "number", 1),
    ],
    "encapsulant": [
        ("Encapsulant Length Le", "number", 4),
        ("Encapsulant Width We", "number", 4),
        ("Enable Die Flush", "checkbox", False),
        ("Encapsulant Thickness Te", "number", 1.2),
    ],
}

DROP_IN_SLUG_SYNTHETIC_FIELDS = [
    ("Slug Length Lsl", "number", None),
    ("Slug Width Wsl", "number", None),
    ("Slug Thickness tsl", "number", None),
    ("Slug Diameter ds", "number", None),
    ("Slug Foot Extend Length Lsf", "number", None),
    ("Slug Foot Extend Width Wsf", "number", None),
    ("Slug Offset Gs", "number", None),
    ("Slug Foot Clearance gsf", "number", None),
    ("Adhesive Present Under Slug Foot", "checkbox", False),
]

# Runtime replay proved that SOP/TSOP ``overallPackage.lengthD`` is not a
# writable FloSCRIPT property, even after non-standard-outline initialization.
COVERAGE_POLICY_OVERRIDES = {
    ("soic_family", "overall_package", "Length D"): {
        "classification": "derived_parameter",
        "coverage_policy": "runtime_rejected_not_independent",
        "reason": (
            "PACK 2504 rejects overallPackage.lengthD in both the JEDEC "
            "baseline and a fully initialized non-standard-outline branch."
        ),
    },
}

INACTIVE_DEFAULT_MATERIAL_BRANCHES = {
    "bare_die": {
        "bumped_die",
    },
    "flip_chip_pbga": {
        "upper_built_up_region",
        "lower_built_up_region",
    },
    "qfn": {
        "thermal_land",
    },
    "wirebond_pbga": {
        "drop_in_slug",
    },
}

for template_id, locations in INACTIVE_DEFAULT_MATERIAL_BRANCHES.items():
    for location in locations:
        COVERAGE_POLICY_OVERRIDES[(template_id, location, "*")] = {
            "classification": "inactive_default_material_branch",
            "coverage_policy": "default_only_inactive_material_branch",
            "reason": (
                "The branch defaults to No Attachment with empty dependent "
                "dimensions. Activating it would require a non-default material, "
                "which is outside the default-only material policy."
            ),
        }

COVERAGE_POLICY_OVERRIDES[("bare_die", "modeling_options", "Solder Bump Modeling")] = {
    "classification": "inactive_default_material_branch",
    "coverage_policy": "default_only_inactive_material_branch",
    "reason": (
        "This modeling option has no effective geometry while Bumped Die uses "
        "its default No Attachment materials."
    ),
}

PROPERTY_TEMPLATE_OVERRIDES = {
    ("wirebond_pbga", "die", "Extent of Bond Wire Pads Lw"): ("bondWireExtentLengthLw"),
    ("wirebond_pbga", "die", "Extent of Bond Wire Pads Ww"): ("bondWireExtentWidthWw"),
}


def option_values(field: dict[str, Any]) -> list[Any]:
    options = field.get("options", [])
    if not isinstance(options, list):
        return [options]
    return [option.get("value") if isinstance(option, dict) else option for option in options]


def is_material_field(name: str) -> bool:
    lowered = name.lower()
    return any(marker in lowered for marker in MATERIAL_MARKERS) or name in {
        "Material",
        "C4 Solder",
    }
