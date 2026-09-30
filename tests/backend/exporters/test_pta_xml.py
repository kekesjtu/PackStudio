import pytest
from lxml import etree

from packstudio.domain.enums import BlockFace, BoundaryKind
from packstudio.domain.thermal import BoundaryCondition, SurfaceReference
from packstudio.exporters.pta_constants import (
    ARRAY_NAMESPACE,
    BOUNDARY_NAMESPACE,
    MODEL_NAMESPACE,
    XSI_NAMESPACE,
)
from packstudio.exporters.pta_xml import export_pta_xml
from packstudio.templates.flip_chip_cbga.parameters import MeshParameters, MeshResolution
from packstudio.templates.package_library.catalog import default_request, generate
from packstudio.templates.package_library.core.parameters import TemplateRequest


def test_pta_export_contains_only_input_model_data() -> None:
    model = generate(default_request("flip_chip_cbga"))

    payload = export_pta_xml(model)
    root = etree.fromstring(payload)
    local_names = [etree.QName(element).localname for element in root.iter()]

    assert etree.QName(root).namespace == MODEL_NAMESPACE
    assert etree.QName(root).localname == "Structure"
    assert "Results" not in local_names
    assert "LayerPBResults" not in local_names
    assert "ThermalMaskResults" not in local_names
    assert "Mesh" not in local_names
    assert "MeshSizeXExpression" in local_names


def test_pta_export_preserves_blocks_materials_and_anisotropy() -> None:
    model = generate(default_request("flip_chip_cbga"))
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
    model = generate(TemplateRequest(template_id="flip_chip_cbga", die_power_w=2))
    root = etree.fromstring(export_pta_xml(model))
    namespace = {"m": MODEL_NAMESPACE}
    die_block = root.xpath(".//m:Block[m:Name='Silicon die']", namespaces=namespace)[0]
    source_density = float(die_block.findtext(f"{{{MODEL_NAMESPACE}}}TiReyuan"))
    die = next(block for block in model.blocks if block.name == "Silicon die")
    expected = 2 / (die.size.x * die.size.y * die.size.z * 1e-9)

    assert source_density == pytest.approx(expected, rel=1e-10)


def test_pta_export_writes_convection_face_keys() -> None:
    model = generate(default_request("flip_chip_cbga"))
    die = next(block for block in model.blocks if block.name == "Silicon die")
    external_boundary = BoundaryCondition(
        id="external-cooling",
        name="External cooling",
        kind=BoundaryKind.CONVECTION,
        targets=[
            SurfaceReference(block_id=die.id, face=face)
            for face in (BlockFace.Z_MIN, BlockFace.Z_MAX)
        ],
        convection_coefficient_w_m2k=12,
        ambient_temperature_k=298,
    )
    root = etree.fromstring(
        export_pta_xml(model.model_copy(update={"boundaries": [external_boundary]}))
    )
    namespace = {"m": MODEL_NAMESPACE, "a": ARRAY_NAMESPACE}
    face_keys = root.xpath(".//m:Boundaries//a:string/text()", namespaces=namespace)

    assert face_keys
    assert all(key.startswith("Z|E|") for key in face_keys)
    assert len(face_keys) == 2


def test_pta_export_writes_mesh_controls_without_mesh_entities() -> None:
    root = etree.fromstring(export_pta_xml(generate(default_request("flip_chip_cbga"))))
    namespace = {"m": MODEL_NAMESPACE}
    layers = root.xpath("./m:Layers/m:Layer", namespaces=namespace)
    blocks = root.xpath(".//m:Layers/m:Layer/m:Blocks/m:Block", namespaces=namespace)

    for layer in layers:
        assert all(
            float(layer.findtext(f"{{{MODEL_NAMESPACE}}}MeshSize{axis}Expression")) > 0
            for axis in "XYZ"
        )
    for block in blocks:
        assert all(
            block.findtext(f"{{{MODEL_NAMESPACE}}}MeshSize{axis}Expression") == "0"
            for axis in "XYZ"
        )
    assert not root.xpath(".//m:Mesh", namespaces=namespace)


