#!/usr/bin/env python3
"""
截图工具 - 智能启动器
自动检测环境并选择合适的运行模式
"""

import sys
import os
from pathlib import Path

def check_gui_environment():
    """检查GUI环境是否可用"""
    try:
        import tkinter as tk
        # 尝试创建一个隐藏的测试窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏窗口
        root.destroy()
        return True
    except Exception:
        return False

def check_display():
    """检查显示环境"""
    return os.environ.get('DISPLAY') is not None

def show_environment_info():
    """显示环境信息"""
    print("截图工具 - 环境检测")
    print("="*30)
    print(f"Python版本: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print(f"操作系统: {os.name}")
    print(f"DISPLAY环境: {os.environ.get('DISPLAY', '未设置')}")
    
    has_display = check_display()
    has_gui = check_gui_environment()
    
    print(f"显示环境: {'✅' if has_display else '❌'}")
    print(f"GUI支持: {'✅' if has_gui else '❌'}")
    print()
    
    return has_gui

def run_gui_mode():
    """运行GUI模式"""
    print("🖥️ 启动GUI模式...")
    try:
        # 添加项目路径
        sys.path.insert(0, str(Path(__file__).parent))
        
        from main import main
        return main()
    except Exception as e:
        print(f"❌ GUI模式启动失败: {e}")
        return False

def run_core_test():
    """运行核心功能测试"""
    print("🔧 启动核心功能测试模式...")
    try:
        # 添加项目路径
        sys.path.insert(0, str(Path(__file__).parent))
        
        from safe_test import main
        main()
        return True
    except Exception as e:
        print(f"❌ 核心功能测试失败: {e}")
        return False

def show_installation_guide():
    """显示安装指南"""
    print("\n" + "="*50)
    print("📖 GUI环境安装指南")
    print("="*50)
    print("在Ubuntu/Debian系统上：")
    print("  sudo apt-get update")
    print("  sudo apt-get install python3-tk python3-dev")
    print()
    print("在WSL中使用GUI：")
    print("  1. 安装X服务器 (如VcXsrv, XLaunch)")
    print("  2. 设置DISPLAY环境变量: export DISPLAY=:0.0")
    print("  3. 安装tkinter包 (如上)")
    print()
    print("在其他Linux发行版：")
    print("  # CentOS/RHEL:")
    print("  sudo yum install tkinter")
    print("  # Arch Linux:")
    print("  sudo pacman -S tk")
    print("="*50)

def main():
    """主启动函数"""
    print("🚀 截图工具 - Jietu")
    print("🔍 正在检测运行环境...")
    print()
    
    # 检测环境
    has_gui = show_environment_info()
    
    if has_gui:
        # 尝试运行GUI模式
        print("✅ GUI环境可用，启动完整模式")
        success = run_gui_mode()
        
        if not success:
            print("\n⚠️ GUI模式启动失败，尝试核心功能测试...")
            run_core_test()
    else:
        # 运行核心功能测试
        print("❌ GUI环境不可用，启动核心功能测试模式")
        run_core_test()
        
        # 显示安装指南
        show_installation_guide()
        
        print("\n💡 安装GUI支持后，可享受完整功能：")
        print("   - 图形化界面配置")
        print("   - 实时截图预览")
        print("   - 全局快捷键支持")
        print("   - 连续截图功能")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 用户取消操作")
    except Exception as e:
        print(f"\n❌ 程序运行出错: {e}")
        sys.exit(1)