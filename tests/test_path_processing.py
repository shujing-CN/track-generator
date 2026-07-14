import math
import pytest
from processing.path_processing import chaikin_smooth, clean_points, process_path, remove_short_backtracks, resample_points, smooth_points, PathProcessingError

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

def test_default_smoothing_runs_multiple_chaikin_rounds():
    source=[(0,0),(5,5),(10,0)]
    assert len(chaikin_smooth(source,3)) > len(source)
    result=process_path(source,min_distance=.01,smoothing=.3,spacing=.5)
    assert result[0]==(0,0) and result[-1]==(10,0)

def _roughness(points,closed=False):
    values=[]
    indices=range(len(points)) if closed else range(1,len(points)-1)
    for i in indices:
        a,b,c=points[(i-1)%len(points)],points[i],points[(i+1)%len(points)]
        values.append(abs((a[1]-2*b[1]+c[1])))
    return sum(values)/max(1,len(values))

def test_mouse_jitter_is_visibly_reduced():
    raw=[(x,(-1 if x%2 else 1)*.8+math.sin(x/5)) for x in range(31)]
    beauty=process_path(raw,.01,.55,.5)
    assert _roughness(beauty)<_roughness(raw)*.2

def test_high_preset_is_smoother_than_low_without_large_shape_change():
    raw=[(0,0),(5,0),(5,5),(10,5)]
    low=process_path(raw,.01,.2,.5); high=process_path(raw,.01,.9,.5)
    assert _roughness(high)<=_roughness(low)
    assert high[0]==raw[0] and high[-1]==raw[-1]

def test_closed_ring_has_smooth_seam_and_no_duplicate_endpoint():
    raw=[(math.cos(i*math.pi/4)*10,math.sin(i*math.pi/4)*10) for i in range(8)]
    result=process_path(raw,.01,.55,1,True)
    assert result[0]!=result[-1]
    lengths=[math.dist(result[i],result[(i+1)%len(result)]) for i in range(len(result))]
    assert max(lengths)-min(lengths)<.2

def test_sparse_path_becomes_dense_and_smooth():
    result=process_path([(0,0),(15,8),(30,0)],.01,.55,1)
    assert len(result)>20 and result[0]==(0,0) and result[-1]==(30,0)

def test_short_pixel_backtrack_removed_but_large_fold_preserved():
    cleaned=remove_short_backtracks([(0,0),(5,0),(4.8,.01),(10,0)],1,False)
    assert len(cleaned)==3
    large=remove_short_backtracks([(0,0),(10,0),(.1,.01)],1,False)
    assert len(large)==3
