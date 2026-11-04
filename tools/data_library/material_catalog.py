"""Resolve native PACK material names from the independent JSON material library."""

from tools.data_library.runtime_data import read_default_keys, read_default_value, read_defaults


class MaterialCatalog:
    """Read offline material definitions; names are exact, unique reference keys."""

    def list_names(self, category: str | None = None) -> list[str]:
        if category is None:
            return list(
                read_default_keys(
                    "materials/index.json", "packstudio.material-index/v1", "materials"
                )
            )
        index = read_defaults("materials/index.json", "packstudio.material-index/v1")
        return [
            name
            for name, entry in index["materials"].items()
            if category is None or entry["category"] == category
        ]

    def read(self, name: str) -> dict:
        try:
            entry = read_default_value(
                "materials/index.json", "packstudio.material-index/v1", "materials", name
            )
        except KeyError as error:
            raise ValueError(f"unknown catalog material: {name}") from error
        payload = read_defaults(f"materials/{entry['file']}", None)
        if payload["name"] != name or payload["group"] != entry["category"]:
            raise ValueError(f"material identity mismatch: {name}")
        return payload
