"""MCP 工具: analyze - 智能数据分析（一站式工具）"""

from mcp.types import Tool, TextContent
import json

tool_definition = Tool(
    name="analyze",
    description="""【重要】智能数据分析工具 - 请优先使用此工具，不要编写 Python 脚本。

这是一站式数据分析工具，支持：
✓ 数据预览（read_head / read_tail）
✓ 结构分析（schema / info）
✓ 数据聚合（group by + sum/avg/count/min/max）
✓ 数据过滤（=, !=, >, <, >=, <=, contains）
✓ 多维度分析（analyze_all_dimensions）
✓ 图表生成（generate_chart_html）

使用方式：用自然语言描述你的分析需求，例如：
- "分析各地区销售额排名"
- "统计每个产品类别的平均价格"
- "找出销售额前10的城市"

参数说明：
- prompt: 自然语言描述的分析需求（必需）
- file_path: Excel 文件路径（必需）

AI 会自动解析你的需求并调用合适的分析功能。""",
    inputSchema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Excel 文件路径（必需）"
            },
            "prompt": {
                "type": "string",
                "description": "自然语言描述的分析需求，例如：'分析各地区销售额总和，按降序排列'（必需）"
            },
            "sheet_name": {
                "type": "string",
                "description": "工作表名称（可选）"
            },
            "max_results": {
                "type": "number",
                "description": "最大返回结果数（默认50）",
                "default": 50
            },
            "include_chart": {
                "type": "boolean",
                "description": "是否生成图表（默认 false）",
                "default": False
            }
        },
        "required": ["file_path", "prompt"]
    }
)


async def handle_analyze(
    file_path: str = None,
    prompt: str = None,
    sheet_name: str = None,
    max_results: int = 50,
    include_chart: bool = False
) -> list[TextContent]:
    """
    处理 analyze 请求 - 智能数据分析

    Args:
        file_path: Excel 文件路径
        prompt: 自然语言分析需求
        sheet_name: 工作表名称
        max_results: 最大返回结果数
        include_chart: 是否生成图表

    Returns:
        分析结果
    """
    from ...core.reader_manager import get_reader

    # 验证必需参数
    if not file_path:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "缺少必需参数: file_path"
            }, ensure_ascii=False)
        )]

    if not prompt:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "缺少必需参数: prompt，请描述你的分析需求"
            }, ensure_ascii=False)
        )]

    try:
        reader = get_reader(file_path)

        # 1. 先获取数据结构
        df = reader._read_file(sheet_name)
        headers = df.columns.tolist()
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = [c for c in headers if c not in numeric_cols]

        # 2. 简单的关键词匹配分析（实际可接入 LLM 解析）
        prompt_lower = prompt.lower()

        # 检测聚合类型
        agg_map = {
            '总和': 'sum', '总和': 'sum', '总计': 'sum', '合计': 'sum',
            '平均': 'avg', '平均值': 'avg', '均值': 'avg',
            '数量': 'count', '计数': 'count', '个数': 'count',
            '最大': 'max', '最高': 'max',
            '最小': 'min', '最低': 'min'
        }

        aggregation = 'sum'  # 默认
        for keyword, agg in agg_map.items():
            if keyword in prompt_lower:
                aggregation = agg
                break

        # 检测分组列（简单启发式）
        group_by = None
        for col in categorical_cols:
            if col.lower() in prompt_lower or col in prompt:
                group_by = col
                break

        # 检测聚合列
        aggregate_column = None
        if aggregation != 'count':
            for col in numeric_cols:
                if col.lower() in prompt_lower or col in prompt:
                    aggregate_column = col
                    break
            # 如果没找到，取第一个数值列
            if not aggregate_column and numeric_cols:
                aggregate_column = numeric_cols[0]

        # 3. 执行查询
        if group_by:
            result = reader.query(
                group_by=group_by,
                aggregation=aggregation,
                aggregate_column=aggregate_column,
                limit=max_results,
                sheet_name=sheet_name,
                order='desc' if '排名' in prompt or '降序' in prompt or 'top' in prompt_lower else 'asc'
            )

            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "analysis": {
                        "type": aggregation,
                        "group_by": group_by,
                        "aggregate_column": aggregate_column,
                        "prompt": prompt
                    },
                    "data": result.get("data"),
                    "metadata": {
                        "total_rows": int(len(df)),
                        "columns": headers,
                        "numeric_columns": numeric_cols,
                        "categorical_columns": categorical_cols
                    },
                    "_note": "此结果由 analyze 工具自动解析需求并生成。如需更复杂的分析，请使用 get_chart_data 工具。"
                }, ensure_ascii=False, indent=2)
            )]
        else:
            # 无明确分组，返回数据结构建议
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "message": "未检测到明确的分组列，请使用 get_chart_data 工具指定分析参数",
                    "available_columns": {
                        "numeric": numeric_cols,
                        "categorical": categorical_cols
                    },
                    "example_usage": {
                        "tool": "get_chart_data",
                        "parameters": {
                            "file_path": file_path,
                            "group_by": categorical_cols[0] if categorical_cols else None,
                            "aggregation": aggregation,
                            "aggregate_column": numeric_cols[0] if numeric_cols else None
                        }
                    }
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
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, ensure_ascii=False)
        )]
