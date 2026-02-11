#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据下载配置对话框
"""

import logging

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (QFormLayout, QGroupBox, QLabel, QLineEdit,
                               QPushButton, QVBoxLayout, QWidget)

from src.infrastructure.config.config_manager import get_config_manager

logger = logging.getLogger(__name__)


class DataDownloadConfigDialog(QWidget):
    """
    数据下载配置对话框
    """

    def __init__(self, parent=None):
        """
        初始化数据下载配置对话框

        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self.config_manager = get_config_manager()
        self.setWindowTitle("数据下载配置")

        # 布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # 配置内容
        self.config_group = QGroupBox("数据下载配置")
        config_layout = QVBoxLayout(self.config_group)
        config_layout.setContentsMargins(10, 10, 10, 10)

        # 配置项
        config_layout.addWidget(QLabel("<h2>数据下载配置</h2>"))
        config_layout.addWidget(QLabel("功能开发中"))
        config_layout.addStretch()

        self.main_layout.addWidget(self.config_group, 1)  # 添加拉伸因子
