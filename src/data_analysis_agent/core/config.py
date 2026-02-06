"""配置管理模块 - 读取和管理 DataAnalysisAgent 配置

支持的配置来源（优先级从高到低）：
1. 环境变量 (DAA_*)
2. 用户配置文件 (~/.config/data-analysis-agent/config.toml)
3. 项目配置文件 (.data-analysis-agent.toml)
4. 默认值

配置文件示例 (.data-analysis-agent.toml):
    [server]
    response_format = "json"  # json 或 toon
    show_format_info = true

    [cache]
    enabled = true
    max_size = 10

    [logging]
    level = "INFO"  # DEBUG, INFO, WARNING, ERROR
    file = "logs/agent.log"

    [performance]
    enable_threading = false
    chunk_size = 10000
"""

import os
import tomli
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, field


def _find_config_file() -> Optional[Path]:
    """查找配置文件

    Returns:
        找到的配置文件路径，如果没有找到则返回 None
    """
    # 检查项目配置文件
    project_config = Path.cwd() / ".data-analysis-agent.toml"
    if project_config.exists():
        return project_config

    # 检查用户配置文件
    home = Path.home()
    user_config_dir = home / ".config" / "data-analysis-agent"
    user_config = user_config_dir / "config.toml"
    if user_config.exists():
        return user_config

    # 检查 Windows 配置目录
    if os.name == "nt":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            win_config = Path(appdata) / "data-analysis-agent" / "config.toml"
            if win_config.exists():
                return win_config

    return None


def _load_toml_config(config_path: Optional[Path]) -> dict:
    """加载 TOML 配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        配置字典
    """
    if not config_path or not config_path.exists():
        return {}

    try:
        with open(config_path, "rb") as f:
            return tomli.load(f)
    except Exception as e:
        # 配置文件读取失败，使用默认值
        return {}


@dataclass
class ServerConfig:
    """服务器配置"""

    # 返回数据格式
    response_format: str = field(
        default_factory=lambda: os.environ.get("DAA_RESPONSE_FORMAT", "json")
    )

    # 是否显示格式信息
    show_format_info: bool = field(
        default_factory=lambda: os.environ.get("DAA_SHOW_FORMAT_INFO", "true").lower() == "true"
    )

    # 服务器主机（如果需要）
    host: str = field(
        default_factory=lambda: os.environ.get("DAA_HOST", "localhost")
    )

    # 服务器端口（如果需要）
    port: int = field(
        default_factory=lambda: int(os.environ.get("DAA_PORT", "8000"))
    )


@dataclass
class CacheConfig:
    """缓存配置"""

    # 是否启用缓存
    enabled: bool = field(
        default_factory=lambda: os.environ.get("DAA_CACHE_ENABLED", "true").lower() == "true"
    )

    # 最大缓存条目数
    max_size: int = field(
        default_factory=lambda: int(os.environ.get("DAA_CACHE_MAX_SIZE", "10"))
    )

    # 缓存过期时间（秒）
    ttl: int = field(
        default_factory=lambda: int(os.environ.get("DAA_CACHE_TTL", "3600"))
    )


@dataclass
class LoggingConfig:
    """日志配置"""

    # 日志级别
    level: str = field(
        default_factory=lambda: os.environ.get("DAA_LOG_LEVEL", "INFO")
    )

    # 日志文件路径
    file: str = field(
        default_factory=lambda: os.environ.get("DAA_LOG_FILE", "logs/agent.log")
    )

    # 是否输出到控制台
    console: bool = field(
        default_factory=lambda: os.environ.get("DAA_LOG_CONSOLE", "true").lower() == "true"
    )

    # 日志文件最大大小（MB）
    max_file_size_mb: int = field(
        default_factory=lambda: int(os.environ.get("DAA_LOG_MAX_SIZE", "10"))
    )

    # 保留的日志文件数量
    backup_count: int = field(
        default_factory=lambda: int(os.environ.get("DAA_LOG_BACKUP_COUNT", "5"))
    )


