#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据展示控件模块
包含表格视图、树形视图、列表视图等数据展示控件
"""

from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem, QTabWidget,
    QGroupBox, QStackedWidget, QPushButton, QHeaderView
)
from PySide2.QtCore import Qt, QSize
from PySide2.QtGui import QIcon, QColor

class TableViewWidget(QWidget):
    """表格视图控件"""
    def __init__(self, parent=None, label="表格数据"):
        super().__init__(parent)
        self.label = label
        self.setup_ui()
        self.populate_sample_data()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标签
        label = QLabel(self.label)
        layout.addWidget(label)
        
        # 表格
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(["ID", "名称", "值", "状态"])
        
        # 设置表头自适应
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.table_widget)
    
    def populate_sample_data(self):
        """填充示例数据"""
        sample_data = [
            [1, "项目A", 100, "活跃"],
            [2, "项目B", 200, "已完成"],
            [3, "项目C", 150, "活跃"],
            [4, "项目D", 300, "已暂停"],
            [5, "项目E", 250, "活跃"]
        ]
        
        self.table_widget.setRowCount(len(sample_data))
        
        for row, data in enumerate(sample_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                # 设置状态列的颜色
                if col == 3:
                    if value == "活跃":
                        item.setBackground(QColor(144, 238, 144))  # 浅绿色
                    elif value == "已完成":
                        item.setBackground(QColor(173, 216, 230))  # 浅蓝色
                    elif value == "已暂停":
                        item.setBackground(QColor(255, 255, 153))  # 浅黄色
                self.table_widget.setItem(row, col, item)
    
    def set_data(self, data, headers=None):
        """设置数据"""
        if headers:
            self.table_widget.setColumnCount(len(headers))
            self.table_widget.setHorizontalHeaderLabels(headers)
            # 设置表头自适应
            header = self.table_widget.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Stretch)
        
        if data:
            self.table_widget.setRowCount(len(data))
            for row, row_data in enumerate(data):
                for col, value in enumerate(row_data):
                    item = QTableWidgetItem(str(value))
                    self.table_widget.setItem(row, col, item)
    
    def get_data(self):
        """获取数据"""
        data = []
        for row in range(self.table_widget.rowCount()):
            row_data = []
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                if item:
                    row_data.append(item.text())
                else:
                    row_data.append("")
            data.append(row_data)
        return data

class TreeViewWidget(QWidget):
    """树形视图控件"""
    def __init__(self, parent=None, label="树形数据"):
        super().__init__(parent)
        self.label = label
        self.setup_ui()
        self.populate_sample_data()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标签
        label = QLabel(self.label)
        layout.addWidget(label)
        
        # 树控件
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["名称", "类型"])
        
        # 设置表头自适应
        header = self.tree_widget.header()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.tree_widget)
    
    def populate_sample_data(self):
        """填充示例数据"""
        # 创建根节点
        root1 = QTreeWidgetItem(self.tree_widget, ["文件夹1", "目录"])
        root2 = QTreeWidgetItem(self.tree_widget, ["文件夹2", "目录"])
        
        # 添加子节点
        child1_1 = QTreeWidgetItem(root1, ["文件1.txt", "文本文件"])
        child1_2 = QTreeWidgetItem(root1, ["文件2.py", "Python文件"])
        child1_3 = QTreeWidgetItem(root1, ["子文件夹", "目录"])
        
        child2_1 = QTreeWidgetItem(root2, ["文件3.csv", "CSV文件"])
        child2_2 = QTreeWidgetItem(root2, ["文件4.json", "JSON文件"])
        
        # 添加孙子节点
        grandchild1_3_1 = QTreeWidgetItem(child1_3, ["文件5.txt", "文本文件"])
        
        # 展开所有节点
        self.tree_widget.expandAll()
    
    def add_node(self, parent, name, type):
        """添加节点"""
        if parent is None:
            return QTreeWidgetItem(self.tree_widget, [name, type])
        else:
            return QTreeWidgetItem(parent, [name, type])
    
    def get_selected_items(self):
        """获取选中项"""
        return self.tree_widget.selectedItems()

class ListViewWidget(QWidget):
    """列表视图控件"""
    def __init__(self, parent=None, label="列表数据"):
        super().__init__(parent)
        self.label = label
        self.setup_ui()
        self.populate_sample_data()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标签
        label = QLabel(self.label)
        layout.addWidget(label)
        
        # 列表控件
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
    
    def populate_sample_data(self):
        """填充示例数据"""
        sample_items = [
            "项目计划",
            "需求分析",
            "设计文档",
            "代码实现",
            "测试报告",
            "部署计划"
        ]
        
        for item_text in sample_items:
            item = QListWidgetItem(item_text)
            self.list_widget.addItem(item)
    
    def add_item(self, text):
        """添加项"""
        item = QListWidgetItem(text)
        self.list_widget.addItem(item)
    
    def remove_selected_item(self):
        """移除选中项"""
        for item in self.list_widget.selectedItems():
            self.list_widget.takeItem(self.list_widget.row(item))
    
    def get_items(self):
        """获取所有项"""
        items = []
        for i in range(self.list_widget.count()):
            items.append(self.list_widget.item(i).text())
        return items

class TabWidget(QWidget):
    """选项卡控件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 选项卡控件
        self.tab_widget = QTabWidget()
        
        # 添加选项卡
        self.add_tabs()
        
        layout.addWidget(self.tab_widget)
    
    def add_tabs(self):
        """添加选项卡"""
        # 表格视图选项卡
        table_tab = QWidget()
        table_layout = QVBoxLayout(table_tab)
        table_view = TableViewWidget(label="项目数据")
        table_layout.addWidget(table_view)
        self.tab_widget.addTab(table_tab, "表格")
        
        # 树形视图选项卡
        tree_tab = QWidget()
        tree_layout = QVBoxLayout(tree_tab)
        tree_view = TreeViewWidget(label="文件结构")
        tree_layout.addWidget(tree_view)
        self.tab_widget.addTab(tree_tab, "树形")
        
        # 列表视图选项卡
        list_tab = QWidget()
        list_layout = QVBoxLayout(list_tab)
        list_view = ListViewWidget(label="任务列表")
        list_layout.addWidget(list_view)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        add_button = QPushButton("添加项")
        remove_button = QPushButton("移除选中项")
        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        list_layout.addLayout(button_layout)
        
        self.tab_widget.addTab(list_tab, "列表")
    
    def add_tab(self, widget, title):
        """添加选项卡"""
        self.tab_widget.addTab(widget, title)

