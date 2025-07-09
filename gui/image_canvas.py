"""高级图像显示画布模块"""

import tkinter as tk
from tkinter import ttk
import numpy as np
from PIL import Image, ImageTk
import threading
import time
from typing import Optional, Callable, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class CanvasState:
    """画布状态类"""
    zoom_factor: float = 1.0
    pan_offset: Tuple[int, int] = (0, 0)
    display_mode: str = "original"  # original, edges, comparison
    image_size: Tuple[int, int] = (0, 0)
    canvas_size: Tuple[int, int] = (0, 0)
    
    def reset(self):
        """重置状态"""
        self.zoom_factor = 1.0
        self.pan_offset = (0, 0)


class ImagePyramid:
    """图像金字塔 - 用于多级缩放优化（带内存管理）"""
    
    def __init__(self, max_levels: int = 6, max_memory_mb: float = 512.0):
        self.max_levels = max_levels
        self.max_memory_mb = max_memory_mb  # 最大内存限制（MB）
        self.pyramid = {}  # {zoom_level: PIL.Image}
        self.base_image = None
        self.current_memory_mb = 0.0  # 当前内存使用量
    
    def _calculate_image_memory(self, pil_image) -> float:
        """计算PIL图像的内存使用量（MB）"""
        if pil_image is None:
            return 0.0
        
        width, height = pil_image.size
        # 根据图像模式计算字节数
        if pil_image.mode == 'RGBA':
            bytes_per_pixel = 4
        elif pil_image.mode == 'RGB':
            bytes_per_pixel = 3
        elif pil_image.mode == 'L':
            bytes_per_pixel = 1
        else:
            bytes_per_pixel = 4  # 保守估算
        
        return (width * height * bytes_per_pixel) / (1024 * 1024)
    
    def _cleanup_memory(self, required_memory: float):
        """智能内存清理，优先保留常用缩放级别"""
        if not self.pyramid:
            return
        
        # 定义常用缩放级别（根据用户习惯）
        common_zoom_levels = {1.0, 0.5, 0.25, 2.0, 1.5}  # 保留这些常用级别
        
        # 按使用频率排序（保留基础图像和常用级别）
        zoom_levels = list(self.pyramid.keys())
        if 1.0 in zoom_levels:
            zoom_levels.remove(1.0)  # 始终保留基础图像
        
        # 分类缩放级别
        common_levels = [level for level in zoom_levels if level in common_zoom_levels]
        uncommon_levels = [level for level in zoom_levels if level not in common_zoom_levels]
        
        # 优先删除不常用的级别，按距离1.0的远近排序
        cleanup_order = []
        
        # 首先删除极端的不常用级别
        uncommon_levels.sort(key=lambda x: abs(x - 1.0), reverse=True)
        cleanup_order.extend(uncommon_levels)
        
        # 如果还需要更多内存，再删除常用级别（保留最重要的几个）
        if common_levels:
            # 按重要性排序：优先保留 1.0, 0.5, 2.0
            importance_order = [1.0, 0.5, 2.0, 1.5, 0.25]
            common_levels.sort(key=lambda x: importance_order.index(x) if x in importance_order else 999)
            cleanup_order.extend(reversed(common_levels))  # 从最不重要的开始删除
        
        # 执行清理
        for zoom_level in cleanup_order:
            if self.current_memory_mb + required_memory <= self.max_memory_mb:
                break
            
            if zoom_level in self.pyramid:
                removed_memory = self._calculate_image_memory(self.pyramid[zoom_level])
                del self.pyramid[zoom_level]
                self.current_memory_mb -= removed_memory
                level_type = "常用" if zoom_level in common_zoom_levels else "不常用"
                print(f"清理金字塔缓存: 删除 {level_type} {zoom_level:.2f}x 级别, 释放 {removed_memory:.1f}MB")
                
                # 统计内存清理次数（如果有回调的话）
                if hasattr(self, 'on_memory_cleanup'):
                    self.on_memory_cleanup(zoom_level, removed_memory)
    
    def set_base_image(self, image: np.ndarray):
        """设置基础图像"""
        # 清除之前的金字塔
        self.pyramid.clear()
        self.current_memory_mb = 0.0
        
        # 转换图像格式
        if len(image.shape) == 3:
            # BGR to RGB
            image_rgb = image[:, :, ::-1]
            self.base_image = Image.fromarray(image_rgb)
        else:
            self.base_image = Image.fromarray(image)
        
        # 计算基础图像内存
        base_memory = self._calculate_image_memory(self.base_image)
        
        # 检查基础图像是否超过内存限制
        if base_memory > self.max_memory_mb:
            print(f"警告: 基础图像占用内存 {base_memory:.1f}MB 超过限制 {self.max_memory_mb}MB")
            # 自动缩放基础图像
            scale_factor = (self.max_memory_mb * 0.8 / base_memory) ** 0.5
            new_size = (
                int(self.base_image.size[0] * scale_factor),
                int(self.base_image.size[1] * scale_factor)
            )
            self.base_image = self.base_image.resize(new_size, Image.LANCZOS)
            base_memory = self._calculate_image_memory(self.base_image)
            print(f"自动缩放基础图像到 {new_size}, 内存使用: {base_memory:.1f}MB")
        
        self.pyramid[1.0] = self.base_image
        self.current_memory_mb = base_memory
    
    def get_image_at_zoom(self, zoom_factor: float) -> Optional[Image.Image]:
        """获取指定缩放级别的图像（带内存管理和性能优化）"""
        if self.base_image is None:
            return None
        
        # 如果已缓存，直接返回
        if zoom_factor in self.pyramid:
            return self.pyramid[zoom_factor]
        
        # 计算新尺寸
        original_size = self.base_image.size
        new_size = (
            int(original_size[0] * zoom_factor),
            int(original_size[1] * zoom_factor)
        )
        
        # 预估新图像的内存需求
        estimated_memory = (new_size[0] * new_size[1] * 3) / (1024 * 1024)  # RGB
        
        # 检查内存限制
        if self.current_memory_mb + estimated_memory > self.max_memory_mb:
            self._cleanup_memory(estimated_memory)
        
        # 如果仍然超过限制，直接返回不缓存
        if self.current_memory_mb + estimated_memory > self.max_memory_mb:
            print(f"内存不足，跳过缓存 {zoom_factor:.2f}x 级别")
            # 直接创建不缓存
            return self._create_scaled_image_optimized(new_size, zoom_factor)
        
        try:
            # 创建缩放图像（使用优化算法）
            scaled_image = self._create_scaled_image_optimized(new_size, zoom_factor)
            
            if scaled_image is None:
                return None
            
            # 缓存结果
            if len(self.pyramid) < self.max_levels:
                actual_memory = self._calculate_image_memory(scaled_image)
                self.pyramid[zoom_factor] = scaled_image
                self.current_memory_mb += actual_memory
            
            return scaled_image
            
        except MemoryError:
            print(f"创建 {zoom_factor:.2f}x 缩放图像失败: 内存不足")
            return None
    
    def _create_scaled_image_optimized(self, new_size: tuple, zoom_factor: float) -> Optional[Image.Image]:
        """优化的缩放图像创建方法"""
        try:
            # 选择最佳缩放算法
            if zoom_factor > 1.0:
                # 放大：使用LANCZOS获得更好的质量
                resample = Image.LANCZOS
            elif zoom_factor < 0.5:
                # 大幅缩小：使用渐进式缩放避免性能问题
                return self._progressive_downscale(new_size, zoom_factor)
            else:
                # 中等缩小：使用LANCZOS（比ANTIALIAS更快且质量更好）
                resample = Image.LANCZOS
            
            # 执行缩放
            return self.base_image.resize(new_size, resample)
            
        except Exception as e:
            print(f"优化缩放失败: {e}")
            # 回退到标准方法
            try:
                return self.base_image.resize(new_size, Image.LANCZOS)
            except:
                return None
    
    def _progressive_downscale(self, target_size: tuple, zoom_factor: float) -> Optional[Image.Image]:
        """渐进式缩放，用于大幅度缩小操作"""
        try:
            current_image = self.base_image
            current_size = current_image.size
            
            # 计算缩放步骤，每次最多缩小到一半
            steps = []
            temp_factor = zoom_factor
            while temp_factor < 0.5:
                steps.append(0.5)
                temp_factor /= 0.5
            if temp_factor < 1.0:
                steps.append(temp_factor)
            
            # 逐步缩放
            for step_factor in steps:
                new_step_size = (
                    int(current_size[0] * step_factor),
                    int(current_size[1] * step_factor)
                )
                current_image = current_image.resize(new_step_size, Image.LANCZOS)
                current_size = new_step_size
            
            # 最后调整到精确尺寸
            if current_size != target_size:
                current_image = current_image.resize(target_size, Image.LANCZOS)
            
            return current_image
            
        except Exception as e:
            print(f"渐进式缩放失败: {e}")
            return None
    
    def clear(self):
        """清除金字塔缓存"""
        self.pyramid.clear()
        self.base_image = None
        self.current_memory_mb = 0.0
    
    def get_memory_info(self) -> Dict[str, Any]:
        """获取内存使用信息"""
        return {
            "current_memory_mb": self.current_memory_mb,
            "max_memory_mb": self.max_memory_mb,
            "memory_usage_percent": (self.current_memory_mb / self.max_memory_mb) * 100,
            "cached_levels": len(self.pyramid),
            "max_levels": self.max_levels,
            "zoom_levels": list(self.pyramid.keys())
        }
    
    def set_memory_limit(self, max_memory_mb: float):
        """设置内存限制"""
        old_limit = self.max_memory_mb
        self.max_memory_mb = max_memory_mb
        
        # 如果新限制较低，清理部分缓存
        if max_memory_mb < old_limit and self.current_memory_mb > max_memory_mb:
            self._cleanup_memory(0)
        
        print(f"更新金字塔内存限制: {old_limit:.1f}MB -> {max_memory_mb:.1f}MB")


