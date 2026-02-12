#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
接口单元测试

测试阶段1创建的接口和异常体系
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.infrastructure.interfaces import (
    IRepository,
    IQueryRepository,
    IService,
    IDataService,
    IDataAnalysisService,
)

from src.infrastructure.exceptions import (
    AppException,
    DatabaseException,
    BusinessException,
    ConfigurationException,
    NotFoundException,
    ValidationException,
)


def test_interfaces_import():
    """测试接口可以正确导入"""
    print("\n测试1: 接口导入")
    
    # 验证所有接口都存在
    assert IRepository is not None
    assert IQueryRepository is not None
    assert IService is not None
    assert IDataService is not None
    assert IDataAnalysisService is not None
    
    print("  [OK] 所有接口成功导入")


def test_exceptions_import():
    """测试异常类可以正确导入"""
    print("\n测试2: 异常类导入")
    
    assert AppException is not None
    assert DatabaseException is not None
    assert BusinessException is not None
    assert ConfigurationException is not None
    
    print("  [OK] 所有异常类成功导入")


def test_exception_creation():
    """测试异常对象创建"""
    print("\n测试3: 异常对象创建")
    
    # 创建基础异常 - 使用驼峰命名
    exc = AppException("测试错误", "ERR_001")
    assert exc.errorCode == "ERR_001"
    assert exc.message == "测试错误"
    
    # 创建带详情的异常
    exc_with_details = DatabaseException(
        "数据库错误",
        "DB_001",
        details={"server": "localhost"}
    )
    assert exc_with_details.details["server"] == "localhost"
    
    # 测试 toDict 方法
    exc_dict = exc_with_details.toDict()
    assert exc_dict["errorCode"] == "DB_001"
    
    print("  [OK] 异常对象创建成功")


def test_exception_hierarchy():
    """测试异常继承关系"""
    print("\n测试4: 异常继承关系")
    
    # 所有异常都继承自 AppException
    assert issubclass(DatabaseException, AppException)
    assert issubclass(BusinessException, AppException)
    assert issubclass(ConfigurationException, AppException)
    
    # 具体异常继承自父类
    assert issubclass(NotFoundException, BusinessException)
    assert issubclass(ValidationException, BusinessException)
    
    print("  [OK] 异常继承关系正确")


def test_interface_methods():
    """测试接口方法签名"""
    print("\n测试5: 接口方法签名")
    
    # 检查 IRepository 是抽象基类
    assert hasattr(IRepository, '__abstractmethods__')
    
    # 检查 IDataService 方法
    assert hasattr(IDataService, 'getData')
    assert hasattr(IDataService, 'saveData')
    
    # 检查 IDataAnalysisService 方法
    assert hasattr(IDataAnalysisService, 'getStatistics')
    
    print("  [OK] 接口方法签名正确")


def test_exception_properties():
    """测试异常属性"""
    print("\n测试6: 异常属性")
    
    exc = AppException("测试消息", "TEST_001", {"key": "value"})
    
    # 验证所有属性
    assert hasattr(exc, 'message')
    assert hasattr(exc, 'errorCode')
    assert hasattr(exc, 'details')
    assert hasattr(exc, 'timestamp')
    assert hasattr(exc, 'tracebackStr')
    
    # 验证 __str__
    assert "TEST_001" in str(exc)
    assert "测试消息" in str(exc)
    
    print("  [OK] 异常属性正确")


def test_not_found_exception():
    """测试NotFoundException"""
    print("\n测试7: NotFoundException")
    
    exc = NotFoundException(
        "用户不存在",
        resourceType="User",
        resourceId=123
    )
    
    assert exc.errorCode == "BZ_002"
    assert exc.details["resourceType"] == "User"
    assert exc.details["resourceId"] == 123
    
    print("  [OK] NotFoundException工作正常")


def test_validation_exception():
    """测试ValidationException"""
    print("\n测试8: ValidationException")
    
    exc = ValidationException(
        "邮箱格式错误",
        field="email",
        value="invalid-email"
    )
    
    assert exc.errorCode == "BZ_001"
    assert exc.details["field"] == "email"
    assert exc.details["value"] == "invalid-email"
    
    print("  [OK] ValidationException工作正常")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("阶段1 接口和异常体系测试")
    print("=" * 60)
    
    tests = [
        test_interfaces_import,
        test_exceptions_import,
        test_exception_creation,
        test_exception_hierarchy,
        test_interface_methods,
        test_exception_properties,
        test_not_found_exception,
        test_validation_exception,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {test.__name__}: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
