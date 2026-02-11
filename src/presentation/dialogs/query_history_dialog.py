#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
查询历史对话框

用于显示、搜索和选择SQL查询历史记录
"""

import logging
from typing import Optional

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                               QListWidgetItem, QPushButton, QLineEdit,
                               QLabel, QMessageBox, QCheckBox, QAbstractItemView)

from src.business.services.query_history_manager import get_query_history_manager

logger = logging.getLogger(__name__)


class QueryHistoryDialog(QDialog):
    """
    查询历史对话框
    
    显示SQL查询历史记录，支持搜索、选择和复用
    """
    
    def __init__(self, parent=None):
        """
        初始化查询历史对话框
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        
        self.history_manager = get_query_history_manager()
        self.selected_sql = None
        
        self.setWindowTitle("查询历史")
        self.resize(800, 600)
        
        self._setup_ui()
        self._load_history()
        
        logger.info("查询历史对话框初始化完成")
    
    def _setup_ui(self):
        """
        设置UI界面
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 标题
        title_label = QLabel("SQL查询历史记录")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 搜索区域
        search_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入关键词搜索历史记录...")
        self.search_edit.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_edit)
        
        self.case_sensitive_check = QCheckBox("区分大小写")
        search_layout.addWidget(self.case_sensitive_check)
        
        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self.on_search_clicked)
        search_layout.addWidget(search_btn)
        
        clear_search_btn = QPushButton("清空")
        clear_search_btn.clicked.connect(self.on_clear_search)
        search_layout.addWidget(clear_search_btn)
        
        layout.addLayout(search_layout)
        
        # 历史记录列表
        self.history_list = QListWidget()
        self.history_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.history_list.setAlternatingRowColors(True)
        self.history_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.history_list.setStyleSheet("""
            QListWidget {
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10pt;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e8f4f8;
            }
        """)
        layout.addWidget(self.history_list)
        
        # 统计信息
        self.stats_label = QLabel("共 0 条历史记录")
        layout.addWidget(self.stats_label)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.use_btn = QPushButton("使用此SQL")
        self.use_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        self.use_btn.clicked.connect(self.on_use_clicked)
        button_layout.addWidget(self.use_btn)
        
        self.view_btn = QPushButton("查看详情")
        self.view_btn.clicked.connect(self.on_view_clicked)
        button_layout.addWidget(self.view_btn)
        
        button_layout.addStretch()
        
        self.delete_btn = QPushButton("删除")
        self.delete_btn.setStyleSheet("background-color: #f44336; color: white;")
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        button_layout.addWidget(self.delete_btn)
        
        self.clear_all_btn = QPushButton("清空全部")
        self.clear_all_btn.setStyleSheet("background-color: #ff9800; color: white;")
        self.clear_all_btn.clicked.connect(self.on_clear_all_clicked)
        button_layout.addWidget(self.clear_all_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # 详情显示区域
        self.detail_label = QLabel("选择一条记录查看详情")
        self.detail_label.setWordWrap(True)
        self.detail_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10pt;
                min-height: 60px;
            }
        """)
        layout.addWidget(self.detail_label)
        
        # 连接列表选择信号
        self.history_list.itemSelectionChanged.connect(self.on_selection_changed)
    
    def _load_history(self):
        """
        加载历史记录到列表
        """
        self.history_list.clear()
        
        history = self.history_manager.get_history()
        
        for entry in history:
            display_text = self.history_manager.get_formatted_history_text(entry)
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, entry)  # 存储完整数据
            item.setToolTip(entry.get('sql', ''))  # 鼠标悬停提示
            self.history_list.addItem(item)
        
        # 更新统计信息
        count = len(history)
        self.stats_label.setText(f"共 {count} 条历史记录")
        
        logger.info(f"加载了 {count} 条历史记录")
    
    def on_search_changed(self, text):
        """
        搜索文本改变时的处理
        """
        if not text:
            self._load_history()
        else:
            self.on_search_clicked()
    
    def on_search_clicked(self):
        """
        搜索按钮点击处理
        """
        keyword = self.search_edit.text().strip()
        
        if not keyword:
            self._load_history()
            return
        
        # 搜索历史记录
        case_sensitive = self.case_sensitive_check.isChecked()
        results = self.history_manager.search_history(keyword, case_sensitive)
        
        # 清空列表并显示结果
        self.history_list.clear()
        
        for entry in results:
            display_text = self.history_manager.get_formatted_history_text(entry)
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, entry)
            item.setToolTip(entry.get('sql', ''))
            self.history_list.addItem(item)
        
        # 更新统计信息
        count = len(results)
        total = self.history_manager.get_history_count()
        self.stats_label.setText(f"搜索 '{keyword}' 找到 {count} 条记录（共 {total} 条）")
        
        logger.info(f"搜索 '{keyword}' 找到 {count} 条记录")
    
    def on_clear_search(self):
        """
        清空搜索
        """
        self.search_edit.clear()
        self._load_history()
    
    def on_selection_changed(self):
        """
        列表选择改变时的处理
        """
        current_item = self.history_list.currentItem()
        
        if current_item:
            entry = current_item.data(Qt.UserRole)
            sql = entry.get('sql', '')
            execution_time = entry.get('execution_time_ms', 0)
            row_count = entry.get('row_count', 0)
            timestamp = entry.get('timestamp', '')
            success = entry.get('success', True)
            error_message = entry.get('error_message', '')
            
            # 构建详情文本
            status = "执行成功" if success else "执行失败"
            detail_text = f"""
<b>执行时间:</b> {timestamp}<br>
<b>执行状态:</b> {status}<br>
<b>耗时:</b> {execution_time:.2f} ms<br>
<b>返回行数:</b> {row_count}<br>
<b>SQL语句:</b><br>
<pre style='background-color: #f0f0f0; padding: 8px; border-radius: 4px;'>{sql}</pre>
            """
            
            if error_message:
                detail_text += f"<br><b>错误信息:</b> {error_message}"
            
            self.detail_label.setText(detail_text)
            
            # 启用按钮
            self.use_btn.setEnabled(True)
            self.view_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
        else:
            self.detail_label.setText("选择一条记录查看详情")
            self.use_btn.setEnabled(False)
            self.view_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
    
    def on_item_double_clicked(self, item):
        """
        列表项双击处理
        """
        self.on_use_clicked()
    
    def on_use_clicked(self):
        """
        使用此SQL按钮点击处理
        """
        current_item = self.history_list.currentItem()
        
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择一条历史记录")
            return
        
        entry = current_item.data(Qt.UserRole)
        self.selected_sql = entry.get('sql', '')
        
        logger.info(f"用户选择了历史SQL: {self.selected_sql[:50]}...")
        
        self.accept()
    
    def on_view_clicked(self):
        """
        查看详情按钮点击处理
        """
        current_item = self.history_list.currentItem()
        
        if not current_item:
            return
        
        entry = current_item.data(Qt.UserRole)
        sql = entry.get('sql', '')
        
        # 创建详细信息对话框
        from PySide2.QtWidgets import QTextEdit
        
        detail_dialog = QDialog(self)
        detail_dialog.setWindowTitle("SQL详情")
        detail_dialog.resize(800, 600)
        
        layout = QVBoxLayout(detail_dialog)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(sql)
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11pt;
                background-color: #f8f8f8;
                padding: 10px;
            }
        """)
        layout.addWidget(text_edit)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(detail_dialog.accept)
        layout.addWidget(close_btn)
        
        detail_dialog.exec_()
    
    def on_delete_clicked(self):
        """
        删除按钮点击处理
        """
        current_row = self.history_list.currentRow()
        
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择一条历史记录")
            return
        
        reply = QMessageBox.question(
            self, 
            "确认删除", 
            "确定要删除选中的历史记录吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.history_manager.delete_history_entry(current_row):
                self.history_list.takeItem(current_row)
                count = self.history_manager.get_history_count()
                self.stats_label.setText(f"共 {count} 条历史记录")
                self.detail_label.setText("选择一条记录查看详情")
                logger.info(f"删除了第 {current_row} 条历史记录")
    
    def on_clear_all_clicked(self):
        """
        清空全部按钮点击处理
        """
        count = self.history_manager.get_history_count()
        
        if count == 0:
            QMessageBox.information(self, "提示", "历史记录已为空")
            return
        
        reply = QMessageBox.question(
            self, 
            "确认清空", 
            f"确定要清空所有 {count} 条历史记录吗？\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.history_manager.clear_history()
            self.history_list.clear()
            self.stats_label.setText("共 0 条历史记录")
            self.detail_label.setText("选择一条记录查看详情")
            logger.info("清空了所有历史记录")
    
    def get_selected_sql(self) -> Optional[str]:
        """
        获取用户选择的SQL语句
        
        Returns:
            选中的SQL语句，如果用户取消则返回None
        """
        return self.selected_sql
