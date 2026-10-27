"""PACK surface/radiation attributes on the external package constituents."""

from lxml import etree


def enabled(model):
    return model.template_id in {"chip_array", "cbga_fc", "pbga_fc"}


def append_attributes(attributes, model):
    if not enabled(model):
        return
    surface = etree.SubElement(etree.SubElement(attributes, "surfaces"), "surface_att")
    etree.SubElement(surface, "name").text = model.name
    etree.SubElement(surface, "emissivity").text = "0.8"
    radiation = etree.SubElement(etree.SubElement(attributes, "radiations"), "radiation_att")
    etree.SubElement(radiation, "name").text = model.template_id
    etree.SubElement(radiation, "surface").text = "subdivided_radiating"
    etree.SubElement(radiation, "subdivided_surface_tolerance").text = repr(
        model.metadata["native_grid_length_mm"] * 0.0001
    )


def append_references(element, block, model):
    if not enabled(model):
        return
    source = block.metadata.get("boolean_source_id")
    ids = (
        {"encapsulant"}
        if model.template_id == "chip_array"
        else {"substrate", "lid", "thermal-plate", "encapsulant"}
    )
    if source in ids:
        etree.SubElement(element, "all_surface").text = model.name
        etree.SubElement(element, "all_radiation").text = model.template_id
