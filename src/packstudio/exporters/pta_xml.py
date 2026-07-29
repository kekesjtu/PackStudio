from collections import defaultdict

from lxml import etree

from packstudio.domain.enums import StructureType
from packstudio.domain.geometry import AxisAlignedBlock
from packstudio.domain.model import PackageModel
from packstudio.exporters.pta_boundaries import (
    append_boundaries,
    append_default_exterior_boundary,
)
from packstudio.exporters.pta_constants import (
    ARRAY_NAMESPACE,
    DIALOG_NAMESPACE,
    MODEL_NAMESPACE,
    XSI_NAMESPACE,
)
from packstudio.exporters.pta_materials import append_block_color, append_materials
from packstudio.exporters.pta_mesh import layer_mesh_sizes


def export_pta_xml(model: PackageModel) -> bytes:
    """Export PTA input data without mesh or solver-result payloads."""
    root = etree.Element(
        etree.QName(MODEL_NAMESPACE, "Structure"),
        nsmap={None: MODEL_NAMESPACE, "i": XSI_NAMESPACE},
    )
    minimum_z = min(block.origin.z for block in model.blocks)
    z_shift = -minimum_z
    ambient_temperature = _ambient_temperature(model)

    _text(root, "AlphaDegree", 0)
    _text(root, "AmbientTemperature", ambient_temperature)
    etree.SubElement(
        root,
        etree.QName(MODEL_NAMESPACE, "BasicGeometries"),
        nsmap={"a": DIALOG_NAMESPACE},
    )
    _text(root, "BetaDegree", 0)
    etree.SubElement(root, etree.QName(MODEL_NAMESPACE, "Blocks"))
    _nil(root, "BottomThermalBoundary")
    append_boundaries(
        root,
        model.boundaries,
        {block.id: block for block in model.blocks},
        z_shift,
    )
    for name, value in (
        ("DieLayerNum", 0),
        ("DieLayerSizeX", 0),
        ("DieLayerSizeY", 0),
    ):
        _text(root, name, value)
    etree.SubElement(root, etree.QName(MODEL_NAMESPACE, "DieMaterialName"))
    _text(root, "DielectricLossFactor", 0)
    _text(root, "Dimension", "Dimension3D")
    _text(root, "EnabledPhysics", "HeatTransfer")
    etree.SubElement(
        root,
        etree.QName(MODEL_NAMESPACE, "Functions"),
        nsmap={"a": ARRAY_NAMESPACE},
    )
    _text(root, "GammaDegree", 0)
    _text(root, "InitialTemperature", ambient_temperature)
    append_layers(root, model, z_shift)
    _text(root, "LengthUnit", "Mm")
    append_materials(root, model.materials)
    _text(root, "MechanicalDampingFactor", 0)
    etree.SubElement(root, etree.QName(MODEL_NAMESPACE, "ObservePoints2D"))
    etree.SubElement(root, etree.QName(MODEL_NAMESPACE, "ObservePoints3D"))
    append_default_exterior_boundary(
        root,
        float(model.metadata.get("default_convection_coefficient_w_m2k", 10)),
        ambient_temperature,
    )
    for name, value in (
        ("SawFrequency", 0),
        ("SawFrequencySolveMode", "SinglePoint"),
        ("SawFrequencyStart", 0),
        ("SawFrequencyStep", 0),
        ("SawFrequencyStop", 0),
        ("SawFrequencyUnit", "GHz"),
        ("SoftwareMode", "PTA"),
        ("StudyType", "Steady"),
    ):
        _text(root, name, value)
    etree.SubElement(root, etree.QName(MODEL_NAMESPACE, "TIMMaterialName"))
    _text(root, "TopLayerIndex", 0)
    _nil(root, "TopThermalBoundary")
    for name, value in (
        ("TransientStudyDuration", 0),
        ("TransientStudyTimeStep", 1),
        ("TransientTimeUnit", "S"),
        ("UseBlockBuildMode", "false"),
    ):
        _text(root, name, value)
    etree.SubElement(
        root,
        etree.QName(MODEL_NAMESPACE, "Variables"),
        nsmap={"a": ARRAY_NAMESPACE},
    )
    return etree.tostring(
        root,
        xml_declaration=True,
        encoding="utf-8",
        pretty_print=True,
    )


