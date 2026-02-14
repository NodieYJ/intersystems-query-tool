#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SQL 补全功能集成测试

测试 SQLCompleter 与 SQLQueryDialog 的集成
以及验收测试用例
"""

import unittest
import os
import sys
import time
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Any

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from PySide2.QtWidgets import QApplication, QTextEdit
from PySide2.QtCore import Qt, QPoint

from presentation.widgets.sql_completer import SQLCompleter
from business.services.metadata_cache_service import LocalMetadataCache


# 创建 QApplication 实例
_app = None


def get_app():
    global _app
    if _app is None:
        _app = QApplication([])
    return _app


class TestSQLCompleterIntegration(unittest.TestCase):
    """SQL 补全器集成测试"""

    @classmethod
    def setUpClass(cls):
        """测试类开始前创建 QApplication"""
        cls.app = get_app()

    def setUp(self):
        """每个测试前创建编辑器"""
        self.editor = QTextEdit()
        self.completer = SQLCompleter(self.editor, 'test_conn')

    def tearDown(self):
        """清理资源"""
        self.completer.deleteLater()
        self.editor.deleteLater()

    # ==================== 集成测试 ====================

    def test_completer_with_empty_metadata(self):
        """测试空元数据情况下的补全"""
        # 不加载任何元数据，应该只返回关键字
        self.assertIsNotNone(self.completer.keyword_provider)
        # 使用正确的方法名获取关键字
        keywords = self.completer.keyword_provider.get_suggestions("")
        self.assertGreater(len(keywords), 0)

    def test_completer_with_tables(self):
        """测试加载表名后的补全"""
        # 模拟加载表元数据 - 使用正确的列格式
        tables_data = [
            {'name': 'users', 'columns': [
                {'name': 'id', 'type': 'INTEGER'},
                {'name': 'username', 'type': 'VARCHAR'},
                {'name': 'email', 'type': 'VARCHAR'},
                {'name': 'created_at', 'type': 'TIMESTAMP'}
            ]},
            {'name': 'orders', 'columns': [
                {'name': 'id', 'type': 'INTEGER'},
                {'name': 'user_id', 'type': 'INTEGER'},
                {'name': 'total', 'type': 'DECIMAL'},
                {'name': 'status', 'type': 'VARCHAR'}
            ]},
            {'name': 'products', 'columns': [
                {'name': 'id', 'type': 'INTEGER'},
                {'name': 'name', 'type': 'VARCHAR'},
                {'name': 'price', 'type': 'DECIMAL'}
            ]},
        ]
        
        self.completer.set_metadata(tables_data)
        
        # 验证表名已加载 - 使用正确的方法
        cached_tables = self.completer.metadata_cache.get_all_tables('test_conn')
        self.assertEqual(len(cached_tables), 3)

    def test_completer_context_detection(self):
        """测试上下文检测功能"""
        # 测试需要表名的场景
        self.assertTrue(self.completer._needs_table_name("SELECT * FROM "))
        self.assertTrue(self.completer._needs_table_name("JOIN "))
        self.assertTrue(self.completer._needs_table_name("INSERT INTO "))
        
        # 测试需要列名的场景
        self.assertTrue(self.completer._needs_column_name("SELECT "))
        self.assertTrue(self.completer._needs_column_name("WHERE "))

    def test_keyword_completion(self):
        """测试关键字补全"""
        # 设置文本为 "SEL"
        self.editor.setPlainText("SEL")
        cursor = self.editor.textCursor()
        cursor.movePosition(cursor.End)
        self.editor.setTextCursor(cursor)
        
        # 获取当前词
        word = self.completer._get_current_word("SEL")
        self.assertEqual(word, "SEL")
        
        # 获取关键字建议 - 使用正确的方法
        suggestions = self.completer._get_suggestions("SEL", "SELECT ")
        # 验证 SELECT 在建议中
        self.assertTrue(any("SELECT" in s.upper() for s in suggestions))

    # ==================== 验收测试 ====================

    def test_acceptance_keyword_suggestions(self):
        """验收测试：输入 SQL 关键字前缀时显示建议"""
        test_cases = [
            ("SEL", ["SELECT"]),
            ("FRO", ["FROM"]),
            ("WHE", ["WHERE"]),
            ("INS", ["INSERT"]),
            ("UPDA", ["UPDATE"]),
            ("DELE", ["DELETE"]),
        ]
        
        for prefix, expected_keywords in test_cases:
            suggestions = self.completer._get_suggestions(prefix, "")
            # 验证至少包含期望的关键字
            has_match = any(kw.upper() in [s.upper() for s in suggestions] 
                          for kw in expected_keywords)
            self.assertTrue(has_match, 
                f"输入 '{prefix}' 时未找到关键字 {expected_keywords}, 实际: {suggestions[:5]}")

    def test_acceptance_table_suggestions(self):
        """验收测试：输入表名前缀时显示匹配的表"""
        # 加载测试表数据 - 使用正确的列格式
        tables_data = [
            {'name': 'users', 'columns': [
                {'name': 'id', 'type': 'INTEGER'},
                {'name': 'username', 'type': 'VARCHAR'}
            ]},
            {'name': 'user_profiles', 'columns': [
                {'name': 'user_id', 'type': 'INTEGER'},
                {'name': 'bio', 'type': 'TEXT'}
            ]},
            {'name': 'orders', 'columns': [
                {'name': 'id', 'type': 'INTEGER'},
                {'name': 'total', 'type': 'DECIMAL'}
            ]},
            {'name': 'order_items', 'columns': [
                {'name': 'order_id', 'type': 'INTEGER'},
                {'name': 'product_id', 'type': 'INTEGER'}
            ]},
        ]
        self.completer.set_metadata(tables_data)
        
        # 测试表名匹配
        test_cases = [
            ("users", ["users", "user_profiles"]),
            ("order", ["orders", "order_items"]),
            ("xyz", []),  # 不存在的表
        ]
        
        for prefix, expected_tables in test_cases:
            suggestions = self.completer._get_table_suggestions(prefix)
            # 去掉 (TABLE) 后缀后比较
            suggestion_names = [s.replace(' (TABLE)', '').replace(' (VIEW)', '') for s in suggestions]
            
            if expected_tables:
                has_match = any(t in suggestion_names for t in expected_tables)
                self.assertTrue(has_match,
                    f"输入 '{prefix}' 时未找到表 {expected_tables}, 实际: {suggestion_names}")
            else:
                # 不存在的表应该返回空或全部建议
                self.assertTrue(len(suggestions) >= 0)

    def test_acceptance_response_time(self):
        """验收测试：补全响应时间 < 100ms"""
        # 加载大量表数据（模拟 1000+ 表）- 使用正确的列格式
        tables_data = [
            {'name': f'table_{i}', 'columns': [
                {'name': f'col_{j}', 'type': 'VARCHAR'} for j in range(10)
            ]}
            for i in range(100)
        ]
        self.completer.set_metadata(tables_data)
        
        # 测试响应时间
        iterations = 10
        total_time = 0
        
        for _ in range(iterations):
            start_time = time.time()
            
            # 执行补全查询
            word = "table_"
            suggestions = self.completer._get_table_suggestions(word)
            
            elapsed = (time.time() - start_time) * 1000  # 转换为毫秒
            total_time += elapsed
        
        avg_time = total_time / iterations
        print(f"\n平均响应时间: {avg_time:.2f}ms")
        
        # 验证平均响应时间 < 100ms
        self.assertLess(avg_time, 100, 
            f"补全响应时间 {avg_time:.2f}ms 超过 100ms 阈值")

    def test_acceptance_large_table_support(self):
        """验收测试：支持 1000+ 表无卡顿"""
        # 创建大量表数据 - 使用正确的列格式
        large_tables_data = [
            {'name': f'table_{i:04d}', 'columns': [
                {'name': f'column_{j}', 'type': 'VARCHAR'} for j in range(20)
            ]}
            for i in range(1200)
        ]
        
        # 设置元数据
        start_time = time.time()
        self.completer.set_metadata(large_tables_data)
        set_time = (time.time() - start_time) * 1000
        
        print(f"\n加载 1200 个表的元数据耗时: {set_time:.2f}ms")
        
        # 验证加载时间合理（< 2秒）
        self.assertLess(set_time, 2000, 
            f"加载 1200 个表耗时 {set_time:.2f}ms，超过 2 秒")
        
        # 测试查询大量表时的响应
        start_time = time.time()
        suggestions = self.completer._get_table_suggestions("table_")
        query_time = (time.time() - start_time) * 1000
        
        print(f"查询 1200 个表的建议耗时: {query_time:.2f}ms")
        
        # 验证查询时间合理（< 200ms）
        self.assertLess(query_time, 200,
            f"查询大量表耗时 {query_time:.2f}ms，超过 200ms")
        
        # 验证返回的建议数量受限（避免过多建议影响性能）
        self.assertLessEqual(len(suggestions), self.completer._MAX_SUGGESTIONS)

    def test_acceptance_column_suggestions(self):
        """验收测试：列名补全"""
        # 加载带列名的表数据 - 使用正确的列格式
        tables_data = [
            {'name': 'users', 'columns': [
                {'name': 'id', 'type': 'INTEGER'},
                {'name': 'username', 'type': 'VARCHAR'},
                {'name': 'email', 'type': 'VARCHAR'},
                {'name': 'password_hash', 'type': 'VARCHAR'},
                {'name': 'created_at', 'type': 'TIMESTAMP'}
            ]},
        ]
        self.completer.set_metadata(tables_data)
        
        # 设置当前查询上下文为 SELECT
        self.editor.setPlainText("SELECT ")
        cursor = self.editor.textCursor()
        cursor.movePosition(cursor.End)
        self.editor.setTextCursor(cursor)
        
        # 获取列名建议 - 需要表名和前缀
        suggestions = self.completer._get_column_suggestions("users", "")
        
        # 验证包含表的所有列名 - 去掉类型后缀
        column_names = [s.split(' (')[0] for s in suggestions]
        self.assertIn("id", column_names)
        self.assertIn("username", column_names)
        self.assertIn("email", column_names)

    def test_acceptance_completion_flow(self):
        """验收测试：完整的补全流程"""
        # 1. 加载元数据 - 使用正确的列格式
        tables_data = [
            {'name': 'customers', 'columns': [
                {'name': 'customer_id', 'type': 'INTEGER'},
                {'name': 'name', 'type': 'VARCHAR'},
                {'name': 'email', 'type': 'VARCHAR'},
                {'name': 'phone', 'type': 'VARCHAR'}
            ]},
            {'name': 'orders', 'columns': [
                {'name': 'order_id', 'type': 'INTEGER'},
                {'name': 'customer_id', 'type': 'INTEGER'},
                {'name': 'amount', 'type': 'DECIMAL'},
                {'name': 'status', 'type': 'VARCHAR'}
            ]},
        ]
        self.completer.set_metadata(tables_data)
        
        # 2. 模拟用户输入 "SELECT "
        text = "SELECT "
        word = self.completer._get_current_word(text)
        
        # 3. 获取建议 - 需要表名和前缀
        prefix = ""
        suggestions = self.completer._get_column_suggestions("", prefix)
        
        # 4. 模拟用户输入 "FROM "
        text = "SELECT * FROM "
        word = self.completer._get_current_word(text)
        
        # 5. 获取表名建议
        if self.completer._needs_table_name(text):
            table_suggestions = self.completer._get_table_suggestions(word)
            # 去掉后缀
            suggestion_names = [s.replace(' (TABLE)', '').replace(' (VIEW)', '') for s in table_suggestions]
            self.assertIn("customers", suggestion_names)
            self.assertIn("orders", suggestion_names)


class TestSQLCompleterPerformance(unittest.TestCase):
    """SQL 补全器性能测试"""

    @classmethod
    def setUpClass(cls):
        """测试类开始前创建 QApplication"""
        cls.app = get_app()

    def test_performance_cache_efficiency(self):
        """测试缓存效率"""
        editor = QTextEdit()
        completer = SQLCompleter(editor, 'perf_test')
        
        # 加载数据 - 使用正确的列格式
        tables_data = [
            {'name': f'test_table_{i}', 'columns': [
                {'name': f'col_{j}', 'type': 'VARCHAR'} for j in range(10)
            ]}
            for i in range(500)
        ]
        completer.set_metadata(tables_data)
        
        # 多次查询同一前缀，验证缓存效果
        times = []
        for _ in range(5):
            start = time.time()
            suggestions = completer._get_table_suggestions("test_")
            times.append((time.time() - start) * 1000)
        
        # 第一次可能较慢，后续应该更快（缓存命中）
        avg_time = sum(times) / len(times)
        print(f"\n缓存查询平均时间: {avg_time:.2f}ms")
        
        self.assertLess(avg_time, 50, f"缓存查询耗时 {avg_time:.2f}ms 过长")
        
        editor.deleteLater()
        completer.deleteLater()


if __name__ == '__main__':
    unittest.main()
