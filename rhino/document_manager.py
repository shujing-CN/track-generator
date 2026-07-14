from geometry.track_builder import build_track_with_recovery, build_turn_curbs_from_track_mesh, sharp_turn_indices
from geometry.terrain_builder import build_terrain_mesh_data
from .layer_manager import ensure_layers, ensure_materials
from .rhino_curve_builder import make_curve, sample_curve

DEFAULT_ROAD_HEIGHT = 0.45
DEFAULT_TERRAIN_HEIGHT = -0.25
DEFAULT_CURB_RAISE = 0.08

class GeneratedDocument:
    def __init__(self): self.object_ids=[]; self.quality_warnings=[]

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

    def generate(self,doc,points,source_points,map_width,map_length,track_width,closed,terrain=True,height=DEFAULT_ROAD_HEIGHT,thickness=0,sample_spacing=2.0,show_source=True,show_centerline=True):
        import Rhino, System
        if doc is None: raise ValueError("Rhino current document is unavailable")
        if track_width>=min(map_width,map_length): raise ValueError("track width is too large for map dimensions")
        layers=ensure_layers(doc); materials=ensure_materials(doc); staged=[]
        def attrs(name):
            import System.Drawing
            a=Rhino.DocObjects.ObjectAttributes(); a.LayerIndex=layers[name]
            color=System.Drawing.Color.FromArgb(*{"SourcePath":(120,120,120),"Centerline":(255,220,0),"Road":(0,0,0),"CurbsRed":(220,0,0),"CurbsWhite":(255,255,255),"Terrain":(90,150,90)}[name])
            a.ObjectColor=color; a.ColorSource=Rhino.DocObjects.ObjectColorSource.ColorFromObject
            a.MaterialIndex=materials[name]; a.MaterialSource=Rhino.DocObjects.ObjectMaterialSource.MaterialFromObject
            return a
        try:
            centerline=make_curve(points,closed)
            curve_points=sample_curve(centerline,sample_spacing,closed)
            solid_thickness=max(float(thickness),.1)
            points,v,f=build_track_with_recovery(curve_points,track_width,height,solid_thickness,closed)
            if show_source:
                source=Rhino.Geometry.PolylineCurve([Rhino.Geometry.Point3d(x,y,0) for x,y in source_points]); staged.append(doc.Objects.AddCurve(source,attrs("SourcePath")))
            if show_centerline: staged.append(doc.Objects.AddCurve(centerline,attrs("Centerline")))
            staged.append(doc.Objects.AddMesh(self._mesh(v,f),attrs("Road")))
            (rv,rf),(wv,wf)=build_turn_curbs_from_track_mesh(points,v,max(track_width*.12,.25),height+DEFAULT_CURB_RAISE,closed,max(solid_thickness*.8,.12))
            if rf: staged.append(doc.Objects.AddMesh(self._mesh(rv,rf),attrs("CurbsRed")))
            if wf: staged.append(doc.Objects.AddMesh(self._mesh(wv,wf),attrs("CurbsWhite")))
            if terrain:
                v,f=build_terrain_mesh_data(map_width,map_length,DEFAULT_TERRAIN_HEIGHT); staged.append(doc.Objects.AddMesh(self._mesh(v,f),attrs("Terrain")))
            if any(value==System.Guid.Empty for value in staged): raise ValueError("Rhino document rejected a generated object")
        except Exception:
            for oid in staged: doc.Objects.Delete(oid,True)
            raise
        for oid in self.object_ids: doc.Objects.Delete(oid,True)
        sharp=sharp_turn_indices(points,track_width,closed)
        self.quality_warnings=[] if not sharp else ["生成后质量检查：第 {} 个采样点附近弯道较急，已采用平滑和局部缩宽结果".format(sharp[0]+1)]
        self.object_ids=staged; doc.Views.Redraw(); return list(staged)

    def clear(self,doc):
        for oid in self.object_ids: doc.Objects.Delete(oid,True)
        self.object_ids=[]; doc.Views.Redraw()
