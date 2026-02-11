#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
现代化扁平设计 UI 样式配置
基于 UI/UX Pro Max 设计系统生成
风格：Flat Design + Soft UI Evolution
适用：PySide2 数据查询分析工具
"""

# ============================================================================
# 🎨 设计系统变量
# ============================================================================

# 主色调 - 专业蓝色系（数据、分析、技术感）
COLORS = {
    # 主色
    "primary": "#2563EB",          # 明亮蓝 - 主要操作、按钮
    "primary_hover": "#1D4ED8",    # 深蓝 - 悬停状态
    "primary_light": "#DBEAFE",    # 浅蓝 - 背景、选中状态
    
    # 次色
    "secondary": "#3B82F6",        # 中蓝 - 次级按钮、链接
    "secondary_light": "#EFF6FF",  # 淡蓝 - 卡片背景
    
    # 强调色
    "accent": "#F59E0B",           # 琥珀 - CTA、高亮、警告
    "accent_hover": "#D97706",     # 深琥珀 - 悬停
    "success": "#10B981",          # 翠绿 - 成功状态
    "error": "#EF4444",            # 红色 - 错误状态
    "warning": "#F59E0B",          # 琥珀 - 警告状态
    "info": "#3B82F6",             # 蓝色 - 信息提示
    
    # 中性色
    "background": "#F8FAFC",       # 背景灰白
    "surface": "#FFFFFF",          # 纯白表面
    "border": "#E2E8F0",           # 边框灰
    "divider": "#F1F5F9",          # 分隔线
    
    # 文字色
    "text_primary": "#1E293B",     # 主要文字 - 深灰黑
    "text_secondary": "#64748B",   # 次要文字 - 中灰
    "text_disabled": "#94A3B8",    # 禁用文字 - 浅灰
    "text_inverse": "#FFFFFF",     # 反色文字 - 白色
}

# 字体系统
TYPOGRAPHY = {
    "font_family": "Segoe UI, Microsoft YaHei, PingFang SC, sans-serif",
    "font_mono": "Consolas, Monaco, monospace",
    
    # 字体大小
    "size_xs": "11px",      # 辅助文字
    "size_sm": "12px",      # 小标签
    "size_base": "13px",    # 正文
    "size_md": "14px",      # 菜单、按钮
    "size_lg": "16px",      # 小标题
    "size_xl": "18px",      # 副标题
    "size_2xl": "20px",     # 标题
    "size_3xl": "24px",     # 大标题
    
    # 字重
    "weight_normal": 400,
    "weight_medium": 500,
    "weight_semibold": 600,
    "weight_bold": 700,
    
    # 行高
    "leading_tight": 1.25,
    "leading_normal": 1.5,
    "leading_relaxed": 1.75,
}

# 间距系统
SPACING = {
    "xs": 4,     # 4px
    "sm": 8,     # 8px
    "md": 12,    # 12px
    "lg": 16,    # 16px
    "xl": 20,    # 20px
    "2xl": 24,   # 24px
    "3xl": 32,   # 32px
    "4xl": 40,   # 40px
}

# 圆角系统
BORDER_RADIUS = {
    "none": 0,
    "sm": 4,     # 小圆角 - 标签、小按钮
    "md": 6,     # 中圆角 - 按钮、输入框
    "lg": 8,     # 大圆角 - 卡片
    "xl": 12,    # 超大圆角 - 模态框
    "full": 9999, # 全圆角 - 胶囊按钮
}

# 阴影系统（扁平化设计使用极浅阴影）
SHADOWS = {
    "none": "none",
    "sm": "0 1px 2px rgba(0, 0, 0, 0.05)",      # 微弱阴影
    "md": "0 1px 3px rgba(0, 0, 0, 0.1)",       # 轻微阴影 - 卡片
    "lg": "0 4px 6px rgba(0, 0, 0, 0.1)",       # 中等阴影 - 悬浮
    "xl": "0 10px 15px rgba(0, 0, 0, 0.1)",     # 强阴影 - 模态框
}

# 过渡动画
TRANSITIONS = {
    "fast": "150ms ease",
    "normal": "200ms ease",
    "slow": "300ms ease",
}

# ============================================================================
# 🎯 PySide2 样式表 (QSS)
# ============================================================================

# 主窗口样式
MAIN_WINDOW_STYLE = f"""
QMainWindow {{
    background-color: {COLORS['background']};
    font-family: {TYPOGRAPHY['font_family']};
    font-size: {TYPOGRAPHY['size_base']};
}}
"""

# 菜单栏样式
MENUBAR_STYLE = f"""
QMenuBar {{
    background-color: {COLORS['surface']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 4px 8px;
    font-size: {TYPOGRAPHY['size_md']};
}}

QMenuBar::item {{
    background: transparent;
    padding: 6px 12px;
    border-radius: {BORDER_RADIUS['md']}px;
    color: {COLORS['text_primary']};
}}

QMenuBar::item:selected {{
    background-color: {COLORS['primary_light']};
    color: {COLORS['primary']};
}}

QMenuBar::item:pressed {{
    background-color: {COLORS['primary']};
    color: {COLORS['text_inverse']};
}}

QMenu {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: {BORDER_RADIUS['md']}px;
    padding: 6px;
}}

