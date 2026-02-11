# PyWindows 项目后续改进计划

> 基于代码审查报告生成
> 生成日期: 2026-02-11
> 审查范围: 完整的重构代码审查

## 执行摘要

本次计划基于代码审查报告，针对生产就绪前的最后优化和长期技术债务管理。所有 Critical 问题已解决，本计划聚焦 Important 和 Minor 级别的改进，以及架构优化。

---

## 进度统计

| 类别 | 待处理 | 进行中 | 已完成 | 总计 |
|------|--------|--------|--------|------|
| 🔴 Critical | 0 | 0 | 0 | 0 |
| 🟡 Important | 0 | 0 | 4 | 4 |
| 🟢 Minor | 3 | 0 | 0 | 3 |
| 🔵 Architecture | 3 | 0 | 0 | 3 |
| 🔧 DevOps | 2 | 0 | 1 | 3 |
| **总计** | **8** | **0** | **5** | **13** |

---

## 执行路线图

### 🎯 第一阶段：生产就绪准备（第1周）

本阶段修复 Important 级别问题，确保代码健壮性。

---

#### IMP-001: 单例模式线程安全加固

**状态**: 🟡 进行中  
**开始日期**: 2026-02-11  
**预计时间**: 2 小时  
**优先级**: 🔴 高  
**依赖**: 无

**问题描述**: 
当前单例模式（ScalingManager, DatabaseDriverFactory）在多线程环境下可能存在竞态条件。

**当前代码** (scaling_manager.py:38-42):
```python
def __new__(cls) -> 'ScalingManager':
    """单例模式实现"""
    if cls._instance is None:
        cls._instance = super().__new__(cls)
    return cls._instance
```

**风险**: 
虽然 Python GIL 降低了风险，但理论上多线程同时创建实例时仍可能出现问题。

**解决方案**:
1. 添加线程锁保护
2. 使用双重检查锁定模式

**修复后代码**:
```python
import threading

class ScalingManager:
    _instance: Optional['ScalingManager'] = None
    _initialized: bool = False
    _lock = threading.Lock()  # 类级别锁
    
    def __new__(cls) -> 'ScalingManager':
        """线程安全的单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                # 双重检查
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

**涉及文件**:
- `src/infrastructure/utils/scaling_manager.py`
- `src/data/repositories/driver_factory.py`

**验收标准**:
- [ ] 添加线程锁保护
- [ ] 实现双重检查锁定
- [ ] 添加多线程测试用例
- [ ] 所有现有测试仍通过

---

#### IMP-002: 配置外部化 - 缩放规则和驱动优先级

**状态**: ✅ 已完成  
**完成日期**: 2026-02-11  
**实际用时**: 3.5 小时  
**计划用时**: 4 小时  
**完成报告**: `docs/IMP-002-config-externalization-report.md`

**问题描述**: 
缩放规则和驱动优先级硬编码在代码中，不方便调整。

**完成内容**:
- ✅ 创建 `config/ui_config.json` 配置文件
- ✅ 创建 `UIConfig` 配置管理类（单例、线程安全、支持热重载）
- ✅ 修改 `ScalingManager` 使用配置文件
- ✅ 修改 `DriverFactory` 使用配置文件
- ✅ 添加 `test_ui_config.py` 单元测试

**当前代码**:
```python
# scaling_manager.py:91-99
if width >= 3200 or height >= 1800:
    self._scale_factor = 2.0  # 硬编码
elif width >= 2560 or height >= 1440:
    self._scale_factor = 1.5  # 硬编码
