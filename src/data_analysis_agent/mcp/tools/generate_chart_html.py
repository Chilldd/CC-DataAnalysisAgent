"""MCP 工具: generate_chart_html - 生成完整 HTML 图表"""

from mcp.types import Tool, TextContent
from pathlib import Path
import json
from typing import List

tool_definition = Tool(
    name="generate_chart_html",
    description="""【可视化】生成 ECharts HTML 图表文件。使用此工具生成可交互图表，无需编写脚本。

完整工作流：
session_start → get_excel_schema → get_chart_data → 本工具 → session_end

参数：
- file_path: Excel 文件路径
- echarts_config: 单个 ECharts 配置（单图表模式）
- echarts_configs: 多个 ECharts 配置数组（多图表模式）
- advice: 分析建议（Claude 生成）
- title: 图表标题
- output_path: 输出 HTML 路径
- show_data_table: 是否显示数据表格（默认 False）

返回：
- html_path: 生成的 HTML 文件路径
- chart_count: 图表数量

生成的 HTML 包含：
- 可交互的 ECharts 图表（支持多图表）
- 分析建议卡片
- 数据表格（可选，默认不显示）""",
    inputSchema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Excel 文件的完整路径"
            },
            "echarts_config": {
                "type": "object",
                "description": "单个 ECharts 配置对象（单图表模式，与 echarts_configs 二选一）"
            },
            "echarts_configs": {
                "type": "array",
                "items": {"type": "object"},
                "description": "多个 ECharts 配置对象数组（多图表模式，与 echarts_config 二选一）"
            },
            "advice": {
                "type": "string",
                "description": "分析建议文本（可选）"
            },
            "title": {
                "type": "string",
                "description": "图表标题（可选）"
            },
            "output_path": {
                "type": "string",
                "description": "输出 HTML 文件路径（可选，默认在源文件同目录）"
            },
            "sheet_name": {
                "type": "string",
                "description": "工作表名称（可选）"
            },
            "show_data_table": {
                "type": "boolean",
                "description": "是否显示数据表格（默认 False）"
            },
            "data_query": {
                "type": "object",
                "description": "数据查询配置（可选，用于筛选/聚合数据）",
                "properties": {
                    "filters": {
                        "type": "array",
                        "description": "过滤条件"
                    },
                    "group_by": {
                        "type": "string",
                        "description": "分组列"
                    },
                    "aggregation": {
                        "type": "string",
                        "enum": ["sum", "avg", "count", "min", "max"],
                        "description": "聚合函数"
                    },
                    "aggregate_column": {
                        "type": "string",
                        "description": "聚合列"
                    },
                    "limit": {
                        "type": "number",
                        "description": "限制行数"
                    }
                }
            }
        },
        "required": ["file_path"]
    }
)


def _default_output_path(file_path: str) -> str:
    """生成默认输出路径"""
    from datetime import datetime
    source_path = Path(file_path)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return str(source_path.parent / f"{source_path.stem}_chart_{timestamp}.html")


async def handle_generate_chart_html(
    file_path: str,
    echarts_config: dict = None,
    echarts_configs: List[dict] = None,
    advice: str = None,
    title: str = None,
    output_path: str = None,
    sheet_name: str = None,
    show_data_table: bool = False,
    data_query: dict = None
) -> list[TextContent]:
    """
    处理 generate_chart_html 请求

    Args:
        file_path: Excel 文件路径
        echarts_config: 单个 ECharts 配置
        echarts_configs: 多个 ECharts 配置数组
        advice: 分析建议
        title: 图表标题
        output_path: 输出路径
        sheet_name: 工作表名称
        show_data_table: 是否显示数据表格
        data_query: 数据查询配置

    Returns:
        包含生成结果的 TextContent 列表
    """
    from ...core.reader_manager import get_reader
    from ...core.chart_renderer import ChartRenderer

    try:
        # 兼容处理：单个配置转为列表
        if echarts_config and not echarts_configs:
            echarts_configs = [echarts_config]

        if not echarts_config and not echarts_configs:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": "必须提供 echarts_config 或 echarts_configs 参数"
                }, ensure_ascii=False, indent=2)
            )]

        # 1. 获取数据（仅当需要显示数据表格时）
        chart_data = None
        if show_data_table:
            reader = get_reader(file_path)

            if data_query:
                # 按查询条件获取数据
                data = reader.query(
                    filters=data_query.get("filters"),
                    group_by=data_query.get("group_by"),
                    aggregation=data_query.get("aggregation"),
                    aggregate_column=data_query.get("aggregate_column"),
                    limit=data_query.get("limit", 1000),
                    sheet_name=sheet_name
                )
                chart_data = data["data"]
            else:
                # 读取完整数据
                result = reader.read(sheet_name=sheet_name)
                chart_data = result["data"]

        # 2. 生成 HTML
        renderer = ChartRenderer()
        html_path = renderer.generate_html(
            echarts_configs=echarts_configs,
            data=chart_data,
            advice=advice,
            title=title or "数据分析图表",
            output_path=output_path or _default_output_path(file_path),
            show_data_table=show_data_table
        )

        # 3. 返回结果
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "html_path": html_path,
                "message": f"图表已生成: {html_path}",
                "chart_count": len(echarts_configs),
                "data_table_included": show_data_table
            }, ensure_ascii=False, indent=2)
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
