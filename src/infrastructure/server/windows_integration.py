#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Windows集成模块

提供Windows平台特有的集成功能：
- 系统托盘图标
- Windows服务封装
- 自启动配置
- 服务监控

依赖: PySide2, pywin32(可选，用于Windows服务)
"""

import logging
import os
import sys
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class ServerTrayIcon:
    """
    服务器系统托盘图标
    
    在Windows系统托盘中显示服务器状态，提供快速操作菜单。
    """
    
    def __init__(
        self,
        server_name: str = "QueryTool Server",
        on_show_status: Optional[Callable[[], None]] = None,
        on_start_server: Optional[Callable[[], None]] = None,
        on_stop_server: Optional[Callable[[], None]] = None,
        on_restart_server: Optional[Callable[[], None]] = None,
        on_exit: Optional[Callable[[], None]] = None
    ):
        self._server_name = server_name
        self._on_show_status = on_show_status
        self._on_start_server = on_start_server
        self._on_stop_server = on_stop_server
        self._on_restart_server = on_restart_server
        self._on_exit = on_exit
        
        self._tray_icon = None
        self._menu = None
        self._is_running = False
        self._server_status = "stopped"  # stopped, running, error
        
        logger.info("ServerTrayIcon initialized")
    
    def create_tray_icon(self) -> bool:
        """创建系统托盘图标"""
        try:
            from PySide2.QtWidgets import QSystemTrayIcon, QMenu, QAction
            from PySide2.QtGui import QIcon
            from PySide2.QtCore import Qt
            
            # 检查系统托盘是否可用
            if not QSystemTrayIcon.isSystemTrayAvailable():
                logger.warning("系统托盘不可用")
                return False
            
            # 创建托盘图标
            self._tray_icon = QSystemTrayIcon()
            self._tray_icon.setToolTip(f"{self._server_name}\nStatus: {self._server_status}")
            
            # 设置图标 (使用默认图标或自定义图标)
            icon = self._create_icon()
            self._tray_icon.setIcon(icon)
            
            # 创建菜单
            self._menu = QMenu()
            self._setup_menu()
            
            self._tray_icon.setContextMenu(self._menu)
            
            # 连接点击事件
            self._tray_icon.activated.connect(self._on_tray_activated)
            
            logger.info("系统托盘图标已创建")
            return True
            
        except ImportError:
            logger.warning("PySide2未安装，无法创建系统托盘图标")
            return False
        except Exception as e:
            logger.error(f"创建系统托盘图标失败: {e}")
            return False
    
    def _create_icon(self):
        """创建托盘图标"""
        from PySide2.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
        from PySide2.QtCore import Qt
        
        # 创建一个简单的圆形图标
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 根据状态选择颜色
        if self._server_status == "running":
            color = QColor(76, 175, 80)  # 绿色
        elif self._server_status == "error":
            color = QColor(244, 67, 54)  # 红色
        else:
            color = QColor(158, 158, 158)  # 灰色
        
        # 绘制圆形
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 56, 56)
        
        # 绘制文字
        painter.setPen(Qt.white)
        font = QFont("Arial", 24, QFont.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "S")
        
        painter.end()
        
        return QIcon(pixmap)
    
    def _setup_menu(self):
        """设置托盘菜单"""
        from PySide2.QtWidgets import QAction
        from PySide2.QtGui import QKeySequence
        
        # 显示状态
        action_status = QAction(f"Status: {self._server_status.upper()}", self._menu)
        action_status.setEnabled(False)
        self._menu.addAction(action_status)
        
        self._menu.addSeparator()
        
        # 显示详细信息
        action_show = QAction("Show Status", self._menu)
        action_show.triggered.connect(self._on_show_status_clicked)
        self._menu.addAction(action_show)
        
        self._menu.addSeparator()
        
        # 服务器控制
        action_start = QAction("Start Server", self._menu)
        action_start.triggered.connect(self._on_start_clicked)
        self._menu.addAction(action_start)
        
        action_stop = QAction("Stop Server", self._menu)
        action_stop.triggered.connect(self._on_stop_clicked)
        self._menu.addAction(action_stop)
        
        action_restart = QAction("Restart Server", self._menu)
        action_restart.triggered.connect(self._on_restart_clicked)
        self._menu.addAction(action_restart)
        
        self._menu.addSeparator()
        
        # 退出
        action_exit = QAction("Exit", self._menu)
        action_exit.setShortcut(QKeySequence("Ctrl+Q"))
        action_exit.triggered.connect(self._on_exit_clicked)
        self._menu.addAction(action_exit)
    
    def _on_tray_activated(self, reason):
        """托盘图标被激活"""
        from PySide2.QtWidgets import QSystemTrayIcon
        
        if reason == QSystemTrayIcon.DoubleClick:
            self._on_show_status_clicked()
    
    def _on_show_status_clicked(self):
        """显示状态被点击"""
        if self._on_show_status:
            self._on_show_status()
    
    def _on_start_clicked(self):
        """启动服务器被点击"""
        if self._on_start_server:
            self._on_start_server()
    
    def _on_stop_clicked(self):
        """停止服务器被点击"""
        if self._on_stop_server:
            self._on_stop_server()
    
    def _on_restart_clicked(self):
        """重启服务器被点击"""
        if self._on_restart_server:
            self._on_restart_server()
    
    def _on_exit_clicked(self):
        """退出被点击"""
        self.hide()
        if self._on_exit:
            self._on_exit()
    
    def show(self):
        """显示托盘图标"""
        if self._tray_icon:
            self._tray_icon.show()
            self._is_running = True
            logger.info("系统托盘图标已显示")
    
    def hide(self):
        """隐藏托盘图标"""
        if self._tray_icon:
            self._tray_icon.hide()
            self._is_running = False
            logger.info("系统托盘图标已隐藏")
    
    def update_status(self, status: str, message: Optional[str] = None):
        """
        更新服务器状态显示
        
        Args:
            status: 状态 (running, stopped, error)
            message: 附加消息
        """
        self._server_status = status
        
        if self._tray_icon:
            tooltip = f"{self._server_name}\nStatus: {status.upper()}"
            if message:
                tooltip += f"\n{message}"
            
            self._tray_icon.setToolTip(tooltip)
            
            # 更新图标
            icon = self._create_icon()
            self._tray_icon.setIcon(icon)
            
            # 可以显示气泡通知
            if status == "error":
                self._tray_icon.showMessage(
                    f"{self._server_name} Error",
                    message or "Server encountered an error",
                    self._tray_icon.Critical,
                    5000
                )
        
        logger.info(f"托盘状态更新: {status}")
    
    def show_notification(self, title: str, message: str, timeout: int = 5000):
        """显示通知消息"""
        if self._tray_icon:
            from PySide2.QtWidgets import QSystemTrayIcon
            self._tray_icon.showMessage(
                title,
                message,
                QSystemTrayIcon.Information,
                timeout
            )
    
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._is_running


class WindowsServiceBase(ABC):
    """
    Windows服务基类
    
    将服务器封装为Windows服务，支持通过服务管理器控制。
    
    使用示例:
        class MyServerService(WindowsServiceBase):
            _svc_name_ = "MyServer"
            _svc_display_name_ = "My Server Service"
            
            async def run(self):
                # 服务器主循环
                pass
    """
    
    _svc_name_ = "QueryToolServer"
    _svc_display_name_ = "QueryTool Server Service"
    _svc_description_ = "InterSystems Query Tool Server Service"
    
    def __init__(self, args):
        self._args = args
        self._running = False
        self._server = None
    
    @abstractmethod
    async def run(self):
        """
        服务主循环
        
        子类必须实现此方法。
        """
        pass
    
    @abstractmethod
    async def stop(self):
        """
        停止服务
        
        子类必须实现此方法。
        """
        pass
    
    def SvcStop(self):
        """Windows服务停止回调"""
        logger.info("收到服务停止信号")
        self._running = False
        # 运行停止逻辑
        try:
            import asyncio
            asyncio.run(self.stop())
        except Exception as e:
            logger.error(f"停止服务失败: {e}")
    
    def SvcDoRun(self):
        """Windows服务运行回调"""
        logger.info("服务启动")
        self._running = True
        
        try:
            import asyncio
            asyncio.run(self.run())
        except Exception as e:
            logger.error(f"服务运行错误: {e}")
    
    @classmethod
    def install(cls):
        """安装Windows服务"""
        try:
            import win32serviceutil
            win32serviceutil.HandleCommandLine(cls)
            logger.info(f"服务 {cls._svc_name_} 已安装")
        except ImportError:
            logger.error("pywin32未安装，无法安装Windows服务")
        except Exception as e:
            logger.error(f"安装服务失败: {e}")
    
    @classmethod
    def start_service(cls):
        """启动Windows服务"""
        try:
            import win32serviceutil
            win32serviceutil.StartService(cls._svc_name_)
            logger.info(f"服务 {cls._svc_name_} 已启动")
        except ImportError:
            logger.error("pywin32未安装")
        except Exception as e:
            logger.error(f"启动服务失败: {e}")
    
    @classmethod
    def stop_service(cls):
        """停止Windows服务"""
        try:
            import win32serviceutil
            win32serviceutil.StopService(cls._svc_name_)
            logger.info(f"服务 {cls._svc_name_} 已停止")
        except ImportError:
            logger.error("pywin32未安装")
        except Exception as e:
            logger.error(f"停止服务失败: {e}")


class StartupManager:
    """
    自启动管理器
    
    管理Windows开机自启动配置。
    """
    
    REGISTRY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    def __init__(self, app_name: str = "QueryToolServer"):
        self._app_name = app_name
    
    def enable_startup(self, executable_path: Optional[str] = None) -> bool:
        """
        启用开机自启动
        
        Args:
            executable_path: 可执行文件路径，默认使用当前程序
            
        Returns:
            bool: 是否成功
        """
        try:
            import winreg
            
            if executable_path is None:
                executable_path = sys.executable
                if getattr(sys, 'frozen', False):
                    # PyInstaller打包的程序
                    executable_path = sys.executable
                else:
                    # Python脚本
                    executable_path = f'"{executable_path}" "{os.path.abspath(sys.argv[0])}"'
            
            # 打开注册表
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REGISTRY_PATH,
                0,
                winreg.KEY_SET_VALUE
            )
            
            # 写入启动项
            winreg.SetValueEx(key, self._app_name, 0, winreg.REG_SZ, executable_path)
            winreg.CloseKey(key)
            
            logger.info(f"已启用开机自启动: {executable_path}")
            return True
            
        except ImportError:
            logger.error("无法导入winreg模块")
            return False
        except Exception as e:
            logger.error(f"启用自启动失败: {e}")
            return False
    
    def disable_startup(self) -> bool:
        """禁用开机自启动"""
        try:
            import winreg
            
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REGISTRY_PATH,
                0,
                winreg.KEY_SET_VALUE
            )
            
            try:
                winreg.DeleteValue(key, self._app_name)
                logger.info("已禁用开机自启动")
            except WindowsError:
                # 键不存在，说明原本就没有启用
                pass
            
            winreg.CloseKey(key)
            return True
            
        except Exception as e:
            logger.error(f"禁用自启动失败: {e}")
            return False
    
    def is_startup_enabled(self) -> bool:
        """检查是否已启用开机自启动"""
        try:
            import winreg
            
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REGISTRY_PATH,
                0,
                winreg.KEY_READ
            )
            
            try:
                winreg.QueryValueEx(key, self._app_name)
                return True
            except WindowsError:
                return False
            finally:
                winreg.CloseKey(key)
                
        except Exception as e:
            logger.error(f"检查自启动状态失败: {e}")
            return False


class ServiceMonitor:
    """
    服务监控器
    
    监控服务器健康状态，提供自动重启等功能。
    """
    
    def __init__(
        self,
        check_interval: float = 30.0,
        max_failures: int = 3,
        auto_restart: bool = True
    ):
        self._check_interval = check_interval
        self._max_failures = max_failures
        self._auto_restart = auto_restart
        
        self._failure_count = 0
        self._is_monitoring = False
        self._monitor_task = None
        self._health_check_fn: Optional[Callable[[], bool]] = None
        self._restart_fn: Optional[Callable[[], None]] = None
    
    def set_health_check(self, fn: Callable[[], bool]):
        """设置健康检查函数"""
        self._health_check_fn = fn
    
    def set_restart_handler(self, fn: Callable[[], None]):
        """设置重启处理函数"""
        self._restart_fn = fn
    
    async def start_monitoring(self):
        """开始监控"""
        if self._is_monitoring:
            return
        
        self._is_monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("服务监控已启动")
    
    async def stop_monitoring(self):
        """停止监控"""
        self._is_monitoring = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("服务监控已停止")
    
    async def _monitor_loop(self):
        """监控循环"""
        import asyncio
        
        while self._is_monitoring:
            try:
                await asyncio.sleep(self._check_interval)
                
                if not self._health_check_fn:
                    continue
                
                # 执行健康检查
                is_healthy = self._health_check_fn()
                
                if is_healthy:
                    if self._failure_count > 0:
                        logger.info("服务恢复健康")
                    self._failure_count = 0
                else:
                    self._failure_count += 1
                    logger.warning(f"健康检查失败 ({self._failure_count}/{self._max_failures})")
                    
                    if self._failure_count >= self._max_failures:
                        logger.error("服务健康检查连续失败，需要重启")
                        
                        if self._auto_restart and self._restart_fn:
                            logger.info("自动重启服务...")
                            try:
                                self._restart_fn()
                                self._failure_count = 0
                            except Exception as e:
                                logger.error(f"自动重启失败: {e}")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        return {
            'is_monitoring': self._is_monitoring,
            'failure_count': self._failure_count,
            'max_failures': self._max_failures,
            'auto_restart': self._auto_restart,
            'check_interval': self._check_interval
        }


# 兼容性导入
import asyncio

def create_tray_icon(
    server_name: str = "QueryTool Server",
    **kwargs
) -> Optional[ServerTrayIcon]:
    """创建系统托盘图标"""
    try:
        tray = ServerTrayIcon(server_name=server_name, **kwargs)
        if tray.create_tray_icon():
            return tray
        return None
    except Exception as e:
        logger.error(f"创建托盘图标失败: {e}")
        return None


def create_startup_manager(app_name: str = "QueryToolServer") -> StartupManager:
    """创建自启动管理器"""
    return StartupManager(app_name=app_name)


def create_service_monitor(
    check_interval: float = 30.0,
    **kwargs
) -> ServiceMonitor:
    """创建服务监控器"""
    return ServiceMonitor(check_interval=check_interval, **kwargs)
