"""Snapshot PACK's built-in material library without loading user files or exporting models."""

import ctypes
import os

from tools.pack_reference.native import cpp_string
from tools.pack_reference.native_details import vector_items


def read_builtin_materials(native) -> list[dict]:
    previous_directory = os.environ.get("FLOCENTRALDIR")
    os.environ["FLOCENTRALDIR"] = str(native.installation / "flocentral")
    storage = ctypes.create_string_buffer(65_536)
    library = ctypes.addressof(storage)
    native.bind(
        "flopackbackend.dll",
        "??0MaterialLibrary@flopack@@QEAA@XZ",
        ctypes.c_void_p,
        [ctypes.c_void_p],
    )(library)
    try:
        native.bind("flopackbackend.dll", "?populateBuiltInMaterials@", None, [ctypes.c_void_p])(
            library
        )
        materials = []
        for item in vector_items(library + 0x30, 8):
            material = ctypes.c_void_p.from_address(item).value
            record = {}
            for field, getter in (("name", "getName"), ("group", "getGroupName")):
                output = ctypes.create_string_buffer(32)
                address = ctypes.addressof(output)
                native.bind(
                    "flopackmaterials.dll",
                    f"?{getter}@FlopackMaterial@",
                    ctypes.c_void_p,
                    [ctypes.c_void_p, ctypes.c_void_p],
                )(material, address)
                try:
                    record[field] = cpp_string(address)
                finally:
                    if ctypes.c_size_t.from_address(address + 24).value >= 16:
                        native.free_functions["flopackmaterials.dll"](
                            ctypes.c_void_p.from_address(address).value
                        )
            for field, getter in (
                ("density_kg_m3", "getDensity"),
                ("specific_heat_j_kg_k", "getSpecificHeat"),
                ("emissivity", "getEmissivity"),
                ("conductivity_w_m_k", "getConductivity"),
                ("conductivity_coefficient", "getConductivityCoefficient"),
                ("conductivity_reference_temperature", "getConductivityRefTemp"),
                ("kx_w_m_k", "getKx"),
                ("ky_w_m_k", "getKy"),
                ("kz_w_m_k", "getKz"),
            ):
                record[field] = native.bind(
                    "flopackmaterials.dll",
                    f"?{getter}@FlopackMaterial@",
                    ctypes.c_double,
                    [ctypes.c_void_p],
                )(material)
            record["conductivity_type"] = native.bind(
                "flopackmaterials.dll", "?getConductivityType@", ctypes.c_int, [ctypes.c_void_p]
            )(material)
            materials.append(record)
        return sorted(materials, key=lambda record: record["name"])
    finally:
        native.bind(
            "flopackproperties.dll",
            "?setMaterialControllerInterface@",
            None,
            [ctypes.c_void_p],
        )(None)
        native.bind("flopackbackend.dll", "??1MaterialLibrary@", None, [ctypes.c_void_p])(library)
        if previous_directory is None:
            os.environ.pop("FLOCENTRALDIR", None)
        else:
            os.environ["FLOCENTRALDIR"] = previous_directory
