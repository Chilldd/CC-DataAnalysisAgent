"""MCP Server 主入口"""

import asyncio
import sys
import json
import traceback
import time
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from ..core.logging_config import get_logger, get_metrics
from ..core.config import get_config, is_toon_enabled
from ..core.toon_serializer import serialize_result

logger = get_logger(__name__)
metrics = get_metrics()

# 导入工具定义和处理函数
from .tools.get_excel_schema import tool_definition as schema_tool, handle_get_excel_schema
from .tools.get_excel_info import tool_definition as info_tool, handle_get_excel_info
from .tools.generate_chart_html import tool_definition as chart_tool, handle_generate_chart_html
from .tools.get_chart_data import tool_definition as data_tool, handle_get_chart_data
from .tools.batch_get_chart_data import tool_definition as batch_data_tool, handle_batch_get_chart_data
from .tools.read_head_excel import tool_definition as head_tool, handle_read_head_excel
from .tools.read_tail_excel import tool_definition as tail_tool, handle_read_tail_excel
from .tools.get_reader_stats import tool_definition as stats_tool, handle_get_reader_stats
from .tools.session_start import tool_definition as session_start_tool, handle_session_start
from .tools.session_end import tool_definition as session_end_tool, handle_session_end

# 创建 MCP Server 实例
server = Server("data-analysis-agent")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的工具"""
    return [session_start_tool, session_end_tool, schema_tool, info_tool, chart_tool, data_tool, batch_data_tool, head_tool, tail_tool, stats_tool]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    调用工具

    Args:
        name: 工具名称
        arguments: 工具参数

    Returns:
        工具执行结果
    """
    # 记录开始时间
    start_time = time.time()

    # 记录请求参数（截断过长的参数）
    args_str = json.dumps(arguments, ensure_ascii=False)
    args_preview = args_str[:300] + "..." if len(args_str) > 300 else args_str
    logger.info(f"[REQUEST] 工具: {name} | 参数: {args_preview}")

    try:
        result = None
        if name == "session_start":
            result = await handle_session_start(**arguments)
        elif name == "session_end":
            result = await handle_session_end(**arguments)
        elif name == "get_excel_schema":
            result = await handle_get_excel_schema(**arguments)
        elif name == "get_excel_info":
            result = await handle_get_excel_info(**arguments)
        elif name == "generate_chart_html":
            result = await handle_generate_chart_html(**arguments)
        elif name == "get_chart_data":
            result = await handle_get_chart_data(**arguments)
        elif name == "batch_get_chart_data":
            result = await handle_batch_get_chart_data(**arguments)
        elif name == "read_head_excel":
            result = await handle_read_head_excel(**arguments)
        elif name == "read_tail_excel":
            result = await handle_read_tail_excel(**arguments)
        elif name == "get_reader_stats":
            result = await handle_get_reader_stats()
        else:
            logger.error(f"未知工具: {name}")
            raise ValueError(f"Unknown tool: {name}")

        # 计算耗时和数据大小
        duration_ms = (time.time() - start_time) * 1000
        result_size = 0
        if result and len(result) > 0:
            result_size = len(result[0].text.encode('utf-8'))

        # 记录到指标系统
        metrics.log_tool_call(
            tool_name=name,
            args=arguments,
            result_size=result_size,
            duration_ms=duration_ms,
            success=True
        )

        # 应用格式转换（如果配置了 TOON）
        config = get_config()
        if config.response_format == "toon" and result and len(result) > 0:
            result = _convert_to_toon(result, name)

        # 重新计算转换后的大小
        if result and len(result) > 0:
            result_size = len(result[0].text.encode('utf-8'))

        # 记录返回数据信息
        logger.info(
            f"[RESPONSE] 工具: {name} | "
            f"返回大小: {_format_bytes(result_size)} | "
            f"格式: {config.response_format.upper()} | "
            f"耗时: {duration_ms:.0f}ms"
        )

        return result

    except Exception as e:
        # 计算错误情况下的耗时
        duration_ms = (time.time() - start_time) * 1000

        # 记录错误到指标系统
        metrics.log_tool_call(
            tool_name=name,
            args=arguments,
            result_size=0,
            duration_ms=duration_ms,
            success=False
        )

        # 捕获所有未处理的异常，返回错误信息而不是崩溃
        logger.error(f"工具执行错误 [{name}]: {e}", exc_info=True)
        error_result = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "tool": name,
            "traceback": traceback.format_exc()
        }
        return [TextContent(
            type="text",
            text=json.dumps(error_result, ensure_ascii=False, indent=2)
        )]


def _format_bytes(bytes_size: int) -> str:
    """格式化字节大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f}TB"


def _convert_to_toon(result: list[TextContent], tool_name: str) -> list[TextContent]:
    """
    将结果转换为 TOON 格式

    Args:
        result: 原始结果列表
        tool_name: 工具名称

    Returns:
        转换后的结果列表
    """
    if not result or len(result) == 0:
        return result

    try:
        # 解析 JSON 数据
        original_text = result[0].text
        data = json.loads(original_text)

        # 检查是否是错误响应
        if isinstance(data, dict) and not data.get("success", True):
            # 错误响应保持 JSON 格式
            return result

        # 转换为 TOON 格式
        config = get_config()
        toon_text = serialize_result(
            data,
            format_type="toon",
            show_format=config.show_format_info
        )

        return [TextContent(
            type="text",
            text=toon_text
        )]

    except json.JSONDecodeError:
        # 如果不是有效的 JSON，保持原样
        return result
    except Exception as e:
        logger.warning(f"TOON 转换失败: {e}，保持 JSON 格式")
        return result


async def main():
    """启动 MCP Server"""
    logger.info("DataAnalysisAgent MCP Server 启动中...")
    logger.info("[METRICS] 数据传输统计已启用，将在 session_end 时输出会话统计报告")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
