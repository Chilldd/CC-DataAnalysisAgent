"""MCP Server 入口"""

import asyncio
import os
from .mcp.server import main
from .core import setup_logging

if __name__ == "__main__":
    # 检查环境变量启用日志
    enable_logging = os.getenv("DAA_LOG_ENABLE", "false").lower() == "true"
    log_dir = os.getenv("DAA_LOG_DIR", "./logs")
    log_level = os.getenv("DAA_LOG_LEVEL", "INFO")

    if enable_logging:
        setup_logging(
            log_level=log_level,
            log_dir=log_dir,
            log_to_console=True,
            log_to_file=True,
            enable_metrics=True
        )
        print(f"[日志系统] 已启用，日志目录: {log_dir}, 级别: {log_level}")
    else:
        print("[日志系统] 使用默认配置（仅控制台输出）")
        print("[日志系统] 要启用文件日志，设置环境变量: DAA_LOG_ENABLE=true")

    asyncio.run(main())
