"""同步进度存储"""
import threading
from typing import Dict, Optional, List
from datetime import datetime
from dataclasses import dataclass, field, asdict
import json


@dataclass
class SyncProgress:
    """同步进度"""
    task_id: str
    status: str = "pending"  # pending, running, completed, failed
    scope: str = ""  # all, watchlist
    mode: str = ""  # full, incremental
    total_stocks: int = 0
    synced_stocks: int = 0
    current_stock: str = ""
    current_stock_name: str = ""
    synced_records: int = 0
    failed_stocks: List[str] = field(default_factory=list)
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    
    def to_dict(self):
        return asdict(self)


class SyncProgressManager:
    """同步进度管理器"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._progress: Dict[str, SyncProgress] = {}
                    cls._instance._progress_lock = threading.Lock()
        return cls._instance
    
    def create_progress(self, task_id: str, scope: str, mode: str, total_stocks: int) -> SyncProgress:
        """创建新的同步进度"""
        with self._progress_lock:
            progress = SyncProgress(
                task_id=task_id,
                scope=scope,
                mode=mode,
                total_stocks=total_stocks,
                start_time=datetime.now().isoformat()
            )
            self._progress[task_id] = progress
            return progress
    
    def get_progress(self, task_id: str) -> Optional[SyncProgress]:
        """获取同步进度"""
        with self._progress_lock:
            return self._progress.get(task_id)
    
    def update_progress(self, task_id: str, **kwargs):
        """更新同步进度"""
        with self._progress_lock:
            if task_id in self._progress:
                progress = self._progress[task_id]
                for key, value in kwargs.items():
                    if hasattr(progress, key):
                        setattr(progress, key, value)
    
    def add_log(self, task_id: str, message: str):
        """添加日志"""
        with self._progress_lock:
            if task_id in self._progress:
                self._progress[task_id].logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
                # 只保留最近100条日志
                if len(self._progress[task_id].logs) > 100:
                    self._progress[task_id].logs = self._progress[task_id].logs[-100:]
    
    def complete_progress(self, task_id: str, success: bool = True):
        """完成同步"""
        with self._progress_lock:
            if task_id in self._progress:
                self._progress[task_id].status = "completed" if success else "failed"
                self._progress[task_id].end_time = datetime.now().isoformat()
    
    def get_latest_progress(self) -> Optional[SyncProgress]:
        """获取最新的同步进度"""
        with self._progress_lock:
            if not self._progress:
                return None
            # 返回最新的进度
            latest = None
            for progress in self._progress.values():
                if latest is None or progress.start_time > latest.start_time:
                    latest = progress
            return latest
    
    def clear_old_progress(self, max_count: int = 10):
        """清理旧的进度记录"""
        with self._progress_lock:
            if len(self._progress) > max_count:
                # 按开始时间排序，删除最旧的
                sorted_keys = sorted(
                    self._progress.keys(),
                    key=lambda k: self._progress[k].start_time or ""
                )
                for key in sorted_keys[:-max_count]:
                    del self._progress[key]


# 全局实例
sync_progress_manager = SyncProgressManager()
