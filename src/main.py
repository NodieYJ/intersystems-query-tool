#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
功能完整的桌面窗体应用程序
支持窗口控制、尺寸调整、滚动条功能和界面交互
基于 UI/UX Pro Max 设计系统，支持动态分辨率缩放
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from typing import Optional

# 添加项目根目录到Python路径，确保能够找到src模块
sys.path.insert(0, os.path.abspath('.'))

# 设置Qt平台插件路径
# 查找PySide2的plugins目录
import PySide2

pyside2_dir = os.path.dirname(PySide2.__file__)
qt_plugin_path = os.path.join(pyside2_dir, "plugins")
if os.path.exists(qt_plugin_path):
    os.environ["QT_PLUGIN_PATH"] = qt_plugin_path
    print(f"设置QT_PLUGIN_PATH为: {qt_plugin_path}")
else:
    print(f"未找到Qt插件目录: {qt_plugin_path}")

# 导入依赖注入模块（用于服务解析）
try:
    from src.infrastructure.di import resolve
    DI_AVAILABLE = True
except ImportError:
    DI_AVAILABLE = False
    resolve = None

from PySide2.QtCore import Qt
from PySide2.QtGui import QScreen, QFont
from PySide2.QtWidgets import QApplication, QMessageBox

from src.infrastructure.di.service_registration import (
    initialize_container,
    IConfig,
    ILogger,
    IScalingManager,
)
from src.infrastructure.logging.logger import setup_logger
from src.infrastructure.utils.scaling_manager import get_scaling_manager
# 导入自定义模块
from src.presentation.windows.main_window import MainWindow

# 配置日志记录
logger = setup_logger()

# 初始化依赖注入容器（在应用程序启动时配置所有服务）
try:
    container = initialize_container()
    logger.info("依赖注入容器初始化完成")
except Exception as e:
    logger.warning(f"依赖注入容器初始化失败（可能缺少某些依赖）: {e}")
    container = None


class Application:
  """
  应用程序类

  封装应用程序初始化和生命周期管理
  """

  def __init__(self, config_file: Optional[str] = None):
    """
    初始化应用程序

    Args:
        config_file: 配置文件路径
    """
    self._config_file = config_file
    self._app: Optional[QApplication] = None
    self._main_window: Optional[MainWindow] = None
    self._is_initialized = False
    self._exit_code = 0

  def initialize(self) -> bool:
    """
    初始化应用程序

    Returns:
        bool: 初始化是否成功
    """
    try:
      # 1. 设置日志
      self._setup_logging()

      # 2. 加载配置
      self._load_config()

      # 3. 初始化服务
      self._initialize_services()

      # 4. 创建 Qt 应用
      self._create_application()

      # 5. 创建主窗口
      self._create_main_window()

      self._is_initialized = True
      return True

    except Exception as e:
      logging.error(f"Application initialization failed: {str(e)}", exc_info=True)
      return False

  def _setup_logging(self) -> None:
    """
    设置日志配置
    """
    logger.info("Logging initialized")

  def _load_config(self) -> None:
    """
    加载配置文件
    """
    config_file = self._config_file or "config.json"
    logger.info(f"Configuration loaded from: {config_file}")

  def _initialize_services(self) -> None:
    """
    初始化服务
    """
    logger.info("Services initialized")

  def _create_application(self) -> None:
    """
    创建 Qt 应用程序实例
    """
    # 设置 Qt 属性
    self._app = QApplication(sys.argv)
    self._app.setApplicationName("PySide2 Desktop App")
    self._app.setApplicationVersion("1.0.0")
    self._app.setAttribute(Qt.AA_EnableHighDpiScaling, True)

    # 设置全局样式
    self._app.setStyleSheet("""
      QMainWindow {
        background-color: #f5f5f5;
      }
      QWidget {
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 14px;
      }
    """)

    logger.info("Qt application created")

  def _create_main_window(self) -> None:
    """
    创建主窗口
    """
    self._main_window = MainWindow()
    self._main_window.setWindowTitle("PySide2 Desktop App")
    self._main_window.resize(1024, 768)

    logger.info("Main window created")

  def run(self) -> int:
    """
    运行应用程序

    Returns:
        int: 退出代码
    """
    if not self._is_initialized:
      if not self.initialize():
        return 1

    # 显示主窗口
    if self._main_window:
      self._main_window.show()

    logger.info("Application started")
    
    if self._app:
      self._exit_code = self._app.exec_()
    else:
      self._exit_code = 1
    
    logger.info(f"Application exited with code: {self._exit_code}")
    return self._exit_code

  def get_main_window(self) -> Optional[MainWindow]:
    """
    获取主窗口实例

    Returns:
        MainWindow 或 None
    """
    return self._main_window


