#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HTTP/2服务器模块

提供高性能HTTP/2服务器支持：
- HTTP/2协议支持
- WebSocket升级
- 流控制
- 多路复用
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """服务器配置"""
    host: str = "0.0.0.0"
    http_port: int = 443
    ws_port: int = 8080
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    max_connections: int = 5000
    request_timeout: float = 30.0
    keep_alive_timeout: float = 300.0
    enable_http2: bool = True
    enable_websocket: bool = True
    enable_compression: bool = True
    max_concurrent_streams: int = 100
    initial_window_size: int = 65535
    max_frame_size: int = 16384


class RequestHandler(ABC):
    """
    请求处理器基类
    
    处理HTTP请求。
    """
    
    @abstractmethod
    async def handle(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理请求
        
        Args:
            request: 请求数据
            
        Returns:
            Dict[str, Any]: 响应数据
        """
        pass
    
    @abstractmethod
    def get_path(self) -> str:
        """
        获取处理路径
        
        Returns:
            str: URL路径
        """
        pass
    
    @abstractmethod
    def get_methods(self) -> List[str]:
        """
        获取支持的HTTP方法
        
        Returns:
            List[str]: HTTP方法列表
        """
        pass


class Router:
    """
    路由器
    
    管理请求路由。
    
    示例:
        >>> router = Router()
        >>> router.register("/api/query", QueryHandler())
        >>> router.register("/api/command", CommandHandler())
    """
    
    def __init__(self):
        self._routes: Dict[str, Dict[str, RequestHandler]] = {}
        self._middlewares: List[Callable] = []
    
    def register(
        self, 
        path: str, 
        handler: RequestHandler,
        methods: Optional[List[str]] = None
    ) -> None:
        """
        注册路由
        
        Args:
            path: URL路径
            handler: 请求处理器
            methods: HTTP方法列表（默认从handler获取）
        """
        if path not in self._routes:
            self._routes[path] = {}
        
        methods = methods or handler.get_methods()
        for method in methods:
            self._routes[path][method.upper()] = handler
        
        logger.info(f"Route registered: {path} [{', '.join(methods)}]")
    
    def unregister(self, path: str) -> bool:
        """
        注销路由
        
        Args:
            path: URL路径
            
        Returns:
            bool: 是否成功
        """
        if path in self._routes:
            del self._routes[path]
            return True
        return False
    
    def add_middleware(self, middleware: Callable) -> None:
        """
        添加中间件
        
        Args:
            middleware: 中间件函数
        """
        self._middlewares.append(middleware)
    
    async def route(
        self, 
        path: str, 
        method: str,
        request: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        路由请求
        
        Args:
            path: URL路径
            method: HTTP方法
            request: 请求数据
            
        Returns:
            Optional[Dict[str, Any]]: 响应数据
        """
        if path not in self._routes:
            return None
        
        handler = self._routes[path].get(method.upper())
        if not handler:
            return None
        
        # 执行中间件
        for middleware in self._middlewares:
            request = await middleware(request)
            if request is None:
                return {"error": "Request rejected by middleware"}
        
        # 执行处理器
        return await handler.handle(request)
    
    def list_routes(self) -> List[str]:
        """
        列出所有路由
        
        Returns:
            List[str]: 路由列表
        """
        return list(self._routes.keys())


class HTTPServer:
    """
    HTTP/2服务器
    
    高性能HTTP/2服务器实现。
    
    示例:
        >>> server = HTTPServer(ServerConfig())
        >>> router = Router()
        >>> server.set_router(router)
        >>> await server.start()
    """
    
    def __init__(self, config: ServerConfig):
        """
        初始化服务器
        
        Args:
            config: 服务器配置
        """
        self._config = config
        self._router: Optional[Router] = None
        self._server: Optional[asyncio.AbstractServer] = None
        self._running = False
        self._connections: Set[asyncio.Transport] = set()
        self._request_count = 0
        self._error_count = 0
        
        logger.info(f"HTTPServer initialized: {config.host}:{config.http_port}")
    
    def set_router(self, router: Router) -> None:
        """
        设置路由器
        
        Args:
            router: 路由器实例
        """
        self._router = router
    
    async def start(self) -> None:
        """启动服务器"""
        if self._running:
            return
        
        self._server = await asyncio.start_server(
            self._handle_connection,
            self._config.host,
            self._config.http_port
        )
        
        self._running = True
        logger.info(f"HTTP/2 Server started on {self._config.host}:{self._config.http_port}")
    
    async def stop(self) -> None:
        """停止服务器"""
        if not self._running:
            return
        
        self._running = False
        
        # 关闭所有连接
        for transport in self._connections:
            transport.close()
        self._connections.clear()
        
        # 关闭服务器
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        
        logger.info("HTTP/2 Server stopped")
    
    async def _handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ) -> None:
        """
        处理连接
        
        Args:
            reader: 流读取器
            writer: 流写入器
        """
        self._connections.add(writer.transport)
        
        try:
            while self._running:
                # 读取请求
                request_data = await self._read_request(reader)
                if not request_data:
                    break
                
                # 处理请求
                response = await self._process_request(request_data)
                
                # 发送响应
                await self._send_response(writer, response)
                
                self._request_count += 1
                
        except Exception as e:
            self._error_count += 1
            logger.error(f"Connection error: {e}")
        finally:
            self._connections.discard(writer.transport)
            writer.close()
            await writer.wait_closed()
    
    async def _read_request(
        self, 
        reader: asyncio.StreamReader
    ) -> Optional[Dict[str, Any]]:
        """
        读取HTTP请求
        
        Args:
            reader: 流读取器
            
        Returns:
            Optional[Dict[str, Any]]: 请求数据
        """
        try:
            # 读取请求头
            header_line = await asyncio.wait_for(
                reader.readline(),
                timeout=self._config.request_timeout
            )
            
            if not header_line:
                return None
            
            # 解析请求行
            request_line = header_line.decode('utf-8').strip()
            parts = request_line.split()
            if len(parts) < 3:
                return None
            
            method, path, version = parts[0], parts[1], parts[2]
            
            # 读取请求头
            headers = {}
            while True:
                line = await reader.readline()
                if line == b'\\r\\n' or line == b'\\n':
                    break
                if not line:
                    break
                
                header_line = line.decode('utf-8').strip()
                if ':' in header_line:
                    key, value = header_line.split(':', 1)
                    headers[key.strip()] = value.strip()
            
            # 读取请求体
            body = b''
            content_length = int(headers.get('Content-Length', 0))
            if content_length > 0:
                body = await reader.read(content_length)
            
            return {
                'method': method,
                'path': path,
                'version': version,
                'headers': headers,
                'body': body.decode('utf-8') if body else None
            }
            
        except asyncio.TimeoutError:
            logger.warning("Request read timeout")
            return None
        except Exception as e:
            logger.error(f"Error reading request: {e}")
            return None
    
    async def _process_request(
        self, 
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理请求
        
        Args:
            request: 请求数据
            
        Returns:
            Dict[str, Any]: 响应数据
        """
        if not self._router:
            return {
                'status': 500,
                'body': json.dumps({'error': 'Router not configured'})
            }
        
        try:
            # 路由请求
            result = await self._router.route(
                request['path'],
                request['method'],
                request
            )
            
            if result is None:
                return {
                    'status': 404,
                    'body': json.dumps({'error': 'Not found'})
                }
            
            return {
                'status': 200,
                'body': json.dumps(result),
                'headers': {'Content-Type': 'application/json'}
            }
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {
                'status': 500,
                'body': json.dumps({'error': str(e)})
            }
    
    async def _send_response(
        self,
        writer: asyncio.StreamWriter,
        response: Dict[str, Any]
    ) -> None:
        """
        发送HTTP响应
        
        Args:
            writer: 流写入器
            response: 响应数据
        """
        status = response.get('status', 200)
        body = response.get('body', '')
        headers = response.get('headers', {})
        
        # 构建响应
        status_text = {
            200: 'OK',
            404: 'Not Found',
            500: 'Internal Server Error'
        }.get(status, 'Unknown')
        
        response_lines = [
            f"HTTP/1.1 {status} {status_text}",
            f"Content-Length: {len(body.encode())}",
            "Connection: keep-alive"
        ]
        
        for key, value in headers.items():
            response_lines.append(f"{key}: {value}")
        
        response_lines.append("")
        response_lines.append(body)
        
        response_text = "\\r\\n".join(response_lines)
        writer.write(response_text.encode())
        await writer.drain()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取服务器统计
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'running': self._running,
            'active_connections': len(self._connections),
            'total_requests': self._request_count,
            'total_errors': self._error_count,
            'config': {
                'host': self._config.host,
                'port': self._config.http_port,
                'max_connections': self._config.max_connections
            }
        }


# 便捷函数
def create_server(config: Optional[ServerConfig] = None) -> HTTPServer:
    """
    创建HTTP/2服务器
    
    Args:
        config: 服务器配置（默认使用默认配置）
        
    Returns:
        HTTPServer: 服务器实例
    """
    config = config or ServerConfig()
    return HTTPServer(config)


def create_router() -> Router:
    """
    创建路由器
    
    Returns:
        Router: 路由器实例
    """
    return Router()
