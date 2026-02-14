# 架构改进执行计划

**项目名称**: PyWindows 桌面应用程序架构改进  
**计划创建时间**: 2026-02-14  
**预计完成时间**: 3个月  
**总工时估算**: 80-100 人时  

---

## 计划概述

本计划基于架构审核报告中发现的问题，制定分阶段、可执行的改进任务。所有任务按优先级（P0/P1/P2）分类，并标注依赖关系。

---

## 第一阶段：基础模型层建设（P0）

### 任务 1.1: 创建领域模型层

**优先级**: P0  
**估计工时**: 8-10 小时  
**依赖**: 无  
**负责人**: 待定  

#### 任务描述
在 `src/business/models/` 目录下创建领域模型，使用 dataclass 定义核心业务对象。

#### 验收标准
- [ ] 创建 `src/business/models/domain_models.py`
- [ ] 实现以下模型类：
  - `DatabaseConnection` - 数据库连接领域模型
  - `QueryResult` - 查询结果领域模型
  - `QueryHistory` - 查询历史领域模型
  - `TableMetadata` - 表元数据领域模型
  - `ColumnMetadata` - 列元数据领域模型
- [ ] 所有模型包含类型注解
- [ ] 所有模型包含 docstring 文档
- [ ] 单元测试覆盖率 > 80%

#### 代码示例
```python
# src/business/models/domain_models.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class DatabaseType(Enum):
    """数据库类型枚举"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    IRIS = "iris"
    CACHE = "cache"

class QueryStatus(Enum):
    """查询状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class DatabaseConnection:
    """数据库连接领域模型"""
    id: str
    name: str
    host: str
    port: int
    database: str
    username: str
    database_type: DatabaseType
    schema: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    last_connected_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        ...
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatabaseConnection':
        """从字典创建实例"""
        ...

@dataclass
class QueryResult:
    """查询结果领域模型"""
    query_id: str
    sql: str
    rows: List[Dict[str, Any]]
    execution_time_ms: float
    row_count: int
    column_names: List[str]
    executed_at: datetime = field(default_factory=datetime.now)
    connection_id: Optional[str] = None
    
    def is_empty(self) -> bool:
        """检查结果是否为空"""
        return self.row_count == 0

@dataclass
class QueryHistory:
    """查询历史领域模型"""
    id: str
    sql: str
    connection_id: str
    executed_at: datetime
    execution_time_ms: float
    row_count: int
    status: QueryStatus
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
```

#### 验证命令
```bash
python -m pytest tests/unit/test_domain_models.py -v
python -m unittest tests.unit.test_domain_models -v
```

---

### 任务 1.2: 创建数据实体层

**优先级**: P0  
**估计工时**: 6-8 小时  
**依赖**: 任务 1.1  
**负责人**: 待定  

#### 任务描述
在 `src/data/entities/` 目录下创建数据实体，用于数据库持久化。

#### 验收标准
- [ ] 创建 `src/data/entities/` 目录结构
- [ ] 实现以下实体类：
  - `DatabaseConnectionEntity` - 连接配置实体
  - `QueryHistoryEntity` - 查询历史实体
  - `TableMetadataEntity` - 表元数据实体
- [ ] 实现实体与领域模型的转换方法（`to_domain()`、`from_domain()`）
- [ ] 单元测试覆盖率 > 80%

#### 代码示例
```python
# src/data/entities/database_connection_entity.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

from src.business.models.domain_models import DatabaseConnection, DatabaseType

@dataclass
class DatabaseConnectionEntity:
    """数据库连接数据实体"""
    id: str
    name: str
    host: str
    port: int
    database: str
    username: str
    encrypted_password: str
    database_type: str
    schema: Optional[str] = None
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: Optional[str] = None
    
    def to_domain(self) -> DatabaseConnection:
        """转换为领域模型"""
        return DatabaseConnection(
            id=self.id,
            name=self.name,
            host=self.host,
            port=self.port,
            database=self.database,
            username=self.username,
            database_type=DatabaseType(self.database_type),
            schema=self.schema,
            is_active=self.is_active,
            created_at=datetime.fromisoformat(self.created_at),
            updated_at=datetime.fromisoformat(self.updated_at) if self.updated_at else None
        )
    
    @classmethod
    def from_domain(cls, domain: DatabaseConnection, encrypted_password: str) -> 'DatabaseConnectionEntity':
        """从领域模型创建实体"""
        return cls(
            id=domain.id,
            name=domain.name,
            host=domain.host,
            port=domain.port,
            database=domain.database,
            username=domain.username,
            encrypted_password=encrypted_password,
            database_type=domain.database_type.value,
            schema=domain.schema,
            is_active=domain.is_active,
            created_at=domain.created_at.isoformat(),
            updated_at=domain.updated_at.isoformat() if domain.updated_at else None
        )
```

