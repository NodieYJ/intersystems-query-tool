#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
现代化扁平设计样式演示程序 v3
完全按照 style_preview.html 的分辨率和元素比例设计
UI/UX Pro Max 设计系统实现
"""

import sys
from datetime import datetime

from PySide2.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QCheckBox,
    QRadioButton, QGroupBox, QTableWidget, QTableWidgetItem, QTabWidget,
    QProgressBar, QFrame, QScrollArea, QStackedWidget, QListWidget,
    QButtonGroup, QHeaderView, QSizePolicy
)
from PySide2.QtCore import Qt, QSize
from PySide2.QtGui import QColor, QFont, QScreen


# 全局缩放比例 - 根据屏幕分辨率动态计算
SCALE_FACTOR = 1.0


def calculate_scale_factor(app: QApplication) -> float:
    """
    根据屏幕分辨率计算缩放比例
    - ≤1920x1080 (1K及以下): 100% (1.0)
    - ~2560x1440 (2K): 150% (1.5)
    - ≥3200x1800 (3K及以上): 200% (2.0)
    """
    screen = app.primaryScreen()
    if screen is None:
        return 1.0
    
    geometry = screen.geometry()
    width = geometry.width()
    height = geometry.height()
    
    # 计算像素总数（百万像素）
    mega_pixels = (width * height) / 1000000
    
    # 根据分辨率判断缩放比例
    if width >= 3200 or height >= 1800:
        # 3K 及以上分辨率 (≥3200x1800)
        return 2.0
    elif width >= 2560 or height >= 1440:
        # 2K 分辨率 (~2560x1440)
        return 1.5
    else:
        # 1K 及以下分辨率 (≤1920x1080)
        return 1.0


def scaled(value: int) -> int:
    """根据缩放比例计算实际像素值"""
    return int(value * SCALE_FACTOR)


# 颜色系统 - 完全匹配 HTML
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


class StyleDemoWindow(QMainWindow):
    """样式演示主窗口 - 完全匹配 HTML 版本，支持动态缩放"""

    def __init__(self):
        super().__init__()
        
        # 基础尺寸（基于 1280x800 设计）
        base_width = 1280
        base_height = 800
        
        # 应用缩放后的尺寸
        self.setGeometry(100, 100, scaled(base_width), scaled(base_height))
        self.setMinimumSize(scaled(1024), scaled(600))
        
        # 设置窗口标题，包含缩放信息
        scale_text = f"{SCALE_FACTOR * 100:.0f}%"
        if SCALE_FACTOR == 1.0:
            res_text = "1K (≤1920x1080)"
        elif SCALE_FACTOR == 1.5:
            res_text = "2K (~2560x1440)"
        else:
            res_text = "3K+ (≥3200x1800)"
        self.setWindowTitle(f'🎨 现代化扁平设计样式演示 - {res_text} @ {scale_text}')

        # 创建主部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # 主布局 - 无间距无外边距
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建左侧边栏 - 固定 240px
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)

        # 创建内容区域
        content = self.create_content_area()
        main_layout.addWidget(content, 1)

        # 应用全局样式
        self.apply_styles()

        # 默认显示第一页
        self.show_page(0)

    def apply_styles(self):
        """应用全局样式 - 完全匹配 HTML CSS"""
        self.setStyleSheet(f"""
            /* 全局基础 */
            QWidget {{
                font-family: 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif;
                font-size: 14px;
                color: {COLORS['text_primary']};
            }}

            /* 侧边栏 */
            #sidebar {{
                background-color: {COLORS['surface']};
                border-right: 1px solid {COLORS['border']};
            }}

            #sidebar_title {{
                font-size: 18px;
                font-weight: 600;
                color: {COLORS['primary']};
                padding: 0 0 10px 0;
                border-bottom: 1px solid {COLORS['divider']};
                margin-bottom: 16px;
            }}

            #sidebar_footer {{
                color: {COLORS['text_secondary']};
                font-size: 11px;
            }}

            /* 导航按钮 */
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

            /* 内容区域 */
            #content_area {{
                background-color: {COLORS['background']};
            }}

            /* 头部 */
            #header {{
                background-color: {COLORS['surface']};
                border-bottom: 1px solid {COLORS['border']};
            }}

            #header_title {{
                font-size: 20px;
                font-weight: 600;
                color: {COLORS['text_primary']};
            }}

            /* 页面标题 */
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

            /* 卡片 (GroupBox) */
            QGroupBox {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 20px;
                margin-top: 20px;
                font-size: 16px;
                font-weight: 600;
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 0;
                top: 0;
                padding: 0 0 12px 0;
                color: {COLORS['text_primary']};
                border-bottom: 1px solid {COLORS['divider']};
            }}

            /* 统计卡片 */
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
                letter-spacing: 0.5px;
            }}

            #stat_value {{
                color: {COLORS['primary']};
                font-size: 32px;
                font-weight: 700;
            }}

            #stat_subtitle {{
                color: {COLORS['text_disabled']};
                font-size: 12px;
            }}

            /* 主要按钮 */
            QPushButton#btn_primary {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_inverse']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
                min-height: 36px;
            }}

            QPushButton#btn_primary:hover {{
                background-color: {COLORS['primary_hover']};
            }}

            /* 次要按钮 */
            QPushButton#btn_secondary {{
                background-color: {COLORS['surface']};
                color: {COLORS['primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
                min-height: 36px;
            }}

            QPushButton#btn_secondary:hover {{
                background-color: {COLORS['primary_light']};
                border-color: {COLORS['primary']};
            }}

            /* 文字按钮 */
            QPushButton#btn_text {{
                background-color: transparent;
                color: {COLORS['primary']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
                min-height: 36px;
            }}

            QPushButton#btn_text:hover {{
                background-color: {COLORS['primary_light']};
            }}

            /* 危险按钮 */
            QPushButton#btn_danger {{
                background-color: {COLORS['error']};
                color: {COLORS['text_inverse']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
                min-height: 36px;
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
                min-height: 36px;
            }}

            QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{
                border: 2px solid {COLORS['primary']};
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

            /* 进度条 */
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

            /* 颜色卡片 */
            #color_card {{
                border: 2px solid {COLORS['border']};
                border-radius: 6px;
            }}

            #color_name {{
                font-weight: 600;
                font-size: 12px;
            }}

            #color_value {{
                font-size: 11px;
                opacity: 0.8;
            }}

            /* 状态标签 */
            #status_success, #status_warning, #status_error {{
                padding: 4px 12px;
                border-radius: 9999px;
                font-size: 12px;
                font-weight: 500;
            }}

            #status_success {{
                background-color: #D1FAE5;
                color: {COLORS['success']};
            }}

            #status_warning {{
                background-color: #FEF3C7;
                color: {COLORS['warning']};
            }}

            #status_error {{
                background-color: #FEE2E2;
                color: {COLORS['error']};
            }}

            /* 代码块 */
            #code_block {{
                background-color: {COLORS['background']};
                border-radius: 6px;
                padding: 16px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 13px;
            }}

            /* 滚动条 */
            QScrollBar:vertical {{
                background-color: {COLORS['background']};
                width: 8px;
                border-radius: 4px;
            }}

            QScrollBar::handle:vertical {{
                background-color: {COLORS['border']};
                border-radius: 4px;
                min-height: 30px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: {COLORS['text_disabled']};
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

    def create_sidebar(self) -> QWidget:
        """创建侧边栏 - 240px 宽度（自动缩放）"""
        sidebar = QWidget()
        sidebar.setObjectName('sidebar')
        sidebar.setFixedWidth(scaled(240))

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(0)

        # 标题
        title = QLabel('🎨 样式演示')
        title.setObjectName('sidebar_title')
        layout.addWidget(title)

        # 导航按钮组
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        nav_items = [
            '📊 概览',
            '🔘 按钮样式',
            '📝 表单控件',
            '📋 数据表格',
            '🗂️ 选项卡',
            '📊 进度指示',
            '🎨 颜色系统',
        ]

        for index, text in enumerate(nav_items):
            btn = QPushButton(text)
            btn.setObjectName('nav_btn')
            btn.setCheckable(True)
            # 修复 lambda 参数问题
            btn.clicked.connect(lambda checked=False, idx=index: self.show_page(idx))
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
        content = QWidget()
        content.setObjectName('content_area')

        layout = QVBoxLayout(content)
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

        return content

    def create_header(self) -> QWidget:
        """创建头部"""
        header = QWidget()
        header.setObjectName('header')
        header.setFixedHeight(56)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)

        title = QLabel('🎨 现代化扁平设计样式演示')
        title.setObjectName('header_title')
        layout.addWidget(title)

        layout.addStretch()

        btn_help = QPushButton('帮助')
        btn_help.setObjectName('btn_secondary')
        layout.addWidget(btn_help)

        btn_about = QPushButton('关于')
        btn_about.setObjectName('btn_primary')
        layout.addWidget(btn_about)

        return header

    def show_page(self, index: int):
        """切换页面"""
        self.stack.setCurrentIndex(index)
        # 更新导航状态
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

    # ==================== 各个页面 ====================

    def create_overview_page(self) -> QWidget:
        """概览页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)

        layout.addLayout(self.create_page_header(
            '📊 设计系统概览',
            '现代化扁平设计系统 - 基于 UI/UX Pro Max • 专业、清晰、现代的桌面应用界面设计'
        ))

        # 统计卡片 - 4列网格
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
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

        layout.addWidget(stats_widget)

        # 设计原则
        card = QGroupBox('🎯 设计原则')
        card_layout = QVBoxLayout(card)

        principles = [
            '✅ 扁平化设计 - 无渐变、无纹理、纯色块',
            '✅ 现代圆角 - 6-8px 统一圆角系统',
            '✅ 层次阴影 - 极浅阴影 0 1px 3px rgba(0,0,0,0.1)',
            '✅ 微交互 - 150-300ms 平滑过渡动画',
            '✅ 无障碍 - WCAG AA 对比度、键盘导航支持',
        ]

        for text in principles:
            lbl = QLabel(text)
            lbl.setStyleSheet(f'color: {COLORS["text_primary"]}; padding: 6px 0;')
            card_layout.addWidget(lbl)

        layout.addWidget(card)

        # 快速开始
        card = QGroupBox('🚀 快速开始')
        card_layout = QVBoxLayout(card)

        code = QLabel("""from modern_flat_theme import get_complete_style, COLORS

# 应用完整样式
app.setStyleSheet(get_complete_style())

# 使用颜色变量
button.setStyleSheet(f"background-color: {COLORS['primary']};")""")
        code.setObjectName('code_block')
        card_layout.addWidget(code)

        layout.addWidget(card)
        layout.addStretch()

        # 包装在滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        scroll.setFrameShape(QFrame.NoFrame)

        return scroll

    def create_stat_card(self, title: str, value: str, subtitle: str) -> QWidget:
        """创建统计卡片"""
        card = QWidget()
        card.setObjectName('stat_card')
        card.setMinimumWidth(200)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)

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

    def create_buttons_page(self) -> QWidget:
        """按钮页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)

        layout.addLayout(self.create_page_header(
            '🔘 按钮样式',
            '多种按钮样式和尺寸，适应不同场景需求'
        ))

        # 主要按钮
        card = QGroupBox('主要按钮 (Primary)')
        card_layout = QHBoxLayout(card)
        card_layout.addWidget(self.create_btn('主要按钮', 'btn_primary'))
        card_layout.addWidget(self.create_btn('悬停状态', 'btn_primary'))
        btn_disabled = self.create_btn('禁用状态', 'btn_primary')
        btn_disabled.setEnabled(False)
        card_layout.addWidget(btn_disabled)
        card_layout.addStretch()
        layout.addWidget(card)

        # 次要按钮
        card = QGroupBox('次要按钮 (Secondary)')
        card_layout = QHBoxLayout(card)
        card_layout.addWidget(self.create_btn('次要按钮', 'btn_secondary'))
        card_layout.addWidget(self.create_btn('悬停查看效果', 'btn_secondary'))
        card_layout.addStretch()
        layout.addWidget(card)

        # 文字按钮
        card = QGroupBox('文字按钮 (Text)')
        card_layout = QHBoxLayout(card)
        card_layout.addWidget(self.create_btn('文字按钮', 'btn_text'))
        card_layout.addWidget(self.create_btn('查看更多', 'btn_text'))
        card_layout.addStretch()
        layout.addWidget(card)

        # 危险按钮
        card = QGroupBox('危险按钮 (Danger)')
        card_layout = QHBoxLayout(card)
        card_layout.addWidget(self.create_btn('🗑️ 删除', 'btn_danger'))
        card_layout.addWidget(self.create_btn('⚠️ 警告操作', 'btn_danger'))
        card_layout.addStretch()
        layout.addWidget(card)

        # 按钮组合
        card = QGroupBox('按钮组合')
        card_layout = QHBoxLayout(card)
        card_layout.addWidget(self.create_btn('✓ 确认', 'btn_primary'))
        card_layout.addWidget(self.create_btn('✕ 取消', 'btn_secondary'))
        card_layout.addWidget(self.create_btn('⋮ 更多操作', 'btn_text'))
        card_layout.addStretch()
        layout.addWidget(card)

        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        scroll.setFrameShape(QFrame.NoFrame)

        return scroll

    def create_btn(self, text: str, style: str) -> QPushButton:
        """创建按钮"""
        btn = QPushButton(text)
        btn.setObjectName(style)
        return btn

    def create_forms_page(self) -> QWidget:
        """表单页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)

        layout.addLayout(self.create_page_header(
            '📝 表单控件',
            '文本输入、下拉选择、复选框、单选按钮等表单元素'
        ))

        # 使用分割器
        splitter_widget = QWidget()
        splitter_layout = QHBoxLayout(splitter_widget)
        splitter_layout.setSpacing(24)

        # 左侧
        left = QWidget()
        left_layout = QVBoxLayout(left)

        # 文本输入卡片
        card = QGroupBox('文本输入')
        card_layout = QVBoxLayout(card)

        lbl = QLabel('单行文本')
        lbl.setObjectName('form_label')
        card_layout.addWidget(lbl)
        edit = QLineEdit()
        edit.setPlaceholderText('请输入文本...')
        card_layout.addWidget(edit)

        lbl = QLabel('密码输入')
        lbl.setObjectName('form_label')
        card_layout.addWidget(lbl)
        edit = QLineEdit()
        edit.setEchoMode(QLineEdit.Password)
        edit.setPlaceholderText('请输入密码...')
        card_layout.addWidget(edit)

        lbl = QLabel('多行文本')
        lbl.setObjectName('form_label')
        card_layout.addWidget(lbl)
        text = QTextEdit()
        text.setPlaceholderText('请输入多行文本...')
        text.setMaximumHeight(100)
        card_layout.addWidget(text)

        left_layout.addWidget(card)

        # 下拉选择
        card = QGroupBox('下拉选择')
        card_layout = QVBoxLayout(card)

        lbl = QLabel('数据库类型')
        lbl.setObjectName('form_label')
        card_layout.addWidget(lbl)
        combo = QComboBox()
        combo.addItems(['请选择...', 'MySQL', 'PostgreSQL', 'SQLite', 'SQL Server'])
        card_layout.addWidget(combo)

        left_layout.addWidget(card)
        left_layout.addStretch()

        splitter_layout.addWidget(left, 1)

        # 右侧
        right = QWidget()
        right_layout = QVBoxLayout(right)

        # 选择控件
        card = QGroupBox('选择控件')
        card_layout = QVBoxLayout(card)

        card_layout.addWidget(QLabel('<b>复选框</b>'))
        card_layout.addWidget(QCheckBox('选项 1（未选中）'))
        cb2 = QCheckBox('选项 2（已选中）')
        cb2.setChecked(True)
        card_layout.addWidget(cb2)
        cb3 = QCheckBox('选项 3（禁用）')
        cb3.setEnabled(False)
        card_layout.addWidget(cb3)

        card_layout.addSpacing(16)

        card_layout.addWidget(QLabel('<b>单选按钮</b>'))
        rb1 = QRadioButton('单选 A')
        rb2 = QRadioButton('单选 B')
        rb2.setChecked(True)
        rb3 = QRadioButton('单选 C（禁用）')
        rb3.setEnabled(False)
        card_layout.addWidget(rb1)
        card_layout.addWidget(rb2)
        card_layout.addWidget(rb3)

        right_layout.addWidget(card)
        right_layout.addStretch()

        splitter_layout.addWidget(right, 1)

        layout.addWidget(splitter_widget)
        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        scroll.setFrameShape(QFrame.NoFrame)

        return scroll

    def create_tables_page(self) -> QWidget:
        """表格页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)

        layout.addLayout(self.create_page_header(
            '📋 数据表格',
            '专业数据展示表格，支持状态标签和操作按钮'
        ))

        # 表格卡片
        card = QGroupBox('用户数据表')
        card_layout = QVBoxLayout(card)

        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.addStretch()
        toolbar.addWidget(self.create_btn('➕ 添加', 'btn_primary'))
        toolbar.addWidget(self.create_btn('📥 导出', 'btn_secondary'))
        card_layout.addLayout(toolbar)

        # 表格
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(['ID', '用户名', '邮箱', '部门', '状态', '创建时间'])
        table.setRowCount(5)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)

        # 设置行高 44px
        for row in range(table.rowCount()):
            table.setRowHeight(row, 44)

        # 数据
        data = [
            ('1', '张三', 'zhang@example.com', '技术部', '激活', '2024-01-15'),
            ('2', '李四', 'li@example.com', '产品部', '激活', '2024-01-14'),
            ('3', '王五', 'wang@example.com', '设计部', '暂停', '2024-01-10'),
            ('4', '赵六', 'zhao@example.com', '运营部', '激活', '2024-01-08'),
            ('5', '钱七', 'qian@example.com', '市场部', '禁用', '2024-01-05'),
        ]

        for row, (id_, name, email, dept, status, date) in enumerate(data):
            table.setItem(row, 0, QTableWidgetItem(id_))
            table.setItem(row, 1, QTableWidgetItem(name))
            table.setItem(row, 2, QTableWidgetItem(email))
            table.setItem(row, 3, QTableWidgetItem(dept))

            status_item = QTableWidgetItem(f'  {status}')
            if status == '激活':
                status_item.setForeground(QColor(COLORS['success']))
            elif status == '暂停':
                status_item.setForeground(QColor(COLORS['warning']))
            else:
                status_item.setForeground(QColor(COLORS['error']))
            table.setItem(row, 4, status_item)

            table.setItem(row, 5, QTableWidgetItem(date))

        card_layout.addWidget(table)
        layout.addWidget(card)
        layout.addStretch()

        return page

    def create_tabs_page(self) -> QWidget:
        """选项卡页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)

        layout.addLayout(self.create_page_header(
            '🗂️ 选项卡',
            '组织内容到不同选项卡，节省空间且易于导航'
        ))

        tabs = QTabWidget()

        # 数据统计
        tab1 = QWidget()
        tab1_layout = QVBoxLayout(tab1)
        tab1_layout.addWidget(QLabel('<h3>数据统计内容</h3>'))
        tab1_layout.addWidget(QLabel('这里是第一个选项卡的内容区域，可以放置数据统计图表、关键指标等内容。'))

        stats_widget = QWidget()
        stats_widget.setStyleSheet(f'background: {COLORS["background"]}; border-radius: 6px; padding: 20px;')
        stats_layout = QHBoxLayout(stats_widget)
        for value, label in [('1,234', '总用户'), ('892', '活跃用户'), ('98%', '满意度')]:
            v_layout = QVBoxLayout()
            lbl_value = QLabel(value)
            lbl_value.setStyleSheet(f'font-size: 24px; font-weight: 700; color: {COLORS["primary"]};')
            lbl_value.setAlignment(Qt.AlignCenter)
            lbl_label = QLabel(label)
            lbl_label.setStyleSheet(f'font-size: 12px; color: {COLORS["text_secondary"]};')
            lbl_label.setAlignment(Qt.AlignCenter)
            v_layout.addWidget(lbl_value)
            v_layout.addWidget(lbl_label)
            stats_layout.addLayout(v_layout)
        tab1_layout.addWidget(stats_widget)
        tab1_layout.addStretch()
        tabs.addTab(tab1, '📊 数据统计')

        # 设置
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        tab2_layout.addWidget(QLabel('<h3>设置内容</h3>'))
        lbl = QLabel('系统名称')
        lbl.setObjectName('form_label')
        tab2_layout.addWidget(lbl)
        edit = QLineEdit('数据查询分析工具')
        tab2_layout.addWidget(edit)
        lbl = QLabel('系统描述')
        lbl.setObjectName('form_label')
        tab2_layout.addWidget(lbl)
        text = QTextEdit('基于 PySide2 的桌面数据查询分析应用程序')
        text.setMaximumHeight(80)
        tab2_layout.addWidget(text)
        tab2_layout.addStretch()
        tabs.addTab(tab2, '⚙️ 设置')

        # 列表
        tab3 = QWidget()
        tab3_layout = QVBoxLayout(tab3)
        tab3_layout.addWidget(QLabel('<h3>列表内容</h3>'))
        list_widget = QListWidget()
        list_widget.addItems(['项目文件 1', '项目文件 2', '项目文件 3', '项目文件 4', '项目文件 5'])
        tab3_layout.addWidget(list_widget)
        tabs.addTab(tab3, '📋 列表')

        # 关于
        tab4 = QWidget()
        tab4_layout = QVBoxLayout(tab4)
        tab4_layout.addWidget(QLabel('<h3>关于</h3>'))
        about = QWidget()
        about.setStyleSheet(f'background: {COLORS["background"]}; border-radius: 6px; padding: 20px;')
        about_layout = QVBoxLayout(about)
        about_layout.addWidget(QLabel('<b>版本:</b> 1.0.0'))
        about_layout.addWidget(QLabel('<b>作者:</b> UI/UX Pro Max 设计系统'))
        about_layout.addWidget(QLabel('<b>技术:</b> PySide2 + 现代化扁平设计'))
        tab4_layout.addWidget(about)
        tab4_layout.addStretch()
        tabs.addTab(tab4, 'ℹ️ 关于')

        layout.addWidget(tabs)
        layout.addStretch()

        return page

    def create_progress_page(self) -> QWidget:
        """进度页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)

        layout.addLayout(self.create_page_header(
            '📊 进度指示',
            '进度条、状态标签等反馈组件'
        ))

        # 进度条
        card = QGroupBox('进度条')
        card_layout = QVBoxLayout(card)

        for value in [25, 50, 75, 100]:
            lbl = QLabel(f'进度 {value}%')
            lbl.setStyleSheet(f'color: {COLORS["text_secondary"]}; font-size: 12px; margin-bottom: 6px;')
            card_layout.addWidget(lbl)
            progress = QProgressBar()
            progress.setValue(value)
            progress.setFormat(f'{value}%')
            card_layout.addWidget(progress)
            card_layout.addSpacing(10)

        layout.addWidget(card)

        # 状态标签
        card = QGroupBox('状态标签')
        card_layout = QHBoxLayout(card)

        lbl_success = QLabel('✅ 成功')
        lbl_success.setObjectName('status_success')
        card_layout.addWidget(lbl_success)

        lbl_warning = QLabel('⚠️ 警告')
        lbl_warning.setObjectName('status_warning')
        card_layout.addWidget(lbl_warning)

        lbl_error = QLabel('❌ 错误')
        lbl_error.setObjectName('status_error')
        card_layout.addWidget(lbl_error)

        card_layout.addStretch()
        layout.addWidget(card)
        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        scroll.setFrameShape(QFrame.NoFrame)

        return scroll

    def create_colors_page(self) -> QWidget:
        """颜色页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)

        layout.addLayout(self.create_page_header(
            '🎨 颜色系统',
            '完整的颜色变量和使用指南'
        ))

        # 主色
        card = QGroupBox('主色')
        card_layout = QHBoxLayout(card)
        card_layout.setSpacing(12)

        for name, bg, text in [
            ('主色', COLORS['primary'], COLORS['text_inverse']),
            ('悬停', COLORS['primary_hover'], COLORS['text_inverse']),
            ('浅色背景', COLORS['primary_light'], COLORS['primary']),
        ]:
            card_layout.addWidget(self.create_color_card(name, bg, text))

        card_layout.addStretch()
        layout.addWidget(card)

        # 功能色
        card = QGroupBox('功能色')
        card_layout = QHBoxLayout(card)
        card_layout.setSpacing(12)

        for name, bg, text in [
            ('成功', COLORS['success'], COLORS['text_inverse']),
            ('警告', COLORS['warning'], COLORS['text_inverse']),
            ('错误', COLORS['error'], COLORS['text_inverse']),
            ('信息', COLORS['info'], COLORS['text_inverse']),
        ]:
            card_layout.addWidget(self.create_color_card(name, bg, text))

        card_layout.addStretch()
        layout.addWidget(card)

        # 中性色
        card = QGroupBox('中性色')
        card_layout = QHBoxLayout(card)
        card_layout.setSpacing(12)

        for name, bg, text in [
            ('页面背景', COLORS['background'], COLORS['text_primary']),
            ('卡片表面', COLORS['surface'], COLORS['text_primary']),
            ('边框', COLORS['border'], COLORS['text_primary']),
            ('分隔线', COLORS['divider'], COLORS['text_primary']),
        ]:
            card_layout.addWidget(self.create_color_card(name, bg, text))

        card_layout.addStretch()
        layout.addWidget(card)

        # 文字色
        card = QGroupBox('文字色')
        card_layout = QHBoxLayout(card)
        card_layout.setSpacing(12)

        for name, bg, text in [
            ('主要文字', COLORS['text_primary'], COLORS['text_inverse']),
            ('次要文字', COLORS['text_secondary'], COLORS['text_inverse']),
            ('禁用文字', COLORS['text_disabled'], COLORS['text_inverse']),
        ]:
            card_layout.addWidget(self.create_color_card(name, bg, text))

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
            lbl = QLabel(f'<b>{title}</b> - {desc}')
            lbl.setStyleSheet(f'color: {COLORS["text_secondary"]}; margin: 6px 0;')
            card_layout.addWidget(lbl)

        # 无障碍提示
        tip = QWidget()
        tip.setStyleSheet(f'background-color: {COLORS["primary_light"]}; border-radius: 6px; padding: 16px;')
        tip_layout = QVBoxLayout(tip)
        lbl = QLabel('<b>无障碍标准：</b>')
        lbl.setStyleSheet(f'color: {COLORS["primary"]};')
        tip_layout.addWidget(lbl)
        for std in ['正文文字对比度 ≥ 4.5:1 (WCAG AA)', '大文字对比度 ≥ 3:1', '禁用状态仍可辨识']:
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
        card.setObjectName('color_card')
        card.setFixedSize(140, 80)
        card.setStyleSheet(f'background-color: {bg};')

        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)

        lbl_name = QLabel(name)
        lbl_name.setObjectName('color_name')
        lbl_name.setStyleSheet(f'color: {text};')
        lbl_name.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_name)

        lbl_value = QLabel(bg)
        lbl_value.setObjectName('color_value')
        lbl_value.setStyleSheet(f'color: {text};')
        lbl_value.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_value)

        return card


def main():
    """主函数"""
    # 启用 Qt 自动高 DPI 缩放
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    
    # 计算并设置缩放比例
    global SCALE_FACTOR
    SCALE_FACTOR = calculate_scale_factor(app)
    
    # 设置全局字体，根据缩放比例调整基础字号
    base_font_size = 10
    font = QFont('Microsoft YaHei', int(base_font_size * SCALE_FACTOR))
    app.setFont(font)
    
    # 输出缩放信息
    screen = app.primaryScreen()
    if screen:
        geometry = screen.geometry()
        print(f"屏幕分辨率: {geometry.width()}x{geometry.height()}")
        print(f"缩放比例: {SCALE_FACTOR * 100:.0f}%")
        
        if SCALE_FACTOR == 1.0:
            print("(1K及以下分辨率，100%缩放)")
        elif SCALE_FACTOR == 1.5:
            print("(2K分辨率，150%缩放)")
        elif SCALE_FACTOR >= 2.0:
            print("(3K及以上分辨率，200%缩放)")
    
    window = StyleDemoWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
