"""配置管理模块"""

import json
import os
from typing import Dict, Any, Tuple, Optional
from pathlib import Path


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config_path = Path(config_file)
        self._config = {}
        self._default_config = {
            "screenshot": {
                "default_region": [1750, 60, 1860, 160],  # 默认截图区域 [x1, y1, x2, y2]
                "custom_region": None,  # 自定义截图区域
                "save_directory": "screenshots",  # 保存目录
                "continuous_interval": 1.0,  # 连续截图间隔(秒)
                "auto_reset_counter": True,  # 是否每次启动重置计数器
            },
            "circle_detection": {
                "enabled": True,  # 是否启用圆形检测功能
                "hough_params": {
                    "dp": 1.0,  # 累加器分辨率比例
                    "min_dist": 50,  # 圆心间最小距离
                    "param1": 50,  # Canny边缘检测高阈值
                    "param2": 30,  # 累加器阈值
                    "min_radius": 10,  # 最小半径
                    "max_radius": 100,  # 最大半径
                },
                "custom_circle": {
                    "enabled": False,  # 是否启用自定义圆形截图
                    "center_x": 100,  # 自定义圆心X坐标
                    "center_y": 100,  # 自定义圆心Y坐标
                    "radius": 50,  # 自定义半径
                },
                "preprocessing": {
                    "blur_kernel_size": 5,  # 高斯模糊核大小
                    "median_blur_size": 5,  # 中值滤波核大小
                    "use_clahe": True,  # 是否使用CLAHE直方图均衡化
                    "clahe_clip_limit": 2.0,  # CLAHE剪裁限制
                    "clahe_tile_grid_size": [8, 8],  # CLAHE瓦片网格大小
                },
                "filtering": {
                    "min_confidence": 0.3,  # 最小置信度阈值
                    "max_circles": 10,  # 最大圆形数量
                    "overlap_threshold": 0.7,  # 重叠阈值
                },
                "capture": {
                    "save_individual": True,  # 保存单独的圆形图像
                    "save_combined": False,  # 保存组合图像
                    "transparent_background": True,  # 透明背景
                    "padding": 10,  # 边界填充像素
                    "anti_alias": True,  # 抗锯齿
                },
                "save_paths": {
                    "circle_images": "screenshots/circles",  # 圆形图像保存目录
                    "detection_data": "screenshots/circle_data",  # 检测数据保存目录
                }
            },
            "hotkeys": {
                "single_capture": "ctrl+shift+s",  # 单次截图快捷键
                "start_continuous": "ctrl+shift+c",  # 开始连续截图快捷键
                "stop_continuous": "ctrl+shift+x",  # 停止连续截图快捷键
            },
            "ui": {
                "window_position": [100, 100],  # 窗口位置 [x, y]
                "window_size": [400, 300],  # 窗口大小 [width, height]
                "always_on_top": False,  # 窗口置顶
                "minimize_to_tray": True,  # 最小化到托盘
            },
            "edge_detection": {
                "enabled": True,  # 是否启用边缘检测功能
                "canny_params": {
                    "threshold1": 50,        # 低阈值
                    "threshold2": 150,       # 高阈值  
                    "aperture_size": 3,      # Sobel算子大小
                    "l2_gradient": False     # 梯度计算方式
                },
                "preprocessing": {
                    "gaussian_blur": True,
                    "blur_kernel_size": 5,
                    "median_filter": False,
                    "median_kernel_size": 5,
                    "clahe_enabled": False,
                    "clahe_clip_limit": 2.0
                },
                "postprocessing": {
                    "morphology_enabled": False,    # 形态学操作
                    "morph_kernel_size": 3,
                    "edge_thinning": False,         # 边缘细化
                    "remove_noise": True            # 噪声去除
                },
                "display": {
                    "view_mode": "comparison",      # 显示模式: "original", "edges", "comparison"
                    "edge_color": [0, 255, 0],     # 边缘颜色 (BGR)
                    "overlay_opacity": 0.7,        # 叠加透明度
                    "zoom_enabled": True,          # 缩放功能
                    "pan_enabled": True            # 平移功能
                },
                "save_paths": {
                    "original_images": "screenshots/edge_detection/original",
                    "edge_results": "screenshots/edge_detection/edges", 
                    "comparison_images": "screenshots/edge_detection/comparison"
                },
                "import_export": {
                    "supported_formats": ["png", "jpg", "jpeg", "bmp", "tiff"],
                    "auto_resize": True,
                    "max_image_size": [2048, 2048],
                    "preserve_aspect_ratio": True
                }
            },
            "general": {
                "auto_create_directory": True,  # 自动创建保存目录
                "show_notifications": True,  # 显示通知
                "save_format": "PNG",  # 保存格式
                "image_quality": 95,  # 图片质量 (JPEG格式时使用)
            }
        }
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置和加载的配置
                    self._config = self._merge_configs(self._default_config, loaded_config)
            else:
                # 如果配置文件不存在，使用默认配置
                self._config = self._default_config.copy()
                self.save_config()  # 创建默认配置文件
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            self._config = self._default_config.copy()
    
    def save_config(self):
        """保存配置到文件"""
        try:
            # 确保配置目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def _merge_configs(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置，确保所有默认键都存在"""
        result = default.copy()
        
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, key_path: str, default=None):
        """
        获取配置值
        
        Args:
            key_path: 配置键路径，用.分隔，如 'screenshot.save_directory'
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """
        设置配置值
        
        Args:
            key_path: 配置键路径，用.分隔
            value: 要设置的值
        """
        keys = key_path.split('.')
        config = self._config
        
        # 导航到目标位置
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # 设置值
        config[keys[-1]] = value
    
    def get_screenshot_config(self) -> Dict[str, Any]:
        """获取截图相关配置"""
        return self._config.get('screenshot', {})
    
    def get_hotkey_config(self) -> Dict[str, str]:
        """获取快捷键配置"""
        return self._config.get('hotkeys', {})
    
    def get_ui_config(self) -> Dict[str, Any]:
        """获取UI配置"""
        return self._config.get('ui', {})
    
    def set_screenshot_region(self, x1: int, y1: int, x2: int, y2: int, is_custom: bool = True):
        """设置截图区域"""
        region = [x1, y1, x2, y2]
        if is_custom:
            self.set('screenshot.custom_region', region)
        else:
            self.set('screenshot.default_region', region)
    
    def get_screenshot_region(self) -> Tuple[int, int, int, int]:
        """获取当前截图区域"""
        # 优先使用自定义区域
        custom_region = self.get('screenshot.custom_region')
        if custom_region:
            return tuple(custom_region)
        
        # 否则使用默认区域
        default_region = self.get('screenshot.default_region', [1750, 60, 1860, 160])
        return tuple(default_region)
    
    def set_save_directory(self, directory: str):
        """设置保存目录"""
        self.set('screenshot.save_directory', directory)
    
    def get_save_directory(self) -> str:
        """获取保存目录"""
        return self.get('screenshot.save_directory', 'screenshots')
    
    def set_hotkey(self, action: str, hotkey: str):
        """设置快捷键"""
        self.set(f'hotkeys.{action}', hotkey)
    
    def get_hotkey(self, action: str) -> Optional[str]:
        """获取快捷键"""
        return self.get(f'hotkeys.{action}')
    
    def set_continuous_interval(self, interval: float):
        """设置连续截图间隔"""
        self.set('screenshot.continuous_interval', max(0.1, interval))
    
    def get_continuous_interval(self) -> float:
        """获取连续截图间隔"""
        return self.get('screenshot.continuous_interval', 1.0)
    
    # === 圆形检测配置方法 ===
    
    def is_circle_detection_enabled(self) -> bool:
        """获取圆形检测是否启用"""
        return self.get('circle_detection.enabled', True)
    
    def set_circle_detection_enabled(self, enabled: bool):
        """设置圆形检测启用状态"""
        self.set('circle_detection.enabled', enabled)
    
    def get_hough_params(self) -> Dict[str, Any]:
        """获取HoughCircles检测参数"""
        return self.get('circle_detection.hough_params', {
            "dp": 1.0,
            "min_dist": 50,
            "param1": 50,
            "param2": 30,
            "min_radius": 10,
            "max_radius": 100
        })
    
    def set_hough_params(self, params: Dict[str, Any]):
        """设置HoughCircles检测参数"""
        current_params = self.get_hough_params()
        current_params.update(params)
        self.set('circle_detection.hough_params', current_params)
    
    def get_preprocessing_params(self) -> Dict[str, Any]:
        """获取图像预处理参数"""
        return self.get('circle_detection.preprocessing', {
            "blur_kernel_size": 5,
            "median_blur_size": 5,
            "use_clahe": True,
            "clahe_clip_limit": 2.0,
            "clahe_tile_grid_size": [8, 8]
        })
    
    def set_preprocessing_params(self, params: Dict[str, Any]):
        """设置图像预处理参数"""
        current_params = self.get_preprocessing_params()
        current_params.update(params)
        self.set('circle_detection.preprocessing', current_params)
    
    def get_filtering_params(self) -> Dict[str, Any]:
        """获取圆形过滤参数"""
        return self.get('circle_detection.filtering', {
            "min_confidence": 0.3,
            "max_circles": 10,
            "overlap_threshold": 0.7
        })
    
    def set_filtering_params(self, params: Dict[str, Any]):
        """设置圆形过滤参数"""
        current_params = self.get_filtering_params()
        current_params.update(params)
        self.set('circle_detection.filtering', current_params)
    
    def get_capture_params(self) -> Dict[str, Any]:
        """获取圆形截图参数"""
        return self.get('circle_detection.capture', {
            "save_individual": True,
            "save_combined": False,
            "transparent_background": True,
            "padding": 10,
            "anti_alias": True
        })
    
    def set_capture_params(self, params: Dict[str, Any]):
        """设置圆形截图参数"""
        current_params = self.get_capture_params()
        current_params.update(params)
        self.set('circle_detection.capture', current_params)
    
    def get_circle_save_paths(self) -> Dict[str, str]:
        """获取圆形保存路径配置"""
        return self.get('circle_detection.save_paths', {
            "circle_images": "screenshots/circles",
            "detection_data": "screenshots/circle_data"
        })
    
    def set_circle_save_paths(self, paths: Dict[str, str]):
        """设置圆形保存路径配置"""
        current_paths = self.get_circle_save_paths()
        current_paths.update(paths)
        self.set('circle_detection.save_paths', current_paths)
    
    def get_circle_images_directory(self) -> str:
        """获取圆形图像保存目录"""
        paths = self.get_circle_save_paths()
        return paths.get('circle_images', 'screenshots/circles')
    
    def get_circle_data_directory(self) -> str:
        """获取圆形检测数据保存目录"""
        paths = self.get_circle_save_paths()
        return paths.get('detection_data', 'screenshots/circle_data')
    
    # === 自定义圆形配置方法 ===
    
    def is_custom_circle_enabled(self) -> bool:
        """获取自定义圆形截图是否启用"""
        return self.get('circle_detection.custom_circle.enabled', False)
    
    def set_custom_circle_enabled(self, enabled: bool):
        """设置自定义圆形截图启用状态"""
        self.set('circle_detection.custom_circle.enabled', enabled)
    
    def get_custom_circle_center(self) -> Tuple[int, int]:
        """获取自定义圆心坐标"""
        center_x = self.get('circle_detection.custom_circle.center_x', 100)
        center_y = self.get('circle_detection.custom_circle.center_y', 100)
        return (center_x, center_y)
    
    def set_custom_circle_center(self, x: int, y: int):
        """设置自定义圆心坐标"""
        self.set('circle_detection.custom_circle.center_x', x)
        self.set('circle_detection.custom_circle.center_y', y)
    
    def get_custom_circle_radius(self) -> int:
        """获取自定义圆形半径"""
        return self.get('circle_detection.custom_circle.radius', 50)
    
    def set_custom_circle_radius(self, radius: int):
        """设置自定义圆形半径"""
        self.set('circle_detection.custom_circle.radius', max(5, radius))  # 最小半径5像素
    
    def get_custom_circle_params(self) -> Dict[str, Any]:
        """获取所有自定义圆形参数"""
        return {
            "enabled": self.is_custom_circle_enabled(),
            "center_x": self.get('circle_detection.custom_circle.center_x', 100),
            "center_y": self.get('circle_detection.custom_circle.center_y', 100),
            "radius": self.get('circle_detection.custom_circle.radius', 50)
        }
    
    def set_custom_circle_params(self, params: Dict[str, Any]):
        """设置自定义圆形参数"""
        if "enabled" in params:
            self.set_custom_circle_enabled(params["enabled"])
        if "center_x" in params and "center_y" in params:
            self.set_custom_circle_center(params["center_x"], params["center_y"])
        if "radius" in params:
            self.set_custom_circle_radius(params["radius"])
    
    # === 边缘检测配置方法 ===
    
    def is_edge_detection_enabled(self) -> bool:
        """获取边缘检测是否启用"""
        return self.get('edge_detection.enabled', True)
    
    def set_edge_detection_enabled(self, enabled: bool):
        """设置边缘检测启用状态"""
        self.set('edge_detection.enabled', enabled)
    
    def get_canny_params(self) -> Dict[str, Any]:
        """获取Canny边缘检测参数"""
        return self.get('edge_detection.canny_params', {
            "threshold1": 50,
            "threshold2": 150,
            "aperture_size": 3,
            "l2_gradient": False
        })
    
    def set_canny_params(self, params: Dict[str, Any]):
        """设置Canny边缘检测参数"""
        current_params = self.get_canny_params()
        current_params.update(params)
        self.set('edge_detection.canny_params', current_params)
    
    def get_edge_preprocessing_params(self) -> Dict[str, Any]:
        """获取边缘检测预处理参数"""
        return self.get('edge_detection.preprocessing', {
            "gaussian_blur": True,
            "blur_kernel_size": 5,
            "median_filter": False,
            "median_kernel_size": 5,
            "clahe_enabled": False,
            "clahe_clip_limit": 2.0
        })
    
    def set_edge_preprocessing_params(self, params: Dict[str, Any]):
        """设置边缘检测预处理参数"""
        current_params = self.get_edge_preprocessing_params()
        current_params.update(params)
        self.set('edge_detection.preprocessing', current_params)
    
    def get_edge_postprocessing_params(self) -> Dict[str, Any]:
        """获取边缘检测后处理参数"""
        return self.get('edge_detection.postprocessing', {
            "morphology_enabled": False,
            "morph_kernel_size": 3,
            "edge_thinning": False,
            "remove_noise": True
        })
    
    def set_edge_postprocessing_params(self, params: Dict[str, Any]):
        """设置边缘检测后处理参数"""
        current_params = self.get_edge_postprocessing_params()
        current_params.update(params)
        self.set('edge_detection.postprocessing', current_params)
    
    def get_edge_display_params(self) -> Dict[str, Any]:
        """获取边缘检测显示参数"""
        return self.get('edge_detection.display', {
            "view_mode": "comparison",
            "edge_color": [0, 255, 0],
            "overlay_opacity": 0.7,
            "zoom_enabled": True,
            "pan_enabled": True
        })
    
    def set_edge_display_params(self, params: Dict[str, Any]):
        """设置边缘检测显示参数"""
        current_params = self.get_edge_display_params()
        current_params.update(params)
        self.set('edge_detection.display', current_params)
    
    def get_edge_save_paths(self) -> Dict[str, str]:
        """获取边缘检测保存路径配置"""
        return self.get('edge_detection.save_paths', {
            "original_images": "screenshots/edge_detection/original",
            "edge_results": "screenshots/edge_detection/edges",
            "comparison_images": "screenshots/edge_detection/comparison"
        })
    
    def set_edge_save_paths(self, paths: Dict[str, str]):
        """设置边缘检测保存路径配置"""
        current_paths = self.get_edge_save_paths()
        current_paths.update(paths)
        self.set('edge_detection.save_paths', current_paths)
    
    def get_edge_import_export_params(self) -> Dict[str, Any]:
        """获取边缘检测导入导出参数"""
        return self.get('edge_detection.import_export', {
            "supported_formats": ["png", "jpg", "jpeg", "bmp", "tiff"],
            "auto_resize": True,
            "max_image_size": [2048, 2048],
            "preserve_aspect_ratio": True
        })
    
    def set_edge_import_export_params(self, params: Dict[str, Any]):
        """设置边缘检测导入导出参数"""
        current_params = self.get_edge_import_export_params()
        current_params.update(params)
        self.set('edge_detection.import_export', current_params)
    
    def get_edge_original_directory(self) -> str:
        """获取边缘检测原始图像保存目录"""
        paths = self.get_edge_save_paths()
        return paths.get('original_images', 'screenshots/edge_detection/original')
    
    def get_edge_results_directory(self) -> str:
        """获取边缘检测结果保存目录"""
        paths = self.get_edge_save_paths()
        return paths.get('edge_results', 'screenshots/edge_detection/edges')
    
    def get_edge_comparison_directory(self) -> str:
        """获取边缘检测对比图像保存目录"""
        paths = self.get_edge_save_paths()
        return paths.get('comparison_images', 'screenshots/edge_detection/comparison')
    
    def get_all_edge_detection_params(self) -> Dict[str, Any]:
        """获取所有边缘检测参数"""
        return {
            "enabled": self.is_edge_detection_enabled(),
            "canny_params": self.get_canny_params(),
            "preprocessing": self.get_edge_preprocessing_params(),
            "postprocessing": self.get_edge_postprocessing_params(),
            "display": self.get_edge_display_params(),
            "save_paths": self.get_edge_save_paths(),
            "import_export": self.get_edge_import_export_params()
        }
    
    def set_all_edge_detection_params(self, params: Dict[str, Any]):
        """设置所有边缘检测参数"""
        if "enabled" in params:
            self.set_edge_detection_enabled(params["enabled"])
        if "canny_params" in params:
            self.set_canny_params(params["canny_params"])
        if "preprocessing" in params:
            self.set_edge_preprocessing_params(params["preprocessing"])
        if "postprocessing" in params:
            self.set_edge_postprocessing_params(params["postprocessing"])
        if "display" in params:
            self.set_edge_display_params(params["display"])
        if "save_paths" in params:
            self.set_edge_save_paths(params["save_paths"])
        if "import_export" in params:
            self.set_edge_import_export_params(params["import_export"])
    
    def reset_to_defaults(self):
        """重置为默认配置"""
        self._config = self._default_config.copy()
        self.save_config()
    
    def export_config(self, export_path: str) -> bool:
        """导出配置到指定文件"""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """从指定文件导入配置"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
                self._config = self._merge_configs(self._default_config, imported_config)
                self.save_config()
            return True
        except Exception as e:
            print(f"导入配置失败: {e}")
            return False


# 全局配置管理器实例
config_manager = ConfigManager()