"""Read complete per-preset parameter records without the Flotherm installation."""

from tools.data_library.catalog_storage import read_catalog_entry
from tools.data_library.material_catalog import MaterialCatalog
from tools.data_library.runtime_data import read_default_value, read_defaults


class PresetCatalog:
    """Standalone native catalog; does not inherit reduced-template fallbacks."""

    def list_ids(self, family: str | None = None) -> list[str]:
        index = read_defaults("presets/index.json", "packstudio.preset-index/v1")
        return [
            name
            for name, entry in index["presets"].items()
            if family is None or entry["family"] == family
        ]

    def read(self, preset_id: str) -> dict:
        try:
            entry = read_default_value(
                "presets/index.json", "packstudio.preset-index/v1", "presets", preset_id
            )
        except KeyError as error:
            raise ValueError(f"unknown catalog preset: {preset_id}") from error
        payload = read_catalog_entry(
            f"presets/{entry['file']}", "packstudio.preset/v1", entry["sha256"]
        )
        if payload["id"] != preset_id or payload["family"] != entry["family"]:
            raise ValueError(f"preset identity mismatch: {preset_id}")
        names = set(MaterialCatalog().list_names())
        if missing := set(payload["material_references"]) - names:
            raise ValueError(f"unresolved preset materials: {sorted(missing)}")
        return payload

    def read_branch(
        self, preset_id: str, branch: str = "default", *, resolve_materials: bool = False
    ) -> dict:
        payload = self.read(preset_id)
        if branch not in payload["branches"]:
            raise ValueError(f"unknown preset branch: {preset_id}/{branch}")
        result = payload["branches"][branch]
        if resolve_materials:
            materials = MaterialCatalog()
            result["materials"] = {
                name: materials.read(name) for name in payload["material_references"]
            }
        return result
