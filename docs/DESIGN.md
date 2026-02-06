# DataAnalysisAgent 设计文档

## 架构概览

```
ClaudeCode → MCP Server → Tools → Core (ExcelReader/ChartRenderer) → Files
```

## 模块结构

| 模块 | 路径 | 职责 |
|------|------|------|
| ExcelReader | `core/excel_reader.py` | Excel/CSV 读取、查询、聚合、分块读取 |
| ChartRenderer | `core/chart_renderer.py` | 生成 ECharts HTML |
| Config | `core/config.py` | 配置管理（TOML 配置文件、环境变量） |
| ToonSerializer | `core/toon_serializer.py` | TOON 格式序列化（节省 40-70% token） |
| ReaderManager | `core/reader_manager.py` | 读取器管理、预加载、缓存协调 |
| MetricsLogger | `core/metrics_logger.py` | 数据传输统计、性能监控 |
| LoggingConfig | `core/logging_config.py` | 日志管理、控制台彩色输出、文件日志 |
| Server | `mcp/server.py` | MCP 协议、工具路由、格式转换 |
| Tools | `mcp/tools/*.py` | 工具实现 |

## MCP 工具接口

### session_start / session_end

**版本**: v0.8.0 新增，v0.10.0 优化

**接口定义**:
```typescript
// session_start
{
  session_name?: string;           // 会话名称
  preload_files?: string[];        // v0.10.0: 预加载文件列表
  preload_mode?: "metadata" | "full";  // v0.10.0: 预加载模式
}

// session_end
{
  session_id?: string;             // 会话 ID（可选）
}
```

**返回**: 会话 ID / 完整统计报告

**特性**:
- 会话生命周期管理
- 自动记录数据传输和性能
- 缓存命中率报告
- 优化建议

**预加载模式**:
| 模式 | 描述 | 速度 | 内存占用 | 适用场景 |
|------|------|------|----------|----------|
| `metadata` | 仅加载元数据（sheet 名称、列信息、前 5 行） | 极快 (~100ms) | 极低 | 探索性分析，先查看结构再决定 |
| `full` | 完整加载数据并缓存 | 较快 (~1-3s) | 取决于文件大小 | 已确定要分析所有数据 |

**性能提升**:
| 场景 | 无预加载 | 预加载 metadata | 提升 |
|------|---------|-----------------|------|
| 首次调用 `get_excel_schema` | ~3000ms | ~5ms | **600x** |

---

### get_excel_schema

**版本**: v0.6.0 新增（推荐使用）

**接口定义**:
```typescript
{
  file_path: string;
  sheet_name?: string;
}
```

**返回**: 列名、第一行数据、总行数、建议的维度/指标列

**推荐工作流**:
1. 调用 `get_excel_schema` 了解数据结构（最少 token）
2. Claude 选择需要使用的列
3. 调用 `get_chart_data(usecols=...)` 按列处理数据

---

### get_excel_info

**接口定义**:
```typescript
{
  file_path: string;
  sheet_name?: string;
  sample_rows?: number;        // 默认 10
  usecols?: string | string[] | number[];  // 列选择
}
```

**返回**: 文件信息、列名/类型、样本数据、列统计

---

### read_head_excel / read_tail_excel

**版本**: v0.4.0 新增

**接口定义**:
```typescript
{
  file_path: string;
  n?: number;                  // 默认 5
  sheet_name?: string;
}
```

**返回**: 前/后 n 行数据

---

### generate_chart_html

**接口定义**:
```typescript
{
  file_path: string;
  echarts_configs: object[];    // v0.5.0: 支持多图表数组
  title?: string;
  output_path?: string;
  sheet_name?: string;
  data_query?: {                // 可选的数据查询
    filters, group_by, aggregation, aggregate_column, limit
  };
}
```

**返回**: HTML 文件路径

**v0.10.1 变更**: 移除 `show_data_table` 参数，强制不显示数据表格

---

### get_chart_data

