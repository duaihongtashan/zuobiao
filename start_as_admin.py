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
        # sys.executable确保我们用的是同一个python解释器
        cmd = f'Start-Process "{sys.executable}" -ArgumentList '
        cmd += f'"{script_path}" -Verb RunAs'
        subprocess.run(['powershell', '-Command', cmd], check=True, capture_output=True)
        return True
    except Exception as e:
        print(f"以管理员身份启动失败: {e}")
        # 打印更详细的错误
        if hasattr(e, 'stderr') and e.stderr:
            print(f"  错误详情: {e.stderr.decode('gbk', errors='ignore')}")
        return False

def main():
    """主函数"""
    script_to_run = "main.py"
    
    if is_admin():
        print(f"✅ 已经以管理员身份运行，正在启动 {script_to_run}...")
        
        # 检查主脚本是否存在
        if not os.path.exists(script_to_run):
            print(f"❌ 主程序文件不存在: {script_to_run}")
            print("💡 请确保此脚本与main.py在同一目录下")
            input("按回车键退出...")
            return

        try:
            # 直接运行主程序
            subprocess.run([sys.executable, script_to_run])
        except Exception as e:
            print(f"❌ 启动 {script_to_run} 失败: {e}")
            input("按回车键退出...")
            
    else:
        print("⚠️  当前未以管理员身份运行")
        print(f"💡 正在尝试以管理员权限启动 {script_to_run}...")
        
        # 获取当前脚本的绝对路径，以找到main.py
        base_dir = os.path.dirname(os.path.abspath(__file__))
        main_script_path = os.path.join(base_dir, script_to_run)
        
        if not os.path.exists(main_script_path):
             print(f"❌ 主程序文件不存在: {main_script_path}")
             input("按回车键退出...")
             return
        
        if run_as_admin(main_script_path):
            print("✅ 已请求管理员权限，请在弹出的UAC对话框中选择'是'")
            # 父进程在这里退出，新的管理员进程已经启动
            sys.exit(0)
        else:
            print("❌ 无法获取管理员权限。")
            print("💡 请尝试手动右键点击此脚本，选择'以管理员身份运行'。")
            input("按回车键退出...")

if __name__ == "__main__":
    main() 