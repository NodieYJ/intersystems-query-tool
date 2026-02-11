#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
应用程序常量

集中管理所有硬编码的配置值
"""

from enum import Enum


class DatabaseDefaults:
    """数据库默认配置"""
    
    # 默认端口
    PORT_DEFAULT = 1972
    PORT_MYSQL = 3306
    PORT_POSTGRESQL = 5432
    PORT_SQLSERVER = 1433
    PORT_ORACLE = 1521
    
    # 默认超时（秒）
    TIMEOUT_CONNECT = 10
    TIMEOUT_QUERY = 30
    
    # 默认字符集
    CHARSET = "UTF-8"
    
    # 连接池默认配置
    POOL_MAX_CONNECTIONS = 10
    POOL_TIMEOUT = 300
    POOL_CLEANUP_INTERVAL = 60


class DatabaseTypes:
    """数据库类型常量"""
    
    IRIS = "IRIS"
    CACHE = "Cache"
    MYSQL = "MySQL"
    POSTGRESQL = "PostgreSQL"
    SQLSERVER = "SQLServer"
    ORACLE = "Oracle"
    UNKNOWN = "UNKNOWN"
    
    @classmethod
    def all_types(cls) -> list:
        """返回所有支持的数据库类型"""
        return [
            cls.IRIS, cls.CACHE, cls.MYSQL, 
            cls.POSTGRESQL, cls.SQLSERVER, cls.ORACLE
        ]
    
    @classmethod
    def get_default_port(cls, db_type: str) -> int:
        """获取数据库类型对应的默认端口"""
        from src.infrastructure.config.constants import DatabaseDefaults
        ports = {
            cls.IRIS: DatabaseDefaults.PORT_DEFAULT,
            cls.CACHE: DatabaseDefaults.PORT_DEFAULT,
            cls.MYSQL: DatabaseDefaults.PORT_MYSQL,
            cls.POSTGRESQL: DatabaseDefaults.PORT_POSTGRESQL,
            cls.SQLSERVER: DatabaseDefaults.PORT_SQLSERVER,
            cls.ORACLE: DatabaseDefaults.PORT_ORACLE,
        }
        return ports.get(db_type, DatabaseDefaults.PORT_DEFAULT)


class SecurityConfig:
    """安全配置"""
    
    # PBKDF2迭代次数（OWASP推荐）
    PBKDF2_ITERATIONS = 100000
    
    # 密钥长度（字节）
    PBKDF2_KEY_LENGTH = 32
    
    # 盐值长度（字节）
    SALT_LENGTH = 16
    
    # Token过期时间（秒）
    TOKEN_EXPIRY = 3600
    
    # 密码最小长度
    PASSWORD_MIN_LENGTH = 8


class UIConfigDefaults:
    """UI默认配置"""
    
    # 默认字体大小
    FONT_SIZE = 10
    
    # 默认字体 - Windows 7/10 通用字体栈
    # 优先使用无衬线字体，确保中文和英文都能正确显示
    FONT_FAMILY = "Microsoft YaHei,Segoe UI,Arial,sans-serif"
    
    # 等宽字体
    MONOSPACE_FONT = "Consolas,Monaco,Courier New,monospace"
    
    # 默认缩放比例
    SCALE_FACTOR = 1.0
    
    # 窗口默认尺寸
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 600
    
    # 布局边距
    LAYOUT_MARGIN = 10
    LAYOUT_SPACING = 5


class LoggingConfig:
    """日志配置"""
    
    # 日志文件路径
    LOG_FILE = "pywindows.log"
    
    # 日志格式
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 日志级别
    LOG_LEVEL = "INFO"
    
    # 日志文件最大大小（字节）
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    
    # 日志文件备份数量
    LOG_BACKUP_COUNT = 5


class ErrorMessages:
    """错误消息常量"""
    
    CONNECTION_FAILED = "数据库连接失败"
    QUERY_FAILED = "查询执行失败"
    CONFIG_ERROR = "配置错误"
    SECURITY_ERROR = "安全错误"
    UNKNOWN_ERROR = "发生未知错误"
    
    @classmethod
    def get_connection_help(cls, error: str) -> str:
        """获取连接错误的帮助信息"""
        return (
            f"{cls.CONNECTION_FAILED}: {error}\n\n"
            "请检查：\n"
            "1. 数据库服务是否正在运行\n"
            "2. 服务器地址和端口是否正确\n"
            "3. 用户名和密码是否正确\n"
            "4. 防火墙是否阻止了连接"
        )
