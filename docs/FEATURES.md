# DataAnalysisAgent 功能清单

本文档提供所有功能的详细描述和代码位置，方便开发者快速定位和修改。

> **相关文档**:
> - `DESIGN.md` - 架构设计和 MCP 工具接口
> - `API.md` - API 参考和扩展示例

---

## 目录

- [MCP 工具](#mcp-工具)
- [核心功能](#核心功能)
- [类型系统](#类型系统)
- [配置](#配置)
- [快速定位](#快速定位)

---

## MCP 工具

### session_start / session_end

**版本**: v0.8.0 新增，v0.10.0 优化

**功能**: 会话管理和统计报告

| 项 | 位置 |
|---|---|
| 工具定义 | `mcp/tools/session_start.py` / `session_end.py` |
| 核心类 | `MetricsLogger` (`core/metrics_logger.py`) |
| 预加载功能 | `ReaderManager.preload_files()` (v0.10.0) |

**特性**:
- 会话生命周期管理
- 数据传输统计（自动记录）
- 性能分析和优化建议
- 缓存命中率报告
- 预加载文件功能（v0.10.0）

**v0.10.1 修复**:
- 修复 metadata 模式预加载后数据只有 1 行的问题
- metadata 模式现在使用 `read_head(n=5)` 获取样本，不缓存数据

**使用示例**:
```python
# 预加载多个文件的元数据（快速模式）
result = await handle_session_start(
    session_name="数据分析",
    preload_files=["data1.xlsx", "data2.xlsx"],
    preload_mode="metadata"  # 或 "full"
)
```

---

### get_excel_schema（推荐）

**版本**: v0.6.0 新增

**功能**: 快速获取 Excel 数据结构，最小 token 消耗

| 项 | 位置 |
|---|---|
| 工具定义 | `mcp/tools/get_excel_schema.py` |
| 核心类 | `ExcelReader._read_file()` |

**返回**: 列名、第一行数据、总行数、建议的维度/指标列

**推荐工作流**:
1. 调用 `get_excel_schema` 了解数据结构
2. Claude 选择需要使用的列
3. 调用 `get_chart_data(usecols=...)` 按列处理数据

---

### get_excel_info

**功能**: 获取 Excel/CSV 文件的结构信息和样本数据

| 项 | 位置 |
|---|---|
| 工具定义 | `mcp/tools/get_excel_info.py` |
| 核心类 | `ExcelReader.get_info()` |
| 列类型检测 | `ExcelReader._get_column_types()` |
| 列统计 | `ExcelReader._get_column_stats()` |

**修改返回数据结构**: 编辑 `get_info()` 方法

---

### generate_chart_html

**功能**: 基于 ECharts 配置生成完整的 HTML 图表文件

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

**版本变更**:
- v0.5.0: `echarts_configs` 参数支持多图表数组
- v0.10.1: 移除 `show_data_table` 参数，强制不显示数据表格

---

### read_head_excel / read_tail_excel

**版本**: v0.4.0 新增

**功能**: 快速读取 Excel 文件前/后 n 行数据

| 项 | 位置 |
|---|---|
| 工具定义 | `mcp/tools/read_head_excel.py` / `read_tail_excel.py` |
| 核心类 | `ExcelReader.read_head()` / `read_tail()` |

---

### get_chart_data

**功能**: 查询和聚合数据用于图表渲染

| 项 | 位置 |
|---|---|
| 工具定义 | `mcp/tools/get_chart_data.py` |
| 核心类 | `ExcelReader.query()` |
| 过滤条件 | `ExcelReader._apply_filters()` |
| 分组聚合 | `ExcelReader._group_and_aggregate()` |

**支持的聚合函数**:
- **基础统计**: sum, avg, count, min, max
- **高级统计**: median（中位数）, std（标准差）, var（方差）[v0.11.0]
- **位置值**: first（第一个值）, last（最后一个值）[v0.11.0]
- **基数统计**: nunique（唯一值计数）[v0.11.0]

**修改**:
- 新增过滤操作符: 编辑 `_apply_filters()` 方法
- 新增聚合函数: 编辑 `_group_and_aggregate()` 方法
- 同时更新工具的 `inputSchema`

**v0.6.0 新增**: `usecols` 参数支持列选择
**v0.11.0 新增**: 6 种新聚合函数（median, std, var, first, last, nunique）

---

### batch_get_chart_data

**版本**: v0.9.0 新增

**功能**: 批量获取图表数据（一次性处理多个查询）

| 项 | 位置 |
|---|---|
| 工具定义 | `mcp/tools/batch_get_chart_data.py` |
| 核心类 | `ExcelReader.query()` |
| 列推断 | `_extract_columns_from_queries()` |

**特点**:
- 只读取一次文件，自动推断所有查询需要的列
- 在内存中执行多个查询，避免重复 I/O
- 返回详细的性能指标

**性能**: 4 个查询 1.36s → 0.35s (3.9x)

---

## 核心功能

### TOON 格式支持

**版本**: v0.8.0 新增

**功能**: Token-Oriented Object Notation - 节省 40-70% token 消耗

| 项 | 位置 |
|---|---|
| 配置模块 | `core/config.py` |
| 序列化器 | `core/toon_serializer.py` |
| 格式转换 | `mcp/server.py:_convert_to_toon()` |
| 配置文件 | `.data-analysis-agent.toml` |

**性能对比**:
| 数据类型 | JSON | TOON | 节省 |
|---------|------|------|------|
| 对象数组 (100 条) | 15,144 tokens | 8,744 tokens | 42% |
| 对象数组 (3 条) | 231 字符 | 68 字符 | 70.6% |
| 简单数据 | 251 字符 | 113 字符 | 55% |

**适用场景**:
- ✅ **推荐**: 对象数组（数据库查询结果、聚合数据）
- ❌ **不推荐**: 深度嵌套结构
- ❌ **不推荐**: 纯表格数据

---

### 大文件分块读取

**版本**: v0.2.0 新增

| 项 | 位置 |
|---|---|
| 方法 | `ExcelReader.read_chunked()` |

**使用示例**:
```python
reader = ExcelReader("large_file.xlsx")
for chunk in reader.read_chunked(chunksize=5000):
    process_chunk(chunk)
```

---

### 智能缓存机制

**版本**: v0.3.0 新增，v0.4.0 升级，v0.9.0 优化

| 项 | 位置 |
|---|---|
| 配置 | `ExcelReader.__init__(enable_cache=True, max_cache_size=10)` |
| 缓存存储 | `_cache`, `_row_count_cache` (OrderedDict) |
| LRU 清理 | `_read_file()` |
| 标准化缓存键 | `_normalize_cache_key()` (v0.9.0) |
| 智能缓存共享 | `_read_file()` (v0.9.0) |

**v0.9.0 优化**:
- 缓存键标准化：列名排序确保一致性
- 智能缓存共享：从全量缓存提取列子集
- 缓存命中率：20% → 80%+

**使用示例**:
```python
reader = ExcelReader("data.xlsx", max_cache_size=20)

# 获取缓存统计
info = reader.get_cache_info()
print(f"命中率: {info['hit_rate']}%, 内存: {info['cache_memory_mb']}MB")

# 清空缓存
reader.clear_cache()
```

---

### 多线程读取

**版本**: v0.4.0 新增

| 项 | 位置 |
|---|---|
| 方法 | `ExcelReader.read_parallel_chunks()` |
| 配置 | `ExcelReader.__init__(enable_threading=True)` |

**使用示例**:
```python
reader = ExcelReader("large_file.xlsx", enable_threading=True)
chunks = reader.read_parallel_chunks(chunksize=10000, num_chunks=4)
df_combined = pd.concat(chunks, ignore_index=True)
```

---

### 快速行数统计

**版本**: v0.3.0 新增

| 项 | 位置 |
|---|---|
| 方法 | `ExcelReader.get_row_count()` |

---

### 日志系统

**版本**: v0.8.0 新增

| 项 | 位置 |
|---|---|
| 模块 | `core/logging_config.py` |
| 导出 | `core/__init__.py` |

**特性**:
- 控制台彩色日志输出
- 文件日志支持按时间/大小滚动
- 错误日志单独记录到 `error.log`
- 指标日志单独记录到 `metrics.log`
- 数据传输量统计
- 性能监控

**日志级别**:
- DEBUG：详细调试信息
- INFO：一般信息
- WARNING：警告信息（大数据传输 >100KB）
- ERROR：错误信息
- CRITICAL：严重错误

---

## 类型系统

### 列类型映射

```
object   → string
int64/int32  → number
float64/float32 → number
datetime64[ns] → datetime
bool     → boolean
```

| 项 | 位置 |
|---|---|
| 方法 | `ExcelReader._get_column_types()` |

**修改**: 添加新的类型映射

---

## 配置

### 依赖管理

文件: `pyproject.toml`

**新增依赖**: 在 `dependencies` 列表中添加

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

### TOON 格式配置

文件: `.data-analysis-agent.toml` 或 `~/.config/data-analysis-agent/config.toml`

```toml
[server]
response_format = "toon"
show_format_info = true
```

---

## 快速定位

| 我想... | 去哪里... |
|---------|-----------|
| 添加新的 MCP 工具 | `mcp/tools/` + `mcp/server.py` |
| 支持新的文件格式 | `core/excel_reader.py:_read_file()` |
| 添加新的聚合函数 | `core/excel_reader.py:_group_and_aggregate()` |
| 添加新的过滤操作符 | `core/excel_reader.py:_apply_filters()` |
| 大文件分块读取 | `ExcelReader.read_chunked()` |
| 多线程并行读取 | `ExcelReader.read_parallel_chunks()` |
| 列选择优化 | 各工具的 `usecols` 参数 |
| 快速行数统计 | `ExcelReader.get_row_count()` |
| 首尾读取 | `ExcelReader.read_head/tail()` |
| 缓存控制 | `ExcelReader(enable_cache=, max_cache_size=)` |
| 缓存统计 | `ExcelReader.get_cache_info()` |
| 清空缓存 | `ExcelReader.clear_cache()` |
| 修改图表样式 | `core/chart_renderer.py:_render_template()` |
| 设置 TOON 格式 | `.data-analysis-agent.toml` 或环境变量 |
| TOON 序列化 | `core/toon_serializer.py` |
| 添加依赖 | `pyproject.toml` |
