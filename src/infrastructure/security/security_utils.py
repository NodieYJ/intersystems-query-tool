#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
安全工具模块
用于处理敏感信息加密和输入验证
"""

import re
import base64
import hashlib
import logging
import warnings
from typing import Any, Dict, List, Optional, Union, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# 可选依赖管理
# ============================================================================

# 尝试导入加密库
CRYPTOGRAPHY_AVAILABLE = False
Fernet = None
hashes = None
PBKDF2HMAC = None
default_backend = None

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    logger.warning(
        "cryptography库未安装，密码加密将使用降级方案（SHA256）。"
        "为提高安全性，请安装cryptography: pip install cryptography>=3.4.8"
    )
except Exception as e:
    logger.error(f"cryptography库初始化失败: {e}")


def check_dependencies() -> Dict[str, bool]:
    """
    检查必需依赖是否可用
    
    Returns:
        Dict[str, bool]: 依赖名称和可用状态
    """
    return {
        "cryptography": CRYPTOGRAPHY_AVAILABLE,
        "PySide2": True,  # 如果能导入此模块，PySide2就可用
    }


class SecurityUtils:
    """
    安全工具类
    """

    # PBKDF2 算法常量
    PBKDF2_ITERATIONS = 100000  # 迭代次数，OWASP 推荐值
    PBKDF2_KEY_LENGTH = 32  # 密钥长度（字节）
    SALT_LENGTH = 16  # 盐值长度（字节）

    @staticmethod
    def encrypt_password(password: str, salt: Optional[str] = None) -> str:
        """
        加密密码

        Args:
            password: 原始密码
            salt: 盐值，如果不提供则生成

        Returns:
            str: 加密后的密码
        """
        try:
            if not salt:
                # 生成随机盐值
                import secrets
                salt = secrets.token_hex(SecurityUtils.SALT_LENGTH)
            
            # 使用PBKDF2算法加密
            import binascii
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            from cryptography.hazmat.backends import default_backend

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=SecurityUtils.PBKDF2_KEY_LENGTH,
                salt=salt.encode(),
                iterations=SecurityUtils.PBKDF2_ITERATIONS,
                backend=default_backend()
            )
            
            key = kdf.derive(password.encode())
            hashed_password = binascii.hexlify(key).decode()
            
            # 返回盐值和加密后的密码，格式为：salt$hashed_password
            return f"{salt}${hashed_password}"
        except ImportError:
            # 如果cryptography库不可用，使用简单的哈希方法
            logger.warning("cryptography库不可用，使用简单哈希方法")
            if not salt:
                salt = hashlib.md5(str(hash(password)).encode()).hexdigest()
            combined = password + salt
            hashed = hashlib.sha256(combined.encode()).hexdigest()
            return f"{salt}${hashed}"
        except Exception as e:
            logger.error(f"密码加密失败: {str(e)}")
            # 降级方案：使用简单的哈希
            if not salt:
                salt = hashlib.md5(str(hash(password)).encode()).hexdigest()
            combined = password + salt
            hashed = hashlib.sha256(combined.encode()).hexdigest()
            return f"{salt}${hashed}"

    @staticmethod
    def verify_password(password: str, encrypted_password: str) -> bool:
        """
        验证密码

        Args:
            password: 原始密码
            encrypted_password: 加密后的密码

        Returns:
            bool: 密码是否正确
        """
        try:
            if "$" not in encrypted_password:
                logger.error("加密密码格式错误")
                return False
            
            salt, hashed = encrypted_password.split("$", 1)
            
            # 使用相同的盐值加密输入密码
            encrypted_input = SecurityUtils.encrypt_password(password, salt)
            input_salt, input_hashed = encrypted_input.split("$", 1)
            
            return input_hashed == hashed
        except Exception as e:
            logger.error(f"密码验证失败: {str(e)}")
            return False

    @staticmethod
    def validate_input(input_str: str, validation_type: str) -> bool:
        """
        验证输入

        Args:
            input_str: 输入字符串
            validation_type: 验证类型

        Returns:
            bool: 输入是否有效
        """
        validations = {
            "server": r"^[a-zA-Z0-9.-]+$",
            "port": r"^[0-9]+$",
            "namespace": r"^[a-zA-Z0-9_]+$",
            "username": r"^[a-zA-Z0-9_]+$",
            "password": r".+",
            "db_type": r"^(IRIS|Cache)$",
            "sql_query": r".+",
        }

        if validation_type not in validations:
            logger.error(f"未知的验证类型: {validation_type}")
            return False

        pattern = validations[validation_type]
        return bool(re.match(pattern, input_str))

    @staticmethod
    def execute_query_safe(
        connection, 
        query: str, 
        params: Optional[Tuple] = None
    ) -> Optional[List[Dict]]:
        """
        使用参数化查询安全执行SQL

        Args:
            connection: 数据库连接对象
            query: SQL查询语句，使用 ? 作为参数占位符
            params: 查询参数元组

        Returns:
            Optional[List[Dict]]: 查询结果列表，失败返回None

        Example:
            >>> results = execute_query_safe(conn, 
            ...                              "SELECT * FROM users WHERE id = ?", 
            ...                              (user_id,))
        """
        if not connection:
            logger.error("数据库连接为空")
            return None

        cursor = None
        try:
            cursor = connection.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # 获取列名
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            # 转换为字典列表
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            return results

        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            return None
        finally:
            if cursor:
                cursor.close()  # type: ignore

    @staticmethod
    def validate_sql_query(query: str) -> bool:
        """
        验证SQL查询是否安全

        Args:
            query: SQL查询语句

        Returns:
            bool: 查询是否安全
        """
        # 检查危险的SQL关键字
        dangerous_keywords = [
            "DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT",
            "UPDATE", "EXEC", "EXECUTE", "xp_", "sp_"
        ]

        query_upper = query.upper()
        for keyword in dangerous_keywords:
            if f" {keyword} " in query_upper or query_upper.startswith(keyword + " "):
                logger.warning(f"检测到危险的SQL关键字: {keyword}")
                return False

        return True

    @staticmethod
    def generate_token(length: int = 32) -> str:
        """
        生成安全的随机令牌

        Args:
            length: 令牌长度

        Returns:
            str: 随机令牌
        """
        try:
            import secrets
            return secrets.token_hex(length // 2)
        except ImportError:
            # 如果secrets库不可用，使用os.urandom
            import os
            return base64.b64encode(os.urandom(length)).decode()[:length]

    @staticmethod
    def secure_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        安全处理配置字典

        Args:
            config: 原始配置字典

        Returns:
            Dict[str, any]: 安全处理后的配置字典
        """
        secured_config = config.copy()

        # 加密数据库密码
        if "database" in secured_config and "password" in secured_config["database"]:
            password = secured_config["database"]["password"]
            if password and not "$" in password:
                secured_config["database"]["password"] = SecurityUtils.encrypt_password(password)

        return secured_config


def sanitize_sql_input(input_str: str) -> str:
    """
    清理SQL输入（已弃用，请使用参数化查询）

    .. deprecated::
        此方法使用简单字符替换，存在安全风险。
        请改用 execute_query_safe() 方法。
    """
    warnings.warn(
        "sanitize_sql_input is deprecated. Use execute_query_safe with parameterized queries instead.",
        DeprecationWarning,
        stacklevel=2
    )

    dangerous_chars = ["'", "\"", ";", "--", "/*", "*/", "xp_"]
    for char in dangerous_chars:
        input_str = input_str.replace(char, "")
    return input_str


# 创建全局安全工具实例（向后兼容）
security_utils = SecurityUtils()


def get_security_utils() -> SecurityUtils:
    """
    获取全局安全工具实例（优先使用DI容器）

    Returns:
        SecurityUtils: 安全工具实例
    """
    # 首先尝试从DI容器获取
    try:
        from src.infrastructure.di import get_container, resolve
        from src.infrastructure.di.service_registration import ISecurityUtils

        container = get_container()
        if container.is_registered(ISecurityUtils):
            return resolve(ISecurityUtils)
    except Exception:
        pass

    # 回退到本地单例
    return security_utils