QMenu::item {{
    padding: 8px 24px 8px 12px;
    border-radius: {BORDER_RADIUS['sm']}px;
    color: {COLORS['text_primary']};
}}

QMenu::item:selected {{
    background-color: {COLORS['primary_light']};
    color: {COLORS['primary']};
}}

QMenu::separator {{
    height: 1px;
    background-color: {COLORS['divider']};
    margin: 6px 0;
}}
"""

# 按钮样式
BUTTON_STYLES = {
    # 主要按钮
    "primary": f"""
        QPushButton {{
            background-color: {COLORS['primary']};
            color: {COLORS['text_inverse']};
            border: none;
            border-radius: {BORDER_RADIUS['md']}px;
            padding: 8px 16px;
            font-size: {TYPOGRAPHY['size_md']};
            font-weight: {TYPOGRAPHY['weight_medium']};
        }}
        
        QPushButton:hover {{
            background-color: {COLORS['primary_hover']};
        }}
        
        QPushButton:pressed {{
            background-color: {COLORS['primary']};
        }}
        
        QPushButton:disabled {{
            background-color: {COLORS['border']};
            color: {COLORS['text_disabled']};
        }}
    """,
    
    # 次要按钮
    "secondary": f"""
        QPushButton {{
            background-color: {COLORS['surface']};
            color: {COLORS['primary']};
            border: 1px solid {COLORS['border']};
            border-radius: {BORDER_RADIUS['md']}px;
            padding: 8px 16px;
            font-size: {TYPOGRAPHY['size_md']};
            font-weight: {TYPOGRAPHY['weight_medium']};
        }}
        
        QPushButton:hover {{
            background-color: {COLORS['primary_light']};
            border-color: {COLORS['primary']};
        }}
        
        QPushButton:pressed {{
            background-color: {COLORS['primary']};
            color: {COLORS['text_inverse']};
        }}
    """,
    
    # 文字按钮
    "text": f"""
        QPushButton {{
            background-color: transparent;
            color: {COLORS['primary']};
            border: none;
            border-radius: {BORDER_RADIUS['md']}px;
            padding: 8px 16px;
            font-size: {TYPOGRAPHY['size_md']};
            font-weight: {TYPOGRAPHY['weight_medium']};
        }}
        
        QPushButton:hover {{
            background-color: {COLORS['primary_light']};
        }}
    """,
    
    # 危险按钮
    "danger": f"""
        QPushButton {{
            background-color: {COLORS['error']};
            color: {COLORS['text_inverse']};
            border: none;
            border-radius: {BORDER_RADIUS['md']}px;
            padding: 8px 16px;
            font-size: {TYPOGRAPHY['size_md']};
            font-weight: {TYPOGRAPHY['weight_medium']};
        }}
        
        QPushButton:hover {{
            background-color: #DC2626;
        }}
    """,
}

# 输入框样式
INPUT_STYLE = f"""
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: {BORDER_RADIUS['md']}px;
    padding: 8px 12px;
    font-size: {TYPOGRAPHY['size_base']};
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['primary_light']};
    selection-color: {COLORS['primary']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 2px solid {COLORS['primary']};
    outline: none;
}}

QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
    background-color: {COLORS['background']};
    color: {COLORS['text_disabled']};
}}

QLineEdit::placeholder, QTextEdit::placeholder {{
    color: {COLORS['text_disabled']};
}}
"""

# 下拉框样式
COMBOBOX_STYLE = f"""
QComboBox {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: {BORDER_RADIUS['md']}px;
    padding: 8px 12px;
    font-size: {TYPOGRAPHY['size_base']};
    color: {COLORS['text_primary']};
    min-width: 120px;
}}

QComboBox:hover {{
    border-color: {COLORS['primary']};
}}

QComboBox:focus {{
    border: 2px solid {COLORS['primary']};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid {COLORS['text_secondary']};
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: {BORDER_RADIUS['md']}px;
    selection-background-color: {COLORS['primary_light']};
    selection-color: {COLORS['primary']};
}}
"""

# 表格样式
TABLE_STYLE = f"""
QTableView, QTableWidget {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: {BORDER_RADIUS['lg']}px;
    gridline-color: {COLORS['divider']};
    font-size: {TYPOGRAPHY['size_base']};
    color: {COLORS['text_primary']};
}}

QTableView::item, QTableWidget::item {{
    padding: 8px 12px;
    border-bottom: 1px solid {COLORS['divider']};
}}

QTableView::item:selected, QTableWidget::item:selected {{
    background-color: {COLORS['primary_light']};
    color: {COLORS['primary']};
}}

QTableView::item:hover, QTableWidget::item:hover {{
    background-color: {COLORS['background']};
}}

QHeaderView::section {{
    background-color: {COLORS['background']};
    color: {COLORS['text_secondary']};
    padding: 10px 12px;
    border: none;
    border-bottom: 2px solid {COLORS['border']};
    font-weight: {TYPOGRAPHY['weight_semibold']};
    font-size: {TYPOGRAPHY['size_sm']};
    text-transform: uppercase;
}}

QHeaderView::section:hover {{
    background-color: {COLORS['primary_light']};
    color: {COLORS['primary']};
}}
"""

# 标签样式
LABEL_STYLES = {
    "title": f"""
        QLabel {{
            font-size: {TYPOGRAPHY['size_2xl']};
            font-weight: {TYPOGRAPHY['weight_bold']};
            color: {COLORS['text_primary']};
        }}
    """,
    
    "subtitle": f"""
        QLabel {{
            font-size: {TYPOGRAPHY['size_lg']};
            font-weight: {TYPOGRAPHY['weight_medium']};
            color: {COLORS['text_secondary']};
        }}
    """,
    
    "body": f"""
        QLabel {{
            font-size: {TYPOGRAPHY['size_base']};
            color: {COLORS['text_primary']};
        }}
    """,
    
    "caption": f"""
        QLabel {{
            font-size: {TYPOGRAPHY['size_sm']};
            color: {COLORS['text_secondary']};
        }}
    """,
}

# 分组框样式
GROUPBOX_STYLE = f"""
QGroupBox {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: {BORDER_RADIUS['lg']}px;
    margin-top: 12px;
    padding-top: 12px;
    font-size: {TYPOGRAPHY['size_md']};
    font-weight: {TYPOGRAPHY['weight_semibold']};
    color: {COLORS['text_primary']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: {COLORS['text_secondary']};
}}
"""

# 滚动条样式
SCROLLBAR_STYLE = f"""
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

