import json
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree

import pytest

from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.catalog import definition
from tests.backend.templates.reference_requests import reference_request

REFERENCE_ROOT = Path(__file__).parents[3] / "flotherm_pack_data" / "templates"

FIELD_PROPERTIES = {
    "bare_die": {
        "die.length": "dieLengthLd",
        "die.width": "dieWidthWd",
        "die.thickness": "dieThicknessTd",
    },
    "cbga_fc": {
        "substrate.length": "substrateLengthD",
        "substrate.width": "substrateWidthE",
        "substrate.thickness": "substrateThicknessA2",
        "die.length": "dieLengthLd",
        "die.width": "dieWidthWd",
        "die.thickness": "dieThicknessTd",
        "bumps.total": "totalNumberOfBumpsMNC4",
        "bumps.diameter": "bumpDiameterBC4",
        "bumps.height": "bumpHeightTC4",
        "bga.columns": "numberOfSolderBallsInXMD",
        "bga.rows": "numberOfSolderBallsInYME",
        "bga.pitch": "ballPitchE",
        "bga.diameter": "ballDiameterB",
        "bga.height": "substrateStandoffA1",
    },
    "pbga_fc": {
        "substrate.length": "substrateLengthD",
        "substrate.width": "substrateWidthE",
        "substrate.thickness": "substrateThicknessA2",
        "die.length": "dieLengthLd",
        "die.width": "dieWidthWd",
        "die.thickness": "dieThicknessTd",
        "bumps.total": "totalNumberOfBumpsMNC4",
        "bumps.diameter": "bumpDiameterBC4",
        "bumps.height": "bumpHeightTC4",
        "bga.columns": "numberOfSolderBallsInXMD",
        "bga.rows": "numberOfSolderBallsInYME",
        "bga.pitch": "ballPitchE",
        "bga.diameter": "ballDiameterB",
        "bga.height": "substrateStandoffA1",
    },
    "pbga_wb": {
        "trace.top_thickness": "topSignalLayerThickness",
        "trace.bottom_thickness": "bottomSignalLayerThickness",
        "package.length": "substrateLengthD",
        "package.width": "substrateWidthE",
        "substrate.thickness": "substrateThicknessA2",
        "encapsulant.length": "lengthLe",
        "encapsulant.width": "widthWe",
        "encapsulant.thickness": "thicknessTe",
        "flag.length": "dieFlagLf",
        "flag.width": "dieFlagWf",
        "solder_mask.thickness": "solderMaskThickness",
        "die.length": "dieLengthLd",
        "die.width": "dieWidthWd",
        "die.thickness": "dieThicknessTd",
        "die.attach": "dieAttachThicknessTda",
        "bond_wire.total": "numberOfBondWiresNw",
        "bond_wire.extent_length": "bondWireExtentLengthLw",
        "bond_wire.extent_width": "bondWireExtentWidthWw",
        "bond_wire.diameter": "bondWireDiameterDw",
        "vias.columns": "numberOfThermalViasInXNVx",
        "vias.rows": "numberOfThermalViasInYNVy",
        "vias.pitch": "viaPitchEv",
        "vias.diameter": "viaDiameterDv",
        "vias.plating": "platingThicknessTpl",
        "bga.columns": "numberOfSolderBallsInXMD",
        "bga.rows": "numberOfSolderBallsInYME",
        "bga.pitch": "ballPitchE",
        "bga.diameter": "ballDiameterB",
        "bga.height": "substrateStandoffA1",
    },
    "chip_array": {
        "trace.top_thickness": "topSignalLayerThickness",
        "trace.bottom_thickness": "bottomSignalLayerThickness",
        "package.length": "lengthD",
        "package.width": "widthE",
        "substrate.thickness": "substrateThicknessA2",
        "encapsulant.thickness": "thicknessTe",
        "solder_mask.thickness": "solderMaskThicknessTsm",
        "die.length": "dieLengthLd",
        "die.width": "dieWidthWd",
        "die.thickness": "dieThicknessTd",
        "die.attach": "dieAttachThicknessTda",
        "bond_wire.extent_length": "extentOfBondWirePadsLw",
        "bond_wire.extent_width": "extentOfBondWirePadsWw",
        "bond_wire.diameter": "bondWireDiameterDw",
        "vias.diameter": "viaDiameterDv",
        "vias.plating": "platingThicknessTpl",
        "vias.offset_x": "viaOffsetInX",
        "vias.offset_y": "viaOffsetInY",
        "bga.columns": "numberOfSolderBallsInXMD",
        "bga.rows": "numberOfSolderBallsInYME",
        "bga.pitch": "ballPitchE",
        "bga.diameter": "ballDiameterB",
        "bga.height": "substrateStandoffA1",
    },
    "qfn": {
        "package.length": "lengthD",
        "package.width": "widthE",
        "package.standoff": "standoffA1",
        "encapsulant.thickness": "encapsulantThicknessA2",
        "die.length": "dieLengthLd",
        "die.width": "dieWidthWd",
        "die.thickness": "dieThicknessTd",
        "die.attach": "dieAttachThicknessTda",
        "pad.length": "dapLengthLp",
        "pad.width": "dapWidthWp",
        "pad.exposed_length": "exposedPADLength",
        "pad.exposed_width": "exposedPADWidth",
        "leads.count_x": "numberOfLeadsOnTopBottomMD",
        "leads.count_y": "numberOfLeadsOnLeftRightME",
        "leads.pitch_x": "pitchInXDirectionEx",
        "leads.pitch_y": "pitchInYDirectionEy",
        "leads.width": "leadWidthB",
        "leads.length": "exposedLeadLengthL",
        "leads.exposed_thickness": "exposedLeadThickness",
        "leads.thickness": "leadThicknessA3",
        "leads.etch": "leadEtch",
        "bond_wire.length_x": "bondWireLengthOnLeftRightLbwx",
        "bond_wire.length_y": "bondWireLengthOnTopBottomLbwy",
        "bond_wire.diameter": "bondWireDiameterDbw",
    },
    "pqfp": {
        "package.length": "lengthD",
        "package.width": "widthE",
        "package.standoff": "standoffA1",
        "body.length": "lengthD1",
        "body.width": "widthE1",
        "body.thickness": "thicknessA2",
        "die.length": "dieLengthLd",
        "die.width": "dieWidthWd",
        "die.thickness": "dieThicknessTd",
        "die.attach": "dieAttachThicknessTda",
        "flag.length": "dieFlagLf",
        "flag.width": "dieFlagWf",
        "flag.coverage": "metalCoverageForDieFlagCf",
        "flag.downset": "dieFlagDownsetDdf",
        "tie_bar.width": "tieBarWidthWtb",
        "leads.count_x": "numberOfLeadsOnTopBottomMD",
        "leads.count_y": "numberOfLeadsOnLeftRightME",
        "leads.pitch": "pitchE",
        "leads.width": "leadWidthB",
        "leads.thickness": "leadThicknessTl",
        "leads.height": "leadframeHeightHl",
        "leads.foot_length": "leadfootLengthWl",
        "leads.gap_x": "leadframeFlagGapG1",
        "leads.gap_y": "leadframeFlagGapG2",
        "bond_wire.length_x": "bondWireLengthOnLeftRightLbwx",
        "bond_wire.length_y": "bondWireLengthOnTopBottomLbwy",
        "bond_wire.count": "numberOfBondWiresN",
        "bond_wire.diameter": "bondWireDiameterDbw",
    },
    "sop": {
        "package.width": "widthE",
        "package.standoff": "standoffA1",
        "body.length": "lengthD1",
        "body.width": "widthE1",
        "body.thickness": "thicknessA2",
        "die.length": "dieLengthLd",
        "die.width": "dieWidthWd",
        "die.thickness": "dieThicknessTd",
        "die.attach": "dieAttachThicknessTda",
        "flag.length": "dieFlagLf",
        "flag.width": "dieFlagWf",
        "flag.thickness": "dieFlagThicknessTf",
        "flag.coverage": "metalCoverageForDieFlagCf",
        "flag.downset": "dieFlagDownsetDdf",
        "tie_bar.width": "tieBarWidthWtb",
        "leads.total": "totalNumberOfLeadsMT",
        "leads.gap": "leadframeFlagGapG1",
        "leads.pitch": "pitchE",
        "leads.width": "leadWidthB",
        "leads.thickness": "leadThicknessTl",
        "leads.height": "leadframeHeightHl",
        "leads.foot_length": "leadfootLengthLft",
        "bond_wire.length": "bondWireLengthLbw",
        "bond_wire.count": "numberOfBondWiresN",
        "bond_wire.diameter": "bondWireDiameterDbw",
    },
}

