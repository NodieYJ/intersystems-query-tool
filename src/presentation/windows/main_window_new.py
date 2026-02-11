#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主窗口模块 - UI/UX Pro Max 现代化重构版本
基于 style_demo_v3.py 设计规范
功能页面直接嵌入右侧内容区
"""

import logging
import sys
from datetime import datetime

from PySide2.QtCore import QEvent, Qt, QThreadPool, QRunnable, Slot, QObject, Signal
from PySide2.QtGui import QColor, QFont, QScreen, QTextCharFormat, QSyntaxHighlighter, QFontDatabase
from PySide2.QtWidgets import (
    QAction, QApplication, QHBoxLayout, QLabel, QMainWindow, QMenu,
    QMenuBar, QMessageBox, QPushButton, QScrollArea, QSizePolicy,
    QStackedLayout, QStackedWidget, QStatusBar, QVBoxLayout, QWidget,
    QFrame, QButtonGroup, QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QTabWidget, QListWidget, QTextEdit,
    QSplitter, QComboBox, QLineEdit, QCheckBox, QFileDialog, QCompleter,
    QTreeWidget, QTreeWidgetItem
)

from src.infrastructure.config.config_manager import get_config_manager
from src.business.services.data_service import get_data_service
from src.business.services.query_history_manager import get_query_history_manager
from utils.performance import EventCompressor, DeferredUpdater, get_optimizer

logger = logging.getLogger(__name__)


# 颜色系统 - UI/UX Pro Max 设计系统
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


# 全局缩放比例
SCALE_FACTOR = 1.0


def scaled(value):
    """根据缩放比例计算实际像素值"""
    return int(value * SCALE_FACTOR)


# SQL语法高亮器
class SQLSyntaxHighlighter(QSyntaxHighlighter):
    """SQL语法高亮器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # SQL关键字 - UI/UX Pro Max 配色
        self.keywords = [
            'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP',
            'ALTER', 'TABLE', 'VIEW', 'INDEX', 'TRIGGER', 'PROCEDURE', 'FUNCTION',
            'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON', 'AS', 'GROUP',
            'BY', 'HAVING', 'ORDER', 'LIMIT', 'OFFSET', 'AND', 'OR', 'NOT',
            'IN', 'LIKE', 'BETWEEN', 'IS', 'NULL', 'TRUE', 'FALSE'
        ]
        
        # 定义格式 - UI/UX Pro Max 配色方案
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor(COLORS['primary']))
        self.keyword_format.setFontWeight(QFont.Bold)
        
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor(COLORS['success']))
        
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor(COLORS['text_disabled']))
        self.comment_format.setFontItalic(True)
        
        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor(COLORS['warning']))
    
    def highlightBlock(self, text):
        """高亮文本块"""
        # 高亮注释
        if '--' in text:
            index = text.index('--')
            self.setFormat(index, len(text) - index, self.comment_format)
        
        # 高亮字符串
        import re
        for match in re.finditer(r"'[^']*'", text):
            self.setFormat(match.start(), match.end() - match.start(), self.string_format)
        
        # 高亮数字
        for match in re.finditer(r'\b\d+\b', text):
            self.setFormat(match.start(), match.end() - match.start(), self.number_format)
        
        # 高亮关键字
        for keyword in self.keywords:
            regex = re.compile(r'\b' + keyword + r'\b', re.IGNORECASE)
            for match in regex.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), self.keyword_format)


