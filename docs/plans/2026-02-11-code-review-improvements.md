# PyWindows 项目代码审查改进计划

> **基于代码审查报告**: `CODE_REVIEW_REPORT.md`
> **生成日期**: 2026-02-11
> **审查评分**: 7.3/10

---

## 执行摘要

本次代码审查发现了3个Critical、4个Important和3个Minor级别的问题。本计划旨在系统性地解决这些问题，进一步提升项目质量。

**总体目标**: 将项目评分从7.3/10提升至8.5/10

---

## 问题清单

### Critical（严重问题）- 立即处理

| 问题ID | 问题描述 | 位置 | 优先级 |
|--------|---------|------|--------|
| CRIT-001 | 弱密码哈希降级方案 | security_utils.py:105-120 | P0 |
| CRIT-002 | SQL注入测试用例不足 | test_parameterized_query.py | P0 |
| CRIT-003 | 全局状态管理影响测试 | 多个模块 | P1 |

### Important（重要问题）- 短期处理

| 问题ID | 问题描述 | 位置 | 优先级 |
|--------|---------|------|--------|
| IMP-001 | 连接池并发控制 | database_repository.py:64-87 | P1 |
| IMP-002 | 循环导入风险 | config_manager.py | P1 |
| IMP-003 | IRIS驱动检测可靠性 | database_repository.py:393 | P2 |
| IMP-004 | 备份文件未清理 | presentation/windows/ | P2 |

### Minor（轻微问题）- 中期处理

| 问题ID | 问题描述 | 位置 | 优先级 |
|--------|---------|------|--------|
| MIN-001 | 私有方法文档不完整 | 多个文件 | P2 |
| MIN-002 | 类型注解缺失 | 部分文件 | P3 |
| MIN-003 | 缺少集成测试 | tests/ | P3 |

---

## 详细执行计划

### Phase 1: Critical 修复（安全优先）

#### CRIT-001: 改进密码哈希降级方案

**问题描述**:
当前降级方案使用MD5生成盐值，不符合密码学安全要求。

**当前代码** (security_utils.py:105-120):
```python
except ImportError:
    # 使用简单的哈希方法
    if not salt:
        salt = hashlib.md5(str(hash(password)).encode()).hexdigest()  # ❌ 不安全
    combined = password + salt
    hashed = hashlib.sha256(combined.encode()).hexdigest()
```

**改进方案**:

```python
except ImportError:
    logger.warning("cryptography库不可用，使用bcrypt降级方案")
    try:
        import bcrypt
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode(), salt).decode()
        return f"{salt}${hashed}"
    except ImportError:
        # 最终降级：使用安全的随机盐
        import secrets
        salt = secrets.token_hex(32)  # 256位随机盐
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            100000  # 保持相同迭代次数
        ).hexdigest()
        return f"{salt}${hashed}"
```

**文件修改**:
- `src/infrastructure/security/security_utils.py`

**测试**:
- 创建 `test_password_fallback.py`

**验收标准**:
- [ ] 降级方案不使用MD5
- [ ] 使用安全的随机盐（至少128位）
- [ ] 保持PBKDF2迭代次数（100000）
- [ ] 新测试通过

---

#### CRIT-002: 增强SQL注入测试

**问题描述**:
现有测试用例较少，缺少边界测试和恶意输入测试。

**当前测试** (test_parameterized_query.py):
- `test_execute_query_with_params` ✓
- `test_sql_injection_prevention` ✓
- `test_deprecated_sanitize_warning` ✓

**新增测试用例**:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SQL注入防护增强测试

