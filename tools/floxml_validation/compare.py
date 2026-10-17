"""Geometry matching and material-field comparison; names are evidence, not keys."""

from dataclasses import replace
from math import isclose

from tools.floxml_validation.partition import (
    GEOMETRY_ABS_MM,
    PROPERTY_ABS,
    PROPERTY_REL,
    overlap_volume,
    partition,
    totals,
)

PROPERTIES = ("kx", "ky", "kz", "density", "specific_heat")


def same_geometry(left, right):
    return all(
        isclose(a, b, abs_tol=GEOMETRY_ABS_MM, rel_tol=1e-10)
        for a, b in zip((*left.origin, *left.size), (*right.origin, *right.size), strict=True)
    )


def property_differences(left, right):
    return {
        key: {"pack": a, "packstudio": b}
        for key, a, b in zip(PROPERTIES, left, right, strict=True)
        if not isclose(a, b, rel_tol=PROPERTY_REL, abs_tol=PROPERTY_ABS)
    }


def match_raw(native, drafts, materials):
    remaining = list(drafts)
    mapped, matches, missing = [], [], []
    for box in native.boxes:
        candidates = [candidate for candidate in remaining if same_geometry(box, candidate)]
        if candidates:
            candidate = candidates[0]
            remaining.remove(candidate)
            mapped.append(
                replace(
                    box,
                    role=candidate.role,
                    priority=candidate.priority,
                    identity=candidate.identity,
                )
            )
            matches.append(
                {
                    "pack_path": box.path,
                    "packstudio_id": candidate.identity,
                    "role": candidate.role,
                    "priority": candidate.priority,
                    "pack_material": box.material,
                    "packstudio_material": candidate.material,
                    "origin_mm": box.origin,
                    "size_mm": box.size,
                    "property_differences": property_differences(
                        native.materials[box.material], materials[candidate.material]
                    ),
                }
            )
        else:
            mapped.append(box)
            missing.append({"pack_path": box.path, "origin_mm": box.origin, "size_mm": box.size})
    return mapped, {
        "matches": matches,
        "unmatched_pack": missing,
        "unmatched_packstudio": [
            {"id": b.identity, "role": b.role, "origin_mm": b.origin, "size_mm": b.size}
            for b in remaining
        ],
        "mapping_complete": not missing,
    }


def compare(native, exported, drafts, draft_materials):
    mapped, raw = match_raw(native, drafts, draft_materials)
    physical = partition(mapped)
    actual = exported.boxes
    mismatches = []
    shared_volume = 0.0
    role_mismatch_volume = 0.0
    property_mismatch_volume = dict.fromkeys(PROPERTIES, 0.0)
    for left in physical:
        for right in actual:
            volume = overlap_volume(left, right)
            if volume <= 1e-12:
                continue
            shared_volume += volume
            differences = property_differences(
                native.materials[left.material], exported.materials[right.material]
            )
            for key in differences:
                property_mismatch_volume[key] += volume
            if left.role != right.role:
                role_mismatch_volume += volume
            if differences or left.role != right.role:
                mismatches.append(
                    {
                        "pack_path": left.path,
                        "packstudio_path": right.path,
                        "pack_role": left.role,
                        "packstudio_role": right.role,
                        "overlap_mm3": volume,
                        "property_differences": differences,
                    }
                )
    expected_totals = totals(physical, native.materials)
    actual_totals = totals(actual, exported.materials)
    return {
        "raw": raw,
        "normalized": {
            "interpretation": "PACK solids clipped using matched PackStudio semantic precedence; "
            "not a claim about FloTHERM solver overlap precedence",
            "status": "comparable"
            if raw["mapping_complete"] and not native.collapsed_solids
            else "provisional_mapping_or_collapsed_solids",
            "pack": expected_totals,
            "packstudio": actual_totals,
            "total_deltas": {
                key: actual_totals[key] - expected_totals[key]
                for key in ("volume_mm3", "mass_kg", "heat_capacity_j_k")
            },
            "shared_volume_mm3": shared_volume,
            "pack_only_volume_mm3": max(0.0, expected_totals["volume_mm3"] - shared_volume),
            "packstudio_only_volume_mm3": max(0.0, actual_totals["volume_mm3"] - shared_volume),
            "role_mismatch_volume_mm3": role_mismatch_volume,
            "property_mismatch_volume_mm3": property_mismatch_volume,
            "differences": mismatches,
        },
        "sources": {
            "pack": native.sources,
            "packstudio": exported.sources,
            "pack_power_w": sum(s["power_w"] for s in native.sources),
            "packstudio_power_w": sum(s["power_w"] for s in exported.sources),
            "total_power_equal": isclose(
                sum(s["power_w"] for s in native.sources),
                sum(s["power_w"] for s in exported.sources),
                rel_tol=1e-10,
                abs_tol=1e-10,
            ),
            "total_power_difference_w": sum(s["power_w"] for s in exported.sources)
            - sum(s["power_w"] for s in native.sources),
            "note": "PACK collapsed surface sources and PackStudio volume sources are explicit "
            "modeling choices; equal total power does not prove equal temperature fields.",
        },
        "native_temperature_materials": native.temperature_materials,
        "native_material_cautions": {
            name: {"density": p[3], "specific_heat": p[4]}
            for name, p in native.materials.items()
            if p[3] <= 1 or p[4] <= 1
        },
        "native_collapsed_solids": native.collapsed_solids,
        "native_nonphysical_entities": native.nonphysical_entities,
        "raw_summed_volume_is_not_physical_total": True,
    }
