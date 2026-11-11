"""DES round trips for native matrix lists and CSV attachments."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from tools.floscript.des import read_des


def cases(baselines: Path, inputs: Path, *, families=None):
    inputs.mkdir(parents=True, exist_ok=True)
    result = []

    def add(identifier, family, changes, request_changes=None, csv=None, via_map=None):
        data = read_des(baselines / f"{family}-baseline.des")
        data.update(changes)
        path = inputs / f"{identifier}.des"
        with ZipFile(path, "w", ZIP_DEFLATED) as archive:
            archive.writestr(path.name, "".join(f"{k}|{v}\n" for k, v in data.items()))
            if csv is not None:
                archive.writestr(path.stem + ".var2", csv)
            if via_map is not None:
                archive.writestr(path.stem + ".var3", via_map)
        result.append(
            {
                "id": identifier,
                "commands": [f'<load_des filename="{path.resolve()}"/>'],
                "request": {"template_id": family, **(request_changes or {})},
                "input_des": path.name,
            }
        )

    for family in ("chip_array", "cbga_fc", "pbga_fc"):
        if families is not None and family not in families:
            continue
        for center in (False, True):
            cells = ":".join(f"{c}x{r}" for c in range(5) for r in range(5) if (r, c) != (0, 0))
            changes = dict(
                MD="5",
                ME="5",
                balls=cells,
                staggered_matrix="CHECKED",
                depop_center="CHECKED" if center else "UNCHECKED",
                MDp="2",
                MEp="2",
                radio_BGA_modeling="3",
            )
            add(
                f"{family}-explicit-{center}",
                family,
                changes,
                {
                    "overrides": {
                        "bga.rows": 5,
                        "bga.columns": 5,
                        "bga.representation": "discrete",
                        "bga.solder_removal_enabled": True,
                        "bga.populated_rows": 2,
                        "bga.populated_columns": 2,
                        "bga.staggered": True,
                        "bga.omitted_cells": [{"row": 0, "column": 0}],
                    },
                },
            )
        for points in (
            [],
            [
                {"id": "A", "x": -1.1, "y": 0.3},
                {"id": "B", "x": 0.25, "y": -0.7},
                {"id": "C", "x": 0.25, "y": -0.7},
            ],
        ):
            add(
                f"{family}-csv-{len(points)}",
                family,
                dict(
                    csvBGA="CHECKED",
                    central_balls="CHECKED",
                    MDc="2",
                    MEc="2",
                    staggered_matrix="CHECKED",
                    radio_BGA_modeling="3",
                ),
                {
                    "overrides": {
                        "bga.representation": "discrete",
                        "bga.ball_map_enabled": True,
                        "bga.ball_map": points,
                        "bga.staggered": True,
                        "bga.center_solder_enabled": True,
                        "bga.center_solder_rows": 2,
                        "bga.center_solder_columns": 2,
                    }
                },
                "\n".join(f"{p['id']},{p['x']},{p['y']}" for p in points),
            )
        add(
            f"{family}-even-staggered",
            family,
            dict(MD="5", ME="4", staggered_matrix="CHECKED", radio_BGA_modeling="3"),
            {
                "overrides": {
                    "bga.rows": 4,
                    "bga.columns": 5,
                    "bga.representation": "discrete",
                    "bga.staggered": True,
                },
            },
        )
    for mode in ("discrete", "equivalent"):
        for isotropic in (False, True):
            if families is not None and "pbga_fc" not in families:
                continue
            add(
                f"core-depop-{mode}-{isotropic}",
                "pbga_fc",
                dict(
                    NVx="3",
                    NVy="4",
                    dv="0.2",
                    ev="0.5",
                    tpl="0.025",
                    radio_Via_modeling="3" if mode == "discrete" else "4",
                    k_substr="BT" if isotropic else "Substrate PBGAFC (Typical)",
                ),
                {
                    "overrides": {
                        "vias.enabled": True,
                        "vias.columns": 3,
                        "vias.rows": 4,
                        "vias.diameter": 0.2,
                        "vias.pitch": 0.5,
                        "vias.plating": 0.025,
                        "vias.modeling": mode,
                        "vias.omitted_cells": [
                            {"row": r, "column": c}
                            for r in range(4)
                            for c in range(3)
                            if (r, c) != (0, 0)
                        ],
                    },
                    "material_assignments": {"group-substrate": "bt"} if isotropic else {},
                },
                via_map="0x0",
            )
    return result
