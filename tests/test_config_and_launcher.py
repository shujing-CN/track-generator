import json, os
import pytest
from config import load_config, save_config, DEFAULTS
from export.unreal_launcher import DEFAULT_UNREAL_ARGS, PROJECT_MARKER, PROJECT_NAME, create_first_person_track_project, find_unreal_editors, find_unreal_projects, launch_first_person_track_project, launch_unreal

def test_config_round_trip_and_fallback(tmp_path):
    path=tmp_path/"config.json"; save_config({"default_track_width":12},str(path)); assert load_config(str(path))["default_track_width"]==12
    path.write_text("bad json",encoding="utf8"); assert load_config(str(path))["default_map_width"]==DEFAULTS["default_map_width"]

def test_launcher_validates_paths(tmp_path):
    with pytest.raises(ValueError,match="UnrealEditor"): launch_unreal(str(tmp_path/"missing.exe"),str(tmp_path/"x.uproject"))
    editor=tmp_path/"editor.exe"; editor.write_text("")
    with pytest.raises(ValueError,match="uproject"): launch_unreal(str(editor),str(tmp_path/"missing.uproject"))

def test_find_unreal_editors(tmp_path):
    editor=tmp_path/"UE_5.6"/"Engine"/"Binaries"/"Win64"/"UnrealEditor.exe"
    editor.parent.mkdir(parents=True); editor.write_text("")
    assert find_unreal_editors(str(tmp_path))==[str(editor)]

def test_find_editor_from_epic_manifest(tmp_path):
    install=tmp_path/"UE_Test"; editor=install/"Engine"/"Binaries"/"Win64"/"UnrealEditor.exe"
    editor.parent.mkdir(parents=True); editor.write_text("")
    manifests=tmp_path/"manifests"; manifests.mkdir(); (manifests/"ue.item").write_text(json.dumps({"InstallLocation":str(install)}))
    assert find_unreal_editors(str(tmp_path/"empty"),str(manifests))==[str(editor)]

def test_find_unreal_projects(tmp_path):
    project=tmp_path/"Game"/"Game.uproject"; project.parent.mkdir(); project.write_text("{}")
    assert find_unreal_projects([str(tmp_path)])==[str(project)]

def test_launcher_includes_memory_ddc_arg(tmp_path, monkeypatch):
    editor=tmp_path/"UnrealEditor.exe"; editor.write_text("")
    project=tmp_path/"Game.uproject"; project.write_text("{}")
    captured={}
    class DummyProcess: pass
    def fake_popen(args,cwd=None):
        captured["args"]=args; captured["cwd"]=cwd; return DummyProcess()
    monkeypatch.setattr("subprocess.Popen",fake_popen)
    process=launch_unreal(str(editor),str(project))
    assert isinstance(process,DummyProcess)
    assert DEFAULT_UNREAL_ARGS[0] in captured["args"]
    assert captured["cwd"]==str(tmp_path)

def _make_fake_engine(tmp_path):
    editor=tmp_path/"EngineRoot"/"Engine"/"Binaries"/"Win64"/"UnrealEditor.exe"
    editor.parent.mkdir(parents=True); editor.write_text("")
    template=tmp_path/"EngineRoot"/"Templates"/"TP_FirstPersonBP"
    (template/"Config").mkdir(parents=True); (template/"Content").mkdir()
    (template/"TP_FirstPersonBP.uproject").write_text(json.dumps({"FileVersion":3,"Plugins":[]}))
    return editor

def test_create_first_person_track_project_copies_template_and_model(tmp_path):
    editor=_make_fake_engine(tmp_path)
    model=tmp_path/"source_name.obj"; model.write_text("o track")
    mtl=tmp_path/"source_name.mtl"; mtl.write_text("newmtl road")
    project=create_first_person_track_project(str(editor),str(model),str(tmp_path/"OutProject"))
    assert os.path.isfile(project["uproject"])
    assert os.path.basename(project["uproject"])==PROJECT_NAME+".uproject"
    assert os.path.isfile(project["model"])
    assert os.path.basename(project["model"])=="generated_track.obj"
    assert os.path.isfile(os.path.join(project["project_dir"],PROJECT_MARKER))
    assert os.path.isfile(os.path.join(project["project_dir"],"TrackSource","generated_track.mtl"))
    assert os.path.isfile(project["script"])
    with open(project["uproject"],encoding="utf-8") as stream:
        assert any(plugin["Name"]=="PythonScriptPlugin" for plugin in json.load(stream)["Plugins"])

def test_create_first_person_track_project_refuses_existing_user_directory(tmp_path):
    editor=_make_fake_engine(tmp_path)
    model=tmp_path/"generated_track.obj"; model.write_text("o track")
    project_dir=tmp_path/"ExistingProject"; project_dir.mkdir()
    (project_dir/"keep.txt").write_text("user data")
    with pytest.raises(ValueError,match="not created by this tool"):
        create_first_person_track_project(str(editor),str(model),str(project_dir))
    assert (project_dir/"keep.txt").read_text()=="user data"

def test_launch_first_person_track_project_uses_import_script(tmp_path, monkeypatch):
    editor=_make_fake_engine(tmp_path)
    model=tmp_path/"generated_track.obj"; model.write_text("o track")
    captured={}
    class DummyProcess: pass
    def fake_popen(args,cwd=None):
        captured["args"]=args; captured["cwd"]=cwd; return DummyProcess()
    monkeypatch.setattr("subprocess.Popen",fake_popen)
    project,process=launch_first_person_track_project(str(editor),str(model),str(tmp_path/"OutProject"))
    assert isinstance(process,DummyProcess)
    assert project["uproject"] in captured["args"]
    assert any(arg.startswith("-ExecutePythonScript=") for arg in captured["args"])
    assert DEFAULT_UNREAL_ARGS[0] in captured["args"]
