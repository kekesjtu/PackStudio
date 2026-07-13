from lxml import etree

from packstudio.domain.enums import BlockFace, BoundaryKind
from packstudio.domain.geometry import AxisAlignedBlock
from packstudio.domain.thermal import BoundaryCondition, SurfaceReference
from packstudio.exporters.pta_constants import (
    ARRAY_NAMESPACE,
    BOUNDARY_NAMESPACE,
    MODEL_NAMESPACE,
    XSI_NAMESPACE,
)


def append_boundaries(
    parent: etree._Element,
    boundaries: list[BoundaryCondition],
    blocks: dict[str, AxisAlignedBlock],
    z_shift: float,
) -> None:
    container = etree.SubElement(parent, etree.QName(MODEL_NAMESPACE, "Boundaries"))
    for boundary in boundaries:
        if boundary.kind is BoundaryKind.ADIABATIC:
            continue
        element = etree.SubElement(container, etree.QName(MODEL_NAMESPACE, "Boundary"))
        _text(element, "BoundaryCategory", "Electrical")
        etree.SubElement(
            element,
            etree.QName(MODEL_NAMESPACE, "FaceIds"),
            nsmap={"a": ARRAY_NAMESPACE},
        )
        face_keys = etree.SubElement(
            element,
            etree.QName(MODEL_NAMESPACE, "FaceKeys"),
            nsmap={"a": ARRAY_NAMESPACE},
        )
        for target in boundary.targets:
            etree.SubElement(face_keys, etree.QName(ARRAY_NAMESPACE, "string")).text = _face_key(
                blocks[target.block_id], target, z_shift
            )
        _text(element, "Name", boundary.name)
        _append_thermal_boundary(element, boundary)


def append_default_exterior_boundary(
    parent: etree._Element,
    convection_coefficient_w_m2k: float,
    ambient_temperature_k: float,
) -> None:
    element = etree.SubElement(
        parent,
        etree.QName(MODEL_NAMESPACE, "OtherThermalBondary"),
        nsmap={"a": BOUNDARY_NAMESPACE},
    )
    element.set(etree.QName(XSI_NAMESPACE, "type"), "a:ThirdTypeThermalBoundary")
    _boundary_text(element, "ConvectionCoefficient", convection_coefficient_w_m2k)
    _boundary_text(element, "EnvironmentTemperature", ambient_temperature_k)


def _append_thermal_boundary(parent: etree._Element, boundary: BoundaryCondition) -> None:
    type_names = {
        BoundaryKind.TEMPERATURE: "FirstTypeThermalBoundary",
        BoundaryKind.HEAT_FLUX: "SecondTypeThermalBoundary",
        BoundaryKind.CONVECTION: "ThirdTypeThermalBoundary",
    }
    element = etree.SubElement(
        parent,
        etree.QName(MODEL_NAMESPACE, "ThermalBoundary"),
        nsmap={"a": BOUNDARY_NAMESPACE},
    )
    element.set(etree.QName(XSI_NAMESPACE, "type"), f"a:{type_names[boundary.kind]}")
    if boundary.kind is BoundaryKind.TEMPERATURE:
        _boundary_text(element, "Temperature", boundary.temperature_k)
    elif boundary.kind is BoundaryKind.HEAT_FLUX:
        _boundary_text(element, "HeatFlux", boundary.heat_flux_w_m2)
    else:
        _boundary_text(
            element,
            "ConvectionCoefficient",
            boundary.convection_coefficient_w_m2k,
        )
        _boundary_text(element, "EnvironmentTemperature", boundary.ambient_temperature_k)


def _face_key(block: AxisAlignedBlock, target: SurfaceReference, z_shift: float) -> str:
    x0, x1 = block.origin.x, block.max_x
    y0, y1 = block.origin.y, block.max_y
    z0, z1 = block.origin.z + z_shift, block.max_z + z_shift
    face = target.face
    if face is BlockFace.Z_MIN:
        return f"Z|E|{_number(z0)}|{_number(x0)},{_number(x1)},{_number(y0)},{_number(y1)}"
    if face is BlockFace.Z_MAX:
        return f"Z|E|{_number(z1)}|{_number(x0)},{_number(x1)},{_number(y0)},{_number(y1)}"
    if face is BlockFace.Y_MIN:
        return f"Y|E|{_number(y0)}|{_number(x0)}|{_number(x1)}|{_number(z0)}|{_number(z1)}"
    if face is BlockFace.Y_MAX:
        return f"Y|E|{_number(y1)}|{_number(x0)}|{_number(x1)}|{_number(z0)}|{_number(z1)}"
    if face is BlockFace.X_MIN:
        return f"X|E|{_number(x0)}|{_number(y0)}|{_number(y1)}|{_number(z0)}|{_number(z1)}"
    return f"X|E|{_number(x1)}|{_number(y0)}|{_number(y1)}|{_number(z0)}|{_number(z1)}"


def _text(parent: etree._Element, name: str, value: str) -> None:
    etree.SubElement(parent, etree.QName(MODEL_NAMESPACE, name)).text = value


def _boundary_text(parent: etree._Element, name: str, value: float | None) -> None:
    if value is None:
        raise ValueError(f"boundary value {name} is missing")
    etree.SubElement(parent, etree.QName(BOUNDARY_NAMESPACE, name)).text = _number(value)


def _number(value: float) -> str:
    if abs(value) < 1e-12:
        return "0"
    return f"{value:.12g}"
