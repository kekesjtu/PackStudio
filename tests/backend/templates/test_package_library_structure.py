from importlib import import_module
from pathlib import Path

import pytest

import packstudio.templates.package_library as package_library

TEMPLATE_MODULES = (
    "bare_die.template",
    "bga.chip_array",
    "bga.pbga_wb",
    "flip_chip.cbga_fc",
    "flip_chip.pbga_fc",
    "leadframe.qfn",
    "leadframe.pqfp",
    "leadframe.sop",
)


@pytest.mark.parametrize("module_name", TEMPLATE_MODULES)
def test_each_handwritten_template_lives_in_an_importable_category(
    module_name: str,
) -> None:
    module = import_module(f"packstudio.templates.package_library.{module_name}")
    assert callable(module.definition)


def test_package_library_root_contains_only_registry_modules() -> None:
    root = Path(package_library.__file__).parent
    root_modules = {path.name for path in root.glob("*.py")}
    assert root_modules == {"__init__.py", "catalog.py"}
