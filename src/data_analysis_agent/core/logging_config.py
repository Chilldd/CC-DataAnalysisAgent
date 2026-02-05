"""日志配置模块 - 为 DataAnalysisAgent 提供统一的日志管理"""

import logging
import sys
import json
import time
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional, Any, Dict
from collections import defaultdict
from functools import wraps
import threading


class ColoredFormatter(logging.Formatter):
    """带颜色的控制台日志格式化器"""

    # ANSI 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
    }
    RESET = '\033[0m'

    def format(self, record):
        # 添加颜色到级别名称
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)

    def formatTime(self, record, datefmt=None):
        """自定义时间格式"""
        return logging.Formatter.formatTime(self, record, '%Y-%m-%d %H:%M:%S')


class MetricsLogger:
    """数据传输和性能指标统计器"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._tool_stats: Dict[str, Dict] = defaultdict(lambda: {
            'call_count': 0,
            'total_bytes_sent': 0,
            'total_bytes_received': 0,
            'total_duration_ms': 0,
            'errors': 0,
            'last_call': None
        })
        self._file_stats: Dict[str, Dict] = defaultdict(lambda: {
            'read_count': 0,
            'total_bytes': 0,
            'cache_hits': 0,
            'cache_misses': 0
        })
        self._logger = None

    def set_logger(self, logger: logging.Logger):
        """设置日志记录器"""
        self._logger = logger

    def log_tool_call(
        self,
        tool_name: str,
        args: dict,
        result_size: int,
        duration_ms: float,
        success: bool = True
    ):
        """记录工具调用统计"""
        stats = self._tool_stats[tool_name]
        stats['call_count'] += 1
        stats['total_bytes_sent'] += self._estimate_size(args)
        stats['total_bytes_received'] += result_size
        stats['total_duration_ms'] += duration_ms
        if not success:
            stats['errors'] += 1
        stats['last_call'] = time.time()

        # 记录详细日志
        if self._logger:
            args_preview = self._truncate_dict(args, max_length=200)
            self._logger.info(
                f"[METRICS] 工具调用: {tool_name} | "
                f"参数: {args_preview} | "
                f"返回大小: {self._format_bytes(result_size)} | "
                f"耗时: {duration_ms:.0f}ms | "
                f"成功: {success}"
            )

            # 警告大数据传输
            if result_size > 100_000:  # > 100KB
                self._logger.warning(
                    f"[METRICS] ⚠️ 大数据传输: {tool_name} 返回 {self._format_bytes(result_size)}"
                )

    def log_file_read(self, file_path: str, bytes_read: int, from_cache: bool = False):
        """记录文件读取统计"""
        stats = self._file_stats[file_path]
        stats['read_count'] += 1
        stats['total_bytes'] += bytes_read
        if from_cache:
            stats['cache_hits'] += 1
        else:
            stats['cache_misses'] += 1

        if self._logger:
            cache_status = "缓存" if from_cache else "文件"
            self._logger.debug(
                f"[METRICS] 文件读取: {file_path} | "
                f"来源: {cache_status} | "
                f"大小: {self._format_bytes(bytes_read)}"
            )

    def get_summary(self) -> dict:
        """获取统计摘要"""
        total_calls = sum(s['call_count'] for s in self._tool_stats.values())
        total_sent = sum(s['total_bytes_sent'] for s in self._tool_stats.values())
        total_received = sum(s['total_bytes_received'] for s in self._tool_stats.values())

        tool_details = {}
        for tool, stats in self._tool_stats.items():
            if stats['call_count'] > 0:
                tool_details[tool] = {
                    '调用次数': stats['call_count'],
                    '平均返回大小': self._format_bytes(
                        stats['total_bytes_received'] // stats['call_count']
                    ),
                    '总返回大小': self._format_bytes(stats['total_bytes_received']),
                    '平均耗时': f"{stats['total_duration_ms'] / stats['call_count']:.0f}ms",
                    '错误数': stats['errors']
                }

        file_details = {}
        for file, stats in self._file_stats.items():
            if stats['read_count'] > 0:
                cache_rate = stats['cache_hits'] / stats['read_count'] * 100
                file_details[file] = {
                    '读取次数': stats['read_count'],
                    '总数据量': self._format_bytes(stats['total_bytes']),
                    '缓存命中率': f"{cache_rate:.1f}%"
                }

        return {
            '总调用次数': total_calls,
            '总发送数据': self._format_bytes(total_sent),
            '总返回数据': self._format_bytes(total_received),
            '工具统计': tool_details,
            '文件统计': file_details
        }

    def log_summary(self):
        """输出统计摘要到日志"""
        summary = self.get_summary()
        if self._logger:
            self._logger.info(f"[METRICS] ===== 数据传输统计摘要 =====")
            self._logger.info(f"[METRICS] 总调用次数: {summary['总调用次数']}")
            self._logger.info(f"[METRICS] 总发送数据: {summary['总发送数据']}")
            self._logger.info(f"[METRICS] 总返回数据: {summary['总返回数据']}")

            if summary['工具统计']:
                self._logger.info(f"[METRICS] --- 工具详情 ---")
                for tool, stats in summary['工具统计'].items():
                    self._logger.info(
                        f"[METRICS]   {tool}: "
                        f"调用{stats['调用次数']}次, "
                        f"平均返回{stats['平均返回大小']}, "
                        f"平均耗时{stats['平均耗时']}"
                    )

            if summary['文件统计']:
                self._logger.info(f"[METRICS] --- 文件详情 ---")
                for file, stats in summary['文件统计'].items():
                    self._logger.info(
                        f"[METRICS]   {file}: "
                        f"读取{stats['读取次数']}次, "
                        f"总数据{stats['总数据量']}, "
                        f"缓存命中率{stats['缓存命中率']}"
                    )

            self._logger.info(f"[METRICS] =============================")

    def reset(self):
        """重置统计数据"""
        self._tool_stats.clear()
        self._file_stats.clear()

    def _estimate_size(self, obj: Any) -> int:
        """估算对象的字节大小"""
        try:
            return len(json.dumps(obj, ensure_ascii=False))
        except Exception:
            return len(str(obj))

    def _format_bytes(self, bytes_size: int) -> str:
        """格式化字节大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f}{unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f}TB"

    def _truncate_dict(self, d: dict, max_length: int = 200) -> str:
        """截断字典的字符串表示"""
        s = json.dumps(d, ensure_ascii=False)
        if len(s) > max_length:
            return s[:max_length] + "..."
        return s