---

## 第二阶段：服务拆分（P1）

### 任务 2.1: 提取验证服务

**优先级**: P1  
**估计工时**: 6-8 小时  
**依赖**: 无  
**负责人**: 待定  

#### 任务描述
将 `InputValidator` 从 `data_service.py` 中提取到独立的验证服务模块。

#### 验收标准
- [ ] 创建 `src/business/validators/` 目录
- [ ] 创建 `src/business/validators/__init__.py`
- [ ] 创建 `src/business/validators/query_validator.py`
- [ ] 创建 `src/business/validators/schema_validator.py`
- [ ] 创建 `src/business/validators/input_validator.py`（兼容层）
- [ ] 所有验证器包含完整的类型注解
- [ ] 单元测试覆盖率 > 90%
- [ ] 原有代码仍能正常工作（向后兼容）

#### 代码示例
```python
# src/business/validators/query_validator.py
import re
from dataclasses import dataclass
from typing import Optional, Tuple, List

@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    message: str
    sanitized_value: str = ""

class QueryValidator:
    """查询验证器"""
    
    # 危险关键字列表
    DANGEROUS_KEYWORDS = [
        ("DROP", "DROP"),
        ("DELETE FROM", "DELETE"),
        ("TRUNCATE", "TRUNCATE"),
        ("ALTER", "ALTER"),
    ]
    
    @staticmethod
    def validate_query(query: str, params: Optional[Tuple] = None) -> ValidationResult:
        """验证查询安全性"""
        if not query:
            return ValidationResult(False, "查询不能为空")
        
        query_upper = query.upper().strip()
        
        # 检查危险关键字
        for keyword, description in QueryValidator.DANGEROUS_KEYWORDS:
            if keyword in query_upper:
                return ValidationResult(False, f"包含危险关键字: {description}")
        
        return ValidationResult(True, "验证通过", query)
    
    @staticmethod
    def validate_parameters(params: Tuple) -> ValidationResult:
        """验证查询参数"""
        if not params:
            return ValidationResult(True, "无参数")
        
        allowed_types = (str, int, float, bool, type(None))
        
        for param in params:
            if not isinstance(param, allowed_types):
                return ValidationResult(False, f"不支持的参数类型: {type(param)}")
        
        return ValidationResult(True, "参数验证通过")
```

#### 验证命令
```bash
python -m pytest tests/unit/test_validators/ -v
flake8 src/business/validators/ --count --select=E9,F63,F7,F82
```

---

### 任务 2.2: 创建连接管理服务

**优先级**: P1  
**估计工时**: 10-12 小时  
**依赖**: 任务 1.1  
**负责人**: 待定  

#### 任务描述
从 DataService 中提取连接管理逻辑，创建独立的 ConnectionService。

#### 验收标准
- [ ] 创建 `src/business/services/connection_service.py`
- [ ] 实现 `ConnectionService` 类
- [ ] 支持连接池管理
- [ ] 支持连接状态监控
- [ ] 支持多数据库类型
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试通过

#### 代码示例
```python
# src/business/services/connection_service.py
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from src.business.models.domain_models import DatabaseConnection, DatabaseType
from src.data.repositories.database_repository import DatabaseRepository

logger = logging.getLogger(__name__)

class ConnectionService:
    """连接管理服务"""
    
    def __init__(self, db_repository: DatabaseRepository):
        self.db_repository = db_repository
        self._active_connections: Dict[str, DatabaseConnection] = {}
    
    def connect(self, connection: DatabaseConnection) -> bool:
        """建立数据库连接"""
        try:
            # 连接逻辑
            self._active_connections[connection.id] = connection
            connection.last_connected_at = datetime.now()
            logger.info(f"连接成功: {connection.name}")
            return True
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False
    
    def disconnect(self, connection_id: str) -> bool:
        """断开连接"""
        if connection_id in self._active_connections:
            del self._active_connections[connection_id]
            return True
        return False
    
    def get_active_connections(self) -> List[DatabaseConnection]:
        """获取所有活动连接"""
        return list(self._active_connections.values())
    
    def test_connection(self, connection: DatabaseConnection) -> bool:
        """测试连接"""
        # 测试逻辑
        pass
```

