LAYER_COLORS={"SourcePath":(120,120,120),"Centerline":(255,220,0),"Road":(0,0,0),"CurbsRed":(220,0,0),"CurbsWhite":(255,255,255),"Terrain":(90,150,90)}

def ensure_layers(doc):
    import Rhino, System.Drawing
    root=doc.Layers.FindName("GeneratedTrack")
    if root is None:
        layer=Rhino.DocObjects.Layer(); layer.Name="GeneratedTrack"; root_index=doc.Layers.Add(layer); root=doc.Layers[root_index]
    result={}
    for name,color in LAYER_COLORS.items():
        full="GeneratedTrack::"+name; layer=doc.Layers.FindName(full)
        if layer is None:
            item=Rhino.DocObjects.Layer(); item.Name=name; item.ParentLayerId=root.Id; item.Color=System.Drawing.Color.FromArgb(*color)
            index=doc.Layers.Add(item); layer=doc.Layers[index]
        result[name]=layer.Index
    return result

def ensure_materials(doc):
    import Rhino, System.Drawing
    result={}
    for name,color in LAYER_COLORS.items():
        material_name="GeneratedTrack_"+name
        index=doc.Materials.Find(material_name,True)
        if index<0:
            material=Rhino.DocObjects.Material(); material.Name=material_name
            material.DiffuseColor=System.Drawing.Color.FromArgb(*color)
            index=doc.Materials.Add(material)
        result[name]=index
    return result
