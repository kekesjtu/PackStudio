"""Inspect symbols and bounded functions without loading or modifying PACK DLLs."""

import argparse
from pathlib import Path

from tools.pack_binary import PackBinary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("--symbol", help="Exported symbol substring; must resolve uniquely")
    parser.add_argument("--rva", type=lambda value: int(value, 0))
    arguments = parser.parse_args()
    binary = PackBinary(arguments.binary)
    if arguments.rva is not None:
        address = arguments.rva
    elif arguments.symbol:
        matches = [(name, rva) for name, rva in binary.exports.items() if arguments.symbol in name]
        if len(matches) != 1:
            for name, rva in matches:
                print(f"{rva:#x} {name}")
            raise SystemExit("symbol must resolve uniquely; use --rva to select")
        address = matches[0][1]
    else:
        for name, rva in sorted(binary.exports.items(), key=lambda item: item[1]):
            print(f"{rva:#x} {name}")
        return
    for instruction in binary.instructions(address):
        print(binary.annotate(instruction))


if __name__ == "__main__":
    main()
