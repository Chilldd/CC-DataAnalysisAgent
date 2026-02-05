# DataAnalysisAgent MCP Server

数据分析 Agent MCP Server，为 ClaudeCode 提供 Excel 数据读取和图表生成能力。

## 功能特性

- **Token 优化工作流** - `get_excel_schema` 快速了解结构 → `get_chart_data(usecols=...)` 按列处理
- 读取 Excel/CSV 文件数据结构
- 灵活的数据查询和聚合
- 基于 ECharts 生成交互式 HTML 图表
- 智能数据分析建议
- **大文件分块读取** - 支持流式处理大型 Excel/CSV 文件
- **列选择优化** - 仅读取需要的列，提升性能
- **LRU 智能缓存** - 基于文件修改时间的自动缓存机制，支持缓存大小限制
- **多线程读取** - 支持 `read_parallel_chunks()` 并行读取大文件
- **缓存统计** - `get_cache_info()` 获取缓存命中率、内存占用等统计
- **清空缓存** - `clear_cache()` 手动清空所有缓存
- **快速统计** - `get_row_count()` 快速获取行数
- **首尾读取** - `read_head()` / `read_tail()` 快速查看文件开头/结尾
- **日志系统** - 统一的日志管理，支持控制台彩色输出和文件日志
- **数据传输统计** - 自动记录每次工具调用的数据大小和耗时，支持优化分析

## 安装

```bash
pip install -e .
```

## 配置 ClaudeCode

在 `%APPDATA%\Claude\claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "data-analysis-agent": {
      "command": "python",
      "args": ["-m", "data_analysis_agent"]
    }
  }
}
```

## 使用示例

```
用户: 分析 D:/data/sales.xlsx 中各地区销售额趋势

Claude 将自动（推荐工作流）：
1. 调用 get_excel_schema 快速了解数据结构（最少 token）
2. 选择需要使用的列
3. 调用 get_chart_data(usecols=[...]) 按列聚合数据
4. 调用 generate_chart_html 生成完整 HTML
5. 提供分析建议
```

## 工具说明

### analyze（推荐）
一站式智能数据分析，自然语言驱动

**特点**：
- 用自然语言描述分析需求，自动解析并执行
- 自动检测分组列、聚合类型、聚合列
- 比自行编写脚本更高效、更安全

**示例**：
- "分析各地区销售额排名"
- "统计每个产品类别的平均价格"

### get_excel_schema（推荐）
快速获取 Excel 数据结构，最小 token 消耗

**返回**：列名、第一行数据、总行数、建议的维度/指标列

**推荐工作流**：
1. 调用 `get_excel_schema` 了解数据结构
2. Claude 选择需要使用的列
3. 调用 `get_chart_data(usecols=...)` 按列处理数据

### get_excel_info
获取 Excel 文件的结构信息和样本数据（包含更多统计信息）

### generate_chart_html
基于 ECharts 配置和 Excel 数据生成完整的 HTML 图表文件

**v0.5.0 新增**：
- 支持多图表（`echarts_configs` 数组）
- 默认不显示数据表格（`show_data_table=False`），减少数据传输
- 可通过 `show_data_table=True` 显示数据表格

### get_chart_data
从 Excel 文件中查询和聚合数据，用于图表渲染

**v0.6.0 新增**：
- `usecols` 参数支持列选择，减少 token 消耗

## 许可证

MIT
