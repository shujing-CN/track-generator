import json, os

DEFAULTS = {"default_map_width":500.0,"default_map_length":500.0,"default_track_width":8.0,"default_smoothing":0.55,"default_sample_spacing":2.0,"export_directory":"","unreal_editor_path":"","unreal_project_path":"","unreal_project_directory":"unreal_projects/GeneratedTrackFPS"}

def config_path(): return os.path.join(os.path.dirname(os.path.abspath(__file__)),"config.json")

def load_config(path=None):
    path=path or config_path(); data=dict(DEFAULTS)
    if os.path.exists(path):
        try:
            with open(path,"r",encoding="utf-8") as f: loaded=json.load(f)
            if isinstance(loaded,dict): data.update(loaded)
        except (OSError,ValueError): pass
    return data

def save_config(data,path=None):
    path=path or config_path()
    with open(path,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
