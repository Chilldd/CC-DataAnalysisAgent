# CLAUDE.md

DataAnalysisAgent MCP Server - 为 ClaudeCode 提供 Excel 数据读取和图表生成能力。

## 文档

| 文档 | 作用 |
|------|------|
| README.md | 用户指南 |
| FEATURES.md | **功能清单与修改位置** |
| DESIGN.md | 架构设计、MCP 工具接口 |
| API.md | 扩展开发指南 |
| TASKS.md | 待办任务清单 |

## 工作流

完成任务后：
1. **删除** TASKS.md 中的任务
2. 更新 DESIGN.md（新功能、版本历史）
3. 更新 README.md（用户可见功能）
4. 更新 API.md（扩展示例）
5. 更新 FEATURES.md（功能清单与修改位置）
6. 思考是否可以有扩展或优化任务，如果有加入到TASKS.md中

## 命令

```bash
pip install -e .                      # 安装
python -m data_analysis_agent        # 运行
```

## 架构

```
ClaudeCode → MCP Server → Tools → Core → Files
```

| 组件 | 路径 |
|------|------|
| ExcelReader | `core/excel_reader.py` |
| ChartRenderer | `core/chart_renderer.py` |
| Server | `mcp/server.py` |

## 扩展

| 扩展 | 位置 |
|------|------|
| 新工具 | `mcp/tools/` + `mcp/server.py` |
| 新文件格式 | `core/excel_reader.py:129` |
| 新聚合函数 | `core/excel_reader.py:230` |
| 新过滤操作符 | `core/excel_reader.py:196` |

## 数据格式

```json
// 工具返回
{"success": true, "data": ...}

// 表格数据
[["列1", "列2"], ["值1", "值2"]]
```

## 约束

- 所有返回数据必须 JSON 可序列化
- datetime 自动转字符串
- 使用 `limit` 参数控制大文件
