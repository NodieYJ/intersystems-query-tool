#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI组件工厂模块

提供标准化的UI组件创建功能，确保UI一致性。
"""

from PySide2.QtWidgets import (
    QPushButton, QLabel, QLineEdit, QComboBox,
    QGroupBox, QFrame, QWidget
)
from PySide2.QtCore import Qt

from src.presentation.utils.theme_manager import get_theme_manager


class UIButtonFactory:
    """
    UI按钮工厂
    
    创建标准化的按钮组件。
    """
    
    @staticmethod
    def create_primary_button(text: str, parent=None) -> QPushButton:
        """
        创建主要按钮
        
        Args:
            text: 按钮文本
            parent: 父部件
            
        Returns:
            QPushButton: 配置好的按钮
        """
        btn = QPushButton(text, parent)
        btn.setObjectName('btn_primary')
        return btn
    
    @staticmethod
    def create_secondary_button(text: str, parent=None) -> QPushButton:
        """
        创建次要按钮
        
        Args:
            text: 按钮文本
            parent: 父部件
            
        Returns:
            QPushButton: 配置好的按钮
        """
        btn = QPushButton(text, parent)
        btn.setObjectName('btn_secondary')
        return btn
    
    @staticmethod
    def create_success_button(text: str, parent=None) -> QPushButton:
        """
        创建成功按钮
        
        Args:
            text: 按钮文本
            parent: 父部件
            
        Returns:
            QPushButton: 配置好的按钮
        """
        btn = QPushButton(text, parent)
        btn.setObjectName('btn_success')
        return btn
    
    @staticmethod
    def create_danger_button(text: str, parent=None) -> QPushButton:
        """
        创建危险按钮（删除等）
        
        Args:
            text: 按钮文本
            parent: 父部件
            
        Returns:
            QPushButton: 配置好的按钮
        """
        btn = QPushButton(text, parent)
        btn.setObjectName('btn_danger')
        return btn
    
    @staticmethod
    def create_warning_button(text: str, parent=None) -> QPushButton:
        """
        创建警告按钮
        
        Args:
            text: 按钮文本
            parent: 父部件
            
        Returns:
            QPushButton: 配置好的按钮
        """
        btn = QPushButton(text, parent)
        btn.setObjectName('btn_warning')
        return btn
    
    @staticmethod
    def create_icon_button(icon_text: str, parent=None) -> QPushButton:
        """
        创建图标按钮
        
        Args:
            icon_text: 图标字符（如 emoji）
            parent: 父部件
            
        Returns:
            QPushButton: 配置好的按钮
        """
        btn = QPushButton(icon_text, parent)
        btn.setObjectName('btn_icon')
        btn.setFixedSize(36, 36)
        return btn


class UILabelFactory:
    """
    UI标签工厂
    
    创建标准化的标签组件。
    """
    
    @staticmethod
    def create_title(text: str, parent=None) -> QLabel:
        """
        创建标题标签
        
        Args:
            text: 标题文本
            parent: 父部件
            
        Returns:
            QLabel: 配置好的标签
        """
        label = QLabel(text, parent)
        label.setObjectName('page_title')
        return label
    
    @staticmethod
    def create_subtitle(text: str, parent=None) -> QLabel:
        """
        创建副标题标签
        
        Args:
            text: 副标题文本
            parent: 父部件
            
        Returns:
            QLabel: 配置好的标签
        """
        label = QLabel(text, parent)
        label.setObjectName('page_subtitle')
        return label
    
    @staticmethod
    def create_status_label(text: str, status: str, parent=None) -> QLabel:
        """
        创建状态标签
        
        Args:
            text: 标签文本
            status: 状态类型 (success/error/warning/info)
            parent: 父部件
            
        Returns:
            QLabel: 配置好的标签
        """
        label = QLabel(text, parent)
        label.setObjectName(f'status_{status}')
        return label
    
    @staticmethod
    def create_muted_text(text: str, parent=None) -> QLabel:
        """
        创建次要/灰色文本标签
        
        Args:
            text: 文本内容
            parent: 父部件
            
        Returns:
            QLabel: 配置好的标签
        """
        label = QLabel(text, parent)
        label.setObjectName('text_muted')
        return label


class UIInputFactory:
    """
    UI输入框工厂
    
    创建标准化的输入组件。
    """
    
    @staticmethod
    def create_line_edit(placeholder: str = '', parent=None) -> QLineEdit:
        """
        创建单行输入框
        
        Args:
            placeholder: 占位符文本
            parent: 父部件
            
        Returns:
            QLineEdit: 配置好的输入框
        """
        edit = QLineEdit(parent)
        edit.setPlaceholderText(placeholder)
        return edit
    
    @staticmethod
    def create_combo_box(items: list = None, parent=None) -> QComboBox:
        """
        创建下拉框
        
        Args:
            items: 选项列表
            parent: 父部件
            
        Returns:
            QComboBox: 配置好的下拉框
        """
        combo = QComboBox(parent)
        if items:
            combo.addItems(items)
        return combo


class UICardFactory:
    """
    UI卡片工厂
    
    创建标准化的卡片组件。
    """
    
    @staticmethod
    def create_stat_card(title: str, value: str, subtitle: str, parent=None) -> QFrame:
        """
        创建统计卡片
        
        Args:
            title: 标题
            value: 数值
            subtitle: 副标题
            parent: 父部件
            
        Returns:
            QFrame: 配置好的卡片
        """
        from PySide2.QtWidgets import QVBoxLayout
        
        card = QFrame(parent)
        card.setObjectName('stat_card')
        
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
    
    @staticmethod
    def create_group_box(title: str, parent=None) -> QGroupBox:
        """
        创建分组框
        
        Args:
            title: 标题
            parent: 父部件
            
        Returns:
            QGroupBox: 配置好的分组框
        """
        group = QGroupBox(title, parent)
        return group


class UIContainerFactory:
    """
    UI容器工厂
    
    创建标准化的容器组件。
    """
    
    @staticmethod
    def create_sidebar(parent=None) -> QWidget:
        """
        创建侧边栏容器
        
        Args:
            parent: 父部件
            
        Returns:
            QWidget: 配置好的侧边栏
        """
        sidebar = QWidget(parent)
        sidebar.setObjectName('sidebar')
        return sidebar
    
    @staticmethod
    def create_content_area(parent=None) -> QWidget:
        """
        创建内容区域容器
        
        Args:
            parent: 父部件
            
        Returns:
            QWidget: 配置好的内容区域
        """
        content = QWidget(parent)
        content.setObjectName('content_area')
        return content
    
    @staticmethod
    def create_divider(horizontal: bool = True, parent=None) -> QFrame:
        """
        创建分隔线
        
        Args:
            horizontal: 是否为水平分隔线
            parent: 父部件
            
        Returns:
            QFrame: 配置好的分隔线
        """
        line = QFrame(parent)
        if horizontal:
            line.setFrameShape(QFrame.HLine)
        else:
            line.setFrameShape(QFrame.VLine)
        line.setStyleSheet('background-color: #F1F5F9;')
        return line


# 便捷函数
def create_export_button(parent=None) -> QPushButton:
    """创建导出按钮（主要按钮）"""
    return UIButtonFactory.create_primary_button('📥 导出', parent)


def create_import_button(parent=None) -> QPushButton:
    """创建导入按钮（次要按钮）"""
    return UIButtonFactory.create_secondary_button('📤 导入', parent)


def create_save_button(parent=None) -> QPushButton:
    """创建保存按钮（成功按钮）"""
    return UIButtonFactory.create_success_button('💾 保存', parent)


def create_delete_button(parent=None) -> QPushButton:
    """创建删除按钮（危险按钮）"""
    return UIButtonFactory.create_danger_button('🗑️ 删除', parent)


def create_cancel_button(parent=None) -> QPushButton:
    """创建取消按钮（次要按钮）"""
    return UIButtonFactory.create_secondary_button('取消', parent)


def create_confirm_button(parent=None) -> QPushButton:
    """创建确认按钮（主要按钮）"""
    return UIButtonFactory.create_primary_button('确认', parent)
