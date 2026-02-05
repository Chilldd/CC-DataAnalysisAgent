"""MCP 工具: analyze_all_dimensions - 批量分析所有维度"""

from mcp.types import Tool, TextContent
import json
from typing import Optional

tool_definition = Tool(
    name="analyze_all_dimensions",
    description="""一次性分析 Excel 文件的所有关键维度，返回紧凑的统计摘要。

分析内容：
- 各分类列的分布（Top 20）
- 数值列的统计（最小值、最大值、平均值、中位数）
- 数据行数、列数

返回格式：紧凑的 JSON，所有分析结果一次返回，无需多次调用。

注意：此工具只返回聚合统计，不返回原始数据。""",
    inputSchema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Excel 文件路径"
            },
            "sheet_name": {
                "type": "string",
                "description": "工作表名称（可选）"
            }
        },
        "required": ["file_path"]
    }
)


async def handle_analyze_all_dimensions(
    file_path: str = None,
    sheet_name: str = None
) -> list[TextContent]:
    """
    批量分析所有维度

    Args:
        file_path: Excel 文件路径
        sheet_name: 工作表名称

    Returns:
        包含所有维度分析的紧凑 JSON
    """
    from ...core.reader_manager import get_reader
    import pandas as pd

    try:
        reader = get_reader(file_path)
        df = reader._read_file(sheet_name)

        result = {
            "r": len(df),
            "c": len(df.columns),
            "dims": {}
        }

        # 分析每一列
        for col in df.columns:
            col_type = "num" if pd.api.types.is_numeric_dtype(df[col]) else "cat"

            if col_type == "num":
                # 数值列：统计 + 分布
                result["dims"][col] = {
                    "t": "num",
                    "min": float(df[col].min()) if not df[col].isna().all() else None,
                    "max": float(df[col].max()) if not df[col].isna().all() else None,
                    "avg": float(df[col].mean()) if not df[col].isna().all() else None,
                    "med": float(df[col].median()) if not df[col].isna().all() else None
                }
            else:
                # 分类列：Top 20 分布
                value_counts = df[col].value_counts().head(20)
                result["dims"][col] = {
                    "t": "cat",
                    "u": int(df[col].nunique()),
                    "top": {str(k): int(v) for k, v in value_counts.items()}
                }

        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, separators=(',', ':'))
        )]

    except FileNotFoundError:
        return [TextContent(
            type="text",
            text=json.dumps({"err": "file_not_found"}, ensure_ascii=False, separators=(',', ':'))
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"err": str(e)}, ensure_ascii=False, separators=(',', ':'))
        )]
