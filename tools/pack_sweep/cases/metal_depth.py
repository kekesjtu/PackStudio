"""Independent top/inner copper thickness and depth probes for WB PBGA."""

import json

from packstudio.templates.package_library.catalog import definition
from packstudio.templates.package_library.core.parameters import TemplateRequest
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
        request = TemplateRequest(
            template_id="pbga_wb", overrides={"pbga_wb.substrate.layers": "4-Layer"}
        )
        rows = definition("pbga_wb").validate_request(request).table("metal.layers")
        rows[0]["thickness"] = top
        rows[1].update(thickness=inner, depth=depth, disconnect=True)
        rows[2]["disconnect"] = False
        payload = request.model_dump(mode="json")
        payload["overrides"]["pbga_wb.metal.layers"] = json.dumps(rows)
        result.append(
            {
                "id": identifier,
                "commands": [f'<load_des filename="{path.resolve()}"/>'],
                "request": payload,
                "input_des": path.name,
            }
        )
    return result
