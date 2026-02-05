# DataAnalysisAgent 功能清单

## MCP 工具

### analyze（推荐，v0.7.0 新增）
一站式智能数据分析工具，自然语言驱动

| 项 | 位置 |
|---|---|
| 工具定义 | `mcp/tools/analyze.py` |
| 核心类 | `ExcelReader.query()` |

**特点**：
- 接受自然语言分析需求
- 自动解析分组列、聚合类型、聚合列
- 返回结构化分析结果

**使用场景**：
- 快速数据分析："分析各地区销售额排名"
- 自动统计："统计每个产品类别的平均价格"

---

### get_excel_schema（推荐，v0.6.0 新增）
快速获取 Excel 数据结构，最小 token 消耗

| 项 | 位置 |
|---|---|
| 工具定义 | `mcp/tools/get_excel_schema.py` |
| 核心类 | `ExcelReader._read_file()` |

**返回**：列名、第一行数据、总行数、建议的维度/指标列

**推荐工作流**：
1. 调用 `get_excel_schema` 了解数据结构
2. Claude 选择需要使用的列
3. 调用 `get_chart_data(usecols=...)` 按列处理数据

---

### get_excel_info
获取 Excel/CSV 文件的结构信息和样本数据

| 项 | 位置 |
|---|---|
| 工具定义 | `mcp/tools/get_excel_info.py` |
| 核心类 | `ExcelReader.get_info()` |
| 文件读取 | `ExcelReader._read_file()` |
| 列类型检测 | `ExcelReader._get_column_types()` |
| 列统计 | `ExcelReader._get_column_stats()` |

**修改**: 要修改返回的数据结构，编辑 `get_info()` 方法

**v0.2.0 新增**:
- `usecols` 参数支持列选择，提升大文件性能

---

### generate_chart_html
基于 ECharts 配置生成完整的 HTML 图表文件

| 项 | 位置 |
|---|---|
| 工具定义 | `mcp/tools/generate_chart_html.py` |
| 核心类 | `ChartRenderer.generate_html()` |
| HTML 模板 | `ChartRenderer._render_template()` |
| HTML 转义 | `ChartRenderer._escape_html()` |

**修改**:
- HTML 样式: 编辑 `_render_template()` 中的 `<style>` 部分
- ECharts 版本: 修改 CDN 链接
- 默认主题: 修改模板中的配色

**v0.5.0 更新**:
- `show_data_table` 参数控制是否显示数据表格（默认 False）
- `echarts_configs` 参数支持多图表数组
- 数据仅在 `show_data_table=True` 时读取，减少 AI 传输数据量

---

### read_head_excel
快速读取 Excel 文件前 n 行数据

| 项 | 位置 |
|---|---|
| 工具定义 | `mcp/tools/read_head_excel.py` |
| 核心类 | `ExcelReader.read_head()` |
| 文件读取 | `ExcelReader._read_file()` |

**v0.4.0 新增**

---

### read_tail_excel
快速读取 Excel 文件后 n 行数据

| 项 | 位置 |
|---|---|
| 工具定义 | `mcp/tools/read_tail_excel.py` |
| 核心类 | `ExcelReader.read_tail()` |
| 文件读取 | `ExcelReader._read_file()` |

**v0.4.0 新增**

---

### get_chart_data
查询和聚合数据用于图表渲染

| 项 | 位置 |
|---|---|
| 工具定义 | `mcp/tools/get_chart_data.py` |
| 核心类 | `ExcelReader.query()` |
| 过滤条件 | `ExcelReader._apply_filters()` |
| 分组聚合 | `ExcelReader._group_and_aggregate()` |
| 数据转换 | `ExcelReader._df_to_array()` |

**修改**:
- 新增过滤操作符: 编辑 `_apply_filters()` 方法
- 新增聚合函数: 编辑 `_group_and_aggregate()` 方法
- 同时更新工具的 `inputSchema`

**v0.6.0 新增**:
- `usecols` 参数支持列选择，减少 token 消耗

---

## 核心功能

### 大文件分块读取 (v0.2.0 新增)
支持流式处理大型 Excel/CSV 文件

| 项 | 位置 |
|---|---|
| 方法 | `ExcelReader.read_chunked()` |
| 行号 | ~143 |