---

### 任务 2.3: 创建查询执行服务

**优先级**: P1  
**估计工时**: 8-10 小时  
**依赖**: 任务 2.1, 任务 2.2  
**负责人**: 待定  

#### 任务描述
从 DataService 中提取查询执行逻辑，创建独立的 QueryExecutionService。

#### 验收标准
- [ ] 创建 `src/business/services/query_execution_service.py`
- [ ] 实现 `QueryExecutionService` 类
- [ ] 集成 QueryValidator 进行验证
- [ ] 支持查询取消
- [ ] 支持执行超时
- [ ] 返回 QueryResult 领域模型
- [ ] 单元测试覆盖率 > 80%

#### 代码示例
```python
# src/business/services/query_execution_service.py
import logging
import time
from typing import Optional, List, Dict, Any
from datetime import datetime

from src.business.models.domain_models import QueryResult, QueryStatus
from src.business.validators.query_validator import QueryValidator, ValidationResult
from src.data.repositories.database_repository import DatabaseRepository

logger = logging.getLogger(__name__)

class QueryExecutionService:
    """查询执行服务"""
    
    def __init__(
        self,
        db_repository: DatabaseRepository,
        query_validator: QueryValidator
    ):
        self.db_repository = db_repository
        self.query_validator = query_validator
    
    def execute_query(
        self,
        sql: str,
        params: Optional[Tuple] = None,
        timeout: Optional[int] = 30
    ) -> QueryResult:
        """执行查询"""
        query_id = generate_query_id()
        start_time = time.time()
        
        try:
            # 验证查询
            validation = self.query_validator.validate_query(sql, params)
            if not validation.is_valid:
                raise ValueError(validation.message)
            
            # 执行查询
            rows = self.db_repository.execute_query(sql, params)
            
            execution_time = (time.time() - start_time) * 1000
            
            return QueryResult(
                query_id=query_id,
                sql=sql,
                rows=rows or [],
                execution_time_ms=execution_time,
                row_count=len(rows) if rows else 0,
                column_names=list(rows[0].keys()) if rows else [],
                executed_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            raise
```

---

### 任务 2.4: 重构 DataService 为 Facade

**优先级**: P1  
**估计工时**: 6-8 小时  
**依赖**: 任务 2.1, 任务 2.2, 任务 2.3  
**负责人**: 待定  

#### 任务描述
将 DataService 重构为 Facade 模式，组合各个子服务。

#### 验收标准
- [ ] 重构 `src/business/services/data_service.py`
- [ ] DataService 作为 Facade，委托给子服务
- [ ] 保持向后兼容（原有接口不变）
- [ ] 代码行数 < 200 行
- [ ] 所有原有测试通过
- [ ] 标记原有方法为 deprecated（如有必要）

#### 代码示例
```python
# src/business/services/data_service.py (重构后)
import logging
from typing import Optional, List, Dict, Any

from src.business.services.connection_service import ConnectionService
from src.business.services.query_execution_service import QueryExecutionService
from src.business.validators.query_validator import QueryValidator
from src.data.repositories.database_repository import DatabaseRepository

logger = logging.getLogger(__name__)

class DataService:
    """数据服务 Facade
    
    提供统一的数据访问接口，内部委托给各个子服务。
    
    注意: 此类正在重构中，建议直接使用子服务：
    - ConnectionService: 连接管理
    - QueryExecutionService: 查询执行
    - QueryValidator: 查询验证
    """
    
    def __init__(
        self,
        connection_service: Optional[ConnectionService] = None,
        query_execution_service: Optional[QueryExecutionService] = None
    ):
        self._connection_service = connection_service or self._create_connection_service()
        self._query_execution_service = query_execution_service or self._create_query_execution_service()
    
    def _create_connection_service(self) -> ConnectionService:
        """创建连接服务（内部使用）"""
        db_repository = get_db_repository()
        return ConnectionService(db_repository)
    
    def _create_query_execution_service(self) -> QueryExecutionService:
        """创建查询执行服务（内部使用）"""
        db_repository = get_db_repository()
        query_validator = QueryValidator()
        return QueryExecutionService(db_repository, query_validator)
    
    # 委托方法
    def test_connection(self) -> bool:
        """测试连接（委托给 ConnectionService）"""
        return self._connection_service.test_connection(...)
    
    def get_data(self, query: str, params: Optional[List[Any]] = None):
        """获取数据（委托给 QueryExecutionService）"""
        result = self._query_execution_service.execute_query(query, tuple(params) if params else None)
        return result.rows
    
    # 保持其他原有方法...
```

