#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
阶段2测试 - 事件总线和异步执行框架
"""

import sys
import os
import time
sys.path.insert(0, os.path.abspath('.'))

from src.infrastructure.events import (
    EventBus,
    Event,
    EventPriority,
    getEventBus,
    publishEvent,
)


def test_event_bus_creation():
    """测试EventBus创建"""
    print("\n测试1: EventBus创建")
    
    bus = EventBus("test")
    
    assert bus.name == "test", "EventBus名称应该匹配"
    assert bus is not None, "EventBus应该成功创建"
    print("  [OK] EventBus创建成功")


def test_event_publish_subscribe():
    """测试事件发布和订阅"""
    print("\n测试2: 事件发布和订阅")
    
    bus = EventBus("test2")
    received_events = []
    
    def handler(event):
        received_events.append(event)
    
    # 订阅事件
    sub_id = bus.subscribe("test.event", handler)
    
    # 发布事件
    event = Event("test.event", data={"message": "hello"})
    bus.publish(event)
    
    # 验证接收
    assert len(received_events) == 1, "应该收到1个事件"
    assert received_events[0].data["message"] == "hello", "数据应该匹配"
    
    print("  [OK] 事件发布和订阅工作正常")


def test_event_priority():
    """测试事件优先级"""
    print("\n测试3: 事件优先级")
    
    # 创建不同优先级的事件
    bus = EventBus("priority_test")
    order = []
    
    def handler_low(event):
        order.append("low")
    
    def handler_normal(event):
        order.append("normal")
    
    def handler_high(event):
        order.append("high")
    
    # 订阅（按低、高、正常顺序订阅）
    bus.subscribe("priority.test", handler_low, priority=EventPriority.LOW)
    bus.subscribe("priority.test", handler_high, priority=EventPriority.HIGH)
    bus.subscribe("priority.test", handler_normal, priority=EventPriority.NORMAL)
    
    # 发布事件
    bus.publish(Event("priority.test"))
    
    # 验证顺序（高 -> 正常 -> 低）
    assert order[0] == "high", "高优先级应该最先执行"
    assert order[1] == "normal", "正常优先级第二"
    assert order[2] == "low", "低优先级最后"
    
    print("  [OK] 事件优先级工作正常")


def test_event_history():
    """测试事件历史记录"""
    print("\n测试4: 事件历史记录")
    
    bus = EventBus("history_test")
    bus.clearHistory()
    
    # 发布几个事件
    bus.publish(Event("history.test", data={"id": 1}))
    bus.publish(Event("history.test", data={"id": 2}))
    bus.publish(Event("history.other", data={"id": 3}))
    
    # 获取历史
    history = bus.getHistory("history.test")
    
    assert len(history) == 2, "应该返回2个事件"
    assert history[0].data["id"] == 1, "第一个事件ID应该是1"
    
    print("  [OK] 事件历史记录工作正常")


def test_event_helper_functions():
    """测试便捷函数"""
    print("\n测试5: 便捷函数")
    
    received = []
    
    # 使用默认总线
    bus = getEventBus("default")
    bus.subscribe("helper.test", lambda e: received.append(e))
    
    # 使用便捷函数
    publishEvent("helper.test", data={"test": "data"})
    
    # 给事件处理一点时间
    time.sleep(0.1)
    
    assert len(received) == 1, "应该收到事件"
    
    print("  [OK] 便捷函数工作正常")


def test_event_unsubscribe():
    """测试取消订阅"""
    print("\n测试6: 取消订阅")
    
    bus = EventBus("unsub_test")
    received = []
    
    def handler(event):
        received.append(event)
    
    # 订阅并获取ID
    sub_id = bus.subscribe("unsub.test", handler)
    
    # 发布一次
    bus.publish(Event("unsub.test"))
    assert len(received) == 1, "应该收到1个事件"
    
    # 取消订阅
    result = bus.unsubscribe("unsub.test", sub_id)
    assert result == True, "取消订阅应该成功"
    
    # 再次发布
    bus.publish(Event("unsub.test"))
    assert len(received) == 1, "不应该再收到事件"
    
    print("  [OK] 取消订阅工作正常")


def test_wildcard_subscription():
    """测试通配符订阅"""
    print("\n测试7: 通配符订阅")
    
    bus = EventBus("wildcard_test")
    received = []
    
    def handler(event):
        received.append(event.eventType)
    
    # 使用通配符订阅
    bus.subscribe("*", handler)
    
    # 发布不同类型的事件
    bus.publish(Event("event.a"))
    bus.publish(Event("event.b"))
    bus.publish(Event("event.c"))
    
    assert len(received) == 3, "应该收到3个事件"
    assert "event.a" in received
    assert "event.b" in received
    assert "event.c" in received
    
    print("  [OK] 通配符订阅工作正常")


def test_event_once():
    """测试一次性订阅"""
    print("\n测试8: 一次性订阅")
    
    bus = EventBus("once_test")
    received = []
    
    def handler(event):
        received.append(event)
    
    # 一次性订阅
    bus.subscribe("once.test", handler, once=True)
    
    # 发布两次
    bus.publish(Event("once.test"))
    bus.publish(Event("once.test"))
    
    # 只应该收到一次
    assert len(received) == 1, "只应该收到1个事件"
    
    print("  [OK] 一次性订阅工作正常")


def test_stop_propagation():
    """测试停止事件传播"""
    print("\n测试9: 停止事件传播")
    
    bus = EventBus("stop_test")
    received = []
    
    def handler1(event):
        received.append(1)
        event.stopPropagation()
    
    def handler2(event):
        received.append(2)
    
    # 两个处理器
    bus.subscribe("stop.test", handler1)
    bus.subscribe("stop.test", handler2)
    
    # 发布事件
    bus.publish(Event("stop.test"))
    
    # 只有第一个处理器应该执行
    assert len(received) == 1, "只应该有1个处理器执行"
    assert received[0] == 1
    
    print("  [OK] 停止事件传播工作正常")


def test_handler_count():
    """测试处理器计数"""
    print("\n测试10: 处理器计数")
    
    bus = EventBus("count_test")
    
    # 初始为0
    assert bus.getHandlerCount("count.test") == 0
    
    # 添加处理器
    bus.subscribe("count.test", lambda e: None)
    bus.subscribe("count.test", lambda e: None)
    
    assert bus.getHandlerCount("count.test") == 2
    assert bus.getHandlerCount() == 2  # 总数
    
    print("  [OK] 处理器计数工作正常")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("阶段2 事件总线测试")
    print("=" * 60)
    
    tests = [
        test_event_bus_creation,
        test_event_publish_subscribe,
        test_event_priority,
        test_event_history,
        test_event_helper_functions,
        test_event_unsubscribe,
        test_wildcard_subscription,
        test_event_once,
        test_stop_propagation,
        test_handler_count,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
