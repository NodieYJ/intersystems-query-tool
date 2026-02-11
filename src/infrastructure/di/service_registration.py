#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
服务注册配置模块

定义应用程序级别的服务注册和依赖关系配置。
所有服务的注册在此模块集中管理，便于维护和测试。
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Tuple, List, Dict, Any

from src.infrastructure.di import DIContainer, ServiceLifetime

logger = logging.getLogger(__name__)


# ============================================================================
# 接口定义
# ============================================================================

class IConfig(ABC):
    """配置服务接口"""
    
    @abstractmethod
    def get(self, key: str, default=None):
        """获取配置值"""
        pass
    
    @abstractmethod
    def get_float(self, key: str, default: float = 0.0) -> float:
        """获取浮点配置值"""
        pass


class IScalingManager(ABC):
    """缩放管理服务接口"""
    
    @abstractmethod
    def calculate_from_screen(self, app) -> float:
        """从屏幕计算缩放比例"""
        pass
    
    @abstractmethod
    def get_scale_factor(self) -> float:
        """获取当前缩放比例"""
        pass


class ILogger(ABC):
    """日志服务接口"""
    
    @abstractmethod
    def debug(self, msg: str, *args, **kwargs):
        """记录调试日志"""
        pass
    
    @abstractmethod
    def info(self, msg: str, *args, **kwargs):
        """记录信息日志"""
        pass
    
    @abstractmethod
    def warning(self, msg: str, *args, **kwargs):
        """记录警告日志"""
        pass
    
    @abstractmethod
    def error(self, msg: str, *args, **kwargs):
        """记录错误日志"""
        pass


class IDatabaseDriverFactory(ABC):
    """数据库驱动工厂接口"""
    
    @abstractmethod
    def create_driver(self, driver_type: str):
        """创建数据库驱动"""
        pass


class ISecurityUtils(ABC):
    """安全工具服务接口"""
    
    @abstractmethod
    def encrypt_password(self, password: str, salt: Optional[str] = None) -> str:
        """加密密码
        
        Args:
            password: 原始密码
            salt: 盐值
            
        Returns:
            str: 加密后的密码
        """
        pass
    
    @abstractmethod
    def verify_password(self, password: str, encrypted_password: str) -> bool:
        """验证密码
        
        Args:
            password: 原始密码
            encrypted_password: 加密后的密码
            
        Returns:
            bool: 密码是否正确
        """
        pass
    
    @abstractmethod
    def execute_query_safe(
        self,
        connection: Any,
        query: str,
        params: Optional[Tuple] = None
    ) -> Optional[List[Dict]]:
        """使用参数化查询安全执行SQL
        
        Args:
            connection: 数据库连接对象
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            Optional[List[Dict]]: 查询结果列表
        """
        pass
    
    @abstractmethod
    def validate_sql_query(self, query: str) -> bool:
        """验证SQL查询是否安全
        
        Args:
            query: SQL查询语句
            
        Returns:
            bool: 查询是否安全
        """
        pass


# ============================================================================
# 服务注册函数
# ============================================================================

def register_config_service(container: DIContainer) -> None:
    """
    注册配置服务
    
    Args:
        container: DI容器实例
    """
    try:
        from src.infrastructure.config.ui_config import get_ui_config
        # 使用工厂函数获取已存在的单例实例
        config_instance = get_ui_config()
        container.register_instance(IConfig, config_instance)
        logger.debug("注册配置服务完成")
    except Exception as e:
        logger.warning(f"注册配置服务失败: {e}")


def register_scaling_manager(container: DIContainer) -> None:
    """
    注册缩放管理服务
    
    Args:
        container: DI容器实例
    """
    try:
        from src.infrastructure.utils.scaling_manager import get_scaling_manager
        # 使用工厂函数获取已存在的单例实例
        scaling_instance = get_scaling_manager()
        container.register_instance(IScalingManager, scaling_instance)
        logger.debug("注册缩放管理服务完成")
    except Exception as e:
        logger.warning(f"注册缩放管理服务失败: {e}")


def register_logger_service(container: DIContainer) -> None:
    """
    注册日志服务
    
    Args:
        container: DI容器实例
    """
    try:
        from src.infrastructure.logging.logger import setup_logger
        # 使用工厂函数获取已存在的日志记录器
        logger_instance = setup_logger()
        container.register_instance(ILogger, logger_instance)
        logger.debug("注册日志服务完成")
    except Exception as e:
        logger.warning(f"注册日志服务失败: {e}")


def register_database_services(container: DIContainer) -> None:
    """
    注册数据库相关服务
    
    Args:
        container: DI容器实例
    """
    try:
        from src.data.repositories.driver_factory import DatabaseDriverFactory
        # 数据库驱动工厂注册为单例
        container.register_singleton(
            IDatabaseDriverFactory,
            DatabaseDriverFactory
        )
        logger.debug("注册数据库服务完成")
    except Exception as e:
        logger.warning(f"注册数据库服务失败: {e}")


def register_security_service(container: DIContainer) -> None:
    """
    注册安全服务
    
    Args:
        container: DI容器实例
    """
    try:
        from src.infrastructure.security.security_utils import SecurityUtils
        # 安全工具注册为单例
        container.register_singleton(
            ISecurityUtils,
            SecurityUtils
        )
        logger.debug("注册安全服务完成")
    except Exception as e:
        logger.warning(f"注册安全服务失败: {e}")


def register_presentation_services(container: DIContainer) -> None:
    """
    注册表示层服务
    
    Args:
        container: DI容器实例
    """
    try:
        # 表示层窗口通常需要瞬态生命周期
        # 这里只注册可能需要注入的服务
        logger.debug("表示层服务注册完成（无需特殊注册）")
    except Exception as e:
        logger.warning(f"注册表示层服务失败: {e}")


def configure_application_services(container: DIContainer) -> None:
    """
    配置应用程序所有服务
    
    这是主要的配置入口，集中注册所有应用程序服务。
    
    Args:
        container: DI容器实例
        
    Example:
        from src.infrastructure.di import get_container
        from src.infrastructure.di.service_registration import configure_application_services
        
        container = get_container()
        configure_application_services(container)
    """
    logger.info("开始配置应用程序服务...")
    
    # 按顺序注册服务（考虑依赖关系）
    # 1. 基础设施层服务（无依赖或依赖外部）
    register_config_service(container)
    register_logger_service(container)
    register_scaling_manager(container)
    register_security_service(container)
    
    # 2. 数据访问层服务
    register_database_services(container)
    
    # 3. 表示层服务
    register_presentation_services(container)
    
    # 记录注册的服务
    registered_services = container.get_registered_services()
    logger.info(f"服务配置完成，已注册 {len(registered_services)} 个服务: {registered_services}")


# ============================================================================
# 便捷函数
# ============================================================================

def initialize_container() -> DIContainer:
    """
    初始化并配置全局容器
    
    Returns:
        DIContainer: 配置完成的容器实例
        
    Example:
        # 在应用程序启动时调用
        container = initialize_container()
        config = container.resolve(IConfig)
    """
    from src.infrastructure.di import get_container
    
    container = get_container()
    configure_application_services(container)
    return container


def get_service(interface):
    """
    便捷函数：从全局容器获取服务
    
    Args:
        interface: 服务接口类型
        
    Returns:
        服务实例
        
    Example:
        from src.infrastructure.di.service_registration import IConfig, get_service
        config = get_service(IConfig)
    """
    from src.infrastructure.di import resolve
    return resolve(interface)
