# 代码审查问题整改计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复代码审查中发现的Critical和Important级别问题，提升代码质量和安全性

**Architecture:** 采用TDD方式逐步修复，优先解决安全风险（SQL注入、连接泄露），然后统一架构（DI容器单例管理），最后完善配置和线程安全

**Tech Stack:** Python, PySide2, pytest, SQLite/Database drivers

---

## 执行顺序概览

**Phase 1: 安全修复 (Critical)** - 立即执行
- Task 1: 修复SQL注入漏洞（参数化查询）
- Task 2: 修复连接池泄露（健康检查）

**Phase 2: 架构统一 (Important)** - 第2周
- Task 3: 统一单例管理（迁移到DI容器）
- Task 4: 添加循环依赖检测

**Phase 3: 配置与并发 (Important)** - 第3周  
- Task 5: 添加依赖声明与缺失处理
- Task 6: 提取硬编码配置值
- Task 7: 修复ConfigManager并发写问题

**Phase 4: 代码质量 (Minor)** - 第4周
- Task 8: 统一工厂函数模式
- Task 9: 清理魔法字符串和类型检查

---

## Phase 1: 安全修复 (Critical)

### Task 1: 修复SQL注入漏洞

**问题:** `sanitize_sql_input` 使用简单字符替换，容易被绕过
**文件:** `src/infrastructure/security/security_utils.py:151-180`

**Files:**
- Modify: `src/infrastructure/security/security_utils.py:151-180`
- Create: `tests/unit/test_parameterized_query.py`

**Step 1: 编写失败的参数化查询测试**

创建测试文件 `tests/unit/test_parameterized_query.py`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
参数化查询测试

验证新的execute_query_safe方法使用参数化查询防止SQL注入
"""

import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, 'D:\\pywindows')


class TestParameterizedQuery(unittest.TestCase):
    """参数化查询测试"""
    
    def test_execute_query_with_params(self):
        """测试带参数的执行方法"""
        from src.infrastructure.security.security_utils import SecurityUtils
        
        security = SecurityUtils()
        
        # 模拟数据库连接
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        # 测试参数化查询
        query = "SELECT * FROM users WHERE id = ? AND name = ?"
        params = (1, "admin")
        
        result = security.execute_query_safe(mock_conn, query, params)
        
        # 验证使用了参数化查询
        mock_cursor.execute.assert_called_once_with(query, params)
        self.assertTrue(result)
    
    def test_sql_injection_prevention(self):
        """测试SQL注入防护"""
        from src.infrastructure.security.security_utils import SecurityUtils
        
        security = SecurityUtils()
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        # 尝试SQL注入
        malicious_input = "1 OR 1=1"
        query = "SELECT * FROM users WHERE id = ?"
        
        result = security.execute_query_safe(mock_conn, query, (malicious_input,))
        
        # 参数应该被正确转义，不会执行恶意代码
        mock_cursor.execute.assert_called_once_with(query, (malicious_input,))
        self.assertTrue(result)
    
    def test_deprecated_sanitize_warning(self):
        """测试旧方法已弃用并发出警告"""
        import warnings
        from src.infrastructure.security.security_utils import sanitize_sql_input
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = sanitize_sql_input("test'; DROP TABLE users; --")
            
            # 应该发出弃用警告
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[0].category, DeprecationWarning))


if __name__ == "__main__":
    unittest.main()
```

**Step 2: 运行测试验证失败**

```bash
python tests/unit/test_parameterized_query.py
```

Expected: FAIL - `execute_query_safe` not defined

**Step 3: 实现参数化查询方法**

修改 `src/infrastructure/security/security_utils.py:151-180`:

```python
import warnings
from typing import Optional, List, Dict, Tuple, Union

def sanitize_sql_input(value: str) -> str:
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
        value = value.replace(char, "")
    return value


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
        if 'cursor' in locals():
            cursor.close()
```

**Step 4: 运行测试验证通过**

```bash
python tests/unit/test_parameterized_query.py -v
```

Expected: PASS (3 tests)

**Step 5: 提交**

```bash
git add tests/unit/test_parameterized_query.py src/infrastructure/security/security_utils.py
git commit -m "security: add parameterized query support and deprecate sanitize_sql_input

- Add execute_query_safe() with parameterized query support
- Mark sanitize_sql_input() as deprecated with warning
- Add comprehensive tests for SQL injection prevention
- Fixes critical SQL injection vulnerability"
```

---

### Task 2: 修复连接池连接泄露

**问题:** `release_connection` 仅更新时间戳，未实际关闭无效连接
**文件:** `src/data/repositories/database_repository.py:25-162`

**Files:**
- Modify: `src/data/repositories/database_repository.py:25-162`
- Create: `tests/unit/test_connection_pool_health.py`

**Step 1: 编写连接池健康检查测试**

创建 `tests/unit/test_connection_pool_health.py`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
连接池健康检查测试

验证连接池的连接健康检查和自动清理功能
"""

import sys
import time
import unittest
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, 'D:\\pywindows')


