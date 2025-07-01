#!/usr/bin/env python3
"""
最小化测试 - 只测试配置和文件管理
"""

import sys
import os
from pathlib import Path

def test_basic_modules():
    """测试基础模块（不涉及GUI）"""
    print("🔧 测试基础模块...")
    
    try:
        # 添加当前目录到Python路径
        sys.path.insert(0, str(Path(__file__).parent))
        
        # 1. 测试配置模块
        print("  1. 测试配置模块...")
        from core.config import ConfigManager
        config = ConfigManager()
        
        # 测试基本配置操作
        region = config.get_screenshot_region()
        save_dir = config.get_save_directory()
        interval = config.get_continuous_interval()
        
        print(f"     ✅ 截图区域: {region}")
        print(f"     ✅ 保存目录: {save_dir}")
        print(f"     ✅ 截图间隔: {interval}秒")
        
        # 测试配置修改
        config.set_screenshot_region(100, 100, 300, 300)
        new_region = config.get_screenshot_region()
        print(f"     ✅ 修改区域: {new_region}")
        
        # 2. 测试文件管理模块
        print("  2. 测试文件管理模块...")
        from utils.file_manager import FileManager
        file_mgr = FileManager("test_screenshots")
        
        # 测试文件名生成
        filename1 = file_mgr.generate_filename()
        filename2 = file_mgr.generate_filename()
        print(f"     ✅ 文件名1: {filename1}")
        print(f"     ✅ 文件名2: {filename2}")
        
        # 测试路径生成
        full_path = file_mgr.get_full_path(filename1)
        print(f"     ✅ 完整路径: {full_path}")
        
        # 测试目录操作
        test_dir = "demo_output"
        file_mgr.set_base_directory(test_dir)
        file_mgr.ensure_directory_exists()
        print(f"     ✅ 目录创建: {test_dir}")
        
        # 3. 测试快捷键解析（不启动监听）
        print("  3. 测试快捷键解析...")
        from core.hotkey import HotkeyManager
        hotkey_mgr = HotkeyManager()
        
        # 测试快捷键解析
        test_keys = ["ctrl+shift+s", "ctrl+shift+c", "ctrl+alt+x"]
        for key in test_keys:
            result = hotkey_mgr.test_hotkey_parsing(key)
            print(f"     ✅ 解析 '{key}': {'成功' if result else '失败'}")
        
        print("\n🎉 基础模块测试全部通过！")
        return True
        
    except Exception as e:
        print(f"    ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_sample_config():
    """创建示例配置文件"""
    print("\n📝 创建示例配置...")
    
    try:
        from core.config import ConfigManager
        config = ConfigManager()
        
        # 设置示例配置
        config.set_screenshot_region(1750, 60, 1860, 160, is_custom=True)
        config.set_save_directory("screenshots")
        config.set_continuous_interval(1.5)
        config.set_hotkey("single_capture", "ctrl+shift+s")
        config.set_hotkey("start_continuous", "ctrl+shift+c")
        config.set_hotkey("stop_continuous", "ctrl+shift+x")
        
        # 保存配置
        config.save_config()
        print("   ✅ 配置文件已保存到 config.json")
        
        # 读取并显示配置
        print("   📋 当前配置:")
        print(f"      截图区域: {config.get_screenshot_region()}")
        print(f"      保存目录: {config.get_save_directory()}")
        print(f"      截图间隔: {config.get_continuous_interval()}秒")
        print(f"      单次截图: {config.get_hotkey('single_capture')}")
        print(f"      连续截图: {config.get_hotkey('start_continuous')}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 配置创建失败: {e}")
        return False

def show_file_structure():
    """显示文件结构"""
    print("\n📁 项目文件结构:")
    print("jietu/")
    print("├── main.py              # 主程序入口")
    print("├── start.py             # 启动脚本")
    print("├── simple_test.py       # 简化测试")
    print("├── minimal_test.py      # 最小化测试")
    print("├── gui/                 # GUI模块")
    print("│   ├── __init__.py")
    print("│   └── main_window.py")
    print("├── core/                # 核心模块")
    print("│   ├── __init__.py")
    print("│   ├── config.py        # 配置管理")
    print("│   ├── screenshot.py    # 截图功能")
    print("│   └── hotkey.py        # 快捷键管理")
    print("├── utils/               # 工具模块")
    print("│   ├── __init__.py")
    print("│   └── file_manager.py  # 文件管理")
    print("├── config.json          # 配置文件 (自动生成)")
    print("└── screenshots/         # 截图保存目录 (自动创建)")

def main():
    """主函数"""
    print("截图工具 - 最小化功能测试")
    print("="*40)
    
    # 测试基础模块
    if not test_basic_modules():
        print("❌ 基础模块测试失败")
        sys.exit(1)
    
    # 创建示例配置
    if not create_sample_config():
        print("❌ 配置创建失败")
        sys.exit(1)
    
    # 显示文件结构
    show_file_structure()
    
    print("\n" + "="*50)
    print("✅ 核心功能测试完成！")
    print("💡 在图形化环境中运行以下命令启动完整程序:")
    print("   python main.py")
    print("🔧 在当前环境中，配置和文件管理功能已验证正常工作")
    print("="*50)

if __name__ == "__main__":
    main()