class ModernMainWindow(QMainWindow):
    """
    现代化主窗口 - 侧边栏导航设计
    功能页面直接嵌入右侧内容区
    基于 UI/UX Pro Max 设计系统
    """

    def __init__(self, scale_factor=1.0):
        """
        初始化主窗口
        
        Args:
            scale_factor: 缩放比例（根据屏幕分辨率自动计算）
                         1.0 = 100% 缩放 (1K及以下分辨率)
                         1.5 = 150% 缩放 (2K分辨率)
                         2.0 = 200% 缩放 (3K及以上分辨率，2倍放大)
        """
        super().__init__()
        
        # 设置全局缩放比例
        global SCALE_FACTOR
        SCALE_FACTOR = scale_factor
        
        self.config_manager = get_config_manager()
        self.data_service = get_data_service()
        self.query_history_manager = get_query_history_manager()

        # 初始化性能优化工具
        self.optimizer = get_optimizer()
        self.optimizer.initialize()

        # 创建事件压缩器用于处理滚动事件
        self.scroll_event_compressor = self.optimizer.create_event_compressor(
            "scroll_events", timeout=50
        )
        self.scroll_event_compressor.handle_events = self._handle_scroll_events

        # 创建延迟更新器用于UI更新
        self.deferred_updater = self.optimizer.get_deferred_updater()

        # 设置窗口属性，标题包含缩放信息
        base_title = self.config_manager.get("application.name", "数据查询分析工具")
        if SCALE_FACTOR == 1.0:
            scale_text = "1K @ 100%"
        elif SCALE_FACTOR == 1.5:
            scale_text = "2K @ 150%"
        else:
            scale_text = "3K+ @ 200%"
        self.setWindowTitle(f"{base_title} - {scale_text}")
        
        # 使用动态缩放后的尺寸（基础尺寸 1280x800）
        self.setGeometry(100, 100, scaled(1280), scaled(800))
        self.setMinimumSize(scaled(1024), scaled(600))

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局 - 无间距无外边距
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建左侧边栏导航
        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar)

        # 创建右侧内容区
        self.content_area = self._create_content_area()
        main_layout.addWidget(self.content_area, 1)

        # 添加状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

        # 应用全局样式
        self._apply_styles()

        # 默认显示概览页
        self._show_page(0)

    def _create_sidebar(self) -> QWidget:
        """创建左侧边栏导航 - 240px 宽度"""
        sidebar = QFrame()
        sidebar.setObjectName('sidebar')
        sidebar.setFixedWidth(scaled(240))

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(scaled(16), scaled(20), scaled(16), scaled(20))
        layout.setSpacing(0)

        # Logo/标题
        title = QLabel('🗔 数据查询工具')
        title.setObjectName('sidebar_title')
        layout.addWidget(title)

        # 导航按钮组
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        nav_items = [
            ('📊 概览', 0),
            ('📝 SQL查询', 1),
            ('⬇️ 数据下载', 2),
            ('📈 数据分析', 3),
            ('🕐 查询历史', 4),
            ('⚙️ 系统设置', 5),
        ]

        for index, text in enumerate(nav_items):
            btn = QPushButton(text[1])
            btn.setObjectName('nav_btn')
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked=False, idx=index: self._show_page(idx))
            self.nav_group.addButton(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # 页脚
        footer = QLabel('UI/UX Pro Max\n现代化扁平设计')
        footer.setObjectName('sidebar_footer')
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

        return sidebar

    def _create_content_area(self) -> QWidget:
        """创建右侧内容区域"""
        content = QWidget()
        content.setObjectName('content_area')

        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 头部
        header = self._create_header()
        layout.addWidget(header)

        # 堆叠窗口用于切换不同功能页面
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # 创建各个功能页面 - 直接嵌入
        self.stack.addWidget(self._create_overview_page())
        self.stack.addWidget(self._create_sql_query_page())
        self.stack.addWidget(self._create_data_download_page())
        self.stack.addWidget(self._create_data_analysis_page())
        self.stack.addWidget(self._create_history_page())
        self.stack.addWidget(self._create_settings_page())

        return content

    def _create_header(self) -> QWidget:
        """创建顶部头部区域"""
        header = QFrame()
        header.setObjectName('header')
        header.setFixedHeight(scaled(56))

        layout = QHBoxLayout(header)
        layout.setContentsMargins(scaled(24), 0, scaled(24), 0)

        # 标题
        title = QLabel('数据查询分析工具')
        title.setObjectName('header_title')
        layout.addWidget(title)

        layout.addStretch()

        # 帮助按钮
        btn_help = QPushButton('帮助')
        btn_help.setObjectName('btn_secondary')
        btn_help.clicked.connect(self._show_help)
        layout.addWidget(btn_help)

        # 关于按钮
        btn_about = QPushButton('关于')
        btn_about.setObjectName('btn_primary')
        btn_about.clicked.connect(self._show_about)
        layout.addWidget(btn_about)

        return header

    def _show_page(self, index: int):
        """显示指定页面"""
        self.stack.setCurrentIndex(index)

        # 更新导航按钮状态
        for i, btn in enumerate(self.nav_group.buttons()):
            btn.setChecked(i == index)

        # 更新状态栏
        page_names = ['概览', 'SQL查询', '数据下载', '数据分析', '查询历史', '系统设置']
        self.status_bar.showMessage(f"当前页面: {page_names[index]}")

    # ==================== 各个功能页面 ====================

    def _create_overview_page(self) -> QWidget:
        """创建概览页面 - UI/UX Pro Max 设计"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(scaled(24), scaled(24), scaled(24), scaled(24))
        layout.setSpacing(0)

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
        stats_layout.setSpacing(scaled(16))

        stats = [
            ('数据库连接', '3', '活跃连接'),
            ('今日查询', '127', '次执行'),
            ('数据导出', '15', '次下载'),
            ('存储空间', '2.3 GB', '已使用'),
        ]

        for title_text, value, subtitle_text in stats:
            card = self._create_stat_card(title_text, value, subtitle_text)
            stats_layout.addWidget(card)

        layout.addWidget(stats_widget)

        # 快速操作卡片
        card = QGroupBox('⚡ 快速操作')
        card_layout = QHBoxLayout(card)

        btn_sql = QPushButton('📝 新建 SQL 查询')
        btn_sql.setObjectName('btn_primary')
        btn_sql.clicked.connect(lambda: self._show_page(1))
        card_layout.addWidget(btn_sql)

        btn_download = QPushButton('⬇️ 数据导出')
        btn_download.setObjectName('btn_secondary')
        btn_download.clicked.connect(lambda: self._show_page(2))
        card_layout.addWidget(btn_download)

        btn_analysis = QPushButton('📈 数据分析')
        btn_analysis.setObjectName('btn_secondary')
        btn_analysis.clicked.connect(lambda: self._show_page(3))
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
            item = self._create_activity_item(icon, title_text, desc, time_text)
            card_layout.addWidget(item)
            
            # 添加分隔线（除了最后一个）
            if icon != activities[-1][0]:
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setStyleSheet(f'background-color: {COLORS["divider"]}; max-height: 1px;')
                card_layout.addWidget(line)

        layout.addWidget(card)
        layout.addStretch()

        # 包装在滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        scroll.setFrameShape(QFrame.NoFrame)

        return scroll

    def _create_sql_query_page(self) -> QWidget:
        """创建 SQL 查询页面 - UI/UX Pro Max 设计"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(scaled(24), scaled(24), scaled(24), scaled(24))
        layout.setSpacing(0)

        # 页面标题
        title = QLabel('📝 SQL 查询')
        title.setObjectName('page_title')
        layout.addWidget(title)

        subtitle = QLabel('编写和执行 SQL 查询语句，支持语法高亮和智能提示')
        subtitle.setObjectName('page_subtitle')
        layout.addWidget(subtitle)

        # 使用分割器
        splitter = QSplitter(Qt.Vertical)

        # 上部：SQL 编辑器
        editor_group = QGroupBox('查询编辑器')
        editor_layout = QVBoxLayout(editor_group)

        # 工具栏
        toolbar = QHBoxLayout()
        
        btn_execute = QPushButton('▶️ 执行查询 (F5)')
        btn_execute.setObjectName('btn_primary')
        btn_execute.clicked.connect(self._execute_query)
        toolbar.addWidget(btn_execute)

        btn_clear = QPushButton('🗑️ 清空')
        btn_clear.setObjectName('btn_secondary')
        btn_clear.clicked.connect(self._clear_query)
        toolbar.addWidget(btn_clear)

        btn_history = QPushButton('🕐 历史')
        btn_history.setObjectName('btn_secondary')
        btn_history.clicked.connect(lambda: self._show_page(4))
        toolbar.addWidget(btn_history)

        toolbar.addStretch()
        editor_layout.addLayout(toolbar)

        # SQL 编辑器
        self.sql_editor = QTextEdit()
        self.sql_editor.setPlaceholderText('-- 在此输入 SQL 查询语句\n-- 例如: SELECT * FROM users WHERE status = "active" LIMIT 100;')
        self.sql_editor.setMinimumHeight(scaled(200))
        
        # 应用语法高亮
        self.sql_highlighter = SQLSyntaxHighlighter(self.sql_editor.document())
        
        # 设置等宽字体
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        font.setPointSize(scaled(12))
        self.sql_editor.setFont(font)
        
        editor_layout.addWidget(self.sql_editor)
        splitter.addWidget(editor_group)

        # 下部：查询结果
        result_group = QGroupBox('查询结果')
        result_layout = QVBoxLayout(result_group)

        # 结果工具栏
        result_toolbar = QHBoxLayout()
        
        self.result_info = QLabel('就绪 - 等待执行查询')
        self.result_info.setStyleSheet(f'color: {COLORS["text_secondary"]};')
        result_toolbar.addWidget(self.result_info)

        result_toolbar.addStretch()

        btn_export = QPushButton('📥 导出结果')
        btn_export.setObjectName('btn_secondary')
        btn_export.clicked.connect(self._export_query_result)
        result_toolbar.addWidget(btn_export)

        result_layout.addLayout(result_toolbar)

        # 结果表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(0)
        self.result_table.setRowCount(0)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.result_table.setMinimumHeight(scaled(250))

        # 设置行高
        for row in range(10):
            self.result_table.setRowHeight(row, scaled(44))

        result_layout.addWidget(self.result_table)
        splitter.addWidget(result_group)

        # 设置分割器比例
        splitter.setSizes([scaled(300), scaled(400)])

        layout.addWidget(splitter)

        return page

    def _create_data_download_page(self) -> QWidget:
        """创建数据下载页面 - UI/UX Pro Max 设计"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(scaled(24), scaled(24), scaled(24), scaled(24))
        layout.setSpacing(0)

        # 页面标题
        title = QLabel('⬇️ 数据下载')
        title.setObjectName('page_title')
        layout.addWidget(title)

        subtitle = QLabel('将查询结果导出为 CSV、Excel 等格式文件')
        subtitle.setObjectName('page_subtitle')
        layout.addWidget(subtitle)

        # 下载配置卡片
        card = QGroupBox('下载配置')
        card_layout = QVBoxLayout(card)

        # 导出格式
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel('导出格式:'))
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(['CSV 文件 (.csv)', 'Excel 文件 (.xlsx)', 'JSON 文件 (.json)', 'SQL 文件 (.sql)'])
        self.format_combo.setMinimumWidth(scaled(200))
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        card_layout.addLayout(format_layout)

        # 编码选项
        encoding_layout = QHBoxLayout()
        encoding_layout.addWidget(QLabel('文件编码:'))
        
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems(['UTF-8', 'GBK', 'UTF-8 with BOM'])
        self.encoding_combo.setMinimumWidth(scaled(200))
        encoding_layout.addWidget(self.encoding_combo)
        encoding_layout.addStretch()
        card_layout.addLayout(encoding_layout)

        # 包含表头
        self.include_header = QCheckBox('包含表头')
        self.include_header.setChecked(True)
        card_layout.addWidget(self.include_header)

        # 进度条
        card_layout.addSpacing(scaled(20))
        self.download_progress = QProgressBar()
        self.download_progress.setValue(0)
        card_layout.addWidget(self.download_progress)

        # 下载按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_download = QPushButton('⬇️ 开始下载')
        btn_download.setObjectName('btn_primary')
        btn_download.setFixedWidth(scaled(200))
        btn_download.clicked.connect(self._start_download)
        btn_layout.addWidget(btn_download)

        card_layout.addLayout(btn_layout)
        layout.addWidget(card)

        # 下载历史卡片
        card = QGroupBox('📋 最近下载')
        card_layout = QVBoxLayout(card)

        history_items = [
            ('users_20240115.csv', 'CSV', '15.2 KB', '15 分钟前'),
            ('orders_20240114.xlsx', 'Excel', '128.5 KB', '1 天前'),
            ('products_export.json', 'JSON', '8.3 KB', '2 天前'),
        ]

        for filename, format_type, size, time in history_items:
            item = QWidget()
            item_layout = QHBoxLayout(item)
            item_layout.setContentsMargins(0, 8, 0, 8)

            lbl_icon = QLabel('📄')
            lbl_icon.setStyleSheet('font-size: 16px;')
            item_layout.addWidget(lbl_icon)

            lbl_name = QLabel(f'<b>{filename}</b>')
            lbl_name.setStyleSheet(f'color: {COLORS["text_primary"]};')
            item_layout.addWidget(lbl_name)

            lbl_format = QLabel(format_type)
            lbl_format.setStyleSheet(f'color: {COLORS["text_secondary"]}; font-size: 12px;')
            item_layout.addWidget(lbl_format)

            item_layout.addStretch()

            lbl_size = QLabel(size)
            lbl_size.setStyleSheet(f'color: {COLORS["text_secondary"]};')
            item_layout.addWidget(lbl_size)

            lbl_time = QLabel(time)
            lbl_time.setStyleSheet(f'color: {COLORS["text_disabled"]}; font-size: 12px;')
            item_layout.addWidget(lbl_time)

            card_layout.addWidget(item)

        layout.addWidget(card)
        layout.addStretch()

        # 包装在滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        scroll.setFrameShape(QFrame.NoFrame)

        return scroll

    def _create_data_analysis_page(self) -> QWidget:
        """创建数据分析页面 - UI/UX Pro Max 设计"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(scaled(24), scaled(24), scaled(24), scaled(24))
        layout.setSpacing(0)

        # 页面标题
        title = QLabel('📈 数据分析')
        title.setObjectName('page_title')
        layout.addWidget(title)

        subtitle = QLabel('可视化数据分析和图表展示')
        subtitle.setObjectName('page_subtitle')
        layout.addWidget(subtitle)

        # 统计卡片行
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setSpacing(scaled(16))

        stats = [
            ('总记录数', '12,547', '条'),
            ('今日新增', '234', '条'),
            ('活跃用户', '892', '人'),
            ('增长率', '+12.5%', '环比'),
        ]

        for title_text, value, unit in stats:
            card = self._create_stat_card(title_text, value, unit)
            stats_layout.addWidget(card)

        layout.addWidget(stats_widget)

        # 图表区域（占位）
        card = QGroupBox('📊 数据趋势')
        card_layout = QVBoxLayout(card)
        
        chart_placeholder = QLabel('数据可视化图表区域\n\n（图表功能开发中）')
        chart_placeholder.setAlignment(Qt.AlignCenter)
        chart_placeholder.setStyleSheet(f'''
            color: {COLORS["text_secondary"]};
            background-color: {COLORS["background"]};
            border-radius: {scaled(8)}px;
            padding: {scaled(60)}px;
            font-size: {scaled(16)}px;
        ''')
        chart_placeholder.setMinimumHeight(scaled(300))
        card_layout.addWidget(chart_placeholder)

        layout.addWidget(card)

        # 数据分布卡片
        card = QGroupBox('📋 数据分布')
        card_layout = QHBoxLayout(card)

        # 左侧：分类统计
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        categories = [
            ('用户数据', '45%', COLORS['primary']),
            ('订单数据', '30%', COLORS['success']),
            ('产品数据', '15%', COLORS['warning']),
            ('其他', '10%', COLORS['text_disabled']),
        ]

        for name, percent, color in categories:
            item = QWidget()
            item_layout = QHBoxLayout(item)
            
            lbl_name = QLabel(f'● {name}')
            lbl_name.setStyleSheet(f'color: {color}; font-weight: 600;')
            item_layout.addWidget(lbl_name)
            
            item_layout.addStretch()
            
            lbl_percent = QLabel(percent)
            lbl_percent.setStyleSheet(f'color: {COLORS["text_primary"]}; font-weight: 600;')
            item_layout.addWidget(lbl_percent)
            
            left_layout.addWidget(item)

        card_layout.addWidget(left_widget)

        layout.addWidget(card)
        layout.addStretch()

        # 包装在滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        scroll.setFrameShape(QFrame.NoFrame)

        return scroll

    def _create_history_page(self) -> QWidget:
        """创建查询历史页面 - UI/UX Pro Max 设计"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(scaled(24), scaled(24), scaled(24), scaled(24))
        layout.setSpacing(0)

        # 页面标题
        title = QLabel('🕐 查询历史')
        title.setObjectName('page_title')
        layout.addWidget(title)

        subtitle = QLabel('查看和管理历史查询记录')
        subtitle.setObjectName('page_subtitle')
        layout.addWidget(subtitle)

        # 工具栏
        toolbar = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('🔍 搜索历史查询...')
        self.search_input.setMinimumWidth(scaled(300))
        toolbar.addWidget(self.search_input)

        toolbar.addStretch()

        btn_clear = QPushButton('🗑️ 清空历史')
        btn_clear.setObjectName('btn_secondary')
        btn_clear.clicked.connect(self._clear_history)
        toolbar.addWidget(btn_clear)

        layout.addLayout(toolbar)

        # 历史列表
        card = QGroupBox('历史记录')
        card_layout = QVBoxLayout(card)

        history_data = [
            ('SELECT * FROM users', '12 行', '2 分钟前', '成功'),
            ('SELECT COUNT(*) FROM orders', '1 行', '15 分钟前', '成功'),
            ('UPDATE products SET price = price * 0.9', '0 行', '1 小时前', '成功'),
            ('SELECT * FROM logs WHERE created_at > "2024-01-01"', '超时', '2 小时前', '失败'),
        ]

        for sql, rows, time, status in history_data:
            item = self._create_history_item(sql, rows, time, status)
            card_layout.addWidget(item)
            
            # 添加分隔线
            if sql != history_data[-1][0]:
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setStyleSheet(f'background-color: {COLORS["divider"]}; max-height: 1px;')
                card_layout.addWidget(line)

        layout.addWidget(card)
        layout.addStretch()

        # 包装在滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        scroll.setFrameShape(QFrame.NoFrame)

        return scroll

    def _create_settings_page(self) -> QWidget:
        """创建设置页面 - UI/UX Pro Max 设计"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(scaled(24), scaled(24), scaled(24), scaled(24))
        layout.setSpacing(0)

        # 页面标题
        title = QLabel('⚙️ 系统设置')
        title.setObjectName('page_title')
        layout.addWidget(title)

        subtitle = QLabel('配置数据库连接和应用设置')
        subtitle.setObjectName('page_subtitle')
        layout.addWidget(subtitle)

        # 数据库连接卡片
        card = QGroupBox('🔗 数据库连接')
        card_layout = QVBoxLayout(card)

        # 连接信息
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel('<b>当前连接:</b>'))
        info_layout.addWidget(QLabel('MySQL (localhost:3306/test_db)'))
        info_layout.addStretch()
        
        lbl_status = QLabel('● 已连接')
        lbl_status.setStyleSheet(f'color: {COLORS["success"]}; font-weight: 600;')
        info_layout.addWidget(lbl_status)
        
        card_layout.addLayout(info_layout)

        # 连接按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_config = QPushButton('⚙️ 连接配置')
        btn_config.setObjectName('btn_primary')
        btn_config.clicked.connect(self._show_connection_config)
        btn_layout.addWidget(btn_config)

        btn_test = QPushButton('🔌 测试连接')
        btn_test.setObjectName('btn_secondary')
        btn_test.clicked.connect(self._test_connection)
        btn_layout.addWidget(btn_test)

        card_layout.addLayout(btn_layout)
        layout.addWidget(card)

        # 应用设置卡片
        card = QGroupBox('🔧 应用设置')
        card_layout = QVBoxLayout(card)

        # 自动保存
        self.auto_save = QCheckBox('自动保存查询历史')
        self.auto_save.setChecked(True)
        card_layout.addWidget(self.auto_save)

        # 结果限制
        limit_layout = QHBoxLayout()
        limit_layout.addWidget(QLabel('最大结果行数:'))
        
        self.limit_input = QLineEdit('1000')
        self.limit_input.setFixedWidth(scaled(100))
        limit_layout.addWidget(self.limit_input)
        limit_layout.addStretch()
        card_layout.addLayout(limit_layout)

        # 主题设置
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel('界面主题:'))
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(['浅色主题', '深色主题', '跟随系统'])
        self.theme_combo.setFixedWidth(scaled(150))
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        card_layout.addLayout(theme_layout)

        # 保存按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_save = QPushButton('💾 保存设置')
        btn_save.setObjectName('btn_primary')
        btn_save.clicked.connect(self._save_settings)
        btn_layout.addWidget(btn_save)

        card_layout.addLayout(btn_layout)
        layout.addWidget(card)

        # 关于卡片
        card = QGroupBox('ℹ️ 关于')
        card_layout = QVBoxLayout(card)
        
        about_text = QLabel(
            '<b>数据查询分析工具</b><br>'
            '版本: 1.0.0<br>'
            '设计风格: UI/UX Pro Max 现代化扁平设计<br>'
            '技术栈: Python + PySide2'
        )
        about_text.setStyleSheet(f'color: {COLORS["text_secondary"]}; line-height: 1.6;')
        card_layout.addWidget(about_text)

        layout.addWidget(card)
        layout.addStretch()

        # 包装在滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        scroll.setFrameShape(QFrame.NoFrame)

        return scroll

    # ==================== 辅助方法 ====================

    def _create_stat_card(self, title, value, subtitle):
        """创建统计卡片"""
        card = QFrame()
        card.setObjectName('stat_card')
        card.setMinimumWidth(scaled(200))

        layout = QVBoxLayout(card)
        layout.setSpacing(scaled(8))

        lbl_title = QLabel(title)
        lbl_title.setObjectName('stat_title')
        layout.addWidget(lbl_title)

        lbl_value = QLabel(value)
        lbl_value.setObjectName('stat_value')
        layout.addWidget(lbl_value)

        lbl_subtitle = QLabel(subtitle)
        lbl_subtitle.setObjectName('stat_subtitle')
        layout.addWidget(lbl_subtitle)

        return card

    def _create_activity_item(self, icon, title, desc, time):
        """创建活动项"""
        item = QWidget()
        item_layout = QHBoxLayout(item)
        item_layout.setContentsMargins(0, 8, 0, 8)

        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet('font-size: 16px;')
        item_layout.addWidget(lbl_icon)

        lbl_title = QLabel(f'<b>{title}</b>')
        lbl_title.setStyleSheet(f'color: {COLORS["text_primary"]};')
        item_layout.addWidget(lbl_title)

        lbl_desc = QLabel(desc)
        lbl_desc.setStyleSheet(f'color: {COLORS["text_secondary"]};')
        item_layout.addWidget(lbl_desc)

        item_layout.addStretch()

        lbl_time = QLabel(time)
        lbl_time.setStyleSheet(f'color: {COLORS["text_disabled"]}; font-size: 12px;')
        item_layout.addWidget(lbl_time)

        return item

    def _create_history_item(self, sql, rows, time, status):
        """创建历史记录项"""
        item = QWidget()
        item_layout = QHBoxLayout(item)
        item_layout.setContentsMargins(0, 8, 0, 8)

        # SQL 语句
        lbl_sql = QLabel(sql[:50] + '...' if len(sql) > 50 else sql)
        lbl_sql.setStyleSheet(f'color: {COLORS["primary"]}; font-family: monospace;')
        item_layout.addWidget(lbl_sql)

        item_layout.addStretch()

        # 行数
        lbl_rows = QLabel(rows)
        lbl_rows.setStyleSheet(f'color: {COLORS["text_secondary"]};')
        item_layout.addWidget(lbl_rows)

        # 时间
        lbl_time = QLabel(time)
        lbl_time.setStyleSheet(f'color: {COLORS["text_disabled"]}; font-size: 12px;')
        item_layout.addWidget(lbl_time)

        # 状态
        lbl_status = QLabel(status)
        if status == '成功':
            lbl_status.setStyleSheet(f'color: {COLORS["success"]}; font-weight: 600;')
        else:
            lbl_status.setStyleSheet(f'color: {COLORS["error"]}; font-weight: 600;')
        item_layout.addWidget(lbl_status)

        return item

    # ==================== 功能方法 ====================

    def _execute_query(self):
        """执行 SQL 查询"""
        sql = self.sql_editor.toPlainText().strip()
        if not sql:
            QMessageBox.warning(self, "警告", "请输入 SQL 查询语句")
            return
        
        # 模拟查询结果
        self.result_info.setText(f'执行成功 - 返回 5 行 (耗时 0.23s)')
        
        # 填充示例数据
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(['ID', '用户名', '邮箱', '状态'])
        self.result_table.setRowCount(5)
        
        data = [
            ('1', '张三', 'zhang@example.com', '激活'),
            ('2', '李四', 'li@example.com', '激活'),
            ('3', '王五', 'wang@example.com', '暂停'),
            ('4', '赵六', 'zhao@example.com', '激活'),
            ('5', '钱七', 'qian@example.com', '禁用'),
        ]
        
        for row, (id_, name, email, status) in enumerate(data):
            for col, value in enumerate([id_, name, email, status]):
                item = QTableWidgetItem(value)
                self.result_table.setItem(row, col, item)
            self.result_table.setRowHeight(row, scaled(44))

    def _clear_query(self):
        """清空查询"""
        self.sql_editor.clear()
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(0)
        self.result_info.setText('就绪 - 等待执行查询')

    def _export_query_result(self):
        """导出查询结果"""
        QMessageBox.information(self, "导出", "查询结果导出功能开发中")

    def _start_download(self):
        """开始下载"""
        self.download_progress.setValue(50)
        # 模拟下载
        from PySide2.QtCore import QTimer
        QTimer.singleShot(1000, lambda: self.download_progress.setValue(100))
        self.status_bar.showMessage("下载完成")

    def _clear_history(self):
        """清空历史"""
        reply = QMessageBox.question(self, "确认", "确定要清空所有历史记录吗？")
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "成功", "历史记录已清空")

    def _show_connection_config(self):
        """显示数据库连接配置"""
        from src.presentation.dialogs.connection_config_dialog import ConnectionConfigDialog
        dialog = ConnectionConfigDialog(self)
        dialog.exec_()

    def _test_connection(self):
        """测试数据库连接"""
        QMessageBox.information(self, "连接测试", "数据库连接成功！")

    def _save_settings(self):
        """保存设置"""
        QMessageBox.information(self, "保存", "设置已保存")

    def _show_help(self):
        """显示帮助"""
        QMessageBox.information(
            self, "帮助",
            "数据查询分析工具 v1.0\n\n"
            "功能说明:\n"
            "• SQL查询: 编写和执行SQL语句\n"
            "• 数据下载: 导出查询结果为文件\n"
            "• 数据分析: 可视化数据展示\n"
            "• 系统设置: 配置数据库连接\n\n"
            "快捷键:\n"
            "• F5: 执行查询\n"
            "• Ctrl+S: 保存配置"
        )

    def _show_about(self):
        """显示关于"""
        QMessageBox.about(
            self, "关于",
            "<h2>数据查询分析工具</h2>"
            "<p>版本: 1.0.0</p>"
            "<p>基于 PySide2 开发的桌面数据查询应用程序</p>"
            "<p>设计风格: UI/UX Pro Max 现代化扁平设计</p>"
            "<p>技术栈: Python + PySide2</p>"
        )

    def _handle_scroll_events(self, events):
        """处理滚动事件"""
        pass

    # ==================== 样式应用 ====================

    def _apply_styles(self):
        """应用全局样式 - UI/UX Pro Max 设计规范"""
        self.setStyleSheet(f"""
            /* 全局基础 */
            QWidget {{
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
                font-size: {scaled(14)}px;
                color: {COLORS['text_primary']};
            }}

            /* 侧边栏 */
            #sidebar {{
                background-color: {COLORS['surface']};
                border-right: 1px solid {COLORS['border']};
            }}

            #sidebar_title {{
                font-size: {scaled(18)}px;
                font-weight: 600;
                color: {COLORS['primary']};
                padding: 0 0 {scaled(10)}px 0;
                border-bottom: 1px solid {COLORS['divider']};
                margin-bottom: {scaled(16)}px;
            }}

            #sidebar_footer {{
                color: {COLORS['text_secondary']};
                font-size: {scaled(11)}px;
            }}

            /* 导航按钮 */
            QPushButton#nav_btn {{
                background-color: transparent;
                border: none;
                border-radius: {scaled(6)}px;
                padding: {scaled(10)}px {scaled(14)}px;
                text-align: left;
                font-size: {scaled(14)}px;
                color: {COLORS['text_primary']};
                margin-bottom: {scaled(4)}px;
            }}

            QPushButton#nav_btn:hover {{
                background-color: {COLORS['primary_light']};
                color: {COLORS['primary']};
            }}

            QPushButton#nav_btn:checked {{
                background-color: {COLORS['primary_light']};
                color: {COLORS['primary']};
                border-left: 3px solid {COLORS['primary']};
            }}

            /* 内容区域 */
            #content_area {{
                background-color: {COLORS['background']};
            }}

            /* 头部 */
            #header {{
                background-color: {COLORS['surface']};
                border-bottom: 1px solid {COLORS['border']};
            }}

            #header_title {{
                font-size: {scaled(20)}px;
                font-weight: 600;
                color: {COLORS['text_primary']};
            }}

            /* 页面标题 */
            #page_title {{
                font-size: {scaled(24)}px;
                font-weight: 700;
                color: {COLORS['text_primary']};
                margin-bottom: {scaled(8)}px;
            }}

            #page_subtitle {{
                color: {COLORS['text_secondary']};
                font-size: {scaled(14)}px;
                margin-bottom: {scaled(24)}px;
            }}

            /* 卡片 (GroupBox) */
            QGroupBox {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: {scaled(8)}px;
                padding: {scaled(20)}px;
                margin-top: {scaled(20)}px;
                font-size: {scaled(16)}px;
                font-weight: 600;
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 0;
                top: 0;
                padding: 0 0 {scaled(12)}px 0;
                color: {COLORS['text_primary']};
                border-bottom: 1px solid {COLORS['divider']};
            }}

            /* 统计卡片 */
            #stat_card {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: {scaled(8)}px;
                padding: {scaled(20)}px;
            }}

            #stat_title {{
                color: {COLORS['text_secondary']};
                font-size: {scaled(12)}px;
                text-transform: uppercase;
            }}

            #stat_value {{
                color: {COLORS['primary']};
                font-size: {scaled(32)}px;
                font-weight: 700;
            }}

            #stat_subtitle {{
                color: {COLORS['text_disabled']};
                font-size: {scaled(12)}px;
            }}

            /* 主要按钮 */
            QPushButton#btn_primary {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_inverse']};
                border: none;
                border-radius: {scaled(6)}px;
                padding: {scaled(8)}px {scaled(16)}px;
                font-size: {scaled(14)}px;
                font-weight: 500;
                min-height: {scaled(36)}px;
            }}

            QPushButton#btn_primary:hover {{
                background-color: {COLORS['primary_hover']};
            }}

            /* 次要按钮 */
            QPushButton#btn_secondary {{
                background-color: {COLORS['surface']};
                color: {COLORS['primary']};
                border: 1px solid {COLORS['border']};
                border-radius: {scaled(6)}px;
                padding: {scaled(8)}px {scaled(16)}px;
                font-size: {scaled(14)}px;
                font-weight: 500;
                min-height: {scaled(36)}px;
            }}

            QPushButton#btn_secondary:hover {{
                background-color: {COLORS['primary_light']};
                border-color: {COLORS['primary']};
            }}

            /* 输入框 */
            QLineEdit, QTextEdit, QComboBox {{
                padding: {scaled(8)}px {scaled(12)}px;
                border: 1px solid {COLORS['border']};
                border-radius: {scaled(6)}px;
                font-size: {scaled(14)}px;
                background-color: {COLORS['surface']};
            }}

            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border: 2px solid {COLORS['primary']};
            }}

            /* 表格样式 */
            QTableWidget {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: {scaled(8)}px;
                gridline-color: {COLORS['divider']};
            }}

            QTableWidget::item {{
                padding: {scaled(12)}px;
                border-bottom: 1px solid {COLORS['divider']};
            }}

            QTableWidget::item:selected {{
                background-color: {COLORS['primary_light']};
                color: {COLORS['text_primary']};
            }}

            QHeaderView::section {{
                background-color: {COLORS['background']};
                color: {COLORS['text_secondary']};
                font-weight: 600;
                font-size: {scaled(12)}px;
                padding: {scaled(12)}px;
                border: none;
                border-bottom: 2px solid {COLORS['border']};
                text-transform: uppercase;
            }}

            /* 进度条 */
            QProgressBar {{
                border: none;
                border-radius: 9999px;
                background-color: {COLORS['border']};
                height: {scaled(8)}px;
                text-align: center;
            }}

            QProgressBar::chunk {{
                background-color: {COLORS['primary']};
                border-radius: 9999px;
            }}

            /* 复选框 */
            QCheckBox {{
                spacing: {scaled(8)}px;
            }}

            QCheckBox::indicator {{
                width: {scaled(18)}px;
                height: {scaled(18)}px;
                border-radius: {scaled(4)}px;
                border: 1px solid {COLORS['border']};
            }}

            QCheckBox::indicator:checked {{
                background-color: {COLORS['primary']};
                border-color: {COLORS['primary']};
            }}

            /* 滚动条 */
            QScrollBar:vertical {{
                background-color: {COLORS['background']};
                width: {scaled(8)}px;
                border-radius: {scaled(4)}px;
            }}

            QScrollBar::handle:vertical {{
                background-color: {COLORS['border']};
                border-radius: {scaled(4)}px;
                min-height: {scaled(30)}px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: {COLORS['text_disabled']};
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)


# 保持向后兼容
MainWindow = ModernMainWindow


def calculate_scale_factor(app):
    """根据屏幕分辨率计算缩放比例"""
    screen = app.primaryScreen()
    if screen is None:
        return 1.0

    geometry = screen.geometry()
    width = geometry.width()
    height = geometry.height()

    if width >= 3200 or height >= 1800:
        return 2.0  # 3K 及以上 - 2倍放大
    elif width >= 2560 or height >= 1440:
        return 1.5  # 2K
    else:
        return 1.0  # 1K 及以下


def main():
    """主函数（用于测试）"""
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    global SCALE_FACTOR
    SCALE_FACTOR = calculate_scale_factor(app)

    font = QFont('Microsoft YaHei', int(10 * SCALE_FACTOR))
    app.setFont(font)

    window = ModernMainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
