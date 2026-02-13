# PyWindows 功能实现方案详档（离线版）

**文档版本**: 1.0  
**创建日期**: 2026-02-13  
**适用范围**: Windows 7, Python 3.8.1, 完全离线  
**状态**: 详细设计文档

---

## 目录

1. [SQL编辑器增强](#一sql编辑器增强)
2. [性能优化](#二性能优化)
3. [用户体验提升](#三用户体验提升)
4. [本地智能功能](#四本地智能功能)
5. [数据集成](#五数据集成)
6. [本地自动化](#六本地自动化)
7. [架构升级](#七架构升级)
8. [实施指南](#八实施指南)

---

## 一、SQL编辑器增强

### 1.1 本地智能代码补全

#### 1.1.1 架构设计

```
┌─────────────────────────────────────────────────────┐
│                  SQL编辑器                           │
│  ┌───────────────────────────────────────────────┐ │
│  │              SQLCompleter                      │ │
│  │  ┌──────────────┐  ┌──────────────────────┐   │ │
│  │  │  KeywordProvider│  │  MetadataProvider    │   │ │
│  │  │  - SQL关键字   │  │  - 表名/列名          │   │ │
│  │  │  - 函数名      │  │  - 实时缓存           │   │ │
│  │  └──────────────┘  └──────────────────────┘   │ │
│  └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────┐
│              LocalMetadataCache                      │
│  ┌───────────────────────────────────────────────┐ │
│  │  SQLite数据库: data/metadata_cache.db         │ │
│  │  - tables (表元数据)                          │ │
│  │  - columns (列元数据)                         │ │
│  │  - indexes (索引信息)                         │ │
│  │  - last_update (更新时间)                     │ │
│  └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

#### 1.1.2 数据模型

**表结构**:
```sql
-- 表元数据表
CREATE TABLE tables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    connection_id TEXT NOT NULL,  -- 连接标识
    schema_name TEXT,             -- 模式名
    table_name TEXT NOT NULL,     -- 表名
    table_type TEXT,              -- 类型: TABLE/VIEW
    comment TEXT,                 -- 注释
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(connection_id, schema_name, table_name)
);

-- 列元数据表
CREATE TABLE columns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_id INTEGER NOT NULL,
    column_name TEXT NOT NULL,
    data_type TEXT,               -- 数据类型
    is_nullable BOOLEAN,
    column_default TEXT,
    comment TEXT,
    ordinal_position INTEGER,     -- 列顺序
    FOREIGN KEY (table_id) REFERENCES tables(id),
    UNIQUE(table_id, column_name)
);

-- 创建全文搜索索引
CREATE VIRTUAL TABLE table_search USING fts5(
    table_name, 
    comment,
    content='tables',
    content_rowid='id'
);
```

#### 1.1.3 核心代码实现

**文件**: `src/presentation/widgets/sql_completer.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SQL智能补全组件
支持本地关键字、表名、列名补全
"""

import sqlite3
import re
from typing import List, Tuple, Optional
from PySide2.QtWidgets import QCompleter, QTextEdit
from PySide2.QtCore import Qt, QStringListModel


class SQLKeywordProvider:
    """SQL关键字提供者"""
    
    # SQL关键字分类
    KEYWORDS = {
        'DML': ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'MERGE'],
        'DDL': ['CREATE', 'ALTER', 'DROP', 'TRUNCATE', 'TABLE', 'INDEX', 'VIEW'],
        'CLAUSES': ['FROM', 'WHERE', 'GROUP BY', 'HAVING', 'ORDER BY', 'LIMIT'],
        'JOINS': ['JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN', 'CROSS JOIN'],
        'OPERATORS': ['AND', 'OR', 'NOT', 'IN', 'EXISTS', 'BETWEEN', 'LIKE'],
        'FUNCTIONS': [
            'COUNT', 'SUM', 'AVG', 'MAX', 'MIN',
            'CONCAT', 'SUBSTRING', 'UPPER', 'LOWER', 'TRIM',
            'DATE', 'NOW', 'YEAR', 'MONTH', 'DAY'
        ]
    }
    
    def __init__(self):
        self.all_keywords = []
        for category in self.KEYWORDS.values():
            self.all_keywords.extend(category)
        self.all_keywords = sorted(set(self.all_keywords))
    
    def get_suggestions(self, prefix: str) -> List[str]:
        """根据前缀获取关键字建议"""
        prefix_upper = prefix.upper()
        return [kw for kw in self.all_keywords if kw.startswith(prefix_upper)]


class LocalMetadataCache:
    """本地元数据缓存管理"""
    
    def __init__(self, db_path: str = 'data/metadata_cache.db'):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS tables (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    connection_id TEXT NOT NULL,
                    schema_name TEXT,
                    table_name TEXT NOT NULL,
                    table_type TEXT,
                    comment TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(connection_id, schema_name, table_name)
                );
                
                CREATE TABLE IF NOT EXISTS columns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_id INTEGER NOT NULL,
                    column_name TEXT NOT NULL,
                    data_type TEXT,
                    is_nullable BOOLEAN,
                    column_default TEXT,
                    comment TEXT,
                    ordinal_position INTEGER,
                    FOREIGN KEY (table_id) REFERENCES tables(id),
                    UNIQUE(table_id, column_name)
                );
                
                CREATE INDEX IF NOT EXISTS idx_tables_conn ON tables(connection_id);
                CREATE INDEX IF NOT EXISTS idx_columns_table ON columns(table_id);
            ''')
    
    def update_metadata(self, connection_id: str, tables_data: List[dict]):
        """更新元数据缓存"""
        with sqlite3.connect(self.db_path) as conn:
            # 删除旧数据
            conn.execute(
                'DELETE FROM tables WHERE connection_id = ?', 
                (connection_id,)
            )
            
            # 插入新数据
            for table_data in tables_data:
                cursor = conn.execute('''
                    INSERT INTO tables (connection_id, schema_name, table_name, table_type, comment)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    connection_id,
                    table_data.get('schema'),
                    table_data['name'],
                    table_data.get('type', 'TABLE'),
                    table_data.get('comment', '')
                ))
                
                table_id = cursor.lastrowid
                
                # 插入列信息
                for col in table_data.get('columns', []):
                    conn.execute('''
                        INSERT INTO columns (table_id, column_name, data_type, 
                                           is_nullable, column_default, comment, ordinal_position)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        table_id,
                        col['name'],
                        col.get('type', 'VARCHAR'),
                        col.get('nullable', True),
                        col.get('default'),
                        col.get('comment', ''),
                        col.get('position', 0)
                    ))
            
            conn.commit()
    
    def search_tables(self, connection_id: str, prefix: str, limit: int = 20) -> List[Tuple]:
        """搜索表名"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT schema_name, table_name, table_type, comment
                FROM tables
                WHERE connection_id = ? 
                  AND (table_name LIKE ? OR comment LIKE ?)
                ORDER BY table_name
                LIMIT ?
            ''', (connection_id, f'{prefix}%', f'%{prefix}%', limit))
            return cursor.fetchall()
    
    def get_columns(self, connection_id: str, table_name: str) -> List[Tuple]:
        """获取表的列信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT c.column_name, c.data_type, c.comment
                FROM columns c
                JOIN tables t ON c.table_id = t.id
                WHERE t.connection_id = ? AND t.table_name = ?
                ORDER BY c.ordinal_position
            ''', (connection_id, table_name))
            return cursor.fetchall()


class SQLCompleter(QCompleter):
    """SQL智能补全器"""
    
    def __init__(self, parent: QTextEdit, connection_id: str = 'default'):
        super().__init__(parent)
        self.text_edit = parent
        self.connection_id = connection_id
        
        # 初始化提供者
        self.keyword_provider = SQLKeywordProvider()
        self.metadata_cache = LocalMetadataCache()
        
        # 设置模型
        self.model = QStringListModel()
        self.setModel(self.model)
        
        # 配置补全器
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompletionMode(QCompleter.PopupCompletion)
        self.setFilterMode(Qt.MatchStartsWith)
        
        # 连接信号
        self.text_edit.textChanged.connect(self._on_text_changed)
        self.activated.connect(self._insert_completion)
    
    def _on_text_changed(self):
        """文本变化时触发补全"""
        cursor = self.text_edit.textCursor()
        current_line = cursor.block().text()[:cursor.positionInBlock()]
        
        # 获取当前单词
        word = self._get_current_word(current_line)
        if len(word) < 2:  # 最少2个字符才触发
            self.complete()
            return
        
        # 获取补全建议
        suggestions = self._get_suggestions(word, current_line)
        
        if suggestions:
            self.model.setStringList(suggestions)
            # 计算补全位置
            rect = self.text_edit.cursorRect()
            self.complete(rect)
    
    def _get_current_word(self, line: str) -> str:
        """获取当前正在输入的单词"""
        # 从后往前找，直到遇到空格或特殊字符
        match = re.search(r'[\w.]+$', line)
        return match.group(0) if match else ''
    
    def _get_suggestions(self, word: str, context: str) -> List[str]:
        """根据上下文获取补全建议"""
        suggestions = []
        word_upper = word.upper()
        
        # 1. 关键字建议
        keywords = self.keyword_provider.get_suggestions(word)
        suggestions.extend(keywords)
        
        # 2. 根据上下文判断是否需要表名/列名
        if self._needs_table_name(context):
            # 添加表名建议
            tables = self.metadata_cache.search_tables(
                self.connection_id, word, limit=10
            )
            for schema, name, type_, comment in tables:
                display = f"{name} ({type_})"
                if comment:
                    display += f" - {comment[:30]}"
                suggestions.append(display)
        
        elif self._needs_column_name(context):
            # 添加列名建议
            table_name = self._extract_table_name(context)
            if table_name:
                columns = self.metadata_cache.get_columns(
                    self.connection_id, table_name
                )
                for col_name, col_type, comment in columns:
                    if col_name.upper().startswith(word_upper):
                        display = f"{col_name} ({col_type})"
                        suggestions.append(display)
        
        return suggestions[:20]  # 限制数量
    
    def _needs_table_name(self, context: str) -> bool:
        """判断当前是否需要表名"""
        patterns = [
            r'\bFROM\s+\w*$',
            r'\bJOIN\s+\w*$',
            r'\bINTO\s+\w*$',
            r'\bTABLE\s+\w*$'
        ]
        context_upper = context.upper()
        return any(re.search(p, context_upper) for p in patterns)
    
    def _needs_column_name(self, context: str) -> bool:
        """判断当前是否需要列名"""
        patterns = [
            r'\bSELECT\s+[\w\s,]*$',
            r'\bWHERE\s+[\w\s]*$',
            r'\bGROUP\s+BY\s+[\w\s]*$',
            r'\bORDER\s+BY\s+[\w\s]*$'
        ]
        context_upper = context.upper()
        return any(re.search(p, context_upper) for p in patterns)
    
    def _extract_table_name(self, context: str) -> Optional[str]:
        """从上下文提取表名"""
        # 简单的表名提取逻辑
        match = re.search(r'\bFROM\s+(\w+)', context, re.IGNORECASE)
        if match:
            return match.group(1)
        
        match = re.search(r'\bJOIN\s+(\w+)', context, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    
    def _insert_completion(self, completion: str):
        """插入选中的补全项"""
        cursor = self.text_edit.textCursor()
        current_line = cursor.block().text()[:cursor.positionInBlock()]
        word = self._get_current_word(current_line)
        
        # 移除已输入的部分
        for _ in range(len(word)):
            cursor.deletePreviousChar()
        
        # 插入补全文本（去掉括号里的说明）
        text_to_insert = completion.split(' (')[0]
        cursor.insertText(text_to_insert)
        
        self.text_edit.setTextCursor(cursor)


# 使用示例
if __name__ == '__main__':
    from PySide2.QtWidgets import QApplication, QTextEdit, QVBoxLayout, QWidget
    import sys
    
    app = QApplication(sys.argv)
    
    window = QWidget()
    layout = QVBoxLayout()
    
    editor = QTextEdit()
    completer = SQLCompleter(editor)
    
    # 测试数据
    test_metadata = [
        {
            'name': 'users',
            'type': 'TABLE',
            'comment': '用户表',
            'columns': [
                {'name': 'id', 'type': 'INT', 'position': 1},
                {'name': 'username', 'type': 'VARCHAR(50)', 'position': 2},
                {'name': 'email', 'type': 'VARCHAR(100)', 'position': 3}
            ]
        },
        {
            'name': 'orders',
            'type': 'TABLE',
            'comment': '订单表',
            'columns': [
                {'name': 'id', 'type': 'INT', 'position': 1},
                {'name': 'user_id', 'type': 'INT', 'position': 2},
                {'name': 'amount', 'type': 'DECIMAL(10,2)', 'position': 3}
            ]
        }
    ]
    
    completer.metadata_cache.update_metadata('default', test_metadata)
    
    layout.addWidget(editor)
    window.setLayout(layout)
    window.resize(600, 400)
    window.show()
    
    sys.exit(app.exec_())
```

#### 1.1.4 实施步骤

**Step 1**: 创建目录结构
```bash
mkdir -p src/presentation/widgets
```

**Step 2**: 安装依赖（Python 3.8.1兼容）
```bash
pip install PySide2==5.14.0
```

**Step 3**: 在SQL编辑器中集成
```python
# 在 sql_query_dialog.py 中
from src.presentation.widgets.sql_completer import SQLCompleter

class SQLQueryDialog:
    def setup_editor(self):
        self.sql_editor = QTextEdit()
        
        # 添加智能补全
        self.completer = SQLCompleter(self.sql_editor, self.connection_id)
        
        # 定期刷新元数据（例如每5分钟）
        self.metadata_refresh_timer = QTimer()
        self.metadata_refresh_timer.timeout.connect(self.refresh_metadata)
        self.metadata_refresh_timer.start(300000)  # 5分钟
    
    def refresh_metadata(self):
        """刷新数据库元数据"""
        tables = self.data_service.get_all_tables()
        columns_info = []
        
        for table in tables:
            columns = self.data_service.get_table_columns(table)
            columns_info.append({
                'name': table,
                'type': 'TABLE',
                'columns': [
                    {
                        'name': col['name'],
                        'type': col['type'],
                        'position': col['ordinal_position']
                    }
                    for col in columns
                ]
            })
        
        self.completer.metadata_cache.update_metadata(
            self.connection_id, columns_info
        )
```

**Step 4**: 测试验证
- 输入"SEL"应提示"SELECT"
- 输入"FROM us"应提示"users"表
- 输入"SELECT u"（在FROM users后）应提示列名

**预期效果**: 编码效率提升50%

---

### 1.2 查询结果可视化增强

#### 1.2.1 架构设计

```
┌─────────────────────────────────────────────────────┐
│              查询结果可视化系统                       │
├─────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────┐ │
│  │           ChartWidget (PyQtGraph)             │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────┐  │ │
│  │  │ 柱状图   │ │ 折线图   │ │ 饼图         │  │ │
│  │  │ BarChart │ │ LineChart│ │ PieChart     │  │ │
│  │  └──────────┘ └──────────┘ └──────────────┘  │ │
│  └───────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────┐ │
│  │        PivotTable (本地计算)                   │ │
│  │  - 行维度选择                                  │ │
│  │  - 列维度选择                                  │ │
│  │  - 值聚合 (SUM/AVG/COUNT)                     │ │
│  │  - 本地Pandas计算                              │ │
│  └───────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────┐ │
│  │        ExportManager (本地导出)                │ │
│  │  - Excel (openpyxl)                           │ │
│  │  - PDF (ReportLab)                            │ │
│  │  - CSV/JSON                                   │ │
│  └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

#### 1.2.2 核心代码实现

**文件**: `src/presentation/widgets/chart_widget.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
图表可视化组件
使用 PyQtGraph 实现本地高性能图表渲染
"""

import pyqtgraph as pg
from PySide2.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QPushButton
from PySide2.QtCore import Qt
from typing import List, Dict, Any, Optional
import numpy as np


class ChartWidget(QWidget):
    """图表可视化组件"""
    
    CHART_TYPES = ['柱状图', '折线图', '饼图', '散点图']
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        self.columns = []
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        # 图表类型选择
        toolbar.addWidget(QLabel('图表类型:'))
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(self.CHART_TYPES)
        self.chart_type_combo.currentTextChanged.connect(self.on_chart_type_changed)
        toolbar.addWidget(self.chart_type_combo)
        
        toolbar.addSpacing(20)
        
        # X轴选择
        toolbar.addWidget(QLabel('X轴:'))
        self.x_axis_combo = QComboBox()
        toolbar.addWidget(self.x_axis_combo)
        
        toolbar.addSpacing(20)
        
        # Y轴选择
        toolbar.addWidget(QLabel('Y轴:'))
        self.y_axis_combo = QComboBox()
        toolbar.addWidget(self.y_axis_combo)
        
        toolbar.addStretch()
        
        # 刷新按钮
        refresh_btn = QPushButton('刷新')
        refresh_btn.clicked.connect(self.update_chart)
        toolbar.addWidget(refresh_btn)
        
        layout.addLayout(toolbar)
        
        # 图表区域
        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)
        
        # 设置中文字体
        self.plot_widget.setLabel('left', '数值')
        self.plot_widget.setLabel('bottom', '类别')
        self.plot_widget.showGrid(x=True, y=True)
    
    def set_data(self, data: List[Dict[str, Any]], columns: List[str]):
        """设置数据"""
        self.data = data
        self.columns = columns
        
        # 更新下拉框
        self.x_axis_combo.clear()
        self.y_axis_combo.clear()
        
        for col in columns:
            self.x_axis_combo.addItem(col)
            self.y_axis_combo.addItem(col)
        
        # 默认选择
        if len(columns) >= 2:
            self.x_axis_combo.setCurrentIndex(0)
            self.y_axis_combo.setCurrentIndex(1)
        
        self.update_chart()
    
    def on_chart_type_changed(self, chart_type: str):
        """图表类型改变"""
        self.update_chart()
    
    def update_chart(self):
        """更新图表"""
        if not self.data or not self.columns:
            return
        
        chart_type = self.chart_type_combo.currentText()
        x_col = self.x_axis_combo.currentText()
        y_col = self.y_axis_combo.currentText()
        
        # 清除旧图表
        self.plot_widget.clear()
        
        # 准备数据
        x_data = [str(row.get(x_col, '')) for row in self.data]
        y_data = [float(row.get(y_col, 0) or 0) for row in self.data]
        
        if chart_type == '柱状图':
            self._draw_bar_chart(x_data, y_data)
        elif chart_type == '折线图':
            self._draw_line_chart(x_data, y_data)
        elif chart_type == '散点图':
            self._draw_scatter_chart(x_data, y_data)
        elif chart_type == '饼图':
            self._draw_pie_chart(x_data, y_data)
    
    def _draw_bar_chart(self, x_data: List[str], y_data: List[float]):
        """绘制柱状图"""
        x_pos = np.arange(len(x_data))
        
        bar_item = pg.BarGraphItem(
            x=x_pos,
            height=y_data,
            width=0.6,
            brush='#2563EB'
        )
        
        self.plot_widget.addItem(bar_item)
        
        # 设置X轴标签
        axis = self.plot_widget.getAxis('bottom')
        axis.setTicks([[(i, label) for i, label in enumerate(x_data)]])
        
        self.plot_widget.setLabel('left', self.y_axis_combo.currentText())
        self.plot_widget.setLabel('bottom', self.x_axis_combo.currentText())
    
    def _draw_line_chart(self, x_data: List[str], y_data: List[float]):
        """绘制折线图"""
        x_pos = np.arange(len(x_data))
        
        self.plot_widget.plot(
            x_pos,
            y_data,
            pen=pg.mkPen(color='#2563EB', width=2),
            symbol='o',
            symbolSize=8,
            symbolBrush='#2563EB'
        )
        
        axis = self.plot_widget.getAxis('bottom')
        axis.setTicks([[(i, label) for i, label in enumerate(x_data)]])
        
        self.plot_widget.setLabel('left', self.y_axis_combo.currentText())
        self.plot_widget.setLabel('bottom', self.x_axis_combo.currentText())
    
    def _draw_scatter_chart(self, x_data: List[str], y_data: List[float]):
        """绘制散点图"""
        x_pos = np.arange(len(x_data))
        
        scatter = pg.ScatterPlotItem(
            x=x_pos,
            y=y_data,
            size=10,
            brush='#2563EB',
            pen=pg.mkPen(color='#1D4ED8', width=1)
        )
        
        self.plot_widget.addItem(scatter)
        
        axis = self.plot_widget.getAxis('bottom')
        axis.setTicks([[(i, label) for i, label in enumerate(x_data)]])
        
        self.plot_widget.setLabel('left', self.y_axis_combo.currentText())
        self.plot_widget.setLabel('bottom', self.x_axis_combo.currentText())
    
    def _draw_pie_chart(self, x_data: List[str], y_data: List[float]):
        """绘制饼图（使用柱状图模拟）"""
        # PyQtGraph不直接支持饼图，使用特殊柱状图
        total = sum(y_data)
        percentages = [y / total * 100 for y in y_data]
        
        colors = ['#2563EB', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899']
        
        x_pos = np.arange(len(x_data))
        
        for i, (x, y, pct) in enumerate(zip(x_pos, y_data, percentages)):
            color = colors[i % len(colors)]
            bar = pg.BarGraphItem(
                x=[x],
                height=[y],
                width=0.6,
                brush=color
            )
            self.plot_widget.addItem(bar)
            
            # 添加标签
            text = pg.TextItem(
                text=f'{x_data[i]}\n{pct:.1f}%',
                anchor=(0.5, 0),
                color='#1E293B'
            )
            text.setPos(x, y)
            self.plot_widget.addItem(text)
        
        axis = self.plot_widget.getAxis('bottom')
        axis.setTicks([[(i, label) for i, label in enumerate(x_data)]])
        
        self.plot_widget.setLabel('left', self.y_axis_combo.currentText())
        self.plot_widget.setLabel('bottom', '类别')


class PivotTableWidget(QWidget):
    """数据透视表组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        from PySide2.QtWidgets import QTableWidget, QTableWidgetItem, QGroupBox
        
        layout = QVBoxLayout(self)
        
        # 配置区域
        config_group = QGroupBox('透视表配置')
        config_layout = QHBoxLayout()
        
        # 行维度
        config_layout.addWidget(QLabel('行维度:'))
        self.row_combo = QComboBox()
        config_layout.addWidget(self.row_combo)
        
        # 列维度
        config_layout.addWidget(QLabel('列维度:'))
        self.col_combo = QComboBox()
        self.col_combo.addItem('(无)')
        config_layout.addWidget(self.col_combo)
        
        # 值字段
        config_layout.addWidget(QLabel('值字段:'))
        self.value_combo = QComboBox()
        config_layout.addWidget(self.value_combo)
        
        # 聚合方式
        config_layout.addWidget(QLabel('聚合:'))
        self.agg_combo = QComboBox()
        self.agg_combo.addItems(['SUM', 'AVG', 'COUNT', 'MAX', 'MIN'])
        config_layout.addWidget(self.agg_combo)
        
        # 应用按钮
        apply_btn = QPushButton('应用')
        apply_btn.clicked.connect(self.update_pivot)
        config_layout.addWidget(apply_btn)
        
        config_layout.addStretch()
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # 结果表格
        self.result_table = QTableWidget()
        layout.addWidget(self.result_table)
    
    def set_data(self, data: List[Dict[str, Any]], columns: List[str]):
        """设置数据"""
        self.data = data
        
        # 更新下拉框
        self.row_combo.clear()
        self.col_combo.clear()
        self.col_combo.addItem('(无)')
        self.value_combo.clear()
        
        for col in columns:
            self.row_combo.addItem(col)
            self.col_combo.addItem(col)
            self.value_combo.addItem(col)
    
    def update_pivot(self):
        """更新透视表"""
        import pandas as pd
        
        if not self.data:
            return
        
        row_col = self.row_combo.currentText()
        col_col = self.col_combo.currentText()
        value_col = self.value_combo.currentText()
        agg_func = self.agg_combo.currentText().lower()
        
        # 转换为DataFrame
        df = pd.DataFrame(self.data)
        
        # 构建透视表
        try:
            if col_col and col_col != '(无)':
                pivot = pd.pivot_table(
                    df,
                    values=value_col,
                    index=row_col,
                    columns=col_col,
                    aggfunc=agg_func,
                    fill_value=0
                )
            else:
                pivot = pd.pivot_table(
                    df,
                    values=value_col,
                    index=row_col,
                    aggfunc=agg_func,
                    fill_value=0
                )
            
            # 显示结果
            self._display_pivot(pivot)
        except Exception as e:
            print(f"透视表计算错误: {e}")
    
    def _display_pivot(self, pivot: 'pd.DataFrame'):
        """显示透视表结果"""
        rows, cols = pivot.shape
        
        self.result_table.setRowCount(rows)
        self.result_table.setColumnCount(cols + 1)  # +1 for index
        
        # 设置表头
        headers = [pivot.index.name or 'Index'] + list(pivot.columns)
        self.result_table.setHorizontalHeaderLabels(headers)
        
        # 填充数据
        for i, (idx, row) in enumerate(pivot.iterrows()):
            # 索引列
            self.result_table.setItem(i, 0, QTableWidgetItem(str(idx)))
            
            # 数据列
            for j, val in enumerate(row):
                self.result_table.setItem(i, j + 1, QTableWidgetItem(str(val)))
```

#### 1.2.3 导出功能实现

**文件**: `src/business/services/export_service.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据导出服务
支持Excel、PDF、CSV、JSON导出（完全离线）
"""

import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ExportService:
    """数据导出服务"""
    
    def export_to_csv(self, data: List[Dict], filepath: str, 
                      encoding: str = 'utf-8-sig') -> bool:
        """导出为CSV"""
        try:
            if not data:
                return False
            
            headers = list(data[0].keys())
            
            with open(filepath, 'w', newline='', encoding=encoding) as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"CSV导出成功: {filepath}")
            return True
        except Exception as e:
            logger.error(f"CSV导出失败: {e}")
            return False
    
    def export_to_json(self, data: List[Dict], filepath: str,
                       indent: int = 2) -> bool:
        """导出为JSON"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
            
            logger.info(f"JSON导出成功: {filepath}")
            return True
        except Exception as e:
            logger.error(f"JSON导出失败: {e}")
            return False
    
    def export_to_excel(self, data: List[Dict], filepath: str,
                        sheet_name: str = 'Sheet1') -> bool:
        """导出为Excel"""
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment
            
            if not data:
                return False
            
            wb = Workbook()
            ws = wb.active
            ws.title = sheet_name
            
            # 写入表头
            headers = list(data[0].keys())
            header_font = Font(bold=True, color='FFFFFF')
            header_fill = PatternFill(start_color='2563EB', end_color='2563EB', fill_type='solid')
            
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center')
            
            # 写入数据
            for row_idx, row_data in enumerate(data, 2):
                for col_idx, header in enumerate(headers, 1):
                    value = row_data.get(header, '')
                    ws.cell(row=row_idx, column=col_idx, value=value)
            
            # 自动调整列宽
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column].width = adjusted_width
            
            wb.save(filepath)
            logger.info(f"Excel导出成功: {filepath}")
            return True
            
        except ImportError:
            logger.error("未安装openpyxl，无法导出Excel")
            return False
        except Exception as e:
            logger.error(f"Excel导出失败: {e}")
            return False
    
    def export_to_pdf(self, data: List[Dict], filepath: str,
                      title: str = "数据报表") -> bool:
        """导出为PDF"""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            
            if not data:
                return False
            
            doc = SimpleDocTemplate(
                filepath,
                pagesize=landscape(A4),
                rightMargin=30,
                leftMargin=30,
                topMargin=30,
                bottomMargin=30
            )
            
            elements = []
            styles = getSampleStyleSheet()
            
            # 标题
            title_para = Paragraph(f"<b>{title}</b>", styles['Title'])
            elements.append(title_para)
            elements.append(Spacer(1, 20))
            
            # 准备表格数据
            headers = list(data[0].keys())
            table_data = [headers]
            
            for row in data[:1000]:  # 限制1000行以防内存溢出
                table_data.append([str(row.get(h, '')) for h in headers])
            
            # 创建表格
            table = Table(table_data, repeatRows=1)
            
            # 表格样式
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563EB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ])
            table.setStyle(table_style)
            
            elements.append(table)
            
            doc.build(elements)
            logger.info(f"PDF导出成功: {filepath}")
            return True
            
        except ImportError:
            logger.error("未安装ReportLab，无法导出PDF")
            return False
        except Exception as e:
            logger.error(f"PDF导出失败: {e}")
            return False


# 便捷函数
def export_data(data: List[Dict], filepath: str, format: str = 'csv') -> bool:
    """导出数据的便捷函数"""
    service = ExportService()
    
    format = format.lower()
    
    if format == 'csv':
        return service.export_to_csv(data, filepath)
    elif format == 'json':
        return service.export_to_json(data, filepath)
    elif format in ['excel', 'xlsx']:
        return service.export_to_excel(data, filepath)
    elif format == 'pdf':
        return service.export_to_pdf(data, filepath)
    else:
        logger.error(f"不支持的导出格式: {format}")
        return False
```

（由于文档长度限制，后续章节继续在下一条回复中）
---

## 后续章节概要

由于文档长度限制，以下是其他功能的实现方案概要：

### 1.3 查询历史本地管理
- **技术**: SQLite + FTS全文搜索
- **核心类**: `LocalQueryHistory`
- **功能**: 本地存储、全文搜索、标签管理、使用统计

### 1.4 性能优化
- **查询缓存**: LRU缓存策略，本地文件存储
- **连接池监控**: 实时监控面板，动态调整
- **流式加载**: 虚拟滚动，大数据量优化

### 1.5 用户体验提升
- **主题系统**: 本地QSS样式文件
- **表格编辑**: 内联编辑，撤销重做
- **快捷键**: 可配置快捷键系统

## 二、本地智能功能

### 2.1 本地SQL分析器
```python
class LocalSQLAnalyzer:
    # 基于规则的SQL检查
    # 无需AI API，完全离线
```

### 2.2 本地统计分析
- 使用 NumPy/Pandas
- 基础统计、相关性分析
- 完全离线计算

## 三、数据集成

### 3.1 本地文件数据源
- CSV/Excel/JSON文件读取
- 使用 openpyxl, pandas
- 虚拟表映射

### 3.2 Windows计划任务集成
```python
class WindowsTaskScheduler:
    # 使用 win32com.client
    # 创建本地定时任务
```

## 四、架构升级

### 4.1 本地插件系统
- Python动态导入
- 本地插件包格式
- 手动安装方式

### 4.2 数据安全
- Windows DPAPI加密
- SQLite加密(SQLCipher)
- 本地密码哈希

## 五、实施检查清单

### 每个功能的实施步骤:
1. [ ] 设计文档编写
2. [ ] 数据模型设计
3. [ ] 核心代码实现
4. [ ] 单元测试编写
5. [ ] 集成测试
6. [ ] 文档更新
7. [ ] 代码审查
8. [ ] 合并到主分支

### 兼容性验证:
- [ ] Windows 7 SP1 测试通过
- [ ] Python 3.8.1 运行正常
- [ ] 离线环境验证通过
- [ ] 所有依赖支持离线安装

---

**文档版本**: 1.0  
**创建日期**: 2026-02-13  
**状态**: 详细设计方案

**注**: 完整代码实现请参考具体功能分支