**使用示例**:
```python
reader = ExcelReader("large_file.xlsx")
for chunk in reader.read_chunked(chunksize=5000):
    # 处理每个数据块
    process_chunk(chunk)
```

---

### 智能缓存机制 (v0.3.0 新增, v0.4.0 升级)
基于文件修改时间的自动缓存，避免重复读取。v0.4.0 新增 LRU 策略和缓存大小限制。

| 项 | 位置 |
|---|---|
| 配置 | `ExcelReader.__init__(enable_cache=True, max_cache_size=10)` |
| 缓存存储 | `_cache`, `_row_count_cache` (OrderedDict) |
| LRU 清理 | `_read_file()` |
| 行号 | ~13, ~316 |

**使用示例**:
```python
# 启用缓存（默认），设置最大缓存条目数
reader = ExcelReader("data.xlsx", max_cache_size=20)
data1 = reader.read()  # 第一次读取，从文件加载
data2 = reader.read()  # 第二次读取，从缓存获取（文件未修改）

# 获取缓存统计
info = reader.get_cache_info()
print(f"命中率: {info['hit_rate']}%, 内存: {info['cache_memory_mb']}MB")

# 清空缓存
reader.clear_cache()

# 禁用缓存
reader = ExcelReader("data.xlsx", enable_cache=False)
```

---

### 多线程读取 (v0.4.0 新增)
并行读取多个数据块，加速大文件处理

| 项 | 位置 |
|---|---|
| 方法 | `ExcelReader.read_parallel_chunks()` |
| 配置 | `ExcelReader.__init__(enable_threading=True)` |
| 行号 | ~200 |

**使用示例**:
```python
# 启用多线程
reader = ExcelReader("large_file.xlsx", enable_threading=True)

# 并行读取 4 个数据块
chunks = reader.read_parallel_chunks(chunksize=10000, num_chunks=4)
df_combined = pd.concat(chunks, ignore_index=True)
```

---

### 快速行数统计 (v0.3.0 新增)
不加载全部数据，快速获取文件行数

| 项 | 位置 |
|---|---|
| 方法 | `ExcelReader.get_row_count()` |
| 行号 | ~184 |

**使用示例**:
```python
reader = ExcelReader("large_file.xlsx")
count = reader.get_row_count()  # 快速获取行数，不加载全部数据
print(f"文件有 {count} 行数据")
```

---

### 首尾快速读取 (v0.3.0 新增)
快速读取文件开头或结尾的几行数据

| 项 | 位置 |
|---|---|
| 方法 | `ExcelReader.read_head()`, `ExcelReader.read_tail()` |
| 行号 | ~230, ~268 |

**使用示例**:
```python
reader = ExcelReader("data.xlsx")
head = reader.read_head(n=5)   # 读取前5行
tail = reader.read_tail(n=5)   # 读取后5行
```

---

### 日志系统 (v0.8.0 新增)
统一的日志管理，支持控制台彩色输出和文件日志

| 项 | 位置 |
|---|---|
| 模块 | `core/logging_config.py` |
| 导出 | `core/__init__.py` |

**特性**：
- 控制台彩色日志输出（级别不同颜色不同）
- 文件日志支持按时间/大小滚动
- 错误日志单独记录到 `error.log`
- **指标日志单独记录到 `metrics.log`**
- **数据传输量统计**（自动记录每次工具调用的数据大小）
- **性能监控**（记录每次工具调用的耗时）
- 可动态调整日志级别
- 支持按命名空间获取 Logger

**使用示例**:
```python
from data_analysis_agent.core import (
    get_logger, setup_logging,
    get_metrics, log_metrics_summary, reset_metrics
)

# 使用默认配置（仅控制台，INFO 级别）
logger = get_logger(__name__)
logger.info("这是一条信息")
logger.error("这是一条错误")

# 自定义配置
setup_logging(
    log_level="DEBUG",
    log_dir="./logs",
    log_to_file=True,
    log_to_console=True,
    use_time_rotation=True  # 按天滚动
)

# 获取统计摘要
metrics = get_metrics()
summary = metrics.get_summary()
print(summary)
# 或直接输出到日志
log_metrics_summary()

# 重置统计
reset_metrics()
```

**日志级别**：
- DEBUG：详细调试信息
- INFO：一般信息（文件读取、缓存操作、工具调用）
- WARNING：警告信息（大数据传输警告 >100KB）
- ERROR：错误信息（文件不存在、工具执行错误）
- CRITICAL：严重错误

