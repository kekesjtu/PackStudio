import json
import shutil
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

import pytest
from lxml import etree

from tools.floscript import runner
from tools.floscript.des import read_des, write_des
from tools.floscript.script import (
    component_element,
    files,
    new_package_element,
    normalize,
    replay_script,
    validate,
    write_xml,
)

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def installation(tmp_path, monkeypatch):
    install = tmp_path / "installation"
    for name in ("config", "flocentral/flopack/Library", "WinXP/64lib/plugins/platforms"):
        (install / name).mkdir(parents=True)
    (install / "config/settings").write_text("runtime settings")
    (install / "flocentral/flopack/Library/custom.mat").write_text("custom material")
    binary = install / "WinXP/bin"
    binary.mkdir()
    host = binary / "pwsh.exe"
    host.write_bytes(b"test PowerShell host")
    monkeypatch.setattr("tools.floscript.environment.POWERSHELL", host)
    for name in (
        "flopack.exe",
        "flopackrealise.dll",
        "flopackfloxmlhandling.dll",
        "flopackmaterials.dll",
    ):
        (binary / name).write_bytes(b"test binary")
    schemas = install / "examples/FloSCRIPT/Schema"
    schemas.mkdir(parents=True)
    (schemas / "FlopackFloSCRIPTSchema.xsd").write_text("""
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="flopack_xml_log_file"><xs:complexType>
    <xs:sequence><xs:any minOccurs="0" maxOccurs="unbounded" processContents="lax"/></xs:sequence>
    <xs:attribute name="version" type="xs:double" use="required"/>
  </xs:complexType></xs:element>
</xs:schema>""")
    shutil.copytree(ROOT / "output_format/floxml", install / "WinXP/PlugIns/XML_PLUGIN_SCHEMA")
    return install


def successful_launch(directory, _installation, _timeout):
    root = ET.parse(directory / "replay.xml").getroot()
    for command in root:
        if command.tag == "save_des":
            write_des(Path(command.attrib["filename"]), {"key": "value"})
        elif command.tag == "export_floxml":
            shutil.copy2(ROOT / "output_format/floxml/bare-die.floxml", command.attrib["filename"])
    logs = directory / "LogFiles"
    logs.mkdir()
    (logs / "native.xml").write_text('<log><message text="export complete"/></log>')
    return {"exit_code": 0, "seconds": 1, "errors": [], "file_version": "test"}


def test_des_preserves_delimiters_and_rejects_ambiguous_archives(tmp_path):
    path = tmp_path / "parameters.des"
    write_des(path, {"label": "a|b", "enabled": "CHECKED"})
    assert read_des(path) == {"label": "a|b", "enabled": "CHECKED"}
    with ZipFile(path, "a") as archive:
        archive.writestr("second.des", "key|value")
    with pytest.raises(ValueError, match="one DES"):
        read_des(path)
    with pytest.raises(ValueError, match="multiline"):
        write_des(path, {"label": "line\nbreak"})


def test_paths_resolve_inputs_at_source_and_outputs_at_run(tmp_path):
    source = tmp_path / "input/script.xml"
    source.parent.mkdir()
    write_des(source.parent / "input.des", {"key": "value"})
    directory = tmp_path / "run"
    root = ET.fromstring("""<flopack_xml_log_file version="1.0">
      <load_des filename="input.des"/><save_des filename="saved.des"/>
      <load_des filename="saved.des"/><export_floxml filename="model.xml"/>
    </flopack_xml_log_file>""")
    # An intermediate load must explicitly address the run directory.
    root[2].set("filename", str(directory / "saved.des"))
    normalize(root, source, directory)
    inputs, outputs = files(root, directory)
    assert inputs == [source.parent / "input.des"]
    assert [path for _, path in outputs] == [directory / "saved.des", directory / "model.xml"]
    assert root[-1].tag == "quit"


@pytest.mark.parametrize("filename", ["../outside.xml", "run.json", "config/model.xml"])
def test_output_paths_cannot_escape_or_overwrite_runtime(tmp_path, filename):
    directory = tmp_path / "run"
    root = ET.Element("flopack_xml_log_file", version="1.0")
    ET.SubElement(root, "export_floxml", filename=filename)
    with pytest.raises(ValueError, match="output"):
        files(normalize(root, tmp_path / "script.xml", directory), directory)


