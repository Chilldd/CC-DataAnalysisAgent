# DataAnalysisAgent API 参考

本文档提供详细的 API 参考和代码扩展示例。

> **相关文档**:
> - `DESIGN.md` - 架构设计和 MCP 工具接口
> - `FEATURES.md` - 功能清单和代码位置

---

## 目录

- [日志系统 API](#日志系统-api)
- [批量查询 API](#批量查询-api)
- [缓存优化 API](#缓存优化-api)
- [预加载 API](#预加载-api)
- [扩展开发](#扩展开发)
- [数据格式](#数据格式)

---

## 日志系统 API

**版本**: v0.8.0 新增

### 基本使用

```python
from data_analysis_agent.core import get_logger

logger = get_logger(__name__)
logger.info("这是一条信息")
logger.debug("调试信息")
logger.warning("警告信息")
logger.error("错误信息")
```

### 自定义配置

```python
from data_analysis_agent.core import setup_logging

setup_logging(
    log_level="DEBUG",           # 日志级别
    log_dir="./logs",            # 日志目录
    log_to_file=True,            # 是否写入文件
    log_to_console=True,         # 是否输出到控制台
    max_file_size=10*1024*1024,  # 单个文件最大 10MB
    backup_count=5,              # 保留 5 个备份
    use_time_rotation=True,      # 按天滚动
    enable_metrics=True          # 启用数据传输统计
)
```

### 数据传输指标统计

```python
from data_analysis_agent.core import get_metrics, log_metrics_summary, reset_metrics

# 获取统计摘要
metrics = get_metrics()
summary = metrics.get_summary()
print(summary)
# 输出示例:
# {
#     '总调用次数': 15,
#     '总发送数据': '2.5KB',
#     '总返回数据': '1.2MB',
#     '工具统计': {...},
#     '文件统计': {...}
# }

# 直接输出统计摘要到日志
log_metrics_summary()

# 重置统计
reset_metrics()
```

### 日志文件

配置 `log_to_file=True` 后，将生成以下日志文件：
- `logs/data_analysis_agent.log` - 主日志文件
- `logs/error.log` - 仅包含 ERROR 及以上级别的日志
- `logs/metrics.log` - 指标统计日志

---

## 批量查询 API

**版本**: v0.9.0 新增

### batch_get_chart_data

**参数**:
```typescript
{
  file_path: string;        // Excel 文件路径
  sheet_name?: string;      // 工作表名称（可选）
  usecols?: string;         // 要读取的列（逗号分隔，可选）
  queries: Array<{          // 查询列表
    group_by: string;       // 分组列名（必需）
    aggregation: string;    // 聚合函数（必需）
    aggregate_column?: string;  // 聚合列名（count 时可选）
    filters?: Array<{       // 过滤条件（可选）
      column: string;
      operator: string;
      value: any;
    }>;
    order_by?: string;      // 排序列名（可选）
    order?: "asc" | "desc"; // 排序方向（可选）
    limit?: number;         // 返回的最大分组数（可选）
  }>;
}
```

**返回**:
```json
{
  "success": true,
  "results": [
    {
      "query_index": 0,
      "success": true,
      "data": {...},
      "query_time_ms": 50
    }
  ],
  "summary": {
    "total_queries": 2,
    "successful_queries": 2,
    "read_time_ms": 200,
    "total_query_time_ms": 100,
    "total_time_ms": 300,
    "avg_time_per_query": 150
  }
}
```

**使用示例**:
```python
# 单个工具调用处理多个图表
result = await handle_batch_get_chart_data(
    file_path="sales.xlsx",
    queries=[
        {"group_by": "地区", "aggregation": "sum", "aggregate_column": "销售额"},
        {"group_by": "产品", "aggregation": "count"},
        {"group_by": "月份", "aggregation": "avg", "aggregate_column": "利润"}
    ]
)
# 性能：1 次文件读取 + 3 次内存查询 ≈ 350ms
# vs 3 次独立调用 ≈ 1360ms
```

---

## 缓存优化 API

**版本**: v0.9.0 新增

### 标准化缓存键

缓存键现在自动标准化，确保列顺序不影响缓存命中：

```python
# 这两个调用现在使用相同的缓存键
reader._read_file(usecols=['A', 'B'])
reader._read_file(usecols=['B', 'A'])
# 缓存键格式: "default:cols:A,B"（列名已排序）
```

### 智能缓存共享

当请求列子集时，自动从全量缓存提取：

```python
# 第一次读取全量数据
df_all = reader.read()  # 缓存全量数据

# 第二次读取列子集（自动从缓存提取）
df_subset = reader.read(usecols=['A', 'B'])  # 从全量缓存提取
```

### 缓存统计

```python
info = reader.get_cache_info()
# {
#     'hit_rate': 85.5,           # 命中率（百分比）
#     'cache_hits': 12,           # 命中次数
#     'cache_misses': 2,          # 未命中次数
#     'cache_memory_mb': 2.5,     # 缓存内存占用
#     'data_cache_count': 3       # 缓存条目数
# }
```

---

## 预加载 API

**版本**: v0.10.0 新增

### session_start 预加载参数

**新增参数**：
```typescript
{
  session_name?: string;           // 会话名称（可选）
  preload_files?: string[];        // 预加载文件列表（可选）
  preload_mode?: "metadata" | "full";  // 预加载模式（默认 metadata）
}
```

**返回**：
```json
{
  "success": true,
  "session_id": "session_1234567890",
  "session_name": "数据分析",
  "start_time": 1234567890.123,
  "message": "会话已开始...",
  "preload": {
    "success": true,
    "mode": "metadata",
    "total_files": 2,
    "loaded_count": 2,
    "error_count": 0,
    "total_time_ms": 250.5,
    "files": [...]
  }
}
```

**预加载模式对比**：

| 模式 | 描述 | 速度 | 内存占用 | 适用场景 |
|------|------|------|----------|----------|
| `metadata` | 仅加载元数据 | 极快 (~100ms) | 极低 | 需要先查看数据结构再决定如何分析 |
| `full` | 完整加载数据 | 较快 (~1-3s) | 取决于文件大小 | 已确定要分析所有数据 |

**使用场景**：

```python
# 场景 1：探索性分析（推荐 metadata 模式）
await handle_session_start(
    session_name="销售数据分析",
    preload_files=["sales.xlsx", "products.xlsx"],
    preload_mode="metadata"  # 快速，只加载列信息
)

# 场景 2：已知分析需求（使用 full 模式）
await handle_session_start(
    session_name="月度报表生成",
    preload_files=["monthly_data.xlsx"],
    preload_mode="full"  # 完整加载，后续查询更快
)
```

### ReaderManager.preload_files()

也可以直接调用预加载函数：

```python
from data_analysis_agent.core.reader_manager import preload_files

result = preload_files(
    file_paths=["data1.xlsx", "data2.xlsx"],
    mode="metadata"  # 或 "full"
)
```

---

## 扩展开发

### 添加新工具

**步骤 1**: 创建工具文件 `mcp/tools/new_tool.py`

```python
from mcp.types import Tool, TextContent
import json

tool_definition = Tool(
    name="new_tool",
    description="工具描述",
    inputSchema={
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "参数描述"}
        },
        "required": ["param1"]
    }
)

async def handle_new_tool(param1: str) -> list[TextContent]:
    # 实现工具逻辑
    result = {"success": True, "data": f"处理: {param1}"}
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
```

**步骤 2**: 在 `mcp/server.py` 中注册工具

```python
from .tools.new_tool import tool_definition as new_tool, handle_new_tool

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [..., new_tool]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "new_tool":
        return await handle_new_tool(**arguments)
    # ... 其他工具
```

### ExcelReader 扩展

**文件**: `core/excel_reader.py`

| 扩展 | 方法 | 说明 |
|------|------|------|
| 新文件格式 | `_read_file` | 添加新的文件格式支持 |
| 新聚合函数 | `_group_and_aggregate` | 添加新的聚合函数 |
| 新过滤操作符 | `_apply_filters` | 添加新的过滤操作符 |

#### 支持的聚合函数 (v0.11.0, v0.12.0)

| 类别 | 函数 | 描述 | 是否需要 aggregate_column | 版本 |
|------|------|------|-------------------------|------|
| 基础统计 | sum | 求和 | 是 | - |
| | avg | 平均值 | 是 | - |
| | count | 计数 | 否 (可选) | - |
| | min | 最小值 | 是 | - |
| | max | 最大值 | 是 | - |
| 高级统计 | median | 中位数 | 是 | v0.11.0 |
| | std | 标准差 | 是 | v0.11.0 |
| | var | 方差 | 是 | v0.11.0 |
| 位置值 | first | 第一个值 | 是 | v0.11.0 |
| | last | 最后一个值 | 是 | v0.11.0 |
| 基数统计 | nunique | 唯一值计数 | 否 (可选) | v0.11.0 |
| 百分位数 | percentile25 | 第 25 百分位数 | 是 | v0.12.0 |
| | percentile75 | 第 75 百分位数 | 是 | v0.12.0 |
| | percentile90 | 第 90 百分位数 | 是 | v0.12.0 |
| 模式统计 | mode | 众数 | 是 | v0.12.0 |
| 累计聚合 | cumsum | 累计求和 | 是 | v0.12.0 |
| | cummax | 累计最大值 | 是 | v0.12.0 |
| | cummin | 累计最小值 | 是 | v0.12.0 |
| 移动平均 | rolling_avg | 移动平均 | 是（需 window 参数） | v0.12.0 |

**添加文件格式**:
```python
# 在 _read_file 方法中添加
elif suffix == '.parquet':
    return pd.read_parquet(self.file_path)
```

**添加聚合函数**:
```python
# 在 _group_and_aggregate 方法的 agg_funcs 中添加
agg_funcs = {
    "sum": "sum",
    "avg": "mean",
    "count": "count",
    "min": "min",
    "max": "max",
    "median": "median",      # v0.11.0 新增
    "std": "std",            # v0.11.0 新增
    "var": "var",            # v0.11.0 新增
    "first": "first",        # v0.11.0 新增
    "last": "last",          # v0.11.0 新增
    "nunique": "nunique",    # v0.11.0 新增
    "percentile25": _quantile_q25,  # v0.12.0 新增
    "percentile75": _quantile_q75,  # v0.12.0 新增
    "percentile90": _quantile_q90,  # v0.12.0 新增
    "mode": _mode_func,      # v0.12.0 新增
}
```

**添加过滤操作符**:
```python
# 在 _apply_filters 方法中添加

# v0.12.0 新增操作符
elif op == "in":
    df = df[df[col].isin(val)]
elif op == "not_in":
    df = df[~df[col].isin(val)]
elif op == "is_null":
    df = df[df[col].isna()]
elif op == "is_not_null":
    df = df[df[col].notna()]
elif op == "starts_with":
    df = df[df[col].astype(str).str.startswith(str(val), na=False)]
elif op == "ends_with":
    df = df[df[col].astype(str).str.endswith(str(val), na=False)]
elif op == "regex":
    df = df[df[col].astype(str).str.match(str(val), na=False)]
```

同时更新 `tools/get_chart_data.py` 的 inputSchema。

### ChartRenderer 扩展

**文件**: `core/chart_renderer.py`

修改 `_render_template` 方法的 HTML/CSS/JavaScript 来自定义图表样式。

---

## 数据格式

### 工具返回格式

**成功响应**:
```json
{"success": true, "data": ...}
```

**错误响应**:
```json
{"success": false, "error": "..."}
```

### 表格数据格式

```json
[["列1", "列2"], ["值1", "值2"]]
```

### TOON 格式 (v0.8.0 新增)

TOON (Token-Oriented Object Notation) 是一种节省 token 的数据格式。

**示例**:
```python
# JSON 格式
{"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}

# TOON 格式
# users[2]{id,name}:
#   1,Alice
#   2,Bob
```

**API**:
```python
from data_analysis_agent.core import to_toon, serialize_result, get_response_format, set_response_format

# 序列化为 TOON
toon_str = to_toon(data)

# 带格式标记的序列化
result = serialize_result(data, format_type="toon", show_format=True)

# 检查和设置格式
current_format = get_response_format()
set_response_format("toon")
```

---

## 版本更新流程

1. 更新 `pyproject.toml` 版本号
2. 更新 `DESIGN.md` 版本历史
3. 更新 `FEATURES.md` 功能描述
4. Git tag: `git tag v0.x.0`
