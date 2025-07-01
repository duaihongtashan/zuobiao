"""
坐标记录器模块 - 基于Context7 pynput最佳实践
用于记录屏幕坐标，支持单次坐标记录
"""

import threading
from typing import Callable, Optional
from pynput import mouse


class CoordinateRecorder:
    """坐标记录器类"""
    
    def __init__(self):
        self.recording = False
        self.coordinates = []
        self.mouse_listener = None
        
    def start_single_recording(self, 
                              target_description: str = "坐标",
                              on_single_recorded: Callable = None,
                              on_status_changed: Callable = None):
        """开始单次坐标记录"""
        if self.recording:
            print("⚠️ 坐标记录已在进行中")
            return False
        
        self.on_single_recorded = on_single_recorded
        self.on_status_changed = on_status_changed
        self.target_description = target_description
        
        self.recording = True
        self.coordinates.clear()
        
        try:
            print(f"🎯 启动{target_description}坐标记录...")
            
            self.mouse_listener = mouse.Listener(
                on_click=self._on_mouse_click_single,
                suppress=False
            )
            
            self.mouse_listener.start()
            self._notify_status(f"请点击{target_description}位置")
            
            print(f"✅ 单次坐标记录器已启动")
            return True
            
        except Exception as e:
            print(f"❌ 启动单次坐标记录失败: {e}")
            self.recording = False
            return False
    
    def stop_recording(self):
        """停止坐标记录"""
        if not self.recording:
            return
        
        try:
            if self.mouse_listener:
                self.mouse_listener.stop()
                self.mouse_listener = None
            
            self.recording = False
            self._notify_status("")
            print("🛑 坐标记录已停止")
            
        except Exception as e:
            print(f"❌ 停止坐标记录失败: {e}")
    
    def _on_mouse_click_single(self, x, y, button, pressed):
        """单次鼠标点击事件处理"""
        if not (self.recording and pressed and button == mouse.Button.left):
            return
        
        try:
            print(f"🖱️ 记录{self.target_description}坐标: ({x}, {y})")
            
            self.coordinates.append((x, y))
            
            if hasattr(self, 'on_single_recorded') and self.on_single_recorded:
                threading.Thread(
                    target=lambda: self.on_single_recorded(x, y), 
                    daemon=True
                ).start()
            
            print(f"✅ {self.target_description}坐标记录完成: ({x}, {y})")
            self._notify_status(f"{self.target_description}坐标记录完成")
            
            self.stop_recording()
                
        except Exception as e:
            print(f"❌ 处理单次鼠标点击事件失败: {e}")
    
    def _notify_status(self, message: str):
        """通知状态变化"""
        if self.on_status_changed:
            threading.Thread(
                target=lambda: self.on_status_changed(message), 
                daemon=True
            ).start()
    
    def is_recording(self) -> bool:
        """检查是否正在记录"""
        return self.recording


def create_coordinate_recorder():
    """创建坐标记录器实例"""
    return CoordinateRecorder() 