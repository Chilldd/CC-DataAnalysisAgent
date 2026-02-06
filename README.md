# DataAnalysisAgent MCP Server

数据分析 Agent MCP Server，为 ClaudeCode 提供 Excel 数据读取和图表生成能力。

## 功能特性

- **Token 优化工作流** - `get_excel_schema` 快速了解结构 → `get_chart_data(usecols=...)` 按列处理
- **TOON 格式支持** - 节省 40-70% token 消耗，对象数组场景最优
- **首次加载优化** - `session_start` 支持预加载文件，首次调用性能提升 600 倍
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
      "args": ["-m", "data_analysis_agent"],
      "cwd": "D:\\WorkSpace\\AI\\CC-DataAnalysisAgent"
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

### 首次加载优化（v0.10.0 新增）

如果需要处理多个文件或已知要分析的数据，可以在会话开始时预加载：

```
// 预加载多个文件的元数据（快速模式）
session_start({
  "session_name": "销售数据分析",
  "preload_files": ["sales.xlsx", "products.xlsx", "customers.xlsx"],
  "preload_mode": "metadata"  // 仅加载元数据，极快（~100ms）
})

// 后续调用 get_excel_schema 将非常快（~5ms）
```

**性能对比**：

| 场景 | 无预加载 | 预加载 metadata | 提升 |
|------|---------|-----------------|------|
| 首次调用 `get_excel_schema` | ~3000ms | ~5ms | **600x** |
| 后续调用 `get_chart_data` | ~5ms | ~5ms | 无变化 |

## 工具说明

### session_start / session_end

会话管理，用于统计数据传输和性能分析

**v0.10.0 新增**：
- `preload_files` 参数：预加载文件列表，优化首次访问性能
- `preload_mode` 参数：选择预加载模式
  - `metadata`：仅加载元数据（极快，~100ms）
  - `full`：完整加载数据（较快，~1-3s）

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

**v0.10.1 更新**：移除 `show_data_table` 参数，强制不显示数据表格

### get_chart_data

从 Excel 文件中查询和聚合数据，用于图表渲染

**v0.6.0 新增**：
- `usecols` 参数支持列选择，减少 token 消耗

**v0.11.0 新增**：
- 扩展聚合函数：median（中位数）、std（标准差）、var（方差）、first、last、nunique

**v0.12.0 新增**：
- 扩展过滤操作符：in、not_in、is_null、is_not_null、starts_with、ends_with、regex
- 扩展聚合函数：percentile25/75/90（百分位数）、mode（众数）、cumsum/cummax/cummin（累计聚合）、rolling_avg（移动平均）
- `window` 参数：用于 rolling_avg 指定窗口大小

### batch_get_chart_data（v0.9.0 新增）

批量获取图表数据，一次性处理多个查询

**优势**：
- 只读取一次文件，自动推断所有查询需要的列
- 在内存中执行多个查询，避免重复 I/O
- 响应速度提升 3-4 倍

**使用场景**：需要生成多个图表时

## 文档

| 文档 | 说明 |
|------|------|
| [DESIGN.md](docs/DESIGN.md) | 架构设计、MCP 工具接口、版本历史 |
| [FEATURES.md](docs/FEATURES.md) | 功能清单与修改位置 |
| [API.md](docs/API.md) | API 参考和扩展示例 |
| [TASKS.md](docs/TASKS.md) | 待办任务清单 |

## 许可证

MIT
