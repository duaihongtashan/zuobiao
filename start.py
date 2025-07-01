#!/usr/bin/env python3
"""
截图工具启动脚本
处理环境依赖和启动检查
"""

import sys
import os
import subprocess

def check_tkinter():
    """检查tkinter是否可用"""
    try:
        import tkinter as tk
        return True
    except ImportError:
        return False

def check_display():
    """检查是否有显示环境"""
    return os.environ.get('DISPLAY') is not None

def install_tkinter_instructions():
    """显示tkinter安装说明"""
    print("=" * 50)
    print("❌ 缺少tkinter模块")
    print("=" * 50)
    print("在Ubuntu/Debian系统上，请运行:")
    print("  sudo apt-get update")
    print("  sudo apt-get install python3-tk python3-dev")
    print()
    print("在其他Linux发行版上:")
    print("  # CentOS/RHEL:")
    print("  sudo yum install tkinter")
    print("  # 或")
    print("  sudo dnf install python3-tkinter")
    print()
    print("  # Arch Linux:")
    print("  sudo pacman -S tk")
    print("=" * 50)

def run_non_gui_test():
    """运行非GUI测试"""
    print("🔧 运行核心功能测试...")
    
    try:
        # 测试核心模块（不需要tkinter）
        from core.screenshot import ScreenshotCapture
        from core.config import ConfigManager
        from utils.file_manager import FileManager
        
        print("✅ 核心模块导入成功")
        
        # 测试配置功能
        config = ConfigManager()
        region = config.get_screenshot_region()
        print(f"✅ 配置管理: 截图区域 {region}")
        
        # 测试文件管理
        file_mgr = FileManager("test_output")
        filename = file_mgr.generate_filename()
        print(f"✅ 文件管理: 生成文件名 {filename}")
        
        # 测试截图类初始化
        screenshot = ScreenshotCapture()
        is_valid = screenshot.validate_region(100, 100, 200, 200)
        print(f"✅ 截图功能: 区域验证 {is_valid}")
        
        print("\n🎉 核心功能测试通过！")
        print("💡 提示: 安装tkinter后可使用完整GUI功能")
        
        return True
        
    except Exception as e:
        print(f"❌ 核心功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_gui_mode():
    """运行GUI模式"""
    try:
        print("🚀 启动GUI模式...")
        from main import main
        main()
        return True
    except Exception as e:
        print(f"❌ GUI启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主启动函数"""
    print("截图工具 - Jietu")
    print("=" * 30)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        print(f"   当前版本: {sys.version}")
        sys.exit(1)
    
    print(f"✅ Python版本: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # 检查显示环境
    if not check_display():
        print("⚠️  警告: 未检测到图形显示环境")
        print("   如果您在SSH或无头环境中运行，GUI功能将不可用")
    
    # 检查tkinter
    if not check_tkinter():
        install_tkinter_instructions()
        print("\n⚡ 尝试运行核心功能测试...")
        run_non_gui_test()
        return
    
    print("✅ tkinter模块可用")
    
    # 运行GUI模式
    success = run_gui_mode()
    
    if not success:
        print("\n⚡ GUI启动失败，尝试运行核心功能测试...")
        run_non_gui_test()

if __name__ == "__main__":
    main()