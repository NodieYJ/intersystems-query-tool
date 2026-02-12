#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
服务层接口定义模块

定义业务逻辑层的服务接口，包括：
- IService: 服务基接口
- IDataService: 数据服务接口
- IAnalysisService: 数据分析服务接口
- IConnectionService: 连接服务接口
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union

T = TypeVar('T')
R = TypeVar('R')


class IService(ABC):
    """
    服务接口基类
    
    所有业务服务都应该实现此接口，确保服务的一致性和可测试性。
    
    示例:
        >>> class UserService(IService):
        ...     def get_name(self) -> str:
        ...         return "UserService"
        ...         
        ...     def initialize(self) -> None:
        ...         pass
    """
    
    @abstractmethod
    def get_name(self) -> str:
        """
        获取服务名称
        
        Returns:
            str: 服务唯一标识名称
        """
        pass
    
    @abstractmethod
    def initialize(self) -> None:
        """
        初始化服务
        
        在服务启动时调用，用于加载配置、建立连接等。
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """
        关闭服务
        
        在服务停止时调用，用于释放资源、关闭连接等。
        """
        pass
    
    def is_initialized(self) -> bool:
        """
        检查服务是否已初始化
        
        Returns:
            bool: 是否已初始化
        """
        return True


class IDataService(IService, ABC):
    """
    数据服务接口
    
    提供数据查询、导出、分析等核心业务功能。
    
    示例:
        >>> service = DataService()
        >>> service.initialize()
        >>> data = service.query_data("SELECT * FROM users")
        >>> service.export_data(data, "csv", "/path/to/export.csv")
    """
    
    @abstractmethod
    def query_data(
        self, 
        sql: str, 
        parameters: Optional[List[Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        执行数据查询
        
        Args:
            sql: SQL查询语句
            parameters: 查询参数
            
        Returns:
            List[Dict[str, Any]]: 查询结果
            
        Raises:
            BusinessException: 查询执行失败
        """
        pass
    
    @abstractmethod
    def export_data(
        self, 
        data: List[Dict[str, Any]], 
        format_type: str, 
        file_path: str
    ) -> bool:
        """
        导出数据到文件
        
        Args:
            data: 要导出的数据
            format_type: 导出格式 (csv, excel, json等)
            file_path: 导出文件路径
            
        Returns:
            bool: 导出是否成功
            
        Raises:
            BusinessException: 导出失败
        """
        pass
    
    @abstractmethod
    def get_table_list(self) -> List[str]:
        """
        获取数据库中的所有表名
        
        Returns:
            List[str]: 表名列表
        """
        pass
    
    @abstractmethod
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """
        获取表结构信息
        
        Args:
            table_name: 表名
            
        Returns:
            List[Dict[str, Any]]: 字段信息列表
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        测试数据库连接
        
        Returns:
            bool: 连接是否正常
        """
        pass
    
    @abstractmethod
    def get_connection_status(self) -> Dict[str, Any]:
        """
        获取连接状态信息
        
        Returns:
            Dict[str, Any]: 状态信息字典
        """
        pass


class IAnalysisService(IService, ABC):
    """
    数据分析服务接口
    
    提供数据统计、分析、可视化等功能。
    
    示例:
        >>> service = AnalysisService()
        >>> stats = service.calculate_statistics(dataframe)
        >>> chart_data = service.generate_chart_data(dataframe, "line")
    """
    
    @abstractmethod
    def calculate_statistics(
        self, 
        data: Any
    ) -> Dict[str, Any]:
        """
        计算数据统计信息
        
        Args:
            data: 数据对象（如DataFrame）
            
        Returns:
            Dict[str, Any]: 统计信息字典，包含count, mean, std, min, max等
        """
        pass
    
    @abstractmethod
    def generate_chart_data(
        self, 
        data: Any, 
        chart_type: str
    ) -> Dict[str, Any]:
        """
        生成图表数据
        
        Args:
            data: 数据源
            chart_type: 图表类型 (line, bar, pie, scatter等)
            
        Returns:
            Dict[str, Any]: 图表数据配置
        """
        pass
    
    @abstractmethod
    def filter_data(
        self, 
        data: Any, 
        conditions: List[Dict[str, Any]]
    ) -> Any:
        """
        根据条件过滤数据
        
        Args:
            data: 原始数据
            conditions: 过滤条件列表
            
        Returns:
            Any: 过滤后的数据
        """
        pass
    
    @abstractmethod
    def sort_data(
        self, 
        data: Any, 
        columns: List[str], 
        ascending: bool = True
    ) -> Any:
        """
        排序数据
        
        Args:
            data: 原始数据
            columns: 排序列
            ascending: 是否升序
            
        Returns:
            Any: 排序后的数据
        """
        pass