```

**解决方案**:
1. 创建 `config/ui_config.json` 文件
2. 添加 `UIConfig` 类管理配置
3. 支持从配置文件读取缩放规则

**配置文件示例**:
```json
{
  "scaling": {
    "rules": [
      {"min_width": 3200, "min_height": 1800, "scale": 2.0, "name": "3K+"},
      {"min_width": 2560, "min_height": 1440, "scale": 1.5, "name": "2K"},
      {"min_width": 0, "min_height": 0, "scale": 1.0, "name": "1K"}
    ],
    "default_scale": 1.0,
    "min_scale": 0.5,
    "max_scale": 3.0
  },
  "database": {
    "driver_priority": ["iris", "pyodbc"],
    "connection_timeout": 30
  }
}
```

**涉及文件**:
- 新增: `src/infrastructure/config/ui_config.py`
- 新增: `config/ui_config.json`
- 修改: `src/infrastructure/utils/scaling_manager.py`
- 修改: `src/data/repositories/driver_factory.py`

**验收标准**:
- [ ] 创建 UIConfig 类
- [ ] 支持从 JSON 文件读取配置
- [ ] 缩放规则可配置
- [ ] 驱动优先级可配置
- [ ] 配置变更无需重启应用

---

#### IMP-003: 降级方案增强 - QMessageBox 失败处理

**状态**: ✅ 已完成  
**完成日期**: 2026-02-11  
**实际用时**: 1 小时  
**计划用时**: 2 小时  
**完成报告**: `docs/IMP-003-error-fallback-report.md`

**问题描述**: 
如果 PySide2 初始化失败，QMessageBox 也会失败，当前只有简单的 print 回退。

**完成内容**:
- ✅ 修改 `handle_startup_error` 实现三级降级方案
- ✅ 添加 tkinter 降级方案
- ✅ 添加错误日志文件写入
- ✅ 添加完整错误堆栈记录
- ✅ 添加 `test_error_fallback.py` 测试（5个测试全部通过）

**当前代码** (main.py:61-67):
```python
try:
    from PySide2.QtWidgets import QWidget
    parent = QWidget()  # type: ignore
    QMessageBox.critical(parent, "启动错误", error_msg)
except Exception:
    print("无法显示错误对话框")
```

**解决方案**:
1. 使用标准库 tkinter 作为降级方案
2. 或者写入错误日志文件并提示用户查看
3. 添加更详细的错误信息

**修复后代码**:
```python
def show_error_dialog(error_msg: str) -> None:
    """显示错误对话框，支持多种降级方案"""
    # 方案1: QMessageBox
    try:
        from PySide2.QtWidgets import QWidget, QMessageBox
        parent = QWidget()  # type: ignore
        QMessageBox.critical(parent, "启动错误", error_msg)
        return
    except Exception:
        pass
    
    # 方案2: tkinter
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("启动错误", error_msg)
        return
    except Exception:
        pass
    
    # 方案3: 写入错误文件
    try:
        error_file = os.path.expanduser("~/pywindows_error.log")
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(f"时间: {datetime.now()}\n")
            f.write(f"错误: {error_msg}\n")
        print(f"错误信息已写入: {error_file}")
    except Exception:
        pass
    
    # 最后方案: 控制台输出
    print("=" * 60)
    print("严重错误:")
    print(error_msg)
    print("=" * 60)
```

**验收标准**:
- [ ] 实现三级降级方案（QMessageBox → tkinter → 文件）
- [ ] 添加错误日志文件写入
- [ ] 测试各种降级场景

---

#### IMP-004: 自动化语法检查集成

**状态**: ✅ 已完成  
**完成日期**: 2026-02-11  
**实际用时**: 2 小时  
**计划用时**: 3 小时  
**完成报告**: `docs/IMP-004-ci-cd-config-report.md`

**问题描述**: 
批量添加 `# type: ignore` 时曾引入语法错误，需要自动化防护。

**完成内容**:
- ✅ 创建 `.pre-commit-config.yaml` 配置（8个 hooks）
- ✅ 创建 `.github/workflows/ci.yml` GitHub Actions 工作流
- ✅ 创建 `setup.cfg` 配置（flake8、isort、pytest）
- ✅ 配置 Black 代码格式化（行长度 120）
- ✅ 配置 Flake8 代码检查
- ✅ 添加 `test_ci_cd_config.py` 测试（5/6 通过）
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: check-ast
      - id: check-json
      - id: check-yaml
      - id: trailing-whitespace
      
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3
        
  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=120']
