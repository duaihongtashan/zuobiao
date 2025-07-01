#!/usr/bin/env python3
"""
简单的GUI测试
"""

import sys

def test_tkinter():
    """测试tkinter是否可用"""
    try:
        print("测试tkinter导入...")
        import tkinter as tk
        print("✅ tkinter导入成功")
        
        print("创建测试窗口...")
        root = tk.Tk()
        root.title("GUI测试")
        root.geometry("200x100")
        
        label = tk.Label(root, text="GUI测试成功!")
        label.pack(pady=20)
        
        button = tk.Button(root, text="关闭", command=root.quit)
        button.pack()
        
        print("✅ 窗口创建成功，显示3秒后自动关闭...")
        
        # 3秒后自动关闭
        root.after(3000, root.quit)
        root.mainloop()
        
        print("✅ GUI测试完成")
        return True
        
    except Exception as e:
        print(f"❌ GUI测试失败: {e}")
        return False

def main():
    print("GUI环境测试")
    print("="*20)
    
    if test_tkinter():
        print("\n🎉 GUI环境正常，可以运行完整程序")
    else:
        print("\n❌ GUI环境不可用")
        print("解决方案:")
        print("1. 确保XLaunch正在运行")
        print("2. 检查DISPLAY环境变量: export DISPLAY=:0.0")
        print("3. 安装tkinter: sudo apt-get install python3-tk python3-dev")

if __name__ == "__main__":
    main()