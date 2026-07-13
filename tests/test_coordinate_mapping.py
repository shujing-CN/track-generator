import pytest
from processing.coordinate_mapping import map_points_to_world

def test_corners_center_flip_and_aspect():
    result=map_points_to_world([(0,0),(100,50),(50,25)],100,50,200,200,0)
    assert result == [(-100,50),(100,-50),(0,0)]

def test_rectangular_map_centers_without_stretch():
    result=map_points_to_world([(0,0),(200,100)],200,100,100,300,0)
    assert result == [(-50,25),(50,-25)]

@pytest.mark.parametrize("args", [(0,1,1,1),(1,0,1,1),(1,1,0,1),(1,1,1,-1)])
def test_invalid_dimensions(args):
    with pytest.raises(ValueError): map_points_to_world([], *args)
