"""Resolve native PACK material names from the independent JSON material library."""

from packstudio.catalog_storage import read_catalog_entry
from packstudio.default_parameters import read_defaults


class MaterialCatalog:
    """Read offline material definitions; names are exact, unique reference keys."""

    def list_names(self, category: str | None = None) -> list[str]:
        index = read_defaults("materials/index.json", "packstudio.material-index/v1")
        return [
            name
            for name, entry in index["materials"].items()
            if category is None or entry["category"] == category
        ]

    def read(self, name: str) -> dict:
        index = read_defaults("materials/index.json", "packstudio.material-index/v1")
        if name not in index["materials"]:
            raise ValueError(f"unknown catalog material: {name}")
        entry = index["materials"][name]
        payload = read_catalog_entry(
            f"materials/{entry['file']}", "packstudio.material/v1", entry["sha256"]
        )
        if payload["name"] != name or payload["category"] != entry["category"]:
            raise ValueError(f"material identity mismatch: {name}")
        return payload
