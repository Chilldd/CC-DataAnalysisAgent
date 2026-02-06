# CLAUDE.md

DataAnalysisAgent MCP Server - 为 ClaudeCode 提供 Excel 数据读取和图表生成能力。

## 文档优先级

1. **AI_REFERENCE.md** - API schema、模块索引、扩展入口
2. **CLAUDE.md** (当前文件) - Agent 工作流、行为约束
3. **README.md** - 用户使用说明

## AI 行为约束

### 必须遵守
- 所有工具返回必须 JSON 可序列化
- datetime 自动转 ISO 字符串
- 大文件使用 usecols + limit 控制 token
- 禁止返回 DataFrame 或二进制数据

### 工作流
```
session_start → get_excel_schema → get_chart_data → generate_chart_html → session_end
```

### 代码修改后
- 接口变化 → 更新 AI_REFERENCE.md
- 使用方式变化 → 更新 README.md
- Agent 流程变化 → 更新 CLAUDE.md

**禁止只改代码不更新文档**

## 文档职责边界

| 文档 | 用途 | 禁止写入 | 触发更新 |
|------|------|----------|----------|
| **README.md** | 用户使用说明、安装配置、功能概览 | 内部架构、Agent规则、API schema、TODO | 新用户可见功能、使用方式改变 |
| **CLAUDE.md** | Agent工作流、行为约束、开发协议 | API细节、完整功能说明、用户教程 | Agent行为变化、工具接入流程变化 |
| **AI_REFERENCE.md** | API schema、模块索引、扩展入口 | 使用教程、Agent workflow、TODO | 新接口、新模块、数据结构变更 |

## 快速命令

```bash
pip install -e .
python -m data_analysis_agent
```

## 架构

```
ClaudeCode → MCP Server → Tools → Core → Files
```

## 扩展入口

| 扩展类型 | 位置 |
|----------|------|
| 新工具 | `mcp/tools/` + `mcp/server.py` |
| 新文件格式 | `core/excel_reader.py:_read_file()` |
| 新聚合函数 | `core/excel_reader.py:_group_and_aggregate()` |
| 新过滤操作符 | `core/excel_reader.py:_apply_filters()` |
