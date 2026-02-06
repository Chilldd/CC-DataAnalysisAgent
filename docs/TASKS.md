# DataAnalysisAgent 任务清单

## 高优先级

### 1. CSV 编码自动检测 (P0)
```python
# core/excel_reader.py
import chardet
def _detect_encoding(self):
    with open(self.file_path, 'rb') as f:
        return chardet.detect(f.read(10000))['encoding'] or 'utf-8'
```

## 功能增强

### 2. 扩展聚合函数 (P1)
添加: median, std, var, first, last, nunique
位置: `core/excel_reader.py:700`

### 3. 扩展过滤操作符 (P1)
添加: in, not_in, is_null, is_not_null, starts_with, ends_with, regex
位置: `core/excel_reader.py:666`

### 4. 支持更多文件格式 (P1)
添加: .parquet, .json, .jsonl, .tsv, .xlsb, .ods
位置: `core/excel_reader.py:552`

### 5. 数据导出功能 (P2)
新增工具: `export_data`
导出: Excel, CSV, JSON, PNG

### 6. 多文件关联分析 (P2)
新增: `join_reader.py`, `join_data.py`
支持: 内连接、左连接、右连接

### 7. 数据清洗功能 (P2)
新增工具: `clean_data`
功能: 去重、空值处理、类型转换、异常检测

### 8. 自定义图表主题 (P2)
位置: `core/chart_renderer.py`
主题: 暗色、科技蓝、暖色、极简

### 9. 图表导出功能 (P2)
位置: `core/chart_renderer.py`
导出: PNG, SVG, PDF

## 代码质量

### 14. 类型注解完善 (P1)
为所有方法添加类型注解，配置 mypy

### 15. 异常处理优化 (P1)
新增: `exceptions.py`

### 17. 代码格式化配置 (P1)
配置: Black, isort, flake8, pre-commit hooks

## 配置与部署

### 18. 配置文件支持 (P2)
新增: `config.py`, `config.yaml`

### 19. Docker 镜像 (P2)
编写: Dockerfile, docker-compose.yml

### 20. 发布到 PyPI (P1)
完善: pyproject.toml, README 英文版, CHANGELOG.md

## 新增优化任务

### 28. 缓存预热优化 (P2)
位置: `core/excel_reader.py`
- 在 `session_start` 时预加载常用列
- 自动分析历史查询模式
- 智能预测可能需要的列

### 29. 查询结果缓存 (P2)
位置: `core/excel_reader.py`
- 缓存聚合查询结果（不仅仅是原始数据）
- 支持不同参数的查询结果缓存
- LRU 清理策略

### 30. 增量数据读取 (P2)
- 支持 CSV 增量读取（只读取新增行）
- 追加模式数据处理
- 大文件持续监控

### 31. 性能监控增强 (P2)
基于 `MetricsLogger` 扩展
- 导出 Prometheus 指标格式
- 添加内存使用监控
- 添加 DataFrame 内存占用追踪
- 支持自定义指标阈值

### 32. Token 优化建议系统 (P2)
新增: `token_optimizer.py`
- 自动检测可优化的工具调用
- 建议使用 `usecols` 参数
- 建议分页读取大文件
- 检测重复查询

### 33. 数据验证功能 (P2)
新增: `validators.py`
- 列数据类型验证
- 数据范围验证
- 必填字段检查
- 自定义验证规则

### 34. 智能列推荐增强 (P2)
位置: `mcp/tools/get_excel_schema.py`
- 基于数据分布推荐图表类型
- 自动检测时间序列数据
- 检测分类/数值列的基数
- 推荐合适的聚合方式

### 35. 错误恢复机制 (P2)
- 文件读取失败重试
- 大文件处理进度保存
- 部分数据返回机制

## 版本规划

| 版本 | 内容 |
|------|------|
| v0.5.0 | 图表优化：默认不显示数据表格、支持多图表、show_data_table 参数 |
| v0.6.0 | CSV编码检测、扩展聚合/过滤、代码格式化、类型注解 |
| v0.7.0 | 大文件优化、数据导出、更多格式、配置文件 |
| v0.8.0 | **日志系统增强**：数据传输统计、性能监控、大数据警告、定期摘要输出 |
| v0.9.0 | **缓存优化**：标准化缓存键、智能缓存共享、批量查询、缓存命中率 80%+ |
| v0.9.1 | **Bug 修复**：修复 usecols 参数传递问题、修复字节解析对带小数点单位的处理 |
| v1.0.0 | 多文件关联、数据清洗、自定义主题、Docker |
