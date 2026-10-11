"""Read-only PE inspection helpers for the installed PACK binaries."""

import hashlib
import struct
from pathlib import Path

import pefile
from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP


class PackBinary:
    def __init__(self, path: Path):
        self.path = path
        self.data = path.read_bytes()
        self.sha256 = hashlib.sha256(self.data).hexdigest()
        self.pe = pefile.PE(data=self.data)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.image = self.pe.get_memory_mapped_image()
        self.decoder = Cs(CS_ARCH_X86, CS_MODE_64)
        self.decoder.detail = True
        self.exports = {
            symbol.name.decode(): symbol.address
            for symbol in self.pe.DIRECTORY_ENTRY_EXPORT.symbols
            if symbol.name
        }
        self.names = {}
        for name, address in self.exports.items():
            self.names.setdefault(self.base + address, []).append(name)
        self.imports = {
            symbol.address: f"{entry.dll.decode()}!{symbol.name.decode()}"
            for entry in self.pe.DIRECTORY_ENTRY_IMPORT
            for symbol in entry.imports
            if symbol.name
        }
        self.functions = {
            entry.struct.BeginAddress: entry.struct.EndAddress
            for entry in self.pe.DIRECTORY_ENTRY_EXCEPTION
        }

    def read(self, address: int, size: int) -> bytes:
        offset = address - self.base
        if offset < 0 or offset + size > len(self.image):
            raise ValueError(f"address outside {self.path.name}: {address:#x}")
        return self.image[offset : offset + size]

    def string(self, address: int) -> str | None:
        offset = address - self.base
        if not 0 <= offset < len(self.image):
            return None
        value = self.image[offset : offset + 160].split(b"\0", 1)[0]
        if len(value) >= 2 and all(32 <= byte < 127 for byte in value):
            return value.decode()
        return None

    def instructions(self, rva: int):
        end = self.functions.get(rva)
        if end is None:
            boundaries = set(self.functions) | set(self.exports.values())
            end = min([start for start in boundaries if start > rva] or [rva + 256])
        return list(self.decoder.disasm(self.image[rva:end], self.base + rva))

    def rip_targets(self, instruction):
        return [
            instruction.address + instruction.size + operand.mem.disp
            for operand in instruction.operands
            if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP
        ]

    def call_name(self, instruction) -> str | None:
        if instruction.mnemonic not in {"call", "jmp"}:
            return None
        operand = instruction.operands[0]
        if operand.type == X86_OP_IMM:
            return (
                " / ".join(self.names.get(operand.imm, [])) or f"local:{operand.imm - self.base:#x}"
            )
        targets = self.rip_targets(instruction)
        return self.imports.get(targets[0]) if targets else None

    def annotate(self, instruction) -> str:
        annotations = []
        name = self.call_name(instruction)
        if name:
            annotations.append(name)
        for target in self.rip_targets(instruction):
            value = self.string(target)
            if value:
                annotations.append(repr(value))
            elif instruction.mnemonic.endswith("sd") and instruction.mnemonic != "cvtsi2sd":
                annotations.append(f"double={struct.unpack('<d', self.read(target, 8))[0]:.16g}")
        suffix = f" ; {'; '.join(annotations)}" if annotations else ""
        prefix = f"{instruction.address - self.base:08x}  {instruction.mnemonic}"
        return f"{prefix} {instruction.op_str}{suffix}"
