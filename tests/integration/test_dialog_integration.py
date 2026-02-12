#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
对话框集成测试

测试对话框之间的交互和错误处理流程
"""

import unittest
import os
import sys
import tempfile
import threading
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 设置 Qt 应用程序（必须在导入 GUI 模块之前）
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt

# 导入需要测试的模块
from src.presentation.dialogs.gui_utils import (
    FileReadUtils, MemoryCache, GUIErrorHandler
)

# 创建 QApplication 实例（如果尚未创建）
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestLogDialogIntegration(unittest.TestCase):
    """LogDialog 集成测试"""

    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        # 创建临时日志目录和文件
        cls.temp_dir = tempfile.mkdtemp()
        cls.log_dir = os.path.join(cls.temp_dir, "logs")
        os.makedirs(cls.log_dir)

        # 创建测试日志文件
        cls.test_log_file = os.path.join(cls.log_dir, "test.log")
        with open(cls.test_log_file, 'w', encoding='utf-8') as f:
            f.write("2024-01-01 10:00:00 INFO Test message 1\n")
            f.write("2024-01-01 10:00:01 WARNING Test message 2\n")
            f.write("2024-01-01 10:00:02 ERROR Test message 3\n")

    @classmethod
    def tearDownClass(cls):
        """清理测试环境"""
        import shutil
        shutil.rmtree(cls.temp_dir)

    def test_log_dialog_creation(self):
        """测试日志对话框创建"""
        from src.presentation.dialogs.log_dialog import LogDialog

        dialog = LogDialog()
        self.assertIsNotNone(dialog)
        self.assertEqual(dialog.windowTitle(), "日志")
        dialog.close()

    def test_log_dialog_file_list_loading(self):
        """测试日志文件列表加载"""
        from src.presentation.dialogs.log_dialog import LogDialog

        # 临时修改日志目录
        dialog = LogDialog()
        original_log_dir = dialog.log_dir
        dialog.log_dir = self.log_dir

        # 重新加载文件列表
        dialog.load_file_list()

        # 验证文件列表
        self.assertEqual(dialog.file_list.count(), 1)

        dialog.close()
        dialog.log_dir = original_log_dir

    def test_log_dialog_file_content_loading(self):
        """测试日志文件内容加载"""
        from src.presentation.dialogs.log_dialog import LogDialog

        dialog = LogDialog()
        dialog.log_dir = self.log_dir
        dialog.load_file_list()

        # 选择文件
        if dialog.file_list.count() > 0:
            item = dialog.file_list.item(0)
            dialog.on_file_selected(item)

            # 验证内容已加载
            content = dialog.text_editor.toPlainText()
            self.assertIn("Test message", content)

        dialog.close()

    def test_log_dialog_search_functionality(self):
        """测试日志搜索功能"""
        from src.presentation.dialogs.log_dialog import LogDialog

        dialog = LogDialog()
        dialog.log_dir = self.log_dir
        dialog.load_file_list()

        # 加载文件内容
        if dialog.file_list.count() > 0:
            item = dialog.file_list.item(0)
            dialog.on_file_selected(item)

            # 执行搜索
            dialog.search_input.setText("ERROR")
            dialog.perform_search('down')

            # 验证搜索结果
            self.assertEqual(dialog.match_info_label.text(), "1/1")

        dialog.close()

    def test_log_dialog_cache_functionality(self):
        """测试日志缓存功能"""
        from src.presentation.dialogs.log_dialog import LogDialog
        from src.presentation.dialogs.gui_utils import log_content_cache

        dialog = LogDialog()
        dialog.log_dir = self.log_dir
        dialog.load_file_list()

        # 第一次加载（应该是缓存未命中）
        if dialog.file_list.count() > 0:
            item = dialog.file_list.item(0)
            dialog.on_file_selected(item)

            # 等待异步加载完成（如果是异步加载）
            time.sleep(0.5)

            # 清除缓存并重新加载（应该是缓存未命中）
            log_content_cache.clear()
            dialog.text_editor.clear()

            item = dialog.file_list.item(0)
            dialog.on_file_selected(item)

            time.sleep(0.5)

        dialog.close()


class TestDataAnalysisDialogIntegration(unittest.TestCase):
    """DataAnalysisDialog 集成测试"""

    def test_data_analysis_dialog_creation(self):
        """测试数据分析对话框创建"""
        from src.presentation.dialogs.data_analysis_dialog import DataAnalysisDialog

        dialog = DataAnalysisDialog()
        self.assertIsNotNone(dialog)
        self.assertEqual(dialog.windowTitle(), "数据分析")
        dialog.close()

    def test_data_analysis_dialog_with_initial_data(self):
        """测试带初始数据的数据分析对话框"""
        from src.presentation.dialogs.data_analysis_dialog import DataAnalysisDialog

        # 创建测试数据
        initial_data = [
            {"name": "Alice", "age": 25, "score": 85},
            {"name": "Bob", "age": 30, "score": 90},
            {"name": "Charlie", "age": 35, "score": 78},
        ]

        dialog = DataAnalysisDialog(initial_data=initial_data)

        # 等待异步加载完成
        time.sleep(0.2)

        dialog.close()


class TestErrorHandlingIntegration(unittest.TestCase):
    """错误处理集成测试"""

    def test_gui_error_handler_integration(self):
        """测试 GUI 错误处理器集成"""
        from src.presentation.dialogs.gui_utils import GUIErrorHandler
        from PySide2.QtWidgets import QWidget

        # 创建父部件
        parent = QWidget()

        # 测试错误处理（不显示对话框）
        try:
            raise ValueError("Test error for integration")
        except ValueError as e:
            GUIErrorHandler.handle_error(
                context="集成测试",
                error=e,
                show_dialog=False,
                parent=parent
            )

        parent.close()

    def test_cache_error_resilience(self):
        """测试缓存错误恢复能力"""
        from src.presentation.dialogs.gui_utils import MemoryCache

        cache = MemoryCache(max_size=5, ttl_seconds=1)

        # 设置正常值
        cache.set("key1", "value1")
        self.assertEqual(cache.get("key1"), "value1")

        # 测试过期后清理
        time.sleep(1.1)
        self.assertIsNone(cache.get("key1"))

        # 测试各种数据类型
        cache.set("dict", {"nested": "value"})
        cache.set("list", [1, 2, 3])
        cache.set("number", 42)

        self.assertEqual(cache.get("dict"), {"nested": "value"})
        self.assertEqual(cache.get("list"), [1, 2, 3])
        self.assertEqual(cache.get("number"), 42)


class TestFileReadUtilsIntegration(unittest.TestCase):
    """FileReadUtils 集成测试"""

    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        cls.temp_dir = tempfile.mkdtemp()

        # 创建不同编码的测试文件
        cls.utf8_file = os.path.join(cls.temp_dir, "utf8.txt")
        with open(cls.utf8_file, 'w', encoding='utf-8') as f:
            f.write("line1\nline2\nline3\n")

        cls.gbk_file = os.path.join(cls.temp_dir, "gbk.txt")
        with open(cls.gbk_file, 'w', encoding='gbk') as f:
            f.write("中文内容\n测试数据\n")

    @classmethod
    def tearDownClass(cls):
        """清理测试环境"""
        import shutil
        shutil.rmtree(cls.temp_dir)

    def test_file_read_utils_utf8(self):
        """测试 UTF-8 文件读取"""
        lines = list(FileReadUtils.read_lines_generator(self.utf8_file))
        self.assertEqual(len(lines), 3)

    def test_file_read_utils_first_n_lines(self):
        """测试读取前 N 行"""
        lines, total = FileReadUtils.read_lines_generator(self.utf8_file), 3
        lines, total = FileReadUtils.read_large_file_first_n(self.utf8_file, n=2)
        self.assertEqual(len(lines), 2)
        self.assertEqual(total, 3)

    def test_file_hash_consistency(self):
        """测试文件哈希一致性"""
        hash1 = FileReadUtils.get_file_hash(self.utf8_file)
        hash2 = FileReadUtils.get_file_hash(self.utf8_file)
        self.assertEqual(hash1, hash2)


class TestMemoryCacheConcurrency(unittest.TestCase):
    """内存缓存并发测试"""

    def test_concurrent_access(self):
        """测试并发访问"""
        cache = MemoryCache(max_size=100, ttl_seconds=60)
        errors = []

        def writer(thread_id):
            try:
                for i in range(50):
                    cache.set(f"thread_{thread_id}_key_{i}", f"value_{i}")
            except Exception as e:
                errors.append(e)

        def reader(thread_id):
            try:
                for i in range(50):
                    cache.get(f"thread_{thread_id}_key_{i}")
            except Exception as e:
                errors.append(e)

        threads = []
        # 创建多个读写线程
        for i in range(5):
            t = threading.Thread(target=writer, args=(i,))
            threads.append(t)
            t = threading.Thread(target=reader, args=(i,))
            threads.append(t)

        # 启动所有线程
        for t in threads:
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join()

        # 验证没有错误
        self.assertEqual(len(errors), 0, f"并发访问出错: {errors}")


if __name__ == '__main__':
    unittest.main()
