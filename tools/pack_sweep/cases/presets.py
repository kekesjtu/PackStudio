"""Native standard-outline initialization for every retained wirebond footprint."""

from packstudio.preset_catalog import PresetCatalog


def append_presets(add):
    catalog = PresetCatalog()
    for family, native in [
        ("pqfp", "pqfp"),
        ("sop", "tsop_conv"),
        ("qfn", "QFN"),
        ("pbga_wb", "pbga_wb"),
    ]:
        for index, identifier in enumerate(catalog.list_ids(native)):
            branch = catalog.read_branch(identifier)
            wizard = {"jedecFootprint": identifier}
            for key in ("pqfpPackageType", "sopPackageType"):
                if key in branch["wizard"]:
                    wizard[key] = branch["wizard"][key]["value"]
            add(
                f"preset-{family}-{index}",
                family,
                overrides={"footprint.size": identifier},
                wizard=wizard,
            )
