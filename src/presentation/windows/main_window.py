#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主窗口模块 - UI/UX Pro Max 现代化重构版本
基于 style_demo_v3.py 设计规范
功能页面直接嵌入右侧内容区
"""

import logging
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径，确保能够找到src模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

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
from src.infrastructure.utils.scaling_manager import get_scaling_manager
from src.business.services.data_service import get_data_service
from src.business.services.query_history_manager import get_query_history_manager
from src.infrastructure.utils.performance import EventCompressor, DeferredUpdater, get_optimizer
from src.presentation.windows.main_window_components import MainWindowComponents
from src.presentation.windows.main_window_pages import MainWindowPages
from src.presentation.windows.ui_constants import COLORS

logger = logging.getLogger(__name__)


# SQL语法高亮器
class SQLSyntaxHighlighter(QSyntaxHighlighter):
    """SQL语法高亮器"""

    def __init__(self, parent=None):
        super().__init__(parent)  # type: ignore

        # SQL关键字 - UI/UX Pro Max 配色
        self.keywords = [
            'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP',
            'ALTER', 'TABLE', 'VIEW', 'INDEX', 'TRIGGER', 'PROCEDURE', 'FUNCTION',
            'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON', 'AS', 'GROUP',
            'BY', 'HAVING', 'ORDER', 'LIMIT', 'OFFSET', 'AND', 'OR', 'NOT',
            'IN', 'LIKE', 'BETWEEN', 'IS', 'NULL', 'TRUE', 'FALSE'
        ]

        # 定义格式 - UI/UX Pro Max 配色方案
        self.keyword_format = QTextCharFormat()  # type: ignore
        self.keyword_format.setForeground(QColor(COLORS['primary']))  # type: ignore
        self.keyword_format.setFontWeight(QFont.Bold)  # type: ignore

        self.string_format = QTextCharFormat()  # type: ignore
        self.string_format.setForeground(QColor(COLORS['success']))  # type: ignore

        self.comment_format = QTextCharFormat()  # type: ignore
        self.comment_format.setForeground(QColor(COLORS['text_disabled']))  # type: ignore
        self.comment_format.setFontItalic(True)

        self.number_format = QTextCharFormat()  # type: ignore
        self.number_format.setForeground(QColor(COLORS['warning']))  # type: ignore
    
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


class MainWindow(QMainWindow):
    """
    现代化主窗口 - 侧边栏导航设计
    功能页面直接嵌入右侧内容区
    基于 UI/UX Pro Max 设计系统
    """

    # 预声明页面创建过程中动态添加的属性（P1修复）
    sql_editor: QTextEdit
    result_table: QTableWidget
    export_format: 'QComboBox'
    export_filename: 'QLineEdit'
    analysis_type: 'QComboBox'
    analysis_result: QTextEdit
    history_list: 'QListWidget'
    scale_combo: 'QComboBox'
    auto_connect_checkbox: 'QCheckBox'

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

        # 初始化缩放管理器
        self.scaling_manager = get_scaling_manager()
        self.scaling_manager.set_scale_factor(scale_factor)

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

        # 初始化UI组件类（重构第一阶段）
        self.components = MainWindowComponents(self.scaled)

        # 初始化页面创建类（重构第三阶段）
        self.pages = MainWindowPages(self)

        # 设置窗口属性
        base_title = self.config_manager.get("application.name", "数据查询分析工具")
        self.setWindowTitle(base_title)
        
        # 存储连接状态，用于标题栏显示
        self._connected_ip = ""
        
        # 使用动态缩放后的尺寸（基础尺寸 1280x800）
        self.setGeometry(100, 100, self.scaled(1280), self.scaled(800))
        self.setMinimumSize(self.scaled(1024), self.scaled(600))

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局 - 无间距无外边距
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)  # type: ignore
        main_layout.setSpacing(0)  # type: ignore

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
        sidebar.setFixedWidth(self.scaled(240))  # type: ignore

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(self.scaled(16), self.scaled(20), self.scaled(16), self.scaled(20))  # type: ignore
        layout.setSpacing(0)  # type: ignore

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

        for text, page_index in nav_items:
            btn = QPushButton(text)
            btn.setObjectName('nav_btn')
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked=False, idx=page_index: self._show_page(idx))  # type: ignore
            self.nav_group.addButton(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # 页脚
        footer = QLabel('UI/UX Pro Max\n现代化扁平设计')
        footer.setObjectName('sidebar_footer')
        footer.setAlignment(Qt.AlignCenter)  # type: ignore
        layout.addWidget(footer)

        return sidebar

    def _create_content_area(self) -> QWidget:
        """创建右侧内容区域"""
        content = QWidget()
        content.setObjectName('content_area')

        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)  # type: ignore
        layout.setSpacing(0)  # type: ignore

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
        header.setFixedHeight(self.scaled(56))  # type: ignore

        layout = QHBoxLayout(header)
        layout.setContentsMargins(self.scaled(24), 0, self.scaled(24), 0)  # type: ignore

        # 标题
        title = QLabel('数据查询分析工具')
        title.setObjectName('header_title')
        layout.addWidget(title)

        layout.addStretch()

        # 帮助按钮
        btn_help = QPushButton('帮助')
        btn_help.setObjectName('btn_secondary')
        btn_help.clicked.connect(self._show_help)  # type: ignore
        layout.addWidget(btn_help)

        # 关于按钮
        btn_about = QPushButton('关于')
        btn_about.setObjectName('btn_primary')
        btn_about.clicked.connect(self._show_about)  # type: ignore
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
        """创建overview页面 - 委托给 MainWindowPages"""
        return self.pages._create_overview_page()


    def _create_sql_query_page(self) -> QWidget:
        """创建sql_query页面 - 委托给 MainWindowPages"""
        return self.pages._create_sql_query_page()


    def _create_data_download_page(self) -> QWidget:
        """创建data_download页面 - 委托给 MainWindowPages"""
        return self.pages._create_data_download_page()


    def _create_data_analysis_page(self) -> QWidget:
        """创建data_analysis页面 - 委托给 MainWindowPages"""
        return self.pages._create_data_analysis_page()


    def _create_history_page(self) -> QWidget:
        """创建history页面 - 委托给 MainWindowPages"""
        return self.pages._create_history_page()


    def _create_settings_page(self) -> QWidget:
        """创建settings页面 - 委托给 MainWindowPages"""
        return self.pages._create_settings_page()


    def _create_stat_card(self, title, value, subtitle):
        """创建统计卡片 - 委托给 MainWindowComponents"""
        return self.components._create_stat_card(title, value, subtitle)

    def _create_activity_item(self, icon, title, desc, time):
        """创建活动项 - 委托给 MainWindowComponents"""
        return self.components._create_activity_item(icon, title, desc, time)

    def _create_history_item(self, sql, rows, time, status):
        """创建历史记录项 - 委托给 MainWindowComponents"""
        return self.components._create_history_item(sql, rows, time, status)

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
            self.result_table.setRowHeight(row, self.scaled(44))  # type: ignore

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

    def _show_log_viewer(self):
        """显示日志查看器"""
        from src.presentation.dialogs.log_dialog import LogDialog
        dialog = LogDialog(self)
        dialog.exec_()

    def _update_connection_status(self, connected: bool, server: str = "", port: int = 0, namespace: str = "", db_type: str = ""):
        """
        更新数据库连接状态并同步更新标题栏显示
        
        Args:
            connected: 是否已连接
            server: 服务器地址
            port: 端口号
            namespace: 命名空间
            db_type: 数据库类型
        """
        base_title = self.config_manager.get("application.name", "数据查询分析工具")
        
        if connected and server:
            # 连接成功，显示连接信息
            self._connected_ip = server
            connection_info = f"{db_type} ({server}:{port}/{namespace})"
            
            # 更新窗口标题
            self.setWindowTitle(f"{base_title} - 已连接: {server}")
            
            # 更新系统设置页面的连接信息显示
            if hasattr(self, 'connection_info_label'):
                self.connection_info_label.setText(connection_info)
                self.connection_info_label.setStyleSheet(f'color: {COLORS["success"]};')  # type: ignore
            
            # 更新状态标签
            if hasattr(self, '_connection_status_label'):
                self._connection_status_label.setText('● 已连接')
                self._connection_status_label.setStyleSheet(f'color: {COLORS["success"]}; font-weight: 600;')  # type: ignore
        else:
            # 未连接
            self._connected_ip = ""
            
            # 更新窗口标题
            self.setWindowTitle(base_title)
            
            # 更新系统设置页面的连接信息显示
            if hasattr(self, 'connection_info_label'):
                self.connection_info_label.setText('未连接')
                self.connection_info_label.setStyleSheet(f'color: {COLORS["text_secondary"]};')  # type: ignore
            
            # 更新状态标签
            if hasattr(self, '_connection_status_label'):
                self._connection_status_label.setText('● 未连接')
                self._connection_status_label.setStyleSheet(f'color: {COLORS["error"]}; font-weight: 600;')  # type: ignore

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
            "• 系统设置: 配置数据库连接和查看日志\n\n"
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

    def scaled(self, value):
        """
        根据当前缩放比例计算实际像素值

        Args:
            value: 基础像素值（基于 1K 分辨率设计）

        Returns:
            int: 缩放后的像素值
        """
        return self.scaling_manager.scale(value)

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
                font-size: {self.scaled(14)}px;
                color: {COLORS['text_primary']};
            }}

            /* 侧边栏 */
            #sidebar {{
                background-color: {COLORS['surface']};
                border-right: 1px solid {COLORS['border']};
            }}

            #sidebar_title {{
                font-size: {self.scaled(18)}px;
                font-weight: 600;
                color: {COLORS['primary']};
                padding: 0 0 {self.scaled(10)}px 0;
                border-bottom: 1px solid {COLORS['divider']};
                margin-bottom: {self.scaled(16)}px;
            }}

            #sidebar_footer {{
                color: {COLORS['text_secondary']};
                font-size: {self.scaled(11)}px;
            }}

            /* 导航按钮 */
            QPushButton#nav_btn {{
                background-color: transparent;
                border: none;
                border-radius: {self.scaled(6)}px;
                padding: {self.scaled(10)}px {self.scaled(14)}px;
                text-align: left;
                font-size: {self.scaled(14)}px;
                color: {COLORS['text_primary']};
                margin-bottom: {self.scaled(4)}px;
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
                font-size: {self.scaled(20)}px;
                font-weight: 600;
                color: {COLORS['text_primary']};
            }}

            /* 页面标题 */
            #page_title {{
                font-size: {self.scaled(24)}px;
                font-weight: 700;
                color: {COLORS['text_primary']};
                margin-bottom: {self.scaled(8)}px;
            }}

            #page_subtitle {{
                color: {COLORS['text_secondary']};
                font-size: {self.scaled(14)}px;
                margin-bottom: {self.scaled(24)}px;
            }}

            /* 卡片 (GroupBox) */
            QGroupBox {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: {self.scaled(8)}px;
                padding: {self.scaled(20)}px;
                margin-top: {self.scaled(20)}px;
                font-size: {self.scaled(16)}px;
                font-weight: 600;
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 0;
                top: 0;
                padding: 0 0 {self.scaled(12)}px 0;
                color: {COLORS['text_primary']};
                border-bottom: 1px solid {COLORS['divider']};
            }}

            /* 统计卡片 */
            #stat_card {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: {self.scaled(8)}px;
                padding: {self.scaled(20)}px;
            }}

            #stat_title {{
                color: {COLORS['text_secondary']};
                font-size: {self.scaled(12)}px;
                text-transform: uppercase;
            }}

            #stat_value {{
                color: {COLORS['primary']};
                font-size: {self.scaled(32)}px;
                font-weight: 700;
            }}

            #stat_subtitle {{
                color: {COLORS['text_disabled']};
                font-size: {self.scaled(12)}px;
            }}

            /* 主要按钮 */
            QPushButton#btn_primary {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_inverse']};
                border: none;
                border-radius: {self.scaled(6)}px;
                padding: {self.scaled(8)}px {self.scaled(16)}px;
                font-size: {self.scaled(14)}px;
                font-weight: 500;
                min-height: {self.scaled(36)}px;
            }}

            QPushButton#btn_primary:hover {{
                background-color: {COLORS['primary_hover']};
            }}

            /* 次要按钮 */
            QPushButton#btn_secondary {{
                background-color: {COLORS['surface']};
                color: {COLORS['primary']};
                border: 1px solid {COLORS['border']};
                border-radius: {self.scaled(6)}px;
                padding: {self.scaled(8)}px {self.scaled(16)}px;
                font-size: {self.scaled(14)}px;
                font-weight: 500;
                min-height: {self.scaled(36)}px;
            }}

            QPushButton#btn_secondary:hover {{
                background-color: {COLORS['primary_light']};
                border-color: {COLORS['primary']};
            }}

            /* 输入框 */
            QLineEdit, QTextEdit, QComboBox {{
                padding: {self.scaled(8)}px {self.scaled(12)}px;
                border: 1px solid {COLORS['border']};
                border-radius: {self.scaled(6)}px;
                font-size: {self.scaled(14)}px;
                background-color: {COLORS['surface']};
            }}

            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border: 2px solid {COLORS['primary']};
            }}

            /* 表格样式 */
            QTableWidget {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: {self.scaled(8)}px;
                gridline-color: {COLORS['divider']};
            }}

            QTableWidget::item {{
                padding: {self.scaled(12)}px;
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
                font-size: {self.scaled(12)}px;
                padding: {self.scaled(12)}px;
                border: none;
                border-bottom: 2px solid {COLORS['border']};
                text-transform: uppercase;
            }}

            /* 进度条 */
            QProgressBar {{
                border: none;
                border-radius: 9999px;
                background-color: {COLORS['border']};
                height: {self.scaled(8)}px;
                text-align: center;
            }}

            QProgressBar::chunk {{
                background-color: {COLORS['primary']};
                border-radius: 9999px;
            }}

            /* 复选框 */
            QCheckBox {{
                spacing: {self.scaled(8)}px;
            }}

            QCheckBox::indicator {{
                width: {self.scaled(18)}px;
                height: {self.scaled(18)}px;
                border-radius: {self.scaled(4)}px;
                border: 1px solid {COLORS['border']};
            }}

            QCheckBox::indicator:checked {{
                background-color: {COLORS['primary']};
                border-color: {COLORS['primary']};
            }}

            /* 滚动条 */
            QScrollBar:vertical {{
                background-color: {COLORS['background']};
                width: {self.scaled(8)}px;
                border-radius: {self.scaled(4)}px;
            }}

            QScrollBar::handle:vertical {{
                background-color: {COLORS['border']};
                border-radius: {self.scaled(4)}px;
                min-height: {self.scaled(30)}px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: {COLORS['text_disabled']};
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

    # 类名已统一为 MainWindow，无需向后兼容别名


def main():
    """主函数（用于测试）"""
    from src.infrastructure.utils.scaling_manager import get_scaling_manager

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    # 使用 ScalingManager 计算缩放比例
    scaling_manager = get_scaling_manager()
    scale_factor = scaling_manager.calculate_from_screen(app)

    font = QFont('Microsoft YaHei', int(10 * scale_factor))
    app.setFont(font)

    window = MainWindow(scale_factor=scale_factor)
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