---

## 第三阶段：领域事件系统（P1）

### 任务 3.1: 定义领域事件

**优先级**: P1  
**估计工时**: 4-6 小时  
**依赖**: 任务 1.1  
**负责人**: 待定  

#### 任务描述
创建领域事件类，用于模型间的通信和解耦。

#### 验收标准
- [ ] 创建 `src/business/events/` 目录
- [ ] 创建 `src/business/events/domain_events.py`
- [ ] 定义以下事件：
  - `DomainEvent` - 领域事件基类
  - `QueryExecutedEvent` - 查询执行事件
  - `ConnectionEstablishedEvent` - 连接建立事件
  - `ConnectionClosedEvent` - 连接关闭事件
  - `DataDownloadedEvent` - 数据下载事件
- [ ] 所有事件包含时间戳和事件ID
- [ ] 单元测试覆盖率 > 90%

#### 代码示例
```python
# src/business/events/domain_events.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

@dataclass
class DomainEvent:
    """领域事件基类"""
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.__class__.__name__
        }

@dataclass
class QueryExecutedEvent(DomainEvent):
    """查询执行事件"""
    query_id: str
    sql: str
    connection_id: str
    execution_time_ms: float
    row_count: int
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'query_id': self.query_id,
            'sql': self.sql,
            'connection_id': self.connection_id,
            'execution_time_ms': self.execution_time_ms,
            'row_count': self.row_count,
            'success': self.success,
            'error_message': self.error_message
        })
        return base

@dataclass
class ConnectionEstablishedEvent(DomainEvent):
    """连接建立事件"""
    connection_id: str
    connection_name: str
    database_type: str
    host: str
    
    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'connection_id': self.connection_id,
            'connection_name': self.connection_name,
            'database_type': self.database_type,
            'host': self.host
        })
        return base
```

---

### 任务 3.2: 集成事件发布到服务

**优先级**: P1  
**估计工时**: 8-10 小时  
**依赖**: 任务 3.1, 任务 2.3  
**负责人**: 待定  

#### 任务描述
在 QueryExecutionService 和 ConnectionService 中集成事件发布。

#### 验收标准
- [ ] 修改 `QueryExecutionService`，在执行完成后发布 `QueryExecutedEvent`
- [ ] 修改 `ConnectionService`，在连接建立/关闭时发布相应事件
- [ ] 使用现有的 `EventBus` 进行事件发布
- [ ] 添加事件发布开关（可配置）
- [ ] 确保事件发布不阻塞主流程
- [ ] 集成测试通过

#### 代码示例
```python
# 修改 QueryExecutionService
from src.business.events.domain_events import QueryExecutedEvent
from src.infrastructure.events.event_bus import get_event_bus

class QueryExecutionService:
    def __init__(self, ..., publish_events: bool = True):
        ...
        self._publish_events = publish_events
        self._event_bus = get_event_bus() if publish_events else None
    
    def execute_query(self, sql: str, ...):
        try:
            ...
            result = QueryResult(...)
            
            # 发布事件
            if self._publish_events and self._event_bus:
                event = QueryExecutedEvent(
                    query_id=result.query_id,
                    sql=sql,
                    connection_id=connection_id,
                    execution_time_ms=result.execution_time_ms,
                    row_count=result.row_count,
                    success=True
                )
                # 异步发布，不阻塞
                self._event_bus.publish_async(event)
            
            return result
            
        except Exception as e:
            # 发布失败事件
            if self._publish_events and self._event_bus:
                event = QueryExecutedEvent(
                    query_id=query_id,
                    sql=sql,
                    connection_id=connection_id,
                    execution_time_ms=0,
                    row_count=0,
                    success=False,
                    error_message=str(e)
                )
                self._event_bus.publish_async(event)
            raise
```

---

## 第四阶段：依赖方向优化（P2）

### 任务 4.1: 完善依赖注入配置

