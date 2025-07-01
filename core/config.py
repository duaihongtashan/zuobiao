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