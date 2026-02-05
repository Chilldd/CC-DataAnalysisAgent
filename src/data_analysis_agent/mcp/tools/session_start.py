"""MCP 工具: session_start - 开始数据分析会话"""

from mcp.types import Tool, TextContent
import json
import time

tool_definition = Tool(
    name="session_start",
    description="""【强制】开始数据分析会话的必须第一步。

⚠️ 工作流要求：
1. 任何数据分析任务必须首先调用此工具
2. 然后才能调用其他数据工具（如 get_excel_schema）
3. 完成后必须调用 session_end

完整工作流：
session_start → get_excel_schema → 分析工具 → session_end

功能：
- 初始化会话统计和缓存
- 记录会话开始时间
- 重置追踪计数器

返回：会话 ID 和开始时间""",
    inputSchema={
        "type": "object",
        "properties": {
            "session_name": {
                "type": "string",
                "description": "会话名称（可选，便于识别）"
            }
        }
    }
)

# 全局会话状态
_session_start_time = None


async def handle_session_start(session_name: str = None) -> list[TextContent]:
    """
    开始数据分析会话

    Args:
        session_name: 会话名称（可选）

    Returns:
        会话信息
    """
    global _session_start_time

    _session_start_time = time.time()

    from ...core.logging_config import get_logger, reset_metrics
    logger = get_logger(__name__)

    # 重置指标
    reset_metrics()

    session_id = f"session_{int(_session_start_time)}"
    name = session_name or "未命名会话"

    logger.info(f"[SESSION] 开始新会话: {name} (ID: {session_id})")

    return [TextContent(
        type="text",
        text=json.dumps({
            "success": True,
            "session_id": session_id,
            "session_name": name,
            "start_time": _session_start_time,
            "message": "会话已开始，请继续使用其他工具进行分析。完成后调用 session_end 查看完整报告。"
        }, ensure_ascii=False, indent=2)
    )]


def get_session_info():
    """获取当前会话信息（内部使用）"""
    global _session_start_time
    return {
        "start_time": _session_start_time,
        "is_active": _session_start_time is not None
    }


def reset_session():
    """重置会话（内部使用）"""
    global _session_start_time
    _session_start_time = None
