"""MCP 工具: get_reader_stats - 获取 ExcelReader 管理器统计信息"""

from mcp.types import Tool, TextContent
import json

tool_definition = Tool(
    name="get_reader_stats",
    description="""获取 ExcelReader 管理器的统计信息，用于监控缓存性能。

返回内容：
- total_readers: 当前缓存的 reader 数量
- max_readers: 最大缓存数量
- manager_hits: 管理器缓存命中次数
- manager_misses: 管理器缓存未命中次数
- manager_hit_rate: 管理器缓存命中率 (%)
- total_cache_entries: 所有 reader 的缓存条目总数
- total_cache_memory_mb: 所有 reader 的缓存总内存 (MB)
- readers: 每个 reader 的详细信息

用途：监控和优化缓存性能""",
    inputSchema={
        "type": "object",
        "properties": {},
        "required": []
    }
)


async def handle_get_reader_stats() -> list[TextContent]:
    """
    处理 get_reader_stats 请求

    Returns:
        包含 ReaderManager 统计信息的 TextContent 列表
    """
    from ...core.reader_manager import get_reader_stats

    try:
        stats = get_reader_stats()

        return [TextContent(
            type="text",
            text=json.dumps(stats, ensure_ascii=False, indent=2)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, ensure_ascii=False, indent=2)
        )]
