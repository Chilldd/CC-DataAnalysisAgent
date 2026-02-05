"""MCP 工具: read_tail_excel - 快速读取 Excel 文件后 n 行"""

from mcp.types import Tool, TextContent
import json

tool_definition = Tool(
    name="read_tail_excel",
    description="""【重要】快速读取 Excel 文件的后 n 行数据。请使用此工具预览数据，不要编写 Python 脚本读取文件。

返回内容：
- data: 二维数组格式的数据（包含表头）
- rows: 实际读取的行数
- columns: 列数

用途：快速预览文件结尾内容，检查最新数据""",
    inputSchema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Excel 或 CSV 文件的完整路径"
            },
            "n": {
                "type": "number",
                "description": "读取行数（默认10）",
                "default": 10
            },
            "sheet_name": {
                "type": "string",
                "description": "工作表名称（可选，默认第一个）"
            },
            "usecols": {
                "type": "string",
                "description": "要读取的列，如 'A:C' 或列名列表（可选）"
            }
        },
        "required": ["file_path"]
    }
)


async def handle_read_tail_excel(
    file_path: str,
    n: int = 10,
    sheet_name: str = None,
    usecols: str = None
) -> list[TextContent]:
    """
    处理 read_tail_excel 请求

    Args:
        file_path: Excel 文件路径
        n: 读取行数
        sheet_name: 工作表名称（可选）
        usecols: 要读取的列（可选）

    Returns:
        包含后 n 行数据的 TextContent 列表
    """
    from ...core.reader_manager import get_reader

    try:
        reader = get_reader(file_path)
        result = reader.read_tail(n=n, sheet_name=sheet_name, usecols=usecols)

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
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e)
            }, ensure_ascii=False, indent=2)
        )]
