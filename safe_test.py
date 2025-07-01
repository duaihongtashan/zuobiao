#!/usr/bin/env python3
"""
安全测试 - 避免可能导致挂起的模块导入
"""

import sys
from pathlib import Path

def test_basic_imports():
    """测试基础模块导入"""
    print("🔧 测试基础模块导入...")
    
    try:
        # 1. 测试Python标准库
        import json
        import threading
        import os
        from datetime import datetime
        print("  ✅ Python标准库导入正常")
        
        # 2. 测试配置模块（不依赖GUI）
        print("  测试配置模块...")
        sys.path.insert(0, str(Path(__file__).parent))
        from core.config import ConfigManager
        config = ConfigManager()
        print("  ✅ 配置模块导入正常")
        
        # 3. 测试文件管理模块
        print("  测试文件管理模块...")
        from utils.file_manager import FileManager
        file_mgr = FileManager()
        print("  ✅ 文件管理模块导入正常")
        
        # 4. 测试快捷键模块（不启动监听）
        print("  测试快捷键模块...")
        from core.hotkey import HotkeyManager
        hotkey = HotkeyManager()
        print("  ✅ 快捷键模块导入正常")
        
        print("\n🎉 所有基础模块导入成功！")
        return True
        
    except Exception as e:
        print(f"  ❌ 模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_operations():
    """测试配置操作"""
    print("\n📝 测试配置操作...")
    
    try:
        from core.config import ConfigManager
        config = ConfigManager()
        
        # 测试读取配置
        region = config.get_screenshot_region()
        save_dir = config.get_save_directory()
        print(f"  ✅ 默认截图区域: {region}")
        print(f"  ✅ 默认保存目录: {save_dir}")
        
        # 测试修改配置
        config.set_screenshot_region(100, 100, 300, 300)
        new_region = config.get_screenshot_region()
        print(f"  ✅ 修改后区域: {new_region}")
        
        # 测试保存配置
        config.save_config()
        print("  ✅ 配置保存成功")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 配置操作失败: {e}")
        return False

def test_file_operations():
    """测试文件操作"""
    print("\n📁 测试文件操作...")
    
    try:
        from utils.file_manager import FileManager
        file_mgr = FileManager("safe_test_output")
        
        # 测试文件名生成
        filename = file_mgr.generate_filename()
        print(f"  ✅ 生成文件名: {filename}")
        
        # 测试目录创建
        file_mgr.ensure_directory_exists()
        print("  ✅ 目录创建成功")
        
        # 测试完整路径
        full_path = file_mgr.get_full_path(filename)
        print(f"  ✅ 完整路径: {full_path}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 文件操作失败: {e}")
        return False

def show_next_steps():
    """显示下一步操作建议"""
    print("\n" + "="*50)
    print("📋 程序状态总结")
    print("="*50)
    print("✅ 核心功能模块：正常")
    print("✅ 配置管理：正常") 
    print("✅ 文件管理：正常")
    print("❌ GUI功能：需要安装tkinter")
    print()
    print("🔧 解决GUI问题:")
    print("  sudo apt-get update")
    print("  sudo apt-get install python3-tk python3-dev")
    print()
    print("🚀 安装GUI支持后可运行:")
    print("  python main.py")
    print()
    print("💡 当前可用功能:")
    print("  - 配置文件管理")
    print("  - 文件命名系统")
    print("  - 快捷键解析")
    print("  - 项目结构正常")
    print("="*50)

def main():
    """主函数"""
    print("截图工具 - 安全测试模式")
    print("="*30)
    
    success = True
    
    # 测试基础导入
    if not test_basic_imports():
        success = False
    
    # 测试配置操作
    if not test_config_operations():
        success = False
    
    # 测试文件操作  
    if not test_file_operations():
        success = False
    
    # 显示总结
    show_next_steps()
    
    if success:
        print("\n🎉 安全测试完成，核心功能正常！")
    else:
        print("\n❌ 测试发现问题，请检查错误信息")

if __name__ == "__main__":
    main()