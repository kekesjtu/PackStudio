"""Read enum choices, wizard inputs and nested objects while native owners are alive."""

import ctypes
import os
import re
import struct
from pathlib import Path

from tools.pack_native import NativePack, cpp_string, object_type, property_map, virtual

EXTRA_BINARIES = {
    "flopackbackend.dll": "37177cc405980a1cbc22ef88a5d8a5af20264ba4a1ea731e331a0c96511656d5",
    "flopackmaterials.dll": "4fdd99632751f4e7c63a2bdc93e290a3bc9ca018bbe8b7921aa7025cedb3cda3",
    "flopackrealise.dll": "838ed6c2e7d40cc749b8b145f55d78e9e95495fef974d593a7641fc0aa528edd",
}


def vector_items(address: int, stride: int, limit: int = 100_000) -> range:
    begin, end = struct.unpack("<QQ", ctypes.string_at(address, 16))
    if end < begin or (end - begin) % stride or end - begin > limit * stride:
        raise ValueError("invalid native vector")
    return range(begin, end, stride)


class DetailedNativePack(NativePack):
    def __init__(self, installation: Path):
        self.shared_directory_handle = os.add_dll_directory(str(installation / "WinXP/64lib"))
        super().__init__(installation, EXTRA_BINARIES)
        self.pending_properties = {}
        self.wizard = {}
        self.pending_children = []

    def snapshot(self, path: Path, four_layer: bool = False) -> list[dict]:
        self.preset_path = path
        return super().snapshot(path, four_layer)

    def enum_details(self, prop: int) -> dict:
        match = re.fullmatch(r"\.\?AV(\w+)@(?:flopack|flodata)@@", object_type(prop))
        if not match:
            return {}
        symbol = f"?getEnumValueItems@{match[1]}@"
        names = [n for n in self.binaries["flopackproperties.dll"].exports if symbol in n]
        if not names or "JedecFootprint" in match[1]:
            return {}
        items = self.bind("flopackproperties.dll", symbol, ctypes.c_void_p, [ctypes.c_void_p])(
            prop
        )
        choices = [cpp_string(item) for item in vector_items(items, 88)]
        state = ctypes.c_uint32.from_address(prop + 8).value
        selected = ctypes.c_uint32.from_address(prop + 0x90).value if state else None
        if selected is not None and selected >= len(choices):
            raise ValueError(f"native enum outside its choices: {match[1]}")
        return {"enum_choices": choices, "enum_index": selected,
                "enum_label": choices[selected] if selected is not None else None}

    def capture_property(self, prop: int) -> None:
        details = self.enum_details(prop)
        kind = object_type(prop)
        if kind == ".?AVNonUniformDieHeatProperty@flopack@@":
            regions = vector_items(prop + 0x98, 8)
            matrix = vector_items(prop + 0xb0, 24)
            if regions or matrix:
                raise ValueError("nonempty heat-map layout needs independent verification")
            details["structured_value"] = {
                "native_mode": ctypes.c_uint64.from_address(prop + 0x90).value,
                "regions": [], "power_matrix": [],
            }
        if kind == ".?AVDepopulationProperty@flopack@@":
            details["structured_value"] = {"native_cell_list": [
                {"column": ctypes.c_int.from_address(item).value,
                 "row": ctypes.c_int.from_address(item + 4).value}
                for item in vector_items(prop + 0x90, 8)
            ]}
        if details:
            self.pending_properties[cpp_string(prop + 16)] = details

    def capture_wizard(self, wizard: int) -> None:
        self.wizard = {}
        for prop in property_map(wizard):
            name = cpp_string(prop + 16)
            if "Footprint" in name:
                continue
            details = self.enum_details(prop)
            if name in {"pqfpPackageType", "sopPackageType"}:
                prefix = self.preset_path.stem.split("_")[0].lower()
                label = "soic/sop/so" if prefix == "sop" else prefix
                selected = details["enum_choices"].index(label)
                virtual(prop, 18, None, [ctypes.c_void_p, ctypes.c_int])(prop, selected)
                details = self.enum_details(prop)
            value = details["enum_label"] if details else self.property_value(prop)
            self.wizard[name] = {"value": value, **details}

    def capture_dataset(self, dataset: int) -> None:
        self.pending_children = []
        if object_type(dataset) != ".?AVTopCoverDataSet@flopack@@":
            return
        for offset in (0x220, 0x980, 0x1f98):
            child = dataset + offset
            properties = []
            for prop in property_map(child):
                state = ctypes.c_uint32.from_address(prop + 8).value
                properties.append({
                    "name": cpp_string(prop + 16), "native_type": object_type(prop),
                    "native_state": state,
                    "value": self.property_value(prop) if state else None,
                    **self.enum_details(prop),
                })
            self.pending_children.append({
                "native_type": object_type(child),
                "properties": sorted(properties, key=lambda prop: prop["name"]),
            })

    def capture_group(self, package: int, index: int) -> dict:
        group = self.bind(
            "flopackpackages.dll",
            "?getDataGroup@FlopackPackage@flopack@@QEBAPEAVFlopackPackageDataGroup@2@_K",
            ctypes.c_void_p, [ctypes.c_void_p, ctypes.c_size_t],
        )(package, index)
        name_buffer = ctypes.create_string_buffer(32)
        virtual(group, 1, ctypes.c_void_p, [ctypes.c_void_p, ctypes.c_void_p])(
            group, ctypes.addressof(name_buffer)
        )
        try:
            name = cpp_string(ctypes.addressof(name_buffer))
        finally:
            if ctypes.c_size_t.from_buffer(name_buffer, 24).value >= 16:
                self.free_functions["flopackpackages.dll"](
                    ctypes.c_void_p.from_buffer(name_buffer).value
                )
        result = {
            "name": name, "group_native_type": object_type(group),
            "enabled": bool(virtual(group, 7, ctypes.c_bool, [ctypes.c_void_p])(group)),
            "group_valid": bool(virtual(group, 6, ctypes.c_bool, [ctypes.c_void_p])(group)),
            "property_details": self.pending_properties,
            "children": self.pending_children,
        }
        self.pending_properties = {}
        if object_type(group) == ".?AVQFNModelingOptions@flopack@@":
            result["effective_parameters"] = {
                "numberOfDiscreteBondwireSteps": self.bind(
                    "flopackpackages.dll", "?getNumberOfDiscreteBondwireSteps@QFNModelingOptions@",
                    ctypes.c_int, [ctypes.c_void_p],
                )(group)
            }
        if object_type(group) == ".?AVSolderBallsDataGroup@flopack@@":
            address = self.bind(
                "flopackpackages.dll", "?getSolderBallMap@", ctypes.c_void_p,
                [ctypes.c_void_p],
            )(group)
            result["solder_ball_map"] = [
                {"name": cpp_string(item),
                 "x_m": ctypes.c_double.from_address(item + 32).value,
                 "y_m": ctypes.c_double.from_address(item + 40).value}
                for item in vector_items(address, 48)
            ]
        return result

    def metal_layers(self, package: int, index: int) -> list[dict] | None:
        rows = super().metal_layers(package, index)
        if rows is not None:
            return rows
        group = self.bind(
            "flopackpackages.dll",
            "?getDataGroup@FlopackPackage@flopack@@QEBAPEAVFlopackPackageDataGroup@2@_K",
            ctypes.c_void_p, [ctypes.c_void_p, ctypes.c_size_t],
        )(package, index)
        if object_type(group) != ".?AVFlipChipPBGABuiltUpRegion@flopack@@":
            return None
        vector = self.bind(
            "flopackpackages.dll", "?getMetalLayerRows@MetalLayersDataGroup@", ctypes.c_void_p,
            [ctypes.c_void_p],
        )(group)
        return [
            dict(zip(("depth_m", "thickness_m", "coverage_percent"),
                     (value if value > -1e307 else None for value in
                      struct.unpack("<ddd", ctypes.string_at(item, 24))), strict=True))
            for item in vector_items(vector, 24)
        ]
