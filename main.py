"""Run this file with Rhino 8 ScriptEditor using Python 3."""
# requirements: Pillow
import os, sys
ROOT=os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path: sys.path.insert(0,ROOT)

def show():
    try:
        import Rhino
        from ui.main_window import TrackGeneratorWindow
    except ImportError as exc:
        raise RuntimeError("请在 Rhino 8 Python 3 ScriptEditor 中运行，并安装 Pillow。详细信息：{}".format(exc))
    form=TrackGeneratorWindow(Rhino.RhinoDoc.ActiveDoc); form.Owner=Rhino.UI.RhinoEtoApp.MainWindow; form.Show(); return form

if __name__ == "__main__": WINDOW=show()
