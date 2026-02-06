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
| Config | `core/config.py` | 配置管理（支持 TOML 配置文件、环境变量） |
| ToonSerializer | `core/toon_serializer.py` | TOON 格式序列化（节省 40-70% token） |
| Server | `mcp/server.py` | MCP 协议、工具路由、格式转换 |
| Tools | `mcp/tools/*.py` | 工具实现 |

## MCP 工具

### session_start / session_end（v0.8.0 新增）
会话管理和统计报告
```typescript
// session_start
{ session_name?: string }

// session_end
{ session_id?: string }
```
返回: 会话 ID / 完整统计报告

**特点**：
- 会话生命周期管理
- 自动记录数据传输和性能
- 缓存命中率报告
- 优化建议

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

### MCP Server 配置

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

### TOON 格式配置 (v0.8.0 新增)

支持通过配置文件或环境变量设置返回数据格式。

**配置文件** (`.data-analysis-agent.toml` 或 `~/.config/data-analysis-agent/config.toml`):

```toml
[server]
# 返回数据格式: "json" 或 "toon"
response_format = "toon"

# 是否在输出中显示格式标记（如 ```toon 代码块）
show_format_info = true
```

**环境变量**:

```bash
export DAA_RESPONSE_FORMAT=toon
export DAA_SHOW_FORMAT_INFO=true
```

**TOON 格式优势**:

| 指标 | JSON | TOON | 节省 |
|------|------|------|------|
| 对象数组 (100 条) | 15,144 tokens | 8,744 tokens | 42% |
| 简单数据 | 251 字符 | 113 字符 | 55% |
| 对象数组 (3 条) | 231 字符 | 68 字符 | 70.6% |

**适用场景**:
- **推荐**: 对象数组（如数据库查询结果、聚合数据）
- **不推荐**: 深度嵌套结构（JSON compact 更高效）
- **不推荐**: 纯表格数据（CSV 更小）

## 缓存优化架构 (v0.9.0 新增)

### 三层缓存策略

1. **标准化缓存键** (`_normalize_cache_key`)
   - 列名排序确保一致性：`['A','B']` 和 `['B','A']` 使用相同缓存
   - 缓存键格式：`{sheet}:full` 或 `{sheet}:cols:A,B,C`

2. **智能缓存共享** (`_read_file`)
   - 当请求列子集时，先检查全量缓存
   - 从全量缓存提取所需列，避免重复读取
   - 自动缓存提取的子集供下次使用

3. **批量查询优化** (`batch_get_chart_data`)
   - 一次性处理多个查询
   - 自动推断所有查询需要的列
   - 只读取一次文件，在内存中执行多个查询

### 性能提升

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 缓存命中率 | 20% | 80%+ | 4x |
| 4 次查询响应 | 1.36s | 0.35s | 3.9x |
| 缓存键冲突 | 有 | 无 | ✓ |

### 使用示例

```typescript
// 批量查询（推荐用于多图表场景）
{
  "file_path": "data.xlsx",
  "queries": [
    {"group_by": "地区", "aggregation": "sum", "aggregate_column": "销售额"},
    {"group_by": "产品", "aggregation": "count"}
  ]
}
// 返回: { results: [...], summary: { total_time_ms: 350, avg_time_per_query: 175 } }
```

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 0.8.0 | 2026-02-06 | **TOON 格式支持**：新增 `core/config.py` 配置管理模块；新增 `core/toon_serializer.py` TOON 序列化器；支持通过配置文件或环境变量设置返回格式（JSON/TOON）；TOON 格式可节省 40-70% token；对象数组场景表现最佳（节省约 70%） |
| 0.9.0 | 2026-02-06 | **缓存优化**：新增 `_normalize_cache_key` 标准化缓存键；新增智能缓存共享逻辑；新增 `batch_get_chart_data` 批量查询工具；`get_excel_schema` 支持 `usecols` 参数；缓存命中率提升至 80%+ |
| 0.9.1 | 2026-02-06 | **Bug 修复**：修复 `excel_reader.py` 中 `usecols` 参数未正确传递给 pandas 的问题（原传递字符串而非解析后的列表）；修复 `session_end.py` 中字节解析对带小数点单位的处理（如 "19.1K"） |
| 0.8.0 | 2025-02-05 | **日志系统增强**：新增 `MetricsLogger` 数据传输统计器；自动记录每次工具调用的参数大小、返回数据大小、耗时；支持大数据传输警告（>100KB）；会话统计报告（`session_start`/`session_end`）；新增 `metrics.log` 专门记录指标 |
| 0.7.0 | 2025-02-05 | ~~AI 行为优化：新增 `analyze` 一站式智能分析工具~~（已移除，由 LLM 直接调用底层工具） |
| 0.6.0 | 2025-02-05 | **Token 优化**：新增 `get_excel_schema` 工具（只返回表头+第一行）；`get_chart_data` 支持 `usecols` 参数；推荐工作流：先了解结构→选择列→处理数据 |
| 0.5.0 | 2025-02-05 | 图表优化：默认不显示数据表格（`show_data_table=False`）；支持多图表（`echarts_configs` 数组）；减少数据传输 |
| 0.4.0 | 2025-02-05 | LRU 缓存优化（`max_cache_size` 参数）；多线程读取（`enable_threading`、`read_parallel_chunks`）；缓存统计（`get_cache_info()`）；清空缓存（`clear_cache()`）；MCP 工具：`read_head_excel`、`read_tail_excel` |
| 0.3.0 | 2025-02-05 | 新增缓存机制（文件修改时间检测）；`get_row_count` 快速行数统计；`read_head/tail` 快速读取首尾；`read`/`query` 支持 `usecols` |
| 0.2.0 | 2025-02-05 | 新增 `read_chunked` 大文件分块读取；`get_info` 支持 `usecols` 列选择优化 |
| 0.1.0 | 2025-02-04 | 初始版本 |
