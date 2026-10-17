"""WB copper/laminate mixtures from the selected preset's layer coverages."""

from packstudio.domain.materials import Material
from packstudio.templates.package_library.core.materials import material_id_for_name
from packstudio.templates.package_library.core.mixtures import mix_material
from packstudio.templates.package_library.core.parameters import TemplateRequest


def wirebond_copper(
    branch: dict, request: TemplateRequest, available: dict[str, Material]
) -> list[Material]:
    layers = branch["groups"]["metalLayers"]
    metal = available[material_id_for_name(layers["properties"]["materialOfMetal"]["value"])]
    matrix = available[request.material_assignments["group-substrate"]]
    coverages = {
        row["index"]: row["coverage_percent"] / 100
        for row in layers["metal_layers"]
        if row["status"] == "specified"
    }
    flag = branch["groups"]["dieFlagAndSolderMask"]["properties"]
    flag_fraction = flag["coveragePercentageCf"]["value"] / 100
    return [
        mix_material(available[identifier], metal, matrix, fraction, set("xyz"))
        for identifier, fraction in [
            ("wirebond-trace-top", coverages[0]),
            ("wirebond-trace-bottom", coverages[5]),
            ("wirebond-die-flag", flag_fraction),
        ]
    ]
