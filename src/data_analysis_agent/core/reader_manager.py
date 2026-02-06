"""ExcelReader 全局管理器 - 在多个工具调用之间共享 ExcelReader 实例

此模块实现了一个单例管理器，用于管理和复用 ExcelReader 实例，
避免每次工具调用都重新读取文件，提高性能并减少内存使用。
"""

import threading
from pathlib import Path
from typing import Dict, Optional
from collections import OrderedDict
from datetime import datetime, timedelta
import time

from .excel_reader import ExcelReader
from .logging_config import get_logger

logger = get_logger(__name__)


class ReaderManager:
    """
    ExcelReader 全局管理器

    功能：
    1. 为每个文件路径维护一个 ExcelReader 实例
    2. 使用 LRU 策略管理实例数量
    3. 自动清理不活跃的实例
    4. 线程安全
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化管理器"""
        if self._initialized:
            return

        # 使用 OrderedDict 实现 LRU 缓存
        # {file_path: (reader, last_used_time)}
        self._readers: OrderedDict[str, tuple[ExcelReader, float]] = OrderedDict()

        # 配置
        self.max_readers = 5  # 最多缓存 5 个文件的 reader
        self.idle_timeout = 300  # 5 分钟未使用则清理

        # 统计信息
        self._hits = 0
        self._misses = 0

        self._initialized = True
        logger.info(f"[ReaderManager] 初始化完成，max_readers={self.max_readers}, idle_timeout={self.idle_timeout}s")

    def get_reader(self, file_path: str) -> ExcelReader:
        """
        获取指定文件的 ExcelReader 实例

        如果已存在则复用，否则创建新实例

        Args:
            file_path: Excel 文件路径

        Returns:
            ExcelReader 实例
        """
        # 规范化路径
        normalized_path = str(Path(file_path).resolve())

        with self._lock:
            current_time = time.time()

            # 检查是否已存在
            if normalized_path in self._readers:
                reader, last_used = self._readers[normalized_path]
                # 检查文件是否被修改
                if self._is_file_modified(file_path, last_used):
                    logger.info(f"[ReaderManager] 文件已修改，重新加载: {file_path}")
                    del self._readers[normalized_path]
                    self._misses += 1
                else:
                    # 更新使用时间，移动到末尾（LRU）
                    self._readers.move_to_end(normalized_path)
                    self._readers[normalized_path] = (reader, current_time)
                    self._hits += 1
                    logger.debug(f"[ReaderManager] 复用 ExcelReader: {file_path}")
                    return reader

            # 创建新实例
            self._misses += 1
            logger.info(f"[ReaderManager] 创建新 ExcelReader: {file_path}")

            # 检查是否需要清理
            self._cleanup_if_needed()

            # 创建新 reader
            reader = ExcelReader(file_path, enable_cache=True)

            # 添加到缓存
            self._readers[normalized_path] = (reader, current_time)

            return reader

    def _is_file_modified(self, file_path: str, last_used: float) -> bool:
        """检查文件在 last_used 时间之后是否被修改"""
        try:
            path = Path(file_path)
            if not path.exists():
                return True

            mtime = path.stat().st_mtime
            return mtime > last_used
        except Exception:
            return False

    def _cleanup_if_needed(self):
        """清理不活跃的 reader"""
        current_time = time.time()

        # 清理超过 idle_timeout 的 reader
        to_remove = []
        for path, (reader, last_used) in self._readers.items():
            if current_time - last_used > self.idle_timeout:
                to_remove.append(path)

        for path in to_remove:
            self._remove_reader(path)

        # 如果还是超过最大数量，删除最旧的
        while len(self._readers) >= self.max_readers:
            oldest_path = next(iter(self._readers))
            self._remove_reader(oldest_path)

    def _remove_reader(self, path: str):
        """移除指定的 reader"""
        if path in self._readers:
            reader, _ = self._readers[path]
            # 获取缓存信息
            cache_info = reader.get_cache_info()
            logger.info(
                f"[ReaderManager] 移除 ExcelReader: {path}, "
                f"缓存={cache_info.get('total_cache_entries', 0)}项"
            )
            del self._readers[path]

    def clear(self, file_path: Optional[str] = None):
        """
        清理缓存的 reader

        Args:
            file_path: 指定文件路径，如果为 None 则清理所有
        """
        with self._lock:
            if file_path:
                normalized_path = str(Path(file_path).resolve())
                if normalized_path in self._readers:
                    self._remove_reader(normalized_path)
            else:
                logger.info(f"[ReaderManager] 清理所有 {len(self._readers)} 个 reader")
                self._readers.clear()
                self._hits = 0
                self._misses = 0

    def get_stats(self) -> Dict:
        """获取管理器统计信息"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0

            # 汇总所有 reader 的缓存信息
            total_cache_entries = 0
            total_cache_memory = 0
            reader_details = []

            for path, (reader, last_used) in self._readers.items():
                cache_info = reader.get_cache_info()
                total_cache_entries += cache_info.get('total_cache_entries', 0)
                total_cache_memory += cache_info.get('cache_memory_bytes', 0)
                reader_details.append({
                    "path": path,
                    "last_used_seconds_ago": int(time.time() - last_used),
                    "cache_entries": cache_info.get('total_cache_entries', 0),
                    "cache_memory_mb": cache_info.get('cache_memory_mb', 0),
                    "reader_hit_rate": cache_info.get('hit_rate', 0)
                })

            return {
                "total_readers": len(self._readers),
                "max_readers": self.max_readers,
                "manager_hits": self._hits,
                "manager_misses": self._misses,
                "manager_hit_rate": round(hit_rate * 100, 2),
                "total_cache_entries": total_cache_entries,
                "total_cache_memory_mb": round(total_cache_memory / 1024 / 1024, 2),
                "readers": reader_details
            }


# 全局单例实例
_reader_manager = ReaderManager()


def get_reader(file_path: str) -> ExcelReader:
    """
    获取指定文件的 ExcelReader 实例（快捷函数）

    Args:
        file_path: Excel 文件路径

    Returns:
        ExcelReader 实例
    """
    return _reader_manager.get_reader(file_path)


def get_reader_stats() -> Dict:
    """获取 reader 管理器统计信息（快捷函数）"""
    return _reader_manager.get_stats()


def clear_reader(file_path: Optional[str] = None):
    """清理缓存的 reader（快捷函数）"""
    _reader_manager.clear(file_path)


def preload_files(file_paths: list[str], mode: str = "metadata") -> Dict:
    """
    预加载多个文件到缓存

    Args:
        file_paths: 文件路径列表
        mode: 预加载模式
            - metadata: 仅加载元数据（sheet 名称、列信息），快速
            - full: 完整加载数据

    Returns:
        预加载结果字典
    """
    import time
    result = {
        "success": True,
        "mode": mode,
        "files": [],
        "total_files": len(file_paths),
        "total_time_ms": 0
    }

    start_time = time.time()

    for file_path in file_paths:
        file_start = time.time()
        try:
            # 获取或创建 reader
            reader = _reader_manager.get_reader(file_path)

            if mode == "metadata":
                # 仅加载元数据，不缓存数据（避免后续获取数据时只有 1 行）
                sheet_names = reader._get_sheet_names()
                # 使用 read_head 方法读取前几行获取列信息（不经过缓存）
                head_result = reader.read_head(n=5)
                columns = head_result["data"][0] if head_result["data"] else []
                # 清除可能被缓存的数据（确保后续能读取完整数据）
                # 注意：read_head 不经过缓存，但为保险起见清除缓存
                reader.clear_cache()

                file_result = {
                    "file_path": file_path,
                    "status": "loaded",
                    "mode": "metadata",
                    "sheets": sheet_names,
                    "columns": len(columns),
                    "sample_rows": len(head_result["data"]) - 1 if head_result["data"] else 0,
                    "time_ms": round((time.time() - file_start) * 1000, 1)
                }
            else:  # mode == "full"
                # 完整加载数据
                df = reader._read_file()
                file_result = {
                    "file_path": file_path,
                    "status": "loaded",
                    "mode": "full",
                    "rows": int(len(df)),
                    "columns": int(len(df.columns)),
                    "size_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
                    "time_ms": round((time.time() - file_start) * 1000, 1)
                }

            result["files"].append(file_result)
            logger.info(f"[ReaderManager] 预加载成功: {file_path} ({file_result['time_ms']}ms)")

        except FileNotFoundError:
            result["files"].append({
                "file_path": file_path,
                "status": "error",
                "error": "文件不存在"
            })
            logger.warning(f"[ReaderManager] 预加载失败: {file_path} - 文件不存在")
        except Exception as e:
            result["files"].append({
                "file_path": file_path,
                "status": "error",
                "error": str(e)
            })
            logger.error(f"[ReaderManager] 预加载失败: {file_path} - {e}")

    result["total_time_ms"] = round((time.time() - start_time) * 1000, 1)
    result["loaded_count"] = sum(1 for f in result["files"] if f.get("status") == "loaded")
    result["error_count"] = sum(1 for f in result["files"] if f.get("status") == "error")

    return result
