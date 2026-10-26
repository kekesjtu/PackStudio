"""Replay wizard choices and scalar dataset edits in the hash-guarded PACK build."""

import ctypes
import struct
from pathlib import Path

from tools.pack_reference.native import (
    FAMILIES,
    cpp_string,
    destroy,
    object_type,
    property_map,
    virtual,
)
from tools.pack_reference.native_details import DetailedNativePack


class InteractionNativePack(DetailedNativePack):
    def probe(self, path: Path, *, wizard: dict | None = None, edits: dict | None = None):
        self.wizard_choices = wizard or {}
        self.dataset_edits = edits or {}
        groups = self.snapshot(path)
        return {"groups": groups, "wizard": self.wizard}

    def set_property(self, prop: int, value) -> None:
        details = self.enum_details(prop)
        if details:
            if value not in details["enum_choices"]:
                raise ValueError(f"unknown native enum label: {value}")
            virtual(prop, 18, None, [ctypes.c_void_p, ctypes.c_int])(
                prop,
                details["enum_choices"].index(value),
            )
            if self.enum_details(prop)["enum_label"] != value:
                raise ValueError(f"native enum setter rejected {value}")
            return
        elif isinstance(value, bool):
            encoded = "CHECKED" if value else "UNCHECKED"
        elif isinstance(value, float):
            encoded = format(value, ".12g")
        else:
            encoded = str(value)
        data = encoded.encode("utf-8")
        if len(data) >= 16:
            raise ValueError("probe supports only short scalar DES values")
        storage = ctypes.create_string_buffer(32)
        ctypes.memmove(storage, data, len(data))
        struct.pack_into("<QQ", storage, 16, len(data), 15)
        self.bind(
            "flopackdes.dll",
            "?applyDesStringToProperty@",
            None,
            [ctypes.c_void_p, ctypes.c_void_p],
        )(ctypes.addressof(storage), prop)
        actual = self.enum_details(prop)
        serialized = actual["enum_label"] if actual else self.property_value(prop)
        if serialized != encoded and not actual:
            try:
                if abs(float(serialized) - float(encoded)) <= 1e-10:
                    return
            except ValueError:
                pass
            raise ValueError(f"native scalar setter rejected {encoded}: {serialized}")
        if actual and serialized != value:
            raise ValueError(f"native enum setter rejected {value}: {serialized}")

    def capture_wizard(self, wizard: int) -> None:
        super().capture_wizard(wizard)
        found = set()
        for prop in property_map(wizard):
            name = cpp_string(prop + 16)
            if name in self.wizard_choices:
                self.set_property(prop, self.wizard_choices[name])
                details = self.enum_details(prop)
                value = details["enum_label"] if details else self.property_value(prop)
                self.wizard[name] = {"value": value, **details}
                found.add(name)
        if missing := self.wizard_choices.keys() - found:
            raise ValueError(f"unknown native wizard fields: {missing}")

    def apply_wizard(self, package: int, class_name: str, four_layer: bool = False) -> None:
        super().apply_wizard(package, class_name, four_layer)
        package_type = FAMILIES[self.preset_path.parent.name][0]
        count = self.bind(
            "flopackdatasets.dll",
            "?getNumberOfDataSets@",
            ctypes.c_int,
            [ctypes.c_int],
        )(package_type)
        found = set()
        for index in range(count):
            dataset = self.bind(
                "flopackdatasets.dll",
                "?createPackageDataSet@",
                ctypes.c_void_p,
                [ctypes.c_int, ctypes.c_size_t],
            )(package_type, index)
            if not dataset:
                raise ValueError(f"missing native dataset {index}")
            try:
                self.bind(
                    "flopackpackages.dll",
                    "?getData@FlopackPackage@flopack@@QEBAXPEAV",
                    None,
                    [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t],
                )(package, dataset, index)
                changed = False
                properties = property_map(dataset)
                if object_type(dataset) == ".?AVTopCoverDataSet@flopack@@":
                    for offset in (0x220, 0x980, 0x1F98):
                        properties.extend(property_map(dataset + offset))
                for prop in properties:
                    name = cpp_string(prop + 16)
                    if name in self.dataset_edits:
                        self.set_property(prop, self.dataset_edits[name])
                        found.add(name)
                        changed = True
                if changed:
                    # RVA 0x20dd0 forwards to group virtual slot 4. The fourth
                    # argument is an optional previous-value dataset, not a wizard.
                    self.bind(
                        "flopackpackages.dll",
                        "?setData@FlopackPackage@flopack@@QEAAXPEAV",
                        None,
                        [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p],
                    )(package, dataset, index, None)
            finally:
                destroy(dataset)
        if missing := self.dataset_edits.keys() - found:
            raise ValueError(f"unknown native dataset properties: {missing}")
