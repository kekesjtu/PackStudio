"""Package verified comparisons and native evidence, excluding configs and licences."""

import argparse
import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path

import pefile

from packstudio.templates.package_library.catalog import generate
from packstudio.templates.package_library.core.parameters import TemplateRequest
from tools.floxml_validation.cases import ROOT
from tools.floxml_validation.classification import classify
from tools.floxml_validation.native import fingerprint
from tools.floxml_validation.reader import read

LIMITATIONS = [
    {
        "category": "insufficient_evidence",
        "id": "U4-solver-overlap-precedence",
        "status": "open",
        "evidence": "Partition precedence is the project rule; native collapsed solids use "
        "nominal envelopes. FloTHERM import/mesh/solver behavior was not verified.",
    },
    {
        "category": "insufficient_evidence",
        "id": "U5-die-thickness-field-meaning",
        "status": "open",
        "evidence": "Chip Array/SOP die and attach overlap is observed in both applications. "
        "the input means silicon thickness or inclusive envelope needs a model decision.",
    },
    {
        "category": "insufficient_evidence",
        "id": "U6-thermal-accuracy-and-coverage",
        "status": "open",
        "evidence": "No solver/measurement accuracy assessment. No exhaustive Cartesian product of "
        "all 346 footprints, tensor constituents, discrete BGA or removed-ball patterns.",
    },
]


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sensitivity(case, exported_path):
    request = TemplateRequest.model_validate(case["request"]).model_copy(
        update={"custom_materials": []}
    )
    baseline = generate(request)
    by_id = {block.id: block for block in baseline.blocks}
    materials = {
        m.id: (m.conductivity.x, m.conductivity.y, m.conductivity.z, m.density, m.specific_heat)
        for m in baseline.materials
    }
    actual = read(exported_path)
    changed = []
    for box in actual.boxes:
        before, after = materials[by_id[box.name].material_id], actual.materials[box.material]
        if before != after:
            changed.append({"id": box.name, "role": box.role, "before": before, "after": after})
    return {
        "changed_blocks": changed,
        "changed_role_counts": dict(Counter(b["role"] for b in changed)),
        "no_final_material_change": not changed,
    }


