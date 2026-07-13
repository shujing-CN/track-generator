import os, subprocess

def launch_unreal(editor_path,project_path):
    if not os.path.isfile(editor_path): raise ValueError("UnrealEditor executable does not exist")
    if not os.path.isfile(project_path) or not project_path.lower().endswith(".uproject"): raise ValueError("Unreal .uproject file does not exist")
    try: return subprocess.Popen([editor_path,project_path])
    except OSError as exc: raise RuntimeError("failed to launch Unreal Engine: {}".format(exc))
