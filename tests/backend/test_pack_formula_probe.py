"""Independent native arithmetic checks for combined wire inputs and via plating."""

import os
from pathlib import Path

import pytest

from packstudio.templates.package_library.catalog import default_request, generate
from packstudio.templates.package_library.core.materials import material
from tools.pack_reference.formula import NativeFormulaProbe

INSTALLATION = os.environ.get("PACK_NATIVE_INSTALLATION")
pytestmark = pytest.mark.skipif(
    not INSTALLATION or os.name != "nt", reason="requires the reviewed Windows PACK installation"
)


@pytest.fixture(scope="module")
def native():
    return NativeFormulaProbe(Path(INSTALLATION))


@pytest.mark.parametrize(
    ("count", "length", "diameter"), [(32, 2, 0.03), (31, 2.2, 0.03), (40, 1.8, 0.033)]
)
def test_combined_pqfp_inputs_match_native_realization_helper(native, count, length, diameter):
    request = default_request("pqfp").model_copy(
        update={
            "overrides": {
                "pqfp.bond_wire.count": count,
                "pqfp.bond_wire.length_x": length,
                "pqfp.bond_wire.diameter": diameter,
            }
        }
    )
    actual = next(m for m in generate(request).materials if m.id == "pqfp-bondwire-x")
    expected = native.wire(
        0.978,
        2.1,
        diameter,
        diameter,
        length,
        int(count / 4),
        material("gold"),
        material("epoxy-mold"),
    )
    assert actual.conductivity.x == pytest.approx(expected["conductivity"], rel=1e-11)
    assert actual.density == pytest.approx(expected["density"], rel=1e-11)
    assert actual.specific_heat == pytest.approx(expected["specific_heat"], rel=1e-11)


@pytest.mark.parametrize("plating", [0.015, 0.0225, 0.0275, 0.04])
def test_plated_via_air_and_shell_match_native_realization_helper(native, plating):
    request = default_request("chip_array").model_copy(
        update={"overrides": {"chip_array.vias.plating": plating}}
    )
    actual = next(m for m in generate(request).materials if m.id == "chip-array-via")
    expected = native.plated_via(0.2 - 2 * plating, 0.2, 0.2, material("copper"), material("bt"))
    assert actual.conductivity.x == pytest.approx(expected["conductivity"], rel=1e-11)
    assert actual.density == pytest.approx(expected["density"], rel=1e-11)
    assert actual.specific_heat == pytest.approx(expected["specific_heat"], rel=1e-11)