class TestConnectionPoolHealth(unittest.TestCase):
    """连接池健康检查测试"""
    
    def setUp(self):
        """设置测试环境"""
        from src.data.repositories.database_repository import ConnectionPool
        self.pool = ConnectionPool()
        self.pool.max_connections = 3
        self.pool.connection_timeout = 2  # 2秒超时便于测试
    
    def test_connection_health_check(self):
        """测试连接健康检查"""
        # 创建模拟连接
        mock_conn = Mock()
        mock_conn.is_connected.return_value = True
        
        # 健康的连接应该返回True
        is_healthy = self.pool._is_connection_healthy(mock_conn)
        self.assertTrue(is_healthy)
        
        # 断开的连接应该返回False
        mock_conn.is_connected.return_value = False
        is_healthy = self.pool._is_connection_healthy(mock_conn)
        self.assertFalse(is_healthy)
    
    def test_connection_expiry(self):
        """测试连接过期检测"""
        mock_conn = Mock()
        
        # 添加连接
        self.pool.connections["test_driver"]["conn_1"] = {
            "connection": mock_conn,
            "in_use": False,
            "last_used": time.time() - 10  # 10秒前使用
        }
        
        # 检查过期（超时设置为2秒）
        expired = self.pool._get_expired_connections("test_driver")
        self.assertEqual(len(expired), 1)
        self.assertIn("conn_1", expired)
    
    def test_auto_cleanup_expired_connections(self):
        """测试自动清理过期连接"""
        mock_conn = Mock()
        
        # 添加过期连接
        self.pool.connections["test_driver"]["old_conn"] = {
            "connection": mock_conn,
            "in_use": False,
            "last_used": time.time() - 10  # 10秒前
        }
        
        # 执行清理
        self.pool.cleanup_expired_connections()
        
        # 验证连接已关闭并移除
        mock_conn.close.assert_called_once()
        self.assertNotIn("old_conn", self.pool.connections["test_driver"])
    
    def test_release_closes_unhealthy_connection(self):
        """测试释放时关闭不健康连接"""
        mock_conn = Mock()
        mock_conn.is_connected.return_value = False  # 不健康
        
        # 添加连接
        self.pool.connections["test_driver"]["unhealthy_conn"] = {
            "connection": mock_conn,
            "in_use": True,
            "last_used": time.time()
        }
        
        # 释放连接
        self.pool.release_connection("test_driver", "unhealthy_conn")
        
        # 不健康连接应该被关闭
        mock_conn.close.assert_called_once()
        self.assertNotIn("unhealthy_conn", self.pool.connections["test_driver"])


if __name__ == "__main__":
    unittest.main()
```

**Step 2: 运行测试验证失败**

```bash
python tests/unit/test_connection_pool_health.py
```

Expected: FAIL - methods not defined

**Step 3: 实现连接池健康检查**

修改 `src/data/repositories/database_repository.py`:

```python
import threading
import time
import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    """连接信息"""
    connection: Any
    in_use: bool = False
    last_used: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)


