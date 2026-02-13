#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
页面基类模块

提供所有页面的公共功能。
"""

from PySide2.QtWidgets import QWidget


class BasePage(QWidget):
    """页面基类"""
    
    def __init__(self, main_window, parent=None):
        """
        初始化页面基类
        
        Args:
            main_window: 主窗口实例
            parent: 父部件
        """
        super().__init__(parent)
        self.main_window = main_window
        self.scaling_manager = main_window.scaling_manager
        self.config_manager = main_window.config_manager
        self.data_service = main_window.data_service
        self.query_history_manager = main_window.query_history_manager
        
    def scaled(self, value):
        """
        根据当前缩放比例计算实际像素值
        
        Args:
            value: 基础像素值
            
        Returns:
            int: 缩放后的像素值
        """
        return self.scaling_manager.scale(value)
    
    def _create_stat_card(self, title, value, subtitle):
        """创建统计卡片"""
        from PySide2.QtWidgets import QFrame, QVBoxLayout, QLabel
        
        card = QFrame()
        card.setObjectName('stat_card')
        card.setMinimumWidth(self.scaled(200))
        
        layout = QVBoxLayout(card)
        layout.setSpacing(self.scaled(8))
        
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
        from PySide2.QtWidgets import QWidget, QHBoxLayout, QLabel
        from PySide2.QtCore import Qt
        from src.presentation.windows.main_window import COLORS
        
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
    
    def _create_history_item(self, sql, rows, time_str, status):
        """创建历史记录项"""
        from PySide2.QtWidgets import QWidget, QHBoxLayout, QLabel
        from src.presentation.windows.main_window import COLORS
        
        item = QWidget()
        item_layout = QHBoxLayout(item)
        item_layout.setContentsMargins(0, 8, 0, 8)
        
        lbl_sql = QLabel(sql[:50] + '...' if len(sql) > 50 else sql)
        lbl_sql.setStyleSheet(f'color: {COLORS["primary"]}; font-family: monospace;')
        item_layout.addWidget(lbl_sql)
        
        item_layout.addStretch()
        
        lbl_rows = QLabel(rows)
        lbl_rows.setStyleSheet(f'color: {COLORS["text_secondary"]};')
        item_layout.addWidget(lbl_rows)
        
        lbl_time = QLabel(time_str)
        lbl_time.setStyleSheet(f'color: {COLORS["text_disabled"]}; font-size: 12px;')
        item_layout.addWidget(lbl_time)
        
        lbl_status = QLabel(status)
        if status == '成功':
            lbl_status.setStyleSheet(f'color: {COLORS["success"]}; font-weight: 600;')
        else:
            lbl_status.setStyleSheet(f'color: {COLORS["error"]}; font-weight: 600;')
        item_layout.addWidget(lbl_status)
        
        return item
