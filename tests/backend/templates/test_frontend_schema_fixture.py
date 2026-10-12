"""Keep the real-schema frontend transition regression fixtures aligned with the API."""

import json
from pathlib import Path

import pytest

from packstudio.templates.package_library.catalog import default_request, schema

FIXTURE = Path(__file__).parents[2] / "frontend/fixtures/flipChipSchema.json"


@pytest.mark.parametrize("template_id", ["cbga_fc", "pbga_fc"])
def test_frontend_transition_fixture_matches_current_schema(template_id):
    stored = json.loads(FIXTURE.read_text(encoding="utf-8"))[template_id]
    fields = [f for step in schema(template_id)["steps"] for f in step["fields"]]
    footprint = next(f for f in fields if f["control"] == "footprint")
    selected = next(f for f in stored["fields"] if f["control"] == "footprint")["options"]
    assert footprint["default"] in selected
    assert len(selected) == 2
    for key in ("preset_values", "preset_bga", "preset_materials", "preset_notes", "option_labels"):
        if footprint.get(key):
            footprint[key] = {k: v for k, v in footprint[key].items() if k in selected}
    footprint["options"] = footprint["supported_values"] = selected
    assert stored["fields"] == fields
    assert stored["request"] == default_request(template_id).model_dump(mode="json")
