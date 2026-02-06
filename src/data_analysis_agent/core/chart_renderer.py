"""图表渲染器 - 生成包含 ECharts 图表的完整 HTML"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class ChartRenderer:
    """渲染包含 ECharts 图表的 HTML 文件"""

    def generate_html(
        self,
        echarts_config: dict = None,
        echarts_configs: List[dict] = None,
        data: List[List] = None,
        advice: str = None,
        title: str = "数据分析图表",
        output_path: str = None,
        show_data_table: bool = False
    ) -> str:
        """
        生成完整的 HTML 文件

        Args:
            echarts_config: 单个 ECharts 配置对象（兼容旧版）
            echarts_configs: 多个 ECharts 配置对象列表
            data: 二维数据数组（包含表头），仅当 show_data_table=True 时使用
            advice: 分析建议文本
            title: 图表标题
            output_path: 输出文件路径
            show_data_table: 是否显示数据表格（默认 False）

        Returns:
            生成的 HTML 文件绝对路径
        """
        # 兼容旧版：单个配置转为列表
        if echarts_config and not echarts_configs:
            echarts_configs = [echarts_config]

        if not echarts_configs:
            raise ValueError("必须提供 echarts_config 或 echarts_configs")

        # 规范化 ECharts 配置格式
        echarts_configs = [self._normalize_echarts_config(cfg) for cfg in echarts_configs]

        html_content = self._render_template(
            title=title,
            echarts_configs=json.dumps(echarts_configs, ensure_ascii=False),
            data=json.dumps(data, ensure_ascii=False) if show_data_table and data else "null",
            advice=advice or "",
            show_data_table=show_data_table,
            chart_count=len(echarts_configs)
        )

        if output_path is None:
            output_path = f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        output_file = Path(output_path)
        output_file.write_text(html_content, encoding='utf-8')
        return str(output_file.absolute())

    def _render_template(
        self,
        title: str,
        echarts_configs: str,
        data: str,
        advice: str,
        show_data_table: bool,
        chart_count: int
    ) -> str:
        """
        渲染 HTML 模板

        Args:
            title: 图表标题
            echarts_configs: ECharts 配置 JSON 数组字符串
            data: 数据 JSON 字符串
            advice: 分析建议
            show_data_table: 是否显示数据表格
            chart_count: 图表数量

        Returns:
            完整的 HTML 内容
        """
        advice_html = ""
        if advice:
            advice_html = f'''
        <div class="advice-card">
            <h3>分析建议</h3>
            <p>{self._escape_html(advice)}</p>
        </div>'''

        data_table_html = ""
        if show_data_table:
            data_table_html = f'''
        <div class="data-table">
            <h3>数据明细</h3>
            <div id="table"></div>
        </div>'''

        # 动态生成图表容器
        charts_html = ""
        charts_js = ""
        for i in range(chart_count):
            charts_html += f'        <div class="chart-card">\n            <div id="chart{i}"></div>\n        </div>\n'
            charts_js += f'''
        // 渲染图表 {i + 1}
        const chartDom{i} = document.getElementById('chart{i}');
        const myChart{i} = echarts.init(chartDom{i});
        const option{i} = echartsConfigs[{i}];
        myChart{i}.setOption(option{i});

        // 响应式调整
        window.addEventListener('resize', () => {{
            myChart{i}.resize();
        }});'''

        # 调整图表高度：单图表 500px，多图表 400px
        chart_height = 400 if chart_count > 1 else 500

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self._escape_html(title)}</title>
    <!-- ECharts 国内 CDN (BootCDN) -->
    <script src="https://cdn.bootcdn.net/ajax/libs/echarts/5.4.3/echarts.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .header {{
            background: white;
            padding: 24px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }}

        .header h1 {{
            font-size: 24px;
            color: #333;
            font-weight: 600;
        }}

        .chart-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }}

        .chart-card > div {{
            width: 100%;
            height: {chart_height}px;
        }}

        .advice-card {{
            background: #e8f4fd;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #2196f3;
            margin-bottom: 20px;
        }}

        .advice-card h3 {{
            color: #1976d2;
            margin-bottom: 12px;
            font-size: 18px;
        }}

        .advice-card p {{
            color: #555;
            white-space: pre-wrap;
        }}

        .data-table {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            overflow-x: auto;
        }}

        .data-table h3 {{
            margin-bottom: 16px;
            color: #333;
            font-size: 18px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}

        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
            position: sticky;
            top: 0;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}

            .header, .chart-card, .data-table {{
                padding: 16px;
            }}

            .chart-card > div {{
                height: 350px;
            }}

            table {{
                font-size: 14px;
            }}

            th, td {{
                padding: 8px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{self._escape_html(title)}</h1>
        </div>
{charts_html}{advice_html}{data_table_html}
    </div>

    <script>
        // ECharts 配置
        const echartsConfigs = {echarts_configs};

        // 数据
        const data = {data};
{charts_js}
        // 渲染数据表格
        if (data && data.length > 0) {{
            let tableHtml = '<table><thead><tr>';
            data[0].forEach(h => {{
                tableHtml += '<th>' + escapeHtml(h) + '</th>';
            }});
            tableHtml += '</tr></thead><tbody>';

            data.slice(1).forEach(row => {{
                tableHtml += '<tr>';
                row.forEach(cell => {{
                    tableHtml += '<td>' + escapeHtml(cell) + '</td>';
                }});
                tableHtml += '</tr>';
            }});
            tableHtml += '</tbody></table>';
            document.getElementById('table').innerHTML = tableHtml;
        }}

        // HTML 转义函数
        function escapeHtml(text) {{
            if (text === null || text === undefined) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}
    </script>
</body>
</html>"""

    def _normalize_echarts_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        将简化的 ECharts 配置格式转换为标准格式

        支持的简化格式：
        {"title": "标题", "series": [...]}

        转换为：
        {"title": {"text": "标题"}, "series": [...]}

        Args:
            config: 简化的配置对象

        Returns:
            标准的 ECharts 配置对象
        """
        if not isinstance(config, dict):
            return config

        result = {}

        for key, value in config.items():
            if key == "title" and isinstance(value, str):
                # 将字符串标题转换为 title 对象
                result["title"] = {"text": value, "left": "center", "top": 20}
            elif key == "dataMap" and isinstance(value, dict):
                # 处理 dataMap 格式（如果有 dataset 相关）
                for k, v in value.items():
                    result[k] = v
            else:
                result[key] = value

        # 确保 tooltip 和 legend 存在（对于饼图等）
        if "series" in result and result["series"]:
            series_list = result["series"] if isinstance(result["series"], list) else [result["series"]]
            series = series_list[0] if series_list else {}
            chart_type = series.get("type", "") if isinstance(series, dict) else ""

            # 清理 series 中的无效配置
            if isinstance(series, dict):
                # 移除可能导致问题的 encode 属性（如果数据不匹配）
                if "encode" in series:
                    data = series.get("data", [])
                    if data and not all(isinstance(item, (list, tuple, dict)) for item in data):
                        # 数据包含非结构化类型，移除 encode
                        del series["encode"]

                # 验证并清理 data
                if "data" in series:
                    series["data"] = self._clean_series_data(series["data"], chart_type)

            # 如果没有 tooltip，添加默认的
            if "tooltip" not in result:
                if chart_type == "pie":
                    result["tooltip"] = {"trigger": "item", "formatter": "{b}: {c} ({d}%)"}
                elif chart_type == "gauge":
                    result["tooltip"] = {"formatter": "{b}: {c}%"}
                else:
                    result["tooltip"] = {"trigger": "axis"}

            # 如果是饼图且没有 legend，添加默认的
            if chart_type == "pie" and "legend" not in result:
                result["legend"] = {"orient": "vertical", "left": "left"}

            # 对于柱状图/折线图，确保有完整的坐标轴
            if chart_type in ["bar", "line", "scatter"]:
                # 确保 yAxis 存在（即使已有 xAxis，也要检查 yAxis）
                if "yAxis" not in result:
                    result["yAxis"] = {"type": "value"}

                # 如果没有 xAxis，根据数据生成
                if "xAxis" not in result:
                    data = series.get("data", [])
                    if data and isinstance(data, list):
                        # 检查数据格式
                        has_object_with_name = any(isinstance(item, dict) and "name" in item for item in data)
                        has_array_items = any(isinstance(item, (list, tuple)) for item in data)

                        if has_object_with_name:
                            # 对象格式: [{"name": "A", "value": 10}, ...]
                            categories = [item.get("name") for item in data if isinstance(item, dict) and "name" in item]
                            values = [item.get("value", item.get("y", 0)) for item in data if isinstance(item, dict)]
                            if categories and values:
                                result["xAxis"] = {"type": "category", "data": categories}
                                series["data"] = values
                        elif has_array_items:
                            # 二维数组格式: [["A", 10], ["B", 20]] 或 [[x1, y1], [x2, y2]]
                            has_string_first = any(isinstance(item[0], str) for item in data if isinstance(item, (list, tuple)) and len(item) >= 2)
                            if has_string_first and chart_type != "scatter":
                                # 类别数据: [["A", 10], ["B", 20]]
                                categories = [item[0] for item in data if isinstance(item, (list, tuple)) and len(item) >= 2]
                                values = [item[1] for item in data if isinstance(item, (list, tuple)) and len(item) >= 2]
                                result["xAxis"] = {"type": "category", "data": categories}
                                series["data"] = values
                            else:
                                # 数值坐标数据: [[x1, y1], [x2, y2]]
                                result["xAxis"] = {"type": "value", "scale": True}
                                result["yAxis"] = {"type": "value", "scale": True}
                        elif chart_type == "scatter":
                            # 散点图需要确保有坐标轴
                            result["xAxis"] = {"type": "value", "scale": True}
                            result["yAxis"] = {"type": "value", "scale": True}
                        else:
                            # 纯数值数组或未知格式，添加默认坐标轴
                            result["xAxis"] = {"type": "category", "data": list(range(len(data)))}

                        # 更新 series
                        if isinstance(result["series"], list):
                            result["series"][0] = series
                        else:
                            result["series"] = series

        return result

    def _clean_series_data(self, data, chart_type: str) -> list:
        """
        清理 series 数据，移除无效条目

        Args:
            data: 原始数据
            chart_type: 图表类型

        Returns:
            清理后的数据列表
        """
        if not isinstance(data, list):
            return []

        cleaned = []
        for item in data:
            # 跳过 None 和非结构化数据
            if item is None:
                continue

            # 对于柱状图、折线图：允许数值、对象、数组
            if chart_type in ["bar", "line"]:
                if isinstance(item, (int, float, dict, list, tuple)):
                    # 检查字典是否有效
                    if isinstance(item, dict):
                        if "value" in item or "name" in item or any(k in item for k in ["x", "y"]):
                            cleaned.append(item)
                    elif isinstance(item, (list, tuple)):
                        if len(item) >= 2:
                            cleaned.append(list(item))
                    else:
                        cleaned.append(item)
                # 跳过字符串（可能是标题或其他非数据内容）
                elif isinstance(item, str):
                    continue
            # 对于饼图：必须是对象 {name, value}
            elif chart_type == "pie":
                if isinstance(item, dict) and "name" in item and "value" in item:
                    cleaned.append(item)
            # 对于散点图：必须是 [x, y] 或 {x, y}
            elif chart_type == "scatter":
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    cleaned.append(list(item))
                elif isinstance(item, dict) and "x" in item and "y" in item:
                    cleaned.append(item)
            else:
                # 其他类型：保留有效数据
                if not isinstance(item, str):
                    cleaned.append(item)

        return cleaned if cleaned else []

    def _escape_html(self, text: str) -> str:
        """转义 HTML 特殊字符"""
        if not text:
            return ""
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&#x27;")
        return text
