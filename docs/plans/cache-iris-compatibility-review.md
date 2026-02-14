# SQL 智能补全计划 - Intersystems Cache/IRIS 兼容性审核报告

**审核日期**: 2025-02-13  
**审核范围**: SQL 智能补全功能对 Intersystems Cache 和 IRIS 数据库的兼容性  
**审核结果**: ⚠️ **部分兼容，需要调整**

---

## 1. 兼容性概览

| 组件 | Cache 兼容性 | IRIS 兼容性 | 备注 |
|------|-------------|-------------|------|
| 元数据获取 (表/列) | ⚠️ 需要调整 | ✅ 兼容 | Cache 需使用 %Dictionary 类 |
| SQL 关键字补全 | ⚠️ 部分 | ⚠️ 部分 | 缺少 Cache/IRIS 特有函数 |
| 表名补全 | ✅ 兼容 | ✅ 兼容 | INFORMATION_SCHEMA 支持 |
| 列名补全 | ✅ 兼容 | ✅ 兼容 | INFORMATION_SCHEMA 支持 |
| 特殊语法补全 | ❌ 不支持 | ❌ 不支持 | 箭头操作符、%函数等 |

---

## 2. 详细分析

### 2.1 元数据获取问题

**当前实现** (TableMetadataRepository):
```python
# 获取所有表
query = "SELECT name FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"

# 获取列信息
query = """
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = %s
"""
```

**问题分析**:

1. **IRIS**: ✅ `INFORMATION_SCHEMA` 完全支持
2. **Cache 2015.2+**: ✅ `INFORMATION_SCHEMA` 支持，但可能需要特殊权限
3. **Cache 旧版本**: ❌ 需要使用 `%Dictionary` 类

**推荐改进**:
```python
def get_all_tables(self) -> List[str]:
    """获取所有表名（兼容 Cache/IRIS）"""
    try:
        # 首先尝试 INFORMATION_SCHEMA（IRIS 和 Cache 2015.2+）
        query = """
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            AND TABLE_SCHEMA NOT LIKE '%%SYS'
        """
        result = self.execute_query(query)
        return [row.get('TABLE_NAME', row.get('name', '')) for row in result]
    except Exception:
        # 回退到 %Dictionary（旧版 Cache）
        query = """
            SELECT Name 
            FROM %Dictionary.ClassDefinition 
            WHERE SqlTableName IS NOT NULL
        """
        result = self.execute_query(query)
        return [row.get('Name', '') for row in result]
```

---

### 2.2 SQL 关键字缺失

**当前关键字列表** (`sql_keywords.json`):
- 通用 SQL 关键字（SELECT, FROM, WHERE 等）
- 通用函数（COUNT, SUM, AVG 等）

**Cache/IRIS 特有内容缺失**:

#### 需要添加的关键字/函数:

```json
{
  "IRIS_CACHE_FUNCTIONS": [
    "%ABS",
    "%ALPHAUP", 
    "%CONTAINS",
    "%INLIST",
    "%MATCH",
    "%MVR",
    "%ODBCIN",
    "%ODBCOUT",
    "%PATTERN",
    "%PI",
    "%SQLSTRING",
    "%SQLUPPER",
    "%STARTSWITH",
    "%STRING",
    "%TRUNCATE",
    "%UPPER"
  ],
  "IRIS_CACHE_TYPES": [
    "%Array",
    "%Binary",
    "%Boolean", 
    "%Date",
    "%DateTime",
    "%Decimal",
    "%Double",
    "%Integer",
    "%List",
    "%ListOfDataTypes",
    "%Numeric",
    "%SmallInt",
    "%Status",
    "%String",
    "%Time",
    "%TimeStamp",
    "%TinyInt",
    "%VarString"
  ],
  "IRIS_CACHE_OPERATORS": [
    "->"
  ]
}
```

#### 箭头操作符 (`->`) 支持:

Cache/IRIS 特有的嵌入式对象访问语法：
```sql
-- 当前不支持补全
SELECT Person->Name, Person->Address->City FROM Orders
--              ↑ 这里需要补全 Person 类的属性
```

**实现建议**:
需要在 `SQLCompleter` 中添加对 `->` 操作符的识别和补全支持。

---

### 2.3 数据类型映射问题

