"""MCP 工具: get_chart_data - 获取图表所需的聚合数据"""

from mcp.types import Tool, TextContent
import json

tool_definition = Tool(
    name="get_chart_data",
    description="""【数据分析】获取聚合数据用于图表生成。请优先使用此工具，不要编写 Python 脚本。

完整工作流：
session_start → get_excel_schema → 本工具（选择列） → generate_chart_html → session_end

内置功能（无需脚本）：
- 过滤：按列值筛选（支持 =, !=, >, <, >=, <=, contains）
- 分组聚合：按维度分组后执行聚合函数
- 排序：升序/降序
- 限制：返回前N个分组（默认100）

必需参数：
- group_by: 分组列名（维度列）
- aggregation: 聚合函数 sum/avg/count/min/max
- aggregate_column: 要聚合的列名（指标列，count 时可选）

优化参数：
- usecols: 只读取指定列，大幅减少 token 消耗
  支持格式：
  - 逗号分隔的列名: "CompanyCode,SectionAmountYuan" （推荐）
  - 列字母范围: "A:C"
  - 列索引列表: [0, 1, 2]

返回格式：[[分组列, 聚合值], ...]，可直接用于 ECharts series.data。

注意：只返回聚合数据。如需查看原始数据，使用 read_head_excel 或 read_tail_excel。""",
    inputSchema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Excel 文件路径"
            },
            "usecols": {
                "type": "string",
                "description": "要处理的列（减少 token：只读取指定列）。支持格式：1) 逗号分隔的列名 'Col1,Col2'（推荐）；2) 列字母范围 'A:C'；3) 列索引 [0,1]"
            },
            "filters": {
                "type": "array",
                "description": "过滤条件列表",
                "items": {
                    "type": "object",
                    "properties": {
                        "column": {"type": "string", "description": "列名"},
                        "operator": {
                            "type": "string",
                            "enum": ["=", "!=", ">", "<", ">=", "<=", "contains"],
                            "description": "操作符"
                        },
                        "value": {"description": "值"}
                    },
                    "required": ["column", "operator", "value"]
                }
            },
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
                "description": "要聚合的列名（count 时可选）"
            },
            "order_by": {
                "type": "string",
                "description": "排序列名"
            },
            "order": {
                "type": "string",
                "enum": ["asc", "desc"],
                "description": "排序方向（默认 asc）"
            },
            "limit": {
                "type": "number",
                "description": "返回的最大分组数（默认100）"
            },
            "sheet_name": {
                "type": "string",
                "description": "工作表名称"
            }
        },
        "required": ["file_path", "group_by", "aggregation"]
    }
)


async def handle_get_chart_data(
    file_path: str = None,
    filters: list = None,
    group_by: str = None,
    aggregation: str = None,
    aggregate_column: str = None,
    order_by: str = None,
    order: str = "asc",
    limit: int = 100,
    sheet_name: str = None,
    usecols: str = None
) -> list[TextContent]:
    """
    处理 get_chart_data 请求

    Args:
        file_path: Excel 文件路径
        filters: 过滤条件
        group_by: 分组列（必需）
        aggregation: 聚合函数（必需）
        aggregate_column: 聚合列
        order_by: 排序列
        order: 排序方向
        limit: 分组数限制
        sheet_name: 工作表名称
        usecols: 要处理的列（可选，减少 token）

    Returns:
        包含聚合数据的 TextContent 列表
    """
    from ...core.reader_manager import get_reader

    try:
        reader = get_reader(file_path)
        result = reader.query(
            filters=filters,
            group_by=group_by,
            aggregation=aggregation,
            aggregate_column=aggregate_column,
            order_by=order_by,
            order=order,
            limit=limit,
            sheet_name=sheet_name,
            usecols=usecols
        )

        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False)
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
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, ensure_ascii=False)
        )]
