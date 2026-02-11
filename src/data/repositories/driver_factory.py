#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库驱动工厂模块

用于管理数据库驱动的延迟导入和检测，支持多种驱动：
- Intersystems IRIS Python 驱动
- pyodbc (作为备用)

使用延迟导入模式避免模块级导入问题。
"""

import logging
import threading
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Type

# 导入配置管理器和常量（延迟导入避免循环依赖）
from src.infrastructure.config.constants import DatabaseDefaults, DatabaseTypes
_config_available = True

try:
  # 延迟导入配置模块（避免循环依赖）
  _config_module = None
  def _get_config():
    """延迟加载配置模块"""
    global _config_module
    if _config_module is None:
      try:
        from src.infrastructure.config import ui_config
        _config_module = ui_config
      except ImportError:
        _config_module = None
    return _config_module
except Exception:
  pass

logger = logging.getLogger(__name__)


class DatabaseDriverType(Enum):
    """数据库驱动类型枚举"""
    IRIS = "iris"
    PYODBC = "pyodbc"
    UNKNOWN = "unknown"


class DatabaseDriverFactory:
    """
    数据库驱动工厂类 - 单例模式
    
    负责：
    1. 延迟导入数据库驱动（避免模块级导入问题）
    2. 检测可用的驱动
    3. 根据配置创建合适的连接
    4. 管理驱动状态
    
    使用示例:
        factory = DatabaseDriverFactory()
        driver_type = factory.detect_available_driver()
        connection = factory.create_connection(params)
    
    线程安全：使用双重检查锁定模式确保线程安全
    """
    
    _instance: Optional['DatabaseDriverFactory'] = None
    _initialized: bool = False
    _lock: threading.Lock = threading.Lock()  # 类级别锁，用于线程安全
    
    def __new__(cls) -> 'DatabaseDriverFactory':
        """线程安全的单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                # 双重检查：获取锁后再次检查
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    logger.debug("DatabaseDriverFactory 实例已创建")
        return cls._instance
    
    def __init__(self):
        """初始化驱动工厂（仅执行一次）"""
        if DatabaseDriverFactory._initialized:
            return
        
        self._driver_modules: Dict[DatabaseDriverType, Any] = {}
        self._driver_status: Dict[DatabaseDriverType, bool] = {
            DatabaseDriverType.IRIS: False,
            DatabaseDriverType.PYODBC: False,
        }
        self._iris_dbapi_available: bool = False
        self._iris_legacy_available: bool = False
        
        DatabaseDriverFactory._initialized = True
        logger.debug("DatabaseDriverFactory 初始化完成（尚未加载驱动）")
    
    def _get_driver_priority_from_config(self) -> List[DatabaseDriverType]:
        """
        从配置获取驱动优先级列表
        
        Returns:
            List[DatabaseDriverType]: 按优先级排序的驱动类型列表
        """
        if _config_available:
            try:
                config_module = _get_config()
                if config_module:
                    config = config_module.get_ui_config()
                    if config:
                        return config.get_driver_priority()
            except Exception as e:
                logger.warning(f"从配置获取驱动优先级失败: {e}，使用默认优先级")
        
        # 默认优先级
        return [DatabaseDriverType.IRIS, DatabaseDriverType.PYODBC]
    
    def _try_load_driver(self, driver_type: DatabaseDriverType) -> bool:
        """
        尝试加载指定类型的驱动
        
        Args:
            driver_type: 驱动类型
            
        Returns:
            bool: 是否成功加载
        """
        if driver_type == DatabaseDriverType.IRIS:
            return self._try_load_iris()
        elif driver_type == DatabaseDriverType.PYODBC:
            return self._try_load_pyodbc()
        return False
    
    def detect_available_driver(self, preferred: Optional[DatabaseDriverType] = None) -> DatabaseDriverType:
        """
        检测并返回可用的数据库驱动类型
        
        Args:
            preferred: 优先使用的驱动类型，如果不可用则尝试其他
            
        Returns:
            DatabaseDriverType: 检测到的驱动类型
            
        检测顺序:
        1. 从配置读取优先级
        2. 按优先级尝试加载驱动
        """
        logger.debug("开始检测可用的数据库驱动...")
        
        # 从配置获取驱动优先级
        priority_list = self._get_driver_priority_from_config()
        
        # 如果指定了优先驱动，先尝试它
        if preferred is not None:
            if preferred in priority_list:
                if self._try_load_driver(preferred):
                    return preferred
            # 如果指定的驱动失败，继续按配置优先级尝试其他
        
        # 按配置优先级尝试
        for driver_type in priority_list:
            if self._try_load_pyodbc():
                return DatabaseDriverType.PYODBC
            elif self._try_load_iris():
                return DatabaseDriverType.IRIS
        else:
            # 自动检测：优先 IRIS，其次 pyodbc
            if self._try_load_iris():
                return DatabaseDriverType.IRIS
            elif self._try_load_pyodbc():
                return DatabaseDriverType.PYODBC
        
        logger.error("没有可用的数据库驱动")
        return DatabaseDriverType.UNKNOWN
    
    def _try_load_iris(self) -> bool:
        """
        尝试加载 IRIS Python 驱动
        
        Returns:
            bool: 是否成功加载
        """
        if self._driver_status[DatabaseDriverType.IRIS]:
            logger.debug("IRIS 驱动已加载")
            return True
        
        try:
            logger.debug("尝试导入 iris 驱动...")
            import iris
            from iris import IRIS
            
            self._driver_modules[DatabaseDriverType.IRIS] = iris
            self._driver_status[DatabaseDriverType.IRIS] = True
            self._iris_legacy_available = True
            
            logger.info("成功加载 IRIS 驱动 (iris)")
            
            # 尝试加载 dbapi 模块
            try:
                from iris.dbapi import connect
                self._iris_dbapi_available = True
                logger.info("成功加载 iris.dbapi 模块")
            except ImportError as e:
                self._iris_dbapi_available = False
                logger.debug(f"iris.dbapi 模块不可用: {e}")
            
            return True
            
        except ImportError as e:
            logger.debug(f"IRIS 驱动不可用: {e}")
            self._driver_status[DatabaseDriverType.IRIS] = False
            return False
    
    def _try_load_pyodbc(self) -> bool:
        """
        尝试加载 pyodbc 驱动
        
        Returns:
            bool: 是否成功加载
        """
        if self._driver_status[DatabaseDriverType.PYODBC]:
            logger.debug("pyodbc 驱动已加载")
            return True
        
        try:
            logger.debug("尝试导入 pyodbc 驱动...")
            import pyodbc
            
            self._driver_modules[DatabaseDriverType.PYODBC] = pyodbc
            self._driver_status[DatabaseDriverType.PYODBC] = True
            
            logger.info("成功加载 pyodbc 驱动")
            return True
            
        except ImportError as e:
            logger.debug(f"pyodbc 驱动不可用: {e}")
            self._driver_status[DatabaseDriverType.PYODBC] = False
            return False
    
    def is_driver_available(self, driver_type: DatabaseDriverType) -> bool:
        """
        检查指定驱动是否可用
        
        Args:
            driver_type: 驱动类型
            
        Returns:
            bool: 是否可用
        """
        if driver_type == DatabaseDriverType.IRIS:
            return self._try_load_iris()
        elif driver_type == DatabaseDriverType.PYODBC:
            return self._try_load_pyodbc()
        return False
    
    def get_available_drivers(self) -> List[DatabaseDriverType]:
        """
        获取所有可用的驱动类型列表
        
        Returns:
            List[DatabaseDriverType]: 可用驱动类型列表
        """
        available = []
        
        if self._try_load_iris():
            available.append(DatabaseDriverType.IRIS)
        
        if self._try_load_pyodbc():
            available.append(DatabaseDriverType.PYODBC)
        
        return available
    
    def create_connection(
        self, 
        connection_params: Dict[str, Any],
        driver_type: Optional[DatabaseDriverType] = None
    ) -> Optional[Tuple[Any, Any]]:
        """
        创建数据库连接
        
        Args:
            connection_params: 连接参数
                - server: 服务器地址
                - port: 端口号
                - namespace: 命名空间
                - username: 用户名
                - password: 密码
                - db_type: 数据库类型 (IRIS/Cache)
            driver_type: 指定使用的驱动类型，None则自动选择
            
        Returns:
            Optional[Tuple[Any, Any]]: (connection, cursor) 元组，失败返回 None
        """
        if driver_type is None:
            driver_type = self.detect_available_driver()
        
        if driver_type == DatabaseDriverType.UNKNOWN:
            logger.error("没有可用的数据库驱动")
            return None
        
        if driver_type == DatabaseDriverType.IRIS:
            return self._create_iris_connection(connection_params)
        elif driver_type == DatabaseDriverType.PYODBC:
            return self._create_pyodbc_connection(connection_params)
        
        logger.error(f"未知的驱动类型: {driver_type}")
        return None
    
    def _create_iris_connection(
        self, 
        connection_params: Dict[str, Any]
    ) -> Optional[Tuple[Any, Any]]:
        """
        使用 IRIS 驱动创建连接
        
        尝试顺序：
        1. iris.dbapi.connect (推荐)
        2. iris.createIRIS
        3. iris.connect
        4. iris.IRISConnection
        """
        if not self._try_load_iris():
            logger.error("IRIS 驱动未加载")
            return None
        
        server = connection_params.get("server", "localhost")
        port = connection_params.get("port", DatabaseDefaults.PORT_DEFAULT)
        namespace = connection_params.get("namespace", "USER")
        username = connection_params.get("username", "")
        password = connection_params.get("password", "")
        db_type = connection_params.get("db_type", DatabaseTypes.IRIS)
        
        logger.info(f"尝试使用 IRIS 驱动连接 {db_type} 数据库: {server}:{port}/{namespace}")
        
        # 尝试使用 iris.dbapi
        if self._iris_dbapi_available:
            try:
                from iris.dbapi import connect
                
                connection = connect(
                    hostname=server,
                    port=port,
                    namespace=namespace,
                    username=username,
                    password=password,
                )
                cursor = connection.cursor()
                
                logger.info(f"成功使用 iris.dbapi 连接到 {db_type} 数据库")
                return connection, cursor
                
            except Exception as e:
                logger.warning(f"使用 iris.dbapi 连接失败: {e}")
        
        # 尝试使用 iris.createIRIS
        if self._iris_legacy_available:
            try:
                import iris
                
                connection = iris.createIRIS()  # type: ignore[call-arg]
                connection.connect(  # type: ignore[call-arg]
                    hostname=server,
                    port=port,
                    namespace=namespace,
                    username=username,
                    password=password,
                )
                cursor = connection
                
                logger.info(f"成功使用 iris.createIRIS 连接到 {db_type} 数据库")
                return connection, cursor
                
            except Exception as e:
                logger.warning(f"使用 iris.createIRIS 连接失败: {e}")
            
            # 尝试使用 iris.connect
            try:
                import iris
                
                connection = iris.connect(
                    hostname=server,
                    port=port,
                    namespace=namespace,
                    username=username,
                    password=password,
                )
                cursor = connection
                
                logger.info(f"成功使用 iris.connect 连接到 {db_type} 数据库")
                return connection, cursor
                
            except Exception as e:
                logger.warning(f"使用 iris.connect 连接失败: {e}")
            
            # 尝试使用 iris.IRISConnection
            try:
                from iris import IRIS, IRISConnection
                
                connection = IRISConnection(
                    hostname=server,
                    port=port,
                    namespace=namespace,
                    username=username,
                    password=password,
                )
                iris_instance = IRIS(connection)
                cursor = iris_instance
                
                logger.info(f"成功使用 iris.IRISConnection 连接到 {db_type} 数据库")
                return iris_instance, cursor
                
            except Exception as e:
                logger.warning(f"使用 iris.IRISConnection 连接失败: {e}")
        
        logger.error("所有 IRIS 连接方式都失败")
        return None
    
    def _create_pyodbc_connection(
        self, 
        connection_params: Dict[str, Any]
    ) -> Optional[Tuple[Any, Any]]:
        """
        使用 pyodbc 驱动创建连接
        
        尝试顺序：
        1. InterSystems IRIS ODBC 驱动
        2. InterSystems Cache ODBC 驱动
        3. DSN-less 连接
        """
        if not self._try_load_pyodbc():
            logger.error("pyodbc 驱动未加载")
            return None
        
        import pyodbc
        
        server = connection_params.get("server", "localhost")
        port = connection_params.get("port", DatabaseDefaults.PORT_DEFAULT)
        namespace = connection_params.get("namespace", "USER")
        username = connection_params.get("username", "")
        password = connection_params.get("password", "")
        db_type = connection_params.get("db_type", DatabaseTypes.IRIS)
        
        logger.info(f"尝试使用 pyodbc 连接 {db_type} 数据库: {server}:{port}/{namespace}")
        
        # 选择驱动列表
        if db_type == DatabaseTypes.IRIS:
            drivers = [
                "InterSystems IRIS ODBC35 Driver",
                "InterSystems IRIS ODBC Driver",
                "InterSystems IRIS",
            ]
        else:
            drivers = [
                "InterSystems Cache ODBC35 Driver",
                "InterSystems Cache ODBC Driver",
                "InterSystems Cache",
            ]
        
        # 尝试使用不同的驱动
        for driver in drivers:
            try:
                conn_str = f"DRIVER={{{driver}}};SERVER={server};PORT={port};DATABASE={namespace};UID={username};PWD={password}"
                
                logger.debug(f"尝试使用驱动 '{driver}'")
                connection = pyodbc.connect(conn_str)
                cursor = connection.cursor()
                
                logger.info(f"成功使用驱动 '{driver}' 连接到 {db_type} 数据库")
                return connection, cursor
                
            except pyodbc.Error as e:
                logger.warning(f"使用驱动 '{driver}' 连接失败: {e}")
                continue
        
        # 尝试 DSN-less 连接
        try:
            conn_str = f"DRIVER={{InterSystems ODBC}};SERVER={server};PORT={port};DATABASE={namespace};UID={username};PWD={password}"
            
            logger.debug("尝试使用 DSN-less 连接")
            connection = pyodbc.connect(conn_str)
            cursor = connection.cursor()
            
            logger.info(f"成功使用 DSN-less 连接到 {db_type} 数据库")
            return connection, cursor
            
        except pyodbc.Error as e:
            logger.error(f"DSN-less 连接失败: {e}")
        
        logger.error("所有 pyodbc 连接方式都失败")
        return None
    
    def get_driver_info(self) -> Dict[str, Any]:
        """
        获取驱动信息
        
        Returns:
            Dict[str, Any]: 驱动状态信息
        """
        return {
            "iris_available": self._driver_status.get(DatabaseDriverType.IRIS, False),
            "iris_dbapi": self._iris_dbapi_available,
            "iris_legacy": self._iris_legacy_available,
            "pyodbc_available": self._driver_status.get(DatabaseDriverType.PYODBC, False),
            "available_drivers": [dt.value for dt in self.get_available_drivers()],
        }


