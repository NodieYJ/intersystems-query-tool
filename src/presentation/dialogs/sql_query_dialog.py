#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SQL查询对话框
"""

import csv
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional

from PySide2.QtCore import Qt, QThreadPool, QRunnable, Slot, QObject, Signal, QRegExp
from PySide2.QtWidgets import (QDialog, QGroupBox, QHBoxLayout, QLabel, QPushButton,
                               QTableWidget, QTableWidgetItem, QTextEdit,
                               QVBoxLayout, QWidget, QSplitter, QStatusBar,
                               QMenu, QAction, QFileDialog, QMessageBox,
                               QProgressBar, QComboBox, QLineEdit, QCheckBox,
                               QTabWidget, QInputDialog, QCompleter, QTreeWidget,
                               QTreeWidgetItem, QHeaderView)
from PySide2.QtGui import QFont, QKeySequence, QSyntaxHighlighter, QTextCharFormat, QColor, QFontDatabase, QIcon

from src.business.services.data_service import get_data_service
from src.business.services.query_history_manager import get_query_history_manager
from src.infrastructure.config.config_manager import get_config_manager
from src.infrastructure.security.security_utils import get_security_utils
from src.presentation.dialogs.query_history_dialog import QueryHistoryDialog

logger = logging.getLogger(__name__)

# 定义信号类
class WorkerSignals(QObject):
    """
    工作线程信号类
    """
    result = Signal(object)
    error = Signal(str)
    progress = Signal(int)

# SQL语法高亮器
class SQLSyntaxHighlighter(QSyntaxHighlighter):
    """
    SQL语法高亮器
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 定义SQL关键字
        self.keywords = [
            'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP',
            'ALTER', 'TABLE', 'VIEW', 'INDEX', 'TRIGGER', 'PROCEDURE', 'FUNCTION',
            'BEGIN', 'END', 'IF', 'ELSE', 'THEN', 'WHILE', 'FOR', 'LOOP',
            'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON', 'AS', 'GROUP',
            'BY', 'HAVING', 'ORDER', 'LIMIT', 'OFFSET', 'AND', 'OR', 'NOT',
            'IN', 'LIKE', 'BETWEEN', 'IS', 'NULL', 'TRUE', 'FALSE'
        ]
        
        # 定义SQL函数
        self.functions = [
            'SUM', 'COUNT', 'AVG', 'MAX', 'MIN', 'ROUND', 'TRUNCATE', 'CONCAT',
            'SUBSTRING', 'LENGTH', 'UPPER', 'LOWER', 'DATE', 'TIME', 'NOW', 'CURDATE',
            'CURTIME', 'DATEDIFF', 'TIMEDIFF', 'CAST', 'CONVERT', 'COALESCE', 'NULLIF'
        ]
        
        # 定义格式
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor(128, 0, 128))  # 紫色
        self.keyword_format.setFontWeight(QFont.Bold)
        
        self.function_format = QTextCharFormat()
        self.function_format.setForeground(QColor(0, 0, 255))  # 蓝色
        self.function_format.setFontWeight(QFont.Bold)
        
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor(0, 128, 0))  # 绿色
        
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor(128, 128, 128))  # 灰色
        self.comment_format.setFontItalic(True)
        
        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor(255, 0, 0))  # 红色
    
    def highlightBlock(self, text):
        """
        高亮文本块
        """
        # 高亮注释
        self.highlight_comments(text)
        
        # 高亮字符串
        self.highlight_strings(text)
        
        # 高亮数字
        self.highlight_numbers(text)
        
        # 高亮关键字和函数
        self.highlight_keywords(text)
        self.highlight_functions(text)
    
    def highlight_comments(self, text):
        """
        高亮注释
        """
        # 单行注释
        comment_pattern = QRegExp('--.*$')
        index = comment_pattern.indexIn(text)
        while index >= 0:
            length = comment_pattern.matchedLength()
            self.setFormat(index, length, self.comment_format)
            index = comment_pattern.indexIn(text, index + length)
    
    def highlight_strings(self, text):
        """
        高亮字符串
        """
        # 单引号字符串
        string_pattern = QRegExp("'[^']*'")
        index = string_pattern.indexIn(text)
        while index >= 0:
            length = string_pattern.matchedLength()
            self.setFormat(index, length, self.string_format)
            index = string_pattern.indexIn(text, index + length)
        
        # 双引号字符串
        string_pattern = QRegExp('"[^"]*"')
        index = string_pattern.indexIn(text)
        while index >= 0:
            length = string_pattern.matchedLength()
            self.setFormat(index, length, self.string_format)
            index = string_pattern.indexIn(text, index + length)
    
    def highlight_numbers(self, text):
        """
        高亮数字
        """
        number_pattern = QRegExp('\\b\d+(\\.\\d+)?\\b')
        index = number_pattern.indexIn(text)
        while index >= 0:
            length = number_pattern.matchedLength()
            self.setFormat(index, length, self.number_format)
            index = number_pattern.indexIn(text, index + length)
    
    def highlight_keywords(self, text):
        """
        高亮关键字
        """
        for keyword in self.keywords:
            pattern = QRegExp('\\b' + keyword + '\\b', Qt.CaseInsensitive)
            index = pattern.indexIn(text)
            while index >= 0:
                length = pattern.matchedLength()
                self.setFormat(index, length, self.keyword_format)
                index = pattern.indexIn(text, index + length)
    
    def highlight_functions(self, text):
        """
        高亮函数
        """
        for function in self.functions:
            pattern = QRegExp('\\b' + function + '\\s*\\(', Qt.CaseInsensitive)
            index = pattern.indexIn(text)
            while index >= 0:
                # 找到函数名的结束位置（左括号前）
                end_index = index
                while end_index < len(text) and text[end_index].isalnum():
                    end_index += 1
                self.setFormat(index, end_index - index, self.function_format)
                index = pattern.indexIn(text, end_index)

