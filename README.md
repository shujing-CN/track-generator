# Rhino 8 手绘赛道基础地图生成工具

这是一个运行在 Rhino 8 内部的赛道基础地图生成工具。你可以在窗口里手绘路径，或者从图片中提取一条明显路径，然后生成 Rhino 模型，并一键创建一个独立的 Unreal Engine 第一人称项目。

工具不会使用 AI 猜测赛道形状。所有几何都来自你的手绘点或图片像素，再经过确定性的清理、平滑、等距重采样、坐标映射和 Mesh 生成。

## 当前能力

- Rhino 8 内部运行，使用 Python 3、RhinoCommon 和 Eto.Forms。
- 支持手绘输入和图片输入。
- 图片输入支持 PNG、JPG、JPEG、BMP。
- 支持自动识别图片线条，也支持手动点击线条取色。
- 自动删除重复点、零长度线段和距离过近的点。
- 自动等距重采样和路径平滑。
- 路径美化提供低、中、高三个预设。
- 可以显示原始路径和美化路径对比。
- 普通直线、圆形、S 形、轻微抖动手绘线、90 度折线都应正常生成。
- 极端折返、自交、赛道宽度明显超过局部转弯半径时才会提示失败。
- Rhino 中生成中心线、黑色实心跑道、红白实心路肩、绿色基础地形。
- 路肩贴合跑道边缘，略高于跑道。
- 跑道和地形做了高度分层，避免黑色路面和绿色地形 Z-fighting 或穿模。
- 可导出 OBJ 或 FBX。
- 可直接创建并打开 Unreal Engine 第一人称项目，不需要选择已有 `.uproject`。
- UE 导入时自动做 Rhino 到 UE 的坐标轴转换，避免地图竖起来。
- UE 项目自动添加基础光照、天空和默认地图。
- UE 启动默认带 `-DDC-ForceMemoryCache`，规避 DerivedDataCache 不可写导致的崩溃。

## 目录说明

```text
<repo-root>
├─ main.py                         Rhino 中运行的入口
├─ config.example.json             本地配置示例
├─ config.py                       配置读取和项目路径解析
├─ ui/                             Rhino Eto 窗口和交互界面
├─ processing/                     路径清理、图片识别、平滑和重采样
├─ geometry/                       赛道、路肩、地形 Mesh 算法
├─ rhino/                          Rhino 文档对象、图层、材质、曲线构建
├─ export/                         Rhino 导出和 Unreal 项目生成
├─ images/                         仓库内测试图片样本
├─ model/                          默认或最近导出的赛道模型
└─ tests/                          自动测试
```

## 环境要求

- Windows
- Rhino 8
- Rhino 8 ScriptEditor 的 Python 3
- Pillow
- 如果要打开 UE：Unreal Engine 5，并且引擎目录中存在 `Templates/TP_FirstPersonBP`

例如本机 UE 路径可以是：

```text
<UnrealEditor.exe path>
```

## 安装依赖

### Rhino 8 内安装 Pillow

在 Rhino 8 的 Python 3 ScriptEditor 里执行：

```python
import subprocess
import sys

subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow>=10,<12"])
```

### 开发测试环境安装依赖

在仓库根目录运行：

```powershell
python -m pip install -r requirements.txt
```

## 在 Rhino 8 中启动工具

1. 打开 Rhino 8。
2. 打开一个可写的 Rhino 文档。
3. 打开 Rhino 的 `ScriptEditor`。
4. 选择 Python 3。
5. 打开并运行：

```text
<repo-root>\main.py
```

运行后会出现“手绘赛道基础地图生成工具”窗口。

不要用 Rhino 7 的 IronPython 2 运行本项目。

## 手绘生成赛道

1. 点击“手绘输入”。
2. 在白色画布上按住鼠标绘制路径。
3. 松开鼠标结束这一笔。
4. 设置参数：

   - 地图宽度
   - 地图长度
   - 赛道宽度
   - 路径美化强度
   - 采样间距
   - 是否闭合路径
   - 是否生成基础地面
   - 路面厚度

5. 可点击“低 / 中 / 高”快速设置平滑强度。
6. 可勾选“显示原始路径”和“显示美化路径”做对比。
7. 点击“生成模型”。
8. 如果修改了参数，点击“重新生成”。

默认建议：

```text
地图宽度：500
地图长度：500
赛道宽度：8
路径美化强度：0.55
采样间距：2
路面厚度：0.3
```

如果手绘线比较抖，把路径美化强度调高一点；如果想更接近原始笔迹，调低一点。