@dataclass
class PerformanceConfig:
    """性能配置"""

    # 是否启用多线程读取
    enable_threading: bool = field(
        default_factory=lambda: os.environ.get("DAA_ENABLE_THREADING", "false").lower() == "true"
    )

    # 分块读取大小
    chunk_size: int = field(
        default_factory=lambda: int(os.environ.get("DAA_CHUNK_SIZE", "10000"))
    )

    # 默认查询限制
    default_limit: int = field(
        default_factory=lambda: int(os.environ.get("DAA_DEFAULT_LIMIT", "100"))
    )

    # 最大查询限制
    max_limit: int = field(
        default_factory=lambda: int(os.environ.get("DAA_MAX_LIMIT", "10000"))
    )


@dataclass
class Config:
    """完整配置对象"""

    server: ServerConfig = field(default_factory=ServerConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)

    @classmethod
    def load(cls) -> "Config":
        """加载完整配置

        Returns:
            Config 实例
        """
        config_path = _find_config_file()
        toml_config = _load_toml_config(config_path)

        # 加载各配置节
        server_section = toml_config.get("server", {})
        cache_section = toml_config.get("cache", {})
        logging_section = toml_config.get("logging", {})
        performance_section = toml_config.get("performance", {})

        return cls(
            server=ServerConfig(
                response_format=server_section.get(
                    "response_format",
                    os.environ.get("DAA_RESPONSE_FORMAT", "json")
                ),
                show_format_info=server_section.get(
                    "show_format_info",
                    os.environ.get("DAA_SHOW_FORMAT_INFO", "true").lower() == "true"
                ),
                host=server_section.get(
                    "host",
                    os.environ.get("DAA_HOST", "localhost")
                ),
                port=server_section.get(
                    "port",
                    int(os.environ.get("DAA_PORT", "8000"))
                )
            ),
            cache=CacheConfig(
                enabled=cache_section.get(
                    "enabled",
                    os.environ.get("DAA_CACHE_ENABLED", "true").lower() == "true"
                ),
                max_size=cache_section.get(
                    "max_size",
                    int(os.environ.get("DAA_CACHE_MAX_SIZE", "10"))
                ),
                ttl=cache_section.get(
                    "ttl",
                    int(os.environ.get("DAA_CACHE_TTL", "3600"))
                )
            ),
            logging=LoggingConfig(
                level=logging_section.get(
                    "level",
                    os.environ.get("DAA_LOG_LEVEL", "INFO")
                ),
                file=logging_section.get(
                    "file",
                    os.environ.get("DAA_LOG_FILE", "logs/agent.log")
                ),
                console=logging_section.get(
                    "console",
                    os.environ.get("DAA_LOG_CONSOLE", "true").lower() == "true"
                ),
                max_file_size_mb=logging_section.get(
                    "max_file_size_mb",
                    int(os.environ.get("DAA_LOG_MAX_SIZE", "10"))
                ),
                backup_count=logging_section.get(
                    "backup_count",
                    int(os.environ.get("DAA_LOG_BACKUP_COUNT", "5"))
                )
            ),
            performance=PerformanceConfig(
                enable_threading=performance_section.get(
                    "enable_threading",
                    os.environ.get("DAA_ENABLE_THREADING", "false").lower() == "true"
                ),
                chunk_size=performance_section.get(
                    "chunk_size",
                    int(os.environ.get("DAA_CHUNK_SIZE", "10000"))
                ),
                default_limit=performance_section.get(
                    "default_limit",
                    int(os.environ.get("DAA_DEFAULT_LIMIT", "100"))
                ),
                max_limit=performance_section.get(
                    "max_limit",
                    int(os.environ.get("DAA_MAX_LIMIT", "10000"))
                )
            )
        )

    def validate(self) -> None:
        """验证配置有效性

        Raises:
            ValueError: 配置无效时抛出
        """
        # 验证服务器配置
        valid_formats = ["json", "toon"]
        if self.server.response_format not in valid_formats:
            raise ValueError(
                f"无效的 response_format: {self.server.response_format}. "
                f"支持的格式: {', '.join(valid_formats)}"
            )

        if not (1 <= self.server.port <= 65535):
            raise ValueError(f"无效的端口号: {self.server.port}")

        # 验证缓存配置
        if self.cache.max_size < 0:
            raise ValueError(f"无效的缓存大小: {self.cache.max_size}")

        if self.cache.ttl < 0:
            raise ValueError(f"无效的缓存 TTL: {self.cache.ttl}")

        # 验证日志配置
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.logging.level.upper() not in valid_log_levels:
            raise ValueError(
                f"无效的日志级别: {self.logging.level}. "
                f"支持的级别: {', '.join(valid_log_levels)}"
            )

        # 验证性能配置
        if self.performance.chunk_size <= 0:
            raise ValueError(f"无效的分块大小: {self.performance.chunk_size}")

        if self.performance.default_limit <= 0:
            raise ValueError(f"无效的默认限制: {self.performance.default_limit}")

        if self.performance.max_limit < self.performance.default_limit:
            raise ValueError(
                f"max_limit ({self.performance.max_limit}) 必须大于等于 "
                f"default_limit ({self.performance.default_limit})"
            )

    def to_dict(self) -> dict[str, Any]:
        """将配置转换为字典

        Returns:
            配置字典
        """
        return {
            "server": {
                "response_format": self.server.response_format,
                "show_format_info": self.server.show_format_info,
                "host": self.server.host,
                "port": self.server.port,
            },
            "cache": {
                "enabled": self.cache.enabled,
                "max_size": self.cache.max_size,
                "ttl": self.cache.ttl,
            },
            "logging": {
                "level": self.logging.level,
                "file": self.logging.file,
                "console": self.logging.console,
                "max_file_size_mb": self.logging.max_file_size_mb,
                "backup_count": self.logging.backup_count,
            },
            "performance": {
                "enable_threading": self.performance.enable_threading,
                "chunk_size": self.performance.chunk_size,
                "default_limit": self.performance.default_limit,
                "max_limit": self.performance.max_limit,
            }
        }

    def save_to_file(self, path: Optional[Path] = None) -> None:
        """保存配置到文件

        Args:
            path: 保存路径（默认为项目配置文件）

        Note:
            需要安装 tomli_w 库来写入 TOML 文件
        """
        if path is None:
            path = Path.cwd() / ".data-analysis-agent.toml"

        try:
            import tomli_w
            with open(path, "wb") as f:
                tomli_w.dump(self.to_dict(), f)
        except ImportError:
            raise ImportError(
                "保存配置需要 tomli_w 库。请运行: pip install tomli-w"
            )


