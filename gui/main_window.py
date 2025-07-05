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
from core.circle_detection import circle_detector, DetectionParams
from core.circle_capture import circle_capture
from utils.file_manager import file_manager
from utils.coordinate_recorder import CoordinateRecorder


class MainWindow:
    """主窗口类"""
    
    def __init__(self):
        # 确保GUI模块已导入
        if not _import_gui_modules():
            raise ImportError("无法导入GUI模块")
            
        self.root = tk.Tk()
        self.root.title("截图工具 - Jietu (Windows版)")
        self.root.geometry("600x680")  # 优化窗口大小
        self.root.resizable(True, True)
        self.root.minsize(580, 600)  # 调整最小窗口尺寸
        
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
        self.circle_detection_enabled = False
        self.current_detected_circles = []
        self.circle_preview_image = None
        
        # 坐标记录器
        self.coordinate_recorder = CoordinateRecorder()
        
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
        # 创建主框架和notebook
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # 创建Notebook进行折叠设计
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # === 基础设置标签页 ===
        basic_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(basic_frame, text="基础设置")
        
        row = 0
        
        # 截图区域设置
        region_frame = ttk.LabelFrame(basic_frame, text="截图区域设置", padding="5")
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
        
        # 坐标记录按钮和状态
        coord_record_frame = ttk.Frame(region_frame)
        coord_record_frame.grid(row=2, column=0, columnspan=5, pady=(5, 0), sticky=(tk.W, tk.E))
        coord_record_frame.columnconfigure(2, weight=1)
        
        # 分别记录左上角和右下角的按钮
        self.record_topleft_btn = ttk.Button(coord_record_frame, text="记录左上角", command=self.start_record_topleft)
        self.record_topleft_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.record_bottomright_btn = ttk.Button(coord_record_frame, text="记录右下角", command=self.start_record_bottomright)
        self.record_bottomright_btn.grid(row=0, column=1, padx=(0, 10))
        
        self.coord_status_var = tk.StringVar(value="")
        self.coord_status_label = ttk.Label(coord_record_frame, textvariable=self.coord_status_var, foreground="blue")
        self.coord_status_label.grid(row=0, column=2, sticky=tk.W)
        
        # 添加全屏截图按钮
        ttk.Button(region_frame, text="全屏截图", command=self.fullscreen_screenshot).grid(row=3, column=0, columnspan=5, pady=(5, 0), sticky=(tk.W, tk.E))
        
        row += 1
        
        # 保存设置
        save_frame = ttk.LabelFrame(basic_frame, text="保存设置", padding="5")
        save_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        save_frame.columnconfigure(1, weight=1)
        
        ttk.Label(save_frame, text="保存目录:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.save_dir_var = tk.StringVar(value="screenshots")
        ttk.Entry(save_frame, textvariable=self.save_dir_var).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(save_frame, text="浏览", command=self.browse_directory).grid(row=0, column=2)
        
        row += 1
        
        # 连续截图设置
        continuous_frame = ttk.LabelFrame(basic_frame, text="连续截图设置", padding="5")
        continuous_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(continuous_frame, text="间隔时间(秒):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.interval_var = tk.StringVar(value="1.0")
        interval_spinbox = ttk.Spinbox(continuous_frame, from_=0.1, to=60.0, increment=0.1, 
                                      textvariable=self.interval_var, width=10)
        interval_spinbox.grid(row=0, column=1, sticky=tk.W)
        
        # === 快捷键设置标签页 ===
        hotkey_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(hotkey_tab, text="快捷键设置")
        
        # Windows系统快捷键设置 - 可自定义版本
        hotkey_frame = ttk.LabelFrame(hotkey_tab, text="快捷键设置 (可自定义)", padding="5")
        hotkey_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
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
        ttk.Button(hotkey_btn_frame, text="重置默认", command=self.reset_default_hotkeys).grid(row=0, column=1)
        
        # 快捷键状态显示
        self.hotkey_status_var = tk.StringVar(value="快捷键状态: 未应用")
        ttk.Label(hotkey_frame, textvariable=self.hotkey_status_var, foreground="blue").grid(row=4, column=0, columnspan=3, pady=(5, 0))
        
        # 初始化键盘捕获状态
        self.capturing_key = False
        self.current_capture_var = None
        self.current_capture_entry = None
        self.pressed_keys = set()
        
        # === 圆形检测标签页 ===
        circle_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(circle_tab, text="圆形检测")
        
        # 圆形检测功能区域
        circle_frame = ttk.LabelFrame(circle_tab, text="圆形检测功能", padding="5")
        circle_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        circle_frame.columnconfigure(1, weight=1)
        
        # 启用圆形检测
        self.circle_detection_var = tk.BooleanVar(value=False)
        circle_enable_cb = ttk.Checkbutton(circle_frame, text="启用圆形检测", 
                                         variable=self.circle_detection_var,
                                         command=self.toggle_circle_detection)
        circle_enable_cb.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # 检测参数调整
        params_frame = ttk.Frame(circle_frame)
        params_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 5))
        params_frame.columnconfigure(1, weight=1)
        params_frame.columnconfigure(3, weight=1)
        
        # 参数1：最小半径
        ttk.Label(params_frame, text="最小半径:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.min_radius_var = tk.StringVar(value="10")
        min_radius_spinbox = ttk.Spinbox(params_frame, from_=5, to=100, increment=5,
                                       textvariable=self.min_radius_var, width=8)
        min_radius_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        # 参数2：最大半径
        ttk.Label(params_frame, text="最大半径:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.max_radius_var = tk.StringVar(value="100")
        max_radius_spinbox = ttk.Spinbox(params_frame, from_=20, to=300, increment=10,
                                       textvariable=self.max_radius_var, width=8)
        max_radius_spinbox.grid(row=0, column=3, sticky=tk.W)
        
        # 参数3：最小距离
        ttk.Label(params_frame, text="最小距离:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.min_dist_var = tk.StringVar(value="50")
        min_dist_spinbox = ttk.Spinbox(params_frame, from_=20, to=150, increment=10,
                                     textvariable=self.min_dist_var, width=8)
        min_dist_spinbox.grid(row=1, column=1, sticky=tk.W, padx=(0, 10))
        
        # 参数4：检测阈值
        ttk.Label(params_frame, text="检测阈值:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5))
        self.param2_var = tk.StringVar(value="30")
        param2_spinbox = ttk.Spinbox(params_frame, from_=20, to=80, increment=5,
                                   textvariable=self.param2_var, width=8)
        param2_spinbox.grid(row=1, column=3, sticky=tk.W)
        
        # 圆形检测控制按钮
        circle_control_frame = ttk.Frame(circle_frame)
        circle_control_frame.grid(row=2, column=0, columnspan=2, pady=(10, 5))
        
        self.detect_circles_btn = ttk.Button(circle_control_frame, text="检测圆形", 
                                           command=self.detect_circles_in_region,
                                           state="disabled")
        self.detect_circles_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.clear_circles_btn = ttk.Button(circle_control_frame, text="清除结果", 
                                          command=self.clear_detected_circles,
                                          state="disabled")
        self.clear_circles_btn.grid(row=0, column=1)
        
        # 检测结果显示
        self.circle_results_var = tk.StringVar(value="暂无检测结果")
        circle_results_label = ttk.Label(circle_frame, textvariable=self.circle_results_var, 
                                       foreground="blue")
        circle_results_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # 自定义圆形截图功能区域
        custom_circle_frame = ttk.LabelFrame(circle_tab, text="自定义圆形截图", padding="5")
        custom_circle_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 10))
        custom_circle_frame.columnconfigure(1, weight=1)
        
        # 启用自定义圆形截图
        self.custom_circle_enabled_var = tk.BooleanVar(value=False)
        custom_circle_enable_cb = ttk.Checkbutton(custom_circle_frame, text="启用自定义圆形截图", 
                                                 variable=self.custom_circle_enabled_var,
                                                 command=self.toggle_custom_circle)
        custom_circle_enable_cb.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # 圆心坐标设置
        center_frame = ttk.Frame(custom_circle_frame)
        center_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 5))
        center_frame.columnconfigure(1, weight=1)
        center_frame.columnconfigure(3, weight=1)
        
        ttk.Label(center_frame, text="圆心 X:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.custom_circle_x_var = tk.StringVar(value="100")
        self.custom_circle_x_entry = ttk.Entry(center_frame, textvariable=self.custom_circle_x_var, width=10)
        self.custom_circle_x_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        ttk.Label(center_frame, text="Y:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.custom_circle_y_var = tk.StringVar(value="100")
        self.custom_circle_y_entry = ttk.Entry(center_frame, textvariable=self.custom_circle_y_var, width=10)
        self.custom_circle_y_entry.grid(row=0, column=3, sticky=tk.W, padx=(0, 10))
        
        # 记录圆心坐标按钮
        self.record_circle_center_btn = ttk.Button(center_frame, text="记录圆心", 
                                                  command=self.start_record_circle_center,
                                                  state="disabled")
        self.record_circle_center_btn.grid(row=0, column=4, padx=(5, 0))
        
        # 半径设置
        radius_frame = ttk.Frame(custom_circle_frame)
        radius_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 5))
        
        ttk.Label(radius_frame, text="半径:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.custom_circle_radius_var = tk.StringVar(value="50")
        radius_spinbox = ttk.Spinbox(radius_frame, from_=5, to=500, increment=5,
                                   textvariable=self.custom_circle_radius_var, width=10)
        radius_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        ttk.Label(radius_frame, text="像素").grid(row=0, column=2, sticky=tk.W, padx=(5, 0))
        
        # 自定义圆形状态显示
        self.custom_circle_status_var = tk.StringVar(value="")
        custom_circle_status_label = ttk.Label(custom_circle_frame, textvariable=self.custom_circle_status_var, 
                                             foreground="blue")
        custom_circle_status_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # === 在主框架底部添加控制按钮和状态显示 ===
        
        # 控制按钮 - 重新组织布局
        control_frame = ttk.LabelFrame(main_frame, text="操作控制", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 截图操作按钮区域
        screenshot_buttons_frame = ttk.Frame(control_frame)
        screenshot_buttons_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.single_btn = ttk.Button(screenshot_buttons_frame, text="单次截图", command=self.single_screenshot)
        self.single_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.continuous_btn = ttk.Button(screenshot_buttons_frame, text="开始连续截图", command=self.toggle_continuous_screenshot)
        self.continuous_btn.grid(row=0, column=1, padx=(0, 10))
        
        # 添加截图模式指示标签
        self.screenshot_mode_var = tk.StringVar(value="当前模式: 矩形截图")
        mode_label = ttk.Label(screenshot_buttons_frame, textvariable=self.screenshot_mode_var, foreground="green")
        mode_label.grid(row=0, column=2, padx=(20, 0))
        
        # 系统操作按钮区域
        system_buttons_frame = ttk.Frame(control_frame)
        system_buttons_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        self.save_settings_btn = ttk.Button(system_buttons_frame, text="保存设置", command=self.save_settings)
        self.save_settings_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.open_folder_btn = ttk.Button(system_buttons_frame, text="打开目录", command=self.open_save_directory)
        self.open_folder_btn.grid(row=0, column=1, padx=(0, 10))
        
        # 添加退出按钮
        self.exit_btn = ttk.Button(system_buttons_frame, text="退出程序", command=self.on_close)
        self.exit_btn.grid(row=0, column=2)
        
        # 状态显示
        status_frame = ttk.LabelFrame(main_frame, text="状态信息", padding="5")
        status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_var = tk.StringVar(value="就绪 - Windows系统已优化")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # 文件计数显示
        self.file_count_var = tk.StringVar(value="已保存: 0 张截图")
        ttk.Label(status_frame, textvariable=self.file_count_var).grid(row=1, column=0, sticky=tk.W)
        
        # 最新截图详情显示
        self.latest_screenshot_var = tk.StringVar(value="暂无截图")
        latest_label = ttk.Label(status_frame, textvariable=self.latest_screenshot_var, foreground="green")
        latest_label.grid(row=2, column=0, sticky=tk.W)
        
        # 最新截图路径（用于打开功能）
        self.latest_screenshot_path = None
        
        # 打开最新截图按钮
        self.open_latest_btn = ttk.Button(status_frame, text="打开图片", command=self.open_latest_screenshot, state="disabled")
        self.open_latest_btn.grid(row=2, column=1, sticky=tk.E, padx=(10, 0))
        
        # 屏幕信息显示
        try:
            screen_size = screenshot_manager.get_screen_size()
            self.screen_info_var = tk.StringVar(value=f"屏幕分辨率: {screen_size[0]}×{screen_size[1]}")
            ttk.Label(status_frame, textvariable=self.screen_info_var).grid(row=3, column=0, sticky=tk.W)
        except:
            pass
    
    def fullscreen_screenshot(self):
        """执行全屏截图"""
        def capture():
            try:
                result = screenshot_manager.capture_fullscreen()
                if result:
                    filename = os.path.basename(result['file_path'])
                    size_info = f"{result['size'][0]}×{result['size'][1]}像素"
                    file_size_kb = result['file_size'] / 1024
                    
                    status_msg = f"全屏截图已保存: {filename} | 大小: {size_info} | 文件: {file_size_kb:.1f}KB"
                    self.update_status(status_msg)
                    self.update_latest_screenshot_info(result)
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
                
                # 检查是否启用自定义圆形截图
                if self.custom_circle_enabled_var.get():
                    # 使用自定义圆形截图
                    params = self.get_custom_circle_params()
                    if params and params.get('center_x') is not None and params.get('center_y') is not None and params.get('radius') is not None:
                        result = screenshot_manager.capture_custom_circle(
                            params['center_x'], 
                            params['center_y'], 
                            params['radius']
                        )
                        screenshot_type = "圆形"
                    else:
                        self.update_status("自定义圆形参数无效！")
                        return
                else:
                    # 使用普通矩形截图
                    result = screenshot_manager.capture_single()
                    screenshot_type = "矩形"
                
                if result:
                    filename = os.path.basename(result['file_path'])
                    file_size_kb = result['file_size'] / 1024
                    
                    if result.get('screenshot_type') == 'custom_circle':
                        center_info = f"圆心: ({result['circle_center'][0]}, {result['circle_center'][1]}), 半径: {result['circle_radius']}"
                        status_msg = f"{screenshot_type}截图已保存: {filename} | {center_info} | 文件: {file_size_kb:.1f}KB"
                    else:
                        size_info = f"{result['size'][0]}×{result['size'][1]}像素"
                        status_msg = f"{screenshot_type}截图已保存: {filename} | 大小: {size_info} | 文件: {file_size_kb:.1f}KB"
                    
                    self.update_status(status_msg)
                    self.update_latest_screenshot_info(result)
                    self.update_file_count()
                else:
                    self.update_status(f"{screenshot_type}截图失败！")
            except Exception as e:
                self.update_status(f"截图错误: {e}")
        
        # 在后台线程中执行截图
        threading.Thread(target=capture, daemon=True).start()
    
    def toggle_continuous_screenshot(self):
        """切换连续截图状态"""
        # 修复时序Bug：在切换前先判断，避免竞争条件
        is_currently_capturing = self.is_continuous_capturing
        
        # UI/状态更新应该在所有逻辑之前，并且是同步的
        if not is_currently_capturing:
            self.is_continuous_capturing = True
            self.continuous_btn.config(text="停止连续截图")
            self.start_continuous_screenshot()
        else:
            self.is_continuous_capturing = False
            self.continuous_btn.config(text="开始连续截图")
            self.stop_continuous_screenshot()
    
    def start_continuous_screenshot(self):
        """开始连续截图的核心逻辑"""
        try:
            # 应用当前设置
            self.apply_current_settings()
            
            use_custom_circle = self.custom_circle_enabled_var.get()
            
            def on_capture(result):
                # ... (on_capture logic remains the same)
                filename = os.path.basename(result['file_path'])
                file_size_kb = result['file_size'] / 1024
                
                if result.get('screenshot_type') == 'custom_circle':
                    center_info = f"圆心: ({result['circle_center'][0]}, {result['circle_center'][1]}), 半径: {result['circle_radius']}"
                    status_msg = f"圆形截图: {filename} | {center_info} | {file_size_kb:.1f}KB"
                else:
                    size_info = f"{result['size'][0]}×{result['size'][1]}像素"
                    status_msg = f"矩形截图: {filename} | {size_info} | {file_size_kb:.1f}KB"
                
                self.root.after(0, lambda: self.update_status(status_msg))
                self.root.after(0, lambda: self.update_latest_screenshot_info(result))
                self.root.after(0, self.update_file_count)
            
            if use_custom_circle:
                custom_circle_params = self.get_custom_circle_params()
                if not (custom_circle_params and custom_circle_params.get('center_x') is not None and 
                       custom_circle_params.get('center_y') is not None and custom_circle_params.get('radius') is not None):
                    self.update_status("自定义圆形参数无效，无法启动！")
                    self.is_continuous_capturing = False # 启动失败，重置状态
                    self.continuous_btn.config(text="开始连续截图")
                    return

                self.update_status("圆形连续截图已开始...")
                self.start_custom_circle_continuous_capture(custom_circle_params, on_capture)

            else:
                self.update_status("矩形连续截图已开始...")
                if not screenshot_manager.start_continuous_capture(on_capture):
                    self.update_status("启动矩形连续截图失败！")
                    self.is_continuous_capturing = False # 启动失败，重置状态
                    self.continuous_btn.config(text="开始连续截图")

        except Exception as e:
            self.update_status(f"连续截图错误: {e}")
            self.is_continuous_capturing = False # 出现异常，重置状态
            self.continuous_btn.config(text="开始连续截图")
    
    def start_custom_circle_continuous_capture(self, params, on_capture_callback):
        """启动自定义圆形连续截图"""
        import time
        
        def circle_capture_loop():
            while self.is_continuous_capturing:
                try:
                    result = screenshot_manager.capture_custom_circle(
                        params['center_x'], 
                        params['center_y'], 
                        params['radius']
                    )
                    if result and on_capture_callback:
                        on_capture_callback(result)
                    
                    # 等待指定间隔
                    time.sleep(screenshot_manager.capture_interval)
                    
                except Exception as e:
                    print(f"圆形连续截图错误: {e}")
                    break
        
        # 启动后台线程
        self.continuous_capture_thread = threading.Thread(target=circle_capture_loop, daemon=True)
        self.continuous_capture_thread.start()
        return True
    
    def stop_continuous_screenshot(self):
        """停止连续截图的核心逻辑"""
        # self.is_continuous_capturing 已经在 toggle 中设置
        screenshot_manager.stop_continuous_capture()
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
            
            # 保存圆形检测设置
            config_manager.set_circle_detection_enabled(self.circle_detection_var.get())
            
            hough_params = {
                'min_radius': int(self.min_radius_var.get()),
                'max_radius': int(self.max_radius_var.get()),
                'min_dist': int(self.min_dist_var.get()),
                'param2': int(self.param2_var.get())
            }
            config_manager.set_hough_params(hough_params)
            
            # 保存自定义圆形设置
            self.apply_custom_circle_settings()
            
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
            
            # 加载圆形检测设置
            circle_enabled = config_manager.is_circle_detection_enabled()
            self.circle_detection_var.set(circle_enabled)
            
            hough_params = config_manager.get_hough_params()
            self.min_radius_var.set(str(hough_params.get('min_radius', 10)))
            self.max_radius_var.set(str(hough_params.get('max_radius', 100)))
            self.min_dist_var.set(str(hough_params.get('min_dist', 50)))
            self.param2_var.set(str(hough_params.get('param2', 30)))
            
            # 加载自定义圆形设置
            custom_circle_params = config_manager.get_custom_circle_params()
            self.custom_circle_enabled_var.set(custom_circle_params.get('enabled', False))
            self.custom_circle_x_var.set(str(custom_circle_params.get('center_x', 100)))
            self.custom_circle_y_var.set(str(custom_circle_params.get('center_y', 100)))
            self.custom_circle_radius_var.set(str(custom_circle_params.get('radius', 50)))
            
            # 应用自定义圆形设置状态
            self.toggle_custom_circle()
            
            # 应用设置到管理器
            screenshot_manager.set_capture_region(x1, y1, x2, y2)
            screenshot_manager.set_save_directory(save_dir)
            screenshot_manager.set_capture_interval(interval)
            file_manager.set_base_directory(save_dir)
            
            # 设置圆形截图保存目录
            circle_save_dir = config_manager.get_circle_images_directory()
            circle_capture.set_save_directory(circle_save_dir)
            
            self.update_file_count()
            
        except Exception as e:
            self.update_status(f"加载设置失败: {e}")
    
    def update_latest_screenshot_info(self, result: dict):
        """更新最新截图详情显示"""
        try:
            # 保存最新截图路径
            self.latest_screenshot_path = result['file_path']
            self.open_latest_btn.config(state="normal")
            
            # 根据截图类型显示不同信息
            if result.get('screenshot_type') == 'custom_circle':
                center_info = f"圆心: ({result['circle_center'][0]}, {result['circle_center'][1]})"
                radius_info = f"半径: {result['circle_radius']}"
                file_info = f"文件: {result['file_size']/1024:.1f}KB"
                detail_text = f"最新圆形截图: {center_info} | {radius_info} | {file_info}"
            else:
                region_info = f"区域: {result['region'][0]},{result['region'][1]} - {result['region'][2]},{result['region'][3]}"
                size_info = f"大小: {result['size'][0]}×{result['size'][1]} ({result['pixels']:,}像素)"
                file_info = f"文件: {result['file_size']/1024:.1f}KB"
                detail_text = f"最新: {region_info} | {size_info} | {file_info}"
            
            self.latest_screenshot_var.set(detail_text)
        except Exception as e:
            print(f"更新截图详情失败: {e}")
    
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
    
    def open_latest_screenshot(self):
        """打开最新的截图文件"""
        if self.latest_screenshot_path and os.path.exists(self.latest_screenshot_path):
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(self.latest_screenshot_path)
                elif os.name == 'posix':  # macOS and Linux
                    import subprocess
                    subprocess.Popen(['xdg-open', self.latest_screenshot_path])
                self.update_status("已打开最新截图")
            except Exception as e:
                messagebox.showerror("错误", f"无法打开图片: {e}")
        else:
            messagebox.showwarning("警告", "截图文件不存在！")
    
    def on_close(self):
        """窗口关闭事件处理"""
        # 停止连续截图
        if self.is_continuous_capturing:
            self.stop_continuous_screenshot()
        
        # 停止坐标记录
        if hasattr(self, 'coordinate_recorder') and self.coordinate_recorder.is_recording():
            self.coordinate_recorder.stop_recording()
        
        # 保存设置
        try:
            self.save_settings()
        except Exception:
            pass
        
        # 关闭窗口
        self.root.destroy()
    
    def _safe_start_continuous(self):
        """线程安全地启动连续截图（供快捷键调用）"""
        if not self.is_continuous_capturing:
            self.start_continuous_screenshot()
        else:
            self.update_status("快捷键操作：连续截图已在运行")
            
    def _safe_stop_continuous(self):
        """线程安全地停止连续截图（供快捷键调用）"""
        if self.is_continuous_capturing:
            self.stop_continuous_screenshot()
        else:
            self.update_status("快捷键操作：连续截图未在运行")
    
    def run(self):
        """运行主窗口"""
        # 启动时自动应用在load_settings中加载的快捷键
        self.apply_hotkeys()
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
                
                success_msg = f"快捷键设置已应用 - 单次:{single_key} 连续:{continuous_key} 停止:{stop_key}"
                self.update_status(success_msg)
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
        
        # 核心修复：确保快捷键调用与GUI按钮完全相同的方法，并保证线程安全
        
        def single_screenshot_callback():
            # 直接调用单次截图按钮的方法
            self.root.after(0, self.single_screenshot)
        
        def toggle_continuous_callback():
            # 直接调用连续截图按钮的 toggle 方法
            self.root.after(0, self.toggle_continuous_screenshot)

        # 注册快捷键
        try:
            hotkey_manager.register_hotkey(single_key, single_screenshot_callback)
            # 让开始和停止快捷键都调用同一个切换方法
            hotkey_manager.register_hotkey(continuous_key, toggle_continuous_callback)
            hotkey_manager.register_hotkey(stop_key, toggle_continuous_callback)
            return True
        except Exception as e:
            print(f"注册快捷键失败: {e}")
            return False

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

    # === 圆形检测功能 ===
    
    def toggle_circle_detection(self):
        """切换圆形检测功能"""
        self.circle_detection_enabled = self.circle_detection_var.get()
        
        if self.circle_detection_enabled:
            # 启用圆形检测
            self.detect_circles_btn.config(state="normal")
            self.update_status("圆形检测功能已启用")
            
            # 应用配置到检测器
            self.apply_circle_detection_params()
        else:
            # 禁用圆形检测
            self.detect_circles_btn.config(state="disabled")
            self.clear_circles_btn.config(state="disabled")
            self.update_status("圆形检测功能已禁用")
            
            # 清除检测结果
            self.clear_detected_circles()
    
    def apply_circle_detection_params(self):
        """应用圆形检测参数"""
        try:
            # 获取GUI参数
            min_radius = int(self.min_radius_var.get())
            max_radius = int(self.max_radius_var.get())
            min_dist = int(self.min_dist_var.get())
            param2 = int(self.param2_var.get())
            
            # 创建检测参数
            params = DetectionParams(
                min_radius=min_radius,
                max_radius=max_radius,
                min_dist=min_dist,
                param2=param2
            )
            
            # 应用到检测器
            circle_detector.set_params(params)
            
        except ValueError as e:
            self.update_status(f"参数设置错误: {e}")
    
    def detect_circles_in_region(self):
        """在指定区域检测圆形"""
        def detect_task():
            try:
                self.root.after(0, lambda: self.update_status("正在检测圆形..."))
                
                # 检查OpenCV是否可用
                try:
                    import cv2
                except ImportError as e:
                    self.root.after(0, lambda: self.update_status("圆形检测功能需要OpenCV，请安装: pip install opencv-python"))
                    return
                
                # 获取截图区域
                x1, y1, x2, y2 = screenshot_manager.get_capture_region()
                
                # 创建临时截图用于检测（不保存到用户目录）
                import tempfile
                import os
                import time
                
                # 使用临时文件路径
                temp_dir = tempfile.gettempdir()
                temp_filename = f"circle_detection_temp_{int(time.time())}.png"
                temp_screenshot_path = os.path.join(temp_dir, temp_filename)
                
                # 截取区域图像到临时路径
                region_screenshot = screenshot_manager.capture_single(save_path=temp_screenshot_path)
                if not region_screenshot:
                    self.root.after(0, lambda: self.update_status("截图失败，请检查截图功能是否正常"))
                    return
                
                # 验证文件是否存在
                if not os.path.exists(region_screenshot['file_path']):
                    self.root.after(0, lambda: self.update_status(f"临时截图文件创建失败: {region_screenshot['file_path']}"))
                    return
                
                # 读取图像文件进行检测
                image = cv2.imread(region_screenshot['file_path'])
                if image is None:
                    self.root.after(0, lambda: self.update_status(f"图像读取失败，文件可能损坏: {region_screenshot['file_path']}"))
                    # 清理临时文件
                    try:
                        os.remove(region_screenshot['file_path'])
                    except:
                        pass
                    return
                
                # 应用检测参数
                self.apply_circle_detection_params()
                
                # 执行圆形检测
                detected_circles = circle_detector.detect_circles(image)
                
                # 过滤结果
                filtered_circles = circle_detector.filter_circles(detected_circles)
                
                # 调整坐标到全局坐标系
                global_circles = []
                for circle in filtered_circles:
                    global_circle = circle.__class__(
                        x=circle.x + x1,
                        y=circle.y + y1,
                        radius=circle.radius,
                        confidence=circle.confidence,
                        adjusted=circle.adjusted
                    )
                    global_circles.append(global_circle)
                
                # 更新检测结果
                self.current_detected_circles = global_circles
                
                # 如果检测到圆形，自动更新自定义圆形参数为第一个检测到的圆形
                if global_circles:
                    first_circle = global_circles[0]
                    self.root.after(0, lambda: self.custom_circle_x_var.set(str(first_circle.x)))
                    self.root.after(0, lambda: self.custom_circle_y_var.set(str(first_circle.y)))
                    self.root.after(0, lambda: self.custom_circle_radius_var.set(str(first_circle.radius)))
                    # 自动启用自定义圆形截图
                    self.root.after(0, lambda: self.custom_circle_enabled_var.set(True))
                    self.root.after(0, lambda: self.toggle_custom_circle())
                
                # 在主线程中更新UI
                self.root.after(0, lambda: self.update_circle_detection_results(len(global_circles)))
                
                # 清理临时文件
                try:
                    os.remove(region_screenshot['file_path'])
                except Exception as cleanup_error:
                    print(f"清理临时文件失败: {cleanup_error}")
                
            except Exception as e:
                # 发生异常时也要清理临时文件
                try:
                    if 'region_screenshot' in locals() and region_screenshot:
                        os.remove(region_screenshot['file_path'])
                except:
                    pass
                self.root.after(0, lambda: self.update_status(f"圆形检测失败: {e}"))
        
        # 在后台线程中执行检测
        import threading
        threading.Thread(target=detect_task, daemon=True).start()
    
    def capture_detected_circles(self):
        """截图检测到的圆形"""
        if not self.current_detected_circles:
            self.update_status("没有检测到圆形，请先进行圆形检测")
            return
        
        def capture_task():
            try:
                self.root.after(0, lambda: self.update_status("正在截图圆形..."))
                
                # 获取全屏截图用于圆形截图
                full_screenshot_result = screenshot_manager.capture_fullscreen()
                if not full_screenshot_result:
                    self.root.after(0, lambda: self.update_status("全屏截图失败"))
                    return
                
                # 读取全屏图像
                import cv2
                full_image = cv2.imread(full_screenshot_result['file_path'])
                if full_image is None:
                    self.root.after(0, lambda: self.update_status("全屏图像读取失败"))
                    return
                
                # 设置圆形截图保存目录
                circle_save_dir = config_manager.get_circle_images_directory()
                circle_capture.set_save_directory(circle_save_dir)
                
                # 执行圆形截图
                capture_results = circle_capture.capture_circles(
                    full_image, 
                    self.current_detected_circles,
                    save_individual=True,
                    save_combined=True
                )
                
                # 更新UI显示结果
                if capture_results["successful_captures"] > 0:
                    success_msg = f"成功截图 {capture_results['successful_captures']} 个圆形"
                    self.root.after(0, lambda: self.update_status(success_msg))
                    self.root.after(0, self.update_file_count)
                else:
                    self.root.after(0, lambda: self.update_status("圆形截图失败"))
                
            except Exception as e:
                self.root.after(0, lambda: self.update_status(f"圆形截图错误: {e}"))
        
        # 在后台线程中执行截图
        import threading
        threading.Thread(target=capture_task, daemon=True).start()
    
    def clear_detected_circles(self):
        """清除检测结果"""
        self.current_detected_circles = []
        self.circle_preview_image = None
        self.circle_results_var.set("暂无检测结果")
        self.clear_circles_btn.config(state="disabled")
        self.update_status("已清除圆形检测结果")
    
    def update_circle_detection_results(self, circle_count: int):
        """更新圆形检测结果显示"""
        if circle_count > 0:
            result_text = f"检测到 {circle_count} 个圆形"
            if circle_count > 5:
                result_text += f" (显示前5个，置信度: "
                top_confidences = [f"{c.confidence:.2f}" for c in self.current_detected_circles[:5]]
                result_text += ", ".join(top_confidences) + ")"
            else:
                confidences = [f"{c.confidence:.2f}" for c in self.current_detected_circles]
                result_text += f" (置信度: {', '.join(confidences)})"
            
            self.circle_results_var.set(result_text)
            self.clear_circles_btn.config(state="normal")
            self.update_status(f"圆形检测完成，发现 {circle_count} 个圆形")
        else:
            self.circle_results_var.set("未检测到圆形")
            self.clear_circles_btn.config(state="normal")
            self.update_status("圆形检测完成，未发现圆形")

    # === 自定义圆形截图功能 ===
    
    def toggle_custom_circle(self):
        """切换自定义圆形截图功能"""
        enabled = self.custom_circle_enabled_var.get()
        
        if enabled:
            # 启用自定义圆形截图
            self.custom_circle_x_entry.config(state="normal")
            self.custom_circle_y_entry.config(state="normal")
            self.record_circle_center_btn.config(state="normal")
            self.custom_circle_status_var.set("自定义圆形截图已启用")
            self.screenshot_mode_var.set("当前模式: 圆形截图")
            self.update_status("自定义圆形截图功能已启用")
        else:
            # 禁用自定义圆形截图
            self.custom_circle_x_entry.config(state="normal")  # 保持可编辑
            self.custom_circle_y_entry.config(state="normal")  # 保持可编辑
            self.record_circle_center_btn.config(state="disabled")
            self.custom_circle_status_var.set("")
            self.screenshot_mode_var.set("当前模式: 矩形截图")
            self.update_status("自定义圆形截图功能已禁用")
    
    def start_record_circle_center(self):
        """开始记录圆心坐标"""
        if self.coordinate_recorder.is_recording():
            self.update_status("坐标记录正在进行中，请先完成当前记录")
            return
        
        def on_center_recorded(x, y):
            # 在主线程中更新圆心坐标
            self.root.after(0, lambda: self._fill_circle_center_coordinate(x, y))
        
        def on_status_changed(message):
            # 在主线程中更新状态
            self.root.after(0, lambda: self.custom_circle_status_var.set(message))
        
        # 启动单次坐标记录
        if self.coordinate_recorder.start_single_recording(
            target_description="圆心",
            on_single_recorded=on_center_recorded,
            on_status_changed=on_status_changed
        ):
            self.update_status("已启动圆心坐标记录，请点击屏幕位置")
        else:
            messagebox.showerror("错误", "启动圆心坐标记录失败")
    
    def _fill_circle_center_coordinate(self, x, y):
        """填充圆心坐标到输入框"""
        try:
            self.custom_circle_x_var.set(str(x))
            self.custom_circle_y_var.set(str(y))
            
            # 更新状态
            self.custom_circle_status_var.set(f"圆心坐标已填充: ({x}, {y})")
            self.update_status(f"圆心坐标已填充: ({x}, {y})")
            
            print(f"✅ 圆心坐标已填充: ({x}, {y})")
            
        except Exception as e:
            print(f"❌ 填充圆心坐标失败: {e}")
            messagebox.showerror("错误", f"填充圆心坐标失败: {e}")
    
    def get_custom_circle_params(self):
        """获取当前自定义圆形参数"""
        try:
            enabled = self.custom_circle_enabled_var.get()
            center_x = int(self.custom_circle_x_var.get())
            center_y = int(self.custom_circle_y_var.get())
            radius = int(self.custom_circle_radius_var.get())
            
            return {
                "enabled": enabled,
                "center_x": center_x,
                "center_y": center_y,
                "radius": radius
            }
        except ValueError:
            return None
    
    def apply_custom_circle_settings(self):
        """应用自定义圆形设置"""
        params = self.get_custom_circle_params()
        if params:
            config_manager.set_custom_circle_params(params)
            return True
        return False

    # === 坐标记录功能 ===
    
    def start_record_topleft(self):
        """开始记录左上角坐标"""
        if self.coordinate_recorder.is_recording():
            self.update_status("坐标记录正在进行中，请先完成当前记录")
            return
        
        def on_single_recorded(x, y):
            # 在主线程中更新左上角坐标
            self.root.after(0, lambda: self._fill_topleft_coordinate(x, y))
        
        def on_status_changed(message):
            # 在主线程中更新状态
            self.root.after(0, lambda: self.coord_status_var.set(message))
        
        # 启动单次坐标记录
        if self.coordinate_recorder.start_single_recording(
            target_description="左上角",
            on_single_recorded=on_single_recorded,
            on_status_changed=on_status_changed
        ):
            self.update_status("已启动左上角坐标记录，请点击屏幕位置")
        else:
            messagebox.showerror("错误", "启动左上角坐标记录失败")
    
    def start_record_bottomright(self):
        """开始记录右下角坐标"""
        if self.coordinate_recorder.is_recording():
            self.update_status("坐标记录正在进行中，请先完成当前记录")
            return
        
        def on_single_recorded(x, y):
            # 在主线程中更新右下角坐标
            self.root.after(0, lambda: self._fill_bottomright_coordinate(x, y))
        
        def on_status_changed(message):
            # 在主线程中更新状态
            self.root.after(0, lambda: self.coord_status_var.set(message))
        
        # 启动单次坐标记录
        if self.coordinate_recorder.start_single_recording(
            target_description="右下角",
            on_single_recorded=on_single_recorded,
            on_status_changed=on_status_changed
        ):
            self.update_status("已启动右下角坐标记录，请点击屏幕位置")
        else:
            messagebox.showerror("错误", "启动右下角坐标记录失败")
    
    def _fill_topleft_coordinate(self, x, y):
        """填充左上角坐标到输入框"""
        try:
            self.x1_var.set(str(x))
            self.y1_var.set(str(y))
            
            # 更新状态
            self.coord_status_var.set(f"左上角坐标已填充: ({x}, {y})")
            self.update_status(f"左上角坐标已填充: ({x}, {y})")
            
            print(f"✅ 左上角坐标已填充: ({x}, {y})")
            
        except Exception as e:
            print(f"❌ 填充左上角坐标失败: {e}")
            messagebox.showerror("错误", f"填充左上角坐标失败: {e}")
    
    def _fill_bottomright_coordinate(self, x, y):
        """填充右下角坐标到输入框"""
        try:
            self.x2_var.set(str(x))
            self.y2_var.set(str(y))
            
            # 更新状态
            self.coord_status_var.set(f"右下角坐标已填充: ({x}, {y})")
            self.update_status(f"右下角坐标已填充: ({x}, {y})")
            
            print(f"✅ 右下角坐标已填充: ({x}, {y})")
            
        except Exception as e:
            print(f"❌ 填充右下角坐标失败: {e}")
            messagebox.showerror("错误", f"填充右下角坐标失败: {e}")
    



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