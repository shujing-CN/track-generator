from geometry.track_builder import build_track_mesh_data, sharp_turn_indices
from geometry.terrain_builder import build_terrain_mesh_data
from .layer_manager import ensure_layers
from .rhino_curve_builder import make_curve

class GeneratedDocument:
    def __init__(self): self.object_ids=[]

    def _mesh(self,vertices,faces):
        import Rhino, System
        mesh=Rhino.Geometry.Mesh()
        for v in vertices: mesh.Vertices.Add(*v)
        for f in faces:
            if len(f)==4: mesh.Faces.AddFace(*f)
            else: mesh.Faces.AddFace(*f)
        mesh.Normals.ComputeNormals(); mesh.Compact()
        if not mesh.IsValid: raise ValueError("generated Rhino mesh is invalid")
        return mesh

    def generate(self,doc,points,source_points,map_width,map_length,track_width,closed,terrain=True,height=.1,thickness=0):
        import Rhino, System
        if doc is None: raise ValueError("Rhino current document is unavailable")
        if track_width>=min(map_width,map_length): raise ValueError("track width is too large for map dimensions")
        if sharp_turn_indices(points,track_width,closed): raise ValueError("path contains turns too sharp for current track width; increase smoothing or reduce width")
        layers=ensure_layers(doc); staged=[]
        def attrs(index): a=Rhino.DocObjects.ObjectAttributes(); a.LayerIndex=index; return a
        try:
            source=Rhino.Geometry.PolylineCurve([Rhino.Geometry.Point3d(x,y,0) for x,y in source_points]); staged.append(doc.Objects.AddCurve(source,attrs(layers["SourcePath"])))
            staged.append(doc.Objects.AddCurve(make_curve(points,closed),attrs(layers["Centerline"])))
            v,f=build_track_mesh_data(points,track_width,height,thickness,closed); staged.append(doc.Objects.AddMesh(self._mesh(v,f),attrs(layers["Road"])))
            if terrain:
                v,f=build_terrain_mesh_data(map_width,map_length,0); staged.append(doc.Objects.AddMesh(self._mesh(v,f),attrs(layers["Terrain"])))
            if any(value==System.Guid.Empty for value in staged): raise ValueError("Rhino document rejected a generated object")
        except Exception:
            for oid in staged: doc.Objects.Delete(oid,True)
            raise
        for oid in self.object_ids: doc.Objects.Delete(oid,True)
        self.object_ids=staged; doc.Views.Redraw(); return list(staged)

    def clear(self,doc):
        for oid in self.object_ids: doc.Objects.Delete(oid,True)
        self.object_ids=[]; doc.Views.Redraw()
