# Bare Except 问题修复文档

**记录日期**: 2026-02-15  
**问题数量**: 5 处

---

## 问题清单

### 1. async_ops/__init__.py - 第 324 行

**文件**: `src/infrastructure/async_ops/__init__.py`  
**行号**: 324  
**上下文**:
```python
try:
  result.result = future.result()
except:  # <-- 问题
  pass
```

**问题分析**:
- 上下文：获取异步任务结果
- 可能的异常：`TimeoutError`, `CancelledError`, `Exception`
- 影响：静默失败，可能导致结果不可用

**建议修复**:
```python
try:
  result.result = future.result()
except Exception as e:  # 捕获所有异常
  result.status = TaskStatus.FAILED
  logger.warning(f"获取任务结果失败: {e}")
```

---

### 2. async_ops/__init__.py - 第 347 行

**文件**: `src/infrastructure/async_ops/__init__.py`  
**行号**: 347  
**上下文**:
```python
try:
  future.result(timeout=timeout)
  return True
except:  # <-- 问题
  return False
```

**问题分析**:
- 上下文：等待任务完成（带超时）
- 可能的异常：`TimeoutError`, `CancelledError`
- 影响：超时返回 False，但不确定是哪种情况

**建议修复**:
```python
try:
  future.result(timeout=timeout)
  return True
except (TimeoutError, asyncio.CancelledError):
  return False
except Exception as e:
  logger.warning(f"等待任务异常: {e}")
  return False
```

---

### 3. query_history_manager.py - 第 351 行

**文件**: `src/business/services/query_history_manager.py`  
**行号**: 351  
**上下文**:
```python
try:
  dt = datetime.fromisoformat(timestamp)
  time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
except:  # <-- 问题
  time_str = timestamp
```

**问题分析**:
- 上下文：解析时间戳
- 可能的异常：`ValueError`, `TypeError`
- 影响：格式不对时保留原始字符串（这是合理的后备行为）

**建议修复**:
```python
try:
  dt = datetime.fromisoformat(timestamp)
  time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
except (ValueError, TypeError) as e:
  # 时间戳格式不对时保留原始字符串
  logger.debug(f"时间戳解析失败: {e}, 保留原始值")
  time_str = timestamp
```

---

### 4. strategy_framework.py - 第 344 行

**文件**: `src/infrastructure/strategy/strategy_framework.py`  
**行号**: 344  
**上下文**:
```python
try:
  return {
    "name": temp_instance.get_name(),
    "description": temp_instance.get_description(),
    "class": strategy_class.__name__,
    "module": strategy_class.__module__
  }
except:  # <-- 问题
  return {
    "name": name,
    "class": strategy_class.__name__,
    "module": strategy_class.__module__
  }
```

**问题分析**:
- 上下文：获取策略元数据
- 可能的异常：`AttributeError`, `Exception`
- 影响：方法不存在时返回简化信息

**建议修复**:
```python
try:
  return {
    "name": temp_instance.get_name(),
    "description": temp_instance.get_description(),
    "class": strategy_class.__name__,
    "module": strategy_class.__module__
  }
except AttributeError:
  # 方法不存在，返回简化信息
  return {
    "name": name,
    "class": strategy_class.__name__,
    "module": strategy_class.__module__
  }
except Exception as e:
  logger.warning(f"获取策略元数据失败: {e}")
  return {
    "name": name,
    "class": strategy_class.__name__,
    "module": strategy_class.__module__
  }
```

---

### 5. multiprocess.py - 第 284 行

**文件**: `src/infrastructure/server/multiprocess.py`  
**行号**: 284  
**上下文**:
```python
try:
  self._task_queues[worker_id].put(None, timeout=1.0)
except:  # <-- 问题
  pass
```

**问题分析**:
- 上下文：发送退出信号到工作进程
- 可能的异常：`Queue.Full`, `KeyError`, `Exception`
- 影响：静默失败，进程可能无法正常退出

**建议修复**:
```python
try:
  self._task_queues[worker_id].put(None, timeout=1.0)
except (Queue.Full, KeyError) as e:
  logger.warning(f"发送退出信号失败: {e}")
except Exception as e:
  logger.error(f"发送退出信号时发生异常: {e}")
```

---

## 修复优先级

| 优先级 | 位置 | 原因 |
|--------|------|------|
| 🔴 高 | multiprocess.py:284 | 可能导致进程泄漏 |
| 🟡 中 | async_ops:324, 347 | 影响任务状态准确性 |
| 🟢 低 | query_history_manager:351 | 有合理的后备行为 |
| 🟢 低 | strategy_framework:344 | 有后备处理 |

---

## 修复状态

- [ ] async_ops/__init__.py:324
- [ ] async_ops/__init__.py:347
- [ ] query_history_manager.py:351
- [ ] strategy_framework.py:344
- [ ] multiprocess.py:284

---

**文档创建完成**: 准备进行修复
