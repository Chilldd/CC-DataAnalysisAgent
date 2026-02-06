# DataAnalysisAgent MCP Server

Excel 数据读取和图表生成 MCP Server。

## 安装

```bash
pip install -e .
```

## 配置

`%APPDATA%\Claude\claude_desktop_config.json`:

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

## 运行

```bash
python -m data_analysis_agent
```

## AI 开发参考

详见 [docs/AI_REFERENCE.md](docs/AI_REFERENCE.md)
