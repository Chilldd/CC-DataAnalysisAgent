# DataAnalysisAgent API 参考

## 日志系统 (v0.8.0 新增)

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

# 配置日志系统
setup_logging(
    log_level="DEBUG",           # 日志级别
    log_dir="./logs",            # 日志目录
    log_to_file=True,            # 是否写入文件
    log_to_console=True,         # 是否输出到控制台
    max_file_size=10*1024*1024,  # 单个文件最大 10MB
    backup_count=5,              # 保留 5 个备份
    use_time_rotation=True,      # 按天滚动（False 则按大小滚动）
    enable_metrics=True          # 启用数据传输统计
)
```

### 数据传输指标统计

日志系统自动记录所有工具调用的数据传输量，用于分析和优化：

```python
from data_analysis_agent.core import get_metrics, log_metrics_summary, reset_metrics

# 获取指标记录器
metrics = get_metrics()

# 获取统计摘要
summary = metrics.get_summary()
print(summary)
# 输出示例:
# {
#     '总调用次数': 15,
#     '总发送数据': '2.5KB',
#     '总返回数据': '1.2MB',
#     '工具统计': {
#         'get_chart_data': {
#             '调用次数': 8,
#             '平均返回大小': '150.0KB',
#             '总返回大小': '1.2MB',
#             '平均耗时': '125ms',
#             '错误数': 0
#         },
#         ...
#     },
#     '文件统计': {
#         'data.xlsx': {
#             '读取次数': 10,
#             '总数据量': '500.0KB',
#             '缓存命中率': '80.0%'
#         }
#     }
# }

# 直接输出统计摘要到日志
log_metrics_summary()

# 重置统计
reset_metrics()
```

### 在扩展模块中使用

```python
from data_analysis_agent.core import get_logger, get_metrics

logger = get_logger(__name__)
metrics = get_metrics()

class MyCustomReader:
    def __init__(self, file_path):
        logger.info(f"初始化 MyCustomReader: {file_path}")

    def read_data(self):
        logger.debug("开始读取数据")
        start_time = time.time()
        try:
            # 数据读取逻辑
            data = self._do_read()

            # 记录操作指标
            duration_ms = (time.time() - start_time) * 1000
            result_size = len(json.dumps(data))

            logger.info(f"数据读取完成: {self._format_bytes(result_size)}, 耗时: {duration_ms:.0f}ms")

            return data
        except Exception as e:
            logger.error(f"读取失败: {e}", exc_info=True)
            raise
```

### 日志文件

配置 `log_to_file=True` 后，将生成以下日志文件：
- `logs/data_analysis_agent.log` - 主日志文件
- `logs/error.log` - 仅包含 ERROR 及以上级别的日志
- `logs/metrics.log` - 指标统计日志（数据传输量、耗时等）
- 滚动备份文件（如 `data_analysis_agent.log.2025-02-04`）

### 日志输出示例

```
[REQUEST] 工具: get_chart_data | 参数: {"file_path":"data.xlsx","group_by":"地区","aggregation":"sum"}
[RESPONSE] 工具: get_chart_data | 返回大小: 15.2KB | 耗时: 120ms
[METRICS] 工具调用: get_chart_data | 参数: {...} | 返回大小: 15.2KB | 耗时: 120ms | 成功: True
[METRICS] ===== 数据传输统计摘要 =====
[METRICS] 总调用次数: 5
[METRICS] 总发送数据: 1.2KB
[METRICS] 总返回数据: 850.5KB
[METRICS] --- 工具详情 ---
[METRICS]   get_chart_data: 调用3次, 平均返回170.1KB, 平均耗时115ms
[METRICS]   get_excel_schema: 调用2次, 平均返回2.5KB, 平均耗时45ms
[METRICS] =============================
```

---

## 扩展点

### 添加新工具

**文件**: `mcp/server.py`

```python
from .tools.new_tool import tool_definition as new_tool, handle_new_tool

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [info_tool, chart_tool, data_tool, new_tool]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "new_tool":
        return await handle_new_tool(**arguments)
```

**文件**: `mcp/tools/new_tool.py`

```python
from mcp.types import Tool, TextContent
import json

tool_definition = Tool(
    name="new_tool",
    description="工具描述",
    inputSchema={"type": "object", "properties": {...}, "required": [...]}
)

async def handle_new_tool(...) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps({"success": True, "data": ...}))]
```

### ExcelReader 扩展

**文件**: `core/excel_reader.py`

| 扩展 | 方法 | 行号 |
|------|------|------|
| 新文件格式 | `_read_file` | 316 |
| 新聚合函数 | `_group_and_aggregate` | 437 |
| 新过滤操作符 | `_apply_filters` | 411 |
| 大文件分块读取 | `read_chunked` | 143 |
| 多线程并行读取 | `read_parallel_chunks` | 200 |
| 列选择优化 | `get_info`, `_read_file`, `read`, `query` | 29, 316, 68, 91 |
| LRU 缓存机制 | `_read_file`, `__init__` | 13, 316 |
| 缓存统计 | `get_cache_info` | 435 |
| 清空缓存 | `clear_cache` | 420 |
| 快速行数统计 | `get_row_count` | 184 |
| 首尾读取 | `read_head`, `read_tail` | 230, 268 |

**添加文件格式**:
```python
elif suffix == '.parquet':
    return pd.read_parquet(self.file_path)
```

**添加聚合函数**:
```python
agg_funcs = {"sum": "sum", "avg": "mean", "new_func": "pandas_func"}
```

**添加过滤操作符**:
```python
elif op == "in":
    df = df[df[col].isin(val)]
```

同时更新 `tools/get_chart_data.py` 的 inputSchema。

### ChartRenderer 扩展

**文件**: `core/chart_renderer.py`

修改 `_render_template` 方法的 HTML/CSS/JavaScript。

## 数据格式

**工具返回**:
```json
{"success": true, "data": ...} 或 {"success": false, "error": "..."}
```

**表格数据**:
```json
[["列1", "列2"], ["值1", "值2"]]
```

## 版本更新

1. 更新 `pyproject.toml` 版本号
2. 更新 `DESIGN.md` 版本历史
3. Git tag: `git tag v0.x.0`