**当前问题**:
- 元数据缓存存储的是 Cache/IRIS 的 `%` 类型（如 `%String`）
- 但显示时可能不够友好

**建议**:
```python
# 在 metadata_cache_service.py 中添加类型映射
CACHE_IRIS_TYPE_MAP = {
    '%String': 'VARCHAR',
    '%Integer': 'INT',
    '%Date': 'DATE',
    '%DateTime': 'TIMESTAMP',
    '%Boolean': 'BOOLEAN',
    '%Numeric': 'NUMERIC',
    '%Binary': 'BLOB',
    # ... 更多映射
}

def get_display_type(self, cache_type: str) -> str:
    """获取显示用的数据类型"""
    return CACHE_IRIS_TYPE_MAP.get(cache_type, cache_type)
```

---

## 3. 改进建议清单

### 高优先级（必须）:

- [ ] **1. 更新 `TableMetadataRepository`**
  - 添加 Cache 旧版本回退机制（使用 `%Dictionary`）
  - 添加 Schema 过滤（排除系统表）

- [ ] **2. 扩展 SQL 关键字列表**
  - 添加 Cache/IRIS 特有的 `%` 函数
  - 添加 Cache/IRIS 特有的数据类型
  - 添加箭头操作符 `->`

### 中优先级（推荐）:

- [ ] **3. 支持箭头操作符补全**
  - 识别 `table->` 语法
  - 提供类属性补全

- [ ] **4. 类型显示优化**
  - 将 `%String` 等显示为 `VARCHAR` 等通用类型
  - 保留原始类型信息

### 低优先级（可选）:

- [ ] **5. 支持 `##class()` 语法**
  - 识别 `##class(Package.Class).Method()` 语法
  - 提供类和方法补全

- [ ] **6. 支持系统类和表**
  - 识别 `%` 开头的系统类
  - 提供系统函数补全

---

## 4. 实施方案

### 方案 A: 最小改动（推荐）

**改动范围**: 仅修改 `sql_keywords.json` 和 `TableMetadataRepository`

**步骤**:
1. 在 `sql_keywords.json` 中添加 `"IRIS_CACHE_SPECIFIC"` 类别
2. 修改 `TableMetadataRepository.get_all_tables()` 添加异常处理
3. 修改 `TableMetadataRepository.get_table_columns()` 添加异常处理

**工作量**: 1-2 小时  
**兼容性**: Cache 2015.2+ 和 IRIS 完全兼容，旧版 Cache 基本兼容

### 方案 B: 完整支持

**改动范围**: 所有组件 + 新增 Cache/IRIS 专用模块

**步骤**:
1. 创建 `cache_iris_repository.py` 专用仓库
2. 实现 `%Dictionary` 查询支持
3. 实现箭头操作符补全
4. 实现 `##class()` 语法支持

**工作量**: 8-12 小时  
**兼容性**: 所有版本 Cache/IRIS 完全兼容

---

## 5. 测试建议

### 必须测试的场景:

1. **IRIS 数据库**
   - 表列表获取
   - 列信息获取
   - SQL 关键字补全

2. **Cache 2015.2+**
   - INFORMATION_SCHEMA 查询
   - 表/列元数据获取

3. **Cache 旧版本**（如果有）
   - %Dictionary 回退机制
   - 基本元数据获取

### 测试 SQL:

```sql
-- 测试表列表
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'

-- 测试列信息
SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Sample.Person'

-- 测试特殊函数
SELECT %SQLUPPER(Name), %EXTERNAL(DOB) FROM Sample.Person

-- 测试箭头操作符
SELECT Company->Name, Company->Address->City FROM Sample.Employee
```

---

## 6. 结论

### 当前状态
SQL 智能补全功能 **基本可用** 于 IRIS 和 Cache 2015.2+，但存在以下限制：
- 缺少 Cache/IRIS 特有的函数和类型
- 不支持箭头操作符补全
- 旧版 Cache 可能无法获取元数据

### 建议
对于 **Intersystems 数据库用户**，建议实施 **方案 A（最小改动）**，可以显著提升用户体验。

如果用户主要使用 **旧版 Cache**（2015.2 之前），建议实施 **方案 B**。

---

**审核人**: Atlas (Orchestrator)  
**日期**: 2025-02-13
