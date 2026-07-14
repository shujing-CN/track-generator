from pathlib import Path

from PIL import Image

from geometry.track_builder import build_track_with_recovery
from processing.coordinate_mapping import map_points_to_world
from processing.image_segmentation import extract_ordered_path
from processing.path_processing import process_path


def test_all_tracked_images_generate_closed_track_meshes():
    image_dir=Path(__file__).parents[1]/"images"
    paths=sorted(image_dir.glob("*"))
    assert paths
    for path in paths:
        with Image.open(path) as image:
            points,closed,mask,color=extract_ordered_path(image,None,.25)
            assert closed and len(points)>100
            world=map_points_to_world(points,image.width,image.height,500,500)
            beauty=process_path(world,.3,.55,2,True)
            final,vertices,faces=build_track_with_recovery(beauty,8,thickness=.3,closed=True)
            assert vertices and faces