class EdgeDetectionCanvas:
    """专业级边缘检测图像显示画布"""
    
    def __init__(self, parent, width: int = 600, height: int = 400, memory_limit_mb: float = 256.0):
        self.parent = parent
        self.width = width
        self.height = height
        
        # 画布状态
        self.state = CanvasState()
        
        # 图像数据
        self.original_image = None
        self.edge_image = None
        self.comparison_image = None
        
        # 图像金字塔缓存（带内存限制）
        pyramid_memory_per_type = memory_limit_mb / 3  # 分配给三种图像类型
        self.original_pyramid = ImagePyramid(max_memory_mb=pyramid_memory_per_type)
        self.edge_pyramid = ImagePyramid(max_memory_mb=pyramid_memory_per_type)
        self.comparison_pyramid = ImagePyramid(max_memory_mb=pyramid_memory_per_type)
        
        # 设置内存清理回调
        self.original_pyramid.on_memory_cleanup = self._on_memory_cleanup
        self.edge_pyramid.on_memory_cleanup = self._on_memory_cleanup
        self.comparison_pyramid.on_memory_cleanup = self._on_memory_cleanup
        
        # UI组件
        self.canvas_frame = None
        self.canvas = None
        self.h_scrollbar = None
        self.v_scrollbar = None
        
        # 缩放级别
        self.zoom_levels = [0.1, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0]
        self.current_zoom_index = 4  # 1.0倍
        
        # 拖拽状态
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.last_pan_offset = (0, 0)
        
        # 防抖机制
        self.debounce_timer = None
        self.debounce_delay = 100  # 防抖延迟（毫秒）
        self.pending_update = False
        self.last_update_time = 0
        self.update_throttle = 50  # 更新节流（毫秒）
        
        # 缓存状态跟踪
        self.last_zoom_factor = None
        self.last_display_mode = None
        self.last_pan_offset = None
        self.cached_tk_image = None
        
        # 性能监控
        self.performance_metrics = {
            'zoom_operations': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_update_time': 0.0,
            'avg_update_time': 0.0,
            'peak_memory_usage': 0.0,
            'memory_cleanups': 0
        }
        self.on_performance_update = None
        
        # 回调函数
        self.on_zoom_changed = None
        self.on_mode_changed = None
        
        # 创建UI
        self.create_widgets()
        
        # 绑定事件
        self.bind_events()
    
    def create_widgets(self):
        """创建UI组件"""
        # 主框架
        self.canvas_frame = ttk.Frame(self.parent)
        
        # 创建画布和滚动条
        self.canvas = tk.Canvas(
            self.canvas_frame,
            width=self.width,
            height=self.height,
            bg='white',
            highlightthickness=0
        )
        
        # 水平滚动条
        self.h_scrollbar = ttk.Scrollbar(
            self.canvas_frame,
            orient=tk.HORIZONTAL,
            command=self.canvas.xview
        )
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set)
        
        # 垂直滚动条
        self.v_scrollbar = ttk.Scrollbar(
            self.canvas_frame,
            orient=tk.VERTICAL,
            command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)
        
        # 布局
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        self.v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 配置网格权重
        self.canvas_frame.columnconfigure(0, weight=1)
        self.canvas_frame.rowconfigure(0, weight=1)
    
    def bind_events(self):
        """绑定事件"""
        # 鼠标滚轮缩放
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)  # Linux
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)  # Linux
        
        # 鼠标拖拽
        self.canvas.bind("<Button-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        
        # 画布大小变化
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        
        # 键盘快捷键
        self.canvas.bind("<Key>", self.on_key_press)
        self.canvas.focus_set()
    
    def get_frame(self) -> ttk.Frame:
        """获取主框架"""
        return self.canvas_frame
    
    def set_images(self, original: Optional[np.ndarray] = None, 
                   edges: Optional[np.ndarray] = None):
        """设置要显示的图像"""
        if original is not None:
            self.original_image = original
            self.original_pyramid.set_base_image(original)
            self.state.image_size = (original.shape[1], original.shape[0])
        
        if edges is not None:
            self.edge_image = edges
            self.edge_pyramid.set_base_image(edges)
            
            # 创建对比图像
            if self.original_image is not None:
                self.comparison_image = self._create_comparison_image()
                self.comparison_pyramid.set_base_image(self.comparison_image)
        
        # 重置视图状态
        self.reset_view()
        
        # 清除缓存
        self._clear_cache()
        
        # 更新显示
        self.update_display()
    
    def _create_comparison_image(self) -> np.ndarray:
        """创建对比图像（左右分屏）"""
        if self.original_image is None or self.edge_image is None:
            return self.original_image if self.original_image is not None else self.edge_image
        
        original = self.original_image
        edges = self.edge_image
        
        # 确保尺寸一致
        if original.shape[:2] != edges.shape[:2]:
            edges = np.resize(edges, original.shape[:2])
        
        # 确保通道数一致
        if len(original.shape) == 3 and len(edges.shape) == 2:
            edges = np.stack([edges] * 3, axis=2)
        elif len(original.shape) == 2 and len(edges.shape) == 3:
            original = np.stack([original] * 3, axis=2)
        
        # 左右拼接
        comparison = np.hstack([original, edges])
        
        return comparison
    
    def set_display_mode(self, mode: str):
        """设置显示模式"""
        if mode in ["original", "edges", "comparison"]:
            self.state.display_mode = mode
            self.update_display()
            
            if self.on_mode_changed:
                self.on_mode_changed(mode)
    
    def get_current_image(self) -> Optional[np.ndarray]:
        """获取当前显示的图像"""
        if self.state.display_mode == "original":
            return self.original_image
        elif self.state.display_mode == "edges":
            return self.edge_image
        elif self.state.display_mode == "comparison":
            return self.comparison_image
        return None
    
    def get_current_pyramid(self) -> ImagePyramid:
        """获取当前显示模式对应的图像金字塔"""
        if self.state.display_mode == "original":
            return self.original_pyramid
        elif self.state.display_mode == "edges":
            return self.edge_pyramid
        elif self.state.display_mode == "comparison":
            return self.comparison_pyramid
        return self.original_pyramid
    
    def update_display(self):
        """更新显示（带防抖）"""
        current_time = time.time() * 1000  # 转换为毫秒
        
        # 如果距离上次更新时间太短，使用防抖
        if current_time - self.last_update_time < self.update_throttle:
            self.update_display_debounced()
            return
        
        # 直接更新
        self._perform_update()
        self.last_update_time = current_time
    
    def update_display_debounced(self):
        """防抖更新显示"""
        # 取消之前的定时器
        if self.debounce_timer:
            self.parent.after_cancel(self.debounce_timer)
        
        # 标记有待更新
        self.pending_update = True
        
        # 设置新的定时器
        self.debounce_timer = self.parent.after(self.debounce_delay, self._debounce_callback)
    
    def _debounce_callback(self):
        """防抖回调"""
        if self.pending_update:
            self._perform_update()
            self.pending_update = False
            self.last_update_time = time.time() * 1000
        self.debounce_timer = None
    
    def _perform_update(self):
        """执行实际的显示更新（带智能缓存和性能监控）"""
        update_start_time = time.time()
        
        current_pyramid = self.get_current_pyramid()
        
        if current_pyramid.base_image is None:
            self.canvas.delete("all")
            self._clear_cache()
            return
        
        # 获取当前状态
        zoom_factor = self.zoom_levels[self.current_zoom_index]
        current_display_mode = self.state.display_mode
        current_pan_offset = self.state.pan_offset
        
        # 检查是否需要重新创建图像
        need_new_image = (
            self.last_zoom_factor != zoom_factor or
            self.last_display_mode != current_display_mode or
            self.cached_tk_image is None
        )
        
        # 性能监控：缓存命中率统计
        if need_new_image:
            self.performance_metrics['cache_misses'] += 1
        else:
            self.performance_metrics['cache_hits'] += 1
        
        # 检查是否只需要重新定位（不需要重新创建图像）
        only_pan_changed = (
            not need_new_image and 
            self.last_pan_offset != current_pan_offset
        )
        
        # 如果需要新图像，重新创建
        if need_new_image:
            # 统计缩放操作
            if self.last_zoom_factor != zoom_factor:
                self.performance_metrics['zoom_operations'] += 1
            
            pil_image = current_pyramid.get_image_at_zoom(zoom_factor)
            
            if pil_image is None:
                return
            
            # 转换为Tkinter格式
            try:
                tk_image = ImageTk.PhotoImage(pil_image)
                self.cached_tk_image = tk_image
            except Exception as e:
                print(f"图像转换失败: {e}")
                return
            
            # 更新缓存状态
            self.last_zoom_factor = zoom_factor
            self.last_display_mode = current_display_mode
        
        # 清除画布并重新绘制
        self.canvas.delete("all")
        
        # 显示图像
        self.canvas.create_image(
            current_pan_offset[0],
            current_pan_offset[1],
            anchor=tk.NW,
            image=self.cached_tk_image
        )
        
        # 保持引用，防止被垃圾回收
        self.canvas.image = self.cached_tk_image
        
        # 更新滚动区域（只在缩放或模式改变时更新）
        if need_new_image:
            self.update_scroll_region()
        
        # 更新状态
        self.state.zoom_factor = zoom_factor
        self.last_pan_offset = current_pan_offset
        
        # 性能监控：更新时间统计
        update_time = time.time() - update_start_time
        self.performance_metrics['total_update_time'] += update_time
        total_operations = self.performance_metrics['cache_hits'] + self.performance_metrics['cache_misses']
        if total_operations > 0:
            self.performance_metrics['avg_update_time'] = self.performance_metrics['total_update_time'] / total_operations
        
        # 性能监控：内存使用情况
        memory_info = self.get_canvas_memory_info()
        current_memory = memory_info.get('total_memory_mb', 0)
        if current_memory > self.performance_metrics['peak_memory_usage']:
            self.performance_metrics['peak_memory_usage'] = current_memory
        
        # 触发性能更新回调
        if self.on_performance_update:
            self.on_performance_update(self.performance_metrics)
    
    def _clear_cache(self):
        """清除显示缓存"""
        self.cached_tk_image = None
        self.last_zoom_factor = None
        self.last_display_mode = None
        self.last_pan_offset = None
    
    def _on_memory_cleanup(self, zoom_level: float, memory_freed: float):
        """内存清理回调"""
        self.performance_metrics['memory_cleanups'] += 1
        if self.on_performance_update:
            self.on_performance_update(self.performance_metrics)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        metrics = self.performance_metrics.copy()
        
        # 计算缓存命中率
        total_operations = metrics['cache_hits'] + metrics['cache_misses']
        if total_operations > 0:
            metrics['cache_hit_rate'] = (metrics['cache_hits'] / total_operations) * 100
        else:
            metrics['cache_hit_rate'] = 0.0
        
        # 添加内存信息
        memory_info = self.get_canvas_memory_info()
        metrics['current_memory_mb'] = memory_info.get('total_memory_mb', 0)
        
        # 添加金字塔信息
        metrics['pyramid_levels'] = {
            'original': len(self.original_pyramid.pyramid),
            'edge': len(self.edge_pyramid.pyramid),
            'comparison': len(self.comparison_pyramid.pyramid)
        }
        
        return metrics
    
    def reset_performance_metrics(self):
        """重置性能指标"""
        self.performance_metrics = {
            'zoom_operations': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_update_time': 0.0,
            'avg_update_time': 0.0,
            'peak_memory_usage': 0.0,
            'memory_cleanups': 0
        }
    
    def update_scroll_region(self):
        """更新滚动区域"""
        if self.state.image_size == (0, 0):
            return
        
        zoom_factor = self.zoom_levels[self.current_zoom_index]
        scaled_width = int(self.state.image_size[0] * zoom_factor)
        scaled_height = int(self.state.image_size[1] * zoom_factor)
        
        # 设置滚动区域
        self.canvas.configure(scrollregion=(
            0, 0, scaled_width, scaled_height
        ))
    
    def zoom_in(self):
        """放大"""
        if self.current_zoom_index < len(self.zoom_levels) - 1:
            self.current_zoom_index += 1
            self.update_display()
            
            if self.on_zoom_changed:
                zoom_factor = self.zoom_levels[self.current_zoom_index]
                self.on_zoom_changed(zoom_factor)
    
    def zoom_out(self):
        """缩小"""
        if self.current_zoom_index > 0:
            self.current_zoom_index -= 1
            self.update_display()
            
            if self.on_zoom_changed:
                zoom_factor = self.zoom_levels[self.current_zoom_index]
                self.on_zoom_changed(zoom_factor)
    
    def zoom_to_fit(self):
        """缩放到适合窗口"""
        if self.state.image_size == (0, 0):
            return
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return
        
        # 计算适合的缩放比例
        scale_x = canvas_width / self.state.image_size[0]
        scale_y = canvas_height / self.state.image_size[1]
        scale = min(scale_x, scale_y)
        
        # 找到最接近的缩放级别
        best_index = 0
        best_diff = abs(self.zoom_levels[0] - scale)
        
        for i, zoom_level in enumerate(self.zoom_levels):
            diff = abs(zoom_level - scale)
            if diff < best_diff:
                best_diff = diff
                best_index = i
        
        self.current_zoom_index = best_index
        self.center_image()
        self.update_display()
        
        if self.on_zoom_changed:
            zoom_factor = self.zoom_levels[self.current_zoom_index]
            self.on_zoom_changed(zoom_factor)
    
    def zoom_to_actual_size(self):
        """缩放到实际大小(100%)"""
        actual_size_index = self.zoom_levels.index(1.0)
        self.current_zoom_index = actual_size_index
        self.center_image()
        self.update_display()
        
        if self.on_zoom_changed:
            self.on_zoom_changed(1.0)
    
    def center_image(self):
        """居中显示图像"""
        if self.state.image_size == (0, 0):
            return
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        zoom_factor = self.zoom_levels[self.current_zoom_index]
        scaled_width = int(self.state.image_size[0] * zoom_factor)
        scaled_height = int(self.state.image_size[1] * zoom_factor)
        
        # 计算居中偏移
        center_x = max(0, (canvas_width - scaled_width) // 2)
        center_y = max(0, (canvas_height - scaled_height) // 2)
        
        self.state.pan_offset = (center_x, center_y)
    
    def reset_view(self):
        """重置视图"""
        self.state.reset()
        self.current_zoom_index = 4  # 1.0倍
        self.center_image()
    
    def on_mouse_wheel(self, event):
        """鼠标滚轮事件"""
        # 获取鼠标位置
        mouse_x = self.canvas.canvasx(event.x)
        mouse_y = self.canvas.canvasy(event.y)
        
        # 确定滚动方向
        if event.delta > 0 or event.num == 4:
            # 向上滚动，放大
            if self.current_zoom_index < len(self.zoom_levels) - 1:
                old_zoom = self.zoom_levels[self.current_zoom_index]
                self.current_zoom_index += 1
                new_zoom = self.zoom_levels[self.current_zoom_index]
                
                # 调整偏移，使鼠标位置保持不变
                self._adjust_zoom_offset(mouse_x, mouse_y, old_zoom, new_zoom)
                self.update_display()
        else:
            # 向下滚动，缩小
            if self.current_zoom_index > 0:
                old_zoom = self.zoom_levels[self.current_zoom_index]
                self.current_zoom_index -= 1
                new_zoom = self.zoom_levels[self.current_zoom_index]
                
                # 调整偏移
                self._adjust_zoom_offset(mouse_x, mouse_y, old_zoom, new_zoom)
                self.update_display()
        
        if self.on_zoom_changed:
            zoom_factor = self.zoom_levels[self.current_zoom_index]
            self.on_zoom_changed(zoom_factor)
    
    def _adjust_zoom_offset(self, mouse_x: float, mouse_y: float, 
                           old_zoom: float, new_zoom: float):
        """调整缩放偏移，保持鼠标位置不变"""
        zoom_ratio = new_zoom / old_zoom
        
        # 计算新的偏移
        new_offset_x = mouse_x - (mouse_x - self.state.pan_offset[0]) * zoom_ratio
        new_offset_y = mouse_y - (mouse_y - self.state.pan_offset[1]) * zoom_ratio
        
        self.state.pan_offset = (int(new_offset_x), int(new_offset_y))
    
    def on_mouse_press(self, event):
        """鼠标按下事件"""
        self.is_dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.last_pan_offset = self.state.pan_offset
        
        # 设置鼠标光标
        self.canvas.configure(cursor="fleur")
    
    def on_mouse_drag(self, event):
        """鼠标拖拽事件"""
        if self.is_dragging:
            # 计算拖拽距离
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            
            # 更新偏移
            new_offset_x = self.last_pan_offset[0] + dx
            new_offset_y = self.last_pan_offset[1] + dy
            
            self.state.pan_offset = (new_offset_x, new_offset_y)
            
            # 更新显示
            self.update_display()
    
    def on_mouse_release(self, event):
        """鼠标释放事件"""
        self.is_dragging = False
        
        # 恢复鼠标光标
        self.canvas.configure(cursor="")
    
    def on_canvas_resize(self, event):
        """画布大小变化事件"""
        self.state.canvas_size = (event.width, event.height)
        
        # 如果是首次显示或自适应模式，重新调整
        if hasattr(self, '_auto_fit_on_resize') and self._auto_fit_on_resize:
            self.zoom_to_fit()
    
    def on_key_press(self, event):
        """键盘按键事件"""
        if event.keysym == "plus" or event.keysym == "equal":
            self.zoom_in()
        elif event.keysym == "minus":
            self.zoom_out()
        elif event.keysym == "0":
            self.zoom_to_actual_size()
        elif event.keysym == "F" or event.keysym == "f":
            self.zoom_to_fit()
        elif event.keysym == "R" or event.keysym == "r":
            self.reset_view()
            self.update_display()
    
    def get_zoom_factor(self) -> float:
        """获取当前缩放因子"""
        return self.zoom_levels[self.current_zoom_index]
    
    def set_zoom_factor(self, zoom_factor: float):
        """设置缩放因子"""
        # 找到最接近的缩放级别
        best_index = 0
        best_diff = abs(self.zoom_levels[0] - zoom_factor)
        
        for i, level in enumerate(self.zoom_levels):
            diff = abs(level - zoom_factor)
            if diff < best_diff:
                best_diff = diff
                best_index = i
        
        self.current_zoom_index = best_index
        self.update_display()
    
    def export_current_view(self) -> Optional[Image.Image]:
        """导出当前视图"""
        current_pyramid = self.get_current_pyramid()
        if current_pyramid.base_image is None:
            return None
        
        zoom_factor = self.zoom_levels[self.current_zoom_index]
        return current_pyramid.get_image_at_zoom(zoom_factor)
    
    def clear(self):
        """清除所有内容"""
        self.canvas.delete("all")
        self.original_pyramid.clear()
        self.edge_pyramid.clear()
        self.comparison_pyramid.clear()
        self.original_image = None
        self.edge_image = None
        self.comparison_image = None
        self.state.reset()
        self._clear_cache()
    
    def get_canvas_memory_info(self) -> Dict[str, Any]:
        """获取画布内存使用信息"""
        return {
            "original_pyramid": self.original_pyramid.get_memory_info(),
            "edge_pyramid": self.edge_pyramid.get_memory_info(),
            "comparison_pyramid": self.comparison_pyramid.get_memory_info(),
            "total_memory_mb": (
                self.original_pyramid.current_memory_mb +
                self.edge_pyramid.current_memory_mb +
                self.comparison_pyramid.current_memory_mb
            )
        }
    
    def set_memory_limit(self, memory_limit_mb: float):
        """设置画布内存限制"""
        pyramid_memory_per_type = memory_limit_mb / 3
        self.original_pyramid.set_memory_limit(pyramid_memory_per_type)
        self.edge_pyramid.set_memory_limit(pyramid_memory_per_type)
        self.comparison_pyramid.set_memory_limit(pyramid_memory_per_type)


if __name__ == "__main__":
    # 测试代码
    root = tk.Tk()
    root.title("图像画布测试")
    root.geometry("800x600")
    
    # 创建测试图像
    test_image = np.random.randint(0, 255, (300, 400, 3), dtype=np.uint8)
    test_edges = np.random.randint(0, 255, (300, 400), dtype=np.uint8)
    
    # 创建画布
    canvas = EdgeDetectionCanvas(root, 600, 400)
    canvas.get_frame().pack(fill=tk.BOTH, expand=True)
    
    # 设置图像
    canvas.set_images(test_image, test_edges)
    
    # 创建控制按钮
    control_frame = ttk.Frame(root)
    control_frame.pack(fill=tk.X, padx=10, pady=5)
    
    ttk.Button(control_frame, text="原图", 
               command=lambda: canvas.set_display_mode("original")).pack(side=tk.LEFT, padx=5)
    ttk.Button(control_frame, text="边缘", 
               command=lambda: canvas.set_display_mode("edges")).pack(side=tk.LEFT, padx=5)
    ttk.Button(control_frame, text="对比", 
               command=lambda: canvas.set_display_mode("comparison")).pack(side=tk.LEFT, padx=5)
    ttk.Button(control_frame, text="适合窗口", 
               command=canvas.zoom_to_fit).pack(side=tk.LEFT, padx=5)
    ttk.Button(control_frame, text="实际大小", 
               command=canvas.zoom_to_actual_size).pack(side=tk.LEFT, padx=5)
    
    root.mainloop()