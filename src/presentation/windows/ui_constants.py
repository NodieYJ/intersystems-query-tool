#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI常量定义模块

集中定义所有UI相关的常量，避免在多个模块中重复定义
"""

# 颜色系统 - UI/UX Pro Max 设计系统
COLORS = {
    'primary': '#2563EB',
    'primary_hover': '#1D4ED8',
    'primary_light': '#DBEAFE',
    'secondary': '#3B82F6',
    'success': '#10B981',
    'warning': '#F59E0B',
    'error': '#EF4444',
    'info': '#3B82F6',
    'background': '#F8FAFC',
    'surface': '#FFFFFF',
    'border': '#E2E8F0',
    'divider': '#F1F5F9',
    'text_primary': '#1E293B',
    'text_secondary': '#64748B',
    'text_disabled': '#94A3B8',
    'text_inverse': '#FFFFFF',
}

# 间距系统（基础单位：8px）
SPACING = {
    'xs': 4,
    'sm': 8,
    'md': 16,
    'lg': 24,
    'xl': 32,
    'xxl': 48,
}

# 字体大小
FONT_SIZES = {
    'xs': 12,
    'sm': 14,
    'md': 16,
    'lg': 18,
    'xl': 20,
    'xxl': 24,
    'title': 32,
}

# 圆角大小
BORDER_RADIUS = {
    'sm': 4,
    'md': 8,
    'lg': 12,
    'xl': 16,
    'full': 9999,
}

# 阴影样式
SHADOWS = {
    'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
    'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
}

# 侧边栏宽度
SIDEBAR_WIDTH = 240

# 头部高度
HEADER_HEIGHT = 64

# 默认窗口尺寸
DEFAULT_WINDOW_SIZE = (1280, 800)

# 最小窗口尺寸
MIN_WINDOW_SIZE = (1024, 600)
