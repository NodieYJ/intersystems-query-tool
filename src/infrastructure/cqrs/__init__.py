#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CQRS (Command Query Responsibility Segregation) 模块

提供命令和查询的分离处理机制。
"""

from src.infrastructure.cqrs.cqrs_bus import (
    Command,
    CommandHandler,
    CommandResult,
    Query,
    QueryHandler,
    QueryResult,
    CQRSBus,
    get_cqrs_bus
)

__all__ = [
    'Command',
    'CommandHandler',
    'CommandResult',
    'Query',
    'QueryHandler',
    'QueryResult',
    'CQRSBus',
    'get_cqrs_bus'
]
