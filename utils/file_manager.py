"""文件管理工具模块"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
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
    
    # === 边缘检测文件管理方法 ===
    
    def ensure_edge_detection_directories(self) -> bool:
        """确保边缘检测相关目录存在"""
        try:
            from core.config import config_manager
            
            # 获取边缘检测保存路径配置
            save_paths = config_manager.get_edge_save_paths()
            
            # 创建所有需要的目录
            directories = [
                save_paths.get('original_images', 'screenshots/edge_detection/original'),
                save_paths.get('edge_results', 'screenshots/edge_detection/edges'),
                save_paths.get('comparison_images', 'screenshots/edge_detection/comparison')
            ]
            
            success = True
            for directory in directories:
                if not self.ensure_directory_exists(directory):
                    success = False
                    print(f"创建边缘检测目录失败: {directory}")
            
            return success
            
        except Exception as e:
            print(f"确保边缘检测目录存在时出错: {e}")
            return False
    
    def get_edge_detection_files(self, category: str = "all") -> List[Tuple[str, str, float]]:
        """
        获取边缘检测相关文件列表
        
        Args:
            category: 文件类别 ("original", "edges", "comparison", "all")
            
        Returns:
            文件信息列表
        """
        try:
            from core.config import config_manager
            save_paths = config_manager.get_edge_save_paths()
            
            files = []
            
            if category == "all" or category == "original":
                original_dir = save_paths.get('original_images', 'screenshots/edge_detection/original')
                original_files = self.get_screenshot_files(original_dir)
                files.extend([(f"[原图] {f[0]}", f[1], f[2]) for f in original_files])
            
            if category == "all" or category == "edges":
                edges_dir = save_paths.get('edge_results', 'screenshots/edge_detection/edges')
                edge_files = self.get_screenshot_files(edges_dir)
                files.extend([(f"[边缘] {f[0]}", f[1], f[2]) for f in edge_files])
            
            if category == "all" or category == "comparison":
                comp_dir = save_paths.get('comparison_images', 'screenshots/edge_detection/comparison')
                comp_files = self.get_screenshot_files(comp_dir)
                files.extend([(f"[对比] {f[0]}", f[1], f[2]) for f in comp_files])
            
            # 按修改时间排序
            files.sort(key=lambda x: x[2], reverse=True)
            
            return files
            
        except Exception as e:
            print(f"获取边缘检测文件列表失败: {e}")
            return []
    
    def generate_edge_detection_filename(self, category: str = "edges", 
                                       base_name: str = None, 
                                       extension: str = "png") -> str:
        """
        生成边缘检测结果文件名
        
        Args:
            category: 文件类别 ("original", "edges", "comparison")
            base_name: 基础文件名，如果为None则自动生成
            extension: 文件扩展名
            
        Returns:
            完整的文件名
        """
        if base_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            counter = self.get_next_counter()
            base_name = f"edge_detection_{counter}_{timestamp}"
        
        # 添加类别前缀
        if category == "original":
            prefix = "original_"
        elif category == "edges":
            prefix = "edges_"
        elif category == "comparison":
            prefix = "comparison_"
        else:
            prefix = ""
        
        return f"{prefix}{base_name}.{extension}"
    
    def get_edge_detection_file_path(self, category: str, filename: str) -> str:
        """
        获取边缘检测文件的完整路径
        
        Args:
            category: 文件类别 ("original", "edges", "comparison")
            filename: 文件名
            
        Returns:
            完整文件路径
        """
        try:
            from core.config import config_manager
            save_paths = config_manager.get_edge_save_paths()
            
            if category == "original":
                directory = save_paths.get('original_images', 'screenshots/edge_detection/original')
            elif category == "edges":
                directory = save_paths.get('edge_results', 'screenshots/edge_detection/edges')
            elif category == "comparison":
                directory = save_paths.get('comparison_images', 'screenshots/edge_detection/comparison')
            else:
                # 默认使用边缘结果目录
                directory = save_paths.get('edge_results', 'screenshots/edge_detection/edges')
            
            self.ensure_directory_exists(directory)
            return str(Path(directory) / filename)
            
        except Exception as e:
            print(f"获取边缘检测文件路径失败: {e}")
            # 回退到默认路径
            default_dir = f"screenshots/edge_detection/{category}"
            self.ensure_directory_exists(default_dir)
            return str(Path(default_dir) / filename)
    
    def cleanup_edge_detection_files(self, days_old: int = 30) -> int:
        """
        清理旧的边缘检测文件
        
        Args:
            days_old: 保留天数，超过这个天数的文件将被删除
            
        Returns:
            删除的文件数量
        """
        import time
        
        try:
            from core.config import config_manager
            save_paths = config_manager.get_edge_save_paths()
            
            directories = [
                save_paths.get('original_images', 'screenshots/edge_detection/original'),
                save_paths.get('edge_results', 'screenshots/edge_detection/edges'),
                save_paths.get('comparison_images', 'screenshots/edge_detection/comparison')
            ]
            
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            deleted_count = 0
            
            for directory in directories:
                dir_path = Path(directory)
                if not dir_path.exists():
                    continue
                
                for file_path in dir_path.iterdir():
                    if file_path.is_file():
                        if file_path.stat().st_mtime < cutoff_time:
                            try:
                                file_path.unlink()
                                deleted_count += 1
                                print(f"已删除旧文件: {file_path}")
                            except Exception as e:
                                print(f"删除文件失败 {file_path}: {e}")
            
            return deleted_count
            
        except Exception as e:
            print(f"清理边缘检测文件失败: {e}")
            return 0
    
    def get_edge_detection_statistics(self) -> Dict[str, Any]:
        """
        获取边缘检测文件统计信息
        
        Returns:
            统计信息字典
        """
        try:
            from core.config import config_manager
            save_paths = config_manager.get_edge_save_paths()
            
            stats = {
                'original_count': 0,
                'edges_count': 0,
                'comparison_count': 0,
                'total_size': 0,
                'directories': {}
            }
            
            categories = {
                'original': save_paths.get('original_images', 'screenshots/edge_detection/original'),
                'edges': save_paths.get('edge_results', 'screenshots/edge_detection/edges'),
                'comparison': save_paths.get('comparison_images', 'screenshots/edge_detection/comparison')
            }
            
            for category, directory in categories.items():
                files = self.get_screenshot_files(directory)
                count = len(files)
                size = self.get_directory_size(directory)
                
                stats[f'{category}_count'] = count
                stats['total_size'] += size
                stats['directories'][category] = {
                    'path': directory,
                    'count': count,
                    'size': size,
                    'size_formatted': self.format_file_size(size)
                }
            
            stats['total_files'] = stats['original_count'] + stats['edges_count'] + stats['comparison_count']
            stats['total_size_formatted'] = self.format_file_size(stats['total_size'])
            
            return stats
            
        except Exception as e:
            print(f"获取边缘检测统计信息失败: {e}")
            return {}


# 全局文件管理器实例
file_manager = FileManager()