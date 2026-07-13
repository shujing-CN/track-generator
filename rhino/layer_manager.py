LAYER_COLORS={"SourcePath":(255,140,0),"Centerline":(255,220,0),"Road":(65,65,65),"Terrain":(90,150,90)}

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
