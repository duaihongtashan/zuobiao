"""圆形检测算法核心模块 - 基于OpenCV HoughCircles"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import time
from dataclasses import dataclass


@dataclass
class Circle:
    """圆形数据结构"""
    x: int           # 圆心X坐标
    y: int           # 圆心Y坐标  
    radius: int      # 半径
    confidence: float = 0.0  # 置信度
    adjusted: bool = False   # 是否被用户调整过
    original_x: int = None   # 原始检测的X坐标
    original_y: int = None   # 原始检测的Y坐标
    original_radius: int = None  # 原始检测的半径
    
    def __post_init__(self):
        if self.original_x is None:
            self.original_x = self.x
        if self.original_y is None:
            self.original_y = self.y
        if self.original_radius is None:
            self.original_radius = self.radius


@dataclass
class DetectionParams:
    """HoughCircles检测参数"""
    dp: float = 1.0                    # 累加器分辨率比例
    min_dist: int = 50                 # 圆心间最小距离
    param1: int = 50                   # Canny边缘检测高阈值
    param2: int = 30                   # 累加器阈值
    min_radius: int = 10               # 最小半径
    max_radius: int = 100              # 最大半径
    blur_kernel_size: int = 5          # 高斯模糊核大小
    median_blur_size: int = 5          # 中值滤波核大小
    use_clahe: bool = True             # 是否使用CLAHE直方图均衡化
    clahe_clip_limit: float = 2.0      # CLAHE剪裁限制
    clahe_tile_grid_size: Tuple[int, int] = (8, 8)  # CLAHE瓦片网格大小


class CircleDetector:
    """圆形检测器 - 基于OpenCV HoughCircles"""
    
    def __init__(self, params: Optional[DetectionParams] = None):
        self.params = params or DetectionParams()
        self.last_detection_time = 0
        self.detection_cache = {}
        self.debug_mode = False
        
        # 预处理工具初始化
        self.clahe = cv2.createCLAHE(
            clipLimit=self.params.clahe_clip_limit,
            tileGridSize=self.params.clahe_tile_grid_size
        )
    
    def set_params(self, params: DetectionParams):
        """设置检测参数"""
        self.params = params
        # 重新初始化CLAHE
        self.clahe = cv2.createCLAHE(
            clipLimit=self.params.clahe_clip_limit,
            tileGridSize=self.params.clahe_tile_grid_size
        )
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        图像预处理管道
        
        Args:
            image: 输入图像 (BGR或灰度)
            
        Returns:
            预处理后的灰度图像
        """
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # CLAHE直方图均衡化（增强对比度）
        if self.params.use_clahe:
            gray = self.clahe.apply(gray)
        
        # 中值滤波降噪
        if self.params.median_blur_size > 0:
            gray = cv2.medianBlur(gray, self.params.median_blur_size)
        
        # 高斯模糊（平滑处理）
        if self.params.blur_kernel_size > 0:
            gray = cv2.GaussianBlur(gray, 
                                  (self.params.blur_kernel_size, self.params.blur_kernel_size), 
                                  0)
        
        return gray
    
    def detect_circles(self, image: np.ndarray) -> List[Circle]:
        """
        检测圆形
        
        Args:
            image: 输入图像
            
        Returns:
            检测到的圆形列表
        """
        start_time = time.time()
        
        # 图像预处理
        processed_image = self.preprocess_image(image)
        
        # HoughCircles检测
        circles_raw = cv2.HoughCircles(
            processed_image,
            cv2.HOUGH_GRADIENT,
            dp=self.params.dp,
            minDist=self.params.min_dist,
            param1=self.params.param1,
            param2=self.params.param2,
            minRadius=self.params.min_radius,
            maxRadius=self.params.max_radius
        )
        
        circles = []
        if circles_raw is not None:
            circles_raw = circles_raw[0, :]  # 获取检测结果
            
            for circle_data in circles_raw:
                x, y, radius = circle_data
                x, y, radius = int(x), int(y), int(radius)
                
                # 计算置信度
                confidence = self.calculate_confidence(processed_image, x, y, radius)
                
                circle = Circle(
                    x=x, y=y, radius=radius, 
                    confidence=confidence
                )
                circles.append(circle)
        
        # 按置信度排序
        circles.sort(key=lambda c: c.confidence, reverse=True)
        
        detection_time = time.time() - start_time
        self.last_detection_time = detection_time
        
        if self.debug_mode:
            print(f"检测完成，用时: {detection_time:.3f}s，发现圆形: {len(circles)}个")
        
        return circles
    
    def calculate_confidence(self, image: np.ndarray, x: int, y: int, radius: int) -> float:
        """
        计算圆形检测置信度
        
        Args:
            image: 处理后的灰度图像
            x, y: 圆心坐标
            radius: 半径
            
        Returns:
            置信度值 (0-1)
        """
        h, w = image.shape
        
        # 边界检查
        if x - radius < 0 or x + radius >= w or y - radius < 0 or y + radius >= h:
            return 0.0
        
        # 1. 边缘强度评估
        edge_score = self._calculate_edge_strength(image, x, y, radius)
        
        # 2. 圆形完整性评估
        completeness_score = self._calculate_completeness(image, x, y, radius)
        
        # 3. 几何一致性评估
        geometry_score = self._calculate_geometry_consistency(image, x, y, radius)
        
        # 综合置信度计算
        confidence = (edge_score * 0.4 + 
                     completeness_score * 0.4 + 
                     geometry_score * 0.2)
        
        return min(1.0, max(0.0, confidence))
    
    def _calculate_edge_strength(self, image: np.ndarray, x: int, y: int, radius: int) -> float:
        """计算圆形边缘强度"""
        # 创建圆形蒙版
        mask = np.zeros(image.shape, dtype=np.uint8)
        cv2.circle(mask, (x, y), radius, 255, 2)  # 2像素宽的圆环
        
        # 计算边缘
        edges = cv2.Canny(image, 50, 150)
        
        # 计算圆环区域的边缘像素比例
        circle_pixels = np.sum(mask > 0)
        edge_pixels = np.sum((mask > 0) & (edges > 0))
        
        if circle_pixels == 0:
            return 0.0
        
        edge_ratio = edge_pixels / circle_pixels
        return min(1.0, edge_ratio * 3)  # 放大3倍，但限制在1.0以内
    
    def _calculate_completeness(self, image: np.ndarray, x: int, y: int, radius: int) -> float:
        """计算圆形完整性"""
        # 采样圆周上的点
        num_samples = 36  # 每10度一个点
        complete_points = 0
        
        for i in range(num_samples):
            angle = 2 * np.pi * i / num_samples
            sample_x = int(x + radius * np.cos(angle))
            sample_y = int(y + radius * np.sin(angle))
            
            # 检查采样点是否在图像边界内
            if 0 <= sample_x < image.shape[1] and 0 <= sample_y < image.shape[0]:
                # 检查该点附近是否有边缘
                region = image[max(0, sample_y-2):min(image.shape[0], sample_y+3),
                              max(0, sample_x-2):min(image.shape[1], sample_x+3)]
                
                if region.size > 0:
                    edges = cv2.Canny(region, 50, 150)
                    if np.any(edges > 0):
                        complete_points += 1
        
        return complete_points / num_samples
    
    def _calculate_geometry_consistency(self, image: np.ndarray, x: int, y: int, radius: int) -> float:
        """计算几何一致性"""
        # 检查圆心区域的特征
        center_region_size = max(3, radius // 4)
        
        # 确保区域在图像边界内
        y_start = max(0, y - center_region_size)
        y_end = min(image.shape[0], y + center_region_size + 1)
        x_start = max(0, x - center_region_size)
        x_end = min(image.shape[1], x + center_region_size + 1)
        
        center_region = image[y_start:y_end, x_start:x_end]
        
        if center_region.size == 0:
            return 0.0
        
        # 计算中心区域的方差（一般圆形物体中心相对均匀）
        center_var = np.var(center_region) / 255.0  # 归一化
        geometry_score = 1.0 - min(1.0, center_var)  # 方差越小，几何一致性越好
        
        return geometry_score
    
    def auto_adjust_params(self, image: np.ndarray) -> DetectionParams:
        """
        根据图像特征自动调整检测参数
        
        Args:
            image: 输入图像
            
        Returns:
            调整后的参数
        """
        gray = self.preprocess_image(image)
        
        # 分析图像特征
        mean_intensity = np.mean(gray)
        contrast = np.std(gray)
        
        # 复制当前参数
        new_params = DetectionParams()
        new_params.__dict__.update(self.params.__dict__)
        
        # 根据图像亮度调整Canny阈值
        if mean_intensity < 100:  # 暗图像
            new_params.param1 = max(30, self.params.param1 - 20)
        elif mean_intensity > 180:  # 亮图像
            new_params.param1 = min(100, self.params.param1 + 20)
        
        # 根据对比度调整累加器阈值
        if contrast < 30:  # 低对比度
            new_params.param2 = max(20, self.params.param2 - 10)
        elif contrast > 80:  # 高对比度
            new_params.param2 = min(50, self.params.param2 + 10)
        
        return new_params
    
    def filter_circles(self, circles: List[Circle], 
                      min_confidence: float = 0.3,
                      max_circles: int = 10) -> List[Circle]:
        """
        过滤圆形结果
        
        Args:
            circles: 原始圆形列表
            min_confidence: 最小置信度阈值
            max_circles: 最大圆形数量
            
        Returns:
            过滤后的圆形列表
        """
        # 按置信度过滤
        filtered = [c for c in circles if c.confidence >= min_confidence]
        
        # 限制数量
        filtered = filtered[:max_circles]
        
        # 去除重叠的圆形
        filtered = self._remove_overlapping_circles(filtered)
        
        return filtered
    
    def _remove_overlapping_circles(self, circles: List[Circle], 
                                   overlap_threshold: float = 0.7) -> List[Circle]:
        """去除重叠的圆形"""
        if len(circles) <= 1:
            return circles
        
        result = []
        for i, circle1 in enumerate(circles):
            is_overlapping = False
            
            for j, circle2 in enumerate(result):
                # 计算两圆心距离
                distance = np.sqrt((circle1.x - circle2.x)**2 + (circle1.y - circle2.y)**2)
                min_radius = min(circle1.radius, circle2.radius)
                
                # 如果距离小于较小半径的overlap_threshold倍，认为是重叠
                if distance < min_radius * overlap_threshold:
                    is_overlapping = True
                    break
            
            if not is_overlapping:
                result.append(circle1)
        
        return result
    
    def create_debug_image(self, image: np.ndarray, circles: List[Circle]) -> np.ndarray:
        """
        创建调试图像，显示检测结果
        
        Args:
            image: 原始图像
            circles: 检测到的圆形
            
        Returns:
            带有标注的调试图像
        """
        debug_img = image.copy()
        if len(debug_img.shape) == 2:
            debug_img = cv2.cvtColor(debug_img, cv2.COLOR_GRAY2BGR)
        
        for i, circle in enumerate(circles):
            # 根据置信度选择颜色
            if circle.confidence > 0.7:
                color = (0, 255, 0)  # 绿色 - 高置信度
            elif circle.confidence > 0.4:
                color = (0, 255, 255)  # 黄色 - 中等置信度
            else:
                color = (0, 0, 255)  # 红色 - 低置信度
            
            # 画圆形
            cv2.circle(debug_img, (circle.x, circle.y), circle.radius, color, 2)
            
            # 画圆心
            cv2.circle(debug_img, (circle.x, circle.y), 3, color, -1)
            
            # 标注置信度
            text = f"{i+1}: {circle.confidence:.2f}"
            cv2.putText(debug_img, text, 
                       (circle.x - 30, circle.y - circle.radius - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return debug_img
    
    def get_detection_info(self) -> Dict[str, Any]:
        """获取检测信息"""
        return {
            "last_detection_time": self.last_detection_time,
            "params": self.params.__dict__,
            "debug_mode": self.debug_mode
        }


# 全局圆形检测器实例
circle_detector = CircleDetector()