#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文件传输服务模块

提供大文件传输功能：
- 分块传输 (64KB chunks)
- 断点续传
- 校验和验证 (MD5/SHA256)
- 传输队列管理
- 病毒扫描集成接口
- 存储管理

支持GB级大文件稳定传输。
"""

import asyncio
import hashlib
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class TransferStatus(Enum):
    """传输状态"""
    PENDING = "pending"
    INITIALIZING = "initializing"
    TRANSFERRING = "transferring"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    VERIFYING = "verifying"


@dataclass
class TransferInfo:
    """传输任务信息"""
    transfer_id: str
    file_name: str
    file_path: str
    file_size: int
    chunk_size: int = 65536  # 64KB
    total_chunks: int = 0
    completed_chunks: Set[int] = field(default_factory=set)
    status: TransferStatus = TransferStatus.PENDING
    checksum: Optional[str] = None
    checksum_algorithm: str = "sha256"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.total_chunks == 0 and self.file_size > 0:
            self.total_chunks = (self.file_size + self.chunk_size - 1) // self.chunk_size
    
    @property
    def progress(self) -> float:
        """计算传输进度"""
        if self.total_chunks == 0:
            return 0.0
        return len(self.completed_chunks) / self.total_chunks
    
    @property
    def bytes_transferred(self) -> int:
        """已传输字节数"""
        if self.total_chunks == 0:
            return 0
        
        # 完整数据块
        complete_chunks = len(self.completed_chunks)
        if complete_chunks == self.total_chunks:
            return self.file_size
        
        # 除最后一个块外的所有完整块
        if complete_chunks == self.total_chunks - 1:
            last_chunk_size = self.file_size % self.chunk_size
            if last_chunk_size == 0:
                last_chunk_size = self.chunk_size
            return (complete_chunks - 1) * self.chunk_size + last_chunk_size
        
        return complete_chunks * self.chunk_size
    
    @property
    def is_complete(self) -> bool:
        """检查是否传输完成"""
        return len(self.completed_chunks) == self.total_chunks
    
    def add_chunk(self, chunk_index: int) -> None:
        """标记数据块已完成"""
        self.completed_chunks.add(chunk_index)
        self.updated_at = time.time()
        
        if self.is_complete:
            self.status = TransferStatus.COMPLETED
            self.completed_at = time.time()
    
    def get_missing_chunks(self, max_count: int = 100) -> List[int]:
        """获取缺失的数据块索引"""
        all_chunks = set(range(self.total_chunks))
        missing = sorted(list(all_chunks - self.completed_chunks))
        return missing[:max_count]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'transfer_id': self.transfer_id,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'chunk_size': self.chunk_size,
            'total_chunks': self.total_chunks,
            'completed_chunks': len(self.completed_chunks),
            'progress': self.progress,
            'status': self.status.value,
            'checksum': self.checksum,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'error_message': self.error_message,
        }


class StorageManager:
    """
    存储管理器
    
    管理上传文件的存储：
    - 临时文件管理
    - 文件路径组织
    - 存储空间检查
    - 文件清理
    """
    
    def __init__(
        self,
        base_path: str = "./uploads",
        temp_path: str = "./temp",
        max_storage_size: int = 100 * 1024 * 1024 * 1024,  # 100GB
        max_file_size: int = 10 * 1024 * 1024 * 1024  # 10GB
    ):
        self._base_path = Path(base_path)
        self._temp_path = Path(temp_path)
        self._max_storage_size = max_storage_size
        self._max_file_size = max_file_size
        
        # 确保目录存在
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._temp_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"StorageManager initialized: base={base_path}, temp={temp_path}")
    
    def get_temp_path(self, transfer_id: str) -> Path:
        """获取临时文件路径"""
        return self._temp_path / f"{transfer_id}.tmp"
    
    def get_final_path(self, file_name: str) -> Path:
        """获取最终存储路径"""
        # 使用日期组织文件
        date_str = time.strftime("%Y%m%d")
        date_path = self._base_path / date_str
        date_path.mkdir(parents=True, exist_ok=True)
        
        # 生成唯一文件名
        unique_name = f"{uuid.uuid4().hex[:8]}_{file_name}"
        return date_path / unique_name
    
    def get_chunk_file_path(self, transfer_id: str, chunk_index: int) -> Path:
        """获取数据块文件路径"""
        chunk_dir = self._temp_path / transfer_id
        chunk_dir.mkdir(parents=True, exist_ok=True)
        return chunk_dir / f"chunk_{chunk_index:08d}"
    
    def check_storage_space(self, required_bytes: int = 0) -> bool:
        """检查存储空间是否充足"""
        try:
            import shutil
            stat = shutil.disk_usage(self._base_path)
            available = stat.free
            
            # 保留10%的余量
            min_free = self._max_storage_size * 0.1
            return available >= required_bytes + min_free
            
        except Exception as e:
            logger.error(f"检查存储空间失败: {e}")
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计"""
        try:
            import shutil
            stat = shutil.disk_usage(self._base_path)
            
            # 计算已用空间
            total_size = sum(
                f.stat().st_size for f in self._base_path.rglob('*') if f.is_file()
            )
            
            return {
                'total_space': stat.total,
                'used_space': total_size,
                'free_space': stat.free,
                'usage_percent': (stat.total - stat.free) / stat.total * 100,
                'max_storage': self._max_storage_size,
                'file_count': sum(1 for _ in self._base_path.rglob('*') if _.is_file())
            }
            
        except Exception as e:
            logger.error(f"获取存储统计失败: {e}")
            return {}
    
    async def write_chunk(
        self,
        transfer_id: str,
        chunk_index: int,
        data: bytes
    ) -> bool:
        """写入数据块"""
        try:
            chunk_path = self.get_chunk_file_path(transfer_id, chunk_index)
            
            # 异步写入
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._write_file, chunk_path, data)
            
            return True
            
        except Exception as e:
            logger.error(f"写入数据块失败: {transfer_id}/{chunk_index} - {e}")
            return False
    
    def _write_file(self, path: Path, data: bytes) -> None:
        """同步写入文件"""
        with open(path, 'wb') as f:
            f.write(data)
    
    async def read_chunk(
        self,
        transfer_id: str,
        chunk_index: int
    ) -> Optional[bytes]:
        """读取数据块"""
        try:
            chunk_path = self.get_chunk_file_path(transfer_id, chunk_index)
            
            if not chunk_path.exists():
                return None
            
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._read_file, chunk_path)
            
        except Exception as e:
            logger.error(f"读取数据块失败: {transfer_id}/{chunk_index} - {e}")
            return None
    
    def _read_file(self, path: Path) -> bytes:
        """同步读取文件"""
        with open(path, 'rb') as f:
            return f.read()
    
    async def assemble_file(self, transfer_info: TransferInfo) -> Optional[Path]:
        """
        组装完整文件
        
        将所有数据块合并为完整文件。
        """
        try:
            transfer_id = transfer_info.transfer_id
            final_path = self.get_final_path(transfer_info.file_name)
            
            logger.info(f"开始组装文件: {transfer_id} -> {final_path}")
            
            loop = asyncio.get_event_loop()
            
            def do_assemble():
                with open(final_path, 'wb') as outfile:
                    for i in range(transfer_info.total_chunks):
                        chunk_path = self.get_chunk_file_path(transfer_id, i)
                        
                        if not chunk_path.exists():
                            raise FileNotFoundError(f"Missing chunk: {i}")
                        
                        with open(chunk_path, 'rb') as infile:
                            outfile.write(infile.read())
                        
                        # 删除已合并的数据块
                        chunk_path.unlink()
                
                # 删除数据块目录
                chunk_dir = self._temp_path / transfer_id
                if chunk_dir.exists():
                    chunk_dir.rmdir()
                
                return final_path
            
            final_path = await loop.run_in_executor(None, do_assemble)
            
            logger.info(f"文件组装完成: {final_path}")
            return final_path
            
        except Exception as e:
            logger.error(f"组装文件失败: {transfer_info.transfer_id} - {e}")
            return None
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """清理临时文件"""
        count = 0
        cutoff = time.time() - (max_age_hours * 3600)
        
        try:
            for item in self._temp_path.iterdir():
                try:
                    if item.is_file() and item.stat().st_mtime < cutoff:
                        item.unlink()
                        count += 1
                    elif item.is_dir():
                        # 检查目录内文件
                        dir_modified = max(
                            (f.stat().st_mtime for f in item.rglob('*') if f.is_file()),
                            default=0
                        )
                        if dir_modified < cutoff:
                            import shutil
                            shutil.rmtree(item)
                            count += 1
                except Exception as e:
                    logger.warning(f"清理失败: {item} - {e}")
                    
        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")
        
        if count > 0:
            logger.info(f"清理了 {count} 个临时文件/目录")
        
        return count


