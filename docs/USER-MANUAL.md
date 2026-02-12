# QueryTool Server 用户手册

**版本**: 1.0.0  
**日期**: 2026-02-12  
**适用版本**: QueryTool Server 1.0+

---

## 目录

1. [简介](#简介)
2. [快速开始](#快速开始)
3. [系统托盘](#系统托盘)
4. [监控面板](#监控面板)
5. [文件传输](#文件传输)
6. [故障排除](#故障排除)
7. [常见问题](#常见问题)

---

## 简介

QueryTool Server 是一个高性能的 InterSystems 数据库查询工具服务器，支持：

- **5000+ 并发连接**: 使用多进程架构处理高并发请求
- **大文件传输**: 支持 GB 级文件的分块传输和断点续传
- **实时监控**: 提供性能、连接、日志监控面板
- **Windows 集成**: 系统托盘图标、Windows 服务支持
- **混合协议**: 支持 HTTP/2 和 WebSocket 协议

---

## 快速开始

### 启动服务器

#### 方法1: 使用系统托盘

```powershell
# 双击启动托盘应用程序
QueryToolServer.exe

# 或者命令行启动
python -m src.infrastructure.server.tray_app
```

托盘图标显示后，右键点击可以：
- **Show Status**: 查看服务器状态窗口
- **Start Server**: 启动服务器
- **Stop Server**: 停止服务器
- **Restart Server**: 重启服务器
- **Exit**: 退出程序

#### 方法2: 命令行启动

```powershell
# 前台模式（带控制台窗口）
python -m src.infrastructure.server.standalone

# 后台模式（无窗口）
pythonw -m src.infrastructure.server.standalone
```

#### 方法3: Windows 服务

```powershell
# 以管理员身份运行
sc start QueryToolServer
```

### 验证服务器运行

打开浏览器访问：
```
http://localhost:8080/health
```

应该返回：
```json
{
  "status": "healthy",
  "timestamp": 1707734400.0,
  "version": "1.0.0"
}
```

---

## 系统托盘

### 托盘图标说明

托盘图标颜色和状态：
- **🟢 绿色**: 服务器运行正常
- **🔴 红色**: 服务器错误
- **⚪ 灰色**: 服务器已停止

### 菜单功能

右键点击托盘图标显示菜单：

| 菜单项 | 功能 |
|--------|------|
| Status: RUNNING | 显示当前服务器状态（不可点击） |
| Show Status | 打开状态监控窗口 |
| Start Server | 启动服务器 |
| Stop Server | 停止服务器 |
| Restart Server | 重启服务器 |
| Exit | 退出应用程序 |

### 气泡通知

服务器会在以下情况显示气泡通知：
- 服务器启动完成
- 服务器遇到错误
- 文件传输完成
- 告警触发

---

## 监控面板

### 访问监控面板

打开浏览器访问：
```
http://localhost:8080/monitoring/overview
```

### 性能监控

#### 查看地址
```
http://localhost:8080/monitoring/performance
```

#### 监控指标

| 指标 | 说明 | 正常范围 |
|------|------|----------|
| CPU 使用率 | 服务器 CPU 使用百分比 | < 80% |
| 内存使用率 | 服务器内存使用百分比 | < 80% |
| 响应时间 | 平均请求响应时间 | < 100ms |
| P95 响应时间 | 95% 请求的响应时间 | < 200ms |
| 错误率 | 请求失败百分比 | < 1% |
| 吞吐量 | 每秒处理请求数 | 视配置 |

#### 历史图表

性能面板显示最近 60 个数据点的历史趋势：
- CPU 使用率趋势
- 内存使用率趋势

### 连接监控

#### 查看地址
```
http://localhost:8080/monitoring/connections
```

#### 监控指标

| 指标 | 说明 |
|------|------|
| 活跃连接数 | 当前连接的客户端数量 |
| 总连接数 | 服务器启动以来的总连接数 |
| 请求分布 | 各端点的请求数量统计 |

### 日志查看

#### 查看地址
```
http://localhost:8080/monitoring/logs
```

#### 查询参数

```
/monitoring/logs?level=ERROR&limit=50&search=connection
```

| 参数 | 说明 | 示例 |
|------|------|------|
| level | 日志级别 | DEBUG, INFO, WARNING, ERROR |
| limit | 返回条目数 | 100 |
| offset | 分页偏移 | 0 |
| search | 搜索关键词 | error |

#### 日志级别

- **DEBUG**: 调试信息
- **INFO**: 一般信息
- **WARNING**: 警告
- **ERROR**: 错误
- **CRITICAL**: 严重错误

---

## 文件传输

### 传输流程

#### 1. 初始化传输

```http
POST /api/transfer/init
Content-Type: application/json

{
  "file_name": "data.zip",
  "file_size": 104857600,
  "checksum": "sha256_hash"
}
```

响应：
```json
{
  "success": true,
  "transfer_id": "uuid",
  "chunk_size": 65536,
  "total_chunks": 1600
}
```

#### 2. 上传数据块

通过 WebSocket 发送二进制数据：
```
ws://localhost:8080/ws
```

数据格式：
- 前 4 字节：数据块索引（大端序）
- 剩余：数据块内容

#### 3. 查询进度

```http
GET /api/transfer/{transfer_id}/status
```

响应：
```json
{
  "transfer_id": "uuid",
  "progress": 0.75,
  "status": "transferring",
  "received_chunks": 1200,
  "total_chunks": 1600
}
```

#### 4. 完成传输

```http
POST /api/transfer/{transfer_id}/complete
```

### 断点续传

如果传输中断，可以查询已接收的数据块：

```http
GET /api/transfer/{transfer_id}/missing
```

响应：
```json
{
  "missing_chunks": [100, 101, 102, ...]
}
```

只需重新上传缺失的数据块即可。

### 传输限制

| 限制项 | 值 | 说明 |
|--------|-----|------|
| 最大文件大小 | 10 GB | 单个文件上限 |
| 数据块大小 | 64 KB | 每个数据块大小 |
| 并发传输 | 10 | 同时进行的传输数 |
| 存储空间 | 100 GB | 总存储上限 |

---

## 故障排除

### 服务器无法启动

#### 症状
托盘图标显示红色或点击"Start Server"无响应

#### 排查步骤

1. **检查端口占用**
```powershell
netstat -ano | findstr :8080
netstat -ano | findstr :443
```

2. **查看日志**
```powershell
type logs\server.log | findstr ERROR
```

3. **检查配置文件**
```powershell
type config\server.json
```

4. **手动启动查看错误**
```powershell
python -m src.infrastructure.server.standalone
```

#### 常见原因

- 端口被其他程序占用
- 配置文件格式错误
- 存储目录权限不足
- 内存不足

### 文件传输失败

#### 症状
传输进度停止或显示错误

#### 排查步骤

1. **检查网络连接**
2. **查看传输日志**
3. **检查存储空间**
```powershell
# 查看磁盘空间
wmic logicaldisk get size,freespace,caption
```

4. **验证文件大小**
确保文件不超过 10GB 限制

### 性能问题

#### 症状
响应慢、CPU 或内存使用率高

#### 优化建议

1. **增加工作进程数**
编辑 `config/server.json`：
```json
{
  "workers": {
    "num_workers": 8
  }
}
```

2. **限制并发连接数**
```json
{
  "server": {
    "max_connections": 3000
  }
}
```

3. **调整日志级别**
```json
{
  "logging": {
    "level": "WARNING"
  }
}
```

### 连接问题

#### 症状
无法连接到服务器

#### 排查步骤

1. **检查防火墙**
```powershell
# 查看防火墙规则
netsh advfirewall firewall show rule name=all | findstr 8080
```

2. **检查服务状态**
```powershell
sc query QueryToolServer
```

3. **测试本地连接**
```powershell
curl http://localhost:8080/health
```

---

## 常见问题

### Q: 如何修改服务器端口？

编辑 `config/server.json`：
```json
{
  "server": {
    "http_port": 8080,
    "ws_port": 8081
  }
}
```

重启服务器生效。

### Q: 如何启用开机自启动？

**方法1**: 托盘菜单
右键托盘图标 -> Settings -> Enable Auto Start

**方法2**: 命令行
```powershell
python -c "from src.infrastructure.server import create_startup_manager; m = create_startup_manager(); m.enable_startup()"
```

### Q: 如何备份配置文件？

配置文件位于：
```
C:\QueryTool\Server\config\server.json
```

复制该文件到备份位置即可。

### Q: 如何查看服务器版本？

访问：
```
http://localhost:8080/health
```

查看 `version` 字段。

### Q: 支持哪些浏览器？

推荐使用：
- Chrome 80+
- Firefox 75+
- Edge 80+

### Q: 如何清理日志文件？

日志文件会自动轮转，默认保留5个备份。手动清理：

```powershell
# 删除旧日志
Remove-Item logs\server.log.* -Force
```

### Q: 文件存储在哪里？

上传的文件默认存储在：
```
C:\QueryTool\Server\uploads\
```

临时文件存储在：
```
C:\QueryTool\Server\temp\
```

### Q: 如何更新服务器？

1. 停止服务器
2. 备份配置文件
3. 覆盖程序文件
4. 恢复配置文件
5. 启动服务器

---

## 技术支持

### 获取帮助

- **GitHub Issues**: https://github.com/NodieYJ/intersystems-query-tool/issues
- **文档**: https://github.com/NodieYJ/intersystems-query-tool/tree/main/docs
- **邮件**: 请通过 GitHub 联系

### 提交反馈

遇到问题请提供：
1. 服务器版本
2. 操作系统版本
3. 错误日志
4. 复现步骤

---

## 更新日志

### v1.0.0 (2026-02-12)
- 初始版本发布
- 支持 HTTP/2 和 WebSocket
- 多进程架构
- 文件传输服务
- Windows 集成
- 监控面板

---

**感谢您的使用！**
