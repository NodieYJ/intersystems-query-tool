#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WebSocket服务器模块

支持动态连接、大文件传输、进度推送：
- WebSocket连接管理
- 协议协商和升级
- 传输会话管理
- 进度实时推送

依赖: aiohttp (提供WebSocket支持)
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """WebSocket连接状态"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    UPGRADING = "upgrading"
    TRANSFERRING = "transferring"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"


@dataclass
class TransferSession:
    """传输会话"""
    session_id: str
    connection_id: str
    file_name: str
    file_size: int
    chunk_size: int = 65536  # 64KB chunks
    total_chunks: int = 0
    received_chunks: Set[int] = field(default_factory=set)
    checksum: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    def __post_init__(self):
        if self.total_chunks == 0 and self.file_size > 0:
            self.total_chunks = (self.file_size + self.chunk_size - 1) // self.chunk_size
    
    @property
    def progress(self) -> float:
        """计算传输进度"""
        if self.total_chunks == 0:
            return 0.0
        return len(self.received_chunks) / self.total_chunks
    
    @property
    def is_complete(self) -> bool:
        """检查是否传输完成"""
        return len(self.received_chunks) == self.total_chunks
    
    def add_chunk(self, chunk_index: int) -> None:
        """添加已接收的数据块"""
        self.received_chunks.add(chunk_index)
        self.updated_at = time.time()


@dataclass
class ConnectionInfo:
    """WebSocket连接信息"""
    connection_id: str
    client_id: str
    state: ConnectionState = ConnectionState.CONNECTING
    connected_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    remote_addr: Optional[str] = None
    user_agent: Optional[str] = None
    auth_token: Optional[str] = None
    transfer_session: Optional[TransferSession] = None
    
    def update_activity(self) -> None:
        """更新最后活动时间"""
        self.last_activity = time.time()


class WebSocketHandler:
    """
    WebSocket连接处理器
    
    管理单个WebSocket连接的生命周期：
    - 连接建立和认证
    - 消息处理
    - 连接关闭
    """
    
    def __init__(
        self,
        connection_id: str,
        client_id: str,
        on_message: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        on_disconnect: Optional[Callable[[str], None]] = None,
        on_progress: Optional[Callable[[str, float], None]] = None
    ):
        self.connection_id = connection_id
        self.client_id = client_id
        self.info = ConnectionInfo(
            connection_id=connection_id,
            client_id=client_id
        )
        self._ws = None  # WebSocket对象 (由服务器设置)
        self._on_message = on_message
        self._on_disconnect = on_disconnect
        self._on_progress = on_progress
        self._running = False
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._send_task: Optional[asyncio.Task] = None
    
    async def handle(self, ws) -> None:
        """
        处理WebSocket连接
        
        Args:
            ws: WebSocket对象
        """
        self._ws = ws
        self.info.state = ConnectionState.CONNECTED
        self._running = True
        
        # 启动发送任务
        self._send_task = asyncio.create_task(self._send_loop())
        
        logger.info(f"WebSocket连接已建立: {self.connection_id}")
        
        try:
            while self._running:
                try:
                    # 接收消息
                    msg = await ws.receive()
                    
                    if msg.type == WSMsgType.TEXT:
                        await self._handle_text_message(msg.data)
                    elif msg.type == WSMsgType.BINARY:
                        await self._handle_binary_message(msg.data)
                    elif msg.type == WSMsgType.ERROR:
                        logger.error(f"WebSocket错误: {msg.data}")
                        break
                    elif msg.type == WSMsgType.CLOSE:
                        logger.info(f"WebSocket关闭: {self.connection_id}")
                        break
                    
                    self.info.update_activity()
                    
                except Exception as e:
                    logger.error(f"WebSocket处理错误: {e}")
                    break
                    
        finally:
            await self._cleanup()
    
    async def _handle_text_message(self, data: str) -> None:
        """处理文本消息"""
        try:
            message = json.loads(data)
            msg_type = message.get('type', 'unknown')
            
            if msg_type == 'negotiate':
                await self._handle_negotiate(message)
            elif msg_type == 'auth':
                await self._handle_auth(message)
            elif msg_type == 'transfer_init':
                await self._handle_transfer_init(message)
            elif msg_type == 'transfer_complete':
                await self._handle_transfer_complete(message)
            else:
                # 通用消息处理
                if self._on_message:
                    self._on_message(self.connection_id, message)
                    
        except json.JSONDecodeError:
            logger.warning(f"无效的JSON消息: {data[:100]}")
            await self.send_error("Invalid JSON format")
    
    async def _handle_binary_message(self, data: bytes) -> None:
        """处理二进制消息（数据块）"""
        if not self.info.transfer_session:
            await self.send_error("No active transfer session")
            return
        
        # 解析数据块头部 (前4字节为块索引)
        if len(data) < 4:
            await self.send_error("Invalid chunk format")
            return
        
        chunk_index = int.from_bytes(data[:4], 'big')
        chunk_data = data[4:]
        
        # 存储数据块 (这里应该调用存储管理器)
        session = self.info.transfer_session
        session.add_chunk(chunk_index)
        
        # 发送进度更新
        progress = session.progress
        await self.send_progress(progress)
        
        if self._on_progress:
            self._on_progress(self.connection_id, progress)
        
        logger.debug(f"收到数据块 {chunk_index}/{session.total_chunks} "
                    f"({progress*100:.1f}%) - {self.connection_id}")
    
    async def _handle_negotiate(self, message: Dict[str, Any]) -> None:
        """处理协商请求"""
        supported_protocols = message.get('protocols', ['websocket'])
        
        # 协商协议版本
        negotiated = {
            'type': 'negotiate_response',
            'protocol': 'websocket',
            'version': '1.0',
            'features': ['binary', 'compression'],
            'chunk_size': 65536,
            'max_file_size': 10 * 1024 * 1024 * 1024,  # 10GB
        }
        
        await self.send_message(negotiated)
        logger.info(f"协议协商完成: {self.connection_id}")
    
    async def _handle_auth(self, message: Dict[str, Any]) -> None:
        """处理认证请求"""
        token = message.get('token')
        
        # TODO: 验证token
        # 这里应该调用AuthManager验证
        
        self.info.auth_token = token
        
        response = {
            'type': 'auth_response',
            'success': True,
            'message': 'Authenticated'
        }
        
        await self.send_message(response)
        logger.info(f"认证完成: {self.connection_id}")
    
    async def _handle_transfer_init(self, message: Dict[str, Any]) -> None:
        """处理传输初始化"""
        file_name = message.get('file_name', 'unknown')
        file_size = message.get('file_size', 0)
        checksum = message.get('checksum')
        
        # 创建传输会话
        session_id = str(uuid.uuid4())
        session = TransferSession(
            session_id=session_id,
            connection_id=self.connection_id,
            file_name=file_name,
            file_size=file_size,
            checksum=checksum
        )
        
        self.info.transfer_session = session
        self.info.state = ConnectionState.TRANSFERRING
        
        response = {
            'type': 'transfer_init_response',
            'success': True,
            'session_id': session_id,
            'chunk_size': session.chunk_size,
            'total_chunks': session.total_chunks
        }
        
        await self.send_message(response)
        logger.info(f"传输会话创建: {session_id} "
                   f"({file_name}, {file_size} bytes)")
    
    async def _handle_transfer_complete(self, message: Dict[str, Any]) -> None:
        """处理传输完成"""
        if not self.info.transfer_session:
            await self.send_error("No active transfer session")
            return
        
        session = self.info.transfer_session
        
        # 检查完整性
        if session.is_complete:
            response = {
                'type': 'transfer_complete_response',
                'success': True,
                'session_id': session.session_id,
                'received_chunks': len(session.received_chunks),
                'total_chunks': session.total_chunks
            }
            logger.info(f"传输完成: {session.session_id}")
        else:
            # 返回缺失的数据块
            missing = set(range(session.total_chunks)) - session.received_chunks
            response = {
                'type': 'transfer_complete_response',
                'success': False,
                'error': 'Transfer incomplete',
                'missing_chunks': sorted(list(missing))[:100]  # 最多100个
            }
            logger.warning(f"传输不完整: {session.session_id} "
                          f"({len(missing)} chunks missing)")
        
        await self.send_message(response)
        self.info.state = ConnectionState.CONNECTED
    
    async def send_message(self, message: Dict[str, Any]) -> None:
        """发送消息"""
        await self._message_queue.put(('text', json.dumps(message)))
    
    async def send_binary(self, data: bytes) -> None:
        """发送二进制数据"""
        await self._message_queue.put(('binary', data))
    
    async def send_progress(self, progress: float) -> None:
        """发送进度更新"""
        message = {
            'type': 'progress',
            'progress': progress,
            'percentage': round(progress * 100, 2)
        }
        await self.send_message(message)
    
    async def send_error(self, error: str) -> None:
        """发送错误消息"""
        message = {
            'type': 'error',
            'error': error
        }
        await self.send_message(message)
    
    async def _send_loop(self) -> None:
        """发送循环"""
        while self._running:
            try:
                msg_type, data = await self._message_queue.get()
                
                if self._ws:
                    if msg_type == 'text':
                        await self._ws.send_str(data)
                    elif msg_type == 'binary':
                        await self._ws.send_bytes(data)
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"发送消息失败: {e}")
    
    async def _cleanup(self) -> None:
        """清理资源"""
        self._running = False
        self.info.state = ConnectionState.DISCONNECTED
        
        if self._send_task:
            self._send_task.cancel()
            try:
                await self._send_task
            except asyncio.CancelledError:
                pass
        
        if self._on_disconnect:
            self._on_disconnect(self.connection_id)
        
        logger.info(f"WebSocket连接已清理: {self.connection_id}")
    
    async def close(self) -> None:
        """主动关闭连接"""
        self.info.state = ConnectionState.DISCONNECTING
        self._running = False
        
        if self._ws:
            await self._ws.close()


# 导入aiohttp WebSocket类型
from aiohttp import WSMsgType


class WebSocketServer:
    """
    WebSocket服务器
    
    管理WebSocket连接：
    - 连接注册和注销
    - 消息广播
    - 连接监控
    """
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        max_connections: int = 1000,
        heartbeat_interval: float = 30.0
    ):
        self._host = host
        self._port = port
        self._max_connections = max_connections
        self._heartbeat_interval = heartbeat_interval
        
        self._connections: Dict[str, WebSocketHandler] = {}
        self._running = False
        self._site = None
        self._app = None
        self._runner = None
        
        # 统计
        self._total_connections = 0
        self._total_messages = 0
        
        logger.info(f"WebSocketServer initialized: {host}:{port}")
    
    async def start(self) -> None:
        """启动WebSocket服务器"""
        if self._running:
            return
        
        self._running = True
        
        try:
            from aiohttp import web
            
            self._app = web.Application()
            self._app.router.add_get('/ws', self._handle_websocket)
            self._app.router.add_post('/negotiate', self._handle_negotiate_http)
            
            self._runner = web.AppRunner(self._app)
            await self._runner.setup()
            
            site = web.TCPSite(self._runner, self._host, self._port)
            await site.start()
            
            # 启动监控任务
            asyncio.create_task(self._monitor_loop())
            
            logger.info(f"WebSocket服务器已启动: ws://{self._host}:{self._port}")
            
        except ImportError:
            logger.error("aiohttp未安装，WebSocket服务器无法启动")
            raise
    
    async def stop(self) -> None:
        """停止WebSocket服务器"""
        if not self._running:
            return
        
        self._running = False
        
        # 关闭所有连接
        close_tasks = [handler.close() for handler in self._connections.values()]
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)
        
        self._connections.clear()
        
        # 关闭服务器
        if self._runner:
            await self._runner.cleanup()
        
        logger.info("WebSocket服务器已停止")
    
    async def _handle_websocket(self, request) -> None:
        """处理WebSocket连接请求"""
        try:
            from aiohttp import web
            
            # 检查连接数限制
            if len(self._connections) >= self._max_connections:
                logger.warning(f"达到最大连接数限制: {self._max_connections}")
                return web.Response(status=503, text="Server busy")
            
            ws = web.WebSocketResponse(
                heartbeat=self._heartbeat_interval,
                autoping=True
            )
            await ws.prepare(request)
            
            # 生成连接ID
            connection_id = str(uuid.uuid4())
            client_id = request.query.get('client_id', 'unknown')
            
            # 创建处理器
            handler = WebSocketHandler(
                connection_id=connection_id,
                client_id=client_id,
                on_message=self._on_message,
                on_disconnect=self._on_disconnect,
                on_progress=self._on_progress
            )
            
            handler.info.remote_addr = request.remote
            handler.info.user_agent = request.headers.get('User-Agent')
            
            self._connections[connection_id] = handler
            self._total_connections += 1
            
            # 处理连接
            await handler.handle(ws)
            
            return ws
            
        except Exception as e:
            logger.error(f"WebSocket处理异常: {e}")
            return web.Response(status=500)
    
    async def _handle_negotiate_http(self, request) -> None:
        """HTTP协商接口"""
        try:
            from aiohttp import web
            
            body = await request.json()
            supported = body.get('protocols', ['websocket'])
            
            response = {
                'protocol': 'websocket',
                'version': '1.0',
                'features': ['binary', 'compression'],
                'endpoint': f'ws://{self._host}:{self._port}/ws',
                'chunk_size': 65536,
                'max_file_size': 10 * 1024 * 1024 * 1024
            }
            
            return web.json_response(response)
            
        except Exception as e:
            logger.error(f"协商失败: {e}")
            return web.Response(status=400)
    
    def _on_message(self, connection_id: str, message: Dict[str, Any]) -> None:
        """消息回调"""
        self._total_messages += 1
        logger.debug(f"收到消息: {connection_id} - {message.get('type', 'unknown')}")
    
    def _on_disconnect(self, connection_id: str) -> None:
        """断开回调"""
        if connection_id in self._connections:
            del self._connections[connection_id]
            logger.info(f"连接已移除: {connection_id}")
    
    def _on_progress(self, connection_id: str, progress: float) -> None:
        """进度回调"""
        logger.debug(f"传输进度: {connection_id} - {progress*100:.1f}%")
    
    async def _monitor_loop(self) -> None:
        """监控循环"""
        while self._running:
            try:
                await asyncio.sleep(60)  # 每分钟报告一次
                
                logger.info(f"WebSocket统计: "
                           f"活跃连接={len(self._connections)}, "
                           f"总连接={self._total_connections}, "
                           f"总消息={self._total_messages}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
    
    async def broadcast(self, message: Dict[str, Any]) -> int:
        """
        广播消息到所有连接
        
        Returns:
            int: 成功发送的连接数
        """
        if not self._connections:
            return 0
        
        tasks = [
            handler.send_message(message)
            for handler in self._connections.values()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        
        return success_count
    
    async def send_to(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """发送消息到指定连接"""
        handler = self._connections.get(connection_id)
        if not handler:
            return False
        
        try:
            await handler.send_message(message)
            return True
        except Exception as e:
            logger.error(f"发送消息失败: {connection_id} - {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'running': self._running,
            'host': self._host,
            'port': self._port,
            'active_connections': len(self._connections),
            'max_connections': self._max_connections,
            'total_connections': self._total_connections,
            'total_messages': self._total_messages,
            'connection_ids': list(self._connections.keys())
        }


def create_websocket_server(
    host: str = "0.0.0.0",
    port: int = 8080,
    **kwargs
) -> WebSocketServer:
    """创建WebSocket服务器"""
    return WebSocketServer(host=host, port=port, **kwargs)