覆盖更多攻击向量和边界情况
"""

import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, 'D:\\pywindows')


class TestSQLInjectionEnhanced(unittest.TestCase):
    """SQL注入防护增强测试"""

    def test_union_based_injection(self):
        """测试UNION-based注入"""
        from src.infrastructure.security.security_utils import SecurityUtils

        security = SecurityUtils()
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.description = [("id",)]
        mock_cursor.fetchall.return_value = []

        malicious = "1 UNION SELECT password FROM users --"
        query = "SELECT * FROM products WHERE id = ?"

        result = security.execute_query_safe(mock_conn, query, (malicious,))

        # 参数被当作字符串处理，不会执行UNION
        mock_cursor.execute.assert_called_once_with(query, (malicious,))
        self.assertEqual(len(result), 0)

    def test_boolean_based_injection(self):
        """测试布尔盲注"""
        from src.infrastructure.security.security_utils import SecurityUtils

        security = SecurityUtils()
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.description = [("id",)]
        mock_cursor.fetchall.return_value = []

        malicious = "' OR '1'='1"
        query = "SELECT * FROM users WHERE name = ?"

        result = security.execute_query_safe(mock_conn, query, (malicious,))

        # 参数化查询阻止了注入
        mock_cursor.execute.assert_called_once_with(query, (malicious,))

    def test_time_based_injection(self):
        """测试时间盲注"""
        from src.infrastructure.security.security_utils import SecurityUtils

        security = SecurityUtils()
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.description = [("id",)]
        mock_cursor.fetchall.return_value = []

        malicious = "'; WAITFOR DELAY '0:0:5'--"
        query = "SELECT * FROM orders WHERE id = ?"

        result = security.execute_query_safe(mock_conn, query, (malicious,))

        # 参数化查询阻止了WAITFOR语句
        mock_cursor.execute.assert_called_once_with(query, (malicious,))

    def test_null_byte_injection(self):
        """测试NULL字节注入"""
        from src.infrastructure.security.security_utils import SecurityUtils

        security = SecurityUtils()
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.description = [("data",)]
        mock_cursor.fetchall.return_value = [("test\x00data",)]

        malicious = "valid\x00UNSELECTABLE"
        query = "SELECT data FROM config WHERE key = ?"

        result = security.execute_query_safe(mock_conn, query, (malicious,))

        # NULL字节被正确处理
        mock_cursor.execute.assert_called_once_with(query, (malicious,))

    def test_multiple_params_injection(self):
        """测试多参数查询注入"""
        from src.infrastructure.security.security_utils import SecurityUtils

        security = SecurityUtils()
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchall.return_value = []

        malicious = "admin'--"
        query = "SELECT * FROM users WHERE id = ? AND name = ?"

        result = security.execute_query_safe(
            mock_conn, query, (1, malicious)
        )

        # 第二个参数被正确转义
        mock_cursor.execute.assert_called_once_with(
            query, (1, malicious)
        )

    def test_like_clause_injection(self):
        """测试LIKE子句注入"""
        from src.infrastructure.security.security_utils import SecurityUtils

        security = SecurityUtils()
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.description = [("name",)]
        mock_cursor.fetchall.return_value = []

        malicious = "%' UNION SELECT * FROM users--"
        query = "SELECT name FROM products WHERE name LIKE ?"

        result = security.execute_query_safe(mock_conn, query, (f"%{malicious}",))

        # LIKE参数中的%被当作普通字符处理
        mock_cursor.execute.assert_called_once()


class TestSQLValidationEnhanced(unittest.TestCase):
    """SQL验证增强测试"""

    def test_nested_query_detection(self):
        """测试嵌套查询检测"""
        from src.infrastructure.security.security_utils import SecurityUtils

        security = SecurityUtils()

        # 检测到嵌套SELECT
        result = security.validate_sql_query(
            "SELECT * FROM users WHERE id = (SELECT id FROM admins)"
        )
        self.assertFalse(result)

    def test_procedure_detection(self):
        """测试存储过程调用检测"""
        from src.infrastructure.security.security_utils import SecurityUtils

        security = SecurityUtils()

        # 检测到EXEC
        result = security.validate_sql_query("EXEC sp_who")
        self.assertFalse(result)

        # 检测到EXECUTE
        result = security.validate_sql_query("EXECUTE master.dbo.xp_cmdshell 'dir'")
        self.assertFalse(result)

    def test_comment_injection(self):
        """测试注释注入"""
        from src.infrastructure.security.security_utils import SecurityUtils

        security = SecurityUtils()

        malicious = "valid' /* malicious */ UNION SELECT--"
        result = security.validate_sql_query(
            f"SELECT * FROM products WHERE name = '{malicious}'"
        )
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
```

**文件修改**:
- `tests/unit/test_sql_injection_enhanced.py` (新增)

**验收标准**:
- [ ] 新增6个以上测试用例
- [ ] 覆盖UNION注入、布尔盲注、时间盲注
- [ ] 所有测试通过

---

#### CRIT-003: 改进全局状态管理

**问题描述**:
全局单例（如`security_utils`、`db_repository`）使单元测试难以隔离。

**改进方案**:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
服务工厂模块

提供测试友好的服务创建接口
"""