# 全局配置实例
_config: Optional[Config] = None


def get_config() -> Config:
    """获取全局配置实例

    Returns:
        Config 实例
    """
    global _config
    if _config is None:
        _config = Config.load()
        _config.validate()
    return _config


def reload_config() -> Config:
    """重新加载配置

    Returns:
        新的 Config 实例
    """
    global _config
    _config = Config.load()
    _config.validate()
    return _config


def set_response_format(format_type: str) -> None:
    """动态设置返回格式

    Args:
        format_type: 格式类型 ("json" 或 "toon")

    Raises:
        ValueError: 格式无效时抛出
    """
    config = get_config()
    if format_type not in ["json", "toon"]:
        raise ValueError(f"无效的格式: {format_type}. 支持的格式: json, toon")
    config.server.response_format = format_type


def get_response_format() -> str:
    """获取当前返回格式

    Returns:
        返回格式类型
    """
    return get_config().server.response_format


def is_toon_enabled() -> bool:
    """检查是否启用 TOON 格式

    Returns:
        如果启用 TOON 格式返回 True，否则返回 False
    """
    return get_config().server.response_format == "toon"


def get_cache_config() -> CacheConfig:
    """获取缓存配置

    Returns:
        CacheConfig 实例
    """
    return get_config().cache


def get_logging_config() -> LoggingConfig:
    """获取日志配置

    Returns:
        LoggingConfig 实例
    """
    return get_config().logging


def get_performance_config() -> PerformanceConfig:
    """获取性能配置

    Returns:
        PerformanceConfig 实例
    """
    return get_config().performance


# 保留旧的 ServerConfig 兼容性
class _ServerConfigCompat:
    """兼容旧版本的 ServerConfig 类"""

    def __init__(self, config: Config):
        self._config = config

    @property
    def response_format(self) -> str:
        return self._config.server.response_format

    @response_format.setter
    def response_format(self, value: str) -> None:
        self._config.server.response_format = value

    @property
    def show_format_info(self) -> bool:
        return self._config.server.show_format_info

    def validate(self) -> None:
        self._config.validate()

    @classmethod
    def load(cls) -> "_ServerConfigCompat":
        return cls(get_config())


# 向后兼容：保留旧的 ServerConfig 类名作为别名
ServerConfig = _ServerConfigCompat
