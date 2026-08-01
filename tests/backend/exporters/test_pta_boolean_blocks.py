import pytest
from lxml import etree

from packstudio.domain.enums import StructureType
from packstudio.domain.geometry import (
    BOOLEAN_SOURCE_ID_KEY,
    BOOLEAN_SOURCE_NAME_KEY,
    AxisAlignedBlock,
    Point3D,
    Size3D,
)
from packstudio.exporters.pta_boolean import compact_boolean_blocks
from packstudio.exporters.pta_constants import MODEL_NAMESPACE
from packstudio.exporters.pta_xml import export_pta_xml
from packstudio.templates.flip_chip_cbga.generator import generate_flip_chip_cbga
from packstudio.templates.flip_chip_cbga.parameters import FlipChipCbgaParameters
from packstudio.templates.package_library.catalog import default_request, generate


def test_boolean_compaction_encodes_a_ring_as_add_then_subtract() -> None:
    blocks = [
        rectangle("bottom", 0, 0, 10, 2),
        rectangle("top", 0, 8, 10, 2),
        rectangle("left", 0, 2, 2, 6),
        rectangle("right", 8, 2, 2, 6),
    ]

    compacted = compact_boolean_blocks(blocks, {})

    assert len(compacted) == 1
    solid = compacted[0].geometry
    assert solid.z == 2
    assert solid.thickness == 3
    assert [operation.add for operation in solid.operations] == [True, False]
    assert solid.operations[0].model_dump(exclude={"add"}) == pytest.approx(
        {"x": 0, "y": 0, "width": 10, "height": 10}
    )
    assert solid.operations[1].model_dump(exclude={"add"}) == pytest.approx(
        {"x": 2, "y": 2, "width": 6, "height": 6}
    )
    signed_area = sum(
        operation.width * operation.height * (1 if operation.add else -1)
        for operation in solid.operations
    )
    assert signed_area * solid.thickness == pytest.approx(
        sum(block.size.x * block.size.y * block.size.z for block in blocks)
    )


def test_boolean_compaction_merges_adjacent_rectangles() -> None:
    compacted = compact_boolean_blocks(
        [
            rectangle("left", 0, 0, 4, 6),
            rectangle("right", 4, 0, 6, 6),
        ],
        {},
    )

    assert len(compacted) == 1
    operations = compacted[0].geometry.operations
    assert len(operations) == 1
    assert operations[0].add is True
    assert operations[0].model_dump(exclude={"add"}) == pytest.approx(
        {"x": 0, "y": 0, "width": 10, "height": 6}
    )


def test_qfn_export_uses_layer_boolean_blocks_to_reduce_entities() -> None:
    model = generate(default_request("qfn"))
    root = etree.fromstring(export_pta_xml(model))
    namespace = {"m": MODEL_NAMESPACE}
    root_blocks = root.xpath("./m:Blocks/m:Block", namespaces=namespace)
    layers = root.xpath("./m:Layers/m:Layer", namespaces=namespace)
    layer_blocks = root.xpath("./m:Layers/m:Layer/m:Blocks/m:Block", namespaces=namespace)
    encapsulant_blocks = root.xpath(
        "./m:Layers/m:Layer/m:Blocks/m:Block[m:MaterialName='eme-7730lf']",
        namespaces=namespace,
    )
    operations = root.xpath(
        "./m:Layers/m:Layer/m:Blocks/m:Block/m:AllRects/m:Rect/m:Add_sub/text()",
        namespaces=namespace,
    )

    assert root.findtext(f"{{{MODEL_NAMESPACE}}}UseBlockBuildMode") == "false"
    assert not root_blocks
    assert layers
    assert len(model.blocks) == 1664
    assert len(layer_blocks) < len(model.blocks) / 4
    assert len(encapsulant_blocks) <= 6
    assert "false" in operations


@pytest.mark.parametrize(
    "template_id",
    ("wirebond_pbga", "fbga_fsbga", "qfn", "qfp_family", "soic_family"),
)
def test_boolean_compaction_preserves_volume_by_material(template_id: str) -> None:
    model = generate(default_request(template_id))
    expected: dict[str, float] = {}
    for block in model.blocks:
        expected[block.material_id] = expected.get(block.material_id, 0) + (
            block.size.x * block.size.y * block.size.z
        )
    actual = _serialized_volume_by_material(etree.fromstring(export_pta_xml(model)))

    assert actual.keys() == expected.keys()
    for material_id, expected_volume in expected.items():
        assert actual[material_id] == pytest.approx(expected_volume, rel=1e-10, abs=1e-10)


