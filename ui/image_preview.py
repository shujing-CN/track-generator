import Eto.Drawing as drawing
import Eto.Forms as forms

class ImagePreview(forms.Drawable):
    def __init__(self,on_pick=None):
        super().__init__(); self.Size=drawing.Size(640,360); self.bitmap=None; self.image_size=None; self.on_pick=on_pick; self.MouseDown+=self._click; self.Paint+=self._paint
    def set_file(self,path,size):
        if self.bitmap: self.bitmap.Dispose()
        self.bitmap=drawing.Bitmap(path); self.image_size=size; self.Invalidate()
    def _rect(self):
        if not self.bitmap: return None
        scale=min(self.Width/self.bitmap.Width,self.Height/self.bitmap.Height); w=self.bitmap.Width*scale; h=self.bitmap.Height*scale
        return drawing.RectangleF((self.Width-w)/2,(self.Height-h)/2,w,h)
    def _paint(self,s,e):
        e.Graphics.Clear(drawing.Colors.White)
        if self.bitmap: e.Graphics.DrawImage(self.bitmap,self._rect())
    def _click(self,s,e):
        rect=self._rect()
        if rect and rect.Contains(e.Location) and self.on_pick:
            x=int((e.Location.X-rect.X)*self.bitmap.Width/rect.Width); y=int((e.Location.Y-rect.Y)*self.bitmap.Height/rect.Height); self.on_pick(x,y)