def test_fine_mesh_profile_is_smaller_than_coarse_profile() -> None:
    def layer_sizes(resolution: MeshResolution) -> list[float]:
        model = generate(
            TemplateRequest(
                template_id="flip_chip_cbga",
                mesh=MeshParameters(resolution=resolution),
            )
        )
        root = etree.fromstring(export_pta_xml(model))
        return [
            float(value)
            for value in root.xpath(
                "./m:Layers/m:Layer/m:MeshSizeXExpression/text()",
                namespaces={"m": MODEL_NAMESPACE},
            )
        ]

    coarse_sizes = layer_sizes(MeshResolution.COARSE)
    fine_sizes = layer_sizes(MeshResolution.FINE)

    assert len(coarse_sizes) == len(fine_sizes)
    assert all(
        fine_size < coarse_size
        for fine_size, coarse_size in zip(fine_sizes, coarse_sizes, strict=True)
    )


def test_pta_export_does_not_inject_cooling_boundaries() -> None:
    root = etree.fromstring(export_pta_xml(generate(default_request("flip_chip_cbga"))))
    namespace = {"m": MODEL_NAMESPACE, "b": BOUNDARY_NAMESPACE}
    default_boundary = root.find(f"{{{MODEL_NAMESPACE}}}OtherThermalBondary")
    names = root.xpath("./m:Boundaries/m:Boundary/m:Name/text()", namespaces=namespace)
    coefficients = root.xpath(
        "./m:Boundaries/m:Boundary/m:ThermalBoundary/b:ConvectionCoefficient/text()",
        namespaces=namespace,
    )

    assert default_boundary is not None
    assert default_boundary.get(f"{{{XSI_NAMESPACE}}}nil") == "true"
    assert names == []
    assert coefficients == []


def test_pta_layers_are_top_to_bottom_with_a_consistent_top_marker() -> None:
    root = etree.fromstring(export_pta_xml(generate(default_request("flip_chip_cbga"))))
    namespace = {"m": MODEL_NAMESPACE}
    layers = root.xpath("./m:Layers/m:Layer", namespaces=namespace)
    layer_blocks = [
        layer.xpath("./m:Blocks/m:Block/m:Name/text()", namespaces=namespace) for layer in layers
    ]
    top_markers = [layer.findtext(f"{{{MODEL_NAMESPACE}}}IsTopLayer") for layer in layers]

    assert len(layers) == 4
    assert layer_blocks[0] == ["Silicon die"]
    assert layer_blocks[-1] == ["solder-ball array equivalent region 1"]
    assert layers[0].findtext(f"{{{MODEL_NAMESPACE}}}Name") == "Layer 1 @ 1.65 mm"
    assert layers[-1].findtext(f"{{{MODEL_NAMESPACE}}}Name") == "Layer 4 @ 0 mm"
    assert root.findtext(f"{{{MODEL_NAMESPACE}}}TopLayerIndex") == "0"
    assert top_markers == ["true", "false", "false", "false"]


def test_pta_template_layers_are_visible_generic_layers() -> None:
    root = etree.fromstring(export_pta_xml(generate(default_request("flip_chip_cbga"))))
    namespace = {"m": MODEL_NAMESPACE}
    layers = root.xpath("./m:Layers/m:Layer", namespaces=namespace)

    for flag in ("IsBottomPackaging", "IsDie", "IsTIM"):
        assert [layer.findtext(f"{{{MODEL_NAMESPACE}}}{flag}") for layer in layers] == [
            "false"
        ] * len(layers)
    assert all(layer.xpath("./m:Blocks/m:Block", namespaces=namespace) for layer in layers)


def test_pta_export_rejects_non_contiguous_layer_stack() -> None:
    model = generate(default_request("flip_chip_cbga"))
    die = next(block for block in model.blocks if block.name == "Silicon die")
    moved_die = die.model_copy(update={"origin": die.origin.model_copy(update={"z": 5})})
    modified_blocks = [moved_die if block.id == die.id else block for block in model.blocks]
    model_with_gap = model.model_copy(update={"blocks": modified_blocks})

    with pytest.raises(ValueError, match="contiguous"):
        export_pta_xml(model_with_gap)
