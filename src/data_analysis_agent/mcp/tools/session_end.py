"""MCP 工具: session_end - 结束数据分析会话并生成报告"""

from mcp.types import Tool, TextContent
import json
import time

tool_definition = Tool(
    name="session_end",
    description="""【强制】结束数据分析会话的必须最后一步。

⚠️ 工作流要求：
1. 完成所有数据分析后必须调用此工具
2. 必须在 session_start 之后调用
3. 生成完整的会话统计报告

完整工作流：
session_start → get_excel_schema → 分析工具 → session_end

报告内容：
- 会话时长
- 工具调用次数统计
- 数据传输量统计（发送/接收）
- 各工具调用详情
- 缓存命中率
- 性能分析建议""",
    inputSchema={
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "会话 ID（可选，用于验证）"
            }
        }
    }
)


async def handle_session_end(session_id: str = None) -> list[TextContent]:
    """
    结束数据分析会话并生成报告

    Args:
        session_id: 会话 ID（可选）

    Returns:
        完整的会话统计报告
    """
    from ...core.logging_config import get_logger, get_metrics
    from .session_start import get_session_info, reset_session
    from ...core.reader_manager import get_reader_stats

    logger = get_logger(__name__)

    session_info = get_session_info()

    if not session_info["is_active"]:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "没有活跃的会话，请先调用 session_start 开始会话"
            }, ensure_ascii=False, indent=2)
        )]

    # 计算会话时长
    session_duration = time.time() - session_info["start_time"]

    # 获取 metrics 统计
    metrics = get_metrics()
    metrics_summary = metrics.get_summary()

    # 输出日志摘要
    metrics.log_summary()

    # 获取 reader 统计
    try:
        reader_stats = get_reader_stats()
    except Exception:
        reader_stats = {
            "total_readers": 0,
            "manager_hit_rate": 0,
            "total_cache_entries": 0,
            "total_cache_memory_mb": 0
        }

    # 解析工具统计
    tool_details = []
    for tool, stats in metrics_summary.get("工具统计", {}).items():
        tool_details.append({
            "tool": tool,
            "calls": stats.get("调用次数", 0),
            "total_return": stats.get("总返回大小", "0B"),
            "avg_return": stats.get("平均返回大小", "0B"),
            "avg_duration": stats.get("平均耗时", "0ms")
        })

    # 解析文件统计
    file_details = []
    for file, stats in metrics_summary.get("文件统计", {}).items():
        file_details.append({
            "file": file,
            "read_count": stats.get("读取次数", 0),
            "total_data": stats.get("总数据量", "0B"),
            "cache_hit_rate": stats.get("缓存命中率", "0%")
        })

    # 生成报告
    report = {
        "success": True,
        "session_report": {
            "duration": {
                "seconds": round(session_duration, 2),
                "formatted": _format_duration(session_duration)
            },
            "calls": {
                "total": metrics_summary.get("总调用次数", 0),
                "by_tool": tool_details
            },
            "data_transmission": {
                "total_sent": metrics_summary.get("总发送数据", "0B"),
                "total_received": metrics_summary.get("总返回数据", "0B")
            },
            "files": file_details,
            "cache": {
                "reader_count": reader_stats.get("total_readers", 0),
                "manager_hit_rate": f"{reader_stats.get('manager_hit_rate', 0)}%",
                "cache_entries": reader_stats.get("total_cache_entries", 0),
                "cache_memory_mb": reader_stats.get("total_cache_memory_mb", 0)
            }
        },
        "analysis": _generate_analysis(
            session_duration,
            metrics_summary.get("总调用次数", 0),
            metrics_summary.get("总返回数据", "0B"),
            reader_stats
        ),
        "message": "会话已结束，以上是完整的统计报告。"
    }

    # 输出日志摘要
    logger.info(f"[SESSION] 会话结束 - 时长: {_format_duration(session_duration)}, "
                f"调用: {metrics_summary.get('总调用次数', 0)}次, "
                f"传输: {metrics_summary.get('总返回数据', '0B')}")

    # 重置会话
    reset_session()

    return [TextContent(
        type="text",
        text=json.dumps(report, ensure_ascii=False, indent=2)
    )]


def _format_duration(seconds: float) -> str:
    """格式化时长"""
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}分钟"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}小时"


def _parse_bytes(size_str: str) -> int:
    """解析字节字符串为字节数"""
    size_str = size_str.strip().upper()
    # 按长度降序检查单位，避免 'K' 匹配到 'KB' 的情况
    for unit, multiplier in [('GB', 1024**3), ('MB', 1024**2), ('KB', 1024), ('K', 1024), ('B', 1)]:
        if size_str.endswith(unit):
            num_str = size_str[:-len(unit)].strip()
            try:
                return float(num_str) * multiplier
            except ValueError:
                continue
    return 0


def _generate_analysis(duration: float, total_calls: int, total_received: str, reader_stats: dict) -> dict:
    """生成分析建议"""
    analysis = {
        "performance_rating": "未知",
        "suggestions": []
    }

    # 评分
    total_received_bytes = _parse_bytes(total_received)
    hit_rate = reader_stats.get("manager_hit_rate", 0)

    if total_calls <= 5:
        analysis["performance_rating"] = "高效"
    elif total_calls <= 15:
        analysis["performance_rating"] = "正常"
    else:
        analysis["performance_rating"] = "可优化"

    # 生成建议
    if isinstance(hit_rate, (int, float)) and hit_rate < 50:
        analysis["suggestions"].append("缓存命中率较低，建议优化工具调用顺序")

    if total_received_bytes > 1024 * 1024:  # > 1MB
        analysis["suggestions"].append("数据传输量较大，建议使用 usecols 参数限制列")

    if duration > 30:
        analysis["suggestions"].append("会话时间较长，考虑分批处理数据")

    if not analysis["suggestions"]:
        analysis["suggestions"].append("性能良好，无需特别优化")

    return analysis
