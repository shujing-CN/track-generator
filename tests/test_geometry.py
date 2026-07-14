import math
import pytest
from geometry.track_builder import build_track_mesh_data, build_track_with_recovery, build_turn_curb_meshes, build_turn_curbs_from_track_mesh, sharp_turn_indices, TrackGeometryError
from geometry.terrain_builder import build_terrain_mesh_data
from processing.path_processing import process_path

def test_open_track_surface():
    vertices,faces=build_track_mesh_data([(0,0),(10,0),(20,0)],8)
    assert len(vertices)==6 and len(faces)==2
    assert vertices[0]==(0,4,.1) and vertices[1]==(0,-4,.1)

def test_closed_track_connects_last_face():
    vertices,faces=build_track_mesh_data([(0,0),(10,0),(10,10),(0,10)],4,closed=True)
    assert len(vertices)==8 and len(faces)==4 and 0 in faces[-1]

def test_thick_track_has_solid_faces():
    vertices,faces=build_track_mesh_data([(0,0),(10,0)],4,thickness=1)
    assert len(vertices)==8 and len(faces)==6

def test_invalid_track_and_terrain():
    with pytest.raises(TrackGeometryError): build_track_mesh_data([(0,0)],4)
    with pytest.raises(ValueError): build_terrain_mesh_data(0,10)

def test_sharp_turn_detection():
    assert isinstance(sharp_turn_indices([(0,0),(5,0),(5.1,.01)],8),list)

def _processed_mesh(points, width=4, closed=False, spacing=1):
    path=process_path(points,min_distance=.01,smoothing=.5,spacing=spacing,closed=closed)
    return build_track_with_recovery(path,width,closed=closed)

def test_straight_path_succeeds():
    path,vertices,faces=_processed_mesh([(0,0),(10,0),(20,0)])
    assert len(faces)==len(path)-1

def test_circle_path_succeeds():
    points=[(20*math.cos(i*math.pi/8),20*math.sin(i*math.pi/8)) for i in range(16)]
    path,vertices,faces=_processed_mesh(points,4,True,1.5)
    assert len(faces)==len(path)

def test_s_curve_succeeds():
    points=[(x,8*math.sin(x/8.0)) for x in range(0,41,4)]
    path,vertices,faces=_processed_mesh(points,5)
    assert faces

def test_jittered_hand_drawn_path_succeeds():
    points=[(x,0.35*(-1 if x%2 else 1)+2*math.sin(x/7.0)) for x in range(31)]
    path,vertices,faces=_processed_mesh(points,4)
    assert faces

def test_ninety_degree_polyline_succeeds():
    path,vertices,faces=_processed_mesh([(0,0),(10,0),(10,10),(20,10)],6)
    assert faces

def test_extreme_fold_is_rejected_in_chinese():
    with pytest.raises(TrackGeometryError,match="extreme fold"):
        build_track_mesh_data([(0,0),(10,0),(.1,.01)],4)

def test_turn_curbs_are_alternating_red_and_white_meshes():
    points=[(x,6*math.sin(x/6.0)) for x in range(0,31)]
    (red_v,red_f),(white_v,white_f)=build_turn_curb_meshes(points,6)
    assert red_f and white_f
    assert len(red_v)//8==len(red_f)//6 and len(white_v)//8==len(white_f)//6
    assert min(v[2] for v in red_v)<max(v[2] for v in red_v)
    red_xy={(round(x,6),round(y,6)) for x,y,z in red_v}
    white_xy={(round(x,6),round(y,6)) for x,y,z in white_v}
    assert red_xy & white_xy  # adjacent red/white solid blocks share seam coordinates

def test_curbs_use_final_road_edge_as_inner_boundary():
    points=[(x,6*math.sin(x/6.0)) for x in range(0,31)]
    final,road_vertices,road_faces=build_track_with_recovery(points,6,thickness=.3)
    (red_v,red_f),(white_v,white_f)=build_turn_curbs_from_track_mesh(final,road_vertices,.8,.14,False,.2)
    assert red_f and white_f
    road_edge_xy={(round(road_vertices[i][0],6),round(road_vertices[i][1],6)) for i in range(0,2*len(final))}
    curb_inner_xy={(round(vertices[k][0],6),round(vertices[k][1],6)) for vertices in (red_v,white_v) for k in range(0,len(vertices),8)}
    assert curb_inner_xy <= road_edge_xy
    assert min(v[2] for v in red_v) < .1 < max(v[2] for v in red_v)
