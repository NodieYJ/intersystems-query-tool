#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
高级交互功能模块
包含拖拽功能、上下文菜单、快捷键支持等
"""

from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMenu,
    QAction, QLineEdit, QTextEdit, QMessageBox
)
from PySide2.QtCore import Qt, QMimeData, QPoint
from PySide2.QtGui import QDrag, QKeySequence, QCursor

class DraggableWidget(QWidget):
    """可拖拽的控件"""
    def __init__(self, parent=None, text="可拖拽控件"):
        super().__init__(parent)
        self.text = text
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        label = QLabel(self.text)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        # 设置样式
        self.setStyleSheet("""
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 5px;
        """)
    
    def mousePressEvent(self, event):
        """鼠标按下事件，开始拖拽"""
        if event.button() == Qt.LeftButton:
            # 创建拖拽对象
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.text)
            drag.setMimeData(mime_data)
            
            # 开始拖拽
            drag.exec_(Qt.CopyAction | Qt.MoveAction)

class DropAreaWidget(QWidget):
    """放置区域控件"""
    def __init__(self, parent=None, text="放置区域"):
        super().__init__(parent)
        self.text = text
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.label = QLabel(self.text)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        
        # 设置样式
        self.setStyleSheet("""
            background-color: #e8f4f8;
            border: 2px dashed #1e90ff;
            border-radius: 5px;
        """)
    
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            # 改变样式以提供视觉反馈
            self.setStyleSheet("""
                background-color: #d0e8f0;
                border: 2px solid #1e90ff;
                border-radius: 5px;
            """)
    
    def dragLeaveEvent(self, event):
        """拖拽离开事件"""
        # 恢复原始样式
        self.setStyleSheet("""
            background-color: #e8f4f8;
            border: 2px dashed #1e90ff;
            border-radius: 5px;
        """)
    
    def dropEvent(self, event):
        """放置事件"""
        if event.mimeData().hasText():
            # 获取拖拽的文本
            text = event.mimeData().text()
            self.label.setText(f"已放置: {text}")
            event.acceptProposedAction()
            
            # 恢复原始样式
            self.setStyleSheet("""
                background-color: #e8f4f8;
                border: 2px dashed #1e90ff;
                border-radius: 5px;
            """)

class ContextMenuWidget(QWidget):
    """带上下文菜单的控件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        label = QLabel("右键点击此处显示上下文菜单")
        layout.addWidget(label)
        
        # 文本编辑框
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("在此处输入文本...")
        layout.addWidget(self.text_edit)
        
        # 设置上下文菜单策略
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def show_context_menu(self, position):
        """显示上下文菜单"""
        # 创建上下文菜单
        context_menu = QMenu(self)
        
        # 添加菜单项
        copy_action = context_menu.addAction("复制")
        paste_action = context_menu.addAction("粘贴")
        cut_action = context_menu.addAction("剪切")
        context_menu.addSeparator()
        clear_action = context_menu.addAction("清空")
        context_menu.addSeparator()
        about_action = context_menu.addAction("关于")
        
        # 连接信号
        copy_action.triggered.connect(self.text_edit.copy)
        paste_action.triggered.connect(self.text_edit.paste)
        cut_action.triggered.connect(self.text_edit.cut)
        clear_action.triggered.connect(self.text_edit.clear)
        about_action.triggered.connect(self.show_about)
        
        # 显示菜单
        context_menu.exec_(self.mapToGlobal(position))
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于", "上下文菜单示例\n\n这是一个带上下文菜单的控件示例")

class ShortcutWidget(QWidget):
    """带快捷键支持的控件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_shortcuts()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        label = QLabel("快捷键示例")
        layout.addWidget(label)
        
        # 快捷键说明
        shortcuts_label = QLabel("可用快捷键:\n"  "Ctrl+C: 复制\n"  "Ctrl+V: 粘贴\n"  "Ctrl+X: 剪切\n"  "Ctrl+Z: 撤销\n"  "Ctrl+Y: 重做\n"  "Ctrl+A: 全选\n"  "F1: 帮助")
        layout.addWidget(shortcuts_label)
        
        # 文本编辑框
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("在此处输入文本并测试快捷键...")
        layout.addWidget(self.text_edit)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        layout.addWidget(self.status_label)
    
    def setup_shortcuts(self):
        """设置快捷键"""
        # 复制快捷键
        copy_action = QAction("复制", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(lambda: self.update_status("复制"))
        self.addAction(copy_action)
        
        # 粘贴快捷键
        paste_action = QAction("粘贴", self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(lambda: self.update_status("粘贴"))
        self.addAction(paste_action)
        
        # 剪切快捷键
        cut_action = QAction("剪切", self)
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(lambda: self.update_status("剪切"))
        self.addAction(cut_action)
        
        # 撤销快捷键
        undo_action = QAction("撤销", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(lambda: self.update_status("撤销"))
        self.addAction(undo_action)
        
        # 重做快捷键
        redo_action = QAction("重做", self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(lambda: self.update_status("重做"))
        self.addAction(redo_action)
        
        # 全选快捷键
        select_all_action = QAction("全选", self)
        select_all_action.setShortcut(QKeySequence.SelectAll)
        select_all_action.triggered.connect(lambda: self.update_status("全选"))
        self.addAction(select_all_action)
        
        # 帮助快捷键
        help_action = QAction("帮助", self)
        help_action.setShortcut(QKeySequence.HelpContents)
        help_action.triggered.connect(self.show_help)
        self.addAction(help_action)
    
    def update_status(self, action):
        """更新状态"""
        self.status_label.setText(f"执行操作: {action}")
    
    def show_help(self):
        """显示帮助"""
        QMessageBox.information(self, "帮助", "快捷键帮助\n\nCtrl+C: 复制\nCtrl+V: 粘贴\nCtrl+X: 剪切\nCtrl+Z: 撤销\nCtrl+Y: 重做\nCtrl+A: 全选\nF1: 帮助")

class DragAndDropDemo(QWidget):
    """拖拽功能演示"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("拖拽功能演示")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # 可拖拽控件
        draggable_layout = QHBoxLayout()
        draggable_layout.addWidget(DraggableWidget(text="控件 1"))
        draggable_layout.addWidget(DraggableWidget(text="控件 2"))
        draggable_layout.addWidget(DraggableWidget(text="控件 3"))
        layout.addLayout(draggable_layout)
        
        # 放置区域
        self.drop_area = DropAreaWidget()
        layout.addWidget(self.drop_area)

class AdvancedInteractionsGroup(QWidget):
    """高级交互功能组"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 拖拽功能演示
        drag_drop_demo = DragAndDropDemo()
        layout.addWidget(drag_drop_demo)
        
        # 上下文菜单演示
        context_menu_widget = ContextMenuWidget()
        layout.addWidget(context_menu_widget)
        
        # 快捷键演示
        shortcut_widget = ShortcutWidget()
        layout.addWidget(shortcut_widget)
