"""Native standard-outline initialization for every retained wirebond footprint."""

from tools.data_library.runtime_data import read_defaults


def append_presets(add):
    entries = read_defaults("presets/index.json", "packstudio.preset-index/v4")["presets"]
    for family in ("pqfp", "sop", "qfn", "pbga_wb"):
        presets = ((name, entry) for name, entry in entries.items() if entry["family"] == family)
        for index, (identifier, entry) in enumerate(presets):
            wizard = {}
            if family in {"pqfp", "sop"}:
                preset = read_defaults(f"presets/{entry['file']}", None)
                wizard[family + "PackageType"] = preset["Values"]["package.type"]
            add(
                f"preset-{family}-{index}",
                family,
                footprint=identifier,
                wizard=wizard,
            )
