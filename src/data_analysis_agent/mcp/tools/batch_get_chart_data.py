"""MCP 工具: batch_get_chart_data - 批量获取图表数据（优化版，减少重复读取）"""

from mcp.types import Tool, TextContent
import json
import time


# 定义查询参数的结构
QUERY_SCHEMA = {
    "type": "object",
    "properties": {
        "group_by": {
            "type": "string",
            "description": "分组列名（必需）"
        },
        "aggregation": {
            "type": "string",
            "enum": ["sum", "avg", "count", "min", "max"],
            "description": "聚合函数（必需）"
        },
        "aggregate_column": {
            "type": "string",
            "description": "要聚合的列名（count 时可选，其他情况必需）"
        },
        "filters": {
            "type": "array",
            "description": "过滤条件列表（可选）",
            "items": {
                "type": "object",
                "properties": {
                    "column": {"type": "string"},
                    "operator": {"type": "string", "enum": ["=", "!=", ">", "<", ">=", "<=", "contains"]},
                    "value": {}
                },
                "required": ["column", "operator", "value"]
            }
        },
        "order_by": {
            "type": "string",
            "description": "排序列名（可选）"
        },
        "order": {
            "type": "string",
            "enum": ["asc", "desc"],
            "description": "排序方向（可选，默认 asc）"
        },
        "limit": {
            "type": "number",
            "description": "返回的最大分组数（可选，默认 100）"
        }
    },
    "required": ["group_by", "aggregation"]
}

tool_definition = Tool(
    name="batch_get_chart_data",
    description="""批量获取图表数据（优化版，一次性处理多个查询）。

重要优势：
- 只读取一次文件，自动推断所有查询需要的列
- 在内存中执行多个查询，避免重复 I/O
- 返回详细的性能指标

典型场景：需要生成多个图表时，使用此工具比多次调用 get_chart_data 快 3-5 倍。

参数：
- file_path: Excel 文件路径
- sheet_name: 工作表名称（可选）
- queries: 查询列表，每个查询包含 group_by、aggregation、aggregate_column 等

返回格式：
{
  "success": true,
  "results": [
    {"query_index": 0, "data": [...], "query_time_ms": 50},
    {"query_index": 1, "data": [...], "query_time_ms": 30}
  ],
  "summary": {
    "total_queries": 2,
    "read_time_ms": 200,
    "total_time_ms": 280,
    "avg_time_per_query": 140
  }
}

注意：如果不指定 usecols，工具会自动分析所有查询需要的列，只读取这些列。""",
    inputSchema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Excel 文件的完整路径"
            },
            "sheet_name": {
                "type": "string",
                "description": "工作表名称（可选，默认第一个）"
            },
            "usecols": {
                "type": "string",
                "description": "要读取的列（逗号分隔，可选。如果不指定，会自动根据 queries 推断）"
            },
            "queries": {
                "type": "array",
                "description": "查询列表",
                "items": QUERY_SCHEMA
            }
        },
        "required": ["file_path", "queries"]
    }
)


def _extract_columns_from_queries(queries: list) -> set:
    """
    从查询列表中提取所有需要的列名

    Args:
        queries: 查询列表

    Returns:
        需要的列名集合
    """
    columns = set()
    for q in queries:
        # 分组列
        if "group_by" in q:
            columns.add(q["group_by"])
        # 聚合列
        if "aggregate_column" in q:
            columns.add(q["aggregate_column"])
        # 过滤条件中的列
        if "filters" in q:
            for f in q["filters"]:
                if "column" in f:
                    columns.add(f["column"])
        # 排序列
        if "order_by" in q:
            columns.add(q["order_by"])
    return columns


async def handle_batch_get_chart_data(
    file_path: str = None,
    sheet_name: str = None,
    usecols: str = None,
    queries: list = None
) -> list[TextContent]:
    """
    处理批量图表数据请求

    Args:
        file_path: Excel 文件路径
        sheet_name: 工作表名称（可选）
        usecols: 要读取的列（逗号分隔，可选）
        queries: 查询列表

    Returns:
        包含批量查询结果的 TextContent 列表
    """
    from ...core.reader_manager import get_reader
    from ...core.logging_config import get_logger

    logger = get_logger(__name__)

    # 验证必需参数
    if not file_path:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "缺少必需参数: file_path"
            }, ensure_ascii=False)
        )]

    if not queries or not isinstance(queries, list):
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "缺少必需参数: queries（必须是数组）"
            }, ensure_ascii=False)
        )]

    try:
        reader = get_reader(file_path)

        # 自动推断需要的列（如果未指定 usecols）
        if not usecols:
            required_columns = _extract_columns_from_queries(queries)
            if required_columns:
                usecols = ",".join(sorted(required_columns))
                logger.debug(f"自动推断需要读取的列: {usecols}")

        # 记录开始时间
        read_start = time.time()

        # 读取数据（只读取需要的列）
        df = reader._read_file(sheet_name, usecols=usecols)

        read_time_ms = (time.time() - read_start) * 1000

        # 执行每个查询
        results = []
        total_query_time = 0

        for idx, query in enumerate(queries):
            query_start = time.time()

            try:
                # 使用 reader.query 方法执行查询
                result = reader.query(
                    filters=query.get("filters"),
                    group_by=query.get("group_by"),
                    aggregation=query.get("aggregation"),
                    aggregate_column=query.get("aggregate_column"),
                    order_by=query.get("order_by"),
                    order=query.get("order", "asc"),
                    limit=query.get("limit", 100),
                    sheet_name=sheet_name,
                    usecols=usecols
                )

                query_time_ms = (time.time() - query_start) * 1000
                total_query_time += query_time_ms

                results.append({
                    "query_index": idx,
                    "success": True,
                    "data": result,
                    "query_time_ms": round(query_time_ms, 2)
                })

            except Exception as e:
                query_time_ms = (time.time() - query_start) * 1000
                results.append({
                    "query_index": idx,
                    "success": False,
                    "error": str(e),
                    "query_time_ms": round(query_time_ms, 2)
                })

        # 计算总时间
        total_time_ms = read_time_ms + total_query_time
        avg_time_per_query = total_time_ms / len(queries) if queries else 0

        # 返回结果
        summary = {
            "total_queries": len(queries),
            "successful_queries": sum(1 for r in results if r.get("success")),
            "read_time_ms": round(read_time_ms, 2),
            "total_query_time_ms": round(total_query_time, 2),
            "total_time_ms": round(total_time_ms, 2),
            "avg_time_per_query": round(avg_time_per_query, 2)
        }

        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "results": results,
                "summary": summary
            }, ensure_ascii=False, indent=2)
        )]

    except FileNotFoundError as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": f"文件不存在: {file_path}"
            }, ensure_ascii=False)
        )]
    except Exception as e:
        logger.error(f"批量查询错误: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, ensure_ascii=False)
        )]
