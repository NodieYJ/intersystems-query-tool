#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
策略模式模块

提供策略模式的基础设施。
"""

from src.infrastructure.strategy.strategy_framework import (
    IStrategy,
    StrategyContext,
    StrategyRegistry,
    CompositeStrategy,
    get_strategy_registry,
    register_strategy,
    get_strategy,
)

__all__ = [
    'IStrategy',
    'StrategyContext',
    'StrategyRegistry',
    'CompositeStrategy',
    'get_strategy_registry',
    'register_strategy',
    'get_strategy',
]
