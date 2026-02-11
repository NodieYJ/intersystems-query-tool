#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
依赖注入迁移指南

演示如何从传统单例模式迁移到DI容器模式
"""

# ============================================================================
# 传统方式（迁移前）
# ============================================================================

def traditional_usage_example():
    """传统使用方式示例"""
    from src.infrastructure.utils.scaling_manager import get_scaling_manager
    from src.infrastructure.config.ui_config import get_ui_config
    from src.infrastructure.logging.logger import setup_logger
    
    # 直接获取单例实例
    scaling_manager = get_scaling_manager()
    config = get_ui_config()
    logger = setup_logger()
    
    # 使用服务
    scale_factor = scaling_manager.get_scale_factor()
    config_value = config.get("font.size", 12)
    logger.info(f"当前缩放比例: {scale_factor}")
    
    return scaling_manager, config, logger


# ============================================================================
# 新方式（迁移后）- 方式1: 使用便捷函数
# ============================================================================

def di_convenient_usage_example():
    """DI便捷函数使用方式"""
    from src.infrastructure.di.service_registration import get_service
    from src.infrastructure.di.service_registration import (
        IConfig,
        ILogger,
        IScalingManager,
    )
    
    # 通过DI容器获取服务（需要先初始化容器）
    scaling_manager = get_service(IScalingManager)
    config = get_service(IConfig)
    logger = get_service(ILogger)
    
    # 使用服务（与之前相同）
    scale_factor = scaling_manager.get_scale_factor()
    config_value = config.get("font.size", 12)
    logger.info(f"当前缩放比例: {scale_factor}")
    
    return scaling_manager, config, logger


# ============================================================================
# 新方式（迁移后）- 方式2: 使用resolve函数
# ============================================================================

def di_resolve_usage_example():
    """DI resolve函数使用方式"""
    from src.infrastructure.di import resolve
    from src.infrastructure.di.service_registration import (
        IConfig,
        ILogger,
        IScalingManager,
    )
    
    # 通过resolve获取服务
    scaling_manager = resolve(IScalingManager)
    config = resolve(IConfig)
    logger = resolve(ILogger)
    
    return scaling_manager, config, logger


# ============================================================================
# 新方式（迁移后）- 方式3: 构造函数注入（推荐）
# ============================================================================

class NewStyleService:
    """
    新风格服务 - 使用构造函数注入
    
    这是推荐的迁移方式，服务通过构造函数声明依赖，
    由DI容器自动注入，无需手动获取依赖。
    """
    
    def __init__(
        self,
        scaling_manager: IScalingManager,
        config: IConfig,
        logger: ILogger
    ):
        self.scaling_manager = scaling_manager
        self.config = config
        self.logger = logger
    
    def do_work(self):
        """执行业务操作"""
        scale_factor = self.scaling_manager.get_scale_factor()
        self.logger.info(f"使用缩放比例 {scale_factor} 执行任务")


def di_constructor_injection_example():
    """构造函数注入示例"""
    from src.infrastructure.di import resolve
    
    # 当解析NewStyleService时，DI容器会自动注入所需依赖
    service = resolve(NewStyleService)
    service.do_work()
    
    return service


# ============================================================================
# 混合使用策略（渐进式迁移）
# ============================================================================

def hybrid_usage_example():
    """
    混合使用示例 - 支持渐进式迁移
    
    在迁移过程中，可以同时支持新旧两种方式。
    这是main.py中采用的策略。
    """
    from src.infrastructure.di import resolve
    from src.infrastructure.di.service_registration import (
        IScalingManager,
        initialize_container,
    )
    from src.infrastructure.utils.scaling_manager import get_scaling_manager
    
    # 初始化容器（应用程序启动时执行一次）
    container = initialize_container()
    
    # 优先使用DI容器获取服务（如果可用）
    if container and container.is_registered(IScalingManager):
        scaling_manager = resolve(IScalingManager)
        print("使用DI容器获取服务")
    else:
        # 回退到传统方式
        scaling_manager = get_scaling_manager()
        print("使用传统方式获取服务")
    
    return scaling_manager


# ============================================================================
# 迁移步骤
# ============================================================================

"""
迁移步骤：

1. 无需修改现有代码
   - DI容器与现有单例模式完全兼容
   - 可以逐步迁移，无需一次性重构

2. 在新代码中使用DI（推荐）
   - 新服务类使用构造函数声明依赖
   - 通过resolve()或get_service()获取服务

3. 逐步重构现有代码
   - 将硬编码的依赖改为接口依赖
   - 使用构造函数注入代替直接获取
   
4. 完整迁移后（可选）
   - 移除传统单例工厂函数
   - 所有服务通过DI容器管理

示例迁移：

# 迁移前
class OldService:
    def __init__(self):
        from src.infrastructure.utils.scaling_manager import get_scaling_manager
        self.scaling = get_scaling_manager()  # 硬编码依赖

# 迁移后
class NewService:
    def __init__(self, scaling_manager: IScalingManager):  # 依赖注入
        self.scaling = scaling_manager
"""


if __name__ == "__main__":
    print("依赖注入迁移指南")
    print("=" * 60)
    print("\n1. 传统方式（仍然有效）：")
    traditional_usage_example()
    
    print("\n2. 混合使用策略（推荐用于main.py）：")
    hybrid_usage_example()
    
    print("\n" + "=" * 60)
    print("DI容器集成完成！")
    print("所有现有代码无需修改即可继续工作。")
    print("新代码可以使用构造函数注入模式。")
