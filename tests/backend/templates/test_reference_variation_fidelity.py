from pathlib import Path

import pytest
from reference_cover_cases import cover_numeric_cases
from reference_variation_fidelity import (
    _cover_cases,
    _native_geometry,
    _reference_geometry,
    _variation_cases,
)


@pytest.mark.parametrize("template_id,field,value,model_path", _variation_cases())
def test_handwritten_numeric_geometry_matches_single_variable_floxml(
    template_id: str,
    field: str,
    value: float,
    model_path: Path,
) -> None:
    expected = _reference_geometry(model_path)
    actual = _native_geometry(template_id, field, value)

    assert actual == expected, {
        "missing": list((expected - actual).elements())[:8],
        "unexpected": list((actual - expected).elements())[:8],
    }


@pytest.mark.parametrize("template_id,cover_type,model_path", _cover_cases())
def test_handwritten_flip_cover_branches_match_floxml(
    template_id: str,
    cover_type: str,
    model_path: Path,
) -> None:
    expected = _reference_geometry(model_path)
    actual = _native_geometry(template_id, "cover.type", cover_type)

    assert actual == expected


@pytest.mark.parametrize("template_id,overrides,model_path", cover_numeric_cases())
def test_handwritten_flip_cover_numeric_variations_match_floxml(
    template_id: str,
    overrides: dict[str, object],
    model_path: Path,
) -> None:
    expected = _reference_geometry(model_path)
    actual = _native_geometry(template_id, overrides)

    assert actual == expected
