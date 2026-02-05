# DataAnalysisAgent 设计文档

## 架构

```
ClaudeCode → MCP Server → Tools → Core (ExcelReader/ChartRenderer) → Files
```

## 模块

| 模块 | 路径 | 职责 |
|------|------|------|
| ExcelReader | `core/excel_reader.py` | Excel/CSV 读取、查询、聚合、分块读取 |
| ChartRenderer | `core/chart_renderer.py` | 生成 ECharts HTML |
| Server | `mcp/server.py` | MCP 协议、工具路由 |
| Tools | `mcp/tools/*.py` | 工具实现 |

## MCP 工具

### analyze（v0.7.0 新增）
一站式智能数据分析工具
```typescript
{
  file_path: string;
  prompt: string;  // 自然语言分析需求
  sheet_name?: string;
  max_results?: number;  // 默认 50
  include_chart?: boolean;  // 默认 false
}
```
返回: 分析结果 + 数据 + 元信息

**特点**：
- 自然语言驱动，降低使用门槛
- 自动解析分析意图（关键词匹配）
- 一站式完成数据查询和聚合

---

### get_excel_schema（推荐，最小 token）
```typescript
{
  file_path: string;
  sheet_name?: string;
}
```
返回: 列名、第一行数据、总行数、建议的维度/指标列

**推荐工作流**:
1. 先调用 `get_excel_schema` 了解数据结构（最少 token）
2. Claude 选择需要使用的列
3. 调用 `get_chart_data` 时指定 `usecols` 参数，只处理选定的列

### get_excel_info
```typescript
{
  file_path: string;
  sheet_name?: string;
  sample_rows?: number; // 默认 10
  usecols?: string | string[] | number[]; // 列选择，支持列名、列索引列表
}
```
返回: 文件信息、列名/类型、样本数据、列统计

### read_chunked (新增)
```typescript
{
  chunksize?: number; // 每块行数，默认 10000
  sheet_name?: string;
  usecols?: string | string[] | number[];
}
```
返回: TextIterator[DataFrame]，用于流式处理大文件

### generate_chart_html
```typescript
{
  file_path: string;
  echarts_config: object;
  advice?: string;
  title?: string;
  output_path?: string;
  sheet_name?: string;
  data_query?: { filters, group_by, aggregation, aggregate_column, limit };
}
```
返回: HTML 文件路径

### get_chart_data
```typescript
{
  file_path: string;
  usecols?: string; // 要处理的列（减少 token：只读取指定列）
  filters?: Array<{column, operator, value}>;
  group_by?: string;
  aggregation?: "sum" | "avg" | "count" | "min" | "max";
  aggregate_column?: string;
  order_by?: string;
  order?: "asc" | "desc";
  limit?: number;
  sheet_name?: string;
}
```
返回: `[[列1, 列2], [值1, 值2], ...]`

**减少 token**: 使用 `usecols` 参数只读取需要的列

## 支持

- **文件格式**: .xlsx, .xls, .csv
- **聚合函数**: sum, avg, count, min, max
- **过滤操作符**: =, !=, >, <, >=, <=, contains
- **列类型**: object→string, int/float→number, datetime64→datetime, bool→boolean

## 配置

```json
{
  "mcpServers": {
    "data-analysis-agent": {
      "command": "python",
      "args": ["-m", "data_analysis_agent"],
      "cwd": "D:\\WorkSpace\\AI\\DataAnalysisAgent"
    }
  }
}
```

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 0.8.0 | 2025-02-05 | **日志系统增强**：新增 `MetricsLogger` 数据传输统计器；自动记录每次工具调用的参数大小、返回数据大小、耗时；支持大数据传输警告（>100KB）；定期输出统计摘要（每 5 次调用）；新增 `metrics.log` 专门记录指标 |
| 0.7.0 | 2025-02-05 | **AI 行为优化**：所有工具描述添加「优先使用此工具，不要编写 Python 脚本」引导提示；新增 `analyze` 一站式智能分析工具（自然语言驱动） |
| 0.6.0 | 2025-02-05 | **Token 优化**：新增 `get_excel_schema` 工具（只返回表头+第一行）；`get_chart_data` 支持 `usecols` 参数；推荐工作流：先了解结构→选择列→处理数据 |
| 0.5.0 | 2025-02-05 | 图表优化：默认不显示数据表格（`show_data_table=False`）；支持多图表（`echarts_configs` 数组）；减少数据传输 |
| 0.4.0 | 2025-02-05 | LRU 缓存优化（`max_cache_size` 参数）；多线程读取（`enable_threading`、`read_parallel_chunks`）；缓存统计（`get_cache_info()`）；清空缓存（`clear_cache()`）；MCP 工具：`read_head_excel`、`read_tail_excel` |
| 0.3.0 | 2025-02-05 | 新增缓存机制（文件修改时间检测）；`get_row_count` 快速行数统计；`read_head/tail` 快速读取首尾；`read`/`query` 支持 `usecols` |
| 0.2.0 | 2025-02-05 | 新增 `read_chunked` 大文件分块读取；`get_info` 支持 `usecols` 列选择优化 |
| 0.1.0 | 2025-02-04 | 初始版本 |
