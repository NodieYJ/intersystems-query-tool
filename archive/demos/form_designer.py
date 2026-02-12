#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
表单设计器 - 完整的可视化查询条件配置器
支持拖放、属性配置、下拉/搜索选择等高级功能
"""

import sys
import json
import copy
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from PySide2.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QListWidget, QListWidgetItem,
    QTreeWidget, QTreeWidgetItem, QTabWidget, QGroupBox, QScrollArea,
    QFrame, QSplitter, QMenu, QAction, QMessageBox, QFileDialog,
    QCheckBox, QRadioButton, QButtonGroup, QSpinBox, QDoubleSpinBox,
    QDateEdit, QDateTimeEdit, QTimeEdit, QTextEdit, QPlainTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QToolBar, QStatusBar,
    QGraphicsView, QGraphicsScene, QGraphicsProxyWidget, QGraphicsItem,
    QSizePolicy, QInputDialog, QDialog, QDialogButtonBox, QFormLayout,
    QGridLayout, QStackedWidget, QSlider, QProgressBar, QSpacerItem
)
from PySide2.QtCore import (
    Qt, QObject, Signal, Slot, QSize, QPoint, QRect, QMimeData, QDataStream,
    QByteArray, QIODevice, QEvent
)
from PySide2.QtGui import (
    QDrag, QDropEvent, QMouseEvent, QPainter, QColor, QPen, QBrush,
    QFont, QIcon, QCursor, QKeySequence, QPalette
)


# ============================================================================
# 数据模型定义
# ============================================================================

class FieldType(Enum):
    """字段类型枚举"""
    TEXT = "text"           # 文本输入
    NUMBER = "number"       # 数字输入
    DATE = "date"           # 日期选择
    DATETIME = "datetime"   # 日期时间选择
    SELECT = "select"       # 下拉选择
    MULTI_SELECT = "multi_select"  # 多选下拉
    SEARCH_SELECT = "search_select"  # 搜索选择
    CHECKBOX = "checkbox"   # 复选框
    RADIO = "radio"         # 单选按钮
    BUTTON = "button"       # 按钮
    LABEL = "label"         # 标签


class DataSourceType(Enum):
    """数据源类型"""
    STATIC = "static"       # 静态数据
    SQL = "sql"             # SQL查询
    API = "api"             # API调用
    FUNCTION = "function"   # 函数调用


class WidgetConfig:
    """控件配置类"""
    
    def __init__(self, field_type: FieldType, name: str = ""):
        self.field_type = field_type
        self.name = name or f"field_{id(self)}"
        self.label = "新字段"
        self.default_value = None
        self.required = False
        self.placeholder = ""
        self.validation_rules = {}
        
        # 数据源配置（用于下拉、搜索等）
        self.data_source = {
            "type": DataSourceType.STATIC.value,
            "config": {}
        }
        
        # 样式配置 - 高度自适应，不设置固定高度
        self.style = {
            "width": 220,
            "font_size": 12,
            "color": "#000000",
            "background_color": "#FFFFFF"
        }
        
        # 事件配置
        self.events = {
            "on_change": None,
            "on_click": None,
            "on_focus": None
        }
        
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "field_type": self.field_type.value,
            "name": self.name,
            "label": self.label,
            "default_value": self.default_value,
            "required": self.required,
            "placeholder": self.placeholder,
            "validation_rules": self.validation_rules,
            "data_source": self.data_source,
            "style": self.style,
            "events": self.events
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WidgetConfig':
        """从字典创建"""
        config = cls(FieldType(data.get("field_type", "text")))
        config.name = data.get("name", "")
        config.label = data.get("label", "")
        config.default_value = data.get("default_value")
        config.required = data.get("required", False)
        config.placeholder = data.get("placeholder", "")
        config.validation_rules = data.get("validation_rules", {})
        config.data_source = data.get("data_source", {})
        config.style = data.get("style", {})
        config.events = data.get("events", {})
        return config


# ============================================================================
# 自定义表单控件
# ============================================================================

class BaseFormWidget(QFrame):
    """表单控件基类 - 支持画布内自由拖动"""
    
    # 信号定义
    selected = Signal(object)  # 控件被选中
    config_changed = Signal(object)  # 配置变更
    deleted = Signal(object)  # 控件被删除
    moved = Signal(object, QPoint)  # 控件移动（控件，新位置）
    
    def __init__(self, config: WidgetConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.is_selected = False
        self.drag_start_pos = None
        self.is_canvas_dragging = False
        self.canvas_drag_start_pos = None
        self.canvas_start_pos = None
        
        # 画布引用（由画布设置）
        self.canvas = None
        self.enable_canvas_drag = False
        
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.setLineWidth(1)
        self.setMinimumSize(100, 30)
        self.setCursor(Qt.OpenHandCursor)
        
        # 启用鼠标跟踪
        self.setMouseTracking(True)
        
        self._build_ui()
        self._apply_config()
    
    def _build_ui(self):
        """构建UI - 子类重写"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(2)
        
        # 标签
        self.label_widget = QLabel(self.config.label)
        self.label_widget.setStyleSheet("font-weight: bold;")
        self.main_layout.addWidget(self.label_widget)
        
        # 内容区域（子类填充）
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.content_widget)
    
    def _apply_config(self):
        """应用配置到UI - 高度自适应内容"""
        self.label_widget.setText(self.config.label)
        if self.config.required:
            self.label_widget.setText(f"{self.config.label} *")
        
        # 应用样式 - 宽度固定，高度自适应
        style = self.config.style
        width = style.get("width", 200)
        # 设置最小宽度和高度，让控件自适应内容
        self.setMinimumSize(width, 40)
        self.setMaximumWidth(width)
        # 高度根据内容自动调整，不设置固定高度
    
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下"""
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            self.set_selected(True)
            self.selected.emit(self)
            
            # 记录画布拖动的起始位置
            if self.enable_canvas_drag and self.canvas:
                self.is_canvas_dragging = True
                self.canvas_drag_start_pos = event.globalPos()
                self.canvas_start_pos = self.pos()
                
                # 标记正在拖动，用于画布识别
                self.is_dragging = True
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动 - 支持画布内拖动和跨画布拖放"""
        if not (event.buttons() & Qt.LeftButton):
            return
        
        if self.drag_start_pos is None:
            return
        
        # 计算移动距离
        distance = (event.pos() - self.drag_start_pos).manhattanLength()
        if distance < QApplication.startDragDistance():
            return
        
        # 如果在画布内且启用了画布拖动，执行画布内拖动
        if self.enable_canvas_drag and self.is_canvas_dragging and self.canvas:
            # 计算新位置
            delta = event.globalPos() - self.canvas_drag_start_pos
            new_pos = self.canvas_start_pos + QPoint(delta.x(), delta.y())
            
            # 限制在画布范围内
            new_pos.setX(max(0, min(new_pos.x(), self.canvas.container.width() - self.width())))
            new_pos.setY(max(0, min(new_pos.y(), self.canvas.container.height() - self.height())))
            
            self.move(new_pos)
            self.moved.emit(self, new_pos)
            
            # 更新对齐辅助线
            if hasattr(self.canvas, '_update_guide_lines'):
                self.canvas._update_guide_lines(new_pos)
                self.canvas.update()
        else:
            # 跨画布拖放（原来的逻辑）
            self._start_drag_to_other_canvas()
    
    def _start_drag_to_other_canvas(self):
        """开始拖放到其他画布"""
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # 序列化配置数据
        config_data = json.dumps(self.config.to_dict())
        mime_data.setText(config_data)
        mime_data.setData("application/x-formwidget", QByteArray())
        
        drag.setMimeData(mime_data)
        
        # 创建拖动时的缩略图
        pixmap = self.grab()
        drag.setPixmap(pixmap.scaled(100, 50, Qt.KeepAspectRatio))
        drag.setHotSpot(QPoint(50, 25))
        
        drag.exec_(Qt.MoveAction)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放"""
        self.setCursor(Qt.OpenHandCursor)
        
        # 结束画布拖动
        if self.is_canvas_dragging:
            self.is_canvas_dragging = False
            self.is_dragging = False
            
            # 通知画布更新
            if self.canvas:
                self.canvas.guides_visible = False
                self.canvas.guide_lines = []
                self.canvas.update()
        
        super().mouseReleaseEvent(event)
    
    def set_selected(self, selected: bool):
        """设置选中状态"""
        self.is_selected = selected
        if selected:
            self.setStyleSheet("""
                BaseFormWidget {
                    border: 2px solid #1E90FF;
                    background-color: #E6F3FF;
                }
            """)
            # 提升层级
            self.raise_()
        else:
            self.setStyleSheet("""
                BaseFormWidget {
                    border: 1px solid #CCCCCC;
                    background-color: #FFFFFF;
                }
            """)
    
    def update_config(self, config: WidgetConfig):
        """更新配置"""
        self.config = config
        self._apply_config()
        self.config_changed.emit(self)
    
    def get_value(self):
        """获取当前值 - 子类重写"""
        return None
    
    def set_value(self, value):
        """设置值 - 子类重写"""
        pass
    
    def keyPressEvent(self, event):
        """键盘事件 - 支持删除和方向键移动"""
        if event.key() == Qt.Key_Delete and self.is_selected:
            self.deleted.emit(self)
        elif self.is_selected and self.canvas and event.key() in (
            Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down
        ):
            # 方向键微调位置
            step = 10
            if event.modifiers() & Qt.ShiftModifier:
                step = 1  # Shift + 方向键 = 微调
            
            pos = self.pos()
            if event.key() == Qt.Key_Left:
                pos.setX(pos.x() - step)
            elif event.key() == Qt.Key_Right:
                pos.setX(pos.x() + step)
            elif event.key() == Qt.Key_Up:
                pos.setY(pos.y() - step)
            elif event.key() == Qt.Key_Down:
                pos.setY(pos.y() + step)
            
            self.move(pos)
            self.moved.emit(self, pos)
            self.config.style["x"] = pos.x()
            self.config.style["y"] = pos.y()
        
        super().keyPressEvent(event)


class TextInputWidget(BaseFormWidget):
    """文本输入控件"""
    
    def _build_ui(self):
        super()._build_ui()
        self.input = QLineEdit()
        self.input.setPlaceholderText(self.config.placeholder)
        self.content_layout.addWidget(self.input)
    
    def _apply_config(self):
        super()._apply_config()
        self.input.setPlaceholderText(self.config.placeholder)
        if self.config.default_value:
            self.input.setText(str(self.config.default_value))
    
    def get_value(self):
        return self.input.text()
    
    def set_value(self, value):
        self.input.setText(str(value) if value else "")


class NumberInputWidget(BaseFormWidget):
    """数字输入控件"""
    
    def _build_ui(self):
        super()._build_ui()
        self.input = QDoubleSpinBox()
        self.input.setRange(-999999999, 999999999)
        self.input.setDecimals(2)
        self.content_layout.addWidget(self.input)
    
    def _apply_config(self):
        super()._apply_config()
        if self.config.default_value is not None:
            self.input.setValue(float(self.config.default_value))
    
    def get_value(self):
        return self.input.value()
    
    def set_value(self, value):
        self.input.setValue(float(value) if value else 0)


class DateInputWidget(BaseFormWidget):
    """日期输入控件"""
    
    def _build_ui(self):
        super()._build_ui()
        self.input = QDateEdit()
        self.input.setCalendarPopup(True)
        self.content_layout.addWidget(self.input)
    
    def get_value(self):
        return self.input.date().toString("yyyy-MM-dd")
    
    def set_value(self, value):
        if value:
            self.input.setDate(QDate.fromString(str(value), "yyyy-MM-dd"))


class SelectWidget(BaseFormWidget):
    """下拉选择控件（支持单选/多选）"""
    
    def _build_ui(self):
        super()._build_ui()
        
        # 根据配置决定使用单选还是多选
        if self.config.field_type == FieldType.MULTI_SELECT:
            self.input = QListWidget()
            self.input.setSelectionMode(QListWidget.MultiSelection)
            self.input.setMaximumHeight(100)
        else:
            self.input = QComboBox()
        
        self.content_layout.addWidget(self.input)
        
        # 加载数据
        self._load_data()
    
    def _load_data(self):
        """加载选项数据"""
        data_source = self.config.data_source
        source_type = data_source.get("type", DataSourceType.STATIC.value)
        
        if source_type == DataSourceType.STATIC.value:
            # 静态数据
            options = data_source.get("config", {}).get("options", [])
            self._set_options(options)
        
        elif source_type == DataSourceType.SQL.value:
            # SQL查询 - 模拟异步加载
            self._set_options([{"label": "加载中...", "value": ""}])
            # 实际项目中使用线程加载
        
        elif source_type == DataSourceType.API.value:
            # API调用
            self._set_options([{"label": "加载中...", "value": ""}])
    
    def _set_options(self, options: List[dict]):
        """设置选项"""
        if isinstance(self.input, QComboBox):
            self.input.clear()
            for opt in options:
                label = opt.get("label", opt.get("value", ""))
                value = opt.get("value", "")
                self.input.addItem(label, value)
        else:  # QListWidget
            self.input.clear()
            for opt in options:
                label = opt.get("label", opt.get("value", ""))
                item = QListWidgetItem(label)
                item.setData(Qt.UserRole, opt.get("value", ""))
                self.input.addItem(item)
    
    def get_value(self):
        """获取选中值"""
        if isinstance(self.input, QComboBox):
            return self.input.currentData()
        else:
            # 多选模式
            selected = []
            for item in self.input.selectedItems():
                selected.append(item.data(Qt.UserRole))
            return selected
    
    def set_value(self, value):
        """设置选中值"""
        if isinstance(self.input, QComboBox):
            index = self.input.findData(value)
            if index >= 0:
                self.input.setCurrentIndex(index)
        else:
            # 多选模式
            self.input.clearSelection()
            if not isinstance(value, list):
                value = [value]
            for i in range(self.input.count()):
                item = self.input.item(i)
                if item.data(Qt.UserRole) in value:
                    item.setSelected(True)


class SearchSelectWidget(BaseFormWidget):
    """搜索选择控件（带搜索功能的下拉选择）"""
    
    def _build_ui(self):
        super()._build_ui()
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 搜索输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键字搜索...")
        self.search_input.textChanged.connect(self._on_search)
        layout.addWidget(self.search_input)
        
        # 选择按钮
        self.select_btn = QPushButton("▼")
        self.select_btn.setFixedWidth(30)
        self.select_btn.clicked.connect(self._show_dropdown)
        layout.addWidget(self.select_btn)
        
        self.content_layout.addLayout(layout)
        
        # 结果显示标签
        self.result_label = QLabel("未选择")
        self.result_label.setStyleSheet("color: #666666; padding: 2px;")
        self.content_layout.addWidget(self.result_label)
        
        # 下拉列表（使用独立的弹出窗口）
        self.dropdown = SearchDropdownWidget(self)
        self.dropdown.item_selected.connect(self._on_item_selected)
        
        # 数据缓存
        self.all_options = []
        self.selected_items = []
    
    def _on_search(self, text):
        """搜索文本变更"""
        if len(text) >= 2:  # 至少2个字符才搜索
            self._perform_search(text)
    
    def _perform_search(self, keyword: str):
        """执行搜索"""
        data_source = self.config.data_source
        source_type = data_source.get("type", DataSourceType.STATIC.value)
        
        if source_type == DataSourceType.STATIC.value:
            # 静态数据过滤
            options = data_source.get("config", {}).get("options", [])
            filtered = [
                opt for opt in options 
                if keyword.lower() in opt.get("label", "").lower()
            ]
            self._show_dropdown_results(filtered)
        
        else:
            # SQL/API 模式 - 执行查询
            query_template = data_source.get("config", {}).get("query", "")
            # 模拟搜索，实际项目中替换为真实查询
            self._show_dropdown_results([
                {"label": f"结果1 - {keyword}", "value": "1"},
                {"label": f"结果2 - {keyword}", "value": "2"},
            ])
    
    def _show_dropdown(self):
        """显示下拉列表"""
        pos = self.search_input.mapToGlobal(
            QPoint(0, self.search_input.height())
        )
        self.dropdown.move(pos)
        self.dropdown.resize(self.search_input.width() + 30, 200)
        
        # 加载初始数据
        if not self.all_options:
            self._load_initial_data()
        
        self.dropdown.show()
    
    def _show_dropdown_results(self, results: List[dict]):
        """显示搜索结果"""
        self.dropdown.set_items(results, self.config.field_type == FieldType.MULTI_SELECT)
        self.dropdown.show()
    
    def _load_initial_data(self):
        """加载初始数据"""
        data_source = self.config.data_source
        # 加载逻辑与 SelectWidget 类似
        self.all_options = [
            {"label": "选项1", "value": "1"},
            {"label": "选项2", "value": "2"},
        ]
    
    def _on_item_selected(self, items: List[dict]):
        """选中项变更"""
        self.selected_items = items
        if items:
            if self.config.field_type == FieldType.MULTI_SELECT:
                labels = [item.get("label", "") for item in items]
                self.result_label.setText(f"已选择: {', '.join(labels)}")
            else:
                self.result_label.setText(f"已选择: {items[0].get('label', '')}")
        else:
            self.result_label.setText("未选择")
        
        self.config_changed.emit(self)
    
    def get_value(self):
        """获取选中值"""
        if self.config.field_type == FieldType.MULTI_SELECT:
            return [item.get("value") for item in self.selected_items]
        else:
            return self.selected_items[0].get("value") if self.selected_items else None
    
    def set_value(self, value):
        """设置值"""
        # 根据value查找对应选项并选中
        pass


class SearchDropdownWidget(QWidget):
    """搜索下拉弹出窗口"""
    
    item_selected = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Popup)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        
        # 列表控件
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_item_click)
        layout.addWidget(self.list_widget)
        
        # 确定按钮（多选模式显示）
        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self._on_ok)
        layout.addWidget(self.ok_btn)
        
        self.is_multi = False
        self.selected_items = []
    
    def set_items(self, items: List[dict], is_multi: bool = False):
        """设置列表项"""
        self.is_multi = is_multi
        self.list_widget.clear()
        self.selected_items = []
        
        for item in items:
            list_item = QListWidgetItem(item.get("label", ""))
            list_item.setData(Qt.UserRole, item)
            self.list_widget.addItem(list_item)
        
        self.ok_btn.setVisible(is_multi)
        
        if is_multi:
            self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        else:
            self.list_widget.setSelectionMode(QListWidget.SingleSelection)
    
    def _on_item_click(self, item):
        """项点击"""
        if not self.is_multi:
            data = item.data(Qt.UserRole)
            self.item_selected.emit([data])
            self.hide()
    
    def _on_ok(self):
        """确定按钮"""
        selected = []
        for item in self.list_widget.selectedItems():
            selected.append(item.data(Qt.UserRole))
        self.item_selected.emit(selected)
        self.hide()


class CheckboxWidget(BaseFormWidget):
    """复选框控件"""
    
    def _build_ui(self):
        super()._build_ui()
        self.input = QCheckBox(self.config.label)
        self.content_layout.addWidget(self.input)
        self.label_widget.hide()  # 隐藏标签，因为复选框自带文本
    
    def get_value(self):
        return self.input.isChecked()
    
    def set_value(self, value):
        self.input.setChecked(bool(value))


class RadioWidget(BaseFormWidget):
    """单选按钮组控件"""
    
    def _build_ui(self):
        super()._build_ui()
        
        self.button_group = QButtonGroup(self)
        
        # 从数据源加载选项
        options = self.config.data_source.get("config", {}).get("options", [])
        
        layout = QHBoxLayout()
        for opt in options:
            radio = QRadioButton(opt.get("label", ""))
            radio.setProperty("value", opt.get("value"))
            self.button_group.addButton(radio)
            layout.addWidget(radio)
        
        self.content_layout.addLayout(layout)
    
    def get_value(self):
        checked = self.button_group.checkedButton()
        return checked.property("value") if checked else None
    
    def set_value(self, value):
        for button in self.button_group.buttons():
            if button.property("value") == value:
                button.setChecked(True)
                break


class ButtonWidget(BaseFormWidget):
    """按钮控件"""
    
    clicked = Signal()
    
    def _build_ui(self):
        super()._build_ui()
        self.label_widget.hide()
        
        self.input = QPushButton(self.config.label)
        self.input.clicked.connect(self.clicked.emit)
        self.content_layout.addWidget(self.input)
    
    def _apply_config(self):
        super()._apply_config()
        self.input.setText(self.config.label)


# ============================================================================
# 工具箱组件
# ============================================================================

class ToolboxWidget(QGroupBox):
    """左侧工具箱"""
    
    drag_started = Signal(object, QMimeData)
    
    def __init__(self, parent=None):
        super().__init__("控件工具箱", parent)
        self.setMinimumWidth(150)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # 控件类别
        categories = {
            "基础控件": [
                ("文本输入", FieldType.TEXT),
                ("数字输入", FieldType.NUMBER),
                ("日期选择", FieldType.DATE),
                ("标签", FieldType.LABEL),
            ],
            "选择控件": [
                ("下拉单选", FieldType.SELECT),
                ("下拉多选", FieldType.MULTI_SELECT),
                ("搜索单选", FieldType.SEARCH_SELECT),
                ("复选框", FieldType.CHECKBOX),
                ("单选组", FieldType.RADIO),
            ],
            "操作控件": [
                ("按钮", FieldType.BUTTON),
            ]
        }
        
        for category_name, items in categories.items():
            group = QGroupBox(category_name)
            group_layout = QVBoxLayout(group)
            group_layout.setSpacing(2)
            
            for label, field_type in items:
                btn = QPushButton(label)
                btn.setProperty("field_type", field_type)
                btn.setCursor(Qt.OpenHandCursor)
                btn.mousePressEvent = lambda e, b=btn, ft=field_type, lb=label: self._on_tool_mouse_press(e, b, ft, lb)
                group_layout.addWidget(btn)
            
            layout.addWidget(group)
        
        layout.addStretch()
    
    def _on_tool_mouse_press(self, event: QMouseEvent, btn: QPushButton, field_type: FieldType, label: str):
        """工具按钮鼠标按下 - 开始拖放"""
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            
            # 创建默认配置
            config = WidgetConfig(field_type, name=f"{field_type.value}_{id(self)}")
            config.label = label
            
            # 根据不同类型设置默认数据源
            if field_type in (FieldType.SELECT, FieldType.MULTI_SELECT, FieldType.SEARCH_SELECT):
                config.data_source = {
                    "type": DataSourceType.STATIC.value,
                    "config": {
                        "options": [
                            {"label": "选项1", "value": "1"},
                            {"label": "选项2", "value": "2"},
                        ]
                    }
                }
            
            mime_data.setText(json.dumps(config.to_dict()))
            mime_data.setData("application/x-newwidget", QByteArray())
            
            drag.setMimeData(mime_data)
            
            # 创建拖动缩略图
            pixmap = btn.grab()
            drag.setPixmap(pixmap.scaled(100, 30, Qt.KeepAspectRatio))
            
            drag.exec_(Qt.CopyAction)


# ============================================================================
# 画布组件 - 支持自由拖放定位
# ============================================================================

class CanvasWidget(QFrame):
    """设计画布 - 支持控件自由拖放定位"""
    
    widget_selected = Signal(object)
    widget_dropped = Signal(object)
    widget_moved = Signal(object, QPoint)  # 控件移动信号
    layout_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Sunken | QFrame.StyledPanel)
        self.setMinimumSize(600, 400)
        
        # 不使用布局管理器，使用绝对定位
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        
        # 创建内部容器用于放置控件
        self.container = QWidget(self)
        self.container.setGeometry(0, 0, 2000, 2000)  # 足够大的画布区域
        self.container.setStyleSheet("background-color: #F5F5F5;")
        
        # 网格设置
        self.grid_size = 10  # 网格大小
        self.show_grid = True  # 是否显示网格
        self.snap_to_grid = True  # 是否吸附到网格
        
        # 控件列表
        self.widgets: List[BaseFormWidget] = []
        self.selected_widget: Optional[BaseFormWidget] = None
        self.dragging_widget: Optional[BaseFormWidget] = None
        self.drag_start_pos = None
        self.widget_start_pos = None
        
        # 占位符文本
        self.placeholder = QLabel("从左侧拖放控件到此处\n支持自由拖动定位", self.container)
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet("""
            color: #999999; 
            padding: 50px;
            font-size: 14px;
            border: 2px dashed #CCCCCC;
            border-radius: 10px;
            background-color: #FAFAFA;
        """)
        self.placeholder.setGeometry(200, 150, 300, 150)
        
        # 对齐辅助线
        self.guides_visible = False
        self.guide_lines = []  # [(x1, y1, x2, y2), ...]
        
        # 多选支持
        self.selected_widgets: List[BaseFormWidget] = []
        self.selection_rect = None
        self.is_selecting = False
        self.selection_start = None
    
    def paintEvent(self, event):
        """绘制网格和辅助线"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        
        # 绘制网格
        if self.show_grid:
            self._draw_grid(painter)
        
        # 绘制对齐辅助线
        if self.guides_visible:
            self._draw_guides(painter)
        
        # 绘制选择框
        if self.is_selecting and self.selection_rect:
            self._draw_selection_rect(painter)
    
    def _draw_grid(self, painter: QPainter):
        """绘制网格背景"""
        pen = QPen(QColor(200, 200, 200))
        pen.setWidth(1)
        painter.setPen(pen)
        
        # 获取可见区域
        visible_rect = self.rect()
        
        # 绘制垂直线
        for x in range(0, visible_rect.width(), self.grid_size):
            painter.drawLine(x, 0, x, visible_rect.height())
        
        # 绘制水平线
        for y in range(0, visible_rect.height(), self.grid_size):
            painter.drawLine(0, y, visible_rect.width(), y)
        
        # 绘制主要网格线（每5格）
        pen = QPen(QColor(180, 180, 180))
        pen.setWidth(1)
        painter.setPen(pen)
        
        for x in range(0, visible_rect.width(), self.grid_size * 5):
            painter.drawLine(x, 0, x, visible_rect.height())
        
        for y in range(0, visible_rect.height(), self.grid_size * 5):
            painter.drawLine(0, y, visible_rect.width(), y)
    
    def _draw_guides(self, painter: QPainter):
        """绘制对齐辅助线"""
        pen = QPen(QColor(255, 100, 100))
        pen.setWidth(1)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        
        for line in self.guide_lines:
            painter.drawLine(line[0], line[1], line[2], line[3])
    
    def _draw_selection_rect(self, painter: QPainter):
        """绘制选择框"""
        pen = QPen(QColor(30, 144, 255))
        pen.setWidth(1)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        
        brush = QBrush(QColor(30, 144, 255, 50))
        painter.setBrush(brush)
        
        painter.drawRect(self.selection_rect)
    
    def dragEnterEvent(self, event: QDropEvent):
        """拖放进入"""
        if event.mimeData().hasFormat("application/x-newwidget") or \
           event.mimeData().hasFormat("application/x-formwidget"):
            event.acceptProposedAction()
            self.guides_visible = True
            self.update()
    
    def dragMoveEvent(self, event: QDropEvent):
        """拖放移动"""
        event.acceptProposedAction()
        
        # 更新对齐辅助线
        if event.mimeData().hasFormat("application/x-formwidget"):
            pos = event.pos()
            self._update_guide_lines(pos)
            self.update()
    
    def dragLeaveEvent(self, event):
        """拖放离开"""
        self.guides_visible = False
        self.guide_lines = []
        self.update()
    
    def dropEvent(self, event: QDropEvent):
        """拖放放下"""
        mime_data = event.mimeData()
        drop_pos = event.pos()
        
        # 隐藏占位符
        self.placeholder.hide()
        
        # 吸附到网格
        if self.snap_to_grid:
            drop_pos = self._snap_to_grid(drop_pos)
        
        if mime_data.hasFormat("application/x-newwidget"):
            # 从工具箱拖入新控件
            config_data = json.loads(mime_data.text())
            config = WidgetConfig.from_dict(config_data)
            
            # 保存位置信息到配置
            config.style["x"] = drop_pos.x()
            config.style["y"] = drop_pos.y()
            
            widget = self.create_form_widget(config)
            widget.setParent(self.container)
            widget.move(drop_pos)
            widget.show()
            
            self.widgets.append(widget)
            self.select_widget(widget)
            self.widget_dropped.emit(widget)
            self.layout_changed.emit()
        
        elif mime_data.hasFormat("application/x-formwidget"):
            # 移动现有控件到新位置
            for widget in self.widgets:
                if widget.is_dragging:
                    widget.move(drop_pos)
                    widget.is_dragging = False
                    
                    # 更新配置中的位置
                    widget.config.style["x"] = drop_pos.x()
                    widget.config.style["y"] = drop_pos.y()
                    
                    self.widget_moved.emit(widget, drop_pos)
                    break
        
        self.guides_visible = False
        self.guide_lines = []
        self.update()
        event.acceptProposedAction()
    
    def _snap_to_grid(self, pos: QPoint) -> QPoint:
        """将位置吸附到网格"""
        x = round(pos.x() / self.grid_size) * self.grid_size
        y = round(pos.y() / self.grid_size) * self.grid_size
        return QPoint(x, y)
    
    def _update_guide_lines(self, pos: QPoint):
        """更新对齐辅助线"""
        self.guide_lines = []
        threshold = 10  # 对齐阈值
        
        # 获取当前拖动的控件大小（假设）
        widget_width = 200
        widget_height = 60
        
        # 检查与其他控件的对齐
        for widget in self.widgets:
            if widget == self.dragging_widget:
                continue
            
            wx, wy = widget.x(), widget.y()
            ww, wh = widget.width(), widget.height()
            
            # 左对齐
            if abs(pos.x() - wx) < threshold:
                self.guide_lines.append((wx, 0, wx, self.height()))
            
            # 右对齐
            if abs((pos.x() + widget_width) - (wx + ww)) < threshold:
                x = wx + ww - widget_width
                self.guide_lines.append((wx + ww, 0, wx + ww, self.height()))
            
            # 顶部对齐
            if abs(pos.y() - wy) < threshold:
                self.guide_lines.append((0, wy, self.width(), wy))
            
            # 底部对齐
            if abs((pos.y() + widget_height) - (wy + wh)) < threshold:
                self.guide_lines.append((0, wy + wh, self.width(), wy + wh))
            
            # 中心对齐（水平）
            if abs((pos.x() + widget_width/2) - (wx + ww/2)) < threshold:
                cx = int(wx + ww/2)
                self.guide_lines.append((cx, 0, cx, self.height()))
            
            # 中心对齐（垂直）
            if abs((pos.y() + widget_height/2) - (wy + wh/2)) < threshold:
                cy = int(wy + wh/2)
                self.guide_lines.append((0, cy, self.width(), cy))
    
    def create_form_widget(self, config: WidgetConfig) -> BaseFormWidget:
        """根据配置创建表单控件"""
        widget_classes = {
            FieldType.TEXT: TextInputWidget,
            FieldType.NUMBER: NumberInputWidget,
            FieldType.DATE: DateInputWidget,
            FieldType.SELECT: SelectWidget,
            FieldType.MULTI_SELECT: SelectWidget,
            FieldType.SEARCH_SELECT: SearchSelectWidget,
            FieldType.CHECKBOX: CheckboxWidget,
            FieldType.RADIO: RadioWidget,
            FieldType.BUTTON: ButtonWidget,
        }
        
        widget_class = widget_classes.get(config.field_type, TextInputWidget)
        widget = widget_class(config)
        
        # 设置画布引用，用于拖放
        widget.canvas = self
        widget.enable_canvas_drag = True
        
        widget.selected.connect(self._on_widget_selected)
        widget.deleted.connect(self._on_widget_deleted)
        widget.moved.connect(self._on_widget_moved)
        
        return widget
    
    def _on_widget_selected(self, widget: BaseFormWidget):
        """控件被选中"""
        self.select_widget(widget)
    
    def select_widget(self, widget: BaseFormWidget):
        """选中指定控件"""
        # 取消之前的选中
        if self.selected_widget and self.selected_widget != widget:
            self.selected_widget.set_selected(False)
        
        self.selected_widget = widget
        widget.set_selected(True)
        self.widget_selected.emit(widget)
    
    def _on_widget_deleted(self, widget: BaseFormWidget):
        """控件被删除"""
        if widget in self.widgets:
            self.widgets.remove(widget)
            widget.deleteLater()
            self.layout_changed.emit()
        
        if self.selected_widget == widget:
            self.selected_widget = None
        
        # 如果没有控件了，显示占位符
        if not self.widgets:
            self.placeholder.show()
    
    def _on_widget_moved(self, widget: BaseFormWidget, new_pos: QPoint):
        """控件被移动"""
        # 吸附到网格
        if self.snap_to_grid:
            new_pos = self._snap_to_grid(new_pos)
            widget.move(new_pos)
        
        # 更新配置
        widget.config.style["x"] = new_pos.x()
        widget.config.style["y"] = new_pos.y()
        
        self.widget_moved.emit(widget, new_pos)
        self.layout_changed.emit()
    
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下空白区域 - 取消选中或开始框选"""
        if event.button() == Qt.LeftButton:
            # 检查是否点击在控件上
            child = self.childAt(event.pos())
            if not child or child == self.container:
                # 点击空白区域，取消选中
                if self.selected_widget:
                    self.selected_widget.set_selected(False)
                    self.selected_widget = None
                
                # 开始框选
                self.is_selecting = True
                self.selection_start = event.pos()
                self.selection_rect = QRect(event.pos(), QSize(0, 0))
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动 - 更新选择框"""
        if self.is_selecting and event.buttons() & Qt.LeftButton:
            # 更新选择框
            self.selection_rect = QRect(
                self.selection_start,
                event.pos()
            ).normalized()
            self.update()
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放 - 结束框选"""
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            
            # 选中框选区域内的控件
            for widget in self.widgets:
                if self.selection_rect.intersects(widget.geometry()):
                    widget.set_selected(True)
                    if widget not in self.selected_widgets:
                        self.selected_widgets.append(widget)
            
            self.selection_rect = None
            self.update()
        
        super().mouseReleaseEvent(event)
    
    def clear_all(self):
        """清空所有控件"""
        for widget in self.widgets[:]:
            widget.deleteLater()
        self.widgets.clear()
        self.selected_widget = None
        self.placeholder.show()
        self.placeholder.move(200, 150)
        self.layout_changed.emit()
    
    def get_all_configs(self) -> List[dict]:
        """获取所有控件配置（包含位置信息）"""
        configs = []
        for widget in self.widgets:
            config_dict = widget.config.to_dict()
            # 确保位置信息被保存
            config_dict["style"]["x"] = widget.x()
            config_dict["style"]["y"] = widget.y()
            configs.append(config_dict)
        return configs
    
    def load_configs(self, configs: List[dict]):
        """加载配置（恢复位置）"""
        self.clear_all()
        
        for config_data in configs:
            config = WidgetConfig.from_dict(config_data)
            widget = self.create_form_widget(config)
            
            # 恢复位置
            x = config.style.get("x", 10)
            y = config.style.get("y", 10)
            widget.setParent(self.container)
            widget.move(x, y)
            widget.show()
            
            self.widgets.append(widget)
        
        if self.widgets:
            self.placeholder.hide()
        
        self.update()
    
    def set_grid_visible(self, visible: bool):
        """设置网格可见性"""
        self.show_grid = visible
        self.update()
    
    def set_snap_to_grid(self, snap: bool):
        """设置是否吸附到网格"""
        self.snap_to_grid = snap
    
    def align_widgets(self, alignment: str):
        """对齐选中的控件"""
        if not self.selected_widgets:
            return
        
        if alignment == "left":
            min_x = min(w.x() for w in self.selected_widgets)
            for widget in self.selected_widgets:
                widget.move(min_x, widget.y())
        
        elif alignment == "right":
            max_right = max(w.x() + w.width() for w in self.selected_widgets)
            for widget in self.selected_widgets:
                widget.move(max_right - widget.width(), widget.y())
        
        elif alignment == "top":
            min_y = min(w.y() for w in self.selected_widgets)
            for widget in self.selected_widgets:
                widget.move(widget.x(), min_y)
        
        elif alignment == "bottom":
            max_bottom = max(w.y() + w.height() for w in self.selected_widgets)
            for widget in self.selected_widgets:
                widget.move(widget.x(), max_bottom - widget.height())
        
        elif alignment == "hcenter":
            avg_x = sum(w.x() + w.width()/2 for w in self.selected_widgets) / len(self.selected_widgets)
            for widget in self.selected_widgets:
                widget.move(int(avg_x - widget.width()/2), widget.y())
        
        elif alignment == "vcenter":
            avg_y = sum(w.y() + w.height()/2 for w in self.selected_widgets) / len(self.selected_widgets)
            for widget in self.selected_widgets:
                widget.move(widget.x(), int(avg_y - widget.height()/2))
        
        self.layout_changed.emit()
        self.update()


# ============================================================================
# 属性面板组件
# ============================================================================

class PropertyPanelWidget(QGroupBox):
    """右侧属性面板"""
    
    config_updated = Signal(object)
    
    def __init__(self, parent=None):
        super().__init__("属性配置", parent)
        self.setMinimumWidth(250)
        
        self.current_widget = None
        self.current_config = None
        
        self._build_ui()
    
    def _build_ui(self):
        """构建属性面板UI"""
        layout = QVBoxLayout(self)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        layout.addWidget(scroll)
        
        # 内容容器
        self.content_widget = QWidget()
        self.content_layout = QFormLayout(self.content_widget)
        self.content_layout.setSpacing(10)
        scroll.setWidget(self.content_widget)
        
        # 占位提示
        self.placeholder = QLabel("请选择控件以编辑属性")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet("color: #999999; padding: 20px;")
        self.content_layout.addRow(self.placeholder)
    
    def set_widget(self, widget: BaseFormWidget):
        """设置当前编辑的控件"""
        self.current_widget = widget
        self.current_config = copy.deepcopy(widget.config)
        self._rebuild_form()
    
    def _rebuild_form(self):
        """重建属性表单"""
        # 清除旧内容
        while self.content_layout.count() > 0:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.current_config:
            self.placeholder = QLabel("请选择控件以编辑属性")
            self.placeholder.setAlignment(Qt.AlignCenter)
            self.content_layout.addRow(self.placeholder)
            return
        
        config = self.current_config
        
        # 基础属性
        self._add_section_header("基础属性")
        
        self.name_edit = QLineEdit(config.name)
        self.name_edit.textChanged.connect(lambda v: self._update_config("name", v))
        self.content_layout.addRow("字段名:", self.name_edit)
        
        self.label_edit = QLineEdit(config.label)
        self.label_edit.textChanged.connect(lambda v: self._update_config("label", v))
        self.content_layout.addRow("显示标签:", self.label_edit)
        
        self.required_check = QCheckBox()
        self.required_check.setChecked(config.required)
        self.required_check.stateChanged.connect(lambda v: self._update_config("required", bool(v)))
        self.content_layout.addRow("必填:", self.required_check)
        
        self.placeholder_edit = QLineEdit(config.placeholder)
        self.placeholder_edit.textChanged.connect(lambda v: self._update_config("placeholder", v))
        self.content_layout.addRow("占位符:", self.placeholder_edit)
        
        # 数据源配置（针对选择类控件）
        if config.field_type in (FieldType.SELECT, FieldType.MULTI_SELECT, 
                                  FieldType.SEARCH_SELECT, FieldType.RADIO):
            self._add_section_header("数据源配置")
            
            source_type_combo = QComboBox()
            source_type_combo.addItems(["静态数据", "SQL查询", "API调用", "函数调用"])
            source_type_map = {
                DataSourceType.STATIC.value: 0,
                DataSourceType.SQL.value: 1,
                DataSourceType.API.value: 2,
                DataSourceType.FUNCTION.value: 3
            }
            current_type = config.data_source.get("type", DataSourceType.STATIC.value)
            source_type_combo.setCurrentIndex(source_type_map.get(current_type, 0))
            source_type_combo.currentIndexChanged.connect(self._on_source_type_changed)
            self.content_layout.addRow("数据源类型:", source_type_combo)
            
            # 根据类型显示不同配置
            self._build_data_source_config(config.data_source)
        
        # 样式配置
        self._add_section_header("样式配置")
        
        width_spin = QSpinBox()
        width_spin.setRange(100, 500)
        width_spin.setValue(config.style.get("width", 220))
        width_spin.valueChanged.connect(lambda v: self._update_style("width", v))
        self.content_layout.addRow("宽度:", width_spin)
        
        # 高度自适应，不再提供固定高度设置
        auto_height_label = QLabel("高度自适应内容")
        auto_height_label.setStyleSheet("color: #666666; font-style: italic;")
        self.content_layout.addRow("高度:", auto_height_label)
        
        # 应用按钮
        self.content_layout.addRow("", QWidget())  # 空行
        apply_btn = QPushButton("应用更改")
        apply_btn.clicked.connect(self._apply_changes)
        self.content_layout.addRow(apply_btn)
    
    def _add_section_header(self, title: str):
        """添加分组标题"""
        label = QLabel(title)
        label.setStyleSheet("""
            font-weight: bold;
            color: #333333;
            padding-top: 10px;
            border-bottom: 1px solid #CCCCCC;
        """)
        self.content_layout.addRow(label)
    
    def _build_data_source_config(self, data_source: dict):
        """构建数据源配置表单"""
        source_type = data_source.get("type", DataSourceType.STATIC.value)
        config = data_source.get("config", {})
        
        if source_type == DataSourceType.STATIC.value:
            # 静态数据编辑器
            options_text = QTextEdit()
            options = config.get("options", [])
            options_text.setPlainText("\n".join([
                f"{opt.get('label', '')}={opt.get('value', '')}" 
                for opt in options
            ]))
            options_text.setMaximumHeight(100)
            options_text.textChanged.connect(self._on_static_options_changed)
            self.content_layout.addRow("选项(格式: 显示=值):", options_text)
        
        elif source_type == DataSourceType.SQL.value:
            # SQL配置
            query_edit = QTextEdit()
            query_edit.setPlainText(config.get("query", ""))
            query_edit.setMaximumHeight(100)
            query_edit.textChanged.connect(self._on_sql_query_changed)
            self.content_layout.addRow("SQL查询:", query_edit)
            
            conn_edit = QLineEdit(config.get("connection", ""))
            conn_edit.textChanged.connect(lambda v: self._update_data_source_config("connection", v))
            self.content_layout.addRow("连接字符串:", conn_edit)
        
        elif source_type == DataSourceType.API.value:
            # API配置
            url_edit = QLineEdit(config.get("url", ""))
            url_edit.textChanged.connect(lambda v: self._update_data_source_config("url", v))
            self.content_layout.addRow("API地址:", url_edit)
            
            method_combo = QComboBox()
            method_combo.addItems(["GET", "POST"])
            method_combo.setCurrentText(config.get("method", "GET"))
            method_combo.currentTextChanged.connect(lambda v: self._update_data_source_config("method", v))
            self.content_layout.addRow("请求方法:", method_combo)
    
    def _update_config(self, key: str, value):
        """更新配置项"""
        if self.current_config:
            setattr(self.current_config, key, value)
    
    def _update_style(self, key: str, value):
        """更新样式配置"""
        if self.current_config:
            self.current_config.style[key] = value
    
    def _update_data_source_config(self, key: str, value):
        """更新数据源配置"""
        if self.current_config:
            self.current_config.data_source["config"][key] = value
    
    def _on_source_type_changed(self, index: int):
        """数据源类型变更"""
        type_map = {
            0: DataSourceType.STATIC.value,
            1: DataSourceType.SQL.value,
            2: DataSourceType.API.value,
            3: DataSourceType.FUNCTION.value
        }
        if self.current_config:
            self.current_config.data_source["type"] = type_map.get(index, "static")
            self._rebuild_form()
    
    def _on_static_options_changed(self):
        """静态选项变更"""
        sender = self.sender()
        text = sender.toPlainText()
        options = []
        for line in text.split("\n"):
            if "=" in line:
                label, value = line.split("=", 1)
                options.append({"label": label.strip(), "value": value.strip()})
        self.current_config.data_source["config"]["options"] = options
    
    def _on_sql_query_changed(self):
        """SQL查询变更"""
        sender = self.sender()
        self.current_config.data_source["config"]["query"] = sender.toPlainText()
    
    def _apply_changes(self):
        """应用更改到控件"""
        if self.current_widget and self.current_config:
            self.current_widget.update_config(self.current_config)
            self.config_updated.emit(self.current_widget)


# ============================================================================
# 主窗口
# ============================================================================

class FormDesignerWindow(QMainWindow):
    """表单设计器主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("表单设计器 - 查询条件配置器")
        self.setGeometry(100, 100, 1200, 800)
        
        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._build_statusbar()
    
    def _build_ui(self):
        """构建主界面"""
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧工具箱
        self.toolbox = ToolboxWidget()
        splitter.addWidget(self.toolbox)
        
        # 中间画布
        self.canvas = CanvasWidget()
        self.canvas.widget_selected.connect(self._on_widget_selected)
        self.canvas.layout_changed.connect(self._on_layout_changed)
        splitter.addWidget(self.canvas)
        
        # 右侧属性面板
        self.property_panel = PropertyPanelWidget()
        self.property_panel.config_updated.connect(self._on_config_updated)
        splitter.addWidget(self.property_panel)
        
        # 设置分割器比例
        splitter.setSizes([200, 700, 300])
    
    def _build_menu(self):
        """构建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        new_action = QAction("新建", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self._on_new)
        file_menu.addAction(new_action)
        
        open_action = QAction("打开...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._on_open)
        file_menu.addAction(open_action)
        
        save_action = QAction("保存", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")
        
        clear_action = QAction("清空画布", self)
        clear_action.triggered.connect(self._on_clear)
        edit_menu.addAction(clear_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图")
        
        self.grid_action = QAction("显示网格", self)
        self.grid_action.setCheckable(True)
        self.grid_action.setChecked(True)
        self.grid_action.triggered.connect(self._on_toggle_grid)
        view_menu.addAction(self.grid_action)
        
        self.snap_action = QAction("吸附到网格", self)
        self.snap_action.setCheckable(True)
        self.snap_action.setChecked(True)
        self.snap_action.triggered.connect(self._on_toggle_snap)
        view_menu.addAction(self.snap_action)
        
        # 对齐菜单
        align_menu = menubar.addMenu("对齐")
        
        align_left = QAction("左对齐", self)
        align_left.triggered.connect(lambda: self.canvas.align_widgets("left"))
        align_menu.addAction(align_left)
        
        align_right = QAction("右对齐", self)
        align_right.triggered.connect(lambda: self.canvas.align_widgets("right"))
        align_menu.addAction(align_right)
        
        align_top = QAction("顶部对齐", self)
        align_top.triggered.connect(lambda: self.canvas.align_widgets("top"))
        align_menu.addAction(align_top)
        
        align_bottom = QAction("底部对齐", self)
        align_bottom.triggered.connect(lambda: self.canvas.align_widgets("bottom"))
        align_menu.addAction(align_bottom)
        
        align_menu.addSeparator()
        
        align_hcenter = QAction("水平居中", self)
        align_hcenter.triggered.connect(lambda: self.canvas.align_widgets("hcenter"))
        align_menu.addAction(align_hcenter)
        
        align_vcenter = QAction("垂直居中", self)
        align_vcenter.triggered.connect(lambda: self.canvas.align_widgets("vcenter"))
        align_menu.addAction(align_vcenter)
        
        # 预览菜单
        view_menu_preview = menubar.addMenu("预览")
        
        preview_action = QAction("预览表单", self)
        preview_action.triggered.connect(self._on_preview)
        view_menu_preview.addAction(preview_action)
    
    def _build_toolbar(self):
        """构建工具栏"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        toolbar.addAction("新建", self._on_new)
        toolbar.addAction("打开", self._on_open)
        toolbar.addAction("保存", self._on_save)
        toolbar.addSeparator()
        toolbar.addAction("清空", self._on_clear)
        toolbar.addSeparator()
        
        # 网格控制
        self.grid_btn = QPushButton("网格")
        self.grid_btn.setCheckable(True)
        self.grid_btn.setChecked(True)
        self.grid_btn.clicked.connect(self._on_toggle_grid)
        toolbar.addWidget(self.grid_btn)
        
        self.snap_btn = QPushButton("吸附")
        self.snap_btn.setCheckable(True)
        self.snap_btn.setChecked(True)
        self.snap_btn.clicked.connect(self._on_toggle_snap)
        toolbar.addWidget(self.snap_btn)
        
        toolbar.addSeparator()
        
        # 对齐按钮
        toolbar.addAction("左对齐", lambda: self.canvas.align_widgets("left"))
        toolbar.addAction("右对齐", lambda: self.canvas.align_widgets("right"))
        toolbar.addAction("顶对齐", lambda: self.canvas.align_widgets("top"))
        toolbar.addAction("底对齐", lambda: self.canvas.align_widgets("bottom"))
        
        toolbar.addSeparator()
        toolbar.addAction("预览", self._on_preview)
    
    def _build_statusbar(self):
        """构建状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("就绪")
    
    def _on_widget_selected(self, widget: BaseFormWidget):
        """控件被选中"""
        self.property_panel.set_widget(widget)
        self.statusbar.showMessage(f"选中控件: {widget.config.label}")
    
    def _on_config_updated(self, widget: BaseFormWidget):
        """配置更新"""
        self.statusbar.showMessage(f"控件 {widget.config.label} 已更新")
    
    def _on_layout_changed(self):
        """布局变更"""
        count = len(self.canvas.widgets)
        self.statusbar.showMessage(f"画布中有 {count} 个控件")
    
    def _on_new(self):
        """新建表单"""
        reply = QMessageBox.question(
            self, "确认", "确定要创建新表单吗？未保存的更改将丢失。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.canvas.clear_all()
    
    def _on_open(self):
        """打开表单配置"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "打开表单配置", "", "JSON文件 (*.json)"
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    configs = json.load(f)
                self.canvas.load_configs(configs)
                self.statusbar.showMessage(f"已加载: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载失败: {str(e)}")
    
    def _on_save(self):
        """保存表单配置"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存表单配置", "", "JSON文件 (*.json)"
        )
        if filename:
            try:
                configs = self.canvas.get_all_configs()
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(configs, f, indent=2, ensure_ascii=False)
                self.statusbar.showMessage(f"已保存: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
    
    def _on_clear(self):
        """清空画布"""
        reply = QMessageBox.question(
            self, "确认", "确定要清空所有控件吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.canvas.clear_all()
    
    def _on_toggle_grid(self, checked: bool):
        """切换网格显示"""
        self.canvas.set_grid_visible(checked)
        self.grid_btn.setChecked(checked)
        self.grid_action.setChecked(checked)
        self.statusbar.showMessage(f"网格显示: {'开启' if checked else '关闭'}")
    
    def _on_toggle_snap(self, checked: bool):
        """切换网格吸附"""
        self.canvas.set_snap_to_grid(checked)
        self.snap_btn.setChecked(checked)
        self.snap_action.setChecked(checked)
        self.statusbar.showMessage(f"网格吸附: {'开启' if checked else '关闭'}")
    
    def _on_preview(self):
        """预览表单"""
        # 创建预览窗口
        preview = PreviewDialog(self.canvas.get_all_configs(), self)
        preview.exec_()


# ============================================================================
# 预览对话框
# ============================================================================

class PreviewDialog(QDialog):
    """表单预览对话框"""
    
    def __init__(self, configs: List[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("表单预览")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # 创建表单
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        self.value_widgets = {}
        
        for config_data in configs:
            config = WidgetConfig.from_dict(config_data)
            
            # 创建标签
            label = QLabel(config.label)
            if config.required:
                label.setText(f"{config.label} *")
            
            # 根据类型创建输入控件
            widget = self._create_input_widget(config)
            self.value_widgets[config.name] = (widget, config)
            
            form_layout.addRow(label, widget)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(form_widget)
        layout.addWidget(scroll)
        
        # 按钮
        btn_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        btn_box.accepted.connect(self._on_ok)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        
        # 添加获取值按钮
        get_values_btn = QPushButton("获取值")
        get_values_btn.clicked.connect(self._show_values)
        btn_box.addButton(get_values_btn, QDialogButtonBox.ActionRole)
    
    def _create_input_widget(self, config: WidgetConfig) -> QWidget:
        """创建输入控件"""
        if config.field_type == FieldType.TEXT:
            widget = QLineEdit()
            widget.setPlaceholderText(config.placeholder)
        
        elif config.field_type == FieldType.NUMBER:
            widget = QDoubleSpinBox()
            widget.setRange(-999999999, 999999999)
        
        elif config.field_type == FieldType.DATE:
            widget = QDateEdit()
            widget.setCalendarPopup(True)
        
        elif config.field_type in (FieldType.SELECT, FieldType.MULTI_SELECT):
            if config.field_type == FieldType.MULTI_SELECT:
                widget = QListWidget()
                widget.setSelectionMode(QListWidget.MultiSelection)
                widget.setMaximumHeight(100)
            else:
                widget = QComboBox()
            
            # 加载选项
            options = config.data_source.get("config", {}).get("options", [])
            if isinstance(widget, QComboBox):
                for opt in options:
                    widget.addItem(opt.get("label", ""), opt.get("value"))
            else:
                for opt in options:
                    item = QListWidgetItem(opt.get("label", ""))
                    item.setData(Qt.UserRole, opt.get("value"))
                    widget.addItem(item)
        
        elif config.field_type == FieldType.CHECKBOX:
            widget = QCheckBox()
        
        else:
            widget = QLineEdit()
        
        return widget
    
    def _on_ok(self):
        """确定按钮"""
        values = self._get_values()
        print("表单值:", values)
        self.accept()
    
    def _get_values(self) -> dict:
        """获取所有值"""
        values = {}
        for name, (widget, config) in self.value_widgets.items():
            if isinstance(widget, QLineEdit):
                values[name] = widget.text()
            elif isinstance(widget, QDoubleSpinBox):
                values[name] = widget.value()
            elif isinstance(widget, QDateEdit):
                values[name] = widget.date().toString("yyyy-MM-dd")
            elif isinstance(widget, QComboBox):
                values[name] = widget.currentData()
            elif isinstance(widget, QListWidget):
                values[name] = [
                    item.data(Qt.UserRole) 
                    for item in widget.selectedItems()
                ]
            elif isinstance(widget, QCheckBox):
                values[name] = widget.isChecked()
        return values
    
    def _show_values(self):
        """显示当前值"""
        values = self._get_values()
        text = json.dumps(values, indent=2, ensure_ascii=False)
        QMessageBox.information(self, "当前值", text)


# ============================================================================
# 启动入口
# ============================================================================

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    
    # 创建并显示主窗口
    window = FormDesignerWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
