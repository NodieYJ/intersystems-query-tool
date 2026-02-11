#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
参数化查询测试

验证新的execute_query_safe方法使用参数化查询防止SQL注入
"""

import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, 'D:\\pywindows')


class TestParameterizedQuery(unittest.TestCase):
    """参数化查询测试"""
    
    def test_execute_query_with_params(self):
        """测试带参数的执行方法"""
        from src.infrastructure.security.security_utils import SecurityUtils
        
        security = SecurityUtils()
        
        # 模拟数据库连接
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        # 设置模拟返回值
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchall.return_value = [(1, "admin")]
        
        # 测试参数化查询
        query = "SELECT * FROM users WHERE id = ? AND name = ?"
        params = (1, "admin")
        
        result = security.execute_query_safe(mock_conn, query, params)
        
        # 验证使用了参数化查询
        mock_cursor.execute.assert_called_once_with(query, params)
        self.assertTrue(result)
        self.assertEqual(result, [{"id": 1, "name": "admin"}])
    
    def test_sql_injection_prevention(self):
        """测试SQL注入防护"""
        from src.infrastructure.security.security_utils import SecurityUtils
        
        security = SecurityUtils()
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        # 设置模拟返回值
        mock_cursor.description = [("id",)]
        mock_cursor.fetchall.return_value = [(1,)]
        
        # 尝试SQL注入
        malicious_input = "1 OR 1=1"
        query = "SELECT * FROM users WHERE id = ?"
        
        result = security.execute_query_safe(mock_conn, query, (malicious_input,))
        
        # 参数应该被正确转义，不会执行恶意代码
        mock_cursor.execute.assert_called_once_with(query, (malicious_input,))
        self.assertIsNotNone(result)  # 返回结果不为None
        self.assertEqual(len(result), 1)
    
    def test_deprecated_sanitize_warning(self):
        """测试旧方法已弃用并发出警告"""
        import warnings
        from src.infrastructure.security.security_utils import sanitize_sql_input
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = sanitize_sql_input("test'; DROP TABLE users; --")
            
            # 应该发出弃用警告
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[0].category, DeprecationWarning))


if __name__ == "__main__":
    unittest.main()
