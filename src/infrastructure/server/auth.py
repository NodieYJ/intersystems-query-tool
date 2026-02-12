#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
认证和安全模块

提供服务器安全功能：
- JWT认证
- 速率限制
- 权限检查
"""

import hashlib
import logging
import secrets
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class PermissionException(Exception):
    """权限异常"""
    def __init__(self, message, required_permission=None):
        super().__init__(message)
        self.required_permission = required_permission


@dataclass
class TokenInfo:
    """Token信息"""
    token: str
    user_id: str
    expires_at: float
    permissions: List[str]


class AuthManager:
    """
    认证管理器
    
    提供JWT风格的Token认证。
    
    示例:
        >>> auth = AuthManager(secret_key="my_secret")
        >>> token = auth.generate_token("user123", permissions=["read", "write"])
        >>> is_valid = auth.verify_token(token)
    """
    
    def __init__(
        self,
        secret_key: str,
        token_ttl: float = 3600.0,  # 1小时
        refresh_ttl: float = 86400.0  # 24小时
    ):
        """
        初始化认证管理器
        
        Args:
            secret_key: 密钥
            token_ttl: Token有效期（秒）
            refresh_ttl: 刷新Token有效期（秒）
        """
        self._secret_key = secret_key
        self._token_ttl = token_ttl
        self._refresh_ttl = refresh_ttl
        
        self._tokens: Dict[str, TokenInfo] = {}
        self._refresh_tokens: Dict[str, str] = {}  # refresh_token -> access_token
        self._revoked_tokens: Set[str] = set()
        
        logger.info("AuthManager initialized")
    
    def generate_token(
        self,
        user_id: str,
        permissions: Optional[List[str]] = None,
        **claims: Any
    ) -> Tuple[str, str]:
        """
        生成Token对（访问Token + 刷新Token）
        
        Args:
            user_id: 用户ID
            permissions: 权限列表
            **claims: 自定义声明
            
        Returns:
            Tuple[str, str]: (访问Token, 刷新Token)
        """
        # 生成访问Token
        access_token = self._generate_token_string()
        expires_at = time.time() + self._token_ttl
        
        token_info = TokenInfo(
            token=access_token,
            user_id=user_id,
            expires_at=expires_at,
            permissions=permissions or []
        )
        
        self._tokens[access_token] = token_info
        
        # 生成刷新Token
        refresh_token = self._generate_token_string()
        self._refresh_tokens[refresh_token] = access_token
        
        logger.debug(f"Token generated for user: {user_id}")
        return access_token, refresh_token
    
    def _generate_token_string(self) -> str:
        """生成随机Token字符串"""
        return secrets.token_urlsafe(32)
    
    def verify_token(self, token: str) -> bool:
        """
        验证Token
        
        Args:
            token: Token字符串
            
        Returns:
            bool: 是否有效
        """
        # 检查是否被吊销
        if token in self._revoked_tokens:
            return False
        
        # 检查是否存在
        if token not in self._tokens:
            return False
        
        # 检查是否过期
        token_info = self._tokens[token]
        if time.time() > token_info.expires_at:
            return False
        
        return True
    
    def get_token_info(self, token: str) -> Optional[TokenInfo]:
        """
        获取Token信息
        
        Args:
            token: Token字符串
            
        Returns:
            Optional[TokenInfo]: Token信息
        """
        if not self.verify_token(token):
            return None
        return self._tokens.get(token)
    
    def revoke_token(self, token: str) -> bool:
        """
        吊销Token
        
        Args:
            token: Token字符串
            
        Returns:
            bool: 是否成功
        """
        if token not in self._tokens:
            return False
        
        self._revoked_tokens.add(token)
        del self._tokens[token]
        
        # 清理对应的刷新Token
        for refresh_token, access_token in list(self._refresh_tokens.items()):
            if access_token == token:
                del self._refresh_tokens[refresh_token]
        
        logger.debug(f"Token revoked: {token[:16]}...")
        return True
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        使用刷新Token获取新的访问Token
        
        Args:
            refresh_token: 刷新Token
            
        Returns:
            Optional[str]: 新的访问Token
        """
        if refresh_token not in self._refresh_tokens:
            return None
        
        old_access_token = self._refresh_tokens[refresh_token]
        
        if old_access_token not in self._tokens:
            return None
        
        token_info = self._tokens[old_access_token]
        
        # 吊销旧Token
        self.revoke_token(old_access_token)
        
        # 生成新Token
        new_access_token, new_refresh_token = self.generate_token(
            token_info.user_id,
            token_info.permissions
        )
        
        # 删除旧刷新Token
        del self._refresh_tokens[refresh_token]
        
        logger.debug(f"Token refreshed for user: {token_info.user_id}")
        return new_access_token
    
    def check_permission(self, token: str, permission: str) -> bool:
        """
        检查Token是否具有指定权限
        
        Args:
            token: Token字符串
            permission: 权限名称
            
        Returns:
            bool: 是否具有权限
        """
        token_info = self.get_token_info(token)
        if not token_info:
            return False
        
        return permission in token_info.permissions
    
    def require_permission(self, permission: str) -> Callable:
        """
        装饰器：要求指定权限
        
        Args:
            permission: 权限名称
            
        Returns:
            Callable: 装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            async def wrapper(*args, **kwargs):
                # 从kwargs中获取token
                token = kwargs.get('token') or kwargs.get('auth_token')
                
                if not token:
                    raise PermissionException("Authentication required")
                
                if not self.check_permission(token, permission):
                    raise PermissionException(
                        f"Permission required: {permission}",
                        required_permission=permission
                    )
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def cleanup_expired_tokens(self) -> int:
        """
        清理过期Token
        
        Returns:
            int: 清理的Token数量
        """
        current_time = time.time()
        expired = []
        
        for token, info in self._tokens.items():
            if current_time > info.expires_at:
                expired.append(token)
        
        for token in expired:
            self.revoke_token(token)
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired tokens")
        
        return len(expired)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'active_tokens': len(self._tokens),
            'revoked_tokens': len(self._revoked_tokens),
            'refresh_tokens': len(self._refresh_tokens)
        }


class RateLimiter:
    """
    速率限制器
    
    限制请求频率，防止滥用。
    
    示例:
        >>> limiter = RateLimiter(default_limit=100, window=60)
        >>> if limiter.allow_request("client_123"):
        ...     process_request()
    """
    
    def __init__(
        self,
        default_limit: int = 100,
        window: float = 60.0,
        burst_size: int = 10
    ):
        """
        初始化速率限制器
        
        Args:
            default_limit: 默认限制（请求数/窗口）
            window: 时间窗口（秒）
            burst_size: 突发容量
        """
        self._default_limit = default_limit
        self._window = window
        self._burst_size = burst_size
        
        # 客户端记录: {client_id: [(timestamp, count), ...]}
        self._client_records: Dict[str, List[Tuple[float, int]]] = {}
        
        # 特殊限制: {client_id: limit}
        self._custom_limits: Dict[str, int] = {}
        
        logger.info(f"RateLimiter initialized: {default_limit}/{window}s")
    
    def set_limit(self, client_id: str, limit: int) -> None:
        """
        设置客户端特殊限制
        
        Args:
            client_id: 客户端ID
            limit: 限制值
        """
        self._custom_limits[client_id] = limit
        logger.debug(f"Rate limit set for {client_id}: {limit}")
    
    def allow_request(self, client_id: str, cost: int = 1) -> bool:
        """
        检查是否允许请求
        
        Args:
            client_id: 客户端ID
            cost: 请求成本（默认1）
            
        Returns:
            bool: 是否允许
        """
        current_time = time.time()
        
        # 清理旧记录
        if client_id in self._client_records:
            cutoff = current_time - self._window
            self._client_records[client_id] = [
                (t, c) for t, c in self._client_records[client_id]
                if t > cutoff
            ]
        else:
            self._client_records[client_id] = []
        
        # 计算当前窗口内的请求数
        current_count = sum(c for _, c in self._client_records[client_id])
        
        # 获取限制
        limit = self._custom_limits.get(client_id, self._default_limit)
        
        # 检查是否允许
        if current_count + cost > limit + self._burst_size:
            logger.warning(f"Rate limit exceeded for {client_id}")
            return False
        
        # 记录请求
        self._client_records[client_id].append((current_time, cost))
        
        return True
    
    def get_remaining(self, client_id: str) -> int:
        """
        获取剩余配额
        
        Args:
            client_id: 客户端ID
            
        Returns:
            int: 剩余请求数
        """
        if client_id not in self._client_records:
            return self._custom_limits.get(client_id, self._default_limit)
        
        current_count = sum(c for _, c in self._client_records[client_id])
        limit = self._custom_limits.get(client_id, self._default_limit)
        
        return max(0, limit - current_count)
    
    def reset(self, client_id: str) -> None:
        """
        重置客户端限制
        
        Args:
            client_id: 客户端ID
        """
        if client_id in self._client_records:
            del self._client_records[client_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'tracked_clients': len(self._client_records),
            'custom_limits': len(self._custom_limits),
            'default_limit': self._default_limit,
            'window': self._window
        }


class PermissionChecker:
    """
    权限检查器
    
    检查用户权限。
    """
    
    def __init__(self):
        self._roles: Dict[str, List[str]] = {}  # role -> permissions
        self._user_roles: Dict[str, Set[str]] = {}  # user_id -> roles
    
    def define_role(self, role: str, permissions: List[str]) -> None:
        """
        定义角色权限
        
        Args:
            role: 角色名称
            permissions: 权限列表
        """
        self._roles[role] = permissions
    
    def assign_role(self, user_id: str, role: str) -> None:
        """
        分配角色给用户
        
        Args:
            user_id: 用户ID
            role: 角色名称
        """
        if user_id not in self._user_roles:
            self._user_roles[user_id] = set()
        self._user_roles[user_id].add(role)
    
    def check_permission(self, user_id: str, permission: str) -> bool:
        """
        检查用户是否具有权限
        
        Args:
            user_id: 用户ID
            permission: 权限名称
            
        Returns:
            bool: 是否具有权限
        """
        if user_id not in self._user_roles:
            return False
        
        for role in self._user_roles[user_id]:
            if role in self._roles and permission in self._roles[role]:
                return True
        
        return False
    
    def get_user_permissions(self, user_id: str) -> List[str]:
        """
        获取用户所有权限
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[str]: 权限列表
        """
        if user_id not in self._user_roles:
            return []
        
        permissions = set()
        for role in self._user_roles[user_id]:
            if role in self._roles:
                permissions.update(self._roles[role])
        
        return list(permissions)


# 便捷函数
def create_auth_manager(secret_key: str, **kwargs) -> AuthManager:
    """创建认证管理器"""
    return AuthManager(secret_key, **kwargs)


def create_rate_limiter(**kwargs) -> RateLimiter:
    """创建速率限制器"""
    return RateLimiter(**kwargs)


def create_permission_checker() -> PermissionChecker:
    """创建权限检查器"""
    return PermissionChecker()
