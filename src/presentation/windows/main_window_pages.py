#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主窗口页面模块

包含6个功能页面的创建
采用引用模式与主窗口协作，避免强耦合
"""

import logging
from typing import TYPE_CHECKING

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QVBoxLayout, QWidget, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QTextEdit, QSplitter, QProgressBar, QFileDialog,
    QComboBox, QCheckBox, QLineEdit, QTabWidget, QListWidget
)

if TYPE_CHECKING:
    from src.presentation.windows.main_window import MainWindow

logger = logging.getLogger(__name__)


# 颜色系统
COLORS = {
    'primary': '#2563EB',
    'primary_hover': '#1D4ED8',
    'primary_light': '#DBEAFE',
    'secondary': '#3B82F6',
    'success': '#10B981',
    'warning': '#F59E0B',
    'error': '#EF4444',
    'info': '#3B82F6',
    'background': '#F8FAFC',
    'surface': '#FFFFFF',
    'border': '#E2E8F0',
    'divider': '#F1F5F9',
    'text_primary': '#1E293B',
    'text_secondary': '#64748B',
    'text_disabled': '#94A3B8',
    'text_inverse': '#FFFFFF',
}


class MainWindowPages:
    """
    主窗口页面创建类

    负责创建6个功能页面，通过引用主窗口访问必要的属性和方法
    这种设计允许页面创建逻辑与主窗口解耦，同时保持功能完整
    """

    def __init__(self, main_window: 'MainWindow'):
        """
        初始化页面创建类

        Args:
            main_window: 主窗口实例，用于访问缩放方法、组件方法和事件处理
        """
        self.main_window = main_window
        self.scaled = main_window.scaled
        self.components = main_window.components

    def _create_overview_page(self) -> QWidget:
        """创建概览页面 - UI/UX Pro Max 设计"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(self.scaled(24), self.scaled(24), self.scaled(24), self.scaled(24))  # type: ignore
        layout.setSpacing(0)  # type: ignore

        # 页面标题
        title = QLabel('📊 数据概览')
        title.setObjectName('page_title')
        layout.addWidget(title)

        subtitle = QLabel('欢迎使用数据查询分析工具，快速查看系统状态和最近活动')
        subtitle.setObjectName('page_subtitle')
        layout.addWidget(subtitle)

        # 统计卡片
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setSpacing(self.scaled(16))  # type: ignore

        stats = [
            ('数据库连接', '3', '活跃连接'),
            ('今日查询', '127', '次执行'),
            ('数据导出', '15', '次下载'),
            ('存储空间', '2.3 GB', '已使用'),
        ]

        for title_text, value, subtitle_text in stats:
            card = self.components._create_stat_card(title_text, value, subtitle_text)
            stats_layout.addWidget(card)

        layout.addWidget(stats_widget)

        # 快速操作卡片
        card = QGroupBox('⚡ 快速操作')
        card_layout = QHBoxLayout(card)

        btn_sql = QPushButton('📝 新建 SQL 查询')
        btn_sql.setObjectName('btn_primary')
        btn_sql.clicked.connect(lambda: self.main_window._show_page(1))  # type: ignore
        card_layout.addWidget(btn_sql)

        btn_download = QPushButton('⬇️ 数据导出')
        btn_download.setObjectName('btn_secondary')
        btn_download.clicked.connect(lambda: self.main_window._show_page(2))  # type: ignore
        card_layout.addWidget(btn_download)

        btn_analysis = QPushButton('📈 数据分析')
        btn_analysis.setObjectName('btn_secondary')
        btn_analysis.clicked.connect(lambda: self.main_window._show_page(3))  # type: ignore
        card_layout.addWidget(btn_analysis)

        card_layout.addStretch()
        layout.addWidget(card)

        # 最近活动卡片
        card = QGroupBox('🕐 最近活动')
        card_layout = QVBoxLayout(card)

        activities = [
            ('✅', 'SQL 查询执行成功', 'SELECT * FROM users', '2 分钟前'),
            ('✅', '数据导出完成', 'users_20240115.csv', '15 分钟前'),
            ('⚠️', '查询执行警告', '连接超时，已重试', '1 小时前'),
            ('✅', '数据库连接成功', 'MySQL (localhost:3306)', '2 小时前'),
        ]

        for icon, title_text, desc, time_text in activities:
            item = self.components._create_activity_item(icon, title_text, desc, time_text)
            card_layout.addWidget(item)

            # 添加分隔线（除了最后一个）
            if icon != activities[-1][0]:
                line = QFrame()
                line.setFrameShape(QFrame.HLine)  # type: ignore
                line.setStyleSheet(f'background-color: {COLORS["divider"]}; max-height: 1px;')  # type: ignore
                card_layout.addWidget(line)

        layout.addWidget(card)
        layout.addStretch()

        # 包装在滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        scroll.setFrameShape(QFrame.NoFrame)  # type: ignore

        return scroll

    def _create_sql_query_page(self) -> QWidget:
        """创建 SQL 查询页面 - UI/UX Pro Max 设计"""
        from src.presentation.dialogs.sql_query_dialog import SQLQueryDialog

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(self.scaled(24), self.scaled(24), self.scaled(24), self.scaled(24))  # type: ignore
        layout.setSpacing(0)  # type: ignore

        # 页面标题
        title = QLabel('📝 SQL 查询')
        title.setObjectName('page_title')
        layout.addWidget(title)

        subtitle = QLabel('编写和执行 SQL 查询语句，支持语法高亮和智能提示')
        subtitle.setObjectName('page_subtitle')
        layout.addWidget(subtitle)

        # SQL编辑器
        editor_card = QGroupBox('SQL 编辑器')
        editor_layout = QVBoxLayout(editor_card)

        self.main_window.sql_editor = QTextEdit()
        self.main_window.sql_editor.setObjectName('sql_editor')
        self.main_window.sql_editor.setPlaceholderText('-- 在此输入 SQL 查询语句\n-- 例如: SELECT * FROM users LIMIT 10')
        editor_layout.addWidget(self.main_window.sql_editor)

        # 按钮栏
        btn_layout = QHBoxLayout()

        btn_execute = QPushButton('▶️ 执行查询')
        btn_execute.setObjectName('btn_primary')
        btn_execute.clicked.connect(self.main_window._execute_query)
        btn_layout.addWidget(btn_execute)

        btn_clear = QPushButton('🗑️ 清空')
        btn_clear.setObjectName('btn_secondary')
        btn_clear.clicked.connect(self.main_window._clear_query)
        btn_layout.addWidget(btn_clear)

        btn_export = QPushButton('📥 导出结果')
        btn_export.setObjectName('btn_secondary')
        btn_export.clicked.connect(self.main_window._export_query_result)
        btn_layout.addWidget(btn_export)

        btn_layout.addStretch()
        editor_layout.addLayout(btn_layout)

        layout.addWidget(editor_card)

        # 结果显示区域
        result_card = QGroupBox('查询结果')
        result_layout = QVBoxLayout(result_card)

        self.main_window.result_table = QTableWidget()
        self.main_window.result_table.setObjectName('result_table')
        self.main_window.result_table.setColumnCount(0)
        self.main_window.result_table.setRowCount(0)
        self.main_window.result_table.setHorizontalHeaderLabels([])
        result_layout.addWidget(self.main_window.result_table)

        layout.addWidget(result_card)

        return page

    def _create_data_download_page(self) -> QWidget:
        """创建数据下载页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(self.scaled(24), self.scaled(24), self.scaled(24), self.scaled(24))  # type: ignore

        # 页面标题
        title = QLabel('⬇️ 数据导出')
        title.setObjectName('page_title')
        layout.addWidget(title)

        subtitle = QLabel('将查询结果导出为 Excel、CSV 或 JSON 格式')
        subtitle.setObjectName('page_subtitle')
        layout.addWidget(subtitle)

        # 导出配置
        config_card = QGroupBox('导出配置')
        config_layout = QVBoxLayout(config_card)

        # 格式选择
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel('导出格式:'))
        self.main_window.export_format = QComboBox()
        self.main_window.export_format.addItems(['Excel (.xlsx)', 'CSV (.csv)', 'JSON (.json)'])
        format_layout.addWidget(self.main_window.export_format)
        format_layout.addStretch()
        config_layout.addLayout(format_layout)

        # 文件名
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel('文件名:'))
        self.main_window.export_filename = QLineEdit()
        self.main_window.export_filename.setPlaceholderText('export_data')
        file_layout.addWidget(self.main_window.export_filename)
        btn_browse = QPushButton('浏览...')
        btn_browse.clicked.connect(lambda: self._browse_export_path())
        file_layout.addWidget(btn_browse)
        config_layout.addLayout(file_layout)

        layout.addWidget(config_card)

        # 开始导出按钮
        btn_start = QPushButton('🚀 开始导出')
        btn_start.setObjectName('btn_primary')
        btn_start.clicked.connect(self.main_window._start_download)
        layout.addWidget(btn_start)

        layout.addStretch()

        return page

    def _browse_export_path(self):
        """浏览导出路径"""
        path = QFileDialog.getExistingDirectory(self.main_window, '选择导出目录')
        if path:
            self.main_window.export_path = path

    def _create_data_analysis_page(self) -> QWidget:
        """创建数据分析页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(self.scaled(24), self.scaled(24), self.scaled(24), self.scaled(24))  # type: ignore

        # 页面标题
        title = QLabel('📈 数据分析')
        title.setObjectName('page_title')
        layout.addWidget(title)

        subtitle = QLabel('对查询结果进行统计分析和可视化')
        subtitle.setObjectName('page_subtitle')
        layout.addWidget(subtitle)

        # 分析配置
        analysis_card = QGroupBox('分析配置')
        analysis_layout = QVBoxLayout(analysis_card)

        # 分析类型
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel('分析类型:'))
        self.main_window.analysis_type = QComboBox()
        self.main_window.analysis_type.addItems(['描述统计', '趋势分析', '分布分析', '相关性分析'])
        type_layout.addWidget(self.main_window.analysis_type)
        type_layout.addStretch()
        analysis_layout.addLayout(type_layout)

        layout.addWidget(analysis_card)

        # 结果显示区域
        result_card = QGroupBox('分析结果')
        result_layout = QVBoxLayout(result_card)

        self.main_window.analysis_result = QTextEdit()
        self.main_window.analysis_result.setReadOnly(True)
        result_layout.addWidget(self.main_window.analysis_result)

        layout.addWidget(result_card)

        layout.addStretch()

        return page

    def _create_history_page(self) -> QWidget:
        """创建查询历史页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(self.scaled(24), self.scaled(24), self.scaled(24), self.scaled(24))  # type: ignore

        # 页面标题
        title = QLabel('🕐 查询历史')
        title.setObjectName('page_title')
        layout.addWidget(title)

        subtitle = QLabel('查看和管理历史查询记录')
        subtitle.setObjectName('page_subtitle')
        layout.addWidget(subtitle)

        # 操作按钮
        btn_layout = QHBoxLayout()

        btn_refresh = QPushButton('🔄 刷新')
        btn_refresh.setObjectName('btn_secondary')
        btn_refresh.clicked.connect(lambda: self._refresh_history())
        btn_layout.addWidget(btn_refresh)

        btn_clear = QPushButton('🗑️ 清空历史')
        btn_clear.setObjectName('btn_secondary')
        btn_clear.clicked.connect(self.main_window._clear_history)
        btn_layout.addWidget(btn_clear)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 历史记录列表
        history_card = QGroupBox('历史记录')
        history_layout = QVBoxLayout(history_card)

        self.main_window.history_list = QListWidget()
        history_layout.addWidget(self.main_window.history_list)

        layout.addWidget(history_card)

        layout.addStretch()

        return page

    def _refresh_history(self):
        """刷新历史记录"""
        # 从查询历史管理器加载记录
        if hasattr(self.main_window, 'query_history_manager'):
            records = self.main_window.query_history_manager.get_recent_queries(limit=50)
            self.main_window.history_list.clear()
            for record in records:
                item_text = f"{record['timestamp']} - {record['sql'][:50]}..."
                self.main_window.history_list.addItem(item_text)

    def _create_settings_page(self) -> QWidget:
        """创建设置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(self.scaled(24), self.scaled(24), self.scaled(24), self.scaled(24))  # type: ignore

        # 页面标题
        title = QLabel('⚙️ 系统设置')
        title.setObjectName('page_title')
        layout.addWidget(title)

        subtitle = QLabel('配置应用程序和数据库连接')
        subtitle.setObjectName('page_subtitle')
        layout.addWidget(subtitle)

        # 设置选项卡
        settings_tabs = QTabWidget()

        # 数据库设置
        db_tab = QWidget()
        db_layout = QVBoxLayout(db_tab)

        # 连接配置按钮
        btn_connection = QPushButton('🔌 数据库连接配置')
        btn_connection.setObjectName('btn_secondary')
        btn_connection.clicked.connect(self.main_window._show_connection_config)
        db_layout.addWidget(btn_connection)

        # 测试连接按钮
        btn_test = QPushButton('🧪 测试连接')
        btn_test.setObjectName('btn_secondary')
        btn_test.clicked.connect(self.main_window._test_connection)
        db_layout.addWidget(btn_test)

        db_layout.addStretch()
        settings_tabs.addTab(db_tab, '数据库')

        # 界面设置
        ui_tab = QWidget()
        ui_layout = QVBoxLayout(ui_tab)

        # 缩放设置
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel('界面缩放:'))
        self.main_window.scale_combo = QComboBox()
        self.main_window.scale_combo.addItems(['100%', '125%', '150%', '175%', '200%'])
        scale_layout.addWidget(self.main_window.scale_combo)
        ui_layout.addLayout(scale_layout)

        # 自动启动选项
        self.main_window.auto_connect_checkbox = QCheckBox('启动时自动连接数据库')
        ui_layout.addWidget(self.main_window.auto_connect_checkbox)

        ui_layout.addStretch()
        settings_tabs.addTab(ui_tab, '界面')

        layout.addWidget(settings_tabs)

        # 保存按钮
        btn_save = QPushButton('💾 保存设置')
        btn_save.setObjectName('btn_primary')
        btn_save.clicked.connect(self.main_window._save_settings)
        layout.addWidget(btn_save)

        layout.addStretch()

        return page
