"""Inventory captured PACK controls against the current schema and reviewed scope."""

import hashlib
import json
from collections import Counter
from datetime import date
from pathlib import Path

from packstudio.templates.package_library.catalog import definitions
from tools.pack_option_probes import run_probes
from tools.pack_option_rules import BARE, BGA, STEP_ALIASES, decision

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/validation/pack_option_audit.json"


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def classify(template, entry, definition, binding):
    prop, location, label = entry["property_name"], entry["ui_location"], entry["label"]
    selected = decision(template, entry)
    if selected:
        status, finding, reason = selected
        return {"status": status, "finding": finding, "reason": reason, "targets": []}
    if prop == "designName":
        return result("implemented", ["request.design_name"])
    if entry["classification"] == "metadata":
        return result("metadata_gap", [], "R02：概要元数据未提供，不影响当前几何")
    if entry["classification"] == "jedec_preset":
        return result("implemented", ["footprint.size"])
    if prop == "gridDensity":
        return result(
            "adapted", ["request.mesh.resolution"], "项目最大网格尺寸预设替代 PACK 网格区域"
        )
    if prop in BGA:
        return result("adapted", ["request." + BGA[prop]], "当前焊球去除、中央区域与表达入口")
    if location == "solder_ball_depopulation" and not prop:
        return result("adapted", ["request.bga.omitted_cells"], "显式索引替代交互去球表及文件导入")
    if location == "solder_balls" and label == "Click To Edit":
        return result("gap", [], "任意坐标 solder-ball map 尚未实现，未批准舍弃")
    if template == "bare_die" and prop in BARE:
        return result("implemented", [BARE[prop]])
    if template == "bare_die" and prop == "dieMaterial":
        return result("implemented", ["material.group-die"], "Si / GaAs 均已开放")
    candidates = [
        key
        for category in ("parameters", "materials")
        for key, path in binding.get(category, {}).items()
        if path[-1] == prop
    ]
    if candidates:
        return result("implemented", candidates, "明确原生属性绑定；材料仍受组件白名单限制")
    if "Group" in label:
        return result("restricted_material", [], "当前组件候选受限；不属于已确认的功能取舍")
    if "Material" in label or label in {
        "Material",
        "Solder Conductivity",
        "Underfill Conductivity",
    }:
        step = STEP_ALIASES.get(location, location)
        selections = [s.group_id for s in definition.material_selections if s.step == step]
        if selections:
            return result("restricted_material", selections, "组件入口存在，候选子集见材料专项 R01")
    return result("unresolved", [], "需要人工核对，不能自动算作已实现或明确取舍")


def result(status, targets, reason=""):
    return {"status": status, "finding": None, "targets": targets, "reason": reason}


def evidence_images(template, entry, ui):
    step = entry["ui_location"].split(".")[0]
    source = next((s for s in ui["steps"] if s["id"] == step), {})
    paths = [source["screenshot"]] if source.get("screenshot") else []
    for field in source.get("fields", []):
        if field["name"] == entry["label"] and field.get("screenshot"):
            paths.append(field["screenshot"])
    return [f"flotherm_pack_data/templates/{template}/{path}" for path in paths]


