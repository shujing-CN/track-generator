import json, os
import pytest
from config import load_config, save_config, DEFAULTS
from export.unreal_launcher import launch_unreal

def test_config_round_trip_and_fallback(tmp_path):
    path=tmp_path/"config.json"; save_config({"default_track_width":12},str(path)); assert load_config(str(path))["default_track_width"]==12
    path.write_text("bad json",encoding="utf8"); assert load_config(str(path))["default_map_width"]==DEFAULTS["default_map_width"]

def test_launcher_validates_paths(tmp_path):
    with pytest.raises(ValueError,match="executable"): launch_unreal(str(tmp_path/"missing.exe"),str(tmp_path/"x.uproject"))
    editor=tmp_path/"editor.exe"; editor.write_text("")
    with pytest.raises(ValueError,match="uproject"): launch_unreal(str(editor),str(tmp_path/"missing.uproject"))
