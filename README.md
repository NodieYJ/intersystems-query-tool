# PyWindows 桌面应用程序

功能完整的桌面窗体应用程序，支持窗口控制、尺寸调整、滚动条功能和界面交互。

## 最新更新 (2024-02)

### 🔒 安全增强
- **密码强度检查**: 自动验证密码复杂度
- **恒定时间比较**: 防止时序攻击
- **SQL 注入防护**: 自动检测危险查询
- **输入验证**: Schema 和参数安全验证

### ⚡ 性能优化
- **连接池超时控制**: 防止资源耗尽
- **配置驱动服务**: 支持 JSON 配置管理
- **缓存机制**: 数据服务缓存支持

## 项目结构

```
src/
├── presentation/         # 表示层
│   ├── windows/          # 窗口
│   ├── dialogs/          # 对话框
│   └── widgets/          # 自定义控件
├── business/             # 业务逻辑层
│   ├── services/         # 服务
│   └── models/            # 模型
├── data/                 # 数据访问层
│   ├── repositories/     # 仓库
│   └── entities/          # 实体
├── infrastructure/        # 基础设施层
│   ├── config/            # 配置管理
│   ├── utils/             # 工具类
│   └── logging/           # 日志管理
└── main.py                # 主入口文件
```

## 功能特性

- 支持多窗口管理
- 数据库连接配置
- 数据下载功能
- SQL查询功能
- 日志查看功能
- 支持Intersystems IRIS和Cache数据库
- 🔒 **安全功能**: 密码加密、强度检查、SQL注入防护
- ⚡ **性能优化**: 连接池管理、查询超时控制、服务注册表

## 安装与配置

### 环境要求

- Python 3.8+
- PySide2 5.14.0+
- 可选: Intersystems IRIS Python驱动或pyodbc

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置文件

项目使用`config.json`文件存储配置信息，包括数据库连接参数、应用程序设置等。

## 使用指南

### 启动应用程序

```bash
python src/main.py
```

### 数据库配置

1. 点击菜单栏中的"设置" -> "连接配置"
2. 填写数据库连接参数
3. 点击"测试连接"按钮验证连接是否成功
4. 点击"保存"按钮保存配置

### 数据下载

1. 点击菜单栏中的"查询统计" -> "数据下载配置"
2. 配置下载参数
3. 点击"查询统计" -> "数据下载"
4. 点击"开始下载"按钮开始下载数据

### SQL查询

1. 点击菜单栏中的"查询统计" -> "SQL查询"
2. 在SQL输入框中输入SQL查询语句
3. 点击"执行查询"按钮执行查询
4. 查看查询结果

## 开发指南

### 代码规范

项目遵循PEP 8代码规范，使用以下工具进行代码质量检查：

- flake8: 代码风格检查
- black: 代码格式化
- isort: 导入语句排序

### 测试

项目使用pytest进行单元测试和集成测试：

```bash
# 运行所有测试
pytest

# 运行安全功能测试
pytest tests/unit/test_security_enhanced.py -v

# 运行输入验证测试
pytest tests/unit/test_input_validation.py -v
```

### 安全测试

项目包含专门的安全功能测试：

```bash
# 密码加密和验证测试
python -m unittest tests.unit.test_security_enhanced

# 输入验证测试
python -m unittest tests.unit.test_input_validation
```

### 构建与分发

使用setuptools构建项目：

```bash
python setup.py sdist bdist_wheel
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务器地址、端口、用户名和密码是否正确
   - 确保数据库服务正在运行
   - 检查网络连接是否正常

2. **应用程序启动失败**
   - 检查Python版本是否符合要求
   - 确保所有依赖项都已正确安装
   - 查看日志文件获取详细错误信息

3. **功能无法正常使用**
   - 检查是否已正确配置相关参数
   - 查看日志文件获取详细错误信息

4. **安全功能问题**
   - 确保 cryptography 库已正确安装 (`pip install cryptography>=3.4.8`)
   - 密码强度要求：至少8个字符
   - 检查 config/services.json 配置是否正确

### 日志文件

日志文件存储在`log`目录中，可通过应用程序中的"设置" -> "日志"菜单查看。

### 安全日志

安全相关事件会记录以下日志级别：
- `WARNING`: 密码强度不足、登录失败
- `ERROR`: 加密失败、SQL注入检测

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 许可证

本项目采用MIT许可证。
