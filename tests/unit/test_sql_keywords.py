#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""SQL关键字数据文件测试"""

import json
import os
import unittest


class TestSQLKeywords(unittest.TestCase):
    """测试 SQL 关键字数据文件"""

    def setUp(self):
        self.keywords_path = 'resources/data/sql_keywords.json'

    def test_keywords_file_exists(self):
        """测试关键字文件存在"""
        self.assertTrue(os.path.exists(self.keywords_path))

    def test_keywords_file_is_valid_json(self):
        """测试关键字文件是有效的 JSON"""
        with open(self.keywords_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertIsInstance(data, dict)

    def test_keywords_has_required_categories(self):
        """测试包含必需的分类"""
        with open(self.keywords_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        required_categories = ['DML', 'DDL', 'CLAUSES', 'JOINS', 'OPERATORS', 'FUNCTIONS']
        for category in required_categories:
            self.assertIn(category, data)
            self.assertIsInstance(data[category], list)
            self.assertGreater(len(data[category]), 0)

    def test_keywords_are_uppercase(self):
        """测试关键字都是大写"""
        with open(self.keywords_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for category, keywords in data.items():
            for keyword in keywords:
                self.assertEqual(keyword, keyword.upper())


if __name__ == '__main__':
    unittest.main()
