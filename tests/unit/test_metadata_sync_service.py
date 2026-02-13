#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""MetadataSyncService 单元测试"""

import unittest
import os
import sys
from unittest.mock import Mock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from business.services.metadata_sync_service import MetadataSyncService


class TestMetadataSyncService(unittest.TestCase):
    """测试元数据同步服务"""

    def setUp(self):
        """设置测试"""
        self.mock_db_repo = Mock()
        self.mock_cache = Mock()
        self.sync_service = MetadataSyncService(self.mock_db_repo, self.mock_cache)

    def test_sync_metadata_success(self):
        """测试成功同步元数据"""
        # 模拟数据库返回的表列表
        self.mock_db_repo.get_all_tables.return_value = ['users', 'orders']
        
        # 模拟表列信息
        self.mock_db_repo.get_table_columns.side_effect = [
            [
                {'name': 'id', 'type': 'INT', 'ordinal_position': 1},
                {'name': 'name', 'type': 'VARCHAR', 'ordinal_position': 2}
            ],
            [
                {'name': 'order_id', 'type': 'INT', 'ordinal_position': 1},
                {'name': 'user_id', 'type': 'INT', 'ordinal_position': 2}
            ]
        ]
        
        # 执行同步
        result = self.sync_service.sync_metadata('test_conn')
        
        # 验证结果
        self.assertTrue(result)
        self.mock_cache.update_metadata.assert_called_once()
        
        # 验证传入的数据
        call_args = self.mock_cache.update_metadata.call_args
        self.assertEqual(call_args[0][0], 'test_conn')
        self.assertEqual(len(call_args[0][1]), 2)  # 2 个表

    def test_sync_metadata_empty_tables(self):
        """测试空表列表"""
        self.mock_db_repo.get_all_tables.return_value = []
        
        result = self.sync_service.sync_metadata('test_conn')
        
        self.assertTrue(result)
        self.mock_cache.update_metadata.assert_called_once()
        self.assertEqual(len(self.mock_cache.update_metadata.call_args[0][1]), 0)

    def test_sync_metadata_db_error(self):
        """测试数据库错误"""
        self.mock_db_repo.get_all_tables.side_effect = Exception("Connection failed")
        
        result = self.sync_service.sync_metadata('test_conn')
        
        self.assertFalse(result)
        self.mock_cache.update_metadata.assert_not_called()


if __name__ == '__main__':
    unittest.main()
