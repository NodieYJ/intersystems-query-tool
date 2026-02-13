#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库连接配置对话框
基于 UI/UX Pro Max 设计系统
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Tuple

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QScrollArea, QTextEdit, QVBoxLayout, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy
)

from src.infrastructure.config.config_manager import get_config_manager
from src.presentation.windows.main_window import COLORS

logger = logging.getLogger(__name__)


class ConnectionConfigDialog(QDialog):
    """
    数据库连接配置对话框 - UI/UX Pro Max 设计
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = get_config_manager()
        self.setWindowTitle("数据库连接配置")
        self.setMinimumSize(750, 700)  # 增加窗口尺寸以显示更多内容
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # 创建滚动区域作为主容器 - UI/UX Pro Max: 支持纵向滚动
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        # 创建内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)  # 增加边距
        content_layout.setSpacing(16)  # 增加间距
        
        # 数据库类型选择 - UI/UX Pro Max: 自适应高度
        self.create_db_type_section(content_layout)
        
        # 连接参数配置 - UI/UX Pro Max: 表单布局，确保所有项可见
        self.create_connection_params_section(content_layout)
        
        # 配置保存与加载 - UI/UX Pro Max: 按钮组
        self.create_config_management_section(content_layout)
        
        # 连接状态显示 - UI/UX Pro Max: 状态指示
        self.create_connection_status_section(content_layout)
        
        # 测试结果记录 - UI/UX Pro Max: 可滚动区域，5倍高度
        self.create_test_results_section(content_layout)
        
        # 添加弹性空间
        content_layout.addSpacing(20)
        
        # 设置滚动区域内容
        self.scroll_area.setWidget(content_widget)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scroll_area)
        
        # 初始化连接状态
        self.update_connection_status(False)

    def get_config_file_path(self):
        """
        获取配置文件路径 - 使用统一的配置路径服务

        Returns:
            str: 配置文件完整路径
        """
        from src.infrastructure.config.config_manager import get_config_manager
        config_manager = get_config_manager()

        # 尝试从配置管理器获取路径，如果未设置则使用默认值
        config_dir = config_manager.get("paths.config_dir", "")

        if not config_dir:
            # 使用默认值
            user_home = os.path.expanduser("~")
            config_dir = os.path.join(user_home, ".app_configs")

        # 确保目录存在
        if not os.path.exists(config_dir):
            try:
                os.makedirs(config_dir, exist_ok=True)
            except Exception as e:
                logger.error(f"创建配置目录失败: {str(e)}")
                # 回退到临时目录
                import tempfile
                config_dir = tempfile.gettempdir()

        config_file = os.path.join(config_dir, "database_connections.json")

        return config_file

    def load_configurations(self):
        """加载所有配置"""
        config_file = self.get_config_file_path()
        if not os.path.exists(config_file):
            return []
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                configurations = json.load(f)
                if not isinstance(configurations, list):
                    logger.error("配置文件格式错误: 应为列表")
                    return []
                return configurations
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            return []

    def save_configurations(self, configurations):
        """保存所有配置"""
        config_file = self.get_config_file_path()
        try:
            if not isinstance(configurations, list):
                logger.error("保存配置失败: 配置数据必须是列表格式")
                return False
            
            valid_configurations = [config for config in configurations if isinstance(config, dict)]
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(valid_configurations, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {str(e)}")
            return False

    def create_db_type_section(self, main_layout):
        """
        创建数据库类型选择区域
        UI/UX Pro Max: 自适应布局，按钮高度动态计算
        """
        db_type_group = QGroupBox("选择数据库类型")
        db_type_layout = QHBoxLayout(db_type_group)
        db_type_layout.setContentsMargins(12, 12, 12, 12)
        db_type_layout.setSpacing(12)
        
        # 使用紧凑布局
        db_type_layout.addWidget(QLabel("类型:"))
        
        self.db_type_combo = QComboBox()
        self.db_type_combo.addItems(["Cache", "IRIS"])
        db_type = self.config_manager.get("database.db_type", "Cache")
        index = self.db_type_combo.findText(db_type)
        if index >= 0:
            self.db_type_combo.setCurrentIndex(index)
        
        db_type_layout.addWidget(self.db_type_combo)
        db_type_layout.addStretch()
        
        # 设置自适应高度 - UI/UX Pro Max: 基于按钮高度调整
        db_type_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        main_layout.addWidget(db_type_group)

    def create_connection_params_section(self, main_layout):
        """
        创建连接参数配置区域
        UI/UX Pro Max: 清晰的表单布局，确保所有配置项完整可见
        """
        params_group = QGroupBox("连接参数配置")
        params_layout = QFormLayout(params_group)
        params_layout.setContentsMargins(16, 16, 16, 16)  # 增加内边距
        params_layout.setSpacing(12)  # 增加间距，确保所有内容可见
        
        # 数据库地址
        self.server_edit = QLineEdit()
        self.server_edit.setText(self.config_manager.get("database.server", ""))
        self.server_edit.setPlaceholderText("例如: localhost")
        params_layout.addRow("数据库地址:", self.server_edit)
        
        # 端口号
        self.port_edit = QLineEdit()
        self.port_edit.setText(str(self.config_manager.get("database.port", 1972)))
        self.port_edit.setPlaceholderText("例如: 1972")
        params_layout.addRow("端口号:", self.port_edit)
        
        # 命名空间
        self.namespace_edit = QLineEdit()
        self.namespace_edit.setText(self.config_manager.get("database.namespace", "USER"))
        self.namespace_edit.setPlaceholderText("例如: USER")
        params_layout.addRow("命名空间:", self.namespace_edit)
        
        # 用户名
        self.username_edit = QLineEdit()
        self.username_edit.setText(self.config_manager.get("database.username", ""))
        self.username_edit.setPlaceholderText("输入用户名")
        params_layout.addRow("用户名:", self.username_edit)
        
        # 密码
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setText(self.config_manager.get("database.password", ""))
        self.password_edit.setPlaceholderText("输入密码")
        params_layout.addRow("密码:", self.password_edit)
        
        # 设置自适应高度
        params_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        main_layout.addWidget(params_group)

    def create_config_management_section(self, main_layout):
        """
        创建配置保存与加载区域
        UI/UX Pro Max: 水平按钮组，自适应高度
        """
        management_group = QGroupBox("配置保存与加载")
        management_layout = QHBoxLayout(management_group)
        management_layout.setContentsMargins(12, 12, 12, 12)
        management_layout.setSpacing(12)
        
        # 测试连接按钮 - UI/UX Pro Max: 主要操作
        self.test_button = QPushButton("▶ 测试连接")
        self.test_button.setMinimumHeight(36)
        self.test_button.clicked.connect(self.test_connection)
        management_layout.addWidget(self.test_button)
        
        # 保存配置按钮
        self.save_button = QPushButton("💾 保存配置")
        self.save_button.setMinimumHeight(36)
        self.save_button.clicked.connect(self.save_config)
        management_layout.addWidget(self.save_button)
        
        # 加载配置按钮
        self.load_button = QPushButton("📂 加载配置")
        self.load_button.setMinimumHeight(36)
        self.load_button.clicked.connect(self.load_config)
        management_layout.addWidget(self.load_button)
        
        # 连接按钮 - UI/UX Pro Max: 强调按钮
        self.connect_button = QPushButton("🔗 连接")
        self.connect_button.setMinimumHeight(36)
        self.connect_button.setObjectName('btn_success')
        self.connect_button.clicked.connect(self.connect_database)
        management_layout.addWidget(self.connect_button)
        
        # 设置自适应高度 - UI/UX Pro Max: 基于按钮高度调整
        management_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        main_layout.addWidget(management_group)

    def create_connection_status_section(self, main_layout):
        """
        创建连接状态显示区域
        UI/UX Pro Max: 清晰的状态指示，自适应高度
        """
        status_group = QGroupBox("连接状态显示")
        status_layout = QHBoxLayout(status_group)
        status_layout.setContentsMargins(12, 12, 12, 12)
        status_layout.setSpacing(12)
        
        status_layout.addWidget(QLabel("状态:"))
        
        self.status_label = QLabel("未连接")
        self.status_label.setStyleSheet(f"color: {COLORS['error']}; font-weight: bold;")
        status_layout.addWidget(self.status_label)
        
        status_layout.addSpacing(16)
        
        self.status_details = QLabel("")
        self.status_details.setStyleSheet(f"color: {COLORS['text_secondary']};")
        status_layout.addWidget(self.status_details)
        status_layout.addStretch()
        
        # 设置自适应高度 - UI/UX Pro Max: 基于按钮高度调整
        status_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        main_layout.addWidget(status_group)

    def create_test_results_section(self, main_layout):
        """
        创建测试结果记录区域
        UI/UX Pro Max: 5倍高度，支持鼠标滚轮滚动的文本区域
        """
        results_group = QGroupBox("测试结果记录")
        results_layout = QVBoxLayout(results_group)
        results_layout.setContentsMargins(16, 16, 16, 16)
        results_layout.setSpacing(12)
        
        # 测试结果文本区域 - UI/UX Pro Max: 5倍高度
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("测试结果将显示在这里...")
        
        # 设置5倍高度 - 基础高度100px，5倍=500px，最大800px
        self.results_text.setMinimumHeight(500)
        self.results_text.setMaximumHeight(800)
        
        # 启用鼠标滚轮 - UI/UX Pro Max: 支持滚轮浏览
        self.results_text.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.results_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 确保文本区域可以接收滚轮事件
        self.results_text.setAttribute(Qt.WA_AcceptTouchEvents, False)
        
        results_layout.addWidget(self.results_text)
        
        # 清空记录按钮
        clear_button = QPushButton("🗑 清空记录")
        clear_button.setMinimumHeight(36)
        clear_button.clicked.connect(self.clear_results)
        results_layout.addWidget(clear_button)
        
        main_layout.addWidget(results_group)

    def _get_connection_params(self) -> Dict[str, str]:
        """
        获取连接参数 - 提取公共方法减少代码重复

        Returns:
            Dict[str, str]: 包含连接参数的字典
        """
        return {
            'server': self.server_edit.text().strip(),
            'port': self.port_edit.text().strip(),
            'namespace': self.namespace_edit.text().strip(),
            'username': self.username_edit.text().strip(),
            'password': self.password_edit.text().strip(),
            'db_type': self.db_type_combo.currentText()
        }

    def _validate_connection_params(self, params: Dict[str, str]) -> Tuple[bool, str]:
        """
        验证连接参数

        Args:
            params: 连接参数字典

        Returns:
            tuple: (是否有效, 错误消息)
        """
        if not params['server']:
            return False, "数据库地址不能为空"

        if not params['port'].isdigit():
            return False, "端口号必须是数字"

        return True, ""

    def _apply_connection_params(self, params: Dict[str, str]):
        """
        应用连接参数到配置管理器

        Args:
            params: 连接参数字典
        """
        self.config_manager.set("database.server", params['server'])
        self.config_manager.set("database.port", int(params['port']))
        self.config_manager.set("database.namespace", params['namespace'])
        self.config_manager.set("database.username", params['username'])
        self.config_manager.set("database.password", params['password'])
        self.config_manager.set("database.db_type", params['db_type'])

    def save_config(self):
        """保存配置"""
        try:
            server = self.server_edit.text().strip()
            port = self.port_edit.text().strip()
            namespace = self.namespace_edit.text().strip()
            username = self.username_edit.text().strip()
            password = self.password_edit.text().strip()
            db_type = self.db_type_combo.currentText()

            if not server:
                QMessageBox.warning(self, "警告", "数据库地址不能为空")
                return

            if not port.isdigit():
                QMessageBox.warning(self, "警告", "端口号必须是数字")
                return

            save_dialog = SaveConfigDialog(self)
            if save_dialog.exec_() == QDialog.Accepted:
                config_name = save_dialog.get_config_name()
                
                configurations = self.load_configurations()
                
                valid_configs = [config for config in configurations if isinstance(config, dict)]
                existing_configs = [config for config in valid_configs if config.get("name") == config_name]
                if existing_configs:
                    QMessageBox.warning(self, "警告", "配置名称已存在，请使用其他名称")
                    return
                configurations = valid_configs
                
                new_config = {
                    "name": config_name,
                    "db_type": db_type,
                    "server": server,
                    "port": int(port),
                    "namespace": namespace,
                    "username": username,
                    "password": password
                }
                
                configurations.append(new_config)
                
                if self.save_configurations(configurations):
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.add_result(f"[{timestamp}] ✅ 配置保存成功!")
                    QMessageBox.information(self, "保存结果", "配置保存成功!")
                else:
                    QMessageBox.critical(self, "保存结果", "配置保存失败，请检查权限。")

        except Exception as e:
            error_msg = f"保存配置失败: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def load_config(self):
        """加载配置"""
        try:
            configurations = self.load_configurations()
            
            if not configurations:
                QMessageBox.warning(self, "警告", "没有找到保存的配置")
                return
            
            load_dialog = LoadConfigDialog(configurations, self)
            if load_dialog.exec_() == QDialog.Accepted:
                selected_config = load_dialog.get_selected_config()
                if selected_config and isinstance(selected_config, dict):
                    self.db_type_combo.setCurrentText(selected_config.get("db_type", "Cache"))
                    self.server_edit.setText(selected_config.get("server", ""))
                    self.port_edit.setText(str(selected_config.get("port", 1972)))
                    self.namespace_edit.setText(selected_config.get("namespace", "USER"))
                    self.username_edit.setText(selected_config.get("username", ""))
                    self.password_edit.setText(selected_config.get("password", ""))
                    
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.add_result(f"[{timestamp}] ✅ 配置加载成功!")
                    QMessageBox.information(self, "加载结果", "配置加载成功!")
                else:
                    QMessageBox.warning(self, "警告", "无效的配置数据")

        except Exception as e:
            error_msg = f"加载配置失败: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def connect_database(self):
        """连接数据库 - 使用公共方法减少代码重复"""
        try:
            # 获取连接参数
            params = self._get_connection_params()

            # 验证参数
            is_valid, error_msg = self._validate_connection_params(params)
            if not is_valid:
                QMessageBox.warning(self, "警告", error_msg)
                return

            # 应用参数到配置管理器
            self._apply_connection_params(params)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.add_result(f"[{timestamp}] 🔄 开始建立数据库连接...")

            from src.business.services.data_service import get_data_service
            data_service = get_data_service()
            result = data_service.test_connection()

            if result:
                self.add_result(f"[{timestamp}] ✅ 数据库连接成功!")
                self.update_connection_status(True)
                QMessageBox.information(self, "连接结果", "数据库连接成功!")
            else:
                self.add_result(f"[{timestamp}] ❌ 数据库连接失败!")
                self.update_connection_status(False)
                QMessageBox.warning(self, "连接结果", "数据库连接失败，请检查连接参数")

        except Exception as e:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            error_msg = f"连接数据库失败: {str(e)}"
            self.add_result(f"[{timestamp}] ❌ {error_msg}")
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def update_connection_status(self, connected):
        """更新连接状态"""
        if connected:
            self.status_label.setText("已连接")
            self.status_label.setStyleSheet(f"color: {COLORS['success']}; font-weight: bold;")
            server = self.server_edit.text().strip()
            port = self.port_edit.text().strip()
            namespace = self.namespace_edit.text().strip()
            db_type = self.db_type_combo.currentText()
            self.status_details.setText(f"{db_type} - {server}:{port}/{namespace}")
            
            # 更新主窗口标题栏显示
            if self.parent():
                try:
                    self.parent()._update_connection_status(True, server, int(port) if port.isdigit() else 1972, namespace, db_type)
                except (AttributeError, TypeError):
                    pass
        else:
            self.status_label.setText("未连接")
            self.status_label.setStyleSheet(f"color: {COLORS['error']}; font-weight: bold;")
            self.status_details.setText("")
            
            # 更新主窗口标题栏显示
            if self.parent():
                try:
                    self.parent()._update_connection_status(False)
                except (AttributeError, TypeError):
                    pass

    def add_result(self, message):
        """添加测试结果"""
        self.results_text.append(message)
        # 滚动到底部
        scrollbar = self.results_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_results(self):
        """清空测试结果"""
        self.results_text.clear()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.add_result(f"[{timestamp}] 🗑 测试记录已清空")


class SaveConfigDialog(QDialog):
    """保存配置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("保存配置")
        self.setMinimumSize(400, 150)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        form_layout = QFormLayout()
        self.config_name_edit = QLineEdit()
        self.config_name_edit.setPlaceholderText("请输入配置名称")
        form_layout.addRow("配置名称:", self.config_name_edit)
        main_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 20, 0, 0)

        self.confirm_button = QPushButton("确认")
        self.confirm_button.clicked.connect(self.accept)
        button_layout.addWidget(self.confirm_button)

        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)

    def accept(self):
        config_name = self.config_name_edit.text().strip()
        if not config_name:
            QMessageBox.warning(self, "警告", "配置名称不能为空")
            return
        super().accept()

    def get_config_name(self):
        return self.config_name_edit.text().strip()