from typing import Any, Dict, Optional, Type, TypeVar

T = TypeVar('T')


class ServiceFactory:
    """
    服务工厂类

    支持创建真实实例和模拟实例，便于测试
    """

    # Mock实例缓存
    _mocks: Dict[str, Any] = {}

    @classmethod
    def set_mock(cls, service_type: str, mock_instance: Any) -> None:
        """
        设置模拟实例

        Args:
            service_type: 服务类型标识
            mock_instance: 模拟实例
        """
        cls._mocks[service_type] = mock_instance

    @classmethod
    def clear_mocks(cls) -> None:
        """清除所有模拟实例"""
        cls._mocks.clear()

    @classmethod
    def create_security_utils(cls, testing: bool = False) -> Any:
        """
        创建SecurityUtils实例

        Args:
            testing: 是否为测试模式

        Returns:
            SecurityUtils实例
        """
        if testing and 'security' in cls._mocks:
            return cls._mocks['security']

        from src.infrastructure.security.security_utils import SecurityUtils
        return SecurityUtils()

    @classmethod
    def create_config_manager(cls, testing: bool = False, config_file: str = None) -> Any:
        """
        创建ConfigManager实例

        Args:
            testing: 是否为测试模式
            config_file: 配置文件路径

        Returns:
            ConfigManager实例
        """
        if testing and 'config' in cls._mocks:
            return cls._mocks['config']

        from src.infrastructure.config.config_manager import ConfigManager
        return ConfigManager(config_file or "config.json")

    @classmethod
    def create_database_repository(cls, testing: bool = False) -> Any:
        """
        创建DatabaseRepository实例

        Args:
            testing: 是否为测试模式

        Returns:
            DatabaseRepository实例
        """
        if testing and 'repository' in cls._mocks:
            return cls._mocks['repository']

        from src.data.repositories.database_repository import DatabaseRepository
        return DatabaseRepository()


# 便捷函数
def get_security_utils(testing: bool = False) -> Any:
    """获取SecurityUtils实例"""
    return ServiceFactory.create_security_utils(testing)


def get_config_manager(testing: bool = False, config_file: str = None) -> Any:
    """获取ConfigManager实例"""
    return ServiceFactory.create_config_manager(testing, config_file)


def get_db_repository(testing: bool = False) -> Any:
    """获取DatabaseRepository实例"""
    return ServiceFactory.create_database_repository(testing)
```

**文件修改**:
- `src/infrastructure/utils/service_factory.py` (增强)
- `tests/unit/test_service_factory.py` (增强)

**验收标准**:
- [ ] ServiceFactory支持创建Mock实例
- [ ] 提供便捷函数`get_*`支持testing参数
- [ ] 单元测试可以使用Mock隔离依赖
- [ ] 向后兼容现有代码

---

### Phase 2: Important 修复

#### IMP-001: 改进连接池并发控制

**问题描述**:
持有锁时调用`_is_connection_valid`可能阻塞。

**改进方案**:

```python
def get_connection(self, connection_params: Dict[str, Any], timeout: float = 30.0) -> Optional[Tuple[Any, Any]]:
    """
    获取数据库连接（改进版）

    Args:
        connection_params: 连接参数
        timeout: 获取连接超时时间（秒）

    Returns:
        (connection, cursor) 元组
    """
    import time
    start_time = time.time()

    with self.lock:
        # 快速检查可用连接
        for i, conn_info in enumerate(self.connections):
            conn, cursor, params, last_used = conn_info
            # 只检查必要条件，不执行查询
            if params == connection_params and not self._is_connection_expired(conn_info):
                # 标记为使用中
                conn_info[3] = datetime.now()
                return conn, cursor

        # 创建新连接
        if len(self.connections) < self.max_connections:
            conn_cursor = self._create_connection(connection_params)
            if conn_cursor:
                self.connections.append([
                    conn_cursor[0],
                    conn_cursor[1],
                    connection_params,
                    datetime.now()
                ])
                return conn_cursor

        return None

