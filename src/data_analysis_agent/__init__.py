"""DataAnalysisAgent MCP Server"""

from .mcp.server import server

__all__ = ["server"]


def main():
    """主入口函数"""
    import asyncio
    from .mcp.server import main as server_main

    asyncio.run(server_main())
