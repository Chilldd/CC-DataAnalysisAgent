"""MCP 工具: get_excel_schema - 获取 Excel 数据结构（轻量级，最小 token）"""

from mcp.types import Tool, TextContent
import json
import pandas as pd
import numpy as np


def _to_serializable(val):
    """将 numpy 类型转换为 JSON 可序列化的 Python 原生类型"""
    if pd.isna(val):
        return None
    elif isinstance(val, (np.integer, np.int64, np.int32)):
        return int(val)
    elif isinstance(val, (np.floating, np.float64, np.float32)):
        return float(val)
    elif isinstance(val, (np.bool_, bool)):
        return bool(val)
    elif hasattr(val, 'isoformat'):  # datetime
        return val.isoformat()
    else:
        return val

tool_definition = Tool(
    name="get_excel_schema",
    description="""【强制】获取 Excel 数据结构。获取数据信息的正确方式。

⚠️ 重要：请始终使用此工具获取数据结构，不要使用 get_excel_info。

完整工作流：
session_start → get_excel_schema → 选择列 → get_chart_data → session_end

返回内容（轻量级，最小 token）：
- headers: 列名列表
- first_row: 第一行数据值
- total_rows: 总行数
- column_count: 列数
- suggested_dimensions: 建议的维度列（唯一值 < 50 的列）
- suggested_metrics: 建议的指标列（数值类型的列）
- columns_info: 详细的列信息（数据类型、唯一值数量等）

优势：
- 比 get_excel_info 返回更少数据（节省 token）
- 自动推荐维度列和指标列
- 包含完整工作流指引
- 支持 usecols 参数只获取指定列的信息，进一步减少数据传输""",
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
                "description": "只获取指定列的信息（逗号分隔的列名，可选）"
            }
        },
        "required": ["file_path"]
    }
)


async def handle_get_excel_schema(
    file_path: str = None,
    sheet_name: str = None,
    usecols: str = None
) -> list[TextContent]:
    """
    处理 get_excel_schema 请求

    Args:
        file_path: Excel 文件路径
        sheet_name: 工作表名称（可选）
        usecols: 只获取指定列的信息（可选）

    Returns:
        包含数据结构信息的 TextContent 列表（紧凑格式）
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

    try:
        reader = get_reader(file_path)

        # 只读取需要的列（如果指定了 usecols）
        df = reader._read_file(sheet_name, usecols=usecols)

        # 获取基本信息
        headers = df.columns.tolist()
        total_rows = len(df)

        # 获取第一行数据（转 JSON 可序列化）
        first_row = {}
        for col in headers:
            val = df[col].iloc[0] if len(df) > 0 else None
            first_row[col] = _to_serializable(val)

        # 分析列类型和推荐维度/指标（只使用前100行样本）
        sample_df = df.head(min(100, len(df)))
        suggested_dimensions = []
        suggested_metrics = []
        columns_info = {}

        for col in headers:
            dtype = df[col].dtype
            unique_count = sample_df[col].nunique()

            # 数值类型 -> 指标列
            if pd.api.types.is_numeric_dtype(dtype):
                suggested_metrics.append(col)
            # 唯一值较少的列 -> 维度列
            elif unique_count < 50:
                suggested_dimensions.append(col)

            # 详细的列信息
            columns_info[col] = {
                "type": str(dtype),
                "unique_count": int(unique_count),
                "is_dimension": col in suggested_dimensions,
                "is_metric": col in suggested_metrics
            }

        # 紧凑格式返回（确保所有值都是 JSON 可序列化的）
        result = {
            "success": True,
            "headers": headers,
            "first_row": first_row,
            "total_rows": int(total_rows),
            "column_count": int(len(headers)),
            "suggested_dimensions": suggested_dimensions,
            "suggested_metrics": suggested_metrics,
            "columns_info": columns_info,
            "_workflow": "1. 调用此工具了解结构 -> 2. 选择列 -> 3. 调用 get_chart_data(usecols=[...])"
        }

        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
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