QScrollBar:horizontal {{
    background-color: {COLORS['background']};
    height: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['border']};
    border-radius: 4px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS['text_disabled']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
"""

# 进度条样式
PROGRESSBAR_STYLE = f"""
QProgressBar {{
    background-color: {COLORS['border']};
    border: none;
    border-radius: {BORDER_RADIUS['full']}px;
    height: 8px;
    text-align: center;
    font-size: {TYPOGRAPHY['size_xs']};
    color: {COLORS['text_secondary']};
}}

QProgressBar::chunk {{
    background-color: {COLORS['primary']};
    border-radius: {BORDER_RADIUS['full']}px;
}}
"""

# 选项卡样式
TABWIDGET_STYLE = f"""
QTabWidget::pane {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: {BORDER_RADIUS['lg']}px;
    top: -1px;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {COLORS['text_secondary']};
    padding: 10px 20px;
    margin-right: 4px;
    border-radius: {BORDER_RADIUS['md']}px {BORDER_RADIUS['md']}px 0 0;
    font-weight: {TYPOGRAPHY['weight_medium']};
}}

QTabBar::tab:hover {{
    background-color: {COLORS['primary_light']};
    color: {COLORS['primary']};
}}

QTabBar::tab:selected {{
    background-color: {COLORS['surface']};
    color: {COLORS['primary']};
    border: 1px solid {COLORS['border']};
    border-bottom: 2px solid {COLORS['primary']};
}}
"""

# 对话框样式
DIALOG_STYLE = f"""
QDialog {{
    background-color: {COLORS['background']};
    font-family: {TYPOGRAPHY['font_family']};
}}

QDialog QPushButton {{
    min-width: 80px;
}}
"""

# 树形控件样式
TREEVIEW_STYLE = f"""
QTreeView, QTreeWidget {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: {BORDER_RADIUS['lg']}px;
    font-size: {TYPOGRAPHY['size_base']};
    color: {COLORS['text_primary']};
    outline: none;
}}

QTreeView::item, QTreeWidget::item {{
    padding: 6px 8px;
    border-radius: {BORDER_RADIUS['sm']}px;
}}

QTreeView::item:selected, QTreeWidget::item:selected {{
    background-color: {COLORS['primary_light']};
    color: {COLORS['primary']};
}}

QTreeView::item:hover, QTreeWidget::item:hover {{
    background-color: {COLORS['background']};
}}

QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid {COLORS['text_secondary']};
}}

QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 6px solid {COLORS['text_secondary']};
}}
"""

# 工具提示样式
TOOLTIP_STYLE = f"""
QToolTip {{
    background-color: {COLORS['text_primary']};
    color: {COLORS['text_inverse']};
    border: none;
    border-radius: {BORDER_RADIUS['md']}px;
    padding: 6px 10px;
    font-size: {TYPOGRAPHY['size_sm']};
}}
"""

# ============================================================================
# 🔧 完整样式组合
# ============================================================================

def get_complete_style() -> str:
    """获取完整的应用程序样式表"""
    styles = [
        MAIN_WINDOW_STYLE,
        MENUBAR_STYLE,
        BUTTON_STYLES["primary"],
        BUTTON_STYLES["secondary"],
        BUTTON_STYLES["text"],
        INPUT_STYLE,
        COMBOBOX_STYLE,
        TABLE_STYLE,
        LABEL_STYLES["body"],
        GROUPBOX_STYLE,
        SCROLLBAR_STYLE,
        PROGRESSBAR_STYLE,
        TABWIDGET_STYLE,
        DIALOG_STYLE,
        TREEVIEW_STYLE,
        TOOLTIP_STYLE,
    ]
    return "\n\n".join(styles)


def get_button_style(variant: str = "primary") -> str:
    """获取特定变体的按钮样式"""
    return BUTTON_STYLES.get(variant, BUTTON_STYLES["primary"])


def get_label_style(variant: str = "body") -> str:
    """获取特定变体的标签样式"""
    return LABEL_STYLES.get(variant, LABEL_STYLES["body"])


# ============================================================================
# 📋 使用示例
# ============================================================================

if __name__ == "__main__":
    # 打印颜色系统
    print("🎨 设计系统颜色:")
    for name, value in COLORS.items():
        print(f"  {name}: {value}")
    
    print("\n✅ 样式系统加载完成")
    print(f"主要字体: {TYPOGRAPHY['font_family']}")
    print(f"基础字号: {TYPOGRAPHY['size_base']}")
    print(f"主色调: {COLORS['primary']}")
