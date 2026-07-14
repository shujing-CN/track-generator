import pytest
from processing.path_ordering import order_mask_path, PathOrderingError

def mask(points,w=8,h=8): return [[(x,y) in points for x in range(w)] for y in range(h)]

def test_open_line():
    ordered,closed=order_mask_path(mask({(1,2),(2,2),(3,2),(4,2)}))
    assert not closed and len(ordered)==4

def test_closed_loop():
    points={(2,1),(3,1),(4,2),(4,3),(3,4),(2,4),(1,3),(1,2)}
    ordered,closed=order_mask_path(mask(points))
    assert closed and len(ordered)==len(points)

def test_branch_rejected():
    with pytest.raises(PathOrderingError, match="branched"): order_mask_path(mask({(1,2),(2,2),(3,2),(2,1)}))

def test_disconnected_rejected():
    with pytest.raises(PathOrderingError, match="disconnected"): order_mask_path(mask({(1,1),(2,1),(5,5),(6,5)}))
