#!/usr/bin/env python3
"""
Jietu 截图工具 - Windows优化版主启动文件
"""

import os
import sys
import platform
from pathlib import Path
import tempfile

# 确保项目根目录在Python路径中
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def setup_windows_environment():
    """设置Windows特定的环境"""
    if platform.system() != "Windows":
        return
    
    # 设置DPI感知
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass
    
    # 设置控制台编码
    try:
        os.system('chcp 65001 >nul 2>&1')  # UTF-8编码
    except:
        pass
    
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def check_dependencies():
    """检查关键依赖"""
    missing_deps = []
    
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")
    
    try:
        import cv2
    except ImportError:
        missing_deps.append("opencv-python")
    
    try:
        import PIL
    except ImportError:
        missing_deps.append("Pillow")
    
    try:
        import tkinter
    except ImportError:
        missing_deps.append("tkinter")
    
    if missing_deps:
        print("❌ 缺少以下依赖:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\n请运行 windows_install.py 安装依赖")
        input("按回车键退出...")
        return False
    
    return True

def main():
    """主函数"""
    print("🚀 启动 Jietu 截图工具...")
    
    # 设置Windows环境
    setup_windows_environment()
    
    # 检查依赖
    if not check_dependencies():
        return
    
    try:
        # 导入并启动主程序
        from gui.main_window import MainWindow
        
        # 创建必要的目录
        screenshots_dir = Path.home() / "Pictures" / "Jietu_Screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        # 启动GUI
        app = MainWindow()
        app.root.mainloop()
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保所有文件都在正确的位置")
        input("按回车键退出...")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")

if __name__ == "__main__":
    main()
