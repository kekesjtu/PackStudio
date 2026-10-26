"""Compile per-preset documents and a separately classified named material library."""

import hashlib
import json
import re
from pathlib import Path

from tools.pack_reference.catalog_properties import metal_rows, property_record, wizard_record
from tools.pack_reference.native import VERIFIED_BINARIES
from tools.pack_reference.native_details import EXTRA_BINARIES

PRESET_SCHEMA = "packstudio.preset/v1"
MATERIAL_SCHEMA = "packstudio.material/v1"
CATEGORIES = {
    "Resins": "resins",
    "Alloys (Leadframe)": "leadframe_alloys",
    "Attachment Materials": "attachment_materials",
    "Alloys (Other)": "other_alloys",
    "Metals": "metals",
    "Ceramics": "ceramics",
    "Alloys (Solders)": "solder_alloys",
    "Substrate Dielectrics": "substrate_dielectrics",
    "Others": "others",
    "Semiconductors": "semiconductors",
}


def write_json(path: Path, payload: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def material_record(raw: dict) -> dict:
    kind = raw["conductivity_type"]
    if kind == 2:
        conductivity = {
            "model": "orthotropic",
            "unit": "W/(m*K)",
            "x": raw["kx_w_m_k"],
            "y": raw["ky_w_m_k"],
            "z": raw["kz_w_m_k"],
            "comment": "原生正交导热张量；此类型不使用标量导热率及温度系数存储。",
        }
    elif kind in {0, 1}:
        conductivity = {
            "model": "constant_isotropic" if kind == 0 else "temperature_dependent",
            "unit": "W/(m*K)",
            "value": raw["conductivity_w_m_k"],
            "comment": "原生各向同性材料；kx/ky/kz 存储中的0不是三个方向的物理导热率。",
        }
        if kind == 1:
            conductivity.update(
                coefficient=raw["conductivity_coefficient"],
                reference_temperature=raw["conductivity_reference_temperature"],
                comment="原生温度相关各向同性材料；完整保留基准值、系数、参考温度，不简化为常数。",
            )
    else:
        raise ValueError(f"unreviewed material conductivity type: {kind}")
    return {
        "schema_version": MATERIAL_SCHEMA,
        "name": raw["name"],
        "category": raw["group"],
        "density": {"value": raw["density_kg_m3"], "unit": "kg/m^3"},
        "specific_heat": {"value": raw["specific_heat_j_kg_k"], "unit": "J/(kg*K)"},
        "emissivity": raw["emissivity"],
        "conductivity": conductivity,
        "native_storage": raw,
        "source": {
            "method": "MaterialLibrary::populateBuiltInMaterials; native getters",
            "binary_sha256": EXTRA_BINARIES,
        },
        "comment": (
            "PACK 2504 内建材料；未读取用户材料文件。native_storage 中非当前类型字段只是原生存储。"
        ),
    }


def write_materials(directory: Path, materials: list[dict]) -> set[str]:
    index = {}
    for raw in materials:
        name = raw["name"]
        if name in index:
            raise ValueError(f"duplicate material name: {name}")
        stem = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
        stem += "_" + hashlib.sha256(name.encode()).hexdigest()[:8]
        relative = f"{CATEGORIES[raw['group']]}/{stem}.json"
        digest = write_json(directory / "materials" / relative, material_record(raw))
        index[name] = {"file": relative, "sha256": digest, "category": raw["group"]}
    write_json(
        directory / "materials/index.json",
        {
            "schema_version": "packstudio.material-index/v1",
            "material_count": len(index),
            "comment": "预设通过完整材料名称引用；名称是唯一键，目录与文件名仅用于分类存储。",
            "materials": index,
        },
    )
    return set(index)


def compiled_group(group: dict, family: str, groups: list[dict]) -> dict:
    result = {
        "name": group["name"],
        "enabled": group["enabled"],
        "native_valid": group["group_valid"],
        "native_type": group["native_type"],
        "comment": "保留原生组开关与校验结果；未启用组仍保存已有子参数。",
        "properties": {
            p["name"]: property_record(p, group, family, groups) for p in group["properties"]
        },
    }
    if group["name"] == "die":
        result["properties"]["dieMaterial"] = {
            "status": "fixed",
            "kind": "material_reference",
            "value": "Silicon (Pure)",
            "comment": (
                "几何实现中固定使用 Silicon (Pure)，并非 .des 或数据集中的可编辑项。"
                "已确认 realise RVA 0xc0e0/0xf700/0x28250/0x43210 的常量及材料创建调用。"
            ),
        }
    if group.get("metal_layer_rows") is not None:
        result["metal_layers"] = metal_rows(group, groups)
        result["comment"] += (
            " 内层深度来自原生表，不重算层间距；4层向导使用gap=(A2-top-bottom-2*solid)/3，"
            "depth1=top+gap，depth2=top+2*gap。"
        )
    if group.get("children"):
        selection = result["properties"]["topCover"]["value"]
        children = {}
        for child, name in zip(group["children"], ("encapsulant", "lid", "plate"), strict=True):
            proxy = {
                **child,
                "name": name,
                "enabled": name == selection,
                "property_details": {p["name"]: p for p in child["properties"]},
            }
            children[name] = {
                "enabled": name == selection,
                "native_type": child["native_type"],
                "properties": {
                    p["name"]: property_record(p, proxy, family, groups)
                    for p in child["properties"]
                },
                "comment": "来自 TopCoverDataSet 嵌套对象，保留未选顶盖分支的原生参数。",
            }
        result["children"] = children
    return result


def material_names(payload) -> set[str]:
    result = set()
    if isinstance(payload, dict):
        if payload.get("kind") == "material_reference" and payload.get("value"):
            result.add(payload["value"])
        for value in payload.values():
            result.update(material_names(value))
    elif isinstance(payload, list):
        for value in payload:
            result.update(material_names(value))
    return result


def compiled_branch(snapshot: dict) -> dict:
    groups = snapshot["groups"]
    return {
        "wizard": {name: wizard_record(name, p) for name, p in snapshot["wizard"].items()},
        "groups": {g["name"]: compiled_group(g, snapshot["family"], groups) for g in groups},
    }


def write_presets(
    directory: Path, records: list[dict], source_records: dict, materials: set[str]
) -> None:
    index = {}
    for record in records:
        family, stem = record["family"], record["preset"]
        key = (family, stem)
        source = source_records[key]
        branches = {"default": compiled_branch(record)}
        if record.get("four_layer"):
            branches["four_layer"] = compiled_branch(record["four_layer"])
        references = sorted(material_names(branches))
        if missing := set(references) - materials:
            raise ValueError(f"unresolved materials in {key}: {missing}")
        payload = {
            "schema_version": PRESET_SCHEMA,
            "id": stem,
            "family": family,
            "default_branch": "default",
            "branches": branches,
            "material_references": references,
            "source": {
                "path": source["source_path"],
                "sha256": source["source_sha256"],
                "des_fields": source["raw_fields"],
                "comment": (
                    "原文本完整无损保留用于追溯；运行参数读取 branches，不能把源空字符串当默认值。"
                ),
                "binary_sha256": VERIFIED_BINARIES | EXTRA_BINARIES,
            },
            "comment": (
                "一个文件保存预设的原生默认向导参数、子对象、材料名称和计算结果。"
                "ChipArray/WB 同时保存四层分支。未指定器件限值及未启用结构没有虚构数值；"
                "通过 status/comment 表明语义。没有继承项目模板兜底值。"
            ),
        }
        relative = f"{family}/{stem}.json"
        digest = write_json(directory / "presets" / relative, payload)
        if stem in index:
            raise ValueError(f"duplicate preset id: {stem}")
        index[stem] = {
            "family": family,
            "file": relative,
            "sha256": digest,
            "branches": list(branches),
        }
    write_json(
        directory / "presets/index.json",
        {
            "schema_version": "packstudio.preset-index/v1",
            "preset_count": len(index),
            "comment": "每个预设独立文件；材料从 materials/index.json 按名称解析。",
            "presets": index,
        },
    )