class LoadConfigDialog(QDialog):
    """加载配置对话框"""

    def __init__(self, configurations, parent=None):
        super().__init__(parent)
        self.configurations = configurations
        self.selected_config = None
        self.setWindowTitle("加载配置")
        self.setMinimumSize(800, 400)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        self.config_table = QTableWidget()
        self.config_table.setColumnCount(6)
        self.config_table.setHorizontalHeaderLabels([
            "配置名称", "数据库类型", "数据库地址", "端口号", "命名空间", "用户名"
        ])
        self.config_table.setSelectionMode(QTableWidget.SingleSelection)
        self.config_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.config_table.setAlternatingRowColors(True)
        self.config_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        self.populate_config_table()

        main_layout.addWidget(self.config_table)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 20, 0, 0)

        self.edit_button = QPushButton("编辑")
        self.edit_button.clicked.connect(self.edit_config)
        button_layout.addWidget(self.edit_button)

        self.confirm_button = QPushButton("确认")
        self.confirm_button.clicked.connect(self.accept)
        button_layout.addWidget(self.confirm_button)

        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)

    def populate_config_table(self):
        valid_configurations = [config for config in self.configurations if isinstance(config, dict)]
        self.config_table.setRowCount(len(valid_configurations))
        for row, config in enumerate(valid_configurations):
            self.config_table.setItem(row, 0, QTableWidgetItem(config.get("name", "")))
            self.config_table.setItem(row, 1, QTableWidgetItem(config.get("db_type", "")))
            self.config_table.setItem(row, 2, QTableWidgetItem(config.get("server", "")))
            self.config_table.setItem(row, 3, QTableWidgetItem(str(config.get("port", ""))))
            self.config_table.setItem(row, 4, QTableWidgetItem(config.get("namespace", "")))
            self.config_table.setItem(row, 5, QTableWidgetItem(config.get("username", "")))

    def accept(self):
        selected_items = self.config_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择一条配置")
            return
        
        row = selected_items[0].row()
        
        if row < len(self.configurations) and isinstance(self.configurations[row], dict):
            self.selected_config = self.configurations[row]
            super().accept()
        else:
            QMessageBox.warning(self, "警告", "选中的配置项无效")

    def edit_config(self):
        selected_items = self.config_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择一条配置")
            return
        
        row = selected_items[0].row()
        
        if row < len(self.configurations) and isinstance(self.configurations[row], dict):
            config = self.configurations[row]
            
            edit_dialog = ConfigEditDialog(config, self)
            if edit_dialog.exec_() == QDialog.Accepted:
                updated_config = edit_dialog.get_config()
                if isinstance(updated_config, dict):
                    self.configurations[row] = updated_config
                    self.populate_config_table()
                else:
                    QMessageBox.warning(self, "警告", "无效的配置数据")
        else:
            QMessageBox.warning(self, "警告", "选中的配置项无效")

    def get_selected_config(self):
        return self.selected_config


