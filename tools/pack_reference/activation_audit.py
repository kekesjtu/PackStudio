"""Audit FC PBGA activation properties, virtual methods and archived geometry.

Run with --root REFERENCE_TREE --work NEW_TEMP_DIRECTORY --output REPORT_JSON.
The reference tree is read-only; the report records input paths and DLL versions.
"""

import argparse
import ctypes
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from tools.floscript.environment import INSTALLATION
from tools.pack_reference.interactions import InteractionNativePack
from tools.pack_reference.native import cpp_string, object_type, property_map

GROUPS = {"coreVias", "upperBuiltUpRegion", "lowerBuiltUpRegion"}
SCENARIOS = ["activation-default", "core-defined", "core-zero-count"] + [
    f"{region}-{state}"
    for region in ("upper", "lower")
    for state in ("region-only", "zero-count", "defined")
]


class ActivationProbe(InteractionNativePack):
    def capture_wizard(self, wizard):
        super().capture_wizard(wizard)
        self.wizard_inventory = [
            {"name": cpp_string(p + 16), "native_type": object_type(p)}
            for p in property_map(wizard)
        ]

    def capture_group(self, package, index):
        result = super().capture_group(package, index)
        if result["name"] not in GROUPS:
            return result
        group = self.bind(
            "flopackpackages.dll",
            "?getDataGroup@FlopackPackage@flopack@@QEBAPEAVFlopackPackageDataGroup@2@_K",
            ctypes.c_void_p,
            [ctypes.c_void_p, ctypes.c_size_t],
        )(package, index)
        table = ctypes.c_void_p.from_address(group).value
        binary = self.binaries["flopackpackages.dll"]
        base = self.libraries["flopackpackages.dll"]._handle
        methods = {}
        for label, slot in [("groupValid", 6), ("isEnabled", 7)]:
            address = ctypes.c_void_p.from_address(table + slot * 8).value
            rva = address - base
            methods[label] = {
                "slot": slot,
                "rva": hex(rva),
                "symbols": binary.names.get(binary.base + rva, []),
                "first_bytes": binary.read(binary.base + rva, 16).hex(),
                "instructions": [binary.annotate(i) for i in binary.instructions(rva)],
            }
        result["virtual_methods"] = methods
        return result


