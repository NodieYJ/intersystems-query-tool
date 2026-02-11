#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
依赖注入模块

提供依赖注入容器和相关工具
"""

from src.infrastructure.di.container import (
    DIContainer,
    Scope,
    ServiceLifetime,
    ServiceDescriptor,
    get_container,
    configure_services,
    register_singleton,
    register_transient,
    resolve,
)

# 导出服务接口（如果已导入）
try:
    from src.infrastructure.di.service_registration import (
        IConfig,
        IScalingManager,
        ILogger,
        IDatabaseDriverFactory,
        configure_application_services,
        initialize_container,
        get_service,
    )
    __all__ = [
        'DIContainer',
        'Scope',
        'ServiceLifetime',
        'ServiceDescriptor',
        'get_container',
        'configure_services',
        'register_singleton',
        'register_transient',
        'resolve',
        'IConfig',
        'IScalingManager',
        'ILogger',
        'IDatabaseDriverFactory',
        'configure_application_services',
        'initialize_container',
        'get_service',
    ]
except ImportError:
    # service_registration 可能依赖其他模块，允许延迟导入
    __all__ = [
        'DIContainer',
        'Scope',
        'ServiceLifetime',
        'ServiceDescriptor',
        'get_container',
        'configure_services',
        'register_singleton',
        'register_transient',
        'resolve',
    ]