# 增强的SQL编辑器
class EnhancedSqlEditor(QTextEdit):
    """
    增强的SQL编辑器，支持语法高亮和自动补全
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置字体
        mono_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        mono_font.setPointSize(10)
        self.setFont(mono_font)
        
        # 添加语法高亮
        self.highlighter = SQLSyntaxHighlighter(self.document())
        
        # 设置自动补全
        self.setup_autocomplete()
        
        # 设置Tab键行为
        self.setTabStopWidth(40)  # 4个空格宽度
    
    def setup_autocomplete(self):
        """
        设置自动补全
        """
        # 自动补全的单词列表
        keywords = [
            'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP',
            'ALTER', 'TABLE', 'VIEW', 'INDEX', 'TRIGGER', 'PROCEDURE', 'FUNCTION',
            'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON', 'AS', 'GROUP',
            'BY', 'HAVING', 'ORDER', 'LIMIT', 'OFFSET', 'AND', 'OR', 'NOT',
            'IN', 'LIKE', 'BETWEEN', 'IS', 'NULL', 'TRUE', 'FALSE'
        ]
        
        functions = [
            'SUM', 'COUNT', 'AVG', 'MAX', 'MIN', 'ROUND', 'TRUNCATE', 'CONCAT',
            'SUBSTRING', 'LENGTH', 'UPPER', 'LOWER', 'DATE', 'TIME', 'NOW', 'CURDATE',
            'CURTIME', 'DATEDIFF', 'TIMEDIFF', 'CAST', 'CONVERT'
        ]
        
        # 合并所有单词
        all_words = keywords + functions
        
        # 创建自动补全器
        self.completer = QCompleter(all_words, self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setWidget(self)
        
        # 连接信号
        self.completer.activated.connect(self.insert_completion)
    
    def insert_completion(self, completion):
        """
        插入补全内容
        """
        tc = self.textCursor()
        length = len(tc.selectedText())
        tc.removeSelectedText()
        tc.insertText(completion)
        self.setTextCursor(tc)
    
    def keyPressEvent(self, event):
        """
        处理按键事件
        """
        if self.completer and self.completer.popup().isVisible():
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab):
                event.ignore()
                return
        
        super().keyPressEvent(event)
        
        # 触发自动补全
        if event.key() in (Qt.Key_Space, Qt.Key_Period) or event.text().isalnum():
            tc = self.textCursor()
            tc.select(Qt.TextCursor.WordUnderCursor)
            self.completer.setCompletionPrefix(tc.selectedText())
            popup = self.completer.popup()
            popup.setCurrentIndex(self.completer.completionModel().index(0, 0))
            
            # 计算弹出位置
            cr = self.cursorRect()
            cr.setWidth(self.completer.popup().sizeHintForColumn(0) + 
                       self.completer.popup().verticalScrollBar().sizeHint().width())
            self.completer.complete(cr)
        else:
            self.completer.popup().hide()

# 定义工作线程类
class QueryWorker(QRunnable):
    """
    查询工作线程 - 使用 QRunnable 实现线程安全查询

    Attributes:
        query: SQL 查询语句
        params: 查询参数
        signals: 工作信号（结果、错误、进度）
        data_service: 数据服务实例
        tab: 关联的查询标签页引用
    """
    def __init__(self, query: str, params: Optional[List[Any]] = None, tab: Optional['QueryTab'] = None):
        super().__init__()
        self.query = query
        self.params = params
        self.signals = WorkerSignals()
        self.data_service = get_data_service()
        self.tab = tab  # 存储 tab 引用

    @Slot()
    def run(self):
        """
        执行查询
        """
        try:
            result = self.data_service.get_data(self.query, self.params)
            self.signals.result.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))

class QueryTab(QWidget):
    """
    查询标签页类
    """
    def __init__(self, tab_name, parent=None):
        super().__init__(parent)
        self.tab_name = tab_name
        self.parent_dialog = parent
        self.current_data = None
        self.all_data = None
        self.current_page = 1
        self.page_size = 100
        self.total_pages = 1
        self.total_rows = 0
        self.is_querying = False
        
        # 布局
        self.main_layout = QVBoxLayout(self)
        
        # 使用分割器创建可调整大小的区域
        splitter = QSplitter(Qt.Vertical)
        
        # SQL输入区域
        sql_widget = QWidget()
        sql_layout = QVBoxLayout(sql_widget)
        
        sql_label = QLabel("SQL语句输入区:")
        sql_label.setFont(QFont("Arial", 10, QFont.Bold))
        sql_layout.addWidget(sql_label)
        
        self.sql_edit = EnhancedSqlEditor()
        self.sql_edit.setPlaceholderText("输入SQL查询语句，例如：SELECT * FROM table_name")
        self.sql_edit.setMinimumHeight(150)
        sql_layout.addWidget(self.sql_edit)
        
        # SQL执行按钮和查询选项
        sql_buttons_layout = QHBoxLayout()
        execute_btn = QPushButton("执行查询 (F5)")
        execute_btn.clicked.connect(self.execute_query)
        execute_btn.setShortcut(QKeySequence("F5"))
        execute_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        
        clear_btn = QPushButton("清空SQL")
        clear_btn.clicked.connect(self.clear_sql)
        
        # 查询选项
        query_options_layout = QHBoxLayout()
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["50", "100", "200", "500", "1000"])
        self.page_size_combo.setCurrentText("100")
        self.page_size_combo.currentTextChanged.connect(lambda text: setattr(self, "page_size", int(text)))
        
        self.limit_checkbox = QCheckBox("限制结果")
        self.limit_checkbox.setChecked(True)
        
        query_options_layout.addWidget(QLabel("每页行数:"))
        query_options_layout.addWidget(self.page_size_combo)
        query_options_layout.addWidget(self.limit_checkbox)
        
        sql_buttons_layout.addWidget(execute_btn)
        sql_buttons_layout.addWidget(clear_btn)
        sql_buttons_layout.addStretch()
        sql_buttons_layout.addLayout(query_options_layout)
        
        sql_layout.addLayout(sql_buttons_layout)
        splitter.addWidget(sql_widget)
        
        # 查询结果区域
        result_widget = QWidget()
        result_layout = QVBoxLayout(result_widget)
        
        result_label = QLabel("查询结果展示区:")
        result_label.setFont(QFont("Arial", 10, QFont.Bold))
        result_layout.addWidget(result_label)
        
        # 结果表格
        self.result_table = QTableWidget()
        self.result_table.setAlternatingRowColors(True)
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.result_table.verticalHeader().setDefaultSectionSize(20)
        self.result_table.setShowGrid(True)
        self.result_table.setGridStyle(Qt.DotLine)
        self.result_table.setStyleSheet("""
            QTableWidget {
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10pt;
                alternate-background-color: #f5f5f5;
            }
            QTableWidget::item {
                padding: 2px 5px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        # 启用排序，但在数据加载时禁用以提高性能
        self.result_table.setSortingEnabled(False)
        result_layout.addWidget(self.result_table)
        
        # 分页控制区域
        pagination_layout = QHBoxLayout()
        self.page_info_label = QLabel("第 0 页，共 0 页")
        self.prev_page_btn = QPushButton("上一页")
        self.prev_page_btn.clicked.connect(self.prev_page)
        self.prev_page_btn.setEnabled(False)
        self.next_page_btn = QPushButton("下一页")
        self.next_page_btn.clicked.connect(self.next_page)
        self.next_page_btn.setEnabled(False)

        # 页码跳转
        self.page_input = QLineEdit()
        self.page_input.setMaximumWidth(50)
        self.page_input.setPlaceholderText("页码")
        self.page_input.setAlignment(Qt.AlignCenter)
        self.page_input.returnPressed.connect(self.goto_page)

        self.goto_page_btn = QPushButton("跳转")
        self.goto_page_btn.clicked.connect(self.goto_page)
        self.goto_page_btn.setEnabled(False)

        pagination_layout.addWidget(self.page_info_label)
        pagination_layout.addStretch()
        pagination_layout.addWidget(QLabel("跳转到:"))
        pagination_layout.addWidget(self.page_input)
        pagination_layout.addWidget(self.goto_page_btn)
        pagination_layout.addWidget(self.prev_page_btn)
        pagination_layout.addWidget(self.next_page_btn)
        result_layout.addLayout(pagination_layout)
        
        # 结果信息区域
        info_layout = QHBoxLayout()
        self.row_count_label = QLabel("行数: 0")
        self.column_count_label = QLabel("列数: 0")
        self.query_time_label = QLabel("查询时间: -")
        
        info_layout.addWidget(self.row_count_label)
        info_layout.addWidget(self.column_count_label)
        info_layout.addWidget(self.query_time_label)
        info_layout.addStretch()
        result_layout.addLayout(info_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        result_layout.addWidget(self.progress_bar)
        
        splitter.addWidget(result_widget)
        self.main_layout.addWidget(splitter)
        
    def execute_query(self):
        """
        执行SQL查询
        """
        self.parent_dialog.execute_query_in_tab(self)
    
    def clear_sql(self):
        """
        清空SQL输入框
        """
        self.sql_edit.clear()
    
    def prev_page(self):
        """
        上一页
        """
        if self.current_page > 1:
            self.current_page -= 1
            self.load_page_data()
            self.display_paged_result()
            self.update_pagination()
    
    def next_page(self):
        """
        下一页
        """
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_page_data()
            self.display_paged_result()
            self.update_pagination()

    def goto_page(self):
        """
        跳转到指定页
        """
        try:
            page_num = int(self.page_input.text().strip())
            if 1 <= page_num <= self.total_pages:
                self.current_page = page_num
                self.load_page_data()
                self.display_paged_result()
                self.update_pagination()
                self.page_input.clear()
            else:
                QMessageBox.warning(
                    self.parent_dialog,
                    "无效页码",
                    f"请输入1到{self.total_pages}之间的页码"
                )
        except ValueError:
            QMessageBox.warning(self.parent_dialog, "无效输入", "请输入有效的页码数字")

    def load_page_data(self):
        """
        加载当前页数据
        """
        if not self.all_data:
            self.current_data = None
            return
        
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        
        # 获取当前页数据
        current_rows = self.all_data['rows'][start_idx:end_idx]
        self.current_data = {
            'columns': self.all_data['columns'],
            'rows': current_rows
        }
    
    def update_pagination(self):
        """
        更新分页信息
        """
        self.page_info_label.setText(f"第 {self.current_page} 页，共 {self.total_pages} 页")
        self.prev_page_btn.setEnabled(self.current_page > 1)
        self.next_page_btn.setEnabled(self.current_page < self.total_pages)
        self.goto_page_btn.setEnabled(self.total_pages > 1)
    
    def display_paged_result(self):
        """
        显示当前页结果
        """
        if not self.current_data:
            self.result_table.setRowCount(0)
            self.result_table.setColumnCount(0)
            return
        
        columns = self.current_data['columns']
        rows = self.current_data['rows']
        
        # 禁用排序以提高性能
        self.result_table.setSortingEnabled(False)
        
        # 清空表格
        self.result_table.clear()
        
        # 设置列数和列标题
        self.result_table.setColumnCount(len(columns))
        self.result_table.setHorizontalHeaderLabels(columns)
        
        # 设置行数
        self.result_table.setRowCount(len(rows))
        
        # 批量填充数据以提高性能
        for row_idx, row_data in enumerate(rows):
            for col_idx, cell in enumerate(row_data):
                item = QTableWidgetItem(str(cell) if cell is not None else "NULL")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # 设为只读
                # 对齐方式
                if isinstance(cell, (int, float)):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.result_table.setItem(row_idx, col_idx, item)
        
        # 调整列宽
        self.result_table.resizeColumnsToContents()
        
        # 启用排序
        self.result_table.setSortingEnabled(True)
    
    def display_result(self, result):
        """
        在表格中显示查询结果
        """
        # 禁用排序以提高性能
        self.result_table.setSortingEnabled(False)
        
        self.result_table.clear()
        
        if not result:
            self.result_table.setRowCount(0)
            self.result_table.setColumnCount(0)
            return

        # 获取列名
        columns = list(result[0].keys())

        # 设置列数和列标题
        self.result_table.setColumnCount(len(columns))
        self.result_table.setHorizontalHeaderLabels(columns)
        
        # 设置行数
        self.result_table.setRowCount(len(result))
        
        # 批量填充数据以提高性能
        for row_idx, row_data in enumerate(result):
            for col_idx, col_name in enumerate(columns):
                cell = row_data.get(col_name, "NULL")
                item = QTableWidgetItem(str(cell) if cell is not None else "NULL")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # 设为只读
                # 对齐方式
                if isinstance(cell, (int, float)):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.result_table.setItem(row_idx, col_idx, item)
        
        # 调整列宽
        self.result_table.resizeColumnsToContents()
        
        # 启用排序
        self.result_table.setSortingEnabled(True)

class SqlQueryDialog(QDialog):
    """
    SQL查询对话框
    """

    def __init__(self, parent=None):
        """
        初始化SQL查询对话框

        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self.config_manager = get_config_manager()
        self.data_service = get_data_service()
        self.security_utils = get_security_utils()
        self.history_manager = get_query_history_manager()
        self.thread_pool = QThreadPool()
        self.setWindowTitle("SQL查询工具")
        self.resize(1200, 800)  # 增大窗口尺寸
        self.setModal(False)

        # 布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # 数据库连接区域
        db_layout = QHBoxLayout()
        self.db_path_label = QLabel("已连接到配置的数据库")
        self.db_path_label.setStyleSheet("color: green;")
        connect_btn = QPushButton("重新连接")
        connect_btn.clicked.connect(self.reconnect_database)
        
        # 添加新标签页按钮
        new_tab_btn = QPushButton("新建查询")
        new_tab_btn.clicked.connect(self.new_query_tab)
        
        # 添加历史按钮
        history_btn = QPushButton("历史")
        history_btn.clicked.connect(self.show_query_history)
        history_btn.setStyleSheet("background-color: #FF9800; color: white;")
        
        db_layout.addWidget(self.db_path_label)
        db_layout.addStretch()
        db_layout.addWidget(history_btn)
        db_layout.addWidget(new_tab_btn)
        db_layout.addWidget(connect_btn)
        self.main_layout.addLayout(db_layout)

        # 创建水平分割器，左侧为对象浏览器，右侧为查询区域
        main_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧对象浏览器
        self.object_browser = QWidget()
        object_browser_layout = QVBoxLayout(self.object_browser)
        
        # 对象浏览器标题
        browser_title = QLabel("数据库对象")
        browser_title.setFont(QFont("Arial", 10, QFont.Bold))
        object_browser_layout.addWidget(browser_title)
        
        # 树状控件
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("对象")
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.show_object_context_menu)
        self.tree_widget.itemDoubleClicked.connect(self.on_object_double_clicked)
        object_browser_layout.addWidget(self.tree_widget)
        
        main_splitter.addWidget(self.object_browser)
        main_splitter.setSizes([250, 950])  # 设置初始大小
        
        # 右侧查询区域
        query_area = QWidget()
        query_layout = QVBoxLayout(query_area)
        
        # 标签页控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        query_layout.addWidget(self.tab_widget)
        
        # 导出按钮
        export_btn = QPushButton("导出数据")
        export_btn.clicked.connect(self.show_export_menu)
        export_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 10px;")
        query_layout.addWidget(export_btn)
        
        main_splitter.addWidget(query_area)
        self.main_layout.addWidget(main_splitter)
        
        # 状态栏
        self.status_bar = QStatusBar()
        
        # 添加状态栏组件
        self.status_labels = {
            'connection': QLabel("连接: 就绪"),
            'query': QLabel("查询: -"),
            'results': QLabel("结果: 0"),
            'time': QLabel("时间: 0ms"),
            'server': QLabel("服务器: -"),
            'status': QLabel("就绪")
        }
        
        # 设置样式
        for label in self.status_labels.values():
            label.setMinimumWidth(120)
            label.setAlignment(Qt.AlignCenter)
            self.status_bar.addWidget(label)
        
        # 右侧状态信息
        self.status_bar.addPermanentWidget(self.status_labels['status'])
        
        self.main_layout.addWidget(self.status_bar)
        
        # 创建导出菜单
        self.export_menu = QMenu()
        self.create_export_actions()
        
        # 创建默认标签页（不弹出输入框，使用默认名称）
        self.create_default_query_tab()
        
        # 延迟加载数据库对象（使用定时器，避免阻塞UI）
        from PySide2.QtCore import QTimer
        QTimer.singleShot(100, self.load_database_objects_async)

    def create_export_actions(self):
        """
        创建导出菜单动作
        """
        export_csv_action = QAction("导出为CSV文件", self)
        export_csv_action.triggered.connect(lambda: self.export_data('csv'))
        
        export_excel_action = QAction("导出为Excel文件", self)
        export_excel_action.triggered.connect(lambda: self.export_data('excel'))
        
        export_txt_action = QAction("导出为文本文件(TXT)", self)
        export_txt_action.triggered.connect(lambda: self.export_data('txt'))
        
        self.export_menu.addAction(export_csv_action)
        self.export_menu.addAction(export_excel_action)
        self.export_menu.addAction(export_txt_action)

    def create_default_query_tab(self):
        """
        创建默认查询标签页（初始化时使用，不弹出输入框）
        """
        tab_name = "查询 1"
        query_tab = QueryTab(tab_name, self)
        tab_index = self.tab_widget.addTab(query_tab, tab_name)
        self.tab_widget.setCurrentIndex(tab_index)
        # 不立即加载表信息，延迟到数据库对象加载完成后
    
    def new_query_tab(self):
        """
        创建新的查询标签页（手动创建时弹出输入框）
        """
        tab_count = self.tab_widget.count() + 1
        tab_name = f"查询 {tab_count}"
        
        # 提示用户输入标签页名称
        name, ok = QInputDialog.getText(self, "新建查询", "输入查询名称:", text=tab_name)
        if ok and name:
            tab_name = name
        
        # 创建新的查询标签页
        query_tab = QueryTab(tab_name, self)
        tab_index = self.tab_widget.addTab(query_tab, tab_name)
        self.tab_widget.setCurrentIndex(tab_index)
        
        # 显示数据库表信息
        self.show_available_tables_in_tab(query_tab)

    def close_tab(self, index):
        """
        关闭标签页
        """
        if self.tab_widget.count() <= 1:
            QMessageBox.warning(self, "警告", "至少需要保留一个查询标签页")
            return
        
        self.tab_widget.removeTab(index)

    def on_tab_changed(self, index):
        """
        标签页切换时的处理
        """
        if index >= 0:
            current_tab = self.tab_widget.widget(index)
            if current_tab:
                self.status_bar.showMessage(f"当前查询: {current_tab.tab_name}")

    def get_current_tab(self):
        """
        获取当前标签页
        """
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            return self.tab_widget.widget(current_index)
        return None

    def update_status_bar(self, key, value):
        """
        更新状态栏信息
        """
        if key in self.status_labels:
            self.status_labels[key].setText(f"{key}: {value}")
        elif key == 'message':
            self.status_labels['status'].setText(value)
    
    def reconnect_database(self):
        """
        重新连接数据库
        """
        try:
            # 测试数据库连接
            self.update_status_bar('connection', '连接中...')
            self.update_status_bar('message', '正在连接数据库...')
            
            success = self.data_service.test_connection()
            if success:
                self.db_path_label.setText("已重新连接到数据库")
                self.db_path_label.setStyleSheet("color: green;")
                self.update_status_bar('connection', '已连接')
                self.update_status_bar('message', '数据库连接成功')
                self.update_status_bar('server', 'Intersystems IRIS')
                QMessageBox.information(self, "连接成功", "数据库连接成功")
                # 刷新对象浏览器
                self.load_database_objects()
                # 显示可用的表
                current_tab = self.get_current_tab()
                if current_tab:
                    self.show_available_tables_in_tab(current_tab)
            else:
                self.db_path_label.setText("数据库连接失败")
                self.db_path_label.setStyleSheet("color: red;")
                self.update_status_bar('connection', '连接失败')
                self.update_status_bar('message', '数据库连接失败')
                QMessageBox.critical(self, "连接失败", "无法连接到数据库，请检查配置")
        except Exception as e:
            self.db_path_label.setText("连接失败")
            self.db_path_label.setStyleSheet("color: red;")
            self.update_status_bar('connection', '连接失败')
            self.update_status_bar('message', f'连接错误: {str(e)}')
            QMessageBox.critical(self, "数据库连接错误", f"连接数据库失败:\n{str(e)}")

    def show_available_tables_in_tab(self, tab):
        """
        在指定标签页中显示数据库中的可用表（异步加载）
        """
        # 使用现有的异步加载机制，避免阻塞主线程
        self.load_database_objects_async()
        
        # 更新状态栏
        self.status_bar.showMessage("正在加载数据库表信息...")

    def load_database_objects_async(self):
        """
        异步加载数据库对象（使用后台线程，避免阻塞UI）
        使用 Qt.AutoConnection 确保信号安全，线程完成后自动清理
        """
        self.status_bar.showMessage("正在加载数据库对象...")
        
        # 创建后台线程加载数据库对象
        from PySide2.QtCore import QThread, Signal
        
        class DatabaseObjectLoader(QThread):
            """数据库对象加载线程"""
            objects_loaded = Signal(object, object)  # 表列表, 视图列表
            load_error = Signal(str)
            
            def __init__(self, data_service):
                super().__init__()
                self.data_service = data_service
            
            def run(self):
                try:
                    # 查询表
                    tables = self.data_service.get_data(
                        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
                    )
                    # 查询视图
                    views = self.data_service.get_data(
                        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'VIEW'"
                    )
                    self.objects_loaded.emit(tables, views)
                except Exception as e:
                    self.load_error.emit(str(e))
        
        # 创建并启动加载线程（使用 Qt.AutoConnection 和 finished 信号清理）
        self.db_loader = DatabaseObjectLoader(self.data_service)
        self.db_loader.objects_loaded.connect(self.on_database_objects_loaded, Qt.AutoConnection)
        self.db_loader.load_error.connect(self.on_database_objects_error, Qt.AutoConnection)
        # 线程完成后自动删除，避免内存泄漏
        self.db_loader.finished.connect(self.db_loader.deleteLater)
        self.db_loader.start()
    
    def on_database_objects_loaded(self, tables_result, views_result):
        """
        数据库对象加载完成回调
        """
        try:
            # 清空树状控件
            self.tree_widget.clear()
            
            # 创建数据库根节点
            db_root = QTreeWidgetItem(self.tree_widget)
            db_root.setText(0, "数据库对象")
            db_root.setExpanded(True)
            
            # 创建表节点
            tables_node = QTreeWidgetItem(db_root)
            tables_node.setText(0, "表")
            tables_node.setData(0, Qt.UserRole, "tables")
            
            # 创建视图节点
            views_node = QTreeWidgetItem(db_root)
            views_node.setText(0, "视图")
            views_node.setData(0, Qt.UserRole, "views")
            
            # 添加表
            if tables_result:
                for row in tables_result:
                    table_name = row.get('TABLE_NAME')
                    if table_name:
                        table_item = QTreeWidgetItem(tables_node)
                        table_item.setText(0, table_name)
                        table_item.setData(0, Qt.UserRole, f"table:{table_name}")
                tables_node.setExpanded(True)
            
            # 添加视图
            if views_result:
                for row in views_result:
                    view_name = row.get('TABLE_NAME')
                    if view_name:
                        view_item = QTreeWidgetItem(views_node)
                        view_item.setText(0, view_name)
                        view_item.setData(0, Qt.UserRole, f"view:{view_name}")
                views_node.setExpanded(True)
            
            # 更新第一个标签页的表信息
            current_tab = self.get_current_tab()
            if current_tab:
                self.show_available_tables_in_tab(current_tab)
            
            self.status_bar.showMessage(f"数据库对象加载完成 (表: {len(tables_result) if tables_result else 0}, 视图: {len(views_result) if views_result else 0})")
            
        except Exception as e:
            self.status_bar.showMessage(f"显示数据库对象失败: {str(e)}")
    
    def on_database_objects_error(self, error_message):
        """
        数据库对象加载失败回调
        """
        self.status_bar.showMessage(f"加载数据库对象失败: {error_message}")
    
    def load_database_objects(self):
        """
        加载数据库对象到左侧浏览器（同步版本，供手动刷新使用）
        """
        try:
            # 清空树状控件
            self.tree_widget.clear()
            
            # 创建数据库根节点
            db_root = QTreeWidgetItem(self.tree_widget)
            db_root.setText(0, "数据库对象")
            db_root.setExpanded(True)
            
            # 创建表节点
            tables_node = QTreeWidgetItem(db_root)
            tables_node.setText(0, "表")
            tables_node.setData(0, Qt.UserRole, "tables")
            
            # 创建视图节点
            views_node = QTreeWidgetItem(db_root)
            views_node.setText(0, "视图")
            views_node.setData(0, Qt.UserRole, "views")
            
            # 查询数据库中的表
            tables_result = self.data_service.get_data("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
            if tables_result:
                for row in tables_result:
                    table_name = row.get('TABLE_NAME')
                    if table_name:
                        table_item = QTreeWidgetItem(tables_node)
                        table_item.setText(0, table_name)
                        table_item.setData(0, Qt.UserRole, f"table:{table_name}")
                tables_node.setExpanded(True)
            
            # 查询数据库中的视图
            views_result = self.data_service.get_data("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'VIEW'")
            if views_result:
                for row in views_result:
                    view_name = row.get('TABLE_NAME')
                    if view_name:
                        view_item = QTreeWidgetItem(views_node)
                        view_item.setText(0, view_name)
                        view_item.setData(0, Qt.UserRole, f"view:{view_name}")
                views_node.setExpanded(True)
            
            self.status_bar.showMessage("数据库对象加载完成")
        except Exception as e:
            self.status_bar.showMessage(f"加载数据库对象失败: {str(e)}")

    def on_object_double_clicked(self, item, column):
        """
        处理对象双击事件
        """
        try:
            item_data = item.data(0, Qt.UserRole)
            if item_data and item_data.startswith('table:'):
                table_name = item_data.split(':', 1)[1]
                # 生成SELECT语句
                select_sql = f"SELECT * FROM {table_name} LIMIT 100;"
                
                # 获取当前标签页并插入SQL
                current_tab = self.get_current_tab()
                if current_tab:
                    current_tab.sql_edit.setText(select_sql)
                    self.status_bar.showMessage(f"已为表 {table_name} 生成查询语句")
            elif item_data and item_data.startswith('view:'):
                view_name = item_data.split(':', 1)[1]
                # 生成SELECT语句
                select_sql = f"SELECT * FROM {view_name} LIMIT 100;"
                
                # 获取当前标签页并插入SQL
                current_tab = self.get_current_tab()
                if current_tab:
                    current_tab.sql_edit.setText(select_sql)
                    self.status_bar.showMessage(f"已为视图 {view_name} 生成查询语句")
        except Exception as e:
            self.status_bar.showMessage(f"处理对象双击事件失败: {str(e)}")

    def show_object_context_menu(self, pos):
        """
        显示对象上下文菜单
        """
        try:
            item = self.tree_widget.itemAt(pos)
            if not item:
                return
            
            item_data = item.data(0, Qt.UserRole)
            if not item_data:
                return
            
            # 创建上下文菜单
            context_menu = QMenu()
            
            if item_data.startswith('table:') or item_data.startswith('view:'):
                # 表或视图的菜单
                object_name = item_data.split(':', 1)[1]
                
                # 查看数据菜单项
                view_data_action = QAction(f"查看 {object_name} 的数据", self)
                view_data_action.triggered.connect(lambda: self.generate_select_statement(object_name))
                context_menu.addAction(view_data_action)
                
                # 查看结构菜单项
                view_structure_action = QAction(f"查看 {object_name} 的结构", self)
                view_structure_action.triggered.connect(lambda: self.generate_describe_statement(object_name))
                context_menu.addAction(view_structure_action)
            
            if context_menu.actions():
                context_menu.exec_(self.tree_widget.mapToGlobal(pos))
        except Exception as e:
            self.status_bar.showMessage(f"显示上下文菜单失败: {str(e)}")

    def generate_select_statement(self, object_name):
        """
        生成SELECT语句
        """
        select_sql = f"SELECT * FROM {object_name} LIMIT 100;"
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.sql_edit.setText(select_sql)
            self.status_bar.showMessage(f"已为 {object_name} 生成查询语句")

    def generate_describe_statement(self, object_name):
        """
        生成DESCRIBE语句
        """
        describe_sql = f"SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH \
FROM INFORMATION_SCHEMA.COLUMNS \
WHERE TABLE_NAME = '{object_name}';"
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.sql_edit.setText(describe_sql)
            self.status_bar.showMessage(f"已为 {object_name} 生成结构查询语句")

    def execute_query_in_tab(self, tab):
        """
        在指定标签页中执行SQL查询
        """
        try:
            sql = tab.sql_edit.toPlainText().strip()
            if not sql:
                self.update_status_bar('message', '请输入SQL查询语句')
                return

            # 验证SQL查询的安全性
            if not self.security_utils.validate_sql_query(sql):
                self.update_status_bar('message', 'SQL查询包含危险操作，不允许执行')
                logger.warning(f"尝试执行危险的SQL查询: {sql}")
                QMessageBox.warning(self, "安全警告", "SQL查询包含危险操作，不允许执行")
                return

            # 清理SQL输入
            sanitized_sql = self.security_utils.sanitize_sql_input(sql)
            logger.info(f"执行SQL查询: {sanitized_sql}")

            # 重置分页信息
            tab.current_page = 1
            
            # 显示加载状态
            tab.is_querying = True
            tab.progress_bar.setVisible(True)
            
            # 更新状态栏
            self.update_status_bar('query', '执行中...')
            self.update_status_bar('results', '0')
            self.update_status_bar('time', '0ms')
            self.update_status_bar('message', '正在执行查询...')

            # 记录开始时间
            import time
            tab.query_start_time = time.time()

            # 创建工作线程（传递 tab 引用）
            worker = QueryWorker(sanitized_sql, tab=tab)
            worker.signals.result.connect(self.on_query_finished)
            worker.signals.error.connect(self.on_query_error)

            # 启动线程
            self.thread_pool.start(worker)
            
        except Exception as e:
            error_msg = f"执行查询失败: {str(e)}"
            logger.error(error_msg)
            self.update_status_bar('message', f'查询失败: {str(e)}')
            QMessageBox.critical(self, "SQL执行错误", f"执行SQL语句时出错:\n{str(e)}")
            tab.is_querying = False
            tab.progress_bar.setVisible(False)

    def on_query_finished(self, result):
        """
        查询完成回调 - 从 worker 获取 tab 引用
        """
        # 获取当前正在执行的 worker
        for i in range(self.thread_pool.activeThreadCount()):
            # 通过结果匹配找到对应的 worker
            pass

        # 由于可能有多个并发查询，我们使用 sender() 获取发送者
        worker = self.sender()
        if worker and hasattr(worker, 'tab'):
            self._process_query_result(worker.tab, result)

    def on_query_error(self, error_message):
        """
        查询错误回调 - 从 worker 获取 tab 引用
        """
        worker = self.sender()
        if worker and hasattr(worker, 'tab'):
            self._handle_query_error(worker.tab, error_message)

    def _process_query_result(self, tab, result):
        """
        处理查询结果 - 内部方法

        Args:
            tab: 查询标签页
            result: 查询结果
        """
        try:
            tab.is_querying = False
            tab.progress_bar.setVisible(False)

            # 计算执行时间
            import time
            execution_time = 0
            if hasattr(tab, 'query_start_time'):
                execution_time = (time.time() - tab.query_start_time) * 1000

            if result is None:
                self.update_status_bar('message', '查询执行失败')
                QMessageBox.critical(self, "查询失败", "查询执行失败，请检查SQL语句")
                return

            # 记录查询历史
            sql = tab.sql_edit.toPlainText().strip()
            self.history_manager.add_history(
                sql=sql,
                execution_time_ms=execution_time,
                row_count=len(result),
                success=True
            )

            tab.total_rows = len(result)

            # 计算总页数
            tab.total_pages = (tab.total_rows + tab.page_size - 1) // tab.page_size

            # 存储所有数据
            if result:
                columns = list(result[0].keys())
                rows = []
                for row in result:
                    row_data = []
                    for col in columns:
                        row_data.append(row.get(col, ""))
                    rows.append(row_data)
                tab.all_data = {
                    'columns': columns,
                    'rows': rows
                }
                # 获取当前页数据
                tab.load_page_data()
            else:
                tab.all_data = None
                tab.current_data = None

            # 显示结果
            tab.display_result(result[:tab.page_size] if result else [])

            # 更新信息标签
            tab.row_count_label.setText(f"行数: {tab.total_rows}")
            tab.column_count_label.setText(f"列数: {len(result[0].keys()) if result else 0}")
            tab.query_time_label.setText(f"查询时间: {execution_time:.2f}ms")

            # 更新分页信息
            tab.update_pagination()

            # 更新状态栏
            self.update_status_bar('query', '完成')
            self.update_status_bar('results', str(tab.total_rows))
            self.update_status_bar('time', f'{execution_time:.2f}ms')
            self.update_status_bar('message', f'查询成功，返回 {tab.total_rows} 行')

            logger.info(f"查询成功，返回{tab.total_rows}条记录，执行时间{execution_time:.2f}ms")
        except Exception as e:
            error_msg = f"处理查询结果失败: {str(e)}"
            logger.error(error_msg)
            self.update_status_bar('message', f'处理结果失败: {str(e)}')
            QMessageBox.critical(self, "错误", f"处理查询结果时出错:\n{str(e)}")

    def _handle_query_error(self, tab, error_message):
        """
        处理查询错误 - 内部方法

        Args:
            tab: 查询标签页
            error_message: 错误信息
        """
        tab.is_querying = False
        tab.progress_bar.setVisible(False)

        # 记录失败的查询历史
        sql = tab.sql_edit.toPlainText().strip()
        import time
        execution_time = 0
        if hasattr(tab, 'query_start_time'):
            execution_time = (time.time() - tab.query_start_time) * 1000

        self.history_manager.add_history(
            sql=sql,
            execution_time_ms=execution_time,
            row_count=0,
            success=False,
            error_message=error_message
        )

        error_msg = f"执行查询失败: {error_message}"
        logger.error(error_msg)
        self.update_status_bar('query', '失败')
        self.update_status_bar('message', f'查询失败: {error_message}')
        QMessageBox.critical(self, "SQL执行错误", f"执行SQL语句时出错:\n{error_message}")

    def show_query_history(self):
        """
        显示查询历史对话框
        """
        try:
            history_dialog = QueryHistoryDialog(self)
            if history_dialog.exec_() == QueryHistoryDialog.Accepted:
                selected_sql = history_dialog.get_selected_sql()
                if selected_sql:
                    # 获取当前标签页并设置SQL
                    current_tab = self.get_current_tab()
                    if current_tab:
                        current_tab.sql_edit.setText(selected_sql)
                        self.status_bar.showMessage(f"已从历史记录加载SQL")
                        logger.info(f"从历史记录加载SQL: {selected_sql[:50]}...")
        except Exception as e:
            logger.error(f"显示查询历史对话框失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"无法打开历史记录:\n{str(e)}")

    def show_available_tables(self):
        """
        显示数据库中的可用表
        """
        current_tab = self.get_current_tab()
        if current_tab:
            self.show_available_tables_in_tab(current_tab)

    def show_export_menu(self):
        """
        显示导出菜单
        """
        current_tab = self.get_current_tab()
        if not current_tab or not current_tab.all_data or not current_tab.all_data['rows']:
            QMessageBox.warning(self, "无数据", "没有可导出的数据，请先执行查询")
            return
            
        # 在导出按钮下方显示菜单
        export_btn = self.sender()
        if export_btn:
            self.export_menu.exec_(export_btn.mapToGlobal(export_btn.rect().bottomLeft()))

    def export_data(self, format_type):
        """
        导出数据到指定格式
        """
        current_tab = self.get_current_tab()
        if not current_tab or not current_tab.all_data:
            return
            
        # 设置默认文件名
        default_name = f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if format_type == 'csv':
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存为CSV文件", 
                f"{default_name}.csv",
                "CSV文件 (*.csv);;所有文件 (*.*)"
            )
            if file_path:
                self.export_to_csv(file_path, current_tab.all_data)
                
        elif format_type == 'excel':
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存为Excel文件", 
                f"{default_name}.xlsx",
                "Excel文件 (*.xlsx *.xls);;所有文件 (*.*)"
            )
            if file_path:
                self.export_to_excel(file_path, current_tab.all_data)
                
        elif format_type == 'txt':
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存为文本文件", 
                f"{default_name}.txt",
                "文本文件 (*.txt);;所有文件 (*.*)"
            )
            if file_path:
                self.export_to_txt(file_path, current_tab.all_data)

    def export_to_csv(self, file_path, data):
        """
        导出为CSV文件
        """
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # 写入列标题
                writer.writerow(data['columns'])
                
                # 写入数据行
                for row in data['rows']:
                    writer.writerow(row)
                    
            QMessageBox.information(self, "导出成功", f"数据已成功导出到:\n{file_path}")
            self.status_bar.showMessage(f"数据已导出到CSV文件: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出CSV文件时出错:\n{str(e)}")

    def export_to_excel(self, file_path, data):
        """
        导出为Excel文件
        """
        try:
            # 使用pandas创建DataFrame并导出
            import pandas as pd
            
            df = pd.DataFrame(
                data['rows'],
                columns=data['columns']
            )
            
            # 根据文件扩展名选择引擎
            if file_path.endswith('.xlsx'):
                df.to_excel(file_path, index=False, engine='openpyxl')
            else:
                df.to_excel(file_path, index=False)
                
            QMessageBox.information(self, "导出成功", f"数据已成功导出到:\n{file_path}")
            self.status_bar.showMessage(f"数据已导出到Excel文件: {file_path}")
            
        except ImportError:
            QMessageBox.warning(
                self, "缺少依赖库", 
                "导出Excel需要pandas和openpyxl库。\n"
                "请安装: pip install pandas openpyxl"
            )
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出Excel文件时出错:\n{str(e)}")

    def export_to_txt(self, file_path, data):
        """
        导出为文本文件
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as txtfile:
                # 写入列标题
                txtfile.write("\t".join(data['columns']) + "\n")
                
                # 写入数据行
                for row in data['rows']:
                    line = "\t".join(str(cell) if cell is not None else "NULL" for cell in row)
                    txtfile.write(line + "\n")
                    
            QMessageBox.information(self, "导出成功", f"数据已成功导出到:\n{file_path}")
            self.status_bar.showMessage(f"数据已导出到文本文件: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出文本文件时出错:\n{str(e)}")
