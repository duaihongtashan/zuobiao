"""边缘检测核心模块"""

import cv2
import numpy as np
import time
import threading
from typing import Optional, Dict, Any, Tuple, Callable
from dataclasses import dataclass
from pathlib import Path
import queue
from functools import lru_cache


@dataclass
class EdgeDetectionParams:
    """边缘检测参数类"""
    # Canny核心参数
    threshold1: int = 50         # 低阈值
    threshold2: int = 150        # 高阈值
    aperture_size: int = 3       # Sobel算子大小
    l2_gradient: bool = False    # 梯度计算方式
    
    # 预处理参数
    gaussian_blur: bool = True
    blur_kernel_size: int = 5
    median_filter: bool = False
    median_kernel_size: int = 5
    clahe_enabled: bool = False
    clahe_clip_limit: float = 2.0
    
    # 后处理参数
    morphology_enabled: bool = False
    morph_kernel_size: int = 3
    edge_thinning: bool = False
    remove_noise: bool = True
    
    def __post_init__(self):
        """参数验证和修正"""
        # 确保参数在有效范围内
        self.threshold1 = max(1, min(255, self.threshold1))
        self.threshold2 = max(1, min(255, self.threshold2))
        self.blur_kernel_size = max(3, self.blur_kernel_size)
        if self.blur_kernel_size % 2 == 0:
            self.blur_kernel_size += 1  # 确保是奇数
        
        # 确保高阈值大于低阈值
        if self.threshold2 <= self.threshold1:
            self.threshold2 = self.threshold1 + 50
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'threshold1': self.threshold1,
            'threshold2': self.threshold2,
            'aperture_size': self.aperture_size,
            'l2_gradient': self.l2_gradient,
            'gaussian_blur': self.gaussian_blur,
            'blur_kernel_size': self.blur_kernel_size,
            'median_filter': self.median_filter,
            'median_kernel_size': self.median_kernel_size,
            'clahe_enabled': self.clahe_enabled,
            'clahe_clip_limit': self.clahe_clip_limit,
            'morphology_enabled': self.morphology_enabled,
            'morph_kernel_size': self.morph_kernel_size,
            'edge_thinning': self.edge_thinning,
            'remove_noise': self.remove_noise
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EdgeDetectionParams':
        """从字典创建参数对象"""
        return cls(**data)


@dataclass
class EdgeDetectionResult:
    """边缘检测结果类"""
    original_image: np.ndarray
    edge_image: np.ndarray
    processed_image: Optional[np.ndarray] = None
    processing_time: float = 0.0
    edge_count: int = 0
    params_used: Optional[EdgeDetectionParams] = None
    timestamp: float = 0.0
    
    def __post_init__(self):
        """后处理初始化"""
        if self.timestamp == 0.0:
            self.timestamp = time.time()
        
        # 计算边缘像素数量
        if self.edge_image is not None:
            self.edge_count = np.count_nonzero(self.edge_image)


class ProcessingQueue:
    """图像处理队列 - 支持后台处理和去抖动"""
    
    def __init__(self, max_workers: int = 2, debounce_delay: float = 0.3):
        self.max_workers = max_workers
        self.debounce_delay = debounce_delay
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.workers = []
        self.running = True
        self.last_request_time = 0.0
        self.pending_task = None
        
        # 启动工作线程
        for i in range(max_workers):
            worker = threading.Thread(target=self._worker, daemon=True)
            worker.start()
            self.workers.append(worker)
        
        # 启动去抖动线程
        self.debounce_thread = threading.Thread(target=self._debounce_worker, daemon=True)
        self.debounce_thread.start()
    
    def _worker(self):
        """工作线程"""
        while self.running:
            try:
                task = self.task_queue.get(timeout=1.0)
                if task is None:
                    break
                
                func, args, kwargs, callback = task
                try:
                    result = func(*args, **kwargs)
                    if callback:
                        callback(result)
                except Exception as e:
                    print(f"处理任务时发生错误: {e}")
                
                self.task_queue.task_done()
            except queue.Empty:
                continue
    
    def _debounce_worker(self):
        """去抖动工作线程"""
        while self.running:
            time.sleep(0.1)
            current_time = time.time()
            
            if (self.pending_task and 
                current_time - self.last_request_time >= self.debounce_delay):
                
                # 执行挂起的任务
                self.task_queue.put(self.pending_task)
                self.pending_task = None
    
    def submit_debounced(self, func: Callable, *args, callback: Optional[Callable] = None, **kwargs):
        """提交去抖动任务"""
        self.last_request_time = time.time()
        self.pending_task = (func, args, kwargs, callback)
    
    def submit_immediate(self, func: Callable, *args, callback: Optional[Callable] = None, **kwargs):
        """立即提交任务"""
        self.task_queue.put((func, args, kwargs, callback))
    
    def shutdown(self):
        """关闭队列"""
        self.running = False
        for _ in self.workers:
            self.task_queue.put(None)


