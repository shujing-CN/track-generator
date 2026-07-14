import Eto.Drawing as drawing
import Eto.Forms as forms

class ImagePreview(forms.Drawable):
    def __init__(self,on_pick=None):
        super().__init__(); self.Size=drawing.Size(640,360); self.bitmap=None; self.image_size=None; self.raw_points=[]; self.beautified_points=[]; self.show_raw=True; self.show_beautified=True; self.on_pick=on_pick; self.MouseDown+=self._click; self.Paint+=self._paint
    def set_file(self,path,size):
        if self.bitmap: self.bitmap.Dispose()
        self.bitmap=drawing.Bitmap(path); self.image_size=size; self.Invalidate()
    def _rect(self):
        if not self.bitmap: return None
        scale=min(self.Width/self.bitmap.Width,self.Height/self.bitmap.Height); w=self.bitmap.Width*scale; h=self.bitmap.Height*scale
        return drawing.RectangleF((self.Width-w)/2,(self.Height-h)/2,w,h)
    def _paint(self,s,e):
        e.Graphics.Clear(drawing.Colors.White)
        if self.bitmap:
            rect=self._rect(); e.Graphics.DrawImage(self.bitmap,rect)
            def mapped(points): return [drawing.PointF(rect.X+x*rect.Width/self.bitmap.Width,rect.Y+y*rect.Height/self.bitmap.Height) for x,y in points]
            if self.show_raw and len(self.raw_points)>1: e.Graphics.DrawLines(drawing.Pen(drawing.Colors.Gray,2),mapped(self.raw_points))
            if self.show_beautified and len(self.beautified_points)>1: e.Graphics.DrawLines(drawing.Pen(drawing.Colors.Black,3),mapped(self.beautified_points))
    def set_paths(self,raw,beautified): self.raw_points=list(raw); self.beautified_points=list(beautified); self.Invalidate()
    def _click(self,s,e):
        rect=self._rect()
        if rect and rect.Contains(e.Location) and self.on_pick:
            x=int((e.Location.X-rect.X)*self.bitmap.Width/rect.Width); y=int((e.Location.Y-rect.Y)*self.bitmap.Height/rect.Height); self.on_pick(x,y)
