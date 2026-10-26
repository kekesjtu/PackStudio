"""Apply preset defaults before explicit request inputs, without mutating either."""

from packstudio.templates.package_library.core.definitions import PresetOption, TemplateDefinition
from packstudio.templates.package_library.core.parameters import BgaConfiguration, TemplateRequest


def resolve_preset_request(
    definition: TemplateDefinition,
    request: TemplateRequest,
) -> tuple[TemplateRequest, PresetOption | None]:
    footprint = next((field for field in definition.fields if field.control == "footprint"), None)
    if footprint is None:
        return request, None
    choice = request.overrides.get(footprint.target_id(definition.id), footprint.default)
    preset = next((item for item in footprint.presets if item.value == choice), None)
    if preset is None or preset.bga is None:
        return request, preset
    configuration = preset.bga.model_dump()
    if request.bga is not None:
        changes = request.bga.model_dump(include=request.bga.model_fields_set)
        if changes.get("representation") is None:
            changes.pop("representation", None)
        configuration.update(changes)
        if (
            "solder_removal_enabled" in request.bga.model_fields_set
            and not request.bga.solder_removal_enabled
            and "omitted_cells" not in request.bga.model_fields_set
        ):
            configuration["omitted_cells"] = []
    return request.model_copy(
        update={"bga": BgaConfiguration.model_validate(configuration)}
    ), preset