def append_layers(parent: etree._Element, model: PackageModel, z_shift: float) -> None:
    container = etree.SubElement(parent, etree.QName(MODEL_NAMESPACE, "Layers"))
    bottom_to_top_layers = _group_layers(model.blocks)
    _validate_contiguous_layers(bottom_to_top_layers, z_shift)
    layers = list(reversed(bottom_to_top_layers))
    source_density = _source_density_by_block(model)
    materials = {material.id: material for material in model.materials}

    for index, ((base_z, thickness), blocks) in enumerate(layers):
        layer = etree.SubElement(container, etree.QName(MODEL_NAMESPACE, "Layer"))
        block_container = etree.SubElement(layer, etree.QName(MODEL_NAMESPACE, "Blocks"))
        for block in blocks:
            _append_block(
                block_container,
                block,
                materials[block.material_id].color,
                source_density.get(block.id, 0),
            )
        structures = {block.structure_type for block in blocks}
        _text(layer, "CreatedByTopLayer", "false")
        _text(layer, "IsBasic", "false")
        _text(layer, "IsBottomPackaging", "false")
        _text(layer, "IsDie", "false")
        _text(layer, "IsDoule", "false")
        _text(layer, "IsIDTSawModel", "false")
        _text(layer, "IsNotIDTSawModel", "false")
        _text(layer, "IsSingle", "false")
        _text(layer, "IsSubstrate", _boolean(StructureType.SUBSTRATE in structures))
        _text(layer, "IsTIM", "false")
        _text(layer, "IsTopLayer", _boolean(index == 0))
        mesh_x, mesh_y, mesh_z = layer_mesh_sizes(model, blocks, thickness)
        _text(layer, "MeshSizeXExpression", mesh_x)
        _text(layer, "MeshSizeYExpression", mesh_y)
        _text(layer, "MeshSizeZExpression", mesh_z)
        _text(layer, "MetalConversionRate", 0.4)
        _text(layer, "Name", f"Layer {index + 1} @ {_number(base_z + z_shift)} mm")
        _text(layer, "PeriodWidth", 10)
        _text(layer, "SawBoundaryOption", "None")
        _text(layer, "ThicknessExpression", thickness)
        _text(layer, "XOffsetExpression", 0)
        _text(layer, "YOffsetExpression", 0)


def _append_block(
    parent: etree._Element,
    block: AxisAlignedBlock,
    color: str,
    volumetric_heat_source: float,
) -> None:
    element = etree.SubElement(parent, etree.QName(MODEL_NAMESPACE, "Block"))
    rectangles = etree.SubElement(element, etree.QName(MODEL_NAMESPACE, "AllRects"))
    rectangle = etree.SubElement(rectangles, etree.QName(MODEL_NAMESPACE, "Rect"))
    _text(rectangle, "Add_sub", "true")
    _text(rectangle, "ArrayDisguise", "false")
    _text(rectangle, "CreatedByArray", "false")
    _text(rectangle, "HeightExpression", block.size.y)
    _text(rectangle, "Name", "Add rectangle 1")
    _text(rectangle, "NotOccupiedByArray", "true")
    _nil(rectangle, "ParentRect")
    _text(rectangle, "WidthExpression", block.size.x)
    _text(rectangle, "XExpression", 0)
    _text(rectangle, "XIntervalExpression", 0)
    _text(rectangle, "XSizeExpression", block.size.x)
    _text(rectangle, "YExpression", 0)
    _text(rectangle, "YIntervalExpression", 0)
    _text(rectangle, "YSizeExpression", block.size.y)
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
    _text(element, "MeshSizeXExpression", 0)
    _text(element, "MeshSizeYExpression", 0)
    _text(element, "MeshSizeZExpression", 0)
    _text(element, "Name", block.name)
    _text(element, "NetDonorConcentration", 0)
    _text(element, "NotChargeConservation", "true")
    etree.SubElement(element, etree.QName(MODEL_NAMESPACE, "PMLType"))
    _nil(element, "ParentBlock")
    etree.SubElement(element, etree.QName(MODEL_NAMESPACE, "SelectedPMLType"))
    _text(element, "TerminalVoltage", 0)
    _text(element, "ThicknessExpression", block.size.z)
    _text(element, "TiReyuan", volumetric_heat_source)
    _text(element, "XOffsetExpression", block.origin.x)
    _text(element, "YOffsetExpression", block.origin.y)
    _text(element, "ZOffsetExpression", 0)


