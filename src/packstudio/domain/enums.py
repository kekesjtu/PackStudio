from enum import StrEnum


class StructureType(StrEnum):
    SUBSTRATE = "substrate"
    DIE = "die"
    ENCAPSULANT = "encapsulant"
    FLIP_CHIP_BUMP = "flip_chip_bump"
    UNDERFILL = "underfill"
    SOLDER_BALL = "solder_ball"
    STATIC_AIR = "static_air"
    THERMAL_INTERFACE = "thermal_interface"
    HEAT_SLUG = "heat_slug"
    LID = "lid"
    DIE_ATTACH = "die_attach"
    LEAD_FRAME = "lead_frame"
    BOND_WIRE = "bond_wire"
    SOLDER_MASK = "solder_mask"
    TRACE = "trace"
    VIA = "via"
    EXPOSED_PAD = "exposed_pad"
    SOLDER = "solder"
    GENERIC = "generic"


class BlockFace(StrEnum):
    X_MIN = "x_min"
    X_MAX = "x_max"
    Y_MIN = "y_min"
    Y_MAX = "y_max"
    Z_MIN = "z_min"
    Z_MAX = "z_max"


class BoundaryKind(StrEnum):
    ADIABATIC = "adiabatic"
    CONVECTION = "convection"
    HEAT_FLUX = "heat_flux"
    TEMPERATURE = "temperature"
