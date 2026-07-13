import os

def export_generated(doc,object_ids,path):
    if not object_ids: raise ValueError("no generated objects to export")
    extension=os.path.splitext(path)[1].lower()
    if extension not in (".obj",".fbx"): raise ValueError("export format must be OBJ or FBX")
    directory=os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(directory): raise ValueError("export directory does not exist")
    for obj in doc.Objects: obj.Select(False)
    for oid in object_ids:
        if not doc.Objects.Select(oid): raise ValueError("generated object is unavailable for export")
    escaped=path.replace('"','""')
    command='_-Export "{}" _Enter _Enter'.format(escaped)
    import Rhino
    ok=Rhino.RhinoApp.RunScript(command,False)
    for oid in object_ids: doc.Objects.UnselectAll()
    if not ok or not os.path.isfile(path): raise RuntimeError("Rhino export failed: output file was not created")
    return path
