#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
表单设计器使用示例
展示如何集成和使用表单设计器
"""

import sys
import json
from PySide2.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QDialog, QTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter, QListWidget, QListWidgetItem,
    QGroupBox, QScrollArea, QFormLayout, QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox
)
from PySide2.QtCore import Qt, Signal

# 导入表单设计器
from form_designer import (
    FormDesignerWindow, FieldType, WidgetConfig, DataSourceType,
    BaseFormWidget
)


class QueryConditionBuilder(QMainWindow):
    """
    查询条件构建器 - 集成表单设计器的实际应用示例
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("动态查询条件构建器")
        self.setGeometry(100, 100, 1400, 900)
        
        self._build_ui()
    
    def _build_ui(self):
        """构建界面"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 分割器
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)
        
        # 上部：表单设计器
        self.form_designer = FormDesignerWidget()
        splitter.addWidget(self.form_designer)
        
        # 下部：预览和代码生成
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        
        # 预览区域
        self.preview_group = PreviewWidget()
        bottom_layout.addWidget(self.preview_group)
        
        # 代码生成区域
        self.code_group = CodeGeneratorWidget()
        bottom_layout.addWidget(self.code_group)
        
        splitter.addWidget(bottom_widget)
        splitter.setSizes([500, 300])
        
        # 工具栏
        toolbar = self.addToolBar("工具")
        toolbar.addAction("加载示例", self._load_example)
        toolbar.addAction("生成查询", self._generate_query)
        toolbar.addAction("导出配置", self._export_config)
    
    def _load_example(self):
        """加载示例配置"""
        example_config = [
            {
                "field_type": "text",
                "name": "keyword",
                "label": "关键词搜索",
                "placeholder": "输入搜索关键词",
                "required": False
            },
            {
                "field_type": "select",
                "name": "category",
                "label": "分类筛选",
                "data_source": {
                    "type": "static",
                    "config": {
                        "options": [
                            {"label": "全部", "value": ""},
                            {"label": "技术", "value": "tech"},
                            {"label": "产品", "value": "product"},
                            {"label": "设计", "value": "design"}
                        ]
                    }
                }
            },
            {
                "field_type": "search_select",
                "name": "user_id",
                "label": "选择用户",
                "data_source": {
                    "type": "sql",
                    "config": {
                        "query": "SELECT id as value, username as label FROM users WHERE username LIKE :keyword LIMIT 20"
                    }
                }
            },
            {
                "field_type": "date",
                "name": "start_date",
                "label": "开始日期",
                "required": True
            },
            {
                "field_type": "date",
                "name": "end_date",
                "label": "结束日期"
            },
            {
                "field_type": "multi_select",
                "name": "status",
                "label": "状态筛选",
                "data_source": {
                    "type": "static",
                    "config": {
                        "options": [
                            {"label": "待处理", "value": "pending"},
                            {"label": "处理中", "value": "processing"},
                            {"label": "已完成", "value": "completed"},
                            {"label": "已取消", "value": "cancelled"}
                        ]
                    }
                }
            },
            {
                "field_type": "number",
                "name": "min_amount",
                "label": "最小金额"
            },
            {
                "field_type": "number",
                "name": "max_amount",
                "label": "最大金额"
            }
        ]
        
        self.form_designer.load_configs(example_config)
        QMessageBox.information(self, "提示", "示例配置已加载")
    
    def _generate_query(self):
        """生成查询条件和代码"""
        configs = self.form_designer.get_all_configs()
        
        if not configs:
            QMessageBox.warning(self, "警告", "请先添加查询条件")
            return
        
        # 更新预览
        self.preview_group.set_conditions(configs)
        
        # 生成代码
        code = self._generate_sql_code(configs)
        self.code_group.set_code(code)
    
    def _generate_sql_code(self, configs: list) -> str:
        """生成SQL查询代码"""
        code_lines = ["# 动态查询生成示例", ""]
        code_lines.append("def build_query(params):")
        code_lines.append('    """构建动态查询"""')
        code_lines.append('    sql = "SELECT * FROM table WHERE 1=1"')
        code_lines.append('    conditions = []')
        code_lines.append('    values = {}')
        code_lines.append('')
        
        for config in configs:
            name = config.get("name", "")
            field_type = config.get("field_type", "")
            
            if field_type in ("text", "search_select"):
                code_lines.append(f'    # {config.get("label", "")}')
                code_lines.append(f'    if params.get("{name}"):')
                code_lines.append(f'        conditions.append(f"{name} LIKE %{{{name}}}%")')
                code_lines.append(f'        values["{name}"] = params["{name}"]')
                code_lines.append('')
            
            elif field_type == "select":
                code_lines.append(f'    # {config.get("label", "")}')
                code_lines.append(f'    if params.get("{name}"):')
                code_lines.append(f'        conditions.append(f"{name} = %{{{name}}}")')
                code_lines.append(f'        values["{name}"] = params["{name}"]')
                code_lines.append('')
            
            elif field_type == "multi_select":
                code_lines.append(f'    # {config.get("label", "")}')
                code_lines.append(f'    if params.get("{name}"):')
                code_lines.append(f'        items = params["{name}"]')
                code_lines.append(f'        placeholders = ",".join(["%s"] * len(items))')
                code_lines.append(f'        conditions.append(f"{name} IN ({{placeholders}})")')
                code_lines.append(f'        values["{name}"] = items')
                code_lines.append('')
            
            elif field_type == "date":
                code_lines.append(f'    # {config.get("label", "")}')
                code_lines.append(f'    if params.get("{name}"):')
                code_lines.append(f'        conditions.append(f"{name} = %{{{name}}}")')
                code_lines.append(f'        values["{name}"] = params["{name}"]')
                code_lines.append('')
            
            elif field_type == "number":
                code_lines.append(f'    # {config.get("label", "")}')
                code_lines.append(f'    if params.get("{name}") is not None:')
                code_lines.append(f'        conditions.append(f"{name} = %{{{name}}}")')
                code_lines.append(f'        values["{name}"] = params["{name}"]')
                code_lines.append('')
        
        code_lines.append('    if conditions:')
        code_lines.append('        sql += " AND " + " AND ".join(conditions)')
        code_lines.append('    return sql, values')
        code_lines.append('')
        
        return "\n".join(code_lines)
    
    def _export_config(self):
        """导出配置"""
        configs = self.form_designer.get_all_configs()
        if not configs:
            QMessageBox.warning(self, "警告", "没有可导出的配置")
            return
        
        # 这里可以添加导出到文件的逻辑
        text = json.dumps(configs, indent=2, ensure_ascii=False)
        dialog = ExportDialog(text, self)
        dialog.exec_()


class FormDesignerWidget(QWidget):
    """
    封装后的表单设计器组件
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
    
    def _build_ui(self):
        """构建界面"""
        from form_designer import (
            ToolboxWidget, CanvasWidget, PropertyPanelWidget
        )
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # 工具箱
        self.toolbox = ToolboxWidget()
        splitter.addWidget(self.toolbox)
        
        # 画布
        self.canvas = CanvasWidget()
        self.canvas.widget_selected.connect(self._on_widget_selected)
        splitter.addWidget(self.canvas)
        
        # 属性面板
        self.property_panel = PropertyPanelWidget()
        splitter.addWidget(self.property_panel)
        
        splitter.setSizes([180, 600, 250])
    
    def _on_widget_selected(self, widget):
        """控件被选中"""
        self.property_panel.set_widget(widget)
    
    def load_configs(self, configs: list):
        """加载配置"""
        self.canvas.load_configs(configs)
    
    def get_all_configs(self) -> list:
        """获取所有配置"""
        return self.canvas.get_all_configs()