**自动记录的指标**：
- 每次工具调用的参数大小
- 每次工具调用的返回数据大小
- 每次工具调用的耗时
- 文件读取的数据量和缓存命中情况
- 每 5 次工具调用自动输出统计摘要

---

### 文件读取
支持 .xlsx, .xls, .csv 格式

| 项 | 位置 |
|---|---|
| 方法 | `ExcelReader._read_file()` |
| 行号 | ~129 |

**新增格式**: 在该方法中添加新的 `elif` 分支

---

### 数据查询
支持过滤、分组聚合、排序、限制行数

| 项 | 位置 |
|---|---|
| 方法 | `ExcelReader.query()` |
| 行号 | ~77 |

**修改**: 调整查询逻辑或参数

---

### 聚合函数
支持: sum, avg, count, min, max

| 项 | 位置 |
|---|---|
| 方法 | `ExcelReader._group_and_aggregate()` |
| 行号 | ~222 |

**新增函数**: 在 `agg_funcs` 字典中添加

---

### 过滤操作符
支持: =, !=, >, <, >=, <=, contains

| 项 | 位置 |
|---|---|
| 方法 | `ExcelReader._apply_filters()` |
| 行号 | ~196 |

**新增操作符**: 添加新的 `elif` 分支，同时更新 `get_chart_data.py` 的 `inputSchema`

---

### HTML 图表生成
生成包含 ECharts 和数据表格的完整 HTML

| 项 | 位置 |
|---|---|
| 方法 | `ChartRenderer.generate_html()` |
| 模板 | `ChartRenderer._render_template()` |
| 行号 | ~12, ~47 |

**修改**: 编辑模板字符串中的 HTML/CSS/JavaScript

---

### 数据格式转换
将 DataFrame 转换为 JSON 可序列化的二维数组

| 项 | 位置 |
|---|---|
| 方法 | `ExcelReader._df_to_array()` |
| 行号 | ~144 |

**修改**: 调整数据转换逻辑（如 datetime 处理）

---

## 类型系统

### 列类型映射
```
object → string
int64/int32 → number
float64/float32 → number
datetime64[ns] → datetime
bool → boolean
```

| 项 | 位置 |
|---|---|
| 方法 | `ExcelReader._get_column_types()` |
| 行号 | ~156 |

**修改**: 添加新的类型映射

---

## MCP 协议

### Server 实现
MCP 服务器主入口

| 项 | 位置 |
|---|---|
| 文件 | `mcp/server.py` |
| 列出工具 | `@server.list_tools()` |
| 调用工具 | `@server.call_tool()` |

**新增工具**:
1. 在 `mcp/tools/` 创建新文件
2. 导入工具定义和处理函数
3. 在 `list_tools()` 返回列表中添加
4. 在 `call_tool()` 中添加路由

---

## 配置

### 依赖管理
文件: `pyproject.toml`

**新增依赖**: 在 `dependencies` 列表中添加

---

### ClaudeCode 配置
文件: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "data-analysis-agent": {
      "command": "python",
      "args": ["-m", "data_analysis_agent"],
      "cwd": "项目路径"
    }
  }
}
```

---

## 快速定位

| 我想... | 去哪里... |
|---------|-----------|
| 添加新的 MCP 工具 | `mcp/tools/` + `mcp/server.py` |
| 支持新的文件格式 | `core/excel_reader.py:316` |
| 添加新的聚合函数 | `core/excel_reader.py:437` |
| 添加新的过滤操作符 | `core/excel_reader.py:411` |
| 大文件分块读取 | `ExcelReader.read_chunked()` |
| 多线程并行读取 | `ExcelReader.read_parallel_chunks()` |
| 列选择优化 | `get_info/read/query(usecols=...)` |
| 快速行数统计 | `ExcelReader.get_row_count()` |
| 首尾读取 | `ExcelReader.read_head/tail()` |
| 缓存控制 | `ExcelReader(enable_cache=False, max_cache_size=10)` |
| 缓存统计 | `ExcelReader.get_cache_info()` |
| 清空缓存 | `ExcelReader.clear_cache()` |
| 修改图表样式 | `core/chart_renderer.py` 模板部分 |
| 修改返回数据格式 | 对应工具的处理函数 |
| 添加依赖 | `pyproject.toml` |
