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


def test_qfn_export_uses_root_boolean_blocks_to_reduce_entities() -> None:
    model = generate(default_request("qfn"))
    root = etree.fromstring(export_pta_xml(model))
    layer_model = model.model_copy(
        update={"metadata": {**model.metadata, "pta_geometry_mode": "layer"}}
    )
    layer_root = etree.fromstring(export_pta_xml(layer_model))
    namespace = {"m": MODEL_NAMESPACE}
    root_blocks = root.xpath("./m:Blocks/m:Block", namespaces=namespace)
    layer_blocks = layer_root.xpath("./m:Layers/m:Layer/m:Blocks/m:Block", namespaces=namespace)
    encapsulant_blocks = root.xpath(
        "./m:Blocks/m:Block[m:MaterialName='eme-7730lf']", namespaces=namespace
    )
    layer_encapsulant_count = sum(
        material_id == "eme-7730lf"
        for material_id in layer_root.xpath(
            "./m:Layers/m:Layer/m:Blocks/m:Block/m:MaterialName/text()",
            namespaces=namespace,
        )
    )
    operations = root.xpath(
        "./m:Blocks/m:Block/m:AllRects/m:Rect/m:Add_sub/text()",
        namespaces=namespace,
    )

    assert root.findtext(f"{{{MODEL_NAMESPACE}}}UseBlockBuildMode") == "true"
    assert not root.xpath("./m:Layers/m:Layer", namespaces=namespace)
    assert len(model.blocks) == 1664
    assert len(layer_blocks) == 3747
    assert len(root_blocks) < len(layer_blocks) / 10
    assert layer_encapsulant_count == 3421
    assert len(encapsulant_blocks) <= 6
    assert "false" in operations


@pytest.mark.parametrize(
    "template_id",
    ("wirebond_pbga", "fbga_fsbga", "qfn", "qfp_family", "soic_family"),
)
def test_boolean_compaction_preserves_volume_by_material(template_id: str) -> None:
    model = generate(default_request(template_id))
    compacted = compact_boolean_blocks(model.blocks, {})
    expected: dict[str, float] = {}
    actual: dict[str, float] = {}
    for block in model.blocks:
        expected[block.material_id] = expected.get(block.material_id, 0) + (
            block.size.x * block.size.y * block.size.z
        )
    for item in compacted:
        solid = item.geometry
        signed_area = sum(
            operation.width * operation.height * (1 if operation.add else -1)
            for operation in solid.operations
        )
        actual[solid.material_id] = actual.get(solid.material_id, 0) + (
            signed_area * solid.thickness
        )

    assert actual.keys() == expected.keys()
    for material_id, expected_volume in expected.items():
        assert actual[material_id] == pytest.approx(expected_volume, rel=1e-10, abs=1e-10)


def test_root_blocks_keep_independent_z_offsets_and_thicknesses() -> None:
    model = generate_flip_chip_cbga(FlipChipCbgaParameters())
    die = next(block for block in model.blocks if block.id == "die")
    moved_die = die.model_copy(
        update={"origin": die.origin.model_copy(update={"z": die.origin.z + 3})}
    )
    modified = model.model_copy(
        update={
            "blocks": [moved_die if block.id == moved_die.id else block for block in model.blocks],
            "metadata": {**model.metadata, "pta_geometry_mode": "block"},
        }
    )

    root = etree.fromstring(export_pta_xml(modified))
    namespace = {"m": MODEL_NAMESPACE}
    root_blocks = root.xpath("./m:Blocks/m:Block", namespaces=namespace)
    z_offsets = {
        float(block.findtext(f"{{{MODEL_NAMESPACE}}}ZOffsetExpression")) for block in root_blocks
    }
    thicknesses = {
        float(block.findtext(f"{{{MODEL_NAMESPACE}}}ThicknessExpression")) for block in root_blocks
    }

    assert root.findtext(f"{{{MODEL_NAMESPACE}}}UseBlockBuildMode") == "true"
    assert len(z_offsets) > 2
    assert len(thicknesses) > 2
    assert not root.xpath("./m:Layers/m:Layer", namespaces=namespace)


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