class StackedWidget(QWidget):
    """堆栈窗口控件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 按钮
        self.btn_page1 = QPushButton("页面1")
        self.btn_page2 = QPushButton("页面2")
        self.btn_page3 = QPushButton("页面3")
        
        button_layout.addWidget(self.btn_page1)
        button_layout.addWidget(self.btn_page2)
        button_layout.addWidget(self.btn_page3)
        
        layout.addLayout(button_layout)
        
        # 堆栈窗口
        self.stacked_widget = QStackedWidget()
        
        # 添加页面
        self.add_pages()
        
        layout.addWidget(self.stacked_widget)
        
        # 连接信号
        self.btn_page1.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.btn_page2.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.btn_page3.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
    
    def add_pages(self):
        """添加页面"""
        # 页面1
        page1 = QWidget()
        page1_layout = QVBoxLayout(page1)
        page1_layout.addWidget(QLabel("这是页面1的内容"))
        page1_layout.addWidget(QPushButton("页面1按钮"))
        self.stacked_widget.addWidget(page1)
        
        # 页面2
        page2 = QWidget()
        page2_layout = QVBoxLayout(page2)
        page2_layout.addWidget(QLabel("这是页面2的内容"))
        page2_layout.addWidget(QPushButton("页面2按钮"))
        self.stacked_widget.addWidget(page2)
        
        # 页面3
        page3 = QWidget()
        page3_layout = QVBoxLayout(page3)
        page3_layout.addWidget(QLabel("这是页面3的内容"))
        page3_layout.addWidget(QPushButton("页面3按钮"))
        self.stacked_widget.addWidget(page3)
    
    def add_page(self, widget, title):
        """添加页面"""
        self.stacked_widget.addWidget(widget)
        # 可以根据需要添加对应的按钮

class DataDisplayGroup(QWidget):
    """数据展示控件组"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 选项卡控件
        self.tab_widget = TabWidget()
        layout.addWidget(self.tab_widget)
        
        # 堆栈窗口
        self.stacked_widget = StackedWidget()
        layout.addWidget(self.stacked_widget)