def audit(root, work, installation=INSTALLATION):
    work.mkdir(parents=True, exist_ok=False)
    inputs = work / "pbga_fc"
    inputs.mkdir()
    native = ActivationProbe(installation)
    snapshots = []
    for scenario in SCENARIOS:
        relative = f"packages/pbga_fc/cases/field_{scenario.replace('-', '_')}"
        source = root / relative
        copied = inputs / (scenario + ".des")
        with ZipFile(source / "model.des") as archive:
            members = [n for n in archive.namelist() if n.lower().endswith(".des")]
            if len(members) != 1:
                raise ValueError(f"expected one parameter member: {source}")
            copied.write_bytes(archive.read(members[0]))
        snapshot = native.probe(copied)
        selected = [g for g in snapshot["groups"] if g["name"] in GROUPS]
        for g in selected:
            g["index"] = next(x["index"] for x in snapshot["groups"] if x["name"] == g["name"])
        geometry = ET.parse(source / "model.xml").getroot()
        relevant = [
            e
            for e in geometry.findall(".//cuboid")
            if (e.findtext("name") or "").startswith(
                ("core_vias", "upper_region", "lower_region", "microvias")
            )
        ]
        snapshots.append(
            {
                "point": relative,
                "files": ["model.des", "model.xml", "script.xml", "case.json"],
                "wizard_property_inventory": native.wizard_inventory,
                "all_dataset_property_names": {
                    g["name"]: [p["name"] for p in g["properties"]] for g in snapshot["groups"]
                },
                "nested_dataset_property_names": {
                    g["name"]: [
                        {
                            "native_type": c["native_type"],
                            "properties": [p["name"] for p in c["properties"]],
                        }
                        for c in g.get("children", [])
                    ]
                    for g in snapshot["groups"]
                    if g.get("children")
                },
                "groups": selected,
                "geometry": [
                    {"name": e.findtext("name"), "material": e.findtext("material")}
                    for e in relevant
                ],
            }
        )
        expected_valid = {g: False for g in GROUPS}
        if scenario.startswith("core-"):
            expected_valid["coreVias"] = True
        for region in ("upper", "lower"):
            if scenario.startswith(region + "-"):
                expected_valid[region + "BuiltUpRegion"] = True
        for g in selected:
            if not g["enabled"] or g["group_valid"] != expected_valid[g["name"]]:
                raise ValueError(f"activation state differs: {scenario}/{g['name']}")
            if g["virtual_methods"]["isEnabled"]["rva"] != "0x22000":
                raise ValueError(
                    "group enable method differs from the reviewed constant implementation"
                )
        names = [e.findtext("name") for e in relevant]
        expected_count = 12 if scenario == "core-defined" else 0
        if scenario.startswith(("upper-", "lower-")):
            expected_count = 1 if scenario.endswith("region-only") else 2
        if len(names) != expected_count:
            raise ValueError(f"activation geometry differs: {scenario}: {names}")

    binary = native.binaries["flopackrealise.dll"]
    guard = binary.instructions(0x24460)
    gate = [binary.annotate(i) for i in guard[:19]]
    callsites = []
    instructions = binary.instructions(0x10ED0)
    for ix, instruction in enumerate(instructions):
        if instruction.mnemonic == "call" and instruction.op_str == hex(binary.base + 0x24460):
            before = instructions[max(0, ix - 3) : ix]
            if any(
                i.mnemonic == "mov" and i.op_str in {"edx, 4", "edx, 6", "edx, 7"} for i in before
            ):
                callsites.append(
                    [binary.annotate(i) for i in instructions[max(0, ix - 3) : ix + 10]]
                )
    return {
        "schema": "packstudio.native-activation-audit/v1",
        "installation": str(installation),
        "binary_sha256": {name: b.sha256 for name, b in native.binaries.items()},
        "probe_method": (
            "extract the archived DES parameter member; load with native loadDESPackage; "
            "apply default FC wizard; enumerate all datasets and wizard properties; "
            "resolve vtable slots 6/7"
        ),
        "scope": (
            "FC PBGA coreVias, upperBuiltUpRegion and lowerBuiltUpRegion "
            "in the hash-guarded PACK 2504 build"
        ),
        "assertions": {
            "scenario_count": len(snapshots),
            "group_enable_constant": True,
            "validity_states_match": True,
            "geometry_counts_match": True,
        },
        "realise_validity_guard": {
            "library": "flopackrealise.dll",
            "rva": "0x24460",
            "instructions": gate,
        },
        "realise_callsites": {
            "library": "flopackrealise.dll",
            "function_rva": "0x10ed0",
            "groups": {"4": "coreVias", "6": "upperBuiltUpRegion", "7": "lowerBuiltUpRegion"},
            "instructions": callsites,
        },
        "snapshots": snapshots,
        "interpretation": {
            "independent_properties": (
                "No one-to-one editable activation boolean was found "
                "in the full dataset/wizard inventories."
            ),
            "isEnabled": (
                "All three groups resolve slot 7 to flopackpackages.dll "
                "RVA 0x22000 (mov al,1; ret). This is constant availability, not user input."
            ),
            "realisation": (
                "The FC geometry dispatch checks groupValid through slot 6 before generating "
                "groups 4,6,7; validity checks parameter definition rather than "
                "an independent activation flag."
            ),
            "count_zero": (
                "Core zero row/column counts produce no core_vias blocks. A built-up region "
                "with zero microvia count still produces its region and an equivalent microvia "
                "block; zero is not a region disable flag."
            ),
            "limits": (
                "Findings describe this binary build and these interfaces; groupValid is not "
                "a substitute for complete physical validation."
            ),
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--installation", type=Path, default=INSTALLATION)
    args = parser.parse_args()
    result = audit(args.root.resolve(), args.work.resolve(), args.installation.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Audited {len(result['snapshots'])} native activation scenarios: {args.output}")


if __name__ == "__main__":
    main()
