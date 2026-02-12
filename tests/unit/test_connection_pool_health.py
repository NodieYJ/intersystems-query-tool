#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
连接池健康检查测试

验证连接池的连接健康检查和自动清理功能
"""

import sys
import time
import unittest
from unittest.mock import Mock, MagicMock

sys.path.insert(0, 'D:\\pywindows')


class TestConnectionPoolHealth(unittest.TestCase):
    """连接池健康检查测试"""
    
    def setUp(self):
        """设置测试环境"""
        from src.data.repositories.database_repository import ConnectionPool
        self.pool = ConnectionPool(max_connections=3, timeout=2)  # 2秒超时便于测试
    
    def test_connection_health_check(self):
        """测试连接健康检查"""
        # 创建模拟连接
        mock_conn = Mock()
        mock_conn.is_connected.return_value = True
        
        # 健康的连接应该返回True
        is_healthy = self.pool._is_connection_healthy(mock_conn)
        self.assertTrue(is_healthy)

        # 断开的连接应该返回False
        mock_conn.is_connected.return_value = False
        is_healthy = self.pool._is_connection_healthy(mock_conn)
        self.assertFalse(is_healthy)
    
    def test_connection_expiry(self):
        """测试连接过期检测"""
        mock_conn = Mock()
        
        # 添加连接（使用列表结构）
        from datetime import datetime, timedelta
        self.pool.connections.append([mock_conn, None, {}, datetime.now() - timedelta(seconds=10)])
        
        # 检查过期（超时设置为2秒）
        expired = self.pool._get_expired_connections()
        self.assertEqual(len(expired), 1)
    
    def test_auto_cleanup_expired_connections(self):
        """测试自动清理过期连接"""
        mock_conn = Mock()
        
        from datetime import datetime, timedelta
        # 添加过期连接
        self.pool.connections.append([mock_conn, None, {}, datetime.now() - timedelta(seconds=10)])

        # 执行清理
        cleaned_count = self.pool.cleanup_expired_connections()

        # 验证连接已关闭并移除
        mock_conn.close.assert_called_once()
        self.assertEqual(len(self.pool.connections), 0)
        self.assertEqual(cleaned_count, 1)
    
    def test_release_closes_unhealthy_connection(self):
        """测试释放时关闭不健康连接"""
        mock_conn = Mock()
        mock_conn.is_connected.return_value = False  # 不健康
        
        from datetime import datetime
        # 添加连接
        self.pool.connections.append([mock_conn, None, {}, datetime.now()])
        
        # 释放连接
        self.pool.release_connection(mock_conn)
        
        # 不健康连接应该被关闭
        mock_conn.close.assert_called_once()
        self.assertEqual(len(self.pool.connections), 0)
    
    def test_no_cleanup_for_fresh_connections(self):
        """测试不会清理新鲜连接"""
        mock_conn = Mock()
        
        from datetime import datetime
        # 添加新鲜连接（刚刚创建）
        self.pool.connections.append([mock_conn, None, {}, datetime.now()])

        # 执行清理
        cleaned_count = self.pool.cleanup_expired_connections()
        
        # 不应该清理
        mock_conn.close.assert_not_called()
        self.assertEqual(len(self.pool.connections), 1)
        self.assertEqual(cleaned_count, 0)


if __name__ == "__main__":
    unittest.main()
