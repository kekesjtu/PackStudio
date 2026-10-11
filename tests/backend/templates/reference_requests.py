"""Explicit inputs used to create archived FloXML, independent of current defaults."""

import json
from pathlib import Path

from packstudio.templates.package_library.catalog import default_request, definition


def reference_request(template_id: str, overrides: dict | None = None):
    payload = json.loads(
        Path(__file__).with_name("reference_inputs.json").read_text(encoding="utf-8")
    )
    values = payload[template_id]
    changes = overrides or {}
    values.update({key.removeprefix(f"{template_id}."): value for key, value in changes.items()})
    item = definition(template_id)
    request = default_request(template_id)
    return request.model_copy(
        update={
            "overrides": {
                field.target_id(template_id): values[field.key]
                for field in item.fields
                if field.key in values
                and all(values.get(key) == value for key, value in field.visible_when.items())
                and all(values.get(key) == value for key, value in field.enabled_when.items())
            }
        }
    )
