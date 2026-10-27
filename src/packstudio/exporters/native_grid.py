"""Native local-grid constraints in SI; these entities carry no material."""

from lxml import etree


def append_grid_attributes(attributes, model):
    data = model.metadata
    if "native_grid_enabled" not in data:
        return
    constraints = etree.SubElement(attributes, "grid_constraints")
    length = min(data["native_grid_length_mm"], data["native_grid_width_mm"]) * 0.001
    height = data["native_grid_height_mm"] * 0.001
    coarse = data["native_grid_density"] == "coarse"
    fine = data["native_grid_density"] == "fine"
    for name, spacing in [
        ("keypoint", length / (20 if fine else 10)),
        ("keypoint_z", height / (10 if fine else 6)),
    ]:
        constraint = etree.SubElement(constraints, "grid_constraint_att")
        text(constraint, "name", name)
        text(constraint, "enable_min_cell_size", "true")
        text(constraint, "min_cell_size", "0.000002")
        control(constraint, coarse, spacing)
        for side, inflation in [("low", 0.0016), ("high", height * 2)]:
            element = etree.SubElement(constraint, side + "_inflation")
            text(element, "inflation_type", "percent" if name == "keypoint" else "size")
            text(
                element,
                "inflation_percent" if name == "keypoint" else "inflation_size",
                "25" if name == "keypoint" else repr(inflation),
            )
            control(element, coarse, spacing)


def append_grid_references(root, model):
    if "native_grid_enabled" not in model.metadata:
        return
    for axis in "xyz":
        text(root, f"{axis}_grid_constraint", "keypoint_z" if axis == "z" else "keypoint")
    text(root, "localized_grid", str(model.metadata["native_grid_enabled"]).lower())


def control(element, coarse, spacing):
    text(element, "number_cells_control", "min_number" if coarse else "max_size")
    text(element, "min_number" if coarse else "max_size", "1" if coarse else repr(spacing))


def text(parent, key, value):
    etree.SubElement(parent, key).text = value
