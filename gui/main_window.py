"""主GUI界面模块"""

import threading
import os
from pathlib import Path

# 延迟导入GUI模块，避免在无GUI环境下导入失败
tk = None
ttk = None
filedialog = None
messagebox = None

def _import_gui_modules():
    """延迟导入GUI模块"""
    global tk, ttk, filedialog, messagebox
    if tk is None:
        try:
            import tkinter as _tk
            from tkinter import ttk as _ttk, filedialog as _filedialog, messagebox as _messagebox
            tk = _tk
            ttk = _ttk
            filedialog = _filedialog
            messagebox = _messagebox
            return True
        except ImportError as e:
            print(f"GUI模块导入失败: {e}")
            return False
    return True

from core.screenshot import screenshot_manager
from core.config import config_manager
from core.hotkey import hotkey_manager, stop_hotkey_service, start_hotkey_service
from utils.file_manager import file_manager


class MainWindow:
    """主窗口类"""
    
    def __init__(self):
        # 确保GUI模块已导入
        if not _import_gui_modules():
            raise ImportError("无法导入GUI模块")
            
        self.root = tk.Tk()
        self.root.title("截图工具 - Jietu (Windows版)")
        self.root.geometry("500x450")  # 增加窗口高度以容纳新功能
        self.root.resizable(True, True)
        
        # Windows系统特定配置
        if os.name == 'nt':
            # 设置窗口图标（如果存在）
            try:
                # 可以添加ico文件路径
                pass
            except:
                pass
            
            # 设置窗口在任务栏中的显示
            self.root.attributes('-toolwindow', False)
        
        # 状态变量
        self.is_continuous_capturing = False
        
        # 创建界面
        self.create_widgets()
        self.load_settings()
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Windows系统快捷键提示
        self.show_windows_shortcuts()
    
    def show_windows_shortcuts(self):
        """显示Windows系统快捷键提示"""
        if os.name == 'nt':
            print("Windows系统快捷键已启用:")
            print("  Ctrl+Shift+S: 单次截图")
            print("  Ctrl+Shift+C: 开始连续截图") 
            print("  Ctrl+Shift+X: 停止连续截图")
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # 截图区域设置
        region_frame = ttk.LabelFrame(main_frame, text="截图区域设置", padding="5")
        region_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        region_frame.columnconfigure(1, weight=1)
        
        # 区域坐标输入
        ttk.Label(region_frame, text="左上角 X:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.x1_var = tk.StringVar(value="1750")
        ttk.Entry(region_frame, textvariable=self.x1_var, width=8).grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        ttk.Label(region_frame, text="Y:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.y1_var = tk.StringVar(value="60")
        ttk.Entry(region_frame, textvariable=self.y1_var, width=8).grid(row=0, column=3, sticky=tk.W)
        
        ttk.Label(region_frame, text="右下角 X:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.x2_var = tk.StringVar(value="1860")
        ttk.Entry(region_frame, textvariable=self.x2_var, width=8).grid(row=1, column=1, sticky=tk.W, padx=(0, 10))
        
        ttk.Label(region_frame, text="Y:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5))
        self.y2_var = tk.StringVar(value="160")
        ttk.Entry(region_frame, textvariable=self.y2_var, width=8).grid(row=1, column=3, sticky=tk.W)
        
        # 应用区域按钮
        ttk.Button(region_frame, text="应用区域", command=self.apply_region).grid(row=0, column=4, rowspan=2, padx=(10, 0))
        
        # 添加全屏截图按钮
        ttk.Button(region_frame, text="全屏截图", command=self.fullscreen_screenshot).grid(row=2, column=0, columnspan=5, pady=(5, 0), sticky=(tk.W, tk.E))
        
        row += 1
        
        # 保存设置
        save_frame = ttk.LabelFrame(main_frame, text="保存设置", padding="5")
        save_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        save_frame.columnconfigure(1, weight=1)
        
        ttk.Label(save_frame, text="保存目录:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.save_dir_var = tk.StringVar(value="screenshots")
        ttk.Entry(save_frame, textvariable=self.save_dir_var).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(save_frame, text="浏览", command=self.browse_directory).grid(row=0, column=2)
        
        row += 1
        
        # 连续截图设置
        continuous_frame = ttk.LabelFrame(main_frame, text="连续截图设置", padding="5")
        continuous_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(continuous_frame, text="间隔时间(秒):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.interval_var = tk.StringVar(value="1.0")
        interval_spinbox = ttk.Spinbox(continuous_frame, from_=0.1, to=60.0, increment=0.1, 
                                      textvariable=self.interval_var, width=10)
        interval_spinbox.grid(row=0, column=1, sticky=tk.W)
        
        row += 1
        
        # Windows系统快捷键设置 - 可自定义版本
        hotkey_frame = ttk.LabelFrame(main_frame, text="快捷键设置 (可自定义)", padding="5")
        hotkey_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        hotkey_frame.columnconfigure(1, weight=1)
        
        # 单次截图快捷键
        ttk.Label(hotkey_frame, text="单次截图:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.single_hotkey_var = tk.StringVar(value="ctrl+shift+s")
        self.single_hotkey_entry = ttk.Entry(hotkey_frame, textvariable=self.single_hotkey_var, width=20)
        self.single_hotkey_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        self.single_hotkey_entry.bind('<Key>', self.on_hotkey_key_press)
        self.single_hotkey_entry.bind('<KeyRelease>', self.on_hotkey_key_release)
        
        # 添加捕获按钮
        ttk.Button(hotkey_frame, text="捕获", command=lambda: self.start_key_capture(self.single_hotkey_var, self.single_hotkey_entry)).grid(row=0, column=2, padx=(5, 0))
        
        # 连续截图快捷键
        ttk.Label(hotkey_frame, text="连续截图:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.continuous_hotkey_var = tk.StringVar(value="ctrl+shift+c")
        self.continuous_hotkey_entry = ttk.Entry(hotkey_frame, textvariable=self.continuous_hotkey_var, width=20)
        self.continuous_hotkey_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        self.continuous_hotkey_entry.bind('<Key>', self.on_hotkey_key_press)
        self.continuous_hotkey_entry.bind('<KeyRelease>', self.on_hotkey_key_release)
        
        # 添加捕获按钮
        ttk.Button(hotkey_frame, text="捕获", command=lambda: self.start_key_capture(self.continuous_hotkey_var, self.continuous_hotkey_entry)).grid(row=1, column=2, padx=(5, 0))
        
        # 停止截图快捷键
        ttk.Label(hotkey_frame, text="停止截图:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5))
        self.stop_hotkey_var = tk.StringVar(value="ctrl+shift+x")
        self.stop_hotkey_entry = ttk.Entry(hotkey_frame, textvariable=self.stop_hotkey_var, width=20)
        self.stop_hotkey_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        self.stop_hotkey_entry.bind('<Key>', self.on_hotkey_key_press)
        self.stop_hotkey_entry.bind('<KeyRelease>', self.on_hotkey_key_release)
        
        # 添加捕获按钮
        ttk.Button(hotkey_frame, text="捕获", command=lambda: self.start_key_capture(self.stop_hotkey_var, self.stop_hotkey_entry)).grid(row=2, column=2, padx=(5, 0))
        
        # 快捷键控制按钮
        hotkey_btn_frame = ttk.Frame(hotkey_frame)
        hotkey_btn_frame.grid(row=3, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(hotkey_btn_frame, text="应用快捷键", command=self.apply_hotkeys).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(hotkey_btn_frame, text="重置默认", command=self.reset_default_hotkeys).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(hotkey_btn_frame, text="验证快捷键", command=self.validate_hotkeys).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(hotkey_btn_frame, text="测试快捷键", command=self.test_current_hotkeys).grid(row=0, column=3)
        
        # 快捷键状态显示
        self.hotkey_status_var = tk.StringVar(value="快捷键状态: 未应用")
        ttk.Label(hotkey_frame, textvariable=self.hotkey_status_var, foreground="blue").grid(row=4, column=0, columnspan=3, pady=(5, 0))
        
        # 初始化键盘捕获状态
        self.capturing_key = False
        self.current_capture_var = None
        self.current_capture_entry = None
        self.pressed_keys = set()
        
        row += 1
        
        # 控制按钮
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=row, column=0, columnspan=2, pady=(10, 0))
        
        self.single_btn = ttk.Button(control_frame, text="单次截图", command=self.single_screenshot)
        self.single_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.continuous_btn = ttk.Button(control_frame, text="开始连续截图", command=self.toggle_continuous_screenshot)
        self.continuous_btn.grid(row=0, column=1, padx=(0, 10))
        
        self.save_settings_btn = ttk.Button(control_frame, text="保存设置", command=self.save_settings)
        self.save_settings_btn.grid(row=0, column=2, padx=(0, 10))
        
        self.open_folder_btn = ttk.Button(control_frame, text="打开目录", command=self.open_save_directory)
        self.open_folder_btn.grid(row=0, column=3, padx=(0, 10))
        
        # 添加退出按钮
        self.exit_btn = ttk.Button(control_frame, text="退出程序", command=self.on_close)
        self.exit_btn.grid(row=0, column=4)
        
        row += 1
        
        # 状态显示
        status_frame = ttk.LabelFrame(main_frame, text="状态信息", padding="5")
        status_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_var = tk.StringVar(value="就绪 - Windows系统已优化")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # 文件计数显示
        self.file_count_var = tk.StringVar(value="已保存: 0 张截图")
        ttk.Label(status_frame, textvariable=self.file_count_var).grid(row=1, column=0, sticky=tk.W)
        
        # 屏幕信息显示
        try:
            screen_size = screenshot_manager.get_screen_size()
            self.screen_info_var = tk.StringVar(value=f"屏幕分辨率: {screen_size[0]}×{screen_size[1]}")
            ttk.Label(status_frame, textvariable=self.screen_info_var).grid(row=2, column=0, sticky=tk.W)
        except:
            pass
    
    def fullscreen_screenshot(self):
        """执行全屏截图"""
        def capture():
            try:
                saved_path = screenshot_manager.capture_fullscreen()
                if saved_path:
                    self.update_status(f"全屏截图已保存: {os.path.basename(saved_path)}")
                    self.update_file_count()
                else:
                    self.update_status("全屏截图失败！")
            except Exception as e:
                self.update_status(f"全屏截图错误: {e}")
        
        # 在后台线程中执行截图
        threading.Thread(target=capture, daemon=True).start()
    
    def apply_region(self):
        """应用截图区域设置"""
        try:
            x1 = int(self.x1_var.get())
            y1 = int(self.y1_var.get())
            x2 = int(self.x2_var.get())
            y2 = int(self.y2_var.get())
            
            # 验证区域
            if not screenshot_manager.validate_region(x1, y1, x2, y2):
                messagebox.showerror("错误", "截图区域无效！请检查坐标是否正确。")
                return
            
            # 应用设置
            screenshot_manager.set_capture_region(x1, y1, x2, y2)
            config_manager.set_screenshot_region(x1, y1, x2, y2, is_custom=True)
            
            self.update_status(f"截图区域已设置: ({x1}, {y1}) 到 ({x2}, {y2})")
            
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字坐标！")
    
    def browse_directory(self):
        """浏览选择保存目录"""
        directory = filedialog.askdirectory(title="选择截图保存目录")
        if directory:
            self.save_dir_var.set(directory)
            screenshot_manager.set_save_directory(directory)
            file_manager.set_base_directory(directory)
            config_manager.set_save_directory(directory)
            self.update_file_count()
    
    def single_screenshot(self):
        """执行单次截图"""
        def capture():
            try:
                # 更新设置
                self.apply_current_settings()
                
                saved_path = screenshot_manager.capture_single()
                if saved_path:
                    self.update_status(f"截图已保存: {os.path.basename(saved_path)}")
                    self.update_file_count()
                else:
                    self.update_status("截图失败！")
            except Exception as e:
                self.update_status(f"截图错误: {e}")
        
        # 在后台线程中执行截图
        threading.Thread(target=capture, daemon=True).start()
    
    def toggle_continuous_screenshot(self):
        """切换连续截图状态"""
        if not self.is_continuous_capturing:
            self.start_continuous_screenshot()
        else:
            self.stop_continuous_screenshot()
    
    def start_continuous_screenshot(self):
        """开始连续截图"""
        try:
            # 应用当前设置
            self.apply_current_settings()
            
            # 开始连续截图
            def on_capture(saved_path):
                self.root.after(0, lambda: self.update_status(f"已截图: {os.path.basename(saved_path)}"))
                self.root.after(0, self.update_file_count)
            
            if screenshot_manager.start_continuous_capture(on_capture):
                self.is_continuous_capturing = True
                self.continuous_btn.config(text="停止连续截图")
                self.update_status("连续截图已开始...")
            else:
                self.update_status("启动连续截图失败！")
                
        except Exception as e:
            self.update_status(f"连续截图错误: {e}")
    
    def stop_continuous_screenshot(self):
        """停止连续截图"""
        screenshot_manager.stop_continuous_capture()
        self.is_continuous_capturing = False
        self.continuous_btn.config(text="开始连续截图")
        self.update_status("连续截图已停止")
    
    def apply_current_settings(self):
        """应用当前界面设置"""
        # 应用保存目录
        save_dir = self.save_dir_var.get()
        if save_dir:
            screenshot_manager.set_save_directory(save_dir)
            file_manager.set_base_directory(save_dir)
        
        # 应用截图间隔
        try:
            interval = float(self.interval_var.get())
            screenshot_manager.set_capture_interval(interval)
            config_manager.set_continuous_interval(interval)
        except ValueError:
            pass  # 使用默认值
        
        # 应用截图区域（如果有变化）
        self.apply_region()
    
    def save_settings(self):
        """保存所有设置"""
        try:
            self.apply_current_settings()
            
            # 保存快捷键设置
            config_manager.set_hotkey("single_capture", self.single_hotkey_var.get().strip().lower())
            config_manager.set_hotkey("start_continuous", self.continuous_hotkey_var.get().strip().lower())
            config_manager.set_hotkey("stop_continuous", self.stop_hotkey_var.get().strip().lower())
            
            config_manager.save_config()
            self.update_status("设置已保存")
        except Exception as e:
            self.update_status(f"保存设置失败: {e}")
    
    def load_settings(self):
        """加载设置"""
        try:
            # 加载截图区域
            x1, y1, x2, y2 = config_manager.get_screenshot_region()
            self.x1_var.set(str(x1))
            self.y1_var.set(str(y1))
            self.x2_var.set(str(x2))
            self.y2_var.set(str(y2))
            
            # 加载保存目录
            save_dir = config_manager.get_save_directory()
            self.save_dir_var.set(save_dir)
            
            # 加载连续截图间隔
            interval = config_manager.get_continuous_interval()
            self.interval_var.set(str(interval))
            
            # 加载快捷键设置
            single_hotkey = config_manager.get_hotkey("single_capture") or "ctrl+shift+s"
            continuous_hotkey = config_manager.get_hotkey("start_continuous") or "ctrl+shift+c"
            stop_hotkey = config_manager.get_hotkey("stop_continuous") or "ctrl+shift+x"
            
            self.single_hotkey_var.set(single_hotkey)
            self.continuous_hotkey_var.set(continuous_hotkey)
            self.stop_hotkey_var.set(stop_hotkey)
            
            # 应用设置到管理器
            screenshot_manager.set_capture_region(x1, y1, x2, y2)
            screenshot_manager.set_save_directory(save_dir)
            screenshot_manager.set_capture_interval(interval)
            file_manager.set_base_directory(save_dir)
            
            self.update_file_count()
            
        except Exception as e:
            self.update_status(f"加载设置失败: {e}")
    
    def update_status(self, message: str):
        """更新状态显示"""
        self.status_var.set(message)
    
    def update_file_count(self):
        """更新文件计数显示"""
        try:
            files = file_manager.get_screenshot_files()
            count = len(files)
            self.file_count_var.set(f"已保存: {count} 张截图")
        except Exception:
            self.file_count_var.set("文件计数: 未知")
    
    def open_save_directory(self):
        """打开保存目录 - Windows优化版本"""
        save_dir = self.save_dir_var.get()
        if save_dir and os.path.exists(save_dir):
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(save_dir)
                elif os.name == 'posix':  # macOS and Linux
                    import subprocess
                    subprocess.Popen(['xdg-open', save_dir])
            except Exception as e:
                messagebox.showerror("错误", f"无法打开目录: {e}")
        else:
            messagebox.showwarning("警告", "保存目录不存在！")
    
    def on_close(self):
        """窗口关闭事件处理"""
        # 停止连续截图
        if self.is_continuous_capturing:
            self.stop_continuous_screenshot()
        
        # 保存设置
        try:
            self.save_settings()
        except Exception:
            pass
        
        # 关闭窗口
        self.root.destroy()
    
    def run(self):
        """运行主窗口"""
        self.root.mainloop()

    def validate_hotkey_format(self, hotkey_str: str) -> bool:
        """验证快捷键格式"""
        if not hotkey_str:
            return False
            
        try:
            # 使用快捷键管理器的详细验证
            is_valid, _ = hotkey_manager.validate_hotkey_with_details(hotkey_str)
            return is_valid
        except:
            return False
    
    def validate_hotkeys(self):
        """验证所有快捷键"""
        single_key = self.single_hotkey_var.get().strip().lower()
        continuous_key = self.continuous_hotkey_var.get().strip().lower()
        stop_key = self.stop_hotkey_var.get().strip().lower()
        
        results = []
        
        # 验证格式
        is_valid, message = hotkey_manager.validate_hotkey_with_details(single_key)
        if is_valid:
            results.append(f"✅ 单次截图: {single_key}")
        else:
            results.append(f"❌ 单次截图: {single_key}")
            results.append(f"   错误: {message}")
            
        is_valid, message = hotkey_manager.validate_hotkey_with_details(continuous_key)
        if is_valid:
            results.append(f"✅ 连续截图: {continuous_key}")
        else:
            results.append(f"❌ 连续截图: {continuous_key}")
            results.append(f"   错误: {message}")
            
        is_valid, message = hotkey_manager.validate_hotkey_with_details(stop_key)
        if is_valid:
            results.append(f"✅ 停止截图: {stop_key}")
        else:
            results.append(f"❌ 停止截图: {stop_key}")
            results.append(f"   错误: {message}")
        
        # 检查重复
        hotkeys = [single_key, continuous_key, stop_key]
        if len(set(hotkeys)) != len(hotkeys):
            results.append("⚠️ 警告: 存在重复的快捷键")
        
        # 添加格式说明
        results.append("\n" + "="*40)
        results.append("快捷键格式说明:")
        results.append("• 基本格式: 修饰键+主键")
        results.append("• 修饰键: ctrl, shift, alt, win")
        results.append("• 主键: 字母、数字、功能键等")
        results.append("• 示例: ctrl+shift+s, alt+f4")
        
        # 显示验证结果
        result_text = "\n".join(results)
        messagebox.showinfo("快捷键验证结果", result_text)
    
    def apply_hotkeys(self):
        """应用自定义快捷键"""
        try:
            # 获取新的快捷键设置
            single_key = self.single_hotkey_var.get().strip().lower()
            continuous_key = self.continuous_hotkey_var.get().strip().lower()
            stop_key = self.stop_hotkey_var.get().strip().lower()
            
            # 使用详细验证
            errors = []
            
            is_valid, message = hotkey_manager.validate_hotkey_with_details(single_key)
            if not is_valid:
                errors.append(f"单次截图快捷键: {message}")
                
            is_valid, message = hotkey_manager.validate_hotkey_with_details(continuous_key)
            if not is_valid:
                errors.append(f"连续截图快捷键: {message}")
                
            is_valid, message = hotkey_manager.validate_hotkey_with_details(stop_key)
            if not is_valid:
                errors.append(f"停止截图快捷键: {message}")
            
            if errors:
                error_msg = "快捷键格式错误:\n\n" + "\n".join(f"• {error}" for error in errors)
                error_msg += "\n\n快捷键格式: 修饰键+主键\n示例: ctrl+shift+s"
                messagebox.showerror("格式错误", error_msg)
                return
            
            # 检查快捷键冲突
            hotkeys = [single_key, continuous_key, stop_key]
            if len(set(hotkeys)) != len(hotkeys):
                messagebox.showerror("错误", "快捷键不能重复！")
                return
            
            # 停止当前快捷键监听
            stop_hotkey_service()
            
            # 清除现有快捷键
            hotkey_manager.clear_all_hotkeys()
            
            # 重新注册快捷键
            self.register_custom_hotkeys(single_key, continuous_key, stop_key)
            
            # 重新启动快捷键服务
            if start_hotkey_service():
                # 保存到配置
                config_manager.set_hotkey("single_capture", single_key)
                config_manager.set_hotkey("start_continuous", continuous_key)
                config_manager.set_hotkey("stop_continuous", stop_key)
                config_manager.save_config()
                
                self.hotkey_status_var.set("快捷键状态: 已应用并保存")
                self.update_status("自定义快捷键已应用")
                
                success_msg = f"快捷键设置已应用！\n\n"
                success_msg += f"单次截图: {single_key}\n"
                success_msg += f"连续截图: {continuous_key}\n" 
                success_msg += f"停止截图: {stop_key}"
                messagebox.showinfo("成功", success_msg)
            else:
                self.hotkey_status_var.set("快捷键状态: 应用失败")
                messagebox.showerror("错误", "快捷键服务启动失败！")
                
        except Exception as e:
            self.hotkey_status_var.set("快捷键状态: 错误")
            messagebox.showerror("错误", f"应用快捷键失败: {e}")
    
    def reset_default_hotkeys(self):
        """重置为默认快捷键"""
        if messagebox.askyesno("确认", "确定要重置为默认快捷键吗？"):
            self.single_hotkey_var.set("ctrl+shift+s")
            self.continuous_hotkey_var.set("ctrl+shift+c")
            self.stop_hotkey_var.set("ctrl+shift+x")
            self.hotkey_status_var.set("快捷键状态: 已重置为默认")
            self.update_status("快捷键已重置为默认值")
    
    def register_custom_hotkeys(self, single_key: str, continuous_key: str, stop_key: str):
        """注册自定义快捷键"""
        def single_screenshot_callback():
            """单次截图回调"""
            try:
                saved_path = screenshot_manager.capture_single()
                if saved_path and hasattr(self, 'root'):
                    self.root.after(0, 
                        lambda: self.update_status(f"快捷键截图: {os.path.basename(saved_path)}"))
                    self.root.after(0, self.update_file_count)
            except Exception as e:
                print(f"快捷键截图失败: {e}")
        
        def start_continuous_callback():
            """开始连续截图回调"""
            try:
                if not screenshot_manager.is_continuous_capturing():
                    def on_capture(saved_path):
                        if hasattr(self, 'root'):
                            self.root.after(0, 
                                lambda: self.update_status(f"连续截图: {os.path.basename(saved_path)}"))
                            self.root.after(0, self.update_file_count)
                    
                    screenshot_manager.start_continuous_capture(on_capture)
                    if hasattr(self, 'root'):
                        self.root.after(0, 
                            lambda: self.update_status("快捷键启动连续截图"))
                        self.root.after(0, 
                            lambda: setattr(self, 'is_continuous_capturing', True))
                        self.root.after(0, 
                            lambda: self.continuous_btn.config(text="停止连续截图"))
            except Exception as e:
                print(f"快捷键启动连续截图失败: {e}")
        
        def stop_continuous_callback():
            """停止连续截图回调"""
            try:
                if screenshot_manager.is_continuous_capturing():
                    screenshot_manager.stop_continuous_capture()
                    if hasattr(self, 'root'):
                        self.root.after(0, 
                            lambda: self.update_status("快捷键停止连续截图"))
                        self.root.after(0, 
                            lambda: setattr(self, 'is_continuous_capturing', False))
                        self.root.after(0, 
                            lambda: self.continuous_btn.config(text="开始连续截图"))
            except Exception as e:
                print(f"快捷键停止连续截图失败: {e}")
        
        # 注册快捷键
        hotkey_manager.register_hotkey(single_key, single_screenshot_callback, "单次截图")
        hotkey_manager.register_hotkey(continuous_key, start_continuous_callback, "开始连续截图")
        hotkey_manager.register_hotkey(stop_key, stop_continuous_callback, "停止连续截图")

    def start_key_capture(self, var, entry):
        """开始捕获快捷键"""
        if self.capturing_key:
            self.stop_key_capture()
            return
            
        self.capturing_key = True
        self.current_capture_var = var
        self.current_capture_entry = entry
        self.pressed_keys.clear()
        
        # 更改输入框外观
        entry.config(state='readonly')
        entry.config(style='Capture.TEntry')
        
        # 设置提示文本
        var.set("按下快捷键组合...")
        
        # 绑定全局按键事件
        self.root.bind('<KeyPress>', self.on_capture_key_press)
        self.root.bind('<KeyRelease>', self.on_capture_key_release)
        self.root.focus_set()
        
        # 5秒后自动停止捕获
        self.root.after(5000, self.stop_key_capture)
    
    def stop_key_capture(self):
        """停止捕获快捷键"""
        if not self.capturing_key:
            return
            
        self.capturing_key = False
        
        # 解绑事件
        self.root.unbind('<KeyPress>')
        self.root.unbind('<KeyRelease>')
        
        # 恢复输入框
        if self.current_capture_entry:
            self.current_capture_entry.config(state='normal')
            
        self.current_capture_var = None
        self.current_capture_entry = None
        self.pressed_keys.clear()
    
    def on_capture_key_press(self, event):
        """捕获按键按下事件"""
        if not self.capturing_key:
            return
            
        # 获取按键信息
        key_name = self.get_key_name(event)
        if key_name:
            self.pressed_keys.add(key_name)
            
        # 如果有修饰键和主键，生成快捷键字符串
        modifiers = []
        main_key = None
        
        for key in self.pressed_keys:
            if key in ['ctrl', 'shift', 'alt', 'win']:
                modifiers.append(key)
            else:
                main_key = key
        
        if modifiers and main_key:
            hotkey_str = '+'.join(sorted(modifiers) + [main_key])
            if self.current_capture_var:
                self.current_capture_var.set(hotkey_str)
    
    def on_capture_key_release(self, event):
        """捕获按键释放事件"""
        if not self.capturing_key:
            return
            
        # 当所有键释放后停止捕获
        if len(self.pressed_keys) > 0:
            key_name = self.get_key_name(event)
            if key_name in self.pressed_keys:
                self.pressed_keys.discard(key_name)
                
            # 如果所有键都释放了，停止捕获
            if len(self.pressed_keys) == 0:
                self.root.after(100, self.stop_key_capture)  # 延迟停止，确保按键组合完整
    
    def get_key_name(self, event):
        """获取标准化的按键名称"""
        key_map = {
            'Control_L': 'ctrl', 'Control_R': 'ctrl',
            'Shift_L': 'shift', 'Shift_R': 'shift',
            'Alt_L': 'alt', 'Alt_R': 'alt',
            'Super_L': 'win', 'Super_R': 'win',
            'Win_L': 'win', 'Win_R': 'win',
            'space': 'space',
            'Return': 'enter',
            'Tab': 'tab',
            'Escape': 'esc',
            'BackSpace': 'backspace',
            'Delete': 'delete',
            'Home': 'home',
            'End': 'end',
            'Page_Up': 'page_up',
            'Page_Down': 'page_down',
            'Up': 'up', 'Down': 'down', 
            'Left': 'left', 'Right': 'right'
        }
        
        keysym = event.keysym
        
        # 映射特殊键
        if keysym in key_map:
            return key_map[keysym]
        
        # 功能键
        if keysym.startswith('F') and keysym[1:].isdigit():
            return keysym.lower()
            
        # 普通字符
        if len(keysym) == 1 and keysym.isalnum():
            return keysym.lower()
            
        return None
    
    def on_hotkey_key_press(self, event):
        """处理快捷键输入框的按键事件"""
        # 如果正在捕获，阻止默认输入
        if self.capturing_key:
            return "break"
        return None
    
    def on_hotkey_key_release(self, event):
        """处理快捷键输入框的按键释放事件"""
        return None
    
    def test_current_hotkeys(self):
        """测试当前快捷键是否有效"""
        print("🧪 测试当前快捷键...")
        
        # 获取当前设置
        single_key = self.single_hotkey_var.get().strip().lower()
        continuous_key = self.continuous_hotkey_var.get().strip().lower()
        stop_key = self.stop_hotkey_var.get().strip().lower()
        
        # 显示测试信息
        test_info = f"""快捷键测试信息:

当前设置:
• 单次截图: {single_key}
• 连续截图: {continuous_key}  
• 停止截图: {stop_key}

快捷键监听状态: {'运行中' if hotkey_manager.is_listening() else '已停止'}
已注册快捷键数量: {len(hotkey_manager.get_registered_hotkeys())}

测试说明:
1. 确保快捷键格式正确
2. 检查是否与其他软件冲突
3. 尝试按下快捷键进行测试
4. 查看控制台输出信息

建议:
• 如果快捷键不响应，尝试以管理员身份运行
• 避免使用系统保留的快捷键
• 确保没有被其他程序占用"""
        
        messagebox.showinfo("快捷键测试", test_info)
        
        # 在控制台输出调试信息
        print(f"  当前快捷键设置:")
        print(f"    单次截图: {single_key}")
        print(f"    连续截图: {continuous_key}")
        print(f"    停止截图: {stop_key}")
        print(f"  快捷键监听状态: {hotkey_manager.is_listening()}")
        print(f"  已注册快捷键: {list(hotkey_manager.get_registered_hotkeys().keys())}")
        
        # 测试快捷键验证
        for name, key in [('单次截图', single_key), ('连续截图', continuous_key), ('停止截图', stop_key)]:
            is_valid, message = hotkey_manager.validate_hotkey_with_details(key)
            status = "✅" if is_valid else "❌"
            print(f"  {status} {name}({key}): {message}")


def create_main_window():
    """创建并返回主窗口实例"""
    if not _import_gui_modules():
        print("错误: 无法创建主窗口，GUI模块导入失败")
        return None
    
    try:
        return MainWindow()
    except Exception as e:
        print(f"错误: 创建主窗口失败 - {e}")
        return None