## 从图片生成赛道

1. 点击“图片输入”。
2. 点击“上传图片”。
3. 选择 PNG、JPG、JPEG 或 BMP。
4. 点击“自动识别线条”。
5. 如果识别不准：

   - 点击“手动选择线条颜色”；
   - 在预览图中点击目标线条；
   - 调整“颜色容差”；
   - 再次识别或确认。

6. 预览遮罩正确后，点击“确认图片路径”。
7. 设置地图和赛道参数。
8. 点击“生成模型”。

图片建议：

- 最好只有一条主要连续路径。
- 线条和背景颜色差异要明显。
- 尽量避免多条线、分叉、自交、严重阴影、复杂纹理背景。
- 透明背景可以用，但目标线条要清楚。

仓库中的 `images/` 目录有测试样本，程序会在自动测试中验证这些图片能生成地图。

## Rhino 中生成的对象

工具会自动创建和复用 `GeneratedTrack` 相关图层：

```text
GeneratedTrack
├─ SourcePath
├─ Centerline
├─ Road
├─ CurbsRed
├─ CurbsWhite
└─ Terrain
```

对象含义：

- `SourcePath`：映射到世界坐标后的原始路径。
- `Centerline`：清理、重采样、平滑后的中心线。
- `Road`：黑色实心跑道 Mesh。
- `CurbsRed`：红色实心路肩 Mesh。
- `CurbsWhite`：白色实心路肩 Mesh。
- `Terrain`：绿色基础地形。

默认高度关系：

```text
绿色地形：Z = -0.25
黑色跑道顶面：Z = 0.45
黑色跑道底面：Z = 0.15  默认厚度 0.3 时
红白路肩顶面：Z = 0.53
```

这样跑道和地形不会贴太近，也不容易在 UE 里穿模或闪烁。

## 导出 OBJ 或 FBX

1. 先点击“生成模型”。
2. 点击“导出模型”。
3. 选择 `.obj` 或 `.fbx` 文件路径。
4. 工具只导出本次生成记录中的对象。
5. 导出完成后，状态栏会显示导出路径。

注意：如果只是为了打开 UE 项目，不需要手动导出，点击“打开 Unreal Engine”时工具会自动导出需要的 OBJ。

## 一键创建并打开 UE 第一人称项目

窗口底部需要配置两个路径。

### UnrealEditor 路径

填写 `UnrealEditor.exe` 的完整路径，例如：

```text
<UnrealEditor.exe path>
```

也可以点击“选择 UnrealEditor”选择。

### UE 项目输出目录

默认是：

```text
<repo-root>/unreal_projects/GeneratedTrackFPS
```

也可以点击“选择输出目录”选择。

建议使用默认目录，别选已有的重要 UE 项目目录。

### 点击“打开 Unreal Engine”后会发生什么

工具会自动执行：

1. 如果 Rhino 当前有生成对象，导出为：

   ```text
   <repo-root>/model/generated_track.obj
   ```

2. 如果当前没有 Rhino 生成对象，则尝试使用已有：

   ```text
   <repo-root>/model/generated_track.obj
   ```

3. 从 UE 引擎模板复制 `TP_FirstPersonBP`。
4. 创建独立项目：

   ```text
   <repo-root>/unreal_projects/GeneratedTrackFPS
   ```

5. 启用 `PythonScriptPlugin`。
6. 把模型复制到：

   ```text
   TrackSource/generated_track.obj
   ```

7. 复制时自动做坐标轴转换：

   ```text
   UE_X = Rhino_X
   UE_Y = -Rhino_Z
   UE_Z = Rhino_Y
   ```

   这样 Rhino 的水平赛道会正确落在 UE 的 XY 地面平面上，不会竖起来。

8. 创建 UE 启动脚本：

   ```text
   Scripts/setup_track_project.py
   ```

9. 第一阶段启动 UE 执行导入脚本，生成 `/Game/Track/TrackMap`。
10. 第二阶段重新正常打开 UE 编辑器，让窗口停留。
11. 设置默认地图为：

   ```text
   /Game/Track/TrackMap
   ```

12. 自动加入太阳光、环境光、天空、大气、轻雾和出生点补光。

## 本地配置文件

可以复制：

```text
config.example.json
```

为：

```text
config.json
```

示例：

