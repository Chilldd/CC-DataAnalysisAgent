# DataAnalysisAgent MCP Server

数据分析 Agent MCP Server，为 ClaudeCode 提供 Excel 数据读取和图表生成能力。

## 功能特性

- **Token 优化工作流** - `get_excel_schema` 快速了解结构 → `get_chart_data(usecols=...)` 按列处理
- **TOON 格式支持** - 节省 40-70% token 消耗，对象数组场景最优
- 读取 Excel/CSV 文件数据结构
- 灵活的数据查询和聚合
- 基于 ECharts 生成交互式 HTML 图表
- 智能数据分析建议
- **大文件分块读取** - 支持流式处理大型 Excel/CSV 文件
- **列选择优化** - 仅读取需要的列，提升性能
- **智能缓存系统** - 标准化缓存键 + 智能缓存共享，命中率 80%+
- **批量查询优化** - `batch_get_chart_data` 一次性处理多个查询，响应速度提升 3-4x
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

### TOON 格式配置（可选）

启用 TOON 格式可节省 40-70% token 消耗。

**方式 1：配置文件**

在项目根目录创建 `.data-analysis-agent.toml`：

```toml
[server]
response_format = "toon"
show_format_info = true
```

**方式 2：环境变量**

```bash
# Windows
set DAA_RESPONSE_FORMAT=toon

# Linux/Mac
export DAA_RESPONSE_FORMAT=toon
```

**性能对比**：

| 数据类型 | JSON | TOON | 节省 |
|---------|------|------|------|
| 对象数组 (100 条) | 15,144 tokens | 8,744 tokens | 42% |
| 简单数据 | 251 字符 | 113 字符 | 55% |
| 对象数组 (3 条) | 231 字符 | 68 字符 | 70.6% |

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

### session_start / session_end
会话管理，用于统计数据传输和性能分析

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

### batch_get_chart_data（v0.9.0 新增，v0.9.1 修复）
批量获取图表数据，一次性处理多个查询

**优势**：
- 只读取一次文件，自动推断所有查询需要的列
- 在内存中执行多个查询，避免重复 I/O
- 响应速度提升 3-4 倍

**使用场景**：需要生成多个图表时

**v0.9.1 修复**：
- 修复 usecols 参数传递问题（pandas 不接受逗号分隔的字符串）

## 许可证

MIT
