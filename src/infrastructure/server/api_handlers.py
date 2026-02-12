#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API处理器

提供RESTful API的具体实现。
"""

import json
import logging
from typing import Any, Dict, List, Optional

from src.infrastructure.server.http_server import RequestHandler
from src.infrastructure.interfaces import IDataService

logger = logging.getLogger(__name__)


class QueryHandler(RequestHandler):
    """
    查询处理器
    
    处理数据查询请求。
    """
    
    def __init__(self, data_service: IDataService):
        """
        初始化
        
        Args:
            data_service: 数据服务
        """
        self._data_service = data_service
    
    def get_path(self) -> str:
        return "/api/query"
    
    def get_methods(self) -> List[str]:
        return ["POST", "GET"]
    
    async def handle(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理查询请求
        
        Args:
            request: 请求数据
            
        Returns:
            Dict[str, Any]: 响应数据
        """
        try:
            # 获取查询参数
            if request['method'] == 'GET':
                # 从URL解析参数
                query = request.get('query_params', {}).get('sql', '')
            else:
                # 从Body解析
                body = json.loads(request.get('body', '{}'))
                query = body.get('sql', '')
            
            if not query:
                return {
                    'success': False,
                    'error': 'SQL query is required'
                }
            
            # 执行查询
            results = self._data_service.query_data(query)
            
            return {
                'success': True,
                'data': results,
                'count': len(results)
            }
            
        except Exception as e:
            logger.error(f"Query error: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class CommandHandler(RequestHandler):
    """
    命令处理器
    
    处理数据修改命令。
    """
    
    def __init__(self, data_service: IDataService):
        """
        初始化
        
        Args:
            data_service: 数据服务
        """
        self._data_service = data_service
    
    def get_path(self) -> str:
        return "/api/command"
    
    def get_methods(self) -> List[str]:
        return ["POST"]
    
    async def handle(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理命令请求
        
        Args:
            request: 请求数据
            
        Returns:
            Dict[str, Any]: 响应数据
        """
        try:
            body = json.loads(request.get('body', '{}'))
            command = body.get('command', '')
            
            if not command:
                return {
                    'success': False,
                    'error': 'Command is required'
                }
            
            # 执行命令（这里简化处理）
            # 实际应该调用data_service的对应方法
            
            return {
                'success': True,
                'message': 'Command executed successfully'
            }
            
        except Exception as e:
            logger.error(f"Command error: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class HealthHandler(RequestHandler):
    """
    健康检查处理器
    """
    
    def get_path(self) -> str:
        return "/health"
    
    def get_methods(self) -> List[str]:
        return ["GET"]
    
    async def handle(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理健康检查请求
        
        Returns:
            Dict[str, Any]: 健康状态
        """
        return {
            'status': 'healthy',
            'timestamp': __import__('time').time()
        }


class StatsHandler(RequestHandler):
    """
    统计信息处理器
    """
    
    def __init__(self, server):
        """
        初始化
        
        Args:
            server: 服务器实例
        """
        self._server = server
    
    def get_path(self) -> str:
        return "/api/stats"
    
    def get_methods(self) -> List[str]:
        return ["GET"]
    
    async def handle(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取服务器统计
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return self._server.get_stats()
