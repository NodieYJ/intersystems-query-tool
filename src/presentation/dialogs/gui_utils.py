#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GUI 通用工具模块

提供对话框和UI组件的通用功能，减少代码重复
"""

import logging
import hashlib
import threading
from typing import Optional, Any, Tuple, Dict, List, Iterator
from functools import lru_cache

from PySide2.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)


class GUIErrorHandler:
    """
    统一的GUI错误处理器

    提供标准化的错误处理和日志记录
    """

    @staticmethod
    def handle_error(
        context: str,
        error: Exception,
        show_dialog: bool = False,
        parent: Optional[Any] = None,
        logger_instance: Optional[logging.Logger] = None
    ) -> None:
        """
        统一处理错误的静态方法

        Args:
            context: 错误上下文描述
            error: 异常对象
            show_dialog: 是否显示错误对话框
            parent: 父窗口部件
            logger_instance: 日志记录器实例
        """
        error_msg = f"{context}: {str(error)}"

        # 记录日志
        if logger_instance:
            logger_instance.error(error_msg, exc_info=True)
        else:
            logger.error(error_msg, exc_info=True)

        # 显示对话框
        if show_dialog and parent:
            QMessageBox.critical(parent, "错误", error_msg)


class FileUtils:
    """
    文件操作工具类
    """

    @staticmethod
    def get_file_extension(filename: str) -> str:
        """
        获取文件扩展名（包含点）

        Args:
            filename: 文件名

        Returns:
            str: 文件扩展名（小写），例如 '.txt'
        """
        _, ext = FileUtils.split_extension(filename)
        return ext

    @staticmethod
    def split_extension(filename: str) -> Tuple[str, str]:
        """
        分离文件名和扩展名

        Args:
            filename: 文件名

        Returns:
            Tuple[str, str]: (基础名, 扩展名)
        """
        if '.' in filename:
            parts = filename.rsplit('.', 1)
            return parts[0], '.' + parts[1].lower()
        return filename, ''

    @staticmethod
    def is_log_file(filename: str, extensions: Tuple[str, ...] = ('.log', '.txt', '.LOG')) -> bool:
        """
        检查是否为日志文件

        Args:
            filename: 文件名
            extensions: 支持的扩展名元组

        Returns:
            bool: 是否为日志文件
        """
        _, ext = FileUtils.split_extension(filename)
        return ext.lower() in extensions


class StringUtils:
    """
    字符串操作工具类
    """

    @staticmethod
    def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """
        截断字符串

        Args:
            text: 原始字符串
            max_length: 最大长度
            suffix: 截断后缀

        Returns:
            str: 截断后的字符串
        """
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix

    @staticmethod
    def mask_sensitive(text: str, show_length: int = 4) -> str:
        """
        脱敏处理（用于日志记录）

        Args:
            text: 原始文本
            show_length: 显示的字符数

        Returns:
            str: 脱敏后的文本
        """
        if len(text) <= show_length:
            return '*' * len(text)
        return text[:show_length] + '*' * (len(text) - show_length)


class MemoryCache:
    """
    简单内存缓存管理器

    提供线程安全的内存缓存，支持TTL过期
    """

    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        """
        初始化缓存管理器

        Args:
            max_size: 最大缓存条目数
            ttl_seconds: 缓存过期时间（秒）
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存的值，不存在或已过期则返回 None
        """
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            import time
            if time.time() - entry['timestamp'] > self._ttl_seconds:
                del self._cache[key]
                return None

            entry['timestamp'] = time.time()  # 更新访问时间
            return entry['value']

    def set(self, key: str, value: Any) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
        """
        with self._lock:
            # 清理过期条目
            self._cleanup_expired()

            # 如果缓存已满，删除最旧的条目
            if len(self._cache) >= self._max_size:
                oldest_key = min(self._cache.keys(),
                                 key=lambda k: self._cache[k]['timestamp'])
                del self._cache[oldest_key]

            import time
            self._cache[key] = {
                'value': value,
                'timestamp': time.time()
            }

    def _cleanup_expired(self) -> None:
        """清理所有过期条目"""
        import time
        expired_keys = [
            key for key, entry in self._cache.items()
            if time.time() - entry['timestamp'] > self._ttl_seconds
        ]
        for key in expired_keys:
            del self._cache[key]

    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()

    def remove(self, key: str) -> bool:
        """
        删除指定缓存

        Args:
            key: 缓存键

        Returns:
            bool: 是否成功删除
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False


class FileReadUtils:
    """
    文件高效读取工具类

    提供内存友好的大文件读取方法
    """

    CHUNK_SIZE = 1024 * 1024  # 1MB chunks

    @staticmethod
    def read_lines_generator(filepath: str, encoding: str = 'utf-8',
                             errors: str = 'ignore') -> Iterator[str]:
        """
        生成器方式逐行读取文件（内存友好）

        Args:
            filepath: 文件路径
            encoding: 编码格式
            errors: 错误处理方式

        Yields:
            str: 文件的每一行
        """
        with open(filepath, 'r', encoding=encoding, errors=errors) as f:
            for line in f:
                yield line

    @staticmethod
    def read_large_file_first_n(filepath: str, n: int = 100,
                                 encoding: str = 'utf-8',
                                 errors: str = 'ignore') -> Tuple[List[str], int]:
        """
        读取大文件的前N行（内存友好）

        Args:
            filepath: 文件路径
            n: 要读取的行数
            encoding: 编码格式
            errors: 错误处理方式

        Returns:
            Tuple[List[str], int]: (前n行列表, 总行数)
        """
        lines = []
        total_lines = 0

        with open(filepath, 'r', encoding=encoding, errors=errors) as f:
            for line in f:
                total_lines += 1
                if len(lines) < n:
                    lines.append(line)

        return lines, total_lines

    @staticmethod
    def get_file_hash(filepath: str, algorithm: str = 'md5') -> str:
        """
        计算文件哈希值（用于缓存验证）

        Args:
            filepath: 文件路径
            algorithm: 哈希算法

        Returns:
            str: 文件哈希值
        """
        hash_func = hashlib.new(algorithm)
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()


# 全局缓存实例（对话框级别复用）
log_content_cache = MemoryCache(max_size=50, ttl_seconds=600)  # 10分钟缓存
stats_cache = MemoryCache(max_size=20, ttl_seconds=300)  # 5分钟缓存


# 导出常用项
__all__ = [
    'GUIErrorHandler',
    'FileUtils',
    'StringUtils',
    'MemoryCache',
    'FileReadUtils',
    'log_content_cache',
    'stats_cache',
]
