"""Read normalized PackStudio presets without the Flotherm installation."""

from tools.data_library.catalog_storage import read_catalog_entry
from tools.data_library.runtime_data import read_default_value, read_defaults


class PresetCatalog:
    """Internal values, material IDs and layouts; no native property projection."""

    def list_ids(self, family: str | None = None) -> list[str]:
        index = read_defaults("presets/index.json", "packstudio.preset-index/v2")
        return [
            name
            for name, entry in index["presets"].items()
            if family is None or entry["family"] == family
        ]

    def read(self, preset_id: str) -> dict:
        try:
            entry = read_default_value(
                "presets/index.json", "packstudio.preset-index/v2", "presets", preset_id
            )
        except KeyError as error:
            raise ValueError(f"unknown catalog preset: {preset_id}") from error
        payload = read_catalog_entry(
            f"presets/{entry['file']}", "packstudio.preset/v2", entry["sha256"]
        )
        if payload["id"] != preset_id or payload["family"] != entry["family"]:
            raise ValueError(f"preset identity mismatch: {preset_id}")
        return payload

    def read_branch(self, preset_id: str, branch: str = "default") -> dict:
        payload = self.read(preset_id)
        if branch not in payload["branches"]:
            raise ValueError(f"unknown preset branch: {preset_id}/{branch}")
        result = payload["branches"][branch]
        return result