**接口定义**:
```typescript
{
  file_path: string;
  usecols?: string;             // v0.6.0: 列选择优化
  filters?: Array<{
    column: string;
    operator: string;           // v0.12.0: 支持 in, not_in, is_null, is_not_null, starts_with, ends_with, regex
    value: any;
  }>;
  group_by?: string;
  aggregation?: "sum" | "avg" | "count" | "min" | "max" | "median" | "std" | "var" | "first" | "last" | "nunique" | "percentile25" | "percentile75" | "percentile90" | "mode" | "cumsum" | "cummax" | "cummin" | "rolling_avg";  // v0.11.0, v0.12.0
  aggregate_column?: string;
  order_by?: string;
  order?: "asc" | "desc";
  limit?: number;
  sheet_name?: string;
  window?: number;              // v0.12.0: rolling_avg 的窗口大小
}
```

**返回**: `[[列1, 列2], [值1, 值2], ...]`

---

### batch_get_chart_data

**版本**: v0.9.0 新增

**接口定义**:
```typescript
{
  file_path: string;
  sheet_name?: string;
  usecols?: string;
  queries: Array<{
    group_by: string;
    aggregation: string;
    aggregate_column?: string;
    filters?: Array<{...}>;
    order_by?: string;
    order?: "asc" | "desc";
    limit?: number;
  }>;
}
```

**返回**:
```json
{
  "success": true,
  "results": [...],
  "summary": {
    "total_queries": 2,
    "read_time_ms": 200,
    "total_time_ms": 300,
    "avg_time_per_query": 150
  }
}
```

**性能**: 4 个查询 1.36s → 0.35s (3.9x)

---

## 支持的数据操作

### 文件格式
- .xlsx, .xls, .csv

### 聚合函数
| 函数 | 描述 | 位置 |
|------|------|------|
| sum | 求和 | `core/excel_reader.py:_group_and_aggregate` |
| avg | 平均值 | 同上 |
| count | 计数 | 同上 |
| min | 最小值 | 同上 |
| max | 最大值 | 同上 |
| median | 中位数 | 同上 (v0.11.0) |
| std | 标准差 | 同上 (v0.11.0) |
| var | 方差 | 同上 (v0.11.0) |
| first | 第一個值 | 同上 (v0.11.0) |
| last | 最後一個值 | 同上 (v0.11.0) |
| nunique | 唯一值计数 | 同上 (v0.11.0) |
| percentile25 | 第 25 百分位数 | 同上 (v0.12.0) |
| percentile75 | 第 75 百分位数 | 同上 (v0.12.0) |
| percentile90 | 第 90 百分位数 | 同上 (v0.12.0) |
| mode | 众数 | 同上 (v0.12.0) |
| cumsum | 累计求和 | 同上 (v0.12.0) |
| cummax | 累计最大值 | 同上 (v0.12.0) |
| cummin | 累计最小值 | 同上 (v0.12.0) |
| rolling_avg | 移动平均（需 window 参数） | 同上 (v0.12.0) |

### 过滤操作符
| 操作符 | 描述 | 位置 |
|--------|------|------|
| = | 等于 | `core/excel_reader.py:_apply_filters` |
| != | 不等于 | 同上 |
| >, <, >=, <= | 比较 | 同上 |
| contains | 包含字符串 | 同上 |
| starts_with | 以...开头 | 同上 (v0.12.0) |
| ends_with | 以...结尾 | 同上 (v0.12.0) |
| regex | 正则表达式匹配 | 同上 (v0.12.0) |
| in | 在列表中 | 同上 (v0.12.0) |
| not_in | 不在列表中 | 同上 (v0.12.0) |
| is_null | 为空 | 同上 (v0.12.0) |
| is_not_null | 不为空 | 同上 (v0.12.0) |

### 列类型映射
```
object   → string
int64/int32  → number
float64/float32 → number
datetime64[ns] → datetime
bool     → boolean
```

## 配置

### MCP Server 配置

