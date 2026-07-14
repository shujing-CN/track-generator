def make_curve(points,closed=False):
    import Rhino
    values=[Rhino.Geometry.Point3d(x,y,0) for x,y in points]
    if closed and values[0].DistanceTo(values[-1])>1e-9: values.append(values[0])
    degree=min(3,len(values)-1)
    curve=Rhino.Geometry.Curve.CreateInterpolatedCurve(values,degree,Rhino.Geometry.CurveKnotStyle.Chord)
    if curve is None or not curve.IsValid: raise ValueError("Rhino centerline curve creation failed")
    return curve

def sample_curve(curve,spacing,closed=False):
    if spacing<=0: raise ValueError("曲线采样间距必须大于 0")
    parameters=curve.DivideByLength(float(spacing),True)
    if not parameters or len(parameters)<2: raise ValueError("平滑曲线过短，无法等距采样")
    points=[curve.PointAt(t) for t in parameters]
    result=[(point.X,point.Y) for point in points]
    if closed and len(result)>1:
        import math
        if math.dist(result[0],result[-1])<1e-7: result.pop()
    return result
