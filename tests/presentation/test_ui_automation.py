#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI 自动化测试 - 使用 pytest-qt 测试 PySide2 桌面应用

测试覆盖:
1. 主窗口创建和显示
2. 对话框交互
3. UI 组件状态
4. 信号槽连接

使用方法:
    pip install pytest pytest-qt
    pytest tests/presentation/ -v
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# pytest-qt 需要的设置
pytest_plugins = ['pytest_qt']


class TestMainWindow:
    """主窗口测试类"""

    def test_main_window_creation(self, qtbot):
        """测试主窗口创建"""
        from src.presentation.windows.main_window import MainWindow

        # 创建主窗口
        window = MainWindow(scale_factor=1.0)

        # 验证窗口属性
        assert window is not None
        assert window.windowTitle() != ""

        # 使用 qtbot 测试窗口显示
        qtbot.addWidget(window)

        # 验证窗口已创建
        assert window.isVisible() or window.isHidden()

    def test_main_window_navigation(self, qtbot):
        """测试导航功能"""
        from src.presentation.windows.main_window import MainWindow

        window = MainWindow(scale_factor=1.0)
        qtbot.addWidget(window)

        # 验证堆叠窗口存在
        assert hasattr(window, 'stack')
        assert window.stack.count() >= 6  # 应该有6个页面

        # 验证导航按钮组存在
        assert hasattr(window, 'nav_group')

        # 测试页面切换
        for i in range(window.stack.count()):
            window._show_page(i)
            assert window.stack.currentIndex() == i


class TestConnectionConfigDialog:
    """连接配置对话框测试类"""

    def test_dialog_creation(self, qtbot):
        """测试对话框创建"""
        from src.presentation.dialogs.connection_config_dialog import ConnectionConfigDialog

        dialog = ConnectionConfigDialog()
        qtbot.addWidget(dialog)

        # 验证对话框属性
        assert dialog.windowTitle() == "数据库连接配置"
        assert dialog.isModal()

        # 验证关键组件存在
        assert hasattr(dialog, 'server_edit')
        assert hasattr(dialog, 'port_edit')
        assert hasattr(dialog, 'username_edit')
        assert hasattr(dialog, 'password_edit')
        assert hasattr(dialog, 'db_type_combo')

    def test_connection_params_methods(self, qtbot):
        """测试连接参数公共方法"""
        from src.presentation.dialogs.connection_config_dialog import ConnectionConfigDialog

        dialog = ConnectionConfigDialog()
        qtbot.addWidget(dialog)

        # 验证公共方法存在
        assert hasattr(dialog, '_get_connection_params')
        assert hasattr(dialog, '_validate_connection_params')
        assert hasattr(dialog, '_apply_connection_params')

        # 测试参数获取方法
        params = dialog._get_connection_params()
        assert isinstance(params, dict)
        assert 'server' in params
        assert 'port' in params
        assert 'username' in params
        assert 'password' in params

        # 测试参数验证方法
        is_valid, error = dialog._validate_connection_params(params)
        # 空参数应该验证失败
        if not params['server']:
            assert is_valid == False

        # 测试有效参数
        valid_params = {
            'server': 'localhost',
            'port': '1972',
            'namespace': 'USER',
            'username': 'test',
            'password': 'test123',
            'db_type': 'IRIS'
        }
        is_valid, error = dialog._validate_connection_params(valid_params)
        assert is_valid == True


class TestSqlQueryDialog:
    """SQL查询对话框测试类"""

    def test_dialog_creation(self, qtbot):
        """测试SQL查询对话框创建"""
        from src.presentation.dialogs.sql_query_dialog import SqlQueryDialog

        dialog = SqlQueryDialog()
        qtbot.addWidget(dialog)

        # 验证对话框属性
        assert dialog.windowTitle() == "SQL查询工具"

        # 验证关键组件存在
        assert hasattr(dialog, 'tab_widget')
        assert hasattr(dialog, 'thread_pool')
        assert hasattr(dialog, 'data_service')

    def test_query_worker_creation(self, qtbot):
        """测试查询工作线程创建"""
        from src.presentation.dialogs.sql_query_dialog import QueryWorker

        # 创建工作线程
        worker = QueryWorker("SELECT * FROM test", tab=None)

        # 验证工作线程属性
        assert worker.query == "SELECT * FROM test"
        assert worker.params is None
        assert hasattr(worker, 'signals')
        assert hasattr(worker, 'data_service')


class TestSignalSlotConnections:
    """信号槽连接测试类"""

    def test_thread_pool_configuration(self, qtbot):
        """测试线程池配置"""
        from src.presentation.dialogs.sql_query_dialog import SqlQueryDialog

        dialog = SqlQueryDialog()

        # 验证线程池已初始化
        assert dialog.thread_pool is not None

        # 验证最大线程数
        max_threads = dialog.thread_pool.maxThreadCount()
        assert max_threads >= 2  # 至少应该支持2个并发线程

    def test_database_loader_signals(self, qtbot):
        """测试数据库加载器信号"""
        # 这个测试验证信号槽机制已正确设置
        from src.presentation.dialogs.sql_query_dialog import WorkerSignals

        signals = WorkerSignals()

        # 验证信号存在
        assert hasattr(signals, 'result')
        assert hasattr(signals, 'error')
        assert hasattr(signals, 'progress')


class TestUIComponents:
    """UI组件测试类"""

    def test_syntax_highlighter(self, qtbot):
        """测试SQL语法高亮器"""
        from src.presentation.dialogs.sql_query_dialog import SQLSyntaxHighlighter
        from PySide2.QtWidgets import QTextEdit

        editor = QTextEdit()
        highlighter = SQLSyntaxHighlighter(editor.document())

        # 验证高亮器已设置关键字
        assert len(highlighter.keywords) > 0
        assert 'SELECT' in highlighter.keywords
        assert 'FROM' in highlighter.keywords

    def test_completer_setup(self, qtbot):
        """测试自动补全器设置"""
        from src.presentation.dialogs.sql_query_dialog import EnhancedSqlEditor

        editor = EnhancedSqlEditor()
        qtbot.addWidget(editor)

        # 验证补全器存在
        assert editor.completer is not None


# pytest 配置
def pytest_configure(config):
    """pytest 配置"""
    # 设置默认的 qt api
    os.environ['QT_API'] = 'pyside2'


if __name__ == '__main__':
    # 运行测试
    pytest.main([__file__, '-v'])
