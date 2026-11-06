"""Independent top/inner copper thickness and depth probes for WB PBGA."""

from tools.dotnet_core import resolve_values
from tools.floscript.des import read_des, write_des


def cases(baseline, inputs):
    inputs.mkdir(parents=True, exist_ok=True)
    result = []
    combinations = (
        (0.01, 0.02, 0.2),
        (0.01, 0.036, 0.2),
        (0.01, 0.06, 0.2),
        (0.018, 0.036, 0.2),
        (0.03, 0.036, 0.2),
        (0.01, 0.036, 0.25),
    )
    for top, inner, depth in combinations:
        identifier = f"metal-depth-t{top:g}-i{inner:g}-d{depth:g}"
        data = read_des(baseline)
        data.update(
            tz1=str(top), tz2=str(inner), z2=str(depth), via_con2="CHECKED", via_con3="UNCHECKED"
        )
        path = inputs / (identifier + ".des")
        write_des(path, data)
        payload = {"template_id": "pbga_wb", "overrides": {"substrate.layers": "4-Layer"}}
        rows = resolve_values(payload)["metal.layers"]
        rows[0]["thickness"] = top
        rows[1].update(thickness=inner, depth=depth, disconnect=True)
        rows[2]["disconnect"] = False
        payload["overrides"]["metal.layers"] = rows
        result.append(
            {
                "id": identifier,
                "commands": [f'<load_des filename="{path.resolve()}"/>'],
                "request": payload,
                "input_des": path.name,
            }
        )
    return result
