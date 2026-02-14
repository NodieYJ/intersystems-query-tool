#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主窗口UI组件模块

包含侧边栏、内容区、头部等UI组件的创建
采用组合模式与主窗口解耦
"""

import logging
from typing import Optional, Callable

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QStackedWidget,
    QVBoxLayout, QWidget, QButtonGroup, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView
)

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


class MainWindowUI:
  """
  主窗口UI组件创建类
  
  负责创建和管理主窗口的所有UI组件
  采用组合模式与主窗口逻辑解耦
  """

  def __init__(self, main_window):
    """
    初始化UI组件类
    
    Args:
      main_window: 主窗口实例，用于访问缩放方法和页面切换
    """
    self.main_window = main_window
    self.scaled = main_window.scaled
    self._show_page_callback = main_window._show_page

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
    self.nav_group = QButtonGroup(self.main_window)
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
      btn.clicked.connect(lambda checked=False, idx=page_index: self._show_page_callback(idx))  # type: ignore
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
    """创建右侧内容区"""
    content = QFrame()
    content.setObjectName('content_area')

    layout = QVBoxLayout(content)
    layout.setContentsMargins(0, 0, 0, 0)  # type: ignore
    layout.setSpacing(0)  # type: ignore

    # 创建头部
    header = self._create_header()
    layout.addWidget(header)

    # 创建堆叠部件用于页面切换
    self.stack = QStackedWidget()
    self.stack.setObjectName('content_stack')
    layout.addWidget(self.stack, 1)

    return content

  def _create_header(self) -> QWidget:
    """创建内容区头部"""
    header = QFrame()
    header.setObjectName('content_header')
    header.setFixedHeight(self.scaled(64))  # type: ignore

    layout = QHBoxLayout(header)
    layout.setContentsMargins(self.scaled(24), 0, self.scaled(24), 0)  # type: ignore

    # 左侧：页面标题（动态更新）
    self.page_title = QLabel('📊 概览')
    self.page_title.setObjectName('page_title')
    layout.addWidget(self.page_title)

    layout.addStretch()

    # 右侧：操作按钮
    self.refresh_btn = QPushButton('🔄 刷新')
    self.refresh_btn.setObjectName('btn_secondary')
    layout.addWidget(self.refresh_btn)

    self.help_btn = QPushButton('❓ 帮助')
    self.help_btn.setObjectName('btn_secondary')
    layout.addWidget(self.help_btn)

    return header

  def _create_stat_card(self, title, value, subtitle):
    """
    创建统计卡片
    
    Args:
      title: 卡片标题
      value: 统计数值
      subtitle: 副标题说明
    """
    card = QGroupBox()
    card.setObjectName('stat_card')
    layout = QVBoxLayout(card)
    layout.setContentsMargins(self.scaled(16), self.scaled(16), self.scaled(16), self.scaled(16))  # type: ignore

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
    """
    item = QWidget()
    layout = QHBoxLayout(item)
    layout.setContentsMargins(0, self.scaled(8), 0, self.scaled(8))  # type: ignore

    # 图标
    icon_label = QLabel(icon)
    icon_label.setObjectName('activity_icon')
    icon_label.setFixedWidth(self.scaled(32))  # type: ignore
    layout.addWidget(icon_label)

    # 内容区
    content = QWidget()
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(0, 0, 0, 0)  # type: ignore
    content_layout.setSpacing(self.scaled(4))  # type: ignore

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
      status: 执行状态
    """
    item = QWidget()
    layout = QHBoxLayout(item)
    layout.setContentsMargins(0, self.scaled(12), 0, self.scaled(12))  # type: ignore

    # 状态图标
    if status == 'success':
      status_icon = QLabel('✅')
    elif status == 'warning':
      status_icon = QLabel('⚠️')
    else:
      status_icon = QLabel('❌')
    status_icon.setObjectName('history_status')
    layout.addWidget(status_icon)

    # SQL内容
    sql_label = QLabel(sql[:60] + '...' if len(sql) > 60 else sql)
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
