#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SQL 关键字提供者模块

提供 SQL 关键字、函数名的智能提示功能
"""

import json
import os
from typing import List, Dict


class SQLKeywordProvider:
    """
    SQL 关键字提供者
    
    从本地 JSON 文件加载 SQL 关键字，提供基于前缀的智能提示
    """

    def __init__(self, keywords_file: str = None):
        """
        初始化关键字提供者
        
        Args:
            keywords_file: 关键字 JSON 文件路径，默认为 resources/data/sql_keywords.json
        """
        if keywords_file is None:
            # 计算默认路径
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            keywords_file = os.path.join(base_dir, 'resources', 'data', 'sql_keywords.json')
        
        self.keywords_file = keywords_file
        self.all_keywords = self._load_keywords()

    def _load_keywords(self) -> List[str]:
        """
        从 JSON 文件加载关键字
        
        Returns:
            排序后的关键字列表
        """
        try:
            with open(self.keywords_file, 'r', encoding='utf-8') as f:
                data: Dict[str, List[str]] = json.load(f)
            
            all_keywords = []
            for category_keywords in data.values():
                all_keywords.extend(category_keywords)
            
            return sorted(set(all_keywords))
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # 如果文件不存在或解析失败，返回基础关键字
            return [
                "SELECT", "INSERT", "UPDATE", "DELETE",
                "FROM", "WHERE", "GROUP BY", "ORDER BY",
                "JOIN", "LEFT JOIN", "RIGHT JOIN",
                "AND", "OR", "NOT", "IN", "EXISTS",
                "COUNT", "SUM", "AVG", "MAX", "MIN"
            ]

    def get_suggestions(self, prefix: str) -> List[str]:
        """
        根据前缀获取关键字建议
        
        Args:
            prefix: 用户输入的前缀（大小写不敏感）
            
        Returns:
            匹配的关键字列表
        """
        if not prefix:
            return self.all_keywords
        
        prefix_upper = prefix.upper()
        return [kw for kw in self.all_keywords if kw.startswith(prefix_upper)]

    def get_keywords_by_category(self, category: str) -> List[str]:
        """
        获取特定类别的关键字
        
        Args:
            category: 类别名称 (DML, DDL, CLAUSES, JOINS, OPERATORS, FUNCTIONS, DATA_TYPES)
            
        Returns:
            该类别下的关键字列表
        """
        try:
            with open(self.keywords_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get(category, [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []


# 单例模式，全局共享
_keyword_provider_instance = None


def get_keyword_provider() -> SQLKeywordProvider:
    """
    获取 SQLKeywordProvider 单例
    
    Returns:
        SQLKeywordProvider 实例
    """
    global _keyword_provider_instance
    if _keyword_provider_instance is None:
        _keyword_provider_instance = SQLKeywordProvider()
    return _keyword_provider_instance
