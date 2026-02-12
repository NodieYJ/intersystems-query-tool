#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
服务器模块

提供高并发服务器的基础设施。
"""

from src.infrastructure.server.concurrency import (
    ConnectionPool,
    MessageQueue,
    HeartbeatMonitor,
    ConnectionDispatcher,
    ConnectionState,
    ConnectionInfo,
    create_connection_pool,
    create_message_queue,
    create_heartbeat_monitor,
    create_connection_dispatcher,
)

from src.infrastructure.server.http_server import (
    HTTPServer,
    Router,
    RequestHandler,
    ServerConfig,
    create_server,
    create_router,
)

from src.infrastructure.server.auth import (
    AuthManager,
    RateLimiter,
    PermissionChecker,
    TokenInfo,
    create_auth_manager,
    create_rate_limiter,
    create_permission_checker,
)

__all__ = [
    # Concurrency
    'ConnectionPool',
    'MessageQueue',
    'HeartbeatMonitor',
    'ConnectionDispatcher',
    'ConnectionState',
    'ConnectionInfo',
    'create_connection_pool',
    'create_message_queue',
    'create_heartbeat_monitor',
    'create_connection_dispatcher',
    # HTTP Server
    'HTTPServer',
    'Router',
    'RequestHandler',
    'ServerConfig',
    'create_server',
    'create_router',
    # Auth
    'AuthManager',
    'RateLimiter',
    'PermissionChecker',
    'TokenInfo',
    'create_auth_manager',
    'create_rate_limiter',
    'create_permission_checker',
]
