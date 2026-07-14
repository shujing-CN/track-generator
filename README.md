# Rhino 8 手绘赛道基础地图生成工具

这是一个运行在 Rhino 8 内部的 Python 3 + RhinoCommon + Eto.Forms 工具。它可以从手绘轨迹或图片中的单条显著路径生成赛道基础地图，并导出为 Unreal Engine 可使用的模型。

程序不使用在线生成式 AI 推测赛道形状。最终几何只来自用户笔迹或图片像素，并经过确定性的清理、等距重采样、平滑、坐标映射和 Mesh 生成流程。

## 已实现功能

- 手绘输入和图片输入两种模式。
- 图片路径提取支持 PNG/JPG/JPEG/BMP、自动识别线条、手动取色、颜色容差和遮罩预览。
- 输入路径会自动删除重复点、零长度段和过密点，然后等距重采样并平滑。
- 路径美化提供低、中、高三个预设，可显示原始路径和美化路径对比。
- Rhino 文档内生成 `SourcePath`、`Centerline`、`Road`、`CurbsRed`、`CurbsWhite`、`Terrain` 图层对象。
- 赛道路面是黑色实心 Mesh。
- 弯道外侧自动生成红白相间的实心路肩，路肩贴合道路边缘、略高于路面，并尽量避免缝隙。
- 普通直线、圆形、S 形、轻微抖动手绘线和 90 度折线会优先自动平滑并生成；极端折返、自交或宽度明显超过局部半径时才提示用户。
- 可从 Rhino 导出 OBJ/FBX。
- 可直接创建独立的 Unreal Engine 第一人称项目，把当前生成的赛道模型作为地图导入并打开，不再依赖已有 `.uproject`。

## 环境要求

- Windows + Rhino 8。
- Rhino 8 ScriptEditor 的 Python 3 运行时。
- Pillow。
- 如需打开 UE：本机 Unreal Engine 5 编辑器，且引擎安装目录中包含 `Templates/TP_FirstPersonBP` 第一人称模板。

在 Rhino 8 的 Python 3 ScriptEditor 中安装 Pillow：

```python
import subprocess, sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow>=10,<12"])
```

开发测试环境安装依赖：

```powershell
python -m pip install -r requirements.txt
```

## 在 Rhino 8 中启动

1. 打开 Rhino 8 和一个可写文档。
2. 打开 `ScriptEditor`，选择 Python 3。
3. 打开仓库根目录的 `main.py` 并运行。
4. “手绘赛道生成工具”窗口会以模型外窗口显示。

不要使用 Rhino 7 的 IronPython 2 运行本项目。

## 基本使用

### 手绘模式

1. 点击“手绘输入”。
2. 在画布按下鼠标并连续绘制，松开结束。
3. 设置地图宽度、地图长度、赛道宽度、平滑程度、采样间距、闭合和地面选项。
4. 点击“生成模型”。
5. 参数变化后点击“重新生成”，原始手绘点会保留。

### 图片模式

1. 点击“上传图片”，选择 PNG/JPG/JPEG/BMP。
2. 点击“自动识别线条”；如果结果不对，使用“手动选择线条颜色”在预览图中点选目标线条。
3. 调整“颜色容差”，直到预览遮罩只覆盖目标路径。
4. 点击“确认图片路径”。
5. 设置参数并点击“生成模型”。

图片最好只包含一条连续、无分叉、与背景有明显颜色或亮度差异的主路径。复杂背景可以用手动取色和容差调整处理。

## 导出模型

1. 先成功生成模型。
2. 点击“导出模型”。
3. 选择 `.obj` 或 `.fbx` 路径。
4. 工具只选择本次记录的生成对象调用 Rhino 导出，并在目标文件真实存在后报告成功。

OBJ 是当前推荐的 UE 交换格式。

## 直接创建并打开 UE 第一人称项目

窗口底部需要填写：

- `UnrealEditor 路径`：例如 `<UnrealEditor.exe path>`
- `UE 项目输出目录`：例如 `<repo-root>/unreal_projects/GeneratedTrackFPS`

点击“打开 Unreal Engine”后，工具会：

1. 如果 Rhino 当前已经生成赛道对象，先导出 `model/generated_track.obj`。
2. 如果当前没有 Rhino 生成对象，则使用已有的 `model/generated_track.obj`。
3. 从当前 UE 安装的 `Templates/TP_FirstPersonBP` 复制一个新的第一人称项目。
4. 启用 UE 的 `PythonScriptPlugin`。
5. 把赛道模型复制到新项目的 `TrackSource/generated_track.obj`。
6. 创建启动导入脚本 `Scripts/setup_track_project.py`。
7. 使用 `-DDC-ForceMemoryCache` 打开 UE，绕过本机 DerivedDataCache 不可写导致的崩溃。
8. UE 启动后自动导入模型、创建 `/Game/Track/TrackMap`，并设置为默认地图。

为了安全，工具只会自动覆盖自己创建过的 `GeneratedTrackFPS` 输出目录。如果你选择了一个已经存在但不是本工具创建的目录，程序会拒绝覆盖，避免误删已有项目。

本地配置可以从 `config.example.json` 复制为被 `.gitignore` 忽略的 `config.json`：

```json
{
  "unreal_editor_path": "<UnrealEditor.exe path>",
  "unreal_project_directory": "unreal_projects/GeneratedTrackFPS"
}
```

## 自动测试

在仓库根目录运行：

```powershell
python -m pytest -q
python -m compileall -q .
```

如果本机安装了 Rhino 8，还可以运行 Rhino 内部 smoke 测试：

```powershell
& "<RhinoCode.exe path>" script "<repo-root>\tests\rhino_ui_smoke.py"
Get-Content .\rhino_ui_smoke_result.txt
```

测试覆盖路径清理、平滑、等距重采样、图片路径提取、仓库 `images/` 样本、赛道 Mesh、路肩 Mesh、配置回退、UE 启动参数和第一人称项目生成流程。

## 已知边界

- 当前只支持单条主要连续路径；多条线、大量分叉、自交、严重遮挡或与背景几乎同色的图片仍可能失败。
- 极端折返或赛道宽度明显超过局部转弯半径时，程序会提示用户降低宽度或提高平滑。
- UE 项目创建依赖引擎自带第一人称模板；如果引擎安装缺少 `TP_FirstPersonBP`，需要先通过 Epic/UE 安装对应模板。