文件: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "data-analysis-agent": {
      "command": "python",
      "args": ["-m", "data_analysis_agent"],
      "cwd": "D:\\WorkSpace\\AI\\CC-DataAnalysisAgent"
    }
  }
}
```

### TOON 格式配置

**版本**: v0.8.0 新增

支持通过配置文件或环境变量设置返回数据格式。

**配置文件**: `.data-analysis-agent.toml` 或 `~/.config/data-analysis-agent/config.toml`

```toml
[server]
response_format = "toon"      # "json" 或 "toon"
show_format_info = true       # 是否显示格式标记
```

**环境变量**:
```bash
export DAA_RESPONSE_FORMAT=toon
export DAA_SHOW_FORMAT_INFO=true
```

**性能对比**:
| 数据类型 | JSON | TOON | 节省 |
|---------|------|------|------|
| 对象数组 (100 条) | 15,144 tokens | 8,744 tokens | 42% |
| 对象数组 (3 条) | 231 字符 | 68 字符 | 70.6% |
| 简单数据 | 251 字符 | 113 字符 | 55% |

**适用场景**:
- ✅ **推荐**: 对象数组（数据库查询结果、聚合数据）
- ❌ **不推荐**: 深度嵌套结构（JSON compact 更高效）
- ❌ **不推荐**: 纯表格数据（CSV 更小）

---

## 缓存优化架构

**版本**: v0.9.0 优化

### 三层缓存策略

1. **标准化缓存键** (`_normalize_cache_key`)
   - 列名排序确保一致性
   - 缓存键格式: `{sheet}:full` 或 `{sheet}:cols:A,B,C`

2. **智能缓存共享** (`_read_file`)
   - 从全量缓存提取列子集
   - 避免重复读取文件

3. **批量查询优化** (`batch_get_chart_data`)
   - 一次性推断所有查询需要的列
   - 内存中执行多个查询

### 性能提升

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 缓存命中率 | 20% | 80%+ | 4x |
| 4 次查询响应 | 1.36s | 0.35s | 3.9x |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| **0.12.0** | 2026-02-06 | **功能增强**：扩展过滤操作符，新增 in、not_in、is_null、is_not_null、starts_with、ends_with、regex；扩展聚合函数进阶，新增 percentile25/75/90（百分位数）、mode（众数）、cumsum/cummax/cummin（累计聚合）、rolling_avg（移动平均，需 window 参数） |
| **0.11.0** | 2026-02-06 | **功能增强**：扩展聚合函数，新增 median（中位数）、std（标准差）、var（方差）、first（第一个值）、last（最后一个值）、nunique（唯一值计数）；count 和 nunique 支持不指定 aggregate_column |
| **0.10.1** | 2026-02-06 | **Bug 修复**：修复 metadata 预加载模式导致数据只有 1 行的问题；`preload_files()` 在 metadata 模式下使用 `read_head(n=5)` 获取样本并清除缓存；移除 `generate_chart_html` 的 `show_data_table` 参数，强制不显示数据表格 |
| **0.10.0** | 2026-02-06 | **首次加载优化**：`session_start` 新增 `preload_files` 参数；新增 `preload_mode` 参数（metadata/full）；`ReaderManager` 新增 `preload_files()` 方法；首次调用 `get_excel_schema` 性能提升 600 倍 |
| **0.9.1** | 2026-02-06 | **Bug 修复**：修复 `usecols` 参数未正确传递给 pandas 的问题；修复字节解析对带小数点单位的处理 |
| **0.9.0** | 2026-02-06 | **缓存优化**：新增标准化缓存键；智能缓存共享；新增 `batch_get_chart_data` 工具；`get_excel_schema` 支持 `usecols` 参数；缓存命中率提升至 80%+ |
| **0.8.0** | 2025-02-05 | **日志系统增强**：新增 `MetricsLogger`；自动记录数据传输和性能；支持大数据传输警告；会话统计报告；新增 `metrics.log` |
| **0.6.0** | 2025-02-05 | **Token 优化**：新增 `get_excel_schema` 工具；`get_chart_data` 支持 `usecols` 参数；推荐工作流：了解结构 → 选择列 → 处理数据 |
| **0.5.0** | 2025-02-05 | 图表优化：默认不显示数据表格；支持多图表（`echarts_configs` 数组） |
| **0.4.0** | 2025-02-05 | LRU 缓存优化；多线程读取；缓存统计；清空缓存；新增 `read_head_excel`、`read_tail_excel` 工具 |
| **0.3.0** | 2025-02-05 | 新增缓存机制；`get_row_count` 快速行数统计；`read_head/tail` 快速读取首尾 |
| **0.2.0** | 2025-02-05 | 新增 `read_chunked` 大文件分块读取；`get_info` 支持 `usecols` |
| **0.1.0** | 2025-02-04 | 初始版本 |
