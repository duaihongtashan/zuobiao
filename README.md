# 截图工具 - Jietu

一个功能丰富的屏幕截图工具，支持自定义区域截图、连续截图和全局快捷键。

## 功能特性

- ✅ **自定义截图区域**: 可以设置任意坐标范围进行截图
- ✅ **两种截图模式**: 单次截图和连续截图（可设置间隔时间）
- ✅ **图形化界面**: 简洁易用的GUI界面，支持各种设置配置
- ✅ **全局快捷键**: 无需切换到程序窗口即可快速截图
- ✅ **智能文件管理**: 自动命名、计数器管理、按序号保存
- ✅ **配置持久化**: 保存用户偏好设置，下次启动自动加载

## 系统要求

- Python 3.12+
- Linux/Windows/macOS

## 安装与使用

1. **安装依赖**:
   ```bash
   uv add Pillow pynput pyautogui
   ```

2. **智能启动** (推荐):
   ```bash
   python jietu.py
   ```
   自动检测环境并选择合适的运行模式

3. **在图形化环境中启动完整程序**:
   ```bash
   python main.py
   ```

4. **在无GUI环境中测试核心功能**:
   ```bash
   python safe_test.py
   ```

5. **在WSL/Linux环境中安装GUI支持** (如需要):
   ```bash
   sudo apt-get update
   sudo apt-get install python3-tk python3-dev
   ```

## 默认设置

- **默认截图区域**: (1750, 60) 到 (1860, 160)
- **默认保存目录**: ./screenshots/
- **默认连续截图间隔**: 1.0秒

## 快捷键

- `Ctrl+Shift+S`: 单次截图
- `Ctrl+Shift+C`: 开始连续截图
- `Ctrl+Shift+X`: 停止连续截图

## GUI界面说明

### 截图区域设置
- **左上角坐标**: 设置截图区域的起始点 (X1, Y1)
- **右下角坐标**: 设置截图区域的结束点 (X2, Y2)
- **应用区域**: 点击应用新的截图区域设置

### 保存设置
- **保存目录**: 选择截图文件的保存位置
- **浏览**: 打开文件夹选择对话框

### 连续截图设置
- **间隔时间**: 设置连续截图的时间间隔（0.1-60秒）

### 控制按钮
- **单次截图**: 立即进行一次截图
- **开始/停止连续截图**: 控制连续截图的开始和停止
- **保存设置**: 将当前配置保存到文件
- **打开目录**: 打开截图保存目录

## 运行方式说明

### 🚀 智能启动 (推荐)
```bash
python jietu.py
```
- 自动检测GUI环境
- 智能选择运行模式
- 提供安装指导和环境信息

### 🖥️ 图形化环境
```bash
python main.py
```
- 完整GUI界面
- 全局快捷键支持
- 所有功能可用

### 🔧 安全测试模式
```bash
python safe_test.py
```
- 测试核心功能
- 配置文件管理
- 文件命名系统验证
- 无GUI依赖，安全可靠

## 文件结构

```
jietu/
├── jietu.py             # 智能启动器 (推荐)
├── main.py              # GUI程序入口
├── safe_test.py         # 安全测试模式
├── test_gui.py          # GUI环境测试
├── gui/                 # GUI界面模块
│   ├── __init__.py
│   └── main_window.py   # 主窗口界面
├── core/                # 核心功能模块
│   ├── __init__.py
│   ├── screenshot.py    # 截图功能
│   ├── config.py        # 配置管理
│   └── hotkey.py        # 快捷键管理
├── utils/               # 工具模块
│   ├── __init__.py
│   └── file_manager.py  # 文件管理
├── config.json          # 配置文件 (自动生成)
├── screenshot_counter.txt # 计数器文件 (自动生成)
└── screenshots/         # 默认截图保存目录 (自动创建)
```

## 配置文件

程序会自动生成 `config.json` 配置文件，包含以下设置：

```json
{
  "screenshot": {
    "default_region": [1750, 60, 1860, 160],
    "custom_region": [1750, 60, 1860, 160],
    "save_directory": "screenshots",
    "continuous_interval": 1.5
  },
  "hotkeys": {
    "single_capture": "ctrl+shift+s",
    "start_continuous": "ctrl+shift+c", 
    "stop_continuous": "ctrl+shift+x"
  },
  "ui": {
    "window_position": [100, 100],
    "window_size": [400, 300],
    "always_on_top": false
  }
}
```

## 环境兼容性

| 环境 | GUI功能 | 核心功能 | 推荐启动方式 |
|------|---------|----------|--------------|
| Windows桌面 | ✅ | ✅ | `python main.py` |
| macOS桌面 | ✅ | ✅ | `python main.py` |
| Linux桌面 | ✅ | ✅ | `python main.py` |
| WSL | ❌ | ✅ | `python minimal_test.py` |
| SSH远程 | ❌ | ✅ | `python minimal_test.py` |
| 服务器 | ❌ | ✅ | `python minimal_test.py` |

## 注意事项

1. **权限要求**: 程序需要屏幕访问权限和键盘监听权限
2. **快捷键冲突**: 如果快捷键与其他程序冲突，请在GUI中修改设置
3. **文件命名**: 截图文件按照 `screenshot_序号_时间戳.png` 格式命名
4. **跨平台兼容**: 程序支持Windows、macOS和Linux系统
5. **WSL限制**: 在WSL环境中无法使用GUI功能，但配置和文件管理功能正常

## 故障排除

### 问题：程序无法启动
**解决方案**:
- 确保已安装所有依赖包: `uv add Pillow pynput pyautogui`
- 在Linux环境安装tkinter: `sudo apt-get install python3-tk python3-dev`

### 问题：快捷键不工作
**解决方案**:
- 检查是否被其他程序占用
- 确认有键盘监听权限
- 在macOS中需要允许辅助功能访问

### 问题：截图失败
**解决方案**:
- 检查截图区域坐标是否超出屏幕范围
- 确认有屏幕录制权限
- 检查显示环境是否正常

### 问题：保存失败
**解决方案**:
- 确保保存目录有写入权限
- 检查磁盘空间是否充足

## 开发者信息

这是一个基于Python开发的开源截图工具，使用了以下主要库：
- `tkinter`: GUI界面
- `Pillow`: 图像处理
- `pynput`: 全局快捷键监听
- `pyautogui`: 屏幕截图

项目结构清晰，模块化设计，易于扩展和维护。