# 数据库代码审查报告

**审查日期**: 2026-02-12  
**审查范围**: `src/data/`, `src/business/services/`  
**审查人员**: Sisyphus AI (database-expert + python-expert)  
**代码质量评分**: B+ (78/100)

---

## 目录

1. [执行摘要](#执行摘要)
2. [审查范围](#审查范围)
3. [优点总结](#优点总结)
4. [问题清单](#问题清单)
5. [详细问题描述](#详细问题描述)
6. [修复建议](#修复建议)
7. [优先级矩阵](#优先级矩阵)
8. [附录](#附录)

---

## 执行摘要

本次代码审查覆盖了数据库相关的核心模块，包括连接池管理、SQL执行、驱动工厂和数据服务层。整体代码架构清晰，采用了分层架构设计，实现了连接池、重试机制和基本的SQL注入防护。然而，在安全性、稳定性和代码质量方面仍有改进空间。

**关键发现**:
- 🔴 Critical (严重): 2项
- 🟠 Important (重要): 4项  
- 🟡 Medium (中等): 5项
- 🟢 Low (低优先级): 3项

**建议**:
1. 优先修复 SQL 注入防护绕过风险
2. 改进连接池的健壮性
3. 统一代码风格和命名规范

---

## 审查范围

### 审查文件

| 文件 | 行数 | 主要功能 |
|------|------|----------|
| `src/data/repositories/database_repository.py` | 817 | 连接池、SQL执行、事务管理 |
| `src/data/repositories/driver_factory.py` | 564 | 驱动检测、连接创建工厂 |
| `src/business/services/data_service.py` | 496 | 数据服务、业务逻辑、输入验证 |
| `src/business/services/query_history_manager.py` | ~200 | 查询历史管理 |

### 架构概览

```
presentation/          # 表示层
  └─ dialogs/         # 对话框 (SQL查询、数据下载等)
business/              # 业务逻辑层
  └─ services/        # 服务层 (DataService, QueryHistoryManager)
data/                  # 数据访问层
  └─ repositories/    # 仓库层 (DatabaseRepository, DriverFactory)
infrastructure/        # 基础设施层
  ├─ config/          # 配置管理
  ├─ security/        # 安全工具
  └─ exceptions/      # 异常定义
```

---

## 优点总结

### 1. 连接池管理 ✅

`ConnectionPool` 类实现了完整的连接池管理：

- **连接复用**: 支持连接复用，减少连接开销
- **超时清理**: 定期清理过期连接，防止资源泄漏
- **健康检查**: 支持连接有效性验证
- **线程安全**: 使用 `threading.RLock` 保护共享状态

```python
class ConnectionPool:
    DEFAULT_CONNECTION_TIMEOUT = 30
    DEFAULT_QUERY_TIMEOUT = 30

    def __init__(self, max_connections=10, timeout=30):
        self.connections = []
        self.lock = threading.RLock()
        self._start_cleanup_thread()  # 后台清理线程
```

### 2. 重试机制 ✅

`_execute_with_retry` 方法实现了指数退避重试：

```python
def _execute_with_retry(self, operation, max_retries=None, timeout=None):
    max_retries = max_retries or self.DEFAULT_MAX_RETRIES
    for attempt in range(max_retries + 1):
        try:
            result = operation()
            return result
        except TimeoutError:
            if attempt < max_retries:
                delay = self.DEFAULT_RETRY_DELAY * (2 ** attempt)
                time.sleep(delay)  # 指数退避
```

### 3. 驱动工厂模式 ✅

`DatabaseDriverFactory` 单例管理多种数据库驱动：

- **延迟导入**: 避免模块级导入问题
- **多驱动支持**: IRIS 原生驱动 + pyodbc
- **自动检测**: 运行时检测可用驱动
- **连接回退**: 主驱动失败时自动切换

### 4. SQL 注入防护 ✅

`InputValidator` 类提供多层防护：

```python
class InputValidator:
    ALLOWED_SCHEMA_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

    @staticmethod
    def validate_query_not_dangerous(query: str) -> ValidationResult:
        # 检查危险关键字
        dangerous_keywords = [
            ("DROP", "DROP"),
            ("DELETE FROM", "DELETE"),
            # ...
        ]
```

### 5. 事务管理 ✅

完整的提交/回滚支持：

```python
try:
    cursor.execute(query, params)
    conn.commit()  # 提交事务
except Exception as e:
    conn.rollback()  # 回滚事务
    raise QueryExecutionException(...)
```

### 6. 详细的日志记录 ✅

所有数据库操作都有详细的日志记录，便于问题排查。

---

## 问题清单

### 🔴 Critical (严重) - 2项

| ID | 问题 | 文件 | 风险等级 |
|----|------|------|----------|
| C-1 | SQL 注入防护不完整 | `data_service.py:184-204` | 高 |
| C-2 | 连接池满时无等待机制 | `database_repository.py:95-106` | 高 |

### 🟠 Important (重要) - 4项

| ID | 问题 | 文件 | 风险等级 |
|----|------|------|----------|
| I-1 | 空 except 块吞噬异常 | `database_repository.py:127-133` | 中 |
| I-2 | 连接没有总存活时间限制 | `database_repository.py:246-262` | 中 |
| I-3 | 密码在错误信息中暴露 | `database_repository.py:603-607` | 中 |
| I-4 | 没有连接泄漏检测 | `database_repository.py` | 低 |

### 🟡 Medium (中等) - 5项

| ID | 问题 | 文件 | 影响 |
|----|------|------|------|
| M-1 | 方法命名不一致 | `database_repository.py` | 可维护性 |
| M-2 | 大结果集日志输出 | `database_repository.py:595` | 性能 |
| M-3 | 缺少数据库连接健康检查 | `data_service.py:240-251` | 可观测性 |
| M-4 | 驱动检测循环调用 | `driver_factory.py:159-170` | 性能 |
| M-5 | 查询历史未加密存储 | `query_history_manager.py` | 安全性 |

### 🟢 Low (低优先级) - 3项

| ID | 问题 | 文件 | 影响 |
|----|------|------|------|
| L-1 | 未使用上下文管理器 | `database_repository.py` | 代码优雅性 |
| L-2 | 缺少查询取消支持 | `database_repository.py` | 功能完整性 |
| L-3 | 没有查询性能监控 | `database_repository.py` | 可观测性 |

---

## 详细问题描述

### C-1: SQL 注入防护不完整

**文件**: `src/business/services/data_service.py:184-204`

#### 问题描述

当前 SQL 注入防护使用简单的关键字黑名单匹配，容易被多种技术绕过：

```python
dangerous_keywords = [
    ("DROP", "DROP"),
    ("DELETE FROM", "DELETE"),
    ("TRUNCATE", "TRUNCATE"),
    ("ALTER", "ALTER"),
    ("CREATE", "CREATE"),
    ("INSERT INTO", "INSERT"),
    ("UPDATE", "UPDATE"),
    ("EXEC", "EXEC"),
    ("EXECUTE", "EXECUTE"),
    ("xp_", "xp_"),
    ("sp_", "sp_"),
]

for keyword, description in dangerous_keywords:
    if keyword in query_upper:  # 简单的子串匹配
        return ValidationResult(is_valid=False, ...)
```

#### 绕过方式

1. **大小写变换**:
   ```
   DrOp TaBlE -> DROP TABLE
   ```

2. **注释绕过**:
   ```
   DRO/*comment*/P TABLE
   D/**/ROP TABLE
   ```

3. **十六进制编码**:
   ```
   0x44524F50 -> DROP
   ```

4. **字符串拼接**:
   ```
   ' || 'DROP' || ' TABLE
   ```

5. **变量赋值**:
   ```
   SET @x = 'DROP'; EXEC @x
   ```

#### 风险评估

- **影响**: 数据库数据泄露、篡改或删除
- **概率**: 中 (需要用户输入动态构建 SQL)
- **严重性**: 极高

#### 建议修复

1. **强制参数化查询**: 对于动态 SQL，必须使用参数化查询
2. **白名单验证**: 只允许特定的查询类型 (SELECT)
3. **输入净化**: 对用户输入进行严格的格式验证

```python
class InputValidator:
    # 只允许 SELECT 开头的查询
    ALLOWED_QUERY_PREFIX = ('SELECT', 'WITH')

    @staticmethod
    def validate_query(query: str, params: Optional[List[Any]] = None) -> ValidationResult:
        # 1. 必须使用参数化查询
        if params is None:
            return ValidationResult(
                is_valid=False,
                message="不允许执行未参数化的动态查询"
            )

        # 2. 检查查询前缀
        query_upper = query.strip().upper()
        if not query_upper.startswith(self.ALLOWED_QUERY_PREFIX):
            return ValidationResult(
                is_valid=False,
                message="只允许 SELECT 查询"
            )

        # 3. 验证参数类型
        if not InputValidator.validate_sql_query_params(tuple(params)):
            return ValidationResult(is_valid=False, message="参数包含危险内容")

        return ValidationResult(is_valid=True, message="Query validated")
```

---

### C-2: 连接池满时无等待机制

**文件**: `src/data/repositories/database_repository.py:95-106`

#### 问题描述

当连接池已满时，`get_connection` 方法直接返回 `None`，调用方没有重试机会：

```python
def get_connection(self, connection_params: Dict[str, Any]) -> Optional[Tuple[Any, Any]]:
    with self.lock:
        # 尝试从连接池获取可用连接
        for conn_info in self.connections:
            if params == connection_params and self._is_connection_valid(conn):
                conn_info[3] = datetime.now()
                return conn, cursor

        # 如果没有可用连接且未达到最大连接数，创建新连接
        if len(self.connections) < self.max_connections:
            conn_cursor = self._create_connection(connection_params)
            if conn_cursor:
                self.connections.append([conn, cursor, connection_params, datetime.now()])
                return conn, cursor

        # ⚠️ 连接池已满，直接返回 None
        self.logger.warning("连接池已满，无法获取连接")
        return None
```

#### 问题影响

1. **请求失败**: 高并发时连接获取失败，请求直接失败
2. **资源浪费**: 客户端需要实现自己的重试逻辑
3. **用户体验差**: 用户看到意外的错误

#### 风险评估

- **影响**: 系统可用性降低
- **概率**: 高 (高并发场景)
- **严重性**: 高

#### 建议修复

使用信号量实现有界阻塞等待：

```python
from threading import Semaphore, TimeoutError as ThreadingTimeoutError

class ConnectionPool:
    def __init__(self, max_connections: int = 10, timeout: int = 30):
        self.max_connections = max_connections
        self.timeout = timeout
        self.connections = []
        self.lock = threading.RLock()
        self.semaphore = Semaphore(max_connections)  # 信号量控制并发

    def get_connection(
        self,
        connection_params: Dict[str, Any],
        wait_timeout: Optional[float] = None
    ) -> Optional[Tuple[Any, Any]]:
        """
        获取数据库连接

        Args:
            connection_params: 连接参数
            wait_timeout: 等待超时时间（秒），None 表示无限等待

        Returns:
            Optional[Tuple[Any, Any]]: (connection, cursor) 元组，超时返回 None
        """
        wait_timeout = wait_timeout or self.timeout

        try:
            # 尝试获取信号量（控制同时获取的连接数）
            if not self.semaphore.acquire(timeout=wait_timeout):
                self.logger.warning("获取连接超时")
                return None
        except ThreadingTimeoutError:
            self.logger.warning("获取连接超时")
            return None

        try:
            with self.lock:
                # 尝试从连接池获取可用连接
                for conn_info in self.connections:
                    conn, cursor, params, last_used = conn_info
                    if params == connection_params and self._is_connection_valid(conn):
                        conn_info[3] = datetime.now()
                        return conn, cursor

                # 创建新连接
                conn_cursor = self._create_connection(connection_params)
                if conn_cursor:
                    conn, cursor = conn_cursor
                    self.connections.append([conn, cursor, connection_params, datetime.now()])
                    return conn, cursor

                # 创建失败，释放信号量
                self.semaphore.release()
                return None

        except Exception as e:
            self.semaphore.release()
            raise

    def release_connection(self, connection: Any):
        """释放连接回连接池"""
        with self.lock:
            for i, conn_info in enumerate(self.connections):
                conn, cursor, _, _ = conn_info
                if conn == connection:
                    # 检查连接健康状态
                    if not self._is_connection_healthy(conn):
                        self._close_connection(conn, cursor)
                        del self.connections[i]
                    else:
                        conn_info[3] = datetime.now()
                    break

        # 释放信号量
        self.semaphore.release()
```

---

### I-1: 空 except 块吞噬异常

**文件**: `src/data/repositories/database_repository.py:127-133`

#### 问题描述

多处使用空的 `except` 块，会吞噬所有异常，导致问题难以排查：

```python
def release_connection(self, connection: Any):
    with self.lock:
        for i, conn_info in enumerate(self.connections):
            conn, cursor, _, _ = conn_info
            if conn == connection:
                if not self._is_connection_healthy(conn):
                    self.logger.warning(f"关闭不健康连接 #{i}")
                    try:
                        if cursor:
                            try:
                                cursor.close()
                            except:  # ❌ 空 except
                                pass
                        if conn:
                            try:
                                conn.close()
                            except:  # ❌ 空 except
                                pass
                    except Exception as e:
                        self.logger.error(f"关闭不健康连接失败: {e}")

                    del self.connections[i]
                    return
```

#### 影响

1. 异常被静默忽略，问题难以发现
2. 可能导致资源泄漏 (连接未正确关闭)
3. 调试困难

#### 建议修复

```python
def release_connection(self, connection: Any):
    with self.lock:
        for i, conn_info in enumerate(self.connections):
            conn, cursor, _, _ = conn_info
            if conn == connection:
                if not self._is_connection_healthy(conn):
                    self._close_connection(conn, cursor, i)
                    del self.connections[i]
                    return

    def _close_connection(self, conn, cursor, index: int):
        """安全关闭连接"""
        for name, obj in [("cursor", cursor), ("connection", conn)]:
            if obj is not None:
                try:
                    obj.close()
                    self.logger.debug(f"已关闭 {name} #{index}")
                except Exception as e:
                    self.logger.warning(f"关闭 {name} #{index} 时出现异常: {e}")
```

---

### I-2: 连接没有总存活时间限制

**文件**: `src/data/repositories/database_repository.py:246-262`

#### 问题描述

当前只检查连接的空闲超时，没有限制连接的总存活时间：

```python
def _get_expired_connections(self) -> List[int]:
    """获取已过期的连接索引列表"""
    expired = []
    current_time = datetime.now()

    for i, conn_info in enumerate(self.connections):
        _, _, _, last_used = conn_info
        # 只检查空闲超时
        if (current_time - last_used).total_seconds() > self.timeout:
            expired.append(i)

    return expired
```

#### 问题影响

1. 长期连接可能因网络波动而失效
2. 数据库服务器端连接可能因超时而断开
3. 失效的连接会导致后续操作失败

#### 建议修复

```python
# 常量定义
CONNECTION_MAX_LIFETIME = 3600  # 连接最大存活时间（秒）

class ConnectionPool:
    def __init__(self, max_connections: int = 10, timeout: int = 30):
        # ...
        self._creation_times: Dict[Any, datetime] = {}

    def _add_connection(self, conn, cursor, params):
        """添加连接时记录创建时间"""
        self.connections.append([conn, cursor, params, datetime.now()])
        self._creation_times[id(conn)] = datetime.now()

    def _get_expired_connections(self) -> List[int]:
        """获取已过期的连接"""
        expired = []
        current_time = datetime.now()

        for i, conn_info in enumerate(self.connections):
            conn, cursor, params, last_used = conn_info

            # 检查空闲超时
            idle_timeout = (current_time - last_used).total_seconds()
            if idle_timeout > self.timeout:
                expired.append(i)
                continue

            # 检查总存活时间
            conn_id = id(conn)
            if conn_id in self._creation_times:
                lifetime = (current_time - self._creation_times[conn_id]).total_seconds()
                if lifetime > CONNECTION_MAX_LIFETIME:
                    self.logger.info(f"连接 #{i} 超过最大存活时间")
                    expired.append(i)

        return expired
```

---

### I-3: 密码在错误信息中暴露

**文件**: `src/data/repositories/database_repository.py:603-607`

#### 问题描述

在异常信息中直接包含参数，可能暴露密码：

```python
raise QueryExecutionException(
    message=f"查询执行失败: {str(e)}",
    sql=query,
    parameters=params  # 可能包含密码
)
```

#### 影响

1. 密码可能出现在日志文件中
2. 密码可能出现在错误报告或监控系统中

#### 建议修复

```python
def _sanitize_params(self, params: Optional[List[Any]]) -> Optional[List[Any]]:
    """脱敏参数用于日志和异常信息"""
    if not params:
        return None

    # 假设密码是第5个参数 (索引4)
    # 更安全的方式是使用参数名称
    sanitized = []
    for i, param in enumerate(params):
        if i == 4:  # 密码参数
            sanitized.append("***")
        elif isinstance(param, str) and len(param) > 8 and '@' not in param:
            # 可能是密码的其他字段
            sanitized.append("***")
        else:
            sanitized.append(param)

    return sanitized

def executeQuery(self, query: str, params: Optional[List[Any]] = None, timeout=None):
    try:
        # ... 执行查询
    except Exception as e:
        raise QueryExecutionException(
            message=f"查询执行失败: {str(e)}",
            sql=query,
            parameters=self._sanitize_params(params)  # 使用脱敏后的参数
        )
```

---

### I-4: 没有连接泄漏检测

**文件**: `src/data/repositories/database_repository.py`

#### 问题描述

当前没有机制检测连接泄漏（获取后未释放的连接）。

#### 建议修复

```python
class ConnectionPool:
    def __init__(self, max_connections: int = 10, timeout: int = 30):
        # ...
        self.active_connections: Dict[Any, Dict[str, Any]] = {}
        self.leak_check_threshold = 300  # 5秒

    def get_connection(self, params):
        conn = # ... 获取连接

        # 记录活跃连接
        self.active_connections[id(conn)] = {
            'thread_id': threading.get_ident(),
            'timestamp': time.time(),
            'params': str(params)[:100]  # 脱敏后的参数摘要
        }

        return conn

    def release_connection(self, conn):
        conn_id = id(conn)
        self.active_connections.pop(conn_id, None)
        # ... 释放逻辑

    def detect_leaks(self):
        """检测潜在泄漏的连接"""
        current_time = time.time()
        leaked = []

        for conn_id, info in self.active_connections.items():
            age = current_time - info['timestamp']
            if age > self.leak_check_threshold:
                leaked.append({
                    'connection_id': conn_id,
                    'thread_id': info['thread_id'],
                    'age_seconds': age,
                    'params': info['params']
                })

        if leaked:
            self.logger.warning(f"检测到 {len(leaked)} 个潜在泄漏的连接:")
            for leak in leaked:
                self.logger.warning(
                    f"  - 连接 #{leak['connection_id']}: "
                    f"线程 {leak['thread_id']}, "
                    f"已占用 {leak['age_seconds']:.1f}秒"
                )

        return leaked
```

---

### M-1: 方法命名不一致

**文件**: `src/data/repositories/database_repository.py`

#### 问题描述

混用 PascalCase 和 snake_case：

```python
def executeQuery(self, ...):      # PascalCase
def executeNonQuery(self, ...):   # PascalCase
def executeScalar(self, ...):     # PascalCase
def getConnectionParams(self):    # PascalCase
def getConnection(self, ...):     # PascalCase
def getConnection_params(self):   # snake_case ✅
def get_db_repository(self):      # snake_case ✅
```

#### 建议修复

根据 PEP 8，统一使用 snake_case：

```python
# 修正后
def execute_query(self, ...):
    pass

def execute_non_query(self, ...):
    pass

def execute_scalar(self, ...):
    pass

def get_connection_params(self):
    pass

def get_connection(self, ...):
    pass
```

---

### M-2: 大结果集日志输出

**文件**: `src/data/repositories/database_repository.py:595`

#### 问题描述

直接输出完整的查询结果，可能导致日志文件过大：

```python
self.logger.info(f"查询执行成功，返回{len(results)}条记录")
self.logger.debug(f"查询结果: {results}")  # 可能输出成千上万行
```

#### 建议修复

```python
self.logger.info(f"查询执行成功，返回{len(results)}条记录")
self.logger.debug(f"查询结果: 前10条 -> {results[:10]}")  # 只输出前10条
```

---

### M-3: 缺少数据库连接健康检查

**文件**: `src/business/services/data_service.py:240-251`

#### 问题描述

`get_connection_status` 只返回内存状态，没有实际测试连接：

```python
def get_connection_status(self) -> Dict[str, Any]:
    return {
        "status": self._connection_status,
        "last_error": self._last_error,
        "retry_count": self._retry_count
    }
```

#### 建议修复

```python
def get_connection_status(self, test_connection: bool = False) -> Dict[str, Any]:
    result = {
        "status": self._connection_status,
        "last_error": self._last_error,
        "retry_count": self._retry_count
    }

    if test_connection:
        try:
            test_result = self.db_repository.execute_query("SELECT 1")
            result["connection_test"] = "success" if test_result else "failed"
        except Exception as e:
            result["connection_test"] = "error"
            result["connection_test_error"] = str(e)

    return result
```

---

### M-4: 驱动检测循环调用

**文件**: `src/data/repositories/driver_factory.py:159-170`

#### 问题描述

在检测可用驱动时重复调用 `_try_load_*` 方法：

```python
def detect_available_driver(self, preferred: Optional[DatabaseDriverType] = None):
    # ...
    for driver_type in priority_list:
        if self._try_load_pyodbc():  # 每次循环都重新尝试
            return DatabaseDriverType.PYODBC
        elif self._try_load_iris():
            return DatabaseDriverType.IRIS
```

#### 问题影响

1. 多次尝试导入相同模块
2. 性能开销

#### 建议修复

```python
def detect_available_driver(self, preferred: Optional[DatabaseDriverType] = None):
    priority_list = self._get_driver_priority_from_config()

    # 如果指定了优先驱动，先尝试
    if preferred is not None and preferred in priority_list:
        if self._try_load_driver(preferred):
            return preferred

    # 按优先级检测
    for driver_type in priority_list:
        if self._driver_status.get(driver_type, False):
            # 已加载，直接返回
            return driver_type
        if self._try_load_driver(driver_type):
            return driver_type

    return DatabaseDriverType.UNKNOWN
```

---

### M-5: 查询历史未加密存储

**文件**: `src/business/services/query_history_manager.py`

#### 问题描述

查询历史以明文形式存储在 JSON 文件中：

```python
def _save_history(self):
    with open(self.history_file, 'w', encoding='utf-8') as f:
        json.dump(self.history, f, ensure_ascii=False, indent=2)
```

#### 影响

1. 敏感 SQL 查询暴露
2. 可能包含业务敏感信息

#### 建议修复

```python
import json
from cryptography.fernet import Fernet
from pathlib import Path

class EncryptedQueryHistoryManager:
    def __init__(self, history_file: Optional[Path] = None, encryption_key: Optional[bytes] = None):
        # ...
        if encryption_key is None:
            # 从文件加载或生成新密钥
            key_file = self.history_file.parent / '.history_key'
            if key_file.exists():
                with open(key_file, 'rb') as f:
                    self.cipher = Fernet(f.read())
            else:
                self.cipher = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(self.cipher)
        else:
            self.cipher = Fernet(encryption_key)

    def _save_history(self):
        data = json.dumps(self.history, ensure_ascii=False)
        encrypted = self.cipher.encrypt(data.encode())
        # ...
```

---

### L-1: 未使用上下文管理器

**文件**: `src/data/repositories/database_repository.py`

#### 当前代码

```python
try:
    # 执行操作
    result = cursor.execute(query)
finally:
    self.connection_pool.release_connection(conn)
```

#### 建议修复

```python
from contextlib import contextmanager

@contextmanager
def connection_context(self, connection_params):
    conn = self.connection_pool.get_connection(connection_params)
    if not conn:
        raise ConnectionException("无法获取连接")
    try:
        yield conn
    finally:
        self.connection_pool.release_connection(conn)

# 使用示例
with repository.connection_context(params) as (conn, cursor):
    cursor.execute(query, params)
```

---

### L-2: 缺少查询取消支持

**文件**: `src/data/repositories/database_repository.py`

#### 建议修复

```python
from threading import Event

class DatabaseRepository:
    def __init__(self):
        self._cancel_events: Dict[str, Event] = {}

    def execute_query(
        self,
        query: str,
        params: Optional[List[Any]] = None,
        query_id: Optional[str] = None,
        cancel_event: Optional[Event] = None
    ):
        if query_id:
            if query_id in self._cancel_events:
                raise QueryAlreadyRunningError(query_id)
            self._cancel_events[query_id] = Event()

        try:
            if cancel_event and cancel_event.is_set():
                raise QueryCancelledError()

            # 执行查询
            # ...

        finally:
            if query_id:
                self._cancel_events.pop(query_id, None)

    def cancel_query(self, query_id: str) -> bool:
        """取消指定查询"""
        if query_id in self._cancel_events:
            self._cancel_events[query_id].set()
            return True
        return False
```

---

### L-3: 没有查询性能监控

**文件**: `src/data/repositories/database_repository.py`

#### 建议修复

```python
class DatabaseRepository:
    def __init__(self):
        # ...
        self._query_metrics = {
            'total_queries': 0,
            'slow_queries': 0,
            'total_duration': 0.0
        }
        self.slow_query_threshold = 1.0  # 秒

    def execute_query(self, query: str, params=None, timeout=None):
        start_time = time.time()

        try:
            result = self._execute_impl(query, params)
            return result
        finally:
            duration = time.time() - start_time
            self._query_metrics['total_queries'] += 1
            self._query_metrics['total_duration'] += duration

            if duration > self.slow_query_threshold:
                self._query_metrics['slow_queries'] += 1
                self.logger.warning(
                    f"慢查询 ({duration:.3f}s): {query[:100]}"
                )

    def get_metrics(self) -> Dict[str, Any]:
        """获取查询指标"""
        total = self._query_metrics['total_queries']
        return {
            'total_queries': total,
            'slow_queries': self._query_metrics['slow_queries'],
            'avg_duration': self._query_metrics['total_duration'] / total if total > 0 else 0,
            'slow_query_rate': self._query_metrics['slow_queries'] / total if total > 0 else 0
        }
```

---

## 修复建议

### 修复优先级

| 优先级 | 问题ID | 修复工作量 | 风险降低 |
|--------|--------|------------|----------|
| 1 | C-1 | 2小时 | 高 |
| 2 | C-2 | 3小时 | 高 |
| 3 | I-1 | 1小时 | 中 |
| 4 | I-2 | 2小时 | 中 |
| 5 | I-3 | 1小时 | 中 |
| 6 | I-4 | 2小时 | 低 |
| 7 | M-1 | 4小时 | 无 (代码质量) |
| 8 | M-2 | 30分钟 | 无 (性能) |
| 9 | M-3 | 1小时 | 无 (可观测性) |
| 10 | M-4 | 1小时 | 无 (性能) |
| 11 | M-5 | 3小时 | 低 |
| 12 | L-1 | 2小时 | 无 (代码优雅性) |
| 13 | L-2 | 3小时 | 无 (功能完整性) |
| 14 | L-3 | 2小时 | 无 (可观测性) |

### 修复计划

#### 阶段 1: 安全修复 (本周)

1. **C-1 SQL 注入防护**: 强制参数化查询
2. **C-2 连接池等待机制**: 添加信号量控制

#### 阶段 2: 稳定性修复 (下周)

1. **I-1 异常处理**: 替换空 except 块
2. **I-2 连接存活时间**: 添加总存活时间限制
3. **I-3 密码脱敏**: 脱敏异常信息中的密码

#### 阶段 3: 质量改进 (下月)

1. **M-1 命名规范**: 统一代码风格
2. **M-2-M-5 其他中等问题**
3. **L-1-L-3 低优先级改进**

---

## 优先级矩阵

```
                    低影响                    高影响
              ┌────────────────────┬────────────────────┐
    高紧急   │                    │  C-1, C-2          │
              ├────────────────────┼────────────────────┤
    中紧急   │  M-2, M-4          │  I-1, I-2, I-3     │
              ├────────────────────┼────────────────────┤
    低紧急   │  L-1, L-2, L-3, M-1│  I-4, M-3, M-5     │
              └────────────────────┴────────────────────┘
```

---

## 附录

### A. 代码度量

| 指标 | 值 |
|------|-----|
| 总代码行数 | ~2000 |
| 函数数量 | ~50 |
| 类数量 | 8 |
| 注释覆盖率 | ~30% |
| 类型注解覆盖率 | ~40% |

### B. 测试覆盖

| 模块 | 单元测试 | 集成测试 |
|------|----------|----------|
| database_repository | 部分 | 部分 |
| driver_factory | 部分 | 无 |
| data_service | 部分 | 无 |
| query_history_manager | 无 | 无 |

### C. 相关资源

- [PEP 8 - Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/)
- [SQL Injection Prevention - OWASP](https://owasp.org/www-community/attacks/SQL_Injection)
- [Python threading documentation](https://docs.python.org/3/library/threading.html)
- [Connection Pool Best Practices](https://docs.sqlalchemy.org/en/14/core/pooling.html)

---

**报告生成时间**: 2026-02-12  
**报告版本**: 1.0
