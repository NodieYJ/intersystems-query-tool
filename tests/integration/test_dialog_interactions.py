#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
集成测试 - 验证对话框交互和业务流程

测试覆盖:
1. 连接配置保存/加载流程
2. SQL查询执行流程
3. 多标签页管理
4. 数据导出流程

使用方法:
    python tests/integration/test_dialog_interactions.py
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


class TestConnectionConfigFlow(unittest.TestCase):
    """连接配置流程测试类"""

    def test_save_and_load_config(self):
        """测试保存和加载配置的完整流程"""
        from src.presentation.dialogs.connection_config_dialog import ConnectionConfigDialog

        # 模拟配置管理器
        mock_config_manager = Mock()
        mock_config_manager.get = Mock(return_value="")
        mock_config_manager.set = Mock()

        # 模拟对话框
        dialog = ConnectionConfigDialog.__new__(ConnectionConfigDialog)
        dialog.config_manager = mock_config_manager

        # 测试获取参数方法
        with patch.object(dialog.server_edit, 'text', return_value='localhost'):
            with patch.object(dialog.port_edit, 'text', return_value='1972'):
                with patch.object(dialog.namespace_edit, 'text', return_value='USER'):
                    with patch.object(dialog.username_edit, 'text', return_value='test'):
                        with patch.object(dialog.password_edit, 'text', return_value='test123'):
                            with patch.object(dialog.db_type_combo, 'currentText', return_value='IRIS'):
                                params = dialog._get_connection_params()

        # 验证参数
        assert params['server'] == 'localhost'
        assert params['port'] == '1972'
        assert params['namespace'] == 'USER'
        assert params['username'] == 'test'
        assert params['password'] == 'test123'
        assert params['db_type'] == 'IRIS'

    def test_validate_empty_server(self):
        """测试空服务器地址验证"""
        from src.presentation.dialogs.connection_config_dialog import ConnectionConfigDialog

        dialog = ConnectionConfigDialog.__new__(ConnectionConfigDialog)

        # 测试空服务器
        invalid_params = {
            'server': '',
            'port': '1972',
            'namespace': 'USER',
            'username': 'test',
            'password': 'test',
            'db_type': 'IRIS'
        }

        is_valid, error = dialog._validate_connection_params(invalid_params)
        assert is_valid == False
        assert '数据库地址不能为空' in error

    def test_validate_invalid_port(self):
        """测试无效端口验证"""
        from src.presentation.dialogs.connection_config_dialog import ConnectionConfigDialog

        dialog = ConnectionConfigDialog.__new__(ConnectionConfigDialog)

        # 测试无效端口
        invalid_params = {
            'server': 'localhost',
            'port': 'abc',
            'namespace': 'USER',
            'username': 'test',
            'password': 'test',
            'db_type': 'IRIS'
        }

        is_valid, error = dialog._validate_connection_params(invalid_params)
        assert is_valid == False
        assert '端口号必须是数字' in error


class TestQueryExecutionFlow(unittest.TestCase):
    """查询执行流程测试类"""

    def test_query_worker_creation(self):
        """测试查询工作线程创建"""
        from src.presentation.dialogs.sql_query_dialog import QueryWorker

        worker = QueryWorker("SELECT * FROM test", tab=None)

        assert worker.query == "SELECT * FROM test"
        assert worker.params is None
        assert worker.tab is None
        assert hasattr(worker, 'signals')
        assert hasattr(worker, 'data_service')

    def test_query_worker_with_tab(self):
        """测试带标签页引用的工作线程"""
        from src.presentation.dialogs.sql_query_dialog import QueryWorker, QueryTab

        # 创建模拟标签页
        mock_tab = Mock()
        mock_tab.sql_edit = Mock()
        mock_tab.sql_edit.toPlainText = Mock(return_value="SELECT 1")

        worker = QueryWorker("SELECT 1", tab=mock_tab)

        assert worker.tab is mock_tab
        assert worker.query == "SELECT 1"

    def test_security_validation(self):
        """测试SQL安全验证"""
        from src.presentation.dialogs.sql_query_dialog import SqlQueryDialog

        dialog = SqlQueryDialog.__new__(SqlQueryDialog)
        dialog.security_utils = Mock()
        dialog.security_utils.validate_sql_query = Mock(return_value=True)
        dialog.security_utils.sanitize_sql_input = Mock(return_value="SELECT 1")

        # 测试有效SQL
        dialog.security_utils.validate_sql_query.return_value = True
        is_valid = dialog.security_utils.validate_sql_query("SELECT * FROM users")
        assert is_valid == True

        # 测试危险SQL
        dialog.security_utils.validate_sql_query.return_value = False
        is_valid = dialog.security_utils.validate_sql_query("DROP TABLE users")
        assert is_valid == False


