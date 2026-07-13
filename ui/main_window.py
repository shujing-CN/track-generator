import os, tempfile, traceback
import Eto.Drawing as drawing
import Eto.Forms as forms
from PIL import Image

from config import load_config, save_config
from processing.path_processing import process_path
from processing.coordinate_mapping import map_points_to_world
from processing.image_segmentation import auto_target_color, segment_by_color, largest_component, mask_preview, extract_ordered_path, SUPPORTED_EXTENSIONS
from .drawing_canvas import DrawingCanvas
from .image_preview import ImagePreview

class TrackGeneratorWindow(forms.Form):
    def __init__(self,doc):
        super().__init__(); self.Title="手绘赛道基础地图生成工具"; self.ClientSize=drawing.Size(980,760); self.Padding=drawing.Padding(12)
        self.doc=doc; self.config=load_config(); self.image=None; self.image_path=None; self.image_points=[]; self.image_closed=False; self.image_confirmed=False; self.target_color=None; self.preview_temp=None
        from rhino.document_manager import GeneratedDocument
        self.generated=GeneratedDocument(); self.canvas=DrawingCanvas(); self.preview=ImagePreview(self._pick_color)
        self.mode=forms.DropDown()
        self.mode.Items.Add(forms.ListItem("手绘输入")); self.mode.Items.Add(forms.ListItem("图片输入"))
        self.mode.SelectedIndex=0; self.mode.SelectedIndexChanged+=self._mode_changed
        self.input_panel=forms.Panel(); self.input_panel.Content=self.canvas
        self.width=self._numeric(self.config["default_map_width"],1,100000); self.length=self._numeric(self.config["default_map_length"],1,100000); self.track_width=self._numeric(self.config["default_track_width"],.01,10000)
        self.smoothing=self._numeric(self.config["default_smoothing"],0,1,.05); self.spacing=self._numeric(self.config["default_sample_spacing"],.1,1000,.5)
        self.tolerance=self._numeric(.25,.01,1.5,.05)
        self.closed=forms.CheckBox(); self.closed.Text="闭合路径"
        self.terrain=forms.CheckBox(); self.terrain.Text="生成基础地面"; self.terrain.Checked=True
        self.thickness=self._numeric(0,0,100,.1)
        self.editor=forms.TextBox(); self.editor.Text=self.config.get("unreal_editor_path",'')
        self.project=forms.TextBox(); self.project.Text=self.config.get("unreal_project_path",'')
        self.status=forms.Label(); self.status.Text="就绪"; self.status.Wrap=forms.WrapMode.Word
        self.Content=self._layout()
    def _numeric(self,value,minv,maxv,inc=1):
        control=forms.NumericStepper(); control.Value=float(value); control.MinValue=minv; control.MaxValue=maxv; control.Increment=inc; control.DecimalPlaces=2
        return control
    def _label(self,text):
        control=forms.Label(); control.Text=text; return control
    def _button(self,text,handler):
        b=forms.Button(); b.Text=text; b.Click+=handler; return b
    def _layout(self):
        p=forms.DynamicLayout(); p.Spacing=drawing.Size(8,8); p.AddRow(self._label("输入模式"),self.mode)
        p.AddRow(self.input_panel)
        p.AddRow(self._button("清空",self._clear),self._button("上传图片",self._upload),self._button("自动识别线条",self._auto),self._button("手动选择线条颜色",self._select_hint),self._button("确认图片路径",self._confirm))
        grid=forms.DynamicLayout(); grid.Spacing=drawing.Size(8,6)
        grid.AddRow(self._label("地图宽度"),self.width,self._label("地图长度"),self.length,self._label("赛道宽度"),self.track_width)
        grid.AddRow(self._label("平滑程度"),self.smoothing,self._label("采样间距"),self.spacing,self._label("颜色容差"),self.tolerance)
        grid.AddRow(self.closed,self.terrain,self._label("路面厚度"),self.thickness)
        p.AddRow(grid); p.AddRow(self._button("生成模型",self._generate),self._button("重新生成",self._generate),self._button("导出模型",self._export),self._button("打开 Unreal Engine",self._unreal))
        p.AddRow(self._label("UnrealEditor 路径"),self.editor); p.AddRow(self._label(".uproject 路径"),self.project); p.AddRow(forms.Separator()); p.AddRow(self.status)
        scroll=forms.Scrollable(); scroll.Content=p; return scroll
    def _set_status(self,text): self.status.Text=text
    def _error(self,prefix,exc): self._set_status("{}：{}".format(prefix,exc)); forms.MessageBox.Show(self,self.status.Text,"错误",forms.MessageBoxButtons.OK,forms.MessageBoxType.Error)
    def _mode_changed(self,s,e):
        self.input_panel.Content=self.canvas if self.mode.SelectedIndex==0 else self.preview
        self.input_panel.Invalidate(); self.Invalidate()
    def _clear(self,s,e):
        if self.mode.SelectedIndex==0: self.canvas.clear()
        else: self.image=None; self.image_path=None; self.image_points=[]; self.image_confirmed=False; self.preview.bitmap=None; self.preview.Invalidate()
        self._set_status("当前输入已清空")
    def _upload(self,s,e):
        dialog=forms.OpenFileDialog(); dialog.Filters.Add(forms.FileFilter("图片",".png",".jpg",".jpeg",".bmp"))
        if dialog.ShowDialog(self)!=forms.DialogResult.Ok: return
        try:
            if os.path.splitext(dialog.FileName)[1].lower() not in SUPPORTED_EXTENSIONS: raise ValueError("不支持的图片格式")
            self.image=Image.open(dialog.FileName); self.image.load(); self.image_path=dialog.FileName; self.target_color=None; self.image_confirmed=False
            self.preview.set_file(dialog.FileName,self.image.size); self.mode.SelectedIndex=1; self._set_status("图片已加载：{} × {}，请识别并确认路径".format(*self.image.size))
        except Exception as exc: self._error("图片无法读取",exc)
    def _pick_color(self,x,y):
        if not self.image: return
        self.target_color=self.image.convert("RGBA").getpixel((x,y)); self._extract("已从像素 ({}, {}) 取色".format(x,y))
    def _select_hint(self,s,e):
        self._set_status("请在图片中的目标线上点击一个像素；点击后会按当前颜色容差刷新预览")
    def _auto(self,s,e):
        if not self.image: self._error("无法识别",ValueError("请先上传图片")); return
        try: self.target_color=auto_target_color(self.image); self._extract("自动识别完成")
        except Exception as exc: self._error("自动识别失败，请在线条上取色并调整容差",exc)
    def _extract(self,prefix):
        try:
            points,closed,mask,color=extract_ordered_path(self.image,self.target_color,float(self.tolerance.Value)); self.image_points=points; self.image_closed=closed; self.image_confirmed=False
            preview=mask_preview(self.image,mask); fd,path=tempfile.mkstemp(suffix=".png"); os.close(fd); preview.save(path); old=self.preview_temp; self.preview_temp=path; self.preview.set_file(path,self.image.size)
            if old and os.path.exists(old): os.remove(old)
            self._set_status("{}；提取 {} 点，{}。请确认图片路径".format(prefix,len(points),"闭合" if closed else "开放"))
        except Exception as exc: self._error("线条提取失败",exc)
    def _confirm(self,s,e):
        if len(self.image_points)<2: self._error("无法确认",ValueError("请先成功提取目标线")); return
        self.image_confirmed=True; self.closed.Checked=self.image_closed; self._set_status("图片路径已确认，共 {} 点".format(len(self.image_points)))
    def _source(self):
        if self.mode.SelectedIndex==0:
            if len(self.canvas.points)<2: raise ValueError("请先绘制至少两个有效点")
            return self.canvas.points,self.canvas.Width,self.canvas.Height
        if not self.image_confirmed: raise ValueError("图片路径尚未确认")
        return self.image_points,self.image.width,self.image.height
    def _generate(self,s,e):
        try:
            raw,sw,sh=self._source(); closed=bool(self.closed.Checked); mw,ml,tw=float(self.width.Value),float(self.length.Value),float(self.track_width.Value)
            if tw<=0 or tw>=min(mw,ml): raise ValueError("赛道宽度必须大于 0 且明显小于地图尺寸")
            world_raw=map_points_to_world(raw,sw,sh,mw,ml); points=process_path(world_raw,max(.01,float(self.spacing.Value)*.15),float(self.smoothing.Value),float(self.spacing.Value),closed)
            ids=self.generated.generate(self.doc,points,world_raw,mw,ml,tw,closed,bool(self.terrain.Checked),.1,float(self.thickness.Value))
            self._set_status("Rhino 模型生成成功：原始 {} 点，处理后 {} 点，共 {} 个对象，{}".format(len(raw),len(points),len(ids),"闭合" if closed else "开放"))
        except Exception as exc: self._error("模型生成失败",exc)
    def _export(self,s,e):
        dialog=forms.SaveFileDialog(); dialog.Filters.Add(forms.FileFilter("Wavefront OBJ",".obj")); dialog.Filters.Add(forms.FileFilter("FBX",".fbx")); dialog.FileName="generated_track.obj"
        if dialog.ShowDialog(self)!=forms.DialogResult.Ok: return
        try:
            from export.model_exporter import export_generated
            path=export_generated(self.doc,self.generated.object_ids,dialog.FileName); self.config["export_directory"]=os.path.dirname(path); save_config(self.config); self._set_status("导出成功："+path)
        except Exception as exc: self._error("导出失败",exc)
    def _unreal(self,s,e):
        try:
            from export.unreal_launcher import launch_unreal
            launch_unreal(self.editor.Text.strip(),self.project.Text.strip()); self.config["unreal_editor_path"]=self.editor.Text.strip(); self.config["unreal_project_path"]=self.project.Text.strip(); save_config(self.config); self._set_status("Unreal Engine 启动命令已执行")
        except Exception as exc: self._error("Unreal Engine 启动失败",exc)
    def OnClosed(self,e):
        if self.preview_temp and os.path.exists(self.preview_temp):
            try: os.remove(self.preview_temp)
            except OSError: pass
        super().OnClosed(e)
