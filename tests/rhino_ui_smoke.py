"""Execute with RhinoCode.exe while Rhino 8 is running."""
import os
import sys
import traceback
import importlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULT = os.path.join(ROOT, "rhino_ui_smoke_result.txt")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

prefixes = ("ui", "processing", "geometry", "rhino", "export", "config")
dotted = tuple(prefix + "." for prefix in prefixes)
for module_name in list(sys.modules):
    if module_name in prefixes or module_name.startswith(dotted):
        del sys.modules[module_name]
importlib.invalidate_caches()

try:
    import Rhino
    from ui.main_window import TrackGeneratorWindow

    window = TrackGeneratorWindow(Rhino.RhinoDoc.ActiveDoc)
    assert window.Content is not None
    window._switch_mode(1)
    assert window.input_panel.Content is window.preview
    window._switch_mode(0)
    assert window.input_panel.Content is window.canvas
    window.Owner = Rhino.UI.RhinoEtoApp.MainWindow
    window.Show()
    window.Close()
    message = "PASS: Rhino 8 Eto window constructed, switched modes, shown, and closed successfully."
except Exception:
    message = "FAIL:\n" + traceback.format_exc()
    with open(RESULT, "w", encoding="utf-8") as stream:
        stream.write(message)
    raise
else:
    with open(RESULT, "w", encoding="utf-8") as stream:
        stream.write(message)
