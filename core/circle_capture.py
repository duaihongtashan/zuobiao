"""圆形截图功能模块 - 基于检测到的圆形进行精确截图"""

import cv2
import numpy as np
import json
import os
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path
from PIL import Image, ImageDraw

from core.circle_detection import Circle, circle_detector
from utils.file_manager import file_manager


class CircleCapture:
    """圆形截图捕获器"""
    
    def __init__(self):
        self.save_directory = "screenshots/circles"
        self.data_directory = "screenshots/circle_data"
        self.anti_alias_scale = 4  # 抗锯齿缩放倍数
        
        # 确保目录存在
        Path(self.save_directory).mkdir(parents=True, exist_ok=True)
        Path(self.data_directory).mkdir(parents=True, exist_ok=True)
    
    def set_save_directory(self, directory: str):
        """设置保存目录"""
        self.save_directory = directory
        self.data_directory = os.path.join(directory, "circle_data")
        Path(self.save_directory).mkdir(parents=True, exist_ok=True)
        Path(self.data_directory).mkdir(parents=True, exist_ok=True)
    
    def create_circle_mask(self, width: int, height: int, 
                          center_x: int, center_y: int, radius: int,
                          anti_alias: bool = True) -> np.ndarray:
        """
        创建圆形蒙版
        
        Args:
            width, height: 图像尺寸
            center_x, center_y: 圆心坐标
            radius: 半径
            anti_alias: 是否使用抗锯齿
            
        Returns:
            圆形蒙版 (0-255灰度图)
        """
        if anti_alias:
            return self._create_anti_aliased_mask(width, height, center_x, center_y, radius)
        else:
            return self._create_simple_mask(width, height, center_x, center_y, radius)
    
    def _create_simple_mask(self, width: int, height: int, 
                           center_x: int, center_y: int, radius: int) -> np.ndarray:
        """创建简单圆形蒙版"""
        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.circle(mask, (center_x, center_y), radius, 255, -1)
        return mask
    
    def _create_anti_aliased_mask(self, width: int, height: int,
                                 center_x: int, center_y: int, radius: int) -> np.ndarray:
        """创建抗锯齿圆形蒙版"""
        scale = self.anti_alias_scale
        
        # 创建大尺寸蒙版
        large_width = width * scale
        large_height = height * scale
        large_mask = np.zeros((large_height, large_width), dtype=np.uint8)
        
        # 在大尺寸上绘制圆形
        cv2.circle(large_mask, 
                  (center_x * scale, center_y * scale), 
                  radius * scale, 255, -1)
        
        # 降采样产生平滑边缘
        smooth_mask = cv2.resize(large_mask, (width, height), 
                               interpolation=cv2.INTER_AREA)
        
        return smooth_mask
    
    def extract_circle_region(self, image: np.ndarray, circle: Circle,
                             padding: int = 0, 
                             transparent_background: bool = True) -> Optional[np.ndarray]:
        """
        提取圆形区域
        
        Args:
            image: 原始图像
            circle: 圆形对象
            padding: 额外的边界填充
            transparent_background: 是否使用透明背景
            
        Returns:
            提取的圆形图像 (RGBA格式如果transparent_background=True)
        """
        if image is None or image.size == 0:
            return None
        
        # 计算边界框
        x, y, r = circle.x, circle.y, circle.radius
        x1 = max(0, x - r - padding)
        y1 = max(0, y - r - padding)
        x2 = min(image.shape[1], x + r + padding + 1)
        y2 = min(image.shape[0], y + r + padding + 1)
        
        # 提取区域
        region = image[y1:y2, x1:x2]
        
        if region.size == 0:
            return None
        
        # 调整圆心坐标到区域坐标系
        region_cx = x - x1
        region_cy = y - y1
        
        # 创建圆形蒙版
        mask = self.create_circle_mask(region.shape[1], region.shape[0], 
                                     region_cx, region_cy, r)
        
        if transparent_background:
            # 创建带透明背景的图像
            if len(region.shape) == 2:
                region = cv2.cvtColor(region, cv2.COLOR_GRAY2BGR)
            
            # 转换为RGBA
            rgba_image = cv2.cvtColor(region, cv2.COLOR_BGR2RGBA)
            
            # 应用蒙版作为Alpha通道
            rgba_image[:, :, 3] = mask
            
            return rgba_image
        else:
            # 应用蒙版到原图像
            if len(region.shape) == 3:
                masked_region = region.copy()
                for i in range(3):
                    masked_region[:, :, i] = cv2.bitwise_and(
                        masked_region[:, :, i], mask
                    )
            else:
                masked_region = cv2.bitwise_and(region, mask)
            
            return masked_region
    
    def capture_circles(self, image: np.ndarray, circles: List[Circle],
                       save_individual: bool = True,
                       save_combined: bool = False) -> Dict[str, Any]:
        """
        批量截图圆形区域
        
        Args:
            image: 原始图像
            circles: 圆形列表
            save_individual: 是否保存单独的圆形图像
            save_combined: 是否保存组合图像
            
        Returns:
            截图结果信息
        """
        if not circles:
            return {"status": "error", "message": "没有圆形可截图"}
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = {
            "timestamp": timestamp,
            "total_circles": len(circles),
            "successful_captures": 0,
            "individual_files": [],
            "combined_file": None,
            "detection_data_file": None,
            "source_image_shape": image.shape
        }
        
        individual_images = []
        
        # 逐个处理圆形
        for i, circle in enumerate(circles):
            try:
                # 提取圆形区域
                circle_image = self.extract_circle_region(
                    image, circle, 
                    padding=10, 
                    transparent_background=True
                )
                
                if circle_image is not None:
                    individual_images.append((circle, circle_image))
                    results["successful_captures"] += 1
                    
                    if save_individual:
                        # 保存单独的圆形图像
                        filename = f"circle_{i+1:02d}_{timestamp}.png"
                        filepath = os.path.join(self.save_directory, filename)
                        
                        # 使用PIL保存透明PNG
                        pil_image = Image.fromarray(circle_image, 'RGBA')
                        pil_image.save(filepath, 'PNG')
                        
                        results["individual_files"].append({
                            "index": i + 1,
                            "filename": filename,
                            "filepath": filepath,
                            "circle": {
                                "x": circle.x,
                                "y": circle.y,
                                "radius": circle.radius,
                                "confidence": circle.confidence,
                                "adjusted": circle.adjusted
                            },
                            "file_size": os.path.getsize(filepath)
                        })
                        
            except Exception as e:
                print(f"截图圆形 {i+1} 失败: {e}")
        
        # 保存组合图像（如果需要）
        if save_combined and individual_images:
            combined_file = self._create_combined_image(individual_images, timestamp)
            if combined_file:
                results["combined_file"] = combined_file
        
        # 保存检测数据
        data_file = self._save_detection_data(circles, results, timestamp)
        if data_file:
            results["detection_data_file"] = data_file
        
        return results
    
    def _create_combined_image(self, individual_images: List[Tuple[Circle, np.ndarray]], 
                              timestamp: str) -> Optional[Dict[str, Any]]:
        """创建组合图像"""
        if not individual_images:
            return None
        
        try:
            # 计算组合图像尺寸
            total_width = 0
            max_height = 0
            
            for circle, img in individual_images:
                total_width += img.shape[1] + 10  # 10像素间距
                max_height = max(max_height, img.shape[0])
            
            total_width -= 10  # 移除最后的间距
            
            # 创建组合图像
            combined = np.zeros((max_height, total_width, 4), dtype=np.uint8)
            
            # 拼接图像
            x_offset = 0
            for circle, img in individual_images:
                h, w = img.shape[:2]
                y_offset = (max_height - h) // 2  # 垂直居中
                
                combined[y_offset:y_offset+h, x_offset:x_offset+w] = img
                x_offset += w + 10
            
            # 保存组合图像
            filename = f"circles_combined_{timestamp}.png"
            filepath = os.path.join(self.save_directory, filename)
            
            pil_image = Image.fromarray(combined, 'RGBA')
            pil_image.save(filepath, 'PNG')
            
            return {
                "filename": filename,
                "filepath": filepath,
                "file_size": os.path.getsize(filepath),
                "dimensions": (total_width, max_height),
                "circle_count": len(individual_images)
            }
            
        except Exception as e:
            print(f"创建组合图像失败: {e}")
            return None
    
    def _save_detection_data(self, circles: List[Circle], 
                           results: Dict[str, Any], 
                           timestamp: str) -> Optional[str]:
        """保存检测数据到JSON文件"""
        try:
            # 准备数据
            data = {
                "detection_info": {
                    "timestamp": timestamp,
                    "datetime": datetime.now().isoformat(),
                    "total_detected": len(circles),
                    "successful_captures": results["successful_captures"],
                    "source_image_shape": results["source_image_shape"],
                    "detector_params": circle_detector.get_detection_info()
                },
                "circles": []
            }
            
            # 添加圆形数据
            for i, circle in enumerate(circles):
                circle_data = {
                    "index": i + 1,
                    "center": {"x": circle.x, "y": circle.y},
                    "radius": circle.radius,
                    "confidence": round(circle.confidence, 4),
                    "adjusted": circle.adjusted,
                    "original_center": {"x": circle.original_x, "y": circle.original_y},
                    "original_radius": circle.original_radius
                }
                data["circles"].append(circle_data)
            
            # 添加文件信息
            data["output_files"] = {
                "individual_files": results.get("individual_files", []),
                "combined_file": results.get("combined_file"),
                "save_directory": self.save_directory
            }
            
            # 保存JSON文件
            filename = f"circle_detection_data_{timestamp}.json"
            filepath = os.path.join(self.data_directory, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return filepath
            
        except Exception as e:
            print(f"保存检测数据失败: {e}")
            return None
    
    def load_detection_data(self, filepath: str) -> Optional[Dict[str, Any]]:
        """从JSON文件加载检测数据"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载检测数据失败: {e}")
            return None
    
    def create_preview_image(self, image: np.ndarray, circles: List[Circle],
                           show_confidence: bool = True,
                           show_radius: bool = True) -> np.ndarray:
        """
        创建预览图像，显示检测到的圆形
        
        Args:
            image: 原始图像
            circles: 圆形列表
            show_confidence: 是否显示置信度
            show_radius: 是否显示半径
            
        Returns:
            带有标注的预览图像
        """
        preview = image.copy()
        if len(preview.shape) == 2:
            preview = cv2.cvtColor(preview, cv2.COLOR_GRAY2BGR)
        
        for i, circle in enumerate(circles):
            # 根据置信度选择颜色
            if circle.confidence > 0.7:
                color = (0, 255, 0)  # 绿色 - 高置信度
            elif circle.confidence > 0.4:
                color = (0, 255, 255)  # 黄色 - 中等置信度
            else:
                color = (0, 0, 255)  # 红色 - 低置信度
            
            # 画圆形
            cv2.circle(preview, (circle.x, circle.y), circle.radius, color, 2)
            
            # 画圆心
            cv2.circle(preview, (circle.x, circle.y), 3, color, -1)
            
            # 添加标注
            texts = [f"#{i+1}"]
            if show_confidence:
                texts.append(f"C:{circle.confidence:.2f}")
            if show_radius:
                texts.append(f"R:{circle.radius}")
            
            text = " ".join(texts)
            
            # 计算文本位置
            text_x = circle.x - 30
            text_y = circle.y - circle.radius - 10
            
            # 确保文本在图像内
            text_x = max(10, min(text_x, preview.shape[1] - 100))
            text_y = max(20, text_y)
            
            cv2.putText(preview, text, (text_x, text_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            # 如果圆形被调整过，添加特殊标记
            if circle.adjusted:
                cv2.putText(preview, "ADJ", 
                           (circle.x + circle.radius - 20, circle.y + 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 255), 1)
        
        return preview
    
    def get_capture_statistics(self) -> Dict[str, Any]:
        """获取截图统计信息"""
        try:
            # 统计文件数量
            circle_files = list(Path(self.save_directory).glob("circle_*.png"))
            combined_files = list(Path(self.save_directory).glob("circles_combined_*.png"))
            data_files = list(Path(self.data_directory).glob("circle_detection_data_*.json"))
            
            # 计算总文件大小
            total_size = 0
            for file_path in circle_files + combined_files:
                total_size += file_path.stat().st_size
            
            return {
                "total_circle_images": len(circle_files),
                "total_combined_images": len(combined_files),
                "total_data_files": len(data_files),
                "total_file_size_bytes": total_size,
                "total_file_size_mb": round(total_size / (1024 * 1024), 2),
                "save_directory": self.save_directory,
                "data_directory": self.data_directory
            }
            
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {}


# 全局圆形截图实例
circle_capture = CircleCapture()