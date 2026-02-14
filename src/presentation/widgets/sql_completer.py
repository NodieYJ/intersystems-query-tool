#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SQL 智能补全组件

支持 SQL 关键字、表名、列名的智能补全
基于 PySide2 QCompleter 实现
"""

import re
import time
import logging
from typing import List, Optional, Tuple

from PySide2.QtWidgets import QCompleter, QTextEdit
from PySide2.QtCore import Qt, QStringListModel

from presentation.widgets.sql_keyword_provider import SQLKeywordProvider, get_keyword_provider
from business.services.metadata_cache_service import LocalMetadataCache, get_metadata_cache

logger = logging.getLogger(__name__)


class SQLCompleter(QCompleter):
    """
    SQL 智能补全器
    
    功能:
    - SQL 关键字补全
    - 表名补全（基于本地缓存的元数据）
    - 列名补全（基于上下文）
    - 上下文感知（根据当前位置提供合适的建议）
    """
    
    # 类级别编译的正则表达式（性能优化）
    _TABLE_PATTERNS = [
        re.compile(r'\bFROM\s+[\w.]*$', re.IGNORECASE),
        re.compile(r'\bJOIN\s+[\w.]*$', re.IGNORECASE),
        re.compile(r'\bINTO\s+[\w.]*$', re.IGNORECASE),
        re.compile(r'\bTABLE\s+[\w.]*$', re.IGNORECASE),
        re.compile(r'\bUPDATE\s+[\w.]*$', re.IGNORECASE),
        re.compile(r'\bDELETE\s+FROM\s+[\w.]*$', re.IGNORECASE)
    ]
    
    _COLUMN_PATTERNS = [
        re.compile(r'\bSELECT\s+[\w\s,.]*$', re.IGNORECASE),
        re.compile(r'\bWHERE\s+[\w\s=<>!]*$', re.IGNORECASE),
        re.compile(r'\bGROUP\s+BY\s+[\w\s,]*$', re.IGNORECASE),
        re.compile(r'\bORDER\s+BY\s+[\w\s,]*$', re.IGNORECASE),
        re.compile(r'\bHAVING\s+[\w\s=<>!]*$', re.IGNORECASE),
        re.compile(r'\bSET\s+[\w\s,=]*$', re.IGNORECASE)
    ]
    
    _TABLE_NAME_PATTERNS = [
        re.compile(r'\bFROM\s+(\w+)', re.IGNORECASE),
        re.compile(r'\bJOIN\s+(\w+)', re.IGNORECASE),
        re.compile(r'\bUPDATE\s+(\w+)', re.IGNORECASE),
        re.compile(r'\bINTO\s+(\w+)', re.IGNORECASE)
    ]
    
    # 缓存配置
    _CACHE_TTL_SECONDS = 300  # 5分钟缓存过期
    _MAX_SUGGESTIONS = 20

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
        
        # 缓存相关属性（性能优化）
        self._table_cache: Optional[List[Tuple]] = None
        self._cache_timestamp: float = 0
        self._cache_connection_id: Optional[str] = None

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
        获取表名建议（使用缓存优化）
        
        Args:
            prefix: 前缀
            
        Returns:
            格式化的表名建议列表
        """
        # 使用缓存获取所有表，然后本地过滤（性能优化）
        try:
            all_tables = self._get_cached_tables()
        except Exception as e:
            logger.error(f"Failed to get cached tables: {e}")
            return []
        
        # 本地过滤匹配前缀的表
        prefix_upper = prefix.upper()
        suggestions = []
        
        for table_info in all_tables:
            # table_info: (schema_name, table_name, table_type)
            if len(table_info) >= 3:
                schema_name, name, type_ = table_info[0], table_info[1], table_info[2]
                if name.upper().startswith(prefix_upper):
                    display = f"{name} ({type_})"
                    suggestions.append(display)
                    
                    if len(suggestions) >= 10:  # 限制结果数量
                        break
        
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
        # 使用类级别编译的正则表达式（性能优化）
        return any(pattern.search(context) for pattern in self._TABLE_PATTERNS)

    def _needs_column_name(self, context: str) -> bool:
        """
        判断当前上下文是否需要列名
        
        Args:
            context: 当前行上下文
            
        Returns:
            是否需要列名
        """
        # 使用类级别编译的正则表达式（性能优化）
        return any(pattern.search(context) for pattern in self._COLUMN_PATTERNS)

    def _extract_table_name(self, context: str) -> Optional[str]:
        """
        从上下文中提取表名
        
        Note:
            当前仅支持简单的表名提取
            不支持：子查询、表别名、CTE等复杂SQL
        
        Args:
            context: 当前行上下文
            
        Returns:
            表名，如果没有找到则返回 None
        """
        # 使用类级别编译的正则表达式（性能优化）
        for pattern in self._TABLE_NAME_PATTERNS:
            match = pattern.search(context)
            if match:
                return match.group(1)
        
        return None
    
    def _get_cached_tables(self) -> List[Tuple]:
        """
        获取缓存的表列表（带缓存机制）
        
        Returns:
            表元组列表
        """
        current_time = time.time()
        
        # 检查缓存是否有效（5分钟内且连接ID未变）
        if (self._table_cache is not None and 
            self._cache_connection_id == self.connection_id and
            current_time - self._cache_timestamp < self._CACHE_TTL_SECONDS):
            return self._table_cache
        
        # 刷新缓存
        try:
            self._table_cache = self.metadata_cache.get_all_tables(self.connection_id)
            self._cache_timestamp = current_time
            self._cache_connection_id = self.connection_id
            logger.debug(f"Refreshed table cache for {self.connection_id}: {len(self._table_cache)} tables")
        except Exception as e:
            logger.error(f"Failed to get table list: {e}")
            return []
        
        return self._table_cache
    
    def clear_cache(self):
        """清除表列表缓存"""
        self._table_cache = None
        self._cache_timestamp = 0
        self._cache_connection_id = None
        logger.debug("Table cache cleared")
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
