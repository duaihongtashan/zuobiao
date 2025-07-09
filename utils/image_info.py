"""图片信息显示模块"""

import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
import psutil

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class ImageInfoAnalyzer:
    """图片信息分析器"""
    
    def __init__(self):
        self.supported_formats = {
            '.png': 'PNG (Portable Network Graphics)',
            '.jpg': 'JPEG (Joint Photographic Experts Group)',
            '.jpeg': 'JPEG (Joint Photographic Experts Group)', 
            '.bmp': 'BMP (Bitmap)',
            '.tiff': 'TIFF (Tagged Image File Format)',
            '.tif': 'TIFF (Tagged Image File Format)',
            '.gif': 'GIF (Graphics Interchange Format)',
            '.webp': 'WebP',
            '.ico': 'ICO (Icon)',
            '.psd': 'PSD (Photoshop Document)'
        }
    
    def analyze_image_file(self, file_path: str) -> Dict[str, Any]:
        """分析图片文件的完整信息"""
        info = {
            'file_info': self._get_file_info(file_path),
            'image_info': self._get_image_info(file_path),
            'memory_info': self._calculate_memory_requirements(file_path),
            'compatibility_info': self._check_compatibility(file_path),
            'metadata': self._get_metadata(file_path),
            'recommendations': []
        }
        
        # 生成建议
        info['recommendations'] = self._generate_recommendations(info)
        
        return info
    
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """获取文件基本信息"""
        try:
            stat = os.stat(file_path)
            path_obj = Path(file_path)
            
            return {
                'filename': path_obj.name,
                'extension': path_obj.suffix.lower(),
                'format_name': self.supported_formats.get(path_obj.suffix.lower(), '未知格式'),
                'file_size_bytes': stat.st_size,
                'file_size_kb': stat.st_size / 1024,
                'file_size_mb': stat.st_size / (1024 * 1024),
                'created_time': time.ctime(stat.st_ctime),
                'modified_time': time.ctime(stat.st_mtime),
                'absolute_path': str(path_obj.absolute()),
                'directory': str(path_obj.parent),
                'is_readable': os.access(file_path, os.R_OK),
                'is_writable': os.access(file_path, os.W_OK)
            }
        except Exception as e:
            return {'error': f'文件信息获取失败: {e}'}
    
    def _get_image_info(self, file_path: str) -> Dict[str, Any]:
        """获取图片尺寸和基本信息"""
        info = {}
        
        # 尝试使用OpenCV
        if CV2_AVAILABLE:
            try:
                image = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
                if image is not None:
                    height, width = image.shape[:2]
                    channels = 1 if len(image.shape) == 2 else image.shape[2]
                    
                    info.update({
                        'width': width,
                        'height': height,
                        'channels': channels,
                        'total_pixels': width * height,
                        'aspect_ratio': width / height,
                        'data_type': str(image.dtype),
                        'opencv_loadable': True
                    })
                    
                    # 释放内存
                    del image
                else:
                    info['opencv_loadable'] = False
            except Exception as e:
                info['opencv_error'] = str(e)
                info['opencv_loadable'] = False
        
        # 尝试使用PIL
        if PIL_AVAILABLE:
            try:
                with PILImage.open(file_path) as img:
                    info.update({
                        'width': img.width,
                        'height': img.height,
                        'mode': img.mode,
                        'format': img.format,
                        'total_pixels': img.width * img.height,
                        'aspect_ratio': img.width / img.height,
                        'pil_loadable': True
                    })
                    
                    # 获取颜色通道信息
                    mode_info = {
                        'L': '灰度 (8位)',
                        'P': '调色板 (8位)',
                        'RGB': 'RGB (24位)',
                        'RGBA': 'RGBA (32位)',
                        'CMYK': 'CMYK (32位)',
                        '1': '二值 (1位)',
                        'I': '整数 (32位)',
                        'F': '浮点 (32位)'
                    }
                    info['color_mode_description'] = mode_info.get(img.mode, f'未知模式 ({img.mode})')
                    
                    # 检查是否有透明度
                    info['has_transparency'] = img.mode in ['RGBA', 'LA'] or 'transparency' in img.info
                    
            except Exception as e:
                info['pil_error'] = str(e)
                info['pil_loadable'] = False
        
        return info
    
    def _calculate_memory_requirements(self, file_path: str) -> Dict[str, Any]:
        """计算内存需求"""
        memory_info = {}
        
        try:
            # 获取图片基本信息
            image_info = self._get_image_info(file_path)
            
            if 'width' in image_info and 'height' in image_info:
                width = image_info['width']
                height = image_info['height']
                
                # 基础内存计算（不同色彩模式）
                if 'mode' in image_info:
                    mode = image_info['mode']
                    bytes_per_pixel = {
                        'L': 1, 'P': 1, '1': 0.125,
                        'RGB': 3, 'RGBA': 4,
                        'CMYK': 4, 'I': 4, 'F': 4
                    }.get(mode, 4)
                elif 'channels' in image_info:
                    bytes_per_pixel = image_info['channels']
                else:
                    bytes_per_pixel = 4  # 保守估计
                
                # 计算不同场景的内存需求
                base_memory = width * height * bytes_per_pixel
                
                memory_info.update({
                    'base_memory_bytes': base_memory,
                    'base_memory_kb': base_memory / 1024,
                    'base_memory_mb': base_memory / (1024 * 1024),
                    'processing_memory_mb': (base_memory * 3) / (1024 * 1024),  # 处理时需要3倍内存
                    'display_memory_mb': (base_memory * 1.5) / (1024 * 1024),   # 显示时需要1.5倍内存
                    'bytes_per_pixel': bytes_per_pixel
                })
                
                # 内存等级分类
                memory_mb = memory_info['base_memory_mb']
                if memory_mb < 10:
                    memory_info['memory_level'] = '小'
                elif memory_mb < 50:
                    memory_info['memory_level'] = '中等'
                elif memory_mb < 200:
                    memory_info['memory_level'] = '大'
                else:
                    memory_info['memory_level'] = '超大'
                
                # 系统内存对比
                try:
                    system_memory = psutil.virtual_memory()
                    memory_info['system_total_gb'] = system_memory.total / (1024**3)
                    memory_info['system_available_mb'] = system_memory.available / (1024**2)
                    memory_info['memory_usage_percent'] = (memory_info['processing_memory_mb'] / memory_info['system_available_mb']) * 100
                except Exception:
                    pass
                
        except Exception as e:
            memory_info['error'] = f'内存计算失败: {e}'
        
        return memory_info
    
    def _check_compatibility(self, file_path: str) -> Dict[str, Any]:
        """检查兼容性"""
        compatibility = {
            'opencv_support': False,
            'pil_support': False,
            'format_issues': [],
            'loading_recommendations': [],
            'opencv_error': None,
            'pil_error': None,
            'fallback_available': False
        }
        
        # 检查PIL兼容性（更宽容，先检查）
        if PIL_AVAILABLE:
            try:
                with PILImage.open(file_path) as img:
                    compatibility['pil_support'] = True
                    # 记录图片基本信息用于后续判断
                    compatibility['pil_mode'] = img.mode
                    compatibility['pil_format'] = img.format
            except Exception as e:
                compatibility['pil_support'] = False
                compatibility['pil_error'] = str(e)
        
        # 检查OpenCV兼容性（更详细的错误处理）
        if CV2_AVAILABLE:
            try:
                # 尝试直接加载
                image = cv2.imread(file_path)
                if image is not None:
                    compatibility['opencv_support'] = True
                    del image
                else:
                    # 如果OpenCV返回None，但PIL可以加载，尝试通过PIL转换
                    if compatibility['pil_support']:
                        try:
                            import numpy as np
                            with PILImage.open(file_path) as pil_img:
                                # 尝试转换为OpenCV格式
                                if pil_img.mode == 'RGBA':
                                    opencv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGBA2BGRA)
                                elif pil_img.mode == 'RGB':
                                    opencv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                                else:
                                    opencv_img = np.array(pil_img)
                                
                                if opencv_img is not None:
                                    compatibility['opencv_support'] = True
                                    compatibility['fallback_available'] = True
                                    del opencv_img
                                    
                        except Exception as fallback_error:
                            compatibility['opencv_error'] = f"直接加载失败，转换也失败: {fallback_error}"
                    else:
                        compatibility['opencv_error'] = "OpenCV返回None，且PIL也无法加载"
                        
            except Exception as e:
                compatibility['opencv_support'] = False
                compatibility['opencv_error'] = str(e)
                
                # 如果OpenCV异常但PIL可以加载，尝试fallback
                if compatibility['pil_support']:
                    try:
                        import numpy as np
                        with PILImage.open(file_path) as pil_img:
                            # 简单的兼容性测试
                            np_array = np.array(pil_img)
                            if np_array is not None:
                                compatibility['fallback_available'] = True
                    except Exception:
                        pass
        
        # 智能化建议生成
        if not compatibility['opencv_support'] and not compatibility['pil_support']:
            compatibility['loading_recommendations'].append('文件可能已损坏或格式不受支持')
        elif not compatibility['opencv_support'] and compatibility['pil_support']:
            if compatibility['fallback_available']:
                compatibility['loading_recommendations'].append('OpenCV无法直接加载，但可通过PIL转换后处理')
            else:
                # 检查是否是已知的OpenCV不支持的格式
                pil_format = compatibility.get('pil_format', '').upper()
                if pil_format in ['WEBP', 'TIFF', 'ICO', 'PSD']:
                    compatibility['loading_recommendations'].append(f'OpenCV不支持{pil_format}格式，建议转换为PNG或JPG')
                else:
                    compatibility['loading_recommendations'].append('OpenCV加载异常，建议检查图片完整性或转换格式')
        elif compatibility['opencv_support'] and not compatibility['pil_support']:
            compatibility['loading_recommendations'].append('PIL无法加载，但OpenCV可以处理')
        
        return compatibility
    
    def _get_metadata(self, file_path: str) -> Dict[str, Any]:
        """获取图片元数据"""
        metadata = {}
        
        if PIL_AVAILABLE:
            try:
                with PILImage.open(file_path) as img:
                    # 获取EXIF数据
                    if hasattr(img, '_getexif') and img._getexif():
                        metadata['has_exif'] = True
                        # 这里可以解析EXIF数据，但为了简化，只记录是否存在
                    else:
                        metadata['has_exif'] = False
                    
                    # 获取其他元数据
                    metadata['info'] = dict(img.info)
                    
            except Exception as e:
                metadata['error'] = f'元数据获取失败: {e}'
        
        return metadata
    
    def _generate_recommendations(self, info: Dict[str, Any]) -> list:
        """生成优化建议"""
        recommendations = []
        
        try:
            memory_info = info.get('memory_info', {})
            image_info = info.get('image_info', {})
            compatibility_info = info.get('compatibility_info', {})
            
            # 内存相关建议（考虑OpenCV兼容性）
            if 'memory_level' in memory_info:
                level = memory_info['memory_level']
                opencv_supported = compatibility_info.get('opencv_support', True)
                
                if level == '超大':
                    if not opencv_supported:
                        recommendations.append('图片尺寸过大导致OpenCV加载失败，建议缩小到4K以下')
                    else:
                        recommendations.extend([
                            '图片尺寸很大，建议缩小到4K以下',
                            '处理前先关闭其他应用程序释放内存',
                            '考虑使用批处理模式分块处理'
                        ])
                elif level == '大':
                    if not opencv_supported:
                        recommendations.append('图片较大可能导致OpenCV加载问题，建议缩小尺寸')
                    else:
                        recommendations.append('图片较大，处理时可能需要较长时间')
            
            # 格式相关建议（更智能化）
            if not compatibility_info.get('opencv_support', True):
                # 检查是否有fallback可用
                if compatibility_info.get('fallback_available', False):
                    recommendations.append('OpenCV无法直接加载，但可通过转换后处理')
                else:
                    # 检查具体错误原因
                    opencv_error = compatibility_info.get('opencv_error', '')
                    if 'memory' in opencv_error.lower() or 'size' in opencv_error.lower():
                        recommendations.append('图片过大导致OpenCV加载失败，建议缩小尺寸')
                    elif compatibility_info.get('pil_support', False):
                        pil_format = compatibility_info.get('pil_format', '').upper()
                        if pil_format in ['WEBP', 'TIFF', 'ICO', 'PSD']:
                            recommendations.append(f'OpenCV不支持{pil_format}格式，建议转换为PNG或JPG格式')
                        else:
                            recommendations.append('OpenCV加载异常，建议检查图片完整性')
                    else:
                        recommendations.append('OpenCV无法加载，建议转换为PNG或JPG格式')
            
            # 尺寸相关建议
            if 'width' in image_info and 'height' in image_info:
                width, height = image_info['width'], image_info['height']
                if width > 8192 or height > 8192:
                    recommendations.append('图片分辨率超过8K，建议降低分辨率以提高处理速度')
                elif width < 100 or height < 100:
                    recommendations.append('图片分辨率较低，某些处理效果可能不佳')
            
            # 透明度建议
            if image_info.get('has_transparency', False):
                recommendations.append('图片包含透明通道，某些操作可能会移除透明度')
            
        except Exception:
            pass
        
        return recommendations
    
    def format_info_text(self, info: Dict[str, Any]) -> str:
        """格式化信息为可读文本"""
        try:
            lines = []
            
            # 文件信息
            file_info = info.get('file_info', {})
            if 'filename' in file_info:
                lines.append(f"文件名: {file_info['filename']}")
                lines.append(f"格式: {file_info.get('format_name', '未知')}")
                lines.append(f"大小: {file_info.get('file_size_mb', 0):.2f} MB")
            
            # 图片信息
            image_info = info.get('image_info', {})
            if 'width' in image_info and 'height' in image_info:
                lines.append(f"尺寸: {image_info['width']} × {image_info['height']}")
                lines.append(f"像素数: {image_info.get('total_pixels', 0):,}")
                if 'color_mode_description' in image_info:
                    lines.append(f"色彩模式: {image_info['color_mode_description']}")
            
            # 内存信息
            memory_info = info.get('memory_info', {})
            if 'base_memory_mb' in memory_info:
                lines.append(f"内存需求: {memory_info['base_memory_mb']:.1f} MB ({memory_info.get('memory_level', '未知')})")
            
            # 兼容性
            compatibility_info = info.get('compatibility_info', {})
            opencv_ok = compatibility_info.get('opencv_support', False)
            pil_ok = compatibility_info.get('pil_support', False)
            lines.append(f"兼容性: OpenCV({'✓' if opencv_ok else '✗'}) PIL({'✓' if pil_ok else '✗'})")
            
            return '\n'.join(lines)
            
        except Exception as e:
            return f"信息格式化失败: {e}"


# 全局实例
image_info_analyzer = ImageInfoAnalyzer()


def get_quick_image_info(file_path: str) -> str:
    """快速获取图片信息的简化接口"""
    try:
        info = image_info_analyzer.analyze_image_file(file_path)
        return image_info_analyzer.format_info_text(info)
    except Exception as e:
        return f"获取图片信息失败: {e}"


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        print("=== 图片信息分析 ===")
        print(get_quick_image_info(file_path))
        
        print("\n=== 详细信息 ===")
        info = image_info_analyzer.analyze_image_file(file_path)
        
        for key, value in info.items():
            print(f"\n{key}:")
            if isinstance(value, dict):
                for k, v in value.items():
                    print(f"  {k}: {v}")
            elif isinstance(value, list):
                for item in value:
                    print(f"  - {item}")
            else:
                print(f"  {value}")
    else:
        print("用法: python image_info.py <图片文件路径>")