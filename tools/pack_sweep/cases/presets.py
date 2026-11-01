"""Native standard-outline initialization for every retained wirebond footprint."""

from tools.data_library.preset_catalog import PresetCatalog


def append_presets(add):
    catalog = PresetCatalog()
    for family, native in [
        ("pqfp", "pqfp"),
        ("sop", "sop"),
        ("qfn", "qfn"),
        ("pbga_wb", "pbga_wb"),
    ]:
        for index, identifier in enumerate(catalog.list_ids(native)):
            branch = catalog.read_branch(identifier)
            wizard = {"jedecFootprint": identifier}
            if family in {"pqfp", "sop"}:
                wizard[family + "PackageType"] = branch["values"]["package.type"]
            add(
                f"preset-{family}-{index}",
                family,
                overrides={"footprint.size": identifier},
                wizard=wizard,
            )
