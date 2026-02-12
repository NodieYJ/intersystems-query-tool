#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PySide2 样式演示程序 v2
现代化扁平设计系统演示
"""

import sys
from PySide2.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QCheckBox,
    QRadioButton, QGroupBox, QTableWidget, QTableWidgetItem, QTabWidget,
    QProgressBar, QFrame, QScrollArea, QStackedWidget, QListWidget,
    QListWidgetItem, QSizePolicy, QHeaderView, QButtonGroup
)
from PySide2.QtCore import Qt, QSize
from PySide2.QtGui import QColor, QPalette, QFont


# 颜色定义
COLORS = {
    'primary': '#2563EB',
    'primary_hover': '#1D4ED8',
    'primary_light': '#DBEAFE',
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


class StyleDemoWindow(QMainWindow):
    """样式演示主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('PySide2 样式演示')
        self.setGeometry(100, 100, 1280, 800)
        self.setMinimumSize(1000, 600)

        # 设置全局样式
        self.setStyleSheet(self.get_global_style())

        # 创建主部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # 主布局
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建侧边栏
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)

        # 创建内容区域
        content_area = self.create_content_area()
        main_layout.addWidget(content_area)

        # 默认显示概览页面
        self.show_page(0)

    def get_global_style(self) -> str:
        """获取全局 QSS 样式"""
        return f"""
        /* 全局样式 */
        QWidget {{
            font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            font-size: 14px;
            color: {COLORS['text_primary']};
        }}

        /* 侧边栏样式 */
        #sidebar {{
            background-color: {COLORS['surface']};
            border-right: 1px solid {COLORS['border']};
        }}

        #sidebar_title {{
            font-size: 18px;
            font-weight: 600;
            color: {COLORS['primary']};
            padding: 10px 0;
            border-bottom: 1px solid {COLORS['divider']};
            margin-bottom: 16px;
        }}

        #sidebar_footer {{
            color: {COLORS['text_secondary']};
            font-size: 11px;
        }}

        /* 导航按钮样式 */
        QPushButton#nav_btn {{
            background-color: transparent;
            border: none;
            border-radius: 6px;
            padding: 10px 14px;
            text-align: left;
            font-size: 14px;
            color: {COLORS['text_primary']};
            margin-bottom: 4px;
        }}

        QPushButton#nav_btn:hover {{
            background-color: {COLORS['primary_light']};
            color: {COLORS['primary']};
        }}

        QPushButton#nav_btn:checked {{
            background-color: {COLORS['primary_light']};
            color: {COLORS['primary']};
            border-left: 3px solid {COLORS['primary']};
        }}

        /* 内容区域样式 */
        #content_area {{
            background-color: {COLORS['background']};
        }}

        #header {{
            background-color: {COLORS['surface']};
            border-bottom: 1px solid {COLORS['border']};
        }}

        #header_title {{
            font-size: 20px;
            font-weight: 600;
        }}

        /* 页面标题样式 */
        #page_title {{
            font-size: 24px;
            font-weight: 700;
            color: {COLORS['text_primary']};
            margin-bottom: 8px;
        }}

        #page_subtitle {{
            color: {COLORS['text_secondary']};
            font-size: 14px;
            margin-bottom: 24px;
        }}

        /* 卡片样式 (GroupBox) */
        QGroupBox {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 0;
            top: 0;
            padding: 0 0 12px 0;
            font-size: 16px;
            font-weight: 600;
            color: {COLORS['text_primary']};
            border-bottom: 1px solid {COLORS['divider']};
        }}

        /* 统计卡片样式 */
        #stat_card {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: 20px;
        }}

        #stat_title {{
            color: {COLORS['text_secondary']};
            font-size: 12px;
            text-transform: uppercase;
        }}

        #stat_value {{
            color: {COLORS['primary']};
            font-size: 32px;
            font-weight: 700;
        }}

        /* 按钮样式 */
        QPushButton#btn_primary {{
            background-color: {COLORS['primary']};
            color: {COLORS['text_inverse']};
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            height: 36px;
            font-weight: 500;
        }}

        QPushButton#btn_primary:hover {{
            background-color: {COLORS['primary_hover']};
        }}

        QPushButton#btn_secondary {{
            background-color: {COLORS['surface']};
            color: {COLORS['primary']};
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
            padding: 8px 16px;
            height: 36px;
            font-weight: 500;
        }}

        QPushButton#btn_secondary:hover {{
            background-color: {COLORS['primary_light']};
            border-color: {COLORS['primary']};
        }}

        QPushButton#btn_text {{
            background-color: transparent;
            color: {COLORS['primary']};
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            height: 36px;
            font-weight: 500;
        }}

        QPushButton#btn_text:hover {{
            background-color: {COLORS['primary_light']};
        }}

        QPushButton#btn_danger {{
            background-color: {COLORS['error']};
            color: {COLORS['text_inverse']};
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            height: 36px;
            font-weight: 500;
        }}

        QPushButton#btn_danger:hover {{
            background-color: #DC2626;
        }}

        /* 表单样式 */
        QLabel#form_label {{
            font-size: 14px;
            font-weight: 500;
            color: {COLORS['text_primary']};
            margin-bottom: 6px;
        }}

        QLineEdit, QComboBox, QTextEdit {{
            padding: 8px 12px;
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
            font-size: 14px;
            background-color: {COLORS['surface']};
        }}

        QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{
            border: 2px solid {COLORS['primary']};
        }}

        QLineEdit::placeholder {{
            color: {COLORS['text_disabled']};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}

        QComboBox QAbstractItemView {{
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
            background-color: {COLORS['surface']};
            selection-background-color: {COLORS['primary_light']};
        }}

        /* 表格样式 */
        QTableWidget {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            gridline-color: {COLORS['divider']};
        }}

        QTableWidget::item {{
            padding: 12px;
            border-bottom: 1px solid {COLORS['divider']};
        }}

        QTableWidget::item:selected {{
            background-color: {COLORS['primary_light']};
            color: {COLORS['text_primary']};
        }}

        QHeaderView::section {{
            background-color: {COLORS['background']};
            color: {COLORS['text_secondary']};
            font-weight: 600;
            font-size: 12px;
            padding: 12px;
            border: none;
            border-bottom: 2px solid {COLORS['border']};
            text-transform: uppercase;
        }}

        /* 选项卡样式 */
        QTabWidget::pane {{
            border: 1px solid {COLORS['border']};
            border-radius: 0 8px 8px 8px;
            background-color: {COLORS['surface']};
        }}

        QTabBar::tab {{
            background-color: {COLORS['background']};
            color: {COLORS['text_secondary']};
            padding: 12px 20px;
            border: none;
            border-bottom: 2px solid transparent;
            font-weight: 500;
        }}

        QTabBar::tab:selected {{
            background-color: {COLORS['surface']};
            color: {COLORS['primary']};
            border-bottom: 2px solid {COLORS['primary']};
        }}

        QTabBar::tab:hover:!selected {{
            color: {COLORS['primary']};
            background-color: {COLORS['primary_light']};
        }}

        /* 进度条样式 */
        QProgressBar {{
            border: none;
            border-radius: 9999px;
            background-color: {COLORS['border']};
            height: 8px;
            text-align: center;
        }}

        QProgressBar::chunk {{
            background-color: {COLORS['primary']};
            border-radius: 9999px;
        }}

        /* 复选框和单选按钮 */
        QCheckBox, QRadioButton {{
            spacing: 8px;
        }}

        QCheckBox::indicator, QRadioButton::indicator {{
            width: 16px;
            height: 16px;
        }}

        QCheckBox::indicator:checked {{
            background-color: {COLORS['primary']};
            border-radius: 3px;
        }}

        /* 滚动条样式 */
        QScrollBar:vertical {{
            background-color: {COLORS['divider']};
            width: 8px;
            border-radius: 4px;
        }}

        QScrollBar::handle:vertical {{
            background-color: {COLORS['text_disabled']};
            border-radius: 4px;
            min-height: 30px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {COLORS['text_secondary']};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        """

    def create_sidebar(self) -> QWidget:
        """创建侧边栏"""
        sidebar = QWidget()
        sidebar.setObjectName('sidebar')
        sidebar.setFixedWidth(240)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(0)

        # 标题
        title = QLabel('样式演示')
        title.setObjectName('sidebar_title')
        layout.addWidget(title)

        # 导航按钮组
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        nav_items = [
            ('概览', 0),
            ('按钮样式', 1),
            ('表单控件', 2),
            ('数据表格', 3),
            ('选项卡', 4),
            ('进度指示', 5),
            ('颜色系统', 6),
        ]

        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setObjectName('nav_btn')
            btn.setCheckable(True)
            # 使用默认参数避免信号参数问题
            btn.clicked.connect(lambda checked=True, idx=index: self.show_page(idx))
            self.nav_group.addButton(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # 页脚
        footer = QLabel('UI/UX Pro Max\n现代化扁平设计')
        footer.setObjectName('sidebar_footer')
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

        return sidebar

    def create_content_area(self) -> QWidget:
        """创建内容区域"""
        content_area = QWidget()
        content_area.setObjectName('content_area')

        layout = QVBoxLayout(content_area)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 头部
        header = self.create_header()
        layout.addWidget(header)

        # 堆叠窗口
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # 创建各个页面
        self.stack.addWidget(self.create_overview_page())
        self.stack.addWidget(self.create_buttons_page())
        self.stack.addWidget(self.create_forms_page())
        self.stack.addWidget(self.create_tables_page())
        self.stack.addWidget(self.create_tabs_page())
        self.stack.addWidget(self.create_progress_page())
        self.stack.addWidget(self.create_colors_page())

        return content_area

    def create_header(self) -> QWidget:
        """创建头部"""
        header = QWidget()
        header.setObjectName('header')
        header.setFixedHeight(56)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)

        title = QLabel('PySide2 现代化扁平设计样式演示')
        title.setObjectName('header_title')
        layout.addWidget(title)

        layout.addStretch()

        # 帮助和关于按钮
        btn_help = QPushButton('帮助')
        btn_help.setObjectName('btn_secondary')
        layout.addWidget(btn_help)

        btn_about = QPushButton('关于')
        btn_about.setObjectName('btn_primary')
        layout.addWidget(btn_about)

        return header

    def show_page(self, index: int):
        """显示指定页面"""
        self.stack.setCurrentIndex(index)
        # 更新导航按钮状态
        for i, btn in enumerate(self.nav_group.buttons()):
            btn.setChecked(i == index)

    def create_page_header(self, title: str, subtitle: str) -> QVBoxLayout:
        """创建页面标题"""
        layout = QVBoxLayout()
        layout.setSpacing(0)

        lbl_title = QLabel(title)
        lbl_title.setObjectName('page_title')
        layout.addWidget(lbl_title)

        lbl_subtitle = QLabel(subtitle)
        lbl_subtitle.setObjectName('page_subtitle')
        layout.addWidget(lbl_subtitle)

        return layout

    def create_overview_page(self) -> QWidget:
        """创建概览页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)

        # 页面标题
        layout.addLayout(self.create_page_header(
            '设计系统概览',
            '现代化扁平设计系统 - 基于 UI/UX Pro Max 专业、清晰、现代的桌面应用界面设计'
        ))

        # 统计卡片
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        stats = [
            ('颜色变量', '12+', '主色/功能色/中性色'),
            ('组件样式', '20+', '按钮/表单/表格/导航'),
            ('字体层级', '8级', '从 11px 到 24px'),
            ('圆角规格', '5级', '从 0px 到 12px'),
        ]

        for title, value, subtitle in stats:
            card = self.create_stat_card(title, value, subtitle)
            stats_layout.addWidget(card)

        layout.addLayout(stats_layout)

        # 设计原则卡片
        card_principles = QGroupBox('设计原则')
        card_layout = QVBoxLayout(card_principles)

        principles = [
            '扁平化设计 - 无渐变、无纹理、纯色块',
            '现代圆角 - 6-8px 统一圆角系统',
            '层次阴影 - 极浅阴影 0 1px 3px rgba(0,0,0,0.1)',
            '微交互 - 150-300ms 平滑过渡动画',
            '无障碍 - WCAG AA 对比度、键盘导航支持',
        ]

        for principle in principles:
            lbl = QLabel(f'✅ {principle}')
            lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; margin: 6px 0;")
            card_layout.addWidget(lbl)

        layout.addWidget(card_principles)

        # 快速开始卡片
        card_start = QGroupBox('快速开始')
        card_layout = QVBoxLayout(card_start)

        code = QLabel('''from modern_flat_theme import get_complete_style, COLORS

# 应用完整样式
app.setStyleSheet(get_complete_style())

# 使用颜色变量
button.setStyleSheet(f"background-color: {COLORS['primary']};")''')
        code.setStyleSheet(f'''
            background-color: {COLORS['background']};
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
            padding: 16px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
            color: {COLORS['text_primary']};
        ''')
        card_layout.addWidget(code)

        layout.addWidget(card_start)
        layout.addStretch()

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        scroll.setFrameShape(QFrame.NoFrame)

        return scroll

    def create_stat_card(self, title: str, value: str, subtitle: str) -> QWidget:
        """创建统计卡片"""
        card = QWidget()
        card.setObjectName('stat_card')
        card.setFixedHeight(120)

        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)

        lbl_title = QLabel(title)
        lbl_title.setObjectName('stat_title')
        lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_title)

        lbl_value = QLabel(value)
        lbl_value.setObjectName('stat_value')
        lbl_value.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_value)

        lbl_subtitle = QLabel(subtitle)
        lbl_subtitle.setStyleSheet(f"color: {COLORS['text_disabled']}; font-size: 12px;")
        lbl_subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_subtitle)

        return card

    def create_buttons_page(self) -> QWidget:
        """创建按钮页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)

        layout.addLayout(self.create_page_header(
            '按钮样式',
            '多种按钮样式和尺寸，适应不同场景需求'
        ))

        # 主要按钮
        card = QGroupBox('主要按钮 (Primary)')
        card_layout = QHBoxLayout(card)
        btn1 = QPushButton('主要按钮')
        btn1.setObjectName('btn_primary')
        btn2 = QPushButton('悬停查看')
        btn2.setObjectName('btn_primary')
        card_layout.addWidget(btn1)
        card_layout.addWidget(btn2)
        card_layout.addStretch()
        layout.addWidget(card)

        # 次要按钮
        card = QGroupBox('次要按钮 (Secondary)')
        card_layout = QHBoxLayout(card)
        btn1 = QPushButton('次要按钮')
        btn1.setObjectName('btn_secondary')
        btn2 = QPushButton('悬停效果')
        btn2.setObjectName('btn_secondary')
        card_layout.addWidget(btn1)
        card_layout.addWidget(btn2)
        card_layout.addStretch()
        layout.addWidget(card)

        # 文字按钮
        card = QGroupBox('文字按钮 (Text)')
        card_layout = QHBoxLayout(card)
        btn1 = QPushButton('文字按钮')
        btn1.setObjectName('btn_text')
        btn2 = QPushButton('查看更多')
        btn2.setObjectName('btn_text')
        btn3 = QPushButton('取消操作')
        btn3.setObjectName('btn_text')
        card_layout.addWidget(btn1)
        card_layout.addWidget(btn2)
        card_layout.addWidget(btn3)
        card_layout.addStretch()
        layout.addWidget(card)

        # 危险按钮
        card = QGroupBox('危险按钮 (Danger)')
        card_layout = QHBoxLayout(card)
        btn1 = QPushButton('删除')
        btn1.setObjectName('btn_danger')
        btn2 = QPushButton('警告操作')
        btn2.setObjectName('btn_danger')
        card_layout.addWidget(btn1)
        card_layout.addWidget(btn2)
        card_layout.addStretch()
        layout.addWidget(card)

        # 按钮组合
        card = QGroupBox('按钮组合')
        card_layout = QHBoxLayout(card)
        btn1 = QPushButton('确认')
        btn1.setObjectName('btn_primary')
        btn2 = QPushButton('取消')
        btn2.setObjectName('btn_secondary')
        btn3 = QPushButton('更多操作')
        btn3.setObjectName('btn_text')
        card_layout.addWidget(btn1)
        card_layout.addWidget(btn2)
        card_layout.addWidget(btn3)
        card_layout.addStretch()
        layout.addWidget(card)

        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        scroll.setFrameShape(QFrame.NoFrame)

        return scroll

    def create_forms_page(self) -> QWidget:
        """创建表单页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)

        layout.addLayout(self.create_page_header(
            '表单控件',
            '文本输入、下拉选择、复选框、单选按钮等表单元素'
        ))

        # 文本输入
        card = QGroupBox('文本输入')
        card_layout = QVBoxLayout(card)

        # 单行文本
        lbl = QLabel('单行文本')
        lbl.setObjectName('form_label')
        card_layout.addWidget(lbl)
        edit = QLineEdit()
        edit.setPlaceholderText('请输入文本...')
        card_layout.addWidget(edit)

        # 密码输入
        lbl = QLabel('密码输入')
        lbl.setObjectName('form_label')
        card_layout.addWidget(lbl)
        edit = QLineEdit()
        edit.setEchoMode(QLineEdit.Password)
        edit.setPlaceholderText('请输入密码...')
        card_layout.addWidget(edit)

        # 多行文本
        lbl = QLabel('多行文本')
        lbl.setObjectName('form_label')
        card_layout.addWidget(lbl)
        text_edit = QTextEdit()
        text_edit.setPlaceholderText('请输入多行文本...')
        text_edit.setMaximumHeight(100)
        card_layout.addWidget(text_edit)

        layout.addWidget(card)

        # 下拉选择
        card = QGroupBox('下拉选择')
        card_layout = QVBoxLayout(card)

        lbl = QLabel('数据库类型')
        lbl.setObjectName('form_label')
        card_layout.addWidget(lbl)
        combo = QComboBox()
        combo.addItems(['请选择...', 'MySQL', 'PostgreSQL', 'SQLite', 'SQL Server'])
        card_layout.addWidget(combo)

        lbl = QLabel('端口号')
        lbl.setObjectName('form_label')
        card_layout.addWidget(lbl)
        edit = QLineEdit()
        edit.setText('3306')
        card_layout.addWidget(edit)

        layout.addWidget(card)

        # 选择控件
        card = QGroupBox('选择控件')
        card_layout = QHBoxLayout(card)

        # 复选框
        checkbox_layout = QVBoxLayout()
        lbl = QLabel('复选框')
        lbl.setObjectName('form_label')
        checkbox_layout.addWidget(lbl)
        checkbox_layout.addWidget(QCheckBox('选项 1（未选中）'))
        checkbox_layout.addWidget(QCheckBox('选项 2（已选中）'))
        chb = QCheckBox('选项 3（禁用）')
        chb.setEnabled(False)
        checkbox_layout.addWidget(chb)
        checkbox_layout.addStretch()
        card_layout.addLayout(checkbox_layout)

        # 单选按钮
        radio_layout = QVBoxLayout()
        lbl = QLabel('单选按钮')
        lbl.setObjectName('form_label')
        radio_layout.addWidget(lbl)
        radio_group = QButtonGroup(self)
        rb1 = QRadioButton('单选 A')
        rb2 = QRadioButton('单选 B')
        rb2.setChecked(True)
        rb3 = QRadioButton('单选 C（禁用）')
        rb3.setEnabled(False)
        radio_group.addButton(rb1)
        radio_group.addButton(rb2)
        radio_group.addButton(rb3)
        radio_layout.addWidget(rb1)
        radio_layout.addWidget(rb2)
        radio_layout.addWidget(rb3)
        radio_layout.addStretch()
        card_layout.addLayout(radio_layout)

        layout.addWidget(card)
        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        scroll.setFrameShape(QFrame.NoFrame)

        return scroll

    def create_tables_page(self) -> QWidget:
        """创建表格页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)

        layout.addLayout(self.create_page_header(
            '数据表格',
            '专业数据展示表格，支持状态标签和操作按钮'
        ))

        # 表格卡片
        card = QGroupBox('用户数据表')
        card_layout = QVBoxLayout(card)

        # 工具栏按钮
        toolbar = QHBoxLayout()
        btn_add = QPushButton('添加')
        btn_add.setObjectName('btn_primary')
        btn_export = QPushButton('导出')
        btn_export.setObjectName('btn_secondary')
        toolbar.addStretch()
        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_export)
        card_layout.addLayout(toolbar)

        # 表格
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(['ID', '用户名', '邮箱', '部门', '状态', '创建时间'])
        table.setRowCount(5)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)

        # 设置行高
        for row in range(table.rowCount()):
            table.setRowHeight(row, 44)

        # 填充数据
        data = [
            ('1', '张三', 'zhang@example.com', '技术部', '激活', '2024-01-15'),
            ('2', '李四', 'li@example.com', '产品部', '激活', '2024-01-14'),
            ('3', '王五', 'wang@example.com', '设计部', '暂停', '2024-01-10'),
            ('4', '赵六', 'zhao@example.com', '运营部', '激活', '2024-01-08'),
            ('5', '钱七', 'qian@example.com', '市场部', '禁用', '2024-01-05'),
        ]

        status_colors = {
            '激活': (COLORS['success'], '#D1FAE5'),
            '暂停': (COLORS['warning'], '#FEF3C7'),
            '禁用': (COLORS['error'], '#FEE2E2'),
        }

        for row, (id_, name, email, dept, status, date) in enumerate(data):
            table.setItem(row, 0, QTableWidgetItem(id_))
            table.setItem(row, 1, QTableWidgetItem(name))
            table.setItem(row, 2, QTableWidgetItem(email))
            table.setItem(row, 3, QTableWidgetItem(dept))

            status_item = QTableWidgetItem(f'  {status}')
            color, bg = status_colors.get(status, (COLORS['text_primary'], COLORS['surface']))
            status_item.setForeground(QColor(color))
            table.setItem(row, 4, status_item)

            table.setItem(row, 5, QTableWidgetItem(date))

        card_layout.addWidget(table)
        layout.addWidget(card)
        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        scroll.setFrameShape(QFrame.NoFrame)

        return scroll

    def create_tabs_page(self) -> QWidget:
        """创建选项卡页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)

        layout.addLayout(self.create_page_header(
            '选项卡',
            '组织内容到不同选项卡，节省空间且易于导航'
        ))

        # 选项卡组件
        tabs = QTabWidget()

        # 数据统计选项卡
        tab1 = QWidget()
        tab1_layout = QVBoxLayout(tab1)
        lbl = QLabel('数据统计内容')
        lbl.setStyleSheet('font-size: 16px; font-weight: 600; margin-bottom: 12px;')
        tab1_layout.addWidget(lbl)
        lbl2 = QLabel('这里是第一个选项卡的内容区域，可以放置数据统计图表、关键指标等内容。')
        lbl2.setStyleSheet(f'color: {COLORS["text_secondary"]};')
        tab1_layout.addWidget(lbl2)

        stats_widget = QWidget()
        stats_widget.setStyleSheet(f'''
            background-color: {COLORS['background']};
            border-radius: 6px;
            padding: 20px;
        ''')
        stats_layout = QHBoxLayout(stats_widget)
        stats = [
            ('总用户', '1,234', COLORS['primary']),
            ('活跃用户', '892', COLORS['success']),
            ('满意度', '98%', COLORS['warning']),
        ]
        for title, value, color in stats:
            stat_widget = QWidget()
            stat_layout = QVBoxLayout(stat_widget)
            lbl_value = QLabel(value)
            lbl_value.setStyleSheet(f'font-size: 24px; font-weight: 700; color: {color};')
            lbl_value.setAlignment(Qt.AlignCenter)
            lbl_title = QLabel(title)
            lbl_title.setStyleSheet(f'font-size: 12px; color: {COLORS["text_secondary"]};')
            lbl_title.setAlignment(Qt.AlignCenter)
            stat_layout.addWidget(lbl_value)
            stat_layout.addWidget(lbl_title)
            stats_layout.addWidget(stat_widget)
        tab1_layout.addWidget(stats_widget)
        tab1_layout.addStretch()

        tabs.addTab(tab1, '数据统计')

        # 设置选项卡
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        lbl = QLabel('设置内容')
        lbl.setStyleSheet('font-size: 16px; font-weight: 600; margin-bottom: 12px;')
        tab2_layout.addWidget(lbl)

        lbl_name = QLabel('系统名称')
        lbl_name.setObjectName('form_label')
        tab2_layout.addWidget(lbl_name)
        edit_name = QLineEdit()
        edit_name.setText('数据查询分析工具')
        tab2_layout.addWidget(edit_name)

        lbl_desc = QLabel('系统描述')
        lbl_desc.setObjectName('form_label')
        tab2_layout.addWidget(lbl_desc)
        edit_desc = QTextEdit()
        edit_desc.setText('基于 PySide2 的桌面数据查询分析应用程序')
        edit_desc.setMaximumHeight(80)
        tab2_layout.addWidget(edit_desc)
        tab2_layout.addStretch()

        tabs.addTab(tab2, '设置')

        # 列表选项卡
        tab3 = QWidget()
        tab3_layout = QVBoxLayout(tab3)
        lbl = QLabel('列表内容')
        lbl.setStyleSheet('font-size: 16px; font-weight: 600; margin-bottom: 12px;')
        tab3_layout.addWidget(lbl)

        list_widget = QListWidget()
        list_widget.addItems(['项目文件 1', '项目文件 2', '项目文件 3', '项目文件 4', '项目文件 5'])
        list_widget.setStyleSheet(f'''
            QListWidget {{
                background-color: {COLORS['background']};
                border-radius: 6px;
                border: none;
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {COLORS['divider']};
            }}
        ''')
        tab3_layout.addWidget(list_widget)

        tabs.addTab(tab3, '列表')

        # 关于选项卡
        tab4 = QWidget()
        tab4_layout = QVBoxLayout(tab4)
        lbl = QLabel('关于')
        lbl.setStyleSheet('font-size: 16px; font-weight: 600; margin-bottom: 12px;')
        tab4_layout.addWidget(lbl)

        about_widget = QWidget()
        about_widget.setStyleSheet(f'''
            background-color: {COLORS['background']};
            border-radius: 6px;
            padding: 20px;
        ''')
        about_layout = QVBoxLayout(about_widget)
        about_layout.addWidget(QLabel(f'<b>版本:</b> 1.0.0'))
        about_layout.addWidget(QLabel(f'<b>作者:</b> UI/UX Pro Max 设计系统'))
        about_layout.addWidget(QLabel(f'<b>技术:</b> PySide2 + 现代化扁平设计'))
        tab4_layout.addWidget(about_widget)
        tab4_layout.addStretch()

        tabs.addTab(tab4, '关于')

        layout.addWidget(tabs)
        layout.addStretch()

        return page

    def create_progress_page(self) -> QWidget:
        """创建进度页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)

        layout.addLayout(self.create_page_header(
            '进度指示',
            '进度条、状态标签等反馈组件'
        ))

        # 进度条卡片
        card = QGroupBox('进度条')
        card_layout = QVBoxLayout(card)

        for value in [25, 50, 75, 100]:
            lbl = QLabel(f'进度 {value}%')
            lbl.setStyleSheet(f'font-size: 12px; color: {COLORS["text_secondary"]}; margin-bottom: 6px;')
            card_layout.addWidget(lbl)

            progress = QProgressBar()
            progress.setValue(value)
            progress.setTextVisible(False)
            progress.setFixedHeight(8)
            card_layout.addWidget(progress)
            card_layout.addSpacing(16)

        layout.addWidget(card)

        # 状态标签卡片
        card = QGroupBox('状态标签')
        card_layout = QHBoxLayout(card)
        card_layout.setSpacing(12)

        statuses = [
            ('成功', COLORS['success'], '#D1FAE5'),
            ('警告', COLORS['warning'], '#FEF3C7'),
            ('错误', COLORS['error'], '#FEE2E2'),
            ('信息', COLORS['primary'], COLORS['primary_light']),
        ]

        for text, color, bg in statuses:
            lbl = QLabel(f'  {text}  ')
            lbl.setStyleSheet(f'''
                background-color: {bg};
                color: {color};
                border-radius: 9999px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: 500;
            ''')
            card_layout.addWidget(lbl)

        card_layout.addStretch()
        layout.addWidget(card)
        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        scroll.setFrameShape(QFrame.NoFrame)

        return scroll

    def create_colors_page(self) -> QWidget:
        """创建颜色系统页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)

        layout.addLayout(self.create_page_header(
            '颜色系统',
            '完整的颜色变量和使用指南'
        ))

        # 主色
        card = QGroupBox('主色')
        card_layout = QHBoxLayout(card)
        card_layout.setSpacing(12)

        colors = [
            ('主色', COLORS['primary'], COLORS['text_inverse']),
            ('悬停', COLORS['primary_hover'], COLORS['text_inverse']),
            ('浅色背景', COLORS['primary_light'], COLORS['primary']),
        ]

        for name, bg, text in colors:
            color_card = self.create_color_card(name, bg, text)
            card_layout.addWidget(color_card)

        card_layout.addStretch()
        layout.addWidget(card)

        # 功能色
        card = QGroupBox('功能色')
        card_layout = QHBoxLayout(card)
        card_layout.setSpacing(12)

        colors = [
            ('成功', COLORS['success'], COLORS['text_inverse']),
            ('警告', COLORS['warning'], COLORS['text_inverse']),
            ('错误', COLORS['error'], COLORS['text_inverse']),
            ('信息', COLORS['info'], COLORS['text_inverse']),
        ]

        for name, bg, text in colors:
            color_card = self.create_color_card(name, bg, text)
            card_layout.addWidget(color_card)

        card_layout.addStretch()
        layout.addWidget(card)

        # 中性色
        card = QGroupBox('中性色')
        card_layout = QHBoxLayout(card)
        card_layout.setSpacing(12)

        colors = [
            ('页面背景', COLORS['background'], COLORS['text_primary']),
            ('卡片表面', COLORS['surface'], COLORS['text_primary']),
            ('边框', COLORS['border'], COLORS['text_primary']),
            ('分隔线', COLORS['divider'], COLORS['text_primary']),
        ]

        for name, bg, text in colors:
            color_card = self.create_color_card(name, bg, text)
            card_layout.addWidget(color_card)

        card_layout.addStretch()
        layout.addWidget(card)

        # 文字色
        card = QGroupBox('文字色')
        card_layout = QHBoxLayout(card)
        card_layout.setSpacing(12)

        colors = [
            ('主要文字', COLORS['text_primary'], COLORS['text_inverse']),
            ('次要文字', COLORS['text_secondary'], COLORS['text_inverse']),
            ('禁用文字', COLORS['text_disabled'], COLORS['text_inverse']),
        ]

        for name, bg, text in colors:
            color_card = self.create_color_card(name, bg, text)
            card_layout.addWidget(color_card)

        card_layout.addStretch()
        layout.addWidget(card)

        # 使用指南
        card = QGroupBox('使用指南')
        card_layout = QVBoxLayout(card)

        guides = [
            ('主色 (Primary)', '用于主要操作按钮、链接、选中状态'),
            ('功能色', '用于状态指示：成功(绿)、警告(琥珀)、错误(红)、信息(蓝)'),
            ('中性色', '用于背景、边框、分隔线等界面元素'),
            ('文字色', '用于文本：主要文字(深色)、次要文字(中灰)、禁用(浅灰)'),
        ]

        for title, desc in guides:
            lbl = QLabel(f'<b style="color: {COLORS["text_primary"]}">{title}</b> - {desc}')
            lbl.setStyleSheet(f'color: {COLORS["text_secondary"]}; margin: 6px 0;')
            card_layout.addWidget(lbl)

        # 无障碍标准提示
        tip = QWidget()
        tip.setStyleSheet(f'''
            background-color: {COLORS['primary_light']};
            border-radius: 6px;
            padding: 16px;
        ''')
        tip_layout = QVBoxLayout(tip)
        tip_title = QLabel('无障碍标准：')
        tip_title.setStyleSheet(f'color: {COLORS["primary"]}; font-weight: 600;')
        tip_layout.addWidget(tip_title)

        standards = [
            '正文文字对比度 ≥ 4.5:1 (WCAG AA)',
            '大文字对比度 ≥ 3:1',
            '禁用状态仍可辨识',
        ]
        for std in standards:
            lbl = QLabel(f'  • {std}')
            lbl.setStyleSheet(f'color: {COLORS["primary"]};')
            tip_layout.addWidget(lbl)

        card_layout.addWidget(tip)
        layout.addWidget(card)
        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        scroll.setFrameShape(QFrame.NoFrame)

        return scroll

    def create_color_card(self, name: str, bg: str, text: str) -> QWidget:
        """创建颜色卡片"""
        card = QWidget()
        card.setFixedSize(140, 80)
        card.setStyleSheet(f'''
            background-color: {bg};
            border: 2px solid {COLORS['border']};
            border-radius: 6px;
        ''')

        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)

        lbl_name = QLabel(name)
        lbl_name.setStyleSheet(f'color: {text}; font-weight: 600; font-size: 12px;')
        lbl_name.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_name)

        lbl_value = QLabel(bg)
        lbl_value.setStyleSheet(f'color: {text}; font-size: 11px; opacity: 0.8;')
        lbl_value.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_value)

        return card


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用全局字体
    font = QFont('Microsoft YaHei', 10)
    app.setFont(font)

    window = StyleDemoWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
