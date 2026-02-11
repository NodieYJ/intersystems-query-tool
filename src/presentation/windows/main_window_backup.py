#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主窗口模块
"""

import logging

from PySide2.QtCore import QEvent, Qt
from PySide2.QtGui import QCursor
from PySide2.QtWidgets import (QAction, QApplication, QHBoxLayout, QLabel,
                               QMainWindow, QMenu, QMenuBar, QMessageBox,
                               QPushButton, QScrollArea, QSizePolicy,
                               QStackedLayout, QStatusBar, QVBoxLayout,
                               QWidget)

from src.infrastructure.config.config_manager import get_config_manager
from src.presentation.dialogs.connection_config_dialog import \
    ConnectionConfigDialog
from src.presentation.dialogs.data_download_config_dialog import \
    DataDownloadConfigDialog
from src.presentation.dialogs.data_download_dialog import DataDownloadDialog
from src.presentation.dialogs.sql_query_dialog import SqlQueryDialog
from utils.performance import EventCompressor, DeferredUpdater, get_optimizer

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    主窗口
    """

    def __init__(self):
        """
        初始化主窗口
        """
        super().__init__()
        self.config_manager = get_config_manager()

        # 初始化性能优化工具
        self.optimizer = get_optimizer()
        self.optimizer.initialize()

        # 创建事件压缩器用于处理滚动事件
        self.scroll_event_compressor = self.optimizer.create_event_compressor("scroll_events", timeout=50)
        self.scroll_event_compressor.handle_events = self._handle_scroll_events

        # 创建延迟更新器用于UI更新
        self.deferred_updater = self.optimizer.get_deferred_updater()

        # 获取配置的窗口尺寸
        window_width = self.config_manager.get("ui.default_window_width", 800)
        window_height = self.config_manager.get("ui.default_window_height", 600)
        min_window_width = self.config_manager.get("ui.min_window_width", 400)
        min_window_height = self.config_manager.get("ui.min_window_height", 300)

        # 设置窗口属性
        self.setWindowTitle(self.config_manager.get("application.name", "桌面应用程序"))
        self.setGeometry(100, 100, window_width, window_height)
        self.setMinimumSize(min_window_width, min_window_height)

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 添加菜单栏
        self.menu_bar = QMenuBar()
        main_layout.addWidget(self.menu_bar)

        # 创建"设置"菜单
        self.settings_menu = QMenu("设置")
        self.menu_bar.addMenu(self.settings_menu)

        # 创建"数据库连接配置"子菜单
        self.connection_config_action = QAction("数据库连接配置")
        self.connection_config_action.triggered.connect(self.show_connection_config)
        self.settings_menu.addAction(self.connection_config_action)

        # 创建"日志"子菜单
        self.log_action = QAction("日志")
        self.log_action.triggered.connect(self.show_log)
        self.settings_menu.addAction(self.log_action)

        # 创建"查询统计"菜单
        self.query_menu = QMenu("查询统计")
        self.menu_bar.addMenu(self.query_menu)

        # 创建"数据下载配置"子菜单
        self.data_download_config_action = QAction("数据下载配置")
        self.data_download_config_action.triggered.connect(
            self.show_data_download_config
        )
        self.query_menu.addAction(self.data_download_config_action)

        # 创建"数据下载"子菜单
        self.data_download_action = QAction("数据下载")
        self.data_download_action.triggered.connect(self.show_data_download)
        self.query_menu.addAction(self.data_download_action)

        # 创建"SQL查询"子菜单
        self.sql_query_action = QAction("SQL查询")
        self.sql_query_action.triggered.connect(self.show_sql_query)
        self.query_menu.addAction(self.sql_query_action)

        # 创建"数据分析"子菜单
        self.data_analysis_action = QAction("数据分析")
        self.data_analysis_action.triggered.connect(self.show_data_analysis)
        self.query_menu.addAction(self.data_analysis_action)

        # 创建"窗口"菜单
        self.window_menu = QMenu("窗口")
        self.menu_bar.addMenu(self.window_menu)

        # 在菜单栏右侧添加窗口控制按钮组
        # 创建窗口控制部件
        self.window_controls = QWidget()
        self.controls_layout = QHBoxLayout(self.window_controls)
        self.controls_layout.setContentsMargins(0, 0, 10, 0)
        self.controls_layout.setSpacing(5)

        # 仅保留关闭按钮
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self.handle_close_button)
        self.controls_layout.addWidget(self.close_btn)
        # 初始状态下隐藏关闭按钮
        self.close_btn.hide()

        # 添加到菜单栏
        self.menu_bar.setCornerWidget(self.window_controls, Qt.TopRightCorner)

        # 存储当前活动的子窗体
        self.active_subwindow = None
        # 存储打开的子窗口列表，按打开顺序排列
        self.open_subwindows = []
        # 存储窗口菜单项映射，用于快速查找
        self.window_menu_actions = {}

        # 添加滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 创建内容部件
        self.content_widget = QWidget()

        # 设置内容部件大小策略，确保填充整个滚动区域
        self.content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.scroll_area.setWidget(self.content_widget)

        # 创建栈布局来管理子窗体
        self.stacked_layout = QStackedLayout(self.content_widget)

        # 设置栈布局的对齐方式为左上角
        self.stacked_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        # 确保内容部件的布局从左上角开始
        self.content_widget.setLayoutDirection(Qt.LeftToRight)

        # 为内容部件安装事件过滤器，确保鼠标滚轮事件传递给滚动区域
        self.content_widget.installEventFilter(self)

        # 添加到主布局
        main_layout.addWidget(self.scroll_area)

        # 添加状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

        # 连接滚动条信号
        self.connect_scrollbar_signals()



    def show_connection_config(self):
        """
        显示数据库连接配置窗口
        """
        try:
            logger.info("用户点击菜单: 数据库连接配置")
            dialog = ConnectionConfigDialog(self)
            logger.info("弹出窗口: 数据库连接配置")
            dialog.exec_()
        except Exception as e:
            error_msg = f"打开数据库连接配置窗口失败: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def show_log(self):
        """
        显示日志窗口
        """
        try:
            logger.info("用户点击菜单: 日志")
            # 创建并显示日志对话框
            from src.presentation.dialogs.log_dialog import LogDialog
            dialog = LogDialog(self)
            logger.info("弹出窗口: 日志")
            dialog.exec_()
        except Exception as e:
            error_msg = f"打开日志窗口失败: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def show_data_download_config(self):
        """
        显示数据下载配置
        """
        try:
            logger.info("用户点击菜单: 数据下载配置")
            # 创建并显示数据下载配置对话框
            dialog = DataDownloadConfigDialog(self)
            logger.info("弹出窗口: 数据下载配置")
            self._setup_subwindow(dialog)
        except Exception as e:
            error_msg = f"打开数据下载配置窗口失败: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def show_data_download(self):
        """
        显示数据下载
        """
        try:
            logger.info("用户点击菜单: 数据下载")
            # 创建并显示数据下载对话框
            dialog = DataDownloadDialog(self)
            logger.info("弹出窗口: 数据下载")
            self._setup_subwindow(dialog)
        except Exception as e:
            error_msg = f"打开数据下载窗口失败: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def show_sql_query(self):
        """
        显示SQL查询
        """
        try:
            logger.info("用户点击菜单: SQL查询")
            # 创建并显示SQL查询对话框
            dialog = SqlQueryDialog(self)
            logger.info("弹出窗口: SQL查询")
            self._setup_subwindow(dialog)
        except Exception as e:
            error_msg = f"打开SQL查询窗口失败: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def show_data_analysis(self):
        """
        显示数据分析对话框
        """
        try:
            logger.info("用户点击菜单: 数据分析")
            # 创建并显示数据分析对话框
            from src.presentation.dialogs.data_analysis_dialog import DataAnalysisDialog
            dialog = DataAnalysisDialog(self)
            logger.info("弹出窗口: 数据分析")
            self._setup_subwindow(dialog)
        except Exception as e:
            error_msg = f"打开数据分析窗口失败: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def _setup_subwindow(self, subwindow):
        """
        设置子窗体

        Args:
            subwindow: 子窗口对象
        """
        try:
            # 存储当前活动的子窗体
            self.active_subwindow = subwindow

            # 为子窗体添加边界颜色样式
            subwindow.setStyleSheet(
                """
                QWidget {
                    border: 2px solid #1E90FF;
                    border-radius: 4px;
                    padding: 10px;
                }
            """
            )

            # 设置子窗体大小策略，确保从左上角开始填充整个工作区
            subwindow.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            # 确保子窗体没有固定大小
            subwindow.setMinimumSize(0, 0)
            subwindow.setMaximumSize(16777215, 16777215)  # 使用Qt的默认最大值

            # 检查子窗口是否已经在栈布局中
            window_title = subwindow.windowTitle()
            existing_index = -1
            for i in range(self.stacked_layout.count()):
                widget = self.stacked_layout.widget(i)
                if (
                    widget
                    and hasattr(widget, "windowTitle")
                    and widget.windowTitle() == window_title
                ):
                    existing_index = i
                    break

            if existing_index >= 0:
                # 如果子窗口已存在，切换到它
                self.stacked_layout.setCurrentIndex(existing_index)
            else:
                # 如果子窗口不存在，添加到栈布局中
                self.stacked_layout.addWidget(subwindow)
                self.stacked_layout.setCurrentWidget(subwindow)

            # 确保滚动区域填充主布局空间
            self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.content_widget.setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Expanding
            )

            # 强制刷新布局，确保子窗体正确显示
            self.stacked_layout.update()
            self.content_widget.layout().activate()
            self.centralWidget().layout().activate()

            # 将子窗口添加到跟踪列表中（如果不存在）
            # 清理已删除的子窗口对象
            self.open_subwindows = [
                w for w in self.open_subwindows if hasattr(w, "windowTitle")
            ]
            if not any(w.windowTitle() == window_title for w in self.open_subwindows):
                self.open_subwindows.append(subwindow)

            # 更新窗口菜单
            self.update_window_menu()

            # 直接调用子窗口显示时的处理
            self._on_subwindow_show()
        except Exception as e:
            error_msg = f"设置子窗口失败: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def _on_subwindow_show(self):
        """
        子窗体显示时的处理
        """
        if self.active_subwindow:
            # 更新窗口标题
            original_title = self.config_manager.get("application.name", "桌面应用程序")
            new_title = (
                f"{original_title} - [{self.active_subwindow.windowTitle()}]".replace(
                    "  ", " "
                )
            )
            self.setWindowTitle(new_title)
            # 显示关闭按钮
            if hasattr(self, "close_btn"):
                # 确保按钮大小正确
                self.close_btn.setFixedSize(30, 30)
                # 确保按钮可见
                self.close_btn.setVisible(True)
                # 强制刷新布局
                self.window_controls.layout().activate()
                self.window_controls.adjustSize()
                self.menu_bar.adjustSize()

    def _close_subwindow(self):
        """
        关闭子窗体
        """
        try:
            # 检查是否有活动子窗口
            if self.active_subwindow:
                # 获取当前活动子窗口的标题
                active_title = self.active_subwindow.windowTitle()
                logger.info(f"用户关闭窗口: {active_title}")

                # 从栈布局中移除当前活动子窗口
                self.stacked_layout.removeWidget(self.active_subwindow)
                self.active_subwindow.deleteLater()

                # 从打开的子窗口列表中移除
                self.open_subwindows = [
                    w
                    for w in self.open_subwindows
                    if not (
                        hasattr(w, "windowTitle") and w.windowTitle() == active_title
                    )
                ]

                # 清除活动子窗体引用
                self.active_subwindow = None

                # 如果还有其他打开的子窗口，切换到第一个
                if self.open_subwindows:
                    first_subwindow = self.open_subwindows[0]
                    self.active_subwindow = first_subwindow
                    self.stacked_layout.setCurrentWidget(first_subwindow)
                    # 更新窗口标题
                    original_title = self.config_manager.get(
                        "application.name", "桌面应用程序"
                    )
                    new_title = (
                        f"{original_title} - [{first_subwindow.windowTitle()}]".replace(
                            "  ", " "
                        )
                    )
                    self.setWindowTitle(new_title)
                else:
                    # 重置窗口标题
                    self.setWindowTitle(
                        self.config_manager.get("application.name", "桌面应用程序")
                    )
                    # 隐藏关闭按钮
                    if hasattr(self, "close_btn"):
                        self.close_btn.hide()

            # 更新窗口菜单
            self.update_window_menu()
        except Exception as e:
            error_msg = f"关闭子窗口失败: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def update_window_menu(self):
        """
        更新窗口菜单的内容
        """
        try:
            # 清除现有的子菜单项
            for action in list(self.window_menu_actions.values()):
                self.window_menu.removeAction(action)
            self.window_menu_actions.clear()

            # 如果有打开的子窗口，添加分隔线和子菜单项
            if self.open_subwindows:
                # 添加分隔线
                separator = self.window_menu.addSeparator()

                # 按打开顺序添加子菜单项
                for subwindow in self.open_subwindows:
                    try:
                        window_title = subwindow.windowTitle()
                        action = self.window_menu.addAction(window_title)

                        # 设置点击事件
                        action.triggered.connect(
                            lambda *args, w=subwindow: self.switch_to_subwindow(w)
                        )

                        # 存储菜单项映射
                        self.window_menu_actions[window_title] = action

                        # 如果是当前活动子窗口，高亮显示
                        if subwindow == self.active_subwindow:
                            action.setFont(subwindow.font())
                            action.setCheckable(True)
                            action.setChecked(True)
                        else:
                            action.setCheckable(False)
                            action.setChecked(False)
                    except Exception as e:
                        logger.error(f"更新窗口菜单项时发生错误: {str(e)}")
        except Exception as e:
            logger.error(f"更新窗口菜单时发生错误: {str(e)}")

    def switch_to_subwindow(self, subwindow):
        """
        切换到指定的子窗口

        Args:
            subwindow: 要切换到的子窗口
        """
        try:
            # 检查子窗口是否有效
            if not subwindow or not hasattr(subwindow, "windowTitle"):
                logger.error("无效的子窗口对象")
                return
            logger.info(f"用户切换窗口: {subwindow.windowTitle()}")

            # 设置子窗口为活动子窗口
            self.active_subwindow = subwindow

            # 检查子窗口是否在栈布局中
            subwindow_in_layout = False
            for i in range(self.stacked_layout.count()):
                widget = self.stacked_layout.widget(i)
                if widget == subwindow:
                    subwindow_in_layout = True
                    # 切换到该子窗口
                    self.stacked_layout.setCurrentIndex(i)
                    break

            if not subwindow_in_layout:
                # 如果子窗口不在栈布局中，添加到栈布局中
                try:
                    self.stacked_layout.addWidget(subwindow)
                    self.stacked_layout.setCurrentWidget(subwindow)
                except RuntimeError as e:
                    if "already deleted" in str(e):
                        logger.error("子窗口对象已删除，无法添加到布局中")
                        # 从打开的子窗口列表中移除该子窗口
                        if subwindow in self.open_subwindows:
                            self.open_subwindows.remove(subwindow)
                        # 更新窗口菜单
                        self.update_window_menu()
                        return
                    else:
                        raise

            # 强制刷新布局，确保子窗口正确显示
            self.stacked_layout.update()
            self.content_widget.layout().activate()
            self.centralWidget().layout().activate()

            # 更新窗口菜单，高亮显示当前子窗口
            self.update_window_menu()

            # 更新窗口标题
            if self.active_subwindow:
                original_title = self.config_manager.get(
                    "application.name", "桌面应用程序"
                )
                new_title = f"{original_title} - [{self.active_subwindow.windowTitle()}]".replace(
                    "  ", " "
                )
                self.setWindowTitle(new_title)

            # 显示关闭按钮
            if hasattr(self, "close_btn"):
                self.close_btn.setVisible(True)
                # 强制刷新布局
                self.window_controls.layout().activate()
                self.window_controls.adjustSize()
                self.menu_bar.adjustSize()
        except Exception as e:
            error_msg = f"切换子窗口失败: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def resizeEvent(self, event):
        """
        调整大小事件
        """
        super().resizeEvent(event)

    def toggle_maximize(self):
        """
        切换最大化/还原状态
        """
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def eventFilter(self, obj, event):
        """
        事件过滤器，处理鼠标滚轮事件

        Args:
            obj: 事件对象
            event: 事件

        Returns:
            bool: 是否处理了事件
        """
        if event.type() == QEvent.Wheel:
            # 将鼠标滚轮事件传递给滚动区域
            self.scroll_area.wheelEvent(event)
            return True

        return super().eventFilter(obj, event)

    def connect_scrollbar_signals(self):
        """
        连接滚动条信号
        """
        # 垂直滚动条信号
        v_scrollbar = self.scroll_area.verticalScrollBar()
        v_scrollbar.valueChanged.connect(self._on_scroll_value_changed)

        # 水平滚动条信号
        h_scrollbar = self.scroll_area.horizontalScrollBar()
        h_scrollbar.valueChanged.connect(self._on_scroll_value_changed)

    def _on_scroll_value_changed(self):
        """
        滚动条值变化处理
        """
        # 使用事件压缩器处理滚动事件
        self.scroll_event_compressor.add_event(None)

    def _handle_scroll_events(self, events):
        """
        批量处理滚动事件

        Args:
            events: 事件列表
        """
        # 使用延迟更新器更新状态栏
        self.deferred_updater.schedule_update(
            "scroll_status",
            self._update_status_batch
        )

    def _update_status_batch(self):
        """
        批量更新状态栏信息
        """
        v_scrollbar = self.scroll_area.verticalScrollBar()
        h_scrollbar = self.scroll_area.horizontalScrollBar()

        v_value = v_scrollbar.value()
        v_max = v_scrollbar.maximum()
        h_value = h_scrollbar.value()
        h_max = h_scrollbar.maximum()

        status_text = f"滚动位置 - 垂直: {v_value}/{v_max}, 水平: {h_value}/{h_max}"
        self.status_bar.showMessage(status_text)

    def closeEvent(self, event):
        """
        关闭事件，显示确认对话框

        Args:
            event: 关闭事件
        """
        reply = QMessageBox.question(
            self,
            "确认关闭",
            "确定要关闭应用程序吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # 关闭性能优化器
            self.optimizer.shutdown()
            event.accept()
        else:
            event.ignore()

    def update_status(self):
        """
        更新状态栏信息（保持兼容）
        """
        self._on_scroll_value_changed()

    def moveEvent(self, event):
        """
        移动事件
        """
        super().moveEvent(event)

    def handle_close_button(self):
        """
        处理关闭按钮点击事件
        """
        # 检查是否有打开的子菜单且子菜单有效
        if (
            hasattr(self, "active_subwindow")
            and self.active_subwindow
            and hasattr(self.active_subwindow, "windowTitle")
        ):
            # 有打开的子菜单，关闭子菜单
            self._close_subwindow()
        else:
            # 没有打开的子菜单或子菜单无效，隐藏关闭按钮
            if hasattr(self, "close_btn"):
                self.close_btn.hide()
            # 清除活动子窗体引用
            self.active_subwindow = None
            # 重置窗口标题
            self.setWindowTitle(
                self.config_manager.get("application.name", "桌面应用程序")
            )
