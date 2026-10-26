"""Call hash-reviewed pure scalar realization helpers with borrowed material storage."""

import ctypes
import struct

from packstudio.domain.materials import Material
from tools.pack_reference.native_details import DetailedNativePack


class NativeFormulaProbe(DetailedNativePack):
    @staticmethod
    def material_storage(material: Material):
        storage = ctypes.create_string_buffer(0x90)
        struct.pack_into("<dd", storage, 0x40, material.density, material.specific_heat)
        struct.pack_into("<d", storage, 0x60, material.conductivity.x)
        return storage

    def wire(self, length, width, height, diameter, wire_length, count, metal, matrix):
        left, right = self.material_storage(metal), self.material_storage(matrix)
        output = ctypes.create_string_buffer(24)
        address = self.libraries["flopackrealise.dll"]._handle + 0x1CCF0
        function = ctypes.CFUNCTYPE(
            ctypes.c_void_p,
            ctypes.c_void_p,
            *([ctypes.c_double] * 5),
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_void_p,
        )(address)
        function(
            ctypes.addressof(output),
            length,
            width,
            height,
            diameter,
            wire_length,
            count,
            ctypes.addressof(left),
            ctypes.addressof(right),
        )
        return dict(
            zip(
                ("specific_heat", "density", "conductivity"),
                struct.unpack("<ddd", output),
                strict=True,
            )
        )

    def plated_via(self, inner, outer, footprint, metal, matrix):
        left, right = self.material_storage(metal), self.material_storage(matrix)
        output = ctypes.create_string_buffer(24)
        address = self.libraries["flopackrealise.dll"]._handle + 0x1D350
        function = ctypes.CFUNCTYPE(
            ctypes.c_void_p,
            ctypes.c_void_p,
            *([ctypes.c_double] * 3),
            ctypes.c_void_p,
            ctypes.c_void_p,
        )(address)
        function(
            ctypes.addressof(output),
            inner,
            outer,
            footprint,
            ctypes.addressof(left),
            ctypes.addressof(right),
        )
        return dict(
            zip(
                ("specific_heat", "density", "conductivity"),
                struct.unpack("<ddd", output),
                strict=True,
            )
        )
