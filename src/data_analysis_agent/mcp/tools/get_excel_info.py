"""MCP 工具: get_excel_info - 获取 Excel 数据结构信息"""

from mcp.types import Tool, TextContent
import json
import traceback

tool_definition = Tool(
    name="get_excel_info",
    description="""【不推荐】获取 Excel 详细信息。

⚠️ 已废弃：请使用 get_excel_schema 代替。
- get_excel_schema 返回更少数据，更节省 token
- get_excel_schema 自动推荐维度和指标列

此工具仅用于调试目的，不推荐常规使用。

返回内容：
- file_info: 文件基本信息
- sheets: 工作表列表
- column_names/column_types: 列信息
- sample_data: 样本数据
- column_stats: 列统计

推荐：使用 get_excel_schema 获取相同信息但返回更少数据""",
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
            "sample_rows": {
                "type": "number",
                "description": "样本行数（默认10）",
                "default": 10
            }
        },
        "required": ["file_path"]
    }
)


async def handle_get_excel_info(
    file_path: str = None,
    sheet_name: str = None,
    sample_rows: int = 10
) -> list[TextContent]:
    """
    处理 get_excel_info 请求

    Args:
        file_path: Excel 文件路径
        sheet_name: 工作表名称（可选）
        sample_rows: 样本行数

    Returns:
        包含数据结构信息的 TextContent 列表
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
        result = reader.get_info(sheet_name=sheet_name, sample_rows=sample_rows)

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
            }, ensure_ascii=False, indent=2)
        )]
    except Exception as e:
        # 记录完整的错误堆栈用于调试
        error_detail = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
        return [TextContent(
            type="text",
            text=json.dumps(error_detail, ensure_ascii=False, indent=2)
        )]
