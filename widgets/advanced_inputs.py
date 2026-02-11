#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
高级输入控件模块
包含日期时间选择器、颜色选择器等高级输入控件
"""

from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDateTimeEdit,
    QPushButton, QColorDialog, QFileDialog, QSlider, QDial,
    QComboBox, QCheckBox, QLineEdit, QGroupBox
)
from PySide2.QtCore import Qt, QDateTime
from PySide2.QtGui import QColor

class DateTimeInputWidget(QWidget):
    """日期时间输入控件"""
    def __init__(self, parent=None, label="日期时间"):
        super().__init__(parent)
        self.label = label
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标签
        label = QLabel(self.label)
        layout.addWidget(label)
        
        # 日期时间选择器
        self.datetime_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        layout.addWidget(self.datetime_edit)
    
    def get_value(self):
        """获取值"""
        return self.datetime_edit.dateTime()
    
    def set_value(self, datetime):
        """设置值"""
        self.datetime_edit.setDateTime(datetime)

class ColorInputWidget(QWidget):
    """颜色输入控件"""
    def __init__(self, parent=None, label="颜色"):
        super().__init__(parent)
        self.label = label
        self.current_color = QColor(255, 0, 0)  # 默认红色
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标签
        label = QLabel(self.label)
        layout.addWidget(label)
        
        # 颜色选择按钮
        self.color_button = QPushButton("选择颜色")
        self.color_button.setStyleSheet(f"background-color: {self.current_color.name()}")
        self.color_button.clicked.connect(self.select_color)
        layout.addWidget(self.color_button)
    
    def select_color(self):
        """选择颜色"""
        color = QColorDialog.getColor(self.current_color, self, "选择颜色")
        if color.isValid():
            self.current_color = color
            self.color_button.setStyleSheet(f"background-color: {color.name()}")
    
    def get_value(self):
        """获取值"""
        return self.current_color
    
    def set_value(self, color):
        """设置值"""
        if isinstance(color, QColor) and color.isValid():
            self.current_color = color
            self.color_button.setStyleSheet(f"background-color: {color.name()}")

class FileInputWidget(QWidget):
    """文件输入控件"""
    def __init__(self, parent=None, label="文件", is_directory=False):
        super().__init__(parent)
        self.label = label
        self.is_directory = is_directory
        self.file_path = ""
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标签
        label = QLabel(self.label)
        layout.addWidget(label)
        
        # 文件路径显示
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        layout.addWidget(self.path_edit)
        
        # 选择按钮
        self.select_button = QPushButton("浏览...")
        self.select_button.clicked.connect(self.select_file)
        layout.addWidget(self.select_button)
    
    def select_file(self):
        """选择文件或目录"""
        if self.is_directory:
            # 选择目录
            directory = QFileDialog.getExistingDirectory(self, "选择目录")
            if directory:
                self.file_path = directory
                self.path_edit.setText(directory)
        else:
            # 选择文件
            file, _ = QFileDialog.getOpenFileName(self, "选择文件")
            if file:
                self.file_path = file
                self.path_edit.setText(file)
    
    def get_value(self):
        """获取值"""
        return self.file_path
    
    def set_value(self, path):
        """设置值"""
        self.file_path = path
        self.path_edit.setText(path)

class SliderInputWidget(QWidget):
    """滑动条输入控件"""
    def __init__(self, parent=None, label="值", min_value=0, max_value=100, default_value=50):
        super().__init__(parent)
        self.label = label
        self.min_value = min_value
        self.max_value = max_value
        self.current_value = default_value
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标签和值显示
        value_layout = QHBoxLayout()
        label = QLabel(self.label)
        self.value_label = QLabel(str(self.current_value))
        value_layout.addWidget(label)
        value_layout.addStretch()
        value_layout.addWidget(self.value_label)
        layout.addLayout(value_layout)
        
        # 滑动条
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(self.min_value)
        self.slider.setMaximum(self.max_value)
        self.slider.setValue(self.current_value)
        self.slider.valueChanged.connect(self.update_value)
        layout.addWidget(self.slider)
    
    def update_value(self, value):
        """更新值"""
        self.current_value = value
        self.value_label.setText(str(value))
    
    def get_value(self):
        """获取值"""
        return self.current_value
    
    def set_value(self, value):
        """设置值"""
        if self.min_value <= value <= self.max_value:
            self.current_value = value
            self.slider.setValue(value)
            self.value_label.setText(str(value))

class DialInputWidget(QWidget):
    """旋钮输入控件"""
    def __init__(self, parent=None, label="值", min_value=0, max_value=100, default_value=50):
        super().__init__(parent)
        self.label = label
        self.min_value = min_value
        self.max_value = max_value
        self.current_value = default_value
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标签
        label = QLabel(self.label)
        layout.addWidget(label)
        
        # 旋钮
        self.dial = QDial()
        self.dial.setMinimum(self.min_value)
        self.dial.setMaximum(self.max_value)
        self.dial.setValue(self.current_value)
        self.dial.valueChanged.connect(self.update_value)
        layout.addWidget(self.dial)
        
        # 值显示
        self.value_label = QLabel(str(self.current_value), alignment=Qt.AlignCenter)
        layout.addWidget(self.value_label)
    
    def update_value(self, value):
        """更新值"""
        self.current_value = value
        self.value_label.setText(str(value))
    
    def get_value(self):
        """获取值"""
        return self.current_value
    
    def set_value(self, value):
        """设置值"""
        if self.min_value <= value <= self.max_value:
            self.current_value = value
            self.dial.setValue(value)
            self.value_label.setText(str(value))

class CheckedComboBox(QWidget):
    """下拉复选框控件"""
    def __init__(self, parent=None, label="选项"):
        super().__init__(parent)
        self.label = label
        self.options = []
        self.checked_options = []
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标签
        label = QLabel(self.label)
        layout.addWidget(label)
        
        # 显示选中项
        self.display_edit = QLineEdit()
        self.display_edit.setReadOnly(True)
        self.display_edit.setText("未选择")
        layout.addWidget(self.display_edit)
        
        # 选项组
        self.options_group = QGroupBox("选择选项")
        self.options_layout = QVBoxLayout(self.options_group)
        layout.addWidget(self.options_group)
    
    def add_option(self, text, checked=False):
        """添加选项"""
        checkbox = QCheckBox(text)
        checkbox.setChecked(checked)
        checkbox.stateChanged.connect(self.update_selection)
        self.options_layout.addWidget(checkbox)
        self.options.append(checkbox)
        if checked:
            self.checked_options.append(text)
        self.update_display()
    
    def update_selection(self):
        """更新选择"""
        self.checked_options = [cb.text() for cb in self.options if cb.isChecked()]
        self.update_display()
    
    def update_display(self):
        """更新显示"""
        if self.checked_options:
            self.display_edit.setText(", ".join(self.checked_options))
        else:
            self.display_edit.setText("未选择")
    
    def get_value(self):
        """获取值"""
        return self.checked_options
    
    def set_value(self, options):
        """设置值"""
        for cb in self.options:
            cb.setChecked(cb.text() in options)
        self.checked_options = [cb.text() for cb in self.options if cb.isChecked()]
        self.update_display()

class AdvancedInputsGroup(QWidget):
    """高级输入控件组"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 日期时间选择器
        self.datetime_widget = DateTimeInputWidget(label="选择日期时间")
        layout.addWidget(self.datetime_widget)
        
        # 颜色选择器
        self.color_widget = ColorInputWidget(label="选择颜色")
        layout.addWidget(self.color_widget)
        
        # 文件选择器
        self.file_widget = FileInputWidget(label="选择文件")
        layout.addWidget(self.file_widget)
        
        # 目录选择器
        self.directory_widget = FileInputWidget(label="选择目录", is_directory=True)
        layout.addWidget(self.directory_widget)
        
        # 滑动条
        self.slider_widget = SliderInputWidget(label="滑动条值")
        layout.addWidget(self.slider_widget)
        
        # 旋钮
        self.dial_widget = DialInputWidget(label="旋钮值")
        layout.addWidget(self.dial_widget)
        
        # 下拉复选框
        self.checked_combo = CheckedComboBox(label="多选选项")
        self.checked_combo.add_option("选项1", checked=True)
        self.checked_combo.add_option("选项2")
        self.checked_combo.add_option("选项3")
        self.checked_combo.add_option("选项4")
        layout.addWidget(self.checked_combo)
    
    def get_all_values(self):
        """获取所有值"""
        values = {
            "datetime": self.datetime_widget.get_value(),
            "color": self.color_widget.get_value(),
            "file": self.file_widget.get_value(),
            "directory": self.directory_widget.get_value(),
            "slider": self.slider_widget.get_value(),
            "dial": self.dial_widget.get_value(),
            "checked_combo": self.checked_combo.get_value()
        }
        return values