@pytest.mark.parametrize(
    "template_id",
    (
        "wirebond_pbga",
        "flip_chip_pbga",
        "fbga_fsbga",
        "flip_chip_cbga",
        "qfn",
        "qfp_family",
        "soic_family",
        "bare_die",
    ),
)
def test_all_templates_use_layers_and_only_top_blocks_may_differ_in_thickness(
    template_id: str,
) -> None:
    model = generate(default_request(template_id))
    root = etree.fromstring(export_pta_xml(model))
    namespace = {"m": MODEL_NAMESPACE}
    layers = root.xpath("./m:Layers/m:Layer", namespaces=namespace)

    assert root.findtext(f"{{{MODEL_NAMESPACE}}}UseBlockBuildMode") == "false"
    assert not root.xpath("./m:Blocks/m:Block", namespaces=namespace)
    assert [layer.findtext(f"{{{MODEL_NAMESPACE}}}IsTopLayer") for layer in layers] == [
        "true",
        *(["false"] * (len(layers) - 1)),
    ]
    for index, layer in enumerate(layers):
        layer_thickness = float(layer.findtext(f"{{{MODEL_NAMESPACE}}}ThicknessExpression"))
        for block in layer.xpath("./m:Blocks/m:Block", namespaces=namespace):
            block_thickness = float(block.findtext(f"{{{MODEL_NAMESPACE}}}ThicknessExpression"))
            assert block.findtext(f"{{{MODEL_NAMESPACE}}}ZOffsetExpression") == "0"
            if index == 0:
                assert block_thickness <= layer_thickness + 1e-10
            else:
                assert block_thickness == pytest.approx(layer_thickness)


def test_top_layer_alone_keeps_independent_block_thicknesses() -> None:
    model = generate_flip_chip_cbga(FlipChipCbgaParameters())
    material_id = model.materials[0].id
    group_id = model.groups[0].id
    blocks = [
        AxisAlignedBlock(
            id="base",
            name="Base",
            structure_type=StructureType.SUBSTRATE,
            origin=Point3D(x=0, y=0, z=0),
            size=Size3D(x=4, y=4, z=1),
            material_id=material_id,
            parent_group_id=group_id,
        ),
        AxisAlignedBlock(
            id="top-tall",
            name="Tall top block",
            structure_type=StructureType.ENCAPSULANT,
            origin=Point3D(x=0, y=0, z=1),
            size=Size3D(x=1, y=1, z=2),
            material_id=material_id,
            parent_group_id=group_id,
        ),
        AxisAlignedBlock(
            id="top-short",
            name="Short top block",
            structure_type=StructureType.ENCAPSULANT,
            origin=Point3D(x=2, y=0, z=1),
            size=Size3D(x=1, y=1, z=1),
            material_id=material_id,
            parent_group_id=group_id,
        ),
    ]
    modified = model.model_copy(
        update={
            "blocks": blocks,
            "heat_sources": [],
            "boundaries": [],
            "metadata": {**model.metadata, "pta_geometry_mode": "block"},
        }
    )

    root = etree.fromstring(export_pta_xml(modified))
    namespace = {"m": MODEL_NAMESPACE}
    layers = root.xpath("./m:Layers/m:Layer", namespaces=namespace)
    top_thicknesses = {
        float(value)
        for value in layers[0].xpath(
            "./m:Blocks/m:Block/m:ThicknessExpression/text()", namespaces=namespace
        )
    }
    lower_thicknesses = {
        float(value)
        for value in layers[1].xpath(
            "./m:Blocks/m:Block/m:ThicknessExpression/text()", namespaces=namespace
        )
    }

    assert root.findtext(f"{{{MODEL_NAMESPACE}}}UseBlockBuildMode") == "false"
    assert len(layers) == 2
    assert layers[0].findtext(f"{{{MODEL_NAMESPACE}}}IsTopLayer") == "true"
    assert float(layers[0].findtext(f"{{{MODEL_NAMESPACE}}}ThicknessExpression")) == 2
    assert top_thicknesses == {1, 2}
    assert lower_thicknesses == {1}
    assert not root.xpath("./m:Blocks/m:Block", namespaces=namespace)


def _serialized_volume_by_material(root: etree._Element) -> dict[str, float]:
    namespace = {"m": MODEL_NAMESPACE}
    volumes: dict[str, float] = {}
    for block in root.xpath("./m:Layers/m:Layer/m:Blocks/m:Block", namespaces=namespace):
        material_id = block.findtext(f"{{{MODEL_NAMESPACE}}}MaterialName")
        signed_area = 0.0
        for rectangle_node in block.xpath("./m:AllRects/m:Rect", namespaces=namespace):
            sign = 1 if rectangle_node.findtext(f"{{{MODEL_NAMESPACE}}}Add_sub") == "true" else -1
            width = float(rectangle_node.findtext(f"{{{MODEL_NAMESPACE}}}WidthExpression"))
            height = float(rectangle_node.findtext(f"{{{MODEL_NAMESPACE}}}HeightExpression"))
            signed_area += sign * width * height
        thickness = float(block.findtext(f"{{{MODEL_NAMESPACE}}}ThicknessExpression"))
        volumes[material_id] = volumes.get(material_id, 0) + signed_area * thickness
    return volumes


def rectangle(
    identifier: str,
    x: float,
    y: float,
    width: float,
    height: float,
) -> AxisAlignedBlock:
    return AxisAlignedBlock(
        id=identifier,
        name="Mold compound",
        structure_type=StructureType.ENCAPSULANT,
        origin=Point3D(x=x, y=y, z=2),
        size=Size3D(x=width, y=height, z=3),
        material_id="encapsulant",
        parent_group_id="group-encapsulant",
        metadata={
            BOOLEAN_SOURCE_ID_KEY: "mold",
            BOOLEAN_SOURCE_NAME_KEY: "Mold compound",
        },
    )