# 全局指标记录器实例
metrics = MetricsLogger()


class LoggerFactory:
    """日志工厂类 - 创建和管理 Logger 实例"""

    _configured = False
    _log_dir: Optional[Path] = None
    _log_level = logging.INFO
    _log_to_file = False
    _log_to_console = True

    @classmethod
    def setup(
        cls,
        log_level: str = "INFO",
        log_dir: Optional[str] = None,
        log_to_file: bool = False,
        log_to_console: bool = True,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        use_time_rotation: bool = True,
        enable_metrics: bool = True
    ) -> None:
        """
        配置全局日志系统

        Args:
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: 日志文件目录
            log_to_file: 是否记录到文件
            log_to_console: 是否输出到控制台
            max_file_size: 单个日志文件最大大小（字节）
            backup_count: 保留的备份文件数量
            use_time_rotation: 是否使用时间滚动（按天），否则使用大小滚动
            enable_metrics: 是否启用数据传输统计
        """
        cls._log_level = getattr(logging, log_level.upper(), logging.INFO)
        cls._log_to_file = log_to_file
        cls._log_to_console = log_to_console

        if log_to_file and log_dir:
            cls._log_dir = Path(log_dir)
            cls._log_dir.mkdir(parents=True, exist_ok=True)

        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(cls._log_level)

        # 清除现有的处理器
        root_logger.handlers.clear()

        # 控制台处理器
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(cls._log_level)
            console_formatter = ColoredFormatter(
                fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)

        # 文件处理器
        if log_to_file and cls._log_dir:
            if use_time_rotation:
                # 按时间滚动（每天一个文件）
                file_handler = TimedRotatingFileHandler(
                    cls._log_dir / 'data_analysis_agent.log',
                    when='midnight',
                    interval=1,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
                file_handler.suffix = '%Y-%m-%d'
            else:
                # 按大小滚动
                file_handler = RotatingFileHandler(
                    cls._log_dir / 'data_analysis_agent.log',
                    maxBytes=max_file_size,
                    backupCount=backup_count,
                    encoding='utf-8'
                )

            file_handler.setLevel(cls._log_level)
            file_formatter = logging.Formatter(
                fmt='%(asctime)s [%(levelname)s] %(name)s [%(filename)s:%(lineno)d]: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

        # 单独的错误日志文件
        if log_to_file and cls._log_dir:
            error_handler = RotatingFileHandler(
                cls._log_dir / 'error.log',
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(file_formatter)
            root_logger.addHandler(error_handler)

        # 单独的指标日志文件
        if log_to_file and cls._log_dir and enable_metrics:
            metrics_handler = RotatingFileHandler(
                cls._log_dir / 'metrics.log',
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            metrics_handler.setLevel(logging.INFO)
            metrics_handler.setFormatter(file_formatter)
            root_logger.addHandler(metrics_handler)

        cls._configured = True

        # 设置指标记录器的日志
        if enable_metrics:
            metrics.set_logger(root_logger)

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        获取命名 Logger 实例

        Args:
            name: Logger 名称，通常使用 __name__

        Returns:
            Logger 实例

        Example:
            logger = LoggerFactory.get_logger(__name__)
            logger.info("这是一条信息")
        """
        if not cls._configured:
            cls.setup()

        logger = logging.getLogger(name)

        # 确保日志级别正确设置
        if logger.level == logging.NOTSET:
            logger.setLevel(cls._log_level)

        return logger

    @classmethod
    def set_level(cls, level: str) -> None:
        """
        动态设置日志级别

        Args:
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        new_level = getattr(logging, level.upper(), logging.INFO)
        cls._log_level = new_level

        root_logger = logging.getLogger()
        root_logger.setLevel(new_level)

        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(new_level)


# 便捷函数
def get_logger(name: str) -> logging.Logger:
    """获取 Logger 实例的便捷函数"""
    return LoggerFactory.get_logger(name)


def setup_logging(**kwargs) -> None:
    """配置日志系统的便捷函数"""
    LoggerFactory.setup(**kwargs)


def get_metrics() -> MetricsLogger:
    """获取指标记录器实例"""
    return metrics


def log_metrics_summary():
    """输出指标统计摘要"""
    metrics.log_summary()


def reset_metrics():
    """重置指标统计"""
    metrics.reset()


# 默认配置 - 初始化时使用
def init_default_logging():
    """初始化默认日志配置（仅控制台输出，INFO 级别）"""
    LoggerFactory.setup(
        log_level="INFO",
        log_to_console=True,
        log_to_file=False
    )


# 自动初始化默认配置
init_default_logging()
