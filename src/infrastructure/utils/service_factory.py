#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一服务工厂模块

提供全局访问点获取所有核心服务实例。
采用惰性初始化模式，确保所有服务按正确顺序初始化。

功能:
- 统一的实例获取接口
- 依赖注入自动处理
- 服务生命周期管理
- 循环依赖检测
"""

import logging
import threading
from typing import Any, Dict, Optional, Type, TypeVar

from src.infrastructure.config.config_manager import (
    ConfigManager,
    config_manager,
    get_config_manager,
)
from src.infrastructure.config.ui_config import UIConfig, get_ui_config
from src.infrastructure.di.container import DIContainer, get_container
from src.infrastructure.di.service_registration import get_service
from src.infrastructure.logging.logger import LogManager, get_log_manager
from src.infrastructure.security.security_utils import SecurityUtils, get_security_utils
from src.infrastructure.utils.performance import PerformanceOptimizer, get_optimizer
from src.infrastructure.utils.scaling_manager import ScalingManager, get_scaling_manager
from src.business.services.data_analysis_service import DataAnalysisService, get_data_analysis_service
from src.business.services.data_service import DataService, get_data_service
from src.business.services.query_history_manager import QueryHistoryManager, get_query_history_manager
from src.data.repositories.database_repository import DatabaseRepository, get_db_repository
from src.data.repositories.driver_factory import DatabaseDriverFactory, get_driver_factory

logger = logging.getLogger(__name__)

# 类型变量用于泛型返回
T = TypeVar('T')


class ServiceFactory:
    """
    统一服务工厂类
    
    提供所有核心服务的统一访问接口。
    使用依赖注入容器管理服务依赖关系。
    
    特性:
    - 惰性初始化：首次访问时创建实例
    - 依赖自动解析：自动处理服务间依赖
    - 单例模式：所有服务都是单例
    - 线程安全：使用锁保护初始化过程
    """

    # 类级别的服务缓存
    _services: Dict[str, Any] = {}
    _initialized: bool = False
    _init_lock = None

    @classmethod
    def initialize(cls) -> None:
        """
        初始化所有核心服务
        
        按正确依赖顺序初始化服务。
        应该在应用启动时调用一次。
        """
        if cls._initialized:
            return
        
        cls._init_lock = threading.Lock()
        with cls._init_lock:
            if cls._initialized:
                return
            
            try:
                # 第一层：基础服务（无依赖）
                cls._get_service_impl(ConfigManager, get_config_manager)
                cls._get_service_impl(DIContainer, get_container)
                
                # 第二层：依赖基础服务的服务
                cls._get_service_impl(SecurityUtils, get_security_utils)
                cls._get_service_impl(LogManager, get_log_manager)
                cls._get_service_impl(UIConfig, get_ui_config)
                
                # 第三层：依赖配置的服务
                cls._get_service_impl(ScalingManager, get_scaling_manager)
                cls._get_service_impl(PerformanceOptimizer, get_optimizer)
                
                # 第四层：数据层服务
                cls._get_service_impl(DatabaseDriverFactory, get_driver_factory)
                cls._get_service_impl(DatabaseRepository, get_db_repository)
                
                # 第五层：业务层服务
                cls._get_service_impl(QueryHistoryManager, get_query_history_manager)
                cls._get_service_impl(DataService, get_data_service)
                cls._get_service_impl(DataAnalysisService, get_data_analysis_service)
                
                cls._initialized = True
                logger.info("ServiceFactory 初始化完成")
                
            except Exception as e:
                logger.error(f"ServiceFactory 初始化失败: {str(e)}", exc_info=True)
                raise

    @classmethod
    def _get_service_impl(cls, service_type: Type[T], factory_func) -> T:
        """
        获取服务实例的内部实现
        
        Args:
            service_type: 服务类型
            factory_func: 服务工厂函数
            
        Returns:
            T: 服务实例
        """
        service_name = service_type.__name__
        
        if service_name not in cls._services:
            try:
                instance = factory_func()
                cls._services[service_name] = instance
                logger.debug(f"服务已创建: {service_name}")
            except Exception as e:
                logger.error(f"创建服务失败 {service_name}: {str(e)}")
                raise
        
        return cls._services[service_name]

    # ========== 核心服务访问方法 ==========

    @classmethod
    def get_config_manager(cls) -> ConfigManager:
        """获取配置管理器实例"""
        return cls._get_service_impl(ConfigManager, get_config_manager)

    @classmethod
    def get_container(cls) -> DIContainer:
        """获取DI容器实例"""
        return cls._get_service_impl(DIContainer, get_container)

    @classmethod
    def get_security_utils(cls) -> SecurityUtils:
        """获取安全工具实例"""
        return cls._get_service_impl(SecurityUtils, get_security_utils)

    @classmethod
    def get_log_manager(cls) -> LogManager:
        """获取日志管理器实例"""
        return cls._get_service_impl(LogManager, get_log_manager)

    @classmethod
    def get_ui_config(cls) -> UIConfig:
        """获取UI配置实例"""
        return cls._get_service_impl(UIConfig, get_ui_config)

    @classmethod
    def get_scaling_manager(cls) -> ScalingManager:
        """获取缩放管理器实例"""
        return cls._get_service_impl(ScalingManager, get_scaling_manager)

    @classmethod
    def get_optimizer(cls) -> PerformanceOptimizer:
        """获取性能优化器实例"""
        return cls._get_service_impl(PerformanceOptimizer, get_optimizer)

    @classmethod
    def get_driver_factory(cls) -> DatabaseDriverFactory:
        """获取数据库驱动工厂实例"""
        return cls._get_service_impl(DatabaseDriverFactory, get_driver_factory)

    @classmethod
    def get_db_repository(cls) -> DatabaseRepository:
        """获取数据库仓库实例"""
        return cls._get_service_impl(DatabaseRepository, get_db_repository)

    @classmethod
    def get_query_history_manager(cls) -> QueryHistoryManager:
        """获取查询历史管理器实例"""
        return cls._get_service_impl(QueryHistoryManager, get_query_history_manager)

    @classmethod
    def get_data_service(cls) -> DataService:
        """获取数据服务实例"""
        return cls._get_service_impl(DataService, get_data_service)

    @classmethod
    def get_data_analysis_service(cls) -> DataAnalysisService:
        """获取数据分析服务实例"""
        return cls._get_service_impl(DataAnalysisService, get_data_analysis_service)

    # ========== 服务状态管理 ==========

    @classmethod
    def is_initialized(cls) -> bool:
        """
        检查是否已初始化
        
        Returns:
            bool: 是否已初始化
        """
        return cls._initialized

    @classmethod
    def get_service(cls, service_type: Type[T]) -> Optional[T]:
        """
        通过类型获取服务实例
        
        Args:
            service_type: 服务类型
            
        Returns:
            Optional[T]: 服务实例，如果不存在返回None
        """
        service_name = service_type.__name__
        return cls._services.get(service_name)

    @classmethod
    def reset(cls) -> None:
        """
        重置所有服务实例
        
        主要用于测试目的。
        """
        cls._services.clear()
        cls._initialized = False
        logger.info("ServiceFactory 已重置")


# 便捷函数（保持向后兼容）

def get_config_manager_service() -> ConfigManager:
    """获取配置管理器实例"""
    return ServiceFactory.get_config_manager()


def get_container_service() -> DIContainer:
    """获取DI容器实例"""
    return ServiceFactory.get_container()


def get_security_service() -> SecurityUtils:
    """获取安全工具实例"""
    return ServiceFactory.get_security_utils()


def get_log_service() -> LogManager:
    """获取日志管理器实例"""
    return ServiceFactory.get_log_manager()


def get_ui_service() -> UIConfig:
    """获取UI配置实例"""
    return ServiceFactory.get_ui_config()


# 初始化工厂（可选，在应用启动时调用）
def initialize_services() -> None:
    """
    初始化所有服务
    
    在应用启动时调用，确保所有服务按正确顺序初始化。
    """
    ServiceFactory.initialize()
