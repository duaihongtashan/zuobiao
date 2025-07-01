#!/usr/bin/env python3
"""
Windows系统专用启动脚本
针对Windows系统优化的截图工具启动器
"""

import sys
import os
import platform
import subprocess
from pathlib import Path

def check_windows_environment():
    """检查Windows环境"""
    print("🔍 检查Windows环境...")
    
    # 检查操作系统
    if platform.system() != 'Windows':
        print("❌ 当前不是Windows系统")
        return False
    
    print(f"✅ Windows系统版本: {platform.platform()}")
    print(f"✅ Python版本: {sys.version}")
    
    # 检查屏幕分辨率
    try:
        import tkinter as tk
        root = tk.Tk()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.destroy()
        print(f"✅ 屏幕分辨率: {screen_width}x{screen_height}")
    except Exception as e:
        print(f"⚠️ 无法获取屏幕信息: {e}")
    
    return True

def check_dependencies():
    """检查依赖包"""
    print("\n📦 检查依赖包...")
    
    required_packages = {
        'tkinter': '图形界面',
        'PIL': '图像处理',
        'pyautogui': '自动化截图',
        'pynput': '全局快捷键',
    }
    
    missing_packages = []
    
    for package, description in required_packages.items():
        try:
            if package == 'tkinter':
                import tkinter
            elif package == 'PIL':
                from PIL import Image
            elif package == 'pyautogui':
                import pyautogui
            elif package == 'pynput':
                import pynput
            
            print(f"  ✅ {package} - {description}")
        except ImportError:
            print(f"  ❌ {package} - {description} (缺失)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ 缺失依赖包: {', '.join(missing_packages)}")
        print("请运行: uv sync")
        return False
    
    return True

def optimize_windows_settings():
    """优化Windows系统设置"""
    print("\n⚙️ 应用Windows优化设置...")
    
    try:
        import pyautogui
        
        # Windows特定优化
        pyautogui.FAILSAFE = False  # 禁用故障保护
        pyautogui.PAUSE = 0.1       # 设置操作间隔
        
        print("  ✅ PyAutoGUI Windows优化已应用")
        
        # 检查UAC和权限
        if os.name == 'nt':
            try:
                # 尝试检查是否有管理员权限
                import ctypes
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
                if is_admin:
                    print("  ✅ 检测到管理员权限")
                else:
                    print("  ℹ️ 非管理员权限运行")
            except:
                pass
        
        return True
        
    except Exception as e:
        print(f"  ⚠️ 优化设置失败: {e}")
        return False

def create_windows_shortcuts():
    """创建Windows桌面快捷方式"""
    print("\n🔗 Windows快捷方式...")
    
    try:
        desktop = Path.home() / "Desktop"
        if desktop.exists():
            print(f"  ℹ️ 可手动创建桌面快捷方式到: {desktop}")
        
        # 显示常用路径
        current_dir = Path.cwd()
        print(f"  📂 程序路径: {current_dir}")
        print(f"  📂 配置文件: {current_dir / 'config.json'}")
        print(f"  📂 截图目录: {current_dir / 'screenshots'}")
        
        return True
        
    except Exception as e:
        print(f"  ⚠️ 快捷方式创建失败: {e}")
        return False

def show_windows_tips():
    """显示Windows使用提示"""
    print("\n💡 Windows使用提示:")
    print("  🎯 快捷键:")
    print("     Ctrl+Shift+S - 单次截图")
    print("     Ctrl+Shift+C - 开始连续截图")
    print("     Ctrl+Shift+X - 停止连续截图")
    print("\n  🔧 Windows特性:")
    print("     - 自动检测屏幕分辨率")
    print("     - 优化的截图性能")
    print("     - 原生文件浏览器集成")
    print("     - Windows通知支持")
    print("\n  📁 文件管理:")
    print("     - 截图自动保存到 screenshots/ 目录")
    print("     - 支持自定义保存路径")
    print("     - 一键打开文件夹")

def start_application():
    """启动主应用程序"""
    print("\n🚀 启动截图工具...")
    
    try:
        # 导入主程序
        from main import JietuApplication
        
        # 创建应用实例
        app = JietuApplication()
        
        # 运行应用
        print("✅ 截图工具已启动 (Windows优化版)")
        app.run()
        
        return True
        
    except KeyboardInterrupt:
        print("\n👋 用户中断程序")
        return False
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        print("\n🔧 故障排除:")
        print("  1. 检查依赖: uv sync")
        print("  2. 重新安装: uv add pyautogui pillow pynput")
        print("  3. 检查Python版本: python --version")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🖼️  截图工具 - Windows版启动器")
    print("=" * 60)
    
    # 检查环境
    if not check_windows_environment():
        input("\n按回车键退出...")
        sys.exit(1)
    
    # 检查依赖
    if not check_dependencies():
        input("\n按回车键退出...")
        sys.exit(1)
    
    # 优化设置
    optimize_windows_settings()
    
    # 创建快捷方式
    create_windows_shortcuts()
    
    # 显示提示
    show_windows_tips()
    
    # 启动应用
    if not start_application():
        input("\n按回车键退出...")
        sys.exit(1)

if __name__ == "__main__":
    main() 