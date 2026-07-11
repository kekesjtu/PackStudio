import pytest
from lxml import etree

from packstudio.exporters.pta_constants import ARRAY_NAMESPACE, MODEL_NAMESPACE
from packstudio.exporters.pta_xml import export_pta_xml
from packstudio.templates.flip_chip_cbga.generator import generate_flip_chip_cbga
from packstudio.templates.flip_chip_cbga.parameters import (
    EnvironmentParameters,
    FlipChipCbgaParameters,
)


def test_pta_export_contains_only_input_model_data() -> None:
    model = generate_flip_chip_cbga(FlipChipCbgaParameters())

    payload = export_pta_xml(model)
    root = etree.fromstring(payload)
    local_names = [etree.QName(element).localname for element in root.iter()]

    assert etree.QName(root).namespace == MODEL_NAMESPACE
    assert etree.QName(root).localname == "Structure"
    assert "Results" not in local_names
    assert "LayerPBResults" not in local_names
    assert "ThermalMaskResults" not in local_names
    assert not any(name.startswith("Mesh") for name in local_names)


def test_pta_export_preserves_blocks_materials_and_anisotropy() -> None:
    model = generate_flip_chip_cbga(FlipChipCbgaParameters())
    root = etree.fromstring(export_pta_xml(model))
    namespace = {"m": MODEL_NAMESPACE, "a": ARRAY_NAMESPACE}

    blocks = root.xpath(".//m:Layers/m:Layer/m:Blocks/m:Block", namespaces=namespace)
    material_entries = root.xpath(
        ".//m:Materials/a:KeyValueOfstringMaterialGyu7GfTz", namespaces=namespace
    )
    conductivities = root.xpath(".//m:Materials//m:DaoreXishu/text()", namespaces=namespace)

    assert len(blocks) == len(model.blocks)
    assert len(material_entries) == len(model.materials)
    assert any("," in conductivity for conductivity in conductivities)


def test_pta_export_converts_total_die_power_to_volumetric_source() -> None:
    parameters = FlipChipCbgaParameters()
    model = generate_flip_chip_cbga(parameters)
    root = etree.fromstring(export_pta_xml(model))
    namespace = {"m": MODEL_NAMESPACE}
    die_block = root.xpath(".//m:Block[m:Name='Silicon die']", namespaces=namespace)[0]
    source_density = float(die_block.findtext(f"{{{MODEL_NAMESPACE}}}TiReyuan"))
    expected = parameters.die.power_w / (
        parameters.die.length * parameters.die.width * parameters.die.thickness * 1e-9
    )

    assert source_density == pytest.approx(expected, rel=1e-10)


def test_pta_export_writes_convection_face_keys() -> None:
    parameters = FlipChipCbgaParameters(
        environment=EnvironmentParameters(
            ambient_temperature_k=300,
            bottom_convection_coefficient_w_m2k=10,
            top_convection_coefficient_w_m2k=20,
        )
    )
    root = etree.fromstring(export_pta_xml(generate_flip_chip_cbga(parameters)))
    namespace = {"m": MODEL_NAMESPACE, "a": ARRAY_NAMESPACE}
    face_keys = root.xpath(".//m:Boundaries//a:string/text()", namespaces=namespace)

    assert face_keys
    assert all(key.startswith("Z|E|") for key in face_keys)


def test_pta_export_rejects_non_contiguous_layer_stack() -> None:
    model = generate_flip_chip_cbga(FlipChipCbgaParameters())
    moved_die = next(block for block in model.blocks if block.id == "die").model_copy(
        update={
            "origin": next(block for block in model.blocks if block.id == "die").origin.model_copy(
                update={"z": 5}
            )
        }
    )
    modified_blocks = [moved_die if block.id == "die" else block for block in model.blocks]
    model_with_gap = model.model_copy(update={"blocks": modified_blocks})

    with pytest.raises(ValueError, match="contiguous"):
        export_pta_xml(model_with_gap)