class IConnectionService(IService, ABC):
    """
    连接服务接口
    
    管理数据库连接配置和连接池。
    
    示例:
        >>> service = ConnectionService()
        >>> config = ConnectionConfig(server="localhost", port=1972)
        >>> service.save_connection_config("default", config)
        >>> service.connect("default")
    """
    
    @abstractmethod
    def save_connection_config(
        self, 
        name: str, 
        config: Dict[str, Any]
    ) -> bool:
        """
        保存连接配置
        
        Args:
            name: 配置名称
            config: 配置参数字典
            
        Returns:
            bool: 保存是否成功
        """
        pass
    
    @abstractmethod
    def get_connection_config(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取连接配置
        
        Args:
            name: 配置名称
            
        Returns:
            Optional[Dict[str, Any]]: 配置字典，不存在返回None
        """
        pass
    
    @abstractmethod
    def list_connection_configs(self) -> List[str]:
        """
        获取所有连接配置名称列表
        
        Returns:
            List[str]: 配置名称列表
        """
        pass
    
    @abstractmethod
    def delete_connection_config(self, name: str) -> bool:
        """
        删除连接配置
        
        Args:
            name: 配置名称
            
        Returns:
            bool: 删除是否成功
        """
        pass
    
    @abstractmethod
    def test_connection(self, config: Dict[str, Any]) -> bool:
        """
        测试连接配置
        
        Args:
            config: 连接配置
            
        Returns:
            bool: 连接是否成功
        """
        pass
    
    @abstractmethod
    def connect(self, config_name: str) -> bool:
        """
        使用指定配置建立连接
        
        Args:
            config_name: 配置名称
            
        Returns:
            bool: 连接是否成功
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """断开当前连接"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """
        检查是否已连接
        
        Returns:
            bool: 连接状态
        """
        pass


class ILoggingService(IService, ABC):
    """
    日志服务接口
    
    提供统一的日志记录和管理功能。
    """
    
    @abstractmethod
    def log_info(self, message: str, **kwargs: Any) -> None:
        """记录信息日志"""
        pass
    
    @abstractmethod
    def log_warning(self, message: str, **kwargs: Any) -> None:
        """记录警告日志"""
        pass
    
    @abstractmethod
    def log_error(self, message: str, exception: Optional[Exception] = None, **kwargs: Any) -> None:
        """记录错误日志"""
        pass
    
    @abstractmethod
    def log_debug(self, message: str, **kwargs: Any) -> None:
        """记录调试日志"""
        pass


class IUIService(IService, ABC):
    """
    UI服务接口
    
    提供UI相关的业务逻辑支持，如缩放管理、主题管理等。
    """
    
    @abstractmethod
    def get_scale_factor(self) -> float:
        """
        获取当前缩放比例
        
        Returns:
            float: 缩放比例 (1.0 = 100%)
        """
        pass
    
    @abstractmethod
    def set_scale_factor(self, factor: float) -> None:
        """
        设置缩放比例
        
        Args:
            factor: 缩放比例
        """
        pass
    
    @abstractmethod
    def calculate_scale_from_screen(self) -> float:
        """
        根据屏幕分辨率自动计算缩放比例
        
        Returns:
            float: 计算后的缩放比例
        """
        pass
