import Eto.Drawing as drawing
import Eto.Forms as forms

class DrawingCanvas(forms.Drawable):
    def __init__(self):
        super().__init__(); self.Size=drawing.Size(640,360); self.points=[]; self.drawing=False; self.BackgroundColor=drawing.Colors.White
        self.MouseDown += self._down; self.MouseMove += self._move; self.MouseUp += self._up; self.Paint += self._paint
    def _down(self,s,e): self.points=[(e.Location.X,e.Location.Y)]; self.drawing=True; self.Invalidate()
    def _move(self,s,e):
        if self.drawing and (not self.points or (e.Location.X-self.points[-1][0])**2+(e.Location.Y-self.points[-1][1])**2>=4): self.points.append((e.Location.X,e.Location.Y)); self.Invalidate()
    def _up(self,s,e): self.drawing=False
    def _paint(self,s,e):
        if len(self.points)>1:
            pts=[drawing.PointF(x,y) for x,y in self.points]; e.Graphics.DrawLines(drawing.Pen(drawing.Colors.OrangeRed,3),pts)
    def clear(self): self.points=[]; self.Invalidate()
