#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据下载对话框
"""

import logging

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (QGroupBox, QLabel, QProgressBar, QPushButton,
                               QVBoxLayout, QWidget)

from src.business.services.data_service import get_data_service
from src.infrastructure.config.config_manager import get_config_manager

logger = logging.getLogger(__name__)


class DataDownloadDialog(QWidget):
    """
    数据下载对话框
    """

    def __init__(self, parent=None):
        """
        初始化数据下载对话框

        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self.config_manager = get_config_manager()
        self.data_service = get_data_service()
        self.setWindowTitle("数据下载")

        # 布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # 下载内容
        self.download_group = QGroupBox("数据下载")
        download_layout = QVBoxLayout(self.download_group)
        download_layout.setContentsMargins(10, 10, 10, 10)

        # 下载项
        download_layout.addWidget(QLabel("<h2>数据下载</h2>"))
        download_layout.addWidget(QLabel("功能开发中"))

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        download_layout.addWidget(self.progress_bar)

        # 下载按钮
        self.download_button = QPushButton("开始下载")
        self.download_button.clicked.connect(self.start_download)
        download_layout.addWidget(self.download_button)

        download_layout.addStretch()

        self.main_layout.addWidget(self.download_group, 1)  # 添加拉伸因子

    def start_download(self):
        """
        开始下载
        """
        try:
            logger.info("开始下载数据")
            # 模拟下载过程
            self.progress_bar.setValue(0)
            self.download_button.setEnabled(False)

            # 这里可以添加实际的下载逻辑
            # 例如调用数据服务获取数据并保存

            # 模拟下载完成
            self.progress_bar.setValue(100)
            logger.info("数据下载完成")
            self.download_button.setEnabled(True)
        except Exception as e:
            error_msg = f"下载数据失败: {str(e)}"
            logger.error(error_msg)
            self.download_button.setEnabled(True)
