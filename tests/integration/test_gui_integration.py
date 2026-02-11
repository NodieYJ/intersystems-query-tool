#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GUI 集成测试模块

测试关键用户操作流程，确保 UI 功能正常
"""

import unittest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.abspath('D:\\pywindows'))

from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt, QTimer
from PySide2.QtTest import QTest

# 创建 QApplication 实例（如果不存在）
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestMainWindow(unittest.TestCase):
    """
    主窗口集成测试类
    
    测试主窗口的创建和基本功能
    """
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.app = app
        print("\n=== 开始主窗口集成测试 ===")
    
    def setUp(self):
        """每个测试前初始化"""
        # 延迟导入以避免初始化问题
        from src.presentation.windows.main_window import MainWindow
        self.window = MainWindow()
        self.window.show()
        QTimer.singleShot(100, lambda: None)  # 等待窗口显示
    
    def tearDown(self):
        """每个测试后清理"""
        if self.window:
            self.window.close()
    
    def test_main_window_creation(self):
        """测试主窗口创建"""
        print("测试: 主窗口创建")
        self.assertIsNotNone(self.window)
        self.assertTrue(self.window.isVisible())
        print("  [PASS] 主窗口创建成功")
    
    def test_main_window_title(self):
        """测试窗口标题"""
        print("测试: 窗口标题")
        title = self.window.windowTitle()
        self.assertIn("InterSystems", title)
        print(f"  [PASS] 窗口标题: {title}")
    
    def test_main_window_has_menu(self):
        """测试菜单栏存在"""
        print("测试: 菜单栏")
        menu_bar = self.window.menuBar()
        self.assertIsNotNone(menu_bar)
        print("  [PASS] 菜单栏存在")
    
    def test_main_window_has_toolbar(self):
        """测试工具栏存在"""
        print("测试: 工具栏")
        toolbars = self.window.findChildren(type(self.window.toolBar()))
        self.assertGreater(len(toolbars), 0)
        print(f"  [PASS] 找到 {len(toolbars)} 个工具栏")
    
    def test_main_window_has_statusbar(self):
        """测试状态栏存在"""
        print("测试: 状态栏")
        status_bar = self.window.statusBar()
        self.assertIsNotNone(status_bar)
        print("  [PASS] 状态栏存在")


class TestSqlQueryDialog(unittest.TestCase):
    """
    SQL 查询对话框集成测试类
    
    测试 SQL 查询对话框的功能
    """
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.app = app
        print("\n=== 开始 SQL 查询对话框集成测试 ===")
    
    def test_sql_dialog_creation(self):
        """测试 SQL 对话框创建"""
        print("测试: SQL 查询对话框创建")
        from src.presentation.dialogs.sql_query_dialog import SqlQueryDialog
        
        dialog = SqlQueryDialog()
        self.assertIsNotNone(dialog)
        dialog.close()
        print("  [PASS] SQL 对话框创建成功")
    
    def test_sql_dialog_has_sql_editor(self):
        """测试 SQL 编辑器存在"""
        print("测试: SQL 编辑器")
        from src.presentation.dialogs.sql_query_dialog import SqlQueryDialog
        
        dialog = SqlQueryDialog()
        # 检查 SQL 编辑器区域
        self.assertTrue(dialog.sql_edit is not None or hasattr(dialog, 'sql_editor'))
        dialog.close()
        print("  [PASS] SQL 编辑器存在")
    
    def test_sql_dialog_has_result_area(self):
        """测试结果区域存在"""
        print("测试: 结果区域")
        from src.presentation.dialogs.sql_query_dialog import SqlQueryDialog
        
        dialog = SqlQueryDialog()
        # 检查结果表格
        self.assertTrue(dialog.result_table is not None)
        dialog.close()
        print("  [PASS] 结果表格存在")


class TestLogDialog(unittest.TestCase):
    """
    日志对话框集成测试类
    
    测试日志对话框的功能
    """
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.app = app
        print("\n=== 开始日志对话框集成测试 ===")
    
    def test_log_dialog_creation(self):
        """测试日志对话框创建"""
        print("测试: 日志对话框创建")
        from src.presentation.dialogs.log_dialog import LogDialog
        
        dialog = LogDialog()
        self.assertIsNotNone(dialog)
        dialog.close()
        print("  [PASS] 日志对话框创建成功")
    
    def test_log_dialog_has_search(self):
        """测试搜索功能"""
        print("测试: 搜索功能")
        from src.presentation.dialogs.log_dialog import LogDialog
        
        dialog = LogDialog()
        self.assertTrue(hasattr(dialog, 'search_edit') or hasattr(dialog, 'search_input'))
        dialog.close()
        print("  [PASS] 搜索输入框存在")


class TestDataAnalysisDialog(unittest.TestCase):
    """
    数据分析对话框集成测试类
    
    测试数据分析对话框的功能
    """
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.app = app
        print("\n=== 开始数据分析对话框集成测试 ===")
    
    def test_data_analysis_dialog_creation(self):
        """测试数据分析对话框创建"""
        print("测试: 数据分析对话框创建")
        from src.presentation.dialogs.data_analysis_dialog import DataAnalysisDialog
        
        dialog = DataAnalysisDialog()
        self.assertIsNotNone(dialog)
        dialog.close()
        print("  [PASS] 数据分析对话框创建成功")
    
    def test_data_analysis_has_load_tab(self):
        """测试数据加载标签页"""
        print("测试: 数据加载标签页")
        from src.presentation.dialogs.data_analysis_dialog import DataAnalysisDialog
        
        dialog = DataAnalysisDialog()
        self.assertTrue(hasattr(dialog, 'data_load_widget') or hasattr(dialog, 'tab_widget'))
        dialog.close()
        print("  [PASS] 数据加载功能存在")


class TestConnectionConfigDialog(unittest.TestCase):
    """
    连接配置对话框集成测试类
    
    测试连接配置对话框的功能
    """
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.app = app
        print("\n=== 开始连接配置对话框集成测试 ===")
    
    def test_connection_config_dialog_creation(self):
        """测试连接配置对话框创建"""
        print("测试: 连接配置对话框创建")
        from src.presentation.dialogs.connection_config_dialog import ConnectionConfigDialog
        
        dialog = ConnectionConfigDialog()
        self.assertIsNotNone(dialog)
        dialog.close()
        print("  [PASS] 连接配置对话框创建成功")
    
    def test_connection_config_has_server_input(self):
        """测试服务器输入框"""
        print("测试: 服务器输入")
        from src.presentation.dialogs.connection_config_dialog import ConnectionConfigDialog
        
        dialog = ConnectionConfigDialog()
        self.assertTrue(hasattr(dialog, 'server_input') or hasattr(dialog, 'host_input'))
        dialog.close()
        print("  [PASS] 服务器输入框存在")


class TestQueryHistoryDialog(unittest.TestCase):
    """
    查询历史对话框集成测试类
    
    测试查询历史对话框的功能
    """
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.app = app
        print("\n=== 开始查询历史对话框集成测试 ===")
    
    def test_query_history_dialog_creation(self):
        """测试查询历史对话框创建"""
        print("测试: 查询历史对话框创建")
        from src.presentation.dialogs.query_history_dialog import QueryHistoryDialog
        
        dialog = QueryHistoryDialog()
        self.assertIsNotNone(dialog)
        dialog.close()
        print("  [PASS] 查询历史对话框创建成功")
    
    def test_query_history_has_history_list(self):
        """测试历史列表"""
        print("测试: 历史列表")
        from src.presentation.dialogs.query_history_dialog import QueryHistoryDialog
        
        dialog = QueryHistoryDialog()
        self.assertTrue(hasattr(dialog, 'history_list') or hasattr(dialog, 'history_widget'))
        dialog.close()
        print("  [PASS] 历史列表存在")


def run_integration_tests():
    """
    运行所有集成测试
    
    Returns:
        bool: 所有测试是否通过
    """
    print("=" * 60)
    print("GUI 集成测试套件")
    print("=" * 60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestMainWindow))
    suite.addTests(loader.loadTestsFromTestCase(TestSqlQueryDialog))
    suite.addTests(loader.loadTestsFromTestCase(TestLogDialog))
    suite.addTests(loader.loadTestsFromTestCase(TestDataAnalysisDialog))
    suite.addTests(loader.loadTestsFromTestCase(TestConnectionConfigDialog))
    suite.addTests(loader.loadTestsFromTestCase(TestQueryHistoryDialog))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出结果摘要
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)
    print(f"测试总数: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped)}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\n总体结果: {'[PASS]' if success else '[FAIL]'}")
    print("=" * 60)
    
    return success


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