class ConfigEditDialog(QDialog):
    """配置编辑对话框"""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.original_config = config.copy()
        self.setWindowTitle("编辑配置")
        self.setMinimumSize(600, 400)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        params_group = QGroupBox("连接参数配置")
        params_layout = QFormLayout(params_group)
        params_layout.setContentsMargins(20, 20, 20, 20)

        self.config_name_edit = QLineEdit()
        self.config_name_edit.setText(config.get("name", ""))
        params_layout.addRow("配置名称:", self.config_name_edit)

        self.db_type_combo = QComboBox()
        self.db_type_combo.addItems(["Cache", "IRIS"])
        db_type = config.get("db_type", "Cache")
        index = self.db_type_combo.findText(db_type)
        if index >= 0:
            self.db_type_combo.setCurrentIndex(index)
        params_layout.addRow("数据库类型:", self.db_type_combo)

        self.server_edit = QLineEdit()
        self.server_edit.setText(config.get("server", ""))
        params_layout.addRow("数据库地址:", self.server_edit)

        self.port_edit = QLineEdit()
        self.port_edit.setText(str(config.get("port", 1972)))
        params_layout.addRow("端口号:", self.port_edit)

        self.namespace_edit = QLineEdit()
        self.namespace_edit.setText(config.get("namespace", "USER"))
        params_layout.addRow("命名空间:", self.namespace_edit)

        self.username_edit = QLineEdit()
        self.username_edit.setText(config.get("username", ""))
        params_layout.addRow("用户名:", self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setText(config.get("password", ""))
        params_layout.addRow("密码:", self.password_edit)

        main_layout.addWidget(params_group)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 20, 0, 0)

        self.confirm_button = QPushButton("确定")
        self.confirm_button.clicked.connect(self.accept)
        button_layout.addWidget(self.confirm_button)

        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)

    def accept(self):
        config_name = self.config_name_edit.text().strip()
        if not config_name:
            QMessageBox.warning(self, "警告", "配置名称不能为空")
            return
        
        port = self.port_edit.text().strip()
        if not port.isdigit():
            QMessageBox.warning(self, "警告", "端口号必须是数字")
            return
        
        super().accept()

    def get_config(self):
        return {
            "name": self.config_name_edit.text().strip(),
            "db_type": self.db_type_combo.currentText(),
            "server": self.server_edit.text().strip(),
            "port": int(self.port_edit.text().strip()),
            "namespace": self.namespace_edit.text().strip(),
            "username": self.username_edit.text().strip(),
            "password": self.password_edit.text().strip()
        }
