import sys
import os
import re
from PySide2.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QListWidget, QListWidgetItem, 
                               QLabel, QFrame, QPlainTextEdit, QLineEdit, QPushButton, QCheckBox)
from PySide2.QtCore import Qt, QRect, QSize
from PySide2.QtGui import (QTextCursor, QFont, QTextOption, QColor, QPainter, 
                          QTextFormat, QFontMetrics, QPalette)

class LineNumberArea(QWidget):
    """自定义行号区域部件，用于显示行号，不可被选中和编辑"""
    def __init__(self, editor):
        super().__init__(editor)
        self.text_editor = editor
        # 设置不接受鼠标事件，不可被选中
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setFocusPolicy(Qt.NoFocus)
        
    def sizeHint(self):
        return QSize(self.text_editor.line_number_area_width(), 0)
    
    def paintEvent(self, event):
        """绘制行号"""
        self.text_editor.line_number_area_paint_event(event)

class TextEditorWithLineNumbers(QPlainTextEdit):
    """自定义文本编辑器，带行号显示，只读模式允许文本选中"""
    def __init__(self):
        super().__init__()
        self.line_number_area = LineNumberArea(self)
        
        # 设置文本区域为只读，允许选中文本但不允许编辑
        self.setReadOnly(True)
        
        # 设置文本选中时的样式，确保蓝底白字效果
        # 参考文档：为选中文本设置高亮效果
        palette = self.palette()
        palette.setColor(QPalette.Highlight, QColor("#3399FF"))
        palette.setColor(QPalette.HighlightedText, QColor("white"))
        self.setPalette(palette)
        
        # 设置文本区域颜色，提高可读性
        palette.setColor(QPalette.Base, QColor("white"))
        self.setPalette(palette)
        
        # 连接信号
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        
        # 更新行号区域宽度
        self.update_line_number_area_width()
        
    def line_number_area_width(self):
        """计算行号区域宽度"""
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
            
        # 每个数字大约8像素宽度，加上边距
        space = 8 * digits + 15
        return space
    
    def update_line_number_area_width(self):
        """更新行号区域宽度"""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
    
    def update_line_number_area(self, rect, dy):
        """更新行号区域"""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), 
                                        self.line_number_area.width(), 
                                        rect.height())
        
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width()
    
    def resizeEvent(self, event):
        """重设大小时重新布局行号区域"""
        super().resizeEvent(event)
        
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), 
                  self.line_number_area_width(), cr.height()
                 )
        )
    
    def line_number_area_paint_event(self, event):
        """绘制行号区域"""
        painter = QPainter(self.line_number_area)
        # 使用浅灰色背景
        painter.fillRect(event.rect(), QColor(240, 240, 240))
        
        # 获取当前可见的文本块
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        
        # 获取字体和字体度量
        font = self.font()
        font_metrics = QFontMetrics(font)
        font_height = font_metrics.height()
        
        # 设置行号字体（与文本区域相同）
        painter.setFont(font)
        painter.setPen(QColor(100, 100, 100))  # 行号使用深灰色
        
        # 绘制所有可见行号
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                # 绘制行号（右对齐）
                number = str(block_number + 1)
                painter.drawText(
                    0, int(top), 
                    self.line_number_area.width() - 8, font_height,
                    Qt.AlignRight | Qt.AlignVCenter, number
                )
            
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

class LogFileViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("日志文件查看器")
        self.setGeometry(100, 100, 1200, 800)
        
        # 设置日志文件路径
        self.log_dir = "src/log"
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 左侧文件列表区域
        left_panel = QFrame()
        left_panel.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        # 文件列表标题
        left_title = QLabel("日志文件")
        left_title.setFont(QFont("Arial", 10, QFont.Bold))
        left_layout.addWidget(left_title)
        
        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setFont(QFont("Arial", 9))
        self.file_list.setSelectionMode(QListWidget.SingleSelection)
        self.file_list.itemClicked.connect(self.on_file_selected)
        left_layout.addWidget(self.file_list)
        
        # 添加提示信息
        info_label = QLabel("点击文件查看内容")
        info_label.setFont(QFont("Arial", 8))
        info_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(info_label)
        
        # 右侧文本显示区域
        right_panel = QFrame()
        right_panel.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 文本显示标题
        self.file_title = QLabel("未选择文件")
        self.file_title.setFont(QFont("Arial", 10, QFont.Bold))
        right_layout.addWidget(self.file_title)
        
        # 使用自定义的文本编辑器（带行号）
        self.text_editor = TextEditorWithLineNumbers()
        
        # 设置文本编辑器属性
        font = QFont("Consolas", 10)  # 使用等宽字体
        self.text_editor.setFont(font)
        self.text_editor.setLineWrapMode(QPlainTextEdit.NoWrap)  # 不自动换行
        self.text_editor.setWordWrapMode(QTextOption.NoWrap)
        
        # 搜索模块
        search_frame = QFrame()
        search_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(5, 5, 5, 5)
        search_layout.setSpacing(5)
        
        # 搜索标签
        search_label = QLabel("搜索:")
        search_layout.addWidget(search_label)
        
        # 搜索输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入搜索内容...")
        self.search_input.returnPressed.connect(self.on_search_enter)
        search_layout.addWidget(self.search_input)
        
        # 匹配信息显示
        self.match_info_label = QLabel("0/0")
        self.match_info_label.setFixedWidth(60)
        self.match_info_label.setAlignment(Qt.AlignCenter)
        search_layout.addWidget(self.match_info_label)
        
        # 导航按钮
        self.up_button = QPushButton("↑")
        self.up_button.setFixedWidth(30)
        self.up_button.clicked.connect(lambda: self.perform_search('up'))
        search_layout.addWidget(self.up_button)
        
        self.down_button = QPushButton("↓")
        self.down_button.setFixedWidth(30)
        self.down_button.clicked.connect(lambda: self.perform_search('down'))
        search_layout.addWidget(self.down_button)
        
        # 选项
        from PySide2.QtWidgets import QCheckBox
        self.case_checkbox = QCheckBox("区分大小写")
        search_layout.addWidget(self.case_checkbox)
        
        self.whole_word_checkbox = QCheckBox("全词匹配")
        search_layout.addWidget(self.whole_word_checkbox)
        
        
        
        # 添加搜索模块到右侧布局
        right_layout.addWidget(self.text_editor)
        right_layout.addWidget(search_frame)
        
        # 添加左右面板到主布局
        main_layout.addWidget(left_panel, 1)  # 左侧面板占1份
        main_layout.addWidget(right_panel, 3)  # 右侧面板占3份
        
        # 搜索相关变量
        self.all_matches = []
        self.current_match_index = -1
        self.first_match_position = 0
        self.previous_search_state = None
        
        # 加载文件列表
        self.load_file_list()
        
    def load_file_list(self):
        """加载src/log目录下的所有日志文件到列表"""
        # 清空文件列表
        self.file_list.clear()
        
        # 检查目录是否存在
        if not os.path.exists(self.log_dir):
            self.show_message(f"目录不存在: {self.log_dir}")
            return
            
        # 获取所有文件
        try:
            for filename in os.listdir(self.log_dir):
                # 只添加日志文件，可以根据需要修改扩展名
                if (filename.endswith('.log') or 
                    filename.endswith('.txt') or 
                    filename.endswith('.LOG')):
                    item = QListWidgetItem(filename)
                    self.file_list.addItem(item)
            
            if self.file_list.count() > 0:
                # 选择第一个文件
                self.file_list.setCurrentRow(0)
                # 自动加载第一个文件
                first_item = self.file_list.item(0)
                if first_item:
                    self.on_file_selected(first_item)
            else:
                self.show_message("没有找到日志文件")
                
        except Exception as e:
            self.show_message(f"读取文件列表时出错: {str(e)}")
    
    def on_file_selected(self, item):
        """当文件被选中时，加载并显示文件内容"""
        if not item:
            return
            
        filename = item.text()
        filepath = os.path.join(self.log_dir, filename)
        
        # 更新文件标题
        self.file_title.setText(f"文件: {filename}")
        
        # 加载文件内容
        self.load_file_content(filepath, filename)
    
    def load_file_content(self, filepath, filename):
        """加载文件内容到文本编辑器"""
        try:
            # 清空当前内容
            self.text_editor.clear()
            
            # 检查文件大小
            file_size = os.path.getsize(filepath)
            if file_size > 10 * 1024 * 1024:  # 10MB
                # 大文件，使用分块读取
                self.load_large_file(filepath, filename, file_size)
            else:
                # 小文件，直接读取
                self.load_small_file(filepath, filename, file_size)
                
        except Exception as e:
            self.show_message(f"读取文件时出错: {str(e)}")
    
    def load_small_file(self, filepath, filename, file_size):
        """加载小文件"""
        try:
            # 使用readlines()读取文件内容
            # 参考文档：《Python数据分析与数据化运营》中读取非结构化文本文件的方法
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # 逐行添加到文本编辑器
            cursor = self.text_editor.textCursor()
            for line in lines:
                cursor.insertText(line)
            
            # 滚动到顶部
            self.text_editor.moveCursor(QTextCursor.Start)
            
            # 更新状态信息
            file_size_str = self.format_file_size(file_size)
            self.file_title.setText(f"文件: {filename} (大小: {file_size_str}, 行数: {len(lines)})")
            
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试其他编码
            try:
                with open(filepath, 'r', encoding='gbk', errors='ignore') as f:
                    lines = f.readlines()
                
                cursor = self.text_editor.textCursor()
                for line in lines:
                    cursor.insertText(line)
                
                self.text_editor.moveCursor(QTextCursor.Start)
                
                file_size_str = self.format_file_size(file_size)
                self.file_title.setText(f"文件: {filename} (大小: {file_size_str}, 行数: {len(lines)})")
                
            except Exception as e:
                self.show_message(f"解码文件时出错: {str(e)}")
    
    def load_large_file(self, filepath, filename, file_size):
        """加载大文件，使用分块读取"""
        try:
            # 获取文件信息
            file_size_str = self.format_file_size(file_size)
            self.file_title.setText(f"文件: {filename} (大小: {file_size_str}, 正在加载...)")
            
            # 分块读取文件，避免内存占用过高
            chunk_size = 1024 * 1024  # 1MB
            line_count = 0
            
            # 使用文本游标
            cursor = self.text_editor.textCursor()
            
            # 使用readlines(sizehint)方法分块读取
            # 参考文档：python 读写、创建 文件
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                while True:
                    # 读取指定大小的块
                    lines = f.readlines(chunk_size)
                    if not lines:
                        break
                    
                    # 添加行到文本编辑器
                    for line in lines:
                        cursor.insertText(line)
                        line_count += 1
                    
                    # 处理UI事件，避免界面冻结
                    QApplication.processEvents()
            
            # 滚动到顶部
            self.text_editor.moveCursor(QTextCursor.Start)
            
            # 更新状态信息
            self.file_title.setText(f"文件: {filename} (大小: {file_size_str}, 行数: {line_count})")
            
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试其他编码
            try:
                cursor = self.text_editor.textCursor()
                line_count = 0
                
                with open(filepath, 'r', encoding='gbk', errors='ignore') as f:
                    while True:
                        lines = f.readlines(chunk_size)
                        if not lines:
                            break
                        
                        for line in lines:
                            cursor.insertText(line)
                            line_count += 1
                        
                        QApplication.processEvents()
                
                self.text_editor.moveCursor(QTextCursor.Start)
                
                self.file_title.setText(f"文件: {filename} (大小: {file_size_str}, 行数: {line_count})")
                
            except Exception as e:
                self.show_message(f"解码大文件时出错: {str(e)}")
    
    def format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    
    def show_message(self, message):
        """显示消息"""
        self.file_title.setText(message)
        self.text_editor.clear()
        cursor = self.text_editor.textCursor()
        cursor.insertText(message)
    
    def on_search_enter(self):
        """处理搜索框回车键事件"""
        self.perform_search()
    
    def perform_search(self, direction='down'):
        """执行搜索"""
        search_text = self.search_input.text().strip()
        if not search_text:
            return
        
        case_sensitive = self.case_checkbox.isChecked()
        whole_word = self.whole_word_checkbox.isChecked()
        
        # 检查搜索词或选项是否改变
        if not self.previous_search_state or (
            search_text != self.previous_search_state['text'] or
            case_sensitive != self.previous_search_state['case'] or
            whole_word != self.previous_search_state['whole_word']
        ):
            # 重置搜索起始位置
            self.first_match_position = 0
            # 保存当前搜索状态
            self.previous_search_state = {
                'text': search_text,
                'case': case_sensitive,
                'whole_word': whole_word
            }
            # 执行新的搜索
            self._search_text(search_text, case_sensitive, whole_word, direction)
        elif self.all_matches:
            # 如果搜索词和选项未改变且已有匹配结果，导航到下一个/上一个匹配项
            if direction == 'down':
                self.navigate_next()
            else:
                self.navigate_previous()
        else:
            # 如果搜索词和选项未改变但没有匹配结果，执行新的搜索
            self._search_text(search_text, case_sensitive, whole_word, direction)
    
    def _search_text(self, search_text, case_sensitive, whole_word, direction):
        """搜索文本并高亮匹配项"""
        # 清除之前的高亮
        self.clear_highlights()
        
        # 获取文本内容
        text = self.text_editor.toPlainText()
        if not text:
            self.match_info_label.setText("0/0")
            return
        
        # 构建正则表达式
        flags = 0 if case_sensitive else re.IGNORECASE
        if whole_word:
            pattern = r'\b' + re.escape(search_text) + r'\b'
        else:
            pattern = re.escape(search_text)
        
        try:
            regex = re.compile(pattern, flags)
        except re.error:
            self.match_info_label.setText("0/0")
            return
        
        # 查找所有匹配项
        self.all_matches = []
        for match in regex.finditer(text):
            self.all_matches.append({
                'start': match.start(),
                'end': match.end()
            })
        
        # 更新匹配信息标签
        if not self.all_matches:
            self.match_info_label.setText("0/0")
            return
        
        # 根据搜索方向定位匹配项
        if direction == 'up':
            # 向上搜索，定位到最后一个匹配项
            self.current_match_index = len(self.all_matches) - 1
        else:
            # 向下搜索，定位到第一个匹配项
            self.current_match_index = 0
        
        # 高亮显示当前匹配项
        self.highlight_current_match()
        
    def navigate_previous(self):
        """导航到上一个匹配项"""
        if self.all_matches:
            self.current_match_index = (self.current_match_index - 1) % len(self.all_matches)
            self.highlight_current_match()
    
    def navigate_next(self):
        """导航到下一个匹配项"""
        if self.all_matches:
            self.current_match_index = (self.current_match_index + 1) % len(self.all_matches)
            self.highlight_current_match()
    
    def highlight_current_match(self):
        """高亮显示当前匹配项"""
        if 0 <= self.current_match_index < len(self.all_matches):
            # 清除所有旧高亮
            self.clear_highlights()
            
            match = self.all_matches[self.current_match_index]
            
            # 创建文本光标
            cursor = self.text_editor.textCursor()
            
            # 选择匹配文本并应用高亮
            cursor.setPosition(match['start'])
            cursor.setPosition(match['end'], QTextCursor.KeepAnchor)
            
            # 创建高亮格式
            from PySide2.QtGui import QTextCharFormat, QBrush
            highlight_format = QTextCharFormat()
            highlight_format.setBackground(QBrush(QColor(144, 238, 144)))  # 浅绿色背景
            
            # 应用高亮
            cursor.setCharFormat(highlight_format)
            
            # 滚动到匹配位置
            cursor.setPosition(match['start'])
            self.text_editor.setTextCursor(cursor)
            self.text_editor.ensureCursorVisible()
            
            # 更新匹配信息标签
            current_match = self.current_match_index + 1
            total_matches = len(self.all_matches)
            self.match_info_label.setText(f"{current_match}/{total_matches}")
    
    def clear_highlights(self):
        """清除所有高亮"""
        # 获取当前文本
        current_text = self.text_editor.toPlainText()
        
        # 重置为纯文本，清除所有格式
        self.text_editor.setPlainText(current_text)

if __name__ == "__main__":
    # 设置高DPI支持
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # 使用Fusion风格，更加现代化
    
    # 设置应用程序信息
    app.setApplicationName("日志文件查看器")
    app.setOrganizationName("MyCompany")
    
    # 检查日志目录
    if not os.path.exists("src/log"):
        os.makedirs("src/log", exist_ok=True)
        print("已创建 src/log 目录，请将日志文件放入此目录中")
    
    window = LogFileViewer()
    window.show()
    
    sys.exit(app.exec_())
