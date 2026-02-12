#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
现代化扁平设计样式演示程序
展示 modern_flat_theme.py 中的所有样式效果
"""

import sys
import random
from datetime import datetime, timedelta

from PySide2.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QTableWidget,
    QTableWidgetItem, QGroupBox, QTabWidget, QProgressBar, QCheckBox,
    QRadioButton, QSlider, QSpinBox, QDoubleSpinBox, QDateEdit,
    QListWidget, QTreeWidget, QTreeWidgetItem, QFrame, QScrollArea,
    QSplitter, QMenuBar, QMenu, QAction, QStatusBar, QMessageBox,
    QFileDialog, QDialog, QDialogButtonBox, QFormLayout, QGridLayout,
    QSizePolicy
)
from PySide2.QtCore import Qt, QSize, QTimer
from PySide2.QtGui import QIcon, QFont, QColor

# 导入样式系统
from modern_flat_theme import (
    get_complete_style, get_button_style, get_label_style,
    COLORS, TYPOGRAPHY, SPACING, BORDER_RADIUS
)


class StyleDemoWindow(QMainWindow):
    """样式演示主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎨 现代化扁平设计样式演示")
        self.setGeometry(100, 100, 1600, 1000)
        self.setMinimumSize(1200, 800)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 创建左侧导航
        self.create_left_sidebar()
        main_layout.addWidget(self.sidebar, 1)
        
        # 创建右侧内容区
        self.create_content_area()
        main_layout.addWidget(self.content_area, 4)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 默认显示概览页
        self.show_overview()
    
    def create_left_sidebar(self):
        """创建左侧导航栏"""
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(260)
        self.sidebar.setObjectName("sidebar")
        
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(20, 24, 20, 24)
        layout.setSpacing(10)
        
        # Logo/标题
        title_label = QLabel("🎨 样式演示")
        title_label.setObjectName("sidebar-title")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 22px;
                font-weight: 600;
                color: {COLORS['primary']};
                padding-bottom: 12px;
            }}
        """)
        layout.addWidget(title_label)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"background-color: {COLORS['divider']};")
        line.setFixedHeight(1)
        layout.addWidget(line)
        
        layout.addSpacing(16)
        
        # 导航按钮
        nav_items = [
            ("📊 概览", self.show_overview),
            ("🔘 按钮样式", self.show_buttons),
            ("📝 表单控件", self.show_forms),
            ("📋 数据表格", self.show_tables),
            ("🗂️ 选项卡", self.show_tabs),
            ("📊 进度指示", self.show_progress),
            ("🌳 树形列表", self.show_trees),
            ("💬 消息通知", self.show_messages),
            ("🎨 颜色系统", self.show_colors),
        ]
        
        self.nav_buttons = []
        for text, callback in nav_items:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setObjectName("nav-button")
            btn.setMinimumHeight(44)
            btn.setStyleSheet(f"""
                QPushButton {{
                    text-align: left;
                    padding: 12px 16px;
                    border: none;
                    border-radius: {BORDER_RADIUS['md']}px;
                    background: transparent;
                    color: {COLORS['text_primary']};
                    font-size: 15px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['primary_light']};
                    color: {COLORS['primary']};
                }}
                QPushButton:checked {{
                    background-color: {COLORS['primary_light']};
                    color: {COLORS['primary']};
                    border-left: 3px solid {COLORS['primary']};
                }}
            """)
            btn.clicked.connect(callback)
            layout.addWidget(btn)
            self.nav_buttons.append(btn)
        
        layout.addStretch()
        
        # 底部信息
        info_label = QLabel("UI/UX Pro Max\n现代化扁平设计")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 12px;
                padding: 12px;
            }}
        """)
        layout.addWidget(info_label)
    
    def create_content_area(self):
        """创建右侧内容区域"""
        self.content_area = QScrollArea()
        self.content_area.setWidgetResizable(True)
        self.content_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.content_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 内容容器
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(32, 32, 32, 32)
        self.content_layout.setSpacing(24)
        
        self.content_area.setWidget(self.content_widget)
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        new_action = QAction("新建", self)
        new_action.setShortcut("Ctrl+N")
        file_menu.addAction(new_action)
        
        open_action = QAction("打开", self)
        open_action.setShortcut("Ctrl+O")
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")
        edit_menu.addAction("撤销")
        edit_menu.addAction("重做")
        edit_menu.addSeparator()
        edit_menu.addAction("剪切")
        edit_menu.addAction("复制")
        edit_menu.addAction("粘贴")
        
        # 视图菜单
        view_menu = menubar.addMenu("视图")
        view_menu.addAction("放大")
        view_menu.addAction("缩小")
        view_menu.addAction("重置缩放")
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        help_menu.addAction("文档")
        help_menu.addAction("关于")
    
    def create_status_bar(self):
        """创建状态栏"""
        statusbar = self.statusBar()
        statusbar.showMessage("就绪")
        
        # 添加永久部件
        statusbar.addPermanentWidget(QLabel("UI/UX Pro Max 设计系统"))
    
    def clear_content(self):
        """清空内容区域"""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def set_active_nav(self, index):
        """设置当前导航项"""
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
    
    # ==================== 各个演示页面 ====================
    
    def show_overview(self):
        """显示概览页面"""
        self.set_active_nav(0)
        self.clear_content()
        
        # 标题
        title = QLabel("📊 设计系统概览")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 32px;
                font-weight: 700;
                color: {COLORS['text_primary']};
                margin-bottom: 8px;
            }}
        """)
        self.content_layout.addWidget(title)
        
        # 简介
        desc = QLabel("现代化扁平设计系统 - 基于 UI/UX Pro Max\n专业、清晰、现代的桌面应用界面设计")
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 16px;")
        self.content_layout.addWidget(desc)
        
        self.content_layout.addSpacing(20)
        
        # 统计卡片
        stats_layout = QHBoxLayout()
        
        stats = [
            ("颜色变量", "12+", "主色/功能色/中性色"),
            ("组件样式", "20+", "按钮/表单/表格/导航"),
            ("字体层级", "8级", "从 11px 到 24px"),
            ("圆角规格", "5级", "从 0px 到 12px"),
        ]
        
        for title, value, subtitle in stats:
            card = self.create_stat_card(title, value, subtitle)
            stats_layout.addWidget(card)
        
        self.content_layout.addLayout(stats_layout)
        
        self.content_layout.addSpacing(20)
        
        # 设计原则
        principles_group = QGroupBox("🎯 设计原则")
        principles_layout = QVBoxLayout(principles_group)
        
        principles = [
            "✅ 扁平化设计 - 无渐变、无纹理、纯色块",
            "✅ 现代圆角 - 6-8px 统一圆角系统",
            "✅ 层次阴影 - 极浅阴影 0 1px 3px rgba(0,0,0,0.1)",
            "✅ 微交互 - 150-300ms 平滑过渡动画",
            "✅ 无障碍 - WCAG AA 对比度、键盘导航支持",
        ]
        
        for principle in principles:
            label = QLabel(principle)
            label.setStyleSheet(f"padding: 6px 0; color: {COLORS['text_primary']};")
            principles_layout.addWidget(label)
        
        self.content_layout.addWidget(principles_group)
        
        # 快速开始
        quick_group = QGroupBox("🚀 快速开始")
        quick_layout = QVBoxLayout(quick_group)
        
        code_label = QLabel("""from modern_flat_theme import get_complete_style, COLORS