```json
{
  "default_map_width": 500,
  "default_map_length": 500,
  "default_track_width": 8,
  "default_smoothing": 0.55,
  "default_sample_spacing": 2,
  "export_directory": "",
  "unreal_editor_path": "<UnrealEditor.exe path>",
  "unreal_project_path": "",
  "unreal_project_directory": "unreal_projects/GeneratedTrackFPS"
}
```

`config.json` 是本地个人配置，不需要提交到 Git。

## 常见问题

### 1. UE 报 DerivedDataCache 不可写

典型错误：

```text
Unable to use default cache graph 'InstalledDerivedDataBackendGraph'
because there are no writable nodes available.
```

工具启动 UE 时已经自动添加：

```text
-DDC-ForceMemoryCache
```

如果仍然报错，检查窗口里的 UnrealEditor 路径是否真的指向当前可用的 UE 安装。

### 2. UE 一打开就消失

旧版本里 `-ExecutePythonScript` 执行完后 UE 会自动退出，看起来像闪退。

现在已经改成两阶段启动：

1. 先执行导入脚本；
2. 再正常打开 UE 编辑器。

如果仍然退出，请查看：

```text
<repo-root>/unreal_projects/GeneratedTrackFPS/Saved/Logs/GeneratedTrackFPS.log
```

### 3. 地图竖起来了

这是 Rhino 和 UE 坐标轴不一致导致的。工具复制 OBJ 到 UE 项目时已经自动转换：

```text
Rhino X/Z 平面 → UE X/Y 平面
Rhino Y 高度 → UE Z 高度
```

如果你打开的是旧项目，需要重新在 Rhino 里点击“打开 Unreal Engine”，让工具重建 UE 项目并重新导入模型。

### 4. 跑道和绿色背景穿模或闪烁

旧版本里路面和地形太近，甚至路面厚度会插入地形。

现在默认高度已经分层：

```text
Terrain = -0.25
Road top = 0.45
Road bottom = 0.15
Curb top = 0.53
```

重新生成模型并重新打开 UE 项目即可。

### 5. `project directory already exists and was not created by this tool`

这是为了防止误删已有 UE 项目的保护。

现在工具允许重建以下目录：

- 有 `.track_generator_project` 标记；
- 有 `GeneratedTrackFPS.uproject`；
- 有 `TP_FirstPersonBP.uproject`；
- 有工具生成的 `TrackSource` 和 `Scripts`。

如果你选了真正陌生的目录，工具会拒绝覆盖。建议使用默认：

```text
<repo-root>/unreal_projects/GeneratedTrackFPS
```

### 6. 图片识别失败

可以尝试：

- 提高或降低“颜色容差”；
- 使用“手动选择线条颜色”；
- 换一张线条和背景对比更明显的图片；
- 去掉图片里的多余线条、文字、阴影、背景纹理。

### 7. 生成失败提示路径自交或极端折返

说明路径本身太复杂，或者折返太极端。可以尝试：

- 提高路径美化强度；
- 增大采样间距；
- 降低赛道宽度；
- 重画一条更平滑的路径；
- 避免 180 度急折返和自交。

## 自动测试

在仓库根目录运行：

```powershell
python -m pytest -q
python -m compileall -q .
```

测试内容包括：

- 路径清理；
- 等距重采样；
- Chaikin 平滑；
- 图片路径提取；
- 仓库 `images/` 样本；
- 直线、圆形、S 形、抖动路径、90 度折线、极端折返；
- 赛道 Mesh；
- 红白路肩 Mesh；
- 地形和高度分层；
- Rhino → UE 坐标轴转换；
- UE 第一人称项目创建；
- UE 启动参数。

如果本机安装 Rhino 8，也可以运行 Rhino 内部 smoke 测试：

```powershell
& "<RhinoCode.exe path>" script "<repo-root>\tests\rhino_ui_smoke.py"
Get-Content .\rhino_ui_smoke_result.txt
```

注意：这个 smoke 测试需要 Rhino 可被 `RhinoCode.exe` 找到；如果没有运行中的 Rhino 实例，可能会提示找不到目标 Rhino。

## Git 分支约定

当前开发在 `dev` 分支进行。

远端仓库：

```text
git@github.com:shujing-CN/track-generator.git
```

## 已知限制

- 当前只支持单条主要连续路径。
- 多条线、大量分叉、严重自交、复杂遮挡图片仍可能失败。
- 自动图片识别基于颜色和骨架路径，不是语义识别。
- UE 项目创建依赖 UE 自带 `TP_FirstPersonBP` 模板。
- 自动生成的是基础地图和第一人称项目，不包含完整赛车玩法、车辆物理、计时系统或 AI 车手。
