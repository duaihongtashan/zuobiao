"""
截图工具 - Jietu
功能：
- 截取屏幕指定区域
- 支持自定义截图区域
- 单次截图和连续截图
- GUI界面配置
- 全局快捷键支持
"""

import sys
import signal
import threading

# 全局变量用于GUI模块
tk = None
messagebox = None
create_main_window = None

def _import_gui_modules():
    """延迟导入GUI模块"""
    global tk, messagebox, create_main_window
    try:
        import tkinter as _tk
        from tkinter import messagebox as _messagebox
        from gui.main_window import create_main_window as _create_main_window
        
        tk = _tk
        messagebox = _messagebox
        create_main_window = _create_main_window
        return True
    except ImportError as e:
        print(f"警告: GUI模块导入失败 - {e}")
        print("这通常发生在WSL或无图形环境中")
        print("请尝试运行: python minimal_test.py")
        return False

# 导入非GUI模块
from core.screenshot import screenshot_manager
from core.config import config_manager
from core.hotkey import hotkey_manager, register_screenshot_hotkeys, start_hotkey_service, stop_hotkey_service
from utils.file_manager import file_manager


class JietuApplication:
    """截图应用程序主类"""
    
    def __init__(self):
        self.main_window = None
        self.hotkey_initialized = False
        self.gui_available = False
        
    def initialize_hotkeys(self, main_window):
        """初始化快捷键 - 支持自定义配置"""
        if self.hotkey_initialized:
            return
            
        try:
            # 从配置加载快捷键设置
            single_key = config_manager.get_hotkey("single_capture") or "ctrl+shift+s"
            continuous_key = config_manager.get_hotkey("start_continuous") or "ctrl+shift+c"
            stop_key = config_manager.get_hotkey("stop_continuous") or "ctrl+shift+x"
            
            # 定义快捷键回调函数
            def single_screenshot():
                """单次截图回调"""
                try:
                    saved_path = screenshot_manager.capture_single()
                    if saved_path and main_window:
                        # 更新GUI状态（线程安全）
                        main_window.root.after(0, 
                            lambda: main_window.update_status(f"快捷键截图: {saved_path.split('/')[-1]}"))
                        main_window.root.after(0, main_window.update_file_count)
                except Exception as e:
                    print(f"快捷键截图失败: {e}")
            
            def start_continuous_screenshot():
                """开始连续截图回调"""
                try:
                    if not screenshot_manager.is_continuous_capturing():
                        def on_capture(saved_path):
                            if main_window:
                                main_window.root.after(0, 
                                    lambda: main_window.update_status(f"连续截图: {saved_path.split('/')[-1]}"))
                                main_window.root.after(0, main_window.update_file_count)
                        
                        screenshot_manager.start_continuous_capture(on_capture)
                        if main_window:
                            main_window.root.after(0, 
                                lambda: main_window.update_status("快捷键启动连续截图"))
                            # 更新GUI按钮状态
                            main_window.root.after(0, 
                                lambda: setattr(main_window, 'is_continuous_capturing', True))
                            main_window.root.after(0, 
                                lambda: main_window.continuous_btn.config(text="停止连续截图"))
                except Exception as e:
                    print(f"快捷键启动连续截图失败: {e}")
            
            def stop_continuous_screenshot():
                """停止连续截图回调"""
                try:
                    if screenshot_manager.is_continuous_capturing():
                        screenshot_manager.stop_continuous_capture()
                        if main_window:
                            main_window.root.after(0, 
                                lambda: main_window.update_status("快捷键停止连续截图"))
                            # 更新GUI按钮状态
                            main_window.root.after(0, 
                                lambda: setattr(main_window, 'is_continuous_capturing', False))
                            main_window.root.after(0, 
                                lambda: main_window.continuous_btn.config(text="开始连续截图"))
                except Exception as e:
                    print(f"快捷键停止连续截图失败: {e}")
            
            # 使用自定义快捷键注册
            from core.hotkey import register_screenshot_hotkeys_custom
            register_screenshot_hotkeys_custom(
                single_screenshot,
                start_continuous_screenshot, 
                stop_continuous_screenshot,
                single_key,
                continuous_key,
                stop_key
            )
            
            # 启动快捷键服务
            if start_hotkey_service():
                self.hotkey_initialized = True
                print(f"自定义快捷键服务已启动:")
                print(f"  单次截图: {single_key}")
                print(f"  连续截图: {continuous_key}")
                print(f"  停止截图: {stop_key}")
            else:
                print("快捷键服务启动失败")
                
        except Exception as e:
            print(f"初始化快捷键失败: {e}")
    
    def initialize_managers(self):
        """初始化各个管理器"""
        try:
            # 加载配置
            config_manager.load_config()
            
            # 初始化截图管理器
            region = config_manager.get_screenshot_region()
            screenshot_manager.set_capture_region(*region)
            screenshot_manager.set_save_directory(config_manager.get_save_directory())
            screenshot_manager.set_capture_interval(config_manager.get_continuous_interval())
            
            # 初始化文件管理器
            file_manager.set_base_directory(config_manager.get_save_directory())
            
            print("管理器初始化完成")
            
        except Exception as e:
            print(f"初始化管理器失败: {e}")
    
    def create_gui(self):
        """创建GUI界面"""
        # 首先尝试导入GUI模块
        if not _import_gui_modules():
            print("错误: 无法导入GUI模块")
            print("解决方案:")
            print("1. 在Linux/WSL中安装: sudo apt-get install python3-tk python3-dev")
            print("2. 或者运行核心功能测试: python minimal_test.py")
            return False
            
        # 确保 create_main_window 可用
        if not create_main_window:
            print("错误: GUI函数未能成功导入。")
            return False
            
        try:
            self.gui_available = True
            self.main_window = create_main_window()
            if self.main_window is None:
                print("错误: create_main_window返回None")
                return False
            return True
        except Exception as e:
            print(f"创建GUI失败: {e}")
            return False
    
    def setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            print("接收到退出信号，正在清理...")
            self.cleanup()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def cleanup(self):
        """清理资源"""
        try:
            # 停止连续截图
            if screenshot_manager.is_continuous_capturing():
                screenshot_manager.stop_continuous_capture()
            
            # 停止快捷键服务
            if self.hotkey_initialized:
                stop_hotkey_service()
            
            # 保存配置
            config_manager.save_config()
            
            print("资源清理完成")
            
        except Exception as e:
            print(f"清理资源时出错: {e}")
    
    def run(self):
        """运行应用程序"""
        try:
            print("启动截图工具...")
            
            # 设置信号处理器
            self.setup_signal_handlers()
            
            # 初始化管理器
            self.initialize_managers()
            
            # 尝试创建GUI
            gui_success = self.create_gui()
            
            if gui_success and self.main_window:
                # GUI模式成功启动, 初始化快捷键并传入窗口实例
                self.initialize_hotkeys(self.main_window)
                
                print("截图工具已启动 (GUI模式)")
                print("快捷键:")
                print("  Ctrl+Shift+S: 单次截图")
                print("  Ctrl+Shift+C: 开始连续截图")
                print("  Ctrl+Shift+X: 停止连续截图")
                
                # 运行GUI主循环
                self.main_window.run()
            else:
                # GUI启动失败，显示帮助信息
                print("\n" + "="*50)
                print("❌ GUI模式启动失败")
                print("="*50)
                print("💡 建议运行以下命令测试核心功能:")
                print("   python minimal_test.py")
                print("   python start.py")
                print("\n🔧 或安装GUI支持:")
                print("   sudo apt-get install python3-tk python3-dev")
                print("="*50)
                return False
            
            return True
            
        except KeyboardInterrupt:
            print("\n用户中断程序")
            return False
        except Exception as e:
            print(f"运行程序时出错: {e}")
            return False
        finally:
            self.cleanup()


def main():
    """主函数"""
    try:
        # 检查Python版本
        if sys.version_info < (3, 8):
            print("错误: 需要Python 3.8或更高版本")
            sys.exit(1)
        
        # 创建并运行应用程序
        app = JietuApplication()
        success = app.run()
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        print(f"程序启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