class ConnectionPool:
    """
    数据库连接池
    
    支持连接健康检查、超时清理和自动释放
    """
    
    def __init__(self, max_connections: int = 10, connection_timeout: int = 300):
        """
        初始化连接池
        
        Args:
            max_connections: 最大连接数
            connection_timeout: 连接超时时间（秒）
        """
        self.connections: Dict[str, Dict[str, ConnectionInfo]] = {}
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self._lock = threading.RLock()
        
        # 启动清理线程
        self._start_cleanup_thread()
        
        logger.info(f"连接池初始化完成，最大连接数: {max_connections}")
    
    def _start_cleanup_thread(self) -> None:
        """启动定期清理线程"""
        def cleanup_worker():
            while True:
                time.sleep(60)  # 每分钟清理一次
                try:
                    self.cleanup_expired_connections()
                except Exception as e:
                    logger.error(f"清理线程出错: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        logger.debug("连接池清理线程已启动")
    
    def _is_connection_healthy(self, connection: Any) -> bool:
        """
        检查连接是否健康
        
        Args:
            connection: 数据库连接对象
            
        Returns:
            bool: 连接是否健康
        """
        try:
            # 检查连接是否有is_connected方法
            if hasattr(connection, 'is_connected'):
                return connection.is_connected()
            
            # 否则尝试执行简单查询
            if hasattr(connection, 'cursor'):
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                return True
            
            return True  # 无法检查时假设健康
        except Exception as e:
            logger.warning(f"连接健康检查失败: {e}")
            return False
    
    def _get_expired_connections(self, driver_type: str) -> List[str]:
        """
        获取已过期的连接ID列表
        
        Args:
            driver_type: 驱动类型
            
        Returns:
            List[str]: 过期连接ID列表
        """
        expired = []
        current_time = time.time()
        
        if driver_type not in self.connections:
            return expired
        
        for conn_id, conn_info in self.connections[driver_type].items():
            # 未使用且超时的连接
            if not conn_info.in_use and (current_time - conn_info.last_used > self.connection_timeout):
                expired.append(conn_id)
        
        return expired
    
    def cleanup_expired_connections(self) -> int:
        """
        清理所有过期的连接
        
        Returns:
            int: 清理的连接数
        """
        cleaned_count = 0
        
        with self._lock:
            for driver_type in list(self.connections.keys()):
                expired_ids = self._get_expired_connections(driver_type)
                
                for conn_id in expired_ids:
                    try:
                        conn_info = self.connections[driver_type][conn_id]
                        if hasattr(conn_info.connection, 'close'):
                            conn_info.connection.close()
                        del self.connections[driver_type][conn_id]
                        cleaned_count += 1
                        logger.debug(f"清理过期连接: {driver_type}/{conn_id}")
                    except Exception as e:
                        logger.error(f"清理连接失败 {conn_id}: {e}")
        
        if cleaned_count > 0:
            logger.info(f"清理了 {cleaned_count} 个过期连接")
        
        return cleaned_count
    
    def release_connection(self, driver_type: str, conn_id: str) -> None:
        """
        释放连接回连接池
        
        Args:
            driver_type: 驱动类型
            conn_id: 连接ID
        """
        with self._lock:
            if driver_type not in self.connections or conn_id not in self.connections[driver_type]:
                return
            
            conn_info = self.connections[driver_type][conn_id]
            
            # 检查连接健康状态
            if not self._is_connection_healthy(conn_info.connection):
                # 不健康则关闭并移除
                try:
                    if hasattr(conn_info.connection, 'close'):
                        conn_info.connection.close()
                    logger.warning(f"关闭不健康连接: {driver_type}/{conn_id}")
                except Exception as e:
                    logger.error(f"关闭连接失败: {e}")
                
                del self.connections[driver_type][conn_id]
                return
            
            # 健康的连接标记为未使用并更新时间
            conn_info.in_use = False
            conn_info.last_used = time.time()
            logger.debug(f"释放连接: {driver_type}/{conn_id}")
    
    def get_connection(self, driver_type: str, conn_id: str) -> Optional[Any]:
        """获取连接（如需要则先清理不健康连接）"""
        with self._lock:
            if driver_type not in self.connections or conn_id not in self.connections[driver_type]:
                return None
            
            conn_info = self.connections[driver_type][conn_id]
            
            # 使用前检查健康状态
            if not self._is_connection_healthy(conn_info.connection):
                logger.warning(f"检测到不健康连接，重新创建: {driver_type}/{conn_id}")
                # 关闭旧连接
                try:
                    if hasattr(conn_info.connection, 'close'):
                        conn_info.connection.close()
                except:
                    pass
                
                # 移除并返回None让调用方重新创建
                del self.connections[driver_type][conn_id]
                return None
            
            conn_info.in_use = True
            return conn_info.connection
    
    def close_all(self) -> None:
        """关闭所有连接"""
        with self._lock:
            for driver_type, connections in self.connections.items():
                for conn_id, conn_info in connections.items():
                    try:
                        if hasattr(conn_info.connection, 'close'):
                            conn_info.connection.close()
                        logger.debug(f"关闭连接: {driver_type}/{conn_id}")
                    except Exception as e:
                        logger.error(f"关闭连接失败 {conn_id}: {e}")
            
            self.connections.clear()
            logger.info("所有连接已关闭")
```

**Step 4: 运行测试验证通过**

```bash
python tests/unit/test_connection_pool_health.py -v
```

Expected: PASS (4 tests)

**Step 5: 提交**

```bash
git add tests/unit/test_connection_pool_health.py src/data/repositories/database_repository.py
git commit -m "fix: add connection pool health check and auto cleanup

- Add connection health check (_is_connection_healthy)
- Add automatic cleanup of expired connections
- Close unhealthy connections on release
- Add cleanup background thread (runs every 60s)
- Add comprehensive health check tests
- Fixes connection leak vulnerability"
```

---

## Phase 2: 架构统一 (Important)

### Task 3: 统一单例管理（迁移到DI容器）

**问题:** 三种不同的单例实现方式
**影响:** `SecurityUtils`, `ScalingManager`, `DatabaseDriverFactory`

**Files:**
- Create: `src/infrastructure/di/singleton_migration.py`
- Modify: `src/infrastructure/security/security_utils.py:223-234`
- Modify: `src/infrastructure/utils/scaling_manager.py:51-69`
- Modify: `src/data/repositories/driver_factory.py:60-68`
- Create: `tests/unit/test_singleton_migration.py`

**Step 1: 编写单例迁移测试**

创建 `tests/unit/test_singleton_migration.py`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
单例迁移测试

验证所有单例都通过DI容器管理
"""

import sys
import unittest

sys.path.insert(0, 'D:\\pywindows')


class TestSingletonMigration(unittest.TestCase):
    """单例迁移测试"""
    
    def test_security_utils_via_di(self):
        """测试SecurityUtils通过DI容器获取"""
        from src.infrastructure.di.service_registration import ISecurityUtils, get_service
        
        security1 = get_service(ISecurityUtils)
        security2 = get_service(ISecurityUtils)
        
        # DI管理的应该是同一个实例
        self.assertIs(security1, security2)
    
    def test_scaling_manager_via_di(self):
        """测试ScalingManager通过DI容器获取"""
        from src.infrastructure.di.service_registration import IScalingManager, get_service
        
        scaling1 = get_service(IScalingManager)
        scaling2 = get_service(IScalingManager)
        
        self.assertIs(scaling1, scaling2)
    
    def test_database_factory_via_di(self):
        """测试DatabaseDriverFactory通过DI容器获取"""
        from src.infrastructure.di.service_registration import IDatabaseDriverFactory, get_service
        
        factory1 = get_service(IDatabaseDriverFactory)
        factory2 = get_service(IDatabaseDriverFactory)
        
        self.assertIs(factory1, factory2)
    
    def test_legacy_getters_delegate_to_di(self):
        """测试旧版getter委托给DI容器"""
        from src.infrastructure.utils.scaling_manager import get_scaling_manager
        from src.infrastructure.di.service_registration import IScalingManager, get_service
        
        # 旧方式和新方式应该返回同一实例
        legacy = get_scaling_manager()
        di_version = get_service(IScalingManager)
        
        self.assertIs(legacy, di_version)


if __name__ == "__main__":
    unittest.main()
```

**Step 2: 运行测试验证失败**

```bash
python tests/unit/test_singleton_migration.py
```

Expected: FAIL - ISecurityUtils not defined

**Step 3: 添加ISecurityUtils接口并修改服务注册**

修改 `src/infrastructure/di/service_registration.py`，添加:

```python
class ISecurityUtils(ABC):
    """安全工具接口"""
    
    @abstractmethod
    def encrypt_password(self, password: str) -> str:
        """加密密码"""
        pass
    
    @abstractmethod
    def verify_password(self, password: str, encrypted: str) -> bool:
        """验证密码"""
        pass
    
    @abstractmethod
    def execute_query_safe(self, connection, query: str, params: Optional[Tuple] = None):
        """安全执行查询"""
        pass


def register_security_service(container: DIContainer) -> None:
    """注册安全服务"""
    try:
        from src.infrastructure.security.security_utils import SecurityUtils
        
        # 确保类使用DI兼容的单例模式
        container.register_singleton(ISecurityUtils, SecurityUtils)
        logger.debug("注册安全服务完成")
    except Exception as e:
        logger.warning(f"注册安全服务失败: {e}")
```

**Step 4: 修改SecurityUtils使用DI兼容的单例**

修改 `src/infrastructure/security/security_utils.py:223-234`:

```python
# 全局实例缓存（由DI容器管理）
_security_utils_instance: Optional['SecurityUtils'] = None
_security_utils_lock = threading.Lock()


def get_security_utils() -> 'SecurityUtils':
    """
    获取SecurityUtils实例（向后兼容）
    
    优先使用DI容器，如果不存在则创建本地单例
    """
    global _security_utils_instance
    
    # 首先尝试从DI容器获取
    try:
        from src.infrastructure.di import resolve
        from src.infrastructure.di.service_registration import ISecurityUtils
        
        container = resolve(DIContainer)
        if container.is_registered(ISecurityUtils):
            return resolve(ISecurityUtils)
    except:
        pass
    
    # 回退到本地单例
    if _security_utils_instance is None:
        with _security_utils_lock:
            if _security_utils_instance is None:
                _security_utils_instance = SecurityUtils()
    
    return _security_utils_instance
```

**Step 5: 运行测试验证通过**

```bash
python tests/unit/test_singleton_migration.py -v
```

Expected: PASS (4 tests)

**Step 6: 提交**

```bash
git add tests/unit/test_singleton_migration.py \
    src/infrastructure/di/service_registration.py \
    src/infrastructure/security/security_utils.py
git commit -m "refactor: unify singleton management via DI container

- Add ISecurityUtils interface
- Register SecurityUtils in DI container
- Update get_security_utils() to delegate to DI
- Add migration tests for all singletons
- Prepare for removing legacy singleton patterns"
```

---

### Task 4: 添加循环依赖检测

**问题:** DI容器递归解析无循环依赖检测
**文件:** `src/infrastructure/di/container.py:290-322`

**Files:**
- Modify: `src/infrastructure/di/container.py:290-322`
- Create: `tests/unit/test_circular_dependency.py`

**Step 1: 编写循环依赖检测测试**

创建 `tests/unit/test_circular_dependency.py`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
循环依赖检测测试

验证DI容器能正确检测并报告循环依赖
"""

import sys
import unittest

sys.path.insert(0, 'D:\\pywindows')


class TestCircularDependency(unittest.TestCase):
    """循环依赖测试"""
    
    def test_direct_circular_dependency(self):
        """测试直接循环依赖检测"""
        from src.infrastructure.di import DIContainer
        
        container = DIContainer()
        
        # 定义循环依赖的类 A -> B -> A
        class ServiceA:
            def __init__(self, b: 'ServiceB'):
                self.b = b
        
        class ServiceB:
            def __init__(self, a: 'ServiceA'):
                self.a = a
        
        container.register_transient(ServiceA, ServiceA)
        container.register_transient(ServiceB, ServiceB)
        
        # 应该抛出循环依赖异常
        with self.assertRaises(Exception) as context:
            container.resolve(ServiceA)
        
        self.assertIn("循环依赖", str(context.exception))
    
    def test_indirect_circular_dependency(self):
        """测试间接循环依赖检测"""
        from src.infrastructure.di import DIContainer
        
        container = DIContainer()
        
        # A -> B -> C -> A
        class ServiceA:
            def __init__(self, b: 'ServiceB'):
                self.b = b
        
        class ServiceB:
            def __init__(self, c: 'ServiceC'):
                self.c = c
        
        class ServiceC:
            def __init__(self, a: 'ServiceA'):
                self.a = a
        
        container.register_transient(ServiceA, ServiceA)
        container.register_transient(ServiceB, ServiceB)
        container.register_transient(ServiceC, ServiceC)
        
        with self.assertRaises(Exception) as context:
            container.resolve(ServiceA)
        
        self.assertIn("循环依赖", str(context.exception))


if __name__ == "__main__":
    unittest.main()
```

**Step 2: 运行测试验证失败**

```bash
python tests/unit/test_circular_dependency.py
```

Expected: FAIL - no circular dependency detection

**Step 3: 实现循环依赖检测**

修改 `src/infrastructure/di/container.py`，在 `DIContainer.__init__` 添加:

```python
def __init__(self):
    """初始化容器"""
    self._services: Dict[Type, ServiceDescriptor] = {}
    self._singletons: Dict[Type, Any] = {}
    self._scopes: Dict[str, Dict[Type, Any]] = {}
    self._lock = threading.RLock()
    self._resolution_stack: List[Type] = []  # 添加解析栈用于循环依赖检测
    
    logger.debug("DIContainer 初始化完成")
```

修改 `resolve` 方法:

```python
def resolve(self, interface: Type[T], scope_id: Optional[str] = None) -> T:
    """
    解析服务（带循环依赖检测）
    
    Raises:
        KeyError: 服务未注册
        RuntimeError: 检测到循环依赖
    """
    # 检测循环依赖
    if interface in self._resolution_stack:
        cycle = " -> ".join([t.__name__ for t in self._resolution_stack + [interface]])
        raise RuntimeError(f"检测到循环依赖: {cycle}")
    
    with self._lock:
        if interface not in self._services:
            raise KeyError(f"服务未注册: {interface.__name__}")
        
        # 添加到解析栈
        self._resolution_stack.append(interface)
        
        try:
            descriptor = self._services[interface]
            
            # 根据生命周期返回实例
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                return self._get_singleton(descriptor)
            elif descriptor.lifetime == ServiceLifetime.SCOPED:
                if scope_id is None:
                    raise ValueError(f"作用域服务 {interface.__name__} 需要提供 scope_id")
                return self._get_scoped(descriptor, scope_id)
            else:  # TRANSIENT
                return self._create_instance(descriptor)
        finally:
            # 从解析栈移除
            self._resolution_stack.pop()
```

**Step 4: 运行测试验证通过**

```bash
python tests/unit/test_circular_dependency.py -v
```

Expected: PASS (2 tests)

**Step 5: 提交**

```bash
git add tests/unit/test_circular_dependency.py src/infrastructure/di/container.py
git commit -m "feat: add circular dependency detection to DI container

- Add resolution stack tracking
- Detect and report circular dependencies with path
- Add tests for direct and indirect circular dependencies
- Improves debugging of complex service graphs"
```

---

## Phase 3: 配置与并发 (Important)

### Task 5: 添加依赖声明与缺失处理

**问题:** `cryptography` 列为可选但直接导入
**文件:** `src/infrastructure/security/security_utils.py:48-50`

**Files:**
- Modify: `requirements.txt`
- Modify: `src/infrastructure/security/security_utils.py:48-50`

**Step 1: 检查当前依赖**

```bash
cat requirements.txt | grep -i crypto
```

Expected: cryptography not listed or marked optional

**Step 2: 更新 requirements.txt**

修改 `requirements.txt`，添加:

```
# Core dependencies
PySide2>=5.15.0
requests>=2.25.0

# Security (required)
cryptography>=3.4.8

# Database drivers (optional based on usage)
# cx_Oracle>=8.0.0  # Oracle support
# pymysql>=1.0.0     # MySQL support
# psycopg2>=2.8.0    # PostgreSQL support
# pyodbc>=4.0.0      # SQL Server support
# intersystems-irispython>=3.2.0  # IRIS support
```

**Step 3: 改进缺失依赖处理**

修改 `src/infrastructure/security/security_utils.py:48-50`:

```python
# 尝试导入加密库
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError as e:
    CRYPTOGRAPHY_AVAILABLE = False
    # 记录错误但不阻止导入 - 将在初始化时检查
    import logging
    logging.getLogger(__name__).warning(
        f"cryptography库未安装 ({e})，密码加密将使用降级方案。"
        f"请运行: pip install cryptography"
    )
    Fernet = None
    hashes = None
    PBKDF2HMAC = None


class SecurityUtils:
    """安全工具类"""
    
    def __init__(self):
        """初始化安全工具"""
        if not CRYPTOGRAPHY_AVAILABLE:
            logger.warning(
                "使用降级加密方案（SHA256）。生产环境请安装cryptography: "
                "pip install cryptography"
            )
        self._init_encryption()
```

**Step 4: 添加安装检查脚本**

创建 `scripts/check_dependencies.py`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
依赖检查脚本

检查所有必需依赖是否已安装
"""

import sys
import importlib


def check_dependency(package: str, import_name: str = None) -> bool:
    """检查依赖是否可用"""
    try:
        importlib.import_module(import_name or package)
        return True
    except ImportError:
        return False


def main():
    """主函数"""
    required = [
        ("PySide2", "PySide2"),
        ("requests", "requests"),
        ("cryptography", "cryptography"),
    ]
    
    optional = [
        ("cx_Oracle", "Oracle database support"),
        ("pymysql", "MySQL database support"),
        ("psycopg2", "PostgreSQL database support"),
        ("pyodbc", "SQL Server database support"),
    ]
    
    print("检查必需依赖...")
    all_required_ok = True
    for package, import_name in required:
        if check_dependency(package, import_name):
            print(f"  ✓ {package}")
        else:
            print(f"  ✗ {package} (缺失)")
            all_required_ok = False
    
    print("\n检查可选依赖...")
    for package, description in optional:
        if check_dependency(package):
            print(f"  ✓ {package} ({description})")
        else:
            print(f"  ○ {package} ({description}, 未安装)")
    
    if not all_required_ok:
        print("\n错误: 有必需依赖缺失!")
        print("请运行: pip install -r requirements.txt")
        sys.exit(1)
    
    print("\n所有必需依赖已安装!")
    sys.exit(0)


if __name__ == "__main__":
    main()
```

**Step 5: 提交**

```bash
git add requirements.txt src/infrastructure/security/security_utils.py scripts/check_dependencies.py
git commit -m "build: add cryptography as required dependency with better handling

- Add cryptography to requirements.txt (required)
- Improve ImportError handling with helpful messages
- Add dependency check script
- Warn users about fallback encryption"
```

---

### Task 6: 提取硬编码配置值

**问题:** 端口1972、数据库类型等硬编码
**文件:** `src/infrastructure/config/config_manager.py:71-77`, `src/data/repositories/driver_factory.py:445-451`

**Files:**
- Create: `src/infrastructure/config/constants.py`
- Modify: `src/infrastructure/config/config_manager.py:71-77`
- Modify: `src/data/repositories/driver_factory.py:445-451`

**Step 1: 创建配置常量文件**

创建 `src/infrastructure/config/constants.py`:

```python
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


class DatabaseTypes:
    """数据库类型常量"""
    
    IRIS = "IRIS"
    CACHE = "Cache"
    MYSQL = "MySQL"
    POSTGRESQL = "PostgreSQL"
    SQLSERVER = "SQLServer"
    ORACLE = "Oracle"
    
    @classmethod
    def all_types(cls) -> list:
        """返回所有支持的数据库类型"""
        return [cls.IRIS, cls.CACHE, cls.MYSQL, cls.POSTGRESQL, cls.SQLSERVER, cls.ORACLE]


class SecurityConfig:
    """安全配置"""
    
    # PBKDF2迭代次数
    PBKDF2_ITERATIONS = 100000
    
    # 盐值长度
    SALT_LENGTH = 32
    
    # Token过期时间（秒）
    TOKEN_EXPIRY = 3600


class UIConfigDefaults:
    """UI默认配置"""
    
    # 默认字体大小
    FONT_SIZE = 10
    
    # 默认缩放比例
    SCALE_FACTOR = 1.0
    
    # 窗口默认尺寸
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 600


class PoolConfig:
    """连接池配置"""
    
    # 最大连接数
    MAX_CONNECTIONS = 10
    
    # 连接超时（秒）
    CONNECTION_TIMEOUT = 300
    
    # 清理间隔（秒）
    CLEANUP_INTERVAL = 60
```

**Step 2: 更新配置管理器使用常量**

修改 `src/infrastructure/config/config_manager.py`:

```python
from src.infrastructure.config.constants import DatabaseDefaults, DatabaseTypes

# 修改默认配置生成
DEFAULT_CONFIG = {
    "database": {
        "server": "localhost",
        "port": DatabaseDefaults.PORT_DEFAULT,  # 使用常量
        "namespace": "USER",
        "username": "_SYSTEM",
        "password": "",
        "driver_type": DatabaseTypes.IRIS,  # 使用常量
        "timeout": DatabaseDefaults.TIMEOUT_CONNECT,
        "charset": DatabaseDefaults.CHARSET,
    },
    # ... 其他配置
}
```

**Step 3: 更新驱动工厂使用常量**

修改 `src/data/repositories/driver_factory.py`:

```python
from src.infrastructure.config.constants import DatabaseTypes, DatabaseDefaults

# 修改默认端口映射
DEFAULT_PORTS = {
    DatabaseTypes.IRIS: DatabaseDefaults.PORT_DEFAULT,
    DatabaseTypes.CACHE: DatabaseDefaults.PORT_DEFAULT,
    DatabaseTypes.MYSQL: DatabaseDefaults.PORT_MYSQL,
    DatabaseTypes.POSTGRESQL: DatabaseDefaults.PORT_POSTGRESQL,
    DatabaseTypes.SQLSERVER: DatabaseDefaults.PORT_SQLSERVER,
    DatabaseTypes.ORACLE: DatabaseDefaults.PORT_ORACLE,
}

# 修改驱动创建
class DatabaseDriverFactory:
    """数据库驱动工厂"""
    
    SUPPORTED_DRIVERS = DatabaseTypes.all_types()  # 使用常量
```

**Step 4: 提交**

```bash
git add src/infrastructure/config/constants.py \
    src/infrastructure/config/config_manager.py \
    src/data/repositories/driver_factory.py
git commit -m "refactor: extract hardcoded values to constants module

- Add centralized constants module
- Extract database ports, timeouts, types
- Extract security and UI defaults
- Update config manager and driver factory to use constants
- Improves maintainability and reduces magic numbers"
```

---

### Task 7: 修复ConfigManager并发写问题

**问题:** `save()` 方法未处理并发写
**文件:** `src/infrastructure/config/config_manager.py:149-180`

**Files:**
- Modify: `src/infrastructure/config/config_manager.py:149-180`
- Create: `tests/unit/test_config_manager_threading.py`

**Step 1: 编写并发写测试**

创建 `tests/unit/test_config_manager_threading.py`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理器线程安全测试

验证ConfigManager的save方法线程安全
"""

import sys
import threading
import time
import tempfile
import os
import unittest

sys.path.insert(0, 'D:\\pywindows')


class TestConfigManagerThreading(unittest.TestCase):
    """配置管理器线程安全测试"""
    
    def test_concurrent_save(self):
        """测试并发保存不会损坏配置文件"""
        from src.infrastructure.config.config_manager import ConfigManager
        
        # 使用临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
            f.write('{"test": "initial"}')
        
        try:
            manager = ConfigManager(temp_path)
            errors = []
            
            def save_config(thread_id):
                try:
                    for i in range(10):
                        manager.set(f"thread_{thread_id}", f"value_{i}")
                        manager.save()
                        time.sleep(0.01)
                except Exception as e:
                    errors.append(str(e))
            
            # 启动多个线程并发保存
            threads = []
            for i in range(5):
                t = threading.Thread(target=save_config, args=(i,))
                threads.append(t)
            
            for t in threads:
                t.start()
            
            for t in threads:
                t.join()
            
            # 验证没有错误
            self.assertEqual(len(errors), 0, f"并发保存出错: {errors}")
            
            # 验证配置可以正常加载
            manager2 = ConfigManager(temp_path)
            self.assertIsNotNone(manager2.config)
            
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()
```

**Step 2: 运行测试验证失败**

```bash
python tests/unit/test_config_manager_threading.py
```

Expected: FAIL - 可能出现并发写入错误

**Step 3: 实现线程安全的save方法**

修改 `src/infrastructure/config/config_manager.py`:

```python
import threading
import tempfile
import shutil

class ConfigManager:
    """配置管理器（线程安全）"""
    
    def __init__(self, config_file: str = "config.json"):
        """初始化配置管理器"""
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self._lock = threading.RLock()  # 添加锁
        self._file_lock = threading.Lock()  # 文件操作专用锁
        self._load_config()
    
    def save(self) -> bool:
        """
        保存配置到文件（线程安全）
        
        使用临时文件+原子重命名避免并发写入损坏
        
        Returns:
            bool: 是否保存成功
        """
        with self._file_lock:  # 文件操作加锁
            try:
                # 使用临时文件
                temp_file = f"{self.config_file}.tmp"
                
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
                
                # 原子重命名（保证完整性）
                shutil.move(temp_file, self.config_file)
                
                logger.debug("配置保存成功")
                return True
                
            except Exception as e:
                logger.error(f"保存配置失败: {e}")
                # 清理临时文件
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                return False
```

**Step 4: 运行测试验证通过**

```bash
python tests/unit/test_config_manager_threading.py -v
```

Expected: PASS

**Step 5: 提交**

```bash
git add tests/unit/test_config_manager_threading.py src/infrastructure/config/config_manager.py
git commit -m "fix: make ConfigManager thread-safe

- Add RLock for thread-safe config access
- Add file_lock for save operations
- Use atomic file rename (temp file + move)
- Add concurrent save test
- Fixes race condition in config saves"
```

---

## Phase 4: 代码质量 (Minor)

### Task 8: 统一工厂函数模式

**问题:** 多个 `get_*_manager()` 函数模式重复

**Files:**
- Create: `src/infrastructure/utils/service_factory.py`
- Modify: 各服务的 `get_*` 函数委托到工厂

**Step 1: 创建统一服务工厂**

创建 `src/infrastructure/utils/service_factory.py`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
服务工厂

统一的服务获取工厂，支持DI容器和传统单例模式
"""

import threading
from typing import TypeVar, Type, Callable, Optional, Any

T = TypeVar('T')


class ServiceFactory:
    """
    服务工厂
    
    统一管理服务的创建和获取，支持：
    - DI容器模式（优先）
    - 传统单例模式（回退）
    """
    
    _instances: dict = {}
    _locks: dict = {}
    _global_lock = threading.Lock()
    
    @classmethod
    def get_service(
        cls,
        interface: Type[T],
        implementation_class: Type[T],
        factory_func: Optional[Callable[[], T]] = None
    ) -> T:
        """
        获取服务实例
        
        优先尝试DI容器，否则使用本地单例
        
        Args:
            interface: 服务接口类型
            implementation_class: 实现类
            factory_func: 可选的工厂函数
            
        Returns:
            服务实例
        """
        # 首先尝试DI容器
        try:
            from src.infrastructure.di import resolve
            from src.infrastructure.di import DIContainer
            
            container = resolve(DIContainer)
            if container.is_registered(interface):
                return resolve(interface)
        except:
            pass
        
        # 回退到本地单例
        return cls._get_singleton(interface, implementation_class, factory_func)
    
    @classmethod
    def _get_singleton(
        cls,
        interface: Type[T],
        implementation_class: Type[T],
        factory_func: Optional[Callable[[], T]] = None
    ) -> T:
        """获取本地单例"""
        # 初始化锁
        if interface not in cls._locks:
            with cls._global_lock:
                if interface not in cls._locks:
                    cls._locks[interface] = threading.Lock()
        
        # 双重检查锁定
        if interface not in cls._instances:
            with cls._locks[interface]:
                if interface not in cls._instances:
                    if factory_func:
                        instance = factory_func()
                    else:
                        instance = implementation_class()
                    cls._instances[interface] = instance
        
        return cls._instances[interface]
    
    @classmethod
    def clear_singleton(cls, interface: Type) -> None:
        """清除单例（用于测试）"""
        if interface in cls._instances:
            del cls._instances[interface]
    
    @classmethod
    def clear_all(cls) -> None:
        """清除所有单例"""
        cls._instances.clear()


def get_service(interface: Type[T]) -> T:
    """
    便捷函数：从DI容器获取服务
    
    Args:
        interface: 服务接口
        
    Returns:
        服务实例
    """
    from src.infrastructure.di import resolve
    return resolve(interface)
```

**Step 2: 更新ScalingManager使用工厂**

修改 `src/infrastructure/utils/scaling_manager.py`:

```python
def get_scaling_manager() -> 'ScalingManager':
    """
    获取ScalingManager实例（向后兼容）
    
    Returns:
        ScalingManager: 单例实例
    """
    from src.infrastructure.utils.service_factory import ServiceFactory
    from src.infrastructure.di.service_registration import IScalingManager
    
    return ServiceFactory.get_service(
        IScalingManager,
        ScalingManager,
        lambda: ScalingManager()
    )
```

**Step 3: 提交**

```bash
git add src/infrastructure/utils/service_factory.py \
    src/infrastructure/utils/scaling_manager.py
git commit -m "refactor: unify service factory pattern

- Add ServiceFactory for consistent singleton management
- Support DI container (priority) and local singleton (fallback)
- Update get_scaling_manager to use factory
- Reduces code duplication across service getters"
```

---

### Task 9: 清理魔法字符串和类型检查

**问题:** 魔法字符串、颜色硬编码、多处 `# type: ignore`

**Files:**
- Create: `src/presentation/theme.py`
- Modify: `src/presentation/windows/main_window.py:40-57`
- Modify: `src/main.py:90, 148`

**Step 1: 创建主题配置**

创建 `src/presentation/theme.py`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI主题配置

集中管理颜色、字体、尺寸等UI常量
"""

from typing import Dict, Tuple


class Colors:
    """颜色定义"""
    
    # 主色调
    PRIMARY = "#2196F3"
    PRIMARY_DARK = "#1976D2"
    PRIMARY_LIGHT = "#BBDEFB"
    
    # 强调色
    ACCENT = "#FF4081"
    
    # 背景色
    BACKGROUND = "#FFFFFF"
    SURFACE = "#F5F5F5"
    
    # 文字色
    TEXT_PRIMARY = "#212121"
    TEXT_SECONDARY = "#757575"
    TEXT_DISABLED = "#BDBDBD"
    
    # 状态色
    SUCCESS = "#4CAF50"
    WARNING = "#FF9800"
    ERROR = "#F44336"
    INFO = "#2196F3"
    
    # 边框和分隔线
    BORDER = "#E0E0E0"
    DIVIDER = "#BDBDBD"


class Fonts:
    """字体定义"""
    
    FAMILY = "Microsoft YaHei"
    SIZE_SMALL = 9
    SIZE_NORMAL = 10
    SIZE_LARGE = 12
    SIZE_TITLE = 14


class Dimensions:
    """尺寸定义"""
    
    PADDING_SMALL = 4
    PADDING_NORMAL = 8
    PADDING_LARGE = 16
    
    BORDER_RADIUS = 4
    BUTTON_HEIGHT = 32
    INPUT_HEIGHT = 28


def get_stylesheet() -> str:
    """获取全局样式表"""
    return f"""
    QMainWindow {{
        background-color: {Colors.BACKGROUND};
    }}
    
    QPushButton {{
        background-color: {Colors.PRIMARY};
        color: white;
        border: none;
        padding: {Dimensions.PADDING_NORMAL}px {Dimensions.PADDING_LARGE}px;
        border-radius: {Dimensions.BORDER_RADIUS}px;
        font-family: '{Fonts.FAMILY}';
        font-size: {Fonts.SIZE_NORMAL}pt;
        min-height: {Dimensions.BUTTON_HEIGHT}px;
    }}
    
    QPushButton:hover {{
        background-color: {Colors.PRIMARY_DARK};
    }}
    
    QPushButton:disabled {{
        background-color: {Colors.TEXT_DISABLED};
    }}
    
    QLineEdit, QTextEdit, QComboBox {{
        border: 1px solid {Colors.BORDER};
        border-radius: {Dimensions.BORDER_RADIUS}px;
        padding: {Dimensions.PADDING_SMALL}px;
        background-color: {Colors.BACKGROUND};
        font-family: '{Fonts.FAMILY}';
        font-size: {Fonts.SIZE_NORMAL}pt;
        min-height: {Dimensions.INPUT_HEIGHT}px;
    }}
    
    QLineEdit:focus, QTextEdit:focus {{
        border-color: {Colors.PRIMARY};
    }}
    """
```

**Step 2: 更新main_window使用主题**

修改 `src/presentation/windows/main_window.py`:

```python
from src.presentation.theme import Colors, Fonts, Dimensions, get_stylesheet

# 替换硬编码颜色
# 旧代码: color = "#2196F3"
# 新代码: color = Colors.PRIMARY
```

**Step 3: 修复main.py中的类型检查**

修改 `src/main.py:90, 148`:

```python
# 旧代码（使用type: ignore）
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # type: ignore

# 新代码（正确类型注解）
from PySide2.QtCore import Qt
from PySide2.QtCore import QCoreApplication

QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
```

**Step 4: 提交**

```bash
git add src/presentation/theme.py \
    src/presentation/windows/main_window.py \
    src/main.py
git commit -m "style: extract magic strings to theme config and fix type hints

- Add centralized theme configuration (colors, fonts, dimensions)
- Replace hardcoded colors with theme constants
- Fix type hints to remove # type: ignore comments
- Improves maintainability and type safety"
```

---

## 完成总结

### 任务清单

**Phase 1: Critical (立即)**
- [ ] Task 1: SQL注入修复（参数化查询）
- [ ] Task 2: 连接池泄露修复（健康检查）

**Phase 2: Important (第2周)**
- [ ] Task 3: 单例管理统一
- [ ] Task 4: 循环依赖检测

**Phase 3: Important (第3周)**
- [ ] Task 5: 依赖声明与处理
- [ ] Task 6: 硬编码配置提取
- [ ] Task 7: 并发写保护

**Phase 4: Minor (第4周)**
- [ ] Task 8: 工厂函数统一
- [ ] Task 9: 魔法字符串清理

### 预计工作量
- **Phase 1**: 4-6小时
- **Phase 2**: 6-8小时  
- **Phase 3**: 8-10小时
- **Phase 4**: 4-6小时
- **总计**: 22-30小时

### 风险评估
- **低风险**: Task 3, 4, 5, 6, 8, 9
- **中风险**: Task 7（需要充分测试）
- **高风险**: Task 1, 2（影响安全性，需彻底测试）

### 验收标准
1. 所有Critical问题已修复
2. 所有新功能有单元测试覆盖
3. 所有测试通过
4. 代码审查报告中的所有问题已解决或记录

---

**计划完成时间**: 2026-02-11
**计划保存路径**: `docs/plans/2026-02-11-code-review-fixes.md`
