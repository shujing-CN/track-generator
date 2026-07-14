import random
from PIL import Image, ImageDraw
import pytest
from processing.image_segmentation import auto_target_color, segment_by_color, largest_component, extract_ordered_path

@pytest.mark.parametrize("bg,line", [((255,255,255),(0,0,0)),((0,0,0),(255,255,255)),((120,120,120),(255,0,0)),((0,80,180),(255,230,0))])
def test_auto_color_and_segmentation(bg,line):
    im=Image.new("RGB",(40,20),bg); ImageDraw.Draw(im).line((3,10,36,10),fill=line,width=1)
    color=auto_target_color(im); mask=segment_by_color(im,color,.25)
    assert sum(map(sum,mask)) >= 30

def test_transparent_background():
    im=Image.new("RGBA",(30,20),(0,0,0,0)); ImageDraw.Draw(im).line((2,10,27,10),fill=(20,200,30,255),width=1)
    mask=segment_by_color(im,(20,200,30),.2); assert sum(map(sum,mask))==26

def test_thick_line_extracts_ordered_centerline():
    im=Image.new("RGB",(50,30),(230,230,230)); ImageDraw.Draw(im).line((5,15,44,15),fill=(220,20,20),width=5)
    points,closed,mask,color=extract_ordered_path(im,(220,20,20),.25)
    assert not closed and len(points)>20

def test_slight_noise_and_color_variation():
    im=Image.new("RGB",(60,30),(235,235,235)); draw=ImageDraw.Draw(im)
    for x in range(5,55): draw.point((x,15),fill=(200+(x%15),20+(x%8),25))
    random.seed(7)
    for _ in range(20):
        x,y=random.randrange(60),random.randrange(30); draw.point((x,y),fill=(210,205,205))
    mask=largest_component(segment_by_color(im,(205,24,25),.28))
    assert sum(map(sum,mask)) >= 45

def test_blank_and_multiple_regions_rejected():
    with pytest.raises(ValueError): auto_target_color(Image.new("RGB",(20,20),"white"))
    mask=[[False]*20 for _ in range(10)]
    for x in range(2,8): mask[2][x]=True; mask[7][x]=True
    with pytest.raises(ValueError, match="multiple"): largest_component(mask)