# 全局工厂实例
_driver_factory: Optional[DatabaseDriverFactory] = None


def get_driver_factory() -> DatabaseDriverFactory:
    """
    获取全局驱动工厂实例
    
    Returns:
        DatabaseDriverFactory: 驱动工厂单例
    """
    global _driver_factory
    if _driver_factory is None:
        _driver_factory = DatabaseDriverFactory()
    return _driver_factory


def detect_available_driver(preferred: Optional[str] = None) -> str:
    """
    便捷函数：检测可用的数据库驱动
    
    Args:
        preferred: 优先使用的驱动名称 ("iris" 或 "pyodbc")
        
    Returns:
        str: 可用的驱动名称
    """
    factory = get_driver_factory()
    
    preferred_type = None
    if preferred:
        try:
            preferred_type = DatabaseDriverType(preferred.lower())
        except ValueError:
            logger.warning(f"未知的驱动类型: {preferred}")
    
    driver_type = factory.detect_available_driver(preferred_type)
    return driver_type.value


def is_driver_available(driver_name: str) -> bool:
    """
    便捷函数：检查指定驱动是否可用
    
    Args:
        driver_name: 驱动名称 ("iris" 或 "pyodbc")
        
    Returns:
        bool: 是否可用
    """
    factory = get_driver_factory()
    
    try:
        driver_type = DatabaseDriverType(driver_name.lower())
        return factory.is_driver_available(driver_type)
    except ValueError:
        return False
