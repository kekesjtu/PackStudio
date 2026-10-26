"""Conservative attribution: unexplained differences remain open evidence items."""


def classify(case, details):
    findings = []

    def add(category, identifier, evidence, status):
        findings.append(
            {"category": category, "id": identifier, "evidence": evidence, "status": status}
        )

    for difference in details["normalized"]["differences"]:
        roles = {difference["pack_role"], difference["packstudio_role"]}
        bump_in_plane_gap = "flip_chip_bump" in roles and set(
            difference["property_differences"]
        ) <= {"kx", "ky"}
        if case["kind"] == "constituent_material" and not bump_in_plane_gap:
            category, reason = "confirmed_implementation_defect", "F2-constituent-edit-propagation"
        elif case["id"] == "qfp-small-height" and roles == {"encapsulant", "bond_wire"}:
            category, reason = (
                "physically_supported_implementation",
                "P1-small-height-wire-segments",
            )
        elif case["template"] == "sop" and "/group-tie-bars/" in difference["packstudio_path"]:
            category, reason = "physically_supported_implementation", "P3-sop-solid-metal-tie-bar"
        elif "lead_frame" in roles and case["template"] in {"pqfp", "sop"}:
            category, reason = "confirmed_implementation_defect", "F1-equivalent-metal-overwritten"
        elif "flip_chip_bump" in roles:
            category, reason = "implementation_gap", "U9-bump-isotropic-alignment"
        else:
            category, reason = (
                "insufficient_evidence",
                "U1-unattributed-material-or-role-difference",
            )
        difference["category"] = category
        difference["attribution"] = reason
        if case["kind"] == "constituent_material" and "flip_chip_bump" in roles:
            difference["additional_attributions"] = ["U9-bump-isotropic-alignment"]
    if details["normalized"]["differences"]:
        for reason in sorted({d["attribution"] for d in details["normalized"]["differences"]}):
            selected = [
                d for d in details["normalized"]["differences"] if d["attribution"] == reason
            ]
            add(
                selected[0]["category"],
                reason,
                {"region_count": len(selected)},
                "confirmed_existing" if reason.startswith("F") else "documented_or_open",
            )
    if case["kind"] == "constituent_material" and case["template"] in {"cbga_fc", "pbga_fc"}:
        add(
            "implementation_gap",
            "U9-bump-isotropic-alignment",
            "The BGA/Bumps decision requires Isotropic Cuboid; "
            "the current orthotropic layer is not aligned. "
            "Constituent sensitivity and normal conductivity are checked independently.",
            "open",
        )
    extra = details["raw"]["unmatched_packstudio"]
    unexpected = [
        b
        for b in extra
        if b["role"] != "static_air"
        and not (case["id"] == "qfp-small-height" and b["role"] == "bond_wire")
    ]
    if details["raw"]["unmatched_pack"] or unexpected:
        add(
            "insufficient_evidence",
            "U2-raw-topology-mapping",
            "Unmatched cuboids are listed explicitly; no guessed material correspondence.",
            "open",
        )
    if case["kind"] == "coupled_material_edit":
        add(
            "physically_supported_implementation",
            "P2-mass-weighted-wire-homogenization",
            "Edited gold enters the declared parallel-conductivity and mass-weighted heat rules; "
            "region values checked, not a solver-accuracy claim.",
            "verified_rule",
        )
    if details["normalized"]["packstudio_only_volume_mm3"] > 1e-6:
        add(
            "insufficient_evidence",
            "C2-static-air-or-extra-region",
            details["normalized"]["packstudio_only_volume_mm3"],
            "open",
        )
    if details["native_collapsed_solids"]:
        add(
            "insufficient_evidence",
            "C3-collapsed-versus-volume-solids",
            details["native_collapsed_solids"],
            "nominal_volume_comparison_only",
        )
    if details["native_temperature_materials"]:
        add(
            "insufficient_evidence",
            "C4-reference-temperature-constant",
            details["native_temperature_materials"],
            "documented",
        )
    if details.get("native_material_cautions"):
        add(
            "inherited_pack_physical_risk",
            "R3-low-native-density-or-specific-heat",
            details["native_material_cautions"],
            "verify_material_data_before_engineering_use",
        )
    if case["template"] in {"chip_array", "sop"}:
        add(
            "inherited_pack_physical_risk",
            "R2-die-attach-same-bottom-overlap",
            "Raw die/attach origins and normalized silicon volume are retained in the case report.",
            "confirmed_geometry_field_meaning_open",
        )
    if case["id"] == "wb-copper-asymmetry":
        add(
            "inherited_pack_physical_risk",
            "R1-via-end-gap",
            "Unequal copper thickness native replay, DES readback and normalized geometry.",
            "confirmed_native_and_project",
        )
    if case["id"] == "qfp-small-height":
        add(
            "physically_supported_implementation",
            "P1-small-height-wire-segments",
            "PACK omits tiny vertical segments; project retains finite cuboids.",
            "compatibility_difference_requires_thermal_validation",
        )
    if any(s["collapse"] for s in details["sources"]["pack"]):
        add(
            "insufficient_evidence",
            "C5-surface-versus-volume-heat-source",
            details["sources"],
            "total_power_checked_spatial_distribution_differs",
        )
    if not details["sources"].get("total_power_equal", True):
        add("insufficient_evidence", "U8-total-power-mismatch", details["sources"], "open")
    return findings
