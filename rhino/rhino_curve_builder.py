def make_curve(points,closed=False):
    import Rhino
    values=[Rhino.Geometry.Point3d(x,y,0) for x,y in points]
    if closed and values[0].DistanceTo(values[-1])>1e-9: values.append(values[0])
    degree=min(3,len(values)-1)
    curve=Rhino.Geometry.Curve.CreateInterpolatedCurve(values,degree,Rhino.Geometry.CurveKnotStyle.Chord)
    if curve is None or not curve.IsValid: raise ValueError("Rhino centerline curve creation failed")
    return curve
