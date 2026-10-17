"""Independent rectangle clipping, never summing overlapping native solid volumes."""

from dataclasses import replace

from tools.floxml_validation.reader import Box

GEOMETRY_ABS_MM = 1e-7
PROPERTY_REL = 1e-7
PROPERTY_ABS = 1e-8


def intersection(left: Box, right: Box):
    low = tuple(max(a, b) for a, b in zip(left.origin, right.origin, strict=True))
    high = tuple(min(a, b) for a, b in zip(left.high, right.high, strict=True))
    return low, high


def overlap_volume(left, right):
    volume = 1.0
    for index in range(3):
        width = min(
            left.origin[index] + left.size[index], right.origin[index] + right.size[index]
        ) - max(left.origin[index], right.origin[index])
        if width <= 1e-10:
            return 0.0
        volume *= width
    return volume


def subtract(box: Box, cutter: Box):
    if not overlap_volume(box, cutter):
        return [box]
    low, high = intersection(box, cutter)
    if any(b - a <= 1e-10 for a, b in zip(low, high, strict=True)):
        return [box]
    # Peel slabs one axis at a time; the remainder shrinks to the intersection.
    minimum, maximum, pieces = list(box.origin), list(box.high), []
    for axis in range(3):
        for start, end in [(minimum[axis], low[axis]), (high[axis], maximum[axis])]:
            if end - start > 1e-10:
                origin, top = minimum.copy(), maximum.copy()
                origin[axis], top[axis] = start, end
                pieces.append(
                    replace(
                        box,
                        origin=tuple(origin),
                        size=tuple(b - a for a, b in zip(origin, top, strict=True)),
                    )
                )
        minimum[axis], maximum[axis] = low[axis], high[axis]
    return pieces


def partition(boxes: list[Box]):
    accepted = []
    blockers = []
    for box in sorted(boxes, key=lambda b: (b.priority, b.volume, b.identity or b.name)):
        pieces = [box]
        # The union of earlier original boxes equals the union of their partition.
        # Clip against originals to avoid propagating unrelated fragment seams.
        for previous in blockers:
            pieces = [part for piece in pieces for part in subtract(piece, previous)]
        accepted.extend(pieces)
        blockers.append(box)
    return accepted


def totals(boxes, materials):
    result = {"volume_mm3": 0.0, "mass_kg": 0.0, "heat_capacity_j_k": 0.0}
    by_role = {}
    for box in boxes:
        rho, cp = materials[box.material][3:]
        values = (box.volume, box.volume * 1e-9 * rho, box.volume * 1e-9 * rho * cp)
        role = by_role.setdefault(box.role, dict.fromkeys(result, 0.0))
        for key, value in zip(result, values, strict=True):
            result[key] += value
            role[key] += value
    return {**result, "by_role": by_role}