def handle_startup_error(error: Exception, error_type: str = "未知错误") -> None:
    """
    统一处理应用程序启动错误
    
    多级降级方案：
    1. QMessageBox (PySide2)
    2. tkinter (Python 标准库)
    3. 写入错误日志文件
    4. 控制台输出
    
    Args:
        error: 异常对象
        error_type: 错误类型描述
    """
    error_msg = f"{error_type}: {str(error)}"
    
    # 输出到控制台
    print("=" * 60)
    print(error_msg)
    print("=" * 60)
    
    # 记录到日志
    try:
        logger.error(error_msg, exc_info=True)
    except Exception as log_error:
        # 日志记录失败，输出到控制台
        print(f"[警告] 日志记录失败: {log_error}")
    
    # 尝试显示错误对话框（多级降级）
    dialog_shown = False
    
    # 方案1: QMessageBox (PySide2)
    if not dialog_shown:
        try:
            from PySide2.QtWidgets import QWidget, QMessageBox
            parent = QWidget()  # type: ignore
            QMessageBox.critical(parent, "启动错误", error_msg)
            dialog_shown = True
        except Exception:
            pass
    
    # 方案2: tkinter (Python 标准库)
    if not dialog_shown:
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
            messagebox.showerror("启动错误", error_msg)
            dialog_shown = True
        except Exception:
            pass
    
    # 方案3: 写入错误日志文件
    if not dialog_shown:
        try:
            error_file = os.path.expanduser("~/pywindows_error.log")
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(f"时间: {datetime.now()}\n")
                f.write(f"错误类型: {error_type}\n")
                f.write(f"错误信息: {str(error)}\n")
                f.write("\n详细错误信息:\n")
                import traceback
                f.write(traceback.format_exc())
            print(f"\n错误信息已写入: {error_file}")
        except Exception:
            pass
    
    # 最后方案: 控制台输出（如果对话框都失败了）
    if not dialog_shown:
        print("\n无法显示图形化错误对话框，请查看控制台输出或日志文件。")
    
    # 退出程序
    sys.exit(1)


def main() -> int:
  """主函数"""
  # 解析命令行参数
  parser = argparse.ArgumentParser(
    description="PySide2 Desktop Application"
  )
  parser.add_argument(
    "-c", "--config",
    help="Configuration file path",
    default="config.json"
  )
  parser.add_argument(
    "-v", "--verbose",
    help="Enable verbose logging",
    action="store_true"
  )

  args = parser.parse_args()

  # 定义异常类型到错误描述的映射
  EXCEPTION_TYPES = (ImportError, ValueError, RuntimeError, OSError)

  exception_handlers = {
    ImportError: ("导入模块失败",
                  "请检查依赖库是否已正确安装\n"
                  "运行: pip install -r requirements.txt"),
    ValueError: ("参数错误",
                 "配置参数不正确，请检查配置文件"),
    RuntimeError: ("运行时错误",
                   "应用程序运行时发生错误，请查看日志"),
    OSError: ("系统错误",
              "操作系统或文件系统错误"),
  }

  try:
    # 启用 Qt 自动高 DPI 缩放 - UI/UX Pro Max 规范
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # type: ignore
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)  # type: ignore

    # 创建应用程序实例
    app = QApplication(sys.argv)

    # 使用 ScalingManager 计算和应用缩放比例
    # 优先使用DI容器获取服务（如果可用），否则回退到直接获取
    if DI_AVAILABLE and container and container.is_registered(IScalingManager):
      scaling_manager = resolve(IScalingManager)
      logger.debug("通过DI容器获取缩放管理器")
    else:
      scaling_manager = get_scaling_manager()
      logger.debug("通过传统方式获取缩放管理器")

    scale_factor = scaling_manager.calculate_from_screen(app)

    # 设置全局字体，根据缩放比例调整
    # 使用跨平台字体栈，确保 Windows 7/10 兼容
    from src.infrastructure.config.constants import UIConfigDefaults
    base_font_size = 10
    font = QFont(UIConfigDefaults.FONT_FAMILY, int(base_font_size * scale_factor))  # type: ignore
    app.setFont(font)

    # 记录应用程序启动
    logger.info(f"应用程序启动 - 屏幕缩放比例: {scale_factor * 100:.0f}%")

    # 创建主窗口，传递缩放比例
    window = MainWindow(scale_factor=scale_factor)
    
    # 显示窗口（最大化）
    window.showMaximized()
    
    # 运行应用程序
    sys.exit(app.exec_())
    
  except EXCEPTION_TYPES as e:
    # 处理已知的特定异常类型
    exc_type = type(e)
    title, suggestion = exception_handlers[exc_type]
    error_msg = f"{title}: {str(e)}\n\n建议: {suggestion}"
    handle_startup_error(e, title)
    return 1
    
  except Exception as e:
    # 处理未知的其他异常
    error_msg = f"应用程序启动失败: {str(e)}"
    logger.critical(f"未预期的错误: {error_msg}", exc_info=True)
    handle_startup_error(e, "应用程序启动失败")
    return 1

  # 确保所有路径都有返回值
  return 0


if __name__ == "__main__":
    main()
