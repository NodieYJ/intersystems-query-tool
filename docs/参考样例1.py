import re
import sys
from PySide2.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QCheckBox,
                               QTableWidget, QTableWidgetItem, QTextEdit,
                               QHeaderView, QFileDialog)
from PySide2.QtCore import Qt
from PySide2.QtGui import QTextCursor, QTextCharFormat, QColor, QBrush

class TextSearchApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.current_highlights = []  # 存储当前高亮的位置，用于清除

    def initUI(self):
        self.setWindowTitle('文本内容模糊搜索器 (PySide2)')
        self.setGeometry(200, 200, 900, 600)

        # 主布局
        main_layout = QVBoxLayout()

        # --- 控制面板 ---
        ctrl_layout = QHBoxLayout()
        
        # 文件选择
        self.file_btn = QPushButton('选择文件')
        self.file_btn.clicked.connect(self.select_file)
        self.file_label = QLabel('未选择文件')
        ctrl_layout.addWidget(self.file_btn)
        ctrl_layout.addWidget(self.file_label)

        # 搜索框
        ctrl_layout.addWidget(QLabel('搜索词:'))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('输入搜索内容...')
        ctrl_layout.addWidget(self.search_input)

        # 选项
        self.case_checkbox = QCheckBox('区分大小写')
        self.whole_word_checkbox = QCheckBox('全词匹配')
        ctrl_layout.addWidget(self.case_checkbox)
        ctrl_layout.addWidget(self.whole_word_checkbox)

        # 搜索按钮
        self.search_btn = QPushButton('开始搜索')
        self.search_btn.clicked.connect(self.perform_search)
        ctrl_layout.addWidget(self.search_btn)

        main_layout.addLayout(ctrl_layout)

        # --- 结果显示区 (表格) ---
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(['行号', '内容预览', '匹配位置'])
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # 内容列自动拉伸
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.itemClicked.connect(self.highlight_match)
        main_layout.addWidget(self.results_table)

        # --- 文本显示区 (用于高亮) ---
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        main_layout.addWidget(self.text_display)

        self.setLayout(main_layout)

    def select_file(self):
        """选择文件并加载内容到文本显示区"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文本文件", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            self.file_label.setText(file_path)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.text_display.setPlainText(content)
                self.current_file_path = file_path
                # 清除旧的搜索结果和高亮
                self.clear_highlights()
                self.results_table.setRowCount(0)
            except Exception as e:
                self.text_display.setPlainText(f"读取文件出错: {e}")

    def perform_search(self):
        """执行搜索，在表格中列出结果"""
        if not hasattr(self, 'current_file_path'):
            self.text_display.setPlainText("请先选择文件。")
            return

        search_text = self.search_input.text().strip()
        if not search_text:
            return

        # 清除旧高亮
        self.clear_highlights()

        # 构建正则表达式
        pattern = re.escape(search_text)  # 转义特殊字符，实现“模糊”中的精确匹配
        if self.whole_word_checkbox.isChecked():
            pattern = r'\b' + pattern + r'\b'
        
        flags = 0 if self.case_checkbox.isChecked() else re.IGNORECASE

        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            self.text_display.setPlainText(f"正则表达式错误: {e}")
            return

        # 读取文件并搜索
        try:
            with open(self.current_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            self.text_display.setPlainText(f"读取文件出错: {e}")
            return

        # 清空并准备结果表格
        self.results_table.setRowCount(0)
        self.all_matches = []  # 存储所有匹配项的信息，用于高亮

        for line_num, line in enumerate(lines, start=1):
            for match in regex.finditer(line):
                # 记录匹配信息 (行号从1开始，用于显示；位置索引用于高亮)
                self.all_matches.append({
                    'line_num': line_num, # 显示用
                    'line_index': line_num - 1, # 文本行索引，从0开始
                    'start': match.start(),
                    'end': match.end(),
                    'preview': line.strip()[:50] + '...' if len(line.strip()) > 50 else line.strip()
                })
                # 在表格中添加一行
                row = self.results_table.rowCount()
                self.results_table.insertRow(row)
                self.results_table.setItem(row, 0, QTableWidgetItem(str(line_num)))
                self.results_table.setItem(row, 1, QTableWidgetItem(self.all_matches[-1]['preview']))
                self.results_table.setItem(row, 2, QTableWidgetItem(f"{match.start()}-{match.end()}"))

        status = f"找到 {len(self.all_matches)} 个匹配项。"
        self.text_display.setPlainText(self.text_display.toPlainText() + f"\n\n--- {status} ---")

    def highlight_match(self, item):
        """高亮当前选中的匹配项"""
        # 清除所有旧高亮
        self.clear_highlights()

        row = item.row()
        if row >= len(self.all_matches):
            return

        match_info = self.all_matches[row]

        # 获取文本光标
        cursor = self.text_document().findBlockByLineNumber(match_info['line_index']).position()
        
        # 创建高亮格式
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QBrush(QColor(144, 238, 144)))  # 浅绿色

        # 创建光标并应用高亮
        text_cursor = QTextCursor(self.text_document())
        text_cursor.setPosition(cursor + match_info['start'])
        text_cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, match_info['end'] - match_info['start'])
        text_cursor.mergeCharFormat(highlight_format)

        # 存储高亮位置，以便后续清除 (此处简化，仅存储最后一个高亮的起止和格式)
        # 注意：实际更复杂的应用可能需要管理多个高亮对象
        self.current_highlights.append({
            'cursor_pos': cursor + match_info['start'],
            'length': match_info['end'] - match_info['start'],
            'format': highlight_format
        })

        # 滚动到高亮行
        self.text_display.setTextCursor(text_cursor)
        self.text_display.centerCursor()

    def clear_highlights(self):
        """清除所有高亮"""
        cursor = QTextCursor(self.text_document())
        cursor.select(QTextCursor.Document)
        default_format = QTextCharFormat()
        default_format.setBackground(QBrush(Qt.white))  # 恢复默认背景色（白色）
        cursor.mergeCharFormat(default_format)
        self.current_highlights.clear()

    def text_document(self):
        return self.text_display.document()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TextSearchApp()
    ex.show()
    sys.exit(app.exec_())