class PreviewWidget(QGroupBox):
    """
    预览控件 - 显示生成的查询条件效果
    """
    
    def __init__(self, parent=None):
        super().__init__("查询条件预览", parent)
        self._build_ui()
    
    def _build_ui(self):
        """构建界面"""
        layout = QVBoxLayout(self)
        
        # 表单区域
        self.form_widget = QWidget()
        self.form_layout = QVBoxLayout(self.form_widget)
        self.form_layout.setAlignment(Qt.AlignTop)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.form_widget)
        layout.addWidget(scroll)
        
        # 获取值按钮
        get_btn = QPushButton("获取查询参数")
        get_btn.clicked.connect(self._get_values)
        layout.addWidget(get_btn)
        
        self.value_widgets = {}
    
    def set_conditions(self, configs: list):
        """设置查询条件"""
        # 清除旧内容
        while self.form_layout.count() > 0:
            item = self.form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.value_widgets.clear()
        
        # 创建表单字段
        form = QWidget()
        form_layout = QFormLayout(form)
        
        for config in configs:
            field_type = config.get("field_type", "")
            label = config.get("label", "")
            name = config.get("name", "")
            
            if field_type in ("text", "search_select"):
                widget = QLineEdit()
                widget.setPlaceholderText(config.get("placeholder", ""))
            
            elif field_type in ("select", "multi_select"):
                widget = QComboBox() if field_type == "select" else QListWidget()
                if field_type == "multi_select":
                    widget.setSelectionMode(QListWidget.MultiSelection)
                
                # 加载选项
                options = config.get("data_source", {}).get("config", {}).get("options", [])
                if isinstance(widget, QComboBox):
                    for opt in options:
                        widget.addItem(opt.get("label", ""), opt.get("value"))
                else:
                    for opt in options:
                        item = QListWidgetItem(opt.get("label", ""))
                        item.setData(Qt.UserRole, opt.get("value"))
                        widget.addItem(item)
            
            elif field_type == "date":
                widget = QDateEdit()
                widget.setCalendarPopup(True)
            
            elif field_type == "number":
                widget = QDoubleSpinBox()
                widget.setRange(-999999999, 999999999)
            
            else:
                widget = QLineEdit()
            
            self.value_widgets[name] = (widget, config)
            
            # 显示标签
            display_label = label
            if config.get("required"):
                display_label += " *"
            
            form_layout.addRow(display_label, widget)
        
        self.form_layout.addWidget(form)
        self.form_layout.addStretch()
    
    def _get_values(self):
        """获取所有值"""
        values = {}
        for name, (widget, config) in self.value_widgets.items():
            field_type = config.get("field_type", "")
            
            if isinstance(widget, QLineEdit):
                values[name] = widget.text()
            elif isinstance(widget, QComboBox):
                values[name] = widget.currentData()
            elif isinstance(widget, QListWidget):
                values[name] = [item.data(Qt.UserRole) for item in widget.selectedItems()]
            elif isinstance(widget, QDateEdit):
                values[name] = widget.date().toString("yyyy-MM-dd")
            elif isinstance(widget, QDoubleSpinBox):
                values[name] = widget.value()
        
        # 显示结果
        dialog = QDialog(self)
        dialog.setWindowTitle("查询参数")
        dialog.resize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(json.dumps(values, indent=2, ensure_ascii=False))
        layout.addWidget(text_edit)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_()


class CodeGeneratorWidget(QGroupBox):
    """
    代码生成器 - 显示生成的查询代码
    """
    
    def __init__(self, parent=None):
        super().__init__("生成的代码", parent)
        self._build_ui()
    
    def _build_ui(self):
        """构建界面"""
        layout = QVBoxLayout(self)
        
        self.code_edit = QTextEdit()
        self.code_edit.setReadOnly(True)
        self.code_edit.setFontFamily("Consolas")
        layout.addWidget(self.code_edit)
        
        copy_btn = QPushButton("复制代码")
        copy_btn.clicked.connect(self._copy_code)
        layout.addWidget(copy_btn)
    
    def set_code(self, code: str):
        """设置代码"""
        self.code_edit.setPlainText(code)
    
    def _copy_code(self):
        """复制代码到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.code_edit.toPlainText())
        QMessageBox.information(self, "提示", "代码已复制到剪贴板")


class ExportDialog(QDialog):
    """
    导出配置对话框
    """
    
    def __init__(self, config_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导出配置")
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(config_text)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        btn_box = QPushButton("关闭")
        btn_box.clicked.connect(self.accept)
        layout.addWidget(btn_box)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置样式
    app.setStyle("Fusion")
    
    window = QueryConditionBuilder()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
