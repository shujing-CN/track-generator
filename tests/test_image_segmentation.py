import random
from PIL import Image, ImageDraw
import pytest
from processing.image_segmentation import auto_target_color, segment_by_color, largest_component, extract_ordered_path, mask_has_enclosed_hole

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

def test_uneven_thick_line_extracts_main_shape():
    im=Image.new("RGB",(90,50),(240,240,240)); draw=ImageDraw.Draw(im)
    centers=[(8+i,25+int(10*__import__("math").sin(i/10))) for i in range(72)]
    for i,point in enumerate(centers):
        radius=2+(i%13)//4
        x,y=point
        draw.ellipse((x-radius,y-radius,x+radius,y+radius),fill=(30,80,220))
    points,closed,mask,color=extract_ordered_path(im,(30,80,220),.28)
    assert not closed
    assert len(points)>45
    assert max(x for x,y in points)-min(x for x,y in points)>60

def test_blobbed_line_uses_rough_center_path_instead_of_failing():
    im=Image.new("RGB",(80,50),(245,245,245)); draw=ImageDraw.Draw(im)
    draw.line((8,40,25,28,42,34,62,10),fill=(220,40,40),width=5)
    draw.ellipse((28,22,48,42),fill=(220,40,40))
    points,closed,mask,color=extract_ordered_path(im,(220,40,40),.25)
    assert not closed
    assert len(points)>25

def test_closed_uneven_ring_stays_closed_by_shape_hole():
    im=Image.new("RGB",(90,70),(245,245,245)); draw=ImageDraw.Draw(im)
    points=[(45+int(30*__import__("math").cos(i/40)),35+int(20*__import__("math").sin(i/40))) for i in range(252)]
    for i,(x,y) in enumerate(points):
        radius=2+(i%17)//5
        draw.ellipse((x-radius,y-radius,x+radius,y+radius),fill=(20,160,40))
    extracted,closed,mask,color=extract_ordered_path(im,(20,160,40),.25)
    assert mask_has_enclosed_hole(mask)
    assert closed
    assert len(extracted)>80

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
