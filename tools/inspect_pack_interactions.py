"""Save bounded disassembly and getter call sites relevant to parameter coupling."""

import argparse
from pathlib import Path

from tools.pack_binary import PackBinary
from tools.pack_catalog_builder import write_json

GETTERS = (
    "getNumberOfBondWires",
    "getBondWireLength",
    "getPlatingThicknessTpl",
    "getMetalCoverageForDieFlagCf",
    "getNumberBondWiresEqualsSolderBalls",
    "getDieAttachThicknessTda",
    "getTotalNumberOfLeadsMT",
)
FUNCTIONS = (
    "?setWizardData@WirebondPBGAPackage@",
    "?setDieTypeData@WirebondPBGAPackage@",
    "?setTopCoverData@FlipChipCBGAPackage@",
    "?setTopCoverData@FlipChipPBGAPackage@",
    "?setData@DieAndAttachDataGroup@",
    "?groupValid@FlipChipBumpsDataGroup@",
    "?groupValid@SolderBallsDataGroup@",
    "?groupValid@ChipArrayVias@",
    "?groupValid@ThermalViasDataGroup@",
    "?setData@FlopackPackage@flopack@@QEAAXPEAV",
)


def inspect(installation: Path) -> dict:
    packages = PackBinary(installation / "WinXP/bin/flopackpackages.dll")
    realize = PackBinary(installation / "WinXP/bin/flopackrealise.dll")
    bounded = []
    for match in FUNCTIONS:
        symbols = [(name, rva) for name, rva in packages.exports.items() if match in name]
        if len(symbols) != 1:
            raise ValueError(f"ambiguous evidence symbol: {match}")
        name, rva = symbols[0]
        bounded.append(
            {
                "symbol": name,
                "rva": hex(rva),
                "instructions": [packages.annotate(i) for i in packages.instructions(rva)],
            }
        )
    references = []
    for rva in realize.functions:
        instructions = realize.instructions(rva)
        for index, instruction in enumerate(instructions):
            name = realize.call_name(instruction)
            if name and any(term in name for term in GETTERS):
                references.append(
                    {
                        "caller_rva": hex(rva),
                        "call_rva": hex(instruction.address - realize.base),
                        "target": name,
                        "instructions": [
                            realize.annotate(i) for i in instructions[max(0, index - 5) : index + 7]
                        ],
                    }
                )
    return {
        "schema_version": "packstudio.pack-interaction-disassembly/v1",
        "binary_sha256": {b.path.name: b.sha256 for b in (packages, realize)},
        "package_functions": bounded,
        "realization_getter_references": references,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("installation", type=Path)
    parser.add_argument(
        "--output", type=Path, default=Path("docs/validation/pack_interaction_disassembly.json")
    )
    args = parser.parse_args()
    evidence = inspect(args.installation)
    write_json(args.output, evidence)
    for row in evidence["realization_getter_references"]:
        print(f"{row['caller_rva']} -> {row['target']}")


if __name__ == "__main__":
    main()
