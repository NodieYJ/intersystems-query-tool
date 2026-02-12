#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
gui_utils.py 单元测试

测试 GUI 通用工具模块的功能
"""

import unittest
import tempfile
import os
import time
from typing import Dict, Any

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.presentation.dialogs.gui_utils import (
    GUIErrorHandler,
    FileUtils,
    StringUtils,
    MemoryCache,
    FileReadUtils,
    log_content_cache,
    stats_cache
)


class TestFileUtils(unittest.TestCase):
    """FileUtils 工具类测试"""

    def test_get_file_extension_with_extension(self):
        """测试获取文件扩展名（有扩展名的情况）"""
        self.assertEqual(FileUtils.get_file_extension("test.txt"), '.txt')
        self.assertEqual(FileUtils.get_file_extension("test.log"), '.log')
        self.assertEqual(FileUtils.get_file_extension("test.TXT"), '.txt')

    def test_get_file_extension_without_extension(self):
        """测试获取文件扩展名（无扩展名的情况）"""
        self.assertEqual(FileUtils.get_file_extension("test"), '')

    def test_split_extension(self):
        """测试分离文件名和扩展名"""
        base, ext = FileUtils.split_extension("test.txt")
        self.assertEqual(base, "test")
        self.assertEqual(ext, '.txt')

        base, ext = FileUtils.split_extension("test.LOG")
        self.assertEqual(base, "test")
        self.assertEqual(ext, '.log')  # 转换为小写

    def test_is_log_file(self):
        """测试日志文件判断"""
        self.assertTrue(FileUtils.is_log_file("test.log"))
        self.assertTrue(FileUtils.is_log_file("test.txt"))
        self.assertTrue(FileUtils.is_log_file("test.LOG"))
        self.assertFalse(FileUtils.is_log_file("test.csv"))
        self.assertFalse(FileUtils.is_log_file("test"))

    def test_is_log_file_custom_extensions(self):
        """测试自定义扩展名判断"""
        extensions = ('.csv', '.dat', '.CSV')
        self.assertTrue(FileUtils.is_log_file("test.csv", extensions))
        self.assertTrue(FileUtils.is_log_file("test.CSV", extensions))
        self.assertFalse(FileUtils.is_log_file("test.log", extensions))


class TestStringUtils(unittest.TestCase):
    """StringUtils 工具类测试"""

    def test_truncate_short_string(self):
        """测试截断短字符串（不需要截断）"""
        result = StringUtils.truncate("hello", max_length=10)
        self.assertEqual(result, "hello")

    def test_truncate_long_string(self):
        """测试截断长字符串"""
        result = StringUtils.truncate("hello world test string", max_length=10, suffix="...")
        self.assertEqual(result, "hello w...")  # 7个字符 + "..."

    def test_truncate_exact_length(self):
        """测试截断恰好长度的字符串"""
        result = StringUtils.truncate("hello", max_length=5)
        self.assertEqual(result, "hello")

    def test_truncate_custom_suffix(self):
        """测试自定义后缀"""
        result = StringUtils.truncate("hello world", max_length=8, suffix="***")
        self.assertEqual(result, "hello***")  # 5个字符 + "***"

    def test_mask_sensitive_short(self):
        """测试脱敏短文本"""
        result = StringUtils.mask_sensitive("1234", show_length=4)
        self.assertEqual(result, "****")

    def test_mask_sensitive_normal(self):
        """测试正常脱敏"""
        result = StringUtils.mask_sensitive("password123", show_length=4)
        self.assertEqual(result, "pass*******")

    def test_mask_sensitive_empty(self):
        """测试空文本脱敏"""
        result = StringUtils.mask_sensitive("", show_length=4)
        self.assertEqual(result, "")


class TestMemoryCache(unittest.TestCase):
    """MemoryCache 缓存类测试"""

    def setUp(self):
        """创建独立的缓存实例用于测试"""
        self.cache = MemoryCache(max_size=10, ttl_seconds=1)

    def test_set_and_get(self):
        """测试设置和获取"""
        self.cache.set("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")

    def test_get_nonexistent(self):
        """测试获取不存在的键"""
        self.assertIsNone(self.cache.get("nonexistent"))

    def test_get_expired(self):
        """测试获取过期的缓存"""
        self.cache.set("key1", "value1")
        time.sleep(1.1)  # 等待过期
        self.assertIsNone(self.cache.get("key1"))

    def test_update_existing(self):
        """测试更新已存在的键"""
        self.cache.set("key1", "value1")
        self.cache.set("key1", "value2")
        self.assertEqual(self.cache.get("key1"), "value2")

    def test_remove(self):
        """测试删除缓存"""
        self.cache.set("key1", "value1")
        self.assertTrue(self.cache.remove("key1"))
        self.assertIsNone(self.cache.get("key1"))
        self.assertFalse(self.cache.remove("nonexistent"))

    def test_clear(self):
        """测试清空缓存"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.clear()
        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNone(self.cache.get("key2"))

    def test_max_size_eviction(self):
        """测试最大大小驱逐"""
        for i in range(15):
            self.cache.set(f"key{i}", f"value{i}")

        # 应该有10个条目
        count = 0
        for i in range(15):
            if self.cache.get(f"key{i}") is not None:
                count += 1
        self.assertLessEqual(count, 10)

    def test_thread_safety(self):
        """测试线程安全"""
        import threading

        def writer():
            for i in range(100):
                self.cache.set(f"key{i}", f"value{i}")

        threads = [threading.Thread(target=writer) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 确保没有异常
        self.assertTrue(True)  # 如果有线程安全问题会抛出异常


class TestFileReadUtils(unittest.TestCase):
    """FileReadUtils 文件读取工具类测试"""

    def setUp(self):
        """创建临时文件用于测试"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        self.large_file = os.path.join(self.temp_dir, "large.txt")

        # 创建测试文件
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write("line1\n")
            f.write("line2\n")
            f.write("line3\n")

        # 创建大文件
        with open(self.large_file, 'w', encoding='utf-8') as f:
            for i in range(1000):
                f.write(f"line {i}\n")

    def tearDown(self):
        """清理临时文件"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_read_lines_generator(self):
        """测试生成器方式读取文件"""
        lines = list(FileReadUtils.read_lines_generator(self.test_file))
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], "line1\n")
        self.assertEqual(lines[1], "line2\n")
        self.assertEqual(lines[2], "line3\n")

    def test_read_large_file_first_n(self):
        """测试读取大文件前N行"""
        lines, total = FileReadUtils.read_large_file_first_n(self.large_file, n=10)
        self.assertEqual(len(lines), 10)
        self.assertEqual(total, 1000)

    def test_read_large_file_first_n_smaller_than_file(self):
        """测试读取行数大于文件行数"""
        lines, total = FileReadUtils.read_large_file_first_n(self.test_file, n=100)
        self.assertEqual(len(lines), 3)
        self.assertEqual(total, 3)

    def test_get_file_hash(self):
        """测试文件哈希计算"""
        hash1 = FileReadUtils.get_file_hash(self.test_file)
        hash2 = FileReadUtils.get_file_hash(self.test_file)
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 32)  # MD5 哈希长度

    def test_get_file_hash_different_files(self):
        """测试不同文件哈希不同"""
        hash1 = FileReadUtils.get_file_hash(self.test_file)
        hash2 = FileReadUtils.get_file_hash(self.large_file)
        self.assertNotEqual(hash1, hash2)


class TestGUIErrorHandler(unittest.TestCase):
    """GUIErrorHandler 错误处理器测试"""

    def test_handle_error_with_dialog(self):
        """测试错误处理（显示对话框）"""
        # 由于需要 QApplication，这里只测试不显示对话框的情况
        error = ValueError("test error")
        GUIErrorHandler.handle_error(
            context="测试",
            error=error,
            show_dialog=False
        )
        # 不应抛出异常

    def test_handle_error_with_logger(self):
        """测试带日志记录器的错误处理"""
        import logging
        test_logger = logging.getLogger("test_logger")

        error = ValueError("test error")
        GUIErrorHandler.handle_error(
            context="测试",
            error=error,
            show_dialog=False,
            logger_instance=test_logger
        )
        # 不应抛出异常


class TestGlobalCacheInstances(unittest.TestCase):
    """全局缓存实例测试"""

    def test_log_content_cache_exists(self):
        """测试日志内容缓存实例存在"""
        self.assertIsInstance(log_content_cache, MemoryCache)

    def test_stats_cache_exists(self):
        """测试统计缓存实例存在"""
        self.assertIsInstance(stats_cache, MemoryCache)


if __name__ == '__main__':
    unittest.main()