def publish(archive_output, native_output, destination):
    original, native = _load(archive_output / "results.json"), _load(native_output / "results.json")
    archived_kinds = {"baseline", "numeric_parameter", "cover_numeric", "enum_option"}
    cases = [c for c in original["cases"] if c["kind"] in archived_kinds] + native["cases"]
    if len({c["id"] for c in cases}) != len(cases):
        raise ValueError("duplicate comparison IDs")
    destination.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": "packstudio.floxml-evidence/v1", "cases": []}
    bundle = destination / "evidence.zip"
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for case in cases:
            directory = Path(case["detail_path"]).parent
            prefix = f"cases/{case['id']}"
            native_path = Path(case["native_path"])
            source_path = Path(case["input_source"])
            if fingerprint(native_path) != case["native_sha256"]:
                raise ValueError(f"native evidence changed: {case['id']}")
            if fingerprint(source_path) != case["input_source_sha256"]:
                raise ValueError(f"input evidence changed: {case['id']}")
            entry = {key: case[key] for key in ("id", "template", "kind", "request")}
            entry.update(
                native=f"{prefix}/native.xml", source=f"{prefix}/source{source_path.suffix}"
            )
            entry.update(
                native_sha256=case["native_sha256"], input_source_sha256=case["input_source_sha256"]
            )
            manifest["cases"].append(entry)
            archive.write(native_path, entry["native"])
            archive.write(source_path, entry["source"])
            archive.write(directory / "request.json", f"{prefix}/request.json")
            if case["status"] == "compared":
                path = directory / "packstudio.floxml"
                if fingerprint(path) != case["export_sha256"]:
                    raise ValueError(f"export changed: {case['id']}")
                archive.write(path, f"{prefix}/packstudio.floxml")
                details = _load(directory / "comparison.json")
                native_materials = read(native_path).materials
                details["native_material_cautions"] = {
                    name: {"density": p[3], "specific_heat": p[4]}
                    for name, p in native_materials.items()
                    if p[3] <= 1 or p[4] <= 1
                }
                details["sources"]["pack"] = read(native_path).sources
                details["sources"]["packstudio"] = read(path).sources
                left_power = sum(s["power_w"] for s in details["sources"]["pack"])
                right_power = sum(s["power_w"] for s in details["sources"]["packstudio"])
                details["sources"].update(
                    total_power_equal=abs(right_power - left_power) < 1e-10,
                    total_power_difference_w=right_power - left_power,
                )
                case["power"].update(
                    total_power_equal=details["sources"]["total_power_equal"],
                    total_power_difference_w=right_power - left_power,
                )
                data = details["normalized"]
                data["total_deltas"] = {
                    key: data["packstudio"][key] - data["pack"][key]
                    for key in ("volume_mm3", "mass_kg", "heat_capacity_j_k")
                }
                case["normalized"]["total_deltas"] = data["total_deltas"]
                if case["kind"] in {"constituent_material", "coupled_material_edit"}:
                    case["project_material_sensitivity"] = _sensitivity(case, path)
                    details["project_material_sensitivity"] = case["project_material_sensitivity"]
                details["findings"] = classify(case, details)
                case["findings"] = details["findings"]
                case["difference_examples"] = details["normalized"]["differences"][:5]
                archive.writestr(
                    f"{prefix}/comparison.json", json.dumps(details, ensure_ascii=False)
                )
            archive.writestr(f"{prefix}/result.json", json.dumps(case, ensure_ascii=False))
            if "native_des_sha256" in case:
                des = native_path.with_suffix(".des")
                if fingerprint(des) != case["native_des_sha256"]:
                    raise ValueError("native DES changed")
                archive.write(des, f"{prefix}/native.des")
            if "native_material_sha256" in case:
                material = next((native_path.parent / "central/flopack/Library").glob("*.mat"))
                if fingerprint(material) != case["native_material_sha256"]:
                    raise ValueError("native constituent material changed")
                archive.write(material, f"{prefix}/constituent.mat")
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        # Include actual native command logs and run fingerprints; never config files.
        for run in native["native_run"]["runs"]:
            source = Path(run["executable"])
            if fingerprint(source) != run["executable_sha256"]:
                raise ValueError("native binary changed since replay")
        for root in {Path(c["native_path"]).parent for c in native["cases"]}:
            archive.write(root / "run.json", f"native-runs/{root.name}/run.json")
            for path in (root / "LogFiles").glob("*.xml"):
                archive.write(path, f"native-runs/{root.name}/{path.name}")
    source_hashes = {
        str(p.relative_to(ROOT)).replace("\\", "/"): fingerprint(p)
        for folder in [
            "src/packstudio",
            "default_parameters",
            "tools/floxml_validation",
            "tests/backend/templates",
        ]
        for p in (ROOT / folder).rglob("*")
        if p.suffix in {".py", ".json"}
    }
    executable = Path(native["native_run"]["runs"][0]["executable"])
    binary = pefile.PE(str(executable))
    version = next(
        table.entries[b"FileVersion"].decode()
        for group in binary.FileInfo
        for item in group
        for table in getattr(item, "StringTable", [])
        if b"FileVersion" in table.entries
    )
    result = {
        **native,
        "cases": cases,
        "counts": dict(Counter(c["status"] for c in cases)),
        "coverage": dict(Counter(c["kind"] for c in cases)),
        "limitations": LIMITATIONS,
        "source_sha256": source_hashes,
        "source_revision_scope": "source_commit is HEAD at execution; source hashes identify the "
        "working-tree source, including changes awaiting commit.",
        "source_normalized_sha256": {
            name: hashlib.sha256((ROOT / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            for name in source_hashes
        },
        "evidence_sha256": fingerprint(bundle),
        "native_file_version": version,
        "native_binary_sha256": {
            name: fingerprint(executable.parent / name)
            for name in ["flopackrealise.dll", "flopackfloxmlhandling.dll", "flopackmaterials.dll"]
        },
        "note": "Archive and final native batches combined; all exported files and native "
        "inputs re-fingerprinted while packaging. Counts are not independent experiments.",
    }
    result["tolerances"].update(clip_axis_mm=1e-10, power_abs_w=1e-10)
    result["contract_sha256"] = {
        p.name: fingerprint(p) for p in (ROOT / "output_format/floxml").glob("*.xsd")
    }
    (destination / "results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
    )
    _markdown(result, destination / "report.md")
    print(result["counts"], result["coverage"], bundle, flush=True)


def _markdown(result, path):
    categories = Counter(f["category"] for c in result["cases"] for f in c["findings"])
    lines = [
        "# FloXML 自动差异验证结果（2026-10-17）",
        "",
        f"实际运行 {len(result['cases'])} 个案例：{result['counts']}。",
        "这些案例含重复基准/关联单变量，数量不等于独立物理实验。",
        "",
        f"PACK：2504，flopack.exe {result['native_file_version']}；"
        "原生批次退出码为 0，日志无 ERROR。",
        "每案输入、路径、SHA-256、几何/物性差异和分类见 results.json 与 evidence.zip。",
        "",
        "## 覆盖",
        "",
        "| 类型 | 案例数 |",
        "| --- | ---: |",
    ]
    lines += [f"| {kind} | {count} |" for kind, count in result["coverage"].items()]
    lines += [
        "",
        "## 八类基准",
        "",
        "下表 PACK 采用项目声明的优先级做独立差集。带 collapsed 的原生实体仅使用名义包络，",
        "不代表求解器实际体积/优先级。Chip Array 的项目体积额外含声明的静态空气。",
        "",
        "| 模板 | PACK体积 mm³ | 项目体积 mm³ | PACK质量 mg | 项目质量 mg | 差异交叠区数 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for case in result["cases"]:
        if case["kind"] == "baseline":
            data = case["normalized"]
            left, right = data["pack"], data["packstudio"]
            lines.append(
                f"| {case['template']} | {left['volume_mm3']:.8g} | "
                f"{right['volume_mm3']:.8g} | {left['mass_kg'] * 1e6:.8g} | "
                f"{right['mass_kg'] * 1e6:.8g} | {case['difference_count']} |"
            )
    lines += ["", "## 分类计数", "", "同案可有多项归因，以下不能相加作为案例总数。", ""]
    lines += [f"- {category}: {count}" for category, count in categories.items()]
    lines += ["", "## 拒绝案例", ""]
    lines += [f"- `{c['id']}`：{c['error']}" for c in result["cases"] if c["status"] != "compared"]
    powered = [c for c in result["cases"] if c["kind"] == "power"]
    assert len(powered) == 8
    assert all(
        abs(c["power"]["pack_power_w"] - 2.5) < 1e-10
        and abs(c["power"]["packstudio_power_w"] - 2.5) < 1e-10
        for c in powered
    )
    lines += [
        "",
        "八类 2.5 W 案例的总功率全部守恒；PACK 面源与项目体源的空间分布不同。",
        "",
        "## 限制",
        "",
        "- 所有成功导出通过安装 XSD 与逐块坐标、材料绑定、张量、密度、比热、功率回读。",
        "- 原生 collapsed 实体、求解重叠优先级、实际导入与求解精度仍属证据边界。",
        "- 不覆盖全部 346 规格的笛卡尔积；离散/去球组合的完整 PACK 对照仍待扩展。",
        "- 已知问题的修复与剩余差异，以本次实际分类、专项说明及独立公式检查为准。",
        "",
        "方法、中文归因和复现命令见 [验证说明](../../research/floxml-validation.md)。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-output", type=Path, required=True)
    parser.add_argument("--native-output", type=Path, required=True)
    parser.add_argument("--destination", type=Path, default=ROOT / "docs/validation/floxml")
    args = parser.parse_args()
    publish(args.archive_output, args.native_output, args.destination)


if __name__ == "__main__":
    main()
