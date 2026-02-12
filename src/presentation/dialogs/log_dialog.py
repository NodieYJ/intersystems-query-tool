#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志对话框

支持日志查看、搜索、高亮显示、导出等功能
"""

import sys
import os
import re
import logging
from datetime import datetime
from functools import partial  # 添加 partial 导入

# ==========================================================================
# 常量定义
# ==========================================================================

# 默认日志目录
DEFAULT_LOG_DIR = "src/log"

from PySide2.QtWidgets import (QApplication, QDialog, QWidget, QVBoxLayout, 
                               QHBoxLayout, QListWidget, QListWidgetItem, 
                               QLabel, QFrame, QPlainTextEdit, QLineEdit, 
                               QPushButton, QCheckBox, QFileDialog, QMessageBox,
                               QComboBox)
from PySide2.QtCore import Qt, QRect, QSize
from PySide2.QtGui import (QTextCursor, QFont, QTextOption, QColor, QPainter, 
                          QTextFormat, QPalette, QTextCharFormat, QBrush, QSyntaxHighlighter,
                          QTextDocument)

logger = logging.getLogger(__name__)

class LogLevelHighlighter(QSyntaxHighlighter):
    """
    日志级别高亮器
    
    根据日志级别（DEBUG/INFO/WARNING/ERROR）显示不同颜色
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 定义各级别的格式
        self.level_formats = {}
        
        # DEBUG - 灰色
        debug_format = QTextCharFormat()
        debug_format.setForeground(QColor(128, 128, 128))
        self.level_formats['DEBUG'] = debug_format
        
        # INFO - 绿色
        info_format = QTextCharFormat()
        info_format.setForeground(QColor(0, 128, 0))
        self.level_formats['INFO'] = info_format
        
        # WARNING - 橙色
        warning_format = QTextCharFormat()
        warning_format.setForeground(QColor(255, 140, 0))
        warning_format.setFontWeight(QFont.Bold)
        self.level_formats['WARNING'] = warning_format
        
        # ERROR - 红色
        error_format = QTextCharFormat()
        error_format.setForeground(QColor(220, 20, 60))
        error_format.setFontWeight(QFont.Bold)
        self.level_formats['ERROR'] = error_format
        
        # CRITICAL - 深红色 + 背景
        critical_format = QTextCharFormat()
        critical_format.setForeground(QColor(139, 0, 0))
        critical_format.setBackground(QColor(255, 228, 225))
        critical_format.setFontWeight(QFont.Bold)
        self.level_formats['CRITICAL'] = critical_format
        
        # 时间戳格式 - 蓝色
        self.timestamp_format = QTextCharFormat()
        self.timestamp_format.setForeground(QColor(0, 0, 255))
        
    def highlightBlock(self, text):
        """高亮文本块"""
        # 高亮日志级别
        for level, format_obj in self.level_formats.items():
            # 使用正则表达式匹配日志级别（整词匹配）
            pattern = r'\b' + level + r'\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format_obj)
        
        # 高亮时间戳 (YYYY-MM-DD HH:MM:SS 格式)
        timestamp_pattern = r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}'
        for match in re.finditer(timestamp_pattern, text):
            start = match.start()
            length = match.end() - start
            self.setFormat(start, length, self.timestamp_format)


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
    """自定义文本编辑器，带行号显示和日志级别高亮，只读模式允许文本选中"""
    def __init__(self):
        super().__init__()
        self.line_number_area = LineNumberArea(self)
        
        # 设置文本区域为只读，允许选中文本但不允许编辑
        self.setReadOnly(True)
        
        # 设置文本选中时的样式，确保蓝底白字效果
        palette = self.palette()
        palette.setColor(QPalette.Highlight, QColor("#3399FF"))
        palette.setColor(QPalette.HighlightedText, QColor("white"))
        self.setPalette(palette)
        
        # 设置文本区域颜色，提高可读性
        palette.setColor(QPalette.Base, QColor("white"))
        self.setPalette(palette)
        
        # 添加日志级别高亮器
        self.highlighter = LogLevelHighlighter(self.document())
        
        # 连接信号
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        
        # 更新行号区域宽度
        self.update_line_number_area_width()
        
    def line_number_area_width(self):
        """计算行号区域宽度"""
        # 获取最大行号
        max_num = max(1, self.blockCount())
        # 转换为字符串以获取位数
        max_num_str = str(max_num)
        # 使用更保守的估算，确保有足够空间显示行号
        # 每个字符14像素宽度（更大的字符宽度），加上20px边距，确保有足够空间
        space = len(max_num_str) * 14 + 20
        return space
    
    def update_line_number_area_width(self):
        """更新行号区域宽度"""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
    
    def update_line_number_area(self, rect, dy):
        """更新行号区域"""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            # 使用计算出的行号区域宽度进行更新
            line_number_width = self.line_number_area_width()
            self.line_number_area.update(0, rect.y(), 
                                        line_number_width, 
                                        rect.height())
        
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width()
            # 确保行号区域几何设置正确
            cr = self.contentsRect()
            line_number_width = self.line_number_area_width()
            self.line_number_area.setGeometry(
                QRect(cr.left(), cr.top(), 
                      line_number_width, cr.height()
                     )
            )
    
    def resizeEvent(self, event):
        """重设大小时重新布局行号区域"""
        super().resizeEvent(event)
        
        cr = self.contentsRect()
        # 确保行号区域宽度根据计算值设置
        line_number_width = self.line_number_area_width()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), 
                  line_number_width, cr.height()
                 )
        )
        # 同时更新视口边距，确保文本区域位置正确
        self.setViewportMargins(line_number_width, 0, 0, 0)
    
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
        
        # 获取字体
        font = self.font()
        # 计算实际的行高，使用文本块的高度
        line_height = self.blockBoundingRect(block).height()
        
        # 设置行号字体（与文本区域相同）
        painter.setFont(font)
        painter.setPen(QColor(100, 100, 100))  # 行号使用深灰色
        
        # 确保使用正确的行号区域宽度
        line_number_width = self.line_number_area_width()
        
        # 绘制所有可见行号
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                # 绘制行号（右对齐）
                number = str(block_number + 1)
                # 使用文本块的实际高度，确保行号与文本行在同一y轴坐标上
                painter.drawText(
                    0, int(top), 
                    line_number_width - 8, int(line_height),
                    Qt.AlignRight | Qt.AlignVCenter, number
                )
            
            block = block.next()
            if block.isValid():
                line_height = self.blockBoundingRect(block).height()
            top = bottom
            if block.isValid():
                bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

