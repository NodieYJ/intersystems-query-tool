#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""SQLCompleter 单元测试"""

import unittest
import os
import sys
from unittest.mock import Mock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from PySide2.QtWidgets import QApplication, QTextEdit
from PySide2.QtCore import Qt

from presentation.widgets.sql_completer import SQLCompleter

# 创建 QApplication 实例（每个测试文件只需要一个）
_app = None


def get_app():
    global _app
    if _app is None:
        _app = QApplication([])
    return _app


class TestSQLCompleter(unittest.TestCase):
    """测试 SQL 补全器"""

    @classmethod
    def setUpClass(cls):
        """测试类开始前创建 QApplication"""
        cls.app = get_app()

    def setUp(self):
        """每个测试前创建编辑器"""
        self.editor = QTextEdit()
        self.completer = SQLCompleter(self.editor, 'test_conn')

    def test_completer_initialization(self):
        """测试补全器初始化"""
        self.assertIsNotNone(self.completer)
        self.assertEqual(self.completer.connection_id, 'test_conn')
        self.assertIsNotNone(self.completer.keyword_provider)
        self.assertIsNotNone(self.completer.metadata_cache)

    def test_get_current_word(self):
        """测试获取当前单词"""
        # 模拟输入 "SELECT us"
        self.editor.setPlainText("SELECT us")
        cursor = self.editor.textCursor()
        cursor.movePosition(cursor.End)
        self.editor.setTextCursor(cursor)
        
        # 由于需要实际 UI 交互，这里简化测试
        word = self.completer._get_current_word("SELECT us")
        self.assertEqual(word, "us")

    def test_needs_table_name(self):
        """测试判断是否需要表名"""
        # 应该匹配的情况
        self.assertTrue(self.completer._needs_table_name("SELECT * FROM "))
        self.assertTrue(self.completer._needs_table_name("JOIN "))
        self.assertTrue(self.completer._needs_table_name("INSERT INTO "))
        
        # 不应该匹配的情况
        self.assertFalse(self.completer._needs_table_name("SELECT "))
        self.assertFalse(self.completer._needs_table_name("WHERE "))

    def test_needs_column_name(self):
        """测试判断是否需要列名"""
        # 应该匹配的情况
        self.assertTrue(self.completer._needs_column_name("SELECT "))
        self.assertTrue(self.completer._needs_column_name("SELECT id, "))
        self.assertTrue(self.completer._needs_column_name("WHERE "))
        
        # 不应该匹配的情况
        self.assertFalse(self.completer._needs_column_name("FROM "))


if __name__ == '__main__':
    unittest.main()