# 应用完整样式
app.setStyleSheet(get_complete_style())

# 使用颜色变量
button.setStyleSheet(f"background-color: {COLORS['primary']};")""")
        code_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['background']};
                padding: 16px;
                border-radius: {BORDER_RADIUS['md']}px;
                font-family: {TYPOGRAPHY['font_mono']};
                font-size: {TYPOGRAPHY['size_sm']};
                color: {COLORS['text_primary']};
            }}
        """)
        quick_layout.addWidget(code_label)
        
        self.content_layout.addWidget(quick_group)
        
        self.content_layout.addStretch()
    
    def create_stat_card(self, title, value, subtitle):
        """创建统计卡片"""
        card = QFrame()
        card.setMinimumHeight(140)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: {BORDER_RADIUS['lg']}px;
                padding: 24px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(12)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px; text-transform: uppercase;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {COLORS['primary']}; font-size: 36px; font-weight: 700;")
        layout.addWidget(value_label)
        
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet(f"color: {COLORS['text_disabled']}; font-size: 12px;")
        layout.addWidget(subtitle_label)
        
        return card
    
    def show_buttons(self):
        """显示按钮样式页面"""
        self.set_active_nav(1)
        self.clear_content()
        
        # 标题
        title = QLabel("🔘 按钮样式")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 32px;
                font-weight: 700;
                color: {COLORS['text_primary']};
                margin-bottom: 8px;
            }}
        """)
        self.content_layout.addWidget(title)
        
        # 主要按钮
        primary_group = QGroupBox("主要按钮 (Primary)")
        primary_layout = QHBoxLayout(primary_group)
        
        btn_primary = QPushButton("主要按钮")
        btn_primary.setStyleSheet(get_button_style("primary"))
        primary_layout.addWidget(btn_primary)
        
        btn_primary_hover = QPushButton("悬停状态")
        btn_primary_hover.setStyleSheet(get_button_style("primary"))
        btn_primary_hover.setEnabled(False)
        primary_layout.addWidget(btn_primary_hover)
        
        btn_primary_disabled = QPushButton("禁用状态")
        btn_primary_disabled.setEnabled(False)
        btn_primary_disabled.setStyleSheet(get_button_style("primary"))
        primary_layout.addWidget(btn_primary_disabled)
        
        primary_layout.addStretch()
        self.content_layout.addWidget(primary_group)
        
        # 次要按钮
        secondary_group = QGroupBox("次要按钮 (Secondary)")
        secondary_layout = QHBoxLayout(secondary_group)
        
        btn_secondary = QPushButton("次要按钮")
        btn_secondary.setStyleSheet(get_button_style("secondary"))
        secondary_layout.addWidget(btn_secondary)
        
        btn_secondary_hover = QPushButton("悬停状态")
        btn_secondary_hover.setStyleSheet(get_button_style("secondary"))
        btn_secondary_hover.setEnabled(False)
        secondary_layout.addWidget(btn_secondary_hover)
        
        secondary_layout.addStretch()
        self.content_layout.addWidget(secondary_group)
        
        # 文字按钮
        text_group = QGroupBox("文字按钮 (Text)")
        text_layout = QHBoxLayout(text_group)
        
        btn_text = QPushButton("文字按钮")
        btn_text.setStyleSheet(get_button_style("text"))
        text_layout.addWidget(btn_text)
        
        btn_text_hover = QPushButton("悬停状态")
        btn_text_hover.setStyleSheet(get_button_style("text"))
        text_layout.addWidget(btn_text_hover)
        
        text_layout.addStretch()
        self.content_layout.addWidget(text_group)
        
        # 危险按钮
        danger_group = QGroupBox("危险按钮 (Danger)")
        danger_layout = QHBoxLayout(danger_group)
        
        btn_danger = QPushButton("删除")
        btn_danger.setStyleSheet(get_button_style("danger"))
        danger_layout.addWidget(btn_danger)
        
        btn_danger_hover = QPushButton("悬停状态")
        btn_danger_hover.setStyleSheet(get_button_style("danger"))
        btn_danger_hover.setEnabled(False)
        danger_layout.addWidget(btn_danger_hover)
        
        danger_layout.addStretch()
        self.content_layout.addWidget(danger_group)
        
        # 按钮尺寸
        size_group = QGroupBox("按钮尺寸")
        size_layout = QHBoxLayout(size_group)
        
        btn_small = QPushButton("小按钮")
        btn_small.setStyleSheet(get_button_style("primary"))
        btn_small.setFixedHeight(28)
        size_layout.addWidget(btn_small)
        
        btn_normal = QPushButton("正常按钮")
        btn_normal.setStyleSheet(get_button_style("primary"))
        size_layout.addWidget(btn_normal)
        
        btn_large = QPushButton("大按钮")
        btn_large.setStyleSheet(get_button_style("primary"))
        btn_large.setFixedHeight(44)
        size_layout.addWidget(btn_large)
        
        size_layout.addStretch()
        self.content_layout.addWidget(size_group)
        
        # 按钮组
        group_group = QGroupBox("按钮组合")
        group_layout = QHBoxLayout(group_group)
        
        btn_ok = QPushButton("确认")
        btn_ok.setStyleSheet(get_button_style("primary"))
        group_layout.addWidget(btn_ok)
        
        btn_cancel = QPushButton("取消")
        btn_cancel.setStyleSheet(get_button_style("secondary"))
        group_layout.addWidget(btn_cancel)
        
        btn_more = QPushButton("更多操作")
        btn_more.setStyleSheet(get_button_style("text"))
        group_layout.addWidget(btn_more)
        
        group_layout.addStretch()
        self.content_layout.addWidget(group_group)
        
        self.content_layout.addStretch()
    
    def show_forms(self):
        """显示表单控件页面"""
        self.set_active_nav(2)
        self.clear_content()
        
        # 标题
        title = QLabel("📝 表单控件")
        title.setStyleSheet(get_label_style("title"))
        self.content_layout.addWidget(title)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：基础输入
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 输入框
        input_group = QGroupBox("文本输入")
        input_layout = QFormLayout(input_group)
        
        line_edit = QLineEdit()
        line_edit.setPlaceholderText("请输入文本...")
        input_layout.addRow("单行文本:", line_edit)
        
        line_edit_disabled = QLineEdit()
        line_edit_disabled.setText("禁用状态")
        line_edit_disabled.setEnabled(False)
        input_layout.addRow("禁用状态:", line_edit_disabled)
        
        password_edit = QLineEdit()
        password_edit.setEchoMode(QLineEdit.Password)
        password_edit.setPlaceholderText("请输入密码...")
        input_layout.addRow("密码输入:", password_edit)
        
        left_layout.addWidget(input_group)
        
        # 多行文本
        text_group = QGroupBox("多行文本")
        text_layout = QVBoxLayout(text_group)
        
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("请输入多行文本...\n支持多行输入")
        text_edit.setMaximumHeight(100)
        text_layout.addWidget(text_edit)
        
        left_layout.addWidget(text_group)
        
        # 下拉选择
        combo_group = QGroupBox("下拉选择")
        combo_layout = QVBoxLayout(combo_group)
        
        combo = QComboBox()
        combo.addItems(["请选择...", "选项 1", "选项 2", "选项 3", "选项 4"])
        combo_layout.addWidget(combo)
        
        left_layout.addWidget(combo_group)
        
        left_layout.addStretch()
        splitter.addWidget(left_widget)
        
        # 右侧：其他控件
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 复选框和单选框
        check_group = QGroupBox("选择控件")
        check_layout = QVBoxLayout(check_group)
        
        check1 = QCheckBox("选项 1（未选中）")
        check2 = QCheckBox("选项 2（已选中）")
        check2.setChecked(True)
        check3 = QCheckBox("选项 3（禁用）")
        check3.setEnabled(False)
        
        check_layout.addWidget(check1)
        check_layout.addWidget(check2)
        check_layout.addWidget(check3)
        
        check_layout.addSpacing(10)
        
        radio1 = QRadioButton("单选 A")
        radio2 = QRadioButton("单选 B")
        radio2.setChecked(True)
        radio3 = QRadioButton("单选 C（禁用）")
        radio3.setEnabled(False)
        
        check_layout.addWidget(radio1)
        check_layout.addWidget(radio2)
        check_layout.addWidget(radio3)
        
        right_layout.addWidget(check_group)
        
        # 数值输入
        num_group = QGroupBox("数值输入")
        num_layout = QFormLayout(num_group)
        
        spin_box = QSpinBox()
        spin_box.setRange(0, 100)
        spin_box.setValue(50)
        num_layout.addRow("整数:", spin_box)
        
        double_spin = QDoubleSpinBox()
        double_spin.setRange(0, 100)
        double_spin.setValue(3.14)
        double_spin.setDecimals(2)
        num_layout.addRow("小数:", double_spin)
        
        right_layout.addWidget(num_group)
        
        # 滑块
        slider_group = QGroupBox("滑块")
        slider_layout = QVBoxLayout(slider_group)
        
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(65)
        slider_layout.addWidget(slider)
        
        slider_label = QLabel("当前值: 65")
        slider_label.setAlignment(Qt.AlignCenter)
        slider.valueChanged.connect(lambda v: slider_label.setText(f"当前值: {v}"))
        slider_layout.addWidget(slider_label)
        
        right_layout.addWidget(slider_group)
        
        # 日期选择
        date_group = QGroupBox("日期选择")
        date_layout = QVBoxLayout(date_group)
        
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(datetime.now())
        date_layout.addWidget(date_edit)
        
        right_layout.addWidget(date_group)
        
        right_layout.addStretch()
        splitter.addWidget(right_widget)
        
        splitter.setSizes([500, 500])
        self.content_layout.addWidget(splitter)
    
    def show_tables(self):
        """显示数据表格页面"""
        self.set_active_nav(3)
        self.clear_content()
        
        # 标题
        title = QLabel("📋 数据表格")
        title.setStyleSheet(get_label_style("title"))
        self.content_layout.addWidget(title)
        
        # 表格
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["ID", "用户名", "邮箱", "部门", "状态", "创建时间"])
        
        # 添加示例数据
        departments = ["技术部", "产品部", "设计部", "运营部", "市场部"]
        statuses = [("激活", COLORS['success']), ("暂停", COLORS['warning']), ("禁用", COLORS['error'])]
        
        for i in range(20):
            row = table.rowCount()
            table.insertRow(row)
            
            # ID
            table.setItem(row, 0, QTableWidgetItem(str(i + 1)))
            
            # 用户名
            table.setItem(row, 1, QTableWidgetItem(f"用户 {i + 1}"))
            
            # 邮箱
            table.setItem(row, 2, QTableWidgetItem(f"user{i+1}@example.com"))
            
            # 部门
            table.setItem(row, 3, QTableWidgetItem(random.choice(departments)))
            
            # 状态（带颜色）
            status, color = random.choice(statuses)
            status_item = QTableWidgetItem(status)
            status_item.setForeground(QColor(color))
            table.setItem(row, 4, status_item)
            
            # 创建时间
            date = datetime.now() - timedelta(days=random.randint(1, 365))
            table.setItem(row, 5, QTableWidgetItem(date.strftime("%Y-%m-%d")))
        
        table.setMinimumHeight(400)
        self.content_layout.addWidget(table)
        
        # 按钮组
        btn_layout = QHBoxLayout()
        
        btn_add = QPushButton("➕ 添加")
        btn_add.setStyleSheet(get_button_style("primary"))
        btn_layout.addWidget(btn_add)
        
        btn_edit = QPushButton("✏️ 编辑")
        btn_edit.setStyleSheet(get_button_style("secondary"))
        btn_layout.addWidget(btn_edit)
        
        btn_delete = QPushButton("🗑️ 删除")
        btn_delete.setStyleSheet(get_button_style("danger"))
        btn_layout.addWidget(btn_delete)
        
        btn_layout.addStretch()
        
        btn_export = QPushButton("📥 导出")
        btn_export.setStyleSheet(get_button_style("secondary"))
        btn_layout.addWidget(btn_export)
        
        self.content_layout.addLayout(btn_layout)
    
    def show_tabs(self):
        """显示选项卡页面"""
        self.set_active_nav(4)
        self.clear_content()
        
        # 标题
        title = QLabel("🗂️ 选项卡")
        title.setStyleSheet(get_label_style("title"))
        self.content_layout.addWidget(title)
        
        # 选项卡控件
        tabs = QTabWidget()
        
        # 选项卡 1
        tab1 = QWidget()
        tab1_layout = QVBoxLayout(tab1)
        tab1_layout.addWidget(QLabel("这是第一个选项卡的内容"))
        tab1_layout.addWidget(QPushButton("选项卡 1 的按钮"))
        tab1_layout.addStretch()
        tabs.addTab(tab1, "📊 数据统计")
        
        # 选项卡 2
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        tab2_layout.addWidget(QLabel("这是第二个选项卡的内容"))
        
        form_layout = QFormLayout()
        form_layout.addRow("名称:", QLineEdit())
        form_layout.addRow("描述:", QTextEdit())
        tab2_layout.addLayout(form_layout)
        tab2_layout.addStretch()
        tabs.addTab(tab2, "⚙️ 设置")
        
        # 选项卡 3
        tab3 = QWidget()
        tab3_layout = QVBoxLayout(tab3)
        
        list_widget = QListWidget()
        list_widget.addItems(["项目 1", "项目 2", "项目 3", "项目 4", "项目 5"])
        tab3_layout.addWidget(list_widget)
        tabs.addTab(tab3, "📋 列表")
        
        # 选项卡 4
        tab4 = QWidget()
        tab4_layout = QVBoxLayout(tab4)
        tab4_layout.addWidget(QLabel("关于信息"))
        tab4_layout.addWidget(QLabel("版本: 1.0.0"))
        tab4_layout.addWidget(QLabel("作者: UI/UX Pro Max"))
        tab4_layout.addStretch()
        tabs.addTab(tab4, "ℹ️ 关于")
        
        self.content_layout.addWidget(tabs)
    
    def show_progress(self):
        """显示进度指示页面"""
        self.set_active_nav(5)
        self.clear_content()
        
        # 标题
        title = QLabel("📊 进度指示")
        title.setStyleSheet(get_label_style("title"))
        self.content_layout.addWidget(title)
        
        # 进度条组
        progress_group = QGroupBox("进度条样式")
        progress_layout = QVBoxLayout(progress_group)
        
        # 不同进度
        for value in [25, 50, 75, 100]:
            label = QLabel(f"进度 {value}%:")
            progress_layout.addWidget(label)
            
            progress = QProgressBar()
            progress.setValue(value)
            progress.setFormat(f"{value}%")
            progress_layout.addWidget(progress)
            progress_layout.addSpacing(10)
        
        self.content_layout.addWidget(progress_group)
        
        # 动态进度
        dynamic_group = QGroupBox("动态进度")
        dynamic_layout = QVBoxLayout(dynamic_group)
        
        self.dynamic_progress = QProgressBar()
        self.dynamic_progress.setRange(0, 100)
        self.dynamic_progress.setValue(0)
        dynamic_layout.addWidget(self.dynamic_progress)
        
        btn_layout = QHBoxLayout()
        
        btn_start = QPushButton("▶️ 开始")
        btn_start.setStyleSheet(get_button_style("primary"))
        btn_start.clicked.connect(self.start_progress)
        btn_layout.addWidget(btn_start)
        
        btn_reset = QPushButton("🔄 重置")
        btn_reset.setStyleSheet(get_button_style("secondary"))
        btn_reset.clicked.connect(self.reset_progress)
        btn_layout.addWidget(btn_reset)
        
        btn_layout.addStretch()
        dynamic_layout.addLayout(btn_layout)
        
        self.content_layout.addWidget(dynamic_group)
        
        # 状态标签
        status_group = QGroupBox("状态标签")
        status_layout = QHBoxLayout(status_group)
        
        statuses = [
            ("✅ 成功", COLORS['success'], "#D1FAE5"),
            ("⚠️ 警告", COLORS['warning'], "#FEF3C7"),
            ("❌ 错误", COLORS['error'], "#FEE2E2"),
            ("ℹ️ 信息", COLORS['info'], "#DBEAFE"),
        ]
        
        for text, color, bg in statuses:
            label = QLabel(text)
            label.setStyleSheet(f"""
                QLabel {{
                    background-color: {bg};
                    color: {color};
                    padding: 6px 12px;
                    border-radius: 12px;
                    font-weight: 500;
                }}
            """)
            status_layout.addWidget(label)
        
        status_layout.addStretch()
        self.content_layout.addWidget(status_group)
        
        self.content_layout.addStretch()
    
    def start_progress(self):
        """开始进度动画"""
        self.progress_value = 0
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(50)
    
    def update_progress(self):
        """更新进度"""
        self.progress_value += 1
        self.dynamic_progress.setValue(self.progress_value)
        
        if self.progress_value >= 100:
            self.progress_timer.stop()
    
    def reset_progress(self):
        """重置进度"""
        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()
        self.dynamic_progress.setValue(0)
    
    def show_trees(self):
        """显示树形列表页面"""
        self.set_active_nav(6)
        self.clear_content()
        
        # 标题
        title = QLabel("🌳 树形列表")
        title.setStyleSheet(get_label_style("title"))
        self.content_layout.addWidget(title)
        
        # 树形控件
        tree = QTreeWidget()
        tree.setHeaderLabels(["名称", "类型", "大小"])
        tree.setColumnWidth(0, 300)
        
        # 添加节点
        root1 = QTreeWidgetItem(tree, ["📁 项目文件", "文件夹", "-"])
        
        child1 = QTreeWidgetItem(root1, ["📄 README.md", "文档", "2 KB"])
        child2 = QTreeWidgetItem(root1, ["📄 main.py", "Python", "5 KB"])
        child3 = QTreeWidgetItem(root1, ["📄 config.json", "JSON", "1 KB"])
        
        subfolder = QTreeWidgetItem(root1, ["📁 src", "文件夹", "-"])
        QTreeWidgetItem(subfolder, ["📄 utils.py", "Python", "3 KB"])
        QTreeWidgetItem(subfolder, ["📄 models.py", "Python", "4 KB"])
        
        root2 = QTreeWidgetItem(tree, ["📁 资源文件", "文件夹", "-"])
        QTreeWidgetItem(root2, ["🖼️ logo.png", "图片", "15 KB"])
        QTreeWidgetItem(root2, ["🎨 styles.css", "CSS", "8 KB"])
        
        root3 = QTreeWidgetItem(tree, ["📁 文档", "文件夹", "-"])
        QTreeWidgetItem(root3, ["📄 设计规范.pdf", "PDF", "2.5 MB"])
        QTreeWidgetItem(root3, ["📄 API 文档.md", "Markdown", "12 KB"])
        
        tree.expandAll()
        tree.setMinimumHeight(400)
        self.content_layout.addWidget(tree)
    
    def show_messages(self):
        """显示消息通知页面"""
        self.set_active_nav(7)
        self.clear_content()
        
        # 标题
        title = QLabel("💬 消息通知")
        title.setStyleSheet(get_label_style("title"))
        self.content_layout.addWidget(title)
        
        # 消息按钮组
        group = QGroupBox("消息类型")
        layout = QVBoxLayout(group)
        
        btn_layout = QHBoxLayout()
        
        btn_info = QPushButton("ℹ️ 信息消息")
        btn_info.setStyleSheet(get_button_style("primary"))
        btn_info.clicked.connect(lambda: self.show_message("info"))
        btn_layout.addWidget(btn_info)
        
        btn_warning = QPushButton("⚠️ 警告消息")
        btn_warning.setStyleSheet(get_button_style("secondary"))
        btn_warning.clicked.connect(lambda: self.show_message("warning"))
        btn_layout.addWidget(btn_warning)
        
        btn_error = QPushButton("❌ 错误消息")
        btn_error.setStyleSheet(get_button_style("danger"))
        btn_error.clicked.connect(lambda: self.show_message("error"))
        btn_layout.addWidget(btn_error)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        btn_question = QPushButton("❓ 确认对话框")
        btn_question.setStyleSheet(get_button_style("primary"))
        btn_question.clicked.connect(self.show_question)
        layout.addWidget(btn_question)
        
        layout.addStretch()
        self.content_layout.addWidget(group)
        
        # 使用说明
        info_group = QGroupBox("消息框样式说明")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QLabel("""
        在现代化扁平设计中，消息框具有以下特点：
        
        • 圆角边框 (12px)
        • 柔和阴影 (0 10px 15px rgba(0,0,0,0.1))
        • 清晰的图标和标题
        • 高对比度文字
        • 明确的操作按钮
        
        不同类型的消息使用不同的颜色：
        - 信息: 蓝色 (#3B82F6)
        - 警告: 琥珀色 (#F59E0B)
        - 错误: 红色 (#EF4444)
        - 成功: 绿色 (#10B981)
        """)
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        self.content_layout.addWidget(info_group)
        self.content_layout.addStretch()
    
    def show_message(self, msg_type):
        """显示消息框"""
        messages = {
            "info": ("信息", "这是一条信息消息，用于显示一般性提示。", QMessageBox.Information),
            "warning": ("警告", "这是一条警告消息，需要注意但不一定阻止操作。", QMessageBox.Warning),
            "error": ("错误", "这是一条错误消息，操作未能成功完成。", QMessageBox.Critical),
        }
        
        title, text, icon = messages.get(msg_type, messages["info"])
        QMessageBox.information(self, title, text) if icon == QMessageBox.Information else \
        QMessageBox.warning(self, title, text) if icon == QMessageBox.Warning else \
        QMessageBox.critical(self, title, text)
    
    def show_question(self):
        """显示确认对话框"""
        reply = QMessageBox.question(
            self,
            "确认操作",
            "确定要执行此操作吗？\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "成功", "操作已确认执行！")
    
    def show_colors(self):
        """显示颜色系统页面"""
        self.set_active_nav(8)
        self.clear_content()
        
        # 标题
        title = QLabel("🎨 颜色系统")
        title.setStyleSheet(get_label_style("title"))
        self.content_layout.addWidget(title)
        
        # 颜色展示
        color_groups = [
            ("主色", [
                ("primary", "主色"),
                ("primary_hover", "悬停"),
                ("primary_light", "浅色背景"),
            ]),
            ("功能色", [
                ("success", "成功"),
                ("warning", "警告"),
                ("error", "错误"),
                ("info", "信息"),
            ]),
            ("中性色", [
                ("background", "页面背景"),
                ("surface", "卡片表面"),
                ("border", "边框"),
                ("divider", "分隔线"),
            ]),
            ("文字色", [
                ("text_primary", "主要文字"),
                ("text_secondary", "次要文字"),
                ("text_disabled", "禁用文字"),
            ]),
        ]
        
        for group_name, colors in color_groups:
            group = QGroupBox(group_name)
            group_layout = QHBoxLayout(group)
            
            for color_key, color_name in colors:
                color_widget = self.create_color_card(color_key, color_name)
                group_layout.addWidget(color_widget)
            
            group_layout.addStretch()
            self.content_layout.addWidget(group)
        
        # 使用说明
        usage_group = QGroupBox("颜色使用指南")
        usage_layout = QVBoxLayout(usage_group)
        
        usage_text = QLabel("""
        <b>主色 (Primary)</b> - 用于主要操作按钮、链接、选中状态<br>
        <b>功能色</b> - 用于状态指示：成功(绿)、警告(琥珀)、错误(红)、信息(蓝)<br>
        <b>中性色</b> - 用于背景、边框、分隔线等界面元素<br>
        <b>文字色</b> - 用于文本：主要文字(深色)、次要文字(中灰)、禁用(浅灰)<br><br>
        
        <b>无障碍标准：</b><br>
        • 正文文字对比度 ≥ 4.5:1 (WCAG AA)<br>
        • 大文字对比度 ≥ 3:1<br>
        • 禁用状态仍可辨识
        """)
        usage_text.setWordWrap(True)
        usage_text.setTextFormat(Qt.RichText)
        usage_layout.addWidget(usage_text)
        
        self.content_layout.addWidget(usage_group)
        self.content_layout.addStretch()
    
    def create_color_card(self, color_key, color_name):
        """创建颜色卡片"""
        card = QFrame()
        card.setFixedSize(120, 100)
        
        color_value = COLORS.get(color_key, "#000000")
        
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color_value};
                border: 2px solid {COLORS['border']};
                border-radius: {BORDER_RADIUS['md']}px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        # 如果是深色背景，文字用白色
        is_dark = color_key in ["primary", "primary_hover", "text_primary"]
        text_color = "#FFFFFF" if is_dark else COLORS['text_primary']
        
        name_label = QLabel(color_name)
        name_label.setStyleSheet(f"color: {text_color}; font-weight: 600;")
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)
        
        value_label = QLabel(color_value)
        value_label.setStyleSheet(f"color: {text_color}; font-size: 10px;")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        return card


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 应用现代化扁平设计样式
    app.setStyleSheet(get_complete_style())
    
    # 创建并显示窗口
    window = StyleDemoWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