def main():
    registry = read("flotherm_pack_data/internal_property_registry.json")
    bindings = read("default_parameters/pack_bindings.json")["families"]
    rows, templates, sources = [], {}, set()
    registry_path = "flotherm_pack_data/internal_property_registry.json"
    sources.update({registry_path, "default_parameters/pack_bindings.json", "requirements.md"})
    for block in registry["templates"]:
        template = block["template_id"]
        definition = definitions()[template]
        relative = f"flotherm_pack_data/templates/{template}/ui.json"
        ui = read(relative)
        sources.update({relative, f"default_parameters/templates/{template}.json"})
        known = {field.key for field in definition.fields}
        known.update(selection.group_id for selection in definition.material_selections)
        known.update(
            f"material.{selection.group_id}" for selection in definition.material_selections
        )
        for index, entry in enumerate(block["entries"]):
            outcome = classify(template, entry, definition, bindings.get(template, {}))
            assert all(
                target in known or target.startswith("request.") for target in outcome["targets"]
            )
            images = evidence_images(template, entry, ui)
            sources.update(images)
            rows.append(
                {
                    "template": template,
                    "reference_target": entry["target_id"],
                    "location": entry["ui_location"],
                    "label": entry["label"],
                    "native_property": entry["property_name"],
                    "reference_options": entry["options"],
                    "registry_entry": index,
                    "screenshots": images,
                    **outcome,
                }
            )
        templates[template] = {
            "reference_entries": len(block["entries"]),
            "current_fields": len(definition.fields),
            "current_material_selections": len(definition.material_selections),
            "nested_ui_details": {
                s["id"]: {
                    key: s[key]
                    for key in ("variants", "length_unit_options", "non_uniform_die_heat_editor")
                    if key in s
                }
                for s in ui["steps"]
                if any(
                    key in s
                    for key in ("variants", "length_unit_options", "non_uniform_die_heat_editor")
                )
            },
        }
    unresolved = [r for r in rows if r["status"] == "unresolved"]
    for row in unresolved:
        print("UNRESOLVED", row["reference_target"], row["native_property"])
    assert len(rows) == registry["entry_count"]
    probes = run_probes(ROOT)
    sources.update(probes["visually_reviewed_images"])
    sources.update(
        {
            "tools/audit_pack_options.py",
            "tools/pack_option_rules.py",
            "tools/pack_option_probes.py",
            "src/packstudio/templates/package_library/core/leadframe_materials.py",
            "src/packstudio/templates/package_library/core/wirebond_copper.py",
            "src/packstudio/templates/package_library/core/coupled_materials.py",
            "src/packstudio/templates/package_library/core/generator.py",
            "src/packstudio/templates/package_library/bga/pbga_wb.py",
            "src/packstudio/templates/package_library/bga/chip_array.py",
            "src/packstudio/templates/package_library/bga/backside_spreader.py",
            "src/packstudio/templates/package_library/core/via_configuration.py",
            "src/packstudio/templates/package_library/core/via_geometry.py",
            "src/packstudio/templates/package_library/leadframe/qfn_vias.py",
            "src/packstudio/templates/package_library/bare_die/template.py",
            "src/frontend/features/package-library/ViaRemovalPanel.tsx",
            "src/frontend/features/package-library/SolderRemovalMatrix.tsx",
            "src/frontend/features/package-library/WorkspaceSteps.tsx",
            "default_parameters/request.json",
            "flotherm_pack_data/templates/qfn/xml_variations/option_switches/"
            "opt_v2_c002_modelviasas_discrete/script.xml",
            "flotherm_pack_data/templates/qfn/xml_variations/option_switches/"
            "opt_v2_c002_modelviasas_discrete/model.xml",
            "flotherm_pack_data/templates/pbga_wb/xml_variations/option_switches/"
            "opt_v2_c008_includebacksidespreader_true/script.xml",
            "flotherm_pack_data/templates/pbga_wb/xml_variations/option_switches/"
            "opt_v2_c008_includebacksidespreader_true/model.xml",
            "src/packstudio/templates/package_library/flip_chip/cover.py",
            "default_parameters/presets/pbga_wb/PBGA_192_17X17mm.json",
            "default_parameters/materials/index.json",
        }
    )
    sources.update(
        {
            "docs/decisions/README.md",
            "docs/decisions/封装外形与芯片类型范围.md",
            "docs/decisions/BGA与Bumps建模表达.md",
            "docs/decisions/仅支持均匀芯片热源.md",
        }
    )
    archived = []
    for template in templates:
        relative = f"flotherm_pack_data/templates/{template}/xml_variations.json"
        manifest = read(relative)
        sources.add(relative)
        gap_props = {
            r["native_property"] for r in rows if r["template"] == template and r["finding"]
        }
        for case in manifest["variations"]:
            if case["target"].get("property") not in gap_props:
                continue
            prefix = f"flotherm_pack_data/templates/{template}/"
            diff_path = prefix + case["artifacts"]["diff"]
            diff = read(diff_path)
            sources.add(diff_path)
            archived.append(
                {
                    "template": template,
                    "target": case["target"],
                    "diff": diff_path,
                    "semantic_change": diff["semantic_change"],
                    "summary": diff["summary"],
                }
            )
    report = {
        "schema_version": "packstudio.option-audit/v1",
        "review_date": date.today().isoformat(),
        "scope": "Current controls and the three approved functional decisions",
        "entry_count": len(rows),
        "counts": dict(Counter(r["status"] for r in rows)),
        "templates": templates,
        "probes": probes,
        "archived_variation_evidence": archived,
        "source_sha256": {
            p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sorted(sources)
        },
        "limitations": [
            "登记表与截图证明控件存在，不证明对应分支具备完整物理验证。",
            "implemented 仅表示当前入口/绑定存在，不表示与原生所有选项和组合等价。",
            "只有当前决策索引中的三项属于明确取舍，其他限制与未实现功能单独记录。",
            "nested_ui_details 保留顶盖嵌套选项；不能把 589 条登记表当作全部嵌套控件。",
        ],
        "entries": rows,
    }
    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"{len(rows)} entries; {len(unresolved)} unresolved; {report['counts']}")


if __name__ == "__main__":
    main()
