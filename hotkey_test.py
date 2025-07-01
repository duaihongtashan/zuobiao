#!/usr/bin/env python3
"""
快捷键自定义功能测试程序
"""

import sys
import time
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from core.hotkey import hotkey_manager, start_hotkey_service, stop_hotkey_service, validate_hotkey_string
from core.config import config_manager

def test_hotkey_validation():
    """测试快捷键验证功能"""
    print("🔧 测试快捷键验证功能...")
    
    test_cases = [
        ("ctrl+shift+s", True, "标准快捷键"),
        ("ctrl+alt+f1", True, "功能键快捷键"),
        ("alt+tab", True, "简单组合键"),
        ("shift+a", True, "字母键"),
        ("ctrl+shift+ctrl", False, "重复修饰键"),
        ("s", False, "缺少修饰键"),
        ("ctrl+", False, "缺少主键"),
        ("invalid+key", False, "无效键名"),
        ("ctrl+shift+space", True, "空格键"),
        ("win+r", True, "Windows键")
    ]
    
    for hotkey, expected, description in test_cases:
        is_valid, message = hotkey_manager.validate_hotkey_with_details(hotkey)
        status = "✅" if is_valid == expected else "❌"
        print(f"  {status} {hotkey} - {description}")
        if not is_valid and expected:
            print(f"      错误: {message}")

def test_custom_hotkeys():
    """测试自定义快捷键注册"""
    print("\n⌨️ 测试自定义快捷键注册...")
    
    # 定义测试回调
    def test_callback_1():
        print("🔥 测试快捷键1被触发！")
    
    def test_callback_2():
        print("🔥 测试快捷键2被触发！")
    
    # 注册测试快捷键
    hotkey_manager.register_hotkey("ctrl+shift+f1", test_callback_1, "测试快捷键1")
    hotkey_manager.register_hotkey("ctrl+shift+f2", test_callback_2, "测试快捷键2")
    
    print("  ✅ 已注册测试快捷键:")
    print("    Ctrl+Shift+F1 - 测试快捷键1")
    print("    Ctrl+Shift+F2 - 测试快捷键2")
    
    # 显示已注册的快捷键
    registered = hotkey_manager.get_registered_hotkeys()
    print(f"  ✅ 当前已注册 {len(registered)} 个快捷键")

def test_hotkey_conflicts():
    """测试快捷键冲突检测"""
    print("\n⚠️ 测试快捷键冲突检测...")
    
    # 测试冲突检测
    test_hotkeys = [
        "ctrl+shift+s",
        "ctrl+shift+c", 
        "ctrl+shift+s",  # 重复
        "alt+f4"
    ]
    
    conflicts = hotkey_manager.get_hotkey_conflicts(test_hotkeys)
    if conflicts:
        print(f"  ❌ 发现冲突的快捷键: {conflicts}")
    else:
        print("  ✅ 没有发现快捷键冲突")

