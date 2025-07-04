"""截图功能核心模块"""

import os
import time
import threading
from datetime import datetime
from typing import Tuple, Optional, Callable

# 延迟导入GUI相关模块，避免在无GUI环境下导入失败
pyautogui = None
Image = None

def _import_gui_modules():
    """延迟导入GUI相关模块"""
    global pyautogui, Image
    if pyautogui is None:
        try:
            import pyautogui as _pyautogui
            from PIL import Image as _Image
            pyautogui = _pyautogui
            Image = _Image
            
            # Windows特定优化配置
            if os.name == 'nt':  # Windows系统
                # 禁用故障保护，提高截图稳定性
                pyautogui.FAILSAFE = False
                # 设置全局暂停时间，避免操作过快
                pyautogui.PAUSE = 0.1
                # 提高图像识别精度（如果使用图像定位功能）
                pyautogui.MINIMUM_DURATION = 0.1
            
            return True
        except ImportError as e:
            print(f"警告: GUI模块导入失败 - {e}")
            print("截图功能将不可用，但配置和文件管理功能正常")
            return False
    return True


class ScreenshotCapture:
    """截图捕获类"""
    
    def __init__(self):
        self.default_region = (1750, 60, 1860, 160)  # 默认截图区域 (x1, y1, x2, y2)
        self.custom_region = None  # 自定义截图区域
        self.save_directory = "screenshots"  # 默认保存目录
        self.image_counter = 1  # 图片计数器
        self.continuous_capture_thread = None
        self.is_capturing = False
        self.capture_interval = 1.0  # 连续截图间隔(秒)
        self.gui_available = False  # GUI模块是否可用
        
        # 尝试导入GUI模块
        self.gui_available = _import_gui_modules()
    
    def set_capture_region(self, x1: int, y1: int, x2: int, y2: int):
        """设置自定义截图区域"""
        self.custom_region = (x1, y1, x2, y2)
    
    def get_capture_region(self) -> Tuple[int, int, int, int]:
        """获取当前截图区域"""
        return self.custom_region if self.custom_region else self.default_region
    
    def set_save_directory(self, directory: str):
        """设置保存目录"""
        self.save_directory = directory
        # 确保目录存在
        os.makedirs(directory, exist_ok=True)
    
    def set_capture_interval(self, interval: float):
        """设置连续截图间隔"""
        self.capture_interval = max(0.1, interval)  # 最小间隔0.1秒
    
    def reset_counter(self):
        """重置图片计数器"""
        self.image_counter = 1
    
    def capture_single(self, save_path: Optional[str] = None) -> Optional[dict]:
        """
        单次截图 - Windows优化版本
        
        Args:
            save_path: 可选的保存路径，如果不提供则使用默认命名
            
        Returns:
            包含截图信息的字典：
            {
                'file_path': str,        # 保存的文件路径
                'region': tuple,         # 截图区域 (x1, y1, x2, y2)
                'size': tuple,           # 区域大小 (width, height)
                'pixels': int,           # 总像素数
                'file_size': int,        # 文件大小（字节）
            }
            失败返回None
        """
        if not self.gui_available:
            print("错误: GUI模块不可用，无法进行截图")
            return None
            
        try:
            # 获取截图区域
            x1, y1, x2, y2 = self.get_capture_region()
            width = x2 - x1
            height = y2 - y1
            
            # Windows系统优化：使用region参数进行部分截图，性能更好
            # 根据Context7文档：pyautogui.screenshot(region=(left, top, width, height))
            screenshot = pyautogui.screenshot(region=(x1, y1, width, height))
            
            # 确定保存路径
            if not save_path:
                os.makedirs(self.save_directory, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{self.image_counter:04d}_{timestamp}.png"
                save_path = os.path.join(self.save_directory, filename)
                self.image_counter += 1
            
            # 保存图片
            screenshot.save(save_path)
            
            # 获取文件大小
            file_size = os.path.getsize(save_path)
            
            # 计算像素总数
            total_pixels = width * height
            
            # 构建返回信息
            result = {
                'file_path': save_path,
                'region': (x1, y1, x2, y2),
                'size': (width, height),
                'pixels': total_pixels,
                'file_size': file_size
            }
            
            print(f"截图已保存: {save_path}")
            print(f"截图区域: ({x1}, {y1}) 到 ({x2}, {y2})")
            print(f"区域大小: {width}×{height} 像素 (共{total_pixels:,}像素)")
            print(f"文件大小: {file_size:,} 字节 ({file_size/1024:.1f}KB)")
            
            return result
            
        except Exception as e:
            print(f"截图失败: {e}")
            return None
    
    def start_continuous_capture(self, on_capture: Optional[Callable[[dict], None]] = None):
        """
        开始连续截图
        
        Args:
            on_capture: 每次截图后的回调函数，接收截图信息字典作为参数
        """
        if self.is_capturing:
            return False
        
        self.is_capturing = True
        
        def capture_loop():
            while self.is_capturing:
                try:
                    result = self.capture_single()
                    if result and on_capture:
                        on_capture(result)
                    
                    # 等待指定间隔
                    time.sleep(self.capture_interval)
                    
                except Exception as e:
                    print(f"连续截图错误: {e}")
                    break
        
        self.continuous_capture_thread = threading.Thread(target=capture_loop, daemon=True)
        self.continuous_capture_thread.start()
        return True
    
    def stop_continuous_capture(self):
        """停止连续截图"""
        self.is_capturing = False
        if self.continuous_capture_thread and self.continuous_capture_thread.is_alive():
            self.continuous_capture_thread.join(timeout=1.0)
    
    def is_continuous_capturing(self) -> bool:
        """检查是否正在连续截图"""
        return self.is_capturing
    
    def get_screen_size(self) -> Tuple[int, int]:
        """获取屏幕尺寸 - Windows优化版本"""
        if not self.gui_available:
            return (1920, 1080)  # 返回默认值
            
        try:
            # 根据Context7文档：pyautogui.size() 返回屏幕分辨率
            return pyautogui.size()
        except Exception:
            return (1920, 1080)  # 默认值
    
    def validate_region(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """验证截图区域是否有效"""
        try:
            screen_width, screen_height = self.get_screen_size()
            
            # 检查坐标是否在屏幕范围内
            if x1 < 0 or y1 < 0 or x2 > screen_width or y2 > screen_height:
                return False
            
            # 检查区域是否有效（x2 > x1 and y2 > y1）
            if x2 <= x1 or y2 <= y1:
                return False
                
            return True
            
        except Exception:
            return False
    
    def capture_fullscreen(self, save_path: Optional[str] = None) -> Optional[dict]:
        """
        全屏截图 - Windows系统优化
        
        Args:
            save_path: 保存路径
            
        Returns:
            包含截图信息的字典：
            {
                'file_path': str,        # 保存的文件路径
                'region': tuple,         # 截图区域 (x1, y1, x2, y2)
                'size': tuple,           # 区域大小 (width, height)
                'pixels': int,           # 总像素数
                'file_size': int,        # 文件大小（字节）
            }
            失败返回None
        """
        if not self.gui_available:
            print("错误: GUI模块不可用，无法进行截图")
            return None
            
        try:
            # 根据Context7文档：不指定region参数即为全屏截图
            screenshot = pyautogui.screenshot()
            
            if not save_path:
                os.makedirs(self.save_directory, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"fullscreen_{timestamp}.png"
                save_path = os.path.join(self.save_directory, filename)
            
            screenshot.save(save_path)
            
            # 获取屏幕尺寸作为截图区域
            screen_width, screen_height = self.get_screen_size()
            
            # 获取文件大小
            file_size = os.path.getsize(save_path)
            
            # 计算像素总数
            total_pixels = screen_width * screen_height
            
            # 构建返回信息
            result = {
                'file_path': save_path,
                'region': (0, 0, screen_width, screen_height),
                'size': (screen_width, screen_height),
                'pixels': total_pixels,
                'file_size': file_size
            }
            
            print(f"全屏截图已保存: {save_path}")
            print(f"全屏区域: 0, 0 到 {screen_width}, {screen_height}")
            print(f"区域大小: {screen_width}×{screen_height} 像素 (共{total_pixels:,}像素)")
            print(f"文件大小: {file_size:,} 字节 ({file_size/1024:.1f}KB)")
            
            return result
            
        except Exception as e:
            print(f"全屏截图失败: {e}")
            return None
    
    def capture_custom_circle(self, center_x: int, center_y: int, radius: int, 
                             save_path: Optional[str] = None) -> Optional[dict]:
        """
        自定义圆形截图
        
        Args:
            center_x: 圆心X坐标
            center_y: 圆心Y坐标  
            radius: 半径
            save_path: 可选的保存路径
            
        Returns:
            包含截图信息的字典，失败返回None
        """
        if not self.gui_available:
            print("错误: GUI模块不可用，无法进行截图")
            return None
            
        try:
            # 先进行全屏截图
            full_screenshot = pyautogui.screenshot()
            
            # 转换为OpenCV格式
            import cv2
            import numpy as np
            from PIL import Image
            
            # PIL to OpenCV
            open_cv_image = np.array(full_screenshot)
            # 转换RGB到BGR (OpenCV使用BGR)
            open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)
            
            # 创建Circle对象用于circle_capture
            from core.circle_detection import Circle
            circle = Circle(x=center_x, y=center_y, radius=radius, confidence=1.0)
            
            # 使用circle_capture提取圆形区域
            from core.circle_capture import circle_capture
            circle_image = circle_capture.extract_circle_region(
                open_cv_image, circle, 
                padding=0, 
                transparent_background=True
            )
            
            if circle_image is None:
                print("圆形区域提取失败")
                return None
            
            # 确定保存路径
            if not save_path:
                os.makedirs(self.save_directory, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"custom_circle_{self.image_counter:04d}_{timestamp}.png"
                save_path = os.path.join(self.save_directory, filename)
                self.image_counter += 1
            
            # 保存为PNG（支持透明度）
            pil_image = Image.fromarray(circle_image, 'RGBA')
            pil_image.save(save_path, 'PNG')
            
            # 获取文件大小
            file_size = os.path.getsize(save_path)
            
            # 计算圆形区域的边界框
            x1 = max(0, center_x - radius)
            y1 = max(0, center_y - radius)
            x2 = min(full_screenshot.width, center_x + radius)
            y2 = min(full_screenshot.height, center_y + radius)
            
            width = x2 - x1
            height = y2 - y1
            total_pixels = width * height
            
            # 构建返回信息
            result = {
                'file_path': save_path,
                'region': (x1, y1, x2, y2),
                'size': (width, height),
                'pixels': total_pixels,
                'file_size': file_size,
                'circle_center': (center_x, center_y),
                'circle_radius': radius,
                'screenshot_type': 'custom_circle'
            }
            
            print(f"自定义圆形截图已保存: {save_path}")
            print(f"圆心: ({center_x}, {center_y})，半径: {radius}")
            print(f"边界框: ({x1}, {y1}) 到 ({x2}, {y2})")
            print(f"文件大小: {file_size:,} 字节 ({file_size/1024:.1f}KB)")
            
            return result
            
        except Exception as e:
            print(f"自定义圆形截图失败: {e}")
            return None


# 全局截图实例
screenshot_manager = ScreenshotCapture()