class EdgeDetectionManager:
    """边缘检测管理器 - 核心处理引擎"""
    
    def __init__(self):
        self.params = EdgeDetectionParams()
        self.processing_queue = ProcessingQueue(max_workers=2, debounce_delay=0.3)
        self.result_cache = {}  # 简单的结果缓存
        self.cache_size_limit = 10
        
        # 状态跟踪
        self.is_processing = False
        self.last_result = None
        self.statistics = {
            'total_processed': 0,
            'total_processing_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def set_params(self, params: EdgeDetectionParams):
        """设置检测参数"""
        self.params = params
        # 清空缓存，因为参数已改变
        self.result_cache.clear()
    
    def update_params(self, **kwargs):
        """更新部分参数"""
        for key, value in kwargs.items():
            if hasattr(self.params, key):
                setattr(self.params, key, value)
        
        # 重新验证参数
        self.params.__post_init__()
        
        # 清空缓存
        self.result_cache.clear()
    
    def get_cache_key(self, image: np.ndarray, params: EdgeDetectionParams) -> str:
        """生成缓存键"""
        # 使用图像形状、参数哈希值生成键
        image_hash = hash(image.tobytes()) if image.size < 1000000 else hash(str(image.shape))
        params_hash = hash(str(params.to_dict()))
        return f"{image_hash}_{params_hash}"
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """图像预处理"""
        processed = image.copy()
        
        # 转换为灰度图
        if len(processed.shape) == 3:
            processed = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
        
        # CLAHE直方图均衡化
        if self.params.clahe_enabled:
            clahe = cv2.createCLAHE(clipLimit=self.params.clahe_clip_limit, tileGridSize=(8,8))
            processed = clahe.apply(processed)
        
        # 高斯模糊
        if self.params.gaussian_blur:
            kernel_size = self.params.blur_kernel_size
            processed = cv2.GaussianBlur(processed, (kernel_size, kernel_size), 0)
        
        # 中值滤波
        if self.params.median_filter:
            kernel_size = self.params.median_kernel_size
            processed = cv2.medianBlur(processed, kernel_size)
        
        return processed
    
    def _postprocess_edges(self, edges: np.ndarray) -> np.ndarray:
        """边缘后处理"""
        processed = edges.copy()
        
        # 噪声去除
        if self.params.remove_noise:
            # 使用开运算去除小噪声
            kernel = np.ones((2, 2), np.uint8)
            processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel)
        
        # 形态学操作
        if self.params.morphology_enabled:
            kernel_size = self.params.morph_kernel_size
            kernel = np.ones((kernel_size, kernel_size), np.uint8)
            processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
        
        # 边缘细化
        if self.params.edge_thinning:
            # 使用Zhang-Suen算法进行细化
            processed = self._zhang_suen_thinning(processed)
        
        return processed
    
    def _zhang_suen_thinning(self, image: np.ndarray) -> np.ndarray:
        """Zhang-Suen边缘细化算法"""
        # 简化实现，实际可以使用skimage.morphology.thin
        try:
            from skimage.morphology import thin
            binary = image > 0
            thinned = thin(binary)
            return (thinned * 255).astype(np.uint8)
        except ImportError:
            # 如果没有skimage，直接返回原图
            return image
    
    def detect_edges_sync(self, image: np.ndarray) -> EdgeDetectionResult:
        """同步边缘检测"""
        start_time = time.time()
        
        # 检查缓存
        cache_key = self.get_cache_key(image, self.params)
        if cache_key in self.result_cache:
            self.statistics['cache_hits'] += 1
            cached_result = self.result_cache[cache_key]
            # 更新时间戳
            cached_result.timestamp = time.time()
            return cached_result
        
        self.statistics['cache_misses'] += 1
        
        try:
            # 预处理
            preprocessed = self._preprocess_image(image)
            
            # Canny边缘检测
            edges = cv2.Canny(
                preprocessed,
                self.params.threshold1,
                self.params.threshold2,
                apertureSize=self.params.aperture_size,
                L2gradient=self.params.l2_gradient
            )
            
            # 后处理
            processed_edges = self._postprocess_edges(edges)
            
            # 创建结果
            processing_time = time.time() - start_time
            result = EdgeDetectionResult(
                original_image=image,
                edge_image=processed_edges,
                processed_image=preprocessed,
                processing_time=processing_time,
                params_used=EdgeDetectionParams(**self.params.to_dict())
            )
            
            # 更新统计
            self.statistics['total_processed'] += 1
            self.statistics['total_processing_time'] += processing_time
            
            # 缓存结果
            self._cache_result(cache_key, result)
            
            self.last_result = result
            return result
            
        except Exception as e:
            print(f"边缘检测失败: {e}")
            # 返回错误结果
            return EdgeDetectionResult(
                original_image=image,
                edge_image=np.zeros_like(image[:,:] if len(image.shape) == 3 else image, dtype=np.uint8),
                processing_time=time.time() - start_time
            )
    
    def detect_edges_async(self, image: np.ndarray, callback: Optional[Callable] = None):
        """异步边缘检测 - 带去抖动"""
        def process():
            result = self.detect_edges_sync(image)
            return result
        
        self.processing_queue.submit_debounced(process, callback=callback)
    
    def detect_edges_immediate(self, image: np.ndarray, callback: Optional[Callable] = None):
        """立即异步边缘检测 - 不去抖动"""
        def process():
            result = self.detect_edges_sync(image)
            return result
        
        self.processing_queue.submit_immediate(process, callback=callback)
    
    def _cache_result(self, key: str, result: EdgeDetectionResult):
        """缓存结果"""
        # 如果缓存已满，删除最旧的条目
        if len(self.result_cache) >= self.cache_size_limit:
            oldest_key = min(self.result_cache.keys(), 
                           key=lambda k: self.result_cache[k].timestamp)
            del self.result_cache[oldest_key]
        
        self.result_cache[key] = result
    
    def clear_cache(self):
        """清空缓存"""
        self.result_cache.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        stats = self.statistics.copy()
        if stats['total_processed'] > 0:
            stats['average_processing_time'] = stats['total_processing_time'] / stats['total_processed']
        else:
            stats['average_processing_time'] = 0.0
        
        stats['cache_hit_rate'] = (stats['cache_hits'] / max(1, stats['cache_hits'] + stats['cache_misses'])) * 100
        stats['cached_results'] = len(self.result_cache)
        
        return stats
    
    def create_comparison_image(self, result: EdgeDetectionResult, mode: str = "side_by_side") -> np.ndarray:
        """创建对比图像"""
        if result.edge_image is None:
            return result.original_image
        
        original = result.original_image
        edges = result.edge_image
        
        # 确保两个图像有相同的通道数
        if len(original.shape) == 3 and len(edges.shape) == 2:
            edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        elif len(original.shape) == 2 and len(edges.shape) == 3:
            original = cv2.cvtColor(original, cv2.COLOR_GRAY2BGR)
            edges_colored = edges
        else:
            edges_colored = edges
        
        if mode == "side_by_side":
            # 左右拼接
            comparison = np.hstack([original, edges_colored])
        elif mode == "overlay":
            # 叠加显示
            if len(original.shape) == 3:
                edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
                edges_colored[:, :, 0] = 0  # 移除蓝色通道
                edges_colored[:, :, 2] = 0  # 移除红色通道
                comparison = cv2.addWeighted(original, 0.7, edges_colored, 0.3, 0)
            else:
                comparison = cv2.addWeighted(original, 0.7, edges, 0.3, 0)
        else:
            # 默认并排显示
            comparison = np.hstack([original, edges_colored])
        
        return comparison
    
    def shutdown(self):
        """关闭管理器"""
        self.processing_queue.shutdown()


