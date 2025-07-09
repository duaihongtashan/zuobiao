"""批处理模块 - 批量图像处理和参数批量应用"""

import os
import time
import threading
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional, Tuple
from dataclasses import dataclass
import queue
import concurrent.futures
import psutil

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    np = None
    print("警告: OpenCV 未安装，批处理功能将被禁用")

from core.config import config_manager
from utils.file_manager import file_manager

if CV2_AVAILABLE:
    from core.edge_detection import edge_detector, EdgeDetectionParams, EdgeDetectionResult


@dataclass
class BatchItem:
    """批处理项目"""
    file_path: str
    output_path: str = ""
    params: Optional[EdgeDetectionParams] = None
    status: str = "pending"  # pending, processing, completed, error
    error_message: str = ""
    processing_time: float = 0.0
    result: Optional[EdgeDetectionResult] = None
    image_info: Optional[Dict[str, Any]] = None
    estimated_memory_mb: float = 0.0


@dataclass
class BatchConfig:
    """批处理配置"""
    input_directory: str = ""
    output_directory: str = ""
    file_formats: List[str] = None
    recursive: bool = False
    overwrite_existing: bool = False
    save_original: bool = True
    save_edges: bool = True
    save_comparison: bool = False
    max_workers: int = 4
    
    def __post_init__(self):
        if self.file_formats is None:
            self.file_formats = ["jpg", "jpeg", "png", "bmp", "tiff"]
    
    # 图片处理限制
    max_resolution_pixels: int = 16777216  # 4096x4096 = 16M pixels
    max_width: int = 8192
    max_height: int = 8192
    max_memory_mb_per_image: float = 512.0  # 单张图片最大内存占用
    enable_auto_resize: bool = True  # 自动缩放超大图片
    memory_safety_factor: float = 0.8  # 内存安全系数


class BatchProgress:
    """批处理进度管理"""
    
    def __init__(self):
        self.total_files = 0
        self.processed_files = 0
        self.completed_files = 0
        self.error_files = 0
        self.start_time = 0.0
        self.current_file = ""
        self.status = "idle"  # idle, running, paused, completed, cancelled
        
    def reset(self):
        """重置进度"""
        self.total_files = 0
        self.processed_files = 0
        self.completed_files = 0
        self.error_files = 0
        self.start_time = 0.0
        self.current_file = ""
        self.status = "idle"
    
    def get_progress_percentage(self) -> float:
        """获取进度百分比"""
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100
    
    def get_elapsed_time(self) -> float:
        """获取已用时间"""
        if self.start_time == 0:
            return 0.0
        return time.time() - self.start_time
    
    def get_estimated_remaining_time(self) -> float:
        """估算剩余时间"""
        if self.processed_files == 0 or self.total_files == 0:
            return 0.0
        
        elapsed = self.get_elapsed_time()
        avg_time_per_file = elapsed / self.processed_files
        remaining_files = self.total_files - self.processed_files
        
        return avg_time_per_file * remaining_files


