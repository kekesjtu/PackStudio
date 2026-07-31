from lxml import etree

from packstudio.domain.geometry import (
    AxisAlignedBlock,
    RectangleOperation,
    RectangularBooleanBlock,
)
from packstudio.exporters.pta_constants import MODEL_NAMESPACE, XSI_NAMESPACE
from packstudio.exporters.pta_materials import append_block_color


def append_layer_block(
    parent: etree._Element,
    block: AxisAlignedBlock,
    color: str,
    volumetric_heat_source: float,
) -> None:
    geometry = RectangularBooleanBlock(
        id=block.id,
        name=block.name,
        structure_type=block.structure_type,
        z=block.origin.z,
        thickness=block.size.z,
        material_id=block.material_id,
        parent_group_id=block.parent_group_id,
        operations=[
            RectangleOperation(
                add=True,
                x=block.origin.x,
                y=block.origin.y,
                width=block.size.x,
                height=block.size.y,
            )
        ],
        source_block_ids=[block.id],
    )
    append_boolean_block(
        parent,
        geometry,
        color,
        volumetric_heat_source,
        z_offset=0,
        mesh_sizes=(0, 0, 0),
    )


def append_boolean_block(
    parent: etree._Element,
    block: RectangularBooleanBlock,
    color: str,
    volumetric_heat_source: float,
    *,
    z_offset: float,
    mesh_sizes: tuple[float, float, float],
) -> None:
    element = etree.SubElement(parent, etree.QName(MODEL_NAMESPACE, "Block"))
    rectangles = etree.SubElement(element, etree.QName(MODEL_NAMESPACE, "AllRects"))
    x_offset = min(operation.x for operation in block.operations)
    y_offset = min(operation.y for operation in block.operations)
    add_index = 0
    subtract_index = 0
    for operation in block.operations:
        if operation.add:
            add_index += 1
            operation_name = f"Add rectangle {add_index}"
        else:
            subtract_index += 1
            operation_name = f"Subtract rectangle {subtract_index}"
        _append_rectangle(
            rectangles,
            operation,
            operation_name,
            x_offset=x_offset,
            y_offset=y_offset,
        )

    _text(element, "CanCreateArray", "true")
    append_block_color(element, color)
    _text(element, "HasBeenChanged", "true")
    _text(element, "InitialName", block.name)
    for name in (
        "IsChargeConservation",
        "IsChargeConservationPiezoelectricity",
        "IsElectrode",
        "IsLinearElasticMaterial",
    ):
        _text(element, name, "false")
    _text(element, "IsNormalMaterial", "true")
    for name in ("IsPML", "IsPiezoelectricMaterial", "IsTerminal"):
        _text(element, name, "false")
    _text(element, "IsVisible", "true")
    _text(element, "MaterialName", block.material_id)
    for axis, size in zip("XYZ", mesh_sizes, strict=True):
        _text(element, f"MeshSize{axis}Expression", size)
    _text(element, "Name", block.name)
    _text(element, "NetDonorConcentration", 0)
    _text(element, "NotChargeConservation", "true")
    etree.SubElement(element, etree.QName(MODEL_NAMESPACE, "PMLType"))
    _nil(element, "ParentBlock")
    etree.SubElement(element, etree.QName(MODEL_NAMESPACE, "SelectedPMLType"))
    _text(element, "TerminalVoltage", 0)
    _text(element, "ThicknessExpression", block.thickness)
    _text(element, "TiReyuan", volumetric_heat_source)
    _text(element, "XOffsetExpression", x_offset)
    _text(element, "YOffsetExpression", y_offset)
    _text(element, "ZOffsetExpression", z_offset)


def boolean_block_extents(
    block: RectangularBooleanBlock,
) -> tuple[float, float, float]:
    minimum_x = min(operation.x for operation in block.operations)
    maximum_x = max(operation.x + operation.width for operation in block.operations)
    minimum_y = min(operation.y for operation in block.operations)
    maximum_y = max(operation.y + operation.height for operation in block.operations)
    return maximum_x - minimum_x, maximum_y - minimum_y, block.thickness


def _append_rectangle(
    parent: etree._Element,
    operation: RectangleOperation,
    name: str,
    *,
    x_offset: float,
    y_offset: float,
) -> None:
    rectangle = etree.SubElement(parent, etree.QName(MODEL_NAMESPACE, "Rect"))
    _text(rectangle, "Add_sub", "true" if operation.add else "false")
    _text(rectangle, "ArrayDisguise", "false")
    _text(rectangle, "CreatedByArray", "false")
    _text(rectangle, "HeightExpression", operation.height)
    _text(rectangle, "Name", name)
    _text(rectangle, "NotOccupiedByArray", "true")
    _nil(rectangle, "ParentRect")
    _text(rectangle, "WidthExpression", operation.width)
    _text(rectangle, "XExpression", operation.x - x_offset)
    _text(rectangle, "XIntervalExpression", operation.x - x_offset)
    _text(rectangle, "XSizeExpression", operation.width)
    _text(rectangle, "YExpression", operation.y - y_offset)
    _text(rectangle, "YIntervalExpression", operation.y - y_offset)
    _text(rectangle, "YSizeExpression", operation.height)


def _nil(parent: etree._Element, name: str) -> None:
    element = etree.SubElement(parent, etree.QName(MODEL_NAMESPACE, name))
    element.set(etree.QName(XSI_NAMESPACE, "nil"), "true")


def _text(parent: etree._Element, name: str, value: str | int | float) -> None:
    etree.SubElement(parent, etree.QName(MODEL_NAMESPACE, name)).text = (
        value if isinstance(value, str) else _number(value)
    )


def _number(value: float) -> str:
    if abs(value) < 1e-12:
        return "0"
    return f"{value:.12g}"
