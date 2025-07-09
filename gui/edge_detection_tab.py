"""边缘检测标签页模块"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import os
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import numpy as np

# 改进的依赖检查和错误处理
def check_dependencies():
    """检查并报告依赖状态"""
    status = {
        'PIL_AVAILABLE': False,
        'CV2_AVAILABLE': False,
        'PIL_ERROR': None,
        'CV2_ERROR': None
    }
    
    # 检查 PIL
    try:
        from PIL import Image, ImageTk
        status['PIL_AVAILABLE'] = True
    except ImportError as e:
        status['PIL_ERROR'] = f"PIL 导入失败: {e}"
    except Exception as e:
        status['PIL_ERROR'] = f"PIL 检查异常: {e}"
    
    # 检查 OpenCV
    try:
        import cv2
        status['CV2_AVAILABLE'] = True
        # 测试基本功能
        cv2.__version__  # 确保模块正确加载
    except ImportError as e:
        status['CV2_ERROR'] = f"OpenCV 导入失败: {e}"
    except Exception as e:
        status['CV2_ERROR'] = f"OpenCV 检查异常: {e}"
    
    return status

# 执行依赖检查
DEPENDENCY_STATUS = check_dependencies()
PIL_AVAILABLE = DEPENDENCY_STATUS['PIL_AVAILABLE']
CV2_AVAILABLE = DEPENDENCY_STATUS['CV2_AVAILABLE']

# 只在成功时进行实际导入
if PIL_AVAILABLE:
    from PIL import Image, ImageTk
    
if CV2_AVAILABLE:
    import cv2
else:
    # 如果 OpenCV 不可用，记录详细错误信息
    print(f"⚠️ OpenCV 不可用: {DEPENDENCY_STATUS['CV2_ERROR']}")

if not PIL_AVAILABLE:
    print(f"⚠️ PIL 不可用: {DEPENDENCY_STATUS['PIL_ERROR']}")

from core.config import config_manager
from gui.image_canvas import EdgeDetectionCanvas
from utils.image_info import image_info_analyzer

# 条件导入边缘检测管理器
if CV2_AVAILABLE:
    from core.edge_detection import edge_detector, EdgeDetectionParams, EdgeDetectionResult
else:
    # 创建占位符类
    class EdgeDetectionParams:
        def __init__(self, **kwargs):
            pass
    
    class EdgeDetectionResult:
        def __init__(self, **kwargs):
            pass
    
    edge_detector = None


class EdgeDetectionTab:
    """边缘检测标签页类"""
    
    def __init__(self, parent):
        self.parent = parent
        
        # 保存依赖状态供外部访问
        self.dependency_status = DEPENDENCY_STATUS
        
        # 状态变量
        self.current_image_path = None
        self.current_result = None
        self.is_processing = False
        self.auto_detect_enabled = True
        
        # GUI变量
        self.threshold1_var = tk.IntVar(value=50)
        self.threshold2_var = tk.IntVar(value=150)
        self.aperture_var = tk.IntVar(value=3)
        self.l2_gradient_var = tk.BooleanVar(value=False)
        
        self.gaussian_blur_var = tk.BooleanVar(value=True)
        self.blur_kernel_var = tk.IntVar(value=5)
        self.median_filter_var = tk.BooleanVar(value=False)
        self.median_kernel_var = tk.IntVar(value=5)
        self.clahe_var = tk.BooleanVar(value=False)
        self.clahe_limit_var = tk.DoubleVar(value=2.0)
        
        self.morphology_var = tk.BooleanVar(value=False)
        self.morph_kernel_var = tk.IntVar(value=3)
        self.edge_thinning_var = tk.BooleanVar(value=False)
        self.remove_noise_var = tk.BooleanVar(value=True)
        
        self.display_mode_var = tk.StringVar(value="comparison")
        self.auto_detect_var = tk.BooleanVar(value=True)
        
        # 状态显示变量
        self.status_var = tk.StringVar(value="就绪")
        self.image_info_var = tk.StringVar(value="未加载图像")
        self.processing_info_var = tk.StringVar(value="")
        self.zoom_info_var = tk.StringVar(value="缩放: 100%")
        
        # 创建主框架
        self.main_frame = ttk.Frame(parent, padding="10")
        
        # 创建UI组件
        self.create_widgets()
        
        # 加载配置
        self.load_settings()
        
        # 绑定参数变化事件
        self.bind_parameter_events()
        
        # 检查依赖
        self.check_dependencies()
    
    def create_widgets(self):
        """创建UI组件"""
        # 配置网格权重
        self.main_frame.columnconfigure(0, weight=2)  # 左侧控制面板
        self.main_frame.columnconfigure(1, weight=3)  # 右侧图像显示
        self.main_frame.rowconfigure(0, weight=1)
        
        # === 左侧控制面板 ===
        self.create_control_panel()
        
        # === 右侧图像显示面板 ===
        self.create_image_panel()
        
        # === 底部状态栏 ===
        self.create_status_bar()
    
    def create_control_panel(self):
        """创建左侧控制面板"""
        control_frame = ttk.Frame(self.main_frame)
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        control_frame.columnconfigure(0, weight=1)
        
        row = 0
        
        # 图像导入区域
        import_frame = ttk.LabelFrame(control_frame, text="图像导入", padding="5")
        import_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        import_frame.columnconfigure(1, weight=1)
        
        ttk.Button(import_frame, text="选择图像", command=self.import_image).grid(row=0, column=0, padx=(0, 5))
        self.image_path_var = tk.StringVar(value="未选择文件")
        ttk.Label(import_frame, textvariable=self.image_path_var, foreground="blue").grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        row += 1
        
        # Canny参数设置
        canny_frame = ttk.LabelFrame(control_frame, text="Canny边缘检测参数", padding="5")
        canny_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        canny_frame.columnconfigure(1, weight=1)
        
        # 低阈值
        ttk.Label(canny_frame, text="低阈值:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        threshold1_frame = ttk.Frame(canny_frame)
        threshold1_frame.grid(row=0, column=1, sticky=(tk.W, tk.E))
        threshold1_frame.columnconfigure(0, weight=1)
        
        self.threshold1_scale = ttk.Scale(threshold1_frame, from_=1, to=255, variable=self.threshold1_var, orient=tk.HORIZONTAL)
        self.threshold1_scale.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.threshold1_label = ttk.Label(threshold1_frame, text="50")
        self.threshold1_label.grid(row=0, column=1)
        
        # 高阈值
        ttk.Label(canny_frame, text="高阈值:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        threshold2_frame = ttk.Frame(canny_frame)
        threshold2_frame.grid(row=1, column=1, sticky=(tk.W, tk.E))
        threshold2_frame.columnconfigure(0, weight=1)
        
        self.threshold2_scale = ttk.Scale(threshold2_frame, from_=1, to=255, variable=self.threshold2_var, orient=tk.HORIZONTAL)
        self.threshold2_scale.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.threshold2_label = ttk.Label(threshold2_frame, text="150")
        self.threshold2_label.grid(row=0, column=1)
        
        # Sobel算子大小
        ttk.Label(canny_frame, text="Sobel算子:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5))
        aperture_spinbox = ttk.Spinbox(canny_frame, from_=3, to=7, increment=2, textvariable=self.aperture_var, width=10)
        aperture_spinbox.grid(row=2, column=1, sticky=tk.W)
        
        # L2梯度
        ttk.Checkbutton(canny_frame, text="L2梯度计算", variable=self.l2_gradient_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        row += 1
        
        # 预处理参数
        preprocess_frame = ttk.LabelFrame(control_frame, text="预处理选项", padding="5")
        preprocess_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        preprocess_frame.columnconfigure(1, weight=1)
        
        # 高斯模糊
        ttk.Checkbutton(preprocess_frame, text="高斯模糊", variable=self.gaussian_blur_var).grid(row=0, column=0, sticky=tk.W)
        blur_kernel_spinbox = ttk.Spinbox(preprocess_frame, from_=3, to=15, increment=2, textvariable=self.blur_kernel_var, width=10)
        blur_kernel_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        # 中值滤波
        ttk.Checkbutton(preprocess_frame, text="中值滤波", variable=self.median_filter_var).grid(row=1, column=0, sticky=tk.W)
        median_kernel_spinbox = ttk.Spinbox(preprocess_frame, from_=3, to=15, increment=2, textvariable=self.median_kernel_var, width=10)
        median_kernel_spinbox.grid(row=1, column=1, sticky=tk.W, padx=(5, 0))
        
        # CLAHE直方图均衡化
        ttk.Checkbutton(preprocess_frame, text="CLAHE增强", variable=self.clahe_var).grid(row=2, column=0, sticky=tk.W)
        clahe_limit_spinbox = ttk.Spinbox(preprocess_frame, from_=1.0, to=10.0, increment=0.5, textvariable=self.clahe_limit_var, width=10, format="%.1f")
        clahe_limit_spinbox.grid(row=2, column=1, sticky=tk.W, padx=(5, 0))
        
        row += 1
        
        # 后处理参数
        postprocess_frame = ttk.LabelFrame(control_frame, text="后处理选项", padding="5")
        postprocess_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        postprocess_frame.columnconfigure(1, weight=1)
        
        # 形态学操作
        ttk.Checkbutton(postprocess_frame, text="形态学操作", variable=self.morphology_var).grid(row=0, column=0, sticky=tk.W)
        morph_kernel_spinbox = ttk.Spinbox(postprocess_frame, from_=3, to=9, increment=2, textvariable=self.morph_kernel_var, width=10)
        morph_kernel_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        # 其他选项
        ttk.Checkbutton(postprocess_frame, text="边缘细化", variable=self.edge_thinning_var).grid(row=1, column=0, columnspan=2, sticky=tk.W)
        ttk.Checkbutton(postprocess_frame, text="噪声去除", variable=self.remove_noise_var).grid(row=2, column=0, columnspan=2, sticky=tk.W)
        
        row += 1
        
        # 显示控制
        display_frame = ttk.LabelFrame(control_frame, text="显示控制", padding="5")
        display_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 显示模式
        ttk.Label(display_frame, text="显示模式:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        mode_frame = ttk.Frame(display_frame)
        mode_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Radiobutton(mode_frame, text="原图", variable=self.display_mode_var, value="original").pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="边缘", variable=self.display_mode_var, value="edges").pack(side=tk.LEFT, padx=(10, 0))
        ttk.Radiobutton(mode_frame, text="对比", variable=self.display_mode_var, value="comparison").pack(side=tk.LEFT, padx=(10, 0))
        
        # 自动检测
        ttk.Checkbutton(display_frame, text="实时检测", variable=self.auto_detect_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        row += 1
        
        # 操作按钮
        buttons_frame = ttk.LabelFrame(control_frame, text="操作", padding="5")
        buttons_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        button_grid_frame = ttk.Frame(buttons_frame)
        button_grid_frame.pack(fill=tk.X)
        
        ttk.Button(button_grid_frame, text="应用检测", command=self.apply_detection).grid(row=0, column=0, padx=(0, 5), pady=(0, 5))
        ttk.Button(button_grid_frame, text="保存结果", command=self.save_result).grid(row=0, column=1, padx=(0, 5), pady=(0, 5))
        ttk.Button(button_grid_frame, text="重置参数", command=self.reset_parameters).grid(row=1, column=0, padx=(0, 5))
        ttk.Button(button_grid_frame, text="清除图像", command=self.clear_image).grid(row=1, column=1, padx=(0, 5))
        ttk.Button(button_grid_frame, text="图像信息", command=self.show_image_info).grid(row=2, column=0, padx=(0, 5))
        ttk.Button(button_grid_frame, text="批处理", command=self.open_batch_dialog).grid(row=2, column=1, pady=(0, 0))
    
    def create_image_panel(self):
        """创建右侧图像显示面板"""
        image_frame = ttk.Frame(self.main_frame)
        image_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        image_frame.columnconfigure(0, weight=1)
        image_frame.rowconfigure(1, weight=1)
        
        # 图像控制工具栏
        toolbar_frame = ttk.Frame(image_frame)
        toolbar_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Button(toolbar_frame, text="适合窗口", command=self.zoom_to_fit).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="实际大小", command=self.zoom_to_actual).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="放大", command=self.zoom_in).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="缩小", command=self.zoom_out).pack(side=tk.LEFT, padx=(0, 5))
        
        # 缩放信息
        ttk.Label(toolbar_frame, textvariable=self.zoom_info_var).pack(side=tk.RIGHT)
        
        # 图像画布
        self.image_canvas = EdgeDetectionCanvas(image_frame, width=500, height=400)
        self.image_canvas.get_frame().grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 绑定画布事件
        self.image_canvas.on_zoom_changed = self.on_zoom_changed
        self.image_canvas.on_mode_changed = self.on_mode_changed
    
    def create_status_bar(self):
        """创建底部状态栏"""
        status_frame = ttk.Frame(self.main_frame)
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        status_frame.columnconfigure(1, weight=1)
        
        # 状态信息
        ttk.Label(status_frame, text="状态:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(status_frame, textvariable=self.status_var, foreground="blue").grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        # 图像信息
        ttk.Label(status_frame, textvariable=self.image_info_var, foreground="green").grid(row=0, column=2, sticky=tk.E, padx=(20, 0))
        
        # 处理信息
        ttk.Label(status_frame, textvariable=self.processing_info_var, foreground="orange").grid(row=1, column=0, columnspan=3, sticky=tk.W)
    
    def bind_parameter_events(self):
        """绑定参数变化事件"""
        # 阈值变化时更新标签
        self.threshold1_var.trace('w', self.on_threshold1_changed)
        self.threshold2_var.trace('w', self.on_threshold2_changed)
        
        # 显示模式变化
        self.display_mode_var.trace('w', self.on_display_mode_changed)
        
        # 自动检测变化
        self.auto_detect_var.trace('w', self.on_auto_detect_changed)
        
        # 参数变化时自动检测（如果启用）
        parameters = [
            self.threshold1_var, self.threshold2_var, self.aperture_var, self.l2_gradient_var,
            self.gaussian_blur_var, self.blur_kernel_var, self.median_filter_var, self.median_kernel_var,
            self.clahe_var, self.clahe_limit_var, self.morphology_var, self.morph_kernel_var,
            self.edge_thinning_var, self.remove_noise_var
        ]
        
        for param in parameters:
            param.trace('w', self.on_parameter_changed)
    
    def check_dependencies(self):
        """检查依赖项 - 增强版本"""
        if not CV2_AVAILABLE:
            error_msg = DEPENDENCY_STATUS.get('CV2_ERROR', 'OpenCV 不可用')
            self.status_var.set(f"错误: {error_msg}")
            
            # 显示详细的依赖状态信息
            self.show_dependency_status()
            
            # 禁用相关控件
            self.disable_opencv_dependent_controls()
            
        elif not PIL_AVAILABLE:
            error_msg = DEPENDENCY_STATUS.get('PIL_ERROR', 'PIL 不可用')
            self.status_var.set(f"警告: {error_msg}")
        else:
            self.status_var.set("就绪 - 所有依赖项正常")

    def show_dependency_status(self):
        """显示依赖状态详情"""
        try:
            # 在图像信息区域显示依赖状态
            status_text = "依赖检查结果:\n"
            
            if CV2_AVAILABLE:
                status_text += "✅ OpenCV: 正常\n"
            else:
                status_text += f"❌ OpenCV: {DEPENDENCY_STATUS.get('CV2_ERROR', '不可用')}\n"
            
            if PIL_AVAILABLE:
                status_text += "✅ PIL: 正常\n"
            else:
                status_text += f"❌ PIL: {DEPENDENCY_STATUS.get('PIL_ERROR', '不可用')}\n"
            
            # 添加解决建议
            if not CV2_AVAILABLE:
                status_text += "\n解决方案:\n"
                status_text += "1. pip install opencv-python\n"
                status_text += "2. 确认虚拟环境已激活\n"
                status_text += "3. 重启应用程序"
            
            self.image_info_var.set(status_text)
            
        except Exception as e:
            print(f"显示依赖状态失败: {e}")

    def disable_opencv_dependent_controls(self):
        """禁用依赖 OpenCV 的控件"""
        try:
            # 禁用相关控件
            controls_to_disable = []
            
            # 遍历主框架的子组件
            for child in self.main_frame.winfo_children():
                if isinstance(child, ttk.LabelFrame):
                    # 跳过图像导入区域，让用户仍能看到错误信息
                    if "图像导入" not in child.cget("text"):
                        controls_to_disable.append(child)
                        for widget in child.winfo_children():
                            if hasattr(widget, 'configure'):
                                try:
                                    widget.configure(state='disabled')
                                except:
                                    pass
            
            print(f"已禁用 {len(controls_to_disable)} 个控件组")
            
        except Exception as e:
            print(f"禁用控件失败: {e}")
    
    def get_frame(self) -> ttk.Frame:
        """获取主框架"""
        return self.main_frame
    
    def import_image(self):
        """导入图像"""
        if not CV2_AVAILABLE:
            error_msg = f"OpenCV 不可用，无法导入图像\n\n详细信息:\n{DEPENDENCY_STATUS.get('CV2_ERROR', '未知错误')}"
            messagebox.showerror("错误", error_msg)
            return
        
        file_types = [
            ("图像文件", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif"),
            ("PNG文件", "*.png"),
            ("JPEG文件", "*.jpg *.jpeg"),
            ("BMP文件", "*.bmp"),
            ("TIFF文件", "*.tiff *.tif"),
            ("所有文件", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="选择图像文件",
            filetypes=file_types
        )
        
        if file_path:
            self.load_image(file_path)
    
    def diagnose_image_error(self, file_path: str) -> str:
        """诊断图像加载错误"""
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return "文件不存在"
            
            # 检查文件权限
            if not os.access(file_path, os.R_OK):
                return "文件没有读取权限"
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return "文件为空"
            
            # 检查文件扩展名
            ext = Path(file_path).suffix.lower()
            supported_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']
            if ext not in supported_formats:
                return f"不支持的文件格式: {ext}"
            
            # 检查是否为PNG文件
            if ext == '.png':
                try:
                    # 检查PNG文件头
                    with open(file_path, 'rb') as f:
                        header = f.read(8)
                        if header != b'\x89PNG\r\n\x1a\n':
                            return "PNG文件头损坏"
                except Exception:
                    return "PNG文件无法读取"
            
            # 尝试使用PIL加载
            if PIL_AVAILABLE:
                try:
                    from PIL import Image as PILImage
                    with PILImage.open(file_path) as pil_img:
                        width, height = pil_img.size
                        # 检查图像尺寸
                        if width <= 0 or height <= 0:
                            return f"无效的图像尺寸: {width}x{height}"
                        
                        # 检查内存需求
                        estimated_memory_mb = (width * height * 4) / (1024 * 1024)  # RGBA
                        if estimated_memory_mb > 512:  # 512MB限制
                            return f"图像过大，预估内存需求: {estimated_memory_mb:.1f}MB"
                        
                        return "PIL可以加载，但OpenCV加载失败"
                except Exception as e:
                    return f"PIL加载失败: {str(e)}"
            
            return "未知错误"
            
        except Exception as e:
            return f"诊断过程出错: {str(e)}"
    
    def load_image_with_fallback(self, file_path: str) -> Optional[np.ndarray]:
        """使用回退机制加载图像"""
        try:
            # 首先尝试OpenCV加载
            image = cv2.imread(file_path)
            if image is not None:
                return image
            
            # OpenCV失败，尝试PIL加载
            if not PIL_AVAILABLE:
                return None
            
            try:
                from PIL import Image as PILImage
                pil_image = PILImage.open(file_path)
                
                # 检查图像尺寸
                width, height = pil_image.size
                if width > 8192 or height > 8192:
                    # 自动缩放大图像
                    max_size = 4096
                    if width > height:
                        new_width = max_size
                        new_height = int(height * max_size / width)
                    else:
                        new_height = max_size
                        new_width = int(width * max_size / height)
                    
                    pil_image = pil_image.resize((new_width, new_height), PILImage.LANCZOS)
                    print(f"自动缩放大图像: {width}x{height} -> {new_width}x{new_height}")
                
                # 转换为OpenCV格式
                if pil_image.mode == 'RGBA':
                    pil_image = pil_image.convert('RGB')
                elif pil_image.mode == 'P':
                    pil_image = pil_image.convert('RGB')
                elif pil_image.mode == 'L':
                    pil_image = pil_image.convert('RGB')
                
                # 转换为NumPy数组
                image_array = np.array(pil_image)
                # RGB到BGR
                if len(image_array.shape) == 3:
                    image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
                
                return image_array
                
            except Exception as e:
                print(f"PIL加载失败: {e}")
                return None
                
        except Exception as e:
            print(f"图像加载异常: {e}")
            return None
    
    def load_image(self, file_path: str):
        """加载图像（增强错误处理）"""
        try:
            self.status_var.set("正在加载图像...")
            
            # 使用增强的加载方法
            image = self.load_image_with_fallback(file_path)
            
            if image is None:
                # 诊断具体错误原因
                error_reason = self.diagnose_image_error(file_path)
                
                # 构建详细错误信息
                file_info = ""
                try:
                    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    file_ext = Path(file_path).suffix.lower()
                    file_info = f"\n\n文件信息:\n- 文件大小: {file_size_mb:.2f}MB\n- 文件格式: {file_ext}\n- 文件路径: {file_path}"
                except Exception:
                    pass
                
                error_msg = f"无法加载图像文件\n\n原因: {error_reason}{file_info}\n\n建议操作:\n1. 检查文件是否损坏\n2. 尝试使用图像编辑软件重新保存\n3. 转换为其他格式再试"
                
                messagebox.showerror("图像加载失败", error_msg)
                self.status_var.set("图像加载失败")
                return
            
            self.current_image_path = file_path
            
            # 更新UI显示
            filename = os.path.basename(file_path)
            self.image_path_var.set(filename)
            
            # 使用增强的图像信息分析
            try:
                detailed_info = image_info_analyzer.analyze_image_file(file_path)
                
                # 提取关键信息
                image_info = detailed_info.get('image_info', {})
                memory_info = detailed_info.get('memory_info', {})
                file_info = detailed_info.get('file_info', {})
                
                # 构建显示文本
                width = image_info.get('width', image.shape[1])
                height = image_info.get('height', image.shape[0])
                channels = image_info.get('channels', 1 if len(image.shape) == 2 else image.shape[2])
                
                file_size_mb = file_info.get('file_size_mb', 0)
                memory_mb = memory_info.get('base_memory_mb', 0)
                memory_level = memory_info.get('memory_level', '未知')
                
                # 检查兼容性
                compatibility = detailed_info.get('compatibility_info', {})
                opencv_ok = compatibility.get('opencv_support', True)
                pil_ok = compatibility.get('pil_support', True)
                compat_text = f"OpenCV({'\u2713' if opencv_ok else '\u2717'}) PIL({'\u2713' if pil_ok else '\u2717'})"
                
                info_text = f"图像: {width}×{height}×{channels} | 文件: {file_size_mb:.1f}MB | 内存: {memory_mb:.1f}MB({memory_level}) | {compat_text}"
                
                # 显示警告信息
                recommendations = detailed_info.get('recommendations', [])
                if recommendations:
                    warning_text = " | 警告: " + recommendations[0]
                    if len(info_text + warning_text) < 150:  # 限制显示长度
                        info_text += warning_text
                
                self.image_info_var.set(info_text)
                
                # 如果有重要建议，显示提示
                if any('超大' in rec or '较大' in rec for rec in recommendations):
                    self.status_var.set(f"已加载图像: {filename} (注意: 图像较大)")
                
            except Exception as e:
                # 回退到简单信息显示
                height, width = image.shape[:2]
                channels = 1 if len(image.shape) == 2 else image.shape[2]
                file_size_kb = os.path.getsize(file_path) / 1024
                memory_mb = (width * height * channels * 4) / (1024 * 1024)
                info_text = f"图像: {width}×{height}×{channels} | 文件: {file_size_kb:.1f}KB | 内存: {memory_mb:.1f}MB"
                self.image_info_var.set(info_text)
                print(f"图像信息分析失败: {e}")
            
            # 根据图像大小调整画布内存限制
            try:
                memory_mb = memory_info.get('base_memory_mb', (width * height * channels * 4) / (1024 * 1024))
                if memory_mb > 256:
                    # 大图像，调整画布内存限制
                    canvas_memory_limit = min(512, memory_mb * 2)
                    self.image_canvas.set_memory_limit(canvas_memory_limit)
                    print(f"检测到大图像，调整画布内存限制到 {canvas_memory_limit:.1f}MB")
            except Exception:
                # 使用默认计算
                height, width = image.shape[:2]
                channels = 1 if len(image.shape) == 2 else image.shape[2]
                memory_mb = (width * height * channels * 4) / (1024 * 1024)
                if memory_mb > 256:
                    canvas_memory_limit = min(512, memory_mb * 2)
                    self.image_canvas.set_memory_limit(canvas_memory_limit)
            
            # 设置到画布
            self.image_canvas.set_images(original=image)
            
            # 自动应用检测
            if self.auto_detect_var.get():
                self.apply_detection()
            
            self.status_var.set(f"已加载图像: {filename}")
            
        except MemoryError:
            error_msg = "内存不足，无法加载此图像\n\n建议操作:\n1. 关闭其他应用程序释放内存\n2. 使用图像编辑软件缩小图像尺寸\n3. 重启应用程序"
            messagebox.showerror("内存不足", error_msg)
            self.status_var.set("内存不足")
        except Exception as e:
            error_msg = f"加载图像时发生未知错误\n\n错误详情: {str(e)}\n\n请检查文件是否损坏或者联系技术支持"
            messagebox.showerror("加载失败", error_msg)
            self.status_var.set("图像加载失败")
    
    def get_current_params(self) -> EdgeDetectionParams:
        """获取当前参数"""
        return EdgeDetectionParams(
            threshold1=self.threshold1_var.get(),
            threshold2=self.threshold2_var.get(),
            aperture_size=self.aperture_var.get(),
            l2_gradient=self.l2_gradient_var.get(),
            gaussian_blur=self.gaussian_blur_var.get(),
            blur_kernel_size=self.blur_kernel_var.get(),
            median_filter=self.median_filter_var.get(),
            median_kernel_size=self.median_kernel_var.get(),
            clahe_enabled=self.clahe_var.get(),
            clahe_clip_limit=self.clahe_limit_var.get(),
            morphology_enabled=self.morphology_var.get(),
            morph_kernel_size=self.morph_kernel_var.get(),
            edge_thinning=self.edge_thinning_var.get(),
            remove_noise=self.remove_noise_var.get()
        )
    
    def apply_detection(self):
        """应用边缘检测（增强错误处理）"""
        if not CV2_AVAILABLE or edge_detector is None:
            error_msg = "边缘检测功能不可用\n\n"
            if not CV2_AVAILABLE:
                error_msg += f"OpenCV 状态: {DEPENDENCY_STATUS.get('CV2_ERROR', '不可用')}\n"
            if edge_detector is None:
                error_msg += "边缘检测器未初始化\n"
            error_msg += "\n请确保 OpenCV 正确安装后重启应用程序"
            messagebox.showerror("错误", error_msg)
            return
        
        if self.current_image_path is None:
            messagebox.showwarning("警告", "请先导入图像")
            return
        
        if self.is_processing:
            return
        
        def detect_task():
            try:
                self.is_processing = True
                self.status_var.set("正在处理...")
                
                # 使用增强加载方法重新加载图像
                image = self.load_image_with_fallback(self.current_image_path)
                if image is None:
                    self.status_var.set("图像读取失败")
                    return
                
                # 检查图像尺寸和内存需求
                height, width = image.shape[:2]
                estimated_memory_mb = (width * height * 12) / (1024 * 1024)  # 边缘检测需要更多内存
                
                if estimated_memory_mb > 1024:  # 1GB限制
                    self.status_var.set("图像过大，无法处理")
                    messagebox.showerror("图像过大", f"图像尺寸 {width}x{height} 过大\n预估内存需求: {estimated_memory_mb:.1f}MB\n\n请缩小图像尺寸后再试")
                    return
                
                # 设置参数
                params = self.get_current_params()
                edge_detector.set_params(params)
                
                # 执行检测
                result = edge_detector.detect_edges_sync(image)
                
                # 更新显示
                self.current_result = result
                self.image_canvas.set_images(original=result.original_image, edges=result.edge_image)
                
                # 更新处理信息
                self.processing_info_var.set(
                    f"处理时间: {result.processing_time:.3f}秒 | "
                    f"边缘像素: {result.edge_count:,} | "
                    f"边缘比例: {result.edge_count/result.original_image.size*100:.2f}% | "
                    f"内存: {estimated_memory_mb:.1f}MB"
                )
                
                self.status_var.set("边缘检测完成")
                
            except MemoryError:
                self.status_var.set("内存不足")
                messagebox.showerror("内存不足", "处理过程中内存不足\n\n建议操作:\n1. 关闭其他应用程序\n2. 缩小图像尺寸\n3. 重启应用程序")
            except Exception as e:
                error_msg = f"处理失败: {str(e)}"
                self.status_var.set(error_msg)
                
                # 提供更详细的错误信息
                if "memory" in str(e).lower() or "allocation" in str(e).lower():
                    messagebox.showerror("内存错误", f"内存分配失败\n\n错误详情: {e}\n\n请尝试缩小图像尺寸")
                else:
                    print(f"边缘检测错误: {e}")
            finally:
                self.is_processing = False
        
        # 在后台线程中执行
        threading.Thread(target=detect_task, daemon=True).start()
    
    def save_result(self):
        """保存检测结果"""
        if self.current_result is None:
            messagebox.showwarning("警告", "没有可保存的结果")
            return
        
        # 获取保存路径
        save_paths = config_manager.get_edge_save_paths()
        
        file_types = [
            ("PNG文件", "*.png"),
            ("JPEG文件", "*.jpg"),
            ("BMP文件", "*.bmp"),
            ("所有文件", "*.*")
        ]
        
        file_path = filedialog.asksaveasfilename(
            title="保存边缘检测结果",
            defaultextension=".png",
            filetypes=file_types,
            initialdir=save_paths.get('edge_results', 'screenshots/edge_detection/edges')
        )
        
        if file_path:
            try:
                # 根据显示模式选择要保存的图像
                if self.display_mode_var.get() == "original":
                    save_image = self.current_result.original_image
                elif self.display_mode_var.get() == "edges":
                    save_image = self.current_result.edge_image
                else:  # comparison
                    save_image = edge_detector.create_comparison_image(self.current_result, "side_by_side")
                
                # 保存图像
                cv2.imwrite(file_path, save_image)
                
                self.status_var.set(f"结果已保存: {os.path.basename(file_path)}")
                messagebox.showinfo("成功", f"结果已保存到:\n{file_path}")
                
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {e}")
                self.status_var.set("保存失败")
    
    def reset_parameters(self):
        """重置参数"""
        if messagebox.askyesno("确认", "确定要重置所有参数吗？"):
            # 重置为默认值
            self.threshold1_var.set(50)
            self.threshold2_var.set(150)
            self.aperture_var.set(3)
            self.l2_gradient_var.set(False)
            
            self.gaussian_blur_var.set(True)
            self.blur_kernel_var.set(5)
            self.median_filter_var.set(False)
            self.median_kernel_var.set(5)
            self.clahe_var.set(False)
            self.clahe_limit_var.set(2.0)
            
            self.morphology_var.set(False)
            self.morph_kernel_var.set(3)
            self.edge_thinning_var.set(False)
            self.remove_noise_var.set(True)
            
            self.status_var.set("参数已重置")
    
    def clear_image(self):
        """清除图像"""
        if messagebox.askyesno("确认", "确定要清除当前图像吗？"):
            self.current_image_path = None
            self.current_result = None
            self.image_path_var.set("未选择文件")
            self.image_info_var.set("未加载图像")
            self.processing_info_var.set("")
            self.image_canvas.clear()
            self.status_var.set("已清除图像")
    
    def zoom_to_fit(self):
        """缩放到适合窗口"""
        self.image_canvas.zoom_to_fit()
    
    def zoom_to_actual(self):
        """缩放到实际大小"""
        self.image_canvas.zoom_to_actual_size()
    
    def zoom_in(self):
        """放大"""
        self.image_canvas.zoom_in()
    
    def zoom_out(self):
        """缩小"""
        self.image_canvas.zoom_out()
    
    # === 事件处理方法 ===
    
    def on_threshold1_changed(self, *args):
        """低阈值变化事件"""
        value = self.threshold1_var.get()
        self.threshold1_label.config(text=str(value))
        
        # 确保低阈值小于高阈值
        if value >= self.threshold2_var.get():
            self.threshold2_var.set(value + 1)
    
    def on_threshold2_changed(self, *args):
        """高阈值变化事件"""
        value = self.threshold2_var.get()
        self.threshold2_label.config(text=str(value))
        
        # 确保高阈值大于低阈值
        if value <= self.threshold1_var.get():
            self.threshold1_var.set(value - 1)
    
    def on_display_mode_changed(self, *args):
        """显示模式变化事件"""
        mode = self.display_mode_var.get()
        self.image_canvas.set_display_mode(mode)
    
    def on_auto_detect_changed(self, *args):
        """自动检测变化事件"""
        self.auto_detect_enabled = self.auto_detect_var.get()
        if self.auto_detect_enabled and self.current_image_path:
            self.apply_detection()
    
    def on_parameter_changed(self, *args):
        """参数变化事件"""
        if self.auto_detect_enabled and self.current_image_path and not self.is_processing:
            # 延迟执行，避免频繁处理
            if hasattr(self, '_param_change_after_id'):
                self.main_frame.after_cancel(self._param_change_after_id)
            self._param_change_after_id = self.main_frame.after(300, self.apply_detection)
    
    def on_zoom_changed(self, zoom_factor: float):
        """缩放变化事件"""
        self.zoom_info_var.set(f"缩放: {zoom_factor*100:.0f}%")
    
    def on_mode_changed(self, mode: str):
        """显示模式变化事件"""
        self.display_mode_var.set(mode)
    
    # === 配置管理 ===
    
    def load_settings(self):
        """加载设置"""
        try:
            # 加载Canny参数
            canny_params = config_manager.get_canny_params()
            self.threshold1_var.set(canny_params.get('threshold1', 50))
            self.threshold2_var.set(canny_params.get('threshold2', 150))
            self.aperture_var.set(canny_params.get('aperture_size', 3))
            self.l2_gradient_var.set(canny_params.get('l2_gradient', False))
            
            # 加载预处理参数
            preprocess_params = config_manager.get_edge_preprocessing_params()
            self.gaussian_blur_var.set(preprocess_params.get('gaussian_blur', True))
            self.blur_kernel_var.set(preprocess_params.get('blur_kernel_size', 5))
            self.median_filter_var.set(preprocess_params.get('median_filter', False))
            self.median_kernel_var.set(preprocess_params.get('median_kernel_size', 5))
            self.clahe_var.set(preprocess_params.get('clahe_enabled', False))
            self.clahe_limit_var.set(preprocess_params.get('clahe_clip_limit', 2.0))
            
            # 加载后处理参数
            postprocess_params = config_manager.get_edge_postprocessing_params()
            self.morphology_var.set(postprocess_params.get('morphology_enabled', False))
            self.morph_kernel_var.set(postprocess_params.get('morph_kernel_size', 3))
            self.edge_thinning_var.set(postprocess_params.get('edge_thinning', False))
            self.remove_noise_var.set(postprocess_params.get('remove_noise', True))
            
            # 加载显示参数
            display_params = config_manager.get_edge_display_params()
            self.display_mode_var.set(display_params.get('view_mode', 'comparison'))
            
        except Exception as e:
            print(f"加载边缘检测设置失败: {e}")
    
    def save_settings(self):
        """保存设置"""
        try:
            # 保存Canny参数
            canny_params = {
                'threshold1': self.threshold1_var.get(),
                'threshold2': self.threshold2_var.get(),
                'aperture_size': self.aperture_var.get(),
                'l2_gradient': self.l2_gradient_var.get()
            }
            config_manager.set_canny_params(canny_params)
            
            # 保存预处理参数
            preprocess_params = {
                'gaussian_blur': self.gaussian_blur_var.get(),
                'blur_kernel_size': self.blur_kernel_var.get(),
                'median_filter': self.median_filter_var.get(),
                'median_kernel_size': self.median_kernel_var.get(),
                'clahe_enabled': self.clahe_var.get(),
                'clahe_clip_limit': self.clahe_limit_var.get()
            }
            config_manager.set_edge_preprocessing_params(preprocess_params)
            
            # 保存后处理参数
            postprocess_params = {
                'morphology_enabled': self.morphology_var.get(),
                'morph_kernel_size': self.morph_kernel_var.get(),
                'edge_thinning': self.edge_thinning_var.get(),
                'remove_noise': self.remove_noise_var.get()
            }
            config_manager.set_edge_postprocessing_params(postprocess_params)
            
            # 保存显示参数
            display_params = {
                'view_mode': self.display_mode_var.get()
            }
            config_manager.set_edge_display_params(display_params)
            
            config_manager.save_config()
            
        except Exception as e:
            print(f"保存边缘检测设置失败: {e}")
    
    def open_batch_dialog(self):
        """打开批处理对话框"""
        if not CV2_AVAILABLE:
            error_msg = f"批处理功能需要 OpenCV 支持\n\n详细信息:\n{DEPENDENCY_STATUS.get('CV2_ERROR', '未知错误')}"
            messagebox.showerror("错误", error_msg)
            return
        
        try:
            # 导入批处理模块
            from core.batch_processor import batch_processor, BatchConfig
            
            # 创建批处理对话框
            self.batch_dialog = BatchProcessDialog(self.parent, self.get_current_params())
            
        except ImportError as e:
            messagebox.showerror("错误", f"批处理功能不可用: {e}")
        except Exception as e:
            messagebox.showerror("错误", f"打开批处理对话框失败: {e}")
    
    def show_image_info(self):
        """显示详细图像信息"""
        if self.current_image_path is None:
            messagebox.showwarning("警告", "请先导入图像")
            return
        
        try:
            # 创建信息窗口
            info_window = ImageInfoWindow(self.parent, self.current_image_path)
        except Exception as e:
            messagebox.showerror("错误", f"显示图像信息失败: {e}")


class BatchProcessDialog:
    """批处理对话框"""
    
    def __init__(self, parent, default_params):
        self.parent = parent
        self.default_params = default_params
        self.is_processing = False
        
        # 创建对话框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("批量边缘检测")
        self.dialog.geometry("600x500")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 批处理配置变量
        self.input_dir_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()
        self.recursive_var = tk.BooleanVar(value=False)
        self.overwrite_var = tk.BooleanVar(value=False)
        self.save_original_var = tk.BooleanVar(value=False)
        self.save_edges_var = tk.BooleanVar(value=True)
        self.save_comparison_var = tk.BooleanVar(value=False)
        self.max_workers_var = tk.IntVar(value=4)
        
        # 进度变量
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="就绪")
        self.current_file_var = tk.StringVar()
        self.time_info_var = tk.StringVar()
        
        # 创建UI
        self.create_dialog_ui()
        
        # 居中显示
        self.center_dialog()
    
    def create_dialog_ui(self):
        """创建对话框UI"""
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 配置网格权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)  # 进度区域可扩展
        
        # === 输入输出设置 ===
        io_frame = ttk.LabelFrame(main_frame, text="输入输出设置", padding="5")
        io_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        io_frame.columnconfigure(1, weight=1)
        
        # 输入目录
        ttk.Label(io_frame, text="输入目录:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        input_frame = ttk.Frame(io_frame)
        input_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        input_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(input_frame, textvariable=self.input_dir_var).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(input_frame, text="浏览", command=self.browse_input_directory).grid(row=0, column=1)
        
        # 输出目录
        ttk.Label(io_frame, text="输出目录:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        output_frame = ttk.Frame(io_frame)
        output_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        output_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(output_frame, textvariable=self.output_dir_var).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(output_frame, text="浏览", command=self.browse_output_directory).grid(row=0, column=1)
        
        # === 处理选项 ===
        options_frame = ttk.LabelFrame(main_frame, text="处理选项", padding="5")
        options_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 选项布局
        options_grid = ttk.Frame(options_frame)
        options_grid.pack(fill=tk.X)
        
        ttk.Checkbutton(options_grid, text="递归扫描子目录", variable=self.recursive_var).grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        ttk.Checkbutton(options_grid, text="覆盖现有文件", variable=self.overwrite_var).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Checkbutton(options_grid, text="保存原图", variable=self.save_original_var).grid(row=1, column=0, sticky=tk.W, padx=(0, 20))
        ttk.Checkbutton(options_grid, text="保存边缘图", variable=self.save_edges_var).grid(row=1, column=1, sticky=tk.W)
        
        ttk.Checkbutton(options_grid, text="保存对比图", variable=self.save_comparison_var).grid(row=2, column=0, sticky=tk.W, padx=(0, 20))
        
        # 最大工作线程数
        worker_frame = ttk.Frame(options_grid)
        worker_frame.grid(row=2, column=1, sticky=tk.W)
        ttk.Label(worker_frame, text="工作线程:").pack(side=tk.LEFT)
        ttk.Spinbox(worker_frame, from_=1, to=8, textvariable=self.max_workers_var, width=5).pack(side=tk.LEFT, padx=(5, 0))
        
        # === 进度和控制 ===
        progress_frame = ttk.LabelFrame(main_frame, text="处理进度", padding="5")
        progress_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        # 进度条
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, mode='determinate')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # 状态信息
        ttk.Label(progress_frame, textvariable=self.status_var).grid(row=1, column=0, sticky=tk.W)
        ttk.Label(progress_frame, textvariable=self.current_file_var, foreground="blue").grid(row=2, column=0, sticky=tk.W)
        ttk.Label(progress_frame, textvariable=self.time_info_var, foreground="green").grid(row=3, column=0, sticky=tk.W)
        
        # === 控制按钮 ===
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        self.start_btn = ttk.Button(button_frame, text="开始处理", command=self.start_batch_processing)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.pause_btn = ttk.Button(button_frame, text="暂停", command=self.pause_processing, state="disabled")
        self.pause_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.cancel_btn = ttk.Button(button_frame, text="取消", command=self.cancel_processing, state="disabled")
        self.cancel_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="关闭", command=self.close_dialog).pack(side=tk.RIGHT)
        
        # 设置默认目录
        self.set_default_directories()
    
    def center_dialog(self):
        """居中显示对话框"""
        self.dialog.update_idletasks()
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"+{x}+{y}")
    
    def set_default_directories(self):
        """设置默认目录"""
        try:
            from core.config import config_manager
            save_paths = config_manager.get_edge_save_paths()
            
            # 设置默认输出目录
            default_output = save_paths.get('edge_results', 'screenshots/edge_detection/edges')
            self.output_dir_var.set(default_output)
            
        except Exception as e:
            print(f"设置默认目录失败: {e}")
    
    def browse_input_directory(self):
        """浏览输入目录"""
        directory = filedialog.askdirectory(title="选择输入目录")
        if directory:
            self.input_dir_var.set(directory)
    
    def browse_output_directory(self):
        """浏览输出目录"""
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_dir_var.set(directory)
    
    def start_batch_processing(self):
        """开始批处理"""
        # 验证输入
        if not self.input_dir_var.get():
            messagebox.showwarning("警告", "请选择输入目录")
            return
        
        if not self.output_dir_var.get():
            messagebox.showwarning("警告", "请选择输出目录")
            return
        
        if not (self.save_original_var.get() or self.save_edges_var.get() or self.save_comparison_var.get()):
            messagebox.showwarning("警告", "请至少选择一种保存选项")
            return
        
        try:
            from core.batch_processor import batch_processor, BatchConfig
            
            # 创建批处理配置
            config = BatchConfig(
                input_directory=self.input_dir_var.get(),
                output_directory=self.output_dir_var.get(),
                recursive=self.recursive_var.get(),
                overwrite_existing=self.overwrite_var.get(),
                save_original=self.save_original_var.get(),
                save_edges=self.save_edges_var.get(),
                save_comparison=self.save_comparison_var.get(),
                max_workers=self.max_workers_var.get()
            )
            
            # 设置回调
            batch_processor.on_progress_changed = self.on_progress_changed
            batch_processor.on_item_completed = self.on_item_completed
            batch_processor.on_batch_completed = self.on_batch_completed
            batch_processor.on_error = self.on_error
            
            # 设置配置并开始处理
            batch_processor.set_config(config)
            
            if batch_processor.start_batch_processing(self.default_params):
                self.is_processing = True
                self.start_btn.config(state="disabled")
                self.pause_btn.config(state="normal")
                self.cancel_btn.config(state="normal")
                self.status_var.set("正在扫描文件...")
            else:
                messagebox.showerror("错误", "启动批处理失败")
                
        except Exception as e:
            messagebox.showerror("错误", f"批处理启动失败: {e}")
    
    def pause_processing(self):
        """暂停/恢复处理"""
        try:
            from core.batch_processor import batch_processor
            
            if batch_processor.progress.status == "running":
                batch_processor.pause_processing()
                self.pause_btn.config(text="恢复")
                self.status_var.set("已暂停")
            elif batch_processor.progress.status == "paused":
                batch_processor.resume_processing()
                self.pause_btn.config(text="暂停")
                self.status_var.set("处理中...")
                
        except Exception as e:
            messagebox.showerror("错误", f"暂停/恢复操作失败: {e}")
    
    def cancel_processing(self):
        """取消处理"""
        if messagebox.askyesno("确认", "确定要取消批处理吗？"):
            try:
                from core.batch_processor import batch_processor
                batch_processor.cancel_processing()
                
                self.is_processing = False
                self.start_btn.config(state="normal")
                self.pause_btn.config(state="disabled", text="暂停")
                self.cancel_btn.config(state="disabled")
                self.status_var.set("已取消")
                
            except Exception as e:
                messagebox.showerror("错误", f"取消操作失败: {e}")
    
    def on_progress_changed(self, progress):
        """进度变化回调"""
        self.dialog.after(0, lambda: self._update_progress_ui(progress))
    
    def _update_progress_ui(self, progress):
        """更新进度UI"""
        # 更新进度条
        percentage = progress.get_progress_percentage()
        self.progress_var.set(percentage)
        
        # 更新状态信息
        if progress.status == "running":
            self.status_var.set(f"处理中... ({progress.processed_files}/{progress.total_files})")
        elif progress.status == "paused":
            self.status_var.set("已暂停")
        elif progress.status == "completed":
            self.status_var.set("处理完成")
        elif progress.status == "cancelled":
            self.status_var.set("已取消")
        
        # 更新当前文件
        if progress.current_file:
            self.current_file_var.set(f"当前: {progress.current_file}")
        
        # 更新时间信息
        elapsed = progress.get_elapsed_time()
        if progress.processed_files > 0:
            remaining = progress.get_estimated_remaining_time()
            self.time_info_var.set(f"已用时: {elapsed:.1f}秒 | 预计剩余: {remaining:.1f}秒")
        else:
            self.time_info_var.set(f"已用时: {elapsed:.1f}秒")
    
    def on_item_completed(self, item):
        """项目完成回调"""
        pass  # 可以在这里添加详细的项目完成处理
    
    def on_batch_completed(self, summary):
        """批处理完成回调"""
        self.dialog.after(0, lambda: self._show_completion_summary(summary))
    
    def _show_completion_summary(self, summary):
        """显示完成摘要"""
        self.is_processing = False
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled", text="暂停")
        self.cancel_btn.config(state="disabled")
        
        # 显示摘要对话框
        summary_text = f"""批处理已完成！

