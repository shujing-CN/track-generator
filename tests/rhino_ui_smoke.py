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
    from rhino.rhino_curve_builder import make_curve, sample_curve
    from rhino.document_manager import GeneratedDocument
    from geometry.track_builder import build_track_mesh_data, build_turn_curbs_from_track_mesh

    window = TrackGeneratorWindow(Rhino.RhinoDoc.ActiveDoc)
    assert window.Content is not None
    window._switch_mode(1)
    assert window.input_panel.Content is window.preview
    window._switch_mode(0)
    assert window.input_panel.Content is window.canvas
    window.Owner = Rhino.UI.RhinoEtoApp.MainWindow
    window.Show()
    window.Close()
    control=[(0,0),(10,1),(20,8),(30,10),(40,4)]
    curve=make_curve(control,False)
    sampled=sample_curve(curve,1.0,False)
    vertices,faces=build_track_mesh_data(sampled,6,thickness=.3)
    mesh=GeneratedDocument()._mesh(vertices,faces)
    assert mesh.IsValid and mesh.IsClosed and len(sampled)>len(control)
    (red,red_faces),(white,white_faces)=build_turn_curbs_from_track_mesh(sampled,vertices,.8,.14,False,.2)
    assert red_faces and white_faces
    red_mesh=GeneratedDocument()._mesh(red,red_faces); white_mesh=GeneratedDocument()._mesh(white,white_faces)
    assert red_mesh.IsValid and red_mesh.IsClosed and white_mesh.IsValid and white_mesh.IsClosed
    temp_doc=Rhino.RhinoDoc.CreateHeadless(None)
    generated=GeneratedDocument()
    ids=generated.generate(temp_doc,sampled,control,100,100,6,False,False,.1,.3,1.0,False,False)
    colors=set()
    for object_id in ids:
        obj=temp_doc.Objects.FindId(object_id)
        colors.add((obj.Attributes.ObjectColor.R,obj.Attributes.ObjectColor.G,obj.Attributes.ObjectColor.B))
        assert obj.Attributes.MaterialIndex>=0
    assert (0,0,0) in colors and (220,0,0) in colors and (255,255,255) in colors
    temp_doc.Dispose()
    message = "PASS: Rhino 8 Eto UI, interpolated curve sampling, road mesh, and alternating curb meshes succeeded."
except Exception:
    message = "FAIL:\n" + traceback.format_exc()
    with open(RESULT, "w", encoding="utf-8") as stream:
        stream.write(message)
    raise
else:
    with open(RESULT, "w", encoding="utf-8") as stream:
        stream.write(message)
