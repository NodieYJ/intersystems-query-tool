#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据分析服务模块

提供数据加载、统计分析、图表生成等功能
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class DataAnalysisService:
    """
    数据分析服务
    
    提供数据加载、统计分析、图表数据准备等功能
    """
    
    def __init__(self):
        """初始化数据分析服务"""
        self.dataframe: Optional[pd.DataFrame] = None
        self.statistics: Optional[Dict[str, Any]] = None
        logger.info("数据分析服务初始化完成")
    
    def load_from_dataframe(self, df: pd.DataFrame) -> bool:
        """
        从DataFrame加载数据
        
        Args:
            df: pandas DataFrame
        
        Returns:
            是否加载成功
        """
        try:
            if df is None or df.empty:
                logger.warning("加载的DataFrame为空")
                return False
            
            self.dataframe = df.copy()
            self.statistics = None  # 重置统计信息
            logger.info(f"从DataFrame加载数据成功，行数: {len(df)}, 列数: {len(df.columns)}")
            return True
        except Exception as e:
            logger.error(f"从DataFrame加载数据失败: {str(e)}")
            return False
    
    def load_from_dict_list(self, data: List[Dict[str, Any]]) -> bool:
        """
        从字典列表加载数据
        
        Args:
            data: 字典列表
        
        Returns:
            是否加载成功
        """
        try:
            if not data:
                logger.warning("加载的数据为空")
                return False
            
            self.dataframe = pd.DataFrame(data)
            self.statistics = None
            logger.info(f"从字典列表加载数据成功，行数: {len(self.dataframe)}")
            return True
        except Exception as e:
            logger.error(f"从字典列表加载数据失败: {str(e)}")
            return False
    
    def load_from_file(self, file_path: str) -> bool:
        """
        从文件加载数据
        
        Args:
            file_path: 文件路径
        
        Returns:
            是否加载成功
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                logger.error(f"文件不存在: {file_path}")
                return False
            
            # 根据扩展名选择读取方式
            suffix = path.suffix.lower()
            
            if suffix == '.csv':
                self.dataframe = pd.read_csv(file_path, encoding='utf-8')
            elif suffix in ['.xls', '.xlsx']:
                self.dataframe = pd.read_excel(file_path)
            elif suffix == '.txt':
                # 尝试用不同分隔符读取
                try:
                    self.dataframe = pd.read_csv(file_path, sep='\t', encoding='utf-8')
                except (pd.errors.ParserError, pd.errors.EmptyDataError) as e:
                    logger.warning(f"Tab分隔解析失败，尝试逗号分隔: {e}")
                    try:
                        self.dataframe = pd.read_csv(file_path, sep=',', encoding='utf-8')
                    except (pd.errors.ParserError, pd.errors.EmptyDataError) as e2:
                        logger.error(f"CSV解析失败: {e2}")
                        return False
                except Exception as e:
                    logger.error(f"读取TXT文件时发生未知错误: {e}")
                    return False
            else:
                logger.error(f"不支持的文件格式: {suffix}")
                return False
            
            self.statistics = None
            logger.info(f"从文件加载数据成功: {file_path}, 行数: {len(self.dataframe)}")
            return True
            
        except Exception as e:
            logger.error(f"从文件加载数据失败: {str(e)}")
            return False
    
    def get_data_preview(self, n_rows: int = 100) -> Dict[str, Any]:
        """
        获取数据预览
        
        Args:
            n_rows: 预览行数
        
        Returns:
            包含预览数据的字典
        """
        if self.dataframe is None:
            return {'error': '没有加载数据'}
        
        try:
            preview_df = self.dataframe.head(n_rows)
            
            return {
                'columns': list(self.dataframe.columns),
                'dtypes': {col: str(dtype) for col, dtype in self.dataframe.dtypes.items()},
                'total_rows': len(self.dataframe),
                'total_columns': len(self.dataframe.columns),
                'preview_rows': len(preview_df),
                'data': preview_df.to_dict('records')
            }
        except Exception as e:
            logger.error(f"获取数据预览失败: {str(e)}")
            return {'error': str(e)}
    
    def calculate_statistics(self) -> Dict[str, Any]:
        """
        计算基础统计信息
        
        Returns:
            统计信息字典
        """
        if self.dataframe is None:
            return {'error': '没有加载数据'}
        
        try:
            stats = {}
            
            # 基本信息
            stats['total_rows'] = len(self.dataframe)
            stats['total_columns'] = len(self.dataframe.columns)
            stats['columns'] = list(self.dataframe.columns)
            
            # 数值型列的统计
            numeric_columns = self.dataframe.select_dtypes(include=[np.number]).columns.tolist()
            stats['numeric_columns'] = numeric_columns
            
            if numeric_columns:
                numeric_stats = []
                for col in numeric_columns:
                    col_data = self.dataframe[col]
                    col_stats = {
                        'column': col,
                        'count': int(col_data.count()),
                        'mean': float(col_data.mean()),
                        'std': float(col_data.std()),
                        'min': float(col_data.min()),
                        '25%': float(col_data.quantile(0.25)),
                        '50%': float(col_data.quantile(0.50)),
                        '75%': float(col_data.quantile(0.75)),
                        'max': float(col_data.max())
                    }
                    numeric_stats.append(col_stats)
                
                stats['numeric_statistics'] = numeric_stats
            
            # 分类型列的统计
            categorical_columns = self.dataframe.select_dtypes(include=['object']).columns.tolist()
            stats['categorical_columns'] = categorical_columns
            
            if categorical_columns:
                categorical_stats = []
                for col in categorical_columns:
                    col_data = self.dataframe[col]
                    col_stats = {
                        'column': col,
                        'count': int(col_data.count()),
                        'unique': int(col_data.nunique()),
                        'top': str(col_data.mode().iloc[0]) if not col_data.mode().empty else '',
                        'freq': int(col_data.value_counts().iloc[0]) if not col_data.value_counts().empty else 0
                    }
                    categorical_stats.append(col_stats)
                
                stats['categorical_statistics'] = categorical_stats
            
            # 缺失值统计
            missing_stats = []
            for col in self.dataframe.columns:
                missing_count = self.dataframe[col].isnull().sum()
                if missing_count > 0:
                    missing_stats.append({
                        'column': col,
                        'missing_count': int(missing_count),
                        'missing_percent': float(missing_count / len(self.dataframe) * 100)
                    })
            
            stats['missing_values'] = missing_stats
            
            self.statistics = stats
            logger.info("统计计算完成")
            return stats
            
        except Exception as e:
            logger.error(f"计算统计信息失败: {str(e)}")
            return {'error': str(e)}
    
    def get_column_data(self, column: str) -> Optional[List[Any]]:
        """
        获取指定列的数据
        
        Args:
            column: 列名
        
        Returns:
            列数据列表
        """
        if self.dataframe is None or column not in self.dataframe.columns:
            return None
        
        return self.dataframe[column].tolist()
    
    def get_chart_data(self, x_column: str, y_column: Optional[str] = None) -> Dict[str, Any]:
        """
        获取图表数据
        
        Args:
            x_column: X轴列名
            y_column: Y轴列名（可选）
        
        Returns:
            图表数据字典
        """
        if self.dataframe is None:
            return {'error': '没有加载数据'}
        
        try:
            if x_column not in self.dataframe.columns:
                return {'error': f'列不存在: {x_column}'}
            
            chart_data = {
                'x_column': x_column,
                'x_data': self.dataframe[x_column].tolist(),
                'y_column': y_column
            }
            
            if y_column:
                if y_column not in self.dataframe.columns:
                    return {'error': f'列不存在: {y_column}'}
                chart_data['y_data'] = self.dataframe[y_column].tolist()
            else:
                # 如果没有Y轴列，统计X轴列的值分布
                value_counts = self.dataframe[x_column].value_counts()
                chart_data['y_data'] = value_counts.tolist()
                chart_data['x_data'] = value_counts.index.tolist()
            
            return chart_data
            
        except Exception as e:
            logger.error(f"获取图表数据失败: {str(e)}")
            return {'error': str(e)}
    
    def get_dataframe(self) -> Optional[pd.DataFrame]:
        """
        获取当前DataFrame
        
        Returns:
            DataFrame或None
        """
        return self.dataframe
    
    def clear(self):
        """清除数据"""
        self.dataframe = None
        self.statistics = None
        logger.info("数据已清除")


# 单例模式
_analysis_service: Optional[DataAnalysisService] = None


def get_data_analysis_service() -> DataAnalysisService:
    """
    获取数据分析服务实例（单例）
    
    Returns:
        DataAnalysisService实例
    """
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = DataAnalysisService()
    return _analysis_service


def reset_data_analysis_service():
    """重置数据分析服务实例"""
    global _analysis_service
    _analysis_service = None
