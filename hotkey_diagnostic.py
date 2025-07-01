#!/usr/bin/env python3
"""
快捷键诊断程序
用于测试键盘监听功能是否正常工作
"""

import sys
import os
import time
import threading
import traceback
from datetime import datetime

try:
    from pynput import keyboard
    from pynput.keyboard import Key, Listener
    print("✅ pynput库导入成功")
except ImportError as e:
    print(f"❌ pynput库导入失败: {e}")
    sys.exit(1)

class KeyboardDiagnostic:
    def __init__(self):
        self.pressed_keys = set()
        self.listener = None
        self.running = False
        self.key_events = []
        
    def on_key_press(self, key):
        """按键按下事件"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        try:
            # 记录按键事件
            key_info = f"[{timestamp}] 按下: {key}"
            print(key_info)
            self.key_events.append(key_info)
            
            self.pressed_keys.add(key)
            
            # 显示当前按下的所有键
            if len(self.pressed_keys) > 1:
                keys_str = ", ".join([str(k) for k in self.pressed_keys])
                combo_info = f"[{timestamp}] 组合键: {keys_str}"
                print(combo_info)
                self.key_events.append(combo_info)
            
            # 检查是否是退出组合键 (Ctrl+Shift+Q)
            if self.check_exit_combination():
                print("\n🛑 检测到退出组合键 (Ctrl+Shift+Q)，程序即将退出...")
                self.stop_listening()
                return False
                
        except Exception as e:
            error_info = f"[{timestamp}] 处理按键事件出错: {e}"
            print(error_info)
            self.key_events.append(error_info)
    
    def on_key_release(self, key):
        """按键释放事件"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        try:
            key_info = f"[{timestamp}] 释放: {key}"
            print(key_info)
            self.key_events.append(key_info)
            
            self.pressed_keys.discard(key)
            
        except Exception as e:
            error_info = f"[{timestamp}] 处理按键释放事件出错: {e}"
            print(error_info)
            self.key_events.append(error_info)
    
    def check_exit_combination(self):
        """检查是否按下了退出组合键"""
        try:
            ctrl_pressed = Key.ctrl_l in self.pressed_keys or Key.ctrl_r in self.pressed_keys
            shift_pressed = Key.shift_l in self.pressed_keys or Key.shift_r in self.pressed_keys
            q_pressed = keyboard.KeyCode.from_char('q') in self.pressed_keys
            
            return ctrl_pressed and shift_pressed and q_pressed
        except Exception as e:
            print(f"检查退出组合键时出错: {e}")
            return False
    
    def start_listening(self):
        """开始监听键盘"""
        if self.running:
            print("⚠️ 监听器已在运行")
            return False
        
        try:
            print("🎯 启动键盘监听器...")
            
            self.listener = Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release,
                suppress=False
            )
            
            self.listener.start()
            self.running = True
            
            print("✅ 键盘监听器启动成功")
            print("📊 监听状态:")
            print(f"   - 监听器运行中: {self.listener.running}")
            print(f"   - 监听器线程存活: {self.listener.is_alive()}")
            
            return True
            
        except Exception as e:
            print(f"❌ 启动键盘监听器失败: {e}")
            print(f"   错误类型: {type(e).__name__}")
            print(f"   错误详情: {traceback.format_exc()}")
            return False
    
    def stop_listening(self):
        """停止监听键盘"""
        if not self.running:
            return
        
        print("\n🛑 停止键盘监听...")
        
        try:
            if self.listener:
                self.listener.stop()
            self.running = False
            print("✅ 键盘监听已停止")
        except Exception as e:
            print(f"❌ 停止监听时出错: {e}")
    
    def print_summary(self):
        """打印事件总结"""
        print(f"\n📈 事件总结:")
        print(f"   - 总计录事件: {len(self.key_events)}")
        print(f"   - 当前按下的键: {len(self.pressed_keys)}")
        
        if self.key_events:
            print("\n📝 最近10个事件:")
            for event in self.key_events[-10:]:
                print(f"   {event}")

def check_permissions():
    """检查是否以管理员身份运行"""
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if is_admin:
            print("✅ 程序以管理员身份运行")
        else:
            print("⚠️ 程序未以管理员身份运行，可能影响键盘监听功能")
            print("💡 建议：右键点击PowerShell，选择'以管理员身份运行'")
        return is_admin
    except Exception as e:
        print(f"⚠️ 无法检查权限状态: {e}")
        return False

def print_system_info():
    """打印系统信息"""
    print("🖥️ 系统信息:")
    print(f"   - Python版本: {sys.version}")
    print(f"   - 平台: {sys.platform}")
    print(f"   - pynput版本: {getattr(keyboard, '__version__', '未知')}")
    
    # 检查键盘相关模块
    try:
        print(f"   - Key类可用: {hasattr(keyboard, 'Key')}")
        print(f"   - Listener类可用: {hasattr(keyboard, 'Listener')}")
        print(f"   - KeyCode类可用: {hasattr(keyboard, 'KeyCode')}")
    except Exception as e:
        print(f"   - 模块检查出错: {e}")

def main():
    print("🔧 快捷键诊断程序")
    print("=" * 50)
    
    # 系统信息检查
    print_system_info()
    print()
    
    # 权限检查
    check_permissions()
    print()
    
    # 创建诊断器
    diagnostic = KeyboardDiagnostic()
    
    try:
        print("🚀 开始键盘监听测试...")
        print("📋 测试说明:")
        print("   1. 程序将监听所有键盘按键")
        print("   2. 按下任意键查看监听效果")
        print("   3. 尝试按下组合键测试")
        print("   4. 按 Ctrl+Shift+Q 退出程序")
        print("   5. 观察控制台输出，确认按键事件被正确捕获")
        print()
        
        # 启动监听
        if not diagnostic.start_listening():
            print("❌ 无法启动键盘监听，程序退出")
            return
        
        print("⏰ 监听已启动，请开始测试...")
        print("   (按 Ctrl+Shift+Q 退出)")
        print("-" * 50)
        
        # 主循环
        start_time = time.time()
        while diagnostic.running:
            time.sleep(0.1)
            
            # 每10秒显示一次状态
            if int(time.time() - start_time) % 10 == 0 and int(time.time() - start_time) > 0:
                elapsed = int(time.time() - start_time)
                print(f"\n⏱️ 已运行 {elapsed} 秒，监听状态正常...")
                start_time = time.time()  # 重置计时器
        
    except KeyboardInterrupt:
        print("\n🛑 用户中断程序")
    except Exception as e:
        print(f"\n❌ 程序运行出错: {e}")
        print(f"错误详情: {traceback.format_exc()}")
    finally:
        # 清理
        diagnostic.stop_listening()
        diagnostic.print_summary()
        
        print("\n🎯 诊断完成")
        print("💡 如果看到按键事件输出，说明键盘监听功能正常")
        print("💡 如果没有看到按键事件，可能需要:")
        print("   1. 以管理员身份运行程序")
        print("   2. 检查杀毒软件设置")
        print("   3. 更新或重新安装pynput库")

if __name__ == "__main__":
    main() 