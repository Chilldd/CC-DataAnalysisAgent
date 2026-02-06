# DataAnalysisAgent 功能清单

## MCP 工具

### session_start / session_end（v0.8.0 新增，v0.10.0 优化）
会话管理和统计报告

| 项 | 位置 |
|---|---|
| 工具定义 | `mcp/tools/session_start.py` / `session_end.py` |
| 核心类 | `MetricsLogger` |
| 预加载功能 | `ReaderManager.preload_files()` (v0.10.0) |

**特点**：
- 会话生命周期管理
- 数据传输统计（自动记录）
- 性能分析和优化建议
- 缓存命中率报告
- **预加载文件功能**（v0.10.0 新增）

**v0.10.0 新增 - 首次加载优化**：
- `preload_files` 参数：在会话开始时预加载文件
- `preload_mode` 参数：选择预加载模式
  - `metadata`：仅加载元数据（sheet 名称、列信息、前5行样本），不缓存数据
  - `full`：完整加载数据并缓存
- 优化首次访问性能，避免第一次调用 `get_excel_schema` 时的延迟

**v0.10.1 修复**：
- 修复 metadata 模式预加载后数据只有 1 行的问题
- metadata 模式现在使用 `read_head(n=5)` 获取样本，不会缓存数据
- 确保后续调用 `get_excel_schema` 能获取完整数据

**使用示例**：
```python
# 预加载多个文件的元数据（快速模式）
result = await handle_session_start(
    session_name="数据分析",
    preload_files=["data1.xlsx", "data2.xlsx"],
    preload_mode="metadata"
)

# 预加载完整数据
result = await handle_session_start(
    session_name="数据分析",
    preload_files=["data.xlsx"],
    preload_mode="full"
)
```

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

**v0.10.1 更新**:
- **移除 `show_data_table` 参数**，强制不显示数据表格
- 移除数据读取逻辑，减少不必要的数据传输

**历史版本**:
- v0.5.0: `echarts_configs` 参数支持多图表数组

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

### batch_get_chart_data（v0.9.0 新增）
批量获取图表数据（优化版，一次性处理多个查询）

| 项 | 位置 |
|---|---|
| 工具定义 | `mcp/tools/batch_get_chart_data.py` |
| 核心类 | `ExcelReader.query()` |
| 列推断 | `_extract_columns_from_queries()` |

**特点**：
- 只读取一次文件，自动推断所有查询需要的列
- 在内存中执行多个查询，避免重复 I/O
- 返回详细的性能指标

**性能提升**：
- 4 个查询：1.36s → 0.35s（3.9x）
- 推荐用于多图表场景

---

## 核心功能

### TOON 格式支持 (v0.8.0 新增)
Token-Oriented Object Notation - 节省 40-70% token 消耗

| 项 | 位置 |
|---|---|
| 配置模块 | `core/config.py` |
| 序列化器 | `core/toon_serializer.py` |
| 格式转换 | `mcp/server.py:_convert_to_toon()` |
| 配置文件 | `.data-analysis-agent.toml` |

**特性**：
- 支持 JSON 和 TOON 格式切换
- 通过配置文件或环境变量设置
- 对象数组场景最优（节省约 70%）
- 自动错误处理（TOON 转换失败时降级到 JSON）

**配置方式**：

1. **配置文件** (`.data-analysis-agent.toml`):
```toml
[server]
response_format = "toon"
show_format_info = true
```

2. **环境变量**:
```bash
export DAA_RESPONSE_FORMAT=toon
```

3. **代码中动态设置**:
```python
from data_analysis_agent.core import set_response_format
set_response_format("toon")
```

**性能对比**：

| 数据类型 | JSON | TOON | 节省 |
|---------|------|------|------|
| 对象数组 (100 条) | 15,144 tokens | 8,744 tokens | 42% |
| 对象数组 (3 条) | 231 字符 | 68 字符 | 70.6% |
| 简单数据 | 251 字符 | 113 字符 | 55% |

**使用示例**:
```python
from data_analysis_agent.core import (
    to_toon, serialize_result, estimate_token_savings,
    get_response_format, set_response_format
)

# 序列化为 TOON 格式
data = {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
toon_str = to_toon(data)
# 输出:
# users[2]{id,name}:
#   1,Alice
#   2,Bob

# 带格式标记的序列化
result = serialize_result(data, format_type="toon", show_format=True)
# 输出:
# ```toon
# users[2]{id,name}:
#   1,Alice
#   2,Bob
# ```

# 估算 token 节省
savings = estimate_token_savings(data)
print(f"节省: {savings['savings_percent']}%")

# 检查和设置格式
print(f"当前格式: {get_response_format()}")
set_response_format("toon")
```

**适用场景**：
- ✅ **推荐**: 对象数组（数据库查询结果、聚合数据）
- ✅ **推荐**: 简单键值对数据
- ❌ **不推荐**: 深度嵌套结构（JSON compact 更高效）
- ❌ **不推荐**: 纯表格数据（CSV 更小）

---

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

### 智能缓存机制 (v0.3.0 新增, v0.4.0 升级, v0.9.0 优化)
基于文件修改时间的自动缓存，避免重复读取。v0.4.0 新增 LRU 策略和缓存大小限制。v0.9.0 新增标准化缓存键和智能缓存共享。

| 项 | 位置 |
|---|---|
| 配置 | `ExcelReader.__init__(enable_cache=True, max_cache_size=10)` |
| 缓存存储 | `_cache`, `_row_count_cache` (OrderedDict) |
| LRU 清理 | `_read_file()` |
| 标准化缓存键 | `_normalize_cache_key()` (v0.9.0) |
| 智能缓存共享 | `_read_file()` (v0.9.0) |
| 行号 | ~13, ~316, ~496 |

**v0.9.0 优化**：
- 缓存键标准化：列名排序确保一致性
- 智能缓存共享：从全量缓存提取列子集
- 缓存命中率：20% → 80%+

**使用示例**:
```python
# 启用缓存（默认），设置最大缓存条目数
reader = ExcelReader("data.xlsx", max_cache_size=20)
data1 = reader.read()  # 第一次读取，从文件加载
data2 = reader.read()  # 第二次读取，从缓存获取（文件未修改）

# 缓存共享：先读取全量，再读取列子集会自动从缓存提取
data_all = reader.read()  # 缓存全量数据
data_subset = reader.read(usecols=["A", "B"])  # 从全量缓存提取

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
| 行号 | ~521 |

**v0.9.1 修复**:
- 修复 `usecols` 参数传递问题（原传递原始字符串而非解析后的列表）
- pandas read_excel/read_csv 不接受逗号分隔的字符串，必须传递列表

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
| 设置 TOON 格式 | `.data-analysis-agent.toml` 或环境变量 `DAA_RESPONSE_FORMAT` |
| TOON 序列化 | `core/toon_serializer.py` |
| 添加依赖 | `pyproject.toml` |
