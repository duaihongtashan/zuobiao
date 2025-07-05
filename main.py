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
import os

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
from core.circle_detection import circle_detector
from core.circle_capture import circle_capture
from utils.file_manager import file_manager


class JietuApplication:
    """截图应用程序主类"""
    
    def __init__(self):
        self.main_window = None
        self.hotkey_initialized = False
        self.gui_available = False
        
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
            
            # 初始化圆形检测和截图功能
            if config_manager.is_circle_detection_enabled():
                # 设置圆形截图保存目录
                circle_save_dir = config_manager.get_circle_images_directory()
                circle_capture.set_save_directory(circle_save_dir)
                
                # 应用检测参数
                hough_params = config_manager.get_hough_params()
                from core.circle_detection import DetectionParams
                detection_params = DetectionParams(
                    min_radius=hough_params.get('min_radius', 10),
                    max_radius=hough_params.get('max_radius', 100),
                    min_dist=hough_params.get('min_dist', 50),
                    param2=hough_params.get('param2', 30)
                )
                circle_detector.set_params(detection_params)
                
                print("圆形检测功能已初始化")
            
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
                # GUI模式成功启动, 让GUI自己处理快捷键
                print("截图工具已启动 (GUI模式)")
                
                # 显示圆形检测功能状态
                if config_manager.is_circle_detection_enabled():
                    print("✅ 圆形检测功能已启用")
                    print("   - 支持HoughCircles算法检测圆形")
                    print("   - 支持圆形区域精确截图")
                    print("   - 支持透明背景和抗锯齿")
                else:
                    print("ℹ️  圆形检测功能已禁用（可在GUI中启用）")
                
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
