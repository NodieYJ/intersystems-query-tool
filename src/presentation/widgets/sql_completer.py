#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SQL 智能补全组件

支持 SQL 关键字、表名、列名的智能补全
基于 PySide2 QCompleter 实现
"""

import re
from typing import List, Optional

from PySide2.QtWidgets import QCompleter, QTextEdit
from PySide2.QtCore import Qt, QStringListModel

from presentation.widgets.sql_keyword_provider import SQLKeywordProvider, get_keyword_provider
from business.services.metadata_cache_service import LocalMetadataCache, get_metadata_cache


class SQLCompleter(QCompleter):
    """
    SQL 智能补全器
    
    功能:
    - SQL 关键字补全
    - 表名补全（基于本地缓存的元数据）
    - 列名补全（基于上下文）
    - 上下文感知（根据当前位置提供合适的建议）
    """

    def __init__(self, parent: QTextEdit, connection_id: str = 'default'):
        """
        初始化 SQL 补全器
        
        Args:
            parent: 父文本编辑器
            connection_id: 数据库连接标识符
        """
        super().__init__(parent)
        
        self.text_edit = parent
        self.connection_id = connection_id
        
        # 初始化提供者
        self.keyword_provider = get_keyword_provider()
        self.metadata_cache = get_metadata_cache()
        
        # 设置模型
        self.model = QStringListModel()
        self.setModel(self.model)
        
        # 配置补全器
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompletionMode(QCompleter.PopupCompletion)
        self.setFilterMode(Qt.MatchStartsWith)
        
        # 设置最大显示数量
        self.setMaxVisibleItems(10)
        
        # 连接信号
        self.activated.connect(self._insert_completion)

    def update_connection(self, connection_id: str):
        """
        更新连接标识符
        
        Args:
            connection_id: 新的连接标识符
        """
        self.connection_id = connection_id

    def refresh_suggestions(self, force: bool = False):
        """
        刷新补全建议
        
        在文本变化时调用，根据当前输入和上下文更新建议列表
        
        Args:
            force: 是否强制刷新（忽略最小触发长度）
        """
        cursor = self.text_edit.textCursor()
        current_line = cursor.block().text()[:cursor.positionInBlock()]
        
        # 获取当前单词
        word = self._get_current_word(current_line)
        
        # 最少 2 个字符才触发（除非强制）
        if len(word) < 2 and not force:
            return
        
        # 获取补全建议
        suggestions = self._get_suggestions(word, current_line)
        
        if suggestions:
            self.model.setStringList(suggestions)
            # 计算补全位置
            rect = self.text_edit.cursorRect()
            self.complete(rect)

    def _get_current_word(self, line: str) -> str:
        """
        获取当前正在输入的单词
        
        Args:
            line: 当前行文本
            
        Returns:
            当前单词（可能包含点号，如 table.column）
        """
        # 从后往前找，匹配单词字符或点号
        match = re.search(r'[\w.]+$', line)
        return match.group(0) if match else ''

    def _get_suggestions(self, word: str, context: str) -> List[str]:
        """
        根据上下文获取补全建议
        
        Args:
            word: 当前输入的单词
            context: 当前行上下文
            
        Returns:
            建议列表
        """
        suggestions = []
        word_upper = word.upper()
        
        # 检查是否是表名.列名格式
        if '.' in word:
            table_part, col_part = word.rsplit('.', 1)
            columns = self._get_column_suggestions(table_part, col_part)
            suggestions.extend(columns)
        else:
            # 1. SQL 关键字建议
            keywords = self.keyword_provider.get_suggestions(word)
            suggestions.extend(keywords)
            
            # 2. 根据上下文判断是否需要表名
            if self._needs_table_name(context):
                tables = self._get_table_suggestions(word)
                suggestions.extend(tables)
            
            # 3. 根据上下文判断是否需要列名
            elif self._needs_column_name(context):
                table_name = self._extract_table_name(context)
                if table_name:
                    columns = self._get_column_suggestions(table_name, word)
                    suggestions.extend(columns)
        
        return suggestions[:20]  # 限制数量

    def _get_table_suggestions(self, prefix: str) -> List[str]:
        """
        获取表名建议
        
        Args:
            prefix: 前缀
            
        Returns:
            格式化的表名建议列表
        """
        tables = self.metadata_cache.search_tables(
            self.connection_id, prefix, limit=10
        )
        
        suggestions = []
        for schema, name, type_, comment in tables:
            display = f"{name} ({type_})"
            if comment:
                display += f" - {comment[:30]}"
            suggestions.append(display)
        
        return suggestions

    def _get_column_suggestions(self, table_name: str, prefix: str) -> List[str]:
        """
        获取列名建议
        
        Args:
            table_name: 表名
            prefix: 列名前缀
            
        Returns:
            格式化的列名建议列表
        """
        columns = self.metadata_cache.get_columns(
            self.connection_id, table_name
        )
        
        suggestions = []
        prefix_upper = prefix.upper()
        
        for col_name, col_type, is_nullable, default, comment in columns:
            if col_name.upper().startswith(prefix_upper):
                display = f"{col_name} ({col_type})"
                suggestions.append(display)
        
        return suggestions

    def _needs_table_name(self, context: str) -> bool:
        """
        判断当前上下文是否需要表名
        
        Args:
            context: 当前行上下文
            
        Returns:
            是否需要表名
        """
        patterns = [
            r'\bFROM\s+[\w.]*$',
            r'\bJOIN\s+[\w.]*$',
            r'\bINTO\s+[\w.]*$',
            r'\bTABLE\s+[\w.]*$',
            r'\bUPDATE\s+[\w.]*$',
            r'\bDELETE\s+FROM\s+[\w.]*$'
        ]
        
        context_upper = context.upper()
        return any(re.search(p, context_upper) for p in patterns)

    def _needs_column_name(self, context: str) -> bool:
        """
        判断当前上下文是否需要列名
        
        Args:
            context: 当前行上下文
            
        Returns:
            是否需要列名
        """
        patterns = [
            r'\bSELECT\s+[\w\s,.]*$',
            r'\bWHERE\s+[\w\s=<>!]*$',
            r'\bGROUP\s+BY\s+[\w\s,]*$',
            r'\bORDER\s+BY\s+[\w\s,]*$',
            r'\bHAVING\s+[\w\s=<>!]*$',
            r'\bSET\s+[\w\s,=]*$'
        ]
        
        context_upper = context.upper()
        return any(re.search(p, context_upper) for p in patterns)

    def _extract_table_name(self, context: str) -> Optional[str]:
        """
        从上下文中提取表名
        
        Args:
            context: 当前行上下文
            
        Returns:
            表名，如果没有找到则返回 None
        """
        # 尝试从 FROM 子句提取
        match = re.search(r'\bFROM\s+(\w+)', context, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # 尝试从 JOIN 子句提取
        match = re.search(r'\bJOIN\s+(\w+)', context, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # 尝试从 UPDATE 子句提取
        match = re.search(r'\bUPDATE\s+(\w+)', context, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # 尝试从 INTO 子句提取
        match = re.search(r'\bINTO\s+(\w+)', context, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None

    def _insert_completion(self, completion: str):
        """
        插入选中的补全项
        
        Args:
            completion: 选中的补全文本
        """
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

    def set_metadata(self, tables_data: List[dict]):
        """
        设置元数据（便捷方法）
        
        Args:
            tables_data: 表元数据列表
        """
        self.metadata_cache.update_metadata(self.connection_id, tables_data)