# 全局边缘检测管理器实例
edge_detector = EdgeDetectionManager()


def create_edge_detection_params(**kwargs) -> EdgeDetectionParams:
    """创建边缘检测参数的便捷函数"""
    return EdgeDetectionParams(**kwargs)


def detect_edges_simple(image: np.ndarray, threshold1: int = 50, threshold2: int = 150) -> np.ndarray:
    """简单的边缘检测函数"""
    params = EdgeDetectionParams(threshold1=threshold1, threshold2=threshold2)
    temp_detector = EdgeDetectionManager()
    temp_detector.set_params(params)
    result = temp_detector.detect_edges_sync(image)
    return result.edge_image


if __name__ == "__main__":
    # 测试代码
    print("边缘检测模块测试")
    
    # 创建测试图像
    test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    
    # 测试同步检测
    params = EdgeDetectionParams(threshold1=50, threshold2=150)
    detector = EdgeDetectionManager()
    detector.set_params(params)
    
    result = detector.detect_edges_sync(test_image)
    print(f"检测完成，处理时间: {result.processing_time:.3f}秒")
    print(f"边缘像素数量: {result.edge_count}")
    
    # 测试统计信息
    stats = detector.get_statistics()
    print(f"统计信息: {stats}")
    
    detector.shutdown()
    print("测试完成")