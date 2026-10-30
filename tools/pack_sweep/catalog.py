"""Load stable sweep inputs; every point belongs to exactly one template."""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from tools.pack_sweep.cases.die_and_fc import cases as die_cases
from tools.pack_sweep.cases.field_correspondence import cases as field_cases
from tools.pack_sweep.cases.wirebond import cases as wirebond_cases


@dataclass
class Point:
    template: str
    id: str
    commands: list[str]
    request: dict | None = None
    origin: str = "fidelity"
    metadata: dict = field(default_factory=dict)
    input_des: Path | None = None

    def __post_init__(self):
        if any(
            not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]*", part)
            for part in (self.template, self.id)
        ):
            raise ValueError("unsafe template or point identifier")

    @property
    def key(self):
        return self.template + "/" + self.id


def legacy_points():
    result = []
    for path in sorted(Path(__file__).with_name("specs").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload["schema"] != "packstudio.sweep-spec/v1":
            raise ValueError(f"unsupported sweep specification: {path}")
        for row in payload["points"]:
            result.append(
                Point(
                    payload["template_id"],
                    row["id"],
                    row["commands"],
                    origin="legacy",
                    metadata={k: v for k, v in row.items() if k not in {"id", "commands"}},
                )
            )
    return result


def fidelity_points():
    return [
        Point(row["request"]["template_id"], row["id"], row["commands"], row["request"])
        for row in die_cases() + wirebond_cases()
    ]


def initial_points():
    native_fields = [
        Point(
            row["template"],
            row["id"],
            row["commands"],
            origin="field_probe",
            metadata=row["metadata"],
        )
        for row in field_cases()
    ]
    result = legacy_points() + fidelity_points() + native_fields
    if len({p.key for p in result}) != len(result):
        raise ValueError("duplicate sweep point")
    return result