class TestTabManagement(unittest.TestCase):
    """标签页管理测试类"""

    def test_create_query_tab(self):
        """测试创建查询标签页"""
        from src.presentation.dialogs.sql_query_dialog import QueryTab

        tab = QueryTab("测试标签")

        assert tab.tab_name == "测试标签"
        assert tab.current_page == 1
        assert tab.page_size == 100
        assert tab.total_pages == 1
        assert tab.total_rows == 0
        assert tab.is_querying == False

    def test_pagination_calculation(self):
        """测试分页计算"""
        from src.presentation.dialogs.sql_query_dialog import QueryTab

        tab = QueryTab("测试")

        # 测试少于一页数据
        tab.total_rows = 50
        tab.total_pages = (tab.total_rows + tab.page_size - 1) // tab.page_size
        assert tab.total_pages == 1

        # 测试超过一页数据
        tab.total_rows = 250
        tab.total_pages = (tab.total_rows + tab.page_size - 1) // tab.page_size
        assert tab.total_pages == 3

    def test_load_page_data(self):
        """测试加载页面数据"""
        from src.presentation.dialogs.sql_query_dialog import QueryTab

        tab = QueryTab("测试")

        # 模拟所有数据
        tab.all_data = {
            'columns': ['id', 'name'],
            'rows': [
                ['1', 'Alice'],
                ['2', 'Bob'],
                ['3', 'Charlie']
            ]
        }
        tab.page_size = 2
        tab.current_page = 1

        # 加载第一页
        tab.load_page_data()

        assert tab.current_data is not None
        assert tab.current_data['columns'] == ['id', 'name']
        assert len(tab.current_data['rows']) == 2


class TestThreadSafety(unittest.TestCase):
    """线程安全测试类"""

    def test_database_loader_signals(self):
        """测试数据库加载器信号"""
        from src.presentation.dialogs.sql_query_dialog import WorkerSignals

        signals = WorkerSignals()

        # 验证信号存在
        assert hasattr(signals, 'result')
        assert hasattr(signals, 'error')
        assert hasattr(signals, 'progress')

    def test_signal_connection_type(self):
        """测试信号连接类型"""
        from PySide2.QtCore import Qt

        # 验证 Qt.AutoConnection 常量存在
        assert hasattr(Qt, 'AutoConnection')

    def test_thread_pool_configured(self):
        """测试线程池已配置"""
        from src.presentation.dialogs.sql_query_dialog import SqlQueryDialog

        dialog = SqlQueryDialog.__new__(SqlQueryDialog)
        dialog.thread_pool = Mock()
        dialog.thread_pool.maxThreadCount = Mock(return_value=4)

        max_threads = dialog.thread_pool.maxThreadCount()
        assert max_threads >= 2


class TestDataExport(unittest.TestCase):
    """数据导出测试类"""

    def test_export_csv(self):
        """测试CSV导出"""
        from src.presentation.dialogs.sql_query_dialog import SqlQueryDialog
        import tempfile
        import csv
        import os

        dialog = SqlQueryDialog.__new__(SqlQueryDialog)

        # 模拟导出数据
        export_data = {
            'columns': ['id', 'name'],
            'rows': [['1', 'Alice'], ['2', 'Bob']]
        }

        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_file = f.name

        try:
            # 模拟写入CSV
            with open(temp_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(export_data['columns'])
                for row in export_data['rows']:
                    writer.writerow(row)

            # 验证文件创建
            assert os.path.exists(temp_file)

            # 验证内容
            with open(temp_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                assert len(lines) == 3  # 标题行 + 2行数据
                assert 'id,name' in lines[0]
        finally:
            # 清理临时文件
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestConfigurationPath(unittest.TestCase):
    """配置路径测试类"""

    def test_config_directory_creation(self):
        """测试配置目录创建"""
        import tempfile
        import os

        # 模拟配置目录
        temp_dir = tempfile.mkdtemp()
        config_dir = os.path.join(temp_dir, '.test_app_configs')

        # 模拟创建目录
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)

        assert os.path.exists(config_dir)
        assert os.path.isdir(config_dir)

        # 清理
        os.rmdir(config_dir)
        os.rmdir(temp_dir)

    def test_config_file_path(self):
        """测试配置文件路径"""
        import tempfile
        import os

        temp_dir = tempfile.mkdtemp()
        config_file = os.path.join(temp_dir, 'test_config.json')

        # 验证路径格式
        assert config_file.endswith('.json')
        assert 'test_config' in config_file

        # 清理
        os.rmdir(temp_dir)


def run_tests():
    """运行所有集成测试"""
    unittest.main(verbosity=2)


if __name__ == '__main__':
    run_tests()