def _is_connection_expired(self, conn_info: list) -> bool:
    """
    检查连接是否过期（轻量级检查）

    Args:
        conn_info: 连接信息列表

    Returns:
        bool: 是否过期
    """
    _, _, _, last_used = conn_info
    return (datetime.now() - last_used).total_seconds() > self.timeout
```

**文件修改**:
- `src/data/repositories/database_repository.py`

**验收标准**:
- [ ] 移除持有锁时的数据库查询
- [ ] 使用轻量级过期检查
- [ ] 连接池测试通过

---

#### IMP-002: 解决循环导入

**问题描述**:
`config_manager.py`依赖`security_utils.py`，而`security_utils.py`又可能被其他模块导入。

**改进方案**:
将`secure_config`逻辑移到独立模块：

```python
# src/infrastructure/utils/config_security.py

"""
配置安全工具模块

提供配置加密和安全的工具函数
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def secure_config(config: Dict[str, Any], security_utils=None) -> Dict[str, Any]:
    """
    安全处理配置字典

    Args:
        config: 原始配置字典
        security_utils: 安全工具实例（可选）

    Returns:
        安全处理后的配置字典
    """
    secured_config = config.copy()

    # 加密数据库密码
    if "database" in secured_config and "password" in secured_config:
        password = secured_config["database"]["password"]
        if password and "$" not in password:
            if security_utils:
                secured_config["database"]["password"] = security_utils.encrypt_password(password)
            else:
                # 直接使用hashlib（降级方案）
                import hashlib
                secured_config["database"]["password"] = hashlib.sha256(
                    password.encode()
                ).hexdigest()

    return secured_config
```

然后修改`config_manager.py`:

```python
# 移除 from src.infrastructure.security.security_utils import get_security_utils
from src.infrastructure.utils.config_security import secure_config

class ConfigManager:
    def save(self) -> bool:
        # ...
        secured_config = secure_config(self.config, self.security_utils)
        # ...
```

**文件修改**:
- `src/infrastructure/utils/config_security.py` (新增)
- `src/infrastructure/config/config_manager.py`

**验收标准**:
- [ ] 移除config_manager对security_utils的循环依赖
- [ ] 单元测试导入无错误
- [ ] 配置保存功能正常

---

#### IMP-003: 改进IRIS驱动检测

**改进方案**:

```python
# 使用明确的接口检测
class IRISDriverInterface:
    """IRIS驱动接口"""

    @property
    def iris(self):
        """IRIS属性"""
        pass

    @property
    def isIRIS(self):
        """是否IRIS驱动"""
        pass


def detect_driver_type(connection) -> str:
    """
    检测数据库驱动类型

    Args:
        connection: 数据库连接

    Returns:
        驱动类型: "iris" / "pyodbc" / "unknown"
    """
    # 检查IRIS特定属性
    if isinstance(connection, IRISDriverInterface):
        return "iris"

    # 检查hasattr（向后兼容）
    if hasattr(connection, 'iris') or hasattr(connection, 'isIRIS'):
        return "iris"

    # 默认使用pyodbc
    return "pyodbc"
```

**文件修改**:
- `src/data/repositories/database_repository.py`

---

#### IMP-004: 清理备份文件

**任务**:
- 检查`presentation/windows/`目录
- 移除或归档`.py`备份文件
- 更新`.gitignore`防止再次提交

**文件修改**:
- `presentation/windows/main_window_backup.py` (删除)
- `presentation/windows/main_window_new.py` (删除或重命名)
- `.gitignore` (更新)

---

### Phase 3: Minor 改进

#### MIN-001: 补充私有方法文档

**任务**:
- 审查所有私有方法（以`_`开头）
- 补充Args/Returns说明

---

#### MIN-002: 完善类型注解

**任务**:
- 检查返回类型注解缺失的方法
- 补充完整类型注解

---

#### MIN-003: 添加集成测试

**任务**:
- 创建`tests/integration/`目录
- 添加DatabaseRepository集成测试
- 添加端到端测试

---

## 测试计划

### 新增测试文件

1. `tests/unit/test_password_fallback.py` - 密码哈希降级测试
2. `tests/unit/test_sql_injection_enhanced.py` - SQL注入增强测试
3. `tests/unit/test_service_factory.py` - 服务工厂测试
4. `tests/unit/test_config_security.py` - 配置安全测试
5. `tests/integration/test_database_repository.py` - 数据库仓库集成测试

### 测试命令

```bash
# 运行所有新增测试
python -m pytest tests/unit/test_password_fallback.py -v
python -m pytest tests/unit/test_sql_injection_enhanced.py -v
python -m pytest tests/unit/test_service_factory.py -v
python -m pytest tests/unit/test_config_security.py -v
python -m pytest tests/integration/ -v

# 运行完整测试套件
python -m pytest tests/unit -v
```

---

## 时间估算

| Phase | 任务 | 预计时间 | 优先级 |
|-------|------|---------|--------|
| Phase 1 | CRIT-001 密码哈希改进 | 2小时 | P0 |
| Phase 1 | CRIT-002 SQL注入测试增强 | 3小时 | P0 |
| Phase 1 | CRIT-003 全局状态改进 | 2小时 | P1 |
| Phase 2 | IMP-001 连接池并发改进 | 3小时 | P1 |
| Phase 2 | IMP-002 循环导入解决 | 2小时 | P1 |
| Phase 2 | IMP-003 IRIS驱动检测改进 | 1小时 | P2 |
| Phase 2 | IMP-004 清理备份文件 | 0.5小时 | P2 |
| Phase 3 | MIN-001 文档补充 | 2小时 | P2 |
| Phase 3 | MIN-002 类型注解完善 | 2小时 | P3 |
| Phase 3 | MIN-003 集成测试添加 | 4小时 | P3 |
| **总计** | | **21.5小时** | |

---

## 验收标准

### 安全性
- [ ] 降级方案不使用MD5
- [ ] SQL注入防护测试覆盖主要攻击向量
- [ ] 安全模块可Mock用于测试

### 架构
- [ ] 移除config_manager循环依赖
- [ ] 连接池无阻塞锁操作
- [ ] 驱动检测使用明确接口

### 代码质量
- [ ] 所有私有方法有完整文档
- [ ] 返回类型注解完整
- [ ] 集成测试覆盖核心功能

### 项目健康
- [ ] 清理所有备份文件
- [ ] 所有新增测试通过
- [ ] 回归测试100%通过

---

## 风险评估

| 风险 | 影响 | 可能性 | 缓解措施 |
|------|------|--------|---------|
| 降级方案破坏现有功能 | 高 | 低 | 添加单元测试，使用渐进式部署 |
| 连接池修改影响稳定性 | 高 | 中 | 充分测试，保留旧代码作为备份 |
| 循环导入修复引入新问题 | 中 | 低 | 逐步修改，每次修改后运行测试 |

---

## 后续行动

1. **立即执行**: Phase 1 (Critical问题)
2. **短期目标**: Phase 2完成
3. **中期目标**: Phase 3完成
4. **长期目标**: 持续改进，达到8.5/10评分

---

**计划完成时间**: 2026-02-11
**计划保存路径**: `docs/plans/2026-02-11-code-review-improvements.md`
