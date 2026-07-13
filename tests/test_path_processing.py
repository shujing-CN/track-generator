import math
import pytest
from processing.path_processing import clean_points, process_path, resample_points, smooth_points, PathProcessingError

def test_clean_invalid_duplicate_dense():
    assert clean_points([None,(0,0),(0,0),("x",1),(0.1,0),(2,0)], .5) == [(0.,0.),(2.,0.)]

@pytest.mark.parametrize("points", [[], [(1,1)], [(0,0),(0,0)]])
def test_too_few(points):
    with pytest.raises(PathProcessingError): process_path(points)

def test_open_keeps_endpoints_and_uniform_spacing():
    result=process_path([(0,0),(2,1),(5,0),(10,0)], smoothing=.4, spacing=1)
    assert result[0] == (0.,0.) and result[-1] == (10.,0.)
    lengths=[math.dist(a,b) for a,b in zip(result,result[1:])]
    assert max(lengths)-min(lengths) < .15

def test_closed_has_no_duplicate_endpoint():
    result=resample_points([(0,0),(10,0),(10,10),(0,10)],2,True)
    assert result[0] != result[-1] and len(result)>=3

def test_smoothing_stays_in_bounds():
    result=smooth_points([(0,0),(2,5),(4,0)],1)
    assert result[0]==(0,0) and result[-1]==(4,0) and 0<=result[1][1]<=5
