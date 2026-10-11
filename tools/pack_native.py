"""Version-guarded access to PACK's in-memory parameter objects, without its UI."""

import ctypes
import hashlib
import os
import struct
from pathlib import Path

from tools.pack_binary import PackBinary

VERIFIED_BINARIES = {
    "flopackdatasets.dll": "43312861dc31e9936bb407104292ce42ef7690a7183f44cd10b969fc8679b4a9",
    "flopackdes.dll": "2ad00011d2399629ea076f350f643973117e452eab8f2d313b64dbb9b49e961e",
    "flopackpackages.dll": "f0a6363dad8e2be5020d9e8704ec427ef9c669218889e202a7228650b883123c",
    "flopackproperties.dll": "b1e37b8db2d2de4fe4fec8781c9051a2b4704827743d5132f08729d3f1acf38a",
}
FAMILIES = {
    "chip_array": (0, "ChipArray"),
    "cbga_fc": (2, "FlipChipCBGA"),
    "pbga_fc": (3, "FlipChipPBGA"),
    "pqfp": (4, "PQFP"),
    "QFN": (5, "QFN"),
    "tsop_conv": (6, "SOP"),
    "pbga_wb": (7, "WirebondPBGA"),
}


def cpp_string(address: int) -> str:
    size, capacity = struct.unpack("<QQ", ctypes.string_at(address + 16, 16))
    if size > 1_000_000 or capacity < size:
        raise ValueError("invalid MSVC string layout")
    data = address if capacity < 16 else ctypes.c_void_p.from_address(address).value
    return ctypes.string_at(data, size).decode("utf-8", errors="replace")


def object_type(address: int) -> str:
    table = ctypes.c_void_p.from_address(address).value
    locator = ctypes.c_void_p.from_address(table - 8).value
    base = locator - ctypes.c_uint32.from_address(locator + 20).value
    descriptor = ctypes.c_uint32.from_address(locator + 12).value
    return ctypes.string_at(base + descriptor + 16).decode()


def virtual(address: int, slot: int, result, arguments):
    table = ctypes.c_void_p.from_address(address).value
    target = ctypes.c_void_p.from_address(table + slot * 8).value
    return ctypes.CFUNCTYPE(result, *arguments)(target)


def destroy(address: int) -> None:
    virtual(address, 0, None, [ctypes.c_void_p, ctypes.c_uint32])(address, 1)


def property_map(dataset: int) -> list[int]:
    """Walk the DataSet's MSVC map<int, Property*>; all pointers are borrowed."""
    head = ctypes.c_void_p.from_address(dataset + 8).value
    nodes = [ctypes.c_void_p.from_address(head + 8).value]
    visited = set()
    properties = []
    while nodes:
        node = nodes.pop()
        if node == head or node in visited:
            continue
        if not node or len(visited) > 10_000:
            raise ValueError("invalid MSVC property map")
        visited.add(node)
        nodes.extend(ctypes.c_void_p.from_address(node + offset).value for offset in (0, 16))
        properties.append(ctypes.c_void_p.from_address(node + 40).value)
    return properties


