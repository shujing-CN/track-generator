import glob
import json
import os
import shutil
import subprocess


DEFAULT_UNREAL_ARGS = ("-DDC-ForceMemoryCache",)
PROJECT_NAME = "GeneratedTrackFPS"
PROJECT_MARKER = ".track_generator_project"


def find_unreal_editors(search_root=None, manifest_root=None):
    candidates = []
    roots = [search_root] if search_root else [os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Epic Games")]
    for root in roots:
        candidates.extend(glob.glob(os.path.join(root, "UE_*", "Engine", "Binaries", "Win64", "UnrealEditor.exe")))
    if search_root is None:
        manifest_root = manifest_root or os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), "Epic", "EpicGamesLauncher", "Data", "Manifests")
    if manifest_root and os.path.isdir(manifest_root):
        for path in glob.glob(os.path.join(manifest_root, "*.item")):
            try:
                with open(path, "r", encoding="utf-8") as stream:
                    data = json.load(stream)
                editor = os.path.join(data.get("InstallLocation", ""), "Engine", "Binaries", "Win64", "UnrealEditor.exe")
                if os.path.isfile(editor):
                    candidates.append(editor)
            except (OSError, TypeError, ValueError):
                pass
    return sorted(set(candidates), reverse=True)


def find_unreal_projects(search_roots=None):
    roots = search_roots or [os.getcwd(), os.path.join(os.path.expanduser("~"), "Documents", "Unreal Projects")]
    found = []
    for root in roots:
        if os.path.isdir(root):
            found.extend(glob.glob(os.path.join(root, "*", "*.uproject")))
    return sorted(set(found))


def _engine_root_from_editor(editor_path):
    current = os.path.abspath(editor_path)
    for _ in range(4):
        current = os.path.dirname(current)
    return current


def first_person_template_path(editor_path):
    template = os.path.join(_engine_root_from_editor(editor_path), "Templates", "TP_FirstPersonBP")
    if not os.path.isdir(template):
        raise ValueError("UE FirstPersonBP template was not found: {}".format(template))
    return template


def _copy_template(template_dir, project_dir):
    def ignore(_directory, names):
        return {name for name in names if name in {"Binaries", "Intermediate", "Saved", "DerivedDataCache", ".vs"}}
    if os.path.isdir(project_dir):
        marker = os.path.join(project_dir, PROJECT_MARKER)
        if not os.path.isfile(marker):
            raise ValueError(
                "project directory already exists and was not created by this tool: {}".format(project_dir)
            )
        shutil.rmtree(project_dir)
    shutil.copytree(template_dir, project_dir, ignore=ignore)
    with open(os.path.join(project_dir, PROJECT_MARKER), "w", encoding="utf-8") as stream:
        stream.write(PROJECT_NAME + "\n")


def _rename_project_file(project_dir):
    old = os.path.join(project_dir, "TP_FirstPersonBP.uproject")
    new = os.path.join(project_dir, PROJECT_NAME + ".uproject")
    if os.path.isfile(old):
        os.replace(old, new)
    with open(new, "r", encoding="utf-8") as stream:
        data = json.load(stream)
    plugins = data.setdefault("Plugins", [])
    if not any(plugin.get("Name") == "PythonScriptPlugin" for plugin in plugins):
        plugins.append({"Name": "PythonScriptPlugin", "Enabled": True})
    with open(new, "w", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2)
    return new


def _copy_model_files(model_path, project_dir):
    if not os.path.isfile(model_path):
        raise ValueError("track model does not exist: {}".format(model_path))
    source_dir = os.path.join(project_dir, "TrackSource")
    os.makedirs(source_dir, exist_ok=True)
    copied = os.path.join(source_dir, "generated_track.obj")
    shutil.copy2(model_path, copied)
    base, _ = os.path.splitext(model_path)
    mtl = base + ".mtl"
    if os.path.isfile(mtl):
        shutil.copy2(mtl, os.path.join(source_dir, "generated_track.mtl"))
    return copied


def write_import_script(project_dir):
    script_dir = os.path.join(project_dir, "Scripts")
    os.makedirs(script_dir, exist_ok=True)
    script_path = os.path.join(script_dir, "setup_track_project.py")
    content = r'''import os
import unreal

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(project_dir, "TrackSource", "generated_track.obj")
asset_path = "/Game/Track/generated_track"
map_path = "/Game/Track/TrackMap"

def log(message):
    unreal.log("[TrackGenerator] " + message)

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
if os.path.isfile(model_path) and not unreal.EditorAssetLibrary.does_asset_exist(asset_path):
    task = unreal.AssetImportTask()
    task.filename = model_path
    task.destination_path = "/Game/Track"
    task.automated = True
    task.save = True
    task.replace_existing = True
    asset_tools.import_asset_tasks([task])
    log("Imported track model: " + model_path)

track_asset = unreal.EditorAssetLibrary.load_asset(asset_path)
world = unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
if track_asset:
    actor = unreal.EditorLevelLibrary.spawn_actor_from_object(track_asset, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    actor.set_actor_label("Generated Track Map")
    actor.set_actor_scale3d(unreal.Vector(100, 100, 100))
    start = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, -800, 180), unreal.Rotator(0, 0, 0))
    start.set_actor_label("FirstPerson Start")

unreal.EditorLoadingAndSavingUtils.save_map(world, map_path)
settings = unreal.GameMapsSettings.get_game_maps_settings()
settings.set_editor_property("editor_startup_map", unreal.SoftObjectPath(map_path))
settings.set_editor_property("game_default_map", unreal.SoftObjectPath(map_path))
settings.save_config()
log("Created first-person track map at " + map_path)
'''
    with open(script_path, "w", encoding="utf-8") as stream:
        stream.write(content)
    return script_path


def create_first_person_track_project(editor_path, model_path, project_dir):
    editor_path = os.path.abspath(os.path.expanduser(editor_path or ""))
    project_dir = os.path.abspath(os.path.expanduser(project_dir or ""))
    if not os.path.isfile(editor_path):
        raise ValueError("UnrealEditor does not exist: {}".format(editor_path))
    if not project_dir:
        raise ValueError("project directory is empty")
    _copy_template(first_person_template_path(editor_path), project_dir)
    uproject = _rename_project_file(project_dir)
    copied_model = _copy_model_files(model_path, project_dir)
    script = write_import_script(project_dir)
    return {"project_dir": project_dir, "uproject": uproject, "model": copied_model, "script": script}


def launch_unreal(editor_path, project_path, extra_args=None):
    editor_path = os.path.abspath(os.path.expanduser(editor_path or ""))
    project_path = os.path.abspath(os.path.expanduser(project_path or ""))
    if not os.path.isfile(editor_path):
        raise ValueError("UnrealEditor path is invalid")
    if not os.path.isfile(project_path) or not project_path.lower().endswith(".uproject"):
        raise ValueError("Unreal .uproject path is invalid")
    args = [editor_path, project_path] + list(DEFAULT_UNREAL_ARGS) + list(extra_args or [])
    try:
        return subprocess.Popen(args, cwd=os.path.dirname(project_path))
    except OSError as exc:
        raise RuntimeError("failed to launch Unreal Engine: {}".format(exc))


def launch_first_person_track_project(editor_path, model_path, project_dir):
    project = create_first_person_track_project(editor_path, model_path, project_dir)
    process = launch_unreal(editor_path, project["uproject"], ["-ExecutePythonScript=" + project["script"]])
    return project, process