class ImageValidator:
    """图片验证器"""
    
    @staticmethod
    def get_image_info(file_path: str) -> Optional[Dict[str, Any]]:
        """获取图片信息而不加载全部数据"""
        try:
            if not CV2_AVAILABLE:
                return None
            
            # 使用OpenCV仅读取图片头信息
            image = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
            if image is None:
                return None
            
            height, width = image.shape[:2]
            channels = 1 if len(image.shape) == 2 else image.shape[2]
            
            # 计算文件大小
            file_size = os.path.getsize(file_path)
            
            # 计算内存需求（单位：MB）
            # 基础内存：原图 + 处理缓存
            base_memory = (width * height * channels * 4) / (1024 * 1024)  # float32
            # 附加内存：边缘检测、中间结果等
            processing_memory = base_memory * 3  # 估算为3倍
            total_memory = base_memory + processing_memory
            
            # 释放内存
            del image
            
            return {
                "width": width,
                "height": height,
                "channels": channels,
                "total_pixels": width * height,
                "file_size_bytes": file_size,
                "file_size_mb": file_size / (1024 * 1024),
                "estimated_memory_mb": total_memory,
                "base_memory_mb": base_memory,
                "processing_memory_mb": processing_memory
            }
            
        except Exception as e:
            print(f"获取图片信息失败 {file_path}: {e}")
            return None
    
    @staticmethod
    def validate_image_size(image_info: Dict[str, Any], config: BatchConfig) -> Tuple[bool, str]:
        """验证图片尺寸是否符合要求"""
        if not image_info:
            return False, "无法获取图片信息"
        
        width = image_info["width"]
        height = image_info["height"]
        total_pixels = image_info["total_pixels"]
        estimated_memory = image_info["estimated_memory_mb"]
        
        # 检查分辨率限制
        if width > config.max_width:
            return False, f"图片宽度超出限制: {width} > {config.max_width}"
        
        if height > config.max_height:
            return False, f"图片高度超出限制: {height} > {config.max_height}"
        
        if total_pixels > config.max_resolution_pixels:
            return False, f"图片像素数超出限制: {total_pixels} > {config.max_resolution_pixels}"
        
        # 检查内存限制
        if estimated_memory > config.max_memory_mb_per_image:
            return False, f"预估内存需求超出限制: {estimated_memory:.1f}MB > {config.max_memory_mb_per_image}MB"
        
        return True, "通过验证"
    
    @staticmethod
    def get_system_memory_info() -> Dict[str, float]:
        """获取系统内存信息"""
        try:
            memory = psutil.virtual_memory()
            return {
                "total_gb": memory.total / (1024**3),
                "available_gb": memory.available / (1024**3),
                "used_gb": memory.used / (1024**3),
                "percent_used": memory.percent,
                "available_mb": memory.available / (1024**2)
            }
        except Exception:
            return {
                "total_gb": 0,
                "available_gb": 0,
                "used_gb": 0,
                "percent_used": 0,
                "available_mb": 0
            }
    
    @staticmethod
    def calculate_batch_memory_requirement(batch_items: List[BatchItem]) -> Dict[str, float]:
        """计算批处理内存需求"""
        total_memory = 0.0
        max_single_memory = 0.0
        valid_items = 0
        
        for item in batch_items:
            if item.image_info:
                memory_needed = item.image_info["estimated_memory_mb"]
                total_memory += memory_needed
                max_single_memory = max(max_single_memory, memory_needed)
                valid_items += 1
        
        # 考虑并发处理的内存需求
        concurrent_memory = max_single_memory * 4  # 假设最多4个并发
        
        return {
            "total_memory_mb": total_memory,
            "max_single_memory_mb": max_single_memory,
            "concurrent_memory_mb": concurrent_memory,
            "valid_items": valid_items,
            "average_memory_mb": total_memory / max(1, valid_items)
        }


