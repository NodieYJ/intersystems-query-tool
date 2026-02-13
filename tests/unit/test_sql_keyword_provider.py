#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""SQLKeywordProvider 单元测试"""

import unittest
import os
import sys

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from presentation.widgets.sql_keyword_provider import SQLKeywordProvider


class TestSQLKeywordProvider(unittest.TestCase):
    """测试 SQL 关键字提供者"""

    def setUp(self):
        self.provider = SQLKeywordProvider()

    def test_provider_initialization(self):
        """测试提供者初始化"""
        self.assertIsNotNone(self.provider)
        self.assertIsInstance(self.provider.all_keywords, list)
        self.assertGreater(len(self.provider.all_keywords), 0)

    def test_get_suggestions_with_prefix(self):
        """测试根据前缀获取建议"""
        suggestions = self.provider.get_suggestions("SEL")
        self.assertIn("SELECT", suggestions)

    def test_get_suggestions_case_insensitive(self):
        """测试大小写不敏感的建议"""
        upper_suggestions = self.provider.get_suggestions("sel")
        lower_suggestions = self.provider.get_suggestions("SEL")
        self.assertEqual(upper_suggestions, lower_suggestions)

    def test_get_suggestions_empty_prefix(self):
        """测试空前缀返回所有关键字"""
        suggestions = self.provider.get_suggestions("")
        self.assertGreater(len(suggestions), 50)

    def test_get_suggestions_no_match(self):
        """测试无匹配时返回空列表"""
        suggestions = self.provider.get_suggestions("XYZ123")
        self.assertEqual(len(suggestions), 0)


if __name__ == '__main__':
    unittest.main()
