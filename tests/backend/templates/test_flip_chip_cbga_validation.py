import pytest
from pydantic import ValidationError

from packstudio.templates.flip_chip_cbga.parameters import FlipChipCbgaParameters


def test_array_outside_parent_envelope_is_rejected() -> None:
    defaults = FlipChipCbgaParameters()
    oversized = defaults.flip_chip_bumps.model_copy(update={"columns": 20})

    with pytest.raises(ValidationError, match="must fit inside the die"):
        FlipChipCbgaParameters(flip_chip_bumps=oversized)


def test_heat_slug_outside_substrate_envelope_is_rejected() -> None:
    defaults = FlipChipCbgaParameters()
    oversized_slug = defaults.heat_slug.model_copy(
        update={"enabled": True, "length": 6.5, "width": 6.5}
    )

    with pytest.raises(ValidationError, match="heat slug must fit"):
        FlipChipCbgaParameters(heat_slug=oversized_slug)


@pytest.mark.parametrize(
    ("update", "message"),
    [
        ({"enabled": True, "length": 1.8}, "extend beyond the die"),
        ({"enabled": True, "length": 6.5}, "fit inside the substrate"),
    ],
)
def test_invalid_encapsulant_envelopes_are_rejected(
    update: dict[str, object], message: str
) -> None:
    defaults = FlipChipCbgaParameters()

    with pytest.raises(ValidationError, match=message):
        FlipChipCbgaParameters(encapsulant=defaults.encapsulant.model_copy(update=update))