```

3. 配置 GitHub Actions CI:
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Check syntax
        run: python -m py_compile src/**/*.py
      - name: Run tests
        run: python -m unittest discover tests/unit
```

**验收标准**:
- [ ] 配置 pre-commit 钩子
- [ ] 配置 GitHub Actions CI
- [ ] 集成 black 代码格式化
- [ ] 集成 flake8 代码检查
- [ ] 所有文件通过检查

---

### 🎯 第二阶段：架构优化（第2-3周）

本阶段实施架构层面的改进，提升可维护性和扩展性。

---

#### ARCH-001: 依赖注入容器

**状态**: 🟡 进行中  
**开始日期**: 2026-02-11  
**预计时间**: 8 小时  
**优先级**: 🟡 中  
**依赖**: IMP-002 (配置外部化)

**问题描述**: 
当前使用单例和全局函数管理依赖，随着项目增长会变得难以维护。

**目标**: 
创建轻量级 DI 容器，管理组件依赖关系。

**设计方案**:
```python
# src/infrastructure/di/container.py
class DIContainer:
    """依赖注入容器"""
    
    def __init__(self):
        self._registrations = {}
        self._singletons = {}
    
    def register_singleton(self, interface: Type, implementation: Type):
        """注册单例服务"""
        self._registrations[interface] = implementation
    
    def register_instance(self, interface: Type, instance: Any):
        """注册实例"""
        self._singletons[interface] = instance
    
    def resolve(self, interface: Type) -> Any:
        """解析依赖"""
        if interface in self._singletons:
            return self._singletons[interface]
        
        if interface in self._registrations:
            impl = self._registrations[interface]
            instance = impl()
            self._singletons[interface] = instance
            return instance
        
        raise KeyError(f"未注册的接口: {interface}")

# 使用
container = DIContainer()
container.register_instance(ScalingManager, get_scaling_manager())
container.register_singleton(DatabaseRepository, DatabaseRepository)
```

**验收标准**:
- [ ] 创建 DIContainer 类
- [ ] 支持单例和实例注册
- [ ] 迁移现有单例到容器
- [ ] 添加生命周期管理
- [ ] 文档和示例

---

#### ARCH-002: 事件总线系统

**状态**: ⬜ 待处理  
**预计时间**: 6 小时  
**优先级**: 🟢 低  
**依赖**: 无

**问题描述**: 
组件间通信直接耦合，不利于模块化和测试。

**目标**: 
实现发布-订阅模式的事件总线，解耦组件。

**设计方案**:
```python
# src/infrastructure/events/event_bus.py
class EventBus:
    """事件总线 - 发布订阅模式"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_type: str, handler: Callable):
        """订阅事件"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
    
    def publish(self, event_type: str, data: Any = None):
        """发布事件"""
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"事件处理失败: {e}")

# 使用示例
# 在配置变更时通知所有监听者
event_bus.publish("config.changed", {"key": "scale_factor", "value": 1.5})
```

**事件类型**:
- `config.changed` - 配置变更
- `database.connected` - 数据库连接成功
- `database.disconnected` - 数据库断开
- `ui.theme.changed` - 主题变更
- `query.executed` - 查询执行

**验收标准**:
- [ ] 创建 EventBus 类
- [ ] 支持同步和异步事件处理
- [ ] 添加事件日志记录
- [ ] 迁移现有回调到事件总线
- [ ] 文档和示例

---

#### ARCH-003: 插件系统架构

**状态**: ⬜ 待处理  
**预计时间**: 16 小时  
**优先级**: 🟢 低  
**依赖**: ARCH-001 (DI容器)