def _group_layers(
    blocks: list[AxisAlignedBlock],
) -> list[tuple[tuple[float, float], list[AxisAlignedBlock]]]:
    z_coordinates = sorted(
        {coordinate for block in blocks for coordinate in (block.origin.z, block.max_z)}
    )
    layers: list[tuple[tuple[float, float], list[AxisAlignedBlock]]] = []
    for base_z, maximum_z in zip(z_coordinates, z_coordinates[1:], strict=False):
        thickness = maximum_z - base_z
        if thickness <= 1e-12:
            continue
        active = [
            block
            for block in blocks
            if block.origin.z <= base_z + 1e-9 and block.max_z >= maximum_z - 1e-9
        ]
        if not active:
            layers.append(((base_z, thickness), []))
            continue
        slices = [
            block.model_copy(
                update={
                    "origin": block.origin.model_copy(update={"z": base_z}),
                    "size": block.size.model_copy(update={"z": thickness}),
                }
            )
            for block in active
        ]
        layers.append(((base_z, thickness), slices))
    return layers


def _validate_contiguous_layers(
    layers: list[tuple[tuple[float, float], list[AxisAlignedBlock]]], z_shift: float
) -> None:
    cursor = 0.0
    for (base_z, thickness), blocks in layers:
        shifted_z = base_z + z_shift
        if abs(shifted_z - cursor) > 1e-8:
            raise ValueError("PTA export requires contiguous z layers")
        if not blocks:
            raise ValueError("PTA export requires a contiguous stack without empty z intervals")
        cursor = shifted_z + thickness


def _source_density_by_block(model: PackageModel) -> dict[str, float]:
    blocks = {block.id: block for block in model.blocks}
    density: dict[str, float] = defaultdict(float)
    for source in model.heat_sources:
        block = blocks[source.block_id]
        volume_m3 = block.size.x * block.size.y * block.size.z * 1e-9
        density[source.block_id] += source.power_w / volume_m3
    return dict(density)


def _ambient_temperature(model: PackageModel) -> float:
    metadata_value = model.metadata.get("ambient_temperature_k")
    if metadata_value is not None:
        return float(metadata_value)
    for boundary in model.boundaries:
        if boundary.ambient_temperature_k is not None:
            return boundary.ambient_temperature_k
    return 300


def _nil(parent: etree._Element, name: str) -> None:
    element = etree.SubElement(parent, etree.QName(MODEL_NAMESPACE, name))
    element.set(etree.QName(XSI_NAMESPACE, "nil"), "true")


def _text(parent: etree._Element, name: str, value: str | int | float) -> None:
    etree.SubElement(parent, etree.QName(MODEL_NAMESPACE, name)).text = (
        value if isinstance(value, str) else _number(value)
    )


def _boolean(value: bool) -> str:
    return "true" if value else "false"


def _number(value: float) -> str:
    if abs(value) < 1e-12:
        return "0"
    return f"{value:.12g}"
