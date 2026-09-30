from collections import defaultdict

from lxml import etree

from packstudio.default_parameters import request_default
from packstudio.domain.enums import StructureType
from packstudio.domain.model import PackageModel
from packstudio.exporters.pta_blocks import append_boolean_block
from packstudio.exporters.pta_boundaries import append_boundaries
from packstudio.exporters.pta_constants import (
    ARRAY_NAMESPACE,
    DIALOG_NAMESPACE,
    MODEL_NAMESPACE,
    XSI_NAMESPACE,
)
from packstudio.exporters.pta_layers import build_boolean_layers
from packstudio.exporters.pta_materials import append_materials
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
    _nil(root, "OtherThermalBondary")
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
    source_density = _source_density_by_block(model)
    layers = list(reversed(build_boolean_layers(model, source_density)))
    materials = {material.id: material for material in model.materials}

    for index, geometry_layer in enumerate(layers):
        layer = etree.SubElement(container, etree.QName(MODEL_NAMESPACE, "Layer"))
        block_container = etree.SubElement(layer, etree.QName(MODEL_NAMESPACE, "Blocks"))
        for compacted in geometry_layer.boolean_blocks:
            block = compacted.geometry
            append_boolean_block(
                block_container,
                block,
                materials[block.material_id].color,
                compacted.volumetric_heat_source,
                z_offset=0,
                mesh_sizes=(0, 0, 0),
            )
        structures = {block.structure_type for block in geometry_layer.physical_blocks}
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
        _text(layer, "IsTopLayer", _boolean(geometry_layer.is_top))
        mesh_x, mesh_y, mesh_z = layer_mesh_sizes(
            model,
            geometry_layer.physical_blocks,
            geometry_layer.thickness,
        )
        _text(layer, "MeshSizeXExpression", mesh_x)
        _text(layer, "MeshSizeYExpression", mesh_y)
        _text(layer, "MeshSizeZExpression", mesh_z)
        _text(layer, "MetalConversionRate", 0.4)
        _text(
            layer,
            "Name",
            f"Layer {index + 1} @ {_number(geometry_layer.base_z + z_shift)} mm",
        )
        _text(layer, "PeriodWidth", 10)
        _text(layer, "SawBoundaryOption", "None")
        _text(layer, "ThicknessExpression", geometry_layer.thickness)
        _text(layer, "XOffsetExpression", 0)
        _text(layer, "YOffsetExpression", 0)


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
    return float(request_default("pta", "initial_temperature_k"))


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