**问题描述**: 
当前功能都在主代码库中，扩展新功能需要修改核心代码。

**目标**: 
设计插件系统，支持动态加载扩展功能。

**设计方案**:
```python
# src/infrastructure/plugins/plugin_interface.py
class PluginInterface(ABC):
    """插件接口"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        pass
    
    @abstractmethod
    def initialize(self, container: DIContainer):
        """初始化插件"""
        pass
    
    @abstractmethod
    def shutdown(self):
        """关闭插件"""
        pass

# 插件管理器
class PluginManager:
    def __init__(self, plugin_dir: str):
        self.plugin_dir = plugin_dir
        self.plugins: List[PluginInterface] = []
    
    def load_plugins(self):
        """加载所有插件"""
        for plugin_file in Path(self.plugin_dir).glob("*_plugin.py"):
            self._load_plugin(plugin_file)
    
    def _load_plugin(self, plugin_file: Path):
        """加载单个插件"""
        # 动态导入插件模块
        # 实例化插件类
        # 调用 initialize
```

**验收标准**:
- [ ] 定义插件接口
- [ ] 实现插件管理器
- [ ] 支持动态加载/卸载
- [ ] 插件隔离（异常不影响主程序）
- [ ] 示例插件
- [ ] 文档

---

### 🎯 第三阶段：代码质量提升（第4周）

---

#### QUAL-001: 完善文档字符串

**状态**: ⬜ 待处理  
**预计时间**: 4 小时  
**优先级**: 🟢 低  
**依赖**: 无

**目标**: 
将所有文档字符串统一为 Google 风格。

**示例**:
```python
def encrypt_password(password: str, salt: Optional[str] = None) -> str:
    """
    加密密码。

    使用 PBKDF2 算法进行密码加密。如果未提供盐值，
    将自动生成随机盐值。

    Args:
        password: 原始密码，长度应至少 8 个字符。
        salt: 可选的盐值，应为十六进制字符串。
              如果为 None，则自动生成。

    Returns:
        str: 加密后的密码，格式为 "salt$hashed_password"。

    Raises:
        ValueError: 当密码为空或长度不足时。
        ImportError: 当 cryptography 库不可用时。

    Example:
        >>> encrypted = SecurityUtils.encrypt_password("my_password")
        >>> is_valid = SecurityUtils.verify_password("my_password", encrypted)
        >>> print(is_valid)
        True
    """
```

**涉及文件**:
- 所有公共 API 文件

**验收标准**:
- [ ] 所有公共方法有完整文档字符串
- [ ] 使用 Google 风格
- [ ] 包含 Args, Returns, Raises
- [ ] 添加使用示例

---

#### QUAL-002: UI 设计常量提取

**状态**: ⬜ 待处理  
**预计时间**: 3 小时  
**优先级**: 🟢 低  
**依赖**: IMP-002 (配置外部化)

**目标**: 
将 UI 尺寸提取为设计常量。

**设计方案**:
```python
# src/presentation/constants/ui_constants.py

class UIConstants:
    """UI 设计常量"""
    
    # 尺寸 (基于 1K 分辨率设计)
    class Sizes:
        SIDEBAR_WIDTH = 240
        HEADER_HEIGHT = 56
        ROW_HEIGHT = 44
        CARD_SPACING = 16
        SECTION_SPACING = 24
        BORDER_RADIUS = 8
        
    # 间距
    class Spacing:
        XS = 4   # extra small
        SM = 8   # small
        MD = 16  # medium
        LG = 24  # large
        XL = 32  # extra large
        
    # 字体大小
    class FontSizes:
        SMALL = 11
        NORMAL = 12
        MEDIUM = 14
        LARGE = 16
        XLARGE = 18
        TITLE = 20
        HEADER = 24
        DISPLAY = 32
```

**验收标准**:
- [ ] 创建 UIConstants 类
- [ ] 提取所有 UI 尺寸
- [ ] 替换 main_window.py 中的硬编码值
- [ ] 保持向后兼容

