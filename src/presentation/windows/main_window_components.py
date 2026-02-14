#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主窗口UI组件模块

包含统计卡片、活动项、历史记录项等可复用UI组件
作为重构第一阶段，从 main_window.py 中独立出来
"""

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QGroupBox, QVBoxLayout, QWidget
)

from src.presentation.windows.ui_constants import COLORS


class MainWindowComponents:
    """
    主窗口UI组件创建类

    提供可复用的UI组件创建方法，与主窗口逻辑解耦
    通过回调函数与主窗口通信
    """

    def __init__(self, scaled_callback):
        """
        初始化组件类

        Args:
            scaled_callback: 缩放函数回调，用于适配不同分辨率
        """
        self.scaled = scaled_callback

    def _create_stat_card(self, title, value, subtitle):
        """
        创建统计卡片

        Args:
            title: 卡片标题
            value: 统计数值
            subtitle: 副标题说明

        Returns:
            QGroupBox: 统计卡片部件
        """
        card = QGroupBox()
        card.setObjectName('stat_card')
        layout = QVBoxLayout(card)
        layout.setContentsMargins(
            self.scaled(16), self.scaled(16),
            self.scaled(16), self.scaled(16)
        )

        title_label = QLabel(title)
        title_label.setObjectName('stat_title')
        layout.addWidget(title_label)

        value_label = QLabel(str(value))
        value_label.setObjectName('stat_value')
        layout.addWidget(value_label)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName('stat_subtitle')
        layout.addWidget(subtitle_label)

        layout.addStretch()

        return card

    def _create_activity_item(self, icon, title, desc, time):
        """
        创建活动项

        Args:
            icon: 图标emoji
            title: 活动标题
            desc: 活动描述
            time: 时间字符串

        Returns:
            QWidget: 活动项部件
        """
        item = QWidget()
        layout = QHBoxLayout(item)
        layout.setContentsMargins(0, self.scaled(8), 0, self.scaled(8))

        # 图标
        icon_label = QLabel(icon)
        icon_label.setObjectName('activity_icon')
        icon_label.setFixedWidth(self.scaled(32))
        layout.addWidget(icon_label)

        # 内容区
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(self.scaled(4))

        title_label = QLabel(title)
        title_label.setObjectName('activity_title')
        content_layout.addWidget(title_label)

        desc_label = QLabel(desc)
        desc_label.setObjectName('activity_desc')
        content_layout.addWidget(desc_label)

        layout.addWidget(content, 1)

        # 时间
        time_label = QLabel(time)
        time_label.setObjectName('activity_time')
        layout.addWidget(time_label)

        return item

    def _create_history_item(self, sql, rows, time, status):
        """
        创建历史记录项

        Args:
            sql: SQL语句
            rows: 影响行数
            time: 执行时间
            status: 执行状态（'success', 'warning', 'error'）

        Returns:
            QWidget: 历史记录项部件
        """
        item = QWidget()
        layout = QHBoxLayout(item)
        layout.setContentsMargins(0, self.scaled(12), 0, self.scaled(12))

        # 状态图标
        status_icons = {
            'success': '✅',
            'warning': '⚠️',
            'error': '❌'
        }
        status_icon = QLabel(status_icons.get(status, '❓'))
        status_icon.setObjectName('history_status')
        layout.addWidget(status_icon)

        # SQL内容（截断显示）
        display_sql = sql[:60] + '...' if len(sql) > 60 else sql
        sql_label = QLabel(display_sql)
        sql_label.setObjectName('history_sql')
        layout.addWidget(sql_label, 1)

        # 行数
        rows_label = QLabel(f'{rows} 行')
        rows_label.setObjectName('history_rows')
        layout.addWidget(rows_label)

        # 时间
        time_label = QLabel(time)
        time_label.setObjectName('history_time')
        layout.addWidget(time_label)

        return item
