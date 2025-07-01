#!/usr/bin/env python3
"""
简单的快捷键测试程序
"""

import time
import sys

print("🔧 简单快捷键测试")
print("=" * 30)

try:
    from pynput.keyboard import Listener, Key, KeyCode
    print("✅ pynput导入成功")
except ImportError as e:
    print(f"❌ pynput导入失败: {e}")
    print("💡 请运行: uv add pynput")
    sys.exit(1)

# 全局变量
pressed_keys = set()
test_active = True

def on_press(key):
    """按键按下"""
    global pressed_keys, test_active
    
    pressed_keys.add(key)
    print(f"按下: {key}")
    
    # 检查Ctrl+Q退出
    try:
        ctrl_pressed = Key.ctrl_l in pressed_keys or Key.ctrl_r in pressed_keys
        q_pressed = KeyCode.from_char('q') in pressed_keys
        
        if ctrl_pressed and q_pressed:
            print("检测到 Ctrl+Q，退出测试")
            test_active = False
            return False
    except:
        pass

def on_release(key):
    """按键释放"""
    global pressed_keys
    
    pressed_keys.discard(key)
    print(f"释放: {key}")

def main():
    global test_active
    
    print("🚀 开始键盘监听测试")
    print("按任意键测试，按 Ctrl+Q 退出")
    print("-" * 30)
    
    try:
        # 创建监听器
        listener = Listener(
            on_press=on_press,
            on_release=on_release,
            suppress=False
        )
        
        # 启动监听
        listener.start()
        print("✅ 监听器已启动")
        
        # 等待用户操作
        while test_active and listener.running:
            time.sleep(0.1)
        
        # 停止监听
        listener.stop()
        print("🛑 监听器已停止")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 