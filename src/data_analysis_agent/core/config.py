"""配置管理模块 - 读取和管理 DataAnalysisAgent 配置

支持的配置来源（优先级从高到低）：
1. 环境变量 (DAA_*)
2. 用户配置文件 (~/.config/data-analysis-agent/config.toml)
3. 项目配置文件 (.data-analysis-agent.toml)
4. 默认值
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

    @classmethod
    def load(cls) -> "ServerConfig":
        """加载配置

        Returns:
            ServerConfig 实例
        """
        config_path = _find_config_file()
        toml_config = _load_toml_config(config_path)

        # 从 TOML 配置读取（如果存在）
        server_section = toml_config.get("server", {})

        return cls(
            response_format=server_section.get(
                "response_format",
                os.environ.get("DAA_RESPONSE_FORMAT", "json")
            ),
            show_format_info=server_section.get(
                "show_format_info",
                os.environ.get("DAA_SHOW_FORMAT_INFO", "true").lower() == "true"
            )
        )

    def validate(self) -> None:
        """验证配置有效性

        Raises:
            ValueError: 配置无效时抛出
        """
        valid_formats = ["json", "toon"]
        if self.response_format not in valid_formats:
            raise ValueError(
                f"无效的 response_format: {self.response_format}. "
                f"支持的格式: {', '.join(valid_formats)}"
            )


# 全局配置实例
_config: Optional[ServerConfig] = None


def get_config() -> ServerConfig:
    """获取全局配置实例

    Returns:
        ServerConfig 实例
    """
    global _config
    if _config is None:
        _config = ServerConfig.load()
        _config.validate()
    return _config


def reload_config() -> ServerConfig:
    """重新加载配置

    Returns:
        新的 ServerConfig 实例
    """
    global _config
    _config = ServerConfig.load()
    _config.validate()
    return _config


def set_response_format(format_type: str) -> None:
    """动态设置返回格式

    Args:
        format_type: 格式类型 ("json" 或 "toon")
    """
    config = get_config()
    if format_type not in ["json", "toon"]:
        raise ValueError(f"无效的格式: {format_type}. 支持的格式: json, toon")
    config.response_format = format_type


def get_response_format() -> str:
    """获取当前返回格式

    Returns:
        返回格式类型
    """
    return get_config().response_format


def is_toon_enabled() -> bool:
    """检查是否启用 TOON 格式

    Returns:
        如果启用 TOON 格式返回 True，否则返回 False
    """
    return get_config().response_format == "toon"
