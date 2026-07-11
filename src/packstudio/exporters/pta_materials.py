from lxml import etree

from packstudio.domain.materials import Material
from packstudio.exporters.pta_constants import (
    ARRAY_NAMESPACE,
    MEDIA_NAMESPACE,
    MODEL_NAMESPACE,
    XSI_NAMESPACE,
)


def append_materials(parent: etree._Element, materials: list[Material]) -> None:
    container = etree.SubElement(
        parent,
        etree.QName(MODEL_NAMESPACE, "Materials"),
        nsmap={"a": ARRAY_NAMESPACE},
    )
    for material in materials:
        entry = etree.SubElement(
            container,
            etree.QName(ARRAY_NAMESPACE, "KeyValueOfstringMaterialGyu7GfTz"),
        )
        etree.SubElement(entry, etree.QName(ARRAY_NAMESPACE, "Key")).text = material.id
        value = etree.SubElement(entry, etree.QName(ARRAY_NAMESPACE, "Value"))
        _append_material_value(value, material)


def append_block_color(parent: etree._Element, color: str) -> None:
    element = etree.SubElement(
        parent,
        etree.QName(MODEL_NAMESPACE, "Color"),
        nsmap={"a": MEDIA_NAMESPACE},
    )
    red, green, blue = (int(color[index : index + 2], 16) for index in (1, 3, 5))
    values = {
        "A": "255",
        "B": str(blue),
        "G": str(green),
        "R": str(red),
        "ScA": "1",
        "ScB": _format_number(_srgb_to_linear(blue / 255)),
        "ScG": _format_number(_srgb_to_linear(green / 255)),
        "ScR": _format_number(_srgb_to_linear(red / 255)),
    }
    for name, value in values.items():
        etree.SubElement(element, etree.QName(MEDIA_NAMESPACE, name)).text = value


def _append_material_value(parent: etree._Element, material: Material) -> None:
    _nil_element(parent, "BiRerong", text=_format_number(material.specific_heat))
    _nil_element(parent, "Chi0")
    _nil_element(parent, "CouplingMatrixForSaw")
    etree.SubElement(parent, etree.QName(MODEL_NAMESPACE, "DaoreXishu")).text = _conductivity_text(
        material
    )
    for name in (
        "DielectricLossFactorForSaw",
        "Eg0",
        "ElasticMatrixForSaw",
        "Epsilon",
        "EpsilonForSaw",
        "EpsilonVectorForSaw",
    ):
        _nil_element(parent, name)
    etree.SubElement(parent, etree.QName(MODEL_NAMESPACE, "MaterialKindForSaw")).text = "压电材料"
    _nil_element(parent, "MechanicalDampingFactorForSaw")
    _nil_element(parent, "Midu", text=_format_number(material.density))
    for name in (
        "MiduForSaw",
        "MuN",
        "MuP",
        "Nc",
        "Nv",
        "PoissonsRatioForSaw",
        "WaveSpeedForSaw",
        "YoungsModulusForSaw",
    ):
        _nil_element(parent, name)


def _conductivity_text(material: Material) -> str:
    conductivity = material.conductivity
    if (
        abs(conductivity.x - conductivity.y) <= 1e-12
        and abs(conductivity.x - conductivity.z) <= 1e-12
    ):
        return _format_number(conductivity.x)
    return ",".join(
        _format_number(value) for value in (conductivity.x, conductivity.y, conductivity.z)
    )


def _nil_element(parent: etree._Element, name: str, text: str | None = None) -> None:
    element = etree.SubElement(parent, etree.QName(MODEL_NAMESPACE, name))
    if text is None:
        element.set(etree.QName(XSI_NAMESPACE, "nil"), "true")
    else:
        element.text = text


def _srgb_to_linear(value: float) -> float:
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def _format_number(value: float) -> str:
    return f"{value:.12g}"
