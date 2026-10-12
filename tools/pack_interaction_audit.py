"""Compare native parameter edits with PackStudio inputs and physical model effects."""

from packstudio.templates.package_library.catalog import default_request, generate
from packstudio.templates.package_library.core.native_presets import at_path, read_binding
from packstudio.templates.package_library.core.parameters import TemplateRequest
from packstudio.templates.package_library.core.preset_request import resolve_preset_request
from tools.pack_catalog_builder import compiled_branch
from tools.pack_catalog_properties import scalar


def physical_signature(request: TemplateRequest) -> dict:
    try:
        model = generate(request)
        data = model.model_dump(mode="json")
        return {
            "blocks": [
                {
                    k: b[k]
                    for k in (
                        "id",
                        "origin",
                        "size",
                        "material_id",
                        "structure_type",
                        "parent_group_id",
                    )
                }
                for b in data["blocks"]
            ],
            "materials": [
                {k: m[k] for k in ("id", "conductivity", "density", "specific_heat")}
                for m in data["materials"]
            ],
            "heat_sources": [
                {k: h[k] for k in ("block_id", "power_w")} for h in data["heat_sources"]
            ],
        }
    except ValueError as error:
        return {"error": str(error)}


def changed_properties(before: dict, after: dict) -> dict:
    def flatten(groups):
        return {f"{g['name']}/{p['name']}": p["value"] for g in groups for p in g["properties"]}

    left, right = flatten(before["groups"]), flatten(after["groups"])
    return {
        key: {"before": left.get(key), "after": value}
        for key, value in right.items()
        if left.get(key) != value
    }


def candidate_value(field, value):
    if isinstance(value, bool):
        return not value
    if field.options:
        return next((v for v in field.options if v != value), None)
    if isinstance(value, int | float):
        step = 1 if field.control.startswith("integer") else max(abs(value) * 0.1, 0.001)
        candidate = value + step
        if field.maximum is not None and candidate > field.maximum:
            candidate = value - step
        if field.minimum is not None and candidate < field.minimum:
            return None
        return candidate
    return None


def audit_fields(native, definition, preset: str) -> list[dict]:
    request = default_request(definition.id)
    footprint = next(f for f in definition.fields if f.control == "footprint")
    request = request.model_copy(update={"overrides": {footprint.target_id(definition.id): preset}})
    binding = read_binding(definition.id)
    path = (
        native.installation / "flocentral/flopack" / binding["family"] / f"{preset}.des"
        if binding
        else None
    )
    result = []
    for field in definition.fields:
        if field.control == "footprint":
            continue
        context = {**field.visible_when, **field.enabled_when}
        active_request = request.model_copy(
            update={
                "overrides": {
                    **request.overrides,
                    **{f"{definition.id}.{k}": v for k, v in context.items()},
                }
            }
        )
        values = definition.validate_request(resolve_preset_request(definition, active_request)[0])
        baseline_model = physical_signature(active_request)
        current = values._values[field.key]
        row = {
            "field": field.key,
            "baseline": current,
            "context": context,
            "baseline_error": baseline_model.get("error"),
        }
        candidate = candidate_value(field, current)
        if candidate is None or field.key == "package.type":
            row["status"] = (
                "subtype_requires_footprint" if field.key == "package.type" else "no_candidate"
            )
            result.append(row)
            continue
        changed = active_request.model_copy(
            update={
                "overrides": {
                    **active_request.overrides,
                    field.target_id(definition.id): candidate,
                }
            }
        )
        changed_model = physical_signature(changed)
        row.update(input=candidate, model_changed=changed_model != baseline_model)
        row["packstudio_error"] = changed_model.get("error")
        native_path = binding["parameters"].get(field.key) if binding else None
        if native_path and len(native_path) in {4, 6} and native_path[:1] == ["groups"]:
            wizard = {"topCover": context["cover.type"]} if "cover.type" in context else {}
            context_edits = {
                binding["parameters"][k][-1]: v
                for k, v in context.items()
                if k in binding["parameters"] and len(binding["parameters"][k]) == 4
            }
            baseline_native = native.probe(path, wizard=wizard, edits=context_edits)
            snapshot = native.probe(
                path, wizard=wizard, edits={**context_edits, native_path[-1]: candidate}
            )
            row["native_property_changes"] = changed_properties(baseline_native, snapshot)
            row["native_invalid_groups"] = [
                g["name"] for g in snapshot["groups"] if g["enabled"] and not g["group_valid"]
            ]
            row["status"] = "native_dataset_edit_replayed"
            group = next(g for g in snapshot["groups"] if g["name"] == native_path[1])
            if len(native_path) == 6:
                group = next(
                    g for g in group["children"] if native_path[3].capitalize() in g["native_type"]
                )
            prop = next(p for p in group["properties"] if p["name"] == native_path[-1])
            row["native_input_value"] = scalar(prop["value"], prop["native_type"])
        elif field.key == "cover.type":
            snapshot = native.probe(path, wizard={"topCover": candidate})
            branch = compiled_branch({**snapshot, "family": binding["family"]})
            changed_values = definition.validate_request(
                resolve_preset_request(definition, changed)[0]
            )
            differences = {}
            for key, location in binding["parameters"].items():
                if key.startswith(("cover.", "lid.", "plate.")):
                    actual = at_path(branch, location).get("value")
                    ours = changed_values._values[key]
                    if actual is not None and actual != ours:
                        differences[key] = {"native": actual, "packstudio": ours}
            row.update(status="native_wizard_choice_replayed", branch_differences=differences)
        else:
            row["status"] = "project_field_or_nested_property_not_replayed"
        result.append(row)
    return result


def audit_covers(native, definition, preset: str) -> list[dict]:
    binding = read_binding(definition.id)
    path = native.installation / "flocentral/flopack" / binding["family"] / f"{preset}.des"
    result = []
    for choice in ("bareDie", "encapsulant", "lid", "plate"):
        snapshot = native.probe(path, wizard={"topCover": choice})
        branch = compiled_branch({**snapshot, "family": binding["family"]})
        cover = "bare_die" if choice == "bareDie" else choice
        request = default_request(definition.id).model_copy(
            update={
                "overrides": {
                    f"{definition.id}.footprint.size": preset,
                    f"{definition.id}.cover.type": cover,
                }
            }
        )
        values = definition.validate_request(resolve_preset_request(definition, request)[0])
        keys = ("lid.",) if choice == "lid" else ("plate.",) if choice == "plate" else ("cover.",)
        differences = {}
        for key, location in binding["parameters"].items():
            if key.startswith(keys) and key != "cover.type":
                actual = at_path(branch, location).get("value")
                if actual is not None and actual != values._values[key]:
                    differences[key] = {"native": actual, "packstudio": values._values[key]}
        result.append(
            {
                "choice": choice,
                "differences": differences,
                "packstudio_error": physical_signature(request).get("error"),
                "native_invalid_groups": [
                    g["name"] for g in snapshot["groups"] if g["enabled"] and not g["group_valid"]
                ],
            }
        )
    return result
