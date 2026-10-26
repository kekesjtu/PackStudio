import pytest

from tools.pack_option_rules import decision


def entry(prop, location="die", label=""):
    return {"property_name": prop, "ui_location": location, "label": label}


@pytest.mark.parametrize("prop", ["outlineType", "dieType", "nonUniformDieHeat"])
def test_only_confirmed_scope_rules_are_marked_as_tradeoffs(prop):
    assert decision("pqfp", entry(prop))[0] == "explicit_tradeoff"


@pytest.mark.parametrize(
    "prop", ["staggeredMatrix", "solderBallMap", "exposedPad", "userDefinedLeadframeCoverage"]
)
def test_removed_historical_restrictions_are_not_approved_tradeoffs(prop):
    result = decision("pqfp", entry(prop))
    assert result is None or result[0] != "explicit_tradeoff"


def test_current_bump_tensor_is_a_gap_against_the_isotropic_decision():
    result = decision("cbga_fc", entry("solderBumpModeling", "solder_bumps"))
    assert result[0] == "implementation_gap"


def test_bga_representation_uses_the_existing_parameter_mapping():
    assert decision("cbga_fc", entry("modelSolderBallArrayAs", "solder_balls")) is None
