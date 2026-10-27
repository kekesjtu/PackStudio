"""PACK wizard initialization before explicit component edits."""

from packstudio.preset_catalog import PresetCatalog
from packstudio.templates.package_library.core.native_presets import (
    at_path,
    native_value,
    read_binding,
)


def initialize_family_values(template, values, overrides):
    if template == "chip_array" and overrides.get("chip_array.substrate.layers") == "4-Layer":
        branch = PresetCatalog().read_branch(values["footprint.size"], "four_layer")
        values["substrate.thickness"] = branch["groups"]["overallPackage"]["properties"][
            "substrateThicknessA2"
        ]["value"]
        values["metal.layers"] = native_value(
            "metal.layers", branch["groups"]["metalLayers"]["metal_layers"]
        )
    if template == "pbga_wb":
        layer = overrides.get("pbga_wb.substrate.layers", values["substrate.layers"])
        if layer == "4-Layer":
            branch = PresetCatalog().read_branch(values["footprint.size"], "four_layer")
            binding = read_binding(template)
            for key, path in binding["parameters"].items():
                if key not in values:
                    continue
                item = at_path(branch, path)
                if isinstance(item, list):
                    item = {"value": item}
                if isinstance(item, bool):
                    values[key] = item
                elif "value" in item:
                    values[key] = native_value(key, item["value"], disconnect=True)
            values["substrate.layers"] = layer
    if template in {"pqfp", "sop"} and overrides.get(
        f"{template}.package.exposed_pad", values["package.exposed_pad"]
    ):
        values["flag.downset"] = overrides.get(f"{template}.leads.height", values["leads.height"])
        values["thermal_land.thickness"] = 0.07
        values["thermal_land.enabled"] = True
