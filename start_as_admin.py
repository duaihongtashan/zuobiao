#!/usr/bin/env python3
"""
以管理员身份启动截图工具
"""

import sys
import subprocess
import ctypes
import os

def is_admin():
    """检查是否以管理员身份运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin(script_path):
    """以管理员身份运行脚本"""
    try:
        # 使用PowerShell以管理员身份运行
        cmd = f'Start-Process python -ArgumentList "{script_path}" -Verb RunAs'
        subprocess.run(['powershell', '-Command', cmd], check=True)
        return True
    except Exception as e:
        print(f"以管理员身份启动失败: {e}")
        return False

def main():
    print("🔐 管理员权限启动器")
    print("=" * 40)
    
    if is_admin():
        print("✅ 已经以管理员身份运行")
        
        # 询问要启动哪个程序
        print("\n选择要启动的程序:")
        print("1. 截图工具 (main.py)")
        print("2. 快捷键诊断 (hotkey_diagnostic.py)")
        print("3. 快捷键测试 (hotkey_test.py)")
        
        try:
            choice = input("请输入选择 (1-3): ").strip()
            
            if choice == "1":
                script = "main.py"
            elif choice == "2":
                script = "hotkey_diagnostic.py"
            elif choice == "3":
                script = "hotkey_test.py"
            else:
                print("❌ 无效选择")
                return
            
            print(f"🚀 启动 {script}...")
            
            # 检查脚本是否存在
            if not os.path.exists(script):
                print(f"❌ 文件不存在: {script}")
                return
            
            # 直接运行
            subprocess.run([sys.executable, script])
            
        except KeyboardInterrupt:
            print("\n🛑 用户取消")
        except Exception as e:
            print(f"❌ 启动失败: {e}")
            
    else:
        print("⚠️ 当前未以管理员身份运行")
        print("💡 正在尝试以管理员身份重新启动...")
        
        # 获取当前脚本路径
        current_script = os.path.abspath(__file__)
        
        if run_as_admin(current_script):
            print("✅ 已请求管理员权限，请在弹出的UAC对话框中选择'是'")
        else:
            print("❌ 无法获取管理员权限")
            print("💡 请手动以管理员身份运行PowerShell，然后执行程序")

if __name__ == "__main__":
    main() 