# 项目架构文档 (更新版)

**版本**: 2.0  
**更新日期**: 2026-02-13  
**包含改进**: P0, P1, P2 所有架构优化

---

## 目录

1. [架构概述](#架构概述)
2. [分层架构](#分层架构)
3. [新增架构模式](#新增架构模式)
4. [依赖关系](#依赖关系)
5. [API文档](#api文档)

---

## 架构概述

本项目采用**分层架构**结合**现代架构模式**，包括：

- ✅ Repository模式 (P1)
- ✅ 缓存层 (P2)
- ✅ CQRS模式 (P2)
- ✅ 依赖注入容器

```
┌─────────────────────────────────────────────────────────────┐
│  Presentation Layer (UI)                                    │
│  - MainWindow, Pages, Dialogs                              │
│  - BasePage基类 (P0)                                        │
├─────────────────────────────────────────────────────────────┤
│  Business Layer                                             │
│  - DataService (Command/Query分离)                         │
│  - QueryHistoryManager                                      │
│  - CQRS Bus (P2)                                           │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                 │
│  - DatabaseRepository                                       │
│  - ConnectionPool (P0)                                     │
│  - Repositories (P1)                                        │
│    - QueryHistoryRepository                                 │
│    - TableMetadataRepository                                │
│  - Cache Layer (P2)                                        │
│    - CacheManager                                           │
│    - QueryCacheManager                                      │
├─────────────────────────────────────────────────────────────┤
│  Infrastructure Layer                                       │
│  - DI Container                                             │
│  - ConfigManager                                            │
│  - AppConfig (P1)                                          │
│  - CQRS Bus (P2)                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 分层架构

### 1. Presentation Layer (表示层)

**职责**: 用户界面展示和交互

**主要组件**:
- `MainWindow`: 主窗口
- `BasePage`: 页面基类 (P0改进)
- `Dialogs`: 各种对话框

**新特性** (P0):
```python
# BasePage 提供通用功能
class OverviewPage(BasePage):
    def _setup_ui(self):
        # 使用 self.scaled() 进行缩放
        # 使用 self._create_stat_card() 创建卡片
```

### 2. Business Layer (业务层)

**职责**: 业务逻辑处理

**主要组件**:
- `DataService`: 数据服务 (支持CQRS)
- `QueryHistoryManager`: 查询历史管理
- `CQRSBus`: 命令查询总线 (P2)

**CQRS使用** (P2):
```python
from src.infrastructure.cqrs import get_cqrs_bus
from src.infrastructure.cqrs.data_service_cqrs import (
    GetTableListQuery,
    UpdateDataCommand
)

bus = get_cqrs_bus()

# 查询操作
query = GetTableListQuery()
result = bus.execute_query(query)

# 命令操作
cmd = UpdateDataCommand("UPDATE users SET name = %s", ["Alice"])
result = bus.execute_command(cmd)
```

### 3. Data Layer (数据层)

**职责**: 数据访问和存储

**主要组件**:

#### 3.1 数据库仓库
- `DatabaseRepository`: 主仓库
- `ConnectionPool`: 连接池 (P0)

#### 3.2 Repository模式 (P1)
```python
from src.data.repositories import (
    QueryHistoryRepository,
    TableMetadataRepository
)

# 查询历史仓库
history_repo = QueryHistoryRepository(db_repository)
history = history_repo.find_by_id(1)
stats = history_repo.get_statistics()

# 表元数据仓库
meta_repo = TableMetadataRepository(db_repository)
tables = meta_repo.get_all_tables()
columns = meta_repo.get_table_columns('users')
```

#### 3.3 缓存层 (P2)
```python
from src.infrastructure.cache import get_query_cache

cache = get_query_cache()

# 缓存查询结果
result = db_repository.execute_query("SELECT * FROM users")
cache.set_query_result("SELECT * FROM users", result, ttl=300)

# 获取缓存
cached = cache.get_query_result("SELECT * FROM users")

# 查看统计
stats = cache.get_stats()
```

### 4. Infrastructure Layer (基础设施层)

**职责**: 基础设施支持

**主要组件**:
- `DIContainer`: 依赖注入容器
- `ConfigManager`: 配置管理
- `AppConfig`: 外部化配置 (P1)
- `CQRSBus`: CQRS总线 (P2)

---

## 新增架构模式

### P0 改进

#### 1. 文件拆分
- `connection_pool.py`: 连接池独立模块 (442行)
- `database_repository.py`: 精简至 684行

#### 2. Pages目录结构
```
presentation/pages/
├── __init__.py
├── base_page.py              # 页面基类
└── (预留: overview_page.py 等)
```

### P1 改进

#### 1. Repository模式

**基础架构**:
```python
class BaseRepository(ABC):
    def find_by_id(self, id) -> Optional[T]
    def find_all(self, limit, offset) -> List[T]
    def save(self, entity) -> bool
    def delete(self, id) -> bool
    def count(self) -> int
```

**具体实现**:
- `QueryHistoryRepository`: 查询历史管理
- `TableMetadataRepository`: 表元数据查询

#### 2. 外部化配置

**配置文件**: `config/app.yaml`

```yaml
ui:
  colors:
    primary: '#2563EB'
    success: '#10B981'
  fonts:
    family: 'Microsoft YaHei'

database:
  pool:
    max_connections: 10
    timeout: 30
```

**使用方式**:
```python
from src.infrastructure.config.app_config import get_app_config

config = get_app_config()
color = config.get_color('primary')
timeout = config.get('database.pool.timeout')
```

### P2 改进

#### 1. 缓存层

**特性**:
- TTL过期
- LRU淘汰
- 线程安全
- 统计信息

**使用示例**:
```python
from src.infrastructure.cache import get_query_cache

cache = get_query_cache(max_size=1000, default_ttl=300)

# 装饰器缓存
@cache.cached(ttl=60)
def get_expensive_data():
    return expensive_query()

# 手动缓存
cache.set('key', value, ttl=300)
value = cache.get('key')
```

#### 2. CQRS模式

**架构**:
```
Command -> CommandHandler -> Write Model (Database)
Query   -> QueryHandler   -> Read Model (Cache/DB)
```

**核心组件**:
- `Command`: 命令基类
- `Query`: 查询基类
- `CommandHandler`: 命令处理器
- `QueryHandler`: 查询处理器
- `CQRSBus`: 总线

---

## 依赖关系

### 依赖注入配置

```python
# service_registration.py
container.register_singleton(IQueryRepository, DatabaseRepository)
container.register_singleton(IDataService, DataService)
```

### 模块依赖图

```
presentation
    ↓ depends on
business
    ↓ depends on
data
    ↓ depends on
infrastructure
```

---

## API文档

### CacheManager API

```python
class CacheManager:
    def get(key: str, default: Any = None) -> Any
    def set(key: str, value: Any, ttl: Optional[int] = None) -> bool
    def delete(key: str) -> bool
    def clear() -> None
    def get_stats() -> Dict[str, Any]
    def cached(ttl: int) -> Callable
```

### Repository API

```python
class BaseRepository:
    def find_by_id(self, entity_id: Any) -> Optional[T]
    def find_all(self, limit: int, offset: int) -> List[T]
    def save(self, entity: T) -> bool
    def delete(self, entity_id: Any) -> bool
    def count(self) -> int
```

### CQRS API

```python
class CQRSBus:
    def register_command_handler(command_type, handler)
    def register_query_handler(query_type, handler)
    def execute_command(command: Command) -> CommandResult
    def execute_query(query: Query[T]) -> QueryResult[T]
```

---

## 文件统计

| 改进阶段 | 新增文件 | 新增行数 | 状态 |
|---------|---------|---------|------|
| P0 | 3 | 570 | ✅ |
| P1 | 6 | 1298 | ✅ |
| P2 | 6 | 1301 | ✅ |
| **总计** | **15** | **3169** | ✅ |

---

## 测试覆盖

### 测试统计

| 测试文件 | 测试数 | 状态 |
|---------|--------|------|
| test_repositories.py | 20 | ✅ |
| test_cache_manager.py | 18 | ✅ |
| **总计** | **38** | ✅ |

---

## 使用建议

### 查询场景

使用 **Repository + 缓存**:
```python
# 1. 尝试从缓存获取
cached = cache.get_query_result(query, params)
if cached:
    return cached

# 2. 从数据库查询
result = repository.find_all()

# 3. 存入缓存
cache.set_query_result(query, result)

return result
```

### 命令场景

使用 **CQRS Command**:
```python
# 创建命令
cmd = UpdateDataCommand(sql, params)

# 执行命令
result = bus.execute_command(cmd)

# 清除相关缓存
if result.success:
    cache.invalidate_table(table_name)
```

---

## 后续建议

### 可继续改进

1. **事件溯源**: 添加 Event Sourcing 支持
2. **读写分离**: 主从数据库配置
3. **分布式缓存**: Redis/Memcached 支持
4. **API文档**: Swagger/OpenAPI 集成

---

**文档版本**: 2.0  
**最后更新**: 2026-02-13