type GeometryRecord = tuple[float, float, float, float, float, float]


def _record(origin: tuple[float, ...], size: tuple[float, ...]) -> GeometryRecord:
    return tuple(round(value, 8) for value in (*origin, *size))


def _reference_geometry(path: Path) -> Counter[GeometryRecord]:
    root = ElementTree.parse(path).getroot()
    records: Counter[GeometryRecord] = Counter()
    for cuboid in root.findall(".//cuboid"):
        position = cuboid.find("position")
        size = cuboid.find("size")
        assert position is not None and size is not None
        origin = tuple(float(position.findtext(axis, "0")) * 1000 for axis in "xyz")
        dimensions = tuple(float(size.findtext(axis, "0")) * 1000 for axis in "xyz")
        records[_record(origin, dimensions)] += 1
    return records


def _native_geometry(
    template_id: str,
    field: str | dict[str, object],
    value: object = None,
) -> Counter[GeometryRecord]:
    overrides = field if isinstance(field, dict) else {f"{template_id}.{field}": value}
    request = reference_request(template_id, overrides)
    item = definition(template_id)
    built = item.builder(item.validate_request(request), request)
    records = Counter(_record(draft.origin, draft.size) for draft in built.drafts)
    for block in built.blocks:
        if block.structure_type is StructureType.STATIC_AIR:
            continue
        records[
            _record(
                (block.origin.x, block.origin.y, block.origin.z),
                (block.size.x, block.size.y, block.size.z),
            )
        ] += 1
    return records