总文件数: {summary['total_files']}
成功处理: {summary['completed_files']}
处理失败: {summary['error_files']}
成功率: {summary['success_rate']:.1f}%

总用时: {summary['total_time']:.1f}秒
平均每文件: {summary['average_time_per_file']:.2f}秒"""
        
        messagebox.showinfo("批处理完成", summary_text)
    
    def on_error(self, error_message):
        """错误回调"""
        self.dialog.after(0, lambda: messagebox.showerror("错误", error_message))
    
    def close_dialog(self):
        """关闭对话框"""
        if self.is_processing:
            if messagebox.askyesno("确认", "批处理正在进行中，确定要关闭吗？"):
                self.cancel_processing()
                self.dialog.destroy()
        else:
            self.dialog.destroy()


class ImageInfoWindow:
    """图像信息显示窗口"""
    
    def __init__(self, parent, image_path: str):
        self.parent = parent
        self.image_path = image_path
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("图像信息")
        self.window.geometry("600x500")
        self.window.resizable(True, True)
        self.window.transient(parent)
        self.window.grab_set()
        
        # 创建 UI
        self.create_ui()
        
        # 居中显示
        self.center_window()
        
        # 加载信息
        self.load_image_info()
    
    def create_ui(self):
        """创建用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 文件名显示
        filename = os.path.basename(self.image_path)
        title_label = ttk.Label(main_frame, text=f"文件: {filename}", font=("", 12, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # 创建笔记本控件
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 基本信息标签页
        self.basic_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.basic_frame, text="基本信息")
        
        # 技术信息标签页
        self.tech_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tech_frame, text="技术信息")
        
        # 建议标签页
        self.rec_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.rec_frame, text="优化建议")
        
        # 创建文本显示区域
        self.create_text_areas()
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="刷新", command=self.load_image_info).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="复制信息", command=self.copy_info).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="关闭", command=self.window.destroy).pack(side=tk.RIGHT)
    
    def create_text_areas(self):
        """创建文本显示区域"""
        # 基本信息文本区域
        basic_scroll_frame = ttk.Frame(self.basic_frame)
        basic_scroll_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.basic_text = tk.Text(basic_scroll_frame, wrap=tk.WORD, font=("", 10))
        basic_scrollbar = ttk.Scrollbar(basic_scroll_frame, orient=tk.VERTICAL, command=self.basic_text.yview)
        self.basic_text.configure(yscrollcommand=basic_scrollbar.set)
        
        self.basic_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        basic_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 技术信息文本区域
        tech_scroll_frame = ttk.Frame(self.tech_frame)
        tech_scroll_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.tech_text = tk.Text(tech_scroll_frame, wrap=tk.WORD, font=("", 9))
        tech_scrollbar = ttk.Scrollbar(tech_scroll_frame, orient=tk.VERTICAL, command=self.tech_text.yview)
        self.tech_text.configure(yscrollcommand=tech_scrollbar.set)
        
        self.tech_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tech_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 建议文本区域
        rec_scroll_frame = ttk.Frame(self.rec_frame)
        rec_scroll_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.rec_text = tk.Text(rec_scroll_frame, wrap=tk.WORD, font=("", 10))
        rec_scrollbar = ttk.Scrollbar(rec_scroll_frame, orient=tk.VERTICAL, command=self.rec_text.yview)
        self.rec_text.configure(yscrollcommand=rec_scrollbar.set)
        
        self.rec_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        rec_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def center_window(self):
        """居中显示窗口"""
        self.window.update_idletasks()
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()
        
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
        
        self.window.geometry(f"+{x}+{y}")
    
    def load_image_info(self):
        """加载图像信息"""
        try:
            # 获取详细信息
            self.info = image_info_analyzer.analyze_image_file(self.image_path)
            
            # 显示基本信息
            self.display_basic_info()
            
            # 显示技术信息
            self.display_tech_info()
            
            # 显示建议
            self.display_recommendations()
            
        except Exception as e:
            error_msg = f"加载图像信息失败: {e}"
            self.basic_text.delete(1.0, tk.END)
            self.basic_text.insert(tk.END, error_msg)
    
    def display_basic_info(self):
        """显示基本信息"""
        self.basic_text.delete(1.0, tk.END)
        
        file_info = self.info.get('file_info', {})
        image_info = self.info.get('image_info', {})
        memory_info = self.info.get('memory_info', {})
        
        lines = []
        
        # 文件信息
        lines.append("═══ 文件信息 ═══")
        lines.append(f"文件名: {file_info.get('filename', '未知')}")
        lines.append(f"格式: {file_info.get('format_name', '未知')}")
        lines.append(f"文件大小: {file_info.get('file_size_mb', 0):.2f} MB")
        lines.append(f"修改时间: {file_info.get('modified_time', '未知')}")
        lines.append("")
        
        # 图像信息
        lines.append("═══ 图像信息 ═══")
        if 'width' in image_info and 'height' in image_info:
            lines.append(f"尺寸: {image_info['width']} × {image_info['height']} 像素")
            lines.append(f"像素数: {image_info.get('total_pixels', 0):,}")
            lines.append(f"宽高比: {image_info.get('aspect_ratio', 0):.2f}:1")
        
        if 'color_mode_description' in image_info:
            lines.append(f"色彩模式: {image_info['color_mode_description']}")
        
        if image_info.get('has_transparency', False):
            lines.append("透明度: 是")
        
        lines.append("")
        
        # 内存信息
        lines.append("═══ 内存信息 ═══")
        if 'base_memory_mb' in memory_info:
            lines.append(f"基础内存: {memory_info['base_memory_mb']:.1f} MB")
            lines.append(f"处理内存: {memory_info.get('processing_memory_mb', 0):.1f} MB")
            lines.append(f"内存等级: {memory_info.get('memory_level', '未知')}")
        
        if 'system_available_mb' in memory_info:
            usage_percent = memory_info.get('memory_usage_percent', 0)
            lines.append(f"系统内存占用: {usage_percent:.1f}%")
        
        self.basic_text.insert(tk.END, '\n'.join(lines))
    
    def display_tech_info(self):
        """显示技术信息"""
        self.tech_text.delete(1.0, tk.END)
        
        image_info = self.info.get('image_info', {})
        compatibility_info = self.info.get('compatibility_info', {})
        metadata = self.info.get('metadata', {})
        
        lines = []
        
        # 技术细节
        lines.append("═══ 技术细节 ═══")
        if 'data_type' in image_info:
            lines.append(f"数据类型: {image_info['data_type']}")
        if 'mode' in image_info:
            lines.append(f"PIL模式: {image_info['mode']}")
        if 'format' in image_info:
            lines.append(f"图像格式: {image_info['format']}")
        lines.append("")
        
        # 兼容性信息
        lines.append("═══ 兼容性 ═══")
        opencv_support = compatibility_info.get('opencv_support', False)
        pil_support = compatibility_info.get('pil_support', False)
        lines.append(f"OpenCV 支持: {'\u2713 是' if opencv_support else '\u2717 否'}")
        lines.append(f"PIL 支持: {'\u2713 是' if pil_support else '\u2717 否'}")
        
        loading_recs = compatibility_info.get('loading_recommendations', [])
        if loading_recs:
            lines.append("加载建议:")
            for rec in loading_recs:
                lines.append(f"  - {rec}")
        lines.append("")
        
        # 元数据
        lines.append("═══ 元数据 ═══")
        if metadata.get('has_exif', False):
            lines.append("EXIF 数据: 是")
        else:
            lines.append("EXIF 数据: 否")
        
        metadata_info = metadata.get('info', {})
        if metadata_info:
            lines.append("其他元数据:")
            for key, value in list(metadata_info.items())[:5]:  # 只显示前5个
                lines.append(f"  {key}: {value}")
            if len(metadata_info) > 5:
                lines.append(f"  ... 及其他 {len(metadata_info) - 5} 个")
        
        self.tech_text.insert(tk.END, '\n'.join(lines))
    
    def display_recommendations(self):
        """显示优化建议"""
        self.rec_text.delete(1.0, tk.END)
        
        recommendations = self.info.get('recommendations', [])
        
        if not recommendations:
            self.rec_text.insert(tk.END, "没有特别的优化建议，图像处于良好状态。")
            return
        
        lines = []
        lines.append("═══ 优化建议 ═══")
        lines.append("")
        
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"{i}. {rec}")
            lines.append("")
        
        # 添加通用建议
        lines.append("═══ 通用建议 ═══")
        lines.append("")
        lines.append("• 如果处理速度慢，考虑缩小图像尺寸")
        lines.append("• 建议使用PNG格式保存处理结果")
        lines.append("• 定期清理系统内存以提高性能")
        lines.append("• 大批量处理时使用批处理功能")
        
        self.rec_text.insert(tk.END, '\n'.join(lines))
    
    def copy_info(self):
        """复制信息到剪贴板"""
        try:
            # 收集所有信息
            all_info = []
            all_info.append(f"图像信息 - {os.path.basename(self.image_path)}")
            all_info.append("=" * 50)
            all_info.append("")
            
            # 基本信息
            all_info.append("基本信息:")
            all_info.append(self.basic_text.get(1.0, tk.END).strip())
            all_info.append("")
            
            # 技术信息
            all_info.append("技术信息:")
            all_info.append(self.tech_text.get(1.0, tk.END).strip())
            all_info.append("")
            
            # 建议
            all_info.append("优化建议:")
            all_info.append(self.rec_text.get(1.0, tk.END).strip())
            
            # 复制到剪贴板
            text_to_copy = '\n'.join(all_info)
            self.window.clipboard_clear()
            self.window.clipboard_append(text_to_copy)
            
            # 显示成功信息
            messagebox.showinfo("成功", "图像信息已复制到剪贴板")
            
        except Exception as e:
            messagebox.showerror("错误", f"复制信息失败: {e}")


if __name__ == "__main__":
    # 测试代码
    root = tk.Tk()
    root.title("边缘检测标签页测试")
    root.geometry("1000x700")
    
    tab = EdgeDetectionTab(root)
    tab.get_frame().pack(fill=tk.BOTH, expand=True)
    
    # 测试加载一个图像（如果有的话）
    import sys
    if len(sys.argv) > 1:
        tab.load_image(sys.argv[1])
    
    root.mainloop()