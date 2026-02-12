# 服务器部署指南

**版本**: 1.0  
**日期**: 2026-02-12  
**适用范围**: InterSystems Query Tool Server

---

## 目录

1. [系统要求](#系统要求)
2. [安装步骤](#安装步骤)
3. [配置说明](#配置说明)
4. [启动和停止](#启动和停止)
5. [Windows服务](#windows服务)
6. [监控和维护](#监控和维护)
7. [故障排除](#故障排除)

---

## 系统要求

### 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 4核 | 8核+ |
| 内存 | 8GB | 16GB+ |
| 磁盘 | 50GB SSD | 200GB+ SSD |
| 网络 | 100Mbps | 1Gbps |

### 软件要求

- **操作系统**: Windows 10 / Windows Server 2016+
- **Python**: 3.8+ (推荐 3.9)
- **依赖库**: 
  - PySide2 5.15+
  - aiohttp 3.8+
  - cryptography 41.0+

---

## 安装步骤

### 1. 安装Python

下载并安装 Python 3.9:
```powershell
# 从官网下载安装程序
https://www.python.org/downloads/release/python-390/

# 安装时勾选 "Add Python to PATH"
```

### 2. 创建虚拟环境

```powershell
# 创建项目目录
mkdir C:\QueryTool
mkdir C:\QueryTool\Server
cd C:\QueryTool\Server

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\activate
```

### 3. 安装依赖

```powershell
# 安装核心依赖
pip install PySide2==5.15.2
pip install aiohttp==3.8.6
pip install cryptography==41.0.7

# 可选依赖 (用于Windows服务)
pip install pywin32==306
```

### 4. 部署应用程序

```powershell
# 复制应用程序文件
xcopy /E /I D:\pywindows\src C:\QueryTool\Server\src
xcopy D:\pywindows\requirements.txt C:\QueryTool\Server\

# 安装所有依赖
pip install -r requirements.txt
```

### 5. 创建配置目录

```powershell
mkdir C:\QueryTool\Server\config
mkdir C:\QueryTool\Server\logs
mkdir C:\QueryTool\Server\uploads
mkdir C:\QueryTool\Server\temp
```

---

## 配置说明

### 主配置文件

创建 `config/server.json`:

```json
{
  "server": {
    "name": "QueryTool Server",
    "version": "1.0.0",
    "host": "0.0.0.0",
    "http_port": 443,
    "ws_port": 8080,
    "max_connections": 5000,
    "request_timeout": 30,
    "enable_http2": true,
    "enable_websocket": true
  },
  "workers": {
    "num_workers": 4,
    "max_tasks_per_worker": 1000,
    "worker_timeout": 300
  },
  "ssl": {
    "enabled": false,
    "cert_file": "config/server.crt",
    "key_file": "config/server.key"
  },
  "auth": {
    "jwt_secret": "your-secret-key-change-this",
    "token_expire_hours": 24,
    "max_login_attempts": 5,
    "lockout_duration_minutes": 30
  },
  "rate_limit": {
    "enabled": true,
    "requests_per_minute": 100,
    "burst_size": 20
  },
  "file_transfer": {
    "base_path": "uploads",
    "temp_path": "temp",
    "max_file_size": 10737418240,
    "max_storage_size": 107374182400,
    "chunk_size": 65536,
    "enable_virus_scan": false
  },
  "logging": {
    "level": "INFO",
    "file": "logs/server.log",
    "max_file_size": 10485760,
    "backup_count": 5,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  },
  "windows": {
    "enable_tray_icon": true,
    "enable_auto_start": false,
    "service_name": "QueryToolServer"
  }
}
```

### 环境变量

可以通过环境变量覆盖配置:

```powershell
# 服务器端口
$env:QUERYTOOL_HTTP_PORT=8443
$env:QUERYTOOL_WS_PORT=8080

# 工作进程数
$env:QUERYTOOL_WORKERS=8

# 日志级别
$env:QUERYTOOL_LOG_LEVEL=DEBUG

# 最大连接数
$env:QUERYTOOL_MAX_CONNECTIONS=10000
```

---

## 启动和停止

### 交互模式启动

```powershell
# 激活虚拟环境
.\venv\Scripts\activate

# 启动服务器 (控制台模式)
python -m src.infrastructure.server.standalone
```

### 后台模式启动

```powershell
# 使用Pythonw (无控制台窗口)
pythonw -m src.infrastructure.server.standalone
```

### 使用系统托盘

```powershell
# 启动并显示系统托盘图标
python -m src.infrastructure.server.tray_app
```

### 停止服务器

- **控制台模式**: 按 `Ctrl+C`
- **托盘模式**: 右键托盘图标 -> "Stop Server"
- **后台模式**: 使用任务管理器结束进程

---

## Windows服务

### 安装为Windows服务

```powershell
# 以管理员身份运行PowerShell

# 安装服务
python -m src.infrastructure.server.install_service

# 或使用sc命令
sc create QueryToolServer binPath= "C:\QueryTool\Server\venv\Scripts\python.exe C:\QueryTool\Server\src\infrastructure\server\service_main.py" start= auto
```

### 服务管理

```powershell
# 启动服务
sc start QueryToolServer
# 或
net start QueryToolServer

# 停止服务
sc stop QueryToolServer
# 或
net stop QueryToolServer

# 删除服务
sc delete QueryToolServer
```

### 开机自启动

```powershell
# 启用开机自启动
python -c "from src.infrastructure.server import create_startup_manager; m = create_startup_manager(); m.enable_startup()"

# 禁用开机自启动
python -c "from src.infrastructure.server import create_startup_manager; m = create_startup_manager(); m.disable_startup()"
```

---

## 监控和维护

### 查看服务器状态

```powershell
# 通过HTTP API获取状态
curl http://localhost:8080/api/status

# 响应示例
{
  "running": true,
  "uptime": 3600,
  "active_connections": 42,
  "total_requests": 15000,
  "workers": {
    "total": 4,
    "active": 4
  },
  "memory_usage_mb": 512,
  "cpu_percent": 15
}
```

### 查看日志

```powershell
# 实时查看日志
tail -f logs/server.log

# Windows PowerShell
Get-Content logs/server.log -Wait

# 搜索错误
Select-String -Path logs/server.log -Pattern "ERROR"
```

### 性能监控

```powershell
# 运行性能测试
python tests\performance\server_performance_test.py
```

### 定期维护任务

**每日**:
- 检查日志文件大小
- 查看错误报告

**每周**:
- 清理临时文件
- 检查磁盘空间

**每月**:
- 更新依赖库
- 安全审计

---

## 故障排除

### 常见问题

#### 1. 端口被占用

**错误信息**:
```
Address already in use: 443
```

**解决方案**:
```powershell
# 查找占用端口的进程
netstat -ano | findstr :443

# 结束进程
taskkill /PID <PID> /F

# 或修改配置使用其他端口
# 编辑 config/server.json, 修改 http_port
```

#### 2. 权限不足

**错误信息**:
```
Permission denied: logs/server.log
```

**解决方案**:
```powershell
# 以管理员身份运行
# 或修改目录权限
icacls "C:\QueryTool\Server" /grant Users:F /T
```

#### 3. 内存不足

**错误信息**:
```
MemoryError
```

**解决方案**:
```powershell
# 减少工作进程数
# 编辑 config/server.json:
{
  "workers": {
    "num_workers": 2  # 从4减少到2
  }
}
```

#### 4. SSL证书错误

**错误信息**:
```
SSL handshake failed
```

**解决方案**:
```powershell
# 生成自签名证书 (仅测试使用)
openssl req -x509 -newkey rsa:4096 -keyout config/server.key -out config/server.crt -days 365 -nodes

# 或禁用SSL
# 编辑 config/server.json:
{
  "ssl": {
    "enabled": false
  }
}
```

### 调试模式

```powershell
# 启用调试日志
$env:QUERYTOOL_LOG_LEVEL=DEBUG
python -m src.infrastructure.server.standalone
```

### 联系支持

- **GitHub Issues**: https://github.com/NodieYJ/intersystems-query-tool/issues
- **文档**: https://github.com/NodieYJ/intersystems-query-tool/tree/main/docs

---

## 附录

### A. 目录结构

```
C:\QueryTool\Server\
├── src\                    # 源代码
│   └── infrastructure\
│       └── server\         # 服务器模块
├── config\                 # 配置文件
│   └── server.json        # 主配置
├── logs\                   # 日志文件
├── uploads\                # 上传文件存储
├── temp\                   # 临时文件
├── venv\                   # Python虚拟环境
├── requirements.txt        # 依赖列表
└── README.md              # 说明文档
```

### B. 默认端口

| 服务 | 端口 | 用途 |
|------|------|------|
| HTTP/2 | 443 | 主API服务 |
| WebSocket | 8080 | 大文件传输 |
| 管理接口 | 8081 | 内部管理 |

### C. 性能基准

- **HTTP/2响应时间**: <100ms (P95)
- **WebSocket连接数**: 1000+ 并发
- **文件传输**: 100MB/s+ (千兆网络)
- **并发连接**: 5000+ (推荐配置)

---

## 更新日志

### v1.0.0 (2026-02-12)
- 初始版本发布
- 支持HTTP/2和WebSocket
- 多进程架构
- 文件传输服务
- Windows集成
