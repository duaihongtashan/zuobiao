"""文件管理工具模块"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
import re


class FileManager:
    """文件管理器"""
    
    def __init__(self, base_directory: str = "screenshots"):
        self.base_directory = Path(base_directory)
        self.counter_file = Path("screenshot_counter.txt")
        self._current_counter = 1
        self.load_counter()
    
    def set_base_directory(self, directory: str):
        """设置基础目录"""
        self.base_directory = Path(directory)
        self.ensure_directory_exists()
    
    def get_base_directory(self) -> str:
        """获取基础目录"""
        return str(self.base_directory)
    
    def ensure_directory_exists(self, directory: Optional[str] = None) -> bool:
        """确保目录存在"""
        target_dir = Path(directory) if directory else self.base_directory
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"创建目录失败: {e}")
            return False
    
    def load_counter(self):
        """从文件加载计数器"""
        try:
            if self.counter_file.exists():
                with open(self.counter_file, 'r') as f:
                    self._current_counter = int(f.read().strip())
            else:
                self._current_counter = 1
        except Exception:
            self._current_counter = 1
    
    def save_counter(self):
        """保存计数器到文件"""
        try:
            with open(self.counter_file, 'w') as f:
                f.write(str(self._current_counter))
        except Exception as e:
            print(f"保存计数器失败: {e}")
    
    def get_next_counter(self) -> int:
        """获取下一个计数器值"""
        current = self._current_counter
        self._current_counter += 1
        self.save_counter()
        return current
    
    def reset_counter(self, start_value: int = 1):
        """重置计数器"""
        self._current_counter = start_value
        self.save_counter()
    
    def generate_filename(self, 
                         prefix: str = "screenshot", 
                         extension: str = "png",
                         include_timestamp: bool = True,
                         include_counter: bool = True) -> str:
        """
        生成文件名
        
        Args:
            prefix: 文件名前缀
            extension: 文件扩展名
            include_timestamp: 是否包含时间戳
            include_counter: 是否包含计数器
            
        Returns:
            生成的文件名
        """
        parts = [prefix]
        
        if include_counter:
            counter = self.get_next_counter()
            parts.append(f"{counter:04d}")
        
        if include_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            parts.append(timestamp)
        
        filename = "_".join(parts) + f".{extension.lstrip('.')}"
        return filename
    
    def get_full_path(self, filename: str, subdirectory: Optional[str] = None) -> str:
        """获取完整文件路径"""
        if subdirectory:
            directory = self.base_directory / subdirectory
        else:
            directory = self.base_directory
        
        self.ensure_directory_exists(str(directory))
        return str(directory / filename)
    
    def get_screenshot_files(self, directory: Optional[str] = None) -> List[Tuple[str, str, float]]:
        """
        获取目录中的截图文件列表
        
        Args:
            directory: 目录路径，如果为None则使用基础目录
            
        Returns:
            文件信息列表，每个元素为 (文件名, 完整路径, 修改时间)
        """
        target_dir = Path(directory) if directory else self.base_directory
        
        if not target_dir.exists():
            return []
        
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}
        files = []
        
        try:
            for file_path in target_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                    stat = file_path.stat()
                    files.append((file_path.name, str(file_path), stat.st_mtime))
            
            # 按修改时间排序（最新的在前）
            files.sort(key=lambda x: x[2], reverse=True)
            
        except Exception as e:
            print(f"读取文件列表失败: {e}")
        
        return files
    
    def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        try:
            Path(file_path).unlink()
            return True
        except Exception as e:
            print(f"删除文件失败: {e}")
            return False
    
    def delete_old_files(self, max_files: int = 100, directory: Optional[str] = None) -> int:
        """
        删除旧文件，保留最新的指定数量
        
        Args:
            max_files: 保留的最大文件数
            directory: 目录路径
            
        Returns:
            删除的文件数量
        """
        files = self.get_screenshot_files(directory)
        
        if len(files) <= max_files:
            return 0
        
        # 计算需要删除的文件
        files_to_delete = files[max_files:]
        deleted_count = 0
        
        for _, file_path, _ in files_to_delete:
            if self.delete_file(file_path):
                deleted_count += 1
        
        return deleted_count
    
    def create_date_subdirectory(self) -> str:
        """创建按日期命名的子目录"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        subdirectory = self.base_directory / date_str
        self.ensure_directory_exists(str(subdirectory))
        return date_str
    
    def organize_files_by_date(self, source_directory: Optional[str] = None) -> int:
        """
        按日期整理文件到子目录
        
        Args:
            source_directory: 源目录，如果为None则使用基础目录
            
        Returns:
            移动的文件数量
        """
        source_dir = Path(source_directory) if source_directory else self.base_directory
        
        if not source_dir.exists():
            return 0
        
        moved_count = 0
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}
        
        try:
            for file_path in source_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                    # 获取文件的修改日期
                    mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    date_str = mod_time.strftime("%Y-%m-%d")
                    
                    # 创建日期目录
                    date_dir = source_dir / date_str
                    self.ensure_directory_exists(str(date_dir))
                    
                    # 移动文件
                    new_path = date_dir / file_path.name
                    if not new_path.exists():  # 避免覆盖
                        shutil.move(str(file_path), str(new_path))
                        moved_count += 1
        
        except Exception as e:
            print(f"整理文件失败: {e}")
        
        return moved_count
    
    def get_directory_size(self, directory: Optional[str] = None) -> int:
        """
        获取目录总大小（字节）
        
        Args:
            directory: 目录路径
            
        Returns:
            目录大小（字节）
        """
        target_dir = Path(directory) if directory else self.base_directory
        
        if not target_dir.exists():
            return 0
        
        total_size = 0
        try:
            for file_path in target_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            print(f"计算目录大小失败: {e}")
        
        return total_size
    
    def format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def find_next_available_counter(self, directory: Optional[str] = None) -> int:
        """
        查找下一个可用的计数器值（基于现有文件）
        
        Args:
            directory: 目录路径
            
        Returns:
            下一个可用的计数器值
        """
        files = self.get_screenshot_files(directory)
        existing_counters = set()
        
        # 正则表达式匹配文件名中的计数器
        counter_pattern = re.compile(r'screenshot_(\d+)_')
        
        for filename, _, _ in files:
            match = counter_pattern.search(filename)
            if match:
                counter = int(match.group(1))
                existing_counters.add(counter)
        
        # 找到最大值并返回下一个
        if existing_counters:
            return max(existing_counters) + 1
        else:
            return 1


# 全局文件管理器实例
file_manager = FileManager()