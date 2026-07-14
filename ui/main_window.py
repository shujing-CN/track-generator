import os, tempfile, traceback
import Eto.Drawing as drawing
import Eto.Forms as forms
import System
from PIL import Image

from config import app_path, load_config, save_config
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
        self.mode_index=0
        self.draw_mode_button=self._button("手绘输入",self._use_draw_mode)
        self.image_mode_button=self._button("图片输入",self._use_image_mode)
        self.input_panel=forms.Panel(); self.input_panel.Content=self.canvas
        self.width=self._numeric(self.config["default_map_width"],1,100000); self.length=self._numeric(self.config["default_map_length"],1,100000); self.track_width=self._numeric(self.config["default_track_width"],.01,10000)
        self.smoothing=self._numeric(self.config["default_smoothing"],0,1,.05); self.spacing=self._numeric(self.config["default_sample_spacing"],.1,1000,.5)
        self.tolerance=self._numeric(.25,.01,1.5,.05)
        self.show_raw=forms.CheckBox(); self.show_raw.Text="显示原始路径"; self.show_raw.Checked=True; self.show_raw.CheckedChanged+=self._preview_visibility
        self.show_beautified=forms.CheckBox(); self.show_beautified.Text="显示美化路径"; self.show_beautified.Checked=True; self.show_beautified.CheckedChanged+=self._preview_visibility
        self.closed=forms.CheckBox(); self.closed.Text="闭合路径"
        self.terrain=forms.CheckBox(); self.terrain.Text="生成基础地面"; self.terrain.Checked=True
        self.thickness=self._numeric(.3,.05,100,.05)
        from export.unreal_launcher import find_unreal_editors
        detected=find_unreal_editors()
        self.editor=forms.TextBox(); self.editor.Text=self.config.get("unreal_editor_path",'') or (detected[0] if detected else "")
        self.project=forms.TextBox(); self.project.Text=app_path(self.config.get("unreal_project_directory",'') or os.path.join("unreal_projects","GeneratedTrackFPS"))
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
        p=forms.DynamicLayout(); p.Spacing=drawing.Size(8,8); p.AddRow(self._label("输入模式"),self.draw_mode_button,self.image_mode_button)
        p.AddRow(self.input_panel)
        p.AddRow(self._button("清空",self._clear),self._button("上传图片",self._upload),self._button("自动识别线条",self._auto),self._button("手动选择线条颜色",self._select_hint),self._button("确认图片路径",self._confirm))
        grid=forms.DynamicLayout(); grid.Spacing=drawing.Size(8,6)
        grid.AddRow(self._label("地图宽度"),self.width,self._label("地图长度"),self.length,self._label("赛道宽度"),self.track_width)
        grid.AddRow(self._label("路径美化强度"),self.smoothing,self._label("采样间距"),self.spacing,self._label("颜色容差"),self.tolerance)
        grid.AddRow(self._label("美化预设"),self._button("低",self._beauty_low),self._button("中",self._beauty_medium),self._button("高",self._beauty_high),self._button("刷新对比预览",self._preview_beauty))
        grid.AddRow(self.show_raw,self.show_beautified)
        grid.AddRow(self.closed,self.terrain,self._label("路面厚度"),self.thickness)
        p.AddRow(grid); p.AddRow(self._button("生成模型",self._generate),self._button("重新生成",self._generate),self._button("导出模型",self._export),self._button("打开 Unreal Engine",self._unreal))
        p.AddRow(self._label("UnrealEditor 路径"),self.editor,self._button("选择 UnrealEditor",self._browse_editor))
        p.AddRow(self._label("UE 项目输出目录"),self.project,self._button("选择输出目录",self._browse_project)); p.AddRow(self._label("")); p.AddRow(self.status)
        scroll=forms.Scrollable(); scroll.Content=p; return scroll
    def _set_status(self,text): self.status.Text=text
    def _error(self,prefix,exc):
        self._set_status("{}：{}".format(prefix,exc))
        forms.MessageBox.Show(self,self.status.Text,"错误",forms.MessageBoxButtons.OK,forms.MessageBoxType.Error,forms.MessageBoxDefaultButton.Default)
    def _switch_mode(self,index):
        self.mode_index=index
        self.input_panel.Content=self.canvas if index==0 else self.preview
        self.input_panel.Invalidate(); self.Invalidate()
        self._set_status("当前模式：{}".format("手绘输入" if index==0 else "图片输入"))
    def _use_draw_mode(self,s,e): self._switch_mode(0)
    def _use_image_mode(self,s,e): self._switch_mode(1)
    def _set_beauty(self,value): self.smoothing.Value=value; self._preview_beauty(None,None)
    def _beauty_low(self,s,e): self._set_beauty(.2)
    def _beauty_medium(self,s,e): self._set_beauty(.55)
    def _beauty_high(self,s,e): self._set_beauty(.9)
    def _preview_visibility(self,s,e):
        raw=bool(self.show_raw.Checked); beauty=bool(self.show_beautified.Checked)
        self.canvas.show_raw=raw; self.canvas.show_beautified=beauty; self.preview.show_raw=raw; self.preview.show_beautified=beauty
        self.canvas.Invalidate(); self.preview.Invalidate()
    def _preview_beauty(self,s,e):
        try:
            raw,sw,sh=self._source(); closed=bool(self.closed.Checked)
            spacing=max(2.0,min(sw,sh)/120.0)
            beauty=process_path(raw,max(.5,spacing*.15),float(self.smoothing.Value),spacing,closed)
            if self.mode_index==0: self.canvas.set_preview(beauty)
            else: self.preview.set_paths(raw,beauty)
            self._set_status("路径对比预览已刷新：原始 {} 点，美化后 {} 点".format(len(raw),len(beauty)))
        except Exception as exc: self._error("路径美化预览失败",exc)
    def _clear(self,s,e):
        if self.mode_index==0: self.canvas.clear()
        else: self.image=None; self.image_path=None; self.image_points=[]; self.image_confirmed=False; self.preview.bitmap=None; self.preview.Invalidate()
        self._set_status("当前输入已清空")
    def _upload(self,s,e):
        dialog=forms.OpenFileDialog(); extensions=System.Array[System.String]([".png",".jpg",".jpeg",".bmp"]); dialog.Filters.Add(forms.FileFilter("图片",extensions))
        if dialog.ShowDialog(self)!=forms.DialogResult.Ok: return
        try:
            if os.path.splitext(dialog.FileName)[1].lower() not in SUPPORTED_EXTENSIONS: raise ValueError("不支持的图片格式")
            self.image=Image.open(dialog.FileName); self.image.load(); self.image_path=dialog.FileName; self.target_color=None; self.image_confirmed=False
            self.preview.set_file(dialog.FileName,self.image.size); self._switch_mode(1); self._set_status("图片已加载：{} × {}，请识别并确认路径".format(*self.image.size))
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
        if self.mode_index==0:
            if len(self.canvas.points)<2: raise ValueError("请先绘制至少两个有效点")
            return self.canvas.points,self.canvas.Width,self.canvas.Height
        if not self.image_confirmed: raise ValueError("图片路径尚未确认")
        return self.image_points,self.image.width,self.image.height
    def _generate(self,s,e):
        try:
            raw,sw,sh=self._source(); closed=bool(self.closed.Checked); mw,ml,tw=float(self.width.Value),float(self.length.Value),float(self.track_width.Value)
            if tw<=0 or tw>=min(mw,ml): raise ValueError("赛道宽度必须大于 0 且明显小于地图尺寸")
            world_raw=map_points_to_world(raw,sw,sh,mw,ml); points=process_path(world_raw,max(.01,float(self.spacing.Value)*.15),float(self.smoothing.Value),float(self.spacing.Value),closed)
            ids=self.generated.generate(self.doc,points,world_raw,mw,ml,tw,closed,bool(self.terrain.Checked),.1,float(self.thickness.Value),float(self.spacing.Value),bool(self.show_raw.Checked),bool(self.show_beautified.Checked))
            warning="；"+self.generated.quality_warnings[0] if self.generated.quality_warnings else ""
            self._set_status("Rhino 模型生成成功：原始 {} 点，处理后 {} 点，共 {} 个对象，{}{}".format(len(raw),len(points),len(ids),"闭合" if closed else "开放",warning))
        except Exception as exc: self._error("模型生成失败",exc)
    def _export(self,s,e):
        dialog=forms.SaveFileDialog(); dialog.Filters.Add(forms.FileFilter("Wavefront OBJ",".obj")); dialog.Filters.Add(forms.FileFilter("FBX",".fbx")); dialog.FileName="generated_track.obj"
        if dialog.ShowDialog(self)!=forms.DialogResult.Ok: return
        try:
            from export.model_exporter import export_generated
            path=export_generated(self.doc,self.generated.object_ids,dialog.FileName); self.config["export_directory"]=os.path.dirname(path); save_config(self.config); self._set_status("导出成功："+path)
        except Exception as exc: self._error("导出失败",exc)
    def _browse_editor(self,s,e):
        dialog=forms.OpenFileDialog(); dialog.Filters.Add(forms.FileFilter("UnrealEditor",System.Array[System.String]([".exe"])))
        if dialog.ShowDialog(self)==forms.DialogResult.Ok:
            self.editor.Text=dialog.FileName; self._set_status("已选择 UnrealEditor："+dialog.FileName)
    def _browse_project(self,s,e):
        dialog=forms.SelectFolderDialog(); dialog.Title="选择 UE 第一人称项目输出目录"; dialog.Directory=self.project.Text
        if dialog.ShowDialog(self)==forms.DialogResult.Ok:
            self.project.Text=dialog.Directory; self._set_status("已选择 UE 项目输出目录："+dialog.Directory)
    def _unreal(self,s,e):
        try:
            from export.model_exporter import export_generated
            from export.unreal_launcher import launch_first_person_track_project
            model_dir=app_path("model"); os.makedirs(model_dir,exist_ok=True)
            model_path=os.path.join(model_dir,"generated_track.obj")
            if self.generated.object_ids:
                export_generated(self.doc,self.generated.object_ids,model_path)
            elif not os.path.isfile(model_path):
                raise ValueError("请先生成赛道模型，或确保 model/generated_track.obj 存在")
            project,process=launch_first_person_track_project(self.editor.Text.strip(),model_path,self.project.Text.strip())
            self.config["unreal_editor_path"]=self.editor.Text.strip(); self.config["unreal_project_directory"]=project["project_dir"]; self.config["export_directory"]=model_dir; save_config(self.config); self._set_status("已创建并打开第一人称 UE 项目："+project["uproject"])
        except Exception as exc: self._error("Unreal Engine 启动失败",exc)
    def OnClosed(self,e):
        if self.preview_temp and os.path.exists(self.preview_temp):
            try: os.remove(self.preview_temp)
            except OSError: pass
        super().OnClosed(e)