class BatchProcessor:
    """批处理器"""
    
    def __init__(self):
        self.config = BatchConfig()
        self.progress = BatchProgress()
        self.batch_items: List[BatchItem] = []
        self.executor: Optional[concurrent.futures.ThreadPoolExecutor] = None
        self.futures: List[concurrent.futures.Future] = []
        self.is_cancelled = False
        self.is_paused = False
        
        # 回调函数
        self.on_progress_changed: Optional[Callable] = None
        self.on_item_completed: Optional[Callable] = None
        self.on_batch_completed: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        # 图片验证器
        self.validator = ImageValidator()
    
    def set_config(self, config: BatchConfig):
        """设置批处理配置"""
        self.config = config
    
    def scan_input_directory(self) -> List[str]:
        """扫描输入目录，获取要处理的文件列表"""
        if not self.config.input_directory:
            return []
        
        input_path = Path(self.config.input_directory)
        if not input_path.exists():
            return []
        
        image_files = []
        
        # 构建文件扩展名列表
        extensions = [f".{fmt.lower()}" for fmt in self.config.file_formats]
        
        try:
            if self.config.recursive:
                # 递归扫描
                for ext in extensions:
                    pattern = f"**/*{ext}"
                    image_files.extend(input_path.glob(pattern))
            else:
                # 仅扫描当前目录
                for file_path in input_path.iterdir():
                    if file_path.is_file() and file_path.suffix.lower() in extensions:
                        image_files.append(file_path)
            
            # 转换为字符串列表并排序
            return sorted([str(f) for f in image_files])
            
        except Exception as e:
            print(f"扫描输入目录失败: {e}")
            return []
    
    def prepare_batch(self, params: EdgeDetectionParams) -> bool:
        """准备批处理任务"""
        try:
            # 扫描输入文件
            input_files = self.scan_input_directory()
            if not input_files:
                if self.on_error:
                    self.on_error("没有找到可处理的图像文件")
                return False
            
            # 确保输出目录存在
            if not file_manager.ensure_directory_exists(self.config.output_directory):
                if self.on_error:
                    self.on_error(f"无法创建输出目录: {self.config.output_directory}")
                return False
            
            # 检查系统内存
            system_memory = self.validator.get_system_memory_info()
            print(f"系统内存信息: 可用 {system_memory['available_gb']:.1f}GB / 总共 {system_memory['total_gb']:.1f}GB")
            
            # 创建批处理项目
            self.batch_items.clear()
            skipped_files = []
            oversized_files = []
            
            for file_path in input_files:
                input_file = Path(file_path)
                base_name = input_file.stem
                
                # 获取图片信息
                image_info = self.validator.get_image_info(file_path)
                if not image_info:
                    skipped_files.append((file_path, "无法读取图片信息"))
                    continue
                
                # 验证图片尺寸
                is_valid, reason = self.validator.validate_image_size(image_info, self.config)
                if not is_valid:
                    if self.config.enable_auto_resize and "超出限制" in reason:
                        # 标记为需要缩放的文件
                        oversized_files.append((file_path, reason))
                        print(f"图片将被自动缩放: {file_path} - {reason}")
                    else:
                        skipped_files.append((file_path, reason))
                        continue
                
                # 生成输出路径
                if self.config.save_edges:
                    output_path = str(Path(self.config.output_directory) / f"{base_name}_edges.png")
                else:
                    output_path = str(Path(self.config.output_directory) / f"{base_name}_processed.png")
                
                # 检查是否覆盖现有文件
                if not self.config.overwrite_existing and Path(output_path).exists():
                    continue
                
                # 创建批处理项目
                item = BatchItem(
                    file_path=file_path,
                    output_path=output_path,
                    params=EdgeDetectionParams(**params.to_dict()) if params else None,
                    image_info=image_info,
                    estimated_memory_mb=image_info["estimated_memory_mb"]
                )
                self.batch_items.append(item)
            
            # 计算批处理内存需求
            memory_req = self.validator.calculate_batch_memory_requirement(self.batch_items)
            print(f"批处理内存需求: 并发处理 {memory_req['concurrent_memory_mb']:.1f}MB, 单张最大 {memory_req['max_single_memory_mb']:.1f}MB")
            
            # 检查内存是否足够
            available_memory_mb = system_memory['available_mb']
            required_memory_mb = memory_req['concurrent_memory_mb']
            
            if required_memory_mb > available_memory_mb * self.config.memory_safety_factor:
                # 调整并发数量
                safe_workers = max(1, int(available_memory_mb * self.config.memory_safety_factor / memory_req['max_single_memory_mb']))
                if safe_workers < self.config.max_workers:
                    print(f"内存不足，调整并发数量: {self.config.max_workers} -> {safe_workers}")
                    self.config.max_workers = safe_workers
            
            # 报告结果
            if skipped_files:
                print(f"跳过了 {len(skipped_files)} 个文件:")
                for file_path, reason in skipped_files[:5]:  # 只显示前5个
                    print(f"  {os.path.basename(file_path)}: {reason}")
                if len(skipped_files) > 5:
                    print(f"  ... 及其他 {len(skipped_files) - 5} 个文件")
            
            if oversized_files:
                print(f"将自动缩放 {len(oversized_files)} 个大尺寸图片")
            
            # 更新进度信息
            self.progress.reset()
            self.progress.total_files = len(self.batch_items)
            
            if len(self.batch_items) == 0:
                if self.on_error:
                    self.on_error("没有可处理的图片文件")
                return False
            
            return True
            
        except Exception as e:
            if self.on_error:
                self.on_error(f"准备批处理失败: {e}")
            return False
    
    def load_and_preprocess_image(self, file_path: str, image_info: Dict[str, Any]) -> Optional[np.ndarray]:
        """加载和预处理图像，处理超大图片"""
        try:
            # 先试着正常加载
            image = cv2.imread(file_path)
            if image is None:
                # 尝试不同的加载方式
                try:
                    # 使用PIL加载再转换
                    from PIL import Image as PILImage
                    pil_image = PILImage.open(file_path)
                    if pil_image.mode == 'RGBA':
                        pil_image = pil_image.convert('RGB')
                    image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                except Exception as e:
                    print(f"PIL加载失败: {e}")
                    return None
            
            if image is None:
                return None
            
            # 检查是否需要缩放
            height, width = image.shape[:2]
            
            # 计算缩放因子
            scale_factor = 1.0
            if width > self.config.max_width or height > self.config.max_height:
                scale_w = self.config.max_width / width
                scale_h = self.config.max_height / height
                scale_factor = min(scale_w, scale_h)
            
            # 检查像素数限制
            if width * height > self.config.max_resolution_pixels:
                pixel_scale = (self.config.max_resolution_pixels / (width * height)) ** 0.5
                scale_factor = min(scale_factor, pixel_scale)
            
            # 检查内存限制
            if image_info and image_info.get('estimated_memory_mb', 0) > self.config.max_memory_mb_per_image:
                memory_scale = (self.config.max_memory_mb_per_image / image_info['estimated_memory_mb']) ** 0.5
                scale_factor = min(scale_factor, memory_scale)
            
            # 执行缩放
            if scale_factor < 1.0:
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                print(f"缩放图片: {width}x{height} -> {new_width}x{new_height} (缩放系数: {scale_factor:.3f})")
                image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            return image
            
        except Exception as e:
            print(f"加载图像失败 {file_path}: {e}")
            return None
    
    def process_single_item(self, item: BatchItem) -> BatchItem:
        """处理单个批处理项目"""
        if not CV2_AVAILABLE:
            item.status = "error"
            item.error_message = "OpenCV未安装"
            return item
        
        start_time = time.time()
        item.status = "processing"
        
        try:
            # 更新当前处理文件
            self.progress.current_file = os.path.basename(item.file_path)
            
            # 检查是否被取消或暂停
            if self.is_cancelled:
                item.status = "error"
                item.error_message = "批处理已取消"
                return item
            
            while self.is_paused:
                time.sleep(0.1)
                if self.is_cancelled:
                    item.status = "error"
                    item.error_message = "批处理已取消"
                    return item
            
            # 加载和预处理图像
            image = self.load_and_preprocess_image(item.file_path, item.image_info)
            if image is None:
                item.status = "error"
                item.error_message = f"无法读取图像: {item.file_path}"
                
                # 提供更详细的错误信息
                if item.image_info:
                    item.error_message += f" (原始尺寸: {item.image_info['width']}x{item.image_info['height']}, 预估内存: {item.image_info['estimated_memory_mb']:.1f}MB)"
                
                return item
            
            # 设置检测参数
            if item.params:
                edge_detector.set_params(item.params)
            
            # 执行边缘检测
            result = edge_detector.detect_edges_sync(image)
            item.result = result
            
            # 保存结果
            success = self.save_processing_result(item, result)
            
            if success:
                item.status = "completed"
            else:
                item.status = "error"
                item.error_message = "保存结果失败"
            
            item.processing_time = time.time() - start_time
            
        except MemoryError as e:
            item.status = "error"
            item.error_message = f"内存不足: {e}"
            item.processing_time = time.time() - start_time
        except Exception as e:
            item.status = "error"
            item.error_message = str(e)
            item.processing_time = time.time() - start_time
        
        return item
    
    def save_processing_result(self, item: BatchItem, result: EdgeDetectionResult) -> bool:
        """保存处理结果"""
        try:
            output_dir = Path(item.output_path).parent
            base_name = Path(item.file_path).stem
            
            success_count = 0
            
            # 保存原图
            if self.config.save_original:
                original_path = output_dir / f"{base_name}_original.png"
                if cv2.imwrite(str(original_path), result.original_image):
                    success_count += 1
            
            # 保存边缘图
            if self.config.save_edges:
                edges_path = output_dir / f"{base_name}_edges.png"
                if cv2.imwrite(str(edges_path), result.edge_image):
                    success_count += 1
            
            # 保存对比图
            if self.config.save_comparison:
                comparison_image = edge_detector.create_comparison_image(result, "side_by_side")
                comparison_path = output_dir / f"{base_name}_comparison.png"
                if cv2.imwrite(str(comparison_path), comparison_image):
                    success_count += 1
            
            return success_count > 0
            
        except Exception as e:
            print(f"保存处理结果失败: {e}")
            return False
    
    def start_batch_processing(self, params: EdgeDetectionParams) -> bool:
        """开始批处理"""
        if not self.prepare_batch(params):
            return False
        
        if len(self.batch_items) == 0:
            if self.on_error:
                self.on_error("没有需要处理的文件")
            return False
        
        # 重置状态
        self.is_cancelled = False
        self.is_paused = False
        self.progress.status = "running"
        self.progress.start_time = time.time()
        
        # 启动线程池
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_workers)
        self.futures.clear()
        
        # 提交任务
        for item in self.batch_items:
            future = self.executor.submit(self.process_single_item, item)
            self.futures.append(future)
        
        # 启动监控线程
        monitor_thread = threading.Thread(target=self._monitor_progress, daemon=True)
        monitor_thread.start()
        
        return True
    
    def _monitor_progress(self):
        """监控处理进度"""
        while self.progress.status == "running":
            completed_count = 0
            error_count = 0
            
            for i, future in enumerate(self.futures):
                if future.done():
                    try:
                        item = future.result()
                        self.batch_items[i] = item
                        
                        if item.status == "completed":
                            completed_count += 1
                        elif item.status == "error":
                            error_count += 1
                        
                        # 调用项目完成回调
                        if self.on_item_completed:
                            self.on_item_completed(item)
                            
                    except Exception as e:
                        error_count += 1
                        if self.on_error:
                            self.on_error(f"处理任务时出错: {e}")
            
            # 更新进度
            self.progress.processed_files = completed_count + error_count
            self.progress.completed_files = completed_count
            self.progress.error_files = error_count
            
            # 调用进度回调
            if self.on_progress_changed:
                self.on_progress_changed(self.progress)
            
            # 检查是否完成
            if self.progress.processed_files >= self.progress.total_files:
                self.progress.status = "completed"
                if self.on_batch_completed:
                    self.on_batch_completed(self.get_batch_summary())
                break
            
            # 检查是否被取消
            if self.is_cancelled:
                self.progress.status = "cancelled"
                break
            
            time.sleep(0.5)  # 更新间隔
        
        # 清理资源
        if self.executor:
            self.executor.shutdown(wait=False)
    
    def pause_processing(self):
        """暂停处理"""
        self.is_paused = True
        self.progress.status = "paused"
    
    def resume_processing(self):
        """恢复处理"""
        self.is_paused = False
        self.progress.status = "running"
    
    def cancel_processing(self):
        """取消处理"""
        self.is_cancelled = True
        self.is_paused = False
        self.progress.status = "cancelled"
        
        # 取消所有未完成的任务
        for future in self.futures:
            if not future.done():
                future.cancel()
        
        # 关闭线程池
        if self.executor:
            self.executor.shutdown(wait=False)
    
    def get_batch_summary(self) -> Dict[str, Any]:
        """获取批处理摘要"""
        return {
            "total_files": self.progress.total_files,
            "completed_files": self.progress.completed_files,
            "error_files": self.progress.error_files,
            "total_time": self.progress.get_elapsed_time(),
            "average_time_per_file": (
                self.progress.get_elapsed_time() / max(1, self.progress.processed_files)
            ),
            "success_rate": (
                self.progress.completed_files / max(1, self.progress.total_files) * 100
            ),
            "status": self.progress.status
        }
    
    def get_failed_items(self) -> List[BatchItem]:
        """获取失败的处理项目"""
        return [item for item in self.batch_items if item.status == "error"]
    
    def export_batch_report(self, report_path: str) -> bool:
        """导出批处理报告"""
        try:
            import json
            from datetime import datetime
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "config": {
                    "input_directory": self.config.input_directory,
                    "output_directory": self.config.output_directory,
                    "file_formats": self.config.file_formats,
                    "recursive": self.config.recursive,
                    "max_workers": self.config.max_workers
                },
                "summary": self.get_batch_summary(),
                "items": []
            }
            
            for item in self.batch_items:
                item_data = {
                    "file_path": item.file_path,
                    "output_path": item.output_path,
                    "status": item.status,
                    "error_message": item.error_message,
                    "processing_time": item.processing_time
                }
                
                if item.result:
                    item_data["edge_count"] = item.result.edge_count
                    item_data["result_processing_time"] = item.result.processing_time
                
                report["items"].append(item_data)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"导出批处理报告失败: {e}")
            return False


# 全局批处理器实例
batch_processor = BatchProcessor()


def create_batch_config(**kwargs) -> BatchConfig:
    """创建批处理配置的便捷函数"""
    return BatchConfig(**kwargs)


if __name__ == "__main__":
    # 测试代码
    print("批处理模块测试")
    
    # 创建测试配置
    config = BatchConfig(
        input_directory="test_images",
        output_directory="test_output",
        max_workers=2
    )
    
    processor = BatchProcessor()
    processor.set_config(config)
    
    # 测试扫描
    files = processor.scan_input_directory()
    print(f"找到 {len(files)} 个图像文件")
    
    print("批处理模块测试完成")