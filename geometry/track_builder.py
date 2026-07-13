import math

class TrackGeometryError(ValueError): pass

def build_track_mesh_data(points,width,height=.1,thickness=0.0,closed=False):
    if width<=0: raise TrackGeometryError("track width must be positive")
    if len(points)<(3 if closed else 2): raise TrackGeometryError("path is too short")
    half=width/2; pairs=[]
    for i,p in enumerate(points):
        if closed: prev,nxt=points[(i-1)%len(points)],points[(i+1)%len(points)]
        elif i==0: prev,nxt=p,points[1]
        elif i==len(points)-1: prev,nxt=points[-2],p
        else: prev,nxt=points[i-1],points[i+1]
        dx,dy=nxt[0]-prev[0],nxt[1]-prev[1]; length=math.hypot(dx,dy)
        if length<1e-9: raise TrackGeometryError("path contains zero-length tangent")
        nx,ny=-dy/length,dx/length
        pairs.append(((p[0]+nx*half,p[1]+ny*half,height),(p[0]-nx*half,p[1]-ny*half,height)))
    vertices=[v for pair in pairs for v in pair]; faces=[]; count=len(points) if closed else len(points)-1
    for i in range(count):
        j=(i+1)%len(points); faces.append((2*i,2*j,2*j+1,2*i+1))
    if thickness>0:
        top_count=len(vertices); vertices += [(x,y,z-thickness) for x,y,z in vertices]
        faces += [tuple(top_count+i for i in reversed(face)) for face in faces[:count]]
        for i in range(count):
            j=(i+1)%len(points); faces.extend([(2*i,2*i+top_count,2*j+top_count,2*j),(2*i+1,2*j+1,2*j+1+top_count,2*i+1+top_count)])
        if not closed: faces.extend([(0,1,1+top_count,top_count),(2*len(points)-2,2*len(points)-2+top_count,2*len(points)-1+top_count,2*len(points)-1)])
    return vertices,faces

def sharp_turn_indices(points,width,closed=False):
    bad=[]
    for i in range(len(points)):
        if not closed and i in (0,len(points)-1): continue
        a,b,c=points[(i-1)%len(points)],points[i],points[(i+1)%len(points)]
        u=(a[0]-b[0],a[1]-b[1]); v=(c[0]-b[0],c[1]-b[1]); lu=math.hypot(*u); lv=math.hypot(*v)
        if min(lu,lv)<width*.45: bad.append(i); continue
        cosine=max(-1,min(1,(u[0]*v[0]+u[1]*v[1])/(lu*lv)))
        if math.degrees(math.acos(cosine))<20: bad.append(i)
    return bad
