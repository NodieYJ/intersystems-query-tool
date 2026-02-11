#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
功能完整的桌面窗体应用程序
支持窗口控制、尺寸调整、滚动条功能和界面交互
"""

import sys
import os
from datetime import datetime

# 添加当前目录到Python路径，确保能够找到app模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Qt平台插件路径
# 查找PySide2的plugins目录
import PySide2
pyside2_dir = os.path.dirname(PySide2.__file__)
qt_plugin_path = os.path.join(pyside2_dir, 'plugins')
if os.path.exists(qt_plugin_path):
    os.environ['QT_PLUGIN_PATH'] = qt_plugin_path
    print(f"设置QT_PLUGIN_PATH为: {qt_plugin_path}")
else:
    print(f"未找到Qt插件目录: {qt_plugin_path}")

from PySide2.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QMessageBox
)
from PySide2.QtCore import Qt

# 导入自定义模块
from app.windows.main_window import MainWindow

# 配置日志记录
import logging
from logging.handlers import RotatingFileHandler

# 确保日志目录存在 - 存储在src文件夹中的log文件夹
project_root = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(project_root, "src")
log_dir = os.path.join(src_dir, "log")
os.makedirs(log_dir, exist_ok=True)

# 配置日志
log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")
handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# 获取根日志记录器
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

# 记录程序启动
logger.info(f"程序启动，当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logger.info(f"Python版本: {sys.version}")
logger.info(f"PySide2版本: {PySide2.__version__}")
logger.info(f"QT_PLUGIN_PATH: {os.environ.get('QT_PLUGIN_PATH', '未设置')}")
logger.info(f"当前工作目录: {os.getcwd()}")
logger.info(f"程序路径: {os.path.abspath(__file__)}")

def main():
    """主函数"""
    logger.info("开始执行主函数")
    try:
        # 创建应用程序
        logger.info("创建QApplication实例")
        app = QApplication(sys.argv)
        logger.info(f"QApplication实例创建成功，参数: {sys.argv}")
        
        # 记录应用程序启动
        logger.info("应用程序启动")
        
        # 创建主窗口
        logger.info("创建主窗口实例")
        window = MainWindow()
        logger.info("主窗口实例创建成功")
        
        # 显示窗口
        logger.info("显示主窗口")
        window.show()
        logger.info("主窗口显示成功")
        
        # 运行应用程序
        logger.info("启动应用程序事件循环")
        exit_code = app.exec_()
        logger.info(f"应用程序事件循环结束，退出代码: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        error_msg = f"应用程序启动失败: {str(e)}"
        print(error_msg)
        logger.error(error_msg, exc_info=True)
        import traceback
        traceback.print_exc()
        QMessageBox.critical(None, "错误", error_msg)
        sys.exit(1)

if __name__ == "__main__":
    logger.info("程序入口点: __main__")
    try:
        main()
    except Exception as e:
        error_msg = f"程序执行失败: {str(e)}"
        print(error_msg)
        logger.error(error_msg, exc_info=True)
        import traceback
        traceback.print_exc()
        QMessageBox.critical(None, "错误", error_msg)
        sys.exit(1)