**优先级**: P2  
**估计工时**: 6-8 小时  
**依赖**: 任务 2.1, 任务 2.2, 任务 2.3  
**负责人**: 待定  

#### 任务描述
完善 DI 容器配置，确保业务层通过接口依赖数据层。

#### 验收标准
- [ ] 创建 `src/infrastructure/di/service_registration.py`（如不存在）
- [ ] 注册所有新服务到 DI 容器
- [ ] 确保业务层只依赖接口，不依赖具体实现
- [ ] 添加生命周期配置
- [ ] 验证循环依赖检测正常工作
- [ ] 所有服务可通过 DI 容器解析

#### 代码示例
```python
# src/infrastructure/di/service_registration.py
from src.infrastructure.di.container import get_container, ServiceLifetime

from src.data.repositories.database_repository import DatabaseRepository
from src.business.services.connection_service import ConnectionService
from src.business.services.query_execution_service import QueryExecutionService
from src.business.validators.query_validator import QueryValidator

def register_services():
    """注册所有服务到 DI 容器"""
    container = get_container()
    
    # 数据层 - 单例
    container.register_singleton(
        DatabaseRepository,
        DatabaseRepository
    )
    
    # 验证器 - 瞬态
    container.register_transient(
        QueryValidator,
        QueryValidator
    )
    
    # 服务层 - 单例
    container.register_singleton(
        ConnectionService,
        ConnectionService
    )
    
    container.register_singleton(
        QueryExecutionService,
        QueryExecutionService
    )

# 在应用启动时调用
# register_services()
```

---

## 依赖关系图

```
任务 1.1 (领域模型)
    ↓
任务 1.2 (数据实体)
    ↓
任务 2.1 (验证服务) ─────┐
    ↓                    │
任务 2.2 (连接服务) ─────┼──→ 任务 2.4 (DataService Facade)
    ↓                    │
任务 2.3 (查询服务) ─────┘
    ↓
任务 3.1 (领域事件) ─────→ 任务 3.2 (事件集成)
    ↓
任务 4.1 (DI 配置)
```

---

## 时间表

| 阶段 | 任务 | 工时 | 开始周 | 结束周 |
|------|------|------|--------|--------|
| **第一阶段** | 任务 1.1 | 8-10h | 第1周 | 第1周 |
| | 任务 1.2 | 6-8h | 第1周 | 第2周 |
| **第二阶段** | 任务 2.1 | 6-8h | 第2周 | 第2周 |
| | 任务 2.2 | 10-12h | 第2周 | 第3周 |
| | 任务 2.3 | 8-10h | 第3周 | 第3周 |
| | 任务 2.4 | 6-8h | 第3周 | 第4周 |
| **第三阶段** | 任务 3.1 | 4-6h | 第4周 | 第4周 |
| | 任务 3.2 | 8-10h | 第4周 | 第5周 |
| **第四阶段** | 任务 4.1 | 6-8h | 第5周 | 第6周 |

**总计**: 62-80 小时（约 6 周，按每周 12-15 小时计算）

---

## 验收清单

### 整体验收标准

- [ ] 所有 P0 任务完成
- [ ] 所有 P1 任务完成
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试全部通过
- [ ] 原有功能不受影响
- [ ] 代码风格检查通过（flake8）
- [ ] 类型检查通过（mypy，如使用）

### 代码质量检查

```bash
# 运行所有检查
python -m pytest tests/unit -v --cov=src --cov-report=html
flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics
python -m unittest discover tests/integration -v
```

---

## 风险与缓解

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 重构引入 Bug | 中 | 高 | 保持向后兼容，充分测试 |
| 工期延误 | 中 | 中 | 分阶段交付，优先完成 P0 |
| 团队不熟悉 DDD | 低 | 中 | 提供代码示例，代码审查 |
| 性能回归 | 低 | 高 | 性能测试，基准对比 |

---

## 附录

### 参考文档

- [架构审核报告](./notepads/architecture-audit/audit-report.md)
- [项目 AGENTS.md](./AGENTS.md)

### 代码规范

- 使用 dataclass 定义模型
- 类型注解必须完整
- docstring 使用三重双引号
- 遵循 PEP 8 规范
- 单元测试使用 pytest

---

**计划版本**: 1.0  
**最后更新**: 2026-02-14  
**审核周期**: 每两周回顾进度
