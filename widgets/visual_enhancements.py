#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视觉增强模块
包含图标、动画效果等视觉增强功能
"""

import os
from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QProgressBar, QApplication
)
from PySide2.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide2.QtGui import QIcon, QPixmap, QColor, QPalette, QLinearGradient

class AnimatedButton(QPushButton):
    """带动画效果的按钮"""
    def __init__(self, parent=None, text="按钮"):
        super().__init__(parent)
        self.setText(text)
        self.setup_animations()
    
    def setup_animations(self):
        """设置动画"""
        # 悬停动画
        self.hover_animation = QPropertyAnimation(self, b"minimumHeight")
        self.hover_animation.setDuration(200)
        self.hover_animation.setStartValue(30)
        self.hover_animation.setEndValue(35)
        self.hover_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # 点击动画
        self.click_animation = QPropertyAnimation(self, b"minimumHeight")
        self.click_animation.setDuration(100)
        self.click_animation.setStartValue(35)
        self.click_animation.setEndValue(28)
        self.click_animation.setEasingCurve(QEasingCurve.InOutQuad)
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        super().enterEvent(event)
        self.hover_animation.setDirection(QPropertyAnimation.Forward)
        self.hover_animation.start()
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        super().leaveEvent(event)
        self.hover_animation.setDirection(QPropertyAnimation.Backward)
        self.hover_animation.start()
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.click_animation.setDirection(QPropertyAnimation.Forward)
            self.click_animation.start()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton:
            self.click_animation.setDirection(QPropertyAnimation.Backward)
            self.click_animation.start()

class FadeWidget(QWidget):
    """淡入淡出效果的控件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_animation()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        label = QLabel("淡入淡出效果示例")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        # 渐变背景
        gradient = QLinearGradient(0, 0, 0, 100)
        gradient.setColorAt(0, QColor(100, 149, 237))
        gradient.setColorAt(1, QColor(70, 130, 180))
        palette = self.palette()
        palette.setBrush(QPalette.Background, gradient)
        self.setPalette(palette)
        self.setAutoFillBackground(True)
    
    def setup_animation(self):
        """设置动画"""
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(1000)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
    
    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)
        self.fade_animation.start()
    
    def start_fade(self):
        """开始淡入动画"""
        self.fade_animation.start()

class ProgressAnimation(QWidget):
    """进度条动画"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0
        self.setup_ui()
        self.setup_animation()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        label = QLabel("进度条动画示例")
        layout.addWidget(label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        self.start_button = QPushButton("开始动画")
        self.start_button.clicked.connect(self.start_animation)
        layout.addWidget(self.start_button)
    
    def setup_animation(self):
        """设置动画"""
        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_progress)
    
    def update_progress(self):
        """更新进度"""
        self.progress += 1
        if self.progress > 100:
            self.progress = 0
            self.timer.stop()
            self.start_button.setText("开始动画")
        self.progress_bar.setValue(self.progress)
    
    def start_animation(self):
        """开始动画"""
        if not self.timer.isActive():
            self.timer.start()
            self.start_button.setText("停止动画")
        else:
            self.timer.stop()
            self.start_button.setText("开始动画")

class IconWidget(QWidget):
    """图标示例控件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        label = QLabel("图标示例")
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(label)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 创建带图标的按钮
        buttons = [
            ("文件", "📄"),
            ("编辑", "✏️"),
            ("视图", "👁️"),
            ("工具", "🛠️"),
            ("帮助", "❓")
        ]
        
        for text, emoji in buttons:
            button = AnimatedButton(text=emoji + " " + text)
            button_layout.addWidget(button)
        
        layout.addLayout(button_layout)

class VisualEnhancementsGroup(QWidget):
    """视觉增强控件组"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("视觉增强效果")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # 图标示例
        icon_widget = IconWidget()
        layout.addWidget(icon_widget)
        
        # 淡入淡出效果
        fade_widget = FadeWidget()
        layout.addWidget(fade_widget)
        
        # 进度条动画
        progress_widget = ProgressAnimation()
        layout.addWidget(progress_widget)
        
        # 动画按钮
        animated_buttons_layout = QHBoxLayout()
        animated_buttons_layout.addWidget(AnimatedButton(text="动画按钮 1"))
        animated_buttons_layout.addWidget(AnimatedButton(text="动画按钮 2"))
        animated_buttons_layout.addWidget(AnimatedButton(text="动画按钮 3"))
        layout.addLayout(animated_buttons_layout)
