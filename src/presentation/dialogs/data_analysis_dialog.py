#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据分析对话框

提供数据加载、预览、统计分析、图表绘制和报告导出功能
"""

import logging
import tempfile
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

import pandas as pd
import numpy as np

try:
  import pyqtgraph as pg
  from pyqtgraph.Qt import QtCore, QtGui
  HAS_PYQTGRAPH = True
except ImportError:
  HAS_PYQTGRAPH = False

from PySide2.QtCore import Qt, QTimer, QThread, Signal
from PySide2.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QComboBox, QLineEdit, QFileDialog, QMessageBox,
                               QTabWidget, QWidget, QHeaderView, QSplitter,
                               QGroupBox, QRadioButton, QButtonGroup, QTextEdit,
                               QProgressBar, QSizePolicy, QGraphicsView,
                               QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem)
from PySide2.QtGui import QFont, QColor, QPixmap, QImage

from src.business.services.data_analysis_service import get_data_analysis_service
from src.presentation.dialogs.gui_utils import stats_cache, GUIErrorHandler

logger = logging.getLogger(__name__)

# 缓存配置
STATS_CACHE_TTL = 300  # 5分钟
STATS_CACHE_MAX_SIZE = 20

# ==========================================================================
# 常量定义
# ==========================================================================

# 数据预览相关常量
PREVIEW_ROWS = 50  # 预览行数
PREVIEW_BATCH_SIZE = 10  # 预览分批加载大小

# 图表相关常量
CHART_WIDTH = 400  # 图表默认宽度
CHART_HEIGHT = 400  # 图表默认高度

# 统计表格常量
STATS_COLUMN_COUNT = 9  # 统计表格列数


class DataAnalysisDialog(QDialog):
    """
    数据分析对话框
    
    提供数据加载、预览、统计分析和图表绘制功能
    """
    
    def __init__(self, parent=None, initial_data=None):
        """
        初始化数据分析对话框

        Args:
            parent: 父窗口
            initial_data: 初始数据（从SQL查询传入）
        """
        super().__init__(parent)

        self.analysis_service = get_data_analysis_service()
        self.initial_data = initial_data
        self.is_loading = False

        self.setWindowTitle("数据分析")
        self.resize(1200, 800)

        # 设置UI
        self._setup_ui()

        # 延迟加载初始数据，避免阻塞UI
        if initial_data:
            QTimer.singleShot(100, self.load_initial_data_async)

        logger.info("数据分析对话框初始化完成")
    
    def _setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title_label = QLabel("数据分析与可视化")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 创建标签页
        self.tab_widget = QTabWidget()

        # 数据加载页（已集成数据预览）
        self.load_tab = self._create_load_tab()
        self.tab_widget.addTab(self.load_tab, "数据加载")

        # 统计分析页
        self.stats_tab = self._create_stats_tab()
        self.tab_widget.addTab(self.stats_tab, "统计分析")

        # 图表页
        self.chart_tab = self._create_chart_tab()
        self.tab_widget.addTab(self.chart_tab, "图表绘制")
        
        layout.addWidget(self.tab_widget)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("导出分析报告")
        self.export_btn.clicked.connect(self.export_report)
        self.export_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        button_layout.addWidget(self.export_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_load_tab(self) -> QWidget:
        """创建数据加载标签页（优化布局）"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 数据源选择
        source_group = QGroupBox("数据源选择")
        source_layout = QVBoxLayout(source_group)
        source_layout.setSpacing(8)

        # 如果传入初始数据，显示使用初始数据选项
        if self.initial_data:
            self.use_initial_radio = QRadioButton("使用当前SQL查询结果")
            self.use_initial_radio.setChecked(True)
            source_layout.addWidget(self.use_initial_radio)

        self.use_file_radio = QRadioButton("从文件加载")
        if not self.initial_data:
            self.use_file_radio.setChecked(True)
        source_layout.addWidget(self.use_file_radio)

        # 文件选择
        file_layout = QHBoxLayout()
        file_layout.setSpacing(8)
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("选择CSV、Excel或TXT文件...")
        self.file_path_edit.setEnabled(False)
        self.file_path_edit.setMinimumWidth(200)
        self.file_path_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        file_layout.addWidget(self.file_path_edit, 1)

        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self.browse_file)
        self.browse_btn.setEnabled(False)
        self.browse_btn.setMinimumWidth(80)
        self.browse_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        file_layout.addWidget(self.browse_btn)

        source_layout.addLayout(file_layout)

        # 连接信号
        if self.initial_data:
            self.use_initial_radio.toggled.connect(self.on_source_changed)
        self.use_file_radio.toggled.connect(self.on_source_changed)

        # 初始状态同步 - 根据单选按钮状态启用/禁用文件选择控件
        self.on_source_changed()

        layout.addWidget(source_group)

        # 加载按钮
        self.load_btn = QPushButton("加载数据")
        self.load_btn.clicked.connect(self.load_data)
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.load_btn.setMinimumHeight(40)
        layout.addWidget(self.load_btn)

        # 数据信息
        self.data_info_label = QLabel("未加载数据")
        self.data_info_label.setAlignment(Qt.AlignCenter)
        self.data_info_label.setStyleSheet("""
            QLabel {
                color: gray;
                padding: 20px;
                font-size: 12px;
                border: 1px dashed #ccc;
                border-radius: 4px;
                background-color: #f9f9f9;
            }
        """)
        self.data_info_label.setMinimumHeight(80)
        layout.addWidget(self.data_info_label)

        # 数据预览区域（初始隐藏，加载数据后显示）
        self.preview_group = QGroupBox("数据预览（前50行）")
        preview_layout = QVBoxLayout(self.preview_group)
        preview_layout.setContentsMargins(5, 5, 5, 5)

        # 预览表格
        self.preview_table = QTableWidget()
        self.preview_table.setAlternatingRowColors(True)
        
        # 设置水平表头（列标题）调整模式
        header = self.preview_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(False)
        header.setDefaultSectionSize(100)
        header.setMinimumSectionSize(50)
        
        # 设置垂直表头（行号列）自适应
        v_header = self.preview_table.verticalHeader()
        v_header.setSectionResizeMode(QHeaderView.Fixed)  # 行高固定
        v_header.setDefaultSectionSize(22)
        v_header.setMinimumSectionSize(22)
        
        # 启用水平滚动条
        self.preview_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.preview_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 禁用自动排序以提高性能
        self.preview_table.setSortingEnabled(False)
        # 设置选择模式
        self.preview_table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.preview_table.setSelectionBehavior(QTableWidget.SelectItems)
        # 设置文本省略模式
        self.preview_table.setTextElideMode(Qt.ElideRight)
        self.preview_table.setStyleSheet("""
            QTableWidget {
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 9pt;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                padding: 5px;
                font-weight: bold;
            }
        """)
        preview_layout.addWidget(self.preview_table)

        # 预览提示信息
        self.preview_info = QLabel("请先加载数据")
        self.preview_info.setAlignment(Qt.AlignCenter)
        self.preview_info.setStyleSheet("color: gray; padding: 10px;")
        preview_layout.addWidget(self.preview_info)

        # 初始隐藏预览区域
        self.preview_group.setVisible(False)
        layout.addWidget(self.preview_group, 1)  # 添加stretch factor使其占据剩余空间

        return tab

    def _create_stats_tab(self) -> QWidget:
        """创建统计分析标签页（优化内容展示）"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)

        # 计算统计按钮
        self.calc_stats_btn = QPushButton("计算统计分析")
        self.calc_stats_btn.clicked.connect(self.calculate_statistics)
        self.calc_stats_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 8px;")
        layout.addWidget(self.calc_stats_btn)

        # 统计结果表格
        self.stats_table = QTableWidget()
        self.stats_table.setAlternatingRowColors(True)
        self.stats_table.setColumnCount(9)
        self.stats_table.setHorizontalHeaderLabels([
            "字段", "计数", "均值", "标准差", "最小值", "25%", "中位数", "75%", "最大值"
        ])
        # 设置水平表头（列标题）调整模式
        stats_header = self.stats_table.horizontalHeader()
        stats_header.setSectionResizeMode(QHeaderView.Interactive)
        stats_header.setStretchLastSection(False)
        stats_header.setDefaultSectionSize(100)
        stats_header.setMinimumSectionSize(60)
        # 设置第一列（字段名）更宽
        self.stats_table.setColumnWidth(0, 150)
        # 设置垂直表头（行号列）自适应
        stats_v_header = self.stats_table.verticalHeader()
        stats_v_header.setSectionResizeMode(QHeaderView.Fixed)
        stats_v_header.setDefaultSectionSize(24)
        stats_v_header.setMinimumSectionSize(24)
        # 启用滚动条
        self.stats_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.stats_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # 设置文本省略模式
        self.stats_table.setTextElideMode(Qt.ElideRight)
        self.stats_table.setStyleSheet("""
            QTableWidget {
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 9pt;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView::section {
                padding: 5px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.stats_table)

        # 分类统计
        self.categorical_group = QGroupBox("分类字段统计")
        cat_layout = QVBoxLayout(self.categorical_group)
        self.categorical_text = QTextEdit()
        self.categorical_text.setReadOnly(True)
        self.categorical_text.setMinimumHeight(150)
        self.categorical_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10pt;
                line-height: 1.5;
                padding: 10px;
            }
        """)
        cat_layout.addWidget(self.categorical_text)
        layout.addWidget(self.categorical_group, 1)  # 添加stretch factor

        return tab
    
    def _create_chart_tab(self) -> QWidget:
        """创建图表绘制标签页（优化内容展示）"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)

        # 图表配置
        config_group = QGroupBox("图表配置")
        config_layout = QHBoxLayout(config_group)
        config_layout.setSpacing(10)

        # 图表类型
        config_layout.addWidget(QLabel("图表类型:"))
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["柱状图", "折线图", "散点图", "饼图"])
        self.chart_type_combo.setMinimumWidth(100)
        config_layout.addWidget(self.chart_type_combo)

        # X轴
        config_layout.addWidget(QLabel("X轴:"))
        self.x_column_combo = QComboBox()
        self.x_column_combo.setMinimumWidth(150)
        config_layout.addWidget(self.x_column_combo)

        # Y轴
        config_layout.addWidget(QLabel("Y轴:"))
        self.y_column_combo = QComboBox()
        self.y_column_combo.addItem("(自动统计)")
        self.y_column_combo.setMinimumWidth(150)
        config_layout.addWidget(self.y_column_combo)

        # 绘制按钮
        self.draw_btn = QPushButton("绘制图表")
        self.draw_btn.clicked.connect(self.draw_chart)
        self.draw_btn.setStyleSheet("background-color: #9C27B0; color: white; padding: 5px 15px;")
        config_layout.addWidget(self.draw_btn)

        config_layout.addStretch()
        layout.addWidget(config_group)

        layout.addWidget(config_group)
        
        # 图表显示区域
        self.chart_container = QWidget()
        chart_layout = QVBoxLayout(self.chart_container)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        
        # 如果有 PyQtGraph，使用 GraphicsLayoutWidget
        if HAS_PYQTGRAPH:
          from pyqtgraph import GraphicsLayoutWidget
          self.chart_view = GraphicsLayoutWidget()
          chart_layout.addWidget(self.chart_view)
        else:
          # 降级使用 QLabel 显示提示信息
          self.chart_view = QLabel()
          self.chart_view.setAlignment(Qt.AlignCenter)
          self.chart_view.setMinimumHeight(400)
          self.chart_view.setStyleSheet("""
              QLabel {
                  background-color: #f5f5f5;
                  border: 2px dashed #ccc;
                  font-size: 14px;
                  color: #666;
              }
          """)
          self.chart_view.setText("请安装 PyQtGraph 以显示图表:\npip install pyqtgraph")
          chart_layout.addWidget(self.chart_view)
        
        layout.addWidget(self.chart_container)
        
        # 导出图表按钮
        self.export_chart_btn = QPushButton("导出图表")
        self.export_chart_btn.clicked.connect(self.export_chart)
        self.export_chart_btn.setEnabled(False)
        layout.addWidget(self.export_chart_btn)
        
        return tab
    
    def on_source_changed(self):
        """数据源改变时的处理"""
        if self.use_file_radio.isChecked():
            self.file_path_edit.setEnabled(True)
            self.browse_btn.setEnabled(True)
        else:
            self.file_path_edit.setEnabled(False)
            self.browse_btn.setEnabled(False)
    
    def browse_file(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择数据文件",
            "",
            "CSV文件 (*.csv);;Excel文件 (*.xlsx *.xls);;文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
    
    def load_initial_data_async(self):
        """异步加载初始数据"""
        if not self.initial_data or self.is_loading:
            return

        self.is_loading = True
        self.data_info_label.setText("正在加载数据...")
        self.data_info_label.setStyleSheet("color: blue; padding: 20px;")

        # 创建后台线程加载数据
        class DataLoadThread(QThread):
            load_finished = Signal(bool, str)

            def __init__(self, analysis_service, initial_data):
                super().__init__()
                self.analysis_service = analysis_service
                self.initial_data = initial_data

            def run(self):
                try:
                    success = self.analysis_service.load_from_dict_list(self.initial_data)
                    if success:
                        self.load_finished.emit(True, "数据加载成功")
                    else:
                        self.load_finished.emit(False, "数据加载失败")
                except Exception as e:
                    self.load_finished.emit(False, str(e))

        # 启动加载线程（添加清理机制避免内存泄漏）
        self.data_loader = DataLoadThread(self.analysis_service, self.initial_data)
        self.data_loader.load_finished.connect(self.on_initial_data_loaded)

        # 线程完成后自动删除，避免内存泄漏
        self.data_loader.finished.connect(self.data_loader.deleteLater)
        self.data_loader.start()

    def on_initial_data_loaded(self, success, message):
        """初始数据加载完成回调"""
        self.is_loading = False

        if success:
            self.update_data_info()
            # 使用延迟更新预览，避免阻塞UI
            QTimer.singleShot(50, self.update_preview_async)
            self.update_column_combos()
            self.statusBar().showMessage("数据加载完成", 3000) if hasattr(self, 'statusBar') else None
        else:
            self.data_info_label.setText(f"加载失败: {message}")
            self.data_info_label.setStyleSheet("color: red; padding: 20px;")
            QMessageBox.warning(self, "失败", f"数据加载失败:\n{message}")

    def load_initial_data(self):
        """加载初始数据（同步版本，供手动调用）"""
        if self.initial_data:
            success = self.analysis_service.load_from_dict_list(self.initial_data)
            if success:
                self.update_data_info()
                self.update_preview()
                self.update_column_combos()
                QMessageBox.information(self, "成功", "已从SQL查询结果加载数据")
    
    def load_data(self):
        """加载数据"""
        try:
            if self.initial_data and self.use_initial_radio.isChecked():
                # 使用初始数据
                success = self.analysis_service.load_from_dict_list(self.initial_data)
            else:
                # 从文件加载
                file_path = self.file_path_edit.text().strip()
                if not file_path:
                    QMessageBox.warning(self, "警告", "请选择数据文件")
                    return
                
                success = self.analysis_service.load_from_file(file_path)
            
            if success:
                self.update_data_info()
                # 使用异步更新预览，避免阻塞UI
                self.update_preview_async()
                self.update_column_combos()
                QMessageBox.information(self, "成功", "数据加载成功，已在本页显示数据预览")
            else:
                QMessageBox.warning(self, "失败", "数据加载失败")
                
        except Exception as e:
            logger.error(f"加载数据失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载数据失败:\n{str(e)}")
    
    def update_data_info(self):
        """更新数据信息显示"""
        df = self.analysis_service.get_dataframe()
        if df is not None:
            info_text = f"数据已加载 - 行数: {len(df)}, 列数: {len(df.columns)}"
            self.data_info_label.setText(info_text)
            self.data_info_label.setStyleSheet("color: green; padding: 20px;")
    
    def update_preview_async(self):
        """异步更新数据预览（分批加载，避免阻塞UI）"""
        preview = self.analysis_service.get_data_preview(n_rows=PREVIEW_ROWS)

        if 'error' in preview:
            self.preview_info.setText(f"错误: {preview['error']}")
            # 显示预览区域但显示错误
            self.preview_group.setVisible(True)
            return

        # 清空表格
        self.preview_table.clear()
        self.preview_table.setRowCount(0)

        # 设置列
        columns = preview['columns']
        self.preview_table.setColumnCount(len(columns))
        self.preview_table.setHorizontalHeaderLabels(columns)

        # 分批加载数据
        data = preview['data']
        total_rows = len(data)

        # 先设置行数
        self.preview_table.setRowCount(total_rows)

        # 显示预览区域
        self.preview_group.setVisible(True)
        self.preview_group.setTitle(f"数据预览（前{total_rows}行 / 共{preview['total_rows']}行）")

        # 分批填充数据（每批10行，避免UI阻塞）
        self._load_preview_batch(data, columns, 0, 10)

        # 更新提示信息
        self.preview_info.setText(f"显示前 {total_rows} 行数据（共 {preview['total_rows']} 行）")

    def _load_preview_batch(self, data, columns, start_idx, batch_size):
        """分批加载预览数据"""
        end_idx = min(start_idx + batch_size, len(data))

        for row_idx in range(start_idx, end_idx):
            row_data = data[row_idx]
            for col_idx, col_name in enumerate(columns):
                value = row_data.get(col_name, "")
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.preview_table.setItem(row_idx, col_idx, item)

        # 如果还有数据，继续加载下一批
        if end_idx < len(data):
            QTimer.singleShot(10, lambda: self._load_preview_batch(data, columns, end_idx, batch_size))
        else:
            # 所有数据加载完成，调整列宽
            self._adjust_table_columns(self.preview_table)

    def update_preview(self):
        """更新数据预览（同步版本）"""
        preview = self.analysis_service.get_data_preview(n_rows=100)

        if 'error' in preview:
            self.preview_info.setText(f"错误: {preview['error']}")
            # 显示预览区域但显示错误
            self.preview_group.setVisible(True)
            return

        # 清空表格
        self.preview_table.clear()

        # 设置列
        columns = preview['columns']
        self.preview_table.setColumnCount(len(columns))
        self.preview_table.setHorizontalHeaderLabels(columns)

        # 设置行
        data = preview['data']
        total_rows = len(data)
        self.preview_table.setRowCount(total_rows)

        # 显示预览区域
        self.preview_group.setVisible(True)
        self.preview_group.setTitle(f"数据预览（前{total_rows}行 / 共{preview['total_rows']}行）")

        # 填充数据
        for row_idx, row_data in enumerate(data):
            for col_idx, col_name in enumerate(columns):
                value = row_data.get(col_name, "")
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.preview_table.setItem(row_idx, col_idx, item)

        # 调整列宽
        self._adjust_table_columns(self.preview_table)

        # 更新提示信息
        self.preview_info.setText(f"显示前 {total_rows} 行数据（共 {preview['total_rows']} 行）")

    def _adjust_table_columns(self, table):
        """
        智能调整表格列宽和行号列宽

        根据内容自动调整列宽，但设置最小和最大宽度限制
        同时自动调整行号列（垂直表头）宽度
        """
        # 调整水平表头（数据列）
        table.resizeColumnsToContents()

        header = table.horizontalHeader()
        for col in range(table.columnCount()):
            current_width = header.sectionSize(col)
            # 设置最小宽度60像素，最大宽度300像素
            new_width = max(60, min(current_width, 300))
            header.resizeSection(col, new_width)
        
        # 调整垂直表头（行号列）宽度自适应
        v_header = table.verticalHeader()
        # 根据行数计算所需宽度（每行最多6位数字）
        row_count = table.rowCount()
        if row_count > 0:
            # 计算行号的最大位数
            digits = len(str(row_count))
            # 每个数字约8像素宽度 + 左右边距
            min_width = max(30, digits * 10 + 16)
            v_header.setDefaultSectionSize(22)
            v_header.setMinimumSectionSize(22)
            # 设置行号列宽度
            v_header.setFixedWidth(min_width)
    
    def update_column_combos(self):
        """更新列选择下拉框"""
        df = self.analysis_service.get_dataframe()
        if df is None:
            return
        
        columns = list(df.columns)
        
        # 清空并重新填充
        self.x_column_combo.clear()
        self.y_column_combo.clear()
        
        self.x_column_combo.addItems(columns)
        self.y_column_combo.addItem("(自动统计)")
        self.y_column_combo.addItems(columns)
    
    def calculate_statistics(self) -> None:
        """计算统计分析（使用缓存优化）"""
        try:
            # 生成缓存键
            df = self.analysis_service.get_dataframe()
            if df is None:
                QMessageBox.warning(self, "警告", "请先加载数据")
                return

            # 使用数据框的内存地址和行数作为缓存键
            cache_key = f"stats_{id(df)}_{len(df)}"

            # 检查缓存
            cached_stats = stats_cache.get(cache_key)
            if cached_stats is not None:
                logger.debug("使用缓存的统计结果")
                self._display_statistics(cached_stats)
                QMessageBox.information(self, "成功", "统计分析完成（使用缓存）")
                return

            # 计算统计
            stats = self.analysis_service.calculate_statistics()

            if 'error' in stats:
                QMessageBox.warning(self, "错误", f"统计计算失败: {stats['error']}")
                return

            # 缓存结果
            stats_cache.set(cache_key, stats)
            logger.debug("统计结果已缓存")

            # 显示统计结果
            self._display_statistics(stats)

            QMessageBox.information(self, "成功", "统计分析完成")

        except Exception as e:
            GUIErrorHandler.handle_error(
                context="计算统计",
                error=e,
                show_dialog=True,
                parent=self,
                logger_instance=logger
            )

    def _display_statistics(self, stats: Dict[str, Any]) -> None:
        """
        显示统计结果

        Args:
            stats: 统计结果字典
        """
        # 显示数值统计
        numeric_stats = stats.get('numeric_statistics', [])
        self.stats_table.setRowCount(len(numeric_stats))

        for row_idx, col_stats in enumerate(numeric_stats):
            self.stats_table.setItem(row_idx, 0, QTableWidgetItem(col_stats['column']))
            self.stats_table.setItem(row_idx, 1, QTableWidgetItem(str(col_stats['count'])))
            self.stats_table.setItem(row_idx, 2, QTableWidgetItem(f"{col_stats['mean']:.2f}"))
            self.stats_table.setItem(row_idx, 3, QTableWidgetItem(f"{col_stats['std']:.2f}"))
            self.stats_table.setItem(row_idx, 4, QTableWidgetItem(f"{col_stats['min']:.2f}"))
            self.stats_table.setItem(row_idx, 5, QTableWidgetItem(f"{col_stats['25%']:.2f}"))
            self.stats_table.setItem(row_idx, 6, QTableWidgetItem(f"{col_stats['50%']:.2f}"))
            self.stats_table.setItem(row_idx, 7, QTableWidgetItem(f"{col_stats['75%']:.2f}"))
            self.stats_table.setItem(row_idx, 8, QTableWidgetItem(f"{col_stats['max']:.2f}"))

        # 显示分类统计
        categorical_stats = stats.get('categorical_statistics', [])
        cat_text = ""
        for cat_stat in categorical_stats:
            cat_text += f"字段: {cat_stat['column']}\n"
            cat_text += f"  唯一值数: {cat_stat['unique']}\n"
            cat_text += f"  最常见值: {cat_stat['top']} (出现 {cat_stat['freq']} 次)\n\n"

        self.categorical_text.setText(cat_text)

        # 调整统计表格列宽
        self._adjust_table_columns(self.stats_table)
    
    def draw_chart(self):
        """绘制图表"""
        try:
            chart_type = self.chart_type_combo.currentText()
            x_column = self.x_column_combo.currentText()
            y_column = self.y_column_combo.currentText()
            
            if y_column == "(自动统计)":
                y_column = None
            
            # 获取图表数据
            chart_data = self.analysis_service.get_chart_data(x_column, y_column)
            
            if 'error' in chart_data:
                QMessageBox.warning(self, "错误", chart_data['error'])
                return
            
            if not HAS_PYQTGRAPH:
                # 显示提示信息
                info_text = f"图表类型: {chart_type}\n"
                info_text += f"X轴字段: {chart_data['x_column']}\n"
                info_text += f"数据点数: {len(chart_data['x_data'])}\n\n"
                info_text += "PyQtGraph 未安装，无法显示图表。\n"
                info_text += "请安装: pip install pyqtgraph"
                if isinstance(self.chart_view, QLabel):
                    self.chart_view.setText(info_text)
                QMessageBox.warning(self, "提示", "请安装 PyQtGraph 以显示图表:\npip install pyqtgraph")
                return
            
            # 清空之前的图表
            self.chart_view.clear()
            
            # 获取数据
            x_data = chart_data['x_data']
            y_data = chart_data['y_data']
            
            # 转换数据为数值类型
            try:
                x_numeric = [float(x) if x is not None else 0 for x in x_data]
                y_numeric = [float(y) if y is not None else 0 for y in y_data]
            except (ValueError, TypeError):
                # 如果无法转换为数值，使用索引
                x_numeric = list(range(len(x_data)))
                y_numeric = [float(y) if y is not None else 0 for y in y_data]
            
            # 根据图表类型绘制
            plot = self.chart_view.addPlot(title=f"{chart_type}: {x_column}")
            
            if chart_type == "柱状图":
                # 绘制柱状图
                x_pos = np.arange(len(x_data))
                plot.setTicks([(x_pos, [str(x)[:10] for x in x_data])])
                bar_plot = pg.BarGraphItem(
                    x=x_pos,
                    height=y_numeric,
                    width=0.6,
                    brush=QColor(100, 149, 237).rgb
                )
                plot.addItem(bar_plot)
                
            elif chart_type == "折线图":
                # 绘制折线图
                plot.plot(x_numeric, y_numeric, pen='b', symbol='o', symbolSize=5)
                
            elif chart_type == "散点图":
                # 绘制散点图
                scatter = pg.ScatterPlotItem(
                    x_numeric, y_numeric,
                    size=10,
                    brush=QColor(255, 99, 71).rgb
                )
                plot.addItem(scatter)
                
            elif chart_type == "饼图":
                # 饼图需要特殊处理
                self._draw_pie_chart(x_data, y_data)
                return
            
            # 设置坐标轴标签
            plot.setLabel('bottom', x_column)
            plot.setLabel('left', y_column if y_column else '计数')
            
            # 启用交互功能
            plot.setMouseEnabled(x=True, y=True)
            plot.showGrid(x=True, y=True)
            
            self.export_chart_btn.setEnabled(True)
            logger.info(f"图表绘制成功: {chart_type}")
            
        except Exception as e:
            logger.error(f"绘制图表失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"绘制图表失败:\n{str(e)}")
    
    def _draw_pie_chart(self, labels, values):
        """绘制饼图"""
        try:
            # 创建饼图场景
            scene = QGraphicsScene()
            self.chart_view.setScene(scene)
            
            # 计算中心点和半径
            center_x, center_y = 200, 200
            radius = 150
            
            # 转换值为数值
            numeric_values = [float(v) if v is not None else 0 for v in values]
            total = sum(numeric_values)
            
            if total == 0:
                return
            
            # 定义颜色
            colors = [
                QColor(255, 99, 71),    # 红色
                QColor(100, 149, 237),  # 蓝色
                QColor(50, 205, 50),    # 绿色
                QColor(255, 215, 0),    # 金色
                QColor(238, 130, 238),  # 紫色
                QColor(255, 165, 0),    # 橙色
                QColor(0, 255, 255),    # 青色
                QColor(255, 20, 147),   # 粉色
            ]
            
            # 绘制饼图切片
            start_angle = 0
            for i, (label, value) in enumerate(zip(labels, numeric_values)):
                if value <= 0:
                    continue
                    
                span_angle = int(360 * value / total)
                color = colors[i % len(colors)]
                
                # 创建饼图切片
                slice_item = QGraphicsRectItem()
                slice_item.setRect(
                    center_x - radius,
                    center_y - radius,
                    radius * 2,
                    radius * 2
                )
                
                # 设置饼图外观
                slice_item.setBrush(color)
                slice_item.setPen(QColor(255, 255, 255))
                
                scene.addItem(slice_item)
                
                # 计算角度（用于标签位置）
                mid_angle = start_angle + span_angle / 2
                angle_rad = np.radians(mid_angle)
                
                # 添加标签
                label_text = f"{str(label)[:8]}: {value:.1f}"
                text_item = QGraphicsTextItem(label_text)
                text_item.setPos(
                    center_x + (radius + 20) * np.cos(angle_rad) - 30,
                    center_y + (radius + 20) * np.sin(angle_rad) - 10
                )
                scene.addItem(text_item)
                
                start_angle += span_angle
            
            # 设置视图
            self.chart_view.setSceneRect(0, 0, 400, 400)
            self.chart_view.fitInView(scene.sceneRect(), Qt.KeepAspectRatio)
            
        except Exception as e:
            logger.error(f"绘制饼图失败: {str(e)}")
            if isinstance(self.chart_view, QLabel):
                self.chart_view.setText(f"饼图绘制失败: {str(e)}")
    
    def export_chart(self):
        """导出图表"""
        try:
            if not HAS_PYQTGRAPH:
                QMessageBox.warning(self, "警告", "PyQtGraph 未安装，无法导出图表")
                return
            
            # 获取当前图表数据
            x_column = self.x_column_combo.currentText()
            y_column = self.y_column_combo.currentText()
            chart_type = self.chart_type_combo.currentText()
            
            chart_data = self.analysis_service.get_chart_data(x_column, y_column)
            
            if 'error' in chart_data:
                QMessageBox.warning(self, "错误", chart_data['error'])
                return
            
            # 选择保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出图表",
                f"chart_{x_column}_{chart_type}.png",
                "PNG图片 (*.png);;所有文件 (*.*)"
            )
            
            if not file_path:
                return
            
            # 从 GraphicsLayoutWidget 获取图表并保存
            try:
                # 获取图表的图像
                img = self.chart_view.grab()
                img.save(file_path, "PNG")
                QMessageBox.information(self, "成功", f"图表已导出到:\n{file_path}")
                logger.info(f"图表已导出: {file_path}")
            except Exception as e:
                # 如果无法从 GraphicsLayoutWidget 获取，尝试其他方法
                logger.error(f"导出图表失败: {str(e)}")
                QMessageBox.warning(self, "警告", f"导出失败: {str(e)}")
                
        except Exception as e:
            logger.error(f"导出图表失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"导出图表失败:\n{str(e)}")
    
    def export_report(self):
        """导出分析报告"""
        try:
            df = self.analysis_service.get_dataframe()
            if df is None:
                QMessageBox.warning(self, "警告", "请先加载数据")
                return
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出分析报告",
                f"analysis_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                "Excel文件 (*.xlsx)"
            )
            
            if not file_path:
                return
            
            # 计算统计
            stats = self.analysis_service.calculate_statistics()
            
            # 创建Excel写入器
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # 写入原始数据
                df.to_excel(writer, sheet_name='原始数据', index=False)
                
                # 写入统计信息
                if 'numeric_statistics' in stats:
                    stats_df = pd.DataFrame(stats['numeric_statistics'])
                    stats_df.to_excel(writer, sheet_name='统计分析', index=False)
            
            QMessageBox.information(self, "成功", f"分析报告已导出到:\n{file_path}")
            logger.info(f"分析报告已导出: {file_path}")
            
        except Exception as e:
            logger.error(f"导出报告失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"导出报告失败:\n{str(e)}")