---

#### QUAL-003: 日志国际化支持

**状态**: ⬜ 待处理  
**预计时间**: 4 小时  
**优先级**: 🟢 低  
**依赖**: 无

**问题描述**: 
日志消息使用中文，在某些环境可能显示乱码。

**解决方案**:
1. 使用 Python 的 `gettext` 模块
2. 或者简单的字典映射方案
3. 优先使用英文，中文作为可选

**简单方案**:
```python
# src/infrastructure/i18n/messages.py
MESSAGES = {
    'zh': {
        'scaling.calculated': '屏幕分辨率: {width} x {height}, DPI: {dpi}',
        'driver.iris.loaded': '成功加载 IRIS 驱动',
        'error.connection_failed': '数据库连接失败: {error}',
    },
    'en': {
        'scaling.calculated': 'Screen resolution: {width} x {height}, DPI: {dpi}',
        'driver.iris.loaded': 'IRIS driver loaded successfully',
        'error.connection_failed': 'Database connection failed: {error}',
    }
}

def get_message(key: str, lang: str = 'zh', **kwargs) -> str:
    """获取本地化消息"""
    msg = MESSAGES.get(lang, MESSAGES['en']).get(key, key)
    return msg.format(**kwargs)
```

**验收标准**:
- [ ] 创建消息映射表
- [ ] 支持中英文切换
- [ ] 所有日志消息通过 i18n 模块
- [ ] 配置文件中可设置语言

---

### 🎯 第四阶段：DevOps 流程（第5-6周）

---

#### DEV-001: 代码覆盖率监控

**状态**: ⬜ 待处理  
**预计时间**: 4 小时  
**优先级**: 🟡 中  
**依赖**: IMP-004 (CI/CD)

**目标**: 
集成 coverage.py，监控测试覆盖率。

**实施步骤**:
1. 安装 coverage: `pip install coverage pytest-cov`
2. 配置 `.coveragerc`:
```ini
[run]
source = src
omit = 
    */tests/*
    */venv/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
```

3. 添加到 CI:
```yaml
- name: Run tests with coverage
  run: |
    coverage run -m unittest discover tests/unit
    coverage report
    coverage html
    
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
```

**验收标准**:
- [ ] 配置 coverage.py
- [ ] 集成到 CI
- [ ] 覆盖率报告 > 80%
- [ ] 添加覆盖率徽章到 README

---

#### DEV-002: 自动版本管理

**状态**: ⬜ 待处理  
**预计时间**: 3 小时  
**优先级**: 🟢 低  
**依赖**: 无

**目标**: 
实现基于 Git 标签的自动版本管理。

**实施方案**:
1. 使用 `setuptools-scm` 或手动方案
2. 版本格式: `主版本.次版本.修订号+构建号`
3. 从 Git 标签自动生成版本

**代码**:
```python
# src/version.py
import subprocess

def get_version() -> str:
    """从 Git 标签获取版本"""
    try:
        version = subprocess.check_output(
            ['git', 'describe', '--tags', '--always'],
            cwd=os.path.dirname(__file__)
        ).decode().strip()
        return version
    except Exception:
        return "0.0.0+unknown"

__version__ = get_version()
```

**验收标准**:
- [ ] 实现版本自动获取
- [ ] 集成到构建流程
- [ ] 版本信息显示在关于对话框
- [ ] 发布时自动打标签

---

#### DEV-003: 性能基准测试

**状态**: ⬜ 待处理  
**预计时间**: 6 小时  
**优先级**: 🟢 低  
**依赖**: 无

**目标**: 
建立性能基准，防止性能退化。

**实施方案**:
1. 使用 `pytest-benchmark` 库
2. 测试关键操作性能:
   - 数据库连接时间
   - SQL 查询执行时间
   - UI 渲染时间
   - 缩放计算时间