def interactive_test():
    """交互式测试"""
    print("\n🎮 交互式快捷键测试")
    print("=" * 50)
    
    while True:
        print("\n选择操作:")
        print("1. 验证快捷键格式")
        print("2. 启动快捷键监听(测试)")
        print("3. 停止快捷键监听")
        print("4. 显示当前配置")
        print("5. 测试自定义快捷键")
        print("0. 退出")
        
        choice = input("请输入选项 (0-5): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            print("\n" + "="*50)
            print("快捷键格式验证")
            print("="*50)
            print(hotkey_manager.get_hotkey_format_help())
            
            while True:
                hotkey = input("\n请输入要验证的快捷键 (输入 'back' 返回主菜单): ").strip()
                if hotkey.lower() == 'back':
                    break
                    
                if not hotkey:
                    print("❌ 请输入快捷键")
                    continue
                
                is_valid, message = hotkey_manager.validate_hotkey_with_details(hotkey)
                if is_valid:
                    print(f"✅ 快捷键 '{hotkey}' 格式正确")
                    print(f"   {message}")
                else:
                    print(f"❌ 快捷键 '{hotkey}' 格式错误")
                    print(f"   错误: {message}")
                    print("   💡 请参考上方的格式说明")
        
        elif choice == "2":
            print("启动快捷键监听...")
            if start_hotkey_service():
                print("✅ 快捷键服务已启动")
                print("📌 测试说明:")
                print("  - 按 Ctrl+Shift+F1 测试快捷键1")
                print("  - 按 Ctrl+Shift+F2 测试快捷键2")
                print("  - 按 Ctrl+C 停止监听")
                
                try:
                    while hotkey_manager.is_listening():
                        time.sleep(0.1)
                except KeyboardInterrupt:
                    print("\n⏹️ 用户中断")
                    stop_hotkey_service()
            else:
                print("❌ 快捷键服务启动失败")
        
        elif choice == "3":
            stop_hotkey_service()
            print("⏹️ 快捷键监听已停止")
        
        elif choice == "4":
            print("\n📋 当前快捷键配置:")
            single_key = config_manager.get_hotkey("single_capture") or "ctrl+shift+s"
            continuous_key = config_manager.get_hotkey("start_continuous") or "ctrl+shift+c"
            stop_key = config_manager.get_hotkey("stop_continuous") or "ctrl+shift+x"
            
            print(f"  单次截图: {single_key}")
            print(f"  连续截图: {continuous_key}")
            print(f"  停止截图: {stop_key}")
            
            registered = hotkey_manager.get_registered_hotkeys()
            print(f"\n📊 已注册快捷键数量: {len(registered)}")
            for hotkey, config in registered.items():
                print(f"  - {hotkey}: {config.get('description', '无描述')}")
        
        elif choice == "5":
            print("\n🔧 设置自定义快捷键")
            print("="*50)
            print("当前配置:")
            current_single = config_manager.get_hotkey('single_capture') or 'ctrl+shift+s'
            current_continuous = config_manager.get_hotkey('start_continuous') or 'ctrl+shift+c'
            current_stop = config_manager.get_hotkey('stop_continuous') or 'ctrl+shift+x'
            
            print(f"  单次截图: {current_single}")
            print(f"  连续截图: {current_continuous}")
            print(f"  停止截图: {current_stop}")
            print("\n" + "="*30)
            
            single = input(f"新的单次截图快捷键 (直接回车保持不变): ").strip()
            continuous = input(f"新的连续截图快捷键 (直接回车保持不变): ").strip()
            stop = input(f"新的停止截图快捷键 (直接回车保持不变): ").strip()
            
            # 使用当前值如果用户没有输入
            if not single:
                single = current_single
            if not continuous:
                continuous = current_continuous
            if not stop:
                stop = current_stop
            
            # 验证并保存
            all_valid = True
            errors = []
            
            is_valid, message = hotkey_manager.validate_hotkey_with_details(single)
            if not is_valid:
                errors.append(f"单次截图快捷键: {message}")
                all_valid = False
                
            is_valid, message = hotkey_manager.validate_hotkey_with_details(continuous)
            if not is_valid:
                errors.append(f"连续截图快捷键: {message}")
                all_valid = False
                
            is_valid, message = hotkey_manager.validate_hotkey_with_details(stop)
            if not is_valid:
                errors.append(f"停止截图快捷键: {message}")
                all_valid = False
            
            # 检查重复
            hotkeys = [single.lower(), continuous.lower(), stop.lower()]
            if len(set(hotkeys)) != len(hotkeys):
                errors.append("快捷键不能重复")
                all_valid = False
            
            if all_valid:
                config_manager.set_hotkey("single_capture", single.lower())
                config_manager.set_hotkey("start_continuous", continuous.lower())
                config_manager.set_hotkey("stop_continuous", stop.lower())
                
                config_manager.save_config()
                print("\n✅ 自定义快捷键已保存到配置!")
                print("新的快捷键配置:")
                print(f"  单次截图: {single.lower()}")
                print(f"  连续截图: {continuous.lower()}")
                print(f"  停止截图: {stop.lower()}")
            else:
                print("\n❌ 快捷键设置失败，发现以下错误:")
                for error in errors:
                    print(f"   • {error}")
                print("\n💡 请检查快捷键格式并重试")

def main():
    """主函数"""
    print("快捷键自定义功能测试程序")
    print("=" * 50)
    
    # 基础测试
    test_hotkey_validation()
    test_custom_hotkeys()
    test_hotkey_conflicts()
    
    # 交互式测试
    print("\n" + "=" * 50)
    try:
        interactive_test()
    except KeyboardInterrupt:
        print("\n👋 程序被中断")
    finally:
        # 清理
        stop_hotkey_service()
        print("\n🧹 清理完成，程序退出")

if __name__ == "__main__":
    main() 