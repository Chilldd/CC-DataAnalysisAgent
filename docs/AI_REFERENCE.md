# AI Reference

代码位置：`src/data_analysis_agent/`

## 项目结构

```
src/data_analysis_agent/
├── mcp/
│   ├── server.py              # MCP 服务器入口
│   └── tools/                 # MCP 工具实现
│       ├── session_start.py
│       ├── session_end.py
│       ├── get_excel_schema.py
│       ├── get_excel_info.py
│       ├── get_chart_data.py
│       ├── batch_get_chart_data.py
│       ├── generate_chart_html.py
│       ├── read_head_excel.py
│       ├── read_tail_excel.py
│       └── get_reader_stats.py
└── core/
    ├── excel_reader.py        # 数据读取、查询、聚合
    ├── chart_renderer.py      # 图表生成
    ├── reader_manager.py      # 读取器管理
    ├── toon_serializer.py     # TOON 格式
    ├── config.py              # 配置管理
    ├── logging_config.py      # 日志系统
    ├── metrics_logger.py      # 指标统计
    └── exceptions.py          # 异常定义
```

## MCP 工具列表

| 工具 | 文件 | 必需参数 | 用途 |
|------|------|----------|------|
| session_start | tools/session_start.py | 无 | 会话初始化 |
| session_end | tools/session_end.py | 无 | 会话结束+统计 |
| get_excel_schema | tools/get_excel_schema.py | file_path | 获取数据结构 |
| get_chart_data | tools/get_chart_data.py | file_path, group_by, aggregation | 聚合查询 |
| batch_get_chart_data | tools/batch_get_chart_data.py | file_path, queries | 批量聚合查询 |
| generate_chart_html | tools/generate_chart_html.py | file_path, echarts_configs | 生成图表HTML |
| read_head_excel | tools/read_head_excel.py | file_path | 读取前n行 |
| read_tail_excel | tools/read_tail_excel.py | file_path | 读取后n行 |
| get_excel_info | tools/get_excel_info.py | file_path | 获取文件信息 |
| get_reader_stats | tools/get_reader_stats.py | file_path | 获取缓存统计 |

## get_chart_data 实际支持的参数

```typescript
{
  file_path: string;           // 必需
  group_by: string;            // 必需：分组列名
  aggregation: string;         // 必需：聚合函数
  aggregate_column?: string;   // count 时可选
  usecols?: string;            // 列选择，逗号分隔
  filters?: Array<{            // 过滤条件
    column: string;
    operator: string;
    value: any;
  }>;
  order_by?: string;
  order?: "asc" | "desc";
  limit?: number;              // 默认 100
  sheet_name?: string;
  window?: number;             // rolling_avg 的窗口大小
}
```

## ExcelReader 实际支持的聚合函数

**基础** (工具定义中): sum, avg, count, min, max
**高级** (代码实现中): median, std, var, first, last, nunique, percentile25, percentile75, percentile90, mode, cumsum, cummax, cummin, rolling_avg

**注意**: 工具的 inputSchema 只定义了基础函数，高级函数需在代码中使用

## ExcelReader 实际支持的过滤操作符

**工具定义中**: =, !=, >, <, >=, <=, contains
**代码实现中**: + starts_with, ends_with, regex, in, not_in, is_null, is_not_null

**注意**: 工具的 inputSchema 只定义了基础操作符

## 返回数据格式

**成功**: `{"success": true, "data": ..., ...}`
**错误**: `{"success": false, "error": "..."}`

**query() 返回**:
```json
{
  "success": true,
  "label": "分组列名",
  "labels": ["值1", "值2"],
  "values": [10, 20],
  "data": [["值1", 10], ["值2", 20]],
  "rows": 2,
  "aggregation": "sum",
  "grouped_by": "分组列名"
}
```

## 扩展入口

| 扩展类型 | 文件 | 位置 |
|----------|------|------|
| 新工具 | tools/new_tool.py | + server.py 注册 |
| 新文件格式 | excel_reader.py | `_read_file()` 方法 |
| 新聚合函数 | excel_reader.py | `_group_and_aggregate()` 的 agg_funcs |
| 新过滤操作符 | excel_reader.py | `_apply_filters()` 方法 |
| 更新工具Schema | tools/get_chart_data.py | inputSchema |

## 关键约束

1. 所有返回值必须是 JSON 可序列化
2. datetime 自动转 ISO 字符串 (`_df_to_array`)
3. 使用 usecols 减少 token 消耗
4. 使用 limit 控制返回行数
5. 缓存键格式: `{sheet}:full` 或 `{sheet}:cols:A,B,C` (列名排序)

## 配置文件

**MCP**: `%APPDATA%\Claude\claude_desktop_config.json`
**项目**: `.data-analysis-agent.toml`

```toml
[server]
response_format = "toon"      # json | toon
show_format_info = true

[cache]
enabled = true
max_size = 10
ttl = 3600

[logging]
level = "INFO"
console = true
file = "logs/agent.log"
```