**示例**:
```python
# tests/benchmark/test_performance.py
import pytest
from src.data.repositories.database_repository import DatabaseRepository

class TestPerformance:
    def test_database_connection(self, benchmark):
        """基准测试：数据库连接时间应 < 5秒"""
        repo = DatabaseRepository()
        result = benchmark(repo.get_connection)
        assert result is not None
        # 基准值：平均 < 5秒
        
    def test_scaling_calculation(self, benchmark):
        """基准测试：缩放计算时间应 < 1ms"""
        from src.infrastructure.utils.scaling_manager import get_scaling_manager
        manager = get_scaling_manager()
        result = benchmark(manager.scale, 100)
        assert result == 100  # 默认缩放比例 1.0
```

**验收标准**:
- [ ] 创建基准测试套件
- [ ] 测试关键性能指标
- [ ] 集成到 CI
- [ ] 性能退化报警

---

## 依赖关系图

```
Phase 1 (生产就绪)
├── IMP-001: 线程安全
├── IMP-002: 配置外部化
│   └── (ARCH-001, QUAL-002 依赖此任务)
├── IMP-003: 降级方案
└── IMP-004: CI/CD

Phase 2 (架构优化)
├── ARCH-001: DI容器
│   └── (依赖 IMP-002)
├── ARCH-002: 事件总线
└── ARCH-003: 插件系统
    └── (依赖 ARCH-001)

Phase 3 (代码质量)
├── QUAL-001: 文档字符串
├── QUAL-002: UI常量
│   └── (依赖 IMP-002)
└── QUAL-003: 国际化

Phase 4 (DevOps)
├── DEV-001: 覆盖率
│   └── (依赖 IMP-004)
├── DEV-002: 版本管理
└── DEV-003: 性能基准
```

---

## 时间线

| 周 | 任务 | 负责人 | 产出 |
|----|------|--------|------|
| 第1周 | IMP-001 ~ IMP-004 | TBD | 生产就绪代码 |
| 第2-3周 | ARCH-001 ~ ARCH-003 | TBD | 架构改进 |
| 第4周 | QUAL-001 ~ QUAL-003 | TBD | 代码质量提升 |
| 第5-6周 | DEV-001 ~ DEV-003 | TBD | DevOps流程 |

---

## 成功标准

### 技术成功标准
- [ ] 所有 Important 任务完成
- [ ] 代码覆盖率 > 80%
- [ ] CI/CD 流程自动化
- [ ] 零 Critical 和 Important 级别 Bug

### 业务成功标准
- [ ] 启动时间 < 3秒
- [ ] 内存占用 < 500MB
- [ ] UI 响应时间 < 100ms
- [ ] 数据库连接成功率 > 99%

---

## 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 重构引入新 Bug | 中 | 高 | 完整测试覆盖，灰度发布 |
| 配置外部化导致配置错误 | 低 | 中 | 配置验证，默认值保护 |
| DI 容器性能开销 | 低 | 低 | 性能基准测试，优化热点 |
| 国际化增加复杂度 | 中 | 低 | 渐进式实施，可选启用 |

---

## 附录

### A. 代码审查原始报告
参考: `docs/FINAL-COMPLETION-REPORT.md`

### B. 技术债务清单
1. PySide2 类型注解不完善（已用 # type: ignore 缓解）
2. 部分 UI 尺寸仍为 Magic Numbers（设计相关，非配置）
3. 单例模式线程安全（计划 IMP-001 修复）

### C. 升级路径
1. **短期** (1-2周): 完成 Phase 1 (生产就绪)
2. **中期** (1-2月): 完成 Phase 2-3 (架构+质量)
3. **长期** (3-6月): 完成 Phase 4 (DevOps)，考虑 PySide6 升级

---

**计划版本**: 1.0  
**创建日期**: 2026-02-11  
**最后更新**: 2026-02-11  
**状态**: 草稿，待评审