class NativePack:
    def __init__(self, installation: Path):
        if os.name != "nt" or ctypes.sizeof(ctypes.c_void_p) != 8:
            raise RuntimeError("the native probe requires 64-bit Windows")
        self.installation = installation.resolve()
        directory = self.installation / "WinXP/bin"
        # Reject other builds before executing any DLL: layouts and virtual slots vary.
        for name, digest in VERIFIED_BINARIES.items():
            if hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
                raise ValueError(f"unreviewed PACK binary: {name}")
        self.directory_handle = os.add_dll_directory(str(directory))
        self.binaries = {name: PackBinary(directory / name) for name in VERIFIED_BINARIES}
        self.libraries = {name: ctypes.CDLL(str(directory / name)) for name in VERIFIED_BINARIES}
        self.bound = {}
        self.free_functions = {}
        for name, binary in self.binaries.items():
            slot = next(
                address for address, item in binary.imports.items() if item.endswith("!free")
            )
            target = ctypes.c_void_p.from_address(
                self.libraries[name]._handle + slot - binary.base
            ).value
            self.free_functions[name] = ctypes.CFUNCTYPE(None, ctypes.c_void_p)(target)

    def bind(self, library: str, match: str, result, arguments):
        key = (library, match)
        if key not in self.bound:
            names = [name for name in self.binaries[library].exports if match in name]
            if len(names) != 1:
                raise ValueError(f"ambiguous native symbol {match}: {names}")
            function = getattr(self.libraries[library], names[0])
            function.restype = result
            function.argtypes = arguments
            self.bound[key] = function
        return self.bound[key]

    def property_value(self, prop: int) -> str:
        output = ctypes.create_string_buffer(32)
        address = ctypes.addressof(output)
        self.bind(
            "flopackdes.dll",
            "?desStringFromProperty@",
            ctypes.c_void_p,
            [ctypes.c_void_p, ctypes.c_void_p],
        )(address, prop)
        try:
            return cpp_string(address)
        finally:
            if ctypes.c_size_t.from_address(address + 24).value >= 16:
                self.free_functions["flopackdes.dll"](ctypes.c_void_p.from_address(address).value)

    def load(self, path: Path) -> int:
        path_text = str(path.resolve())
        text = ctypes.create_unicode_buffer(path_text)
        # boost::filesystem::path wraps an MSVC wstring; input storage remains Python-owned.
        wrapper = ctypes.create_string_buffer(32)
        struct.pack_into(
            "<Q8xQQ", wrapper, 0, ctypes.addressof(text), len(path_text), len(path_text)
        )
        package = self.bind(
            "flopackdes.dll", "?loadDESPackage@", ctypes.c_void_p, [ctypes.c_void_p]
        )(ctypes.addressof(wrapper))
        if not package:
            raise ValueError(f"PACK rejected {path}")
        return package

    def apply_wizard(self, package: int, class_name: str, four_layer: bool = False) -> None:
        storage = ctypes.create_string_buffer(65_536)
        wizard = ctypes.addressof(storage)
        name = f"{class_name}WizardPackageDataSet"
        self.bind(
            "flopackdatasets.dll",
            f"??0{name}@flopack@@QEAA@XZ",
            ctypes.c_void_p,
            [ctypes.c_void_p],
        )(wizard)
        try:
            self.bind("flopackdatasets.dll", f"?initialise@{name}@", None, [ctypes.c_void_p])(
                wizard
            )
            if four_layer:
                prop = self.bind(
                    "flopackdatasets.dll",
                    f"?getSubstrateLayerEnum@{name}@",
                    ctypes.c_void_p,
                    [ctypes.c_void_p],
                )(wizard)
                choice = ctypes.create_string_buffer(32)
                # DES enum numbers include the native index origin (usually one).
                origin = ctypes.c_int.from_address(prop + 0x128).value
                encoded = str(1 + origin).encode("ascii")
                ctypes.memmove(choice, encoded, len(encoded))
                struct.pack_into("<QQ", choice, 16, len(encoded), 15)
                self.bind(
                    "flopackproperties.dll",
                    "?valueFromDesString@FlopackEnumValue@",
                    None,
                    [ctypes.c_void_p, ctypes.c_void_p],
                )(prop, ctypes.addressof(choice))
                if ctypes.c_int.from_address(prop + 0x90).value != 1:
                    raise ValueError("PACK did not accept the 4-Layer wizard option")
            # BackendCtrl::createPackage invokes this same virtual slot after DES loading.
            virtual(package, 2, None, [ctypes.c_void_p, ctypes.c_void_p])(package, wizard)
        finally:
            self.bind("flopackdatasets.dll", f"??1{name}@", None, [ctypes.c_void_p])(wizard)

    def snapshot(self, path: Path, four_layer: bool = False) -> list[dict]:
        package_type, class_name = FAMILIES[path.parent.name]
        if four_layer and class_name not in {"ChipArray", "WirebondPBGA"}:
            raise ValueError("4-Layer is supported only for ChipArray and WirebondPBGA")
        package = self.load(path)
        try:
            if object_type(package) != f".?AV{class_name}Package@flopack@@":
                raise ValueError(f"unexpected package type in {path}")
            self.apply_wizard(package, class_name, four_layer)
            count = self.bind(
                "flopackdatasets.dll", "?getNumberOfDataSets@", ctypes.c_int, [ctypes.c_int]
            )(package_type)
            groups = []
            for index in range(count):
                dataset = self.bind(
                    "flopackdatasets.dll",
                    "?createPackageDataSet@",
                    ctypes.c_void_p,
                    [ctypes.c_int, ctypes.c_size_t],
                )(package_type, index)
                if not dataset:
                    raise ValueError(f"missing PACK data set {package_type}/{index}")
                try:
                    self.bind(
                        "flopackpackages.dll",
                        "?getData@FlopackPackage@flopack@@QEBAXPEAV",
                        None,
                        [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t],
                    )(package, dataset, index)
                    properties = []
                    for prop in property_map(dataset):
                        state = ctypes.c_uint32.from_address(prop + 8).value
                        if state not in {0, 1, 2, 3, 4}:
                            raise ValueError(f"unreviewed native property state: {state}")
                        # Native serialization of an unset numeric property reads uninitialised
                        # storage. Such bytes are not defaults and must never enter the snapshot.
                        value = self.property_value(prop) if state != 0 else None
                        properties.append(
                            {
                                "name": cpp_string(prop + 16),
                                "value": value,
                                "native_type": object_type(prop),
                                "native_state": state,
                            }
                        )
                    groups.append(
                        {
                            "index": index,
                            "native_type": object_type(dataset),
                            "properties": sorted(properties, key=lambda item: item["name"]),
                            "metal_layer_rows": self.metal_layers(package, index),
                        }
                    )
                finally:
                    destroy(dataset)
            return groups
        finally:
            destroy(package)

    def metal_layers(self, package: int, index: int) -> list[dict] | None:
        group = self.bind(
            "flopackpackages.dll",
            "?getDataGroup@FlopackPackage@flopack@@QEBAPEAVFlopackPackageDataGroup@2@_K",
            ctypes.c_void_p,
            [ctypes.c_void_p, ctypes.c_size_t],
        )(package, index)
        kind = object_type(group)
        classes = {
            ".?AVChipArrayMetalLayers@flopack@@": ("ChipArrayMetalLayers", 24),
            ".?AVWirebondPBGAMetalLayers@flopack@@": ("WirebondPBGAMetalLayers", 32),
            ".?AVFlipChipPBGAMetalLayers@flopack@@": ("MetalLayersDataGroup", 24),
        }
        if kind not in classes:
            return None
        name, stride = classes[kind]
        vector = self.bind(
            "flopackpackages.dll",
            f"?getMetalLayerRows@{name}@",
            ctypes.c_void_p,
            [ctypes.c_void_p],
        )(group)
        begin, end = struct.unpack("<QQ", ctypes.string_at(vector, 16))
        if (end - begin) % stride or not 0 <= end - begin <= 32_000:
            raise ValueError("invalid native metal-layer table")
        rows = []
        for address in range(begin, end, stride):
            depth, thickness, coverage = struct.unpack("<ddd", ctypes.string_at(address, 24))
            row = {
                "depth_m": depth if depth > -1e307 else None,
                "thickness_m": thickness if thickness > -1e307 else None,
                "coverage_percent": coverage if coverage > -1e307 else None,
            }
            if stride == 32:
                row["disconnect_to_vias"] = bool(ctypes.c_ubyte.from_address(address + 24).value)
            rows.append(row)
        return rows
