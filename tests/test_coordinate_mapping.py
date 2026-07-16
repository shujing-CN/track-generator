import pytest
from processing.coordinate_mapping import map_points_to_world

def test_corners_center_flip_and_aspect():
    result=map_points_to_world([(0,0),(100,50),(50,25)],100,50,200,200,0)
    assert result == [(-100,50),(100,-50),(0,0)]

def test_rectangular_map_centers_without_stretch():
    result=map_points_to_world([(0,0),(200,100)],200,100,100,300,0)
    assert result == [(-50,25),(50,-25)]

def test_image_path_can_fit_its_own_bounds_instead_of_canvas_whitespace():
    result=map_points_to_world([(400,400),(800,500)],1200,900,500,500,0.05,fit_to_points=True)
    xs=[point[0] for point in result]; ys=[point[1] for point in result]
    assert max(xs)-min(xs) == pytest.approx(450)
    assert max(ys)-min(ys) == pytest.approx(112.5)
    assert sum(xs) == pytest.approx(0)
    assert sum(ys) == pytest.approx(0)

@pytest.mark.parametrize("args", [(0,1,1,1),(1,0,1,1),(1,1,0,1),(1,1,1,-1)])
def test_invalid_dimensions(args):
    with pytest.raises(ValueError): map_points_to_world([], *args)