class LogDialog(QDialog):
    """日志对话框"""

    def __init__(self, parent=None):
        """初始化日志对话框

        Args:
            parent: 父窗口
        """
        try:
            logger.debug("开始初始化日志对话框")
            super().__init__(parent)

            self.setWindowTitle("日志")
            # 获取屏幕分辨率
            screen = QApplication.primaryScreen()
            screen_geometry = screen.geometry()
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()
            
            # 计算窗口大小：屏幕宽度的60%，长宽比4:3
            window_width = int(screen_width * 0.6)
            window_height = int(window_width * 3 / 4)
            
            # 确保窗口大小不小于最小尺寸
            min_width = 800
            min_height = 600
            window_width = max(window_width, min_width)
            window_height = max(window_height, min_height)
            
            self.resize(window_width, window_height)
            self.setMinimumSize(min_width, min_height)
            # 去除窗口中的?按钮
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            logger.debug(f"设置日志对话框窗口属性，大小: {window_width}x{window_height}")

            # 主布局
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(5, 5, 5, 5)
            main_layout.setSpacing(5)
            
            # 创建中央部件
            central_widget = QWidget()
            main_layout.addWidget(central_widget)
            
            # 主布局
            main_layout_inner = QHBoxLayout(central_widget)
            main_layout_inner.setContentsMargins(5, 5, 5, 5)
            main_layout_inner.setSpacing(5)
            
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
            
            # 添加导出按钮
            export_btn = QPushButton("导出当前日志")
            export_btn.clicked.connect(self.export_current_log)
            export_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px;")
            left_layout.addWidget(export_btn)
            
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
            self.up_button.clicked.connect(partial(self.perform_search, 'up'))
            search_layout.addWidget(self.up_button)
            
            self.down_button = QPushButton("↓")
            self.down_button.setFixedWidth(30)
            self.down_button.clicked.connect(partial(self.perform_search, 'down'))
            search_layout.addWidget(self.down_button)
            
            # 选项
            self.case_checkbox = QCheckBox("区分大小写")
            search_layout.addWidget(self.case_checkbox)
            
            self.whole_word_checkbox = QCheckBox("全词匹配")
            search_layout.addWidget(self.whole_word_checkbox)
            
            # 添加搜索模块到右侧布局
            right_layout.addWidget(self.text_editor)
            right_layout.addWidget(search_frame)
            
            # 添加左右面板到主布局
            main_layout_inner.addWidget(left_panel, 1)  # 左侧面板占1份
            main_layout_inner.addWidget(right_panel, 3)  # 右侧面板占3份
            
            # 搜索相关变量
            self.all_matches = []
            self.current_match_index = -1
            self.first_match_position = 0
            self.previous_search_state = None

            # 设置日志文件路径（使用常量，支持从配置覆盖）
            self.log_dir = DEFAULT_LOG_DIR

            # 尝试从配置管理器获取日志目录
            try:
                from src.infrastructure.config.config_manager import get_config_manager
                config_dir = get_config_manager().get("paths.log_dir", "")
                if config_dir:
                    self.log_dir = config_dir
            except ImportError:
                pass  # 使用默认值
            
            # 加载文件列表
            self.load_file_list()
            
            logger.debug("日志对话框初始化完成")
        except Exception as e:
            error_msg = f"初始化日志对话框失败: {str(e)}"
            logger.error(error_msg)
            from PySide2.QtWidgets import QMessageBox
            QMessageBox.critical(self, "错误", error_msg)
    
    def load_file_list(self):
        """加载src/log目录下的所有日志文件到列表（倒序排列）"""
        # 清空文件列表
        self.file_list.clear()
        
        # 检查目录是否存在
        if not os.path.exists(self.log_dir):
            self.show_message(f"目录不存在: {self.log_dir}")
            return
            
        # 获取所有文件
        try:
            log_files = []
            for filename in os.listdir(self.log_dir):
                # 只添加日志文件，可以根据需要修改扩展名
                if (filename.endswith('.log') or 
                    filename.endswith('.txt') or 
                    filename.endswith('.LOG')):
                    log_files.append(filename)
            
            # 按文件名倒序排列（最新的日志文件排在前面）
            log_files.sort(reverse=True)
            
            # 添加到列表控件
            for filename in log_files:
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
            error_msg = f"读取文件列表时出错: {str(e)}"
            self.show_message(error_msg)
            logger.error(error_msg, exc_info=True)
    
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
        """
        加载大文件，使用分块读取（异步方式避免阻塞UI）
        """
        # 使用异步方式加载大文件，避免阻塞主线程
        self._start_async_file_load(filepath, filename, file_size)

    def _start_async_file_load(self, filepath, filename, file_size):
        """
        开始异步文件加载
        """
        from PySide2.QtCore import QThread, Signal

        class LargeFileLoader(QThread):
            """大文件异步加载线程"""
            progress = Signal(int)  # 进度百分比
            finished = Signal(str, int)  # 文件内容, 行数
            error = Signal(str)  # 错误信息

            def __init__(self, filepath, chunk_size=1024 * 1024):
                super().__init__()
                self.filepath = filepath
                self.chunk_size = chunk_size
                self.encodings = ['utf-8', 'gbk']

            def run(self):
                """在后台线程中加载文件"""
                content = []
                line_count = 0
                file_size = os.path.getsize(self.filepath)

                for encoding in self.encodings:
                    try:
                        with open(self.filepath, 'r', encoding=encoding, errors='ignore') as f:
                            while True:
                                lines = f.readlines(self.chunk_size)
                                if not lines:
                                    break
                                content.extend(lines)
                                line_count += len(lines)

                                # 发送进度
                                progress = min(100, int(f.tell() / file_size * 100))
                                self.progress.emit(progress)

                        # 成功加载
                        self.finished.emit(''.join(content), line_count)
                        return

                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        self.error.emit(str(e))
                        return

                self.error.emit("无法解码文件")

        # 创建并启动加载线程
        self.file_loader = LargeFileLoader(filepath)
        self.file_loader.progress.connect(self._on_file_load_progress)
        self.file_loader.finished.connect(self._on_file_load_finished)
        self.file_loader.error.connect(self._on_file_load_error)
        self.file_loader.finished.connect(self.file_loader.deleteLater)
        self.file_loader.start()

        # 更新标题
        file_size_str = self.format_file_size(file_size)
        self.file_title.setText(f"文件: {filename} (大小: {file_size_str}, 正在加载...)")

    def _on_file_load_progress(self, progress):
        """文件加载进度回调"""
        self.file_title.setText(f"正在加载... {progress}%")

    def _on_file_load_finished(self, content, line_count):
        """文件加载完成回调"""
        # 清空并设置内容
        self.text_editor.clear()
        cursor = self.text_editor.textCursor()
        cursor.insertText(content)

        # 滚动到顶部
        self.text_editor.moveCursor(QTextCursor.Start)

        # 更新标题
        filename = self.file_list.currentItem().text() if self.file_list.currentItem() else "未知"
        file_size = os.path.getsize(os.path.join(self.log_dir, filename))
        file_size_str = self.format_file_size(file_size)
        self.file_title.setText(f"文件: {filename} (大小: {file_size_str}, 行数: {line_count})")

    def _on_file_load_error(self, error_msg):
        """文件加载错误回调"""
        self.show_message(f"加载文件时出错: {error_msg}")
    
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
    
    def export_current_log(self):
        """
        导出当前显示的日志内容
        """
        try:
            # 获取当前选中的文件
            current_item = self.file_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "警告", "请先选择一个日志文件")
                return
            
            filename = current_item.text()
            source_path = os.path.join(self.log_dir, filename)
            
            # 检查文件是否存在
            if not os.path.exists(source_path):
                QMessageBox.warning(self, "警告", f"文件不存在: {filename}")
                return
            
            # 获取文件大小
            file_size = os.path.getsize(source_path)
            file_size_str = self.format_file_size(file_size)
            
            # 弹出保存对话框
            default_name = f"{os.path.splitext(filename)[0]}_exported_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出日志文件",
                default_name,
                "日志文件 (*.log);;文本文件 (*.txt);;所有文件 (*.*)"
            )
            
            if not file_path:
                return
            
            # 复制文件
            import shutil
            shutil.copy2(source_path, file_path)
            
            QMessageBox.information(
                self,
                "导出成功",
                f"日志文件已成功导出到:\n{file_path}\n\n文件大小: {file_size_str}"
            )
            
            logger.info(f"日志文件已导出: {file_path}")
            
        except Exception as e:
            logger.error(f"导出日志文件失败: {str(e)}")
            QMessageBox.critical(self, "导出失败", f"导出日志文件时出错:\n{str(e)}")
    
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