class ChecksumVerifier:
    """
    校验和验证器
    
    支持MD5和SHA256校验。
    """
    
    @staticmethod
    def calculate_checksum(
        file_path: Path,
        algorithm: str = "sha256"
    ) -> Optional[str]:
        """计算文件校验和"""
        try:
            hasher = hashlib.new(algorithm)
            
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):  # 8KB blocks
                    hasher.update(chunk)
            
            return hasher.hexdigest()
            
        except Exception as e:
            logger.error(f"计算校验和失败: {file_path} - {e}")
            return None
    
    @staticmethod
    def verify_checksum(
        file_path: Path,
        expected_checksum: str,
        algorithm: str = "sha256"
    ) -> bool:
        """验证文件校验和"""
        actual = ChecksumVerifier.calculate_checksum(file_path, algorithm)
        
        if actual is None:
            return False
        
        # 支持大小写不敏感比较
        return actual.lower() == expected_checksum.lower()
    
    @staticmethod
    def calculate_checksum_async(
        file_path: Path,
        algorithm: str = "sha256"
    ) -> asyncio.Future:
        """异步计算校验和"""
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(
            None,
            ChecksumVerifier.calculate_checksum,
            file_path,
            algorithm
        )


class TransferQueue:
    """
    传输队列管理器
    
    管理文件传输任务队列：
    - 任务排队
    - 优先级管理
    - 并发控制
    """
    
    def __init__(
        self,
        max_concurrent: int = 5,
        max_queue_size: int = 100
    ):
        self._max_concurrent = max_concurrent
        self._max_queue_size = max_queue_size
        
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._active_transfers: Dict[str, TransferInfo] = {}
        self._completed_transfers: Dict[str, TransferInfo] = {}
        
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._running = False
        
        logger.info(f"TransferQueue initialized: max_concurrent={max_concurrent}")
    
    async def start(self) -> None:
        """启动队列处理"""
        self._running = True
        
        # 启动处理任务
        for _ in range(self._max_concurrent):
            asyncio.create_task(self._process_loop())
        
        logger.info("TransferQueue started")
    
    async def stop(self) -> None:
        """停止队列处理"""
        self._running = False
        
        # 等待活跃传输完成
        if self._active_transfers:
            logger.info(f"等待 {len(self._active_transfers)} 个活跃传输完成...")
            # 给传输一些时间完成
            await asyncio.sleep(2)
        
        logger.info("TransferQueue stopped")
    
    async def _process_loop(self) -> None:
        """处理循环"""
        while self._running:
            try:
                transfer_info = await self._queue.get()
                
                async with self._semaphore:
                    self._active_transfers[transfer_info.transfer_id] = transfer_info
                    
                    try:
                        await self._process_transfer(transfer_info)
                    finally:
                        if transfer_info.transfer_id in self._active_transfers:
                            del self._active_transfers[transfer_info.transfer_id]
                
                self._queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"处理传输任务失败: {e}")
    
    async def _process_transfer(self, transfer_info: TransferInfo) -> None:
        """处理单个传输任务"""
        # 这里应该调用实际的传输逻辑
        # 目前只是占位
        logger.info(f"处理传输: {transfer_info.transfer_id}")
    
    async def enqueue(self, transfer_info: TransferInfo) -> bool:
        """添加传输任务到队列"""
        try:
            self._queue.put_nowait(transfer_info)
            return True
        except asyncio.QueueFull:
            logger.warning(f"传输队列已满: {transfer_info.transfer_id}")
            return False
    
    def get_transfer_info(self, transfer_id: str) -> Optional[TransferInfo]:
        """获取传输信息"""
        # 先查活跃的
        if transfer_id in self._active_transfers:
            return self._active_transfers[transfer_id]
        
        # 再查已完成的
        if transfer_id in self._completed_transfers:
            return self._completed_transfers[transfer_id]
        
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取队列统计"""
        return {
            'running': self._running,
            'queue_size': self._queue.qsize(),
            'active_transfers': len(self._active_transfers),
            'completed_transfers': len(self._completed_transfers),
            'max_concurrent': self._max_concurrent,
            'max_queue_size': self._max_queue_size
        }


class FileTransferManager:
    """
    文件传输管理器
    
    整合所有文件传输功能：
    - 传输初始化
    - 数据块管理
    - 文件组装
    - 校验验证
    """
    
    def __init__(
        self,
        storage_manager: Optional[StorageManager] = None,
        transfer_queue: Optional[TransferQueue] = None,
        enable_virus_scan: bool = False
    ):
        self._storage = storage_manager or StorageManager()
        self._queue = transfer_queue or TransferQueue()
        self._enable_virus_scan = enable_virus_scan
        
        # 活跃传输
        self._transfers: Dict[str, TransferInfo] = {}
        
        # 回调函数
        self._on_progress: Optional[Callable[[str, float], None]] = None
        self._on_complete: Optional[Callable[[str, Path], None]] = None
        self._on_error: Optional[Callable[[str, str], None]] = None
        
        logger.info("FileTransferManager initialized")
    
    async def start(self) -> None:
        """启动传输管理器"""
        await self._queue.start()
        logger.info("FileTransferManager started")
    
    async def stop(self) -> None:
        """停止传输管理器"""
        await self._queue.stop()
        logger.info("FileTransferManager stopped")
    
    async def initialize_transfer(
        self,
        file_name: str,
        file_size: int,
        checksum: Optional[str] = None,
        checksum_algorithm: str = "sha256",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[TransferInfo]:
        """
        初始化文件传输
        
        Args:
            file_name: 文件名
            file_size: 文件大小(字节)
            checksum: 预期校验和(可选)
            checksum_algorithm: 校验算法
            metadata: 附加元数据
            
        Returns:
            TransferInfo: 传输信息对象
        """
        # 检查文件大小
        if file_size > self._storage._max_file_size:
            logger.error(f"文件过大: {file_size} > {self._storage._max_file_size}")
            return None
        
        # 检查存储空间
        if not self._storage.check_storage_space(file_size):
            logger.error("存储空间不足")
            return None
        
        # 创建传输ID
        transfer_id = str(uuid.uuid4())
        
        # 创建传输信息
        transfer_info = TransferInfo(
            transfer_id=transfer_id,
            file_name=file_name,
            file_path="",  # 组装后设置
            file_size=file_size,
            checksum=checksum,
            checksum_algorithm=checksum_algorithm,
            metadata=metadata or {}
        )
        
        transfer_info.status = TransferStatus.INITIALIZING
        
        # 保存传输信息
        self._transfers[transfer_id] = transfer_info
        
        logger.info(f"传输初始化: {transfer_id} ({file_name}, {file_size} bytes)")
        
        return transfer_info
    
    async def receive_chunk(
        self,
        transfer_id: str,
        chunk_index: int,
        data: bytes
    ) -> bool:
        """
        接收数据块
        
        Args:
            transfer_id: 传输ID
            chunk_index: 数据块索引
            data: 数据块内容
            
        Returns:
            bool: 是否成功
        """
        transfer_info = self._transfers.get(transfer_id)
        if not transfer_info:
            logger.error(f"传输不存在: {transfer_id}")
            return False
        
        if transfer_info.status not in [TransferStatus.INITIALIZING, TransferStatus.TRANSFERRING]:
            logger.error(f"传输状态不正确: {transfer_id} - {transfer_info.status}")
            return False
        
        # 更新状态
        transfer_info.status = TransferStatus.TRANSFERRING
        
        # 写入数据块
        success = await self._storage.write_chunk(transfer_id, chunk_index, data)
        
        if success:
            transfer_info.add_chunk(chunk_index)
            
            # 触发进度回调
            if self._on_progress:
                self._on_progress(transfer_id, transfer_info.progress)
            
            logger.debug(f"接收数据块: {transfer_id}/{chunk_index} "
                        f"({transfer_info.progress*100:.1f}%)")
            
            # 检查是否完成
            if transfer_info.is_complete:
                asyncio.create_task(self._finalize_transfer(transfer_id))
            
            return True
        else:
            transfer_info.retry_count += 1
            if transfer_info.retry_count >= transfer_info.max_retries:
                transfer_info.status = TransferStatus.FAILED
                transfer_info.error_message = "Max retries exceeded"
            
            return False
    
    async def _finalize_transfer(self, transfer_id: str) -> None:
        """完成传输（验证和组装）"""
        transfer_info = self._transfers.get(transfer_id)
        if not transfer_info:
            return
        
        logger.info(f"完成传输: {transfer_id}")
        
        try:
            transfer_info.status = TransferStatus.VERIFYING
            
            # 组装文件
            final_path = await self._storage.assemble_file(transfer_info)
            
            if not final_path:
                raise Exception("文件组装失败")
            
            transfer_info.file_path = str(final_path)
            
            # 验证校验和
            if transfer_info.checksum:
                logger.info(f"验证校验和: {transfer_id}")
                
                is_valid = await asyncio.get_event_loop().run_in_executor(
                    None,
                    ChecksumVerifier.verify_checksum,
                    final_path,
                    transfer_info.checksum,
                    transfer_info.checksum_algorithm
                )
                
                if not is_valid:
                    # 删除无效文件
                    final_path.unlink(missing_ok=True)
                    raise Exception("Checksum verification failed")
                
                logger.info(f"校验和验证通过: {transfer_id}")
            
            # 病毒扫描（如果启用）
            if self._enable_virus_scan:
                logger.info(f"病毒扫描: {transfer_id}")
                # TODO: 集成病毒扫描
            
            # 更新状态
            transfer_info.status = TransferStatus.COMPLETED
            transfer_info.completed_at = time.time()
            
            # 触发完成回调
            if self._on_complete:
                self._on_complete(transfer_id, final_path)
            
            logger.info(f"传输完成: {transfer_id} -> {final_path}")
            
        except Exception as e:
            logger.error(f"完成传输失败: {transfer_id} - {e}")
            transfer_info.status = TransferStatus.FAILED
            transfer_info.error_message = str(e)
            
            if self._on_error:
                self._on_error(transfer_id, str(e))
    
    async def get_transfer_status(self, transfer_id: str) -> Optional[Dict[str, Any]]:
        """获取传输状态"""
        transfer_info = self._transfers.get(transfer_id)
        if not transfer_info:
            return None
        
        return transfer_info.to_dict()
    
    async def cancel_transfer(self, transfer_id: str) -> bool:
        """取消传输"""
        transfer_info = self._transfers.get(transfer_id)
        if not transfer_info:
            return False
        
        transfer_info.status = TransferStatus.CANCELLED
        
        # 清理临时文件
        chunk_dir = self._storage._temp_path / transfer_id
        if chunk_dir.exists():
            import shutil
            shutil.rmtree(chunk_dir)
        
        logger.info(f"传输已取消: {transfer_id}")
        return True
    
    def get_missing_chunks(self, transfer_id: str, max_count: int = 100) -> List[int]:
        """获取缺失的数据块"""
        transfer_info = self._transfers.get(transfer_id)
        if not transfer_info:
            return []
        
        return transfer_info.get_missing_chunks(max_count)
    
    def set_callbacks(
        self,
        on_progress: Optional[Callable[[str, float], None]] = None,
        on_complete: Optional[Callable[[str, Path], None]] = None,
        on_error: Optional[Callable[[str, str], None]] = None
    ) -> None:
        """设置回调函数"""
        self._on_progress = on_progress
        self._on_complete = on_complete
        self._on_error = on_error
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self._transfers)
        completed = sum(1 for t in self._transfers.values() if t.status == TransferStatus.COMPLETED)
        failed = sum(1 for t in self._transfers.values() if t.status == TransferStatus.FAILED)
        active = sum(1 for t in self._transfers.values() if t.status == TransferStatus.TRANSFERRING)
        
        return {
            'total_transfers': total,
            'active_transfers': active,
            'completed_transfers': completed,
            'failed_transfers': failed,
            'storage_stats': self._storage.get_storage_stats()
        }


def create_file_transfer_manager(
    base_path: str = "./uploads",
    temp_path: str = "./temp",
    **kwargs
) -> FileTransferManager:
    """创建文件传输管理器"""
    storage = StorageManager(base_path=base_path, temp_path=temp_path)
    return FileTransferManager(storage_manager=storage, **kwargs)
