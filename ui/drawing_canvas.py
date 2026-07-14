import Eto.Drawing as drawing
import Eto.Forms as forms

class DrawingCanvas(forms.Drawable):
    def __init__(self):
        super().__init__(); self.Size=drawing.Size(640,360); self.points=[]; self.beautified_points=[]; self.show_raw=True; self.show_beautified=True; self.drawing=False; self.BackgroundColor=drawing.Colors.White
        self.MouseDown += self._down; self.MouseMove += self._move; self.MouseUp += self._up; self.Paint += self._paint
    def _down(self,s,e): self.points=[(e.Location.X,e.Location.Y)]; self.drawing=True; self.Invalidate()
    def _move(self,s,e):
        if self.drawing and (not self.points or (e.Location.X-self.points[-1][0])**2+(e.Location.Y-self.points[-1][1])**2>=4): self.points.append((e.Location.X,e.Location.Y)); self.Invalidate()
    def _up(self,s,e): self.drawing=False
    def _paint(self,s,e):
        if self.show_raw and len(self.points)>1:
            pts=[drawing.PointF(x,y) for x,y in self.points]; e.Graphics.DrawLines(drawing.Pen(drawing.Colors.Gray,2),pts)
        if self.show_beautified and len(self.beautified_points)>1:
            pts=[drawing.PointF(x,y) for x,y in self.beautified_points]; e.Graphics.DrawLines(drawing.Pen(drawing.Colors.Black,3),pts)
    def set_preview(self,points): self.beautified_points=list(points); self.Invalidate()
    def clear(self): self.points=[]; self.beautified_points=[]; self.Invalidate()
