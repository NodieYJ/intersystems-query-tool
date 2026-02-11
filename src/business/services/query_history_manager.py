#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
查询历史管理器模块

用于管理SQL查询历史记录的存储、检索和管理
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class QueryHistoryManager:
    """
    查询历史管理器
    
    负责SQL查询历史记录的保存、加载、查询和管理
    """
    
    def __init__(self, history_file: Optional[str] = None, max_history: int = 100):
        """
        初始化查询历史管理器
        
        Args:
            history_file: 历史记录文件路径，默认为 ~/.app_configs/query_history.json
            max_history: 最大历史记录数量，默认100条
        """
        if history_file is None:
            # 默认存储在用户主目录下的 .app_configs 文件夹中
            home_dir = Path.home()
            config_dir = home_dir / '.app_configs'
            config_dir.mkdir(exist_ok=True)
            self.history_file = config_dir / 'query_history.json'
        else:
            self.history_file = Path(history_file)
        
        self.max_history = max_history
        self.history: List[Dict[str, Any]] = []
        self._load_history()
        
        logger.info(f"查询历史管理器初始化完成，历史文件: {self.history_file}")
    
    def _load_history(self) -> None:
        """
        加载历史记录
        """
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
                logger.info(f"加载了 {len(self.history)} 条历史记录")
            else:
                self.history = []
                logger.info("历史记录文件不存在，创建新的历史记录列表")
        except Exception as e:
            logger.error(f"加载历史记录失败: {str(e)}")
            self.history = []
    
    def _save_history(self) -> None:
        """
        保存历史记录到文件
        """
        try:
            # 确保目录存在
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"历史记录已保存，共 {len(self.history)} 条")
        except Exception as e:
            logger.error(f"保存历史记录失败: {str(e)}")
    
    def add_history(
        self, 
        sql: str, 
        execution_time_ms: float = 0, 
        row_count: int = 0,
        success: bool = True,
        error_message: str = ""
    ) -> None:
        """
        添加一条历史记录
        
        Args:
            sql: SQL语句
            execution_time_ms: 执行时间（毫秒）
            row_count: 返回行数
            success: 是否执行成功
            error_message: 错误信息（如果失败）
        """
        # 清理SQL语句（去除首尾空白）
        sql = sql.strip()
        
        # 忽略空SQL
        if not sql:
            return
        
        # 创建历史记录条目
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'sql': sql,
            'execution_time_ms': execution_time_ms,
            'row_count': row_count,
            'success': success,
            'error_message': error_message
        }
        
        # 检查是否已有相同的SQL（在最近10条内），如果有则更新
        for i, entry in enumerate(self.history[:10]):
            if entry['sql'] == sql:
                # 移除旧的记录
                self.history.pop(i)
                break
        
        # 添加到列表开头（最新的在前面）
        self.history.insert(0, history_entry)
        
        # 限制历史记录数量
        if len(self.history) > self.max_history:
            self.history = self.history[:self.max_history]
        
        # 保存到文件
        self._save_history()
        
        logger.info(f"添加历史记录: {sql[:50]}...")
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取历史记录列表
        
        Args:
            limit: 限制返回的数量，None表示返回全部
        
        Returns:
            历史记录列表
        """
        if limit is None:
            return self.history.copy()
        return self.history[:limit]
    
    def search_history(self, keyword: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        搜索历史记录
        
        Args:
            keyword: 搜索关键词
            case_sensitive: 是否区分大小写
        
        Returns:
            匹配的历史记录列表
        """
        if not keyword:
            return self.history.copy()
        
        results = []
        for entry in self.history:
            sql = entry['sql']
            if not case_sensitive:
                sql = sql.lower()
                keyword = keyword.lower()
            
            if keyword in sql:
                results.append(entry)
        
        return results
    
    def clear_history(self) -> None:
        """
        清空所有历史记录
        """
        self.history = []
        self._save_history()
        logger.info("历史记录已清空")
    
    def delete_history_entry(self, index: int) -> bool:
        """
        删除指定索引的历史记录
        
        Args:
            index: 历史记录索引
        
        Returns:
            是否删除成功
        """
        try:
            if 0 <= index < len(self.history):
                deleted_entry = self.history.pop(index)
                self._save_history()
                logger.info(f"删除历史记录: {deleted_entry['sql'][:50]}...")
                return True
            return False
        except Exception as e:
            logger.error(f"删除历史记录失败: {str(e)}")
            return False
    
    def get_history_count(self) -> int:
        """
        获取历史记录数量
        
        Returns:
            历史记录数量
        """
        return len(self.history)
    
    def get_formatted_history_text(self, entry: Dict[str, Any]) -> str:
        """
        获取格式化的历史记录文本（用于显示）
        
        Args:
            entry: 历史记录条目
        
        Returns:
            格式化后的文本
        """
        timestamp = entry.get('timestamp', '')
        sql = entry.get('sql', '')
        execution_time = entry.get('execution_time_ms', 0)
        row_count = entry.get('row_count', 0)
        success = entry.get('success', True)
        
        # 解析时间戳
        try:
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            time_str = timestamp
        
        # 截断SQL语句（如果太长）
        sql_display = sql[:80] + '...' if len(sql) > 80 else sql
        
        # 构建状态标识
        status = "成功" if success else "失败"
        
        return f"[{time_str}] {status} | {execution_time:.0f}ms | {row_count}行 | {sql_display}"


# 单例模式
_query_history_manager: Optional[QueryHistoryManager] = None


def get_query_history_manager() -> QueryHistoryManager:
    """
    获取查询历史管理器实例（单例）
    
    Returns:
        QueryHistoryManager实例
    """
    global _query_history_manager
    if _query_history_manager is None:
        _query_history_manager = QueryHistoryManager()
    return _query_history_manager


def reset_query_history_manager() -> None:
    """
    重置查询历史管理器实例（主要用于测试）
    """
    global _query_history_manager
    _query_history_manager = None