def _cover_cases() -> list[object]:
    cases = []
    for template_id in ("cbga_fc", "pbga_fc"):
        manifest_path = REFERENCE_ROOT / template_id / "xml_variations.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for item in manifest["variations"]:
            if item["target"]["property"] != "topCover":
                continue
            value = item["target"]["value"]
            if value not in {"lid", "plate", "encapsulant"}:
                continue
            model = REFERENCE_ROOT / template_id / item["artifacts"]["model"]
            cases.append(
                pytest.param(
                    template_id,
                    value,
                    model,
                    id=f"{template_id}-cover-{value}",
                )
            )
    return cases


def _variation_cases() -> list[object]:
    cases = []
    for template_id, mappings in FIELD_PROPERTIES.items():
        manifest_path = REFERENCE_ROOT / template_id / "xml_variations.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        fields_by_property = {property_name: field for field, property_name in mappings.items()}
        for item in manifest["variations"]:
            property_name = item["target"]["property"]
            if (
                item["kind"] != "numeric_parameter"
                or item["comparison_baseline"] != "baseline/model.xml"
                or property_name not in fields_by_property
            ):
                continue
            field = fields_by_property[property_name]
            model = REFERENCE_ROOT / template_id / item["artifacts"]["model"]
            cases.append(
                pytest.param(
                    template_id,
                    field,
                    item["target"]["value"],
                    model,
                    id=f"{template_id}-{field}-{item['variation_id']}",
                )
            )
    return cases