def test_duplicate_case_ids_and_early_quit_are_rejected(tmp_path):
    with pytest.raises(ValueError, match="duplicate"):
        replay_script([{"id": "a", "commands": []}] * 2, tmp_path)
    with pytest.raises(ValueError, match="invalid"):
        replay_script([{"id": "../escape", "commands": []}], tmp_path)
    root = ET.fromstring("""<flopack_xml_log_file version="1.0">
      <quit/><export_floxml filename="model.xml"/>
    </flopack_xml_log_file>""")
    with pytest.raises(ValueError, match="last command"):
        normalize(root, tmp_path / "script.xml", tmp_path)


def test_script_generation_escapes_dynamic_attributes(tmp_path):
    root = ET.Element("flopack_xml_log_file", version="1.0")
    root.append(new_package_element("Die", {"designName": 'a & b "quoted"'}))
    root.append(component_element("die", "label", "<label>"))
    path = tmp_path / "escaped.xml"
    write_xml(root, path)
    parsed = ET.parse(path).getroot()
    assert parsed[0][0].get("new_value") == 'a & b "quoted"'
    assert parsed[1].get("new_value") == "<label>"


def test_success_records_validated_outputs_and_material_policy(tmp_path, installation, monkeypatch):
    monkeypatch.setattr(runner, "_launch", successful_launch)
    directory = tmp_path / "run"
    result = runner.replay(
        installation, [{"id": "case", "commands": []}], directory, copy_materials=False
    )
    assert result["status"] == "success"
    assert all(result["checks"].values())
    assert len(result["outputs"]) == 2
    assert result["exports"]["case"] == runner.fingerprint(directory / "case.xml")
    assert not list((directory / "central/flopack/Library").iterdir())
    assert (directory / result["launcher_file"]).is_file()
    assert json.loads((directory / "run.json").read_text())["status"] == "success"
    with pytest.raises(FileExistsError, match="already executed"):
        runner.execute(directory, installation)
    second = tmp_path / "with-materials"
    runner.prepare_replay(installation, [{"id": "case", "commands": []}], second)
    assert (second / "central/flopack/Library/custom.mat").is_file()


@pytest.mark.parametrize(
    "failure", ["missing", "bad-xml", "bad-des", "bad-log", "native-error", "timeout"]
)
def test_failed_runs_keep_evidence_and_never_report_success(
    tmp_path, installation, monkeypatch, failure
):
    def launch(directory, install, timeout):
        result = successful_launch(directory, install, timeout)
        if failure == "missing":
            (directory / "case.xml").unlink()
        elif failure == "bad-xml":
            (directory / "case.xml").write_text("<invalid/>")
        elif failure == "bad-des":
            (directory / "case.des").write_text("not a ZIP")
        elif failure == "bad-log":
            (directory / "LogFiles/native.xml").write_text("<broken>")
        elif failure == "native-error":
            (directory / "LogFiles/native.xml").write_text(
                '<log><message text="ERROR failed"/></log>'
            )
        else:
            result["exit_code"] = "timeout"
        return result

    monkeypatch.setattr(runner, "_launch", launch)
    directory = tmp_path / "run"
    result = runner.replay(installation, [{"id": "case", "commands": []}], directory)
    assert result["status"] == ("timed_out" if failure == "timeout" else "failed")
    assert failure == "timeout" or result["errors"]
    assert (directory / "run.json").is_file()
    if failure == "bad-des":
        with pytest.raises(BadZipFile):
            read_des(directory / "case.des")


def test_invalid_script_and_existing_export_are_rejected_before_launch(
    tmp_path, installation, monkeypatch
):
    monkeypatch.setattr(runner, "_launch", lambda *_: pytest.fail("must not launch"))
    source = tmp_path / "invalid.xml"
    source.write_text("<wrong/>")
    with pytest.raises(etree.DocumentInvalid):
        validate(source, installation)
    directory = tmp_path / "run"
    directory.mkdir()
    (directory / "case.xml").write_text("old export")
    with pytest.raises(FileExistsError, match="existing output"):
        runner.prepare_replay(installation, [{"id": "case", "commands": []}], directory)
    assert (directory / "case.xml").read_text() == "old export"
