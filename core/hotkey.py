"""快捷键管理模块 - 基于Context7 pynput最佳实践"""

import threading
from typing import Dict, Callable, Optional
from pynput import keyboard
from pynput.keyboard import GlobalHotKeys


class ModernHotkeyManager:
    """
    现代化快捷键管理器
    基于Context7 pynput文档的GlobalHotKeys实现
    """
    
    def __init__(self):
        self.hotkey_callbacks: Dict[str, Callable] = {}  # 快捷键回调映射
        self.global_hotkeys: Optional[GlobalHotKeys] = None
        self.running = False
        
    def convert_hotkey_format(self, hotkey_str: str) -> str:
        """
        将自定义格式转换为pynput的GlobalHotKeys格式
        
        Args:
            hotkey_str: 自定义格式，如 "ctrl+shift+s"
            
        Returns:
            pynput格式，如 "<ctrl>+<shift>+s"
        """
        # 移除空格并转为小写
        hotkey_str = hotkey_str.strip().lower()
        
        # 分割快捷键
        parts = [part.strip() for part in hotkey_str.split('+')]
        
        # 特殊键映射 - 基于Context7 pynput文档
        special_keys = {
            'space': '<space>',
            'enter': '<enter>',
            'tab': '<tab>',
            'esc': '<esc>',
            'escape': '<esc>',
            'backspace': '<backspace>',
            'delete': '<delete>',
            'home': '<home>',
            'end': '<end>',
            'page_up': '<page_up>',
            'page_down': '<page_down>',
            'up': '<up>',
            'down': '<down>',
            'left': '<left>',
            'right': '<right>',
        }
        
        # 功能键映射
        for i in range(1, 13):
            special_keys[f'f{i}'] = f'<f{i}>'
        
        # 转换格式
        converted_parts = []
        for part in parts:
            if part in ['ctrl', 'shift', 'alt', 'win', 'cmd']:
                # 修饰键加上尖括号
                if part == 'win':
                    converted_parts.append('<cmd>')  # Windows键在pynput中是cmd
                else:
                    converted_parts.append(f'<{part}>')
            elif part in special_keys:
                # 特殊键使用映射
                converted_parts.append(special_keys[part])
            else:
                # 普通字符键直接使用
                converted_parts.append(part)
        
        return '+'.join(converted_parts)
    
    def register_hotkey(self, hotkey_str: str, callback: Callable, description: str = ""):
        """
        注册快捷键
        
        Args:
            hotkey_str: 快捷键字符串，如 "ctrl+shift+s"
            callback: 回调函数
            description: 描述信息
        """
        try:
            # 转换为pynput格式
            pynput_format = self.convert_hotkey_format(hotkey_str)
            
            # 创建线程安全的回调包装器
            def safe_callback():
                try:
                    print(f"🔥 快捷键触发: {hotkey_str} ({description})")
                    # 在新线程中执行回调，避免阻塞快捷键监听
                    callback_thread = threading.Thread(target=callback, daemon=True)
                    callback_thread.start()
                except Exception as e:
                    print(f"❌ 快捷键回调执行失败 {hotkey_str}: {e}")
            
            # 保存回调
            self.hotkey_callbacks[pynput_format] = safe_callback
            
            print(f"✅ 注册快捷键: {hotkey_str} -> {pynput_format} ({description})")
            
            # 如果监听器正在运行，重新启动以应用新的快捷键
            if self.running:
                self._restart_listener()
            
        except Exception as e:
            print(f"❌ 注册快捷键失败 {hotkey_str}: {e}")
    
    def unregister_hotkey(self, hotkey_str: str):
        """取消注册快捷键"""
        try:
            pynput_format = self.convert_hotkey_format(hotkey_str)
            if pynput_format in self.hotkey_callbacks:
                del self.hotkey_callbacks[pynput_format]
                print(f"✅ 取消注册快捷键: {hotkey_str}")
                
                # 重新启动监听器以应用更改
                if self.running:
                    self._restart_listener()
            else:
                print(f"⚠️ 快捷键未注册: {hotkey_str}")
        except Exception as e:
            print(f"❌ 取消注册快捷键失败 {hotkey_str}: {e}")
    
    def start_listening(self):
        """开始监听快捷键"""
        if self.running:
            print("⚠️ 快捷键监听已在运行")
            return True
        
        if not self.hotkey_callbacks:
            print("⚠️ 没有注册任何快捷键")
            return False
        
        try:
            print("🎯 启动全局快捷键监听...")
            print(f"📊 注册的快捷键: {len(self.hotkey_callbacks)} 个")
            
            for hotkey_format in self.hotkey_callbacks.keys():
                print(f"   • {hotkey_format}")
            
            # 使用Context7推荐的GlobalHotKeys
            self.global_hotkeys = GlobalHotKeys(self.hotkey_callbacks)
            self.global_hotkeys.start()
            self.running = True
            
            print("✅ 全局快捷键监听已启动")
            return True
            
        except Exception as e:
            print(f"❌ 启动快捷键监听失败: {e}")
            print(f"   错误类型: {type(e).__name__}")
            print("💡 解决方案:")
            print("   1. 以管理员身份运行程序")
            print("   2. 检查快捷键格式是否正确")
            print("   3. 确保没有冲突的快捷键")
            return False
    
    def stop_listening(self):
        """停止监听快捷键"""
        if not self.running:
            return
        
        try:
            if self.global_hotkeys:
                self.global_hotkeys.stop()
                self.global_hotkeys = None
            self.running = False
            print("✅ 快捷键监听已停止")
            
        except Exception as e:
            print(f"❌ 停止快捷键监听失败: {e}")
    
    def _restart_listener(self):
        """重新启动监听器（内部使用）"""
        if self.running:
            print("🔄 重新启动快捷键监听器...")
            self.stop_listening()
            self.start_listening()
    
    def is_listening(self) -> bool:
        """检查是否正在监听"""
        return self.running and self.global_hotkeys is not None
    
    def get_registered_hotkeys(self) -> Dict[str, str]:
        """获取已注册的快捷键列表"""
        return {k: "已注册" for k in self.hotkey_callbacks.keys()}
    
    def clear_all_hotkeys(self):
        """清除所有快捷键"""
        was_running = self.running
        if was_running:
            self.stop_listening()
        
        self.hotkey_callbacks.clear()
        print("✅ 已清除所有快捷键")
        
        if was_running:
            print("ℹ️ 监听器已停止，请重新启动")
    
    def validate_hotkey_with_details(self, hotkey_str: str) -> tuple:
        """
        验证快捷键并返回详细信息
        
        Args:
            hotkey_str: 快捷键字符串
            
        Returns:
            (是否有效, 错误信息)
        """
        if not hotkey_str or not hotkey_str.strip():
            return False, "快捷键不能为空"
        
        hotkey_str = hotkey_str.strip().lower()
        
        try:
            # 检查基本格式
            if '+' not in hotkey_str:
                return False, "快捷键必须包含修饰键，格式如: ctrl+shift+s"
            
            parts = [part.strip() for part in hotkey_str.split('+')]
            
            # 分离修饰键和主键
            modifiers = []
            main_keys = []
            
            valid_modifiers = {'ctrl', 'shift', 'alt', 'win', 'cmd'}
            
            for part in parts:
                if part in valid_modifiers:
                    modifiers.append(part)
                else:
                    main_keys.append(part)
            
            # 检查修饰键
            if not modifiers:
                return False, "必须包含至少一个修饰键 (ctrl, shift, alt, win)"
            
            # 检查主键
            if not main_keys:
                return False, "必须包含一个主键"
            
            if len(main_keys) > 1:
                return False, f"只能有一个主键，发现: {main_keys}"
            
            # 检查修饰键重复
            if len(modifiers) != len(set(modifiers)):
                return False, "修饰键不能重复"
            
            # 尝试转换格式以验证
            try:
                pynput_format = self.convert_hotkey_format(hotkey_str)
                return True, f"格式正确，将转换为: {pynput_format}"
            except Exception as e:
                return False, f"格式转换失败: {e}"
            
        except Exception as e:
            return False, f"解析错误: {str(e)}"
    
    def get_hotkey_format_help(self) -> str:
        """获取快捷键格式帮助信息"""
        return """
🎯 快捷键格式说明
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 基本格式: 修饰键+主键
   示例: ctrl+shift+s

🔧 修饰键 (至少选择一个):
   • ctrl  - Ctrl键
   • shift - Shift键  
   • alt   - Alt键
   • win   - Windows键

⌨️ 主键 (选择一个):
   • 字母: a-z
   • 数字: 0-9
   • 功能键: f1-f12
   • 特殊键: space, enter, tab, esc

✅ 正确示例:
   • ctrl+shift+s (截图)
   • alt+f4 (关闭窗口)
   • ctrl+c (复制)
   • win+r (运行)

❌ 错误示例:
   • s (缺少修饰键)
   • ctrl+ (缺少主键)
   • ctrl+shift+ctrl (重复修饰键)

💡 基于Context7 pynput最佳实践实现
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    def get_listener_status(self) -> dict:
        """获取监听器状态信息"""
        return {
            'running': self.running,
            'listener_alive': self.global_hotkeys is not None,
            'registered_hotkeys': len(self.hotkey_callbacks),
            'hotkey_list': list(self.hotkey_callbacks.keys())
        }


# 为了向后兼容，创建一个适配器
class HotkeyManager(ModernHotkeyManager):
    """向后兼容的快捷键管理器"""
    
    def __init__(self):
        super().__init__()
        print("🆕 使用现代化快捷键管理器 (基于Context7最佳实践)")


# 全局快捷键管理器实例
hotkey_manager = HotkeyManager()


# 便捷函数
def register_screenshot_hotkeys(single_callback, continuous_start_callback, continuous_stop_callback):
    """注册截图相关的快捷键"""
    hotkey_manager.register_hotkey("ctrl+shift+s", single_callback, "单次截图")
    hotkey_manager.register_hotkey("ctrl+shift+c", continuous_start_callback, "开始连续截图")
    hotkey_manager.register_hotkey("ctrl+shift+x", continuous_stop_callback, "停止连续截图")


def register_screenshot_hotkeys_custom(single_callback, continuous_start_callback, continuous_stop_callback,
                                      single_key="ctrl+shift+s", continuous_key="ctrl+shift+c", stop_key="ctrl+shift+x"):
    """注册自定义截图相关的快捷键"""
    print(f"🎯 注册自定义快捷键:")
    print(f"   单次截图: {single_key}")
    print(f"   连续截图: {continuous_key}")
    print(f"   停止截图: {stop_key}")
    
    hotkey_manager.register_hotkey(single_key, single_callback, "单次截图")
    hotkey_manager.register_hotkey(continuous_key, continuous_start_callback, "开始连续截图")
    hotkey_manager.register_hotkey(stop_key, continuous_stop_callback, "停止连续截图")


def start_hotkey_service():
    """启动快捷键服务"""
    return hotkey_manager.start_listening()


def stop_hotkey_service():
    """停止快捷键服务"""
    hotkey_manager.stop_listening()


def validate_hotkey_string(hotkey_str: str) -> bool:
    """验证快捷键字符串格式"""
    is_valid, _ = hotkey_manager.validate_hotkey_with_details(hotkey_str)
    return is_valid