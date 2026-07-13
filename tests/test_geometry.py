import pytest
from geometry.track_builder import build_track_mesh_data, sharp_turn_indices, TrackGeometryError
from geometry.terrain_builder import build_terrain_mesh_data

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
    assert sharp_turn_indices([(0,0),(5,0),(5.1,.01)],8)==[1]
